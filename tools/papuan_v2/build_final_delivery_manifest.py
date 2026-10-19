"""Step 3+4: identity handling + final manifest assembly for the delivery package.

Builds:
- delivery/papuan_v2_final_2026-10-19/04_Manifests/final_sample_manifest.csv (231 rows)
- delivery/papuan_v2_final_2026-10-19/04_Manifests/annotation_checklist.csv (231 rows)
- copies frame_level_extraction_manifest.csv as-is

Identity policy (per task brief, no new tracking run):
- Default person_id = "unknown" for all 231.
- TENTATIVE_MATCH-involved sample_ids (either side of the pair, from the
  13 TENTATIVE_MATCH rows in identity_pilot_results.csv) -> person_id =
  "needs_review", with an explanatory identity_note.
- NEEDS_HUMAN_REVIEW pairs (2 pairs, 4 sample_ids) stay "unknown" for
  person_id (never silently upgraded to a confident match) but get an
  identity_note flagging the specific unresolved comparison.
- Non-face detections identified in the pilot report (named explicitly:
  frame_000008_face03, frame_000009_face03, frame_000010_face06,
  frame_000010_face07, frame_000011_face07 -- a 6th crop is mentioned in
  the pilot report's prose but not individually named/traceable in the
  pilot CSV, so it cannot be honestly flagged by sample_id here) that fall
  within the 231 get person_id="unknown" + identity_note flagging a likely
  non-face detection. They are NOT excluded from QC (that was already
  decided by the frozen blur/size threshold).
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / "docs/reports/frozen_candidate_v1_2026-10-19/frozen_candidate_manifest.csv"
TRANSFORM_CSV = REPO / "delivery/papuan_v2_final_2026-10-19/04_Manifests/_standardization_transform.csv"
IDENTITY_PILOT = REPO / "docs/reports/identity_pilot_2026-10-19/identity_pilot_results.csv"
FRAME_LEVEL = REPO / "docs/reports/extraction_audit_2026-10-19/frame_level_extraction_manifest.csv"

OUT_DIR = REPO / "delivery/papuan_v2_final_2026-10-19"
MANIFEST_DIR = OUT_DIR / "04_Manifests"
INITIAL_DIR = OUT_DIR / "03_Landmarks" / "Initial"
REVIEWED_DIR = OUT_DIR / "03_Landmarks" / "Reviewed"

NON_FACE_NAMED = {
    "frame_000008_face03", "frame_000009_face03", "frame_000010_face06",
    "frame_000010_face07", "frame_000011_face07",
}


def load_identity_flags():
    rows = list(csv.DictReader(open(IDENTITY_PILOT)))
    tentative_sids = set()
    for r in rows:
        if r["status"] == "TENTATIVE_MATCH":
            tentative_sids.add(r["sample_id"])
            tentative_sids.add(r["matched_against_sample_id"])

    needs_review_pairs = []  # list of (sid, matched_against)
    for r in rows:
        if r["status"] == "NEEDS_HUMAN_REVIEW":
            needs_review_pairs.append((r["sample_id"], r["matched_against_sample_id"], r["similarity_score"]))

    needs_review_sids = {}
    for sid, matched, score in needs_review_pairs:
        needs_review_sids.setdefault(sid, []).append((matched, score))
        needs_review_sids.setdefault(matched, []).append((sid, score))

    return tentative_sids, needs_review_sids


def main():
    frozen_rows = list(csv.DictReader(open(FROZEN)))
    assert len(frozen_rows) == 231
    transforms = {t["sample_id"]: t for t in csv.DictReader(open(TRANSFORM_CSV))}
    assert len(transforms) == 231

    tentative_sids, needs_review_sids = load_identity_flags()

    frozen_ids = {r["sample_id"] for r in frozen_rows}
    non_face_in_scope = NON_FACE_NAMED & frozen_ids
    tentative_in_scope = tentative_sids & frozen_ids

    final_rows = []
    checklist_rows = []

    for row in frozen_rows:
        sid = row["sample_id"]
        t = transforms[sid]

        # --- identity ---
        person_id = "unknown"
        notes = []
        if sid in tentative_in_scope:
            person_id = "needs_review"
            notes.append("tentative embedding match from 31-crop pilot (threshold=0.5), "
                         "NOT validated for full-dataset use, pending human confirmation")
        if sid in needs_review_sids:
            pairs_str = "; ".join(f"ambiguous vs {m} (similarity={s})" for m, s in needs_review_sids[sid])
            notes.append(f"UNRESOLVED identity comparison from 31-crop pilot: {pairs_str} "
                         f"(0.35-0.5 similarity band, flagged NEEDS_HUMAN_REVIEW, no human reviewer "
                         f"available at delivery time -- explicitly left unresolved, not converted to a match)")
        if sid in non_face_in_scope:
            notes.append("likely non-face detection (pilot subset only): InsightFace re-detection found "
                         "no face in this crop during the 31-crop identity pilot; upstream detector false "
                         "positive, not re-verified dataset-wide; not excluded from QC")
        identity_note = " | ".join(notes) if notes else "NOT_ASSESSED — outside 31-crop identity pilot scope"

        # --- landmarks ---
        landmark_initial_path_delivery = f"03_Landmarks/Initial/{sid}.json"
        assert (INITIAL_DIR / f"{sid}.json").exists(), f"missing initial landmark json for {sid}"
        landmark_initial_source = "reused" if row["landmark_initial_path"] != "NOT_AVAILABLE" else "generated"

        reviewed_file = REVIEWED_DIR / f"{sid}.json"
        if reviewed_file.exists():
            landmark_reviewed_path_delivery = f"03_Landmarks/Reviewed/{sid}.json"
            landmark_status = "complete"
        else:
            landmark_reviewed_path_delivery = "NOT_AVAILABLE"
            landmark_status = "pending_landmark_review"

        # --- expression label ---
        if row["expression_label"] != "NOT_AVAILABLE" and row["expression_label_status"] == "labeled_single_annotator":
            expression_label = row["expression_label"]
            # "complete" here means a single-annotator label exists (this
            # dataset's labeling track has never completed cross-annotator
            # verification for ANY sample project-wide -- Annotator B has 0
            # completions dataset-wide, see PAPUAN_V2_STANDARDIZATION_AUDIT.
            # This single-annotator caveat is called out explicitly in
            # LIMITATIONS.md; "complete" is not a claim of inter-annotator agreement.)
            expression_label_status = "complete"
        else:
            expression_label = "NOT_AVAILABLE"
            expression_label_status = "pending_label"

        missing_expression_label = expression_label == "NOT_AVAILABLE"
        missing_landmark_review = landmark_status != "complete"
        identity_needs_review = (sid in tentative_in_scope) or (sid in needs_review_sids)

        other_notes_parts = []
        if sid in non_face_in_scope:
            other_notes_parts.append("flagged possible non-face detection in identity pilot")
        other_notes = "; ".join(other_notes_parts) if other_notes_parts else ""

        final_rows.append({
            "sample_id": sid,
            "source_video_id": row["source_video_id"],
            "sampled_frame_index": row["sampled_frame_index"],
            "source_frame_index": row["source_frame_index"],
            "frame_timestamp_seconds": row["frame_timestamp_seconds"],
            "face_index_in_frame": row["face_index_in_frame"],
            "person_id": person_id,
            "identity_note": identity_note,
            "qc_blur_variance": row["qc_blur_variance"],
            "qc_width": row["qc_width"],
            "qc_height": row["qc_height"],
            "qc_status": "APPROVED_QC_V1",
            "original_path": f"data/papuan_v2/faces/{sid}.jpg",
            "clahe_path": f"data/papuan_v2/clahe/{sid}.jpg",
            "standardized_original_path": f"02_Images/Original/{sid}.jpg",
            "standardized_clahe_path": f"02_Images/CLAHE/{sid}.jpg",
            "source_width": t["source_width"],
            "source_height": t["source_height"],
            "scale_factor": t["scale_factor"],
            "pad_left": t["pad_left"],
            "pad_top": t["pad_top"],
            "pad_right": t["pad_right"],
            "pad_bottom": t["pad_bottom"],
            "landmark_initial_path": landmark_initial_path_delivery,
            "landmark_initial_source": landmark_initial_source,
            "landmark_reviewed_path": landmark_reviewed_path_delivery,
            "landmark_status": landmark_status,
            "expression_label": expression_label,
            "expression_label_status": expression_label_status,
            "bbox_status": "NOT_AVAILABLE — not historically persisted, see methodology report",
        })

        checklist_rows.append({
            "sample_id": sid,
            "missing_expression_label": missing_expression_label,
            "missing_landmark_review": missing_landmark_review,
            "identity_needs_review": identity_needs_review,
            "other_notes": other_notes,
        })

    fieldnames = list(final_rows[0].keys())
    with open(MANIFEST_DIR / "final_sample_manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(final_rows)

    with open(MANIFEST_DIR / "annotation_checklist.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "missing_expression_label", "missing_landmark_review",
                                           "identity_needs_review", "other_notes"])
        w.writeheader()
        w.writerows(checklist_rows)

    # Copy frame_level_extraction_manifest.csv as-is
    import shutil
    shutil.copy(FRAME_LEVEL, MANIFEST_DIR / "frame_level_extraction_manifest.csv")

    print("final_sample_manifest.csv rows:", len(final_rows))
    print("annotation_checklist.csv rows:", len(checklist_rows))
    print("person_id=unknown:", sum(1 for r in final_rows if r["person_id"] == "unknown"))
    print("person_id=needs_review:", sum(1 for r in final_rows if r["person_id"] == "needs_review"))
    print("missing_expression_label:", sum(1 for r in checklist_rows if r["missing_expression_label"]))
    print("missing_landmark_review:", sum(1 for r in checklist_rows if r["missing_landmark_review"]))
    print("identity_needs_review:", sum(1 for r in checklist_rows if r["identity_needs_review"]))
    print("landmark_initial_source=reused:", sum(1 for r in final_rows if r["landmark_initial_source"] == "reused"))
    print("landmark_initial_source=generated:", sum(1 for r in final_rows if r["landmark_initial_source"] == "generated"))


if __name__ == "__main__":
    main()
