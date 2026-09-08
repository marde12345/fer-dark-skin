# FER-Dataset Repository Audit Report

Produced per `docs/REFACTORING_PLAN.md`. **No source files were modified while producing this report.** This is a planning artifact only.

---

## A. Executive Summary

This repository is **not** a model-training codebase — it is a **semi-automatic dataset-generation pipeline**. It takes one source video, extracts frames, detects/crops faces, pseudo-labels each face's emotion with a pretrained model (HSEmotion ONNX), extracts MediaPipe facial landmarks + geometric features + skin-tone estimate, and assembles a labeled image dataset (`data/processed/`) plus a markdown report.

There is no dataset split, no model training/fine-tuning, no loss function, no optimizer, and no random seed anywhere in `src/`. "Experimental integrity" in this repo means: **the pseudo-labeling and feature-extraction logic must produce the same outputs on the same input video**, because the thesis's downstream analysis (in the notebooks) depends on these CSVs/images being reproducible.

The `src/` pipeline is small (9 files, ~700 LOC), reasonably readable, and already fairly modular (one class per stage). The real technical debt is concentrated in:
1. **Two parallel, diverging implementations** of the same preprocessing/labeling logic — one in `src/`, one duplicated inline in `notebooks/preprocessing_experiment.ipynb`.
2. **A stage in `docs/ARCHITECTURE.md`/`SDD.md` that doesn't exist in code** (Quality Filter / blur & brightness filtering, checkpointing) — the docs describe an aspirational pipeline, not the actual one.
3. **A dangling/orphaned module** (`landmark_comparison.py`) never invoked from `main.py`, only runnable standalone.
4. **No tests at all** (`tests/` is empty).
5. **Hardcoded paths and models** (video path in config is fine; but `face_landmarker.task` path, `hsemotion enet_b0_8_best_vgaf`, InsightFace `buffalo_l` are hardcoded in class bodies, not config).
6. **Destructive-by-default stages**: several classes delete prior output directories/files on `__init__` (`clear_directory`, `annotation_file.unlink()`), which is fine for a linear single-video pipeline but is a foot-gun for re-runs/experiments and has no dry-run or backup.

None of this affects "results" in the ML sense (there's no trained model), but it does affect **reproducibility of the labeled dataset**, which is the actual research artifact. The refactor should focus on: deduplicating notebook vs. src logic, centralizing config-driven parameters, adding minimal regression tests around labeling/feature math, and reconciling docs with actual pipeline.

---

## B. Current Architecture / Repository Structure

```
FER-Dataset/
├── config/config.yaml          # single run config (video path, thresholds, output paths)
├── src/
│   ├── main.py                 # orchestrator / entry point
│   ├── frame_extractor.py      # video -> frames (OpenCV)
│   ├── face_detector.py        # frames -> face crops (InsightFace/SCRFD)
│   ├── emotion_classifier.py   # face crops -> pseudo-labels (HSEmotion ONNX) + optional viz
│   ├── landmark_analyzer.py    # face crops -> 478 MediaPipe landmarks + geometric features + skin tone
│   ├── dataset_builder.py      # copies labeled crops into data/processed/images + annotations.csv
│   ├── dataset_report.py       # annotations.csv -> reports/dataset_report.md + plots
│   ├── landmark_comparison.py  # ORPHAN: standalone script, not called from main.py
│   ├── file_utils.py           # clear_directory() helper
│   └── logger.py               # section() print helper
├── tools/
│   └── visualize_landmark_npy.py   # new (untracked), ad-hoc single-file landmark visualizer, hardcoded paths
├── notebooks/
│   ├── data_audit.ipynb                    # audits model predictions vs manual ground truth
│   ├── preprocessing_experiment.ipynb      # tests CLAHE preprocessing variant — DUPLICATES emotion_classifier/landmark_analyzer logic inline
│   └── preprocessing_experiment_executed.ipynb  # executed copy of the above (output cache)
├── docs/
│   ├── ARCHITECTURE.md    # describes an idealized pipeline incl. stages not implemented (Quality Filter, checkpointing)
│   ├── SDD.md              # design doc, also describes unimplemented stages (YOLO detector — actual code uses InsightFace)
│   ├── DEVELOPMENT_ROADMAP.md  # checklist, partially stale
│   ├── EXPERIMENT.md       # empty experiment log template, no filled entries
│   └── REFACTORING_PLAN.md # source of truth for this audit
├── reports/                 # generated report + all plot assets (checked into git)
├── data/                    # gitignored entirely; raw video, intermediate frames/faces/landmarks, processed dataset
├── tests/                   # EMPTY
└── face_landmarker.task     # downloaded MediaPipe model binary, checked into git root (3.7MB)
```

Note: `docs/ARCHITECTURE.md` and `docs/SDD.md` reference a "Quality Filter" stage (blur/brightness/face-size filtering) and a checkpoint/resume system. **Neither exists in the current code.** `config.yaml` has `quality.min_face_size` and `quality.blur_threshold` keys defined but **no code in `src/` reads or applies them** — they are dead config.

---

## C. Execution Flow (actual, traced from `main.py`)

```
config/config.yaml
        │
        ▼
FrameExtractor.extract()        video -> data/intermediate/frames/*.jpg  (OpenCV, fixed FPS sampling)
        │
        ▼
FaceDetector.detect()           frames -> data/intermediate/faces/*.jpg (InsightFace SCRFD "buffalo_l", 20% bbox padding)
        │
        ▼
EmotionClassifier.predict()     faces -> data/intermediate/annotations.csv (HSEmotion ONNX "enet_b0_8_best_vgaf", softmax confidence)
        │                       (+ optional landmark-dot visualization via a SECOND InsightFace instance)
        ▼
DatasetBuilder.build()          faces + annotations.csv -> data/processed/images/*.jpg + data/processed/annotations.csv (renumbered filenames)
        │
        ▼
[if landmark_analysis.enabled] LandmarkAnalyzer.run()
        faces -> data/intermediate/landmarks_468/*.npy (478 MediaPipe landmarks)
              -> data/intermediate/landmark_features.csv (brow_lowering_distance, lip_corner_distance,
                 mouth_openness, inter_ocular_distance, skin_tone via LAB-channel heuristic)
        │
        ▼
DatasetReport.generate()        data/processed/annotations.csv -> reports/dataset_report.md + reports/assets/*.png
```

Two things worth flagging about this flow:
- `LandmarkAnalyzer` reads `config["output"]["processed_annotations"]` (i.e. `data/processed/annotations.csv`, produced by `DatasetBuilder`) to attach labels to features — but it iterates over face crops in `input_dir` = `data/intermediate/faces`, and falls back to **row-order alignment** (`ann.iloc[idx]`) when filename match fails (`landmark_analyzer.py:206-209`). This is a silent correctness risk if the two directories/files ever get out of sync (see Section E).
- `LandmarkComparison` (`src/landmark_comparison.py`) is a **separate downstream analysis step** (group comparisons + boxplots for angry-vs-neutral / skin-tone) that is never called by `main.py`. It's only runnable via `python src/landmark_comparison.py` directly. Its outputs (`reports/landmark_comparison_summary.csv`, several `landmark_*.png`) exist in the repo, so it clearly has been run manually — it's just structurally disconnected from the declared pipeline.
- The notebooks (`data_audit.ipynb`, `preprocessing_experiment.ipynb`) are a **third, independent execution path** that reads the CSVs the pipeline produces and, in `preprocessing_experiment.ipynb`, **reimplements CLAHE preprocessing + HSEmotion inference inline** rather than importing `src/emotion_classifier.py`. This is the most important structural finding — see D.1.

---

## D. Major Problems

### D.1 — Duplicated pipeline logic between `src/` and notebooks (HIGH, structural)
**Location:** `notebooks/preprocessing_experiment.ipynb` cells 2-3 vs `src/landmark_analyzer.py:118-137` (`_compute_skin_tone`) and `src/emotion_classifier.py` (HSEmotion invocation + softmax).
**Current behavior:** The notebook independently defines `compute_l_weighted()` (near-identical to `LandmarkAnalyzer._compute_skin_tone`) and re-instantiates `HSEmotionRecognizer` to re-run inference with a CLAHE preprocessing step, rather than importing and reusing `src/` code.
**Problem:** Any future change to the skin-tone formula or classifier invocation in `src/` will silently diverge from what the notebook (and thesis findings drawn from it) actually used. There's no single source of truth for "how is skin tone computed."
**Proposed change:** Extract shared logic (`compute_skin_tone`, emotion inference wrapper) into an importable module notebooks can call, OR explicitly document the notebook as a frozen, standalone experiment snapshot that should never be reconciled with `src/` (since it represents a specific past experiment's exact code).
**Risk:** LOW to do the extraction structurally, but MEDIUM to decide *which* implementation is canonical if they've already diverged in values.
**Validation required:** Diff the notebook's `compute_l_weighted` against `LandmarkAnalyzer._compute_skin_tone` line-by-line before touching either.

### D.2 — `landmark_comparison.py` is disconnected from `main.py` (MEDIUM)
**Location:** `src/landmark_comparison.py`, not imported/called anywhere in `src/main.py`.
**Problem:** A pipeline stage that produces committed report artifacts is invisible from the documented entry point, so "how do I reproduce `reports/landmark_comparison_summary.csv`" is not answerable from `main.py` or `config.yaml` alone.
**Proposed change:** Either wire it into `main.py` as an optional stage (config-gated, like `landmark_analysis.enabled`) or move it into a clearly-labeled `experiments/` or `analysis/` folder to signal it's a standalone analysis script, not a pipeline stage.
**Risk:** LOW (no computation changes, just wiring/location).
**Validation required:** Confirm output CSV/plots are byte-identical before/after move.

### D.3 — Docs describe stages that don't exist in code (MEDIUM)
**Location:** `docs/ARCHITECTURE.md` (Quality Filter, checkpointing), `docs/SDD.md` (YOLO for face detection — actual code uses InsightFace SCRFD).
**Problem:** Anyone onboarding from docs will build a wrong mental model. `config.yaml`'s `quality.min_face_size` / `quality.blur_threshold` keys reinforce this — they look active but are unused.
**Proposed change:** Update docs to reflect actual pipeline (SAFE, docs-only), OR flag `quality.*` config keys as either dead code to remove or a genuinely missing feature to implement (this is a **decision for you**, not something to silently resolve).
**Risk:** SAFE (docs only) for the doc fix. Implementing the missing quality filter would be a **behavioral change** requiring approval since it would change which faces enter the dataset.

### D.4 — Destructive `__init__` side effects (LOW/MEDIUM)
**Location:** `frame_extractor.py:30`, `face_detector.py:23`, `emotion_classifier.py:34-35`, `dataset_builder.py:27-29` — each stage clears its own output directory/file the moment the class is constructed, before `.run()`/`.extract()`/etc. is even called.
**Problem:** Instantiating `main.py`'s objects (all constructed up front, lines 20-57, before any `section()` call) means the *very act of building the pipeline object graph* deletes prior run outputs — even if a later stage then crashes. There's no dry-run, no "are you sure," no backup of the previous run.
**Proposed change:** Not urgent to change behavior, but worth centralizing "clear before run" into an explicit orchestration step (e.g., a `Pipeline.run()` that clears stage-by-stage right before that stage executes) rather than at construction time. This is a **structural** improvement — SAFE if implemented as a pure refactor (same net effect, different timing only if nothing errors mid-pipeline; if something errors mid-pipeline the *current* behavior already partially clears things, so making clearing lazy is actually slightly safer).
**Risk:** LOW-MEDIUM — must confirm identical final on-disk state assuming no exceptions.

### D.5 — Hardcoded model names / thresholds not in config (LOW/MEDIUM)
**Location:** `face_detector.py:26` (`name="buffalo_l"`, `det_size=(640,640)`), `emotion_classifier.py:39` (`model_name="enet_b0_8_best_vgaf"`), `landmark_analyzer.py:61-63` (MediaPipe confidence thresholds `0.5`), `face_detector.py:57` (`padding = 0.2`), `landmark_analyzer.py:131-136` (skin-tone bucket thresholds `100/150/190`).
**Problem:** `config.yaml` already centralizes some thresholds (`face_detection.confidence`, `expression.confidence_threshold`) but **none of these are actually read/used by the code** — e.g. `config["face_detection"]["confidence"]` is never passed into `FaceDetector`. This is a second instance of dead config (see D.3), and conversely some real thresholds (padding, skin-tone buckets, model names) live as magic numbers in code instead of config.
**Proposed change:** Reconcile config.yaml with what's actually parameterizable; move magic numbers to config where they represent genuine experimental parameters (skin-tone thresholds, padding) — this touches HIGH-RISK preprocessing logic, so treat carefully (see E).
**Risk:** MEDIUM — moving a magic number to config is safe only if the config value is set to exactly the current hardcoded value.

### D.6 — No tests (HIGH from a refactor-safety standpoint)
**Location:** `tests/` is empty.
**Problem:** There is currently zero automated protection against a refactor silently changing skin-tone bucketing, feature normalization, or label mapping. All "validation" during refactor would depend on rerunning the full pipeline (slow — SCRFD/HSEmotion/MediaPipe inference) and diffing CSVs by hand.
**Proposed change:** See Section I.

### D.7 — Committed `.venv`-adjacent artifacts / notebook checkpoints (LOW)
**Location:** `src/__pycache__/*.pyc` are on disk (though `.gitignore` excludes `__pycache__/`, so likely not tracked — verify), `notebooks/.ipynb_checkpoints/data_audit-checkpoint.ipynb` exists on disk.
**Problem:** Checkpoint notebook may or may not be tracked in git; if tracked, it's redundant.
**Proposed change:** Confirm `.ipynb_checkpoints/` is gitignored; if not, add it and remove from tracking. SAFE.

### D.8 — `face_landmarker.task` (3.7MB binary) committed to repo root (LOW)
**Location:** `/face_landmarker.task`, and `landmark_analyzer.py:53-55` auto-downloads it if missing from a hardcoded Google URL.
**Problem:** Binary model files in git bloat repo history; the code already has a self-healing download mechanism, so committing the file is redundant (and version-pins nothing, since the URL always points at `float16/1/`).
**Proposed change:** Consider removing from git tracking (add to `.gitignore`) since the code re-downloads it anyway — SAFE, but confirm the URL is stable/still resolves before relying on auto-download only.

### D.9 — `.DS_Store` tracked in git (LOW/COSMETIC)
**Location:** repo root `.DS_Store`, shown as modified in git status.
**Proposed change:** Add to `.gitignore`, `git rm --cached .DS_Store`. SAFE, trivial.

---

## E. Experimental Integrity Risks — components that define the actual research methodology

This project has no train/test split or model training, so "experimental integrity" means: **the labeled dataset and derived features must be reproducible and must not silently change meaning.** These are the boundaries that must remain byte-for-byte / functionally equivalent unless you explicitly approve a change:

| Component | Location | Must preserve exactly? | Notes |
|---|---|---|---|
| Frame sampling | `frame_extractor.py:56-59` (`frame_interval = max(int(original_fps/target_fps),1)`) | YES | Determines *which* frames exist at all; changing this changes the entire downstream dataset. |
| Face detection model & params | `face_detector.py:25-33` (InsightFace `buffalo_l`, det_size 640×640, CPU) | YES | Model choice affects which faces are found/cropped. |
| Bounding-box padding | `face_detector.py:57` (`padding = 0.2`) | YES | Changes crop framing fed into both classifier and landmarker. |
| Emotion pseudo-labeling model | `emotion_classifier.py:39` (HSEmotion `enet_b0_8_best_vgaf`) + softmax (`emotion_classifier.py:11-14`) | YES | This *is* the label generation — the ground truth for the whole dataset is model output, not human-annotated. |
| Landmark model | `landmark_analyzer.py:57-67` (MediaPipe FaceLandmarker, confidence thresholds 0.5) | YES | |
| Geometric feature formulas | `landmark_analyzer.py:85-115` (`brow_lowering_distance`, `lip_corner_distance`, `mouth_openness`, all normalized by inter-ocular distance using specific landmark indices 33/55/65/61/291/13/14/263) | YES — these indices/formulas are cited as "user requirement" per comment at line 86; any change is a methodology change, not a refactor. | HIGH RISK |
| Skin-tone heuristic | `landmark_analyzer.py:118-137` (LAB L-channel, weighted center/mean/median, thresholds 100/150/190) | YES | This is a thesis-relevant grouping variable (fairness/robustness analysis by skin tone) — bucket boundaries are load-bearing. |
| Label/annotation join logic | `landmark_analyzer.py:199-209` (filename match, fallback to row-order) | YES, but **flagged as a potential issue** — see below. | |
| Random seeds | **None found anywhere in `src/`.** | N/A | Neither face detection, emotion classification, nor landmark detection in this pipeline use stochastic algorithms with settable seeds in the current code — behavior should already be deterministic given identical inputs/model weights/library versions. Confirm library versions are pinned (they are, via `uv.lock`) since ONNX/mediapipe results can vary across versions. |

### Potential Issue (flagging, not fixing)

```
Potential Issue: Silent fallback to row-order label alignment
Impact: If data/intermediate/faces (input to LandmarkAnalyzer) and data/processed/annotations.csv
        (input to the label-join) ever contain a different number of images, or images in a
        different order — e.g. because DatasetBuilder skips faces whose source file no longer
        exists (dataset_builder.py:41-42), or because faces/ was regenerated after annotations.csv
        was built — then landmark_analyzer.py:206-209 silently attaches the WRONG label to a
        landmark feature row via positional (iloc) alignment instead of failing loudly.
Evidence: landmark_analyzer.py lines 199-209 — filename match is tried first, but on miss it
        falls back to `ann.iloc[idx]` where idx is the enumerate() index over
        sorted(input_dir.glob("*.jpg")), not a guaranteed-aligned index into `ann`.
Recommended action: Add a hard assertion/warning when the fallback path triggers (currently it
        does so silently), and audit whether it has ever actually triggered on the existing dataset
        (i.e., check reports/dataset_report.md counts vs landmark_features.csv row count for
        historical runs).
Requires researcher approval: YES
```

```
Potential Issue: Two independently-instantiated InsightFace models in EmotionClassifier
Impact: emotion_classifier.py constructs a SECOND full InsightFace FaceAnalysis instance
        (lines 41-46) purely to draw 5-point keypoints for the optional visualization feature —
        this is not a correctness bug (doesn't affect labels/features), but it roughly doubles
        model load time/memory for a visualization-only feature, and duplicates the detector
        already instantiated in FaceDetector for the same crops.
Evidence: emotion_classifier.py:41-46 vs face_detector.py:25-33 (same "buffalo_l" model).
Recommended action: Not a correctness risk, safe to defer/pass a shared detector instance in a
        later refactor phase — flagged here only because it touches face-detection code, which is
        HIGH RISK by classification.
Requires researcher approval: NO (informational; low priority)
```

---

## F. Proposed Target Architecture

Given the repo is genuinely a linear ETL-style pipeline (not a training codebase), a heavy `src/{data,models,training,evaluation}` split is over-engineering. Proposed structure stays close to current layout but resolves the disconnects found above:

```
FER-Dataset/
├── config/
│   └── config.yaml                 # extend to include currently-hardcoded params (Section D.5)
├── src/
│   └── fer_dataset/                # (optional) turn into an installable package to fix relative-import fragility
│       ├── pipeline/
│       │   ├── frame_extractor.py
│       │   ├── face_detector.py
│       │   ├── emotion_classifier.py
│       │   ├── landmark_analyzer.py
│       │   ├── dataset_builder.py
│       │   └── dataset_report.py
│       ├── analysis/
│       │   └── landmark_comparison.py   # MOVED here: clearly downstream analysis, not pipeline
│       ├── shared/
│       │   └── skin_tone.py             # EXTRACTED: single source of truth, importable by notebooks too
│       └── main.py                      # orchestrator, unchanged logic
├── tools/
│   └── visualize_landmark_npy.py   # keep as ad-hoc script; parametrize CLI args instead of hardcoded paths
├── notebooks/
│   ├── data_audit.ipynb
│   └── preprocessing_experiment.ipynb   # update to import shared/skin_tone.py instead of inline copy
├── tests/
│   └── (see Section I)
├── docs/
│   ├── ARCHITECTURE.md   # corrected to match actual pipeline
│   └── SDD.md             # corrected (InsightFace not YOLO; remove unimplemented Quality Filter or mark as "planned")
└── reports/
```

For each proposed move:

```
FROM: src/*.py (flat)
TO:   src/fer_dataset/pipeline/*.py
WHY:  Currently main.py uses bare `from frame_extractor import FrameExtractor` — this only works
      because src/ is added to sys.path implicitly (likely via running `python src/main.py` from
      src/, or PYTHONPATH). Packaging it properly removes import fragility and makes it importable
      from notebooks/tests without path hacks.
DEPENDENCIES: main.py imports; any notebook that does `sys.path.append("src")` (verify none do —
      notebooks currently reimplement rather than import, per D.1).
RISK: LOW structurally, but MUST verify current import mechanism first (see Questions, Section — 
      this needs verification before executing, since "how does src/main.py currently resolve its
      imports" wasn't fully confirmed by static reading alone).
```

```
FROM: src/landmark_comparison.py (standalone, uncalled)
TO:   src/fer_dataset/analysis/landmark_comparison.py, optionally wired as an optional stage in main.py
WHY:  Currently invisible from the pipeline entry point despite producing committed report assets.
DEPENDENCIES: reads data/intermediate/landmark_features.csv (produced by LandmarkAnalyzer).
RISK: LOW (pure move + optional wiring), SAFE if output files are verified identical.
```

```
FROM: (duplicated) skin-tone/CLAHE logic in notebooks/preprocessing_experiment.ipynb
TO:   src/fer_dataset/shared/skin_tone.py, imported by both landmark_analyzer.py and the notebook
WHY:  Single source of truth for a thesis-relevant heuristic (D.1).
DEPENDENCIES: landmark_analyzer.py, preprocessing_experiment.ipynb.
RISK: MEDIUM — requires confirming the two current implementations are actually identical before
      merging; if they differ, that's a decision requiring your approval on which is canonical.
```

---

## G. Refactoring Roadmap (mapped to REFACTORING_PLAN.md phases)

```
Phase 0 — Baseline (DO NOT MODIFY)
Status: This audit satisfies Phase 0/1 requirements; no files modified.
Relevant files: all of src/, config/, docs/, notebooks/
Required actions: None further; proceed to Phase A once you approve this report.

Phase 1 — Audit
Status: COMPLETE (this document).
Findings: See Sections D, E, J.

Phase 2 — Architecture Audit
Status: COMPLETE. See Sections B, C.

Phase 3 (REFACTORING_PLAN Phase A) — Safe cleanup
Files: .DS_Store, .gitignore, docs/ARCHITECTURE.md, docs/SDD.md, __pycache__ verification
Changes: Remove .DS_Store from tracking; fix docs to match actual pipeline; verify .ipynb_checkpoints
         is gitignored.
Risk: SAFE
Validation: `git status` clean, docs review only, no code execution needed.

Phase B — Configuration
Files: config/config.yaml, face_detector.py, emotion_classifier.py, landmark_analyzer.py
Changes: Wire up currently-dead config keys (face_detection.confidence, expression.confidence_threshold,
         quality.*) OR remove them if genuinely unused; move hardcoded padding/skin-tone thresholds/model
         names into config, set to current hardcoded values.
Risk: MEDIUM (touches HIGH-RISK preprocessing parameters — must set config defaults to CURRENT values,
      not "sensible" ones)
Validation: Full pipeline dry-run on a small debug clip (debug.enabled=true, max_frames=100, already
      supported), diff annotations.csv/landmark_features.csv against a pre-refactor baseline run.

Phase C — Data pipeline / dedup (this repo's biggest actual issue)
Files: landmark_analyzer.py, preprocessing_experiment.ipynb, new shared/skin_tone.py
Changes: Extract skin-tone computation to shared module; import from both places.
Risk: MEDIUM — see F above.
Validation: Confirm extracted function produces identical output to both prior implementations on a
      sample of existing face crops before switching either caller over.

Phase D — Package structure
Files: src/*.py -> src/fer_dataset/pipeline/*.py, tests importability
Changes: Convert to proper package, fix imports, move landmark_comparison.py to analysis/.
Risk: LOW-MEDIUM (mechanical, but must verify current import resolution mechanism first — flagged
      as a question below).
Validation: `python -m fer_dataset.main` (or equivalent) runs end-to-end on debug config, output
      files identical to baseline.

Phase E — N/A (no training loop exists)

Phase F — Evaluation / analysis wiring
Files: main.py, landmark_comparison.py
Changes: Optionally gate landmark_comparison as a config-controlled stage.
Risk: LOW
Validation: Compare landmark_comparison_summary.csv before/after.

Phase G — Experiment traceability
Files: docs/EXPERIMENT.md (currently just an empty template)
Changes: Actually log the experiments already run (frame sampling rate, CLAHE preprocessing test,
      the data audit) using the existing template — this is documentation, not code.
Risk: SAFE

Phase H — Testing
Files: new tests/ (see Section I)
Risk: SAFE (additive only)

Phase I — Documentation
Files: docs/ARCHITECTURE.md, docs/SDD.md, README.md
Risk: SAFE
```

Recommended execution order (safest first): **Phase A (docs/cleanup) → Phase H (add characterization tests BEFORE touching logic) → Phase B (config) → Phase C (dedup) → Phase D (packaging) → Phase F/G (wiring/docs)**. Note this reorders REFACTORING_PLAN's own suggested "Phase A→B→C→D..." slightly by pulling testing earlier, because this repo currently has **zero tests protecting HIGH-RISK preprocessing math**, and Phase C (dedup) is the phase most likely to actually touch that math.

---

## H. Validation Strategy

Because there's no train/eval split to compare against, "baseline" here means: **run the current pipeline on the existing debug-mode clip (or full video) and snapshot the output CSVs/file counts**, then diff after each refactor step.

For each step:
- **Before:** Run `python src/main.py` with `debug.enabled: true` (already limits to 100 frames), save `data/intermediate/annotations.csv`, `data/processed/annotations.csv`, `data/intermediate/landmark_features.csv`, and file counts as the baseline snapshot (copy outside `data/`, since `data/` is gitignored and gets cleared on every run).
- **During:** No behavior should change — same row counts, same labels, same confidence values (floating point tolerance ~1e-6 given identical model weights/versions), same feature values.
- **After:** Diff new run's CSVs against baseline snapshot (`pandas.testing.assert_frame_equal` or a simple row-by-row diff script). Re-run `dataset_report.md` generation and confirm identical numbers.
- **Acceptance criteria:** Byte-identical (or floating-point-tolerance-identical) CSV outputs for any refactor classified SAFE/LOW RISK. Any deviation triggers investigation before commit, per REFACTORING_PLAN Phase 8.

---

## I. Tests to Add (prioritized to protect research validity, not coverage)

1. **`test_skin_tone.py`** — feed a synthetic/fixture image (or a saved real face crop) through `_compute_skin_tone`, assert exact bucket + `L_weighted` value. This is the single highest-value test given D.1/E.
2. **`test_landmark_features.py`** — feed a fixed synthetic 478×2 landmark array through `_compute_features`, assert `brow_lowering_distance`/`lip_corner_distance`/`mouth_openness`/`inter_ocular_distance` match hand-computed expected values. Protects the formulas flagged HIGH RISK in Section E.
3. **`test_label_join.py`** — construct a small annotations DataFrame + face-crop filename list where filename match succeeds for some rows and is absent for others; assert the current fallback behavior (and once flagged issue is resolved, assert the new explicit-failure behavior).
4. **`test_frame_sampling.py`** — given a known `original_fps`/`target_fps`, assert `frame_interval` calculation and that debug `max_frames` cutoff triggers correctly.
5. **`test_dataset_builder.py`** — given a small annotations.csv + directory of dummy face files (some missing), assert correct renumbering, correct skip-if-missing behavior, correct output annotation schema.
6. **Config round-trip test** — once Phase B wires up config values, assert each `FaceDetector`/`EmotionClassifier`/`LandmarkAnalyzer` actually receives and uses the config value (currently nothing verifies this, which is exactly how D.5's dead config went unnoticed).

Not recommended: mocking/testing InsightFace or HSEmotion or MediaPipe model outputs themselves (that's testing third-party model behavior, not this codebase) — instead test everything *around* them (feature math, joins, sampling, config wiring) with fixture data.

---

## J. Dead / Legacy / Unclear Code

**Definitely unused (safe candidates for removal, pending your confirmation):**
- `config.yaml`'s `quality.min_face_size`, `quality.blur_threshold` — no code reads these keys anywhere in `src/`.
- `config.yaml`'s `face_detection.confidence` — `FaceDetector` never receives or uses it (InsightFace uses its own internal default).
- `config.yaml`'s `expression.confidence_threshold` — `EmotionClassifier` never filters/uses it; all predictions are recorded regardless of confidence.
- `config.yaml`'s `output.save_landmarks`, `output.save_csv` — not referenced in `landmark_analyzer.py` (it always saves both).
- `notebooks/.ipynb_checkpoints/data_audit-checkpoint.ipynb` — Jupyter's own autosave artifact, not meaningful source.

**Possibly unused (requires confirmation from you):**
- `src/landmark_comparison.py` — not dead code (clearly run manually, produces committed reports), but disconnected from the declared pipeline. Confirm whether it's still an active part of your workflow or a one-off analysis you're done with.
- `emotion_classifier.py`'s visualization path (`visualize`/`visualization_dir`, lines 86-103) — uses a second InsightFace instance just to draw keypoints. Confirm whether these visualizations (`data/intermediate/landmarks` per config) are still used, since `landmark_analyzer.py` separately produces the "real" 478-point landmarks.

**Legacy (potentially useful but outdated):**
- `docs/ARCHITECTURE.md` / `docs/SDD.md` — describe a Quality Filter + checkpoint system that was apparently planned (see `docs/DEVELOPMENT_ROADMAP.md` Milestone 4) but never implemented. Worth deciding: implement it for real, or update docs to remove it as a "future work" item instead of presenting it as current architecture.
- `docs/EXPERIMENT.md` — template-only, no actual experiments logged despite at least 2 real experiments existing (frame/preprocessing work in the notebooks).

**Unknown (cannot determine from static analysis alone):**
- `tools/visualize_landmark_npy.py` — untracked (`??` in git status), hardcodes a specific frame path (`frame_000043_face02`). Unclear if this is a reusable tool-in-progress or a one-off debug script that happened to get saved into `tools/`. Needs your input on intent (see Section K).
- Whether `src/main.py`'s bare imports (`from frame_extractor import FrameExtractor`, no `src.` prefix) currently work via `cwd`-relative execution, an implicit `sys.path` entry, or a project-level path config not visible in static analysis — this affects how safely Phase D (packaging) can be executed.

---

## K. Questions Requiring Your Decision

1. **`quality.*` config keys and the "Quality Filter" stage in docs**: implement the missing blur/face-size/brightness filtering for real (a genuine feature addition, needs approval since it changes which faces enter the dataset), or strip the dead config keys and correct the docs to drop this stage? This directly affects dataset composition either way.
2. **`landmark_comparison.py`**: is this still an active analysis step you run, or a finished one-off you're fine leaving disconnected/archived?
3. **`tools/visualize_landmark_npy.py`**: intended as a reusable debugging tool (should it take CLI args instead of the hardcoded `frame_000043_face02` path) or a throwaway script that happened to get committed to `tools/`?
4. **Notebook vs. `src/` divergence (D.1)**: if `compute_l_weighted` in the notebook and `_compute_skin_tone` in `landmark_analyzer.py` turn out to differ numerically once diffed, which is the "correct"/canonical one for the thesis narrative — the notebook (since it produced a specific published result) or `src/` (since it's the ongoing pipeline)?
5. **Import mechanism**: how is `src/main.py` currently invoked (bare `python src/main.py` from repo root? `cd src && python main.py`? an editor run config?) — this determines whether Phase D packaging is a trivial rename or requires an entry-point/console-script change. Not discoverable from static files alone.
6. **`face_landmarker.task` in git**: OK to stop tracking it in git (rely on the existing auto-download), or is there a reason (offline reproducibility, pinned model version independent of the Google URL) it's intentionally committed?

---

## L. Proposed Changes to REFACTORING_PLAN.md

No changes to the fundamental refactoring plan are required.

The plan's phase structure (A–I) maps cleanly onto this repository once "Phase E — Training" is recognized as not applicable (there is no training loop) and "Phase C — Data pipeline" is understood to be this repo's actual core deliverable (dataset generation) rather than a preprocessing step feeding a trainer. I'd suggest, as a non-binding recommendation only, moving Phase H (Testing) earlier in the execution sequence for this specific repo, since Phase C here directly touches the HIGH-RISK feature/skin-tone math — but this is a sequencing suggestion, not a change to the plan's scope or objectives.
