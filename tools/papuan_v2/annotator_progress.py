"""EXP-PAP-004: machine-readable multi-annotator progress snapshot for
the dashboard (not built yet, per scope -- this only produces the
artifact it will later read).

Writes experiments/EXP-PAP-004/annotator_progress.json with:
    experiment_id, dataset_version, pilot_size,
    annotator_A_assigned, annotator_B_assigned, overlap_size,
    annotator_A_completed, annotator_B_completed,
    human_human_agreement, disagreements, adjudicated,
    project_A_id, project_A_url, project_B_id, project_B_url,
    generated_at

Queries Project A (always expected to be reachable) and Project B
(best-effort -- B's server may not exist yet if Annotator B hasn't been
set up, which is a normal, non-error state early in the workflow).
human_human_agreement/disagreements/adjudicated are read from
experiments/EXP-PAP-004/human_human_agreement.json if it exists (written
by human_agreement_report.py), otherwise reported as null/"not_computed"
-- this script never computes agreement itself, only surfaces it.
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
    ANNOTATOR_B_OVERLAP_SIZE,
    PROJECT_TITLE,
    PROJECT_TITLE_B,
    expected_pilot_image_ids,
)

OUTPUT_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "annotator_progress.json"
AGREEMENT_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "human_human_agreement.json"


def _project_progress(url: str | None, api_key: str | None, title: str) -> dict | None:
    if not url or not api_key:
        return None
    try:
        from label_studio_sdk._legacy.client import Client

        client = Client(url=url, api_key=api_key)
        client.check_connection()
    except Exception:  # noqa: BLE001 -- server simply not up yet; not an error for this script
        return None

    for project in client.get_projects():
        params = project.get_params()
        if params.get("title") == title:
            tasks = project.get_tasks()
            completed = sum(1 for t in tasks if t.get("total_annotations", 0) > 0)
            return {"project_id": params.get("id"), "project_url": url, "completed": completed, "total": len(tasks)}
    return None


def _load_agreement() -> dict:
    if not AGREEMENT_PATH.exists():
        return {"human_human_agreement": None, "disagreements": None, "adjudicated": False, "status": "not_computed"}
    data = json.loads(AGREEMENT_PATH.read_text())
    return {
        "human_human_agreement": {"raw_agreement": data.get("raw_agreement"), "cohens_kappa": data.get("cohens_kappa")},
        "disagreements": data.get("n_disagreements"),
        "adjudicated": data.get("adjudicated", False),
        "status": "computed",
    }


def run(url_a: str, key_a: str, url_b: str | None, key_b: str | None) -> dict:
    pilot_size = len(expected_pilot_image_ids())
    progress_a = _project_progress(url_a, key_a, PROJECT_TITLE)
    progress_b = _project_progress(url_b, key_b, PROJECT_TITLE_B)
    agreement = _load_agreement()

    metadata = {
        "experiment_id": "EXP-PAP-004",
        "dataset_version": "papuan_v2",
        "pilot_size": pilot_size,
        "annotator_A_assigned": pilot_size,
        "annotator_B_assigned": ANNOTATOR_B_OVERLAP_SIZE,
        "overlap_size": ANNOTATOR_B_OVERLAP_SIZE,
        "annotator_A_completed": progress_a["completed"] if progress_a else None,
        "annotator_B_completed": progress_b["completed"] if progress_b else None,
        "project_A_id": progress_a["project_id"] if progress_a else None,
        "project_A_url": url_a if progress_a else None,
        "project_B_id": progress_b["project_id"] if progress_b else None,
        "project_B_url": url_b if progress_b else None,
        **agreement,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(metadata, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-a", default=os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080"))
    parser.add_argument("--api-key-a", default=os.environ.get("LABEL_STUDIO_API_KEY"))
    parser.add_argument("--url-b", default=os.environ.get("LABEL_STUDIO_B_URL", "http://localhost:8081"))
    parser.add_argument("--api-key-b", default=os.environ.get("LABEL_STUDIO_B_API_KEY"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.api_key_a:
        raise SystemExit("LABEL_STUDIO_API_KEY is not set.")
    result = run(args.url_a, args.api_key_a, args.url_b, args.api_key_b)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
