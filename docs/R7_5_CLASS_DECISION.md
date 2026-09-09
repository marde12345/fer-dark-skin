# R7.5 — Class & Error Analysis Decision

> Decision-analysis only. No source code, dataset, notebook, report, existing experiment artifact, or configuration was modified. No model was retrained. No new experiment was executed.

---

## 1. Executive Summary

`Angry` has exactly **1** ground-truth sample and `Disgust` exactly **2**, in *every* population stage examined — the full 227-sample manually-labeled set, the 144-sample valid (non-`Ambiguous`) subset, and the 138-sample ArcFace-embedded-and-valid subset. **This rarity is not an artifact of ArcFace embedding exclusion, detection failures, or the R6 pipeline** — it is a property of the manually-labeled ground truth itself, present before ArcFace ever touches the data. A legitimate 7-class ArcFace experiment is therefore **not currently feasible** with this dataset — no plausible reweighting, thresholding, or cross-validation design can make a 1-sample class statistically evaluable. The 5-class ArcFace experiment **cannot** and **must not** be used to claim anything about `Neutral→Angry` behavior, since `Angry` is outside its output space by construction. The recommended structure (Section 10) keeps the 5-class ArcFace performance comparison as one line of evidence, treats `Neutral→Angry` specifically as HSEmotion-only historical/error-analysis evidence (not a paired comparison), and does not fabricate a workaround to force the two together.

---

## 2. Seven-Class Data Availability

| Class | Full manual labels (N=227) | Valid non-`Ambiguous` (N=144) | ArcFace-embedded + valid (N=138) | Used by R6 (N=135) | Excluded | Reason |
|---|---|---|---|---|---|---|
| Neutral | 80 | 80 | 76 | 76 | 4 (embedding-stage) | Detection-on-crop failure (Section 3) |
| Happy | 34 | 34 | 32 | 32 | 2 (embedding-stage) | Detection-on-crop failure |
| Sad | 12 | 12 | 12 | 12 | 0 | — |
| Surprise | 8 | 8 | 8 | 8 | 0 | — |
| Fear | 7 | 7 | 7 | 7 | 0 | — |
| **Disgust** | 2 | 2 | 2 | **0** | 2 (rare-class rule) | Below R6's minimum-class-count threshold (5) |
| **Angry** | 1 | 1 | 1 | **0** | 1 (rare-class rule) | Below R6's minimum-class-count threshold (5) |
| `Ambiguous` (not a target class) | 83 | — | — | — | 83 | Excluded from all valid-label populations (not one of the 7 expression classes) |

**Precision on what each population means** (per the instruction not to confuse them):
- **227**: every manually-labeled face crop, including `Ambiguous`.
- **144**: after removing `Ambiguous` only — this is the ground-truth class distribution the dataset actually offers for a 7-class experiment, independent of ArcFace entirely.
- **138**: after further restricting to crops where ArcFace's re-detection-on-crop succeeded (Section 2 of `docs/EXP-007_ARCFACE_EVALUATION.md`) — a small additional loss (6 samples: 4 Neutral, 2 Happy), none of which came from `Angry` or `Disgust` (both counts are identical, 1 and 2, at 227/144/138).
- **135**: R6's final classifier population, after also removing the two rare classes.

---

## 3. Why Angry and Disgust Are Rare

Traced directly, not assumed:

- **Not caused by ArcFace embedding exclusions**: `Angry`=1 and `Disgust`=2 are identical across the 227, 144, and 138-sample populations. None of the 48 `excluded_no_face` or 1 `excluded_multiple_faces` crops (R6) were `Angry` or `Disgust` ground truth — if they had been, the count would have dropped between 144 and 138, and it did not.
- **Not caused by the R6 minimum-class-size rule itself**: that rule (Section 2 of `tools/train_arcface_classifier.py`) only *excludes* already-rare classes from training; it does not cause or explain the rarity, which exists upstream in the manual labels.
- **Not caused by `Ambiguous`-label filtering**: the `Angry`/`Disgust` counts are identical between the full 227-row set and the 144-row `Ambiguous`-filtered set — no `Angry`/`Disgust` samples were reclassified as `Ambiguous` or vice versa.
- **Most plausible remaining cause: actual dataset/content imbalance**, compounded by the debug-mode frame sampling. The source video (`pesta_babi.mp4`, a documentary of a Papuan pig-feast ceremony) and the debug-mode 100-frame subsample (`config/config.yaml`: `debug.max_frames: 100`) together determine how many distinct expressive moments of any kind appear at all. A human reviewer manually labeling `gt_label` found only one crop across the entire reviewed set that they judged genuinely `Angry`, and two `Disgust` — consistent with a documentary/ceremonial setting where overt anger or disgust are simply infrequent facial expressions in the recorded footage, not consistent with any labeling-methodology bug (the labeling schema itself, `manual_labels_export.csv`, has no structural reason to suppress these two labels — it allows all 7 classes plus `Ambiguous` freely, and other rare-ish classes like `Fear` (7) and `Surprise` (8) were still assigned more often).
- **Cannot be fully separated from frame-sampling limitation**: this analysis was run on the 100-frame debug configuration (`debug.enabled: true`), not the full video. It is not established here whether a full, non-debug run of the entire ~96-minute video would surface more `Angry`/`Disgust` instances — this is a genuine open question, not resolved by this document (see Section 11).

**Conclusion**: the rarity is a **combination of genuine content-level scarcity in this specific video (or at least in the 100-frame debug sample of it) and possibly incomplete frame sampling** — not a bug, not a labeling-methodology artifact, and not caused by ArcFace's pipeline.

---

## 4. Option A — Five-Class Experiment

**Advantages**: uses all currently available, statistically-usable ground truth; already implemented and validated (R6/R7); avoids forcing a classifier to learn from 1-2 samples, which would be indefensible under any cross-validation scheme.

**Disadvantages**: cannot address the specific, most narratively prominent phenomenon (`Neutral→Angry`) at all for ArcFace; asymmetric comparison against HSEmotion's full 7-class output space (Section 3 of `docs/EXP-007_ARCFACE_EVALUATION.md`); the 5 classes it does cover are still small and uneven (`Fear`=7, `Surprise`=8).

**Research questions it CAN answer**: whether a frozen-ArcFace-embedding + Logistic Regression system performs comparably to HSEmotion on the 5 classes that have enough ground truth to evaluate at all (already answered descriptively in EXP-007: similar, not statistically distinguishable, McNemar p=0.4614).

**Research questions it CANNOT answer**: anything involving `Angry` or `Disgust` prediction behavior for ArcFace, including the central `Neutral→Angry` phenomenon.

**Verified, not assumed**: `tools/train_arcface_classifier.py`'s `class_order` is `sorted(set(s.gt_label for s in usable))` computed *after* rare-class filtering — `Angry` literally cannot appear in `class_order`, so `LogisticRegression` is fit with zero knowledge that an `Angry` class exists; it cannot output it under any circumstance. **Confirmed: the 5-class experiment cannot legitimately test whether ArcFace reduces `Neutral→Angry` errors — not because of a modeling limitation, but because the question is undefined for a classifier that was never given that output option.**

---

## 5. Option B — Seven-Class Experiment

| Approach | Feasibility | Methodological Risk | Expected Benefit | Preserves Research Integrity? |
|---|---|---|---|---|
| **1. Use Angry(1)/Disgust(2) as-is** | **Not feasible.** `StratifiedGroupKFold` (or any stratified CV) requires at least as many samples per class as folds; a class with 1 sample cannot appear in more than one fold's data at all, and can never be both trained-on and evaluated-on. A 1-sample class is fundamentally unlearnable and unevaluable. | Very high — any reported metric for `Angry` would be based on 0 or 1 observations, statistically meaningless, and a single mislabeled or lucky sample would swing its "accuracy" between 0% and 100%. | None — no real signal obtainable from 1-2 samples. | No — reporting a metric that is actually noise as if it were a finding would misrepresent the evidence. |
| **2. Lower the minimum-class threshold** | Mechanically trivial (change one constant), but the task explicitly instructs not to do this "solely to obtain desired class balance," and the underlying data problem (1-2 samples) is not solved by relabeling the threshold — the classes remain statistically unevaluable regardless of what threshold value permits them into the class list. | High — this would be changing a decision rule to fit a desired outcome shape, not to fit the evidence; exactly the "cherry-picking" pattern flagged in Section 12. | None beyond cosmetically including the classes in a table; no real improvement in evaluability. | No. |
| **3. Class weighting only (keep threshold as-is, weight `Angry`/`Disgust` heavily)** | Feasible to implement, but weighting cannot manufacture information that doesn't exist — with 1 `Angry` sample, even an infinitely-weighted loss term has only one data point to learn a decision boundary from, and cross-validation still cannot both train and test on it. | High — same fundamental problem as Approach 1, dressed up with a hyperparameter; class weighting helps *imbalance* (uneven but present classes), not *near-total absence* (1-2 samples). | Minimal to none. | No. |
| **4. Collect/add more labeled data** | **The only approach that actually addresses the root cause** (Section 3) — either running the pipeline on more of the source video (beyond the 100-frame debug subset) to surface more `Angry`/`Disgust` instances, or sourcing additional labeled data. Feasibility depends on whether the full video (or additional footage) actually contains more such expressions — unknown without trying. | Low methodologically (this is the standard, legitimate way to fix a data-scarcity problem), but requires real effort/time and is not guaranteed to succeed (the expressions may simply be rare in the source material). | High, if successful — would enable a genuine 7-class comparison. | Yes — this is the methodologically correct fix, not a shortcut. |
| **5. Other defensible strategy** | Not identified beyond Section 7's alternative error-metric framing, which sidesteps rather than solves the 7-class classification problem. | N/A | See Section 7. | See Section 7. |

**Conclusion on Option B**: not currently feasible with the existing dataset. The only methodologically sound path to a real 7-class experiment is Approach 4 (more data), which is a data-collection task, not a modeling or threshold-tuning task.

---

## 6. Neutral → Angry Research Validity

| | Current 5-Class ArcFace Design | Potential 7-Class ArcFace Design (if Approach 4 succeeded) |
|---|---|---|
| **Observed** | Cannot observe — `Angry` is not in ArcFace's output space; HSEmotion's `Neutral→Angry` remains observable and already is (18/76, EXP-007 Section 8). | Would be observable for both models, if enough `Angry` ground truth existed to train on. |
| **Quantified** | Quantifiable for HSEmotion only. | Quantifiable for both, if sample size permits stable estimation (would still need considerably more than 1-2 samples for any per-class metric to be stable). |
| **Compared** | Cannot be compared between models — comparing "0 (structurally forced)" against "18 (real behavior)" is not a valid comparison, as already flagged in EXP-007 Section 8/13. | Could be compared, contingent on adequate sample size in the new `Angry` class. |
| **Statistically tested** | Not testable as a paired comparison (no ArcFace `Angry` predictions exist to test against). | Would be testable (e.g., McNemar restricted to `Angry`-vs-not, or a one-vs-rest test — Section 7) only with enough `Angry` samples for the test to have any power. |

**Under the current 5-class design, the only scientifically honest statement about `Neutral→Angry` is**: *"HSEmotion exhibits a Neutral→Angry misclassification pattern (18/76 Neutral samples, 23.7%) in this dataset; whether a frozen-ArcFace-embedding approach would exhibit the same, a different, or no such pattern cannot currently be determined, because the available ground truth does not support training or evaluating an Angry class for it."*

---

## 7. Alternative Error Metrics

Investigated, per instruction not to invent a workaround merely to preserve the narrative:

- **Confusion among shared classes**: legitimate and already reported (EXP-007 Section 7) — e.g., ArcFace's `Neutral→Happy` (15) and `Neutral→Fear` (8) confusions are real, observable, comparable errors within the 5-class space.
- **Neutral misclassification rate (overall, not Angry-specific)**: legitimate and computable from existing data — "of 76 Neutral ground-truth samples, how many did each model get wrong, regardless of what they predicted instead" is answerable for both models on the common subset and does not require `Angry` to be in-scope.
- **Dominant predicted class for Neutral**: legitimate and already partially visible in the confusion matrices (EXP-007 Section 7) — HSEmotion's dominant wrong-Neutral prediction is the "Other" bucket (18, i.e. mostly `Angry`); ArcFace's dominant wrong-Neutral prediction is `Happy` (15). This is a valid, honest point of comparison: *what* each model confuses Neutral with, even though ArcFace cannot confuse it with `Angry` specifically.
- **Error entropy/distribution**: legitimate in principle (e.g., entropy of the wrong-prediction distribution per true class) — not yet computed, would be a new, small, low-risk analysis using only already-collected predictions (no retraining).
- **One-vs-rest treatment**: **not defensible here** — a one-vs-rest `Angry`-vs-not-Angry classifier would still need to be *trained* on the same 1 positive example, so it inherits the identical statistical-instability problem as Approach 1 in Section 5. This is not a legitimate workaround.

**Conclusion**: general Neutral-misclassification-rate and dominant-confusion-target comparisons are scientifically legitimate substitutes for the specific `Neutral→Angry` metric, and can be reported for both models without needing `Angry` in ArcFace's class space. They answer a related but explicitly narrower question ("does ArcFace also confuse Neutral with something, and with what" rather than "does ArcFace specifically confuse Neutral with Angry").

---

## 8. Role of HSEmotion

**Recommendation: HSEmotion should be treated as the historical/production baseline for the pipeline as a whole, and additionally as the sole available evidence source for any `Angry`-specific claim, given ArcFace cannot currently address it.** It should not be recast as "the primary baseline for the thesis" in a way that implies the thesis's main contribution is about HSEmotion — the thesis's evaluative interest is in the ArcFace comparison, and HSEmotion is the reference point that comparison is measured against.

**Both the historical 7-class HSEmotion result (227 samples) and the new 5-class paired comparison (135 samples) should appear in the thesis, kept clearly separate**, exactly as EXP-007 Section 6 already does — the historical figure characterizes HSEmotion's real-world behavior across its full label space and dataset; the paired figure characterizes a specifically-scoped, fair, same-subset comparison against ArcFace. Presenting only one would either lose the full picture of HSEmotion's behavior (if only the 135-sample figure is shown) or invite an apples-to-oranges comparison against ArcFace (if only the 227-sample figure is shown next to ArcFace's 135-sample result). **Never merge the two into one number.**

---

## 9. Skin-Tone Analysis Impact

Determined precisely, not assumed:

- **Dark vs. Medium-Dark accuracy comparison (HSEmotion)**: **remains valid**, both historically (227-sample, `docs/RESEARCH_FRAMING.md`) and on the 135-sample common subset (EXP-007 Section 9) — neither `Angry` nor `Disgust` exclusion changes this, since this comparison is about `Neutral`/`Happy`/`Sad`/`Surprise`/`Fear` accuracy patterns, not about `Angry`-specific behavior. The Fisher's exact test result (p=0.0027, EXP-007 Section 10) is unaffected by the 5-class restriction.
- **Fairness gap (historical, 0.2971)**: **remains valid** as originally computed (full 227-sample, all-class accuracy by skin tone) — this figure is not recomputed or superseded by the 5-class experiment and should continue to be cited as the full-dataset figure it is.
- **False-Angry analysis by skin tone (HSEmotion)**: **remains fully valid** — HSEmotion's false-Angry behavior (Dark 0.2174, Medium-Dark 0.5000 rate, EXP-007 Section 9) is unaffected by ArcFace's class restriction, since it only describes HSEmotion.
- **False-Angry analysis by skin tone (ArcFace)**: **not valid as a finding** — structurally 0 in every skin-tone group, for the identical reason as the aggregate false-Angry rate (Section 6 above). This was already correctly caveated in EXP-007 Section 9 and remains the correct treatment.
- **Subgroup sample sizes**: unaffected by the `Angry`/`Disgust` exclusion specifically — the Dark (46) / Medium-Dark (32) / Unknown (57) breakdown in the 135-sample subset would be nearly identical (at most 3 samples different) even if `Angry`/`Disgust` had been includable, since those two classes contributed at most 3 samples total to any population stage.

**Nothing about the skin-tone findings needs to be discarded or revised** because of the class-count decision — the only skin-tone-adjacent metric invalidated is ArcFace's false-Angry rate specifically, which was already correctly flagged as non-interpretable in EXP-007.

---

## 10. Recommended Experimental Structure

**Structure C — 5-class ArcFace primary performance experiment + separate error-analysis treatment of `Neutral→Angry` as HSEmotion-specific evidence — with Section 7's legitimate alternative error metrics (general Neutral-misclassification rate, dominant-confusion-target) added as a genuine, if narrower, cross-model error comparison.**

This is effectively Structure A with an explicit addition (the Section 7 alternative metrics), which is why it's labeled as its own structure rather than a trivial restatement of A.

**Why, weighed against the required considerations**:
- **Research objective**: the objective (per `docs/RESEARCH_FRAMING.md`'s recommended Candidate D) is performance + error-pattern characterization on a dark-skinned, Papuan-sourced population, with skin-tone as supporting evidence — nothing in that framing requires a complete 7-class comparison to be answerable; it requires an honest performance comparison plus honest error characterization, both of which Structure C delivers.
- **Dataset size / class imbalance**: 227 total samples with a 1-sample and a 2-sample class make Structure B (7-class) currently infeasible (Section 5) — not a matter of preference, a matter of what the data can support.
- **Observed Neutral→Angry phenomenon**: preserved as legitimate HSEmotion-specific evidence (Section 6/8), not deleted, not forced into an invalid ArcFace comparison, and supplemented with the legitimate related metrics from Section 7 so the thesis isn't left with *zero* ArcFace-side error characterization for Neutral.
- **Statistical validity**: Structure C makes no claim (Angry-related) that the data cannot support; every number kept in the primary comparison (accuracy, macro F1, McNemar, general Neutral-misclassification) has an adequate-enough sample size to report, with limitations stated where they exist.
- **Thesis defensibility**: an examiner asking "did you test whether ArcFace fixes the Angry over-prediction problem?" is best answered with "no — the available ground truth could not support training an Angry class at all, and here is the evidence (Section 2) — but here is what we can say about Neutral misclassification more generally (Section 7)" rather than an answer that silently omits the limitation or, worse, presents 0% false-Angry as a fabricated improvement.
- **Practical feasibility**: requires no new modeling work, no data collection, no retraining — only additional, already-computable descriptive analysis (Section 11, P1).

**Structure B is not recommended** given Section 5's finding that it isn't currently feasible without new data. **Structure D was considered but no alternative structure emerged from this analysis that better fits the evidence than C.**

---

## 11. Required New Work

- **P0 — mandatory**: none. The current EXP-007 evaluation is already valid for what it claims (5-class performance comparison); Structure C requires only additive analysis, not a prerequisite fix.
- **P1 — important**: compute and report the Section 7 alternative metrics (general Neutral-misclassification rate for both models on the common subset; dominant-wrong-prediction-for-Neutral for both models) as a supplementary error-analysis addendum to EXP-007 or a new short document — this uses only already-collected predictions (`reports/arcface_evaluation/evaluation_predictions.csv`), no retraining, no new data.
- **P2 — optional**: investigate whether running the pipeline on more of the source video (beyond the 100-frame debug subset) surfaces enough additional `Angry`/`Disgust` ground truth to eventually revisit a 7-class experiment (Section 5, Approach 4) — this **is** additional data collection, and its outcome is uncertain (the expressions may simply be rare in the underlying footage, per Section 3). This should be explicitly framed as exploratory/uncertain, not a guaranteed fix, if pursued.

**Explicit answer to "is additional data collection required?"**: **Yes, if and only if a genuine 7-class ArcFace experiment is later desired.** It is not required for the recommended Structure C, which does not depend on a 7-class experiment.

---

## 12. Invalid / Unsafe Approaches to Avoid

Explicitly listed, per instruction:

- Claiming ArcFace's 0 false-Angry rate as an improvement or fairness benefit — it is a structural artifact of class exclusion, not observed behavior (already caveated in EXP-007, restated here as a standing rule).
- Artificially duplicating or oversampling the single `Angry` sample (or the two `Disgust` samples) to reach the minimum-class threshold — this would fabricate the appearance of data that does not exist and produce a classifier that has "seen" the same one example multiple times, not real diversity.
- Using HSEmotion's own predictions to backfill missing `Angry` ground-truth labels — this would be circular (defeats the entire purpose of an independent ground-truth-based evaluation) and was already explicitly prohibited in R6.
- Lowering the minimum-class-count threshold solely to make the 7-class experiment "work" — addressed in Section 5, Approach 2.
- Cherry-picking which samples/classes to report based on which produces a more favorable ArcFace-vs-HSEmotion story.
- Changing the evaluation population (adding/removing samples) after having already seen the R7 results — the 135-sample population is fixed; any future population change must be justified independently of the results it would produce.
- Comparing the 5-class ArcFace result against HSEmotion's full 7-class historical result as if they were the same comparison — Section 8 requires keeping these separate; EXP-007 already does this correctly and it must remain so.
- Inferring Papuan ethnicity, or any ethnicity-specific effect, from skin-tone bucket membership — restated from `docs/RESEARCH_FRAMING.md` and `docs/EXP-007_ARCFACE_EVALUATION.md`; skin tone is a LAB-luminance heuristic, not an ethnicity label, and this document's Section 9 findings must not be reworded into an ethnicity claim.

---

## 13. Single Recommended Next Phase

**R8 — Proceed with the Section 7 alternative error-analysis addendum (general Neutral-misclassification rate and dominant-confusion-target comparison for both models on the existing common subset), then move to skin-tone/error-analysis write-up for the thesis, explicitly treating `Neutral→Angry` as HSEmotion-specific historical evidence rather than a paired ArcFace comparison.**

This is the smallest, lowest-risk next step consistent with Structure C (Section 10): it requires no retraining, no new data, and no dataset changes — only additional descriptive computation over predictions that already exist (`reports/arcface_evaluation/evaluation_predictions.csv`), and it directly fills the one real gap Structure C leaves open (an ArcFace-side view of Neutral misclassification, even though `Angry`-specifically remains out of reach).

---

## 14. Source Traceability

- `docs/EXP-007_ARCFACE_EVALUATION.md` (R7, in full — Sections 2, 4, 5, 8, 9, 13)
- `docs/ARCFACE_EXPERIMENT_DESIGN.md` (R4, Section 8's grouping limitation, Section 6-7's classifier choice)
- `docs/RESEARCH_FRAMING.md` (R2.5, Candidate D recommendation, Section 4's dataset/limitations)
- `docs/RESEARCH_EVIDENCE_AUDIT.md`, `docs/THESIS_RQ_ALIGNMENT.md` (R1, R2)
- `docs/EXPERIMENT.md` (EXP-005, EXP-006, EXP-007)
- `tools/train_arcface_classifier.py` (`MIN_CLASS_COUNT = 5`, `build_usable_samples()`'s class-order/exclusion logic — read, not modified)
- `tools/evaluate_arcface_vs_hsemotion.py` (evaluation logic — read, not modified)
- `data/intermediate/arcface_embeddings/embeddings.csv`, `classifier_predictions.csv` (read-only, for the Section 2 population counts)
- `data/1408-1010-intermediate/manual_labels_export.csv` (read-only — full 227-row `gt_label` distribution counted directly for this document: `Neutral 80, Ambiguous 83, Happy 34, Sad 12, Disgust 2, Fear 7, Surprise 8, Angry 1`)
- `config/config.yaml` (`debug.max_frames: 100` — confirms the 100-frame debug scope referenced in Section 3)
