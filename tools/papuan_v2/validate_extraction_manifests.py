"""
Validate docs/reports/extraction_audit_2026-10-19/frame_level_extraction_manifest.csv
and per_face_sample_manifest.csv against the real files on disk.

Checks:
  1. Every path referenced in either manifest exists on disk.
  2. sample_id uniqueness (no duplicate crops) in per_face_sample_manifest.csv.
  3. bbox fields are either NOT_AVAILABLE or a valid (non-negative, in-range) box.
  4. Frame indices are non-negative; sampled_frame_index is monotonic/unique
     within frame_level_extraction_manifest.csv (one video here, so "within a
     video" == "across the whole file").
  5. original vs CLAHE crop dimension correspondence, verified by actually
     opening both files for every sample with has_clahe=True.
  6. Every sample_id referenced in landmark/label source files also appears in
     per_face_sample_manifest.csv, and vice versa (orphan check both directions).

Usage: uv run python tools/papuan_v2/validate_extraction_manifests.py
"""
import csv
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs/reports/extraction_audit_2026-10-19"
FRAME_CSV = OUT_DIR / "frame_level_extraction_manifest.csv"
SAMPLE_CSV = OUT_DIR / "per_face_sample_manifest.csv"

EXP004 = ROOT / "experiments/EXP-PAP-004"
EXP005 = ROOT / "experiments/EXP-PAP-005"

NA = "NOT_AVAILABLE"


def load_csv(p):
    with open(p) as f:
        return list(csv.DictReader(f))


def load_json(p):
    with open(p) as f:
        return json.load(f)


def main():
    errors = []
    warnings = []

    frame_rows = load_csv(FRAME_CSV)
    sample_rows = load_csv(SAMPLE_CSV)

    # --- Check 1: path existence ---
    missing_paths = []
    for r in sample_rows:
        for col in ("original_path", "clahe_path", "landmark_initial_path", "landmark_reviewed_path"):
            v = r[col]
            if v and v != NA:
                if not (ROOT / v).exists():
                    missing_paths.append((r["sample_id"], col, v))
    if missing_paths:
        for sid, col, v in missing_paths:
            errors.append(f"[path-missing] {sid}: {col}={v} does not exist on disk")
    print(f"Check 1 (path existence): {len(missing_paths)} missing out of "
          f"{len(sample_rows) * 2} original/clahe path checks (+landmark paths)")

    # --- Check 2: sample_id uniqueness ---
    ids = [r["sample_id"] for r in sample_rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"[duplicate-sample-id] {len(dupes)} duplicate sample_id values: {sorted(dupes)[:10]}")
    print(f"Check 2 (sample_id uniqueness): {len(ids)} rows, {len(set(ids))} unique, "
          f"{len(dupes)} duplicated ids")

    # --- Check 3: bbox validity (NOT_AVAILABLE is exempt, not a failure) ---
    bbox_bad = 0
    bbox_exempt = 0
    for r in sample_rows:
        vals = [r["bbox_x"], r["bbox_y"], r["bbox_w"], r["bbox_h"]]
        if all(v == NA for v in vals):
            bbox_exempt += 1
            continue
        if any(v == NA for v in vals):
            errors.append(f"[bbox-partial] {r['sample_id']}: mixed NOT_AVAILABLE and real bbox values")
            bbox_bad += 1
            continue
        try:
            x, y, w, h = (float(v) for v in vals)
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                errors.append(f"[bbox-invalid] {r['sample_id']}: bbox out of valid range {vals}")
                bbox_bad += 1
        except ValueError:
            errors.append(f"[bbox-unparseable] {r['sample_id']}: {vals}")
            bbox_bad += 1
    print(f"Check 3 (bbox validity): {bbox_exempt} exempt (NOT_AVAILABLE), {bbox_bad} invalid, "
          f"{len(sample_rows) - bbox_exempt - bbox_bad} valid")

    # --- Check 4: frame index validity + monotonicity ---
    sampled_indices = [int(r["sampled_frame_index"]) for r in frame_rows]
    neg = [i for i in sampled_indices if i < 0]
    if neg:
        errors.append(f"[negative-frame-index] {len(neg)} negative sampled_frame_index values")
    is_monotonic = sampled_indices == sorted(sampled_indices)
    is_unique = len(sampled_indices) == len(set(sampled_indices))
    if not is_monotonic:
        errors.append("[frame-index-order] sampled_frame_index is not monotonically increasing in frame_level_extraction_manifest.csv")
    if not is_unique:
        errors.append("[frame-index-dup] sampled_frame_index has duplicates in frame_level_extraction_manifest.csv")
    source_indices = [int(r["source_frame_index"]) for r in frame_rows]
    neg_src = [i for i in source_indices if i < 0]
    if neg_src:
        errors.append(f"[negative-source-frame-index] {len(neg_src)} negative source_frame_index values")
    print(f"Check 4 (frame indices): monotonic={is_monotonic}, unique={is_unique}, "
          f"negative_sampled={len(neg)}, negative_source={len(neg_src)}")

    # --- Check 5: original vs CLAHE dimension correspondence (programmatic) ---
    dim_checked = 0
    dim_mismatch = 0
    for r in sample_rows:
        if r["has_clahe"] != "True":
            continue
        orig_p = ROOT / r["original_path"]
        clahe_p = ROOT / r["clahe_path"]
        if not orig_p.exists() or not clahe_p.exists():
            continue
        img_o = cv2.imread(str(orig_p))
        img_c = cv2.imread(str(clahe_p))
        if img_o is None or img_c is None:
            warnings.append(f"[dim-check-unreadable] {r['sample_id']}: could not open original or clahe image")
            continue
        dim_checked += 1
        if img_o.shape[:2] != img_c.shape[:2]:
            dim_mismatch += 1
            errors.append(
                f"[dim-mismatch] {r['sample_id']}: original {img_o.shape[:2]} != clahe {img_c.shape[:2]}"
            )
    print(f"Check 5 (original vs CLAHE dims): {dim_checked} pairs checked, {dim_mismatch} mismatches")

    # --- Check 6: orphan check both directions ---
    manifest_ids = set(r["sample_id"] for r in sample_rows)

    def ids_from_json_dict(path):
        d = load_json(path)
        return set(d.keys())

    def ids_from_json_list_of_points(path, key="image_id"):
        d = load_json(path)
        return set(r[key] for r in d)

    def ids_from_json_list_of_records(path, key="image_id"):
        d = load_json(path)
        return set(r[key] for r in d)

    landmark_source_ids = set()
    landmark_source_ids |= ids_from_json_dict(EXP005 / "insightface_68pt_pilot_predictions.json")
    landmark_source_ids |= ids_from_json_list_of_points(EXP005 / "cvat_reviewed_landmarks.json")
    landmark_source_ids |= ids_from_json_dict(EXP005 / "calibration_batch_40_predictions.json")
    landmark_source_ids |= ids_from_json_list_of_points(EXP005 / "calibration_batch_40_reviewed.json")
    landmark_source_ids |= ids_from_json_list_of_records(EXP005 / "batch3_predictions.json")

    label_source_ids = set()
    with open(EXP004 / "human_labels.csv") as f:
        for r in csv.DictReader(f):
            if r.get("gt_label", "").strip():
                label_source_ids.add(r["image_id"])

    orphans_landmark_not_in_manifest = landmark_source_ids - manifest_ids
    orphans_label_not_in_manifest = label_source_ids - manifest_ids

    # reverse direction: manifest rows claiming landmark/label status but source disagrees
    manifest_claims_reviewed_or_init = {
        r["sample_id"] for r in sample_rows if r["landmark_status"] != "not_initialized"
    }
    manifest_claims_labeled = {
        r["sample_id"] for r in sample_rows if r["expression_label_status"] != "not_labeled"
    }
    orphans_manifest_landmark_not_in_source = manifest_claims_reviewed_or_init - landmark_source_ids
    orphans_manifest_label_not_in_source = manifest_claims_labeled - label_source_ids

    for sid in orphans_landmark_not_in_manifest:
        errors.append(f"[orphan-landmark-source] {sid} appears in a landmark source file but not in per_face_sample_manifest.csv")
    for sid in orphans_label_not_in_manifest:
        errors.append(f"[orphan-label-source] {sid} appears in human_labels.csv but not in per_face_sample_manifest.csv")
    for sid in orphans_manifest_landmark_not_in_source:
        errors.append(f"[orphan-manifest-landmark] {sid} marked as landmark-initialized/reviewed in manifest but not found in any source file")
    for sid in orphans_manifest_label_not_in_source:
        errors.append(f"[orphan-manifest-label] {sid} marked as labeled in manifest but not found in human_labels.csv")

    print(f"Check 6 (orphans): landmark_source_not_in_manifest={len(orphans_landmark_not_in_manifest)}, "
          f"label_source_not_in_manifest={len(orphans_label_not_in_manifest)}, "
          f"manifest_landmark_not_in_source={len(orphans_manifest_landmark_not_in_source)}, "
          f"manifest_label_not_in_source={len(orphans_manifest_label_not_in_source)}")

    print("\n=== RESULT ===")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        print("\nFirst 20 errors:")
        for e in errors[:20]:
            print(" -", e)
    if warnings:
        print("\nFirst 10 warnings:")
        for w in warnings[:10]:
            print(" -", w)

    if errors:
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
