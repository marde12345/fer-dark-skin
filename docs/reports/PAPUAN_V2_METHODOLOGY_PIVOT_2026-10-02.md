# Papuan V2 — Methodology Pivot (2026-10-02)

**Experiment/phase:** Cross-cutting — supersedes EXP-PAP-004's role as the primary annotation track; establishes the planning basis for a new `EXP-PAP-LM-NNN` landmark-annotation sub-sequence (none created yet).

**Report type:** Audit + architecture-design documentation only. No implementation.

---

## Task Report Metadata

- **Date/time of this report:** 2026-10-02 (session timestamps on underlying evidence files range 2026-09-19 to 2026-10-02; git commit dates quoted below where available).
- **Task objective:** (1) Audit the repository for existing facial-landmark, CVAT, and training infrastructure; (2) document the supervisor-directed pivot from emotion-label annotation to facial-landmark annotation; (3) propose — without creating — a compatible experiment-ID scheme and branch/metadata design for Original vs. CLAHE landmark tracks; (4) preserve and clearly re-label the prior emotion-annotation work as exploratory/superseded, not deleted.
- **Context:** Pak Fadhil clarified that the primary annotation target for the current research cycle is facial landmarks/keypoints (to be reviewed in CVAT and used to train/retrain landmark models on two parallel branches — original face crops and CLAHE-preprocessed face crops), not the facial-expression labels EXP-PAP-004 was built to collect.
- **Files inspected:** see the per-section evidence below; summary list — `src/fer_dataset/pipeline/landmark_analyzer.py`, `src/fer_dataset/pipeline/face_detector.py`, `src/fer_dataset/pipeline/emotion_classifier.py`, `data/intermediate/landmarks_468/` (85 files), `data/intermediate/landmarks/` (179 files), `data/papuan_v2/{faces,clahe,pilot}/`, `tools/train_arcface_classifier.py`, `docs/EXPERIMENT.md`, `experiments/EXP-PAP-004/*`, `tools/papuan_v2/*`, repo-wide greps for "cvat"/"docker-compose", `dashboard/` directory contents.
- **Commands executed:** read-only file/dir listings, `grep`/`find` searches repo-wide for landmark/CVAT/training code, direct set-comparison of `landmarks_468` filenames against `data/papuan_v2/{faces,pilot}` manifests, `git log --oneline` on relevant paths. No write, train, install, or mutate commands were run.
- **Decisions made in this report:** (a) recommend `EXP-PAP-LM-NNN` as the new sub-sequence prefix, continuing the repo's own established `EXP-PAP-NNN` convention rather than inventing a new one; (b) recommend `PAPUAN_V2_CURRENT_STATE.md` continue serving as the project's dashboard/source-of-truth, since no other markdown dashboard exists and the one HTML artifact found (`dashboard/`) is a different kind of tool (see "Dashboard" section below) — not recommending it be repurposed as a status document.
- **Changes made:** none to code, data, Label Studio, or CVAT. This report and three related markdown reports are the only filesystem changes (see "Reports created/updated" at the end of this task's reply).
- **Changes NOT made:** no CVAT installation, no CVAT project, no landmark annotation collected, no dataset regenerated/modified, no Label Studio configuration touched or deleted, no training code written, no experiment directories created, no automatic commit/push.
- **Current status:** Planning/architecture-audit complete for the pivot; implementation not started.
- **Blockers:** None blocking the audit itself. Blocking *implementation* (tracked here, not yet actioned): CVAT is fully absent from this environment (Part 7 below) and must be stood up before any real landmark review can happen; the existing MediaPipe landmark extraction covers only 85 of 645 face crops (13%) and must be (re-)run at full scale before CVAT import is meaningful.
- **Next actions:** see "Next Actions" at the end of this report.

---

## Reason for Pivot

Supervisor clarification (Pak Fadhil): the annotation target for the current research workflow is facial landmarks/keypoints on detected face crops, not facial expression labels. Reviewed landmarks (via CVAT) become the training ground truth for landmark models, built on two parallel branches — original face crops and CLAHE-preprocessed face crops — so the two can later be compared.

## Previous Direction

Emotion annotation: face crops → HSEmotion / ArcFace+LR predictions → Label Studio human annotation (blind, two-annotator design, EXP-PAP-004) → human-human agreement → (intended) ground truth for emotion-model evaluation.

## Work Completed Before the Pivot

Verified directly against the repository, not assumed from documentation:

- **Dataset foundation:** 645 face crops (`data/papuan_v2/faces/`), 645 CLAHE crops (`data/papuan_v2/clahe/`), 150-image CLAHE-only pilot subsample (`data/papuan_v2/pilot/images/`), all with stable `image_id` lineage in `experiments/EXP-PAP-004/pilot_manifest.csv`.
- **AI-candidate predictions:** HSEmotion and ArcFace+LR predictions complete for all 150 pilot images (`experiments/EXP-PAP-004/ai_predictions.csv`, 300 rows).
- **Label Studio two-annotator infrastructure:** isolated-server architecture (separate process/data-dir/org per annotator — required because this Label Studio Community edition has no per-project role isolation), validated by a genuine throwaway Phase 1 exercise (port 8090, synthetic fixtures, 20 passing tests) before being applied to the real pilot.
- **Annotator A — full completion and validated export:** all 150 images labeled; export validated 150/150 rows, 150 unique images, 0 duplicates, 0 missing, exactly one real annotator identity, all labels within the valid 7-class set (`experiments/EXP-PAP-004/label_studio_export.csv`).
- **Annotator B infrastructure stood up:** isolated server (port 8081), project `"EXP-PAP-004 Overlap (Annotator B)"` created with exactly the 75 deterministic-overlap tasks, label config byte-identical to Annotator A's blind config (diff-verified) — ready for manual annotation, not yet annotated (0/75 at time of this pivot).
- **AI-assisted annotation methodology design review:** a full comparison of three candidate AI-pre-label workflows, evaluation-leakage analysis, and a minimal provenance schema (`docs/reports/PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`) — produced but never implemented.
- **A separate, pre-existing MediaPipe-based landmark extraction pipeline** (`src/fer_dataset/pipeline/landmark_analyzer.py`) was already present in the codebase, predating the Papuan V2 framing, and had already been run against **85 of the 645** Papuan V2 face crops (including 20 of the 150 pilot images) — see "Landmark Infrastructure Audit" below. This was built for a different purpose (geometric emotion-proxy features, e.g. brow-lowering/lip-corner distances), not as a landmark-training target, but its existence is directly relevant to the new direction.

## What Remains Useful

- The **two-annotator isolation architecture** (separate Label Studio server/data-dir/org per annotator) generalizes directly to a landmark-review context if CVAT ends up needing similar per-reviewer isolation, or stays relevant if emotion annotation resumes later.
- The **provenance-and-identity conventions** established across this project (`annotator_source` resolved from real user records never faked; `image_id` as the stable cross-file join key, chosen specifically to survive internal task-ID churn; deterministic seeded sampling with seeds documented inline) are tooling-agnostic and should be reused for the landmark-annotation assignment/export design, not reinvented.
- The **anti-circularity principle** already enforced in `tools/train_arcface_classifier.py` (ground truth restricted to a human-authored label column, never a model's own prediction) is the same principle that must carry over to landmark model training: reviewed/corrected CVAT landmarks become ground truth, not the raw MediaPipe/InsightFace proposal.
- The **existing MediaPipe landmark extraction code** (`landmark_analyzer.py`) is a candidate source of initial/pre-annotation proposals for CVAT import, pending the methodology decision in "Risks / Open Questions" below.
- `pilot_manifest.csv`'s lineage fields (source paths, sampling seed, timestamps) are exactly the kind of `source_image_id`/lineage metadata the Original-vs-CLAHE landmark branches need (Part 6 below) and should be extended, not replaced.

## What Is Superseded

The following are no longer the **primary** annotation methodology for this research cycle, per the supervisor's clarification — they are preserved, not deleted, and remain valid exploratory/infrastructure-validation work:

- EXP-PAP-004's blind human emotion-labeling pilot (Annotator A's completed 150 labels, Annotator B's stood-up-but-unlabeled 75-overlap infrastructure).
- The HSEmotion / ArcFace+LR AI-candidate-prediction comparison for emotion labels.
- The AI-assisted (emotion) annotation methodology design review.
- The Label Studio server infrastructure built for emotion labeling (both A's and B's servers/projects) — left running/intact, not torn down, in case the emotion-annotation track is revisited.

## New Direction

Facial landmark/keypoint annotation on face crops, reviewed in CVAT, split into two parallel branches by preprocessing condition (original vs. CLAHE), each branch producing its own trained landmark model for later comparison.

## New Experimental Branches — Original vs. CLAHE

```text
Branch A (Original):   Original face crop → landmark annotation → CVAT review → reviewed GT → training → Landmark Model A
Branch B (CLAHE):      CLAHE face crop    → landmark annotation → CVAT review → reviewed GT → training → Landmark Model B
```

**Constraint carried over from the existing dataset design:** original and CLAHE crops for the same underlying face must remain linked by a shared source identity — `data/papuan_v2/faces/` and `data/papuan_v2/clahe/` already satisfy this today (file-name-aligned, 645 each, same source frames), so Branch A/B's `image_id`s should reuse this existing pairing rather than deriving a new one.

**Minimum metadata proposed** (evaluated against the task's example list, trimmed to what's actually necessary, following this project's established "don't add fields unless necessary" convention):

| Field | Necessary? | Reasoning |
|---|---|---|
| `image_id` | Yes | Existing stable join key convention; reused as-is. |
| `source_image_id` | Yes | Required specifically to keep original/CLAHE pairs linked — `image_id` alone doesn't encode which preprocessing variant a row is, so a shared `source_image_id` (the pre-preprocessing frame/face identity) is the field that prevents the "two unrelated datasets" failure mode the task explicitly warns against. |
| `preprocessing` | Yes | `original` \| `clahe` — the one field that actually distinguishes Branch A from Branch B rows sharing a `source_image_id`. |
| `width`, `height` | Yes, but derivable | Needed by CVAT/training code to interpret pixel-coordinate landmarks; could be read from the image file at load time instead of stored redundantly — recommend storing only if a downstream step needs it without re-opening the image (e.g. a fast manifest scan); otherwise omit and derive on demand. |
| `landmark_schema` | Yes | Must be recorded explicitly once a schema is chosen (Part 5 found the existing MediaPipe output is 478-point; a different, smaller scheme may be chosen for CVAT — see "Risks" below) — without this field, two annotation runs using different point counts would be silently incompatible. |
| `landmark_coordinates` | Yes | The actual annotation payload; format (JSON array vs. separate x/y columns) is an implementation detail for the later implementation prompt, not decided here. |
| `annotation_status` | Yes | Mirrors the existing `human_labels.csv`/`annotator_progress.json` pattern of tracking not-started/in-progress/complete — needed to replicate the existing "refuse to proceed on incomplete data" guard pattern already used for `human_agreement_report.py`. |
| `annotator` | Yes | Same real-identity-never-faked convention as `annotator_source` elsewhere in this project. |
| `review_status` | Yes | Distinguishes "auto-proposed" vs. "CVAT-reviewed/corrected" — the field that encodes the "AI/auto proposal must not silently become ground truth" principle for landmarks, mirroring the emotion-track's existing `human_verified` field. |

No field is proposed beyond this list; `annotation_timestamp`-equivalent provenance is already available natively from CVAT's own task history, the same way Label Studio's `created_at`/`updated_at` already covered this for the emotion track — no need to duplicate it in a custom column.

## Annotation Tool — CVAT Readiness

**Confirmed via repo-wide search: CVAT is fully absent from this repository.** Zero references to "cvat" anywhere in `src/`, `tools/`, `docs/`, or `pyproject.toml`; no `docker-compose*` file exists anywhere (CVAT's standard self-hosted deployment is Docker-Compose-based) — this is a from-scratch integration with no existing configuration to reconcile or conflict with, and no risk of accidentally disturbing a prior CVAT setup (there isn't one).

**What self-hosted CVAT generally supports** (general tool knowledge, stated as such — not verified against a running instance here since none exists): skeleton/point-based keypoint annotation, task import of pre-existing keypoints as a starting annotation (so the existing MediaPipe output could seed CVAT tasks rather than starting annotators from a blank image), and export in multiple formats including CVAT's own XML/JSON and COCO-keypoints-style formats. These are standard CVAT capabilities but have not been confirmed against this specific project's exact landmark schema requirements — doing so needs a real (even if minimal, single-project) CVAT instance, which is implementation, not audit.

**Open, unresolved by this audit:** whether local/self-hosted CVAT (Docker Compose, matching the project's existing "everything runs locally, nothing uploaded to a cloud service" pattern already established for Label Studio) is sufficient, versus any paid/cloud CVAT tier — nothing in the supervisor's clarification as relayed indicates a paid tier is required, unlike the earlier "paid AI-assisted annotation" instruction for the (now-superseded) emotion track.

## Landmark Infrastructure Audit (repository findings)

A facial-landmark extraction pipeline **already exists** in this codebase, independent of and predating the Papuan V2 framing:

- **Code:** `src/fer_dataset/pipeline/landmark_analyzer.py` — uses MediaPipe's Face Landmarker Tasks API (downloads `face_landmarker.task` from Google's model storage).
- **Landmark definition:** 478 points (468 face-mesh points + 10 iris points) — confirmed by reading the module's own docstring/comments and output-shape handling (`landmarks_xy.shape[0] < 468` guard, "Saved per-image landmarks (up to 478 points)").
- **Coordinate system:** pixel coordinates (`lm.x * w, lm.y * h`), **not normalized** — MediaPipe's raw output is 0–1 normalized, but this code explicitly multiplies by the crop's width/height before saving.
- **Relative to crop, not original frame:** `w, h` are read from the face-crop image's own dimensions, not the source video frame — so these landmarks are crop-relative, which matters for the Original-vs-CLAHE branch design since crops (not full frames) are exactly what both branches annotate.
- **Existing coverage, verified by direct file-set comparison:** 85 `.npy` files in `data/intermediate/landmarks_468/`, all 85 confirmed to be a subset of the 645 Papuan V2 `faces/` images (13.2% coverage), of which exactly 20 overlap with the 150-image pilot set. **625 of 645 face crops (97%) have no landmark data yet.** A separate `data/intermediate/landmarks/` directory (179 `.jpg` files) holds visualization overlays, not raw coordinate data.
- **InsightFace side:** the project's face-detection step (`src/fer_dataset/pipeline/face_detector.py`, SCRFD via `insightface.app.FaceAnalysis(name="buffalo_l")`) computes a 5-point alignment keypoint (`det.kps`) internally as a side effect of detection, but **discards it** after cropping — it is never saved to disk. A second, separate InsightFace instantiation in `emotion_classifier.py` recomputes keypoints solely for an optional visualization overlay (a known, already-documented inefficiency in `docs/EXPERIMENT.md`) — also not persisted as structured data.
- **No landmark training/model code exists anywhere in the repo** — confirmed by a repo-wide search for deep-learning framework usage (`torch`, `tensorflow`, `nn.Module`): zero hits in `src/` or `tools/`. The only training precedent at all is classical ML (next section), not landmarks, not deep learning.

**Direct answers to the audit's specific questions:**
1. Current landmark definition: MediaPipe Face Landmarker (mesh + iris).
2. Point count: 478 (commonly cited as "468" in casual use, but this implementation includes 10 extra iris points).
3. Coordinate system: Cartesian x/y.
4. Normalized vs. pixel: pixel.
5. Relative to crop or original image: crop-relative.
6. Can existing automatic landmarks serve as initial proposals: technically yes for the 85 already-computed files, but the extraction would need to be (re-)run project-wide (625 of 645 crops are missing it) before this is useful as a systematic pre-annotation source.
7–9. CVAT import / format support / training export format: undetermined — depends on the CVAT setup, which doesn't exist yet (see above); this is implementation work, correctly out of scope for this audit.

## Training — Pipeline Design (audit of existing precedent, no new code written)

The only real training code in the repository is `tools/train_arcface_classifier.py`: trains a classical `sklearn.linear_model.LogisticRegression` on frozen, pre-computed ArcFace embeddings — not raw pixels, and not a deep-learning model. It uses `StratifiedGroupKFold` (5-fold, grouped by a temporal/frame-index block to prevent near-duplicate-frame leakage across folds — a genuine, documented leakage safeguard worth reusing), `class_weight="balanced"`, a fixed seed, and restricts its ground-truth source to a human-authored label column, never a model's own prediction output (the same anti-circularity principle the landmark track must preserve). No other training script, and no PyTorch/TensorFlow model class, exists anywhere in the repo.

**What this means for Model A/B (landmark models), stated as open design questions, not decisions:** a landmark-regression task (predicting continuous x/y coordinates, not a class label) is architecturally different from this repo's only precedent (a linear classifier on fixed embeddings) — there is no existing deep-learning training loop, loss function, or coordinate-regression model class to reuse as-is. This is a legitimate "no existing evidence to select an architecture from" situation per the task's own instruction not to pick an architecture without evidence; an architecture choice should be a dedicated, later design conversation, not inferred here.

## Experiment ID Proposal

The repository's own convention, read directly from `docs/EXPERIMENT.md:450`: **`EXP-PAP-NNN`** (3-digit zero-padded), explicitly scoped to "Papuan V2 data-side work," distinct from the older `EXP-NNN`/`R\d` convention used for pre-Papuan-V2 work. Only one experiment directory currently exists on disk (`experiments/EXP-PAP-004/`); `EXP-PAP-001`–`003` are documented narrative sections in `docs/EXPERIMENT.md` without dedicated directories. **Next free number in the existing single-track sequence would be `EXP-PAP-005`.**

For the landmark pivot specifically, a sub-prefixed scheme is proposed — **not created yet**, pending your confirmation this fits your intended convention:

```text
EXP-PAP-LM-001   Original landmark annotation
EXP-PAP-LM-002   CLAHE landmark annotation
EXP-PAP-LM-003   Original landmark model training
EXP-PAP-LM-004   CLAHE landmark model training
EXP-PAP-LM-005   Original vs. CLAHE comparison
```

This keeps the established `EXP-PAP-` prefix (continuity with the existing convention) while the `-LM-` infix distinguishes the new landmark sub-sequence from a plain continuation of the emotion-annotation numbering (`...005, 006...`), so the two research tracks stay visually distinguishable in any future directory listing or report index. No experiment directories were created.

## Risks / Open Questions

1. **Landmark schema choice:** should the new annotation effort adopt the existing 478-point MediaPipe schema (re-run at full scale), a smaller/custom point set more suited to manual CVAT correction (478 points is a lot to manually correct per image), or something else? This decision gates the `landmark_schema` field's value and CVAT project configuration.
2. **Auto-proposal source:** should CVAT tasks be pre-filled with MediaPipe (or InsightFace 5-point) proposals, or should the first review pass start blank? This mirrors the same "does AI pre-fill bias the human reviewer" question already analyzed for the emotion track's AI-assisted-annotation design (`PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`) and that analysis's reasoning likely transfers, but has not been re-derived specifically for landmarks here.
3. **CVAT deployment scope:** local Docker Compose (consistent with this project's existing "nothing leaves this machine" pattern) vs. any hosted option — no evidence yet that a paid/hosted tier is required for landmarks, unlike the emotion track's "paid AI-assisted annotation" instruction.
4. **Model architecture for landmark regression:** genuinely open — no existing code in this repo to build from; needs a dedicated design decision, not an inferred choice.
5. **Relationship between the two research tracks going forward:** should Annotator B's already-stood-up-but-unused emotion-annotation infrastructure (75-task Label Studio project, 0/75 complete) be formally paused, or left available in case the emotion track resumes in parallel? Not resolved here — stated as a question for you/the supervisor, not decided unilaterally.

## Next Actions

1. Resolve the landmark-schema and auto-proposal-visibility questions above (a decision task, not an engineering task) before any CVAT setup begins.
2. Stand up a local, self-hosted CVAT instance (Docker Compose) as a separate, later implementation prompt — not part of this audit.
3. Decide whether to re-run the existing MediaPipe landmark extraction across the full 645-face set (or the 150-pilot subset first, as a smaller pilot) before CVAT import, once the schema question above is resolved.
4. Confirm or adjust the proposed `EXP-PAP-LM-NNN` experiment-ID scheme before creating any experiment directories.
5. Explicitly decide the status of Annotator B's stood-up emotion-annotation infrastructure (pause vs. keep available) — see Risk 5 above.

---

*Generated as part of the supervisor-directed methodology pivot audit, 2026-10-02. No code, dataset, Label Studio, or CVAT configuration was created or modified in the course of producing this report.*
