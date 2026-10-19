# PAPUAN V2 Dataset Standardization — Audit & Proposal

**Date:** 2026-10-19
**Status:** Audit complete, no implementation performed. Awaiting supervisor confirmation on open decisions in §8.
**Scope:** Read-only inspection of the repository to assess readiness for a standardized, Google-Drive-deliverable, supervisor-facing FER dataset package. No code, data, or pipeline runs were modified as part of this audit.

---

## 1. Audit scope and method

Inspected: all scripts under `tools/papuan_v2/`, `tools/realtime_demo/`, `src/fer_dataset/pipeline/`; manifest/CSV/JSON artifacts under `experiments/EXP-PAP-004/`, `experiments/EXP-PAP-005/`, `experiments/EXP-DASH-001-landmark-fer/`; all 17 files under `docs/reports/PAPUAN_V2_*.md` plus `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md`, `docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md`, `docs/EXPERIMENT.md`; `pyproject.toml`; `config/config.yaml`; test suite under `tests/`; git log for `tools/papuan_v2` and `docs/reports`. No file was modified, no script executed, no data moved or deleted.

Findings below are tagged **[VERIFIED]** (read directly from a file) or **[ASSUMPTION]** (inferred, not directly confirmed in any artifact).

---

## 2. What already exists and is reusable

### 2.1 Pipeline stages implemented today

| Stage | Status | Evidence |
|---|---|---|
| Frame extraction | **[VERIFIED]** implemented | `src/fer_dataset/pipeline/` `FrameExtractor`, reused unmodified by `tools/papuan_v2/build_pilot_source.py` |
| Face detection | **[VERIFIED]** implemented | `FaceDetector` (same pipeline module), InsightFace-backed |
| Face cropping | **[VERIFIED]** implemented | crops written to `data/papuan_v2/faces/` |
| CLAHE generation | **[VERIFIED]** implemented, tested | `tests/test_papuan_clahe.py`; params `clip_min=1.5, clip_max=3.5, l_min=60, l_max=220, tileGridSize=(8,8)`; verified pure L-channel transform, zero geometric change on all 645 pairs |
| Landmark prediction (initial) | **[VERIFIED]** implemented | InsightFace `landmark_3d_68` sub-model (`1k3d68.onnx`, buffalo_l bundle), x/y used, z discarded |
| Landmark annotation review | **[VERIFIED]** implemented, partially executed | CVAT-based correction workflow; 64/645 crops reviewed, 40 more AI-initialized but not yet reviewed |
| Expression-label annotation | **[VERIFIED]** implemented, partially executed | Label Studio dual-annotator workflow; 150/150 complete for Annotator A, 0/75 for Annotator B |
| Quality filtering | **[VERIFIED]** NOT implemented as an exclusion rule | only descriptive statistics exist (blur variance, dimension percentiles over 645 images); `config/config.yaml`'s `quality.min_face_size`/`quality.blur_threshold` keys are present but confirmed dead/unused (`docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md:79`) |

**Conclusion:** every required pipeline stage has a working implementation except quality filtering, which exists only as characterization, not as an applied filter. This is consistent with the existing docs' own conclusion (`PAPUAN_V2_DATASET_QUALITY_AUDIT.md`: *"No numeric quality threshold was set"*).

### 2.2 Dataset scale as of this audit **[VERIFIED]**

- 645 face crops extracted (+645 CLAHE counterparts), from a single source video (`pesta_babi.mp4`).
- Emotion-label pilot (`EXP-PAP-004`): 150 images sampled (seed=42); Annotator A complete (150/150, distribution Neutral 93 / Happy 31 / Sad 13 / Surprise 8 / Angry 4 / Fear 1); Annotator B infrastructure deployed but 0/75 completions (confirmed via SQLite read of the idle Label Studio instance).
- AI baseline predictions generated for all 150 pilot images under two models (HSEmotion 8-class, ArcFace+LogisticRegression 5-class) — disclosed class-set asymmetry, not yet reconciled.
- Landmark track (`EXP-PAP-005`, current primary track since 2026-10-02 pivot): 104/645 crops landmark-initialized, 64 reviewed (24-image pilot seed=200 + 40-image calibration batch seed=300), 40 more AI-initialized but unreviewed (Batch 3, seed=500).
- First landmark regression baseline (Ridge, 32×32 grayscale → 136-dim output, 45/11/8 split, 64 images) performs statistically indistinguishable from a content-blind mean-shape baseline — explicitly reported as inconclusive, not hidden.

### 2.3 Tooling maturity vs. dataset maturity

Tooling (14 scripts, full test suite, two isolated Label Studio deployments, CVAT-based review pipeline with audit-trail preservation) is substantially more mature than the dataset itself. Of 645 extracted crops: 150 have one annotator's emotion label, 64 have reviewed landmarks. The project has invested heavily in *process correctness* (annotator blindness, no-leakage guards, deterministic sampling, audit-trail preservation) ahead of *volume*.

---

## 3. Metadata gaps

### 3.1 No unified extraction manifest **[VERIFIED]**

Provenance is currently split across two non-joined artifacts:

- `source_video_manifest.json` — **video-level only**: SHA-256, original FPS, total frame count, sampling config (target FPS, frame interval, max frames). One record for the whole video.
- `pilot_manifest.csv` — **pilot-selection-level only**: `image_id, face_filename, source_face_path, source_clahe_path, pilot_image_path, sample_seed, sampled_at`. No bounding box, no detected-face-count, no detector confidence, no tool/model version, no distinction between original-video frame index and sampled-frame index.

There is no per-crop record joining video provenance → frame → detected face → bbox → crop. This is the single largest gap relative to the target manifest in the task brief (§2A).

### 3.2 No person_id / identity tracking **[VERIFIED — confirmed absent, not merely unimplemented]**

Grepped across the full codebase and manifests: no `person_id`, `track_id`, or identity field exists anywhere. This is explicitly stated as a known limitation in three independent docs (`docs/ARCFACE_EXPERIMENT_DESIGN.md:138`, `docs/thesis-latex/research-audit/DATA_DICTIONARY.md:18`, `docs/EXPERIMENT.md:375`) and in `tools/train_arcface_classifier.py:155-157`. The `face_NN` suffix in `frame_000037_face01.jpg` is a per-frame detection index, reset per frame — **not** a cross-frame identity, exactly as flagged in the task brief. Current ML work substitutes a frame-adjacency proxy (consecutive-frame blocks of 3) for identity-grouped cross-validation splits, which is disclosed as weaker than true identity grouping.

### 3.3 Landmark original-vs-reviewed provenance **[VERIFIED — already preserved]**

This one is in good shape: original (InsightFace) and reviewed (CVAT) landmark sets are stored as **separate, never-overwritten JSON files** per batch (e.g. `insightface_68pt_pilot_predictions.json` vs. `cvat_reviewed_landmarks.json`). The CVAT export pipeline deliberately snapshots both pre- and post-review states for auditability, even though CVAT's own live DB holds only the current state. Per-image/per-region change statistics already exist (e.g. 220/1,632 points changed in the 24-image pilot, 13.5%, mean displacement 10.3px).

One caveat worth flagging to the supervisor: in the 40-image calibration batch, 6 of 11 "corrected" images show a bit-identical rigid whole-skeleton translation rather than per-point judgment — meaning some fraction of "reviewed" status reflects a coarse shift, not fine-grained correction. This is already disclosed in `PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md`.

### 3.4 Minor terminology inconsistency **[VERIFIED]**

`dashboard/appearance_simulation.js` comments reference "face-api.js 68-point landmarks," while the actual pipeline uses InsightFace's `landmark_3d_68`. Functionally the same 68-point array shape, but ordering has not been independently pixel-verified as identical between the two naming conventions. Low-risk (dashboard-only, not thesis pipeline), but worth a one-line fix for clarity.

---

## 4. Landmark schema — verified index mapping

Cross-checked across `PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md`, `PAPUAN_V2_CVAT_LANDMARK_PILOT.md`, and `PAPUAN_V2_LANDMARK_SCHEMA_AND_ANNOTATION_METHOD.md` — all three agree, no discrepancy found.

**Current production schema: full 68-point iBUG-300W/dlib-style convention**, sourced from InsightFace `landmark_3d_68` (x/y only, z discarded):

| Region | Indices | Count |
|---|---|---|
| Jaw | 0–16 | 17 |
| Right eyebrow | 17–21 | 5 |
| Left eyebrow | 22–26 | 5 |
| Nose bridge | 27–30 | 4 |
| Nose base (tip = 33) | 31–35 | 5 |
| Right eye | 36–41 | 6 |
| Left eye | 42–47 | 6 |
| Mouth outer | 48–59 | 12 |
| Mouth inner | 60–67 | 8 |

**Target subset per task brief** (eyebrows + eyes + mouth, excluding nose/jaw) maps cleanly onto this existing index space:

| Target region | Source indices | Count |
|---|---|---|
| Right eyebrow | 17–21 | 5 |
| Left eyebrow | 22–26 | 5 |
| Right eye | 36–41 | 6 |
| Left eye | 42–47 | 6 |
| Mouth (outer+inner) | 48–67 | 20 |
| **Total** | | **42** |

This matches the task brief's target counts exactly (10 eyebrow + 12 eye + 20 mouth = 42). **No remapping or reprediction is required** — the subset is a pure column-selection filter (`{17..26, 36..47, 48..67}`) applied to the existing 68-point arrays, for both the InsightFace originals and the CVAT-reviewed sets. Jaw (17 pts) and nose (9 pts) are simply dropped, not renumbered — I recommend keeping original 68-point index values as a `source_index` field in the 42-point output rather than renumbering 0–41, so the subset stays traceable back to the full schema and to any future re-review.

**Caveat carried forward from the docs, not independently re-verified by me:** "left"/"right" is subject-anatomical, assumes a non-mirrored source video. Worth a quick manual check on a few frames before finalizing.

**CVAT export pitfall** (relevant to any reproduction/automation): CVAT's `elements` array is not ordered by point index — must join by `label_id`, not array position.

---

## 5. Image variants and annotation traceability

Per task brief §2D, each face sample should be traceable to: original crop, CLAHE crop, initial landmarks, reviewed landmarks, validated expression label.

Current state **[VERIFIED]**:
- Original crop ↔ CLAHE crop: joined via `sample_id` (= filename stem), 1:1, geometry-identical — confirmed on all 645 pairs.
- Initial landmarks ↔ reviewed landmarks: joined via `image_id` across separate JSON files — exists for 64/645 samples only (104 initialized, 40 pending review).
- Expression label: exists for 150/645 samples (Annotator A only); 0 samples have two independent annotations (Annotator B incomplete) so inter-annotator agreement cannot currently be computed for any sample.

**Gap:** there is no single manifest row per `sample_id` that joins *all five* artifact types with explicit status flags. Each pipeline stage currently has its own manifest with its own key column, and joining requires knowing which files to look up by convention rather than reading one authoritative table. This is the core "main sample manifest" gap the task brief's §4A/§4(04_Labels_and_Manifest) is asking to close.

---

## 6. Quality control — current state vs. target

**[VERIFIED]** No QC threshold is implemented as an exclusion rule anywhere in the pipeline. What exists:
- Blur variance (`cv2.Laplacian(...).var()`) computed once, dataset-wide, as characterization only (not a filter).
- Dimension statistics: width min 22px / median 67px / max 697px; area median ≈6,097px²; 0/645 aspect-ratio outliers.
- `PAPUAN_V2_DATASET_QUALITY_AUDIT.md` explicitly declines to set a numeric threshold, citing insufficient reviewer-grounded data, and proposes three unadopted options (A: dimensional threshold, B: CVAT "uncertain" flag, C: training-set exclusion), recommending B first.
- The CVAT uncertainty mechanism (`occluded`/`outside` flags, a `review_status` tag) exists in the schema but was **never used** — 0/2,720 reviewed points flagged occluded to date.

This matches the task brief's own instruction not to invent thresholds and to run a small visual pilot first — the existing docs already reached the same conclusion independently. No contradiction to resolve here, just execution.

---

## 7. Proposed design

### 7.1 Standardized directory structure (proposal, not yet created)

```
papuan_v2_standardized/
  manifests/
    extraction_manifest.csv       # video -> frame -> face -> bbox -> crop, one row per detection
    sample_manifest.csv           # one row per sample_id, joins all artifact types + status flags
    person_registry.csv           # person_id -> evidence, confidence, assignment method
    exclusion_manifest.csv        # sample_id, reason, measured_value, threshold, filter_version
  images/
    original/{sample_id}.jpg
    clahe/{sample_id}.jpg
  landmarks/
    initial_68pt/{sample_id}.json
    initial_42pt/{sample_id}.json   # derived subset, source_index preserved
    reviewed_68pt/{sample_id}.json
    reviewed_42pt/{sample_id}.json
  labels/
    expression_labels.csv         # sample_id, annotator, label, confidence, verified
  qc/
    quality_metrics.csv           # per-sample blur, size, dims — descriptive, pre-filter
    pilot_threshold_study/        # visual pilot used to set thresholds, see §7.5
```

This is additive over existing `data/papuan_v2/` — a derived, standardized view generated from existing artifacts, not a replacement of raw pipeline outputs.

### 7.2 Manifest schemas (minimum required fields)

**`extraction_manifest.csv`** (one row per detected face, per the task brief §2A):
`video_id, video_path, video_sha256, video_fps, video_width, video_height, video_duration_s, sampling_fps, source_frame_index, sampled_frame_index, frame_timestamp_s, faces_in_frame, face_index_in_frame, bbox_x, bbox_y, bbox_w, bbox_h, crop_w, crop_h, detector_model, detector_version, run_id, run_config_hash, sample_id`

**`sample_manifest.csv`** (one row per sample_id, the "join everything" table):
`sample_id, person_id, person_id_confidence, has_original_crop, has_clahe_crop, has_initial_landmarks, has_reviewed_landmarks, landmark_schema_version, landmark_reviewer, landmark_review_status, has_expression_label, expression_label, expression_label_annotator, expression_label_verified, qc_status, qc_exclusion_reason`

**`person_registry.csv`**: `person_id, first_sample_id, last_sample_id, sample_count, assignment_method (tracking|reid|manual), confidence, needs_review`

**`exclusion_manifest.csv`** (per task brief §2E): `sample_id, exclusion_reason, measured_value, threshold_used, filter_version, excluded_at` — excluded samples stay in `images/` and are only flagged here, never deleted.

### 7.3 ID conventions and identity-tracking strategy

Keep the existing `frame_{idx:06d}_face{NN}` filename convention (it already works, is in wide use, and the brief explicitly endorses it) but make `sample_id` the canonical join key everywhere (already the de facto convention — just needs to be made explicit as policy) and add `person_id` as a **separate, derived** field, never conflated with the face-suffix.

**Recommended approach for identity tracking**, given the brief's instruction not to assign confident identities without evidence:
1. **Tracking first** (e.g. IoU/centroid tracking across consecutive sampled frames, or a lightweight tracker like ByteTrack/SORT on the full un-sampled video) to link detections within unbroken sequences. This handles the common case cheaply.
2. **Re-identification (ArcFace embeddings, already a pipeline dependency) for sequence-break resolution** — when tracking drops (occlusion, missed detection, re-entry), use embedding similarity to propose a merge, above a conservative similarity threshold.
3. **Human review required for**: any re-ID merge below high confidence, any scene cut, and a random audit sample of high-confidence merges to estimate error rate.
4. **Uncertain identities get `person_id = null` with a `needs_review` flag**, never a guessed ID. A single-video dataset with likely few distinct people is a favorable case for this, but it must still be validated, not assumed — I have not inspected the video content and cannot state how many distinct people appear.

**[ASSUMPTION]** I have not verified how many people appear in `pesta_babi.mp4` or how much occlusion/scene variation it contains — this materially affects whether tracking alone will suffice. This should be checked (by a human watching representative clips, or a quick tracking dry-run) before committing to a specific re-ID threshold.

### 7.4 Landmark schema and index mapping

Use the 42-point subset defined in §4, generated as a column-selection filter over existing 68-point arrays (both initial and reviewed). No recomputation needed for already-reviewed samples. Preserve `source_index` (0–67) in the 42-point output rather than renumbering, so results stay traceable to the full schema.

### 7.5 Quality control rules and pilot methodology

Do not set thresholds from this audit. Recommend:
1. A visual pilot of ~40–60 images spanning the existing blur-variance and dimension-percentile range (stratified sampling from the 645, not random) reviewed by a human to label "acceptable" / "borderline" / "reject."
2. Fit a threshold to that pilot's human judgments (e.g. ROC-style cutoff on blur variance against the human labels) rather than picking a round number.
3. Apply the resulting threshold as `filter_version: v1`, log every excluded sample in `exclusion_manifest.csv` with its measured value, never delete source files.
4. Separately flag (not exclude) samples with missing/incomplete landmarks or missing expression labels — these are completeness gaps, not quality failures, and should surface in dataset statistics as "pending," not be silently dropped.

### 7.6 Migration plan from existing artifacts

1. Build `extraction_manifest.csv` by re-reading existing detection outputs (bbox/confidence should already be in the detector's in-memory output even if not currently persisted — **needs code verification**, see §8 open question) joined against `source_video_manifest.json` for video-level fields. If bbox was not persisted, this requires re-running detection only (not re-extraction/re-cropping) to recover bbox — cheap, deterministic, same images.
2. Build `sample_manifest.csv` by joining existing `pilot_manifest.csv`, landmark JSON file presence, and `human_labels.csv`/`label_studio_export.csv` by `sample_id`/`image_id` (note: existing files use `image_id` as the key name — standardize to `sample_id` in the new manifest, keep `image_id` as alias during migration).
3. Derive 42-point landmark files from existing 68-point JSON via the index filter in §4 — pure data transform, no model inference.
4. `person_registry.csv` and identity assignment is new work per §7.3 — this is the one component that is **not** a reuse/reformat of existing data and requires either a tracking run over the full video or a scoped sample.
5. Run the QC pilot (§7.5), apply the resulting filter to produce `exclusion_manifest.csv`.
6. Everything else (images, raw landmark/label artifacts) is copied or symlinked as-is into the new structure — no recomputation.

### 7.7 Automated validation checks and statistics

Minimum checks for a `validate_dataset.py`-style script (not yet written):
- Every `sample_id` in `sample_manifest.csv` has a corresponding file in `images/original/` and `images/clahe/` with matching dimensions to the manifest's record (if recorded) and to each other.
- Every landmark JSON has exactly the expected point count (68 for full, 42 for subset) with finite, in-bounds x/y.
- No `sample_id` appears in both `exclusion_manifest.csv` and as "accepted" in `sample_manifest.csv`.
- `person_id` values in `sample_manifest.csv` all exist in `person_registry.csv`.
- Expression label values are within the declared label set; flag any off-schema value rather than silently accepting it.
- Dataset statistics report (counts by: total samples, samples with reviewed landmarks, samples with expression labels, samples per person_id, excluded samples by reason) generated directly from the manifests, never hand-typed.

### 7.8 Missing information that cannot be reconstructed without rerunning extraction

- **Per-crop bounding boxes and detector confidence**, if not currently persisted anywhere (needs direct code check of `FaceDetector`'s output path — not yet confirmed either way by this audit) — would require a detection-only rerun (not full extraction) to recover, since it's deterministic given the same frames.
- **Original-vs-sampled frame index distinction** — `source_video_manifest.json` has sampling config but I have not confirmed whether per-frame output filenames encode the *original* video frame index or only the *sampled* sequence index. This affects whether timestamp reconstruction is exact or approximate. Needs direct check before the manifest schema is finalized.
- **Identity/person_id** — cannot be reconstructed from existing artifacts at all; this is new annotation/tracking work, not a migration task.
- **Annotator B's 75 emotion labels** — simply not yet produced; infrastructure is ready, just needs the annotator to complete the work.
- **Human-reviewed landmarks for 541/645 crops** — 104 initialized, 64 reviewed; the remaining 541 need InsightFace initialization (cheap, automated) and reviewed status needs human CVAT work (not automatable).

---

## 8. Open questions requiring supervisor confirmation

1. **Scope of full dataset vs. pilot delivery**: Should the supervisor-facing Drive package (§5 of the task brief) ship now with the current partial coverage (150/645 expression-labeled, 64/645 landmark-reviewed), clearly marked as partial, or wait for fuller coverage first?
2. **Identity-tracking investment**: Is person-level identity actually needed for the thesis's current analysis goals, or is frame/sample-level analysis sufficient for now? This determines whether §7.3's tracking+re-ID work is in scope immediately or can be deferred.
3. **QC threshold pilot**: Confirm the proposed ~40–60 image stratified visual-QC pilot (§7.5) as the method for setting blur/size thresholds, rather than adopting a round-number default.
4. **Annotator B**: Is completing the remaining 75 emotion labels still planned, given the project's pivot to the landmark track on 2026-10-02? If emotion labels are now secondary, the Drive package should state that explicitly rather than imply completeness.
5. **Bit-identical "reviewed" landmarks**: The calibration batch's 6/11 rigid-translation corrections (§3.3) — should these count as "reviewed" in supervisor-facing statistics, or be flagged separately as lower-confidence reviews?
6. **42-point subset as the delivered schema**: Confirm that jaw/nose should be dropped entirely from the Drive deliverable (not just hidden in visualization) — i.e., `03_Landmarks/` ships only the 42-point files, with the full 68-point originals available only in internal/engineering docs, not supervisor-facing.

---

## 9. Risks

- **Partial coverage risk**: shipping a Drive package now will show mostly "pending" status for landmarks/identity; if not framed clearly, this could read as incomplete work rather than an intentional staged process.
- **Identity-tracking accuracy risk**: without inspecting the source video's content, the tracking+re-ID approach in §7.3 is a reasonable default but unvalidated — a quick dry-run is needed before trusting its output for any person-level statistics.
- **Review-depth inconsistency risk**: the rigid-translation vs. per-point-correction distinction in reviewed landmarks (§3.3, §8.5) could silently inflate "reviewed" counts if not surfaced in QC reporting.
- **Terminology drift risk**: the face-api.js vs. InsightFace landmark naming inconsistency in dashboard code (§3.4) is low-stakes but should be fixed before any dashboard-sourced documentation is reused in supervisor materials.

---

## 10. Recommended implementation sequence

1. Confirm open questions in §8 with supervisor.
2. Verify the two unresolved code-level questions in §7.8 (bbox persistence, frame-index semantics) by reading `src/fer_dataset/pipeline/face_detector.py` and the frame-extraction output path directly (quick, read-only follow-up).
3. Build `extraction_manifest.csv` and `sample_manifest.csv` from existing artifacts (§7.6 steps 1–3) — pure reformatting, no recomputation.
4. Derive 42-point landmark files from existing 68-point JSON (§7.6 step 3).
5. Run the QC visual pilot and finalize thresholds (§7.5).
6. Decide and execute (or defer) the identity-tracking approach (§7.3) based on supervisor input from §8.2.
7. Write `validate_dataset.py` (§7.7) and run it against the migrated structure before any Drive package is assembled.
8. Only after the above is both run and supervisor-confirmed: assemble the Drive package per the task brief's §5 (not started in this audit).

---

## Summary for the supervisor

The pipeline (extraction → detection → crop → CLAHE → landmark prediction → CVAT review → expression labeling) is fully implemented and tested; the gap is dataset *coverage* and *provenance granularity*, not missing capability. The main engineering tasks to reach the target standardized dataset are reformatting/joining existing artifacts into unified manifests and deriving the 42-point landmark subset — both low-risk, no recomputation. The two genuinely new pieces of work are: (1) person-level identity tracking, which doesn't exist today in any form and needs a validated approach before use, and (2) a QC threshold pilot, which the project's own prior audit already recommended and declined to shortcut. Six decisions (§8) need supervisor input before implementation proceeds; none of them block further read-only investigation.
