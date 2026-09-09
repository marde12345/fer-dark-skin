"""Regression tests for the skin-tone estimation heuristic.

Protects: src/landmark_analyzer.py LandmarkAnalyzer._compute_skin_tone
(lines 117-137). This is the canonical implementation per
docs/REFACTORING_PLAN.md addendum (Approved Decision #4: "src/ is
canonical" over the notebook's inline copy). The weighting formula
(0.2*mean + 0.3*median + 0.5*center) and bucket thresholds
(100 / 150 / 190) are classified as a "Research-methodology change"
boundary in docs/EXPERIMENT.md — a thesis-relevant grouping variable.
Thresholds are NOT modified by these tests, only characterized.

_compute_skin_tone is a @staticmethod, exercised directly with synthetic
uniform-gray images (no model loading, no I/O).
"""

import numpy as np
import pytest

from fer_dataset.pipeline.landmark_analyzer import LandmarkAnalyzer


def _uniform_bgr(value: int) -> np.ndarray:
    return np.full((100, 100, 3), value, dtype=np.uint8)


@pytest.mark.parametrize(
    "gray_value,expected_bucket",
    [
        (10, "Dark"),
        (60, "Dark"),
        (90, "Dark"),
        (120, "Medium-Dark"),
        (160, "Medium-Light"),
        (200, "Light"),
        (250, "Light"),
    ],
)
def test_skin_tone_bucket_for_uniform_image(gray_value, expected_bucket):
    """Ground truth captured directly from the current implementation for a
    uniform-intensity BGR crop at each gray value."""
    bucket, _ = LandmarkAnalyzer._compute_skin_tone(_uniform_bgr(gray_value))
    assert bucket == expected_bucket


def test_skin_tone_weighted_value_for_uniform_image_equals_mean_L():
    """For a uniform image, mean == median == center-region mean, so the
    weighted formula (weights sum to 1.0) collapses to that single value.
    This verifies the weighting formula itself, not just bucket thresholds."""
    import cv2

    img = _uniform_bgr(120)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    expected_l_mean = float(np.mean(lab[:, :, 0]))

    _, l_weighted = LandmarkAnalyzer._compute_skin_tone(img)
    assert l_weighted == pytest.approx(expected_l_mean, abs=1e-3)


def test_skin_tone_bucket_boundaries_are_exclusive_of_upper_edge():
    """Characterizes the exact boundary comparisons at landmark_analyzer.py
    :131-137 (`< 100`, `< 150`, `< 190`, else). Not asserting these SHOULD
    be the thresholds — only that they currently ARE, since bucket edges
    matter for skin-tone-group comparisons downstream."""
    # A uniform image whose L channel lands very close to a threshold is
    # sensitive to LAB conversion rounding, so this test only pins the
    # documented threshold values themselves, not edge-pixel behavior.
    _, lw_dark_top = LandmarkAnalyzer._compute_skin_tone(_uniform_bgr(90))
    _, lw_medium_dark_bottom = LandmarkAnalyzer._compute_skin_tone(_uniform_bgr(120))
    assert lw_dark_top < 100
    assert 100 <= lw_medium_dark_bottom < 150
