"""EXP-012: render 42-point landmark overlays for the 227 legacy crops.

Reads (never modifies): the legacy crops and the existing landmark files listed
in relabel_config.py. Generates no new landmarks.

Writes:
  - <data-root>/data/exp012/overlays/<image_id>.png -- an enlarged COPY of each
    crop with eyebrow/eye/mouth points drawn and a status banner
    (REVIEWED / UNREVIEWED PROPOSAL / MISSING). Git-ignored, regenerable.
  - experiments/EXP-012-relabel/landmark_sources.csv -- which source each crop used.

Run:
    uv run python tools/exp012/render_overlays.py --data-root /path/to/main/checkout
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import relabel_config as cfg  # noqa: E402

DISPLAY_MIN_SIDE = 280
COLORS = {"brow": (0, 200, 255), "eye": (0, 255, 0), "mouth": (255, 80, 255)}  # BGR
BANNER = {
    cfg.STATUS_REVIEWED: ("REVIEWED", (0, 140, 0)),
    cfg.STATUS_PROPOSAL: ("UNREVIEWED PROPOSAL", (0, 120, 230)),
    cfg.STATUS_MISSING: ("NO LANDMARKS", (60, 60, 200)),
}


def region_of(index: int) -> str:
    return next(name for name, rng in cfg.REGIONS.items() if index in rng)


def render(image_path: Path, landmark: dict, out_path: Path) -> None:
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(image_path)
    scale = max(1.0, DISPLAY_MIN_SIDE / min(img.shape[:2]))
    canvas = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    radius = max(2, round(canvas.shape[1] / 110))
    for i, (x, y) in landmark["points"].items():
        cv2.circle(canvas, (round(x * scale), round(y * scale)), radius, COLORS[region_of(i)], -1, cv2.LINE_AA)
    text, color = BANNER[landmark["status"]]
    banner_h = 26
    canvas = cv2.copyMakeBorder(canvas, banner_h, 0, 0, 0, cv2.BORDER_CONSTANT, value=color)
    cv2.putText(canvas, text, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-root", type=Path, default=cfg.REPO_ROOT,
                        help="Checkout whose git-ignored data/ holds the legacy crops (default: this repo).")
    parser.add_argument("--only", nargs="*", help="Render only these image_ids (e.g. the verification sample).")
    args = parser.parse_args(argv)

    image_ids = cfg.legacy_image_ids(args.data_root)
    if len(image_ids) != 227:
        raise SystemExit(f"expected 227 legacy crops, found {len(image_ids)} under {args.data_root / cfg.LEGACY_FACES_REL}")
    landmarks = cfg.resolve_landmarks(image_ids)
    overlay_dir = args.data_root / cfg.OVERLAY_REL
    for image_id in (args.only or image_ids):
        render(args.data_root / cfg.LEGACY_FACES_REL / f"{image_id}.jpg", landmarks[image_id], overlay_dir / f"{image_id}.png")

    cfg.EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(cfg.EXPERIMENT_DIR / "landmark_sources.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["image_id", "landmark_status", "landmark_source", "n_points"])
        w.writeheader()
        for image_id in image_ids:
            lm = landmarks[image_id]
            w.writerow({"image_id": image_id, "landmark_status": lm["status"],
                        "landmark_source": lm["source"], "n_points": len(lm["points"])})
    counts = {s: sum(lm["status"] == s for lm in landmarks.values()) for s in BANNER}
    print(f"Rendered {len(args.only or image_ids)} overlay(s) to {overlay_dir}; status counts {counts}")


if __name__ == "__main__":
    main()
