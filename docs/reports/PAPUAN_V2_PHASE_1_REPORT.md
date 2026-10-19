# Phase 1 — Annotation Architecture Validation

## Status

DONE (as a narrow architecture-isolation validation). This is NOT a validation of the full AI-assisted annotation workflow — only of one specific question: whether a shared Label Studio instance can serve 3 annotators without one seeing another's submitted labels before they submit their own.

## Objective

Empirically verify, on a throwaway/synthetic project, whether Label Studio Community 1.23.0's shared-instance, `task.overlap=N` mechanism actually isolates annotators from each other's submitted annotations before they submit their own — a prerequisite decision for the proposed full (~600-image, 3-annotator) workflow in `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §3.1.

## Current State

This phase exists and was genuinely executed against an isolated throwaway environment, not merely documented as planned. Verified from the repository:

- **Separate server**: port **8090** (vs. the real pilot's 8080/8081), separate `--data-dir` (outside the repo, under a `.claude/jobs/.../tmp/` path), separate SQLite DB, separate organization.
- **Synthetic fixture images**: 3 generated with numpy/opencv (colored blocks + noise + baked-in text labels "FIX01/02/03"), stored outside the repo, never copied from `data/papuan_v2/`.
- **Test users**: 4 — `owner@phase1-validation.test` (id 1, inspector), `annotator-a@phase1-validation.test` (id 2), `annotator-b@phase1-validation.test` (id 3), `annotator-c@phase1-validation.test` (id 4). Created via Django shell, throwaway tokens.
- **Test project**: id 1, title `"PHASE1-VALIDATION (throwaway, not pilot)"`.
- **Code**: `tools/papuan_v2/validation/fixture_config.py`, `export_fixture_annotations.py`, `consensus_fixture.py`; output `tools/papuan_v2/validation/fixture_export.csv` (the actual 3-row exported result, kept as evidence).
- **Tests**: `tests/test_phase1_validation_fixture.py` — 20 tests, confirmed passing in this audit (full suite run: 83/83 total tests across all papuan_v2-related test files passed, including these 20).

## Evidence

- `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md`, "Phase 1 Validation Results" section (lines 432–544) — the primary write-up.
- `docs/EXPERIMENT.md` lines 602–612 ("Papuan V2 Full Workflow — Phase 1 Architecture Validation").
- `tools/papuan_v2/validation/` (4 files: `fixture_config.py`, `export_fixture_annotations.py`, `consensus_fixture.py`, `fixture_export.csv`).
- `tests/test_phase1_validation_fixture.py` (269 lines, 20 tests, all passing — verified by running `pytest` in this audit).

## Completed

- **Role-permission behavior confirmed**: Community 1.23.0 has no enforced "Annotator" role distinct from "Owner" at the `OrganizationMember` level (confirmed by source reading AND live behavior).
- **Bilingual label config**: PASS — English/Indonesian pairs verified live on the fixture project.
- **AI-visibility result**: PASS — no AI-derived field/value anywhere in the config or task payload (there was no AI prediction to hide in this fixture; this confirms the mechanism, not that it was exercised with a real prediction present).
- **Overlap=3 at project creation**: PASS — setting `maximum_annotations=3` before task import gives every task `overlap=3` automatically (a lower-friction finding vs. the pilot's post-hoc PATCH approach).
- **Critical visibility test — co-annotator annotations NOT visible pre-submission**: empirically confirmed via direct, authenticated API calls (`GET /api/projects/1/next` with each annotator's own token) — before submitting, annotators B and C saw `"annotations": []`, `"predictions": []`, `"drafts": []`. Only a non-content signal (`total_annotations` count) was visible. Separately confirmed `GET /api/tasks/1/` and `/api/tasks/1/annotations/` returned 404 for a non-owner token.
- **Identity/export result**: PASS — all 3 distinct annotations correctly attributed to their real submitter via `completed_by`, exported in a deterministic, task-order-independent fashion.
- **Consensus fixture**: PASS — pure majority-vote function matched all of the brief's worked examples plus the real fixture data (3-way distinct → `no_majority`, `adjudication_required=True`).
- **Pilot preservation verified, before and after**: MD5 checksums of `pilot_manifest.csv`, `human_labels.csv`, `ai_predictions.csv` unchanged; Task 1's existing annotation (`Neutral`/`Medium`) byte-identical; ports 8080/8081 project/task state unchanged; legacy data directory file counts unchanged (596/596/24183/2).

## In Progress

- Nothing; this phase is marked complete in its own scope.

## Blockers

- None for this narrow validation. It does not block or unblock anything downstream by itself — the real blocker for proceeding to the full workflow is EXP-PAP-004 (Phase 2), which this phase's own "Recommendation for the next phase" section explicitly states.

## Known Issues

- **Not independently re-verified in this audit.** This audit did not re-run the live Label Studio server interactions (port 8090 environment was ephemeral/local and is not necessarily still running); the conclusions above are taken from the repository's own detailed write-up plus the fact that the 20 associated unit tests pass today. The *unit-test* claims are independently verified; the *live API* claims (e.g., actual `GET /api/projects/1/next` responses) are evidenced only by the document's own transcription, not re-executed live in this audit.
- **Self-acknowledged gap**: no real-browser visual confirmation was performed — all testing was via direct API calls. The document itself flags this as a cheap, recommended (not blocking) follow-up.
- **Self-acknowledged gap**: whether annotators need explicit per-project `ProjectMember` records (vs. only organization-level membership) was not exercised, since all API calls addressed the project by known ID rather than via a "my projects" discovery call.
- No evidence the validation "accidentally touched the real pilot" — the before/after checksum table is the explicit evidence against this, and is corroborated by the separate port/data-dir/DB/org design.

## Outputs / Artifacts

- `tools/papuan_v2/validation/fixture_export.csv`
- `tests/test_phase1_validation_fixture.py` (20 passing tests)

## Methodology Notes

This phase validates an **infrastructure/isolation** question only ("can one shared Label Studio project safely serve 3 annotators without leaking content"). It does **not** validate anything about AI-assisted pre-annotation, bias, or ground-truth construction — those are separate, still-open questions (see Phase 3 report). Conflating "Phase 1 validated" with "the AI-assisted annotation methodology is validated" would be a misreading of the repository's own scope statement.

## Next Actions

- No action required to re-run Phase 1 itself.
- Per the document's own recommendation: before real annotators are recruited for any shared-instance deployment, perform one real-browser login as a throwaway account to visually confirm the API-level visibility finding (cheap, not blocking).
- Treat this phase as informing — not substituting for — the still-unresolved methodology decisions in Phase 3 (AI-assisted annotation) and Phase 4 (ground truth).
