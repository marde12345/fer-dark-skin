# Phase 0 — Dataset / Pipeline Foundation

## Status

DONE (for the pilot-scale 645-crop pool). The "full dataset" scope (~600+ crops from the uncapped ~96-minute source video) is NOT STARTED — current crops come from a capped, pilot-scale extraction.

## Objective

Produce raw frames, detected faces, CLAHE-preprocessed crops, and pseudo-labels (AI model outputs) that feed the human annotation pilot and, eventually, the full Papuan V2 dataset.

## Current State

- Source video: `data/raw/videos/pesta_babi.mp4`, reused unmodified from the legacy pipeline (`FrameExtractor`, `FaceDetector` classes in `src/fer_dataset/pipeline/`).
- Extraction run as **EXP-PAP-001**, capped at `max_frames=250` (debug mode), fps target 2.0 → 250 frames sampled → **645 faces detected** → **645 CLAHE crops** written.
- Outputs: `data/papuan_v2/faces/` (645 raw crops), `data/papuan_v2/clahe/` (645 CLAHE crops, same filenames), `data/papuan_v2/raw/source_video_manifest.json` (video SHA-256, fps, frame_interval, code provenance, timestamp).
- CLAHE module: `src/fer_dataset/shared/clahe.py` (Strategy B, params `clip_min=1.5, clip_max=3.5, l_min=60, l_max=220, tileGridSize=[8,8]`), tested by `tests/test_papuan_clahe.py` (passes).
- A 150-image deterministic subsample (seed=42) of the 645 CLAHE crops was taken for the pilot (**EXP-PAP-002**) — see `experiments/EXP-PAP-004/pilot_manifest.csv`. This is pilot scope, not full-dataset scope.
- Pseudo-labeling / AI-candidate predictions (**EXP-PAP-003**) were run on the 150-image pilot subset only, not the full 645-crop pool: HSEmotion (`hsemotion_clahe`, 150/150 ok) and ArcFace+LogisticRegression (`arcface_lr_clahe`, 150/150 ok after a fix — see Known Issues). Full-pool (645-crop) AI prediction has NOT been generated; `run_ai_predictions.py` is already parameterized for this but has not been invoked against `data/papuan_v2/clahe/`.
- Broader evaluation/model-training infrastructure (legacy, pre-dates papuan_v2) exists at repo root: `tools/extract_arcface_embeddings.py`, `tools/train_arcface_classifier.py` (trained the LR classifier reused by EXP-PAP-003, on legacy `manual_labels_export.csv`, **not** on any Papuan V2 data), `tools/evaluate_arcface_vs_hsemotion.py`, `tools/analyze_arcface_errors.py`.

## Evidence

- `tools/papuan_v2/build_pilot_source.py` (EXP-PAP-001 code)
- `tools/papuan_v2/sample_pilot.py`, `tools/papuan_v2/init_human_labels_template.py` (EXP-PAP-002 code)
- `tools/papuan_v2/run_ai_predictions.py` (EXP-PAP-003 code)
- `data/papuan_v2/raw/source_video_manifest.json`
- `experiments/EXP-PAP-004/pilot_manifest.csv` (151 lines = 150 rows + header)
- `experiments/EXP-PAP-004/ai_predictions.csv` (301 lines = 300 rows = 150 × 2 models)
- `experiments/EXP-PAP-004/metadata.json` (`ai_models` block: both candidates, 150/150 ok)
- `docs/EXPERIMENT.md` lines 457–560 (EXP-PAP-001/002/003 narrative entries)
- `src/fer_dataset/shared/clahe.py`, `tests/test_papuan_clahe.py`

## Completed

- Frame extraction, face detection, CLAHE preprocessing for the 645-crop pilot-scale pool.
- Deterministic 150-image pilot subsample with full provenance (seed, source paths, timestamps).
- AI candidate predictions (HSEmotion, ArcFace+LR) on the 150-image pilot subset, with a documented bugfix for the ArcFace embedding path (see Known Issues).
- Reproducibility metadata recorded at each stage (manifests, seeds, git commit hash at pilot start, dependency versions).

## In Progress

- Nothing actively in progress at the Phase 0 level; the pilot-scale foundation is frozen pending the human-labeling blocker downstream (Phase 2).

## Blockers

- None internal to Phase 0 itself. Full-dataset-scope extraction (uncapped video) is explicitly deferred, pending a scope decision (see Known Issues).

## Known Issues

- **Dataset size ambiguity, unresolved.** The 645 crops come from a capped extraction (`max_frames=250` out of a much longer source video). Whether "the full Papuan V2 dataset" means these same 645 crops or requires re-running EXP-PAP-001 without the cap is an open decision, explicitly flagged in `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §1.4/§11.3. This has not been decided or actioned.
- **ArcFace embedding bug, fixed but worth noting for audit trail**: an earlier implementation re-ran face detection on the pilot crop to get landmarks, which failed on 50/150 (33%) images. The fix (direct `ArcFaceONNX.get_feat()`, no detection) resolved this to 150/150, but introduces a documented distributional caveat (classifier trained on aligned embeddings; inference path skips alignment). This is stated explicitly in `metadata.json`'s `superseded_result` and `caveat` fields — not hidden, but also not resolved/re-validated against the training distribution.
- Full-pool (645-image) AI predictions do not yet exist — only the 150-image pilot subset has predictions.

## Outputs / Artifacts

- `data/papuan_v2/faces/` (645 images)
- `data/papuan_v2/clahe/` (645 images)
- `data/papuan_v2/pilot/images/` (150 images, CLAHE)
- `data/papuan_v2/raw/source_video_manifest.json`
- `experiments/EXP-PAP-004/pilot_manifest.csv`
- `experiments/EXP-PAP-004/ai_predictions.csv`

## Methodology Notes

CLAHE-only input is used for AI prediction and pilot labeling, per supervisor requirement ("AI-assisted annotation input must be CLAHE-preprocessed"). Original (non-CLAHE) crops are preserved in `data/papuan_v2/faces/` for a future Original-vs-CLAHE comparison (flagged as a future experiment "E3" in the proposal docs), but that comparison has not been run.

## Next Actions

- Decide dataset-size scope (keep 645 vs re-extract full video) before any `EXP-PAP-010`-series full-manifest work begins.
- If full-pool AI prediction is desired, run `run_ai_predictions.py` against `data/papuan_v2/clahe/` with the `--models` flag once EXP-PAP-004's assistant selection is made (currently blocked — see Phase 2 report).
