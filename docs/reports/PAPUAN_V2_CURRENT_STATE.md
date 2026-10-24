# Papuan V2 — Current State (Master Report)

**Audit date:** 2026-10-01 (original audit below, preserved unchanged). **Pivot update appended:** 2026-10-02. **Landmark schema/method update appended:** 2026-10-02 (same day, later task). **CVAT pilot implementation appended:** 2026-10-02 (same day, third task). **Landmark label schema appended:** 2026-10-02 (same day, fourth task). **Labels abbreviated:** 2026-10-18 (fifth task, during active human review). **Abbreviations clarified:** 2026-10-18 (sixth task, same review session). **Review exported and QC'd:** 2026-10-19 (seventh task). **Review confirmed + quality limitation documented:** 2026-10-19 (eighth task). **Dataset-wide quality audit:** 2026-10-19 (ninth task). **Calibration batch plan:** 2026-10-19 (tenth task). **Calibration task implemented:** 2026-10-19 (eleventh task, superseded by a same-day bugfix — see Update 12). **Calibration review exported/QC'd:** 2026-10-19 (thirteenth task). **Heavy-correction audit:** 2026-10-19 (fourteenth task). **Task 4 (original-proposal comparison) created:** 2026-10-19 (fifteenth task). **First landmark training baseline run:** 2026-10-19 (sixteenth task) — see the sixteen dated sections immediately below; everything after them is the original 2026-10-01 audit, kept as a historical record per the project's standing instruction not to overwrite prior reports. **Scope:** repository state, not documentation claims. Where documentation and repository state disagreed, repository state (file contents, row counts, test results) is reported as authoritative, and the discrepancy is noted explicitly.

---

## [2026-10-19 UPDATE 16] First Landmark Training Baseline — Mean-Shape, 64-Image Train/Val/Test Split

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §22. Pooled all currently-reviewed landmark data (24-image pilot + 40-image calibration batch, 0 overlap, 64 images / 4,352 points total) into the project's first train/val/test split (45/11/8, seed=400), grouped by frame-number adjacency to mitigate the still-unresolved subject-ID leakage gap (no identity column exists anywhere in the manifests — disclosed, not assumed away).

Trained a **mean-shape baseline** (per-landmark mean position, content-blind — no deep-learning code exists anywhere in the repo, so this is the honestly-smallest supportable baseline, not a placeholder). Val normalized error (by diagonal) 0.090, test 0.101 — stable despite raw pixel error varying widely (9.2px vs. 40.1px) due to crop-size differences between splits. **Original vs. CLAHE confirmed identical by construction** for this baseline (it doesn't read pixel content, and the two conditions share identical coordinates/dimensions) — a real image-conditioned model is required to answer that question, which this dataset size doesn't yet support training reliably.

---

## [2026-10-19 UPDATE 15] CVAT Task 4 Created — Original-Proposal Counterpart to Task 3

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §20. Created **Task 4** (`http://localhost:8070/tasks/4`, "EXP-PAP-005 Calibration — 40 Images (Original Proposals)") holding the same 40 images in the same order as **Task 3** (`http://localhost:8070/tasks/3`), but populated only with the original, unreviewed InsightFace proposals from `calibration_batch_40_predictions.json` — never Task 3's corrected coordinates. 2,720/2,720 points verified matching the raw proposal file exactly; 0 tags (no invented review status). **Task 3 confirmed byte-for-byte unchanged** before/after (direct full-annotation dict equality). Task 4's SVG was freshly generated (not copied from Task 3) to avoid repeating the earlier Task-2 rendering bug.

---

## [2026-10-19 UPDATE 14] Audit of the 11 Heavily-Corrected Calibration Images — No Issue Found, Two Correction Patterns Identified

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §19. Audited the 11 images with near-complete (46–68/68) point corrections. **No evidence of annotation/export corruption or detection failure** — all 68 landmark indices/names verified intact on every image. **Key finding:** the 11 split into two distinct patterns — **6 images show a mathematically exact, bit-identical displacement across all 68 points** (e.g. `frame_000198_face02`: every point shifted by precisely `(5.253249, 5.828802)`), the signature of a whole-skeleton drag/translate in CVAT, not 68 independent point judgments; **5 images show genuine point-by-point variance**, consistent with individual correction (same pattern as the 24-image pilot). This refines, without invalidating, the earlier "714/2,720 points changed" statistic — its granularity is uneven across images. 10 of these 11 are tagged `review_status: ok` (only 1 `low_quality`), suggesting the tag reflects post-correction confidence, not pre-correction proposal quality.

---

## [2026-10-19 UPDATE 13] Calibration Batch (Task 3) Reviewed, Exported, QC'd

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §18. The user completed human review of all 40 Task 3 images (confirmed real: `updated_date` advanced 7 hours past creation, 40/40 `review_status` tags present — **30 `ok`, 10 `low_quality`, 0 `needs_review`**).

Exported (`experiments/EXP-PAP-005/calibration_batch_40_reviewed.json`, 2,720 records) and QC'd clean (0 errors). Comparison vs. the original InsightFace proposals: **714/2,720 points changed (26.2%)**, concentrated in **11 of 40 images** — notably, most corrected images show **all or nearly all 68 points changed** (verified as genuine per-point correction, not a uniform-shift artifact), a different pattern than the 24-image pilot's partial corrections. **0 points flagged `occluded`** — the point-level uncertainty mechanism was not exercised in this batch, flagged as an open question for the design, not an error. Original↔CLAHE pairing re-verified for all 40 (0 mismatches). Not yet checked: whether the 11 corrected images overlap with the 10 `low_quality`-tagged ones — flagged as a natural next step, not computed here.

---

## [2026-10-19 UPDATE 12] Bug Found and Fixed — Correct Task ID Is 3, Not 2

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §17. **Task ID 2 (Update 11) crashed the CVAT UI** on open — root cause confirmed: its skeleton SVG was copied verbatim from Task 1, carrying hardcoded `data-label-id` references to Task 1's specific sublabel database IDs, which don't exist in Task 2. Task 2 was deleted (0 review progress existed on it) and **recreated as Task ID 3** (`http://localhost:8070/tasks/3`), this time generating a fresh, self-consistent SVG rather than reusing another task's saved one. Re-verified: 40/40 images, 2,720/2,720 points, 0 mismatches — identical data integrity to the original import, just without the broken SVG. Task 1 reconfirmed unaffected throughout. **Use Task 3 going forward — Task 2 no longer exists.**

---

## [2026-10-19 UPDATE 11] Calibration Task Implemented — CVAT Task 2, Ready for Human Review

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` §16. The 40-image calibration batch designed in Update 10 was actually implemented: InsightFace predictions generated for all 40 (0 failures, reusing the same tight-crop fix as EXP-PAP-005), a **new** CVAT task created (**Task ID 2**, `http://localhost:8070/tasks/2`) reusing Task 1's exact 68-point skeleton label plus one new `review_status` tag (ok/needs_review/low_quality), 40 images + 2,720 skeleton points imported and verified via API with **0 coordinate mismatches** against the raw prediction artifact. Point-level uncertainty uses the skeleton's existing native `occluded` field — no new per-point schema added. **Task 1 confirmed unchanged** (still 24 shapes, job state still `in progress`). **Human review has not started** — Task 2 is populated and ready.

---

## [2026-10-19 UPDATE 10] Next Calibration Batch Designed (Not Executed)

Full detail: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md`. Designed the next annotation batch: 40 images (seed=300, 4 per area-decile stratum, drawn from the 621 images not already in EXP-PAP-005), plus a minimal uncertainty-capture mechanism — confirmed from CVAT's live schema and source that labels/sublabels already support an `attributes` array (checkbox/radio/number/text/select types) and that every skeleton point already has a native, unused `occluded`/`outside` boolean. Recommended mechanism: reuse `occluded` for point-level "can't confidently judge" (zero schema change), one new `review_status` tag label for image-level status (on a new task only — Task 1 untouched), and an external manifest for uncertainty reasons — deliberately the least disruptive combination, not a new multi-attribute skeleton schema. Full reviewer protocol and acceptance criteria defined. **Nothing executed:** no predictions generated for the 40 images, no new CVAT task created, Task 1 unmodified.

---

## [2026-10-19 UPDATE 9] Dataset-Wide Quality Audit (645 Images) — No Threshold Set

Full detail: `docs/reports/PAPUAN_V2_DATASET_QUALITY_AUDIT.md`. Audited all 645 Original/CLAHE crop pairs for inventory integrity and quality-relevant distributions before any scale-up decision.

**Verified clean:** 645/645 Original↔CLAHE pairs present, 0 missing/duplicate/mismatched, 0 dimension mismatches between Original and CLAHE (full-dataset re-confirmation of the geometric-identity property), 0 aspect-ratio outliers (truncation indicator), 645/645 images open successfully, all RGB. Dimension range: 22×25px to 697×966px (median 67×91px, area median 6,097px²). Blur-variance (Laplacian, a standard no-new-dependency heuristic) computed for all 645; weak correlation with crop area (Pearson r=−0.209, reported neutrally, not interpreted causally given known scale-sensitivity of the metric). No pre-existing quality/confidence metadata found anywhere in the project for any image — every signal in this audit was newly computed.

**No numeric quality threshold was set — explicitly, per instruction.** The audit characterizes the dataset's distribution but found no existing reviewer-grounded data (beyond the 24-image pilot) to calibrate a threshold against. Recommended minimal policy: add a CVAT "uncertain" flag for the *next* annotation batch (not retroactive) to generate that missing reviewer-judgment data, deferring any dimensional-threshold decision until real data supports one. CVAT job 1 re-confirmed still `"in progress"` (read-only check, not modified).

---

## [2026-10-19 UPDATE 8] Reviewer Confirms Full Review; Image-Quality Limitation Documented

Full detail: `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md` §20. The reviewer confirmed directly that all 24 images were visually reviewed, that some needed no correction, that some had image-quality/resolution limitations making confident localization difficult, and that the 5 images already identified from coordinate comparison (Update 7) were the ones manually corrected. This resolves the "was review performed at all" question from Update 7.

**Still unresolved, explicitly flagged, not guessed at:** which of the 19 unchanged images were accepted because the AI proposal was verified correct, versus accepted because low resolution made correction impractical — no per-image quality flag exists in any artifact. A new objective finding: the pilot's 3 smallest crops (616–1,628 px²) all show zero corrections, a pattern *consistent with* (not proof of) the quality-limitation explanation, alongside two of the most heavily-corrected images being comparatively large — i.e., **no simple size-correlates-with-correction relationship exists in this data**. `experiments/EXP-PAP-005/metadata.json` updated accordingly: `review_status` now reflects confirmed full review, plus a new `image_quality_limitation_note` field. A quality-control rule (minimum-resolution flagging before full-scale annotation) is proposed but **not implemented or approved** — pending decision.

---

## [2026-10-19 UPDATE 7] Pilot Review Exported and QC'd — Review Coverage Ambiguity Found

Full detail: `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`. Exported CVAT task 1's current annotations (`experiments/EXP-PAP-005/cvat_reviewed_landmarks.json`, 1,632 points, 24/24 images, structural QC PASS) and compared against the original InsightFace proposals.

**Key verified-but-unresolved finding:** only 5 of 24 images show any point correction beyond a 0.5px tolerance (19–66 of 68 points changed each); the other 19 images are coordinate-identical to the original AI proposal. CVAT's own job metadata (task 1, job 1) still reads stage=`"annotation"`, state=`"in progress"` — not `"completed"` — despite the user reporting all 24 images reviewed. **This report does not resolve whether the 19 zero-change images were genuinely accurate proposals or not actually reviewed** — flagged explicitly for the user to clarify before any scale-up decision. `experiments/EXP-PAP-005/metadata.json`'s `review_status` was updated to reflect this ambiguity rather than asserting full completion.

Overall correction rate across all 1,632 points: 13.5% (220 points), median displacement 8.27px among corrected points. Original↔CLAHE pairing re-verified for all 24 images (identical dimensions, confirming the existing coordinate-reuse design remains valid).

---

## [2026-10-18 UPDATE 6] CVAT Abbreviations Clarified (Side/Detail-Encoded)

Full detail: `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md` §14. The plain region+index abbreviations from Update 5 (`ns0`...`ns4`) lost left/right and inner/outer information. Replaced with side/detail-encoded names (e.g. `nsli` = nose, left, inner — the reviewer's own example) while keeping the same 68 indices. Validated the same way as Update 5: snapshot-before vs. after showed 1,622/1,632 points unchanged by the rename itself; the remaining 10 (a complete eyebrow region on one frame) were the reviewer's own in-progress correction, made concurrently and preserved correctly, not lost — confirmed via the task's advancing `updated_date` and the coherent (non-random) shape of the difference.

---

## [2026-10-18 UPDATE 5] CVAT Labels Abbreviated During Active Human Review

Full detail: `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md` §13. While reviewing the pilot, the reviewer found the full anatomical label names (`right_eye_outer_corner`, etc.) too visually crowded on the canvas. Renamed to short region+index form (e.g. `j0`...`j16` for jaw, `re0`...`re5` for right eye) via the same validated-safe PATCH mechanism — same 68 point indices/semantics, only the display name changed. **Validated against a snapshot of the live task taken immediately before the rename** (not just the original AI predictions), since human review was already in progress at the time: all 1,632 points and all occlusion/outside flags were confirmed identical before and after, so no review progress was lost. This is now the naming convention in effect for ongoing review.

---

## [2026-10-02 UPDATE 4] CVAT Skeleton Labels Renamed to Anatomical Names

Full detail: `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md`. The pilot's CVAT skeleton originally used generic `pt0`...`pt67` labels, which a human reviewer could not map to anatomical features. All 68 labels were renamed (e.g. `pt36` → `right_eye_outer_corner`, `pt33` → `nose_tip`) via CVAT's label-PATCH API, verified safe (no task recreation needed — CVAT references annotations by label `id`, not `name`). Full before/after validation on all 24×68=1,632 points confirmed **zero coordinate drift** and exact index-identity preservation. The verified index→anatomical mapping (confirmed via mean-shape geometry, empirical pixel checks across 5 real images, and the model's exact structural match to the ibug-300W convention) is documented in the linked report, including an explicit "right"/"left" = subject-anatomical (not image-space) convention with its one disclosed caveat (unverified assumption that source frames aren't mirror-flipped). A CVAT API pitfall was found and documented: the annotations endpoint's `elements` array is not ordered by point index — joins must always use `label_id`.

---

## [2026-10-02 UPDATE 3] EXP-PAP-005 CVAT Landmark Pilot — Implemented (24-image pilot, human review pending)

Full detail: `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md`. Following the three methodology decisions confirmed by the user/supervisor (68-point InsightFace schema; Original-only annotation; InsightFace predictions as initial CVAT proposals), a working pilot was implemented end-to-end through the import step:

- **CVAT deployed locally** (self-hosted, Docker Compose, now running at `http://localhost:8070` — remapped from the default 8080 after discovering a port collision with the still-running Annotator A Label Studio server; Label Studio itself was not touched).
- **24-image pilot subset** selected deterministically (seed=200, distinct from the project's existing seeds 42/100) from the existing 150-image EXP-PAP-004 pilot set.
- **InsightFace `landmark_3d_68` predictions generated** for all 24 Original crops (after fixing a SCRFD re-detection failure on tight crops — the same bug/fix pattern already documented for this project's ArcFace pipeline). QC validation: 0 errors, 5 minor non-fatal out-of-bounds warnings (jaw/ear points near one tight crop's edge).
- **CVAT task created** with a 68-point skeleton label, 24 images imported, 24 InsightFace-generated skeletons imported as initial proposals — verified via API (24/24 frames, 68/68 points each, no gaps).
- **Human review has not yet been performed** — the pilot is ready and waiting for the single human reviewer's pass.
- New in-repo artifacts: `experiments/EXP-PAP-005/` (metadata, predictions, QC script).

---

## [2026-10-02 UPDATE 2] Landmark Schema & AI-Proposal Methodology Gates — Investigated

Full detail: `docs/reports/PAPUAN_V2_LANDMARK_SCHEMA_AND_ANNOTATION_METHOD.md`. Branch used for this and all subsequent work: **`main`** (per explicit instruction; the audit branch `worktree-papuan-v2-audit` is preserved untouched as the historical archive, not merged/cherry-picked — its content was ported to `main` as a plain file copy, see commit `de3c238`).

**Resolved by direct evidence in this investigation:**
- **CLAHE does not change pixel geometry** in this codebase's implementation (pure L-channel intensity transform, no resize/crop/warp — confirmed by code inspection and direct pixel-dimension measurement). Consequence: **independent CLAHE-branch annotation is not scientifically required** — Original-branch landmark coordinates can be reused as-is (identity-mapped) for the CLAHE branch's training target. Recommended against independent re-annotation, pending supervisor confirmation of this simplified design.
- A 68-point landmark schema is obtainable from an already-installed dependency (InsightFace's `landmark_3d_68` sub-model, currently excluded via `allowed_modules`) — no new package required.
- The 10 MediaPipe iris points (of its 478-point output) are unused by any code in this repository today and add annotation cost without a realized use case.

**Still requiring supervisor confirmation (not decided by this audit):** final landmark schema (68-point recommended over 468/478-point, with stated assumptions); whether AI-generated proposals are shown to annotators at all, and if so from which source (InsightFace preferred over MediaPipe on circularity grounds — MediaPipe risks the same self-referential-evaluation pattern already flagged for the superseded HSEmotion/ArcFace emotion track); confirmation of the Original-only-annotation-with-coordinate-reuse design as a substitute for the originally-envisioned two-independent-branch design.

---

## [2026-10-02 UPDATE 1] Research Direction Pivot: Facial Landmarks Supersede Emotion Labels as the Primary Target

**The primary annotation target has changed from facial expression labels to facial landmarks, following a supervisor clarification (Pak Fadhil) on 2026-10-02.** Full detail, audit evidence, and risk analysis: `docs/reports/PAPUAN_V2_METHODOLOGY_PIVOT_2026-10-02.md`. Chronological detail: `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`.

### Historical / Exploratory (preserved, not deleted, no longer primary)

- FER emotion annotation methodology (EXP-PAP-001–004): dataset foundation, HSEmotion/ArcFace+LR predictions, Label Studio two-annotator blind pilot.
- Annotator A's completed, validated 150/150 export (`experiments/EXP-PAP-004/label_studio_export.csv`) — kept as a real, valid research artifact of the exploratory track, not discarded.
- Annotator B's stood-up (75-task, isolated-server) but unlabeled infrastructure — left running/intact, status of continuing it unresolved (see pivot report's "Risks / Open Questions").
- The AI-assisted (emotion) annotation methodology design review (`PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`) — never implemented, now superseded as the active methodology question, but retained as valid design work.
- All Phase 0–6 sections and reports below/elsewhere describing the emotion-annotation track are **SUPERSEDED as the primary direction**, not retracted as findings — they remain an accurate record of what was investigated and why.

### Current Primary Direction

Facial landmark annotation, reviewed in CVAT, on two parallel branches (original vs. CLAHE face crops), each producing its own trained landmark model for comparison:

```text
Raw images
    │
    ▼
Face detection/crop
    │
    ├─────────────────┬─────────────────┐
    ▼                 ▼
Original           CLAHE
    │                 │
    ▼                 ▼
Landmark           Landmark
annotation         annotation
    │                 │
    ▼                 ▼
CVAT review        CVAT review
    │                 │
    ▼                 ▼
Training           Training
    │                 │
    └────────┬────────┘
             ▼
Original vs. CLAHE landmark model comparison
```

### Phase Status (landmark track — reflects actual repository state, not aspiration)

| Phase | Status | Notes |
|---|---|---|
| Dataset foundation | DONE | Existing 645-crop face extraction pipeline (original + CLAHE), reused as-is for the landmark track. |
| Landmark annotation design | IN PROGRESS (planning) | This pivot audit; schema/auto-proposal/CVAT-deployment questions open, not yet decided. |
| Pre-existing landmark extraction (MediaPipe) | PARTIAL / DISCOVERED | `src/fer_dataset/pipeline/landmark_analyzer.py` already exists and already covers 85/645 face crops (20/150 pilot images) — predates this pivot, built for a different purpose, not yet run at full scale. |
| Original landmark annotation | IN PROGRESS (pilot) | 24-image pilot subset selected and InsightFace-initialized in CVAT; awaiting human review. Full 645-image scale-up not started. |
| CLAHE landmark annotation | NOT STARTED | Depends on CVAT setup. |
| CVAT review (both branches) | IN PROGRESS (pilot) | CVAT now deployed locally (`http://localhost:8070`), EXP-PAP-005 pilot task populated with 24 images + InsightFace-initialized 68pt proposals; human review pass not yet performed. See `PAPUAN_V2_CVAT_LANDMARK_PILOT.md`. |
| Original landmark training | NOT STARTED | No landmark training code or model architecture exists in the repo yet; architecture choice explicitly deferred pending evidence/design discussion. |
| CLAHE landmark training | NOT STARTED | Same as above. |
| Model comparison (Original vs. CLAHE) | NOT STARTED | Depends on both training phases. |
| Old FER emotion annotation (EXP-PAP-004) | SUPERSEDED | Exploratory track; Annotator A's 150/150 export remains valid and preserved; Annotator B infrastructure left standing, continuation undecided. |

---

The Papuan V2 pipeline has a solid, tested foundation (frame extraction → face detection → CLAHE → AI-candidate predictions, 645 crops / 150-image pilot subset) and a well-designed, genuinely-isolated two-annotator Label Studio pilot (EXP-PAP-004), plus a narrow but real architecture-validation exercise (Phase 1, throwaway port-8090 server, 20 passing tests) confirming that a shared Label Studio instance can safely serve multiple annotators without leaking content. However, the project is currently **blocked at the human-labeling step**: of 150 pilot images, **0 have a human ground-truth label** (one real Label Studio annotation exists but was never copied into `human_labels.csv`), and the secondary annotator has completed 0 of 75 overlap images. Every downstream step — AI-candidate selection, agreement metrics, consensus, ground truth, model evaluation — is consequently blocked, by code-enforced guards, not just by policy.

Separately, and this is the most important finding for the supervisor's new direction: **AI-assisted annotation (AI pre-label → human review/correction inside Label Studio) does not exist in this repository in any form.** No ML backend, no paid-AI-provider integration, no prediction-import code, no provenance schema for "AI suggested, human corrected." The existing `ai_predictions.csv` is an offline comparison artifact for selecting *which* model to use later, not an implementation of AI-assisted annotation itself. This is a greenfield phase requiring a methodological decision (blind vs. pre-filled annotation) before any implementation should begin.

## Phase Status

| Phase | Status | Evidence | Main Blocker |
|---|---|---|---|
| 0 — Dataset/Pipeline Foundation | DONE (pilot scale) | `data/papuan_v2/{faces,clahe}/` (645 each), `experiments/EXP-PAP-004/pilot_manifest.csv` | Full-dataset scope (uncapped video) undecided |
| 1 — Architecture Validation | DONE | `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` Phase 1 section, 20 passing tests | None (self-contained) |
| 2 — EXP-PAP-004 Pilot | BLOCKED | `human_labels.csv` 0/150 filled; `annotator_progress.json` | Human labeling not performed |
| 3 — AI-Assisted Annotation | NOT IMPLEMENTED | No code found anywhere in repo | Methodology decision not made; no implementation started |
| 4 — Human-Validated Ground Truth | NOT STARTED | No `final_labels.csv`/`consensus.csv` exist | Depends on Phase 2 + Phase 3 |
| 5 — Model Evaluation | BLOCKED | `pilot_agreement_report.py` refuses to run (RuntimeError guard) | Depends on Phase 2 |
| 6 — Agreement & Robustness | BLOCKED | Metric code tested on synthetic data only | Depends on Phase 2 |

## Current Pipeline (as actually implemented today)

```
pesta_babi.mp4
     │  (EXP-PAP-001, capped 250 frames)
     ▼
645 face crops  ──CLAHE──▶  645 CLAHE crops
     │
     │ (EXP-PAP-002, seeded sample, n=150)
     ▼
150-image pilot set (data/papuan_v2/pilot/images/)
     │
     ├────────────────────────────┐
     ▼                             ▼
AI predictions (offline,      Label Studio (2 isolated servers)
both candidates,              Project A (:8080) — Annotator A, 150 tasks
150/150 each)                 Project B (:8081) — Annotator B, 75 overlap tasks
ai_predictions.csv                  │
     │                              ▼
     │                       human_labels.csv  ◀── 0/150 FILLED (BLOCKED HERE)
     │                              │
     └──────────────✗ (no agreement run yet) ✗──┘
                        ↓ (blocked)
          pilot_agreement_report.py / human_agreement_report.py
                        ↓ (blocked)
          AI-candidate selection decision (human, manual)
                        ↓ (not started)
          Full-dataset AI-assisted annotation  ◀── DOES NOT EXIST
                        ↓ (not started)
          consensus.csv / final_labels.csv / ground truth  ◀── DOES NOT EXIST
                        ↓ (not started)
          HSEmotion / ArcFace evaluation against ground truth
```

## Annotation Architecture (as actually implemented)

```
Pilot (EXP-PAP-004, real):
  Server :8080 — Project "EXP-PAP-004 Papuan V2 Pilot (Blind)" (id=2)
    └─ Annotator A — 150 tasks, overlap=2 on 75 of them
  Server :8081 — Project "EXP-PAP-004 Overlap (Annotator B)" (id=1)
    └─ Annotator B — 75 tasks (deterministic overlap subset, seed=100)
  Isolation mechanism: SEPARATE SERVER PROCESSES (separate port/data-dir/DB/org) —
  required because Label Studio Community 1.23.0 has no per-project role-based
  isolation (OrganizationMember has no role field).

Phase 1 validation (throwaway, torn down):
  Server :8090 — Project "PHASE1-VALIDATION (throwaway, not pilot)" (id=1, separate org/DB)
    └─ 4 synthetic users (1 owner + 3 annotators), 3 synthetic fixture tasks
  Confirmed: a SHARED project with task.overlap=3 does NOT leak co-annotator
  content before submission (only a non-content annotation-count is visible).
  This validates that a shared-instance design (no longer requiring separate
  servers) is viable FOR THE FUTURE full 3-annotator workflow — not yet adopted
  for anything real.
```

## Dataset State

- **Images**: 645 face crops (`data/papuan_v2/faces/`) + 645 CLAHE crops (`data/papuan_v2/clahe/`) + 150-image pilot subsample (`data/papuan_v2/pilot/images/`, CLAHE only).
- **Locations**: all under `data/papuan_v2/`; experiment artifacts under `experiments/EXP-PAP-004/`.
- **Preprocessing state**: CLAHE Strategy B applied and used as the sole input for all pilot/AI-prediction work; non-CLAHE originals preserved but unused downstream so far.
- **Labels**: 0 human ground-truth labels exist for the pilot (150/150 `human_labels.csv` rows blank); exactly 1 real Label Studio annotation exists in the system (`frame_000008_face01` → `Neutral`/`Medium`, not yet propagated into `human_labels.csv`'s `gt_label`); 300 AI-candidate prediction rows (150 × 2 models) exist and are complete.
- **Splits**: none — no train/test/val split exists or is needed yet (ArcFace classifier was trained entirely on legacy, non-Papuan-V2 data).
- **IDs/lineage**: strong — `pilot_manifest.csv` records `image_id`, source paths, sampling seed, and timestamp for every pilot image; `source_video_manifest.json` records video SHA-256 and extraction parameters.
- **Missing metadata**: full-dataset-scope decision (645 vs. re-extracted larger pool) is undocumented/undecided; AI-prediction schema lacks `ai_model_version`/`input_preprocessing`/`source_crop_path` fields the full-workflow plan proposes adding.

## Model State

- **HSEmotion** (`enet_b0_8_best_vgaf`, `hsemotion-onnx==0.3.1`): predictions complete on the 150-image pilot (150/150 ok); zero evaluation metrics computed (blocked on ground truth).
- **ArcFace + LogisticRegression** (`buffalo_l/w600k_r50` embeddings, classifier trained on **legacy**, non-Papuan-V2 data via `tools/train_arcface_classifier.py`): predictions complete on the 150-image pilot (150/150 ok, after a documented re-detection bugfix); classifier/embedding pipeline has a known, explicitly-documented distributional mismatch between training (aligned) and inference (unaligned, direct `get_feat()`) paths; zero evaluation metrics computed.

## Human Annotation State

- **Tasks**: 150 assigned to Annotator A, 75 (deterministic overlap, seed=100) assigned to Annotator B.
- **Annotators**: 2 real identities confirmed working (`Annotator A` has 1 real submitted annotation); Annotator B's identity/server is set up but has 0 submissions.
- **Completion**: 1/150 (A), 0/75 (B).
- **Overlap**: correctly, deterministically computed (75 of 150 images, seed=100) and reflected in `annotator_assignment.csv`; Task 1's existing annotation was preserved byte-identical through the overlap-PATCH operation (verified).
- **Exports**: `label_studio_export.csv` exists with exactly 1 real data row; export pipeline is otherwise validated only via unit tests with synthetic data.
- **Agreement**: `null` / not computed — both the AI-vs-human and human-vs-human agreement scripts refuse to run against incomplete data (enforced by a runtime guard, not merely absent).

## AI-Assisted Annotation State

- **Implemented**: NO. Confirmed by repo-wide search — no ML backend, no paid-AI-provider SDK/dependency, no prediction-import code, no pre-annotation UI/workflow.
- **Current technology**: Label Studio Community Edition 1.23.0, self-hosted via local server processes (no Docker). Native `task["predictions"]` import mechanism exists in Label Studio itself and is structurally usable, but unused by any script in this repo.
- **Required changes**: (1) supervisor decision on blind-vs-pre-filled AI suggestion visibility to annotators; (2) decision on paid-AI-provider vs. self-hosted-model source for pre-annotations, and whether that source overlaps with HSEmotion/ArcFace+LR (circularity risk if so); (3) new provenance schema fields (`ai_suggested_label`, `human_accepted_ai`, `human_correction_reason`, `ai_model_version`); (4) a Label Studio prediction-import script; (5) human-review-workflow enforcement (AI output must never silently become the stored label without a human action).
- **Open methodological questions**: see the dedicated review section below.

## Blockers

1. **(Primary, cascades to everything downstream)** No real human labels exist for the EXP-PAP-004 pilot — 0/150 (A), 0/75 (B). This is a deliberate gap: the repository's own `report.md` states the implementing assistant declined to fabricate labels, since doing so would defeat the pilot's independence/circularity safeguards.
2. AI-assisted annotation (the supervisor's new direction) has zero implementation and an unresolved methodology decision (blind vs. pre-filled suggestion) that must be made by a human before building anything.
3. Dataset-size scope (645 crops vs. a larger re-extraction) is undecided and blocks any "full workflow" (`EXP-PAP-010`+) work.

## Recommended Next Actions (ordered by dependency, no scope expansion)

1. Complete real human labeling for the 150-image pilot (Annotator A) and the 75-image overlap (Annotator B) — this is a human task, not something that can be automated or delegated further in code.
2. Run `pilot_agreement_report.py` and `human_agreement_report.py` against the now-complete data to produce real metrics.
3. Human (supervisor/researcher) reviews the metrics and records the AI-candidate-selection decision in `docs/EXPERIMENT.md`.
4. Resolve the AI-assisted-annotation methodology decision (Option 1 vs. Option 2, and paid-provider vs. self-hosted) — a discussion/decision task, not an engineering task.
5. Only after 1–4: design and implement the AI-assisted pre-annotation workflow (Phase 3), the extended provenance schema, and the ground-truth/consensus pipeline (Phase 4), followed by real model evaluation (Phase 5) and full agreement/robustness analysis (Phase 6).
6. Separately and independently of 1–5: decide the dataset-size scope (645 vs. larger) before any `EXP-PAP-010`-series full-manifest work begins.

---

## Next Decision: AI-Assisted Annotation Methodology

A full design review comparing three candidate AI-assisted annotation workflows (both annotators see the AI pre-label / one assisted + one blind / assisted-plus-audit-sample), an evaluation-leakage analysis, a minimal provenance schema, and three concrete implementable protocols is in `docs/reports/PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`. No design is implemented yet; the blocking decision is whether the AI pre-label should be shown to both annotators, one annotator (with the other kept blind as a control), or neither (AI compared only after human labels are finished) — this determines whether the existing 75-image overlap still measures classic human-human agreement or something else. See that document's Section 7 for the exact questions to raise with Pak Fadhil before any implementation begins.

---

# AI-Assisted Annotation Methodology Review

Evaluating the proposed workflow: CLAHE crop → paid AI-assisted annotation → AI pre-label → human review → human correction → final human-validated label → ground truth → HSEmotion/ArcFace evaluation.

## 1. Is this methodologically defensible?

Yes, in principle — "AI-assisted annotation with mandatory human review" is a recognized and defensible annotation methodology, provided the human review is substantive (not rubber-stamping) and the process is documented transparently. It is defensible *conditionally*: the repository's own existing safeguards (never let AI auto-become ground truth, preserve raw human judgment, write-once final labels) are the right shape of guardrail and should carry forward into this new direction.

## 2. Could AI pre-labeling introduce bias?

Yes — this is the central risk, and it is well-documented in the project's own planning materials even though those materials predate the "paid AI-assisted annotation" instruction. Anchoring bias is explicitly named in `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md` §3.3: "three annotators shown the same AI suggestion are not three independent judgments anymore; measured inter-annotator agreement would be inflated by shared anchoring, not genuine consensus." The same logic applies here: a human reviewer shown a plausible-looking AI suggestion is measurably more likely to accept it than to independently derive the same answer from scratch, even when the suggestion is wrong — this is a well-established finding in human-AI collaboration research generally, not specific to this project.

## 3. How to prevent circular evaluation?

The single most important structural choice: **the model(s) used to generate the AI pre-label should not be the same model(s) later evaluated against the resulting ground truth** (or, if unavoidable, the overlap must be explicitly disclosed and ideally measured). Concretely for this project: if HSEmotion or ArcFace+LR is used to pre-fill annotations, then evaluating that same model's accuracy against the resulting "human-validated" labels is partially circular, because human correction behavior is itself biased toward the AI's suggestion (point 2). A clean alternative is to use a third, independent model/provider (e.g., a general-purpose paid LLM/VLM API, distinct from both evaluated candidates) for pre-annotation, keeping HSEmotion and ArcFace+LR purely as the *evaluated* systems, never the *annotation assistant*.

## 4. Should human annotation remain independent between annotators?

For the *first* independent judgment, yes — nothing in the supervisor's new instruction necessarily requires abandoning this. The existing architecture (separate servers or, per Phase 1's validated finding, a shared instance with `overlap=N` and content hidden until submission) already supports this and should be reused rather than redesigned.

## 5. Should both annotators see the AI pre-label?

This is a genuine trade-off, not a question with a single correct answer:
- **Both see it**: faster annotation, matches "AI-assisted" literally, but risks correlated anchoring across annotators, which would inflate measured human-human agreement in a way that doesn't reflect genuine independent consensus.
- **Neither sees it initially** (AI compared only after independent human labeling): preserves the cleanest "independent human judgment" claim, forfeits the speed benefit, and arguably stops being "AI-assisted annotation" in the sense the supervisor likely intends.

## 6. Should one annotator remain completely blind to AI suggestions?

This is a concrete, practical design the project's existing two-annotator infrastructure makes nearly free to implement: have Annotator A label with the AI suggestion hidden (preserving a clean independent-human baseline), and Annotator B label with the AI suggestion visible (measuring the AI-assisted workflow's actual behavior, including acceptance/correction rates). This directly reuses the existing isolated two-server architecture and would let the project measure the anchoring effect itself, empirically, rather than just worrying about it abstractly — turning a risk into a measured variable. This is an option worth the supervisor's explicit consideration, not a decision this audit makes.

## 7. What metadata/provenance must be stored?

At minimum: `ai_model` / `ai_model_version` / `ai_provider` (for a paid external API, record the exact model/version string and the query/call timestamp — API-backed models change silently over time, unlike pinned local packages); `ai_suggested_label` (preserved verbatim, never overwritten); `human_label` (the human's final choice); `human_accepted_ai` (bool: did the human keep the AI's suggestion unchanged); `human_correction_reason` (free text, optional); `annotator_identity` (real, resolvable — continuing this project's existing "never fake annotator IDs" principle); `review_started_at` / `review_completed_at` (to later analyze whether AI suggestions measurably sped up review, a legitimate research question this design enables). This extends, rather than replaces, the existing provenance conventions already established in `pilot_manifest.csv`/`ai_predictions.csv`.

## 8. How to report AI-assisted annotation in the thesis/paper?

Report explicitly and quantitatively, not just as a methods-section sentence: which model/provider generated pre-labels, on what fraction of images the human kept vs. changed the AI suggestion (this is itself a useful descriptive statistic), whether any annotator was kept blind to AI suggestions as a control (per point 6), and — critically — an explicit circularity statement disclosing whether the pre-annotation source overlaps with the evaluated models (per point 3), even if the answer is "no, we used a different model/provider for pre-annotation specifically to avoid this." A reviewer/examiner is likely to ask about exactly this; having the disclosure ready, with numbers, is stronger than silence.

---

*Generated by repository audit, 2026-10-01. No code, dataset, Label Studio configuration, or experiment data was modified in the course of this audit.*
