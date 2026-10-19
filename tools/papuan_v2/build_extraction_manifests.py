"""
Build frame_level_extraction_manifest.csv and per_face_sample_manifest.csv
from EXISTING papuan_v2 artifacts only. Does not call InsightFace, does not
re-extract frames, does not re-run face detection. Reads real files on disk
and computes real pixel-derived QC metrics (dimensions, Laplacian blur
variance) by opening each image.

Usage: uv run python tools/papuan_v2/build_extraction_manifests.py
"""
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs/reports/extraction_audit_2026-10-19"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_MANIFEST = ROOT / "data/papuan_v2/raw/source_video_manifest.json"
FACES_DIR = ROOT / "data/papuan_v2/faces"
CLAHE_DIR = ROOT / "data/papuan_v2/clahe"
VIDEO_PATH = ROOT / "data/raw/videos/pesta_babi.mp4"

EXP004 = ROOT / "experiments/EXP-PAP-004"
EXP005 = ROOT / "experiments/EXP-PAP-005"

FRAME_RE = re.compile(r"^frame_(\d{6})_face(\d{2})$")


def load_json(p):
    with open(p) as f:
        return json.load(f)


def main():
    manifest = load_json(RAW_MANIFEST)
    source_video = manifest["source_video"]
    sampling = manifest["sampling_config"]
    outputs = manifest["outputs"]

    source_video_id = Path(source_video["path"]).stem
    source_video_path = source_video["path"]
    source_video_sha256 = source_video["sha256"]
    source_fps = source_video["original_fps"]
    source_frame_count = source_video["total_frames_in_source"]
    source_duration_seconds = source_frame_count / source_fps

    # Real video width/height read directly from the (copied, unmodified) source file.
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if cap.isOpened():
        video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cv2_fps = cap.get(cv2.CAP_PROP_FPS)
        cv2_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        video_meta_source = "verified_from_file (cv2.VideoCapture on data/raw/videos/pesta_babi.mp4)"
        assert abs(cv2_fps - source_fps) < 0.01, f"fps mismatch: cv2={cv2_fps} manifest={source_fps}"
        assert cv2_count == source_frame_count, f"frame count mismatch: cv2={cv2_count} manifest={source_frame_count}"
    else:
        video_w = video_h = "NOT_AVAILABLE"
        video_meta_source = "not_available (could not open source video file)"

    sampling_fps = sampling["target_fps"]
    frame_interval = sampling["frame_interval"]
    frames_sampled = outputs["frames_sampled"]  # 250
    extraction_run_id = manifest.get("generated_at", "NOT_AVAILABLE")
    detector_model = "insightface buffalo_l (SCRFD detector, via insightface.app.FaceAnalysis)"
    detector_version = "insightface==1.0.1 (resolved pin, uv.lock); pyproject.toml specifier insightface>=1.0.1"
    software_versions_note = (
        "det_size=(640,640) (src/fer_dataset/pipeline/face_detector.py:18,30); "
        "providers=['CPUExecutionProvider']; buffalo_l bundle includes SCRFD detector "
        "+ 1k3d68.onnx landmark sub-model (landmark prediction only, not used for bbox)."
    )

    # ---- Inventory face crops: map sampled_frame_index -> list of face indices ----
    face_files = sorted(FACES_DIR.glob("*.jpg"))
    frame_to_faces = defaultdict(list)
    sample_ids = []
    for fp in face_files:
        m = FRAME_RE.match(fp.stem)
        if not m:
            continue
        sampled_idx = int(m.group(1))
        face_idx = int(m.group(2))
        frame_to_faces[sampled_idx].append(face_idx)
        sample_ids.append(fp.stem)

    print(f"Face crop files found: {len(face_files)}")
    print(f"Distinct sampled-frame indices with >=1 face: {len(frame_to_faces)}")

    # ---- Step 3: frame_level_extraction_manifest.csv ----
    # All sampled frames are indices 0..frames_sampled-1 (saved_index increments
    # sequentially on every save, per frame_extractor.py:70-98). Frames with zero
    # detected faces still exist as a sampled frame (just no crop files), so we
    # emit all frames_sampled rows, not only the ones with a face.
    frame_rows = []
    for sampled_idx in range(frames_sampled):
        source_frame_index = sampled_idx * frame_interval  # exact per frame_extractor.py:63-92 logic
        requested_ts = source_frame_index / source_fps
        actual_ts = requested_ts  # no PTS-based decode in code; sequential cap.read() only
        detected_count = len(frame_to_faces.get(sampled_idx, []))
        row = {
            "source_video_id": source_video_id,
            "source_video_path": source_video_path,
            "source_video_sha256": source_video_sha256,
            "source_fps": source_fps,
            "source_frame_count": source_frame_count,
            "source_duration_seconds": round(source_duration_seconds, 4),
            "source_width": video_w,
            "source_height": video_h,
            "sampling_method": "fixed-interval frame-index stepping (frame_index % frame_interval == 0), NOT fixed-FPS re-timestamping",
            "sampling_fps": sampling_fps,
            "sampled_frame_index": sampled_idx,
            "source_frame_index": source_frame_index,
            "requested_timestamp_seconds": round(requested_ts, 4),
            "actual_timestamp_seconds": round(actual_ts, 4),
            "frame_width": "NOT_AVAILABLE",  # original full frames were not retained on disk
            "frame_height": "NOT_AVAILABLE",
            "detected_faces_count": detected_count,
            "extraction_run_id": extraction_run_id,
            "detector_model": detector_model,
            "detector_version": detector_version,
            "software_versions_note": software_versions_note,
            "metadata_source": (
                "derived: source_frame_index/timestamp computed from frame_interval formula "
                "(frame_extractor.py:63-66,82-92), verified exact given sequential cap.read() "
                "semantics; source_* fields verified_from_file (source_video_manifest.json + "
                "cv2.VideoCapture read of actual video file); detected_faces_count derived from "
                "counting face-crop filenames sharing this sampled_frame_index; frame_width/height "
                "not_available because extracted frame .jpg files were not retained on disk "
                "(only face crops + CLAHE crops persisted)."
            ),
        }
        frame_rows.append(row)

    frame_csv_path = OUT_DIR / "frame_level_extraction_manifest.csv"
    with open(frame_csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(frame_rows[0].keys()))
        w.writeheader()
        w.writerows(frame_rows)
    print(f"Wrote {len(frame_rows)} rows -> {frame_csv_path}")

    # ---- Load label/landmark artifacts for joins ----
    def load_human_labels():
        p = EXP004 / "human_labels.csv"
        out = {}
        if p.exists():
            with open(p) as f:
                for r in csv.DictReader(f):
                    if r.get("gt_label", "").strip():
                        out[r["image_id"]] = {
                            "label": r["gt_label"],
                            "annotator": r.get("labeled_by", ""),
                        }
        return out

    human_labels = load_human_labels()

    def collect_landmark_status():
        """Return dict sample_id -> (initial_path, reviewed_path, status)."""
        status = {}

        # pilot (24): initial predictions
        pilot_init = load_json(EXP005 / "insightface_68pt_pilot_predictions.json")
        for sid in pilot_init:
            status.setdefault(sid, {})["initial"] = str(
                (EXP005 / "insightface_68pt_pilot_predictions.json").relative_to(ROOT)
            )

        # pilot (24): reviewed (flat list of points, group by image_id)
        pilot_reviewed = load_json(EXP005 / "cvat_reviewed_landmarks.json")
        reviewed_pilot_ids = set(r["image_id"] for r in pilot_reviewed)
        for sid in reviewed_pilot_ids:
            status.setdefault(sid, {})["reviewed"] = str(
                (EXP005 / "cvat_reviewed_landmarks.json").relative_to(ROOT)
            )

        # calibration batch 40: initial predictions (dict keyed by image_id)
        calib_init = load_json(EXP005 / "calibration_batch_40_predictions.json")
        for sid in calib_init:
            status.setdefault(sid, {})["initial"] = str(
                (EXP005 / "calibration_batch_40_predictions.json").relative_to(ROOT)
            )

        # calibration batch 40: reviewed (flat list of points)
        calib_reviewed = load_json(EXP005 / "calibration_batch_40_reviewed.json")
        reviewed_calib_ids = set(r["image_id"] for r in calib_reviewed)
        for sid in reviewed_calib_ids:
            status.setdefault(sid, {})["reviewed"] = str(
                (EXP005 / "calibration_batch_40_reviewed.json").relative_to(ROOT)
            )

        # batch 3 (40): initial predictions only, unreviewed (list of records)
        batch3 = load_json(EXP005 / "batch3_predictions.json")
        for rec in batch3:
            sid = rec["image_id"]
            status.setdefault(sid, {})["initial"] = str(
                (EXP005 / "batch3_predictions.json").relative_to(ROOT)
            )

        return status

    landmark_status = collect_landmark_status()
    initialized_count = sum(1 for v in landmark_status.values() if "initial" in v)
    reviewed_count = sum(1 for v in landmark_status.values() if "reviewed" in v)
    print(f"Landmark status: {initialized_count} initialized, {reviewed_count} reviewed")

    # ---- Step 4: per_face_sample_manifest.csv ----
    sample_rows = []
    qc_values = []  # (sample_id, width, height, blur_var)

    for fp in sorted(FACES_DIR.glob("*.jpg")):
        sample_id = fp.stem
        m = FRAME_RE.match(sample_id)
        if not m:
            continue
        sampled_idx = int(m.group(1))
        face_idx_in_frame = int(m.group(2))
        source_frame_index = sampled_idx * frame_interval
        frame_ts = round(source_frame_index / source_fps, 4)

        original_path_abs = fp
        original_path_rel = str(fp.relative_to(ROOT))
        clahe_fp = CLAHE_DIR / fp.name
        has_clahe = os.path.exists(clahe_fp)
        clahe_path_rel = str(clahe_fp.relative_to(ROOT)) if has_clahe else "NOT_AVAILABLE"

        # QC: open the real image, compute real width/height/blur
        img = cv2.imread(str(original_path_abs))
        if img is None:
            qc_w = qc_h = "NOT_AVAILABLE"
            blur_var = "NOT_AVAILABLE"
        else:
            qc_h, qc_w = img.shape[0], img.shape[1]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            qc_values.append((sample_id, qc_w, qc_h, blur_var))

        lstat = landmark_status.get(sample_id, {})
        landmark_initial_path = lstat.get("initial", "NOT_AVAILABLE")
        landmark_reviewed_path = lstat.get("reviewed", "NOT_AVAILABLE")
        if "reviewed" in lstat:
            landmark_status_str = "reviewed"
        elif "initial" in lstat:
            landmark_status_str = "ai_initialized_unreviewed"
        else:
            landmark_status_str = "not_initialized"

        hl = human_labels.get(sample_id)
        if hl:
            expr_label = hl["label"]
            expr_annotator = hl["annotator"]
            expr_status = "labeled_single_annotator"
        else:
            expr_label = "NOT_AVAILABLE"
            expr_annotator = "NOT_AVAILABLE"
            expr_status = "not_labeled"

        row = {
            "sample_id": sample_id,
            "source_video_id": source_video_id,
            "sampled_frame_index": sampled_idx,
            "source_frame_index": source_frame_index,
            "frame_timestamp_seconds": frame_ts,
            "face_index_in_frame": face_idx_in_frame,
            "person_id": "NOT_AVAILABLE",
            "bbox_x": "NOT_AVAILABLE",
            "bbox_y": "NOT_AVAILABLE",
            "bbox_w": "NOT_AVAILABLE",
            "bbox_h": "NOT_AVAILABLE",
            "crop_width": qc_w,
            "crop_height": qc_h,
            "original_path": original_path_rel,
            "clahe_path": clahe_path_rel,
            "has_clahe": has_clahe,
            "landmark_initial_path": landmark_initial_path,
            "landmark_reviewed_path": landmark_reviewed_path,
            "landmark_status": landmark_status_str,
            "expression_label": expr_label,
            "expression_label_annotator": expr_annotator,
            "expression_label_status": expr_status,
            "qc_blur_variance": round(blur_var, 4) if isinstance(blur_var, float) else blur_var,
            "qc_width": qc_w,
            "qc_height": qc_h,
            "qc_status": "PENDING_THRESHOLD",
            "qc_exclusion_reason": "NOT_AVAILABLE (no validated threshold exists yet)",
            "annotation_review_status": landmark_status_str,
            "metadata_source": (
                "derived: sampled_frame_index/face_index_in_frame parsed from filename "
                "(face_detector.py:85 'frame_{stem}_face{idx+1:02d}.jpg'); source_frame_index/"
                "frame_timestamp_seconds computed via frame_interval formula; crop_width/height/"
                "qc_blur_variance verified_from_file (real cv2.imread + cv2.Laplacian computation "
                "on this exact file); bbox_* not_available (face_detector.py never persists "
                "face.bbox to disk, only the already-cropped+padded jpg is written, see "
                "face_detector.py:62-90); person_id not_available (no identity tracking exists "
                "anywhere in the codebase); landmark/expression fields derived from real joins "
                "against experiments/EXP-PAP-005 landmark JSON files and "
                "experiments/EXP-PAP-004/human_labels.csv by sample_id/image_id."
            ),
        }
        sample_rows.append(row)

    sample_csv_path = OUT_DIR / "per_face_sample_manifest.csv"
    with open(sample_csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sample_rows[0].keys()))
        w.writeheader()
        w.writerows(sample_rows)
    print(f"Wrote {len(sample_rows)} rows -> {sample_csv_path}")

    # ---- QC threshold candidates report ----
    import statistics as st

    blur_vals = sorted(v[3] for v in qc_values)
    w_vals = sorted(v[1] for v in qc_values)
    h_vals = sorted(v[2] for v in qc_values)
    min_dim_vals = sorted(min(v[1], v[2]) for v in qc_values)

    def pct(vals, p):
        if not vals:
            return None
        k = (len(vals) - 1) * p / 100
        f = int(k)
        c = min(f + 1, len(vals) - 1)
        if f == c:
            return vals[f]
        return vals[f] + (vals[c] - vals[f]) * (k - f)

    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

    lines = []
    lines.append("# QC Threshold Candidates (papuan_v2, 2026-10-19)\n")
    lines.append(
        "Descriptive distribution only. No threshold has been supervisor-validated; "
        "`qc_status` in `per_face_sample_manifest.csv` is left as `PENDING_THRESHOLD` "
        "for all rows. This file exists to let a human pick a threshold later.\n"
    )
    lines.append(f"Total crops analyzed: {len(qc_values)} / 645\n")

    lines.append("\n## Blur variance (cv2.Laplacian(gray, CV_64F).var()) percentiles\n")
    lines.append("| Percentile | Value |\n|---|---|")
    for p in percentiles:
        lines.append(f"| p{p} | {pct(blur_vals, p):.2f} |")

    lines.append("\n## Width (px) percentiles\n")
    lines.append("| Percentile | Value |\n|---|---|")
    for p in percentiles:
        lines.append(f"| p{p} | {pct(w_vals, p):.1f} |")

    lines.append("\n## Height (px) percentiles\n")
    lines.append("| Percentile | Value |\n|---|---|")
    for p in percentiles:
        lines.append(f"| p{p} | {pct(h_vals, p):.1f} |")

    lines.append("\n## min(width,height) (px) percentiles\n")
    lines.append("| Percentile | Value |\n|---|---|")
    for p in percentiles:
        lines.append(f"| p{p} | {pct(min_dim_vals, p):.1f} |")

    lines.append(
        "\n## Illustrative candidate thresholds (NOT a decision — for discussion only)\n"
    )
    lines.append("| Candidate rule | Samples passing | % of 645 |\n|---|---|---|")
    candidates = [
        ("blur_variance > p10 AND min(w,h) >= 32px", lambda b, w, h: b > pct(blur_vals, 10) and min(w, h) >= 32),
        ("blur_variance > p25 AND min(w,h) >= 48px", lambda b, w, h: b > pct(blur_vals, 25) and min(w, h) >= 48),
        ("blur_variance > p50 AND min(w,h) >= 64px", lambda b, w, h: b > pct(blur_vals, 50) and min(w, h) >= 64),
        ("blur_variance > p25 only (no size floor)", lambda b, w, h: b > pct(blur_vals, 25)),
        ("min(w,h) >= 48px only (no blur floor)", lambda b, w, h: min(w, h) >= 48),
    ]
    for name, fn in candidates:
        n = sum(1 for sid, w, h, b in qc_values if fn(b, w, h))
        lines.append(f"| {name} | {n} | {n/len(qc_values)*100:.1f}% |")

    qc_md_path = OUT_DIR / "qc_threshold_candidates.md"
    with open(qc_md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote QC distribution report -> {qc_md_path}")

    print("\n--- Summary ---")
    print(f"Frame rows: {len(frame_rows)}")
    print(f"Sample rows: {len(sample_rows)}")
    print(f"Expression-labeled samples: {len(human_labels)}")
    print(f"Landmark initialized: {initialized_count}, reviewed: {reviewed_count}")


if __name__ == "__main__":
    main()
