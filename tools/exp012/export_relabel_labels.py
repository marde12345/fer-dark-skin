"""EXP-012: export round-2 labels from the EXP-012 Label Studio project.

Writes only experiments/EXP-012-relabel/labels_round2.csv (or --out). Never
reads or writes any round-1 label file. Refuses to overwrite an existing
output unless --force is given.

Run:
    uv run --group labeling python tools/exp012/export_relabel_labels.py
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import relabel_config as cfg  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project-title", default=cfg.PROJECT_TITLE)
    parser.add_argument("--out", type=Path, default=cfg.EXPERIMENT_DIR / "labels_round2.csv")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    args = parser.parse_args(argv)

    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} exists; pass --force to overwrite it.")

    from ls_client import make_client

    client = make_client(os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080"),
                         os.environ["LABEL_STUDIO_API_KEY"])
    project = next((p for p in client.get_projects() if p.get_params().get("title") == args.project_title), None)
    if project is None:
        raise SystemExit(f"project {args.project_title!r} not found")
    users = {u.get("id"): u.get("email", "") for u in client.make_request("GET", "/api/users").json()}
    rows = cfg.label_rows_from_tasks(project.get_tasks(), users)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cfg.LABELS_FIELDNAMES)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} annotation row(s) for {len({r['image_id'] for r in rows})} crop(s) to {args.out}")


if __name__ == "__main__":
    main()
