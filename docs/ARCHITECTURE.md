# System Architecture

> This document describes the pipeline as it is **currently implemented**. It is reconciled against source code as of the Phase 0 baseline commit `f9c9fae` (see `docs/EXPERIMENT.md`) and the findings in `docs/REPO_AUDIT_REPORT.md`. Where documentation and code previously disagreed, code is treated as the source of truth. Items that are planned but not implemented are explicitly labeled `Planned / Not currently implemented`.

## Overview

```text
                     Config (config/config.yaml)
                       │
                       ▼
             Frame Extractor
                       │
                       ▼
             Face Detector
                       │
                       ▼
        Emotion Pseudo-labeling (Classifier)
                       │
                       ▼
             Dataset Builder
                       │
                       ▼
        Landmark / Feature Extraction (optional stage)
                       │
                       ▼
             Dataset Report
```

`main.py` runs these six stages in this order. A seventh stage, **Landmark Comparison Analysis**, exists in the codebase (`src/landmark_comparison.py`) as an active downstream analysis step but is **not currently invoked from `main.py`** — it is run standalone. Wiring it into `main.py` as an optional pipeline stage is planned for a later refactoring phase (see `docs/REFACTORING_PLAN.md` addendum, Approved Decision #2); it must not be assumed to already be wired in.

There is no dataset train/validation/test split, no model training, and no quality-filtering stage anywhere in this pipeline. This is a dataset-generation/pseudo-labeling pipeline, not a model-training pipeline.

---

# Modules (Current Implementation)

## 1. Frame Extractor

**Source:** `src/frame_extractor.py`

Input

```text
video.mp4  (path from config: video.path)
```

Output

```text
data/intermediate/frames/frame_000000.jpg, frame_000001.jpg, ...
```

Responsibilities

- Open the video with OpenCV and read its FPS/frame count.
- Sample frames at a configurable target FPS (`video.fps` in config), using interval `max(int(original_fps / target_fps), 1)`.
- Save each sampled frame as a JPEG.
- In debug mode (`debug.enabled`), stop after `debug.max_frames` saved frames.
- Clear the output directory of prior `*.jpg` files before writing (destructive by default; happens at construction time, before extraction runs).

Not implemented: face-size/blur/brightness filtering at this stage (there is none anywhere in the pipeline — see Module 3 below).

---

## 2. Face Detector

**Source:** `src/face_detector.py`

Input

```text
Frame (data/intermediate/frames/*.jpg)
```

Output

```text
Face crop (data/intermediate/faces/frame_XXXXXX_faceNN.jpg)
```

Responsibilities

- Detect faces using InsightFace `FaceAnalysis` with the `buffalo_l` model bundle (SCRFD detector), CPU execution provider, detection size 640×640.
- Crop each detected face with 20% bounding-box padding on all sides, clamped to image bounds.
- Save each crop as a JPEG. Skips crops that end up empty after clamping.
- Clears the output directory of prior `*.jpg` files before detection begins.

**Note:** `config/config.yaml`'s `face_detection.confidence` key exists but is not read or applied by this module — InsightFace's own internal defaults are used instead. This is a documented discrepancy, not a bug fix target for this phase.

---

## 3. Quality Filter

**Status: `Planned / Not currently implemented`.**

`docs/DEVELOPMENT_ROADMAP.md` lists face quality filtering (blur detection, brightness detection, face-size filtering) as a milestone, and `config/config.yaml` defines `quality.min_face_size` and `quality.blur_threshold` keys. **No code in `src/` reads these config keys or performs any blur/brightness/size filtering.** Every face crop produced by the Face Detector proceeds to the next stage unfiltered.

This stage must not be implemented as part of the current refactoring phase (Phase 2). If it is implemented in a future phase, it will change dataset composition and requires explicit researcher approval as a behavioral/methodology change, not a routine refactor.

---

## 4. Emotion Pseudo-labeling (Expression Classifier)

**Source:** `src/emotion_classifier.py`

Input

```text
Face crop (data/intermediate/faces/*.jpg)
```

Output

```text
data/intermediate/annotations.csv  (filename, label, confidence)
[optional] data/intermediate/landmarks/*.jpg  (keypoint visualization overlays)
```

Responsibilities

- Run each face crop through the HSEmotion ONNX model `enet_b0_8_best_vgaf` to obtain per-class logits.
- Apply softmax to the logits to obtain a confidence score for the predicted label.
- Write one row per face crop to the intermediate annotations CSV.
- If `visualization.enabled` is true, additionally run each crop through a **second, independent** InsightFace `buffalo_l` instance purely to draw 5-point keypoints on a saved visualization image. This is a known duplication (see `docs/EXPERIMENT.md`, Known Issues) — it does not affect labels or confidence values.
- Deletes any pre-existing annotations file before writing.

**Note:** `config/config.yaml`'s `expression.confidence_threshold` key exists but is not applied — no prediction is filtered out based on confidence; all predictions are recorded.

---

## 5. Dataset Builder

**Source:** `src/dataset_builder.py`

Input

```text
data/intermediate/faces/*.jpg
data/intermediate/annotations.csv
```

Output

```text
data/processed/images/img_000001.jpg, ...
data/processed/annotations.csv  (filename, label, confidence)
```

Responsibilities

- Read the intermediate annotations CSV.
- For each row whose source face crop still exists on disk, copy it into `data/processed/images/` under a renumbered filename and record it in the final annotations CSV. Rows whose source file is missing are silently skipped (not written to the output CSV).
- Clears the output image directory and deletes any pre-existing final annotations file before building.

Not currently produced: a separate `metadata.csv` (bounding box, blur score, brightness, face size, frame index) — only `filename`, `label`, `confidence` are written. `docs/SDD.md`'s prior claim of richer per-image metadata did not match actual output and has been corrected.

---

## 6. Landmark / Feature Extraction (Optional Stage)

**Source:** `src/landmark_analyzer.py`

Runs only if `landmark_analysis.enabled` is true in config (currently true by default).

Input

```text
data/intermediate/faces/*.jpg
data/processed/annotations.csv  (for label lookup)
```

Output

```text
data/intermediate/landmarks_468/*.npy (or *.json, per landmark_analysis.save_format)
data/intermediate/landmark_features.csv
```

Responsibilities

- Detect 478 facial landmarks (468 mesh points + 10 iris points) per face crop using MediaPipe FaceLandmarker (`face_landmarker.task`, auto-downloaded if missing), with detection/presence/tracking confidence thresholds of 0.5.
- Compute four geometry-derived features (`brow_lowering_distance`, `lip_corner_distance`, `mouth_openness`, `inter_ocular_distance`) from specific landmark indices (33, 55, 65, 61, 291, 13, 14, 263), each normalized by inter-ocular distance.
- Compute a skin-tone estimate and bucket (`Dark` / `Medium-Dark` / `Medium-Light` / `Light`) from the LAB color-space L-channel of each face crop.
- Attach a label to each row by matching the face-crop filename against the final annotations CSV; if no filename match is found, falls back to positional (row-order) alignment. **This fallback is a known, unfixed issue** — see `docs/EXPERIMENT.md`, Known Issues, and `docs/REPO_AUDIT_REPORT.md` Section E.
- Save per-image landmark coordinate files and one aggregated feature CSV.

---

## 7. Dataset Report

**Source:** `src/dataset_report.py`

Input

```text
data/processed/annotations.csv
```

Output

```text
reports/dataset_report.md
reports/assets/label_distribution.png
reports/assets/confidence_histogram.png
reports/assets/confidence_per_class.png
```

Responsibilities

- Compute label distribution, confidence statistics (mean/median/std/min/max), and per-class mean confidence.
- Render a markdown report and three plots.

---

## 8. Landmark Comparison Analysis (Active, Not Wired Into `main.py`)

**Source:** `src/landmark_comparison.py`

**Status:** Active downstream analysis step. Run manually (`python src/landmark_comparison.py`), **not** currently invoked by `main.py`. Wiring it into `main.py` as an optional config-gated stage is planned (see `docs/REFACTORING_PLAN.md` addendum) but has not been implemented as of this document.

Input

```text
data/intermediate/landmark_features.csv
```

Output

```text
reports/landmark_comparison_summary.csv
reports/assets/landmark_*.png  (angry-vs-neutral and per-skin-tone comparison boxplots)
```

Responsibilities

- Compute summary statistics (count/mean/median/std) of the four geometric features, grouped by emotion label and by skin-tone bucket.
- Produce comparison boxplots: angry vs. neutral per feature, and per-emotion-label skin-tone-group comparisons.

---

# Data Flow (Current Implementation)

```text
Video
  ↓
Frames (data/intermediate/frames)
  ↓
Face Crops (data/intermediate/faces)
  ↓
Emotion Labels + Confidence (data/intermediate/annotations.csv)
  ↓
Final Dataset (data/processed/images, data/processed/annotations.csv)
  ↓
[optional] Landmarks + Geometric/Skin-tone Features (data/intermediate/landmarks_468, data/intermediate/landmark_features.csv)
  ↓
Dataset Report (reports/dataset_report.md)

[separately, manual invocation] Landmark Comparison Analysis (reports/landmark_comparison_summary.csv)
```

Note there is no "Filtered Faces" step in the actual data flow — every detected face proceeds through the entire pipeline; see Module 3 above.

---

# Error Handling

Each stage prints progress via `tqdm` and a `section()` header (`src/logger.py`) rather than a structured logging system. There is no per-module structured log file; console output is the only error/progress record. Exceptions during emotion prediction or landmark visualization are caught and the affected image is silently skipped (`emotion_classifier.py`), rather than logged with a reason. This is current behavior, not a documented target — flagged here for accuracy, not proposed for change in this phase.

---

# Checkpointing

**Status: `Planned / Not currently implemented`.**

There is no checkpoint/resume system in the current code. Every run of `main.py` re-executes the entire pipeline end to end and clears prior stage outputs before regenerating them (see the "clears ... before" notes in Modules 1, 2, 4, 5 above). A partial or interrupted run leaves the pipeline in a partially-cleared state with no resume capability.

---

# Cross-References

- Full audit and risk classification: `docs/REPO_AUDIT_REPORT.md`
- Experimental integrity boundaries and known issues: `docs/EXPERIMENT.md`
- Approved decisions and phased execution plan: `docs/REFACTORING_PLAN.md`
