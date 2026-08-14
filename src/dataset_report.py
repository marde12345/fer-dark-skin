from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


class DatasetReport:
    def __init__(
        self,
        annotation_file: str,
        output_dir: str,
    ):
        self.annotation_file = Path(annotation_file)
        self.output_dir = Path(output_dir)

    def generate(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(self.annotation_file)

        self._plot_label_distribution(df)
        self._plot_confidence_histogram(df)
        self._plot_confidence_per_class(df)

        total_images = len(df)
        num_classes = df["label"].nunique()

        label_distribution = (
            df["label"]
            .value_counts()
            .rename_axis("Emotion")
            .reset_index(name="Count")
        )

        label_distribution["Percentage"] = (
            label_distribution["Count"] / total_images * 100
        ).round(2)

        confidence = df["confidence"]

        confidence_stats = {
            "Mean": confidence.mean(),
            "Median": confidence.median(),
            "Std": confidence.std(),
            "Min": confidence.min(),
            "Max": confidence.max(),
        }

        confidence_per_class = (
            df.groupby("label")["confidence"]
            .agg(["mean", "std"])
            .reset_index()
            .rename(
                columns={
                    "label": "Emotion",
                    "mean": "Mean Confidence",
                    "std": "Std",
                }
            )
        )

        report_path = self.output_dir / "dataset_report.md"

        with open(report_path, "w") as f:
            f.write("# FER Dataset Report\n\n")

            f.write("## 1. Dataset Information\n\n")
            f.write("| Property | Value |\n")
            f.write("|----------|-------|\n")
            f.write(f"| Generated Date | {datetime.now():%Y-%m-%d %H:%M:%S} |\n")
            f.write(f"| Total Images | {total_images:,} |\n")
            f.write(f"| Number of Classes | {num_classes} |\n\n")

            f.write("---\n\n")

            f.write("## 2. Emotion Distribution\n\n")
            f.write("| Emotion | Count | Percentage |\n")
            f.write("|---------|------:|-----------:|\n")

            for _, row in label_distribution.iterrows():
                f.write(
                    f"| {row['Emotion']} | "
                    f"{row['Count']:,} | "
                    f"{row['Percentage']:.2f}% |\n"
                )

            f.write("\n")

            f.write("> Visualization will be added in a future version.\n\n")

            f.write("---\n\n")

            f.write("## 3. Confidence Statistics\n\n")

            f.write("| Metric | Value |\n")
            f.write("|--------|------:|\n")

            for metric, value in confidence_stats.items():
                f.write(f"| {metric} | {value:.4f} |\n")

            f.write("\n")

            f.write("> Visualization will be added in a future version.\n\n")

            f.write("---\n\n")

            f.write("## 4. Confidence per Emotion\n\n")

            f.write("| Emotion | Mean Confidence | Std |\n")
            f.write("|---------|----------------:|----:|\n")

            for _, row in confidence_per_class.iterrows():
                f.write(
                    f"| {row['Emotion']} | "
                    f"{row['Mean Confidence']:.4f} | "
                    f"{row['Std']:.4f} |\n"
                )

            f.write("\n")

            f.write("> Visualization will be added in a future version.\n\n")

            f.write("---\n\n")

            largest = label_distribution.iloc[0]
            smallest = label_distribution.iloc[-1]

            f.write("## 5. Dataset Characteristics\n\n")

            f.write("| Characteristic | Value |\n")
            f.write("|---------------|-------|\n")
            f.write(f"| Total Images | {total_images:,} |\n")
            f.write(f"| Number of Classes | {num_classes} |\n")
            f.write(f"| Largest Class | {largest['Emotion']} |\n")
            f.write(f"| Smallest Class | {smallest['Emotion']} |\n")
            f.write(f"| Average Confidence | {confidence.mean():.4f} |\n\n")

            f.write("---\n\n")

            f.write("## 6. Annotation Format\n\n")

            f.write("| Column | Description |\n")
            f.write("|--------|-------------|\n")
            f.write("| filename | Image filename |\n")
            f.write("| label | Predicted emotion label |\n")
            f.write("| confidence | Softmax confidence score |\n\n")

            f.write("---\n\n")

            f.write("## 7. Limitations\n\n")

            f.write("- Emotion labels are generated automatically using a pretrained model.\n")
            f.write("- No manual verification has been performed.\n")
            f.write("- Dataset quality depends on face detection and emotion classification accuracy.\n")
            f.write("- Class distribution reflects the source video.\n\n")

            f.write("---\n\n")

            f.write("## 8. Conclusion\n\n")

            f.write(
                f"This dataset contains **{total_images:,}** facial images "
                f"covering **{num_classes}** emotion classes. "
                "The annotations were generated automatically using a "
                "pretrained facial emotion recognition model.\n"
            )

        print(f"Dataset report saved to {report_path}")

    def _plot_label_distribution(self, df: pd.DataFrame):
        output = self.output_dir / "assets"
        output.mkdir(parents=True, exist_ok=True)

        counts = df["label"].value_counts()

        plt.figure(figsize=(8, 5))
        counts.plot(kind="bar")

        plt.title("Emotion Distribution")
        plt.xlabel("Emotion")
        plt.ylabel("Number of Images")

        plt.tight_layout()
        plt.savefig(output / "label_distribution.png")
        plt.close()

    def _plot_confidence_histogram(self, df: pd.DataFrame):
        output = self.output_dir / "assets"
        output.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(8, 5))

        plt.hist(
            df["confidence"],
            bins=20,
        )

        plt.title("Confidence Distribution")
        plt.xlabel("Confidence")
        plt.ylabel("Frequency")

        plt.tight_layout()
        plt.savefig(output / "confidence_histogram.png")
        plt.close()

    def _plot_confidence_per_class(self, df: pd.DataFrame):
        output = self.output_dir / "assets"
        output.mkdir(parents=True, exist_ok=True)

        confidence = (
            df.groupby("label")["confidence"]
            .mean()
            .sort_values(ascending=False)
        )

        plt.figure(figsize=(8, 5))
        confidence.plot(kind="bar")

        plt.title("Mean Confidence per Emotion")
        plt.xlabel("Emotion")
        plt.ylabel("Mean Confidence")

        plt.tight_layout()
        plt.savefig(output / "confidence_per_class.png")
        plt.close()