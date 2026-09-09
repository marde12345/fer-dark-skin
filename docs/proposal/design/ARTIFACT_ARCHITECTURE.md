# Artifact Architecture

> **Purpose**: Determine what artifact type is actually justified by the requirements established in `docs/proposal/design/DESIGN_REQUIREMENTS.md` — not what the existing codebase happens to already contain. No RQ, artifact, or methodology is finalized here. ArcFace + Logistic Regression is not assumed to be the artifact anywhere in this document; that assumption is explicitly tested and, where it fails, said so directly.

---

## 1. Artifact Type Analysis

| Artifact Type | Requirements Satisfied | Problem Fit | Research Contribution Potential | Evaluation Feasibility | Risk |
|---|---|---|---|---|---|
| **Method** (a defined procedure: input → process → decision rules → output, per guideline BAB 11 §11.4) | F-01, F-02, A-01, A-02, A-03, D-01–D-04, E-01–E-03, R-01–R-03 — nearly the full requirements set can be expressed as a procedure | Strong — the practical problem (`PROBLEM_ARCHITECTURE.md`) is fundamentally about *how to reliably characterize* FER error/skin-tone patterns, which is exactly what a method specifies | Moderate — a well-specified method (input/process/decision-rules/output, roles, conditions of use) is itself a valid, if modest, design-research contribution per the guideline, distinct from just running one experiment | High — a method's steps are directly checkable against its own specification | Low — closest fit to what the requirements actually demand; least likely to overclaim |
| **Framework** (purpose, scope, components, relationships, process of use, expected outcome, per guideline BAB 11 §11.5) | Same requirement coverage as Method, plus explicit componentization (A-03/D-03 skin-tone stratification, E-02/E-03 statistical layer) | Strong, if the artifact is meant to be *reused* across future datasets/classifiers, not just applied once here | Higher than Method *if* genuinely reusable — but guideline explicitly warns a labeled-box diagram without a use-process explanation is not really a framework (p.173–174) | Moderate — harder to evaluate a framework's general reusability with only one dataset available | Moderate — risk of over-claiming "framework" when only one instantiation (this dataset) has ever been run through it |
| **Pipeline** (an ordered, close relative of Method, emphasizing data flow through stages) | F-01, D-01–D-04, R-01–R-02 | Strong for the *data-handling* half of the requirements, weaker for the *analytical/evaluative* half (A-01–A-03, E-01–E-03) | Low as a standalone contribution — a pipeline alone (detect → crop → predict) is largely already existing infrastructure (`src/fer_dataset/pipeline/`), not new design knowledge | High — pipelines are mechanically easy to verify (does data flow through correctly) | Moderate — risk of mistaking existing infrastructure for the research contribution (this is the exact trap the guideline warns against, BAB 11 p.169) |
| **Model** (descriptive/predictive/computational, per guideline BAB 11 §11.3) | F-01, F-02 only, if "model" means a classifier | Weak on its own — a single predictive model does not, by itself, satisfy the analytical/skin-tone/reproducibility requirements that dominate the requirements set | Low, standalone — and directly undermined by `STATE_OF_ART_AND_GAP.md` §7's finding that an ArcFace-based FER *model* is not novel | High (models are the easiest of all candidates to evaluate numerically) | High — this is the candidate most likely to collapse into "we trained a classifier," which is evaluation, not design (see §11 below) |
| **Evaluation framework/procedure** (a structured way of assessing FER systems — criteria, metrics, baseline, statistical tests, subgroup handling) | A-01–A-03, D-02–D-04, E-01–E-03, X-02–X-03 — the requirements set's largest cluster | Strong — this is arguably the requirements set's actual center of gravity: most `MUST` items are about *how to evaluate and report*, not *how to classify* | Moderate-to-high — a rigorous, reusable evaluation procedure for FER on small, skin-tone-stratified, real-world datasets is a plausible, modestly novel contribution, since the literature review (`STATE_OF_ART_AND_GAP.md` §5, G3/G4) did not find this combination addressed elsewhere | High — an evaluation procedure evaluates itself by whether it can be run consistently and reproduce known findings (E-01) | Low — closely matches actual requirement density; main risk is scope creep into claiming more than "a way of evaluating," e.g., silently becoming a Model candidate |
| **Design principle** (goal + context + mechanism, prescriptive knowledge for a *class* of artifacts, per guideline BAB 10 §10.6) | Could summarize A-01–A-03, D-02–D-04 as a *transferable prescription* ("when evaluating FER on small, skin-tone-heterogeneous, real-world datasets, do X") rather than a specific tool | Strong in principle, but premature — requires a Method/Framework/Evaluation-procedure to already exist and be tested before a design principle can credibly be extracted from it (guideline p.163: principles are the higher-abstraction output of validated design work, not a starting point) | Highest ceiling of all candidates *if* eventually reached, but not achievable as a standalone artifact at this stage | Low, currently — nothing to evaluate yet at this abstraction level | High if attempted now — would be an unsupported abstraction leap without an underlying tested method first |

**Reasoning summary**: the requirements set (`DESIGN_REQUIREMENTS.md`) is dominated by analytical, data-handling, evaluation, and reproducibility requirements (A-01–A-03, D-01–D-04, E-01–E-03, R-01–R-03) — not by requirements that specify *what a new classifier must do*. This weighs the artifact-type analysis toward **Method** and **Evaluation framework/procedure**, and against **Model** as a standalone artifact. **Pipeline** alone is largely already-existing infrastructure, not new design. **Framework** and **Design principle** are plausible *ceiling* outcomes but are not yet earned — they require the Method/Evaluation-procedure layer to exist and be validated first.

---

## 2. Technology vs. Artifact

### Existing Technologies (not designed by the researcher; used as-is)

- **ArcFace** (`buffalo_l`/`w600k_r50`) — a pretrained face-verification embedding model.
- **InsightFace/SCRFD** — pretrained face-detection model.
- **HSEmotion** (`enet_b0_8_best_vgaf`) — pretrained FER classifier, used as baseline.
- **MediaPipe** — pretrained facial-landmark model, used for skin-tone-adjacent landmark analysis.
- **Logistic Regression** — a standard, off-the-shelf classification algorithm (scikit-learn), not itself designed by the researcher.

### Existing Research Assets (produced by prior work in this repository; available to build on, not automatically "the artifact")

- The current dataset (227 labeled face crops, sourced from *Pesta Babi*).
- The current manual ground-truth labels.
- The current data-processing pipeline (`src/fer_dataset/pipeline/`).
- Existing experiments and their results (R1–R9: HSEmotion audit, CLAHE experiment, ArcFace+LR training/evaluation, error/skin-tone analysis, cross-experiment consistency validation).
- Existing evaluation scripts (`tools/extract_arcface_embeddings.py`, `tools/train_arcface_classifier.py`, `tools/evaluate_arcface_vs_hsemotion.py`, `tools/analyze_arcface_errors.py`).

### Researcher Design (what has actually been designed/integrated, as opposed to used off-the-shelf)

- The **decision to evaluate a frozen face-representation model as a feature source for FER**, rather than fine-tuning or training a representation model from scratch (a design decision, documented in `docs/ARCFACE_EXPERIMENT_DESIGN.md`).
- The **evaluation procedure** itself: filename-based (not row-order) identity joins, temporal-block grouping as a leakage-prevention proxy, `StratifiedGroupKFold` cross-validation, the specific combination of McNemar's test + group-aware bootstrap + Fisher's exact test, and the explicit N/A-vs-0 handling for ArcFace's structurally-absent classes. This is genuinely researcher-designed integration, not a reused off-the-shelf tool.
- The **skin-tone-stratified, `Unknown`-aware reporting convention** (excluding rather than imputing `Unknown`, always reporting subgroup N alongside metrics) — a researcher-authored analytical convention, not something any of the underlying technologies provide by default.
- The **cross-population consistency-checking discipline** (never merging N=227 and N=135, verifying findings reproduce across both) — again, a researcher-authored methodological practice, not a technology.

### Potential Artifact

Based on the above, **the artifact — if one is confirmed by later phases — is most plausibly the evaluation procedure/method itself** (the specific combination of joins, grouping, statistical tests, subgroup handling, and reporting conventions), **not** any of the underlying pretrained technologies (ArcFace, HSEmotion, MediaPipe), and **not** the raw data pipeline (which is existing infrastructure, not new design). This directly answers the phase's caution: **the existence of a software pipeline in this repository does not automatically make that pipeline the research artifact.**

---

## 3. Requirement-to-Artifact Mapping

| Requirement ID | Requirement | Candidate Artifact Component | Mechanism | Evaluation |
|---|---|---|---|---|
| F-01 | Per-sample predictions producible | Prediction-generation step | Apply a named classifier to a defined population | Output reviewable per-sample (already demonstrated, R1/R7) |
| F-02 | Named baseline comparison | Baseline-comparison step | Compare against HSEmotion specifically | Baseline identity documented |
| A-01 | Per-class error visibility | Confusion/error-analysis component | Cross-tabulate ground truth × prediction | Per-class breakdown reproducible |
| A-02 | Association-vs-causal distinction | Reporting-convention component (not a technical mechanism) | Explicit labeling rule applied at report-generation time | Checked presence in output, not computed |
| A-03 | Skin-tone-stratified metrics with N | Subgroup-stratification component | Group by skin-tone bucket, compute metric + N per group | N reported alongside every stratified metric |
| D-01 | Independent ground truth | (Existing research asset — manual labels) | N/A — data property, not an artifact mechanism | Label source documented as independent of prediction |
| D-02 | Explicit class-scarcity exclusion | Class-inclusion filter | Apply documented minimum-count threshold | Exclusion criteria stated in any per-class report |
| D-03 | `Unknown` skin-tone handling | Skin-tone bucket with explicit Unknown category | Exclude, never impute, `Unknown` from comparisons | Unknown appears as its own row, excluded from Dark/Medium-Dark comparison |
| D-04 | Population N/source stated with metric | Population-labeling convention | Attach N + source to every reported metric | N and source present with every metric |
| E-01 | Cross-population reproduction check | Reproduction-checking component | Compute the same metric on ≥2 independently-derived populations, compare | Reproduction check present in output |
| E-02 | Skin-tone association test | Statistical-testing component | Apply an association test appropriate to small/uneven subgroups (e.g., Fisher's exact) | Test result accompanies stratified claim |
| E-03 | Paired significance for comparative claims | Statistical-testing component (shared with E-02) | Apply a paired test (e.g., McNemar) on a matched population | Paired test accompanies comparative claim |
| R-01 | Documented exclusion/funnel | Funnel-documentation component | Record stage → N at each exclusion step | Funnel reproducible from documented rules |
| R-02 | Grouping/leakage prevention | Grouping component (only if a classifier is trained) | Temporal-block (or better) grouping, checked for train/eval overlap | Group-overlap absence checked and stated |
| R-03 | Fixed seeds/parameters | Configuration-documentation component | Record seed/resampling-count values alongside any stochastic result | Seed/parameters stated with result |
| X-01 | Data provenance/consent documentation | **Not implementable by the artifact itself** — this is a documentation/institutional requirement, not a technical component | N/A | **Flagged: cannot be satisfied by any artifact mechanism; requires separate, non-technical resolution (see Phase 5, unresolved)** |
| X-02 | Skin-tone/ethnicity separation | Reporting-convention component (shared with A-02) | Explicit statement template attached to any skin-tone output | Checked presence in output |
| X-03 | Negative-result visibility | Reporting-convention component | No suppression rule — all computed results (including null/non-significant) are included in output | Null-result presence checked, not just positive results |

**Flag, per instruction**: **X-01 cannot be implemented or represented by any artifact component** — it is a provenance/consent question that exists prior to and outside of any technical design, and no mechanism in a Method/Framework/Evaluation-procedure can resolve it. It remains an open blocker (carried from Phase 5), not a design element.

**No component below was found to be an `UNJUSTIFIED DESIGN ELEMENT`** — every artifact component listed above traces to at least one Phase-5 requirement. (This is a check on the mapping *as built here*, not a claim that every technically possible component would automatically be justified — see §9 for how this applies to a candidate artifact.)

---

## 4. Candidate Artifacts

### Candidate A — Reproducible FER Error-Characterization Method

1. **Purpose**: Provide a defined, repeatable procedure for characterizing an FER classifier's systematic, class-specific error patterns on a given evaluation population.
2. **Intended context**: Small-to-moderate, real-world (non-benchmark) FER datasets where systematic error patterns are suspected but not yet formally characterized.
3. **Intended user/stakeholder**: **Plausible, not evidence-supported** — researchers or practitioners evaluating an FER classifier's reliability on a specific population before deployment or further study; no stakeholder evidence exists in this repository (per `PROBLEM_ARCHITECTURE.md` §3), so this is stated as plausible only.
4. **Problem addressed**: The Practical/Knowledge Problem from `PROBLEM_ARCHITECTURE.md` §2 — that a classifier's error behavior on this dataset is observed but not yet systematically, reproducibly characterized.
5. **Requirements satisfied**: F-01, F-02, A-01, A-02, D-01, D-02, D-04, E-01, R-01, R-03, X-02 (partially, if error reporting touches subgroup data), X-03.
6. **Core mechanism**: Apply classifier → cross-tabulate ground truth × prediction → check consistency across ≥2 populations → report class-specific patterns with explicit exclusion criteria.
7. **Components**: prediction-generation step, confusion/error-analysis component, reproduction-checking component, funnel-documentation component, reporting conventions.
8. **Inputs**: labeled face-image dataset, a classifier's predictions.
9. **Outputs**: per-class error report, confusion matrix, cross-population consistency statement.
10. **Assumptions**: ground-truth labels are of adequate quality (Phase 5 §12); classifier predictions are available in a filename-keyed, auditable form.
11. **Constraints**: 5-class scope (D-02); N=227/N=135 population distinction must be preserved, not merged.
12. **Evaluation strategy**: does the method, when applied, actually surface a class-specific pattern that reproduces across populations (as already demonstrated for Neutral→Angry, R1/R9)?
13. **Expected contribution**: primarily **empirical** (a characterized error pattern) and **method-level** (a reusable characterization procedure); minimal design/artifact novelty on its own, since confusion analysis itself is a well-established technique.
14. **Risk**: could be seen as too close to a standard evaluation practice to constitute a distinct research contribution, unless the *combination* (small real-world dataset + cross-population reproduction discipline) is explicitly argued as the contribution.

### Candidate B — Skin-Tone-Stratified FER Evaluation Procedure

1. **Purpose**: Provide a defined, repeatable procedure for evaluating and reporting FER classifier performance across measured skin-tone categories, with explicit handling of small/uneven subgroups and an unmeasurable (`Unknown`) category.
2. **Intended context**: Real-world FER datasets where skin-tone measurement is available but incomplete, and subgroup sizes are too small for standard, benchmark-scale fairness-audit techniques.
3. **Intended user/stakeholder**: **Plausible, not evidence-supported** — same caveat as Candidate A.
4. **Problem addressed**: The skin-tone-stratified accuracy variation observed in `PROBLEM_ARCHITECTURE.md` (Fisher's exact OR=5.88, p=0.0027) and its currently under-characterized relationship to standard-benchmark demographic-bias literature (Gap G2, `STATE_OF_ART_AND_GAP.md`).
5. **Requirements satisfied**: F-02, A-02, A-03, D-03, D-04, E-02, X-02, X-03.
6. **Core mechanism**: Stratify predictions by measured skin-tone bucket → exclude `Unknown` from comparison, report it separately → apply an association test appropriate to small/uneven subgroups → report association, not causal, findings.
7. **Components**: subgroup-stratification component, `Unknown`-handling component, statistical-testing component, reporting conventions (A-02/X-02).
8. **Inputs**: labeled face-image dataset with skin-tone measurement, a classifier's predictions.
9. **Outputs**: skin-tone-stratified accuracy/error report, association-test result, explicit non-causal framing statement.
10. **Assumptions**: the skin-tone measurement (LAB-luminance bucket) is a stable, consistent proxy across the dataset's conditions (Phase 5 §12 — not independently re-verified).
11. **Constraints**: Dark N=46, Medium-Dark N=32, Unknown N=57 (of N=135) — small, uneven, large unmeasured fraction.
12. **Evaluation strategy**: does the procedure, when applied, produce a result consistent with (though not necessarily identical to) the general literature pattern (Gap G2), while correctly avoiding conflation with race/ethnicity/causal claims?
13. **Expected contribution**: primarily **empirical** (an in-sample association, on a population/measurement combination not found elsewhere in the Phase 3 literature review); a possible **procedural/method** contribution if the `Unknown`-handling and small-subgroup-appropriate testing convention is judged distinct enough from standard fairness-audit practice to be worth stating as a reusable procedure.
14. **Risk**: **highest overclaiming risk of the three candidates** if the wording discipline (A-02/X-02) is not maintained rigorously throughout any artifact built around this candidate; small subgroup sizes limit how strong a claim the evaluation can support regardless of procedure quality.

### Candidate C — Face-Representation-Based FER Evaluation Framework (with Error and Skin-Tone Analysis)

1. **Purpose**: Provide a framework for evaluating a face-representation-based FER approach (of which the existing ArcFace+LR instance is one example) against a baseline classifier, with integrated error and skin-tone-stratified analysis.
2. **Intended context**: Settings where a face-representation-based alternative to a general-purpose FER classifier is being considered, and where its behavior (not just aggregate accuracy) needs characterizing.
3. **Intended user/stakeholder**: **Plausible, not evidence-supported** — same caveat as A/B.
4. **Problem addressed**: Gap G3 (`STATE_OF_ART_AND_GAP.md` §5) — that no literature found in the Phase 3 review evaluates a face-representation-based FER approach on a skin-tone-stratified, real-world population — **contingent on Candidates A and/or B first establishing this is worth investigating with an alternative representation**, per `RQ_OPTIONS.md` §2 (RQ-4's explicit contingency).
5. **Requirements satisfied**: all of Candidate A's + Candidate B's requirements, plus E-03, R-02 (only relevant if a second classifier is trained/compared).
6. **Core mechanism**: Candidates A + B's mechanisms, applied to (at least) two classification approaches — a baseline and a face-representation-based approach — with a paired significance test added for the comparative claim.
7. **Components**: all of A + B's components, plus a representation-model integration point, a grouping/leakage-prevention component (R-02), and a paired-comparison statistical component (E-03).
8. **Inputs**: labeled face-image dataset with skin-tone measurement; at least two classifiers' predictions on a matched population.
9. **Outputs**: everything Candidates A and B output, plus a paired comparative-significance result.
10. **Assumptions**: a representation-based approach is available/buildable (currently satisfied by the existing ArcFace+LR instance, R5–R9); temporal-block grouping is an adequate leakage-prevention proxy (Phase 5 §12).
11. **Constraints**: everything from A + B, plus the compounding-small-cells risk already flagged in `RQ_OPTIONS.md` §3 for RQ-4 (class × skin-tone cross-tabulation on an already-small N=135 with 5-class scope).
12. **Evaluation strategy**: does the framework, when applied to a face-representation-based approach, produce a materially different (not necessarily "better") error/skin-tone profile than the baseline, evaluated with a paired significance test?
13. **Expected contribution**: **empirical** (a comparative, skin-tone-stratified result), and **possibly design** (only if Requirements/Theory for *why* a representation-based approach should behave differently are built — currently `MISSING` per the Phase 1 audit) — **not** an artifact-novelty contribution from ArcFace itself (§6 below).
14. **Risk**: **highest structural risk of the three** — this is the candidate most likely to silently reintroduce the solution-first framing this entire proposal-design track was built to avoid, unless it is explicitly derived from A/B's findings rather than backfilled to justify the already-built ArcFace+LR pipeline (the same warning already given in `PROBLEM_ARCHITECTURE.md` Framing C and `RQ_OPTIONS.md` RQ-4).

---

## 5. Design Hypotheses

Explicitly labeled as hypotheses, not established results:

> **DESIGN HYPOTHESIS (Candidate A)**: If a reproducible, cross-population error-characterization procedure (per-class confusion analysis + explicit exclusion criteria + reproduction checking) is applied under the context of a small, real-world FER dataset, and satisfies requirements F-01/F-02/A-01/A-02/D-01/D-02/D-04/E-01/R-01/R-03/X-03, then a class-specific, reproducible error pattern (if one genuinely exists in the data) should be observable and distinguishable from noise through cross-population consistency evidence (E-01).

> **DESIGN HYPOTHESIS (Candidate B)**: If a skin-tone-stratified evaluation procedure (subgroup stratification + explicit `Unknown` handling + small-sample-appropriate statistical testing) is applied under the context of a real-world dataset with incomplete skin-tone measurement, and satisfies requirements F-02/A-02/A-03/D-03/D-04/E-02/X-02/X-03, then an in-sample skin-tone-stratified performance association (if one genuinely exists) should be detectable and reportable without conflating it with ethnicity or causal claims.

> **DESIGN HYPOTHESIS (Candidate C)**: If a face-representation-based FER approach is evaluated under a framework combining Candidates A and B's mechanisms plus a paired comparative-significance test, and satisfies requirements E-03/R-02 in addition to A's and B's, then any difference (or lack thereof) between the representation-based approach's and the baseline's error/skin-tone profile should be observable as a statistically-qualified comparative result — **which may show no significant difference**, and such a null result would still be a valid design-hypothesis test outcome (Rule 4).

None of these hypotheses is presented as an established result — Candidate A's and B's mechanisms have already been *exercised* (not yet formally *validated as an artifact*) in R1–R9; Candidate C's has been exercised once (R7) with a null comparative result (McNemar p=0.4614), which is evidence the hypothesis is testable, not evidence it is confirmed.

---

## 6. ArcFace Role

Evaluated explicitly against the possible roles listed in the phase instructions:

- **Requirement**: **No.** No requirement in `DESIGN_REQUIREMENTS.md` mandates ArcFace (confirmed there in its own §9, reconfirmed here).
- **Design mechanism**: **Only within Candidate C**, and only as *one instance* of the broader mechanism class "face-representation-based approach" — not as a uniquely required mechanism.
- **Implementation choice**: **Yes, this is its most accurate role** — among available pretrained face-representation models, ArcFace is the one already integrated and evaluated (R5–R9); a different backbone could, in principle, fill the same role.
- **Existing asset**: **Yes** — the embeddings, trained classifier, and evaluation results already exist and are reusable if Candidate C is pursued.
- **Experimental treatment**: **Yes, if Candidate C is pursued** — ArcFace-based prediction would function as the "treatment" condition compared against the HSEmotion "control"/baseline condition.
- **Not necessary**: **True for Candidates A and B** — neither requires ArcFace at all; both are fully specifiable and evaluable using only the existing HSEmotion baseline and ground-truth labels.

**What would the research contribution be beyond simply applying ArcFace, if it appears in the artifact (Candidate C)?** Per `STATE_OF_ART_AND_GAP.md` §7, ArcFace-as-feature-extractor-for-FER is **not novel** — Altaha et al. (2023) and Waldner & Mitra (2024) already published this exact technique. Therefore, **applying ArcFace by itself is not a defensible contribution claim**. The only defensible contribution angle identified across all prior phases is **context/evaluation-design**: evaluating a face-representation-based approach specifically on a skin-tone-stratified, real-world, non-standard-benchmark population — a combination the Phase 3 literature review did not find elsewhere (Gap G3, explicitly marked *contingent* and *"not found," not "does not exist"*). **If Candidate C is pursued without this specific context/evaluation-design framing, no defensible contribution beyond "we applied an existing technique to a new dataset" currently exists** — this is stated directly, per instruction, rather than papered over.

---

## 7. HSEmotion Role

HSEmotion is treated as **baseline / comparison system** throughout all three candidates, consistent with its role in every prior phase (`DESIGN_REQUIREMENTS.md` §9 explicitly: "HSEmotion... is retained as such"). No requirement or candidate artifact repositions HSEmotion as part of the artifact being designed — it remains the fixed point of comparison against which any candidate's evaluation procedure is exercised. This is not revisited or changed here.

---

## 8. Artifact Boundary

| Element | Inside the Artifact | Outside the Artifact |
|---|---|---|
| Source video (*Pesta Babi*) | | ✓ (raw data source, not designed) |
| Dataset (face crops, labels) | | ✓ (existing research asset, input to the artifact, not the artifact itself) |
| Annotation/labeling process | | ✓ (existing research asset — the manual labeling procedure was not designed as part of this artifact) |
| Face detector (InsightFace/SCRFD) | | ✓ (existing technology, used as-is) |
| Face-representation model (ArcFace, if Candidate C) | Partially — as an *integration point*, not as a designed component itself | ✓ — the model's internals (training, architecture) are existing technology |
| Baseline classifier (HSEmotion) | | ✓ (existing technology, fixed comparison point) |
| Classifier (Logistic Regression, if Candidate C) | Partially — as an *integration point* | ✓ — the algorithm itself is existing technology |
| **Evaluation procedure** (joins, grouping, statistical tests, exclusion criteria) | ✓ — this is the core of the candidate artifacts | |
| **Subgroup-stratification and `Unknown`-handling convention** | ✓ | |
| **Reporting conventions** (association-vs-causal labeling, negative-result visibility, denominator preservation) | ✓ | |
| **Cross-population consistency-checking discipline** | ✓ | |
| Reporting/dashboard (e.g., `dashboard/index.html`) | | ✓ (a presentation layer built on top of artifact outputs, not the artifact's evaluative mechanism itself) |

The boundary is drawn to match §2's conclusion: **the artifact is the evaluation procedure/method and its associated conventions, not the underlying pretrained technologies, not the raw dataset/pipeline, and not the presentation layer.**

---

## 9. Preliminary Specification (Strongest Candidate: A, with B as an integrated secondary layer)

Per §10's comparison below, Candidate A (with B folded in as its skin-tone-stratified secondary analysis, matching the Structure A+B working direction) is the strongest candidate. Its preliminary specification:

| Specification | Description |
|---|---|
| **Purpose** | A reproducible procedure for characterizing an FER classifier's systematic, class-specific error patterns on a defined evaluation population, with skin-tone-stratified performance/error patterns as an integrated secondary analytical layer. |
| **Context** | Small-to-moderate, real-world (non-benchmark) FER datasets with incomplete demographic/skin-tone measurement, where systematic error patterns are suspected but not yet formally, reproducibly characterized. |
| **User/Stakeholder** | **Plausible, not evidence-supported** — researchers/practitioners evaluating FER classifier reliability on a specific, non-benchmark population. No stakeholder evidence exists in this repository; this remains an open item (`PROBLEM_ARCHITECTURE.md` §3, `DESIGN_REQUIREMENTS.md` unresolved items). |
| **Problem** | The Practical/Knowledge Problem in `PROBLEM_ARCHITECTURE.md` §2 — observed but not yet systematically characterized classifier error behavior, secondarily stratified by measured skin-tone category. |
| **Requirements** | F-01, F-02, A-01, A-02, A-03, D-01–D-04, E-01, E-02, R-01, R-03, X-02, X-03 (nearly all of `DESIGN_REQUIREMENTS.md` except the comparative-classifier-specific E-03/R-02, which belong to Candidate C only). |
| **Mechanism** | Apply classifier(s) → cross-tabulate ground truth × prediction (overall and per skin-tone bucket, `Unknown` excluded from comparison) → check consistency across ≥2 populations where available → apply association testing to any stratified claim → report with explicit association-vs-causal and denominator-preserving conventions. |
| **Components** | Prediction-generation step; confusion/error-analysis component; subgroup-stratification component with `Unknown` handling; statistical-testing component (association-level); reproduction-checking component; funnel-documentation component; reporting conventions. |
| **Inputs** | Labeled face-image dataset (ground truth independent of any prediction); a classifier's predictions; skin-tone measurement per sample (where available). |
| **Outputs** | Per-class error report; confusion matrix; skin-tone-stratified accuracy/error report with N per subgroup; association-test result; cross-population consistency statement; explicit exclusion/funnel documentation. |
| **Evaluation** | Does the procedure, when applied, reproduce the already-observed patterns (Neutral→Angry across N=227/N=135; skin-tone association on N=135) and remain auditable/reproducible from documented parameters and exclusion criteria? |

This is stated, per the guideline, as a **design hypothesis**, not a final truth — later phases (Methodology, Phase 7; Evaluation Architecture, Phase 8) will test and likely refine it.

---

## 10. Design Alternatives Comparison

| Criterion | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| Problem fit | Strong | Moderate | Moderate (contingent on A/B) |
| Requirement coverage | High (11 of 18 requirements) | Moderate (8 of 18) | Highest (all 18, but E-03/R-02 only activate if pursued) |
| RQ compatibility | RQ-1, RQ-3 | RQ-2, RQ-3 | RQ-4 only (and only if contingency is honored) |
| Design-research suitability | Moderate (leans evaluative, see §11) | Moderate (leans evaluative, see §11) | Moderate, with the highest *potential* if Requirements/Theory are built first — but currently weakest actual suitability, since it is closest to already-completed evaluative work (R7) |
| Evaluation feasibility | High (N=227/N=135 fully available) | Moderate (small/uneven subgroups) | Moderate-Low (compounds small subgroups with 5-class scope) |
| Novelty potential | Low-Moderate (confusion analysis is well-established; the reproduction-discipline framing is the main candidate novelty angle) | Moderate (context/measurement-combination novelty per Gap G2, if literature connection stays honest about measurement-system differences) | Low on the ArcFace technique itself (confirmed not novel); Moderate on the context/evaluation-design angle only (Gap G3) |
| Existing implementation reuse | High (R1, R8 already largely exercise this) | High (R7, R8 already largely exercise this) | High (R5–R9 already fully exercise this) — but high reuse here raises, not lowers, the reverse-engineering risk (§11) |
| Risk | Low | Moderate (overclaiming risk on skin-tone/ethnicity wording) | High (solution-first reintroduction risk; contribution-beyond-ArcFace risk) |
| Scope | Well-bounded, feasible for Master's thesis | Well-bounded, feasible, but thinner evidentiary ceiling given small subgroups | Broadest scope; feasible only if treated as contingent extension, not a standalone starting point |

### Strongest Candidate
**Candidate A** (with B integrated as its secondary layer, i.e., the combined A+B specification in §9) — highest requirement coverage relative to its risk, most direct match to the strongest existing evidence, lowest overclaiming exposure.

### Safest Candidate
**Candidate A** alone (without B) — if an even more conservative scope is wanted, dropping the skin-tone secondary layer entirely removes essentially all of Candidate B's overclaiming risk while retaining the strongest single evidenced pattern (Neutral→Angry).

### Highest-Potential Candidate
**Candidate C** — the only candidate with a path to a genuinely under-explored angle (Gap G3, ArcFace × skin-tone-stratified evaluation), but only if built as a contingent extension of A/B, with Requirements/Theory established first, and with the contribution explicitly scoped to context/evaluation-design rather than the ArcFace technique itself.

### Highest-Risk Candidate
**Candidate C**, unconditionally — both the solution-first reintroduction risk and the "no defensible contribution beyond applying an existing technique" risk (§6) are concentrated here, and neither risk is present in Candidates A or B.

No candidate is selected as final here — this is a structured comparison only, per instruction.

---

## 11. Design-Research Test

For each candidate: is the researcher actually designing something, or merely evaluating existing technologies?

- **Candidate A**: **PRIMARILY EVALUATION, with POSSIBLE DESIGN CONTRIBUTION at the procedure level.** Applying confusion analysis to a classifier's predictions is standard evaluative practice, not novel design. The candidate *design* element — a documented, reproducible, cross-population-consistency-checked procedure with explicit exclusion criteria — is real but modest; it would need to be argued explicitly as a *procedural* contribution (a "how to do this reliably on small real-world datasets" prescription) to rise above pure evaluation. As currently exercised in R1/R8, this work is evaluative.
- **Candidate B**: **PRIMARILY EVALUATION, with POSSIBLE DESIGN CONTRIBUTION at the procedure level.** Same reasoning as A — subgroup-stratified accuracy comparison with an association test is standard fairness-audit-adjacent methodology (already demonstrated by Buolamwini & Gebru 2018 and others, per `STATE_OF_ART_AND_GAP.md`). The candidate design element (the specific `Unknown`-handling and small-subgroup-appropriate convention) is real but, again, needs to be explicitly argued as reusable procedural knowledge, not just asserted.
- **Candidate C**: **NOT YET A DESIGN CONTRIBUTION.** As currently exercised (R5–R9), this is evaluation of an existing technique (ArcFace-as-feature-extractor, already published elsewhere) against an existing baseline (HSEmotion) — a controlled experiment, not a design act. It could become a design contribution only if (a) Requirements/Theory are built first (per the Phase 1 audit, currently `MISSING`) to justify *why* a representation-based mechanism should be expected to behave differently, and (b) the resulting artifact is explicitly the *evaluation-design/context* (Gap G3), not the ArcFace application itself.

**Explicit statement, per instruction**: **the current work across all three candidates is, as it stands today, primarily evaluative, not yet a confirmed design contribution.** This is stated directly rather than inflated. A defensible design contribution is *reachable* from any of the three (most plausibly A/B, via an explicit procedural/method framing), but none of them currently constitute one merely by virtue of already having been run.

---

## 12. Contribution Test

| Candidate | Artifact Contribution (what was designed/built) | Empirical Contribution (what evidence does evaluation produce) | Knowledge Contribution (what is learned) | Practical Contribution (who could use it) |
|---|---|---|---|---|
| A | A documented, reproducible error-characterization procedure (modest; needs explicit procedural framing to count as "designed" rather than "applied") | A characterized, cross-population-reproduced error pattern (Neutral→Angry, 18/76=23.68%) | Possible, if the pattern's boundary conditions (which classes, which direction, under what conditions) are explained, not just described | Plausible: researchers/practitioners evaluating FER reliability on similar populations — not evidence-supported as an actual stakeholder |
| B | A documented skin-tone-stratified evaluation convention (modest, same caveat as A) | An in-sample skin-tone-stratified accuracy association (OR=5.88, p=0.0027) | Possible, if connected (with appropriate measurement-system caveats) to the general literature pattern (Gap G2) | Same plausible-only stakeholder as A |
| C | Minimal beyond A+B's, unless Requirements/Theory are built first (§11) | A comparative, skin-tone-stratified evaluation result (currently: no significant difference, McNemar p=0.4614) | Possible — a null result characterizing a boundary condition ("this representation-based approach does not resolve this dataset's skin-tone-stratified gap either") is valid knowledge (Rule 4), but not yet obtained as *new* knowledge beyond what R7 already reported | Same plausible-only stakeholder as A/B, narrower (specifically those considering a representation-based approach) |

No candidate is assumed to automatically produce all four contribution types — Candidate C in particular has the weakest confirmed Artifact Contribution of the three, despite having the most already-built code.

---

## 13. RQ Compatibility

| Artifact | RQ-1 | RQ-2 | RQ-3 | RQ-4 | Compatibility |
|---|---|---|---|---|---|
| Candidate A | Full | Not applicable (no skin-tone mechanism) | Partial (covers the error half only) | Partial (baseline-comparison mechanism reusable, but lacks representation-based integration) | Best fit: RQ-1 |
| Candidate B | Not applicable (no error-characterization mechanism) | Full | Partial (covers the skin-tone half only) | Partial (skin-tone mechanism reusable, but lacks representation-based integration) | Best fit: RQ-2 |
| Candidate A+B (§9 specification) | Full | Full | Full | Partial (missing E-03/R-02 comparative layer) | Best fit: RQ-3, and the closest of all candidates to the current Structure A+B working direction |
| Candidate C | Full (inherits A) | Full (inherits B) | Full (inherits A+B) | Full | Only candidate fully compatible with RQ-4, but see §10/§11 for why this is also the highest-risk option |

**No incompatibility was found that would invalidate any RQ candidate** — RQ-1/RQ-2/RQ-3 are each servable by a correspondingly-scoped artifact without requiring Candidate C's added risk. RQ-5 (`RQ_OPTIONS.md`'s deliberately-included cautionary candidate) is not mapped here, since it was already rated `BLOCKED`/not-recommended in Phase 4 independent of artifact considerations.

---

## 14. Constraints Preserved (Explicit Check)

- N=227 (historical) vs. N=135 (controlled common-subset) kept distinct throughout §1–§13 — no table or example merges them.
- 5-class final evaluation scope (Neutral, Happy, Sad, Surprise, Fear) stated as a constraint in Candidates A/B/C (§4) and in §9's specification.
- Angry=1, Disgust=2 ground-truth scarcity referenced explicitly (§4, Candidate A's constraints) as a structural, not artifact-fixable, limitation.
- Dark N=46, Medium-Dark N=32, Unknown N=57 stated explicitly wherever skin-tone subgroup size is discussed (§4 Candidate B, §10).
- Skin tone kept distinct from ethnicity throughout (§4, §6, §9, reporting-convention components in §2/§3).
- No causal interpretation of the Fisher's exact result anywhere in this document (§4 Candidate B explicitly frames it as "association").
- No claim that ArcFace statistically outperforms HSEmotion — §5's Candidate C design hypothesis explicitly states a null result is a valid outcome; §6 restates the existing McNemar p=0.4614 null finding without reinterpreting it.
- No claim that ArcFace solves bias — not stated anywhere; §6 explicitly limits ArcFace's role to implementation-choice/experimental-treatment, never a bias-solving claim.
- No claim that ArcFace itself is novel — §6 states plainly, per `STATE_OF_ART_AND_GAP.md` §7, that ArcFace-for-FER is not novel, and that applying it alone is not a defensible contribution.

---

## Open Design Questions

- What is the actual artifact, finally? (This document narrows it to "most plausibly the evaluation procedure/method," not any pretrained technology — but the final answer depends on which RQ, from `RQ_OPTIONS.md`, is eventually selected.)
- Who is the intended stakeholder/user? (Still only "plausible, not evidence-supported" across every candidate — unresolved since Phase 2.)
- Is the contribution primarily a method, a framework, or an empirical evaluation? (§11's finding: currently primarily evaluation, across all three candidates, with method-level contribution reachable but not yet secured.)
- How much of ArcFace is actually part of the artifact? (§6/§8: at most an integration point/experimental treatment, never a required or novel component, and only relevant if Candidate C is pursued.)
- Is skin-tone analysis a core artifact capability or merely an evaluation dimension? (Currently modeled as a core capability of Candidate B specifically, and as an integrated secondary layer of the strongest candidate (A+B, §9) — but its final status depends on the still-open Phase-5 decision about how heavily skin-tone will be weighted in the final thesis.)
- What methodology best fits the artifact? (Explicitly deferred to Phase 7 — not addressed here.)
- What evidence is required to validate the artifact? (Partially addressed at requirement level in §9's "Evaluation" row and `DESIGN_REQUIREMENTS.md` §6, but the full Evaluation Architecture is explicitly Phase 8's task.)
- Should Candidate C be pursued at all, given §11's finding that it is "not yet a design contribution" as currently exercised — or should the thesis scope explicitly exclude a representation-based comparison and remain within Candidates A/B only?
- If Candidate C is pursued, what specific Requirements/Theory (currently `MISSING`) would need to be built to justify it as more than "applying an already-published technique to a new dataset"?

---

## Completed

Analyzed six candidate artifact types against the Phase 5 requirements, distinguished existing technologies / existing research assets / researcher design / potential artifact, built a full requirement-to-artifact mapping (no unjustified design elements found; X-01 flagged as unimplementable by any artifact mechanism), developed three candidate artifacts (error-characterization method, skin-tone-stratified evaluation procedure, and a contingent face-representation-based extension), stated three explicit design hypotheses, evaluated ArcFace's and HSEmotion's roles explicitly, defined the artifact boundary, produced a preliminary specification for the strongest candidate, compared all three candidates across 9 criteria, ran the design-research test (finding all three candidates are currently primarily evaluative, not yet confirmed design contributions), ran the contribution test, checked RQ compatibility, and verified all constraint-preservation requirements. Produced `docs/proposal/design/ARTIFACT_ARCHITECTURE.md`.

## Files Created

- `docs/proposal/design/ARTIFACT_ARCHITECTURE.md`

## Files Modified

None. No source code, R1–R9 document, or prior proposal-phase document was changed.

## Key Findings

- **The requirements set points most strongly toward "Method" and "Evaluation framework/procedure" as artifact types — not "Model."** A standalone predictive-model artifact (e.g., "the ArcFace+LR classifier") is weakly supported by the actual requirements, which are dominated by analytical, data-handling, and reporting requirements rather than classification-performance requirements.
- **ArcFace is confirmed, again and more specifically, to never be a requirement** — at most an implementation choice / experimental treatment, relevant only to the contingent, highest-risk Candidate C. Applying ArcFace alone, without an explicit context/evaluation-design framing (Gap G3), has **no defensible contribution** given Phase 3's finding that ArcFace-for-FER is not novel.
- **The Design-Research Test found all three candidates are currently primarily evaluative, not yet confirmed design contributions** — stated directly rather than inflated. A defensible design/method contribution is reachable, most plausibly from Candidates A/B via explicit procedural framing, but is not automatic from having already run R1–R9.
- **The artifact boundary excludes the dataset, pipeline, and pretrained models** — the most defensible artifact is the evaluation procedure and its associated conventions (subgroup handling, statistical testing, reproducibility/reporting discipline), not the software pipeline that happens to already exist in `tools/`.
- **Candidate A (+B integrated, matching the current Structure A+B working direction) is both the strongest and safest candidate**; Candidate C is simultaneously the highest-potential and highest-risk candidate, and should only be pursued as a contingent extension of A/B, never as a standalone starting point.
- **X-01 (data provenance/consent) cannot be resolved by any artifact design** — carried forward as an unimplementable-by-design, still-open blocker.

## Blockers

- X-01 remains unresolved (unchanged from Phase 5) and is now further confirmed as outside any artifact's technical scope.
- The stakeholder question remains unresolved (unchanged since Phase 2) — every candidate's "User/Stakeholder" row is marked "plausible, not evidence-supported."
- Requirements/Theory (guideline sense) remain `MISSING` (Phase 1 audit), which specifically blocks Candidate C from ever exceeding "primarily evaluation" per §11's test.

## Decisions Needed

- Whether the final thesis scope excludes Candidate C entirely (staying within A/B, the safer path) or retains it as a contingent extension — and if retained, whether the effort to build genuine Requirements/Theory justification for it is worth the risk identified in §10/§11.
- Whether skin-tone (Candidate B) should be a core artifact capability or remain a secondary evaluation dimension only — still open from Phase 5, restated here as it directly affects the final artifact specification in §9.
- Whether "Method" or "Evaluation framework/procedure" is the more accurate artifact-type label going forward (§1) — a naming decision with guideline-compliance implications (BAB 11 explicitly cautions against calling something a "framework" without demonstrated reusability).

## Recommendation

Proceed to Phase 7 (Methodology) using the combined Candidate A+B specification (§9) as the working artifact concept — explicitly still a design hypothesis, not a final artifact — while keeping Candidate C's contingent status intact for later reconsideration only if Requirements/Theory work is separately undertaken.

STOP — waiting for approval for the next phase.
