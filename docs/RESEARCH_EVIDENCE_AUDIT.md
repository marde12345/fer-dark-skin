# Research Evidence Audit

> Read-only research audit performed after Phase 11C. This document is a map of what repository evidence actually supports — it does not introduce new experiments, code changes, or research claims. Every substantive number below is cited to its exact repository source (file, cell, or line range).

---

## 1. Research Questions Found

**No formally stated "Research Question" (RQ1, RQ2, ...) or thesis problem-statement text exists anywhere in this repository.** A repository-wide search for `research question`, `RQ`, `hypothesis`, `contribution`, `problem statement`, `research objective` found no such labeled section in any `.md`, `.py`, or notebook file.

The closest evidence of the thesis's actual direction is **`Tesis_Knowledge_Transfer_(1).md`**, a single-section (Section 15 only — sections 1–14 are not present in this repository) Indonesian-language knowledge-transfer note. It is **not phrased as a formal RQ**, but it is the only document in the repository that states research motivation and next steps in narrative form. Quoting its own framing (Section 15.4–15.6, translated sense, not reworded as a formal RQ):

- The work concerns a "dataset dokumenter Papua" (Papua documentary dataset), stated as "100% kulit gelap" (100% dark skin) in the presentation narrative (Section 15.5) — **this claim is not fully consistent with the repository's own computed evidence**, which records both `Dark` and `Medium-Dark` skin-tone buckets in the same dataset (see Section 7 below). This inconsistency is reported, not resolved.
- The stated implication (Section 15.4, translated sense): the observed FER model failures are attributed to "bias representasi di training data HSEmotion" (representation bias in HSEmotion's training data) rather than lighting/contrast alone, used to justify a proposed "Strategy C" (balanced training + skin-tone augmentation).
- Section 15.6 lists unchecked next steps: presenting findings to an advisor ("dosbing"), downloading RAF-DB for main training, implementing "Strategy C," fine-tuning on the Papua dataset, evaluating with fairness metrics (worst-group accuracy, fairness gap), and creating a recording protocol for a private student dataset.

**Conclusion:** the thesis research questions are not explicitly recorded in the repository in the form of a stated RQ. What exists is a narrative research motivation and a next-steps list in `Tesis_Knowledge_Transfer_(1).md`, which should not be treated as an authoritative substitute for the actual thesis RQs — only the thesis author can confirm those.

---

## 2. Existing Experiment Inventory

| ID | Name | Nature | Evidence |
|---|---|---|---|
| EXP-000 | Phase 0 Refactoring Baseline | **Engineering/reproducibility baseline, not a research experiment.** It captures pipeline output counts for regression-testing later refactoring phases; it does not test a research hypothesis. | `docs/EXPERIMENT.md` §EXP-000; `docs/baseline_snapshots/phase0/` |
| EXP-005 | Data Audit: Model Predictions vs. Manual Ground Truth | **Research analysis** — measures the off-the-shelf HSEmotion model's accuracy, fairness, and error patterns against manually reviewed ground truth. | `notebooks/data_audit.ipynb`; `reports/audit_summary_metrics.csv`; `reports/audit_per_skin_tone_accuracy.csv`; `docs/EXPERIMENT.md` §EXP-005 |
| EXP-006 | Preprocessing Experiment: Strategy B CLAHE vs. False-Angry Rate | **Exploratory intervention experiment** — tests one preprocessing variant against the EXP-005 baseline. | `notebooks/preprocessing_experiment.ipynb`, `notebooks/preprocessing_experiment_executed.ipynb` (frozen, unmodified); `reports/preprocessing_experiment_summary.csv`; `docs/EXPERIMENT.md` §EXP-006 |
| Landmark Comparison Analysis | Descriptive geometric-feature comparison by emotion label and skin tone | **Descriptive analysis**, optional pipeline stage. | `src/fer_dataset/analysis/landmark_comparison.py`; `reports/landmark_comparison_summary.csv`; `reports/assets/landmark_*.png` |
| Skin-Tone Analysis | Accuracy / false-Angry-rate breakdown by skin-tone bucket | Embedded within EXP-005 (`notebooks/data_audit.ipynb` cells 9, 11), not a separate experiment. | Same as EXP-005 |

No other substantive research experiment was found in `notebooks/`, `reports/`, `tools/`, or repository history beyond what is listed above. `tools/visualize_landmark_npy.py` is a visualization utility, not an experiment. The Phase 0–11C refactoring work (package restructuring, bug fixes, test suite) is engineering validity work — classified separately in Section 9, not counted as a research experiment here.

---

## 3. Research Evidence Matrix

Since no formal RQ exists, this matrix maps **research objectives evidenced by actual repository work**, not official thesis RQs.

| ID | Research Question / Objective (evidence-derived, not official) | Experiment | Input/Data | Method | Metrics | Result | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| O1 | How accurate is the off-the-shelf HSEmotion model on this dataset? | EXP-005 | `manual_labels_export.csv` (n=227) | Accuracy = (gt_label == model_label) | overall_accuracy, error_rate | 0.2247 / 0.7753 | `notebooks/data_audit.ipynb` cell 5; `reports/audit_summary_metrics.csv` | 🟢 Evidence sufficient (for this specific dataset/model pairing) |
| O2 | Does model accuracy differ by skin tone? | EXP-005 | `landmark_features.csv` `skin_tone` (n=85 with skin_tone) | Group accuracy by `skin_tone` | accuracy_Dark, accuracy_Medium-Dark, fairness_gap | 0.44 / 0.1429 / 0.2971 | `notebooks/data_audit.ipynb` cell 9; `reports/audit_per_skin_tone_accuracy.csv` | 🟠 Evidence weak / requires validation — descriptive group difference only, no statistical test, no confidence interval, small/uneven group sizes not reported |
| O3 | Is the model systematically biased toward predicting "Angry"? | EXP-005 | Same as O1/O2 | Confusion-matrix breakdown of false "Angry" predictions | false_angry_rate; per-GT-class breakdown | 0.1762 overall (40/227); Neutral→Angry 18, Happy→Angry 8, Sad→Angry 6, Ambiguous→Angry 3, Fear→Angry 3, Surprise→Angry 2 | `notebooks/data_audit.ipynb` cell 11 output | 🟢 Evidence sufficient (descriptive) |
| O4 | Is the model overconfident on incorrect "Angry" predictions? | EXP-005 | Same | Mean confidence comparison, true vs. false Angry | mean confidence | true Angry 0.4194 vs. false Angry 0.5968 | `notebooks/data_audit.ipynb` cell 13 output | 🟡 Evidence exists but incomplete — descriptive mean comparison only, no significance test, no variance/CI reported |
| O5 | Does landmark geometry (e.g. brow lowering) explain false "Angry" predictions? | EXP-005 | `landmark_features.csv` `brow_lowering_distance`, joined by filename | Mean comparison, true vs. false Angry | mean brow_lowering_distance | true Angry 0.0377 (**n=1**) vs. false Angry 0.1346 (**n=27**) | `notebooks/data_audit.ipynb` cell 15 output | 🔴 No evidence yet — the notebook's own printed conclusion states the hypothesis is "weak/unsupported in this sample," and the true-Angry group has only **1** sample, which cannot support any comparison |
| O6 | Do predicted-Angry and predicted-Neutral faces differ geometrically? | Landmark Comparison Analysis | `landmark_features.csv`, grouped by predicted `label` (not GT) | Descriptive summary stats (mean/median/std) + boxplots | brow_lowering_distance, lip_corner_distance, mouth_openness, inter_ocular_distance | Angry mean 0.131 vs. Neutral mean 0.147 (brow); similar overlap on other features | `reports/landmark_comparison_summary.csv`; `reports/assets/landmark_angry_vs_neutral_*.png` | ⚪ Exploratory / descriptive only — no statistical test; note this groups by **predicted** label, not ground truth, which is a different question from O5 |
| O7 | Does adaptive CLAHE preprocessing reduce false-Angry rate / improve fairness? | EXP-006 | `data/1408-1010-intermediate/faces/*.jpg`, `annotations.csv`, `manual_labels_export.csv` | Re-classify CLAHE-adjusted crops with the same HSEmotion model, compare to original | accuracy, false_angry_rate, per-skin-tone breakdown | Accuracy **decreased** (0.2247→0.1982); false-Angry rate **increased** (0.1762→0.1806); Medium-Dark false-Angry rate unchanged (0.3538→0.3538) | `notebooks/preprocessing_experiment_executed.ipynb` cells 11, 13, 19; `reports/preprocessing_experiment_summary.csv` | 🟢 Evidence sufficient that **this specific CLAHE variant did not help**, for this dataset/model — 🔴 No evidence for the broader claim that preprocessing cannot help (untested alternatives) |

---

## 4. Baseline Performance

All values sourced from `reports/audit_summary_metrics.csv` and `notebooks/data_audit.ipynb` (cells 5, 9, 11, 13, 17), verified against the notebook's stored execution outputs (not recomputed in this audit):

| Metric | Value | Source |
|---|---|---|
| overall_accuracy | 0.2247 | `reports/audit_summary_metrics.csv`; `notebooks/data_audit.ipynb` cell 5 |
| error_rate | 0.7753 | same |
| false_angry_rate | 0.1762 (40/227) | `reports/audit_summary_metrics.csv`; cell 11 output |
| fairness_gap (max−min accuracy across skin-tone groups) | 0.2971 | `reports/audit_summary_metrics.csv`; cell 9 |
| accuracy_Dark | 0.4400 | `reports/audit_per_skin_tone_accuracy.csv` |
| accuracy_Medium-Dark | 0.1429 | `reports/audit_per_skin_tone_accuracy.csv` |
| confusion matrix (GT × predicted) | full matrix rendered | `reports/assets/audit_confusion_matrix.png`; cell 7 |
| mean confidence (correct) | 0.5035 | cell 13 output |
| mean confidence (wrong) | 0.4418 | cell 13 output |
| mean confidence (true Angry) | 0.4194 | cell 13 output |
| mean confidence (false Angry) | 0.5968 | cell 13 output |
| false-Angry rate by skin tone — Dark | 0.2200 | cell 11 output |
| false-Angry rate by skin tone — Medium-Dark | 0.4571 | cell 11 output |
| per-emotion precision/recall/F1 | **Not currently available** — only a raw confusion matrix is computed; no classification report was generated | — |
| sample/support counts per skin-tone group | **Not currently available as an explicit table** — inferable only by cross-referencing `landmark_features.csv` row counts (85 total, `skin_tone` populated); not tabulated per class × skin-tone | — |

Note on denominators: `manual_labels_export.csv` has 227 rows (all face crops with manual ground truth), but `landmark_features.csv` (and therefore `skin_tone`) is only populated for 85 of those 227 rows (the subset where MediaPipe successfully detected ≥468 landmarks — see `docs/EXPERIMENT.md` EXP-000). So O1/O3/O4 (accuracy, false-Angry breakdown, confidence) are computed over n=227, while O2/skin-tone metrics are computed over the smaller n=85 subset. This distinction is not stated explicitly in the notebook and is worth being precise about when citing these numbers.

---

## 5. Existing Error Analysis

- **Expression-level errors**: A full confusion matrix (GT × model label) exists (`reports/assets/audit_confusion_matrix.png`, `notebooks/data_audit.ipynb` cell 7). The most frequent misclassification-into-Angry source class is identified (`Neutral`, 18 cases) but the notebook does not report a general "most confused pairs" ranking beyond the Angry-focused breakdown.
- **Per-class precision/recall/F1**: **Not currently available.** Only raw counts (confusion matrix cells, false-Angry breakdown) are computed — no `sklearn.classification_report` or equivalent.
- **Confidence vs. correctness**: Yes — analyzed. Mean confidence for correct (0.5035) vs. wrong (0.4418) predictions, and true-Angry (0.4194) vs. false-Angry (0.5968), plus histograms (`reports/assets/audit_confidence_analysis.png`). The notebook's own printed statement ("Over-confident on false Angry? True") is a **direct mean comparison**, not a statistical test — no p-value, effect size, or confidence interval is computed.
- **Landmark geometry (error-specific)**: `brow_lowering_distance` compared between true-Angry (n=**1**) and false-Angry (n=27) predictions (`notebooks/data_audit.ipynb` cell 15). The n=1 true-Angry group makes this comparison **not meaningful** as evidence — the notebook's own printed output concedes the hypothesis is "weak/unsupported in this sample." This is **descriptive only**, not statistical association, and the sample size renders even the descriptive claim fragile.
- **Landmark geometry (broader, predicted-label grouping)**: `src/fer_dataset/analysis/landmark_comparison.py` computes mean/median/std for four features (brow_lowering_distance, lip_corner_distance, mouth_openness, inter_ocular_distance) grouped by **predicted** label (n=28 Angry, n=29 Neutral) and produces boxplots — this is **descriptive evidence only**; no statistical test, effect size, or confidence interval exists in this module (confirmed by reading the full source — it computes `.mean()/.median()/.std()` and `matplotlib` boxplots, nothing else).
- **Skin tone**: Groups present are `Dark` and `Medium-Dark` only, in the 85-row landmark-features subset (no `Medium-Light` or `Light` rows appear in `reports/landmark_comparison_summary.csv` or `reports/audit_per_skin_tone_accuracy.csv`, despite `Medium-Light` being a defined bucket in `src/fer_dataset/pipeline/landmark_analyzer.py`). Group sizes: not explicitly tabulated for accuracy computation (see Section 4 caveat); false-Angry-rate group sizes are visible from `notebooks/data_audit.ipynb` cell 11 output (`Medium-Dark: 16`, `Dark: 11`, `NaN: 13`, out of 40 total false-Angry rows). No statistical significance or effect-size test was performed anywhere in the repository for any skin-tone comparison.

---

## 6. Landmark Analysis

**Source:** `src/fer_dataset/analysis/landmark_comparison.py` (full file read).

- **Features analyzed**: `brow_lowering_distance`, `lip_corner_distance`, `mouth_openness`, `inter_ocular_distance` (the `FEATURES` constant, lines 9-14).
- **Groups compared**: (a) predicted label `Angry`/`Anger` vs. `Neutral` (lines 58-61, 135-136); (b) within each predicted label, `Dark` vs. `Light/Medium` skin-tone group (lines 82-97, 143-165) — in practice, only `Dark` rows exist in this dataset (Section 5), so the skin-tone-within-label comparison currently has no `Light/Medium` counterpart to compare against.
- **Outputs**: `reports/landmark_comparison_summary.csv` (count/mean/median/std per group×feature); `reports/assets/landmark_angry_vs_neutral_*.png` (4 boxplots) and `reports/assets/landmark_{emotion}_skin_*.png` (24 boxplots).
- **Statistical tests**: none. **Effect sizes**: none. **Confidence intervals**: none. The module computes only `pandas` `.mean()`, `.median()`, `.std()`, and `matplotlib.pyplot.boxplot` — confirmed by reading the complete module source; no `scipy.stats` or equivalent import exists anywhere in `src/fer_dataset/`.

**Evidence level supported: Level 1 — Descriptive only.** The repository does not currently support Level 2 (statistical association) or Level 3 (causal evidence) for any landmark-geometry claim. Any statement of the form "the model doesn't use landmark signal Y" (as appears in `Tesis_Knowledge_Transfer_(1).md` Section 15.3, translated sense: "Model tidak menggunakan sinyal landmark/gerakan otot untuk memprediksi Angry") is an **interpretation beyond what the current descriptive comparison supports** — the repository evidence shows overlapping descriptive statistics between groups, which is consistent with, but does not statistically establish, the absence of a geometric signal.

---

## 7. Skin-Tone Analysis

**Source:** `notebooks/data_audit.ipynb` (cells 9, 11); `src/fer_dataset/pipeline/landmark_analyzer.py` (`_compute_skin_tone`, the underlying measurement).

- **Groups present in actual data**: `Dark`, `Medium-Dark` (confirmed in both `reports/audit_per_skin_tone_accuracy.csv` and `reports/landmark_comparison_summary.csv`). The bucket scheme itself defines four possible buckets (`Dark`, `Medium-Dark`, `Medium-Light`, `Light`; `landmark_analyzer.py:131-137`), but only the two darker buckets are populated in this specific dataset's 85-row landmark subset.
- **Group sizes**: not explicitly tabulated for the accuracy computation (85-row subset); for the false-Angry breakdown (40-row subset), `Medium-Dark: 16`, `Dark: 11`, unlabeled: 13 (cell 11 output).
- **Accuracy by group**: Dark 0.44, Medium-Dark 0.1429 (`reports/audit_per_skin_tone_accuracy.csv`).
- **False-Angry rate by group**: Dark 0.22, Medium-Dark 0.4571 (cell 11 output).
- **Fairness gap**: 0.2971 (max−min accuracy across the two groups present).
- **Statistical testing / effect size**: **none performed anywhere in the repository.**

Distinguishing language, per the audit's own requirement: the repository supports the statement "an **observed difference** in accuracy and false-Angry rate exists between the Dark and Medium-Dark groups in this sample," but does **not** support "a **statistically validated** difference" (no test performed) or any **causal** claim about skin tone causing the model's errors.

---

## 8. Preprocessing Experiment

**Source:** `notebooks/preprocessing_experiment.ipynb` (live, canonical-skin-tone version) and `notebooks/preprocessing_experiment_executed.ipynb` (frozen historical execution — **read only, not modified by this audit**); `reports/preprocessing_experiment_summary.csv`.

- **Research motivation**: per the notebook's own header (cell 0, markdown): "This notebook tests whether adaptive CLAHE (Strategy B) reduces false Angry predictions and improves fairness across skin-tone groups."
- **Original hypothesis**: CLAHE preprocessing reduces false-Angry predictions and improves cross-skin-tone fairness (stated, not separately justified with prior literature in-repository).
- **Baseline condition**: original HSEmotion predictions on unmodified face crops (`data/1408-1010-intermediate/annotations.csv`).
- **Treatment condition**: same face crops, CLAHE-adjusted with a skin-tone-dependent clip limit (`apply_strategy_b_clahe`, `clip_min=1.5, clip_max=3.5, l_min=60, l_max=220`), re-classified with the same HSEmotion model.
- **Independent variable**: presence/absence of the CLAHE transform (and its skin-tone-dependent clip limit).
- **Dependent variables**: overall accuracy, false-Angry rate, per-skin-tone accuracy, per-skin-tone false-Angry rate, label-change rate, confidence shift.
- **Recorded results** (verified from `notebooks/preprocessing_experiment_executed.ipynb` cells 9, 11, 13, 15, 19 and cross-checked against `reports/preprocessing_experiment_summary.csv`):

| Metric | Before | After | Delta |
|---|---|---|---|
| Overall accuracy | 0.2247 | 0.1982 | **−0.0264** |
| False-Angry rate | 0.1762 | 0.1806 | **+0.0044** |
| Accuracy — Dark | 0.2767 | 0.2516 | −0.0251 |
| Accuracy — Medium-Dark | 0.1077 | 0.0769 | −0.0308 |
| Accuracy — Medium-Light | 0.0 | 0.0 | 0.0 |
| False-Angry — Dark | 0.1069 | 0.1132 | +0.0063 |
| False-Angry — Medium-Dark | 0.3538 | 0.3538 | 0.0 |
| Label changed ratio | — | 0.2555 (58/227) | — |
| Originally-Angry changed away | — | 7/41 | — |
| Confidence-down rate (previously false-Angry) | — | 0.40 | — |

Per the executed notebook's own transition matrix (cell 9), of 41 originally-Angry predictions, 34 stayed Angry, 4 became Neutral, 2 became Fear, 1 became Sad after CLAHE.

- **Whether the hypothesis was supported**: **No.** Both target metrics moved in the direction opposite to the stated hypothesis (accuracy decreased, false-Angry rate increased). The Medium-Dark false-Angry rate was completely unchanged (0.3538 → 0.3538), meaning CLAHE had zero measurable effect on the group the data-audit identified as most affected by false-Angry errors.
- **Limitations** (evidence-supported, not inferred): single preprocessing variant tested (one clip-limit curve); tested against the same fixed HSEmotion model with no retraining; small, heavily skin-tone-skewed sample (Medium-Light group has 0 accuracy before and after, suggesting near-zero or very small sample in that bucket); no repeated runs or variance estimate.
- **Classification**: **Exploratory experiment.** It is explicitly not part of the production `src/fer_dataset` pipeline — `src/fer_dataset/pipeline/emotion_classifier.py` contains no CLAHE or adaptive-contrast step (confirmed by reading the full module). Per the important instruction in this audit's scope: **this result does not establish that preprocessing in general cannot help** — it establishes that this specific CLAHE variant, on this specific dataset and model, did not improve the tested metrics. The repository's own narrative note (`Tesis_Knowledge_Transfer_(1).md` §15.4) draws a broader implication (representation bias in training data, motivating "Strategy C") — this is the thesis author's own stated interpretation in that document, not a claim independently re-derived by this audit.

---

## 9. Research Infrastructure / Validity Evidence

Classified as **research infrastructure / validity evidence**, not itself a scientific finding, per the audit's required distinction:

- **Phase 0 baseline snapshot** (`docs/baseline_snapshots/phase0/`) — establishes a reproducible reference point for pipeline output, enabling later phases to detect unintended behavioral drift.
- **Annotation-alignment bug discovery and fix** (Phase 9/9B): the original `LandmarkAnalyzer` used a silent positional (row-order) fallback when filename matching failed, and was additionally wired to the wrong annotation-file namespace, meaning **the label-to-landmark-row association mechanism was invalid** end-to-end prior to Phase 9B.
- **Row-order fallback removal** (Phase 9): replaced silent positional guessing with strict filename matching plus an explicit skip-and-count for unmatched rows.
- **Corrected annotation-source wiring** (Phase 9B): `LandmarkAnalyzer` now reads `data/intermediate/annotations.csv` (the correct, same-namespace file) instead of `data/processed/annotations.csv`.
- **Historical output audit and validation** (Phase 9C/9D): the pre-fix mechanism was invalid, but **the specific historical 85-row landmark_features.csv output was independently checked row-by-row and found to be coincidentally correct for this dataset** — every one of the 85 historical labels matched what the corrected, filename-based mechanism produces when re-run on the same data. **This is a distinct claim from "the old mechanism was valid"** — the mechanism remained invalid (it could have produced wrong labels under different directory/annotation drift conditions, as demonstrated by the Phase 9 regression tests), and only this specific dataset's specific output happened to be unaffected.
- **Byte-identical regeneration** (Phase 9D, 11A): `reports/landmark_comparison_summary.csv` and all 28 associated PNGs were regenerated through the corrected pipeline and found to be byte-identical (MD5-verified) to the pre-fix committed versions — confirming the coincidental-correctness finding at the artifact level, not just the row level.
- **Package restructuring** (Phase 10): `src/*.py` → `src/fer_dataset/{pipeline,analysis}` with a proper installable package, validated end-to-end with matching pipeline output counts before/after.
- **Dependency cleanup** (Phase 8): removed three genuinely-unused dependencies (`ultralytics`, `fer`, `retina-face`); added the missing direct `matplotlib` dependency; verified no change to any core ML/scientific dependency version.
- **Configuration cleanup** (Phase 7): removed six confirmed-dead config keys; did not implement any of the functionality they implied (no quality filtering, no confidence-based filtering was added).
- **Test suite**: 65 tests, covering frame sampling, softmax, skin-tone/landmark formulas, annotation alignment (including the fixed behavior), config wiring, the non-destructive constructor fix, and the visualization CLI — all passing as of this audit.
- **Optional analysis wiring** (Phase 11A): landmark comparison is now an explicit, config-gated, default-off pipeline stage, rather than only a standalone script.
- **Experiment documentation** (Phase 11C): `docs/EXPERIMENT.md` now records EXP-000, EXP-005, EXP-006 with evidence-sourced fields.

**How this supports research trustworthiness**: it establishes that the dataset-generation and feature-extraction pipeline now produces label associations by verified filename identity (not silent positional guessing), that this specific historical dataset's already-published numbers were checked and found not to be corrupted by the fixed bug, and that the pipeline's behavior is covered by an automated regression suite — all of which support confidence in **reusing the existing `landmark_features.csv` and its downstream artifacts** for further thesis work. It does **not** itself constitute a research finding about facial expression recognition, fairness, or preprocessing.

---

## 10. Research Gaps

| Objective | Status | Minimum Required Work |
|---|---|---|
| O2 — Skin-tone accuracy difference | **Partially answered** — descriptive difference measured (0.44 vs. 0.1429), but no statistical validation. | Determine whether inferential testing is appropriate given the small, uneven group sizes (exact sizes not currently tabulated — must be extracted first); if appropriate, report an effect size and an uncertainty measure; interpret cautiously given sample size. |
| O4 — Overconfidence on false-Angry | **Partially answered** — mean difference reported (0.4194 vs. 0.5968), no variance/significance. | Report the underlying sample sizes and spread (already partially visible in the histogram asset); assess whether a formal comparison is warranted given the sample sizes. |
| O5 — Brow-lowering geometry and false-Angry (GT-based) | **Not answered** — n=1 true-Angry sample. | This specific comparison cannot be strengthened without more manually-labeled true-Angry, landmark-detected samples — a data availability gap, not an analysis gap. |
| O6 — Landmark geometry by predicted label | **Partially answered** — descriptive only. | Decide whether a statistical/effect-size layer is warranted for this specific comparison, given the also-small Dark-only per-emotion subgroup sizes (as low as n=1 for `Surprise|Dark`). |
| Skin-tone bucket coverage | **Cannot determine** — only `Dark`/`Medium-Dark` appear in this dataset; `Light`/`Medium-Light` are defined but empty. | Determine whether the source video/dataset genuinely contains no lighter-skin-tone subjects, or whether this is a detection/labeling artifact, before drawing any fairness conclusion that implies comparison across the full bucket range. |
| Formal thesis RQ | **Cannot determine** — not present in repository. | Obtain the actual, official thesis research questions from the thesis author/advisor; this audit cannot supply them. |
| "100% dark skin" claim vs. computed `Medium-Dark` presence | **Cannot determine** from repository evidence alone — appears to be an inconsistency between the narrative summary and the computed buckets. | Reconcile directly with the thesis author: is "100% kulit gelap" a simplification, or does it indicate the `Medium-Dark` bucket should not exist for this dataset? |
| CLAHE generalizability | **Not answered** — one variant tested. | If preprocessing remains a research direction, define and test additional variants (or proceed directly to the training-side intervention already proposed in `Tesis_Knowledge_Transfer_(1).md`) rather than treating this single negative result as conclusive either way. |

---

## 11. Prioritized Remaining Work

### P0 — Required for Thesis Validity

- Obtain the actual, official thesis research question(s) from the thesis author — no further evidence audit or roadmap step can be correctly scoped without this, and this audit explicitly cannot supply it.
- Reconcile the "100% dark skin" narrative claim against the repository's own `Dark`/`Medium-Dark` bucket evidence before it is used in any thesis-facing summary — an unresolved factual inconsistency in a headline dataset-description claim is a validity risk.
- Determine and report the actual sample sizes underlying every fairness/skin-tone claim (currently scattered across cell outputs, not tabulated) before any of those numbers are presented as thesis findings — several existing comparisons rest on very small subgroups (e.g., `Medium-Light`: 0 accuracy computed from an unknown, possibly zero or near-zero, sample size; O5's n=1 true-Angry group).

### P1 — Strongly Recommended

- Add statistical validation (appropriate test + effect size + uncertainty measure, chosen based on the actual group sizes and data structure once P0's sample-size audit is done) for the skin-tone accuracy/false-Angry-rate differences, since these are the paper's most fairness-relevant claims and currently rest on raw group means only.
- Produce a per-class precision/recall/F1 table from the existing confusion-matrix data (`notebooks/data_audit.ipynb` cell 7) — the raw counts already exist; only the derived metrics are missing.
- Decide, and document explicitly, whether the descriptive landmark-geometry comparisons (Section 6) are intended to support a thesis claim at all; if so, they need the same statistical treatment as the skin-tone metrics before being cited as evidence rather than illustration.

### P2 — Optional

- Tabulate the empty `Light`/`Medium-Light` skin-tone buckets explicitly (rather than leaving them absent) so any reader of `reports/landmark_comparison_summary.csv` can see they were checked and found empty, not omitted.
- Consider re-running the CLAHE experiment with additional variants only if preprocessing remains part of the thesis narrative after P0's RQ clarification — otherwise this may be superseded by the already-proposed training-side intervention ("Strategy C").

---

## 12. Proposed Research Roadmap

Based strictly on the evidence audited above, the natural next steps — **not forced into the R1–R10 template**, since the evidence shows the project is not starting a fresh baseline-model-analysis phase but rather has an existing baseline (EXP-005) that needs statistical hardening before moving on:

```
R1  Research Question & Evidence Audit          (this document)
 ↓
R2  RQ Clarification with thesis author/advisor  — P0, cannot proceed rigorously without this
 ↓
R3  Sample-Size & Data-Quality Audit             — tabulate exact n's behind every existing metric (P0)
 ↓
R4  Statistical Validation of Existing Findings  — add tests/effect sizes to EXP-005 and landmark comparison (P1)
 ↓
R5  Decision Point: Preprocessing vs. Training-side Intervention
      — informed by R2; the repository's own narrative (Tesis_Knowledge_Transfer) already leans toward
        a training-side intervention ("Strategy C") over further preprocessing experiments
 ↓
R6  Final Experiment Matrix / Findings Consolidation
 ↓
R7  Thesis Chapter Mapping
 ↓
R8  Thesis Writing
```

This audit found no evidence justifying a separate "Baseline Model Analysis" phase distinct from EXP-005 (it already exists), nor evidence that a fresh "Research Dataset Freeze" phase is needed before statistical validation of already-collected data — reordering the generic template accordingly.

---

## 13. Thesis Readiness Assessment

| Area | Status | Evidence / Reason |
|---|---|---|
| Research question clarity | 🔴 Not ready | No official RQ found anywhere in the repository (Section 1). |
| Dataset readiness | 🟡 Partially ready | 227 manually-labeled face crops exist with model predictions; only 85 have landmark features; skin-tone coverage is limited to 2 of 4 defined buckets, and this may or may not match the intended dataset scope (Section 7, Section 10). |
| Pipeline reproducibility | 🟢 Ready | Package-structured, tested (65 tests), deterministic given fixed inputs/versions, annotation-lineage bug fixed and validated (Section 9). |
| Baseline evaluation | 🟢 Ready | Overall accuracy, error rate, confusion matrix, confidence analysis all computed and sourced (Section 4). |
| Error analysis | 🟡 Partially ready | Confusion matrix and false-Angry breakdown exist; per-class precision/recall/F1 do not (Section 5). |
| Landmark analysis | 🟡 Partially ready | Descriptive comparisons exist for two different groupings (GT-based and predicted-label-based); no statistical layer; one key comparison (O5) has n=1 in a critical group (Section 6). |
| Skin-tone analysis | 🟡 Partially ready | Clear descriptive accuracy/false-Angry-rate gap exists; no statistical validation; bucket coverage and the "100% dark skin" narrative claim are inconsistent with each other (Section 7). |
| Preprocessing experiment | 🟢 Ready (as a completed, honestly-reported negative result) | Fully executed, metrics recorded and verified, hypothesis explicitly not supported, frozen historical record preserved (Section 8). |
| Statistical validation | 🔴 Not ready | No statistical test, effect size, or confidence interval exists anywhere in the repository for any comparison. |
| Main findings | 🟡 Partially ready | Several concrete, evidence-backed observations exist (low overall accuracy, skin-tone accuracy gap, Angry over-prediction, CLAHE not helping) — but none carry statistical backing, and no formal RQ exists to frame them as "findings" against. |
| Thesis writing readiness | 🔴 Not ready | Cannot responsibly begin writing findings chapters without P0 items resolved (RQ clarity, sample-size transparency, the dark-skin-percentage inconsistency). |

No overall numeric percentage is given, per the audit's own instruction not to assign one without sufficient evidential basis for a single composite score.

---

## 14. Single Most Important Next Action

**Obtain the official thesis research question(s) directly from the thesis author/advisor, and reconcile them against the evidence in this audit — before any further data analysis, statistical work, or writing.**

Reasoning, based strictly on the evidence above: every other gap in this audit (which statistical tests are appropriate, whether the CLAHE result matters or should be superseded by a training-side intervention, whether the "100% dark skin" claim needs correcting, which of the many descriptive findings in Sections 4–8 actually matter for the thesis) is downstream of knowing what the thesis is actually trying to answer. The repository contains substantial, mostly-sound descriptive evidence (Sections 4, 5, 8) and solid engineering validity (Section 9), but without a stated RQ, this audit cannot determine which findings are central and which are incidental — and no further prioritization in Section 11 can be sharpened past "P0" without it. This is a research-critical, non-engineering action, consistent with the instruction to prefer research-critical work over further code changes.

---

## 15. Evidence Sources

- `Tesis_Knowledge_Transfer_(1).md` (Section 15 only)
- `README.md`
- `docs/EXPERIMENT.md` (§EXP-000, §EXP-005, §EXP-006, Experimental Integrity Boundaries, Known Issues)
- `docs/REPO_AUDIT_REPORT.md`
- `docs/REFACTORING_PLAN.md`
- `docs/ARCHITECTURE.md`, `docs/SDD.md`
- `notebooks/data_audit.ipynb` (cells 1, 3, 5, 7, 9, 11, 13, 15, 17 — source and stored execution outputs)
- `notebooks/preprocessing_experiment.ipynb` (live, canonical-skin-tone version)
- `notebooks/preprocessing_experiment_executed.ipynb` (cells 2, 3, 7, 9, 11, 13, 15, 17, 19 — frozen historical execution outputs; not modified)
- `reports/audit_summary_metrics.csv`
- `reports/audit_per_skin_tone_accuracy.csv`
- `reports/preprocessing_experiment_summary.csv`
- `reports/landmark_comparison_summary.csv`
- `reports/assets/audit_confusion_matrix.png`, `audit_accuracy_by_skin_tone.png`, `audit_false_angry_by_skin_tone.png`, `audit_confidence_analysis.png`, `audit_brow_lowering_true_vs_false_angry.png`
- `reports/assets/landmark_angry_vs_neutral_*.png`, `landmark_*_skin_*.png`
- `src/fer_dataset/analysis/landmark_comparison.py` (full source)
- `src/fer_dataset/pipeline/landmark_analyzer.py` (full source, `_compute_skin_tone`, `_compute_features`)
- `src/fer_dataset/pipeline/emotion_classifier.py` (confirmed no CLAHE/adaptive preprocessing in production)
- `src/fer_dataset/main.py`
- `data/1408-1010-intermediate/manual_labels_export.csv`, `annotations.csv`, `landmark_features.csv`, `clahe_predictions.csv` (schema/row-count inspection only)
- `git log --oneline --all --decorate` (repository commit history, used only to confirm no separate thesis-document commits exist beyond what is listed above)
