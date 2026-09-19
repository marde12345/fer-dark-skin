# Papuan Dataset V2 — Reconnaissance & Proposal

Status: **PROPOSAL — APPROVED (decisions locked below), reconnaissance only, no pipeline code changed yet.**
Scope: Data-side restart (CLAHE + AI-assisted annotation + human verification + subject-independent split) to support later fine-tuning/adaptation for Eastern Papuan FER.

## Approved Decisions (supersede the "Summary — what I'd do next" section below)

1. **Legacy boundary — logical only, no physical move.** `data/1408-1010-intermediate/`, `data/intermediate/`, `data/processed/`, `data/raw/` stay exactly where they are, unmodified. The legacy/V2 separation is enforced by (a) new code only ever writing under `data/papuan_v2/`, and (b) a mandatory out-of-band backup step before any new data-generation code runs — see §11 "Backup requirement," now a hard precondition, not a suggestion.
2. **Experiment namespace — `EXP-PAP-NNN`, approved.** See §9 for the lineage log.
3. **AI-assisted annotation model — not pre-selected.** A pilot annotation/evaluation workflow (§10a) must run first, comparing HSEmotion+CLAHE and ArcFace+LR+CLAHE against independently human-labeled pilot images, before either model is used for larger-scale annotation assistance.

---

## 1. Current Data Flow

```
config/config.yaml
        │
        ▼
FrameExtractor        data/raw/videos/pesta_babi.mp4 -> data/intermediate/frames/*.jpg   (OpenCV, fixed FPS=2)
        │
        ▼
FaceDetector           frames -> data/intermediate/faces/*.jpg   (InsightFace SCRFD "buffalo_l", 20% bbox padding)
        │
        ▼
EmotionClassifier      faces -> data/intermediate/annotations.csv   (HSEmotion ONNX "enet_b0_8_best_vgaf", pseudo-labels + softmax confidence)
        │
        ▼
DatasetBuilder         faces + annotations.csv -> data/processed/images/*.jpg + data/processed/annotations.csv  (renumbered img_NNNNNN.jpg)
        │
        ▼
LandmarkAnalyzer       faces -> data/intermediate/landmarks_468/*.npy + landmark_features.csv (468 MediaPipe pts,
        │                        geometric features, skin_tone heuristic via LAB L-channel)
        ▼
DatasetReport          processed/annotations.csv -> reports/dataset_report.md + plots
```

Separately, `tools/extract_arcface_embeddings.py` + `tools/train_arcface_classifier.py` + `tools/evaluate_arcface_vs_hsemotion.py` form a second-generation, **already-trained** research track: InsightFace ArcFace embeddings → `LogisticRegression` classifier → evaluated against HSEmotion, using `manual_labels_export.csv` as ground truth and `StratifiedGroupKFold` (grouped by frame-index blocks, since there is **no person-ID field**) for leakage control.

**Key facts that shape this proposal:**
- There is **no train/val/test split anywhere in the repo today** (confirmed in README "Future Improvements" and in `docs/REPO_AUDIT_REPORT.md`).
- There is **no person/subject-ID field anywhere** — grouping for CV currently uses frame-index temporal blocks as a proxy, which is not the same guarantee as true subject independence.
- Labels are pseudo-labels from HSEmotion by default; a human-verified subset exists only in `manual_labels_export.csv` (`gt_label` column).
- The pipeline is destructive-by-default: each stage clears its own output directory in `__init__`, and `data/` is entirely gitignored — so **nothing under `data/` is actually version-controlled today**. This matters directly for the "preserve legacy" requirement (see §11).

## 2. Current Legacy Dataset Location

No literal "legacy" folder exists. The de facto legacy/frozen snapshot is:

```
data/1408-1010-intermediate/     # timestamp-named snapshot of a completed run
├── frames/, faces/, landmarks/, landmarks_468/
├── annotations.csv                # HSEmotion pseudo-labels
├── landmark_features.csv          # geometric features + skin_tone
├── manual_labels_export.csv       # human ground truth (gt_label, model_label, confidence, notes, labeled_at)
└── clahe_predictions.csv          # EXP-006 CLAHE re-classification result
```
plus the live/regenerable `data/intermediate/` (same shape, no manual labels) and `data/processed/` (227 flat images, `img_NNNNNN.jpg`, + `annotations.csv`).

Since `data/` is gitignored, **none of this is currently protected by git** — "do not delete/overwrite" has to be enforced by convention/backup, not by version control alone. I flag this explicitly in §11.

## 3. Current Annotation Format

CSV only, no JSON. Three schemas in use:

| File | Columns |
|---|---|
| `*/annotations.csv` | `filename, label, confidence` (HSEmotion pseudo-label) |
| `manual_labels_export.csv` | `filename, gt_label, model_label, confidence, notes, labeled_at` |
| `landmark_features.csv` | `face_filename, dataset_filename, label, skin_tone, L_weighted, brow_lowering_distance, lip_corner_distance, mouth_openness, inter_ocular_distance, iod_px` |
| `clahe_predictions.csv` | `filename, original_label, original_confidence, clahe_label, clahe_confidence, l_weighted, clip_limit_used, label_changed, skin_tone` |

Filename convention: crops `frame_NNNNNN_faceNN.jpg`; processed `img_NNNNNN.jpg`. No expression-per-folder layout (flat images + CSV), which is a convention worth keeping for V2.

## 4. Current Preprocessing Flow

- Face detection/crop: `src/fer_dataset/pipeline/face_detector.py`, InsightFace SCRFD `buffalo_l`, 640×640, 20% padding.
- CLAHE: **exists but is not part of the main pipeline.** Canonical implementation is `tools/realtime_demo/clahe_preprocessing.py` (`compute_l_weighted`, `apply_strategy_b_clahe`), a port of logic originally written inline in `notebooks/preprocessing_experiment_executed.ipynb` for EXP-006. Applied to the LAB L-channel of face crops only, adaptive clip limit `[1.5, 3.5]` from a weighted L-value, `tileGridSize=(8,8)`. It has never been run through the ArcFace track, only re-scored with HSEmotion in the notebook experiment.
- No face alignment stage and no quality filter stage exist in `src/`, despite `config.yaml` having dead `quality.min_face_size` / `quality.blur_threshold` keys (confirmed unused by `docs/REPO_AUDIT_REPORT.md` §D.3/§J and by direct inspection).

## 5. Current Experiment Structure

Two overlapping ID schemes, no code-level `experiments/` folder:
- `EXP-NNN` — entries in `docs/EXPERIMENT.md` (EXP-000 refactor baseline, EXP-005 data audit, EXP-006 CLAHE, EXP-007 ArcFace vs HSEmotion eval, EXP-008 error/skin-tone analysis, EXP-009 final statistical validation).
- `R\d` — research-step labels in docstrings/doc titles (R5 embedding extraction … R9 final validation), overlapping in content with the EXP-NNN docs.

Outputs land in `reports/<experiment-name>/` (self-contained CSV+PNG folders), e.g. `reports/arcface_evaluation/`, `reports/arcface_error_analysis/`, `reports/final_research_validation/`. There is no `E0/E1/E2` numeric convention currently in use — that's new to this proposal (§9), so I'll namespace it clearly to avoid colliding with `EXP-NNN`/`R\d`.

## 6. What Can Be Reused

- **Pipeline stages as-is** for face detection and (optionally) frame extraction — `FaceDetector` (InsightFace SCRFD) is a reasonable, already-working face-crop step for new raw Papuan images too.
- **CLAHE implementation** (`tools/realtime_demo/clahe_preprocessing.py`) — this is exactly what the supervisor asked for (CLAHE-preprocessed input to AI-assisted annotation); it just needs to be promoted from a demo-only tool into a proper pipeline stage/importable module.
- **ArcFace embedding + LogisticRegression classifier tooling** (`tools/extract_arcface_embeddings.py`, `tools/train_arcface_classifier.py`) — directly reusable as the "AI prediction" source for AI-assisted annotation, and later as the E1/E2 baseline model.
- **CSV-based, flat-image annotation convention** — keep the same shape (`filename/image_id, label, confidence, ...`) rather than inventing a new format, just extend columns for provenance (§8).
- **`StratifiedGroupKFold` leakage-avoidance pattern** from `train_arcface_classifier.py` — same idea applies to subject-independent splitting, once a real subject/person ID exists.
- **`tests/` conventions and `uv run pytest`** — extend, don't replace.
- **`docs/EXP-NNN` logging convention** — use it to log the new experiments too, just adding a distinct namespace (§9).

## 7. What Should Remain Untouched

- `data/1408-1010-intermediate/`, `data/intermediate/`, `data/processed/`, `data/raw/videos/pesta_babi.mp4` — the entire legacy dataset tree, byte-for-byte.
- `reports/*` — all existing experiment output folders (arcface_evaluation, arcface_error_analysis, final_research_validation, slide_assets, dataset_report, etc.).
- `dashboard/` — the existing model-comparison dashboard and its data.js.
- `src/fer_dataset/pipeline/*.py` — existing stage classes should not be modified in place; new Papuan-V2 logic should be additive (new modules/CLI entry points), not edits to files whose current output defines the legacy baseline.
- `docs/EXP-000` through `EXP-009` and `R5`–`R9` docs, and `docs/baseline_snapshots/phase0/` (pinned to git commit `f9c9fae`) — historical record, do not edit.
- `tools/train_arcface_classifier.py`'s existing behavior when run against the legacy manual labels — it becomes the literal "existing/pretrained model" evaluated in E1, so its current trained artifact (or a reproducible re-run of it) must stay reproducible as-is.

## 8. Proposed Dataset V2 Structure

```
data/
├── legacy/                          # NEW: explicit, git-tracked-by-convention pointer/copy boundary
│   └── README.md                    # documents that data/intermediate, data/1408-1010-intermediate,
│                                     # data/processed, data/raw are the frozen legacy tree (paths unchanged,
│                                     # not physically moved, to avoid breaking existing tooling paths)
│
└── papuan_v2/
    ├── raw/                         # raw Papuan source images/video, as collected
    ├── faces/                       # face-detected/cropped, via reused FaceDetector
    ├── clahe/                       # CLAHE-preprocessed crops (LAB L-channel, reused clahe_preprocessing.py)
    ├── annotations/
    │   ├── ai_predictions.csv       # AI-Assisted Annotation output (never treated as ground truth)
    │   └── verification_log.csv     # per-review audit trail (who/when/accept-or-correct)
    ├── verified/
    │   └── labels.csv               # final human-verified ground truth (see schema §9 below)
    ├── pilot/                       # NEW: pilot annotation/evaluation workflow (§10a)
    │   ├── images/                  # 100–200 sampled CLAHE images for the pilot
    │   ├── human_labels.csv         # independent human ground truth for the pilot set only
    │   ├── ai_predictions/
    │   │   ├── hsemotion_clahe.csv
    │   │   └── arcface_lr_clahe.csv
    │   └── agreement_report.md + assets/   # metrics comparing each model to human_labels.csv
    ├── audit/
    │   └── distribution_report.md + assets/   # §10 distribution audit outputs
    └── splits/
        ├── train.csv                # image_id + subject_id, subject-independent
        ├── val.csv
        └── test.csv
```

Legacy paths (`data/1408-1010-intermediate/`, `data/intermediate/`, `data/processed/`, `data/raw/`) are **unchanged by this proposal** — no physical move, no rename, no in-place edits. The legacy/V2 boundary is enforced purely by convention: all new code exclusively reads/writes under `data/papuan_v2/`.

Rationale for **not physically moving** `data/intermediate`/`data/processed`/etc. into `data/legacy/`: those paths are hardcoded throughout `config/config.yaml`, `src/fer_dataset/pipeline/*.py`, and several `tools/*.py` scripts. Moving them risks silently breaking reproducibility of the legacy pipeline (exactly the destructive-side-effect risk already flagged in `docs/REPO_AUDIT_REPORT.md` §D.4). Instead, `data/legacy/README.md` documents the existing paths as the frozen boundary, and all new code paths exclusively touch `data/papuan_v2/`. If you'd prefer an actual physical move for cleanliness, that should be a separate, explicitly-approved step with a before/after diff — not bundled into this data-side restart.

## 9. Proposed Annotation Schema

`data/papuan_v2/verified/labels.csv` (final ground truth):

```
image_id            # stable ID, e.g. papuan_v2 crop filename
subject_id          # REQUIRED — person identity; unknown/single-frame-only subjects marked explicitly
expression           # final 7-class (or agreed subset) label
ai_model              # e.g. "hsemotion_clahe", "arcface_lr_clahe" — which model produced ai_prediction
ai_prediction         # raw AI-assisted-annotation output, preserved even after correction
human_verified         # bool
human_corrected        # bool — true if final_label != ai_prediction
final_label            # == expression, kept as an explicit alias for provenance clarity
reviewer_id            # who verified (can be anonymized/coded)
reviewed_at            # ISO timestamp
notes                  # free text
```

`ai_model` + `ai_prediction` + `human_verified` + `human_corrected` + `final_label` are the exact provenance fields requested. `final_label` is always the human-verified value — the AI model output is never written into `final_label` directly, only into `ai_prediction`, enforced by the pilot/annotation tooling (§10a/§10b), not by convention alone.

This directly implements the supervisor's flow (`CLAHE image → AI prediction → Human review → Accept/Correct → Verified final label`) and preserves the AI-vs-human distinction requested. `subject_id` is a **new, mandatory field** — nothing in the legacy pipeline has this, and it's the load-bearing field for §10's subject-independent split, so Papuan image collection/annotation must capture it at collection time (e.g. per-video-segment or per-individual folder naming), not be inferred after the fact.

## 9a. Experiment Lineage (`EXP-PAP-NNN`)

Approved namespace, logged in `docs/EXPERIMENT.md` alongside (never mixed into) the existing `EXP-NNN`/`R\d` entries:

| ID | Stage | Depends on |
|---|---|---|
| `EXP-PAP-001` | Raw collection → face detect → CLAHE (`data/papuan_v2/{raw,faces,clahe}`) | Legacy `FaceDetector`, promoted CLAHE module |
| `EXP-PAP-002` | Pilot annotation set construction + independent human labeling | EXP-PAP-001 output |
| `EXP-PAP-003` | AI-assisted-annotation agreement analysis (HSEmotion+CLAHE vs. ArcFace+LR+CLAHE vs. human pilot labels) | EXP-PAP-002 |
| `EXP-PAP-004` | Annotation-assistant selection decision (documented, not silently chosen by whichever score is higher) | EXP-PAP-003 |
| `EXP-PAP-005` | Full-scale AI-assisted annotation + human verification pass | EXP-PAP-004 |
| `EXP-PAP-006` | Dataset audit (distribution, quality, duplicates) | EXP-PAP-005 |
| `EXP-PAP-007` | Subject-independent train/val/test split | EXP-PAP-006 |

E1 (new-dataset baseline eval), E2 (fine-tuning), E3 (further adaptation experiments) remain **out of scope** for this phase and are not assigned `EXP-PAP` IDs yet — they'll follow once `EXP-PAP-007` is complete and reviewed.

## 10. Proposed Implementation Steps (data-side only, this phase)

### 10a. Pilot Annotation/Evaluation Workflow (do this before any large-scale annotation)

This is the immediate next implementation phase, replacing "jump straight to AI-assisted annotation":

```
data/papuan_v2/clahe/*  (from EXP-PAP-001)
        │
        ▼
Sample 100–200 images  →  data/papuan_v2/pilot/images/
        │
        ├──────────────────────────────┐
        ▼                              ▼
Independent human labeling      AI predictions (no access to human labels)
  → pilot/human_labels.csv        ├── HSEmotion + CLAHE  → pilot/ai_predictions/hsemotion_clahe.csv
                                   └── ArcFace+LR + CLAHE → pilot/ai_predictions/arcface_lr_clahe.csv
        │                              │
        └──────────────┬───────────────┘
                        ▼
         Agreement analysis (per model vs. human_labels.csv):
           - accuracy, macro-F1, per-class precision/recall
           - Cohen's kappa (human vs. AI agreement, chance-corrected)
           - confusion matrix per model
           - confidence-vs-correctness breakdown (does high AI confidence predict human agreement?)
                        │
                        ▼
         pilot/agreement_report.md — documents both models' usefulness
         as an ANNOTATION ASSISTANT, not a claim that one model is "better" overall.
                        │
                        ▼
         EXP-PAP-004: explicit, documented decision on which model (if either)
         is used to pre-populate ai_prediction for full-scale annotation (EXP-PAP-005).
         If neither model clears an agreed usefulness bar, fall back to fully
         manual annotation for the affected expressions/subset — that is an
         acceptable outcome, not a failure requiring a workaround.
```

Implementation:
1. `tools/papuan_v2/build_pilot_set.py` — samples 100–200 CLAHE images from `data/papuan_v2/clahe/`, stratified where possible across whatever distribution info is available (source/subject) to avoid an accidentally skewed pilot.
2. Human labeling of the pilot set is done **independently of any AI output** (label first, or at minimum blind to AI predictions at labeling time) — this independence is the control that makes the agreement analysis meaningful, and must be true, not assumed.
3. `tools/papuan_v2/run_ai_predictions.py` — runs both HSEmotion+CLAHE and ArcFace+LR+CLAHE on `pilot/images/`, writing separate CSVs; **never touches `human_labels.csv`**.
4. `tools/papuan_v2/pilot_agreement_report.py` — computes the metrics above, writes `pilot/agreement_report.md` + confusion-matrix assets, following the existing `reports/<experiment>/` output convention.
5. Decision on annotation assistant is a written note in `docs/EXPERIMENT.md` under `EXP-PAP-004`, referencing the agreement report — not an automatic "pick argmax(kappa)" rule, since usefulness-as-an-assistant (e.g. reducing correction workload) matters more than raw accuracy.

### 10b. Subsequent Steps (after the pilot decision, still no fine-tuning)

6. Write `data/legacy/README.md` documenting the legacy tree as a **logical, not physical**, boundary — explicitly states legacy paths (§2) are unchanged and gitignored, and links to the backup requirement in §11.
7. Scaffold `data/papuan_v2/{raw,faces,clahe,pilot,annotations,verified,audit,splits}/` (empty, `.gitkeep`), if not already created in 10a.
8. Promote `tools/realtime_demo/clahe_preprocessing.py` into an importable module (e.g. `src/fer_dataset/shared/clahe.py`), reused by both the new Papuan pipeline and (optionally, unchanged behavior) the existing realtime demo — mirrors the dedup fix already recommended in `docs/REPO_AUDIT_REPORT.md` §D.1/Phase C.
9. `tools/papuan_v2/ai_assisted_annotate.py` — full-scale annotation using the model selected in EXP-PAP-004, writing `annotations/ai_predictions.csv`; plus a minimal review helper (CSV-driven or notebook-based — no custom UI needed for this phase) producing `verified/labels.csv` with the schema in §9.
10. `dataset_audit.py` — expression distribution, subject distribution, gender distribution (only if metadata available — currently none exists, so this will likely report "not collected" and must say so explicitly rather than fabricate it), source distribution, blur/quality metric, lighting metric, pose estimate (reuse MediaPipe landmarks), duplicate/near-duplicate detection (perceptual hash) — writes `data/papuan_v2/audit/distribution_report.md`.
11. `subject_split.py` — group-based split by `subject_id` (`GroupShuffleSplit` or manual assignment for small subject counts), writing `splits/{train,val,test}.csv`; must assert zero subject overlap across splits as a hard check, not just an informal report.
12. Tests: schema/contract tests for the new CSVs, a split-integrity test, a CLAHE regression test against `clahe_predictions.csv` reference values (see §12 for the full list).

**Explicitly out of scope for this phase:** large-scale annotation before the pilot decision is made and documented, E1 baseline evaluation run, any fine-tuning (E2), oversampling/augmentation/class-weighting (E3), and building a custom annotation-review web UI.

## 11. Potential Risks / Data Leakage Risks

### Backup requirement (hard precondition, not optional)

**`data/` is entirely gitignored** — "do not delete/overwrite" cannot be enforced by git alone, and several existing stage classes clear their own output directories on construction (`docs/REPO_AUDIT_REPORT.md` §D.4). Because the approved legacy boundary (§1) is logical-only — the legacy paths physically remain inside the same `data/` tree that new code will also be writing into — an out-of-band backup of `data/1408-1010-intermediate/`, `data/processed/`, `data/intermediate/`, and `data/raw/` (e.g. zip to external/cloud storage, with a checksum or file-count manifest to verify integrity) **must be taken before running any `EXP-PAP-001`+ code**, not just recommended. All new Papuan V2 tooling must also be written so it only ever constructs/targets paths under `data/papuan_v2/` — never importing or instantiating the legacy pipeline's stage classes against a Papuan config — so an accidental config mix-up can't trigger legacy `clear_directory()` calls.

### Circularity risk — explicit analysis

If the same model that produces AI-assisted annotations is later the model whose adaptation/fine-tuning is evaluated using those same annotations, the evaluation is contaminated: the "baseline" or "improvement" would partly be measuring the model agreeing with itself, not genuine performance on independently-verified ground truth. This is the core reason the pilot workflow (§10a) exists instead of picking a model up front. Concretely, the circularity guards adopted are:

1. **Pilot set is human-labeled independently.** `pilot/human_labels.csv` is produced without reference to any AI prediction (labelers blind to AI output at labeling time), so it is a clean reference, not a self-fulfilling comparison.
2. **AI predictions never modify human ground truth.** `run_ai_predictions.py` (§10a step 3) only ever writes to `pilot/ai_predictions/*.csv`; nothing in the pilot workflow overwrites or merges into `human_labels.csv`.
3. **The final Papuan V2 dataset used for any future model evaluation (E1/E2/E3) must consist of human-verified labels (`final_label` in `verified/labels.csv`), never raw `ai_prediction` values.** This is enforced by keeping the two fields structurally distinct in the schema (§9) rather than collapsing them after annotation.
4. **`ai_model` provenance is retained permanently** in `verified/labels.csv`, so any future analysis can slice results by "was this label AI-suggested-and-accepted vs. AI-suggested-and-corrected vs. fully manual" — this makes latent circularity visible/auditable even if it's later discovered, rather than hidden by discarding the field after review.
5. **Annotation-assistant selection is independent of which model becomes the E1/E2 subject.** EXP-PAP-004's decision should explicitly consider *not* using the same model family for both annotation assistance and later fine-tuning/evaluation subject where practical; if the same family is used anyway (e.g. because it's the only usable assistant), that fact must be stated plainly as a limitation in the thesis, not silently absorbed.
6. **No pilot image may leak into training/annotation-tuning use.** Pilot images are a held-out evaluation set for *choosing the annotation assistant*, not additional annotated training data by default — if any pilot images are later folded into the main verified dataset, they carry their pilot-derived `human_labels.csv` label as `final_label` (never an AI prediction), and must still respect `subject_id` split independence in §10b step 11 like any other verified image.

### Other risks

- **No existing person-ID field** — the ArcFace classifier's current leakage control (`StratifiedGroupKFold` by frame-index block) is a proxy, not true subject independence for the *legacy* dataset; this is a known limitation to state plainly in the thesis, not something to silently fix by relabeling legacy data.
- **CLAHE applied before annotation but must also be defined for the eventual E1/E2/E3 comparison** — since CLAHE vs. original is explicitly listed as an E3 (later) experiment, make sure `papuan_v2/faces/` (non-CLAHE) is retained alongside `papuan_v2/clahe/`, not overwritten, so the "CLAHE vs original" comparison remains possible later without re-running face detection.
- **Distribution audit before more collection** — if audit reveals near-duplicate frames (e.g. consecutive video frames of the same subject/expression), naive per-image subject-independent splitting is necessary but not sufficient; near-duplicates of the same subject must also stay together in the same split (already covered by grouping on `subject_id`, but worth stating as an explicit acceptance check in the split-integrity test, §12).
- **Small subject count risk** — if Papuan data collection yields few unique subjects, a subject-independent 3-way split may leave val/test with very few subjects (high variance metrics). Flag this in the audit report rather than forcing a split that looks balanced but isn't statistically meaningful — this may become a discussion point with your supervisor once real numbers are known.
- **Pilot set size (100–200 images) may be too small for stable per-class metrics** on rare expressions — `pilot_agreement_report.md` should report per-class support counts alongside metrics so low-support classes aren't over-interpreted.

## 12. Tests to Add/Update

New (pytest, `uv run pytest`):
- `test_papuan_clahe.py` — promoted CLAHE module produces same `l_weighted`/output as existing `clahe_predictions.csv` reference rows (regression test against legacy values).
- `test_pilot_independence.py` — asserts `run_ai_predictions.py`'s output writer never opens `human_labels.csv` in write mode, and that `pilot_agreement_report.py` treats `human_labels.csv` as read-only input (guards circularity safeguard #2 in §11).
- `test_pilot_agreement_metrics.py` — feeds a small synthetic human-vs-AI label fixture through the agreement computation, asserts accuracy/macro-F1/kappa match hand-computed expected values.
- `test_papuan_annotation_schema.py` — `verified/labels.csv` contract test (required columns, types, `human_corrected == (final_label != ai_prediction)` invariant, `final_label` never silently equal to a raw unreviewed `ai_prediction` row).
- `test_subject_independent_split.py` — hard assertion of zero `subject_id` overlap across train/val/test; also checks every split is non-empty (given the small-subject-count risk above).
- `test_dataset_audit.py` — smoke test that `dataset_audit.py` runs on a small fixture set and produces the expected report sections (expression/subject/source distribution at minimum; gender/quality/pose sections should degrade gracefully to "not available" rather than erroring when metadata is absent).

No changes needed to existing tests (`test_annotation_alignment.py`, `test_data_contracts.py`, `test_skin_tone.py`, etc.) — they continue protecting the legacy pipeline unchanged.

---

## Summary — immediate next step

Decisions are locked (§ "Approved Decisions" above). The next implementation phase is **§10a only**: back up legacy `data/` out-of-band, scaffold `data/papuan_v2/{raw,faces,clahe,pilot}/`, promote the CLAHE module, build the pilot set, collect independent human labels, run both candidate models, and produce `pilot/agreement_report.md`. I will stop after the agreement report for your review and the `EXP-PAP-004` decision before touching `annotations/`, `verified/`, `audit/`, or `splits/` (§10b) — no large-scale annotation, audit, splitting, evaluation, or fine-tuning code will be written in this phase.

No pipeline or data files were modified in producing this report.
