# EXP-DASH-001 — Landmark-based Expression Classifier (Dashboard Demo)

**This is a dashboard demonstration experiment, separate from the formal thesis experiments/results.**

## Phase 1 — Data inspection

Searched the repository for expression-labeled data. Found
`data/1408-1010-intermediate/manual_labels_export.csv` — the same ground-truth
label source already used by this project's own real thesis classifier
(`tools/train_arcface_classifier.py`). Its `gt_label` column holds human-assigned
labels for 227 face crops; its `model_label` column is HSEmotion's own prediction
and was **never** used as a training target (that would be pseudo-labeling the
model this classifier is meant to be compared against).

227 rows → 83 "Ambiguous" excluded → 144 usable → after excluding classes with
fewer than 5 samples (`MIN_CLASS_COUNT=5`, matching the existing ArcFace
classifier's own convention): **141 samples, 5 classes** (Angry: 1 and Disgust: 2
excluded as too rare).

Not blocked: suitable labeled data existed, so training proceeded.

## Phase 2 — Training

- **Landmarks**: InsightFace `landmark_3d_68` (same method as the CVAT pilot —
  synthetic full-crop bbox, skip re-detection). 144/144 crops succeeded.
- **Features** (7, all normalized by inter-ocular distance; translation/scale
  invariant by construction): `ear_mean`, `mouth_openness`, `mouth_width_ratio`,
  `lip_corner_angle`, `brow_eye_dist_mean`, `inner_brow_distance`, `jaw_drop`.
- **Split/leakage control**: `StratifiedGroupKFold`, 5 folds, grouped by
  consecutive-frame-index blocks of 3 (identical to
  `tools/train_arcface_classifier.py` — no person-ID field exists anywhere in
  this repository). Every sample is scored out-of-fold; there is no separate
  static test set (141 samples / 5 classes is too small to hold one out without
  making the rare classes unusable).
- **Models compared**: Logistic Regression, Random Forest, SVM-RBF — identical
  features/splits.

### Class distribution (usable, 141 samples)

| Class | Count |
|---|---|
| Neutral | 80 |
| Happy | 34 |
| Sad | 12 |
| Surprise | 8 |
| Fear | 7 |

### Out-of-fold cross-validation results

| Model | macro-F1 |
|---|---|
| **Logistic Regression** | **0.223** |
| Random Forest | 0.209 |
| SVM (RBF) | 0.153 |

Logistic Regression — per-class (out-of-fold):

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Fear | 0.05 | 0.14 | 0.07 | 7 |
| Happy | 0.45 | 0.41 | 0.43 | 34 |
| Neutral | 0.63 | 0.21 | 0.32 | 80 |
| Sad | 0.10 | 0.33 | 0.15 | 12 |
| Surprise | 0.11 | 0.25 | 0.15 | 8 |

Full confusion matrices, per-model reports, and exclusion counts: see
`landmark_classifier_metadata.json`.

**This classifier is weak** — macro-F1 ≈0.22 is close to chance for 5
imbalanced classes, and performance on the rare classes (Fear, Surprise, Sad)
is especially unreliable given only 7–12 out-of-fold predictions each. This is
reported as-is, not hidden or downplayed.

### Deployment choice

Logistic Regression is deployed (fit on all 141 usable samples, no held-out
split for the deployed artifact — the CV above is the real evaluation) because
its linear decision function ports trivially to pure browser JS (dot product +
softmax, zero ML libraries) — not because it had a decisively better score;
all three baselines performed similarly poorly.

### Artifacts

- `extract_landmark_features.py` — landmark extraction + feature computation
- `landmark_classifier_features.csv` — 144 rows, raw features + gt_label
- `train_landmark_classifier.py` — CV evaluation + final model fit
- `landmark_classifier_model.joblib` — sklearn model + scaler + class order (Python-side)
- `landmark_classifier_weights.json` — plain-JSON export of the same model, for the browser
- `landmark_classifier_metadata.json` — full dataset/label/split/metrics/limitations record

## Phase 3 — Dashboard integration

- New file `dashboard/landmark_expression_classifier.js`: computes the same 7
  features from face-api.js's 68-point output (formulas manually cross-checked
  line-by-line against `extract_landmark_features.py`; no automated
  cross-language numeric test was possible — no JS runtime was available in
  this environment), then runs the frozen LR weights (dot product + softmax).
- `dashboard/realtime_landmark_demo.js` was extended (not replaced) so the
  classifier runs on the **same landmark positions already computed for the
  overlay/status**, in all three input modes (Original continuous loop, CLAHE
  and Appearance Simulation one-shot renders) — no second face/landmark
  detection call anywhere.
- New "Landmark-based Expression" panel added beside the 4 existing FER panels
  and the landmark panel in `dashboard/index.html`, with its own caveat text
  and a dedicated "Technical details" block.
- Existing FER models, the FER server, and `realtime_demo.js`'s FER inference
  logic are unchanged; Original/CLAHE/Appearance Simulation mode controls are
  unchanged and still work.

## Phase 4 — Comparison

A "Phase 4" note card was added directly in the dashboard explaining that the
live side-by-side panels are illustrative only, not a quantitative comparison
— image-based FER and the landmark classifier were never evaluated on the same
labeled test examples in the same run, so live agreement/disagreement must not
be read as an accuracy measurement for either approach. The only real
quantitative numbers for the landmark classifier are the offline CV metrics
above; image-based FER's own formal numbers come from a different evaluation
(R7–R9) on a different test set — no shared-test-set comparison was possible
within this task's scope.

## Limitations (restated from `landmark_classifier_metadata.json`)

1. Only 141 labeled samples across 5 classes; Angry/Disgust excluded entirely.
2. Severe residual imbalance (Neutral=80 vs. Fear=7) — rare-class metrics are
   not statistically reliable.
3. This is an illustrative demo classifier, not a validated research result.
4. 68 geometric points cannot capture texture cues (e.g. nose wrinkling for
   Disgust) — a structural ceiling independent of sample size.
5. No automated cross-language verification between the Python feature
   extractor and its browser JS port (manual inspection only).
6. The scheme-compatibility assumption (InsightFace `landmark_3d_68` ≡
   face-api.js 68-point ordering) is documented but not independently verified
   pixel-for-pixel.
