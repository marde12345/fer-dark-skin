# Papuan V2 — Research Timeline

**Experiment/phase:** Cross-cutting (covers pre-Papuan-V2 foundation through the 2026-10-02 landmark pivot).

**Date of this report:** 2026-10-02.

**Dating method, stated explicitly per instruction:** dates below come from two different sources that should not be confused — (a) **git commit dates**, for files that are actually committed to the repository, and (b) **internal file timestamps** (`generated_at` fields inside JSON metadata, `exported_at` fields inside CSVs), for the EXP-PAP-004/papuan_v2 work, which is **untracked** in git (never committed) and therefore has no commit-date evidence at all. Where neither source gives a date, this timeline says so explicitly rather than guessing.

---

## Earlier Pipeline (pre-Papuan-V2 foundation, git-dated)

| Date (commit) | Commit | What it established |
|---|---|---|
| 2026-08-14 | `9b5d0ac` "git ignore data" | Data directories excluded from version control — explains why later `data/papuan_v2/` and `experiments/EXP-PAP-004/` content is untracked by design, not by omission. |
| 2026-08-15 | `31f5401` "labeling" | Earliest commit referencing a labeling-related change found in this history scan; exact scope not re-verified in this pass. |
| between 2026-08-15 and 2026-09-08 (exact date not re-queried) | `74caeb7` "Refactor code structure for improved readability and maintainability", `988b2cc` "refactor plan" | Codebase restructuring — exact dates uncertain, state as a range, not a point. |
| 2026-09-08 | `f9c9fae` "test: capture Phase 0 baseline pipeline outputs" | Baseline pipeline test capture — the project's own "Phase 0" framing already existed by this date. |
| 2026-09-09 | `13cafe4`, `840e0d5`, `9ae155d`, `ef3fbd9`, `ace29ec` | A cluster of same-day commits: refactor-plan execution, research-plan execution, dashboard research execution, presentation-slide image generation, and a guideline proposal — the project's general (pre-Papuan-V2) FER pipeline (face detection, cropping, CLAHE, HSEmotion, ArcFace) was substantially in place by this point, per these commit messages; this timeline does not claim exact line-level dates for each sub-component beyond what the commit messages state. |
| 2026-09-19 | `a62f0fa` "feature(dashboard): model comparison" | Added `dashboard/` (HTML/JS model-comparison demo) and `docs/DEMO_MODEL_COMPARISON.md`. |
| 2026-09-19 | `21f1108` "dataset(papuan_v2): add new dataset for papuan v2" | **Papuan V2 framing formally introduced** as a committed, named dataset entry in the repository's git history — this is the clearest single git-dated marker for "Papuan V2 begins" as a distinct research line. |

## Annotation Exploration (EXP-PAP-001 through EXP-PAP-004, internally-dated — untracked in git)

No commits exist for these files (`experiments/EXP-PAP-004/*`, `tools/papuan_v2/*` are untracked per the `.gitignore` pattern set in `9b5d0ac`). Dates below are read from each file's own internal timestamp field, which is the only evidence available:

- **EXP-PAP-001 — pilot-scale raw source pipeline** (frame extraction, face detection, CLAHE): documented narratively in `docs/EXPERIMENT.md`; produced the 645 face crops (`data/papuan_v2/faces/`) and 645 CLAHE crops (`data/papuan_v2/clahe/`). No internal timestamp found independent of EXP-PAP-002's manifest; treat as preceding EXP-PAP-002.
- **EXP-PAP-002 — pilot set construction + human-labels template:** produced the 150-image pilot subsample and `pilot_manifest.csv`. Internal evidence: `experiments/EXP-PAP-004/label_studio_metadata.json` carries `"generated_at": "2026-09-19T08:09:48Z"` for the downstream Label Studio project setup, implying EXP-PAP-002's pilot construction happened at or before this date.
- **EXP-PAP-003 — AI-assisted-annotation candidates + agreement analysis (offline comparison, not the later "paid AI-assisted annotation" instruction):** produced `ai_predictions.csv` (HSEmotion + ArcFace+LR predictions, 150×2 rows). Same 2026-09-19 window as EXP-PAP-002, per `docs/EXPERIMENT.md`'s cross-references between the two.
- **Phase 1 — annotation architecture validation (throwaway):** a separate, isolated Label Studio instance (port 8090, synthetic fixture images, separate DB/org), 20 passing tests confirming a shared Label Studio project does not leak co-annotator content before submission. Date not independently pinned beyond "before or alongside EXP-PAP-004's real pilot setup" (2026-09-19 window) — no internal timestamp field was found specifically for this validation run in this pass.
- **EXP-PAP-004 — 150-image human-annotation pilot, two-annotator isolation design:** `label_studio_metadata.json generated_at: 2026-09-19T08:09:48Z` (Project A/150-task setup); `annotator_progress.json generated_at: 2026-09-19T08:24:59Z` (overlap/progress tracking scaffold, at that point `annotator_A_completed: 1`, `annotator_B_completed: 0`).
- **Manual annotation experiment — Annotator A completion:** per this session's own direct conversation record (not a file timestamp independently re-checked here), Annotator A's full 150/150 submissions were reported complete on 2026-10-01.
- **Annotator A export and validation:** `label_studio_export.csv exported_at: 2026-10-01T21:40:09Z`; validated in this session — 150/150 rows, 150 unique images, 0 duplicates, 0 missing, exactly one annotator identity, all labels within the valid 7-class set.
- **Annotator B infrastructure stood up:** isolated server (port 8081) + project `"EXP-PAP-004 Overlap (Annotator B)"`, 75 tasks imported matching the deterministic `overlap=true` subset exactly — completed in this session, 2026-10-01/02; 0/75 annotated at time of the pivot below.
- **AI-assisted annotation investigation (emotion track):** a design review comparing three AI-pre-label workflow designs, an evaluation-leakage analysis, and a minimal provenance schema — produced in this session, 2026-10-01, in `docs/reports/PAPUAN_V2_AI_ASSISTED_ANNOTATION_DESIGN.md`. Never implemented.

## Methodological Pivot

**2026-10-02 — Supervisor clarification (Pak Fadhil):** the annotation target for the current research workflow should be facial landmarks/keypoints, not emotion labels. Reviewed-in-CVAT landmarks become training ground truth for landmark models, on two parallel branches (original face crops vs. CLAHE-preprocessed face crops), to be compared against each other.

**New direction, effective 2026-10-02:**
```text
Face detection/crop
      │
      ├─────────────────┬─────────────────┐
      ▼                 ▼
Original face       CLAHE face
      │                 │
      ▼                 ▼
Landmark             Landmark
annotation           annotation
      │                 │
      ▼                 ▼
CVAT review          CVAT review
      │                 │
      ▼                 ▼
Reviewed GT          Reviewed GT
      │                 │
      ▼                 ▼
Training             Training
      │                 │
      ▼                 ▼
Original model      CLAHE model
                 │
                 ▼
     Original vs. CLAHE comparison
```

Full detail, risk analysis, and audit evidence for this pivot: `docs/reports/PAPUAN_V2_METHODOLOGY_PIVOT_2026-10-02.md`.

**A relevant pre-existing fact surfaced only during this pivot's audit, not before:** a MediaPipe-based landmark extraction pipeline (`src/fer_dataset/pipeline/landmark_analyzer.py`) already existed in the codebase prior to the Papuan V2 framing, and had already been run against 85 of the 645 Papuan V2 face crops (including 20 of the 150 pilot images) for an unrelated purpose (geometric emotion-proxy features). This predates and is independent of the pivot decision itself, but is directly relevant to implementing it.

---

*This timeline will be appended to, not rewritten, as the project progresses — per the project's standing instruction to preserve chronological history rather than overwrite it. No code, dataset, or configuration was modified in producing this report.*
