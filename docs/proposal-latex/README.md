# Proposal LaTeX — Document Skeleton

## Purpose

This directory holds the future LaTeX source of the thesis research proposal. **It is currently a document-architecture skeleton only — not a draft proposal and not ready for submission or review as content.** It was created as a controlled adjustment inserted before Phase 5 (Design Requirements) of the proposal-design workflow, to establish the proposal's chapter structure while the underlying research-design decisions are still open.

Nothing in this directory should be read as a finalized claim. Every chapter contains `\TODO{...}` markers (rendered visibly, in red, if compiled) or `\textbf{[...]}` placeholders wherever a decision has not yet been made.

## What Is Deliberately Not Here Yet

Per the current state of `docs/proposal/` (see the audit and RQ-options documents below), the following are **not finalized** and must not be treated as settled by anything in this directory:

- **Official Research Question** — `docs/proposal/research/RQ_OPTIONS.md` lists 5 non-final candidate RQs and a decision-support memo recommending a working direction (Structure A+B: FER performance/error characterization as primary, skin-tone-stratified analysis as secondary). No RQ has been selected by the user or supervisor.
- **Final artifact** — Chapter 4 (`chapters/04_proposed_design.tex`) explicitly does **not** define "ArcFace + Logistic Regression" as the artifact. Per the guideline, artifact form is a consequence of a requirements analysis that has not yet been performed (Phase 5/6 of `docs/proposal/`).
- **Design requirements** — Phase 5 has not been executed.
- **Research methodology** (DSRM/DRM/other) — Phase 7 has not been executed.
- **Novelty claim** — the literature review (`docs/proposal/research/STATE_OF_ART_AND_GAP.md`) found that ArcFace-as-feature-extractor for FER is **not** novel as a technique (already published by Altaha et al. 2023 and Waldner & Mitra 2024). This is stated plainly in Chapter 2 — do not soften or omit it in any future draft.

## Source Markdown Documents

Every chapter's content, once written, must trace back to one of these — never to invented material:

| Document | Covers |
|---|---|
| `docs/proposal/guideline/PROPOSAL_GUIDELINE_EXTRACTION.md` | Pak Arry's design-research guideline, extracted with page citations (Phase 0) |
| `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md` | Current thesis state vs. guideline requirements (Phase 1) |
| `docs/proposal/research/PROBLEM_ARCHITECTURE.md` | Solution-neutral problem chain, evidence, claims-we-can/cannot-make (Phase 2) |
| `docs/proposal/research/STATE_OF_ART_AND_GAP.md` | Literature review, gap analysis, ArcFace novelty check, skin-tone gap check (Phase 3) |
| `docs/proposal/research/RQ_OPTIONS.md` | 5 candidate RQs, quality/solution-neutrality/data-answerability tests, non-final shortlist (Phase 4) |
| `docs/RESEARCH_FINDINGS.md`, `docs/R9_FINAL_STATISTICAL_VALIDATION.md` | Existing R1–R9 experimental evidence (already obtained, cited as such — never as future proposal results) |

Every `.tex` file in `chapters/` carries `% Source: ...` comments at the top and inline, pointing to the specific Markdown document/section a future draft must pull from. These comments are for traceability only and do not render in the compiled PDF.

## Template Status

**No official ITB/department LaTeX class or template was found anywhere in this repository** at the time this skeleton was created (searched for `*.cls`, `*.sty`, filenames containing "itb", and any pre-existing `.tex` file — none exist). `main.tex` uses the standard LaTeX `report` class as a neutral placeholder base. **When the official ITB thesis/proposal template becomes available, `main.tex`'s preamble (document class and packages) should be swapped to match it — the chapter content structure in `chapters/` should not need to change.**

## How to Compile

```
cd docs/proposal-latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

**Compilation was not validated in this environment.** No LaTeX toolchain (`pdflatex`, `xelatex`, or `lualatex`) is installed here — this was checked directly (`which pdflatex xelatex lualatex` all returned not-found, and `kpsewhich` is unavailable). The document was written to standard, conservative LaTeX (`report` class, `natbib`, `booktabs`, `hyperref`, `graphicx`, `amsmath` — all common, stable packages) and every `\input`/`\cite`/`\label`/`\ref` was manually cross-checked against the files that exist:
- All 5 `\input{chapters/...}` targets in `main.tex` exist.
- Every `\citep`/`\cite` key used in `chapters/02_literature_review.tex` (`deng2019arcface`, `li2020deep`, `mollahosseini2017affectnet`, `buolamwini2018gender`, `altaha2023facial`, `waldner2024pairwise`, `chhua2024bias`) has a matching entry in `references.bib`.
- No `\ref{}` targets a `\label{}` that doesn't exist.

This is a manual consistency check, not a substitute for an actual compile. **Please compile locally (or in Overleaf) before relying on this structure**, and report back if anything fails — do not assume it compiles cleanly on first try.

## What Is Still Pending Supervisor/Research-Design Decisions

- Which candidate RQ (or which structure — A, B, or A+B) becomes official (`docs/proposal/research/RQ_OPTIONS.md`, "Decision Required").
- Whether ArcFace's role in the eventual thesis is as one evaluated face-representation approach (per the current working direction) or is dropped/expanded — this affects Chapter 2 §ArcFace and Chapter 4 entirely.
- Whether the skin-tone secondary analysis (Chapter 5 §Skin-Tone-Stratified Analysis) should also incorporate the N=227 historical population's separate skin-tone breakdown, or remain scoped to the N=135 common subset only.
- Resolution of the 5 literature citations flagged "requires verification" (listed in Chapter 2's "Citations Requiring Verification" section and at the bottom of `references.bib`) before they can be cited in a final draft.
- Design Requirements (Phase 5) and Artifact Architecture (Phase 6), which this skeleton deliberately leaves as `\TODO{}` placeholders in Chapter 4.
- Methodology selection (Phase 7), left as a placeholder in Chapter 3.
- The ethics content gap flagged in `docs/proposal/validation/PROPOSAL_GUIDELINE_AUDIT.md` (data provenance/consent for the source film, face-crop data handling policy, misuse-risk statement) — Chapter 3 §Ethical Considerations flags this explicitly rather than treating it as a formality.
