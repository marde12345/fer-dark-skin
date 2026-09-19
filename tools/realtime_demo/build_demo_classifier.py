"""Fit-once, demo-only Logistic Regression classifier artifact.

This is NOT part of the R6/R7 research evaluation and does not change,
recompute, or supersede any R6/R7/R8/R9 result. Those phases evaluate
the ArcFace-embedding + Logistic Regression approach via
StratifiedGroupKFold cross-validation (tools/train_arcface_classifier.py)
and never persist a final model -- each fold's classifier is fit,
scored, and discarded, by design, since the research question is
"how well does this approach generalize" (an out-of-fold question),
not "produce a deployable model."

The live demo (docs/DEMO_MODEL_COMPARISON.md) needs an actual, loadable
classifier to run in real time, which the research pipeline never
produced. This script closes exactly that gap: it fits ONE Logistic
Regression on ALL 178 existing usable embeddings (same feature source,
same class scope, same hyperparameters, same random_state=42 as
tools/train_arcface_classifier.py's CLASSIFIER_CONFIG), and saves the
fitted model + its class order to disk with joblib.

No new embeddings are extracted. No ArcFace fine-tuning occurs. No
ground truth is changed. Existing data/intermediate/arcface_embeddings/
outputs (embeddings.csv, classifier_predictions.csv,
classifier_metadata.json -- all R6 research artifacts) are read-only
inputs here and are never modified.

Run with: uv run python tools/realtime_demo/build_demo_classifier.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from train_arcface_classifier import (  # noqa: E402
    CLASSIFIER_CONFIG,
    build_usable_samples,
    load_embeddings,
    load_ground_truth_labels,
)

import numpy as np

EMBEDDINGS_CSV = Path("data/intermediate/arcface_embeddings/embeddings.csv")
MANUAL_LABELS_CSV = Path("data/1408-1010-intermediate/manual_labels_export.csv")
OUTPUT_DIR = Path(__file__).resolve().parent / "artifacts"
OUTPUT_MODEL = OUTPUT_DIR / "arcface_lr_demo_model.joblib"
OUTPUT_METADATA = OUTPUT_DIR / "arcface_lr_demo_model_metadata.json"


def main() -> None:
    embeddings = load_embeddings(EMBEDDINGS_CSV)
    gt_labels = load_ground_truth_labels(MANUAL_LABELS_CSV)
    usable, exclusions = build_usable_samples(embeddings, gt_labels)

    class_order = sorted(set(s.gt_label for s in usable))
    X = np.stack([s.embedding for s in usable])
    label_to_index = {label: i for i, label in enumerate(class_order)}
    y = np.array([label_to_index[s.gt_label] for s in usable])

    clf = LogisticRegression(
        penalty=CLASSIFIER_CONFIG["penalty"],
        solver=CLASSIFIER_CONFIG["solver"],
        class_weight=CLASSIFIER_CONFIG["class_weight"],
        max_iter=CLASSIFIER_CONFIG["max_iter"],
        random_state=CLASSIFIER_CONFIG["random_state"],
    )
    clf.fit(X, y)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, OUTPUT_MODEL)

    metadata = {
        "purpose": "DEMO ONLY -- not a research artifact. Fit once on all usable "
        "embeddings for real-time inference in docs/DEMO_MODEL_COMPARISON.md's "
        "live dashboard demo. Never used for, or reported as, an R6/R7/R8/R9 result.",
        "feature_extractor": "ArcFace",
        "arcface_model": "buffalo_l/w600k_r50",
        "embedding_dim": 512,
        "embedding_normalization": "L2 (face.normed_embedding)",
        "classifier": CLASSIFIER_CONFIG,
        "fit_strategy": "single fit on all usable samples (no cross-validation held out) -- "
        "appropriate for a deployable demo artifact, NOT a substitute for R6's "
        "StratifiedGroupKFold generalization evaluation, which remains the source of "
        "record for any accuracy claim.",
        "class_order": class_order,
        "n_training_samples": len(usable),
        "class_counts": {label: int((y == i).sum()) for label, i in label_to_index.items()},
        "exclusions": exclusions,
        "source_embeddings": str(EMBEDDINGS_CSV),
        "source_labels": str(MANUAL_LABELS_CSV),
    }
    with OUTPUT_METADATA.open("w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Trained demo-only classifier on {len(usable)} samples, classes: {class_order}")
    print(f"Saved model to {OUTPUT_MODEL}")
    print(f"Saved metadata to {OUTPUT_METADATA}")


if __name__ == "__main__":
    main()
