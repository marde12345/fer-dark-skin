# Data Dictionary

## Entity: Face Crop (both lineages)

The fundamental unit of both D-LEGACY and D-PAPUANV2 is a **face crop**: one detected face, cropped from one video frame, at one point in time. A face crop is identified by (video, frame index, detection index within frame) in principle; whether this composite identifier is actually stored as an explicit column in the underlying CSVs was **not independently re-verified against the raw files** in this pass (the raw `data/` files are gitignored and were inspected only through summary CSVs in `reports/`).

| Field (as referenced in reports/CSVs) | Type | Meaning | Unit/Range | Missing-value convention | Provenance |
|---|---|---|---|---|---|
| Expression label (manual) | categorical | human-assigned emotion class | 7-class set: {Neutral, Ambiguous, Happy, Sad, Disgust, Fear, Surprise, Angry} | not observed in reviewed summaries | single human annotator |
| Expression label (HSEmotion) | categorical | pretrained-model prediction | HSEmotion's own 7-class vocabulary: {Anger, Disgust, Fear, Happiness, Neutral, Sadness, Surprise} | N/A — model always emits a class | HSEmotion ONNX pretrained inference |
| Skin-tone bucket | categorical | LAB-luminance-derived bucket | observed values: {Dark, Medium-Dark, Unknown} | "Unknown" is an explicit bucket, not a null | computed from face-crop pixels, `src/landmark_analyzer.py` |
| Temporal group | integer/categorical | 3-frame block grouping, used only for CV grouping (leakage mitigation) | 16 groups observed in the N=135 evaluation | N/A | derived from frame index, not a real subject ID |
| ArcFace embedding | float vector | 512-d, L2-normalized face-recognition feature | continuous | N/A | InsightFace `buffalo_l/w600k_r50`, frozen |
| `alignment_status` | categorical | records whether ArcFace re-detection/alignment on a given crop succeeded or failed (e.g., `"aligned"` vs. `"excluded_no_face_on_recrop"` / `"excluded_multi_face_on_recrop"`), per `docs/ARCFACE_EXPERIMENT_DESIGN.md` | {aligned, excluded\_no\_face\_on\_recrop, excluded\_multi\_face\_on\_recrop} | exclusion reasons are explicit categories, not nulls | ArcFace re-detection step; this field is what ultimately separates the 227-crop population from the 178 crops with successful embeddings, and contributes 6 of the 92 exclusions between the 141 label-eligible population and the final N=135 (see `research-audit/DATA_DISCREPANCIES.md` D-2) |

### What Does *Not* Exist

- **No subject/person-identity field exists anywhere in either dataset.** The "temporal group" field used for cross-validation grouping is a heuristic proxy (adjacent frames are *likely* to show the same subject in a near-duplicate pose) and is explicitly **not** a verified identity label. **Implication for leakage:** it is possible for the same real individual to appear in frames far apart in time (e.g., re-entering a scene) and be assigned to different temporal groups, meaning some cross-group "independence" assumed by the grouped cross-validation may not hold. This is a standing, unresolved limitation of every evaluation in this repository, not something fixed by any experiment to date.
- **No ethnicity field exists.** The skin-tone bucket is a pixel-luminance computation, not a self-reported or externally assigned ethnicity/demographic label. Using it as a proxy for "Papuan" or any other population identity is a stated assumption of this research, not a verified fact about the subjects — the dataset's relevance to "Papuan" facial characteristics rests entirely on the fact that the source film's subjects are, by the film's own documentary subject matter, Papuan individuals, not on any per-image demographic annotation.
- **No consent or provenance record exists** for the use of individual subjects' likenesses from the source film.
- **No frame-level timestamp-to-wall-clock mapping, camera/shot metadata, or lighting-condition label exists**, which limits the ability to separate "skin-tone effect" from "lighting/shot-composition effect" in the subgroup analyses reported in Chapter 4 of the thesis manuscript.

### Label Schema Mapping (5-class reduction used in all formal comparative evaluation)

| Original 7/8-class label | Included in 5-class evaluation taxonomy? |
|---|---|
| Neutral | Yes |
| Happy | Yes |
| Sad | Yes |
| Fear | Yes |
| Surprise | Yes |
| Disgust | **No** — excluded (n=2 at N=227 scale, too sparse) |
| Angry | **No** — excluded (n=1 at N=227 scale, too sparse) |
| Ambiguous | **No** — excluded from the 5-class taxonomy; its disposition in the N=135 subset (whether "Ambiguous" instances were dropped entirely or reassigned) was **not located in the documents reviewed**. Flagged as an open item. |

### CVAT Landmark Schema (Papuan V2, landmark track)

68 points, ibug-300W convention, renamed from generic identifiers (`pt0`..`pt67`) to anatomically descriptive names (e.g., jawline, eyebrow, eye-contour, nose-bridge, nose-base, mouth-outer, mouth-inner point groups — exact naming scheme in `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md`). Each point's coordinate is currently an **automatic proposal** (InsightFace `landmark_3d_68`), not a human-verified label, pending CVAT review.
