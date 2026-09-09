# Research Findings

> Canonical research findings document, synthesized in R9 from EXP-005 through EXP-008. Every claim below is traceable to a specific artifact and population. No new experiment, model, or statistical test was introduced in this phase beyond consolidating and cross-checking what already existed. This document does not state an official thesis conclusion — see Section 10 for what is explicitly out of scope.

---

## 1. Primary Research Finding

On the 135-sample common evaluation population (5 classes: Fear, Happy, Neutral, Sad, Surprise), **ArcFace + Logistic Regression achieved a higher observed accuracy (40.74%) than HSEmotion (36.30%) evaluated on the identical samples, but this difference was not statistically significant** (McNemar's test, b=20, c=26, p=0.4614). Separately, HSEmotion exhibits a well-evidenced Neutral→Angry misclassification pattern (18/76 = 23.7% of Neutral ground-truth samples), reproducible identically in both the historical 227-sample population and the 135-sample common subset — but this specific pattern **cannot be evaluated for ArcFace**, because `Angry` is outside ArcFace's 5-class label space in the current experiment (Section 6, `docs/R7_5_CLASS_DECISION.md`).

---

## 2. Model Comparison

| Metric | ArcFace+LR | HSEmotion (same 135 samples) |
|---|---|---|
| N | 135 | 135 |
| Accuracy | 0.4074 | 0.3630 |
| Macro Precision | 0.2803 | 0.5898 |
| Macro Recall | 0.2931 | 0.2058 |
| Macro F1 | 0.2717 | 0.2489 |

**Paired statistical test**: McNemar, a=29 (both correct), b=20 (HSEmotion only correct), c=26 (ArcFace only correct), d=60 (both wrong), p=0.4614 — **no statistically significant paired difference detected**.

**Group-aware bootstrap 95% CI** (resampling 16 temporal blocks, not individual samples): ArcFace accuracy 0.4074 [0.3383, 0.4809]; HSEmotion accuracy 0.3630 [0.2692, 0.4672]. The intervals overlap substantially — consistent with, but not independent proof beyond, the McNemar result. **Overlapping CIs are not treated here as an automatic proof of "no difference"; McNemar remains the primary paired test** (per instruction).

HSEmotion's much higher macro precision alongside lower macro recall reflects a "confident but rare" prediction pattern for some classes (e.g., `Happy` and `Surprise` precision = 1.0 but recall = 0.125 each — HSEmotion is nearly always correct *when* it predicts these classes, but predicts them very rarely).

---

## 3. Error Characteristics

Per-class error rates, both models, same 135-sample subset:

| Class | ArcFace Error Rate | HSEmotion Error Rate |
|---|---|---|
| Fear (N=7) | 100.0% | 85.7% |
| Happy (N=32) | 46.9% | 87.5% |
| Neutral (N=76) | 56.6% | 44.7% |
| Sad (N=12) | 75.0% | 91.7% |
| Surprise (N=8) | 75.0% | 87.5% |

**Error distribution**: ArcFace's Neutral errors are *distributed* across `Happy` (15), `Sad` (14), `Fear` (8), `Surprise` (6) with no single dominant target. HSEmotion's Neutral errors are more *concentrated*: `Angry` alone (18) accounts for 52.9% of its 34 total Neutral errors.

---

## 4. Neutral Error Pattern

| | ArcFace+LR | HSEmotion (common subset) |
|---|---|---|
| Neutral N | 76 | 76 |
| Correct | 33 | 42 |
| **Overall Neutral error rate** | 56.6% | 44.7% |
| Dominant wrong class | Happy (15) | Angry (18) |
| **Neutral→Angry specifically** | N/A (outside label space) | **18/76 = 23.7%** |

**Important distinction, stated precisely** (per instruction not to confuse these): HSEmotion's *total* Neutral error rate on this population is 44.7% (34/76 wrong for any reason); its *Neutral→Angry-specific* rate is a narrower 23.7% (18/76) — the remaining 20.9% of Neutral errors go to `Fear` (13) and `Sad` (3). These are two different numbers answering two different questions and must not be conflated.

---

## 5. Skin-Tone Analysis

Population (recomputed independently in EXP-008, confirmed identical to EXP-007): Dark N=46, Medium-Dark N=32, Unknown N=57 (of 135 total). `Unknown` is not treated as a skin-tone category in any accuracy calculation.

| Skin Tone | N | ArcFace Accuracy | HSEmotion Accuracy |
|---|---|---|---|
| Dark | 46 | 0.4565 | 0.4565 |
| Medium-Dark | 32 | 0.3125 | 0.1250 |

**Statistical test**: Fisher's exact test on HSEmotion's Dark-vs-Medium-Dark correct/incorrect counts: OR=5.88, **p=0.0027** — a statistically significant association *in this sample*. **This is reported as an association, not a causal or demographic claim** — skin tone is a LAB-luminance-derived bucket (`src/fer_dataset/pipeline/landmark_analyzer.py`), not an ethnicity label, and no ethnicity variable exists in this dataset to test independently.

---

## 6. Dataset/Class Limitations

`Angry` (1 ground-truth sample) and `Disgust` (2 ground-truth samples) are too rare, in every population stage examined (227 full → 144 valid → 138 embedded-and-valid), to support any defensible classifier training or cross-validation. This is a **ground-truth-level scarcity**, confirmed not to be an artifact of ArcFace's embedding pipeline (`docs/R7_5_CLASS_DECISION.md` Section 3). A legitimate 7-class ArcFace experiment is **not currently feasible** with this dataset; the only methodologically sound path forward is additional data collection (Section 5 of the same document), not threshold-lowering, oversampling, or reweighting.

---

## 7. Papuan Population Limitation

*The researcher observed apparent Neutral-to-Angry misclassification among Papuan faces during dataset inspection. However, ethnicity is not encoded as a formal dataset attribute, so the current quantitative analysis cannot independently estimate a Papuan-specific error rate.* Skin tone must not be used as a proxy for ethnicity in any claim — they are measured differently and are not established as equivalent anywhere in this repository.

---

## 8. Statistical Evidence

| Test | Comparison | Result | Interpretation |
|---|---|---|---|
| McNemar (exact binomial) | ArcFace vs. HSEmotion paired accuracy, N=135 | b=20, c=26, p=0.4614 | Not statistically significant |
| Group-aware bootstrap (2000 resamples, 16 groups) | Accuracy CIs, both models | ArcFace [0.3383, 0.4809]; HSEmotion [0.2692, 0.4672] | Substantially overlapping |
| Fisher's exact | HSEmotion accuracy, Dark vs. Medium-Dark | OR=5.88, p=0.0027 | Statistically significant association, in-sample |

No additional statistical tests were run in R9 beyond re-verifying these three against their source artifacts (`reports/arcface_evaluation/statistical_tests.csv`) — all values reproduced exactly.

---

## 9. Claims We Can Make

1. ArcFace+Logistic Regression achieved higher observed accuracy (40.74%) than HSEmotion (36.30%) on the common 135-sample, 5-class evaluation population.
2. The paired accuracy difference between the two models was not statistically significant (McNemar p=0.4614).
3. ArcFace's and HSEmotion's errors follow different patterns: ArcFace's Neutral errors are distributed across multiple classes; HSEmotion's Neutral errors concentrate substantially on `Angry`.
4. HSEmotion exhibits a reproducible Neutral→Angry misclassification pattern (18/76 = 23.7%), identical in both the 227-sample historical population and the 135-sample common subset.
5. HSEmotion's accuracy and Neutral-error-rate differ descriptively (and, for accuracy, statistically per Fisher's exact test) between the Dark and Medium-Dark skin-tone buckets in this sample.
6. A defensible 7-class ArcFace evaluation is not currently possible with this dataset, due to `Angry`/`Disgust` ground-truth scarcity that predates and is independent of the ArcFace pipeline.

---

## 10. Claims We Cannot Make

Explicitly rejected, per instruction, unless directly supported above (none of the following are supported by current evidence):

- ArcFace is **definitively superior** to HSEmotion (McNemar was not significant).
- ArcFace **solves** the false-Angry problem (the metric is structurally undefined for ArcFace's 5-class configuration, not resolved by it).
- ArcFace **removes demographic bias** (no demographic/ethnicity variable exists to test this at all).
- Skin tone **causes** FER errors (association only, no causal design).
- Papuan ethnicity **causes** FER errors (no ethnicity metadata exists).
- HSEmotion is **definitively biased against Papuan people** (would require ethnicity metadata this dataset does not have).
- The dataset is **100% dark-skinned** (contradicted — `docs/THESIS_RQ_ALIGNMENT.md` Section 4 — the 85/135-sample skin-tone-characterized subset splits 58.8%/41.2% Dark/Medium-Dark, and 57/135 samples in the R7/R8 common subset have no characterized skin tone at all).
- **7-class ArcFace performance is known** (it has never been measured; only conceptually assessed as currently infeasible).

---

## 11. Final Evidence Summary

See `reports/final_research_validation/final_evidence_matrix.csv` for the complete, machine-readable version of this table.

| Finding | Metric | Population | Evidence Strength | Thesis Use |
|---|---|---|---|---|
| ArcFace accuracy | 0.4074 | N=135 | Moderate | Always paired with HSEmotion figure + McNemar result |
| HSEmotion accuracy (common subset) | 0.3630 | N=135 | Moderate | Never presented alone, separate from the N=227 historical figure |
| Paired difference not significant | McNemar p=0.4614 | N=135 | Strong (as a null result) | State explicitly, do not omit |
| ArcFace error distribution | Distributed across Happy/Sad/Fear/Surprise | N=76 | Moderate | Descriptive only |
| HSEmotion Neutral→Angry pattern | 18/76 = 23.7% | N=76 (227 and 135 both) | Strong | Central motivating finding |
| Dark vs. Medium-Dark (HSEmotion) | 0.4565 vs. 0.1250, Fisher p=0.0027 | N=46/32 | Moderate | Association only, not causal/demographic |
| Papuan-specific effect | No ethnicity metadata | N/A | Unsupported | Researcher observation only |
| ArcFace false-Angry=0 | Structural (Angry excluded) | N=135 | Unsupported as improvement | Always caveated |
| 7-class ArcFace feasibility | Angry=1, Disgust=2 in every population | N=227/144/138 | Strong (as a limitation) | Report as a data limitation, not a modeling failure |
