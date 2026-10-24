# Papuan V2 — CVAT Landmark Label Schema (EXP-PAP-005)

## 1. Why Generic pt0...pt67 Was Insufficient

The original CVAT skeleton (Section 9 of `PAPUAN_V2_CVAT_LANDMARK_PILOT.md`) used bare index names `pt0`...`pt67`. On visual inspection in the CVAT UI, a human reviewer has no way to tell which anatomical feature any given point represents without cross-referencing an external index table — making correction decisions ("is this point in the right place?") much harder than necessary. This report replaces those names with meaningful anatomical labels while preserving the exact underlying landmark identity.

## 2. Exact InsightFace Model/Source Used

`insightface` package version `1.0.1` (confirmed via `insightface.__version__` in this project's `.venv`), model `landmark_3d_68` (`insightface/model_zoo/landmark.py`, class `Landmark`), part of the `buffalo_l` bundle, backed by the ONNX file `1k3d68.onnx`. The model's own code (`landmark.py`) determines `lmk_dim=3, lmk_num=68` purely from its output tensor shape (3309 = 68×3×... channels) and sets `self.taskname = 'landmark_3d_68'` — this is the exact model this project's pilot used, not a different/newer InsightFace landmark model.

For pose estimation, the same code loads a bundled reference template via `get_object('meanshape_68.pkl')` — this mean-shape (a `(68, 3)` canonical face template) was used in this investigation purely as a **geometric reference** to verify point semantics, not as training data or a prediction source.

## 3. Verified Index → Anatomical Mapping

**Verification method (not an assumption):**
1. Dumped the full `(68, 3)` mean-shape template and inspected x/y values for every one of the 68 points — confirmed symmetric extremes (point 0 and point 16 at x≈∓0.627), monotonic sweeps within each facial region (e.g. nose bridge points 27→30 have monotonically increasing y), and clear corner/center points (nose tip at point 33, x≈0).
2. **Empirically cross-checked against real pixel output**, not just the abstract mean-shape: across 5 real pilot images, the point-36-to-41 group consistently has *smaller* pixel-x than the point-42-to-47 group (e.g. for `frame_000009_face04`: group 36–41 mean x=18.1px vs. group 42–47 mean x=31.0px, out of a 64px-wide crop) — confirming the mean-shape's left/right sign convention carries through to this project's actual real-image predictions, not just to an abstract template.
3. Confirmed the **region sizes exactly match** the well-documented ibug-300W/dlib 68-point convention: jaw (17 pts, indices 0–16), eyebrows (5+5, 17–26), nose (4+5, 27–35), eyes (6+6, 36–47), mouth (12+8, 48–67) — this structural match, combined with (1) and (2), is what justifies applying that convention's semantic names here rather than inventing a new scheme.

**Resulting mapping** (full 68-entry table; "right"/"left" per Section 4):

| Region | Indices | Notes |
|---|---|---|
| Jaw | 0–16 | Continuous curve crossing the midline; named `jaw_0`...`jaw_16` only (no left/right/corner claim per-point, since the jaw line itself doesn't split cleanly — this follows the task's own stated preference for `<region>_<index>` where finer semantics aren't independently verifiable). |
| Right eyebrow | 17–21 | `right_eyebrow_outer`(17) → `right_eyebrow_inner`(21); outer/inner verified by monotonic \|x\| moving toward 0. |
| Left eyebrow | 22–26 | `left_eyebrow_inner`(22) → `left_eyebrow_outer`(26); mirror of the above. |
| Nose bridge | 27–30 | `nose_bridge_top`(27) → `nose_bridge_bottom`(30); verified by monotonic y. |
| Nose bottom | 31–35 | `nose_bottom_right`(31), `..._right_inner`(32), `nose_tip`(33, x≈0 center — the one point in this group confidently namable beyond region+index), `..._left_inner`(34), `nose_bottom_left`(35). |
| Right eye | 36–41 | `right_eye_outer_corner`(36), `_top_outer`(37), `_top_inner`(38), `right_eye_inner_corner`(39), `_bottom_inner`(40), `_bottom_outer`(41) — corners verified by \|x\| extremes; top/bottom assigned by y-sign (upper lid = more negative y in the mean-shape, i.e. higher up). |
| Left eye | 42–47 | Mirror of the above: `left_eye_inner_corner`(42) → `left_eye_outer_corner`(45), with top/bottom-outer/inner by the same logic. |
| Mouth outer | 48–59 | `mouth_outer_right_corner`(48), `mouth_outer_left_corner`(54) — corners verified by x extremes within the group; the 10 points between them are named `mouth_outer_upper_1..4`/`mouth_outer_upper_center`(51) and `mouth_outer_lower_1..4`/`mouth_outer_lower_center`(57) — center points verified by extreme y within their half (topmost/bottommost), the numbered interior points are **not** independently claimed as "left peak" vs. "right peak" beyond that ordering, per the task's own caution against unverifiable semantics. |
| Mouth inner | 60–67 | `mouth_inner_right_corner`(60), `mouth_inner_left_corner`(64), `mouth_inner_upper_center`(62), `mouth_inner_lower_center`(66), remaining 4 as `mouth_inner_upper_1/2`, `mouth_inner_lower_1/2`. |

Full index-by-index table (all 68), as actually applied in CVAT:

```
0  jaw_0                      17 right_eyebrow_outer        34 nose_bottom_left_inner    51 mouth_outer_upper_center
1  jaw_1                      18 right_eyebrow_1            35 nose_bottom_left          52 mouth_outer_upper_3
2  jaw_2                      19 right_eyebrow_2            36 right_eye_outer_corner     53 mouth_outer_upper_4
3  jaw_3                      20 right_eyebrow_3            37 right_eye_top_outer        54 mouth_outer_left_corner
4  jaw_4                      21 right_eyebrow_inner        38 right_eye_top_inner        55 mouth_outer_lower_1
5  jaw_5                      22 left_eyebrow_inner         39 right_eye_inner_corner     56 mouth_outer_lower_2
6  jaw_6                      23 left_eyebrow_1             40 right_eye_bottom_inner     57 mouth_outer_lower_center
7  jaw_7                      24 left_eyebrow_2             41 right_eye_bottom_outer     58 mouth_outer_lower_3
8  jaw_8                      25 left_eyebrow_3             42 left_eye_inner_corner      59 mouth_outer_lower_4
9  jaw_9                      26 left_eyebrow_outer         43 left_eye_top_inner         60 mouth_inner_right_corner
10 jaw_10                     27 nose_bridge_top            44 left_eye_top_outer         61 mouth_inner_upper_1
11 jaw_11                     28 nose_bridge_1              45 left_eye_outer_corner      62 mouth_inner_upper_center
12 jaw_12                     29 nose_bridge_2              46 left_eye_bottom_outer      63 mouth_inner_upper_2
13 jaw_13                     30 nose_bridge_bottom         47 left_eye_bottom_inner      64 mouth_inner_left_corner
14 jaw_14                     31 nose_bottom_right          48 mouth_outer_right_corner   65 mouth_inner_lower_1
15 jaw_15                     32 nose_bottom_right_inner    49 mouth_outer_upper_1        66 mouth_inner_lower_center
16 jaw_16                     33 nose_tip                   50 mouth_outer_upper_2        67 mouth_inner_lower_2
```

**Confidence level, stated honestly:** HIGH for corners, tips, chin, and region boundaries (geometrically verified via monotonicity/symmetry, cross-checked against real pixel data). MODERATE for the specific "upper_1 vs upper_2" style interior-point distinctions (ordering is verified; the precise anatomical micro-role of each is inferred from the well-documented ibug-300W convention matching this model's exact structure, not independently re-derived point-by-point from a visual render). No name was assigned where this project could not verify at least the ordering/extremity claim.

## 4. Subject-vs-Image Left/Right Convention

**"right"/"left" in all names refer to the subject's own anatomical right/left, not image-space left/right.** This was explicitly verified, not assumed:
- The mean-shape's x<0 group (indices 0–7ish/17–21/36–41) was empirically confirmed to land at **smaller pixel-x values** (i.e., the **left side of the image**) across 5 real sample images (Section 3, point 2).
- Under the standard, unmirrored frontal-camera convention (a subject facing the camera has their anatomical right side appear on the image's left side — the same reason a mirror-less photo of someone raising their right hand shows the raised hand on the photo's left), this x<0/image-left group corresponds to the subject's **anatomical right** — matching the well-documented ibug-300W naming where indices 17–21 are called the "right eyebrow" in exactly this anatomical sense.
- **Caveat, stated explicitly:** this relies on the assumption that the source video/frames are not mirror-flipped (e.g. not processed as a "selfie" mirror view). This project's pipeline documentation gives no indication of mirroring, but this was not independently re-confirmed against raw camera/capture metadata — if the source frames ever turn out to be mirrored, every "right"/"left" label in this schema would need to be swapped (the point *indices* and *coordinates* would remain completely unaffected either way, since this is purely a naming-convention question, not a data question).

## 5. CVAT Implementation

Labels were updated via `PATCH /api/labels/{parent_label_id}` with a `sublabels` payload containing each sublabel's existing `id` and its new `name` — **critically, by `id`, never by recreating or reordering sublabels.** CVAT's API explicitly rejected a naive `PATCH /api/labels/{sublabel_id}` with just `{"name": ...}` ("Sublabels cannot be modified this way") — the correct, documented mechanism is a single PATCH on the parent skeleton label carrying the full sublabel list with IDs preserved. This was tested first on a single point (`pt0` → `jaw_0_TEST`), verified safe (annotation intact, coordinate unchanged), then reverted and applied to all 68 points in one batch PATCH.

**A real pitfall found and corrected during this work:** CVAT's `GET /api/tasks/{id}/annotations` response's `elements` array for each skeleton shape is **not** ordered by point index — it's an unordered list of `{label_id, points, ...}` objects. The elements array's first entry for one frame was found to be `label_id=47` (`pt45`), not `pt0`. All verification and any future export/analysis code **must join by `label_id` → sublabel name, never by array position** — this is documented here explicitly so it isn't rediscovered the hard way later.

## 6. Coordinate Preservation Validation

Full validation performed (not spot-checked only):
- Snapshotted all 24 frames' full 68-point state (joined by `label_id`) **before** the rename.
- Applied the batch rename.
- Re-fetched all 24 frames' annotations **after** the rename, re-joined by `label_id` → new name.
- Compared all **1,632 points** (24 images × 68 points) against the original source prediction file `experiments/EXP-PAP-005/insightface_68pt_pilot_predictions.json`.
- **Result: 0 mismatches.** Every single coordinate is bit-for-bit (within floating-point tolerance 0.01px) identical to the original InsightFace output.

## 7. Annotation Preservation Validation

- 24 shapes present after the rename (same as before — none lost, none duplicated).
- Every shape has exactly 68 elements (no missing points).
- All 68 `label_id`s per shape are unique (no duplicate points).
- All 68 new names are unique across the label set (`len(set(names)) == 68`, verified programmatically) — no naming collision was introduced.
- All 24 frame indices 0–23 are present with no gaps.

## 8. CVAT Limitations Found

- Sublabel names cannot be PATCHed individually by sublabel ID — only via the parent (skeleton) label's full `sublabels` payload, which must include every sublabel's `id` to avoid accidentally creating new sublabels or losing existing ones.
- The annotations API's `elements` array has no guaranteed order — any code reading per-point data must join by `label_id`, not position (Section 5).

Neither limitation required a destructive workaround or task recreation — both were handled by using CVAT's documented (if slightly non-obvious) correct API pattern.

## 9. Changes Made

- Renamed all 68 skeleton sublabels on CVAT task id 1 (`EXP-PAP-005...`) from `pt0`...`pt67` to the anatomical names in Section 3, via `PATCH /api/labels/1` (parent label id 1, "face68").
- Added `docs/reports/PAPUAN_V2_CVAT_LANDMARK_LABEL_SCHEMA.md` (this report).
- Appended updates to `docs/reports/PAPUAN_V2_CURRENT_STATE.md` and `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`.

## 10. Changes NOT Made

No landmark coordinates were changed (verified, Section 6). No change to the 68-point ordering/index identity (index N still means the same InsightFace landmark N, Section 6). No images, predictions, or the dataset were regenerated. No human review was started. No points were manually moved. The existing CVAT task was **not** recreated or deleted — the rename was applied safely in-place. Label Studio, the old emotion experiment, MediaPipe/InsightFace 5-point infrastructure, and model training were all untouched. No commit or push was performed.

## 11. Current Status

CVAT task id 1 now shows 68 human-readable anatomical labels instead of `pt0`...`pt67`, with every underlying coordinate, point index, and image unchanged from the validated pilot state. Ready for human review.

## 12. Next Step

Open `http://localhost:8070`, review the task — labels should now read e.g. `right_eye_outer_corner`, `nose_tip`, `mouth_outer_left_corner` instead of `pt36`, `pt33`, `pt54` — and begin the human review pass per the procedure already documented in `PAPUAN_V2_CVAT_LANDMARK_PILOT.md` Section 11.

---

*Label-naming update only. No coordinates, point identity, images, or task structure were altered beyond the sublabel names themselves.*

---

## 13. [Update] Abbreviated Label Names

**Why:** the full anatomical names (`right_eye_outer_corner`, `mouth_outer_upper_center`, etc.) made the CVAT canvas visually crowded during actual human review — overlapping on-canvas text labels across 68 closely-packed points on small (58–284px) crops. The reviewer requested shorter names.

**New scheme:** same 68 indices, same semantics, abbreviated per-region prefix + sequential number — index identity unchanged, only the displayed string is shorter:

```
j0..j16     jaw (17)                    re0..re5   right eye (36-41)
rb0..rb4    right eyebrow (17-21)       le0..le5   left eye (42-47)
lb0..lb4    left eyebrow (22-26)        mo0..mo11  mouth outer (48-59)
nb0..nb3    nose bridge (27-30)         mi0..mi7   mouth inner (60-67)
ns0..ns4    nose base (31-35, ns2=tip)
```

The descriptive outer/inner/corner/tip suffixes from the long-form names (Section 3) are dropped for brevity; **the long-form mapping in Section 3 remains the authoritative semantic reference** — cross-reference by index (e.g. `re0` = index 36 = `right_eye_outer_corner`).

**Applied via the same mechanism validated in Section 5** (parent-label PATCH, by sublabel `id`, not name). **Validation performed against a pre-rename snapshot of the live task state** (not just the original AI predictions), since human review was already in progress — confirmed all 1,632 points (24 images × 68 points) and all `occluded`/`outside` flags identical before and after the rename. Zero data loss, including any corrections already made during review.

**Current status:** this abbreviated scheme is now live in CVAT task id 1 and is the naming convention in effect for ongoing human review.

---

## 14. [Update] Clearer Abbreviations (v2) — Side/Detail-Encoded

**Why:** the v1 abbreviations (Section 13, plain `region+index` like `ns0`..`ns4`) were shorter but lost the side/detail information the full names carried — the reviewer couldn't tell left from right nose points at a glance. Requested clearer abbreviations, with `nsli` (nose, left, inner) given as the example.

**New scheme**, same 68 indices/semantics as Sections 3 and 13, now encoding side (`r`/`l`) and detail (inner/outer/top/bottom/corner/tip) where Section 3 verified it:

```
j0..j16                     jaw (no side split, continuous curve)
rbo,rb1,rb2,rb3,rbi         right eyebrow: outer->inner (17-21)
lbi,lb1,lb2,lb3,lbo         left eyebrow: inner->outer (22-26)
nbt,nb1,nb2,nbb             nose bridge: top->bottom (27-30)
nsro,nsri,nst,nsli,nslo     nose base: right-outer, right-inner, tip, left-inner, left-outer (31-35)
reoc,reto,reti,reic,reli,relo   right eye: outer corner->top->inner corner->bottom (36-41)
leic,leti,leto,leoc,lelo,leli   left eye: inner corner->top->outer corner->bottom (42-47)
morc,mou1-4,mouc,molc       mouth outer upper half: right corner, upper x4 (mouc=upper center), left corner (48-54)
mod1-4,modc                 mouth outer lower half: lower x4 (modc=lower center) (55-59)
mirc,miu1,miuc,miu2,milc    mouth inner upper half: right corner, upper x2 (miuc=center), left corner (60-64)
mid1,midc,mid2              mouth inner lower half (65-67)
```

**Applied and validated the same way as Section 13** — snapshot of the live task immediately before the rename, batch PATCH by sublabel `id`, full comparison after. **Result:** 1,622 of 1,632 points identical to the pre-rename snapshot (the rename itself changed zero coordinates, as expected); the other 10 (all of both eyebrows, on one frame) differed because the reviewer was actively correcting that region in CVAT in the same window — confirmed by the task's `updated_date` advancing between the snapshot and the check, and by the changed points forming a complete, coherent anatomical region rather than a random scatter. That correction was preserved correctly, not lost.

**Current status:** this v2 scheme is now live in CVAT task id 1 and is the naming convention in effect for ongoing human review, superseding the Section 13 v1 scheme.
