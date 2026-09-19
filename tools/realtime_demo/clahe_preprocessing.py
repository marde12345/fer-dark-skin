"""CLAHE preprocessing, reused verbatim from EXP-006.

EXP-006 ("Preprocessing Experiment: Strategy B CLAHE vs. False-Angry
Rate", docs/EXPERIMENT.md) defines `compute_l_weighted` and
`apply_strategy_b_clahe` as notebook-local functions in
notebooks/preprocessing_experiment_executed.ipynb (and the unexecuted
counterpart notebooks/preprocessing_experiment.ipynb). Because they are
notebook-local (not part of the importable `src/` package), they cannot
be imported directly -- the two functions below are copied here
VERBATIM, including their default parameters
(clip_min=1.5, clip_max=3.5, l_min=60, l_max=220, tileGridSize=(8, 8)),
with no change to the transform logic or defaults.

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
    un-cropped camera/video frame -- see docs/EXPERIMENT.md EXP-006 and
    the notebook's own preprocessing cell, which calls
    `apply_strategy_b_clahe(img_bgr)` directly on each loaded crop file.

What this demo REUSES exactly: both functions, unchanged, applied to
the same kind of input (a face-crop image) EXP-006 used them on.

What this demo EXTENDS beyond EXP-006 (must not be presented as
established research evidence -- see tools/realtime_demo/README.md):
EXP-006 only ever re-classified CLAHE-adjusted crops with HSEmotion.
It never tested a CLAHE-adjusted crop through the ArcFace + Logistic
Regression pipeline (which did not yet exist at the time EXP-006 ran).
Applying the identical, already-established crop-level CLAHE transform
before ArcFace's own internal alignment is a natural, documented
extension for this demo -- not a claim that EXP-006 evaluated it.
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
