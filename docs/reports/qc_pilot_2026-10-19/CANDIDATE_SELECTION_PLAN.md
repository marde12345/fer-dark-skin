# Candidate Selection Plan — papuan_v2 (2026-10-19)

Status: the resulting `candidate_samples.csv` is a **CANDIDATE list pending
QC threshold approval**, not a final/approved dataset. See
`QC_THRESHOLD_RECOMMENDATION.md` for the threshold rationale (Candidate C,
not yet approved).

## Selection logic

Implemented in `tools/papuan_v2/select_candidate_samples.py`. The threshold
is a CLI parameter, not hardcoded — no value is reverse-engineered to force
a count of ~250. Filters applied, in order:

1. `qc_blur_variance > <min_blur_variance>` (CLI arg)
2. `min(qc_width, qc_height) >= <min_dimension>` (CLI arg)
3. `has_clahe == True` — requires the original/CLAHE pair to exist on disk
   (trivially true for all 645 current rows, but enforced going forward)

## Run used for this report

```
uv run python3 tools/papuan_v2/select_candidate_samples.py \
  --manifest docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv \
  --out docs/reports/qc_pilot_2026-10-19/candidate_samples.csv \
  --min-blur-variance 75 \
  --min-dimension 60
```

Result: **231 of 645 samples retained (35.8%)**, written to
`candidate_samples.csv` with every row carrying
`candidate_status = CANDIDATE_PENDING_QC_THRESHOLD_APPROVAL` plus the exact
threshold values used, so the file is self-documenting about its provisional
status. This is 19 below the task brief's rough ~250 target — a secondary
observation, not the basis for the threshold (see
`QC_THRESHOLD_RECOMMENDATION.md` §3-4).

To re-run with a different (e.g. supervisor-approved) threshold, change only
the two `--min-*` flags; no code change is needed.

## Near-duplicate / redundancy handling (deliberately NOT a hard filter)

The task notes two things that look like redundancy but are not, plus one
real limitation:

- **Same `sampled_frame_index`, different `face_index_in_frame`**: these are
  different face detections within the same video frame (different people,
  or occasionally multiple detections of the same person side by side).
  **Not treated as redundant.** No filtering applied on this basis.

- **Same physical face reappearing across consecutive sampled frames**: this
  *would* be genuine redundancy (near-identical crop of the same person a
  fraction of a second apart), but there is no `person_id` or tracking
  anywhere in this dataset (`person_id` is `NOT_AVAILABLE` for all 645
  rows — confirmed in the manifest and consistent with the prior
  standardization audit's finding that no identity-tracking code exists in
  the codebase). **Without identity linkage, it is not possible to reliably
  tell whether two faces in adjacent sampled frames are the same person or
  not** — they could be the same person, a different person who happens to
  be in a similar position, or a different person entirely. Implementing a
  heuristic (e.g. "same frame-adjacency = assume duplicate") risks silently
  dropping legitimate distinct samples, so **no such filter is implemented**
  in `select_candidate_samples.py`.

- **Conservative informational note only**: among the 231 candidates, 87 of
  95 distinct `sampled_frame_index` values have at least one other candidate
  sample whose `sampled_frame_index` is adjacent (±1). This number is
  reported here purely as a diversity signal for a human reviewer — it is
  NOT used to drop any row, and should not be read as "87 frames are
  duplicates." It just flags where a reviewer doing manual diversity
  curation might want to look first.

## Future identity-tracking stage (scope only, not implemented)

Consistent with the earlier standardization audit's §7.3 recommendation,
if/when identity consistency becomes a hard requirement (e.g. for
per-person train/test splits, or to avoid the same individual appearing in
both train and test), a separate stage should be scoped and run
independently of this QC pilot:

1. **Tracking**: run a lightweight visual tracker (e.g. IoU/centroid
   tracking, or a stronger tracker if available) across each source video's
   frame sequence to link face detections into per-video tracklets.
2. **Re-identification for track breaks**: where tracking drops a face
   (occlusion, fast motion, frame gaps from the sampling interval), use
   ArcFace (or an equivalent face-embedding re-identification model) to
   propose links between tracklets that likely belong to the same person.
3. **Human review for uncertain merges**: any ArcFace-proposed link below a
   confidence threshold is queued for human review rather than
   auto-accepted, to avoid silently merging two different people.

This stage is out of scope for the current QC pilot and is not implemented
here — it is noted so it is not lost, and so `person_id` is understood as a
known, explicitly scoped gap rather than an oversight.
