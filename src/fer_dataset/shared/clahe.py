"""CLAHE preprocessing (EXP-006 "Strategy B" transform), promoted to a
single importable source of truth.

This module's two functions were originally defined notebook-locally in
`notebooks/preprocessing_experiment_executed.ipynb` (EXP-006, see
`docs/EXPERIMENT.md`), then copied verbatim into
`tools/realtime_demo/clahe_preprocessing.py` for the realtime demo. This
module is a further promotion of that same, unchanged logic into the
installable `fer_dataset` package so it has exactly one implementation,
importable by both `tools/realtime_demo/` (which now re-exports from
here, see that module's docstring) and the new Papuan V2 pipeline
(`tools/papuan_v2/*.py`), per
`docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md` §10b step 8.

No transform logic or default parameters were changed in this move
(clip_min=1.5, clip_max=3.5, l_min=60, l_max=220, tileGridSize=(8, 8)).
See `tests/test_papuan_clahe.py` for a regression test confirming this
module's output matches the values already recorded in
`data/1408-1010-intermediate/clahe_predictions.csv` (EXP-006's own
output), and confirming `tools/realtime_demo/clahe_preprocessing.py`
re-exports identically.

What EXP-006 established, and what this module reuses exactly:
  - CLAHE is applied to the LAB color space's L (lightness) channel only.
  - The clip limit is adaptively scaled per-image based on a weighted
    L-value (`l_weighted`): darker images get a higher clip limit
    (more aggressive local contrast enhancement), within [1.5, 3.5].
  - `l_weighted` combines the whole-crop mean, whole-crop median, and a
    center-region mean (0.2/0.3/0.5 weights) to reduce sensitivity to
    background pixels at the crop edges.
  - EXP-006 applied this to face-CROP images only (files under
    data/1408-1010-intermediate/faces/*.jpg), never to a full,
    un-cropped camera/video frame.
"""

from __future__ import annotations

import cv2
import numpy as np


def compute_l_weighted(img_bgr: np.ndarray) -> float:
    """Verbatim copy of EXP-006's `compute_l_weighted`
    (notebooks/preprocessing_experiment_executed.ipynb)."""
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)
    h, w = L.shape
    cy, cx = h // 2, w // 2
    half = max(int(min(h, w) * 0.4 / 2), 1)
    L_center = float(np.mean(L[cy - half : cy + half, cx - half : cx + half]))
    return 0.2 * float(np.mean(L)) + 0.3 * float(np.median(L)) + 0.5 * L_center


def apply_strategy_b_clahe(
    img_bgr: np.ndarray,
    clip_min: float = 1.5,
    clip_max: float = 3.5,
    l_min: float = 60,
    l_max: float = 220,
) -> tuple[np.ndarray, float, float]:
    """Verbatim copy of EXP-006's `apply_strategy_b_clahe`
    (notebooks/preprocessing_experiment_executed.ipynb), including its
    default parameters. Returns (clahe_image_bgr, l_weighted, clip_limit_used)."""
    l_w = compute_l_weighted(img_bgr)
    clip = clip_max - (clip_max - clip_min) * (l_w - l_min) / (l_max - l_min)
    clip = float(np.clip(clip, clip_min, clip_max))
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), l_w, clip
