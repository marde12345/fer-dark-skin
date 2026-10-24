"""Generate InsightFace landmark_3d_68 proposals for EXP-PAP-005 batch 3
(40 new images, experiments/EXP-PAP-005/batch3_manifest.csv).

Reuses the exact method documented in docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md:
- insightface.app.FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark_3d_68"])
- skip re-detection (crops are already-tight faces); construct a synthetic
  full-crop bbox Face(bbox=[0,0,w,h]) and call the landmark_3d_68 model's
  .get(img, face) directly.
- only x, y of the (68,3) output are kept (z discarded, matches prior convention).

Output: experiments/EXP-PAP-005/batch3_predictions.json, same schema as
insightface_68pt_pilot_predictions.json / calibration_batch_40_predictions.json.
"""
import csv
import json
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.app.common import Face

REPO = "/Users/MAC/Projects/FER-Dataset"
FACES_DIR = f"{REPO}/data/papuan_v2/faces"
MANIFEST = f"{REPO}/experiments/EXP-PAP-005/batch3_manifest.csv"
OUT = f"{REPO}/experiments/EXP-PAP-005/batch3_predictions.json"

app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark_3d_68"])
app.prepare(ctx_id=-1, det_size=(640, 640))
lmk_model = app.models["landmark_3d_68"]

rows = list(csv.DictReader(open(MANIFEST)))
results = []
failures = []

for row in rows:
    image_id = row["image_id"]
    path = f"{FACES_DIR}/{image_id}.jpg"
    img = cv2.imread(path)
    if img is None:
        failures.append((image_id, "cv2.imread failed"))
        continue
    h, w = img.shape[:2]
    face = Face(bbox=np.array([0, 0, w, h], dtype=np.float32), kps=None, det_score=1.0)
    lmk_model.get(img, face)
    lmk = face.landmark_3d_68  # (68, 3)
    results.append({
        "image_id": image_id,
        "crop_width": w,
        "crop_height": h,
        "landmark_schema": "insightface_landmark_3d_68",
        "landmarks_xy": lmk[:, :2].tolist(),
    })

print(f"succeeded: {len(results)}/{len(rows)}")
if failures:
    print("failures:", failures)

json.dump(results, open(OUT, "w"), indent=2)
print("wrote", OUT)
