"""R7 — Formal ArcFace vs. HSEmotion evaluation on a common subset.

Reads (does not modify):
  - data/intermediate/arcface_embeddings/classifier_predictions.csv (R6 OOF predictions, unchanged)
  - data/intermediate/annotations.csv (HSEmotion's original predictions, unchanged)
  - data/1408-1010-intermediate/manual_labels_export.csv (ground truth, unchanged)
  - data/intermediate/arcface_embeddings/embeddings.csv (for skin-tone-eligible identity only)
  - data/1408-1010-intermediate/landmark_features.csv (skin_tone column, unchanged)

Writes only to reports/arcface_evaluation/ (a new, dedicated directory) —
no historical report or dataset artifact is overwritten.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest, fisher_exact
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def save_confusion_matrix_png(cm: np.ndarray, labels: list[str], title: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(max(6, len(labels)), max(5, len(labels) - 1)))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground Truth")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(int(cm[i, j])), ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

OUT_DIR = Path("reports/arcface_evaluation")
RANDOM_SEED = 42
N_BOOTSTRAP = 2000

# HSEmotion's raw label vocabulary -> manual gt_label's short-form vocabulary,
# identical to the mapping already used in notebooks/data_audit.ipynb cell 3.
HSEMOTION_LABEL_MAP = {"Anger": "Angry", "Happiness": "Happy", "Sadness": "Sad"}


def normalize_hsemotion_label(label: str) -> str:
    return HSEMOTION_LABEL_MAP.get(label, label)


def load_arcface_predictions(path: Path) -> dict[str, dict]:
    result = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            result[row["face_filename"]] = {
                "gt_label": row["gt_label"],
                "predicted_label": row["predicted_label"],
                "fold": int(row["fold"]),
                "probabilities": json.loads(row["prediction_probabilities"]),
            }
    return result


def load_hsemotion_predictions(path: Path) -> dict[str, dict]:
    result = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            result[row["filename"]] = {
                "predicted_label": normalize_hsemotion_label(row["label"]),
                "predicted_label_raw": row["label"],
                "confidence": float(row["confidence"]),
            }
    return result


def load_skin_tone(path: Path) -> dict[str, str]:
    result = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            result[row["face_filename"]] = row["skin_tone"]
    return result


def build_common_population(arcface: dict, hsemotion: dict) -> list[str]:
    """Intersection by face_filename identity, never row position.
    ArcFace's OOF set already enforces valid-GT + eligible-class + embedded;
    HSEmotion predictions exist for every crop, so the intersection equals
    ArcFace's OOF set restricted to filenames that also have an HSEmotion
    prediction (expected to be all of them, verified explicitly below)."""
    common = [fn for fn in arcface if fn in hsemotion]
    return sorted(common)


def compute_metrics(y_true: list[str], y_pred: list[str], class_order: list[str]) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=class_order, zero_division=0
    )
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=class_order, average="macro", zero_division=0
    )
    accuracy = float(np.mean([yt == yp for yt, yp in zip(y_true, y_pred)]))
    return {
        "n": len(y_true),
        "accuracy": accuracy,
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "per_class": {
            class_order[i]: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i in range(len(class_order))
        },
    }


def false_angry_analysis(y_true: list[str], y_pred: list[str]) -> dict:
    """False-Angry: predicted == 'Angry' AND true != 'Angry'.
    Denominator convention matches notebooks/data_audit.ipynb cell 11:
    rate = false_angry_count / total_n (of the evaluated population), NOT
    of the Neutral-only subset."""
    total_n = len(y_true)
    false_angry_pairs = [(t, p) for t, p in zip(y_true, y_pred) if p == "Angry" and t != "Angry"]
    false_angry_n = len(false_angry_pairs)
    rate = false_angry_n / total_n if total_n else float("nan")
    breakdown = Counter(t for t, p in false_angry_pairs)

    neutral_total = sum(1 for t in y_true if t == "Neutral")
    neutral_to_angry = sum(1 for t, p in false_angry_pairs if t == "Neutral")
    neutral_to_angry_rate = neutral_to_angry / neutral_total if neutral_total else float("nan")

    return {
        "total_n": total_n,
        "false_angry_count": false_angry_n,
        "false_angry_rate_of_total": rate,
        "breakdown_by_true_class": dict(breakdown),
        "neutral_total": neutral_total,
        "neutral_to_angry_count": neutral_to_angry,
        "neutral_to_angry_rate_of_neutral": neutral_to_angry_rate,
    }


def mcnemar_test(hsemotion_correct: list[bool], arcface_correct: list[bool]) -> dict:
    a = sum(1 for h, ar in zip(hsemotion_correct, arcface_correct) if h and ar)
    b = sum(1 for h, ar in zip(hsemotion_correct, arcface_correct) if h and not ar)
    c = sum(1 for h, ar in zip(hsemotion_correct, arcface_correct) if not h and ar)
    d = sum(1 for h, ar in zip(hsemotion_correct, arcface_correct) if not h and not ar)

    n_discordant = b + c
    if n_discordant == 0:
        p_value = 1.0
    else:
        # Exact binomial McNemar test (appropriate for small discordant counts).
        result = binomtest(min(b, c), n_discordant, 0.5, alternative="two-sided")
        p_value = result.pvalue

    return {"a_both_correct": a, "b_hsemotion_only": b, "c_arcface_only": c, "d_both_wrong": d, "p_value": p_value}


def group_aware_bootstrap_ci(
    values_by_group: dict[int, list[bool]],
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = RANDOM_SEED,
) -> tuple[float, float, float]:
    """Group-aware bootstrap: resample GROUPS (temporal blocks) with
    replacement, not individual samples, since samples within a group are
    not independent (docs/ARCFACE_EXPERIMENT_DESIGN.md Section 8). Returns
    (point_estimate, ci_lower, ci_upper) for the mean of the boolean metric."""
    rng = np.random.default_rng(seed)
    group_ids = list(values_by_group.keys())
    all_values = [v for vals in values_by_group.values() for v in vals]
    point_estimate = float(np.mean(all_values))

    boot_means = []
    for _ in range(n_bootstrap):
        sampled_groups = rng.choice(group_ids, size=len(group_ids), replace=True)
        sampled_values = [v for g in sampled_groups for v in values_by_group[g]]
        if sampled_values:
            boot_means.append(np.mean(sampled_values))

    lower = float(np.percentile(boot_means, 2.5))
    upper = float(np.percentile(boot_means, 97.5))
    return point_estimate, lower, upper


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    arcface = load_arcface_predictions(Path("data/intermediate/arcface_embeddings/classifier_predictions.csv"))
    hsemotion = load_hsemotion_predictions(Path("data/intermediate/annotations.csv"))
    skin_tone = load_skin_tone(Path("data/1408-1010-intermediate/landmark_features.csv"))

    class_order = sorted(set(r["gt_label"] for r in arcface.values()))
    common = build_common_population(arcface, hsemotion)

    # --- Population accounting ---------------------------------------------
    all_crops_n = len(list(Path("data/intermediate/faces").glob("*.jpg")))
    with open("data/intermediate/arcface_embeddings/embeddings.csv") as f:
        embedded_n = sum(1 for r in csv.DictReader(f) if r["status"] == "embedded")
    with open("data/1408-1010-intermediate/manual_labels_export.csv") as f:
        manual_rows = list(csv.DictReader(f))
    valid_gt_n = sum(1 for r in manual_rows if r["gt_label"] not in ("Ambiguous", "", None))

    population_table = {
        "all_face_crops": all_crops_n,
        "arcface_embeddings": embedded_n,
        "valid_gt_labels_full_dataset": valid_gt_n,
        "arcface_classifier_population": len(arcface),
        "hsemotion_predictions_available": len(hsemotion),
        "common_evaluation_subset": len(common),
    }

    y_true = [arcface[fn]["gt_label"] for fn in common]
    y_pred_arcface = [arcface[fn]["predicted_label"] for fn in common]
    y_pred_hsemotion = [hsemotion[fn]["predicted_label"] for fn in common]

    class_counts_common = dict(Counter(y_true))

    # --- Metrics -------------------------------------------------------------
    arcface_metrics = compute_metrics(y_true, y_pred_arcface, class_order)
    hsemotion_metrics = compute_metrics(y_true, y_pred_hsemotion, class_order)

    cm_arcface = confusion_matrix(y_true, y_pred_arcface, labels=class_order)
    cm_hsemotion_labels = class_order + ["Other"]
    y_pred_hsemotion_bucketed = [p if p in class_order else "Other" for p in y_pred_hsemotion]
    cm_hsemotion = confusion_matrix(y_true, y_pred_hsemotion_bucketed, labels=cm_hsemotion_labels)

    # --- False-Angry analysis -------------------------------------------------
    fa_arcface = false_angry_analysis(y_true, y_pred_arcface)
    fa_hsemotion = false_angry_analysis(y_true, y_pred_hsemotion)

    # --- McNemar ---------------------------------------------------------------
    hsemotion_correct = [t == p for t, p in zip(y_true, y_pred_hsemotion)]
    arcface_correct = [t == p for t, p in zip(y_true, y_pred_arcface)]
    mcnemar_result = mcnemar_test(hsemotion_correct, arcface_correct)

    # --- Bootstrap (group-aware, using temporal blocks from R6 fold groups) ---
    def frame_group(filename: str) -> int:
        import re

        m = re.match(r"frame_(\d+)_face\d+\.jpg", filename)
        return int(m.group(1)) // 3

    groups_for_common = {fn: frame_group(fn) for fn in common}

    def grouped(bool_list: list[bool]) -> dict[int, list[bool]]:
        out: dict[int, list[bool]] = defaultdict(list)
        for fn, val in zip(common, bool_list):
            out[groups_for_common[fn]].append(val)
        return dict(out)

    boot_acc_arcface = group_aware_bootstrap_ci(grouped(arcface_correct))
    boot_acc_hsemotion = group_aware_bootstrap_ci(grouped(hsemotion_correct))

    fa_arcface_bool = [p == "Angry" and t != "Angry" for t, p in zip(y_true, y_pred_arcface)]
    fa_hsemotion_bool = [p == "Angry" and t != "Angry" for t, p in zip(y_true, y_pred_hsemotion)]
    boot_fa_arcface = group_aware_bootstrap_ci(grouped(fa_arcface_bool))
    boot_fa_hsemotion = group_aware_bootstrap_ci(grouped(fa_hsemotion_bool))

    # --- Skin-tone analysis -----------------------------------------------------
    skin_groups: dict[str, list[str]] = defaultdict(list)
    for fn in common:
        skin_groups[skin_tone.get(fn, "Unknown") or "Unknown"].append(fn)

    skin_tone_rows = []
    for group_name, filenames in sorted(skin_groups.items()):
        gt = [arcface[fn]["gt_label"] for fn in filenames]
        pred_arc = [arcface[fn]["predicted_label"] for fn in filenames]
        pred_hse = [hsemotion[fn]["predicted_label"] for fn in filenames]
        n = len(filenames)
        acc_arc = float(np.mean([t == p for t, p in zip(gt, pred_arc)])) if n else float("nan")
        acc_hse = float(np.mean([t == p for t, p in zip(gt, pred_hse)])) if n else float("nan")
        fa_arc = sum(1 for t, p in zip(gt, pred_arc) if p == "Angry" and t != "Angry")
        fa_hse = sum(1 for t, p in zip(gt, pred_hse) if p == "Angry" and t != "Angry")
        skin_tone_rows.append(
            {
                "skin_tone": group_name,
                "n": n,
                "arcface_accuracy": acc_arc,
                "hsemotion_accuracy": acc_hse,
                "arcface_false_angry_count": fa_arc,
                "hsemotion_false_angry_count": fa_hse,
                "arcface_false_angry_rate": fa_arc / n if n else float("nan"),
                "hsemotion_false_angry_rate": fa_hse / n if n else float("nan"),
            }
        )

    # Fisher's exact test: HSEmotion accuracy, Dark vs Medium-Dark (if both present with n>0)
    fisher_result = None
    dark_row = next((r for r in skin_tone_rows if r["skin_tone"] == "Dark"), None)
    meddark_row = next((r for r in skin_tone_rows if r["skin_tone"] == "Medium-Dark"), None)
    if dark_row and meddark_row and dark_row["n"] > 0 and meddark_row["n"] > 0:
        dark_correct = round(dark_row["hsemotion_accuracy"] * dark_row["n"])
        dark_wrong = dark_row["n"] - dark_correct
        med_correct = round(meddark_row["hsemotion_accuracy"] * meddark_row["n"])
        med_wrong = meddark_row["n"] - med_correct
        table = [[dark_correct, dark_wrong], [med_correct, med_wrong]]
        odds_ratio, p_value = fisher_exact(table)
        fisher_result = {
            "comparison": "HSEmotion accuracy: Dark vs Medium-Dark",
            "table": table,
            "odds_ratio": float(odds_ratio),
            "p_value": float(p_value),
        }

    # --- Save artifacts -----------------------------------------------------
    with (OUT_DIR / "comparison_metrics.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "hsemotion_common_subset", "arcface", "difference"])
        for key, label in [
            ("n", "N"),
            ("accuracy", "Accuracy"),
            ("macro_precision", "Macro Precision"),
            ("macro_recall", "Macro Recall"),
            ("macro_f1", "Macro F1"),
        ]:
            h = hsemotion_metrics[key]
            a = arcface_metrics[key]
            writer.writerow([label, h, a, (a - h) if isinstance(a, float) else ""])
        writer.writerow(["False-Angry Rate", fa_hsemotion["false_angry_rate_of_total"], fa_arcface["false_angry_rate_of_total"], fa_arcface["false_angry_rate_of_total"] - fa_hsemotion["false_angry_rate_of_total"]])
        writer.writerow(["Neutral->Angry rate (of Neutral)", fa_hsemotion["neutral_to_angry_rate_of_neutral"], fa_arcface["neutral_to_angry_rate_of_neutral"], fa_arcface["neutral_to_angry_rate_of_neutral"] - fa_hsemotion["neutral_to_angry_rate_of_neutral"]])

    with (OUT_DIR / "per_class_metrics.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class", "model", "precision", "recall", "f1", "support"])
        for cls in class_order:
            for model_name, metrics in [("HSEmotion", hsemotion_metrics), ("ArcFace+LR", arcface_metrics)]:
                pc = metrics["per_class"][cls]
                writer.writerow([cls, model_name, pc["precision"], pc["recall"], pc["f1"], pc["support"]])

    np.savetxt(OUT_DIR / "confusion_matrix_arcface.csv", cm_arcface, fmt="%d", delimiter=",", header=",".join(class_order), comments="")
    np.savetxt(OUT_DIR / "confusion_matrix_hsemotion.csv", cm_hsemotion, fmt="%d", delimiter=",", header=",".join(cm_hsemotion_labels), comments="")
    save_confusion_matrix_png(cm_arcface, class_order, "ArcFace+LR Confusion Matrix (common subset)", OUT_DIR / "confusion_matrix_arcface.png")
    save_confusion_matrix_png(cm_hsemotion, cm_hsemotion_labels, "HSEmotion Confusion Matrix (common subset)", OUT_DIR / "confusion_matrix_hsemotion.png")

    with (OUT_DIR / "false_angry_analysis.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "total_n", "false_angry_count", "false_angry_rate", "neutral_total", "neutral_to_angry_count", "neutral_to_angry_rate"])
        for model_name, fa in [("HSEmotion", fa_hsemotion), ("ArcFace+LR", fa_arcface)]:
            writer.writerow([model_name, fa["total_n"], fa["false_angry_count"], fa["false_angry_rate_of_total"], fa["neutral_total"], fa["neutral_to_angry_count"], fa["neutral_to_angry_rate_of_neutral"]])

    with (OUT_DIR / "skin_tone_analysis.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(skin_tone_rows[0].keys()) if skin_tone_rows else [])
        writer.writeheader()
        for row in skin_tone_rows:
            writer.writerow(row)

    with (OUT_DIR / "statistical_tests.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["test", "detail", "value"])
        writer.writerow(["McNemar", "a_both_correct", mcnemar_result["a_both_correct"]])
        writer.writerow(["McNemar", "b_hsemotion_only_correct", mcnemar_result["b_hsemotion_only"]])
        writer.writerow(["McNemar", "c_arcface_only_correct", mcnemar_result["c_arcface_only"]])
        writer.writerow(["McNemar", "d_both_wrong", mcnemar_result["d_both_wrong"]])
        writer.writerow(["McNemar", "p_value", mcnemar_result["p_value"]])
        writer.writerow(["Bootstrap_Accuracy_ArcFace", "point,lower,upper", boot_acc_arcface])
        writer.writerow(["Bootstrap_Accuracy_HSEmotion", "point,lower,upper", boot_acc_hsemotion])
        writer.writerow(["Bootstrap_FalseAngryRate_ArcFace", "point,lower,upper", boot_fa_arcface])
        writer.writerow(["Bootstrap_FalseAngryRate_HSEmotion", "point,lower,upper", boot_fa_hsemotion])
        if fisher_result:
            writer.writerow(["Fisher_exact", fisher_result["comparison"], f"OR={fisher_result['odds_ratio']:.4f}, p={fisher_result['p_value']:.4f}, table={fisher_result['table']}"])

    with (OUT_DIR / "evaluation_predictions.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["face_filename", "gt_label", "arcface_predicted", "hsemotion_predicted_raw", "hsemotion_predicted_normalized", "skin_tone"])
        for fn in common:
            writer.writerow([fn, arcface[fn]["gt_label"], arcface[fn]["predicted_label"], hsemotion[fn]["predicted_label_raw"], hsemotion[fn]["predicted_label"], skin_tone.get(fn, "")])

    # --- Print summary for report authoring ----------------------------------
    print(json.dumps({
        "population_table": population_table,
        "class_order": class_order,
        "class_counts_common": class_counts_common,
        "arcface_metrics": arcface_metrics,
        "hsemotion_metrics": hsemotion_metrics,
        "fa_arcface": fa_arcface,
        "fa_hsemotion": fa_hsemotion,
        "mcnemar": mcnemar_result,
        "boot_acc_arcface": boot_acc_arcface,
        "boot_acc_hsemotion": boot_acc_hsemotion,
        "boot_fa_arcface": boot_fa_arcface,
        "boot_fa_hsemotion": boot_fa_hsemotion,
        "skin_tone_rows": skin_tone_rows,
        "fisher_result": fisher_result,
        "cm_arcface": cm_arcface.tolist(),
        "cm_hsemotion": cm_hsemotion.tolist(),
        "cm_hsemotion_labels": cm_hsemotion_labels,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
