"""Orchestration tests for Phase 11A: wiring LandmarkComparison into
fer_dataset.main as an optional, config-gated stage.

These tests protect ONLY pipeline orchestration (whether/when
LandmarkComparison.run() is called, and with what feature_file) — not the
analysis methodology itself (already covered by src/fer_dataset/analysis/
landmark_comparison.py's own unmodified logic, and validated end-to-end by
byte-comparison against Phase 9D's approved outputs, per the completion
report).

main() constructs every pipeline stage unconditionally at the top of the
function (frame extraction, face detection, emotion classification,
landmark analysis, dataset building), each of which would load a real
InsightFace/HSEmotion/MediaPipe model if instantiated for real. To test
main()'s orchestration logic without any model loading, every stage class
is patched with a lightweight stand-in that mimics just the methods main()
calls.
"""

from unittest.mock import MagicMock, patch

import fer_dataset.main as main_module


def _make_config(tmp_path, landmark_comparison_enabled: bool) -> dict:
    return {
        "video": {"path": "unused.mp4", "fps": 2},
        "visualization": {"enabled": False},
        "landmark_analysis": {"enabled": True, "save_format": "npy"},
        "analysis": {"landmark_comparison": {"enabled": landmark_comparison_enabled}},
        "output": {
            "frames": str(tmp_path / "frames"),
            "faces": str(tmp_path / "faces"),
            "intermediate_annotations": str(tmp_path / "intermediate_annotations.csv"),
            "dataset": str(tmp_path / "processed"),
            "processed_annotations": str(tmp_path / "processed" / "annotations.csv"),
            "visualizations": str(tmp_path / "landmarks_vis"),
            "landmarks_468": str(tmp_path / "landmarks_468"),
            "landmark_features": str(tmp_path / "landmark_features.csv"),
        },
        "debug": {"enabled": True, "max_frames": 10},
    }


def _run_main_with_all_stages_mocked(tmp_path, landmark_comparison_enabled: bool):
    """Patches every pipeline/analysis class main() constructs, plus
    load_config, then calls main(). Returns the mock LandmarkComparison
    CLASS (so call args / call count can be inspected) and the mock
    instance actually used inside main()."""
    config = _make_config(tmp_path, landmark_comparison_enabled)

    with patch.object(main_module, "load_config", return_value=config), \
         patch.object(main_module, "FrameExtractor") as MockFrameExtractor, \
         patch.object(main_module, "FaceDetector") as MockFaceDetector, \
         patch.object(main_module, "EmotionClassifier") as MockEmotionClassifier, \
         patch.object(main_module, "DatasetBuilder") as MockDatasetBuilder, \
         patch.object(main_module, "LandmarkAnalyzer") as MockLandmarkAnalyzer, \
         patch.object(main_module, "DatasetReport") as MockDatasetReport, \
         patch.object(main_module, "LandmarkComparison") as MockLandmarkComparison:

        MockFrameExtractor.return_value.extract.return_value = []
        MockFaceDetector.return_value.detect.return_value = 0
        MockEmotionClassifier.return_value.predict.return_value = 0
        MockDatasetBuilder.return_value.build.return_value = 0
        MockLandmarkAnalyzer.return_value.run.return_value = 0
        MockDatasetReport.return_value.generate.return_value = None
        MockLandmarkComparison.return_value.run.return_value = None

        main_module.main()

    return MockLandmarkComparison


def test_landmark_comparison_not_called_when_disabled(tmp_path):
    mock_class = _run_main_with_all_stages_mocked(tmp_path, landmark_comparison_enabled=False)
    mock_class.return_value.run.assert_not_called()


def test_landmark_comparison_called_when_enabled(tmp_path):
    mock_class = _run_main_with_all_stages_mocked(tmp_path, landmark_comparison_enabled=True)
    mock_class.return_value.run.assert_called_once()


def test_landmark_comparison_receives_landmark_features_config_path(tmp_path):
    """Confirms the analysis is constructed with config.output.landmark_features
    as feature_file — the corrected intermediate namespace source, never
    processed_annotations.csv."""
    config = _make_config(tmp_path, landmark_comparison_enabled=True)

    with patch.object(main_module, "load_config", return_value=config), \
         patch.object(main_module, "FrameExtractor") as MockFrameExtractor, \
         patch.object(main_module, "FaceDetector") as MockFaceDetector, \
         patch.object(main_module, "EmotionClassifier") as MockEmotionClassifier, \
         patch.object(main_module, "DatasetBuilder") as MockDatasetBuilder, \
         patch.object(main_module, "LandmarkAnalyzer") as MockLandmarkAnalyzer, \
         patch.object(main_module, "DatasetReport") as MockDatasetReport, \
         patch.object(main_module, "LandmarkComparison") as MockLandmarkComparison:

        MockFrameExtractor.return_value.extract.return_value = []
        MockFaceDetector.return_value.detect.return_value = 0
        MockEmotionClassifier.return_value.predict.return_value = 0
        MockDatasetBuilder.return_value.build.return_value = 0
        MockLandmarkAnalyzer.return_value.run.return_value = 0
        MockDatasetReport.return_value.generate.return_value = None

        main_module.main()

        _, kwargs = MockLandmarkComparison.call_args
        assert kwargs["feature_file"] == config["output"]["landmark_features"]
        assert kwargs["feature_file"] != config["output"]["processed_annotations"]


def test_landmark_comparison_runs_after_landmark_analyzer():
    """Verifies the intended stage ORDER via source inspection: the
    landmark_comparison.run() call must appear after landmark_analyzer.run()
    in main.py's source, matching the documented flow (Landmark/Feature
    Extraction -> (optional) Landmark Comparison Analysis -> Dataset Report)."""
    import inspect

    src = inspect.getsource(main_module)

    landmark_analyzer_call_idx = src.index("landmark_feature_count = landmark_analyzer.run()")
    landmark_comparison_call_idx = src.index("landmark_comparison.run()")
    dataset_report_call_idx = src.index("report.generate()")

    assert landmark_analyzer_call_idx < landmark_comparison_call_idx < dataset_report_call_idx


def test_default_config_has_landmark_comparison_disabled():
    """The repository's committed config/config.yaml must default this
    flag to false — enabling it is an explicit, opt-in action, not the
    default pipeline behavior."""
    import yaml
    from pathlib import Path

    config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert config["analysis"]["landmark_comparison"]["enabled"] is False
