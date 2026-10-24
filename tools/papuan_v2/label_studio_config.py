"""Shared, importable configuration for the EXP-PAP-004 Label Studio pilot
annotation project. No network calls here -- pure constants and pure
functions, so they can be unit-tested without a live Label Studio server
(per the approved scope: "Do NOT add tests that require a live Label
Studio server unless the repository already has an established
integration-test pattern" -- it doesn't, so everything importable here
must be server-free).

Independence constraint (approved proposal): the label config below must
NEVER expose any AI-derived information -- no HSEmotion/ArcFace
prediction, no model name, no model confidence. Only the seven
expression classes, an optional human-confidence field, and instructions
telling the annotator not to reference any model prediction.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PILOT_MANIFEST_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "pilot_manifest.csv"
PILOT_IMAGES_DIR = REPO_ROOT / "data" / "papuan_v2" / "pilot" / "images"
ANNOTATOR_ASSIGNMENT_PATH = REPO_ROOT / "experiments" / "EXP-PAP-004" / "annotator_assignment.csv"

PROJECT_TITLE = "EXP-PAP-004 Papuan V2 Pilot (Blind)"  # Label Studio caps project titles at 50 chars
PROJECT_TITLE_B = "EXP-PAP-004 Overlap (Annotator B)"  # separate project/server, see README
LABELING_CONFIG_VERSION = "v1"

# Deterministic overlap-subset sampling for a second annotator (Annotator
# B). Distinct seed from sample_pilot.py's pilot-from-faces sampling
# (seed=42) -- this samples WITHIN the already-fixed 150-image pilot, a
# different sampling problem, so a different seed avoids any appearance
# of reusing/deriving one from the other.
ANNOTATOR_B_OVERLAP_SEED = 100
ANNOTATOR_B_OVERLAP_SIZE = 75

ANNOTATOR_ASSIGNMENT_FIELDNAMES = ["image_id", "annotator_A", "annotator_B", "overlap"]
EXPRESSION_CLASSES = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
CONFIDENCE_LEVELS = ["High", "Medium", "Low"]

ANNOTATION_INSTRUCTIONS = (
    "Label the dominant facial expression visible in the face crop. "
    "Use the facial appearance itself, not the surrounding event/context. "
    "Do not infer the expression from the source video. "
    "Do not use any model prediction as a reference. "
    "When uncertain, choose the most appropriate expression and mark confidence as Low."
)

# Label Studio XML config: one required, single-select "expression" Choices
# field (the ground-truth field) and one optional, separate "confidence"
# Choices field. Deliberately contains no field, value, or instruction text
# referencing any AI model, prediction, or confidence score -- verified by
# tests/test_label_studio_pilot.py.
LABEL_CONFIG = f"""<View>
  <Header value="EXP-PAP-004 Pilot Annotation"/>
  <Text name="instructions" value="{ANNOTATION_INSTRUCTIONS}"/>
  <Image name="image" value="$image"/>
  <Choices name="expression" toName="image" choice="single" required="true">
{chr(10).join(f'    <Choice value="{c}"/>' for c in EXPRESSION_CLASSES)}
  </Choices>
  <Choices name="confidence" toName="image" choice="single" required="false">
{chr(10).join(f'    <Choice value="{c}"/>' for c in CONFIDENCE_LEVELS)}
  </Choices>
</View>"""


def load_pilot_manifest(manifest_path: Path = PILOT_MANIFEST_PATH) -> list[dict]:
    with manifest_path.open() as f:
        return list(csv.DictReader(f))


def expected_pilot_image_ids(manifest_path: Path = PILOT_MANIFEST_PATH) -> set[str]:
    return {row["image_id"] for row in load_pilot_manifest(manifest_path)}


def verify_pilot_images_present(
    manifest_path: Path = PILOT_MANIFEST_PATH, images_dir: Path = PILOT_IMAGES_DIR
) -> None:
    """Raises RuntimeError with a precise diagnostic if the images on disk
    don't exactly match the manifest's image_id set. Never regenerates or
    resamples anything -- read-only verification."""
    manifest_ids = expected_pilot_image_ids(manifest_path)
    if not manifest_ids:
        raise RuntimeError(f"{manifest_path} has no rows -- pilot manifest is empty or missing.")

    disk_ids = {p.stem for p in images_dir.glob("*.jpg")}

    missing_on_disk = manifest_ids - disk_ids
    extra_on_disk = disk_ids - manifest_ids

    if missing_on_disk:
        raise RuntimeError(
            f"{len(missing_on_disk)} manifest image_id(s) have no file in {images_dir}: "
            f"{sorted(missing_on_disk)[:5]}..."
        )
    if extra_on_disk:
        raise RuntimeError(
            f"{len(extra_on_disk)} file(s) in {images_dir} are not in the manifest "
            f"(pilot set must be exactly the 150 manifest rows, no more): {sorted(extra_on_disk)[:5]}..."
        )


def local_file_url(image_id: str, manifest_rows: list[dict] | None = None, manifest_path: Path = PILOT_MANIFEST_PATH) -> str:
    """Label Studio's local-files-serving URL for a pilot image, relative
    to whatever LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT is set to at server
    start time (documented in tools/papuan_v2/README_label_studio.md).
    Uses the manifest's own recorded pilot_image_path, not a re-derived
    path, so this never depends on directory-listing order."""
    if manifest_rows is None:
        manifest_rows = load_pilot_manifest(manifest_path)
    for row in manifest_rows:
        if row["image_id"] == image_id:
            # pilot_image_path is already REPO_ROOT-relative (e.g.
            # "data/papuan_v2/pilot/images/xyz.jpg"); Label Studio's
            # local-files serving expects a path relative to
            # LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT, which this project's
            # setup script always sets to REPO_ROOT (see setup script).
            return f"/data/local-files/?d={row['pilot_image_path']}"
    raise KeyError(f"image_id {image_id!r} not found in pilot manifest")


def build_tasks(manifest_rows: list[dict] | None = None, manifest_path: Path = PILOT_MANIFEST_PATH) -> list[dict]:
    """Builds Label Studio task payloads from the pilot manifest.

    Each task's `data` contains ONLY: image (local-files URL), image_id
    (for deterministic export mapping), experiment_id. NEVER any
    AI-derived field (prediction, model name, model confidence) -- this
    is the structural guarantee behind the "blind labeling" requirement,
    verified in tests/test_label_studio_pilot.py by asserting the key set
    exactly, not just absence of specific banned keys.
    """
    if manifest_rows is None:
        manifest_rows = load_pilot_manifest(manifest_path)

    tasks = []
    for row in manifest_rows:
        image_id = row["image_id"]
        tasks.append(
            {
                "data": {
                    "image": local_file_url(image_id, manifest_rows),
                    "image_id": image_id,
                    "experiment_id": "EXP-PAP-004",
                }
            }
        )
    return tasks


def tasks_missing_from_project(existing_task_image_ids: set[str], manifest_rows: list[dict] | None = None, manifest_path: Path = PILOT_MANIFEST_PATH) -> list[dict]:
    """Pure idempotency logic: given the set of image_ids already present
    as tasks in the Label Studio project, returns only the task payloads
    for manifest rows NOT yet imported. Running the setup script twice
    against the same project must not create duplicate tasks."""
    if manifest_rows is None:
        manifest_rows = load_pilot_manifest(manifest_path)
    missing_rows = [row for row in manifest_rows if row["image_id"] not in existing_task_image_ids]
    return build_tasks(missing_rows)


def compute_overlap_assignment(
    manifest_rows: list[dict] | None = None,
    manifest_path: Path = PILOT_MANIFEST_PATH,
    seed: int = ANNOTATOR_B_OVERLAP_SEED,
    overlap_size: int = ANNOTATOR_B_OVERLAP_SIZE,
) -> list[dict]:
    """Deterministic Annotator-A/Annotator-B assignment over the fixed
    150-image pilot set.

    Annotator A is assigned all 150 images (already true by construction
    of the existing pilot project). Annotator B is assigned a
    reproducible `overlap_size`-image subset, sampled via
    `random.Random(seed).sample()` over the SORTED manifest image_id list
    (never directory-listing or Label Studio task order, both of which
    are not guaranteed stable). Task 1 (or any other already-annotated
    image) is not special-cased in or out -- it is eligible for the
    overlap subset exactly like every other image, per the approved
    design ("Task 1 should remain part of the pilot and should be
    eligible for the overlap subset even though A has already labeled
    it").

    Returns one row per manifest image, in manifest order:
        {image_id, annotator_A: True, annotator_B: bool, overlap: bool}
    (annotator_B == overlap here, since only overlap images go to B in
    this design -- kept as two columns for schema clarity /
    forward-compatibility with a future non-overlap-only B assignment.)
    """
    if manifest_rows is None:
        manifest_rows = load_pilot_manifest(manifest_path)

    all_ids_sorted = sorted(row["image_id"] for row in manifest_rows)
    if overlap_size > len(all_ids_sorted):
        raise ValueError(
            f"overlap_size ({overlap_size}) exceeds pilot size ({len(all_ids_sorted)})."
        )
    overlap_ids = set(random.Random(seed).sample(all_ids_sorted, overlap_size))

    return [
        {
            "image_id": row["image_id"],
            "annotator_A": True,
            "annotator_B": row["image_id"] in overlap_ids,
            "overlap": row["image_id"] in overlap_ids,
        }
        for row in manifest_rows
    ]


def write_annotator_assignment_csv(rows: list[dict], path: Path = ANNOTATOR_ASSIGNMENT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ANNOTATOR_ASSIGNMENT_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "image_id": row["image_id"],
                    "annotator_A": str(row["annotator_A"]).lower(),
                    "annotator_B": str(row["annotator_B"]).lower(),
                    "overlap": str(row["overlap"]).lower(),
                }
            )


def load_annotator_assignment(path: Path = ANNOTATOR_ASSIGNMENT_PATH) -> list[dict]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["annotator_A"] = row["annotator_A"] == "true"
        row["annotator_B"] = row["annotator_B"] == "true"
        row["overlap"] = row["overlap"] == "true"
    return rows


def overlap_image_ids(assignment_rows: list[dict] | None = None, path: Path = ANNOTATOR_ASSIGNMENT_PATH) -> set[str]:
    if assignment_rows is None:
        assignment_rows = load_annotator_assignment(path)
    return {row["image_id"] for row in assignment_rows if row["overlap"]}
