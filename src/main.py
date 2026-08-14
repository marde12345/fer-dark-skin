import yaml

from frame_extractor import FrameExtractor
from face_detector import FaceDetector
from landmark_analyzer import LandmarkAnalyzer
from emotion_classifier import EmotionClassifier
from dataset_builder import DatasetBuilder
from logger import section
from dataset_report import DatasetReport


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
        annotation_file=config["output"]["processed_annotations"],
        feature_file=config["output"]["landmark_features"],
        save_format=config["landmark_analysis"]["save_format"],
    )

    builder = DatasetBuilder(
        input_dir=config["output"]["faces"],
        annotation_file=config["output"]["intermediate_annotations"],
        output_dir=config["output"]["dataset"],
    )

    report = DatasetReport(
        annotation_file=config["output"]["processed_annotations"],
        output_dir="reports",
    )

    section("Frame Extraction")
    frame_paths = extractor.extract()

    section("Face Detection")
    face_count = detector.detect(frame_paths)

    section("Emotion Classification")
    prediction_count = classifier.predict()

    section("Dataset Builder")
    dataset_count = builder.build()

    landmark_feature_count = 0
    if config["landmark_analysis"]["enabled"]:
        section("Landmark Analysis (Optional, Stage 4.5)")
        landmark_feature_count = landmark_analyzer.run()
    else:
        print("\nLandmark Analysis skipped (landmark_analysis.enabled = false)")

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