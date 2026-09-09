"""Unit tests for tools/extract_arcface_embeddings.py (R5).

Protects: the embedding contract (shape/finiteness), identity-key
preservation (no row-order joins), and exclusion accounting — the parts
of R5 that don't require loading a real ArcFace model. Real-model
inference is exercised only in the separate real-data smoke test
(documented in the R5 completion report), not in this unit-test file,
per the instruction not to require a model download/load in every test.

tools/ is not part of the fer_dataset package, so it's imported here via
a direct file path (importlib), matching the existing precedent in
tests/test_visualize_landmark_npy.py.
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "extract_arcface_embeddings.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("extract_arcface_embeddings", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool_module()


def _fake_face(embedding=None):
    face = MagicMock()
    face.normed_embedding = embedding
    return face


# --- Embedding contract: shape, finiteness ---------------------------------


def test_resolve_faces_to_embedding_returns_512d_finite_vector():
    good_embedding = np.random.default_rng(0).normal(size=512).astype(np.float32)
    good_embedding = good_embedding / np.linalg.norm(good_embedding)  # simulate L2-normalized
    status, embedding = tool.resolve_faces_to_embedding([_fake_face(good_embedding)])

    assert status == tool.ExclusionReason.EMBEDDED
    assert embedding.shape == (512,)
    assert embedding.dtype == np.float32
    assert np.all(np.isfinite(embedding))


def test_resolve_faces_to_embedding_rejects_wrong_dimension():
    wrong_dim = np.zeros(128, dtype=np.float32)
    status, embedding = tool.resolve_faces_to_embedding([_fake_face(wrong_dim)])

    assert status == tool.ExclusionReason.EMBEDDING_ERROR
    assert embedding is None


def test_resolve_faces_to_embedding_rejects_non_finite_values():
    bad_embedding = np.full(512, np.nan, dtype=np.float32)
    status, embedding = tool.resolve_faces_to_embedding([_fake_face(bad_embedding)])

    assert status == tool.ExclusionReason.EMBEDDING_ERROR
    assert embedding is None


def test_resolve_faces_to_embedding_handles_none_embedding():
    status, embedding = tool.resolve_faces_to_embedding([_fake_face(None)])

    assert status == tool.ExclusionReason.EMBEDDING_ERROR
    assert embedding is None


# --- Alignment: standard ArcFace input size documented ----------------------


def test_align_size_matches_arcface_standard_112():
    assert tool.ALIGN_SIZE == 112
    assert tool.EMBEDDING_DIM == 512


# --- Exclusion handling: zero-face and multiple-face cases ------------------


def test_zero_faces_is_excluded_not_guessed():
    status, embedding = tool.resolve_faces_to_embedding([])

    assert status == tool.ExclusionReason.NO_FACE
    assert embedding is None


def test_multiple_faces_is_excluded_not_guessed():
    face1 = _fake_face(np.ones(512, dtype=np.float32))
    face2 = _fake_face(np.ones(512, dtype=np.float32) * 2)
    status, embedding = tool.resolve_faces_to_embedding([face1, face2])

    assert status == tool.ExclusionReason.MULTIPLE_FACES
    assert embedding is None


# --- Determinism: same input face list produces equivalent output ----------


def test_resolve_faces_to_embedding_is_deterministic_for_same_input():
    embedding_vec = np.random.default_rng(42).normal(size=512).astype(np.float32)
    face = _fake_face(embedding_vec)

    status1, emb1 = tool.resolve_faces_to_embedding([face])
    status2, emb2 = tool.resolve_faces_to_embedding([face])

    assert status1 == status2
    np.testing.assert_array_equal(emb1, emb2)


# --- Identity / no row-order joins, using the full extract_embeddings() loop,
# with the heavyweight ArcFaceEmbedder replaced by a lightweight fake ------


def test_extract_embeddings_preserves_filename_identity_not_row_order(tmp_path):
    """Regression guard: identity must come from each file's own name,
    never from iteration/row position. Simulates two crops where the
    embedder's result depends on file content, and confirms each output
    record's face_filename/sample_id matches its own input file — not
    e.g. the previous file's identity due to an off-by-one row-order bug."""
    faces_dir = tmp_path / "faces"
    faces_dir.mkdir()

    # Two 1x1 pixel images with different content so we can distinguish them.
    import cv2

    img_a = np.zeros((4, 4, 3), dtype=np.uint8)
    img_b = np.full((4, 4, 3), 255, dtype=np.uint8)
    path_a = faces_dir / "frame_000001_face01.jpg"
    path_b = faces_dir / "frame_000002_face01.jpg"
    cv2.imwrite(str(path_a), img_a)
    cv2.imwrite(str(path_b), img_b)

    embedding_a = np.full(512, 0.1, dtype=np.float32)
    embedding_b = np.full(512, 0.9, dtype=np.float32)

    class DistinguishingFakeEmbedder:
        def embed_image(self, image):
            # Distinguish by mean pixel value, proving the correct image
            # (not just "some" image) was routed to the correct output row.
            if image.mean() < 128:
                return tool.ExclusionReason.EMBEDDED, embedding_a
            return tool.ExclusionReason.EMBEDDED, embedding_b

    records, counts = tool.extract_embeddings(faces_dir, embedder=DistinguishingFakeEmbedder())

    by_filename = {r.face_filename: r for r in records}
    assert by_filename["frame_000001_face01.jpg"].sample_id == "frame_000001_face01"
    assert by_filename["frame_000001_face01.jpg"].embedding == pytest.approx(embedding_a.tolist())
    assert by_filename["frame_000002_face01.jpg"].sample_id == "frame_000002_face01"
    assert by_filename["frame_000002_face01.jpg"].embedding == pytest.approx(embedding_b.tolist())
    assert counts[tool.ExclusionReason.EMBEDDED] == 2


def test_extract_embeddings_counts_invalid_image_without_calling_embedder(tmp_path):
    faces_dir = tmp_path / "faces"
    faces_dir.mkdir()
    corrupt_path = faces_dir / "corrupt.jpg"
    corrupt_path.write_bytes(b"not a real jpg")

    class ShouldNotBeCalledEmbedder:
        def embed_image(self, image):
            raise AssertionError("embedder must not be called for an unreadable image")

    records, counts = tool.extract_embeddings(faces_dir, embedder=ShouldNotBeCalledEmbedder())

    assert counts[tool.ExclusionReason.INVALID_IMAGE] == 1
    assert records[0].status == tool.ExclusionReason.INVALID_IMAGE
    assert records[0].embedding is None


def test_save_embeddings_csv_round_trips_identity_and_embedding(tmp_path):
    record = tool.EmbeddingRecord(
        sample_id="frame_000001_face01",
        face_filename="frame_000001_face01.jpg",
        status=tool.ExclusionReason.EMBEDDED,
        embedding_model=tool.EMBEDDING_MODEL_ID,
        embedding=[0.1] * 512,
    )
    excluded_record = tool.EmbeddingRecord(
        sample_id="frame_000002_face01",
        face_filename="frame_000002_face01.jpg",
        status=tool.ExclusionReason.NO_FACE,
        embedding_model=tool.EMBEDDING_MODEL_ID,
        embedding=None,
    )

    output_path = tmp_path / "embeddings.csv"
    tool.save_embeddings_csv([record, excluded_record], output_path)

    import csv
    import json

    with output_path.open() as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["sample_id"] == "frame_000001_face01"
    assert rows[0]["face_filename"] == "frame_000001_face01.jpg"
    assert json.loads(rows[0]["embedding"]) == [0.1] * 512
    assert rows[1]["status"] == tool.ExclusionReason.NO_FACE
    assert rows[1]["embedding"] == ""
