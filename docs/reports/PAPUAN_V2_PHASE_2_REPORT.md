# Phase 2 — EXP-PAP-004 Human Annotation Pilot

## Status

BLOCKED

## Objective

Establish a human-human agreement pilot: 150 CLAHE face crops, Primary annotator (A) labels all 150, Secondary annotator (B) labels a deterministic 75-image overlap subset, independently and blind to AI predictions — to support both human-human agreement analysis and (separately) AI-candidate-vs-human agreement, in order to select an annotation-assistant model (HSEmotion vs. ArcFace+LR).

**Important reframe vs. the task brief's assumed design**: this pilot's primary stated purpose per the repository (`experiments/EXP-PAP-004/metadata.json` title: "Papuan V2 pilot annotation-assistant agreement analysis") is to **select which AI model** (HSEmotion or ArcFace+LR) to use as the annotation assistant for the full workflow, by comparing each candidate's predictions against independent human labels. The human-human (A vs. B) agreement extension was added afterward as a secondary analysis. Both are blocked on the same missing input: real human labels.

## Current State

- **Infrastructure: complete.** Both the single-annotator (A, 150 images) and two-annotator-with-overlap (A=150, B=75 deterministic overlap, seed=100) designs are fully implemented, live-tested against two separate Label Studio server processes (port 8080 for A, port 8081 for B), and unit-tested.
- **Human labeling: not performed.** This is the actual, current blocker.

### Precise counts (verified by direct file inspection)

| File | Rows | Key finding |
|---|---|---|
| `pilot_manifest.csv` | 150 | 150-image pilot set, seed=42 |
| `ai_predictions.csv` | 300 (150 × 2 models) | Both candidates 150/150 "ok" |
| `human_labels.csv` | 150 | **0 of 150 have a non-empty `gt_label`** — fully blank template |
| `annotator_assignment.csv` | 150 | Annotator A: 150 assigned; Annotator B: 75 assigned (`overlap=true` for exactly 75 rows, verified by count) |
| `label_studio_export.csv` | 1 data row | Exactly **one** annotation exists in the real system: `frame_000008_face01`, label `Neutral`, confidence `Medium`, annotator `Annotator A`, exported 2026-09-19 |
| `annotator_progress.json` | — | `annotator_A_completed: 1`, `annotator_B_completed: 0`, `human_human_agreement: null`, `status: "not_computed"` |
| `label_studio_metadata.json` | — | Project A: `annotation_status: "not_started"`, `labeled_count: 0`, `remaining_count: 150` (stale relative to the 1 completed annotation shown elsewhere — see Known Issues) |

## Evidence

- `experiments/EXP-PAP-004/human_labels.csv` (150 blank rows, verified via `awk` count of non-empty `gt_label`: **0**)
- `experiments/EXP-PAP-004/annotator_assignment.csv` (75 `overlap=true` rows, verified by grep count)
- `experiments/EXP-PAP-004/annotator_progress.json`
- `experiments/EXP-PAP-004/label_studio_export.csv` (1 real annotation)
- `experiments/EXP-PAP-004/report.md` (explicit self-reported status: "PENDING_HUMAN_LABELING")
- `tools/papuan_v2/pilot_agreement_report.py` — enforces the block: refuses to run with any blank `gt_label`, confirmed by the project's own note that running it against the template raises `RuntimeError`
- `tools/papuan_v2/human_agreement_report.py` — the human-human agreement script; implemented and unit-tested but never run against real data
- `tests/test_pilot_agreement_metrics.py`, `tests/test_pilot_independence.py`, `tests/test_annotator_overlap.py`, `tests/test_label_studio_pilot.py` — 4 test files, verified passing in this audit (`pytest`, all green)

## Completed

- Deterministic task assignment (A=150, B=75 overlap, reproducible via documented seed).
- Isolated two-server annotator architecture (separate port/data-dir/DB/org for B), live-verified distinct from the throwaway Phase 1 validation environment.
- Real annotator-identity resolution (`client.get_users()`, not hardcoded strings) — confirmed working on the one real annotation that exists.
- Task-overlap PATCH applied without disturbing existing annotation content (before/after diff check passed).
- Agreement-computation code (both AI-vs-human and human-vs-human) implemented and unit-tested against synthetic fixtures.

## In Progress

- Nothing is actively in progress — the pilot is idle, waiting on human input. No automation can advance it further without a human performing the labeling.

## Blockers

- **The exact blocker**: a human must open each of 150 images and independently record a label in `human_labels.csv`'s `gt_label` column (Annotator A), and a second human must do the same for the 75-image overlap subset via the separate Annotator-B Label Studio server (port 8081). Currently only 1 of 150 (Annotator A) and 0 of 75 (Annotator B) are done.
- The repository's own `report.md` explicitly states the implementing assistant declined to fabricate these labels, citing the pilot's circularity/independence safeguards — this is a deliberate, documented refusal, not an oversight.

## Known Issues

- **Duplicate/conflicting records**: none found — `label_studio_export.csv` has exactly 1 data row, consistent with `annotator_progress.json`'s `annotator_A_completed: 1`.
- **Staleness inconsistency**: `label_studio_metadata.json` reports `annotation_status: "not_started"` / `labeled_count: 0`, which is stale relative to `annotator_progress.json`'s `annotator_A_completed: 1` (generated 15 minutes later, per timestamps: metadata.json `08:09:48`, annotator_progress.json `08:24:59`). This is a snapshot-staleness artifact (each file reflects the state at its own generation time), not a data-integrity bug — but a reader should not treat `label_studio_metadata.json` as live-accurate.
- **Blindness to AI predictions**: by design and by file separation (`human_labels.csv` has no column referencing `ai_predictions.csv`, and `tests/test_pilot_independence.py` specifically asserts the agreement-report code never cross-references the two), human labeling is structurally blind to AI predictions. This is enforced by code inspection tests, not just convention.
- **Export completeness unverified beyond 1 row**: because almost no real labeling has occurred, the export pipeline's behavior at full scale (150 or 75 rows, multiple annotators) is validated only via unit tests with synthetic fixtures, not via a real full run.
- No audit trail beyond the standard Label Studio annotation history mechanism (`created_at`, `completed_by`) and the CSV exports themselves — there is no separate append-only audit log.

## Outputs / Artifacts

- `experiments/EXP-PAP-004/{pilot_manifest.csv, ai_predictions.csv, human_labels.csv, annotator_assignment.csv, label_studio_metadata.json, label_studio_export.csv, annotator_progress.json, metadata.json, report.md}`

## Methodology Notes

The design correctly separates "independent human ground truth" from "AI candidate predictions" at the file and code level, and a unit test (`test_pilot_independence.py`) actively guards against accidental cross-contamination. This is a real, enforced methodological safeguard, not just a stated intention.

## Next Actions

1. A human annotator (not the implementing assistant) must complete `human_labels.csv` for all 150 images (Annotator A), and a second human must complete the 75-image overlap set via the Annotator-B server (port 8081).
2. Run `uv run python tools/papuan_v2/pilot_agreement_report.py` to generate real `agreement_metrics.json`, confusion matrices, and overwrite `report.md`.
3. Run `uv run python tools/papuan_v2/human_agreement_report.py` for human-human agreement once both A and B have completed their 75-image overlap.
4. A human (supervisor or researcher) reviews the resulting metrics and records the EXP-PAP-004 annotation-assistant selection decision in `docs/EXPERIMENT.md` — this is explicitly a human decision, not automated by the script.
