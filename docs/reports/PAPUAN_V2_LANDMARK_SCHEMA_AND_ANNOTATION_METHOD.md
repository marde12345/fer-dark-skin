# Papuan V2 — Landmark Schema & Annotation Method Investigation

## 1. Objective

Resolve two specific methodological gates left open by the 2026-10-02 pivot audit (`PAPUAN_V2_METHODOLOGY_PIVOT_2026-10-02.md`), without installing CVAT, creating annotation tasks, training anything, or modifying the dataset: (a) what landmark schema the thesis should annotate, and (b) whether automatically generated landmarks should be shown to human annotators as CVAT proposals. A third question — whether Original and CLAHE branches both need independent manual annotation — was added because it is a prerequisite the first two gates depend on.

## 2. Research Context

Facial landmark/keypoint annotation (reviewed in CVAT) is now the primary annotation target for Papuan V2, superseding the emotion-label track (EXP-PAP-004), per supervisor (Pak Fadhil) clarification. The two parallel branches are: Original face crop → landmarks → CVAT review → training → Original landmark model; CLAHE face crop → landmarks → CVAT review → training → CLAHE landmark model.

## 3. Repository Files Inspected

`src/fer_dataset/pipeline/landmark_analyzer.py` (full read), `src/fer_dataset/pipeline/face_detector.py` (full read), `src/fer_dataset/shared/clahe.py` (full read), `src/fer_dataset/analysis/landmark_comparison.py` (full read), `tools/extract_arcface_embeddings.py`, `src/fer_dataset/pipeline/emotion_classifier.py` (kps-visualization section), `data/intermediate/landmarks_468/`, `data/papuan_v2/faces/` and `data/papuan_v2/clahe/` (direct dimension measurement on sampled pairs), `tests/test_papuan_clahe.py`, repo-wide greps for "dlib", "shape_predictor", "68", "class Landmark".

## 4. Existing Landmark Infrastructure (confirmed facts, not assumptions)

### A. MediaPipe Face Landmarker — exact output

- **478 points, not configurable to 468 in this code.** The Tasks API (`mp_vision.FaceLandmarkerOptions`) used here has no `refine_landmarks` flag at all (that belongs to the older `mp.solutions.face_mesh` API) — 478 is simply the Tasks API's unconditional default. The code's own comment (`landmark_analyzer.py:189`) notes "Tasks API returns 478 landmarks; first 468 keep mesh indexing," but **the code never separates or labels which indices are the 10 iris points** (conventionally 468–477, split left/right eye) — the array is saved whole, untagged.
- **Coordinate system:** pixel, not normalized — `landmarks_xy = [[lm.x * w, lm.y * h] for lm in landmarks]` where `w, h` are the face-crop's own array dimensions (`landmark_analyzer.py:183-187`).
- **Crop-relative, not original-image-relative** — confirmed by the same line: `w, h` come from the crop, never the source frame.
- **Storage:** one `.npy` file per crop, named by the crop's own filename stem (e.g. `frame_000008_face01.npy`) — a clean 1:1 mapping to `image_id`, no additional join logic needed.
- **Current usage of the 478 points:** the only downstream consumer (`_compute_features`) indexes points 13, 14, 33, 55, 61, 65, 263, 291 — all well under 468. **The 10 iris points (indices 468-477) are not used by anything in this codebase today.**

### B. InsightFace — exact output

- **5-point keypoints (`det.kps`), standard InsightFace/ArcFace convention** (left eye, right eye, nose, mouth-left, mouth-right) — this repo's own code never names the semantic order explicitly (it consumes `face.kps` straight from the library), so the order is taken on InsightFace's documented convention, not re-verified against custom repo code.
- **`face_detector.py` never reads or saves `.kps` at all** — true discard by omission, not an explicit delete.
- **Where `.kps` *is* actively used:** `ArcFaceONNX.get()` (called from `tools/extract_arcface_embeddings.py`) internally uses `kps` to drive `insightface.utils.face_align.norm_crop(...)` — i.e. the 5 points already do real work in this pipeline (ArcFace alignment), just never surface as a standalone landmark artifact.
- **New finding not in the prior audit:** the installed `buffalo_l` model bundle also ships `landmark_3d_68` and `landmark_2d_106` sub-models, confirmed by `extract_arcface_embeddings.py`'s own docstring explicitly excluding them via `allowed_modules` "for efficiency." **A 68-point (or 106-point) schema is available from the already-installed dependency with no new package required — it is simply not currently loaded.**

### C. 68-point/dlib schema — confirmed absent as implemented code

Zero hits for "dlib", "shape_predictor" anywhere in the repo. No dlib dependency. The only 68-adjacent artifact is InsightFace's unloaded `landmark_3d_68` sub-model (4.B above) — a 68-point option exists as a loadable capability, not as existing code/output.

### D. Face crop geometry (needed for Part 5)

Crops are variable-sized (not resized to a fixed dimension), bounding box padded 20% on all sides, no aspect-ratio normalization (`face_detector.py`). Measured directly: three sampled crops are `(58,72)`, `(65,94)`, `(116,108)` — confirming genuine per-face variability, not a fixed canvas.

### E. CLAHE geometry (the single most important fact for Part 5)

Read directly from `src/fer_dataset/shared/clahe.py`: CLAHE here is applied **only to the L (lightness) channel of LAB color space**, via `cv2.createCLAHE(...).apply(lab[:,:,0])`, then converted back to BGR. **No resize, crop, warp, or any geometric operation exists anywhere in this function.** The module's own docstring confirms this is an unchanged, verbatim-promoted transform from EXP-006 with a regression test (`tests/test_papuan_clahe.py`) guaranteeing output parity across its three copies in the codebase.

**Direct measurement, not inference:** sampled Original/CLAHE pairs for the same `image_id` have identical width/height (`(58,72)`/`(58,72)`, `(65,94)`/`(65,94)`, `(116,108)`/`(116,108)`). **Original and CLAHE crops for the same `image_id` are pixel-grid-identical; CLAHE changes brightness/contrast values at each `(x,y)` location but never moves, resizes, or warps anything.**

## 5. Landmark Schema Comparison (factual, not ranked)

| Dimension | 5-point (InsightFace) | 68-point (dlib-style / InsightFace `landmark_3d_68`) | 468-point (MediaPipe mesh) | 478-point (MediaPipe mesh + iris) |
|---|---|---|---|---|
| Annotation burden per image (manual correction in CVAT) | Lowest — 5 clicks/corrections | Moderate — 68 points, grouped by facial region, well-established manual-correction UX in most annotation tools | High — 468 points is a dense mesh, impractical to manually inspect/correct point-by-point for 645+ images | Highest — 10 more points than 468, same density problem plus 2 small, easily-mis-clicked iris regions |
| Human review complexity | Trivial to visually verify (sparse, semantically obvious points) | Moderate — well-known schema, many annotators/tools have built-in "68-point face" templates | High — a dense mesh is hard for a human to visually audit for small errors at typical image resolution | Highest — same mesh problem, plus iris points are tiny targets at this project's crop sizes (crops as small as 58×72 px measured directly) |
| Facial-expression information content | Low — only eye/nose/mouth-corner positions, no mouth-opening/eyebrow-shape detail | Good — standard schema used by many classic FER/AU-adjacent pipelines, covers brows, eye contour, nose, full lip contour, jaw | Very high — dense mesh captures subtle surface deformation (this codebase's own existing feature extractor already uses specific mesh points for brow-lowering/lip-corner/mouth-openness) | Same as 468 plus iris (gaze-adjacent, not expression-relevant per se) |
| Compatibility with MediaPipe (already installed, already run on 85/645 images) | Not MediaPipe's native output (would require re-deriving 5 points from the 478, or using InsightFace instead) | Not MediaPipe's native output | Native, and the existing 85-image extraction already produced this | Native, exact match to what already exists for 85/645 images |
| Compatibility with CVAT | CVAT supports arbitrary point/skeleton templates — 5-point is trivial to define | CVAT supports skeleton templates; a 68-point "face" skeleton is a common pre-built template in annotation tooling generally (not confirmed specifically for this project's CVAT instance, since none exists yet) | Technically importable as 468 unconnected points, but CVAT's skeleton/point UI is not designed for mesh-density annotation — no project evidence either way since CVAT isn't deployed | Same constraint as 468, plus 10 more points |
| Training complexity (regression target) | Simplest possible regression target (10 output values) | Moderate (136 output values), well-trodden in the broader FER/landmark literature as a standard target size | High-dimensional regression target (936 values), unusual for a 645-image dataset to learn without heavy overfitting risk | Same as 468 plus 20 more values |
| Fit for a 645-image dataset | Very good — low-dimensional target is easiest to learn from a small dataset without overfitting | Good — 68-point regression on small datasets is common in the literature; still demanding relative to dataset size, but well-precedented | Risky — a 936-dimensional (468×2) output space learned from ~645 images (before train/val/test split shrinks this further) is a substantial overfitting risk with no existing precedent in this repo's training code (which so far is a linear classifier on fixed embeddings, not a coordinate regressor) | Same risk as 468, marginally worse |
| Suitability for an Original-vs-CLAHE thesis comparison | Workable but information-poor — may not show much difference between branches since so little geometry is captured | Reasonable middle ground — enough facial detail to potentially show a CLAHE effect, without the annotation burden of a full mesh | Most information-rich if annotation effort is solvable, but the annotation burden (above) is a serious practical constraint this project would have to solve, not assume away | Same as 468, iris points add preprocessing-irrelevant cost |

## 6. Is 478 Points (Specifically the 10 Iris Points) Necessary?

No evidence found that it is, for this project's stated FER-preprocessing/landmark use case specifically. Three independent, concrete reasons: (1) the existing feature-extraction code in this same codebase (`landmark_analyzer._compute_features`) already ignores indices 468-477 entirely, using only mesh points well under 468 for its brow/lip/mouth-openness features; (2) iris position is a gaze-direction signal, not a facial-expression signal — nothing in the stated research question (Original vs. CLAHE landmark model comparison for FER preprocessing) calls for gaze information; (3) iris points are the smallest, most annotation-error-prone targets at this project's actual crop sizes (measured as small as 58×72 pixels) — adding manual-correction burden for a signal the project doesn't use elsewhere. This points toward 468 (mesh only, dropping the 10 iris points) being the more defensible ceiling if a dense-mesh schema is chosen at all — but see the explicit recommendation and its assumptions below.

## 7. Recommended Schema — Explicit Recommendation With Stated Assumptions and Trade-offs

**Recommendation, not a unilateral decision:** a **68-point schema** (loaded from InsightFace's already-installed `landmark_3d_68` sub-model, requiring no new dependency — just enabling a currently-excluded `allowed_module`) is the most defensible starting point for this thesis, under these explicit assumptions:
- *Assumption 1:* the thesis's goal is to compare Original-vs-CLAHE landmark model quality/behavior, not to produce a dense, publication-grade face mesh — if the latter is actually the goal, this recommendation does not hold and 468-point should be reconsidered despite its overfitting/annotation-burden risk.
- *Assumption 2:* 645 total images (before any train/val/test split) is treated as a small-dataset regime where a lower-dimensional regression target is safer — if the dataset is expected to grow substantially before training, this trade-off shifts.
- *Assumption 3:* manual CVAT correction time scales roughly with point count — if CVAT's specific UI makes dense-mesh correction faster than expected (unverified, since CVAT isn't deployed), the annotation-burden argument weakens.

**Trade-off being made explicitly:** this recommendation sacrifices some facial-expression information density (68-point captures less subtle deformation than a 468-point mesh) in exchange for annotation feasibility and training-dataset-size appropriateness. **This is a recommendation to bring to Pak Fadhil, not a conclusion to implement unilaterally** — the schema choice materially affects CVAT project configuration and cannot be cheaply changed later.

## 8. AI Proposal Methodology Comparison (Option A: blank vs. Option B: AI-proposal-then-correct)

| Dimension | Option A — blank annotation | Option B — AI proposal (MediaPipe or InsightFace) → human correction |
|---|---|---|
| Annotation efficiency | Slowest — every point placed from scratch per image | Faster — human adjusts an already-plausible starting position rather than placing from nothing |
| Human error | Lower anchoring risk, but higher raw placement-error variance (humans are less precise at freehand point placement than at nudging a pre-placed point) | Lower raw placement error (small nudges are easier to get right than cold placement), but see anchoring bias below |
| Anchoring bias | Not applicable — no AI signal present to anchor on | Present and directionally well-established in human-AI collaboration research generally (already discussed for the emotion track's AI-assisted-annotation design, `PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`): a human is less likely to catch a subtly-wrong AI-placed point than to independently derive the correct position from scratch, because confirming a plausible-looking point requires less scrutiny than generating one |
| Systematic model bias | Not inherited — whatever error pattern blank human annotation has is independent of any specific model's failure modes | Inherited risk — if MediaPipe (or InsightFace) has a systematic placement bias for certain face shapes/lighting conditions (plausible, untested here), uncorrected instances of that bias could persist into the "human-reviewed" output at a higher rate than fully independent annotation would produce |
| Provenance | Simple — every point's position has exactly one source: the human | Must be tracked explicitly — which points were AI-proposed-and-accepted-unchanged vs. AI-proposed-and-corrected vs. (if applicable) no-AI-fallback; without this tracking, "human-reviewed" becomes an unverifiable claim |
| Can the result reasonably be called "human-reviewed ground truth"? | Yes, unambiguously | Conditionally — only if correction was substantive (not rubber-stamping) and this is verifiable via the provenance tracking above; without that tracking, the claim is asserted, not demonstrated |
| Thesis methodology implications | Cleanest possible claim of independent human judgment; costs more annotator time | Faster, but requires the thesis to explicitly disclose the AI-proposal source and ideally report an acceptance/correction-rate statistic, or risk an examiner challenging whether "human-reviewed" is actually independent |
| Can the proposal model be evaluated independently later? | Yes, trivially — the proposal model (if used to generate predictions after the fact) was never in the loop | Only if the proposal model is *different* from whatever model is later evaluated as part of the FER preprocessing pipeline — see Part 9 (circularity) below; otherwise the "independent evaluation" claim is compromised |

**Explicit terminology distinction, as required:** an **"AI-generated proposal"** is the raw MediaPipe/InsightFace output before any human sees it — it is a model prediction, nothing more. A **"human-reviewed annotation"** is what exists after a human has looked at and potentially corrected a proposal (or placed points from blank) — this is a process description, not a quality guarantee. **"Ground truth"** is the status this project intends to assign to the *final*, reviewed annotation for training purposes — but **a human-reviewed AI proposal is not automatically equivalent to fully independent human annotation**; the gap between them is exactly the anchoring-bias risk in the table above, and whether that gap is acceptable is a methodological judgment call, not a fact this audit can resolve unilaterally.

## 9. Circularity / Data Leakage Analysis

**The core risk, stated precisely:** if a model's own output is used to generate the annotation proposal, and a human's correction behavior is biased toward accepting that proposal (per the anchoring-bias risk above), then training a model on the resulting "ground truth" and evaluating that same model's accuracy against it is partially circular — the evaluation partly measures whether the model agrees with its own prior output, filtered through imperfect human correction, not independent accuracy.

**This project's specific circularity exposure depends on what the trained landmark model is later used for:**
- If the trained Original/CLAHE landmark models are **only** evaluated against each other (Original vs. CLAHE comparison) and never re-inserted as a preprocessing step whose output is then re-evaluated against human-reviewed labels that *that same model* (or its proposal-generation ancestor) helped produce, the circularity risk is lower — the two trained models are downstream consumers of the annotation, not participants in generating it.
- If, however, the landmark model is later used **as part of the FER preprocessing pipeline** (as the pivot documentation anticipates — landmarks feed the broader FER pipeline, same as the existing MediaPipe-derived emotion-proxy features do today) and that pipeline is evaluated using labels whose underlying landmarks were originally proposed by the *same family* of model (MediaPipe, if MediaPipe both proposes training-time landmarks and is the architecture trained), the exposure is direct and analogous to the already-identified emotion-track risk (using HSEmotion to pre-label data that HSEmotion is later evaluated against).

**Risk comparison across the three candidate proposal sources, as requested:**

| Proposal source → training path | Circularity risk | Reasoning |
|---|---|---|
| MediaPipe proposal → human correction → training a landmark model (if that model's architecture/purpose overlaps with MediaPipe's role in the pipeline) | **Highest** | Same model family generates the proposal and is the trained/evaluated artifact — the clearest case of self-referential evaluation, directly analogous to the already-flagged HSEmotion/ArcFace emotion-track risk. |
| InsightFace proposal → human correction → training a landmark model | **Lower, but not zero** | InsightFace's 5-point detector is architecturally distinct from a landmark-regression model trained from scratch on these annotations, reducing direct self-reference — but if InsightFace's 5 points are themselves later used anywhere in the same evaluation chain (e.g. as an alignment step the trained model's output is compared against), a subtler, second-order circularity could still exist; this project's current code does use `kps` for ArcFace alignment, which is a different purpose than landmark-model evaluation, so this specific path is not currently active, but should be kept in mind if the pipeline design changes. |
| Blank annotation → human annotation → training | **Lowest** | No model participates in generating the ground truth at all; whatever is later trained and evaluated has no shared ancestry with the labels it's measured against. |

**Concrete recommendation to keep the experiment scientifically defensible:** if an AI proposal is used at all (Option B above), prefer **InsightFace's 5-point output or a lower-risk third-party source over MediaPipe** specifically because MediaPipe is the tool whose output already feeds this codebase's existing emotion-proxy feature pipeline and is the most likely candidate to also become (or inform) the trained landmark model's architecture — using it to generate training-time proposals as well risks the direct self-reference case in the table above. If MediaPipe-sourced proposals are used anyway (e.g. because InsightFace's 5 points are too sparse to meaningfully speed up 68-point annotation), the thesis should explicitly disclose this and, ideally, report an AI-acceptance/correction-rate statistic as partial mitigation — the same disclosure principle already established for the emotion track's AI-assisted-annotation design review.

## 10. Original vs. CLAHE Annotation Analysis — Critical Design Decision

**Direct evidence (Section 4.E above) resolves the geometric half of this question unambiguously:** CLAHE in this codebase is a pure per-pixel L-channel intensity transform with no resize, crop, or warp — confirmed by code inspection and direct pixel-dimension measurement on sampled pairs (identical width/height for every pair checked). **CLAHE does not and — given this implementation — cannot change where a facial landmark sits in pixel coordinates**, because it never moves any pixel; it only changes that pixel's lightness value.

**This means the "annotate once, transform deterministically" alternative is not merely viable but is, for this specific CLAHE implementation, the identity transform** — a landmark annotated at pixel `(x, y)` on the Original crop is, by construction, already at pixel `(x, y)` on the CLAHE crop for the same `image_id`, with no coordinate math required at all (not even a scaling/affine step — truly identical coordinates).

**Comparison:**

| | Annotate once (Original) + reuse coordinates for CLAHE | Independent annotation on both Original and CLAHE |
|---|---|---|
| Annotation effort | Half — only one branch is manually annotated | Double — both branches independently annotated |
| Consistency | Perfect by construction — the same coordinates, no human-to-human or session-to-session variation between branches | Subject to normal human annotation variance between the two passes, even for the same underlying face geometry — any difference observed between Original-branch and CLAHE-branch "ground truth" would be annotation noise, not a real effect |
| Scientific validity | High, provided the geometric-identity claim is true (verified above for this specific CLAHE implementation) and documented with the supporting evidence | Only adds value if there is a real hypothesis that lightness/contrast changes could cause a human (or a model) to perceive/place landmarks differently — see below |
| Does CLAHE change geometry? | No (directly verified, Section 4.E) | N/A |
| Should CLAHE theoretically change landmark coordinates? | No, under a pure intensity-transform definition — there is no theoretical mechanism by which changing lightness values alone would move where an eye corner or mouth corner physically is in the pixel grid | N/A |
| Is independent annotation of both branches necessary? | **Not for establishing ground-truth landmark positions**, given the above. **It could still be a separate, deliberate experimental question** — e.g. "does CLAHE's contrast enhancement improve or degrade a *model's* landmark-prediction accuracy," which is a model-behavior question answerable by training two models on the *same* (reused) coordinates against Original vs. CLAHE pixel input, not by re-annotating. | |

**Recommendation:** reuse the Original branch's annotated coordinates as the CLAHE branch's training target (identity-mapped, no transform needed), and do **not** independently annotate CLAHE crops. This halves annotation effort without sacrificing validity, given the verified geometric-identity property of this specific CLAHE implementation. The Original-vs-CLAHE *comparison* then becomes a question about how well a model trained/evaluated on each **input** (Original pixels vs. CLAHE pixels) predicts the **same** target coordinates — a cleaner, more directly interpretable comparison than one confounded by two independently-noisy annotation passes. **This recommendation should still be confirmed with the supervisor**, since it changes the originally-envisioned two-independent-annotation-branches design into a single-annotation/two-training-input design — a meaningful methodological simplification that the supervisor may want to explicitly approve rather than discover after the fact.

## 11. Recommended Annotation Protocol (practical, minimal)

1. **Landmark schema:** 68 points (Section 7's recommendation), pending supervisor confirmation.
2. **Number of landmarks:** 68.
3. **Landmark semantics:** standard 68-point face schema (jawline, eyebrows, nose bridge/base, eye contours, outer/inner lip contour) — the conventional ordering associated with this point count in the broader face-landmark literature; exact index-to-semantic mapping should be pinned down from whichever concrete source (InsightFace's `landmark_3d_68` output ordering) is actually used, not assumed from a different library's convention, when implementation begins.
4. **Coordinate convention:** pixel coordinates, crop-relative (consistent with the existing MediaPipe code's convention, Section 4.A) — not normalized, to avoid an extra conversion step and avoid introducing a second coordinate convention into the project.
5. **Original vs. CLAHE relationship:** annotate Original only; CLAHE training target = identical coordinates (Section 10) — no independent CLAHE annotation pass.
6. **AI proposals visible to annotators:** open question requiring supervisor confirmation (Section 8/9); if used, prefer InsightFace-derived or another lower-circularity-risk source over MediaPipe for the reasons in Section 9, and track acceptance/correction explicitly (next point).
7. **Valid human correction:** any annotator adjustment to a proposed point's position counts as a correction; a point left completely unmoved should be explicitly recorded as "accepted-as-proposed" (not silently indistinguishable from "corrected") so the acceptance-rate statistic in Section 9 is actually computable later.
8. **Review procedure:** reuse this project's existing precedent — a single primary annotation pass, with a smaller deterministic overlap/audit subset reviewed by a second person (the same overlap-and-audit pattern already built for EXP-PAP-004, not a new invention) — exact overlap fraction/size is an implementation decision, not resolved here.
9. **Annotation provenance:** per point (or per image, whichever CVAT's export naturally supports): `proposal_source` (none / mediapipe / insightface), `human_action` (placed-from-blank / accepted-as-proposed / corrected), `annotator_id` (real identity, never faked — same convention as the emotion track), `review_status`.
10. **Quality-control rules:** reuse the existing project convention of a hard-enforced guard script that refuses to proceed to training if any required field is missing or any annotator identity is unresolved — mirroring `human_agreement_report.py`'s existing "refuse to run on incomplete data" pattern, not a new QC mechanism.
11. **Missing/occluded landmarks:** mark explicitly as "occluded/not visible" rather than guessing a plausible position — a dedicated flag per point (or per image, if occlusion is whole-face) is simpler and more honest than forcing every point to have a coordinate.
12. **Export format:** CVAT's native export (format choice — e.g. CVAT XML vs. COCO-keypoints — is an implementation detail to decide once CVAT is actually deployed; not resolved here since CVAT doesn't exist in this environment yet).
13. **Annotations → training targets:** reviewed Original-branch coordinates become the direct regression target for Model A; the same coordinates (no transform, per Section 10) become the regression target for Model B trained on CLAHE pixel input.

## 12. Pilot Experiment Proposal

**Proposed ID, pending confirmation this fits the project's convention:** `EXP-PAP-005` (the next free number in the existing single-track `EXP-PAP-NNN` sequence — see `PAPUAN_V2_METHODOLOGY_PIVOT_2026-10-02.md`'s experiment-ID section; a `-LM-` sub-prefix was also proposed there as an alternative, not re-decided here). **Not created yet.**

- **Sample size for pilot:** a small subset of the 150-image EXP-PAP-004 pilot set is a reasonable starting point (reusing an already-curated, already-lineage-tracked image set rather than drawing a new sample) — exact count (e.g. 20-30 images) should be small enough to validate the workflow quickly without committing significant annotator time before the schema/AI-proposal questions are confirmed.
- **Annotation workflow:** Original-only annotation (per Section 10), using the confirmed schema (Section 7), with or without AI proposals per the supervisor's confirmation (Section 8/9).
- **Validation/review:** a small deterministic overlap subset (e.g. half the pilot) reviewed by a second person, mirroring the existing EXP-PAP-004 overlap pattern.
- **Output artifacts:** a landmark CSV/JSON per the minimal schema in `PAPUAN_V2_METHODOLOGY_PIVOT_2026-10-02.md` Part 6 (`image_id`, `source_image_id`, `preprocessing`, `landmark_schema`, `landmark_coordinates`, `annotation_status`, `annotator`, `review_status`), plus a CVAT export in whatever format is chosen at implementation time.
- **Success criteria:** 100% of the pilot sample has a reviewed annotation with no missing required fields; overlap-subset agreement (e.g. mean pixel distance between the two reviewers' corrected positions) is computed and inspected for obviously-unreasonable variance before scaling up.
- **What should happen before scaling from pilot to all 645 images:** (1) confirm the schema and AI-proposal decisions with the supervisor using this pilot's actual experience, not just the abstract analysis above; (2) confirm CVAT's chosen export format actually round-trips cleanly into the minimal metadata schema; (3) only then commit to annotating the remaining ~615-620 images.

## 13. Open Questions

- Final landmark schema confirmation (68-point recommended, not decided).
- Final AI-proposal-visibility decision (not decided; circularity analysis favors avoiding MediaPipe-as-proposal-source if AI proposals are used at all).
- Exact 68-point semantic-index mapping, pinned to whichever concrete source is actually implemented (not yet implemented).
- CVAT deployment specifics (local Docker Compose assumed consistent with the project's existing "nothing leaves this machine" pattern, not yet set up).
- Exact overlap/review fraction for the pilot and full-scale phases.
- Status of Annotator B's still-standing, still-unused emotion-track Label Studio infrastructure (carried over from the prior pivot report, still unresolved).

## 14. Decisions Now Resolved (by direct evidence in this investigation)

- **CLAHE does not change pixel geometry** for any landmark in this codebase's implementation — confirmed by code inspection and direct measurement. This resolves the "does CLAHE change geometry" question definitively, for this implementation.
- **Independent CLAHE annotation is not scientifically required** to establish ground-truth landmark positions, given the above — recommended against, though this recommendation (not the underlying geometric fact) still benefits from supervisor sign-off since it changes the originally-envisioned two-branch annotation design.
- **A 68-point schema is obtainable from already-installed dependencies** (InsightFace's `landmark_3d_68`) with no new package required — removes "do we need a new dependency" as an open question.
- **The 10 MediaPipe iris points are not used by anything in this codebase today** and add annotation cost without a corresponding, currently-realized use case.

## 15. Decisions Still Requiring Supervisor Confirmation

1. Final landmark schema (68-point recommended; 478/468-point remains viable if the thesis's actual goal calls for mesh-level detail despite the annotation-burden/overfitting trade-offs).
2. Whether AI proposals are shown to annotators at all, and if so, which source (InsightFace preferred over MediaPipe on circularity grounds, per Section 9).
3. Confirmation that the Original-only-annotation-with-coordinate-reuse design (Section 10) is an acceptable substitution for the originally-envisioned two-independent-annotation-branches design.
4. The still-open question (carried over) of whether Annotator B's standing emotion-track infrastructure should be paused or kept available.

## 16. Exact Next Implementation Step

Bring Sections 7, 9, and 10's recommendations to Pak Fadhil for confirmation. Only after that confirmation: begin CVAT deployment planning (a separate, later implementation prompt) — not part of this investigation.

## 17. Date/Time

2026-10-02.

## 18. Current Git Branch

`main` (confirmed via `git branch --show-current` at the start of this task; the prior audit/pivot work originally lived on `worktree-papuan-v2-audit` and was ported to `main` as a plain file copy earlier in this task, per explicit user instruction — not merged or cherry-picked).

## 19. Changes Made

- This report file: `docs/reports/PAPUAN_V2_LANDMARK_SCHEMA_AND_ANNOTATION_METHOD.md` (new).
- `docs/reports/PAPUAN_V2_CURRENT_STATE.md` (appended — see that file's new dated section).
- `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md` (appended — new milestone entry).
- Earlier in this task, as a separate, explicitly-requested action: the 11 pre-existing `docs/reports/*.md` files were copied (plain file copy, not a git merge) from `worktree-papuan-v2-audit` onto `main` and committed (commit `de3c238`).

## 20. Changes NOT Made

No CVAT installation, no Docker Compose file, no CVAT project or task, no landmark annotation collected, no model training, no dataset modification, no Label Studio changes, no deletion of any exploratory/superseded work, no experiment directory created (`EXP-PAP-005` is proposed, not created), no automatic commit of today's new/updated report content (per the standing "do not commit or push automatically" rule — only the earlier, explicitly-requested historical-report port was committed).

---

*Investigation only. No CVAT, training, or dataset changes were made in producing this report.*
