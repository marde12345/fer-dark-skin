# Papuan V2 Review Package — 2026-10-19

**NOTHING IN THIS PACKAGE IS FINAL OR APPROVED.** This is a human-readable
decision package assembled from three prior, already-committed phases of
work (audit, extraction, QC pilot). It reviews, verifies, and organizes
those outputs for supervisor review — it does not redo the audits, rerun
extraction/detection, perform full-scale annotation, split the dataset, or
train any model.

## 1. Dataset overview — verified counts

All counts below were recomputed directly against the current
`docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv`
(645 rows) in this phase, not copied blindly from prior docs:

| Metric | Count | Verified how |
|---|---|---|
| Total face crops | 645 | row count of per-face manifest |
| Frames sampled from source video | 250 | `source_video_manifest.json` + frame-level manifest |
| QC candidates (blur_variance>75 AND min_dim>=60) | **231** | re-ran the filter against the live manifest; matches `candidate_samples.csv` exactly, 0 discrepancy — see `QC_DECISION_SUMMARY.md` |
| Expression-labeled (single annotator) | 150/645 | `expression_label_status == labeled_single_annotator` |
| Landmarks reviewed (CVAT) | 64/645 | `landmark_status == reviewed` |
| Landmarks AI-initialized but unreviewed | 40/645 | `landmark_status == ai_initialized_unreviewed` |
| Landmarks not yet initialized | 541/645 | `landmark_status == not_initialized` |
| person_id available | 0/645 (`NOT_AVAILABLE` for all rows) | see identity section below |

## 2. Package contents

This package (`docs/reports/review_package_2026-10-19/`):

- `README.md` — this file.
- `QC_DECISION_SUMMARY.md` — plain-English explanation of the QC metrics,
  why the proposed threshold is defensible, and the ~250-target gap-closing
  finding. Threshold status: **pending approval**, not adopted.
- `IDENTITY_TRACKING_NEXT_STEP.md` — proposed smallest-next-step pilot for
  identity tracking (not implemented), including what was found when
  checking for existing ArcFace embedding artifacts.
- `BACKUP_AND_ROLLBACK_PROCEDURE.md` — source video/data locations, the
  verified SHA-256, a proposed (not performed) backup step, and a
  legacy/papuan_v2 separation check.
- `example_crops/` — 9 real crop files (3 accepted, 3 borderline, 3
  excluded), copied (not moved) from `data/papuan_v2/faces/`, see §5 below.

Prior-phase documents this package builds on (not duplicated here):

- `docs/reports/PAPUAN_V2_STANDARDIZATION_AUDIT_2026-10-19.md` — full
  architecture/traceability audit, source of the landmark schema restated
  below.
- `docs/reports/extraction_audit_2026-10-19/` — `frame_level_extraction_manifest.csv`
  (250 rows), `per_face_sample_manifest.csv` (645 rows, real QC values),
  `EXTRACTION_METHODOLOGY_REPORT.md`.
- `docs/reports/qc_pilot_2026-10-19/` — `QC_THRESHOLD_RECOMMENDATION.md`
  (contact-sheet visual evidence behind the proposed threshold),
  `CANDIDATE_SELECTION_PLAN.md`, `candidate_samples.csv` (231 rows),
  `ANNOTATION_BACKLOG.md` + `annotation_backlog.csv` (231 rows),
  `DRIVE_DELIVERY_STRUCTURE.md`, `contact_sheets/` (25 sheets),
  `tools/papuan_v2/select_candidate_samples.py`.

## 3. Landmark schema (42-point subset) — restated from the standardization audit

Full production schema is the 68-point iBUG-300W/dlib convention (InsightFace
`landmark_3d_68`, x/y only). The target 42-point subset for eyebrow/eye/mouth
annotation, confirmed in `PAPUAN_V2_STANDARDIZATION_AUDIT_2026-10-19.md` §4
and not re-derived here:

| Region | Source indices (of 68) | Count |
|---|---|---|
| Right eyebrow | 17–21 | 5 |
| Left eyebrow | 22–26 | 5 |
| Right eye | 36–41 | 6 |
| Left eye | 42–47 | 6 |
| Mouth (outer+inner) | 48–67 | 20 |
| **Total** | | **42** |

Jaw (0-16) and nose (27-35) are dropped, not renumbered — original 68-point
indices are recommended to be kept as a `source_index` field for
traceability. This is a pure column-selection filter; no reprediction
needed.

## 4. sample_id vs. person_id

- **`sample_id`** is filename-based and per-detection (e.g.
  `frame_000137_face02` = frame 137, 2nd detected face in that frame). It
  exists for all 645 rows and is stable/unique.
- **`person_id`** is `NOT_AVAILABLE` for all 645 rows, dataset-wide. No
  identity has been inferred, tracked, or assigned. **No person_id value
  should ever be invented or backfilled without the explicit human-review
  step described in `IDENTITY_TRACKING_NEXT_STEP.md`.**

## 5. Example crops (`example_crops/`)

Copied directly from `data/papuan_v2/faces/` (source files untouched):

| File | sample_id | qc_blur_variance | min(w,h) | Category reason |
|---|---|---|---|---|
| `accepted_frame_000020_face04.jpg` | frame_000020_face04 | 1080.8 | 70 | well above both thresholds |
| `accepted_frame_000018_face02.jpg` | frame_000018_face02 | 1058.4 | 77 | well above both thresholds |
| `accepted_frame_000019_face04.jpg` | frame_000019_face04 | 953.9 | 80 | well above both thresholds |
| `borderline_blurband_frame_000137_face02.jpg` | frame_000137_face02 | 74.2 | 212 | just below blur cutoff (75); visually legible |
| `borderline_blurband_frame_000103_face01.jpg` | frame_000103_face01 | 73.7 | 179 | just below blur cutoff; mouth occluded by foreground object |
| `borderline_dimband_frame_000054_face02.jpg` | frame_000054_face02 | 1122.5 | 56 | just below size cutoff (60px); partial/shadowed face |
| `excluded_frame_000217_face01.jpg` | frame_000217_face01 | 1.7 | 666 | large crop, but genuinely unusable motion blur |
| `excluded_frame_000221_face02.jpg` | frame_000221_face02 | 1.9 | 368 | same — large but unreadable |
| `excluded_frame_000216_face02.jpg` | frame_000216_face02 | 1.9 | 655 | same — large but unreadable |

See `QC_DECISION_SUMMARY.md` for the full narrow-band analysis these were
drawn from.

## 6. Manual annotation checklist — supervisor summary (231 QC candidates)

Recomputed directly against `docs/reports/qc_pilot_2026-10-19/annotation_backlog.csv`
(231 rows, matches the 231 QC candidates exactly):

| Item | Count (of 231) | Note |
|---|---|---|
| Missing expression label | 179 | `missing_expression_label == True` |
| Missing landmarks entirely | 191 | `missing_landmarks == True` |
| Landmarks pending review (AI-initialized, not yet CVAT-reviewed) | 14 | `landmarks_pending_review == True` |
| Uncertain identities | **231 (all)** | `identity_uncertain == True` for every row — expected, since `person_id` is `NOT_AVAILABLE` dataset-wide (§4); this is not a data-quality gap, it reflects that identity tracking has not been attempted yet |

These figures were independently recomputed from the CSV in this phase, not
copied from `ANNOTATION_BACKLOG.md`; no inconsistency was found between the
two.

## 7. What requires supervisor decision

- Approve, adjust, or reject the QC threshold (blur_variance>75,
  min_dim>=60, 231 candidates) — see `QC_DECISION_SUMMARY.md`.
- Decide whether to pursue the identity-tracking pilot proposed in
  `IDENTITY_TRACKING_NEXT_STEP.md`, and allocate time for the human review
  step it requires before any `person_id` is written.
- Decide whether/when to execute the backup step proposed in
  `BACKUP_AND_ROLLBACK_PROCEDURE.md` before any full-scale rerun.
- Decide whether the ~250-candidate target should flex down to ~231, or
  whether a full (not spot-check) contact-sheet review of the 51-sample
  blur band (50-75, min_dim>=60) should be commissioned.
- Decide on annotation prioritization among the 231 candidates given the
  backlog counts in §6 (179 missing expression labels, 191 missing
  landmarks).

## 8. Explicit statement

Nothing in this package — the QC threshold, the example crop categorization,
the identity-tracking proposal, or the backup procedure — is final or
approved. All figures were independently recomputed against current source
manifests during this phase; where a cached number from a prior phase was
confirmed to match, that is stated explicitly, and where a discrepancy would
have been found, it would have been reported rather than silently reused.
