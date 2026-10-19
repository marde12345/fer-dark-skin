"""Step 7: validate the final delivery package.

Checks:
1. Every standardized image is exactly 224x224 (all 462).
2. Original/CLAHE standardized dimensions match pairwise.
3. Every path referenced in final_sample_manifest.csv exists on disk.
4. sample_id uniqueness (231, no dupes).
5. Landmark coordinate sanity: all x/y in [0,224], flag out-of-bounds.
6. Annotation-status counts in the manifest match a fresh recount from
   source files (not trusting Step 4's own printed counts).
7. Source-to-sample lineage: sampled_frame_index/source_frame_index match
   the original per_face_sample_manifest.csv row for each sample_id.

Prints PASS/FAIL per check with counts. Exits non-zero if any check fails.
"""
import csv
import json
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
DELIVERY = REPO / "delivery/papuan_v2_final_2026-10-19"
FINAL_MANIFEST = DELIVERY / "04_Manifests/final_sample_manifest.csv"
ORIG_DIR = DELIVERY / "02_Images/Original"
CLAHE_DIR = DELIVERY / "02_Images/CLAHE"
INITIAL_DIR = DELIVERY / "03_Landmarks/Initial"
REVIEWED_DIR = DELIVERY / "03_Landmarks/Reviewed"
PER_FACE_MANIFEST = REPO / "docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv"

failures = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    rows = list(csv.DictReader(open(FINAL_MANIFEST)))

    # 1. Every standardized image is exactly 224x224
    bad_size = []
    orig_files = sorted(ORIG_DIR.glob("*.jpg"))
    clahe_files = sorted(CLAHE_DIR.glob("*.jpg"))
    for p in orig_files + clahe_files:
        im = Image.open(p)
        if im.size != (224, 224):
            bad_size.append((str(p), im.size))
    check("1. All standardized images are 224x224",
          len(bad_size) == 0 and len(orig_files) == 231 and len(clahe_files) == 231,
          f"orig={len(orig_files)}, clahe={len(clahe_files)}, bad_size={len(bad_size)} {bad_size[:5]}")

    # 2. Original/CLAHE dims match pairwise (both already forced 224x224 so
    # this is checking file presence pairing, i.e. no orphan)
    orig_ids = {p.stem for p in orig_files}
    clahe_ids = {p.stem for p in clahe_files}
    mismatch = orig_ids.symmetric_difference(clahe_ids)
    check("2. Original/CLAHE sample_id sets match pairwise", len(mismatch) == 0,
          f"mismatched: {sorted(mismatch)[:10]}")

    # 3. Every path in final_sample_manifest.csv exists on disk
    missing_paths = []
    path_cols = ["original_path", "clahe_path", "standardized_original_path",
                 "standardized_clahe_path", "landmark_initial_path"]
    for r in rows:
        for col in path_cols:
            val = r[col]
            if val in ("NOT_AVAILABLE",) or val.startswith("NOT_AVAILABLE"):
                continue
            full = REPO / val if col in ("original_path", "clahe_path") else DELIVERY / val
            if not full.exists():
                missing_paths.append((r["sample_id"], col, str(full)))
        rv = r["landmark_reviewed_path"]
        if rv != "NOT_AVAILABLE":
            full = DELIVERY / rv
            if not full.exists():
                missing_paths.append((r["sample_id"], "landmark_reviewed_path", str(full)))
    check("3. Every manifest path exists on disk", len(missing_paths) == 0,
          f"missing={len(missing_paths)} {missing_paths[:5]}")

    # 4. sample_id uniqueness
    ids = [r["sample_id"] for r in rows]
    check("4. sample_id uniqueness (231, no dupes)",
          len(ids) == 231 and len(set(ids)) == 231,
          f"rows={len(ids)}, unique={len(set(ids))}")

    # 5. Landmark coordinate sanity: all x/y in [0,224]
    oob = []
    checked_files = 0
    for d, label in [(INITIAL_DIR, "initial"), (REVIEWED_DIR, "reviewed")]:
        for p in d.glob("*.json"):
            obj = json.load(open(p))
            checked_files += 1
            for pt in obj["points"]:
                if not (0 <= pt["x"] <= 224 and 0 <= pt["y"] <= 224):
                    oob.append((label, obj["sample_id"], pt["source_index"], pt["x"], pt["y"]))
    check("5. All landmark coordinates within [0,224]", len(oob) == 0,
          f"checked_files={checked_files}, out_of_bounds={len(oob)} {oob[:5]}")

    # 6. Annotation-status counts: fresh recount vs manifest's own values
    recount_label_complete = sum(1 for r in rows if r["expression_label"] != "NOT_AVAILABLE")
    manifest_label_complete = sum(1 for r in rows if r["expression_label_status"] == "complete")
    recount_landmark_reviewed_files = len(list(REVIEWED_DIR.glob("*.json")))
    manifest_landmark_complete = sum(1 for r in rows if r["landmark_status"] == "complete")
    check("6a. expression_label presence matches expression_label_status=complete count",
          recount_label_complete == manifest_label_complete,
          f"recount={recount_label_complete}, manifest={manifest_label_complete}")
    check("6b. Reviewed-landmark file count matches landmark_status=complete count",
          recount_landmark_reviewed_files == manifest_landmark_complete,
          f"recount={recount_landmark_reviewed_files}, manifest={manifest_landmark_complete}")
    recount_initial_files = len(list(INITIAL_DIR.glob("*.json")))
    check("6c. Initial-landmark file count == 231 (all samples)",
          recount_initial_files == 231, f"recount={recount_initial_files}")

    # 7. Source-to-sample lineage against per_face_sample_manifest.csv
    per_face = {r["sample_id"]: r for r in csv.DictReader(open(PER_FACE_MANIFEST))}
    lineage_mismatches = []
    for r in rows:
        sid = r["sample_id"]
        src = per_face.get(sid)
        if src is None:
            lineage_mismatches.append((sid, "missing_from_per_face_manifest"))
            continue
        if str(src["sampled_frame_index"]) != str(r["sampled_frame_index"]):
            lineage_mismatches.append((sid, "sampled_frame_index mismatch",
                                        src["sampled_frame_index"], r["sampled_frame_index"]))
        if str(src["source_frame_index"]) != str(r["source_frame_index"]):
            lineage_mismatches.append((sid, "source_frame_index mismatch",
                                        src["source_frame_index"], r["source_frame_index"]))
    check("7. sample_id lineage matches per_face_sample_manifest.csv",
          len(lineage_mismatches) == 0,
          f"mismatches={len(lineage_mismatches)} {lineage_mismatches[:5]}")

    print()
    if failures:
        print(f"OVERALL: FAIL ({len(failures)} check(s) failed): {failures}")
        sys.exit(1)
    else:
        print("OVERALL: PASS (all checks passed)")


if __name__ == "__main__":
    main()
