# Evaluation Architecture

> **Purpose**: Design the evaluation architecture for the current Structure A+B working direction, the Candidate A+B artifact hypothesis (`ARTIFACT_ARCHITECTURE.md` §9), and DSRM as the current working methodology recommendation (`METHODOLOGY_DESIGN.md` §13) — none of which are finalized. No RQ, artifact, or methodology is selected here. No new evaluation is run; no R1–R9 result is altered. This document distinguishes what has already been evaluated (R1–R9, as existing empirical evidence) from what a finalized future research design would still need to evaluate.

---

## 1. Purpose of Evaluation — Three Distinct Levels

| Level | Question | Existing R1–R9 Evaluations That Belong Here |
|---|---|---|
| **Model Evaluation** | How well does an individual FER model (HSEmotion, or the ArcFace+LR instance) perform on a given population? | R1 (HSEmotion audit, N=227); R7 (ArcFace+LR vs. HSEmotion, N=135) — these are model-level accuracy/precision/recall/F1 measurements. |
| **Research Evaluation** | Does the accumulated evidence provide sufficient basis to answer the eventual RQ? | R8 (error + skin-tone analysis) and R9 (cross-experiment consistency audit, findings synthesis) — these aggregate model-level results into research-level claims (e.g., "a reproducible Neutral→Angry pattern exists"), which is a different, higher-order question than any single model's accuracy. |
| **Artifact Evaluation** | Does the proposed artifact (the Method/Evaluation-procedure from `ARTIFACT_ARCHITECTURE.md` §9) satisfy its own requirements (`DESIGN_REQUIREMENTS.md`) — e.g., does it correctly handle `Unknown` skin-tone, correctly exclude rare classes, correctly reproduce known findings when run? | **Not yet performed by any R1–R9 activity.** R1–R9 produced the *outputs* an artifact evaluation would later check against (as a validity/sanity reference, per `METHODOLOGY_DESIGN.md` §9), but no prior phase formally specified the artifact and then evaluated whether it satisfies its own stated requirements — that is the still-outstanding future work identified in `METHODOLOGY_DESIGN.md` §5. |

**These three levels are related but not identical**, per instruction. A strong Model Evaluation (e.g., R7's rigorous McNemar/bootstrap comparison) does not by itself constitute a Research Evaluation (which requires the finding to be shown reproducible/interpretable at a higher level, as R9 attempted) or an Artifact Evaluation (which requires a *specified* artifact to check against, which does not yet exist — `ARTIFACT_ARCHITECTURE.md` explicitly left the artifact as a design hypothesis).

**Explicit statement**: R1–R9 evidence is overwhelmingly **Model Evaluation** and partially **Research Evaluation** (R8/R9). **No Artifact Evaluation has yet occurred**, because no artifact has yet been formally specified (`ARTIFACT_ARCHITECTURE.md` §9 remains a design hypothesis). This document's §16 makes this separation explicit for every requirement.

---

## 2. Claim → Evidence Architecture

For every important **future** claim the current working direction (Structure A+B) would plausibly need to support. Existing R1–R9 claims are listed separately in §6, not duplicated here as if they were future work.

| Claim (future, contingent on RQ finalization) | Criterion | Indicator | Metric/Evidence | Method | Conclusion Boundary |
|---|---|---|---|---|---|
| "The [baseline/candidate] classifier exhibits a reproducible, class-specific error pattern on this dataset." | Reproducibility across independently-derived populations | Whether the same class-specific error concentration appears in ≥2 populations | Per-class error rate, confusion matrix, computed on N=227 and N=135 separately | Confusion analysis + cross-population consistency check (already demonstrated methodologically by R9) | Bounded to *this dataset and this classifier*; cannot claim the pattern generalizes to other FER systems or datasets without further evidence (`STATE_OF_ART_AND_GAP.md` §10) |
| "Classification performance differs across measured skin-tone categories in this dataset." | Statistically detectable association, appropriately caveated for small/uneven subgroups | Accuracy delta between Dark and Medium-Dark buckets, with an association-test result | Subgroup accuracy + N per subgroup; Fisher's exact test (or equivalent, appropriate to small-cell sizes) | Subgroup stratified comparison, `Unknown` excluded not imputed | Bounded to *association in this sample*; cannot claim causality, cannot claim ethnicity-specific effect, cannot claim generalization beyond this dataset's measured skin-tone buckets |
| "A face-representation-based approach's error pattern differs from the baseline's" (only if a comparative/Candidate-C-adjacent claim is pursued) | Paired, statistically-qualified comparison on a matched population | Paired significance test result, per-class error comparison | McNemar's test (or equivalent), per-class confusion comparison, N=135 | Paired comparison, matched sample IDs | Cannot claim general superiority of either approach; a non-significant or even reversed future result must be reported with equal weight (§14) |
| "The proposed artifact reliably characterizes these patterns when applied as specified." (Artifact Evaluation, not Model/Research Evaluation) | The artifact's output, when run, matches the independently-known reference findings (R1–R9) within the artifact's own stated tolerances | Match/mismatch between artifact output and reference findings; correct handling of documented edge cases (`Unknown`, rare classes) | Comparison of artifact output against R1–R9 CSVs as a reference; a documented checklist against `DESIGN_REQUIREMENTS.md`'s MUST items | Demonstration + Evaluation activities (`METHODOLOGY_DESIGN.md` §5, §9) — **not yet performed** | Bounded to *this artifact's specific mechanism*; a successful artifact evaluation does not itself validate any scientific claim about FER beyond what the underlying data already showed |

No claim above is worded more strongly than its listed evidence path can support — each "Conclusion Boundary" column exists specifically to cap overclaiming before it happens, per instruction.

---

## 3. Objective → Evaluation Traceability (Candidate Objectives, RQ Not Yet Finalized)

Using the candidate objectives already derived per-RQ in `RQ_OPTIONS.md` §7:

| Candidate Objective | Requirement (`DESIGN_REQUIREMENTS.md`) | Evaluation Question | Metric/Evidence | Data | Method | Expected Evidence | Stability |
|---|---|---|---|---|---|---|---|
| Characterize systematic misclassification patterns (RQ-1) | A-01, A-02, D-02, E-01 | Which classes are most affected, and does the pattern reproduce? | Per-class error rate, confusion matrix, cross-population consistency | N=227 and/or N=135 | Confusion analysis, reproduction check | An error-pattern characterization report, extending `docs/RESEARCH_FINDINGS.md` §3–4 | **Stable** across RQ-1/RQ-3/RQ-4 — this evaluation question survives regardless of which of those three is finally selected |
| Determine extent of skin-tone-stratified performance difference (RQ-2) | A-03, D-03, D-04, E-02, X-02 | Does accuracy/error differ across measured skin-tone buckets, and is the difference statistically detectable? | Subgroup accuracy + N, association-test result | N=135 (and/or N=227 skin-tone breakdown, kept separate) | Subgroup comparison, Fisher's exact (or equivalent) | A skin-tone-stratified performance report | **Stable** across RQ-2/RQ-3/RQ-4 |
| Combined error + skin-tone characterization (RQ-3) | A-01–A-03, D-02–D-04, E-01–E-02 | Do error patterns and skin-tone variation relate, or are they independent findings? | Joint (class × skin-tone) cross-tabulation | N=135 | Combined confusion + subgroup analysis | A combined characterization, extending R8 | **Contingent** — only meaningful if both RQ-1's and RQ-2's evaluation questions are both retained in the final RQ |
| Compare a representation-based approach to baseline across skin tone (RQ-4) | All of the above, plus E-03, R-02 | Does a face-representation-based approach's error/skin-tone profile differ materially from the baseline's? | Paired significance test, per-subgroup comparative accuracy | N=135 | Paired comparison (McNemar or equivalent), matched samples | A comparative, skin-tone-stratified evaluation | **Contingent** — only applicable if a representation-based comparison is retained in the final scope (`ARTIFACT_ARCHITECTURE.md` §10 flagged this as the highest-risk, contingent-only candidate) |

**Stable mappings** (RQ-1's and RQ-2's evaluation questions) can be planned for with confidence regardless of which RQ candidate is finally selected. **Contingent mappings** (RQ-3's joint analysis, RQ-4's comparative layer) should not be assumed as part of the evaluation plan until the RQ is finalized — building them prematurely risks the same solution-first/scope-creep risk flagged in `ARTIFACT_ARCHITECTURE.md` §6/§10 for Candidate C.

---

## 4. Verification vs. Validation

Per the guideline's explicit distinction (`PROPOSAL_GUIDELINE_EXTRACTION.md` §16, BAB 13 §13.1, p.196–197):

### Verification — "Does the artifact satisfy its intended specification?"

| Verification Check | What It Confirms |
|---|---|
| Reproducibility | Running the artifact's procedure twice on the same input, with the same fixed seed/parameters, produces identical output (R-03 in `DESIGN_REQUIREMENTS.md`) |
| Correct data handling | Ground-truth labels are joined to predictions by filename, never by row-order (an already-fixed historical bug, Phase 9 of the earlier refactoring work — cited here only as a known failure mode to guard against, not re-litigated) |
| Deterministic/controlled processing | Class-exclusion rules (D-02) and skin-tone `Unknown` handling (D-03) are applied consistently, not ad hoc, across runs |
| Correct subgroup assignment | Every sample's skin-tone bucket assignment matches its documented measurement, with `Unknown` correctly excluded (not merged) from Dark/Medium-Dark comparisons |
| Correct metric calculation | Accuracy/precision/recall/F1/error-rate formulas are computed correctly against their stated denominators (D-04) |
| Traceability | Every reported number can be traced back to a specific population (N and source), per D-04 |
| Output completeness | All `MUST`-priority requirement outputs (`DESIGN_REQUIREMENTS.md` §10) are actually produced when the artifact runs, not silently skipped |

### Validation — "Does the artifact address the intended research problem?"

| Validation Check | What It Confirms |
|---|---|
| Useful characterization of FER errors | The artifact's error report actually surfaces a pattern that matches or meaningfully extends the already-known Neutral→Angry finding — not merely that *a* confusion matrix was produced |
| Meaningful comparison | Any baseline/comparative claim is backed by a paired, matched-population test (E-03), not just two independently-computed accuracy numbers |
| Useful subgroup analysis | The skin-tone-stratified output is interpretable given its small/uneven subgroup sizes — i.e., it does not overstate what N=46/N=32 can support |
| Evidence supporting the intended research need | The artifact's output, taken as a whole, actually speaks to the Research Need stated in `PROBLEM_ARCHITECTURE.md` §1, not just to a narrower technical question |

**Explicit statement, per instruction**: model accuracy alone is **not** treated as artifact validation anywhere in this document. Accuracy is one *input* to Model Evaluation (§1); artifact Validation is a distinct, higher-order question about whether the artifact's *characterization work* (not raw accuracy) is useful and correctly scoped.

---

## 5. Formative vs. Summative

| Evaluation Activity | Formative? | Summative? | Explanation |
|---|---|---|---|
| Verification checks (§4) | Yes | No | Purely diagnostic — "what needs fixing before the artifact can be trusted at all" |
| Validation checks (§4) | Yes | Yes (dual role) | Per the guideline (§16, p.198–199), the distinction is about *purpose of use*, not timing — the same validation pass both informs whether refinement is needed (formative) and, if reported as final evidence in the thesis, judges the artifact against its objectives (summative) |
| Reproduction-of-known-findings check (§2, §9) | Yes | Partially | Primarily formative (a mismatch would trigger investigation/refinement, per `METHODOLOGY_DESIGN.md` §6's explicit trigger conditions); becomes summative only once reported as the thesis's evidence that the artifact is trustworthy |
| Any future comparative extension (RQ-4-contingent) | No | Yes | If pursued at all, this would be a one-shot, matched-population comparative test (mirroring R7's already-completed McNemar test) — not iterative in itself, though its *result* could trigger a broader formative reconsideration of scope |

**Single build-evaluate-learn pass justification** (per `METHODOLOGY_DESIGN.md` §6, restated here in evaluation terms): the currently-planned evaluation is a **single pass** whose formative function is to check the artifact against its own requirements (§4 Verification) and against known reference findings (§4 Validation), with refinement triggered only by a **documented discrepancy** — not invented as an assumed multi-cycle process. No iterative cycle is fabricated here; if the single pass reveals no discrepancy, that is itself a valid, reportable outcome (`METHODOLOGY_DESIGN.md` §14, "Inability to demonstrate refinement" risk — already addressed there as not equivalent to absence of learning).

---

## 6. Current R1–R9 Evidence — Explicitly Mapped (Existing, Not Future)

All figures below are restated, not recomputed, from their source CSVs, and are labeled by their exact population.

### Historical HSEmotion (N=227)

| Metric | Value | Source |
|---|---|---|
| Accuracy | 22.47% | `reports/audit_summary_metrics.csv` |
| False-Angry rate | 17.62% | same |
| Neutral → Angry | 18/76 = 23.68% | same; reconfirmed identically on N=135 (see below) |

### Controlled Comparison (N=135 common subset)

| Metric | ArcFace + Logistic Regression | HSEmotion |
|---|---|---|
| Accuracy | 40.74% | 36.30% |
| Macro Precision | 28.03% | 58.98% |
| Macro Recall | 29.31% | 20.58% |
| Macro F1 | 27.17% | 24.89% |

McNemar's test (paired, N=135): **p = 0.4614** — not statistically significant. Source: `reports/arcface_evaluation/comparison_metrics.csv`, `statistical_tests.csv`.

### ArcFace Neutral-Class Detail (N=76 of 135)

| | Value |
|---|---|
| Correct | 33 |
| Incorrect | 43 |
| Error rate | 56.6% |
| Dominant wrong predictions | Happy=15, Sad=14, Fear=8, Surprise=6 |

Source: `reports/arcface_error_analysis/neutral_error_analysis.csv`.

### Skin-Tone Analysis (N=135 common subset)

| Category | N | ArcFace Accuracy | HSEmotion Accuracy |
|---|---|---|---|
| Dark | 46 | 45.65% | 45.65% |
| Medium-Dark | 32 | 31.25% | 12.50% |
| Unknown | 57 | N/A (excluded from comparison) | N/A (excluded from comparison) |

Fisher's exact test (HSEmotion, Dark vs. Medium-Dark): **OR = 5.88, p = 0.0027**. Source: `reports/arcface_evaluation/skin_tone_analysis.csv`, `statistical_tests.csv`.

**This is treated strictly as an observed association in this sample.** It is **not** described, here or anywhere in this document, as causal, as racial bias, as ethnic bias, or as Papuan-specific — consistent with every prior phase's discipline (`docs/RESEARCH_FINDINGS.md` §10, `STATE_OF_ART_AND_GAP.md` §8).

**All of the above is existing, already-produced evidence** — restated here for evaluation-architecture reference, not re-derived, re-run, or presented as new.

---

## 7. Baseline Design

**HSEmotion is the baseline.**

- **Why it is a baseline, not the artifact**: HSEmotion is a pre-existing, off-the-shelf, general-purpose FER classifier that was not designed by the researcher (`ARTIFACT_ARCHITECTURE.md` §2, "Existing Technologies"). It provides the fixed comparison point against which any characterization or comparative claim is measured — exactly the role a baseline plays, and a role explicitly distinct from an artifact under design.
- **Why no other baseline is currently required**: HSEmotion is already the system whose behavior motivated the entire practical problem (`PROBLEM_ARCHITECTURE.md` — the Neutral→Angry pattern was first observed in HSEmotion's output). Introducing a second baseline (e.g., a different off-the-shelf FER classifier) is not currently justified by any requirement in `DESIGN_REQUIREMENTS.md` and would not be invented here without such justification.
- **A candidate representation-based approach (ArcFace+Logistic Regression) is not a baseline** — per `ARTIFACT_ARCHITECTURE.md` §6, ArcFace is at most a candidate mechanism/experimental treatment, and Logistic Regression is an implementation choice; neither functions as the fixed comparison point HSEmotion does.

---

## 8. Fair Comparison Requirements

For any comparison to be valid within this evaluation architecture, it must satisfy:

- **Same evaluation population** — e.g., the N=135 common subset, used identically for both models being compared (already satisfied by R7's design).
- **Same ground-truth labels** — the same manually-assigned labels used for every compared classifier, never a different label source per classifier.
- **Same class scope** — the 5-class scope (Neutral, Happy, Sad, Surprise, Fear), consistently applied; Angry/Disgust excluded for both classifiers being compared, not just one (D-02).
- **Same sample IDs** — comparisons matched by `face_filename`, never by row order (a historically-fixed failure mode, referenced in §4 above).
- **Same evaluation protocol** — identical preprocessing/scope applied to both classifiers' inputs where technically meaningful.
- **No label leakage** — ground truth never derived from or influenced by any classifier's own prediction (D-01).
- **No training on test samples** — any classifier requiring training (e.g., the Logistic Regression layer, if a representation-based comparison is retained) must use grouped, leakage-checked cross-validation (R-02), never evaluate on samples used in its own training fold.
- **Explicit exclusion rules** — documented, not ad hoc (R-01).

**N=227 (historical) is never mixed with N=135 (controlled comparison)** anywhere in this evaluation architecture — every table in §6 explicitly labels its population, and this separation is treated as a hard constraint on any future evaluation activity as well, not just a historical practice.

---

## 9. Error Analysis Design

| Analysis | What It Can Establish | What It Cannot Establish |
|---|---|---|
| Confusion matrix | The full observed pattern of ground-truth × predicted-class pairs for a given classifier/population | *Why* any particular cell is large — no explanatory/causal mechanism |
| Per-class error rate | Which classes are, in this data, predicted correctly least often | Whether this reflects a general property of the classifier, or is specific to this dataset's conditions |
| Dominant confusion (e.g., Neutral→Angry) | That a specific misclassification direction is disproportionately common, relative to other possible errors for that class | *Why* that specific direction dominates (e.g., a shared visual feature, a training-data artifact, an inherent ambiguity in the expression) — this would require a separate, not-yet-planned investigation |
| Neutral-specific analysis | The full distribution of what Neutral ground-truth samples are misclassified as, for a given classifier | Whether this distribution would hold on a larger or differently-sourced Neutral sample |
| Prediction distribution (e.g., `reports/arcface_error_analysis/neutral_prediction_distribution.png`) | A visual/tabular comparison of how two classifiers' error patterns differ in shape (concentrated vs. distributed) | Which pattern is "better" in any absolute sense — a distributed error pattern is not automatically preferable to a concentrated one without a stated evaluation criterion for why |
| Confidence/probability analysis | Whether a classifier's stated confidence correlates with correctness, if confidence scores are available (`reports/assets/confidence_histogram.png`, `confidence_per_class.png` already exist from earlier work) | Any causal claim about confidence as a *mechanism* for error, and this analysis is not currently justified as a `MUST` requirement for the Structure A+B direction (`DESIGN_REQUIREMENTS.md` §4 rated this `COULD`, not `MUST`) |

**Explicit worked example, per instruction**: the Neutral→Angry concentration (18/76 = 23.68%, HSEmotion) **can establish** that this is a disproportionate, reproducible, observed prediction pattern (E-01's reproduction check already confirms this across N=227 and N=135). It **cannot, by itself, establish** *why* the model makes this specific error — that would require a mechanism-level investigation (e.g., examining shared visual features between Neutral and Angry expressions in this dataset, or model-internal analysis) that is explicitly out of scope for the current working direction and is not claimed as accomplished anywhere in this document.

---

## 10. Skin-Tone Evaluation Architecture

- **Subgroup accuracy**: computed per skin-tone bucket (Dark, Medium-Dark), as already demonstrated in R7/R8.
- **Subgroup error**: the complement of subgroup accuracy; equally reportable.
- **Sample counts**: **Dark N=46, Medium-Dark N=32, Unknown N=57** (of N=135) — stated explicitly with every subgroup metric, never omitted (D-04, A-03).
- **Confidence intervals, if feasible**: group-aware bootstrap CIs are already demonstrated as feasible and were computed for overall accuracy in R7 (`reports/arcface_evaluation/statistical_tests.csv`); a subgroup-level CI (e.g., for Dark-only or Medium-Dark-only accuracy) was **not** computed in R7/R8 and would be a genuinely future evaluation step if pursued — flagged in §16, not assumed already done.
- **Appropriate statistical comparison**: Fisher's exact test, already used and appropriate given the small, uneven subgroup sizes (a chi-square approximation would be less appropriate at these cell sizes).
- **Class/subgroup cell-size limitation**: explicitly acknowledged — any future joint (class × skin-tone) cross-tabulation (RQ-3/RQ-4-contingent) will produce some cells in the single digits given N=135 split across 5 classes and 2–3 skin-tone buckets; this limitation is stated here in advance, not discovered after the fact.
- **`Unknown` handling**: N=57 is **never imputed** into Dark or Medium-Dark, and is **never treated as a third skin-tone category** for comparison purposes (it is reported as its own row with its own N, then excluded from the Dark-vs-Medium-Dark comparison) — consistent with D-03.

**Explicit statement, required verbatim by instruction**: **skin tone, throughout this document, is an image-derived measurement category (a LAB-luminance-based bucket computed from face-crop pixels), not an ethnicity variable.** The dataset contains no ethnicity field. No skin-tone finding in this document is extended to any ethnicity, race, or Papuan-specific claim.

---

## 11. Statistical Evidence — Justified Tests Only

| Test | Research Purpose | Unit of Analysis | Null Hypothesis | Interpretation | Limitation |
|---|---|---|---|---|---|
| **McNemar's exact test** | Paired comparison of two classifiers' correctness on the same samples | Individual sample (matched pair: both-correct / A-only-correct / B-only-correct / both-wrong) | No systematic difference in the two classifiers' paired correctness (P(A-only) = P(B-only)) | Already applied, R7: b=20, c=26, p=0.4614 → **fails to reject the null; no statistically significant paired difference detected** | Assumes the compared classifiers are evaluated on exactly the same, matched population (satisfied here, N=135); does not by itself explain *why* any difference does or doesn't exist |
| **Fisher's exact test** | Association between a categorical subgroup variable (skin-tone bucket) and a categorical outcome (correct/incorrect) | Individual sample, cross-tabulated by subgroup × correctness | No association between skin-tone bucket and classification correctness | Already applied, R7: OR=5.88, p=0.0027 → **rejects the null at α=0.05; an association is present in this sample** | Appropriate specifically because of small/uneven cell counts (Dark n=46, Medium-Dark n=32); does **not** establish causality, does **not** generalize beyond this sample without further evidence, and is not a test of any ethnicity-related hypothesis (no ethnicity variable exists to test) |
| **Group-aware bootstrap confidence intervals** | Quantify uncertainty around a point-estimate accuracy figure, resampling by temporal group (not individual sample) to respect non-independence | Temporal block/group (16 groups, N=135) | N/A (a CI is not a hypothesis test) | Already applied, R7: ArcFace accuracy 40.74% [33.83%, 48.09%]; HSEmotion accuracy 36.30% [26.92%, 46.72%] — substantially overlapping intervals | Overlapping CIs are consistent with, but not independent proof of, the McNemar non-significance result — both are reported together, neither substitutes for the other (`docs/RESEARCH_FINDINGS.md` §2) |

**No additional statistical test is proposed here merely for appearance.** All three tests above are already justified by, and already applied to, existing evidence — this section documents their continued appropriateness for the current working direction, not a wishlist of additional tests. If a future comparative extension (RQ-4-contingent) is pursued, McNemar's test (already validated as appropriate) would be the natural re-application, not a new, unjustified test.

---

## 12. Threats to Validity

### Internal Validity

- **Label quality**: ground-truth labels are manually assigned once per sample; no inter-rater reliability check (e.g., a second independent labeler) has been performed or is claimed. This is an **unresolved** threat, not a solved one.
- **Data leakage**: filename-based joins (not row-order) are already enforced (a historically-fixed failure mode); grouped cross-validation (`StratifiedGroupKFold`) with temporal-block grouping is already used where a classifier is trained (R6) — but temporal-block grouping is an *approximation* of true person-identity grouping, since no person-ID metadata exists (`DESIGN_REQUIREMENTS.md` §12) — this is a **partially mitigated, not eliminated**, threat.
- **Temporal correlation**: frames from the same scene are likely to be highly similar; temporal-block grouping mitigates but does not eliminate the risk that near-duplicate frames inflate apparent consistency.
- **Preprocessing differences**: any comparison assumes consistent preprocessing was applied to both classifiers' inputs — already true for R7, but must be re-verified if a future comparative extension changes any preprocessing step.

### External Validity

- **Single film/source context**: all data derives from one film (*Pesta Babi*) — no claim in this document, or any future evaluation built on this architecture, generalizes to other films, other real-world video sources, or FER "in general."
- **Limited sample**: N=227 total, N=135 common-evaluation subset — small by contemporary FER-benchmark standards (contrast with AffectNet's ~450,000 images, `STATE_OF_ART_AND_GAP.md` §2A).
- **Limited classes**: 5-class scope only; Angry/Disgust structurally excluded (D-02) — no claim about 7-class or Angry/Disgust-specific behavior is supported.
- **Limited skin-tone categories**: only Dark and Medium-Dark are compared; Unknown (N=57) is excluded, not a third category; no "Light" or other skin-tone category is represented in this dataset at all.
- **Unknown generalization**: whether any finding here (error pattern, skin-tone association) would replicate on a different dataset is explicitly untested and unclaimed.

### Construct Validity

- **Image-derived skin-tone bucket**: this measurement is a LAB-luminance-derived proxy, not a validated psychometric or self-reported demographic construct — per `STATE_OF_ART_AND_GAP.md` §8, it is **methodologically distinct** from the literature's typical race/Fitzpatrick-scale measurement, and any comparison to that literature must account for this distinction, not treat the two as equivalent.
- **Expression labels**: ground-truth expression labels are categorical human judgments of an inherently sometimes-ambiguous construct (facial expression); no formal inter-rater agreement statistic exists to validate label consistency (same gap as "label quality" above).
- **Whether metrics represent the intended construct**: accuracy/precision/recall/F1 measure classification correctness against the given labels — they do not, by themselves, measure any broader construct like "FER system reliability" or "fairness," which would require additional, not-yet-defined operationalization if claimed.

### Statistical Conclusion Validity

- **Small subgroups**: Medium-Dark (N=32) in particular limits the precision of any subgroup-specific estimate.
- **Class imbalance**: Neutral (N=76 of 135) vastly outnumbers Fear (N=7) — already a known factor in why macro-averaged metrics (Macro F1) are reported alongside accuracy (`DESIGN_REQUIREMENTS.md` §4).
- **Multiple comparisons**: if a future evaluation reports several subgroup or per-class tests simultaneously, the risk of a spurious significant result increases; no multiple-comparison correction has been applied in R1–R9's existing analyses, and this should be considered if a future evaluation expands the number of simultaneous statistical tests reported.
- **Uncertainty intervals**: already reported for overall accuracy (bootstrap CIs, R7); **not yet reported at the subgroup level** (§10) — an explicit gap for future evaluation, not an oversight to hide.

**No threat above is claimed as solved unless evidence directly supports that** — most are stated as partially mitigated or explicitly unresolved, consistent with instruction.

---

## 13. Success / Failure Criteria

Defined without requiring any particular scientific outcome:

**Success**: the artifact (once specified and built, per `METHODOLOGY_DESIGN.md` §5) provides reproducible and interpretable evidence about FER performance/error patterns under the defined evaluation conditions — i.e., it passes its Verification checks (§4) and its output is judged, via Validation (§4), to meaningfully address the stated Research Need (`PROBLEM_ARCHITECTURE.md` §1).

**Failure**: the artifact cannot reliably reproduce results (fails Verification's reproducibility check), cannot trace its conclusions to evidence (fails traceability/D-04), or cannot answer the intended evaluation questions (fails Validation regardless of what the underlying data shows).

**Explicitly not used as a success criterion anywhere in this document**: "ArcFace accuracy > HSEmotion accuracy." Per instruction, defining success this way would make the research's validity contingent on a specific desired outcome, which is scientifically inappropriate and inconsistent with Rule 4 (negative results are valid) carried through every prior phase of this workflow.

---

## 14. Negative Results — Explicit Meaningfulness Check

| If Future Work Finds... | The Evaluation Remains Meaningful Because... |
|---|---|
| A representation-based approach performs worse than the baseline | This characterizes a genuine boundary condition — that this class of approach does not improve on the baseline for this population — which is itself informative for future researchers considering the same approach (Rule 4; `METHODOLOGY_DESIGN.md` §10) |
| A representation-based approach performs similarly to the baseline (as R7 already found, McNemar p=0.4614) | Already demonstrated as meaningful: R7's null result is reported plainly in `docs/RESEARCH_FINDINGS.md` §2 as one of the "Claims We Can Make," not hidden or reframed as failure |
| Skin-tone differences disappear (e.g., under a larger or re-sampled dataset) | This would itself be informative — it would suggest the originally-observed association (OR=5.88, p=0.0027) was sample-specific rather than robust, which is a legitimate, reportable finding about the limits of the original evidence, not an invalidation of the research |
| Neutral→Angry is not reproduced in some future extension (e.g., a different classifier or population) | This would sharpen, not undermine, the claim — it would show the pattern is specific to HSEtion's behavior/this dataset rather than a general FER phenomenon, which is a more precise, still-valid finding |
| Statistical significance disappears under a stricter correction (e.g., multiple-comparisons adjustment) | This is exactly what Statistical Conclusion Validity (§12) is for — a corrected non-significant result would simply mean the original finding should be reported with appropriately adjusted confidence, not discarded as a research failure |
| The proposed design fails to improve the baseline in any respect | Per §13, this was never the success criterion — a failure to improve the baseline is a valid, reportable empirical/knowledge outcome, not a failure of the evaluation architecture itself |

**In every row above, "the evaluation remains meaningful" because the evaluation architecture's own success criterion (§13) is about reproducibility, traceability, and interpretability — not about which direction any specific number moves.**

---

## 15. Evaluation Matrix (Consolidated Traceability Artifact)

| Requirement | Claim | Evaluation Type | Metric/Evidence | Baseline | Dataset | Method | Validity Threat |
|---|---|---|---|---|---|---|---|
| F-01, F-02 | A named baseline's predictions are available and comparable | Model Evaluation | Per-sample predictions | HSEmotion | N=227 / N=135 | Direct inference | Preprocessing consistency |
| A-01, D-02 | The baseline shows a class-specific error concentration | Model + Research Evaluation | Confusion matrix, per-class error rate | HSEmotion | N=227 and N=135 (checked separately) | Confusion analysis | Label quality; class imbalance |
| A-02, X-02, X-03 | Any reported pattern is labeled association-only, non-causal, with negative results retained | Reporting-convention check (part of Artifact Verification) | Presence of required labeling in output | N/A | N/A | Manual/automated convention check | N/A (a process check, not a statistical one) |
| A-03, D-03, D-04 | Skin-tone-stratified performance is reported with subgroup N, `Unknown` excluded | Model + Research Evaluation | Subgroup accuracy + N | HSEmotion (and candidate approach if pursued) | N=135 | Subgroup comparison | Small/uneven subgroups; construct validity of skin-tone measurement |
| E-01 | Findings reproduce across independently-derived populations | Research Evaluation | Cross-population consistency check | N/A | N=227 vs. N=135 | Comparison of identical metrics across populations | Temporal correlation; sample overlap between the two populations (N=135 is a subset-derived population, not fully independent of N=227 — a limitation not previously stated this explicitly and worth carrying forward) |
| E-02 | Skin-tone association is statistically qualified | Model + Research Evaluation | Fisher's exact test result | HSEmotion | N=135 | Fisher's exact test | Small-cell statistical conclusion validity |
| E-03, R-02 | A comparative claim (if pursued) is paired and leakage-checked | Model Evaluation | McNemar's test result; group-overlap check | HSEmotion | N=135 | Paired significance test; grouped CV | Leakage via imperfect person-identity proxy (temporal-block grouping) |
| R-01, R-03 | Results are reproducible from documented exclusions and parameters | Artifact Evaluation (Verification) | Funnel documentation; seed/parameter record | N/A | All | Documentation audit | N/A (a documentation completeness check) |
| X-01 | Data provenance/consent is documented | **Not evaluable — unresolved** | N/A | N/A | N/A | N/A | **This requirement currently has no evidence path at all — flagged, not filled in** |
| (Artifact-level) | The artifact, once built, reliably reproduces known findings | Artifact Evaluation (Validation) | Match against R1–R9 reference findings | N/A (self-referential check) | N=227/N=135 as reference | Comparison against existing CSVs | Circularity risk: matching known findings validates internal consistency, not external correctness — a genuine limitation of this specific check, stated here rather than hidden |

---

## 16. Existing Evaluation vs. Required for Proposed Research

### Existing Evaluation (R1–R9 — already done, not to be re-run or re-claimed as future)

- HSEmotion baseline audit (N=227): accuracy, false-Angry rate, Neutral→Angry pattern.
- ArcFace+LR vs. HSEmotion controlled comparison (N=135): accuracy, macro P/R/F1, McNemar's test, bootstrap CIs.
- Error analysis (N=135): per-class error rates, Neutral-specific breakdown, prediction-distribution comparison.
- Skin-tone analysis (N=135, and separately N=227): subgroup accuracy, Fisher's exact test.
- Cross-experiment consistency audit (R9): confirmed zero inconsistencies across EXP-005–008.

### Required for Proposed Research (genuinely not yet done)

| Requirement/Claim | Why R1–R9 Does Not Already Satisfy It |
|---|---|
| Artifact Evaluation (Verification + Validation, §4) | No artifact has been formally specified yet to check against — `ARTIFACT_ARCHITECTURE.md` §9 remains a design hypothesis, not a built, checkable artifact. R1–R9's evaluations are Model/Research Evaluation, not Artifact Evaluation (§1). |
| Subgroup-level confidence intervals (§10) | R7 computed a bootstrap CI for *overall* accuracy only, not per skin-tone-subgroup accuracy — a genuinely new computation if pursued. |
| Joint class × skin-tone cross-tabulation with adequate statistical treatment (RQ-3-contingent) | R8 reported class-level and skin-tone-level findings largely separately (`STATE_OF_ART_AND_GAP.md` §5, gap G4/Option 4 discussion) — a true joint analysis was not fully performed. |
| Inter-rater label-quality check (§12) | No second independent labeler or agreement statistic exists anywhere in this repository. |
| Data provenance/consent documentation (X-01) | Confirmed absent at every prior phase (Phase 1, 5, 6, 7) — no evaluation activity can produce this; it requires separate, non-technical resolution. |
| Multiple-comparisons-corrected statistical reporting (§12, if a future evaluation expands the number of simultaneous tests) | Not previously needed given R1–R9's relatively small number of tests; would need explicit consideration if the evaluation scope grows. |

**If no additional evaluation is currently necessary for a given requirement, this is stated explicitly rather than left ambiguous**: for F-01, F-02, A-01, A-02, D-01, D-02, D-04, E-01, E-02, R-01, R-03, X-02, X-03, the *existing* R1–R9 evidence (§6) already substantively demonstrates that these requirements are satisfiable and have been satisfied at the Model/Research Evaluation level — what remains outstanding is specifically the **Artifact-level** re-verification (does a formally-specified procedure, not just a script, reproduce this), not re-collecting the same evidence again.

---

## 17. Evaluation Boundaries — What This Evaluation Will NOT Establish

Explicitly, per instruction:

- **Causal effect of skin tone** on FER accuracy — only an in-sample association is, or will be, established.
- **Ethnicity-specific bias** — no ethnicity variable exists in this dataset; none can be tested.
- **Papuan-specific bias** — no ethnicity/nationality/cultural-group variable exists; skin tone is not a valid proxy.
- **Universal FER performance** — all findings are bounded to this dataset, this film source, and the classifiers evaluated.
- **Statistical superiority of ArcFace** — the existing evidence (McNemar p=0.4614) does not support this, and no future evaluation planned here is designed to manufacture such a claim.
- **General superiority of one model** — neither HSEmotion nor any representation-based approach is established as generally superior; only specific, bounded, population-scoped comparisons are made.
- **Causal explanation of Neutral→Angry** — the pattern is characterized as an observed, reproducible prediction concentration; no mechanism-level explanation is established or attempted within this evaluation architecture.
- **Novelty of ArcFace itself** — already confirmed not novel as a technique (`STATE_OF_ART_AND_GAP.md` §7); no evaluation activity in this document is designed to or capable of reversing that literature-based finding.

---

## 18. Validation Checklist

- Every major future claim in §2 has a stated evidence path (metric, method, and an explicit conclusion boundary capping its strength).
- Artifact Evaluation, Research Evaluation, and Model Evaluation are distinguished throughout (§1) and re-applied consistently in §15/§16.
- Verification and Validation are distinguished with concrete, non-overlapping examples (§4).
- Existing (R1–R9) and future evaluation are explicitly separated (§6 vs. §2/§16), with §16 stating explicitly, per item, why existing evidence does or does not already satisfy a given requirement.
- N=227 and N=135 are kept separate in every table in this document (§6, §8, §15).
- Skin-tone categories are correctly scoped throughout (Dark=46, Medium-Dark=32, Unknown=57 — restated consistently in §6, §10, §15) with `Unknown` never imputed.
- No causal demographic claim is introduced anywhere (§6, §10, §17 explicitly restate the association-only framing).
- No statistical result is overstated — §11 states each test's actual result and explicit limitations; §6 restates R7's non-significant McNemar result without reinterpretation.
- No evaluation criterion requires a positive result (§13 explicitly rejects "ArcFace accuracy > HSEmotion" as a success criterion).
- Negative results are shown to remain scientifically meaningful under six distinct future scenarios (§14).
- No final RQ is selected — §3 explicitly separates "stable" from "contingent" objective mappings without choosing among them.
- No final artifact is selected — §1, §15, §16 treat the artifact as a not-yet-built design hypothesis throughout.
- No final methodology is selected — DSRM is referenced only as the current working recommendation (`METHODOLOGY_DESIGN.md` §13), consistent with that document's own non-final status.

---

## Completed

Designed the evaluation architecture for the current Structure A+B working direction, the Candidate A+B artifact hypothesis, and DSRM as the current working methodology — distinguishing Artifact/Research/Model Evaluation levels, building a Claim→Evidence architecture with explicit conclusion boundaries, mapping candidate objectives to evaluation questions (stable vs. RQ-contingent), separating Verification from Validation, classifying formative/summative status without inventing iteration, mapping all existing R1–R9 evidence explicitly by population, defining the baseline (HSEmotion) and fair-comparison requirements, designing error-analysis and skin-tone-evaluation architectures with explicit "can/cannot establish" boundaries, documenting only the three already-justified statistical tests, producing a full Threats-to-Validity section (internal/external/construct/statistical-conclusion), defining outcome-neutral success/failure criteria, checking negative-result meaningfulness under six scenarios, building a consolidated Evaluation Matrix, explicitly separating existing from required-future evaluation, and stating eight explicit evaluation boundaries. Produced `docs/proposal/design/EVALUATION_ARCHITECTURE.md`.

## Files Created

- `docs/proposal/design/EVALUATION_ARCHITECTURE.md`

## Files Modified

None. No source code, R1–R9 result, or prior proposal-phase document was changed.

## Key Findings

- **No Artifact Evaluation has yet occurred anywhere in this project** — R1–R9 is overwhelmingly Model Evaluation and partially Research Evaluation; Artifact Evaluation requires a formally-specified artifact to check against, which `ARTIFACT_ARCHITECTURE.md` deliberately left as a design hypothesis. This is the evaluation architecture's single clearest "not yet done" finding.
- **A subtle, previously-unstated validity note surfaced during this phase**: the N=135 common-evaluation subset is not fully independent of the N=227 historical population (N=135 is subset-derived from N=227), which slightly weakens E-01's "cross-population reproduction" check as genuine independent replication — flagged explicitly in §15 rather than left implicit, since it had not been stated this directly in any prior phase document.
- **Success/failure criteria are defined without requiring any specific outcome** — "ArcFace accuracy > HSEmotion" is explicitly rejected as a success criterion, consistent with Rule 4 carried through every prior phase.
- **Two genuinely new (not-yet-performed) evaluation gaps were identified**: subgroup-level confidence intervals (only overall-accuracy CIs exist) and a true joint class × skin-tone cross-tabulation (R8 kept these largely separate) — both flagged as future work, not claimed as already done.
- **X-01 (data provenance/consent) has no evidence path at all** — restated in the Evaluation Matrix (§15) as literally unevaluable, not just unresolved.

## Blockers

- X-01 remains unresolved and is now confirmed to have no possible evaluation-architecture solution — it requires non-technical resolution outside this workflow.
- Artifact Evaluation cannot be performed until Phase 6's artifact hypothesis is formally specified and built (`METHODOLOGY_DESIGN.md` §5's Development activity) — this evaluation architecture is ready for that point but cannot itself trigger it.
- Contingent objective mappings (RQ-3, RQ-4) remain unresolved pending RQ finalization.

## Decisions Needed

- Whether to invest in subgroup-level confidence intervals and a true joint cross-tabulation as part of future work, given their added complexity against the already-known small-cell-size limitations (§10, §12).
- Whether the N=135-is-a-subset-of-N=227 non-independence note (§15) should change how "reproduction across populations" (E-01) is described in future proposal writing — it remains suggestive evidence, but is weaker than fully independent replication would be.
- Whether an inter-rater label-quality check is worth pursuing given the remaining thesis timeline, or should instead be stated as an accepted, permanent limitation.

## Recommendation

With Phases 5–8 now complete (Requirements, Artifact Architecture, Methodology, Evaluation Architecture), the next natural step per `PLAN_PROPOSAL_DESIGN.md` is Phase 9 (Contribution and Novelty) — but since RQ finalization remains the single largest open dependency threading through every phase since Phase 4, you may also want to revisit that decision before proceeding further.

STOP — waiting for approval for the next phase.
