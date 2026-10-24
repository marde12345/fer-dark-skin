# Data Discrepancy Register

**Status legend:**
- **RESOLVED** — conflicting claims reconciled with supporting evidence and a stated rationale.
- **UNRESOLVED** — conflicting or ambiguous evidence; no reconciliation possible from available artifacts.
- **SUPERSEDED** — an earlier claim is explicitly replaced by a later one, for a documented reason; the earlier claim is preserved here, not deleted.
- **NOT VERIFIABLE** — the evidence needed to resolve the question does not exist in this repository.

---

### D-0 — "Experiment B" (FER2013 + ResNet18, 68.57%/69.77%/68.65%/69.76%/26.96% generalization gap)

- **Claim:** this task's background context states these specific figures as a prior experiment.
- **Conflicting evidence:** a repository-wide, case-insensitive search across all tracked and untracked `.md`, `.py`, `.ipynb`, `.csv`, and `.json` files for `FER2013`, `ResNet18`, `resnet`, and each of the five specific numeric strings returned **zero matches**. No dataset directory, config file, training script, model checkpoint, or report references FER2013 or ResNet18 anywhere in this repository.
- **Different versions or conditions?** Not determinable — there is no artifact to compare against.
- **Most reliable evidence:** the absence of any trace, after an exhaustive search, is itself the only evidence available.
- **Resolvable?** No, not from this repository.
- **Resolution:** None. This experiment, and these figures, are **not used anywhere in the thesis manuscript**.
- **Remaining uncertainty / impact:** If this experiment genuinely occurred (e.g., in a different project, a different machine, a notebook/platform not synced to this repository, or a prior conversation with no export present in this workspace), its source must be located and provided before it can be cited. Its definition of "generalization gap" (val-vs-test? train-vs-val? train-vs-test?) is explicitly flagged by the task itself as not to be assumed, and cannot be determined here either way, since no artifact defining it was found.
- **Status: NOT VERIFIABLE.**

### D-1 — Papuan V2 Annotator A Completion (EXP-PAP-004)

- **Claim:** one internal record (a session/status note, not independently re-opened and re-verified against the raw file in this pass) states Annotator A's 150 Label Studio tasks were fully submitted as of 2026-10-01.
- **Conflicting evidence:** the raw artifacts that would directly confirm this (`experiments/EXP-PAP-004/label_studio_export.csv`, `annotator_progress.json`) exist in the repository and were read during an earlier audit pass in this session, but their row-by-row completion count was not re-tabulated and cross-checked line-by-line against the 150/150 claim in *this* specific pass.
- **Different versions or conditions?** No — same artifact, same claim, just not independently re-counted here.
- **Most reliable evidence:** the raw export/progress files, not the status-note summary of them.
- **Resolvable?** Yes, in principle — directly from the two files named above — but not yet executed as an explicit row-count check in this audit.
- **Resolution:** **Deferred, not assumed.** The thesis manuscript's methodology chapter (and `EXPERIMENT_REGISTRY.md` above) explicitly state this figure as unverified rather than repeating "150/150 complete" as fact.
- **Remaining uncertainty / impact:** If Annotator A's labels are genuinely complete, a human-vs-pseudo-label agreement analysis becomes possible for the 150-image pilot (filling part of the Chapter 4 "Papuan V2" TODO). If they are not actually complete, this must be stated plainly rather than assumed.
- **Status: UNRESOLVED** (resolvable with one direct file check not yet performed in this pass).

### D-2 — Derivation of the $N=135$ Common Evaluation Subset from $N=227$

- **Update (post-clarification):** a prior version of this entry considered the possibility that $N=135$ originated from a separate "Papuan V2 reconstruction." **That possibility was raised, investigated, and explicitly ruled out by the author.** `docs/EXP-007_ARCFACE_EVALUATION.md` §2–3 documents, with a programmatic `face_filename`-based join (not row-position matching), that the 135-sample common subset is drawn from the **same 227-crop legacy dataset**, not from Papuan V2: the 18 historical Neutral→Angry cases from the full 227-sample population are shown to fall *exactly* inside the 135-sample subset, which would not hold if the two populations were drawn from independently re-extracted data. **Provenance is therefore Verified: legacy/227, not Papuan V2.**
- **Claim (original):** `reports/arcface_evaluation/*.csv` and `docs/RESEARCH_FINDINGS.md` both use a 135-image subset of the 227-image legacy population for the EXP-007 comparison; the exact derivation rule was not located in the first audit pass.
- **Resolution of the derivation arithmetic (this revision):** cross-referencing `docs/EXP-007_ARCFACE_EVALUATION.md` §2 and `docs/ARCFACE_EXPERIMENT_DESIGN.md` (§§ on `Ambiguous` handling, alignment exclusion, and the instruction to report "exact sample count at each filtering stage: raw 227 → after `Ambiguous` exclusion → after alignment-eligibility exclusion → final evaluation set") yields a consistent, corroborated chain:
  1. 227 total face crops (legacy dataset).
  2. − 83 `Ambiguous`-labeled crops (excluded from classifier training/evaluation by explicit design decision) → **144**, which matches EXP-007 §2's reported "Valid (non-`Ambiguous`) GT labels, full dataset: 144" exactly.
  3. − 1 `Angry` − 2 `Disgust` (rare-class exclusion, insufficient samples for the 5-class classifier) → **141** label-eligible crops.
  4. − 6 further crops lost to ArcFace re-detection/alignment failure on re-crop (part of the 49 total alignment failures reported — $227-178=49$ — most of which overlap with crops already excluded in steps 2–3 for label reasons, leaving 6 "additional" losses within the 141 label-eligible population) → **135**, matching EXP-007 §2's final "ArcFace classifier population (R6, after rare-class exclusion): 135" exactly.
- **Most reliable evidence:** this chain is corroborated by two independent documents (`EXP-007_ARCFACE_EVALUATION.md`'s reported counts and `ARCFACE_EXPERIMENT_DESIGN.md`'s prescribed filter order), and the arithmetic is internally consistent (144 matches exactly; 135 matches exactly once the 6-sample alignment loss is accounted for).
- **Remaining unresolved gap:** the specific identity of the 6 samples lost at the alignment stage (i.e., the exact row-level list, re-derived directly from `data/intermediate/arcface_embeddings/classifier_predictions.csv` and the raw alignment-status field) was **not independently re-counted row-by-row from the raw CSV in this pass**. The *rule* (what kind of exclusion) and the *arithmetic* (that the counts are mutually consistent) are resolved; the *exact row-level membership* of the final 135 is not independently re-verified beyond trusting the programmatic join already documented in EXP-007 §2/§22.
- **Status: RESOLVED (provenance: legacy/227, confirmed; derivation rule and arithmetic: resolved and cross-corroborated) — NOT fully resolved at the row-level identity-list granularity**, which is a materially smaller residual gap than the original "derivation rule not located" finding. Do not treat this as a complete re-verification from raw data; treat it as a resolved documentary cross-check.

### D-3 — "100% / Uniformly Dark-Skinned" Claim vs. Computed Skin-Tone Distribution

- **Claim:** an earlier personal note (`Tesis_Knowledge_Transfer_(1).md`) describes the dataset's subjects, in prose, as dark-skinned, in a way read by a later internal audit as implying near-uniformity.
- **Conflicting evidence:** the computed LAB-luminance skin-tone bucket distribution shows 58.8% Dark / 41.2% Medium-Dark at the $N=227$ scale (46 Dark / 32 Medium-Dark / 57 Unknown at $N=135$) — i.e., a two-category split, not a uniform population.
- **Different versions or conditions?** No — same population, same underlying images; the discrepancy is between an informal prose description and a later, more precise computed measurement.
- **Most reliable evidence:** the computed LAB-luminance distribution (`reports/audit_per_skin_tone_accuracy.csv` and related files), because it is a direct, reproducible pixel-level calculation rather than an unquantified prose impression.
- **Resolvable?** Yes.
- **Resolution:** The dataset is **not** uniformly dark-skinned; it contains a Dark/Medium-Dark split, both of which are themselves pixel-luminance-derived buckets, not ethnicity labels. The earlier "100% dark-skinned" framing is corrected, not retained, in the thesis manuscript.
- **Remaining uncertainty:** the LAB-luminance bucketing methodology's own validity as a stand-in for any meaningful skin-tone construct (versus, e.g., a Fitzpatrick-scale-based or dermatologically validated measure) has not been independently assessed.
- **Status: RESOLVED** (in favor of the computed distribution; the earlier claim is superseded).

### D-4 — Primary Papuan V2 Annotation Target: Emotion Labels vs. Facial Landmarks

- **Claim (earlier):** Papuan V2's purpose, through EXP-PAP-001–004, was to build a larger emotion-labeled dataset, continuing the legacy dataset's research direction.
- **Claim (later):** per `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, on 2026-10-02 a supervisor ("Pak Fadhil") directed that the primary annotation target change from emotion labels to facial landmarks.
- **Different versions or conditions?** Yes — this is a genuine change in research direction over time, not a measurement conflict. Both claims are accurate *for their respective time periods*.
- **Most reliable evidence:** the dated internal report explicitly describing the pivot and its rationale.
- **Resolvable?** Yes, as a timeline fact (see `RESEARCH_TIMELINE.md` Stage 6) — but **the implication for the thesis's scope is not resolvable from evidence alone**: whether the thesis's primary contribution is the (completed) emotion-classification comparison, the (incomplete) landmark track, or both, is a scope decision requiring the author/supervisor, not a fact to be inferred.
- **Resolution:** The pivot itself is accepted as fact at the *annotation-target* level within the Papuan V2 dataset-construction track (facial landmarks did become the primary annotation target for that specific pilot, superseding the paused Label Studio emotion-annotation effort). **However, the author has since confirmed (2026-10-09 clarification) that facial-emotion classification remains the primary research objective of the thesis as a whole; the facial-landmark track is a supporting/future-work development track, not a redefinition of the thesis's core research direction.** This resolves the higher-level scope question that was previously left open: the thesis's primary contribution is the completed emotion-classification/model-comparison work (EXP-005/006/007); the landmark track is discussed as supporting methodology and future work, contingent on completion of human review and any subsequent retraining. See `RESEARCH_DECISIONS.md` for the full record of this confirmation and its implications.
- **Status: SUPERSEDED** (annotation-target-within-Papuan-V2 fact, unchanged) **+ RESOLVED** (thesis-level scope: FER confirmed primary, landmarks confirmed supporting/future work, per author decision recorded in `RESEARCH_DECISIONS.md`).

### D-5 — Research Framing: "FER for Dark-Skinned Faces Using ArcFace" vs. Solution-Neutral Reformulation

- **Claim (earlier):** `docs/RESEARCH_FRAMING.md` records the project's own original framing in these terms.
- **Claim (later):** `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md` flags this framing as a solution-first violation of the supervisor's design-research guideline, and `docs/proposal/research/PROBLEM_ARCHITECTURE.md` was built specifically to avoid starting from it.
- **Different versions or conditions?** No — this is an internal methodological self-correction, not a data discrepancy in the usual sense.
- **Resolution:** The later, solution-neutral framing is adopted in the thesis manuscript; the earlier framing is preserved here and in `RESEARCH_TIMELINE.md` as a documented part of the research's actual history, not erased.
- **Status: SUPERSEDED** (by the project's own explicit self-correction).

### D-6 — ArcFace-as-FER-Feature-Extractor: Novel Technique vs. Prior Art

- **Claim (implicit in earlier framing):** combining ArcFace embeddings with a downstream classifier for FER was treated, in earlier project framing, as a candidate novel contribution.
- **Conflicting evidence:** `docs/proposal/research/STATE_OF_ART_AND_GAP.md` identifies that this technique is already published (Altaha et al. 2023; Waldner & Mitra 2024).
- **Resolvable?** Yes.
- **Resolution:** The thesis manuscript explicitly states that this technique is not novel; any contribution claim rests on the specific empirical comparison and population, not the technique itself.
- **Status: RESOLVED** (in favor of the literature-verified prior-art finding).

### D-8 — EXP-006's "Before" Per-Skin-Tone Accuracy Does Not Match EXP-005's Dedicated Audit

- **Claim:** EXP-006 (`reports/preprocessing_experiment_summary.csv`) reports Dark accuracy 0.2767 and Medium-Dark accuracy 0.1077 for its "before" (original, pre-CLAHE) condition — nominally the same HSEmotion-on-original-crops condition that EXP-005 (`reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv`) reports as Dark 0.44 and Medium-Dark 0.1429.
- **Investigated and resolved (see `research-audit/D8_SKIN_TONE_DISCREPANCY_INVESTIGATION.md` for the full method, scripts, and recomputation).** Contrary to the prior note that the raw CSVs were unavailable, the underlying intermediate files (`data/1408-1010-intermediate/manual_labels_export.csv`, `landmark_features.csv`, `clahe_predictions.csv`) exist on disk (gitignored, never deleted). Recomputing both experiments' figures directly from these files reproduced every reported number exactly, to full floating-point precision, with zero discrepancy against the committed summary CSVs.
- **Root cause, confirmed by exact recomputation:** EXP-005's skin-tone breakdown is computed over an inner join with `landmark_features.csv`, an optional pipeline stage (`docs/ARCHITECTURE.md` marks it `[optional]` in the data-flow diagram) that successfully produced output for only **85 of the 227** face crops (50 Dark, 35 Medium-Dark — recomputed as 22/50=0.44 and 5/35=0.142857..., exact matches). EXP-006 computes `skin_tone` independently, in its own notebook, for **all 227** crops (159 Dark, 65 Medium-Dark, 3 Medium-Light — recomputed as 44/159=0.276730..., 7/65=0.107692..., 0/3=0.0, all exact matches, before-condition). Both figures are internally correct; they describe different, unequally-sized populations, not the same population computed two different ways. Overall accuracy matches exactly between the two (51/227 in both) because it does not depend on `landmark_features.csv` at all.
- **Secondary question, plausibly but not fully explained:** why `landmark_features.csv` covers only 85 of 227 crops. `docs/ARCHITECTURE.md`'s Error Handling section documents that exceptions during landmark processing are "caught and the affected image is silently skipped... rather than logged with a reason," consistent with (but not independently confirmed per-crop for) the other 142 crops having failed this optional stage silently.
- **Resolvable?** Yes — resolved in this pass by direct recomputation from files that were, in fact, available on disk.
- **Resolution:** EXP-005's and EXP-006's skin-tone figures are both correct for the population each actually measures (85-crop subset vs. full 227-crop population respectively) and should not be read as corroborating or contradicting one another. The 29.71-percentage-point gap used for RQ1 should be labeled explicitly as computed over the 85-crop skin-tone-characterized subset, not the full 227-crop sample.
- **Remaining uncertainty / impact:** None material to the numbers themselves — both are now fully traced to their exact source population. The only open item is the precise per-crop reason for the 142-crop gap in `landmark_features.csv`, which is a minor provenance question, not a correctness question.
- **Status: RESOLVED.**

### D-7 — Sample-Count Units: "227 Samples" as Subjects vs. Face Crops vs. Frames

- **Claim:** informal references to "227 samples" could be read as 227 subjects.
- **Evidence:** 227 is the count of detected **face crops** from 100 sampled frames; no subject-identity field exists (see `DATA_DICTIONARY.md`), so the number of distinct individuals represented is unknown and could be smaller than 227 (same person appearing in multiple frames) or, in principle, if multiple faces per frame are common, the crop count naturally exceeds frame count without implying 227 distinct people either way.
- **Resolvable?** No, not without a subject-identity labeling effort that does not exist.
- **Resolution:** The thesis manuscript consistently describes 227 (and 645, for Papuan V2) as face-crop counts, never as subject counts, and states the absence of subject-level identity as a limitation.
- **Status: NOT VERIFIABLE** (subject count); **RESOLVED** (unit of counting, clarified as face crops).
