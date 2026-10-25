# Outstanding Thesis TODOs (Prioritized)

**Resolved since the previous revision (2026-10-09):**
- FER confirmed as the primary objective, with landmarks as supporting/future work; N=135 provenance and derivation arithmetic resolved (`RESEARCH_DECISIONS.md` Decisions 1–3).
- Fairness evaluation adopted as the direction, as relayed by the author (`RESEARCH_DECISIONS.md` Decision 5); Chapters 1–5, title, and abstracts revised to the fairness RQs, using EXP-010/011 (`docs/EXP-010_FAIRNESS_135.md`, `docs/EXP-011_CLAHE_FAIRNESS_135.md`).
- **D-8 resolved:** the two skin-tone breakdowns cover different populations (85 vs. 227 crops), not a calculation error (`research-audit/D8_SKIN_TONE_DISCREPANCY_INVESTIGATION.md`).
- **D-1 resolved:** Annotator A 150/150 confirmed from `human_labels.csv` and `label_studio_export.csv`; `annotator_progress.json` is stale (`research-audit/DATA_DISCREPANCIES.md` D-1).
- Landmark pilot human review done for 64 images (24 pilot + 40 calibration; `experiments/EXP-PAP-005/`).
- Manuscript compiles with XeLaTeX + BibTeX (2026-10-25, binaries in `/Library/TeX/texbin`, not on PATH): 0 errors, no undefined references; 3 pre-existing overfull-box warnings remain.
- Citations corrected/added and verified: `li2020deeper` (cross-dataset bias), `buolamwini2018gender` (gender classification), `zuiderveld1994clahe`, `sagawa2020dro`, `mcnemar1947note`, `dietterich1998approximate`, `kunsch1989jackknife`.

**Still open:**

1. **Obtain Pak Fadhil's approval of the RQ wording and thesis title** (`chapters/01-introduction.tex` §1.5, `config.tex`), including whether to name "Papua" in both. Record the approval and its source in `RESEARCH_DECISIONS.md` Decision 5.
2. **Verify data provenance/consent** for the source film — unresolved and outside the scope of any technical step; also decide publication privacy measures (anonymized figures, aggregate-only results).
3. **Complete the front matter:** `frontmatter/declaration.tex` placeholders (statement, date, name, NIM), `\ThesisApprovalDate` in `config.tex`, abbreviation page numbers (`frontmatter/abbreviations.tex`), and the acknowledgements `\TODO` (Pak Arry's full name and title).
4. **Expand both abstracts to the guideline's 500–800 words** (currently about 290–310 words), after item 1.
5. **Re-verify the row-level identity of the 6 alignment-failure exclusions** within the N=135 subset against the raw `classifier_predictions.csv`, if a fully closed derivation is required (`research-audit/DATA_DISCREPANCIES.md` D-2).
6. **Independently verify the 5 "requires verification" sources** listed at the end of `chapters/02-literature-review.tex` before citing any of them.
7. **Check the Zuiderveld (1994) page range** (474–485) against the printed *Graphics Gems IV*; currently confirmed only by secondary sources (see the `references.bib` note).
8. **Decide the continuation status of the Papuan V2 emotion-label track** (Annotator B 0/75; no inter-annotator agreement).
9. **Record exact package/model-weight versions** (from `pyproject.toml`/`uv.lock`) against each experiment in `REPRODUCIBILITY.md`.
10. **Confirm the current ITB formatting rules**: only the 2017/2019 guide and template in this directory were found; the official ITB-SPs CSL is not applied (`apalike` substitute; see `README.md` "Formatting Assumptions").
11. **Optional:** trim Chapter 4 §4.1, which repeats Chapter 3 §3.3.5.

Locate this file's companions for full detail: `README.md` (status/build), `RESEARCH_DECISIONS.md` (confirmed scope), `EVIDENCE_MAP.md` (claim→source), `REPRODUCIBILITY.md`, and `research-audit/DATA_DISCREPANCIES.md`.
