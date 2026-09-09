# FER Dataset Generation Pipeline

> A semi-automatic pipeline for generating a labeled Facial Expression Recognition (FER) dataset from video recordings.

---

## Overview

This project aims to build a reproducible pipeline for generating a labeled Facial Expression Recognition (FER) dataset from videos.

Instead of manually annotating every image, the pipeline automatically:

- Extracts frames from videos
- Detects human faces
- Detects facial landmarks and derived geometric features
- Predicts facial expressions using a pretrained FER model (pseudo-labeling, not human annotation)
- Generates a structured dataset with labels

The generated dataset is intended to support research involving facial expression recognition across subjects with diverse skin tones.

There is currently no quality-filtering stage (blur/face-size/brightness) and no checkpoint/resume system — each run processes the full configured input from scratch. See `docs/ARCHITECTURE.md` for the authoritative current-state architecture.

---

## Features

- 🎥 Video-to-dataset pipeline
- 😀 Emotion pseudo-labels (HSEmotion model vocabulary)
- 📍 Facial landmark extraction with geometric features and skin-tone estimation
- 📦 Automatic dataset generation
- ⚙️ YAML-based configuration
- 📊 Optional downstream landmark comparison analysis
- 📝 Experiment logging
- 🔄 Reproducible workflow (deterministic given fixed input, model weights, and dependency versions)

---

## Supported Facial Expressions

The HSEmotion model's own label vocabulary (as stored, unmapped, in the dataset):

| Label |
|--------|
| Anger |
| Disgust |
| Fear |
| Happiness |
| Neutral |
| Sadness |
| Surprise |

---

## Project Structure

```text
FER-Dataset/
│
├── config/
│   └── config.yaml
│
├── data/
│   ├── raw/videos/
│   ├── intermediate/
│   │   ├── frames/
│   │   ├── faces/
│   │   ├── landmarks_468/
│   │   └── annotations.csv
│   └── processed/
│       ├── images/
│       └── annotations.csv
│
├── docs/
│   ├── SDD.md
│   ├── ARCHITECTURE.md
│   ├── EXPERIMENT.md
│   ├── REPO_AUDIT_REPORT.md
│   └── REFACTORING_PLAN.md
│
├── src/
│   └── fer_dataset/
│       ├── main.py            # entry point (uv run python -m fer_dataset.main)
│       ├── pipeline/          # frame_extractor, face_detector, emotion_classifier,
│       │                      # dataset_builder, landmark_analyzer, dataset_report, ...
│       └── analysis/          # landmark_comparison (optional, config-gated stage)
│
├── tools/
│   └── visualize_landmark_npy.py
│
├── tests/
│
├── notebooks/
├── reports/
│
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Pipeline

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
     Expression Pseudo-labeling
                    │
                    ▼
          Dataset Builder
                    │
                    ▼
      Landmark / Feature Extraction  (optional, landmark_analysis.enabled)
                    │
                    ▼
   Landmark Comparison Analysis      (optional, analysis.landmark_comparison.enabled)
                    │
                    ▼
            Dataset Report
```

There is no Quality Filtering or Face Alignment stage in the current implementation — see `docs/ARCHITECTURE.md` for the full current-state module breakdown.

---

## Installation

### Clone Repository

```bash
git clone <repository-url>

cd FER-Dataset
```

### Install Dependencies

```bash
uv sync
```

or

```bash
uv venv

source .venv/bin/activate

uv sync
```

---

## Configuration

All parameters are stored in

```text
config/config.yaml
```

Example (see `config/config.yaml` for the complete, current set of keys):

```yaml
video:
  path: data/raw/videos/pesta_babi.mp4
  fps: 2

landmark_analysis:
  enabled: true
  save_format: npy

analysis:
  landmark_comparison:
    enabled: false   # set true to run landmark comparison after feature extraction

debug:
  enabled: true
  max_frames: 100
```

---

## Running the Pipeline

```bash
uv run python -m fer_dataset.main
```

---

## Output

```
data/processed/
├── images/
└── annotations.csv
```

---

## Annotation Format

### data/processed/annotations.csv

| Column | Description |
|----------|-------------|
| filename | Image filename (renumbered `img_NNNNNN.jpg`) |
| label | Expression pseudo-label |
| confidence | Softmax confidence score |

Example

| filename | label | confidence |
|----------|-------|-----------|
| img_000001.jpg | Fear | 0.36 |
| img_000002.jpg | Neutral | 0.49 |

There is no separate `metadata.csv` — bounding box, blur score, brightness, and head pose are not currently captured anywhere in the pipeline's output.

---

## Optional: Landmark Comparison Analysis

When `landmark_analysis.enabled: true`, the pipeline additionally produces `data/intermediate/landmark_features.csv` (landmark geometry, skin-tone estimate, and the associated emotion label per face crop).

Setting `analysis.landmark_comparison.enabled: true` runs an additional optional stage after landmark/feature extraction, comparing these geometric features across emotion labels and skin-tone groups, writing `reports/landmark_comparison_summary.csv` and comparison plots to `reports/assets/`. This stage consumes `data/intermediate/landmark_features.csv` for label association — never `data/processed/annotations.csv`. When the flag is `false` (the default), this stage is skipped entirely and the rest of the pipeline is unaffected.

It can also be run standalone, independent of `main`:

```bash
uv run python -m fer_dataset.analysis.landmark_comparison
```

---

## Intermediate Outputs

```text
data/intermediate/
├── frames/
├── faces/
├── annotations.csv
├── landmarks_468/
└── landmark_features.csv
```

Each pipeline run clears and regenerates these from scratch — there is no checkpoint/resume system, so an interrupted run must be restarted from the beginning.

---

## Landmark Visualization Tool

`tools/visualize_landmark_npy.py` renders a saved landmark `.npy` file as a scatter plot, optionally overlaid on its source face-crop image:

```bash
uv run python tools/visualize_landmark_npy.py \
  --input <landmark.npy> \
  [--output <blank_canvas.png>] \
  [--image <face_crop.jpg>] \
  [--overlay-output <overlay.png>]
```

`--output`/`--overlay-output` default to `reports/assets/landmark_<input-stem>_{blank,overlay}.png` if omitted; `--image` is optional and enables the overlay plot when provided.

---

## Experiment Tracking

All experiments should be documented in

```
docs/EXPERIMENT.md
```

Examples include:

- Frame extraction FPS
- Detection confidence
- Blur threshold
- FER confidence threshold
- Dataset balancing

---

## Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.12 |
| Environment | uv |
| Computer Vision | OpenCV |
| Face Detection | InsightFace (SCRFD, `buffalo_l`) |
| Landmark Detection | MediaPipe FaceLandmarker |
| FER | HSEmotion (pretrained, `enet_b0_8_best_vgaf`) |
| Data Processing | Pandas |
| Progress Bar | tqdm |
| Configuration | YAML |

---

## Future Improvements

- Face tracking
- Duplicate face removal
- Human verification interface
- Batch video processing
- Multi-thread processing
- GPU acceleration
- Dataset quality report
- Automatic train/validation/test split

---

## Documentation

Project documentation is available in

```
docs/
```

| Document | Description |
|-----------|-------------|
| SDD.md | Software Design Document |
| ARCHITECTURE.md | System Architecture |
| EXPERIMENT.md | Experiment Log |
| REPO_AUDIT_REPORT.md | Codebase audit (current-state findings) |
| REFACTORING_PLAN.md | Refactoring plan and approved decisions |

---

## Research Goal

The primary objective of this project is to develop a semi-automatic FER dataset generation pipeline that reduces manual annotation effort while maintaining high-quality labeled facial expression images suitable for research purposes.

---

## License

This project is developed for academic research purposes.
