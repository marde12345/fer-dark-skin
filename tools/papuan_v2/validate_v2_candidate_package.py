"""Step 8: focused validator for the v2 candidate package."""
import csv
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
QC_MANIFEST = REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv"
OUT_ORIG = REPO / "delivery/papuan_v2_v2_candidate_2026-10-19/02_Images/Original"
OUT_CLAHE = REPO / "delivery/papuan_v2_v2_candidate_2026-10-19/02_Images/CLAHE"

V1_MANIFEST = REPO / "docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv"


def main():
    rows = list(csv.DictReader(open(QC_MANIFEST)))
    candidates = [r for r in rows if r["pass_all"] == "True"]
    sample_ids = [r["sample_id"] for r in candidates]

    results = {}

    # 1. all images exactly 224x224
    bad_size = []
    for sid in sample_ids:
        for d in (OUT_ORIG, OUT_CLAHE):
            p = d / f"{sid}.jpg"
            if not p.exists():
                bad_size.append((sid, "MISSING", str(p)))
                continue
            im = Image.open(p)
            if im.size != (224, 224):
                bad_size.append((sid, im.size, str(p)))
    results["all_images_224x224"] = ("PASS" if not bad_size else "FAIL", bad_size[:10])

    # 2. original/clahe dimension correspondence (both 224x224 by construction; check both exist)
    missing_pair = [sid for sid in sample_ids if not (OUT_ORIG / f"{sid}.jpg").exists() or not (OUT_CLAHE / f"{sid}.jpg").exists()]
    results["original_clahe_pair_exists"] = ("PASS" if not missing_pair else "FAIL", missing_pair[:10])

    # 3. sample_id uniqueness + no collision with v1 namespace
    dupes = len(sample_ids) != len(set(sample_ids))
    v1_ids = set(r["sample_id"] for r in csv.DictReader(open(V1_MANIFEST)))
    collisions = [s for s in sample_ids if s in v1_ids]
    all_prefixed = all(s.startswith("v2_frame_") for s in sample_ids)
    results["sample_id_unique"] = ("PASS" if not dupes else "FAIL", dupes)
    results["no_v1_collision"] = ("PASS" if not collisions else "FAIL", collisions[:10])
    results["namespace_prefix_v2"] = ("PASS" if all_prefixed else "FAIL", [s for s in sample_ids if not s.startswith("v2_frame_")][:5])

    # 4. landmark coords within [0,224]
    import json
    lm_dir = REPO / "delivery/papuan_v2_v2_candidate_2026-10-19/03_Landmarks/Initial"
    bad_lm = []
    checked = 0
    for sid in sample_ids:
        p = lm_dir / f"{sid}.json"
        if not p.exists():
            continue
        data = json.load(open(p))
        for pt in data["points_42"]:
            checked += 1
            if not (0 <= pt["x"] <= 224 and 0 <= pt["y"] <= 224):
                bad_lm.append((sid, pt))
    results["landmarks_within_bounds"] = ("PASS" if not bad_lm else "FAIL", f"checked={checked}, bad={bad_lm[:10]}")

    # 5. manifest path existence (original/clahe source paths referenced in QC manifest)
    missing_src = []
    for r in rows:
        if not (REPO / r["original_path"]).exists() or not (REPO / r["clahe_path"]).exists():
            missing_src.append(r["sample_id"])
    results["manifest_source_paths_exist"] = ("PASS" if not missing_src else "FAIL", missing_src[:10])

    # 6. counts match fresh recount
    n_standardized_orig = len(list(OUT_ORIG.glob("*.jpg")))
    n_standardized_clahe = len(list(OUT_CLAHE.glob("*.jpg")))
    results["counts_match"] = (
        "PASS" if n_standardized_orig == len(sample_ids) == n_standardized_clahe else "FAIL",
        f"candidates={len(sample_ids)} orig_files={n_standardized_orig} clahe_files={n_standardized_clahe}",
    )

    print("=== VALIDATION RESULTS ===")
    for k, (status, detail) in results.items():
        print(f"{k}: {status}  detail={detail}")


if __name__ == "__main__":
    main()
