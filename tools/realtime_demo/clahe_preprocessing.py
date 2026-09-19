"""CLAHE preprocessing for the realtime demo — re-exported from the
promoted single source of truth.

EXP-006 ("Preprocessing Experiment: Strategy B CLAHE vs. False-Angry
Rate", docs/EXPERIMENT.md) originally defined `compute_l_weighted` and
`apply_strategy_b_clahe` as notebook-local functions in
notebooks/preprocessing_experiment_executed.ipynb. They were copied here
verbatim for the demo, and have now been promoted a second time into
`src/fer_dataset/shared/clahe.py` (see that module's docstring) as part
of the Papuan V2 data-pipeline work
(docs/proposal/PAPUAN_V2_RECON_AND_PROPOSAL.md §10b step 8), so there is
exactly one implementation shared by this demo and the new Papuan V2
pipeline instead of two copies silently able to diverge.

This module now only re-exports; no transform logic changed. Callers
that already do `from clahe_preprocessing import apply_strategy_b_clahe`
continue to work unchanged.

What this demo EXTENDS beyond EXP-006 (must not be presented as
established research evidence -- see tools/realtime_demo/README.md):
EXP-006 only ever re-classified CLAHE-adjusted crops with HSEmotion.
It never tested a CLAHE-adjusted crop through the ArcFace + Logistic
Regression pipeline (which did not yet exist at the time EXP-006 ran).
Applying the identical, already-established crop-level CLAHE transform
before ArcFace's own internal alignment is a natural, documented
extension for this demo -- not a claim that EXP-006 evaluated it.
"""

from __future__ import annotations

from fer_dataset.shared.clahe import apply_strategy_b_clahe, compute_l_weighted

__all__ = ["compute_l_weighted", "apply_strategy_b_clahe"]
