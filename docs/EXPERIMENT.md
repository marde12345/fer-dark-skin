# Experiment Log

This document records every experiment conducted during the development of the FER Dataset Generation Pipeline.

---

# Experiment Template

## Experiment ID

EXP-001

---

## Date

YYYY-MM-DD

---

## Objective

Example

Evaluate the effect of frame extraction rate on the number of detected faces.

---

## Configuration

| Parameter | Value |
|------------|------|
| FPS | 2 |
| Detection Confidence | 0.7 |
| Blur Threshold | 80 |
| Face Size | 120 px |

---

## Input

| Item | Value |
|------|-------|
| Video | pesta_babi.mp4 |
| Resolution | 1920×1080 |
| Duration | 96 min |

---

## Result

| Metric | Value |
|---------|------|
| Frames | |
| Faces Detected | |
| Faces Filtered | |
| Final Dataset | |

---

## Observation

Write observations here.

Example

- Many false detections occurred in low lighting.
- Increasing FPS generated redundant samples.
- Blur filtering removed approximately 12% of detected faces.

---

## Conclusion

Summarize findings.

---

# Experiment History

| ID | Objective | Status |
|----|-----------|--------|
| EXP-001 | FPS Evaluation | Planned |
| EXP-002 | Detection Confidence | Planned |
| EXP-003 | Blur Threshold | Planned |
| EXP-004 | FER Confidence Threshold | Planned |