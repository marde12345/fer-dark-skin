"""Step 2+3 for the v2 extraction pool: frontality proxy + visibility check
+ QC (blur/size) filtering. Reads per_face_sample_manifest_v2.csv and the
raw landmark JSONs written by run_extraction_v2.py.

Frontality method (documented, single, explainable):
  Using landmark_3d_68 (indices per the standard 68-point scheme):
    - left eye corner ~= 36 (outer) .. 39 (inner); right eye ~= 42(inner)..45(outer)
    - nose tip = 30
  We compute the horizontal midpoint of the two eye-OUTER-corners (36, 45)
  as `eye_mid_x`, and compare nose tip x (30) to that midpoint, normalized
  by the inter-ocular distance (|x45 - x36|):
      frontality_offset = (x30 - eye_mid_x) / (x45 - x36)
  frontality_offset ~ 0 => nose centered between eyes => frontal.
  |frontality_offset| large => nose shifted toward one eye => turned/profile.
  frontality_score = 1 - min(1, |frontality_offset| / OFFSET_PROFILE_THRESHOLD)
  (clipped to [0,1], 1=frontal, 0=profile-ish)

Visibility check: for the 42 target landmark indices (17-26 brows, 36-47
eyes, 48-67 mouth), flag `visibility_flag=CLIPPED` if any of those points
fall within VISIBILITY_MARGIN_PX of the crop boundary (0,0)-(crop_w,crop_h)
in crop-local coordinates (landmark coords are in ORIGINAL frame coords in
our raw JSON since they come straight from face.landmark_3d_68 before any
crop offset is subtracted here -- we subtract crop_px1/crop_py1 to get
crop-local coords for this check).

QC: blur variance via cv2.Laplacian(...).var() on grayscale, min(w,h) dim.
Starting thresholds reused from v1 (blur>75, min_dim>=60), but this script
ALSO reports the v2 pool's own distribution before applying them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
REPORT_DIR = REPO / "docs/reports/extraction_v2_2026-10-19"
FACE_MANIFEST = REPORT_DIR / "per_face_sample_manifest_v2.csv"
OUT_MANIFEST = REPORT_DIR / "per_face_sample_manifest_v2_qc.csv"

OFFSET_PROFILE_THRESHOLD = 0.6  # |offset| >= this treated as profile (score 0)
VISIBILITY_MARGIN_PX = 3
BLUR_THRESHOLD = 75.0
MIN_DIM_THRESHOLD = 60

BROW_EYE_MOUTH_IDX = list(range(17, 27)) + list(range(36, 48)) + list(range(48, 68))
assert len(BROW_EYE_MOUTH_IDX) == 42


def frontality_for(lm: np.ndarray) -> float:
    x36, x45 = lm[36, 0], lm[45, 0]
    x30 = lm[30, 0]
    eye_mid_x = (x36 + x45) / 2.0
    denom = (x45 - x36)
    if abs(denom) < 1e-6:
        return float("nan")
    offset = (x30 - eye_mid_x) / denom
    score = 1.0 - min(1.0, abs(offset) / OFFSET_PROFILE_THRESHOLD)
    return round(max(0.0, score), 4), round(float(offset), 4)


def visibility_for(lm: np.ndarray, crop_px1: int, crop_py1: int, crop_w: int, crop_h: int) -> str:
    clipped = False
    for i in BROW_EYE_MOUTH_IDX:
        x = lm[i, 0] - crop_px1
        y = lm[i, 1] - crop_py1
        if x < VISIBILITY_MARGIN_PX or y < VISIBILITY_MARGIN_PX or x > crop_w - VISIBILITY_MARGIN_PX or y > crop_h - VISIBILITY_MARGIN_PX:
            clipped = True
            break
    return "CLIPPED_LIKELY_OCCLUDED" if clipped else "OK"


def main():
    df = pd.read_csv(FACE_MANIFEST)
    print(f"loaded {len(df)} face rows")

    frontality_scores = []
    frontality_offsets = []
    visibility_flags = []
    blur_vars = []
    min_dims = []

    for _, row in df.iterrows():
        lm_path = row["landmark_raw_path"]
        if lm_path == "NOT_AVAILABLE" or not isinstance(lm_path, str):
            frontality_scores.append(float("nan"))
            frontality_offsets.append(float("nan"))
            visibility_flags.append("NO_LANDMARKS")
        else:
            with open(REPO / lm_path) as f:
                data = json.load(f)
            lm = np.array(data["landmark_3d_68"])
            score, offset = frontality_for(lm)
            frontality_scores.append(score)
            frontality_offsets.append(offset)
            vis = visibility_for(lm, data["crop_px1"], data["crop_py1"], row["crop_width"], row["crop_height"])
            visibility_flags.append(vis)

        img_path = REPO / row["original_path"]
        img = cv2.imread(str(img_path))
        if img is None:
            blur_vars.append(float("nan"))
            min_dims.append(0)
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_vars.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
            min_dims.append(int(min(img.shape[0], img.shape[1])))

    df["frontality_score"] = frontality_scores
    df["frontality_offset"] = frontality_offsets
    df["visibility_flag"] = visibility_flags
    df["qc_blur_variance"] = blur_vars
    df["qc_min_dim"] = min_dims

    df["pass_size_blur"] = (df["qc_blur_variance"] > BLUR_THRESHOLD) & (df["qc_min_dim"] >= MIN_DIM_THRESHOLD)

    def frontal_bucket(s):
        if pd.isna(s):
            return "UNKNOWN"
        if s >= 0.7:
            return "FRONTAL"
        if s >= 0.4:
            return "NEAR_FRONTAL"
        return "PROFILE"

    df["frontal_bucket"] = df["frontality_score"].apply(frontal_bucket)
    df["pass_frontal_visibility"] = df["frontal_bucket"].isin(["FRONTAL", "NEAR_FRONTAL"]) & (df["visibility_flag"] == "OK")
    df["pass_all"] = df["pass_size_blur"] & df["pass_frontal_visibility"]

    df.to_csv(OUT_MANIFEST, index=False)

    print("\n--- Distributions (v2 pool, own data) ---")
    print(df["qc_blur_variance"].describe())
    print(df["qc_min_dim"].describe())
    print(df["frontality_score"].describe())
    print("\nvisibility_flag counts:\n", df["visibility_flag"].value_counts())
    print("\nfrontal_bucket counts:\n", df["frontal_bucket"].value_counts())
    print("\nFunnel:")
    print("faces total:", len(df))
    print("pass_size_blur:", df["pass_size_blur"].sum())
    print("pass_frontal_visibility:", df["pass_frontal_visibility"].sum())
    print("pass_all (final candidates):", df["pass_all"].sum())


if __name__ == "__main__":
    main()
