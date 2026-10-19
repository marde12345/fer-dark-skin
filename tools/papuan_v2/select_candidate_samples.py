"""Select candidate annotation samples from per_face_sample_manifest.csv by a
parameterized QC threshold (blur_variance minimum, min-dimension minimum).

This produces a CANDIDATE list, not an approved/final set. No threshold is
hardcoded as "the" answer here -- pass whichever threshold has been chosen
(e.g. from docs/reports/qc_pilot_2026-10-19/QC_THRESHOLD_RECOMMENDATION.md)
via CLI flags. Defaults match that doc's recommended-but-NOT-approved
candidate purely for convenience; override them explicitly for any other run.

Usage:
    uv run python3 tools/papuan_v2/select_candidate_samples.py \
        --manifest docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv \
        --out docs/reports/qc_pilot_2026-10-19/candidate_samples.csv \
        --min-blur-variance 75 \
        --min-dimension 60

Filters applied:
    1. qc_blur_variance > --min-blur-variance
    2. min(qc_width, qc_height) >= --min-dimension
    3. has_clahe == True (original/CLAHE pair must exist)

Known limitation (deliberately NOT implemented here): adjacent-frame
near-duplicate deprioritization. person_id is NOT_AVAILABLE dataset-wide and
there is no tracking/identity linkage, so there is no reliable way to tell
whether the same physical face reappears in consecutive sampled frames vs.
two different people captured in nearby frames. Faces with the same
sampled_frame_index but different face_index_in_frame are different
detections within one frame (different people, or multiple detections of the
same person), NOT redundant samples -- they are never filtered here. This
script does not drop any row on a "likely duplicate" guess. See
CANDIDATE_SELECTION_PLAN.md for a conservative, clearly-labeled adjacency
note that is informational only and never used as a hard filter.
"""
import argparse
import sys
import pandas as pd


def select_candidates(manifest_path: str, min_blur_variance: float, min_dimension: float) -> pd.DataFrame:
    df = pd.read_csv(manifest_path)
    required_cols = {"qc_blur_variance", "qc_width", "qc_height", "has_clahe"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"manifest missing required columns: {missing}")

    min_dim = df[["qc_width", "qc_height"]].min(axis=1)
    mask = (
        (df["qc_blur_variance"] > min_blur_variance)
        & (min_dim >= min_dimension)
        & (df["has_clahe"] == True)  # noqa: E712
    )
    out = df[mask].copy()
    out.insert(0, "candidate_status", "CANDIDATE_PENDING_QC_THRESHOLD_APPROVAL")
    out["candidate_min_blur_variance_threshold"] = min_blur_variance
    out["candidate_min_dimension_threshold"] = min_dimension
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="Path to per_face_sample_manifest.csv")
    ap.add_argument("--out", required=True, help="Path to write candidate_samples.csv")
    ap.add_argument("--min-blur-variance", type=float, required=True,
                     help="Minimum qc_blur_variance (Laplacian variance), exclusive")
    ap.add_argument("--min-dimension", type=float, required=True,
                     help="Minimum min(qc_width, qc_height) in pixels, inclusive")
    args = ap.parse_args()

    out = select_candidates(args.manifest, args.min_blur_variance, args.min_dimension)
    out.to_csv(args.out, index=False)

    total = len(pd.read_csv(args.manifest))
    print(f"CANDIDATE (pending QC threshold approval) selection:")
    print(f"  manifest total samples: {total}")
    print(f"  threshold: qc_blur_variance > {args.min_blur_variance}, "
          f"min(width,height) >= {args.min_dimension}")
    print(f"  retained: {len(out)} ({100*len(out)/total:.1f}%)")
    print(f"  written to: {args.out}")
    print("  NOTE: this is a candidate list only, not an approved/final QC-passed set.")


if __name__ == "__main__":
    sys.exit(main())
