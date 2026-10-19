# Identity Tracking — Proposed Next Step (2026-10-19)

Status: **PROPOSAL ONLY. Not implemented, not scheduled.** `person_id` is
`NOT_AVAILABLE` for all 645 rows in the manifest and must stay that way
until a human review step (not just an algorithm) signs off.

## What already exists (checked directly, not assumed)

A repo-wide search for ArcFace embedding artifacts was run
(`find . -iname "*arcface*"`, plus a check for `*.npy`/embedding files under
`data/papuan_v2/`). Findings:

- ArcFace **tooling** exists (`tools/extract_arcface_embeddings.py`,
  `tools/train_arcface_classifier.py`, `tools/evaluate_arcface_vs_hsemotion.py`,
  `tools/analyze_arcface_errors.py`) and has prior evaluation outputs under
  `reports/arcface_evaluation/` and `reports/arcface_error_analysis/`.
- These tools and prior reports belong to an **earlier, different**
  experiment (confusion-matrix/expression-classification work), not
  papuan_v2. `tools/extract_arcface_embeddings.py` contains no reference to
  `papuan_v2` or `data/papuan_v2/`.
- **No embedding artifact (`.npy`, `.json`, or similar) exists anywhere
  under `data/papuan_v2/` today.** Embeddings would have to be generated
  from scratch for papuan_v2's 645 face crops; nothing can be reused as-is.
- InsightFace (the `buffalo_l` bundle, already used for landmark detection
  in this pipeline — see `data/papuan_v2/raw/source_video_manifest.json`
  and the standardization audit) typically bundles an ArcFace recognition
  model in the same model pack, so adding embedding extraction would not
  require a new model family — but this is an opportunity noted for a
  future pilot, not something already wired up.

## Smallest practical next step (proposed)

A scoped pilot, not a full implementation:

1. Pick a short, visually-dense window of consecutive sampled frames (e.g.
   20-30 of the 250 sampled frames, chosen from a span with multiple faces
   per frame per the extraction manifest) rather than the full 645-crop set.
2. Run a simple **centroid/IoU tracker** across consecutive frames in that
   window using the existing `bbox_x/y/w/h` columns already in
   `per_face_sample_manifest.csv` (cheap, no model inference needed) to
   produce candidate track groupings.
3. In parallel, as a comparison, extract ArcFace embeddings for just that
   same small window's face crops and cluster by cosine similarity, to see
   whether appearance-based grouping agrees with the positional tracker.
4. Compare the two outputs by hand on that small window and report where
   they agree/disagree — this is the pilot's actual deliverable, not a
   working tracker.

## What tracking alone can and cannot resolve

- **Can**: group temporally-adjacent, unoccluded, non-re-entering faces
  within a short clip with reasonable confidence from bbox position alone;
  ArcFace similarity can additionally re-associate the same person across
  short gaps if appearance is stable.
- **Cannot**: resolve occlusion (a face leaving frame and an unrelated face
  entering at a similar position can be confused by IoU/centroid alone),
  re-entry after a long gap (a person leaving and returning later has no
  temporal continuity for a simple tracker to exploit), or scene structure
  (how many distinct people appear in the source video at all is unknown —
  nothing in the current manifests records a ground-truth person count).
  Both failure modes require a human to look at the clustering output and
  make a judgment call, especially given this is a real-world outdoor
  recording (`pesta_babi.mp4`) with multiple people, motion, and partial
  occlusion already visible in the QC contact sheets.

## Explicit constraint

No candidate identity — from a tracker, a clustering algorithm, or any
combination — should be written into `person_id` in any manifest until a
human has reviewed the ambiguous cases the pilot surfaces. Writing
unreviewed identities into the manifest would silently convert an
algorithmic guess into what looks like ground truth to anyone downstream.
