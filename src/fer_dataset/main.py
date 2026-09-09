import yaml

from fer_dataset.pipeline.frame_extractor import FrameExtractor
from fer_dataset.pipeline.face_detector import FaceDetector
from fer_dataset.pipeline.landmark_analyzer import LandmarkAnalyzer
from fer_dataset.pipeline.emotion_classifier import EmotionClassifier
from fer_dataset.pipeline.dataset_builder import DatasetBuilder
from fer_dataset.pipeline.logger import section
from fer_dataset.pipeline.dataset_report import DatasetReport
from fer_dataset.analysis.landmark_comparison import LandmarkComparison


def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    extractor = FrameExtractor(
        video_path=config["video"]["path"],
        output_dir=config["output"]["frames"],
        fps=config["video"]["fps"],
        debug=config["debug"]["enabled"],
        max_frames=config["debug"]["max_frames"],
    )

    
    detector = FaceDetector(
        output_dir=config["output"]["faces"],
    )

    classifier = EmotionClassifier(
        input_dir=config["output"]["faces"],
        annotation_file=config["output"]["intermediate_annotations"],
        visualization_dir=config["output"]["visualizations"],
        visualize=config["visualization"]["enabled"],
    )

    landmark_analyzer = LandmarkAnalyzer(
        input_dir=config["output"]["faces"],
        output_dir=config["output"]["landmarks_468"],
        # LandmarkAnalyzer iterates face crops from config["output"]["faces"]
        # (data/intermediate/faces, "frame_XXXXXX_faceNN.jpg" namespace), so
        # its annotation source must be intermediate_annotations.csv, which
        # is written by EmotionClassifier in that same filename namespace —
        # NOT processed_annotations.csv, whose filenames were renumbered by
        # DatasetBuilder into a different "img_NNNNNN.jpg" namespace.
        annotation_file=config["output"]["intermediate_annotations"],
        feature_file=config["output"]["landmark_features"],
        save_format=config["landmark_analysis"]["save_format"],
    )

    builder = DatasetBuilder(
        input_dir=config["output"]["faces"],
        annotation_file=config["output"]["intermediate_annotations"],
        output_dir=config["output"]["dataset"],
    )

    landmark_comparison = LandmarkComparison(
        # Uses the same corrected landmark feature source as LandmarkAnalyzer
        # writes (config.output.landmark_features) — never
        # processed_annotations.csv, per the Phase 9B data-lineage fix.
        feature_file=config["output"]["landmark_features"],
        report_dir="reports",
    )

    report = DatasetReport(
        annotation_file=config["output"]["processed_annotations"],
        output_dir="reports",
    )

    section("Frame Extraction")
    extractor.clear_outputs()
    frame_paths = extractor.extract()

    section("Face Detection")
    detector.clear_outputs()
    face_count = detector.detect(frame_paths)

    section("Emotion Classification")
    classifier.clear_outputs()
    prediction_count = classifier.predict()

    section("Dataset Builder")
    builder.clear_outputs()
    dataset_count = builder.build()

    landmark_feature_count = 0
    if config["landmark_analysis"]["enabled"]:
        section("Landmark Analysis (Optional, Stage 4.5)")
        landmark_feature_count = landmark_analyzer.run()
    else:
        print("\nLandmark Analysis skipped (landmark_analysis.enabled = false)")

    if config["analysis"]["landmark_comparison"]["enabled"]:
        section("Landmark Comparison Analysis (Optional)")
        landmark_comparison.run()
    else:
        print("\nLandmark Comparison Analysis skipped (analysis.landmark_comparison.enabled = false)")

    section("Dataset Report")
    report.generate()

    print()
    print("=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    print(f"Frames Extracted : {len(frame_paths)}")
    print(f"Faces Detected   : {face_count}")
    print(f"Landmark Features: {landmark_feature_count}")
    print(f"Predictions      : {prediction_count}")
    print(f"Dataset Images   : {dataset_count}")
    print("Report Generated : reports/dataset_report.md")
    print("=" * 60)


if __name__ == "__main__":
    main()