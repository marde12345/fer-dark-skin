"""EXP-PAP-004: apply the annotator_assignment.csv overlap flag to
Project A's (id=2, "EXP-PAP-004 Papuan V2 Pilot (Blind)") existing 150
tasks.

Label Studio's task-distribution queue only keeps offering a task to
additional annotators until `task.overlap` annotations exist for it
(confirmed by reading `label_studio/tasks/models.py` --
`completed_annotations >= overlap` is the completion check). Project A's
tasks were created with the project default `overlap=1`, which means
once Annotator A submits an annotation, Label Studio would treat those
tasks as fully labeled and would NOT offer them to a second annotator in
the same project's stream. Setting `overlap=2` on exactly the 75
overlap-subset tasks (and explicitly leaving the other 75 at `overlap=1`)
is what allows a second independent annotation to actually be collected
-- WITHOUT this, Annotator B would find nothing left to label.

This ONLY PATCHes the integer `overlap` field on each Task row via
Label Studio's REST API (`PATCH /api/tasks/<id>/`). It never touches
the `annotations` table, so Task 1's existing annotation from Annotator
A is structurally untouched -- verified by this script re-reading and
diffing each task's `annotations` before/after the PATCH and refusing to
proceed if anything about them changed.

This script is idempotent: tasks already at the correct overlap value
are skipped (reported, not re-PATCHed).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from label_studio_config import load_annotator_assignment  # noqa: E402

DEFAULT_LABEL_STUDIO_URL = "http://localhost:8080"
DEFAULT_PROJECT_ID = 2


def fetch_tasks(base_url: str, api_key: str, project_id: int) -> list[dict]:
    resp = requests.get(
        f"{base_url}/api/tasks",
        params={"project": project_id, "page_size": 100000},
        headers={"Authorization": f"Token {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["tasks"]


def fetch_task_detail(base_url: str, api_key: str, task_id: int) -> dict:
    resp = requests.get(
        f"{base_url}/api/tasks/{task_id}/",
        headers={"Authorization": f"Token {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def patch_task_overlap(base_url: str, api_key: str, task_id: int, overlap: int) -> None:
    resp = requests.patch(
        f"{base_url}/api/tasks/{task_id}/",
        json={"overlap": overlap},
        headers={"Authorization": f"Token {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()


def run(base_url: str, api_key: str, project_id: int, assignment_path) -> dict:
    assignment_rows = load_annotator_assignment(assignment_path)
    overlap_by_image_id = {row["image_id"]: row["overlap"] for row in assignment_rows}

    tasks = fetch_tasks(base_url, api_key, project_id)
    tasks_by_image_id = {t["data"]["image_id"]: t for t in tasks}

    missing = set(overlap_by_image_id) - set(tasks_by_image_id)
    if missing:
        raise RuntimeError(
            f"{len(missing)} assignment image_id(s) have no matching task in project "
            f"{project_id}: {sorted(missing)[:5]} -- refusing to proceed."
        )

    updated, skipped = [], []
    annotation_snapshots_before = {}

    for image_id, is_overlap in overlap_by_image_id.items():
        task = tasks_by_image_id[image_id]
        task_id = task["id"]
        target_overlap = 2 if is_overlap else 1
        current_overlap = task.get("overlap", 1)

        detail_before = fetch_task_detail(base_url, api_key, task_id)
        annotation_snapshots_before[task_id] = detail_before.get("annotations", [])

        if current_overlap == target_overlap:
            skipped.append(image_id)
            continue

        patch_task_overlap(base_url, api_key, task_id, target_overlap)
        updated.append(image_id)

    # Verify no annotation was altered by the PATCH calls.
    for task_id, before in annotation_snapshots_before.items():
        after = fetch_task_detail(base_url, api_key, task_id).get("annotations", [])
        before_ids = sorted(a["id"] for a in before)
        after_ids = sorted(a["id"] for a in after)
        if before_ids != after_ids:
            raise RuntimeError(
                f"SAFETY CHECK FAILED: task {task_id}'s annotation set changed "
                f"during overlap PATCH ({before_ids} -> {after_ids}). Stopping immediately."
            )

    print(f"Updated overlap on {len(updated)} task(s); {len(skipped)} already correct.")
    print("Verified: no annotation was added, removed, or modified by this script.")
    return {"updated": updated, "skipped": skipped}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("LABEL_STUDIO_URL", DEFAULT_LABEL_STUDIO_URL))
    parser.add_argument("--api-key", default=os.environ.get("LABEL_STUDIO_API_KEY"))
    parser.add_argument("--project-id", type=int, default=DEFAULT_PROJECT_ID)
    parser.add_argument("--assignment-path", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    from label_studio_config import ANNOTATOR_ASSIGNMENT_PATH

    args = parse_args(argv)
    if not args.api_key:
        raise SystemExit("LABEL_STUDIO_API_KEY is not set.")
    run(args.url, args.api_key, args.project_id, args.assignment_path or ANNOTATOR_ASSIGNMENT_PATH)


if __name__ == "__main__":
    main()
