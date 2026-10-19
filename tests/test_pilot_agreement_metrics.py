"""Unit tests for tools/papuan_v2/pilot_agreement_report.py's metric
computation, using small synthetic fixtures (no real pilot data) so the
agreement-analysis math is verified independent of whether real human
labels exist yet.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "papuan_v2"))

from pilot_agreement_report import (  # noqa: E402
    compute_model_metrics,
    confidence_vs_correctness,
    load_ai_predictions,
    load_human_labels,
    run,
)


def test_load_human_labels_rejects_blank_gt_label(tmp_path):
    path = tmp_path / "human_labels.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "gt_label", "labeled_by", "labeled_at", "notes"])
        writer.writeheader()
        writer.writerow({"image_id": "img1", "gt_label": "Happy", "labeled_by": "x", "labeled_at": "t", "notes": ""})
        writer.writerow({"image_id": "img2", "gt_label": "", "labeled_by": "", "labeled_at": "", "notes": ""})

    with pytest.raises(RuntimeError, match="empty gt_label"):
        load_human_labels(path)


def test_load_human_labels_accepts_complete_labels(tmp_path):
    path = tmp_path / "human_labels.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "gt_label", "labeled_by", "labeled_at", "notes"])
        writer.writeheader()
        writer.writerow({"image_id": "img1", "gt_label": "Happy", "labeled_by": "x", "labeled_at": "t", "notes": ""})
        writer.writerow({"image_id": "img2", "gt_label": "Sad", "labeled_by": "x", "labeled_at": "t", "notes": ""})

    result = load_human_labels(path)
    assert result == {"img1": "Happy", "img2": "Sad"}


def test_confidence_vs_correctness_basic():
    pairs = [
        ("Happy", "Happy", 0.9),
        ("Happy", "Sad", 0.6),
        ("Sad", "Sad", 0.95),
    ]
    result = confidence_vs_correctness(pairs)
    assert result["n_correct"] == 2
    assert result["n_incorrect"] == 1
    assert result["mean_confidence_when_correct"] == pytest.approx((0.9 + 0.95) / 2)
    assert result["mean_confidence_when_incorrect"] == pytest.approx(0.6)


def test_compute_model_metrics_perfect_agreement(tmp_path):
    human_labels = {"img1": "Happy", "img2": "Sad", "img3": "Happy"}
    predictions = [
        {"image_id": "img1", "ai_prediction": "Happy", "ai_confidence": "0.9", "status": "ok"},
        {"image_id": "img2", "ai_prediction": "Sad", "ai_confidence": "0.8", "status": "ok"},
        {"image_id": "img3", "ai_prediction": "Happy", "ai_confidence": "0.7", "status": "ok"},
    ]
    metrics = compute_model_metrics("test_model", predictions, human_labels, tmp_path)

    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["cohens_kappa"] == pytest.approx(1.0)
    assert metrics["n_covered"] == 3
    assert (tmp_path / "test_model.csv").exists()


def test_compute_model_metrics_excludes_non_ok_status(tmp_path):
    human_labels = {"img1": "Happy", "img2": "Sad"}
    predictions = [
        {"image_id": "img1", "ai_prediction": "Happy", "ai_confidence": "0.9", "status": "ok"},
        {"image_id": "img2", "ai_prediction": "", "ai_confidence": "", "status": "excluded_no_face"},
    ]
    metrics = compute_model_metrics("test_model", predictions, human_labels, tmp_path)

    assert metrics["n_covered"] == 1
    assert metrics["n_excluded_by_model"] == 1
    assert metrics["excluded_image_ids"] == ["img2"]


def test_compute_model_metrics_partial_disagreement_kappa_below_one(tmp_path):
    human_labels = {"img1": "Happy", "img2": "Sad", "img3": "Neutral", "img4": "Happy"}
    predictions = [
        {"image_id": "img1", "ai_prediction": "Happy", "ai_confidence": "0.9", "status": "ok"},
        {"image_id": "img2", "ai_prediction": "Neutral", "ai_confidence": "0.5", "status": "ok"},
        {"image_id": "img3", "ai_prediction": "Neutral", "ai_confidence": "0.6", "status": "ok"},
        {"image_id": "img4", "ai_prediction": "Sad", "ai_confidence": "0.4", "status": "ok"},
    ]
    metrics = compute_model_metrics("test_model", predictions, human_labels, tmp_path)

    # img1 (Happy/Happy) and img3 (Neutral/Neutral) agree; img2, img4 disagree -> 2/4.
    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["cohens_kappa"] < 1.0


def test_run_end_to_end_writes_metrics_and_report(tmp_path):
    human_labels_path = tmp_path / "human_labels.csv"
    ai_predictions_path = tmp_path / "ai_predictions.csv"
    metrics_out = tmp_path / "agreement_metrics.json"
    confusion_dir = tmp_path / "confusion_matrices"
    report_out = tmp_path / "report.md"

    with human_labels_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "gt_label", "labeled_by", "labeled_at", "notes"])
        writer.writeheader()
        writer.writerow({"image_id": "img1", "gt_label": "Happy", "labeled_by": "x", "labeled_at": "t", "notes": ""})
        writer.writerow({"image_id": "img2", "gt_label": "Sad", "labeled_by": "x", "labeled_at": "t", "notes": ""})

    with ai_predictions_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["image_id", "ai_model", "ai_prediction", "ai_confidence", "status", "generated_at"]
        )
        writer.writeheader()
        writer.writerow(
            {"image_id": "img1", "ai_model": "model_a", "ai_prediction": "Happy", "ai_confidence": "0.9", "status": "ok", "generated_at": "t"}
        )
        writer.writerow(
            {"image_id": "img2", "ai_model": "model_a", "ai_prediction": "Sad", "ai_confidence": "0.8", "status": "ok", "generated_at": "t"}
        )

    results = run(human_labels_path, ai_predictions_path, metrics_out, confusion_dir, report_out)

    assert metrics_out.exists()
    assert report_out.exists()
    assert (confusion_dir / "model_a.csv").exists()

    persisted = json.loads(metrics_out.read_text())
    assert persisted["models"]["model_a"]["accuracy"] == 1.0
    # Script must never auto-select a winner -- the decision text is explicit that it's separate.
    assert "EXP-PAP-004" in report_out.read_text()
    assert "Not made by this script" in report_out.read_text()
