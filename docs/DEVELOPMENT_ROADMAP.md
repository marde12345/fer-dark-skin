# Development Roadmap

> Project roadmap for the Facial Expression Recognition (FER) Dataset Generation Pipeline.

---

# Project Status

| Phase | Status |
|--------|--------|
| Planning | 🟢 Completed |
| Environment Setup | 🟢 Completed |
| Implementation | 🟡 In Progress |
| Testing | ⚪ Not Started |
| Evaluation | ⚪ Not Started |
| Documentation | 🟡 In Progress |

---

# Milestone 1 — Environment Setup

## Objective

Prepare the local development environment.

### Tasks

- [x] Install Homebrew
- [x] Install Python 3.12
- [x] Install uv
- [x] Create virtual environment
- [x] Initialize project
- [x] Create repository structure
- [x] Create documentation
- [ ] Install project dependencies
- [ ] Configure YAML settings

---

# Milestone 2 — Frame Extraction

## Objective

Extract image frames from the input video.

### Input

```
video.mp4
```

### Output

```
frames/
```

### Tasks

- [ ] Read video metadata
- [ ] Support configurable FPS
- [ ] Save extracted frames
- [ ] Progress bar
- [ ] Logging
- [ ] Checkpoint support

---

# Milestone 3 — Face Detection

## Objective

Detect human faces from extracted frames.

### Input

```
frames/
```

### Output

```
faces/
```

### Tasks

- [ ] Load detection model
- [ ] Detect multiple faces
- [ ] Crop faces
- [ ] Save cropped images
- [ ] Save bounding boxes
- [ ] Logging
- [ ] Checkpoint support

---

# Milestone 4 — Face Quality Filtering

## Objective

Remove unusable face images.

### Quality Criteria

- Minimum face size
- Blur threshold
- Detection confidence
- Image brightness

### Tasks

- [ ] Blur detection
- [ ] Brightness detection
- [ ] Face size filtering
- [ ] Save rejected images (optional)

---

# Milestone 5 — Landmark Detection

## Objective

Extract facial landmarks.

### Output

```
landmarks/
```

### Tasks

- [ ] Detect landmarks
- [ ] Save landmark coordinates
- [ ] Save visualization (optional)
- [ ] Logging

---

# Milestone 6 — Expression Classification

## Objective

Predict facial expressions.

### Output

```
Happy
Sad
Neutral
...
```

### Tasks

- [ ] Load pretrained FER model
- [ ] Predict expression
- [ ] Confidence score
- [ ] Save prediction

---

# Milestone 7 — Dataset Builder

## Objective

Generate the final dataset.

### Output

```
processed/

images/

annotations.csv

metadata.csv
```

### Tasks

- [ ] Copy accepted images
- [ ] Generate annotations.csv
- [ ] Generate metadata.csv
- [ ] Verify dataset integrity

---

# Milestone 8 — Visualization

## Objective

Generate debugging visualizations.

Examples

- Bounding boxes
- Landmarks
- Predicted expressions

### Tasks

- [ ] Draw bounding boxes
- [ ] Draw landmarks
- [ ] Draw labels
- [ ] Save visualization

---

# Milestone 9 — Logging

## Objective

Track pipeline execution.

### Tasks

- [ ] Console logging
- [ ] File logging
- [ ] Error logging
- [ ] Execution summary

---

# Milestone 10 — Checkpoint System

## Objective

Allow pipeline recovery after interruption.

### Tasks

- [ ] Save completed stages
- [ ] Resume pipeline
- [ ] Skip completed modules

---

# Milestone 11 — Evaluation

## Objective

Evaluate generated dataset quality.

### Metrics

- Number of frames
- Number of detected faces
- Number of accepted faces
- Expression distribution
- Processing time

### Tasks

- [ ] Generate statistics
- [ ] Generate charts
- [ ] Export summary

---

# Milestone 12 — Final Documentation

### Tasks

- [ ] Update README
- [ ] Update Architecture
- [ ] Update SDD
- [ ] Update Experiment Log
- [ ] Write thesis methodology

---

# Project Checklist

## Planning

- [x] Define project scope
- [x] Design architecture
- [x] Define folder structure
- [x] Create documentation

---

## Development

- [ ] Frame Extraction
- [ ] Face Detection
- [ ] Face Quality Filtering
- [ ] Landmark Detection
- [ ] Expression Classification
- [ ] Dataset Builder

---

## Testing

- [ ] Unit testing
- [ ] Integration testing
- [ ] End-to-end testing

---

## Evaluation

- [ ] Evaluate processing time
- [ ] Evaluate dataset quality
- [ ] Evaluate label distribution

---

## Thesis

- [ ] Chapter 3 (Methodology)
- [ ] Chapter 4 (Implementation)
- [ ] Chapter 5 (Evaluation)

---

# Current Sprint

## Sprint Goal

Complete the first runnable version of the pipeline.

### Sprint Tasks

- [ ] Install dependencies
- [ ] Create configuration loader
- [ ] Implement Frame Extractor
- [ ] Implement Face Detector
- [ ] Verify pipeline execution

---

# Notes

Use this document as the primary project tracker.

Update the checklist after completing each milestone.

Every completed milestone should be accompanied by:

- Updated documentation
- Experiment log (if applicable)
- Git commit
- Tag/release (optional)
