# EXP-010 — Skin-Brightness Group Fairness Analysis (135-Crop Subset)

> Re-analysis of existing EXP-007 predictions. No model was trained, re-run, or re-extracted; no label, dataset, or prediction file was modified. All numbers below are produced by `tools/analyze_fairness_135.py` and saved in `reports/fairness_135/`.

## Purpose

Answer, on the existing data, the fairness-focused RQs approved by Pak Fadhil: how large the performance gap between skin-brightness groups is for HSEmotion (RQ1), and whether ArcFace + Logistic Regression differs from HSEmotion in that gap (RQ3). RQ2 (CLAHE) is not addressed here.

## Data and method

- **Population:** the 135-crop, 5-class common subset of EXP-007 (Neutral 76, Happy 32, Sad 12, Surprise 8, Fear 7), read from `reports/arcface_evaluation/evaluation_predictions.csv`. Ground truth is identical to `data/1408-1010-intermediate/manual_labels_export.csv`.
- **Class mapping (verified):** HSEmotion `Anger→Angry`, `Happiness→Happy`, `Sadness→Sad` (`HSEMOTION_LABEL_MAP`, `tools/evaluate_arcface_vs_hsemotion.py`). HSEmotion's 37 `Angry` predictions fall outside the 5-class label space and count as errors.
- **Brightness groups:** EXP-007/008 had a group for only 78 crops, because `landmark_features.csv` covers 85 crops. The same function (`LandmarkAnalyzer._compute_skin_tone`) was applied to the original (non-CLAHE) crops for all 135. It reproduces all 78 validated groups (78/78) and yields **Dark 89, Medium-Dark 46**; no Medium-Light or Light crops exist in this subset. Results are reported for both the full regrouping (primary) and the validated 78 (stability check).
- **Metrics:** accuracy and macro F1 overall (5 classes); accuracy and macro F1 per group (over classes present in that group); gap = Dark accuracy − Medium-Dark accuracy; worst-group accuracy; McNemar exact test per group; recall within Neutral and Happy per group.
- **Confidence intervals:** 95% grouped bootstrap, resampling temporal blocks (`frame_index // 3`) with replacement, 2,000 resamples, seed 42, the same scheme as EXP-007.

## Results

### Overall (n = 135), matches EXP-007

| Model | Accuracy | Macro F1 |
|---|---|---|
| HSEmotion | 0.363 | 0.249 |
| ArcFace+LR | 0.407 | 0.272 |

### Per group, full regrouping (n = 135, primary)

| Group | n | HSEmotion acc / F1 | ArcFace+LR acc / F1 | McNemar (HSE-only / Arc-only correct) |
|---|---|---|---|---|
| Dark | 89 | 0.483 / 0.278 | 0.449 / 0.271 | 18 / 15, p = 0.728 |
| Medium-Dark | 46 | 0.130 / 0.118 | 0.326 / 0.264 | 2 / 11, p = 0.022 |

| Measure | HSEmotion | ArcFace+LR |
|---|---|---|
| Gap (Dark − Medium-Dark) | 0.353 [0.182, 0.540] | 0.123 [−0.038, 0.282] |
| Worst-group accuracy | 0.130 [0.029, 0.250] | 0.326 [0.179, 0.442] |

Gap difference (HSEmotion gap − ArcFace+LR gap): **0.229 [0.054, 0.442]**.

### Per group, validated grouping only (n = 78, stability check)

| Group | n | HSEmotion acc / F1 | ArcFace+LR acc / F1 | McNemar |
|---|---|---|---|---|
| Dark | 46 | 0.457 / 0.342 | 0.457 / 0.268 | 9 / 9, p = 1.000 |
| Medium-Dark | 32 | 0.125 / 0.128 | 0.312 / 0.260 | 2 / 8, p = 0.109 |

| Measure | HSEmotion | ArcFace+LR |
|---|---|---|
| Gap (Dark − Medium-Dark) | 0.332 [0.135, 0.514] | 0.144 [−0.086, 0.410] |
| Worst-group accuracy | 0.125 [0.000, 0.227] | 0.312 [0.125, 0.450] |

Gap difference: **0.188 [−0.083, 0.477]**, so this interval includes 0.

### Within-class recall (full regrouping)

| Class | Group | n | HSEmotion recall | ArcFace+LR recall | HSEmotion → Angry |
|---|---|---|---|---|---|
| Neutral | Dark | 55 | 0.691 | 0.491 | 6 |
| Neutral | Medium-Dark | 21 | 0.190 | 0.286 | 12 |
| Happy | Dark | 18 | 0.167 | 0.611 | 4 |
| Happy | Medium-Dark | 14 | 0.071 | 0.429 | 4 |

## Conclusions (limited to this sample)

1. HSEmotion's accuracy on Medium-Dark crops is about 35 percentage points lower than on Dark crops; the confidence interval excludes zero under both groupings. The gap persists within the same class (Neutral, Happy), so a different expression mix alone does not explain it; Neutral→Angry errors are concentrated in Medium-Dark crops (12/21 vs 6/55).
2. ArcFace+LR shows a smaller gap whose confidence interval includes zero. The reduction comes from higher Medium-Dark accuracy, not from better Dark accuracy (Dark: 0.449 vs 0.483).
3. The smaller ArcFace+LR gap is **suggestive, not established**: the gap-difference interval excludes zero with all 135 crops grouped but includes zero on the validated 78.
4. Overall accuracy does not differ significantly between the models (EXP-007 McNemar p = 0.4614), and both models perform poorly in absolute terms (macro F1 < 0.28).

These are associations observed in one sample. They do not establish that skin tone causes the gap, and they do not generalize to Papuan people, other footage, or other skin-tone groups.

## Limitations

- **Proxy groups:** skin brightness is a LAB-luminance bucket computed from pixels, confounded with lighting. Only two groups, both dark, are present; **light vs dark performance cannot be evaluated**.
- **Small groups:** Medium-Dark n = 46 (32 in the validated grouping), with 2 Fear and 2 Surprise; per-class results are only meaningful for Neutral and Happy.
- **One film, one annotator:** all crops come from `pesta_babi.mp4`; ground truth has a single annotator with no agreement measure.
- **No identity data:** temporal-block resampling only partly accounts for the same people appearing in multiple crops.
- **Analysis after the fact:** EXP-007 predates the RQs. HSEmotion is used as-is, while ArcFace+LR uses grouped 5-fold cross-validation predictions; its 5-class label space cannot produce the Neutral→Angry error.
- **Consent and provenance** of the source film remain undocumented and unresolved.

## Reproduction

```bash
uv run python tools/analyze_fairness_135.py
# options: --predictions, --faces-dir (default data/1408-1010-intermediate/faces, git-ignored), --out-dir
```

Outputs, in `reports/fairness_135/`:
- `fairness_summary.json`: all metrics and confidence intervals.
- `skin_tone_groups.csv`: validated vs recomputed group per crop, and the temporal block.
- `within_class_recall.csv`: within-class recall table.

Output is deterministic (verified identical across two runs).
