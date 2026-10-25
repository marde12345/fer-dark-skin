"""EXP-012: shared, server-free configuration for manually relabeling the
227 legacy face crops in a separate Label Studio project.

Landmarks are a visual aid only. They are drawn on a separate rendered copy
of each crop; the original crop and every existing landmark file are only
read, never modified. No previous label, model prediction, or model name is
ever put into a task.

Landmark source priority (no new landmarks are generated):
  1. reviewed  -- human-reviewed CVAT landmarks (EXP-PAP-005 pilot/calibration)
  2. proposal  -- unreviewed InsightFace landmark_3d_68 proposals (EXP-PAP-005)
  3. proposal  -- unreviewed delivery-package 42-point initial landmarks,
                  mapped back from standardized 224x224 to crop coordinates
  4. missing   -- no landmarks available
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ID = "EXP-012"
EXPERIMENT_DIR = REPO_ROOT / "experiments" / "EXP-012-relabel"
LABEL_ROUND = 2  # round 1 = data/1408-1010-intermediate/manual_labels_export.csv

PROJECT_TITLE = "EXP-012 Legacy 227 Relabel (Round 2)"
SAMPLE_PROJECT_TITLE = "EXP-012 SAMPLE VERIFY (do not label)"
LABELING_CONFIG_VERSION = "v1"

# Relative to the data root (the main checkout's git-ignored data/).
LEGACY_FACES_REL = Path("data/1408-1010-intermediate/faces")
LEGACY_LABELS_REL = Path("data/1408-1010-intermediate/manual_labels_export.csv")
OVERLAY_REL = Path("data/exp012/overlays")

EXP_PAP_005 = REPO_ROOT / "experiments" / "EXP-PAP-005"
DELIVERY_DIR = REPO_ROOT / "delivery" / "papuan_v2_final_2026-10-19"

# Eyebrows 17-26, eyes 36-47, mouth 48-67 (same subset as
# tools/papuan_v2/generate_delivery_landmarks.py).
LANDMARK_SUBSET = list(range(17, 27)) + list(range(36, 48)) + list(range(48, 68))
REGIONS = {"brow": range(17, 27), "eye": range(36, 48), "mouth": range(48, 68)}

STATUS_REVIEWED = "reviewed"
STATUS_PROPOSAL = "proposal"
STATUS_MISSING = "missing"
STATUS_TEXT = {
    STATUS_REVIEWED: "Landmarks: REVIEWED by a human (visual aid only).",
    STATUS_PROPOSAL: "Landmarks: UNREVIEWED automatic proposal - may be wrong (visual aid only).",
    STATUS_MISSING: "Landmarks: MISSING for this crop - label from the original image.",
}

EXPRESSION_CLASSES = ["Neutral", "Happy", "Sad", "Surprise", "Fear", "Angry", "Disgust", "Ambiguous"]
EVAL_CLASSES = ["Fear", "Happy", "Neutral", "Sad", "Surprise"]  # five evaluation classes
CONFIDENCE_LEVELS = ["High", "Medium", "Low"]
OVERLAY_QUALITY = ["Usable", "Unreliable", "Not used"]

INSTRUCTIONS = (
    "Label the dominant facial expression from the ORIGINAL face crop. "
    "The landmark overlay only helps you look at the eyebrows, eyes, and mouth; "
    "do not decide the label from the dots, and ignore the overlay if it does not match the face. "
    "Choose Ambiguous if the expression cannot be determined reliably. "
    "No previous label or model prediction is shown, and none should be consulted."
)

LABEL_CONFIG = f"""<View>
  <Header value="EXP-012 Relabel (Round 2)"/>
  <Text name="instructions" value="{INSTRUCTIONS}"/>
  <Text name="landmark_note" value="$landmark_note"/>
  <View style="display:flex; gap:16px; align-items:flex-start">
    <View><Header value="Original crop" size="6"/><Image name="image" value="$image" maxWidth="300px"/></View>
    <View><Header value="Landmark overlay (visual aid)" size="6"/><Image name="overlay" value="$overlay" maxWidth="300px"/></View>
  </View>
  <Choices name="expression" toName="image" choice="single" required="true" showInline="true">
{chr(10).join(f'    <Choice value="{c}"/>' for c in EXPRESSION_CLASSES)}
  </Choices>
  <Header value="Confidence (optional)" size="6"/>
  <Choices name="confidence" toName="image" choice="single" required="false" showInline="true">
{chr(10).join(f'    <Choice value="{c}"/>' for c in CONFIDENCE_LEVELS)}
  </Choices>
  <Header value="Was the overlay usable? (optional)" size="6"/>
  <Choices name="overlay_quality" toName="image" choice="single" required="false" showInline="true">
{chr(10).join(f'    <Choice value="{c}"/>' for c in OVERLAY_QUALITY)}
  </Choices>
  <TextArea name="notes" toName="image" placeholder="Optional note" maxSubmissions="1" rows="2"/>
</View>"""

TASK_DATA_KEYS = {"image", "overlay", "image_id", "experiment_id", "label_round", "landmark_status",
                  "landmark_source", "landmark_note"}

LABELS_FIELDNAMES = ["experiment_id", "label_round", "image_id", "label", "eval_class", "confidence",
                     "overlay_quality", "notes", "annotator", "labeled_at", "landmark_status",
                     "landmark_source", "annotation_id"]


def legacy_image_ids(data_root: Path) -> list[str]:
    return sorted(p.stem for p in (data_root / LEGACY_FACES_REL).glob("*.jpg"))


def _rows_to_points(rows: list[dict]) -> dict[str, dict[int, tuple[float, float]]]:
    out: dict[str, dict[int, tuple[float, float]]] = {}
    for r in rows:
        out.setdefault(r["image_id"], {})[int(r["landmark_index"])] = (float(r["x"]), float(r["y"]))
    return out


def _xy_to_points(records) -> dict[str, dict[int, tuple[float, float]]]:
    return {r["image_id"]: {i: (float(x), float(y)) for i, (x, y) in enumerate(r["landmarks_xy"])} for r in records}


def load_reviewed() -> dict[str, dict[int, tuple[float, float]]]:
    pts = _rows_to_points(json.load(open(EXP_PAP_005 / "cvat_reviewed_landmarks.json")))
    pts.update(_rows_to_points(json.load(open(EXP_PAP_005 / "calibration_batch_40_reviewed.json"))))
    return pts


def load_exp005_proposals() -> dict[str, dict[int, tuple[float, float]]]:
    pts = _xy_to_points(json.load(open(EXP_PAP_005 / "insightface_68pt_pilot_predictions.json")).values())
    pts.update(_xy_to_points(json.load(open(EXP_PAP_005 / "calibration_batch_40_predictions.json")).values()))
    pts.update(_xy_to_points(json.load(open(EXP_PAP_005 / "batch3_predictions.json"))))
    return pts


def unstandardize(x: float, y: float, transform: dict) -> tuple[float, float]:
    """Inverse of generate_delivery_landmarks.py's letterbox: std = crop*scale + pad."""
    scale = float(transform["scale_factor"])
    return (x - float(transform["pad_left"])) / scale, (y - float(transform["pad_top"])) / scale


def load_delivery_initial() -> dict[str, dict[int, tuple[float, float]]]:
    transforms = {r["sample_id"]: r for r in csv.DictReader(open(DELIVERY_DIR / "04_Manifests" / "_standardization_transform.csv"))}
    out = {}
    for path in sorted((DELIVERY_DIR / "03_Landmarks" / "Initial").glob("*.json")):
        d = json.load(open(path))
        t = transforms[d["sample_id"]]
        out[d["sample_id"]] = {int(p["source_index"]): unstandardize(p["x"], p["y"], t) for p in d["points"]}
    return out


def resolve_landmarks(image_ids: list[str]) -> dict[str, dict]:
    """Picks one landmark source per crop by priority; keeps only the 42-point subset."""
    sources = [
        (STATUS_REVIEWED, "EXP-PAP-005 CVAT reviewed", load_reviewed()),
        (STATUS_PROPOSAL, "EXP-PAP-005 InsightFace proposal", load_exp005_proposals()),
        (STATUS_PROPOSAL, "delivery 42-pt initial (unstandardized)", load_delivery_initial()),
    ]
    resolved = {}
    for image_id in image_ids:
        resolved[image_id] = {"status": STATUS_MISSING, "source": "none", "points": {}}
        for status, name, pts in sources:
            if image_id in pts and all(i in pts[image_id] for i in LANDMARK_SUBSET):
                resolved[image_id] = {"status": status, "source": name,
                                      "points": {i: pts[image_id][i] for i in LANDMARK_SUBSET}}
                break
    return resolved


def local_file_url(abs_path: Path, document_root: Path) -> str:
    return f"/data/local-files/?d={abs_path.resolve().relative_to(document_root.resolve())}"


def build_tasks(image_ids: list[str], landmarks: dict[str, dict], data_root: Path, overlay_dir: Path,
                document_root: Path) -> list[dict]:
    tasks = []
    for image_id in image_ids:
        lm = landmarks[image_id]
        tasks.append({"data": {
            "image": local_file_url(data_root / LEGACY_FACES_REL / f"{image_id}.jpg", document_root),
            "overlay": local_file_url(overlay_dir / f"{image_id}.png", document_root),
            "image_id": image_id,
            "experiment_id": EXPERIMENT_ID,
            "label_round": LABEL_ROUND,
            "landmark_status": lm["status"],
            "landmark_source": lm["source"],
            "landmark_note": STATUS_TEXT[lm["status"]],
        }})
    return tasks


def sample_image_ids(landmarks: dict[str, dict], n_per_status: int = 2, seed: int = 1200) -> list[str]:
    """Deterministic small sample covering every landmark status, for end-to-end verification."""
    rng = random.Random(seed)
    picked = []
    for status in (STATUS_REVIEWED, STATUS_PROPOSAL, STATUS_MISSING):
        ids = sorted(i for i, lm in landmarks.items() if lm["status"] == status)
        picked += rng.sample(ids, min(n_per_status, len(ids)))
    return sorted(picked)


def _choice(result: list[dict], name: str) -> str:
    for item in result:
        if item.get("from_name") == name:
            vals = item.get("value", {}).get("choices", [])
            return vals[0] if vals else ""
    return ""


def _text(result: list[dict], name: str) -> str:
    for item in result:
        if item.get("from_name") == name:
            return " ".join(item.get("value", {}).get("text", []))
    return ""


def label_rows_from_tasks(tasks: list[dict], user_email_by_id: dict[int, str] | None = None) -> list[dict]:
    """One row per submitted annotation (several annotators per crop are kept as separate rows)."""
    user_email_by_id = user_email_by_id or {}
    rows = []
    for task in tasks:
        data = task.get("data", {})
        for ann in task.get("annotations", []):
            if ann.get("was_cancelled"):
                continue
            result = ann.get("result", [])
            label = _choice(result, "expression")
            if not label:
                continue
            completed_by = ann.get("completed_by")
            rows.append({
                "experiment_id": EXPERIMENT_ID,
                "label_round": LABEL_ROUND,
                "image_id": data.get("image_id", ""),
                "label": label,
                "eval_class": label if label in EVAL_CLASSES else "",
                "confidence": _choice(result, "confidence"),
                "overlay_quality": _choice(result, "overlay_quality"),
                "notes": _text(result, "notes"),
                "annotator": user_email_by_id.get(completed_by, str(completed_by)),
                "labeled_at": ann.get("updated_at") or ann.get("created_at") or "",
                "landmark_status": data.get("landmark_status", ""),
                "landmark_source": data.get("landmark_source", ""),
                "annotation_id": ann.get("id", ""),
            })
    return sorted(rows, key=lambda r: (r["image_id"], str(r["annotation_id"])))
