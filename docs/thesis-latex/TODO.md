# Outstanding Thesis TODOs (Prioritized)

**Resolved since the previous revision (2026-10-09), see `RESEARCH_DECISIONS.md`:** FER confirmed as the primary research objective, with the facial-landmark track confirmed as supporting/future work (previously item 4 below); N=135's provenance confirmed as the legacy 227-crop dataset and its derivation arithmetic resolved (previously item 2 below, at the rule/arithmetic level — a row-level residual gap remains, see item 2 below).

1. **Obtain supervisor (Pak Fadhil) sign-off on the RQ1/RQ2/RQ3 structure** — see `chapters/01-introduction.tex` §1.5 and `RESEARCH_DECISIONS.md` Decision 4. Scope and structure are author-confirmed; supervisor approval of the exact wording is still pending.
2. **Investigate D-8**: EXP-006's "before" per-skin-tone accuracy (Dark 27.67%, Medium-Dark 10.77%) does not match EXP-005's dedicated audit (Dark 44.00%, Medium-Dark 14.29%) despite identical overall accuracy — inspect both notebooks' row-level skin-tone grouping logic (`research-audit/DATA_DISCREPANCIES.md` D-8). This is new in this revision and currently unresolved.
2b. **Re-verify the row-level identity of the 6 alignment-failure exclusions** within the $N=135$ subset against the raw `classifier_predictions.csv`, if a fully closed (not just documentarily resolved) derivation is required (`research-audit/DATA_DISCREPANCIES.md` D-2).
3. **Resolve D-1**: directly re-count `experiments/EXP-PAP-004/label_studio_export.csv` / `annotator_progress.json` rows to confirm or correct the "Annotator A 150/150 complete" figure before citing it anywhere. Unaffected by the scope clarifications.
4. **Complete human review of the 24-image CVAT landmark pilot** (EXP-PAP-005), following the staged workflow in `chapters/03-research-methodology.tex` §3.6 — confirmed as supporting/future work, not blocking the thesis's primary FER contribution.
5. **Decide the continuation status of the paused Papuan V2 emotion-label annotation track** (Annotator B, 0/75; Annotator A, status per item 3 above) — this track remains separate from, and is not required by, the primary FER contribution.
6. **Verify data provenance/consent** for the source film — flagged repeatedly in this project's own internal audits as unresolved and outside the scope of any technical step.
7. **Independently verify the 5 "requires verification" literature citations** listed at the end of `chapters/02-literature-review.tex`.
8. **Record exact package/model-weight version numbers** (from `pyproject.toml`/`uv.lock`) against each experiment, for `REPRODUCIBILITY.md`.
9. **Obtain the official ITB thesis formatting template**, or a friend's-thesis file for structural reference — neither was found in this repository; see `README.md` "Formatting Assumptions."
10. **Compile the manuscript** with an actual LaTeX toolchain (none available in this environment) and fix any resulting errors/warnings.
11. **Finalize both abstracts and the title** only after item 1 (RQ sign-off) is settled.

Locate this file's companions for full detail: `README.md` (status/build), `RESEARCH_DECISIONS.md` (confirmed scope), `EVIDENCE_MAP.md` (claim→source), `REPRODUCIBILITY.md`, and `research-audit/DATA_DISCREPANCIES.md`.
