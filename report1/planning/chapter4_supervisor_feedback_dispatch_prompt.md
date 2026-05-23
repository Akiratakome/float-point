# Chapter 4 Supervisor-Feedback Execution Prompt

This prompt is for the next writing window after the Chapter 5 supervisor
feedback work. It follows the workflow style of
`report1/planning/chapter5_supervisor_feedback_dispatch_prompt.md`, but the
content requirements come from the updated supervisor-feedback map and the
current Chapter 4 text.

This is not a content plan based on archived prompts. Older plans under
`report1/planning/old/` are archival only.

---

## Master prompt

You are the main agent for a supervisor-feedback revision of Report 1 Chapter 4.
Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

This round revises only Chapter 4, "Implementation and Experimental Design".
The actionable requirements are in:

```text
report1/planning/supervisor_feedback_map.md
```

The original supervisor guide is:

```text
report1/planning/supervisorguide.md
```

Use the supervisor guide only to resolve ambiguity in the map. Do not use
`report1/planning/old/` as a content source.

### Required reading

Read these files before dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/planning/reportagents.md`
5. `report1/planning/manuscript_outline.md`
6. `report1/planning/supervisor_feedback_map.md`
7. `report1/planning/supervisorguide.md`
8. `experiments/report1_evidence_map.md`
9. `report1/references/reference.md`
10. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
11. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
12. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`
13. `report1/phd-thesis-template-2.4/References/references.bib`

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison.

Read these style skills before any manuscript prose is edited, and reread them
before final prose review:

```text
report1/skills/scientific-writing-duke/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/academic-english-style/SKILL.md
```

Use `scientific-writing-duke` for report-level technical explanation, then
`academic-english-style` for hedging and sentence control, and finally
`avoiding-ai-flavor` as a paragraph-level acceptance gate.

### Main-agent role

The main agent must not directly rewrite Chapter 4 prose. Its role is:

- read the required context;
- identify current section boundaries and risks;
- dispatch one subagent per section, serially;
- review each returned section before dispatching the next worker;
- if a section fails the requirements, send it back to the same worker or a new
  worker with a focused repair prompt;
- maintain chapter-level continuity notes between workers;
- run the final three-round self-check and compile verification.

The main agent may make only mechanical non-prose changes if needed for
integration, such as preserving section markers after a worker edit. Any
substantive prose, table, caption, or equation change must be made by a
section-scoped worker.

Tell every worker:

```text
You are not alone in the codebase; do not revert or overwrite edits outside your assigned Chapter 4 section.
```

Workers run serially. Never allow two workers to edit `chapter4.tex` at the
same time.

### Current Chapter 4 section markers

Use the actual current markers:

```latex
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>

% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>

% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>

% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>

% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Do not remove these markers.

### Chapter 4 ownership

Chapter 4 owns:

- implementation route and comparability principle;
- code-level precision/backend switches at report level;
- algorithmic execution structure and pseudocode;
- experimental-design matrix;
- metric definitions, including SSIM and reference-scaled ratios;
- reference-solution and downsampling strategy;
- evidence boundaries needed by Chapter 5.

Chapter 4 must not:

- present Chapter 5 measured results as if they are design definitions;
- derive the full numerical method already owned by Chapter 3;
- make Chapter 6-style conclusions;
- claim MHD validation;
- direct assessors to source paths instead of explaining the method;
- imply Verificarlo `p32` is IEEE fp32;
- frame CFL max/min selection as summation-order floating-point sensitivity.

Working word target: keep Chapter 4 near the outline range of 950-1,100
Overleaf-counted words. Tables and captions are not controlling-count words
under the current course clarification, but they must remain readable and not
substitute for prose interpretation. Pseudocode text is counted, so do not add
another algorithm environment unless it is essential.

Section-level word-budget guardrails:

- Section 4.1 should stay concise and design-facing; avoid a long historical
  implementation narrative.
- Section 4.2 should keep exactly one algorithm box if one remains. The
  algorithm should stay at or below 12 lines, each about seven words or fewer;
  the GPU mirror should be one short paragraph, not a second algorithm.
- Section 4.3 should use a compact flag table or code-like table rather than a
  prose list.
- Section 4.4 may use table space because tables are excluded from the current
  controlling count, but the table must be readable and interpreted in prose.
- Section 4.5 should remain a reference-strategy explanation, not a second
  results section.

### Hard rules

- Do not modify solver numerics, cfg defaults, experiment output formats, raw
  artifacts, or anything under `experiments/`.
- Do not change evidence artifacts to make the writing easier.
- Do not use manuscript-facing internal labels: `week7`, `week8`, `week9`,
  `D1`, `D2`, `HLLC-fill`, `config12`, `LW12/config12`, `P1`, or `USE_GPU`.
- Use `ENABLE_CUDA`, not `USE_GPU`.
- Use "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)" at first mention, then "LW3" and
  "LW12".
- Chapter 4 may mention Verificarlo virtual mantissa settings only as MCA
  diagnostics. `p32` is not IEEE binary32/fp32.
- Use author-name prose for specific methods/tools where natural, e.g.
  "Denis et al.'s Verificarlo", "Parker's Monte Carlo arithmetic", "Toro's
  exact Riemann solutions", and "Liska and Wendroff's configurations".
- Compiler flags should appear as a short listing, code-like block, or compact
  table, not as a long sentence.
- Do not add LaTeX packages for code listings in this pass. Prefer an existing
  `tabular`, `tabularx`, `verbatim`-style block if already supported, or a
  compact table with `\texttt{...}` entries. If a package change appears
  necessary, stop and report the need instead of editing the preamble.
- Tables and captions must be self-contained enough to read without source-code
  knowledge: name the compared axis, define abbreviations, and keep fonts large
  enough to read in the compiled PDF.
- AI-assisted prose must pass `avoiding-ai-flavor`: no generic filler, no
  marketing tone, no unsupported confidence, no template-like prose.

### Evidence and source context by worker

Every worker must read `experiments/report1_evidence_map.md` before editing.
Workers should inspect only the evidence/source files relevant to their
section. If a required fact is not supported, report the gap rather than
inventing a detail.

| Worker | Required context |
|---|---|
| A, 4.1 implementation route | `report1/planning/supervisor_feedback_map.md` §4.1; `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`; inspect CMake/source definitions only as needed to verify `FLOAT_PRECISION`, `HRSC_REAL`, and `ENABLE_CUDA` wording |
| B, 4.2 algorithmic structure | `report1/planning/supervisor_feedback_map.md` §4.2 and Chapter-Level Caution; current Chapter 4 algorithm box; source inspection only to verify functional description, not to cite source paths in prose |
| C, 4.3 precision/hardware variants | `report1/planning/supervisor_feedback_map.md` §4.3; `report1/references/reference.md`; `references.bib`; build-flag context in current C4 |
| D, 4.4 matrix and metrics | `report1/planning/supervisor_feedback_map.md` §4.4; `experiments/report1_evidence_map.md`; Chapter 5 current metric usage; evidence summaries only to verify design-matrix labels, not to add new result claims |
| E, 4.5 reference strategy | `report1/planning/supervisor_feedback_map.md` §4.5; `experiments/report1_evidence_map.md`; `scripts/metrics/downsample_2d.py` if present; 2D reference summaries for LW3/LW12 |

---

## Worker A: Section 4.1 Implementation Route and Comparability Principle

Assigned region:

```latex
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>
```

Goal:

- Make the stand-alone implementation route clear without overemphasising
  AMReX. Delete AMReX if it is not needed, or compress it to one
  non-load-bearing context sentence.
- Add a short code-like snippet or compact table showing
  `FLOAT_PRECISION=float/double` mapped to `HRSC_REAL`.
- Mention `ENABLE_CUDA` if this is the clearest place to define the backend
  switch.
- State the toolchain split plainly:
  Toro3/Toro5 use Windows BuildTools; Sod/LW3/LW12 use Linux/WSL; each
  within-case CPU/GPU comparison is made within one matched
  binary/configuration.
- If Boost::Multiprecision is mentioned, state it is out of Report 1 evidence
  scope unless actually used.

Constraints:

- Do not add source paths as explanation.
- Do not make cross-toolchain equivalence claims.
- Keep the section as implementation design, not results.

Worker summary must report:

- whether AMReX was removed or compressed;
- where the precision/backend snippet was added;
- the exact wording used for the toolchain boundary.

---

## Worker B: Section 4.2 Algorithmic Structure

Assigned region:

```latex
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Goal:

- Define CUDA as the NVIDIA GPU programming model/backend used here.
- Define thread blocks as GPU thread tiles and OpenMP static schedules as fixed
  CPU loop assignment.
- Replace source-path style explanation with functional prose.
- Correct the CFL wording: CFL selection is deterministic max/min comparison,
  not summation reduction or reduction-order floating-point sensitivity.
- Preserve the existing algorithm box if it remains useful, but keep it concise
  because pseudocode text counts in Overleaf. Keep at most 12 algorithm lines,
  with each line about seven words or fewer. If the current algorithm already
  exceeds this, shorten it rather than adding explanatory algorithm text.
- Keep Kahan summation only if it is relevant and accurately tied to the time
  accumulator; do not let it distract from the main algorithmic path.

Constraints:

- Do not derive MUSCL-Hancock/HLLC in detail; Chapter 3 owns the method.
- Do not claim stage-by-stage CPU/GPU identity.
- Do not direct readers to source files.

Worker summary must report:

- how CUDA/thread blocks/OpenMP were defined;
- the exact CFL correction;
- whether the algorithm box was shortened or left intact.

---

## Worker C: Section 4.3 Precision, Hardware, and Diagnostic Axes

Assigned region:

```latex
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>
```

Goal:

- Define matched device comparison as same case, same executable, same
  precision/configuration, changing only runtime device selection.
- Replace long prose flag lists with a short listing or compact table covering:
  `-ffp-contract=off`, `-fno-fast-math`, `--fmad=false`, `--ftz=false`,
  `--prec-div=true`, and `--prec-sqrt=true`.
- Prefer a compact `tabular`/`tabularx` presentation using `\texttt{...}` for
  flags. Do not add `listings`, `minted`, or other code-listing packages.
- Add short meanings for those flags:
  FMA contraction, fast-math transformations, denormal/flush-to-zero behaviour,
  and precise division/square-root requests.
- State that Verificarlo `p8/p16/p32/p53` are virtual mantissa settings used for
  MCA diagnostics, not binary storage formats.
- Use author-name prose for Parker and Denis et al. where natural.

Constraints:

- Do not present Verificarlo `p32` as IEEE fp32.
- Do not turn this into a floating-point background section; Chapter 2 owns
  broad floating-point theory.
- Do not expand the citation set unless `reference.md` supports the citation
  and `references.bib` already contains or receives a verified entry.

Worker summary must report:

- whether a listing or table was used for flags;
- whether matched device comparison is explicitly defined;
- where `p32 != fp32` is stated.

---

## Worker D: Section 4.4 Test-Case Matrix and Metrics

Assigned region:

```latex
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Goal:

- Define SSIM as an image-structure similarity metric, with values near 1
  indicating closer structural agreement with the reference image.
- Define the reference-scaled ratio:
  `R_ref = ||U_fp32 - U_fp64||_1 / ||U_fp64 - U_ref||_1`.
- Explain the ratio interpretation:
  `<1` means the precision gap is below the chosen reference/discretisation
  scale; near or above 1 means comparable to or larger than that scale; zero
  denominators are degenerate cases.
- Make the design matrix readable: avoid `\scriptsize` if possible, increase
  spacing, split the table, or move some detail to prose if needed.
- If the matrix must remain wide, prefer `\small`, clearer column grouping,
  `\addlinespace`, or a split table over unreadably dense `\scriptsize`.
- Give compact initial-condition or benchmark-definition context for Sod,
  Toro3, Toro5, LW3, and LW12, or explicitly state where that context appears.
- Avoid generic "rows"; use "entries", "comparisons", "cases", or a specific
  "table row" only when the table itself is being discussed.
- Use author-name prose for Sod, Toro, and Liska-Wendroff where natural.

Constraints:

- Do not add new measured results; this is design and metrics.
- Do not overpack the matrix so it becomes unreadable.
- Do not use `config12`.

Worker summary must report:

- where SSIM and `R_ref` were defined;
- how table readability was improved;
- whether initial-condition context was added or cross-referenced.

---

## Worker E: Section 4.5 Reference-Solution Strategy

Assigned region:

```latex
% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Goal:

- State clearly that Sod/Toro 1D cases use exact Riemann references, while LW3
  and LW12 use high-resolution numerical fp64 references.
- Do not call 2D references exact.
- Explain downsampling/mapping from high-resolution references to lower grids.
  If supported by `scripts/metrics/downsample_2d.py`, state:
  conserved variables are integer-ratio block-averaged, then converted to
  primitive variables for norms/SSIM.
- Include the specific ratios if supported:
  LW3 `1600 -> 400/200` uses `4x4/8x8` block averaging;
  LW12 `800 -> 400/200` uses `2x2/4x4` block averaging.
- Keep the ratio boundary: reference-scaled metrics compare precision drift to
  the chosen reference/discretisation scale, not to a universal rounding-error
  bound.

Constraints:

- Do not introduce new result values.
- Do not change or move files under `experiments/`.
- Do not use "CPU/GPU rows"; use "CPU/GPU comparisons" or "entries".

Worker summary must report:

- exact wording used for 2D reference mapping;
- whether `downsample_2d.py` was inspected;
- any unresolved gap in reference-mapping evidence.

---

## Main-Agent Integration Review

After each worker:

1. Re-read only the edited section and one paragraph before/after it.
2. Check that the section satisfies its worker goals.
3. Check that the section does not duplicate Chapter 3 method derivation or
   Chapter 5 results.
4. If the section fails, dispatch a focused repair worker before continuing.
5. Record a short continuity note for the next worker.

The main agent must not directly rewrite failed prose. It must request a worker
repair.

After all workers:

1. Read the full Chapter 4 for flow and consistency.
2. Check that labels and cross-references still compile.
3. Confirm Chapter 5 dependencies remain aligned:
   Chapter 4 defines metrics/reference strategy/design; Chapter 5 reports
   measured values.
4. Confirm no archived plan language or internal experiment label entered the
   manuscript.

---

## Required Three-Round Self-Check

Do not stop after worker edits. Complete all three self-check rounds. If any
round scores below 95/100, dispatch a focused repair worker and rerun that round
once. If after three full rounds the chapter still cannot reach 95/100, stop and
explain exactly which requirement blocks it.

### Round 1: Supervisor-Requirement Coverage

Score Chapter 4 against `report1/planning/supervisor_feedback_map.md` §4.1-4.5
and the Chapter-Level CFL caution.

Checklist:

- 4.1: AMReX removed/compressed; `FLOAT_PRECISION -> HRSC_REAL` shown;
  `ENABLE_CUDA` correct; toolchain split plain and bounded.
- 4.2: CUDA/thread blocks/OpenMP defined; source-path explanation avoided; CFL
  max/min comparison not described as summation-order sensitivity.
- 4.3: matched device comparison defined; compiler flags presented as
  listing/table; each flag has a short meaning; `p32 != fp32`.
- 4.4: SSIM and `R_ref` defined; ratio interpretation clear; table readable;
  initial-condition/benchmark context sufficient; no generic "rows" misuse.
- 4.5: 1D exact vs 2D numerical references separated; downsampling/block
  averaging explained; 2D references not called exact.

Pass threshold: 95/100.

### Round 2: Evidence, Citation, and Prose-Risk Audit

Checklist:

- Every implementation/evidence boundary is supported by a read file or named
  artifact.
- No new result claim appears in Chapter 4.
- Citations support the sentence they appear in.
- Author-name prose is used where it improves clarity for specific methods,
  benchmarks, or tools.
- Technical explanation follows `scientific-writing-duke`: topic sentences are
  concrete, each paragraph has a clear function, and implementation detail is
  connected to method, validation, or evidence interpretation.
- Prose passes `avoiding-ai-flavor`: no generic filler, marketing confidence,
  unsupported certainty, or repeated template rhythm.
- Word count risk is controlled: Chapter 4 remains near 950-1,100 counted words
  and no unnecessary algorithm text was added. Section 4.2 keeps no more than
  one algorithm box, at most 12 concise algorithm lines.
- Table/caption presentation is assessor-readable: no table is made readable
  only by zooming; captions define the table purpose and compared axes.

Pass threshold: 95/100.

### Round 3: Mechanical, LaTeX, and Forbidden-Token Check

Run from repository root:

```powershell
git diff --check -- report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: no whitespace or patch-format warnings introduced by this pass.

```powershell
rg -n "week7|week8|week9|D1|D2|HLLC-fill|config12|LW12/config12|P1|USE_GPU|fp32 L1 error|fp64 L1 error" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: no manuscript-facing hits.

Check citation keys:

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n "^@" report1/phd-thesis-template-2.4/References/references.bib
```

Check labels/cross-references:

```powershell
rg -n "\\\\label|\\\\ref|\\\\autoref" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Compile:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If citations changed, run:

```powershell
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Pass threshold: no new Chapter 4 LaTeX errors, no forbidden-token hits, no
undefined citation introduced by this pass.

---

## Final Response Format

Respond in Chinese with:

- which C4 sections were revised by which worker;
- how each supervisor issue was addressed;
- what evidence/source files were used;
- whether any worker needed a repair pass;
- the three self-check scores and outcomes;
- compile/check results;
- remaining dependencies on Chapter 3, Chapter 5, Chapter 6, or the References
  capitalization pass.

Do not claim the full report is finished.
