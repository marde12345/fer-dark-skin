# PAPUAN V2 Extraction Methodology Report

**Date:** 2026-10-19
**Scope:** Concrete deliverables built from existing artifacts only — no re-extraction, no re-detection, no API calls. Companion to the prior read-only audit (`docs/reports/PAPUAN_V2_STANDARDIZATION_AUDIT_2026-10-19.md`).
**Outputs in this directory:** `frame_level_extraction_manifest.csv` (250 rows), `per_face_sample_manifest.csv` (645 rows), `qc_threshold_candidates.md`. Validator: `tools/papuan_v2/validate_extraction_manifests.py`. Builder: `tools/papuan_v2/build_extraction_manifests.py`.

---

## 1. Sampling method

**Verified.** `src/fer_dataset/pipeline/frame_extractor.py:63-98`.

- `frame_interval = max(int(original_fps / target_fps), 1)` (line 63-66). With `original_fps=25.0` and `target_fps=2.0` (from `data/papuan_v2/raw/source_video_manifest.json`'s `sampling_config.target_fps`), `frame_interval = 12`.
- The extractor reads the video sequentially with `cap.read()` and keeps a frame **iff `frame_index % frame_interval == 0`** (line 82), where `frame_index` counts every decoded source frame starting at 0. This is fixed-interval frame-index stepping, **not** re-timestamping at a fixed output FPS and not keyframe-based sampling.
- Saved filename is `frame_{saved_index:06d}.jpg` (line 84), where `saved_index` increments only on save (line 92) — i.e. it is the **sampled sequence index** (0, 1, 2, ...), not the source frame index. The source frame index is **not** encoded in the filename anywhere.
- Because every 12th source frame is saved in strict order starting at frame 0, `source_frame_index = sampled_frame_index * frame_interval` is an **exact, verified** relationship given this code — not an approximation. This is the formula used to populate `source_frame_index` in `frame_level_extraction_manifest.csv`.
- `debug=True` / `max_frames=100` config exists (`config/config.yaml:debug`) but the actual papuan_v2 run used `max_frames=250` per `source_video_manifest.json:sampling_config.max_frames` (the pipeline's own debug cap, not the `config/config.yaml` default — confirmed these are two different config paths, `build_pilot_source.py` does not read `config/config.yaml`).

## 2. Video-level metadata

**Verified / Derived.**

- `source_video_manifest.json` (`data/papuan_v2/raw/source_video_manifest.json`) stores: filename, path, `sha256`, `original_fps` (25.0), `total_frames_in_source` (144084). No width/height field exists in this JSON.
- Video width/height **were not persisted anywhere on disk** prior to this report. We derived them by opening the actual (unmodified, copied-not-moved) source video file with `cv2.VideoCapture` and reading `CAP_PROP_FRAME_WIDTH`/`HEIGHT`: **1920×1080**. We cross-checked `CAP_PROP_FPS` (25.0) and `CAP_PROP_FRAME_COUNT` (144084) against the manifest's values — both matched exactly, which is independent confirmation the manifest's recorded FPS/frame-count are accurate for this file.
- Duration = `144084 / 25.0 = 5763.36` seconds (≈96.06 minutes). Derived (not directly stored as a field), but exact given the verified inputs.
- `generated_at` (`2026-09-19T07:46:28.359979+00:00`) is the closest thing to a run identifier; there is no explicit `run_id` field in any artifact. We used this timestamp as `extraction_run_id` in the manifest, flagged as derived.

## 3. Timestamp calculation and VFR/rounding risk

**Verified (mechanism) / Not available (VFR status).**

- `frame_extractor.py` computes **no explicit timestamp at all** — it does sequential `cap.read()` calls and infers position purely by counting reads (`frame_index += 1` at line 97). There is no use of `cap.get(cv2.CAP_PROP_POS_MSEC)` or any PTS-based timestamp anywhere in the extraction code.
- We derive `requested_timestamp_seconds = actual_timestamp_seconds = source_frame_index / original_fps` in the manifest. This is **only exact if the source video is genuinely constant-frame-rate (CFR)** with no dropped/duplicated frames during decode. If the video is variable-frame-rate (VFR), `cap.read()` still returns frames in order but the true wall-clock timestamp of the Nth frame would drift from `N / fps`.
- **VFR/CFR status: unknown.** `ffprobe` is not installed in this environment (`which ffprobe` → not found), so we could not inspect per-packet PTS to determine this directly. OpenCV's `CAP_PROP_FPS` only reports a single average value regardless of CFR/VFR, so matching `source_fps` against the manifest (done above) does not resolve this question. **Risk, not fact:** if the source `.mp4` is VFR, `actual_timestamp_seconds` in the manifest should be treated as an approximation with unknown bounded error, not a ground-truth timestamp. Recommend running `ffprobe -select_streams v -show_entries frame=pkt_pts_time` (or similar) once ffmpeg/ffprobe is available, as a cheap follow-up that needs no pipeline rerun.

## 4. Detection, bbox, crop, and filename mechanics

**Verified — this was the most important fact to nail down, and the answer is bbox is computed but never persisted.**

- `src/fer_dataset/pipeline/face_detector.py:23-31`: `insightface.app.FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])`, `det_size=(640,640)`. This is InsightFace's SCRFD detector bundled in `buffalo_l`.
- `face_detector.py:56`: `faces = self.app.get(image)` returns InsightFace `Face` objects, each carrying `.bbox` (and much more — landmarks, det score, embedding) **in memory only**.
- `face_detector.py:62-78`: bbox is read (`x1,y1,x2,y2 = face.bbox.astype(int)`), then **padded by 20%** on each side (`padding = 0.2`), then clamped to image bounds. This padded box is used only to slice the crop (`crop = image[y1:y2, x1:x2]`, line 80).
- `face_detector.py:87-90`: only the **cropped pixel array** is written to disk via `cv2.imwrite`. There is no JSON/CSV/sidecar write anywhere in this function, in `FaceDetector`, or in `build_pilot_source.py` (confirmed by reading the full detection call site and by grepping the whole repo for `bbox`, `detections.json`, `faces_manifest` — the only `bbox` reference in the entire codebase is `face_detector.py:62`). **Conclusion: bounding box coordinates and detector confidence scores are not recoverable from any artifact on disk today.** They exist only transiently in memory during a run and are lost once that run ends. `bbox_x/y/w/h` are therefore populated as the literal string `NOT_AVAILABLE` for all 645 rows in `per_face_sample_manifest.csv` — this is a genuine gap, not an oversight in the search.
- Filename: `filename = f"{stem}_face{idx + 1:02d}.jpg"` (line 85), where `stem` is the sampled frame's filename stem (`frame_NNNNNN`) and `idx` is the 0-based position of this face within InsightFace's per-frame `faces` list (so `face01`, `face02`, ... reset per frame). **Confirmed (not assumed):** this is a per-frame detection-order index, not a cross-frame identity — matches the prior audit's conclusion, now re-derived directly from code rather than cited.
- CLAHE: `src/fer_dataset/shared/clahe.py` operates purely on the already-cropped jpg (confirmed in this report's own Check 5: all 645 original/CLAHE pairs have byte-identical dimensions, verified by re-opening every pair with `cv2.imread`, not merely cited from the prior audit).

## 5. Detector / model / config versions

**Verified.**

- Detector: InsightFace `buffalo_l` bundle, SCRFD-based face detector (`face_detector.py:23-24`).
- `det_size=(640,640)` (`face_detector.py:18,30`), `providers=["CPUExecutionProvider"]` (CPU-only inference, no GPU).
- `insightface>=1.0.1` is the `pyproject.toml` specifier; the actually **resolved/locked** version is `insightface==1.0.1` per `uv.lock` (`name = "insightface" / version = "1.0.1"`).
- Landmark sub-model used elsewhere in the same `buffalo_l` bundle (not for bbox): `1k3d68.onnx`, `landmark_3d_68` — confirmed by `experiments/EXP-PAP-005/metadata.json:"landmark_schema": "insightface_landmark_3d_68"` and consistent across all landmark JSON files read for this report.

---

## 6. Manifest build summary

- `frame_level_extraction_manifest.csv`: 250 rows (one per sampled frame, indices 0–249, matching `source_video_manifest.json`'s `outputs.frames_sampled: 250`). Per-video fields (fps, sha256, resolution, etc.) repeat on every row by design. `detected_faces_count` is derived by counting face-crop filenames sharing each `sampled_frame_index` — 165/250 sampled frames have ≥1 detected face, 85 have zero (these still appear as rows with `detected_faces_count=0`, they are not silently dropped). `frame_width`/`frame_height` are `NOT_AVAILABLE` because the extracted full-frame `.jpg` files were never retained on disk (only face crops and CLAHE crops persisted) — this is a genuine gap, not computed.
- `per_face_sample_manifest.csv`: 645 rows, one per face crop, confirming the 645 figure directly from `find data/papuan_v2/faces -name '*.jpg' | wc -l`. `bbox_*` = `NOT_AVAILABLE` for all rows (§4). `person_id` = `NOT_AVAILABLE` for all rows (no identity tracking exists anywhere — confirmed again in this pass, no new evidence found). `qc_blur_variance`/`qc_width`/`qc_height` are real per-image computations (`cv2.Laplacian(gray, CV_64F).var()` and actual pixel dimensions) over all 645 crops, not estimates. `landmark_status`/`expression_label*` are real joins against `experiments/EXP-PAP-005/*.json` and `experiments/EXP-PAP-004/human_labels.csv` by `sample_id`/`image_id`.
- `qc_status` is left as `PENDING_THRESHOLD` for all 645 rows — no threshold is set by this report. See `qc_threshold_candidates.md` for the real percentile distribution and a few explicitly illustrative (not adopted) candidate cutoffs.

## 7. Validation results

`tools/papuan_v2/validate_extraction_manifests.py`, run against the manifests above:

| Check | Result |
|---|---|
| Path existence (original/clahe/landmark paths) | 0 missing / 1290 checked |
| `sample_id` uniqueness | 645 unique / 645 rows, 0 duplicates |
| bbox validity (NOT_AVAILABLE exempt) | 645 exempt, 0 invalid |
| Frame index validity + monotonicity | monotonic=True, unique=True, 0 negative |
| Original vs CLAHE dimension correspondence | 645 pairs checked programmatically, 0 mismatches |
| Orphan check (landmark/label sources ↔ manifest, both directions) | 0 orphans in any direction |

All checks passed on the first clean run after fixing two JSON-shape bugs in the manifest builder itself (`calibration_batch_40_predictions.json` and `batch3_predictions.json` turned out to use different container shapes — dict-keyed-by-id vs. list-of-records — discovered and fixed during this pass, not a data gap).

---

## 8. Classification summary

**Verified (read directly from code/data):**
- Sampling method, frame_interval formula, filename semantics (§1, §4)
- Video FPS/frame-count/resolution/sha256/duration (§2)
- Detector model/version/config (§5)
- bbox is computed in-memory but never persisted (§4) — verified absent, not merely unconfirmed
- All manifest row counts, QC metrics, landmark/label join results (§6, §7)

**Derived/computed (exact given verified inputs, not independently observed):**
- `source_frame_index` from `sampled_frame_index * frame_interval`
- `actual_timestamp_seconds` from `source_frame_index / source_fps`
- `extraction_run_id` from `source_video_manifest.json`'s `generated_at` (no explicit run_id field exists)

**Not available — requires rerun or new tooling, genuinely missing, not fabricated:**
- Per-crop bbox coordinates and detector confidence (would need a detection-only rerun over the already-extracted frames — cheap, but frames themselves are also gone, so this would need frame re-extraction too, since frame `.jpg` files were not retained)
- `frame_width`/`frame_height` for the 250 sampled frames (frames not retained on disk)
- CFR vs. VFR determination for the source video (needs `ffprobe`, not installed in this environment)
- `person_id` / identity tracking (confirmed absent again, no new evidence)
