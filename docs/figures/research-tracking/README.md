# Research Tracking Figures — FER Thesis

Visual package for tracking the FER fairness thesis: methodology diagrams, experiment results, and research status. Every plotted number is read from a committed or saved experiment output; nothing is estimated. `validate_figures.py` re-derives all plotted values from the sources (99 checks, 0 mismatches at generation).

Open `index.html` for the dashboard (milestones, findings, limitations, figure inventory).

## Two evaluation protocols — never mixed in one panel

| | Protocol A | Protocol B |
|---|---|---|
| Experiments | EXP-010 (models), EXP-011 (CLAHE) | EXP-012 (relabel + retrain) |
| Crops | 135 | 72 usable (70 for same-crop comparisons) |
| Labels | Round 1 (`manual_labels_export.csv`) | Round 2 (`labels_round2.csv`, latest per crop) |
| Classes | 5 (Fear, Happy, Neutral, Sad, Surprise) | 4 (Happy, Neutral, Sad, Surprise) |
| Groups | Dark 89, Medium-Dark 46 | Dark 46, Medium-Dark 26 |

Protocol B numbers are **not comparable** to Protocol A: labels, classes, and population all differ (see `experiments/EXP-012-relabel/results/REPORT.md`).

## Figure inventory

Each figure is saved as SVG and PDF (vector) and PNG at 300 DPI in `figures/`. ⚠ marks figures that show identifiable faces: **internal use only**; anonymize or replace before any publication (source-film consent is unresolved).

| # | File | Caption | Source | Suggested placement |
|---|---|---|---|---|
| 1 | `fig01_research_pipeline` | Overall FER fairness evaluation pipeline: source video → face crops → labels and brightness groups → three model branches → group-gap evaluation, with Protocols A and B. | Ch. 3; `docs/EXPERIMENT.md` | Ch. 3 §3.1 |
| 2 | `fig02_dataset_extraction_qc` | (a) Legacy set: 144,084 source frames → 100 sampled frames → 227 labeled crops → 144 → 141 → 135. (b) Papuan V2 extraction: 1,390 sampled frames → 3,413 faces → 668 passing all QC (supporting, not evaluated). | `source_video_manifest.json`, `manual_labels_export.csv`, V2 QC manifests, EXP-007 | Ch. 3 §3.2 |
| 3 ⚠ | `fig03_original_vs_clahe` | Original crops and the EXP-006 adaptive CLAHE output for two Dark and two Medium-Dark crops, with per-crop clip limits (recomputed with the EXP-006 function; identical to the saved values). | `fer_dataset.shared.clahe`, `clahe_predictions.csv` | Ch. 3 §3.3.3 |
| 4 ⚠ | `fig04_landmark_annotation` | 42-point eyebrow/eye/mouth overlays used as a labeling aid in EXP-012: (a) reviewed, (b) unreviewed proposal, (c) missing; (d) overlay status for 227 crops (21 / 131 / 75). | `data/exp012/overlays`, `landmark_sources.csv` | Ch. 3 §3.5 |
| 5 | `fig05_arcface_logreg` | ArcFace + Logistic Regression: re-detection and alignment, frozen ArcFace w600k_r50, 512-d embedding, class-balanced L2 logistic regression; 5-fold grouped CV. | `tools/train_arcface_classifier.py` | Ch. 3 §3.3.4 |
| 6 | `fig06_exp010_performance` | EXP-010 (Protocol A): accuracy (95% grouped-bootstrap CI) and macro F1 for HSEmotion (0.363 / 0.249) and ArcFace+LR (0.407 / 0.272). | `reports/fairness_135/fairness_summary.json`, EXP-007 `statistical_tests.csv` | Ch. 4 §4.4 |
| 7 | `fig07_exp011_clahe` | EXP-011 (Protocol A): (a) HSEmotion original vs. CLAHE; (b) CLAHE − original changes with 95% CIs, all including zero (gap change −0.023 [−0.136, 0.073]). | `reports/clahe_fairness_135/clahe_fairness_summary.json` | Ch. 4 §4.3 |
| 8 | `fig08_exp012_performance` | EXP-012 (Protocol B): accuracy and macro F1 on the same 70 crops scored against round-2 labels, for the retrained ArcFace+LR, HSEmotion, and the EXP-007 ArcFace+LR. | `experiments/EXP-012-relabel/results/metrics.json` | Ch. 4 (new EXP-012 section) |
| 9 | `fig09_exp012_confusion_per_class` | EXP-012 retrained model, out-of-fold: (a) confusion matrix; (b) per-class F1 (Sad 0.000, n = 7). | `confusion_matrix.csv`, `per_class_metrics.csv` | Ch. 4 (EXP-012 section) |
| 10 | `fig10_dark_vs_medium_dark` | Dark vs. Medium-Dark accuracy and gap with 95% CIs, one row per protocol. EXP-010 did not save group-accuracy CIs for ArcFace+LR, so those points have no error bars. | EXP-010/011/012 JSON | Ch. 4 §4.5 |
| 11 | `fig11_annotation_landmarks` | (a) Round-1 vs. round-2 label distribution (227 crops); (b) round-2 Ambiguous rate by overlay status (72 of 75 crops without landmarks were Ambiguous). | `manual_labels_export.csv`, `labels_round2.csv`, `landmark_sources.csv` | Ch. 3 §3.5 or appendix |
| 12 | `fig12_timeline` | Research timeline; dates from round-1 label timestamps and first-commit dates in git history. | git log, `manual_labels_export.csv` | Appendix / progress report |

Mermaid sources (editable; render with any Mermaid viewer, e.g. GitHub, VS Code, or mermaid.live):

| # | File | Content |
|---|---|---|
| M1 | `mermaid/research_flowchart.mmd` | Overall research flowchart with Protocols A and B |
| M2 | `mermaid/experiment_workflow.mmd` | Experiment dependencies EXP-005 → EXP-012 |
| M3 | `mermaid/annotation_evaluation_workflow.mmd` | EXP-012 annotation, exclusion, and evaluation workflow (counts checked by the validator) |

`figures/figure_data.json` holds every plotted value, keyed by figure.

## Example selection (Figures 3 and 4)

Examples are chosen by a fixed rule in `make_figures.py:pick_examples`, not by hand: Figure 3 uses the first two crops (by ID) per brightness group whose round-2 overlay was rated *Usable*; Figure 4 uses the first *Usable* crop with reviewed and with proposal landmarks, and the first crop without landmarks.

## Regenerate and validate

Run from the repository root. `--data-root` points at the checkout that holds the git-ignored `data/` directory (crops, round-1 labels, CLAHE predictions, overlays).

```bash
uv run python docs/figures/research-tracking/make_figures.py --data-root /Users/MAC/Projects/FER-Dataset
uv run python docs/figures/research-tracking/validate_figures.py --data-root /Users/MAC/Projects/FER-Dataset
```

No new dependencies: matplotlib, pandas, numpy, and OpenCV are already in `pyproject.toml`. The scripts only read experiment outputs and write inside `docs/figures/research-tracking/figures/`.

## Notes and limitations shown in the figures

- Brightness groups are a LAB-luminance proxy computed from crop pixels; only Dark and Medium-Dark exist, so no light-skin evaluation is possible.
- CLAHE's effect on the gap is inconclusive (CI includes zero); ArcFace+LR's smaller Protocol-A gap is suggestive, not established; the EXP-012 retrained model's gap is not distinguishable from zero.
- Single annotator in both rounds; no subject IDs (temporal-block CV and bootstrap only partly control for repeated people).
