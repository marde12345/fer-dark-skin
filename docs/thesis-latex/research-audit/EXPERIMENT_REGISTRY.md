# Experiment Registry

Each entry is independent. Experiments are never merged on the basis of a shared model name alone.

---

### EXP-000 — Source Video Characterization
- **RQ:** none (infrastructure step).
- **Dataset:** source film, full length (144,084 frames, 25fps, 1920×1080).
- **Config:** none (metadata extraction only).
- **Status:** Completed. **Evidence:** `docs/EXPERIMENT.md`.

### EXP-005 — HSEmotion Pretrained Baseline, D-LEGACY ($N=227$)
- **RQ (retrospective framing; not an a-priori stated RQ):** how does a pretrained FER model perform, in aggregate and by skin-tone subgroup, on this Papuan face-crop sample?
- **Dataset/version:** D-LEGACY, $N=227$, original (non-CLAHE) crops.
- **Model:** HSEmotion, ONNX `enet_b0_8_best_vgaf`, pretrained inference only, no fine-tuning.
- **Preprocessing:** none (original crops).
- **Label source:** HSEmotion prediction vs. single-annotator manual ground truth.
- **Split:** none — entire $N=227$ population evaluated, no held-out partition (this is a baseline characterization, not a train/test experiment).
- **Seed:** N/A (no stochastic training step).
- **Metrics:** overall accuracy 22.47%; false-Angry rate 17.62%; Neutral→Angry rate 23.68% (18/76); skin-tone subgroup accuracy Dark 44.00% / Medium-Dark 14.29%; subgroup gap 29.71 pp.
- **Result artifacts:** `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv`.
- **Execution status:** Completed.
- **Reproducibility status:** Provisional — HSEmotion weights are pinned/pretrained (reproducible given same input images), but the input images themselves (227 crops) are not committed to version control (gitignored), so exact reproduction requires re-running the extraction pipeline against the same source video with the same debug-mode sampling, which was not independently re-executed in this audit.
- **Known limitations:** single-annotator ground truth; small, unbalanced skin-tone subgroup sizes; 7-class taxonomy structurally unusable for two classes.
- **Source evidence:** `docs/EXPERIMENT.md` (EXP-005 entry), `docs/R7_5_CLASS_DECISION.md`, `docs/proposal/research/PROBLEM_ARCHITECTURE.md`.

### EXP-006 — CLAHE Ablation, D-LEGACY ($N=227$)
- **RQ:** does CLAHE preprocessing change HSEmotion's accuracy on this population?
- **Dataset/version:** D-LEGACY, $N=227$, CLAHE-preprocessed crops (LAB L-channel, adaptive clip 1.5–3.5, 8×8 tiles), compared directly against EXP-005's original-crop result on the **same 227 images**.
- **Model:** HSEmotion, identical configuration to EXP-005.
- **Metrics:** overall accuracy 19.82% (vs. 22.47% original); false-Angry rate 18.06% (vs. 17.62%).
- **Result:** CLAHE **reduced** accuracy and **increased** the false-Angry rate. Reported as a negative result.
- **Execution status:** Completed.
- **Reproducibility status:** Provisional, same caveat as EXP-005 (raw images not committed).
- **Known limitations:** single preprocessing parameterization tested; no sweep over CLAHE clip-limit range was performed, so "CLAHE doesn't help" is specific to this configuration, not a general CLAHE verdict; no significance test or confidence interval was computed for the accuracy/false-Angry deltas — this is a single uncontrolled run. **This experiment's own per-skin-tone "before" breakdown (Dark 27.67%, Medium-Dark 10.77%) does not match EXP-005's dedicated skin-tone audit (Dark 44.00%, Medium-Dark 14.29%) for the same nominal condition, despite identical 22.47% overall accuracy in both — see `DATA_DISCREPANCIES.md` D-8. The thesis uses EXP-005's figures as the skin-tone-proxy reference; EXP-006's before/after delta is used only for the within-notebook CLAHE effect, not as independent corroboration of EXP-005's absolute numbers.**
- **Source evidence:** `docs/EXPERIMENT.md` (EXP-006 entry).

### EXP-007 — HSEmotion vs. ArcFace+Logistic-Regression, D-COMMON135, 5-Class
- **RQ (retrospective framing):** does a frozen-ArcFace-embedding classifier differ in accuracy or error pattern from the pretrained HSEmotion baseline, on the same evaluation population?
- **Dataset/version:** D-COMMON135 ($N=135$, derived from D-LEGACY, provenance confirmed and derivation chain resolved — see `DATA_DISCREPANCIES.md` D-2), 5-class taxonomy (Fear, Happy, Neutral, Sad, Surprise).
- **Model A:** HSEmotion, pretrained inference, original crops.
- **Model B:** Logistic Regression (multinomial, L2-regularized, class-weighted) trained on frozen ArcFace (`buffalo_l/w600k_r50`) 512-d embeddings of the same 135 crops.
- **Split:** no held-out test set; Model B's reported metrics are from 5-fold `StratifiedGroupKFold` cross-validation, grouped by 3-frame temporal block (heuristic leakage mitigation, not verified subject-identity grouping).
- **Seed:** 42 (recorded).
- **Metrics:** accuracy HSEmotion 36.30% / ArcFace+LR 40.74%; macro precision 0.5898/0.2803; macro recall 0.2058/0.2931; macro F1 0.2489/0.2717; McNemar $b=20,c=26,p=0.4614$ (not significant); group-aware bootstrap 95% CI accuracy HSEmotion [0.2692,0.4672] / ArcFace+LR [0.3383,0.4809]; skin-tone subgroup accuracy (Dark n=46: both 45.65%; Medium-Dark n=32: ArcFace+LR 31.25% / HSEmotion 12.50%); Fisher's exact (HSEmotion skin-tone association) OR=5.88, $p=0.0027$; Neutral-class (n=76) error distribution: HSEmotion 34/76 errors concentrated (18 to Angry), ArcFace+LR 43/76 errors distributed (Happy 15, Sad 14, Fear 8, Surprise 6).
- **Result artifacts:** `reports/arcface_evaluation/{comparison_metrics,statistical_tests,skin_tone_analysis}.csv`, `reports/arcface_error_analysis/neutral_error_analysis.csv`.
- **Execution status:** Completed.
- **Reproducibility status:** Provisional — seed and model configuration recorded, enabling re-run of the classifier training step; the 227→135 filter chain is now documented and arithmetically resolved (see `DATA_DISCREPANCIES.md` D-2), but the underlying 135 images are not committed (gitignored), and the row-level identity list of the 6 alignment-failure exclusions was not independently re-derived from the raw CSV, so the *exact* population cannot be independently regenerated from this repository's committed state alone.
- **Known limitations:** $N=135$ not statistically independent of $N=227$; no causal interpretation of the skin-tone association is supported; small subgroup sizes; cross-validation only, no held-out test partition; temporal-block grouping is a leakage-mitigation heuristic, not verified subject-wise separation.
- **Source evidence:** `docs/EXP-007_ARCFACE_EVALUATION.md`, `docs/RESEARCH_FINDINGS.md`, `docs/R9_FINAL_STATISTICAL_VALIDATION.md`.

### EXP-PAP-001 — Papuan V2 Pilot-Scale Extraction
- **RQ:** infrastructure step (establish a larger, independently sampled extraction for Papuan V2).
- **Dataset:** source film, `max_frames=250`, target fps=2.0.
- **Output:** 645 face crops + 645 CLAHE crops.
- **Execution status:** Completed.
- **Reproducibility status:** Provisional (pinned config values recorded; raw frames not committed).
- **Source evidence:** `docs/reports/PAPUAN_V2_CURRENT_STATE.md`.

### EXP-PAP-002 — Pilot Annotation Sample Selection
- **Dataset:** 150-image subset of EXP-PAP-001's CLAHE branch, seed=42.
- **Execution status:** Completed (sample selected; `pilot_manifest.csv` exists).
- **Source evidence:** `docs/reports/PAPUAN_V2_CURRENT_STATE.md`.

### EXP-PAP-003 — AI Predictions on Pilot Sample
- **Dataset:** EXP-PAP-002's 150-image pilot, CLAHE branch.
- **Models:** HSEmotion (150/150 predictions obtained); ArcFace+LR using the EXP-007-trained classifier, applied (not retrained) to these 150 images (150/150 obtained, after a re-detection bugfix — the nature of this bugfix was not independently re-verified by re-reading the relevant diff in this pass).
- **Execution status:** Completed (predictions obtained). **Human-agreement analysis against these predictions: Pending** — no completed human labels exist yet for this 150-image pilot (see EXP-PAP-004).
- **Source evidence:** `docs/reports/PAPUAN_V2_CURRENT_STATE.md`.

### EXP-PAP-004 — Human Annotation Pilot (Label Studio), Emotion Labels
- **Dataset:** EXP-PAP-002's 150-image pilot (Annotator A, full set) + a 75-image overlap subset (Annotator B, seed=100), via two isolated Label Studio server instances.
- **Execution status:** **BLOCKED / incomplete.** Annotator B: 0/75 tasks completed at last recorded status (`annotator_progress.json`). Annotator A: one internal record reports 150/150 submitted, but this figure was **not independently re-verified against the raw export file in this pass** — see `DATA_DISCREPANCIES.md` D-1. This track was subsequently **superseded** (not formally terminated) as the primary Papuan V2 annotation target on 2026-10-02.
- **Source evidence:** `experiments/EXP-PAP-004/{annotator_assignment.csv,annotator_progress.json,label_studio_export.csv,label_studio_metadata.json}`, `docs/reports/PAPUAN_V2_CURRENT_STATE.md`.

### EXP-PAP-005 — CVAT Facial-Landmark Pilot
- **Dataset:** 24-image subset of EXP-PAP-001's output, seed=200.
- **Model:** InsightFace `landmark_3d_68` (automatic 68-point proposal generation, ibug-300W convention).
- **Execution status:** Proposals generated and loaded into CVAT; point-label scheme renamed to anatomical names (verified zero coordinate drift). **Human review: not performed as of time of writing.**
- **Reproducibility status:** Provisional (seed recorded; raw images not committed; human-review step, being manual, is inherently not "reproducible" in the computational sense — it is a one-time annotation act to be performed, not rerun).
- **Known limitations:** automatic proposals are not ground truth; no inter-annotator agreement protocol has been exercised yet for landmark placement.
- **Source evidence:** `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md`, `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md`, `experiments/EXP-PAP-005/`.

### EXP-PAP-006, EXP-PAP-007 — Not Found
- A repository-wide search for these identifiers (named as a possible range in the task's background context) returned no matching experiment documents, reports, or directories. **Status: Unverifiable / does not appear to exist in this repository.** Not included in any thesis claim.

### "Experiment B" (FER2013 + ResNet18) — Not Found
- See `DATA_DISCREPANCIES.md` item D-0. No registry entry can be created: no dataset path, config, result artifact, or document reference exists anywhere in this repository for this experiment.
