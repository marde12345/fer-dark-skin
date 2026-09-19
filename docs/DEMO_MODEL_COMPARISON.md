# PLAN — Dashboard Live FER Model Comparison Demo

## 1. Objective

Extend the existing static research dashboard with an interactive,
real-time webcam demonstration of the two FER systems evaluated in R7–R9:

1. HSEmotion — baseline
2. ArcFace + Logistic Regression — proposed approach

The demo must appear INSIDE the existing dashboard as a new section.

The audience should be able to:

- enable the laptop camera
- see the same live input processed by both systems
- see the two model predictions side-by-side
- observe that the two systems may produce different predictions
- stop the camera safely

This is a visual demonstration only.

It must NOT modify the existing research evaluation pipeline or research results.

---

# 2. Existing Dashboard

Before implementation:

1. Inspect the existing dashboard structure.
2. Identify:
   - dashboard/index.html
   - dashboard/dashboard.js
   - dashboard/data.js
   - dashboard/assets/
   - existing CSS
   - sidebar/navigation structure
   - section/card conventions
3. Follow the existing dashboard visual language.

Do NOT redesign the existing dashboard.

Do NOT replace the existing static dashboard.

Add the demo as an additional section.

---

# 3. New Dashboard Section

Add a new navigation item:

    Live Model Demo

Recommended position:

    after Model Comparison

because the logical story becomes:

    Model Comparison
        ↓
    Live Model Demo
        ↓
    Error Analysis

The exact position may follow the existing dashboard structure if another placement is more consistent.

---

# 4. Demo Section

The section should communicate the purpose clearly.

Suggested heading:

    Live Model Comparison

Short explanation:

    See how the two FER approaches respond to the same live camera input.

Small methodological note:

    This is an interactive demonstration, not a formal evaluation.

Avoid technical jargon in the primary UI.

Technical details can be placed inside a collapsible `<details>` section.

---

# 5. Camera Interaction

Use the browser's webcam API where appropriate.

Preferred mechanism:

    navigator.mediaDevices.getUserMedia()

The dashboard should request camera permission only when the user explicitly starts the demo.

Do NOT request camera permission automatically when the dashboard loads.

Initial state:

    Camera not active

Display:

    [Start Camera]

After clicking:

    request webcam permission
    ↓
    initialize video
    ↓
    start model inference
    ↓
    display live comparison

Provide:

    [Stop Camera]

When stopped:

- release the webcam tracks
- stop inference loop
- clear/hide live predictions
- do not continue accessing the camera

---

# 6. Important Architecture Decision

The existing dashboard is a static HTML/CSS/JS dashboard.

Browser JavaScript cannot directly execute the existing Python HSEmotion,
InsightFace, ArcFace, and Logistic Regression pipeline.

Therefore:

DO NOT attempt to simply import the existing Python models into
dashboard.js.

Instead, investigate the simplest architecture that allows the browser
dashboard to communicate with a local Python inference service.

Preferred architecture:

    Browser Dashboard
          │
          │ HTTP/WebSocket
          ▼
    Local Python Demo Server
          │
          ├── HSEmotion
          │
          └── ArcFace + Logistic Regression

The dashboard remains the presentation/UI layer.

Python remains the model inference layer.

---

# 7. Local Inference Service

Create a minimal local inference service for the demo.

Possible structure:

    tools/
        realtime_demo/
            server.py
            inference.py

Use the project's existing Python environment and dependencies.

Do NOT introduce a heavyweight framework unless necessary.

Before selecting the server technology:

1. Inspect currently installed dependencies.
2. Prefer an existing dependency if suitable.
3. If a new dependency is required, explain why before adding it.

Do not modify research dependencies unnecessarily.

---

# 8. Browser ↔ Python Communication

The implementation may use either:

### Option A — WebSocket

    Browser
       ↕
    WebSocket
       ↕
    Python inference server

This is preferred if practical because the demo is continuously streaming
frames and predictions.

### Option B — HTTP frame requests

    Browser
       ↓
    JPEG frame
       ↓
    Python
       ↓
    prediction
       ↓
    Browser

Use this only if it provides a simpler and sufficiently responsive demo.

Do NOT implement both approaches.

Choose the simplest robust architecture.

---

# 9. Same-Frame Requirement

Both models must process the SAME captured frame.

Conceptually:

    frame_t
       │
       ├── HSEmotion
       │
       └── ArcFace + LR

Do NOT capture independent frames for each model.

Do NOT compare predictions generated from different moments.

The visual comparison must represent:

    same input
    → different model
    → different prediction

---

# 10. Model A — HSEmotion

Reuse the same HSEmotion model used in the research pipeline.

Model:

    enet_b0_8_best_vgaf

Pipeline:

    camera frame
        ↓
    face detection
        ↓
    face crop
        ↓
    HSEmotion
        ↓
    expression prediction

Do not substitute another FER model.

---

# 11. Model B — ArcFace + Logistic Regression

Reuse the existing R5–R7 approach.

Pipeline:

    camera frame
        ↓
    face detection
        ↓
    face crop
        ↓
    5-point face landmark detection
        ↓
    ArcFace alignment
        ↓
    ArcFace w600k_r50
        ↓
    512-D embedding
        ↓
    existing Logistic Regression
        ↓
    expression prediction

ArcFace must remain frozen.

Do NOT retrain the classifier.

Do NOT create a new classifier for the demo.

---

# 12. Existing Artifacts

Before implementation, locate and verify:

### HSEmotion

Existing HSEmotion model/artifact.

### ArcFace

    buffalo_l/w600k_r50.onnx

### Logistic Regression

Existing trained classifier artifact from R6/R7.

Confirm:

- path
- loading mechanism
- embedding dimension
- class labels
- preprocessing
- alignment

If the trained Logistic Regression artifact cannot be found or loaded:

STOP and report the blocker.

Do NOT retrain it.

---

# 13. Five-Class Scope

Use the same five-class scope established in R7/R7.5:

    Fear
    Happiness
    Neutral
    Sadness
    Surprise

Do not introduce Angry or Disgust unless the actual classifier artifact
contains those classes.

The UI must display the actual classifier labels.

---

# 14. Face Detection

Initial scope:

    Single face

For each frame:

1. detect face
2. select the primary face
3. use the SAME detected face for both pipelines

Recommended primary face selection:

    largest/highest-confidence face

If no face:

    No face detected

If multiple faces:

    Multiple faces detected

or select the documented primary face consistently.

Do not allow the two models to process different people.

---

# 15. Dashboard Layout

Recommended layout:

    ┌────────────────────────────────────────────────────────┐
    │ Live Model Comparison                                  │
    │ Same camera input → two different FER approaches       │
    │                                                        │
    │                 [ Start Camera ]                       │
    │                                                        │
    ├─────────────────────────┬──────────────────────────────┤
    │ HSEmotion               │ ArcFace + LR                 │
    │ Baseline                │ Proposed Approach            │
    │                         │                              │
    │      LIVE VIDEO         │       LIVE VIDEO             │
    │                         │                              │
    │ Prediction              │ Prediction                   │
    │ NEUTRAL                 │ HAPPINESS                    │
    │ Confidence: 62%         │ Confidence: 48%              │
    └─────────────────────────┴──────────────────────────────┘

The two panels should have equal visual weight.

---

# 16. Video Rendering

Prefer a single camera/video stream as the source.

Do NOT open two independent webcam streams.

The UI can show the same camera image in both panels, with each panel
overlaid with its model's prediction.

If technically necessary, use a shared video source and render it through
two canvas/video presentation layers.

The important point is:

    one camera input
    one frame
    two inference paths

---

# 17. Face Bounding Box

Show the detected face bounding box.

The bounding box should be consistent between the two panels.

If the same detected face is used:

    HSEmotion panel → same face box
    ArcFace panel   → same face box

This helps the audience understand that both models are seeing the same
face.

---

# 18. Prediction Display

Keep the prediction large.

Example:

    PREDICTION

    NEUTRAL

    Confidence: 62%

The model name should be more prominent than technical implementation
details.

Do not show:

- embedding vectors
- 512 individual features
- internal logits
- raw tensor values
- model file paths

These are unnecessary for a conference demo.

---

# 19. Confidence

Display confidence only if the model provides a meaningful prediction
score through its existing inference path.

Call it:

    Confidence

Do NOT call it:

    Certainty

Do NOT claim that confidence is calibrated probability.

---

# 20. Demo Status

Include a small status indicator.

Examples:

    Camera: OFF

    Camera: LIVE

    Processing...

    No face detected

    Model unavailable

Keep the status visually subtle.

---

# 21. Performance

The demo should feel real-time on a normal laptop.

Priorities:

1. camera responsiveness
2. stable inference
3. clear predictions
4. acceptable FPS

Potential optimizations:

- reduce inference frame resolution
- process only one face
- throttle inference FPS
- reuse detection where safe
- avoid unnecessary frame encoding
- avoid disk I/O

Do NOT:

- change model weights
- retrain
- change classifier architecture
- modify research preprocessing without documenting it
- introduce a new model solely for speed

If the real-time demo requires a practical optimization that changes the
formal research pipeline, keep that optimization DEMO-ONLY and clearly
document it.

---

# 22. UI Design

Follow the existing dashboard style.

Maintain:

- minimalist blue visual language
- clean cards
- simple typography
- no gradients
- no glowing AI graphics
- no unnecessary animations
- no emojis
- no decorative "AI" imagery

The demo should look like part of the research dashboard, not a separate
consumer application.

---

# 23. Technical Details

Add a collapsible section:

    Technical details

Containing a concise explanation:

    HSEmotion:
    pretrained expression classifier

    ArcFace + Logistic Regression:
    frozen ArcFace face representation +
    Logistic Regression expression classifier

    Input:
    same live webcam frame

    Scope:
    five expression classes

Do not expose unnecessary implementation details in the primary view.

---

# 24. Research Context Callout

Below the live panels, add a small research-context card.

Example:

    Research context

    Formal evaluation on the common N=135 subset:

    ArcFace + Logistic Regression
    Accuracy: 40.74%

    HSEmotion
    Accuracy: 36.30%

    McNemar p = 0.4614

    The live demo is illustrative and does not replace the formal evaluation.

This connects the live demo to the existing dashboard evidence.

Do NOT state:

    "ArcFace is better"

Instead:

    "ArcFace achieved higher measured accuracy in the formal evaluation,
     but the difference was not statistically significant."

---

# 25. Research Integrity

The demo must remain completely separate from formal evaluation.

It must NOT:

- modify evaluation CSVs
- modify dataset files
- write predictions into experiment reports
- retrain models
- recalculate R7/R8/R9 metrics
- overwrite dashboard/data.js
- change existing experiment results

Live predictions are demonstration outputs only.

---

# 26. Camera Privacy

The camera stream should remain local.

Do not send camera frames to external services.

Do not upload frames to cloud APIs.

Do not save webcam frames to disk by default.

Do not retain frames after the demo is stopped.

If the local Python service receives frames:

    browser → localhost → Python

and not:

    browser → external server

Document this briefly in the demo instructions.

---

# 27. Startup / Usage

The final dashboard should have a simple workflow.

Potentially:

### Terminal 1

    uv run python tools/realtime_demo/server.py

### Browser

Open:

    dashboard/index.html

Then:

    Live Model Demo
        ↓
    Start Camera

If a different startup mechanism is required, document it clearly.

Do not require unnecessary setup steps.

---

# 28. Error Handling

### Camera permission denied

Show:

    Camera permission denied.
    Allow camera access and try again.

### Camera unavailable

Show:

    Camera unavailable.

### Python service unavailable

Show:

    Demo server unavailable.
    Start the local inference server first.

### No face

Show:

    No face detected.

### ArcFace failure

Show:

    ArcFace unavailable

without crashing HSEmotion.

### HSEmotion failure

Show:

    HSEmotion unavailable

without crashing ArcFace.

### Model artifact missing

Show a clear technical startup error.

Never silently substitute another model.

---

# 29. Dashboard Isolation

The rest of the dashboard must remain functional if the demo server is
not running.

Important:

    dashboard opens normally
    ↓
    all static sections work
    ↓
    Live Model Demo shows "Demo server offline"
    ↓
    no JavaScript crash

The live demo is an optional interactive feature.

---

# 30. Validation

Before declaring complete, verify:

## Dashboard

- existing dashboard still loads
- navigation still works
- all existing sections remain functional
- new section appears correctly

## Camera

- camera permission requested only after Start Camera
- camera starts
- camera stops
- webcam tracks are released

## Inference

- HSEmotion loads
- ArcFace loads
- Logistic Regression loads
- both process the same frame
- predictions update

## Face detection

- face box appears
- no-face condition works
- multiple-face condition is handled

## UI

- two panels have equal size
- model names are clear
- predictions are readable
- confidence is displayed appropriately
- FPS/status does not clutter the interface

## Isolation

- no research CSV changes
- no experiment output changes
- no dataset changes
- no model retraining

## Failure handling

Test:

- server offline
- camera denied
- no face
- face leaves frame
- model loading failure

---

# 31. Manual Demo Test

Perform an actual live test.

At minimum test:

1. neutral face
2. smile/happiness
3. transition between expressions
4. deliberately observe a case where models disagree, if it naturally occurs

Do NOT manufacture or cherry-pick a failure.

Record only qualitative observations.

Do not convert the live demo into a new quantitative experiment.

---

# 32. Documentation

Add/update a concise README section explaining:

- purpose
- architecture
- how to start the local inference server
- how to open the dashboard
- camera permission
- controls
- five-class scope
- local-only processing
- demo limitations

Explicitly state:

    This demo is for interactive visualization and is not part of the
    formal R7–R9 statistical evaluation.

---

# 33. Deliverables

Expected:

    dashboard/index.html
    dashboard/dashboard.js
    dashboard/...
    tools/realtime_demo/...

Only modify files necessary for the feature.

Do not restructure unrelated dashboard code.

---

# 34. Final Report

After implementation, report:

## Created

List every new file.

## Modified

List every modified existing file.

## Architecture

Briefly explain:

    Browser dashboard
        ↓
    local inference service
        ↓
    HSEmotion
    ArcFace + Logistic Regression

## Model Artifacts

Report the exact artifacts reused.

## Validation

Report:

- dashboard loading
- camera
- same-frame processing
- face detection
- HSEmotion
- ArcFace + LR
- UI
- error handling
- research isolation

## Performance

Report observed approximate FPS/latency if measured.

Do not turn this into a formal benchmark.

## Known Limitations

Especially:

- single-face scope
- local inference server requirement
- browser camera permissions
- demo is qualitative
- live confidence is not calibration evidence
- live demo is not formal evaluation

Then STOP.

Do not add further features without approval.