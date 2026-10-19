# QC Decision Summary — papuan_v2 (2026-10-19)

Status: **PENDING APPROVAL.** This document explains the QC filter already
proposed in `docs/reports/qc_pilot_2026-10-19/QC_THRESHOLD_RECOMMENDATION.md`
in plain language for a supervisor decision. It does not adopt, finalize, or
change the threshold. `qc_status` remains `PENDING_THRESHOLD` for all 645
rows in the manifest.

## Re-verification (this phase)

The filter `qc_blur_variance > 75 AND min(qc_width, qc_height) >= 60` was
re-run directly against the current 645-row
`docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv`.
**Result: 231 matching rows — identical to the 231 rows already present in
`docs/reports/qc_pilot_2026-10-19/candidate_samples.csv`** (exact `sample_id`
set match, zero difference). The cached 231 figure is confirmed accurate,
not stale.

## (a) What the two metrics actually measure, and their limits

- **Blur variance** = variance of the Laplacian (second-derivative edge
  response) of the grayscale crop. High variance means lots of sharp edges;
  low variance means a flat, soft image. It is a defocus/motion-blur proxy,
  not a direct measurement of "can a human see the eyebrows." Limitations
  observed directly in the contact sheets: it is **scale-dependent** (the
  same true sharpness reads as lower variance on a large crop than a small
  one, because detail is spread over more pixels), it can be inflated by
  **compression artifacts or sensor noise** on small crops (sharp-edged
  noise looks "sharp" to a Laplacian even though no real facial detail is
  present), and it says nothing about lighting, occlusion, or whether the
  blur is even across the face or only in the eye/mouth region specifically.
- **min(width, height)** is a crude size floor. It does not account for
  aspect ratio (a 60x200 sliver passes just as easily as a 60x60 square),
  and it has no knowledge of partial occlusion — a 100x100 crop with the
  mouth cut off by a frame edge or another object still counts as "big
  enough."

Both are cheap, automatable proxies for annotatability — not ground truth.

## (b) Why blur>75 + min_dim>=60 is defensible for this dataset

Summarized from the contact-sheet review already done in
`QC_THRESHOLD_RECOMMENDATION.md` (not re-derived here):

- Crops below ~50-65px on the smaller side are unusable for landmark work
  regardless of sharpness — even blur variance up to ~2000 on a 22x25px
  crop produced unreadable blotches, not distinct eyebrow/eye/mouth regions.
- A blur floor in the 60-100 range reliably screens out genuine motion blur
  (observed: crops with blur <30 at large size, e.g. 291x326px, were
  visually unreadable) without needing to be aggressive, because crops
  already above ~50px of real in-focus detail naturally produce Laplacian
  variance well past that range.
- The chosen pair (75, 60) sits inside both of those visually-verified safe
  zones with a small margin, rather than at the exact boundary.

## (c) Status

**This threshold is a recommendation only. It is PENDING APPROVAL.** No
`qc_status` field has been changed, no row has been dropped from the
manifest, and `select_candidate_samples.py` continues to require the
threshold be passed explicitly as CLI arguments rather than hardcoding it.
A supervisor must explicitly approve (or adjust) blur>75 / min_dim>=60
before it is treated as final.

## ~250 gap-closing check

Current candidate count is 231 against an approximate target of 250 (gap of
19). Rather than loosening the threshold globally, two narrow bands just
below the current cutoffs were measured directly against the manifest:

| Band | Definition | Count |
|---|---|---|
| Blur band | `50 <= qc_blur_variance < 75` AND `min_dim >= 60` | 51 |
| Size band | `qc_blur_variance > 75` AND `52 <= min_dim < 60` | 65 |

A handful of real crop files from each band were opened directly
(`data/papuan_v2/faces/*.jpg`) for a visual call:

- `frame_000137_face02` (blur 74.2, 212x270): clearly legible — eyebrows,
  eyes, and mouth all distinct despite being just under the blur cutoff.
- `frame_000134_face03` (blur 73.8, 87x112): small but features still
  identifiable.
- `frame_000103_face01` (blur 73.7, 179x367): eyebrows/eyes legible; mouth
  is occluded by a foreground log — a framing problem, not a blur problem,
  and the kind of case neither metric can catch.
- `frame_000069_face03` (blur 1357.8, 59x64, size band): too small to make
  a confident eyebrow/eye call despite very high sharpness — supports the
  existing size-floor reasoning.
- `frame_000054_face02` (blur 1122.5, 56x66, size band): partial face, eyes
  shadowed under a hat — not confidently annotatable.

**Factual conclusion:** the blur-band samples just under 75 (51 total) look
visually closer to "usable" than the size-band samples just under 60px (65
total), which is consistent with the existing finding that the size floor
is the harder constraint of the two. However, the spot-check was only 5
images out of 116 candidates in these two bands, is not a substitute for a
full contact-sheet pass, and under this phase's scope no threshold change is
being made. The honest conclusion is: **~231 remains the defensible,
already-verified count; the ~250 target should flex downward rather than be
forced by loosening the threshold on a 5-image spot-check.** If a
supervisor wants to pursue the blur band specifically (50-75, min_dim>=60),
a full contact-sheet review of those 51 samples — not a shortcut — would be
the correct next step, and is explicitly out of scope here.
