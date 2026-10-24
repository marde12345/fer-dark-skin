/* Landmark-based Expression Classifier -- dashboard/landmark_expression_classifier.js
 *
 * EXP-DASH-001 (dashboard demo experiment, NOT a formal thesis result).
 * Computes the same 7 normalized geometric features used to train
 * experiments/EXP-DASH-001-landmark-fer/train_landmark_classifier.py
 * (ibug-300W 68-point ordering, identical formulas -- see that script's
 * extract_landmark_features.py for the Python reference), then runs a
 * frozen multinomial Logistic Regression entirely client-side: a 7x5
 * dot product + softmax. No ML library needed, no server round trip.
 *
 * Training data: 141 human-labeled face crops (data/1408-1010-intermediate/
 * manual_labels_export.csv's gt_label column), 5 classes (Angry and
 * Disgust excluded -- too few samples). Out-of-fold cross-validated
 * macro-F1 was ~0.22 (near chance for 5 classes) -- this is a weak,
 * experimental classifier. It is NOT validated to match or exceed the
 * image-based FER models shown alongside it, and should be read as
 * illustrative only.
 *
 * Reuses the landmark points already computed by realtime_landmark_demo.js
 * for the active input mode -- this file does NOT run its own face
 * detection. It exposes:
 *   window.LandmarkExpressionClassifier = {
 *     ready(),                 -> Promise<boolean>, loads weights JSON once
 *     predict(positions),      -> {label, confidence, probabilities} | null
 *   }
 *
 * This file does not touch dashboard.js, data.js, realtime_demo.js,
 * realtime_landmark_demo.js, or appearance_simulation.js. It is purely
 * additive.
 */
(function () {
  // Trained weights, inlined directly (not fetched) -- fetch() of a
  // local JSON file is blocked by the browser's same-origin policy when
  // this dashboard is opened as a plain file:// page (no local server),
  // which is exactly how this dashboard is normally opened. Inlining
  // avoids that failure mode entirely; the source of truth for these
  // numbers is experiments/EXP-DASH-001-landmark-fer/landmark_classifier_weights.json
  // (regenerate this block from that file if the model is retrained).
  const TRAINED_WEIGHTS = {
    "class_order": [
      "Fear",
      "Happy",
      "Neutral",
      "Sad",
      "Surprise"
    ],
    "feature_names": [
      "ear_mean",
      "mouth_openness",
      "mouth_width_ratio",
      "lip_corner_angle",
      "brow_eye_dist_mean",
      "inner_brow_distance",
      "jaw_drop"
    ],
    "scaler_mean": [
      0.4244388417313045,
      0.1394696093480355,
      0.8569464932784564,
      -0.2764028451927584,
      0.44370927745144656,
      0.5465065145227646,
      1.040947502099189
    ],
    "scaler_scale": [
      0.615181155806884,
      0.34047781092354223,
      0.15985380777103184,
      0.2271570894202436,
      0.4579758856861854,
      0.042513811973476236,
      1.419094767405642
    ],
    "coef": [
      [
        0.2763857683587184,
        -0.7699583106833368,
        -0.29041982510988634,
        -0.012031386556371117,
        -0.37143420623780066,
        -0.22755027701678376,
        0.2153778770065953
      ],
      [
        -0.7759009713641823,
        0.7830805993961292,
        0.9798174199542407,
        0.34136412814054423,
        0.49852604957991337,
        0.21519400620578344,
        0.4423280979148571
      ],
      [
        1.1391885086393696,
        -0.9222716620692423,
        -0.16410115491450294,
        -0.08340584986401132,
        0.17303380626435877,
        0.16127541991152508,
        0.11123535409020605
      ],
      [
        -0.2319687845309438,
        -0.6056677647020295,
        0.14626847552283492,
        0.24049523028394731,
        -0.9726984197642199,
        0.1291227953532678,
        -0.13515782531975826
      ],
      [
        -0.40770452110296174,
        1.5148171380584794,
        -0.6715649154526863,
        -0.48642212200410884,
        0.6725727701577483,
        -0.27804194445379254,
        -0.6337835036919003
      ]
    ],
    "intercept": [
      0.031092741477381027,
      0.11368895046079956,
      0.22677338158166999,
      -0.24018068818101743,
      -0.1313743853388362
    ]
  };

  const RIGHT_EYE = [36, 37, 38, 39, 40, 41];
  const LEFT_EYE = [42, 43, 44, 45, 46, 47];
  const RIGHT_BROW = [17, 18, 19, 20, 21];
  const LEFT_BROW = [22, 23, 24, 25, 26];
  const MOUTH_OUTER_LEFT_CORNER = 48;
  const MOUTH_OUTER_RIGHT_CORNER = 54;
  const MOUTH_OUTER_TOP_CENTER = 51;
  const MOUTH_OUTER_BOTTOM_CENTER = 57;
  const INNER_LIP_TOP = 62;
  const INNER_LIP_BOTTOM = 66;
  const CHIN = 8;

  let weights = null;

  function dist(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  function meanPoint(pts, indices) {
    let sx = 0;
    let sy = 0;
    indices.forEach((i) => {
      sx += pts[i].x;
      sy += pts[i].y;
    });
    return { x: sx / indices.length, y: sy / indices.length };
  }

  // computeFeatures(positions): positions is face-api.js's 68-point
  // landmarks.positions array ({x,y} x 68). Mirrors
  // experiments/EXP-DASH-001-landmark-fer/extract_landmark_features.py's
  // compute_features() formula-for-formula. Returns null if degenerate
  // (near-zero inter-ocular distance).
  function computeFeatures(positions) {
    if (!positions || positions.length !== 68) return null;

    const rightEyeCenter = meanPoint(positions, RIGHT_EYE);
    const leftEyeCenter = meanPoint(positions, LEFT_EYE);
    const iod = dist(rightEyeCenter, leftEyeCenter);
    if (iod < 1e-3) return null;

    function ear(eyeIdx) {
      const p = eyeIdx.map((i) => positions[i]);
      const vertical = dist(p[1], p[5]) + dist(p[2], p[4]);
      const horizontal = dist(p[0], p[3]);
      if (horizontal < 1e-6) return 0;
      return vertical / (2 * horizontal);
    }
    const earMean = (ear(RIGHT_EYE) + ear(LEFT_EYE)) / 2;

    const mouthOpenness = dist(positions[INNER_LIP_TOP], positions[INNER_LIP_BOTTOM]) / iod;
    const mouthWidthRatio = dist(positions[MOUTH_OUTER_LEFT_CORNER], positions[MOUTH_OUTER_RIGHT_CORNER]) / iod;

    const cornerMidY = (positions[MOUTH_OUTER_LEFT_CORNER].y + positions[MOUTH_OUTER_RIGHT_CORNER].y) / 2;
    const verticalOffset = positions[MOUTH_OUTER_TOP_CENTER].y - cornerMidY;
    const halfWidth = dist(positions[MOUTH_OUTER_LEFT_CORNER], positions[MOUTH_OUTER_RIGHT_CORNER]) / 2;
    const lipCornerAngle = halfWidth > 1e-6 ? Math.atan2(verticalOffset, halfWidth) : 0;

    const rightBrowMid = meanPoint(positions, RIGHT_BROW);
    const leftBrowMid = meanPoint(positions, LEFT_BROW);
    const browEyeDistMean = (dist(rightBrowMid, rightEyeCenter) + dist(leftBrowMid, leftEyeCenter)) / (2 * iod);

    const innerBrowDistance = dist(positions[21], positions[22]) / iod;

    const mouthCenter = {
      x: (positions[MOUTH_OUTER_TOP_CENTER].x + positions[MOUTH_OUTER_BOTTOM_CENTER].x) / 2,
      y: (positions[MOUTH_OUTER_TOP_CENTER].y + positions[MOUTH_OUTER_BOTTOM_CENTER].y) / 2,
    };
    const jawDrop = dist(positions[CHIN], mouthCenter) / iod;

    return [earMean, mouthOpenness, mouthWidthRatio, lipCornerAngle, browEyeDistMean, innerBrowDistance, jawDrop];
  }

  function softmax(logits) {
    const max = Math.max.apply(null, logits);
    const exps = logits.map((v) => Math.exp(v - max));
    const sum = exps.reduce((a, b) => a + b, 0);
    return exps.map((v) => v / sum);
  }

  async function ready() {
    if (weights) return true;
    try {
      if (
        !TRAINED_WEIGHTS ||
        !Array.isArray(TRAINED_WEIGHTS.coef) ||
        !Array.isArray(TRAINED_WEIGHTS.class_order)
      ) {
        throw new Error("malformed inlined weights");
      }
      weights = TRAINED_WEIGHTS;
      return true;
    } catch (err) {
      weights = null;
      return false;
    }
  }

  // predict(positions) -> { label, confidence, probabilities } | null
  // Returns null if the model isn't loaded, positions are missing/invalid,
  // or features are degenerate. Never throws.
  function predict(positions) {
    if (!weights) return null;
    const features = computeFeatures(positions);
    if (!features) return null;

    const scaled = features.map((v, i) => (v - weights.scaler_mean[i]) / weights.scaler_scale[i]);
    const logits = weights.coef.map((row, classIdx) => {
      let sum = weights.intercept[classIdx];
      for (let i = 0; i < row.length; i++) sum += row[i] * scaled[i];
      return sum;
    });
    const probs = softmax(logits);

    let bestIdx = 0;
    for (let i = 1; i < probs.length; i++) {
      if (probs[i] > probs[bestIdx]) bestIdx = i;
    }

    const probabilities = {};
    weights.class_order.forEach((label, i) => {
      probabilities[label] = probs[i];
    });

    return {
      label: weights.class_order[bestIdx],
      confidence: probs[bestIdx],
      probabilities,
    };
  }

  window.LandmarkExpressionClassifier = { ready, predict, computeFeatures };
})();
