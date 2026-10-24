# Research Timeline — Reconstructed

**Evidence basis.** This reconstruction is built from: (a) the full commit history of the `main` branch (15 commits, 2026-08-14 to 2026-10-02 — all dates as recorded by the repository's own clock, not independently verified against a calendar), (b) the internal documents each commit introduced or modified, and (c) a direct, repository-wide search for the content described in the task's background context. It is **not** built from any Claude conversation export or external chat log — none was found in the workspace. Where internal documents themselves record a self-correction (e.g., "this earlier claim was wrong"), that correction is preserved here as part of the history, not silently resolved.

**Evidence classification used throughout:** Verified / Corroborated / Provisional / Unresolved / Unverifiable (see `DATA_DISCREPANCIES.md` for the full definitions).

---

## Stage 0 — Repository Initialization (2026-08-14)

- `9b5d0ac` "git ignore data" — `data/` excluded from version control. **Implication:** no raw video, frames, or face-crop images are, or ever have been, committed to this repository; all dataset artifacts referenced below are described from documentation/CSV/report files, not from inspecting the images themselves. **Verified** (commit exists; implication is a direct consequence of the `.gitignore` change).

## Stage 1 — Early Pipeline / Labeling Work (2026-08-15)

- `31f5401` "labeling", `74caeb7` "Refactor code structure for improved readability and maintainability". These are the earliest substantive code commits found. No experiment-registry-style document exists this far back; the FER pipeline's shape at this point cannot be reconstructed beyond "labeling and refactoring work occurred." **Unverifiable in detail** — no commit-level diff of model choices was reviewed in this pass (would require a line-by-line `git show` of each commit, not performed here as it falls outside the current evidence-gathering budget; flagged as a gap, not glossed over).

## Stage 2 — Phase 0 Baseline Capture (2026-09-08)

- `988b2cc` "refactor plan", `f9c9fae` "test: capture Phase 0 baseline pipeline outputs". This is the first point with an explicit "Phase 0 baseline" framing in a commit message, suggesting a planned, staged research process was already in place by this date. **Provisional**: the existence of a "Phase 0" implies a numbered phase plan, but the plan document itself was not located and inspected line-by-line in this pass.

## Stage 3 — Concentrated Research-Infrastructure Day (2026-09-09)

Five commits land the same day: `13cafe4` "refactor plan execution", `840e0d5` "research plan execution", `9ae155d` "dashboard research execution", `ef3fbd9` "presentation slide 27 image generation", `ace29ec` "guideline proposal pak arry". **Reading of this cluster:** the legacy FER pipeline (face detection, HSEmotion pseudo-labeling, the $N=227$ manually labeled population, the ArcFace+Logistic-Regression comparison, and the R1–R9 internal evaluation sequence referenced throughout `docs/RESEARCH_FINDINGS.md` and `docs/R9_FINAL_STATISTICAL_VALIDATION.md`) was **substantially complete by this date**, since the only later commits (Stage 4 below) are explicitly about a *new*, separately named dataset ("papuan_v2"). This is a **Provisional** inference from commit message framing and document cross-reference, not from reading every commit's full diff.

- `ace29ec` "guideline proposal pak arry" is the first commit to name a supervisor figure directly in a commit message ("Pak Arry"), consistent with `docs/proposal/guideline/PROPOSAL_GUIDELINE_EXTRACTION.md`'s description of Pak Arry as the source of the proposal-writing/design-research guideline. **Corroborated** (commit message + document content agree).

## Stage 4 — Papuan V2 Line Begins (2026-09-19)

- `a62f0fa` "feature(dashboard): model comparison" and `21f1108` "dataset(papuan_v2): add new dataset for papuan v2" land the same day. This is the **first point at which a distinctly named "Papuan V2" dataset line exists**, separate from the legacy ($N=227$/$N=135$) dataset. Per `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md` and `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, Papuan V2 work from this point includes: a pilot-scale extraction (EXP-PAP-001, 645 face crops + 645 CLAHE crops), a 150-image pilot sample (EXP-PAP-002), HSEmotion/ArcFace predictions on the pilot (EXP-PAP-003), and a Label Studio human-annotation pilot setup (EXP-PAP-004, two isolated annotator servers). **Verified** (dataset existence, commit date, and experiment IDs cross-confirmed between commit log and internal reports); **the actual completion status of each EXP-PAP-00x step is tracked separately in `EXPERIMENT_REGISTRY.md`** — this timeline entry records only that the line of work began on this date, not that every sub-experiment within it finished.

## Stage 5 — Papuan V2 Audit and Design Documents (2026-10-01)

- `fdcad06` "docs(papuan_v2): add full project phase audit reports", `06defa6` "docs(papuan_v2): add AI-assisted annotation methodology design review". Internal reports as of this date describe: Annotator A (Label Studio, 150 tasks) reportedly fully submitted (**status re-flagged as unverified independently — see `DATA_DISCREPANCIES.md` item D-1**); Annotator B infrastructure (75-task overlap subset, isolated server) newly stood up but with 0/75 tasks complete; an "AI-assisted (paid) pre-labeling" annotation methodology considered and designed but confirmed, by explicit repository-wide search, to have **zero implementation** anywhere in the codebase.

## Stage 6 — Methodological Pivot and Landmark Track (2026-10-02)

- `de3c238` "docs(papuan_v2): port existing docs/reports history from worktree-papuan-v2-audit to main". Per `docs/reports/PAPUAN_V2_CURRENT_STATE.md`: on this date, a research supervisor referred to in internal documents as "Pak Fadhil" directed a **change of the primary annotation target from facial-expression labels to facial landmarks**. Concretely: a 68-point landmark schema (ibug-300W convention) was adopted; automatic landmark proposals were generated via InsightFace's `landmark_3d_68` sub-model; a 24-image CVAT pilot (EXP-PAP-005, fixed seed) was populated with these proposals; the CVAT point-label scheme was renamed from generic (`pt0`..`pt67`) to anatomically descriptive names, verified to introduce zero coordinate drift. **Human review of the CVAT pilot had not been performed as of this date.** This is the most recent dated milestone found in the committed history. **Verified** (commit exists; pivot is explicitly and repeatedly documented in the project's own internal reports, not inferred).

## Post-2026-10-02 — Uncommitted, In-Progress Work (current working tree, not yet committed)

The working tree (as of this reconstruction) contains substantial **uncommitted** changes beyond the last commit: modifications to `docs/EXPERIMENT.md`, `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, `docs/reports/PAPUAN_V2_RESEARCH_TIMELINE.md`, `pyproject.toml`, `uv.lock`; and new, untracked files including `docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md`, three new `docs/reports/PAPUAN_V2_CVAT_*` documents, `experiments/EXP-PAP-004/*` (annotator assignment/progress/export files), a new `experiments/EXP-PAP-005/` directory, three new test files, and six new `tools/papuan_v2/*.py` scripts plus a `validation/` subdirectory. **This represents work in progress that has not yet reached a committed, stable state**; per the Git-safety instructions for this task, none of these uncommitted files were modified, moved, or committed by this process. Their content was read (where relevant) as evidence for this audit, but they should be treated as **Provisional** until committed and, ideally, until their own internal consistency is independently re-checked after being finalized by the author.

## Stage 7 — Author Confirmation of Research Scope (2026-10-09)

Following the initial research-audit pass (this document's first version), the author confirmed two decisions that resolve previously open items, recorded in full in `RESEARCH_DECISIONS.md`:

1. **Facial emotion classification (the EXP-005/006/007 line) remains the primary research objective of the thesis.** The facial-landmark track (Stage 6) is a supporting/future-work development track, not a redefinition of the thesis's core direction.
2. **The $N=135$ common evaluation subset's provenance was investigated and confirmed to be the legacy 227-crop dataset, not a separate Papuan V2 reconstruction.** A hypothesis raised by the author that $N=135$ might come from a Papuan V2 reconstruction was checked against `docs/EXP-007_ARCFACE_EVALUATION.md`'s programmatic `face_filename`-join evidence (which shows the 227-sample population's 18 historical Neutral→Angry cases falling exactly inside the 135-sample subset) and withdrawn. See `research-audit/DATA_DISCREPANCIES.md` D-2 for the resolved derivation chain.

## What This Timeline Does *Not* Establish

- **No evidence of a FER2013 + ResNet18 "Experiment B"** (val acc 68.57% / test acc 69.77% / macro F1 68.65% / weighted F1 69.76% / generalization gap 26.96%) was found at any point in this timeline. A repository-wide, case-insensitive search for `FER2013`, `ResNet18`, `resnet`, and the specific numeric strings `68.57`, `69.77`, `68.65`, `69.76`, `26.96` across all tracked and untracked `.md`, `.py`, `.ipynb`, `.csv`, and `.json` files returned **zero matches**. See `DATA_DISCREPANCIES.md` item D-0 for the full disposition of this finding: it is classified **Unverifiable from this repository** — not fabricated, not disproven, simply absent. If this experiment exists, it exists in a different project, a different machine, an external notebook/platform, or a conversation/export not present in this workspace.
- **No pre-2026-08-14 history exists.** Git history begins at `9b5d0ac`; whatever research planning or exploratory work (if any) preceded that commit is not reconstructable from this repository alone.
- **No person/subject-identity field exists at any stage.** This is a standing limitation across the entire timeline, not something that changed at any dated milestone (see `DATA_DICTIONARY.md`).
