"""Regression tests for frame sampling behavior.

Protects: src/frame_extractor.py FrameExtractor.extract() (lines 32-100),
specifically the frame_interval formula
`max(int(original_fps / target_fps), 1)` (lines 56-59) and the debug
max_frames cutoff (lines 87-88). Frame sampling is classified as a
"Research-methodology change" boundary in docs/EXPERIMENT.md: it determines
which frames exist in the dataset at all.

A tiny synthetic video is generated on the fly with OpenCV's VideoWriter so
these tests require no external video file, no internet access, and no
pretrained model downloads.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from fer_dataset.pipeline.frame_extractor import FrameExtractor


def _write_synthetic_video(path: Path, num_frames: int, fps: float, size=(64, 48)) -> None:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, size)
    for i in range(num_frames):
        frame = np.full((size[1], size[0], 3), i % 256, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_frame_interval_downsamples_at_expected_rate(tmp_path):
    """original_fps=10, target_fps=2 -> interval = max(int(10/2), 1) = 5.
    30 source frames sampled every 5th frame -> 6 saved frames."""
    video_path = tmp_path / "synthetic.mp4"
    _write_synthetic_video(video_path, num_frames=30, fps=10.0)

    output_dir = tmp_path / "frames"
    extractor = FrameExtractor(
        video_path=str(video_path),
        output_dir=str(output_dir),
        fps=2.0,
        debug=False,
        max_frames=100,
    )
    saved = extractor.extract()

    assert len(saved) == 6
    assert all(p.exists() for p in saved)


def test_frame_interval_floor_of_one_when_target_fps_exceeds_source(tmp_path):
    """When target_fps >= original_fps, interval floors to 1 (every frame
    kept) per `max(int(original_fps / target_fps), 1)`."""
    video_path = tmp_path / "synthetic.mp4"
    _write_synthetic_video(video_path, num_frames=10, fps=5.0)

    output_dir = tmp_path / "frames"
    extractor = FrameExtractor(
        video_path=str(video_path),
        output_dir=str(output_dir),
        fps=30.0,
        debug=False,
        max_frames=100,
    )
    saved = extractor.extract()

    assert len(saved) == 10


def test_debug_mode_caps_saved_frames(tmp_path):
    """debug.enabled + debug.max_frames stops extraction early, per
    frame_extractor.py:87-88."""
    video_path = tmp_path / "synthetic.mp4"
    _write_synthetic_video(video_path, num_frames=50, fps=10.0)

    output_dir = tmp_path / "frames"
    extractor = FrameExtractor(
        video_path=str(video_path),
        output_dir=str(output_dir),
        fps=10.0,  # interval = 1, would save all 50 without the debug cap
        debug=True,
        max_frames=7,
    )
    saved = extractor.extract()

    assert len(saved) == 7


def test_missing_video_raises_file_not_found(tmp_path):
    extractor = FrameExtractor(
        video_path=str(tmp_path / "does_not_exist.mp4"),
        output_dir=str(tmp_path / "frames"),
        fps=2.0,
    )
    with pytest.raises(FileNotFoundError):
        extractor.extract()
