# QC Threshold Candidates (papuan_v2, 2026-10-19)

Descriptive distribution only. No threshold has been supervisor-validated; `qc_status` in `per_face_sample_manifest.csv` is left as `PENDING_THRESHOLD` for all rows. This file exists to let a human pick a threshold later.

Total crops analyzed: 645 / 645


## Blur variance (cv2.Laplacian(gray, CV_64F).var()) percentiles

| Percentile | Value |
|---|---|
| p1 | 2.89 |
| p5 | 16.85 |
| p10 | 31.88 |
| p25 | 60.61 |
| p50 | 151.09 |
| p75 | 325.35 |
| p90 | 600.89 |
| p95 | 752.86 |
| p99 | 1071.73 |

## Width (px) percentiles

| Percentile | Value |
|---|---|
| p1 | 24.4 |
| p5 | 36.0 |
| p10 | 42.0 |
| p25 | 51.0 |
| p50 | 67.0 |
| p75 | 120.0 |
| p90 | 248.0 |
| p95 | 337.0 |
| p99 | 641.4 |

## Height (px) percentiles

| Percentile | Value |
|---|---|
| p1 | 31.0 |
| p5 | 44.0 |
| p10 | 52.0 |
| p25 | 66.0 |
| p50 | 91.0 |
| p75 | 148.0 |
| p90 | 311.0 |
| p95 | 433.2 |
| p99 | 860.5 |

## min(width,height) (px) percentiles

| Percentile | Value |
|---|---|
| p1 | 24.4 |
| p5 | 36.0 |
| p10 | 42.0 |
| p25 | 51.0 |
| p50 | 67.0 |
| p75 | 120.0 |
| p90 | 244.0 |
| p95 | 336.8 |
| p99 | 641.4 |

## Illustrative candidate thresholds (NOT a decision — for discussion only)

| Candidate rule | Samples passing | % of 645 |
|---|---|---|
| blur_variance > p10 AND min(w,h) >= 32px | 558 | 86.5% |
| blur_variance > p25 AND min(w,h) >= 48px | 367 | 56.9% |
| blur_variance > p50 AND min(w,h) >= 64px | 140 | 21.7% |
| blur_variance > p25 only (no size floor) | 483 | 74.9% |
| min(w,h) >= 48px only (no blur floor) | 514 | 79.7% |
