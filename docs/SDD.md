# Software Design Document (SDD)

## 1. Overview

### Objective

This project aims to build a semi-automatic pipeline for generating a labeled Facial Expression Recognition (FER) dataset from video recordings.

The generated dataset consists of:

- Cropped face images
- Facial expression labels
- Facial landmarks
- Metadata for each face

The final dataset is intended to support research on Facial Expression Recognition involving subjects with diverse skin tones.

---

## 2. Input

### Video Specification

| Property | Value |
|----------|-------|
| Format | MP4 |
| Resolution | 1920 × 1080 |
| Duration | ~96 minutes |
| Source | Raw Video |

---

## 3. Output

```
data/
└── processed/
    ├── images/
    ├── annotations.csv
    └── metadata.csv
```

---

## 4. Functional Requirements

The system shall:

- Extract frames from video.
- Detect human faces.
- Filter low-quality faces.
- Extract facial landmarks.
- Predict facial expression labels.
- Generate a labeled dataset.
- Save metadata.
- Support checkpointing.

---

## 5. Non-functional Requirements

- Modular
- Reproducible
- Configurable
- Fault tolerant
- Scalable
- Cross-platform (macOS)

---

## 6. Dataset Labels

The system generates seven facial expression labels.

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

## 7. Metadata

Each image will store:

- filename
- expression label
- confidence score
- bounding box
- facial landmark file
- blur score
- brightness
- face size
- frame index

---

## 8. Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.12 |
| Package Manager | uv |
| Face Detection | YOLO |
| Landmark Detection | MediaPipe Face Mesh |
| FER Model | Pretrained FER Model |
| Image Processing | OpenCV |
| Data Processing | Pandas |
| Configuration | YAML |

---

## 9. Directory Structure

```
FER-Dataset/

config/

data/

docs/

logs/

models/

src/

tests/
```

---

## 10. Pipeline

```
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
Expression Classification
    │
    ▼
Dataset Builder
```

---

## 11. Checkpoint System

Each module stores intermediate outputs.

```
Video

↓

Frames

↓

Faces

↓

Landmarks

↓

Predictions

↓

Dataset
```

The pipeline can resume from the last successful checkpoint without repeating previous stages.

---

## 12. Future Improvements

- Multi-video processing
- Automatic skin tone estimation
- Human verification interface
- Dataset balancing
- Multi-thread processing