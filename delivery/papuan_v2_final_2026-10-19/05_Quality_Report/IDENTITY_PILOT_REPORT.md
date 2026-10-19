# Identity-Tracking Pilot — Report (2026-10-19)

Status: **SMALL-SCOPE PILOT ONLY**, as explicitly authorized. Not a
full-scale tracking run. No `person_id` has been written to any production
manifest.

## Scope authorized

Supervisor authorized a small identity-tracking pilot only (not full-scale
tracking, not final `person_id` assignment), per
`docs/reports/review_package_2026-10-19/IDENTITY_TRACKING_NEXT_STEP.md`'s
proposal as the starting point.

## Deviation from the originally proposed method (important)

`IDENTITY_TRACKING_NEXT_STEP.md` proposed comparing two signals on a small
window: (1) a cheap centroid/IoU tracker using `bbox_x/y/w/h` already in
`per_face_sample_manifest.csv`, and (2) ArcFace embedding similarity, then
comparing where the two agree/disagree.

**This was re-checked directly before writing any code and found not
possible with current artifacts.** `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`
are `NOT_AVAILABLE` for all 645 rows in `per_face_sample_manifest.csv` (no
exceptions — confirmed via `df['bbox_x'].unique()` returning a single value,
`NOT_AVAILABLE`). No bounding box was ever persisted for this dataset.
Without a bounding box there is no spatial position to track frame-to-frame,
so centroid/IoU tracking is **not possible** from existing artifacts alone.

**This pilot therefore implements only the ArcFace embedding-similarity
half** of the original proposal. There is no tracker output to compare it
against. This is a scope reduction, not a silent substitution — it is
documented here and the comparison step from the original proposal is
explicitly not performed.

## Pilot subset chosen

- `sampled_frame_index` 8 through 12 inclusive — **5 consecutive sampled
  frames**, the first contiguous run in the dataset with multiple faces per
  frame.
- **31 face crops total** (frame 8: 3, frame 9: 4, frame 10: 7, frame 11: 7,
  frame 12: 10).
- This is a smaller frame-count window than the "~15-20 consecutive frames"
  initially suggested, but was chosen deliberately: frame density in this
  stretch of the source video is high (up to 10-11 faces/frame), so 5
  frames already produces a 20-40 crop pilot (the actual target size for a
  hand-reviewable pilot). Extending to 15-20 frames at this density would
  have produced 100+ crops, beyond pilot scope.
- Source script: `tools/papuan_v2/identity_pilot_arcface.py`.

## Method actually used

1. Load `tools/extract_arcface_embeddings.py`'s `ArcFaceEmbedder` (reused
   as-is, not reimplemented) — InsightFace `buffalo_l` bundle, recognition
   sub-model `w600k_r50` (ArcFace architecture), `detection` + `recognition`
   modules only.
2. Run it only on the 31 pilot crop files (`original_path` from the
   manifest) — **not** the full 645-crop dataset.
3. For every pair of face crops whose `sampled_frame_index` differs by
   exactly 1 (temporally-adjacent frames only — same-frame detections are
   never compared, since the manifest already documents that different
   `face_index_in_frame` values within one frame are distinct detections),
   compute cosine similarity between their 512-dim normalized embeddings.
4. Classify each pair: `similarity_score >= 0.5` -> `TENTATIVE_MATCH`;
   `0.35 <= similarity_score < 0.5` -> `NEEDS_HUMAN_REVIEW`; otherwise
   `NO_MATCH_FOUND`.
5. Group `TENTATIVE_MATCH` edges into tentative `PILOT_CLUSTER_NN` groups
   via union-find, for convenience only — these are not identities.

## Embedding extraction outcome

25 of 31 crops produced a usable embedding. 6 crops (`frame_000008_face03`,
`frame_000009_face03`, `frame_000010_face06`, `frame_000010_face07`,
`frame_000011_face07`, and one more — see CSV `status=excluded_no_face`
rows) were excluded because InsightFace's own face re-detection found no
face in the crop at all. Visual inspection of two of these
(`frame_000008_face03`, `frame_000010_face06`) confirms this is correct: one
crop is a cap/logo with no visible face, the other is a hand — both appear
to be upstream face-detector false positives carried into the manifest, not
embedding failures. This pilot does not attempt to fix those upstream
detections; it only reports that they cannot be embedded.

## Similarity score distribution (real, observed)

169 adjacent-frame pairs were compared; 111 had both embeddings available
(the rest involve a `no_face`-excluded crop, recorded as `NO_MATCH_FOUND`
with an empty similarity score).

| Statistic | Value |
|---|---|
| min | -0.0150 |
| 5th pct | 0.0538 |
| 25th pct | 0.1243 |
| median | 0.1903 |
| 75th pct | 0.2814 |
| 95th pct | 0.8053 |
| max | 0.9182 |

The distribution is clearly bimodal: a large low-similarity mass (median
~0.19, consistent with different people / unrelated faces) and a small
high-similarity tail above ~0.55-0.9 (consistent with same-person matches
across adjacent frames). **A threshold of 0.5 was chosen because it sits
in the empirical gap between these two modes** (between the 75th percentile
~0.28 and 95th percentile ~0.81 of the observed scores), not as a textbook
default. The `0.35-0.5` band was flagged `NEEDS_HUMAN_REVIEW` rather than
auto-classified, because it sits just below the chosen threshold without
enough separation margin to trust algorithmically.

## Results summary

Of 169 adjacent-frame pairwise comparisons:

- **13 TENTATIVE_MATCH**
- **2 NEEDS_HUMAN_REVIEW**
- **154 NO_MATCH_FOUND** (includes pairs where one or both crops had no
  usable embedding)

Output: `docs/reports/identity_pilot_2026-10-19/identity_pilot_results.csv`
(31 unique `sample_id` values, every pilot sample covered at least once).
Columns: `sample_id, sampled_frame_index, pilot_cluster_id,
match_confidence, matched_against_sample_id, similarity_score, status`.
**No `person_id` column exists in this output.** `pilot_cluster_id` values
are prefixed `PILOT_CLUSTER_` specifically to avoid being mistaken for a
real identity assignment.

## Failure modes actually observed (not speculative — inspected directly)

- **Non-face detections surviving into the manifest**: at least two of the
  31 pilot crops (`frame_000008_face03`, `frame_000010_face06`) are not
  faces at all on visual inspection (a cap/logo, a hand) — these are
  upstream detector false positives, and ArcFace's own re-detection
  correctly refused to embed them (`excluded_no_face`), rather than forcing
  a spurious embedding.
- **Profile vs. near-frontal pose mismatch in the ambiguous band**: the two
  `NEEDS_HUMAN_REVIEW` pairs (e.g. `frame_000010_face01` vs.
  `frame_000011_face04`, similarity 0.4584) involve one crop in a more
  profile-angled pose and the other closer to frontal — this is a
  plausible reason embedding similarity sits in the ambiguous band rather
  than a clear match, consistent with ArcFace's known sensitivity to large
  pose change, and is exactly the kind of case this pilot is designed to
  flag for a human rather than resolve automatically.

## Explicit non-assignment statement

**No `person_id` has been written or modified in any production manifest**
(`per_face_sample_manifest.csv`, `frozen_candidate_manifest.csv`, or any
other manifest in this repository). `person_id` remains `NOT_AVAILABLE`
dataset-wide, unchanged by this pilot. The only output of this pilot is
`identity_pilot_results.csv`, a separate file using `pilot_cluster_id`
(never `person_id`) with `TENTATIVE_MATCH`/`NEEDS_HUMAN_REVIEW`/
`NO_MATCH_FOUND` status — explicitly a pilot signal pending human review,
not ground truth. **Full-scale identity tracking across all 645 samples has
NOT been run** and is out of scope for this pilot.
