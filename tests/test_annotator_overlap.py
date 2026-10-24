"""Unit tests for the multi-annotator (A/B) overlap-assignment and
human-human agreement logic added to EXP-PAP-004. No live Label Studio
server is required.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "papuan_v2"))

import export_label_studio_labels as export_mod  # noqa: E402
import human_agreement_report as agreement_mod  # noqa: E402
import label_studio_config as ls_config  # noqa: E402
import setup_label_studio_annotator_b as setup_b_mod  # noqa: E402

REAL_ASSIGNMENT_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "annotator_assignment.csv"
REAL_MANIFEST = REPO_ROOT / "experiments" / "EXP-PAP-004" / "pilot_manifest.csv"


def _write_manifest(tmp_path: Path, image_ids: list[str], filename: str = "pilot_manifest.csv") -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / filename
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id"])
        writer.writeheader()
        for image_id in image_ids:
            writer.writerow({"image_id": image_id})
    return path


# --- Overlap subset: size, determinism, membership -------------------------


def test_overlap_subset_size_is_75_by_default(tmp_path):
    ids = [f"img_{i:04d}" for i in range(150)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path)

    overlap_ids = {r["image_id"] for r in rows if r["overlap"]}
    assert len(overlap_ids) == 75


def test_overlap_subset_size_configurable(tmp_path):
    ids = [f"img_{i:04d}" for i in range(150)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path, overlap_size=10)

    overlap_ids = {r["image_id"] for r in rows if r["overlap"]}
    assert len(overlap_ids) == 10


def test_overlap_selection_is_deterministic_across_runs(tmp_path):
    ids = [f"img_{i:04d}" for i in range(150)]
    manifest_path = _write_manifest(tmp_path, ids)

    rows_1 = ls_config.compute_overlap_assignment(manifest_path=manifest_path)
    rows_2 = ls_config.compute_overlap_assignment(manifest_path=manifest_path)

    overlap_1 = sorted(r["image_id"] for r in rows_1 if r["overlap"])
    overlap_2 = sorted(r["image_id"] for r in rows_2 if r["overlap"])
    assert overlap_1 == overlap_2


def test_overlap_selection_does_not_depend_on_manifest_row_order(tmp_path):
    ids_forward = [f"img_{i:04d}" for i in range(150)]
    ids_reversed = list(reversed(ids_forward))

    manifest_forward = _write_manifest(tmp_path, ids_forward, filename="forward.csv")
    manifest_reversed = _write_manifest(tmp_path, ids_reversed, filename="reversed.csv")

    overlap_forward = {r["image_id"] for r in ls_config.compute_overlap_assignment(manifest_path=manifest_forward) if r["overlap"]}
    overlap_reversed = {r["image_id"] for r in ls_config.compute_overlap_assignment(manifest_path=manifest_reversed) if r["overlap"]}

    assert overlap_forward == overlap_reversed


def test_all_overlap_image_ids_exist_in_manifest(tmp_path):
    ids = [f"img_{i:04d}" for i in range(150)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path)

    overlap_ids = {r["image_id"] for r in rows if r["overlap"]}
    assert overlap_ids.issubset(set(ids))


def test_annotator_A_is_assigned_all_images(tmp_path):
    ids = [f"img_{i:04d}" for i in range(150)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path)

    assert all(r["annotator_A"] for r in rows)
    assert len(rows) == 150


def test_overlap_size_larger_than_pilot_raises(tmp_path):
    ids = [f"img_{i:04d}" for i in range(10)]
    manifest_path = _write_manifest(tmp_path, ids)
    with pytest.raises(ValueError):
        ls_config.compute_overlap_assignment(manifest_path=manifest_path, overlap_size=20)


# --- Task 1 preserved / eligible, no special-casing -------------------------


def test_already_annotated_image_is_still_eligible_for_overlap(tmp_path):
    """Task 1's image (already labeled by A) must not be excluded or
    force-included -- it's just another manifest row to the sampler."""
    ids = ["frame_000008_face01"] + [f"img_{i:04d}" for i in range(149)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path)

    row = next(r for r in rows if r["image_id"] == "frame_000008_face01")
    assert row["annotator_A"] is True
    # Whether overlap is True or False here is a property of the deterministic
    # sample, not a special case -- the assertion is just that it's a normal bool.
    assert isinstance(row["overlap"], bool)


@pytest.mark.skipif(not REAL_ASSIGNMENT_PATH.exists(), reason="real annotator_assignment.csv not present")
def test_real_task1_image_present_in_real_assignment_with_annotator_A_true():
    rows = ls_config.load_annotator_assignment(REAL_ASSIGNMENT_PATH)
    row = next((r for r in rows if r["image_id"] == "frame_000008_face01"), None)
    assert row is not None
    assert row["annotator_A"] is True


# --- CSV round-trip ----------------------------------------------------------


def test_annotator_assignment_csv_round_trip(tmp_path):
    ids = [f"img_{i:04d}" for i in range(20)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path, overlap_size=5)

    out_path = tmp_path / "annotator_assignment.csv"
    ls_config.write_annotator_assignment_csv(rows, out_path)
    loaded = ls_config.load_annotator_assignment(out_path)

    assert len(loaded) == 20
    assert {r["image_id"] for r in loaded if r["overlap"]} == {r["image_id"] for r in rows if r["overlap"]}
    assert all(isinstance(r["annotator_A"], bool) for r in loaded)
    assert all(isinstance(r["annotator_B"], bool) for r in loaded)
    assert all(isinstance(r["overlap"], bool) for r in loaded)


def test_overlap_image_ids_helper(tmp_path):
    ids = [f"img_{i:04d}" for i in range(20)]
    manifest_path = _write_manifest(tmp_path, ids)
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path, overlap_size=5)

    out_path = tmp_path / "annotator_assignment.csv"
    ls_config.write_annotator_assignment_csv(rows, out_path)

    overlap_ids = ls_config.overlap_image_ids(path=out_path)
    assert len(overlap_ids) == 5


# --- Annotator B task-building never copies A's label -----------------------


def test_annotator_b_tasks_built_from_overlap_rows_contain_no_label_fields(tmp_path):
    ids = [f"img_{i:04d}" for i in range(20)]
    manifest_path = _write_manifest(tmp_path, ids)
    assignment_rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path, overlap_size=5)
    overlap_ids = {r["image_id"] for r in assignment_rows if r["overlap"]}

    manifest_rows = ls_config.load_pilot_manifest(manifest_path) if False else [{"image_id": i} for i in ids]
    # build_tasks requires the richer manifest schema (pilot_image_path etc.);
    # verify indirectly: no task payload field ever carries a label/expression value.
    overlap_manifest_rows = [
        {
            "image_id": i,
            "pilot_image_path": f"data/papuan_v2/pilot/images/{i}.jpg",
        }
        for i in overlap_ids
    ]
    tasks = ls_config.build_tasks(overlap_manifest_rows)
    for task in tasks:
        assert "expression" not in task["data"]
        assert "gt_label" not in task["data"]
        assert "human_label" not in task["data"]
        assert "annotator_A_label" not in str(task["data"])


# --- Verify overlap assignment helper (used by setup_label_studio_annotator_b) --


def test_verify_overlap_assignment_rejects_wrong_size(tmp_path, monkeypatch):
    ids = [f"img_{i:04d}" for i in range(150)]
    manifest_path = _write_manifest(tmp_path, ids)
    # Build a BAD assignment with only 50 overlap rows.
    rows = ls_config.compute_overlap_assignment(manifest_path=manifest_path, overlap_size=50)
    assignment_path = tmp_path / "annotator_assignment.csv"
    ls_config.write_annotator_assignment_csv(rows, assignment_path)

    monkeypatch.setattr(ls_config, "PILOT_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(setup_b_mod, "expected_pilot_image_ids", lambda: set(ids))

    with pytest.raises(RuntimeError, match="Expected exactly 75"):
        setup_b_mod.verify_overlap_assignment(assignment_path)


# --- Annotator identity preserved (real Label Studio identity, not faked) ---


def test_export_rows_use_real_email_from_completed_by_dict():
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed_by": {"id": 1, "email": "real.annotator@example.com"},
                    "result": [{"from_name": "expression", "value": {"choices": ["Happy"]}}],
                }
            ],
        }
    ]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-02T00:00:00Z")
    assert rows[0]["annotator_source"] == "real.annotator@example.com"


def test_export_rows_resolve_integer_completed_by_via_user_map():
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed_by": 42,
                    "result": [{"from_name": "expression", "value": {"choices": ["Sad"]}}],
                }
            ],
        }
    ]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-02T00:00:00Z", user_email_by_id={42: "b@example.com"})
    assert rows[0]["annotator_source"] == "b@example.com"


def test_export_rows_never_fakes_identity_when_unresolvable():
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed_by": 999,
                    "result": [{"from_name": "expression", "value": {"choices": ["Fear"]}}],
                }
            ],
        }
    ]
    rows = export_mod.export_rows_from_tasks(tasks, "2026-01-02T00:00:00Z", user_email_by_id={})
    assert rows[0]["annotator_source"] == "label_studio_user_999"


def test_export_write_human_labels_rejected_for_annotator_b_project():
    with pytest.raises(RuntimeError, match="only valid when exporting Annotator A"):
        export_mod.run(
            "http://unused",
            "unused-key",
            write_human_labels=True,
            force=False,
            project_title=export_mod.PROJECT_TITLE_B,
            export_out=Path("/dev/null"),
        )


# --- No AI info exposed / confidence separate from expression (extends existing coverage) --


def test_label_config_still_never_exposes_ai_information_with_two_projects():
    lowered = ls_config.LABEL_CONFIG.lower()
    for term in ["hsemotion", "arcface", "ai_prediction", "annotator_a", "annotator_b"]:
        assert term not in lowered


# --- Human-human agreement (pure computation, synthetic data only) ----------


def test_human_agreement_raises_when_overlap_incomplete():
    overlap_ids = {"img1", "img2", "img3"}
    labels_a = {"img1": {"human_label": "Happy"}, "img2": {"human_label": "Sad"}, "img3": {"human_label": "Fear"}}
    labels_b = {"img1": {"human_label": "Happy"}}  # missing img2, img3

    with pytest.raises(RuntimeError, match="Refusing to compute a partial result"):
        agreement_mod.compute_agreement(overlap_ids, labels_a, labels_b)


def test_human_agreement_perfect_match():
    overlap_ids = {"img1", "img2"}
    labels_a = {"img1": {"human_label": "Happy"}, "img2": {"human_label": "Sad"}}
    labels_b = {"img1": {"human_label": "Happy"}, "img2": {"human_label": "Sad"}}

    result = agreement_mod.compute_agreement(overlap_ids, labels_a, labels_b)
    assert result["raw_agreement"] == 1.0
    assert result["n_disagreements"] == 0
    assert result["adjudicated"] is False


def test_human_agreement_reports_disagreements_without_resolving_them():
    overlap_ids = {"img1", "img2"}
    labels_a = {"img1": {"human_label": "Happy"}, "img2": {"human_label": "Sad"}}
    labels_b = {"img1": {"human_label": "Neutral"}, "img2": {"human_label": "Sad"}}

    result = agreement_mod.compute_agreement(overlap_ids, labels_a, labels_b)
    assert result["raw_agreement"] == 0.5
    assert result["n_disagreements"] == 1
    assert result["disagreements"][0]["image_id"] == "img1"
    assert result["disagreements"][0]["annotator_A_label"] == "Happy"
    assert result["disagreements"][0]["annotator_B_label"] == "Neutral"
    assert result["adjudicated"] is False
    assert "not_computed" not in result  # this script doesn't pick a winner, but it does compute the metric
