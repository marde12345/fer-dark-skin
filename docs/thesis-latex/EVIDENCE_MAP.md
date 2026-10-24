# Evidence Map — Thesis Claims to Source Artifacts

Every empirical claim in `chapters/04-results-and-discussion.tex` is listed here with its exact source. This map exists so a future reader can verify any number in the thesis without re-deriving it.

| Thesis location | Claim | Source artifact(s) | Registry entry | Evidence class |
|---|---|---|---|---|
| Ch.4 §RQ1 (`sec:rq1-results`) | HSEmotion baseline accuracy 22.47%, $N=227$ | `reports/audit_summary_metrics.csv`; `docs/EXPERIMENT.md` | `EXPERIMENT_REGISTRY.md` EXP-005 | Verified |
| Ch.4 §RQ1 | Skin-tone-proxy gap 29.71pp (Dark 44.00% / Medium-Dark 14.29%) | `reports/audit_per_skin_tone_accuracy.csv` | EXP-005 | Verified, but see D-8 below — not independently corroborated by EXP-006 |
| Ch.4 §RQ1 | EXP-006's conflicting "before" breakdown (Dark 27.67%, Medium-Dark 10.77%) | `reports/preprocessing_experiment_summary.csv` via `docs/EXPERIMENT.md` EXP-006 entry | EXP-006 | Verified as reported; **conflicts with EXP-005's figures above — see `DATA_DISCREPANCIES.md` D-8, unresolved** |
| Ch.4 §RQ2 (`sec:rq2-results`) | CLAHE accuracy 19.82% (vs. 22.47%), single uncontrolled run | `docs/EXPERIMENT.md` EXP-006 entry | EXP-006 | Verified; no significance test exists for this delta |
| Ch.4 §RQ3 (`sec:rq3-results`) | HSEmotion 36.30% vs. ArcFace+LR 40.74% accuracy, $N=135$ | `reports/arcface_evaluation/comparison_metrics.csv` | EXP-007 | Verified |
| Ch.4 §RQ3 | McNemar $p=0.4614$ (46 discordant pairs) | `reports/arcface_evaluation/statistical_tests.csv` | EXP-007 | Verified; absence of significance, not equivalence |
| Ch.4 §RQ1/RQ3 | Fisher's exact OR=5.88, $p=0.0027$ | `reports/arcface_evaluation/statistical_tests.csv` | EXP-005/EXP-007 | Verified; association, not causation |
| Ch.4 §RQ3 | Neutral-error distribution (HSEmotion concentrated, ArcFace+LR distributed) | `reports/arcface_error_analysis/neutral_error_analysis.csv` | EXP-007 | Verified |
| Ch.4 §Papuan V2 status | 645 pilot crops, 150-image annotation subset, 75-image overlap, 24-image CVAT pilot | `docs/reports/PAPUAN_V2_CURRENT_STATE.md`, `experiments/EXP-PAP-00{1,2,4,5}/` | EXP-PAP-001/002/004/005 | Verified (counts) / Unresolved (annotation completion, see D-1) |
| Ch.3 | 227→135 subset derivation and provenance (legacy, not Papuan V2) | `docs/EXP-007_ARCFACE_EVALUATION.md` §2 (227/178/144/135 checkpoint counts, `face_filename` join); `docs/ARCFACE_EXPERIMENT_DESIGN.md` (prescribed filter order) | — | `DATA_DISCREPANCIES.md` D-2 — **Resolved** (provenance + arithmetic); row-level sample-identity list for the final 6 exclusions remains unverified |
| (absent — deliberately not in Ch.4) | FER2013/ResNet18 "Experiment B" figures | **No artifact exists in this repository** | EXP registry, "Not Found" entry | `DATA_DISCREPANCIES.md` D-0 |

For the full dataset lineage behind each row, see `research-audit/DATA_LINEAGE.md`; for the complete experiment-by-experiment record, see `research-audit/EXPERIMENT_REGISTRY.md`; for every known conflict or gap, see `research-audit/DATA_DISCREPANCIES.md`; for the confirmed scope decisions (FER as primary objective, landmarks as supporting/future work, N=135 provenance) underlying this map, see `RESEARCH_DECISIONS.md`.
