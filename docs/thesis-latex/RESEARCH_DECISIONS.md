# Research Decisions — Confirmed 2026-10-09

This file records decisions confirmed directly by the author, distinct from inferences drawn from repository evidence alone. It supersedes, for the items listed, the "open item" framing used in the first audit pass (see `research-audit/RESEARCH_TIMELINE.md` Stage 7 and `research-audit/DATA_DISCREPANCIES.md` D-2, D-4).

## Decision 1 — Facial Emotion Recognition (FER) Remains the Primary Research Objective

**Confirmed:** The thesis's primary research objective is facial emotion classification. The existing HSEmotion-baseline, CLAHE-ablation, and ArcFace+Logistic-Regression comparison experiments (EXP-005, EXP-006, EXP-007) are the core experimental contribution.

**Implication:** Chapters 1, 3, 4, and 5 of the manuscript are revised so that the research narrative, objectives, and (candidate) research question are built around these completed experiments, not around the facial-landmark track.

**Not decided by this confirmation:** the exact wording of the final Research Question. The author confirmed the *topic* (FER performance/robustness characterization via the existing experiments), not a specific RQ sentence. A grounded candidate RQ is proposed in `chapters/01-introduction.tex` §1.5 for the author's/supervisor's approval — it is a **proposal**, not a confirmed final RQ.

## Decision 2 — Facial Landmarks Are a Supporting/Future-Work Track, Not the Primary Contribution

**Confirmed:** The facial-landmark annotation and (planned) model-refinement track is supporting methodological development, not a replacement for the FER research direction.

**Implication:** The manuscript discusses this track only as (a) a dataset-development effort in progress, and (b) a planned future workflow, never as a completed experiment or as something that has already improved emotion-classification performance. The planned workflow is stated explicitly as:

```
Automatic landmark proposals (InsightFace landmark_3d_68, EXP-PAP-005)
  → human review and correction in CVAT                        [NOT YET DONE]
  → quality control (e.g., inter-annotator agreement on         [NOT YET DONE —
     landmark placement, if a second reviewer is used)           protocol not yet defined]
  → creation of a reviewed, human-verified landmark dataset       [NOT YET DONE]
  → training or refinement of a downstream model using these     [NOT YET DONE — no
     landmarks (e.g., as auxiliary features for emotion            training code exists]
     classification, or as its own landmark-prediction task)
  → evaluation on a held-out set                                 [NOT YET DONE]
```

**Evidence required before any stage above can be described as complete:** a committed, reviewed CVAT export (stage 1→2); an explicit agreement statistic if multi-reviewer (stage 2→3); a dataset manifest distinguishing reviewed from unreviewed points (stage 3→4); training code, a trained checkpoint, and a logged training run (stage 4→5); and a held-out evaluation report with metrics (stage 5→6). **None of these exist in the repository at the time of writing.** No claim that landmark review or retraining has improved — or even been tested against — emotion-classification performance may be made without a controlled experiment establishing that relationship, which does not currently exist.

## Decision 3 — N=135 Provenance: Legacy Dataset, Not Papuan V2

**Investigated and resolved:** The author initially recalled that the $N=135$ common evaluation subset originated from a Papuan V2 reconstruction. This was checked against `docs/EXP-007_ARCFACE_EVALUATION.md` §2–3, which documents a programmatic `face_filename`-based join (not row-position matching) showing that the 18 historical Neutral→Angry misclassifications from the full 227-sample legacy population fall *exactly* inside the 135-sample subset — a result that would not hold if the two populations were independently extracted datasets. **The author confirmed this evidence outweighs the recollection; $N=135$ is a filtered subset of the legacy 227-crop dataset, not a Papuan V2 reconstruction.**

**Additionally resolved in this pass:** the exact filter chain producing 135 from 227 — previously an open item (`DATA_DISCREPANCIES.md` D-2) — is now documented: 227 → −83 `Ambiguous` → 144 → −1 `Angry`/−2 `Disgust` → 141 → −6 ArcFace alignment-failure exclusions → 135, cross-corroborated between `docs/EXP-007_ARCFACE_EVALUATION.md` and `docs/ARCFACE_EXPERIMENT_DESIGN.md`.

**Not fully resolved:** the row-level identity of the 6 alignment-failure exclusions was not independently re-derived from the raw `classifier_predictions.csv` in this pass. This residual gap is much narrower than the original "derivation rule unknown" finding and does not block presenting the EXP-007 results as a well-documented, if not perfectly re-verified-from-raw-data, comparison.

## Decision 4 — Research Question Structure (2026-10-09, second revision)

**Confirmed:** the thesis adopts a primary RQ plus three sub-questions (RQ1, RQ2, RQ3), one per completed experiment, rather than a single compound sentence. The approved formulation (reproduced verbatim in `chapters/01-introduction.tex` §1.5) is:

> **Primary RQ:** How does a pretrained, general-purpose facial emotion recognition model perform in terms of classification errors and skin-tone-proxy subgroup differences on a sample of facial expression images from a single source film, and how do the evaluated contrast-preprocessing and alternative-classifier configurations affect the observed results?
> **RQ1:** What are the overall accuracy, dominant confusion patterns, and observed skin-tone-proxy subgroup accuracy differences of HSEmotion on the 227-image sample?
> **RQ2:** How does the tested adaptive CLAHE configuration affect HSEmotion's classification accuracy and error patterns on the same 227-image sample?
> **RQ3:** On the derived 135-image, five-class evaluation subset, how do the observed accuracy and error patterns of ArcFace-embedding-based Logistic Regression compare with those of HSEmotion?

This supersedes the single-sentence RQ proposed in the prior revision. The new structure resolves two weaknesses identified in the preceding review: it explicitly separates the N=227 population (RQ1, RQ2) from the N=135 derived subset (RQ3) rather than implying one shared "evaluation population," and it gives CLAHE (RQ2) its own question rather than leaving it absent from the RQ despite being a confirmed objective.

**Still a proposal, not a supervisor-approved RQ.** The structure and wording are approved by the author as the direction for this revision; Pak Fadhil's sign-off is still pending. The manuscript states this in the chapter text itself (not only in a code comment), so a reader encounters the pending-approval status directly.

**Editorial note on wording, per the author's instruction to document any change rather than silently alter scope:** the supplied primary-RQ wording was kept essentially verbatim; the sub-question wording was likewise kept verbatim. No scope change was introduced in transcribing these into the manuscript.

**Disclosure preserved from the prior revision:** RQ3's comparison (EXP-007) was run before any version of the RQ existed in writing. The manuscript's Chapter 4 treats this explicitly as analysis of previously collected evidence, not as a confirmatory test designed prospectively around RQ3.

**Discrepancy surfaced during this revision (D-8), since resolved:** EXP-006's "before" per-skin-tone figures (Dark 27.67%, Medium-Dark 10.77%) differ from EXP-005's (Dark 44.00%, Medium-Dark 14.29%) because they cover different populations — all 227 crops vs. the 85 crops with landmark features — not because of a calculation error (`research-audit/D8_SKIN_TONE_DISCREPANCY_INVESTIGATION.md`). See `research-audit/DATA_DISCREPANCIES.md` D-8 for how the thesis now cites each.

**Superseded by Decision 5:** the RQ wording above has been replaced in the manuscript by the fairness-focused RQs below.

## Decision 5 — Fairness Evaluation as the Primary Direction (recorded 2026-10-25)

**As relayed by the author:** Pak Fadhil approved fairness evaluation in FER as the thesis direction. No written record of that approval (email, meeting note, or signed form) exists in this repository; this entry records the author's report only.

**Adopted in the manuscript (Chapters 1–5, title, abstracts):** the thesis evaluates the performance gap between two skin-brightness groups, Dark and Medium-Dark, on the 135-crop five-class subset (EXP-010, EXP-011), with 227-crop results as supporting evidence only. Light-skin evaluation is out of scope because the data contain no Light crops and only 3 Medium-Light crops.

> **Primary RQ:** To what extent does a pretrained FER model's performance differ between skin-brightness groups (a proxy, not a measure of ethnicity or pigmentation) on face crops from one Papuan documentary film, and does contrast preprocessing (CLAHE) or an alternative classifier (ArcFace + Logistic Regression) change that difference on the evaluated sample?
> **RQ1:** How large is HSEmotion's performance difference between the Dark and Medium-Dark groups, and which error patterns dominate in each?
> **RQ2:** Does the tested CLAHE configuration change that between-group difference on the same sample?
> **RQ3:** On the same five-class subset, do ArcFace + Logistic Regression and HSEmotion differ in the size of the between-group difference?

**Still a proposal:** the exact RQ wording and the thesis title (`config.tex`) are the author's proposal; Pak Fadhil's approval of the wording, including naming "Papua" in the RQ and title, is pending.

## Open Items Still Requiring Author/Supervisor Input

1. **Supervisor sign-off on the RQ wording and thesis title** (Decision 5) — the fairness direction is reported as approved; the exact wording is pending. Record the approval here, with its source, once given.
6. **D-8** — resolved (population difference; see `research-audit/DATA_DISCREPANCIES.md`). No action remaining.
2. **Whether the landmark track appears in the final thesis at all**, and if so, how much space it receives (a single "future work" paragraph vs. a full methodology subsection) — the current draft treats it as a modest, clearly-labeled supporting-track discussion; this allocation itself is an editorial judgment the author may want to revise.
3. **Row-level re-verification of the 135-sample population** against the raw `classifier_predictions.csv`, if the author wants the derivation fully closed rather than documentarily resolved.
4. **Annotator A completion status** (Papuan V2 Label Studio pilot) — resolved 2026-10-25: 150/150 confirmed from the raw files (`DATA_DISCREPANCIES.md` D-1). Annotator B remains 0/75; whether to continue that track is still undecided.
5. **Official ITB formatting template / friend's-thesis structural reference** — still not located in the repository.
