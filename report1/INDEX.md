# Report 1 Index

Report 1 is the Cambridge MPhil Report 1 writing workspace for *Effect of Floating-Point Precision and Hardware on HRSC Schemes*. It is an Euler validation, precision, and hardware evidence report. Ideal MHD is project context and a Report 2 direction unless new validated MHD evidence is added.

The repository-level harness rule still applies: fit experiment work into `config -> build -> run -> measure -> aggregate -> plot`, keep run metadata with summaries, and do not change solver numerics, cfg defaults, output formats, or raw experiment artifacts while writing the report.

## Reading Order for Future AI

1. `docs/INDEX.md` — project-wide orientation, harness conventions, and where evidence lives.
2. `docs/HARNESS.md` — canonical experiment pipeline and metadata discipline.
3. `report1/INDEX.md` — this Report 1 entry point, scope, forbidden claims, and LaTeX map.
4. `report1/WRITING_AGENT.md` — short global writing-agent rules for future AI sessions.
5. `report1/planning/reportagents.md` — report requirements, marking expectations, front matter, and writing constraints.
6. `report1/planning/manuscript_outline.md` — chapter-by-chapter writing plan, word budget, prompts, evidence locks, and final checklist.
7. `experiments/report1_evidence_map.md` — evidence routing map. Do not move these artifacts.
8. `report1/references/reference.md` — citation map. Add a citation only when it supports a sentence.
9. `report1/skills/` — writing skills. In particular, apply `avoiding-ai-flavor/SKILL.md` to every AI-assisted paragraph and use `academic-english-style/SKILL.md` for hedging and academic stance.
10. `report1/phd-thesis-template-2.4/` — LaTeX workspace. Write manuscript prose only after reading the outline and evidence map.

## Folder Map

| Path | Role |
|---|---|
| `report1/planning/` | Writing plan, report-agent requirements, and drafting status. |
| `report1/WRITING_AGENT.md` | Short global rules for Report 1 writing agents. |
| `report1/requirements/` | Official project and course PDFs. These override derived notes if there is a conflict. |
| `report1/references/` | Working citation map and reference notes. |
| `report1/examples/` | Example Report 1 PDF for structure only; do not reuse scientific content. |
| `report1/skills/` | Writing and editing skills plus source notes. |
| `report1/phd-thesis-template-2.4/` | CUED LaTeX report workspace. |
| `experiments/report1_evidence_map.md` | External evidence map for Report 1; linked here but not moved. |

## Requirement Map

The project brief gives five equally weighted Report 1 categories:

- Literature review and background.
- Mathematical theory.
- Code and implementation description.
- Validation.
- Quality of write-up.

The handbook general criteria require:

- Awareness of background science and relevant literature.
- Understanding of computational techniques and limitations.
- Accurate description, validation, and interpretation of computational results.
- Awareness and quantification of errors and ambiguities.
- Conclusions based on the evidence presented.
- Clear presentation, appropriate length, figures, tables, and references.

Word count rule for this workspace:

- Use the Overleaf counted-text result as the controlling value.
- Tables and figure captions are not counted under the current course clarification.
- Bibliography is excluded.
- Pseudocode and algorithm-environment bodies are counted as prose.
- Drafting target: no more than 7,400 counted words. Hard cap: 7,500.

## Evidence Map

Use `experiments/report1_evidence_map.md` as the single routing document for experiment artifacts. Core P0 evidence roles are:

- 1D Euler validation.
- 2D LW3 and LW12 validation.
- Real fp32/fp64 comparison.
- Matched CPU/GPU strict-HLLC comparison.
- Compiler, branch-rule, and solver variation.
- Drift growth over time.
- Verificarlo virtual-precision diagnostics.

Every figure, table, or numerical claim must trace to an artifact named in the outline or evidence map. Do not cite raw grids directly in prose.

## Forbidden Claims

- Do not say MHD validation has been completed.
- Do not say fp32 is generally adequate.
- Do not say hardware has no effect generally.
- Do not treat Verificarlo `p32` virtual precision as IEEE fp32.
- Do not extend final-time CPU/GPU zero drift to intermediate times, non-strict builds, or untested cases.
- Do not use local evidence labels such as `week7`, `week8`, `D1`, `D2`, or `HLLC-fill` in manuscript prose, captions, headings, or bibliography.
- Do not write `config12` in manuscript-facing prose; use Liska-Wendroff configuration 12 at first mention and LW12 after that.
- Do not use `USE_GPU` in writing or build notes for this project; use `ENABLE_CUDA`.
- Avoid misleading phrases such as "fp32 L1 error" or "fp64 L1 error" when the metric is a comparison against a reference, another precision, or another device. Name the two quantities being compared.

## LaTeX Workspace Guide

Root file:

- `report1/phd-thesis-template-2.4/thesis.tex`

Metadata and front matter:

- `report1/phd-thesis-template-2.4/thesis-info.tex` — title, author placeholder, department, degree, supervisor, date, keywords.
- `report1/phd-thesis-template-2.4/Declaration/declaration.tex` — handbook declaration wording with author/date placeholder.
- `report1/phd-thesis-template-2.4/WordCount/wordcount.tex` — Overleaf word-count declaration placeholder.
- `report1/phd-thesis-template-2.4/Abstract/abstract.tex` — abstract TODO; write last.
- `report1/phd-thesis-template-2.4/References/references.bib` — empty verified-bibliography workspace.
- `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md` — map of compile-facing configuration, package locations, and transient build products.

Main chapter files:

- `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex` — Introduction.
- `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` — Background and Governing Equations.
- `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` — Numerical Method.
- `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` — Implementation and Experimental Design.
- `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` — Validation and Precision Results.
- `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` — Discussion.
- `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex` — Conclusion.

Template sample material:

- Original sample chapters, sample appendices, and sample bibliography are quarantined in `report1/phd-thesis-template-2.4/SampleContent/template-originals/`.
- `thesis.tex` includes Chapters 1--7 and no sample appendices. The dedication page is commented out.
- `Classes/`, `Preamble/`, `sty/`, `Figs/`, and `References/` keep README files explaining their roles; core compile paths have not been moved.

Next drafting entry point:

- Start with `Chapter5/chapter5.tex`, following the evidence-first drafting order in `report1/planning/manuscript_outline.md`.
- Do not write full prose until each planned figure/table has a traceable artifact in `experiments/report1_evidence_map.md`.
