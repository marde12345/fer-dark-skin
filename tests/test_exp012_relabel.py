"""Server-free tests for the EXP-012 relabeling configuration."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "exp012"))

import relabel_config as cfg  # noqa: E402


def test_landmark_subset_is_brows_eyes_mouth():
    assert len(cfg.LANDMARK_SUBSET) == 42
    assert cfg.LANDMARK_SUBSET == list(range(17, 27)) + list(range(36, 68))


def test_label_config_has_ambiguous_and_no_model_or_old_label_fields():
    assert "Ambiguous" in cfg.EXPRESSION_CLASSES
    assert set(cfg.EVAL_CLASSES) <= set(cfg.EXPRESSION_CLASSES)
    lowered = cfg.LABEL_CONFIG.lower()
    for banned in ("hsemotion", "arcface", "$prediction", "$gt_label", "$model_label", "$old_label"):
        assert banned not in lowered
    for name in ("expression", "confidence", "overlay_quality", "notes"):
        assert f'name="{name}"' in cfg.LABEL_CONFIG


def test_unstandardize_inverts_delivery_letterbox():
    t = {"scale_factor": "2.5", "pad_left": "10", "pad_top": "4"}
    x, y = 13.0, 21.0
    assert cfg.unstandardize(x * 2.5 + 10, y * 2.5 + 4, t) == (x, y)


def test_tasks_expose_only_allowed_keys(tmp_path):
    doc_root = tmp_path
    data_root = tmp_path / "repo"
    (data_root / cfg.LEGACY_FACES_REL).mkdir(parents=True)
    landmarks = {"a": {"status": cfg.STATUS_MISSING, "source": "none", "points": {}}}
    tasks = cfg.build_tasks(["a"], landmarks, data_root, data_root / cfg.OVERLAY_REL, doc_root)
    assert set(tasks[0]["data"]) == cfg.TASK_DATA_KEYS
    assert tasks[0]["data"]["image"] == "/data/local-files/?d=repo/data/1408-1010-intermediate/faces/a.jpg"
    assert tasks[0]["data"]["landmark_note"] == cfg.STATUS_TEXT[cfg.STATUS_MISSING]


def test_sample_covers_every_status_deterministically():
    lm = {f"r{i}": {"status": cfg.STATUS_REVIEWED} for i in range(5)}
    lm |= {f"p{i}": {"status": cfg.STATUS_PROPOSAL} for i in range(5)}
    lm |= {f"m{i}": {"status": cfg.STATUS_MISSING} for i in range(5)}
    sample = cfg.sample_image_ids(lm)
    assert sample == cfg.sample_image_ids(lm)
    assert {lm[i]["status"] for i in sample} == {cfg.STATUS_REVIEWED, cfg.STATUS_PROPOSAL, cfg.STATUS_MISSING}


def test_label_rows_keep_each_annotation_and_map_eval_class():
    tasks = [{"data": {"image_id": "a", "landmark_status": "proposal", "landmark_source": "x"},
              "annotations": [
                  {"id": 1, "completed_by": 7, "updated_at": "t1", "result": [
                      {"from_name": "expression", "value": {"choices": ["Happy"]}},
                      {"from_name": "overlay_quality", "value": {"choices": ["Unreliable"]}}]},
                  {"id": 2, "completed_by": 8, "updated_at": "t2", "result": [
                      {"from_name": "expression", "value": {"choices": ["Ambiguous"]}}]},
                  {"id": 3, "was_cancelled": True, "result": []}]}]
    rows = cfg.label_rows_from_tasks(tasks, {7: "a@x", 8: "b@x"})
    assert [(r["label"], r["eval_class"], r["annotator"]) for r in rows] == [("Happy", "Happy", "a@x"), ("Ambiguous", "", "b@x")]
    assert rows[0]["overlay_quality"] == "Unreliable" and rows[0]["label_round"] == cfg.LABEL_ROUND
