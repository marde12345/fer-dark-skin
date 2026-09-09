
import cv2
import insightface

from pathlib import Path
from tqdm import tqdm
from fer_dataset.pipeline.file_utils import clear_directory


class FaceDetector:
    """
    Detect and crop faces using InsightFace (SCRFD).
    """

    def __init__(
        self,
        output_dir: str,
        det_size: tuple[int, int] = (640, 640),
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.app = insightface.app.FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],
        )

        self.app.prepare(
            ctx_id=0,
            det_size=det_size,
        )

    def clear_outputs(self) -> None:
        """
        Remove previously saved face crops from output_dir.

        This is an explicit action, not a side effect of construction —
        call it before detect() if a clean output state is desired.
        """
        clear_directory(self.output_dir, "*.jpg")

    def detect(self, frame_paths: list[Path]) -> None:
        """
        Detect faces from extracted frames.
        """

        saved = 0

        for frame_path in tqdm(frame_paths):

            image = cv2.imread(str(frame_path))

            if image is None:
                continue

            faces = self.app.get(image)

            stem = frame_path.stem

            for idx, face in enumerate(faces):

                x1, y1, x2, y2 = face.bbox.astype(int)

                padding = 0.2  # 20%

                width = x2 - x1
                height = y2 - y1

                x1 -= int(width * padding)
                y1 -= int(height * padding)
                x2 += int(width * padding)
                y2 += int(height * padding)

                # Pastikan tidak keluar dari ukuran gambar
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(image.shape[1], x2)
                y2 = min(image.shape[0], y2)

                crop = image[y1:y2, x1:x2]

                if crop.size == 0:
                    continue

                filename = f"{stem}_face{idx + 1:02d}.jpg"

                cv2.imwrite(
                    str(self.output_dir / filename),
                    crop,
                )

                saved += 1

        print(f"\nSaved {saved} face crops.")

        return saved