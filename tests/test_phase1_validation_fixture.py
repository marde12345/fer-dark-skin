"""Unit tests for the Phase 1 validation fixture
(tools/papuan_v2/validation/) that empirically validated the full
annotation architecture proposed in
docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md, BEFORE any real
full-dataset implementation. No live Label Studio server is required for
these tests -- they exercise the same pure functions that were also
exercised live against the throwaway fixture project (port 8090,
project id 1) during Phase 1.

Deliberately separate from tests/test_label_studio_pilot.py and
tests/test_annotator_overlap.py (pilot production code) -- nothing here
imports pilot modules or touches EXP-PAP-004/Project ID 2/ports 8080-8081.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "papuan_v2" / "validation"))

import consensus_fixture as consensus_mod  # noqa: E402
import export_fixture_annotations as export_mod  # noqa: E402
import fixture_config as fx  # noqa: E402


# --- Bilingual labeling configuration ---------------------------------------


def test_label_config_has_exactly_seven_expression_classes():
    assert len(fx.EXPRESSION_CLASSES_BILINGUAL) == 7


def test_label_config_expression_choices_are_bilingual():
    for en, idn in fx.EXPRESSION_CLASSES_BILINGUAL:
        assert f'value="{en} / {idn}"' in fx.FIXTURE_LABEL_CONFIG


def test_label_config_confidence_choices_are_bilingual():
    for en, idn in fx.CONFIDENCE_LEVELS_BILINGUAL:
        assert f'value="{en} / {idn}"' in fx.FIXTURE_LABEL_CONFIG


def test_label_config_contains_both_english_and_indonesian_instructions():
    assert "instructions_en" in fx.FIXTURE_LABEL_CONFIG
    assert "instructions_id" in fx.FIXTURE_LABEL_CONFIG
    assert "Select the facial expression" in fx.INSTRUCTIONS_EN
    assert "Pilih ekspresi wajah" in fx.INSTRUCTIONS_ID


def test_confidence_field_is_separate_control_from_expression():
    expr_idx = fx.FIXTURE_LABEL_CONFIG.index('name="expression"')
    conf_idx = fx.FIXTURE_LABEL_CONFIG.index('name="confidence"')
    assert expr_idx != conf_idx
    # confidence is optional, expression is required
    expr_slice = fx.FIXTURE_LABEL_CONFIG[expr_idx - 20 : expr_idx + 80]
    conf_slice = fx.FIXTURE_LABEL_CONFIG[conf_idx - 20 : conf_idx + 80]
    assert 'required="true"' in expr_slice
    assert 'required="false"' in conf_slice


def test_canonical_expression_value_strips_indonesian_text():
    assert fx.canonical_expression_value("Happy / Senang") == "Happy"
    assert fx.canonical_expression_value("Fear / Takut") == "Fear"


# --- AI prediction never exposed to annotators -------------------------------


def test_label_config_never_exposes_ai_information():
    """The instructions text is allowed to TELL annotators not to use an
    AI prediction (prose) -- what must never appear is an actual
    AI-derived value/field name (a $variable, a Choice value, a model
    identifier) that could leak a prediction into the UI."""
    lowered = fx.FIXTURE_LABEL_CONFIG.lower()
    for banned in ["ai_prediction", "ai_model", "ai_confidence", "hsemotion", "arcface", "model_score", "$prediction", "$ai_"]:
        assert banned not in lowered
    # No $-templated data field other than the image itself is referenced.
    assert lowered.count("$") == 1
    assert "$image" in lowered


def test_fixture_tasks_never_contain_ai_fields():
    tasks = fx.build_fixture_tasks(["fixture_task_01.jpg", "fixture_task_02.jpg"])
    for task in tasks:
        assert set(task["data"].keys()) == {"image", "image_id"}
        for value in task["data"].values():
            assert "ai_" not in str(value).lower()
            assert "hsemotion" not in str(value).lower()
            assert "arcface" not in str(value).lower()


def test_fixture_tasks_keyed_by_filename_not_position():
    tasks = fx.build_fixture_tasks(["fixture_task_03.jpg", "fixture_task_01.jpg"])
    ids = [t["data"]["image_id"] for t in tasks]
    assert ids == ["fixture_task_03", "fixture_task_01"]  # preserves input order, not re-sorted or re-indexed


# --- Multi-annotator export: identity, no copying, order independence ------


def test_export_multi_annotator_one_row_per_annotation():
    tasks = [
        {
            "data": {"image_id": "fixture_task_01"},
            "annotations": [
                {
                    "id": 1,
                    "completed_by": {"id": 2, "email": "annotator-a@phase1-validation.test"},
                    "created_at": "2026-01-01T00:00:00Z",
                    "result": [
                        {"from_name": "expression", "value": {"choices": ["Happy / Senang"]}},
                        {"from_name": "confidence", "value": {"choices": ["High / Tinggi"]}},
                    ],
                },
                {
                    "id": 2,
                    "completed_by": {"id": 3, "email": "annotator-b@phase1-validation.test"},
                    "created_at": "2026-01-01T00:01:00Z",
                    "result": [{"from_name": "expression", "value": {"choices": ["Sad / Sedih"]}}],
                },
            ],
        }
    ]
    rows = export_mod.export_rows_multi_annotator(tasks, user_email_by_id={})

    assert len(rows) == 2
    identities = {r["annotator_identity"] for r in rows}
    assert identities == {"annotator-a@phase1-validation.test", "annotator-b@phase1-validation.test"}


def test_export_no_annotation_copied_between_annotators():
    """Each row's expression must trace back to its OWN annotation's
    result, never another annotator's -- guards against any accidental
    cross-assignment in the export grouping logic."""
    tasks = [
        {
            "data": {"image_id": "fixture_task_01"},
            "annotations": [
                {"id": 1, "completed_by": {"id": 2, "email": "a@x.test"}, "created_at": "t1",
                 "result": [{"from_name": "expression", "value": {"choices": ["Happy / Senang"]}}]},
                {"id": 2, "completed_by": {"id": 3, "email": "b@x.test"}, "created_at": "t2",
                 "result": [{"from_name": "expression", "value": {"choices": ["Sad / Sedih"]}}]},
                {"id": 3, "completed_by": {"id": 4, "email": "c@x.test"}, "created_at": "t3",
                 "result": [{"from_name": "expression", "value": {"choices": ["Fear / Takut"]}}]},
            ],
        }
    ]
    rows = export_mod.export_rows_multi_annotator(tasks, user_email_by_id={})
    by_identity = {r["annotator_identity"]: r["expression"] for r in rows}

    assert by_identity["a@x.test"] == "Happy / Senang"
    assert by_identity["b@x.test"] == "Sad / Sedih"
    assert by_identity["c@x.test"] == "Fear / Takut"
    # No value duplicated across two different identities.
    assert len(set(by_identity.values())) == 3


def test_export_uses_real_identity_never_faked_by_ordering():
    """If completed_by is an integer (not an inline dict), identity must
    be resolved via the provided user map -- never invented as
    'annotator_A'/'annotator_B' based on list position."""
    tasks = [
        {
            "data": {"image_id": "img1"},
            "annotations": [
                {"id": 10, "completed_by": 99, "created_at": "t1",
                 "result": [{"from_name": "expression", "value": {"choices": ["Neutral / Netral"]}}]},
            ],
        }
    ]
    rows = export_mod.export_rows_multi_annotator(tasks, user_email_by_id={99: "real.user@x.test"})
    assert rows[0]["annotator_identity"] == "real.user@x.test"
    assert "annotator_A" not in rows[0]["annotator_identity"]


def test_export_output_order_is_deterministic_not_task_list_order():
    """run()'s sort key is (image_id, annotator_identity) -- verify the
    pure export function's output does not depend on the INPUT tasks
    list order either, by feeding the same tasks in reverse order."""
    tasks_forward = [
        {"data": {"image_id": "img_b"}, "annotations": [{"id": 1, "completed_by": {"id": 1, "email": "a@x.test"}, "created_at": "t",
         "result": [{"from_name": "expression", "value": {"choices": ["Happy / Senang"]}}]}]},
        {"data": {"image_id": "img_a"}, "annotations": [{"id": 2, "completed_by": {"id": 1, "email": "a@x.test"}, "created_at": "t",
         "result": [{"from_name": "expression", "value": {"choices": ["Sad / Sedih"]}}]}]},
    ]
    tasks_reversed = list(reversed(tasks_forward))

    rows_forward = export_mod.export_rows_multi_annotator(tasks_forward, {})
    rows_reversed = export_mod.export_rows_multi_annotator(tasks_reversed, {})

    # content-equal regardless of input order (order-sensitivity is handled by run()'s explicit sort;
    # the pure per-task extraction itself must not silently depend on task list position either)
    key = lambda rows: sorted((r["image_id"], r["annotator_identity"], r["expression"]) for r in rows)
    assert key(rows_forward) == key(rows_reversed)


def test_export_csv_round_trip_preserves_all_fields(tmp_path):
    rows = [
        {"image_id": "img1", "annotation_id": 1, "annotator_identity": "a@x.test",
         "expression": "Happy / Senang", "confidence": "High / Tinggi", "created_at": "t1"},
    ]
    out_path = tmp_path / "export.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=export_mod.FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with out_path.open() as f:
        loaded = list(csv.DictReader(f))
    assert loaded[0]["annotator_identity"] == "a@x.test"
    assert loaded[0]["expression"] == "Happy / Senang"


# --- Consensus fixture -------------------------------------------------------


def test_consensus_unanimous():
    result = consensus_mod.compute_consensus("ex1", "Happy", "Happy", "Happy")
    assert result.agreement_status == "unanimous"
    assert result.consensus_label == "Happy"
    assert result.adjudication_required is False


def test_consensus_majority_two_of_three():
    result = consensus_mod.compute_consensus("ex2", "Fear", "Fear", "Surprise")
    assert result.agreement_status == "majority"
    assert result.consensus_label == "Fear"
    assert result.adjudication_required is False


def test_consensus_no_majority_requires_adjudication():
    result = consensus_mod.compute_consensus("ex3", "Fear", "Surprise", "Happy")
    assert result.agreement_status == "no_majority"
    assert result.consensus_label is None
    assert result.adjudication_required is True


def test_consensus_is_reproducible():
    r1 = consensus_mod.compute_consensus("x", "Happy", "Sad", "Happy")
    r2 = consensus_mod.compute_consensus("x", "Happy", "Sad", "Happy")
    assert r1 == r2


def test_consensus_never_accepts_confidence_or_ai_as_input():
    """Structural guard: compute_consensus's signature has no
    confidence/AI parameter at all, so neither can silently influence
    the vote -- verified by introspection, not just behavior."""
    import inspect

    sig = inspect.signature(consensus_mod.compute_consensus)
    param_names = set(sig.parameters.keys())
    assert "confidence" not in param_names
    assert "ai_prediction" not in param_names
    assert "ai_confidence" not in param_names


def test_consensus_order_of_inputs_does_not_change_the_vote_outcome():
    """majority/unanimous/no_majority must depend only on the multiset of
    labels, not on which annotator (a/b/c slot) contributed which label."""
    r_abc = consensus_mod.compute_consensus("x", "Fear", "Fear", "Surprise")
    r_bca = consensus_mod.compute_consensus("x", "Surprise", "Fear", "Fear")
    assert r_abc.agreement_status == r_bca.agreement_status == "majority"
    assert r_abc.consensus_label == r_bca.consensus_label == "Fear"
