"""EXP-PAP-002 (part 2): human-labels template scaffolding.

Writes experiments/EXP-PAP-004/human_labels.csv as an EMPTY template
(one row per pilot image, `gt_label`/`labeled_by`/`labeled_at`/`notes`
left blank) for a human annotator to fill in independently of any AI
prediction.

IMPORTANT: this script does not, and must never, fill in gt_label
values itself. No model or script output is written into this file --
per the approved proposal's independence constraint
("Human labels -> independent ground truth"), the only valid way rows
in this file get populated is a human looking at each
data/papuan_v2/pilot/images/*.jpg file and recording a label, ideally
without having seen either candidate model's prediction for that image.

If experiments/EXP-PAP-004/human_labels.csv already exists and already
has non-empty gt_label values, this script refuses to overwrite it
(use --force to regenerate an empty template anyway, which would
destroy any labeling work already done -- confirm with your labeler
before doing this).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "experiments" / "EXP-PAP-004" / "pilot_manifest.csv"
DEFAULT_OUTPUT = REPO_ROOT / "experiments" / "EXP-PAP-004" / "human_labels.csv"

FIELDNAMES = ["image_id", "gt_label", "labeled_by", "labeled_at", "notes"]


def has_existing_labels(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return any(row.get("gt_label", "").strip() for row in rows)


def build_template(manifest_path: Path, output_path: Path, force: bool) -> int:
    if not force and has_existing_labels(output_path):
        raise RuntimeError(
            f"{output_path} already contains non-empty gt_label values. "
            "Refusing to overwrite existing human labeling work. Pass --force "
            "only if you are certain (this destroys existing labels)."
        )

    with manifest_path.open() as f:
        manifest_rows = list(csv.DictReader(f))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(
                {
                    "image_id": row["image_id"],
                    "gt_label": "",
                    "labeled_by": "",
                    "labeled_at": "",
                    "notes": "",
                }
            )

    print(f"Wrote {len(manifest_rows)}-row empty human-labels template to {output_path}")
    print("Fill in gt_label for each row independently before running pilot_agreement_report.py.")
    return len(manifest_rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    build_template(args.manifest, args.output, args.force)


if __name__ == "__main__":
    main()
