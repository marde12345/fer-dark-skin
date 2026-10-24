# EXP-PAP-004 — Local Label Studio Setup

Blind human labeling of the 150-image Papuan V2 pilot set
(`data/papuan_v2/pilot/images/`), per
`docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md` §10a.

## Install

Already added to this repo's `uv`-managed environment as a separate
dependency group (not a separate virtualenv, not pip):

```bash
uv add --group labeling label-studio label-studio-sdk
```

Run any Label Studio command through this group:

```bash
uv run --group labeling label-studio ...
```

## 1. Start the local server

Label Studio must be started with local file serving enabled and its
document root set to the repository root, so pilot images can be served
without copying them anywhere. Note the env var names: the **server**
process reads the unprefixed `LOCAL_FILES_SERVING_ENABLED` /
`LOCAL_FILES_DOCUMENT_ROOT` (confirmed by reading
`label_studio/core/settings/base.py`); this is easy to get wrong since
the SDK-side helper in the next step reads a *differently-prefixed*
variable.

```bash
export LATEST_VERSION_CHECK=false      # avoids a slow/hanging outbound update-check call
export COLLECT_ANALYTICS=false
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT="$(pwd)"   # run from the repo root
uv run --group labeling label-studio start --no-browser --port 8080 \
  --username <you>@local.test --password "<a local password>" \
  --user-token "<generate one, e.g. python -c 'import secrets; print(secrets.token_hex(20))'>" \
  --enable-legacy-api-token
```

This starts the server at `http://localhost:8080`, creates a local
SQLite database + media directory under
`~/Library/Application Support/label-studio/` (macOS; XDG data dir on
Linux — outside the repo, never committed), and creates the default user
+ API token from the flags above, so no manual browser sign-up step is
needed. The `--enable-legacy-api-token` flag only takes effect for a
**newly created** organization — if you already started the server once
without it, flip the existing organization's setting instead of
recreating the database:

```bash
uv run --group labeling label-studio shell
# In the shell:
from organizations.models import Organization
org = Organization.objects.first()
org.jwt.legacy_api_tokens_enabled = True
org.jwt.save()
```

## 2. Set your API key (never commit this)

```bash
export LABEL_STUDIO_API_KEY="<the --user-token value from step 1>"
```

Do not put this in any tracked file. It is machine/account-specific.

## 3. Run the setup script

In a second terminal (the server from step 1 keeps running):

```bash
export LABEL_STUDIO_API_KEY="<your token>"
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$(pwd)"   # yes, THIS one IS the LABEL_STUDIO_-prefixed
                                                            # name -- required by the SDK's own
                                                            # connect_local_import_storage() safety
                                                            # check, separate from the server's
                                                            # unprefixed LOCAL_FILES_DOCUMENT_ROOT above.
uv run --group labeling python tools/papuan_v2/setup_label_studio_pilot.py
```

This:
1. Verifies all 150 pilot images on disk exactly match
   `experiments/EXP-PAP-004/pilot_manifest.csv` (no regeneration, no
   resampling).
2. Creates the project `"EXP-PAP-004 Papuan V2 Pilot (Blind)"` if it
   doesn't already exist, or reuses it if it does (idempotent — safe to
   re-run).
3. Configures the label interface: 7 required, single-select expression
   classes (Angry/Disgust/Fear/Happy/Sad/Surprise/Neutral) + an optional,
   separate confidence field (High/Medium/Low) + the annotation
   instructions. No AI prediction, model name, or model confidence is
   ever shown.
4. Connects `data/papuan_v2/pilot/images/` as the project's Local Files
   import storage — Label Studio's local-files-serving view only serves
   a file if it falls under a storage path registered this way; setting
   the server env vars alone enables the *capability* but not any given
   path (confirmed by reading
   `io_storages/localfiles/views.py:localfiles_data`). Idempotent — skips
   if already connected.
5. Imports exactly the 150 pilot tasks (only tasks not already present —
   re-running never creates duplicates).
6. Writes `experiments/EXP-PAP-004/label_studio_metadata.json` with the
   project id and current annotation progress.

Verified end-to-end in this environment: project id `2`, 150/150 tasks
imported, a sample image request
(`/data/local-files/?d=data/papuan_v2/pilot/images/frame_000008_face01.jpg`)
returns `HTTP 200`, and re-running the script twice produces zero
duplicate tasks and zero duplicate storage connections.

## 4. Label

Open `http://localhost:8080`, open the project, and label. Each task
shows only the image, the instructions, the 7 expression choices, and
the optional confidence choices — nothing AI-derived.

## 5. Export (after labeling — not yet)

```bash
export LABEL_STUDIO_API_KEY="<your key>"
uv run --group labeling python tools/papuan_v2/export_label_studio_labels.py
```

Writes `experiments/EXP-PAP-004/label_studio_export.csv` (full
provenance: `experiment_id, image_id, human_label, human_confidence,
annotator_source, human_verified, exported_at`).

To also populate the pipeline's existing `human_labels.csv`
(`image_id, gt_label, labeled_by, labeled_at, notes` — confidence folded
into `notes`, never into `gt_label`):

```bash
uv run --group labeling python tools/papuan_v2/export_label_studio_labels.py --write-human-labels
```

This refuses to run if `human_labels.csv` already has any non-empty
`gt_label` rows (pass `--force` only if you are certain you want to
overwrite existing labeling work).

## Notes

- Images are served locally only, from this machine's filesystem — never
  uploaded to any cloud service.
- No secrets or machine-specific absolute paths are committed; `LABEL_STUDIO_API_KEY`
  and `LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT` must be set fresh in each
  environment that runs these scripts.
- `experiments/EXP-PAP-004/human_labels.csv` is never written by the setup
  script, and is only written by the export script when explicitly asked
  (`--write-human-labels`) — the pilot's independent, empty template is
  never touched by any of this until you have actually labeled the images.

---

## Multi-annotator (Annotator A + Annotator B) setup

### Why Annotator B runs on a SEPARATE server, not a second project

This installed Label Studio (Community edition 1.23.0) has **no
role-based Data Manager restriction** — confirmed by reading
`organizations/models.py`: `OrganizationMember` has no `role` field at
all (that's Enterprise-only). Any member of an organization can open the
Data Manager for **any** project in that organization and see every
existing annotation. A second project in the same organization would
therefore NOT actually isolate Annotator B from Annotator A's results.
The only isolation this edition genuinely supports is a **separate
server process** (separate SQLite DB, separate `--data-dir`, separate
organization) — verified live: Annotator B's server has exactly one
project (its own) and zero knowledge of Project A's existence.

What IS shared safely: the pilot image files on disk
(`data/papuan_v2/pilot/images/`), served read-only to both servers via
Label Studio's local-files mechanism — never copied, moved, or modified.

### 1. Generate the deterministic overlap assignment (once)

```bash
uv run python -c "
import sys; sys.path.insert(0, 'tools/papuan_v2')
from label_studio_config import compute_overlap_assignment, write_annotator_assignment_csv
write_annotator_assignment_csv(compute_overlap_assignment())
"
```

Writes `experiments/EXP-PAP-004/annotator_assignment.csv` (150 rows:
`image_id, annotator_A, annotator_B, overlap`) — Annotator A is always
`true`; Annotator B/`overlap` is a fixed, reproducible 75-image subset
(`random.Random(100).sample()` over the sorted manifest image_id list,
seed distinct from the pilot's own sampling seed). Re-running this
produces the identical 75 image IDs. This file is the single source of
truth for who is assigned what — never re-derive it ad hoc.

### 2. Allow Project A's overlap tasks to accept a second annotation

```bash
export LABEL_STUDIO_API_KEY="<A's token>"
uv run --group labeling python tools/papuan_v2/apply_task_overlap.py
```

Label Studio only keeps offering a task to further annotators until
`task.overlap` annotations exist. Project A's tasks were created with
the default `overlap=1`, so without this step Annotator A's own
submissions would close every task and Annotator B would find nothing
left in the queue. This script PATCHes only the integer `overlap` field
(`2` for the 75 overlap tasks, `1` for the rest) via the REST API — it
re-reads and diffs each task's `annotations` before/after every PATCH
and aborts immediately if anything about them changed, so Task 1's
(or any already-submitted) annotation cannot be silently altered.
Idempotent — already-correct tasks are skipped.

### 3. Start Annotator B's isolated server

```bash
export LATEST_VERSION_CHECK=false COLLECT_ANALYTICS=false
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT="$(pwd)"
uv run --group labeling label-studio start --no-browser --port 8081 \
  --data-dir /path/to/a/separate/data/dir \
  --username <annotator-b-real-email> --password "<a local password>" \
  --user-token "<generate one>" --enable-legacy-api-token
```

`--data-dir` must point somewhere OTHER than Project A's default data
directory (which is `~/Library/Application Support/label-studio/` on
macOS unless `--data-dir` was passed there too) — this is what gives B a
completely separate database/organization.

### 4. Create Annotator B's project + import the 75-image subset

```bash
export LABEL_STUDIO_B_API_KEY="<B's token from step 3>"
export LABEL_STUDIO_B_URL="http://localhost:8081"
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$(pwd)"
uv run --group labeling python tools/papuan_v2/setup_label_studio_annotator_b.py
```

Verifies the 75-image overlap subset against `pilot_manifest.csv`,
creates `"EXP-PAP-004 Overlap (Annotator B)"` with the IDENTICAL label
config as Project A (reused from `label_studio_config.LABEL_CONFIG`, not
retyped), connects the same local-files storage, and imports exactly the
75 overlap tasks. Idempotent.

Have Annotator B log into `http://localhost:8081` with their own
credentials and label via "Label All Tasks." They have no account, no
link, and no path in their own server's UI to Project A or Task 1's
annotation.

### 5. Export both annotators' labels

```bash
export LABEL_STUDIO_API_KEY="<A's token>"
uv run --group labeling python tools/papuan_v2/export_label_studio_labels.py --annotator A
# writes experiments/EXP-PAP-004/label_studio_export.csv (all completed A labels)

export LABEL_STUDIO_B_API_KEY="<B's token>"
uv run --group labeling python tools/papuan_v2/export_label_studio_labels.py --annotator B
# writes experiments/EXP-PAP-004/label_studio_export_annotator_b.csv
```

Both use each server's own `completed_by` user record (resolved to a
real email via `client.get_users()`) as `annotator_source` — never a
hardcoded or faked identity. `--write-human-labels` is only accepted for
`--annotator A` (the full 150-image project); it's rejected for B, since
`human_labels.csv`'s schema expects all 150 pilot images, not a 75-image
subset.

### 6. Human-human agreement (once both exports cover all 75 overlap images)

```bash
uv run --group labeling python tools/papuan_v2/human_agreement_report.py
```

Refuses to run until BOTH exports have a label for every one of the 75
overlap image IDs. Computes raw agreement, Cohen's kappa, a confusion
matrix, and per-class agreement over the overlap subset ONLY — writes
`experiments/EXP-PAP-004/human_human_agreement.json`. Disagreements are
listed, never auto-resolved; adjudication is a separate, later, human
step (`adjudicated: false` always, from this script).

### 7. Dashboard-readiness snapshot (safe to run anytime)

```bash
export LABEL_STUDIO_API_KEY="<A's token>"
export LABEL_STUDIO_B_API_KEY="<B's token, if B's server is up>"
uv run --group labeling python tools/papuan_v2/annotator_progress.py
```

Writes `experiments/EXP-PAP-004/annotator_progress.json` (pilot size,
per-annotator assigned/completed counts, overlap size, and the current
human-human agreement summary once step 6 has run). B's server is
optional/best-effort here — if it isn't reachable yet, those fields are
simply `null`, not an error.
