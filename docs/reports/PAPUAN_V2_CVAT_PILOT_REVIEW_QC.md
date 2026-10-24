# Papuan V2 — CVAT Pilot Review Export & QC (EXP-PAP-005)

## 1. Objective

Export the EXP-PAP-005 CVAT pilot's annotations after the user's reported human-review pass, validate them against the original InsightFace proposals, run quality control, and verify Original↔CLAHE lineage — without modifying CVAT, regenerating predictions, training anything, or scaling the pilot.

## 2. Current Branch and Environment

Branch: `main` (verified via `git branch --show-current`). CVAT: self-hosted, reachable at `http://localhost:8070`, confirmed `200` on `/api/server/about`. Task id 1, "EXP-PAP-005 Facial Landmark Pilot (InsightFace-initialized, human-reviewed)".

## 3. Source Artifacts Inspected

`experiments/EXP-PAP-005/metadata.json`, `experiments/EXP-PAP-005/insightface_68pt_pilot_predictions.json`, `experiments/EXP-PAP-005/qc_validate_pilot_landmarks.py`, `experiments/EXP-PAP-004/pilot_manifest.csv`, `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md`, `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md` (sections 13–14, current abbreviation scheme), `data/papuan_v2/faces/`, `data/papuan_v2/clahe/`.

## 4. CVAT Task State (verified, not assumed)

- `GET /api/tasks/1`: `status: "annotation"`, `size: 24`, `updated_date: 2026-10-18T17:07:01Z`.
- `GET /api/jobs?task_id=1`: **job stage=`"annotation"`, state=`"in progress"`** — not marked `"completed"` in CVAT's own workflow metadata, despite the user reporting the review finished.
- Label schema: parent label `face68` (id 1), 68 sublabels, all matched 1:1 to the verified landmark-index mapping with zero unmatched names (confirms the current abbreviation scheme from the prior report is still in effect, unmodified).

**This discrepancy (job state vs. reported completion) is addressed directly in Section 8.**

## 5. Export Procedure

Used CVAT's REST API directly (`GET /api/tasks/1/annotations` for shape/element data, `GET /api/tasks/1/data/meta` for per-frame filename/dimensions) — the same safe, already-validated method used throughout this pilot, not CVAT's file-based export feature (not needed; the API gives the same underlying data with less format-conversion risk). Joined strictly by `label_id` → the already-verified landmark index (never by array position or display name alone, per the documented CVAT pitfall), and by `frame` → `image_id` (re-verified this export: frame order still matches `sorted(image_ids)` exactly, filename-stem-checked before building any output). The original prediction file (`insightface_68pt_pilot_predictions.json`) was not read-modified or overwritten at any point.

## 6. Export Schema and Coordinate Convention

New artifact: **`experiments/EXP-PAP-005/cvat_reviewed_landmarks.json`** (separate from, and does not overwrite, the original predictions file). One record per (image, landmark):

```json
{
  "experiment_id": "EXP-PAP-005",
  "image_id": "frame_000009_face04",
  "source_image_id": "frame_000009_face04",
  "image_path": "data/papuan_v2/faces/frame_000009_face04.jpg",
  "image_width": 64, "image_height": 67,
  "landmark_index": 0, "landmark_name": "j0",
  "x": 16.10, "y": 41.43,
  "occluded": false, "outside": false,
  "landmark_schema": "insightface_landmark_3d_68",
  "annotation_source": "insightface",
  "review_status": "human_reviewed"
}
```

Coordinate convention: pixel, crop-relative — unchanged from the original predictions' convention (Section 4.A of the prior landmark-schema investigation), so no conversion was needed or performed. `source_image_id` is set equal to `image_id` since the Original branch *is* the canonical source (per the confirmed CLAHE-reuse design, Section 11) — this field exists to keep the schema forward-compatible if a future branch ever needs a distinct source identity, not because one exists today.

## 7. Image/Landmark Coverage

- Images matched: **24 / 24**.
- Landmark points matched: **1,632 / 1,632** (24 × 68).
- 0 missing images, 0 missing/duplicate/unexpected landmark indices.

## 8. Proposal-versus-Reviewed Correction Statistics

**Explicitly not accuracy — this measures how much the human reviewer's final coordinates differ from the initial AI proposal, nothing more.** Tolerance: 0.5px (accounts for CVAT's internal float storage/serialization, distinguishing real correction from rounding noise).

| Metric | Value |
|---|---|
| Points changed (>0.5px) | 220 / 1,632 (13.5%) |
| Points unchanged (within tolerance) | 1,412 / 1,632 (86.5%) |
| Mean displacement (corrected points) | 10.34 px |
| Median displacement | 8.27 px |
| P25 / P75 / P90 / P99 | 4.12 / 14.97 / 21.77 / 29.94 px |
| Max displacement | 38.97 px |
| Mean displacement, normalized by image diagonal | 0.0742 |
| Median displacement, normalized | 0.0705 |

**The verified, flagged finding:** per-image correction counts are **not evenly distributed**:

| image_id | points corrected (of 68) |
|---|---|
| frame_000009_face04 | 19 |
| frame_000010_face05 | 23 |
| frame_000022_face11 | 66 |
| frame_000049_face04 | 51 |
| frame_000226_face03 | 61 |
| **all other 19 images** | **0** |

Only 5 of 24 images show any detected correction; those 5 show substantial correction (19–66 of 68 points each). The remaining 19 images are coordinate-identical to the original InsightFace proposal within tolerance.

**What this does and does not establish:** this pattern is *consistent with* either (a) the InsightFace proposals genuinely needing no correction on those 19 images, or (b) those 19 images not actually having been reviewed despite the user's report, or (c) some mix. **Coordinate data alone cannot distinguish these possibilities**, and this report does not pick one. This is stated as a verified fact (the correction counts) with an explicitly unresolved interpretation, not smoothed over — consistent with Section 4's finding that CVAT's own job-state metadata still reads `"in progress"`, not `"completed"`.

## 9. Per-Region and Per-Image Findings

Per-region correction rates (across all 1,632 points, all 24 images — so these are necessarily dominated by the 5 corrected images):

| Region | Corrected / Total | Rate |
|---|---|---|
| Right eyebrow | 25 / 120 | 20.8% |
| Right eye | 30 / 144 | 20.8% |
| Nose bridge | 16 / 96 | 16.7% |
| Left eyebrow | 15 / 120 | 12.5% |
| Nose base | 15 / 120 | 12.5% |
| Left eye | 18 / 144 | 12.5% |
| Mouth outer | 36 / 288 | 12.5% |
| Mouth inner | 22 / 192 | 11.5% |
| Jaw | 43 / 408 | 10.5% |

Right-side eye/eyebrow regions show the highest correction rates among the 5 corrected images — not generalizable to the other 19 given the small corrected-image count (5), stated as a descriptive observation only.

## 10. QC Checks and Outcomes

| Check | Result |
|---|---|
| 24 expected images represented | PASS (24/24) |
| Exactly 68 landmarks per image | PASS (all 24) |
| 1,632 total landmarks | PASS |
| No duplicate landmark indices per image | PASS |
| No missing/unexpected indices | PASS |
| Valid finite x/y coordinates | PASS (all finite) |
| Coordinates within image bounds | 5 points (of 1,632) outside bounds — same 5 points already flagged as non-fatal in the original pilot report (Section 13 there), on the same tightly-cropped image; unchanged by review |
| Stable image_id mapping | PASS — frame order re-verified against sorted image_ids before export |
| Correct landmark index/name mapping | PASS — all 68 sublabels matched the verified index table with 0 unmatched |
| No missing reviewed annotations | PASS structurally (all 1,632 present) — see Section 8 for the separate, unresolved *review-coverage* question |
| Reviewed coordinates distinct from proposal where corrected | PASS — 220 points differ by >0.5px, confirmed real coordinate changes, not serialization artifacts (spot-checked: several corrected points differ by 10+ px, far outside any plausible rounding range) |

**Overall QC: structural PASS. Review-coverage interpretation: unresolved, flagged explicitly (Section 8), not silently passed.**

## 11. Original-to-CLAHE Pairing and Coordinate Reuse

Verified directly for all 24 reviewed images: `data/papuan_v2/faces/<image_id>.jpg` and `data/papuan_v2/clahe/<image_id>.jpg` both exist for every `image_id`, and their pixel dimensions are identical (re-confirmed via `PIL.Image.size` for all 24 pairs — 0 mismatches). This reuses the geometric-identity finding already established for the full 645-image dataset (CLAHE is a pure per-pixel lightness transform here).

**Training-target reuse mechanism (documented, not yet implemented — no training performed):** `cvat_reviewed_landmarks.json`'s coordinates serve as the single canonical landmark source; a CLAHE-branch training run would read the same file, substitute `image_path` from `data/papuan_v2/faces/` to `data/papuan_v2/clahe/`, and use the identical `(x, y)` values — no new annotation file, no coordinate transform. This satisfies the "no redundant CLAHE annotation file" instruction directly: one canonical reviewed-annotation source, `preprocessing` is a substitution at load time, not a stored duplicate.

## 12. Provenance Conventions

Per the confirmed terminology: these are **"InsightFace-initialized, human-reviewed landmark annotations"** — not independent human-from-scratch annotation. The original proposals (`insightface_68pt_pilot_predictions.json`) and the reviewed export (`cvat_reviewed_landmarks.json`) are kept as two separate, both-preserved artifacts specifically so corrections remain auditable (this report's Section 8 comparison depends on both existing independently). `metadata.json`'s `review_status` was updated only to the extent directly supported by verified CVAT state — it now reads `"cvat_export_captured_2026-10-19_coverage_ambiguous"` with an explicit note (not a blanket `"human_reviewed"` claim), because the data does not unambiguously support claiming full review coverage (Section 8).

## 13. Problems and Limitations

1. **Review-coverage ambiguity (Section 8)** — the central open question this report surfaces rather than resolves.
2. **CVAT job never marked "completed"** in its own workflow state — either an oversight (the user simply didn't click the stage-completion control) or a genuine signal of partial work; not distinguishable from the API alone.
3. Same 5 out-of-bounds points already known from the original pilot report persist unchanged (jaw/ear points near one tight crop's edge) — not a new issue, re-confirmed only.
4. No independent second reviewer exists for this pilot (by design, per the original pilot scope — "one human reviewer").

## 14. Changes Made

- `experiments/EXP-PAP-005/cvat_reviewed_landmarks.json` (new).
- `experiments/EXP-PAP-005/proposal_vs_reviewed_comparison.json` (new).
- `experiments/EXP-PAP-005/metadata.json` (updated: `review_status` changed from `"ai_initialized_pending_human_review"` to a status reflecting the verified-but-ambiguous coverage, plus a `review_status_note` field and paths to the two new artifacts).
- `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md` (this report).
- Appended updates to `docs/reports/PAPUAN_V2_CURRENT_STATE.md` and `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`.

## 15. Changes NOT Made

No CVAT label/skeleton schema change. No annotation moved or modified in CVAT. No InsightFace predictions regenerated (original file untouched, byte-for-byte — not re-read-and-rewritten). No model training. No additional images annotated. No CLAHE images independently annotated. No Label Studio changes. No unrelated code/data changes. No commit, no push.

## 16. Recommendation on Readiness to Scale

**Not ready to recommend scaling yet — pending the Section 8 clarification.** If the 19 zero-correction images genuinely needed no correction, the pilot is a strong, clean result (a 13.5% overall correction rate with the expected regional pattern) and scaling is reasonable to discuss. If those 19 images were not actually reviewed, the pilot's real reviewed-and-validated coverage is 5/24 images, not 24/24, which is a materially different starting point for any scale-up decision. **This is a factual question for the user to resolve** (e.g. by reopening the CVAT task and confirming each image's review status, or explicitly marking the CVAT job stage as completed once genuinely done) — not something this report decides unilaterally.

## 17. Exact Next Step

User confirms (or CVAT job-completion state confirms) whether all 24 images were actually opened and checked point-by-point, or only the 5 showing corrections. Once resolved, either (a) finish reviewing the remaining 19 if incomplete, or (b) explicitly mark the CVAT job stage as completed and treat the pilot as fully reviewed — then proceed to the scale-up decision.

## 18. Date/Time

2026-10-19.

## 19. Git Status

Branch: `main`. New/modified: `experiments/EXP-PAP-005/cvat_reviewed_landmarks.json`, `experiments/EXP-PAP-005/proposal_vs_reviewed_comparison.json`, `experiments/EXP-PAP-005/metadata.json`, `docs/reports/PAPUAN_V2_CVAT_PILOT_REVIEW_QC.md`, `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`. All uncommitted, per the standing no-auto-commit rule. No other files touched.

---

*Export and QC report. No CVAT data, labels, or predictions were modified in producing this report — findings are reported, not acted upon, where resolution requires user input (Section 8).*

---

## 20. [Update 2026-10-19] Reviewer Confirmation and Image-Quality Limitation

### Confirmed reviewer statement

The human reviewer (the user) confirmed directly, in conversation, on 2026-10-19:
- All 24 pilot images were visually reviewed.
- Some images already had correct InsightFace landmark positions and required no coordinate changes.
- Some images had **insufficient image quality/resolution, making facial features difficult to detect or localize reliably**.
- Five images required manual corrections, already made in CVAT (matching the 5 identified in Section 8).

This resolves the Section 8/16 open question to the extent a reviewer statement can: the reviewer did look at all 24, addressing the "was review actually performed on all 24" uncertainty. It does **not** resolve, and this report does not claim to resolve, a finer-grained question raised below: on the 19 unchanged images, how many were unchanged because the proposal was genuinely correct, versus unchanged because the image quality made confident correction impractical. The reviewer's statement confirms both situations occurred somewhere in the 24; it does not say which image is which.

### Three categories — not mutually exclusive, as instructed

| Category | Definition | What the comparison-stats data can show | What it cannot show |
|---|---|---|---|
| **A — Accepted without correction** | Reviewer judged the AI proposal correct as-is | Which images had 0 points changed (19 images, Section 8) | Whether "0 changed" reflects genuine correctness or an unverifiable image the reviewer couldn't confidently correct |
| **B — Manually corrected** | Reviewer judged the proposal wrong and moved the point(s) | Which images/points changed, by how much (5 images, 220 points, Section 8) | Whether every corrected image was *fully* resolved, or only the clearly-wrong points were fixable and others were left uncertain |
| **C — Quality-limited** | Image resolution/clarity made confident judgment difficult, independent of whether a correction was ultimately made | Nothing directly — **no per-image quality flag exists in any artifact** (CVAT task data, the reviewed export, or prior reports) | Which specific image_ids the reviewer considered quality-limited — **this was not recorded and is not invented here** |

**A and C can co-occur** (an image could be "accepted unchanged" specifically *because* it was too unclear to confidently correct, not because it was verified accurate) — this is flagged as a real possibility below, not asserted as fact. **B and C can also co-occur** (a reviewer might correct the points they could judge on a low-quality image while remaining unsure about others).

### What the existing evidence can and cannot establish about which images had quality problems

No log, CVAT field, or prior report records a per-image quality assessment. **Stating this explicitly, per instruction, rather than inventing image IDs.** The only objective, pre-existing evidence relevant to image quality is **crop pixel dimensions**, already present in `cvat_reviewed_landmarks.json`:

| | image_id | dimensions | area (px²) | points corrected |
|---|---|---|---|---|
| Smallest | `frame_000078_face01` | 22×28 | 616 | **0** |
| 2nd smallest | `frame_000227_face04` | 32×39 | 1,248 | **0** |
| 3rd smallest | `frame_000248_face13` | 37×44 | 1,628 | **0** |
| 4th smallest | `frame_000054_face05` | 49×52 | 2,548 | 0 |
| 5th smallest | `frame_000012_face10` | 49×63 | 3,087 | 0 |
| ... | | | | |
| Corrected (51 pts) | `frame_000049_face04` | 114×157 | 17,898 | 51 |
| Corrected (61 pts) | `frame_000226_face03` | 120×133 | 15,960 | 61 |

**Verified finding:** there is **no simple monotonic relationship between crop size and correction count** in this pilot. The three smallest crops in the entire 24-image set (616, 1,248, 1,628 px²) all show **zero** corrections — the same pattern as the 16 mid-sized uncorrected images — while two of the most heavily corrected images (51 and 61 points) are comparatively large (17,898 and 15,960 px²).

**This is worth stating plainly, with appropriate hedging:** this pattern is *consistent with* (not proof of) the smallest crops being genuinely unverifiable — too small for the reviewer to confidently judge *or* correct any point, resulting in a "0 corrections" outcome that looks identical in the data to "all 68 points were already correct," even though the underlying reviewer experience may have been very different. **This report does not assert this is what happened on these three specific images** — only that the reviewer's own qualitative statement ("some images had insufficient quality to localize features reliably") is directly consistent with this data pattern, and that the pattern itself is real and verified, independent of interpretation.

**Important distinction, per instruction:** nothing here establishes that InsightFace's **face detector failed** on any image — detection clearly succeeded for all 24 (68 landmarks exist for every image, Section 7). The concern is **localization reliability on a low-resolution crop**, a separate issue from detection failure, and no artifact in this project distinguishes "detector failed" from "detector succeeded but a human can't verify the result" — this report does not conflate the two.

### Statistics (unchanged, restated per instruction)

24 images, 68 landmarks/image, 1,632 total landmarks, 220 points changed beyond the 0.5px tolerance, 5 images with corrections, 19 images with no significant coordinate change. Displacement statistics unchanged from Section 8 (mean 10.34px, median 8.27px among corrected points). **Restated explicitly:** an unchanged coordinate means the reviewer did not move that point — it is evidence of reviewer *acceptance*, not independent evidence of model *accuracy* against any ground truth outside this same review process.

### Limitation and scale-up recommendation

**How low resolution affects reliable review:** on crops as small as 22×28px, individual facial landmarks (eye corners, lip edges) may occupy only 1-2 pixels, below the threshold where a human can confidently distinguish "correctly placed" from "off by a few pixels" — the displacement statistics in Section 8 (median correction ~8px) would be *larger than the entire image* on the smallest crops in this pilot.

**Why a reviewer should not be forced to guess:** a forced-choice review (every point must be either "confirmed correct" or "moved somewhere") on an unverifiable image produces data that *looks* identical to confident acceptance, silently contaminating the resulting "ground truth" with unverified guesses — exactly the ambiguity this section documents. This is a known class of problem in annotation methodology generally, not specific to this project.

**Options for a documented quality-control rule** (proposed, **not implemented, pending approval** per instruction):
1. **Minimum crop-dimension threshold** (e.g. minimum side length or area) below which an image is automatically flagged `quality_review_required` at import time, routed to a separate review queue or explicitly marked `uncertain` rather than silently mixed in with confidently-reviewed images.
2. **An explicit reviewer-facing "low confidence" flag per image or per point** in the CVAT workflow (e.g. a tag, or a dedicated attribute), so future ambiguity like this is captured at review time rather than reconstructed after the fact from coordinate deltas.
3. **Exclusion from the training set** for images below a resolution threshold, while still keeping them in the repository (never deleting data) — a stricter version of option 1.

**Why the 24-image pilot cannot estimate the quality distribution of all 645 images:** 24 images is a small, specific, already-biased sample (drawn from the 150-image pilot subset, itself a sample of 645) — its size distribution here (616 to 152,334 px²) shows the *range* that exists but not the *proportion* of the full 645 that falls below any given quality threshold. A dedicated, larger size/quality audit of the full 645-image set would be needed before setting a numeric threshold with any statistical basis — this pilot can motivate that audit, not substitute for it.

**No decision made.** Which rule (if any), what threshold, and whether to apply it retroactively to this 24-image pilot are left for the user/supervisor to decide — this report documents the problem and options, not a resolution.

---

*2026-10-19 update. No CVAT annotations, predictions, or dataset files were modified in producing this update — only documentation and the already-existing metadata.json provenance fields.*
