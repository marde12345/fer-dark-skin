# Phase 5 — Model Evaluation

## Status

BLOCKED

## Objective

Evaluate HSEmotion and ArcFace+LogisticRegression predictions against human-validated ground truth, with metrics (accuracy, macro/weighted F1, Cohen's kappa, confusion matrix) and an explicit check for leakage/circularity.

## Current State

### HSEmotion

- Input dataset: 150-image CLAHE pilot subset (`data/papuan_v2/pilot/images/`).
- Preprocessing: CLAHE Strategy B (same as all pilot inputs).
- Model/version: `enet_b0_8_best_vgaf`, package `hsemotion-onnx==0.3.1` (pinned, recorded in `experiments/EXP-PAP-004/metadata.json`).
- Prediction output: `experiments/EXP-PAP-004/ai_predictions.csv`, 150/150 rows with `status=ok`.
- Evaluation metrics: **not computed** — `tools/papuan_v2/pilot_agreement_report.py` implements accuracy/macro-F1/Cohen's kappa/confusion-matrix computation and is unit-tested (`tests/test_pilot_agreement_metrics.py`, passing), but refuses to run until `human_labels.csv` is fully populated (currently 0/150).
- Ground-truth source: intended to be the independent human pilot labels (`human_labels.csv`) — not yet available.

### ArcFace + Logistic Regression

- Face embedding generation: `buffalo_l/w600k_r50` (InsightFace 1.0.1), via direct `ArcFaceONNX.get_feat()` (fixed to avoid re-detection on crops — see Phase 0 report Known Issues).
- Classifier: pre-trained multinomial `LogisticRegression`, artifact `tools/realtime_demo/artifacts/arcface_lr_demo_model.joblib`.
- Training dataset: **legacy** `manual_labels_export.csv`, trained via `tools/train_arcface_classifier.py` (project code "R6"). **Not retrained on any Papuan V2 data** — stated explicitly in `metadata.json`.
- Evaluation dataset: same 150-image CLAHE pilot subset as HSEmotion.
- Preprocessing: CLAHE crop input, but note the classifier's *training* data went through full InsightFace detect+landmark-align, while *inference* here uses a direct, unaligned embedding path — an explicitly documented distributional mismatch (see caveat in Phase 0 report).
- Prediction output: `experiments/EXP-PAP-004/ai_predictions.csv`, 150/150 rows `status=ok` (after the re-detection bugfix; an earlier, superseded 100/150 run is preserved only as a debugging note, never used for agreement).
- Metrics: **not computed**, same blocker as HSEmotion.

## Evidence

- `experiments/EXP-PAP-004/metadata.json` (`ai_models` block — full model/version/training-data details for both candidates)
- `experiments/EXP-PAP-004/ai_predictions.csv` (301 lines, 300 data rows)
- `tools/papuan_v2/pilot_agreement_report.py` (evaluation logic)
- `tests/test_pilot_agreement_metrics.py` (144 lines, passing — tests the metrics-computation logic against synthetic data, not real pilot data)
- `tools/train_arcface_classifier.py`, `tools/extract_arcface_embeddings.py` (legacy classifier training, pre-dates Papuan V2)
- Broader legacy evaluation tooling found at repo root: `tools/evaluate_arcface_vs_hsemotion.py`, `tools/analyze_arcface_errors.py` — these predate Papuan V2 and operate on the legacy dataset, not papuan_v2 data; not audited in depth here as they are out of this project's current scope, but their existence shows evaluation methodology precedent in this codebase.

## Completed

- Both candidate models' predictions generated and recorded with full provenance (model name, package version, class set, success/exclusion counts).
- Evaluation-metrics code written and unit-tested against synthetic data.

## In Progress

- Nothing; evaluation is fully blocked pending ground truth.

## Blockers

- **No ground truth exists yet** (Phase 2/Phase 4 blocker cascades directly here). `pilot_agreement_report.py` has a hard runtime guard (`RuntimeError`) preventing it from running against incomplete `human_labels.csv` — this is enforced in code, not just policy.

## Known Issues — Leakage / Circularity Risk Assessment

- **No leakage currently possible, by construction, for the pilot's intended comparison** (AI predictions vs. independent human labels) — `human_labels.csv` has no AI-derived column, and `tests/test_pilot_independence.py` specifically asserts the agreement-report code's source never references `ai_predictions.csv` when building ground truth.
- **Latent risk for the *new* supervisor-directed workflow**: if AI-assisted pre-annotation (Phase 3, not yet implemented) is added and the *same* models (HSEmotion/ArcFace+LR) that will later be evaluated are also used to pre-fill the human annotator's suggestion, this would constitute exactly the circularity the task brief warns against ("HSEmotion or ArcFace should not be used as the source of ground truth if those same models are later being evaluated against that ground truth"). **This is not a hypothetical risk already resolved by the repo — it is a real design decision not yet made**, since Phase 3 does not exist yet and no document commits to which model(s), if any, would generate AI pre-annotations for the human-review workflow. If the eventual ground-truth-generation pre-annotation model is the same as (or highly correlated with) one of the two models under evaluation, the evaluation numbers for that model would be inflated/biased toward agreement with its own suggestions (anchoring bias), even if the human "corrects" the label, because correction behavior itself is known to be biased toward accepting a plausible-looking default.
- **Person-identity leakage**: not evaluated in this audit — the pilot sources all 645 crops from a single source video (`pesta_babi.mp4`), which likely means the same individuals appear multiple times across frames. No train/test split or person-disjoint partitioning exists or is needed yet (there is no "training" happening within papuan_v2 — the ArcFace LR classifier was trained entirely on legacy data, not Papuan V2 frames), so this is currently moot for the *evaluation* pipeline, but would become relevant if Papuan V2 data is ever used to retrain either model. Flagged as UNKNOWN / not currently applicable rather than resolved.
- **Train/test contamination for ArcFace+LR**: the classifier was trained on **legacy** data, evaluated on **Papuan V2** pilot data — these are disjoint datasets, so no contamination in the classic sense. However, the distributional mismatch (aligned training embeddings vs. unaligned inference embeddings, see Phase 0) is a different kind of validity concern, already documented as a caveat in `metadata.json`.

## Outputs / Artifacts

- `experiments/EXP-PAP-004/ai_predictions.csv` (predictions, no metrics yet)

## Methodology Notes

The existing independence safeguards (`test_pilot_independence.py`) are a genuine, code-enforced precedent this project can reuse: if the AI-assisted pre-annotation workflow (Phase 3) is built, an equivalent test should assert that the pre-annotation-generation code path is structurally decoupled from (or explicitly documented as overlapping with) whichever model(s) are later evaluated.

## Next Actions

1. Unblock by completing Phase 2 human labeling.
2. Run `pilot_agreement_report.py` to produce real metrics for both candidates.
3. Before building Phase 3 (AI-assisted pre-annotation), explicitly decide and document whether the pre-annotation model(s) overlap with HSEmotion/ArcFace+LR (the models under evaluation) — if so, design around it (e.g., use a third, non-evaluated model/provider for pre-annotation, or clearly report the circularity caveat in any resulting thesis/paper).
