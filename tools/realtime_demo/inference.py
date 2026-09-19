"""Live inference for the 2x2 Original/CLAHE x HSEmotion/ArcFace+LR demo,
now supporting multiple simultaneously detected faces.

Loads three model artifacts ONCE at process startup (one InsightFace
FaceAnalysis instance providing both detection and the ArcFace
recognition sub-model, one HSEmotionRecognizer, one demo-only Logistic
Regression classifier) and exposes a single process_frame() entry point
that:

  1. Runs face detection ONCE per frame (shared across every face and
     every one of the four pipelines -- never re-detected per face or
     per pipeline).
  2. Sorts detected faces deterministically, left-to-right by bounding
     box x1 (a stable, reproducible ordering -- not detector-confidence
     order, which can vary frame to frame for near-tied faces).
  3. Processes up to MAX_DEMO_FACES faces (see that constant below);
     any additional faces beyond the limit are counted but not
     processed, and this is reported explicitly in the response, never
     silently dropped.
  4. For each processed face, runs all four pipelines (Original
     HSEmotion, Original ArcFace+LR, CLAHE HSEmotion, CLAHE ArcFace+LR)
     from that face's own crop -- one face's pipeline failure is caught
     and reported per-pipeline, never allowed to abort the whole frame
     or the other faces.
  5. Also returns small, resized JPEG thumbnails (base64-encoded) of
     EVERY processed face's original and CLAHE crops, for the
     dashboard's live CLAHE before/after preview and "Live Processing
     Flow" detail view (which lets the user pick which detected face
     to inspect) -- generated from the SAME apply_strategy_b_clahe()
     call already used for that face's CLAHE inference paths, never a
     second, separate CLAHE call, and never a second crop operation.

CLAHE preprocessing is `tools/realtime_demo/clahe_preprocessing.py`,
copied verbatim from EXP-006 (see that module's docstring for exactly
what is reused vs. extended).

Nothing here writes to any research CSV, dataset file, or experiment
report. This module only performs read-only model loading and
in-memory inference on live camera frames that are never persisted to
disk.
"""

from __future__ import annotations

import base64
from pathlib import Path

import cv2
import insightface
import joblib
import numpy as np
from hsemotion_onnx.facial_emotions import HSEmotionRecognizer

from clahe_preprocessing import apply_strategy_b_clahe

DEMO_MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "arcface_lr_demo_model.joblib"
DEMO_CLASS_ORDER = ["Fear", "Happy", "Neutral", "Sad", "Surprise"]  # must match build_demo_classifier.py output

# Maximum number of simultaneously detected faces the demo will run all
# four pipelines on per frame. Beyond this, additional faces are
# detected and counted but not processed, to keep the demo responsive
# on a normal laptop CPU (each extra face roughly doubles the per-frame
# HSEmotion + ArcFace inference cost). Documented in
# tools/realtime_demo/README.md.
MAX_DEMO_FACES = 3

# Size (pixels, square) of the live CLAHE before/after preview
# thumbnails sent to the browser. Deliberately small -- this is a
# visualization aid, not a high-resolution image transfer.
PREVIEW_THUMBNAIL_SIZE = 96
PREVIEW_JPEG_QUALITY = 70


class DemoInferenceEngine:
    def __init__(self) -> None:
        self.face_app = None
        self.recognition_model = None  # app.models["recognition"], reused directly for the CLAHE re-embed
        self.hsemotion_model = None
        self.arcface_classifier = None
        self.load_errors: dict[str, str] = {}

        try:
            self.face_app = insightface.app.FaceAnalysis(
                name="buffalo_l",
                allowed_modules=["detection", "recognition"],
                providers=["CPUExecutionProvider"],
            )
            self.face_app.prepare(ctx_id=0)
            self.recognition_model = self.face_app.models.get("recognition")
        except Exception as exc:  # noqa: BLE001 -- startup diagnostics, reported not swallowed
            self.load_errors["face_detection"] = str(exc)

        try:
            self.hsemotion_model = HSEmotionRecognizer(model_name="enet_b0_8_best_vgaf")
        except Exception as exc:  # noqa: BLE001
            self.load_errors["hsemotion"] = str(exc)

        try:
            if not DEMO_MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"{DEMO_MODEL_PATH} not found -- run "
                    "`uv run python tools/realtime_demo/build_demo_classifier.py` first."
                )
            self.arcface_classifier = joblib.load(DEMO_MODEL_PATH)
        except Exception as exc:  # noqa: BLE001
            self.load_errors["arcface_classifier"] = str(exc)

    def _sort_faces(self, faces: list) -> list:
        """Deterministic left-to-right ordering by bounding-box x1, so
        'Face 1'/'Face 2'/'Face 3' stay visually consistent (leftmost
        person is always Face 1) and consistent across all four panels,
        which all receive this same ordered list."""
        return sorted(faces, key=lambda f: float(f.bbox[0]))

    def _run_hsemotion(self, image_bgr: np.ndarray) -> dict:
        if self.hsemotion_model is None or image_bgr.size == 0:
            return {"available": False, "error": self.load_errors.get("hsemotion", "no face crop")}
        try:
            emotion, scores = self.hsemotion_model.predict_emotions(image_bgr, logits=False)
            return {"available": True, "label": emotion, "confidence": float(np.max(scores))}
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "error": str(exc)}

    def _run_arcface_from_embedding(self, embedding: np.ndarray | None) -> dict:
        if self.arcface_classifier is None:
            return {
                "available": False,
                "error": self.load_errors.get("arcface_classifier", "classifier not loaded"),
            }
        if embedding is None:
            return {"available": False, "error": "no embedding produced for detected face"}
        try:
            embedding = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
            probs = self.arcface_classifier.predict_proba(embedding)[0]
            pred_idx = int(np.argmax(probs))
            return {
                "available": True,
                "label": DEMO_CLASS_ORDER[pred_idx],
                "confidence": float(probs[pred_idx]),
            }
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "error": str(exc)}

    def _encode_thumbnail(self, image_bgr: np.ndarray) -> str | None:
        try:
            resized = cv2.resize(
                image_bgr, (PREVIEW_THUMBNAIL_SIZE, PREVIEW_THUMBNAIL_SIZE), interpolation=cv2.INTER_AREA
            )
            ok, buf = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, PREVIEW_JPEG_QUALITY])
            if not ok:
                return None
            return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")
        except Exception:  # noqa: BLE001
            return None

    def _process_one_face(self, frame_bgr: np.ndarray, face, face_id: int, include_preview: bool) -> dict:
        h, w = frame_bgr.shape[:2]
        x1, y1, x2, y2 = face.bbox
        bbox_norm = [
            float(max(0.0, x1 / w)),
            float(max(0.0, y1 / h)),
            float(min(1.0, x2 / w)),
            float(min(1.0, y2 / h)),
        ]
        x1i, y1i = max(0, int(x1)), max(0, int(y1))
        x2i, y2i = min(w, int(x2)), min(h, int(y2))
        original_crop = frame_bgr[y1i:y2i, x1i:x2i]

        record = {"face_id": face_id, "bbox": bbox_norm, "original": {}, "clahe": {}}

        if original_crop.size == 0:
            unavailable = {"available": False, "error": "empty face crop"}
            record["original"] = {"hsemotion": unavailable, "arcface": unavailable}
            record["clahe"] = {"hsemotion": unavailable, "arcface": unavailable}
            return record

        # --- Original path: HSEmotion ---
        record["original"]["hsemotion"] = self._run_hsemotion(original_crop)

        # --- Original path: ArcFace + LR ---
        # face.normed_embedding was already computed by the single
        # face_app.get() call in process_frame() (FaceAnalysis internally
        # runs every loaded recognition sub-model on every detected face)
        # -- reused here per-face, not recomputed.
        original_embedding = None
        try:
            emb = face.normed_embedding
            if emb is not None:
                original_embedding = np.array(emb, dtype=np.float32, copy=True)
        except Exception:  # noqa: BLE001
            original_embedding = None
        record["original"]["arcface"] = self._run_arcface_from_embedding(original_embedding)

        # --- CLAHE preprocessing of this face's crop (EXP-006's transform, verbatim) ---
        try:
            clahe_crop, _l_weighted, _clip_used = apply_strategy_b_clahe(original_crop)
            clahe_error = None
        except Exception as exc:  # noqa: BLE001
            clahe_crop = None
            clahe_error = str(exc)

        if clahe_crop is None:
            unavailable = {"available": False, "error": f"CLAHE unavailable: {clahe_error}"}
            record["clahe"]["hsemotion"] = unavailable
            record["clahe"]["arcface"] = unavailable
            if include_preview:
                record["preprocessing"] = {
                    "original_crop": self._encode_thumbnail(original_crop),
                    "clahe_crop": None,
                }
            return record

        # --- CLAHE path: HSEmotion ---
        record["clahe"]["hsemotion"] = self._run_hsemotion(clahe_crop)

        # --- CLAHE path: ArcFace + LR ---
        # Re-run ONLY the recognition sub-model (no second detection) on
        # the CLAHE-adjusted crop, using kps shifted into crop-local
        # coordinates (this crop's own top-left corner as origin).
        clahe_embedding = None
        if self.recognition_model is not None and face.kps is not None:
            try:
                local_kps = np.asarray(face.kps, dtype=np.float32) - np.array([x1i, y1i], dtype=np.float32)
                clahe_face = insightface.app.common.Face(
                    bbox=face.bbox - [x1i, y1i, x1i, y1i], kps=local_kps
                )
                self.recognition_model.get(clahe_crop, clahe_face)
                emb = clahe_face.normed_embedding
                if emb is not None:
                    clahe_embedding = np.array(emb, dtype=np.float32, copy=True)
            except Exception:  # noqa: BLE001
                clahe_embedding = None
        record["clahe"]["arcface"] = self._run_arcface_from_embedding(clahe_embedding)

        # --- Live CLAHE before/after preview thumbnails, same crops used above ---
        if include_preview:
            record["preprocessing"] = {
                "original_crop": self._encode_thumbnail(original_crop),
                "clahe_crop": self._encode_thumbnail(clahe_crop),
            }

        return record

    def process_frame(self, frame_bgr: np.ndarray) -> dict:
        if self.face_app is None:
            return {"status": "error", "error": "face detection unavailable"}

        # --- Shared face detection: ONE invocation for every face and every pipeline ---
        faces = self.face_app.get(frame_bgr)

        if len(faces) == 0:
            return {"status": "no_face"}

        ordered = self._sort_faces(faces)
        faces_detected = len(ordered)
        to_process = ordered[:MAX_DEMO_FACES]
        faces_truncated = faces_detected - len(to_process)

        face_records = []
        for idx, face in enumerate(to_process, start=1):
            try:
                # Preview thumbnails are generated for EVERY processed face
                # (not just the primary one) so the dashboard's "Live
                # Processing Flow" detail view can show any selected face's
                # crop/CLAHE thumbnails without a second request. This adds
                # only a cheap resize+JPEG-encode per face (the crop and
                # CLAHE arrays are already computed regardless) -- no
                # additional detection, cropping, or CLAHE computation.
                record = self._process_one_face(frame_bgr, face, idx, include_preview=True)
            except Exception as exc:  # noqa: BLE001 -- one face's failure must not abort the frame
                unavailable = {"available": False, "error": str(exc)}
                record = {
                    "face_id": idx,
                    "bbox": None,
                    "original": {"hsemotion": unavailable, "arcface": unavailable},
                    "clahe": {"hsemotion": unavailable, "arcface": unavailable},
                }
            face_records.append(record)

        return {
            "status": "ok",
            "faces_detected": faces_detected,
            "faces_processed": len(face_records),
            "faces_truncated": faces_truncated,
            "faces": face_records,
        }


def decode_jpeg_bytes(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return image
