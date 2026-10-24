"""EXP-PAP-004: set up Annotator B's ISOLATED Label Studio project.

Why a separate server process, not a second project in the same org:
this repo's installed Label Studio (Community edition 1.23.0) has NO
role-based Data Manager restriction -- confirmed by reading
`label_studio/organizations/models.py`: `OrganizationMember` has no
`role` field at all (that's an Enterprise-only concept). Any org member
can open the Data Manager for ANY project in the organization and see
every existing annotation, including Task 1's. A second *project* in
the SAME organization would therefore not actually isolate Annotator B
from Annotator A's results -- only a second, fully separate server
process (separate SQLite DB, separate data directory, no shared
organization) does, since then B's account/server literally has no
record of Project A's existence or contents.

What IS shared (safely, read-only): the pilot image files themselves,
served from the same `data/papuan_v2/pilot/images/` directory on this
machine's filesystem via Label Studio's local-files-serving mechanism --
no image is copied, moved, or modified.

This script:
  1. Verifies the annotator_assignment.csv exists and its overlap subset
     is exactly 75 images, all present in pilot_manifest.csv.
  2. Connects to Annotator B's OWN Label Studio server (a different
     port/data-dir than Annotator A's -- see
     tools/papuan_v2/README_label_studio.md for the startup command).
  3. Creates/reuses the project "EXP-PAP-004 Overlap (Annotator B)" with
     the IDENTICAL label config as Project A (same 7 expression classes,
     same confidence field, same instructions) -- reusing
     label_studio_config.LABEL_CONFIG, not a re-typed copy.
  4. Connects the same `data/papuan_v2/pilot/images/` directory as local
     storage (read-only in effect -- this script never writes into it).
  5. Imports exactly the 75 overlap-subset tasks (idempotent).
  6. Sets show_collab_predictions=False, show_annotation_history=False.

Never touches Project A (id=2), never touches human_labels.csv, never
regenerates the pilot or the assignment.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from label_studio_config import (  # noqa: E402
    ANNOTATOR_B_OVERLAP_SIZE,
    LABEL_CONFIG,
    PILOT_IMAGES_DIR,
    PROJECT_TITLE_B,
    build_tasks,
    expected_pilot_image_ids,
    load_annotator_assignment,
    load_pilot_manifest,
    overlap_image_ids,
    tasks_missing_from_project,
)

DEFAULT_LABEL_STUDIO_B_URL = "http://localhost:8081"


def verify_overlap_assignment(assignment_path) -> list[dict]:
    assignment_rows = load_annotator_assignment(assignment_path)
    overlap_ids = overlap_image_ids(assignment_rows)
    if len(overlap_ids) != ANNOTATOR_B_OVERLAP_SIZE:
        raise RuntimeError(
            f"Expected exactly {ANNOTATOR_B_OVERLAP_SIZE} overlap images, found {len(overlap_ids)}."
        )
    pilot_ids = expected_pilot_image_ids()
    unknown = overlap_ids - pilot_ids
    if unknown:
        raise RuntimeError(f"Overlap set contains image_id(s) not in pilot_manifest.csv: {sorted(unknown)[:5]}")

    manifest_rows = load_pilot_manifest()
    overlap_rows = [row for row in manifest_rows if row["image_id"] in overlap_ids]
    print(f"Verified {len(overlap_rows)} overlap images, all present in pilot_manifest.csv.")
    return overlap_rows


def find_or_create_project(client, title: str, label_config: str):
    for project in client.get_projects():
        params = project.get_params()
        if params.get("title") == title:
            print(f"Reusing existing project: id={params.get('id')} title={title!r}")
            if params.get("label_config") != label_config:
                project.set_params(label_config=label_config)
                print("Updated label_config on existing project to match the current pilot config.")
            return project

    print(f"Creating new project: title={title!r}")
    return client.create_project(
        title=title, label_config=label_config, show_collab_predictions=False, show_annotation_history=False
    )


def ensure_local_storage_connected(project) -> None:
    existing = project.get_import_storages()
    for storage in existing:
        if storage.get("type") == "localfiles" and storage.get("path") == str(PILOT_IMAGES_DIR):
            print(f"Local files storage already connected: {storage.get('path')}")
            return
    if "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT" not in os.environ:
        os.environ["LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT"] = str(REPO_ROOT)
    project.connect_local_import_storage(local_store_path=str(PILOT_IMAGES_DIR), title="EXP-PAP-004 overlap images")
    print(f"Connected local files storage: {PILOT_IMAGES_DIR}")


def existing_task_image_ids(project) -> set[str]:
    return {t["data"]["image_id"] for t in project.get_tasks() if t.get("data", {}).get("image_id")}


def run(label_studio_b_url: str, api_key: str, assignment_path) -> dict:
    overlap_rows = verify_overlap_assignment(assignment_path)

    from label_studio_sdk._legacy.client import Client

    client = Client(url=label_studio_b_url, api_key=api_key)
    client.check_connection()

    project = find_or_create_project(client, PROJECT_TITLE_B, LABEL_CONFIG)
    ensure_local_storage_connected(project)

    existing_ids = existing_task_image_ids(project)
    missing_tasks = tasks_missing_from_project(existing_ids, overlap_rows)
    if missing_tasks:
        project.import_tasks(missing_tasks)
        print(f"Imported {len(missing_tasks)} new task(s) ({len(existing_ids)} already present).")
    else:
        print(f"No new tasks to import ({len(existing_ids)} already present).")

    params = project.get_params()
    return {"project_id": params.get("id"), "project_title": params.get("title"), "tasks_total": len(overlap_rows)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("LABEL_STUDIO_B_URL", DEFAULT_LABEL_STUDIO_B_URL))
    parser.add_argument("--api-key", default=os.environ.get("LABEL_STUDIO_B_API_KEY"))
    parser.add_argument("--assignment-path", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    from label_studio_config import ANNOTATOR_ASSIGNMENT_PATH

    args = parse_args(argv)
    if not args.api_key:
        raise SystemExit("LABEL_STUDIO_B_API_KEY is not set. See tools/papuan_v2/README_label_studio.md.")
    result = run(args.url, args.api_key, args.assignment_path or ANNOTATOR_ASSIGNMENT_PATH)
    print(result)


if __name__ == "__main__":
    main()
