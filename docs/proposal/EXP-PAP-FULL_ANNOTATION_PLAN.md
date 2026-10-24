# Papuan V2 Full Annotation Workflow — Implementation Plan (Design Only)

Status: **PLANNING document. Phase 1 (empirical validation of the architecture below) has since been executed against a throwaway fixture project — see "Phase 1 Validation Results" at the end of this document for what was actually tested and observed.** The design sections below (§1-§13) remain the original plan as written; only the appended results section reflects live testing. No pilot code, pilot data, or pilot Label Studio project/server was modified by Phase 1.

Scope: design the evolution from the EXP-PAP-004 pilot (150 images, 2 human annotators, blind AI-vs-human comparison) into the full Papuan V2 multi-annotator consensus workflow (~600 images, ~3 annotators, AI-assisted, adjudicated). This document does not select HSEmotion vs ArcFace, does not implement majority voting, does not create new Label Studio instances, and does not touch the pilot.

---

## 1. Current Architecture Assessment

### 1.1 What exists on disk right now

```
data/papuan_v2/
├── raw/source_video_manifest.json     # EXP-PAP-001 provenance (video sha256, fps, frame_interval)
├── faces/            645 face crops   (frame_NNNNNN_faceNN.jpg)
├── clahe/             645 CLAHE crops (same filenames, 1:1 with faces/)
└── pilot/images/      150 CLAHE crops (a seeded sample of clahe/, see pilot_manifest.csv)

experiments/EXP-PAP-004/
├── metadata.json                 # pilot-level provenance: sample, preprocessing, both AI models' config
├── pilot_manifest.csv            # image_id, source_face_path, source_clahe_path, pilot_image_path, sample_seed, sampled_at
├── ai_predictions.csv            # image_id, ai_model, ai_prediction, ai_confidence, status, generated_at  (300 rows = 150 × 2 models)
├── human_labels.csv              # image_id, gt_label, labeled_by, labeled_at, notes   — INTENTIONALLY EMPTY (150 blank rows)
├── annotator_assignment.csv      # image_id, annotator_A, annotator_B, overlap  (A=150, B=75 deterministic overlap, seed=100)
├── label_studio_metadata.json    # Project A: id, title, url, labeled_count/remaining_count
├── label_studio_export.csv       # experiment_id, image_id, human_label, human_confidence, annotator_source, human_verified, exported_at
├── annotator_progress.json       # dashboard-ready rollup: assigned/completed per annotator, agreement summary (currently null — B hasn't labeled)
└── report.md                     # human-readable status narrative
```

`tools/papuan_v2/` contains one script per pipeline stage (`build_pilot_source.py`, `sample_pilot.py`, `run_ai_predictions.py`, `init_human_labels_template.py`, `setup_label_studio_pilot.py`, `setup_label_studio_annotator_b.py`, `apply_task_overlap.py`, `export_label_studio_labels.py`, `pilot_agreement_report.py`, `human_agreement_report.py`) plus `label_studio_config.py`, which holds every pure/importable constant and function (label config XML, task-building, overlap-sampling, CSV read/write helpers) — this is the module every new script below should extend, not duplicate.

### 1.2 What the pilot already proves works

- **CLAHE promotion is done and tested** (`src/fer_dataset/shared/clahe.py`, `tests/test_papuan_clahe.py`) — directly reusable, no changes needed.
- **AI prediction generation is done for both candidates** on the full 645-crop pool is *not* yet done — only the 150-image pilot subset has predictions (`ai_predictions.csv`). `run_ai_predictions.py` already contains the correct, tested logic for both candidates (including the fixed direct-embedding ArcFace path that avoids re-detection) — it takes an `--pilot-images-dir`/output-path pair as arguments, so it is already parameterizable to a different image set; it is not pilot-specific by construction.
- **Label Studio scripting patterns are proven**: idempotent project creation, idempotent task import (by `image_id`, never Label Studio's internal ordering), local-files storage connection, label-config reuse via `label_studio_config.LABEL_CONFIG`, real annotator identity resolution via `client.get_users()` (never a hardcoded string), and a live-verified safety pattern for mutating `task.overlap` without touching `annotations` (`apply_task_overlap.py`'s before/after diff check).
- **Two-annotator isolation is proven**: separate Label Studio server processes (separate port, `--data-dir`, DB, organization) are the *only* mechanism in Community 1.23.0 that actually isolates annotators, because `OrganizationMember` has no `role` field — any org member can browse any project's Data Manager and see every existing annotation. This was confirmed by reading `organizations/models.py` and live-verified (Annotator B's server's `/api/projects` lists only its own project).

### 1.3 What the pilot deliberately does NOT have (gaps this plan must fill)

- No `ai_model_version` field, no `prediction_timestamp` distinct from `generated_at`, no explicit link from a prediction row to *which* preprocessing variant produced the input crop (implicit today: always CLAHE, always `pilot/images/`).
- No consensus computation of any kind — `human_labels.csv` has one `gt_label` column, implicitly meaning "the one human label," which cannot represent 3 independent judgments per image.
- No adjudication concept anywhere in code (only `human_agreement_report.py`'s `adjudicated: false` placeholder field, always false, never settable).
- `annotator_assignment.csv`'s schema (`annotator_A: bool, annotator_B: bool, overlap: bool`) encodes "is X assigned," which is boolean-per-annotator — adequate for 2 annotators with partial overlap, but was never designed for "every annotator sees every image," which collapses the `overlap` column to always-true and is a wasted/misleading field in the full-workflow case.
- No shared-instance-with-role-based-queue investigation was ever needed for the pilot (2 annotators, deliberately separate by design) — this plan is the first time "does one shared instance make sense" is a real question.

### 1.4 Corrected assumption: dataset size

The task brief says "approximately 600 face crops." The actual number of face crops already extracted from `pesta_babi.mp4` and CLAHE-processed is **645** (`data/papuan_v2/faces/`, `data/papuan_v2/clahe/`), all already on disk from EXP-PAP-001's pilot-scale run (`max_frames=250`, not the full video). This plan treats **the count as always read from `data/papuan_v2/clahe/` at run time** (`len(list(clahe_dir.glob("*.jpg")))`), never hardcoded as 600 or 645, per the task's explicit constraint. If the full dataset is meant to include more than these 645 (i.e., re-running EXP-PAP-001 without the `max_frames` cap, closer to the ~96-minute source video), that is a **prerequisite decision**, flagged in §11, not assumed by this plan.

---

## 2. Proposed Full Annotation Architecture

### 2.1 High-level pipeline (restated with concrete artifact names)

```
data/papuan_v2/faces/, data/papuan_v2/clahe/         (already exist, EXP-PAP-001 — REUSED, not regenerated)
                    │
                    ▼
   EXP-PAP-010  full_manifest.csv        (ALL crops, not a 150-sample — see §4.1)
                    │
                    ▼
   EXP-PAP-011  full_ai_predictions.csv  (chosen AI model × every image — see §5)
                    │
                    ▼
   EXP-PAP-012  Label Studio project(s)  (3 annotators, every image — see §3, §6)
                    │
                    ▼
   EXP-PAP-013  full_annotations.csv     (per-annotator-per-image rows, exported — see §4.2)
                    │
                    ▼
   EXP-PAP-014  consensus.csv            (per-image consensus/adjudication status — see §7)
                    │
                    ▼
   EXP-PAP-015  final_labels.csv         (image_id → final_label, full provenance — see §4.4)
                    │
                    ▼
   (future, separate task) dataset_audit.py, subject_split.py, fine-tuning
```

This reuses the `EXP-PAP-NNN` numbering convention already established (`docs/EXPERIMENT.md`), continuing from `EXP-PAP-004`'s children onward: **`EXP-PAP-010`+** is proposed as the "full annotation" sub-namespace, deliberately gapped from `005-009` (reserved, unused so far) so the full workflow's lineage reads as a distinct phase from the pilot's `001-004`, without colliding with either.

### 2.2 Directory/namespace separation from the pilot

```
data/papuan_v2/
├── faces/, clahe/                 # SHARED — same crops feed both pilot and full workflow, never duplicated
├── pilot/                         # UNCHANGED — pilot-only, never touched by full-workflow code
└── full/                          # NEW — full-workflow-only artifacts that aren't just "the same crops"
    └── (only if a full-workflow-specific image derivative is ever needed; today none is — full
        annotation reads directly from clahe/, no copy needed, mirroring how pilot/images/ was
        only created because the pilot needed a *sampled subset*; the full workflow needs the
        *entire* clahe/ directory, so a redundant copy would violate the "avoid duplicating
        implementations/data" instinct already applied elsewhere in this repo)

experiments/
├── EXP-PAP-004/                   # UNCHANGED — pilot artifacts, frozen
└── EXP-PAP-01x/                   # NEW — full-workflow artifacts, separate directory per experiment
    ├── full_manifest.csv
    ├── ai_predictions.csv
    ├── annotator_roster.csv
    ├── label_studio_metadata.json
    ├── annotations/
    │   ├── annotator_A.csv
    │   ├── annotator_B.csv
    │   └── annotator_C.csv
    ├── consensus.csv
    ├── adjudication_log.csv
    ├── final_labels.csv
    └── dashboard_snapshot.json
```

This mirrors the existing `data/legacy/` vs `data/papuan_v2/` "logical boundary, no physical duplication of shared assets" pattern already approved for legacy-vs-pilot separation — applied one level deeper (pilot-vs-full).

---

## 3. Label Studio Architecture Recommendation

### 3.1 The decision: **Option A, one shared instance — with a caveat**

For the *full* workflow, recommend **one shared Label Studio instance/project**, not 3 isolated servers. Reasoning:

| Consideration | Pilot (2 annotators) | Full workflow (3 annotators) |
|---|---|---|
| Independence requirement | **Blind** — B must not see A's label before submitting their own, because the *comparison itself* (human-vs-human, then human-vs-AI) is the research output | **Verification** — every annotator is independently judging the same image, but the eventual output is a *consensus*, not a comparison of blindness itself; each annotator's raw judgment still matters and must stay individually attributable, but there is no methodological requirement that annotator C never learns annotator A once submitted |
| What Community 1.23.0 actually restricts | N/A — same constraint applies to both | `OrganizationMember` has no role; no annotator-queue partitioning by role. But it **does** have a real per-task mechanism: `task.overlap` (already used in the pilot to open Task 1 to a second annotator) governs how many independent annotations a task accepts before Label Studio stops offering it. With `overlap = 3` and `maximum_annotations = 3` (or higher) on every task, Label Studio's own task-distribution queue will serve every task to every annotator up to that count — this is a genuine, tested, non-Enterprise mechanism (confirmed via `tasks/models.py`'s `overlap_with_agreement_threshold`/`completed_annotations >= overlap` logic, and already exercised safely by `apply_task_overlap.py` this session). |
| Does a shared instance leak A's label to B before B submits? | Would violate blindness (unacceptable for pilot) | Label Studio's default annotation UI does **not** show a task's existing annotations to an annotator who hasn't submitted their own yet, **provided** `show_collab_predictions` (already forced `False` for AI predictions in the pilot) and, more importantly, **`show_annotation_history`** stays `False` (also already forced `False` in the pilot) and the project does NOT use "review" mode. This needs a live confirmation step before rollout (§11 risk), but nothing found in `projects/models.py` suggests annotators see co-annotator submissions mid-stream by default — the risk is specifically the *reviewer*/*manager* UI, which annotator-role users should not have access to if they're only invited as annotators (not org admins). **This is the one caveat that must be verified live before committing to Option A** — see Phase 1 in §12. |
| Operational complexity | 2 servers already stood up and working | 3 separate servers = 3x credential management, 3x export runs, 3x "is Docker/local-files serving configured right" debugging, and — critically — it would NOT even buy back blindness (since blindness isn't required here), so the complexity has no methodological payoff |
| Reproducible exports / clear identity | Already solved per-server via `client.get_users()` | A single project's `/api/tasks` response already nests every annotation's real `completed_by` — exporting per-annotator subsets from one project's task list is a `groupby` on that field, no worse than merging 3 separate exports |

**Conclusion:** one shared project, `task.overlap = 3` (or `N_annotators`), `maximum_annotations = 3`, annotators added as **Annotator role** users (never Manager/Admin) to that single project, `show_collab_predictions=False`, `show_annotation_history=False`, and — this is the part requiring a live check, not an assumption — confirm that an Annotator-role user's labeling view genuinely never surfaces another annotator's submitted result for a task they haven't yet completed. If that live check fails, fall back to Option B for the full workflow too (isolated servers), which remains a safe, already-proven pattern; the added operational cost is real but bounded, and correctness must win over convenience.

### 3.2 Why this differs from the pilot's own reasoning, explicitly

The pilot's write-up (`README_label_studio.md`) states isolation is required because "Community edition does not provide sufficient per-user isolation for blind independent annotation." That conclusion is **still correct for the pilot** (blindness is the whole point of comparing A vs B before any AI involvement) and **does not automatically transfer** to the full workflow, where the requirement is "3 independently-recorded judgments feeding a consensus," not "3 annotators who must never have any shared platform." Conflating these two would either (a) force 3 servers for no methodological reason, or (b) wrongly conclude Community edition "can't be used" for the full workflow when it likely can, given `overlap`. This distinction should be stated explicitly in whatever document eventually replaces this plan with real work, so a future reader does not assume the pilot's server-isolation choice was a blanket policy for the whole project.

### 3.3 AI-prediction visibility to annotators — the required methodological decision

This is the one open design question this plan does **not** resolve, and should not resolve silently:

**Option 1 — AI prediction hidden from annotators (annotators blind to AI, same as pilot).**
Every annotator's judgment is a fully independent human judgment; AI enters only as a fourth, separate column compared against the human consensus afterward. Cleanest methodological claim ("we compared independent human consensus to AI"), but forfeits the practical benefit that motivated "AI-assisted annotation" in the first place (faster annotation via pre-filled suggestions) — annotators still label from scratch.

**Option 2 — AI prediction shown as a pre-filled suggestion annotators may accept or correct** (Label Studio's native `predictions` mechanism, already present in the API as `task["predictions"]`, distinct from `task["annotations"]` — visible in every task payload already inspected this session, currently always empty since the pilot never imports predictions).
Faster annotation, matches "AI-assisted" framing literally. Risk: anchoring bias — three annotators shown the same AI suggestion are not three independent judgments anymore; measured inter-annotator agreement would be inflated by shared anchoring, not genuine consensus, and this would be a **silent contamination of the human-human agreement metric** unless explicitly flagged.

**Recommendation:** keep annotators blind to the AI prediction during full-dataset labeling too (Option 1), identical in spirit to the pilot's independence guarantee, and treat "AI-assisted" as meaning "AI proposes an initial full-dataset annotation queue/prioritization and a provenance column for later comparison," not "AI pre-fills the human's answer." This preserves the ability to measure genuine human-consensus-vs-AI agreement later (exactly the comparison EXP-PAP-004 was designed to eventually support) without the anchoring confound. **This is a recommendation for you to approve, not a decision this plan makes unilaterally** — if you want Option 2 for annotation-speed reasons, the schema in §4 already accommodates it (the `ai_prediction` column exists independent of whether it's shown in Label Studio), but the methodology section of the eventual research writeup would need an explicit anchoring-bias caveat.

---

## 4. Data / Schema Changes

### 4.1 `full_manifest.csv` (new, EXP-PAP-010)

Analogous to `pilot_manifest.csv` but covering every crop, not a sample:

```
image_id, face_filename, source_face_path, source_clahe_path, dataset_version, generated_at
```

No `sample_seed`/`sampled_at` (there is no sampling — every crop in `data/papuan_v2/clahe/` is included; the row count must be read from the directory, never hardcoded, per the task's explicit instruction). Generation is a straight `sorted(clahe_dir.glob("*.jpg"))` listing — reuses `label_studio_config.load_pilot_manifest`'s CSV-shape conventions but is a new function (`load_full_manifest`) since the row schema differs (no sampling provenance columns).

### 4.2 Per-annotator raw annotation export schema

Reuses the EXISTING `label_studio_export.csv` schema (`experiment_id, image_id, human_label, human_confidence, annotator_source, human_verified, exported_at`) **unchanged** — `export_label_studio_labels.py`'s `export_rows_from_tasks()` already handles multiple annotations per task correctly *for a single annotator's identity* today (it takes the *latest* annotation, appropriate when one annotator submits once). For the full workflow, one project holds 3 annotators' worth of annotations per task; the export step needs a **new grouping mode** — export ALL annotations per task (not just the latest), each tagged with its own `completed_by`-resolved `annotator_source` — rather than 3 separate per-server export runs like the pilot did. Proposed: a new function `export_rows_from_tasks_multi_annotator()` in `export_label_studio_labels.py` (or a new `export_full_annotations.py` script reusing its helpers) that, per task, emits one row per annotation (not one row total), still using the same column schema. This is additive — the pilot's existing single-annotator export path is untouched.

### 4.3 `consensus.csv` (new, EXP-PAP-014) — see §7 for the full consensus design

```
image_id, n_annotators, labels_collected (JSON list or pipe-joined), agreement_status
  (unanimous | majority | no_majority), consensus_label (nullable),
  consensus_rule_version, adjudication_required (bool), computed_at
```

### 4.4 `final_labels.csv` (new, EXP-PAP-015) — the authoritative output feeding dataset audit / splits later

This is the schema the task brief sketched, refined against what already exists:

```
image_id
ai_model                  # nullable; which AI candidate (if any) produced ai_prediction below
ai_model_version           # nullable; e.g. package version pin, or joblib artifact hash — see §5.3
ai_prediction               # nullable; never overwritten once written
ai_confidence                 # nullable
prediction_timestamp            # nullable; when the AI prediction was generated (distinct from any human timestamp)
input_preprocessing               # e.g. "clahe_strategy_b_v1" — links to src/fer_dataset/shared/clahe.py's params, so a future
                                    #  CLAHE-vs-original experiment (already flagged as E3 in the original proposal) can filter by this
annotator_A, annotator_A_confidence, annotator_A_source   # annotator_A_source = real Label Studio identity (email), not a role label
annotator_B, annotator_B_confidence, annotator_B_source
annotator_C, annotator_C_confidence, annotator_C_source
agreement_status            # unanimous | majority | no_majority  (mirrors consensus.csv, denormalized here for convenience)
consensus_label             # nullable — see §7
adjudication_required       # bool
adjudication_label          # nullable — set ONLY by the adjudication step, never inferred
adjudicated_by               # nullable — real identity of the human who adjudicated, never "system"/"AI"
adjudicated_at                 # nullable
final_label                  # the ONE column downstream dataset-audit/split code should ever read
final_label_source            # enum: "consensus" | "adjudication" — reconstructs *how* final_label was produced, per requirement
generated_at
```

Design notes justifying deviations from the brief's sketch:
- **Fixed `annotator_A/B/C` columns, not a long/tidy table**, matches the existing `annotator_assignment.csv`'s wide-per-annotator convention already in this repo (not introduced fresh here) — keeps `final_labels.csv` human-skimmable and matches how `human_labels.csv`/`ai_predictions.csv` are already consumed downstream. The per-annotator *raw* export (§4.2) remains long/tidy (one row per annotation) as the underlying source of truth; `final_labels.csv` is a derived, wide rollup — never hand-edited, always regenerated from §4.2 + §4.3.
- **`final_label` is write-once in spirit, not in mechanism**: nothing in a flat CSV can enforce immutability at the filesystem level, so this must be enforced procedurally, exactly like `human_labels.csv`'s existing "refuses to overwrite existing non-empty `gt_label` without `--force`" pattern (`init_human_labels_template.py`, `export_label_studio_labels.py`'s `write_human_labels_csv`). The final-labels writer must adopt the identical guard.
- **`ai_model`/`ai_model_version` kept nullable** because the AI-assisted step (§5) and the human-annotation step (§6) are decoupled — a full run should be able to proceed even if, for some reason, AI prediction is skipped/delayed for a subset of images (matches the existing `status`/exclusion-reason pattern already used in `ai_predictions.csv` for images where a model produced no usable prediction).

---

## 5. AI-Assisted Annotation Workflow (full dataset)

### 5.1 Reuse, not reimplementation

`tools/papuan_v2/run_ai_predictions.py` already implements both candidates correctly and takes directory arguments (`--pilot-images-dir`, `--output`) rather than hardcoded pilot paths. The full-dataset version is the **same script**, pointed at `data/papuan_v2/clahe/` (the full 645-crop pool) instead of `data/papuan_v2/pilot/images/`, writing to `experiments/EXP-PAP-01x/ai_predictions.csv`. No new prediction logic is needed. What IS new:

### 5.2 Model selection must be config-driven, not hardcoded

Today `run_ai_predictions.py` always runs **both** candidates (appropriate for the pilot, whose whole purpose was comparing them). The full workflow needs to run **only the model EXP-PAP-004 selects** — this must be a parameter (`--model {hsemotion_clahe,arcface_lr_clahe}`), not a code fork, and not decided by this plan. Proposed: extend `run_ai_predictions.py` with a `--models` argument (default: both, for backward compatibility with the pilot's existing invocation) so the exact same script serves both phases, and the full-workflow caller passes `--models hsemotion_clahe` (or whichever EXP-PAP-004 selects) explicitly once that decision is made and documented in `docs/EXPERIMENT.md`.

### 5.3 New provenance fields require a small, additive schema extension

Current `ai_predictions.csv` columns (`image_id, ai_model, ai_prediction, ai_confidence, status, generated_at`) already cover `ai_model`, `ai_prediction`, `ai_confidence`, and a timestamp (`generated_at`, filling the same role as the requested `prediction_timestamp`). Missing, to be added:
- `ai_model_version` — for HSEmotion this is the pinned package version (`hsemotion-onnx==0.3.1`, already recorded once in `metadata.json` but not per-row); for ArcFace+LR it should be a content hash of `tools/realtime_demo/artifacts/arcface_lr_demo_model.joblib` (the trained classifier artifact) so a future retraining of that model doesn't silently invalidate old predictions without a visible version change.
- `input_preprocessing` — a fixed string identifying the CLAHE variant/params used (e.g., `"clahe_strategy_b_v1"`), preparing for the already-flagged-as-future E3 "CLAHE vs original" comparison without requiring a schema change later.
- `source_crop_path` and `clahe_crop_path` — both already exist as separate directories (`data/papuan_v2/faces/`, `data/papuan_v2/clahe/`) with matching filenames; recording both paths per prediction row (not just relying on filename convention) makes "preserve both the CLAHE input and original crop references" (an explicit ask) queryable directly from the predictions CSV rather than reconstructed by convention.

This is a **backward-compatible additive schema change** — old pilot rows in `experiments/EXP-PAP-004/ai_predictions.csv` are untouched; the new columns apply only to the new `experiments/EXP-PAP-01x/ai_predictions.csv`.

---

## 6. Multi-Annotator Workflow

### 6.1 Roster and assignment

New `annotator_roster.csv` (EXP-PAP-01x), replacing the boolean-per-annotator-column pattern of the pilot's `annotator_assignment.csv` (which made sense for "does B get this specific image" but is degenerate when every annotator gets every image):

```
annotator_role, annotator_identity, label_studio_user_id, joined_at
A, <realemail-or-username>, <int>, <iso8601>
B, ...
C, ...
```

Kept deliberately simple: with "every annotator annotates every image," there is no per-image assignment matrix to encode — the only thing worth recording is *who the three annotators are* and their real, resolvable Label Studio identity (continuing the pilot's "never fake annotator IDs" principle). The **image-level completeness** ("has annotator X labeled image Y yet") is already fully derivable from the Label Studio task/annotation API (exactly how `annotator_progress.py` computes `annotator_A_completed`/`annotator_B_completed` today) — no separate assignment CSV is needed to answer that question, avoiding a second source of truth that could drift from Label Studio's actual state.

### 6.2 Task configuration on the shared project

- `task.overlap = 3`, `project.maximum_annotations = 3` (project-level default; per-task override only needed if a future partial-coverage design is introduced, which this plan does not propose).
- Reuse `label_studio_config.LABEL_CONFIG` verbatim (same 7 expression classes, same optional confidence field, same instructions) — no schema change needed to the *labeling interface itself*, only to how many annotations each task accepts and how tasks are imported (all `full_manifest.csv` rows, not a 150-sample).
- Reuse the idempotent `find_or_create_project`/`tasks_missing_from_project` pattern from `label_studio_config.py` and `setup_label_studio_pilot.py` — a new `setup_label_studio_full.py` script, structurally parallel to the existing setup scripts, pointed at `full_manifest.csv` instead of `pilot_manifest.csv`.

### 6.3 Confidence stays separate from the label (unchanged principle, reaffirmed)

Already enforced structurally in the pilot (`Choices name="confidence"` is a separate, optional field; `export_rows_to_human_labels_rows` explicitly folds confidence into `notes`, never into `gt_label`). The full workflow's `final_labels.csv` schema (§4.4) keeps this by construction: `annotator_A_confidence` is a distinct column from `annotator_A`, never merged.

---

## 7. Consensus + Adjudication Workflow

This section proposes a design, explicitly not an implementation (per the stop condition).

### 7.1 Consensus representation

`consensus.csv` (§4.3) stores, per image: the full set of collected labels, an `agreement_status` enum, and a nullable `consensus_label`. The enum has three states, matching the brief's own worked examples exactly:

- `unanimous` — all N annotators gave the same label. `consensus_label` = that label.
- `majority` — a strict majority (more than half) agree; `consensus_label` = the majority label. For N=3, this means 2-of-3 agreement (the brief's `Fear, Fear, Surprise → Fear` example).
- `no_majority` — no label has a strict majority (for N=3, all three different). `consensus_label` = null, `adjudication_required` = true.

### 7.2 Is majority vote appropriate? — recommendation, not a decision

For N=3 with 7 possible classes, majority vote (≥2-of-3) is a reasonable default **because it's the simplest rule that matches the brief's own worked examples** and requires no weighting scheme to justify. Two caveats to flag for your explicit approval before implementation:
- **Ties are impossible to misinterpret with N=3** (you can never get exactly 1.5 votes), which is precisely why 3 annotators — not 2 or 4 — was chosen; this is worth stating as a deliberate design reason in the eventual methodology write-up, not just an operational default.
- **If a 4th annotator is ever added later** (not currently planned, but worth flagging so the schema doesn't need rework), majority vote at N=4 can produce a genuine 2-2 tie with no majority — the `no_majority`/adjudication-required path already handles this correctly without any code change, since it's defined as "no label has a strict majority," not "exactly N=3."

### 7.3 Should confidence affect consensus, or remain metadata-only?

**Recommendation: metadata-only, does not affect the consensus computation.** Rationale: the brief explicitly warns "Do not treat confidence as the ground-truth class" and separately asks "Whether confidence should affect consensus or only be metadata" as an open question — but letting confidence *weight* the vote (e.g., a "High"-confidence vote counting more than a "Low"-confidence one) reintroduces exactly the kind of implicit, hard-to-audit rule the rest of this plan is trying to avoid (majority vote is auditable by inspection; confidence-weighted vote requires re-deriving the weighting formula to understand any given consensus_label). Confidence should instead be a **trigger for adjudication prioritization** — e.g., a `consensus.csv` row that IS unanimous but where all three annotators marked "Low" confidence could be flagged for optional secondary review — but this is a separate, additive signal (`low_confidence_unanimous_flag`, not proposed as a blocking field, just noted as a possible future refinement) rather than something that changes whether adjudication is *required*.

### 7.4 Adjudication mechanism — human-only, explicitly recorded, never overwrites

- Adjudication is triggered exactly when `agreement_status == "no_majority"` (§7.1), or optionally when an operator manually flags a `majority` row for review (e.g., low-confidence majority) — but never automatically decided by any model.
- The adjudication *action* is a human (a fourth reviewer, or one of A/B/C acting as tie-breaker with full visibility of all three original labels — unlike the blind initial annotation, adjudication is explicitly NOT blind, since its entire purpose is to look at the disagreement and resolve it) recording a decision into `adjudication_log.csv`:
  ```
  image_id, adjudicated_by, adjudicated_at, original_labels (all 3, preserved verbatim),
  adjudication_label, adjudication_rationale (free text, optional), previous_final_label (null on first adjudication)
  ```
- Critically: **adjudication never edits `annotator_A/B/C` in `final_labels.csv`** — those columns remain the original, individually-attributed raw judgments forever, satisfying "Human labels must remain individually attributable" and "adjudication cannot silently overwrite original annotations." Only `final_labels.csv`'s `adjudication_label`/`final_label`/`final_label_source` columns are set by this step, and only via the same overwrite-guarded writer pattern already used for `human_labels.csv`.
- AI must never be a tie-breaker input to adjudication — the adjudication log schema has no AI-related column at all, by design, so there's no accidental path for `ai_prediction` to leak into a `no_majority` resolution.

---

## 8. Dashboard Artifacts (schemas only, no UI)

Extending the pilot's proven `annotator_progress.py` pattern (query Label Studio live + read existing JSON/CSV artifacts, write one rollup JSON, never compute anything the underlying artifacts don't already contain) to a new `experiments/EXP-PAP-01x/dashboard_snapshot.json`:

```json
{
  "experiment_id": "EXP-PAP-01x",
  "dataset_version": "papuan_v2_full",
  "total_images": null,                        // read from full_manifest.csv row count, never hardcoded
  "ai_predictions_completed": null,
  "annotator_completed": {"A": null, "B": null, "C": null},
  "human_human_agreement": {
    "pairwise_cohens_kappa": {"A_B": null, "A_C": null, "B_C": null},
    "fleiss_kappa": null,
    "raw_agreement": null,
    "n_disagreements": null
  },
  "consensus_completed": null,
  "adjudication_required": null,
  "adjudication_completed": null,
  "final_labels_completed": null,
  "per_class_distribution": null,                // {label: count}, from final_labels.csv
  "per_class_agreement": null,                   // {label: raw_agreement_when_A_said_this_label}, mirrors pilot's per_class_agreement_given_A
  "ai_vs_human_consensus_agreement": null,        // only meaningful once final_labels.csv exists; separate from human-human agreement
  "generated_at": null
}
```

Fleiss' kappa is new relative to the pilot (which only ever needed pairwise Cohen's kappa for 2 annotators) — `scikit-learn` does not ship Fleiss' kappa directly; `statsmodels.stats.inter_rater.fleiss_kappa` is the standard implementation and would be a new dependency (`uv add statsmodels`) unless a small in-repo implementation is preferred (Fleiss' kappa's formula is short enough to implement in ~20 lines without a new dependency, consistent with this repo's general preference for minimal dependencies — worth an explicit choice, not assumed here).

---

## 9. Experiment / Data Lineage

Continuing the `EXP-PAP-NNN` convention with a dedicated sub-block:

| ID | Stage | Depends on |
|---|---|---|
| `EXP-PAP-010` | Full manifest generation (`data/papuan_v2/clahe/` → `full_manifest.csv`) | EXP-PAP-001 (raw crops already exist) |
| `EXP-PAP-011` | Full-dataset AI prediction (selected model only) | EXP-PAP-010, **EXP-PAP-004's assistant-selection decision** |
| `EXP-PAP-012` | Shared Label Studio project setup, roster, task import (overlap=3) | EXP-PAP-010 |
| `EXP-PAP-013` | Multi-annotator export (per-annotation rows, real identity) | EXP-PAP-012 (annotators have labeled) |
| `EXP-PAP-014` | Consensus computation (majority rule, `no_majority` flagged) | EXP-PAP-013 |
| `EXP-PAP-015` | Adjudication + final label assembly | EXP-PAP-014 (where `adjudication_required`) |
| `EXP-PAP-016` | Dashboard snapshot artifact | EXP-PAP-011, 013, 014, 015 (best-effort on whichever exist) |

`docs/EXPERIMENT.md` gets one new `## EXP-PAP-01x — ...` block per stage, following the exact narrative format already used for `EXP-PAP-001` through the multi-annotator pilot extension (status, what was done, live verification performed, code references) — no new documentation convention needed.

### 9.1 Explicit non-interference with the pilot

- `data/papuan_v2/pilot/` — never read or written by any `EXP-PAP-01x` script.
- `experiments/EXP-PAP-004/*` — never read or written by any `EXP-PAP-01x` script (the *selected AI model identifier*, once EXP-PAP-004 concludes, is a one-time manual parameter passed to `EXP-PAP-011`'s `--models` flag, documented in `docs/EXPERIMENT.md`, not a live dependency that re-reads pilot files).
- Legacy `data/1408-1010-intermediate/`, `data/intermediate/`, `data/processed/`, `data/raw/` — untouched, exactly as already established.
- Both currently-running Label Studio server processes (ports 8080/8081, Projects "EXP-PAP-004 Papuan V2 Pilot (Blind)" and "EXP-PAP-004 Overlap (Annotator B)") are **pilot infrastructure** and must not be reused, repurposed, or have the full-workflow project created inside them — the full workflow's shared project (§3.1) needs its own server or, if reusing port 8080's server process is desired for operational simplicity, at minimum a **new, separate project** within it, never the existing Project 2.

---

## 10. Test Plan (proposed, not implemented)

Mapped to the brief's list, each grounded in an existing test file's pattern where one already exists for the analogous pilot behavior:

| # | Test | Pattern to follow |
|---|---|---|
| 1 | Every full-dataset image assigned to all 3 annotators | New — assert `task.overlap == 3` for every imported task, and that `maximum_annotations == 3` at the project level, mirroring `apply_task_overlap.py`'s live-verification style but as a unit test against a mocked/fixture task list |
| 2 | No image accidentally omitted | New — `set(full_manifest_ids) == set(clahe_dir_filenames)`, same shape as `test_verify_pilot_images_present_passes_on_exact_match` in `tests/test_label_studio_pilot.py` |
| 3 | No duplicate image IDs | New — trivial `len(ids) == len(set(ids))` on `full_manifest.csv` |
| 4 | Annotator identity preserved | Extends `test_export_rows_use_real_email_from_completed_by_dict` / `test_export_rows_resolve_integer_completed_by_via_user_map` (`tests/test_annotator_overlap.py`) to the multi-row-per-task export mode |
| 5 | AI provenance preserved | New — round-trip `final_labels.csv` write/read, assert `ai_model`/`ai_model_version`/`ai_prediction` survive unchanged when later steps (consensus, adjudication) write to *other* columns |
| 6 | Human labels independent from AI metadata | New — assert the multi-annotator export function's source never references `ai_predictions.csv`/`ai_prediction`, same source-inspection technique as `test_run_ai_predictions_never_opens_or_paths_to_human_labels` (`tests/test_pilot_independence.py`) |
| 7 | Consensus is reproducible | New — same `(labels_a, labels_b, labels_c) → consensus_label` input twice yields identical output; pure-function test, same style as `test_human_agreement_perfect_match` |
| 8 | Disagreement is explicitly represented | New — a `no_majority` fixture case (3 distinct labels) asserts `consensus_label is None` and `adjudication_required is True`, mirroring the brief's own worked example |
| 9 | Adjudication cannot silently overwrite original annotations | New — after adjudication, assert `final_labels.csv`'s `annotator_A/B/C` columns are byte-identical to their pre-adjudication values; only `adjudication_label`/`final_label`/`final_label_source` differ |
| 10 | Final label provenance is reconstructable | New — for every row, `final_label_source in {"consensus","adjudication"}` and the corresponding source column (`consensus_label` or `adjudication_label`) actually equals `final_label` |
| 11 | Export does not depend on Label Studio task ordering | Extends the existing pattern already used throughout (`build_tasks`/`local_file_url` keyed by `image_id`, never list position) — the multi-annotator export must key exclusively by `task["data"]["image_id"]`, never `task["id"]`/list index, same principle already tested implicitly by every existing export test's fixture shape |
| 12 | Dashboard artifacts are deterministic | New — `dashboard_snapshot.json` generation twice against the same underlying CSVs/JSON produces identical output except `generated_at`, mirroring how the pilot's `label_studio_metadata.json`/`annotator_progress.json` are already regenerated idempotently today |

New test file proposed: `tests/test_full_annotation_workflow.py`, following the existing convention of one test file per major workflow addition (matches `test_annotator_overlap.py` being added alongside the multi-annotator pilot extension rather than folded into `test_label_studio_pilot.py`).

---

## 11. Risks and Methodological Concerns

1. **Shared-instance annotator-view leakage is unverified, not just assumed safe.** §3.1's recommendation hinges on a live check (does an Annotator-role user's labeling UI ever surface a co-annotator's already-submitted result for an unfinished task) that has not been performed. This must be the first thing validated in Phase 1 (§12), on a small fixture project, before any real full-dataset import — if it fails, the fallback (3 separate servers) is already a proven pattern from the pilot, so there's no schedule risk, only a decision-point.
2. **AI-visibility-to-annotators (Option 1 vs Option 2, §3.3) is a methodology decision, not an engineering one**, and this plan deliberately does not make it. Silently defaulting to Option 2 "for speed" without flagging the anchoring-bias tradeoff would be exactly the "silently convert AI-assisted into AI-generated ground truth" failure mode the brief explicitly warns against.
3. **Dataset size ambiguity (§1.4).** 645 existing crops came from a pilot-scale, capped extraction (`max_frames=250` out of a ~96-minute source video). Whether "the full Papuan V2 dataset" means these same 645 crops, or requires re-running EXP-PAP-001 without the cap (producing a much larger pool), is unresolved and materially changes AI-prediction runtime, annotator workload, and Label Studio task-import scale. This should be confirmed before EXP-PAP-010 begins.
4. **`annotator_assignment.csv`'s schema doesn't extend cleanly to N=3-sees-all** (§6.1) — resolved by not needing a per-image assignment file at all in the full workflow, but worth flagging that this is an intentional *simplification*, not an oversight, since a reviewer comparing the pilot's and full workflow's artifact sets might otherwise expect a parallel file.
5. **Fleiss' kappa dependency choice (statsmodels vs. hand-rolled) is unresolved** (§8) and affects `pyproject.toml`; a small addition either way, flagged so it isn't decided implicitly during implementation.
6. **Confidence-triggered-adjudication (§7.3) is proposed only as a non-blocking future refinement**, not part of this plan's core adjudication trigger — implementing it prematurely would add a second, less-auditable adjudication trigger alongside the primary `no_majority` one, diluting "adjudication_required" as a clean, single-condition field.
7. **The currently-running pilot servers (ports 8080/8081) must not be quietly reused** for the full workflow's shared project — doing so would blur the pilot/full-workflow experiment lineage this plan otherwise keeps clean (§9.1), even though it might seem operationally convenient to "just add one more project" to the already-running port-8080 server.

---

## 12. Exact Files To Be Created/Modified (when implementation is approved)

**New files (create):**
- `tools/papuan_v2/build_full_manifest.py` (EXP-PAP-010)
- `tools/papuan_v2/setup_label_studio_full.py` (EXP-PAP-012)
- `tools/papuan_v2/export_full_annotations.py` (EXP-PAP-013) — or an added mode inside `export_label_studio_labels.py`, decide at implementation time based on how much actually diverges
- `tools/papuan_v2/compute_consensus.py` (EXP-PAP-014)
- `tools/papuan_v2/adjudicate.py` (EXP-PAP-015) — likely a CSV-driven review helper, not a UI, matching the pilot's "no custom annotation-review web UI needed" precedent
- `tools/papuan_v2/full_dashboard_snapshot.py` (EXP-PAP-016)
- `tests/test_full_annotation_workflow.py`
- `experiments/EXP-PAP-010/` … `EXP-PAP-016/` output directories (generated, not hand-authored)

**Modified files (extend, not rewrite):**
- `tools/papuan_v2/label_studio_config.py` — add `load_full_manifest`, and any new pure helpers needed for `overlap=3`/roster logic, alongside (not replacing) the existing pilot functions.
- `tools/papuan_v2/run_ai_predictions.py` — add `--models` selector argument (defaults preserve current pilot behavior).
- `tools/papuan_v2/export_label_studio_labels.py` — add the multi-annotation-per-task export mode as a new function, existing single-annotator path untouched.
- `docs/EXPERIMENT.md` — append `EXP-PAP-010` through `EXP-PAP-016` entries.
- `pyproject.toml` / `uv.lock` — only if Fleiss' kappa dependency (§8, §11.5) is resolved in favor of `statsmodels`.

**Untouched (must remain so):** everything under `data/papuan_v2/pilot/`, `experiments/EXP-PAP-004/`, `data/legacy/`, `data/1408-1010-intermediate/`, `data/intermediate/`, `data/processed/`, `data/raw/`, and the two currently-running pilot Label Studio server processes/projects.

---

## 13. Recommended Implementation Phases

**Phase 0 (prerequisite, blocking everything else):** Resolve the two open decisions this plan flags rather than assumes — (a) EXP-PAP-004's AI-assistant selection (already in progress, blocked on Annotator B's pilot labeling), (b) dataset-size scope (§1.4/§11.3), (c) your explicit choice on AI-visibility-to-annotators (§3.3).

**Phase 1 (small, safe validation before any real-scale work):** Live-verify the shared-instance annotator-isolation assumption (§3.1, §11.1) on a throwaway 2-3-task fixture project with 2 test accounts, before committing to Option A for the real 3-annotator rollout. Cheap to do, de-risks the biggest architectural bet in this plan.

**Phase 2:** `EXP-PAP-010` (full manifest) + `EXP-PAP-011` (full AI predictions, selected model) — both purely reuse existing tested code paths, lowest-risk implementation step.

**Phase 3:** `EXP-PAP-012` (shared project + roster setup) — depends on Phase 1's verification outcome to know whether it's really "shared" or falls back to 3 servers.

**Phase 4:** Annotation period (real, human-paced — not something to schedule tightly).

**Phase 5:** `EXP-PAP-013` (multi-annotator export) → `EXP-PAP-014` (consensus) → `EXP-PAP-015` (adjudication, only for `no_majority` rows) → `EXP-PAP-016` (dashboard snapshot), in that strict dependency order.

**Phase 6 (explicitly out of scope for the eventual implementation task too, not just this plan):** dataset audit, subject-independent split, fine-tuning — unchanged from the original proposal's phasing, still gated on `final_labels.csv` existing and being reviewed by you first.

---

No files outside this document were created or modified. No Label Studio project, task, or server configuration was changed. Both pilot servers (ports 8080/8081) remain exactly as they were at the end of the previous session.

---

## Phase 1 Validation Results (empirical, live-tested)

**Status: Complete.** Executed against a fully isolated, throwaway Label Studio project. Nothing under this section describes the pilot (EXP-PAP-004, Project ID 2, ports 8080/8081), which was verified untouched before and after (see "Pilot preservation" below).

### Environment

- Label Studio Community **1.23.0** (same version as the pilot).
- New, fully isolated server process: **port 8090**, separate `--data-dir` (`/Users/MAC/.claude/jobs/17c23021/tmp/ls_validation/data_dir`, outside the repo), separate SQLite DB, separate organization — never derived from or connected to the pilot's servers.
- Project: **id 1**, title `"PHASE1-VALIDATION (throwaway, not pilot)"`.
- Fixture images: 3 synthetic (colored blocks + noise + a baked-in "FIX01/02/03" text label), generated with `numpy`/`opencv`, stored outside the repo (`.../ls_validation/fixture_images/`) — never copied from `data/papuan_v2/`, never real face data.
- 4 users created: **owner** (`owner@phase1-validation.test`, the server's own `--username` account, used only to inspect/administer) + **Annotator A** (`annotator-a@phase1-validation.test`) + **Annotator B** (`annotator-b@phase1-validation.test`) + **Annotator C** (`annotator-c@phase1-validation.test`), each with their own real Label Studio user id (1/2/3/4) and their own API token, created via Django shell (`User.objects.get_or_create` + `Token.objects.create`), all added to the same organization. Credentials are local-only, throwaway, and were never real/production credentials.

### Test users created

| Role | Email | User ID |
|---|---|---|
| Owner (admin/inspector, not one of the 3 annotators) | `owner@phase1-validation.test` | 1 |
| Annotator A | `annotator-a@phase1-validation.test` | 2 |
| Annotator B | `annotator-b@phase1-validation.test` | 3 |
| Annotator C | `annotator-c@phase1-validation.test` | 4 |

All four authenticated correctly with their own token against `/api/current-user/whoami` (verified live). **Role-permission caveat, confirmed empirically (not just from source reading):** Community 1.23.0 has no enforced "Annotator" role distinct from "Owner" at the `OrganizationMember` level — the distinction here is purely by convention (which account is used for which purpose), not by a platform-enforced permission boundary. This matches what the architecture plan predicted from reading `organizations/models.py`, and is now also confirmed behaviorally: annotator-role tokens *can* reach the Data Manager task-list endpoint (`/api/tasks?project=1`), though — see next section — it does not expose annotation content, only a count.

### Bilingual UI result: **PASS**

Live-fetched the project's `label_config` via `GET /api/projects/1` and confirmed, verbatim on the server: both `<Text name="instructions_en">` and `<Text name="instructions_id">` present; all 7 expression `Choice` values rendered as `"English / Indonesian"` pairs (e.g. `"Happy / Senang"`, `"Fear / Takut"`); all 3 confidence levels likewise bilingual (`"High / Tinggi"`, etc.). Confidence remains a structurally separate, optional `Choices` control from the required `expression` control — never mergeable into one field.

### AI visibility result: **PASS — AI is fully hidden from annotators**

- The label config contains no AI-derived field, value, or model name (checked programmatically: no `ai_prediction`/`ai_model`/`hsemotion`/`arcface`/`model_score`/`confidence_score` substring anywhere in the config).
- `show_collab_predictions=False` and `show_annotation_history=False` confirmed set on the live project.
- The exact task payload an annotator's own token receives from the real labeling-stream endpoint (`GET /api/projects/1/next`, the endpoint the frontend actually calls to render "give me the next task") was fetched with **Annotator B's own token** and inspected: no AI-related substring present anywhere in that JSON response.
- No prediction object was ever imported for this fixture (`task["predictions"]` is `[]` on every task) — the fixture never had an AI prediction to hide in the first place, which is itself the correct configuration for the "AI hidden" design (Option 1 in §3.3 of this plan).

### Overlap = 3 result: **PASS**

All 3 imported tasks came back from Label Studio with `task.overlap == 3` automatically, because the project was created with `maximum_annotations=3` **before** task import (unlike the pilot, which started at the default `maximum_annotations=1` and required a separate post-hoc `apply_task_overlap.py` PATCH step). This is a useful, lower-friction finding for the real full-dataset rollout: **set `maximum_annotations=3` at project-creation time**, and every imported task inherits `overlap=3` for free — no per-task PATCH script needed for the full workflow (unlike the pilot's one-off Task-1 retrofit).

### Critical visibility test result: **Co-annotator annotations are NOT visible before submission — empirically confirmed, not inferred from documentation.**

Test sequence performed exactly as specified:

1. **Annotator A submitted** a deliberately recognizable annotation on Task 1 (`Happy / Senang`, `High / Tinggi`) via `POST /api/tasks/1/annotations/` with A's own token.
2. **Logged in as Annotator B** (B's own token) and fetched the task via the REAL labeling-stream endpoint the frontend uses, `GET /api/projects/1/next` — **before B submitted anything**. Result, inspected field-by-field:
   - `"annotations": []` — empty. A's actual choices (`Happy / Senang`, `High / Tinggi`) are **not present anywhere** in B's view.
   - `"predictions": []`, `"drafts": []` — also empty, confirming no other channel leaked content either.
   - `"total_annotations": 1` — a bare **count** is visible (B can tell *someone* already annotated this task), but **not the content of what they chose**.
3. B submitted their own, deliberately different annotation (`Sad / Sedih`, `Medium / Sedang`).
4. **Logged in as Annotator C** and repeated the same before-submission check — same result (`annotations: []`, no leak), then C submitted a third, deliberately different annotation (`Fear / Takut`, `Low / Rendah`).
5. **Separately checked** whether B's own token could browse A's annotation through any *other* endpoint (not just the labeling-stream one): `GET /api/tasks/1/` and `GET /api/tasks/1/annotations/`, both with B's token, both returned **404 Not Found** (not 403 — Label Studio's queryset for these endpoints appears scoped such that a non-owner org member without explicit Data Manager access simply cannot resolve these object URLs, rather than being shown a permission-denied error). The **only** endpoint that returned any information about Task 1's annotation state to B was the Data Manager list endpoint (`GET /api/tasks?project=1`), and even there, the per-task entries carry only `total_annotations: 1` (a count), never the nested `result`/choices content.

**Conclusion: For this project configuration (annotator accounts as plain organization members, `show_collab_predictions=False`, `show_annotation_history=False`, no reviewer/manager role granted), Label Studio Community 1.23.0's real labeling-stream flow does not expose a co-annotator's submitted annotation content to another annotator before they submit their own.** The only leak is a non-content signal (an annotation-count integer), which does not reveal *what* was selected and is very unlikely to bias a subsequent independent judgment the way seeing the actual label would. This validates §3.1's recommendation: the shared-instance architecture (Option A) is safe to use for the real full-dataset rollout's multi-annotator collection, **under the exact same project settings used in this fixture** (`show_collab_predictions=False`, `show_annotation_history=False`, annotators never granted Manager/Admin/reviewer access, which would surface the full Data Manager UI including per-annotation content).

**Caveat, stated plainly:** this was verified via direct API calls with each user's own token, which exercises exactly what the browser-based labeling UI itself calls (the same `/next` endpoint) — but the actual rendered browser UI was not separately screenshotted/visually inspected in this session. The API-level result is the load-bearing one (the UI cannot show data the API never sent it), so this is considered a sufficient empirical test, not merely "inferred from documentation" — but a final visual sanity check in an actual browser session before real annotators begin is a cheap, recommended confirmation step, not a blocking gap.

### Identity / export result: **PASS**

Final state of Task 1: `total_annotations: 3`, `overlap: 3`. All three annotations, fetched via the owner's account:

| annotation_id | completed_by (real, resolved) | expression | confidence | created_at |
|---|---|---|---|---|
| 1 | `annotator-a@phase1-validation.test` (id 2) | Happy / Senang | High / Tinggi | 2026-09-24T08:30:44Z |
| 2 | `annotator-b@phase1-validation.test` (id 3) | Sad / Sedih | Medium / Sedang | 2026-09-24T08:31:31Z |
| 3 | `annotator-c@phase1-validation.test` (id 4) | Fear / Takut | Low / Rendah | 2026-09-24T08:31:31Z |

No annotation was copied between users (each of the three is deliberately distinct, and each trace back to its own submitter). The new `tools/papuan_v2/validation/export_fixture_annotations.py` script (one row per annotation, keyed by real `completed_by` resolved via `client.get_users()`, never by task-list position) exported exactly these 3 rows correctly. Order-independence was verified both live (the export script sorts output by `(image_id, annotator_identity)`, not task order) and in a unit test (`test_export_output_order_is_deterministic_not_task_list_order`) that feeds the same annotation data in reversed task-list order and confirms identical content.

### Consensus fixture result: **PASS**

`tools/papuan_v2/validation/consensus_fixture.py`'s `compute_consensus()` was run against:
- The brief's three worked examples — all three matched exactly (`unanimous`/`Happy`, `majority`/`Fear`, `no_majority`/`None`+`adjudication_required=True`).
- The REAL live fixture data (A=Happy, B=Sad, C=Fear — deliberately chosen to be three-way distinct for this test) → correctly resolved to `no_majority`, `consensus_label=None`, `adjudication_required=True`.

Confidence and AI prediction are structurally excluded from `compute_consensus()`'s function signature (not just "unused" — there is no parameter for either), verified by a dedicated introspection test.

### Pilot preservation: **VERIFIED UNCHANGED, before and after**

Compared against a baseline snapshot taken immediately before Phase 1 began:

| Check | Before | After |
|---|---|---|
| Ports 8080/8081 listening | yes | yes (unchanged PIDs) |
| Project count on :8080 | 1 (`"EXP-PAP-004 Papuan V2 Pilot (Blind)"`, id 2) | 1 (same) |
| Task 1 `overlap` | 2 | 2 (unchanged) |
| Task 1 annotation content | `Neutral` / `Medium` | `Neutral` / `Medium` (byte-identical) |
| `experiments/EXP-PAP-004/pilot_manifest.csv` MD5 | `c5ec86555bed93c48cc374c74b0a80e3` | same |
| `experiments/EXP-PAP-004/human_labels.csv` MD5 | `1e3ad03ab920257a55b2cb4b2ad2b2f6` (still empty template) | same |
| `experiments/EXP-PAP-004/ai_predictions.csv` MD5 | `0b8a56623ab7353e5dfc878f9312ecc1` | same |
| Legacy data file counts (`1408-1010-intermediate`/`intermediate`/`processed`/`raw`) | 596/596/24183/2 | 596/596/24183/2 (unchanged) |

No pilot artifact was read-modified or regenerated; the validation project lives entirely on a separate server (port 8090) with a separate database.

### What remains unresolved after Phase 1

1. **Visual/browser confirmation of the API-level visibility finding** — recommended as a cheap final check before real annotators start (see caveat above), not performed in this session (no browser automation was used; all testing was via direct authenticated API calls, which is what actually determines what the UI can show).
2. **AI-visibility-to-annotators (Option 1 vs Option 2, plan §3.3)** — Phase 1 validated that AI is *successfully hidden* under Option 1's design, but the choice between Option 1 and Option 2 itself remains yours to make; this phase did not (and was not asked to) resolve it.
3. **Dataset-size scope** (plan §1.4/§11.3) — still unresolved, unaffected by Phase 1.
4. **EXP-PAP-004's own AI-assistant selection** — still pending Annotator B's pilot labeling; entirely unaffected by, and independent of, this validation phase.
5. **Whether Community edition's per-project member list needs each annotator explicitly added as a "Project Member"** (distinct from "Organization Member") before they can see the project in their own dashboard — in this fixture, all four users were added at the *organization* level and could reach the project directly by ID/URL; a full rollout should double check whether project-level `ProjectMember` records need to be created too for the project to appear in an annotator's own project list, since that wasn't specifically exercised here (all API calls addressed the project by known ID, not discovered via a "my projects" listing call).

### Files created for Phase 1 (all new, nothing modified)

- `tools/papuan_v2/validation/fixture_config.py` — bilingual label config + pure task-building
- `tools/papuan_v2/validation/export_fixture_annotations.py` — multi-annotation-per-task export
- `tools/papuan_v2/validation/consensus_fixture.py` — pure majority-vote consensus function
- `tools/papuan_v2/validation/fixture_export.csv` — the actual exported result from the live 3-annotation test (kept as evidence)
- `tests/test_phase1_validation_fixture.py` — 20 unit tests, all passing

### Recommendation for the next phase

Proceed to plan §12 Phase 2 (`EXP-PAP-010`/`EXP-PAP-011`: full manifest + full AI predictions for the selected model) once EXP-PAP-004's assistant selection is made — Phase 1's findings de-risk plan §12 Phase 1's own validation step (it's now done) and confirm Option A (shared instance) is viable for Phase 3 (`EXP-PAP-012`, real project setup), using the exact same `maximum_annotations=3`-at-creation-time / `show_collab_predictions=False` / `show_annotation_history=False` / organization-member-only-annotators configuration validated here. The one remaining pre-rollout action worth taking (cheap, not blocking): a single real-browser login as one throwaway account to visually confirm finding #1 above before real annotators are recruited.

**Reminder: the throwaway validation server (port 8090) and its 4 test accounts are local-only, disposable, and can be torn down at any time — nothing there needs to be preserved once you've reviewed this report.**
