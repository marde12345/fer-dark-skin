import argparse
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


KEY_POINTS = {
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


def visualize_landmarks(
    input_path: Path,
    output_path: Path | None = None,
    image_path: Path | None = None,
    overlay_output_path: Path | None = None,
) -> None:
    """
    Load a saved landmark .npy file, print its coordinate table, and save a
    blank-canvas scatter plot of the landmarks. If image_path is provided
    and readable, also save an overlay plot of the landmarks on that image.

    Preserves the original script's plotting geometry, key-point labels,
    figure size, axis behavior, and output image format exactly — only the
    previously hardcoded input/output paths are now parameters.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Landmark file not found: {input_path}")

    pts = np.load(input_path)

    print("=== Landmark NPY Info ===")
    print(f"Path: {input_path}")
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

    stem = input_path.stem

    if output_path is None:
        output_path = Path("reports/assets") / f"landmark_{stem}_blank.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Plot on blank canvas
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(pts[:, 0], pts[:, 1], s=8)

    for idx, name in KEY_POINTS.items():
        if idx < len(pts):
            x, y = pts[idx, 0], pts[idx, 1]
            ax.text(x + 1.5, y + 1.5, f"{idx}", fontsize=8)

    ax.set_title(f"Landmark Visualization — {stem}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.invert_yaxis()
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)
    fig.tight_layout()

    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    print(f"\nSaved blank-canvas plot: {output_path}")

    # Overlay on actual image if provided and readable
    if image_path is not None and image_path.exists():
        img_bgr = cv2.imread(str(image_path))
        if img_bgr is None:
            print(f"Could not read image: {image_path}")
        else:
            if overlay_output_path is None:
                overlay_output_path = Path("reports/assets") / f"landmark_{stem}_overlay.png"
            overlay_output_path.parent.mkdir(parents=True, exist_ok=True)

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            fig2, ax2 = plt.subplots(figsize=(8, 8))
            ax2.imshow(img_rgb)
            ax2.scatter(pts[:, 0], pts[:, 1], s=8)

            for idx, name in KEY_POINTS.items():
                if idx < len(pts):
                    x, y = pts[idx, 0], pts[idx, 1]
                    ax2.text(x + 1.5, y + 1.5, f"{idx}", fontsize=8)

            ax2.set_title(f"Landmark Overlay — {stem}")
            ax2.set_xlabel("x")
            ax2.set_ylabel("y")
            ax2.invert_yaxis()
            fig2.tight_layout()

            fig2.savefig(overlay_output_path, dpi=200)
            plt.close(fig2)
            print(f"Saved overlay plot: {overlay_output_path}")
    elif image_path is not None:
        print(f"Image not found, skip overlay: {image_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize a saved MediaPipe landmark .npy file as a blank-canvas "
        "scatter plot, and optionally as an overlay on the source face-crop image.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the landmark .npy file (shape (N, 2) or (N, >=2)).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to save the blank-canvas landmark plot. "
        "Defaults to reports/assets/landmark_<input-stem>_blank.png.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Optional path to the source face-crop image, to additionally render "
        "an overlay plot. If omitted, only the blank-canvas plot is produced.",
    )
    parser.add_argument(
        "--overlay-output",
        type=Path,
        default=None,
        help="Path to save the overlay plot (only used if --image is provided). "
        "Defaults to reports/assets/landmark_<input-stem>_overlay.png.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    visualize_landmarks(
        input_path=args.input,
        output_path=args.output,
        image_path=args.image,
        overlay_output_path=args.overlay_output,
    )


if __name__ == "__main__":
    main()
