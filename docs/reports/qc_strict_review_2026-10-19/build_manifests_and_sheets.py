"""Build passed/rejected manifests and contact sheets for QC strict review.
Recommended candidate thresholds presented (NOT auto-adopted):
  - Candidate A (conservative/current): min_dim>=60, blur>75
  - Candidate B (moderate): min_dim>=80, blur>75
  - Candidate C (strict): min_dim>=96, blur>75
We label v1/v2 passed/rejected manifests using Candidate B (min_dim>=80, blur>75)
as the PRIMARY labeled candidate (clearly marked), while threshold_analysis.csv /
funnel files retain the full comparison across all candidates for the supervisor
to choose.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/reports/qc_strict_review_2026-10-19"
SHEETS = OUT / "contact_sheets"
SHEETS.mkdir(parents=True, exist_ok=True)

PRIMARY_MIN_DIM = 80
PRIMARY_BLUR = 75.0

v1 = pd.read_csv(OUT / "v1_pool_with_frontality.csv")
v2 = pd.read_csv(REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv")

# ---------------- v1 passed/rejected ----------------
v1_out = v1.copy()
v1_out["pass_resolution"] = v1_out["min_dim"] >= PRIMARY_MIN_DIM
v1_out["pass_blur"] = v1_out["qc_blur_variance"] > PRIMARY_BLUR
v1_out["pass_candidate_B"] = v1_out["pass_resolution"] & v1_out["pass_blur"]


def v1_reason(row):
    if row["pass_candidate_B"]:
        return "PASS"
    reasons = []
    if not row["pass_resolution"]:
        reasons.append(f"resolution_fail(min_dim={row['min_dim']}<{PRIMARY_MIN_DIM})")
    if not row["pass_blur"]:
        reasons.append(f"blur_fail(blur_var={row['qc_blur_variance']:.2f}<={PRIMARY_BLUR})")
    return ";".join(reasons)


v1_out["candidate_B_status"] = v1_out.apply(v1_reason, axis=1)
v1_out["threshold_label"] = "candidate_B_min80px_blur75 (NOT YET ADOPTED - see report for alternatives)"

cols_v1 = ["sample_id", "source_video_id", "frame_timestamp_seconds", "original_path", "clahe_path",
           "min_dim", "qc_width", "qc_height", "qc_blur_variance", "frontality_score", "frontal_bucket",
           "landmark_status", "expression_label_status", "pass_candidate_B", "candidate_B_status", "threshold_label"]

v1_pass = v1_out[v1_out["pass_candidate_B"]][cols_v1]
v1_rej = v1_out[~v1_out["pass_candidate_B"]][cols_v1]
v1_pass.to_csv(OUT / "v1_candidates_passed_manifest.csv", index=False)
v1_rej.to_csv(OUT / "v1_candidates_rejected_manifest.csv", index=False)
print(f"v1 passed (candidate B): {len(v1_pass)}  rejected: {len(v1_rej)}  total: {len(v1_out)}")

# ---------------- v2 passed/rejected ----------------
v2_out = v2.copy()
v2_out["pass_resolution"] = v2_out["qc_min_dim"] >= PRIMARY_MIN_DIM
v2_out["pass_blur"] = v2_out["qc_blur_variance"] > PRIMARY_BLUR
v2_out["pass_frontal"] = v2_out["frontal_bucket"].isin(["FRONTAL", "NEAR_FRONTAL"])
v2_out["pass_candidate_B"] = v2_out["pass_resolution"] & v2_out["pass_blur"] & v2_out["pass_frontal"]


def v2_reason(row):
    if row["pass_candidate_B"]:
        return "PASS"
    reasons = []
    if not row["pass_resolution"]:
        reasons.append(f"resolution_fail(min_dim={row['qc_min_dim']}<{PRIMARY_MIN_DIM})")
    if not row["pass_blur"]:
        reasons.append(f"blur_fail(blur_var={row['qc_blur_variance']:.2f}<={PRIMARY_BLUR})")
    if not row["pass_frontal"]:
        reasons.append(f"frontality_fail(bucket={row['frontal_bucket']})")
    return ";".join(reasons)


v2_out["candidate_B_status"] = v2_out.apply(v2_reason, axis=1)
v2_out["threshold_label"] = "candidate_B_min80px_blur75_frontal (NOT YET ADOPTED - see report for alternatives)"

cols_v2 = ["sample_id", "source_video_id", "frame_timestamp_seconds", "original_path", "clahe_path",
           "qc_min_dim", "crop_width", "crop_height", "qc_blur_variance", "frontality_score", "frontal_bucket",
           "visibility_flag", "pass_candidate_B", "candidate_B_status", "threshold_label"]

v2_pass = v2_out[v2_out["pass_candidate_B"]][cols_v2]
v2_rej = v2_out[~v2_out["pass_candidate_B"]][cols_v2]
v2_pass.to_csv(OUT / "v2_candidates_passed_manifest.csv", index=False)
v2_rej.to_csv(OUT / "v2_candidates_rejected_manifest.csv", index=False)
print(f"v2 passed (candidate B): {len(v2_pass)}  rejected: {len(v2_rej)}  total: {len(v2_out)}")

v1_out.to_csv(OUT / "v1_pool_full_with_candidateB.csv", index=False)
v2_out.to_csv(OUT / "v2_pool_full_with_candidateB.csv", index=False)

# ---------------- contact sheets ----------------

def make_contact_sheet(rows, title, out_path, thumb=160):
    n = len(rows)
    if n == 0:
        return
    cols = min(4, n)
    rows_n = (n + cols - 1) // cols
    cap_h = 46
    cell_w, cell_h = thumb, thumb + cap_h
    sheet = Image.new("RGB", (cols * cell_w, rows_n * cell_h + 30), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((5, 5), title, fill="black")
    for i, (img_path, caption) in enumerate(rows):
        r, c = divmod(i, cols)
        x0, y0 = c * cell_w, 30 + r * cell_h
        try:
            im = Image.open(img_path).convert("RGB")
            im.thumbnail((thumb, thumb))
            paste_x = x0 + (cell_w - im.width) // 2
            paste_y = y0 + (thumb - im.height) // 2
            sheet.paste(im, (paste_x, paste_y))
        except Exception as e:
            draw.text((x0 + 5, y0 + 5), "ERR", fill="red")
        for j, line in enumerate(caption.split("\n")):
            draw.text((x0 + 3, y0 + thumb + 2 + j * 11), line, fill="black")
    sheet.save(out_path)
    print(f"wrote {out_path} ({n} tiles)")


def dim_bucket_examples(df, dimcol, blurcol, pathcol, sidcol, threshold, n_each=4):
    below = df[(df[dimcol] < threshold) & (df[dimcol] >= threshold - 20)].sort_values(dimcol, ascending=False)
    above = df[(df[dimcol] >= threshold) & (df[dimcol] < threshold + 20)].sort_values(dimcol)
    rows = []
    for _, r in below.head(n_each).iterrows():
        rows.append((REPO / r[pathcol], f"{r[sidcol]}\n{r[dimcol]}px blur={r[blurcol]:.0f}\nREJECT(<{threshold})"))
    for _, r in above.head(n_each).iterrows():
        rows.append((REPO / r[pathcol], f"{r[sidcol]}\n{r[dimcol]}px blur={r[blurcol]:.0f}\nPASS(>={threshold})"))
    return rows


for thr in [60, 80, 96, 112]:
    rows = dim_bucket_examples(v1, "min_dim", "qc_blur_variance", "original_path", "sample_id", thr)
    make_contact_sheet(rows, f"v1 pool: reject-vs-pass near {thr}px (min dim)", SHEETS / f"v1_threshold_{thr}px.png")

for thr in [60, 80, 96, 112]:
    rows = dim_bucket_examples(v2, "qc_min_dim", "qc_blur_variance", "original_path", "sample_id", thr)
    make_contact_sheet(rows, f"v2 pool: reject-vs-pass near {thr}px (min dim)", SHEETS / f"v2_threshold_{thr}px.png")

# Combined comparison sheet at the moderate (80px) threshold for v1 vs v2 side by side
rows_v1_80 = dim_bucket_examples(v1, "min_dim", "qc_blur_variance", "original_path", "sample_id", 80, n_each=3)
rows_v2_80 = dim_bucket_examples(v2, "qc_min_dim", "qc_blur_variance", "original_path", "sample_id", 80, n_each=3)
make_contact_sheet(rows_v1_80 + rows_v2_80, "v1 vs v2 comparison at 80px threshold (v1 first, v2 second)", SHEETS / "comparison_v1_v2_80px.png")

print("Contact sheets complete.")
