# Papuan V2 — Current State (Master Report)

**Audit date:** 2026-10-01. **Scope:** repository state, not documentation claims. Where documentation and repository state disagreed, repository state (file contents, row counts, test results) is reported as authoritative, and the discrepancy is noted explicitly.

## Executive Summary

The Papuan V2 pipeline has a solid, tested foundation (frame extraction → face detection → CLAHE → AI-candidate predictions, 645 crops / 150-image pilot subset) and a well-designed, genuinely-isolated two-annotator Label Studio pilot (EXP-PAP-004), plus a narrow but real architecture-validation exercise (Phase 1, throwaway port-8090 server, 20 passing tests) confirming that a shared Label Studio instance can safely serve multiple annotators without leaking content. However, the project is currently **blocked at the human-labeling step**: of 150 pilot images, **0 have a human ground-truth label** (one real Label Studio annotation exists but was never copied into `human_labels.csv`), and the secondary annotator has completed 0 of 75 overlap images. Every downstream step — AI-candidate selection, agreement metrics, consensus, ground truth, model evaluation — is consequently blocked, by code-enforced guards, not just by policy.

Separately, and this is the most important finding for the supervisor's new direction: **AI-assisted annotation (AI pre-label → human review/correction inside Label Studio) does not exist in this repository in any form.** No ML backend, no paid-AI-provider integration, no prediction-import code, no provenance schema for "AI suggested, human corrected." The existing `ai_predictions.csv` is an offline comparison artifact for selecting *which* model to use later, not an implementation of AI-assisted annotation itself. This is a greenfield phase requiring a methodological decision (blind vs. pre-filled annotation) before any implementation should begin.

## Phase Status

| Phase | Status | Evidence | Main Blocker |
|---|---|---|---|
| 0 — Dataset/Pipeline Foundation | DONE (pilot scale) | `data/papuan_v2/{faces,clahe}/` (645 each), `experiments/EXP-PAP-004/pilot_manifest.csv` | Full-dataset scope (uncapped video) undecided |
| 1 — Architecture Validation | DONE | `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` Phase 1 section, 20 passing tests | None (self-contained) |
| 2 — EXP-PAP-004 Pilot | BLOCKED | `human_labels.csv` 0/150 filled; `annotator_progress.json` | Human labeling not performed |
| 3 — AI-Assisted Annotation | NOT IMPLEMENTED | No code found anywhere in repo | Methodology decision not made; no implementation started |
| 4 — Human-Validated Ground Truth | NOT STARTED | No `final_labels.csv`/`consensus.csv` exist | Depends on Phase 2 + Phase 3 |
| 5 — Model Evaluation | BLOCKED | `pilot_agreement_report.py` refuses to run (RuntimeError guard) | Depends on Phase 2 |
| 6 — Agreement & Robustness | BLOCKED | Metric code tested on synthetic data only | Depends on Phase 2 |

## Current Pipeline (as actually implemented today)

```
pesta_babi.mp4
     │  (EXP-PAP-001, capped 250 frames)
     ▼
645 face crops  ──CLAHE──▶  645 CLAHE crops
     │
     │ (EXP-PAP-002, seeded sample, n=150)
     ▼
150-image pilot set (data/papuan_v2/pilot/images/)
     │
     ├────────────────────────────┐
     ▼                             ▼
AI predictions (offline,      Label Studio (2 isolated servers)
both candidates,              Project A (:8080) — Annotator A, 150 tasks
150/150 each)                 Project B (:8081) — Annotator B, 75 overlap tasks
ai_predictions.csv                  │
     │                              ▼
     │                       human_labels.csv  ◀── 0/150 FILLED (BLOCKED HERE)
     │                              │
     └──────────────✗ (no agreement run yet) ✗──┘
                        ↓ (blocked)
          pilot_agreement_report.py / human_agreement_report.py
                        ↓ (blocked)
          AI-candidate selection decision (human, manual)
                        ↓ (not started)
          Full-dataset AI-assisted annotation  ◀── DOES NOT EXIST
                        ↓ (not started)
          consensus.csv / final_labels.csv / ground truth  ◀── DOES NOT EXIST
                        ↓ (not started)
          HSEmotion / ArcFace evaluation against ground truth
```

## Annotation Architecture (as actually implemented)

```
Pilot (EXP-PAP-004, real):
  Server :8080 — Project "EXP-PAP-004 Papuan V2 Pilot (Blind)" (id=2)
    └─ Annotator A — 150 tasks, overlap=2 on 75 of them
  Server :8081 — Project "EXP-PAP-004 Overlap (Annotator B)" (id=1)
    └─ Annotator B — 75 tasks (deterministic overlap subset, seed=100)
  Isolation mechanism: SEPARATE SERVER PROCESSES (separate port/data-dir/DB/org) —
  required because Label Studio Community 1.23.0 has no per-project role-based
  isolation (OrganizationMember has no role field).

Phase 1 validation (throwaway, torn down):
  Server :8090 — Project "PHASE1-VALIDATION (throwaway, not pilot)" (id=1, separate org/DB)
    └─ 4 synthetic users (1 owner + 3 annotators), 3 synthetic fixture tasks
  Confirmed: a SHARED project with task.overlap=3 does NOT leak co-annotator
  content before submission (only a non-content annotation-count is visible).
  This validates that a shared-instance design (no longer requiring separate
  servers) is viable FOR THE FUTURE full 3-annotator workflow — not yet adopted
  for anything real.
```

## Dataset State

- **Images**: 645 face crops (`data/papuan_v2/faces/`) + 645 CLAHE crops (`data/papuan_v2/clahe/`) + 150-image pilot subsample (`data/papuan_v2/pilot/images/`, CLAHE only).
- **Locations**: all under `data/papuan_v2/`; experiment artifacts under `experiments/EXP-PAP-004/`.
- **Preprocessing state**: CLAHE Strategy B applied and used as the sole input for all pilot/AI-prediction work; non-CLAHE originals preserved but unused downstream so far.
- **Labels**: 0 human ground-truth labels exist for the pilot (150/150 `human_labels.csv` rows blank); exactly 1 real Label Studio annotation exists in the system (`frame_000008_face01` → `Neutral`/`Medium`, not yet propagated into `human_labels.csv`'s `gt_label`); 300 AI-candidate prediction rows (150 × 2 models) exist and are complete.
- **Splits**: none — no train/test/val split exists or is needed yet (ArcFace classifier was trained entirely on legacy, non-Papuan-V2 data).
- **IDs/lineage**: strong — `pilot_manifest.csv` records `image_id`, source paths, sampling seed, and timestamp for every pilot image; `source_video_manifest.json` records video SHA-256 and extraction parameters.
- **Missing metadata**: full-dataset-scope decision (645 vs. re-extracted larger pool) is undocumented/undecided; AI-prediction schema lacks `ai_model_version`/`input_preprocessing`/`source_crop_path` fields the full-workflow plan proposes adding.

## Model State

- **HSEmotion** (`enet_b0_8_best_vgaf`, `hsemotion-onnx==0.3.1`): predictions complete on the 150-image pilot (150/150 ok); zero evaluation metrics computed (blocked on ground truth).
- **ArcFace + LogisticRegression** (`buffalo_l/w600k_r50` embeddings, classifier trained on **legacy**, non-Papuan-V2 data via `tools/train_arcface_classifier.py`): predictions complete on the 150-image pilot (150/150 ok, after a documented re-detection bugfix); classifier/embedding pipeline has a known, explicitly-documented distributional mismatch between training (aligned) and inference (unaligned, direct `get_feat()`) paths; zero evaluation metrics computed.

## Human Annotation State

- **Tasks**: 150 assigned to Annotator A, 75 (deterministic overlap, seed=100) assigned to Annotator B.
- **Annotators**: 2 real identities confirmed working (`Annotator A` has 1 real submitted annotation); Annotator B's identity/server is set up but has 0 submissions.
- **Completion**: 1/150 (A), 0/75 (B).
- **Overlap**: correctly, deterministically computed (75 of 150 images, seed=100) and reflected in `annotator_assignment.csv`; Task 1's existing annotation was preserved byte-identical through the overlap-PATCH operation (verified).
- **Exports**: `label_studio_export.csv` exists with exactly 1 real data row; export pipeline is otherwise validated only via unit tests with synthetic data.
- **Agreement**: `null` / not computed — both the AI-vs-human and human-vs-human agreement scripts refuse to run against incomplete data (enforced by a runtime guard, not merely absent).

## AI-Assisted Annotation State

- **Implemented**: NO. Confirmed by repo-wide search — no ML backend, no paid-AI-provider SDK/dependency, no prediction-import code, no pre-annotation UI/workflow.
- **Current technology**: Label Studio Community Edition 1.23.0, self-hosted via local server processes (no Docker). Native `task["predictions"]` import mechanism exists in Label Studio itself and is structurally usable, but unused by any script in this repo.
- **Required changes**: (1) supervisor decision on blind-vs-pre-filled AI suggestion visibility to annotators; (2) decision on paid-AI-provider vs. self-hosted-model source for pre-annotations, and whether that source overlaps with HSEmotion/ArcFace+LR (circularity risk if so); (3) new provenance schema fields (`ai_suggested_label`, `human_accepted_ai`, `human_correction_reason`, `ai_model_version`); (4) a Label Studio prediction-import script; (5) human-review-workflow enforcement (AI output must never silently become the stored label without a human action).
- **Open methodological questions**: see the dedicated review section below.

## Blockers

1. **(Primary, cascades to everything downstream)** No real human labels exist for the EXP-PAP-004 pilot — 0/150 (A), 0/75 (B). This is a deliberate gap: the repository's own `report.md` states the implementing assistant declined to fabricate labels, since doing so would defeat the pilot's independence/circularity safeguards.
2. AI-assisted annotation (the supervisor's new direction) has zero implementation and an unresolved methodology decision (blind vs. pre-filled suggestion) that must be made by a human before building anything.
3. Dataset-size scope (645 crops vs. a larger re-extraction) is undecided and blocks any "full workflow" (`EXP-PAP-010`+) work.

## Recommended Next Actions (ordered by dependency, no scope expansion)

1. Complete real human labeling for the 150-image pilot (Annotator A) and the 75-image overlap (Annotator B) — this is a human task, not something that can be automated or delegated further in code.
2. Run `pilot_agreement_report.py` and `human_agreement_report.py` against the now-complete data to produce real metrics.
3. Human (supervisor/researcher) reviews the metrics and records the AI-candidate-selection decision in `docs/EXPERIMENT.md`.
4. Resolve the AI-assisted-annotation methodology decision (Option 1 vs. Option 2, and paid-provider vs. self-hosted) — a discussion/decision task, not an engineering task.
5. Only after 1–4: design and implement the AI-assisted pre-annotation workflow (Phase 3), the extended provenance schema, and the ground-truth/consensus pipeline (Phase 4), followed by real model evaluation (Phase 5) and full agreement/robustness analysis (Phase 6).
6. Separately and independently of 1–5: decide the dataset-size scope (645 vs. larger) before any `EXP-PAP-010`-series full-manifest work begins.

---

# AI-Assisted Annotation Methodology Review

Evaluating the proposed workflow: CLAHE crop → paid AI-assisted annotation → AI pre-label → human review → human correction → final human-validated label → ground truth → HSEmotion/ArcFace evaluation.

## 1. Is this methodologically defensible?

Yes, in principle — "AI-assisted annotation with mandatory human review" is a recognized and defensible annotation methodology, provided the human review is substantive (not rubber-stamping) and the process is documented transparently. It is defensible *conditionally*: the repository's own existing safeguards (never let AI auto-become ground truth, preserve raw human judgment, write-once final labels) are the right shape of guardrail and should carry forward into this new direction.

## 2. Could AI pre-labeling introduce bias?

Yes — this is the central risk, and it is well-documented in the project's own planning materials even though those materials predate the "paid AI-assisted annotation" instruction. Anchoring bias is explicitly named in `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §3.3: "three annotators shown the same AI suggestion are not three independent judgments anymore; measured inter-annotator agreement would be inflated by shared anchoring, not genuine consensus." The same logic applies here: a human reviewer shown a plausible-looking AI suggestion is measurably more likely to accept it than to independently derive the same answer from scratch, even when the suggestion is wrong — this is a well-established finding in human-AI collaboration research generally, not specific to this project.

## 3. How to prevent circular evaluation?

The single most important structural choice: **the model(s) used to generate the AI pre-label should not be the same model(s) later evaluated against the resulting ground truth** (or, if unavoidable, the overlap must be explicitly disclosed and ideally measured). Concretely for this project: if HSEmotion or ArcFace+LR is used to pre-fill annotations, then evaluating that same model's accuracy against the resulting "human-validated" labels is partially circular, because human correction behavior is itself biased toward the AI's suggestion (point 2). A clean alternative is to use a third, independent model/provider (e.g., a general-purpose paid LLM/VLM API, distinct from both evaluated candidates) for pre-annotation, keeping HSEmotion and ArcFace+LR purely as the *evaluated* systems, never the *annotation assistant*.

## 4. Should human annotation remain independent between annotators?

For the *first* independent judgment, yes — nothing in the supervisor's new instruction necessarily requires abandoning this. The existing architecture (separate servers or, per Phase 1's validated finding, a shared instance with `overlap=N` and content hidden until submission) already supports this and should be reused rather than redesigned.

## 5. Should both annotators see the AI pre-label?

This is a genuine trade-off, not a question with a single correct answer:
- **Both see it**: faster annotation, matches "AI-assisted" literally, but risks correlated anchoring across annotators, which would inflate measured human-human agreement in a way that doesn't reflect genuine independent consensus.
- **Neither sees it initially** (AI compared only after independent human labeling): preserves the cleanest "independent human judgment" claim, forfeits the speed benefit, and arguably stops being "AI-assisted annotation" in the sense the supervisor likely intends.

## 6. Should one annotator remain completely blind to AI suggestions?

This is a concrete, practical design the project's existing two-annotator infrastructure makes nearly free to implement: have Annotator A label with the AI suggestion hidden (preserving a clean independent-human baseline), and Annotator B label with the AI suggestion visible (measuring the AI-assisted workflow's actual behavior, including acceptance/correction rates). This directly reuses the existing isolated two-server architecture and would let the project measure the anchoring effect itself, empirically, rather than just worrying about it abstractly — turning a risk into a measured variable. This is an option worth the supervisor's explicit consideration, not a decision this audit makes.

## 7. What metadata/provenance must be stored?

At minimum: `ai_model` / `ai_model_version` / `ai_provider` (for a paid external API, record the exact model/version string and the query/call timestamp — API-backed models change silently over time, unlike pinned local packages); `ai_suggested_label` (preserved verbatim, never overwritten); `human_label` (the human's final choice); `human_accepted_ai` (bool: did the human keep the AI's suggestion unchanged); `human_correction_reason` (free text, optional); `annotator_identity` (real, resolvable — continuing this project's existing "never fake annotator IDs" principle); `review_started_at` / `review_completed_at` (to later analyze whether AI suggestions measurably sped up review, a legitimate research question this design enables). This extends, rather than replaces, the existing provenance conventions already established in `pilot_manifest.csv`/`ai_predictions.csv`.

## 8. How to report AI-assisted annotation in the thesis/paper?

Report explicitly and quantitatively, not just as a methods-section sentence: which model/provider generated pre-labels, on what fraction of images the human kept vs. changed the AI suggestion (this is itself a useful descriptive statistic), whether any annotator was kept blind to AI suggestions as a control (per point 6), and — critically — an explicit circularity statement disclosing whether the pre-annotation source overlaps with the evaluated models (per point 3), even if the answer is "no, we used a different model/provider for pre-annotation specifically to avoid this." A reviewer/examiner is likely to ask about exactly this; having the disclosure ready, with numbers, is stronger than silence.

---

*Generated by repository audit, 2026-10-01. No code, dataset, Label Studio configuration, or experiment data was modified in the course of this audit.*
