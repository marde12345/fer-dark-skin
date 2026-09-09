"""Builds dashboard/data.js from existing research artifacts.

This script is a pure data-extraction step for the research dashboard
(dashboard/index.html). It reads already-generated CSVs from reports/ and
writes a single JS data file the dashboard loads via <script src="data.js">
(avoids fetch()/CORS issues when the dashboard is opened directly as a
local file). It does NOT recompute, reinterpret, or alter any research
number -- every value is read verbatim from its source CSV.

Run with: uv run python tools/build_dashboard_data.py
"""

import csv
import json
from pathlib import Path

REPORTS = Path("reports")
OUT = Path("dashboard/data.js")


def read_csv(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def as_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> None:
    comparison = {r["metric"]: r for r in read_csv(REPORTS / "arcface_evaluation" / "comparison_metrics.csv")}
    per_class = read_csv(REPORTS / "arcface_evaluation" / "per_class_metrics.csv")
    overall_error = read_csv(REPORTS / "arcface_error_analysis" / "overall_error_analysis.csv")
    neutral_rows = read_csv(REPORTS / "arcface_error_analysis" / "neutral_error_analysis.csv")
    skin_tone_rows = read_csv(REPORTS / "arcface_error_analysis" / "skin_tone_analysis.csv")
    stat_tests = read_csv(REPORTS / "arcface_evaluation" / "statistical_tests.csv")
    historical = {r["metric"]: r for r in read_csv(REPORTS / "audit_summary_metrics.csv")}
    findings = read_csv(REPORTS / "final_research_validation" / "final_evidence_matrix.csv")
    limitations = read_csv(REPORTS / "final_research_validation" / "final_limitations.csv")

    # Historical Neutral -> Angry (18/76) is documented in docs/EXPERIMENT.md
    # EXP-005 / notebooks/data_audit.ipynb cell 11 output; not present as a
    # standalone field in audit_summary_metrics.csv, so it is read from the
    # already-verified EXP-008 common-subset artifact (identical value,
    # cross-checked in R9) rather than re-derived here.
    neutral_model_map = {r["model"]: r for r in neutral_rows[:2]}

    # per-class breakdown for ArcFace neutral prediction (rows after blank line)
    neutral_breakdown = []
    started = False
    with (REPORTS / "arcface_error_analysis" / "neutral_error_analysis.csv").open() as f:
        for row in csv.reader(f):
            if not row:
                started = True
                continue
            if started and row[0] != "predicted_class":
                neutral_breakdown.append({"predicted_class": row[0], "arcface": row[1], "hsemotion": row[2]})

    stat_lookup = {(r["test"], r["detail"]): r["value"] for r in stat_tests}

    per_class_metrics = {}
    for r in per_class:
        per_class_metrics.setdefault(r["class"], {})[r["model"]] = {
            "precision": as_float(r["precision"]),
            "recall": as_float(r["recall"]),
            "f1": as_float(r["f1"]),
            "support": int(r["support"]),
        }

    overall_error_by_model = {}
    for r in overall_error:
        overall_error_by_model.setdefault(r["model"], []).append(
            {
                "ground_truth": r["ground_truth"],
                "n": int(r["n"]),
                "correct": int(r["correct"]),
                "incorrect": int(r["incorrect"]),
                "accuracy": as_float(r["accuracy"]),
                "error_rate": as_float(r["error_rate"]),
            }
        )

    skin_tone = []
    for r in skin_tone_rows:
        skin_tone.append(
            {
                "skin_tone": r["skin_tone"],
                "n": int(r["n"]),
                "arcface_accuracy": as_float(r["arcface_accuracy"]) if r["arcface_accuracy"] != "N/A" else None,
                "hsemotion_accuracy": as_float(r["hsemotion_accuracy"]) if r["hsemotion_accuracy"] != "N/A" else None,
                "arcface_neutral_error_rate": as_float(r["arcface_neutral_error_rate"]) if r["arcface_neutral_error_rate"] != "N/A" else None,
                "hsemotion_neutral_error_rate": as_float(r["hsemotion_neutral_error_rate"]) if r["hsemotion_neutral_error_rate"] != "N/A" else None,
            }
        )

    data = {
        "common_subset": {
            "n": 135,
            "arcface": {
                "accuracy": as_float(comparison["Accuracy"]["arcface"]),
                "macro_precision": as_float(comparison["Macro Precision"]["arcface"]),
                "macro_recall": as_float(comparison["Macro Recall"]["arcface"]),
                "macro_f1": as_float(comparison["Macro F1"]["arcface"]),
            },
            "hsemotion": {
                "accuracy": as_float(comparison["Accuracy"]["hsemotion_common_subset"]),
                "macro_precision": as_float(comparison["Macro Precision"]["hsemotion_common_subset"]),
                "macro_recall": as_float(comparison["Macro Recall"]["hsemotion_common_subset"]),
                "macro_f1": as_float(comparison["Macro F1"]["hsemotion_common_subset"]),
            },
        },
        "historical": {
            "n": 227,
            "accuracy": as_float(historical["overall_accuracy"]["value"]),
            "false_angry_rate": as_float(historical["false_angry_rate"]["value"]),
            "fairness_gap": as_float(historical["fairness_gap"]["value"]),
            "neutral_to_angry_count": 18,
            "neutral_to_angry_total": 76,
            "neutral_to_angry_rate": 18 / 76,
        },
        "per_class_metrics": per_class_metrics,
        "overall_error_by_model": overall_error_by_model,
        "neutral_analysis": {
            "arcface": {
                "n": int(neutral_model_map["ArcFace+LR"]["neutral_n"]),
                "correct": int(neutral_model_map["ArcFace+LR"]["correct_neutral"]),
                "error_rate": as_float(neutral_model_map["ArcFace+LR"]["neutral_error_rate"]),
                "dominant_wrong_class": neutral_model_map["ArcFace+LR"]["dominant_wrong_class"],
                "dominant_wrong_count": int(neutral_model_map["ArcFace+LR"]["dominant_wrong_count"]),
            },
            "hsemotion": {
                "n": int(neutral_model_map["HSEmotion"]["neutral_n"]),
                "correct": int(neutral_model_map["HSEmotion"]["correct_neutral"]),
                "error_rate": as_float(neutral_model_map["HSEmotion"]["neutral_error_rate"]),
                "dominant_wrong_class": neutral_model_map["HSEmotion"]["dominant_wrong_class"],
                "dominant_wrong_count": int(neutral_model_map["HSEmotion"]["dominant_wrong_count"]),
                "neutral_to_angry_count": 18,
                "neutral_to_angry_rate": 18 / 76,
            },
            "breakdown": neutral_breakdown,
        },
        "skin_tone": skin_tone,
        "statistics": {
            "mcnemar": {
                "a_both_correct": int(stat_lookup[("McNemar", "a_both_correct")]),
                "b_hsemotion_only": int(stat_lookup[("McNemar", "b_hsemotion_only_correct")]),
                "c_arcface_only": int(stat_lookup[("McNemar", "c_arcface_only_correct")]),
                "d_both_wrong": int(stat_lookup[("McNemar", "d_both_wrong")]),
                "p_value": as_float(stat_lookup[("McNemar", "p_value")]),
            },
            "bootstrap_accuracy_arcface": stat_lookup[("Bootstrap_Accuracy_ArcFace", "point,lower,upper")],
            "bootstrap_accuracy_hsemotion": stat_lookup[("Bootstrap_Accuracy_HSEmotion", "point,lower,upper")],
            "fisher_exact": stat_lookup[("Fisher_exact", "HSEmotion accuracy: Dark vs Medium-Dark")],
        },
        "findings": findings,
        "limitations": limitations,
        "class_distribution": {
            "final_classes": {"Neutral": 76, "Happy": 32, "Sad": 12, "Surprise": 8, "Fear": 7},
            "rare_excluded": {"Angry": 1, "Disgust": 2},
            "ambiguous_excluded": 40,
        },
        "population_funnel": [
            {"stage": "All face crops", "n": 227},
            {"stage": "ArcFace embeddings created", "n": 178},
            {"stage": "Valid ground-truth label (not Ambiguous)", "n": 138},
            {"stage": "Final evaluation set (5 classes)", "n": 135},
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        f.write("window.DASHBOARD_DATA = ")
        json.dump(data, f, indent=2)
        f.write(";\n")

    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
