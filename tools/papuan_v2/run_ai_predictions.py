"""EXP-PAP-003 (part 1): run both AI-assisted-annotation candidates on
the pilot set.

Candidate A: CLAHE image -> HSEmotion (enet_b0_8_best_vgaf)
Candidate B: CLAHE image -> ArcFace embedding (InsightFace buffalo_l
             recognition sub-model) -> LogisticRegression
             (tools/realtime_demo/artifacts/arcface_lr_demo_model.joblib,
             trained per tools/train_arcface_classifier.py / R6)

Both candidates run on data/papuan_v2/pilot/images/*.jpg (the CLAHE
pilot images written by sample_pilot.py) and write ONLY to
experiments/EXP-PAP-004/ai_predictions.csv. This script never reads or
writes experiments/EXP-PAP-004/human_labels.csv -- AI predictions must
never influence or overwrite human ground truth (approved proposal,
"Important independence constraints").

Both candidates run on the EXACT SAME 150 pilot crop images -- neither
candidate performs a second face-detection pass on the already-cropped
image. This was NOT true in the first implementation of this script: it
originally reused tools/extract_arcface_embeddings.py's ArcFaceEmbedder,
which re-runs InsightFace's own face DETECTOR on the crop (needed only
to obtain 5-point landmarks for `face_align.norm_crop`) and excluded any
crop where that re-detection found zero or multiple faces -- 50/150
(33%) of the pilot set was excluded this way, purely as an artifact of
re-detecting on an already-tightly-cropped image, not because ArcFace+LR
is a weaker annotation assistant. That result was never used as
evidence and is documented only as an implementation note (see
docs/EXPERIMENT.md EXP-PAP-003).

Fix: Candidate B now calls the recognition sub-model's own
`ArcFaceONNX.get_feat()` directly on the pilot crop (confirmed by
reading insightface/model_zoo/arcface_onnx.py: `get_feat()` internally
resizes via `cv2.dnn.blobFromImages` to the model's expected 112x112
input and does not require a Face/landmark object at all -- only
`ArcFaceONNX.get()`, which this script no longer calls, requires
detection-derived landmarks for `face_align.norm_crop`). No face
detector is loaded for this path at all (`allowed_modules=["recognition"]`),
so a second detection is structurally impossible, not just avoided by
convention. The resulting embedding is L2-normalized identically to
`Face.normed_embedding` (`embedding / l2_norm(embedding)`) before being
passed to the same trained LogisticRegression classifier.

Caveat (recorded, not hidden): the classifier was trained on embeddings
produced through InsightFace's full detect+landmark-align pipeline
(tools/extract_arcface_embeddings.py, used to build
manual_labels_export.csv-based training data). This direct-get_feat path
skips that landmark-based alignment and instead relies on the crop
already being face-centered (FaceDetector's own 20%-padded bbox crop).
This is a distributional difference from the classifier's training input
worth stating explicitly in the EXP-PAP-004 decision -- it trades a
selection-bias problem (50 crops silently excluded) for a possible
alignment-mismatch problem (all 150 crops scored, but on slightly
different input statistics than training). Both candidates' agreement
numbers should be read with this in mind.

Candidate B's class set is fixed by the existing demo model to
["Fear", "Happy", "Neutral", "Sad", "Surprise"] (5 classes) --
narrower than HSEmotion's 8 classes. This asymmetry is a known
limitation, surfaced in the agreement report rather than hidden.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import insightface
import joblib
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from hsemotion_onnx.facial_emotions import HSEmotionRecognizer  # noqa: E402

PILOT_IMAGES_DIR = REPO_ROOT / "data" / "papuan_v2" / "pilot" / "images"
DEMO_MODEL_PATH = REPO_ROOT / "tools" / "realtime_demo" / "artifacts" / "arcface_lr_demo_model.joblib"
DEMO_CLASS_ORDER = ["Fear", "Happy", "Neutral", "Sad", "Surprise"]
HSEMOTION_MODEL_NAME = "enet_b0_8_best_vgaf"
OUTPUT_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "ai_predictions.csv"

FIELDNAMES = [
    "image_id",
    "ai_model",
    "ai_prediction",
    "ai_confidence",
    "status",
    "generated_at",
]


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - np.max(logits)
    exp = np.exp(logits)
    return exp / exp.sum()


def run_hsemotion_clahe(image_paths: list[Path]) -> list[dict]:
    model = HSEmotionRecognizer(model_name=HSEMOTION_MODEL_NAME)
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for path in image_paths:
        image = cv2.imread(str(path))
        if image is None:
            rows.append(
                {
                    "image_id": path.stem,
                    "ai_model": "hsemotion_clahe",
                    "ai_prediction": "",
                    "ai_confidence": "",
                    "status": "invalid_image",
                    "generated_at": now,
                }
            )
            continue
        try:
            emotion, logits = model.predict_emotions(image)
            confidence = float(softmax(np.asarray(logits)).max())
            rows.append(
                {
                    "image_id": path.stem,
                    "ai_model": "hsemotion_clahe",
                    "ai_prediction": emotion,
                    "ai_confidence": confidence,
                    "status": "ok",
                    "generated_at": now,
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "image_id": path.stem,
                    "ai_model": "hsemotion_clahe",
                    "ai_prediction": "",
                    "ai_confidence": "",
                    "status": f"error:{exc}",
                    "generated_at": now,
                }
            )
    return rows


class DirectArcFaceEmbedder:
    """Recognition-only ArcFace embedder: loads ONLY the buffalo_l
    recognition sub-model (w600k_r50.onnx) directly via InsightFace's
    own `ArcFaceONNX` class -- not through `FaceAnalysis`, which asserts
    a detection model must also be loaded (`assert 'detection' in
    self.models`, insightface/app/face_analysis.py) and would otherwise
    force us to carry a detector we deliberately never call. With no
    detection model loaded at all, a second face detection on an
    already-cropped pilot image is structurally impossible here, not
    just avoided by convention. Embeds directly via
    `ArcFaceONNX.get_feat()`, which InsightFace itself documents as
    operating on an already-aligned/cropped image with no landmark
    input required (see module docstring for the source read that
    confirmed this)."""

    EMBEDDING_DIM = 512

    def __init__(self) -> None:
        model_path = Path.home() / ".insightface" / "models" / "buffalo_l" / "w600k_r50.onnx"
        if not model_path.exists():
            raise FileNotFoundError(
                f"{model_path} not found -- run any script that loads the buffalo_l "
                "bundle once (e.g. tools/extract_arcface_embeddings.py) to trigger "
                "InsightFace's own model download, then retry."
            )
        self.recognition_model = insightface.model_zoo.get_model(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        self.recognition_model.prepare(ctx_id=0)

    def embed_image(self, image: np.ndarray) -> tuple[str, np.ndarray | None]:
        if image is None or image.size == 0:
            return "excluded_invalid_image", None
        try:
            raw = self.recognition_model.get_feat(image).flatten()
        except Exception:  # noqa: BLE001
            return "excluded_embedding_error", None

        raw = np.asarray(raw, dtype=np.float32)
        if raw.shape != (self.EMBEDDING_DIM,) or not np.all(np.isfinite(raw)):
            return "excluded_embedding_error", None

        norm = float(np.linalg.norm(raw))
        if norm == 0.0:
            return "excluded_embedding_error", None

        return "embedded", raw / norm


def run_arcface_lr_clahe(image_paths: list[Path]) -> list[dict]:
    if not DEMO_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"{DEMO_MODEL_PATH} not found -- run "
            "`uv run python tools/realtime_demo/build_demo_classifier.py` first."
        )
    classifier = joblib.load(DEMO_MODEL_PATH)
    embedder = DirectArcFaceEmbedder()
    now = datetime.now(timezone.utc).isoformat()

    rows = []
    for path in image_paths:
        image = cv2.imread(str(path))
        if image is None:
            rows.append(
                {
                    "image_id": path.stem,
                    "ai_model": "arcface_lr_clahe",
                    "ai_prediction": "",
                    "ai_confidence": "",
                    "status": "invalid_image",
                    "generated_at": now,
                }
            )
            continue

        status, embedding = embedder.embed_image(image)
        if status != "embedded":
            rows.append(
                {
                    "image_id": path.stem,
                    "ai_model": "arcface_lr_clahe",
                    "ai_prediction": "",
                    "ai_confidence": "",
                    "status": status,
                    "generated_at": now,
                }
            )
            continue

        probs = classifier.predict_proba(embedding.reshape(1, -1))[0]
        pred_idx = int(np.argmax(probs))
        rows.append(
            {
                "image_id": path.stem,
                "ai_model": "arcface_lr_clahe",
                "ai_prediction": DEMO_CLASS_ORDER[pred_idx],
                "ai_confidence": float(probs[pred_idx]),
                "status": "ok",
                "generated_at": now,
            }
        )
    return rows


def run(pilot_images_dir: Path, output_path: Path) -> int:
    image_paths = sorted(pilot_images_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"No pilot images found in {pilot_images_dir} -- run sample_pilot.py first.")

    print(f"Running Candidate A (HSEmotion + CLAHE) on {len(image_paths)} pilot images...")
    rows_a = run_hsemotion_clahe(image_paths)

    print(f"Running Candidate B (ArcFace + LogisticRegression + CLAHE) on {len(image_paths)} pilot images...")
    rows_b = run_arcface_lr_clahe(image_paths)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_a)
        writer.writerows(rows_b)

    print(f"Wrote {len(rows_a) + len(rows_b)} predictions ({len(rows_a)} + {len(rows_b)}) to {output_path}")
    return len(rows_a) + len(rows_b)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-images-dir", type=Path, default=PILOT_IMAGES_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run(args.pilot_images_dir, args.output)


if __name__ == "__main__":
    main()
