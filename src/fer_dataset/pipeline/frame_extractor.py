from pathlib import Path

import cv2
from tqdm import tqdm

from fer_dataset.pipeline.file_utils import clear_directory


class FrameExtractor:
    """
    Extract frames from a video at a configurable FPS.
    """

    def __init__(
        self,
        video_path: str,
        output_dir: str,
        fps: float = 2.0,
        debug: bool = False,
        max_frames: int = 100,
    ):
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.target_fps = fps
        self.debug = debug
        self.max_frames = max_frames

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def clear_outputs(self) -> None:
        """
        Remove previously extracted frames from output_dir.

        This is an explicit action, not a side effect of construction —
        call it before extract() if a clean output state is desired.
        """
        clear_directory(self.output_dir, "*.jpg")

    def extract(self) -> list[Path]:
        """
        Extract frames and return the saved frame paths.
        """

        cap = cv2.VideoCapture(str(self.video_path))

        if not cap.isOpened():
            raise FileNotFoundError(
                f"Cannot open video: {self.video_path}"
            )

        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        duration = total_frames / original_fps

        print(f"Video           : {self.video_path.name}")
        print(f"Duration        : {duration:.2f} sec")
        print(f"Original FPS    : {original_fps:.2f}")
        print(f"Target FPS      : {self.target_fps}")
        print(f"Total Frames    : {total_frames}")
        print("=" * 60)

        frame_interval = max(
            int(original_fps / self.target_fps),
            1,
        )

        saved_frames: list[Path] = []

        frame_index = 0
        saved_index = 0

        progress = tqdm(total=total_frames)

        while True:

            success, frame = cap.read()

            if not success:
                break

            if frame_index % frame_interval == 0:

                filename = f"frame_{saved_index:06d}.jpg"

                output_path = self.output_dir / filename

                cv2.imwrite(str(output_path), frame)

                saved_frames.append(output_path)

                saved_index += 1

                if self.debug and saved_index >= self.max_frames:
                    break

            frame_index += 1
            progress.update(1)

        progress.close()

        cap.release()

        print()
        print(f"Saved {len(saved_frames)} frames")

        return saved_frames