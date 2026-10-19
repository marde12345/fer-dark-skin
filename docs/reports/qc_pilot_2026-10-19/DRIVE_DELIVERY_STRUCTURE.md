# Proposed Drive Delivery Structure — papuan_v2 (2026-10-19)

**Design document only.** No PDF/xlsx is created and no files are copied
into this structure here — this proposes the folder layout and maps each
folder to existing artifacts (by path) vs. artifacts still to be produced.

```
papuan_v2_delivery/
  00_README.pdf
  01_Dataset_Overview.xlsx
  02_Images/
    original/
    clahe/
  03_Landmarks/
    initial/
    reviewed/
  04_Labels_and_Manifest/
  05_Quality_Report/
```

## 00_README.pdf

**Status: needs to be created.** Supervisor-facing, plain English, 1-2
pages. Should summarize: what papuan_v2 is, how many videos/frames/faces,
that `person_id`/identity tracking is not yet implemented
(`NOT_AVAILABLE` dataset-wide — see §7.3 of
`docs/reports/PAPUAN_V2_STANDARDIZATION_AUDIT_2026-10-19.md`), that QC
threshold is a pending recommendation not an approved cut
(`docs/reports/qc_pilot_2026-10-19/QC_THRESHOLD_RECOMMENDATION.md`), and
where to find more detail (pointers into `05_Quality_Report/`). Source
material to draw the plain-English summary from already exists in
`docs/reports/PAPUAN_V2_CURRENT_STATE.md` and
`docs/reports/extraction_audit_2026-10-19/EXTRACTION_METHODOLOGY_REPORT.md`,
but the PDF itself does not exist yet.

## 01_Dataset_Overview.xlsx

**Status: needs to be created.** Should tabulate: total source videos,
total sampled frames, total face crops (645), candidate count under the
recommended-pending threshold (231), breakdown by expression label status,
landmark status, and QC stratum. The underlying numbers already exist in
`docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv` and
`docs/reports/qc_pilot_2026-10-19/candidate_samples.csv` — this is a
spreadsheet summary/pivot of data that is already computed, not new
analysis. Still needs to be built as an actual .xlsx.

## 02_Images/

**Status: data exists on disk, not yet packaged into this structure.**

- `original/` — would be populated from `data/papuan_v2/faces/` (645 JPEGs,
  confirmed present on disk, gitignored). Not copied here; this folder
  structure is a proposal only.
- `clahe/` — would be populated from `data/papuan_v2/clahe/` (645 JPEGs,
  CLAHE-enhanced versions, 1:1 with `original/` — `has_clahe == True` for
  all 645 rows per the manifest).

Recommend including only the 231 (or whatever final-approved count)
candidate images, not all 645, unless the supervisor wants the full
pre-QC set for reference — flag this as an open question for sign-off.

## 03_Landmarks/

**Status: partially exists, incomplete.**

- `initial/` — AI-initialized landmark JSON files. Per the manifest, 40
  samples dataset-wide (14 among the 231 candidates) have
  `landmark_status == ai_initialized_unreviewed`; the underlying files live
  under `experiments/EXP-PAP-005/` (referenced by
  `landmark_initial_path` in the manifest for samples that have one).
  Needs to be filtered/copied into this subfolder, not yet done.
- `reviewed/` — human-reviewed landmarks. 64 samples dataset-wide (26 among
  the 231 candidates) have `landmark_status == reviewed`
  (`landmark_reviewed_path` in the manifest). Also not yet copied into this
  structure.
- The majority of candidates (191/231, see
  `docs/reports/qc_pilot_2026-10-19/ANNOTATION_BACKLOG.md`) have no
  landmarks at all yet — this folder will be sparse until that backlog is
  worked.

## 04_Labels_and_Manifest/

**Status: exists, needs consolidation into this folder.**

- Sample manifest: `docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv`
  (645 rows, already produced).
- Extraction manifest: `docs/reports/extraction_audit_2026-10-19/frame_level_extraction_manifest.csv`
  (250 rows, already produced).
- Person registry: **does not exist** — would need to explicitly state that
  `person_id` is `NOT_AVAILABLE` for all rows and that no identity-tracking
  stage has run (see `CANDIDATE_SELECTION_PLAN.md`'s proposed future
  tracking/ArcFace/human-review stage). A placeholder registry file noting
  this gap should be authored, not fabricated with invented IDs.
- Expression labels: `experiments/EXP-PAP-004/human_labels.csv` and
  `experiments/EXP-PAP-004/label_studio_export.csv` already exist;
  150/645 samples dataset-wide have `expression_label_status ==
  labeled_single_annotator` (52/231 among candidates, per
  `ANNOTATION_BACKLOG.md`).
- Annotation status: `annotation_review_status` column already present in
  `per_face_sample_manifest.csv`; could also surface
  `docs/reports/qc_pilot_2026-10-19/annotation_backlog.csv` here directly
  as the current backlog snapshot.

## 05_Quality_Report/

**Status: produced by this QC pilot, ready to drop in as-is.**

- QC findings: `docs/reports/qc_pilot_2026-10-19/QC_THRESHOLD_RECOMMENDATION.md`
  (recommendation, explicitly not approved).
- Exclusion manifest: **does not exist yet** — once a threshold is actually
  approved, a manifest of excluded `sample_id`s with `qc_exclusion_reason`
  should be generated (the `qc_exclusion_reason` column already exists in
  `per_face_sample_manifest.csv`, currently all `NOT_AVAILABLE` pending
  approval; generating the real exclusion list is a follow-up step after
  sign-off, not done here).
- Contact sheet examples: `docs/reports/qc_pilot_2026-10-19/contact_sheets/`
  (25 PNGs) and `docs/reports/qc_pilot_2026-10-19/qc_pilot_strata_index.md`
  already exist and can be included directly or as a representative subset.
- Distribution tables: `docs/reports/extraction_audit_2026-10-19/qc_threshold_candidates.md`
  (re-verified accurate in this pilot) could also be included here.

## Open items before this structure can actually be assembled

1. Supervisor approval of a QC threshold (currently only a recommendation).
2. Authoring `00_README.pdf` and `01_Dataset_Overview.xlsx` (no existing
   artifact is in those formats yet).
3. A decision on whether `02_Images/` ships all 645 or only approved
   candidates.
4. Generating the real exclusion manifest once a threshold is approved.
5. Working down the annotation backlog (expression labels, landmarks) to
   whatever completeness level the supervisor expects before delivery.
