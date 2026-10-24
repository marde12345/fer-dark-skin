# Papuan V2 — Annotation Calibration Batch Plan (Post-EXP-PAP-005)

## 1. Objective

Design (not execute) the next calibration annotation batch, including a minimal review-uncertainty capture mechanism and a deterministic, stratified image sample, before any full-dataset (645-image) annotation begins. This is a design document — no new annotation, no new predictions, no CVAT task created or modified.

## 2. Current Branch

`main` (verified via `git branch --show-current`).

## 3. Verified Audit Findings (carried forward, not re-derived)

From `docs/reports/PAPUAN_V2_DATASET_QUALITY_AUDIT.md`: 645 Original/CLAHE pairs, 645/645 matched with identical dimensions, area range 550–655,180 px² (median 6,097), width 22–697px, height 25–966px, 0 aspect-ratio outliers, all RGB, Laplacian blur-variance computed for all 645 (weak, non-causal correlation with area, r=−0.209), no pre-existing quality metadata anywhere. From `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`: the 24-image EXP-PAP-005 pilot is reviewed and corrected (5 images, 220/1,632 points changed); CVAT Task 1 / Job 1 still reports `stage: "annotation"`, `state: "in progress"`. No numeric image-quality threshold has been approved.

## 4. CVAT Uncertainty/Attribute Capabilities (verified from live schema + source, not assumed)

Checked directly against the running CVAT instance (`GET /api/labels?task_id=1`, read-only) and the CVAT source (`cvat/apps/engine/models.py`, `AttributeType` enum):

- **Both the parent skeleton label and every individual sublabel (point) already carry their own `attributes` array** in the live schema (`face68`'s `attributes: []`, and each of its 68 sublabels' `attributes: []`) — confirmed structurally present, currently unused (empty), not something that would need to be newly invented from scratch.
- **Supported attribute input types:** `checkbox`, `radio`, `number`, `text`, `select` (from `AttributeType`) — a `select`-type attribute with a fixed option list is directly usable for a "reason" field (low_resolution / blur / occlusion / ambiguous_location / other).
- **Every skeleton point element already carries native `occluded` and `outside` boolean fields** on every annotation (confirmed throughout this project's own exports, e.g. `cvat_reviewed_landmarks.json`'s `occluded`/`outside` fields, present and populated — currently always `false` in the existing pilot, but structurally live and already round-tripping correctly through export). **This is a zero-schema-change mechanism already available today.**
- **CVAT also supports a `tag`-type label** (`LabelType.TAG`, confirmed in `cvat-ui` source), a label that attaches to a whole frame/image independent of any shape — the natural fit for an image-level review-status flag, structurally separate from the point-level skeleton.
- **Limitation confirmed, not assumed:** adding new attributes to sublabels requires a label-schema PATCH (the same mechanism already used, and already proven safe, for the point-renaming work in the earlier pilot) — this is a real, if minor, schema change, not something CVAT supports "for free." It was **not** applied to Task 1's existing `face68` label (per the explicit constraint not to modify Task 1); any such change belongs only to a newly-created calibration task's own label config.

## 5. Proposed Minimal Uncertainty Representation

Recommended as a **small combination of CVAT-native fields and an external review manifest**, deliberately avoiding a complex per-point attribute scheme:

| Need | Mechanism | Why this one |
|---|---|---|
| Landmark-level "cannot confidently place this point" | **Reuse CVAT's existing, already-native `occluded` boolean** on the relevant skeleton element | Zero schema change — this field already exists on every point in every CVAT skeleton task, already proven to export/import correctly throughout this project. No new label-schema PATCH needed at all. |
| Image-level review status (reviewed-ok / needs-further-review / quality-flagged) | **One new CVAT `tag`-type label** (e.g. `review_status`, with a `select` attribute: `ok` / `needs_review` / `low_quality`) on the **new calibration task only** | Gives the reviewer a native, one-click-per-image action inside the CVAT workflow itself (better usability than a separate external form mid-review), structurally independent of the skeleton — does not touch or require modifying the point schema. |
| Reason for uncertainty (low resolution / blur / occlusion / ambiguous location / other) | **External review manifest**, a CSV/JSON keyed by `(image_id, landmark_index)` for point-level reasons and by `image_id` for image-level reasons | Avoids adding a `select` attribute to all 68 sublabels (which Section 4 confirmed is *possible* but is the more invasive option) — keeps the CVAT label schema change to the single new tag label, nothing on the skeleton itself. The manifest is filled in alongside review (not a replacement for it), and is trivially joinable back to the CVAT export by the same `image_id`/`landmark_index` keys already used throughout this project. |

**This is deliberately the least disruptive viable option**, per instruction: one new tag label (not touching the skeleton at all), reuse of an already-existing boolean field for point-level flagging, and a lightweight external file for free-text/categorical reasons — no multi-user workflow, no new CVAT project, no modification to Task 1.

## 6. Deterministic Stratified Sample Design

**Sampling frame:** the 621 images in the 645-image pool **not already covered by EXP-PAP-005** (645 − 24 = 621; verified directly, not assumed).

**Stratification:** 10 strata, by **area decile**, computed from the already-audited **full 645-image distribution** (not re-derived from the smaller eligible pool, so the strata boundaries stay anchored to the dataset-wide audit, not re-biased by exclusion):

| Decile | Area range (px²) | Eligible images in stratum (of 621) |
|---|---|---|
| 0 | 550 – 2,188 | 62 |
| 1 | 2,188 – 2,903 | 63 |
| 2 | 2,903 – 3,763 | 61 |
| 3 | 3,763 – 4,491 | 60 |
| 4 | 4,491 – 6,097 | 62 |
| 5 | 6,097 – 8,362 | 63 |
| 6 | 8,362 – 12,948 | 63 |
| 7 | 12,948 – 21,993 | 62 |
| 8 | 21,993 – 74,231 | 61 |
| 9 | 74,231 – 655,180 | 64 |

**Sampling method:** `random.Random(300).sample(sorted(stratum_image_ids), 4)` — 4 images per decile, 10 deciles = **40 images total**. Seed 300, distinct from every prior seed used in this project (42: original pilot sampling; 100: Annotator B overlap; 200: EXP-PAP-005's own 24-image sample) — no collision, independently reproducible.

**Why this avoids sampling only the easiest or hardest images:** by construction, 4 images are drawn from *every* decile of the real, audited area distribution — including the smallest (550–2,188px², where EXP-PAP-005 saw its only zero-correction-despite-small-size pattern) and the largest (74,231–655,180px², comparable to EXP-PAP-005's heavily-corrected large images) in equal number, rather than letting a single random draw over the whole pool happen to cluster in the dense middle deciles (which, per the audit, hold most of the mass — deciles are area-based, not count-based, so a naive unstratified sample would skew toward common mid-sized crops and under-sample the extremes that are actually most relevant to the calibration question).

**Full sampled image_id list (40, drawn from real data — not invented):**

```
Decile 0: frame_000012_face09, frame_000170_face04, frame_000187_face05, frame_000249_face18
Decile 1: frame_000173_face06, frame_000190_face07, frame_000192_face05, frame_000215_face03
Decile 2: frame_000191_face03, frame_000198_face02, frame_000199_face02, frame_000248_face11
Decile 3: frame_000022_face04, frame_000060_face01, frame_000178_face01, frame_000192_face02
Decile 4: frame_000015_face05, frame_000038_face02, frame_000169_face02, frame_000188_face02
Decile 5: frame_000011_face07, frame_000019_face02, frame_000245_face10, frame_000246_face02
Decile 6: frame_000168_face01, frame_000175_face01, frame_000243_face01, frame_000244_face05
Decile 7: frame_000034_face02, frame_000134_face04, frame_000188_face01, frame_000227_face03
Decile 8: frame_000037_face01, frame_000047_face03, frame_000142_face03, frame_000185_face01
Decile 9: frame_000043_face05, frame_000102_face02, frame_000127_face02, frame_000133_face01
```

**Scope note, stated plainly per instruction:** this design calibrates the *review workflow and uncertainty-capture mechanism* — it is explicitly **not** claimed to be a statistically representative sample of the full 645-image population's quality distribution; 4 images per decile is sufficient to exercise the full range of crop sizes during calibration, not to estimate a population proportion with any stated confidence interval.

## 7. Reviewer Protocol

| Situation | Action |
|---|---|
| InsightFace proposal looks correctly placed | Leave unchanged (same as the EXP-PAP-005 protocol — no action needed, acceptance is the default, non-moving state) |
| Proposal is visibly off | Move the point to the correct anatomical location (unchanged from EXP-PAP-005) |
| Point's true location **cannot be confidently judged** (too small/blurry/occluded to tell) | **Do not guess a coordinate.** Mark the element `occluded: true` (Section 5) and leave its coordinate at the AI-proposed position (not moved, since moving it would itself be an unverified guess) — the `occluded` flag, not the coordinate, carries the "don't trust this one" signal |
| An entire image is too degraded to review any point confidently | Set the image-level `review_status` tag to `low_quality`, and still mark individual points `occluded` as applicable — do not skip the image or leave it with no record |
| A reason is identifiable (low resolution / blur / occlusion / ambiguous anatomical location / other) | Record it in the external review manifest (Section 5), keyed by `image_id` (image-level) or `(image_id, landmark_index)` (point-level) — **never invent a reason if none is clearly identifiable; "other" with no further detail is an acceptable, honest answer** |
| Landmark is anatomically invisible (e.g. extreme profile pose hides one eye) | Same as the "cannot confidently judge" case — `occluded: true`, no guessed coordinate, reason recorded as `occlusion` specifically (distinct from `ambiguous_location`, which is for cases where the feature is visible but its exact point is hard to pin down, e.g. a blurry jawline) |

**Explicit prohibition, carried over from the task's own instruction:** annotators must never invent a coordinate for a landmark they cannot locate. The `occluded` flag exists precisely so "I don't know" has a valid, honest, recorded answer distinct from "I checked and it's correct."

## 8. Acceptance Criteria (for deciding the workflow is ready to scale past this calibration batch)

| Criterion | What it checks |
|---|---|
| **Image coverage** | All 40 calibration images have a complete CVAT skeleton annotation (68 points) and an image-level `review_status` tag — no image silently skipped |
| **Landmark coverage** | 40 × 68 = 2,720 points present, correctly indexed (join by `label_id`, per the already-documented CVAT elements-array-ordering pitfall), no duplicates/missing indices |
| **Provenance completeness** | Every point traceable to its InsightFace-proposed origin and its final reviewed state, same `cvat_reviewed_landmarks.json`-style export schema as EXP-PAP-005, plus the new `review_status` tag and `occluded` flags actually populated (not just structurally present but empty) |
| **Uncertainty capture actually used** | At least some non-trivial fraction of the 40 images exercise the `occluded`/`review_status`/manifest-reason mechanism — if literally zero uncertainty is ever recorded across all 40, that itself is a finding worth investigating (either the mechanism is too cumbersome to use, or this batch genuinely had no ambiguous cases, which the stratified design across all deciles makes less likely) |
| **Export/re-import reproducibility** | The same export-and-compare procedure already validated for EXP-PAP-005 (Section 5/8 of `PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`) runs cleanly on this batch with zero errors — proves the pipeline, not just the pilot, is repeatable |
| **Reviewer usability** | A qualitative check: did the reviewer find the `occluded` checkbox + `review_status` tag + manifest workflow usable in practice, or cumbersome? (Not a number — a direct question to ask the reviewer after this batch, since no prior data exists to set a quantitative usability bar) |
| **QC validation** | Same structural checks as `PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md` Section 10, re-run on this batch: 40/40 images, 68/68 landmarks each, no duplicates, finite coordinates, in-bounds (or explicitly flagged out-of-bounds, as already precedented) |

**No arbitrary numeric quality threshold is imposed here**, per instruction — these are process/coverage/reproducibility criteria, not a pass/fail score on image quality itself. Whether the *rate* of uncertainty flags observed in this batch is "acceptable" is a judgment call for the user/supervisor to make after seeing real numbers, not a threshold set in advance.

## 9. Risks and Limitations

- 40 images is still small relative to 645 — this calibrates the *mechanism*, not a population-level quality estimate (restated from Section 6).
- The `occluded`-flag reuse is minimal but means "uncertain" and "literally occluded by something in the scene" share one field — if that distinction later matters, a dedicated attribute would be needed (a larger schema change than this plan proposes).
- An external review manifest introduces a second artifact that must stay synchronized with CVAT's own export — a documented risk, mitigated only by using the same stable `image_id`/`landmark_index` keys already proven reliable throughout this project, not eliminated entirely.
- This plan does not itself resolve the CVAT Task 1 job-state (`"in progress"`) question — unrelated to this calibration batch, carried over as still open.

## 10. Implementation Sequence (not executed — sequencing only)

1. Generate InsightFace proposals for the 40 sampled images (same method as EXP-PAP-005, not yet run).
2. Create a **new** CVAT task (not Task 1) with: the same `face68` skeleton label (reused, not redefined) plus one new `review_status` tag label (Section 5).
3. Import the 40 images + proposals as initial annotations (same mechanism as EXP-PAP-005).
4. Reviewer completes the protocol (Section 7), using `occluded` + the tag + the external manifest.
5. Export, compare against proposals, QC (same procedure as `PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`).
6. Evaluate against Section 8's acceptance criteria.
7. Only then: decide on scaling to the remaining ~605 images, informed by real uncertainty-rate data this batch will have produced.

## 11. Exact Files Inspected

`docs/reports/PAPUAN_V2_DATASET_QUALITY_AUDIT.md`, `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`, `experiments/EXP-PAP-005/metadata.json`, `experiments/EXP-PAP-005/insightface_68pt_pilot_predictions.json`, `data/papuan_v2/faces/*` (645 files, dimension read only), CVAT API (`GET /api/labels?task_id=1`, read-only), CVAT source (`cvat/apps/engine/models.py` AttributeType enum, `cvat-ui` LabelType.TAG reference) in the local clone used earlier for CVAT deployment.

## 12. Files Created or Modified

- `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md` (this report, new).
- Appended updates to `docs/reports/PAPUAN_V2_CURRENT_STATE.md` and `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`.

## 13. Changes NOT Made

No image file modified. No dataset manifest modified. No CVAT Task 1 change (label schema, annotations, or otherwise) — all CVAT capability checks were read-only GETs against the existing schema. No new CVAT task actually created. No InsightFace predictions generated for the 40-image sample (listed/designed only). No additional images annotated. No model trained. No Label Studio change. No quality threshold invented — Section 8 explicitly declines to set one. No sample IDs invented — all 40 image_ids above are real, drawn from the actual 645-image manifest/directory listing by the documented deterministic procedure.

## 14. Date/Time

2026-10-19.

## 15. Git Status

Branch: `main`. New: `docs/reports/PAPUAN_V2_ANNOTATION_CALIBRATION_PLAN.md`. Modified (appended): `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`. All uncommitted, per the standing no-auto-commit rule. No other files touched.

---

*Design/planning report only. No annotation, CVAT task creation, prediction generation, or dataset change was performed.*

---

## 16. [Update 2026-10-19] Implementation Results — Calibration Task Created, Ready for Review

### Selected 40 image IDs (actually used, verbatim from Section 6 above — no deviation)

Reused the exact list from Section 6 of this report. Verified before use: 40/40 unique, 0 overlap with EXP-PAP-005's 24 images, 40/40 have both Original and CLAHE files present on disk.

### Prediction generation

Reused the same validated InsightFace `landmark_3d_68` extraction method as EXP-PAP-005 (synthetic full-crop bounding box, skipping SCRFD re-detection, which fails on tight crops — the same fix already proven necessary and applied there). **40/40 succeeded, 0 failures.**

Artifact (new, raw predictions, preserved unchanged after generation): `experiments/EXP-PAP-005/calibration_batch_40_predictions.json`.

Validated before import: 40 images, 2,720 total points (40×68), 0 errors, all coordinates finite. **PASS.**

### New CVAT task

- **Task ID: 2** (actual ID returned by CVAT, not assumed in advance).
- **URL:** `http://localhost:8070/tasks/2` (job id 2, stage `annotation`, state `new`).
- **Name:** "EXP-PAP-005 Calibration — 40 Images".
- **Labels:** `face68` (skeleton, 68 sublabels, names/order/SVG copied verbatim from Task 1's live label config — not redefined by hand, avoiding any drift) + **one new** `review_status` tag label with a `select` attribute `status` (values: `ok`, `needs_review`, `low_quality`, default `needs_review`).

### Uncertainty mechanism actually implemented

Exactly as planned in Section 5 — no more, no less:
- **Point-level:** the skeleton's native `occluded`/`outside` boolean fields (already present on every point by virtue of being a CVAT `points`-type skeleton element — no schema addition needed, confirmed structurally identical to Task 1's points).
- **Image-level:** the new `review_status` tag (`ok`/`needs_review`/`low_quality`), confirmed live via `GET /api/labels?task_id=2`.
- **Reasons:** left to an external manifest, to be filled in only as needed during review — not pre-created with placeholder rows, since no uncertainty has been recorded yet (review hasn't started).
- **Not added:** no per-sublabel attributes on any of the 68 points — the simpler mechanisms (reused `occluded` + the one tag) were sufficient, per the "do not add attributes to all 68 skeleton labels unless simpler mechanisms prove insufficient" instruction.

### Import and validation results (all verified via CVAT API after import, not assumed)

| Check | Result |
|---|---|
| Task contains exactly 40 images | PASS (`data/meta` size=40) |
| Image order matches the prediction manifest | PASS (frame stems == `sorted(image_ids)`, verified before building the import payload) |
| All 40 images have 68 landmark proposals | PASS |
| All 2,720 points present and correctly indexed | PASS (joined strictly by `label_id`, per the documented CVAT elements-array-ordering pitfall) |
| Imported coordinates match the raw prediction artifact | PASS — **0 mismatches across all 2,720 points** |
| `review_status` tag available | PASS, confirmed live with all 3 expected values |
| Task 1 unchanged | PASS — still 24 shapes, job 1 still `stage: annotation, state: in progress`, unmodified |

### Known limitations

Same as Section 9 (restated, unchanged by implementation): 40 images calibrates the *mechanism*, not a population-level quality estimate; `occluded` conflates "uncertain" with "literally occluded"; the external manifest must be kept in sync manually using the same stable keys already used throughout the project.

### How the user should begin the review

1. Open `http://localhost:8070/tasks/2`.
2. Log in (same credentials as Task 1).
3. For each of the 40 images: review the pre-filled 68-point skeleton (leave correct points unchanged, move incorrect ones, mark `occluded: true` on any point that can't be confidently judged rather than guessing).
4. Before moving to the next image, set the `review_status` tag attribute (`ok` / `needs_review` / `low_quality`) based on overall confidence in that image.
5. If a clear reason for uncertainty is identifiable, note it (image_id and/or landmark index + short reason) in a simple external manifest — can be a plain text/CSV note for now; no CVAT action required for this step.
6. Save periodically in CVAT.

### What remains to be done after review

Once the user finishes: export this task's annotations (same method as EXP-PAP-005's export — `GET /api/tasks/2/annotations`, join by `label_id`), compare against `calibration_batch_40_predictions.json` the same way as EXP-PAP-005's proposal-vs-reviewed comparison, run the same QC checks, and evaluate against this report's Section 8 acceptance criteria. **None of this has been done yet** — this update stops at "ready for review."

---

## 17. [Update 2026-10-19, same day] Bug Found and Fixed — Task Recreated as Task ID 3

### Problem

Task ID 2 (Section 16) failed to open in the CVAT UI with a frontend crash: `TypeError: Cannot read properties of undefined (reading 'addClass')` in `activateShape`, reported by the user when opening `http://localhost:8070/tasks/2/jobs/2`.

### Root cause (confirmed, not guessed)

Task 2's skeleton label was created by reusing **Task 1's `svg` field verbatim**. Inspecting that SVG showed each point element carries a `data-label-id` attribute (e.g. `data-label-id="2"`) that CVAT had auto-injected to reference **Task 1's own specific sublabel database row IDs**. When the same SVG text was reused to create Task 2, Task 2's sublabels were assigned entirely new, different database IDs (CVAT IDs are global, not per-task) — so the copied SVG's `data-label-id` values pointed to sublabels that don't exist in Task 2 at all. The frontend's shape-activation code expects a valid SVG node for every annotated element; failing to find one throws exactly this crash.

### Fix

Task 2 was deleted (confirmed beforehand: 0 tags, 0 manual edits beyond the 40 imported machine proposals — nothing of review value existed yet) and **recreated as Task ID 3**, this time generating the skeleton's SVG fresh (same method originally used to create Task 1 — `data-label-name` only, no hardcoded IDs) rather than reusing another task's saved SVG. Verified the newly-saved SVG's auto-injected `data-label-id` values (141–208) fall exactly within Task 3's own sublabel ID range — self-consistent, unlike the copied version.

**Lesson for any future task creation that reuses an existing skeleton config:** reuse the **label structure** (names, order, point count) by reading it from an existing task, but always let CVAT **generate a fresh SVG** for the new task rather than copying the `svg` string verbatim — the SVG is not actually a portable, task-independent artifact despite looking like static markup; it's tied to the specific sublabel IDs assigned when it was saved.

### Re-verification after the fix

Images re-uploaded (40/40), predictions re-imported (2,720/2,720 points, 0 mismatches against the raw prediction artifact — identical result to Section 16's original import, confirming no data was lost or altered by the recreation), page confirmed reachable (`http://localhost:8070/tasks/3/jobs/3` → HTTP 200). Task 1 re-confirmed unaffected throughout (still 24 shapes, job still `stage: annotation, state: in progress`).

**Corrected task reference for the remainder of this plan: use Task ID 3, not Task ID 2.** `http://localhost:8070/tasks/3` is the task to review. Task 2 no longer exists (deleted).

**Not independently confirmed:** this response verifies the server-side data is now self-consistent and the page returns HTTP 200, but actual rendering inside a browser was not visually observed by this process — the user should confirm the skeleton actually displays and is clickable before relying on this fix being complete.

---

## 18. [Update 2026-10-19] Human Review Complete — Export, QC, and Comparison Results

**Task reference note:** the user's request referred to "CVAT Task 2" — the live task is actually **Task ID 3** (Task 2 was deleted and recreated as Task 3 due to the SVG bug documented in §17). All verification below was run against Task 3, confirmed via its `updated_date` advancing from creation time (2026-10-18T18:07Z) to 2026-10-19T01:15Z — real review activity, not an empty/untouched task.

### CVAT state verification (before export, not assumed)

- Task 3: 40/40 images present.
- 40 skeleton shapes, 40 `review_status` tags — **one tag per frame, no gaps** (verified `sorted(frames) == range(40)`).
- `review_status` distribution: **30 `ok`, 10 `low_quality`, 0 `needs_review`**.
- Point-level `occluded` flags: **0 points flagged occluded** across all 2,720 — the reviewer did not use this mechanism on this batch (noted as a finding, not an error; see Limitations below).

### Export

New artifacts (originals preserved unchanged):
- `experiments/EXP-PAP-005/calibration_batch_40_reviewed.json` — 2,720 records, same schema as the 24-image pilot's reviewed export, plus `review_status_image` and `batch` fields.
- `experiments/EXP-PAP-005/calibration_batch_40_review_status.json` — per-image `review_status`, keyed by `image_id`.
- `experiments/EXP-PAP-005/calibration_batch_40_comparison.json` — full comparison statistics (below).

`calibration_batch_40_predictions.json` (raw proposals) and all Task 1 / 24-image pilot artifacts are unchanged — confirmed by not touching those files in this task.

### QC results

| Check | Result |
|---|---|
| 40 images, 68 landmarks each | PASS |
| 2,720 total landmarks | PASS |
| No duplicate/missing indices | PASS |
| Finite coordinates | PASS |
| Within image bounds | 5 points (of 2,720) out-of-bounds — informational, consistent with the same class of edge-case already documented for the 24-image pilot, not a new issue |
| Correct image-to-annotation mapping | PASS — frame order re-verified against `sorted(image_ids)` before export |
| `review_status` preserved | PASS — all 40 images carry a value, no missing tags |
| Uncertainty flags preserved | PASS structurally (field present and exported correctly) — **0 points actually flagged**, see Limitations |

**Overall QC: PASS, 0 errors.**

### Correction statistics (human correction relative to AI proposal — explicitly not accuracy)

- **714 / 2,720 points changed** beyond the 0.5px tolerance (**26.2%**) — higher than the 24-image pilot's 13.5%, driven by a different pattern (below).
- **11 of 40 images have at least one correction**; the other 29 are coordinate-identical to the proposal.
- Displacement (corrected points): mean 5.66px, median 5.11px, p90 7.85px, max 38.12px — **notably tighter/smaller typical displacements than the 24-image pilot** (whose median was 8.27px), though the max is comparable.

**Key pattern, verified not an artifact:** unlike the 24-image pilot (where corrected images had *partial* per-point corrections), this batch shows a near-bimodal pattern — most of the 11 corrected images have **all or nearly all 68 points changed** (e.g. `frame_000170_face04`: 68/68, `frame_000198_face02`: 68/68, `frame_000243_face01`: 68/68), rather than a handful of individual points. **Spot-checked to confirm this is genuine per-point correction, not a uniform shift/bug:** sampled one fully-corrected image's displacement vectors — they vary meaningfully point-to-point (dx range −6.0 to +2.3px, dy range −0.7 to +3.1px for the sample checked), ruling out a rigid-transform artifact. This is consistent with the reviewer substantially re-placing the entire skeleton on certain images rather than nudging individual points — a legitimate review outcome, reported as observed, not interpreted further here.

**Per-region correction rates** (across all 2,720 points): fairly uniform, 25.0–27.5% across all 9 regions (jaw 26.9%, eyebrows/eyes 25.4–27.5%, nose/mouth 25.0–27.0%) — no region stands out, consistent with whole-image corrections rather than a region-specific proposal weakness.

**Cross-reference with `review_status`:** worth noting for the next analysis step (not computed here, flagged as a natural follow-up): whether the 11 corrected images overlap with the 10 `low_quality`-tagged images is not yet checked in this report — see Next Actions.

### Review-status distribution

**30 `ok`, 10 `low_quality`, 0 `needs_review`** (of 40 images).

### Uncertainty/occlusion counts

**0 points flagged `occluded`** across all 2,720. **Limitation, stated plainly:** this means the point-level "can't confidently judge" mechanism (Section 5's design) was not exercised in this batch — either because the reviewer found every individual point judgeable even on `low_quality`-tagged images (addressing uncertainty at the image level via the tag instead), or because the mechanism wasn't used in practice for another reason not captured by this data. This report does not assume which; it is a verified fact (zero flags) with an open interpretation, same epistemic stance as the 24-image pilot's earlier ambiguity findings.

### Original-to-CLAHE lineage

Verified directly for all 40 reviewed images: all have both `data/papuan_v2/faces/<id>.jpg` and `data/papuan_v2/clahe/<id>.jpg` present, **0 missing, 0 dimension mismatches** — consistent with the dataset-wide audit and the 24-image pilot. **No duplicate CLAHE annotation file created** — per existing project convention, the reviewed Original coordinates in `calibration_batch_40_reviewed.json` are the single canonical source; a CLAHE-branch training run substitutes `image_path` and reuses the same `(x, y)` values unchanged.

### Export/QC failures

None. No blocker encountered.

### Ready for a scale-up decision?

**Partially — more informative than the 24-image pilot, but with a new open question of its own.** This batch resolves the prior pilot's central ambiguity (no job-state doubt here — `updated_date` and non-trivial `review_status`/correction data confirm real review occurred across the full 40). It also newly surfaces: (a) the all-or-nothing correction pattern on 11 images, worth understanding before scaling, and (b) zero use of the `occluded` mechanism, meaning this calibration batch did not actually produce data to validate whether that specific design choice works in practice. **Recommendation: review these two findings with the user/supervisor before finalizing the scale-up decision — not a blocker, but material to how the mechanism should be refined (or not) before applying it at full scale.**

### Files Created in This Update

- `experiments/EXP-PAP-005/calibration_batch_40_reviewed.json`
- `experiments/EXP-PAP-005/calibration_batch_40_review_status.json`
- `experiments/EXP-PAP-005/calibration_batch_40_comparison.json`

---

## 19. [Update 2026-10-19] Audit of the 11 Heavily-Corrected Images

### Objective

Determine whether the 11 images with near-complete (46–68 of 68) point corrections reflect genuinely inaccurate AI proposals, low image quality, individual careful review, or a possible annotation/export artifact — without changing any annotation, coordinate, or CVAT state.

### The 11 images (confirmed, with correction count and review_status)

| image_id | points changed | review_status |
|---|---|---|
| frame_000170_face04 | 68/68 | ok |
| frame_000173_face06 | 68/68 | ok |
| frame_000192_face02 | 68/68 | ok |
| frame_000198_face02 | 68/68 | ok |
| frame_000199_face02 | 68/68 | low_quality |
| frame_000243_face01 | 68/68 | ok |
| frame_000244_face05 | 68/68 | ok |
| frame_000246_face02 | 68/68 | ok |
| frame_000190_face07 | 67/68 | ok |
| frame_000011_face07 | 57/68 | ok |
| frame_000227_face03 | 46/68 | ok |

**10 of 11 are tagged `ok`, only 1 `low_quality`** — consistent with `review_status` reflecting the reviewer's confidence *after* correction, not the AI proposal's initial quality (a plausible, non-contradictory reading, not asserted as the only possible one).

### Landmark index/name integrity (verified)

All 68 indices present with no gaps/duplicates, and every `landmark_name` matches the verified index mapping exactly, for all 11 images — re-checked explicitly in this audit, not merely inherited from the batch-wide QC. **No ordering or identity corruption found.**

### Key finding: two distinct correction patterns, not one

Computing the per-point displacement vector `(dx, dy)` for each of the 11 images (not just the aggregate distance already reported) reveals **two clearly distinct groups**:

**Group 1 — exact uniform rigid translation (6 images):** `frame_000192_face02`, `frame_000198_face02`, `frame_000199_face02`, `frame_000243_face01`, `frame_000244_face05`, `frame_000246_face02`. For every one of these, **all 68 points moved by the bit-identical `(dx, dy)` vector** (spot-checked to 6 decimal places on `frame_000198_face02`: every sampled point shows delta `(5.253249, 5.828802)`, exactly). Displacement standard deviation across all 68 points is **0.00 px** for both x and y in every image in this group.

**Group 2 — genuine independent per-point correction (5 images):** `frame_000170_face04`, `frame_000173_face06`, `frame_000190_face07`, `frame_000011_face07`, `frame_000227_face03`. These show real point-to-point variance in displacement (standard deviation 0.60–11.43px across the group, non-zero in every case), consistent with the reviewer judging and moving each point individually — the same pattern already established for the 24-image pilot.

### Interpretation (evidence-grounded, not asserted beyond what the data shows)

A mathematically exact, bit-identical displacement across all 68 points of a single image is the signature of **a whole-skeleton drag/translate** — a standard CVAT interaction where the reviewer repositions the entire skeleton object as one rigid group rather than touching each point individually. This is consistent with: the AI proposal placing a correctly-shaped skeleton in approximately the right location but offset from the actual face (e.g. by a few pixels in both axes), which the reviewer then corrected in a single drag rather than 68 separate point moves.

**This is not evidence of a reviewer error, nor of InsightFace detection failure, nor of an export/import bug** — the displacement magnitudes (1.6–7.9px on a diagonal of 85–153px for this group) are modest, plausible corrections, and the landmark identity/ordering is confirmed intact (previous section). **It does mean** that, for these 6 images, "68/68 points changed" measures one whole-skeleton repositioning decision, not 68 independent per-point judgments — a materially different signal than the same statistic on the 5 Group 2 images or on the 24-image pilot's corrected images. The aggregate "26.2% of points changed" / "714 points changed" statistics reported earlier remain numerically accurate, but their *granularity* is now known to be uneven across images: some of that count reflects fine-grained review, some reflects coarse-grained whole-skeleton repositioning.

### Whether this is consistent with inaccurate proposals, low quality, or an issue

- **Inaccurate proposals:** consistent with Group 1 (the proposal's overall position, not its internal shape, was off) and with Group 2 (individual points were off).
- **Low image quality:** only 1 of the 11 (`frame_000199_face02`) is tagged `low_quality` by the reviewer — the evidence does not support attributing most of these 11 corrections to image quality specifically; they appear to be ordinary proposal-placement corrections on images the reviewer considered reviewable (`ok`).
- **Annotation/export issue:** **no evidence found.** Landmark identity/ordering is intact (verified above), and the uniform-translation pattern has a known, benign, expected explanation (whole-object drag) rather than indicating corrupted data. **This report does not conclude an issue exists.**

### Explicitly inconclusive points, stated rather than guessed

- Whether the Group 1 images' *original* AI-proposal shape (before the whole-skeleton shift) was otherwise accurate, or whether individual points within those 6 images also needed adjustment that the reviewer chose not to make after the group-move, **cannot be determined from coordinate data alone** — this would require the reviewer's direct account or a visual re-inspection, neither performed here (no overlay/visualization tool exists in this repository, and per instruction, none was built for this audit).
- Why the reviewer chose a whole-skeleton drag for 6 images and individual point correction for 5 others is not recorded anywhere and is not inferred here.

### Files inspected for this audit

`experiments/EXP-PAP-005/calibration_batch_40_comparison.json`, `experiments/EXP-PAP-005/calibration_batch_40_reviewed.json`, `experiments/EXP-PAP-005/calibration_batch_40_predictions.json`, `experiments/EXP-PAP-005/calibration_batch_40_review_status.json`. No new files created; no annotation, coordinate, prediction, label, or CVAT task was modified.

---

## 20. [Update 2026-10-19] Task 4 Created — Original (Unreviewed) Proposal Counterpart to Task 3

### Why

To let the user visually compare human-reviewed annotations against the original, untouched InsightFace proposals side-by-side in CVAT, without needing to interpret raw coordinate data — a second task holding only the original proposals, using the identical visual schema as Task 3.

### Task IDs and URLs (verified via API, not assumed)

- **Task 3** ("EXP-PAP-005 Calibration — 40 Images", human-reviewed): `http://localhost:8070/tasks/3`
- **Task 4** ("EXP-PAP-005 Calibration — 40 Images (Original Proposals)", unreviewed): `http://localhost:8070/tasks/4`

### Image manifest equivalence (verified)

Both tasks hold the identical 40 images in identical order — confirmed by comparing `GET /api/tasks/{id}/data/meta` frame-name lists directly: **40/40 filenames match, same order, for both tasks.**

### Prediction source

Task 4's annotations were imported directly from `experiments/EXP-PAP-005/calibration_batch_40_predictions.json` — the original, unmodified InsightFace proposal artifact. **Task 3's reviewed/corrected coordinates were never read for this task's import** — the import script sourced only the raw predictions file.

### Coordinate-preservation validation

- 40/40 images, 2,720/2,720 landmark points present, correctly indexed (joined by `label_id`, not array order).
- **0 coordinate mismatches** against `calibration_batch_40_predictions.json` — every imported point matches the raw proposal exactly.
- Landmark names/index mapping confirmed identical between Task 3 and Task 4 (same 68 sublabel names, same schema).
- `review_status` tag label is present and available on Task 4 (kept for schema consistency, per instruction) but **holds 0 tags** — no original review status was invented; the tag simply exists as an available, empty mechanism, same as it started on Task 3 before review.

### Confirmation that Task 3 was not modified

Snapshotted Task 3's full annotation state (`GET /api/tasks/3/annotations`) immediately before creating Task 4, and re-fetched it immediately after Task 4's import completed: **the two snapshots are byte-for-byte identical** (40 shapes, 40 tags, unchanged) — confirmed via direct dict equality, not just a count comparison.

### Known limitation from Task 4's creation (lesson applied from Task 3's earlier bug)

Task 4's skeleton SVG was **freshly generated** for this task (same method used to fix Task 3 previously), not copied verbatim from Task 3's saved SVG — reusing another task's SVG string carries task-specific `data-label-id` references that don't transfer, which caused the earlier Task 2 crash. Verified before use this time: Task 4's saved SVG's `data-label-id` values are a subset of Task 4's own actual sublabel IDs.

### How the user can open each task

- **Task 3 (reviewed):** `http://localhost:8070/tasks/3`
- **Task 4 (original proposals, for comparison):** `http://localhost:8070/tasks/4`

Both use the identical 68-point skeleton with identical landmark names, so switching between them shows the same visual layout — only the point positions (and, for Task 3 only, the `review_status` tags) differ.

---

## 21. [Update 2026-10-19] Finalized Task 3 vs Task 4 Comparison

### Exports

- **Task 3 (reviewed):** `experiments/EXP-PAP-005/calibration_batch_40_reviewed.json` — reused unchanged, since Task 3's `updated_date` was confirmed identical to when this file was originally exported (no new activity since §18/§19).
- **Task 4 (original proposals):** `experiments/EXP-PAP-005/calibration_batch_40_task4_export.json` (new) — Task 4's current saved state exported fresh via the CVAT API; confirmed 0/2,720 points differ from `calibration_batch_40_predictions.json`, i.e. Task 4 remains exactly the original proposal baseline, as intended (per this task's framing — Task 4 is deliberately not reviewed).
- Comparison statistics: `experiments/EXP-PAP-005/task3_vs_task4_comparison.json` (new).
- `calibration_batch_40_predictions.json` (original prediction artifact) unchanged.

### QC results

Both exports: **PASS** — 40/40 images, 2,720/2,720 landmarks each, 0 missing/duplicate indices, 0 non-finite coordinates.

### Image/identity equivalence

Verified directly: identical 40-image sets between Task 3 and Task 4, identical `(image_id, landmark_index)` key sets, **0 `landmark_name` mismatches** across all 2,720 corresponding pairs — both tasks' schemas and identity mapping are fully consistent.

### Comparison: Task 4 (original proposals) vs. Task 3 (human-reviewed reference)

| Metric | Value |
|---|---|
| Points compared | 2,720 |
| Points changed (>0.5px) | 714 (26.2%) |
| Mean displacement | 1.487 px |
| Median displacement | 0.000 px |
| Mean displacement, normalized by image diagonal | 0.01502 |
| Median displacement, normalized | 0.00000 |

The median is 0 because the majority of points (73.8%) are unchanged between the two tasks — the mean is pulled up by the 11 images with substantial corrections (consistent with and numerically identical to the correction pattern already documented in §18–19, since Task 3's reviewed coordinates and Task 4's unreviewed baseline are the same two datasets compared from the opposite direction).

**Per-image summary:** 29 of 40 images show 0px mean/median/max displacement (fully unchanged); 11 images show corrections, matching exactly the set and magnitudes already identified and audited in §19 (`frame_000011_face07`, `frame_000170_face04`, `frame_000173_face06`, `frame_000190_face07`, `frame_000192_face02`, `frame_000198_face02`, `frame_000199_face02`, `frame_000227_face03`, `frame_000243_face01`, `frame_000244_face05`, `frame_000246_face02`).

**As established in §3/§18:** these displacement statistics measure the magnitude of human correction relative to the initial AI proposal — they are not an independent accuracy measurement, and are not treated as one here.

### Blockers

None. No export or QC failure encountered.

---

## 22. [Baseline Training Update, 2026-10-19] First Landmark Training Baseline — Mean-Shape, Train/Val/Test

### Objective

Prepare the first held-out train/val/test split across all currently-reviewed landmark data and train the smallest defensible baseline, to establish a floor for future image-conditioned models — not to produce a final production landmark predictor.

### Data pooled

All currently-reviewed, human-corrected landmark annotations: the 24-image pilot (`experiments/EXP-PAP-005/cvat_reviewed_landmarks.json`) and the 40-image calibration batch (`experiments/EXP-PAP-005/calibration_batch_40_reviewed.json`, Task 3's reviewed export — **not** Task 4's unreviewed proposals, which were explicitly excluded from training per instruction). **Verified 0 image overlap between the two sets** (disjoint `image_id`s, direct set intersection check) — **64 distinct images, 4,352 landmark points total** pooled.

### Subject-ID leakage check — real limitation found and disclosed, not assumed away

**No subject/person-identity column exists anywhere in the project's manifests** (`pilot_manifest.csv` has only `image_id, face_filename, source_face_path, source_clahe_path, pilot_image_path, sample_seed, sampled_at` — confirmed by direct inspection, consistent with this exact gap already documented in the thesis methodology chapter's leakage section). A true subject-level split is **not possible** with current project data.

**Mitigation used instead of an unguarded image-level split:** frame-number-adjacency grouping, reusing this project's own existing precedent (`tools/train_arcface_classifier.py`'s `StratifiedGroupKFold` temporal-block grouping) rather than inventing a new heuristic. Images whose source frame numbers are within 3 of each other were grouped into one block (18 blocks from 64 images, ranging 1–10 images per block — several blocks are multiple faces from the exact same frame, which are certainly the same capture moment). **Entire blocks, never individual images, were assigned to train/val/test**, preventing near-duplicate/same-moment frames from leaking across the split boundary. This is a disclosed, cautious proxy for subject-level grouping, not a true identity-based split — explicitly weaker than a real subject ID would provide, and stated as such.

### Split

Deterministic, seed=400 (distinct from every prior seed used in this project: 42, 100, 200, 300), block-shuffled, target ratios ~70/15/15 by image count:

| Split | Images | Points |
|---|---|---|
| Train | 45 | 3,060 |
| Validation | 11 | 748 |
| Test | 8 | 544 |

**Verified zero frame-block spans a split boundary** (checked programmatically — no warning raised).

### Model: smallest practical baseline supported by the repository

**No deep-learning or landmark-regression training code exists anywhere in this repository** (re-confirmed: zero `torch`/`tensorflow`/`nn.Module`/`keras` references in `src/` or `tools/`). Given this and the dataset size (45 training images), the smallest practical, non-overengineered baseline is a **mean-shape predictor**: for each of the 68 landmarks, compute the mean position in width/height-normalized space (`x/image_width, y/image_height`) across the 45 training images; at evaluation time, scale this fixed mean shape to each target image's actual pixel dimensions. **This model does not look at image pixel content at all** — it is a closed-form statistical floor, not a learned image-conditioned model, and is reported as exactly that, not inflated into something it isn't. No new model architecture, framework, or dependency was introduced.

### Evaluation results

| Split | Images | Points | Pixel error (mean / median / p90 / max) | Normalized error, by diagonal (mean / median) |
|---|---|---|---|---|
| Validation | 11 | 748 | 9.16 / 6.45 / 20.68 / 40.66 px | 0.0898 / 0.0843 |
| Test | 8 | 544 | 40.11 / 23.52 / 94.69 / 174.97 px | 0.1008 / 0.0887 |

**Normalized error is far more stable across splits (0.090 vs. 0.101) than raw pixel error (9.2px vs. 40.1px)** — the test split happens to contain several of the largest crops in this pool (e.g. `frame_000102_face02`, `frame_000120_face01`), so raw pixel error inflates accordingly while the diagonal-normalized figure stays comparable. This is expected behavior for a mean-shape baseline and confirms the normalization is doing its job, not a sign of val/test being drawn from different underlying distributions.

Full per-image mean/median/max pixel error for all 19 held-out images is recorded in `experiments/EXP-PAP-005/landmark_baseline_meanshape_results.json`.

### Original vs. CLAHE comparison

**Verified identical by construction for this baseline, not merely assumed:** re-confirmed for all 64 images in this specific pool that Original and CLAHE crops have identical pixel dimensions (0 mismatches), and — per the already-established, repeatedly-verified geometric-identity property of this project's CLAHE transform — the reviewed landmark coordinates are identical between the two conditions. **Because the mean-shape baseline uses no image pixel content whatsoever, its predictions and resulting error are mathematically identical for Original and CLAHE** — there is nothing to compare, by design, not by omission. **A meaningful Original-vs-CLAHE landmark-model comparison requires an image-conditioned model** (one that actually reads pixel values), which this dataset's size (45 training images) does not currently support training reliably — this is the honest boundary of what this baseline can answer, stated explicitly rather than glossed over.

### Artifacts produced

- `experiments/EXP-PAP-005/landmark_baseline_meanshape_results.json` (new) — split definition, mean shape, full val/test metrics and per-image results.

No CVAT annotation, original prediction artifact, or dataset image was modified. No new CVAT task created. No manual annotation performed.

### Limitations (explicit)

1. Subject-level leakage control is a frame-adjacency proxy, not true identity-based grouping — stated above, not resolved.
2. 45 training / 11 validation / 8 test images is a very small sample for any evaluation claim beyond "this specific baseline's floor on this specific split" — no generalization claim is made.
3. This baseline is intentionally content-blind; it establishes a floor for comparison, not a usable landmark predictor, and cannot answer the Original-vs-CLAHE question by design (see above).
4. Only 64 of 645 total dataset images have reviewed landmarks — this training run uses under 10% of the full dataset.

### Not a blocker — stopped intentionally at the baseline this data actually supports

Per instruction #7, this task did not attempt to train an image-conditioned model (e.g. a CNN regressor) on 45 images, which would almost certainly overfit and produce a misleading result. The mean-shape baseline was chosen specifically because it is the smallest model class honestly supportable by this data size, not as a placeholder for something larger that was simply skipped.

---

## 23. [Model Training Update, 2026-10-19] First Image-Based Landmark Model — Ridge Regression on Pixel Features

### Objective

Train the first genuinely image-conditioned landmark model (distinct from the content-blind mean-shape baseline in §22) on the 64 human-reviewed Original images, per supervisor direction. Minimal, no new framework.

### Dependency check — real blocker found, smallest fix used instead of a workaround

`import torch` succeeds but resolves to an **empty namespace stub** (`torch.__file__` is `None`, `torch.nn` does not exist) — PyTorch is not actually usable in this environment. Rather than installing a new heavy dependency (explicitly discouraged — "reuse existing dependencies"), **`scikit-learn` (already a project dependency, already used in `tools/train_arcface_classifier.py`) was used instead** — a classical, genuinely image-conditioned regression approach, not a deep-learning model.

### Model and features

- **Model:** `sklearn.linear_model.Ridge(alpha=5000.0)`, jointly predicting all 68 landmarks (136-dim output: `x/width, y/height` per landmark, same normalization convention as the §22 mean-shape baseline) from a single feature vector per image.
- **Features:** grayscale, resized to 32×32, flattened, `/255`-normalized (1,024-dim). Deliberately small — 45 training images cannot support a larger feature space without even worse overfitting risk.
- **Why this `alpha`:** with 1,024 features and 45 training samples, heavy L2 regularization is necessary to avoid the model degenerating into pure memorization; `alpha=5000` was chosen as a reasonable, not-tuned-against-val-performance starting point (tuning it against the 11-image validation set would itself risk a form of overfitting at this sample size, so no hyperparameter search was performed).

### Data and split (reused, not rebuilt)

Same 64 images (24-pilot + 40-calibration, 0 overlap) and same train/val/test split as §22 (**seed=400**, 45/11/8, frame-number-adjacency grouped — **subject IDs are unavailable; this is a disclosed proxy for subject-level leakage control, not a guarantee**, identical limitation already stated in §22).

### Results

| Split | Condition | Pixel error (mean/median) | Normalized error (mean/median) |
|---|---|---|---|
| Train (45) | Original | 11.27 / 8.34 px | 0.0811 / 0.0770 |
| **Val (11)** | **Original** | **9.08 / 6.46 px** | **0.0893 / 0.0845** |
| **Test (8)** | **Original** | **39.99 / 23.64 px** | **0.1009 / 0.0888** |
| Val (11) | CLAHE (same model) | 9.12 / 6.50 px | 0.0897 / 0.0847 |
| Test (8) | CLAHE (same model) | 39.91 / 23.43 px | 0.1010 / 0.0885 |

### The central, honest finding

**Held-out performance is statistically indistinguishable from the §22 mean-shape baseline** (val: 9.08px here vs. 9.16px mean-shape; test: 39.99px here vs. 40.11px mean-shape — differences of ~0.1-0.2px, far smaller than any plausible noise floor). **This model has not yet demonstrated that pixel content provides measurable predictive value beyond the trivial mean-shape baseline at this dataset size.** This is reported as the actual result, not softened — it is itself informative: 45 training images, even reduced to a 1,024-dim feature space, is not enough signal for this classical approach to clearly beat a constant predictor under the regularization needed to avoid overfitting. Train error (11.27px) is actually *higher* than validation error — consistent with heavy regularization preventing memorization (not a bug), but also consistent with the model not fitting a meaningfully different function from the mean shape in the first place.

**Original vs. CLAHE, same trained model:** nearly identical (differences of ~0.01-0.04px mean) — consistent with the model not using image content strongly enough to be differentially sensitive to the preprocessing change. **This measures apparent robustness to preprocessing for this specific, currently-mean-shape-equivalent model — it does not establish that a model which actually learns from pixel content would show the same invariance**, and should not be read as a general robustness claim.

### Artifacts

- `experiments/EXP-PAP-005/landmark_ridge_baseline_model.joblib` — the trained model (checkpoint).
- `experiments/EXP-PAP-005/landmark_ridge_baseline_results.json` — full train/val/test, Original/CLAHE results and per-image detail.

### Limitations (explicit)

1. **Model does not yet outperform the content-blind mean-shape baseline** — the single most important limitation, stated plainly above, not buried.
2. Same frame-adjacency-proxy leakage control as §22 — no true subject ID exists.
3. 45 training images is far below what this feature space (1,024-dim) could meaningfully use even with regularization — more reviewed images are the most direct lever to improve this, not further hyperparameter tuning on the current tiny val set.
4. No fairness or generalization claim is made or supported by this result — 64 images, one source video, one annotator.
5. Original-vs-CLAHE "robustness" here reflects this specific, near-mean-shape-equivalent model, not a property of image-based landmark models in general.

### Not claimed

This is not presented as a working landmark predictor, not as evidence CLAHE is safe for landmark models in general, and not as superior to the mean-shape baseline — it is the first genuinely image-conditioned attempt, honestly reported as not yet distinguishable from the simpler baseline.

---

## 24. [Figures Update, 2026-10-19] Thesis-Ready Figures for Supervisor Discussion

### Objective

Produce a small set of honest, clearly-labeled figures from already-existing artifacts (§16–§23) to support a supervisor discussion on whether to proceed with more manual landmark annotation. No new training, no hyperparameter search, no new annotation.

### Figure index

All saved under `experiments/EXP-PAP-005/figures/`:

| File | Shows |
|---|---|
| `fig1_reviewed_landmarks_example.png` | One human-reviewed image (`frame_000186_face01`) with all 68 landmarks, color-coded by facial region (jaw/eyebrows/nose/eyes/mouth), with a legend. |
| `fig2_proposal_vs_reviewed_overlay.png` | InsightFace's raw, unreviewed proposal (red ×) vs. the final human-reviewed landmarks (blue ●) on the same face (`frame_000244_face05`) — one of the 6 images documented in §19 as corrected via a single whole-skeleton shift, chosen specifically because it visibly demonstrates that correction pattern. |
| `fig3_groundtruth_vs_ridge_test.png` | Ground truth vs. Ridge regression predictions on 3 held-out test images — **transparently selected as the best, median, and worst by already-saved test error** (`frame_000038_face02`, `frame_000123_face02`, `frame_000043_face05`), not cherry-picked; the worst case is the explicit difficult example. |
| `fig4_meanshape_vs_ridge_test_errors.png` | Grouped bar chart, mean-shape vs. Ridge mean pixel error, all 8 test images, sorted by error. |
| `fig5_original_clahe_pair.png` | Original and CLAHE versions of the same image (`frame_000038_face02`) with the identical reviewed landmark coordinates overlaid on both, demonstrating the already-verified geometric-identity property. |

Image selection method, stated explicitly per instruction: Figures 1 and 5 used images not otherwise reused elsewhere, chosen for adequate resolution/clarity only (no error-based selection, since their purpose isn't performance comparison). Figure 2 used one of the 6 already-documented "whole-skeleton-shift" images (§19), the largest of that set, chosen for clarity, not because it looks best. Figure 3's three images were selected purely by rank on the already-saved `landmark_ridge_baseline_results.json` test error — first, middle, and last of 8 sorted images — a fully transparent, reproducible selection rule.

### Key interpretation

**Figure 4 is the central evidence:** the Ridge and mean-shape bars are visually almost indistinguishable across every one of the 8 test images, not just on average. **Figure 3 shows what this means concretely** — on the worst case (`frame_000043_face05`, 90.7px mean error), the Ridge prediction (orange) is visibly displaced from the actual face structure and does not track the true landmark positions (blue); even on the best case (`frame_000038_face02`, 7.6px), the predicted skeleton's shape only loosely follows the actual face, without clearly adapting to this image's specific pose/geometry beyond what a fixed average shape would already capture.

**Figure 2 demonstrates the correction scale** the review process actually applied — a full-skeleton repositioning, not minor point nudges — on one of the clearest documented examples of that pattern (§19).

**Figure 5 reconfirms, visually, the already-established geometric-identity property**: identical landmark positions are equally valid overlays on both Original and CLAHE for this image, consistent with every numeric verification already performed in this project.

### Does Ridge show evidence of learning beyond mean-shape?

**No — not yet, and this is shown visually here, not just numerically restated.** None of the 5 figures provide visual evidence that the Ridge model's predictions are meaningfully conditioned on image content beyond what a constant average shape already provides. This is consistent with, not a new finding beyond, §23's own disclosed conclusion.

### Recommendation on proceeding with more manual annotation

**The current evidence does not yet justify investing in substantially more annotation purely to improve this specific modeling approach** — the bottleneck demonstrated here is not annotation quantity in isolation; it's that 45 training images is too few for *any* classical pixel-based regressor at a usable feature resolution to clearly separate itself from a trivial baseline, and more images alone (without also addressing feature resolution, model capacity, or a different modeling approach entirely) may not resolve this by itself. **Practical recommendation:** before committing to a larger annotation round, run one smaller, cheap diagnostic — train the same Ridge pipeline at 2-3 different feature resolutions and regularization strengths on the current 64 images (a few minutes of compute, no new annotation, no new dependency) to check whether *any* setting in this classical-model family shows a detectable gap over mean-shape at all. If even that shows no separation, the signal is that the modeling approach (not just the data volume) needs to change before more annotation is worth prioritizing; if it does show separation, that's a concrete, evidence-based case for scaling annotation next. **This diagnostic was not run as part of this task** (explicitly out of scope — "do not start another training run" was a hard constraint here) — it is reported as the recommended next step, not performed.

---

## 25. [New Batch, 2026-10-19] Batch 3 — 40 Images Prepared for Human Review

### Objective

Continue the annotation pipeline: select the next 40 images (from the 581 not yet in the 64-image reviewed pool), generate InsightFace `landmark_3d_68` proposals, and create a new CVAT task for human review. No automatic review/correction was performed -- this batch is AI-initialized only, exactly like Task 1 and Task 3 were before their respective review passes.

### Selection

Deterministic: `random.Random(500).sample(sorted(remaining_pool), 40)`, where `remaining_pool` = the 645-image `data/papuan_v2/faces/` directory minus the union of the 24-image pilot (Task 1) and 40-image calibration batch (Task 3) image IDs (64 total, 0 overlap, confirmed by reading `cvat_reviewed_landmarks.json` and `calibration_batch_40_predictions.json` directly). Seed 500, distinct from every prior seed in this project (42, 100, 200, 300, 400). Manifest: `experiments/EXP-PAP-005/batch3_manifest.csv`. Overlap with the 64 already-reviewed images verified as 0.

### Proposal generation

Reused the exact method documented earlier in this project (`PAPUAN_V2_CVAT_LANDMARK_PILOT.md`): `insightface.app.FaceAnalysis(name="buffalo_l", allowed_modules=["detection","landmark_3d_68"])`, skipping re-detection (synthetic full-crop bbox `Face(bbox=[0,0,w,h])`), calling the `landmark_3d_68` sub-model's `.get(img, face)` directly, keeping only x, y. Script saved as `experiments/EXP-PAP-005/gen_batch3_predictions.py`. Result: 40/40 succeeded, 0 failures. Output: `experiments/EXP-PAP-005/batch3_predictions.json`.

### New CVAT task

- **Task ID:** 5 (confirmed via the CVAT API after creation -- not assumed to be the next sequential number given Task 2's earlier deletion).
- **Job ID:** 5, stage `annotation`, state `new`.
- **URL:** `http://localhost:8070/tasks/5/jobs/5`
- **Name:** "EXP-PAP-005 Batch 3 -- 40 Images (AI-initialized, pending human review)"
- **Label schema:** reused the existing `face68` skeleton structure (68 sublabels, same names/order as Task 1/3/4, read directly from Task 1's live label schema). Per the lesson recorded earlier in this report (Task 2's SVG crash), the skeleton SVG was **generated fresh** for this task using `data-label-name` references, not copied verbatim from another task's saved SVG -- confirmed afterward that the task's saved SVG's `data-label-id` values are a correct subset of this task's own actual sublabel IDs (68/68), so the Task 2 crash mode does not apply here.
- **Images:** 40/40 uploaded (Original crops, `data/papuan_v2/faces/`), confirmed via `GET /api/tasks/5/data/meta` (`size: 40`).
- **Annotations:** 40 skeleton shapes imported from `batch3_predictions.json`, 2,720/2,720 points (40 x 68), confirmed via `GET /api/tasks/5/annotations`.

### Existing tasks/data confirmed unchanged

Re-checked via the CVAT API immediately after Task 5's creation: Task 1 (24 shapes), Task 3 (40 shapes), Task 4 (40 shapes) -- all unchanged. No existing CVAT task, reviewed annotation, or original prediction artifact (`insightface_68pt_pilot_predictions.json`, `calibration_batch_40_predictions.json`) was modified.

### Next step

Human review of Task 5 (`http://localhost:8070/tasks/5/jobs/5`) has not been performed -- this task stops at "ready for review," identical in scope to how Task 1 and Task 3 were handed off before their own review passes.
