# Report 1 Writing Agent

Read `docs/INDEX.md`, `docs/HARNESS.md`, and `report1/INDEX.md` first.

This folder is the writing workspace for Cambridge MPhil Report 1: an Euler
validation, precision, and hardware evidence report for *Effect of
Floating-Point Precision and Hardware on HRSC Schemes*.

Hard rules:

- Do not change solver numerics, cfg defaults, experiment output formats, or raw
  experiment artifacts while writing.
- Do not move anything under `experiments/`; link to evidence through
  `experiments/report1_evidence_map.md`.
- Treat MHD as project context and future direction unless validated MHD evidence
  is added.
- Keep every precision or hardware claim tied to a metric, figure, table,
  citation, or named evidence artifact.
- Do not use internal labels such as `week7`, `week8`, `D1`, `D2`,
  `HLLC-fill`, or `config12` in manuscript prose. Use descriptive labels and
  write "Liska-Wendroff configuration 12" or "LW12".
- Do not treat Verificarlo `p32` as IEEE fp32.
- Use `ENABLE_CUDA`, not `USE_GPU`.
- Do not paste AI-generated prose directly into the final report; rewrite in the
  student's voice and pass `report1/skills/avoiding-ai-flavor/SKILL.md`.

Canonical writing path:

1. Read `report1/planning/reportagents.md` for requirements.
2. Read `report1/planning/manuscript_outline.md` for chapter plan, word budget,
   and evidence locks.
3. Read `experiments/report1_evidence_map.md` before making any result claim.
4. Read `report1/references/reference.md` before adding any citation.
5. Draft in `report1/phd-thesis-template-2.4/`, starting with
   `Chapter5/chapter5.tex`.

Word-count rule:

- Use Overleaf counted text as the controlling count.
- Tables and figure captions are excluded under the current course clarification.
- Pseudocode and algorithm text are counted.
- Target no more than 7,400 counted words; hard cap 7,500.

Canonical LaTeX guide:

- Root file: `report1/phd-thesis-template-2.4/thesis.tex`.
- Config/package map: `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`.
- Do not revive sample template prose from `SampleContent/template-originals/`.

Before claiming a section is ready:

- Check every figure/table is interpreted in prose.
- Check every citation supports a specific sentence.
- Search manuscript-facing `.tex` files for forbidden internal labels.
- Compile the template with `pdflatex -draftmode -interaction=nonstopmode thesis.tex`
  from `report1/phd-thesis-template-2.4/`.
