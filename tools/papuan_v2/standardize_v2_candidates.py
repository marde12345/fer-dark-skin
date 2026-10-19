"""Step 7: standardize v2 candidate set (pass_all == True rows from the
QC manifest) to 224x224 letterboxed Original + CLAHE, transform landmarks,
derive the 42-point subset. Output to
delivery/papuan_v2_v2_candidate_2026-10-19/ using the v1 folder convention
(02_Images/{Original,CLAHE}, 03_Landmarks/{Initial,Reviewed}, 04_Manifests).
Reuses the exact letterbox approach from tools/papuan_v2/standardize_images.py.
"""
import csv
import json
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
QC_MANIFEST = REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv"
OUT_ROOT = REPO / "delivery/papuan_v2_v2_candidate_2026-10-19"
OUT_ORIG = OUT_ROOT / "02_Images/Original"
OUT_CLAHE = OUT_ROOT / "02_Images/CLAHE"
OUT_LM_INITIAL = OUT_ROOT / "03_Landmarks/Initial"
OUT_LM_REVIEWED = OUT_ROOT / "03_Landmarks/Reviewed"
OUT_MANIFESTS = OUT_ROOT / "04_Manifests"
TARGET = 224
TARGET_INDICES = list(range(17, 27)) + list(range(36, 48)) + list(range(48, 68))
assert len(TARGET_INDICES) == 42


def letterbox(img: Image.Image):
    w, h = img.size
    scale = TARGET / max(w, h)
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    resized = img.resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new("RGB", (TARGET, TARGET), (0, 0, 0))
    pad_left = (TARGET - new_w) // 2
    pad_top = (TARGET - new_h) // 2
    canvas.paste(resized, (pad_left, pad_top))
    return canvas, scale, pad_left, pad_top


def main():
    for d in [OUT_ORIG, OUT_CLAHE, OUT_LM_INITIAL, OUT_LM_REVIEWED, OUT_MANIFESTS]:
        d.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(open(QC_MANIFEST)))
    candidates = [r for r in rows if r["pass_all"] == "True"]
    print(f"candidates to standardize: {len(candidates)} / {len(rows)} total faces")

    transforms = []
    failures = []

    for row in candidates:
        sid = row["sample_id"]
        try:
            orig = Image.open(REPO / row["original_path"]).convert("RGB")
            clahe = Image.open(REPO / row["clahe_path"]).convert("RGB")
            assert orig.size == clahe.size

            out_orig, scale, pad_l, pad_t = letterbox(orig)
            w, h = clahe.size
            new_w, new_h = max(1, round(w * scale)), max(1, round(h * scale))
            resized_clahe = clahe.resize((new_w, new_h), Image.BILINEAR)
            canvas_clahe = Image.new("RGB", (TARGET, TARGET), (0, 0, 0))
            canvas_clahe.paste(resized_clahe, (pad_l, pad_t))

            out_orig.save(OUT_ORIG / f"{sid}.jpg", quality=95)
            canvas_clahe.save(OUT_CLAHE / f"{sid}.jpg", quality=95)

            lm_path = row["landmark_raw_path"]
            if lm_path and lm_path != "NOT_AVAILABLE":
                data = json.load(open(REPO / lm_path))
                lm68 = data["landmark_3d_68"]
                crop_px1, crop_py1 = data["crop_px1"], data["crop_py1"]
                subset = []
                for idx in TARGET_INDICES:
                    x, y, _z = lm68[idx]
                    xl = (x - crop_px1) * scale + pad_l
                    yl = (y - crop_py1) * scale + pad_t
                    subset.append({"landmark_index": idx, "x": round(xl, 2), "y": round(yl, 2)})
                with open(OUT_LM_INITIAL / f"{sid}.json", "w") as f:
                    json.dump({"sample_id": sid, "landmark_status": "ai_initialized_unreviewed",
                               "points_42": subset}, f)
            # No Reviewed landmarks exist for this brand-new pool (as expected per task spec).

            transforms.append({
                "sample_id": sid, "source_width": orig.size[0], "source_height": orig.size[1],
                "scale_factor": scale, "pad_left": pad_l, "pad_top": pad_t,
            })
        except Exception as e:
            failures.append((sid, str(e)))

    with open(OUT_MANIFESTS / "_standardization_transform_v2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "source_width", "source_height", "scale_factor", "pad_left", "pad_top"])
        w.writeheader()
        w.writerows(transforms)

    print(f"standardized: {len(transforms)}, failures: {len(failures)}")
    if failures:
        print(failures[:10])


if __name__ == "__main__":
    main()
