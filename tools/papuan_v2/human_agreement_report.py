"""EXP-PAP-004: human-human (Annotator A vs Annotator B) agreement over
the 75-image overlap subset.

This is prepared and unit-tested now (tests/test_annotator_overlap.py)
but is NOT run against real data yet -- Annotator B has not labeled
anything. Per the approved scope: "Do not run final model-vs-human
agreement analysis yet. First we need human-human agreement... Do NOT
adjudicate automatically."

Reads two independent label exports (see export_label_studio_labels.py,
run once per server: A's export from http://localhost:8080, B's export
from http://localhost:8081) and computes, over the 75 overlap image_ids
ONLY:
  - raw (percent) agreement
  - Cohen's kappa
  - confusion matrix (A's label vs B's label)
  - per-class agreement breakdown

Refuses to run if either annotator's export is missing a label for any
of the 75 overlap image_ids -- human-human agreement must be computed
over a complete, matched pair set, not a partial one.

This script NEVER adjudicates or picks a "correct" label between A and
B, and NEVER lets an AI prediction influence the comparison -- it
reports disagreements as data for a human to review later
(docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md's
"Adjudication of disagreements" stage, out of scope for this phase).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import cohen_kappa_score, confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from label_studio_config import ANNOTATOR_ASSIGNMENT_PATH, overlap_image_ids  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_A_EXPORT = REPO_ROOT / "experiments" / "EXP-PAP-004" / "label_studio_export.csv"
DEFAULT_B_EXPORT = REPO_ROOT / "experiments" / "EXP-PAP-004" / "label_studio_export_annotator_b.csv"
OUTPUT_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "human_human_agreement.json"


def load_export_labels(path: Path) -> dict[str, dict]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return {row["image_id"]: row for row in rows}


def compute_agreement(overlap_ids: set[str], labels_a: dict[str, dict], labels_b: dict[str, dict]) -> dict:
    missing_a = overlap_ids - set(labels_a)
    missing_b = overlap_ids - set(labels_b)
    if missing_a or missing_b:
        raise RuntimeError(
            f"Human-human agreement requires BOTH annotators to have labeled all {len(overlap_ids)} "
            f"overlap images. Missing from A: {len(missing_a)}, missing from B: {len(missing_b)}. "
            "Refusing to compute a partial result."
        )

    ordered_ids = sorted(overlap_ids)
    y_a = [labels_a[i]["human_label"] for i in ordered_ids]
    y_b = [labels_b[i]["human_label"] for i in ordered_ids]

    agreements = [a == b for a, b in zip(y_a, y_b)]
    raw_agreement = sum(agreements) / len(agreements)
    kappa = cohen_kappa_score(y_a, y_b)

    all_labels = sorted(set(y_a) | set(y_b))
    cm = confusion_matrix(y_a, y_b, labels=all_labels)

    per_class = {}
    for label in all_labels:
        a_indices = [i for i, v in enumerate(y_a) if v == label]
        if not a_indices:
            per_class[label] = None
            continue
        matches = sum(1 for i in a_indices if y_b[i] == label)
        per_class[label] = matches / len(a_indices)

    disagreements = [
        {"image_id": i, "annotator_A_label": labels_a[i]["human_label"], "annotator_B_label": labels_b[i]["human_label"]}
        for i in ordered_ids
        if labels_a[i]["human_label"] != labels_b[i]["human_label"]
    ]

    return {
        "experiment_id": "EXP-PAP-004",
        "n_overlap_images": len(ordered_ids),
        "raw_agreement": raw_agreement,
        "cohens_kappa": float(kappa),
        "confusion_matrix_labels": all_labels,
        "confusion_matrix": cm.tolist(),
        "per_class_agreement_given_A": per_class,
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
        "adjudicated": False,
        "adjudication_note": "Not adjudicated -- disagreements are reported for later human review, never auto-resolved by an AI prediction.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run(a_export_path: Path, b_export_path: Path, assignment_path: Path, output_path: Path) -> dict:
    overlap_ids = overlap_image_ids(path=assignment_path)
    labels_a = load_export_labels(a_export_path)
    labels_b = load_export_labels(b_export_path)

    result = compute_agreement(overlap_ids, labels_a, labels_b)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {output_path}")
    print(f"Raw agreement: {result['raw_agreement']:.3f}, Cohen's kappa: {result['cohens_kappa']:.3f}")
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a-export", type=Path, default=DEFAULT_A_EXPORT)
    parser.add_argument("--b-export", type=Path, default=DEFAULT_B_EXPORT)
    parser.add_argument("--assignment-path", type=Path, default=ANNOTATOR_ASSIGNMENT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run(args.a_export, args.b_export, args.assignment_path, args.output)


if __name__ == "__main__":
    main()
