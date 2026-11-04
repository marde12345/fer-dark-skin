"""EXP-012: retrain ArcFace + Logistic Regression on the round-2 labels and
evaluate overall and Dark vs. Medium-Dark performance.

Reuses, unchanged:
  - tools/train_arcface_classifier.py: embedding loading, usable-sample rules
    (Ambiguous excluded, classes with < 5 samples excluded), 5-fold
    StratifiedGroupKFold over 3-frame temporal blocks, class-balanced L2
    logistic regression, seed 42, train/test group-overlap assertion.
  - tools/analyze_fairness_135.py: skin-brightness grouping on original crops,
    grouped bootstrap CIs (2,000 resamples, seed 42), McNemar.
No new embeddings are extracted. HSEmotion is not re-run: its saved
predictions are re-scored against the round-2 labels.

Reads (never modifies): experiments/EXP-012-relabel/labels_round2.csv,
data/intermediate/arcface_embeddings/embeddings.csv,
data/1408-1010-intermediate/{annotations.csv,manual_labels_export.csv,faces/},
reports/arcface_evaluation/evaluation_predictions.csv.
Writes only to experiments/EXP-012-relabel/results/.

Run:
    uv run python tools/exp012/train_eval_round2.py [--data-root /path/to/main/checkout]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
import analyze_fairness_135 as exp010  # noqa: E402
import train_arcface_classifier as arc  # noqa: E402

LABELS = REPO_ROOT / "experiments" / "EXP-012-relabel" / "labels_round2.csv"
OUT_DIR = REPO_ROOT / "experiments" / "EXP-012-relabel" / "results"
EXP007_PREDICTIONS = REPO_ROOT / "reports" / "arcface_evaluation" / "evaluation_predictions.csv"
EXP010_SUMMARY = REPO_ROOT / "reports" / "fairness_135" / "fairness_summary.json"
HSEMOTION_LABEL_MAP = {"Anger": "Angry", "Happiness": "Happy", "Sadness": "Sad"}  # as in EXP-007/010/011
# Prediction columns, keyed by the names used by the EXP-010 helpers.
MODELS = {
    "ArcFace+LR (round-2 retrained)": "arcface_r2",
    "HSEmotion (fixed)": "hsemotion",
    "ArcFace+LR (EXP-007, round-1 trained)": "arcface_r1",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_round2(data_root: Path) -> pd.DataFrame:
    """One annotation per crop (the latest), with inclusion decisions recorded."""
    labels = pd.read_csv(LABELS).sort_values("labeled_at").groupby("image_id").tail(1)
    if len(labels) != 227 or labels.image_id.duplicated().any():
        raise SystemExit(f"expected 227 unique crops, got {len(labels)}")
    return labels.reset_index(drop=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    d = args.data_root
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Freeze the round-2 dataset and apply the existing usable-sample rules.
    labels = freeze_round2(d)
    gt = {f"{i}.jpg": lab for i, lab in zip(labels.image_id, labels.label)}
    embeddings = arc.load_embeddings(d / "data/intermediate/arcface_embeddings/embeddings.csv")
    usable, exclusions = arc.build_usable_samples(embeddings, gt)
    used = {s.face_filename for s in usable}

    def reason(row) -> str:
        f = f"{row.image_id}.jpg"
        if row.label == "Ambiguous":
            return "ambiguous"
        if f not in embeddings:
            return "no_arcface_embedding"
        if f not in used:
            return "rare_class"
        return ""

    labels["exclusion_reason"] = labels.apply(reason, axis=1)
    labels["included"] = labels.exclusion_reason == ""
    labels[["image_id", "label", "confidence", "overlay_quality", "landmark_status", "annotation_id", "labeled_at",
            "included", "exclusion_reason"]].to_csv(OUT_DIR / "round2_dataset.csv", index=False)

    # 2. Retrain with the unchanged EXP-007 cross-validation.
    class_order = sorted({s.gt_label for s in usable})
    oof = pd.DataFrame(arc.run_cross_validation(usable, class_order))
    df = pd.DataFrame({"face_filename": [s.face_filename for s in usable], "gt_label": [s.gt_label for s in usable],
                       "frame_index": [s.frame_index for s in usable]})
    df["arcface_r2"] = df.face_filename.map(dict(zip(oof.face_filename, oof.predicted_label)))
    df["block"] = df.frame_index // exp010.TEMPORAL_BLOCK_SIZE
    df["skin_tone_all"] = [  # same function and original crops as EXP-010
        exp010.LandmarkAnalyzer._compute_skin_tone(cv2.imread(str(d / "data/1408-1010-intermediate/faces" / f)))[0]
        for f in df.face_filename]

    # Existing predictions, re-scored against round-2 labels (no re-running).
    hse = pd.read_csv(d / "data/1408-1010-intermediate/annotations.csv")
    df["hsemotion"] = df.face_filename.map(dict(zip(hse.filename, hse.label.replace(HSEMOTION_LABEL_MAP))))
    e7 = pd.read_csv(EXP007_PREDICTIONS)
    df["arcface_r1"] = df.face_filename.map(dict(zip(e7.face_filename, e7.arcface_predicted)))
    r1 = pd.read_csv(d / "data/1408-1010-intermediate/manual_labels_export.csv")
    df["round1_label"] = df.face_filename.map(dict(zip(r1.filename, r1.gt_label)))
    df.to_csv(OUT_DIR / "oof_predictions.csv", index=False)

    # 3. Metrics for the retrained model on all usable crops.
    exp010.MODELS = {**exp010.MODELS, **MODELS}  # let EXP-010 helpers address these prediction columns
    y, p = df.gt_label, df.arcface_r2
    prec, rec, f1, sup = precision_recall_fscore_support(y, p, labels=class_order, zero_division=0)
    per_class = pd.DataFrame({"class": class_order, "precision": prec, "recall": rec, "f1": f1, "support": sup})
    per_class.to_csv(OUT_DIR / "per_class_metrics.csv", index=False)
    cm = confusion_matrix(y, p, labels=class_order)
    pd.DataFrame(cm, index=class_order, columns=class_order).to_csv(OUT_DIR / "confusion_matrix.csv")
    plot_confusion_matrix(cm, class_order)

    def model_block(sub: pd.DataFrame, name: str) -> dict:
        col = MODELS[name]
        out = {"n": len(sub), "accuracy": float(accuracy_score(sub.gt_label, sub[col])),
               "accuracy_ci95": exp010.bootstrap_ci(sub, lambda x: exp010.correct(x, name).mean()),
               "macro_f1": float(f1_score(sub.gt_label, sub[col], labels=class_order, average="macro", zero_division=0)),
               "groups": {}}
        for g in exp010.GROUPS:
            gs = sub[sub.skin_tone_all == g]
            out["groups"][g] = {"n": len(gs), "class_counts": gs.gt_label.value_counts().to_dict(),
                                "accuracy": exp010.group_acc(sub, "skin_tone_all", g, name),
                                "accuracy_ci95": exp010.bootstrap_ci(sub, lambda x, g=g: exp010.group_acc(x, "skin_tone_all", g, name))}
        out["gap_dark_minus_medium_dark"] = exp010.gap(sub, "skin_tone_all", name)
        out["gap_ci95"] = exp010.bootstrap_ci(sub, lambda x: exp010.gap(x, "skin_tone_all", name))
        worst = lambda x: min(exp010.group_acc(x, "skin_tone_all", g, name) for g in exp010.GROUPS)
        out["worst_group_accuracy"] = worst(sub)
        out["worst_group_ci95"] = exp010.bootstrap_ci(sub, worst)
        return out

    def paired(sub: pd.DataFrame, a: str, b: str) -> dict:
        ca, cb = sub[MODELS[a]] == sub.gt_label, sub[MODELS[b]] == sub.gt_label
        n01, n10 = int((ca & ~cb).sum()), int((cb & ~ca).sum())
        from scipy.stats import binomtest
        pv = binomtest(min(n01, n10), n01 + n10, 0.5).pvalue if n01 + n10 else float("nan")
        diff = lambda x: (x[MODELS[a]] == x.gt_label).mean() - (x[MODELS[b]] == x.gt_label).mean()
        gapdiff = lambda x: exp010.gap(x, "skin_tone_all", a) - exp010.gap(x, "skin_tone_all", b)
        return {"n": len(sub), f"{a}_only_correct": n01, f"{b}_only_correct": n10, "mcnemar_p": float(pv),
                "accuracy_difference": float(diff(sub)), "accuracy_difference_ci95": exp010.bootstrap_ci(sub, diff),
                "gap_difference": float(gapdiff(sub)), "gap_difference_ci95": exp010.bootstrap_ci(sub, gapdiff)}

    common = df[df.arcface_r1.notna() & df.hsemotion.notna()]
    r1_ok = common[common.round1_label.isin(class_order)]
    summary = {
        "experiment_id": "EXP-012",
        "dataset": {"round2_crops": 227, "one_annotation_per_crop": "latest", "exclusions": dict(sorted(exclusions.items())),
                    "missing_embedding": int((labels.exclusion_reason == "no_arcface_embedding").sum()),
                    "usable": len(df), "class_counts": Counter(df.gt_label), "class_order": class_order,
                    "group_counts": Counter(df.skin_tone_all),
                    "class_by_group": pd.crosstab(df.gt_label, df.skin_tone_all).to_dict(),
                    "temporal_blocks": int(df.block.nunique())},
        "retrained_all_usable": model_block(df, "ArcFace+LR (round-2 retrained)"),
        "per_class": per_class.to_dict(orient="records"),
        "comparison_same_crops_round2_labels": {
            "n": len(common),
            "models": {name: model_block(common, name) for name in MODELS},
            "retrained_vs_hsemotion": paired(common, "ArcFace+LR (round-2 retrained)", "HSEmotion (fixed)"),
            "retrained_vs_round1_arcface": paired(common, "ArcFace+LR (round-2 retrained)", "ArcFace+LR (EXP-007, round-1 trained)"),
        },
        "label_effect_hsemotion_fixed_model": {
            "n_crops_labeled_in_class_order_both_rounds": len(r1_ok),
            "accuracy_vs_round1_labels": float((r1_ok.hsemotion == r1_ok.round1_label).mean()),
            "accuracy_vs_round2_labels": float((r1_ok.hsemotion == r1_ok.gt_label).mean()),
            "round1_round2_label_agreement": float((r1_ok.round1_label == r1_ok.gt_label).mean()),
        },
        "exp010_reference": {k: json.load(open(EXP010_SUMMARY))["overall"][k] for k in ("HSEmotion", "ArcFace+LR")},
        "bootstrap": {"seed": exp010.RANDOM_SEED, "n": exp010.N_BOOTSTRAP, "unit": "temporal block (frame_index // 3)"},
    }
    config = {
        "labels_file": str(LABELS.relative_to(REPO_ROOT)), "labels_sha256": sha256(LABELS),
        "embeddings_sha256": sha256(d / "data/intermediate/arcface_embeddings/embeddings.csv"),
        "classifier": arc.CLASSIFIER_CONFIG, "min_class_count": arc.MIN_CLASS_COUNT, "n_splits": arc.N_SPLITS,
        "temporal_block_size": arc.TEMPORAL_BLOCK_SIZE, "cv": "StratifiedGroupKFold(shuffle=True, random_state=42)",
        "bootstrap": summary["bootstrap"], "hsemotion_label_map": HSEMOTION_LABEL_MAP,
    }
    (OUT_DIR / "config.json").write_text(json.dumps(config, indent=2, default=str))
    (OUT_DIR / "metrics.json").write_text(json.dumps(summary, indent=2, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)))
    print(json.dumps(summary, indent=2, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)))


def plot_confusion_matrix(cm, labels: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Round-2 label")
    ax.set_title("EXP-012 ArcFace+LR (round-2), out-of-fold")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
