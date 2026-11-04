# EXP-012 Results — ArcFace + LR Retrained on Round-2 Labels

> Retraining and evaluation on the round-2 labels (`../labels_round2.csv`). Produced by `tools/exp012/train_eval_round2.py`; deterministic (byte-identical outputs across runs). EXP-007/010/011 results, embeddings, and round-1 labels are unchanged.

## Dataset (frozen)

- 227 crops, one annotation per crop (latest; one crop, `frame_000066_face01`, had two identical annotations). Inclusion decisions per crop: `round2_dataset.csv`. Labels file SHA-256 in `config.json`.
- Excluded: **148 Ambiguous** (intentional: faces without enough visible features), 2 crops without an ArcFace embedding (alignment failure), and, by the existing rule of at least 5 samples per class, **Fear (2) and Disgust (3)**.
- **Usable: 72 crops, 4 classes** — Happy 30, Neutral 23, Surprise 12, Sad 7.

| Class | Dark | Medium-Dark |
|---|---|---|
| Happy | 17 | 13 |
| Neutral | 16 | 7 |
| Sad | 6 | 1 |
| Surprise | 7 | 5 |
| **Total** | **46** | **26** |

## Method (unchanged from EXP-007/010)

Frozen ArcFace embeddings (existing `embeddings.csv`), class-balanced L2 logistic regression, 5-fold `StratifiedGroupKFold` over 14 temporal blocks (frame index ÷ 3), seed 42, with an assertion that no block is in both train and test. Every crop is predicted once, by a model that did not see its block. Brightness groups from `_compute_skin_tone` on the original crops. 95% CIs: grouped bootstrap over temporal blocks, 2,000 resamples, seed 42. HSEmotion and the EXP-007 ArcFace+LR model are **not re-run**; their saved predictions are re-scored against the round-2 labels.

## Results — retrained model (72 crops, out-of-fold)

| Metric | Value |
|---|---|
| Accuracy | 0.611 [0.528, 0.714] |
| Macro F1 (4 classes) | 0.482 |
| Dark accuracy (n = 46) | 0.543 [0.455, 0.658] |
| Medium-Dark accuracy (n = 26) | 0.731 [0.522, 0.897] |
| Gap (Dark − Medium-Dark) | −0.187 [−0.388, 0.079] |
| Worst-group accuracy | 0.543 [0.450, 0.649] |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Happy | 0.667 | 0.800 | 0.727 | 30 |
| Neutral | 0.684 | 0.565 | 0.619 | 23 |
| Sad | 0.000 | 0.000 | 0.000 | 7 |
| Surprise | 0.583 | 0.583 | 0.583 | 12 |

Confusion matrix (rows = round-2 label): `confusion_matrix.csv` / `.png`. Sad is never predicted correctly (5 of 7 predicted as Neutral).

## Comparison on the same 70 crops, all scored against round-2 labels

| Model | Accuracy [CI] | Macro F1 | Dark | Medium-Dark | Gap [CI] |
|---|---|---|---|---|---|
| ArcFace+LR, round-2 retrained | 0.614 [0.532, 0.717] | 0.484 | 0.556 | 0.720 | −0.164 [−0.370, 0.106] |
| ArcFace+LR, EXP-007 (round-1 trained) | 0.414 [0.284, 0.581] | 0.350 | 0.400 | 0.440 | −0.040 [−0.397, 0.282] |
| HSEmotion (fixed) | 0.157 [0.079, 0.246] | 0.169 | 0.222 | 0.040 | 0.182 [0.024, 0.339] |

- Retrained vs. HSEmotion: McNemar 38 vs. 6, p < 0.001; accuracy difference 0.457 [0.339, 0.586]; gap difference −0.347 [−0.529, −0.141].
- Retrained vs. EXP-007 ArcFace+LR: McNemar 19 vs. 5, p = 0.007; accuracy difference 0.200 [0.045, 0.327]; gap difference −0.124 [−0.316, 0.098].

## How much of the difference is the new labels, not a better model

- **Same algorithm, same features.** The retrained model differs from EXP-007's only in its training labels (round 2 vs. round 1) and in having 4 instead of 5 classes. Its higher score against round-2 labels is therefore expected and is **not** evidence of a better modeling method.
- **Label change alone moves scores a lot.** On the 68 crops labeled with one of the 4 classes in round 2, the *unchanged* HSEmotion predictions score 0.279 against round-1 labels but 0.162 against round-2 labels. Round-1 and round-2 labels agree on 58.8% of these crops.
- **Easier task and filtered population.** The 4-class task has a higher chance level than EXP-010's 5 classes, and excluding 148 Ambiguous crops leaves mostly clearer faces. Both raise accuracy independently of the model.
- **EXP-010 is not directly comparable.** EXP-010 reported ArcFace+LR 0.407 / 0.272 and HSEmotion 0.363 / 0.249 on 135 crops, 5 classes, round-1 labels. Population, classes, and labels all differ here.

## Interpretation (limited to this sample)

1. With round-2 labels, the retrained classifier reaches 0.61 out-of-fold accuracy on 72 usable crops, but macro F1 is 0.48 and Sad is not recognized at all.
2. The Dark vs. Medium-Dark gap is not distinguishable from zero for the retrained model (CI −0.388 to 0.079). The point estimate even favors Medium-Dark, but with 26 Medium-Dark crops (1 Sad) this is not a reliable difference in either direction. **No fairness improvement is claimed.**
3. HSEmotion still shows a positive gap on these crops (0.182 [0.024, 0.339]), consistent in direction with EXP-010, but on far fewer crops.

## Limitations

- **Small sample:** 72 crops; Medium-Dark 26; Sad 7 (1 Medium-Dark); Fear and Disgust excluded. Per-class results within groups are not interpretable.
- **Single annotator, no agreement measure;** 74% of round-2 annotations were Low confidence (see `../README.md`).
- **Non-random exclusion:** Ambiguous crops are the lowest-quality faces, so results describe clearer faces only and are not comparable to evaluations that include them.
- **No subject IDs:** 3-frame temporal blocks only keep neighboring frames apart; the same person may appear in both train and test folds, so out-of-fold accuracy may be optimistic. With 14 blocks and small classes, fold composition is uneven.
- **Exploratory tests:** McNemar and gap comparisons are uncorrected for multiple comparisons.
- **Brightness proxy:** two dark groups only; no light-skin evaluation. Consent/provenance of the source film remains unresolved.

## Files

`config.json` (settings, input hashes) · `metrics.json` · `per_class_metrics.csv` · `confusion_matrix.csv` / `.png` · `oof_predictions.csv` (per crop: round-2 label, round-1 label, group, block, all three models' predictions) · `round2_dataset.csv` (frozen dataset and exclusion reasons)
