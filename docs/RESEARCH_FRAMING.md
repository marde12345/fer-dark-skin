# Research Framing

> R2.5 — read-only research-framing reconstruction, building on `docs/RESEARCH_EVIDENCE_AUDIT.md` (R1) and `docs/THESIS_RQ_ALIGNMENT.md` (R2). No source code, notebooks, datasets, reports, or configuration were modified to produce this document. Nothing in this document is an official thesis RQ, objective, hypothesis, or contribution — all candidate framings below are explicitly labeled as such and require author/advisor confirmation.

---

## 1. Author's Intended Research Direction

As stated by the author for this phase (not independently verifiable from repository files, and reproduced here exactly as given, not reworded into a formal RQ):

> Facial Expression Recognition (FER) for dark-skinned faces using ArcFace, using a dataset collected from the film "Pesta Babi" through a semi-automatic dataset generation and labeling pipeline.

And an observed empirical phenomenon the author reports motivating the research:

> Papuan faces show a tendency toward false detection, particularly Neutral expressions being predicted as Angry.

Both statements are treated here as **author-provided research intent**, distinct from what the repository's code and data can independently verify (Section 5).

---

## 2. Reconstructed Research Problem

Based on the author's stated intent and the repository's actual evidence (Sections 3–4), the research problem can be described, in concise academic form, as:

> Off-the-shelf facial expression recognition models are typically trained and validated on datasets that underrepresent dark-skinned faces. This repository's dataset-generation pipeline produced a labeled facial-expression dataset from a documentary video ("Pesta Babi") depicting a dark-skinned Papuan population, and an initial evaluation of an off-the-shelf FER model (HSEmotion) against manually-verified ground truth on this dataset shows low overall accuracy (22.5%) and a specific, recurring failure mode: faces are frequently misclassified as "Angry," most often when the true expression is "Neutral" (18 of 40 false-Angry cases). This raises the question of whether — and to what extent — this off-the-shelf model's performance and error pattern is associated with skin-tone characteristics present in this population, and whether the pipeline's face-detection/embedding component (InsightFace, which internally uses an ArcFace-architecture recognition model) combined with a dedicated FER classifier can be evaluated or improved for this population.

This framing deliberately does **not** assert "fairness research" as the primary framing (per the instruction not to default to that), and does **not** assert a demonstrated Papuan-specific or ethnicity-specific effect (Section 4) — it states the observed technical phenomenon (Neutral→Angry misclassification) and the population context (dark-skinned faces, Papua documentary source) as given, separately.

---

## 3. Research Components

| Component | Role in Research | Note on repository evidence |
|---|---|---|
| ArcFace | Author-stated main FER model/method | **Discrepancy found** — the current pipeline does not use ArcFace (or any model) for expression classification. `src/fer_dataset/pipeline/emotion_classifier.py` uses **HSEmotion** (`enet_b0_8_best_vgaf`) for emotion classification. ArcFace-family weights (`w600k_r50`, task "recognition") are loaded only as part of the InsightFace `buffalo_l` bundle in `src/fer_dataset/pipeline/face_detector.py` and `emotion_classifier.py`, for face **detection/embedding**, not expression classification — and the recognition-embedding output does not appear to be consumed anywhere in the current code (see Section 5). |
| Pesta Babi | Dataset source | Confirmed: `config/config.yaml` → `video.path: data/raw/videos/pesta_babi.mp4`. |
| Dark-skinned faces | Target data/population | Partially confirmed: of the 85/227 labeled samples with computed skin tone, all fall into `Dark` (58.8%) or `Medium-Dark` (41.2%) buckets — no `Light`/`Medium-Light` rows. The remaining 142/227 samples have no computed skin tone (Section 4). |
| Papuan faces | Author-stated observed subgroup/context | **Narrative only** — no field in any dataset CSV encodes ethnicity, Papuan identity, or population subgroup. The association is asserted in `Tesis_Knowledge_Transfer_(1).md` (author's own notes), not encoded as queryable metadata. |
| Labeling pipeline | Dataset construction methodology | Confirmed and validated — `src/fer_dataset/pipeline/` (frame extraction → face detection → HSEmotion pseudo-labeling → dataset build → landmark/feature extraction), with the annotation-alignment bug fixed and validated (Phase 9/9B, `docs/RESEARCH_EVIDENCE_AUDIT.md` §9). |
| Baseline FER evaluation | Main performance evidence | Confirmed — overall accuracy 0.2247, error rate 0.7753 (`notebooks/data_audit.ipynb` cell 5). |
| False-Angry analysis | Observed error phenomenon | Confirmed and is the most concrete, well-evidenced finding in the repository (Section 4). |
| Skin-tone analysis | Supporting bias/fairness analysis | Confirmed as descriptive evidence only (accuracy/false-Angry-rate by bucket); not statistically validated. |
| CLAHE | Potential intervention/preprocessing experiment | Already tested once (Strategy B); result was negative (Section 4). |
| Landmark analysis | Exploratory explanatory analysis | Descriptive only; one key comparison (true-Angry geometry) has n=1 and is not usable as evidence (Section 4). |

---

## 4. Existing Evidence

### Dataset
- **Source**: `pesta_babi.mp4`, a single documentary video (`config/config.yaml`).
- **Samples**: 227 face crops with manual ground-truth labels (`data/1408-1010-intermediate/manual_labels_export.csv`). A separate, larger debug/baseline run (`docs/baseline_snapshots/phase0/`) processed a 100-frame subset of the same or a similarly-configured run, yielding the same 227-face-crop count — the manually-labeled set and the pipeline's debug baseline appear to be the same population (same counts, same label distribution pattern), though the repository does not explicitly state this equivalence.
- **Labeling process**: two-stage — (1) automatic HSEmotion pseudo-labeling during pipeline execution, (2) manual review producing `gt_label` in `manual_labels_export.csv` (227 rows, each with `gt_label`, `model_label`, `confidence`, `notes`, `labeled_at`).
- **Skin-tone information**: computed only where MediaPipe landmark detection succeeded — **85 of 227 rows (37.4%)**. Within that subset: **Dark = 50, Medium-Dark = 35** (58.8% / 41.2% **of the 85**, not of the full 227). The skin-tone profile of the other 142 rows is unknown, not zero, not assumed to match the 85-row subset.
- **Known limitations**: no ethnicity/identity metadata field exists in any CSV; skin-tone coverage is partial (37.4% of labeled samples); the ground-truth label set includes an `Ambiguous` category (visible in `manual_labels_export.csv`/`gt_label` values) not documented in `docs/SDD.md`'s 7-label list, indicating some faces were not confidently labelable even manually.

### FER Performance
- Overall accuracy: **0.2247**; error rate: **0.7753** (`notebooks/data_audit.ipynb` cell 5; `reports/audit_summary_metrics.csv`).
- Confusion matrix exists as an image (`reports/assets/audit_confusion_matrix.png`); no derived per-class precision/recall/F1 table exists.
- Confidence behavior: mean confidence correct = 0.5035, wrong = 0.4418; true-Angry = 0.4194, false-Angry = 0.5968 — the model is descriptively *more* confident when incorrectly predicting Angry than when correctly predicting it (`notebooks/data_audit.ipynb` cell 13).

### False-Angry Phenomenon
- **Neutral → Angry**: 18 cases — the single largest contributor to the 40 total false-Angry predictions (`notebooks/data_audit.ipynb` cell 11 output).
- **Other sources**: Happy→Angry 8, Sad→Angry 6, Ambiguous→Angry 3, Fear→Angry 3, Surprise→Angry 2 (same source).
- **Overall false-Angry rate**: 0.1762 (40/227).
- **Papuan identity/group information**: **not explicitly available** in any dataset field. The observation "Papuan faces show a tendency toward Neutral→Angry false detection" is the **author's own observation** (stated in this task's context and in `Tesis_Knowledge_Transfer_(1).md`'s narrative), not something the current numerical analysis can independently confirm, because there is no per-sample ethnicity/subgroup label to test it against. What the repository **does** quantitatively demonstrate is: (a) a Neutral→Angry misclassification pattern exists in this dataset, and (b) this dataset is sourced from a video the author describes as depicting a Papuan population. The repository **cannot** currently distinguish "this pattern is specific to Papuan faces" from "this pattern would occur on any dark-skinned population this model was evaluated on" from "this pattern is specific to this video's lighting/framing/expression style" — these are three different explanations, only the first of which matches the author's framing, and none of which the current metadata can adjudicate between.

### Skin-Tone Analysis
- Accuracy: Dark 0.44, Medium-Dark 0.1429; fairness gap (max−min) 0.2971 (`reports/audit_per_skin_tone_accuracy.csv`).
- False-Angry rate: Dark 0.22, Medium-Dark 0.4571, with group sizes 11 and 16 (of 40 false-Angry rows) respectively (`notebooks/data_audit.ipynb` cell 11).
- No statistical test, effect size, or confidence interval computed anywhere.
- **Can skin tone function as a proxy for the "dark-skinned research population"?** Reasonably, yes, for the narrow claim that all 85 characterized samples are non-light-skinned (no `Light`/`Medium-Light` rows exist). It cannot function as a proxy for "Papuan" specifically — skin-tone bucket (a LAB-luminance-derived heuristic, `src/fer_dataset/pipeline/landmark_analyzer.py:118-137`) is not an ethnicity indicator, and no independent ethnicity variable exists to check the two against each other.

### CLAHE
Strategy B CLAHE (adaptive, skin-tone-dependent clip limit) was tested once: accuracy 0.2247→0.1982 (−0.0264), false-Angry rate 0.1762→0.1806 (+0.0044), Medium-Dark false-Angry rate unchanged (0.3538→0.3538). Hypothesis (CLAHE improves fairness/reduces false-Angry) **not supported** (`reports/preprocessing_experiment_summary.csv`; `notebooks/preprocessing_experiment_executed.ipynb`).

### Landmark Analysis
- Predicted-label-based (Angry n=28 vs. Neutral n=29): overlapping descriptive geometry, e.g. brow_lowering_distance 0.131 vs. 0.147 (`reports/landmark_comparison_summary.csv`).
- Ground-truth-based (true-Angry n=**1** vs. false-Angry n=27): not usable as evidence given the n=1 group; the notebook's own output states the hypothesis is unsupported in-sample (`notebooks/data_audit.ipynb` cell 15).
- No statistical layer exists for either comparison.

---

## 5. Evidence Limitations

- **ArcFace discrepancy**: the author's stated method (ArcFace-based FER) does not match the implemented pipeline (HSEmotion for classification; ArcFace-architecture weights present only incidentally, for face embedding, inside the InsightFace bundle, and not used for expression output). This must be reconciled before any RQ naming ArcFace as the FER method can be considered accurate to the current implementation.
- **No ethnicity metadata**: any claim connecting the observed error pattern to "Papuan faces" specifically is not currently testable from repository data — it is an author observation, not a data-encoded, statistically checkable variable.
- **Partial skin-tone coverage**: 62.6% of labeled samples (142/227) have no computed skin tone; all skin-tone-based conclusions currently describe only the other 37.4%.
- **Small subgroups**: Medium-Dark false-Angry group n=16, Dark n=11 (of 40); true-Angry landmark group n=1 — several existing comparisons rest on group sizes too small for confident generalization.
- **No statistical validation anywhere**: every quantitative comparison in the repository (accuracy by group, confidence by correctness, geometry by group) is a raw descriptive comparison with no test, effect size, or interval.
- **Dataset scale**: a single source video, 227 labeled faces — generalization beyond this specific video/session is not evidenced.

---

## 6. Candidate Research Questions

None of the following is an official thesis RQ. Each is a candidate framing derived from the author's stated intent plus existing evidence.

### Candidate A — Performance-focused
**RQ wording**: "How accurately does an off-the-shelf FER pipeline (InsightFace/ArcFace-based detection + a pretrained expression classifier) recognize facial expressions in a dark-skinned Papuan population, as evaluated against manually-verified ground truth?"
- **Investigates**: raw model performance on the target population.
- **Existing evidence supporting it**: overall accuracy (0.2247), error rate (0.7753), full confusion matrix — already complete.
- **Missing evidence**: per-class precision/recall/F1; comparison against any published baseline accuracy on a more balanced/mainstream dataset (no such comparison exists in-repository).
- **Required experiments**: none new — largely a reporting/derivation task from existing confusion-matrix data.
- **Risk/limitation**: doesn't address the specific Neutral→Angry phenomenon the author flagged as a key motivation; risks being too generic to constitute a full thesis contribution alone.

### Candidate B — Error-analysis-focused
**RQ wording**: "What are the characteristic misclassification patterns of an off-the-shelf FER model on this dataset, and to what extent is the Neutral→Angry confusion the dominant failure mode?"
- **Investigates**: the specific, already-observed error phenomenon motivating the research.
- **Existing evidence supporting it**: complete false-Angry breakdown (18/8/6/3/3/2 by true class), confidence-vs-correctness analysis, confusion matrix — the strongest, most complete evidence thread in the repository.
- **Missing evidence**: per-class precision/recall/F1; statistical characterization of whether Neutral→Angry is significantly more frequent than other confusions (currently only the largest raw count, not tested); no geometric/causal explanation currently holds up (Section 4, Landmark Analysis).
- **Required experiments**: none new for the core finding; a stronger analysis (not a new experiment) would derive per-class metrics and rank confusion pairs formally.
- **Risk/limitation**: does not by itself connect to the "dark-skinned"/"ArcFace" framing unless explicitly paired with Candidate A or C.

### Candidate C — Bias/fairness-focused
**RQ wording**: "Does FER model performance (accuracy, false-Angry rate) differ across skin-tone subgroups within this dataset?"
- **Investigates**: the fairness/bias framing the author explicitly asked not to default to as the *main* framing, but which has the most complete existing evidence.
- **Existing evidence supporting it**: per-skin-tone accuracy and false-Angry rate, fairness gap — already computed.
- **Missing evidence**: statistical test/effect size/CI; sample-size transparency; coverage of only 2 of the population's presumed skin-tone range (no light-skin comparison group exists or is likely relevant given the population, which limits this to a within-population, not a cross-population, fairness claim).
- **Required experiments**: none new; statistical validation of existing numbers.
- **Risk/limitation**: per the author's explicit instruction, should not be the default/primary framing; also cannot support a *cross-population* fairness claim (e.g., vs. light-skinned faces) since no such comparison group exists in this dataset.

### Candidate D — Combined
**RQ wording**: "How does an off-the-shelf FER pipeline perform on a dark-skinned Papuan population sourced from documentary video, what is the dominant error pattern, and is that pattern associated with within-population skin-tone variation?"
- **Investigates**: performance (A) + error pattern (B) + within-population association (C, as a secondary/supporting analysis, not the primary framing) — matches the author's stated intent most closely (dark-skinned FER as primary, Neutral→Angry as key motivating observation, skin-tone as supporting, not central, analysis).
- **Existing evidence supporting it**: all of the above (Sections 3–4) — this is the only candidate for which essentially all currently-collected evidence is directly relevant, none of it needing to be discarded as off-topic.
- **Missing evidence**: same as A+B+C combined — per-class metrics, statistical validation, ArcFace/HSEmotion reconciliation, ethnicity-metadata gap.
- **Required experiments**: none new for a first pass; statistical hardening of existing descriptive results.
- **Risk/limitation**: broader scope requires being disciplined about which sub-question is primary (performance/error pattern) vs. supporting (skin-tone) in the actual thesis narrative, to avoid diluting the contribution.

### Candidate E — Method-reconciliation-focused
**RQ wording**: "What role does an ArcFace-based face representation play in this FER pipeline's detection and error behavior, and does it need to be more directly incorporated into the expression-classification step?"
- **Investigates**: directly addresses the ArcFace discrepancy (Section 5) — currently ArcFace-architecture weights are loaded but not used for expression output.
- **Existing evidence supporting it**: none yet — this is the least evidenced candidate; the discrepancy itself is evidence that this question is currently *unanswered*, not that it's supported.
- **Missing evidence**: essentially all of it — no experiment currently uses ArcFace embeddings for expression-related analysis.
- **Required experiments**: a genuinely new experiment would be needed (e.g., using ArcFace embeddings as classifier input/features) — this is the only candidate that requires new modeling work rather than analysis of existing data.
- **Risk/limitation**: highest effort, most divergent from what's already been evidenced; only worth pursuing if the author's mention of "ArcFace" was meant literally as the intended FER method rather than an imprecise reference to the InsightFace detection pipeline already in use.

---

## 7. Recommended Candidate RQ

> **Recommended Candidate RQ — NOT YET OFFICIAL**
>
> Candidate D (Combined): *"How does an off-the-shelf FER pipeline perform on a dark-skinned Papuan-sourced dataset, what is the dominant error pattern, and is that pattern associated with within-population skin-tone variation?"* — with performance and error-pattern analysis as the **primary** contribution and skin-tone association as a **secondary, supporting** analysis (explicitly not the primary framing, per the author's instruction).

**Why recommended:**
1. **Author's stated intent**: most directly matches "FER for dark-skinned faces" (primary) plus the explicitly-mentioned Neutral→Angry observation (key motivation), while keeping skin-tone/fairness as supporting rather than central — exactly the structure the author asked for.
2. **Existing evidence**: this is the only candidate where essentially all already-collected evidence (baseline accuracy, confusion matrix, confidence analysis, skin-tone breakdown) is directly usable without being off-topic or requiring new experiments to even be relevant.
3. **Feasibility**: requires no new data collection or modeling — the remaining work (Section 9) is analysis-strengthening (per-class metrics, statistical validation), not new experimentation.
4. **Scientific coherence**: keeps the causal/associative distinctions clean — performance and error pattern are directly measured; skin-tone is explicitly framed as an association to investigate, not a proven cause, consistent with what the evidence actually supports (Section 4).
5. **Defensible contribution**: a combined performance + error-characterization result on an under-represented population, with an honest secondary association analysis, is a more defensible thesis contribution than either an under-evidenced ArcFace-integration question (Candidate E) or an over-narrow single-axis question (A, B, or C alone).

This recommendation does **not** resolve the ArcFace discrepancy (Section 5) — that must still be confirmed with the advisor (Section 11) regardless of which candidate is chosen, since it affects how the "method" component of any RQ should be worded.

---

## 8. RQ → Evidence → Gap Mapping

For the recommended candidate (Section 7):

| Research Question Component | Existing Evidence | Missing Evidence |
|---|---|---|
| Target population | 85/227 samples characterized as Dark/Medium-Dark skin tone; video source described by author as Papuan documentary | No ethnicity/identity metadata; 142/227 samples uncharacterized for skin tone |
| Dataset | 227 manually-labeled face crops from `pesta_babi.mp4`, pipeline-validated construction | Population/demographic documentation beyond the author's narrative description |
| Model | HSEmotion (`enet_b0_8_best_vgaf`) for classification; InsightFace/`buffalo_l` (ArcFace-architecture recognition component included but unused for expression) for detection | Reconciliation of "ArcFace" as stated method vs. actual implementation (Section 5) |
| Baseline performance | Overall accuracy 0.2247, error rate 0.7753, full confusion matrix | Per-class precision/recall/F1 |
| Error pattern | Complete false-Angry breakdown by true class (18/8/6/3/3/2), confidence-vs-correctness analysis | Formal ranking/significance of confusion pairs beyond raw counts |
| Skin-tone relationship | Accuracy and false-Angry rate by bucket, fairness gap (descriptive) | Statistical test/effect size/CI; sample-size transparency |
| Statistical validation | None | Needed for every quantitative claim above before thesis-level presentation |
| Intervention | CLAHE tested once, negative result | Not required to answer this recommended RQ (intervention was for a different, narrower question); would only become relevant if the thesis scope is later extended to "can this be mitigated" |

---

## 9. Required Research Work

Classified against the recommended candidate (Section 7):

### Already sufficient
- Baseline overall accuracy/error rate.
- Confusion matrix (raw).
- False-Angry breakdown by true class.
- Confidence-vs-correctness descriptive comparison.

### Needs stronger analysis (no new data collection)
- Per-class precision/recall/F1 (derivable from the existing confusion matrix).
- Statistical test + effect size + CI for the skin-tone accuracy/false-Angry-rate differences (data already collected; only the analysis layer is missing).
- Explicit tabulation of exact sample sizes behind every subgroup metric.

### Requires new experiment
- None identified as *necessary* to answer the recommended RQ. Specifically:
  - **Additional CLAHE experiments**: not necessary for this RQ — CLAHE addressed a narrower "can preprocessing fix this" question, which is not part of the recommended framing's core; only relevant if the thesis scope is explicitly extended to interventions.
  - **Additional ArcFace configurations**: only necessary if Candidate E (or an ArcFace-inclusive rewording of the method component) is confirmed with the advisor as intended; not necessary for Candidate D as recommended.
  - **Landmark analysis**: not necessary for this RQ as framed; the existing geometric evidence is too weak (n=1 in the key comparison) to serve as core evidence and was already found inconclusive by the notebook's own output.

### Exploratory only (keep, but do not present as core evidence)
- CLAHE experiment (already completed, negative — valuable as a documented ruled-out approach, not as an answer to the recommended RQ).
- Landmark geometry comparisons (both variants) — illustrative at most, given sample-size and statistical-validation gaps.

---

## 10. Candidate Thesis Contributions

> **Candidate Contribution — requires author/advisor validation.** None of the following is asserted as a novel or final contribution.

1. **Empirical evaluation contribution**: a documented, reproducible evaluation of an off-the-shelf FER pipeline's accuracy and error behavior on a dark-skinned, Papuan-sourced video dataset — a population likely underrepresented in standard FER benchmarks (this underrepresentation is a reasonable inference from general FER literature context, not something this repository's evidence independently establishes).
2. **Error-characterization contribution**: a specific, quantified characterization of a Neutral→Angry misclassification pattern in this population, including its relationship to prediction confidence (the model is more confident, not less, when making this specific error) — a concrete, evidence-backed finding distinct from generic accuracy reporting.
3. **Dataset/pipeline contribution**: the semi-automatic dataset-generation and labeling pipeline itself (frame extraction → detection → pseudo-labeling → manual verification → landmark/feature extraction), now validated for correct annotation lineage (Phase 9/9B) and reproducibility (`docs/RESEARCH_EVIDENCE_AUDIT.md` §9) — a methodological/infrastructure contribution, distinct from the empirical findings above, and one that should be described as infrastructure supporting the research, not as the primary scientific finding, per the Section 7 recommendation's emphasis.

---

## 11. What Must Be Confirmed With Advisor

1. **The actual, official thesis RQ** — none of Candidates A–E should be treated as settled without the author's/advisor's confirmation.
2. **The ArcFace discrepancy** — whether "ArcFace" in the intended research direction refers to the FER classifier (not currently implemented) or to the InsightFace detection/embedding step already in use (which does include ArcFace-architecture weights, unused for expression output) — this materially changes both the method description and whether Candidate E's new-experiment work is needed.
3. **The Papuan-specificity claim** — whether the thesis intends to claim a Papuan-specific effect (which would require ethnicity metadata not currently present, or an explicit scoping caveat that this cannot be tested with current data) or a more general dark-skinned-population effect (which the current skin-tone data can more directly support).
4. **The "100% dark skin" narrative claim** (carried over from R2, `docs/THESIS_RQ_ALIGNMENT.md` §4) — still unresolved; the 58.8%/41.2% Dark/Medium-Dark split applies only to the 85/227 characterized subset.
5. **Whether skin-tone/fairness analysis should remain secondary** in the final thesis narrative, consistent with the author's explicit instruction in this phase not to default to a fairness framing — this should be reconfirmed once a formal RQ is drafted, since it's easy for a "combined" framing (Candidate D) to drift toward fairness-as-primary during writing.

---

## 12. Source Traceability

- Author-provided research direction and observed phenomenon (this task's context — not an independently verifiable repository file, reproduced verbatim in Section 1)
- `docs/RESEARCH_EVIDENCE_AUDIT.md` (R1, in full)
- `docs/THESIS_RQ_ALIGNMENT.md` (R2, in full)
- `Tesis_Knowledge_Transfer_(1).md` (§15)
- `config/config.yaml` (`video.path: data/raw/videos/pesta_babi.mp4`)
- `data/1408-1010-intermediate/manual_labels_export.csv` (227 rows, `gt_label`/`model_label`/`confidence`/`notes`/`labeled_at` schema, including an `Ambiguous` gt_label value)
- `data/1408-1010-intermediate/landmark_features.csv` (85 rows, skin-tone distribution: Dark 50/58.8%, Medium-Dark 35/41.2% of the 85)
- `notebooks/data_audit.ipynb` (cells 3, 5, 7, 9, 11, 13, 15 — source and stored outputs)
- `notebooks/preprocessing_experiment_executed.ipynb` (cells 9, 11, 13, 19 — frozen historical outputs)
- `reports/audit_summary_metrics.csv`, `reports/audit_per_skin_tone_accuracy.csv`, `reports/preprocessing_experiment_summary.csv`, `reports/landmark_comparison_summary.csv`
- `src/fer_dataset/pipeline/emotion_classifier.py` (confirms HSEmotion, not ArcFace, is the expression classifier)
- `src/fer_dataset/pipeline/face_detector.py` (confirms InsightFace `buffalo_l` bundle, including `w600k_r50` "recognition" (ArcFace-architecture) weights, used for detection/embedding only)
- `src/fer_dataset/pipeline/landmark_analyzer.py` (skin-tone bucket definitions and computation, lines 118-137)
- Repository-wide text search (this session) for: ArcFace, Papua, Papuan, ethnicity — confirmed no dataset field encodes ethnicity/Papuan identity; "Papua"/"Papuan" appear only in `Tesis_Knowledge_Transfer_(1).md`'s narrative text.
