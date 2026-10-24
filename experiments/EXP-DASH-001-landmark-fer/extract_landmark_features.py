"""EXP-DASH-001 (dashboard demo experiment, NOT a formal thesis experiment):
extract 68-point landmarks and 7 engineered geometric features for every
usable, human-labeled face crop, for training a landmark-based expression
classifier.

Ground truth: data/1408-1010-intermediate/manual_labels_export.csv's
`gt_label` column ONLY -- the same, already-established label source used
by this project's own real thesis classifier (tools/train_arcface_classifier.py).
HSEmotion's `model_label` column in that file is never used as a target
(that would be circular/pseudo-labeling, exactly what this file must NOT do).
"Ambiguous" rows and rows with no/blank label are excluded, matching that
script's own convention.

Landmark extraction: InsightFace's `landmark_3d_68` sub-model (buffalo_l),
the exact same method already used and documented in
docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md and
experiments/EXP-PAP-005/gen_batch3_predictions.py -- skip re-detection on
the already-tight face crop (SCRFD fails on crops this small, documented
repeatedly in this repo), construct a synthetic full-crop bounding box, and
call the landmark sub-model directly. Only x, y are kept (z discarded).

Scheme-compatibility assumption (explicitly documented, not independently
verified pixel-for-pixel): InsightFace's landmark_3d_68 and face-api.js's
68-point faceLandmark68Net both follow the standard ibug-300W 68-point
ordering (jaw 0-16, right brow 17-21, left brow 22-26, nose bridge 27-30,
nose bottom 31-35, right eye 36-41, left eye 42-47, outer lip 48-59, inner
lip 60-67). This script and the browser-side feature extractor
(dashboard/landmark_expression_classifier.js) therefore use identical
point indices and formulas. If the two detectors' underlying training data
caused any systematic ordering/placement differences, feature values
could differ between training (this script) and live inference (browser) --
this is a disclosed limitation, not something this experiment claims to
have ruled out.

Output: experiments/EXP-DASH-001-landmark-fer/landmark_classifier_features.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.app.common import Face

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAME_INDEX_PATTERN = re.compile(r"^frame_(\d+)_face\d+$")

DEFAULT_MANUAL_LABELS = REPO_ROOT / "data/1408-1010-intermediate/manual_labels_export.csv"
DEFAULT_FACES_DIR = REPO_ROOT / "data/1408-1010-intermediate/faces"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "landmark_classifier_features.csv"

# ibug-300W 68-point index ranges, shared verbatim with
# dashboard/realtime_landmark_demo.js's REGIONS and
# dashboard/landmark_expression_classifier.js's feature extractor.
RIGHT_EYE = list(range(36, 42))
LEFT_EYE = list(range(42, 48))
RIGHT_BROW = list(range(17, 22))
LEFT_BROW = list(range(22, 27))
MOUTH_OUTER_LEFT_CORNER = 48
MOUTH_OUTER_RIGHT_CORNER = 54
MOUTH_OUTER_TOP_CENTER = 51
INNER_LIP_TOP = 62
INNER_LIP_BOTTOM = 66
CHIN = 8


def parse_frame_index(stem: str) -> int | None:
    match = FRAME_INDEX_PATTERN.match(stem)
    return int(match.group(1)) if match else None


def load_ground_truth_labels(manual_labels_csv: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    with manual_labels_csv.open() as f:
        for row in csv.DictReader(f):
            result[row["filename"]] = row["gt_label"]
    return result


def _dist(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1 - p2))


def compute_features(landmarks_xy: np.ndarray) -> dict[str, float] | None:
    """landmarks_xy: (68, 2) array, pixel coordinates. Returns the 7
    normalized geometric features, or None if inter-ocular distance is
    degenerate (would divide by ~0)."""
    right_eye_center = landmarks_xy[RIGHT_EYE].mean(axis=0)
    left_eye_center = landmarks_xy[LEFT_EYE].mean(axis=0)
    iod = _dist(right_eye_center, left_eye_center)
    if iod < 1e-3:
        return None

    def ear(eye_idx: list[int]) -> float:
        p = landmarks_xy[eye_idx]
        vertical = _dist(p[1], p[5]) + _dist(p[2], p[4])
        horizontal = _dist(p[0], p[3])
        if horizontal < 1e-6:
            return 0.0
        return vertical / (2.0 * horizontal)

    ear_mean = (ear(RIGHT_EYE) + ear(LEFT_EYE)) / 2.0

    mouth_openness = _dist(landmarks_xy[INNER_LIP_TOP], landmarks_xy[INNER_LIP_BOTTOM]) / iod
    mouth_width_ratio = _dist(landmarks_xy[MOUTH_OUTER_LEFT_CORNER], landmarks_xy[MOUTH_OUTER_RIGHT_CORNER]) / iod

    corner_mid_y = (landmarks_xy[MOUTH_OUTER_LEFT_CORNER][1] + landmarks_xy[MOUTH_OUTER_RIGHT_CORNER][1]) / 2.0
    vertical_offset = landmarks_xy[MOUTH_OUTER_TOP_CENTER][1] - corner_mid_y
    half_width = _dist(landmarks_xy[MOUTH_OUTER_LEFT_CORNER], landmarks_xy[MOUTH_OUTER_RIGHT_CORNER]) / 2.0
    lip_corner_angle = math.atan2(vertical_offset, half_width) if half_width > 1e-6 else 0.0

    right_brow_mid = landmarks_xy[RIGHT_BROW].mean(axis=0)
    left_brow_mid = landmarks_xy[LEFT_BROW].mean(axis=0)
    brow_eye_dist_mean = (_dist(right_brow_mid, right_eye_center) + _dist(left_brow_mid, left_eye_center)) / (2.0 * iod)

    inner_brow_distance = _dist(landmarks_xy[21], landmarks_xy[22]) / iod

    mouth_center = (landmarks_xy[MOUTH_OUTER_TOP_CENTER] + landmarks_xy[57]) / 2.0
    jaw_drop = _dist(landmarks_xy[CHIN], mouth_center) / iod

    return {
        "ear_mean": ear_mean,
        "mouth_openness": mouth_openness,
        "mouth_width_ratio": mouth_width_ratio,
        "lip_corner_angle": lip_corner_angle,
        "brow_eye_dist_mean": brow_eye_dist_mean,
        "inner_brow_distance": inner_brow_distance,
        "jaw_drop": jaw_drop,
    }


FEATURE_NAMES = [
    "ear_mean",
    "mouth_openness",
    "mouth_width_ratio",
    "lip_corner_angle",
    "brow_eye_dist_mean",
    "inner_brow_distance",
    "jaw_drop",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual-labels", type=Path, default=DEFAULT_MANUAL_LABELS)
    parser.add_argument("--faces-dir", type=Path, default=DEFAULT_FACES_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gt_labels = load_ground_truth_labels(args.manual_labels)

    app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark_3d_68"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    lmk_model = app.models["landmark_3d_68"]

    exclusions: dict[str, int] = {}
    rows: list[dict] = []

    for face_filename, gt_label in gt_labels.items():
        label = (gt_label or "").strip()
        if label == "" or label.lower() == "nan":
            exclusions["excluded_missing_label"] = exclusions.get("excluded_missing_label", 0) + 1
            continue
        if label == "Ambiguous":
            exclusions["excluded_ambiguous_label"] = exclusions.get("excluded_ambiguous_label", 0) + 1
            continue

        stem = Path(face_filename).stem
        frame_index = parse_frame_index(stem)
        if frame_index is None:
            exclusions["excluded_unparseable_filename"] = exclusions.get("excluded_unparseable_filename", 0) + 1
            continue

        img_path = args.faces_dir / face_filename
        img = cv2.imread(str(img_path))
        if img is None:
            exclusions["excluded_missing_crop"] = exclusions.get("excluded_missing_crop", 0) + 1
            continue

        h, w = img.shape[:2]
        face = Face(bbox=np.array([0, 0, w, h], dtype=np.float32), kps=None, det_score=1.0)
        lmk_model.get(img, face)
        landmarks_xy = face.landmark_3d_68[:, :2]

        features = compute_features(landmarks_xy)
        if features is None:
            exclusions["excluded_degenerate_landmarks"] = exclusions.get("excluded_degenerate_landmarks", 0) + 1
            continue

        row = {
            "face_filename": face_filename,
            "frame_index": frame_index,
            "gt_label": label,
        }
        row.update(features)
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["face_filename", "frame_index", "gt_label"] + FEATURE_NAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"wrote {len(rows)} rows -> {args.output}")
    print("exclusions:", exclusions)
    from collections import Counter

    print("label distribution (usable, pre rare-class filtering):", Counter(r["gt_label"] for r in rows))


if __name__ == "__main__":
    main()
