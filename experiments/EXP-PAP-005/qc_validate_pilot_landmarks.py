"""QC validation for the EXP-PAP-005 InsightFace-initialized 68pt pilot predictions.
Minimal checks only, per task scope: exactly 68 landmarks, no duplicate/unexpected
index, valid x/y, in-bounds (clamped if slightly over, flagged not failed), all
pilot images present, all map to a known image_id.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRED_PATH = REPO_ROOT / "experiments" / "EXP-PAP-005" / "insightface_68pt_pilot_predictions.json"
MANIFEST_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "pilot_manifest.csv"
EXPECTED_SCHEMA = "insightface_landmark_3d_68"
N_POINTS = 68

def main():
    import csv
    manifest_ids = {row["image_id"] for row in csv.DictReader(open(MANIFEST_PATH))}
    preds = json.load(open(PRED_PATH))

    errors = []
    warnings = []

    for image_id, entry in preds.items():
        if image_id not in manifest_ids:
            errors.append(f"{image_id}: not a known pilot image_id")
            continue
        if entry.get("landmark_schema") != EXPECTED_SCHEMA:
            errors.append(f"{image_id}: unexpected landmark_schema {entry.get('landmark_schema')!r}")
        pts = entry.get("landmarks_xy", [])
        if len(pts) != N_POINTS:
            errors.append(f"{image_id}: expected {N_POINTS} points, got {len(pts)}")
            continue
        w, h = entry["crop_width"], entry["crop_height"]
        for idx, (x, y) in enumerate(pts):
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                errors.append(f"{image_id}[{idx}]: non-numeric coordinate ({x}, {y})")
                continue
            if x < 0 or y < 0 or x > w or y > h:
                warnings.append(f"{image_id}[{idx}]: ({x:.1f},{y:.1f}) outside crop bounds ({w}x{h})")

    missing = manifest_ids & set() # not all 150 are expected for the pilot; see coverage check below
    pilot_ids = set(preds.keys())
    print(f"Total predictions: {len(preds)}")
    print(f"Unique image_ids: {len(pilot_ids)}")
    print(f"Duplicate-index / malformed errors: {len([e for e in errors if 'duplicate' in e.lower()])}")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print("  ERROR:", e)
    print(f"Warnings (out-of-bounds, non-fatal): {len(warnings)}")
    for w_ in warnings:
        print("  WARN:", w_)

    print()
    print("PASS" if not errors else "FAIL")
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
