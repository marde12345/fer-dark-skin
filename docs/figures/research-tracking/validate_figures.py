"""Check that every number in figures/figure_data.json and the Mermaid files matches its source.

Re-derives values directly from the saved experiment outputs (raw CSVs/JSON),
independently of make_figures.py. Exits non-zero on any mismatch.

Run from the repository root:
    uv run python docs/figures/research-tracking/validate_figures.py --data-root /path/to/main/checkout
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import pandas as pd

from fer_dataset.shared.clahe import apply_strategy_b_clahe

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FAIL: list[str] = []
N_CHECKS = 0


def check(name: str, got, expected, tol: float = 1e-9) -> None:
    global N_CHECKS
    N_CHECKS += 1
    ok = abs(float(got) - float(expected)) <= tol if isinstance(expected, (int, float)) else got == expected
    if not ok:
        FAIL.append(f"{name}: figure={got!r} source={expected!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-root", type=Path, default=REPO)
    d = parser.parse_args().data_root
    fd = json.load(open(HERE / "figures" / "figure_data.json"))
    e10 = json.load(open(REPO / "reports/fairness_135/fairness_summary.json"))
    e11 = json.load(open(REPO / "reports/clahe_fairness_135/clahe_fairness_summary.json"))
    e12 = json.load(open(REPO / "experiments/EXP-012-relabel/results/metrics.json"))

    # Figure 2 — counts from raw manifests and labels.
    v2 = pd.read_csv(REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv")
    frames = pd.read_csv(REPO / "docs/reports/extraction_v2_2026-10-19/frame_level_extraction_manifest_v2.csv")
    r1 = pd.read_csv(d / "data/1408-1010-intermediate/manual_labels_export.csv")
    video = json.load(open(d / "data/papuan_v2/raw/source_video_manifest.json"))["source_video"]
    legacy = dict(fd["fig02"]["legacy"])
    check("fig02 source frames", legacy["Source frames (25 fps)"], video["total_frames_in_source"])
    check("fig02 labeled crops", legacy["Labeled face crops"], len(r1))
    check("fig02 non-ambiguous", legacy["Excluding Ambiguous"], int((r1.gt_label != "Ambiguous").sum()))
    check("fig02 rare excluded", legacy["Excluding rare classes (Angry 1, Disgust 2)"],
          int((~r1.gt_label.isin(["Ambiguous", "Angry", "Disgust"])).sum()))
    check("fig02 final 135", legacy["Excluding ArcFace alignment failures (6)"],
          len(pd.read_csv(REPO / "reports/arcface_evaluation/evaluation_predictions.csv")))
    v2s = dict(fd["fig02"]["v2"])
    for k, v in [("Sampled frames", len(frames)), ("Detected faces", len(v2)), ("Pass frontality/visibility", int(v2.pass_frontal_visibility.sum())),
                 ("Pass size/blur", int(v2.pass_size_blur.sum())), ("Pass all QC", int(v2.pass_all.sum()))]:
        check(f"fig02 v2 {k}", v2s[k], v)

    # Figure 3 — recomputed clip limits must equal those saved by EXP-006.
    saved = {r["filename"][:-4]: r for r in csv.DictReader(open(d / "data/1408-1010-intermediate/clahe_predictions.csv"))}
    for row in fd["fig03"]:
        _, _, clip = apply_strategy_b_clahe(cv2.imread(str(d / "data/1408-1010-intermediate/faces" / f"{row['image_id']}.jpg")))
        check(f"fig03 clip {row['image_id']} vs EXP-006", round(clip, 4), round(float(saved[row["image_id"]]["clip_limit_used"]), 4), 1e-4)
        check(f"fig03 group {row['image_id']}", row["skin_tone"], saved[row["image_id"]]["skin_tone"])

    # Figure 4 / 11 — landmark and label counts from raw CSVs.
    ls = pd.read_csv(REPO / "experiments/EXP-012-relabel/landmark_sources.csv")
    for k, v in Counter(ls.landmark_status).items():
        check(f"fig04 {k}", fd["fig04"]["counts"][k], v)
    r2 = pd.read_csv(REPO / "experiments/EXP-012-relabel/labels_round2.csv")
    latest = r2.sort_values("labeled_at").groupby("image_id").tail(1)
    for k, v in Counter(r1.gt_label).items():
        check(f"fig11 round1 {k}", fd["fig11"]["round1"][k], v)
    for k, v in Counter(latest.label).items():
        check(f"fig11 round2 {k}", fd["fig11"]["round2"][k], v)
    st = latest.merge(ls, on="image_id", suffixes=("", "_src"))
    for s in ["reviewed", "proposal", "missing"]:
        sub = st[st.landmark_status_src == s]
        check(f"fig11 ambiguous {s}", fd["fig11"]["ambiguous_by_landmark_status"][s], [int((sub.label == "Ambiguous").sum()), int((sub.label != "Ambiguous").sum())])

    # Figure 6 — EXP-010 overall and EXP-007 bootstrap CIs.
    for m in ("HSEmotion", "ArcFace+LR"):
        check(f"fig06 {m} acc", fd["fig06"]["accuracy"][m], e10["overall"][m]["accuracy"])
        check(f"fig06 {m} f1", fd["fig06"]["macro_f1"][m], e10["overall"][m]["macro_f1"])
    tests = {r["test"]: r["value"] for r in csv.DictReader(open(REPO / "reports/arcface_evaluation/statistical_tests.csv"))}
    for m, key in (("HSEmotion", "Bootstrap_Accuracy_HSEmotion"), ("ArcFace+LR", "Bootstrap_Accuracy_ArcFace")):
        lo, hi = [float(x) for x in tests[key].strip("()").split(",")][1:]
        check(f"fig06 {m} CI", [round(x, 12) for x in fd["fig06"]["accuracy_ci95"][m]], [round(lo, 12), round(hi, 12)])

    # Figure 7 — EXP-011.
    c = e11["conditions"]
    for k in c:
        check(f"fig07 {k} acc", fd["fig07"]["accuracy"][k], c[k]["accuracy"])
        check(f"fig07 {k} f1", fd["fig07"]["macro_f1"][k], c[k]["macro_f1"])
        for g in c[k]["groups"]:
            check(f"fig07 {k} {g}", fd["fig07"]["group_accuracy"][k][g], c[k]["groups"][g]["accuracy"])
    ch = e11["clahe_minus_original"]
    check("fig07 gap change", fd["fig07"]["changes"]["gap"], [ch["gap_change"], *ch["gap_change_ci95"]])
    check("fig07 acc change", fd["fig07"]["changes"]["accuracy"], [ch["accuracy_change"], *ch["accuracy_change_ci95"]])

    # Figures 8-10 — EXP-012 and protocol-A group results.
    r = e12["retrained_all_usable"]
    check("fig08 retrained acc", fd["fig08"]["retrained"]["accuracy"], r["accuracy"])
    check("fig08 retrained CI", fd["fig08"]["retrained"]["accuracy_ci95"], r["accuracy_ci95"])
    check("fig08 retrained f1", fd["fig08"]["retrained"]["macro_f1"], r["macro_f1"])
    for k, v in e12["comparison_same_crops_round2_labels"]["models"].items():
        for f in ("n", "accuracy", "accuracy_ci95", "macro_f1"):
            check(f"fig08 {k} {f}", fd["fig08"]["same_crops"][k][f], v[f])
    cm = pd.read_csv(REPO / "experiments/EXP-012-relabel/results/confusion_matrix.csv", index_col=0)
    check("fig09 confusion", fd["fig09"]["confusion_matrix"], json.loads(cm.to_json()))
    for row in e12["per_class"]:
        check(f"fig09 F1 {row['class']}", fd["fig09"]["per_class_f1"][row["class"]], row["f1"])
    oof = pd.read_csv(REPO / "experiments/EXP-012-relabel/results/oof_predictions.csv")
    check("fig09 confusion total = usable", int(cm.values.sum()), len(oof))
    a = fd["fig10"]["protocol_A"]
    check("fig10 A HSE gap", a[0][5], c["Original"]["gap_dark_minus_medium_dark"])
    check("fig10 A HSE gap = EXP-010", a[0][5], e10["full_regroup_n135"]["models"]["HSEmotion"]["gap_dark_minus_medium_dark"])
    check("fig10 A ArcFace gap", a[2][5], e10["full_regroup_n135"]["models"]["ArcFace+LR"]["gap_dark_minus_medium_dark"])
    check("fig10 A ArcFace gap CI", a[2][6], e10["full_regroup_n135"]["models"]["ArcFace+LR"]["gap_ci95"])
    check("fig10 A ArcFace Dark", a[2][1], e10["full_regroup_n135"]["groups"]["Dark"]["ArcFace+LR"]["accuracy"])
    check("fig10 A ArcFace MD", a[2][3], e10["full_regroup_n135"]["groups"]["Medium-Dark"]["ArcFace+LR"]["accuracy"])
    b = fd["fig10"]["protocol_B"]
    check("fig10 B retrained gap", b[0][5], r["gap_dark_minus_medium_dark"])
    check("fig10 B retrained gap CI", b[0][6], r["gap_ci95"])
    check("fig10 B retrained Dark CI", b[0][2], r["groups"]["Dark"]["accuracy_ci95"])
    # Recompute protocol-B group accuracies from per-crop predictions.
    for g in ("Dark", "Medium-Dark"):
        sub = oof[oof.skin_tone_all == g]
        check(f"fig10 B retrained {g} n", fd["fig10"]["group_n_B"][g], len(sub))
        check(f"fig10 B retrained {g} acc (recomputed)", b[0][1] if g == "Dark" else b[0][3], float((sub.arcface_r2 == sub.gt_label).mean()))

    # Mermaid counts.
    mm = (HERE / "mermaid" / "annotation_evaluation_workflow.mmd").read_text()
    excl = e12["dataset"]["exclusions"]
    for text, val in [(f"reviewed ({fd['fig04']['counts']['reviewed']})", True), (f"unreviewed proposal ({fd['fig04']['counts']['proposal']})", True),
                      (f"missing ({fd['fig04']['counts']['missing']})", True), (f"{len(r2)} rows", True),
                      (f"Ambiguous ({int((latest.label == 'Ambiguous').sum())})", True), (f"Fear {excl['excluded_rare_class_Fear']}", True),
                      (f"Disgust {excl['excluded_rare_class_Disgust']}", True), (f"{e12['dataset']['usable']} crops", True),
                      (f"no ArcFace embedding ({e12['dataset']['missing_embedding']})", True),
                      (f"Dark ({r['groups']['Dark']['n']}) vs Medium-Dark ({r['groups']['Medium-Dark']['n']})", True)]:
        check(f"mermaid: '{text}'", text in mm, val)

    print(f"{N_CHECKS} checks, {len(FAIL)} mismatches")
    for f in FAIL:
        print("  MISMATCH", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
