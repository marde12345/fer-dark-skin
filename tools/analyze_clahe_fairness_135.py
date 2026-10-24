"""EXP-011 — Original vs. CLAHE (HSEmotion) skin-brightness group analysis on the 135-crop subset.

Reuses EXP-010's grouping, metrics, and grouped bootstrap (tools/analyze_fairness_135.py).
No inference is run: CLAHE predictions are the saved EXP-006 outputs.

Reads (does not modify):
  - reports/arcface_evaluation/evaluation_predictions.csv (135-crop subset, gt labels, EXP-007 HSEmotion predictions)
  - data/1408-1010-intermediate/clahe_predictions.csv (EXP-006 original + CLAHE HSEmotion predictions, 227 crops)
  - data/1408-1010-intermediate/faces/ (original crops, for the brightness groups, as in EXP-010)

Writes only to reports/clahe_fairness_135/ (a new, dedicated directory).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import f1_score

import analyze_fairness_135 as exp010

CONDITIONS = {"Original": "hsemotion_original", "CLAHE": "hsemotion_clahe"}
# EXP-006 stores HSEmotion labels already renamed; EXP-007 stores the model's raw names.
HSEMOTION_LABEL_MAP = {"Anger": "Angry", "Happiness": "Happy", "Sadness": "Sad"}
GROUP_COL = "skin_tone_all"


def load(predictions_csv: Path, clahe_csv: Path, faces_dir: Path) -> tuple[pd.DataFrame, dict]:
    df = exp010.load_predictions(predictions_csv, faces_dir)
    clahe = pd.read_csv(clahe_csv)
    df = df.merge(clahe, left_on="face_filename", right_on="filename", how="left",
                  validate="1:1", suffixes=("", "_exp006"))
    if df["filename"].isna().any():
        raise ValueError("crops missing from CLAHE predictions")
    df["hsemotion_original"] = df["original_label"].replace(HSEMOTION_LABEL_MAP)
    df["hsemotion_clahe"] = df["clahe_label"].replace(HSEMOTION_LABEL_MAP)
    checks = {
        "crops_matched": int(df["filename"].notna().sum()),
        "original_label_literal_match_exp007_raw": int((df["original_label"] == df["hsemotion_predicted_raw"]).sum()),
        "original_label_match_exp007_after_mapping": int((df["hsemotion_original"] == df["hsemotion_predicted_normalized"]).sum()),
        "exp006_skin_tone_match_recomputed": int((df["skin_tone_exp006"] == df[GROUP_COL]).sum()),
        "predictions_changed_by_clahe": int((df["hsemotion_original"] != df["hsemotion_clahe"]).sum()),
    }
    if checks["original_label_match_exp007_after_mapping"] != len(df):
        raise ValueError("EXP-006 original predictions do not match EXP-007 after label mapping")
    return df, checks


def condition_metrics(df: pd.DataFrame, cond: str) -> dict:
    out = {
        "accuracy": float(exp010.correct(df, cond).mean()),
        "accuracy_ci95": exp010.bootstrap_ci(df, lambda x: exp010.correct(x, cond).mean()),
        "macro_f1": float(f1_score(df["gt_label"], df[CONDITIONS[cond]], labels=exp010.CLASSES,
                                   average="macro", zero_division=0)),
        "gap_dark_minus_medium_dark": exp010.gap(df, GROUP_COL, cond),
        "gap_ci95": exp010.bootstrap_ci(df, lambda x: exp010.gap(x, GROUP_COL, cond)),
        "groups": {},
    }
    for g in exp010.GROUPS:
        d = df[df[GROUP_COL] == g]
        out["groups"][g] = {
            "n": len(d),
            "accuracy": exp010.group_acc(df, GROUP_COL, g, cond),
            "accuracy_ci95": exp010.bootstrap_ci(df, lambda x, g=g: exp010.group_acc(x, GROUP_COL, g, cond)),
            "angry_prediction_rate": float((d[CONDITIONS[cond]] == "Angry").mean()),
        }
    return out


def changes(df: pd.DataFrame) -> dict:
    acc_change = lambda x: exp010.correct(x, "CLAHE").mean() - exp010.correct(x, "Original").mean()
    gap_change = lambda x: exp010.gap(x, GROUP_COL, "CLAHE") - exp010.gap(x, GROUP_COL, "Original")
    out = {
        "accuracy_change": float(acc_change(df)),
        "accuracy_change_ci95": exp010.bootstrap_ci(df, acc_change),
        "gap_change": float(gap_change(df)),
        "gap_change_ci95": exp010.bootstrap_ci(df, gap_change),
        "group_accuracy_change": {},
        "mcnemar": {"all": paired_mcnemar(df)},
    }
    for g in exp010.GROUPS:
        ch = lambda x, g=g: exp010.group_acc(x, GROUP_COL, g, "CLAHE") - exp010.group_acc(x, GROUP_COL, g, "Original")
        out["group_accuracy_change"][g] = {"change": float(ch(df)), "ci95": exp010.bootstrap_ci(df, ch)}
        out["mcnemar"][g] = paired_mcnemar(df[df[GROUP_COL] == g])
    return out


def paired_mcnemar(df: pd.DataFrame) -> dict:
    o, c = exp010.correct(df, "Original"), exp010.correct(df, "CLAHE")
    b, cc = int((o & ~c).sum()), int((c & ~o).sum())
    p = binomtest(min(b, cc), b + cc, 0.5).pvalue if b + cc else float("nan")
    return {"original_only_correct": b, "clahe_only_correct": cc, "p_value": float(p)}


def validated_check(df: pd.DataFrame) -> dict:
    v = df.dropna(subset=["skin_tone"])
    gap_change = lambda x: exp010.gap(x, "skin_tone", "CLAHE") - exp010.gap(x, "skin_tone", "Original")
    return {"n": len(v), "gap_original": exp010.gap(v, "skin_tone", "Original"),
            "gap_clahe": exp010.gap(v, "skin_tone", "CLAHE"),
            "gap_change": float(gap_change(v)), "gap_change_ci95": exp010.bootstrap_ci(v, gap_change)}


def within_class(df: pd.DataFrame) -> list[dict]:
    rows = []
    for cls in ["Neutral", "Happy"]:
        for g in exp010.GROUPS:
            d = df[(df["gt_label"] == cls) & (df[GROUP_COL] == g)]
            rows.append({"class": cls, "group": g, "n": len(d),
                         "recall_original": float((d["hsemotion_original"] == cls).mean()),
                         "recall_clahe": float((d["hsemotion_clahe"] == cls).mean()),
                         "to_angry_original": int((d["hsemotion_original"] == "Angry").sum()),
                         "to_angry_clahe": int((d["hsemotion_clahe"] == "Angry").sum())})
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EXP-011 Original vs. CLAHE group analysis (135-crop subset).")
    parser.add_argument("--predictions", type=Path, default=Path("reports/arcface_evaluation/evaluation_predictions.csv"))
    parser.add_argument("--clahe-predictions", type=Path, default=Path("data/1408-1010-intermediate/clahe_predictions.csv"))
    parser.add_argument("--faces-dir", type=Path, default=Path("data/1408-1010-intermediate/faces"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/clahe_fairness_135"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    df, checks = load(args.predictions, args.clahe_predictions, args.faces_dir)
    exp010.MODELS = {**exp010.MODELS, **CONDITIONS}  # let EXP-010 helpers address the two conditions

    summary = {
        "n": len(df),
        "data_checks": checks,
        "conditions": {c: condition_metrics(df, c) for c in CONDITIONS},
        "clahe_minus_original": changes(df),
        "validated_grouping_n78": validated_check(df),
        "within_class": within_class(df),
        "bootstrap": {"seed": exp010.RANDOM_SEED, "n": exp010.N_BOOTSTRAP,
                      "unit": f"temporal block (frame_index // {exp010.TEMPORAL_BLOCK_SIZE})"},
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "clahe_fairness_summary.json").write_text(json.dumps(summary, indent=2))
    df[["face_filename", "gt_label", GROUP_COL, "block", "hsemotion_original", "hsemotion_clahe"]].to_csv(
        args.out_dir / "per_crop_predictions.csv", index=False)
    pd.DataFrame(summary["within_class"]).to_csv(args.out_dir / "within_class_recall.csv", index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
