# Phase 6 — Agreement & Robustness Analysis

## Status

BLOCKED (code exists and is unit-tested; no real-data run has ever happened)

## Objective

Support human-human agreement, AI-human agreement, HSEmotion-human and ArcFace-human agreement, Original-vs-CLAHE comparison, error analysis, confusion matrices, per-class performance, macro/weighted F1, and accuracy.

## Current State

| Analysis | Code exists? | Unit-tested? | Run on real data? |
|---|---|---|---|
| AI-vs-human agreement (accuracy, macro-F1, Cohen's kappa, confusion matrix, confidence-vs-correctness) | Yes — `tools/papuan_v2/pilot_agreement_report.py` | Yes — `tests/test_pilot_agreement_metrics.py` (passing) | **No** — blocked on `human_labels.csv` |
| Human-human agreement (raw agreement, Cohen's kappa, confusion matrix, per-class agreement, disagreement list) | Yes — `tools/papuan_v2/human_agreement_report.py` | Implemented per `docs/EXPERIMENT.md`'s own description ("implemented and unit-tested") — dedicated test file not independently located by filename in this audit; functionality is exercised indirectly via the agreement-report module's shared helpers in `tests/test_annotator_overlap.py` | **No** — blocked on both annotators completing the 75-image overlap (currently 0/75 for Annotator B) |
| Original vs. CLAHE comparison | **No code found** | N/A | No — flagged only as a future experiment ("E3") in proposal docs, not started |
| Fleiss' kappa (for future 3-annotator consensus) | **No code found**; explicitly flagged as an open dependency decision (`statsmodels` vs. hand-rolled) in `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §8 | N/A | No |
| Per-class distribution / per-class agreement | Designed into `annotator_progress.json`'s/`dashboard_snapshot.json`'s proposed schema; `human_agreement_report.py` claims per-class agreement output | Partially, via the same agreement-report tests | No |

## Evidence

- `tools/papuan_v2/pilot_agreement_report.py`, `tools/papuan_v2/human_agreement_report.py`
- `tests/test_pilot_agreement_metrics.py` (144 lines, passing)
- `tests/test_annotator_overlap.py` (319 lines, passing — covers identity resolution and overlap mechanics more than agreement math itself)
- `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §8 (Fleiss' kappa flagged as an unresolved future dependency)
- `pyproject.toml` — no `statsmodels` dependency present, confirming Fleiss' kappa is not yet implemented or decided

## Completed

- Pairwise (2-annotator) agreement metric implementations, unit-tested against synthetic data.
- AI-vs-human metric implementations (accuracy, macro-F1, Cohen's kappa, confusion matrix, confidence-vs-correctness), unit-tested.

## In Progress

- Nothing; all of this is idle pending real data.

## Blockers

- Same root blocker as Phase 2/5: no real human labels exist yet for either the 150-image full set (Annotator A, 1/150 effectively via the one real annotation) or the 75-image overlap (Annotator B, 0/75).

## Known Issues

- Original-vs-CLAHE comparison has **zero code**, not just zero results — this is a genuine gap, not merely "not yet run." It would need new prediction runs against `data/papuan_v2/faces/` (the non-CLAHE crops already on disk) and a new comparison script; nothing currently reads `data/papuan_v2/faces/` for prediction purposes.
- Fleiss' kappa (needed once 3 annotators exist in the full workflow) has no implementation and an unresolved dependency choice — flagged in the plan but not decided or coded.
- "Per-class performance" exists as a schema field name in design documents (`dashboard_snapshot.json`'s proposed `per_class_distribution`/`per_class_agreement`) but this file does not exist on disk anywhere.

## Outputs / Artifacts

- None (all metric outputs are gated behind the human-labeling blocker).

## Methodology Notes

The 2-annotator agreement code (Cohen's kappa, raw agreement) is a reasonable foundation but was explicitly designed only for N=2; moving to N=3 annotators (per the full-workflow plan) requires Fleiss' kappa or an equivalent multi-rater statistic, which is an acknowledged, unresolved gap — not an oversight unique to this audit.

## Next Actions

1. Unblock via Phase 2 (real labels).
2. Run both agreement scripts against real data once available.
3. If/when the full 3-annotator workflow is implemented, resolve the Fleiss' kappa dependency decision before relying on any multi-rater agreement number.
4. If Original-vs-CLAHE comparison is still wanted, scope it as new work — no existing code can be reused directly for this specific comparison.
