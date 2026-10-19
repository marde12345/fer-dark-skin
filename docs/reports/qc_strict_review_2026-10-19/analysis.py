"""QC Strict Review 2026-10-19 — analysis script (read-only on all source data).
Writes outputs ONLY under docs/reports/qc_strict_review_2026-10-19/.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import cv2
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/reports/qc_strict_review_2026-10-19"
OUT.mkdir(parents=True, exist_ok=True)

V1_POOL = REPO / "docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv"
V2_POOL = REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv"
V1_DELIV = REPO / "delivery/papuan_v2_final_2026-10-19/04_Manifests/final_sample_manifest.csv"
V2_DELIV_TRANSFORM = REPO / "delivery/papuan_v2_v2_candidate_2026-10-19/04_Manifests/_standardization_transform_v2.csv"

RES_THRESHOLDS = [60, 80, 96, 112]
BLUR_THRESHOLDS = {"blur75": 75.0, "blurP75": 325.3481}

OFFSET_PROFILE_THRESHOLD = 0.6


def frontality_for(lm: np.ndarray):
    x36, x45 = lm[36, 0], lm[45, 0]
    x30 = lm[30, 0]
    eye_mid_x = (x36 + x45) / 2.0
    denom = (x45 - x36)
    if abs(denom) < 1e-6:
        return float("nan"), float("nan")
    offset = (x30 - eye_mid_x) / denom
    score = 1.0 - min(1.0, abs(offset) / OFFSET_PROFILE_THRESHOLD)
    return round(max(0.0, score), 4), round(float(offset), 4)


def frontal_bucket(s):
    if pd.isna(s):
        return "UNKNOWN"
    if s >= 0.7:
        return "FRONTAL"
    if s >= 0.4:
        return "NEAR_FRONTAL"
    return "PROFILE"


# ---------------------------------------------------------------------------
# 1. Load pools
# ---------------------------------------------------------------------------
print("Loading v1 pool...")
v1 = pd.read_csv(V1_POOL)
print(f"  v1 pool rows: {len(v1)}")
print("Loading v2 pool...")
v2 = pd.read_csv(V2_POOL)
print(f"  v2 pool rows: {len(v2)}")

# v1 uses qc_width/qc_height (== crop_width/crop_height, verified below), qc_blur_variance
v1["min_dim"] = v1[["qc_width", "qc_height"]].min(axis=1)
v2["min_dim"] = v2["qc_min_dim"]

# ---------------------------------------------------------------------------
# 1b. Verify dims against real image files (sample check)
# ---------------------------------------------------------------------------
verify_rows = []
rng = np.random.default_rng(42)
v1_sample_idx = rng.choice(len(v1), size=min(25, len(v1)), replace=False)
for i in v1_sample_idx:
    row = v1.iloc[i]
    p = REPO / row["original_path"]
    ok = p.exists()
    actual_w = actual_h = None
    match = "NOT_FOUND"
    if ok:
        with Image.open(p) as im:
            actual_w, actual_h = im.size
        match = "MATCH" if (actual_w == row["qc_width"] and actual_h == row["qc_height"]) else "MISMATCH"
    verify_rows.append({
        "pool": "v1", "sample_id": row["sample_id"], "path": row["original_path"],
        "manifest_w": row["qc_width"], "manifest_h": row["qc_height"],
        "actual_w": actual_w, "actual_h": actual_h, "result": match,
    })

v2_sample_idx = rng.choice(len(v2), size=min(25, len(v2)), replace=False)
for i in v2_sample_idx:
    row = v2.iloc[i]
    p = REPO / row["original_path"]
    ok = p.exists()
    actual_w = actual_h = None
    match = "NOT_FOUND"
    if ok:
        with Image.open(p) as im:
            actual_w, actual_h = im.size
        match = "MATCH" if (actual_w == row["crop_width"] and actual_h == row["crop_height"]) else "MISMATCH"
    verify_rows.append({
        "pool": "v2", "sample_id": row["sample_id"], "path": row["original_path"],
        "manifest_w": row["crop_width"], "manifest_h": row["crop_height"],
        "actual_w": actual_w, "actual_h": actual_h, "result": match,
    })

# v1 delivery (resized) check: source_width/height vs standardized_original_path actual (should be 224x224 after resize+pad)
v1d = pd.read_csv(V1_DELIV)
for i in rng.choice(len(v1d), size=min(15, len(v1d)), replace=False):
    row = v1d.iloc[i]
    p_orig = REPO / row["original_path"]
    p_std = REPO / row["standardized_original_path"]
    orig_match = "NOT_FOUND"
    if p_orig.exists():
        with Image.open(p_orig) as im:
            aw, ah = im.size
        orig_match = "MATCH" if (aw == row["source_width"] and ah == row["source_height"]) else f"MISMATCH({aw}x{ah})"
    std_dim = "NOT_FOUND"
    if p_std.exists():
        with Image.open(p_std) as im:
            std_dim = f"{im.size[0]}x{im.size[1]}"
    verify_rows.append({
        "pool": "v1_delivery_resize", "sample_id": row["sample_id"], "path": row["original_path"],
        "manifest_w": row["source_width"], "manifest_h": row["source_height"],
        "actual_w": orig_match, "actual_h": std_dim, "result": orig_match,
    })

v2t = pd.read_csv(V2_DELIV_TRANSFORM)
print("v2 standardization transform columns:", list(v2t.columns))
for i in rng.choice(len(v2t), size=min(15, len(v2t)), replace=False):
    row = v2t.iloc[i]
    sid = row["sample_id"]
    sw = row.get("source_width"); sh = row.get("source_height")
    verify_rows.append({
        "pool": "v2_delivery_transform", "sample_id": sid, "path": "",
        "manifest_w": sw, "manifest_h": sh, "actual_w": "see_v2_pool_crossref", "actual_h": "",
        "result": "LOGGED",
    })

verify_df = pd.DataFrame(verify_rows)
verify_df.to_csv(OUT / "dimension_verification_sample.csv", index=False)
print("Dimension verification mismatches:", (verify_df["result"].astype(str).str.contains("MISMATCH")).sum())

# ---------------------------------------------------------------------------
# 2. Threshold analysis table
# ---------------------------------------------------------------------------
thr_rows = []
for pool_name, df, dimcol, blurcol in [("v1", v1, "min_dim", "qc_blur_variance"), ("v2", v2, "min_dim", "qc_blur_variance")]:
    total = len(df)
    for r in RES_THRESHOLDS:
        n = (df[dimcol] >= r).sum()
        thr_rows.append({"pool": pool_name, "metric": "min_dim_crop_original", "threshold": f">={r}px", "n_pass": int(n), "total": total, "pct": round(100*n/total, 2)})
    for bname, bval in BLUR_THRESHOLDS.items():
        n = (df[blurcol] > bval).sum()
        thr_rows.append({"pool": pool_name, "metric": "blur_variance", "threshold": f">{bval} ({bname})", "n_pass": int(n), "total": total, "pct": round(100*n/total, 2)})
thr_df = pd.DataFrame(thr_rows)
thr_df.to_csv(OUT / "threshold_analysis.csv", index=False)
print(thr_df.to_string())

# ---------------------------------------------------------------------------
# 3. v1 frontality (only where landmarks available)
# ---------------------------------------------------------------------------
print("\nComputing v1 frontality where landmarks are available...")
v1["frontality_score"] = np.nan
v1["frontality_offset"] = np.nan
v1["frontal_bucket"] = "NOT_EVALUATED_NO_LANDMARKS"

landmark_cache = {}

def load_landmark_file(path_str):
    if path_str in landmark_cache:
        return landmark_cache[path_str]
    full = REPO / path_str
    try:
        data = json.loads(full.read_text())
    except Exception:
        data = None
    landmark_cache[path_str] = data
    return data

n_computed = 0
n_landmark_rows = 0
for idx, row in v1.iterrows():
    lp = row["landmark_initial_path"]
    if lp == "NOT_AVAILABLE" or not isinstance(lp, str):
        continue
    n_landmark_rows += 1
    data = load_landmark_file(lp)
    if data is None:
        continue
    sid = row["sample_id"]
    rec = None
    if isinstance(data, dict):
        rec = data.get(sid)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("image_id") == sid:
                rec = item
                break
    if rec is None or "landmarks_xy" not in rec:
        continue
    lm = np.array(rec["landmarks_xy"])
    if lm.shape[0] < 68:
        continue
    score, offset = frontality_for(lm)
    v1.at[idx, "frontality_score"] = score
    v1.at[idx, "frontality_offset"] = offset
    v1.at[idx, "frontal_bucket"] = frontal_bucket(score)
    n_computed += 1

print(f"v1 rows with a landmark_initial_path reference: {n_landmark_rows}")
print(f"v1 rows where frontality was actually computed from landmarks_xy: {n_computed}")
print(v1["frontal_bucket"].value_counts())

v1.to_csv(OUT / "v1_pool_with_frontality.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Funnel tables (consistent denominator = pool total)
# ---------------------------------------------------------------------------

def build_funnel(df, dimcol, blurcol, pool_total, has_frontal_col):
    rows = []
    rows.append({"stage": "Total pool (all detected faces)", "n": pool_total, "pct_of_total": 100.0})
    for r in RES_THRESHOLDS:
        n = (df[dimcol] >= r).sum()
        rows.append({"stage": f"Pass resolution >= {r}px (min dim)", "n": int(n), "pct_of_total": round(100*n/pool_total, 2)})
    for bname, bval in BLUR_THRESHOLDS.items():
        n = (df[blurcol] > bval).sum()
        rows.append({"stage": f"Pass blur > {bval} ({bname})", "n": int(n), "pct_of_total": round(100*n/pool_total, 2)})
    for r in RES_THRESHOLDS:
        for bname, bval in BLUR_THRESHOLDS.items():
            n = ((df[dimcol] >= r) & (df[blurcol] > bval)).sum()
            rows.append({"stage": f"Pass res>={r}px AND blur>{bval}({bname}) [JOINT]", "n": int(n), "pct_of_total": round(100*n/pool_total, 2)})
    if has_frontal_col:
        n = (df["frontal_bucket"].isin(["FRONTAL", "NEAR_FRONTAL"])).sum()
        rows.append({"stage": "Pass frontality (FRONTAL or NEAR_FRONTAL)", "n": int(n), "pct_of_total": round(100*n/pool_total, 2)})
        # joint with best combos
        for r in RES_THRESHOLDS:
            for bname, bval in BLUR_THRESHOLDS.items():
                n = ((df[dimcol] >= r) & (df[blurcol] > bval) & (df["frontal_bucket"].isin(["FRONTAL", "NEAR_FRONTAL"]))).sum()
                rows.append({"stage": f"JOINT res>={r} AND blur>{bval}({bname}) AND frontal", "n": int(n), "pct_of_total": round(100*n/pool_total, 2)})
    else:
        rows.append({"stage": "Pass frontality", "n": "NOT_EVALUATED (no stored frontality scores for this pool previously; see v1 landmark-based computation separately where available)", "pct_of_total": ""})
    return pd.DataFrame(rows)

funnel_v1 = build_funnel(v1, "min_dim", "qc_blur_variance", len(v1), has_frontal_col=False)
funnel_v1_landmark_subset = build_funnel(
    v1[v1["frontal_bucket"] != "NOT_EVALUATED_NO_LANDMARKS"].copy(),
    "min_dim", "qc_blur_variance",
    (v1["frontal_bucket"] != "NOT_EVALUATED_NO_LANDMARKS").sum(),
    has_frontal_col=True,
) if n_computed > 0 else None

funnel_v2 = build_funnel(v2, "min_dim", "qc_blur_variance", len(v2), has_frontal_col=True)

funnel_v1.to_csv(OUT / "funnel_v1.csv", index=False)
funnel_v2.to_csv(OUT / "funnel_v2.csv", index=False)
if funnel_v1_landmark_subset is not None:
    funnel_v1_landmark_subset.to_csv(OUT / "funnel_v1_landmark_subset.csv", index=False)

print("\n=== FUNNEL V1 ===")
print(funnel_v1.to_string())
print("\n=== FUNNEL V2 ===")
print(funnel_v2.to_string())

print("\nDone with core analysis.")
