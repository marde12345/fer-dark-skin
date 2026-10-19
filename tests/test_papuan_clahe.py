"""Regression tests for the promoted CLAHE module
(src/fer_dataset/shared/clahe.py), part of the Papuan V2 pilot workflow
(docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md §10b step 8).

Confirms:
  1. The promoted module's output matches EXP-006's own recorded
     reference values (data/1408-1010-intermediate/clahe_predictions.csv)
     on real legacy face crops -- i.e. the move did not change behavior.
  2. tools/realtime_demo/clahe_preprocessing.py, now a re-export shim,
     produces byte-identical output to the promoted module (no
     duplicated implementation left behind).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from fer_dataset.shared.clahe import apply_strategy_b_clahe, compute_l_weighted

REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_FACES_DIR = REPO_ROOT / "data" / "1408-1010-intermediate" / "faces"
LEGACY_CLAHE_CSV = REPO_ROOT / "data" / "1408-1010-intermediate" / "clahe_predictions.csv"


def _load_reference_rows(n: int) -> list[dict]:
    with LEGACY_CLAHE_CSV.open() as f:
        rows = list(csv.DictReader(f))
    return rows[:n]


@pytest.mark.skipif(
    not LEGACY_FACES_DIR.exists() or not LEGACY_CLAHE_CSV.exists(),
    reason="legacy data/1408-1010-intermediate not present in this environment",
)
def test_promoted_clahe_matches_exp006_reference_values():
    rows = _load_reference_rows(5)
    assert rows, "expected at least one reference row in clahe_predictions.csv"

    checked = 0
    for row in rows:
        img_path = LEGACY_FACES_DIR / row["filename"]
        if not img_path.exists():
            continue
        image = cv2.imread(str(img_path))
        assert image is not None

        _clahe_img, l_weighted, clip_used = apply_strategy_b_clahe(image)

        assert l_weighted == pytest.approx(float(row["l_weighted"]), rel=1e-4)
        assert clip_used == pytest.approx(float(row["clip_limit_used"]), rel=1e-4)
        checked += 1

    assert checked > 0, "no reference face crops were found on disk to verify against"


def test_compute_l_weighted_is_deterministic():
    rng = np.random.default_rng(42)
    image = rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)

    first = compute_l_weighted(image)
    second = compute_l_weighted(image)

    assert first == second


def test_apply_strategy_b_clahe_clip_limit_is_bounded():
    rng = np.random.default_rng(7)
    dark_image = np.clip(rng.normal(20, 5, size=(64, 64, 3)), 0, 255).astype(np.uint8)
    bright_image = np.clip(rng.normal(240, 5, size=(64, 64, 3)), 0, 255).astype(np.uint8)

    _img, _l_w, clip_dark = apply_strategy_b_clahe(dark_image)
    _img, _l_w, clip_bright = apply_strategy_b_clahe(bright_image)

    assert 1.5 <= clip_dark <= 3.5
    assert 1.5 <= clip_bright <= 3.5
    # Darker images should receive a clip limit >= that of brighter images.
    assert clip_dark >= clip_bright


def test_realtime_demo_shim_reexports_identical_function(monkeypatch):
    demo_dir = REPO_ROOT / "tools" / "realtime_demo"
    monkeypatch.syspath_prepend(str(demo_dir))
    # Force a fresh import in case a stale module is cached under the same name.
    sys.modules.pop("clahe_preprocessing", None)
    import clahe_preprocessing as demo_shim  # noqa: E402

    assert demo_shim.apply_strategy_b_clahe is apply_strategy_b_clahe
    assert demo_shim.compute_l_weighted is compute_l_weighted
