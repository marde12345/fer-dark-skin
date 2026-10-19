"""Step 2 landmark handling for the final delivery package.

For the 231 frozen-candidate samples:
- Reuse existing initial 68-point InsightFace predictions where available
  (joined via landmark_initial_path in the frozen manifest).
- For samples missing initial landmarks, generate them with InsightFace's
  landmark_3d_68 sub-model (buffalo_l bundle) on the ORIGINAL (non-standardized)
  crop, using the exact pattern from experiments/EXP-PAP-005/gen_batch3_predictions.py.
- Derive the 42-point subset (indices 17-26, 36-47, 48-67) from every 68-point set.
- Apply the Step-1 letterbox transform (new_x = x*scale + pad_left, new_y = y*scale + pad_top).
- Write delivery/papuan_v2_final_2026-10-19/03_Landmarks/Initial/{sample_id}.json
- For the subset with human-reviewed landmarks, write the reviewed 42-point
  subset (same transform) to .../03_Landmarks/Reviewed/{sample_id}.json
"""
import csv
import json
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "docs/reports/frozen_candidate_v1_2026-10-19/frozen_candidate_manifest.csv"
TRANSFORM_CSV = REPO / "delivery/papuan_v2_final_2026-10-19/04_Manifests/_standardization_transform.csv"
FACES_DIR = REPO / "data/papuan_v2/faces"
OUT_INITIAL = REPO / "delivery/papuan_v2_final_2026-10-19/03_Landmarks/Initial"
OUT_REVIEWED = REPO / "delivery/papuan_v2_final_2026-10-19/03_Landmarks/Reviewed"

TARGET_INDICES = list(range(17, 27)) + list(range(36, 48)) + list(range(48, 68))
assert len(TARGET_INDICES) == 42

EXP5 = REPO / "experiments/EXP-PAP-005"
INITIAL_FILES = {
    "experiments/EXP-PAP-005/insightface_68pt_pilot_predictions.json": "dict_of_arrays",
    "experiments/EXP-PAP-005/batch3_predictions.json": "list_of_arrays",
    "experiments/EXP-PAP-005/calibration_batch_40_predictions.json": "dict_of_arrays",
}
REVIEWED_FILES = {
    "experiments/EXP-PAP-005/cvat_reviewed_landmarks.json": "point_rows",
    "experiments/EXP-PAP-005/calibration_batch_40_reviewed.json": "point_rows",
}


def load_initial_source(rel_path):
    """Returns dict: image_id -> list of 68 [x,y] points."""
    kind = INITIAL_FILES[rel_path]
    data = json.load(open(REPO / rel_path))
    out = {}
    if kind == "dict_of_arrays":
        for k, v in data.items():
            out[v["image_id"]] = v["landmarks_xy"]
    elif kind == "list_of_arrays":
        for v in data:
            out[v["image_id"]] = v["landmarks_xy"]
    return out


def load_reviewed_source(rel_path):
    """Returns dict: image_id -> {landmark_index: [x,y]}."""
    data = json.load(open(REPO / rel_path))
    out = {}
    for row in data:
        iid = row["image_id"]
        out.setdefault(iid, {})[row["landmark_index"]] = [row["x"], row["y"]]
    return out


def main():
    rows = list(csv.DictReader(open(FROZEN)))
    assert len(rows) == 231

    transforms = {t["sample_id"]: t for t in csv.DictReader(open(TRANSFORM_CSV))}
    assert len(transforms) == 231

    # Preload all initial/reviewed source files
    initial_sources = {p: load_initial_source(p) for p in INITIAL_FILES}
    reviewed_sources = {p: load_reviewed_source(p) for p in REVIEWED_FILES}

    reused = 0
    generated = 0
    has_reviewed = 0
    gen_failures = []

    # Lazy-load InsightFace only if needed
    app = None
    lmk_model = None

    for row in rows:
        sid = row["sample_id"]
        t = transforms[sid]
        scale = float(t["scale_factor"])
        pad_l = float(t["pad_left"])
        pad_t = float(t["pad_top"])

        lp = row["landmark_initial_path"]
        pts68 = None
        source_tag = None

        if lp != "NOT_AVAILABLE" and lp in initial_sources:
            d = initial_sources[lp]
            if sid in d:
                pts68 = d[sid]
                source_tag = "existing_prediction_reused"
                reused += 1

        if pts68 is None:
            # Generate via InsightFace landmark_3d_68 on the ORIGINAL (non-standardized) crop
            if app is None:
                from insightface.app import FaceAnalysis
                from insightface.app.common import Face
                app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark_3d_68"])
                app.prepare(ctx_id=-1, det_size=(640, 640))
                lmk_model = app.models["landmark_3d_68"]
                FaceCls = Face
            img = cv2.imread(str(FACES_DIR / f"{sid}.jpg"))
            if img is None:
                gen_failures.append(sid)
                continue
            h, w = img.shape[:2]
            face = FaceCls(bbox=np.array([0, 0, w, h], dtype=np.float32), kps=None, det_score=1.0)
            lmk_model.get(img, face)
            lmk = face.landmark_3d_68
            pts68 = lmk[:, :2].tolist()
            source_tag = "insightface_landmark_3d_68"
            generated += 1

        # Build 42-point initial subset in standardized coordinate space
        points = []
        for idx in TARGET_INDICES:
            x, y = pts68[idx]
            nx = x * scale + pad_l
            ny = y * scale + pad_t
            points.append({"source_index": idx, "x": nx, "y": ny})

        out_obj = {
            "sample_id": sid,
            "coordinate_space": "standardized_224x224",
            "points": points,
            "source": source_tag,
        }
        json.dump(out_obj, open(OUT_INITIAL / f"{sid}.json", "w"), indent=2)

        # Reviewed subset, if applicable
        rp = row["landmark_reviewed_path"]
        if rp != "NOT_AVAILABLE" and rp in reviewed_sources:
            rd = reviewed_sources[rp]
            if sid in rd:
                pt_map = rd[sid]
                rpoints = []
                ok = True
                for idx in TARGET_INDICES:
                    if idx not in pt_map:
                        ok = False
                        break
                    x, y = pt_map[idx]
                    nx = x * scale + pad_l
                    ny = y * scale + pad_t
                    rpoints.append({"source_index": idx, "x": nx, "y": ny})
                if ok:
                    rout = {
                        "sample_id": sid,
                        "coordinate_space": "standardized_224x224",
                        "points": rpoints,
                        "source": "cvat_human_reviewed",
                    }
                    json.dump(rout, open(OUT_REVIEWED / f"{sid}.json", "w"), indent=2)
                    has_reviewed += 1

    print(f"reused initial: {reused}")
    print(f"generated initial: {generated}")
    print(f"generation failures: {len(gen_failures)} {gen_failures}")
    print(f"has reviewed: {has_reviewed}")
    print(f"total initial written: {reused + generated}")


if __name__ == "__main__":
    main()
