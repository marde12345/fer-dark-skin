# Thesis RQ Alignment

> R2 — read-only research-framing audit, building on `docs/RESEARCH_EVIDENCE_AUDIT.md` (R1). No source code, notebooks, datasets, reports, or configuration were modified to produce this document.

---

## 1. Executive Summary

No official thesis Research Question, problem statement, objective, hypothesis, or contribution statement exists anywhere in this repository — confirmed again in this pass with a broader search (including "thesis title," "paper title," "research scope," "research aim," "proposal") that found nothing beyond what R1 already identified. The most authoritative research-framing document present is `Tesis_Knowledge_Transfer_(1).md` (Section 15 only), which is narrative/handoff notes, not a formal RQ statement.

The "100% dark skin" claim in that document is **contradicted** by the pipeline's own computed skin-tone data: the 85-row landmark-feature subset splits **58.8% Dark (50 rows) / 41.2% Medium-Dark (35 rows)** — two distinct buckets, not one. This is documented as a discrepancy, not corrected in the source document, and not used to alter any dataset, threshold, or result.

The evidence most strongly supports a research direction centered on **fairness/bias evaluation of an off-the-shelf FER model across skin-tone subgroups**, with a secondary, already-completed exploratory strand on **whether a specific preprocessing intervention (CLAHE) mitigates that bias** (it did not, per the recorded results). No statistical validation exists for any of this yet.

---

## 2. Official Thesis Framing

### Research Question
**Not found.** No file in the repository states a research question in any form (numbered RQ, prose question, or equivalent).

### Problem Statement
**Not found** as an explicit, labeled statement. The closest evidence is `Tesis_Knowledge_Transfer_(1).md` §15.4's implication (translated sense): the observed FER model failures are attributed to "bias representasi di training data HSEmotion" (representation bias in HSEmotion's training data) rather than lighting/contrast alone. This is an **interpretive conclusion drawn by the thesis author in that document**, not a problem statement framed at the start of the research.

### Objective
**Not found** as an explicit statement. `README.md`'s "Research Goal" section states: "The primary objective of this project is to develop a semi-automatic FER dataset generation pipeline that reduces manual annotation effort while maintaining high-quality labeled facial expression images suitable for research purposes." This describes the **dataset-generation pipeline's** objective, not a thesis research objective about FER model performance, fairness, or bias — these are different scopes, and conflating them would misrepresent the evidence.

### Hypothesis
**Not found** as a formally stated thesis hypothesis. Two narrower, experiment-scoped hypotheses exist and are evidenced:
- EXP-006's notebook header states its own hypothesis: adaptive CLAHE "reduces false Angry predictions and improves fairness across skin-tone groups" (`notebooks/preprocessing_experiment.ipynb`, cell 0) — **not supported** by its own recorded results (Section 6).
- `notebooks/data_audit.ipynb` cell 15 tests a narrower geometric hypothesis (false-Angry predictions show lower brow-lowering than true-Angry) — the notebook's own printed output states this is "weak/unsupported in this sample" (n=1 true-Angry group).

Neither is a thesis-level hypothesis; both are experiment-local.

### Contribution
**Not found.** No statement of intended or claimed research contribution exists in the repository.

---

## 3. Research Direction Supported by Evidence

Ranking by strength of existing, already-collected evidence (not by importance or novelty):

1. **Strongest support: FER model fairness/bias evaluation across skin-tone subgroups.** This is the only direction with a complete, executed, multi-metric analysis: overall accuracy (0.2247), per-skin-tone accuracy (Dark 0.44, Medium-Dark 0.1429), fairness gap (0.2971), per-skin-tone false-Angry rate (Dark 0.22, Medium-Dark 0.4571) — all from `notebooks/data_audit.ipynb` (cells 5, 9, 11) and `reports/audit_*.csv`. This is descriptive-only (no statistical test), but it is the most complete evidence thread in the repository.
2. **Moderate support: systematic misclassification-toward-"Angry" behavior.** A specific, well-evidenced error pattern (40/227 false-Angry, breakdown by true class, over-confidence on wrong Angry predictions) exists and is internally consistent across the notebook and `Tesis_Knowledge_Transfer_(1).md`'s independent narrative summary of the same numbers.
3. **Weaker, exploratory support: whether preprocessing (CLAHE) can mitigate the bias.** One variant tested, cleanly executed, negative result. This is evidence *against* one specific intervention, not evidence *for* a research direction — it is more naturally framed as a completed negative sub-experiment within direction (1) than as its own thesis pillar.
4. **Weakest support: landmark-geometry-based explanation of model errors.** Only descriptive comparisons exist, one of which rests on a single-sample group (n=1); the repository's own printed output already concludes this specific hypothesis is unsupported in-sample. This direction currently has the least evidentiary weight of the four.

---

## 4. Skin-Tone Claim Reconciliation

**Claim under review:** `Tesis_Knowledge_Transfer_(1).md` §15.5 states the dataset is "227 face crops, 100% kulit gelap" (100% dark skin), used in a narrative summary intended for an advisor presentation.

**Evidence checked:**
- `data/1408-1010-intermediate/manual_labels_export.csv`: 227 rows total (the full manually-labeled population this claim likely refers to).
- `data/1408-1010-intermediate/landmark_features.csv`: 85 of those 227 rows have a computed `skin_tone` value (the other 142 rows lack landmark data — MediaPipe did not detect ≥468 landmarks for those crops, per `docs/EXPERIMENT.md` EXP-000 — so skin tone is simply **not computed** for 142/227 rows, not necessarily "not dark").
- Of the 85 rows with a computed skin tone: **`Dark`: 50 rows (58.8%)`, `Medium-Dark`: 35 rows (41.2%)`. Zero rows fall into `Medium-Light` or `Light` (both are defined buckets in `src/fer_dataset/pipeline/landmark_analyzer.py:131-137` but empty in this data).

**Conclusion: Contradicted, with a caveat.**
- The narrow, literal claim — "100% dark skin" as a single undifferentiated category — is **contradicted**: the pipeline's own bucketing splits the population into two distinct categories (58.8% / 41.2%), not one.
- A broader, looser reading of the claim — "no light-skinned subjects are present" — is **not contradicted** by available evidence: `Light` and `Medium-Light` are indeed empty in the 85-row subset that has skin-tone data.
- **Coverage caveat**: this conclusion is based on the 85/227 (37.4%) subset that has computed skin-tone values. The skin-tone distribution of the other 142/227 rows (where landmark detection failed) is **unknown** — it cannot be assumed to match the 85-row subset's distribution.
- **Cannot determine** whether the "100% dark skin" claim in `Tesis_Knowledge_Transfer_(1).md` was written before this two-bucket split was computed, or whether it refers to a different dataset/version — no evidence in the repository establishes this document's exact composition date relative to when the skin-tone computation was run (both fall on 2026-08-15 per file timestamps, with insufficient granularity to establish order).

No dataset, threshold, or skin-tone bucket was altered to produce this conclusion — only existing data was counted.

---

## 5. Evidence Matrix

| Research Element | Current Evidence | Source | Status | Gap |
|---|---|---|---|---|
| RQ | None found | Repository-wide search | Missing | Obtain from thesis author/advisor |
| Objective | Pipeline-engineering objective only (README "Research Goal"); no thesis-research objective | `README.md` | Missing (thesis-level) | Distinguish pipeline objective from thesis research objective |
| Hypothesis | Two experiment-local hypotheses (CLAHE fairness improvement; brow-lowering geometry) | `notebooks/preprocessing_experiment.ipynb` cell 0; `notebooks/data_audit.ipynb` cell 15 | Found (experiment-level only) | No thesis-level hypothesis exists |
| Dataset | 227 manually-labeled face crops; 85 with landmark/skin-tone data; skin tone is Dark 58.8% / Medium-Dark 41.2% within that 85 | `data/1408-1010-intermediate/manual_labels_export.csv`, `landmark_features.csv` | Found, but partially characterized (142/227 rows have unknown skin tone) | Characterize or explain the 142 rows without landmark/skin-tone data |
| Baseline | Overall accuracy 0.2247, error rate 0.7753 | `notebooks/data_audit.ipynb` cell 5; `reports/audit_summary_metrics.csv` | Found | No statistical baseline (e.g., chance-level comparison, class-balance-adjusted metric) |
| Error Analysis | Confusion matrix, false-Angry breakdown by true class, confidence-vs-correctness comparison | `notebooks/data_audit.ipynb` cells 7, 11, 13 | Found (descriptive) | No per-class precision/recall/F1; no significance testing |
| Skin Tone | Accuracy and false-Angry rate by bucket, fairness gap | `notebooks/data_audit.ipynb` cells 9, 11; `reports/audit_per_skin_tone_accuracy.csv` | Found (descriptive) | No statistical test/effect size/CI; exact per-bucket sample sizes for the accuracy computation not separately tabulated |
| Landmark | Descriptive geometric comparisons (GT-based and predicted-label-based) | `src/fer_dataset/analysis/landmark_comparison.py`; `notebooks/data_audit.ipynb` cell 15 | Found (descriptive only) | GT-based comparison has n=1 in one group; no statistical layer anywhere |
| Preprocessing | CLAHE experiment fully executed; hypothesis not supported | `notebooks/preprocessing_experiment_executed.ipynb`; `reports/preprocessing_experiment_summary.csv` | Found (complete, negative result) | Only one variant tested; no repeated runs |
| Statistical Validation | None anywhere in the repository | Repository-wide (no `scipy.stats` or equivalent import found) | Missing | Needed for every quantitative comparison above before it can support a thesis claim |

---

## 6. Existing Evidence

### Baseline
Overall accuracy 0.2247, error rate 0.7753 (`notebooks/data_audit.ipynb` cell 5; `reports/audit_summary_metrics.csv`), computed over the full 227-row manually-labeled set against the original HSEmotion predictions. This is the single most complete, unambiguous number in the repository.

### Error Analysis
False-Angry rate 0.1762 (40/227); breakdown by true class — Neutral→Angry 18, Happy→Angry 8, Sad→Angry 6, Ambiguous→Angry 3, Fear→Angry 3, Surprise→Angry 2 (`notebooks/data_audit.ipynb` cell 11 output). Mean confidence: correct 0.5035, wrong 0.4418, true-Angry 0.4194, false-Angry 0.5968 — model is descriptively more confident when wrongly predicting Angry than when correctly predicting it (cell 13 output). A full confusion matrix image exists (`reports/assets/audit_confusion_matrix.png`) but no derived per-class precision/recall/F1 table.

### Skin Tone
Within the 85-row landmark subset: Dark 50 (58.8%), Medium-Dark 35 (41.2%). Accuracy: Dark 0.44, Medium-Dark 0.1429 (fairness gap 0.2971). False-Angry rate: Dark 0.22, Medium-Dark 0.4571, with group sizes 11 and 16 respectively out of the 40 false-Angry rows (`notebooks/data_audit.ipynb` cell 11 output; `reports/audit_per_skin_tone_accuracy.csv`). No statistical test performed.

### Landmark
Predicted-label-based comparison: Angry (n=28) mean brow_lowering_distance 0.131 vs. Neutral (n=29) 0.147, and three other geometric features, all descriptive only (`reports/landmark_comparison_summary.csv`; `src/fer_dataset/analysis/landmark_comparison.py`). Ground-truth-based comparison (true-Angry vs. false-Angry, within model-predicted-Angry rows): true-Angry n=1 (mean 0.0377), false-Angry n=27 (mean 0.1346) — the n=1 group cannot support a meaningful comparison, and the notebook's own output states the hypothesis is unsupported in this sample (`notebooks/data_audit.ipynb` cell 15).

### Preprocessing
CLAHE (Strategy B): accuracy 0.2247→0.1982 (−0.0264), false-Angry rate 0.1762→0.1806 (+0.0044), Medium-Dark false-Angry rate completely unchanged (0.3538→0.3538) (`reports/preprocessing_experiment_summary.csv`; `notebooks/preprocessing_experiment_executed.ipynb` cells 11, 13, 19). The stated hypothesis (CLAHE improves fairness/reduces false-Angry) is not supported by these results.

---

## 7. Core vs Supporting vs Exploratory Evidence

**Core thesis evidence** (directly measures the fairness/bias question that the available evidence most strongly supports as the research direction — Section 3, item 1):
- Overall accuracy, error rate, per-skin-tone accuracy, fairness gap, per-skin-tone false-Angry rate.

**Supporting evidence** (contextualizes the core finding but does not itself measure fairness/bias):
- Full confusion matrix; confidence-vs-correctness analysis; the specific false-Angry-by-true-class breakdown.

**Exploratory evidence** (a tested but so-far-unsuccessful intervention, or a descriptive analysis whose hypothesis was explicitly not supported by its own data):
- CLAHE preprocessing experiment (negative result, single variant).
- GT-based landmark geometry comparison (true-Angry vs. false-Angry; n=1 limits it to illustrative-only status).

**Engineering evidence** (supports trustworthiness of the above, is not itself a research finding):
- Pipeline reproducibility, annotation-alignment bug fix and validation, package restructuring, test suite, byte-identical output regeneration — all per `docs/RESEARCH_EVIDENCE_AUDIT.md` Section 9.

Predicted-label-based landmark comparison (`landmark_comparison.py`'s Angry-vs-Neutral analysis) sits between supporting and exploratory: it's a complete, methodologically consistent descriptive analysis, but with no statistical backing and no clearly established connection to a stated research question — conservatively classified as **exploratory** until an RQ clarifies whether it's meant to support a bias claim or a separate geometric-signal claim.

---

## 8. Missing Evidence

### P0
- The official thesis RQ itself — without it, "missing evidence" cannot be precisely scoped; everything below is inferred from the strongest-supported direction (Section 3), not a confirmed RQ.
- Characterization of the 142/227 rows lacking landmark/skin-tone data (Section 4) — needed before any fairness claim can be scoped as "representative of the dataset" versus "representative of the 37% subset that happened to have detectable landmarks."
- Reconciliation of the "100% dark skin" claim with the actual 58.8%/41.2% split, directly with the thesis author (Section 4).

### P1
- Per-class precision/recall/F1 (derivable from the existing confusion matrix without new data collection).
- Statistical test + effect size + confidence interval for the skin-tone accuracy/false-Angry-rate differences (the central fairness claim currently rests on raw group means over small, uneven groups).
- Exact sample sizes underlying every subgroup metric, tabulated in one place (currently scattered across notebook cell outputs).

### P2
- Additional preprocessing variants, only if the RQ (once obtained) still calls for a preprocessing-focused answer rather than the training-side intervention already proposed in `Tesis_Knowledge_Transfer_(1).md` §15.6 ("Strategy C").
- Statistical treatment of the landmark-geometry descriptive comparisons, only if an RQ establishes they matter to the thesis argument.

No experiment is recommended here purely because it is technically interesting — each item above is tied to strengthening or completing evidence for the fairness/bias direction identified as most strongly supported in Section 3.

---

## 9. Proposed Chapter 4 Evidence Structure

Based only on what exists or is clearly required to complete it (not a generic template):

```text
4.1 Dataset Characteristics
    — sample counts, manual-label coverage, skin-tone bucket distribution (with the
      142/227 uncharacterized-subset caveat stated explicitly), correcting the
      "100% dark skin" narrative claim

4.2 Baseline Model Performance
    — overall accuracy, error rate, confusion matrix

4.3 Error Analysis
    — false-Angry pattern, confidence-vs-correctness, (P1: per-class precision/recall/F1)

4.4 Skin-Tone Fairness Analysis
    — per-group accuracy, false-Angry rate, fairness gap, (P1: statistical validation)

4.5 Preprocessing Intervention (CLAHE) — Exploratory
    — hypothesis, method, result (explicitly negative), limitations

4.6 Landmark Geometry — Exploratory
    — descriptive comparison, explicit caveat on small-sample GT-based comparison

4.7 Discussion
    — synthesis, explicitly separating descriptive/associative findings from any
      causal or generalizable claim, per Section 7's core/supporting/exploratory split
```

This structure omits a separate "Research Question" framing chapter section only because none exists yet to describe — Section 4.1 onward assumes the fairness/bias direction (Section 3) is confirmed as the actual RQ once obtained; if the real RQ differs, this structure would need to be re-derived, not reused as-is.

---

## 10. Thesis Readiness

Unchanged from `docs/RESEARCH_EVIDENCE_AUDIT.md` Section 13 in substance; this pass adds the skin-tone reconciliation (Section 4 above), which downgrades confidence in "Dataset readiness" slightly further: it is 🟡 Partially ready, and the specific reason is now sharper — not just "limited bucket coverage" but a **confirmed contradiction** between the narrative dataset description and the pipeline's own computed distribution, plus an **unknown** skin-tone profile for 62.6% of the labeled population. Research question clarity and statistical validation remain 🔴 Not ready — no new evidence in this pass changes that.

---

## 11. Single Most Important Next Action

**Take the fairness/bias-across-skin-tone direction (Section 3, item 1) and the corrected skin-tone distribution (Section 4) to the thesis author/advisor together, as one conversation: confirm whether this is in fact the intended RQ, and get the "100% dark skin" claim corrected or explained before it propagates into any thesis-facing writing.**

This combines R1's single recommendation (get the official RQ) with this pass's most consequential finding (a factual dataset-description error): both block the same downstream work — writing Chapter 4 — and both are cheaper to resolve together in one conversation than sequentially. Everything else in Sections 8–9 is either derivable from existing data (P1 items) or contingent on this conversation's outcome (P2 items, and the exact shape of Chapter 4 itself).

---

## 12. Source Traceability

- `Tesis_Knowledge_Transfer_(1).md` (§15, in full)
- `docs/RESEARCH_EVIDENCE_AUDIT.md` (R1, in full)
- `docs/EXPERIMENT.md` (§EXP-000, §EXP-005, §EXP-006)
- `docs/ARCHITECTURE.md`, `docs/SDD.md`, `README.md`
- `notebooks/data_audit.ipynb` (cells 1, 3, 5, 7, 9, 11, 13, 15 — source + stored outputs)
- `notebooks/preprocessing_experiment.ipynb` (cell 0 — hypothesis statement)
- `notebooks/preprocessing_experiment_executed.ipynb` (cells 9, 11, 13, 15, 19 — frozen historical outputs; not modified)
- `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv`, `reports/preprocessing_experiment_summary.csv`, `reports/landmark_comparison_summary.csv`
- `data/1408-1010-intermediate/manual_labels_export.csv` (227-row count), `landmark_features.csv` (85-row count, skin-tone distribution: Dark 50/58.8%, Medium-Dark 35/41.2% — counted directly from this file for this document, not previously tabulated anywhere in the repository)
- `src/fer_dataset/pipeline/landmark_analyzer.py` (skin-tone bucket definitions, lines 131-137)
- `src/fer_dataset/analysis/landmark_comparison.py` (full source)
- Repository-wide text search (this session) for: research question, RQ, hypothesis, contribution, problem statement, research objective, thesis title, paper title, research scope, research aim, proposal — no additional matches beyond what R1 already found.
