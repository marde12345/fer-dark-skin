# Experiment Log

This document records every experiment conducted during the development of the FER Dataset Generation Pipeline.

---

# Experiment Template

## Experiment ID

EXP-001

---

## Date

YYYY-MM-DD

---

## Objective

Example

Evaluate the effect of frame extraction rate on the number of detected faces.

---

## Configuration

| Parameter | Value |
|------------|------|
| FPS | 2 |
| Detection Confidence | 0.7 |
| Blur Threshold | 80 |
| Face Size | 120 px |

---

## Input

| Item | Value |
|------|-------|
| Video | pesta_babi.mp4 |
| Resolution | 1920×1080 |
| Duration | 96 min |

---

## Result

| Metric | Value |
|---------|------|
| Frames | |
| Faces Detected | |
| Faces Filtered | |
| Final Dataset | |

---

## Observation

Write observations here.

Example

- Many false detections occurred in low lighting.
- Increasing FPS generated redundant samples.
- Blur filtering removed approximately 12% of detected faces.

---

## Conclusion

Summarize findings.

---

# Experiment History

| ID | Objective | Status |
|----|-----------|--------|
| EXP-001 | FPS Evaluation | Planned |
| EXP-002 | Detection Confidence | Planned |
| EXP-003 | Blur Threshold | Planned |
| EXP-004 | FER Confidence Threshold | Planned |
| EXP-000 | Phase 0 Refactoring Baseline | Completed (see below) |
| EXP-005 | Data Audit: Model Predictions vs. Manual Ground Truth | Completed (see below) |
| EXP-006 | Preprocessing Experiment: Strategy B CLAHE vs. False-Angry Rate | Completed (see below) |
| EXP-007 | Frozen ArcFace Feature Extraction + Logistic Regression, formally evaluated vs. HSEmotion (R5/R6/R7) | Completed — see `docs/EXP-007_ARCFACE_EVALUATION.md` for the formal R7 evaluation |
| EXP-008 | ArcFace/HSEmotion Error & Skin-Tone Analysis (R8, descriptive-only, reuses R7's common evaluation artifact) | Completed — see `docs/EXP-008_ERROR_AND_SKIN_TONE_ANALYSIS.md` |
| EXP-009 | Final Statistical Validation & Research Findings Synthesis (R9, consolidates EXP-005–EXP-008; no new experiment) | Completed — see `docs/RESEARCH_FINDINGS.md` and `docs/R9_FINAL_STATISTICAL_VALIDATION.md` |

---

# EXP-000 — Phase 0 Refactoring Baseline

## Date

2026-09-08

## Objective

Capture a reproducible snapshot of the current pipeline's outputs (debug-mode run) to serve as the baseline for validating that later refactoring phases (`docs/REFACTORING_PLAN.md`) do not change experimental behavior.

## Baseline Reference

- Snapshot location: `docs/baseline_snapshots/phase0/`
- Baseline commit: `f9c9fae`

## Configuration (from `config/config.yaml` at baseline commit)

| Parameter | Value |
|---|---|
| Video path | `data/raw/videos/pesta_babi.mp4` |
| Target FPS | 2 |
| Debug mode | enabled |
| Debug max frames | 100 |
| Face detection confidence (config key) | 0.7 — **Not recorded as actually applied**; audit found `face_detection.confidence` is not read by `FaceDetector` (Known Issue, see `docs/REPO_AUDIT_REPORT.md` Section J) |
| Quality: min face size (config key) | 120 px — **Not recorded as actually applied**; not read by any code |
| Quality: blur threshold (config key) | 80 — **Not recorded as actually applied**; not read by any code |
| Expression confidence threshold (config key) | 0.90 — **Not recorded as actually applied**; not read by `EmotionClassifier` |
| Landmark analysis enabled | true |
| Landmark save format | npy |
| Visualization enabled | true |

## Input

| Item | Value |
|---|---|
| Video | `pesta_babi.mp4` |
| Duration | 5763.36 sec (~96 min), as printed by `FrameExtractor` at run time |
| Original FPS | 25.00, as printed by `FrameExtractor` at run time |
| Total frames in source video | 144,084, as printed by `FrameExtractor` at run time |
| Resolution | Not recorded (not printed by the pipeline; not read from baseline artifacts) |

## Result (observed values from Phase 0 run)

| Metric | Value | Source |
|---|---|---|
| Frames extracted | 100 | `docs/baseline_snapshots/phase0/pipeline_summary.txt` |
| Faces detected | 227 | `docs/baseline_snapshots/phase0/pipeline_summary.txt` |
| Emotion predictions | 227 | `docs/baseline_snapshots/phase0/pipeline_summary.txt` |
| Dataset images (final) | 227 | `docs/baseline_snapshots/phase0/pipeline_summary.txt` |
| Landmark feature rows | 85 | `docs/baseline_snapshots/phase0/pipeline_summary.txt` |
| Faces filtered | Not recorded — no quality filtering stage exists in current code (see Known Issues / audit Section D.3) | — |

## Emotion Class Distribution (from `docs/baseline_snapshots/phase0/intermediate_annotations.csv`)

| Label | Count |
|---|---|
| Neutral | 88 |
| Fear | 83 |
| Anger | 41 |
| Sadness | 7 |
| Happiness | 5 |
| Surprise | 3 |

Note: 6 of the 7 labels defined in `docs/SDD.md` Section 6 (Angry/Disgust/Fear/Happy/Neutral/Sad/Surprise) appeared in this debug-scale run; `Disgust` did not appear in this 100-frame sample. Label spellings as emitted by the model are `Anger`, `Fear`, `Neutral`, `Sadness`, `Happiness`, `Surprise` (not the `SDD.md` short forms) — this is the raw HSEmotion output vocabulary, unmodified by any mapping step in `src/`.

## Relevant Model Names (from source, `src/` at baseline commit)

| Stage | Model | Location |
|---|---|---|
| Face detection | InsightFace `buffalo_l` (SCRFD), CPUExecutionProvider, det_size (640, 640) | `src/face_detector.py:25-33` |
| Emotion classification | HSEmotion ONNX `enet_b0_8_best_vgaf` | `src/emotion_classifier.py:39` |
| Landmark detection | MediaPipe FaceLandmarker, `face_landmarker.task` (float16, 478 points: 468 mesh + 10 iris) | `src/landmark_analyzer.py:17-21, 57-67` |

## Relevant Thresholds / Parameters (from source, `src/` at baseline commit)

| Parameter | Value | Location |
|---|---|---|
| Face bounding-box padding | 20% (0.2) | `src/face_detector.py:57` |
| MediaPipe min_face_detection_confidence | 0.5 | `src/landmark_analyzer.py:61` |
| MediaPipe min_face_presence_confidence | 0.5 | `src/landmark_analyzer.py:62` |
| MediaPipe min_tracking_confidence | 0.5 | `src/landmark_analyzer.py:63` |
| Skin-tone bucket thresholds (L_weighted) | Dark < 100, Medium-Dark < 150, Medium-Light < 190, else Light | `src/landmark_analyzer.py:131-137` |
| Skin-tone weighting formula | `0.2*mean + 0.3*median + 0.5*center_region_mean` of LAB L-channel | `src/landmark_analyzer.py:118-129` |
| Landmark indices used for features | 33, 55, 65, 61, 291, 13, 14, 263 | `src/landmark_analyzer.py:87-94` |
| Frame sampling interval formula | `max(int(original_fps / target_fps), 1)` | `src/frame_extractor.py:56-59` |

## Dependency Versions (from `docs/baseline_snapshots/phase0/pinned_versions.txt`, actually-installed versions at baseline)

| Package | Version |
|---|---|
| insightface | 1.0.1 |
| hsemotion-onnx | 0.3.1 |
| mediapipe | 1.0.0 |
| opencv-python | 5.0.0.93 |
| onnxruntime | 1.28.0 |
| numpy | 2.5.1 |
| pandas | 3.0.5 |

## Random Seeds

Not recorded — no random seed is set anywhere in `src/` (confirmed by audit, `docs/REPO_AUDIT_REPORT.md` Section E). All stages are treated as deterministic given fixed model weights, fixed input video, and fixed library versions above.

## Observation

- Re-running the identical debug-mode pipeline against the same source video reproduced identical `reports/dataset_report.md` content (227 images, 6 classes, identical distribution) except for the "Generated Date" timestamp, consistent with deterministic behavior at these pinned versions.
- `Neutral` and `Fear` dominate the debug-scale sample; `Disgust` was not observed in this 100-frame subset.

## Conclusion

This run establishes the Phase 0 reproducibility baseline. All future refactoring phases must be validated by re-running the pipeline under this same debug configuration and diffing against `docs/baseline_snapshots/phase0/`.

---

# EXP-005 — Data Audit: Model Predictions vs. Manual Ground Truth

## Evidence Sources

- `notebooks/data_audit.ipynb`
- `reports/audit_summary_metrics.csv`
- `reports/audit_per_skin_tone_accuracy.csv`
- `reports/assets/audit_*.png`

## Date

2026-08-15 — inferred from the file modification timestamp of `reports/audit_summary_metrics.csv` (06:39) and its input `data/1408-1010-intermediate/manual_labels_export.csv` (01:16). Not an explicitly logged execution date; the notebook itself carries no execution timestamp cells.

## Purpose / Question

Per the notebook's own markdown header: "This notebook audits prediction quality, fairness by skin tone, and Angry-specific misclassification behavior."

## Data / Input

- `data/1408-1010-intermediate/manual_labels_export.csv` — manually reviewed ground-truth labels (`gt_label`) paired with the model's original prediction (`model_label`) and confidence, per face-crop filename.
- `data/1408-1010-intermediate/landmark_features.csv` — merged in for `skin_tone`, `L_weighted`, and geometric feature columns (`brow_lowering_distance`, etc.), joined on filename.

## Method

Not explicitly recorded in repository beyond what the notebook cells compute directly: label normalization (`Anger`→`Angry`, `Happiness`→`Happy`, `Sadness`→`Sad`) applied to both `gt_label` and `model_label`; overall accuracy and confusion matrix computed from `gt_label` vs. `model_label`; per-skin-tone accuracy computed by grouping on the `skin_tone` column (sourced from `landmark_features.csv`, not re-derived in this notebook); a "false Angry" analysis isolating rows where `model_label == "Angry"` and `gt_label != "Angry"`; a confidence-distribution comparison between correct and incorrect predictions; a geometric-feature comparison (`brow_lowering_distance`) between true-Angry and false-Angry rows.

## Relevant Variables

`gt_label`, `model_label`, `confidence`, `skin_tone`, `brow_lowering_distance`.

## Outputs / Metrics

From `reports/audit_summary_metrics.csv`:

| Metric | Value |
|---|---|
| overall_accuracy | 0.2247 |
| error_rate | 0.7753 |
| false_angry_rate | 0.1762 |
| fairness_gap (max − min per-skin-tone accuracy) | 0.2971 |
| accuracy_Dark | 0.44 |
| accuracy_Medium-Dark | 0.1429 |

From `reports/audit_per_skin_tone_accuracy.csv`: per-skin-tone accuracy broken out further (Dark: 0.44, Medium-Dark: 0.1429, and any additional groups present in that file).

## Observed Result

The values above are what the committed CSVs contain. Not explicitly recorded in repository: sample size (row count) behind each metric, statistical significance, or any narrative interpretation beyond the raw numbers.

## Interpretation / Status

Not explicitly recorded in repository — the notebook computes and displays these metrics but contains no markdown conclusion cell drawing a final interpretation. Reporting the numbers as observed, not as an endorsed conclusion.

## Relationship to Thesis Methodology

Per Phase 9C's downstream impact audit (`docs/REPO_AUDIT_REPORT.md` / prior refactoring-phase completion reports), this notebook's accuracy/confusion-matrix/false-Angry metrics are sourced from `manual_labels_export.csv`'s own `gt_label`/`model_label` columns, independent of `landmark_features.csv`'s `label` column — so these specific metrics were **not** affected by the annotation-alignment bug fixed in Phase 9/9B. The `skin_tone`-based metrics (`accuracy_Dark`, `fairness_gap`, per-skin-tone accuracy) use `landmark_features.csv`'s `skin_tone` column, which — per the same audit — is computed independently per face-crop image and was also not affected by that bug. No other explicit connection to thesis methodology is stated in the repository.

## Reproducibility Notes

The notebook reads `data/1408-1010-intermediate/` — a directory not covered by `docs/baseline_snapshots/phase0/` (which snapshots `data/intermediate/` from the 100-frame debug run). Reproducing this experiment exactly requires that same `data/1408-1010-intermediate/` dataset and its `manual_labels_export.csv`, which is a manually produced artifact, not automatically regenerable by the pipeline.

---

# EXP-006 — Preprocessing Experiment: Strategy B CLAHE vs. False-Angry Rate

## Evidence Sources

- `notebooks/preprocessing_experiment.ipynb` (canonical skin-tone/softmax logic reconciled with `src/` in Phase 6 — see `docs/REFACTORING_PLAN.md` Approved Decision #4)
- `notebooks/preprocessing_experiment_executed.ipynb` (frozen historical execution — not modified by any refactoring phase)
- `reports/preprocessing_experiment_summary.csv`
- `reports/assets/prep_*.png`

## Date

2026-08-15 — inferred from the file modification timestamp of `reports/preprocessing_experiment_summary.csv` and `data/1408-1010-intermediate/clahe_predictions.csv` (both 06:51), after `reports/audit_summary_metrics.csv` (06:39), suggesting this experiment ran after EXP-005 on the same day. Not an explicitly logged execution date.

## Purpose / Question

Per the notebook's own markdown header: "This notebook tests whether adaptive CLAHE (Strategy B) reduces false Angry predictions and improves fairness across skin-tone groups."

## Data / Input

- `data/1408-1010-intermediate/annotations.csv` — original (pre-CLAHE) HSEmotion predictions.
- `data/1408-1010-intermediate/faces/*.jpg` — face crops re-classified after CLAHE preprocessing.
- `data/1408-1010-intermediate/manual_labels_export.csv` — manual ground truth, same source as EXP-005.

## Method

An adaptive CLAHE transform (`apply_strategy_b_clahe`, notebook-local, not part of the production `src/` pipeline) is applied to each face crop, with a clip-limit that varies based on the canonical skin-tone L-weighted value (`clip_min=1.5, clip_max=3.5, l_min=60, l_max=220`). Each CLAHE-adjusted crop is re-classified with the same HSEmotion model (`enet_b0_8_best_vgaf`) used by the production pipeline. Results are compared against the original (pre-CLAHE) predictions and against manual ground truth: overall accuracy before/after, false-Angry rate before/after (overall and per skin tone), label-change rate, and confidence-shift direction for previously-false-Angry predictions.

## Relevant Variables

`original_label`, `original_confidence`, `clahe_label`, `clahe_confidence`, `l_weighted`, `clip_limit_used`, `skin_tone`, `gt_label`.

## Outputs / Metrics

From `reports/preprocessing_experiment_summary.csv`:

| Metric | Before | After | Delta |
|---|---|---|---|
| Overall accuracy | 0.2247 | 0.1982 | −0.0264 |
| False-Angry rate | 0.1762 | 0.1806 | +0.0044 |
| Accuracy — Dark | 0.2767 | 0.2516 | −0.0251 |
| Accuracy — Medium-Dark | 0.1077 | 0.0769 | −0.0308 |
| Accuracy — Medium-Light | 0.0 | 0.0 | 0.0 |
| False-Angry — Dark | 0.1069 | 0.1132 | +0.0063 |
| False-Angry — Medium-Dark | 0.3538 | 0.3538 | 0.0 |

Additional recorded metrics: `label_changed_ratio` = 0.2555; `false_angry_before_confidence_down_rate` = 0.4; `false_angry_before_label_changed_rate` = 0.15.

## Observed Result

Per the committed summary CSV, the CLAHE (Strategy B) preprocessing variant produced a **lower** overall accuracy and a **higher** (not lower) false-Angry rate than the original, un-preprocessed predictions, both overall and in the Dark skin-tone group. The Medium-Dark false-Angry rate was unchanged; the Medium-Light group had zero accuracy both before and after (sample-size caveat: row counts behind this group are not recorded in the summary CSV).

## Interpretation / Status

Not explicitly recorded in repository as a narrative conclusion. Based strictly on the numbers above, this experiment's own stated hypothesis ("CLAHE reduces false Angry predictions and improves fairness") is **not supported** by the recorded results for this run — the metrics moved in the opposite direction. This is reported as an observation from the data, not as an interpretation authored by the notebook.

## Relationship to Thesis Methodology

This CLAHE preprocessing variant is **exploratory only** and is not part of the production `src/fer_dataset` pipeline — `src/fer_dataset/pipeline/emotion_classifier.py` performs no CLAHE or other adaptive preprocessing before HSEmotion classification. Per `docs/REFACTORING_PLAN.md` Approved Decision #4 and the Phase 6 completion report, this notebook's skin-tone computation was reconciled to call the canonical `src/fer_dataset/pipeline/landmark_analyzer.LandmarkAnalyzer._compute_skin_tone`, so the skin-tone values feeding this experiment are guaranteed consistent with the production pipeline's own skin-tone logic — but the CLAHE step itself remains an experimental branch, not a change to dataset-generation methodology.

## Reproducibility Notes

Same dataset dependency as EXP-005 (`data/1408-1010-intermediate/`, including the manual `manual_labels_export.csv`). `notebooks/preprocessing_experiment_executed.ipynb` preserves the historical executed outputs of this notebook and must not be modified or re-run to "update" this record — per refactoring-phase rules, historical experiment outputs are treated as immutable evidence.

---

# Experimental Integrity Boundaries

The following parameters/logic define the pipeline's actual methodology and must not change unintentionally during refactoring. For each, a change is classified as one of:

- **Safe refactoring** — implementation/location may change, output must remain identical.
- **Behavioral change** — output would change; requires explicit researcher approval before implementing, even if the change looks like an improvement.
- **Research-methodology change** — alters what is being measured/labeled/grouped; requires explicit researcher approval and should be treated as a new experiment, not a refactor.

| Item | Location | Sensitivity / Why | Classification if changed |
|---|---|---|---|
| Frame sampling (`frame_interval = max(int(original_fps/target_fps), 1)`) | `src/frame_extractor.py:56-59` | Determines which frames exist at all in the dataset; changes propagate through the entire pipeline. | Research-methodology change |
| InsightFace model & detection parameters (`buffalo_l`, CPUExecutionProvider, det_size (640,640)) | `src/face_detector.py:25-33` | Model choice and detector resolution affect which faces are found at all. | Research-methodology change |
| Face bounding-box padding (20%) | `src/face_detector.py:57` | Changes crop framing fed into both the emotion classifier and the landmark analyzer. | Behavioral change |
| HSEmotion model (`enet_b0_8_best_vgaf`) | `src/emotion_classifier.py:39` | This *is* the label-generation model — dataset ground truth is model output, not human annotation. | Research-methodology change |
| Softmax / emotion prediction behavior | `src/emotion_classifier.py:11-14, 71-76` | Confidence values derive directly from this; used for dataset filtering/reporting downstream. | Behavioral change |
| MediaPipe model & confidence thresholds (0.5 / 0.5 / 0.5) | `src/landmark_analyzer.py:57-67` | Determines which faces get landmarks at all, and landmark stability. | Behavioral change |
| Landmark indices & geometric feature formulas (`brow_lowering_distance`, `lip_corner_distance`, `mouth_openness`, inter-ocular normalization; indices 33/55/65/61/291/13/14/263) | `src/landmark_analyzer.py:85-115` | Explicitly documented in-code as "user requirement" (line 86) — these are thesis-defined geometric features, not incidental implementation detail. | Research-methodology change |
| Skin-tone calculation (LAB L-channel, weighted mean/median/center) | `src/landmark_analyzer.py:118-129` | Thesis-relevant grouping variable (fairness/robustness analysis by skin tone). | Research-methodology change |
| Skin-tone bucket thresholds (100 / 150 / 190) | `src/landmark_analyzer.py:131-137` | Boundaries are load-bearing for skin-tone group comparisons in `landmark_comparison.py` and the notebooks. | Research-methodology change |
| Label/annotation alignment (filename match, fallback to row-order) | `src/landmark_analyzer.py:199-209` | Determines which label gets attached to which landmark feature row; see Known Issue #1 below. | Behavioral change (fixing the fallback) / Research-methodology change (if the fix would alter which rows get which label in the existing dataset) |

---

# EXP-007 — Frozen ArcFace Feature Extraction + Logistic Regression

> **This entry records implementation/validation evidence, not final research evaluation evidence.** No accuracy/F1/statistical comparison against HSEmotion has been computed. That is reserved for a future evaluation phase (R7). Everything below is a sanity-check record confirming the pipeline runs correctly and produces a valid artifact — not a thesis finding.

## Date

2026-09-09 (session date; not independently corroborated by an external log).

## Objective

Implement and validate the first stage of the ArcFace-based FER experiment proposed in `docs/ARCFACE_EXPERIMENT_DESIGN.md`: frozen ArcFace embedding extraction (R5) followed by a frozen-embedding, trained Logistic Regression classifier evaluated via group-aware cross-validation (R6). HSEmotion remains the pipeline's production expression classifier, unchanged.

## Implementation

- `tools/extract_arcface_embeddings.py` — extracts 512-d, L2-normalized ArcFace (`buffalo_l/w600k_r50`) embeddings from existing face crops, re-detecting 5-point landmarks within each crop for InsightFace's internal `norm_crop` alignment (112×112). Every crop resolves to `embedded` or an explicit exclusion reason.
- `tools/train_arcface_classifier.py` — joins embeddings to `manual_labels_export.csv`'s `gt_label` by filename (never row order), excludes `Ambiguous`/missing labels and classes with fewer than 5 usable samples, and trains/evaluates a multinomial, L2-regularized, class-weighted Logistic Regression via 5-fold `StratifiedGroupKFold` cross-validation, grouped by 3-consecutive-frame temporal blocks (no person-identity metadata exists in this repository).

## Full-Dataset Population

| Stage | Count |
|---|---|
| Total face crops (`data/intermediate/faces`) | 227 |
| ArcFace-embedded successfully | 178 |
| Excluded — no face on crop re-detection | 48 |
| Excluded — multiple faces on crop re-detection | 1 |
| Excluded — invalid image | 0 |
| Excluded — embedding error | 0 |
| Excluded — `Ambiguous` ground-truth label | 40 |
| Excluded — rare class `Disgust` (2 samples, below the 5-sample minimum) | 2 |
| Excluded — rare class `Angry` (1 sample, below the 5-sample minimum) | 1 |
| **Final usable samples for classifier training/evaluation** | **135** |

## Class Order and Counts (deterministic, alphabetical)

`["Fear", "Happy", "Neutral", "Sad", "Surprise"]` — `Neutral: 76, Happy: 32, Sad: 12, Surprise: 8, Fear: 7`.

**Deviation from R4's "seven classes" assumption**: only 5 of the 7 canonical HSEmotion-vocabulary classes have enough manually-labeled ground-truth examples (≥5) to be included in this classifier experiment. `Angry` (1 sample) and `Disgust` (2 samples) are excluded — not silently dropped, but explicitly counted and reported here, per the requirement not to force an invalid cross-validation configuration around single-digit classes.

## Cross-Validation

`StratifiedGroupKFold`, 5 splits, 16 temporal groups (blocks of 3 consecutive frame indices), `random_state=42`. Every one of the 135 usable samples received exactly one out-of-fold prediction; no group appeared as a CV test set in more than one fold (verified programmatically, not merely assumed — see `tests/test_train_arcface_classifier.py`).

## Classifier Configuration

`LogisticRegression(penalty="l2", solver="lbfgs", class_weight="balanced", max_iter=1000, random_state=42)`. No hyperparameter sweep was performed.

## Output Artifacts (not committed; `data/` is gitignored)

- `data/intermediate/arcface_embeddings/embeddings.csv` — full-dataset ArcFace embeddings (identity: `sample_id`, `face_filename`).
- `data/intermediate/arcface_embeddings/classifier_predictions.csv` — 135 out-of-fold predictions (`sample_id`, `face_filename`, `gt_label`, `predicted_label`, `fold`, `split_role`, `prediction_probabilities`).
- `data/intermediate/arcface_embeddings/classifier_metadata.json` — full reproducibility metadata (model identifiers, configuration, class order, exclusion counts).

## Basic Sanity Checks (implementation validation only — NOT final metrics)

- Embedding dimensionality: 512, confirmed finite and L2-normalized (norm ≈ 1.0) on a real sample.
- Prediction probabilities: confirmed finite, in [0, 1], summing to ≈1.0 per sample.
- No duplicate `sample_id` in the prediction artifact (135 rows, 135 unique IDs).
- All 5 folds represented in the output.

No accuracy, F1, confusion matrix, or comparison to HSEmotion's baseline was computed in this entry — see the reservation at the top of this section.

## Relationship to HSEmotion Baseline

Entirely separate. `data/intermediate/annotations.csv` and `data/processed/annotations.csv` (HSEmotion's outputs) were not read, modified, or regenerated by this experiment. HSEmotion's `model_label` was never used as a training target — ground truth for this experiment is exclusively `manual_labels_export.csv`'s `gt_label`.

## Reproducibility Notes

Requires `data/intermediate/faces` (227 crops from the existing debug-mode pipeline run) and `data/1408-1010-intermediate/manual_labels_export.csv` (227-row manual ground truth). Both are gitignored/local artifacts, not committed — reproducing this experiment requires regenerating or retaining them.

---

# Known Issues (from audit, not fixed in Phase 1)

## Known issue — not fixed in Phase 1: Silent row-order fallback in landmark annotation alignment

**Location:** `src/landmark_analyzer.py:199-209`

**Description:** When a face-crop filename has no matching row in the processed annotations CSV, the code falls back to positional alignment (`ann.iloc[idx]` where `idx` is the enumeration index over sorted face-crop filenames) instead of failing loudly or leaving the label as `Unknown`. If the face-crop directory and the annotations file ever differ in count or ordering (e.g., because `DatasetBuilder` skips crops whose source file no longer exists), this can silently attach the wrong label to a landmark feature row.

**Status:** `Known issue — not fixed in Phase 1`. Per audit Section E, this requires researcher approval before any fix, since a fix could change which labels are historically attached to which rows in already-published results.

## Known issue — not fixed in Phase 1: Duplicate InsightFace model instantiation in `EmotionClassifier`

**Location:** `src/emotion_classifier.py:41-46`

**Description:** `EmotionClassifier` constructs a second, independent InsightFace `FaceAnalysis` (`buffalo_l`) instance solely to draw 5-point keypoints for the optional visualization output, duplicating the detector already instantiated in `FaceDetector` for the same face crops. This does not affect labels or features — it is a performance/resource redundancy, not a correctness issue.

**Status:** `Known issue — not fixed in Phase 1`. Low priority per audit; flagged only because it touches face-detection code, which is classified high-risk.
---

# Papuan V2 Pilot Workflow (EXP-PAP-NNN)

New namespace, approved in `docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md`
("Approved Decisions" §2), used exclusively for Papuan V2 data-side work so
it can never be confused with the `EXP-NNN`/`R\d` entries above, all of
which describe the legacy pipeline/dataset and remain unmodified.

## EXP-PAP-001 — Pilot-scale raw source pipeline (frame extraction, face detection, CLAHE)

**Status:** Complete.

**What was done:** Re-ran frame extraction (`FrameExtractor`, unmodified,
reused from the legacy pipeline) and face detection (`FaceDetector`,
unmodified) against `data/raw/videos/pesta_babi.mp4` — the same source
video the legacy pipeline used — but writing to new,
non-overlapping output paths (`data/papuan_v2/faces/`), never touching any
legacy `data/` directory. CLAHE (Strategy B, promoted to
`src/fer_dataset/shared/clahe.py`) was then applied to every face crop,
writing `data/papuan_v2/clahe/`.

**Config:** fps=2.0 (target), `frame_interval`=12 (from source FPS 25.0),
debug mode with `max_frames=250` — a deliberate pilot-scale cap, not the
full ~96-minute video, since this stage only needs to produce enough face
crops to support a 100–200 image pilot (see script docstring for full
rationale). A full-scale Papuan V2 build would reuse the same code with
`debug=False`.

**Results:** 250 frames sampled → 645 face crops detected → 645 CLAHE
images written. Full reproducibility metadata (source video SHA-256,
original FPS, frame interval, code provenance, timestamp) recorded in
`data/papuan_v2/raw/source_video_manifest.json`.

**Code:** `tools/papuan_v2/build_pilot_source.py`.

## EXP-PAP-002 — Pilot set construction + human-labels template

**Status:** Pilot set and template complete; actual human labeling pending
(see EXP-PAP-004 status).

**What was done:** Deterministically sampled 150 images (seed=42,
`random.Random(seed).sample()` over the sorted face-crop filename list) from
the 645 EXP-PAP-001 face crops, copying each image's CLAHE version (never
the un-preprocessed crop, per the supervisor's requirement that AI-assisted
annotation input be CLAHE-preprocessed) into `data/papuan_v2/pilot/images/`.
Wrote `experiments/EXP-PAP-004/pilot_manifest.csv` (image_id, source paths,
seed, timestamp) as the single source of truth for pilot membership, and an
empty `human_labels.csv` template (150 rows, blank `gt_label`) for a human
annotator to fill in independently of any AI prediction.

**Code:** `tools/papuan_v2/sample_pilot.py`,
`tools/papuan_v2/init_human_labels_template.py`.

## EXP-PAP-003 — AI-assisted-annotation candidates + agreement analysis

**Status:** AI predictions complete; agreement metrics pending human labels
(see EXP-PAP-004).

**What was done:** Ran both candidates on the exact same 150 CLAHE pilot
images, neither performing a second face-detection pass on the crop:
  - Candidate A (`hsemotion_clahe`): HSEmotion ONNX (`enet_b0_8_best_vgaf`)
    directly on the CLAHE crop. 150/150 succeeded.
  - Candidate B (`arcface_lr_clahe`): InsightFace ArcFace
    (`buffalo_l/w600k_r50`) embedding of the CLAHE crop, classified by the
    existing pre-trained `LogisticRegression` demo model
    (`tools/realtime_demo/artifacts/arcface_lr_demo_model.joblib`, trained
    per `tools/train_arcface_classifier.py`/R6 on legacy
    `manual_labels_export.csv` — not retrained on any Papuan V2 data).
    **150/150 succeeded** after a fix (see note below).

**Implementation note — ArcFace embedding path was fixed to remove
re-detection:** the first implementation reused
`tools/extract_arcface_embeddings.py`'s `ArcFaceEmbedder`, which re-runs
InsightFace's own face detector on the already-cropped pilot image solely to
obtain 5-point landmarks for `face_align.norm_crop`. That re-detection
failed to find exactly one face on 50/150 (33%) of pilot images (48
`excluded_no_face`, 2 `excluded_multiple_faces`) — an artifact of redundant
detection on a tight crop, not a real signal about ArcFace+LR's usefulness
as an annotation assistant. **That 100/150 result was never used as
agreement-analysis input**; it is preserved only as a debugging note (see
`experiments/EXP-PAP-004/metadata.json`'s `superseded_result` field and
`report.md`).

Fix: Candidate B now calls the recognition sub-model directly
(`insightface.model_zoo.get_model(".../w600k_r50.onnx")` →
`ArcFaceONNX.get_feat()`), confirmed by reading InsightFace's own source to
require no detection or landmarks — it resizes the given crop internally via
`cv2.dnn.blobFromImages`. No detection model is loaded for this path at all
(`FaceAnalysis` normally asserts one must be present), so a second detection
is structurally impossible here, not merely avoided by convention. The
embedding is L2-normalized identically to `Face.normed_embedding` before
being passed to the same trained classifier.

**Caveat, stated explicitly:** the classifier was trained on embeddings
produced through the full detect+landmark-align pipeline
(`tools/extract_arcface_embeddings.py`). This direct `get_feat()` path skips
that alignment, relying instead on the crop already being face-centered by
`FaceDetector`'s 20%-padded bounding box — a distributional difference from
training input, to be weighed alongside the agreement metrics once computed.

Predictions written to `experiments/EXP-PAP-004/ai_predictions.csv`. This
file was never merged into or allowed to influence `human_labels.csv` (see
`tests/test_pilot_independence.py`).

The agreement-metrics computation (accuracy, macro-F1, Cohen's kappa,
confusion matrix, confidence-vs-correctness) is implemented and unit-tested
(`tools/papuan_v2/pilot_agreement_report.py`,
`tests/test_pilot_agreement_metrics.py`) but has not been run against real
data — it refuses to run while `human_labels.csv` has any blank `gt_label`
(verified by attempting a run against the current template, which raised
the expected `RuntimeError`).

## EXP-PAP-004 — Annotation-assistant selection decision

**Status:** PENDING. Blocked on human labeling of the 150-image pilot set
(`experiments/EXP-PAP-004/human_labels.csv`) — see
`experiments/EXP-PAP-004/report.md` for the full explanation of why this
step cannot be performed by the assistant implementing this pipeline (doing
so would fabricate the independent ground truth the pilot design depends
on, exactly the self-confirmation-bias failure mode the pilot exists to
prevent).

Once human labeling is complete, running
`uv run python tools/papuan_v2/pilot_agreement_report.py` produces the real
`agreement_metrics.json`, `confusion_matrices/`, and `report.md`. The
annotation-assistant selection decision itself must then be written here as
a follow-up entry, referencing that report — it is not automatically chosen
by the script.

## EXP-PAP-004 (extension) — Multi-annotator overlap for human-human agreement

**Status:** Infrastructure complete and live-verified; Annotator B has not yet labeled (server ready, 0/75 completed).

**What was done:** Extended the single-annotator pilot to support two independent human annotators:

- **Deterministic overlap assignment**: `experiments/EXP-PAP-004/annotator_assignment.csv` — Annotator A assigned all 150 pilot images (unchanged), Annotator B assigned a reproducible 75-image subset (`random.Random(100).sample()` over the sorted `pilot_manifest.csv` image_id list — a seed distinct from the pilot-sampling seed). Task 1's image (`frame_000008_face01`, already labeled by A) was not special-cased in or out of the sample and happened to land in the overlap set by the deterministic draw.
- **Task 1 preserved**: `tools/papuan_v2/apply_task_overlap.py` PATCHes only the integer `overlap` field on Project A's tasks (2 for the 75 overlap tasks, 1 for the rest) via the REST API, never touching the `annotations` table. Live-verified: Task 1's single existing annotation (`Neutral`/`Medium`, submitted by `mardefasma123up@gmail.com`) was byte-identical before and after the PATCH, confirmed by the script's own before/after diff check.
- **Annotator B isolation investigated and resolved**: the installed Label Studio (Community 1.23.0) has no role-based Data Manager restriction (`OrganizationMember` has no `role` field — confirmed by reading `organizations/models.py`), so any org member can browse any project's annotations. A second project in the same organization would not have isolated B from A. Instead, Annotator B runs on a **fully separate Label Studio server process** (`tools/papuan_v2/setup_label_studio_annotator_b.py`, separate port/`--data-dir`/SQLite DB/organization), live-verified to have zero knowledge of Project A: its own `/api/projects` lists only its own project. The same pilot image files are served read-only to both servers (no copies).
- **Real annotator identity**: `export_label_studio_labels.py` now resolves each annotation's `completed_by` field to that user's actual email via `client.get_users()` (live-verified: Task 1's export correctly shows `mardefasma123up@gmail.com`, not a placeholder string).
- **Human-human agreement**: `tools/papuan_v2/human_agreement_report.py` (raw agreement, Cohen's kappa, confusion matrix, per-class agreement, disagreement list) is implemented and unit-tested but has NOT been run against real data — it refuses to run until both annotators have labeled all 75 overlap images, and it never adjudicates disagreements automatically.
- **Dashboard-readiness**: `tools/papuan_v2/annotator_progress.py` writes `experiments/EXP-PAP-004/annotator_progress.json` (assigned/completed counts per annotator, overlap size, current agreement summary) by querying both servers live; B's server is optional/best-effort.

**Live verification performed this session:**
- Project A (id=2): 75/150 tasks now at `overlap=2`, 75 at `overlap=1`; `show_collab_predictions=False`, `show_annotation_history=False`.
- Project B (id=1, separate server on port 8081): 75/75 tasks imported, isolated (own org, own DB), local file serving verified (`HTTP 200`), idempotent on rerun (0 duplicate tasks/storage connections on a second run).
- `annotator_progress.json` generated live: `annotator_A_completed: 1`, `annotator_B_completed: 0`, `human_human_agreement: null` (correctly pending).

**Code:** `tools/papuan_v2/{apply_task_overlap,setup_label_studio_annotator_b,human_agreement_report,annotator_progress}.py`; extensions to `label_studio_config.py` and `export_label_studio_labels.py`.

**Explicitly not done (per scope):** no agreement computed (Annotator B hasn't labeled yet), no adjudication, no model-vs-human comparison, no full-scale annotation, no splits, no fine-tuning, no legacy data touched.

---

# Papuan V2 Full Workflow — Phase 1 Architecture Validation

**Status:** Complete. Empirical validation only, no real annotation performed. See `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` ("Phase 1 Validation Results" section) for full detail.

**Summary:** Stood up a fully isolated, throwaway Label Studio server (port 8090, separate data-dir/DB/organization, never connected to the pilot's ports 8080/8081) with 4 users (1 owner/inspector + Annotators A/B/C), a bilingual (English/Indonesian) label config, 3 synthetic fixture images, and `maximum_annotations=3` set at project-creation time (which automatically gave every imported task `overlap=3`, with no post-hoc PATCH needed — a lower-friction finding versus the pilot's Task-1 retrofit). Empirically confirmed, via each annotator's own API token against the actual labeling-stream endpoint (`GET /api/projects/<id>/next`), that Annotator B's and C's task view carries zero content from a co-annotator's already-submitted annotation (only a non-content `total_annotations` count is visible) — validating that the shared-instance architecture (one project, `overlap=N`) is safe for independent initial human judgments in Label Studio Community 1.23.0, under this project configuration (`show_collab_predictions=False`, `show_annotation_history=False`, annotators added only as plain organization members, never Manager/reviewer). All 3 annotators then submitted deliberately distinct annotations on the same task; exported with real resolved identities (never faked/ordering-based), and a pure majority-vote consensus function was validated against all three of the brief's worked examples plus the real fixture data.

Pilot preservation verified before and after via checksum/state comparison: Task 1's annotation, `pilot_manifest.csv`, `human_labels.csv`, `ai_predictions.csv`, and all four legacy data directories were confirmed byte-for-byte/count-for-count unchanged.

**Code:** `tools/papuan_v2/validation/{fixture_config,export_fixture_annotations,consensus_fixture}.py` (all new, isolated from pilot production code). Tests: `tests/test_phase1_validation_fixture.py` (20 tests).

**Open items carried forward:** a real-browser visual confirmation of the API-level visibility finding (recommended, not blocking); the AI-visibility-to-annotators methodology choice (still yours to make); dataset-size scope for the full dataset; EXP-PAP-004's own assistant selection (unaffected by this phase); whether annotators need explicit per-project `ProjectMember` records for the real rollout (not exercised in this fixture, since all calls addressed the project by known ID).
