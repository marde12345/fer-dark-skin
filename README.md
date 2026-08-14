# FER Dataset Generation Pipeline

> A semi-automatic pipeline for generating a labeled Facial Expression Recognition (FER) dataset from video recordings.

---

## Overview

This project aims to build a reproducible pipeline for generating a labeled Facial Expression Recognition (FER) dataset from videos.

Instead of manually annotating every image, the pipeline automatically:

- Extracts frames from videos
- Detects human faces
- Filters low-quality face images
- Detects facial landmarks
- Predicts facial expressions using a pretrained FER model
- Generates a structured dataset with labels and metadata

The generated dataset is intended to support research involving facial expression recognition across subjects with diverse skin tones.

---

## Features

- 🎥 Video-to-dataset pipeline
- 😀 Seven facial expression labels
- 📍 Facial landmark extraction
- 📦 Automatic dataset generation
- ⚙️ YAML-based configuration
- 💾 Checkpoint system
- 📊 Metadata generation
- 📝 Experiment logging
- 🔄 Reproducible workflow

---

## Supported Facial Expressions

| Label |
|--------|
| Angry |
| Disgust |
| Fear |
| Happy |
| Neutral |
| Sad |
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
│   ├── raw/
│   │   └── videos/
│   │
│   ├── intermediate/
│   │   ├── frames/
│   │   ├── faces/
│   │   └── landmarks/
│   │
│   └── processed/
│       ├── images/
│       ├── visualization/
│       ├── annotations.csv
│       └── metadata.csv
│
├── docs/
│   ├── SDD.md
│   ├── ARCHITECTURE.md
│   └── EXPERIMENT.md
│
├── logs/
│
├── models/
│
├── src/
│   ├── main.py
│   ├── pipeline.py
│   ├── frame_extractor.py
│   ├── face_detector.py
│   ├── quality_filter.py
│   ├── landmark_detector.py
│   ├── expression_classifier.py
│   ├── dataset_builder.py
│   ├── config.py
│   └── utils.py
│
├── tests/
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
         Quality Filtering
                    │
                    ▼
          Face Alignment
                    │
                    ▼
      Landmark Detection
                    │
                    ▼
     Expression Prediction
                    │
                    ▼
          Dataset Builder
                    │
                    ▼
            Final FER Dataset
```

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

Example

```yaml
video:
  path: data/raw/videos/pesta_babi.mp4
  fps: 2

face_detection:
  confidence: 0.7

quality:
  min_face_size: 120
  blur_threshold: 80

expression:
  confidence_threshold: 0.90

output:
  save_landmarks: true
  save_csv: true
```

---

## Running the Pipeline

```bash
uv run python src/main.py
```

---

## Output

```
processed/

images/

annotations.csv

metadata.csv
```

---

## Annotation Format

### annotations.csv

| Column | Description |
|----------|-------------|
| filename | Image filename |
| label | Expression label |

Example

| filename | label |
|----------|-------|
| img000001.jpg | Happy |
| img000002.jpg | Neutral |

---

## Metadata Format

metadata.csv

| Column | Description |
|----------|-------------|
| filename | Image filename |
| confidence | Prediction confidence |
| blur | Blur score |
| brightness | Brightness score |
| yaw | Head yaw angle |
| pitch | Head pitch angle |
| roll | Head roll angle |
| face_width | Face width |
| face_height | Face height |

---

## Intermediate Outputs

The pipeline stores intermediate results to support checkpointing.

```text
frames/

faces/

landmarks/
```

If the pipeline stops unexpectedly, processing can resume without restarting from the beginning.

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
| Face Detection | YOLO |
| Landmark Detection | MediaPipe Face Mesh |
| FER | Pretrained FER Model |
| Data Processing | Pandas |
| Progress Bar | tqdm |
| Configuration | YAML |

---

## Future Improvements

- Face tracking
- Duplicate face removal
- Automatic skin tone estimation
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

---

## Research Goal

The primary objective of this project is to develop a semi-automatic FER dataset generation pipeline that reduces manual annotation effort while maintaining high-quality labeled facial expression images suitable for research purposes.

---

## License

This project is developed for academic research purposes.
