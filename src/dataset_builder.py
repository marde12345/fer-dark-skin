import shutil
import pandas as pd

from tqdm import tqdm
from pathlib import Path
from file_utils import clear_directory


class DatasetBuilder:
    """
    Build the final FER dataset.
    """

    def __init__(
        self,
        input_dir: str,
        annotation_file: str,
        output_dir: str,
    ):
        self.input_dir = Path(input_dir)
        self.annotation_file = Path(annotation_file)
        self.output_dir = Path(output_dir)

        self.image_dir = self.output_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)

        clear_directory(self.output_dir, "*.jpg")
        if self.annotation_file.exists():
            self.annotation_file.unlink()

    def build(self) -> None:

        df = pd.read_csv(self.annotation_file)

        records = []

        for idx, row in tqdm(df.iterrows(), total=len(df)):

            source = self.input_dir / row["filename"]

            if not source.exists():
                continue

            filename = f"img_{idx + 1:06d}.jpg"

            destination = self.image_dir / filename

            shutil.copy2(source, destination)

            records.append(
                {
                    "filename": filename,
                    "label": row["label"],
                    "confidence": row["confidence"],
                }
            )

        pd.DataFrame(records).to_csv(
            self.output_dir / "annotations.csv",
            index=False,
        )

        print(f"\nDataset created with {len(records)} images.")

        return len(records)