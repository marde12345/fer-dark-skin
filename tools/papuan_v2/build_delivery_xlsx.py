"""Step 6: build 01_Dataset_Overview.xlsx for the final delivery package."""
from pathlib import Path
import csv
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "delivery/papuan_v2_final_2026-10-19/04_Manifests/final_sample_manifest.csv"
OUT = REPO / "delivery/papuan_v2_final_2026-10-19/01_Dataset_Overview.xlsx"

rows = list(csv.DictReader(open(MANIFEST)))
n = len(rows)

summary = [
    ("Total delivered candidates", n),
    ("Source video", "pesta_babi (single video)"),
    ("QC blur-variance threshold", "> 75 (exclusive)"),
    ("QC min dimension threshold", ">= 60 px (width and height)"),
    ("Total crops originally extracted (pre-QC)", 645),
    ("Crops excluded by QC filter", 645 - n),
    ("Expression label complete", sum(1 for r in rows if r["expression_label_status"] == "complete")),
    ("Expression label pending", sum(1 for r in rows if r["expression_label_status"] == "pending_label")),
    ("Landmark review complete", sum(1 for r in rows if r["landmark_status"] == "complete")),
    ("Landmark review pending", sum(1 for r in rows if r["landmark_status"] == "pending_landmark_review")),
    ("Initial landmarks reused from prior runs", sum(1 for r in rows if r["landmark_initial_source"] == "reused")),
    ("Initial landmarks newly generated", sum(1 for r in rows if r["landmark_initial_source"] == "generated")),
    ("person_id = unknown", sum(1 for r in rows if r["person_id"] == "unknown")),
    ("person_id = needs_review", sum(1 for r in rows if r["person_id"] == "needs_review")),
    ("Image standardized size", "224 x 224 px, letterboxed, both variants"),
    ("Generation date", "2026-10-19"),
]
summary_df = pd.DataFrame(summary, columns=["Metric", "Value"])

data_dict = [
    ("sample_id", "Unique identifier for one face crop: sampled video frame + detection index within that frame."),
    ("source_video_id", "Name of the source video this sample was extracted from."),
    ("sampled_frame_index", "Index of the frame within the sampled (sub-sampled) frame sequence."),
    ("source_frame_index", "Index of the frame within the original, full-rate video."),
    ("frame_timestamp_seconds", "Timestamp (seconds) of the source frame in the original video."),
    ("face_index_in_frame", "Which detection this is within its frame (resets per frame, not a cross-frame identity)."),
    ("person_id", "'unknown' (never identity-assessed) or 'needs_review' (weak, unconfirmed pilot match). Never a verified identity. See README section 3."),
    ("identity_note", "Plain-English explanation of the person_id value and any identity-pilot flags for this sample."),
    ("qc_blur_variance", "Laplacian-variance blur/sharpness measure computed on the original crop; higher = sharper."),
    ("qc_width / qc_height", "Pixel dimensions of the original (pre-standardization) crop."),
    ("qc_status", "QC outcome for this sample. All rows here are APPROVED_QC_V1 (passed the frozen v1 QC filter)."),
    ("original_path / clahe_path", "Path to the original (un-standardized) source image in the repository."),
    ("standardized_original_path / standardized_clahe_path", "Path (relative to this delivery folder) to the 224x224 standardized image."),
    ("source_width / source_height", "Original crop dimensions before standardization (used to derive the letterbox transform)."),
    ("scale_factor", "Resize scale applied to reach 224px on the longer side, preserving aspect ratio."),
    ("pad_left / pad_top / pad_right / pad_bottom", "Black-letterbox padding (pixels) added to reach exactly 224x224, centered."),
    ("landmark_initial_path", "Path to this sample's 42-point AI-predicted landmark JSON (standardized coordinate space)."),
    ("landmark_initial_source", "'reused' = existing prior InsightFace prediction reused as-is; 'generated' = newly predicted for this delivery using the same model/method."),
    ("landmark_reviewed_path", "Path to this sample's human-reviewed 42-point landmark JSON, or NOT_AVAILABLE if not yet reviewed."),
    ("landmark_status", "'complete' = human-reviewed landmarks exist; 'pending_landmark_review' = AI-predicted only, not yet human-corrected."),
    ("expression_label", "Emotion label value (e.g. Neutral, Happy), or NOT_AVAILABLE if unlabeled."),
    ("expression_label_status", "'complete' = a single-annotator label exists; 'pending_label' = no label yet. Note: no sample in this project has two-annotator cross-verification yet -- see LIMITATIONS.md."),
    ("bbox_status", "Always 'NOT_AVAILABLE' -- the original face-detection bounding box was never persisted to disk by the extraction pipeline; only the cropped image was saved."),
]
dict_df = pd.DataFrame(data_dict, columns=["Column", "Plain-English meaning"])

with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    dict_df.to_excel(writer, sheet_name="Data Dictionary", index=False)

    for sheet_name, df in [("Summary", summary_df), ("Data Dictionary", dict_df)]:
        ws = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns, start=1):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = min(max_len, 90)

print("wrote", OUT)
