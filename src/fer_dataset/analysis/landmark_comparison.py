from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


FEATURES = [
    "brow_lowering_distance",
    "lip_corner_distance",
    "mouth_openness",
    "inter_ocular_distance",
]


class LandmarkComparison:
    """
    Compare landmark-based geometry distributions across emotion and skin-tone groups.
    """

    def __init__(
        self,
        feature_file: str,
        report_dir: str = "reports",
    ):
        self.feature_file = Path(feature_file)
        self.report_dir = Path(report_dir)
        self.assets_dir = self.report_dir / "assets"

        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def _summary_stats(
        self,
        df: pd.DataFrame,
        group_name: str,
    ) -> pd.DataFrame:
        rows: list[dict[str, object]] = []

        for feature in FEATURES:
            if feature not in df.columns:
                continue

            values = df[feature].dropna()
            rows.append(
                {
                    "group": group_name,
                    "feature": feature,
                    "count": int(values.count()),
                    "mean": float(values.mean()) if not values.empty else float("nan"),
                    "median": float(values.median()) if not values.empty else float("nan"),
                    "std": float(values.std()) if not values.empty else float("nan"),
                }
            )

        return pd.DataFrame(rows)

    def _plot_angry_vs_neutral(self, df: pd.DataFrame) -> None:
        subset = df[df["label"].isin(["Anger", "Angry", "Neutral"])].copy()

        subset["label_group"] = subset["label"].replace({"Anger": "Angry"})

        for feature in FEATURES:
            if feature not in subset.columns:
                continue

            plot_df = subset[["label_group", feature]].dropna()
            if plot_df.empty:
                continue

            plt.figure(figsize=(8, 5))
            plot_df.boxplot(column=feature, by="label_group")
            plt.title(f"{feature}: Angry vs Neutral")
            plt.suptitle("")
            plt.xlabel("Predicted Label")
            plt.ylabel(feature)
            plt.tight_layout()
            out_path = self.assets_dir / f"landmark_angry_vs_neutral_{feature}.png"
            plt.savefig(out_path, dpi=150)
            plt.close()

    def _plot_skin_tone_within_label(self, df: pd.DataFrame) -> None:
        if "skin_tone" not in df.columns:
            return

        normalized = df.copy()
        normalized["skin_group"] = normalized["skin_tone"].astype(str).str.strip().str.lower()
        normalized["skin_group"] = normalized["skin_group"].replace(
            {
                "dark": "Dark",
                "light": "Light/Medium",
                "medium": "Light/Medium",
                "light/medium": "Light/Medium",
            }
        )

        normalized = normalized[normalized["skin_group"].isin(["Dark", "Light/Medium"])]

        for label in sorted(normalized["label"].dropna().unique()):
            label_df = normalized[normalized["label"] == label]
            if label_df.empty:
                continue

            for feature in FEATURES:
                if feature not in label_df.columns:
                    continue

                plot_df = label_df[["skin_group", feature]].dropna()
                if plot_df.empty:
                    continue

                plt.figure(figsize=(8, 5))
                plot_df.boxplot(column=feature, by="skin_group")
                plt.title(f"{feature}: {label} by Skin Tone")
                plt.suptitle("")
                plt.xlabel("Skin Tone Group")
                plt.ylabel(feature)
                plt.tight_layout()
                out_path = self.assets_dir / f"landmark_{label.lower()}_skin_{feature}.png"
                plt.savefig(out_path, dpi=150)
                plt.close()

    def run(self) -> pd.DataFrame:
        if not self.feature_file.exists():
            raise FileNotFoundError(f"Feature file not found: {self.feature_file}")

        df = pd.read_csv(self.feature_file)

        required = {"label", "skin_tone"}
        missing = required.difference(df.columns)
        if missing:
            for col in missing:
                df[col] = "Unknown"

        angry = df[df["label"].isin(["Anger", "Angry"])].copy()
        neutral = df[df["label"] == "Neutral"].copy()

        summary_parts = [
            self._summary_stats(angry, "Angry"),
            self._summary_stats(neutral, "Neutral"),
        ]

        normalized = df.copy()
        normalized["skin_group"] = normalized["skin_tone"].astype(str).str.strip().str.lower()
        normalized["skin_group"] = normalized["skin_group"].replace(
            {
                "dark": "Dark",
                "light": "Light/Medium",
                "medium": "Light/Medium",
                "light/medium": "Light/Medium",
            }
        )

        label_values = sorted(normalized["label"].dropna().unique())
        for label in label_values:
            per_label = normalized[normalized["label"] == label]
            dark = per_label[per_label["skin_group"] == "Dark"]
            light_medium = per_label[per_label["skin_group"] == "Light/Medium"]

            if not dark.empty:
                summary_parts.append(self._summary_stats(dark, f"{label}|Dark"))
            if not light_medium.empty:
                summary_parts.append(
                    self._summary_stats(light_medium, f"{label}|Light/Medium")
                )

        summary = pd.concat(summary_parts, ignore_index=True)

        summary_path = self.report_dir / "landmark_comparison_summary.csv"
        summary.to_csv(summary_path, index=False)

        self._plot_angry_vs_neutral(df)
        self._plot_skin_tone_within_label(df)

        print("Landmark comparison summary:")
        print(summary.to_string(index=False))
        print(f"Saved summary table to {summary_path}")
        print(f"Saved comparison plots to {self.assets_dir}")

        return summary


if __name__ == "__main__":
    comparator = LandmarkComparison(
        feature_file="data/intermediate/landmark_features.csv",
        report_dir="reports",
    )
    comparator.run()
