# EXP-008 — ArcFace/HSEmotion Error & Skin-Tone Analysis

> R8 — descriptive analysis only, using exclusively the R7 common evaluation artifact (`reports/arcface_evaluation/evaluation_predictions.csv`). No model retrained, no label changed, no sample added/removed, no skin-tone recomputation, no new statistical test beyond what R7 already performed. All outputs are new files in `reports/arcface_error_analysis/`; `reports/arcface_evaluation/` and every historical artifact remain unmodified (verified by file timestamp, Section "Validation").

---

## 1. Analysis Population

Exactly the R7 common evaluation population — recomputed by direct inspection, not assumed:

| Check | Result |
|---|---|
| N | 135 |
| Unique `face_filename` IDs | 135 (no duplicates) |
| GT classes present | Fear, Happy, Neutral, Sad, Surprise |
| ArcFace predicted classes present | Fear, Happy, Neutral, Sad, Surprise (no out-of-space predictions — verified programmatically) |
| HSEmotion predicted classes present | Angry, Fear, Happy, Neutral, Sad, Surprise |
| Every sample has both models' predictions | Yes (source file is the R7 joined artifact) |

---

## 2. ArcFace Overall Error Analysis (N=135)

| Ground Truth | N | Correct | Incorrect | Accuracy | Error Rate |
|---|---|---|---|---|---|
| Fear | 7 | 0 | 7 | 0.0000 | 1.0000 |
| Happy | 32 | 17 | 15 | 0.5313 | 0.4688 |
| Neutral | 76 | 33 | 43 | 0.4342 | 0.5658 |
| Sad | 12 | 3 | 9 | 0.2500 | 0.7500 |
| Surprise | 8 | 2 | 6 | 0.2500 | 0.7500 |

`Fear` (N=7) shows 0% accuracy — flagged, not overinterpreted: at 7 samples, this is consistent with either a genuinely weak signal for this class or simple small-sample noise; not distinguishable with this data.

---

## 3. HSEmotion Overall Error Analysis (same 135 samples — NOT the historical 227)

| Ground Truth | N | Correct | Incorrect | Accuracy | Error Rate |
|---|---|---|---|---|---|
| Fear | 7 | 1 | 6 | 0.1429 | 0.8571 |
| Happy | 32 | 4 | 28 | 0.1250 | 0.8750 |
| Neutral | 76 | 42 | 34 | 0.5526 | 0.4474 |
| Sad | 12 | 1 | 11 | 0.0833 | 0.9167 |
| Surprise | 8 | 1 | 7 | 0.1250 | 0.8750 |

---

## 4. Neutral Error Analysis (core analysis)

| Model | Neutral N | Correct Neutral | Neutral Error Rate | Dominant Wrong Class | Count |
|---|---|---|---|---|---|
| ArcFace+LR | 76 | 33 | 0.5658 | Happy | 15 |
| HSEmotion | 76 | 42 | 0.4474 | Angry | 18 |

Full breakdown of wrong predictions for GT=Neutral:

| Predicted | ArcFace | HSEmotion |
|---|---|---|
| Neutral (correct) | 33 | 42 |
| Happy | 15 | 0 |
| Sad | 14 | 3 |
| Surprise | 6 | 0 |
| Fear | 8 | 13 |
| **Angry** | **N/A (not in label space)** | **18** |
| **Disgust** | **N/A (not in label space)** | **0** |

Per instruction: `Angry`/`Disgust` are marked `N/A` for ArcFace, not `0` — a `0` would misleadingly imply "ArcFace never makes this error" when the correct statement is "this error is undefined for ArcFace's classifier."

---

## 5. General Error Taxonomy

Full pairwise confusion counts: `reports/arcface_error_analysis/error_taxonomy.csv`. Dominant patterns, observed (not explained):

**ArcFace+LR**:
- Dominant confusion: `Neutral→Happy` (15)
- Second: `Neutral→Sad` (14)
- Errors are **distributed** across several target classes for `Neutral`, rather than concentrated in one.

**HSEmotion**:
- Dominant confusion: `Neutral→Angry` (18)
- Second: `Happy→Fear` (12, from `overall_error_analysis`/`error_taxonomy.csv`)
- Errors are more **concentrated**: `Neutral→Angry` alone accounts for a larger single share of that class's errors (18/34 = 52.9% of Neutral's wrong predictions) than ArcFace's largest single wrong-class share (15/43 = 34.9%).

No explanation for *why* either pattern occurs is offered — only what the prediction data shows.

---

## 6. Comparing Error Distributions

- **Neutral errors**: ArcFace has *more* total Neutral errors (43 vs. 34) but a *less concentrated* distribution across wrong classes; HSEmotion has fewer total Neutral errors but a large fraction of them land specifically on `Angry`.
- **Dominant wrong class differs**: ArcFace → `Happy`; HSEmotion → `Angry`. These are different failure modes, not the same error under a different name.
- **Concentration**: HSEmotion's errors are more concentrated on a single target class (`Angry`, for `Neutral`) than ArcFace's, which spreads more evenly across `Happy`/`Sad`/`Fear`.
- No new hypothesis test was run here — R7's McNemar test remains the primary paired significance result (p=0.4614, not significant for overall accuracy).

---

## 7. Correct/Incorrect Probability Analysis — Scope Limitation

**Not performed in this phase.** The R7 common-evaluation artifact (`evaluation_predictions.csv`) that this analysis is scoped to use does not carry per-sample probability columns (ArcFace's OOF probabilities live in a separate R6 artifact, `classifier_predictions.csv`; HSEmotion's confidence lives in `data/intermediate/annotations.csv`). Joining a second/third artifact to recover probabilities was judged out of scope for a phase explicitly bounded to "use only existing artifacts" in the form R7 already assembled them, rather than reconstructing a new joined population. This is recorded as a limitation, not silently skipped — a future phase could add probability/confidence analysis using the already-existing per-model artifacts without any new experiment.

---

## 8. Skin-Tone Population (recomputed directly from the R7 artifact, not assumed)

| Skin Tone | N |
|---|---|
| Dark | 46 |
| Medium-Dark | 32 |
| Unknown | 57 |
| **Total** | **135** |

Matches the R7-reported counts exactly — confirmed independently, not merely copied forward. `Unknown` is reported as its own row and explicitly **not** treated as a skin-tone group in any accuracy/performance calculation below (`N/A` entries, not imputed).

---

## 9. Skin-Tone Performance

| Skin Tone | N | ArcFace Accuracy | HSEmotion Accuracy |
|---|---|---|---|
| Dark | 46 | 0.4565 | 0.4565 |
| Medium-Dark | 32 | 0.3125 | 0.1250 |
| Unknown | 57 | N/A | N/A |

(Macro F1 by skin-tone subgroup was not computed — per-subgroup, per-class counts are small enough, especially in `Medium-Dark`, that a 5-class macro F1 would rest on several near-empty class×subgroup cells; reported as accuracy only, per the instruction to compute macro F1 "if meaningful.")

---

## 10. Skin-Tone Error Analysis

| Skin Tone | N | ArcFace Neutral Error Rate | HSEmotion Neutral Error Rate |
|---|---|---|---|
| Dark | 46 | 0.5600 | 0.3200 |
| Medium-Dark | 32 | 0.8462 | 0.8462 |

For `Medium-Dark`, ArcFace and HSEmotion's Neutral error rates are numerically identical (0.8462) — noted as a coincidence at this small subgroup size (13 Neutral samples in Medium-Dark; not independently verified as anything beyond coincidence).

**Re-examination of the R7 Dark-vs-Medium-Dark finding**: the direction of the descriptive HSEmotion accuracy gap (Dark 0.4565 > Medium-Dark 0.1250) **is still present** in this same population — this is the identical 135-sample subset R7 already tested with Fisher's exact test (p=0.0027, `docs/EXP-007_ARCFACE_EVALUATION.md` Section 10). This document does not re-run that test (R7 already performed it); it confirms the underlying descriptive numbers are unchanged, since this analysis draws on the exact same artifact.

---

## 11. Fairness Interpretation

**Permitted framing used throughout this document**: *"A descriptive difference in accuracy and Neutral-error-rate was observed between Dark and Medium-Dark samples, in the same direction for both models."*

**Not claimed**: that HSEmotion (or ArcFace) is "biased against" Medium-Dark-skin-tone individuals, or any demographic group. The dataset contains a **skin-tone bucket** (a LAB-luminance-derived heuristic) — an **association** between this bucket and model accuracy is observed; no **causal** claim is made, and no **demographic/ethnicity** claim is made, since no ethnicity field exists to test against.

---

## 12. Historical Neutral → Angry Evidence

| Population | Neutral→Angry | Rate |
|---|---|---|
| Historical full dataset (N=227, HSEmotion only) | 18/76 | 23.7% (`docs/EXPERIMENT.md` EXP-005) |
| R7/R8 common evaluation subset (N=135, HSEmotion) | 18/76 | 23.7% (this document, Section 4) |

**These two populations are not identical in size (227 vs. 135) but happen to share the exact same Neutral→Angry numerator and denominator** — meaning all 18 historical Neutral→Angry cases, and the full 76-sample Neutral ground-truth group, are entirely contained within the smaller common-evaluation subset. This was already noted in `docs/EXP-007_ARCFACE_EVALUATION.md` Section 8 and is reconfirmed here from the R8 artifact independently.

**Framing, per instruction**: this finding is evidence **motivating** the investigation into whether an alternative facial representation (ArcFace) would behave differently — it is explicitly **not** proof that ArcFace solves the problem, since ArcFace's classifier cannot predict `Angry` at all (Section 4, R7.5). The comparable, valid ArcFace-side evidence is the general Neutral-misclassification behavior in Section 4 (56.6% Neutral error rate, dominant wrong class `Happy`), not a `Neutral→Angry`-specific figure.

---

## 13. Papuan Interpretation

*The researcher observed apparent Neutral-to-Angry misclassification among Papuan faces during dataset inspection. However, ethnicity is not encoded as a formal dataset attribute, so the current quantitative analysis cannot independently estimate a Papuan-specific error rate.* Skin tone (Section 8-11) is not used, and must not be used, as a proxy for ethnicity in this or any other analysis in this repository — it is a LAB-luminance bucket, not an ethnicity label, and no dataset field encodes Papuan identity.

---

## 14. Finding-Strength Classification

| Finding | Evidence | Strength | Limitation |
|---|---|---|---|
| ArcFace accuracy vs. HSEmotion | 0.4074 vs. 0.3630 (recomputed: 55/135 vs. 49/135), N=135, McNemar p=0.4614 | **Moderate** | Not statistically significant; small/uneven per-class N; single dataset/video |
| ArcFace Neutral error behavior | N=76, error rate 0.5658, dominant wrong class Happy (15) | **Moderate** | Descriptive only; no significance test; cannot predict Angry/Disgust |
| HSEmotion Neutral→Angry (common subset) | 18/76 = 23.7% | **Strong** | Population is the 135-sample subset, not the full 227 |
| HSEmotion Neutral→Angry (historical, full dataset) | 18/76 = 23.7% (`docs/EXPERIMENT.md` EXP-005) | **Strong** | Different population (N=227); numerically identical here but not derived from the same denominator conceptually |
| Dark vs. Medium-Dark performance (HSEmotion) | R7 Fisher's exact p=0.0027; reconfirmed descriptively here (0.4565 vs. 0.1250) | **Moderate** | Statistically significant in-sample; small subgroups; association only, not causal |
| Papuan-specific error effect | No ethnicity field exists | **Unsupported** | Cannot be quantitatively estimated with current metadata |
| ArcFace false-Angry = 0 | Structural: Angry excluded from label space | **Unsupported (as improvement claim)** | Must never be interpreted as a behavioral finding |

Full machine-readable version: `reports/arcface_error_analysis/finding_strength.csv`.

---

## 15. Thesis-Ready Findings

| # | Factual Statement | Supporting Metric | Population | Limitation |
|---|---|---|---|---|
| 1 | HSEmotion systematically misclassifies a substantial share of Neutral expressions as Angry | 18/76 (23.7%) Neutral→Angry, both in the full 227-sample historical set and the 135-sample common subset | N=227 (historical) / N=135 (common subset) | Descriptive; no ground-truth-encoded ethnicity to test subgroup-specificity |
| 2 | On the same 135-sample subset, ArcFace+LR and HSEmotion show statistically indistinguishable overall accuracy | 0.4074 vs. 0.3630, McNemar p=0.4614 | N=135 | Not significant; should not be read as "equivalent," only as "not distinguished by this test at this sample size" |
| 3 | ArcFace and HSEmotion exhibit different dominant Neutral-confusion patterns | ArcFace→Happy (15); HSEmotion→Angry (18) | N=76 (Neutral subset of the 135) | Observed pattern only; no causal explanation offered |
| 4 | HSEmotion's accuracy and Neutral-error-rate differ descriptively between Dark and Medium-Dark skin-tone buckets, in the same direction for both models | HSEmotion accuracy 0.4565 (Dark) vs. 0.1250 (Medium-Dark), Fisher's exact p=0.0027 (R7) | N=46 (Dark) / N=32 (Medium-Dark) | Association, not causation; no ethnicity metadata; small subgroup sizes |
| 5 | ArcFace's structural inability to predict Angry/Disgust means its false-Angry rate cannot be compared to HSEmotion's | 0 (ArcFace) vs. 37/135 (HSEmotion), R7 Section 8 | N=135 | Not a behavioral finding — must be presented with this caveat every time it is cited |

No causal claims are made in any of the five statements above.

---

## 16. What This Phase Does NOT Conclude

Explicitly, per instruction — none of the following is concluded by R8 (or any prior phase) unless already directly supported and cited above:

- ArcFace does **not** eliminate false-Angry errors (the metric is structurally undefined for it, Section 4/12).
- ArcFace is **not** shown to be statistically superior to HSEmotion (McNemar p=0.4614, not significant).
- HSEmotion is **not** definitively shown to be biased against a demographic group (only a skin-tone-bucket association is shown; no demographic/ethnicity variable exists).
- Skin tone is **not** shown to cause FER errors (association only).
- Papuan ethnicity is **not** shown to cause FER errors (no ethnicity metadata exists at all).
- ArcFace is **not** "better" because it has 0 Angry predictions (structural artifact, not a behavioral result).
- CLAHE's effect on ArcFace is **not** addressed by this phase (CLAHE was only ever tested against HSEmotion, EXP-006; no CLAHE+ArcFace experiment exists).
- Landmark geometry is **not** shown to explain any of the errors analyzed here (landmark-based analysis, EXP evidence in `reports/landmark_comparison_summary.csv`, is a separate, purely descriptive analysis not cross-referenced against these specific error cases in this phase).

---

## 17. Visualizations

- `confusion_matrix_arcface.png`, `confusion_matrix_hsemotion.png` — full 5-class (+"Other" for HSEmotion) confusion matrices on the 135-sample common subset.
- `neutral_prediction_distribution.png` — side-by-side predicted-class counts for the 76 ground-truth-Neutral samples, both models.
- `skin_tone_accuracy_comparison.png` — accuracy by skin tone (Dark, Medium-Dark only — `Unknown` excluded from this plot since it is not a skin-tone group), both models, exact counts labeled.

No additional plots were created, per the instruction to avoid excessive visualization.

---

## Validation

- Population: N=135, 135 unique IDs, all samples have both models' predictions, GT identical for both — confirmed programmatically in `tools/analyze_arcface_errors.py`'s assertions (see script output).
- ArcFace predictions confirmed to contain only its 5 valid classes (assertion in script; would have raised `AssertionError` otherwise).
- HSEmotion predictions read verbatim from the R7 artifact, not modified.
- Skin-tone `Unknown` reported as its own category, never imputed (57 rows, `N/A` performance cells).
- No row-order joins: all computation operates on the already-identity-joined `evaluation_predictions.csv` rows directly (list comprehensions over already-paired columns), never re-joining by position.
- Historical artifacts confirmed unchanged by file modification timestamp: `data/intermediate/annotations.csv` (Sep 8 17:13, pre-dates this session), `data/1408-1010-intermediate/manual_labels_export.csv` (Aug 15), `data/1408-1010-intermediate/landmark_features.csv` (Aug 14), `data/intermediate/arcface_embeddings/classifier_predictions.csv` (unchanged from the R6/R7 run).
- `reports/arcface_evaluation/` untouched (only read from).

## Source Traceability

- `reports/arcface_evaluation/evaluation_predictions.csv` (R7 common evaluation artifact — sole data source for this phase)
- `docs/EXP-007_ARCFACE_EVALUATION.md`, `docs/R7_5_CLASS_DECISION.md` (R7, R7.5)
- `docs/ARCFACE_EXPERIMENT_DESIGN.md`, `docs/METHODOLOGY_RECONCILIATION.md`, `docs/RESEARCH_FRAMING.md`, `docs/THESIS_RQ_ALIGNMENT.md`, `docs/RESEARCH_EVIDENCE_AUDIT.md`
- `docs/EXPERIMENT.md` (EXP-005 historical Neutral→Angry figure)
- `tools/analyze_arcface_errors.py` (this phase's implementation)
- `reports/arcface_error_analysis/` (all generated artifacts: `overall_error_analysis.csv`, `neutral_error_analysis.csv`, `error_taxonomy.csv`, `skin_tone_analysis.csv`, `finding_strength.csv`, and the three PNGs)
