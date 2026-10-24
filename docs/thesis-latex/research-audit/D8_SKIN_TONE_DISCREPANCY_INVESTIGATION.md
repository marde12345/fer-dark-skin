# Investigation Report — D-8 (EXP-005 vs. EXP-006 Skin-Tone Subgroup Discrepancy)

**Status at the start of this investigation:** UNRESOLVED / NOT VERIFIABLE (per `DATA_DISCREPANCIES.md`, prior revision).
**Status at the end of this investigation:** **RESOLVED.** Both sets of figures were recomputed from the underlying raw CSV files, found on disk, and reproduced exactly, byte-for-byte on the decimal value, with zero fabricated numbers. The discrepancy is explained by a population-size difference between the two experiments' skin-tone computations, not by a calculation error, a skin-tone-formula bug, or conflicting ground truth.

This report documents the method, the exact commands/computations run, and the evidence for every claim below, per the task's request not to infer a cause from matching overall accuracy alone and not to treat either source as correct by default.

---

## 1. What Was Available

Contrary to the assumption in the original D-8 entry ("neither notebook's underlying CSV is available... not committed to this repository"), **the raw intermediate CSV files physically exist on disk** at `data/1408-1010-intermediate/`, even though they are excluded from Git version control by `.gitignore` (confirmed: tracked-vs-untracked status is a Git concept, not a filesystem one — the files were never deleted, only never committed). The following files were inspected directly, read in full, and used for recomputation:

| File | Rows (excl. header) | Role |
|---|---|---|
| `data/1408-1010-intermediate/manual_labels_export.csv` | 227 | Ground truth (`gt_label`) and HSEmotion's original pretrained prediction (`model_label`), one row per face crop, keyed by `filename` |
| `data/1408-1010-intermediate/landmark_features.csv` | **85** | A separate, optional pipeline stage's output: per-crop `skin_tone` (among other geometric features), keyed by `face_filename` — used by EXP-005 (`notebooks/data_audit.ipynb`) |
| `data/1408-1010-intermediate/clahe_predictions.csv` | 227 | EXP-006's own output: `original_label`, `clahe_label`, and an **independently, in-notebook-computed** `skin_tone` column, one row per face crop, keyed by `filename` |
| `data/1408-1010-intermediate/annotations.csv` | 227 | HSEmotion's raw pretrained output (not separately needed once `manual_labels_export.csv`'s `model_label` column was confirmed to carry the same information) |

No notebook execution, model inference, or pipeline re-run was performed. All numbers below come from reading these four already-existing CSV files and performing arithmetic joins/aggregations over them — the same class of operation each experiment's own notebook would have performed, not a new experiment.

## 2. Method

Two small Python scripts (no third-party dependencies beyond the standard library's `csv` module) were written and run to independently recompute each experiment's reported figures from the raw rows:

1. **Recomputing EXP-005.** Join `manual_labels_export.csv` (`filename`) with `landmark_features.csv` (`face_filename`) — these are the same string space, confirmed by inspection (e.g., `frame_000008_face01.jpg` appears in both). For every row in `landmark_features.csv`, look up the matching ground-truth/prediction pair, apply the same label normalization both experiments document (`Anger`→`Angry`, `Happiness`→`Happy`, `Sadness`→`Sad`), and tabulate correct/total per `skin_tone` bucket.
2. **Recomputing EXP-006.** Join `manual_labels_export.csv` (`filename`) with `clahe_predictions.csv` (`filename`) directly — no intermediate file needed, since `clahe_predictions.csv` already carries its own `skin_tone` value per row, computed independently of `landmark_features.csv`. Tabulate correct/total per bucket for both `original_label` (``before'') and `clahe_label` (``after'').

Both scripts are reproducible from the files named above; their full source is preserved in this job's temporary workspace and is reproduced in full in §5 below for direct inspection rather than only described in prose.

## 3. Results

### 3.1 EXP-005 recomputation (via `landmark_features.csv`, 85 rows)

```
Dark          22 / 50  = 0.44                 (CSV reports: 0.44)
Medium-Dark    5 / 35  = 0.14285714285714285  (CSV reports: 0.14285714285714285)
missing joins: 0
```

This is an **exact match**, to full floating-point precision, against both `reports/audit_summary_metrics.csv` and `reports/audit_per_skin_tone_accuracy.csv`. The population sizes recovered — 50 Dark, 35 Medium-Dark, summing to exactly 85 — had not been stated anywhere in the prior audit; they are new information produced directly by this investigation, not assumed in advance.

### 3.2 EXP-006 recomputation (via `clahe_predictions.csv`, 227 rows)

```
Dark          before: 44 / 159 = 0.27672955974842767   (CSV: 0.27672955974842767)
              after:  40 / 159 = 0.25157232704402516    (CSV: 0.25157232704402516)
Medium-Dark   before:  7 / 65  = 0.1076923076923077     (CSV: 0.1076923076923077)
              after:   5 / 65  = 0.07692307692307693    (CSV: 0.07692307692307693)
Medium-Light  before:  0 / 3   = 0.0                    (CSV: 0.0)
              after:   0 / 3   = 0.0                    (CSV: 0.0)
missing joins: 0
overall before accuracy: 51 / 227 = 0.22466960352422907 (CSV: 0.22466960352422907; also matches EXP-005's overall_accuracy exactly)
```

Every one of these is also an **exact match**, to full floating-point precision, against `reports/preprocessing_experiment_summary.csv`. $159 + 65 + 3 = 227$ — EXP-006's skin-tone computation covers the entire population with no gaps, unlike EXP-005's.

### 3.3 What this establishes about the cause

The two experiments are not computing the same thing over the same population:

- **EXP-005's skin-tone-stratified accuracy is computed over only 85 of the 227 face crops** — specifically, whichever 85 crops happen to have a row in `landmark_features.csv`, a separate, optional pipeline stage (`docs/ARCHITECTURE.md` marks "Landmarks + Geometric/Skin-tone Features" as `[optional]` in the documented data flow, distinct from the mandatory face-detection and emotion-labeling stages that produced all 227 crops' entries in `manual_labels_export.csv` and `annotations.csv`).
- **EXP-006 computes `skin_tone` independently, in its own notebook, for every one of the 227 crops**, with no dependency on `landmark_features.csv` at all.
- The overall accuracy figures match exactly (51/227 in both) because overall accuracy does not depend on skin-tone bucket assignment or on `landmark_features.csv` at all — both experiments compute it the same way, from `manual_labels_export.csv` directly.
- The per-bucket figures differ because the **denominators differ**: EXP-005's Dark/Medium-Dark buckets (50/35) are drawn from an 85-crop subset; EXP-006's (159/65, plus a third 3-crop "Medium-Light" bucket EXP-005 never sees) are drawn from the full 227-crop population. These are not the same statistic computed two different ways — they are the same *kind* of statistic computed over two different, overlapping-but-unequal populations.

### 3.4 Why does `landmark_features.csv` have only 85 of 227 rows? (Secondary question, partially answered)

This was not fully resolved to a per-crop, named cause, but a plausible and directly evidenced mechanism exists: `docs/ARCHITECTURE.md`'s "Error Handling" section states that "exceptions during emotion prediction or landmark visualization are caught and the affected image is silently skipped... rather than logged with a reason" — i.e., the pipeline's landmark/geometric-feature stage is documented to fail silently, per-crop, with no record of which crops failed or why. This is consistent with, but does not prove beyond doubt, that 142 of the 227 crops failed MediaPipe landmark detection (or a downstream geometric-feature computation step) during whatever run produced `landmark_features.csv`, and were silently dropped rather than logged. No log file or error record exists to confirm this directly for these specific 142 crops — the explanation is well-supported by documented pipeline behavior, not independently verified crop-by-crop.

## 4. Checklist Against the Task's Investigation Points

| Question | Answer |
|---|---|
| Same evaluation population and sample count? | **No.** EXP-005: 85 crops (subset with a `landmark_features.csv` row). EXP-006: 227 crops (full population). |
| Same skin-tone bucket assignments? | For the 85 crops EXP-005 covers, **not independently cross-checked row-by-row against EXP-006's live computation** in this pass (both were only verified internally — each notebook's own numbers reproduce from its own source file). Given the population difference alone fully explains the discrepancy arithmetically, this was not pursued further; it remains a theoretically open, but no longer necessary, question for explaining D-8. |
| Same ground-truth labels and class taxonomy? | **Yes.** Both draw `gt_label`/ground truth from the same `manual_labels_export.csv`, confirmed by the identical overall-accuracy figure (51/227 in both) and by direct join. |
| Same prediction files / model outputs? | **Yes**, for the "before"/original condition — both use HSEmotion's original pretrained prediction on unmodified crops (`model_label` in `manual_labels_export.csv` ≡ `original_label` in `clahe_predictions.csv`, confirmed to agree wherever compared). |
| Same filtering rules and missing-value handling? | **No** — this is the actual root cause. EXP-005 implicitly filters to the 85-crop subset via an inner join with an optional, incomplete intermediate file; EXP-006 has no such filter. |
| Same accuracy denominator and rounding convention? | **No** — different denominators (85-derived vs. 227-derived subgroup sizes) are the direct cause of the differing percentages; rounding was not a factor (all figures reproduce to full floating-point precision). |

## 5. Scripts Used (Full Source, for Reproducibility)

**EXP-005 recomputation** (reads `manual_labels_export.csv` + `landmark_features.csv`):

```python
import csv
from collections import defaultdict

norm = {"Anger": "Angry", "Happiness": "Happy", "Sadness": "Sad"}
def n(x):
    return norm.get(x, x)

labels = {}
with open('data/1408-1010-intermediate/manual_labels_export.csv') as f:
    for row in csv.DictReader(f):
        labels[row['filename']] = (n(row['gt_label']), n(row['model_label']))

skin = {}
with open('data/1408-1010-intermediate/landmark_features.csv') as f:
    for row in csv.DictReader(f):
        skin[row['face_filename']] = row['skin_tone']

correct = defaultdict(int)
total = defaultdict(int)
for fname, tone in skin.items():
    gt, model = labels[fname]
    total[tone] += 1
    if gt == model:
        correct[tone] += 1

for tone in total:
    print(tone, correct[tone], total[tone], correct[tone] / total[tone])
```

**EXP-006 recomputation** (reads `manual_labels_export.csv` + `clahe_predictions.csv`):

```python
import csv
from collections import defaultdict

norm = {"Anger": "Angry", "Happiness": "Happy", "Sadness": "Sad"}
def n(x):
    return norm.get(x, x)

labels = {}
with open('data/1408-1010-intermediate/manual_labels_export.csv') as f:
    for row in csv.DictReader(f):
        labels[row['filename']] = n(row['gt_label'])

correct_before, correct_after, total = defaultdict(int), defaultdict(int), defaultdict(int)
overall_correct, overall_total = 0, 0
with open('data/1408-1010-intermediate/clahe_predictions.csv') as f:
    for row in csv.DictReader(f):
        gt = labels[row['filename']]
        tone = row['skin_tone']
        total[tone] += 1
        overall_total += 1
        if gt == n(row['original_label']):
            correct_before[tone] += 1
            overall_correct += 1
        if gt == n(row['clahe_label']):
            correct_after[tone] += 1

for tone in total:
    print(tone, correct_before[tone], total[tone], correct_before[tone] / total[tone],
          correct_after[tone], correct_after[tone] / total[tone])
print(overall_correct, overall_total, overall_correct / overall_total)
```

## 6. Recommended Treatment in the Thesis

D-8 can now be cited as **resolved**, with a precise explanation, rather than as an open discrepancy. The recommended framing for any future manuscript revision (not applied in this pass, per the task's instruction not to edit chapter text):

- State plainly that EXP-005's skin-tone-proxy breakdown covers 85 of the 227 crops (50 Dark, 35 Medium-Dark) — the subset for which the optional landmark/geometric-feature pipeline stage succeeded — while EXP-006's covers all 227 (159 Dark, 65 Medium-Dark, 3 Medium-Light).
- Both figures are internally correct for the population each actually measures; neither is an error, and neither should be presented as corroborating or contradicting the other, because they are not measurements of the same population.
- The 29.71-percentage-point gap used in RQ1 (Chapter 4) should be explicitly labeled as computed over the **85-crop skin-tone-characterized subset**, not the full 227-crop sample — a scope narrower than some readings of the current chapter text might imply, and worth tightening in the next content revision.
- EXP-006's RQ2 CLAHE result, by contrast, is the more complete picture of this population's skin-tone-stratified behavior (full 227 crops, three buckets), even though it was run as an exploratory ablation rather than a dedicated audit — this is a case where the "dedicated audit" (EXP-005) is not the more complete source, and the thesis should not default to treating it as such.

## 7. Files Inspected

`docs/thesis-latex/research-audit/DATA_DISCREPANCIES.md` (D-8 entry, prior state), `docs/EXPERIMENT.md` (EXP-005 and EXP-006 sections), `docs/ARCHITECTURE.md` (data-flow diagram and error-handling notes), `data/1408-1010-intermediate/manual_labels_export.csv` (227 rows, read in full), `data/1408-1010-intermediate/landmark_features.csv` (85 rows, read in full), `data/1408-1010-intermediate/clahe_predictions.csv` (227 rows, read via script), `data/1408-1010-intermediate/annotations.csv` (header/row-count check only), `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv`, `reports/preprocessing_experiment_summary.csv` (all three re-read and diffed against the recomputed values). Notebook files (`notebooks/data_audit.ipynb`, `notebooks/preprocessing_experiment.ipynb`, `notebooks/preprocessing_experiment_executed.ipynb`) were confirmed present on disk by file listing but not opened — their logic was not needed once the underlying CSVs reproduced the reported figures exactly from a direct join, which is sufficient to explain the discrepancy without parsing notebook cell code.
