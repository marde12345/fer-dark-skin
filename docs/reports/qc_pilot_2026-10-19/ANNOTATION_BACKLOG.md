# Annotation Backlog — papuan_v2 Candidate Samples (2026-10-19)

Scope: the 231 rows in `candidate_samples.csv` (Candidate C threshold,
pending QC approval — see `QC_THRESHOLD_RECOMMENDATION.md`). Per-row detail
in `annotation_backlog.csv`, derived directly from
`landmark_status`, `expression_label_status`, and `annotation_review_status`
in the manifest — no fields are guessed.

## Summary counts (of 231 candidates)

| Flag | Count | Basis |
|---|---|---|
| `missing_expression_label` | 179 | `expression_label_status == not_labeled` |
| `missing_landmarks` | 191 | `landmark_status == not_initialized` |
| `landmarks_pending_review` | 14 | `landmark_status == ai_initialized_unreviewed` |
| landmarks already reviewed (reference, not a backlog flag) | 26 | `landmark_status == reviewed` |
| `identity_uncertain` | 231 (all) | `person_id` is `NOT_AVAILABLE` for every row in the manifest — no identity tracking exists anywhere in this codebase, so identity cannot be asserted for any sample |

Sanity check: 191 (missing_landmarks) + 14 (pending_review) + 26 (reviewed)
= 231, accounting for every candidate row's landmark state exactly once.

## Other quality flags

`other_quality_flags` in the CSV marks, per row, whether a candidate falls
below the stricter Candidate D threshold from
`QC_THRESHOLD_RECOMMENDATION.md` (`blur_variance > 100`, `min_dim >= 64`),
purely as an informational marker for reviewers deciding between candidate
thresholds later — it does not remove any row from the backlog.

## Reading this backlog

- 179 of 231 candidates (77.5%) still need an expression label.
- 191 of 231 candidates (82.7%) have no landmarks at all yet; another 14
  (6.1%) have AI-initialized landmarks awaiting human review. Only 26
  (11.3%) are fully landmark-reviewed.
- All 231 candidates carry `identity_uncertain = True` by definition, since
  `person_id` is not available dataset-wide (see `CANDIDATE_SELECTION_PLAN.md`
  for the proposed future tracking/re-ID/human-review stage to resolve
  this if identity consistency becomes required).

This backlog is meant to size the remaining annotation work on the
candidate set, not to prioritize it — prioritization (e.g. which 179
missing-label samples to label first) is a separate decision for whoever
owns the annotation pipeline.
