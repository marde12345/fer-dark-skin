# Papuan V2 — AI-Assisted Annotation Methodology Design Review

**Status of this document:** design review only. No code, data, Label Studio configuration, or experiment artifacts have been modified as part of producing this document. Nothing here is a decision — it is the trade-off analysis needed to make one.

**Context:** EXP-PAP-004's real human-human pilot is built but unlabeled (0/150 Annotator A, 0/75 Annotator B overlap — see `PAPUAN_V2_CURRENT_STATE.md`). Before more labeling effort is spent, the supervisor has proposed a different workflow: paid AI-assisted annotation inside Label Studio, i.e. an AI pre-label that a human reviews and corrects, with the human-corrected label — not the raw AI output — becoming ground truth. This document evaluates how that instruction should be implemented without undermining the pilot's existing independence/circularity safeguards.

---

## 1. Comparison of Three Candidate Designs

### Design A — Both annotators see the AI pre-label

```text
AI pre-label
   ├── Annotator A review
   └── Annotator B review
             ↓
        Agreement
             ↓
      Final ground truth
```

| Dimension | Assessment |
|---|---|
| Methodological advantages | Fastest annotation throughput (both annotators start from a draft rather than a blank label); most literal reading of "AI-assisted annotation"; both annotators experience the same workflow, so operational comparison between them (speed, correction rate) is apples-to-apples. |
| Methodological risks | Correlated anchoring: if both annotators are nudged toward the same AI suggestion, their agreement is inflated by shared exposure to the same stimulus, not by independent reasoning converging on the same answer. A high measured human-human agreement under Design A cannot be cleanly attributed to "genuine consensus" vs. "both anchored on the same draft." |
| Annotation efficiency | Highest of the three designs — every task starts pre-filled. |
| AI-induced anchoring bias | Highest risk of the three designs, and unmeasured — there is no blind condition to compare against, so the magnitude of the anchoring effect in this specific annotator pool is never known. |
| Human-human agreement validity | Weakest — the resulting agreement statistic answers "do two people converge when shown the same draft," which is a different (and less informative) question than "do two people independently arrive at the same label." |
| Suitability for a thesis | Workable, but an examiner is likely to ask how anchoring was ruled out; without a blind arm, that question has no empirical answer, only a caveat in the limitations section. |
| Reproducibility | High — a single, simple workflow (one Label Studio configuration serves both annotators identically). |
| Implementation complexity | Lowest of the three — one annotation-UI configuration, one prediction-import step, no per-annotator branching logic. |

### Design B — One AI-assisted annotator + one blind annotator

```text
AI pre-label
      ↓
Annotator A
      ↓
Candidate labels
      ↓
Annotator B (blind)
      ↓
Agreement / adjudication
      ↓
Final ground truth
```

| Dimension | Assessment |
|---|---|
| Methodological advantages | Converts the anchoring risk from an unmeasured caveat into a measured variable: Annotator B's blind labels function as an independent baseline against which Annotator A's AI-assisted labels can be compared. This also directly reuses the project's *already-validated* two-isolated-server architecture (Phase 1) with no structural change — only the content of what Annotator A's server shows changes. |
| Methodological risks | Annotator A and Annotator B are no longer doing the same task, which complicates interpreting "human-human agreement" as a single number — agreement now partly reflects an annotator-condition effect (AI-assisted vs. blind), not annotator identity alone. If A and B disagree, it is not immediately clear whether that reflects genuine label ambiguity or the AI-assistance condition itself. |
| Annotation efficiency | Mixed — Annotator A benefits from AI speed-up, Annotator B does not; overall pilot throughput is between Design A and a fully-blind pilot. |
| AI-induced anchoring bias | Directly measurable: compare Annotator A's acceptance rate / disagreement-with-B rate against what a fully-blind pilot would show. This is the only one of the three designs that produces a number for the anchoring effect rather than just a concern about it. |
| Human-human agreement validity | Partially compromised by design, but in a disclosed, useful way — the "agreement" figure becomes "AI-assisted-vs-blind agreement," which is itself a legitimate and reportable research quantity, just not the same quantity as classic inter-annotator agreement. |
| Suitability for a thesis | Strong — it turns the supervisor's methodological concern (anchoring bias) into an empirical result the thesis can report, rather than a limitation to apologize for. |
| Reproducibility | High — reuses existing infrastructure (two isolated Label Studio instances/projects) with a one-line change to which project receives AI predictions. |
| Implementation complexity | Low-to-moderate — requires one Label Studio project to receive AI pre-labels via the prediction-import mechanism and the other to remain exactly as the current blind pilot already is; no new UI logic, only an added import step on one side. |

### Design C — AI-assisted annotation + independent audit sample

```text
AI pre-label
      ↓
Human review
      ↓
Final labels
      ↓
Independent human audit sample
```

| Dimension | Assessment |
|---|---|
| Methodological advantages | Scales best — only one annotator does AI-assisted review of the full set, and a smaller random/stratified subsample gets a fully independent second opinion for quality control. Mirrors a common applied-ML / industry QA pattern (spot-check audits) rather than a classic academic inter-annotator-agreement design. |
| Methodological risks | The "independent audit sample" measures *label error rate* on a subsample, not inter-annotator agreement on the full set — a different and weaker claim. If the audit sample is small, confidence intervals on the implied error rate will be wide, and this needs to be stated plainly rather than implied away. |
| Annotation efficiency | Highest total efficiency for a given label count, since only the audit subsample needs duplicate labor. |
| AI-induced anchoring bias | Present and essentially unaddressed for the primary (full-set) annotator, since no blind full-set baseline exists; the audit sample can be blind, giving a partial, subsample-only anchoring estimate. |
| Human-human agreement validity | Limited to the audit subsample; cannot be generalized to the full 150-image set without an explicit (and debatable) stationarity assumption. |
| Suitability for a thesis | Workable as a secondary/QA design, weaker as the thesis's primary evidence for annotation quality if the audit sample is small; stronger if combined with a reasonably large audit fraction (e.g. the existing 75/150 = 50% overlap fraction already used in the current pilot design). |
| Reproducibility | High, and notably: this design is structurally closest to what EXP-PAP-004 *already does* (full set + 50% deterministic overlap) — it only adds an AI pre-label step in front of the first pass. |
| Implementation complexity | Lowest change from the current pilot's existing shape — the overlap-assignment, isolated-server, and export machinery can be reused essentially unmodified; only a prediction-import step is new. |

**No ranking is given.** All three are methodologically legitimate under different weightings of speed vs. measurability-of-bias vs. reuse-of-existing-infrastructure; Section 6 turns these into concrete protocols and Section 7 identifies the one decision that actually has to be made before implementation.

---

## 2. What Is EXP-PAP-004 Actually Trying to Establish?

The repository's own design documents and code conflate several distinct research questions that should be kept conceptually separate, since introducing AI pre-labels changes the validity of some of them and not others:

| Question | What it needs | Does introducing AI pre-labels change it? |
|---|---|---|
| **Human ground truth** — what is the "true" emotion label for each image? | At least one human judgment per image, ideally independent of any single model's bias. | Yes, directly — the central question of this whole review is whether an AI-pre-labeled-then-corrected judgment still counts as a valid ground-truth judgment, and under what conditions. |
| **AI-assisted labeling (process)** — how does showing an AI suggestion change annotation behavior/speed/content? | Both an AI-assisted condition and a blind condition to compare against. | This question *only exists* once AI pre-labels are introduced; EXP-PAP-004 as currently built cannot answer it at all. |
| **Model prediction** — what does HSEmotion/ArcFace+LR output for each image? | Already exists: `ai_predictions.csv`, 150×2 rows, complete. | No — unaffected, this is pure model inference, independent of annotation workflow. |
| **Model-vs-human agreement** — do HSEmotion/ArcFace+LR predictions match human ground truth? | Ground truth (above) + predictions (already have). | Yes, critically — see Section 5. If the pre-label source overlaps with the evaluated model, this comparison becomes partially circular. |
| **Human-human agreement** — do independent human judges agree with each other? | Two genuinely independent human judgments on overlapping images. | Yes — this is exactly the quantity AI pre-labels put at risk (Designs A/B above), since "independent" stops being true once both see the same draft. |
| **Robustness to CLAHE** — does preprocessing change model behavior? | Predictions on both CLAHE and non-CLAHE crops; currently CLAHE-only. | No — orthogonal to the annotation-workflow question; not something this AI-assisted-annotation decision affects either way. |
| **Bias/fairness analysis** — does performance vary across identities/skin tones/etc.? | Demographic or identity metadata plus per-group metrics; not currently built. | No direct effect, but AI-induced anchoring bias (if present and unmeasured) would be a confound that is hard to disentangle from a genuine fairness effect later — another reason to measure anchoring explicitly (Design B) rather than leave it unmeasured (Design A/C). |

**Does introducing AI pre-labels change the interpretation of EXP-PAP-004?** Yes, materially. As currently designed (no AI pre-label), EXP-PAP-004's 75-image overlap exists specifically to measure human-human agreement as a proxy for label reliability. If an AI pre-label is shown to both annotators (Design A), that overlap measurement stops cleanly answering "are humans reliable" and starts answering "do humans converge when shown the same draft" — a different and weaker claim that risks being reported as if it were the former. This is not a reason to avoid AI assistance; it is a reason the *design choice* (A vs. B vs. C) has to be made deliberately rather than defaulted into.

---

## 3. Label Studio Implementation Options

### What the current self-hosted/Community setup already supports

- **Prediction import** — Label Studio's task JSON format has a native `predictions` field; a task can be created (or updated) with one or more model predictions attached, which the labeling UI can then pre-fill before a human ever opens it. This is a core, documented Community Edition feature — not Enterprise-gated.
- **Multiple isolated projects/servers** — already built and validated by this project (Phase 1 validation + EXP-PAP-004's two-server design), sufficient for Design B or Design C above without further Label Studio-level work.
- **Export with full annotation history** — `label_studio_export.csv` and the existing `export_label_studio_labels.py` script already pull completed annotations out; the same mechanism can be extended to also pull the attached prediction alongside the human's final choice, since Label Studio retains both.

### What would require Label Studio Enterprise/paid functionality

- **Built-in reviewer workflows / task-level review-and-accept UI** (a dedicated "reviewer" role distinct from "annotator," with sign-off tracking) is an Enterprise feature. The project's own Phase 1 finding — that Community Edition's `OrganizationMember` has no role field — already confirms this gap exists in the deployed version (1.23.0 Community).
- **Built-in model-backend management UI** (configuring/monitoring an ML backend through the Label Studio UI rather than a script) is more polished in Enterprise, though the underlying "ML backend" protocol itself is not Enterprise-exclusive.

### Whether an external paid vision/LLM API could be integrated

Yes, structurally straightforward: a standalone script calls the paid API (e.g. a VLM) per image, writes the result into each task's `predictions` field via Label Studio's REST API (`POST /api/tasks` or `PATCH` with a `predictions` payload) before the annotator opens it — no Label Studio ML-backend server process is required for a one-shot batch pre-annotation step. This is the lowest-implementation-complexity integration path and does not require Label Studio Enterprise.

### Whether a Label Studio ML backend is sufficient / necessary

Not necessary for the proposed workflow. An ML backend (a long-running prediction server Label Studio calls live, e.g. for interactive/streaming pre-annotation) is the right tool if predictions need to be generated on-demand per task as annotators open them. For a fixed, pre-generated batch of 150 images, a simpler one-time batch script that writes `predictions` into each task ahead of time is sufficient and matches how `ai_predictions.csv` is already generated offline today — no new infrastructure class is required, only a new import step.

### How predictions would enter the annotation workflow

1. Generate AI pre-labels offline (paid API or local model) for the relevant task set → a CSV/JSON, analogous to the existing `ai_predictions.csv`.
2. Import into Label Studio via the task `predictions` field, either at task-creation time or via a PATCH to existing tasks (the project already has precedent for PATCH-based task updates — the overlap-assignment step in `apply_task_overlap.py` does this for `human_labels.csv` row data; preserved byte-identical per the audit's verification).
3. Annotator opens the task; Label Studio UI shows the prediction as the pre-filled form state, which the annotator can accept as-is or change.
4. On submission, Label Studio stores the human's final annotation as the `result`; the original `predictions` entry remains retrievable separately (Label Studio does not overwrite predictions with results — they are distinct fields on the task).

### Can AI predictions be stored separately from final human labels?

Yes, and they already are, structurally, by Label Studio's own data model (`task.predictions` vs. `task.annotations`/`result`) — no custom storage mechanism is required to keep them apart; the risk is only in the *export* step silently collapsing them into one field. The export script must be written (or extended) to preserve both explicitly.

### What provenance metadata should be stored

See Section 4 below.

---

## 4. Minimal Data/Provenance Model

Evaluating the illustrative field list against actual necessity for this project's stated research questions (Section 2) and leakage-prevention requirements (Section 5):

| Field | Necessary? | Reasoning |
|---|---|---|
| `image_id` | **Yes** | Required join key; already the convention in `pilot_manifest.csv`/`human_labels.csv`. |
| `annotator_id` | **Yes** | Already a convention in this project (real, resolvable identities — see audit finding on the current pilot). Required to compute per-annotator statistics and to know which arm (AI-assisted vs. blind) an annotation belongs to under Design B. |
| `ai_provider` | **Yes, if AI pre-labels are used** | Needed for the thesis's circularity disclosure (Section 5) and because paid APIs can silently change model versions — provider identity is part of reproducibility. |
| `ai_model` / `ai_model_version` | **Yes, if AI pre-labels are used** | Same reasoning; without a version string, "we used an AI pre-label" is not a reproducible methods-section claim. Can be merged into a single `ai_model_version` string field rather than two separate columns — unnecessary to split further. |
| `ai_prediction` | **Yes** | The actual pre-label shown, needed to compute acceptance/correction rate (a reportable statistic per Section 1 Design B). |
| `ai_confidence` | **Conditionally necessary** | Only if the AI source actually returns a calibrated confidence value the project intends to analyze (e.g. "did annotators correct low-confidence suggestions more often"). If the chosen AI source does not expose a meaningful confidence score, omitting this field is correct — do not fabricate or default one. |
| `human_initial_label` | **Unnecessary, with a caveat** | Only meaningful if the UI/workflow distinguishes "what the human saw first" from "what the human submitted" as two separate recorded states, which the current Label Studio data model does not naturally separate (predictions vs. result already captures this: `ai_prediction` is "what they saw first," `human_final_label` is "what they submitted" — an extra `human_initial_label` field would be redundant with `ai_prediction` unless the human is allowed multiple intermediate edits worth tracking, which is over-engineering for this pilot's scale). |
| `human_final_label` | **Yes** | The actual ground-truth-candidate value; already the role `human_labels.csv`'s `gt_label` column plays today. |
| `human_changed_ai_prediction` | **Yes, but derivable** | Equivalent to `ai_prediction != human_final_label`; worth materializing as an explicit boolean column at export time (rather than left purely implicit) because it is the single most load-bearing statistic for both the anchoring-bias analysis (Section 1) and the thesis's methods section (Section 5.6) — but it does not need to be captured at annotation time, only computed once at export/analysis time. |
| `annotation_timestamp` | **Yes** | Already present in Label Studio's own export (`created_at`/`updated_at`); needed to detect suspiciously fast accept-without-review behavior (a basic annotation-quality check). |

**Fields to deliberately exclude as over-engineering for this project's current scale:** per-keystroke edit logs, free-text `human_correction_reason` as a *required* field (optional free text is fine if an annotator wants to add it, but mandating structured reason codes for a 150-image pilot adds annotator burden disproportionate to the benefit at this sample size), and separate `review_started_at`/`review_completed_at` timestamps beyond what Label Studio already logs natively.

**Minimal resulting schema:**
```text
image_id
annotator_id
ai_provider
ai_model_version
ai_prediction
ai_confidence            (only if the source provides a real one)
human_final_label
human_changed_ai_prediction   (derived at export time)
annotation_timestamp
```

---

## 5. Evaluation Leakage Analysis

1. **Can HSEmotion generate the AI pre-label?** Technically yes — HSEmotion already runs offline and outputs a label per image (`ai_predictions.csv` already has these). But doing so and then evaluating HSEmotion against the resulting human-corrected ground truth is methodologically compromised: the human's correction behavior is anchored on HSEmotion's own output (Section 1, anchoring bias), so HSEmotion would be partially evaluated against a label it helped produce. This does not make HSEmotion's resulting accuracy meaningless, but it inflates it in an unknown, unmeasured direction unless a blind baseline (Design B/C) exists to quantify the inflation.

2. **Can ArcFace+LR generate the AI pre-label?** Same reasoning as (1), with an added concern specific to this project: the audit already found the ArcFace+LR classifier was trained on **legacy, non-Papuan-V2 data** with a documented train/inference preprocessing mismatch. Using this specific classifier to pre-label the Papuan V2 pilot would compound two separate validity problems (anchoring bias + an already-known distributional mismatch) in one place, making any resulting evaluation of ArcFace+LR especially hard to interpret.

3. **Can a third-party emotion model generate the AI pre-label?** Yes, and this is the cleanest option from a leakage standpoint: if the pre-label source is architecturally and provenance-wise distinct from both evaluated systems (HSEmotion and ArcFace+LR), then neither evaluated model's reported accuracy is self-referential. The project does not need the pre-label source to be *better* than HSEmotion/ArcFace+LR — only *different enough that neither evaluated model gets credit for its own suggestion being accepted.*

4. **Can an LLM/VLM generate the AI pre-label?** Yes, and this is a specific case of (3) — likely what "paid AI-assisted annotation" in the supervisor's instruction refers to. A general-purpose paid VLM is architecturally unrelated to either evaluated candidate (HSEmotion is a dedicated small CNN classifier; ArcFace+LR is embedding+linear-classifier), so using one to pre-label avoids the same-model circularity of (1)/(2). It does not avoid *general* anchoring bias (Section 1, point 2 of the existing methodology review) — a VLM's wrong suggestion can still bias a human reviewer even though it isn't the model later being scored.

5. **If the AI pre-label is wrong, how could it influence the human annotator?** Through anchoring: a plausible-but-wrong suggestion is accepted at a higher rate than a human would independently produce that same wrong answer from a blank slate, because reviewing-and-confirming requires less cognitive effort than generating-from-scratch, and a plausible wrong answer does not always trigger the "this looks off" signal a human would need to override it. This effect is well-established in human-AI collaboration literature generally; this project has no current data to quantify its own magnitude, which is exactly the gap Design B's blind arm is positioned to fill.

6. **How should this limitation be documented in the thesis?** Explicitly, with numbers where available: name the pre-label source and its relationship (or lack thereof) to the evaluated models (points 1–4); if a blind condition exists (Design B), report the measured acceptance/correction rate and any agreement delta between the AI-assisted and blind annotator; if no blind condition exists (Design A or a non-audited Design C), state plainly that anchoring bias was not empirically measured and that reported human-human or human-AI agreement should be read as an upper bound on independence, not a clean estimate of it.

---

## 6. Recommended Experimental Protocol Options

No ranking given — these map roughly onto Designs A/B/C above, made concrete for this specific repository's existing tooling.

### Protocol 1 — "Blind-vs-Assisted Split" (maps to Design B)

```text
Protocol name:        Blind-vs-Assisted Split
Purpose:               Produce a ground-truth label set while directly measuring AI-induced anchoring bias as a reportable statistic, reusing existing infrastructure almost unchanged.
Workflow:               Annotator A's existing 150-task Label Studio project receives AI pre-labels (via task.predictions import) before A annotates; Annotator B's existing 75-task overlap project remains exactly as-is today (no predictions imported, fully blind).
Annotator setup:        No change to the existing two-isolated-server architecture (Phase 1-validated); only Project A's task-creation/update step changes to include a predictions payload.
AI visibility:          Annotator A sees AI suggestions; Annotator B does not (deliberately asymmetric, by design).
Ground-truth construction: On the 75-image overlap, where A and B agree, that label is ground truth; where they disagree, adjudication is needed (a third opinion, or a documented tie-break rule) — the existing architecture does not yet have an adjudication step and one would need to be designed (not implemented here).
Agreement measurement:   Two numbers, not one: (a) A-vs-B agreement on the 75-overlap set (interpretable as an AI-assisted-vs-blind comparison, not classic IAA); (b) A's AI-suggestion-acceptance rate (what fraction of A's final labels equal the AI pre-label) — a direct anchoring-magnitude estimate.
Main methodological caveat: The 75-image "overlap" no longer measures classic human-human reliability; it measures agreement under differing AI-exposure conditions, which must be reported as such, not relabeled as standard inter-annotator agreement.
Implementation effort:  Low — only a predictions-import step is added to Project A's existing task-creation code path; Project B's code path is untouched.
```

### Protocol 2 — "Full AI-Assisted with Deterministic Audit" (maps to Design C, closest to current pilot shape)

```text
Protocol name:        Full AI-Assisted with Deterministic Audit
Purpose:               Maximize annotation throughput across the full 150-image set while preserving a meaningful independent-quality check, reusing the pilot's existing 50% overlap fraction unchanged.
Workflow:               All 150 tasks (Project A) receive AI pre-labels; the existing deterministic 75-image overlap subset (already selected, seed=100) is additionally labeled blind by Annotator B (Project B unchanged, as today).
Annotator setup:        Identical to Protocol 1's infrastructure — the difference from Protocol 1 is purely interpretive: here, B's 75 labels are framed explicitly as an audit/QA sample against A's full AI-assisted set, not as a parallel ground-truth source.
AI visibility:          Same as Protocol 1 (A sees AI suggestions, B does not) — Protocol 1 and 2 are nearly identical in implementation; they differ mainly in how the resulting 75-overlap comparison is used (bias measurement vs. quality audit) and how ground truth for the non-overlap 75 images is constructed (Protocol 2 treats A's AI-assisted labels as ground truth for the un-audited 75, Protocol 1 does not make this full-set ground-truth claim).
Ground-truth construction: AI-assisted A-labels serve as ground truth directly for the 75 non-overlap images; for the 75 overlap images, A-vs-B agreement/adjudication (same as Protocol 1) determines ground truth.
Agreement measurement:   Audit-sample agreement rate (A vs. B on the 75 overlap) is used to estimate an implied label-error rate for the full 150-image set — an explicit extrapolation that should be reported with the caveat that it assumes the audited half is representative of the un-audited half.
Main methodological caveat: Treating the non-overlap 75 images' AI-assisted labels as ground truth without any blind check on them is the weakest link — the thesis would need to explicitly justify why the audit-sample agreement rate is assumed to generalize to the unaudited half.
Implementation effort:  Low — essentially identical code changes to Protocol 1; the only difference is in the downstream ground-truth-construction script's logic, not the Label Studio import mechanism.
```

### Protocol 3 — "Fully Blind Baseline, AI Compared Post-Hoc" (no AI exposure during annotation)

```text
Protocol name:        Fully Blind Baseline, AI Compared Post-Hoc
Purpose:               Preserve the cleanest possible human-human ground truth (no annotator ever sees an AI suggestion before submitting), then compare the AI pre-label against the finished ground truth afterward, purely as an offline analysis step.
Workflow:               Both Annotator A (150 tasks) and Annotator B (75-overlap tasks) label exactly as the current, already-built pilot does today — zero changes to Label Studio task creation. AI pre-labels are generated and stored separately (e.g. extending ai_predictions.csv-style offline output) but never imported into any task's predictions field.
Annotator setup:        Fully unchanged from the current, already-implemented EXP-PAP-004 pilot.
AI visibility:          Neither annotator ever sees the AI suggestion before submitting their own label.
Ground-truth construction: Standard human-human agreement/adjudication on the existing 75-overlap set, exactly as originally designed — unaffected by any AI-assistance question.
Agreement measurement:   Classic human-human IAA (uncontaminated by anchoring, since no AI exposure occurred) plus a separate, independent "AI-suggestion accuracy against finished ground truth" statistic computed afterward.
Main methodological caveat: This does not satisfy the supervisor's literal instruction ("AI pre-annotation → human review → correction") — the AI never participates in the annotation workflow itself, only in a post-hoc comparison. Whether this still counts as "AI-assisted annotation" in the sense intended needs confirmation (Section 7, question 1).
Implementation effort:  Lowest of the three — requires no change to the Label Studio workflow at all, only an additional offline comparison script once both human label sets exist.
```

---

## 7. Recommendation to Discuss With Supervisor

No design is declared the winner here. The repository audit identifies one decision that blocks all forward implementation, plus supporting questions whose answers determine which protocol in Section 6 is applicable.

**The key methodological decision requiring supervisor confirmation:**

> Should the AI pre-label be shown to both annotators, to one annotator while the other remains fully blind, or to neither annotator during labeling (with the AI compared only after human labels are finished)? This single choice determines whether EXP-PAP-004's existing 75-image overlap still measures classic human-human agreement, or instead measures something else (AI-assisted-vs-blind agreement, or an audit-sample error rate) that must be reported differently in the thesis.

**Concise questions to raise with Pak Fadhil:**

1. "Should the second annotator (B) remain blind to AI pre-labels so that we retain an independent agreement measurement, or is the literal 'AI pre-label → human review' workflow intended for both annotators?"
2. "For the AI pre-label source, is a third-party/paid model (distinct from HSEmotion and ArcFace+LR) required to avoid circularity, or would he consider it acceptable — with disclosure — for one of the two evaluated models to also generate the pre-label?"
3. "Does the thesis need an empirically measured anchoring-bias estimate (which requires a blind comparison arm, i.e. Protocol 1 or 2), or is a documented limitation/caveat about unmeasured anchoring sufficient (which would permit the simpler Protocol 3, or Design A)?"

**Information needed from him before implementation begins:**

- Confirmation of which of Designs A/B/C (or Protocols 1–3) matches his intent for "paid AI-assisted annotation," since "paid AI-assisted annotation in Label Studio" alone is compatible with several structurally different workflows.
- Which paid provider/model he has in mind (or budget/access constraints), since this determines whether `ai_provider`/`ai_model_version` will name a VLM, a commercial emotion-recognition API, or something else — and whether it is independent enough from HSEmotion/ArcFace+LR to avoid the circularity concern in Section 5.
- Whether the existing 150/75 pilot scale is still the intended scope for this methodology change, or whether a decision to use paid AI assistance also implies revisiting the full-dataset-scope question already flagged as undecided in `PAPUAN_V2_CURRENT_STATE.md`.

---

## What Should NOT Be Implemented Yet

- No Label Studio project, task, or prediction-import code should be written until Question 1 above is answered — it determines which of Protocols 1–3 (structurally different Label Studio configurations) applies.
- No paid API should be called or budgeted until Question 2 is answered — the provider choice is itself a circularity-prevention decision, not an implementation detail.
- The existing EXP-PAP-004 blind pilot (0/150, 0/75) should not be abandoned or reset in the meantime — under Protocols 1–3, the current infrastructure is reused, not replaced, so no existing work is wasted by waiting for this decision.

---

*Generated as a design review, 2026-10-01. No code, dataset, Label Studio configuration, or experiment data was modified in the course of producing this document.*
