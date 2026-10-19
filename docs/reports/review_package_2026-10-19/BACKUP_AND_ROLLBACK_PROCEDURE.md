# Backup and Rollback Procedure — papuan_v2 (2026-10-19)

Status: **PROPOSAL ONLY.** No copy, backup, or rollback operation was
performed as part of this phase. Paths and hashes below were verified by
direct inspection, not assumed.

## Current artifact locations (verified to exist)

| Artifact | Path | Verified |
|---|---|---|
| Source video | `data/raw/videos/pesta_babi.mp4` | exists, 2.2 GB |
| Raw extraction outputs (faces, CLAHE, raw frames, pilot) | `data/papuan_v2/{faces,clahe,raw,pilot}/` | exists, 16 MB total |
| Extraction/QC manifests | `docs/reports/extraction_audit_2026-10-19/`, `docs/reports/qc_pilot_2026-10-19/` | exists |
| Source video manifest (provenance record) | `data/papuan_v2/raw/source_video_manifest.json` | exists |

## Source video integrity

`source_video_manifest.json` records:

```
sha256: de2ea92ac3da6c8572eef47f7b610a771f1e68f469acbe81571731faca156f0f
```

This was independently re-verified against the live file in this worktree
(`shasum -a 256 data/raw/videos/pesta_babi.mp4`) and **matches exactly**.
The source video on disk is confirmed unmodified since the recorded
extraction run (2026-09-19).

## Proposed backup step (not performed)

Before any large-scale rerun of extraction/detection (which would overwrite
or multiply the current 645-crop output):

1. Copy `data/raw/videos/pesta_babi.mp4` and the full `data/papuan_v2/`
   tree to an external or cloud location (e.g. a dedicated backup drive or
   cloud bucket outside the working repo/worktree).
2. Verify the copy by re-computing SHA-256 on the copied video file and
   confirming it still matches `de2ea92ac3da6c8572eef47f7b610a771f1e68f469acbe81571731faca156f0f`;
   for `data/papuan_v2/` (many small files), a recursive checksum manifest
   (e.g. `find data/papuan_v2 -type f -exec shasum -a 256 {} \;` on both
   source and copy, diffed) is the equivalent integrity check.
3. Keep the backup immutable (read-only / versioned) rather than a location
   that gets overwritten by future pipeline runs, so a rollback target
   always exists independent of the working tree.
4. Only after a verified backup exists should any full-scale (non-pilot,
   `debug_mode: false` / no `max_frames` cap) re-extraction run proceed.

This is a recommendation for the supervisor/engineering owner to schedule
and execute — it was not run as part of this review-package phase.

## Legacy vs. papuan_v2 separation — verified

Checked for legacy artifact directories that should never mix into the
papuan_v2 delivery tree (e.g. `data/legacy/`, `data/1408-1010-intermediate/`
or similar pre-papuan_v2 naming):

- `find . -maxdepth 3 -iname "*legacy*"` and a search for `*1408*1010*`
  under `data/` both returned **no matches** in this worktree.
- `data/` currently contains only `papuan_v2/` and `raw/` (the source video
  directory) — no other dataset-version directories are present.
- Cross-checked all 645 `original_path` values in
  `per_face_sample_manifest.csv`: **100% reference `data/papuan_v2/...`
  paths, zero reference any other tree.**

**Conclusion: no legacy/papuan_v2 cross-contamination exists in this
worktree.** This worktree does not currently contain a separate legacy data
directory to compare against — if one exists elsewhere (e.g. in the
original `FER-Dataset` working directory outside this isolated worktree),
that location was not in scope for this check and should be verified
separately before any package handoff that spans both.
