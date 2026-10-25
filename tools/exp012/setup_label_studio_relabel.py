"""EXP-012: create the separate Label Studio project for relabeling the 227
legacy crops, connect the image folders, and import tasks.

Never touches the EXP-PAP-004 projects, any existing label file, or any
experiment output. Idempotent: re-running reuses the project by title and
imports only tasks not already present.

Requires a running Label Studio server started with
LOCAL_FILES_SERVING_ENABLED=true and LOCAL_FILES_DOCUMENT_ROOT=<document root>
(see experiments/EXP-012-relabel/README.md), plus:
  LABEL_STUDIO_URL     (default http://localhost:8080)
  LABEL_STUDIO_API_KEY (never committed)

Run a small verification sample first:
    uv run --group labeling python tools/exp012/setup_label_studio_relabel.py --sample
then, after the sample is confirmed, the full set:
    uv run --group labeling python tools/exp012/setup_label_studio_relabel.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import relabel_config as cfg  # noqa: E402


def find_or_create_project(client, title: str):
    for project in client.get_projects():
        if project.get_params().get("title") == title:
            print(f"Reusing project {project.get_params().get('id')}: {title!r}")
            if project.get_params().get("label_config") != cfg.LABEL_CONFIG:
                project.set_params(label_config=cfg.LABEL_CONFIG)
            return project
    print(f"Creating project: {title!r}")
    return client.create_project(title=title, label_config=cfg.LABEL_CONFIG)


def ensure_storage(project, path: Path, title: str) -> None:
    for storage in project.get_import_storages():
        if storage.get("type") == "localfiles" and storage.get("path") == str(path):
            return
    project.connect_local_import_storage(local_store_path=str(path), title=title)
    print(f"Connected local files storage: {path}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", action="store_true", help="Create the SAMPLE project with a small verification set.")
    mode.add_argument("--all", action="store_true", help="Create the real project with all 227 crops.")
    parser.add_argument("--data-root", type=Path, default=cfg.REPO_ROOT)
    parser.add_argument("--document-root", type=Path,
                        default=Path(os.environ.get("LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT", cfg.REPO_ROOT)))
    args = parser.parse_args(argv)

    from label_studio_sdk import Client  # imported here so the config module stays server-free

    api_key = os.environ.get("LABEL_STUDIO_API_KEY")
    if not api_key:
        raise SystemExit("Set LABEL_STUDIO_API_KEY (see experiments/EXP-012-relabel/README.md).")
    os.environ["LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT"] = str(args.document_root)
    url = os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080")

    image_ids = cfg.legacy_image_ids(args.data_root)
    if len(image_ids) != 227:
        raise SystemExit(f"expected 227 legacy crops, found {len(image_ids)}")
    landmarks = cfg.resolve_landmarks(image_ids)
    selected = cfg.sample_image_ids(landmarks) if args.sample else image_ids
    overlay_dir = args.data_root / cfg.OVERLAY_REL
    missing = [i for i in selected if not (overlay_dir / f"{i}.png").exists()]
    if missing:
        raise SystemExit(f"{len(missing)} overlay(s) missing in {overlay_dir}; run render_overlays.py first.")

    client = Client(url=url, api_key=api_key)
    project = find_or_create_project(client, cfg.SAMPLE_PROJECT_TITLE if args.sample else cfg.PROJECT_TITLE)
    ensure_storage(project, args.data_root / cfg.LEGACY_FACES_REL, "EXP-012 legacy crops")
    ensure_storage(project, overlay_dir, "EXP-012 landmark overlays")

    present = {t["data"].get("image_id") for t in project.get_tasks()}
    new_tasks = [t for t in cfg.build_tasks(selected, landmarks, args.data_root, overlay_dir, args.document_root)
                 if t["data"]["image_id"] not in present]
    if new_tasks:
        project.import_tasks(new_tasks)
    print(f"Imported {len(new_tasks)} new task(s); {len(present)} already present.")

    meta = {
        "experiment_id": cfg.EXPERIMENT_ID,
        "label_round": cfg.LABEL_ROUND,
        "mode": "sample" if args.sample else "all",
        "project_id": project.get_params().get("id"),
        "project_title": project.get_params().get("title"),
        "label_studio_url": url,
        "n_tasks": len(present) + len(new_tasks),
        "labeling_config_version": cfg.LABELING_CONFIG_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    cfg.EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    (cfg.EXPERIMENT_DIR / f"label_studio_project_{meta['mode']}.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
