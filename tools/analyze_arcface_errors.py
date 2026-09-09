"""R8 — Descriptive error analysis + skin-tone analysis on the R7 common
evaluation population.

Reads ONLY reports/arcface_evaluation/evaluation_predictions.csv (the
exact R7 common evaluation artifact — 135 samples, ArcFace OOF
predictions, HSEmotion predictions, ground truth, skin tone). No model is
retrained, no label is changed, no new prediction is generated.

Writes only to reports/arcface_error_analysis/ (new directory) — does not
touch reports/arcface_evaluation/ or any historical artifact.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SRC = Path("reports/arcface_evaluation/evaluation_predictions.csv")
OUT_DIR = Path("reports/arcface_error_analysis")

ARCFACE_CLASSES = ["Fear", "Happy", "Neutral", "Sad", "Surprise"]
FULL_CLASSES = ["Fear", "Happy", "Neutral", "Sad", "Surprise", "Angry", "Disgust"]


def load_rows(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def per_class_table(y_true: list[str], y_pred: list[str], classes: list[str]) -> list[dict]:
    rows = []
    for cls in classes:
        idx = [i for i, t in enumerate(y_true) if t == cls]
        n = len(idx)
        correct = sum(1 for i in idx if y_pred[i] == cls)
        incorrect = n - correct
        rows.append(
            {
                "ground_truth": cls,
                "n": n,
                "correct": correct,
                "incorrect": incorrect,
                "accuracy": correct / n if n else float("nan"),
                "error_rate": incorrect / n if n else float("nan"),
            }
        )
    return rows


def neutral_error_breakdown(y_true: list[str], y_pred: list[str], valid_pred_classes: list[str]) -> dict:
    idx = [i for i, t in enumerate(y_true) if t == "Neutral"]
    n = len(idx)
    correct = sum(1 for i in idx if y_pred[i] == "Neutral")
    wrong = [y_pred[i] for i in idx if y_pred[i] != "Neutral"]
    wrong_counts = Counter(wrong)
    dominant = wrong_counts.most_common(1)[0] if wrong_counts else (None, 0)
    breakdown = {}
    for cls in FULL_CLASSES:
        if cls == "Neutral":
            continue
        if cls not in valid_pred_classes:
            breakdown[cls] = None  # not in label space
        else:
            breakdown[cls] = wrong_counts.get(cls, 0)
    return {
        "n": n,
        "correct": correct,
        "error_rate": (n - correct) / n if n else float("nan"),
        "dominant_wrong_class": dominant[0],
        "dominant_wrong_count": dominant[1],
        "breakdown": breakdown,
    }


def confusion_pairs(y_true: list[str], y_pred: list[str]) -> Counter:
    return Counter((t, p) for t, p in zip(y_true, y_pred) if t != p)


def save_confusion_matrix_png(cm: np.ndarray, labels: list[str], title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(max(6, len(labels)), max(5, len(labels) - 1)))
    im = ax.imshow(cm, cmap="Purples")
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
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows(SRC)

    # --- Validation checks (Section 21) --------------------------------------
    n = len(rows)
    ids = [r["face_filename"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate sample IDs found"
    for r in rows:
        assert r["gt_label"], "missing GT label"
        assert r["arcface_predicted"], "missing ArcFace prediction"
        assert r["hsemotion_predicted_normalized"], "missing HSEmotion prediction"
        assert r["arcface_predicted"] in ARCFACE_CLASSES, f"ArcFace predicted out-of-space class: {r['arcface_predicted']}"

    y_true = [r["gt_label"] for r in rows]
    y_pred_arc = [r["arcface_predicted"] for r in rows]
    y_pred_hse = [r["hsemotion_predicted_normalized"] for r in rows]

    print(f"Population check: N={n}, unique_ids={len(set(ids))}")
    print(f"GT classes present: {sorted(set(y_true))}")
    print(f"ArcFace predicted classes present: {sorted(set(y_pred_arc))}")
    print(f"HSEmotion predicted classes present: {sorted(set(y_pred_hse))}")

    # --- Section 3/4: overall error analysis ---------------------------------
    arcface_table = per_class_table(y_true, y_pred_arc, ARCFACE_CLASSES)
    hsemotion_table = per_class_table(y_true, y_pred_hse, ARCFACE_CLASSES)

    with (OUT_DIR / "overall_error_analysis.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "ground_truth", "n", "correct", "incorrect", "accuracy", "error_rate"])
        for model_name, table in [("ArcFace+LR", arcface_table), ("HSEmotion", hsemotion_table)]:
            for row in table:
                writer.writerow([model_name, row["ground_truth"], row["n"], row["correct"], row["incorrect"], row["accuracy"], row["error_rate"]])

    # --- Section 5: Neutral error analysis -----------------------------------
    neutral_arc = neutral_error_breakdown(y_true, y_pred_arc, ARCFACE_CLASSES)
    neutral_hse = neutral_error_breakdown(y_true, y_pred_hse, FULL_CLASSES)

    with (OUT_DIR / "neutral_error_analysis.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "neutral_n", "correct_neutral", "neutral_error_rate", "dominant_wrong_class", "dominant_wrong_count"])
        writer.writerow(["ArcFace+LR", neutral_arc["n"], neutral_arc["correct"], neutral_arc["error_rate"], neutral_arc["dominant_wrong_class"], neutral_arc["dominant_wrong_count"]])
        writer.writerow(["HSEmotion", neutral_hse["n"], neutral_hse["correct"], neutral_hse["error_rate"], neutral_hse["dominant_wrong_class"], neutral_hse["dominant_wrong_count"]])
        writer.writerow([])
        writer.writerow(["predicted_class", "arcface_count_or_na", "hsemotion_count"])
        for cls in ["Neutral", "Happy", "Sad", "Surprise", "Fear", "Angry", "Disgust"]:
            arc_val = "N/A" if cls not in ARCFACE_CLASSES else (neutral_arc["correct"] if cls == "Neutral" else neutral_arc["breakdown"].get(cls))
            hse_val = neutral_hse["correct"] if cls == "Neutral" else neutral_hse["breakdown"].get(cls)
            writer.writerow([cls, arc_val, hse_val])

    # --- Section 6: general error taxonomy -----------------------------------
    arc_pairs = confusion_pairs(y_true, y_pred_arc)
    hse_pairs = confusion_pairs(y_true, y_pred_hse)

    with (OUT_DIR / "error_taxonomy.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "true_class", "predicted_class", "count"])
        for model_name, pairs in [("ArcFace+LR", arc_pairs), ("HSEmotion", hse_pairs)]:
            for (t, p), c in sorted(pairs.items(), key=lambda kv: -kv[1]):
                writer.writerow([model_name, t, p, c])

    # --- Section 8: probability analysis (descriptive only) ------------------
    # ArcFace has stored probabilities in the original R6/R7 artifact; this
    # evaluation_predictions.csv does not carry them (by R7 design), so a
    # probability comparison is not recomputed from a different artifact --
    # documented as a scope limitation in the report instead of silently
    # joining a second file.

    # --- Section 9/10: skin-tone population and performance ------------------
    skin_groups: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        st = r["skin_tone"].strip()
        key = st if st else "Unknown"
        skin_groups.setdefault(key, []).append(i)

    with (OUT_DIR / "skin_tone_analysis.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["skin_tone", "n", "arcface_accuracy", "hsemotion_accuracy", "arcface_neutral_error_rate", "hsemotion_neutral_error_rate"])
        for group, idxs in sorted(skin_groups.items()):
            gt_g = [y_true[i] for i in idxs]
            arc_g = [y_pred_arc[i] for i in idxs]
            hse_g = [y_pred_hse[i] for i in idxs]
            n_g = len(idxs)
            if group == "Unknown":
                writer.writerow([group, n_g, "N/A", "N/A", "N/A", "N/A"])
                continue
            acc_arc = float(np.mean([t == p for t, p in zip(gt_g, arc_g)]))
            acc_hse = float(np.mean([t == p for t, p in zip(gt_g, hse_g)]))
            neutral_idx_g = [i for i, t in enumerate(gt_g) if t == "Neutral"]
            if neutral_idx_g:
                neu_err_arc = 1 - float(np.mean([arc_g[i] == "Neutral" for i in neutral_idx_g]))
                neu_err_hse = 1 - float(np.mean([hse_g[i] == "Neutral" for i in neutral_idx_g]))
            else:
                neu_err_arc = float("nan")
                neu_err_hse = float("nan")
            writer.writerow([group, n_g, acc_arc, acc_hse, neu_err_arc, neu_err_hse])

    # --- Confusion matrices (visualizations) ---------------------------------
    from sklearn.metrics import confusion_matrix

    cm_arc = confusion_matrix(y_true, y_pred_arc, labels=ARCFACE_CLASSES)
    save_confusion_matrix_png(cm_arc, ARCFACE_CLASSES, "ArcFace+LR Confusion Matrix (R8, N=135)", OUT_DIR / "confusion_matrix_arcface.png")

    hse_labels = ARCFACE_CLASSES + ["Other"]
    y_pred_hse_bucketed = [p if p in ARCFACE_CLASSES else "Other" for p in y_pred_hse]
    cm_hse = confusion_matrix(y_true, y_pred_hse_bucketed, labels=hse_labels)
    save_confusion_matrix_png(cm_hse, hse_labels, "HSEmotion Confusion Matrix (R8, N=135)", OUT_DIR / "confusion_matrix_hsemotion.png")

    # Neutral prediction distribution comparison
    neutral_idx = [i for i, t in enumerate(y_true) if t == "Neutral"]
    arc_neutral_preds = Counter(y_pred_arc[i] for i in neutral_idx)
    hse_neutral_preds = Counter(y_pred_hse[i] for i in neutral_idx)
    all_pred_classes = sorted(set(arc_neutral_preds) | set(hse_neutral_preds))

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(all_pred_classes))
    w = 0.38
    ax.bar(x - w / 2, [arc_neutral_preds.get(c, 0) for c in all_pred_classes], width=w, label="ArcFace+LR")
    ax.bar(x + w / 2, [hse_neutral_preds.get(c, 0) for c in all_pred_classes], width=w, label="HSEmotion")
    ax.set_xticks(x)
    ax.set_xticklabels(all_pred_classes, rotation=20, ha="right")
    ax.set_ylabel("Count")
    ax.set_title(f"Predicted Class Distribution for Ground-Truth Neutral (N={len(neutral_idx)})")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "neutral_prediction_distribution.png", dpi=150)
    plt.close(fig)

    # Skin-tone accuracy comparison (Dark/Medium-Dark only, per scope)
    plot_groups = [g for g in sorted(skin_groups) if g != "Unknown"]
    if plot_groups:
        accs_arc = []
        accs_hse = []
        for g in plot_groups:
            idxs = skin_groups[g]
            gt_g = [y_true[i] for i in idxs]
            accs_arc.append(float(np.mean([y_true[i] == y_pred_arc[i] for i in idxs])))
            accs_hse.append(float(np.mean([y_true[i] == y_pred_hse[i] for i in idxs])))
        fig, ax = plt.subplots(figsize=(7, 5))
        x = np.arange(len(plot_groups))
        w = 0.38
        ax.bar(x - w / 2, accs_arc, width=w, label="ArcFace+LR")
        ax.bar(x + w / 2, accs_hse, width=w, label="HSEmotion")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{g}\n(N={len(skin_groups[g])})" for g in plot_groups])
        ax.set_ylabel("Accuracy")
        ax.set_ylim(0, 1)
        ax.set_title("Accuracy by Skin Tone (R8, common subset)")
        ax.legend()
        ax.grid(axis="y", alpha=0.25)
        plt.tight_layout()
        fig.savefig(OUT_DIR / "skin_tone_accuracy_comparison.png", dpi=150)
        plt.close(fig)

    # --- Finding-strength table (Section 16) ---------------------------------
    finding_rows = [
        {
            "finding": "ArcFace accuracy vs HSEmotion (common subset)",
            "evidence": f"ArcFace {arcface_table_acc(arcface_table):.4f} vs HSEmotion {arcface_table_acc(hsemotion_table):.4f}, N=135, McNemar p=0.4614 (R7)",
            "strength": "Moderate",
            "limitation": "Not statistically significant; small/uneven per-class N; single dataset/video",
        },
        {
            "finding": "ArcFace Neutral error behavior",
            "evidence": f"Neutral N={neutral_arc['n']}, error rate={neutral_arc['error_rate']:.4f}, dominant wrong class={neutral_arc['dominant_wrong_class']}",
            "strength": "Moderate",
            "limitation": "Descriptive only; no significance test; ArcFace cannot predict Angry/Disgust (out of label space)",
        },
        {
            "finding": "HSEmotion Neutral->Angry (common subset)",
            "evidence": f"{neutral_hse['breakdown'].get('Angry')}/{neutral_hse['n']} Neutral samples predicted Angry",
            "strength": "Strong",
            "limitation": "Descriptive; population is the 135-sample common subset, not the full 227-sample historical population",
        },
        {
            "finding": "HSEmotion Neutral->Angry (historical, full dataset)",
            "evidence": "18/76 = 23.7% (docs/EXPERIMENT.md EXP-005)",
            "strength": "Strong",
            "limitation": "Different population (N=227) than the R7/R8 common subset; not directly poolable with the common-subset figure",
        },
        {
            "finding": "Dark vs Medium-Dark performance (HSEmotion)",
            "evidence": "R7 Fisher's exact test p=0.0027 on the 135-sample common subset (docs/EXP-007_ARCFACE_EVALUATION.md Section 10)",
            "strength": "Moderate",
            "limitation": "Statistically significant in this sample, but small subgroup sizes and no external replication; association only, not causal",
        },
        {
            "finding": "Papuan-specific error effect",
            "evidence": "No ethnicity field exists in any dataset artifact",
            "strength": "Unsupported",
            "limitation": "Cannot be quantitatively estimated with current metadata; remains a researcher observation only",
        },
        {
            "finding": "ArcFace false-Angry = 0",
            "evidence": "Structural: Angry excluded from ArcFace's 5-class label space (R6/R7.5)",
            "strength": "Unsupported (as an improvement claim)",
            "limitation": "Not a behavioral finding; must not be interpreted as evidence of anything about false-Angry behavior",
        },
    ]

    with (OUT_DIR / "finding_strength.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["finding", "evidence", "strength", "limitation"])
        writer.writeheader()
        for row in finding_rows:
            writer.writerow(row)

    # --- Print summary --------------------------------------------------------
    print("\n=== ArcFace overall (per class) ===")
    for row in arcface_table:
        print(row)
    print("\n=== HSEmotion overall (per class, common subset) ===")
    for row in hsemotion_table:
        print(row)
    print("\n=== Neutral breakdown ArcFace ===", neutral_arc)
    print("\n=== Neutral breakdown HSEmotion ===", neutral_hse)
    print("\n=== Skin tone groups ===", {k: len(v) for k, v in skin_groups.items()})
    print("\nSaved artifacts to", OUT_DIR)


def arcface_table_acc(table: list[dict]) -> float:
    total_n = sum(r["n"] for r in table)
    total_correct = sum(r["correct"] for r in table)
    return total_correct / total_n if total_n else float("nan")


if __name__ == "__main__":
    main()
