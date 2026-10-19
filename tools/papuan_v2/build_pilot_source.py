"""EXP-PAP-001: Papuan V2 pilot-scale source pipeline.

Raw video -> frame extraction -> face detection/crop -> CLAHE, writing
into data/papuan_v2/{faces,clahe}/ (never into any legacy data/
directory -- see data/legacy/README.md).

Per the approved proposal
(docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md, "Approved Decisions"),
the raw source is the SAME video already used by the legacy pipeline,
`data/raw/videos/pesta_babi.mp4` -- Papuan V2 re-derives a fresh set of
frames/faces/CLAHE crops from it using its own config and output paths,
rather than reusing legacy face crops or labels. The video itself is
read-only here and is never copied or modified.

Scope: this run is PILOT-SCALE, not the full-dataset build. It uses a
frame-sampling config (debug mode, max_frames) deliberately limited to
produce enough face crops to support a ~100-200 image pilot annotation
set (docs/proposal/... §10a), without processing the entire ~96-minute
source video. A full-scale Papuan V2 build (out of scope for this
phase, and gated on the EXP-PAP-004 annotation-assistant decision) would
reuse this exact code with debug.enabled=False.

Frame extraction and face detection reuse the existing, unmodified
`FrameExtractor`/`FaceDetector` classes from the legacy pipeline
(src/fer_dataset/pipeline/), always constructed against NEW
data/papuan_v2/... output paths -- never against legacy config or
output directories, so their destructive clear-on-construct behavior
can never touch legacy data.

Extracted frames are intermediate/disposable and are written to a
scratch directory outside data/papuan_v2/ (kept out of the approved,
deliberately minimal data/papuan_v2/{raw,faces,clahe,pilot}/ scaffold);
only face crops and their CLAHE versions are retained as V2 pipeline
outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from fer_dataset.pipeline.face_detector import FaceDetector  # noqa: E402
from fer_dataset.pipeline.frame_extractor import FrameExtractor  # noqa: E402
from fer_dataset.shared.clahe import apply_strategy_b_clahe  # noqa: E402

DEFAULT_VIDEO_PATH = REPO_ROOT / "data" / "raw" / "videos" / "pesta_babi.mp4"
PAPUAN_V2_DIR = REPO_ROOT / "data" / "papuan_v2"
DEFAULT_FPS = 2.0
DEFAULT_MAX_FRAMES = 250  # pilot-scale cap; see module docstring "Scope"
RANDOM_SEED_NOTE = "deterministic sampling (frame_interval + max_frames), no RNG used in this stage"


def sha256_of_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def build(
    video_path: Path,
    faces_dir: Path,
    clahe_dir: Path,
    raw_manifest_path: Path,
    fps: float,
    max_frames: int,
    frames_scratch_dir: Path,
) -> dict:
    if not video_path.exists():
        raise FileNotFoundError(f"Source video not found: {video_path}")

    faces_dir.mkdir(parents=True, exist_ok=True)
    clahe_dir.mkdir(parents=True, exist_ok=True)
    raw_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    frames_scratch_dir.mkdir(parents=True, exist_ok=True)

    print("Computing source video checksum (sha256)...")
    video_sha256 = sha256_of_file(video_path)

    cap = cv2.VideoCapture(str(video_path))
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    frame_interval = max(int(original_fps / fps), 1)

    extractor = FrameExtractor(
        video_path=str(video_path),
        output_dir=str(frames_scratch_dir),
        fps=fps,
        debug=True,
        max_frames=max_frames,
    )
    extractor.clear_outputs()
    frame_paths = extractor.extract()

    detector = FaceDetector(output_dir=str(faces_dir))
    detector.clear_outputs()
    faces_saved = detector.detect(frame_paths)

    face_files = sorted(faces_dir.glob("*.jpg"))
    clahe_count = 0
    for face_path in face_files:
        image = cv2.imread(str(face_path))
        if image is None:
            continue
        clahe_image, _l_weighted, _clip_used = apply_strategy_b_clahe(image)
        cv2.imwrite(str(clahe_dir / face_path.name), clahe_image)
        clahe_count += 1

    manifest = {
        "experiment_id": "EXP-PAP-001",
        "stage": "raw_frame_extraction_face_detection_clahe",
        "source_video": {
            "filename": video_path.name,
            "path": str(video_path.relative_to(REPO_ROOT)),
            "sha256": video_sha256,
            "original_fps": original_fps,
            "total_frames_in_source": total_frames,
        },
        "sampling_config": {
            "target_fps": fps,
            "frame_interval": frame_interval,
            "debug_mode": True,
            "max_frames": max_frames,
            "randomness": RANDOM_SEED_NOTE,
            "note": (
                "Pilot-scale run: max_frames caps the number of sampled frames "
                "well below the full video to keep this stage fast while still "
                "producing enough face crops for a 100-200 image pilot. A "
                "full-scale build would set debug=False / remove max_frames."
            ),
        },
        "outputs": {
            "frames_sampled": len(frame_paths),
            "faces_detected_and_saved": faces_saved,
            "clahe_images_written": clahe_count,
            "faces_dir": str(faces_dir.relative_to(REPO_ROOT)),
            "clahe_dir": str(clahe_dir.relative_to(REPO_ROOT)),
        },
        "code_provenance": {
            "face_detector": "src/fer_dataset/pipeline/face_detector.py (unmodified, reused from legacy pipeline)",
            "frame_extractor": "src/fer_dataset/pipeline/frame_extractor.py (unmodified, reused from legacy pipeline)",
            "clahe": "src/fer_dataset/shared/clahe.py (promoted from tools/realtime_demo/clahe_preprocessing.py, EXP-006)",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    raw_manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote source video manifest: {raw_manifest_path}")
    print(f"Frames sampled: {len(frame_paths)}")
    print(f"Faces saved: {faces_saved}")
    print(f"CLAHE images written: {clahe_count}")

    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, default=DEFAULT_VIDEO_PATH)
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS)
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES)
    parser.add_argument("--faces-dir", type=Path, default=PAPUAN_V2_DIR / "faces")
    parser.add_argument("--clahe-dir", type=Path, default=PAPUAN_V2_DIR / "clahe")
    parser.add_argument(
        "--raw-manifest",
        type=Path,
        default=PAPUAN_V2_DIR / "raw" / "source_video_manifest.json",
    )
    parser.add_argument(
        "--frames-scratch-dir",
        type=Path,
        default=None,
        help="Scratch directory for disposable extracted frames (default: a temp dir).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    scratch = args.frames_scratch_dir or Path(tempfile.mkdtemp(prefix="papuan_v2_frames_"))
    build(
        video_path=args.video,
        faces_dir=args.faces_dir,
        clahe_dir=args.clahe_dir,
        raw_manifest_path=args.raw_manifest,
        fps=args.fps,
        max_frames=args.max_frames,
        frames_scratch_dir=scratch,
    )


if __name__ == "__main__":
    main()
