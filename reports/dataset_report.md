# FER Dataset Report

## 1. Dataset Information

| Property | Value |
|----------|-------|
| Generated Date | 2026-08-14 23:49:58 |
| Total Images | 227 |
| Number of Classes | 6 |

---

## 2. Emotion Distribution

| Emotion | Count | Percentage |
|---------|------:|-----------:|
| Neutral | 88 | 38.77% |
| Fear | 83 | 36.56% |
| Anger | 41 | 18.06% |
| Sadness | 7 | 3.08% |
| Happiness | 5 | 2.20% |
| Surprise | 3 | 1.32% |

> Visualization will be added in a future version.

---

## 3. Confidence Statistics

| Metric | Value |
|--------|------:|
| Mean | 0.4557 |
| Median | 0.4057 |
| Std | 0.1703 |
| Min | 0.1957 |
| Max | 0.8874 |

> Visualization will be added in a future version.

---

## 4. Confidence per Emotion

| Emotion | Mean Confidence | Std |
|---------|----------------:|----:|
| Anger | 0.5925 | 0.1913 |
| Fear | 0.3712 | 0.1003 |
| Happiness | 0.4573 | 0.1839 |
| Neutral | 0.4764 | 0.1706 |
| Sadness | 0.4510 | 0.1434 |
| Surprise | 0.3259 | 0.1228 |

> Visualization will be added in a future version.

---

## 5. Dataset Characteristics

| Characteristic | Value |
|---------------|-------|
| Total Images | 227 |
| Number of Classes | 6 |
| Largest Class | Neutral |
| Smallest Class | Surprise |
| Average Confidence | 0.4557 |

---

## 6. Annotation Format

| Column | Description |
|--------|-------------|
| filename | Image filename |
| label | Predicted emotion label |
| confidence | Softmax confidence score |

---

## 7. Limitations

- Emotion labels are generated automatically using a pretrained model.
- No manual verification has been performed.
- Dataset quality depends on face detection and emotion classification accuracy.
- Class distribution reflects the source video.

---

## 8. Conclusion

This dataset contains **227** facial images covering **6** emotion classes. The annotations were generated automatically using a pretrained facial emotion recognition model.
