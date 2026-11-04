"""Generate the research-tracking figures for the FER thesis.

Every plotted number is read from a saved experiment output (paths in SOURCES);
nothing is estimated. All plotted values are also written to
figures/figure_data.json, which validate_figures.py checks against the sources.

Reads only; writes only inside docs/figures/research-tracking/figures/.

Run from the repository root:
    uv run python docs/figures/research-tracking/make_figures.py --data-root /path/to/main/checkout
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from fer_dataset.shared.clahe import apply_strategy_b_clahe  # noqa: E402  (verbatim EXP-006 function)

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"

SOURCES = {
    "exp010": "reports/fairness_135/fairness_summary.json",
    "exp011": "reports/clahe_fairness_135/clahe_fairness_summary.json",
    "exp007_tests": "reports/arcface_evaluation/statistical_tests.csv",
    "exp012": "experiments/EXP-012-relabel/results/metrics.json",
    "exp012_cm": "experiments/EXP-012-relabel/results/confusion_matrix.csv",
    "exp012_per_class": "experiments/EXP-012-relabel/results/per_class_metrics.csv",
    "round2_labels": "experiments/EXP-012-relabel/labels_round2.csv",
    "landmark_sources": "experiments/EXP-012-relabel/landmark_sources.csv",
    "v2_qc": "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv",
    "v2_frames": "docs/reports/extraction_v2_2026-10-19/frame_level_extraction_manifest_v2.csv",
    # git-ignored, read from --data-root:
    "round1_labels": "data/1408-1010-intermediate/manual_labels_export.csv",
    "clahe_predictions": "data/1408-1010-intermediate/clahe_predictions.csv",
    "source_video": "data/papuan_v2/raw/source_video_manifest.json",
    "legacy_faces": "data/1408-1010-intermediate/faces",
    "overlays": "data/exp012/overlays",
}
# Legacy 227 -> 135 derivation as documented in Chapter 3 and docs/EXP-007_ARCFACE_EVALUATION.md.
LEGACY_DERIVATION = [("Labeled face crops", 227), ("Excluding Ambiguous", 144),
                     ("Excluding rare classes (Angry 1, Disgust 2)", 141),
                     ("Excluding ArcFace alignment failures (6)", 135)]
LEGACY_SAMPLED_FRAMES = 100  # Chapter 3 §3.2: 100 sampled frames produced the 227 crops

# Example crops for Figures 3 and 4 are chosen by a fixed rule (see pick_examples), not by hand.


def pick_examples(data_root: Path) -> tuple[list[str], dict[str, str]]:
    """Figure 3: first two crops (by id) per brightness group whose round-2 overlay was rated Usable.
    Figure 4: first Usable crop with reviewed / proposal landmarks, and the first crop with none."""
    r2 = pd.read_csv(REPO / SOURCES["round2_labels"]).sort_values("labeled_at").groupby("image_id").tail(1)
    tone = {r["filename"][:-4]: r["skin_tone"] for r in csv.DictReader(open(data_root / SOURCES["clahe_predictions"]))}
    r2 = r2.assign(skin_tone=r2.image_id.map(tone)).sort_values("image_id")
    usable = r2[r2.overlay_quality == "Usable"]
    clahe = [i for g in ("Dark", "Medium-Dark") for i in usable[usable.skin_tone == g].image_id.head(2)]
    landmarks = {s: usable[usable.landmark_status == s].image_id.iloc[0] for s in ("reviewed", "proposal")}
    landmarks["missing"] = r2[r2.landmark_status == "missing"].image_id.iloc[0]
    return clahe, landmarks

BLUE, MID, LIGHT, GREY, DARK = "#1f4e79", "#2e75b6", "#9dc3e6", "#8c8c8c", "#333333"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                     "axes.edgecolor": "#444444", "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
                     "svg.fonttype": "none"})
DATA: dict = {}


def save(fig, name: str, raster: bool = False) -> None:
    """SVG + PDF (vector) and a 300-DPI PNG for slides/Word. `raster` marks figures containing photos."""
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def box(ax, x, y, w, h, text, fc=LIGHT, ec=BLUE, fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", fc=fc, ec=ec, lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=DARK,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=10, color=BLUE, lw=1))


def blank(ax, xlim=(0, 10), ylim=(0, 6)):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")


# ----------------------------------------------------------------------------- methodology
def fig01_pipeline():
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    blank(ax, ylim=(-0.1, 6.2))
    top = [("Source video\npesta_babi.mp4", 0.1), ("Frame sampling\n+ face detection", 2.1), ("Face crops\n(227 legacy)", 4.1),
           ("Manual emotion\nlabels (round 1 / 2)", 6.1), ("Brightness group\n(LAB proxy, from\ncrop pixels)", 8.1)]
    for text, x in top:
        box(ax, x, 4.7, 1.8, 1.0, text, fs=7.5)
    for (_, x), (_, x2) in zip(top[:3], top[1:3]):
        arrow(ax, x + 1.8, 5.2, x2, 5.2)
    arrow(ax, 5.9, 5.2, 6.1, 5.2)
    models = [("HSEmotion\n(pretrained, used as-is)", 0.3), ("Adaptive CLAHE (EXP-006)\n+ HSEmotion", 3.7),
              ("ArcFace embedding\n+ Logistic Regression", 7.1)]
    for text, x in models:
        box(ax, x, 2.75, 2.6, 0.95, text, fc="white", fs=7.5)
        arrow(ax, 5.0, 4.7, x + 1.3, 3.7)
    arrow(ax, 7.0, 4.7, 8.6, 3.7)  # labels train the classifier
    box(ax, 1.2, 1.15, 7.6, 1.0, "Group-gap evaluation: accuracy, macro F1, Dark − Medium-Dark gap,\n"
        "worst-group accuracy; grouped-bootstrap 95% CI, McNemar", fs=7.5, bold=False)
    for _, x in models:
        arrow(ax, x + 1.3, 2.75, min(max(x + 1.3, 1.6), 8.4), 2.15)
    arrow(ax, 9.0, 4.7, 8.6, 2.15)  # brightness group used only at evaluation
    box(ax, 0.1, 0.0, 4.85, 0.8, "Protocol A — EXP-010/011\n135 crops · round-1 labels · 5 classes", fc="#eef4fa", fs=7)
    box(ax, 5.05, 0.0, 4.85, 0.8, "Protocol B — EXP-012\n72 crops · round-2 labels · 4 classes", fc="#eef4fa", fs=7)
    ax.text(5, 6.0, "FER fairness evaluation pipeline", ha="center", fontsize=10, fontweight="bold", color=BLUE)
    save(fig, "fig01_research_pipeline")


def fig02_dataset(data_root: Path):
    video = json.load(open(data_root / SOURCES["source_video"]))["source_video"]
    v2 = pd.read_csv(REPO / SOURCES["v2_qc"])
    v2_frames = pd.read_csv(REPO / SOURCES["v2_frames"])
    r1 = pd.read_csv(data_root / SOURCES["round1_labels"])
    assert len(r1) == LEGACY_DERIVATION[0][1] and (r1.gt_label != "Ambiguous").sum() == LEGACY_DERIVATION[1][1]
    legacy = [("Source frames (25 fps)", int(video["total_frames_in_source"])), ("Sampled frames", LEGACY_SAMPLED_FRAMES)] + LEGACY_DERIVATION
    v2_steps = [("Sampled frames", len(v2_frames)), ("Detected faces", len(v2)),
                ("Pass frontality/visibility", int(v2.pass_frontal_visibility.sum())),
                ("Pass size/blur", int(v2.pass_size_blur.sum())), ("Pass all QC", int(v2.pass_all.sum()))]
    DATA["fig02"] = {"legacy": legacy, "v2": v2_steps}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0))
    for ax, steps, title in [(axes[0], legacy, "(a) Legacy set used by EXP-005–012"),
                             (axes[1], v2_steps, "(b) Papuan V2 extraction (supporting, not evaluated)")]:
        labels = [s for s, _ in steps][::-1]
        vals = [v for _, v in steps][::-1]
        ax.barh(labels, vals, color=[MID if i == 0 else LIGHT for i in range(len(vals))], edgecolor=BLUE, lw=0.6)
        ax.set_xscale("log")
        for i, v in enumerate(vals):
            ax.text(v * 1.08, i, f"{v:,}", va="center", fontsize=8)
        ax.set_title(title, loc="left")
        ax.set_xlabel("Count (log scale)")
        ax.set_xlim(right=max(vals) * 6)
    fig.tight_layout()
    save(fig, "fig02_dataset_extraction_qc")


def fig03_clahe(data_root: Path, examples: list[str]):
    saved = {r["filename"][:-4]: r for r in csv.DictReader(open(data_root / SOURCES["clahe_predictions"]))}
    fig, axes = plt.subplots(2, len(examples), figsize=(6.4, 3.9))
    rows = []
    for j, image_id in enumerate(examples):
        img = cv2.imread(str(data_root / SOURCES["legacy_faces"] / f"{image_id}.jpg"))
        out, l_w, clip = apply_strategy_b_clahe(img)
        rows.append({"image_id": image_id, "skin_tone": saved[image_id]["skin_tone"], "clip_limit": round(clip, 4),
                     "saved_clip_limit": round(float(saved[image_id]["clip_limit_used"]), 4)})
        for i, (im, lab) in enumerate([(img, "Original"), (out, f"CLAHE (clip {clip:.2f})")]):
            axes[i, j].imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
            axes[i, j].set_xticks([])
            axes[i, j].set_yticks([])
            axes[i, j].set_title(lab if i else f"{saved[image_id]['skin_tone']}\n{lab}", fontsize=8)
    DATA["fig03"] = rows
    fig.suptitle("INTERNAL — identifiable faces; anonymize before publication", fontsize=7, color="#a00000", y=0.02)
    fig.tight_layout()
    save(fig, "fig03_original_vs_clahe", raster=True)


def fig04_landmarks(data_root: Path, examples: dict[str, str]):
    src = pd.read_csv(REPO / SOURCES["landmark_sources"])
    counts = src.landmark_status.value_counts().to_dict()
    DATA["fig04"] = {"counts": counts, "examples": examples}
    fig = plt.figure(figsize=(7.0, 2.8))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.4])
    for k, (status, image_id) in enumerate(examples.items()):
        ax = fig.add_subplot(gs[0, k])
        ax.imshow(cv2.cvtColor(cv2.imread(str(data_root / SOURCES["overlays"] / f"{image_id}.png")), cv2.COLOR_BGR2RGB))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"({'abc'[k]}) {status}", fontsize=8)
    ax = fig.add_subplot(gs[0, 3])
    order = ["reviewed", "proposal", "missing"]
    ax.bar(range(3), [counts[o] for o in order], color=[BLUE, MID, LIGHT], edgecolor=BLUE, lw=0.6)
    ax.set_xticks(range(3), ["Reviewed", "Proposal", "Missing"], fontsize=7)
    for i, o in enumerate(order):
        ax.text(i, counts[o] + 2, counts[o], ha="center", fontsize=8)
    ax.set_title("(d) Overlay status, 227 crops", fontsize=8)
    ax.set_ylabel("Crops")
    fig.text(0.01, -0.02, "42 points: eyebrows 17–26, eyes 36–47, mouth 48–67. Visual aid only.   "
             "INTERNAL — identifiable faces.", fontsize=7, color="#a00000")
    fig.tight_layout()
    save(fig, "fig04_landmark_annotation", raster=True)


def fig05_arcface():
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
    blank(ax, ylim=(0, 3))
    steps = [("Face crop", 0.05, 1.8), ("Re-detect + align\n(InsightFace)", 2.05, 1.8), ("ArcFace\nw600k_r50\n(frozen)", 4.05, 1.8),
             ("512-d\nL2-normalized\nembedding", 6.05, 1.8), ("Logistic\nRegression (L2,\nclass-balanced)", 8.05, 1.9)]
    for text, x, w in steps:
        box(ax, x, 1.4, w, 1.1, text, fc=LIGHT if "frozen" not in text else "white", fs=7)
    for (_, x, w), (_, x2, _) in zip(steps, steps[1:]):
        arrow(ax, x + w, 1.95, x2, 1.95)
    ax.text(5.0, 0.75, "Validation: 5-fold StratifiedGroupKFold over 3-frame temporal blocks, seed 42; "
            "every crop predicted out-of-fold.", ha="center", fontsize=8, color=DARK)
    ax.text(5.0, 0.3, "Only the classifier is trained; ArcFace weights are never updated (no fine-tuning).",
            ha="center", fontsize=8, color=GREY)
    save(fig, "fig05_arcface_logreg")


# ----------------------------------------------------------------------------- results
def parse_ci(text: str) -> tuple[float, float, float]:
    return tuple(float(x) for x in text.strip("()").split(","))


def fig06_exp010():
    e10 = json.load(open(REPO / SOURCES["exp010"]))
    tests = {r["test"]: r["value"] for r in csv.DictReader(open(REPO / SOURCES["exp007_tests"]))}
    models = ["HSEmotion", "ArcFace+LR"]
    acc = [e10["overall"][m]["accuracy"] for m in models]
    f1 = [e10["overall"][m]["macro_f1"] for m in models]
    ci = [parse_ci(tests["Bootstrap_Accuracy_HSEmotion"])[1:], parse_ci(tests["Bootstrap_Accuracy_ArcFace"])[1:]]
    DATA["fig06"] = {"accuracy": dict(zip(models, acc)), "macro_f1": dict(zip(models, f1)), "accuracy_ci95": dict(zip(models, ci)), "n": e10["n"]}
    fig, ax = plt.subplots(figsize=(4.2, 2.8))
    x = np.arange(2)
    ax.bar(x - 0.18, acc, 0.34, color=MID, label="Accuracy",
           yerr=[[a - c[0] for a, c in zip(acc, ci)], [c[1] - a for a, c in zip(acc, ci)]], capsize=3, ecolor=DARK)
    ax.bar(x + 0.18, f1, 0.34, color=LIGHT, edgecolor=BLUE, lw=0.6, label="Macro F1")
    for i in range(2):
        ax.text(i - 0.18, acc[i] / 2, f"{acc[i]:.3f}", ha="center", color="white", fontsize=8)
        ax.text(i + 0.18, f1[i] / 2, f"{f1[i]:.3f}", ha="center", fontsize=8)
    ax.set_xticks(x, models)
    ax.set_ylim(0, 0.7)
    ax.set_ylabel("Score")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"EXP-010 (Protocol A): n = {e10['n']}, 5 classes", loc="left")
    save(fig, "fig06_exp010_performance")


def fig07_exp011():
    e = json.load(open(REPO / SOURCES["exp011"]))
    c = e["conditions"]
    ch = e["clahe_minus_original"]
    DATA["fig07"] = {
        "accuracy": {k: c[k]["accuracy"] for k in c}, "macro_f1": {k: c[k]["macro_f1"] for k in c},
        "group_accuracy": {k: {g: c[k]["groups"][g]["accuracy"] for g in c[k]["groups"]} for k in c},
        "changes": {"accuracy": [ch["accuracy_change"], *ch["accuracy_change_ci95"]],
                    "Dark": [ch["group_accuracy_change"]["Dark"]["change"], *ch["group_accuracy_change"]["Dark"]["ci95"]],
                    "Medium-Dark": [ch["group_accuracy_change"]["Medium-Dark"]["change"], *ch["group_accuracy_change"]["Medium-Dark"]["ci95"]],
                    "gap": [ch["gap_change"], *ch["gap_change_ci95"]]}}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axes[0]
    labels = ["Accuracy", "Macro F1", "Dark\naccuracy", "Medium-Dark\naccuracy"]
    orig = [c["Original"]["accuracy"], c["Original"]["macro_f1"], c["Original"]["groups"]["Dark"]["accuracy"], c["Original"]["groups"]["Medium-Dark"]["accuracy"]]
    clahe = [c["CLAHE"]["accuracy"], c["CLAHE"]["macro_f1"], c["CLAHE"]["groups"]["Dark"]["accuracy"], c["CLAHE"]["groups"]["Medium-Dark"]["accuracy"]]
    x = np.arange(4)
    ax.bar(x - 0.18, orig, 0.34, color=MID, label="Original")
    ax.bar(x + 0.18, clahe, 0.34, color=LIGHT, edgecolor=BLUE, lw=0.6, label="CLAHE")
    for i in range(4):
        ax.text(i - 0.18, orig[i] + 0.01, f"{orig[i]:.3f}", ha="center", fontsize=7)
        ax.text(i + 0.18, clahe[i] + 0.01, f"{clahe[i]:.3f}", ha="center", fontsize=7)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylim(0, 0.6)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("(a) HSEmotion, 135 crops", loc="left")
    ax = axes[1]
    names = ["accuracy", "Dark", "Medium-Dark", "gap"]
    shown = ["Accuracy", "Dark acc.", "Medium-Dark acc.", "Gap (Dark − MD)"]
    for i, k in enumerate(names):
        v, lo, hi = DATA["fig07"]["changes"][k]
        ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], fmt="o", color=BLUE, capsize=3)
        ax.text(hi + 0.01, i, f"{v:+.3f}", va="center", fontsize=7)
    ax.axvline(0, color=GREY, lw=0.8, ls="--")
    ax.set_yticks(range(4), shown, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("CLAHE − Original (95% CI)")
    ax.set_title("(b) Changes: inconclusive", loc="left")
    fig.tight_layout()
    save(fig, "fig07_exp011_clahe")


def fig08_exp012():
    m = json.load(open(REPO / SOURCES["exp012"]))
    r = m["retrained_all_usable"]
    comp = m["comparison_same_crops_round2_labels"]["models"]
    names = list(comp)
    DATA["fig08"] = {"retrained": {"n": r["n"], "accuracy": r["accuracy"], "accuracy_ci95": r["accuracy_ci95"], "macro_f1": r["macro_f1"]},
                     "same_crops": {k: {"n": v["n"], "accuracy": v["accuracy"], "accuracy_ci95": v["accuracy_ci95"], "macro_f1": v["macro_f1"]} for k, v in comp.items()}}
    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    x = np.arange(len(names))
    acc = [comp[k]["accuracy"] for k in names]
    ci = [comp[k]["accuracy_ci95"] for k in names]
    f1 = [comp[k]["macro_f1"] for k in names]
    ax.bar(x - 0.18, acc, 0.34, color=MID, label="Accuracy", yerr=[[a - c[0] for a, c in zip(acc, ci)], [c[1] - a for a, c in zip(acc, ci)]], capsize=3, ecolor=DARK)
    ax.bar(x + 0.18, f1, 0.34, color=LIGHT, edgecolor=BLUE, lw=0.6, label="Macro F1")
    for i in range(len(names)):
        ax.text(i - 0.18, 0.02, f"{acc[i]:.3f}", ha="center", color="white", fontsize=7.5)
        ax.text(i + 0.18, 0.02, f"{f1[i]:.3f}", ha="center", fontsize=7.5)
    ax.set_xticks(x, ["ArcFace+LR\nretrained (round 2)", "HSEmotion\n(fixed)", "ArcFace+LR\nEXP-007 (round 1)"], fontsize=8)
    ax.set_ylim(0, 0.85)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title(f"EXP-012 (Protocol B): same {comp[names[0]]['n']} crops, round-2 labels, 4 classes", loc="left")
    ax.text(0.0, -0.3, f"Retrained model on all {r['n']} usable crops: accuracy {r['accuracy']:.3f} "
            f"[{r['accuracy_ci95'][0]:.3f}, {r['accuracy_ci95'][1]:.3f}], macro F1 {r['macro_f1']:.3f}. "
            "Error bars: 95% grouped-bootstrap CI.", transform=ax.transAxes, fontsize=7, color=GREY)
    save(fig, "fig08_exp012_performance")


def fig09_exp012_cm():
    cm = pd.read_csv(REPO / SOURCES["exp012_cm"], index_col=0)
    pc = pd.read_csv(REPO / SOURCES["exp012_per_class"])
    DATA["fig09"] = {"confusion_matrix": cm.to_dict(), "per_class_f1": dict(zip(pc["class"], pc.f1)), "support": dict(zip(pc["class"], pc.support.astype(int)))}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1, 1.1]})
    ax = axes[0]
    ax.imshow(cm.values, cmap="Blues")
    ax.set_xticks(range(len(cm.columns)), cm.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(cm.index)), cm.index)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            v = cm.values[i, j]
            ax.text(j, i, v, ha="center", va="center", fontsize=8, color="white" if v > cm.values.max() / 2 else DARK)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Round-2 label")
    ax.set_title("(a) Confusion matrix (out-of-fold)", loc="left")
    ax.spines[:].set_visible(False)
    ax = axes[1]
    ax.barh(pc["class"], pc.f1, color=MID)
    for i, (f, s) in enumerate(zip(pc.f1, pc.support)):
        ax.text(f + 0.01, i, f"{f:.3f}  (n={s})", va="center", fontsize=8)
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    ax.set_xlabel("F1")
    ax.set_title("(b) Per-class F1", loc="left")
    fig.tight_layout()
    save(fig, "fig09_exp012_confusion_per_class")


def fig10_groups():
    e10 = json.load(open(REPO / SOURCES["exp010"]))["full_regroup_n135"]
    e11 = json.load(open(REPO / SOURCES["exp011"]))["conditions"]
    e12 = json.load(open(REPO / SOURCES["exp012"]))
    a_rows = [  # (label, Dark acc, Dark CI or None, MD acc, MD CI or None, gap, gap CI)
        ("HSEmotion (original)", e11["Original"]["groups"]["Dark"]["accuracy"], e11["Original"]["groups"]["Dark"]["accuracy_ci95"],
         e11["Original"]["groups"]["Medium-Dark"]["accuracy"], e11["Original"]["groups"]["Medium-Dark"]["accuracy_ci95"],
         e11["Original"]["gap_dark_minus_medium_dark"], e11["Original"]["gap_ci95"]),
        ("HSEmotion (CLAHE)", e11["CLAHE"]["groups"]["Dark"]["accuracy"], e11["CLAHE"]["groups"]["Dark"]["accuracy_ci95"],
         e11["CLAHE"]["groups"]["Medium-Dark"]["accuracy"], e11["CLAHE"]["groups"]["Medium-Dark"]["accuracy_ci95"],
         e11["CLAHE"]["gap_dark_minus_medium_dark"], e11["CLAHE"]["gap_ci95"]),
        ("ArcFace+LR", e10["groups"]["Dark"]["ArcFace+LR"]["accuracy"], None, e10["groups"]["Medium-Dark"]["ArcFace+LR"]["accuracy"], None,
         e10["models"]["ArcFace+LR"]["gap_dark_minus_medium_dark"], e10["models"]["ArcFace+LR"]["gap_ci95"]),
    ]
    comp = e12["comparison_same_crops_round2_labels"]["models"]
    retr = e12["retrained_all_usable"]
    b_rows = [(f"ArcFace+LR retrained (n={retr['n']})", retr["groups"]["Dark"]["accuracy"], retr["groups"]["Dark"]["accuracy_ci95"],
               retr["groups"]["Medium-Dark"]["accuracy"], retr["groups"]["Medium-Dark"]["accuracy_ci95"],
               retr["gap_dark_minus_medium_dark"], retr["gap_ci95"])]
    for k, short in [("HSEmotion (fixed)", "HSEmotion, re-scored"), ("ArcFace+LR (EXP-007, round-1 trained)", "ArcFace+LR EXP-007, re-scored")]:
        v = comp[k]
        b_rows.append((f"{short} (n={v['n']})", v["groups"]["Dark"]["accuracy"], v["groups"]["Dark"]["accuracy_ci95"],
                       v["groups"]["Medium-Dark"]["accuracy"], v["groups"]["Medium-Dark"]["accuracy_ci95"],
                       v["gap_dark_minus_medium_dark"], v["gap_ci95"]))
    DATA["fig10"] = {"protocol_A": a_rows, "protocol_B": b_rows,
                     "group_n_A": {g: e10["groups"][g]["n"] for g in e10["groups"]},
                     "group_n_B": {g: retr["groups"][g]["n"] for g in retr["groups"]}}
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.6), gridspec_kw={"width_ratios": [1.3, 1]})
    for r, (rows, title) in enumerate([(a_rows, f"Protocol A — EXP-010/011: 135 crops (Dark {e10['groups']['Dark']['n']}, "
                                                f"Medium-Dark {e10['groups']['Medium-Dark']['n']}), round-1 labels, 5 classes"),
                                       (b_rows, f"Protocol B — EXP-012: round-2 labels, 4 classes (Dark {retr['groups']['Dark']['n']}, "
                                                f"Medium-Dark {retr['groups']['Medium-Dark']['n']} for the retrained model)")]):
        ax = axes[r, 0]
        for i, (lab, d, dci, md, mdci, *_rest) in enumerate(rows):
            for val, ci, off, color, name in [(d, dci, -0.15, BLUE, "Dark"), (md, mdci, 0.15, LIGHT, "Medium-Dark")]:
                if ci is None:
                    ax.plot(val, i + off, "o", color=color, mec=BLUE, label=name if i == 0 else None)
                else:
                    ax.errorbar(val, i + off, xerr=[[val - ci[0]], [ci[1] - val]], fmt="o", color=color, mec=BLUE,
                                ecolor=BLUE, capsize=2.5, label=name if i == 0 else None)
        ax.set_yticks(range(len(rows)), [x[0] for x in rows], fontsize=7.5)
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.set_xlabel("Accuracy (95% CI where saved)")
        if r == 0:
            ax.legend(frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(0.0, 1.08), ncol=2)
        ax.set_title(title, loc="left", fontsize=8)
        ax = axes[r, 1]
        for i, (*_, g, gci) in enumerate(rows):
            ax.errorbar(g, i, xerr=[[g - gci[0]], [gci[1] - g]], fmt="s", color=BLUE, capsize=2.5)
            ax.text(gci[1] + 0.02, i, f"{g:+.3f}", va="center", fontsize=7)
        ax.axvline(0, color=GREY, lw=0.8, ls="--")
        ax.set_yticks(range(len(rows)), [""] * len(rows))
        ax.invert_yaxis()
        ax.set_xlim(-0.6, 0.8)
        ax.set_xlabel("Gap: Dark − Medium-Dark (95% CI)")
    fig.tight_layout()
    save(fig, "fig10_dark_vs_medium_dark")


def fig11_annotation(data_root: Path):
    r1 = pd.read_csv(data_root / SOURCES["round1_labels"])
    r2 = pd.read_csv(REPO / SOURCES["round2_labels"]).sort_values("labeled_at").groupby("image_id").tail(1)
    src = pd.read_csv(REPO / SOURCES["landmark_sources"]).set_index("image_id")
    classes = ["Neutral", "Happy", "Sad", "Surprise", "Fear", "Angry", "Disgust", "Ambiguous"]
    c1, c2 = Counter(r1.gt_label), Counter(r2.label)
    r2 = r2.assign(status=r2.image_id.map(src.landmark_status))
    amb = {s: [int(((r2.status == s) & (r2.label == "Ambiguous")).sum()), int(((r2.status == s) & (r2.label != "Ambiguous")).sum())]
           for s in ["reviewed", "proposal", "missing"]}
    DATA["fig11"] = {"round1": {k: c1.get(k, 0) for k in classes}, "round2": {k: c2.get(k, 0) for k in classes},
                     "ambiguous_by_landmark_status": amb}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    x = np.arange(len(classes))
    ax.bar(x - 0.2, [c1.get(k, 0) for k in classes], 0.38, color=LIGHT, edgecolor=BLUE, lw=0.6, label="Round 1 (EXP-005–011)")
    ax.bar(x + 0.2, [c2.get(k, 0) for k in classes], 0.38, color=MID, label="Round 2 (EXP-012)")
    for i, k in enumerate(classes):
        ax.text(i - 0.2, c1.get(k, 0) + 2, c1.get(k, 0), ha="center", fontsize=6.5)
        ax.text(i + 0.2, c2.get(k, 0) + 2, c2.get(k, 0), ha="center", fontsize=6.5)
    ax.set_xticks(x, classes, rotation=30, ha="right")
    ax.set_ylabel("Crops (of 227)")
    ax.legend(frameon=False, fontsize=7.5)
    ax.set_title("(a) Label distribution by round", loc="left")
    ax = axes[1]
    order = ["reviewed", "proposal", "missing"]
    a = [amb[s][0] for s in order]
    n = [amb[s][1] for s in order]
    ax.bar(order, n, color=MID, label="Emotion label")
    ax.bar(order, a, bottom=n, color=LIGHT, edgecolor=BLUE, lw=0.6, label="Ambiguous")
    for i in range(3):
        ax.text(i, n[i] + a[i] + 2, f"{a[i]}/{a[i] + n[i]} Amb.", ha="center", fontsize=7)
    ax.set_ylabel("Crops")
    ax.set_ylim(0, max(a[i] + n[i] for i in range(3)) * 1.35)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.set_title("(b) Round 2 by overlay status", loc="left")
    fig.tight_layout()
    save(fig, "fig11_annotation_landmarks")


TIMELINE = [  # (date, label, evidence)
    ("2026-08-14", "Round-1 manual labels (227 crops)", "manual_labels_export.csv labeled_at"),
    ("2026-08-15", "EXP-005/006: HSEmotion audit, CLAHE ablation", "first commit 74caeb7"),
    ("2026-09-09", "EXP-007/008/R9: ArcFace+LR, error analysis, validation", "first commit 840e0d5"),
    ("2026-10-19", "Papuan V2 extraction, QC, delivery package", "commits 8373e1c, 8a7c60a"),
    ("2026-10-24", "EXP-010/011: group-gap and CLAHE fairness analysis", "commits 5ae3a56, a697f23"),
    ("2026-10-25", "Thesis Ch. 1–5 aligned to fairness RQs", "commits 62256a7–4739f13"),
    ("2026-10-25", "EXP-012 labeling project (227 tasks)", "commit 3a8a072"),
    ("2026-11-04", "EXP-012 round-2 export and retraining", "commits 684ed4c, bc8df93"),
]


def fig12_timeline():
    DATA["fig12"] = TIMELINE
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    dates = pd.to_datetime([d for d, _, _ in TIMELINE])
    ys = np.arange(len(TIMELINE))[::-1]
    ax.plot(dates, ys, color=LIGHT, lw=1, zorder=1)
    for y, dt, (_, label, _) in zip(ys, dates, TIMELINE):
        ax.plot(dt, y, "o", color=BLUE, ms=5, zorder=2)
        ax.text(dt + pd.Timedelta(days=2), y, f"{dt:%d %b}  {label}", va="center", fontsize=7.2)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlim(dates.min() - pd.Timedelta(days=4), dates.max() + pd.Timedelta(days=60))
    ax.set_ylim(-0.7, len(TIMELINE) - 0.3)
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
    ax.set_title("Research timeline (dates from labels and git history)", loc="left")
    save(fig, "fig12_timeline")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-root", type=Path, default=REPO, help="Checkout whose git-ignored data/ holds crops and labels.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    fig01_pipeline()
    fig02_dataset(args.data_root)
    clahe_examples, landmark_examples = pick_examples(args.data_root)
    fig03_clahe(args.data_root, clahe_examples)
    fig04_landmarks(args.data_root, landmark_examples)
    fig05_arcface()
    fig06_exp010()
    fig07_exp011()
    fig08_exp012()
    fig09_exp012_cm()
    fig10_groups()
    fig11_annotation(args.data_root)
    fig12_timeline()
    (OUT / "figure_data.json").write_text(json.dumps(DATA, indent=1, default=str))
    print(f"Wrote {len(list(OUT.glob('*.svg')))} SVG figures and figure_data.json to {OUT}")


if __name__ == "__main__":
    main()
