# PAPUAN V2 — "v2" Candidate Pool — Status

**STATUS: UNREVIEWED. NOT FINALIZED. NOT APPROVED.**

## Partial video coverage (read this first)

This package was built from a single extraction run
(`tools/papuan_v2/run_extraction_v2.py --full --max-seconds 2400`) that was
terminated cleanly (SIGTERM) after ~46 real minutes because it exceeded its
intended 40-minute budget and would not finish the originally targeted
12,000 sampled frames at its observed throughput (~2.3-2.5 frames/sec).

It covers only source-video timestamps **0 to 277.8 seconds**, out of a
full video duration of **5763.36 seconds** — approximately **4.8%** of the
video. This is **NOT full-video coverage**. Do not treat counts or
proportions derived from this pool as representative of the full video.

## What this package is

A proposal-stage candidate pool of **668 face crops** (out of 3413 faces
detected in this partial window), selected by:
1. Size + blur QC (`qc_blur_variance > 75`, `min(w,h) >= 60`) — reused
   as-is from the already-validated v1 thresholds.
2. A new landmark-geometry frontality/visibility filter (Step 2 of this
   audit) layered on top.

See `docs/reports/extraction_v2_2026-10-19/CANDIDATE_SELECTION_REPORT_V2.md`
for the full methodology, funnel, visual validation, and dedup/identity
proposal.

## What this package is NOT

- NOT merged with, nor a replacement for, the existing 231-sample
  `frozen_candidate_v1_2026-10-19` pool. That pool is untouched.
- NOT reviewed by a human. `03_Landmarks/Reviewed/` is intentionally empty —
  only `03_Landmarks/Initial/` (AI-initialized, unreviewed landmarks)
  exists.
- NOT deduplicated or identity-resolved. Any adjacent-frame identity
  matches are PROPOSALS ONLY
  (`docs/reports/extraction_v2_2026-10-19/dedup_identity_proposal_v2.csv`);
  `person_id` remains `unknown` everywhere in this package.
- NOT a claim of annotation completeness or dataset finality of any kind.

## Folder layout (same convention as v1)

- `02_Images/Original/`, `02_Images/CLAHE/` — 224x224 letterboxed crops,
  668 each, `{sample_id}.jpg`.
- `03_Landmarks/Initial/` — 42-point (brows+eyes+mouth) AI-derived
  landmarks per candidate, transformed into the 224x224 letterboxed space.
- `03_Landmarks/Reviewed/` — empty (no human review has occurred).
- `04_Manifests/_standardization_transform_v2.csv` — per-sample
  scale/pad transform record.
