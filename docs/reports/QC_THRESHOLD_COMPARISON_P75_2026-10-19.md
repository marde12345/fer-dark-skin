# QC Threshold Comparison — Frozen v1 vs. P75-Blur Proposal

**Date:** 2026-10-19
**Status:** PROPOSAL ONLY — not approved, not adopted. The frozen QC v1 manifest, thresholds, and the final delivery package (`delivery/papuan_v2_final_2026-10-19/`) are unmodified by this analysis.

Source data: `docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv` (645 rows, real computed `qc_blur_variance`/`qc_width`/`qc_height` per sample). Compared against: `docs/reports/frozen_candidate_v1_2026-10-19/frozen_candidate_manifest.csv` (231 rows, `APPROVED_QC_V1`).

## 1. Exact P75 value

Computed directly from the 645-row `qc_blur_variance` column (pandas `.quantile(0.75)`, linear interpolation, not estimated from the median):

**P75 = 325.3481**

(For reference: the frozen v1 threshold was blur-variance > 75, a fixed round number chosen from visual contact-sheet review — not a percentile. 325.35 is roughly the 4.3x-stricter cutoff compared to 75.)

## 2. Candidate configuration: blur-variance > 325.3481 AND min(width,height) >= 60px

| Filter | Count passing | % of 645 |
|---|---|---|
| Blur-variance > P75 (325.3481) alone | 161 | 24.96% |
| min-dimension >= 60px alone | 372 | 57.67% |
| **Both (P75 proposal)** | **70** | **10.85%** |

## 3. Comparison against frozen QC v1 (231 samples, 35.81% of 645)

| | Count |
|---|---|
| Frozen v1 total | 231 |
| P75-proposal total | 70 |
| Retained in both (intersection) | 70 |
| Removed from v1 (in v1, not in P75 set) | 161 |
| Newly added by P75 (in P75 set, not in v1) | 0 |

The P75-blur set is a **strict subset** of the frozen v1 set — every sample that passes the stricter blur threshold also already passed v1's looser one (expected, since min-dimension is unchanged and blur>325.35 implies blur>75). No new samples are introduced.

**Net effect of switching to P75:** 161/231 (69.7%) of the currently-approved candidates would be dropped, retaining only 70/231 (30.3%) of the v1 set, i.e. 70/645 (10.85%) of the full dataset.

## 4. Distribution of the retained 70 samples (P75 config)

**Blur variance** (n=70): min 326.85, p25 408.70, median 538.33, p75 719.96, max 1080.78, mean 578.82, std 203.33 — all comfortably above the 325.35 cutoff by construction; no borderline cases near the threshold remain since this is the top blur quartile of the whole dataset.

**Min-dimension (px)** (n=70): min 60.0 (floor, unchanged constraint), p25 70.0, median 94.0, p75 140.75, max 248.0, mean 111.2, std 52.6.

## 5. Interpretation

- P75-on-blur is a *data-relative* threshold (always keeps exactly the sharpest quartile of whatever distribution exists) rather than the v1 threshold's *visually-grounded absolute* cutoff (chosen by inspecting contact sheets to find where eyebrow/eye/mouth legibility actually degrades, landing at 75). The two are not interchangeable: P75 was not chosen with reference to landmark legibility, it only guarantees relative sharpness within this dataset.
- 10.85% of 645 (70 samples) is well short of both the original ~250 target and the already-approved 231. This proposal is far stricter than necessary based on the visual evidence that supported v1 (which found blur>75 already screens out the crops where eyebrow/eye/mouth regions become illegible — see `docs/reports/qc_pilot_2026-10-19/QC_THRESHOLD_RECOMMENDATION.md`).
- No visual re-inspection of the newly-stricter cutoff was performed in this analysis — it is a pure numerical comparison, not a re-validated QC pilot. If P75 were to be considered seriously, it would need the same contact-sheet visual justification that v1 received, not just a statistical percentile.

## 6. Recommendation

**Do not adopt.** The existing frozen v1 threshold (blur > 75, min-dim >= 60) remains the only visually-validated, approved QC configuration. This P75 comparison is provided purely as a requested numerical "what if" and is not a recommendation to change course — it would discard 161 already-approved, already-processed samples (standardized images, landmarks, manifests) for no demonstrated quality benefit beyond what v1 already secures.

## 7. What was not touched

- `docs/reports/frozen_candidate_v1_2026-10-19/frozen_candidate_manifest.csv` — unmodified.
- `docs/reports/frozen_candidate_v1_2026-10-19/FREEZE_RECORD.md` — unmodified.
- `delivery/papuan_v2_final_2026-10-19/` — unmodified.
- No new candidate-selection script run with the P75 threshold was persisted as an "official" output; all numbers above were computed directly against the existing manifest for this comparison only.
