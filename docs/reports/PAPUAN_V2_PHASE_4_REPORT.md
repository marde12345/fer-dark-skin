# Phase 4 — Human-Validated Ground Truth

## Status

NOT STARTED

## Objective

Produce a final, human-validated ground-truth dataset (`final_labels.csv` or equivalent) with full provenance, where any AI contribution has been explicitly reviewed/corrected by a human and is never auto-promoted to ground truth.

## Current State

No ground-truth dataset exists yet, at any scale.

- `human_labels.csv` (the would-be ground-truth source for the 150-image pilot) is 150/150 blank (see Phase 2 report).
- No `final_labels.csv`, `consensus.csv`, or `adjudication_log.csv` exist anywhere in the repository — these are all still design-only, described in `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §4.3–4.4, §7, as proposed schemas for a future `EXP-PAP-01x` phase that has not begun implementation.
- No consensus-computation code exists for real data. A **pure function** prototype (`compute_consensus()`) exists in `tools/papuan_v2/validation/consensus_fixture.py`, built and unit-tested during Phase 1, but it operates only on synthetic fixture data (3 hand-picked examples + the live 3-annotation fixture result) — it has never been pointed at real annotation data and there is no production script that calls it against `experiments/EXP-PAP-004/` or any other real experiment directory.
- No adjudication mechanism exists for real data (design-only, §7.4 of the plan document).

## Evidence

- `experiments/EXP-PAP-004/human_labels.csv` — 150 blank rows (verified).
- `tools/papuan_v2/validation/consensus_fixture.py` — pure, synthetic-fixture-only consensus function; tested via `tests/test_phase1_validation_fixture.py`.
- `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §4.3 (`consensus.csv` schema, proposed not implemented), §4.4 (`final_labels.csv` schema, proposed not implemented), §7 (consensus/adjudication design), §12 (explicit list of files "to be created" when implementation is approved — none of which exist on disk).
- Repository-wide search found no `final_labels.csv`, `consensus.csv`, or `adjudication_log.csv` file anywhere under `experiments/` or `data/`.

## Completed

- The **conceptual schema design** for `final_labels.csv`, `consensus.csv`, and `adjudication_log.csv`, including explicit provenance fields (`ai_model`, `ai_model_version`, `annotator_A/B/C` with per-annotator attribution preserved forever, `final_label_source` enum distinguishing `consensus` vs. `adjudication`), and an explicit non-overwrite guarantee pattern (mirrors `human_labels.csv`'s existing "refuses to overwrite without `--force`" convention). This is design work only, not executable code against real data.
- A pure majority-vote consensus function, validated against worked examples and synthetic fixture data (Phase 1).

## In Progress

- Nothing. This phase has not started implementation.

## Blockers

- **Upstream dependency**: Phase 4 (consensus/ground truth) structurally depends on Phase 2 (real human labels existing) and, per the supervisor's new direction, on Phase 3 (AI-assisted pre-annotation) being resolved first, since the ground-truth workflow now needs to incorporate "AI suggestion → human verification → correction → final label" rather than purely independent human labeling. Neither prerequisite is complete.
- No decision yet on majority-vote vs. other consensus rules being final (the plan recommends majority vote for N=3 but flags it as "a recommendation, not a decision" pending supervisor approval).

## Known Issues

- The proposed `final_labels.csv` schema was designed for the *old* 2-annotator-then-3-annotator-consensus architecture (independent human judgments, AI compared afterward). It has **not** been revisited against the supervisor's new "AI pre-annotation → human review" direction, which implies additional needed fields (e.g., `ai_suggested_label`, `human_accepted_ai: bool`, `human_correction_reason`) that do not appear anywhere in the current schema design. This is a real gap between the existing design document and the new instruction, not yet reconciled in any document.

## Outputs / Artifacts

- None.

## Methodology Notes

The existing design (pre-dating the supervisor's new direction) is explicit that "the AI pre-label should not automatically become ground truth" and enforces this procedurally (write-once guards, human-only adjudication, no AI column in the adjudication log at all "by design, so there's no accidental path for `ai_prediction` to leak into a `no_majority` resolution"). This principle is compatible with the supervisor's new requirement and does not need to be re-derived — but the concrete mechanics (schema, review UI, override-tracking) need to be extended to represent "AI suggested X, human reviewed and kept/changed to Y," which the current schema does not capture.

## Next Actions

1. Do not implement `final_labels.csv`/`consensus.csv` against real data until Phase 2's human labels exist for at least the pilot.
2. Revise the `final_labels.csv`/consensus schema to explicitly represent AI-suggested-vs-human-confirmed/corrected, once Phase 3's methodology (Option 1 vs. Option 2 pre-annotation visibility) is decided.
3. Only then adapt `tools/papuan_v2/validation/consensus_fixture.py`'s logic (currently fixture-only) into a production script reading real annotation exports.
