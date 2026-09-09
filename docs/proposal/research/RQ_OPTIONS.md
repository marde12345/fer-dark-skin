# Research Question Options

> **Purpose**: Develop and evaluate candidate Research Questions from the solution-neutral problem architecture (`docs/proposal/research/PROBLEM_ARCHITECTURE.md`, Phase 2) and the literature-supported gaps (`docs/proposal/research/STATE_OF_ART_AND_GAP.md`, Phase 3). No RQ is finalized here — final RQ selection is an explicit supervisor/user decision, per `docs/proposal/guideline/PROPOSAL_GUIDELINE_EXTRACTION.md` §8 and the plan's Rule 6. No new experiment was run to produce this document; all thesis-evidence references below restate, not recompute, existing R1–R9 numbers.
>
> **Chain followed**: Problem → Research Gap → Research Question → Objective → Research Activity → Output → Evidence → Contribution (guideline p.139). **Chain explicitly avoided**: Interesting existing result → RQ (Rule 5).

---

## 1. Inputs Used

- `docs/proposal/research/PROBLEM_ARCHITECTURE.md` — practical problem, evidence, Framings A/B/C, Claims We Can/Cannot Make Now.
- `docs/proposal/research/STATE_OF_ART_AND_GAP.md` — Gaps G1 (moderate), G2 (moderate-to-strong), G3 (moderate, contingent), G4 (unsupported); Framing Assessment (A=PROMISING, B=PROMISING, C=POSSIBLE); ArcFace novelty check (ArcFace-for-FER **not novel** — Altaha et al. 2023, Waldner & Mitra 2024).
- `docs/proposal/guideline/PROPOSAL_GUIDELINE_EXTRACTION.md` §8 (RQ formulation, p.131–136).
- R1–R9 verified evidence, restated with denominators kept explicit throughout (never mixing N=227 historical with N=135 common-subset, or pooling skin-tone subgroups N=46/N=32/N=57 without labeling).

---

## 2. Candidate Research Questions

Five candidates are developed, covering Direction A, B, A+B, a gap-derived Direction C, and — deliberately included as a cautionary contrast — a Direction C variant that is **not** gap-derived, to make the reverse-engineering risk concrete rather than abstract.

### RQ-1 (Direction A — Performance / Error Characterization)

> **RQ-1**: What systematic misclassification patterns, if any, characterize general-purpose FER classification on this dataset, and under what conditions (e.g., expression category) are they most pronounced?

Grounded in Gap G1 (moderate): HSEmotion's Neutral→Angry pattern (18/76 = 23.68%, N=227 historical, identically reproduced on N=135 common subset) is well-evidenced internally; Chhua et al. (2024) confirm that class-specific, demographic-stratified FER confusion patterns are a real phenomenon in at least one other system, without confirming this specific pattern externally. Names no candidate solution.

### RQ-2 (Direction B — Skin-Tone Robustness)

> **RQ-2**: To what extent, if any, does general-purpose FER classification performance differ across measured skin-tone categories in this dataset?

Grounded in Gap G2 (moderate-to-strong in the literature; moderate in this thesis's own evidence): Fisher's exact OR=5.88, p=0.0027, HSEmotion accuracy, Dark (n=46) vs. Medium-Dark (n=32), N=135 common subset. Deliberately phrased as "measured skin-tone categories," not race/ethnicity/bias, per the phase's explicit wording constraint.

### RQ-3 (Direction A+B — Combined)

> **RQ-3**: What systematic FER misclassification patterns exist in this dataset, and how, if at all, do these patterns vary across measured skin-tone categories?

Grounded in both G1 and G2 together, and directly continuous with work already begun in R8 (`reports/arcface_error_analysis/skin_tone_analysis.csv`, `neutral_error_analysis.csv`). This is the combined framing flagged as "Option 4" in `STATE_OF_ART_AND_GAP.md` §9.

### RQ-4 (Direction C — Representation-Based Design, gap-derived)

> **RQ-4**: How does a face-representation-based FER approach's classification performance and error pattern compare to a general-purpose FER classifier's, across measured skin-tone categories, in this dataset?

Grounded in Gap G3 (moderate, explicitly contingent — `STATE_OF_ART_AND_GAP.md` §5, §7): neither Altaha et al. (2023) nor Waldner & Mitra (2024) evaluate an ArcFace-family representation on a skin-tone-stratified population; this review did not find that combination elsewhere either (flagged "not found," not "does not exist"). **This RQ is legitimate only if derived from RQ-2/RQ-3's finding that skin-tone variation is worth investigating** — not because ArcFace is already implemented. Uses "face-representation-based FER approach," not "ArcFace emotion classifier" (§14 constraint) — ArcFace is one candidate instance of this approach class, not named as the RQ's subject.

### RQ-5 (Direction C — Representation-Based Design, NOT gap-derived — included as cautionary contrast)

> **RQ-5**: Does an ArcFace-based FER approach outperform HSEmotion on this dataset?

**This candidate is included deliberately to make the reverse-engineering risk concrete, not because it is recommended.** It restates, almost verbatim, the question R7 already answered (`docs/RESEARCH_FINDINGS.md` §2: accuracy 40.74% vs. 36.30%, McNemar p=0.4614, not significant) — i.e., it is an *Interesting existing result → RQ* construction (Rule 5), not a *Problem → Gap → RQ* construction. It is carried into the comparison table below specifically so its weaknesses can be shown side-by-side against the other four, rather than only asserted abstractly.

---

## 3. RQ Quality Test

| Criterion | RQ-1 (A) | RQ-2 (B) | RQ-3 (A+B) | RQ-4 (C, gap-derived) | RQ-5 (C, not gap-derived) |
|---|---|---|---|---|---|
| Problem relevance | STRONG | STRONG | STRONG | MODERATE | WEAK |
| Gap relevance | MODERATE (G1) | MODERATE-STRONG (G2) | MODERATE-STRONG (G1+G2) | MODERATE (G3, contingent — see below) | **BLOCKED** (see below) |
| Answerability | STRONG | STRONG | STRONG | MODERATE | STRONG (already answered) |
| Data availability | STRONG (N=227/N=135 exist) | MODERATE (N=46/32 usable, N=57 Unknown) | MODERATE (same as RQ-2, plus RQ-1's) | MODERATE (same skin-tone-subset constraints as RQ-2, applied to the 5-class ArcFace scope) | STRONG (already collected/analyzed) |
| Method feasibility | STRONG | STRONG | STRONG | MODERATE | STRONG |
| Evaluation feasibility | STRONG | MODERATE (small/uneven subgroups) | MODERATE | MODERATE-WEAK (small subgroup × 5-class scope compounds sample sparsity) | STRONG |
| Evidence availability | STRONG (R1, R5, R8 already produced relevant evidence) | MODERATE (R7, R8 skin-tone evidence exists but is thin) | MODERATE | MODERATE (R7 evidence exists but wasn't collected *to answer this exact RQ*) | STRONG (but see below) |
| Independence from a specific solution | STRONG (no solution named) | STRONG (no solution named) | STRONG (no solution named) | MODERATE (names a solution *class*, not one technique) | **WEAK** |
| Contribution potential | MODERATE | MODERATE-STRONG | STRONG | MODERATE | WEAK |
| Scope suitability for Master's thesis | STRONG | STRONG | MODERATE (broader scope, still feasible) | MODERATE | STRONG (but for the wrong reason — already done) |
| Risk of overclaiming | LOW | MODERATE (skin-tone/ethnicity conflation risk — see §13 discipline) | MODERATE | MODERATE | **HIGH** |

**Explanation of every WEAK/BLOCKED rating:**

- **RQ-4, Gap relevance = MODERATE (contingent)**: G3 in `STATE_OF_ART_AND_GAP.md` is explicitly marked "moderate, contingent on G1/G2 providing the requirements basis" — this is not a standalone gap; it only holds together if RQ-2/RQ-3 first establishes that skin-tone variation is a real, worthwhile phenomenon to test a representation-based approach against.
- **RQ-4, Evaluation feasibility = MODERATE-WEAK**: the existing 5-class scope (Angry=1, Disgust=2 ground truth excluded — `docs/R7_5_CLASS_DECISION.md`) combined with already-small skin-tone subgroups (N=46 Dark, N=32 Medium-Dark within N=135) means any skin-tone-stratified *and* class-stratified breakdown for a representation-based approach would operate on cells potentially in the single digits for some class×skin-tone combinations. This is a real feasibility constraint, not a fatal one, but must be stated plainly.
- **RQ-5, Gap relevance = BLOCKED**: this RQ has no gap to trace to beyond "we already have a result and want to ask about it" — `docs/proposal/research/STATE_OF_ART_AND_GAP.md` explicitly found ArcFace-for-FER is *not novel* as a technique, and this RQ does not specify skin-tone-stratification or any other angle that would make it more than a restatement of an already-completed comparison.
- **RQ-5, Independence from a specific solution = WEAK**: the RQ *is* ArcFace — removing ArcFace removes the entire question (see §4 below).
- **RQ-5, Risk of overclaiming = HIGH**: phrased as "Does X outperform Y," a yes/no question invites a binary headline claim; the actual existing evidence is a non-significant difference (McNemar p=0.4614), which a binary-framed RQ pressures toward overstatement in either direction ("ArcFace wins" or "ArcFace fails") when the honest answer is "no significant difference was found."

---

## 4. Solution-Neutrality Test

> "If ArcFace were removed from the thesis tomorrow, would this RQ still represent a meaningful research question?"

| Candidate | Classification | Explanation |
|---|---|---|
| RQ-1 | **YES** | Entirely about FER error patterns in general-purpose classification; ArcFace is never mentioned or presupposed. |
| RQ-2 | **YES** | Entirely about skin-tone-stratified performance of general-purpose classification; ArcFace is never mentioned or presupposed. |
| RQ-3 | **YES** | Combination of RQ-1 and RQ-2; same reasoning applies. |
| RQ-4 | **PARTIALLY** | The RQ names a *class* of approach ("face-representation-based FER"), not ArcFace specifically — a different representation model (e.g., a different pretrained face-recognition backbone) could answer it. But if *no* representation-based approach were available/considered at all, the RQ would have no candidate mechanism to evaluate, so it is not fully independent either. |
| RQ-5 | **NO** | The RQ's entire subject is "an ArcFace-based FER approach" — removing ArcFace removes the question itself. Classified NO, not automatically rejected, but flagged high risk per the phase instruction, and is the primary reason it is the weakest candidate in §8. |

---

## 5. Data Answerability Test

### RQ-1

- **Required data**: face images with ground-truth expression labels and FER-classifier predictions.
- **Current data**: exists — N=227 historical (`data/1408-1010-intermediate/manual_labels_export.csv`, `data/intermediate/annotations.csv`); N=135 common subset for cross-model comparison (`reports/arcface_evaluation/evaluation_predictions.csv`).
- **Missing data**: none required beyond what already exists for a within-dataset characterization; a second, independent dataset would be needed only if generalization *beyond this dataset* were claimed (not required for RQ-1 as worded).
- **Evaluation unit**: individual face crop (one row per `face_filename`).
- **Sample size**: N=227 (historical HSEmotion characterization) and/or N=135 (if cross-model consistency is part of the characterization) — **must be reported separately, never pooled**, per `docs/RESEARCH_FINDINGS.md`'s existing discipline.

### RQ-2

- **Required data**: face images with ground-truth expression labels, FER-classifier predictions, and a skin-tone measurement per image.
- **Current data**: exists — skin-tone bucket already computed and stored for the N=135 common subset (`reports/arcface_evaluation/skin_tone_analysis.csv`) and, separately, for the N=227 historical population (`reports/audit_per_skin_tone_accuracy.csv`, `reports/audit_summary_metrics.csv`).
- **Missing data**: the `Unknown` skin-tone bucket (N=57 of 135) has no usable skin-tone measurement — this is a real, currently unresolved data gap, not an oversight; more balanced Dark/Medium-Dark subgroup sizes would strengthen (not currently block) the analysis.
- **Evaluation unit**: individual face crop, stratified by skin-tone bucket.
- **Sample size**: **N=135 common subset, with Dark=46, Medium-Dark=32, Unknown=57 explicitly separated** (Unknown excluded from any accuracy-by-skin-tone comparison, consistent with `docs/RESEARCH_FINDINGS.md` §5); alternatively N=227 historical with its own skin-tone breakdown (`reports/audit_per_skin_tone_accuracy.csv`) — **the two populations' skin-tone breakdowns must not be merged**, since they are computed over different underlying sample sets.

### RQ-3

- **Required / current / missing data**: union of RQ-1 and RQ-2's requirements — no additional data type beyond what both already require.
- **Evaluation unit**: individual face crop, cross-tabulated by ground-truth class × prediction × skin-tone bucket.
- **Sample size**: N=135 common subset (the only population with both full cross-model predictions and skin-tone data together) — historical N=227 skin-tone data exists but was not computed against the same cross-model comparison, so a combined characterization is most defensibly scoped to N=135.

### RQ-4

- **Required data**: same as RQ-3, plus a face-representation-based approach's predictions specifically (not just any FER classifier's).
- **Current data**: exists for one specific instance — ArcFace+Logistic Regression predictions on N=135 (`reports/arcface_evaluation/evaluation_predictions.csv`), already including a skin-tone breakdown (`reports/arcface_evaluation/skin_tone_analysis.csv`).
- **Missing data**: if RQ-4 is meant to test face-representation-based approaches as a *class* (not just the one already-built ArcFace+LR instance), additional representation-model instances would need to be built and evaluated — this is currently missing and would be new work, not a data gap in the traditional sense.
- **Evaluation unit**: individual face crop, stratified by skin-tone bucket, for a representation-based classifier's predictions specifically.
- **Sample size**: N=135 common subset, Dark=46/Medium-Dark=32/Unknown=57, with the additional caveat (§3) that class×skin-tone cross-tabulation on the current 5-class scope will produce some very small cells.

### RQ-5

- **Required / current data**: already fully collected and analyzed — N=135, `reports/arcface_evaluation/comparison_metrics.csv`, `statistical_tests.csv`.
- **Missing data**: none — this RQ requires no new data collection, which is precisely why it is flagged as reverse-engineered rather than forward-designed (§2, §4).
- **Evaluation unit / sample size**: N=135 common subset, as already reported.

---

## 6. Method Answerability

No methodology is finalized here (deferred to Phase 7) — only the *kind* of research activity each RQ would require:

| Candidate | Kind of research activity |
|---|---|
| RQ-1 | Error analysis (descriptive + explanatory); confusion-pattern characterization; possibly qualitative inspection of misclassified cases for hypothesis generation. |
| RQ-2 | Subgroup analysis; statistical comparison (association testing, e.g. as already used: Fisher's exact); descriptive accuracy-by-subgroup reporting. |
| RQ-3 | Combination of the above two — error analysis cross-tabulated by subgroup; statistical comparison within subgroups. |
| RQ-4 | Controlled model comparison (representation-based approach vs. baseline); subgroup analysis; statistical comparison; would likely require design-and-evaluation activity if new representation instances are built, or purely evaluative activity if reusing the existing ArcFace+LR instance under a newly-derived requirement/theory basis (Phase 6/9 concern, not decided here). |
| RQ-5 | Controlled model comparison; statistical comparison — **already fully executed** (R7); no new research activity would actually be required, which is itself evidence this RQ is not forward-looking. |

---

## 7. RQ → Objective → Activity → Output → Evidence → Potential Contribution

For each candidate, the objective is proposed, not claimed achieved; existing evidence is labeled as such; future evaluation is labeled as such.

### RQ-1

- **Objective (proposed)**: Characterize the systematic misclassification patterns of general-purpose FER classification on this dataset, including which expression categories are most affected and in which direction errors concentrate.
- **Research Activity**: Error/confusion analysis across the full label set; statistical description of error concentration (e.g., which off-diagonal confusion-matrix cells are disproportionately large).
- **Output**: An error-pattern characterization report/table (extending, not replacing, `docs/RESEARCH_FINDINGS.md` §3–4).
- **Evidence (existing)**: R1 audit (`reports/audit_summary_metrics.csv`), R8 error analysis (`reports/arcface_error_analysis/overall_error_analysis.csv`) already provide a substantial starting evidence base.
- **Evidence (future)**: would likely need deeper qualitative inspection of specific misclassified cases (not yet performed) to move from "pattern observed" to "pattern explained."
- **Potential Contribution**: primarily **empirical** (a characterized error pattern for this dataset/classifier); possibly **knowledge** if a transferable explanatory mechanism is identified (not yet available — see Theory gap, Phase 1 audit).

### RQ-2

- **Objective (proposed)**: Determine the extent to which general-purpose FER classification accuracy differs across measured skin-tone categories in this dataset.
- **Research Activity**: Subgroup accuracy comparison; association testing (e.g., Fisher's exact, as already used); explicit handling of the `Unknown` bucket.
- **Output**: A skin-tone-stratified performance report.
- **Evidence (existing)**: R7/R8 already provide this for HSEmotion on N=135 (Fisher's exact OR=5.88, p=0.0027) and N=227 (`reports/audit_per_skin_tone_accuracy.csv`).
- **Evidence (future)**: a larger or more balanced Dark/Medium-Dark sample, and/or a resolution strategy for the `Unknown` bucket, would strengthen the finding's robustness.
- **Potential Contribution**: primarily **empirical** (a documented, in-sample association, on a real-world non-benchmark population — this specific population/measurement combination was not found elsewhere in the Phase 3 literature review); not causal, not a fairness/design contribution unless a mechanism or intervention is separately proposed.

### RQ-3

- **Objective (proposed)**: Characterize FER misclassification patterns and determine whether/how they vary across measured skin-tone categories.
- **Research Activity**: Combination of RQ-1 and RQ-2's activities, cross-tabulated.
- **Output**: A combined error-by-subgroup characterization (extending R8, `reports/arcface_error_analysis/skin_tone_analysis.csv` + `neutral_error_analysis.csv`).
- **Evidence (existing)**: R8 already began exactly this combination.
- **Evidence (future)**: deeper statistical treatment of the joint (class × skin-tone) distribution, which R8 did not fully perform (R8 reported class-level and skin-tone-level findings largely separately).
- **Potential Contribution**: **empirical**, with possible **knowledge** contribution if a consistent joint pattern (e.g., "the Neutral→Angry pattern is itself unevenly distributed across skin-tone buckets") is found and explained — not yet established either way.

### RQ-4

- **Objective (proposed)**: Evaluate and compare a face-representation-based FER approach's performance and error pattern to a general-purpose baseline's, across measured skin-tone categories.
- **Research Activity**: Controlled comparison (as R7 already modeled methodologically), extended with an explicit skin-tone-stratified evaluation lens as a *primary*, not secondary, analysis axis.
- **Output**: A skin-tone-stratified comparative evaluation.
- **Evidence (existing)**: R7's comparison exists (40.74% vs. 36.30%, N=135, McNemar p=0.4614) and R7/R8 already include a skin-tone breakdown of it — but that breakdown was produced as *secondary* analysis, not as the RQ's primary object, per the current repository's own framing.
- **Evidence (future)**: if RQ-4 is to be more than a relabeling of already-existing R7/R8 work, it would need either (a) a justificatory-knowledge basis for *why* a representation-based approach should behave differently across skin tone (currently `MISSING`, Phase 1 audit "Theory" row), or (b) additional representation-model instances beyond the one already built, to test whether the finding is specific to ArcFace or general to the approach class.
- **Potential Contribution**: potentially **design** (if requirements/theory are built first, per the Phase 1 audit's guidance) and/or **empirical** (a skin-tone-stratified comparative result); **not yet a design contribution as things currently stand**, since Requirements/Theory remain `MISSING`.

### RQ-5

- **Objective (proposed)**: Determine whether an ArcFace-based FER approach outperforms HSEmotion on this dataset.
- **Research Activity**: Controlled comparison — **already fully executed** in R7.
- **Output**: Already produced (`reports/arcface_evaluation/comparison_metrics.csv`, `statistical_tests.csv`).
- **Evidence (existing)**: Complete — accuracy 40.74% vs. 36.30%, McNemar p=0.4614 (not significant).
- **Evidence (future)**: none needed; the RQ is already answered by existing evidence, which is precisely the reverse-engineering problem flagged throughout this document.
- **Potential Contribution**: minimal beyond what R7 already reports; framing existing completed work as a forward RQ does not, by itself, generate new contribution.

---

## 8. Contribution Test

| Candidate | Empirical Contribution | Design Contribution | Knowledge Contribution |
|---|---|---|---|
| RQ-1 | Yes — characterized error pattern, this dataset/classifier | No (no artifact designed) | Possible, if a transferable explanatory mechanism is found (not yet available) |
| RQ-2 | Yes — documented skin-tone-stratified association, this dataset | No | Possible, if connected to/extending the general literature pattern (Hosseini et al. 2025; Buolamwini & Gebru 2018) with appropriate measurement-system caveats |
| RQ-3 | Yes — combined characterization | No | Possible, same basis as RQ-1/RQ-2 combined |
| RQ-4 | Yes, if executed | Possible, only if Requirements/Theory are built first (currently `MISSING`) | Possible, if a representation-based mechanism's behavior across skin tone is explained, not just measured |
| RQ-5 | Minimal (already produced) | No | No — the question has already been answered by existing evidence; no new knowledge is generated by re-asking it as an RQ |

A purely evaluative RQ (RQ-2, RQ-5) is not assumed to automatically produce a design contribution, consistent with the phase instruction — none of RQ-1/RQ-2/RQ-3 claim a design contribution here.

---

## 9. Negative-Result Test

| Candidate | Outcome A (pattern found / approach performs as expected) | Outcome B (pattern not found / approach does not outperform) | Meaningful under Outcome B? |
|---|---|---|---|
| RQ-1 | A specific, explainable error concentration is characterized. | No clear systematic pattern beyond what's already known is found. | **Yes** — a null/weak-pattern finding is still a valid empirical characterization (Rule 4: negative results are valid), and would itself be informative (e.g., "the Neutral→Angry pattern does not extend to other classes in an explainable way"). |
| RQ-2 | A clear, consistent skin-tone-stratified accuracy difference is found. | No significant or consistent difference is found (e.g., a larger sample changes the Fisher's exact result). | **Yes** — a null finding here is scientifically meaningful too: it would suggest the originally-observed association (OR=5.88, p=0.0027) may not be robust at larger scale, which is itself worth reporting, not hiding. |
| RQ-3 | Error patterns and skin-tone variation are found to be jointly related. | Error patterns and skin-tone variation appear independent, or the joint analysis is inconclusive due to small cell sizes. | **Yes**, though weaker — an inconclusive joint result due to sample size is a legitimate methodological finding (a boundary condition on what small real-world datasets can support), but is less satisfying as a standalone contribution than RQ-1 or RQ-2's null results. |
| RQ-4 | A representation-based approach shows a materially different (not necessarily better) error/skin-tone profile than the baseline. | No material difference is found — mirroring R7's existing McNemar p=0.4614 result. | **Yes, if framed correctly** — Rule 4 explicitly protects this: "the proposed artifact does NOT have to outperform the baseline." A null result here would still characterize a boundary condition (e.g., "this class of representation-based approach does not resolve this dataset's skin-tone-stratified accuracy gap either"), which is real knowledge. **Risk**: if RQ-4 is worded or motivated as "does the new approach fix the problem," Outcome B risks being read as thesis failure rather than valid finding — wording must avoid this framing. |
| RQ-5 | ArcFace is shown to outperform HSEmotion. | ArcFace does not outperform HSEmotion — **this is the actual, already-obtained result** (McNemar p=0.4614). | **No, not meaningfully, as currently worded** — because the RQ already has its answer, "Outcome B" isn't a possible future finding to guard against, it's the settled present state; the RQ produces no new empirical, design, or knowledge contribution under either outcome, since the outcome is already known before the "research" begins. |

---

## 10. Skin-Tone and ArcFace Wording Discipline (Applied Throughout)

Per the phase's explicit constraints, checked against every RQ above:

- No RQ uses "racial bias," "ethnic bias," "Papuan bias," or "biological effect of skin tone" — all skin-tone RQs (RQ-2, RQ-3, RQ-4) use "measured skin-tone categories" or equivalent neutral phrasing.
- Every skin-tone RQ's data-answerability section explicitly notes: skin tone is image-derived (not self-reported/ethnicity), ethnicity is not recorded in the dataset, the `Unknown` bucket exists and is excluded from accuracy comparisons, and the current sample (N=46/N=32) is small and uneven.
- No RQ uses "ArcFace emotion classifier" — RQ-4 and RQ-5 both correctly use "ArcFace-based face representation" framing (RQ-4) or, where RQ-5 names ArcFace directly, it is in the context of the already-existing R7 comparison, not as a classifier-role claim.
- Per Phase 3's finding, every mention of ArcFace above (RQ-4, RQ-5) is accompanied by the explicit statement that ArcFace-as-feature-extractor-for-FER is **not** considered novel as a technique (`STATE_OF_ART_AND_GAP.md` §7) — RQ-4's potential contribution is explicitly scoped to the skin-tone-stratified evaluation *context*, not to the technique itself.

---

## 11. RQ Comparison Table

| Candidate | Core Focus | Gap | Solution-Neutral? | Data Ready? | Evaluation Ready? | Contribution | Scope Risk | Overall |
|---|---|---|---|---|---|---|---|---|
| RQ-1 | FER error-pattern characterization | G1 (moderate) | YES | Strong (N=227/N=135) | Strong | Empirical (+possible knowledge) | Low | **STRONG** |
| RQ-2 | Skin-tone-stratified performance | G2 (moderate-strong) | YES | Moderate (small/uneven subgroups, Unknown bucket) | Moderate | Empirical (+possible knowledge) | Moderate (overclaiming risk if discipline slips) | **STRONG, with discipline requirement** |
| RQ-3 | Combined error + skin-tone | G1+G2 | YES | Moderate | Moderate | Empirical (+possible knowledge) | Moderate (broader scope, small joint cells) | **MODERATE-STRONG** |
| RQ-4 | Representation-based approach across skin tone | G3 (moderate, contingent) | PARTIALLY | Moderate (existing ArcFace+LR instance only; more instances = new work) | Moderate-Weak (small joint cells) | Empirical (+possible design, if Requirements/Theory built first) | Moderate-High (contingent on RQ-2/3, risk of solution-first drift) | **MODERATE, conditional** |
| RQ-5 | ArcFace vs. HSEmotion (unconditioned) | **BLOCKED** (no gap) | NO | Strong (already collected) | Strong (already executed) | Minimal | **HIGH** (reverse-engineered, already answered) | **WEAK — not recommended** |

No final RQ is selected by this table — it is a structured comparison only.

---

## 12. Recommended Shortlist

*(Recommendation only — final RQ remains a supervisor/user decision, per Rule 6.)*

### Strongest Candidate

**RQ-1** (FER error-pattern characterization). Highest scores across problem relevance, answerability, data availability, and scope suitability, with the lowest overclaiming risk of any candidate. It is fully solution-neutral and already has the deepest existing evidence base (R1, R5, R8) to build from without requiring new data collection.

### Safest Candidate

**RQ-1**, for the same reasons — but if a broader scope is preferred, **RQ-2** is the safest candidate that still engages the skin-tone dimension, *provided* the wording discipline in §10 is maintained throughout the eventual proposal and thesis, since it carries the highest reward-to-discipline-risk ratio of the skin-tone-involving candidates.

### Highest-Potential Candidate

**RQ-4** (representation-based approach across skin tone). Has the clearest path to a genuinely novel contribution angle (the skin-tone-stratified evaluation context that Phase 3's literature review did not find elsewhere) and could plausibly support a design contribution — but only if Requirements and Theory (currently `MISSING` per the Phase 1 audit) are built *before* the artifact is re-justified, not backfilled to justify the already-built ArcFace+LR pipeline. This is real potential with real, explicitly acknowledged risk.

### Weakest Candidate

**RQ-5** (ArcFace vs. HSEmotion, unconditioned). Should not be carried forward as worded. It has no traceable gap (Phase 3 found ArcFace-for-FER is not novel, and this RQ adds no further angle such as skin-tone-stratification), fails the solution-neutrality test outright (NO), and — most fundamentally — is already fully answered by existing R7 evidence, meaning it cannot generate new contribution under any outcome. Its only legitimate value in this document is as the cautionary contrast case referenced throughout.

---

## Decision Required

1. **Currently strongest candidate**: RQ-1 (FER error-pattern characterization), on problem relevance, answerability, data readiness, and low overclaiming risk.
2. **Currently safest candidate**: RQ-1, or RQ-2 if the skin-tone dimension is considered essential to the thesis's motivation (per the author's original framing in `docs/RESEARCH_FRAMING.md`, which the supervisor may weight differently than this document does).
3. **Currently highest-potential candidate**: RQ-4, contingent on Requirements/Theory being built first and on RQ-2/RQ-3 first establishing the skin-tone finding is robust enough to warrant testing an alternative representation against it.
4. **Supervisor/user decision required**:
   - Whether the thesis should be scoped primarily around Direction A (error characterization), Direction B (skin-tone robustness), a combined A+B, or should retain a Direction C (representation-based/ArcFace) component — and if so, whether ArcFace specifically or the "face-representation-based approach" class more generally.
   - Whether RQ-5-style direct ArcFace-vs-HSEmotion framing is acceptable as a *secondary* research question (e.g., nested inside RQ-4) even though it is not viable as a *primary* RQ on its own, given that R7's result already exists and is not in dispute.
   - Whether the skin-tone dimension (RQ-2/RQ-3/RQ-4) should be primary or secondary to the final thesis scope — this materially changes Phase 5's (Design Requirements) starting point.
5. **Evidence/clarification still needed before locking the RQ**:
   - Confirmation (from the supervisor) of which framing best matches the thesis's intended scope and the program's expectations for a Master's-level design-research proposal.
   - For RQ-4 specifically: whether building additional face-representation-model instances (beyond the existing ArcFace+LR one) is within the thesis's remaining time/resource budget, or whether RQ-4 should be scoped to only the existing instance (with that scoping made explicit, not implicit).
   - Resolution (or explicit acceptance) of the five "requires verification" citations from Phase 3 before any RQ's gap justification is finalized in proposal prose.

STOP — waiting for approval for the next phase.
