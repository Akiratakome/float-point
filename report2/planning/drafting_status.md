# Report 2 Drafting Status

Status vocabulary: `structure-only`, `evidence-locked`, `drafting`, `author-rewrite`, `reviewed`.

| Part | Status | Entry gate |
|---|---|---|
| Front matter | structure-only | Final title, declaration, word count rule. |
| Abstract | author-rewrite | The evidence-bounded draft is complete at 190 local `texcount` words. It distinguishes deterministic coverage from provisional MCA scope and requires student rewrite plus the authoritative Overleaf count. |
| Chapter 1 | author-rewrite | The C2--C6-backed narrowing-funnel draft states four labelled research questions, names the covered cases and Euler continuity role, gives explicit exclusions and bounded contributions, and cross-references the C2 decision map. C3 now operationalises the same four questions rather than posing a second set. Student rewrite and the authoritative Overleaf count remain. |
| Chapter 2 | author-rewrite | Evidence-locked plan executed at 942 local `texcount` words with an implementation-delta figure, divergence-control alternatives, verified citations, source-path boundaries, and C3--C5 interfaces; student rewrite, final fact check, and Overleaf word count remain. |
| Chapter 3 | author-rewrite | The evidence hierarchy, completed case/build matrix, controlled-axis comparison table, metric definitions, split timing protocols, metadata and exclusions are integrated at 932 local `texcount` words; student rewrite remains. |
| Chapter 4 | author-rewrite | The evidence-bound draft integrates six figures and one generated CPU/GPU table, including Brio--Wu profiles and bounded Orszag--Tang/Kelvin--Helmholtz morphology and solver-comparison panels. Local `texcount`, including the input table, is 1,320 words; student rewrite and the Overleaf count remain. |
| Chapter 5 | author-rewrite | The evidence-bound results draft integrates seven figures and one table, including direct build-semantics and Kelvin--Helmholtz CFL panels, the corrected 12/12 resolution-dependent precision matrix, repeated timing, temporal fit-quality diagnostics and the deterministic/MCA scope audit. Local `texcount`, including the input table, is 1,663 words; student voice and final sign-off remain. |
| Chapter 6 | author-rewrite | The reviewed, skill-edited C2--C5 synthesis executes the five-section plan at 765 local `texcount` words, adds no result or ranking, and uses source-verified discussion citations with bounded claims; student rewrite and the authoritative Overleaf count remain. |
| Chapter 7 | author-rewrite | The reviewed 380-word draft explicitly answers the four C1 research questions through three load-bearing findings, states configuration boundaries, and prioritises four limitation-driven experiments, including an independent two-dimensional field comparison. Student voice and the authoritative Overleaf count remain. |
| Appendix | author-rewrite | The thesis appendix contains only the reader-facing MCA scope-status table and its comparison boundary; repository paths and operational commands remain in the separate code-submission manifest. The provisional OT and unavailable full-scale KH MCA boundaries remain visible. Local `texcount`, including the input table, is 116 words. |
| References | reviewed | All 30 BibTeX records have source-checked publisher, standards-body, institutional or DOI metadata and all 30 keys are cited in the manuscript. The scripted `pdflatex -> bibtex -> pdflatex -> pdflatex` build remains the release gate. Reopen if student revision adds or removes sources. |
| Code submission bundle | drafting | `submission/code_submission_manifest.md` now routes source, build, config, script, environment, checksum, retention and reproduction evidence. Release commit, clean-tree state, archive name and archive hash remain intentionally unfrozen. |
| Supervisor review copy | overdue external milestone | Requested for 2026-07-27; send the current reviewable draft immediately and label incomplete sections. |
| Supervisor feedback | pending | Expected by 2026-07-31 after the review copy is sent; triage every comment before release. |
| Combined submission | structure-only | The retained Report 2 input predates the current standalone draft. Replace it only after the final standalone PDF, Overleaf count and release checks are frozen; then verify divider, bookmarks, page order and hashes. |
| Signed declaration | external input required | Official attached form obtained, signed, and submitted separately or embedded; Report 2 word count declared. |
| Poster | scheduled | Supervisor-comment window after report release; submit by 2026-08-12. |

## Evidence-package readiness

| Package | Readiness | Planning consequence |
|---|---|---|
| Euler--MHD cross-system matrix | report-grade; 16/16 completion-attested runs | Required in Chapters 3 and 5; bounded sensitivity only. |
| MHD three-resolution ladder | report-grade bounded diagnostic; 24/24 runs, eight complete groups | Include completed trends; no exact-solution or asymptotic-convergence claim. |
| Week-15 Brio--Wu deterministic plus MCA | report-grade bounded scope | Same-scope N=800/t=0.1 HLL/HLLD rows pass the unified audit. |
| Week-15 OT deterministic plus MCA | provisional reduced scope | Deterministic 256^2/t=0.5 and MCA 64^2/t=0.05 must remain separate. |
| Historical Week-15/16 2D L1/L2 | excluded after metric audit | Use unaffected Linf or corrected Week-18 mean/area metrics. |
| Full-scale KH MCA | deferred | State as a limitation/future experiment, not completed evidence. |
| Publication figure set | source audit passed; seven primary PNG/PDF pairs plus six source-hashed supplementary manuscript figures | Use the primary manifest and `Figs/README.md` provenance routing; exclude the arbitrary Week-17 axis-ranking plot. The Chapter 3 pair of native LaTeX tables completes the eight-item review expansion. |

## Drafting order

1. Chapter 4 results skeleton.
2. Chapter 5 results skeleton.
3. Chapter 3 experimental design.
4. Chapter 2 project development.
5. Chapter 6 discussion.
6. Chapter 1 introduction.
7. Chapter 7 conclusion.
8. Abstract and front matter.

Chapters 1--7, the abstract and the appendix are in `author-rewrite` after the
evidence-bounded drafting pass. Chapter 3 is 932 local `texcount` words, within
its rebalanced 900--950-word working range. The remaining prose gate is student rewrite
and fact checking, followed by the authoritative Overleaf count.

## Local release audit (2026-08-03)

- Standalone local `texcount`: 6,994 words; the independent Overleaf count is
  authoritative for submission.
- Abstract: 190 counted words and within its working range.
- Chapter 3: 932 counted words and within its working range.
- Chapter 7: 380 counted words and within its working range.
- Appendix: 116 counted words including its input MCA status table and within
  its working range.
- Main-text figures and tables: 14 figures and five tables are present. The
  review expansion adds six source-hashed experiment figures and two native
  LaTeX tables to the prior manuscript.
- A clean scripted LaTeX/BibTeX build produces a 59-page PDF with no undefined
  citations/references, BibTeX warnings or overfull boxes. One harmless template warning
  remains for an unused `subfigure` caption setup.
- The full Python suite passes 515 tests with six skipped; the focused
  manuscript-review subset passes 22/22 and its manifest subset
  passes 33/33. The experiment audit keeps two Week-14 HLLD MCA candidate build
  roots (36 tracked files) at `reference audit required`; it does not remove
  them.
- The combined-report Report 2 input is a stale pre-final PDF and must not be
  treated as the release candidate.

The 2026-07-29 incomplete-experiment and two-skill prose review is recorded in
`report2/planning/chapter4_incomplete_experiment_review.md`. It records the
successful OT/HLLD/fp64/$512^2$ repair and keeps the chapter at `author-rewrite`
until student-language, formal word-count, and final manual fact checks close.
