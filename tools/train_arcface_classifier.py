"""Frozen ArcFace embeddings + multinomial Logistic Regression (R6).

Implements the first proposed classifier from docs/ARCFACE_EXPERIMENT_DESIGN.md
Section 7: a multinomial, L2-regularized Logistic Regression trained on
frozen ArcFace embeddings (produced by tools/extract_arcface_embeddings.py).

This is an implementation-validation phase, NOT the final R7 evaluation.
No accuracy/F1/statistical comparison against HSEmotion is computed here
(see docs/EXPERIMENT.md EXP-007) — only the out-of-fold prediction
artifact and basic sanity checks needed to confirm the pipeline works
correctly.

Ground truth: manual_labels_export.csv's `gt_label` column ONLY. HSEmotion
predictions (`model_label`) are never used as targets — using them would
be circular, since HSEmotion is the system this future evaluation is
meant to be independent of.

Grouping/leakage: the source video's frame index (parsed from each face
crop's filename, e.g. "frame_000123_face01" -> 123) is the only identity-
adjacent metadata available (no person-ID field exists anywhere in the
repository, confirmed in docs/ARCFACE_EXPERIMENT_DESIGN.md Section 8).
Consecutive frame indices are grouped into fixed-size temporal blocks so
that near-adjacent frames (very likely the same individual(s), same
pose/lighting, since frames are sampled from one continuous video) always
fall entirely within one CV fold, never split across train and test.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

FRAME_INDEX_PATTERN = re.compile(r"^frame_(\d+)_face\d+$")

# Classes with fewer than this many usable (embedded + valid-labeled)
# samples are excluded from training/evaluation entirely -- see
# docs/EXPERIMENT.md EXP-007 for the exact counts and reasoning. This is
# a documented deviation from R4's "seven classes" assumption, not a
# silent substitution.
MIN_CLASS_COUNT = 5

RANDOM_SEED = 42
N_SPLITS = 5
TEMPORAL_BLOCK_SIZE = 3

CLASSIFIER_CONFIG = {
    "algorithm": "LogisticRegression",
    "multi_class_strategy": "multinomial (scikit-learn's default for lbfgs with >2 classes)",
    "penalty": "l2",
    "solver": "lbfgs",
    "class_weight": "balanced",
    "max_iter": 1000,
    "random_state": RANDOM_SEED,
}


@dataclass
class UsableSample:
    sample_id: str
    face_filename: str
    gt_label: str
    embedding: np.ndarray
    frame_index: int


def parse_frame_index(face_filename_stem: str) -> int | None:
    match = FRAME_INDEX_PATTERN.match(face_filename_stem)
    if match is None:
        return None
    return int(match.group(1))


def load_embeddings(embeddings_csv: Path) -> dict[str, np.ndarray]:
    """Returns {face_filename: embedding} for rows with status == 'embedded' only."""
    result: dict[str, np.ndarray] = {}
    with embeddings_csv.open() as f:
        for row in csv.DictReader(f):
            if row["status"] != "embedded":
                continue
            result[row["face_filename"]] = np.array(json.loads(row["embedding"]), dtype=np.float32)
    return result


def load_ground_truth_labels(manual_labels_csv: Path) -> dict[str, str]:
    """Returns {filename: gt_label} for ALL rows (including Ambiguous/missing
    -- filtering happens in build_usable_samples, so exclusions are counted
    explicitly rather than silently dropped here)."""
    result: dict[str, str] = {}
    with manual_labels_csv.open() as f:
        for row in csv.DictReader(f):
            result[row["filename"]] = row["gt_label"]
    return result


def build_usable_samples(
    embeddings: dict[str, np.ndarray],
    gt_labels: dict[str, str],
    min_class_count: int = MIN_CLASS_COUNT,
) -> tuple[list[UsableSample], dict[str, int]]:
    """Joins embeddings to ground-truth labels by filename (never row
    order). Returns (usable_samples, exclusion_counts)."""
    exclusions: Counter = Counter()
    candidates: list[UsableSample] = []

    for face_filename, embedding in embeddings.items():
        gt_label = gt_labels.get(face_filename)
        if gt_label is None:
            exclusions["excluded_no_manual_label"] += 1
            continue
        gt_label = gt_label.strip()
        if gt_label == "" or gt_label.lower() == "nan":
            exclusions["excluded_missing_label"] += 1
            continue
        if gt_label == "Ambiguous":
            exclusions["excluded_ambiguous_label"] += 1
            continue

        stem = Path(face_filename).stem
        frame_index = parse_frame_index(stem)
        if frame_index is None:
            exclusions["excluded_unparseable_filename"] += 1
            continue

        candidates.append(
            UsableSample(
                sample_id=stem,
                face_filename=face_filename,
                gt_label=gt_label,
                embedding=embedding,
                frame_index=frame_index,
            )
        )

    class_counts = Counter(c.gt_label for c in candidates)
    rare_classes = {label for label, count in class_counts.items() if count < min_class_count}
    for label in rare_classes:
        exclusions[f"excluded_rare_class_{label}"] = class_counts[label]

    usable = [c for c in candidates if c.gt_label not in rare_classes]
    return usable, dict(exclusions)


def assign_temporal_group(frame_index: int, block_size: int = TEMPORAL_BLOCK_SIZE) -> int:
    """Deterministic grouping: consecutive frame indices are chunked into
    fixed-size blocks. This does not require or invent a person-identity
    field -- it only ensures near-adjacent frames (most likely to share
    identity/pose/lighting) fall in the same CV fold."""
    return frame_index // block_size


def run_cross_validation(
    samples: list[UsableSample],
    class_order: list[str],
    n_splits: int = N_SPLITS,
    random_seed: int = RANDOM_SEED,
) -> list[dict]:
    """Runs StratifiedGroupKFold cross-validation. Returns one out-of-fold
    prediction record per sample -- every sample is evaluated exactly once,
    by a model that never saw it (or its group) during training."""
    X = np.stack([s.embedding for s in samples])
    label_to_index = {label: i for i, label in enumerate(class_order)}
    y = np.array([label_to_index[s.gt_label] for s in samples])
    groups = np.array([assign_temporal_group(s.frame_index) for s in samples])

    n_groups = len(set(groups.tolist()))
    effective_splits = min(n_splits, n_groups)
    if effective_splits < n_splits:
        print(
            f"WARNING: requested n_splits={n_splits} but only {n_groups} groups exist; "
            f"using n_splits={effective_splits} instead.",
            file=sys.stderr,
        )

    splitter = StratifiedGroupKFold(n_splits=effective_splits, shuffle=True, random_state=random_seed)

    oof_records = [None] * len(samples)
    for fold_id, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups)):
        # Leakage guard: no group may appear in both train and test.
        train_groups = set(groups[train_idx].tolist())
        test_groups = set(groups[test_idx].tolist())
        assert train_groups.isdisjoint(test_groups), (
            f"Fold {fold_id}: train/test group overlap detected: {train_groups & test_groups}"
        )

        clf = LogisticRegression(
            penalty=CLASSIFIER_CONFIG["penalty"],
            solver=CLASSIFIER_CONFIG["solver"],
            class_weight=CLASSIFIER_CONFIG["class_weight"],
            max_iter=CLASSIFIER_CONFIG["max_iter"],
            random_state=CLASSIFIER_CONFIG["random_state"],
        )
        clf.fit(X[train_idx], y[train_idx])

        probabilities = clf.predict_proba(X[test_idx])
        predictions = clf.predict(X[test_idx])

        for local_i, sample_idx in enumerate(test_idx):
            sample = samples[sample_idx]
            probs = probabilities[local_i]
            oof_records[sample_idx] = {
                "sample_id": sample.sample_id,
                "face_filename": sample.face_filename,
                "gt_label": sample.gt_label,
                "predicted_label": class_order[predictions[local_i]],
                "fold": fold_id,
                "split_role": "out_of_fold_test",
                "prediction_probabilities": json.dumps(
                    {class_order[i]: float(p) for i, p in enumerate(probs)}
                ),
            }

    assert all(r is not None for r in oof_records), "Every sample must receive exactly one OOF prediction."
    return oof_records


def save_predictions_csv(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "face_filename",
        "gt_label",
        "predicted_label",
        "fold",
        "split_role",
        "prediction_probabilities",
    ]
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)


def save_metadata_json(
    output_path: Path,
    class_order: list[str],
    n_splits_used: int,
    n_groups: int,
    class_counts: dict[str, int],
    exclusions: dict[str, int],
    total_input_samples: int,
) -> None:
    metadata = {
        "feature_extractor": "ArcFace",
        "arcface_model": "buffalo_l/w600k_r50",
        "embedding_dim": 512,
        "embedding_normalization": "L2",
        "classifier": CLASSIFIER_CONFIG,
        "evaluation_strategy": "StratifiedGroupKFold",
        "n_splits_requested": N_SPLITS,
        "n_splits_used": n_splits_used,
        "grouping_strategy": f"temporal block of {TEMPORAL_BLOCK_SIZE} consecutive frame indices",
        "n_groups": n_groups,
        "class_order": class_order,
        "min_class_count_threshold": MIN_CLASS_COUNT,
        "class_counts_used_for_training": class_counts,
        "exclusions": exclusions,
        "total_input_samples": total_input_samples,
        "label_source": "manual_labels_export.csv:gt_label (NOT HSEmotion model_label)",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(metadata, f, indent=2)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train/evaluate a frozen-ArcFace-embedding Logistic Regression classifier "
        "via grouped, stratified cross-validation. Implementation-validation only -- "
        "no final research metrics are computed here.",
    )
    parser.add_argument("--embeddings", type=Path, default=Path("data/intermediate/arcface_embeddings/embeddings.csv"))
    parser.add_argument("--manual-labels", type=Path, default=Path("data/1408-1010-intermediate/manual_labels_export.csv"))
    parser.add_argument("--output-predictions", type=Path, default=Path("data/intermediate/arcface_embeddings/classifier_predictions.csv"))
    parser.add_argument("--output-metadata", type=Path, default=Path("data/intermediate/arcface_embeddings/classifier_metadata.json"))
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    embeddings = load_embeddings(args.embeddings)
    gt_labels = load_ground_truth_labels(args.manual_labels)
    usable, exclusions = build_usable_samples(embeddings, gt_labels)

    class_order = sorted(set(s.gt_label for s in usable))
    class_counts = dict(Counter(s.gt_label for s in usable))
    n_groups = len(set(assign_temporal_group(s.frame_index) for s in usable))

    print(f"Total embedded samples available: {len(embeddings)}")
    print(f"Usable samples (valid label + not rare class): {len(usable)}")
    print(f"Class order: {class_order}")
    print(f"Class counts: {class_counts}")
    print(f"Number of temporal groups: {n_groups}")
    print(f"Exclusions: {exclusions}")

    records = run_cross_validation(usable, class_order)
    save_predictions_csv(records, args.output_predictions)

    n_splits_used = len(set(r["fold"] for r in records))
    save_metadata_json(
        args.output_metadata,
        class_order=class_order,
        n_splits_used=n_splits_used,
        n_groups=n_groups,
        class_counts=class_counts,
        exclusions=exclusions,
        total_input_samples=len(embeddings),
    )

    print(f"Saved {len(records)} out-of-fold predictions to {args.output_predictions}")
    print(f"Saved metadata to {args.output_metadata}")


if __name__ == "__main__":
    main()
