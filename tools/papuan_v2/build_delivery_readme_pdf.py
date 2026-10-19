"""Step 6: build 00_README.pdf for the final supervisor delivery package.
Uses reportlab (added as a project dependency for this deliverable).
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib import colors

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "delivery/papuan_v2_final_2026-10-19/00_README.pdf"

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Heading1"], spaceAfter=10)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14, spaceAfter=6)
small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#444444"))

story = []

story.append(Paragraph("Papuan V2 FER Dataset — Final Delivery Package", h1))
story.append(Paragraph("Generated: 2026-10-19", small))
story.append(Spacer(1, 6))

story.append(Paragraph("1. What this dataset is", h2))
story.append(Paragraph(
    "This package contains 231 face crops extracted from a single source video "
    "(<b>pesta_babi.mp4</b>), intended as a working facial-expression-recognition "
    "(FER) dataset for thesis research. Each sample is a cropped face image, "
    "available in two variants (a plain crop and a CLAHE-contrast-enhanced "
    "version), standardized to a fixed 224x224 pixel size. These 231 samples "
    "are the subset of 645 originally extracted crops that passed a basic "
    "quality-control filter (described in section 4).", body))

story.append(Paragraph("2. Folder guide", h2))
folder_rows = [
    ["Folder", "Contents"],
    ["02_Images/Original/", "231 standardized (224x224) plain face crops, one JPEG per sample."],
    ["02_Images/CLAHE/", "231 standardized (224x224) contrast-enhanced face crops, same geometry as Original."],
    ["03_Landmarks/Initial/", "231 JSON files: 42-point facial landmark predictions (AI-generated or reused), in standardized 224x224 coordinates."],
    ["03_Landmarks/Reviewed/", "26 JSON files: human-corrected 42-point landmarks for the subset that has been reviewed."],
    ["04_Manifests/", "CSV spreadsheets describing every sample (see section 3)."],
    ["05_Quality_Report/", "QC methodology, identity-pilot report, example contact sheets, and this package's LIMITATIONS.md."],
    ["00_README.pdf", "This document."],
    ["01_Dataset_Overview.xlsx", "Summary statistics and a plain-English data dictionary for every manifest column."],
]
t = Table(folder_rows, colWidths=[55*mm, 110*mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)

story.append(Paragraph("3. sample_id vs. person_id", h2))
story.append(Paragraph(
    "<b>sample_id</b> (e.g. <i>frame_000010_face02</i>) identifies one detected face "
    "crop: which sampled video frame it came from and which detection within that "
    "frame. It is a stable, reliable key for joining images, landmarks, and labels.", body))
story.append(Paragraph(
    "<b>person_id is NOT a reliable identity yet.</b> No cross-frame identity "
    "tracking has been run on this dataset at scale. Every sample defaults to "
    "person_id = <b>\"unknown\"</b>, meaning identity was never assessed. A small "
    "31-crop pilot test (covering only 5 consecutive sampled frames) tried "
    "matching faces across frames using AI face-embedding similarity; 11 of "
    "the 231 delivered samples were involved in a weak, unconfirmed match from "
    "that pilot and are marked person_id = <b>\"needs_review\"</b> instead. This is "
    "still not a confirmed identity — it only means a human should look at it. "
    "Two specific comparisons from that pilot were too ambiguous to call either "
    "way and are left explicitly unresolved. Do not use person_id for any "
    "identity-grouped analysis (e.g. train/test splits by person) without "
    "first running and validating a proper tracking/re-identification step.", body))

story.append(Paragraph("4. 42-point landmark schema", h2))
story.append(Paragraph(
    "Landmarks follow the standard 68-point facial landmark convention (as "
    "produced by the InsightFace landmark_3d_68 model), but only a 42-point "
    "subset relevant to expression is kept here, dropping the jaw outline and "
    "nose. Each point in the JSON files keeps its original 0-67 "
    "<i>source_index</i> so it can always be traced back to the full 68-point "
    "scheme.", body))
lm_rows = [
    ["Region", "Source indices (0-67)", "Count"],
    ["Right eyebrow", "17-21", "5"],
    ["Left eyebrow", "22-26", "5"],
    ["Right eye", "36-41", "6"],
    ["Left eye", "42-47", "6"],
    ["Mouth (outer + inner)", "48-67", "20"],
    ["Total", "", "42"],
]
t2 = Table(lm_rows, colWidths=[55*mm, 60*mm, 20*mm])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t2)
story.append(Paragraph(
    "Coordinates in this delivery are in <i>standardized 224x224 pixel space</i> "
    "(i.e. already transformed to match the Original/CLAHE images in "
    "02_Images/), not the original crop's native pixel space.", body))

story.append(Paragraph("5. Quality control (QC)", h2))
story.append(Paragraph(
    "Of 645 originally extracted face crops, 231 passed a basic quality "
    "filter: blur-variance (a sharpness measure) greater than 75, and a "
    "minimum crop dimension (width and height) of at least 60 pixels, plus "
    "requiring a successfully-generated CLAHE counterpart. These thresholds "
    "came from a small human-reviewed visual pilot, not a large validated "
    "classifier — see 05_Quality_Report/QC_THRESHOLD_RECOMMENDATION.md for "
    "the full methodology. The 414 excluded crops were too blurry or too "
    "small by this heuristic; they are not included in this package at all.", body))

story.append(Paragraph("6. Completion status (231 delivered samples)", h2))
status_rows = [
    ["Aspect", "Complete", "Pending"],
    ["Image standardization (both variants)", "231 / 231", "0"],
    ["Initial 42-point landmarks", "231 / 231", "0"],
    ["Human-reviewed landmarks", "26 / 231", "205"],
    ["Expression label (single annotator)", "52 / 231", "179"],
    ["person_id (validated identity tracking)", "0 / 231", "231 (by design, see section 3)"],
]
t3 = Table(status_rows, colWidths=[75*mm, 30*mm, 55*mm])
t3.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t3)

story.append(Paragraph("7. Explicit limitations", h2))
story.append(ListFlowable([
    ListItem(Paragraph("Face bounding boxes were never saved by the original detection pipeline — only the final cropped image. See 05_Quality_Report/LIMITATIONS.md item 1.", body)),
    ListItem(Paragraph("person_id is unvalidated at full-dataset scale; only a 31-crop pilot (5 frames) was tested. See section 3 and LIMITATIONS.md item 2.", body)),
    ListItem(Paragraph("That same pilot found 6 crops in its 31-crop subset that are not real faces (upstream detector false positives); only this subset has been checked, not the full 231 or 645. See LIMITATIONS.md item 3.", body)),
    ListItem(Paragraph("205 of 231 samples have only AI-predicted (not human-reviewed) landmarks. See LIMITATIONS.md item 4.", body)),
    ListItem(Paragraph("179 of 231 samples have no expression label yet, and all existing labels are single-annotator only (no cross-annotator verification exists anywhere in this project). See LIMITATIONS.md item 5.", body)),
    ListItem(Paragraph("The QC threshold used to select these 231 samples is pilot-derived, not a large-scale validated classifier. See LIMITATIONS.md item 6.", body)),
], bulletType="bullet"))

story.append(Paragraph("8. Full detail", h2))
story.append(Paragraph(
    "See 05_Quality_Report/LIMITATIONS.md for the complete, citation-linked "
    "version of every item above, and 04_Manifests/annotation_checklist.csv "
    "for a per-sample to-do list of exactly what remains (missing label, "
    "missing landmark review, identity needs review).", body))

doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                         leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
doc.build(story)
print("wrote", OUT)
