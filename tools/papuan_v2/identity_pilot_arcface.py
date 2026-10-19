"""Small-scope identity-tracking PILOT for papuan_v2 (2026-10-19).

Context / deviation from the original proposal
------------------------------------------------
docs/reports/review_package_2026-10-19/IDENTITY_TRACKING_NEXT_STEP.md
proposed comparing a cheap bbox-based centroid/IoU tracker against ArcFace
embedding similarity on a small window of frames. That comparison is NOT
possible here: `bbox_x/y/w/h` are `NOT_AVAILABLE` for all 645 rows in
per_face_sample_manifest.csv (re-verified directly, not assumed, before
writing this script). Without a persisted bounding box, there is no
frame-to-frame spatial position to track. The only viable pilot signal
with the artifacts that actually exist is ArcFace embedding similarity
between face crops in temporally-adjacent sampled frames. This script
implements ONLY that half of the original proposal.

This script does NOT assign person_id anywhere. It produces a separate,
clearly-labeled pilot output with `pilot_cluster_id` (prefixed
`PILOT_CLUSTER_`) and status flags, for human review only.

Reuses tools/extract_arcface_embeddings.py's ArcFaceEmbedder (same
buffalo_l/w600k_r50 model, same loading approach) rather than
re-implementing model loading, but is run only on this pilot's small
subset of face crop files -- not the full 645-crop dataset.
"""
from __future__ import annotations

import csv
import sys
from itertools import combinations
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.extract_arcface_embeddings import ArcFaceEmbedder, resolve_faces_to_embedding  # noqa: E402

MANIFEST = REPO_ROOT / "docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv"
OUT_DIR = REPO_ROOT / "docs/reports/identity_pilot_2026-10-19"
FRAME_MIN = 8
FRAME_MAX = 12
SIM_THRESHOLD_MATCH = 0.5
SIM_AMBIGUOUS_BAND = (0.35, 0.5)  # below threshold but close enough to flag for review


def main() -> None:
    df = pd.read_csv(MANIFEST)
    sub = df[(df["sampled_frame_index"] >= FRAME_MIN) & (df["sampled_frame_index"] <= FRAME_MAX)].copy()
    sub = sub.sort_values(["sampled_frame_index", "face_index_in_frame"]).reset_index(drop=True)

    print(f"Pilot subset: sampled_frame_index in [{FRAME_MIN}, {FRAME_MAX}] -> {len(sub)} face crops "
          f"across {sub['sampled_frame_index'].nunique()} consecutive sampled frames")

    embedder = ArcFaceEmbedder()
    embeddings: dict[str, np.ndarray | None] = {}
    statuses: dict[str, str] = {}

    for _, row in sub.iterrows():
        sample_id = row["sample_id"]
        path = REPO_ROOT / row["original_path"]
        image = cv2.imread(str(path))
        if image is None:
            statuses[sample_id] = "excluded_invalid_image"
            embeddings[sample_id] = None
            continue
        faces = embedder.app.get(image)
        status, emb = resolve_faces_to_embedding(faces)
        statuses[sample_id] = status
        embeddings[sample_id] = emb

    for sid, st in statuses.items():
        print(f"  {sid}: {st}")

    # Compare every pair of crops that sit in temporally-adjacent frames
    # (sampled_frame_index differs by exactly 1), or the same frame (two
    # different detections in one frame -- always a NO_MATCH by construction
    # since they are different face_index_in_frame detections already known
    # to be distinct people/detections per the manifest's own documentation).
    frame_of = dict(zip(sub["sample_id"], sub["sampled_frame_index"]))
    sample_ids = list(sub["sample_id"])

    results = []
    sims_observed = []

    for sid_a, sid_b in combinations(sample_ids, 2):
        fa, fb = frame_of[sid_a], frame_of[sid_b]
        if abs(fa - fb) != 1:
            continue  # only adjacent-frame pairs are candidate identity links
        emb_a, emb_b = embeddings.get(sid_a), embeddings.get(sid_b)
        if emb_a is None or emb_b is None:
            results.append({
                "sample_id": sid_a,
                "sampled_frame_index": fa,
                "pilot_cluster_id": "",
                "match_confidence": "",
                "matched_against_sample_id": sid_b,
                "similarity_score": "",
                "status": "NO_MATCH_FOUND",
            })
            continue
        sim = float(np.dot(emb_a, emb_b))  # both are L2-normalized -> dot == cosine similarity
        sims_observed.append(sim)
        if sim >= SIM_THRESHOLD_MATCH:
            status = "TENTATIVE_MATCH"
            conf = "high" if sim >= 0.65 else "moderate"
        elif SIM_AMBIGUOUS_BAND[0] <= sim < SIM_AMBIGUOUS_BAND[1]:
            status = "NEEDS_HUMAN_REVIEW"
            conf = "ambiguous"
        else:
            status = "NO_MATCH_FOUND"
            conf = "low"
        results.append({
            "sample_id": sid_a,
            "sampled_frame_index": fa,
            "pilot_cluster_id": "",
            "match_confidence": conf,
            "matched_against_sample_id": sid_b,
            "similarity_score": round(sim, 4),
            "status": status,
        })

    # Assign tentative pilot cluster ids via union-find over TENTATIVE_MATCH edges only.
    parent = {sid: sid for sid in sample_ids}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for r in results:
        if r["status"] == "TENTATIVE_MATCH":
            union(r["sample_id"], r["matched_against_sample_id"])

    cluster_label = {}
    next_cluster_num = 1
    for sid in sample_ids:
        root = find(sid)
        if root not in cluster_label:
            cluster_label[root] = f"PILOT_CLUSTER_{next_cluster_num:02d}"
            next_cluster_num += 1

    for r in results:
        r["pilot_cluster_id"] = cluster_label[find(r["sample_id"])]

    # Also emit a row for every sample_id with no adjacent-frame pair at all
    # (e.g. first/last frame in window with no match), so every pilot
    # sample_id appears at least once in the output.
    covered = {r["sample_id"] for r in results}
    for sid in sample_ids:
        if sid not in covered:
            results.append({
                "sample_id": sid,
                "sampled_frame_index": frame_of[sid],
                "pilot_cluster_id": cluster_label[find(sid)],
                "match_confidence": "",
                "matched_against_sample_id": "",
                "similarity_score": "",
                "status": "NO_MATCH_FOUND",
            })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "identity_pilot_results.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sample_id", "sampled_frame_index", "pilot_cluster_id", "match_confidence",
            "matched_against_sample_id", "similarity_score", "status",
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    n_tentative = sum(1 for r in results if r["status"] == "TENTATIVE_MATCH")
    n_review = sum(1 for r in results if r["status"] == "NEEDS_HUMAN_REVIEW")
    n_nomatch = sum(1 for r in results if r["status"] == "NO_MATCH_FOUND")

    print(f"\nAdjacent-frame pairwise comparisons: {len(results)}")
    print(f"  TENTATIVE_MATCH: {n_tentative}")
    print(f"  NEEDS_HUMAN_REVIEW: {n_review}")
    print(f"  NO_MATCH_FOUND: {n_nomatch}")
    if sims_observed:
        arr = np.array(sims_observed)
        print(f"\nSimilarity score distribution (n={len(arr)}): "
              f"min={arr.min():.4f} max={arr.max():.4f} mean={arr.mean():.4f} "
              f"median={np.median(arr):.4f}")
        print("Percentiles:", {p: round(float(np.percentile(arr, p)), 4) for p in (5, 25, 50, 75, 95)})
    print(f"\nWrote {out_csv}")


if __name__ == "__main__":
    main()
