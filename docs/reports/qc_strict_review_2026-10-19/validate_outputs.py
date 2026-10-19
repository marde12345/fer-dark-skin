"""Validation script for qc_strict_review_2026-10-19 outputs. Read-only.
Checks: row counts match claims, image paths exist, dims match claims,
Original/CLAHE pairing consistent, lineage back to source pools consistent.
Reports EVERY discrepancy found -- does not hide any.
"""
from pathlib import Path
import pandas as pd
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/reports/qc_strict_review_2026-10-19"

issues = []


def check(cond, msg):
    if not cond:
        issues.append(msg)


# 1. row count checks
v1_pass = pd.read_csv(OUT / "v1_candidates_passed_manifest.csv")
v1_rej = pd.read_csv(OUT / "v1_candidates_rejected_manifest.csv")
v2_pass = pd.read_csv(OUT / "v2_candidates_passed_manifest.csv")
v2_rej = pd.read_csv(OUT / "v2_candidates_rejected_manifest.csv")

check(len(v1_pass) + len(v1_rej) == 645, f"v1 passed+rejected = {len(v1_pass)+len(v1_rej)} != 645")
check(len(v2_pass) + len(v2_rej) == 3413, f"v2 passed+rejected = {len(v2_pass)+len(v2_rej)} != 3413")
print(f"v1 passed={len(v1_pass)} rejected={len(v1_rej)} total={len(v1_pass)+len(v1_rej)}")
print(f"v2 passed={len(v2_pass)} rejected={len(v2_rej)} total={len(v2_pass)+len(v2_rej)}")

# 2. no duplicate sample_ids within pool
for name, df in [("v1_pass", v1_pass), ("v1_rej", v1_rej), ("v2_pass", v2_pass), ("v2_rej", v2_rej)]:
    dup = df["sample_id"].duplicated().sum()
    check(dup == 0, f"{name} has {dup} duplicate sample_id rows")

v1_ids = set(v1_pass["sample_id"]) | set(v1_rej["sample_id"])
v2_ids = set(v2_pass["sample_id"]) | set(v2_rej["sample_id"])
check(len(set(v1_pass["sample_id"]) & set(v1_rej["sample_id"])) == 0, "v1 overlap between passed and rejected")
check(len(set(v2_pass["sample_id"]) & set(v2_rej["sample_id"])) == 0, "v2 overlap between passed and rejected")

# 3. image paths exist + dims match claims (sample full pass set, since manageable)
def verify_dims(df, wcol, hcol, pathcol, label, limit=None):
    n_checked = 0
    n_missing = 0
    n_mismatch = 0
    rows = df if limit is None else df.head(limit)
    for _, row in rows.iterrows():
        p_img = REPO / row[pathcol]
        if not p_img.exists():
            n_missing += 1
            issues.append(f"{label}: missing file {row[pathcol]} (sample_id={row['sample_id']})")
            continue
        with Image.open(p_img) as im:
            w, h = im.size
        n_checked += 1
        if w != row[wcol] or h != row[hcol]:
            n_mismatch += 1
            issues.append(f"{label}: dim mismatch sample_id={row['sample_id']} manifest=({row[wcol]}x{row[hcol]}) actual=({w}x{h})")
    print(f"{label}: checked={n_checked} missing={n_missing} mismatch={n_mismatch} (of {len(rows)} rows)")


v1_all = pd.concat([v1_pass, v1_rej])
v2_all = pd.concat([v2_pass, v2_rej])
verify_dims(v1_all, "qc_width", "qc_height", "original_path", "v1_all_original")
verify_dims(v2_all, "crop_width", "crop_height", "original_path", "v2_all_original")

# 4. Original/CLAHE pairing
def verify_clahe_pairing(df, label):
    missing_clahe = 0
    for _, row in df.iterrows():
        clahe_p = REPO / row["clahe_path"]
        if not clahe_p.exists():
            missing_clahe += 1
            issues.append(f"{label}: missing CLAHE pair for sample_id={row['sample_id']} expected {row['clahe_path']}")
    print(f"{label}: clahe missing = {missing_clahe}/{len(df)}")


verify_clahe_pairing(v1_all, "v1_all_clahe")
verify_clahe_pairing(v2_all, "v2_all_clahe")

# 5. lineage: sample_id must exist in source pool manifests
v1_src = pd.read_csv(REPO / "docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv")
v2_src = pd.read_csv(REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv")
v1_src_ids = set(v1_src["sample_id"])
v2_src_ids = set(v2_src["sample_id"])

missing_lineage_v1 = v1_ids - v1_src_ids
missing_lineage_v2 = v2_ids - v2_src_ids
check(len(missing_lineage_v1) == 0, f"v1: {len(missing_lineage_v1)} sample_ids not found in source pool manifest: {list(missing_lineage_v1)[:10]}")
check(len(missing_lineage_v2) == 0, f"v2: {len(missing_lineage_v2)} sample_ids not found in source pool manifest: {list(missing_lineage_v2)[:10]}")
check(v1_ids == v1_src_ids, f"v1: candidate manifest ids != full source pool ids (set diff sizes: {len(v1_ids - v1_src_ids)}, {len(v1_src_ids - v1_ids)})")
check(v2_ids == v2_src_ids, f"v2: candidate manifest ids != full source pool ids (set diff sizes: {len(v2_ids - v2_src_ids)}, {len(v2_src_ids - v2_ids)})")

# 6. XLSX / DOCX exist
check((OUT / "Papuan_V2_QC_Strict_Review.xlsx").exists(), "XLSX report missing")
check((OUT / "Papuan_V2_QC_Strict_Review.docx").exists(), "DOCX report missing")

print("\n=== VALIDATION RESULT ===")
if issues:
    print(f"{len(issues)} ISSUE(S) FOUND:")
    for i in issues:
        print(" -", i)
else:
    print("ALL CHECKS PASSED. No discrepancies found.")

with open(OUT / "validation_report.txt", "w") as f:
    if issues:
        f.write(f"{len(issues)} issues found:\n")
        for i in issues:
            f.write(f"- {i}\n")
    else:
        f.write("ALL CHECKS PASSED. No discrepancies found.\n")
