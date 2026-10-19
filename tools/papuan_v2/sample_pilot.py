"""EXP-PAP-002 (part 1): reproducible pilot-set sampling.

Samples a fixed-size, seeded subset of data/papuan_v2/faces/ (the EXP-PAP-001
output) for the pilot annotation/evaluation workflow
(docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md §10a). Copies each sampled
image's CLAHE version (never the un-preprocessed crop) into
data/papuan_v2/pilot/images/, since the supervisor's requirement is that
AI-assisted annotation input must be CLAHE-preprocessed.

Reproducibility: sampling is `random.Random(seed).sample()` over the
lexicographically sorted list of available face filenames (a stable,
deterministic ordering -- not directory-iteration order, which is not
guaranteed stable across filesystems). Re-running this script with the
same seed against the same faces/ directory reproduces an identical
pilot set.

This script never writes to human_labels.csv or any AI-prediction file --
it only establishes WHICH images are in the pilot and copies their pixel
data, per the "pilot membership is reproducible" and "AI predictions
never modify human ground truth" constraints in the approved proposal.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PAPUAN_V2_DIR = REPO_ROOT / "data" / "papuan_v2"
DEFAULT_SAMPLE_SIZE = 150
DEFAULT_SEED = 42


def _relpath(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sample_pilot(
    faces_dir: Path,
    clahe_dir: Path,
    pilot_images_dir: Path,
    manifest_path: Path,
    sample_size: int,
    seed: int,
) -> list[dict]:
    face_files = sorted(p.name for p in faces_dir.glob("*.jpg"))
    if not face_files:
        raise RuntimeError(f"No face crops found in {faces_dir} -- run build_pilot_source.py first.")

    n = min(sample_size, len(face_files))
    rng = random.Random(seed)
    sampled = sorted(rng.sample(face_files, n))

    pilot_images_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    missing_clahe = 0
    for filename in sampled:
        clahe_src = clahe_dir / filename
        if not clahe_src.exists():
            missing_clahe += 1
            continue
        dest = pilot_images_dir / filename
        shutil.copy2(clahe_src, dest)
        rows.append(
            {
                "image_id": Path(filename).stem,
                "face_filename": filename,
                "source_face_path": _relpath(faces_dir / filename),
                "source_clahe_path": _relpath(clahe_src),
                "pilot_image_path": _relpath(dest),
                "sample_seed": seed,
                "sampled_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    if missing_clahe:
        print(f"WARNING: {missing_clahe} sampled filenames had no matching CLAHE file and were skipped.")

    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_id",
                "face_filename",
                "source_face_path",
                "source_clahe_path",
                "pilot_image_path",
                "sample_seed",
                "sampled_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Sampled {len(rows)} pilot images (seed={seed}) -> {pilot_images_dir}")
    print(f"Manifest written to {manifest_path}")
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--faces-dir", type=Path, default=PAPUAN_V2_DIR / "faces")
    parser.add_argument("--clahe-dir", type=Path, default=PAPUAN_V2_DIR / "clahe")
    parser.add_argument("--pilot-images-dir", type=Path, default=PAPUAN_V2_DIR / "pilot" / "images")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "experiments" / "EXP-PAP-004" / "pilot_manifest.csv",
    )
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    sample_pilot(
        faces_dir=args.faces_dir,
        clahe_dir=args.clahe_dir,
        pilot_images_dir=args.pilot_images_dir,
        manifest_path=args.manifest,
        sample_size=args.sample_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
