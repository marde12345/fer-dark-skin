"""EXP-PAP-004: export Label Studio annotations and map them back to
pilot_manifest.csv-stable image_ids.

Run this only AFTER blind human labeling in Label Studio is complete (or
partially complete -- it exports whatever annotations currently exist).

Two outputs, kept deliberately separate:

1. experiments/EXP-PAP-004/label_studio_export.csv -- the full-provenance
   export (experiment_id, image_id, human_label, human_confidence,
   annotator_source, human_verified, exported_at). This is the single
   source of truth for what Label Studio actually recorded; nothing here
   is hand-edited or duplicated elsewhere.

2. experiments/EXP-PAP-004/human_labels.csv -- ONLY written if
   --write-human-labels is passed. Maps human_label -> gt_label,
   annotator_source -> labeled_by, exported_at -> labeled_at (the schema
   already defined by init_human_labels_template.py -- this script does
   not invent a conflicting schema). Confidence is metadata only and is
   folded into `notes` (e.g. "confidence=Low"), never into `gt_label`,
   per the approved proposal's "confidence must NOT become part of the
   expression ground truth."

   Like init_human_labels_template.py, this refuses to overwrite a
   human_labels.csv that already has non-empty gt_label rows unless
   --force is passed, so a half-finished manual labeling pass already in
   that file can never be silently clobbered by an export.

Mapping uses each task's `data.image_id` (set at task-creation time by
setup_label_studio_pilot.py / label_studio_config.build_tasks), never
Label Studio's own task ordering or numeric task id, so re-exports remain
correct even if Label Studio's internal ordering changes.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from label_studio_config import PROJECT_TITLE, PROJECT_TITLE_B, expected_pilot_image_ids  # noqa: E402

DEFAULT_LABEL_STUDIO_URL = "http://localhost:8080"
EXPORT_OUT = REPO_ROOT / "experiments" / "EXP-PAP-004" / "label_studio_export.csv"
EXPORT_OUT_B = REPO_ROOT / "experiments" / "EXP-PAP-004" / "label_studio_export_annotator_b.csv"
HUMAN_LABELS_OUT = REPO_ROOT / "experiments" / "EXP-PAP-004" / "human_labels.csv"

EXPORT_FIELDNAMES = [
    "experiment_id",
    "image_id",
    "human_label",
    "human_confidence",
    "annotator_source",
    "human_verified",
    "exported_at",
]
HUMAN_LABELS_FIELDNAMES = ["image_id", "gt_label", "labeled_by", "labeled_at", "notes"]


def extract_choice(annotation_result: list[dict], field_name: str) -> str | None:
    for item in annotation_result:
        if item.get("from_name") == field_name:
            values = item.get("value", {}).get("choices", [])
            if values:
                return values[0]
    return None


def export_rows_from_tasks(tasks: list[dict], now_iso: str, user_email_by_id: dict[int, str] | None = None) -> list[dict]:
    """Pure function: given raw Label Studio task dicts (each with `data`
    and `annotations`), returns export rows. Only the LATEST annotation
    per task is used (tasks can in principle carry multiple annotations
    if re-reviewed; we take the most recently created one, matching
    "one final human label per image").

    Annotator identity: uses Label Studio's own `completed_by` user id,
    resolved to that user's real email via `user_email_by_id` (built from
    `client.get_users()` -- see `run()`). Never a hardcoded/fake
    annotator string. Falls back to the raw
    `f"label_studio_user_{completed_by}"` if no email mapping is
    available (e.g. in a unit test that doesn't supply one), so the
    field is never silently empty."""
    user_email_by_id = user_email_by_id or {}
    rows = []
    for task in tasks:
        image_id = task.get("data", {}).get("image_id")
        if not image_id:
            continue
        annotations = task.get("annotations") or []
        if not annotations:
            continue
        latest = max(annotations, key=lambda a: a.get("created_at", ""))
        result = latest.get("result", [])
        human_label = extract_choice(result, "expression")
        human_confidence = extract_choice(result, "confidence")
        if not human_label:
            continue

        completed_by = latest.get("completed_by")
        if isinstance(completed_by, dict):
            annotator_source = completed_by.get("email") or f"label_studio_user_{completed_by.get('id')}"
        elif completed_by is not None:
            annotator_source = user_email_by_id.get(completed_by, f"label_studio_user_{completed_by}")
        else:
            annotator_source = "unknown"

        rows.append(
            {
                "experiment_id": "EXP-PAP-004",
                "image_id": image_id,
                "human_label": human_label,
                "human_confidence": human_confidence or "",
                "annotator_source": annotator_source,
                "human_verified": True,
                "exported_at": now_iso,
            }
        )
    return rows


def write_export_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def export_rows_to_human_labels_rows(export_rows: list[dict]) -> list[dict]:
    """Maps the rich export schema onto the already-defined human_labels.csv
    schema (image_id, gt_label, labeled_by, labeled_at, notes). Confidence
    is folded into `notes`, never into `gt_label`."""
    rows = []
    for row in export_rows:
        notes = f"confidence={row['human_confidence']}" if row["human_confidence"] else ""
        rows.append(
            {
                "image_id": row["image_id"],
                "gt_label": row["human_label"],
                "labeled_by": row["annotator_source"],
                "labeled_at": row["exported_at"],
                "notes": notes,
            }
        )
    return rows


def has_existing_labels(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return any(row.get("gt_label", "").strip() for row in rows)


def write_human_labels_csv(rows: list[dict], out_path: Path, force: bool) -> None:
    if not force and has_existing_labels(out_path):
        raise RuntimeError(
            f"{out_path} already contains non-empty gt_label values. "
            "Refusing to overwrite existing labeling work. Pass --force only if certain."
        )
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HUMAN_LABELS_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def run(
    label_studio_url: str,
    api_key: str,
    write_human_labels: bool,
    force: bool,
    project_title: str = PROJECT_TITLE,
    export_out: Path = EXPORT_OUT,
) -> list[dict]:
    if write_human_labels and project_title != PROJECT_TITLE:
        raise RuntimeError(
            "--write-human-labels is only valid when exporting Annotator A's full-pilot project "
            f"({PROJECT_TITLE!r}) -- human_labels.csv's schema expects all 150 pilot images, not a "
            "75-image overlap subset. Export Annotator B's project without --write-human-labels; "
            "use human_agreement_report.py to compare the two exports instead."
        )

    from label_studio_sdk._legacy.client import Client

    client = Client(url=label_studio_url, api_key=api_key)
    project = None
    for p in client.get_projects():
        if p.get_params().get("title") == project_title:
            project = p
            break
    if project is None:
        raise RuntimeError(f"No Label Studio project found with title {project_title!r} on {label_studio_url}.")

    user_email_by_id = {u.id: u.email for u in client.get_users()}
    tasks = project.get_tasks()
    now_iso = datetime.now(timezone.utc).isoformat()
    export_rows = export_rows_from_tasks(tasks, now_iso, user_email_by_id)

    exported_ids = {r["image_id"] for r in export_rows}
    expected_ids = expected_pilot_image_ids()
    unexpected = exported_ids - expected_ids
    if unexpected:
        raise RuntimeError(
            f"{len(unexpected)} exported annotation(s) reference image_id(s) not in "
            f"pilot_manifest.csv: {sorted(unexpected)[:5]} -- refusing to export."
        )

    write_export_csv(export_rows, export_out)
    print(f"Wrote {len(export_rows)} annotated row(s) to {export_out}")

    if write_human_labels:
        human_rows = export_rows_to_human_labels_rows(export_rows)
        write_human_labels_csv(human_rows, HUMAN_LABELS_OUT, force)
        print(f"Wrote {len(human_rows)} row(s) to {HUMAN_LABELS_OUT}")

    return export_rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotator",
        choices=["A", "B"],
        default="A",
        help="A: export Project A (all 150, http://localhost:8080 by default). "
        "B: export Project B (75-overlap, http://localhost:8081 by default).",
    )
    parser.add_argument("--url", default=None, help="Overrides the --annotator-based default URL.")
    parser.add_argument("--api-key", default=None, help="Overrides LABEL_STUDIO_API_KEY/LABEL_STUDIO_B_API_KEY.")
    parser.add_argument("--output", type=Path, default=None, help="Overrides the --annotator-based default output path.")
    parser.add_argument("--write-human-labels", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.annotator == "A":
        url = args.url or os.environ.get("LABEL_STUDIO_URL", DEFAULT_LABEL_STUDIO_URL)
        api_key = args.api_key or os.environ.get("LABEL_STUDIO_API_KEY")
        project_title = PROJECT_TITLE
        export_out = args.output or EXPORT_OUT
        key_hint = "LABEL_STUDIO_API_KEY"
    else:
        url = args.url or os.environ.get("LABEL_STUDIO_B_URL", "http://localhost:8081")
        api_key = args.api_key or os.environ.get("LABEL_STUDIO_B_API_KEY")
        project_title = PROJECT_TITLE_B
        export_out = args.output or EXPORT_OUT_B
        key_hint = "LABEL_STUDIO_B_API_KEY"

    if not api_key:
        raise SystemExit(f"{key_hint} is not set. See tools/papuan_v2/README_label_studio.md.")
    run(url, api_key, args.write_human_labels, args.force, project_title=project_title, export_out=export_out)


if __name__ == "__main__":
    main()
