"""Coordinate-only landmark diagrams for the thesis (no image pixels, no faces).

Replaces the earlier photo-based landmark figures with plots drawn purely
from saved 68-point coordinates on a blank canvas, so no identifiable face
appears in the thesis. Reads only experiments/EXP-PAP-005/*.json; writes only
docs/thesis-latex/figures/landmark-*.{pdf,png}.

Run from the repository root:
    uv run python docs/thesis-latex/figures/src/make_landmark_diagrams.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
SRC = REPO / "experiments" / "EXP-PAP-005"
OUT = REPO / "docs" / "thesis-latex" / "figures"

# Same crops as the photo figures they replace.
PILOT_ID = "frame_000186_face01"   # pilot: proposal and human-reviewed
CALIB_ID = "frame_000244_face05"   # calibration batch: proposal vs. reviewed (whole-skeleton shift case)

GROUPS = {  # ibug-300W 68-point layout
    "jaw": (range(0, 17), False), "right eyebrow": (range(17, 22), False), "left eyebrow": (range(22, 27), False),
    "nose bridge": (range(27, 31), False), "nose base": (range(31, 36), False),
    "right eye": (range(36, 42), True), "left eye": (range(42, 48), True),
    "mouth outer": (range(48, 60), True), "mouth inner": (range(60, 68), True),
}
COLORS = {"jaw": "#8c8c8c", "right eyebrow": "#1f4e79", "left eyebrow": "#1f4e79", "nose bridge": "#2e75b6",
          "nose base": "#2e75b6", "right eye": "#2e75b6", "left eye": "#2e75b6", "mouth outer": "#c0504d", "mouth inner": "#c0504d"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "savefig.facecolor": "white", "figure.facecolor": "white"})


def reviewed(path: str, image_id: str) -> tuple[dict[int, tuple[float, float]], tuple[int, int]]:
    rows = [r for r in json.load(open(SRC / path)) if r["image_id"] == image_id]
    return {int(r["landmark_index"]): (float(r["x"]), float(r["y"])) for r in rows}, (rows[0]["image_width"], rows[0]["image_height"])


def proposal(path: str, image_id: str) -> dict[int, tuple[float, float]]:
    rec = json.load(open(SRC / path))[image_id]
    return {i: (float(x), float(y)) for i, (x, y) in enumerate(rec["landmarks_xy"])}


def draw(ax, pts, size, style="-o", color=None, label=None, ms=3.5):
    w, h = size
    ax.add_patch(plt.Rectangle((0, 0), w, h, fill=False, ec="#bbbbbb", lw=0.8, ls="--"))
    for k, (idx, closed) in GROUPS.items():
        seq = [pts[i] for i in idx] + ([pts[idx[0]]] if closed else [])
        xs, ys = zip(*seq)
        ax.plot(xs, ys, style, color=color or COLORS[k], ms=ms, lw=1.1, mfc="white" if style == "-o" else None,
                label=label if (label and k == "jaw") else None)
    ax.set_xlim(-2, w + 2)
    ax.set_ylim(h + 2, -2)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    # (1) Automatic 68-point proposal for the pilot crop, as imported into CVAT.
    rev, size = reviewed("cvat_reviewed_landmarks.json", PILOT_ID)
    prop = proposal("insightface_68pt_pilot_predictions.json", PILOT_ID)
    fig, ax = plt.subplots(figsize=(2.6, 3.2))
    draw(ax, prop, size)
    ax.set_title("Automatic proposal (68 points)", fontsize=8)
    save(fig, "landmark-usulan-68-titik")

    # (2) Human-reviewed 68-point landmarks for the same crop.
    fig, ax = plt.subplots(figsize=(3.0, 3.6))
    draw(ax, rev, size)
    handles = [plt.Line2D([], [], color=c, marker="o", mfc="white", lw=1.1, label=n)
               for n, c in [("jaw", COLORS["jaw"]), ("eyebrows, eyes, nose", "#1f4e79"), ("mouth", COLORS["mouth outer"])]]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=3, fontsize=7, frameon=False)
    save(fig, "landmark-diperiksa-manusia")

    # (3) Proposal vs. reviewed for the calibration crop.
    rev2, size2 = reviewed("calibration_batch_40_reviewed.json", CALIB_ID)
    prop2 = proposal("calibration_batch_40_predictions.json", CALIB_ID)
    fig, ax = plt.subplots(figsize=(3.0, 3.8))
    draw(ax, prop2, size2, style="-x", color="#c0504d", label="Automatic proposal (unreviewed)", ms=4)
    draw(ax, rev2, size2, style="-o", color="#1f4e79", label="Human-reviewed", ms=3)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=1, fontsize=7, frameon=False)
    save(fig, "landmark-usulan-vs-diperiksa")
    print("Wrote landmark-usulan-68-titik, landmark-diperiksa-manusia, landmark-usulan-vs-diperiksa")


if __name__ == "__main__":
    main()
