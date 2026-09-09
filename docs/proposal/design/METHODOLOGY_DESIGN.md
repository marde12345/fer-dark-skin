# Methodology Design

> **Purpose**: Determine and justify a research methodology recommendation for the current working artifact concept — *a method/evaluation procedure or framework for reproducible FER performance and systematic error characterization, with measured skin-tone-stratified analysis as a secondary analytical dimension* (`docs/proposal/design/ARTIFACT_ARCHITECTURE.md` §9) — which remains a **design hypothesis**, not a finalized artifact. No RQ is finalized. No new experiment is run. R1–R9's history is not rewritten to retroactively fit any methodology.

---

## 0. A Note on Source Fidelity

Per instruction, this document uses `docs/proposal/guideline/PROPOSAL_GUIDELINE_EXTRACTION.md` as the primary source wherever it speaks directly to a methodology. A direct check of that extraction (re-verified against the guideline PDF citations recorded there) found:

- The guideline **cites Peffers et al. (2007)** — the canonical DSRM (Design Science Research Methodology) reference — once, in the context of research objectives (§9, p.137) and demonstration (§15, p.189–190), but **does not present a dedicated, named "DSRM" step-by-step methodology chapter**.
- The guideline **cites Blessing & Chakrabarti (2009)**'s DRM (Design Research Methodology) *Impact Model* once, specifically for the ex ante/ex post evaluation distinction (§16, p.199–201), **not as a full methodology comparison**.
- The guideline **explicitly warns against naming "DSRM" alone as if it explained how an artifact was built** (`PROPOSAL_GUIDELINE_EXTRACTION.md` §21, p.213: *"naming 'DSRM' alone does not explain how the artifact was actually built"*) — this warning is taken seriously below; DSRM is not adopted here merely because it is the most commonly cited name in design-research literature.
- The guideline **does not mention ERM (Engineering Research Methodology / Empirical Research Methods) or ADR (Action Design Research) by name anywhere** in the extraction. Where those two are discussed below, this is stated explicitly as **general design-research-methodology knowledge supplementing the guideline**, not guideline content — consistent with the instruction not to fabricate guideline coverage that does not exist.
- The guideline's own repeatedly-stated master cycle — **understanding → designing → evaluating → learning** (§1, p.41) and **Build → Demonstrate → Evaluate → Learn → Refine** (implied throughout BAB 12, explicit at p.184–186, p.225) — is used below as the primary structural touchstone, since it is what the guideline itself actually prescribes, independent of which named methodology label is ultimately used.

---

## 1. Methodology Options

Four candidate methodologies are evaluated, with their sourcing made explicit:

- **DSRM (Design Science Research Methodology, Peffers et al. 2007)** — cited by the guideline (see §0); a six-activity process: problem identification → objectives → design & development → demonstration → evaluation → communication.
- **DRM (Design Research Methodology, Blessing & Chakrabarti 2009)** — cited by the guideline (see §0), specifically for its Impact Model / ex ante–ex post evaluation framing; DRM's full four-stage structure (Research Clarification → Descriptive Study I → Prescriptive Study → Descriptive Study II) is **general design-research-methodology knowledge**, not itself detailed in the guideline extraction — flagged here as supplementary, not guideline-sourced.
- **ERM (Empirical/Evaluation Research Methods, e.g., controlled comparison and statistical hypothesis testing as a methodology in its own right)** — **not named in the guideline extraction at all**; included here as a candidate because it most closely matches what R1–R9 have actually been doing (controlled baseline comparison, statistical testing), and must be evaluated honestly against the guideline's design-research orientation, not assumed compatible.
- **ADR (Action Design Research, Sein et al. 2011)** — **not named in the guideline extraction at all**; included as a candidate because it is a well-known alternative for artifacts co-shaped by ongoing organizational/stakeholder interaction — included here specifically to test whether it fits, given this thesis's current, unresolved stakeholder gap (Phase 2/5/6).

---

## 2. Methodology Fit

| Criterion | DSRM | DRM | ERM | ADR |
|---|---|---|---|---|
| Problem fit | STRONG — DSRM's problem-identification→objectives chain matches the already-established Problem→Evidence→Research Need chain in `PROBLEM_ARCHITECTURE.md` directly | STRONG — DRM's Research Clarification stage matches equally well, with an added emphasis on criteria/success-measure clarification that fits the requirements-heavy artifact hypothesis | MODERATE — fits the *evaluative* half of the problem (characterizing classifier error/skin-tone patterns) but has no native concept of "artifact design," which weakens fit to the design-oriented parts of the problem | WEAK — ADR presumes an organizational context with an engaged problem-owner shaping the artifact through use; no such context or stakeholder is evidenced here (Phase 2/5/6) |
| Research question fit | STRONG — compatible with RQ-1/RQ-2/RQ-3 (evaluative/design-oriented mix) and RQ-4 (design-oriented) per `RQ_OPTIONS.md` Table 8.1 typology | STRONG — same compatibility, DRM's descriptive/prescriptive split maps cleanly onto RQ-1/RQ-2 (Descriptive Study I-like) vs. RQ-4 (Prescriptive-Study-like) | MODERATE — fits RQ-1/RQ-2/RQ-3 (evaluative/comparative questions) well; poor fit for RQ-4 if RQ-4 is meant to produce a design contribution, since ERM has no native design-iteration concept | WEAK — poor fit for all current RQ candidates, none of which presume ongoing organizational intervention |
| Artifact fit | STRONG — DSRM explicitly expects a designed artifact (method/model/construct/instantiation), matching `ARTIFACT_ARCHITECTURE.md`'s Method/Evaluation-procedure candidates | STRONG — same, with DRM's stronger emphasis on *support* (the artifact "supports" a desired change), which fits an evaluation-procedure artifact well | WEAK — ERM does not center an artifact at all; it centers a hypothesis test. `ARTIFACT_ARCHITECTURE.md` §11 already found the current work is "primarily evaluative" — adopting ERM would make this an honest but *artifact-less* framing, in tension with a design-research proposal's Chapter-4 expectations | MODERATE — ADR's artifact is explicitly "ensemble" (technology + organizational context), which does not match the current stakeholder-less state of this work |
| Design iteration | MODERATE — DSRM formally supports iteration (its process is drawn as a nominal sequence but Peffers et al. explicitly allow entry at different points and iterative return) | STRONG — DRM's four-stage structure is explicitly meant to be revisited/iterated, and its evaluation stages are structured around exactly this | WEAK — ERM's typical structure (hypothesize → test → report) does not natively support build-evaluate-learn iteration on an artifact | MODERATE — ADR is inherently iterative (its Building-Intervention-Evaluation cycles are continuous), but iteration in ADR is driven by organizational interaction, which is not available here |
| Technical rigor | STRONG — DSRM is agnostic to and fully compatible with statistical/technical rigor in its Evaluation activity | STRONG — same, DRM's Descriptive Study II stage is explicitly about rigorous impact evaluation | STRONG — this is ERM's core strength; R1–R9's statistical rigor (McNemar, bootstrap, Fisher's exact) is a direct match | MODERATE — ADR permits rigor but is not itself the source of it; rigor is not ADR's emphasis |
| Evaluation | STRONG — DSRM's Evaluation activity, plus the guideline's own verification/validation and formative/summative distinctions (BAB 13), map directly | STRONG — DRM's ex ante/ex post Impact Model (explicitly cited by the guideline, §16 p.199–201) is a strong structural match for evaluating a null-result-tolerant design hypothesis | STRONG — evaluation *is* ERM's entire content | MODERATE — ADR evaluates continuously through organizational use, which this project cannot do (no organizational deployment) |
| Learning/refinement | STRONG — DSRM's Communication activity plus the guideline's own explicit Learn step (BAB 12 §12.2, p.184–186) fit directly | STRONG — DRM structurally requires a Descriptive Study II "did it work, why/why not" reflection, matching Learning very closely | WEAK — ERM as a methodology does not have a native "Learn/Refine the artifact" step; learning in ERM is about the hypothesis, not about an artifact design | MODERATE — ADR's learning is continuous but tightly coupled to organizational engagement not present here |
| Stakeholder/context fit | WEAK for all non-DSRM options in one specific sense — **stakeholder evidence is currently missing for every methodology candidate** (Phase 2/5/6), so no methodology can claim strong stakeholder fit; ADR is rated separately below because it specifically *requires* stakeholder engagement to function at all, which is a categorical (not just evidentiary) mismatch | WEAK, same missing-stakeholder-evidence caveat as DSRM | WEAK, same caveat, though ERM does not itself require stakeholder engagement to be valid — it can proceed with a general research audience instead, which is a smaller mismatch than ADR's | **NOT FIT** — ADR's core mechanism (Building-Intervention-Evaluation *with* an organizational problem-owner) cannot be enacted at all without a stakeholder, which is precisely what is missing |
| Feasibility | STRONG — no new infrastructure needed; R1–R9's existing work already resembles several DSRM activities informally (see §4) | STRONG — same feasibility profile as DSRM | STRONG — most feasible in the narrow sense of "requires the least additional methodological apparatus," since it matches what has already been done | WEAK — would require establishing an organizational engagement this project does not have access to, within a Master's-thesis timeline |
| Thesis fit | STRONG — DSRM is the most commonly recognized design-research methodology for a Master's-level design-research thesis, and is explicitly the methodology the guideline's own citations lean toward (Peffers et al. cited twice, for objectives and demonstration) | STRONG — DRM is an equally legitimate, guideline-cited (for evaluation) alternative, sometimes preferred when the thesis's emphasis is more on a rigorous *evaluation/impact* framing than on a novel *build* | MODERATE — a legitimate methodology in its own right, but choosing it would mean **not** framing this as a design-research thesis in the artifact-centric sense the guideline (BAB 1–3) sets up — a real, honest option (see §13) but a scope-narrowing one | WEAK — poor fit given the missing stakeholder/organizational context; would require inventing an engagement this thesis does not have |
| **Main risk** | Risk of overclaiming "iteration" if in practice only one build-evaluate pass is completed (see §6) | Risk of DRM's heavier four-stage apparatus being more process than this modestly-scoped thesis needs | Risk of implicitly abandoning any design/artifact contribution claim, leaving only an empirical-evaluation contribution (a legitimate but different thesis framing — see §13's Second-Best Alternative) | Risk of being categorically inapplicable, given the confirmed absence of any stakeholder/organizational context |

---

## 3. Research Orientation → Methodology → Activities → Methods → Evidence

Kept explicitly distinct, per instruction:

```
Research Orientation:  Design research (understanding + designing + evaluating + learning),
                       per guideline §1 (p.10-14, 39-41) — NOT a purely explanatory/behavioral
                       orientation, though the current work leans evaluative in practice
                       (ARTIFACT_ARCHITECTURE.md §11).
        ↓
Methodology:           DSRM or DRM (candidates compared in §2) — a named, structured
                       process for moving from problem to evaluated artifact to knowledge.
                       NOT itself an experiment, a statistical test, or an algorithm.
        ↓
Research Activities:   e.g., "characterize classifier error patterns," "stratify performance
                       by skin-tone," "compare a face-representation-based approach to
                       baseline" — concrete activities the chosen methodology structures
                       (detailed in §4-5). NOT the methodology itself.
        ↓
Research Methods:      e.g., confusion-matrix analysis, McNemar's test, Fisher's exact test,
                       StratifiedGroupKFold cross-validation, LAB-luminance skin-tone bucketing
                       — specific techniques used WITHIN an activity. NOT the methodology,
                       and NOT machine-learning algorithms treated as if they were research
                       design (Logistic Regression is a method-level implementation choice,
                       per ARTIFACT_ARCHITECTURE.md §9, not a methodology).
        ↓
Evidence:              CSVs, statistical test outputs, confusion matrices, reproducibility
                       checks — the actual output data (already produced for R1-R9;
                       to be produced going forward per §5).
```

This chain is stated explicitly to guard against three conflations named in the phase instructions: DSRM is not an experiment; a methodology is not a statistical test; a methodology is not a machine-learning algorithm; and (added here) the artifact is not its implementation tools (`tools/*.py` are implementation, not the artifact itself, per `ARTIFACT_ARCHITECTURE.md` §2/§8).

---

## 4. Current Research Activities (R1–R9) — Classified, Not Rewritten

| Activity | R-Phase | Classification |
|---|---|---|
| Dataset generation (video → frames → face crops) | Pre-R1 (repository foundation) | **PRE-RESEARCH-DESIGN / EXISTING EMPIRICAL WORK** — infrastructure, not a design-research activity in itself |
| Manual annotation (ground-truth labeling) | Pre-R1 | **PRE-RESEARCH-DESIGN / EXISTING EMPIRICAL WORK** |
| Baseline (HSEmotion) evaluation/audit | R1 | **EVALUATION ACTIVITY** — measuring an existing, pre-built classifier's behavior; not a design activity |
| CLAHE preprocessing experiment | Pre-R1/early | **EVALUATION ACTIVITY** — testing a preprocessing intervention's effect, not artifact design in the guideline's sense |
| Research evidence audit, RQ alignment, framing reconstruction | R1–R2.5 | **SUPPORTING ACTIVITY** — clarifying what evidence exists; closer to the guideline's "problem identification" activity than to design or evaluation |
| Methodology/model reconciliation (confirming HSEmotion is the sole classifier, ArcFace unused) | R3 | **SUPPORTING ACTIVITY** |
| ArcFace experiment design (on paper) | R4 | **SUPPORTING ACTIVITY**, bordering on **DESIGN ACTIVITY** — this is the closest R1–R9 comes to a genuine design step (deciding to treat ArcFace as frozen, deciding on Logistic Regression as classifier) — but it was not derived from a formal Requirements phase (confirmed `MISSING` in the Phase 1 audit), so it is classified as informal, pre-methodology design reasoning, not a methodologically-structured Design activity |
| ArcFace embedding extraction | R5 | **EVALUATION ACTIVITY** (implementation of an already-decided design choice, then measured for feasibility — 178/227 successfully embedded) |
| Classifier training + cross-validation | R6 | **EVALUATION ACTIVITY** |
| Formal ArcFace vs. HSEmotion comparison (McNemar, bootstrap, Fisher's exact) | R7 | **EVALUATION ACTIVITY** |
| Class/error-analysis decision (5-class scope) | R7.5 | **SUPPORTING ACTIVITY** |
| Error + skin-tone analysis | R8 | **EVALUATION ACTIVITY** |
| Cross-experiment consistency validation, findings synthesis | R9 | **SUPPORTING ACTIVITY** (an audit/consolidation step, not new evaluation or design) |
| Proposal-design workflow (Phase 0–6, this document's own predecessors) | Current | **DESIGN ACTIVITY** (problem architecture, requirements, artifact architecture) — the first activities in this entire project that are methodologically structured as *design research* in the guideline's sense |

**Explicit statement, per instruction**: **R1–R9 were not executed according to any named design-research methodology.** They constitute genuine, rigorous **empirical/evaluative work** (baseline characterization, comparative evaluation, statistical validation) conducted prior to, and independently of, the design-research framing now being retrofitted around them (Phase 0 onward). This document does not claim otherwise. The one activity closest to "design" (R4, ArcFace Experiment Design) was informal — it selected a design decision (frozen embeddings, Logistic Regression) without a preceding formal Requirements phase, which is precisely why `ARTIFACT_ARCHITECTURE.md` §11 rated it, and everything built on it, as "primarily evaluation, not yet a confirmed design contribution."

---

## 5. Future Research Activities

### Already Completed (not to be repeated or re-framed as "future")

- Dataset generation, annotation, baseline evaluation, ArcFace embedding extraction, classifier training, formal comparison, error/skin-tone analysis, cross-experiment validation (R1–R9, per §4).
- Problem architecture, guideline audit, literature review/gap analysis, RQ options, design requirements, artifact architecture (Phase 0–6, this workflow's own predecessors).

### Proposed Future Work

| Activity | Purpose | Input | Process | Output | Evidence |
|---|---|---|---|---|---|
| **RQ finalization** | Lock the official research question (currently `MISSING`) | `RQ_OPTIONS.md`'s 5 candidates + supervisor decision | Supervisor/user review and selection (not this document's task) | An official RQ statement | A decision record |
| **Requirements refinement (if needed)** | Adjust `DESIGN_REQUIREMENTS.md` to match the finalized RQ, if the RQ differs from the current A+B working direction | Finalized RQ | Re-derive/confirm requirements against the new RQ | Updated or reconfirmed requirements | Traceability check (as in Phase 5 §13) |
| **Artifact finalization** | Select and formally specify one artifact candidate from `ARTIFACT_ARCHITECTURE.md` §4/§9 | Finalized requirements | Formal specification per Table 11.2 of the guideline (name, type, purpose, mechanism, components, evaluation criteria, open decisions) | A finalized artifact specification document | Specification completeness check |
| **Development (Build)** | Implement or formally re-package the artifact's mechanism (evaluation procedure/method) | Finalized artifact specification | Implement/adapt the procedure — likely substantially reusing existing `tools/*.py` code, but now as a *justified* implementation of a *specified* design, not an unstructured prior build | A working, documented implementation of the specified procedure | Code + documentation, unit-testable (as R5/R6's existing test suites already demonstrate is feasible in this codebase) |
| **Demonstration** | Show the artifact's mechanism runs and produces its intended output form (distinct from evaluating how well it performs, per guideline §15 p.189–190) | Implemented artifact | Run the procedure on at least one population (likely reusing the existing N=135/N=227 data) and confirm it produces the specified output types (error report, skin-tone-stratified report, etc.) | A demonstration record (inputs/outputs/configuration documented for repeatability, per guideline §15) | Demonstration log |
| **Evaluation** | Determine whether the artifact's mechanism actually characterizes error/skin-tone patterns as intended, and whether it reproduces the already-known findings (Neutral→Angry, skin-tone association) as a sanity/validity check | Demonstration output + existing R1–R9 findings as a reference point | Compare the artifact's output against the already-known findings; assess whether the procedure is reproducible, auditable, and correctly handles known edge cases (Unknown skin-tone, rare classes) | An evaluation report | Comparison against R1–R9 findings; validity-threat discussion (Phase 8's task to formalize fully) |
| **Learning** | Extract what was learned — about the artifact's mechanism, about the problem, or about the boundary conditions of either | Evaluation report | Reflect on where the artifact's output matched/diverged from expectations, and why | A learning/reflection record (per guideline BAB 12 §12.7's required documentation artifacts) | Documented rationale for any refinement decision |
| **Refinement (conditional)** | Adjust the artifact if evaluation reveals a correctable issue (e.g., an edge case not handled, an unclear reporting convention) | Learning record | Targeted revision of the specific component found lacking | Revised artifact/documentation | Updated version log |

Not every category from the phase instructions (Problem identification, Requirement definition, Design, Development, Demonstration, Evaluation, Learning, Refinement) is listed as a *separate future activity* — **Problem identification, Requirement definition, and Design** are substantially already completed by Phase 2/5/6 of this workflow and are listed above only where genuine *refinement* (not re-starting) may still be needed.

---

## 6. Design Iteration

**Determination: a single, deliberate build-evaluate-learn pass is currently justified as the starting plan; a second iteration should be conditionally triggered, not assumed in advance.**

- **What would be refined**: most plausibly the artifact's *reporting conventions* (e.g., exactly how `Unknown` skin-tone is displayed, exactly what "reproduction across populations" requires to count as confirmed) rather than its *core mechanism* (confusion analysis, subgroup stratification, statistical testing) — the core mechanism is already well-exercised (R1–R9) and unlikely to need structural rework.
- **What would trigger refinement**: (a) the artifact's output failing to reproduce an already-known, well-evidenced finding (e.g., if the procedure, when formally run, did *not* reproduce the Neutral→Angry pattern already found informally in R1/R8 — this would indicate a bug or conceptual error in the procedure, not a new scientific finding); (b) a reviewer/supervisor identifying a reporting-convention ambiguity; (c) discovery that a requirement (`DESIGN_REQUIREMENTS.md`) was not actually satisfiable as specified.
- **Evidence required to justify refinement**: a documented discrepancy between the artifact's output and the reference R1–R9 findings, or an explicitly identified gap between a requirement and the artifact's actual behavior — not a preference-based change.
- **Why iteration should not be assumed extensive**: this is a Master's-thesis-scoped project building on an already-substantial base of prior empirical work (R1–R9); the guideline's own caution against an "overly tight Gantt chart with no refinement time" (§19, p.217) argues for *some* buffer, but nothing in the current evidence suggests the artifact's core mechanism requires multiple substantial redesigns — R1–R9's underlying procedures have already proven stable and reproducible (R9's cross-experiment consistency audit found zero inconsistencies).

**Explicit statement, per instruction**: R1–R9 were **not** iterative design cycles in the guideline's sense — they were a sequence of independent empirical studies (§4). The Build-Demonstrate-Evaluate-Learn cycle described in this section is proposed as the **forward-looking** structure for the *next* phase of work (formally specifying and validating the artifact), not a retroactive description of what already happened.

---

## 7. Methodology → Activity Traceability

| Methodology Element | Research Activity | Artifact | Evidence | Contribution |
|---|---|---|---|---|
| Problem Identification (DSRM Activity 1 / DRM Research Clarification) | Already completed — `PROBLEM_ARCHITECTURE.md` (Phase 2) | N/A (pre-artifact) | Problem chain, evidence table | Supports Knowledge/Practical contribution framing later |
| Define Objectives (DSRM Activity 2) | Pending — depends on finalized RQ | N/A | `RQ_OPTIONS.md` §7 (candidate objectives, non-final) | N/A until RQ finalized |
| Design & Development (DSRM Activity 3 / DRM Prescriptive Study) | Proposed future work — artifact finalization + Build (§5) | Method/Evaluation-procedure candidate (`ARTIFACT_ARCHITECTURE.md` §9) | To be produced | Artifact Contribution (if procedural framing is made explicit, per `ARTIFACT_ARCHITECTURE.md` §11) |
| Demonstration (DSRM Activity 4) | Proposed future work (§5) | Same artifact | Demonstration log (to be produced) | Supports Artifact Contribution claim |
| Evaluation (DSRM Activity 5 / DRM Descriptive Study II) | Partially already completed as informal evaluative work (R1–R9); formal artifact-level evaluation is proposed future work (§5) | Same artifact | R1–R9 CSVs (existing) + new evaluation report (future) | Empirical Contribution (already substantially available); Artifact-validity contribution (future) |
| Communication (DSRM Activity 6) | Proposed future work — thesis writing, `docs/proposal-latex/` (Phase 14, later) | N/A | Thesis document | Knowledge/Practical Contribution, formally stated |
| Learning (guideline's explicit stage, BAB 12 §12.2/§12.7) | Proposed future work (§5) | N/A directly — informs artifact refinement | Learning/reflection record (future) | Knowledge Contribution |

**No methodology element above is marked `NOT YET JUSTIFIED`** — every element connects to either an already-completed activity or a specified, scoped future activity. (This connects the methodology to real, existing work — it does not assert that all resulting contribution claims are already earned; several are explicitly marked "future" or "if procedural framing is made explicit.")

---

## 8. Data and Methods (Kept Separate From Methodology)

**Research Data** (the actual data assets):
- Source video (*Pesta Babi*); face crops (N=227); manual ground-truth labels; HSEmotion predictions; ArcFace embeddings (178/227); skin-tone measurements (LAB-luminance buckets); the N=135 common-evaluation subset.

**Research Methods** (specific techniques used within an activity — not the methodology):
- Face detection (InsightFace/SCRFD); feature extraction (ArcFace embedding); classification (HSEmotion inference; Logistic Regression on embeddings); confusion-matrix analysis; subgroup (skin-tone-stratified) analysis; statistical testing (McNemar's exact test, group-aware bootstrap resampling, Fisher's exact test); cross-validation (`StratifiedGroupKFold` with temporal-block grouping).

**Research Methodology** (the structuring process — the subject of this document):
- DSRM / DRM / ERM / ADR (candidates compared in §2).

These three levels are kept explicit and separate throughout this document, per instruction — e.g., "Logistic Regression" never appears above as a methodology, and "DSRM" never appears as a statistical test.

---

## 9. Evaluation Position (Requirement-Level Only — Full Design Deferred to Phase 8)

- **Where evaluation sits**: within whichever methodology is selected (DSRM or DRM, per §13), evaluation is the activity that follows Demonstration and precedes Learning/Communication — it answers "how well does the artifact's mechanism characterize error/skin-tone patterns," not merely "does it run" (that is Demonstration, per guideline §15's explicit distinction, p.189–190).
- **Role it plays**: primarily **validation** (does the artifact address the intended problem — can it reproduce and correctly characterize the already-known patterns) rather than pure **verification** (does it run to spec) — though both are relevant (guideline BAB 13 §13.1, p.196–197).
- **Formative vs. summative**: the proposed single build-evaluate-learn pass (§6) is best understood as **formative** in intent (its primary purpose is to check whether the artifact's mechanism works as specified and to catch correctable issues) but would also serve a **summative** function if its result is reported as the thesis's evidence for the artifact's validity — per the guideline (§16, p.198–199), this dual role is about *purpose of use*, not timing, and is consistent with a single-pass design.
- **Verification/validation relevance**: both apply — verification checks the artifact's mechanism runs correctly (e.g., correctly excludes `Unknown` skin-tone, correctly applies the documented exclusion criteria); validation checks whether the resulting characterization is a faithful, reproducible account of the actual data (e.g., does it reproduce the Neutral→Angry finding).
- **What refinement decisions may depend on evaluation**: per §6, refinement is triggered specifically by a documented mismatch between the artifact's output and the reference R1–R9 findings, or an identified requirement-satisfaction gap — not by open-ended dissatisfaction.

**This is not the full Evaluation Architecture** (Objective → Requirement → Claim → Criterion → Indicator → Metric → Baseline → Evaluation Method → Data) — that is explicitly Phase 8's task and is not attempted here.

---

## 10. Learning

What could genuinely be learned, beyond simply reporting model accuracy:

- **From successful design** (if the artifact's mechanism correctly reproduces known findings and generalizes its reporting conventions cleanly): evidence that a *documented, reproducible procedure* — not just one-off scripts — can reliably characterize FER error/skin-tone patterns on small, real-world datasets; this is knowledge about the *procedure's* validity, distinct from any finding about FER itself.
- **From unsuccessful design** (if the artifact's mechanism fails to reproduce a known finding, or produces an ambiguous/inconsistent report): a boundary condition on the procedure itself — e.g., "confusion analysis alone does not surface X without also controlling for Y" — this is exactly the kind of negative-result knowledge the guideline (§20, p.218) and Rule 4 explicitly protect as valid.
- **From baseline comparison** (already substantially available, R7): that a face-representation-based approach's accuracy is not statistically distinguishable from HSEmotion's on this population (McNemar p=0.4614) — knowledge about the *comparative behavior* of two approaches on this specific, small, real-world dataset, not a general claim about either approach's superiority.
- **From error patterns** (already substantially available, R1/R8): that HSEmotion's errors concentrate on a specific class-pair (Neutral→Angry) while a representation-based approach's errors, when they occur, distribute across multiple classes — knowledge about *differential failure modes*, which is more informative for future FER work on similar data than a single aggregate accuracy number would be.
- **From skin-tone analysis** (already substantially available, R7/R8): that an in-sample association between skin-tone bucket and accuracy exists and is statistically detectable even at small subgroup sizes (N=46/N=32) — knowledge about *what is measurable* on a real-world dataset of this scale, which is itself informative for future researchers considering similar analyses on similarly-sized data.
- **From failed hypotheses** (e.g., if a future comparative extension, Candidate C, again fails to show significance): this would still be valid knowledge — specifically, evidence about a *boundary condition* (representation-based approaches of this kind do not resolve this dataset's skin-tone-stratified accuracy gap either) — not a failure of the research.

**Explicit statement, per instruction**: none of the above equates "learning" with simply restating model accuracy. Each learning category above specifies a *distinct kind of knowledge* (procedural validity, boundary conditions, differential failure modes, measurability limits) that goes beyond a single performance number.

---

## 11. Stakeholder Problem — How the Methodology Should Handle It

Per Phase 2/5/6, stakeholder evidence remains genuinely missing — not invented here either. Status: **REQUIRES SUPERVISOR/RESEARCHER VALIDATION.**

- **Is stakeholder identification necessary before proceeding?** Not strictly necessary to proceed with the *evaluative/characterization* activities already scoped (§5) — these can proceed with a general research-audience framing (researchers/practitioners studying FER reliability on non-benchmark populations), consistent with `ARTIFACT_ARCHITECTURE.md`'s repeated "plausible, not evidence-supported" stakeholder framing.
- **Can it remain contextual/general?** Yes, for DSRM or DRM as recommended (§13) — both methodologies can proceed with a general research-knowledge objective (Practical Contribution framed generally, e.g., "researchers evaluating FER on similar populations," rather than a named organizational stakeholder) — this is a legitimate, if modest, scoping choice, not a methodological failure.
- **Or does it become a limitation?** Yes, explicitly — this must be stated as a limitation in the eventual thesis (carried forward from Phase 1/2/5/6): the Practical Contribution claim (guideline §18, p.139–140) will be correspondingly modest/general rather than tied to a specific, validated stakeholder need, and this should be acknowledged directly rather than papered over with an invented stakeholder persona.
- **Recommended methodology handling**: DSRM/DRM's "Objectives" and "Requirements" activities should proceed using the general-research-audience framing above, with an explicit note (carried into the final proposal) that stakeholder validation remains an open item.

---

## 12. Ethics and Integrity — Where the Methodology Must Incorporate Them

- **Data provenance / consent/legal basis**: must be addressed as an explicit, separate methodological checkpoint **before** Development/Demonstration proceeds on any new artifact build — currently unresolved (X-01, carried forward from Phase 5/6). **Not resolved here.**
- **Face-crop handling**: any Development activity (§5) that touches face-crop data should document handling (storage, access) as part of its activity record (guideline BAB 12 §12.7's documentation-artifact requirement) — not yet formally written, but should be a checklist item in the Development activity, not an afterthought.
- **Privacy**: same as above — no privacy statement currently exists (Phase 5/6); the methodology should require one before Communication (thesis writing).
- **Demographic interpretation**: the Evaluation activity (§5, §9) must apply the same non-causal, non-ethnicity-inferring discipline already used in R1–R9 (`docs/RESEARCH_FINDINGS.md` §10) to any new output the artifact produces — this is a **methodological control**, not just a writing-style rule: it should be checked as part of any Evaluation activity's completion criteria.
- **Skin-tone/ethnicity distinction**: same — a standing check applied at Evaluation and Communication activities, not resolved once and forgotten.
- **Transparent reporting**: the Learning activity (§10) explicitly requires reporting "unsuccessful design" and "failed hypotheses" with the same visibility as successes — this is a direct methodological commitment, not a general aspiration.
- **Negative results**: same — any future comparative extension's null result (as R7 already produced once) must be retained and reported, not filtered out at the Communication stage.

**Explicit statement, per instruction**: **data provenance and consent status is not resolved by this document.** It remains an open, unaddressed item that must be checked before any further Development activity proceeds on new data handling, and must be explicitly acknowledged (not silently omitted) in the eventual thesis regardless of whether it is ever fully resolved.

---

## 13. Recommendation

### Recommended Methodology: **DSRM (Design Science Research Methodology, Peffers et al. 2007)**

This is a **current recommendation, not the official final methodology.**

- **Why it fits the problem**: DSRM's Problem Identification → Objectives chain matches `PROBLEM_ARCHITECTURE.md`'s already-built Problem→Evidence→Research Need chain directly, without requiring restructuring.
- **Why it fits the artifact hypothesis**: DSRM expects a designed artifact of the general classes (construct/model/method/instantiation) that `ARTIFACT_ARCHITECTURE.md` already narrowed the candidate artifact to (Method/Evaluation-procedure) — a closer match than ERM (no native artifact concept) or ADR (wrong context entirely).
- **Why it fits the current evidence**: DSRM's Evaluation activity readily absorbs the already-substantial R1–R9 evaluative evidence as supporting material for a (still-to-be-formalized) artifact evaluation, without requiring that evidence be misrepresented as something it wasn't (§4's explicit non-rewriting of R1–R9's history).
- **Why it is feasible**: DSRM's six linear-but-iterable activities are well-suited to a Master's-thesis timeline, requiring no new organizational access (unlike ADR) and no abandonment of the design-research framing this whole workflow has been built around (unlike ERM).
- **What it cannot solve**: DSRM does not resolve the stakeholder-evidence gap (§11) — no methodology can, since that requires actual stakeholder data collection, which is out of scope here. DSRM also does not, by itself, guarantee the artifact rises above "primarily evaluative" (`ARTIFACT_ARCHITECTURE.md` §11) — that depends on how rigorously the Design & Development activity is actually carried out, not on the methodology label chosen.
- **What assumptions must be validated**: that a single build-evaluate-learn pass (§6) is sufficient — this assumption should be revisited once Development/Demonstration are actually attempted, not treated as guaranteed; that the general-research-audience stakeholder framing (§11) is acceptable to the supervisor/program, rather than requiring a more specific validated stakeholder.

### Second-Best Alternative: **DRM (Design Research Methodology, Blessing & Chakrabarti 2009)**

DRM would be preferable specifically if the thesis's eventual emphasis shifts toward a **more rigorous, structured impact-evaluation framing** than DSRM's relatively lighter Evaluation activity implies — DRM's explicit ex ante/ex post Impact Model (already cited by the guideline for exactly this purpose, §16 p.199–201) gives a more elaborated structure for reasoning about *why* an artifact's mechanism did or did not produce its expected effect, which could matter more if the skin-tone-stratified secondary analysis (Candidate B) becomes a larger, more central part of the final scope than currently planned. DRM would also be preferable if the supervisor specifically wants the proposal to engage more deeply with the descriptive-study/prescriptive-study distinction as a framing device. It is rated second, not first, mainly because it is a heavier methodological apparatus than this modestly-scoped thesis's current artifact hypothesis (a Method/Evaluation-procedure, not a large system) clearly requires — DSRM's leaner structure is a better proportionality match.

**ERM is explicitly not recommended as primary**, despite its strong technical-rigor fit, because adopting it would mean abandoning the design-research/artifact framing this entire workflow (Phase 0–6) has been built around — a legitimate but different thesis type (a purely evaluative/explanatory thesis) that would require restructuring, not just relabeling, the preceding phases. **ADR is not recommended at all**, given its categorical mismatch with the confirmed absence of any stakeholder/organizational context (§2, §11).

---

## 14. Methodology Risks

| Risk | Why It Matters | Mitigation |
|---|---|---|
| Methodology chosen after (some) implementation already exists | Could look like retrofitting a methodology label onto work that wasn't actually planned that way | §4 explicitly classifies R1–R9 as pre-methodology empirical work, not DSRM activities in disguise; this must be stated the same way in the eventual thesis methodology chapter, not smoothed over |
| Artifact still primarily evaluative | `ARTIFACT_ARCHITECTURE.md` §11 already found this; adopting DSRM does not automatically fix it | The Design & Development activity (§5, §7) must be carried out with genuine attention to specifying a *reusable procedure*, not just re-running existing scripts and calling the result "designed" |
| Missing stakeholder evidence | Weakens the Practical Contribution claim DSRM's Communication activity would otherwise support strongly | §11's explicit handling — proceed with general-research-audience framing, state the limitation plainly, do not invent a stakeholder |
| Insufficient iteration | A single build-evaluate-learn pass may be judged too thin for a design-research thesis by some reviewers | §6's explicit trigger conditions for refinement are stated in advance, so a decision not to iterate further is a *documented*, evidence-based choice, not an oversight |
| Insufficient validation | The artifact's evaluation (§9) currently only proposes checking reproduction of *already-known* findings, which is a weaker validation than testing genuinely new predictions | Flagged explicitly here; Phase 8 (Evaluation Architecture) must strengthen this if a stronger validation design is feasible within scope |
| Overclaiming design contribution | `ARTIFACT_ARCHITECTURE.md` §11's "primarily evaluation" finding could be forgotten by the time the thesis is written | This document restates that finding directly (§4, §7) so it remains visible in the methodology chain, not just buried in an earlier phase document |
| Inability to demonstrate refinement | If no refinement actually occurs (because evaluation finds no discrepancy), the thesis could appear to lack a genuine "Learn" step | §10 makes clear that *confirming* an artifact reproduces known findings without needing refinement is itself a valid, reportable outcome — absence of refinement is not the same as absence of learning |

---

## Completed

Compared DSRM, DRM, ERM, and ADR against the current problem, requirements, and working artifact concept, using the guideline's own citations (Peffers et al. 2007 for DSRM, Blessing & Chakrabarti 2009 for DRM) as the primary source and explicitly flagging ERM/ADR as not guideline-sourced. Distinguished research orientation / methodology / activities / methods / evidence. Classified every R1–R9 activity honestly (none reclassified as having followed a methodology it did not follow). Specified proposed future activities (already-completed vs. future, per instruction) with input/process/output/evidence. Determined a single build-evaluate-learn pass is currently justified, with explicit refinement triggers rather than assumed iteration. Built methodology→activity traceability (no unjustified elements). Separated data/methods/methodology explicitly. Positioned evaluation at requirement level only (full architecture deferred to Phase 8). Described concrete, accuracy-independent learning categories. Addressed the stakeholder gap without inventing a stakeholder. Addressed ethics/integrity placement without claiming provenance is resolved. Recommended DSRM (current recommendation, not final), with DRM as second-best and explicit reasoning for rejecting ERM/ADR as primary. Listed 7 methodology risks with mitigations. Produced `docs/proposal/design/METHODOLOGY_DESIGN.md`.

## Files Created

- `docs/proposal/design/METHODOLOGY_DESIGN.md`

## Files Modified

None. No source code, R1–R9 document, or prior proposal-phase document was changed.

## Key Findings

- **R1–R9 were not executed according to any named design-research methodology** — they are genuine, rigorous empirical/evaluative work, classified honestly in §4 rather than retrofitted. The only activity bordering on "design" (R4, ArcFace Experiment Design) was informal, made without a preceding formal Requirements phase — directly consistent with `ARTIFACT_ARCHITECTURE.md` §11's finding that the current work is "primarily evaluative, not yet a confirmed design contribution."
- **DSRM is recommended as the current-best methodology fit**, primarily on problem/artifact/feasibility/thesis-fit grounds, with DRM as a legitimate second-best specifically if the skin-tone secondary analysis grows into a larger, more central role. ERM and ADR are both explicitly not recommended as primary — ERM because it would abandon the design-research framing entirely, ADR because it categorically requires a stakeholder/organizational context this project does not have.
- **A single build-evaluate-learn pass is judged currently sufficient**, with explicit, evidence-based triggers for further iteration specified in advance (§6) — iteration is not assumed by default, nor ruled out.
- **The stakeholder gap is handled, not resolved** — DSRM/DRM can proceed with a general-research-audience framing, but this must be stated as an explicit limitation in the eventual thesis, not smoothed over.
- **Ethics/provenance (X-01) remains explicitly unresolved** — restated here as a required methodological checkpoint before any further Development activity, not claimed to be solved by anything in this document.

## Blockers

- X-01 (data provenance/consent) still unresolved — now additionally positioned as a required checkpoint before Development activities proceed.
- Stakeholder evidence still missing — handled via general-audience framing, not resolved.
- Official RQ still not finalized — several methodology-activity mappings (§7, Objectives row) remain contingent on this.

## Decisions Needed

- Whether DSRM (recommended) or DRM (second-best) better matches supervisor/program expectations for this thesis's methodology chapter.
- Whether the general-research-audience stakeholder framing (§11) is acceptable, or whether stakeholder validation should be attempted before proceeding further.
- Whether a single build-evaluate-learn pass (§6) is an acceptable scope, or whether the supervisor expects a more explicitly multi-iteration design process.

## Recommendation

Proceed to Phase 8 (Evaluation Architecture) using DSRM as the working methodology recommendation, with the single-pass build-evaluate-learn structure from §6/§9 as its starting evaluation position — full Evaluation Architecture (Objective → Requirement → Claim → Criterion → Indicator → Metric → Baseline → Evaluation Method → Data) to be built there, not here.

STOP — waiting for approval for the next phase.
