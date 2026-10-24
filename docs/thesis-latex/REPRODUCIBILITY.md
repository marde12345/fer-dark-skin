# Reproducibility Notes

## What Can Be Reproduced From This Repository Alone

- **HSEmotion and ArcFace inference** are deterministic given the same input images, since both models are pinned, pretrained, frozen weights never modified by this project (ONNX `enet_b0_8_best_vgaf`; InsightFace `buffalo_l`/`w600k_r50`). Re-running inference on the same crops will reproduce the same predictions, modulo library/runtime version drift (exact pinned versions not recorded in this pass — see TODO.md item 9).
- **The Logistic Regression classifier (EXP-007)** is reproducible given the same ArcFace embeddings and the recorded configuration: multinomial, L2-regularized, class-weighted, `StratifiedGroupKFold` 5-fold CV grouped by 3-frame temporal block, seed=42.
- **CLAHE preprocessing** is reproducible given its recorded parameters (LAB L-channel, adaptive clip limit 1.5–3.5 from weighted mean luminance, 8×8 tile grid).
- **Sampling seeds** for Papuan V2 pilot/overlap subsets are recorded (seed=42 for the 150-image pilot, seed=100 for the 75-image overlap subset, seed=200 for the 24-image CVAT pilot).

## What Cannot Be Reproduced From This Repository Alone

- **The underlying images** (frames, face crops, CLAHE crops) are excluded from version control (`.gitignore`, since commit `9b5d0ac`). Reproducing any reported number from scratch requires re-running the extraction pipeline against the same source video file, which is not itself committed to this repository either.
- **The 227→135 subset selection rule is now documented** (`research-audit/DATA_DISCREPANCIES.md` D-2: exclude 83 `Ambiguous` → 144, exclude 1 `Angry`/2 `Disgust` → 141, exclude 6 ArcFace alignment failures → 135), cross-corroborated between `docs/EXP-007_ARCFACE_EVALUATION.md` and `docs/ARCFACE_EXPERIMENT_DESIGN.md`. What remains unverified is the row-level identity of the 6 alignment-failure exclusions within the 141 label-eligible crops — the *rule* is resolved, the *exact row list* is not independently re-derived from the raw CSV in this pass.
- **Human annotation** (manual emotion labels, CVAT landmark review) is, by nature, not computationally reproducible — it is a one-time human judgment, recorded in `manual_labels_export.csv` and (pending) CVAT exports respectively.
- **Package/library/model-weight exact version numbers** were not independently re-extracted from `pyproject.toml`/`uv.lock` and cross-referenced against each experiment's execution date in this pass.
- **EXP-006's per-skin-tone breakdown cannot currently be reconciled with EXP-005's** (`research-audit/DATA_DISCREPANCIES.md` D-8) without access to both notebooks' underlying row-level data, which is not committed to this repository.

## Recommended Steps to Re-Verify a Reported Number

1. Identify the experiment ID from `research-audit/EXPERIMENT_REGISTRY.md`.
2. Locate its result artifact (CSV/JSON path) from the registry entry.
3. Open the corresponding CSV directly and confirm the value matches what is cited in `EVIDENCE_MAP.md` and the relevant thesis chapter.
4. If re-running from source images is required, confirm the source video and pipeline configuration (seed, frame-sampling rate, detector settings) match the registry entry before comparing new output to the recorded figure.
