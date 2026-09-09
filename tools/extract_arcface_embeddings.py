"""Frozen ArcFace embedding extraction (R5).

Extracts a 512-dimensional ArcFace face embedding for each existing face
crop, per the design in docs/ARCFACE_EXPERIMENT_DESIGN.md. This is NOT the
expression classifier — HSEmotion remains the pipeline's expression
classifier, unchanged. This tool only produces a frozen feature-embedding
artifact for later, separate classifier experiments (not implemented here).

Model: InsightFace `buffalo_l` bundle's recognition sub-model
(`w600k_r50.onnx`, ArcFace architecture), accessed via InsightFace's own
`FaceAnalysis`/`ArcFaceONNX` — no new dependency, no re-implementation of
ArcFace's math, no different model file.

Alignment: `FaceAnalysis.get(image)` internally re-detects landmarks in
the given image and, for every loaded "recognition"-task sub-model, calls
that model's own `.get(image, face)` — which for `ArcFaceONNX` performs
`insightface.utils.face_align.norm_crop(image, landmark=face.kps,
image_size=112)` before running inference (confirmed by reading
`insightface/model_zoo/arcface_onnx.py` and `insightface/app/
face_analysis.py`, per docs/ARCFACE_EXPERIMENT_DESIGN.md Section 3-4).
This tool does not call `norm_crop` itself — InsightFace's own `.get()`
call chain already does it, using the standard ArcFace alignment
template, unmodified.

Because each face crop is a bounding-box crop (not the original frame),
`FaceAnalysis` is re-run on the crop itself to obtain crop-local
landmarks, per docs/ARCFACE_EXPERIMENT_DESIGN.md Section 4 — this reuses
the same "re-detect within an already-cropped image" pattern already
established in src/fer_dataset/pipeline/emotion_classifier.py's
visualization path.

Every input face crop resolves to exactly one outcome: "embedded" or a
specific exclusion reason (never silently dropped) — see ExclusionReason.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import insightface
import numpy as np
from tqdm import tqdm

EMBEDDING_MODEL_ID = "buffalo_l/w600k_r50"
EMBEDDING_DIM = 512
ALIGN_SIZE = 112  # ArcFace's standard input size; alignment performed internally by InsightFace.


class ExclusionReason:
    EMBEDDED = "embedded"
    NO_FACE = "excluded_no_face"
    MULTIPLE_FACES = "excluded_multiple_faces"
    INVALID_IMAGE = "excluded_invalid_image"
    EMBEDDING_ERROR = "excluded_embedding_error"


@dataclass
class EmbeddingRecord:
    sample_id: str
    face_filename: str
    status: str
    embedding_model: str
    embedding: list[float] | None


def resolve_faces_to_embedding(faces: list) -> tuple[str, np.ndarray | None]:
    """Pure decision logic, independent of model inference — given the
    list of Face objects InsightFace's FaceAnalysis.get() returned for one
    image, decide the exclusion status and extract the embedding if
    exactly one usable face is present.

    Never guesses which face is correct when zero or multiple are found.
    """
    if len(faces) == 0:
        return ExclusionReason.NO_FACE, None
    if len(faces) > 1:
        return ExclusionReason.MULTIPLE_FACES, None

    face = faces[0]
    try:
        embedding = face.normed_embedding
    except Exception:
        return ExclusionReason.EMBEDDING_ERROR, None

    if embedding is None:
        return ExclusionReason.EMBEDDING_ERROR, None

    embedding = np.asarray(embedding, dtype=np.float32)
    if embedding.shape != (EMBEDDING_DIM,) or not np.all(np.isfinite(embedding)):
        return ExclusionReason.EMBEDDING_ERROR, None

    return ExclusionReason.EMBEDDED, embedding


class ArcFaceEmbedder:
    """Wraps InsightFace's FaceAnalysis, restricted to the detection and
    recognition (ArcFace) sub-models only — genderage/landmark_3d68/
    landmark_2d106 are not needed for this stage and are skipped for
    efficiency; this does not change which detection or recognition model
    is used, only which of buffalo_l's five bundled sub-models are loaded.
    """

    def __init__(self) -> None:
        self.app = insightface.app.FaceAnalysis(
            name="buffalo_l",
            allowed_modules=["detection", "recognition"],
            providers=["CPUExecutionProvider"],
        )
        self.app.prepare(ctx_id=0)

    def embed_image(self, image: np.ndarray) -> tuple[str, np.ndarray | None]:
        faces = self.app.get(image)
        return resolve_faces_to_embedding(faces)


def extract_embeddings(
    input_dir: Path,
    sample_limit: int | None = None,
    embedder: ArcFaceEmbedder | None = None,
) -> tuple[list[EmbeddingRecord], Counter]:
    """Runs frozen ArcFace embedding extraction over every *.jpg face crop
    in input_dir. Returns (records, exclusion_counts). Every input image
    produces exactly one EmbeddingRecord — identity is the crop's own
    filename, never a positional/row-order index."""
    if embedder is None:
        embedder = ArcFaceEmbedder()

    image_paths = sorted(Path(input_dir).glob("*.jpg"))
    if sample_limit is not None:
        image_paths = image_paths[:sample_limit]

    records: list[EmbeddingRecord] = []
    counts: Counter = Counter()

    for image_path in tqdm(image_paths, desc="ArcFace embedding extraction"):
        sample_id = image_path.stem
        image = cv2.imread(str(image_path))

        if image is None:
            counts[ExclusionReason.INVALID_IMAGE] += 1
            records.append(
                EmbeddingRecord(
                    sample_id=sample_id,
                    face_filename=image_path.name,
                    status=ExclusionReason.INVALID_IMAGE,
                    embedding_model=EMBEDDING_MODEL_ID,
                    embedding=None,
                )
            )
            continue

        status, embedding = embedder.embed_image(image)
        counts[status] += 1
        records.append(
            EmbeddingRecord(
                sample_id=sample_id,
                face_filename=image_path.name,
                status=status,
                embedding_model=EMBEDDING_MODEL_ID,
                embedding=embedding.tolist() if embedding is not None else None,
            )
        )

    return records, counts


def save_embeddings_csv(records: list[EmbeddingRecord], output_path: Path) -> None:
    """CSV output with the embedding vector JSON-encoded in one cell.

    Deviation from docs/ARCFACE_EXPERIMENT_DESIGN.md Section 5's Parquet
    recommendation: pyarrow is not currently an installed dependency, and
    this phase is instructed to add no new dependency. CSV+JSON-encoded
    vector is used instead; identity keys (sample_id, face_filename) and
    the embedding_model/status fields are preserved exactly as specified.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import csv

    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "face_filename", "status", "embedding_model", "embedding"])
        for r in records:
            embedding_json = json.dumps(r.embedding) if r.embedding is not None else ""
            writer.writerow([r.sample_id, r.face_filename, r.status, r.embedding_model, embedding_json])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frozen ArcFace (buffalo_l/w600k_r50) embeddings from existing face crops.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/intermediate/faces"),
        help="Directory of existing face-crop .jpg files (default: data/intermediate/faces).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/intermediate/arcface_embeddings/embeddings.csv"),
        help="Output CSV path (default: data/intermediate/arcface_embeddings/embeddings.csv).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of face crops to process (sorted order, deterministic).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    records, counts = extract_embeddings(args.input_dir, sample_limit=args.limit)
    save_embeddings_csv(records, args.output)

    total = len(records)
    print(f"Processed {total} face crop(s) from {args.input_dir}")
    for status in (
        ExclusionReason.EMBEDDED,
        ExclusionReason.NO_FACE,
        ExclusionReason.MULTIPLE_FACES,
        ExclusionReason.INVALID_IMAGE,
        ExclusionReason.EMBEDDING_ERROR,
    ):
        print(f"  {status}: {counts.get(status, 0)}")
    print(f"Saved embeddings to {args.output}")


if __name__ == "__main__":
    main()
