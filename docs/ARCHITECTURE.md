# System Architecture

## Overview

```
                     Video
                       │
                       ▼
             Frame Extractor
                       │
                       ▼
             Face Detector
                       │
                       ▼
            Face Quality Filter
                       │
                       ▼
            Landmark Detector
                       │
                       ▼
          Expression Classifier
                       │
                       ▼
             Dataset Builder
```

---

# Modules

## 1. Frame Extractor

Input

```
video.mp4
```

Output

```
frame_000001.jpg
```

Responsibilities

- Read video
- Extract frames
- Save images

---

## 2. Face Detector

Input

```
Frame
```

Output

```
Bounding Box
Confidence
```

Responsibilities

- Detect faces
- Crop faces
- Save crops

---

## 3. Quality Filter

Input

```
Face Crop
```

Output

```
Valid Face
```

Responsibilities

- Remove blurry images
- Remove tiny faces
- Remove low confidence detections

---

## 4. Landmark Detector

Input

```
Face Crop
```

Output

```
468 facial landmarks
```

Responsibilities

- Detect facial landmarks
- Save landmark files

---

## 5. Expression Classifier

Input

```
Face Crop
```

Output

```
Expression
Confidence
```

Responsibilities

- Predict expression
- Calculate confidence

---

## 6. Dataset Builder

Input

```
Predictions
```

Output

```
images/

annotations.csv

metadata.csv
```

Responsibilities

- Save images
- Save CSV
- Generate metadata

---

# Data Flow

```
Video

↓

Frames

↓

Faces

↓

Filtered Faces

↓

Landmarks

↓

Expression Labels

↓

Dataset
```

---

# Error Handling

Every module produces logs.

Example

```
[FrameExtractor]

Video loaded

11253 frames extracted
```

Example

```
[FaceDetector]

Frame 120 skipped

Reason:
No face detected
```

---

# Checkpointing

```
Frame Extraction
        │
        ▼
checkpoint

        │
        ▼
Face Detection
        │
        ▼
checkpoint

        │
        ▼
Landmark Detection
        │
        ▼
checkpoint

        │
        ▼
Expression Classification
        │
        ▼
checkpoint
```