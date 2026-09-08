# Thesis FER — Codebase Audit & Refactoring Plan

You are acting as the primary software engineer for my thesis repository.

This repository contains the implementation for my Facial Expression Recognition (FER) thesis research, including dataset handling, preprocessing, model training, evaluation, robustness analysis, and experiment code.

Your role is to help me refactor and clean up the repository while preserving the scientific validity and reproducibility of the thesis.

## CORE PRINCIPLE

The primary objective is:

> Improve code quality, structure, readability, maintainability, and reproducibility WITHOUT unintentionally changing the experimental behavior or results.

This is a research codebase, not a generic software project.

Therefore, scientific correctness and reproducibility take priority over aggressive abstraction or "clean code".

---

# PHASE 0 — DO NOT MODIFY ANYTHING

Before making any changes, inspect the entire repository.

Do NOT create, delete, rename, or modify files during this phase.

First understand:

* Repository structure
* Entry points
* Dataset pipeline
* Preprocessing
* Augmentation
* Model implementations
* Training pipeline
* Validation pipeline
* Testing pipeline
* Evaluation
* Robustness analysis
* Visualization
* Experiment scripts
* Configuration
* Checkpoints
* Result generation
* Utility functions
* Dependencies

Trace the actual execution flow:

Dataset
→ Dataset preprocessing
→ DataLoader
→ Model
→ Training
→ Validation
→ Checkpoint
→ Testing
→ Evaluation
→ Metrics
→ Visualization / Results

---

# PHASE 1 — BASELINE & EXPERIMENTAL INTEGRITY

Before refactoring, identify the current experimental baseline.

Document:

### Dataset

* Dataset source
* Dataset structure
* Number of classes
* Class mapping
* Train/validation/test split
* Any filtering
* Any balancing
* Any sampling

### Preprocessing

* Image resizing
* Normalization
* Cropping
* Face detection
* Landmark processing
* Augmentation
* Any other transformation

### Training

* Model architecture
* Loss function
* Optimizer
* Learning rate
* Scheduler
* Batch size
* Number of epochs
* Early stopping
* Weight initialization
* Random seed

### Evaluation

* Accuracy
* Precision
* Recall
* F1-score
* Confusion matrix
* Per-class metrics
* Any robustness metrics
* Any additional thesis-specific metrics

### Reproducibility

Identify:

* Random seeds
* Deterministic settings
* Environment/dependency requirements
* Dataset version/path assumptions
* Checkpoint dependencies

Identify which parts of the code are experimentally sensitive.

Especially flag:

* Dataset splitting
* Label mapping
* Preprocessing
* Augmentation
* Normalization
* Randomness
* Model architecture
* Loss calculation
* Evaluation metrics

These components must be treated as HIGH RISK during refactoring.

---

# PHASE 2 — CURRENT ARCHITECTURE AUDIT

Analyze the current architecture and produce a clear map.

For each important file, explain:

* Its responsibility
* Which files depend on it
* Which files it depends on
* Whether its responsibility is appropriate
* Whether it contains duplicated logic
* Whether it is overly coupled
* Whether it should be split, merged, moved, or left untouched

Identify:

### Code quality issues

* Poor naming
* Large functions
* Large classes
* Duplicate code
* Dead code
* Unused imports
* Magic numbers
* Hardcoded paths
* Hardcoded hyperparameters
* Repeated logic
* Inconsistent conventions
* Excessive comments
* Missing documentation

### Architecture issues

* Circular dependencies
* Tight coupling
* Responsibilities mixed together
* Training logic mixed with evaluation
* Visualization mixed with metric calculation
* Data processing mixed with model logic
* Experiment-specific code mixed with reusable code
* Scripts containing too much business logic

### Research-code issues

* Hidden assumptions
* Non-reproducible behavior
* Potential data leakage
* Inconsistent preprocessing
* Inconsistent train/test behavior
* Evaluation logic that may differ between experiments
* Results that cannot easily be traced back to a configuration

---

# PHASE 3 — TECHNICAL DEBT PRIORITIZATION

Create a prioritized technical-debt list.

Use:

## CRITICAL

Issues that can affect scientific validity, correctness, reproducibility, or experimental results.

## HIGH

Issues that significantly affect maintainability or can easily cause inconsistent experiments.

## MEDIUM

Structural and readability issues that should be improved but are unlikely to affect results.

## LOW

Cosmetic or minor cleanup.

For every issue provide:

1. Problem
2. Location
3. Why it matters
4. Recommended solution
5. Risk of changing behavior
6. Priority

---

# PHASE 4 — PROPOSE TARGET ARCHITECTURE

DO NOT implement it yet.

Based on the actual repository, propose a cleaner architecture.

The architecture should conceptually separate:

```text
Configuration
     ↓
Data
     ↓
Preprocessing / Augmentation
     ↓
Model
     ↓
Training
     ↓
Evaluation
     ↓
Experiment Management
     ↓
Results / Visualization
```

Potential conceptual structure:

```text
project/
├── configs/
├── src/
│   ├── data/
│   ├── models/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── utils/
├── experiments/
├── scripts/
├── tests/
├── checkpoints/
├── results/
└── README.md
```

IMPORTANT:

Do NOT force this structure blindly.

Adapt the target architecture to the actual repository.

For every proposed structural change explain:

* Current location
* Proposed location
* Reason
* Dependencies affected
* Refactoring risk

---

# PHASE 5 — REFACTORING STRATEGY

Create a phased refactoring roadmap.

The order should prioritize low-risk changes first.

Recommended priority:

### Phase A — Safe cleanup

* Formatting
* Naming
* Import cleanup
* Dead code
* Obvious duplication
* Documentation

### Phase B — Configuration

Centralize:

* Paths
* Hyperparameters
* Dataset settings
* Model settings
* Training settings
* Evaluation settings
* Random seeds

### Phase C — Data pipeline

Separate:

* Dataset loading
* Preprocessing
* Augmentation
* DataLoader construction

### Phase D — Model layer

Separate:

* Model definitions
* Model factory
* Losses
* Model configuration

### Phase E — Training

Separate:

* Training loop
* Validation loop
* Checkpointing
* Logging

### Phase F — Evaluation

Separate:

* Metric calculation
* Confusion matrix
* Per-class analysis
* Robustness evaluation
* Visualization

### Phase G — Experiment management

Make experiments reproducible and traceable.

### Phase H — Testing

Add tests around high-risk components.

### Phase I — Documentation

Finalize README and experiment documentation.

Do NOT assume all phases are necessary.
Adjust based on the audit.

---

# PHASE 6 — EXPERIMENT TRACEABILITY

The refactored repository should make it easy to answer:

> "Where did this result come from?"

For every experiment, ideally we should be able to identify:

```text
Experiment
    ↓
Configuration
    ↓
Dataset
    ↓
Preprocessing
    ↓
Model
    ↓
Training
    ↓
Checkpoint
    ↓
Evaluation
    ↓
Metrics
    ↓
Figures / Tables
```

Pay special attention to thesis experiments such as:

* Baseline
* Model comparison
* Preprocessing comparison
* Augmentation experiments
* Robustness analysis
* Ablation studies
* Any other experiments currently present in the repository

Do not change the scientific methodology.

Improve only the implementation structure and traceability.

---

# PHASE 7 — TESTING STRATEGY

Propose tests for behavior that must remain stable.

At minimum consider:

### Dataset

* Correct dataset loading
* Correct label mapping
* Correct number of classes
* Correct image shape

### Preprocessing

* Expected output dimensions
* Expected normalization
* Consistent train/test preprocessing

### Model

* Correct input shape
* Correct output shape
* Correct number of classes
* Forward pass

### Evaluation

* Correct metric calculation
* Correct class ordering
* Correct confusion matrix
* Correct aggregation

### Reproducibility

* Random seed handling
* Deterministic settings where applicable

Do NOT add unnecessary tests just for test coverage.

Focus on protecting scientific behavior.

---

# PHASE 8 — VALIDATION AFTER EACH REFACTOR

When implementation begins, NEVER refactor the entire repository in one operation.

Use this loop:

```text
Select ONE refactoring scope
        ↓
Implement
        ↓
Run tests
        ↓
Run relevant experiment
        ↓
Compare against baseline
        ↓
Verify no unintended behavior change
        ↓
Commit
        ↓
Move to next scope
```

Each refactoring step should be independently reviewable.

If a refactor changes experimental results, STOP and investigate before continuing.

Do not simply accept changed results.

---

# PHASE 9 — GIT / CHANGE MANAGEMENT

Recommend logical commits.

For example:

```text
refactor: clean unused imports
refactor: centralize configuration
refactor: separate dataset pipeline
refactor: extract training loop
refactor: modularize evaluation
test: add dataset validation tests
docs: update experiment documentation
```

Avoid giant commits such as:

```text
refactor entire project
```

Each commit should ideally represent one conceptual change.

---

# PHASE 10 — FINAL REPOSITORY GOAL

The final repository should satisfy:

### Maintainability

* Clear responsibilities
* Small and understandable modules
* Minimal duplication
* Consistent naming

### Reproducibility

* Explicit configuration
* Explicit random seeds
* Documented dependencies
* Reproducible experiment commands

### Research integrity

* Dataset split preserved
* Preprocessing behavior preserved
* Model behavior preserved
* Evaluation methodology preserved
* Metrics preserved

### Experiment usability

It should be straightforward to:

```text
Train a model
Run evaluation
Run inference
Run robustness analysis
Compare experiments
Reproduce thesis results
```

---

# REQUIRED OUTPUT FROM THIS AUDIT

Before changing any code, return the following report:

## 1. Executive Summary

Briefly explain the current state of the repository.

## 2. Repository Structure

Explain the important directories and files.

## 3. Execution Flow

Show the actual pipeline from dataset to final results.

## 4. Current Architecture

Explain how components currently interact.

## 5. Technical Debt

Prioritized as:

Critical → High → Medium → Low

## 6. Experimental Integrity Risks

Explicitly identify anything that must be preserved.

## 7. Proposed Target Architecture

Show the proposed structure.

## 8. Refactoring Roadmap

Provide a phased implementation plan.

For each phase include:

* Scope
* Files affected
* Expected changes
* Risk
* Validation method
* Expected outcome

## 9. Testing Strategy

What tests should be introduced and why.

## 10. Migration Strategy

Explain how to move from the current architecture to the proposed architecture safely.

## 11. Questions / Ambiguities

List anything you cannot determine from the repository and need clarification on.

---

# IMPORTANT RULES

1. DO NOT MODIFY ANY FILES during this audit.
2. DO NOT DELETE CODE.
3. DO NOT rewrite code yet.
4. DO NOT change model architecture.
5. DO NOT change preprocessing.
6. DO NOT change dataset splitting.
7. DO NOT change hyperparameters.
8. DO NOT change evaluation methodology.
9. DO NOT optimize performance unless explicitly requested.
10. DO NOT introduce abstractions merely for the sake of abstraction.
11. Prefer simple, readable solutions.
12. Preserve existing behavior unless a bug is explicitly identified and approved for fixing.
13. Clearly distinguish between:

    * Refactoring
    * Bug fixing
    * Behavioral change
    * Research-methodology change
14. If you suspect a bug that could affect thesis results, FLAG IT instead of silently fixing it.
15. Do not start implementation until the audit report has been reviewed.

The immediate goal is NOT to make the code "perfect".

The immediate goal is to understand the codebase deeply enough that we can safely refactor it without compromising the thesis.

---

# ADDENDUM — Approved Decisions & Phase 0–2 Implementation Plan

This addendum reflects the completed audit (`docs/REPO_AUDIT_REPORT.md`) and the researcher's approved decisions on the open questions it raised. It supersedes nothing above — the original phase definitions (0–10) remain the process; this section pins down which options were chosen where the plan required a decision, and details what Phase 0–2 execution looks like for this specific repository.

## Approved Decisions

| # | Question | Decision |
|---|---|---|
| 1 | `quality.*` config keys / undocumented "Quality Filter" stage | **Strip dead config, fix docs.** Remove `quality.min_face_size` and `quality.blur_threshold` from `config/config.yaml`; correct `docs/ARCHITECTURE.md` and `docs/SDD.md` to describe the pipeline as it actually exists (no quality-filtering stage, no checkpoint/resume system). Also remove the other confirmed-dead config keys found in the audit (`face_detection.confidence`, `expression.confidence_threshold`, `output.save_landmarks`, `output.save_csv`) since none are read by any code. |
| 2 | `src/landmark_comparison.py` status | **Active — wire into `main.py`.** It remains a used analysis step; make it an optional, config-gated stage (mirroring the existing `landmark_analysis.enabled` pattern) so it is reproducible from the documented entry point instead of only runnable standalone. |
| 3 | `tools/visualize_landmark_npy.py` intent | **Reusable tool — parametrize.** Treat as a keeper utility; a later phase will convert its hardcoded `frame_000043_face02` path into a CLI argument. |
| 4 | Notebook vs. `src/` skin-tone/CLAHE logic divergence | **`src/` is canonical.** `src/landmark_analyzer.py`'s `_compute_skin_tone` is the source of truth. If a diff shows `notebooks/preprocessing_experiment.ipynb`'s inline `compute_l_weighted` differs numerically, the notebook is reconciled to match `src/`, not the other way around. |
| 5 | `face_landmarker.task` binary in git | **Stop tracking it.** Remove from git; rely on the existing auto-download-if-missing logic in `landmark_analyzer.py`. |
| 6 | Import mechanism for `src/main.py` | **Resolved by inspection, no decision needed.** `README.md` documents `uv run python src/main.py` as the invocation; running a script this way puts its own directory (`src/`) on `sys.path`, which is why the bare `from frame_extractor import FrameExtractor`-style imports in `main.py` currently work without a package install. This constrains Phase D (packaging, per the audit's target architecture) to either preserve this invocation style or update `README.md`/add a console-script entry point in lockstep — not something to change silently. |

These decisions are binding for Phases 3 onward (Safe Cleanup, Configuration, Data pipeline, Package structure) in the audit's roadmap (Section G of `docs/REPO_AUDIT_REPORT.md`). They do not change the fundamental scope of this refactoring plan — they resolve ambiguities the plan explicitly asked to have flagged rather than silently resolved.

## Phase 0 — Baseline (Do Not Modify) — Implementation Plan

**Goal:** Capture a reproducible snapshot of current pipeline outputs to diff against after every later change. No source files are touched in this phase.

Steps:
1. Confirm `config/config.yaml` is set to `debug.enabled: true`, `debug.max_frames: 100` (already the case) so the baseline run is fast and deterministic in scope.
2. Run `uv run python src/main.py` once, end to end, on the existing `data/raw/videos/pesta_babi.mp4`.
3. Copy the following outputs out of `data/` (which is gitignored and gets cleared by the pipeline on every run) into a durable, git-tracked snapshot location, e.g. `docs/baseline_snapshots/phase0/`:
   - `data/intermediate/annotations.csv`
   - `data/processed/annotations.csv`
   - `data/intermediate/landmark_features.csv`
   - File counts per stage (frames, faces, landmarks) as printed in the pipeline summary
4. Record the exact `uv.lock`-pinned versions of `insightface`, `hsemotion-onnx`, `mediapipe`, `opencv-python`, `onnxruntime` alongside the snapshot (these determine model behavior; a version bump later would explain a legitimate diff vs. an actual regression).
5. Commit the snapshot with a message such as `test: capture Phase 0 baseline pipeline outputs`.

**Validation:** Snapshot files exist, are non-empty, and row counts match the pipeline's own printed summary. No code changed — `git diff` over `src/`, `config/`, `docs/*.md` (other than this plan and the snapshot) should be empty.

## Phase 1 — Baseline & Experimental Integrity — Implementation Plan

**Goal:** Formally document, in `docs/EXPERIMENT.md`, the experimentally-sensitive parameters and behaviors identified in the audit (Section E) as the record against which all later refactors are checked. Still no source changes.

Steps:
1. Fill in a real `EXPERIMENT.md` entry (using its existing template) for the Phase 0 baseline run itself: FPS, detection confidence (as actually hardcoded, not the dead config value), blur/face-size (note: not actually filtered, per Decision 1), and the resulting frame/face/prediction counts from Phase 0.
2. Add a short "Experimental Integrity Boundaries" table to `docs/EXPERIMENT.md` (or reference `docs/REPO_AUDIT_REPORT.md` Section E directly) listing the HIGH-RISK items that must remain byte-for-byte equivalent through Phases 3+: frame sampling interval, InsightFace model/padding, HSEmotion model + softmax, MediaPipe landmark model/thresholds, the four geometric feature formulas, and the skin-tone LAB thresholds.
3. Explicitly note the two flagged Potential Issues from the audit (silent row-order label fallback; duplicate InsightFace instantiation in `EmotionClassifier`) as **known, un-fixed** behavior going into Phase 2, so they aren't mistaken for a Phase 2 finding.

**Validation:** `docs/EXPERIMENT.md` reads as a filled record, not a template. No `src/` changes.

## Phase 2 — Current Architecture Audit — Implementation Plan

**Goal:** This phase is substantially already complete via `docs/REPO_AUDIT_REPORT.md` (Sections B–D). The remaining Phase 2 work is to fold the *approved decisions* back into the living docs so `docs/ARCHITECTURE.md` and `docs/SDD.md` stop describing an aspirational pipeline — this is documentation-only, classified SAFE, and is the first phase that touches files outside `docs/REFACTORING_PLAN.md`/`docs/REPO_AUDIT_REPORT.md`/`docs/EXPERIMENT.md`.

Steps:
1. `docs/ARCHITECTURE.md`: remove the "Quality Filter" module section and the "Checkpointing" section (neither exists in code, per Decision 1); replace the pipeline diagram with the actual flow from `docs/REPO_AUDIT_REPORT.md` Section C (including the now-wired `LandmarkComparison` stage per Decision 2).
2. `docs/SDD.md`: correct the Technology Stack table's "Face Detection: YOLO" to "InsightFace (SCRFD, buffalo_l)"; remove the Quality Filtering functional requirement and the checkpoint-system section per Decision 1; update the Pipeline diagram to drop "Quality Filtering" and "Face Alignment" (neither implemented).
3. Add a short note to both docs pointing at `docs/REPO_AUDIT_REPORT.md` as the authoritative current-state audit, so future edits don't re-drift from code.
4. No changes to `src/` in this phase — config key removal (Decision 1) and the `landmark_comparison.py` wiring (Decision 2) are Phase 3 (Safe Cleanup) / Phase-C-equivalent (Data pipeline) work per the audit's roadmap, since they touch `config.yaml` and `main.py` respectively, not just docs.

**Validation:** `git diff` for this phase touches only `docs/ARCHITECTURE.md`, `docs/SDD.md`, and this plan file. `src/`, `config/`, `tests/` remain untouched. Docs, read cold, now match the traced execution flow in Section C of the audit report.

## What Comes Next (not part of this Phase 0–2 plan)

Per the roadmap in `docs/REPO_AUDIT_REPORT.md` Section G, source-code changes begin at Phase 3 (Safe Cleanup: `.DS_Store`/`.gitignore`/`face_landmarker.task` untracking) and are sequenced Safe Cleanup → Testing (pulled early, since Phase C below is HIGH RISK) → Configuration → Data pipeline dedup → Package structure → Analysis wiring/docs. Phase 3 execution requires a separate go-ahead per the "Do NOT modify source code yet" instruction governing this addendum.
