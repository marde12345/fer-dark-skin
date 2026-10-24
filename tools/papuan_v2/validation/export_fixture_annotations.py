"""Phase 1 validation: export all annotations from the throwaway fixture
project (multiple annotations per task, real annotator identity), used
to empirically validate the export/provenance design proposed in
docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md section 4.2 before it is
implemented against the real full dataset.

Deliberately separate from tools/papuan_v2/export_label_studio_labels.py
(the pilot's production export script, which exports ONE annotation per
task/annotator) -- this validates the NEW multi-annotation-per-task
export shape the full workflow needs, without touching pilot code.

Keys exclusively by `task["data"]["image_id"]` and each annotation's own
`completed_by` (resolved to a real email via `client.get_users()`),
never by Label Studio's task list position/order or numeric ids -- the
same principle already enforced in the pilot's export code.
"""

from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

FIELDNAMES = [
    "image_id",
    "annotation_id",
    "annotator_identity",
    "expression",
    "confidence",
    "created_at",
]


def extract_choice(result: list[dict], field_name: str) -> str | None:
    for item in result:
        if item.get("from_name") == field_name:
            values = item.get("value", {}).get("choices", [])
            if values:
                return values[0]
    return None


def export_rows_multi_annotator(tasks: list[dict], user_email_by_id: dict[int, str]) -> list[dict]:
    """Pure function: one row PER ANNOTATION (not per task), covering
    every annotation on every task -- the shape the full workflow needs,
    distinct from the pilot's "latest annotation only" export mode."""
    rows = []
    for task in tasks:
        image_id = task.get("data", {}).get("image_id")
        if not image_id:
            continue
        for annotation in task.get("annotations") or []:
            completed_by = annotation.get("completed_by")
            if isinstance(completed_by, dict):
                identity = completed_by.get("email") or f"label_studio_user_{completed_by.get('id')}"
            elif completed_by is not None:
                identity = user_email_by_id.get(completed_by, f"label_studio_user_{completed_by}")
            else:
                identity = "unknown"

            result = annotation.get("result", [])
            rows.append(
                {
                    "image_id": image_id,
                    "annotation_id": annotation.get("id"),
                    "annotator_identity": identity,
                    "expression": extract_choice(result, "expression") or "",
                    "confidence": extract_choice(result, "confidence") or "",
                    "created_at": annotation.get("created_at", ""),
                }
            )
    return rows


def run(label_studio_url: str, api_key: str, project_id: int, output_path: Path) -> list[dict]:
    from label_studio_sdk._legacy.client import Client

    client = Client(url=label_studio_url, api_key=api_key)
    project = client.get_project(project_id)

    user_email_by_id = {u.id: u.email for u in client.get_users()}
    tasks = project.get_tasks()

    rows = export_rows_multi_annotator(tasks, user_email_by_id)
    rows.sort(key=lambda r: (r["image_id"], r["annotator_identity"]))  # deterministic output order, never task-list order

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} annotation rows ({len(tasks)} tasks) to {output_path}")
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("PHASE1_LS_URL", "http://localhost:8090"))
    parser.add_argument("--api-key", default=os.environ.get("PHASE1_OWNER_TOKEN"))
    parser.add_argument("--project-id", type=int, default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "tools" / "papuan_v2" / "validation" / "fixture_export.csv",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.api_key:
        raise SystemExit("PHASE1_OWNER_TOKEN is not set.")
    run(args.url, args.api_key, args.project_id, args.output)


if __name__ == "__main__":
    main()
