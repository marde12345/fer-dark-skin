# Live Model & Preprocessing Demo

A real-time, 2×2 webcam demonstration comparing two FER approaches (HSEmotion baseline vs. ArcFace + Logistic Regression) under two preprocessing conditions (Original vs. CLAHE), with multi-face support, a selectable-face live processing-flow visualization, and dashboard-driven server control, embedded as a new section in the existing research dashboard.

**This demo is for interactive visualization and is not part of the formal R7–R9 statistical evaluation.** CLAHE in this demo is an exploratory preprocessing condition based on the project's CLAHE experiment (EXP-006). The live demo is not a formal evaluation and does not generate research metrics.

## Purpose

Let a live audience see the same camera input, from the same detected face(s), processed four ways at once — two FER models × two preprocessing conditions — and observe that predictions can differ by model and by preprocessing condition. It does not compute any new accuracy, error-rate, or statistical result — those all remain exactly as reported in `docs/RESEARCH_FINDINGS.md` and `dashboard/`.

## Architecture

```
Browser dashboard (dashboard/index.html + dashboard/realtime_demo.js)
        │
        ├── POST /start, /stop, GET /status  →  Lifecycle controller
        │                                        (tools/realtime_demo/launcher.py, 127.0.0.1:8766)
        │                                        controls the inference server's process only
        │
        └── POST /predict (raw JPEG, ~1.5 FPS) →  Inference server
                                                    (tools/realtime_demo/server.py, 127.0.0.1:8765)
                                                         │
                                                         ▼
                                              Shared face detection (ONE call per frame,
                                              InsightFace buffalo_l, up to 3 faces)
                                                         │
                                                    per detected face
                                                         │
                                                  ┌──────┴──────┐
                                                  │             │
                                              Original        CLAHE (tools/realtime_demo/clahe_preprocessing.py,
                                                  │             EXP-006's transform)
                                                ┌─┴─┐         ┌─┴─┐
                                                ▼   ▼         ▼   ▼
                                              HSE  ArcLR    HSE  ArcLR
```

Two distinct local processes, deliberately kept separate:

- **The controller** (`launcher.py`, port 8766) only starts/stops the inference server's process. It does no inference itself.
- **The inference server** (`server.py`, port 8765) does all model inference, unchanged in role from before this enhancement.

Communication for `/predict` is plain HTTP frame-request/response (not WebSocket) — unchanged from the original demo; see `server.py`'s module docstring for the full reasoning (zero new Python dependencies, throttled polling rate doesn't need a persistent socket).

## Enhancement A — CLAHE Before/After Visualization

A small "Live preprocessing preview" card shows two live thumbnails — **Original** and **Processed Face** — generated from the **current** detected face on every inference tick (never a static, pre-generated, or dataset example image).

- The preview is generated for the **primary face only** (Face 1 — see "Multi-Face ordering" below), to keep the widget simple even when multiple people are in frame.
- Both thumbnails are produced by `tools/realtime_demo/inference.py`'s `_encode_thumbnail()`, called on the **exact same** `original_crop` / `clahe_crop` arrays already used for that face's HSEmotion/ArcFace inference — never a second, separately-computed CLAHE call. The transform itself is `tools/realtime_demo/clahe_preprocessing.py`'s `apply_strategy_b_clahe()`, copied verbatim from EXP-006 (see that module for exactly what matches EXP-006 and what's an extension — summarized again below).
- Thumbnails are resized to 96×96px JPEG (quality 70) and sent as base64 data URIs inside the normal `/predict` JSON response — no separate endpoint, no full-resolution image transfer.
- Labeling deliberately says **"Adaptive CLAHE"** / **"Contrast enhancement"**, never "Brightness Adjustment" or "Original → Bright" — CLAHE is a local-contrast transform, not a simple brightness correction, and the UI avoids implying otherwise. Technical parameters (LAB L-channel, adaptive clip limit 1.5–3.5, tile grid 8×8) are shown in small print beneath the preview and in the "Technical details" `<details>` panel, kept out of the main flow for non-technical audiences.

### CLAHE — source and parameters (unchanged from the previous phase)

`tools/realtime_demo/clahe_preprocessing.py` reuses EXP-006's transform **verbatim** (copied, not reimplemented, from `notebooks/preprocessing_experiment_executed.ipynb`): `compute_l_weighted()` + `apply_strategy_b_clahe(img, clip_min=1.5, clip_max=3.5, l_min=60, l_max=220, tileGridSize=(8,8))`, applied to the face **crop** (never the full frame), matching EXP-006 exactly.

**What extends beyond EXP-006 (flagged, not silently done):** EXP-006 only ever tested CLAHE-adjusted crops through **HSEmotion**. CLAHE→ArcFace is a documented extension for this demo, using the identical crop-level transform before ArcFace's own internal alignment — not something EXP-006 itself evaluated. EXP-006's own recorded result found CLAHE did **not** improve HSEmotion's accuracy or false-Angry rate — the live demo does not contradict, confirm, or update that result.

## Enhancement B — Multiple Face Detection

The demo now processes **all faces up to a limit**, instead of refusing with `multiple_faces`.

- **`MAX_DEMO_FACES = 3`** (`tools/realtime_demo/inference.py`) — chosen because each additional face roughly doubles per-frame inference cost (2× HSEmotion calls + 2× ArcFace alignment/embed calls per extra face), and 3 was confirmed responsive on a normal laptop CPU during testing (see "Performance" below).
- **Ordering rule**: faces are sorted **deterministically, left-to-right by bounding-box x1** (leftmost person is always "Face 1"). This is stable across ticks for a given arrangement of people and is the same ordering used for every one of the four panels — "Face 1" in the Original/HSEmotion panel is always the same physical person as "Face 1" in the CLAHE/ArcFace panel.
- If more than 3 faces are detected, the extra faces are **counted, not silently dropped**: the dashboard shows e.g. *"3 faces shown — 2 additional face(s) not processed."*
- **Per-face, per-pipeline failure isolation**: one face's ArcFace (or HSEmotion, or CLAHE) failure is caught and reported for that face/pipeline only — it does not stop processing of the other detected faces or the other three pipelines.
- Single-face behavior is unchanged — with one face in frame, the demo behaves exactly as before this enhancement (one "Face 1" row per panel).

### `/predict` response shape (extended, not replaced)

```json
{
  "status": "ok",
  "faces_detected": 5,
  "faces_processed": 3,
  "faces_truncated": 2,
  "faces": [
    {
      "face_id": 1,
      "bbox": [0.13, 0.15, 0.88, 0.89],
      "original": { "hsemotion": {"available": true, "label": "Neutral", "confidence": 0.62}, "arcface": {...} },
      "clahe":    { "hsemotion": {...}, "arcface": {...} },
      "preprocessing": { "original_crop": "data:image/jpeg;base64,...", "clahe_crop": "data:image/jpeg;base64,..." }
    },
    { "face_id": 2, "bbox": [...], "original": {...}, "clahe": {...}, "preprocessing": {...} }
  ]
}
```

`"preprocessing"` (original/CLAHE crop thumbnails) is present on **every** processed face's entry, not just the primary one — this lets the dashboard's "Live Processing Flow" section (see below) show any selected face's crops without a second request; it costs only a cheap resize+JPEG-encode per face, since the crop and CLAHE arrays are already computed for every face regardless. `"status": "no_face"` is unchanged from before. The old single-face `"multiple_faces"` status no longer occurs — multiple faces are now processed, not rejected.

## Live Processing Flow

A "Live Processing Flow — Face N" panel below the four prediction panels gives a step-by-step, education-focused detail view of exactly one selected face's pipeline, using **only already-computed intermediate data** — no extra detection, cropping, CLAHE computation, or model inference is triggered by this visualization.

```
Camera Frame → Face Detection → Face Crop
                                     │
                        ┌────────────┴────────────┐
                        ▼                          ▼
                    Original                     Adaptive CLAHE
                        │                          │
            ┌───────────┴───────────┐  ┌───────────┴───────────┐
            HSEmotion          ArcFace + LR   HSEmotion    ArcFace + LR
```

- **Step 1 (Camera Frame) and Step 2 (Face Detection)** are drawn **entirely client-side**: the small thumbnail canvases capture directly from the browser's own live `<video>` element (already present locally — never requested from the server just for this visualization) and draw the selected face's bounding box on top, using the same `bbox` coordinates already returned by `/predict`. This adds zero network cost and zero server-side work.
- **Step 3 (Face Crop) and Step 4 (Original / Adaptive CLAHE)** use the `preprocessing.original_crop` / `preprocessing.clahe_crop` thumbnails already described above — the same crop and the same CLAHE transform already used for that face's inference, never recomputed for display.
- **Step 5 (Expression Model)** shows compact text lines ("HSEmotion: Neutral (62%)" / "ArcFace + LR: unavailable") reusing the exact same `original`/`clahe` → `hsemotion`/`arcface` result objects already used to populate the four main panels.
- Each step shows a small ✓ / "unavailable" status, so a failure at any stage (e.g., CLAHE or ArcFace unavailable) is visible, never hidden.
- **Face selection**: if more than one face is detected, small "Face 1" / "Face 2" / "Face 3" buttons appear (only for faces currently present) and switching between them re-renders the flow for that face — the same face IDs used in the four main panels, so "Face 2" in the flow view is always the same person as "Face 2" everywhere else on the page. Only one face's flow is shown at a time — the existing four-panel grid above remains the overview across all detected faces; the flow section is the detail view for one of them.
- The flow section carries its own note: *"This visualization shows the processing path used by the live demo. It is an interactive demonstration and is not part of the formal R7–R9 evaluation."*
- This replaces the earlier, simpler "Live preprocessing preview — Face 1" widget from a prior iteration of this demo, which only ever showed Face 1 and only the CLAHE before/after step — the flow view is a strict superset (any selected face, the full pipeline, not just CLAHE).

## Enhancement C — Start/Stop the Demo Server from the Dashboard

A browser page cannot spawn processes or run shell commands directly (and this implementation deliberately does not attempt any such workaround — no `eval`, no arbitrary command execution, no unsafe endpoint). Instead:

**One command, run once, replaces the previous two-step manual setup:**

```
uv run python tools/realtime_demo/launcher.py
```

This starts a small lifecycle **controller** (127.0.0.1:8766) and opens the dashboard in your default browser automatically. From then on, the dashboard's **"Demo Server"** control row lets you:

- **Start Demo** — asks the controller to start the actual inference server (`server.py`) as a subprocess, and waits (blocking the request, up to 25s) until it responds healthy.
- **Stop Demo** — asks the controller to stop the inference server it started. If the camera is still active, it is stopped first (tracks released) before the server is asked to stop, so the browser never ends up holding a camera connection to a dead backend.
- Status (`●` dot + "Offline" / "Starting..." / "Ready") is polled every 3 seconds.

### Security boundaries (see `launcher.py`'s module docstring for the full reasoning)

- The controller binds to **127.0.0.1 only** — never reachable from another machine.
- It exposes exactly **three fixed operations**: `GET /status`, `POST /start`, `POST /stop`. Request bodies are never read for `/start` or `/stop` — there is no way for any request to influence *what* command runs.
- `/start` always spawns the **exact same hardcoded command** (`uv run python <path to server.py>`, falling back to the current interpreter if `uv` isn't on `PATH`) — this is not a generic "run a command" endpoint.
- `/start` first does a real health-check probe of port 8765; if a server is already responding, it does **not** spawn a duplicate — it just reports the existing one.
- `/stop` only terminates a subprocess **this controller itself spawned** (tracked via its own process handle). If an inference server is running but was started manually in a separate terminal, `/stop` reports that plainly and does **not** attempt to find or kill an arbitrary process bound to port 8765 — that would be exactly the kind of unsafe, overly broad action this design avoids.

### If you prefer the manual two-terminal setup

That still works unchanged — run `uv run python tools/realtime_demo/server.py` yourself, open `dashboard/index.html`, and the dashboard's status polling will detect the running server directly (it falls back to probing port 8765's `/health` endpoint whenever the controller at 8766 isn't reachable) and show "Ready" — the "Start Demo"/"Stop Demo" buttons just won't have a controller to talk to in that case (clicking "Start Demo" without the controller running will report "Controller unavailable").

## How to Run

**1. Build the demo classifier artifact (one-time, or after re-running R5's embedding extraction):**

```
uv run python tools/realtime_demo/build_demo_classifier.py
```

**2. Start everything with one command:**

```
uv run python tools/realtime_demo/launcher.py
```

This opens `dashboard/index.html` in your default browser automatically. In the dashboard, click **"Live Model Demo"** in the sidebar, then **"Start Demo"** (waits ~10–25s for models to load), then **"Start Camera"**.

*(Alternative: skip the launcher and run `uv run python tools/realtime_demo/server.py` directly in a terminal, then open `dashboard/index.html` yourself — see "If you prefer the manual two-terminal setup" above.)*

## Controls

- **Start Demo / Stop Demo** — controls the local inference server's process (Enhancement C, see above).
- **Start Camera** — requests browser camera permission (only at this point, never automatically on page load) and begins sending frames; disabled until the demo server reports "Ready."
- **Stop Camera** — stops the inference loop and releases the webcam tracks immediately.

## Scope and Behavior

- **Five expression classes** for ArcFace + LR (both preprocessing conditions): Fear, Happy, Neutral, Sad, Surprise (the same 5-class scope established in R7/R7.5). HSEmotion's native output classes are shown as-is.
- **Up to 3 simultaneous faces** processed per frame (`MAX_DEMO_FACES`, see Enhancement B); additional faces are detected, counted, and reported as not processed — never silently dropped.
- **Same frame, same faces, all four panels** — every set of predictions shown comes from one captured frame and the same detected face(s), with consistent Face 1/2/3 identifiers across all four panels.
- **Independent per-panel, per-face failure handling** — ArcFace failing only affects ArcFace panels; CLAHE failing only affects CLAHE panels; one face's failure doesn't affect other faces or other panels.

## Privacy

Camera frames are sent from the browser to `127.0.0.1` (your own machine) only, to both the controller (lifecycle commands only, no image data) and the inference server (`/predict`, image data). Nothing is uploaded to any external service. Frames are not written to disk and are not retained after each `/predict` request completes or after the camera is stopped. The small CLAHE preview thumbnails follow the same rule — generated in memory, sent once per tick, never persisted.

## Research Isolation

This demo never modifies any research artifact:

- Does not write to any evaluation CSV, dataset file, or experiment report.
- Does not modify `dashboard/data.js` or any R1–R9 result.
- Does not retrain, fine-tune, or recompute any existing metric.
- Does not generate new accuracy, error-rate, or statistical numbers of any kind — the "Research context" card shows only the existing, unchanged R7–R9 figures.
- Live predictions (including the CLAHE preview thumbnails) are demonstration output only, held in memory, and are not fed back into any research pipeline.

## About the Demo-Only Classifier Artifact (unchanged)

`tools/train_arcface_classifier.py` (R6) only performs cross-validation and never saves a final, loadable model. `tools/realtime_demo/build_demo_classifier.py` fits **one** `LogisticRegression`, with R6's exact hyperparameters and `random_state=42`, on all 135 usable existing embeddings, and saves it with `joblib`. It is explicitly labeled demo-only in its own metadata, never used for or reported as an R6/R7/R8/R9 result, git-ignored, and regenerated by running the build script.

## Known Limitations

- Requires the local inference server running (via the launcher or manually) alongside the dashboard — it is not a fully static feature.
- Maximum 3 simultaneously processed faces; extra faces are reported as not processed, not analyzed.
- The "Live Processing Flow" section shows **one selected face's detail at a time** — it is a detail view, not a second full comparison grid; switch faces with the Face 1/2/3 buttons to inspect a different person.
- The flow visualization, like the rest of the demo, is qualitative and illustrative only — it is not part of, and does not affect, the formal R7–R9 evaluation.
- Multi-face processing increases per-frame latency roughly linearly with face count (see "Performance" in the implementation report) — still within the existing ~600ms polling interval for up to 3 faces in testing, but a very cluttered scene could visibly lag.
- Confidence values are the models' own output scores (softmax for HSEmotion, `predict_proba` for the Logistic Regression classifier) — shown as "Confidence," never claimed to be calibrated probabilities.
- The demo-only Logistic Regression classifier is a fit-once artifact never individually validated by the R6/R7 cross-validation process itself (though it reuses R6's exact hyperparameters and training data).
- CLAHE→ArcFace remains an exploratory extension beyond EXP-006's tested scope (EXP-006 tested CLAHE with HSEmotion only).
- The lifecycle controller (`launcher.py`) can only stop servers it started itself — a manually-started server must be stopped manually (by design, for safety, not a bug).
- This is a qualitative, illustrative demonstration. It is not a new experiment and does not replace or update the formal R7–R9 statistical evaluation shown elsewhere in the dashboard. It cannot establish that CLAHE improves accuracy, that CLAHE improves dark-skin FER, that ArcFace is universally better, that HSEmotion is biased, that CLAHE fixes skin-tone bias, or that one model is objectively better — those all require the formal, already-completed evaluation, not a live example.
