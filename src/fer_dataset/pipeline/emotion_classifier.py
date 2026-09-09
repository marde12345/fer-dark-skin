from pathlib import Path

import cv2
import pandas as pd
import insightface
from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
from tqdm import tqdm
import numpy as np


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - np.max(logits)
    exp = np.exp(logits)
    return exp / exp.sum()


class EmotionClassifier:
    """
    Predict facial emotion from cropped face images.
    """

    def __init__(
        self,
        input_dir: str,
        annotation_file: str,
        visualization_dir: str | None = None,
        visualize: bool = False,
    ):
        self.input_dir = Path(input_dir)
        self.annotation_file = Path(annotation_file)
        self.visualization_dir = Path(visualization_dir) if visualization_dir else None
        self.visualize = visualize

        self.annotation_file.parent.mkdir(parents=True, exist_ok=True)

        self.model = HSEmotionRecognizer(model_name="enet_b0_8_best_vgaf")
        # Prepare InsightFace for landmark extraction (used for visualization)
        self.face_app = insightface.app.FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],
        )

        self.face_app.prepare(ctx_id=0)

    def clear_outputs(self) -> None:
        """
        Remove a previously written annotation file, if present.

        This is an explicit action, not a side effect of construction —
        call it before predict() if a clean output state is desired.
        """
        if self.annotation_file.exists():
            self.annotation_file.unlink()

    def predict(self) -> int:

        records = []

        image_paths = sorted(self.input_dir.glob("*.jpg"))

        vis_dir = None
        if self.visualize:
            if self.visualization_dir:
                vis_dir = Path(self.visualization_dir)
            else:
                vis_dir = self.input_dir.parent / "visualization"

            vis_dir.mkdir(parents=True, exist_ok=True)

        for image_path in tqdm(image_paths):

            image = cv2.imread(str(image_path))

            if image is None:
                continue

            try:
                emotion, logits = self.model.predict_emotions(image)
            except Exception:
                continue

            probabilities = softmax(logits)
            confidence = float(probabilities.max())

            records.append(
                {
                    "filename": image_path.name,
                    "label": emotion,
                    "confidence": confidence,
                }
            )

            # Visualization: detect landmarks and draw on image
            if self.visualize and self.visualization_dir is not None:
                try:
                    faces = self.face_app.get(image)
                    if faces:
                        # Use the first detected face in the cropped image
                        face = faces[0]
                        if hasattr(face, "kps") and face.kps is not None:
                            kps = face.kps.astype(int)
                            vis = image.copy()
                            for (x, y) in kps:
                                cv2.circle(vis, (int(x), int(y)), 2, (0, 255, 0), -1)

                            out_path = vis_dir / image_path.name
                            cv2.imwrite(str(out_path), vis)
                except Exception:
                    # Don't fail the whole run on visualization errors
                    pass

        df = pd.DataFrame(records)

        df.to_csv(
            self.annotation_file,
            index=False,
        )

        print(f"\nSaved {len(df)} predictions.")
        if self.visualize and self.visualization_dir is not None:
            print(f"Saved visualizations to {self.visualization_dir}")

        return len(df)