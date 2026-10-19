"""EXP-PAP-003 (part 2): agreement analysis between each AI-assisted-
annotation candidate and independently human-labeled pilot ground truth.

Reads experiments/EXP-PAP-004/human_labels.csv (human ground truth,
gt_label must be non-empty for every row) and
experiments/EXP-PAP-004/ai_predictions.csv (both candidates' raw
predictions), and computes, per candidate:
  - accuracy
  - macro-F1
  - Cohen's kappa (chance-corrected agreement)
  - confusion matrix
  - confidence-vs-correctness breakdown (mean AI confidence for
    correct vs. incorrect predictions, and accuracy within confidence
    bins)

Writes experiments/EXP-PAP-004/agreement_metrics.json,
experiments/EXP-PAP-004/confusion_matrices/*.csv, and
experiments/EXP-PAP-004/report.md.

This script NEVER writes to human_labels.csv -- it only reads it. If
human_labels.csv has any blank gt_label rows, it refuses to run (the
pilot ground truth must be complete before agreement is computed,
per "Human labels -> independent ground truth", approved proposal).

The report explicitly states this is a usefulness-as-an-annotation-
-assistant analysis, not a "which model is better" ranking, and the
EXP-PAP-004 selection decision (docs/EXPERIMENT.md) must be written
separately, referencing this report -- this script does not auto-select
a winner.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = REPO_ROOT / "experiments" / "EXP-PAP-004"
DEFAULT_HUMAN_LABELS = EXP_DIR / "human_labels.csv"
DEFAULT_AI_PREDICTIONS = EXP_DIR / "ai_predictions.csv"
DEFAULT_METRICS_OUT = EXP_DIR / "agreement_metrics.json"
DEFAULT_CONFUSION_DIR = EXP_DIR / "confusion_matrices"
DEFAULT_REPORT_OUT = EXP_DIR / "report.md"
CONFIDENCE_BINS = [0.0, 0.5, 0.7, 0.85, 1.0001]


def _relpath(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_human_labels(path: Path) -> dict[str, str]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"{path} is empty.")
    blanks = [r["image_id"] for r in rows if not r.get("gt_label", "").strip()]
    if blanks:
        raise RuntimeError(
            f"{path} has {len(blanks)} row(s) with an empty gt_label (e.g. {blanks[:5]}). "
            "Human labeling must be complete and independent before agreement analysis can run."
        )
    return {r["image_id"]: r["gt_label"].strip() for r in rows}


def load_ai_predictions(path: Path) -> dict[str, list[dict]]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_model[row["ai_model"]].append(row)
    return dict(by_model)


def confidence_vs_correctness(pairs: list[tuple[str, str, float]]) -> dict:
    correct_confidences = [c for gt, pred, c in pairs if gt == pred]
    incorrect_confidences = [c for gt, pred, c in pairs if gt != pred]

    bins = []
    for lo, hi in zip(CONFIDENCE_BINS[:-1], CONFIDENCE_BINS[1:]):
        in_bin = [(gt, pred) for gt, pred, c in pairs if lo <= c < hi]
        if not in_bin:
            bins.append({"range": [lo, hi], "n": 0, "accuracy": None})
            continue
        acc = sum(1 for gt, pred in in_bin if gt == pred) / len(in_bin)
        bins.append({"range": [lo, hi], "n": len(in_bin), "accuracy": acc})

    return {
        "mean_confidence_when_correct": float(np.mean(correct_confidences)) if correct_confidences else None,
        "mean_confidence_when_incorrect": float(np.mean(incorrect_confidences)) if incorrect_confidences else None,
        "n_correct": len(correct_confidences),
        "n_incorrect": len(incorrect_confidences),
        "accuracy_by_confidence_bin": bins,
    }


def compute_model_metrics(
    model_name: str,
    predictions: list[dict],
    human_labels: dict[str, str],
    confusion_dir: Path,
) -> dict:
    ok_predictions = {r["image_id"]: r for r in predictions if r["status"] == "ok"}
    covered_ids = sorted(set(ok_predictions) & set(human_labels))
    excluded_ids = sorted(set(r["image_id"] for r in predictions) - set(ok_predictions))

    if not covered_ids:
        return {
            "model": model_name,
            "n_pilot_images": len(predictions),
            "n_covered": 0,
            "n_excluded_by_model": len(excluded_ids),
            "error": "No overlapping (gt_label, ok prediction) pairs -- cannot compute metrics.",
        }

    y_true = [human_labels[i] for i in covered_ids]
    y_pred = [ok_predictions[i]["ai_prediction"] for i in covered_ids]
    confidences = [float(ok_predictions[i]["ai_confidence"]) for i in covered_ids]

    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    confusion_dir.mkdir(parents=True, exist_ok=True)
    cm_path = confusion_dir / f"{model_name}.csv"
    with cm_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["gt_label\\ai_prediction"] + labels)
        for label, row in zip(labels, cm):
            writer.writerow([label] + list(row))

    metrics = {
        "model": model_name,
        "n_pilot_images": len(predictions),
        "n_covered": len(covered_ids),
        "n_excluded_by_model": len(excluded_ids),
        "excluded_image_ids": excluded_ids,
        "class_labels_observed": labels,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0)),
        "cohens_kappa": float(cohen_kappa_score(y_true, y_pred, labels=labels)),
        "confusion_matrix_path": _relpath(cm_path),
        "confidence_vs_correctness": confidence_vs_correctness(list(zip(y_true, y_pred, confidences))),
    }
    return metrics


def run(
    human_labels_path: Path,
    ai_predictions_path: Path,
    metrics_out: Path,
    confusion_dir: Path,
    report_out: Path,
) -> dict:
    human_labels = load_human_labels(human_labels_path)
    predictions_by_model = load_ai_predictions(ai_predictions_path)

    results = {
        "experiment_id": "EXP-PAP-003",
        "purpose": (
            "Determine whether either candidate is sufficiently useful as an "
            "AI annotation assistant, NOT to declare one model better overall. "
            "The EXP-PAP-004 selection decision must be written separately in "
            "docs/EXPERIMENT.md, referencing this report."
        ),
        "n_human_labeled_pilot_images": len(human_labels),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": {},
    }

    for model_name, predictions in predictions_by_model.items():
        results["models"][model_name] = compute_model_metrics(
            model_name, predictions, human_labels, confusion_dir
        )

    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    metrics_out.write_text(json.dumps(results, indent=2))

    _write_report_md(results, report_out)

    print(f"Wrote {metrics_out}")
    print(f"Wrote {report_out}")
    return results


def _write_report_md(results: dict, report_out: Path) -> None:
    lines = [
        "# EXP-PAP-003 — Pilot Annotation-Assistant Agreement Report",
        "",
        f"Generated: {results['generated_at']}",
        f"Pilot images with complete human labels: {results['n_human_labeled_pilot_images']}",
        "",
        "## Purpose",
        "",
        results["purpose"],
        "",
        "## Limitations and uncertainty",
        "",
        "- Pilot sample size (150 images) is small; per-class metrics for rare "
        "expressions have low support and should not be over-interpreted.",
        "- Candidate B (ArcFace+LR) is restricted to 5 classes "
        "(Fear/Happy/Neutral/Sad/Surprise) by the existing trained demo model, "
        "versus Candidate A (HSEmotion)'s 8 classes — this asymmetry alone can "
        "make raw accuracy/F1 not directly comparable between candidates.",
        "- Candidate B's embedding step re-runs face detection on an "
        "already-cropped CLAHE image; images where that re-detection fails "
        "(no_face / multiple_faces) are excluded from that candidate's "
        "metrics and reported separately below — this is itself a signal "
        "about real-world annotation-assistant usefulness, not just missing data.",
        "",
        "## Per-model results",
        "",
    ]
    for model_name, m in results["models"].items():
        lines.append(f"### {model_name}")
        lines.append("")
        if "error" in m:
            lines.append(f"ERROR: {m['error']}")
            lines.append("")
            continue
        lines.extend(
            [
                f"- Pilot images: {m['n_pilot_images']}",
                f"- Covered by this model (had an 'ok' prediction + human label): {m['n_covered']}",
                f"- Excluded by this model: {m['n_excluded_by_model']}",
                f"- Accuracy: {m['accuracy']:.4f}",
                f"- Macro-F1: {m['macro_f1']:.4f}",
                f"- Cohen's kappa: {m['cohens_kappa']:.4f}",
                f"- Confusion matrix: `{m['confusion_matrix_path']}`",
                (
                    f"- Mean confidence (correct): "
                    f"{m['confidence_vs_correctness']['mean_confidence_when_correct']}"
                ),
                (
                    f"- Mean confidence (incorrect): "
                    f"{m['confidence_vs_correctness']['mean_confidence_when_incorrect']}"
                ),
                "",
            ]
        )
    lines.append(
        "## EXP-PAP-004 decision\n\n"
        "Not made by this script. Record the documented annotation-assistant "
        "selection decision in docs/EXPERIMENT.md under EXP-PAP-004, referencing "
        "this report and agreement_metrics.json.\n"
    )
    report_out.write_text("\n".join(lines))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--human-labels", type=Path, default=DEFAULT_HUMAN_LABELS)
    parser.add_argument("--ai-predictions", type=Path, default=DEFAULT_AI_PREDICTIONS)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_OUT)
    parser.add_argument("--confusion-dir", type=Path, default=DEFAULT_CONFUSION_DIR)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run(args.human_labels, args.ai_predictions, args.metrics_out, args.confusion_dir, args.report_out)


if __name__ == "__main__":
    main()
