"""Phase 1 validation: tiny deterministic consensus fixture demonstrating
the future consensus logic proposed in
docs/proposal/EXP-PAP-FULL_ANNOTATION_PLAN.md section 7, before it is
implemented against real annotation data.

Pure functions only -- no live server, no real pilot/full-dataset data.
Operates on plain (image_id -> label) dicts, never on Label Studio task
objects directly, so it can be unit-tested in isolation and later reused
unchanged once real exports exist.

Majority-vote rule for N=3: unanimous (all three agree) or majority
(2-of-3) both resolve to a consensus_label with adjudication_required =
False; no-majority (all three different) sets consensus_label = None and
adjudication_required = True. AI predictions and confidence values are
NEVER inputs to this computation -- confidence is deliberately not even
accepted as a parameter, so it cannot silently influence consensus.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ConsensusResult:
    image_id: str
    labels: tuple[str, str, str]
    agreement_status: str  # "unanimous" | "majority" | "no_majority"
    consensus_label: str | None
    adjudication_required: bool


def compute_consensus(image_id: str, label_a: str, label_b: str, label_c: str) -> ConsensusResult:
    """Majority-vote consensus for exactly 3 independent human labels.
    Confidence is intentionally not a parameter -- it must never affect
    this computation, only be recorded as separate metadata elsewhere."""
    labels = (label_a, label_b, label_c)
    counts = Counter(labels)
    most_common_label, most_common_count = counts.most_common(1)[0]

    if most_common_count == 3:
        return ConsensusResult(image_id, labels, "unanimous", most_common_label, False)
    if most_common_count == 2:
        return ConsensusResult(image_id, labels, "majority", most_common_label, False)
    return ConsensusResult(image_id, labels, "no_majority", None, True)
