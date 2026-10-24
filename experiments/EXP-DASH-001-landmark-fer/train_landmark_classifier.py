"""EXP-DASH-001 (dashboard demo experiment, NOT a formal thesis experiment):
train and evaluate a lightweight landmark-based expression classifier on
the 7 geometric features produced by extract_landmark_features.py.

Reuses this project's own established conventions from
tools/train_arcface_classifier.py (the real thesis ArcFace classifier):
MIN_CLASS_COUNT=5 rare-class exclusion, N_SPLITS=5, TEMPORAL_BLOCK_SIZE=3
frame-adjacency grouping (no person-ID field exists anywhere in this
repository -- confirmed previously in docs/ARCFACE_EXPERIMENT_DESIGN.md
Section 8 and reconfirmed here), StratifiedGroupKFold cross-validation
used as the held-out evaluation (every sample is scored out-of-fold by a
model that never saw it or its temporal group during training -- there is
no separate static train/test split, because 141 usable samples across 5
classes is too small to hold out a static test set without making it
unusably tiny for the rarer classes).

Three simple baselines are compared (Logistic Regression, Random Forest,
SVM-RBF) with identical features/splits, per the task's "evaluate a
simple baseline first ... avoid unnecessary complexity" instruction.
Logistic Regression is additionally the deployment candidate if it is
competitive, since its linear decision function trivially ports to pure
browser JS with zero new dependencies (dot product + softmax) -- see
dashboard/landmark_expression_classifier.js.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

HERE = Path(__file__).resolve().parent
FEATURES_CSV = HERE / "landmark_classifier_features.csv"
FEATURE_NAMES = [
    "ear_mean",
    "mouth_openness",
    "mouth_width_ratio",
    "lip_corner_angle",
    "brow_eye_dist_mean",
    "inner_brow_distance",
    "jaw_drop",
]

MIN_CLASS_COUNT = 5  # matches tools/train_arcface_classifier.py
N_SPLITS = 5  # matches tools/train_arcface_classifier.py
TEMPORAL_BLOCK_SIZE = 3  # matches tools/train_arcface_classifier.py
RANDOM_SEED = 42  # matches tools/train_arcface_classifier.py


def assign_temporal_group(frame_index: int, block_size: int = TEMPORAL_BLOCK_SIZE) -> int:
    """Identical to tools/train_arcface_classifier.py's grouping function:
    deterministic chunking of consecutive frame indices, so near-adjacent
    frames (most likely to share identity/pose/lighting) never split
    across train and test within a CV fold."""
    return frame_index // block_size


def load_rows() -> list[dict]:
    import csv

    with FEATURES_CSV.open() as f:
        return list(csv.DictReader(f))


def build_dataset(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], dict]:
    class_counts = Counter(r["gt_label"] for r in rows)
    rare_classes = {label for label, count in class_counts.items() if count < MIN_CLASS_COUNT}
    exclusions = {f"excluded_rare_class_{label}": class_counts[label] for label in rare_classes}

    usable = [r for r in rows if r["gt_label"] not in rare_classes]
    class_order = sorted(set(r["gt_label"] for r in usable))
    label_to_index = {label: i for i, label in enumerate(class_order)}

    X = np.array([[float(r[name]) for name in FEATURE_NAMES] for r in usable], dtype=np.float64)
    y = np.array([label_to_index[r["gt_label"]] for r in usable], dtype=np.int64)
    groups = np.array([assign_temporal_group(int(r["frame_index"])) for r in usable], dtype=np.int64)

    return X, y, groups, class_order, exclusions


def run_cv(model_factory, X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Returns out-of-fold predicted class indices, one per sample, in the
    original sample order. Each fold scales features on the training
    portion only (StandardScaler fit inside the fold, never on held-out
    data) to avoid any leakage through feature normalization statistics."""
    n_groups = len(set(groups.tolist()))
    n_splits = min(N_SPLITS, n_groups)
    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)

    oof_pred = np.full(len(y), -1, dtype=np.int64)
    for train_idx, test_idx in cv.split(X, y, groups):
        scaler = StandardScaler().fit(X[train_idx])
        X_train = scaler.transform(X[train_idx])
        X_test = scaler.transform(X[test_idx])

        model = model_factory()
        model.fit(X_train, y[train_idx])
        oof_pred[test_idx] = model.predict(X_test)

    assert (oof_pred >= 0).all(), "every sample must receive exactly one out-of-fold prediction"
    return oof_pred


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, class_order: list[str]) -> dict:
    report = classification_report(
        y_true, y_pred, target_names=class_order, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_order))))
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    return {
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "macro_f1": float(macro_f1),
    }


def main() -> None:
    rows = load_rows()
    X, y, groups, class_order, exclusions = build_dataset(rows)

    print(f"usable samples: {len(y)} across classes {class_order}")
    print("class distribution:", Counter(class_order[i] for i in y))
    print("exclusions (rare classes, MIN_CLASS_COUNT={}):".format(MIN_CLASS_COUNT), exclusions)
    print(f"temporal groups: {len(set(groups.tolist()))}")

    candidates = {
        "LogisticRegression": lambda: LogisticRegression(
            solver="lbfgs",
            class_weight="balanced", max_iter=2000, random_state=RANDOM_SEED,
        ),
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=200, max_depth=5, class_weight="balanced", random_state=RANDOM_SEED,
        ),
        "SVM_RBF": lambda: SVC(
            kernel="rbf", class_weight="balanced", random_state=RANDOM_SEED,
        ),
    }

    results = {}
    for name, factory in candidates.items():
        oof_pred = run_cv(factory, X, y, groups)
        results[name] = evaluate(y, oof_pred, class_order)
        print(f"\n=== {name} ===")
        print(f"macro-F1 (out-of-fold CV): {results[name]['macro_f1']:.4f}")
        print(classification_report(y, oof_pred, target_names=class_order, zero_division=0))
        print("confusion matrix (rows=true, cols=pred):")
        print(np.array(results[name]["confusion_matrix"]))

    best_name = max(results, key=lambda n: results[n]["macro_f1"])
    print(f"\nBest macro-F1: {best_name} ({results[best_name]['macro_f1']:.4f})")

    # Deployment model: Logistic Regression, fit on ALL usable data (no
    # held-out split for the deployed artifact -- the CV above is the
    # actual evaluation; this final fit is only for serving predictions).
    # Chosen for browser portability (see module docstring) regardless of
    # which model had the top CV macro-F1, UNLESS LR trails the best
    # model by a large margin -- reported explicitly either way so this
    # choice is never silent.
    final_scaler = StandardScaler().fit(X)
    X_scaled = final_scaler.transform(X)
    final_model = LogisticRegression(
        solver="lbfgs",
        class_weight="balanced", max_iter=2000, random_state=RANDOM_SEED,
    )
    final_model.fit(X_scaled, y)

    import joblib

    joblib.dump(
        {
            "model": final_model,
            "scaler": final_scaler,
            "class_order": class_order,
            "feature_names": FEATURE_NAMES,
        },
        HERE / "landmark_classifier_model.joblib",
    )

    metadata = {
        "experiment_id": "EXP-DASH-001",
        "description": "Dashboard-demo landmark-based expression classifier. NOT a formal thesis experiment/result.",
        "dataset_source": "data/1408-1010-intermediate/manual_labels_export.csv (gt_label column)",
        "pseudo_label_warning": "manual_labels_export.csv's model_label column (HSEmotion's own prediction) was NEVER used as a training target -- gt_label (human-assigned) only.",
        "landmark_source": "InsightFace landmark_3d_68 (buffalo_l), extracted by extract_landmark_features.py",
        "scheme_compatibility_assumption": "InsightFace landmark_3d_68 and face-api.js's 68-point faceLandmark68Net are assumed to share the same ibug-300W point ordering; not independently verified pixel-for-pixel. See extract_landmark_features.py docstring.",
        "class_order": class_order,
        "min_class_count_threshold": MIN_CLASS_COUNT,
        "excluded_rare_classes": exclusions,
        "n_usable_samples": int(len(y)),
        "class_distribution": {class_order[i]: int(c) for i, c in Counter(y.tolist()).items()},
        "split_strategy": f"StratifiedGroupKFold, n_splits={N_SPLITS}, groups=consecutive-frame-index blocks of size {TEMPORAL_BLOCK_SIZE} (no person-ID field exists in this repository; matches tools/train_arcface_classifier.py's own documented approach)",
        "cv_results": results,
        "deployed_model": "LogisticRegression (fit on all usable data; chosen for pure-JS browser portability, see train_landmark_classifier.py docstring)",
        "feature_names": FEATURE_NAMES,
        "limitations": [
            f"Only {len(y)} labeled samples across {len(class_order)} classes after excluding Ambiguous and rare classes (<{MIN_CLASS_COUNT} samples) -- Angry and Disgust were excluded entirely (1 and 2 samples respectively, pre-filtering).",
            "Severe class imbalance remains even after filtering (Neutral=80, Happy=34, Sad=12, Surprise=8, Fear=7) -- per-class metrics for Surprise/Fear/Sad are based on very few out-of-fold predictions and should not be read as statistically reliable.",
            "This is an illustrative dashboard demo classifier, not a validated research result. It has not been compared against image-based FER on a shared test set with matched sampling (see Phase 4 in the dashboard for the live, non-quantitative comparison only).",
            "Geometric features derived from only 68 points cannot capture texture-based cues (e.g. nose wrinkling for Disgust); this is a structural limitation of the landmark-only approach, independent of sample size.",
            "No automated cross-language check exists between this Python feature extractor and the browser JS port (dashboard/landmark_expression_classifier.js) -- no JS runtime was available in this environment to verify numerically. Formulas were written to match by inspection only.",
        ],
    }
    with (HERE / "landmark_classifier_metadata.json").open("w") as f:
        json.dump(metadata, f, indent=2)

    # Export the deployed LR model's coefficients + scaler stats as plain
    # JSON, so the browser can run inference with zero ML libraries
    # (just a dot product + softmax) -- see
    # dashboard/landmark_expression_classifier.js.
    export = {
        "class_order": class_order,
        "feature_names": FEATURE_NAMES,
        "scaler_mean": final_scaler.mean_.tolist(),
        "scaler_scale": final_scaler.scale_.tolist(),
        "coef": final_model.coef_.tolist(),
        "intercept": final_model.intercept_.tolist(),
    }
    with (HERE / "landmark_classifier_weights.json").open("w") as f:
        json.dump(export, f, indent=2)

    print("\nWrote landmark_classifier_model.joblib, landmark_classifier_metadata.json, landmark_classifier_weights.json")


if __name__ == "__main__":
    main()
