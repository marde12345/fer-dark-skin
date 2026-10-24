# EXP-011 — Original vs. CLAHE: Skin-Brightness Group Analysis (135-Crop Subset)

> Re-analysis of saved EXP-006 predictions on the EXP-010 population. No inference was run, no model was trained, and no label, dataset, or prediction file was modified. All numbers are produced by `tools/analyze_clahe_fairness_135.py` and saved in `reports/clahe_fairness_135/`.

## Purpose

Answer RQ2 on the main 135-crop population: does the tested CLAHE configuration change HSEmotion's performance gap between skin-brightness groups? EXP-006 reported this only descriptively on the 227-crop sample, without confidence intervals.

## Data and method

- **Population and groups:** identical to EXP-010. The 135-crop 5-class subset, with brightness groups from `LandmarkAnalyzer._compute_skin_tone` on the original crops (Dark 89, Medium-Dark 46).
- **Predictions:** `original_label` and `clahe_label` from `data/1408-1010-intermediate/clahe_predictions.csv` (EXP-006: one adaptive CLAHE configuration, `clip_min=1.5, clip_max=3.5`, HSEmotion `enet_b0_8_best_vgaf`).
- **Metrics and intervals:** the EXP-010 functions are imported directly. Accuracy, macro F1 (5 classes), per-group accuracy, gap (Dark − Medium-Dark), and paired change (CLAHE − Original). 95% grouped bootstrap over temporal blocks (`frame_index // 3`), 2,000 resamples, seed 42. Exact McNemar test overall and per group.

## Data checks

| Check | Result |
|---|---|
| Crops found in EXP-006 file | 135/135 (227 rows, no duplicates) |
| Original predictions = EXP-007 HSEmotion predictions | 135/135 after label mapping |
| EXP-006 `skin_tone` = EXP-010 recomputed group | 135/135 |
| Predictions changed by CLAHE | 32/135 |

**Label-name difference (cosmetic):** EXP-006 stores HSEmotion labels already renamed (`Angry`, `Happy`, `Sad`), while EXP-007 stores the model's raw names (`Anger`, `Happiness`, `Sadness`). Compared literally, only 88/135 match; after the shared mapping, all 135 match. This is a naming difference, not a data difference. HSEmotion's `Angry` predictions count as errors, since `Angry` is outside the 5 classes.

## Results

| | Original | CLAHE | CLAHE − Original |
|---|---|---|---|
| Accuracy | 0.363 [0.269, 0.467] | 0.326 [0.233, 0.424] | −0.037 [−0.109, 0.020] |
| Macro F1 | 0.249 | 0.199 | −0.050 (no CI) |
| Dark accuracy (n = 89) | 0.483 [0.366, 0.633] | 0.438 [0.326, 0.560] | −0.045 [−0.143, 0.028] |
| Medium-Dark accuracy (n = 46) | 0.130 [0.029, 0.250] | 0.109 [0.030, 0.188] | −0.022 [−0.098, 0.061] |
| **Gap (Dark − Medium-Dark)** | 0.353 [0.182, 0.540] | 0.330 [0.217, 0.447] | **−0.023 [−0.136, 0.073]** |
| Angry predicted, Dark | 0.169 | 0.202 | |
| Angry predicted, Medium-Dark | 0.478 | 0.478 | |

McNemar (original-only correct / CLAHE-only correct): all 11/6, p = 0.332; Dark 9/5, p = 0.424; Medium-Dark 2/1, p = 1.000.

Validated grouping only (n = 78): gap 0.332 → 0.319, change −0.012 [−0.098, 0.102].

Within class: Neutral recall Dark 0.691 → 0.673, Medium-Dark 0.190 → 0.143 (Neutral→Angry 12 → 11); Happy recall Dark 0.167 → 0.056, Medium-Dark 0.071 → 0.071.

## Conclusions (limited to this sample)

1. The tested CLAHE configuration did not measurably change the Dark vs. Medium-Dark gap: the change is −0.023, and its interval includes zero under both groupings. The gap remains large with and without CLAHE.
2. Accuracy decreased slightly but not significantly: all accuracy-change intervals include zero, and every McNemar p ≥ 0.33. Macro F1 fell by 0.05 (no interval computed).
3. The Medium-Dark Angry-prediction rate is unchanged (0.478), so CLAHE did not address the main error pattern behind the gap.
4. These results agree with EXP-006's descriptive 227-crop result (lower accuracy, no narrower gap) and add confidence intervals on the main population.

## Limitations

- **One exploratory configuration:** a single adaptive CLAHE setting from a notebook outside the production pipeline; no conclusion about CLAHE in general.
- **Low power:** Medium-Dark n = 46 with only 3 changed predictions there. "No significant change" does not mean "no effect".
- **Proxy groups:** brightness is mixed with lighting; only Dark and Medium-Dark are present, so light vs dark cannot be evaluated.
- **Data:** one film, one annotator with no agreement measure, no identity data. The temporal-block bootstrap only partly accounts for the same people in several crops.
- **Multiple tests:** McNemar tests are not corrected for multiple comparisons; treat them as exploratory.
- **Analysis after the fact:** the CLAHE predictions predate the RQs.
- **Consent and provenance** of the source film remain unresolved.

## Reproduction

```bash
uv run python tools/analyze_clahe_fairness_135.py
# options: --predictions, --clahe-predictions, --faces-dir (both data/ paths are git-ignored), --out-dir
```

Outputs, in `reports/clahe_fairness_135/`:
- `clahe_fairness_summary.json`: data checks, all metrics and intervals.
- `per_crop_predictions.csv`: group, temporal block, and both mapped predictions per crop.
- `within_class_recall.csv`: within-class recall table.

Output is deterministic (verified identical across runs).
