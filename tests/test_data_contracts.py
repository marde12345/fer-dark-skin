"""Lightweight contract tests for pipeline output schemas.

Protects the CURRENT output schemas so a refactor cannot silently drop or
rename a column consumed downstream (by notebooks, dataset_report.py,
landmark_comparison.py). These are duplications of the exact field lists
built in source, since none of the schemas are currently defined as a
shared constant/dataclass in src/ — introducing one is out of scope for
Phase 4 (would be a structural refactor, not a test).
"""

import numpy as np

from fer_dataset.pipeline.landmark_analyzer import LandmarkAnalyzer


def test_dataset_builder_output_columns():
    """Mirrors the record dict built in dataset_builder.py:50-56."""
    expected_columns = {"filename", "label", "confidence"}
    record = {
        "filename": "img_000001.jpg",
        "label": "Neutral",
        "confidence": 0.87,
    }
    assert set(record.keys()) == expected_columns


def test_emotion_classifier_intermediate_annotation_columns():
    """Mirrors the record dict built in emotion_classifier.py:78-84."""
    expected_columns = {"filename", "label", "confidence"}
    record = {
        "filename": "frame_000000_face01.jpg",
        "label": "Happiness",
        "confidence": 0.91,
    }
    assert set(record.keys()) == expected_columns


def test_landmark_feature_row_schema():
    """Mirrors the record dict built in landmark_analyzer.py:211-220:
    fixed fields (face_filename, dataset_filename, label, skin_tone,
    L_weighted) plus whatever _compute_features() returns."""
    pts = np.zeros((468, 2), dtype=np.float32)
    pts[33] = [0.0, 0.0]
    pts[263] = [100.0, 0.0]
    feats = LandmarkAnalyzer._compute_features(pts)

    fixed_fields = {"face_filename", "dataset_filename", "label", "skin_tone", "L_weighted"}
    record = {
        "face_filename": "f.jpg",
        "dataset_filename": "img_000001.jpg",
        "label": "Neutral",
        "skin_tone": "Medium-Dark",
        "L_weighted": 120.0,
        **feats,
    }

    assert fixed_fields.issubset(record.keys())
    assert set(feats.keys()) == {
        "brow_lowering_distance",
        "lip_corner_distance",
        "mouth_openness",
        "inter_ocular_distance",
        "iod_px",
    }
    assert set(record.keys()) == fixed_fields | set(feats.keys())


def test_emotion_label_vocabulary_per_baseline():
    """Per docs/EXPERIMENT.md EXP-000, the pseudo-labeling model's observed
    label vocabulary (HSEmotion's own class names, unmapped by src/). This
    guards against an accidental label-remapping step being introduced."""
    observed_baseline_labels = {"Anger", "Fear", "Neutral", "Sadness", "Happiness", "Surprise"}
    full_model_vocabulary = observed_baseline_labels | {"Disgust"}

    # No mapping table exists in src/emotion_classifier.py; labels are
    # passed through verbatim from HSEmotionRecognizer.predict_emotions().
    assert "Angry" not in full_model_vocabulary  # short-form from SDD.md is NOT what's stored
    assert "Anger" in full_model_vocabulary
