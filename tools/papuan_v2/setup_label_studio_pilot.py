"""EXP-PAP-004: set up a local Label Studio project for blind human
labeling of the 150-image Papuan V2 pilot set.

Reads ONLY existing artifacts:
  - experiments/EXP-PAP-004/pilot_manifest.csv (source of truth for pilot
    membership -- never regenerated here)
  - data/papuan_v2/pilot/images/*.jpg (never modified or resampled here)

Writes:
  - A Label Studio project (created once; re-running this script re-uses
    the existing project by title and only imports tasks not already
    present -- idempotent, see label_studio_config.tasks_missing_from_project)
  - experiments/EXP-PAP-004/label_studio_metadata.json (machine-readable
    status snapshot: project id, annotation progress, config version)

Never writes to experiments/EXP-PAP-004/human_labels.csv -- that file is
only ever written by export_label_studio_labels.py, AFTER labeling is
complete in Label Studio, and even then not automatically (see that
script's docstring).

Requires:
  - LABEL_STUDIO_URL (default: http://localhost:8080)
  - LABEL_STUDIO_API_KEY (no default -- must be set by you after your
    first Label Studio login; never hardcoded or committed here)
  - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true and
    LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=<repo root, absolute path>
    must be set in the environment Label Studio's server process itself
    runs in (not just this script's environment) -- see
    tools/papuan_v2/README_label_studio.md for the exact startup command.

Run:
    uv run --group labeling python tools/papuan_v2/setup_label_studio_pilot.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from label_studio_config import (  # noqa: E402
    LABEL_CONFIG,
    LABELING_CONFIG_VERSION,
    PILOT_IMAGES_DIR,
    PROJECT_TITLE,
    build_tasks,
    load_pilot_manifest,
    tasks_missing_from_project,
    verify_pilot_images_present,
)

DEFAULT_LABEL_STUDIO_URL = "http://localhost:8080"
METADATA_OUT = REPO_ROOT / "experiments" / "EXP-PAP-004" / "label_studio_metadata.json"


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
    project = client.create_project(title=title, label_config=label_config)
    return project


def existing_task_image_ids(project) -> set[str]:
    ids = set()
    for task in project.get_tasks():
        image_id = task.get("data", {}).get("image_id")
        if image_id:
            ids.add(image_id)
    return ids


def ensure_local_storage_connected(project) -> None:
    """Registers data/papuan_v2/pilot/images/ as a Local Files import
    storage for this project, if not already connected. Required by
    Label Studio's own local-files-serving permission check (it only
    serves a file if it falls under a LocalFilesImportStorage `path`
    registered against a project the requesting user can access) --
    the LOCAL_FILES_SERVING_ENABLED/LOCAL_FILES_DOCUMENT_ROOT env vars
    on the server alone are necessary but not sufficient."""
    existing = project.get_import_storages()
    for storage in existing:
        if storage.get("type") == "localfiles" and storage.get("path") == str(PILOT_IMAGES_DIR):
            print(f"Local files storage already connected: {storage.get('path')}")
            return

    if "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT" not in os.environ:
        os.environ["LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT"] = str(REPO_ROOT)

    project.connect_local_import_storage(
        local_store_path=str(PILOT_IMAGES_DIR),
        title="EXP-PAP-004 pilot images",
    )
    print(f"Connected local files storage: {PILOT_IMAGES_DIR}")


def import_missing_tasks(project, manifest_rows: list[dict]) -> int:
    existing_ids = existing_task_image_ids(project)
    missing_tasks = tasks_missing_from_project(existing_ids, manifest_rows)
    if not missing_tasks:
        print(f"No new tasks to import ({len(existing_ids)} already present).")
        return 0
    project.import_tasks(missing_tasks)
    print(f"Imported {len(missing_tasks)} new task(s) ({len(existing_ids)} were already present).")
    return len(missing_tasks)


def write_metadata(project, manifest_rows: list[dict], label_studio_url: str) -> dict:
    params = project.get_params()
    tasks = project.get_tasks()
    labeled_count = sum(1 for t in tasks if t.get("annotations"))
    total = len(manifest_rows)

    status = "not_started"
    if labeled_count > 0:
        status = "complete" if labeled_count >= total else "in_progress"

    metadata = {
        "experiment_id": "EXP-PAP-004",
        "dataset_version": "papuan_v2",
        "pilot_size": total,
        "project_id": params.get("id"),
        "project_title": params.get("title"),
        "label_studio_url": label_studio_url,
        "annotation_status": status,
        "labeled_count": labeled_count,
        "remaining_count": max(total - labeled_count, 0),
        "labeling_config_version": LABELING_CONFIG_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    METADATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    METADATA_OUT.write_text(json.dumps(metadata, indent=2))
    print(f"Wrote {METADATA_OUT}")
    return metadata


def run(label_studio_url: str, api_key: str) -> dict:
    verify_pilot_images_present()
    manifest_rows = load_pilot_manifest()
    if len(manifest_rows) != 150:
        raise RuntimeError(
            f"Expected exactly 150 pilot manifest rows, found {len(manifest_rows)}. "
            "Refusing to proceed -- pilot membership must match pilot_manifest.csv exactly."
        )
    print(f"Verified {len(manifest_rows)} pilot images present and matching the manifest.")

    # Imported lazily so this module (and label_studio_config, which has
    # no SDK dependency) stays importable/testable without label-studio-sdk
    # installed or a live server reachable.
    from label_studio_sdk._legacy.client import Client

    client = Client(url=label_studio_url, api_key=api_key)
    client.check_connection()

    project = find_or_create_project(client, PROJECT_TITLE, LABEL_CONFIG)
    ensure_local_storage_connected(project)
    import_missing_tasks(project, manifest_rows)
    return write_metadata(project, manifest_rows, label_studio_url)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("LABEL_STUDIO_URL", DEFAULT_LABEL_STUDIO_URL))
    parser.add_argument("--api-key", default=os.environ.get("LABEL_STUDIO_API_KEY"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.api_key:
        raise SystemExit(
            "LABEL_STUDIO_API_KEY is not set. Log into your local Label Studio instance, "
            "copy your API key from Account & Settings, and set it: "
            "export LABEL_STUDIO_API_KEY=<your key>. See tools/papuan_v2/README_label_studio.md."
        )
    metadata = run(args.url, args.api_key)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
