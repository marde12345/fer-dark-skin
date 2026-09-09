"""Regression tests for the geometric feature formulas used in landmark analysis.

Protects: src/landmark_analyzer.py LandmarkAnalyzer._compute_features (lines
85-115) and ._euclidean (lines 69-71). These formulas and landmark indices
(33, 55, 65, 61, 291, 13, 14, 263) are documented in-code as a "user
requirement" and classified as a "Research-methodology change" boundary in
docs/EXPERIMENT.md — they must not be altered without explicit approval.

_compute_features/_euclidean are @staticmethod, so they can be exercised
directly with synthetic landmark arrays without instantiating
LandmarkAnalyzer (which would load the MediaPipe model from disk/network).
"""

import numpy as np
import pytest

from fer_dataset.pipeline.landmark_analyzer import LandmarkAnalyzer


def _synthetic_landmarks() -> np.ndarray:
    pts = np.zeros((468, 2), dtype=np.float32)
    pts[33] = [0.0, 0.0]
    pts[263] = [100.0, 0.0]
    pts[55] = [0.0, 10.0]
    pts[65] = [0.0, 20.0]
    pts[61] = [40.0, 50.0]
    pts[291] = [60.0, 50.0]
    pts[13] = [50.0, 40.0]
    pts[14] = [50.0, 55.0]
    return pts


def test_euclidean_distance():
    p1 = np.array([0.0, 0.0])
    p2 = np.array([3.0, 4.0])
    assert LandmarkAnalyzer._euclidean(p1, p2) == pytest.approx(5.0)


def test_compute_features_known_values():
    """Ground truth computed directly from the current implementation and
    hand-verified against the formulas at landmark_analyzer.py:96-115."""
    feats = LandmarkAnalyzer._compute_features(_synthetic_landmarks())

    assert feats["inter_ocular_distance"] == pytest.approx(100.0)
    assert feats["iod_px"] == pytest.approx(100.0)
    # ((|0-10| + |0-20|) / 2) / 100 = 15 / 100
    assert feats["brow_lowering_distance"] == pytest.approx(0.15)
    # |40 - 60| / 100
    assert feats["lip_corner_distance"] == pytest.approx(0.2)
    # |40 - 55| / 100
    assert feats["mouth_openness"] == pytest.approx(0.15)


def test_compute_features_returns_expected_schema():
    feats = LandmarkAnalyzer._compute_features(_synthetic_landmarks())
    assert set(feats.keys()) == {
        "brow_lowering_distance",
        "lip_corner_distance",
        "mouth_openness",
        "inter_ocular_distance",
        "iod_px",
    }


def test_inter_ocular_distance_has_floor_to_avoid_division_by_zero():
    """landmark_analyzer.py:96-99 clamps IOD to a minimum of 1e-8 when the
    two eye landmarks coincide, to avoid a divide-by-zero in the other
    features. This is existing behavior, not a new invariant."""
    pts = np.zeros((468, 2), dtype=np.float32)
    # p33 == p263 == origin; all other required indices default to origin too.
    feats = LandmarkAnalyzer._compute_features(pts)
    assert feats["inter_ocular_distance"] == pytest.approx(1e-8)
