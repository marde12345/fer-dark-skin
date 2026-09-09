# Software Design Document (SDD)

> This document is reconciled against the actual codebase as of Phase 0 baseline commit `f9c9fae`. Where earlier versions of this document described planned-but-unimplemented functionality, those sections have been corrected and explicitly labeled `Planned / Not currently implemented`. See `docs/ARCHITECTURE.md` for the module-by-module breakdown and `docs/REPO_AUDIT_REPORT.md` for the full audit this reconciliation is based on.

## 1. Overview

### Objective

This project aims to build a semi-automatic pipeline for generating a labeled Facial Expression Recognition (FER) dataset from video recordings.

The generated dataset consists of:

- Cropped face images
- Facial expression pseudo-labels (model-generated, not manually annotated)
- Facial landmarks and derived geometric features
- Per-image skin-tone estimate
- Confidence scores

The final dataset is intended to support research on Facial Expression Recognition involving subjects with diverse skin tones.

---

## 2. Input

### Video Specification

| Property | Value |
|----------|-------|
| Format | MP4 |
| Resolution | 1920 × 1080 |
| Duration | ~96 minutes |
| Source | Raw Video (`data/raw/videos/pesta_babi.mp4`) |

---

## 3. Output

```text
data/
├── intermediate/
│   ├── frames/                   frame_000000.jpg, ...
│   ├── faces/                    frame_XXXXXX_faceNN.jpg
│   ├── annotations.csv           filename, label, confidence
│   ├── landmarks/                [optional] keypoint visualization overlays
│   ├── landmarks_468/            per-image landmark files (.npy or .json)
│   └── landmark_features.csv     geometric + skin-tone features, joined to labels
└── processed/
    ├── images/                   img_000001.jpg, ...
    └── annotations.csv           filename, label, confidence

reports/
├── dataset_report.md
├── landmark_comparison_summary.csv
└── assets/                       generated plots
```

Note: this output structure reflects what the code actually writes. A single unified `metadata.csv` with bounding box / blur score / brightness / face size / frame index (as described in an earlier version of this document) is **not** currently produced — only `filename`, `label`, `confidence` are recorded in the annotations CSVs.

---

## 4. Functional Requirements

The system shall:

- Extract frames from video at a configurable sampling rate.
- Detect human faces in each frame.
- Predict a facial expression pseudo-label and confidence score for each detected face using a pretrained model.
- Build a final image dataset with corresponding label annotations.
- Extract facial landmarks and derived geometric features for each face (optional stage, config-gated).
- Estimate skin tone per face from color-space statistics.
- Generate a summary report of the resulting dataset (label distribution, confidence statistics).

The following are **not** current functional requirements of the implemented system — see `docs/ARCHITECTURE.md` Modules 3 and "Checkpointing" for details:

- Quality filtering of low-quality faces (blur, brightness, size): `Planned / Not currently implemented`.
- Checkpoint/resume support: `Planned / Not currently implemented`.

---

## 5. Non-functional Requirements

- Modular (one class per pipeline stage)
- Reproducible (deterministic given fixed input video, fixed model weights, fixed pinned dependency versions — no randomness/seeding is present or required in the current implementation, see `docs/EXPERIMENT.md`)
- Configurable (via `config/config.yaml`, though several config keys are not yet wired to code — see `docs/REPO_AUDIT_REPORT.md` Section J)
- Cross-platform (macOS, as currently developed/run)

Fault tolerance, scalability, and multi-threading are not current properties of the implementation and are not claimed here.

---

## 6. Dataset Labels

The pseudo-labeling model (HSEmotion `enet_b0_8_best_vgaf`) emits labels from its own vocabulary. Observed labels in the Phase 0 baseline run (`docs/EXPERIMENT.md`, EXP-000) were: `Anger`, `Fear`, `Neutral`, `Sadness`, `Happiness`, `Surprise`. `Disgust` is part of the model's label set but did not appear in the 100-frame baseline sample. No label remapping step exists in `src/` — labels are stored exactly as emitted by the model.

| Label (as emitted by the model) |
|--------|
| Anger |
| Disgust |
| Fear |
| Happiness |
| Neutral |
| Sadness |
| Surprise |

---

## 7. Metadata

Each row of `data/processed/annotations.csv` currently stores:

- `filename`
- `label` (expression pseudo-label)
- `confidence` (softmax confidence score)

Each row of `data/intermediate/landmark_features.csv` additionally stores:

- `face_filename`, `dataset_filename`, `label`
- `skin_tone`, `L_weighted`
- `brow_lowering_distance`, `lip_corner_distance`, `mouth_openness`, `inter_ocular_distance`, `iod_px`

Bounding box, blur score, brightness, face size, and frame index are **not** currently stored anywhere in the pipeline's output metadata.

---

## 8. Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.12 |
| Package Manager | uv |
| Video/Image Processing | OpenCV |
| Face Detection | InsightFace (SCRFD detector, `buffalo_l` model bundle), CPU execution provider |
| Facial Landmark Detection | MediaPipe FaceLandmarker (478-point: 468 mesh + 10 iris) |
| Facial Expression Pseudo-labeling | HSEmotion ONNX (`enet_b0_8_best_vgaf`), pretrained, not fine-tuned |
| Data Processing | Pandas |
| Plotting | Matplotlib |
| Configuration | YAML |

Correction from a prior version of this document: face detection is **InsightFace/SCRFD**, not YOLO. `ultralytics` (YOLO) appears as a dependency in `pyproject.toml` but is not imported or used by any current pipeline stage in `src/`.

---

## 9. Directory Structure

```text
FER-Dataset/

config/
data/
docs/
logs/
models/
src/
tests/
tools/
notebooks/
reports/
```

`tools/` and `notebooks/` were not listed in a prior version of this document; both exist and are part of the current repository (see `docs/REPO_AUDIT_REPORT.md` Section B for their contents). `tests/` currently contains no test files.

---

## 10. Pipeline

```text
Video
    │
    ▼
Frame Extraction
    │
    ▼
Face Detection
    │
    ▼
Emotion Pseudo-labeling
    │
    ▼
Dataset Builder
    │
    ▼
[optional] Landmark / Feature Extraction
    │
    ▼
Dataset Report
```

Removed from this diagram relative to a prior version of this document:

- **Quality Filtering** — `Planned / Not currently implemented` (see Section 4 above).
- **Face Alignment** — not present as a distinct implemented pipeline stage anywhere in `src/`; no code performs geometric face alignment as a separate step.

`Landmark Comparison Analysis` (`src/landmark_comparison.py`) is an active downstream analysis step that currently runs standalone (`python src/landmark_comparison.py`), separately from this `main.py` pipeline. It is not shown in this diagram because it is not currently invoked from `main.py`; see `docs/ARCHITECTURE.md` Module 8. Wiring it in as an optional stage is planned for a future refactoring phase, not yet implemented.

---

## 11. Checkpoint System

**Status: `Planned / Not currently implemented`.**

There is no checkpoint/resume mechanism in the current implementation. Each stage clears its own prior output at the start of a run, and `main.py` always executes every enabled stage from the beginning; it cannot resume from a partially-completed prior run.

---

## 12. Future Improvements

Items below are aspirational and not part of the current implementation. Listing them here does not constitute approval to implement them — any of these would require explicit researcher sign-off before implementation, per `docs/REFACTORING_PLAN.md`.

- Quality filtering (blur, brightness, face-size) as an implemented pipeline stage.
- Checkpoint/resume support.
- Multi-video processing.
- Human verification interface.
- Dataset balancing.
- Multi-thread processing.
