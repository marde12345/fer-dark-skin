"""Phase 1 validation fixture: bilingual (English/Indonesian) label config
and pure task-building logic for the THROWAWAY Label Studio project used
to empirically test the full-annotation architecture proposed in
docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md.

This module, and everything under tools/papuan_v2/validation/, is
DELIBERATELY SEPARATE from tools/papuan_v2/label_studio_config.py (the
pilot's production config module) -- nothing here is imported by, or
imports from, the pilot's EXP-PAP-004 scripts. The validation fixture
must never touch Project ID 2, ports 8080/8081, or any pilot data.

No network calls here -- pure constants and pure functions, unit-testable
without a live server, same convention as label_studio_config.py.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Fixture images are synthetic (generated noise + colored blocks with a
# baked-in "FIX01"/"FIX02"/"FIX03" label), never real Papuan face crops
# and never copied from data/papuan_v2/. Kept outside the repo (job scratch
# dir) since they are throwaway test fixtures, not a durable artifact.
FIXTURE_PROJECT_TITLE = "PHASE1-VALIDATION (throwaway, not pilot)"
FIXTURE_LABELING_CONFIG_VERSION = "phase1-validation-v1"

EXPRESSION_CLASSES_BILINGUAL = [
    ("Angry", "Marah"),
    ("Disgust", "Jijik"),
    ("Fear", "Takut"),
    ("Happy", "Senang"),
    ("Sad", "Sedih"),
    ("Surprise", "Terkejut"),
    ("Neutral", "Netral"),
]
CONFIDENCE_LEVELS_BILINGUAL = [
    ("High", "Tinggi"),
    ("Medium", "Sedang"),
    ("Low", "Rendah"),
]

# Choice `value` fields stay English-only (single canonical machine value
# per class, matching the pilot's existing EXPRESSION_CLASSES/CONFIDENCE_LEVELS
# so any future merge with the pilot's schema is a non-issue) -- only the
# human-visible label text is bilingual, via each Choice's own bilingual
# `alias`-free label text embedded directly in the tag body.
INSTRUCTIONS_EN = (
    "Label the dominant facial expression visible in the image. "
    "Select the facial expression that best matches the face. Choose exactly one expression. "
    "Do not use context outside the visible face. "
    "Do not use any AI/model prediction as a reference -- none is shown to you."
)
INSTRUCTIONS_ID = (
    "Beri label ekspresi wajah yang paling dominan pada gambar. "
    "Pilih ekspresi wajah yang paling sesuai dengan wajah pada gambar. Pilih tepat satu ekspresi. "
    "Jangan menggunakan konteks di luar wajah yang terlihat. "
    "Jangan menggunakan prediksi AI/model sebagai referensi -- tidak ada yang ditampilkan kepada Anda."
)


def _bilingual_choice_tags(pairs: list[tuple[str, str]]) -> str:
    """Each <Choice> uses its English canonical `value` (the machine-readable
    ground-truth value stored in exports) with bilingual display text via
    Label Studio's `value`+visible body pattern: Choices tags render the
    `value` attribute as the visible label, so bilingual text is embedded
    directly into `value` as "English / Indonesian" -- verified this is
    still a single unambiguous machine value per row (the whole string,
    e.g. "Happy / Senang", is what gets stored) -- see
    fixture_config.canonical_expression_value() for the English-only
    extraction used by export/consensus code, so downstream logic never
    has to parse the bilingual string."""
    return "\n".join(f'    <Choice value="{en} / {idn}"/>' for en, idn in pairs)


FIXTURE_LABEL_CONFIG = f"""<View>
  <Header value="Phase 1 Validation — Facial Expression Labeling / Pelabelan Ekspresi Wajah"/>
  <Text name="instructions_en" value="{INSTRUCTIONS_EN}"/>
  <Text name="instructions_id" value="{INSTRUCTIONS_ID}"/>
  <Image name="image" value="$image"/>
  <Header value="Expression / Ekspresi" size="4"/>
  <Choices name="expression" toName="image" choice="single" required="true">
{_bilingual_choice_tags(EXPRESSION_CLASSES_BILINGUAL)}
  </Choices>
  <Header value="Confidence / Keyakinan (optional, metadata only / opsional, hanya metadata)" size="4"/>
  <Choices name="confidence" toName="image" choice="single" required="false">
{_bilingual_choice_tags(CONFIDENCE_LEVELS_BILINGUAL)}
  </Choices>
</View>"""


def canonical_expression_value(bilingual_value: str) -> str:
    """Extracts the English canonical value from a bilingual Choice value
    like "Happy / Senang" -> "Happy". Used by export/consensus code so
    downstream logic (consensus voting, agreement metrics) always operates
    on the English canonical class, never the bilingual display string."""
    return bilingual_value.split(" / ")[0].strip()


def build_fixture_tasks(image_filenames: list[str], local_files_prefix: str = "fixture_images") -> list[dict]:
    """Builds Label Studio task payloads for the fixture images.

    Each task's `data` contains ONLY: image (local-files URL), image_id
    (stable identity for export mapping, keyed off the filename, never
    task list position). No AI-derived field of any kind -- verified by
    tests/test_phase1_validation_fixture.py by asserting the exact key
    set, matching the pilot's build_tasks() guarantee."""
    tasks = []
    for filename in image_filenames:
        image_id = Path(filename).stem
        tasks.append(
            {
                "data": {
                    "image": f"/data/local-files/?d={local_files_prefix}/{filename}",
                    "image_id": image_id,
                }
            }
        )
    return tasks
