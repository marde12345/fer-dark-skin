# R9 — Final Statistical Validation

> Consolidation and cross-experiment consistency audit of EXP-005 through EXP-008. No new model, training run, preprocessing experiment, dataset, or research question was introduced. No new statistical test was run beyond re-verifying existing reported statistics against their source artifacts.

---

## Cross-Experiment Consistency Audit

Full machine-readable version: `reports/final_research_validation/cross_experiment_consistency.csv`. Every value below was re-read directly from its source CSV, not copied from prose documentation.

| Finding | Source Experiment | Population | Value | Recomputed? | Consistent? |
|---|---|---|---|---|---|
| EXP-005 overall accuracy | EXP-005 | N=227 | 0.2247 | Yes — `reports/audit_summary_metrics.csv` | Yes |
| EXP-005 false-Angry rate | EXP-005 | N=227 | 0.1762 | Yes — same file | Yes |
| EXP-005 Neutral→Angry | EXP-005 | N=76 (of 227) | 18/76 = 0.2368 | Yes — `notebooks/data_audit.ipynb` cell 11 output, `docs/EXPERIMENT.md` | Yes |
| EXP-006 CLAHE accuracy before/after | EXP-006 | N=227 | 0.2247 / 0.1982 | Yes — `reports/preprocessing_experiment_summary.csv` | Yes |
| EXP-006 CLAHE false-Angry before/after | EXP-006 | N=227 | 0.1762 / 0.1806 | Yes — same file | Yes |
| EXP-007 ArcFace accuracy | EXP-007 | N=135 | 0.4074 | Yes — `reports/arcface_evaluation/comparison_metrics.csv` | Yes |
| EXP-007 HSEmotion accuracy (common subset) | EXP-007 | N=135 | 0.3630 | Yes — same file | Yes |
| EXP-007 macro P/R/F1 (both models) | EXP-007 | N=135 | ArcFace 0.2803/0.2931/0.2717; HSEmotion 0.5898/0.2058/0.2489 | Yes — same file | Yes |
| McNemar test | EXP-007 | N=135 paired | b=20, c=26, p=0.4614 | Yes — `reports/arcface_evaluation/statistical_tests.csv` | Yes |
| Bootstrap CI (accuracy, both models) | EXP-007 | N=135 (group-aware) | ArcFace [0.3383, 0.4809]; HSEmotion [0.2692, 0.4672] | Yes — same file | Yes |
| Fisher's exact (skin tone) | EXP-007 | N=46+32 | OR=5.88, p=0.0027 | Yes — same file | Yes |
| EXP-008 Neutral error rates | EXP-008 | N=76 (of 135) | ArcFace 43/76=0.5658; HSEmotion 34/76=0.4474 | Yes — `reports/arcface_error_analysis/neutral_error_analysis.csv` | Yes |
| EXP-008 skin-tone counts | EXP-008 | N=135 | Dark=46, Medium-Dark=32, Unknown=57 | Yes — `reports/arcface_error_analysis/skin_tone_analysis.csv` | Yes, matches EXP-007 exactly |
| EXP-008 subgroup accuracies | EXP-008 | N=46/32 | Dark: 0.4565/0.4565; Medium-Dark: 0.3125/0.1250 (ArcFace/HSEmotion) | Yes — same file | Yes, matches EXP-007 |

**No inconsistency was found across EXP-005, EXP-006, EXP-007, and EXP-008.** Every value that appears in more than one document (e.g., Neutral→Angry=18/76 appearing in both EXP-005 and EXP-008; skin-tone counts appearing in both EXP-007 and EXP-008) was independently re-derived from its underlying CSV in this validation pass and found identical to what was previously documented.

---

## Statistical Robustness — Consolidated

No new statistical test was introduced. The three existing tests are consolidated here as the final statistical record:

1. **McNemar's test (primary paired model comparison)**: b=20, c=26, p=0.4614. **Interpretation used throughout this synthesis: no statistically significant paired accuracy difference detected between ArcFace+LR and HSEmotion on this population.**
2. **Group-aware bootstrap 95% CIs**: ArcFace accuracy [0.3383, 0.4809]; HSEmotion accuracy [0.2692, 0.4672]. These are reported descriptively alongside McNemar, not as an independent significance test — overlapping CIs are consistent with, but do not by themselves prove, the absence of a difference.
3. **Fisher's exact test (skin-tone subgroup)**: OR=5.88, p=0.0027, on HSEmotion's Dark-vs-Medium-Dark correct/incorrect counts. Reported strictly as an association observed in this sample — not extended to a causal, demographic, or ethnicity conclusion.

---

## Reproducibility Verification

All figures in this document and in `docs/RESEARCH_FINDINGS.md` were re-read from the following unmodified source files during this validation pass (file timestamps confirmed unchanged from their R6/R7/R8 creation):

- `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv` (EXP-005)
- `reports/preprocessing_experiment_summary.csv` (EXP-006)
- `reports/arcface_evaluation/comparison_metrics.csv`, `statistical_tests.csv`, `skin_tone_analysis.csv` (EXP-007)
- `reports/arcface_error_analysis/overall_error_analysis.csv`, `neutral_error_analysis.csv`, `skin_tone_analysis.csv` (EXP-008)

No file above was modified in this phase. No model was retrained. No label was changed. No new data was introduced. No row-order join was used anywhere in this validation (all consistency checks compare already-identity-keyed values from each source CSV).

---

## Thesis-Ready Numerical Summary

**Common-subset comparison (N=135, do not mix with the historical table below):**

| Metric | ArcFace | HSEmotion |
|---|---|---|
| Evaluation N | 135 | 135 |
| Accuracy | 0.4074 | 0.3630 |
| Macro Precision | 0.2803 | 0.5898 |
| Macro Recall | 0.2931 | 0.2058 |
| Macro F1 | 0.2717 | 0.2489 |
| Neutral Error Rate | 0.5658 | 0.4474 |

**Historical HSEmotion (N=227, full dataset — kept separate, never combined with the table above):**

| Metric | Value |
|---|---|
| N | 227 |
| Accuracy | 22.47% |
| False-Angry Rate | 17.62% |
| Neutral → Angry | 23.68% |

---

## Research Question Readiness

| Research Question Component | Evidence Available | Status | Remaining Gap |
|---|---|---|---|
| Target population (dark-skinned, Papuan-sourced) | Video source confirmed (`pesta_babi.mp4`); skin-tone bucket data for 78/135 common-subset samples | Partial | No ethnicity metadata; 57/135 samples uncharacterized for skin tone |
| Baseline FER performance | HSEmotion accuracy fully characterized (227-sample and 135-sample subset) | Answered | None |
| Proposed method (ArcFace feature extraction + classifier) | Fully implemented and evaluated (R5–R7) | Answered | Only 5-class scope; frozen-embedding-only, no fine-tuning explored |
| Error pattern characterization (Neutral→Angry) | Fully characterized for HSEmotion; explicitly out-of-scope for ArcFace | Partial | ArcFace-side comparison structurally unavailable without more `Angry` ground truth |
| Skin-tone association | Descriptive + one Fisher's exact test performed | Partial | Small, uneven subgroups; only 2 of 4 possible buckets populated |
| Statistical validation of model comparison | McNemar + bootstrap CI performed | Answered | Result is a null finding (not significant), not a confirmed difference |
| Formal thesis RQ wording | Not present in repository | **Not established** | — |

**Per instruction, stated explicitly**: *The final wording of the research question remains a thesis-author decision and is not established by the experimental repository.* This document does not manufacture an official RQ.

---

## Final Research Story (Evidence Chain)

Each arrow below is backed by a specific artifact, not asserted without support:

```text
Pesta Babi source video (config/config.yaml: video.path)
        ↓
Semi-automatic dataset generation (src/fer_dataset/pipeline/*, validated Phases 0-11C)
        ↓
Manual ground-truth labeling (data/1408-1010-intermediate/manual_labels_export.csv, 227 samples)
        ↓
Class imbalance discovered: Angry=1, Disgust=2 (docs/R7_5_CLASS_DECISION.md Section 2-3)
        ↓
5-class defensible evaluation adopted (tools/train_arcface_classifier.py, MIN_CLASS_COUNT=5)
        ↓
HSEmotion baseline established (EXP-005: 22.47% accuracy, N=227)
        ↓
Observed Neutral→Angry pattern (EXP-005: 18/76=23.7%; reconfirmed identically in EXP-008 on N=135)
        ↓
ArcFace frozen feature extraction implemented (R5: 512-d embeddings, 178/227 successful)
        ↓
Logistic Regression classifier trained via grouped CV (R6: 135 usable samples, 5 classes)
        ↓
ArcFace vs HSEmotion paired comparison (EXP-007: accuracy 0.4074 vs 0.3630, McNemar p=0.4614)
        ↓
Error analysis (EXP-008: distributed ArcFace errors vs concentrated HSEmotion Neutral→Angry)
        ↓
Skin-tone secondary analysis (EXP-007/008: Dark vs Medium-Dark descriptive + Fisher's exact p=0.0027)
        ↓
Limitations consolidated (R9: 14 limitations, reports/final_research_validation/final_limitations.csv)
        ↓
Research conclusion: NOT drawn in this repository (thesis-author decision, Section "Research Question Readiness")
```

---

## Final Conclusion Boundaries

**What the data supports**: ArcFace + Logistic Regression achieved higher observed accuracy than HSEmotion on the common 135-sample, 5-class evaluation population, but the paired difference was not statistically significant.

**What the data suggests**: ArcFace and HSEmotion exhibit different error distributions, with HSEmotion showing a pronounced Neutral→Angry pattern that ArcFace's current 5-class configuration cannot be compared against.

**What remains unresolved**: whether the proposed ArcFace-based approach provides a statistically reliable improvement for FER on the target population — the current sample size and the non-significant McNemar result do not resolve this either way.

**What cannot be concluded** (explicitly rejected, matching `docs/RESEARCH_FINDINGS.md` Section 10): ArcFace is definitively superior; ArcFace solves false-Angry; ArcFace removes demographic bias; skin tone causes errors; Papuan ethnicity causes errors; HSEmotion is definitively biased against Papuan people; the dataset is 100% dark-skinned; 7-class ArcFace performance is known.

---

## Remaining Research Blockers (carried forward, not resolved by R9)

- P0: the official thesis research question remains undetermined by the repository (`docs/THESIS_RQ_ALIGNMENT.md` Section 1) — R9 does not resolve this; it is a thesis-author decision.
- P0: the "100% dark skin" narrative claim in `Tesis_Knowledge_Transfer_(1).md` remains unreconciled with the actual 58.8%/41.2% Dark/Medium-Dark split — still requires direct author confirmation.
- P1: a defensible 7-class ArcFace experiment requires new data collection; not attempted in R9, per explicit scope restriction.

See `docs/RESEARCH_FINDINGS.md` and `reports/final_research_validation/` for the full synthesis.
