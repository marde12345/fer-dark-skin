# Papuan V2 — Dataset-Wide Image Quality & Resolution Audit (645 Crops)

## 1. Objective

Audit all 645 Original face crops and their CLAHE counterparts for inventory integrity, dimension/quality distributions, before any decision on how (or whether) to scale the EXP-PAP-005 landmark-annotation pilot beyond its current 24 images. Decision-support only — no annotation, training, or dataset modification performed.

## 2. Current Branch

`main` (verified via `git branch --show-current` before and confirmed again after this audit).

## 3. Dataset Inventory and Pairing

Verified independently (not solely from a single pass):

| Check | Result |
|---|---|
| Files in `data/papuan_v2/faces/` (excluding `.gitkeep`) | **645** |
| Files in `data/papuan_v2/clahe/` (excluding `.gitkeep`) | **645** |
| Image_ids present in both directories (intersection) | **645 / 645** |
| Present in `faces/` only | 0 |
| Present in `clahe/` only | 0 |
| Duplicate filenames (case-insensitive) in either directory | 0 |
| Files that failed to open | 0 (the only non-image file, `.gitkeep`, was excluded explicitly, not silently) |
| `experiments/EXP-PAP-004/pilot_manifest.csv` (150 image_ids) vs. `faces/` | **Manifest is a strict subset of `faces/`** — all 150 manifest image_ids exist in `faces/`; 495 additional image_ids exist in `faces/` beyond the manifest (150 + 495 = 645) |

**Conclusion:** the 645-crop pool is a single, internally consistent set — no orphaned Original or CLAHE files, no duplicates, and the existing 150-image pilot (and by extension the 24-image EXP-PAP-005 landmark pilot) is confirmed to be a genuine subset of this same 645-image population, not a separately-sourced set.

Existing stable `image_id` (filename stem) identity was used throughout — no new identity scheme introduced.

## 4. Dimension and Aspect-Ratio Statistics (645 Original crops)

All 645 images opened successfully (0 failures), all in RGB color mode (645/645 — no grayscale, no RGBA, no inconsistency).

| Metric | Min | P5 | P10 | P25 | Median | P75 | P90 | P95 | Max |
|---|---|---|---|---|---|---|---|---|---|
| Width (px) | 22 | 36 | 42 | 51 | 67 | 120 | 248 | 337 | 697 |
| Height (px) | 25 | 44 | 52 | 66 | 91 | 148 | 311 | 433.2 | 966 |
| Area (px²) | 550 | 1,596.8 | 2,187.6 | 3,366 | 6,097 | 17,136 | 74,230.8 | 149,433.6 | 655,180 |
| Aspect ratio (w/h) | 0.468 | 0.626 | 0.655 | 0.714 | 0.782 | 0.831 | 0.886 | 0.924 | 1.564 |

Mean width 109.95px, mean height 143.79px, mean area 32,175px² (means pulled well above the medians by a long right tail of larger crops — the distribution is right-skewed, not symmetric; median is the more representative "typical crop" figure).

**Aspect-ratio outliers (below 0.3 or above 3.0 — a sign of a severely truncated/partial-face crop):** **0 found** across all 645. The entire dataset's aspect ratios sit in a comparatively narrow, plausible-for-a-face-crop band (0.468–1.564).

**Original vs. CLAHE dimension consistency:** checked all 645 pairs individually (not assumed from the earlier spot-check on the 24-image pilot) — **645 / 645 exact matches, 0 mismatches**. This directly re-confirms, at full dataset scale, the geometric-identity property of this project's CLAHE transform already established for the 24-image pilot and the broader 645-image set in earlier reports.

## 5. Quality Signals Investigated

**5a. Image dimensions** — covered above (Section 4); this is the only quality-adjacent signal with any prior precedent in this project's documentation (the EXP-PAP-005 QC report's crop-size table).

**5b. Blur/sharpness (Laplacian variance, `cv2.Laplacian(gray, cv2.CV_64F).var()`)** — a standard, widely-used blur heuristic (lower variance = less high-frequency detail = more likely blurry or low-texture), computed via `cv2`, already installed, no new dependency. Computed for all 645 images, 0 failures:

| Metric | Min | P5 | P10 | P25 | Median | P75 | P90 | P95 | Max |
|---|---|---|---|---|---|---|---|---|---|
| Blur variance | 1.69 | 16.85 | 31.88 | 60.61 | 151.09 | 325.35 | 600.89 | 752.86 | 1,966.81 |

Mean 240.65 (again right-skewed, median more representative).

**Correlation between crop area and blur variance: Pearson r = −0.209** (N=645) — a weak negative correlation, reported as a neutral statistic only. **Explicitly not interpreted as causal and not treated as evidence that smaller crops are sharper or blurrier** — raw Laplacian variance is known to be scale-sensitive (a resize or crop-size difference alone shifts the measured variance independent of actual focus quality), and no area-normalization was applied here, so this correlation is reported, not acted upon.

**5c. Crop truncation / unusual aspect ratios:** covered in Section 4 — 0 outliers found by the aspect-ratio heuristic.

**5d. Existing quality metadata search:** searched `data/papuan_v2/`, `experiments/EXP-PAP-004/`, `experiments/EXP-PAP-005/` for any pre-existing detector-confidence, blur, or sharpness score per image. **Result: none found.** The only "confidence"-matching fields that exist are the human annotator's self-reported confidence (High/Medium/Low) on the *emotion label* from the superseded Label Studio track (`ai_predictions.csv`, `label_studio_export.csv`) — unrelated to image quality — and the word "quality" appearing once in `experiments/EXP-PAP-005/metadata.json`'s `image_quality_limitation_note`, which is prose written during the prior documentation task, not a computed metric. **Every quality signal in this report (dimensions, blur variance) was newly computed for this audit; none was already recorded anywhere in the project.**

**5e. Explicit scope statement, per instruction:** no image in this dataset was visually inspected as part of this audit. All findings above are numeric heuristics computed programmatically. Occlusion and landmark-localization difficulty specifically are **not** assessed by any signal computed here — blur variance and dimensions are proxies for *image clarity*, not for whether a *specific facial landmark* is occluded or hard to localize, and this report does not conflate the two.

## 6. Outliers and Limitations

**Smallest-area tail (descriptive, not a threshold recommendation):**
- Below the 5th percentile (≤1,596.8 px²): **33 images**.
- Below the 1st percentile (≤775 px²): **8 images**, the smallest being `frame_000083_face01` at 22×25 = 550px².

**Limitation of blur-variance as a quality signal here:** given the unresolved scale-sensitivity issue (Section 5b), this metric alone should not be used to rank or exclude images without a documented normalization approach — flagged as an open methodological question, not resolved by this audit.

**Limitation of this audit generally:** it characterizes the *dataset's* dimension/blur distribution; it does **not** and cannot establish which specific images would be hard for a *human reviewer* to confidently judge, since that depends on factors (occlusion, lighting, facial pose) not measured here. The EXP-PAP-005 pilot's own finding — that the 3 smallest pilot images all received zero corrections, a pattern consistent with (not proof of) unverifiability — remains the only reviewer-grounded evidence available, and it covers only 24 of 645 images.

## 7. Proposed Quality-Control Policies (compared, not decided)

| Option | Mechanism | Advantages | Trade-offs |
|---|---|---|---|
| **A — Dimensional threshold flagging** | Flag images below a chosen width/height/area threshold for mandatory additional review before acceptance | Simple, automatable, catches the clearest cases (e.g. the 8 images below the 1st percentile) | **No defensible numeric threshold exists yet** — this audit characterizes the distribution but does not establish where "too small to review" actually begins; setting one now would be arbitrary, which the task explicitly warns against |
| **B — Per-image/per-point "uncertain" flag in CVAT** | Let the reviewer mark an image or individual landmark as uncertain/unusable during review itself | Captures the reviewer's actual judgment at the moment of review — the one thing no automated heuristic here can measure; directly closes the Section 6 gap (no reviewer-grounded data beyond the 24-pilot) | Requires a CVAT workflow/schema change (a new attribute or tag) — not implemented here, since this task excludes CVAT structure changes; is a recommendation for the *next* annotation round, not retroactive to the current pilot |
| **C — Training-set exclusion by documented criterion** | Exclude images below a quality criterion from the training set only (data stays in the repository, never deleted) | Least invasive to the annotation process itself; reversible (criterion can be revised); doesn't block annotation, only downstream training | Still requires *some* criterion to be defined and justified first — same threshold problem as Option A, just deferred to a later pipeline stage |

**Recommended minimal policy, given the evidence actually available:** **Option B first, Option A/C deferred.** The single biggest gap this audit surfaces is that no per-image reviewer judgment exists beyond the 24-image pilot, and no dimensional threshold can be responsibly set without it (per the task's own explicit instruction not to infer one from the 24-image pilot). Adding a lightweight "uncertain" flag to the CVAT review workflow for the *next* annotation batch would generate exactly the reviewer-grounded data needed to set a defensible Option A/C threshold later — using this audit's dimension distribution (Section 4) as the measurement scale once real review-uncertainty data exists to calibrate it against.

**If the evidence is insufficient to set a threshold today — stated plainly: it is.** This audit characterizes the full 645-image distribution (a necessary input), but a threshold also requires knowing, for a reasonably-sized and reasonably-distributed sample, which specific images a human reviewer actually found unverifiable — data this project does not yet have at scale. **Recommended path to obtain it:** run Option B (reviewer-flagging) on a next, larger-than-24 annotation batch, stratified across the dimension distribution characterized here (e.g. deliberately including images from each decile of Section 4's area distribution, not just a random/deterministic sample as before) — this would let a threshold be set from actual reviewer behavior rather than from dimensions alone.

## 8. Recommended Next Action

1. Decide whether to add an "uncertain/unusable" flag to the CVAT annotation workflow (Option B) before the next annotation batch — a design decision for the user/supervisor, not made here.
2. If adopted, design the next pilot/batch sampling to deliberately span the full dimension distribution characterized in Section 4 (not just reuse the existing 150-image pilot pool, which was not drawn with this purpose in mind), so the resulting uncertain-flag data can actually calibrate a threshold.
3. Only after that: revisit Options A/C with real data behind the threshold choice.
4. Separately, resolve the still-open CVAT job-state question (Section 9) if it matters administratively.

## 9. CVAT Job-State Observation

Verified read-only, twice (once via the background audit, once independently): **Task 1 / Job 1 — `stage: "annotation"`, `state: "in progress"`** — still not marked `"completed"`, unchanged since the prior (2026-10-19) report. No write/PATCH call was made to CVAT at any point in this audit; this is purely an administrative observation, explicitly treated as separate from annotation QC per instruction — whether to mark it complete is a decision for the user, not performed here.

## 10. Files Inspected

`data/papuan_v2/faces/*` (645 images, read-only `PIL.Image.open`/`.size`/`.mode` and `cv2` grayscale+Laplacian reads), `data/papuan_v2/clahe/*` (645 images, dimension check only), `experiments/EXP-PAP-004/pilot_manifest.csv`, `experiments/EXP-PAP-004/ai_predictions.csv`, `experiments/EXP-PAP-004/label_studio_export.csv`, `experiments/EXP-PAP-005/metadata.json`, CVAT API (`GET /api/jobs?task_id=1`, read-only).

## 11. Files Created or Modified

- `docs/reports/PAPUAN_V2_DATASET_QUALITY_AUDIT.md` (this report, new).
- Appended updates to `docs/reports/PAPUAN_V2_CURRENT_STATE.md` and `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`.

## 12. Changes NOT Made

No image file modified, moved, or deleted. No annotation, prediction, or CVAT label/task-structure change. No model trained. No additional images annotated. No CVAT job-state change (observed only, per instruction treating this as a separate administrative action). No Label Studio change. No new dependency installed. No numeric quality threshold was invented or adopted — Section 7 explicitly declines to set one and explains why.

## 13. Date/Time

2026-10-19.

## 14. Git Status

Branch: `main`. New: `docs/reports/PAPUAN_V2_DATASET_QUALITY_AUDIT.md`. Modified (appended): `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`. All uncommitted, per the standing no-auto-commit rule. No other files touched.

---

*Audit and decision-support report only. No annotation, training, or dataset changes were made.*
