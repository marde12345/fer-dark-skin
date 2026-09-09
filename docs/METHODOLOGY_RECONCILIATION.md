# Methodology Reconciliation

> R3 — read-only methodology audit, building on `docs/RESEARCH_FRAMING.md` (R2.5). No source code, notebooks, datasets, reports, configuration, or dependencies were modified to produce this document.

---

## 1. Executive Summary

**The current pipeline's expression classifier is HSEmotion (`enet_b0_8_best_vgaf`), not ArcFace.** ArcFace-architecture weights (`w600k_r50`) are loaded as part of the InsightFace `buffalo_l` bundle, but only its detection (`det_10g`) and keypoint (`kps`) outputs are ever read by the code — the recognition/embedding output (`.embedding`/`.normed_embedding`) is never accessed anywhere in the repository. All existing baseline results (22.47% accuracy, false-Angry rate, Neutral→Angry breakdown, confidence analysis) are **HSEmotion results**, evaluated on InsightFace-detected face crops — they are not ArcFace results in any sense. This is a **P0-level discrepancy** if the thesis genuinely requires ArcFace as the FER method, since none of the existing experimental evidence would then answer the intended research question. A single decision — confirming with the advisor what "ArcFace" was meant to refer to — is required before any further experiment is designed.

---

## 2. Current Pipeline Methodology

```text
Video (pesta_babi.mp4)
    │  cv2.VideoCapture, frame sampling
    ▼
Frame Extraction  →  src/fer_dataset/pipeline/frame_extractor.py
    │
    ▼
Face Detection  →  src/fer_dataset/pipeline/face_detector.py
    │  InsightFace FaceAnalysis("buffalo_l") — SCRFD detector (det_10g.onnx)
    │  reads: face.bbox only
    ▼
Face Crop (20% padded bounding-box crop, saved as .jpg)
    │
    ▼
Expression Prediction  →  src/fer_dataset/pipeline/emotion_classifier.py
    │  HSEmotionRecognizer(model_name="enet_b0_8_best_vgaf")
    │  input: face crop image; output: emotion label + softmax confidence
    │  (a SECOND InsightFace FaceAnalysis("buffalo_l") instance is also
    │   constructed here, but only for face.kps — 5-point keypoints — used
    │   purely for an optional visualization overlay, not for classification)
    ▼
Dataset Annotation  →  src/fer_dataset/pipeline/dataset_builder.py, dataset_report.py
    │
    ▼
Landmark / Skin-Tone Analysis  →  src/fer_dataset/pipeline/landmark_analyzer.py
    │  MediaPipe FaceLandmarker (478-point) — independent of InsightFace/HSEmotion
    ▼
landmark_features.csv (skin-tone bucket, geometric features, associated label)
```

---

## 3. Current Model Inventory

| Stage | Implementation | Model | Purpose | Research Role |
|---|---|---|---|---|
| Face Detection | `src/fer_dataset/pipeline/face_detector.py:23-24` | InsightFace `buffalo_l` bundle → SCRFD detector (`det_10g.onnx`) | Locate face bounding boxes in frames | Produces the face crops everything downstream operates on |
| Face Detection (2nd instance) | `src/fer_dataset/pipeline/emotion_classifier.py:38-39` | Same InsightFace `buffalo_l` bundle, same SCRFD detector | Re-detect faces within already-cropped images, solely to obtain 5-point keypoints for an optional visualization overlay | Cosmetic only; not used for classification (also a known, previously-flagged redundancy — `docs/EXPERIMENT.md` Known Issues) |
| Face Recognition/Embedding | *(loaded, not read)* | InsightFace `buffalo_l` bundle → `w600k_r50.onnx` ("recognition" task, ArcFace architecture) | Would generate identity-embedding vectors if invoked | **Currently no research role** — never called for its output anywhere in the codebase |
| Expression Classification | `src/fer_dataset/pipeline/emotion_classifier.py:36,71-83` | HSEmotion ONNX, `enet_b0_8_best_vgaf` | Predict emotion label + confidence from a face-crop image | **This is the model behind every baseline/error-analysis result currently in the repository** |
| Landmark Detection | `src/fer_dataset/pipeline/landmark_analyzer.py:57-67` | MediaPipe FaceLandmarker (478-point: 468 mesh + 10 iris) | Geometric features, skin-tone-adjacent analysis | Independent of both InsightFace and HSEmotion |

---

## 4. ArcFace Audit

Repository-wide search performed for: `ArcFace`, `arcface`, `w600k_r50`, `buffalo_l`, InsightFace recognition models, `face embedding`, `recognition`, `embedding extraction`, `FaceAnalysis`, `normed_embedding`.

**Findings:**
- `buffalo_l` is instantiated via `insightface.app.FaceAnalysis(name="buffalo_l", ...)` in exactly two places: `face_detector.py:23-24` and `emotion_classifier.py:38-39`.
- The `buffalo_l` bundle, per InsightFace's own model zoo, includes five sub-models: `det_10g` (detection), `1k3d68` (3D landmarks), `2d106det` (2D landmarks), `genderage`, and **`w600k_r50`** (recognition — an ArcFace-family ResNet-based architecture). This is confirmed by the pipeline's own runtime log output (captured during Phase 0/9 validation runs): `find model: .../buffalo_l/w600k_r50.onnx recognition [...]`.
- **No code in the repository ever accesses `.embedding` or `.normed_embedding`** (the attributes InsightFace's `Face` object exposes for recognition output) — confirmed via a targeted grep across `src/` and `tools/` for `embedding`, `normed_embedding`, and `w600k_r50`: zero matches outside this audit document itself.
- The only `Face` object attributes read anywhere are `face.bbox` (`face_detector.py:62`) and `face.kps` (`emotion_classifier.py:100-101`).

**Answering the five specific questions:**
- **A. Is ArcFace explicitly instantiated?** Not by name — it is instantiated *implicitly* as one of five sub-models loaded whenever `FaceAnalysis(name="buffalo_l")` is constructed. No code refers to "ArcFace" or `w600k_r50` by name.
- **B. Are ArcFace embeddings actually extracted?** The underlying ONNX model runs as part of InsightFace's internal pipeline whenever `.get(image)` is called (InsightFace's `FaceAnalysis.get()` runs all loaded sub-models and populates the returned `Face` object's attributes, including `.embedding`), so the computation likely happens internally — but the **result is never read or used** by any of this repository's code.
- **C. Are embeddings used as input to an expression classifier?** No. The expression classifier (HSEmotion) takes a raw cropped image as input, not an embedding vector.
- **D. Is ArcFace involved only indirectly because it is bundled with InsightFace?** Yes — this is the accurate characterization. It is present as an artifact of using the `buffalo_l` bundle for detection, not a deliberate methodological choice.
- **E. Is ArcFace completely unused for expression recognition?** Yes, completely.

---

## 5. HSEmotion Audit

**Source:** `src/fer_dataset/pipeline/emotion_classifier.py` (full file).

- **Model initialization** (line 36): `self.model = HSEmotionRecognizer(model_name="enet_b0_8_best_vgaf")` — an EfficientNet-B0-based model from the HSEmotion library, pretrained (not fine-tuned in this repository).
- **Input preprocessing**: handled internally by `HSEmotionRecognizer.predict_emotions(image)` (library-internal; the repository passes the raw BGR crop image directly, per line 71 area — no separate resize/normalize code exists in this repository, meaning any such steps are entirely inside the third-party `hsemotion_onnx` package).
- **Output logits/probabilities**: `emotion, logits = self.model.predict_emotions(image)` returns a label string directly (from the library) plus raw logits.
- **Softmax**: applied explicitly by this repository's own `softmax()` function (lines 11-14) to the returned logits, to compute a confidence score — the label itself comes from the library's own internal argmax, not from this repository's softmax call.
- **Label mapping**: none — the label returned by `HSEmotionRecognizer` is stored verbatim (`records.append({"filename": ..., "label": emotion, ...})`, line ~87), which is why the stored vocabulary is HSEmotion's own (`Anger`, `Happiness`, `Sadness`, etc.), not the short-form (`Angry`, `Happy`, `Sad`) used elsewhere in the project's own documentation (an already-known, previously-documented discrepancy — see `docs/EXPERIMENT.md`).
- **Final expression label**: written to `data/intermediate/annotations.csv`, which is what every subsequent stage (dataset builder, landmark analysis, `data_audit.ipynb`) consumes as "the model's prediction."

**Conclusion: yes, HSEmotion is unambiguously the actual, sole FER classifier currently in this pipeline.**

---

## 6. Detection vs Recognition vs Expression Recognition

These are three genuinely distinct computer-vision tasks, and the repository's evidence maps them to three distinct (non-overlapping) model components:

| Concept | Definition | Model performing it here | Evidence |
|---|---|---|---|
| **Face Detection** | Locating a face's bounding box within an image | InsightFace `buffalo_l` → SCRFD (`det_10g.onnx`) | `face_detector.py:23-33`, reads `face.bbox` |
| **Face Recognition / Embedding** | Generating an identity-characterizing feature vector for a face (used for verification/identification, not expression) | InsightFace `buffalo_l` → `w600k_r50.onnx` (ArcFace architecture) — **loaded but its output is never used** | Section 4 |
| **Facial Expression Recognition** | Predicting an emotion/expression class from a face image | HSEmotion (`enet_b0_8_best_vgaf`) | `emotion_classifier.py:36,71-90` |

**These must not be conflated.** SCRFD (detection) and the ArcFace-architecture recognition model (`w600k_r50`) are both bundled inside "InsightFace `buffalo_l`," but they perform different tasks and only one of the two (detection) is actually used by this pipeline. Neither InsightFace component performs expression recognition — that is HSEmotion's role exclusively, and HSEmotion is an entirely separate library/model family from InsightFace.

---

## 7. Intended Thesis Method vs Current Implementation

| Intended Method | Current Implementation | Match? | Issue |
|---|---|---|---|
| FER using ArcFace | Face detection via InsightFace/SCRFD; expression classification via HSEmotion; ArcFace-architecture weights loaded but unused | **No** | ArcFace performs no role in expression prediction anywhere in the current pipeline |

**Can the current repository legitimately describe its FER classifier as "ArcFace-based"? No.** Every expression-classification result currently in the repository was produced by HSEmotion. Describing these results as "ArcFace-based FER" would misrepresent the actual methodology. The repository could accurately say it uses "InsightFace (SCRFD) for face detection" and, separately, "HSEmotion for expression classification" — but ArcFace itself contributes zero information to any expression prediction currently on record.

---

## 8. Possible Interpretations of "ArcFace"

| Interpretation | Currently supported? | Missing to support it | Implementation required |
|---|---|---|---|
| **(1) ArcFace as a face-recognition backbone/embedding model** (used for something other than expression, e.g. identity clustering, duplicate-face removal) | Loaded but unused — partially present as a byproduct of `buffalo_l` | A defined purpose for the embeddings (e.g., de-duplication, identity-consistency checks) | Read `.embedding`/`.normed_embedding` from the already-loaded model and use it for whatever purpose is intended |
| **(2) ArcFace embeddings used as a feature extractor feeding a separate expression classifier** (e.g., embedding → small MLP/classifier head → emotion label) | Not present at all | An expression classifier trained/fitted on ArcFace embeddings; no such classifier exists in this repository | New modeling work: extract embeddings for the labeled dataset, train a classifier head, evaluate it |
| **(3) ArcFace used directly as the expression classifier** (unusual — ArcFace is architected for identity verification, not typically for expression classes) | Not present, and not a standard use of ArcFace | An expression-output head on top of the ArcFace backbone; not how ArcFace is conventionally used | Substantial new modeling work; would also require justifying this atypical use of an identity-verification architecture for an expression task |
| **(4) Informal reference to "InsightFace" as a package/model family**, with ArcFace named loosely because it's InsightFace's best-known component | Fully present — InsightFace/SCRFD is already the detector | None — if this is the intended meaning, the current pipeline already matches, modulo correcting the terminology from "ArcFace" to "InsightFace (SCRFD)" | None; only a wording clarification |
| **(5) Aspirational/planned future model**, not yet implemented, mentioned as intended direction rather than current method | Consistent with `Tesis_Knowledge_Transfer_(1).md`'s own next-steps list, which mentions future work (RAF-DB training, fine-tuning, "Strategy C") without mentioning ArcFace specifically in that list | Clarification of whether ArcFace was part of that future plan or a separate, currently-unstated one | Depends entirely on what is confirmed |

No interpretation is assumed correct here — Section 11 states the single decision needed to resolve this.

---

## 9. What Existing Results Actually Measure

Stated precisely, per the audit's requirement not to relabel these as ArcFace results:

- **22.47% accuracy, 77.53% error rate** — HSEmotion's expression-prediction accuracy against manual ground truth, on InsightFace/SCRFD-detected face crops from `pesta_babi.mp4`.
- **False-Angry rate (0.1762), Neutral→Angry breakdown (18/40)** — characterizes HSEmotion's specific error pattern on this dataset.
- **Confidence analysis (true-Angry 0.4194 vs. false-Angry 0.5968)** — HSEmotion's own softmax-derived confidence scores.
- **Skin-tone analysis (accuracy/false-Angry rate by Dark/Medium-Dark)** — HSEmotion's accuracy broken out by a skin-tone bucket computed independently via MediaPipe landmarks + LAB color analysis (`landmark_analyzer.py`), unrelated to either InsightFace or ArcFace.

**All of the above are HSEmotion results.** None of them involve ArcFace in any capacity — ArcFace contributes nothing to face cropping (that's SCRFD), nothing to the expression label (that's HSEmotion), and nothing to the skin-tone computation (that's MediaPipe + a custom LAB-channel heuristic).

---

## 10. Research Impact

**Classification: P0**, conditionally — the actual severity depends entirely on which interpretation (Section 8) turns out to be correct, which cannot be determined from the repository alone:

- **If interpretation (2) or (3)** (ArcFace genuinely required as, or as input to, the FER method) **is correct: this is P0.** None of the existing baseline, error-analysis, or skin-tone results would answer a thesis question framed around ArcFace-based FER — they measure a different model entirely. All current experimental evidence (Sections 4, 8, 9 of `docs/RESEARCH_FRAMING.md`) would need to be reproduced, or the RQ substantially reworded, before the thesis could proceed on solid ground.
- **If interpretation (1)** (ArcFace as an auxiliary embedding model for some other purpose, not expression classification itself) **is correct: this is P1.** The existing HSEmotion-based results remain valid as the FER evidence; ArcFace would be an additional, separate analysis thread, not a replacement.
- **If interpretation (4)** (informal reference to InsightFace generally) **is correct: this is P2.** No methodological change is needed — only a terminology correction (say "InsightFace/SCRFD," not "ArcFace," when describing the detection stage) — and all existing results remain fully valid as-is.

Given the repository cannot determine which interpretation applies, this discrepancy is treated as **P0 by default** until resolved, since proceeding under the wrong assumption risks the entire experimental evidence base being misapplied to the wrong research question.

---

## 11. Required Decision Before Further Experiments

**Confirm with the advisor/thesis author which interpretation of "ArcFace" (Section 8) was intended, before designing or running any further experiment.**

Specifically, the confirming question should be posed as: *"Is ArcFace meant to be the actual expression classifier (or a required feature extractor feeding one), or was 'ArcFace' used loosely to refer to the InsightFace face-detection pipeline already in use?"* The answer directly determines whether the existing HSEmotion-based evidence base (baseline accuracy, error analysis, skin-tone analysis — all already collected and audited in `docs/RESEARCH_FRAMING.md`) can proceed as the thesis's core evidence unchanged, or whether new modeling work involving ArcFace must be undertaken first. No other next action in `docs/RESEARCH_FRAMING.md` (per-class metrics, statistical validation, etc.) should be prioritized ahead of this, since all of it currently rests on HSEmotion results whose relevance to the stated ArcFace-based intent is exactly what's in question.

This report does not recommend which interpretation is correct — that determination belongs to the author/advisor, not to this audit.

---

## 12. Source Traceability

- `docs/RESEARCH_FRAMING.md` (R2.5, in full — the ArcFace discrepancy was first flagged there; this document performs the detailed audit that finding called for)
- `docs/RESEARCH_EVIDENCE_AUDIT.md`, `docs/THESIS_RQ_ALIGNMENT.md` (R1, R2)
- `src/fer_dataset/pipeline/face_detector.py` (full file — `FaceAnalysis("buffalo_l")` instantiation, `face.bbox` usage)
- `src/fer_dataset/pipeline/emotion_classifier.py` (full file — `HSEmotionRecognizer` instantiation and usage, softmax, second `FaceAnalysis("buffalo_l")` instance, `face.kps` usage)
- `src/fer_dataset/pipeline/landmark_analyzer.py` (skin-tone computation, independent of InsightFace/HSEmotion)
- `src/fer_dataset/pipeline/dataset_report.py`, `dataset_builder.py` (annotation flow, confirming HSEmotion's label is what propagates downstream)
- Pipeline runtime log output (captured during earlier phase validation runs, e.g. Phase 0/9 end-to-end executions): `find model: .../buffalo_l/w600k_r50.onnx recognition [...]` — confirms `w600k_r50` (ArcFace-architecture) is part of the loaded `buffalo_l` bundle
- Repository-wide grep (this session) for: `ArcFace`, `arcface`, `w600k_r50`, `buffalo_l`, `embedding`, `normed_embedding`, `recognition`, `FaceAnalysis` across `src/` and `tools/` — confirmed no code path reads embedding/recognition output anywhere
- `Tesis_Knowledge_Transfer_(1).md` (§15.6 — next-steps list, checked for any ArcFace-specific mention; none found beyond the general research-direction statement provided as this task's context)
