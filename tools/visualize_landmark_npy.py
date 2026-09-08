from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main() -> None:
    npy_path = Path("data/1408-1010-intermediate/landmarks_468/frame_000043_face02.npy")
    image_path = Path("data/1408-1010-intermediate/faces/frame_000043_face02.jpg")

    if not npy_path.exists():
        raise FileNotFoundError(f"Landmark file not found: {npy_path}")

    pts = np.load(npy_path)

    print("=== Landmark NPY Info ===")
    print(f"Path: {npy_path}")
    print(f"Shape: {pts.shape}")
    print(f"Dtype: {pts.dtype}")

    if pts.ndim != 2 or pts.shape[1] < 2:
        raise ValueError(f"Expected shape (N, 2) or (N, >=2), got {pts.shape}")

    table = pd.DataFrame({
        "index": np.arange(len(pts), dtype=int),
        "x": pts[:, 0],
        "y": pts[:, 1],
    })

    print("\n=== All Landmark Coordinates (index, x, y) ===")
    print(table.to_string(index=False))

    out_dir = Path("reports/assets")
    out_dir.mkdir(parents=True, exist_ok=True)

    key_points = {
        33: "right eye",
        263: "left eye",
        1: "nose tip",
        13: "upper lip",
        14: "lower lip",
        61: "right mouth corner",
        291: "left mouth corner",
        55: "right brow inner",
        65: "right brow outer",
    }

    # Plot on blank canvas
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(pts[:, 0], pts[:, 1], s=8)

    for idx, name in key_points.items():
        if idx < len(pts):
            x, y = pts[idx, 0], pts[idx, 1]
            ax.text(x + 1.5, y + 1.5, f"{idx}", fontsize=8)

    ax.set_title("Landmark Visualization — frame_000043_face02")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.invert_yaxis()
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)
    fig.tight_layout()

    blank_plot_path = out_dir / "landmark_frame_000043_face02_blank.png"
    fig.savefig(blank_plot_path, dpi=200)
    plt.close(fig)

    print(f"\nSaved blank-canvas plot: {blank_plot_path}")

    # Overlay on actual image if available
    if image_path.exists():
        img_bgr = cv2.imread(str(image_path))
        if img_bgr is None:
            print(f"Could not read image: {image_path}")
        else:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            fig2, ax2 = plt.subplots(figsize=(8, 8))
            ax2.imshow(img_rgb)
            ax2.scatter(pts[:, 0], pts[:, 1], s=8)

            for idx, name in key_points.items():
                if idx < len(pts):
                    x, y = pts[idx, 0], pts[idx, 1]
                    ax2.text(x + 1.5, y + 1.5, f"{idx}", fontsize=8)

            ax2.set_title("Landmark Overlay — frame_000043_face02")
            ax2.set_xlabel("x")
            ax2.set_ylabel("y")
            ax2.invert_yaxis()
            fig2.tight_layout()

            overlay_path = out_dir / "landmark_frame_000043_face02_overlay.png"
            fig2.savefig(overlay_path, dpi=200)
            plt.close(fig2)
            print(f"Saved overlay plot: {overlay_path}")
    else:
        print(f"Image not found, skip overlay: {image_path}")


if __name__ == "__main__":
    main()
