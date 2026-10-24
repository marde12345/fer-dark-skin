/* Live Model & Preprocessing Demo — dashboard/realtime_demo.js
 *
 * 2x2 comparison: {Original, CLAHE} x {HSEmotion, ArcFace + LR}, now
 * with multi-face support (up to MAX_DEMO_FACES faces, see
 * tools/realtime_demo/inference.py), a live CLAHE before/after preview
 * for the primary face, and dashboard-driven start/stop of the local
 * inference server via a separate lifecycle controller
 * (tools/realtime_demo/launcher.py, 127.0.0.1:8766).
 *
 * Two distinct local services this file talks to:
 *   - CONTROLLER_URL (127.0.0.1:8766) — start/stop/status of the
 *     inference server itself. Optional: if the user started
 *     tools/realtime_demo/server.py manually instead of via
 *     launcher.py, the controller simply won't be reachable and the
 *     "Start Demo"/"Stop Demo" buttons will report that plainly —
 *     "Start Camera" still works as long as the inference server
 *     itself (SERVER_URL) is reachable.
 *   - SERVER_URL (127.0.0.1:8765) — the actual inference server,
 *     unchanged from the original 2-panel demo's architecture (plain
 *     HTTP frame requests, not WebSocket).
 *
 * This file does not touch dashboard.js, data.js, or any research
 * artifact. It is purely additive.
 */
(function () {
  const SERVER_URL = "http://localhost:8765";
  const CONTROLLER_URL = "http://localhost:8766";
  const INFERENCE_INTERVAL_MS = 600; // throttled inference rate (~1.5 FPS), unchanged
  const SERVER_STATUS_POLL_MS = 3000;
  const MAX_DEMO_FACES_DISPLAY_HINT = 3; // must match tools/realtime_demo/inference.py MAX_DEMO_FACES

  const PANELS = [
    { key: "orig-hse", group: "original", model: "hsemotion" },
    { key: "orig-af", group: "original", model: "arcface" },
    { key: "clahe-hse", group: "clahe", model: "hsemotion" },
    { key: "clahe-af", group: "clahe", model: "arcface" },
  ];

  let stream = null;
  let inferenceTimer = null;
  let serverPollTimer = null;
  let inflight = false;
  let cameraActive = false;
  let selectedFaceId = 1;
  let lastFaces = []; // faces array from the most recent /predict response

  // Input mode: "original" | "clahe" | "simulation". Controls which frame
  // is sent to the FER server AND which frame the landmark panel renders,
  // so both outputs consume the same selected input for the active mode.
  let currentMode = "original";
  let simIntensity = 0.5;

  const els = { panels: {} };

  function cacheEls() {
    els.startBtn = document.getElementById("demo-start-btn");
    els.stopBtn = document.getElementById("demo-stop-btn");
    els.status = document.getElementById("demo-status");
    els.serverDot = document.getElementById("demo-server-dot");
    els.serverLabel = document.getElementById("demo-server-label");
    els.serverStartBtn = document.getElementById("demo-server-start-btn");
    els.serverStopBtn = document.getElementById("demo-server-stop-btn");
    els.facesNote = document.getElementById("demo-faces-note");
    els.flowFaceNum = document.getElementById("demo-flow-face-num");
    els.flowFaceSelector = document.getElementById("demo-flow-face-selector");
    els.flowCamera = document.getElementById("demo-flow-camera");
    els.flowDetection = document.getElementById("demo-flow-detection");
    els.flowCrop = document.getElementById("demo-flow-crop");
    els.flowOrigCrop = document.getElementById("demo-flow-orig-crop");
    els.flowClaheCrop = document.getElementById("demo-flow-clahe-crop");
    els.flowStatusCamera = document.getElementById("demo-flow-status-camera");
    els.flowStatusDetection = document.getElementById("demo-flow-status-detection");
    els.flowStatusCrop = document.getElementById("demo-flow-status-crop");
    els.flowStatusOrig = document.getElementById("demo-flow-status-orig");
    els.flowStatusClahe = document.getElementById("demo-flow-status-clahe");
    els.flowOrigHse = document.getElementById("demo-flow-orig-hse");
    els.flowOrigAf = document.getElementById("demo-flow-orig-af");
    els.flowClaheHse = document.getElementById("demo-flow-clahe-hse");
    els.flowClaheAf = document.getElementById("demo-flow-clahe-af");
    PANELS.forEach((p) => {
      els.panels[p.key] = {
        video: document.getElementById("demo-video-" + p.key),
        canvas: document.getElementById("demo-canvas-" + p.key),
        list: document.getElementById("demo-" + p.key + "-list"),
      };
    });
    els.lmkVideo = document.getElementById("lmk-video");
    els.lmkCanvas = document.getElementById("lmk-canvas");
    els.lmkBaseCanvas = document.getElementById("lmk-base-canvas");
    els.lmkError = document.getElementById("lmk-error");
    els.lmkStatus = document.getElementById("lmk-status-text");
    els.lmkExprList = document.getElementById("lmk-expr-list");
    els.lmkInputNote = document.getElementById("lmk-input-note");

    els.modeBtns = Array.from(document.querySelectorAll(".demo-mode-btn"));
    els.modeLabel = document.getElementById("demo-mode-label");
    els.simControls = document.getElementById("sim-controls");
    els.simCard = document.getElementById("sim-card");
    els.simIntensityInput = document.getElementById("sim-intensity");
    els.simIntensityValue = document.getElementById("sim-intensity-value");
    els.simRawVideo = document.getElementById("sim-raw-video");

    els.flowModeLabel = document.getElementById("demo-flow-mode-label");
    els.flowLandmarkInput = document.getElementById("demo-flow-landmark-input");
    els.flowLandmarkCaption = document.getElementById("demo-flow-landmark-caption");
    els.flowStatusLandmark = document.getElementById("demo-flow-status-landmark");
  }

  function setStatus(text) {
    els.status.textContent = "Camera: " + text;
  }

  function clearCanvas(canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  function resetPredictions() {
    PANELS.forEach((p) => {
      const el = els.panels[p.key];
      el.list.innerHTML = "";
      clearCanvas(el.canvas);
    });
    els.facesNote.textContent = "";
    lastFaces = [];
    selectedFaceId = 1;
    resetFlow();
  }

  function resetFlow() {
    clearCanvas(els.flowCamera);
    clearCanvas(els.flowDetection);
    els.flowCrop.removeAttribute("src");
    els.flowOrigCrop.removeAttribute("src");
    els.flowClaheCrop.removeAttribute("src");
    [els.flowStatusCamera, els.flowStatusDetection, els.flowStatusCrop, els.flowStatusOrig, els.flowStatusClahe].forEach(
      (el) => {
        el.textContent = "";
        el.className = "flow-step-status";
      }
    );
    [els.flowOrigHse, els.flowOrigAf, els.flowClaheHse, els.flowClaheAf].forEach((el) => (el.textContent = ""));
    els.flowFaceNum.textContent = "1";
    els.flowFaceSelector.innerHTML = "";
  }

  // ---------------------------------------------------------------
  // Demo server lifecycle (Enhancement C)
  // ---------------------------------------------------------------

  function setServerUi(state) {
    // state: "offline" | "starting" | "ready"
    els.serverDot.className = "demo-server-dot " + state;
    if (state === "ready") {
      els.serverLabel.textContent = "Ready";
      els.serverStartBtn.style.display = "none";
      els.serverStopBtn.style.display = "inline-block";
      els.startBtn.disabled = false;
    } else if (state === "starting") {
      els.serverLabel.textContent = "Starting...";
      els.serverStartBtn.disabled = true;
    } else {
      els.serverLabel.textContent = "Offline";
      els.serverStartBtn.style.display = "inline-block";
      els.serverStartBtn.disabled = false;
      els.serverStopBtn.style.display = "none";
      els.startBtn.disabled = true;
    }
  }

  async function pollServerStatus() {
    try {
      const resp = await fetch(CONTROLLER_URL + "/status");
      if (!resp.ok) throw new Error("controller error");
      const data = await resp.json();
      setServerUi(data.inference_server_running ? "ready" : "offline");
      return;
    } catch (err) {
      // Controller (launcher.py) not reachable -- fall back to probing
      // the inference server directly, in case it was started manually.
    }
    try {
      const resp = await fetch(SERVER_URL + "/health");
      setServerUi(resp.ok ? "ready" : "offline");
    } catch (err) {
      setServerUi("offline");
    }
  }

  async function startDemoServer() {
    setServerUi("starting");
    try {
      const resp = await fetch(CONTROLLER_URL + "/start", { method: "POST" });
      const data = await resp.json();
      if (data.status === "started" || data.status === "already_running") {
        setServerUi("ready");
      } else {
        setServerUi("offline");
        els.serverLabel.textContent = "Failed to start — see terminal";
      }
    } catch (err) {
      // No controller reachable at all -- guide the user to the manual fallback.
      setServerUi("offline");
      els.serverLabel.textContent = "Controller unavailable — run launcher.py or server.py manually";
    }
  }

  async function stopDemoServer() {
    if (cameraActive) {
      stopCamera();
    }
    try {
      const resp = await fetch(CONTROLLER_URL + "/stop", { method: "POST" });
      const data = await resp.json();
      if (data.status === "not_managed") {
        alert(data.message);
      }
    } catch (err) {
      // Controller unreachable; nothing this page can safely do.
    }
    pollServerStatus();
  }

  // ---------------------------------------------------------------
  // Camera + inference (Enhancements A & B)
  // ---------------------------------------------------------------

  function drawFaceBoxes(canvas, video, faces) {
    if (!canvas || !video) return;
    if (!canvas.width || canvas.width !== video.clientWidth) {
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
    }
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!faces) return;
    faces.forEach((face) => {
      if (!face.bbox) return;
      const x = face.bbox[0] * canvas.width;
      const y = face.bbox[1] * canvas.height;
      const w = (face.bbox[2] - face.bbox[0]) * canvas.width;
      const h = (face.bbox[3] - face.bbox[1]) * canvas.height;
      ctx.strokeStyle = "#2f5bd7";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = "#2f5bd7";
      ctx.font = "12px -apple-system, sans-serif";
      const label = "Face " + face.face_id;
      const textWidth = ctx.measureText(label).width;
      ctx.fillRect(x, Math.max(0, y - 16), textWidth + 8, 16);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x + 4, Math.max(12, y - 4));
    });
  }

  async function startCamera() {
    els.startBtn.disabled = true;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    } catch (err) {
      els.startBtn.disabled = false;
      if (err && err.name === "NotAllowedError") {
        setStatus("permission denied — allow camera access and try again");
      } else {
        setStatus("unavailable");
      }
      return;
    }

    PANELS.forEach((p) => {
      els.panels[p.key].video.srcObject = stream;
    });
    if (els.lmkVideo) {
      els.lmkVideo.srcObject = stream;
    }
    if (els.simRawVideo) {
      els.simRawVideo.srcObject = stream;
    }
    els.startBtn.style.display = "none";
    els.stopBtn.style.display = "inline-block";
    els.stopBtn.disabled = false;
    cameraActive = true;
    setStatus("LIVE");

    inferenceTimer = setInterval(runInferenceTick, INFERENCE_INTERVAL_MS);

    // Landmark overlay reuses this same stream -- no second getUserMedia()
    // call. Landmarks for all three input modes now come from the FER
    // server's InsightFace landmark_3d_68 model, returned as part of the
    // same /predict response already fetched for HSEmotion/ArcFace --
    // the overlay/classifier are therefore driven once per FER tick in
    // every mode (see runInferenceTick/updateLandmarkPanel below), not
    // by an independent, faster client-side detection loop as before.
  }

  function stopCamera() {
    if (inferenceTimer) {
      clearInterval(inferenceTimer);
      inferenceTimer = null;
    }
    if (window.LandmarkDemo) {
      window.LandmarkDemo.clear(els.lmkCanvas, els.lmkStatus, els.lmkExprList);
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    PANELS.forEach((p) => {
      els.panels[p.key].video.srcObject = null;
    });
    if (els.lmkVideo) {
      els.lmkVideo.srcObject = null;
    }
    if (els.simRawVideo) {
      els.simRawVideo.srcObject = null;
    }
    if (els.lmkBaseCanvas) clearCanvas(els.lmkBaseCanvas);
    if (els.flowLandmarkInput) clearCanvas(els.flowLandmarkInput);
    if (els.flowLandmarkCaption) els.flowLandmarkCaption.textContent = "";
    if (els.flowStatusLandmark) els.flowStatusLandmark.textContent = "";
    els.startBtn.style.display = "inline-block";
    els.startBtn.disabled = false;
    els.stopBtn.style.display = "none";
    cameraActive = false;
    resetPredictions();
    setStatus("OFF");
  }

  function grabRawCanvas() {
    const video = els.panels["orig-hse"].video;
    if (!video.videoWidth) return null;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas;
  }

  function canvasToBlob(canvas) {
    return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.8));
  }

  function loadImageFromDataUrl(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("image load failed"));
      img.src = dataUrl;
    });
  }

  // fetchPredict(canvas): POSTs one frame to the FER server's unchanged
  // /predict endpoint and returns its parsed JSON, or throws. Shared by
  // the main per-tick request and (in Appearance Simulation mode only)
  // the extra landmarks-for-the-raw-frame request below.
  async function fetchPredict(canvas) {
    const blob = await canvasToBlob(canvas);
    if (!blob) throw new Error("failed to encode frame");
    const resp = await fetch(SERVER_URL + "/predict", {
      method: "POST",
      headers: { "Content-Type": "image/jpeg" },
      body: blob,
    });
    if (!resp.ok) throw new Error("server error " + resp.status);
    return resp.json();
  }

  // extractSelectedFaceLandmarks(data, which, width, height): reads the
  // currently selected face's InsightFace landmarks ("original" or
  // "clahe") from a /predict response and denormalizes the server's
  // [0,1]-normalized coordinates to pixel space for a target of size
  // (width, height). Returns null if unavailable (no face, landmark
  // model unavailable, wrong status) -- never throws.
  function extractSelectedFaceLandmarks(data, which, width, height) {
    if (!data || data.status !== "ok") return null;
    const faces = data.faces || [];
    const face = faces.find((f) => f.face_id === selectedFaceId) || faces[0];
    const norm = face && face.landmarks && face.landmarks[which];
    if (!norm || !width || !height) return null;
    return norm.map((p) => ({ x: p[0] * width, y: p[1] * height }));
  }

  // Builds the frame actually sent to the FER server this tick, according
  // to currentMode. "original" and "clahe" modes send the unmodified raw
  // camera frame unchanged -- the server's own unaltered pipeline already
  // computes both Original and CLAHE predictions/crops (and, now,
  // InsightFace landmarks for both) from that single request.
  //
  // "simulation" mode needs landmarks for the RAW frame to build the
  // synthetic tone-shift mask, but those landmarks only exist in a
  // /predict response -- so this mode makes ONE EXTRA request here,
  // sending the raw frame purely to obtain its landmarks (its FER
  // predictions are computed but not displayed). The simulated frame
  // built from that mask is then sent as the tick's MAIN request (in
  // runInferenceTick below); that response's own landmarks are reused
  // for the overlay/classifier -- no third request is made. This roughly
  // doubles Appearance Simulation mode's per-tick latency (two
  // sequential server round-trips instead of one); Original and CLAHE
  // modes are unaffected (still one request per tick).
  async function buildOutgoingFrame() {
    const rawCanvas = grabRawCanvas();
    if (!rawCanvas) return null;

    if (currentMode !== "simulation") {
      return { sendCanvas: rawCanvas, rawCanvas };
    }

    let rawPositions = null;
    try {
      const rawData = await fetchPredict(rawCanvas);
      rawPositions = extractSelectedFaceLandmarks(rawData, "original", rawCanvas.width, rawCanvas.height);
    } catch (err) {
      rawPositions = null; // server unreachable for this extra request -- simulate with no mask below
    }

    let simCanvas = rawCanvas;
    if (rawPositions && window.AppearanceSimulation) {
      simCanvas = window.AppearanceSimulation.apply(rawCanvas, rawPositions, simIntensity);
    }
    return { sendCanvas: simCanvas, rawCanvas, rawPositions };
  }

  async function runInferenceTick() {
    if (inflight || !stream) return;
    inflight = true;
    try {
      const frame = await buildOutgoingFrame();
      if (!frame) {
        inflight = false;
        return;
      }
      setStatus("Processing...");
      const data = await fetchPredict(frame.sendCanvas);
      renderPrediction(data);
      const lmkResult = await updateLandmarkPanel(data, frame);
      updateLandmarkFlowThumb(lmkResult);
      setStatus("LIVE");
    } catch (err) {
      setStatus("Demo server unavailable — start the local inference server first.");
      if (els.lmkError) {
        els.lmkError.textContent =
          "Landmark panel depends on the FER server response and is paused until it is reachable.";
      }
    } finally {
      inflight = false;
    }
  }

  // ---------------------------------------------------------------
  // Landmark panel (all three input modes -- InsightFace landmarks are
  // now returned by the server's /predict response in every mode)
  // ---------------------------------------------------------------

  function drawBaseImageOnLmkCanvas(source) {
    if (!els.lmkBaseCanvas) return;
    if (!source) {
      if (els.lmkBaseCanvas.width && els.lmkBaseCanvas.height) clearCanvas(els.lmkBaseCanvas);
      return;
    }
    const w = source.naturalWidth || source.width;
    const h = source.naturalHeight || source.height;
    if (!w || !h) return;
    if (els.lmkBaseCanvas.width !== w || els.lmkBaseCanvas.height !== h) {
      els.lmkBaseCanvas.width = w;
      els.lmkBaseCanvas.height = h;
    }
    els.lmkBaseCanvas.getContext("2d").drawImage(source, 0, 0, w, h);
  }

  // Updates the landmark panel for the active mode and returns
  // { usedSource, caption } describing what was actually fed to the
  // landmark overlay this tick, for the pipeline-flow thumbnail below.
  async function updateLandmarkPanel(data, frame) {
    if (!window.LandmarkDemo) {
      return { usedSource: null, caption: "Landmark library unavailable" };
    }

    if (currentMode === "original") {
      const video = els.panels["orig-hse"].video;
      const positions = extractSelectedFaceLandmarks(data, "original", frame.rawCanvas.width, frame.rawCanvas.height);
      await window.LandmarkDemo.renderForVideo(positions, video, els.lmkCanvas, els.lmkError, els.lmkStatus, els.lmkExprList);
      return {
        usedSource: frame.rawCanvas,
        caption: "Live camera frame — InsightFace landmarks from the same /predict response used for the FER panels",
      };
    }

    if (currentMode === "clahe") {
      const faces = data.faces || [];
      const face = faces.find((f) => f.face_id === selectedFaceId) || faces[0];
      const claheCropUrl = face && face.preprocessing && face.preprocessing.clahe_crop;
      const claheNorm = face && face.landmarks && face.landmarks.clahe;
      if (!claheCropUrl || !claheNorm) {
        if (els.lmkError) {
          els.lmkError.textContent =
            "No CLAHE crop/landmarks available this frame (no face detected, or CLAHE unavailable) — landmark overlay skipped for this tick.";
        }
        drawBaseImageOnLmkCanvas(null);
        if (els.lmkCanvas) clearCanvas(els.lmkCanvas);
        return { usedSource: null, caption: "No CLAHE crop/landmarks this tick" };
      }
      try {
        const img = await loadImageFromDataUrl(claheCropUrl);
        drawBaseImageOnLmkCanvas(img);
        const positions = claheNorm.map((p) => ({ x: p[0] * img.naturalWidth, y: p[1] * img.naturalHeight }));
        await window.LandmarkDemo.renderOnCanvas(
          positions,
          els.lmkCanvas,
          img.naturalWidth,
          img.naturalHeight,
          els.lmkError,
          els.lmkStatus,
          els.lmkExprList
        );
        return {
          usedSource: img,
          caption:
            "Server's own CLAHE-processed face crop — InsightFace landmarks computed directly on this same, full-resolution crop (not the 96×96 preview thumbnail)",
        };
      } catch (err) {
        if (els.lmkError) els.lmkError.textContent = "Failed to load this frame's CLAHE crop for the landmark overlay.";
        return { usedSource: null, caption: "CLAHE crop failed to load" };
      }
    }

    if (currentMode === "simulation") {
      drawBaseImageOnLmkCanvas(frame.sendCanvas);
      const positions = extractSelectedFaceLandmarks(data, "original", frame.sendCanvas.width, frame.sendCanvas.height);
      await window.LandmarkDemo.renderOnCanvas(
        positions,
        els.lmkCanvas,
        frame.sendCanvas.width,
        frame.sendCanvas.height,
        els.lmkError,
        els.lmkStatus,
        els.lmkExprList
      );
      return {
        usedSource: frame.sendCanvas,
        caption:
          "Simulated frame — InsightFace landmarks from this same request's response (a separate earlier request supplied the raw-frame landmarks used to build the mask)",
      };
    }

    return { usedSource: null, caption: "" };
  }

  function updateLandmarkFlowThumb(result) {
    if (!els.flowLandmarkInput) return;
    const ctx = els.flowLandmarkInput.getContext("2d");
    ctx.clearRect(0, 0, els.flowLandmarkInput.width, els.flowLandmarkInput.height);
    if (result && result.usedSource) {
      ctx.drawImage(result.usedSource, 0, 0, els.flowLandmarkInput.width, els.flowLandmarkInput.height);
    }
    if (els.flowLandmarkCaption) els.flowLandmarkCaption.textContent = (result && result.caption) || "";
    if (els.flowStatusLandmark) {
      els.flowStatusLandmark.textContent = result && result.usedSource ? "✓" : result && result.caption ? "⚠" : "";
    }
  }

  // ---------------------------------------------------------------
  // Input mode switching (Original / CLAHE / Appearance Simulation)
  // ---------------------------------------------------------------

  const MODE_NAMES = { original: "Original", clahe: "CLAHE", simulation: "Appearance Simulation" };
  const MODE_DESCRIPTIONS = {
    original: "(unmodified camera frame, sent to both FER and the InsightFace landmark model, one server request per tick)",
    clahe:
      "(unmodified frame sent to the server; FER computes CLAHE itself, unchanged, and InsightFace landmarks are computed on that same full-resolution CLAHE crop, one server request per tick)",
    simulation:
      "(synthetic tone-shifted frame sent to both FER and the InsightFace landmark model; building the mask needs an extra server request for the raw frame's landmarks, so this mode makes two requests per tick)",
  };

  function setMode(mode) {
    if (mode === currentMode) return;
    currentMode = mode;

    if (els.modeBtns) {
      els.modeBtns.forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-mode") === mode);
      });
    }
    if (els.modeLabel) {
      els.modeLabel.innerHTML = "Active mode: <strong>" + MODE_NAMES[mode] + "</strong> " + MODE_DESCRIPTIONS[mode];
    }
    if (els.flowModeLabel) els.flowModeLabel.textContent = MODE_NAMES[mode];
    if (els.simControls) els.simControls.style.display = mode === "simulation" ? "block" : "none";
    if (els.simCard) els.simCard.style.display = mode === "simulation" ? "block" : "none";

    // Original mode displays the continuously-live <video> (the overlay
    // dots are still only redrawn once per FER tick, ~every 600ms, since
    // landmarks now come from the server); CLAHE/Simulation show a
    // per-tick still <canvas> instead, matching their own base image.
    if (els.lmkVideo) els.lmkVideo.style.display = mode === "original" ? "block" : "none";
    if (els.lmkBaseCanvas) els.lmkBaseCanvas.style.display = mode === "original" ? "none" : "block";
    if (els.lmkInputNote) {
      els.lmkInputNote.textContent =
        mode === "original"
          ? "Input: live camera, InsightFace landmarks updated ~once per FER cycle (Original mode)"
          : mode === "clahe"
          ? "Input: server's InsightFace landmarks on the full-resolution CLAHE crop (updates ~once per FER cycle)"
          : "Input: client-built Appearance Simulation frame, InsightFace landmarks from the server (updates ~once per FER cycle, two server requests per tick)";
    }

    if (!cameraActive) return;

    // Every mode is now driven by the same per-tick /predict response
    // (no continuous client-side detection loop), so switching modes
    // only needs to clear stale drawings/predictions from the previous
    // mode -- the next tick (within INFERENCE_INTERVAL_MS) repopulates
    // the panel for the newly selected mode.
    if (window.LandmarkDemo) window.LandmarkDemo.clear(els.lmkCanvas, els.lmkStatus, els.lmkExprList);
    if (els.lmkBaseCanvas) clearCanvas(els.lmkBaseCanvas);
  }

  function panelRowHtml(face, modelResult, modelName) {
    if (modelResult && modelResult.available) {
      const pct = modelResult.confidence != null ? Math.round(modelResult.confidence * 100) + "%" : "";
      return (
        '<div class="demo-prediction-row">' +
        '<span class="face-id">Face ' +
        face.face_id +
        '</span><span class="face-label">' +
        modelResult.label +
        '</span><span class="face-conf">' +
        pct +
        "</span></div>"
      );
    }
    const err = (modelResult && modelResult.error) || "";
    const label = err.indexOf("CLAHE unavailable") === 0 ? "CLAHE unavailable" : modelName + " unavailable";
    return (
      '<div class="demo-prediction-row"><span class="face-id">Face ' +
      face.face_id +
      '</span><span class="face-label">' +
      label +
      '</span><span class="face-conf"></span></div>'
    );
  }

  function renderPrediction(data) {
    if (data.status === "no_face") {
      PANELS.forEach((p) => {
        els.panels[p.key].list.innerHTML =
          '<div class="demo-prediction-row"><span class="face-label">No face detected</span></div>';
        clearCanvas(els.panels[p.key].canvas);
      });
      els.facesNote.textContent = "";
      lastFaces = [];
      resetFlow();
      return;
    }
    if (data.status !== "ok") {
      PANELS.forEach((p) => {
        els.panels[p.key].list.innerHTML =
          '<div class="demo-prediction-row"><span class="face-label">Model unavailable</span></div>';
      });
      return;
    }

    const faces = data.faces || [];
    lastFaces = faces;

    // Same detected faces -> same bounding boxes drawn on all four panels.
    PANELS.forEach((p) => {
      const el = els.panels[p.key];
      drawFaceBoxes(el.canvas, el.video, faces);
    });

    PANELS.forEach((p) => {
      const modelName = p.model === "hsemotion" ? "HSEmotion" : "ArcFace";
      const rows = faces.map((face) => {
        const groupResult = face[p.group]; // "original" or "clahe"
        const modelResult = groupResult ? groupResult[p.model] : null;
        return panelRowHtml(face, modelResult, modelName);
      });
      els.panels[p.key].list.innerHTML = rows.join("");
    });

    if (data.faces_truncated && data.faces_truncated > 0) {
      els.facesNote.textContent =
        data.faces_processed + " faces shown — " + data.faces_truncated + " additional face(s) not processed.";
    } else if (faces.length > 1) {
      els.facesNote.textContent = faces.length + " faces detected and processed.";
    } else {
      els.facesNote.textContent = "";
    }

    renderFaceSelector(faces);
    renderFlow(faces);
  }

  // ---------------------------------------------------------------
  // Live Processing Flow (selected-face detail view)
  // ---------------------------------------------------------------

  function renderFaceSelector(faces) {
    if (!faces.some((f) => f.face_id === selectedFaceId)) {
      selectedFaceId = faces.length ? faces[0].face_id : 1;
    }
    if (faces.length <= 1) {
      els.flowFaceSelector.innerHTML = "";
      return;
    }
    els.flowFaceSelector.innerHTML = faces
      .map((f) => {
        const active = f.face_id === selectedFaceId ? " active" : "";
        return (
          '<button type="button" class="flow-face-btn' +
          active +
          '" data-face-id="' +
          f.face_id +
          '">Face ' +
          f.face_id +
          "</button>"
        );
      })
      .join("");
    Array.from(els.flowFaceSelector.querySelectorAll(".flow-face-btn")).forEach((btn) => {
      btn.addEventListener("click", () => {
        selectedFaceId = parseInt(btn.getAttribute("data-face-id"), 10);
        renderFaceSelector(lastFaces);
        renderFlow(lastFaces);
      });
    });
  }

  function setFlowStatus(el, available) {
    el.textContent = available ? "✓" : "unavailable";
    el.className = "flow-step-status" + (available ? "" : " unavailable");
  }

  function modelLineText(modelName, result) {
    if (result && result.available) {
      const pct = result.confidence != null ? " (" + Math.round(result.confidence * 100) + "%)" : "";
      return modelName + ": " + result.label + pct;
    }
    return modelName + ": unavailable";
  }

  function renderFlow(faces) {
    els.flowFaceNum.textContent = String(selectedFaceId);
    const face = faces.find((f) => f.face_id === selectedFaceId);
    if (!face) {
      resetFlow();
      return;
    }

    // Step 1: Camera Frame -- captured directly from the browser's own
    // live video element (already available locally; never requested
    // from the server just for this visualization).
    const sourceVideo = els.panels["orig-hse"].video;
    if (sourceVideo.videoWidth) {
      const ctx = els.flowCamera.getContext("2d");
      ctx.drawImage(sourceVideo, 0, 0, els.flowCamera.width, els.flowCamera.height);
      setFlowStatus(els.flowStatusCamera, true);

      // Step 2: Face Detection -- same camera thumbnail, selected face's
      // bbox drawn on top (bbox coordinates already returned by /predict,
      // no extra request).
      const dctx = els.flowDetection.getContext("2d");
      dctx.drawImage(sourceVideo, 0, 0, els.flowDetection.width, els.flowDetection.height);
      if (face.bbox) {
        const x = face.bbox[0] * els.flowDetection.width;
        const y = face.bbox[1] * els.flowDetection.height;
        const w = (face.bbox[2] - face.bbox[0]) * els.flowDetection.width;
        const h = (face.bbox[3] - face.bbox[1]) * els.flowDetection.height;
        dctx.strokeStyle = "#2f5bd7";
        dctx.lineWidth = 2;
        dctx.strokeRect(x, y, w, h);
      }
      setFlowStatus(els.flowStatusDetection, !!face.bbox);
    } else {
      setFlowStatus(els.flowStatusCamera, false);
      setFlowStatus(els.flowStatusDetection, false);
    }

    // Step 3: Face Crop, and the Original/CLAHE branch -- all sourced
    // from the same preprocessing.* thumbnails already generated
    // server-side from the same crop/CLAHE arrays used for inference
    // (tools/realtime_demo/inference.py), never a second crop or a
    // second CLAHE call.
    const pp = face.preprocessing;
    if (pp && pp.original_crop) {
      els.flowCrop.src = pp.original_crop;
      els.flowOrigCrop.src = pp.original_crop;
      setFlowStatus(els.flowStatusCrop, true);
      setFlowStatus(els.flowStatusOrig, true);
    } else {
      els.flowCrop.removeAttribute("src");
      els.flowOrigCrop.removeAttribute("src");
      setFlowStatus(els.flowStatusCrop, false);
      setFlowStatus(els.flowStatusOrig, false);
    }
    if (pp && pp.clahe_crop) {
      els.flowClaheCrop.src = pp.clahe_crop;
      setFlowStatus(els.flowStatusClahe, true);
    } else {
      els.flowClaheCrop.removeAttribute("src");
      setFlowStatus(els.flowStatusClahe, false);
    }

    // Step 5: model paths (compact labels, no extra large video feeds --
    // the existing 4-panel grid above already shows those).
    els.flowOrigHse.textContent = modelLineText("HSEmotion", face.original && face.original.hsemotion);
    els.flowOrigAf.textContent = modelLineText("ArcFace + LR", face.original && face.original.arcface);
    els.flowClaheHse.textContent = modelLineText("HSEmotion", face.clahe && face.clahe.hsemotion);
    els.flowClaheAf.textContent = modelLineText("ArcFace + LR", face.clahe && face.clahe.arcface);
  }

  function fillResearchContext() {
    const D = window.DASHBOARD_DATA;
    if (!D) return;
    const pct = (x) => (x == null ? "N/A" : (x * 100).toFixed(2) + "%");
    const el = (id) => document.getElementById(id);
    if (el("demo-context-af-acc")) el("demo-context-af-acc").textContent = pct(D.common_subset.arcface.accuracy);
    if (el("demo-context-hse-acc")) el("demo-context-hse-acc").textContent = pct(D.common_subset.hsemotion.accuracy);
    if (el("demo-context-p")) el("demo-context-p").textContent = D.statistics.mcnemar.p_value.toFixed(4);
  }

  document.addEventListener("DOMContentLoaded", function () {
    cacheEls();
    if (!els.startBtn) return; // section not present, nothing to wire up
    fillResearchContext();
    resetPredictions();
    setStatus("OFF");
    setServerUi("offline");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("unavailable — this browser does not support camera access");
      els.startBtn.disabled = true;
    } else {
      els.startBtn.addEventListener("click", startCamera);
      els.stopBtn.addEventListener("click", stopCamera);
    }

    els.serverStartBtn.addEventListener("click", startDemoServer);
    els.serverStopBtn.addEventListener("click", stopDemoServer);

    if (els.modeBtns) {
      els.modeBtns.forEach((btn) => {
        btn.addEventListener("click", () => setMode(btn.getAttribute("data-mode")));
      });
    }
    if (els.simIntensityInput) {
      els.simIntensityInput.addEventListener("input", () => {
        const pct = parseInt(els.simIntensityInput.value, 10);
        simIntensity = pct / 100;
        if (els.simIntensityValue) els.simIntensityValue.textContent = pct + "%";
      });
    }

    pollServerStatus();
    serverPollTimer = setInterval(pollServerStatus, SERVER_STATUS_POLL_MS);

    window.addEventListener("beforeunload", function () {
      stopCamera();
      if (serverPollTimer) clearInterval(serverPollTimer);
    });
  });
})();
