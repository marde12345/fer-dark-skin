"""Tests for configuration values and their (current) wiring status.

Step 4 of Phase 4 asks that experiment-boundary constants/configuration be
tested "where practical." These tests assert the config file's raw values
(so a silent edit to config/config.yaml is caught) and document which keys
are actually consumed by src/main.py.

Per docs/REPO_AUDIT_REPORT.md Section J, six config.yaml keys were dead
(not read anywhere in src/): face_detection.confidence, quality.min_face_size,
quality.blur_threshold, expression.confidence_threshold, output.save_landmarks,
output.save_csv. These were removed in Phase 7 (docs/REFACTORING_PLAN.md).
No functionality those keys implied (quality filtering, confidence
filtering, optional CSV saving) was implemented — this was cleanup only.

These tests do not duplicate business logic and do not test model
internals (no InsightFace/HSEmotion/MediaPipe model loading).
"""

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def test_config_file_loads_and_has_expected_top_level_sections():
    config = _load_config()
    expected_sections = {
        "video",
        "visualization",
        "landmark_analysis",
        "analysis",
        "output",
        "debug",
    }
    assert expected_sections.issubset(config.keys())


def test_landmark_comparison_analysis_flag_defaults_to_disabled():
    """Phase 11A (docs/REFACTORING_PLAN.md, Approved Decision #2): wiring
    landmark_comparison into main.py must be opt-in. The committed default
    must keep existing pipeline behavior unchanged unless a researcher
    explicitly enables it."""
    config = _load_config()
    assert config["analysis"]["landmark_comparison"]["enabled"] is False


def test_video_and_output_keys_actually_consumed_by_main(monkeypatch=None):
    """These keys ARE read by src/main.py (lines 20-57) and therefore are
    live experiment-boundary values, not dead config."""
    config = _load_config()
    assert "path" in config["video"]
    assert "fps" in config["video"]
    assert config["video"]["fps"] == 2

    required_output_keys = {
        "frames",
        "faces",
        "intermediate_annotations",
        "dataset",
        "processed_annotations",
        "visualizations",
        "landmarks_468",
        "landmark_features",
    }
    assert required_output_keys.issubset(config["output"].keys())


def test_debug_mode_matches_phase0_baseline():
    """Regression guard for the Phase 0 baseline reproducibility: if this
    value changes, docs/baseline_snapshots/phase0/ is no longer comparable
    without re-running under the new configuration."""
    config = _load_config()
    assert config["debug"]["enabled"] is True
    assert config["debug"]["max_frames"] == 100


def test_landmark_analysis_config_matches_baseline():
    config = _load_config()
    assert config["landmark_analysis"]["enabled"] is True
    assert config["landmark_analysis"]["save_format"] == "npy"


def test_previously_dead_config_keys_have_been_removed():
    """Regression guard for Phase 7 cleanup (docs/REFACTORING_PLAN.md):
    the six config keys identified as dead in docs/REPO_AUDIT_REPORT.md
    Section J (never read by any code in src/) must stay removed. This
    protects against silently reintroducing config that looks active but
    isn't wired to anything — the exact failure mode that created the
    original dead-config finding."""
    config = _load_config()

    assert "face_detection" not in config
    assert "quality" not in config
    assert "expression" not in config
    assert "save_landmarks" not in config.get("output", {})
    assert "save_csv" not in config.get("output", {})


def test_no_functionality_was_implemented_for_removed_dead_keys():
    """Phase 7 was cleanup only: removing config.yaml keys that implied
    unimplemented features (quality filtering, confidence-based filtering)
    must NOT have come bundled with an implementation of those features.
    Confirms src/ still contains no filtering logic tied to face size,
    blur, or prediction-confidence thresholds."""
    pipeline_dir = Path(__file__).resolve().parent.parent / "src" / "fer_dataset" / "pipeline"
    face_detector_src = (pipeline_dir / "face_detector.py").read_text()
    emotion_classifier_src = (pipeline_dir / "emotion_classifier.py").read_text()

    assert "blur" not in face_detector_src.lower()
    assert "min_face_size" not in face_detector_src
    assert "confidence_threshold" not in emotion_classifier_src


def test_landmark_analyzer_wired_to_intermediate_annotations_not_processed():
    """Regression guard for Phase 9B (docs/REFACTORING_PLAN.md): LandmarkAnalyzer
    iterates face crops from config.output.faces (data/intermediate/faces,
    "frame_XXXXXX_faceNN.jpg" namespace). Its annotation_file MUST be
    config.output.intermediate_annotations (written by EmotionClassifier in
    that same namespace), NOT config.output.processed_annotations (DatasetBuilder's
    renumbered "img_NNNNNN.jpg" namespace) — the latter can never produce a
    filename match and was the root cause fixed in Phase 9B. Source-inspection
    test: avoids loading MediaPipe/InsightFace/HSEmotion models."""
    main_src = (Path(__file__).resolve().parent.parent / "src" / "fer_dataset" / "main.py").read_text()

    landmark_analyzer_call = main_src[
        main_src.index("landmark_analyzer = LandmarkAnalyzer(") : main_src.index("builder = DatasetBuilder(")
    ]

    assert 'annotation_file=config["output"]["intermediate_annotations"]' in landmark_analyzer_call
    assert 'annotation_file=config["output"]["processed_annotations"]' not in landmark_analyzer_call
