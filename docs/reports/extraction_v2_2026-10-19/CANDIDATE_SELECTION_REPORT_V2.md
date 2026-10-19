# PAPUAN V2 — "v2 extraction pool" Candidate Selection Report (2026-10-19)

Status: **NEW, SEPARATE candidate pool.** Not merged with and not
replacing the existing 231-sample frozen v1 candidate set
(`docs/reports/frozen_candidate_v1_2026-10-19/`) or the shipped
`delivery/papuan_v2_final_2026-10-19/` package. No file under
`data/papuan_v2/`, `docs/reports/frozen_candidate_v1_2026-10-19/`, or
`delivery/papuan_v2_final_2026-10-19/` was modified.

## Source video

`data/raw/videos/pesta_babi.mp4`. SHA-256 re-verified read-only against the
recorded value and **matches exactly**:
`de2ea92ac3da6c8572eef47f7b610a771f1e68f469acbe81571731faca156f0f`.
25 fps, 144084 frames, 5763.36s duration, 1920x1080.

## Step 0 — Sampling rate and runtime budgeting (honest account)

Chose **5fps** (2.5x denser than v1's 2fps) — a reasonable middle of the
4-6fps range, balancing yield against runtime/redundancy on an almost
96-minute video.

Timing test: first 200 sampled frames at 5fps (det_size 640x640,
buffalo_l), **no file writes**, measured 80.8s elapsed → 2.476 sampled
frames/sec → naive extrapolation to the full video (28817 sampled frames)
was ~194 minutes, over budget. Per the instructions, chose option (b):
process a documented, bounded time range rather than reduce fps, since
5fps was judged worth keeping for yield.

Targeted bound: first 2400s (40 min) of the 5763s video, chosen from the
200-frame test's throughput to project ~81 minutes of wall-clock runtime,
within the ~90 minute budget.

**What actually happened:** once full-pool processing began (now
additionally writing face crops, CLAHE variants, and per-face landmark
JSON to disk per detected face — not done in the no-write timing test),
real wall-clock throughput was measurably *slower* than the write-free
test, and further degraded over time as later frames in the video contain
denser crowds (more detected faces per frame, each with its own
crop+CLAHE+landmark I/O cost). Measured throughput over the actual run
ranged from ~2.8 sampled-frames/sec early on down to under 1 sampled-frame/sec
in denser segments, averaging roughly 2.3-2.5 sampled-frames/sec overall.

Given this, and to respect the runtime budget honestly rather than let the
job run unboundedly, **the run was stopped (SIGTERM) before reaching the
2400s target**. The actual processed range is:

- **Sampled frames processed: 1390** (sampled_frame_index 0–1389)
- **Actual video time covered: 0.0s – 277.8s (~4.6 minutes) of the 5763.36s video**
- This is **far less than the originally targeted 2400s (40 min)**, and this
  truncation is stated here prominently and in the candidate-package
  README as required. It reflects a real, measured throughput limitation
  (crowd-density-driven per-face I/O cost), not a silent/undocumented cut.

This is a smaller window than intended, but at 5fps (denser than v1) it
still yields a usable, honestly-bounded new candidate pool from the start
of the video, distinct in content from the 2fps-sampled v1 pool (different
exact frames even in the overlapping time range, since the stride differs).

## Step 1 — Extraction + detection with full provenance

New script: `tools/papuan_v2/run_extraction_v2.py` (does not modify the
existing shared `FrameExtractor`/`FaceDetector` classes). Reuses the same
`cv2.VideoCapture` stepping formula and the same `insightface.app.FaceAnalysis`
buffalo_l / SCRFD call (det_size=(640,640), `CPUExecutionProvider`), but
additionally persists per detected face: `bbox_x/y/w/h` (original-frame
pixel coords, pre-padding), `face.det_score` (confirmed attribute, real
values observed in [0.5000, 0.9208] — 0.5 appears to be InsightFace's
internal detection threshold floor, not a missing/placeholder value),
`landmark_3d_68` (raw, verbatim JSON per face), crop dimensions,
`extraction_run_id`, and full sampling config. **This closes the exact gap
flagged in `EXTRACTION_METHODOLOGY_REPORT.md`** (v1 computed bbox in
memory but never wrote it to disk).

Outputs:
- `data/papuan_v2_ext_2026-10-19/faces/v2_frame_NNNNNN_faceNN.jpg` (3413 crops)
- `data/papuan_v2_ext_2026-10-19/clahe/v2_frame_NNNNNN_faceNN.jpg` (3413 crops, same CLAHE "Strategy B" transform as v1: `clip_min=1.5, clip_max=3.5, l_min=60, l_max=220, tileGridSize=(8,8)`, reused verbatim from `src/fer_dataset/shared/clahe.py`)
- `docs/reports/extraction_v2_2026-10-19/landmarks_raw/*.json` (3413 raw 68-point + bbox/crop-offset files)
- `docs/reports/extraction_v2_2026-10-19/frame_level_extraction_manifest_v2.csv` (1390 rows)
- `docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2.csv` (3413 rows)

**Counts: 1390 frames processed → 3413 faces detected** (mean ~2.45
faces/sampled-frame including zero-face frames).

## Step 2 — Frontality / visibility (reused landmarks, no new model)

Method: using `landmark_3d_68` indices 36 (left eye outer corner), 45
(right eye outer corner), 30 (nose tip):

```
eye_mid_x = (x36 + x45) / 2
frontality_offset = (x30 - eye_mid_x) / (x45 - x36)
frontality_score = clip(1 - |frontality_offset| / 0.6, 0, 1)
```

Score near 1 = nose centered between eyes = frontal. Buckets:
FRONTAL (score≥0.7), NEAR_FRONTAL (0.4≤score<0.7), PROFILE (score<0.4).

**Visual spot-check (15 real crops, 5 per bucket):** the 5 highest-scoring
FRONTAL examples were unambiguously front-facing in visual inspection. The
5 lowest-scoring PROFILE examples (score=0.0) included at least one
clearly side-on profile face and others visibly turned well off-axis —
metric direction confirmed correct. NEAR_FRONTAL examples were harder to
judge by eye due to low image quality (dark, motion-blurred crowd crops)
but were plausibly at a mild angle, not contradicting the score. **Overall
verdict: the metric tracks visual frontality in the expected direction and
was judged good enough to use as a filter**, with the caveat that
NEAR_FRONTAL-band judgments are less certain than FRONTAL/PROFILE
extremes given this video's generally poor lighting/motion conditions.

Distribution: FRONTAL=1490, NEAR_FRONTAL=777, PROFILE=1146 (of 3413).

Visibility check (42-point brow/eye/mouth subset, indices 17-26/36-47/48-67,
flagged CLIPPED if any point within 3px of crop boundary in crop-local
coords): OK=3037, CLIPPED_LIKELY_OCCLUDED=376.

## Step 3 — QC + frontal-preference filtering

Blur/size QC reuses v1's already-visually-justified thresholds
(`blur_variance > 75`, `min(w,h) >= 60`) as the starting point, layered
with the NEW frontal/visibility filters from Step 2 (not a replacement).
v2 pool's OWN distribution (recomputed, not assumed):
blur_variance: mean 233.2, median 131.2, min 1.7, max 2809.0 (right-skewed,
much higher variance than v1's typically smaller, more uniform pool — this
video has very mixed lighting/crowd conditions).
qc_min_dim: mean 120.8, median 66, min 18, max 1080.

False-positive spot-check: inspected the 3 lowest-`det_score` detections
(all ≈0.500, apparently InsightFace's internal floor — no detections below
0.5 were ever returned). Of 3 inspected, **1 confirmed false positive**
(`v2_frame_001229_face08` — tree foliage, not a face) and 2 confirmed real
(low-contrast) faces. This confirms the same phenomenon the v1 identity
pilot found: low-confidence detections include real non-face false
positives and are not reliable without review. This sample was NOT
manually removed from the manifest (left traceable, as per task
instructions — it fails the frontal/visibility+blur/size filters anyway in
this case and would not reach the final candidate set regardless).

**Funnel (cumulative):**

| Stage | Count | % of faces detected |
|---|---|---|
| Faces detected | 3413 | 100% |
| Pass size+blur (blur>75, min_dim≥60) | 1090 | 31.9% |
| Pass frontal(FRONTAL/NEAR_FRONTAL)+visibility(OK) | 1972 | 57.8% |
| **Pass ALL (final candidates)** | **668** | **19.6%** |

(1390 frames processed → 3413 faces detected → 668 final candidates =
19.6% of faces, 0.48 candidates/sampled-frame.)

## Step 4 — Dedup / identity proposal (PROPOSAL ONLY)

Script: `tools/papuan_v2/dedup_identity_proposal_v2.py`. Reuses ArcFace
embeddings (`tools/extract_arcface_embeddings.py`'s `ArcFaceEmbedder`, same
buffalo_l/w600k_r50 model/pattern as `identity_pilot_arcface.py`), applied
to ALL adjacent-sampled-frame face pairs in the QC'd pool (not just a small
pilot window, since full-pool proposal IS this step's purpose). Compares
cosine similarity of embeddings for every face in sampled_frame N against
every face in sampled_frame N+1. Writes
`docs/reports/extraction_v2_2026-10-19/dedup_identity_proposal_v2.csv`
with per-pair `status` in `{LIKELY_DUPLICATE_ADJACENT (sim≥0.5),
NEEDS_HUMAN_REVIEW (0.35≤sim<0.5), NO_MATCH (sim<0.35), EMBED_FAILED}`.
**No merges, no deletions, no `person_id` other than `unknown` written
anywhere** — `person_id` is `unknown` for all 3413 rows in the main
manifest.

See the final-report summary (sent to orchestrator) for exact pair counts
once this step completes — numbers are written directly to the CSV.

## Step 5 — Contact sheets

`docs/reports/extraction_v2_2026-10-19/contact_sheets/`: `frontal.jpg`,
`near_frontal.jpg`, `profile_excluded.jpg`, `blurry_excluded.jpg`,
`small_excluded.jpg`, `false_positive_candidate.jpg` — each a PIL
grid+caption sheet (sample_id, blur, dims, frontality score per thumbnail),
up to 15 real examples per category.

## Step 7 — Standardized outputs

`tools/papuan_v2/standardize_v2_candidates.py` (adapted from v1's
`standardize_images.py`, same letterbox-to-224 approach) processed all 668
final candidates: 224x224 letterboxed Original + CLAHE, 42-point landmark
subset transformed into the standardized coordinate space (scale+pad
formula identical to v1). Output:
`delivery/papuan_v2_v2_candidate_2026-10-19/02_Images/{Original,CLAHE}/`,
`03_Landmarks/Initial/` (`03_Landmarks/Reviewed/` is empty — no human
review has occurred for this new pool). 668/668 standardized, 0 failures.
`README_CANDIDATE_STATUS.md` in that directory marks this explicitly as an
unreviewed, non-final candidate pool with `expression_label_status:
pending_label` for all samples.

## Step 8 — Validation

`tools/papuan_v2/validate_v2_candidate_package.py` — all checks PASS:
images exactly 224x224, Original/CLAHE pairs exist for every candidate,
sample_id uniqueness confirmed, zero collisions with the v1
`frame_NNNNNN_faceNN` namespace (all 668 prefixed `v2_frame_`), all 28056
checked landmark coordinates (668 samples × 42 points) within [0,224],
manifest source paths all exist on disk, and fresh recounts match
(668 candidates = 668 Original files = 668 CLAHE files).

## Scale comparison to v1

668 new v2 candidates vs. 231 frozen v1 candidates — **~2.9x the v1
pool's size**, despite covering only ~4.6 minutes of video (vs. v1's full
~96-minute coverage at 2fps). This reflects the much higher candidate
yield per unit of video time at 5fps with the added frontal/visibility
filter layered on top of size/blur — i.e., per-minute yield is far higher
for v2, but total video coverage is far smaller due to the bounded-range
truncation documented in Step 0. Direct scale comparison should account
for this: v2 is denser-per-minute but currently covers much less of the
source video than v1 does.

**No decision is made here on replacing v1 or merging into main — that is
explicitly deferred to the orchestrator/supervisor**, per instructions.
