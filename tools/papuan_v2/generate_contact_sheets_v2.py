"""Step 5: contact sheets for the v2 pool, PIL grid+caption, one sheet per
category: frontal, near_frontal, profile_excluded, blurry_excluded,
small_excluded, false_positive_candidate.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv"
OUT_DIR = REPO / "docs/reports/extraction_v2_2026-10-19/contact_sheets"
THUMB = 150
CAPTION_H = 60
COLS = 5


def make_sheet(rows: pd.DataFrame, title: str, out_path: Path, n=15):
    rows = rows.head(n)
    n_rows = max(1, (len(rows) + COLS - 1) // COLS)
    sheet = Image.new("RGB", (COLS * THUMB, n_rows * (THUMB + CAPTION_H) + 30), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((5, 5), title, fill=(0, 0, 0))
    for i, (_, row) in enumerate(rows.iterrows()):
        r, c = divmod(i, COLS)
        x0 = c * THUMB
        y0 = 30 + r * (THUMB + CAPTION_H)
        try:
            img = Image.open(REPO / row["original_path"]).convert("RGB")
            img.thumbnail((THUMB, THUMB))
            sheet.paste(img, (x0, y0))
        except Exception as e:
            draw.text((x0 + 2, y0 + 2), f"ERR:{e}", fill=(255, 0, 0))
        cap = (f"{row['sample_id']}\nblur={row['qc_blur_variance']:.0f} dim={row['qc_min_dim']}\n"
               f"front={row.get('frontality_score', 'NA')}")
        draw.text((x0 + 2, y0 + THUMB + 2), cap, fill=(0, 0, 0))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    print(f"wrote {out_path} ({len(rows)} thumbs)")


def main():
    df = pd.read_csv(MANIFEST)

    frontal = df[df["frontal_bucket"] == "FRONTAL"].sort_values("frontality_score", ascending=False)
    near = df[df["frontal_bucket"] == "NEAR_FRONTAL"]
    profile = df[df["frontal_bucket"] == "PROFILE"]
    blurry = df[df["qc_blur_variance"] <= 75]
    small = df[df["qc_min_dim"] < 60]
    low_conf = df.sort_values("det_score").head(15) if "det_score" in df.columns else df.iloc[0:0]

    make_sheet(frontal, "FRONTAL (included)", OUT_DIR / "frontal.jpg")
    make_sheet(near, "NEAR_FRONTAL (included)", OUT_DIR / "near_frontal.jpg")
    make_sheet(profile, "PROFILE (excluded)", OUT_DIR / "profile_excluded.jpg")
    make_sheet(blurry, "BLURRY (excluded, blur<=75)", OUT_DIR / "blurry_excluded.jpg")
    make_sheet(small, "SMALL (excluded, min_dim<60)", OUT_DIR / "small_excluded.jpg")
    make_sheet(low_conf, "LOW_DET_CONFIDENCE (false-positive spot-check)", OUT_DIR / "false_positive_candidate.jpg")


if __name__ == "__main__":
    main()
