# Papuan V2 — CVAT Landmark Pilot (EXP-PAP-005)

## 1. Objective

Prove the smallest possible end-to-end workflow: InsightFace 68-point prediction → CVAT import → human correction → export → validation → reusable ground truth, on a small (24-image) pilot, without yet scaling to all 645 images, annotating CLAHE independently, or training a model.

## 2. Confirmed Methodology (final, per user/supervisor decision)

1. **Landmark schema:** exactly 68 points, from InsightFace's `landmark_3d_68` sub-model (already installed, previously unloaded). MediaPipe 468/478-point and InsightFace 5-point infrastructure remain in the repo as historical/exploratory, not used for the primary target.
2. **Annotation image:** Original face crops only. CLAHE crops are not independently annotated.
3. **Initial annotation:** InsightFace 68-point predictions imported as initial proposals; human reviews and corrects in CVAT. Workflow: Original crop → InsightFace prediction → CVAT → human review → correction where needed → final reviewed annotation. Documented explicitly as **"InsightFace-initialized, human-reviewed landmark annotations"** — not fully independent human-from-scratch annotation.
4. **CLAHE:** no independent annotation pass; the Original image's final reviewed coordinates are reused unchanged as the CLAHE training target, since CLAHE was verified (prior audit) to be a pure per-pixel lightness transform with no geometric change.
5. **Primary comparison:** Model A (Original → 68pt landmark model) vs. Model B (CLAHE → 68pt landmark model), both trained against the *same* ground-truth coordinates — an intentional, documented design choice.

## 3. Branch Confirmation

All work in this task was performed with the FER-Dataset repository's `main` branch as the target for persisted artifacts (verified via `git branch --show-current` → `main`). `worktree-papuan-v2-audit` was not used or modified. CVAT itself and its supporting Docker/colima infrastructure live outside the git repository (a separate Docker Compose checkout under a job-scoped temp directory, plus a local container runtime) and are not part of any git branch.

## 4. Dataset Subset Selected

**24 images**, deterministically sampled with `random.Random(200).sample(sorted(image_ids), 24)` over the existing 150-image `experiments/EXP-PAP-004/pilot_manifest.csv` image_id list. Seed 200 is distinct from both pre-existing seeds in this project (42: original 150-image pilot sampling; 100: the Annotator-B 75-image overlap subset), so this pilot draws from, but does not collide with, either prior sampling decision.

Selected image_ids (sorted): `frame_000009_face04, frame_000010_face05, frame_000012_face10, frame_000015_face04, frame_000022_face11, frame_000041_face03, frame_000049_face04, frame_000054_face05, frame_000069_face02, frame_000078_face01, frame_000120_face01, frame_000123_face02, frame_000136_face04, frame_000139_face04, frame_000172_face02, frame_000184_face02, frame_000186_face01, frame_000199_face01, frame_000226_face03, frame_000227_face04, frame_000242_face02, frame_000242_face06, frame_000248_face13, frame_000249_face07`.

All 24 images confirmed present in both `data/papuan_v2/faces/` (original, used for annotation) and `data/papuan_v2/clahe/` (CLAHE, confirmed present but not independently annotated per the confirmed methodology).

## 5. Why This Subset Was Selected

Reuses the already-curated, already-lineage-tracked 150-image EXP-PAP-004 pilot set rather than drawing a fresh sample from the full 645-image pool — this avoids introducing a second, incompatible sampling decision and keeps this pilot traceable through existing manifest/lineage files. 24 (~16% of the 150-image pilot, ~3.7% of the full 645-image set) is small enough to validate the mechanical workflow quickly without committing significant human-review time before the schema/workflow are confirmed to work end-to-end.

## 6. 68-Point Landmark Schema

InsightFace's `landmark_3d_68` sub-model, part of the already-installed `buffalo_l` bundle (previously excluded via `allowed_modules` in this repo's existing ArcFace embedding code — now additionally loaded for this pilot, no new package dependency). Output is `(68, 3)` (x, y, z); **only x, y were used** — the z-coordinate is discarded, since CVAT's 2D point/skeleton annotation and this project's 2D pixel-coordinate convention (matching the existing MediaPipe landmark code's convention) have no use for a third dimension here.

Coordinates are **pixel, crop-relative** — consistent with the existing MediaPipe landmark code's own convention (`landmark_analyzer.py`), so this project now has one consistent coordinate convention across both its historical (MediaPipe) and current (InsightFace) landmark infrastructure.

## 7. Landmark Semantic/Index Mapping

Verified (not assumed) via two independent checks:
- **Source inspection:** `insightface/model_zoo/landmark.py` confirms `lmk_dim=3, lmk_num=68, taskname='landmark_3d_68'`, loaded from a bundled `meanshape_68.pkl` mean-shape template.
- **Geometric inspection of the actual mean-shape coordinates:** point 0 (x≈−0.627) and point 16 (x≈+0.627) are symmetric at the horizontal extremes — consistent with jawline endpoints; point 8 (x≈0, y at the maximum) is bottom-center — consistent with the chin tip; points 27/33 are horizontally centered — consistent with the nose bridge/base; points 36 and 48 are off-center in the expected eye-corner/mouth-corner positions.

This matches the standard iBUG-300W/dlib 68-point convention point-for-point on every index spot-checked:
- **0–16:** jawline
- **17–21:** right eyebrow
- **22–26:** left eyebrow
- **27–35:** nose (bridge + base)
- **36–41:** right eye (including outer/inner corners)
- **42–47:** left eye (including outer/inner corners)
- **48–67:** mouth (outer + inner lip contour, including corners)

**Confidence level, stated honestly:** HIGH but not 100% officially certified — no InsightFace model card or source comment explicitly names this "iBUG-300W"; this is strong circumstantial confirmation from the mean-shape geometry itself, not an official vendor statement. If exact per-point semantics ever become load-bearing for a specific analysis (e.g. "point 48 is definitely the right mouth corner"), a direct visual overlay check against a real face image is recommended before relying on it further.

The CVAT skeleton preserves this ordering consistently: each of the 68 sublabels is named `pt0`...`pt67` and mapped 1:1 to the InsightFace output index at creation time (verified in Section 9/13).

## 8. InsightFace Proposal Generation

For each of the 24 selected Original face crops, `insightface.app.FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark_3d_68"])` was run to extract the 68-point array. **A real bug was found and fixed, mirroring an already-documented issue in this repo:** the naive approach (letting `FaceAnalysis.get()` re-run SCRFD face detection on the already-cropped image) failed on 22 of 24 images with "no face detected" — the crops are too tight/small (as small as 52×73px) for SCRFD's own detector to reliably re-find a face inside an already-cropped face image. This is the *exact same failure mode* already documented in this repository for the ArcFace embedding pipeline (`docs/EXPERIMENT.md`, "re-detection... failed on 50/150"). Fixed identically: skip re-detection, construct a synthetic full-crop bounding box (`Face(bbox=[0,0,w,h], ...)`, since the crop already *is* the face), and call the `landmark_3d_68` model's `.get(img, face)` directly. Result: **24/24 succeeded, 0 failures** after the fix.

Output saved (and now persisted in-repo, see Section 19) as `experiments/EXP-PAP-005/insightface_68pt_pilot_predictions.json`, keyed by `image_id`, each entry: `{image_id, crop_width, crop_height, landmark_schema: "insightface_landmark_3d_68", landmarks_xy: [[x,y]×68]}`.

## 9. CVAT Setup

**Deployment:** local, self-hosted CVAT via its own official Docker Compose configuration (`cvat-ai/cvat`, shallow-cloned at HEAD, `dev` image tags — no release tag pinned for this pilot). Running under **colima** (a lightweight, CLI-only container runtime — chosen over Docker Desktop specifically to avoid installing a GUI app for what is a server-only use case), installed fresh via Homebrew since no container runtime existed on this machine beforehand.

**Resource note, documented as an implementation lesson:** the first colima VM (2 CPU / 4GB) was badly undersized for CVAT's ~17-container stack running under amd64-on-arm64 emulation — it thrashed (load average 134 on 2 CPUs, memory exhausted) and made the server's own startup migrations appear to hang for over 20 minutes. Resizing to 6 CPU / 10GB (well within this machine's 10-CPU/16GB capacity) fixed this immediately — the same already-pulled containers restarted and became healthy within about a minute.

**Port conflict, found and fixed:** CVAT's docker-compose defaults its reverse-proxy (traefik) to host port 8080 — the same port already in use by this project's own Annotator A Label Studio server (left running from an earlier task in this session, per the explicit instruction not to modify it). The symptom was subtle: `curl http://localhost:8080/...` returned a *plausible-looking* 404 page, but it was Label Studio's own 404 page, not CVAT's — traefik's port bind silently lost to the already-listening Label Studio process. **Fixed by remapping CVAT's exposed ports** in the cloned (non-repo) docker-compose.yml from `8080:8080`/`8090:8090` to `8070:8080`/`8091:8090`, leaving Label Studio's ports completely untouched. CVAT is now reachable at `http://localhost:8070`.

**CVAT version running:** 2.77.1 (per `/api/server/about`).

## 10. Annotation Workflow

```text
Original face crop (data/papuan_v2/faces/<image_id>.jpg)
      │
      ▼
InsightFace landmark_3d_68 prediction (68 points, pixel, crop-relative)
      │
      ▼
CVAT task "EXP-PAP-005 Facial Landmark Pilot (InsightFace-initialized, human-reviewed)"
(task id 1, label "face68": a skeleton with 68 point sublabels pt0..pt67,
 imported as the initial annotation for each of the 24 frames)
      │
      ▼
Human review (not yet performed — this report stops before that step)
      │
      ▼
Final reviewed landmark annotation (becomes ground truth once reviewed)
```

## 11. Human Review Procedure (as configured, not yet executed)

A single human reviewer opens the CVAT task, reviews each of the 24 images' pre-filled 68-point skeleton. If a point is correctly placed, it is left unchanged. If incorrect or missing, the reviewer drags it to the correct anatomical location (per the confirmed methodology's explicit instruction). No multi-user review architecture was built — this pilot intentionally has exactly one reviewer, per the task's own "do not create a complicated multi-user annotation architecture yet" instruction.

## 12. Provenance Model

Recorded at the task/metadata level rather than as a new per-point CVAT field (CVAT's native schema has no built-in "review_status" column, and adding one would require a custom CVAT ML-backend/attribute scheme — out of scope for "do not overengineer"):
- **Task name** explicitly states `"(InsightFace-initialized, human-reviewed)"` — visible to anyone opening the CVAT project.
- **`experiments/EXP-PAP-005/metadata.json`** (in-repo) records `source: "insightface"`, `review_status: "ai_initialized_pending_human_review"` (to be updated to a reviewed status once the human pass is done), `landmark_schema`, `cvat_task_id`, and the sampling seed/lineage.
- **CVAT's own annotation `source` field** is set to `"manual"` on import per CVAT's API convention (this is CVAT's own schema term for "this coordinate exists as a concrete annotation," not a claim about who authored it) — the actual authorship distinction (AI-initialized vs. human-corrected) lives in the task name and metadata.json above, not in this field.
- **Image_id lineage preserved:** CVAT's internal frame order (lexicographic, verified identical to the sorted `image_ids` list used for the predictions) is the join key back to `pilot_manifest.csv`'s `image_id`, `original_image_path` (`data/papuan_v2/faces/<image_id>.jpg`), and `clahe_image_path` (`data/papuan_v2/clahe/<image_id>.jpg`) — no second, incompatible ID system was introduced.

## 13. QC Validation

`experiments/EXP-PAP-005/qc_validate_pilot_landmarks.py` (minimal checks only, per task scope) — run against the InsightFace prediction file before CVAT import:

```
Total predictions: 24
Unique image_ids: 24
Errors: 0
Warnings (out-of-bounds, non-fatal): 5
  (all 5 are jaw/ear-adjacent points on one tightly-cropped image, frame_000123_face02,
   slightly outside its 133×284 crop bounds — expected behavior for a model predicting
   near a tight crop's edge, not a data-integrity failure)

PASS
```

Additionally verified directly against the live CVAT task via API (Section 9's task, confirmed post-import):
- 24 skeleton shapes exist, one per frame, covering frames 0–23 with no gaps.
- Every skeleton shape has exactly 68 `elements` (points) — no missing, no duplicate indices.
- Spot-checked coordinate values match the source prediction file exactly (e.g. frame 0's first point: `[34.68, 34.19]`, matching the JSON source).

All pilot images have an annotation; all annotations map back to a known `image_id` (verified via the lexicographic frame-order check in Section 9).

## 14. Original → CLAHE Coordinate Reuse

Not yet executed as a concrete transformation step in this pilot (the task explicitly scoped this pilot to the Original-branch workflow only, stopping before human review). Per the confirmed methodology and the prior audit's verified fact (CLAHE is a pure per-pixel lightness transform, zero geometric change), the mechanism when needed is the identity mapping: `clahe_target[image_id] = original_annotation[image_id]`, no coordinate math. **No duplicate annotation file was created for CLAHE** — per the task's explicit "prefer a single canonical annotation source with preprocessing metadata rather than maintaining two independent annotation files" instruction, the plan is for `experiments/EXP-PAP-005/metadata.json`-style records to carry a `preprocessing` field distinguishing which training input (Original pixels vs. CLAHE pixels) a given model run used, while both point at the one canonical landmark coordinate source.

## 15. Pilot Results

- 24/24 InsightFace predictions generated successfully (after the SCRFD re-detection bugfix).
- 24/24 QC validation passed (0 errors, 5 minor non-fatal out-of-bounds warnings).
- 24/24 images successfully uploaded into CVAT task id 1.
- 24/24 skeleton annotations (68 points each) successfully imported as initial proposals, verified via direct API inspection.
- **Human review has not yet been performed** — this report stops at "ready for human review," per the task's explicit scope.

## 16. Problems Encountered

1. **No container runtime pre-installed** — required installing colima + Docker CLI + docker-compose via Homebrew (user explicitly confirmed this was acceptable before proceeding).
2. **Undersized VM caused apparent hang** — 2 CPU/4GB colima VM thrashed under CVAT's ~17-container stack running emulated amd64-on-arm64; resized to 6 CPU/10GB, which resolved it within about a minute of restart.
3. **Port collision with Label Studio** — CVAT's default port 8080 collided with the already-running Annotator A Label Studio server; the symptom (a plausible-but-wrong 404 page) delayed diagnosis. Fixed by remapping CVAT's own ports to 8070/8091 in its own (non-repo) docker-compose.yml, leaving Label Studio fully untouched.
4. **SCRFD re-detection failure on tight crops** — 22/24 images failed naive InsightFace landmark extraction; fixed using the same synthetic-bbox workaround already established in this repo for an identical ArcFace-pipeline bug.
5. **No `requests` package in the ambient Python** — resolved by using the repository's own `.venv` (which already has it as a dependency), rather than installing a new package globally.

## 17. Changes Made

- Installed: `colima`, `docker` (CLI), `docker-compose` via Homebrew (system-level, outside the repo); a CVAT Docker Compose checkout (`cvat-ai/cvat`, shallow clone) under a job-scoped temp directory, **not inside this git repository**.
- Started: a colima VM (6 CPU/10GB) and CVAT's ~17-container stack, now running locally at `http://localhost:8070` (CVAT admin: username `admin`, password set during this session — not recorded in any repo file or this report).
- Created: CVAT task id 1 ("EXP-PAP-005 Facial Landmark Pilot...") with a 68-point skeleton label, 24 imported images, 24 imported skeleton annotations (InsightFace-initialized).
- Added to the repository: `experiments/EXP-PAP-005/metadata.json`, `experiments/EXP-PAP-005/insightface_68pt_pilot_predictions.json`, `experiments/EXP-PAP-005/qc_validate_pilot_landmarks.py`, `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md` (this report), plus appended updates to `docs/reports/PAPUAN_V2_CURRENT_STATE.md` and `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`.
- CVAT's own docker-compose.yml (in its temp-directory clone, outside this repo) was edited to change its exposed host ports from 8080/8090 to 8070/8091.

## 18. Changes NOT Made

No model training. No annotation of all 645 images (only the 24-image pilot). No CLAHE images independently annotated. No modification to the old Label Studio emotion experiment (Annotator A's server/project/data were never touched; the only interaction was discovering and avoiding its port). No deletion of MediaPipe or InsightFace 5-point infrastructure (both remain exactly as they were). No deletion of historical reports (only appends). No unnecessary dependencies installed beyond what CVAT's deployment itself required (no new Python packages added to the repo's own dependency files — `requests` was already present in `.venv`). No unrelated code refactored. No git commit or push performed on the FER-Dataset repository as part of this task (per the standing "do not commit or push automatically" rule).

## 19. Remaining Blockers

None blocking the next step (human review can begin immediately — CVAT is live and the task is populated). Noted for awareness, not blocking: the CVAT admin password and this session's container/VM state live only on this machine and this session's memory — they are not written to any repo file, so continuity across a machine restart would require re-establishing credentials (not a data-loss risk, since the actual annotation data lives in CVAT's own Docker volumes, which persist across container restarts as already demonstrated when the VM was resized).

## 20. Next Step

Open `http://localhost:8070`, log in as `admin`, open task "EXP-PAP-005 Facial Landmark Pilot (InsightFace-initialized, human-reviewed)", and perform the human review pass on the 24 pre-filled skeletons (leave correct points unchanged, drag incorrect ones to the correct anatomical location), per Section 11's procedure. After review, export annotations from CVAT and compare against the source InsightFace predictions to produce the first real "human-reviewed" vs. "AI-proposed" acceptance/correction-rate statistic discussed in the earlier methodology design review.

## 21. Date/Time

2026-10-02.

## 22. Git Status

Branch: `main`. New/modified paths at the time of writing this report: `experiments/EXP-PAP-005/` (new directory, 3 files), `docs/reports/PAPUAN_V2_CVAT_LANDMARK_PILOT.md` (new), `docs/reports/PAPUAN_V2_CURRENT_STATE.md` (appended), `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md` (appended). All uncommitted, per the standing "do not commit or push automatically" instruction. No other repository files were touched.

---

*Pilot implementation report. No model training, full-dataset annotation, or CLAHE-independent annotation was performed.*
