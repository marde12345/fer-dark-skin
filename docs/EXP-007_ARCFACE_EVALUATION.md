# EXP-007 — ArcFace FER Evaluation

> First formal research evaluation phase (R7). Reports factual, descriptive results only — no thesis conclusion is drawn here (Section 12). Neither model was modified, retrained, or tuned based on these results. All artifacts are in `reports/arcface_evaluation/` (new directory; no historical report was overwritten).

---

## 1. Objective

Formally compare the frozen ArcFace + Logistic Regression system (R6) against the existing HSEmotion baseline, on a common, identity-matched evaluation subset, using the same ground-truth labels and class definitions for both.

---

## 2. Evaluation Population

| Population | N |
|---|---|
| All face crops | 227 |
| ArcFace embeddings (successful) | 178 |
| Valid (non-`Ambiguous`) GT labels, full dataset | 144 |
| ArcFace classifier population (R6, after rare-class exclusion) | 135 |
| HSEmotion predictions available | 227 |
| **Common evaluation subset** | **135** |

The common subset equals the full R6 ArcFace population, because every crop with an ArcFace embedding also has an HSEmotion prediction (HSEmotion runs on all 227 crops unconditionally) — the intersection is bounded entirely by ArcFace's own exclusions (detection-on-crop failures, `Ambiguous`/missing labels, rare classes), not by any HSEmotion-side gap. Joined by `face_filename` (exact identity), never row position — verified programmatically (see Section 22).

**Class distribution in the common subset**: `Neutral: 76, Happy: 32, Sad: 12, Surprise: 8, Fear: 7` — same 5 classes as R6 (`Angry` and `Disgust` excluded for insufficient samples, per R6).

**Explicit statement per instructions**: *The formal paired comparison is conducted on the five-class eligible population because two classes (`Angry`: 1 sample, `Disgust`: 2 samples) did not meet the predefined minimum sample requirement for the ArcFace classifier. This is not a complete seven-class evaluation.*

---

## 3. Methodology

- **ArcFace predictions**: exactly the 135 out-of-fold predictions from `data/intermediate/arcface_embeddings/classifier_predictions.csv` (R6) — not regenerated, not retrained.
- **HSEmotion predictions**: exactly `data/intermediate/annotations.csv`'s `label` column, restricted to the 135 common filenames, with HSEmotion's raw vocabulary (`Anger`, `Happiness`, `Sadness`) normalized to the manual `gt_label` vocabulary (`Angry`, `Happy`, `Sad`) using the same mapping already established in `notebooks/data_audit.ipynb` cell 3 — no other transformation.
- **Ground truth**: `manual_labels_export.csv`'s `gt_label`, identical for both models.
- **Asymmetry, stated explicitly**: ArcFace's classifier can only output one of the 5 eligible classes (by construction — it was never trained on `Angry`/`Disgust`). HSEmotion's raw output can be any of its 7-class vocabulary. Predictions falling outside the 5 eligible classes are **not excluded from evaluation** — they are counted as incorrect against the true label (standard multi-class precision/recall/F1 behavior with a fixed `labels=` set), and shown in a dedicated "Other" column in HSEmotion's confusion matrix (Section 7). This asymmetry is a direct, unavoidable consequence of R6's rare-class exclusion and is treated as a headline limitation (Section 13), not glossed over.

---

## 4. ArcFace Results (common subset, N=135)

| Metric | Value |
|---|---|
| Accuracy | 0.4074 |
| Macro Precision | 0.2803 |
| Macro Recall | 0.2931 |
| Macro F1 | 0.2717 |

Per-class:

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Fear | 0.0000 | 0.0000 | 0.0000 | 7 |
| Happy | 0.4048 | 0.5313 | 0.4595 | 32 |
| Neutral | 0.7174 | 0.4342 | 0.5410 | 76 |
| Sad | 0.1364 | 0.2500 | 0.1765 | 12 |
| Surprise | 0.1429 | 0.2500 | 0.1818 | 8 |

(Support values are ground-truth counts per class in the subset, matching Section 2's class distribution.)

---

## 5. HSEmotion Same-Subset Results (N=135)

| Metric | Value |
|---|---|
| Accuracy | 0.3630 |
| Macro Precision | 0.5898 |
| Macro Recall | 0.2058 |
| Macro F1 | 0.2489 |

Per-class:

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Fear | 0.0323 | 0.1429 | 0.0526 | 7 |
| Happy | 1.0000 | 0.1250 | 0.2222 | 32 |
| Neutral | 0.7500 | 0.5526 | 0.6364 | 76 |
| Sad | 0.1667 | 0.0833 | 0.1111 | 12 |
| Surprise | 1.0000 | 0.1250 | 0.2222 | 8 |

Note the high precision / low recall pattern for `Happy` and `Surprise`: HSEmotion rarely predicts these classes on this subset, but is usually correct when it does (consistent with HSEmotion's own strong tendency to predict `Angry`/`Neutral`/`Fear` overall — see the confusion matrix, Section 7).

---

## 6. Historical HSEmotion Baseline (full 227-sample dataset — kept separate, not replaced)

| Metric | Value | Source |
|---|---|---|
| N | 227 | `reports/audit_summary_metrics.csv` |
| Overall accuracy | 0.2247 | same |
| Error rate | 0.7753 | same |
| False-Angry rate | 0.1762 | same |
| Fairness gap (Dark vs. Medium-Dark) | 0.2971 | same |
| Accuracy — Dark | 0.4400 | same |
| Accuracy — Medium-Dark | 0.1429 | same |

**This historical figure is not comparable to Section 5's same-subset HSEmotion accuracy (0.3630)** without accounting for two differences: (a) the historical figure evaluates all 7 classes over 227 samples (including `Angry`/`Disgust`/`Ambiguous`-adjacent cases and detection-on-crop failures excluded here), and (b) the historical figure's "correct" includes exact matches on `Angry`/`Disgust`, which by definition cannot occur in this smaller, 5-class-restricted, 135-sample subset. The two numbers answer different questions and must not be conflated.

---

## 7. Confusion Matrix

**ArcFace+LR** (rows = ground truth, columns = predicted; order: Fear, Happy, Neutral, Sad, Surprise):

```
              Fear  Happy  Neutral  Sad  Surprise
Fear             0      3        2    2         0
Happy            3     17        4    3         5
Neutral          8     15       33   14         6
Sad              0      3        5    3         1
Surprise         0      4        2    0         2
```

**HSEmotion** (rows = ground truth, columns = predicted; order: Fear, Happy, Neutral, Sad, Surprise, **Other** [any HSEmotion label outside the 5 eligible classes, i.e. `Angry`/`Disgust`]):

```
              Fear  Happy  Neutral  Sad  Surprise  Other
Fear             1      0        2    1         0      3
Happy           12      4        8    0         0      8
Neutral         13      0       42    3         0     18
Sad              4      0        1    1         0      6
Surprise         1      0        3    1         1      2
```

Full numeric CSVs: `reports/arcface_evaluation/confusion_matrix_arcface.csv`, `confusion_matrix_hsemotion.csv`. Rendered images: `confusion_matrix_arcface.png`, `confusion_matrix_hsemotion.png`.

The HSEmotion "Other" column's `Neutral` row (18) is exactly the historical Neutral→Angry+Disgust-adjacent false-prediction count discussed next.

---

## 8. False-Angry Analysis

Denominator convention matches `notebooks/data_audit.ipynb` cell 11: rate = count / total evaluated N (not restricted to the `Neutral` subset for the headline rate).

| | HSEmotion (common subset, N=135) | ArcFace+LR (common subset, N=135) |
|---|---|---|
| False-Angry count | 37 | **0** |
| False-Angry rate (of 135) | 0.2741 | **0.0000** |
| Neutral→Angry count | 18 | 0 |
| Neutral total (in subset) | 76 | 76 |
| Neutral→Angry rate (of Neutral) | 0.2368 | 0.0000 |
| Breakdown by true class | Neutral 18, Happy 8, Sad 6, Fear 3, Surprise 2 | — (none) |

**Critical caveat, stated as plainly as possible**: ArcFace's false-Angry rate is exactly 0 **by construction**, not because it resolved the false-Angry error pattern. The ArcFace classifier was trained on only 5 classes (`Angry` excluded in R6 for having only 1 ground-truth sample) — it is **structurally incapable of ever predicting "Angry."** This is not evidence that a frozen-ArcFace-embedding approach fixes HSEmotion's Angry-over-prediction behavior; it is an artifact of the class-eligibility filtering applied for an unrelated reason (insufficient sample count). This must not be reported as "ArcFace reduces false-Angry rate" in any subsequent summary.

The historical HSEmotion Neutral→Angry count (18, per `docs/EXPERIMENT.md` EXP-005) matches exactly the same-subset count found here (18) — meaning all 18 historical Neutral→Angry cases fall inside this 135-sample common subset.

---

## 9. Skin-Tone Analysis

Skin-tone values taken directly from `landmark_features.csv` (unchanged methodology, no recomputation, no imputation of missing values).

| Skin Tone | N | ArcFace Accuracy | HSEmotion Accuracy | ArcFace False-Angry Rate | HSEmotion False-Angry Rate |
|---|---|---|---|---|---|
| Dark | 46 | 0.4565 | 0.4565 | 0.0000 | 0.2174 |
| Medium-Dark | 32 | 0.3125 | 0.1250 | 0.0000 | 0.5000 |
| Unknown (no skin-tone value) | 57 | 0.4211 | 0.4211 | 0.0000 | 0.1930 |

(ArcFace and HSEmotion accuracy coincide exactly for `Dark` and `Unknown` — this is a numerical coincidence at this sample size, not a methodological artifact; both models were evaluated on the identical filenames within each subgroup.)

**Observed pattern**: HSEmotion's accuracy is descriptively lower and false-Angry rate descriptively higher in `Medium-Dark` than `Dark`, consistent with the historical full-dataset finding (`docs/RESEARCH_FRAMING.md` Section 4). ArcFace shows the same directional accuracy gap (0.4565 vs. 0.3125) but, again, a structurally-zero false-Angry rate for the reason stated in Section 8.

**57/135 (42%) samples have no skin-tone value** in this subset — reported as a distinct "Unknown" group, not imputed, not excluded from the overall metrics (Sections 4-5), only excluded from the skin-tone-stratified breakdown's Dark/Medium-Dark rows.

---

## 10. Statistical Comparison

### McNemar's Test (paired, ArcFace vs. HSEmotion correctness on the same 135 samples)

| | HSEmotion Correct | HSEmotion Wrong |
|---|---|---|
| **ArcFace Correct** | 29 | 26 |
| **ArcFace Wrong** | 20 | 60 |

Exact binomial McNemar test on the discordant pairs (b=20, c=26): **p = 0.4614**.

**Interpretation**: not statistically significant at conventional thresholds. The observed accuracy difference (0.4074 vs. 0.3630) is **not distinguishable from chance** given this sample size and discordant-pair count. This says nothing about practical significance in either direction — it says the data here do not provide strong evidence of a genuine difference.

### Bootstrap 95% Confidence Intervals (group-aware — resampling temporal blocks, not individual samples, since samples within a block are not independent)

| Metric | Point Estimate | 95% CI |
|---|---|---|
| ArcFace Accuracy | 0.4074 | [0.3383, 0.4809] |
| HSEmotion Accuracy | 0.3630 | [0.2692, 0.4672] |
| ArcFace False-Angry Rate | 0.0000 | [0.0000, 0.0000] (degenerate — see Section 8 caveat) |
| HSEmotion False-Angry Rate | 0.2741 | [0.2072, 0.3521] |

The accuracy CIs overlap substantially, consistent with McNemar's non-significant result.

### Fisher's Exact Test (skin-tone subgroup comparison — the single most research-relevant comparison selected, per instruction not to test every metric)

**HSEmotion accuracy, Dark vs. Medium-Dark** (2×2 correct/incorrect table): `[[21, 25], [4, 28]]`, odds ratio = 5.88, **p = 0.0027**.

**Interpretation**: this specific difference (HSEmotion's accuracy being lower in Medium-Dark than Dark) **is** statistically significant at p<0.01 in this sample. This is the one skin-tone-related result in this evaluation with formal statistical support — reported as such, not overstated: it is a within-model, within-dataset descriptive association test, not a causal claim, and not extended to ArcFace (ArcFace's Dark/Medium-Dark sample sizes are the same, but no separate Fisher test was run for it, per the instruction to select only the most relevant comparison rather than testing everything).

---

## 11. Error Analysis

| Error Type | HSEmotion (N=135) | ArcFace+LR (N=135) |
|---|---|---|
| False-Angry (predicted Angry, GT≠Angry) | 37 (27.4%) | 0 (structurally impossible — Section 8) |
| Neutral→Angry specifically | 18 (23.7% of Neutral) | 0 (structurally impossible) |
| Other confusion (wrong, not Angry) | 60 total wrong − 37 false-Angry = 23 | 80 total wrong (135 − 55 correct) |

**Dominant observed pattern for HSEmotion**: over-prediction toward "Angry"/"Other"-bucket labels, especially from `Neutral` ground truth (18/76 Neutral samples, the single largest source) — consistent with the historical EXP-005 finding, reproduced here on the same-subset population.

**Dominant observed pattern for ArcFace+LR**: the confusion matrix (Section 7) shows the largest off-diagonal mass is `Neutral`→`Happy` (15) and `Neutral`→`Fear` (8), i.e., a different error pattern from HSEmotion's Angry-directed bias — ArcFace's errors do not cluster toward any single predicted class as strongly as HSEmotion's cluster toward "Other" (Angry/Disgust).

This is an **observed pattern**, not a hypothesized cause: this report does not claim why HSEmotion over-predicts Angry or why ArcFace's errors distribute differently — only what the confusion matrices show.

---

## 12. Findings

Classified per the required categories — **no thesis conclusion is drawn**:

- **Performance**: ArcFace+LR shows **similar** performance to HSEmotion on this common subset (accuracy 0.4074 vs. 0.3630, macro F1 0.2717 vs. 0.2489) — the difference is **not** statistically significant (McNemar p=0.4614; overlapping bootstrap CIs).
- **False-Angry behavior**: **not meaningfully comparable** between the two systems in this evaluation — ArcFace's zero false-Angry rate is a structural artifact of class exclusion (Section 8), not an observed behavioral improvement.
- **Skin-tone pattern**: **observed difference** for HSEmotion (Dark accuracy 0.4565 vs. Medium-Dark 0.1250, statistically significant via Fisher's exact test, p=0.0027). For ArcFace, an **observed difference in the same direction** (0.4565 vs. 0.3125) exists but was not separately statistically tested.
- **Statistical evidence**: **not significant** for the overall ArcFace-vs-HSEmotion accuracy comparison (McNemar); **significant** for the HSEmotion Dark-vs-Medium-Dark skin-tone comparison (Fisher's exact).

---

## 13. Limitations

- **The false-Angry/Neutral→Angry comparison between models is not valid** — ArcFace cannot predict `Angry` at all in this experiment (Section 8). Any future comparison of this specific error mode requires either including `Angry` in the ArcFace classifier (which R6 explicitly could not do with only 1 ground-truth sample) or restricting the comparison to a metric that doesn't structurally favor the class-restricted model.
- **Small, uneven per-class sample sizes**: `Fear` (7) and `Surprise` (8) are small enough that their precision/recall/F1 values (Section 4-5) are unstable — small changes in a handful of predictions would shift them substantially.
- **57/135 samples (42%) have unknown skin tone** — the skin-tone-stratified analysis (Section 9) covers only 58% of the common subset.
- **No formal ethnicity/Papuan-identity metadata exists** — per `docs/RESEARCH_FRAMING.md` Section 4, any statement connecting these results to "Papuan faces" specifically remains a **researcher observation**, not something this quantitative evaluation can independently establish. This evaluation can and does quantify expression-prediction errors and skin-tone-associated accuracy differences (Section 9-10) — it cannot attribute either to ethnicity, since skin-tone bucket (a LAB-luminance heuristic) is not an ethnicity label and no ethnicity variable exists to test against.
- **Group-aware bootstrap, not fully independent-sample bootstrap**: the 16 temporal groups from R6 were reused as resampling units; this reduces but does not eliminate potential non-independence between samples (Section 8 of `docs/ARCFACE_EXPERIMENT_DESIGN.md`'s acknowledged limitation).
- **Prediction probabilities are not calibrated confidence** for either model — HSEmotion's softmax confidence and the Logistic Regression's `predict_proba` output are both raw classifier outputs; no calibration analysis (e.g., reliability diagrams, Brier score) was performed, per instruction to keep this out of scope for R7.
- **This is a single dataset, single video, single classifier configuration** — no generalization beyond this specific evaluation is implied.

---

## 14. Evidence Reuse

| Prior Evidence | Status |
|---|---|
| HSEmotion 22.47% (full 227-sample accuracy) | **Reused directly**, kept in a separate historical-baseline table (Section 6), not replaced |
| Historical false-Angry analysis (0.1762 rate, Neutral→Angry=18) | **Recomputed on common subset** (Section 8) — the recomputed 18/76 Neutral→Angry count exactly matches the historical 18, confirming full overlap; the historical full-227 rate (0.1762) remains valid for its own population and is not superseded |
| Historical skin-tone analysis (Dark 0.44, Medium-Dark 0.1429 accuracy) | **Recomputed on common subset** (Section 9) — same values for Dark/Medium-Dark HSEmotion accuracy on this subset as the historical figures (0.4565 vs 0.44 differs slightly because the common subset (46 Dark samples) differs slightly from the full-dataset skin-tone-eligible population) |
| CLAHE experiment (EXP-006) | **Not applicable** — orthogonal intervention (image preprocessing before HSEmotion), not involved in this ArcFace-vs-HSEmotion comparison |
| Landmark geometry analysis (`landmark_comparison.py`) | **Not applicable** — answers a different question (geometric correlates of predicted labels), not reused or superseded by this evaluation |

Nothing was deleted or overwritten; `reports/audit_summary_metrics.csv`, `reports/landmark_comparison_summary.csv`, and all EXP-005/EXP-006 artifacts remain exactly as they were.

---

## 15. Source Traceability

- `docs/ARCFACE_EXPERIMENT_DESIGN.md` (R4), `docs/METHODOLOGY_RECONCILIATION.md` (R3), `docs/RESEARCH_FRAMING.md` (R2.5), `docs/THESIS_RQ_ALIGNMENT.md` (R2), `docs/RESEARCH_EVIDENCE_AUDIT.md` (R1), `docs/EXPERIMENT.md` (EXP-005, EXP-006, EXP-007)
- `data/intermediate/arcface_embeddings/classifier_predictions.csv` (R6 OOF predictions, unmodified)
- `data/intermediate/annotations.csv` (HSEmotion predictions, unmodified)
- `data/1408-1010-intermediate/manual_labels_export.csv` (ground truth, unmodified)
- `data/1408-1010-intermediate/landmark_features.csv` (skin-tone values, unmodified)
- `notebooks/data_audit.ipynb` cell 3 (HSEmotion label-normalization mapping, reused identically)
- `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv` (historical baseline, Section 6)
- `tools/evaluate_arcface_vs_hsemotion.py` (this evaluation's implementation)
- `reports/arcface_evaluation/` (all generated artifacts: `comparison_metrics.csv`, `per_class_metrics.csv`, `confusion_matrix_arcface.{csv,png}`, `confusion_matrix_hsemotion.{csv,png}`, `false_angry_analysis.csv`, `skin_tone_analysis.csv`, `statistical_tests.csv`, `evaluation_predictions.csv`)
