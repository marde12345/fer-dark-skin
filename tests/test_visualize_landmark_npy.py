"""Tests for the Phase 11B CLI parameterization of
tools/visualize_landmark_npy.py.

Protects: CLI argument parsing and the input/output path plumbing added
around the tool's unmodified visualization logic (landmark loading,
plotting geometry, figure size, key-point labels, output format all
untouched — see the tool's own module docstring / completion report).

tools/ is not part of the fer_dataset package, so it's imported here via
a direct file path (importlib), matching how the tool is actually run
(`uv run python tools/visualize_landmark_npy.py`), not as a package module.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "visualize_landmark_npy.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("visualize_landmark_npy", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load_tool_module()


def _synthetic_landmarks_npy(path: Path, n_points: int = 468) -> None:
    rng = np.random.default_rng(0)
    pts = rng.uniform(0, 200, size=(n_points, 2)).astype(np.float32)
    np.save(path, pts)


# --- CLI argument parsing ---------------------------------------------------


def test_parse_args_requires_input():
    with pytest.raises(SystemExit):
        tool.parse_args([])


def test_parse_args_minimal_input_only():
    args = tool.parse_args(["--input", "some_file.npy"])
    assert args.input == Path("some_file.npy")
    assert args.output is None
    assert args.image is None
    assert args.overlay_output is None


def test_parse_args_all_options():
    args = tool.parse_args(
        [
            "--input",
            "landmark.npy",
            "--output",
            "out.png",
            "--image",
            "face.jpg",
            "--overlay-output",
            "overlay.png",
        ]
    )
    assert args.input == Path("landmark.npy")
    assert args.output == Path("out.png")
    assert args.image == Path("face.jpg")
    assert args.overlay_output == Path("overlay.png")


# --- Input validation --------------------------------------------------------


def test_missing_input_path_raises_file_not_found_error(tmp_path):
    missing = tmp_path / "does_not_exist.npy"
    with pytest.raises(FileNotFoundError):
        tool.visualize_landmarks(input_path=missing)


def test_malformed_shape_raises_value_error(tmp_path):
    """Existing (pre-refactor) validation is preserved unchanged: a 1-D
    array is rejected the same way it always was."""
    bad_npy = tmp_path / "bad.npy"
    np.save(bad_npy, np.array([1.0, 2.0, 3.0], dtype=np.float32))

    with pytest.raises(ValueError):
        tool.visualize_landmarks(input_path=bad_npy, output_path=tmp_path / "out.png")


# --- Synthetic end-to-end (no real model/data required) --------------------


def test_visualize_landmarks_blank_canvas_only(tmp_path):
    npy_path = tmp_path / "synthetic.npy"
    _synthetic_landmarks_npy(npy_path)

    output_path = tmp_path / "blank.png"
    tool.visualize_landmarks(input_path=npy_path, output_path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_visualize_landmarks_default_output_path_uses_input_stem(tmp_path, monkeypatch):
    """When --output is omitted, output defaults to
    reports/assets/landmark_<stem>_blank.png relative to cwd — verified
    here against a temp cwd to avoid touching the real reports/ directory."""
    monkeypatch.chdir(tmp_path)
    npy_path = tmp_path / "frame_000123_face01.npy"
    _synthetic_landmarks_npy(npy_path)

    tool.visualize_landmarks(input_path=npy_path)

    expected = tmp_path / "reports" / "assets" / "landmark_frame_000123_face01_blank.png"
    assert expected.exists()


def test_visualize_landmarks_with_overlay_image(tmp_path):
    import cv2

    npy_path = tmp_path / "synthetic.npy"
    _synthetic_landmarks_npy(npy_path)

    image_path = tmp_path / "face.jpg"
    fake_image = (np.random.default_rng(1).uniform(0, 255, size=(100, 100, 3))).astype("uint8")
    cv2.imwrite(str(image_path), fake_image)

    blank_output = tmp_path / "blank.png"
    overlay_output = tmp_path / "overlay.png"
    tool.visualize_landmarks(
        input_path=npy_path,
        output_path=blank_output,
        image_path=image_path,
        overlay_output_path=overlay_output,
    )

    assert blank_output.exists()
    assert overlay_output.exists()
    assert overlay_output.stat().st_size > 0


def test_visualize_landmarks_missing_overlay_image_skips_gracefully(tmp_path, capsys):
    npy_path = tmp_path / "synthetic.npy"
    _synthetic_landmarks_npy(npy_path)

    missing_image = tmp_path / "does_not_exist.jpg"
    blank_output = tmp_path / "blank.png"
    overlay_output = tmp_path / "overlay.png"

    tool.visualize_landmarks(
        input_path=npy_path,
        output_path=blank_output,
        image_path=missing_image,
        overlay_output_path=overlay_output,
    )

    assert blank_output.exists()
    assert not overlay_output.exists()
    assert "skip overlay" in capsys.readouterr().out
