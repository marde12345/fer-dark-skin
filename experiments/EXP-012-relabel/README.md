# EXP-012 — Manual Relabeling of the 227 Legacy Crops (Round 2)

Status: **real project ready for manual annotation** — `EXP-012 Legacy 227 Relabel (Round 2)`, project id 4 on the local Label Studio (http://localhost:8080/projects/4/data), 227 unique tasks, 0 annotations (2026-10-25). The 6-crop sample project (id 3) is for checking only. No model is retrained in this step.

Full-project check (2026-10-25): 227 tasks with 227 unique `image_id`s matching the legacy crop set exactly; every original and overlay URL returned HTTP 200 and is byte-identical to the file on disk; landmark status/source match `landmark_sources.csv` (reviewed 21, proposal 131, missing 75); label config identical to `relabel_config.LABEL_CONFIG`; task data contains only the allowed fields; EXP-PAP-004 (id 2) and the sample project (id 3) unchanged.

## Purpose

Per Pak Fadhil's instruction, relabel the existing dataset manually and later retrain the model. This round relabels the 227 legacy crops (`data/1408-1010-intermediate/faces/`), which contain all 135 crops of the EXP-007/010/011 evaluation subset.

## What is shown to the annotator

- The **original crop**, unchanged.
- A **landmark overlay**: an enlarged copy of the crop with the 42 eyebrow (17–26), eye (36–47), and mouth (48–67) points, plus a banner and a task note stating the overlay status:
  - `REVIEWED` — human-reviewed CVAT landmarks (EXP-PAP-005): 21 crops
  - `UNREVIEWED PROPOSAL` — InsightFace proposals (EXP-PAP-005) or delivery-package 42-point initial landmarks mapped back to crop coordinates: 131 crops
  - `NO LANDMARKS` — no existing landmarks: 75 crops (none were generated)
- Labels: Neutral, Happy, Sad, Surprise, Fear, Angry, Disgust, **Ambiguous** (required); confidence (optional); "Was the overlay usable?" Usable / Unreliable / Not used (optional); free-text note.
- Never shown: round-1 labels, model predictions, or model names.

Landmarks are a visual aid only. Labels are a human judgment from the face; nothing is inferred from coordinates. Even "reviewed" overlays can be poor on blurry or profile faces (e.g. `frame_000022_face11`), so annotators should mark such overlays Unreliable and label from the original crop.

## Files

| Path | Role |
|---|---|
| `tools/exp012/relabel_config.py` | Label interface, landmark source priority, task builder, export mapping (no network calls) |
| `tools/exp012/render_overlays.py` | Renders overlays to `data/exp012/overlays/` (git-ignored, regenerable) and writes `landmark_sources.csv` |
| `tools/exp012/setup_label_studio_relabel.py` | Creates the separate project (`--sample` or `--all`), connects image folders, imports tasks (idempotent) |
| `tools/exp012/export_relabel_labels.py` | Exports to `labels_round2.csv`; refuses to overwrite without `--force` |
| `tests/test_exp012_relabel.py` | Server-free tests |
| `experiments/EXP-012-relabel/landmark_sources.csv` | Landmark status/source per crop (227 rows) |

Round-1 labels (`manual_labels_export.csv`, `EXP-PAP-004/human_labels.csv`) and all earlier experiment outputs are only read, never written. Round-2 labels go to `experiments/EXP-012-relabel/labels_round2.csv`, one row per annotation, with `label_round=2`, annotator, timestamp, and landmark status/source.

## Sample verification (2026-10-25)

Run on a temporary Label Studio 1.23.0 server (port 8097, scratch data directory), not on the main instance:
- 6 sample crops (2 per landmark status) imported into `EXP-012 SAMPLE VERIFY (do not label)`; re-running imported 0 duplicates.
- Every task's data had exactly the allowed fields; all 12 original/overlay URLs returned HTTP 200 (JPEG/PNG).
- A test annotation (Ambiguous, overlay Unreliable) exported to a correct round-2 row; re-export without `--force` was refused.
- Inverse delivery transform checked: 0.0000 px difference on all 40 crops that also have EXP-PAP-005 proposals. All 227 original crops are byte-identical to the 2026-10-24 backup.

## How to start labeling

Run from the main checkout (where `data/` lives), with your Label Studio server on port 8080 (started per `tools/papuan_v2/README_label_studio.md`, document root = repo root).

1. Render overlays (already done once; safe to re-run):
   `uv run python tools/exp012/render_overlays.py`
2. Set your key (never commit it):
   `export LABEL_STUDIO_API_KEY=<your token>`
3. Create the sample project and check it in the browser at http://localhost:8080:
   `uv run --group labeling python tools/exp012/setup_label_studio_relabel.py --sample`
4. **Only after the sample looks right**, create the real project:
   `uv run --group labeling python tools/exp012/setup_label_studio_relabel.py --all`
5. After labeling, export:
   `uv run --group labeling python tools/exp012/export_relabel_labels.py`

## Open items (not done in this step)

- Who labels round 2, and the second-annotator overlap (planned ≥20%, stratified by brightness group).
- Landmarks for the 75 crops without any are not generated yet.
- Retraining (ArcFace + LR with existing settings) and the Dark vs Medium-Dark re-evaluation come after labeling.
- Consent/provenance of the source film remains unresolved; identity leakage across distant frames is not controlled by the existing 3-frame grouping.
