"""Standardize the 231 frozen-candidate original + CLAHE crops to 224x224
via aspect-preserving resize + centered black letterbox padding.

Reads: docs/reports/frozen_candidate_v1_2026-10-19/frozen_candidate_manifest.csv
Writes: delivery/papuan_v2_final_2026-10-19/02_Images/{Original,CLAHE}/{sample_id}.jpg
Outputs a side-table of per-sample transform params (for merging into the
final manifest in step 2) to delivery/papuan_v2_final_2026-10-19/04_Manifests/_standardization_transform.csv

Does NOT touch data/papuan_v2/faces or data/papuan_v2/clahe (read-only there).
"""
import csv
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "docs/reports/frozen_candidate_v1_2026-10-19/frozen_candidate_manifest.csv"
OUT_ROOT = REPO / "delivery/papuan_v2_final_2026-10-19/02_Images"
OUT_ORIG = OUT_ROOT / "Original"
OUT_CLAHE = OUT_ROOT / "CLAHE"
TRANSFORM_CSV = REPO / "delivery/papuan_v2_final_2026-10-19/04_Manifests/_standardization_transform.csv"

TARGET = 224


def letterbox(img: Image.Image):
    w, h = img.size
    scale = TARGET / max(w, h)
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    resized = img.resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new("RGB", (TARGET, TARGET), (0, 0, 0))
    pad_left = (TARGET - new_w) // 2
    pad_top = (TARGET - new_h) // 2
    canvas.paste(resized, (pad_left, pad_top))
    pad_right = TARGET - new_w - pad_left
    pad_bottom = TARGET - new_h - pad_top
    return canvas, scale, pad_left, pad_top, pad_right, pad_bottom


def process_sample(sample_id: str, orig_path: Path, clahe_path: Path):
    orig = Image.open(orig_path).convert("RGB")
    clahe = Image.open(clahe_path).convert("RGB")
    assert orig.size == clahe.size, f"{sample_id}: original/CLAHE size mismatch {orig.size} vs {clahe.size}"

    out_orig, scale, pad_l, pad_t, pad_r, pad_b = letterbox(orig)
    # Apply the SAME scale+padding to CLAHE (not re-derived) to guarantee identical geometry.
    w, h = clahe.size
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    resized_clahe = clahe.resize((new_w, new_h), Image.BILINEAR)
    canvas_clahe = Image.new("RGB", (TARGET, TARGET), (0, 0, 0))
    canvas_clahe.paste(resized_clahe, (pad_l, pad_t))

    out_orig.save(OUT_ORIG / f"{sample_id}.jpg", quality=95)
    canvas_clahe.save(OUT_CLAHE / f"{sample_id}.jpg", quality=95)

    return {
        "sample_id": sample_id,
        "source_width": orig.size[0],
        "source_height": orig.size[1],
        "scale_factor": scale,
        "pad_left": pad_l,
        "pad_top": pad_t,
        "pad_right": pad_r,
        "pad_bottom": pad_b,
    }


def main():
    rows = list(csv.DictReader(open(FROZEN)))
    assert len(rows) == 231, f"expected 231 frozen rows, got {len(rows)}"

    spot_check = "--spot-check" in sys.argv
    only_n = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            only_n = int(a.split("=")[1])

    if spot_check:
        rows = rows[:3]
    elif only_n:
        rows = rows[:only_n]

    transforms = []
    failures = []
    for row in rows:
        sample_id = row["sample_id"]
        orig_path = REPO / row["original_path"]
        clahe_path = REPO / row["clahe_path"]
        try:
            t = process_sample(sample_id, orig_path, clahe_path)
            transforms.append(t)
        except Exception as e:
            failures.append((sample_id, str(e)))

    print(f"processed: {len(transforms)}/{len(rows)}")
    if failures:
        print("FAILURES:", failures)

    if not spot_check:
        mode = "a" if TRANSFORM_CSV.exists() and only_n else "w"
        write_header = not (TRANSFORM_CSV.exists() and only_n)
        with open(TRANSFORM_CSV, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(transforms[0].keys()) if transforms else [
                "sample_id", "source_width", "source_height", "scale_factor",
                "pad_left", "pad_top", "pad_right", "pad_bottom"])
            if write_header:
                writer.writeheader()
            writer.writerows(transforms)
        print("wrote", TRANSFORM_CSV)


if __name__ == "__main__":
    main()
