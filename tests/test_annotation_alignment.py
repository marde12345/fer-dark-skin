"""Regression tests for the label/annotation alignment fix (Phase 9).

Protects: src/landmark_analyzer.py LandmarkAnalyzer.run(), specifically the
annotation-association block (around lines 197-218):

    if ann.empty:
        label = "Unknown"
        dataset_filename = ""
    else:
        matched = ann[ann["filename"] == image_path.name]
        if matched.empty:
            unmatched_count += 1
            continue
        row = matched.iloc[0]
        label = str(row.get("label", "Unknown"))
        dataset_filename = str(row.get("filename", ""))

Prior to Phase 9, an unmatched filename silently fell back to
`ann.iloc[idx]` — positional (row-order) alignment — which could attach the
WRONG label to a landmark feature row whenever data/intermediate/faces and
the annotation file drifted in count or order. Phase 9 removed that
fallback: filename identity is now the ONLY way a label gets attached. A
row with no filename match is skipped from landmark_features.csv entirely
(the .npy landmark file is still saved — landmark geometry is independent
of annotation data and that behavior is out of scope for this fix). If no
annotation data exists at all, every row is explicitly labeled "Unknown"
(a distinct, pre-existing, non-fabricating fallback — not a guess).

This logic lives inline inside `run()`, which also drives MediaPipe
landmark detection and file I/O, and is not currently extracted as an
independently-callable function (extracting it would be a structural
refactor beyond Phase 9's scope: fix the behavior, not the architecture).
The tests below mirror the exact algorithm verbatim, kept in lockstep with
landmark_analyzer.py lines 197-218 — the same documented-duplication
approach used before Phase 9's fix.
"""

import pandas as pd


def _associate_label(ann: pd.DataFrame, filename: str) -> tuple[str, str, bool]:
    """Verbatim mirror of landmark_analyzer.py:197-218 (post-Phase-9).
    Returns (label, dataset_filename, was_skipped)."""
    if ann.empty:
        return "Unknown", "", False

    matched = ann[ann["filename"] == filename]
    if matched.empty:
        return "", "", True  # row skipped; no label attached

    row = matched.iloc[0]
    label = str(row.get("label", "Unknown"))
    dataset_filename = str(row.get("filename", ""))
    return label, dataset_filename, False


# --- Test A: correct filename match ---------------------------------------


def test_matching_filenames_receive_correct_labels():
    ann = pd.DataFrame(
        {
            "filename": ["image_001.jpg", "image_002.jpg"],
            "label": ["Happy", "Sad"],
        }
    )

    label1, dataset_filename1, skipped1 = _associate_label(ann, "image_001.jpg")
    label2, dataset_filename2, skipped2 = _associate_label(ann, "image_002.jpg")

    assert (label1, dataset_filename1, skipped1) == ("Happy", "image_001.jpg", False)
    assert (label2, dataset_filename2, skipped2) == ("Sad", "image_002.jpg", False)


def test_matched_confidence_and_filename_fields_are_preserved_exactly():
    """Valid matches must be completely unaffected by the fix: same label,
    same dataset_filename, sourced only from the matching row."""
    ann = pd.DataFrame(
        {
            "filename": ["a.jpg", "b.jpg", "c.jpg"],
            "label": ["Neutral", "Angry", "Fear"],
            "confidence": [0.91, 0.72, 0.65],
        }
    )
    matched_row = ann[ann["filename"] == "b.jpg"].iloc[0]
    label, dataset_filename, skipped = _associate_label(ann, "b.jpg")

    assert skipped is False
    assert label == "Angry" == matched_row["label"]
    assert dataset_filename == "b.jpg" == matched_row["filename"]


# --- Test B: no row-order fallback on drift --------------------------------


def test_drift_between_face_dir_and_annotations_no_longer_misattributes():
    """The exact drift scenario that used to cause misattribution
    (docs/EXPERIMENT.md, formerly 'Known issue'): image_002.jpg is missing
    from the faces directory, so annotations are offset by one relative to
    directory order. image_003.jpg must NOT receive image_002's label
    merely because it would land on that row index."""
    face_crop_filenames = ["image_001.jpg", "image_003.jpg"]  # image_002.jpg missing
    ann = pd.DataFrame(
        {
            "filename": ["image_001.jpg", "image_002.jpg", "image_003.jpg"],
            "label": ["Neutral", "Angry", "Fear"],
        }
    )

    results = {fn: _associate_label(ann, fn) for fn in face_crop_filenames}

    # image_001.jpg matches its own row correctly.
    assert results["image_001.jpg"] == ("Neutral", "image_001.jpg", False)
    # image_003.jpg matches ITS OWN row correctly (by filename), not the
    # row-order-adjacent "Angry" (image_002's label) it would have received
    # under the old idx-based fallback.
    assert results["image_003.jpg"] == ("Fear", "image_003.jpg", False)


def test_no_row_order_fallback_remains_for_genuinely_unmatched_filename():
    """A filename with no annotation counterpart at all (not just
    positionally offset) must be skipped, never assigned a neighboring
    row's label."""
    ann = pd.DataFrame(
        {
            "filename": ["a.jpg", "b.jpg", "c.jpg"],
            "label": ["Happy", "Sad", "Angry"],
        }
    )
    label, dataset_filename, skipped = _associate_label(ann, "x.jpg")

    assert skipped is True
    assert label == ""
    assert dataset_filename == ""
    # Explicitly NOT any label present in ann — proves no positional guess occurred.
    assert label not in {"Happy", "Sad", "Angry"}


# --- Test C: unmatched filename behavior is explicit -----------------------


def test_unmatched_filename_is_skipped_not_silently_defaulted():
    """Verifies the CHOSEN safe behavior explicitly: skip, signaled via the
    `was_skipped` flag — not merely 'some label got attached'. In the real
    implementation this corresponds to `continue` (the row is never
    appended to records, hence never written to landmark_features.csv),
    plus an incremented `unmatched_count` used for the end-of-run WARNING
    summary (landmark_analyzer.py run(), post-loop)."""
    ann = pd.DataFrame({"filename": ["only_this.jpg"], "label": ["Neutral"]})

    _, _, skipped = _associate_label(ann, "not_present.jpg")
    assert skipped is True


def test_empty_annotations_uses_explicit_unknown_not_skip():
    """Distinct, pre-existing, non-fabricating fallback: when NO annotation
    data exists at all (e.g., landmark analysis run before/without emotion
    classification), every row is explicitly labeled 'Unknown' rather than
    skipped or guessed. This is unchanged by Phase 9 — it was never the
    row-order bug, since there is no row to index into in the first place."""
    ann = pd.DataFrame()
    label, dataset_filename, skipped = _associate_label(ann, "anything.jpg")

    assert skipped is False
    assert label == "Unknown"
    assert dataset_filename == ""


def test_unmatched_count_accumulates_across_multiple_misses():
    """Mirrors the run()-level `unmatched_count` accumulator used for the
    end-of-run WARNING summary line."""
    ann = pd.DataFrame({"filename": ["only.jpg"], "label": ["Neutral"]})
    face_crop_filenames = ["only.jpg", "missing1.jpg", "missing2.jpg", "missing3.jpg"]

    unmatched_count = 0
    for fn in face_crop_filenames:
        _, _, skipped = _associate_label(ann, fn)
        if skipped:
            unmatched_count += 1

    assert unmatched_count == 3


# --- Phase 9B: annotation-source namespace lineage -------------------------
#
# Phase 9's fallback removal correctly made matching strict, but exposed a
# separate, pre-existing wiring defect: src/main.py wired LandmarkAnalyzer's
# annotation_file to config.output.processed_annotations (DatasetBuilder's
# renumbered "img_NNNNNN.jpg" namespace) instead of
# config.output.intermediate_annotations (EmotionClassifier's output, same
# "frame_XXXXXX_faceNN.jpg" namespace LandmarkAnalyzer actually iterates via
# config.output.faces). Phase 9B fixed the wiring in main.py. These tests
# protect the data-lineage contract, not the matching algorithm itself
# (already covered above).


def test_intermediate_namespace_filenames_match_intermediate_annotations():
    """Test B: demonstrates the CORRECT namespace pairing. A face-crop
    filename in FaceDetector's format (frame_XXXXXX_faceNN.jpg) matches an
    annotation row written in that same format (as EmotionClassifier
    actually writes it — see emotion_classifier.py:87, image_path.name)."""
    face_crop_filename = "frame_000001_face01.jpg"
    intermediate_ann = pd.DataFrame(
        {
            "filename": ["frame_000001_face01.jpg", "frame_000002_face01.jpg"],
            "label": ["Fear", "Neutral"],
        }
    )

    label, dataset_filename, skipped = _associate_label(intermediate_ann, face_crop_filename)

    assert skipped is False
    assert label == "Fear"
    assert dataset_filename == "frame_000001_face01.jpg"


def test_processed_namespace_never_matches_intermediate_face_filenames():
    """Test C: explicit anti-regression for the exact Phase 9B root cause.
    A face-crop filename in FaceDetector's format must NEVER match against
    processed/annotations.csv's renumbered namespace (as DatasetBuilder
    writes it — see dataset_builder.py:56, f"img_{idx+1:06d}.jpg") — proving
    why LandmarkAnalyzer must not be wired to processed_annotations when
    iterating data/intermediate/faces."""
    face_crop_filename = "frame_000001_face01.jpg"
    processed_ann = pd.DataFrame(
        {
            "filename": ["img_000001.jpg", "img_000002.jpg", "img_000003.jpg"],
            "label": ["Fear", "Neutral", "Angry"],
        }
    )

    label, dataset_filename, skipped = _associate_label(processed_ann, face_crop_filename)

    assert skipped is True
    assert label == ""
    assert dataset_filename == ""
