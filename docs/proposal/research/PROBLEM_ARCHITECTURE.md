# Problem Architecture

> **Purpose**: Define and structure the research problem from currently verified evidence only, kept solution-neutral throughout. No final RQ, no final artifact, and no methodology are selected in this document. Every number below was re-checked against its source CSV during this phase (`reports/audit_summary_metrics.csv`, `reports/arcface_evaluation/comparison_metrics.csv`, `reports/arcface_evaluation/skin_tone_analysis.csv`, `reports/arcface_evaluation/statistical_tests.csv`, `reports/arcface_error_analysis/neutral_error_analysis.csv`).
>
> Per `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md`, this phase deliberately does **not** start from `docs/RESEARCH_FRAMING.md`'s original "FER for dark-skinned faces using ArcFace" framing — that framing names a candidate solution inside the problem statement, which the guideline's neutrality principle (BAB 4 §4.6) explicitly rejects. The problem below is built from evidence upward, not from the existing experiment downward.

---

## 1. The Problem Chain

### Context

Facial Expression Recognition (FER) systems are used to automatically classify a person's emotional expression from a face image. FER systems, like most vision models, are typically developed and validated using training and benchmark data whose demographic composition is not guaranteed to include dark-skinned populations at meaningful scale — this is a general, widely-observed characteristic of vision datasets, not a claim specific to any named FER product. *(Evidence-supported context; the general dataset-composition concern is not independently re-verified against external literature in this repository — see "Claims We Cannot Make Yet.")*

### Phenomenon

In this project's own dataset — face crops drawn from the film *Pesta Babi*, manually labeled by a human annotator (N=227) — an existing, general-purpose FER classifier (HSEmotion) was applied and audited. A specific, reproducible error pattern was observed: faces with a ground-truth label of **Neutral** were disproportionately misclassified as **Angry**.

### Current State (Evidence)

All values below are drawn directly from the historical N=227 population unless otherwise marked.

| Metric | Value | Population | Source |
|---|---|---|---|
| Overall HSEmotion accuracy | 22.47% | N=227 | `reports/audit_summary_metrics.csv` |
| HSEmotion false-Angry rate | 17.62% | N=227 | `reports/audit_summary_metrics.csv` |
| Neutral → Angry (HSEmotion) | 18 / 76 = 23.68% of Neutral ground truth | N=227 (76 Neutral samples within it) | `docs/RESEARCH_FINDINGS.md` §4, reconfirmed identically on the N=135 common subset (`reports/arcface_error_analysis/neutral_error_analysis.csv`) |
| HSEmotion accuracy, Dark skin tone | 44.0% | N=227 subset with skin-tone data | `reports/audit_summary_metrics.csv` |
| HSEmotion accuracy, Medium-Dark skin tone | 14.3% | N=227 subset with skin-tone data | `reports/audit_summary_metrics.csv` |

This is the **current state**: on this dataset, an existing general-purpose FER classifier shows a low overall accuracy and a specific, disproportionate Neutral→Angry error pattern.

### Evidence

The Neutral→Angry pattern is not a one-off artifact of a single analysis run — it was independently reconfirmed across separate experiment stages operating on different (but overlapping) populations:

- N=227 historical population: 18/76 = 23.68% (`reports/audit_summary_metrics.csv`, `docs/RESEARCH_FINDINGS.md` §4).
- N=135 common-evaluation-subset population: identical 18/76 = 23.68% for HSEmotion (`reports/arcface_error_analysis/neutral_error_analysis.csv`).
- Cross-experiment consistency was explicitly audited in R9 (`docs/R9_FINAL_STATISTICAL_VALIDATION.md`) with **zero inconsistencies found** across EXP-005 through EXP-008.

A secondary, statistically-tested pattern also exists in the evidence: on the N=135 common subset, HSEmotion's accuracy differs between two skin-tone buckets (Dark: 45.65%, n=46; Medium-Dark: 12.5%, n=32), an association confirmed by Fisher's exact test (OR=5.88, p=0.0027; `reports/arcface_evaluation/statistical_tests.csv`, `reports/arcface_evaluation/skin_tone_analysis.csv`). This is reported here strictly as an **observed association**, not a demonstrated cause.

### Consequence

If an FER system disproportionately misreads a person's neutral expression as an angry one, any downstream use of that output (e.g., automated affect logging, human-computer interaction feedback, behavioral analysis) would be built on a systematically distorted signal for at least some population(s) or expression categories. *(Evidence-supported for this dataset's classifier and population; the downstream-use consequence itself is a stated general implication of the observed error pattern, not something separately measured in this repository — no downstream application was built or tested here.)*

### Desired State

An FER classification result should reflect the person's actual expressed emotion at a rate that does not vary in a disproportionate, unexplained way across measurable image/population characteristics available in the data. *(Stated at the level the current evidence can support — see "Plausible stakeholder requiring validation" below for why a more specific desired-state statement, e.g. a numeric target accuracy or a named fairness criterion, is not yet claimed.)*

### Practical Problem

The gap between current state and desired state, stated without naming a solution:

> On this dataset, an existing FER classifier's Neutral-expression predictions are disproportionately wrong in one specific direction (toward "Angry"), and its overall accuracy differs across at least one measurable image-based population characteristic (skin-tone bucket) in a statistically observable way — a gap between the classifier's actual behavior and the behavior expected of a reliable FER system.

Note what this statement deliberately does **not** say: it does not name ArcFace, does not name Logistic Regression, and does not presume the solution is a different face-representation method. It remains true, and remains a problem worth investigating, regardless of which candidate solution is later evaluated or whether that candidate turns out to help.

### Existing Response

The only existing response within this repository's evidence base is the empirical ArcFace+Logistic-Regression comparison already carried out (R5–R9). Framed here strictly as a data point about what has already been *tried*, not as a validated *solution* to the practical problem above:

| Metric | ArcFace + Logistic Regression | HSEmotion | Population | Source |
|---|---|---|---|---|
| Accuracy | 40.74% | 36.30% | N=135 common subset | `reports/arcface_evaluation/comparison_metrics.csv` |
| Macro Precision | 28.03% | 58.98% | N=135 | same |
| Macro Recall | 29.31% | 20.58% | N=135 | same |
| Macro F1 | 27.17% | 24.89% | N=135 | same |
| Paired significance | McNemar p = 0.4614 (b=20, c=26) | — | N=135 | `reports/arcface_evaluation/statistical_tests.csv` |
| Neutral error rate | 56.6% (33/76 correct) | 44.7% (42/76 correct) | N=135, Neutral subset of 76 | `reports/arcface_error_analysis/neutral_error_analysis.csv` |
| Neutral wrong-prediction targets | Happy=15, Sad=14, Fear=8, Surprise=6 (distributed) | Angry=18 (concentrated) | same | same |

This existing response **does not resolve** the practical problem: the accuracy difference is not statistically significant, and while ArcFace's Neutral errors do not concentrate on "Angry" the way HSEmotion's do, this is partly a structural fact of the current 5-class evaluation scope (Angry is outside ArcFace's evaluated label space here — see Limitation below), not proof that a different mechanism was found and shown to work.

### Limitation

Separated per the phase instructions:

- **Observed limitation in current empirical evidence**: the ArcFace+LR vs. HSEmotion accuracy difference is not statistically significant (McNemar p=0.4614) — the existing response has not been shown to actually close the practical-problem gap.
- **Limitation of current dataset/experiment**: `Angry` (1 ground-truth sample) and `Disgust` (2 ground-truth samples) are too rare, at every population stage examined (227 → 144 valid → 138 embedded-valid), to support a defensible 7-class evaluation (`docs/R7_5_CLASS_DECISION.md`). This specifically limits how directly ArcFace's behavior can be compared to HSEmotion's Neutral→Angry pattern — ArcFace's Neutral→Angry rate is structurally `N/A`, not `0`, and not evidence of improvement.
- **Limitation of existing system (HSEmotion, as observed here)**: disproportionate Neutral→Angry misclassification and an accuracy difference across skin-tone buckets, both as described above — but only as observed on this dataset; not asserted as a general property of HSEmotion.
- **Limitation that requires literature evidence (not yet available)**: whether this Neutral→Angry pattern, or this skin-tone accuracy difference, is a known, general characteristic of FER systems (of this one, or FER systems generally) cannot be assessed without a literature review, which has not been performed (`docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md`, "Existing Knowledge"/"Existing Solution"/"State of Art" rows are `MISSING`). This repository's evidence characterizes a limitation **in this dataset and this classifier**, not in FER generally.

### Research Need

A research need broad enough to admit multiple possible solutions (not just ArcFace):

> There is a need to better characterize, and investigate ways to address, systematic FER expression-recognition errors — specifically the observed Neutral→Angry misclassification pattern and the observed accuracy variation across skin-tone buckets — in populations and conditions similar to this dataset, using methods whose face-representation and/or classification mechanism has not yet been shown, one way or the other, to avoid these specific error patterns.

This research need does not prescribe ArcFace, Logistic Regression, or any specific face-representation technique. It would remain valid even if a future literature review or experiment showed ArcFace-based approaches to be unhelpful.

---

## 2. Practical Problem / Knowledge Problem / Design Problem / Research Need

| Type | Statement | Basis |
|---|---|---|
| **Practical Problem** | An existing FER classifier's outputs, on this dataset, are systematically distorted in a specific direction (Neutral misread as Angry) and vary across a measurable population characteristic (skin-tone bucket) in a statistically observable way — this diverges from what a reliable FER system's stakeholders would expect. | Demands a change in the world (a more reliable classifier or a documented, understood limitation) — per Wieringa's practical-problem definition cited in the guideline. |
| **Knowledge Problem** | It is not yet known, from evidence collected so far, *why* this classifier concentrates Neutral errors on Angry specifically, nor whether an alternative face-representation-and-classifier combination can produce a systematically different (not necessarily better on every metric) error pattern under a rigorous, controlled comparison. | Demands new knowledge about the world — a "why"/"under what conditions" question, not yet answered even by the existing ArcFace+LR comparison, since that comparison shows a *different* error distribution but does not explain the *mechanism* behind either model's behavior. |
| **Design Problem** | It is not yet established what capability, mechanism, or design decision (in a face-representation model, a classifier, a training/evaluation procedure, or something else entirely) is currently missing that would close the gap between current and desired classifier behavior. | No design requirements or artifact specification exist yet (`docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md`, "Requirements" and "Artifact" rows) — this is explicitly deferred to later phases, not resolved here. |
| **Research Need** | See the Research Need statement above — broad enough to be answered by an evaluative study, an explanatory study, or a design-research study, depending on how later phases scope it. | Kept solution-neutral per the phase's explicit instruction. |

---

## 3. Stakeholder Component

Per the phase instruction, stakeholders are **not invented**. What follows distinguishes what the repository actually supports from what is merely plausible.

- **Evidence-supported stakeholder/context**: none. No document in this repository (R1–R9, `docs/RESEARCH_FRAMING.md`, `docs/THESIS_RQ_ALIGNMENT.md`, or elsewhere) records a stakeholder interview, a named affected user group, a deployment context, or an organizational owner of the "problem." The dataset's origin (a documentary film, *Pesta Babi*) is a data source, not a documented stakeholder relationship.
- **Plausible stakeholder requiring validation**: researchers/practitioners who would deploy or study FER systems on populations underrepresented in typical FER training/benchmark data; the individuals whose expressions are being classified (as data subjects, not as a validated "user" of the system, since no deployed system exists). These are plausible based on the general nature of the practical problem, but are not documented in this repository and would need direct validation (e.g., discussion with the thesis supervisor, or literature-based framing of who typically bears this cost in FER research) before being asserted as established stakeholders.
- **Missing stakeholder evidence**: no stakeholder analysis (Table 4.5-style: role, concern, goal, influence, potential requirement) exists anywhere in the repository. This is flagged as `MISSING` in `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md` and remains missing after this phase — it is out of this phase's scope to invent one.

The Desired State and Consequence sections above are, correspondingly, stated at the most general, evidence-defensible level ("an FER classifier's output should reflect actual expression without disproportionate, unexplained variation") rather than at a specific stakeholder-value level (e.g., a named accuracy target, a named application's safety requirement), because no stakeholder evidence exists yet to ground a more specific claim.

---

## 4. Existing Response — Scope Note

Per instruction, this section discusses existing FER approaches **only to the extent supported by the current repository** — i.e., only the HSEmotion baseline and the ArcFace+Logistic-Regression comparison already executed in R5–R9. No claim is made here about the broader FER research landscape, no comparison to published FER methods is attempted, and no state-of-the-art position is claimed. That comparison is explicitly deferred to Phase 3 (State of the Art and Gap), which requires the literature review currently `MISSING` per the Phase 1 audit.

---

## Claims We Can Make Now

1. On this dataset (N=227 historical), HSEmotion's overall accuracy is 22.47%, and its false-Angry rate is 17.62%.
2. On this dataset, HSEmotion disproportionately misclassifies Neutral-labeled faces as Angry: 18 of 76 Neutral ground-truth samples (23.68%), identically reproduced in both the N=227 historical population and the N=135 common-evaluation subset.
3. On the N=135 common-evaluation subset, ArcFace+Logistic Regression achieved a numerically higher accuracy (40.74%) than HSEmotion (36.30%), but this difference was not statistically significant (McNemar p=0.4614, b=20, c=26).
4. On the N=135 common-evaluation subset, ArcFace+LR's Neutral errors (56.6% error rate, 43/76) are distributed across Happy (15), Sad (14), Fear (8), and Surprise (6), rather than concentrated on a single class the way HSEmotion's are.
5. On the N=135 common-evaluation subset, an association was observed between skin-tone bucket and HSEmotion's accuracy (Dark 45.65% n=46, Medium-Dark 12.5%\* n=32 — \*note: `reports/audit_summary_metrics.csv`'s N=227-population value for Medium-Dark is 14.29%; the N=135-subset value from `reports/arcface_evaluation/skin_tone_analysis.csv` is 12.5% — both are correctly reported here, each labeled to its own population, and must not be interchanged), confirmed by Fisher's exact test (OR=5.88, p=0.0027).
6. `Angry` (1 sample) and `Disgust` (2 samples) ground-truth counts are too rare, at every population stage checked, to support a defensible 7-class evaluation with current data.
7. Skin tone in this repository is a measured image-based category (LAB-luminance-derived bucket), not an ethnicity label, and the dataset contains no ethnicity field.

## Claims We Cannot Make Yet

- That skin tone **causes** the observed accuracy difference (Fisher's exact test shows an in-sample association only, no causal design).
- That any performance difference is specific to **Papuan** individuals or any other ethnicity — no ethnicity field exists in the dataset, and skin tone is not a valid proxy for ethnicity.
- That ArcFace+Logistic Regression is **generally superior** to HSEmotion — the accuracy difference on N=135 was not statistically significant.
- That FER **universally fails** on dark-skinned populations — this repository's evidence describes one dataset and one classifier, not FER systems in general.
- That ArcFace+Logistic Regression is **statistically superior** to HSEmotion on any metric tested — no statistically significant superiority was found on accuracy (the only paired significance test performed), and macro precision was in fact substantially lower for ArcFace+LR.
- That a **research gap** is definitively established — no literature review has been performed; the practical problem and its evidence are established, but "gap" in the guideline's sense (insufficiency relative to existing knowledge) requires that review first.
- That this research direction has **definitive novelty** — novelty cannot be assessed without knowing the existing literature (per `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md`, "Novelty" is `MISSING / BLOCKED`, not merely unassessed).
- That the "100%-dark-skinned" dataset description (an older, now-corrected internal claim) is accurate — it is not; the skin-tone-characterized subset splits 58.8%/41.2% Dark/Medium-Dark, and a substantial portion of samples are skin-tone `Unknown` (`docs/THESIS_RQ_ALIGNMENT.md`).

---

## Framing Alternatives

Provided for later comparison in Phase 3/4. No framing is selected here.

| Framing | Strength | Evidence Support | Missing Evidence | Risk |
|---|---|---|---|---|
| **A. FER performance and error characterization** — study what error patterns a general-purpose FER classifier exhibits on this dataset, and characterize them (which classes, which direction, how consistent). | Directly matches the strongest existing evidence (Neutral→Angry pattern, cross-experiment-consistent); requires no new data or new claims about causality. | Very strong — this is essentially what R1–R9 already measured and cross-validated. | Literature grounding for whether this error pattern is already known/characterized elsewhere; a stakeholder/desired-state statement beyond "errors should not be systematically distorted." | Risk of being seen as purely descriptive/audit-like rather than research-question-worthy unless paired with a clear knowledge or design contribution target. |
| **B. Robustness across skin-tone categories** — investigate whether/how FER performance and error characteristics vary across measurable skin-tone buckets, and why. | Matches the second-strongest evidence line (Fisher's exact association); inherently comparative, which the guideline favors for evaluative claims. | Moderate — an association is established (OR=5.88, p=0.0027), but on an uneven, partly `Unknown`-heavy population (Dark n=46, Medium-Dark n=32, Unknown n=57) and without a causal mechanism. | Literature on skin-tone/illumination effects in FER or face-representation models generally; a stated mechanism/theory for *why* skin tone might affect this specific classifier; explicit handling of the `Unknown` bucket and the small/uneven subgroup sizes. | Highest risk of misreading by an audience as an ethnicity/fairness/bias claim if not framed and caveated as carefully as this document and `docs/RESEARCH_FINDINGS.md` already do — requires disciplined language throughout any later proposal draft. |
| **C. Design of a face-representation-based FER approach** — design and evaluate a face-representation-based method (of which the existing ArcFace+LR work is one candidate instance) intended to address the observed error pattern(s). | Has a concrete existing instantiation to build from (R5–R9), and the guideline's design-research orientation fits this framing most directly of the three. | Moderate — the existing instantiation exists and was evaluated, but did not achieve statistical superiority over the baseline, and its design was not derived from stated requirements/justificatory knowledge (per the Phase 1 audit's "Theory," "Requirements," and "Artifact" rows). | A design-requirements analysis grounded in Framing A/B's evidence; justificatory knowledge for *why* a face-representation approach should help; literature on prior face-representation-based FER work, to establish design-gap validity per the guideline's §7.3. | Highest risk of reintroducing the solution-first problem this document was built to avoid (`docs/RESEARCH_FRAMING.md`'s original ArcFace-first framing) unless Requirements are genuinely derived from Framing A/B first, not backfilled to justify the already-built pipeline. |

These are not mutually exclusive — Framing C could be built as a design response to a gap established via A and/or B. That composition decision is explicitly deferred to Phase 4 (RQ Options).

## Open Questions Before RQ Formulation

- Whether a literature-supported research gap can actually be established (Framing A, B, and C all currently lack this — `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md`, "Gap" = `MISSING`).
- Who the target stakeholder is, and whether that can be validated (e.g., through supervisor discussion) rather than left implicit.
- What desired-state statement is defensible beyond the general one used in this document — e.g., is there a specific accuracy/fairness/error-rate criterion that matters to the target stakeholder, or is characterization itself the goal?
- Whether skin-tone analysis should be a **primary** research dimension (Framing B) or a **secondary** analytical lens on a primarily performance/error-focused study (Framing A or C with skin-tone as one evaluation axis) — this materially changes what evidence, literature, and evaluation design would be required.
- Whether the research is primarily **explanatory** (why does this error pattern occur), **evaluative** (how well does a candidate method perform against the baseline, which is what R5–R9 already partially did), or **design-oriented** (what should be designed to address the problem) — per the guideline's RQ typology (Table 8.1), these lead to different objective/requirement/evaluation chains and are not automatically compatible with each other in a single RQ.
- What role, if any, ArcFace/Logistic Regression should play going forward: as the object of a purely evaluative RQ (Framing C-lite, reusing existing results), as one of several candidate designs considered only after Requirements are derived (full Framing C), or set aside entirely if Framing A or B is chosen as the primary direction.
- Whether the current 5-class evaluation scope (Angry/Disgust excluded for insufficient ground truth) is an acceptable permanent scope boundary for the eventual RQ, or whether it should be listed as a limitation requiring future work/data collection.
- Whether the "100%-dark-skinned" claim's correction (58.8%/41.2% Dark/Medium-Dark split, large `Unknown` portion) needs to be explicitly reconciled with any supervisor-facing narrative material before proposal writing begins (carried forward from the Phase 1 audit's Ethics/Contradictions sections).
