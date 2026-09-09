from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import numpy as np
import pandas as pd
from tqdm import tqdm


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
MODEL_PATH = "face_landmarker.task"


class LandmarkAnalyzer:
    """
    Post-classification analysis stage: run MediaPipe Face Landmarker
    (478 landmarks: 468 mesh + 10 iris)
    on cropped faces and compute expression-proxy geometric features using
    labels from processed annotations and skin tone computed from face crops.
    """

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        annotation_file: str,
        feature_file: str,
        save_format: str = "npy",
        static_image_mode: bool = True,
        max_num_faces: int = 1,
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.annotation_file = Path(annotation_file)
        self.feature_file = Path(feature_file)
        self.save_format = save_format.lower()
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.feature_file.parent.mkdir(parents=True, exist_ok=True)

        if not os.path.exists(MODEL_PATH):
            print("Downloading face_landmarker.task...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=self.max_num_faces,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)

    @staticmethod
    def _euclidean(p1: np.ndarray, p2: np.ndarray) -> float:
        return float(np.linalg.norm(p1 - p2))

    def _save_landmarks(self, stem: str, landmarks_xy: np.ndarray) -> None:
        if self.save_format == "json":
            payload = landmarks_xy.tolist()
            out_path = self.output_dir / f"{stem}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f)
            return

        out_path = self.output_dir / f"{stem}.npy"
        np.save(out_path, landmarks_xy)

    @staticmethod
    def _compute_features(landmarks_xy: np.ndarray) -> dict[str, float]:
        # Chosen indices follow the user requirement and are normalized by IOC.
        p33 = landmarks_xy[33]
        p55 = landmarks_xy[55]
        p65 = landmarks_xy[65]
        p61 = landmarks_xy[61]
        p291 = landmarks_xy[291]
        p13 = landmarks_xy[13]
        p14 = landmarks_xy[14]
        p263 = landmarks_xy[263]

        inter_ocular_distance = max(
            LandmarkAnalyzer._euclidean(p33, p263),
            1e-8,
        )

        brow_lowering_distance = (
            (abs(float(p33[1] - p55[1])) + abs(float(p33[1] - p65[1]))) / 2.0
        ) / inter_ocular_distance

        lip_corner_distance = abs(float(p61[0] - p291[0])) / inter_ocular_distance

        mouth_openness = abs(float(p13[1] - p14[1])) / inter_ocular_distance

        return {
            "brow_lowering_distance": brow_lowering_distance,
            "lip_corner_distance": lip_corner_distance,
            "mouth_openness": mouth_openness,
            "inter_ocular_distance": inter_ocular_distance,
            "iod_px": inter_ocular_distance,
        }

    @staticmethod
    def _compute_skin_tone(img_bgr: np.ndarray) -> tuple[str, float]:
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0].astype(np.float32)
        h, w = l_channel.shape
        cy, cx = h // 2, w // 2
        half = max(int(min(h, w) * 0.4 / 2), 1)
        l_center = float(np.mean(l_channel[cy - half:cy + half, cx - half:cx + half]))
        l_weighted = (
            0.2 * float(np.mean(l_channel))
            + 0.3 * float(np.median(l_channel))
            + 0.5 * l_center
        )

        if l_weighted < 100:
            return "Dark", l_weighted
        if l_weighted < 150:
            return "Medium-Dark", l_weighted
        if l_weighted < 190:
            return "Medium-Light", l_weighted
        return "Light", l_weighted

    def _load_annotations(self) -> pd.DataFrame:
        if not self.annotation_file.exists():
            print(
                "Warning: annotation file not found. "
                "Features will be saved with unknown labels."
            )
            return pd.DataFrame()

        df = pd.read_csv(self.annotation_file)

        if "label" not in df.columns:
            df["label"] = "Unknown"

        if "filename" not in df.columns:
            df["filename"] = ""

        return df

    def run(self) -> int:
        image_paths = sorted(self.input_dir.glob("*.jpg"))
        if not image_paths:
            print(f"No face crops found in {self.input_dir}")
            return 0

        ann = self._load_annotations()

        records: list[dict[str, object]] = []
        unmatched_count = 0

        for idx, image_path in enumerate(tqdm(image_paths, desc="Face Landmarker 478")):
            image_bgr = cv2.imread(str(image_path))
            if image_bgr is None:
                continue

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB),
            )
            result = self._landmarker.detect(mp_image)

            if not result.face_landmarks:
                continue

            landmarks = result.face_landmarks[0]
            h, w = image_bgr.shape[:2]
            landmarks_xy = np.array(
                [[lm.x * w, lm.y * h] for lm in landmarks],
                dtype=np.float32,
            )

            # Tasks API returns 478 landmarks; first 468 keep mesh indexing.
            if landmarks_xy.shape[0] < 468:
                continue

            self._save_landmarks(image_path.stem, landmarks_xy)
            feats = self._compute_features(landmarks_xy)
            skin_tone, l_weighted = self._compute_skin_tone(image_bgr)

            # Annotation association is by filename identity ONLY. A
            # landmark feature must never be attributed to an emotion
            # label/confidence merely because it occupies the same row
            # index as some annotation row — that has previously produced
            # silently mislabeled feature rows when data/intermediate/faces
            # and the annotation file drift in count or order (see
            # docs/EXPERIMENT.md, formerly "Known issue"). If no
            # annotation data exists at all, every row is explicitly
            # labeled "Unknown" (see _load_annotations) rather than guessed.
            # If annotation data exists but this filename has no match,
            # the row is skipped — not silently mislabeled.
            if ann.empty:
                label = "Unknown"
                dataset_filename = ""
            else:
                matched = ann[ann["filename"] == image_path.name]
                if matched.empty:
                    unmatched_count += 1
                    continue
                row = matched.iloc[0]
                label = str(row.get("label", "Unknown"))
                dataset_filename = str(row.get("filename", ""))

            records.append(
                {
                    "face_filename": image_path.name,
                    "dataset_filename": dataset_filename,
                    "label": label,
                    "skin_tone": skin_tone,
                    "L_weighted": l_weighted,
                    **feats,
                }
            )

        self._landmarker.close()

        df = pd.DataFrame(records)
        df.to_csv(self.feature_file, index=False)

        print(f"Saved {len(df)} landmark feature rows to {self.feature_file}")
        print(f"Saved per-image landmarks (up to 478 points) to {self.output_dir}")
        if unmatched_count:
            print(
                f"WARNING: {unmatched_count} face crop(s) had no matching "
                f"annotation filename and were skipped (no row-order fallback)."
            )

        return len(df)
