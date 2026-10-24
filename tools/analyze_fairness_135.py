"""EXP-010 — Skin-brightness group fairness analysis on the 135-crop common subset.

Reuses existing EXP-007 predictions; no model is trained or re-run.

Reads (does not modify):
  - reports/arcface_evaluation/evaluation_predictions.csv (EXP-007 predictions, gt labels, validated skin_tone)
  - data/1408-1010-intermediate/faces/ (original crops, only to fill the 57 missing skin-tone buckets
    with the same LandmarkAnalyzer._compute_skin_tone function used for the validated 78)

Writes only to reports/fairness_135/ (a new, dedicated directory).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score

from fer_dataset.pipeline.landmark_analyzer import LandmarkAnalyzer

CLASSES = ["Fear", "Happy", "Neutral", "Sad", "Surprise"]
GROUPS = ["Dark", "Medium-Dark"]
MODELS = {"HSEmotion": "hsemotion_predicted_normalized", "ArcFace+LR": "arcface_predicted"}
RANDOM_SEED = 42  # same as tools/evaluate_arcface_vs_hsemotion.py
N_BOOTSTRAP = 2000
TEMPORAL_BLOCK_SIZE = 3  # frame_index // 3, same blocks as EXP-007's bootstrap


def load_predictions(predictions_csv: Path, faces_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(predictions_csv)
    df["block"] = df["face_filename"].str.extract(r"frame_(\d+)")[0].astype(int) // TEMPORAL_BLOCK_SIZE
    buckets = []
    for fn in df["face_filename"]:
        img = cv2.imread(str(faces_dir / fn))
        if img is None:
            raise FileNotFoundError(faces_dir / fn)
        buckets.append(LandmarkAnalyzer._compute_skin_tone(img)[0])
    df["skin_tone_all"] = buckets
    return df


def correct(df: pd.DataFrame, model: str) -> pd.Series:
    return df[MODELS[model]] == df["gt_label"]


def group_acc(df: pd.DataFrame, col: str, group: str, model: str) -> float:
    return float(correct(df[df[col] == group], model).mean())


def gap(df: pd.DataFrame, col: str, model: str) -> float:
    return group_acc(df, col, "Dark", model) - group_acc(df, col, "Medium-Dark", model)


def bootstrap_ci(df: pd.DataFrame, stat, seed: int = RANDOM_SEED, n_bootstrap: int = N_BOOTSTRAP) -> tuple[float, float]:
    """Resample temporal blocks with replacement (crops within a block are not independent)."""
    rng = np.random.default_rng(seed)
    blocks = df.groupby("block").indices
    block_ids = list(blocks)
    values = []
    for _ in range(n_bootstrap):
        idx = np.concatenate([blocks[b] for b in rng.choice(block_ids, size=len(block_ids), replace=True)])
        values.append(stat(df.iloc[idx]))
    lower, upper = np.nanpercentile(values, [2.5, 97.5])
    return float(lower), float(upper)


def mcnemar(df: pd.DataFrame) -> dict:
    h, a = correct(df, "HSEmotion"), correct(df, "ArcFace+LR")
    b, c = int((h & ~a).sum()), int((a & ~h).sum())
    p = binomtest(min(b, c), b + c, 0.5).pvalue if b + c else float("nan")
    return {"b_hsemotion_only": b, "c_arcface_only": c, "p_value": float(p)}


def analyze(df: pd.DataFrame, col: str) -> dict:
    sub = df[df[col].isin(GROUPS)]
    result = {"groups": {}, "models": {}}
    for g in GROUPS:
        d = sub[sub[col] == g]
        present = sorted(d["gt_label"].unique())
        result["groups"][g] = {
            "n": len(d),
            "class_counts": d["gt_label"].value_counts().to_dict(),
            "mcnemar": mcnemar(d),
            **{m: {"accuracy": float(correct(d, m).mean()),
                   "macro_f1_present_classes": float(f1_score(d["gt_label"], d[c], labels=present, average="macro", zero_division=0))}
               for m, c in MODELS.items()},
        }
    for m in MODELS:
        worst = lambda x, m=m: min(group_acc(x, col, g, m) for g in GROUPS)
        result["models"][m] = {
            "gap_dark_minus_medium_dark": gap(sub, col, m),
            "gap_ci95": bootstrap_ci(sub, lambda x, m=m: gap(x, col, m)),
            "worst_group_accuracy": worst(sub),
            "worst_group_ci95": bootstrap_ci(sub, worst),
        }
    gap_diff = lambda x: gap(x, col, "HSEmotion") - gap(x, col, "ArcFace+LR")
    result["gap_difference_hsemotion_minus_arcface"] = gap_diff(sub)
    result["gap_difference_ci95"] = bootstrap_ci(sub, gap_diff)
    return result


def within_class(df: pd.DataFrame, col: str) -> list[dict]:
    rows = []
    for cls in ["Neutral", "Happy"]:
        for g in GROUPS:
            d = df[(df["gt_label"] == cls) & (df[col] == g)]
            rows.append({
                "class": cls, "group": g, "n": len(d),
                "hsemotion_recall": float((d[MODELS["HSEmotion"]] == cls).mean()),
                "arcface_recall": float((d[MODELS["ArcFace+LR"]] == cls).mean()),
                "hsemotion_to_angry": int((d[MODELS["HSEmotion"]] == "Angry").sum()),
            })
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EXP-010 skin-brightness group fairness analysis (135-crop subset).")
    parser.add_argument("--predictions", type=Path, default=Path("reports/arcface_evaluation/evaluation_predictions.csv"))
    parser.add_argument("--faces-dir", type=Path, default=Path("data/1408-1010-intermediate/faces"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/fairness_135"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    df = load_predictions(args.predictions, args.faces_dir)

    validated = df.dropna(subset=["skin_tone"])
    summary = {
        "n": len(df),
        "overall": {m: {"accuracy": float(accuracy_score(df["gt_label"], df[c])),
                        "macro_f1": float(f1_score(df["gt_label"], df[c], labels=CLASSES, average="macro", zero_division=0))}
                    for m, c in MODELS.items()},
        "regroup_agreement_with_validated": f"{int((validated['skin_tone'] == validated['skin_tone_all']).sum())}/{len(validated)}",
        "skin_tone_all_counts": df["skin_tone_all"].value_counts().to_dict(),
        "full_regroup_n135": analyze(df, "skin_tone_all"),
        "validated_grouping_n78": analyze(df, "skin_tone"),
        "within_class_full_regroup": within_class(df, "skin_tone_all"),
        "bootstrap": {"seed": RANDOM_SEED, "n": N_BOOTSTRAP, "unit": f"temporal block (frame_index // {TEMPORAL_BLOCK_SIZE})"},
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "fairness_summary.json").write_text(json.dumps(summary, indent=2))
    df[["face_filename", "gt_label", "skin_tone", "skin_tone_all", "block"]].to_csv(args.out_dir / "skin_tone_groups.csv", index=False)
    with open(args.out_dir / "within_class_recall.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary["within_class_full_regroup"][0]))
        writer.writeheader()
        writer.writerows(summary["within_class_full_regroup"])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
