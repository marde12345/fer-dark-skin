/* Appearance Simulation -- dashboard/appearance_simulation.js
 *
 * A synthetic, face-region-only color/tone shift, used as an optional
 * input mode for the combined Live FER & Landmark Demo. This is NOT a
 * Papuan ethnicity simulator and is not a realistic representation of
 * any real population -- it is a visual toy for exploring how a
 * synthetic tone shift alone affects the FER and landmark models'
 * outputs. It does not establish demographic bias, fairness, or
 * real-world robustness.
 *
 * Design (plain Canvas2D, no new dependencies):
 *  1. The face-region mask is built directly from the already-detected
 *     face-api.js 68-point landmarks (jaw line + eyebrow line, offset
 *     upward to approximate the forehead) -- geometry is READ, never
 *     altered, so landmark positions are unaffected by this effect.
 *  2. Mask edges are feathered with a canvas blur filter for a smooth
 *     transition (falls back to hard edges if the browser doesn't
 *     support canvas filters -- a cosmetic-only degradation).
 *  3. A full-canvas fill using globalCompositeOperation = "color" (the
 *     canvas blend-mode, not an inference step) replaces hue/saturation
 *     while preserving the destination's luminance -- i.e. the original
 *     shading/texture/expression cues survive, only perceived skin tone
 *     shifts.
 *  4. The tone layer is masked to the face region only (destination-in
 *     against the feathered mask), then composited back onto the
 *     untouched source frame at an alpha equal to the intensity slider
 *     (0 = no effect, 1 = full effect) -- so everything outside the
 *     face region, and the no-effect case, is pixel-identical to the
 *     original frame.
 *
 * This file does not touch dashboard.js, data.js, realtime_demo.js, or
 * realtime_landmark_demo.js. It is purely additive and exposes:
 *   window.AppearanceSimulation = { apply(sourceCanvas, positions, intensity, toneColor) }
 */
(function () {
  const DEFAULT_TONE = "#6b4226"; // an arbitrary synthetic brown tone -- not tied to any specific population

  function buildMaskCanvas(width, height, positions) {
    const mask = document.createElement("canvas");
    mask.width = width;
    mask.height = height;
    const ctx = mask.getContext("2d");
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, width, height);

    if (!positions || positions.length < 27) return mask; // not enough points (jaw 0-16 + brows 17-26)

    const jaw = positions.slice(0, 17);
    const browIndices = [26, 25, 24, 23, 22, 21, 20, 19, 18, 17];
    const jawTop = Math.min(positions[19].y, positions[24].y);
    const jawBottom = Math.max.apply(null, jaw.map((p) => p.y));
    const faceHeight = Math.max(1, jawBottom - jawTop);
    const foreheadOffset = faceHeight * 0.38;

    const top = browIndices.map((i) => ({ x: positions[i].x, y: positions[i].y - foreheadOffset }));
    const pathPts = jaw.concat(top);

    try {
      ctx.filter = "blur(6px)";
    } catch (err) {
      // canvas filter not supported -- mask will just have hard edges
    }
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.moveTo(pathPts[0].x, pathPts[0].y);
    for (let i = 1; i < pathPts.length; i++) {
      ctx.lineTo(pathPts[i].x, pathPts[i].y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.filter = "none";
    return mask;
  }

  // apply(sourceCanvas, positions, intensity, toneColor) -> HTMLCanvasElement
  // sourceCanvas: the raw camera frame (untouched).
  // positions: face-api landmark positions array ({x,y} x 68), or null/empty (no-op).
  // intensity: 0..1. 0 returns a pixel-identical copy of sourceCanvas.
  // toneColor: optional CSS color string for the synthetic tone fill.
  function apply(sourceCanvas, positions, intensity, toneColor) {
    const w = sourceCanvas.width;
    const h = sourceCanvas.height;
    const out = document.createElement("canvas");
    out.width = w;
    out.height = h;
    const octx = out.getContext("2d");
    octx.drawImage(sourceCanvas, 0, 0, w, h);

    const alpha = Math.max(0, Math.min(1, intensity || 0));
    if (alpha <= 0 || !positions || !positions.length) {
      return out; // no-op: identical to the source frame
    }

    const mask = buildMaskCanvas(w, h, positions);

    const tone = document.createElement("canvas");
    tone.width = w;
    tone.height = h;
    const tctx = tone.getContext("2d");
    tctx.drawImage(sourceCanvas, 0, 0, w, h);
    tctx.globalCompositeOperation = "color";
    tctx.fillStyle = toneColor || DEFAULT_TONE;
    tctx.fillRect(0, 0, w, h);
    tctx.globalCompositeOperation = "destination-in";
    tctx.drawImage(mask, 0, 0, w, h);
    tctx.globalCompositeOperation = "source-over";

    octx.globalAlpha = alpha;
    octx.drawImage(tone, 0, 0, w, h);
    octx.globalAlpha = 1;
    return out;
  }

  window.AppearanceSimulation = { apply, DEFAULT_TONE };
})();
