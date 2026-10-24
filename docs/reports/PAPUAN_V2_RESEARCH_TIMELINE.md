# Papuan V2 — Research Timeline

**Experiment/phase:** Cross-cutting (covers pre-Papuan-V2 foundation through the 2026-10-02 landmark pivot).

**Date of this report:** 2026-10-02.

**Dating method, stated explicitly per instruction:** dates below come from two different sources that should not be confused — (a) **git commit dates**, for files that are actually committed to the repository, and (b) **internal file timestamps** (`generated_at` fields inside JSON metadata, `exported_at` fields inside CSVs), for the EXP-PAP-004/papuan_v2 work, which is **untracked** in git (never committed) and therefore has no commit-date evidence at all. Where neither source gives a date, this timeline says so explicitly rather than guessing.

---

## Earlier Pipeline (pre-Papuan-V2 foundation, git-dated)

| Date (commit) | Commit | What it established |
|---|---|---|
| 2026-08-14 | `9b5d0ac` "git ignore data" | Data directories excluded from version control — explains why later `data/papuan_v2/` and `experiments/EXP-PAP-004/` content is untracked by design, not by omission. |
| 2026-08-15 | `31f5401` "labeling" | Earliest commit referencing a labeling-related change found in this history scan; exact scope not re-verified in this pass. |
| between 2026-08-15 and 2026-09-08 (exact date not re-queried) | `74caeb7` "Refactor code structure for improved readability and maintainability", `988b2cc` "refactor plan" | Codebase restructuring — exact dates uncertain, state as a range, not a point. |
| 2026-09-08 | `f9c9fae` "test: capture Phase 0 baseline pipeline outputs" | Baseline pipeline test capture — the project's own "Phase 0" framing already existed by this date. |
| 2026-09-09 | `13cafe4`, `840e0d5`, `9ae155d`, `ef3fbd9`, `ace29ec` | A cluster of same-day commits: refactor-plan execution, research-plan execution, dashboard research execution, presentation-slide image generation, and a guideline proposal — the project's general (pre-Papuan-V2) FER pipeline (face detection, cropping, CLAHE, HSEmotion, ArcFace) was substantially in place by this point, per these commit messages; this timeline does not claim exact line-level dates for each sub-component beyond what the commit messages state. |
| 2026-09-19 | `a62f0fa` "feature(dashboard): model comparison" | Added `dashboard/` (HTML/JS model-comparison demo) and `docs/DEMO_MODEL_COMPARISON.md`. |
| 2026-09-19 | `21f1108` "dataset(papuan_v2): add new dataset for papuan v2" | **Papuan V2 framing formally introduced** as a committed, named dataset entry in the repository's git history — this is the clearest single git-dated marker for "Papuan V2 begins" as a distinct research line. |

## Annotation Exploration (EXP-PAP-001 through EXP-PAP-004, internally-dated — untracked in git)

No commits exist for these files (`experiments/EXP-PAP-004/*`, `tools/papuan_v2/*` are untracked per the `.gitignore` pattern set in `9b5d0ac`). Dates below are read from each file's own internal timestamp field, which is the only evidence available:

- **EXP-PAP-001 — pilot-scale raw source pipeline** (frame extraction, face detection, CLAHE): documented narratively in `docs/EXPERIMENT.md`; produced the 645 face crops (`data/papuan_v2/faces/`) and 645 CLAHE crops (`data/papuan_v2/clahe/`). No internal timestamp found independent of EXP-PAP-002's manifest; treat as preceding EXP-PAP-002.
- **EXP-PAP-002 — pilot set construction + human-labels template:** produced the 150-image pilot subsample and `pilot_manifest.csv`. Internal evidence: `experiments/EXP-PAP-004/label_studio_metadata.json` carries `"generated_at": "2026-09-19T08:09:48Z"` for the downstream Label Studio project setup, implying EXP-PAP-002's pilot construction happened at or before this date.
- **EXP-PAP-003 — AI-assisted-annotation candidates + agreement analysis (offline comparison, not the later "paid AI-assisted annotation" instruction):** produced `ai_predictions.csv` (HSEmotion + ArcFace+LR predictions, 150×2 rows). Same 2026-09-19 window as EXP-PAP-002, per `docs/EXPERIMENT.md`'s cross-references between the two.
- **Phase 1 — annotation architecture validation (throwaway):** a separate, isolated Label Studio instance (port 8090, synthetic fixture images, separate DB/org), 20 passing tests confirming a shared Label Studio project does not leak co-annotator content before submission. Date not independently pinned beyond "before or alongside EXP-PAP-004's real pilot setup" (2026-09-19 window) — no internal timestamp field was found specifically for this validation run in this pass.
- **EXP-PAP-004 — 150-image human-annotation pilot, two-annotator isolation design:** `label_studio_metadata.json generated_at: 2026-09-19T08:09:48Z` (Project A/150-task setup); `annotator_progress.json generated_at: 2026-09-19T08:24:59Z` (overlap/progress tracking scaffold, at that point `annotator_A_completed: 1`, `annotator_B_completed: 0`).
- **Manual annotation experiment — Annotator A completion:** per this session's own direct conversation record (not a file timestamp independently re-checked here), Annotator A's full 150/150 submissions were reported complete on 2026-10-01.
- **Annotator A export and validation:** `label_studio_export.csv exported_at: 2026-10-01T21:40:09Z`; validated in this session — 150/150 rows, 150 unique images, 0 duplicates, 0 missing, exactly one annotator identity, all labels within the valid 7-class set.
- **Annotator B infrastructure stood up:** isolated server (port 8081) + project `"EXP-PAP-004 Overlap (Annotator B)"`, 75 tasks imported matching the deterministic `overlap=true` subset exactly — completed in this session, 2026-10-01/02; 0/75 annotated at time of the pivot below.
- **AI-assisted annotation investigation (emotion track):** a design review comparing three AI-pre-label workflow designs, an evaluation-leakage analysis, and a minimal provenance schema — produced in this session, 2026-10-01, in `docs/reports/PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`. Never implemented.

## Methodological Pivot

**2026-10-02 — Supervisor clarification (Pak Fadhil):** the annotation target for the current research workflow should be facial landmarks/keypoints, not emotion labels. Reviewed-in-CVAT landmarks become training ground truth for landmark models, on two parallel branches (original face crops vs. CLAHE-preprocessed face crops), to be compared against each other.

**New direction, effective 2026-10-02:**
```text
Face detection/crop
      │
      ├─────────────────┬─────────────────┐
      ▼                 ▼
Original face       CLAHE face
      │                 │
      ▼                 ▼
Landmark             Landmark
annotation           annotation
      │                 │
      ▼                 ▼
CVAT review          CVAT review
      │                 │
      ▼                 ▼
Reviewed GT          Reviewed GT
      │                 │
      ▼                 ▼
Training             Training
      │                 │
      ▼                 ▼
Original model      CLAHE model
                 │
                 ▼
     Original vs. CLAHE comparison
```

Full detail, risk analysis, and audit evidence for this pivot: `docs/reports/PAPUAN_V2_METHODOLOGY_PIVOT_2026-10-02.md`.

**A relevant pre-existing fact surfaced only during this pivot's audit, not before:** a MediaPipe-based landmark extraction pipeline (`src/fer_dataset/pipeline/landmark_analyzer.py`) already existed in the codebase prior to the Papuan V2 framing, and had already been run against 85 of the 645 Papuan V2 face crops (including 20 of the 150 pilot images) for an unrelated purpose (geometric emotion-proxy features). This predates and is independent of the pivot decision itself, but is directly relevant to implementing it.

## 2026-10-02 (same day, later task) — Landmark Schema & AI-Proposal Methodology Investigation

Following the pivot above, a focused investigation resolved two of its open methodological gates (landmark schema choice; whether to show AI-generated landmark proposals to human annotators during CVAT review), plus a prerequisite third question (whether Original and CLAHE branches both need independent manual annotation). Full detail: `docs/reports/PAPUAN_V2_LANDMARK_SCHEMA_AND_ANNOTATION_METHOD.md`.

Key resolved finding: direct code inspection and pixel-dimension measurement confirmed this project's CLAHE implementation is a pure per-pixel lightness-channel transform with no geometric operation — Original and CLAHE crops for the same `image_id` are pixel-grid-identical. This means landmarks annotated once on the Original branch can be reused unchanged (no coordinate transform needed) as the CLAHE branch's training target, removing the need to independently annotate both branches. A 68-point schema (available from an already-installed InsightFace sub-model, no new dependency) was recommended over the existing 478-point MediaPipe output, with explicit assumptions stated; both this and the AI-proposal-visibility question still require supervisor confirmation before implementation.

**Branch note:** this task also marked the first instance of all work being confined to `main` per explicit instruction, with the prior audit branch (`worktree-papuan-v2-audit`)'s existing report history ported onto `main` as a plain file copy (not a git merge), preserving that branch untouched as the original archive.

---

## 2026-10-02 (same day, third task) — EXP-PAP-005 CVAT Landmark Pilot Implemented

With all three open methodological gates resolved (68-point InsightFace schema; Original-only annotation; InsightFace predictions shown as initial CVAT proposals), the first concrete implementation step was taken: a working 24-image CVAT pilot. Full detail: `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md`.

Key events: a container runtime (colima) was installed on this machine for the first time (none existed previously) to run CVAT's self-hosted Docker Compose deployment; an undersized VM initially caused what looked like a hang but was resolved by allocating more CPU/memory; a port collision with the still-running Annotator A Label Studio server was discovered and fixed by remapping CVAT's own ports, leaving Label Studio untouched; InsightFace's 68-point landmark sub-model was verified end-to-end (semantic ordering cross-checked against its mean-shape geometry, matching the standard 68-point jaw/eyebrow/nose/eye/mouth convention) and used to generate initial proposals for the 24-image pilot, which were then imported into a new CVAT task as a 68-point skeleton. The pilot is now populated and ready for a human reviewer; the actual review pass has not yet been performed.

---

## 2026-10-02 (same day, fourth task) — CVAT Landmark Labels Renamed to Anatomical Names

After visually inspecting the EXP-PAP-005 pilot, the generic `pt0`...`pt67` skeleton labels were found insufficiently user-friendly for human review. Full detail: `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md`.

The InsightFace `landmark_3d_68` index-to-anatomical mapping was independently verified (not assumed) via three cross-checks: the model's own bundled mean-shape template geometry, empirical pixel-coordinate checks across 5 real pilot images, and a structural match to the well-documented ibug-300W 68-point convention. All 68 CVAT sublabels were renamed in place (e.g. `pt36`→`right_eye_outer_corner`) using CVAT's parent-label PATCH mechanism, which preserves label `id`-based annotation references — no task recreation was needed. A full before/after check of all 1,632 point coordinates (24 images × 68 points) confirmed zero drift. One CVAT API quirk was discovered and documented for future reference: the annotations endpoint's per-shape `elements` array is unordered and must be joined by `label_id`, never by array position.

---

## 2026-10-18 — CVAT Labels Abbreviated Mid-Review

While actively reviewing the EXP-PAP-005 pilot in CVAT, the full anatomical label names from the 2026-10-02 rename were found too visually crowded on the canvas for practical use. Abbreviated to short region+index names (`j0`, `re3`, `mo7`, etc., full mapping in `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md` §13) using the same validated-safe label-rename mechanism. Because human review was already in progress, validation this time was performed against a snapshot of the live annotation state taken immediately before the rename (not just the original AI predictions) — confirmed zero data loss across all 1,632 points and all occlusion flags, meaning any review progress already made was preserved.

---

## 2026-10-18 (same review session) — CVAT Abbreviations Clarified with Side/Detail Encoding

The plain abbreviations from earlier the same day (`ns0`...`ns4`) didn't convey left/right or inner/outer, so the reviewer requested clearer short names, giving `nsli` (nose, left, inner) as the example. Replaced with a side/detail-encoded scheme across all 68 points, same indices, applied via the same validated-safe rename mechanism. Validation (snapshot immediately before the rename vs. after) found 10 of 1,632 points differed — not from the rename, but from the reviewer's own concurrent correction of one frame's eyebrow region, confirmed by the task's `updated_date` advancing mid-operation and by the changed points forming a complete, coherent anatomical region. That correction was preserved, not lost.

---

## 2026-10-19 — Pilot Review Exported, Compared, and QC'd; Review Coverage Flagged as Ambiguous

Following the user's report that all 24 pilot images had been manually reviewed, the CVAT annotations were exported (`experiments/EXP-PAP-005/cvat_reviewed_landmarks.json`) and compared against the original InsightFace proposals. Full detail: `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`.

Structural QC passed cleanly (24/24 images, 1,632/1,632 landmarks, no missing/duplicate indices). However, the comparison surfaced a finding this report does not resolve: only 5 of 24 images show any point displaced beyond a 0.5px tolerance from the original AI proposal; the other 19 are coordinate-identical. CVAT's own job-state metadata also still read "in progress," not "completed," at export time. Whether this reflects genuinely accurate AI proposals on 19 images or incomplete review is explicitly left open for the user to clarify — the report's metadata updates and scale-up recommendation were written conservatively around this ambiguity rather than assuming completion.

---

## 2026-10-19 (same day, following task) — Reviewer Confirms Full Review; Image-Quality Limitation Documented

The reviewer confirmed directly that all 24 pilot images were visually reviewed: some needed no correction, some had image-quality/resolution limitations that made confident feature localization difficult, and the 5 images already identified by coordinate comparison were the ones manually corrected. Full detail: `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md` §20.

This resolves the prior report's open "was review actually performed on all 24" question. A finer question remains open by design: which of the 19 unchanged images were accepted as genuinely correct versus accepted because low resolution made them hard to judge — no per-image quality flag was recorded, and none is invented here. A new objective finding from crop-dimension data: the pilot's 3 smallest images (616–1,628 px²) all show zero corrections, while two of the most heavily-corrected images are comparatively large — a pattern consistent with, but not proof of, the quality-limitation explanation. A quality-control rule for flagging low-resolution images before full-scale annotation is proposed in the updated report, not yet approved or implemented.

---

## 2026-10-19 (same day, following task) — Dataset-Wide Quality Audit (645 Images)

Before deciding how to scale EXP-PAP-005 beyond its 24-image pilot, all 645 Original/CLAHE crop pairs were audited for inventory integrity and quality-relevant distributions. Full detail: `docs/reports/PAPUAN_V2_DATASET_QUALITY_AUDIT.md`.

Found clean: 645/645 pairs present and dimension-matched, 0 duplicates, 0 aspect-ratio truncation outliers, all RGB, all opened successfully. Dimension distribution characterized in full (22×25px to 697×966px). A blur-sharpness heuristic (Laplacian variance, no new dependency) was computed for all 645 images for the first time — no such signal existed in the project previously. No numeric quality threshold was set: the audit found no existing reviewer-grounded data beyond the 24-image pilot to calibrate one against, and explicitly declined to infer one from that small sample per instruction. Recommended next step: add an "uncertain" flag to the CVAT workflow for the next annotation batch to generate the missing calibration data, rather than guessing a threshold now.

---

## 2026-10-19 (same day, following task) — Next Calibration Batch Designed

Designed (not executed) the next annotation batch following the dataset-wide quality audit. Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md`.

40 images selected deterministically (seed=300, 4 per area-decile stratum from the already-audited 645-image distribution, drawn from the 621 images outside the existing EXP-PAP-005 pilot) to calibrate a new uncertainty-capture mechanism before any larger-scale annotation. CVAT's label/sublabel schema was confirmed (via live API and source inspection) to already support per-point attributes and a native `occluded`/`outside` boolean on every skeleton point; the recommended design reuses that existing field for point-level uncertainty rather than adding new schema, plus one new image-level tag label and an external reason manifest — the least disruptive combination evaluated. A full reviewer protocol and acceptance-criteria set was defined. Nothing in this task was executed: no predictions generated, no CVAT task created, Task 1 untouched.

---

## 2026-10-19 (same day, following task) — 40-Image Calibration Task Implemented in CVAT

The calibration batch designed earlier the same day was implemented: InsightFace predictions generated for all 40 sampled images (0 failures), a new CVAT task created (Task ID 2, reusing Task 1's exact skeleton label plus one new `review_status` tag for ok/needs_review/low_quality), and all 40 images with 2,720 skeleton points imported and verified via API with zero coordinate mismatches against the raw predictions. Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §16.

Task 1 (the original 24-image pilot) was confirmed unchanged throughout. Human review of Task 2 has not started — this task stops with the batch populated and ready.

---

## 2026-10-19 (same day, immediately following) — Calibration Task Bug Found, Fixed, Recreated as Task 3

The newly-created calibration task (Task ID 2) crashed CVAT's UI on open. Root cause confirmed: its skeleton SVG was copied verbatim from Task 1 and carried hardcoded references to Task 1's own sublabel database IDs, which don't exist in a different task. Fixed by deleting Task 2 (no review progress existed yet) and recreating it as **Task ID 3** with a freshly-generated, self-consistent SVG. Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §17.

Data integrity was re-verified identical to the original import (40/40 images, 2,720/2,720 points, 0 mismatches). Task 1 confirmed unaffected throughout. The user should use Task 3, not Task 2, going forward.

---

## 2026-10-19 (same day, following task) — Calibration Batch Reviewed, Exported, and QC'd

The user completed human review of all 40 Task 3 calibration images. Exported and QC'd clean (2,720/2,720 points, 0 errors). Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §18.

714/2,720 points (26.2%) changed from the original InsightFace proposals, concentrated in 11 of 40 images that were mostly re-placed wholesale rather than individually nudged (verified genuine, not a shift artifact). Review-status tags: 30 ok, 10 low_quality. The point-level occluded uncertainty flag was not used at all in this batch (0/2,720) — a finding for the design to address, not resolved here. Original↔CLAHE pairing re-verified for all 40.

---

## 2026-10-19 (same day, following task) — Heavy-Correction Audit: No Issue Found, Two Correction Patterns Identified

Audited the 11 calibration images with near-complete point corrections. Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §19.

Landmark index/name integrity confirmed intact for all 11 — no evidence of export or annotation corruption. The 11 split into two patterns: 6 images show an exact, bit-identical displacement across all 68 points (a whole-skeleton drag in CVAT, not independent point-by-point correction), and 5 show genuine per-point variance. This refines the earlier correction-rate statistic's interpretation without invalidating it. No visualization tool was built for this audit (none existed in the repo already) — findings are based entirely on coordinate-level analysis.

---

## 2026-10-19 (same day, following task) — CVAT Task 4 Created as Original-Proposal Comparison

Created Task 4, a second CVAT task holding the same 40 calibration images in the same order as Task 3, populated only with the original unreviewed InsightFace proposals (never Task 3's corrected coordinates) — giving the user a direct visual before/after comparison in CVAT. Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §20.

2,720/2,720 points verified matching the raw proposal artifact exactly; Task 3 confirmed byte-for-byte unchanged throughout. Applied the lesson from the earlier Task-2 SVG bug: Task 4's skeleton SVG was freshly generated, not copied from another task.

---

## 2026-10-19 (same day, following task) — First Landmark Training Baseline Run

Pooled all 64 currently-reviewed landmark images (24-image pilot + 40-image calibration batch, verified 0 overlap) into the project's first train/val/test split (45/11/8, seed=400, frame-adjacency-grouped to mitigate the still-unresolved lack of subject-ID data). Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §22.

Trained a mean-shape baseline — the honestly-smallest model class this repository and dataset size can support, since no deep-learning training code exists anywhere in the project. Normalized landmark error ~0.09-0.10 of image diagonal on held-out data. Confirmed, not assumed, that this content-blind baseline produces identical results for Original and CLAHE by construction — a real image-conditioned model would be needed to measure any actual preprocessing effect, which 45 training images cannot reliably support.

---

*This timeline will be appended to, not rewritten, as the project progresses — per the project's standing instruction to preserve chronological history rather than overwrite it. No code, dataset, or configuration was modified in producing this report.*
