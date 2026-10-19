# Frozen QC Candidate Manifest — FREEZE_RECORD

**Freeze version:** `v1`
**Freeze timestamp:** 2026-10-19 (this session)
**Scope of this freeze:** QC-acceptance stage only.

## What this freeze is

A versioned, immutable snapshot of the already-approved QC candidate list
(`docs/reports/qc_pilot_2026-10-19/candidate_samples.csv`), with an added
`candidate_status` of `APPROVED_QC_V1` and `freeze_version` of `v1`. This
freeze exists so the pre-freeze candidate list (`candidate_samples.csv`)
remains untouched for audit, and so downstream work has a stable, versioned
reference point for "the 231 samples that passed this QC stage."

**This is NOT a final dataset freeze.** It only certifies that 231 of the
645 extracted face crops passed the blur/size QC threshold. Expression
labels, landmarks, and person identity are explicitly NOT part of what is
being frozen here and remain incomplete/pending (see Known Gaps below).

## QC configuration used

| Parameter | Value |
|---|---|
| `qc_blur_variance` threshold | `> 75` (exclusive) |
| `min(qc_width, qc_height)` threshold | `>= 60` (inclusive) |
| `has_clahe` requirement | `True` |

## Provenance

| Item | Value |
|---|---|
| Selection script | `tools/papuan_v2/select_candidate_samples.py` |
| Script SHA-256 at freeze time | `ff104757b1755f6f8e0427a8d8069e0fe2d143b608c9e99f115cc9be3a3d113a` |
| Source manifest | `docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv` |
| Source manifest row count | 645 |
| Git commit (parent, before this session's changes) | `770cc704e17551e27ced132bb70c55888d99312e` |
| Resulting frozen row count | 231 |

## Re-verification performed

Before freezing, `select_candidate_samples.py` was re-run fresh against the
current `per_face_sample_manifest.csv` with the same thresholds
(`--min-blur-variance 75 --min-dimension 60`). The output was diffed
byte-for-byte against the live `docs/reports/qc_pilot_2026-10-19/candidate_samples.csv`
and found **identical** (231 data rows + header, no drift). The source
manifest has not changed since the candidate list was produced.

Every `sample_id` in `frozen_candidate_manifest.csv` was checked against
`per_face_sample_manifest.csv` for `original_path` and `clahe_path`
existence on disk (`os.path.exists`, read-only check). Result: **0 missing
files out of 231 rows x 2 paths = 462 path checks.**

## Known gaps (explicitly NOT resolved by this freeze)

Per `docs/reports/qc_pilot_2026-10-19/annotation_backlog.csv` (231 rows,
one per candidate sample, re-verified this session):

- **179 / 231** rows have `missing_expression_label = True`
- **191 / 231** rows have `missing_landmarks = True`
- **14 / 231** rows have `landmarks_pending_review = True`

`person_id` is `NOT_AVAILABLE` for all rows dataset-wide (verified this
session against the live `per_face_sample_manifest.csv`) and is not
affected by this freeze. See `docs/reports/identity_pilot_2026-10-19/` for
a small, separate, non-authoritative identity-tracking pilot — its outputs
are explicitly not `person_id` and are not referenced by this freeze.

## Explicit non-scope statement

This freeze certifies QC-acceptance (blur + minimum dimension + CLAHE
pairing) only. It does not certify, assign, or imply completion of
expression labeling, landmark annotation, or person identity. Those remain
pending work tracked separately in `docs/reports/qc_pilot_2026-10-19/annotation_backlog.csv`
and must not be treated as resolved because this freeze exists.
