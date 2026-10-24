# Research Inventory

Canonical list of datasets, code modules, experiments, and annotation artifacts relevant to this thesis, as found in the repository. Status labels use the scale defined in `DATA_DISCREPANCIES.md` (Verified / Corroborated / Provisional / Unresolved / Unverifiable).

## Datasets

### D-LEGACY: Legacy Papuan Face-Crop Dataset

- **Version/name:** unversioned; referred to as the "legacy" or "original" dataset to distinguish it from Papuan V2.
- **Physical location:** `data/1408-1010-intermediate/` and related intermediate paths (not committed — see `.gitignore`, Stage 0 of `RESEARCH_TIMELINE.md`); summary statistics survive in `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv`.
- **Source/parent:** a single documentary film ("Pesta Babi," a Papuan pig-feast ceremony), 1920×1080, ~96 minutes, 144,084 frames at 25 fps (per `docs/EXPERIMENT.md` EXP-000).
- **Generation process:** debug-scale pipeline run (`debug.max_frames=100`) → frame extraction → InsightFace SCRFD face detection/cropping → 227 face crops → HSEmotion pseudo-labels (baseline) → manual human labels for all 227 (`manual_labels_export.csv`).
- **Sample count:** 227 face crops, manually labeled. Each record is one face crop from one sampled video frame — **not** independently verified to represent 227 distinct subjects (see `DATA_DICTIONARY.md`).
- **Label schema:** 7-class human taxonomy (Neutral 80, Ambiguous 83, Happy 34, Sad 12, Disgust 2, Fear 7, Surprise 8, Angry 1); HSEmotion's own 7-emotion pseudo-label vocabulary (Anger, Disgust, Fear, Happiness, Neutral, Sadness, Surprise) used separately for the pretrained baseline.
- **Intended purpose (at creation):** debug/smoke-test of the pipeline at small scale.
- **Actual observed usage:** became the dataset for the entire R1–R9 evaluation sequence (baseline accuracy, CLAHE ablation, ArcFace+LR comparison) — a scale-up or re-collection to a larger population was apparently never executed for this specific dataset line (superseded instead by Papuan V2, a separate collection).
- **Known limitations:** single annotator, no inter-rater check; structurally unusable 7-class taxonomy (Angry n=1, Disgust n=2) forcing a reduced 5-class evaluation; no data-provenance/consent documentation for the source film.
- **Evidence:** `docs/EXPERIMENT.md` (EXP-000, EXP-005), `docs/R7_5_CLASS_DECISION.md`, `reports/audit_summary_metrics.csv`.
- **Status:** **Verified** (sample count, label distribution, and generation process are corroborated across at least 3 independent documents and a raw CSV export).

### D-COMMON135: Common Evaluation Subset ($N=135$)

- **Version:** derived subset of D-LEGACY, 5-class taxonomy (Angry, Disgust excluded).
- **Physical location:** `reports/arcface_evaluation/*.csv`.
- **Source/parent:** D-LEGACY ($N=227$). **Provenance confirmed (2026-10-09): this is the legacy 227-crop dataset, not a Papuan V2 reconstruction.** A prior hypothesis that $N=135$ might originate from a separate Papuan V2 reconstruction was raised by the author, investigated against `docs/EXP-007_ARCFACE_EVALUATION.md`'s programmatic `face_filename`-join evidence, and withdrawn — see `RESEARCH_DECISIONS.md` and `DATA_DISCREPANCIES.md` D-2.
- **Generation process:** 227 crops → exclude 83 `Ambiguous`-labeled crops → 144 label-eligible → exclude 1 `Angry` + 2 `Disgust` (rare-class exclusion) → 141 → minus 6 further crops lost to ArcFace re-detection/alignment failure → **135**. This chain is cross-corroborated between `docs/EXP-007_ARCFACE_EVALUATION.md` §2 (which reports the 227/178/144/135 checkpoint counts) and `docs/ARCFACE_EXPERIMENT_DESIGN.md` (which prescribes this exact filter order). See `DATA_DISCREPANCIES.md` D-2 for the full arithmetic and its residual gap (row-level sample-identity list not independently re-counted from the raw CSV).
- **Sample count:** 135; skin-tone breakdown Dark=46, Medium-Dark=32, Unknown=57.
- **Status:** **Verified** (provenance and derivation arithmetic, cross-corroborated across two independent documents) — **Provisional** only at the row-level-identity granularity (see D-2). The subset underlies every number in Chapter 4, §Experiment EXP-007 of the thesis manuscript.

### D-PAPUANV2: Papuan V2 Pilot Dataset

- **Version:** v2 (distinguished from D-LEGACY by non-overlapping output paths under `data/papuan_v2/`).
- **Physical location:** `data/papuan_v2/faces/`, `data/papuan_v2/clahe/`, `data/papuan_v2/pilot/images/` (not committed); manifests in `experiments/EXP-PAP-00*/`.
- **Source/parent:** the same source film as D-LEGACY, re-extracted independently (not a subset or superset of D-LEGACY's 227 crops — a separate extraction run).
- **Generation process:** pilot-scale extraction (`max_frames=250`, fps=2.0) → 645 face crops + 645 CLAHE crops (EXP-PAP-001) → 150-image pilot sample, seed=42 (EXP-PAP-002) → HSEmotion/ArcFace+LR predictions on the 150-image pilot (EXP-PAP-003) → Label Studio human-annotation pilot, two isolated annotators (EXP-PAP-004) → CVAT 68-point landmark pilot, 24 images, seed=200 (EXP-PAP-005).
- **Sample count:** 645 pilot-scale crops (both branches); 150-image annotation pilot subset; 75-image annotator-overlap subset; 24-image CVAT landmark pilot.
- **Label schema:** originally HSEmotion's 7-class vocabulary (for the abandoned emotion-annotation track); now a 68-point ibug-300W-convention landmark schema with anatomically named points (post-rename from `pt0`..`pt67`).
- **Intended purpose (at creation):** pilot-scale validation of an annotation architecture (Label Studio + later CVAT), not a finished labeled dataset.
- **Actual observed usage:** no model has been trained on this dataset yet (no landmark-model training code exists); no emotion-label human annotation was completed on it either.
- **Known limitations:** no train/val/test split exists; human annotation (both emotion-label and landmark tracks) incomplete; dataset scale (645) far below the full ~144k-frame source video's extractable potential, and no decision has been made on whether/when to scale up.
- **Evidence:** `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`, `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md`, `experiments/EXP-PAP-00{1,2,3,4,5}/`.
- **Status:** **Verified** for extraction/pilot-scale facts; **Unresolved/Provisional** for annotation completion (see `EXPERIMENT_REGISTRY.md` and `DATA_DISCREPANCIES.md` items D-1, D-3, D-4).

### D-FER2013-RESNET18 ("Experiment B," per task background context)

- **Version/name:** as named in the task's background context only.
- **Physical location:** **not found**. Repository-wide search (all tracked + untracked `.md`, `.py`, `.ipynb`, `.csv`, `.json` files) for `FER2013`, `ResNet18`, and the specific figures 68.57%/69.77%/68.65%/69.76%/26.96% returned zero matches.
- **Status:** **Unverifiable from this repository.** Not included anywhere in the thesis manuscript. See `DATA_DISCREPANCIES.md` item D-0.

## Code Modules

| Module | Role | Status |
|---|---|---|
| `src/frame_extractor.py` | Frame extraction from source video, configurable FPS | Verified (present, referenced in `docs/ARCHITECTURE.md`) |
| `src/face_detector.py` | InsightFace `buffalo_l` (SCRFD) face detection/cropping | Verified |
| `src/fer_dataset/shared/clahe.py` (promoted from `tools/realtime_demo/clahe_preprocessing.py`) | CLAHE preprocessing, LAB L-channel, adaptive clip limit | Verified |
| `src/emotion_classifier.py` | HSEmotion ONNX pretrained inference (`enet_b0_8_best_vgaf`) | Verified |
| `tools/extract_arcface_embeddings.py` | ArcFace (`buffalo_l/w600k_r50`) frozen 512-d embedding extraction | Verified |
| `tools/train_arcface_classifier.py` | Logistic Regression training on ArcFace embeddings, `StratifiedGroupKFold` CV | Verified |
| `src/landmark_analyzer.py` | MediaPipe 478-point face mesh + 4 geometric features + skin-tone bucket | Verified |
| `tools/papuan_v2/setup_label_studio_pilot.py`, `setup_label_studio_annotator_b.py` | Label Studio annotator-isolation infrastructure | Verified (present); **annotation output incomplete**, see registry |
| `tools/papuan_v2/apply_task_overlap.py` | 75-task overlap-subset selection for inter-annotator agreement | Verified (present); agreement statistic itself **not yet computable** (no completed overlap labels) |
| `tools/papuan_v2/human_agreement_report.py` | Inter-annotator agreement computation | Verified (present); **not yet run against real data** — no completed annotation pairs exist to feed it |
| `tools/papuan_v2/annotator_progress.py` | Tracks per-annotator task completion | Verified (present) |
| `tools/papuan_v2/export_label_studio_labels.py` | Label Studio export utility | Verified (present) |
| Landmark-model training code (Original vs. CLAHE comparison) | — | **Does not exist.** Confirmed by repository-wide search. |
| "AI-assisted (paid) pre-labeling" annotation code | — | **Does not exist.** Confirmed by repository-wide search; design-only, per `docs/reports` AI-assisted annotation methodology review (commit `06defa6`). |

## Reports / Evaluation Artifacts

| File | Contents | Status |
|---|---|---|
| `reports/audit_summary_metrics.csv` | D-LEGACY baseline accuracy, false-Angry rate, Neutral→Angry rate | Verified |
| `reports/audit_per_skin_tone_accuracy.csv` | D-LEGACY per-skin-tone accuracy | Verified |
| `reports/arcface_evaluation/comparison_metrics.csv` | HSEmotion vs. ArcFace+LR, D-COMMON135 | Verified |
| `reports/arcface_evaluation/statistical_tests.csv` | McNemar, bootstrap CI, Fisher's exact, D-COMMON135 | Verified |
| `reports/arcface_evaluation/skin_tone_analysis.csv` | Subgroup accuracy breakdown, D-COMMON135 | Verified |
| `reports/arcface_error_analysis/neutral_error_analysis.csv` | Neutral-class error distribution, D-COMMON135 | Verified |
| `experiments/EXP-PAP-004/annotator_progress.json`, `label_studio_export.csv` | Papuan V2 annotation completion records | Provisional — contents read but completion figures **re-flagged for independent re-verification**, see `DATA_DISCREPANCIES.md` D-1 |
| `experiments/EXP-PAP-005/` | CVAT landmark pilot manifest/config | Verified present; review-stage contents not yet produced (review not performed) |

## Annotation / Guideline Artifacts

| File | Role | Status |
|---|---|---|
| `tools/papuan_v2/README_label_studio.md` | Label Studio setup/annotator instructions | Verified present |
| `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md` | 68-point anatomical naming scheme, drift verification | Verified |
| `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md` | CVAT pilot setup description | Verified present; describes pilot setup, not completed review |
| `docs/reports/PAPUAN_V2_LANDMARK_SCHEMA_AND_ANNOTATION_METHOD.md` | Landmark annotation methodology | Verified present |
| `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` | Full-scale annotation plan (uncommitted) | Provisional — plan, not executed |
