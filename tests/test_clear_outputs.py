"""Regression tests for Phase 5: removing the destructive
"clear output directory on construction" side effect.

Prior behavior (Known Issue, docs/REPO_AUDIT_REPORT.md Section D.4): merely
instantiating FrameExtractor, FaceDetector, EmotionClassifier, or
DatasetBuilder deleted the contents of their output directory/annotation
file as a constructor side effect — before any processing method was
called. This meant object construction alone could destroy a previous run's
outputs.

Phase 5 moves this cleanup into an explicit `clear_outputs()` method on
each class. Construction no longer deletes anything; `src/main.py` now
calls `clear_outputs()` explicitly, immediately before the corresponding
processing call, preserving the same clean-start guarantee for a normal
pipeline run.

FaceDetector and EmotionClassifier load real InsightFace/HSEmotion models
in their constructors, so Test A for those two classes is intentionally
NOT included here (would require model downloads/heavy loading, prohibited
for this test suite per Phase 4's constraints, still in force). Their
`clear_outputs()` bodies are simple, already-existing, well-understood
operations (`clear_directory()` / `Path.unlink()`) that are directly
covered by Test B (explicit cleanup works) instead.

Phase 9A addendum — pipeline-breaking regression fix:
Phase 5's move to explicit clear_outputs() calls, each immediately before
its own stage's processing call, introduced a real bug: EmotionClassifier
and DatasetBuilder are both configured with the SAME file as
`annotation_file` (config.output.intermediate_annotations — EmotionClassifier
WRITES it, DatasetBuilder READS it). DatasetBuilder.clear_outputs() used to
unlink that file "for cleanliness," but by the time it ran (main.py stage
order: classifier.clear_outputs() -> classifier.predict() [writes the file]
-> builder.clear_outputs() [deleted the file just written!] -> builder.build()
[FileNotFoundError]), it was destroying its own required input, which
EmotionClassifier's own clear_outputs() had already correctly cleared
before writing. DatasetBuilder.clear_outputs() no longer touches
self.annotation_file at all — it was never DatasetBuilder's output to
begin with (build() only ever reads it, never writes it).
"""

from pathlib import Path

from fer_dataset.pipeline.dataset_builder import DatasetBuilder
from fer_dataset.pipeline.frame_extractor import FrameExtractor


# --- FrameExtractor -----------------------------------------------------
# Cheap to instantiate for real (no model loading), so both Test A and
# Test B are covered directly against the real class.


def test_frame_extractor_construction_is_non_destructive(tmp_path):
    output_dir = tmp_path / "frames"
    output_dir.mkdir()
    sentinel = output_dir / "sentinel.jpg"
    sentinel.write_bytes(b"fake-jpg-bytes")

    FrameExtractor(
        video_path=str(tmp_path / "unused.mp4"),
        output_dir=str(output_dir),
        fps=2.0,
    )

    assert sentinel.exists()


def test_frame_extractor_clear_outputs_removes_jpgs(tmp_path):
    output_dir = tmp_path / "frames"
    output_dir.mkdir()
    sentinel = output_dir / "sentinel.jpg"
    sentinel.write_bytes(b"fake-jpg-bytes")

    extractor = FrameExtractor(
        video_path=str(tmp_path / "unused.mp4"),
        output_dir=str(output_dir),
        fps=2.0,
    )
    extractor.clear_outputs()

    assert not sentinel.exists()


# --- DatasetBuilder -------------------------------------------------------
# Also cheap to instantiate for real (no model loading).


def test_dataset_builder_construction_is_non_destructive(tmp_path):
    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    sentinel_image = output_dir / "sentinel.jpg"
    sentinel_image.write_bytes(b"fake-jpg-bytes")
    annotation_file = output_dir / "annotations.csv"
    annotation_file.write_text("filename,label,confidence\n")

    DatasetBuilder(
        input_dir=str(tmp_path / "faces"),
        annotation_file=str(tmp_path / "faces" / "intermediate_annotations.csv"),
        output_dir=str(output_dir),
    )

    assert sentinel_image.exists()
    assert annotation_file.exists()


def test_dataset_builder_clear_outputs_removes_stale_jpgs_only(tmp_path):
    """Test B: DatasetBuilder's own genuinely-stale output (output_dir/*.jpg)
    is still cleared, per its original (pre-Phase-9A) behavior."""
    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    sentinel_image = output_dir / "sentinel.jpg"
    sentinel_image.write_bytes(b"fake-jpg-bytes")
    input_annotation_file = tmp_path / "faces" / "intermediate_annotations.csv"
    input_annotation_file.parent.mkdir(parents=True, exist_ok=True)
    input_annotation_file.write_text("filename,label,confidence\n")

    builder = DatasetBuilder(
        input_dir=str(tmp_path / "faces"),
        annotation_file=str(input_annotation_file),
        output_dir=str(output_dir),
    )
    builder.clear_outputs()

    assert not sentinel_image.exists()


def test_dataset_builder_clear_outputs_does_not_delete_its_annotation_input(tmp_path):
    """Test A (Phase 9A regression test): DatasetBuilder.clear_outputs()
    must NEVER delete self.annotation_file — it is an INPUT (read in
    build()), not an output DatasetBuilder produces. This is exactly the
    scenario that crashed the real pipeline: annotation_file already
    contains real rows (as EmotionClassifier would have just written)."""
    output_dir = tmp_path / "processed"
    output_dir.mkdir()

    annotation_file = tmp_path / "faces" / "intermediate_annotations.csv"
    annotation_file.parent.mkdir(parents=True, exist_ok=True)
    annotation_file.write_text("filename,label,confidence\nframe_000000_face01.jpg,Neutral,0.9\n")

    builder = DatasetBuilder(
        input_dir=str(tmp_path / "faces"),
        annotation_file=str(annotation_file),
        output_dir=str(output_dir),
    )
    builder.clear_outputs()

    assert annotation_file.exists()
    assert "frame_000000_face01.jpg" in annotation_file.read_text()


def test_dataset_builder_build_succeeds_after_clear_outputs_when_annotation_file_is_shared(tmp_path):
    """End-to-end reproduction of the exact crash scenario: the SAME file
    path is used as EmotionClassifier's output and DatasetBuilder's input
    (as main.py actually wires config.output.intermediate_annotations to
    both). Simulates: classifier writes the file -> builder.clear_outputs()
    -> builder.build() must NOT raise FileNotFoundError."""
    faces_dir = tmp_path / "faces"
    faces_dir.mkdir()
    face_file = faces_dir / "frame_000000_face01.jpg"
    face_file.write_bytes(b"fake-jpg-bytes")

    shared_annotation_file = faces_dir / "intermediate_annotations.csv"
    # Simulates EmotionClassifier.predict() having just written this file.
    shared_annotation_file.write_text(
        "filename,label,confidence\nframe_000000_face01.jpg,Neutral,0.9\n"
    )

    output_dir = tmp_path / "processed"
    builder = DatasetBuilder(
        input_dir=str(faces_dir),
        annotation_file=str(shared_annotation_file),
        output_dir=str(output_dir),
    )

    builder.clear_outputs()  # must not delete shared_annotation_file
    record_count = builder.build()  # must not raise FileNotFoundError

    assert record_count == 1
    assert (output_dir / "images" / "img_000001.jpg").exists()


# --- main.py entry-point wiring (source inspection, no execution) --------
# Instantiating the full pipeline in main() requires downloading/loading
# InsightFace, HSEmotion, and MediaPipe models — explicitly out of scope
# for this test suite. Instead, this test verifies via static inspection
# that main.py calls clear_outputs() explicitly, before each processing
# call, for every stage that has one. This directly protects against the
# destructive behavior being silently reintroduced inside a constructor
# without a corresponding explicit call in main.py.


def test_main_calls_clear_outputs_before_each_stage_processing_call():
    main_src = (Path(__file__).resolve().parent.parent / "src" / "fer_dataset" / "main.py").read_text()

    pairs = [
        ("extractor.clear_outputs()", "frame_paths = extractor.extract()"),
        ("detector.clear_outputs()", "face_count = detector.detect(frame_paths)"),
        ("classifier.clear_outputs()", "prediction_count = classifier.predict()"),
        ("builder.clear_outputs()", "dataset_count = builder.build()"),
    ]

    for clear_call, process_call in pairs:
        assert clear_call in main_src
        assert process_call in main_src
        assert main_src.index(clear_call) < main_src.index(process_call)


def test_main_wires_classifier_and_builder_to_the_same_annotation_file():
    """Documents WHY the Phase 9A fix is necessary: main.py's config wiring
    genuinely does point EmotionClassifier's and DatasetBuilder's
    annotation_file at the same config key (config.output.intermediate_annotations).
    This is not a hypothetical scenario — it's the exact real wiring, which
    is why DatasetBuilder.clear_outputs() must never delete that file."""
    main_src = (Path(__file__).resolve().parent.parent / "src" / "fer_dataset" / "main.py").read_text()

    classifier_call = main_src[
        main_src.index("classifier = EmotionClassifier(") : main_src.index("landmark_analyzer = LandmarkAnalyzer(")
    ]
    builder_call = main_src[
        main_src.index("builder = DatasetBuilder(") : main_src.index("report = DatasetReport(")
    ]

    assert 'annotation_file=config["output"]["intermediate_annotations"]' in classifier_call
    assert 'annotation_file=config["output"]["intermediate_annotations"]' in builder_call


def test_dataset_builder_clear_outputs_source_never_touches_annotation_file():
    """Test C (source-inspection, per Phase 9A Step 5): a static guard
    against the exact regression recurring — DatasetBuilder.clear_outputs()
    must not reference self.annotation_file at all. Full pipeline ordering
    (classifier.predict() writes the shared file, then builder.clear_outputs()
    runs, then builder.build() reads it) is additionally covered end-to-end,
    without loading any heavyweight model, by
    test_dataset_builder_build_succeeds_after_clear_outputs_when_annotation_file_is_shared
    above."""
    src = (Path(__file__).resolve().parent.parent / "src" / "fer_dataset" / "pipeline" / "dataset_builder.py").read_text()
    clear_outputs_body = src[src.index("def clear_outputs") : src.index("def build")]

    # The docstring is expected to mention self.annotation_file (to explain
    # why it's excluded) — what must never reappear is code that acts on
    # it (e.g. deleting it).
    assert "annotation_file.unlink" not in clear_outputs_body
    assert "annotation_file.exists" not in clear_outputs_body
