"""Step 4 for v2 pool: PROPOSAL-ONLY dedup/identity linkage between faces
in temporally-adjacent sampled frames, using ArcFace embeddings.

Reuses ArcFaceEmbedder / resolve_faces_to_embedding from
tools/extract_arcface_embeddings.py (same model loading pattern as
tools/papuan_v2/identity_pilot_arcface.py), applied to the FULL v2 QC'd
pool this time (not just a small pilot window), since this script's own
purpose IS the full-pool proposal.

Writes docs/reports/extraction_v2_2026-10-19/dedup_identity_proposal_v2.csv
with one row per adjacent-frame FACE PAIR, status in:
  LIKELY_DUPLICATE_ADJACENT  (sim >= MATCH_THRESHOLD)
  NEEDS_HUMAN_REVIEW         (AMBIGUOUS_BAND)
  NO_MATCH                   (below ambiguous band)
  TENTATIVE_MATCH is not used standalone here; LIKELY_DUPLICATE_ADJACENT
  IS the tentative-match-above-threshold case for adjacent frames, named
  per the task's requested vocabulary.

Never merges, never deletes, never writes a person_id other than
'unknown'/'needs_review' anywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.extract_arcface_embeddings import ArcFaceEmbedder, resolve_faces_to_embedding  # noqa: E402

MANIFEST = REPO / "docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv"
OUT_CSV = REPO / "docs/reports/extraction_v2_2026-10-19/dedup_identity_proposal_v2.csv"

MATCH_THRESHOLD = 0.5
AMBIGUOUS_BAND = (0.35, 0.5)


def cos_sim(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    df = pd.read_csv(MANIFEST)
    df = df.sort_values(["sampled_frame_index", "face_index_in_frame"]).reset_index(drop=True)
    print(f"pool size: {len(df)} faces across {df['sampled_frame_index'].nunique()} sampled frames")

    embedder = ArcFaceEmbedder()
    emb_cache: dict[str, np.ndarray | None] = {}
    status_cache: dict[str, str] = {}

    def get_emb(sample_id, path):
        if sample_id in emb_cache:
            return emb_cache[sample_id]
        img = cv2.imread(str(REPO / path))
        if img is None:
            emb_cache[sample_id] = None
            status_cache[sample_id] = "excluded_invalid_image"
            return None
        faces = embedder.app.get(img)
        status, emb = resolve_faces_to_embedding(faces)
        emb_cache[sample_id] = emb
        status_cache[sample_id] = status
        return emb

    rows = []
    by_frame = {idx: g for idx, g in df.groupby("sampled_frame_index")}
    frame_indices = sorted(by_frame.keys())

    counts = {"LIKELY_DUPLICATE_ADJACENT": 0, "NEEDS_HUMAN_REVIEW": 0, "NO_MATCH": 0, "EMBED_FAILED": 0}

    for i, fi in enumerate(frame_indices):
        cur = by_frame[fi]
        nxt_fi = fi + 1
        if nxt_fi not in by_frame:
            continue
        nxt = by_frame[nxt_fi]
        for _, r1 in cur.iterrows():
            e1 = get_emb(r1["sample_id"], r1["original_path"])
            for _, r2 in nxt.iterrows():
                e2 = get_emb(r2["sample_id"], r2["original_path"])
                if e1 is None or e2 is None:
                    status = "EMBED_FAILED"
                    sim = float("nan")
                else:
                    sim = cos_sim(e1, e2)
                    if sim >= MATCH_THRESHOLD:
                        status = "LIKELY_DUPLICATE_ADJACENT"
                    elif AMBIGUOUS_BAND[0] <= sim < AMBIGUOUS_BAND[1]:
                        status = "NEEDS_HUMAN_REVIEW"
                    else:
                        status = "NO_MATCH"
                counts[status] += 1
                rows.append({
                    "sample_id_a": r1["sample_id"], "sample_id_b": r2["sample_id"],
                    "sampled_frame_index_a": fi, "sampled_frame_index_b": nxt_fi,
                    "cosine_similarity": round(sim, 4) if sim == sim else "NaN",
                    "status": status,
                    "person_id_a": "unknown", "person_id_b": "unknown",
                })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(out)} pairs to {OUT_CSV}")
    print(counts)


if __name__ == "__main__":
    main()
