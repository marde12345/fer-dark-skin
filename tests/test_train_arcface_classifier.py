"""Unit tests for tools/train_arcface_classifier.py (R6).

Protects: label handling (valid ground truth only, ambiguous/missing/rare
classes excluded and counted), deterministic class ordering, classifier
configuration, identity preservation, group-aware cross-validation
integrity (no train/test group overlap, exactly one OOF prediction per
sample), and probability validity.

Uses small synthetic embeddings (random vectors are sufficient -- these
tests check plumbing/contracts, not classification quality) so no real
ArcFace model or real dataset is required.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "train_arcface_classifier.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("train_arcface_classifier", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool_module()


# --- Frame index parsing / grouping -----------------------------------------


def test_parse_frame_index_extracts_integer():
    assert tool.parse_frame_index("frame_000123_face01") == 123


def test_parse_frame_index_returns_none_for_unrecognized_pattern():
    assert tool.parse_frame_index("not_a_frame_filename") is None


def test_assign_temporal_group_buckets_consecutive_frames_together():
    # block size 3 (default): frames 0,1,2 -> group 0; frames 3,4,5 -> group 1
    assert tool.assign_temporal_group(0) == tool.assign_temporal_group(2)
    assert tool.assign_temporal_group(2) != tool.assign_temporal_group(3)


# --- Label handling: valid ground truth only --------------------------------


def test_build_usable_samples_excludes_ambiguous_and_counts_it():
    embeddings = {
        "frame_000001_face01.jpg": np.zeros(512, dtype=np.float32),
        "frame_000002_face01.jpg": np.zeros(512, dtype=np.float32),
    }
    gt_labels = {
        "frame_000001_face01.jpg": "Ambiguous",
        "frame_000002_face01.jpg": "Neutral",
    }
    usable, exclusions = tool.build_usable_samples(embeddings, gt_labels, min_class_count=1)

    assert len(usable) == 1
    assert usable[0].gt_label == "Neutral"
    assert exclusions["excluded_ambiguous_label"] == 1


def test_build_usable_samples_excludes_missing_label_and_counts_it():
    embeddings = {"frame_000001_face01.jpg": np.zeros(512, dtype=np.float32)}
    gt_labels = {}  # no manual label at all for this filename

    usable, exclusions = tool.build_usable_samples(embeddings, gt_labels, min_class_count=1)

    assert len(usable) == 0
    assert exclusions["excluded_no_manual_label"] == 1


def test_build_usable_samples_never_trains_on_hsemotion_model_label():
    """Regression guard: build_usable_samples() must only ever look at
    the gt_labels mapping passed to it (which the caller populates from
    manual_labels_export.csv's gt_label column) -- it has no code path
    that reads a 'model_label' field at all."""
    import inspect

    source = inspect.getsource(tool.build_usable_samples)
    assert "model_label" not in source


def test_build_usable_samples_excludes_rare_classes_and_counts_them():
    embeddings = {f"frame_{i:06d}_face01.jpg": np.zeros(512, dtype=np.float32) for i in range(5)}
    gt_labels = {
        "frame_000000_face01.jpg": "Neutral",
        "frame_000001_face01.jpg": "Neutral",
        "frame_000002_face01.jpg": "Neutral",
        "frame_000003_face01.jpg": "Angry",  # only 1 sample -- rare
        "frame_000004_face01.jpg": "Neutral",
    }
    usable, exclusions = tool.build_usable_samples(embeddings, gt_labels, min_class_count=2)

    assert all(s.gt_label != "Angry" for s in usable)
    assert exclusions["excluded_rare_class_Angry"] == 1
    assert len(usable) == 4


# --- Identity preservation ---------------------------------------------------


def test_build_usable_samples_preserves_filename_identity():
    embeddings = {
        "frame_000010_face01.jpg": np.full(512, 0.1, dtype=np.float32),
        "frame_000020_face02.jpg": np.full(512, 0.9, dtype=np.float32),
    }
    gt_labels = {
        "frame_000010_face01.jpg": "Happy",
        "frame_000020_face02.jpg": "Sad",
    }
    usable, _ = tool.build_usable_samples(embeddings, gt_labels, min_class_count=1)

    by_filename = {s.face_filename: s for s in usable}
    assert by_filename["frame_000010_face01.jpg"].sample_id == "frame_000010_face01"
    assert by_filename["frame_000010_face01.jpg"].gt_label == "Happy"
    np.testing.assert_array_equal(by_filename["frame_000010_face01.jpg"].embedding, embeddings["frame_000010_face01.jpg"])


# --- Classifier configuration ------------------------------------------------


def test_classifier_config_is_multinomial_l2_balanced():
    assert tool.CLASSIFIER_CONFIG["penalty"] == "l2"
    assert tool.CLASSIFIER_CONFIG["class_weight"] == "balanced"
    assert tool.CLASSIFIER_CONFIG["random_state"] == tool.RANDOM_SEED


# --- Cross-validation: OOF integrity, no group overlap, class ordering -----


def _make_synthetic_samples(n_per_class=6, n_classes=3, seed=0):
    rng = np.random.default_rng(seed)
    class_names = [f"Class{c}" for c in range(n_classes)]
    samples = []
    frame_idx = 0
    for class_name in class_names:
        # Give each class a well-separated cluster so the classifier can
        # plausibly learn something (not required for these tests, but
        # avoids degenerate all-same-prediction edge cases).
        center = rng.normal(loc=class_names.index(class_name) * 5.0, scale=0.1, size=512)
        for _ in range(n_per_class):
            embedding = (center + rng.normal(scale=0.05, size=512)).astype(np.float32)
            samples.append(
                tool.UsableSample(
                    sample_id=f"frame_{frame_idx:06d}_face01",
                    face_filename=f"frame_{frame_idx:06d}_face01.jpg",
                    gt_label=class_name,
                    embedding=embedding,
                    frame_index=frame_idx,
                )
            )
            frame_idx += 3  # spread across distinct temporal groups
    return samples, class_names


def test_cross_validation_every_sample_gets_exactly_one_oof_prediction():
    samples, class_names = _make_synthetic_samples()
    records = tool.run_cross_validation(samples, class_order=sorted(class_names), n_splits=3)

    assert len(records) == len(samples)
    seen_ids = [r["sample_id"] for r in records]
    assert len(seen_ids) == len(set(seen_ids))  # no duplicates, no gaps
    assert all(r["split_role"] == "out_of_fold_test" for r in records)


def test_cross_validation_train_test_groups_never_overlap():
    """run_cross_validation() itself asserts this internally (leakage
    guard); this test additionally re-derives fold->group assignment from
    the returned records and confirms no group's samples are split
    across two different folds."""
    samples, class_names = _make_synthetic_samples()
    records = tool.run_cross_validation(samples, class_order=sorted(class_names), n_splits=3)

    sample_by_id = {s.sample_id: s for s in samples}
    group_to_folds = {}
    for r in records:
        group = tool.assign_temporal_group(sample_by_id[r["sample_id"]].frame_index)
        group_to_folds.setdefault(group, set()).add(r["fold"])

    for group, folds in group_to_folds.items():
        assert len(folds) == 1, f"group {group} appears as test-fold in multiple folds: {folds}"


def test_cross_validation_uses_deterministic_class_order():
    samples, class_names = _make_synthetic_samples()
    class_order = sorted(class_names)
    records = tool.run_cross_validation(samples, class_order=class_order, n_splits=3)

    for r in records:
        assert r["predicted_label"] in class_order


# --- Probability validity ----------------------------------------------------


def test_prediction_probabilities_are_finite_in_range_and_sum_to_one():
    import json

    samples, class_names = _make_synthetic_samples()
    class_order = sorted(class_names)
    records = tool.run_cross_validation(samples, class_order=class_order, n_splits=3)

    for r in records:
        probs = json.loads(r["prediction_probabilities"])
        values = list(probs.values())
        assert all(np.isfinite(v) for v in values)
        assert all(0.0 <= v <= 1.0 for v in values)
        assert sum(values) == pytest.approx(1.0, abs=1e-6)
        assert set(probs.keys()) == set(class_order)


# --- Determinism -------------------------------------------------------------


def test_cross_validation_is_reproducible_with_fixed_seed():
    samples, class_names = _make_synthetic_samples()
    class_order = sorted(class_names)

    records1 = tool.run_cross_validation(samples, class_order=class_order, n_splits=3, random_seed=7)
    records2 = tool.run_cross_validation(samples, class_order=class_order, n_splits=3, random_seed=7)

    by_id_1 = {r["sample_id"]: (r["fold"], r["predicted_label"]) for r in records1}
    by_id_2 = {r["sample_id"]: (r["fold"], r["predicted_label"]) for r in records2}
    assert by_id_1 == by_id_2


# --- Insufficient groups: does not silently force an invalid split --------


def test_run_cross_validation_reduces_splits_when_too_few_groups(capsys):
    # 2 groups (via frame_index) but requesting 5 splits -- must fall back,
    # not crash or silently fabricate groups.
    samples = [
        tool.UsableSample("s1", "f1.jpg", "A", np.zeros(512, dtype=np.float32), frame_index=0),
        tool.UsableSample("s2", "f2.jpg", "B", np.zeros(512, dtype=np.float32), frame_index=0),
        tool.UsableSample("s3", "f3.jpg", "A", np.zeros(512, dtype=np.float32), frame_index=10),
        tool.UsableSample("s4", "f4.jpg", "B", np.zeros(512, dtype=np.float32), frame_index=10),
    ]
    records = tool.run_cross_validation(samples, class_order=["A", "B"], n_splits=5)

    assert len(records) == 4
    captured = capsys.readouterr()
    assert "only 2 groups exist" in captured.err
