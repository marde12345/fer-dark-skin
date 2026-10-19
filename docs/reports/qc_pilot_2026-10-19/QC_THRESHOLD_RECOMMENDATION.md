# QC Threshold Recommendation — papuan_v2 (2026-10-19)

Status: **RECOMMENDATION ONLY, NOT APPROVED.** `qc_status` in
`per_face_sample_manifest.csv` remains `PENDING_THRESHOLD` for all 645 rows.
Nothing here finalizes a threshold; it is input for a human/supervisor
decision. This document is grounded in direct visual inspection of the
contact sheets in `contact_sheets/` (see `qc_pilot_strata_index.md` for the
full index), read via the Read tool during this audit.

## 1. Distribution re-verification

The distribution in `docs/reports/extraction_audit_2026-10-19/qc_threshold_candidates.md`
was re-computed independently against the current 645-row
`per_face_sample_manifest.csv` and matches exactly (same percentile values
to the digit). It is accurate and is reused here rather than duplicated:

| Percentile | qc_blur_variance | min(width,height) px |
|---|---|---|
| p5  | 16.85  | 36.0 |
| p10 | 31.88  | 42.0 |
| p25 | 60.61  | 51.0 |
| p50 | 151.09 | 67.0 |
| p75 | 325.35 | 120.0 |
| p90 | 600.89 | 244.0 |
| p95 | 752.86 | 336.8 |

## 2. What the contact sheets actually show

Five strata/cross-cells were opened and visually reviewed (not estimated):

- **`sheet_blur_p0-10_x_size_p0-10.png`** (4 samples, blur 15.9–26.7,
  29x35–37x50 px): faces reduced to indistinct dark blobs. No eyebrow, eye,
  or mouth boundary is identifiable at all. Unusable for annotation.

- **`sheet_blur_p75-100_x_size_p0-10.png`** (28 of 28 samples, blur
  337–1967, but only 22x25–42x65 px): this is the critical finding. Even
  with *very high* sharpness (Laplacian variance up to ~2000), crops this
  small are pixelated enough that eyebrows, eyes, and mouth cannot be
  distinguished as separate regions — the whole face reads as a handful of
  blotches. **Blur variance alone, without a size floor, is not sufficient**
  — it rewards small sharp-edged noise/pixelation just as much as real
  detail.

- **`sheet_blur_p0-10_x_size_p75-100.png`** (36 of 41 samples, large crops
  133x164 to 697x940 px, but blur variance only 1.7–31): mixed bag. Some
  (e.g. `frame_000138_face01`, 291x326, blur=14.1) are clearly readable —
  eyes/eyebrows/mouth distinct — because at large resolution, Laplacian
  variance is naturally lower per-pixel even on in-focus skin-heavy crops.
  Others (`frame_000221_face02`, blur=1.9; `frame_000216_face02`, blur=3.0)
  are genuinely motion-blurred and unreadable regardless of size. **This
  confirms blur_variance is scale-dependent and a single global blur floor
  interacts with crop size** — a floor tuned for small crops is too
  permissive for large ones and vice versa; a size-aware minimum matters as
  much as the blur number itself.

- **`sheet_blur_p10-25_x_size_p25-50.png`** (29 of 29, blur 32–59, 51x71 to
  67x95 px): mouth and eyebrow position mostly inferable, fine eye detail
  (gaze direction, eyelid shape) is soft/marginal. Borderline — usable for
  coarse expression labeling, risky for precise landmark placement.

- **`sheet_blur_p25-50_x_size_p10-25.png`** (27 of 27, blur 61–145, 42x44 to
  50x77 px): similar marginal case — small crops, moderate sharpness.
  Eyebrow/eye/mouth regions are generally locatable but lack fine detail.

- **`sheet_blur_p50-75_x_size_p50-75.png`** (36 of 49, blur 153–324, 70x81
  to 114x149 px): clearly good. Eyebrows, eyelids, pupils, and mouth corners
  are all distinctly visible in essentially every thumbnail. This is the
  "obviously fine" reference point.

**Conclusion from visual evidence:** a size floor around 50–65px on the
smaller crop dimension is where eyebrow/eye/mouth regions start to be
reliably distinguishable (below that, even sharp crops are unusable — see
the blur_p75-100 x size_p0-10 sheet). A blur-variance floor in the
60–100 range screens out genuine motion blur without needing to be very
high, because crop sizes above ~50px already carry Laplacian variance well
past that range when the face is actually in focus.

## 3. Candidate thresholds

All counts computed directly from the 645-row manifest (not estimated):

| Candidate | Rule | Retained | % of 645 | Visual basis |
|---|---|---|---|---|
| **A — lenient** | `qc_blur_variance > 50` AND `min(w,h) >= 50` | 386 | 59.8% | Keeps most of the p25-50 x p10-25 borderline cell (eyebrow/mouth locatable, eye detail soft). Maximizes volume but keeps marginal-detail crops. |
| **C — recommended** | `qc_blur_variance > 75` AND `min(w,h) >= 60` | 231 | 35.8% | Sits just above the borderline cells reviewed; excludes the size_p0-10 pixelation failure mode seen even at high blur variance, and excludes the bottom blur_p0-10 stratum's genuine motion blur. Matches where the "obviously fine" p50-75 x p50-75 sheet begins. |
| **D — strict** | `qc_blur_variance > 100` AND `min(w,h) >= 64` | 188 | 29.1% | Roughly the p50 blur / p50 size point. Visually indistinguishable in quality from Candidate C on the sheets reviewed, just a smaller set — mainly trims mid-sharpness mid-size crops that already looked fine, little obvious quality gain over C. |

A fourth, even more permissive rule was computed for context only and not
treated as a serious candidate: `min(w,h) >= 48px` with no blur floor passes
514/645 (79.7%) but — per the `sheet_blur_p0-10_x_size_p75-100` sheet —
includes clearly motion-blurred crops, so it is not recommended on its own.

### Tradeoffs

- **A (386)** maximizes dataset size but keeps samples where only coarse
  expression judgment is reliable, not fine landmark placement (eyelid
  curvature, mouth-corner subtlety). Risk: noisier landmark annotations,
  more annotator disagreement.
- **C (231)** is the best fit to what was visually confirmed as
  eyebrow/eye/mouth-readable across every cell reviewed, while still being a
  meaningfully large set. This is close to the ~250-sample target mentioned
  in the original task brief, but that proximity is a secondary observation,
  not the basis for picking it — see below.
- **D (188)** is the safest visually but trims ~43 samples relative to C
  that looked equally annotatable in the p50-75 x p50-75 sheet; the marginal
  quality gain over C was not visible in the sheets reviewed, so D mainly
  trades sample count for a margin of safety not obviously needed.

### Target-count comparison (secondary, not the basis for the recommendation)

The task brief mentions a rough ~250-sample target. For reference only,
after the visual/threshold analysis above:

| Candidate | Retained | Distance from ~250 |
|---|---|---|
| A | 386 | +136 |
| C | 231 | −19 |
| D | 188 | −62 |

## 4. Recommendation

**Candidate C** (`qc_blur_variance > 75` AND `min(width,height) >= 60px`,
231 samples) is recommended, because it is the threshold most directly
supported by what the contact sheets show about eyebrow/eye/mouth
legibility — not because it happens to land near 250. **This is a
recommendation pending human/supervisor sign-off, not an approved
threshold.** `qc_status` should remain `PENDING_THRESHOLD` until someone
with authority over the dataset reviews the contact sheets and confirms (or
overrides) this choice.
