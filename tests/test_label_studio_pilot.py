"""Unit tests for the EXP-PAP-004 Label Studio pilot setup — all against
pure configuration/payload-building logic in
tools/papuan_v2/label_studio_config.py and the export-mapping logic in
tools/papuan_v2/export_label_studio_labels.py. No live Label Studio
server is required or used (per approved scope).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "papuan_v2"))

import export_label_studio_labels as export_mod  # noqa: E402
import label_studio_config as ls_config  # noqa: E402

REAL_MANIFEST = REPO_ROOT / "experiments" / "EXP-PAP-004" / "pilot_manifest.csv"
REAL_PILOT_IMAGES_DIR = REPO_ROOT / "data" / "papuan_v2" / "pilot" / "images"

AI_LEAKAGE_TERMS = [
    "hsemotion",
    "arcface",
    "ai_prediction",
    "ai_model",
    "model_confidence",
    "logisticregression",
]


def _write_manifest(tmp_path: Path, image_ids: list[str]) -> Path:
    path = tmp_path / "pilot_manifest.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_id",
                "face_filename",
                "source_face_path",
                "source_clahe_path",
                "pilot_image_path",
                "sample_seed",
                "sampled_at",
            ],
        )
        writer.writeheader()
        for image_id in image_ids:
            writer.writerow(
                {
                    "image_id": image_id,
                    "face_filename": f"{image_id}.jpg",
                    "source_face_path": f"data/papuan_v2/faces/{image_id}.jpg",
                    "source_clahe_path": f"data/papuan_v2/clahe/{image_id}.jpg",
                    "pilot_image_path": f"data/papuan_v2/pilot/images/{image_id}.jpg",
                    "sample_seed": 42,
                    "sampled_at": "2026-01-01T00:00:00+00:00",
                }
            )
    return path


# --- Label config content ---------------------------------------------


def test_label_config_contains_all_seven_expression_classes():
    for expression in ls_config.EXPRESSION_CLASSES:
        assert f'value="{expression}"' in ls_config.LABEL_CONFIG
    assert len(ls_config.EXPRESSION_CLASSES) == 7


def test_expression_field_is_required_single_select():
    # crude but reliable XML substring check on the "expression" Choices tag
    expression_tag_start = ls_config.LABEL_CONFIG.index('name="expression"')
    tag_slice = ls_config.LABEL_CONFIG[expression_tag_start - 40 : expression_tag_start + 100]
    assert 'choice="single"' in tag_slice
    assert 'required="true"' in tag_slice


def test_confidence_field_is_separate_and_optional():
    assert 'name="confidence"' in ls_config.LABEL_CONFIG
    confidence_tag_start = ls_config.LABEL_CONFIG.index('name="confidence"')
    tag_slice = ls_config.LABEL_CONFIG[confidence_tag_start - 40 : confidence_tag_start + 100]
    assert 'required="false"' in tag_slice
    for level in ls_config.CONFIDENCE_LEVELS:
        assert f'value="{level}"' in ls_config.LABEL_CONFIG


def test_label_config_never_exposes_ai_information():
    lowered = ls_config.LABEL_CONFIG.lower()
    for term in AI_LEAKAGE_TERMS:
        assert term not in lowered


def test_instructions_tell_annotator_not_to_use_model_predictions():
    lowered = ls_config.ANNOTATION_INSTRUCTIONS.lower()
    assert "model prediction" in lowered
    assert "confidence as low" in lowered


# --- Task-building (pure) -----------------------------------------------


def test_build_tasks_produces_no_ai_fields(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1", "img2", "img3"])
    tasks = ls_config.build_tasks(manifest_path=manifest_path)

    assert len(tasks) == 3
    for task in tasks:
        assert set(task["data"].keys()) == {"image", "image_id", "experiment_id"}
        for key, value in task["data"].items():
            assert "hsemotion" not in str(value).lower()
            assert "arcface" not in str(value).lower()


def test_build_tasks_image_ids_match_manifest_exactly(tmp_path):
    ids = ["img_a", "img_b", "img_c", "img_d"]
    manifest_path = _write_manifest(tmp_path, ids)
    tasks = ls_config.build_tasks(manifest_path=manifest_path)

    task_ids = {t["data"]["image_id"] for t in tasks}
    assert task_ids == set(ids)


def test_local_file_url_uses_manifest_recorded_path_not_reconstruction(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["frame_000001_face01"])
    url = ls_config.local_file_url("frame_000001_face01", manifest_path=manifest_path)
    assert url == "/data/local-files/?d=data/papuan_v2/pilot/images/frame_000001_face01.jpg"


def test_local_file_url_raises_for_unknown_image_id(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1"])
    with pytest.raises(KeyError):
        ls_config.local_file_url("does_not_exist", manifest_path=manifest_path)


# --- Idempotent import logic ---------------------------------------------


def test_tasks_missing_from_project_excludes_already_imported(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1", "img2", "img3"])
    manifest_rows = ls_config.load_pilot_manifest(manifest_path)

    missing = ls_config.tasks_missing_from_project({"img1"}, manifest_rows)
    missing_ids = {t["data"]["image_id"] for t in missing}
    assert missing_ids == {"img2", "img3"}


def test_tasks_missing_from_project_returns_nothing_when_all_present(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1", "img2"])
    manifest_rows = ls_config.load_pilot_manifest(manifest_path)

    missing = ls_config.tasks_missing_from_project({"img1", "img2"}, manifest_rows)
    assert missing == []


# --- Pilot verification against manifest ----------------------------------


def test_verify_pilot_images_present_raises_on_missing_file(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1", "img2"])
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img1.jpg").write_bytes(b"fake")
    # img2.jpg intentionally missing

    with pytest.raises(RuntimeError, match="have no file"):
        ls_config.verify_pilot_images_present(manifest_path=manifest_path, images_dir=images_dir)


def test_verify_pilot_images_present_raises_on_extra_file(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1"])
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img1.jpg").write_bytes(b"fake")
    (images_dir / "extra.jpg").write_bytes(b"fake")

    with pytest.raises(RuntimeError, match="not in the manifest"):
        ls_config.verify_pilot_images_present(manifest_path=manifest_path, images_dir=images_dir)


def test_verify_pilot_images_present_passes_on_exact_match(tmp_path):
    manifest_path = _write_manifest(tmp_path, ["img1", "img2"])
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img1.jpg").write_bytes(b"fake")
    (images_dir / "img2.jpg").write_bytes(b"fake")

    ls_config.verify_pilot_images_present(manifest_path=manifest_path, images_dir=images_dir)  # no raise


@pytest.mark.skipif(not REAL_MANIFEST.exists(), reason="real EXP-PAP-004 pilot manifest not present")
def test_real_pilot_manifest_matches_real_pilot_images_exactly():
    ls_config.verify_pilot_images_present()  # no raise
    ids = ls_config.expected_pilot_image_ids()
    assert len(ids) == 150


# --- Export mapping (pure, no live server) --------------------------------


def test_export_rows_from_tasks_extracts_label_and_confidence_separately():
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed_by": {"id": 1, "email": "annotator-a@local.test"},
                    "result": [
                        {"from_name": "expression", "value": {"choices": ["Happy"]}},
                        {"from_name": "confidence", "value": {"choices": ["High"]}},
                    ],
                }
            ],
        }
    ]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-02T00:00:00Z")

    assert len(rows) == 1
    row = rows[0]
    assert row["image_id"] == "img1"
    assert row["human_label"] == "Happy"
    assert row["human_confidence"] == "High"
    assert row["annotator_source"] == "annotator-a@local.test"
    assert row["human_verified"] is True


def test_export_rows_from_tasks_confidence_optional():
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {
                    "created_at": "2026-01-01T00:00:00Z",
                    "result": [{"from_name": "expression", "value": {"choices": ["Sad"]}}],
                }
            ],
        }
    ]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-02T00:00:00Z")
    assert rows[0]["human_confidence"] == ""


def test_export_rows_from_tasks_skips_unannotated_tasks():
    tasks = [{"data": {"image_id": "img1"}, "annotations": []}]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-02T00:00:00Z")
    assert rows == []


def test_export_rows_from_tasks_uses_latest_annotation_only():
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {
                    "created_at": "2026-01-01T00:00:00Z",
                    "result": [{"from_name": "expression", "value": {"choices": ["Sad"]}}],
                },
                {
                    "created_at": "2026-01-03T00:00:00Z",
                    "result": [{"from_name": "expression", "value": {"choices": ["Happy"]}}],
                },
            ],
        }
    ]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-04T00:00:00Z")
    assert rows[0]["human_label"] == "Happy"


def test_export_rows_to_human_labels_rows_never_puts_confidence_in_gt_label():
    export_rows = [
        {
            "experiment_id": "EXP-PAP-004",
            "image_id": "img1",
            "human_label": "Fear",
            "human_confidence": "Low",
            "annotator_source": "label_studio_blind_pilot",
            "human_verified": True,
            "exported_at": "2026-01-02T00:00:00Z",
        }
    ]
    human_rows = export_mod.export_rows_to_human_labels_rows(export_rows)

    assert len(human_rows) == 1
    row = human_rows[0]
    assert row["gt_label"] == "Fear"
    assert "Low" not in row["gt_label"]
    assert row["notes"] == "confidence=Low"
    assert set(row.keys()) == {"image_id", "gt_label", "labeled_by", "labeled_at", "notes"}


def test_write_human_labels_csv_refuses_to_overwrite_existing_labels(tmp_path):
    out_path = tmp_path / "human_labels.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=export_mod.HUMAN_LABELS_FIELDNAMES)
        writer.writeheader()
        writer.writerow({"image_id": "img1", "gt_label": "Happy", "labeled_by": "x", "labeled_at": "t", "notes": ""})

    rows = [{"image_id": "img1", "gt_label": "Sad", "labeled_by": "y", "labeled_at": "t2", "notes": ""}]
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        export_mod.write_human_labels_csv(rows, out_path, force=False)

    with out_path.open() as f:
        preserved = list(csv.DictReader(f))
    assert preserved[0]["gt_label"] == "Happy"


def test_setup_script_never_writes_human_labels_csv():
    """Source-level guard: setup_label_studio_pilot.py's executable code
    (docstrings/comments excluded) must not reference human_labels.csv --
    only export_label_studio_labels.py may write it, and only when
    explicitly asked."""
    setup_path = REPO_ROOT / "tools" / "papuan_v2" / "setup_label_studio_pilot.py"
    executable_lines = []
    in_docstring = False
    for line in setup_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.endswith('"""'):
            in_docstring = not in_docstring if stripped.count('"""') == 1 else in_docstring
            continue
        if in_docstring or stripped.startswith("#"):
            continue
        executable_lines.append(line)

    assert "human_labels" not in "\n".join(executable_lines).lower()


# --- Local storage connection idempotency (pure, mocked client objects) ----


class _FakeProject:
    def __init__(self, existing_storages):
        self._existing_storages = existing_storages
        self.connect_calls = []

    def get_import_storages(self):
        return self._existing_storages

    def connect_local_import_storage(self, local_store_path, title=""):
        self.connect_calls.append(local_store_path)


def test_ensure_local_storage_connected_skips_when_already_present(monkeypatch):
    import setup_label_studio_pilot as setup_mod

    project = _FakeProject([{"type": "localfiles", "path": str(setup_mod.PILOT_IMAGES_DIR)}])
    setup_mod.ensure_local_storage_connected(project)

    assert project.connect_calls == []


def test_ensure_local_storage_connected_connects_when_missing(monkeypatch):
    import setup_label_studio_pilot as setup_mod

    project = _FakeProject([])
    setup_mod.ensure_local_storage_connected(project)

    assert project.connect_calls == [str(setup_mod.PILOT_IMAGES_DIR)]
