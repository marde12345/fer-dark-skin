"""Guards the pilot workflow's core independence constraint (approved
proposal, "Important independence constraints"):

    Human labels -> independent ground truth
    AI predictions -> comparison only

Specifically verifies:
  1. run_ai_predictions.py's output writer never opens human_labels.csv
     at all (by source inspection), so it structurally cannot write to
     or read from it.
  2. pilot_agreement_report.py treats human_labels.csv as read-only:
     running the agreement report does not modify the file's bytes.
  3. init_human_labels_template.py never writes a non-empty gt_label
     itself, and refuses to overwrite a file that already has labeled
     rows unless --force is passed.
  4. sample_pilot.py's sampling is reproducible: same seed + same input
     directory produces an identical pilot set.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "papuan_v2"))

import init_human_labels_template as human_labels_mod  # noqa: E402
import pilot_agreement_report as agreement_mod  # noqa: E402
import run_ai_predictions as ai_predictions_mod  # noqa: E402
import sample_pilot as sample_pilot_mod  # noqa: E402


def test_run_ai_predictions_never_opens_or_paths_to_human_labels():
    """The module docstring is allowed to mention "human_labels.csv" in
    prose (explaining the independence constraint) -- what must never
    happen is any executable reference: no constant/path pointing at it,
    and no open()/Path() call naming it, outside of comments/docstrings."""
    source_path = Path(ai_predictions_mod.__file__)
    executable_lines = []
    in_docstring = False
    for line in source_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.endswith('"""'):
            in_docstring = not in_docstring if stripped.count('"""') == 1 else in_docstring
            continue
        if in_docstring:
            continue
        if stripped.startswith("#"):
            continue
        executable_lines.append(line)

    executable_source = "\n".join(executable_lines)
    assert "human_labels" not in executable_source.lower()

    # No module-level constant/attribute exposes a path to human_labels.csv.
    for name in dir(ai_predictions_mod):
        value = getattr(ai_predictions_mod, name)
        if isinstance(value, Path):
            assert "human_labels" not in str(value).lower()


def test_pilot_agreement_report_does_not_modify_human_labels_file(tmp_path):
    human_labels_path = tmp_path / "human_labels.csv"
    ai_predictions_path = tmp_path / "ai_predictions.csv"

    with human_labels_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "gt_label", "labeled_by", "labeled_at", "notes"])
        writer.writeheader()
        writer.writerow({"image_id": "img1", "gt_label": "Happy", "labeled_by": "x", "labeled_at": "t", "notes": ""})

    with ai_predictions_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["image_id", "ai_model", "ai_prediction", "ai_confidence", "status", "generated_at"]
        )
        writer.writeheader()
        writer.writerow(
            {"image_id": "img1", "ai_model": "model_a", "ai_prediction": "Happy", "ai_confidence": "0.9", "status": "ok", "generated_at": "t"}
        )

    before_bytes = human_labels_path.read_bytes()
    before_mtime = human_labels_path.stat().st_mtime_ns

    agreement_mod.run(
        human_labels_path,
        ai_predictions_path,
        tmp_path / "agreement_metrics.json",
        tmp_path / "confusion_matrices",
        tmp_path / "report.md",
    )

    assert human_labels_path.read_bytes() == before_bytes
    assert human_labels_path.stat().st_mtime_ns == before_mtime


def test_init_human_labels_template_writes_only_blank_labels(tmp_path):
    manifest_path = tmp_path / "pilot_manifest.csv"
    output_path = tmp_path / "human_labels.csv"

    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id"])
        writer.writeheader()
        writer.writerow({"image_id": "img1"})
        writer.writerow({"image_id": "img2"})

    human_labels_mod.build_template(manifest_path, output_path, force=False)

    with output_path.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert all(row["gt_label"] == "" for row in rows)


def test_init_human_labels_template_refuses_to_overwrite_existing_labels(tmp_path):
    manifest_path = tmp_path / "pilot_manifest.csv"
    output_path = tmp_path / "human_labels.csv"

    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id"])
        writer.writeheader()
        writer.writerow({"image_id": "img1"})

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "gt_label", "labeled_by", "labeled_at", "notes"])
        writer.writeheader()
        writer.writerow({"image_id": "img1", "gt_label": "Happy", "labeled_by": "a", "labeled_at": "t", "notes": ""})

    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        human_labels_mod.build_template(manifest_path, output_path, force=False)

    # File must be untouched after the refusal.
    with output_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["gt_label"] == "Happy"


def test_sample_pilot_is_reproducible_with_fixed_seed(tmp_path):
    faces_dir = tmp_path / "faces"
    clahe_dir = tmp_path / "clahe"
    faces_dir.mkdir()
    clahe_dir.mkdir()

    for i in range(20):
        name = f"frame_{i:06d}_face01.jpg"
        (faces_dir / name).write_bytes(b"fake-face-bytes")
        (clahe_dir / name).write_bytes(b"fake-clahe-bytes")

    pilot_dir_1 = tmp_path / "pilot1"
    manifest_1 = tmp_path / "manifest1.csv"
    rows_1 = sample_pilot_mod.sample_pilot(faces_dir, clahe_dir, pilot_dir_1, manifest_1, sample_size=5, seed=42)

    pilot_dir_2 = tmp_path / "pilot2"
    manifest_2 = tmp_path / "manifest2.csv"
    rows_2 = sample_pilot_mod.sample_pilot(faces_dir, clahe_dir, pilot_dir_2, manifest_2, sample_size=5, seed=42)

    ids_1 = sorted(r["image_id"] for r in rows_1)
    ids_2 = sorted(r["image_id"] for r in rows_2)
    assert ids_1 == ids_2
    assert len(ids_1) == 5


def test_sample_pilot_different_seed_can_change_selection(tmp_path):
    faces_dir = tmp_path / "faces"
    clahe_dir = tmp_path / "clahe"
    faces_dir.mkdir()
    clahe_dir.mkdir()

    for i in range(30):
        name = f"frame_{i:06d}_face01.jpg"
        (faces_dir / name).write_bytes(b"fake-face-bytes")
        (clahe_dir / name).write_bytes(b"fake-clahe-bytes")

    rows_seed_a = sample_pilot_mod.sample_pilot(
        faces_dir, clahe_dir, tmp_path / "pilot_a", tmp_path / "manifest_a.csv", sample_size=5, seed=1
    )
    rows_seed_b = sample_pilot_mod.sample_pilot(
        faces_dir, clahe_dir, tmp_path / "pilot_b", tmp_path / "manifest_b.csv", sample_size=5, seed=2
    )

    ids_a = sorted(r["image_id"] for r in rows_seed_a)
    ids_b = sorted(r["image_id"] for r in rows_seed_b)
    assert ids_a != ids_b


def test_arcface_candidate_never_loads_a_detection_model():
    """Locks in the fix for the re-detection-on-crop problem: Candidate B's
    embedder must not construct any object that owns a face detector, so a
    second detection pass on an already-cropped pilot image is structurally
    impossible, not just avoided by convention."""
    source = Path(ai_predictions_mod.__file__).read_text()
    assert "allowed_modules=[\"detection\"" not in source
    assert "FaceAnalysis(" not in source, (
        "DirectArcFaceEmbedder must load the recognition sub-model directly via "
        "insightface.model_zoo.get_model(), not via FaceAnalysis (which requires "
        "a detection model to be present)."
    )
    assert "insightface.model_zoo.get_model" in source
