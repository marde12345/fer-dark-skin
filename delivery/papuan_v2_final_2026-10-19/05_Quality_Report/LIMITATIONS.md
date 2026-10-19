# Known Limitations — Papuan V2 FER Dataset, Final Delivery (2026-10-19)

This file consolidates every known gap in this delivery package. None of
these are hidden elsewhere — each is also stated in the source report it
cites. Read this before using the dataset for training or evaluation.

## 1. Bounding boxes were never persisted

`bbox_x/y/w/h` is `NOT_AVAILABLE` for all 231 samples (and all 645 in the
full extraction set). The face-detection stage crops and writes the padded
JPEG directly to disk without saving the original detector bounding box
(`face_detector.py:62-90`). Only the final crop dimensions are available.
See `docs/reports/extraction_audit_2026-10-19/EXTRACTION_METHODOLOGY_REPORT.md`
for the full methodology trace. This is a structural limitation of the
existing pipeline, not something this delivery could recover without
re-running face detection, which was explicitly out of scope.

## 2. person_id is not a verified identity

No cross-frame identity tracking has been run at dataset scale. All 231
samples default to `person_id = "unknown"`. A small, separate 31-crop pilot
(`docs/reports/identity_pilot_2026-10-19/`) tested ArcFace embedding
similarity between temporally-adjacent frames (sampled_frame_index 8-12
only) and found:

- **13 TENTATIVE_MATCH pairs** (similarity >= 0.5, unvalidated threshold).
  11 of the 231 delivered samples are involved in at least one such pair
  (either side). These get `person_id = "needs_review"`, never a confident
  identity.
- **2 NEEDS_HUMAN_REVIEW pairs** (similarity in the ambiguous 0.35-0.5
  band): `frame_000010_face01` vs `frame_000011_face04` (0.4584), and
  `frame_000011_face02` vs `frame_000012_face09` (0.3737). No human
  reviewer was available at delivery time. Both pairs are left explicitly
  **unresolved** in `identity_note` — they are not silently converted into
  either a match or a non-match.
- The 0.5 similarity threshold itself was chosen as a starting point for
  the pilot only and has **not been validated** against any human-labeled
  ground truth, and has **not been tested at full-dataset scale** (only 31
  of 645 crops, 5 consecutive sampled frames).

`person_id = "unknown"` means "never assessed." `person_id =
"needs_review"` means "weakly assessed via an unvalidated pilot method,
unconfirmed." Neither should be read as a verified identity.

## 3. Non-face detections found in the identity pilot (pilot subset only)

The 31-crop identity pilot found that InsightFace's own face re-detection
could not find a face at all in 6 of the 31 crops — i.e. some upstream
face-detector outputs are not faces (a cap/logo and a hand were visually
confirmed; see `IDENTITY_PILOT_REPORT.md` lines 125-132). Of those 6, 5 are
individually named in the pilot report
(`frame_000008_face03`, `frame_000009_face03`, `frame_000010_face06`,
`frame_000010_face07`, `frame_000011_face07`); the report's prose mentions
"and one more" without naming it, so that 6th crop cannot be honestly
attributed to a specific `sample_id` from the artifacts available here
without re-running the pilot, which was out of scope for this delivery.

Of the 5 named, **1 falls within the 231 delivered samples**
(`frame_000011_face07`) and is flagged in `identity_note` and
`other_notes` in the manifests. This check was **only performed on the
31-crop pilot subset** (sampled_frame_index 8-12) — it has **not** been
checked across the full 231 or the full 645-crop dataset. Other non-face
detections may exist undetected outside that subset.

## 4. Landmark review is incomplete

- All 231 samples have **initial** 42-point landmark predictions (40 reused
  from prior InsightFace `landmark_3d_68` runs, 191 newly generated with
  the same model/method on the original, non-standardized crops).
- Only **26 of 231** samples have human-reviewed (CVAT) landmarks. The
  remaining **205 of 231** have `landmark_status = pending_landmark_review`
  — initial AI predictions only, not yet human-corrected.
- Even within reviewed samples, the project's own calibration-batch
  analysis found that roughly half of one 11-image reviewed batch showed a
  bit-identical rigid whole-skeleton translation rather than fine-grained
  per-point correction (see
  `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md`) — "reviewed"
  does not uniformly mean "individually judged per point."

## 5. Expression labels are incomplete and single-annotator only

- **52 of 231** samples have an expression label (`expression_label_status
  = complete`); **179 of 231** have none (`pending_label`).
- Every existing label comes from a single annotator
  (`mardefasma123up@gmail.com`). The dataset's own dual-annotator design
  (Annotator A / Annotator B) has **never reached inter-annotator
  agreement for any sample dataset-wide** — Annotator B has 0/75
  completions. `expression_label_status = complete` in this package means
  "a label value exists," not "cross-verified by two annotators."

## 6. QC threshold is a pilot-derived heuristic, not a validated classifier

The `qc_blur_variance > 75` and `min(width,height) >= 60` thresholds that
produced these 231 candidates from 645 extracted crops come from a small
visual pilot (see `QC_THRESHOLD_RECOMMENDATION.md` in this folder), not a
large-scale validated quality classifier. Treat the 231/645 split as a
reasonable first-pass filter, not a guarantee that every included image is
usable or every excluded image is unusable.

## Summary of real completion counts (231 delivered samples)

| Aspect | Complete | Pending |
|---|---|---|
| Image standardization (224x224, both variants) | 231 / 231 | 0 |
| Initial landmarks (42-point) | 231 / 231 | 0 |
| Reviewed landmarks (42-point) | 26 / 231 | 205 |
| Expression label (single annotator) | 52 / 231 | 179 |
| person_id (dataset-wide tracking) | 0 / 231 | 231 (by design — see §2) |
| Identity pilot flags (needs_review / non-face) | 12 flagged | n/a — informational only |
