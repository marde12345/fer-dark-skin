/* Live Landmark overlay renderer -- dashboard/realtime_landmark_demo.js
 *
 * Pure rendering module: draws already-detected 68-point landmarks and
 * dispatches to the landmark-based expression classifier. Performs NO
 * face/landmark detection itself and loads no model -- landmarks now
 * come from the local FER inference server's InsightFace
 * `landmark_3d_68` model (tools/realtime_demo/inference.py), reused
 * from the same response already fetched for HSEmotion/ArcFace, never
 * a second detector. This replaces the previous face-api.js-based
 * implementation entirely (removed per the InsightFace migration).
 *
 * Exposes window.LandmarkDemo = {
 *   computeCoverTransform(naturalW, naturalH, boxW, boxH),
 *   renderForVideo(positions, videoEl, canvasEl, errorEl, statusEl, exprEl),
 *     -- positions in the video's native pixel space; applies the
 *        object-fit:cover transform so dots land on the actually
 *        displayed pixels (used for Original mode).
 *   renderOnCanvas(positions, canvasEl, width, height, errorEl, statusEl, exprEl),
 *     -- positions already in a 1:1 pixel space matching (width,height);
 *        used for CLAHE and Appearance Simulation modes, where the base
 *        image is drawn into its own canvas at that exact resolution
 *        (no object-fit:cover distortion to account for).
 *   clear(canvasEl, statusEl, exprEl),
 *   REGIONS,
 * }
 *
 * This file does not touch dashboard.js, data.js, appearance_simulation.js,
 * or landmark_expression_classifier.js (both of which are already
 * detector-agnostic and require no changes for this migration). It is
 * purely additive/replacing in scope.
 */
(function () {
  // dlib/ibug-300W 68-point region ranges (inclusive), matched to the
  // legend shown in the dashboard. "closed" regions draw a line back
  // from their last point to their first. Confirmed (not assumed) to
  // match InsightFace's landmark_3d_68 ordering -- see
  // experiments/EXP-DASH-001-landmark-fer/extract_landmark_features.py's
  // docstring for the empirical verification.
  const REGIONS = [
    { name: "Jaw", start: 0, end: 16, closed: false, color: "#22d3ee" },
    { name: "Right eyebrow", start: 17, end: 21, closed: false, color: "#fde047" },
    { name: "Left eyebrow", start: 22, end: 26, closed: false, color: "#fde047" },
    { name: "Nose bridge", start: 27, end: 30, closed: false, color: "#fb923c" },
    { name: "Nose bottom", start: 30, end: 35, closed: true, color: "#fb923c" },
    { name: "Right eye", start: 36, end: 41, closed: true, color: "#4ade80" },
    { name: "Left eye", start: 42, end: 47, closed: true, color: "#4ade80" },
    { name: "Outer lips", start: 48, end: 59, closed: true, color: "#f43f5e" },
    { name: "Inner lips", start: 60, end: 67, closed: true, color: "#f43f5e" },
  ];
  const EXPECTED_POINTS = 68;

  function setErrorOn(el, text) {
    if (el) el.textContent = text || "";
  }

  function setStatusOn(el, text, ok) {
    if (!el) return;
    el.textContent = text || "";
    el.classList.remove("lmk-status-ok", "lmk-status-warn");
    el.classList.add(ok ? "lmk-status-ok" : "lmk-status-warn");
  }

  function clearCanvasEl(canvasEl) {
    if (!canvasEl) return;
    const ctx = canvasEl.getContext("2d");
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
  }

  // Draws thin high-contrast connecting lines per facial region, then a
  // dark-outlined bright dot on every point (so dots stay visible against
  // any skin tone or background), and reports a detected/count status.
  function drawPositions(canvasEl, positions, statusElArg) {
    const ctx = canvasEl.getContext("2d");

    REGIONS.forEach((region) => {
      const pts = positions.slice(region.start, region.end + 1);
      if (pts.length < 2) return;
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 1; i < pts.length; i++) {
        ctx.lineTo(pts[i].x, pts[i].y);
      }
      if (region.closed) ctx.closePath();
      ctx.strokeStyle = region.color;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.9;
      ctx.stroke();
      ctx.globalAlpha = 1;
    });

    positions.forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 2.3, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 1.4, 0, 2 * Math.PI);
      ctx.fillStyle = "#1d3fd6";
      ctx.fill();
    });

    setStatusOn(statusElArg, "Face detected — " + positions.length + "/" + EXPECTED_POINTS + " points rendered", true);
  }

  function reportNoFace(canvasEl, statusElArg) {
    clearCanvasEl(canvasEl);
    setStatusOn(statusElArg, "No face detected — move closer to the camera, face it directly, and improve lighting", false);
  }

  // updateExpressionPanel(positions, exprElArg): runs the EXP-DASH-001
  // landmark-based expression classifier on the SAME positions just used
  // for the overlay/status above -- never a second detection call, so
  // the drawn landmarks and this prediction always come from the same
  // server response. Positions here are pre-transform (native/crop pixel
  // space); this is safe because every feature the classifier computes
  // is a ratio/angle invariant to uniform scale and translation, so the
  // on-screen cover-fit transform (an affine scale+translate) cannot
  // change the computed features.
  async function updateExpressionPanel(positions, exprElArg) {
    if (!exprElArg) return;
    if (!positions) {
      exprElArg.innerHTML = '<div class="demo-prediction-row"><span class="face-label">No face detected</span></div>';
      return;
    }
    if (!window.LandmarkExpressionClassifier) {
      exprElArg.innerHTML = '<div class="demo-prediction-row"><span class="face-label">Classifier script unavailable</span></div>';
      return;
    }
    const loaded = await window.LandmarkExpressionClassifier.ready();
    if (!loaded) {
      exprElArg.innerHTML = '<div class="demo-prediction-row"><span class="face-label">Classifier weights failed to load</span></div>';
      return;
    }
    const result = window.LandmarkExpressionClassifier.predict(positions);
    if (!result) {
      exprElArg.innerHTML = '<div class="demo-prediction-row"><span class="face-label">Prediction unavailable this frame</span></div>';
      return;
    }
    const pct = Math.round(result.confidence * 100) + "%";
    exprElArg.innerHTML =
      '<div class="demo-prediction-row"><span class="face-label">' +
      result.label +
      '</span><span class="face-conf">' +
      pct +
      "</span></div>";
  }

  // computeCoverTransform: the live <video> element is displayed with
  // CSS object-fit:cover (crops to fill its box while preserving aspect
  // ratio). The server's landmarks are in full-frame pixel space, so a
  // naive linear stretch of those coordinates onto the canvas's
  // displayed box misaligns whenever the camera's native aspect ratio
  // doesn't exactly match the box -- this reproduces the same
  // scale-and-center math object-fit:cover uses, so dots land exactly on
  // the video pixels the user actually sees.
  function computeCoverTransform(naturalW, naturalH, boxW, boxH) {
    const scale = Math.max(boxW / naturalW, boxH / naturalH);
    const offsetX = (boxW - naturalW * scale) / 2;
    const offsetY = (boxH - naturalH * scale) / 2;
    return { scale, offsetX, offsetY };
  }

  function syncCanvasSize(canvasEl, videoEl) {
    const w = videoEl.clientWidth;
    const h = videoEl.clientHeight;
    if (w && h && (canvasEl.width !== w || canvasEl.height !== h)) {
      canvasEl.width = w;
      canvasEl.height = h;
    }
  }

  // renderForVideo(positions, videoEl, canvasEl, errorElArg, statusElArg, exprElArg):
  // positions must be in videoEl's NATIVE pixel space (videoWidth x
  // videoHeight) -- the caller denormalizes the server's [0,1]-normalized
  // landmarks by that resolution before calling this. Used for Original
  // mode, where the overlay sits on top of a continuously-live <video>
  // displayed with object-fit:cover.
  async function renderForVideo(positions, videoEl, canvasEl, errorElArg, statusElArg, exprElArg) {
    if (!canvasEl || !videoEl) return;
    syncCanvasSize(canvasEl, videoEl);
    setErrorOn(errorElArg, "");

    if (!positions || !videoEl.videoWidth) {
      reportNoFace(canvasEl, statusElArg);
      await updateExpressionPanel(null, exprElArg);
      return;
    }

    const { scale, offsetX, offsetY } = computeCoverTransform(
      videoEl.videoWidth,
      videoEl.videoHeight,
      canvasEl.width,
      canvasEl.height
    );
    const transformed = positions.map((p) => ({
      x: p.x * scale + offsetX,
      y: p.y * scale + offsetY,
    }));

    clearCanvasEl(canvasEl);
    drawPositions(canvasEl, transformed, statusElArg);
    await updateExpressionPanel(positions, exprElArg);
  }

  // renderOnCanvas(positions, canvasEl, width, height, errorElArg, statusElArg, exprElArg):
  // positions already in a 1:1 pixel space matching (width, height) --
  // used for CLAHE and Appearance Simulation modes, where the caller
  // draws the base image (CLAHE crop thumbnail, or the simulated frame)
  // into its own canvas at exactly that resolution, so no object-fit
  // cover transform is needed.
  async function renderOnCanvas(positions, canvasEl, width, height, errorElArg, statusElArg, exprElArg) {
    if (!canvasEl || !width || !height) return;
    if (canvasEl.width !== width || canvasEl.height !== height) {
      canvasEl.width = width;
      canvasEl.height = height;
    }
    setErrorOn(errorElArg, "");

    if (!positions) {
      reportNoFace(canvasEl, statusElArg);
      await updateExpressionPanel(null, exprElArg);
      return;
    }

    clearCanvasEl(canvasEl);
    drawPositions(canvasEl, positions, statusElArg);
    await updateExpressionPanel(positions, exprElArg);
  }

  function clear(canvasEl, statusElArg, exprElArg) {
    if (canvasEl) clearCanvasEl(canvasEl);
    setErrorOn(null, "");
    setStatusOn(statusElArg, "", false);
    if (exprElArg) exprElArg.innerHTML = "";
  }

  window.LandmarkDemo = { computeCoverTransform, renderForVideo, renderOnCanvas, clear, REGIONS };
})();
