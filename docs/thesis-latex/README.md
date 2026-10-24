# Thesis LaTeX — Initial Draft Manuscript

## Purpose

This directory holds the LaTeX source of the **formal Master's thesis manuscript** (Smart Systems, Institut Teknologi Bandung). It is a separate deliverable from, and must not be confused with, `docs/proposal-latex/` (the **research proposal** skeleton) or `docs/proposal/` (the proposal-design working documents). A thesis and a proposal are different documents with different audiences and different completeness expectations; this directory is new and does not modify either of those.

**Status: revised draft manuscript, not a final/defensible thesis.** Every chapter contains substantive prose grounded in this repository's existing evidence. As of this revision (2026-10-09), the author has confirmed: facial emotion classification (EXP-005/006/007) is the primary research objective; the facial-landmark track is supporting/future work; the $N=135$ subset's provenance and derivation are resolved; and the Research Question is structured as one primary question with three sub-questions (RQ1 baseline, RQ2 CLAHE, RQ3 ArcFace comparison), each tied to its own population (227 crops for RQ1/RQ2, the derived 135-crop subset for RQ3). See `RESEARCH_DECISIONS.md` Decisions 1–4 for the full record. What remains open is **Pak Fadhil's sign-off** on the RQ1/RQ2/RQ3 wording (Chapter 1, §1.5), and a newly surfaced, unresolved discrepancy (D-8, `research-audit/DATA_DISCREPANCIES.md`) between two independently computed skin-tone-proxy breakdowns for the same nominal baseline condition.

## Structure

## Project Layout: Where to Edit What

The project is split by concern, on purpose, so no single file has to carry everything:

| File | Edit this when you want to... |
|---|---|
| `config.tex` | Fill in your thesis title, author, NIM, supervisors, or approval date. **This is the only file to touch for metadata** — every frontmatter page (title page, Abstrak, Abstract, Halaman Pengesahan, Pedoman Penggunaan Tesis) reads from here instead of repeating its own placeholder, so one edit propagates everywhere. |
| `itb-thesis.sty` | Change margins, fonts, heading sizes/weights, or chapter/figure/table/equation numbering rules. |
| `chapters.tex` | Add, remove, or reorder a **Bab** (chapter). One `\input{chapters/...}` line per Bab. |
| `frontmatter.tex` | Add, remove, or reorder a **frontmatter page** (title page, abstracts, Halaman Pengesahan, etc.). |
| `bibliography.tex` | Change the bibliography style or the `.bib` file referenced — the actual citation entries still live in `references.bib`. |
| `structure.tex` | Almost never. It only wires the three files above together inside `\begin{document}...\end{document}`, in order: frontmatter, chapters, bibliography. |
| `main.tex` | Almost never. It's deliberately thin: `\documentclass`, load `itb-thesis.sty`, `\input{config}`, set `\title`/`\author`/`\hypersetup`, then `\input{structure}`. |
| `chapters/*.tex`, `frontmatter/*.tex` | The actual prose content of each chapter/page. |

```text
docs/thesis-latex/
├── main.tex                        — thin entry point only: documentclass, itb-thesis.sty, \input{config}, \input{structure}
├── config.tex                      — SINGLE SOURCE for title/author/NIM/supervisors/dates — edit this, not main.tex, for metadata
├── structure.tex                   — thin orchestrator: \begin{document} + \input{frontmatter,chapters,bibliography} + \end{document}
├── frontmatter.tex                 — \input order for every frontmatter page (title page through Daftar Singkatan dan Lambang)
├── chapters.tex                    — \input order for every Bab (one line per chapter, points at chapters/*.tex)
├── bibliography.tex                — \bibliographystyle + \bibliography{references} only
├── itb-thesis.sty                  — centralized ITB Juknis-derived formatting (margins, fonts, chapter/figure/table numbering, page-numbering helpers)
├── FORMAT_COMPLIANCE.md            — every applicable guideline mapped to its LaTeX implementation and validation status
├── fc0779-juknis_tesis_Mei2019_rev.pdf — the supplied ITB formatting guide itself (read in full; not authored by this project)
├── template-tesis_Mei2019.docx     — the matching official Word template (its XML was parsed directly, not just opened; see FORMAT_COMPLIANCE.md)
├── references.bib                  — verified bibliography (copied/shared basis with docs/proposal-latex/)
├── latexmkrc                       — latexmk config (xelatex + bibtex; see "LaTeX Compiler and Dependencies")
├── README.md                       — this file
├── RESEARCH_DECISIONS.md           — confirmed author decisions (FER primary, landmarks supporting, N=135 provenance) and their implications
├── EVIDENCE_MAP.md                 — every Chapter 4 claim mapped to its exact source file
├── REPRODUCIBILITY.md              — what can/cannot be reproduced from this repo alone
├── TODO.md                         — prioritized outstanding research/writing items
├── research-audit/                 — evidence-reconstruction audit, produced BEFORE drafting chapters
│   ├── RESEARCH_TIMELINE.md        — chronological reconstruction from the earliest Git history
│   ├── RESEARCH_INVENTORY.md       — canonical list of datasets/code/experiments/annotation artifacts
│   ├── DATA_LINEAGE.md             — raw video → ... → evaluation, for both dataset lineages
│   ├── DATA_DICTIONARY.md          — field-level schema, label mappings, identity/leakage caveats
│   ├── EXPERIMENT_REGISTRY.md      — one canonical entry per experiment ID, never merged by model name
│   ├── DATA_DISCREPANCIES.md       — every known conflict/gap, with RESOLVED/UNRESOLVED/SUPERSEDED/NOT VERIFIABLE status
│   └── D8_SKIN_TONE_DISCREPANCY_INVESTIGATION.md — full recomputation resolving the EXP-005/EXP-006 skin-tone discrepancy
├── chapters/
│   ├── 01-introduction.tex
│   ├── 02-literature-review.tex
│   ├── 03-research-methodology.tex
│   ├── 04-results-and-discussion.tex
│   └── 05-conclusion.tex
├── frontmatter/
│   ├── title-page.tex              — Halaman Judul
│   ├── abstract-id.tex             — Abstrak (page i)
│   ├── abstract-en.tex             — Abstract (page ii)
│   ├── pengesahan.tex              — Halaman Pengesahan / approval page (page iii)
│   ├── pedoman-penggunaan-tesis.tex — Pedoman Penggunaan Tesis / usage notice (page iv)
│   ├── acknowledgements.tex        — Kata Pengantar
│   ├── abbreviations.tex           — Daftar Singkatan dan Lambang
│   └── declaration.tex             — superseded by pengesahan.tex; kept for history, not \input by main.tex
├── figures/                        — final, LaTeX-ready images only; referenced via \includegraphics
├── screenshots-raw/                — staging area for raw screenshots/exports; NOT referenced by any .tex file
└── tables/                         — empty; standalone \input-able table files can go here if a table grows large
```

**Screenshot/figure workflow:** drop new raw screenshots into `screenshots-raw/` first, never directly into
`figures/`. When asked to turn one into a thesis figure, the source file in `screenshots-raw/` is always
**copied** (not moved) into `figures/` under its final name, then cropped/adjusted there — the raw original in
`screenshots-raw/` is left untouched. `figures/` should only ever contain files that are actually referenced by
an `\includegraphics` call somewhere in the document.

## LaTeX Compiler and Dependencies

- Document class: `report` (12pt, A4), formatting delegated to `itb-thesis.sty` — margins (left 4cm/right 3cm/top 3cm/bottom 3cm), `\onehalfspacing`, no-indent/blank-line paragraph style, Roman-numeral chapter numbering with chapter-scoped figure/table/equation numbers, and the roman→arabic page-numbering switch between frontmatter and main body. See `FORMAT_COMPLIANCE.md` for the full page-by-page mapping to the supplied ITB guide.
- **Font**: Times New Roman, per the guide. `itb-thesis.sty` detects the engine: under **XeLaTeX or LuaLaTeX** it loads `fontspec` and sets `\setmainfont{Times New Roman}` — the literal font, **which must be installed on the compiling machine** (not guaranteed; not independently verified here). Under plain **pdfLaTeX** it falls back to `mathptmx`, a Times-metric clone — visually close but not the literal font. **xelatex is the recommended/default engine** for this reason (see `latexmkrc`).
- Bibliography: BibTeX via `natbib[round,authoryear]`, style `apalike` — an unverified substitute for the official ITB-SPs Citation Style Language referenced in the guide (see `FORMAT_COMPLIANCE.md` "References").
- Packages beyond the above: `graphicx`, `booktabs`, `amsmath`/`amssymb`, `hyperref`, `xcolor`, `longtable`, `titlesec`, `iftex` — all standard, widely available, no obscure dependencies.

### How to Compile

```bash
cd docs/thesis-latex
latexmk -pdf main.tex          # latexmkrc invokes xelatex AND sets the
                                # output filename to "23524301_Marde Fasma_FER.pdf"
                                # (see $jobname in latexmkrc) -- not main.pdf.
# or, without latexmk (must pass -jobname explicitly to get the same filename):
xelatex -jobname="23524301_Marde Fasma_FER" main.tex
bibtex "23524301_Marde Fasma_FER"
xelatex -jobname="23524301_Marde Fasma_FER" main.tex
xelatex -jobname="23524301_Marde Fasma_FER" main.tex
# pdfLaTeX fallback (mathptmx instead of literal Times New Roman):
pdflatex -jobname="23524301_Marde Fasma_FER" main.tex && bibtex "23524301_Marde Fasma_FER" && pdflatex -jobname="23524301_Marde Fasma_FER" main.tex && pdflatex -jobname="23524301_Marde Fasma_FER" main.tex
```

**Output filename convention**: the compiled PDF is always named `23524301_Marde Fasma_FER.pdf` (`<NIM>_<nama depan>_<topik>`), matching the naming convention of the reference thesis `23524315_Yogi Putra_PT Pos.pdf`. `latexmkrc`'s `$jobname` enforces this automatically; if compiling manually without latexmk, pass `-jobname="23524301_Marde Fasma_FER"` as shown above so aux/bbl/pdf files stay consistent. If NIM or author name in `config.tex` ever changes, update `$jobname` in `latexmkrc` (and the commands above) to match.

**Compilation status (updated 2026-10-13): actually compiled and visually inspected, not just statically checked.** A real TeX Live 2026 ("basic" scheme) installation exists on this machine at `/usr/local/texlive/2026basic/` — not on the default shell `PATH`, but present. Compiled with:

```bash
export PATH="/usr/local/texlive/2026basic/bin/universal-darwin:$PATH"
xelatex -interaction=nonstopmode -jobname="23524301_Marde Fasma_FER" main.tex
bibtex "23524301_Marde Fasma_FER"
xelatex -interaction=nonstopmode -jobname="23524301_Marde Fasma_FER" main.tex
xelatex -interaction=nonstopmode -jobname="23524301_Marde Fasma_FER" main.tex
```

Result: **41 pages, exit code 0 on all four passes, 0 warnings, 0 undefined references/citations, 0 overfull/underfull-box issues after fixes (see below).** One package, `titlesec`, was missing from the "basic" TeX Live scheme and was installed via `tlmgr --usermode install titlesec` (user-tree only, not system-wide) with explicit authorization. The resulting PDF was read page-by-page, which is how the two defects below were actually found — a static source review could not have caught either:

1. **Bold/italic text wasn't rendering distinctly anywhere** (chapter titles, section headings, italicized bibliography entries all looked like plain weight). Cause: `itb-thesis.sty`'s `fontspec` block mapped `BoldFont=*`/`ItalicFont=*`/`BoldItalicFont=*` all to the same glyph file as the regular weight. **Fixed** by removing those options and letting `fontspec` auto-detect Times New Roman's real Bold/Italic sub-faces. Re-verified: a second compile shows three distinct font instances in the log, and bold/italic now visibly render correctly in the PDF.
2. **4 overfull hboxes** from long unbreakable file-path strings in two places, plus an abbreviations table too wide for the 4cm/3cm margins. **Fixed** with `\allowbreak` insertions and narrower table columns (no wording changed). Re-verified: 0 overfull hboxes in the next compile.

The old `main.pdf` that predated this formatting work has been superseded by this actually-verified build. See `FORMAT_COMPLIANCE.md` for the full row-by-row mapping, now marked "visually verified" wherever this pass actually confirmed it rather than only implementing it on paper.

If recompiling on a different machine: everything `itb-thesis.sty` needs (`fontspec`, `iftex`, `mathptmx`, `titlesec`, `apalike.bst`, `natbib`) must be present in that machine's TeX installation, and Times New Roman must be installed for literal font compliance under `xelatex`/`lualatex` — neither was verified beyond the one machine used for this pass.

### Adding Chapters, Figures, Tables, and References

- **New chapter/section content**: edit the relevant file in `chapters/`; do not add a new top-level chapter file without also adding a corresponding `\input{...}` line in `chapters.tex` (not `main.tex` or `structure.tex` — see "Project Layout" above).
- **Figures**: place image files in `figures/`, reference with `\includegraphics[...]{figures/filename}` inside the relevant chapter, and wrap in a `figure` environment with `\caption{}` and `\label{fig:...}` for cross-referencing.
- **Tables**: small tables can stay inline in the chapter file (see the two tables in `chapters/04-results-and-discussion.tex` for the pattern used so far); a table file in `tables/` should be used only if a table becomes large enough that keeping it in its own file improves chapter readability — do not create empty table files preemptively.
- **References**: add new BibTeX entries to `references.bib` only after independently verifying their metadata (author, title, venue, year) against a primary source (publisher page, DOI, arXiv abstract page, or official dataset documentation). Never invent a reference. See the "Citations Requiring Verification" list at the end of `chapters/02-literature-review.tex` for sources that were identified but not yet verified — resolve those before citing them, rather than adding them speculatively.

## Current Manuscript Status

All five chapters contain substantive initial prose, grounded in this repository's existing documentation and data files (not invented), with explicit `\TODO{}` markers wherever a claim, number, or decision could not yet be verified or finalized. In summary:

- **Chapter 1 (Introduction)**: background, problem formulation, and scope are drafted from evidence. Research Objectives and Research Contributions are grounded in the confirmed scope (FER primary). §1.5 presents a primary RQ plus RQ1/RQ2/RQ3, each scoped to the correct population (227 crops or the derived 135-crop subset) and each disclosing, where relevant, that the underlying experiment predates the question. Awaiting Pak Fadhil's sign-off on wording.
- **Chapter 2 (Literature Review)**: synthesizes the 9 bibliography entries already verified in this repository (ArcFace, HSEmotion, AffectNet, two FER-bias/survey papers, Gender Shades, two ArcFace-for-FER prior-art papers, one FER-bias-in-foundation-models paper); explicitly states that ArcFace-as-FER-feature-extractor is **not** a novel technique (already published by Altaha et al. 2023 and Waldner & Mitra 2024); lists 5 further sources found but not yet independently verified.
- **Chapter 3 (Methodology)**: documents the actual pipeline (SCRFD/InsightFace detection, CLAHE, HSEmotion pretrained inference, ArcFace frozen-embedding feature extraction, Logistic-Regression classifier training, MediaPipe geometric features) and explicitly distinguishes pretrained inference vs. feature extraction vs. classifier training vs. fine-tuning (the last of which never occurs in this project). Documents the Papuan V2 dataset extension and both its emotion-label (Label Studio) and facial-landmark (CVAT) annotation pilots as **incomplete, in-progress** work, not a finished dataset.
- **Chapter 4 (Results and Discussion)**: reports only verified, source-traceable numbers from three completed experiments (HSEmotion baseline, CLAHE ablation, HSEmotion-vs-ArcFace+LR comparison), each with an explicit "what this does/does not establish" subsection. The Papuan V2 section contains **no numeric results** — only a status summary and an explicit `% TODO:` marker for the pending results table. **The FER2013/ResNet18 figures originally supplied as background context for this task (68.57% val / 69.77% test / 68.65% macro-F1 / 69.76% weighted-F1 / 26.96% generalization gap) were not found anywhere in this repository and are not used anywhere in this manuscript** — this repository's experiments do not use FER2013 or ResNet18 at all; if these figures belong to this thesis, their source file must be located and provided before they can be cited.
- **Chapter 5 (Conclusion)**: explicitly provisional; states plainly that Research Questions cannot yet be answered because none is finalized, and lists future work grounded in the actual outstanding items identified above.

## Formatting Assumptions Needing Confirmation

As of this revision, formatting follows two supplied, cross-checked sources: `fc0779-juknis_tesis_Mei2019_rev.pdf` ("Petunjuk Teknis Penulisan Tesis Magister," ITB Sekolah Pascasarjana, Juni 2017) and `template-tesis_Mei2019.docx`, the matching official Word template — see `FORMAT_COMPLIANCE.md` for the complete guideline-to-implementation mapping, including the specific `styles.xml`/`sectPr` values extracted from the `.docx` wherever they could settle a question the PDF's prose left ambiguous (most notably: the real template applies a flat 4cm/3cm/3cm/3cm margin with no `mirrorMargins` set, confirming the simpler variant over the PDF's mirrored-margin prose). **No newer or Smart-System-program-specific ITB template was found anywhere in this repository**; if one exists, it was not available to check against, and these 2017/2019 documents should not be read as confirmed-current policy. No official ITB `.cls`/`.sty` file was found either — `itb-thesis.sty` in this directory is this project's own, unofficial implementation of these two documents' rules, not an ITB-distributed file.

Items still needing confirmation before final submission:
- **The official ITB-SPs Citation Style Language** (`http://www.sps.itb.ac.id/in/csl/`, referenced in the guide) was not fetched or verified — `apalike` is used as a documented, unverified substitute (renders "et al." rather than the guide's Indonesian "dkk.").
- **Times New Roman font availability** on whichever machine eventually compiles this with XeLaTeX/LuaLaTeX — not independently verified; pdfLaTeX's `mathptmx` fallback is a visual approximation only.
- **Supervisor names, dates, and NIM** on the title page and `frontmatter/pengesahan.tex` — all placeholders, not invented.
- **Whether a Smart System program variant** of this guide exists with different specifics (e.g., a different margin or citation convention) — not checked, since none was found in this repository.

## Outstanding Research and Writing TODOs (Prioritized)

1. **Confirm the final Research Question** (or RQ set) with the supervisor(s) — everything else in Chapter 1 (§1.3–1.6), the Chapter 4 synthesis, and all of Chapter 5 depends on this and is currently only a candidate/placeholder.
2. **Confirm the final thesis title**, which depends on (1).
3. **Decide the role of the facial-landmark track** (Papuan V2 / CVAT) relative to the finalized RQ: core contribution, supporting work, or out of scope for this thesis.
4. **Re-verify Papuan V2 Label Studio Annotator A's reported completion** directly against `experiments/EXP-PAP-004/label_studio_export.csv` and `annotator_progress.json` before citing any completion figure.
5. **Complete human review of the 24-image CVAT landmark pilot**, and decide the continuation status of the separate, paused emotion-label annotation track.
6. **Verify dataset provenance/consent** for the source documentary film — flagged in this repository's own audit as unresolved by any technical step, requiring non-technical/institutional action.
7. **Independently verify the 5 literature sources** listed as "requires verification" at the end of `chapters/02-literature-review.tex` before citing them.
8. **Fetch and apply the official ITB-SPs CSL** (`http://www.sps.itb.ac.id/in/csl/`) in place of the `apalike` substitute currently used — see `FORMAT_COMPLIANCE.md` "References."
9. **Compile the manuscript with XeLaTeX** in an environment with a LaTeX toolchain and Times New Roman installed, and fix any resulting warnings/errors — in particular, visually confirm `titlesec`'s chapter-format redefinition and the Roman-numeral chapter/figure/table numbering actually render as intended (none of this could be checked here — see "Compilation status" above).
10. **Finalize both abstracts** only after the above items, and especially the RQ and any completed Papuan V2 results, are settled.

## What the "Background Context" Numbers in the Task Request Mean for This Manuscript

The task that produced this manuscript listed, as background context (explicitly described as "search clues, not automatically approved final thesis results"), a FER2013/ResNet18 experiment (68.57% val accuracy / 69.77% test accuracy / 68.65% macro F1 / 69.76% weighted F1 / 26.96% generalization gap). **A repository-wide search found no trace of FER2013, ResNet18, or these specific figures anywhere in this repository.** This manuscript therefore does not reference them. If these figures belong to a different experiment, project, or an external document not present in this repository, they must be located and their source file identified before any attempt is made to incorporate them here — per this task's own integrity requirements, they are not presented as an established finding of this thesis.
