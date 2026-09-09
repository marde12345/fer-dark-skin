# ArcFace FER Experiment Design

> R4 — read-only experiment design, building on `docs/METHODOLOGY_RECONCILIATION.md` (R3), which established that the current pipeline's FER classifier is HSEmotion and that ArcFace weights are loaded but unused. This document designs (does not implement) a frozen-ArcFace-embedding + trainable-classifier FER experiment. No source code, notebooks, datasets, reports, configuration, or dependencies were modified or added to produce this document.

---

## 1. Research Objective

> How should ArcFace embeddings be used as a frozen facial feature representation for expression classification on this dataset, and how should the resulting FER system be fairly evaluated against the existing HSEmotion baseline?

This is an experiment-design question, not a request to prove ArcFace superior — Section 18 explicitly keeps the outcome open in all three directions (better/similar/worse).

---

## 2. Proposed Architecture

```text
Video (pesta_babi.mp4)
    ↓
Frame Extraction                    [existing, unchanged: src/fer_dataset/pipeline/frame_extractor.py]
    ↓
Face Detection (InsightFace/SCRFD)  [existing, unchanged: src/fer_dataset/pipeline/face_detector.py]
    ↓
Face Crop (.jpg, already on disk)
    ↓
[NEW] Landmark Re-detection for Alignment   — see Section 4
    ↓
[NEW] ArcFace Alignment (112×112 norm_crop) — see Section 4
    ↓
[NEW] ArcFace Feature Extraction (w600k_r50, frozen)
    ↓
Frozen Embedding (512-d float32)    — see Section 5
    ↓
[NEW] Expression Classifier (trained on embeddings) — see Sections 6-7
    ↓
Expression Prediction (7-class label + confidence)
```

| Stage | Input | Output | Model/Library | Key Parameters | Trained/Frozen | Research Purpose |
|---|---|---|---|---|---|---|
| Frame Extraction | video file | frame `.jpg` sequence | OpenCV (existing) | `fps=2` | N/A | Unchanged from current pipeline |
| Face Detection | frame `.jpg` | bbox + face crop `.jpg` | InsightFace SCRFD (existing) | `det_size=(640,640)`, 20% bbox padding | Frozen (pretrained) | Unchanged from current pipeline |
| Landmark Re-detection for Alignment | face crop `.jpg` | 5-point `kps` in crop coordinates | InsightFace SCRFD, re-run on the crop (same technique already used in `emotion_classifier.py`'s visualization path) | same detector, single-face expected | Frozen (pretrained) | Required because ArcFace's own alignment (`face_align.norm_crop`) needs 5-point landmarks, which the saved face-crop files do not carry |
| ArcFace Alignment | face crop + `kps` | 112×112 aligned face | InsightFace `face_align.norm_crop` (bundled utility, not a trainable model) | `image_size=112`, `arcface_dst` template | N/A (deterministic geometric transform) | Standardizes pose/scale before embedding, per ArcFace's own expected input contract |
| ArcFace Feature Extraction | 112×112 aligned face | 512-d embedding | InsightFace `buffalo_l` → `w600k_r50.onnx` (`ArcFaceONNX`) | `input_mean=127.5, input_std=127.5` | **Frozen** (no fine-tuning, per the stated experimental assumption) | Produces the fixed facial representation the classifier will learn on top of |
| Expression Classifier | 512-d embedding | 7-class prediction + confidence | To be selected — Section 7 | To be defined once selected | **Trained** on this dataset | The only trained component in this design |

---

## 3. ArcFace Implementation

**Recommendation: use the ArcFace model already bundled inside InsightFace's `buffalo_l` (`w600k_r50.onnx`), accessed via InsightFace's own `ArcFaceONNX` wrapper — do not add a new dependency or a different ArcFace implementation.**

Evidence from inspecting the installed package (`insightface==1.0.1`, `.venv/lib/python3.12/site-packages/insightface/model_zoo/arcface_onnx.py`) rather than assuming reuse is safe:

- **Model**: `w600k_r50.onnx`, task name `"recognition"`, ResNet-50-based ArcFace architecture, already present on disk (already downloaded as part of `buffalo_l`, confirmed in Phase 0/9 runtime logs).
- **Embedding dimensionality**: **512**, `float32` — confirmed directly from the ONNX graph's output tensor shape (`dim_value: 512`), not merely assumed from ArcFace convention.
- **Input resolution**: **112×112×3** — confirmed from the ONNX graph's input tensor shape.
- **Preprocessing**: `input_mean=127.5, input_std=127.5` (i.e., pixel values scaled to roughly [-1, 1]), BGR→RGB swap (`swapRB=True` in `get_feat`) — both read directly from `ArcFaceONNX.__init__`/`get_feat`, not assumed.
- **Normalization**: the model's raw output (`.embedding`) is **not** L2-normalized; InsightFace's `Face` object (`insightface/app/common.py`) exposes a separate `.normed_embedding` property that L2-normalizes on access. **Recommendation: store the L2-normalized embedding** (`normed_embedding`), since cosine-similarity-style comparison (the standard use case for ArcFace embeddings, and compatible with a linear/logistic classifier) is scale-invariant only after normalization, and this avoids ambiguity about whether downstream consumers must normalize themselves.
- **Determinism**: `CPUExecutionProvider` (already the project's convention for InsightFace elsewhere, e.g. `face_detector.py`) is deterministic given identical input and library versions — consistent with the project's existing "deterministic given fixed input, model weights, and dependency versions" reproducibility stance (`docs/EXPERIMENT.md`).

No new package needs to be added — `insightface` is already a direct dependency (`pyproject.toml`), and this is exactly the model file already present on disk from the existing pipeline's `buffalo_l` usage. This is a reuse of already-downloaded weights, not a new model acquisition.

---

## 4. Face Alignment and Preprocessing

This is the most consequential design decision in this document, and it is **not** a silent assumption — it was determined by reading InsightFace's own alignment code (`insightface/utils/face_align.py`, `arcface_onnx.py:get`).

**Finding**: `ArcFaceONNX.get(img, face)` calls `face_align.norm_crop(img, landmark=face.kps, image_size=112)`, which requires (a) the image the landmarks were detected in, and (b) 5-point facial landmarks (`kps`) **in that same image's coordinate space**. It does **not** accept an arbitrary pre-cropped image without corresponding landmarks.

**Problem**: the current pipeline's saved face crops (`data/intermediate/faces/*.jpg`, produced by `face_detector.py`) are bounding-box crops with 20% padding — they do **not** carry `kps`, and `face_detector.py` discards the `Face` object (including its `kps`) once the bbox is used for cropping (`face_detector.py:62`, only `face.bbox` is read).

**Two candidate approaches, evaluated:**

1. **Re-run detection on the original frame to recover `kps`, then align from the frame.** Rejected as the primary approach: it requires re-associating each saved face crop back to its source frame and re-running full-frame detection, which risks re-detecting a *different* face if multiple faces exist in the frame (ambiguous match-back), and duplicates work already partially done.
2. **Re-run detection on the already-saved face crop itself to recover crop-local `kps`, then align from the crop.** **Recommended.** This mirrors an approach **already established in this codebase**: `emotion_classifier.py`'s second `FaceAnalysis` instance already does exactly this (re-detects within the crop to get `kps` for its visualization overlay — `emotion_classifier.py:89-101`). Using the same technique for ArcFace alignment introduces no new preprocessing methodology, only a new *use* of an already-precedented step.

**Recommended alignment procedure**:
```text
face crop (.jpg, already on disk, padded per face_detector.py:57)
    → InsightFace FaceAnalysis.get(crop_image)   [re-detect within the crop]
    → face.kps (5-point landmarks, crop-local coordinates)
    → face_align.norm_crop(crop_image, landmark=face.kps, image_size=112)
    → 112×112 aligned face
    → ArcFaceONNX.get_feat(aligned_face)
    → 512-d embedding
```

**Research implication to document explicitly**: if a crop contains zero detected faces on re-detection (possible, since the original detection ran on the full frame with different context) or more than one face, that sample must be **excluded and counted**, not silently guessed at — this mirrors the same class of silent-failure risk already fixed once in this repository (the Phase 9 annotation-matching bug). The exact exclusion count must be reported alongside any final embedding dataset (Section 5).

**Do not reuse the current 20%-padded crop directly as ArcFace input without alignment** — `norm_crop`'s similarity-transform alignment (rotation/scale/translation to a canonical 112×112 template) is a different, more precise operation than a padded bounding-box crop, and ArcFace embeddings are known (from the architecture's own design intent) to be sensitive to alignment quality. Skipping alignment would not be "reusing the existing crop directly" in any methodologically neutral sense — it would silently degrade embedding quality relative to ArcFace's documented expected input.

---

## 5. Embedding Contract

| Field | Specification |
|---|---|
| `sample_id` | The existing face-crop filename stem (e.g. `frame_000008_face01`) — already a unique, stable identifier in this repository's convention; no new ID scheme needed |
| `face_filename` | Full existing filename (`frame_000008_face01.jpg`) — preserves the join key already used by `landmark_features.csv` and `manual_labels_export.csv` |
| `label` | Ground-truth label from `manual_labels_export.csv`'s `gt_label` column (see Section 9 — not the HSEmotion pseudo-label) |
| `skin_tone` | Joined from `landmark_features.csv`'s `skin_tone` column where available; `null`/absent where not (see Section 10 — never imputed) |
| `embedding` | 512-length `float32` vector, **L2-normalized** (`normed_embedding`, per Section 3) |
| `alignment_status` | `"aligned"` or `"excluded_no_face_on_recrop"` / `"excluded_multi_face_on_recrop"` (per Section 4's exclusion handling) — required so excluded samples are visible, not silently dropped |
| `embedding_model` | Literal string `"buffalo_l/w600k_r50"` and the InsightFace package version (`insightface==1.0.1`) — for reproducibility, per Section 13 |

**Storage format**: a single CSV or Parquet file with one row per sample, `embedding` stored as a serialized array (e.g. a JSON-encoded list in a CSV cell, or a native array column in Parquet). **Recommendation: Parquet**, since a 512-float CSV cell is unwieldy and error-prone to parse reliably, and this repository does not currently have an established convention for storing per-sample float vectors in CSV (its existing CSVs — `landmark_features.csv`, `annotations.csv` — store only scalar columns). This would be the first vector-valued artifact in the repository, so the format choice should be made deliberately, not by extending CSV past its comfortable use case here.

This mirrors the existing `landmark_features.csv` convention (`face_filename` as join key, `skin_tone` column) rather than inventing a new identity scheme.

---

## 6. Expression Classifier Options

| | Option A — Logistic Regression / Linear | Option B — Small MLP | Option C — SVM (RBF or linear kernel) |
|---|---|---|---|
| Advantages | Simple, fast, highly interpretable (per-class weight vectors), minimal hyperparameters, very low overfitting risk on small data | Can model non-linear decision boundaries; moderate flexibility | Strong small-sample performance historically for embedding classification; RBF kernel captures non-linearity |
| Disadvantages | May underfit if classes aren't linearly separable in embedding space | More hyperparameters (layer size, depth, learning rate, regularization); higher overfitting risk on a small dataset | Less interpretable than linear; kernel/C/gamma selection needed; slower at scale (not a concern here) |
| Computational cost | Very low | Low-moderate (still trivial at this dataset size) | Low-moderate |
| Overfitting risk (this dataset size) | **Low** — dataset is small (≤227 samples, likely fewer after alignment exclusions and skin-tone/label filtering) | **Moderate-to-high** — an MLP's extra capacity is a real risk with so few samples per class (e.g., `Surprise` had only 1-3 samples in prior analyses) | **Low-moderate** — generally robust on small samples but still requires care with class imbalance |
| Interpretability | High (linear weights) | Low | Moderate (support vectors, less directly interpretable than linear weights) |
| Reproducibility | Very high (convex optimization, deterministic given fixed seed/solver) | Lower (initialization-sensitive, needs a fixed seed and careful reporting) | High (deterministic given fixed kernel/params) |

---

## 7. Recommended Classifier

**Logistic Regression (multinomial, L2-regularized) — Option A.**

Rationale: the dataset is small (≤227 samples total, with several classes having single-digit counts per skin-tone group as documented in `docs/RESEARCH_FRAMING.md`), which makes an MLP's extra capacity a genuine overfitting risk rather than a benefit, and makes an SVM's additional kernel/hyperparameter surface harder to justify without evidence it's needed. A linear classifier on top of a *pretrained, frozen* 512-d ArcFace embedding is also methodologically the most defensible "does the frozen embedding linearly separate expressions" first experiment — if it performs poorly, that is itself informative (Section 18) before reaching for more complex, harder-to-reproduce classifiers. This is consistent with the design brief's request for the *first* experiment, not a final, optimized one.

---

## 8. Dataset Split Strategy

**Available grouping metadata, inspected directly**: face-crop filenames encode `frame_XXXXXX_faceNN` — i.e., a frame index and a within-frame face index, **not** a person/identity label. No column in `manual_labels_export.csv`, `annotations.csv`, or `landmark_features.csv` encodes person identity across frames. `face_XX` numbering within a frame is not a stable cross-frame identity (there's no guarantee `face01` in frame 8 is the same individual as `face01` in frame 9 — InsightFace assigns this index per-detection-call, not via tracking).

**Critical leakage risk**: since frames are sampled from a single continuous video at 2 fps, temporally adjacent frames very likely contain the **same individuals** in near-identical pose/lighting. A random per-image split would very likely place near-duplicate views of the same person's face in both train and test, inflating apparent performance — this is a real, evidence-supported risk given the video's continuous nature (`config/config.yaml`: single video, `fps: 2`), not a hypothetical one.

**Recommended grouping strategy, given no identity labels exist**: **group by source frame index** (the `frame_XXXXXX` portion of the filename) as the best available proxy for temporal/scene locality, and additionally **enforce a temporal buffer** — assign entire contiguous frame-index ranges (e.g., blocks of N consecutive sampled frames) to a single split, rather than shuffling individual frames, to reduce the chance that near-adjacent frames (same person, near-identical pose) land in different splits. This is an explicit **limitation**, not a solved problem: without true identity labels, no split can fully guarantee zero identity leakage — this must be stated plainly in any resulting thesis text, not glossed over.

**Recommended protocol given the small sample size**: given ≤227 total samples (and likely fewer usable ones after alignment exclusions, Section 4), a full train/val/test three-way split risks each split — especially per-class subsets — becoming too small to be meaningful (recall `Surprise` had as few as 1-3 samples in existing analyses). **Recommend grouped k-fold cross-validation** (e.g., `GroupKFold`, grouping by frame-block as above) over a single fixed train/test split, reporting mean ± spread across folds, rather than a single-point estimate that a small test set would make noisy and hard to trust.

---

## 9. Label Strategy

- **Label source**: use `manual_labels_export.csv`'s `gt_label` (manually verified ground truth), **not** the HSEmotion pseudo-label (`model_label` or `annotations.csv`'s `label`) — training and evaluating a new classifier against pseudo-labels produced by the very model being compared against would be circular and would not constitute an independent evaluation.
- **Seven emotion classes**: the manually-labeled set's actual observed `gt_label` values include the six HSEmotion-vocabulary emotions observed in `docs/EXPERIMENT.md`'s EXP-000 baseline (`Anger`/`Fear`/`Neutral`/`Sadness`/`Happiness`/`Surprise`) **plus an `Ambiguous` category** (confirmed present in `manual_labels_export.csv`'s `gt_label` values, per `docs/RESEARCH_FRAMING.md` Section 4/Dataset). `Disgust` (the 7th class per `docs/SDD.md`) was not observed in the audited baseline sample and its presence in `manual_labels_export.csv` was not independently re-confirmed in this document.
- **Handling `Ambiguous`**: this is a genuine label-strategy decision, not something to silently resolve. Recommend **excluding `Ambiguous`-labeled samples from classifier training and evaluation**, reporting the exclusion count explicitly, since "Ambiguous" is not one of the target expression classes and including it would require deciding how a classifier should treat an inherently unclear ground truth — a decision this document does not make unilaterally.
- **Pseudo-labels vs. manual**: to be unambiguous — `gt_label` is manually reviewed (per `manual_labels_export.csv`'s own `labeled_at` timestamp column, indicating a human labeling process occurred), while `model_label`/`annotations.csv`'s `label` are HSEmotion's automatic pseudo-labels. This experiment must train and evaluate against `gt_label` only.
- **Label noise**: not independently quantifiable from repository evidence (no inter-rater/repeated-labeling data exists to estimate manual-label noise) — stated as a limitation, not estimated.

---

## 10. Class Imbalance Strategy

**Recommendation: class-weighted cross-entropy (equivalently, `class_weight="balanced"` in a logistic regression fit) — not plain cross-entropy, and not balanced *sampling*.**

Reasoning: the existing evidence (`docs/RESEARCH_FRAMING.md` Section 4, EXP-000 baseline distribution) shows a heavily skewed distribution (e.g., `Neutral`/`Fear` dominant, `Surprise` a handful of samples). Balanced *sampling* (oversampling minority classes or undersampling majority ones) risks either duplicating an already-tiny minority class's few examples many times over (oversampling, inflating apparent minority-class confidence artificially) or discarding already-scarce majority-class data (undersampling, worsening an already small dataset). Class-weighted loss/fit achieves a similar rebalancing effect on the *objective* without physically manipulating the sample set, and is the simpler, lower-risk choice consistent with the "avoid unnecessary complexity" instruction.

---

## 11. Baseline Comparison

**Fair-comparison requirements, all necessary simultaneously**:
1. **Same dataset**: the exact same sample set (post-alignment-exclusion, post-`Ambiguous`-exclusion) must be used for both HSEmotion and the ArcFace-based classifier's evaluation — not HSEmotion's original 227-sample evaluation vs. a smaller ArcFace-eligible subset. **Recommendation: report HSEmotion's accuracy/metrics recomputed on the exact same evaluation subset used for the ArcFace classifier**, in addition to (not instead of) the existing full-227-sample HSEmotion baseline — both numbers should be shown, clearly labeled, so a shrinking evaluation set isn't mistaken for a genuine ArcFace advantage or disadvantage.
2. **Same ground-truth labels**: `gt_label` for both, per Section 9 — HSEmotion's existing accuracy figures were already computed against `gt_label` (`notebooks/data_audit.ipynb` cell 5), so this is consistent with reuse, not a new requirement.
3. **Same class definitions**: exclude `Ambiguous` from both comparisons' metrics identically (Section 9), and decide `Disgust`'s handling identically for both if it turns out to be present/absent asymmetrically between the two evaluation sets.

**Metrics** (all to be computed on the same evaluation subset for both systems):
- Accuracy
- Macro Precision, Macro Recall, Macro F1
- Per-class F1
- Confusion matrix
- False-Angry rate (rate of predicting "Angry" when `gt_label != "Angry"`, matching the existing definition in `notebooks/data_audit.ipynb` cell 11)
- Neutral→Angry count/rate specifically (matching the existing analysis)
- Confidence/calibration: HSEmotion already provides a softmax confidence per prediction; a logistic-regression classifier (Section 7) also naturally provides class probabilities — both can be compared on mean-confidence-by-correctness the same way the existing audit already does (`notebooks/data_audit.ipynb` cell 13), so this comparison is directly reusable in form, not just concept.

---

## 12. Skin-Tone Analysis

**Analysis population**: only the subset of samples that have (a) a `gt_label` (not `Ambiguous`), (b) a successful ArcFace alignment (Section 4), and (c) a computed `skin_tone` value (currently 85/227 in the existing landmark-features data, though this exact count may shift slightly for the ArcFace-eligible subset after Section 4's alignment exclusions — this must be recounted for the actual ArcFace-experiment population, not assumed to stay at 85).

**Subgroup sample sizes**: must be explicitly tabulated for the actual analysis population (not assumed from prior HSEmotion-era counts), since Sections 4 and 9's exclusions may change which specific samples are eligible.

**Metrics per subgroup**: accuracy, macro F1, false-Angry rate — computed separately for `Dark` and `Medium-Dark` (the only two buckets with any data, per existing evidence), for **both** HSEmotion and the ArcFace classifier, enabling a same-metric, same-subgroup, cross-model comparison that does not currently exist.

**Fairness/bias interpretation**: report as an **observed difference**, not a statistically validated one, unless Section 14's statistical layer is actually applied and passes — consistent with the caution already established in `docs/RESEARCH_FRAMING.md`.

**Missing skin-tone values**: **do not impute.** The 142/227 (or whatever the ArcFace-eligible-subset equivalent turns out to be) samples lacking a computed skin tone should be reported as a separate "skin-tone unknown" group in descriptive tables where relevant, or simply excluded from skin-tone-stratified analysis with the exclusion count stated — never filled in with an assumed or predicted value, since skin-tone bucket is itself a measured, LAB-color-derived quantity (`landmark_analyzer.py:118-137`), and imputing it would fabricate a measurement that was never taken.

---

## 13. False-Angry Analysis

**Design, mirroring the existing HSEmotion-era analysis exactly, so the two are comparable**:
- **Count**: number of samples with `gt_label == "Neutral"` and `predicted_label == "Angry"`, computed identically for HSEmotion and for the ArcFace classifier, on the same evaluation subset.
- **Rate**: that count divided by the total number of `Neutral`-ground-truth samples in the evaluation subset (denominator = `Neutral` GT count, not total dataset size — this must be stated explicitly, since "false-Angry rate" could otherwise ambiguously mean "of all samples" vs. "of Neutral samples," and the existing analysis's exact denominator convention should be checked and matched, not assumed).
- **Comparison against other errors**: report the full false-Angry breakdown by true class (as `notebooks/data_audit.ipynb` cell 11 already does for HSEmotion) for the ArcFace classifier too, to see whether Neutral→Angry remains the dominant false-Angry source or shifts.
- **HSEmotion vs. ArcFace comparison**: side-by-side counts/rates on the identical evaluation subset (Section 11's fair-comparison requirement applies here specifically).
- **Demographic/Papuan-identity separation**: per `docs/RESEARCH_FRAMING.md` Section 4's already-established finding, no field in this dataset encodes ethnicity or Papuan identity. Any claim that a specific quantitative pattern (e.g., "the false-Angry rate is a Papuan-specific phenomenon") remains a **researcher observation about the population the video depicts**, not a **quantitatively demonstrated subgroup effect**, since there is no subgroup variable to test it against. This distinction must be preserved identically for the ArcFace experiment's results — a lower or higher false-Angry rate under ArcFace does not, by itself, provide or remove evidence about ethnicity-specific effects; it only speaks to this specific model's behavior on this specific (undifferentiated-by-ethnicity) sample.

---

## 14. Statistical Evaluation

Minimum, not maximal, statistically defensible analysis — deliberately not overcomplicated:

- **Overall model comparison (ArcFace vs. HSEmotion)**: since both models produce predictions on the **same** samples (paired, not independent, comparison), **McNemar's test** is the appropriate choice for comparing two classifiers' accuracy on identical paired samples (it directly tests whether the disagreement pattern between the two models' correct/incorrect calls is asymmetric) — more appropriate here than an unpaired test, since both models are evaluated on the same items.
- **Confidence intervals**: report a **bootstrap confidence interval** (resampling the evaluation set with replacement, recomputing accuracy/macro-F1 each time) for each model's headline metrics, given the small sample size makes a single point estimate hard to trust in isolation — this is a standard, low-complexity approach that doesn't require distributional assumptions.
- **Skin-tone subgroup comparison (Dark vs. Medium-Dark)**: given small, uneven group sizes (as established in prior audits — e.g., as few as 11-16 samples in some prior groupings), a **Fisher's exact test** (for a 2×2 accuracy-correct/incorrect × skin-tone-group contingency table) is more appropriate than a chi-square test, which assumes larger expected cell counts than these subgroups likely provide. Report an **effect size** (e.g., odds ratio, alongside its own confidence interval) rather than relying on a p-value alone, given the small-sample setting.
- **Error comparison (False-Angry / Neutral→Angry)**: the same paired-McNemar approach applies if comparing HSEmotion's vs. ArcFace's false-Angry behavior on the same samples (paired); Fisher's exact test applies if comparing false-Angry rate across skin-tone subgroups within one model (independent groups).
- **What NOT to do**: no need for more advanced techniques (e.g., permutation tests, Bayesian hierarchical models) at this stage — the sample sizes and comparison structure here do not require them, and introducing them would add complexity without a corresponding evidentiary need.

---

## 15. Reproducibility Contract

Everything below must be frozen and recorded before implementation begins:

**Dataset**
- Exact input file: `data/1408-1010-intermediate/manual_labels_export.csv` (or its `docs/baseline_snapshots/phase0/`-equivalent, whichever is designated as canonical for this experiment — must be decided explicitly, not left ambiguous, since both exist).
- Exact sample count at each filtering stage (raw 227 → after `Ambiguous` exclusion → after alignment-eligibility exclusion → final evaluation set), each count reported, not just the final number.
- Label version: `gt_label` column as it exists at a specific, recorded file checksum/commit — since this file could in principle be re-exported with corrections.

**Face Detection**
- Model: InsightFace `buffalo_l`, SCRFD `det_10g.onnx` (already fixed by the existing pipeline; unchanged for this experiment, per the design brief's instruction not to modify existing detection).
- Detection parameters: `det_size=(640,640)`, CPU execution provider (existing, unchanged).
- Bbox handling: existing 20% padding — but note per Section 4 that ArcFace alignment does **not** use this padded crop as-is; it re-detects `kps` within the crop and re-aligns to 112×112 via `norm_crop`.

**ArcFace**
- Model: `buffalo_l/w600k_r50.onnx`, `insightface==1.0.1` (exact version pinned, per `uv.lock`).
- Embedding dimension: 512, `float32`, L2-normalized (`normed_embedding`).
- Alignment: `face_align.norm_crop`, `image_size=112`, `arcface_dst` template (InsightFace's built-in, unmodified).
- Preprocessing: `input_mean=127.5, input_std=127.5`, BGR→RGB (all internal to `ArcFaceONNX`, unmodified).

**Classifier**
- Algorithm: multinomial logistic regression (Section 7), L2-regularized.
- Hyperparameters: regularization strength, solver, max iterations — to be fixed and recorded at implementation time (this design does not prescribe exact values, since that is a tuning decision belonging to implementation, not design).
- Random seed: a single fixed seed must be recorded and reused across all folds/runs.

**Evaluation**
- Split: grouped k-fold cross-validation (Section 8), exact `k` and grouping-block size to be fixed and recorded at implementation time.
- Metrics: as listed in Section 11.
- Statistical tests: as listed in Section 14, with exact library/implementation (e.g., `scipy.stats` — not currently a dependency; would need to be added at implementation time, which this document does not do) recorded.

---

## 16. Experiment Matrix

| Experiment | Feature Extractor | Classifier | Purpose |
|---|---|---|---|
| Baseline | HSEmotion (`enet_b0_8_best_vgaf`) | HSEmotion's own native output (no separate classifier) | Existing, already-collected reference point |
| Proposed | ArcFace (`w600k_r50`, frozen) | Logistic Regression (Section 7) | Main experiment — answers this document's research objective |

No additional matrix cells are proposed. A hyperparameter sweep, alternative classifiers (Options B/C), or additional ArcFace-variant experiments are explicitly **not** recommended at this stage — per the design brief's instruction to avoid a large sweep, and because Sections 6-7 already justify a single classifier choice for the first experiment. If the logistic-regression result is inconclusive or clearly underfitting, that would be a data-driven reason to consider Option B/C in a *later*, separate experiment — not something to pre-build into this first matrix.

---

## 17. Existing Evidence Reuse

| Existing Evidence | Classification | Reasoning |
|---|---|---|
| HSEmotion overall accuracy (0.2247), error rate | **Reusable after re-analysis** | Valid as a reference point, but for a *fair* comparison (Section 11) it should be recomputed on the exact same evaluation subset used for the ArcFace classifier, alongside (not instead of) the original full-sample figure |
| False-Angry analysis (Neutral→Angry breakdown) | **Reusable after re-analysis** | Same reasoning — the existing breakdown is valid HSEmotion evidence, but a same-subset recomputation is needed for direct comparison |
| Skin-tone analysis (accuracy/false-Angry by bucket) | **Reusable after re-analysis** | Same reasoning; also the ArcFace-eligible subset's skin-tone composition must be recounted (Section 12), not assumed identical to the prior 85-sample count |
| Landmark/geometric-feature analysis (`brow_lowering_distance` etc.) | **Cannot be reused for this experiment** | This analysis answers a different question (geometric correlates of predicted labels) unrelated to ArcFace embeddings; it neither validates nor is validated by an ArcFace-vs-HSEmotion comparison |
| CLAHE preprocessing experiment | **Cannot be reused for this experiment** | Tested a different intervention (image preprocessing before HSEmotion classification); orthogonal to the frozen-embedding-plus-classifier design here. Could become relevant later only if CLAHE were tested as a pre-alignment step for ArcFace specifically — not proposed here |
| Manual ground-truth labels (`gt_label`) | **Reusable without modification** | This is exactly the label source this experiment should use (Section 9) — no changes needed |
| Face-crop images on disk | **Reusable without modification** | These are the correct starting point for the alignment step (Section 4); no need to regenerate frames/detections |

---

## 18. Success Criteria

Defined without presupposing which model wins:

- **Strong result**: ArcFace+classifier achieves a statistically meaningful improvement (per Section 14's McNemar/CI framework) in macro-F1 and/or false-Angry rate over HSEmotion on the identical evaluation subset, **and** the improvement (or lack of degradation) holds consistently across both skin-tone subgroups (not just in aggregate) — this would support a defensible thesis claim that a frozen-ArcFace-embedding approach helps this specific population/error pattern.
- **Neutral result**: ArcFace+classifier performs comparably to HSEmotion (no statistically distinguishable difference per Section 14) — this is still a valid, reportable finding: it would suggest the bottleneck is not the facial representation but something else (e.g., training-data representation bias generally, as the existing `Tesis_Knowledge_Transfer_(1).md` narrative already speculates), which is itself useful information for deciding the thesis's next direction (e.g., toward "Strategy C"-style training-side intervention rather than representation swapping).
- **Negative result**: ArcFace+classifier performs statistically worse than HSEmotion, and/or shows a larger (not smaller) skin-tone fairness gap — this would be a legitimate, reportable finding that a general-purpose identity-recognition embedding does not transfer well to this expression-classification task on this population, and should be reported as such, not discarded or reframed.

All three outcomes are equally valid experimental results under this design; none is presupposed as more likely or more desirable.

---

## 19. Recommended Next Implementation Phase

**R5 — Implement frozen ArcFace embedding extraction only, for the existing manually-labeled face-crop set, with no classifier training yet.**

This is deliberately the smallest independently-verifiable next step, not the whole pipeline at once:
- Scope: re-detect `kps` on each existing face crop, align to 112×112, extract the 512-d `normed_embedding`, and write the embedding dataset per the contract in Section 5 — including the `alignment_status` field so exclusions are visible.
- Verifiable independently of any classifier or comparison work: the output can be checked for correct shape (512-d), correct normalization (unit L2 norm), correct row count against expectations, and correct exclusion accounting — all without needing to have decided final classifier hyperparameters or split strategy details yet.
- Training the classifier (Section 7), the grouped cross-validation split (Section 8), and the HSEmotion comparison (Sections 11-14) should each be **separate, subsequent, independently-reviewable implementation phases** (e.g., R6, R7, R8) — not folded into R5 — so that a bug or unexpected result in embedding extraction is caught and fixed before it silently propagates into classifier training and evaluation, mirroring the lesson already learned once in this repository (Phase 9's annotation-alignment bug was only caught because each pipeline stage could be validated somewhat independently).

---

## 20. Source Traceability

- `docs/METHODOLOGY_RECONCILIATION.md` (R3, in full)
- `docs/RESEARCH_FRAMING.md` (R2.5), `docs/THESIS_RQ_ALIGNMENT.md` (R2), `docs/RESEARCH_EVIDENCE_AUDIT.md` (R1)
- `.venv/lib/python3.12/site-packages/insightface/model_zoo/arcface_onnx.py` (installed `insightface==1.0.1`) — `ArcFaceONNX` class, preprocessing constants, `get`/`get_feat` methods
- `.venv/lib/python3.12/site-packages/insightface/utils/face_align.py` — `norm_crop`, `estimate_norm`, `arcface_dst` template
- `.venv/lib/python3.12/site-packages/insightface/app/common.py` — `Face.embedding_norm`, `Face.normed_embedding` properties
- `/Users/MAC/.insightface/models/buffalo_l/w600k_r50.onnx` — inspected directly via `onnx.load(...).graph.{input,output}` to confirm 512-d output, 112×112×3 input (not assumed from documentation)
- `src/fer_dataset/pipeline/face_detector.py` (existing detection stage, confirmed unchanged by this design)
- `src/fer_dataset/pipeline/emotion_classifier.py` (existing HSEmotion usage; also the precedent for re-detecting `kps` within an already-cropped image, reused in Section 4's alignment design)
- `data/1408-1010-intermediate/manual_labels_export.csv` (`gt_label`, `Ambiguous` category, `labeled_at` — schema inspected, not modified)
- `data/1408-1010-intermediate/landmark_features.csv` (skin-tone join-key convention, `face_filename` column)
- `docs/EXPERIMENT.md` (EXP-000 baseline label distribution; reproducibility stance)
- `pyproject.toml`, `uv.lock` (confirmed `insightface` already a direct dependency at the pinned version; no new dependency identified as necessary for this design)
