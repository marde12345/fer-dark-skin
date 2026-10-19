"""New extraction+detection pass for PAPUAN V2 ("v2 pool"), 2026-10-19.

Addresses the exact gap flagged in
docs/reports/extraction_audit_2026-10-19/EXTRACTION_METHODOLOGY_REPORT.md:
the v1 pipeline (src/fer_dataset/pipeline/face_detector.py) computes
face.bbox in memory but never persists it. This script reuses the same
FrameExtractor/FaceDetector classes conceptually (same cv2.VideoCapture
stepping formula, same insightface buffalo_l FaceAnalysis call with
det_size=(640,640)) but is a NEW, standalone script (does not edit the
existing shared pipeline classes) that additionally persists, for every
detected face:
  - bbox_x/y/w/h in ORIGINAL (pre-padding, pre-crop) frame pixel coords
  - face.det_score (confirmed attribute on insightface Face objects)
  - landmark_3d_68 (for frontality/visibility derivation in a later step)
  - crop dimensions, extraction_run_id, sampling config

Does NOT touch data/papuan_v2/, frozen_candidate_v1_2026-10-19/, or
delivery/papuan_v2_final_2026-10-19/. Writes new, namespaced outputs only.

Run modes:
  --test N      : decode+detect only the first N sampled frames (timing test,
                   no file writes), report throughput and extrapolation.
  --full        : run the full (or bounded, see --max-seconds) pass and
                   persist faces/clahe crops + manifests.
  --max-seconds S : stop sampling once actual_timestamp_seconds exceeds S
                   (bounded-range mode). Documented explicitly in manifest
                   sampling_method field and must be reported prominently.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from fer_dataset.shared.clahe import apply_strategy_b_clahe  # noqa: E402
import insightface  # noqa: E402

VIDEO_PATH = REPO / "data/raw/videos/pesta_babi.mp4"
VIDEO_SHA256 = "de2ea92ac3da6c8572eef47f7b610a771f1e68f469acbe81571731faca156f0f"
TARGET_FPS = 5.0  # chosen in Step 0, see CANDIDATE_SELECTION_REPORT_V2.md
PADDING = 0.2  # same 20% padding convention as v1 face_detector.py:64

FACES_DIR = REPO / "data/papuan_v2_ext_2026-10-19/faces"
CLAHE_DIR = REPO / "data/papuan_v2_ext_2026-10-19/clahe"
REPORT_DIR = REPO / "docs/reports/extraction_v2_2026-10-19"
LANDMARKS_DIR = REPORT_DIR / "landmarks_raw"
FRAME_MANIFEST = REPORT_DIR / "frame_level_extraction_manifest_v2.csv"
FACE_MANIFEST = REPORT_DIR / "per_face_sample_manifest_v2.csv"

EXTRACTION_RUN_ID = datetime.now(timezone.utc).isoformat()

FRAME_FIELDS = [
    "source_video_id", "source_video_path", "source_video_sha256", "source_fps",
    "source_frame_count", "source_duration_seconds", "source_width", "source_height",
    "sampling_method", "sampling_fps", "sampled_frame_index", "source_frame_index",
    "requested_timestamp_seconds", "actual_timestamp_seconds", "frame_width", "frame_height",
    "detected_faces_count", "extraction_run_id", "detector_model", "detector_version",
    "software_versions_note", "bounded_range_note",
]

FACE_FIELDS = [
    "sample_id", "source_video_id", "sampled_frame_index", "source_frame_index",
    "frame_timestamp_seconds", "face_index_in_frame", "person_id",
    "bbox_x", "bbox_y", "bbox_w", "bbox_h", "det_score",
    "crop_width", "crop_height", "original_path", "clahe_path", "has_clahe",
    "landmark_raw_path", "extraction_run_id", "metadata_source",
]


def get_app():
    app = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def open_video():
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise FileNotFoundError(f"cannot open {VIDEO_PATH}")
    return cap


def run(test_n: int | None, max_seconds: float | None, full: bool):
    cap = open_video()
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / original_fps
    frame_interval = max(int(original_fps / TARGET_FPS), 1)

    print(f"original_fps={original_fps} total_frames={total_frames} duration={duration:.2f}s "
          f"frame_interval={frame_interval} target_fps={TARGET_FPS}")

    app = get_app()

    FACES_DIR.mkdir(parents=True, exist_ok=True)
    CLAHE_DIR.mkdir(parents=True, exist_ok=True)
    LANDMARKS_DIR.mkdir(parents=True, exist_ok=True)

    bounded_note = "NOT_BOUNDED (full video processed)"
    if max_seconds is not None:
        bounded_note = f"BOUNDED RANGE: only first {max_seconds:.1f}s of {duration:.2f}s video processed (explicit, documented truncation)"

    frame_rows = []
    face_rows = []

    frame_index = 0
    sampled_index = 0
    t0 = time.time()
    n_faces_total = 0

    frame_f = None
    face_f = None
    frame_w = None
    face_w = None
    if full:
        frame_f = open(FRAME_MANIFEST, "w", newline="")
        face_f = open(FACE_MANIFEST, "w", newline="")
        frame_w = csv.DictWriter(frame_f, fieldnames=FRAME_FIELDS)
        face_w = csv.DictWriter(face_f, fieldnames=FACE_FIELDS)
        frame_w.writeheader()
        face_w.writeheader()

    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_index % frame_interval == 0:
            actual_ts = frame_index / original_fps

            if max_seconds is not None and actual_ts > max_seconds:
                break

            faces = app.get(frame)
            n_faces_total += len(faces)

            frame_row = {
                "source_video_id": "pesta_babi",
                "source_video_path": "data/raw/videos/pesta_babi.mp4",
                "source_video_sha256": VIDEO_SHA256,
                "source_fps": original_fps,
                "source_frame_count": total_frames,
                "source_duration_seconds": round(duration, 2),
                "source_width": width,
                "source_height": height,
                "sampling_method": "fixed-interval frame-index stepping (frame_index % frame_interval == 0), NEW v2 run, denser than v1's 2fps",
                "sampling_fps": TARGET_FPS,
                "sampled_frame_index": sampled_index,
                "source_frame_index": frame_index,
                "requested_timestamp_seconds": round(sampled_index / TARGET_FPS, 3),
                "actual_timestamp_seconds": round(actual_ts, 3),
                "frame_width": width,
                "frame_height": height,
                "detected_faces_count": len(faces),
                "extraction_run_id": EXTRACTION_RUN_ID,
                "detector_model": "insightface buffalo_l (SCRFD detector, via insightface.app.FaceAnalysis)",
                "detector_version": "insightface==1.0.1",
                "software_versions_note": "det_size=(640,640); providers=['CPUExecutionProvider']; v2 run ALSO persists bbox (original-frame coords, pre-padding) and det_score, closing the v1 gap.",
                "bounded_range_note": bounded_note,
            }

            if full:
                frame_w.writerow(frame_row)
            else:
                frame_rows.append(frame_row)

            for idx, face in enumerate(faces):
                x1, y1, x2, y2 = face.bbox.astype(int)
                bbox_x, bbox_y = int(x1), int(y1)
                bbox_w, bbox_h = int(x2 - x1), int(y2 - y1)
                det_score = float(getattr(face, "det_score", float("nan")))

                px1, py1, px2, py2 = x1, y1, x2, y2
                pw, ph = x2 - x1, y2 - y1
                px1 -= int(pw * PADDING)
                py1 -= int(ph * PADDING)
                px2 += int(pw * PADDING)
                py2 += int(ph * PADDING)
                px1 = max(0, px1)
                py1 = max(0, py1)
                px2 = min(width, px2)
                py2 = min(height, py2)
                crop = frame[py1:py2, px1:px2]
                if crop.size == 0:
                    continue

                sample_id = f"v2_frame_{sampled_index:06d}_face{idx + 1:02d}"

                if full:
                    orig_path = FACES_DIR / f"{sample_id}.jpg"
                    cv2.imwrite(str(orig_path), crop)
                    clahe_img, l_w, clip = apply_strategy_b_clahe(crop)
                    clahe_path = CLAHE_DIR / f"{sample_id}.jpg"
                    cv2.imwrite(str(clahe_path), clahe_img)

                    lm = getattr(face, "landmark_3d_68", None)
                    landmark_raw_path = "NOT_AVAILABLE"
                    if lm is not None:
                        lm_path = LANDMARKS_DIR / f"{sample_id}.json"
                        with open(lm_path, "w") as lf:
                            json.dump({
                                "landmark_3d_68": lm.tolist(),
                                "bbox_x": int(bbox_x), "bbox_y": int(bbox_y),
                                "bbox_w": int(bbox_w), "bbox_h": int(bbox_h),
                                "crop_px1": int(px1), "crop_py1": int(py1),
                            }, lf)
                        landmark_raw_path = str(lm_path.relative_to(REPO))

                    face_row = {
                        "sample_id": sample_id,
                        "source_video_id": "pesta_babi",
                        "sampled_frame_index": sampled_index,
                        "source_frame_index": frame_index,
                        "frame_timestamp_seconds": round(actual_ts, 3),
                        "face_index_in_frame": idx + 1,
                        "person_id": "unknown",
                        "bbox_x": bbox_x, "bbox_y": bbox_y, "bbox_w": bbox_w, "bbox_h": bbox_h,
                        "det_score": round(det_score, 4),
                        "crop_width": crop.shape[1], "crop_height": crop.shape[0],
                        "original_path": str(orig_path.relative_to(REPO)),
                        "clahe_path": str(clahe_path.relative_to(REPO)),
                        "has_clahe": True,
                        "landmark_raw_path": landmark_raw_path,
                        "extraction_run_id": EXTRACTION_RUN_ID,
                        "metadata_source": "verified_from_file: bbox/det_score read directly from this insightface.app.FaceAnalysis.get() call this run, crop written and re-derivable; landmark_3d_68 raw output from same call, persisted verbatim to JSON.",
                    }
                    face_w.writerow(face_row)
                else:
                    face_rows.append({"sample_id": f"test_{sampled_index}_{idx}", "det_score": det_score})

            sampled_index += 1
            if test_n is not None and sampled_index >= test_n:
                break

        frame_index += 1

    cap.release()
    if frame_f:
        frame_f.close()
    if face_f:
        face_f.close()

    elapsed = time.time() - t0
    print(f"sampled_frames={sampled_index} faces_detected={n_faces_total} elapsed={elapsed:.1f}s "
          f"throughput={sampled_index / elapsed:.3f} sampled_frames/sec")

    if test_n is not None:
        total_sampled_frames_full = total_frames // frame_interval + 1
        est_full_seconds = total_sampled_frames_full / (sampled_index / elapsed)
        print(f"ESTIMATE full video ({total_sampled_frames_full} sampled frames at {TARGET_FPS}fps): "
              f"{est_full_seconds:.0f}s = {est_full_seconds/60:.1f} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=int, default=None)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=None)
    args = ap.parse_args()
    run(test_n=args.test, max_seconds=args.max_seconds, full=args.full)
