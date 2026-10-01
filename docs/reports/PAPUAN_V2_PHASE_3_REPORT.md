# Phase 3 — AI-Assisted Annotation

## Status

NOT IMPLEMENTED

## Objective

Implement the supervisor's new direction: AI pre-annotation inside Label Studio, followed by mandatory human review/correction, producing a human-validated final label (AI output is never auto-accepted as ground truth).

## Current State

**This phase does not exist in the repository.** A repo-wide search for ML-backend / pre-annotation / paid-AI-provider terminology (`ML backend`, `pre-annotation`, `pre-label`, `openai`, `anthropic api`, `gpt-4`, `vlm`, `llm`) across `tools/papuan_v2/`, `experiments/EXP-PAP-004/`, `docs/EXPERIMENT.md`, and `docs/proposal/` returned **zero implementation hits** — the only hits were unrelated literature-review citations in `docs/proposal/research/STATE_OF_ART_AND_GAP.md` discussing GPT-4o in the context of a *different* published study, not this project's own pipeline.

`pyproject.toml` was checked for dependencies that would indicate this phase exists: no `openai`, `anthropic`, or similar paid-AI-SDK packages are present. Only `label-studio>=1.23.0` and `label-studio-sdk>=2.0.18` are installed — i.e., Label Studio Community Edition's own SDK, nothing else.

### What exists that is adjacent but distinct

- `experiments/EXP-PAP-004/ai_predictions.csv` — this is **not** AI-assisted annotation in the "pre-label, then human corrects in Label Studio" sense. It is a static CSV of two candidate models' (HSEmotion, ArcFace+LR) predictions, generated offline via `tools/papuan_v2/run_ai_predictions.py`, kept entirely separate from the Label Studio labeling interface and never imported into Label Studio as `task["predictions"]`. The design plan (`docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §3.3) explicitly notes "currently always empty since the pilot never imports predictions."
- Label Studio's native `task["predictions"]` mechanism — confirmed present in the API/payload structure (inspected during Phase 1 validation) and structurally capable of carrying pre-annotations, but **never used or populated** by any script in this repository.
- `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §3.3 discusses, at the design level only, "AI prediction shown as a pre-filled suggestion" (Option 2) vs. "AI prediction hidden from annotators" (Option 1), and explicitly recommends Option 1 (hidden) as the default for the *already-planned* AI-model-selection pilot — this recommendation predates, and is in tension with, the supervisor's new "paid AI-assisted annotation" direction, which implies pre-filled suggestions (Option 2 in the plan's own framing). This is a live open methodological question, not a decided one (see "What would need to be added").

## Evidence

- Grep results (repo-wide, this audit): no AI pre-annotation/ML-backend code found.
- `pyproject.toml`: no paid-AI SDK dependency.
- `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §3.3 ("AI-prediction visibility to annotators — the required methodological decision") — explicitly flagged as unresolved and NOT this plan's decision to make.
- `tools/papuan_v2/run_ai_predictions.py` — exists, generates predictions, but writes to a standalone CSV, not into Label Studio's prediction import API.

## Completed

- Nothing toward AI-assisted annotation specifically. (The offline AI-candidate-comparison pipeline for EXP-PAP-004 is a prerequisite/adjacent piece of infrastructure, documented in Phase 0/Phase 2, but is not the same thing as in-tool AI pre-annotation.)

## In Progress

- Nothing.

## Blockers

- **No implementation exists.** This is a greenfield phase. It is also blocked, logically, on the supervisor's methodological choice between Option 1 (AI hidden, annotators label blind, AI compared after the fact) and Option 2 (AI pre-fills a suggestion in Label Studio, human corrects it) — the repository's own planning document flags this exact choice as open and refuses to default it silently.
- EXP-PAP-004 (Phase 2) itself is unresolved, which — per the plan's own dependency ordering (`EXP-PAP-011` depends on "EXP-PAP-004's assistant-selection decision") — blocks selecting *which* AI model would even generate pre-annotations for a full-scale AI-assisted workflow.

## Known Issues

- None (there is no code to have issues).

## Label Studio Deployment Type

- **Community Edition**, self-hosted, run as local server processes (not Docker; no `docker-compose.yml`/`Dockerfile` found in the repo). Version pinned: `label-studio>=1.23.0`, `label-studio-sdk>=2.0.18` (`pyproject.toml`).
- Current pilot runs **two separate local server processes** (ports 8080 and 8081) for annotator isolation, plus a now-torn-down throwaway validation server (port 8090, Phase 1).
- No Enterprise features are configured or referenced anywhere in the repo (no SSO, no Enterprise ML-backend config, no licensed-feature flags).

### What would require paid/Enterprise functionality vs. what is achievable self-hosted

| Capability | Self-hosted Community (achievable now) | Requires paid/Enterprise or external service |
|---|---|---|
| Pre-filling `task["predictions"]` with a model's output so annotators see a suggestion | **Yes** — this is a native Community-edition API feature (predictions import), confirmed present in the task payload structure during Phase 1 testing; just never used | No |
| Running a custom ML backend that auto-generates predictions on task creation (Label Studio's "ML Backend" integration) | **Yes, self-hostable** — Label Studio Community supports registering an external ML backend over HTTP; this is not an Enterprise-only feature | No, but requires building/hosting the backend service yourself |
| Calling a *paid* external AI annotation provider (e.g., a commercial LLM/VLM API) to generate the pre-labels | Achievable as a plain external script that writes into Label Studio's prediction-import API (same mechanism as above) | The "paid" part is the external API cost (e.g., an LLM provider's usage fees), not a Label Studio license — Label Studio itself does not need to be Enterprise for this |
| Role-based, enforced annotator isolation (true "Annotator" role separate from "Owner") within one project | **No** — confirmed in Phase 1 validation: Community 1.23.0's `OrganizationMember` has no role field; isolation is currently achieved by running separate server processes, a workaround | This is the one capability that plausibly requires Enterprise (role-based access control is marketed as an Enterprise feature) — not independently confirmed against Enterprise's actual feature list in this audit; marked UNKNOWN below |
| Reviewer/QA workflow UI (compare multiple annotators' labels, accept/reject) | Partially — Data Manager can show per-task annotation counts and content to users with sufficient access; a dedicated "Review" stage UI is more polished in Enterprise | UNKNOWN whether Community's review UI is sufficient for this project's adjudication needs — not evaluated in this audit since no review workflow has been built yet |

**UNKNOWN**: Whether Label Studio Enterprise's specific "Annotator" role (if it exists as a precise feature) would fully solve the isolation problem Phase 1 worked around with separate servers. Not verified against Enterprise's actual documentation/feature matrix in this audit — would need direct comparison against Enterprise licensing docs, which were not available/in-scope here.

## Outputs / Artifacts

- None.

## Methodology Notes

See the dedicated "AI-Assisted Annotation Methodology Review" in `docs/reports/PAPUAN_V2_CURRENT_STATE.md` for the full trade-off discussion (bias risk, circularity, blind-vs-visible annotator design, provenance requirements).

## Next Actions

1. Supervisor/researcher must explicitly decide: AI-hidden-then-compared (Option 1) vs. AI-pre-filled-suggestion-then-corrected (Option 2) — these are methodologically different experiments, not an implementation detail.
2. Decide which AI model(s) would generate the pre-annotations — likely gated on EXP-PAP-004's existing (not yet run) assistant-selection pilot, since that pilot was explicitly designed to answer "which model to use as the annotation assistant."
3. Decide whether "paid AI-assisted annotation" means (a) an external paid LLM/VLM API call that writes into Label Studio's existing `predictions` import mechanism (buildable on Community edition, confirmed), or (b) a Label Studio Enterprise ML-backend/licensed feature (not yet investigated against Enterprise's actual feature set).
4. Only after those decisions: design + implement the pre-annotation import step, the human-review-must-override-AI UI/workflow, and the provenance schema (`ai_model`, `ai_model_version`, `prediction_timestamp`, `confidence_score`, `was_ai_suggested: bool`, `human_overrode_ai: bool`) — none of which currently exists in any CSV/JSON schema in this repo.
