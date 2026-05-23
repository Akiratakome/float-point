# Chapter 2 Supervisor-Feedback Execution Prompt

This prompt is for drafting/revising Report 1 Chapter 2 after the supervisor
feedback round. It follows the serial worker/marker workflow used by
`report1/planning/old/chapter4_dispatch_prompt.md` and the newer supervisor
feedback prompts, but the content requirements come from the current outline,
the supervisor-feedback map, the original supervisor guide, the discarded
Draft 2 PDF, the official project brief, and the handbook.

This is not a content plan based on archived prompts. Older plans under
`report1/planning/old/` are archival only.

---

## Master prompt

You are the main agent for Report 1 Chapter 2, "Background and Literature
Context". Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```

This round drafts/revises only Chapter 2. The actionable requirements come
from:

```text
report1/planning/manuscript_outline.md
report1/planning/supervisor_feedback_map.md
report1/planning/supervisorguide.md
report1/draft2.pdf
report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf
report1/requirements/SciComp_Mphil_Handbook-2025-26.pdf
```

Use `report1/planning/supervisor_feedback_map.md` as the actionable map. Use
`report1/planning/supervisorguide.md` and `report1/draft2.pdf` only to verify
what the supervisor was responding to. Use the official PDFs to resolve any
conflict in requirements. Do not use `report1/planning/old/` as a content
source.

### Required reading

Read these files before dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/WRITING_AGENT.md`
5. `report1/planning/reportagents.md`
6. `report1/planning/manuscript_outline.md`
7. `report1/planning/supervisor_feedback_map.md`
8. `report1/planning/supervisorguide.md`
9. `report1/references/reference.md`
10. `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
11. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
12. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
13. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
14. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`
15. `report1/phd-thesis-template-2.4/References/references.bib`
16. `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`
17. `report1/requirements/SciComp_Mphil_Handbook-2025-26.pdf`
18. `report1/draft2.pdf`

If PDF text extraction is needed, use `pdftotext` or another local text
extraction method. Do not quote long passages from the PDFs; use them to verify
requirements.

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison.

Read these style skills before any manuscript prose is edited, and reread them
before final prose review:

```text
report1/skills/writing-literature-review/SKILL.md
report1/skills/academic-english-style/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/report1-context/SKILL.md
```

Use `writing-literature-review` for background/literature structure,
`academic-english-style` for hedging and sentence control,
`report1-context` for Report 1 scope boundaries, and `avoiding-ai-flavor` as a
paragraph-level acceptance gate.

### Main-agent role

The main agent must not directly rewrite Chapter 2 prose. Its role is:

- read the required context;
- create or repair the Chapter 2 marker skeleton if needed;
- dispatch one subagent per section, serially;
- review each returned section before dispatching the next worker;
- if a section fails the requirements, send it back to the same worker or a new
  worker with a focused repair prompt;
- maintain chapter-level continuity notes between workers;
- run the final three-round self-check and compile verification.

The main agent may make only mechanical non-prose changes if needed for
integration: adding section headings, preserving markers, fixing cross-reference
syntax, or adding a verified BibTeX entry flagged by a worker after checking
`report1/references/reference.md`. Any substantive prose, equation explanation,
caption, or citation-context change must be made by the owning section worker.

Tell every worker:

```text
You are not alone in the codebase; do not revert or overwrite edits outside your assigned Chapter 2 section.
```

Workers run serially. Never allow two workers to edit `chapter2.tex` at the
same time.

### Required Chapter 2 section skeleton

The current Chapter 2 may still contain TODO comments and may not yet include
Section 2.5. The main agent should create this marker skeleton before dispatch
if it is absent:

```latex
\section{Compressible Euler Equations}
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>

\section{Ideal-MHD Project Context}
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>

\section{HRSC and Benchmark Literature}
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>

\section{Floating-Point Arithmetic and Reproducibility}
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>

\section{Report 1 Gap}
% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Do not leave TODO or LLM-directive text in manuscript-facing Chapter 2.

### Chapter 2 ownership

Chapter 2 owns:

- concise background and literature context;
- the compressible Euler equations and ideal-gas closure needed later;
- ideal-MHD as project context, including the divergence-free magnetic-field
  constraint;
- a literature-level overview of HRSC finite-volume methods and benchmark
  sources;
- floating-point arithmetic and reproducibility mechanisms at background level;
- the gap statement connecting background literature to Report 1's controlled
  Euler precision/hardware evidence.

Chapter 2 must read as a literature review with governing background, not as a
general textbook primer. Every section should make the source function visible:
which source supplies the governing equations, which source supplies benchmark
context, which source supplies method lineage, which source supplies
floating-point mechanisms, and what measured gap this report then addresses.
Do not write a chronological literature survey, and do not pad paragraphs with
sources that do not support a specific sentence.

Chapter 2 must not:

- derive the finite-volume update, MUSCL-Hancock predictor, HLLC flux, CFL
  formula, or limiter equations; Chapter 3 owns those;
- define implementation switches, matched-device evidence, metrics, or
  reference downsampling; Chapter 4 owns those;
- report numerical validation values or interpret result tables/figures;
  Chapter 5 owns those;
- synthesize the results or write conclusions; Chapter 6/7 own that;
- claim MHD validation or a completed MHD method;
- use detailed Toro/Liska-Wendroff test descriptions as background prose;
  those belong in Chapter 4/5.

Working word target: 850-950 Overleaf-counted words. This is a hard background
chapter budget, not a writing entitlement. Suggested section budgets:

- 2.1 Euler equations: 170-210 words plus a compact equation block.
- 2.2 ideal-MHD context: 130-170 words plus a compact equation/constraint
  block; do not expand into MHD validation.
- 2.3 HRSC and benchmark literature: 160-210 words.
- 2.4 floating-point arithmetic: 300-360 words.
- 2.5 gap statement: 70-110 words.

Tables and figure captions are not counted under the current project
clarification, but Chapter 2 should not need figures or tables. Equations are
allowed where they reduce prose, but do not add derivations.

### Project-brief and handbook compliance

Chapter 2 is the main chapter satisfying the project brief's Literature review
and background [20%] category. Workers must visibly cover:

- overview of Euler equations for a compressible ideal gas;
- overview of ideal-MHD equations;
- finite-volume schemes at a basic literature/background level;
- brief discussion of floating-point arithmetic and effects of hardware,
  compiler options, and parallel-thread ordering on simple expressions and
  algorithms.

The handbook requires Report 1 to include project background, literature review,
underlying mathematical models, algorithms for their solution, validation, and
references. Chapter 2 supports background/literature and the governing-model
part of this requirement. It must also respect the handbook-style presentation
requirements: clear English, properly acknowledged sources, and no raw
AI-generated prose.

Overlap guard:

- Chapter 1 owns the broad motivation, applications, report scope, and roadmap.
- Chapter 2 owns the source-backed background and literature roles.
- Chapter 3 owns equations and algorithms once they become derivations or
  choices used by the solver.
- Chapter 4 owns implementation route, design matrix, metrics, and reference
  strategy.
- Chapter 5 owns measured validation and precision/hardware results.
- Chapter 6/7 own synthesis, limitations, and final conclusions.

If a drafted Chapter 2 sentence could be moved unchanged into Chapter 3, 4, or
5, the worker must either reduce it to literature context or delete it.

### Hard rules

- Do not modify solver numerics, cfg defaults, experiment output formats, raw
  artifacts, or anything under `experiments/`.
- Do not write MHD as a completed Report 1 result.
- Do not use manuscript-facing internal labels: `week7`, `week8`, `week9`,
  `D1`, `D2`, `HLLC-fill`, `config12`, `LW12/config12`, `P1`, or `USE_GPU`.
- Use `ENABLE_CUDA`, not `USE_GPU`, if a CUDA build switch must be named.
- Do not treat Verificarlo `p32` as IEEE fp32.
- Use author-name prose for specific methods, tools, or benchmark families
  where natural: Toro, Sod, Liska and Wendroff, Harten-Lax-van Leer, van Leer,
  Goldberg, Higham, Parker, Denis et al., Dedner et al., Evans and Hawley.
- Use citations only where they support a specific sentence. Do not decorate
  paragraphs with broad citation lists.
- AI-assisted prose must pass `avoiding-ai-flavor`: no generic filler,
  marketing tone, unsupported confidence, repeated template rhythm, or
  paragraph that could fit an unrelated dissertation.

### Citation policy

Use `report1/references/reference.md` before adding or changing citations.

Likely citation roles:

- `toro2009`: Euler equations, Riemann problems, finite-volume/HRSC background.
- `sod_1978`: Sod shock-tube source only if Sod is mentioned in background.
- `liska_wendroff_2003`: 2D Euler benchmark source, not detailed results.
- `harten_lax_vanleer_1983`: HLL-family/Godunov-type flux context if needed.
- `vanleer_1979`: MUSCL reconstruction history if needed.
- `goldberg_1991`, `higham_2002`, `ieee754_2019`: floating-point arithmetic,
  rounding, non-associativity, and numerical error concepts.
- `brogi_etal_2024`: CFD-specific reduced/mixed precision background,
  including accuracy/performance trade-offs and CPU/GPU aspects; do not use it
  as evidence for this report's HRSC solver or selected Euler results.
- `wang_xia_chen_2025`: compressible finite-volume hybrid precision on
  heterogeneous CPU/GPU hardware if a second CFD-specific example is useful;
  keep it clearly separate from this report's structured-grid HRSC evidence.
- `parker_1997`, `denis_etal_2016`: Monte Carlo arithmetic and Verificarlo if
  MCA/Verificarlo is introduced.
- Demmel and Nguyen on reproducible floating-point reductions only if final
  metadata is verified and parallel reduction reproducibility is explicitly
  discussed; do not assume a BibTeX key already exists.
- `dedner_2002`, `evans_hawley_1988`: divergence cleaning or constrained
  transport, if named.
- `bard_dorelli_2014`: ideal-MHD GPU/MUSCL-Hancock project-context example only
  if it improves the MHD-context paragraph.

Do not cite AMReX unless Chapter 2 explicitly discusses AMReX background, which
is normally unnecessary here.

---

## Worker A: Section 2.1 Compressible Euler Equations

Assigned region:

```latex
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>
```

Goal:

- Present Euler as the Report 1 validation system, not as the whole project.
- Include a compact 1D/2D conservation-law equation block:
  `partial_t U + partial_x F(U) + partial_y G(U)=0` is sufficient if the state
  and fluxes are defined.
- Define conservative variables: density, momentum, total energy.
- Define `\gamma` as the ratio of specific heats.
- Explain the ideal-gas closure:
  `E = rho e + 1/2 rho (u^2+v^2)` and
  `p = (gamma-1) rho e`, or the equivalent expression
  `p=(gamma-1)(E - 1/2 rho(u^2+v^2))`.
- Explain why Euler is used first: shocks, contacts, rarefactions, and
  auditable Riemann/benchmark references before adding magnetic fields.

Constraints:

- Do not derive the finite-volume update or wave-speed eigenstructure.
- Do not introduce HLLC here.
- Keep equations minimal and notation consistent with Chapter 3.

Worker summary must report:

- where `\gamma`, `p`, and `E` are defined;
- whether the section stayed within the background scope;
- any citation used and what sentence it supports.

---

## Worker B: Section 2.2 Ideal-MHD Project Context

Assigned region:

```latex
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Goal:

- Give ideal MHD as project context and future direction.
- Include a compact ideal-MHD equation block or tightly written conservation
  form. This is required by the supervisor feedback; do not leave MHD as a
  purely verbal description.
- Define the magnetic field `B`, total pressure if used, and the induction
  equation or conservative MHD form at a report-background level.
- Explain `\nabla\cdot B=0` as the solenoidal magnetic-field constraint.
- Explain why preserving or controlling divergence matters: numerical
  divergence errors can contaminate magnetic forces and wave propagation.
- Name divergence cleaning or constrained transport only as future numerical
  choices, supported by Dedner or Evans-Hawley if cited.

Constraints:

- Keep this section about 130-170 counted words if possible, excluding compact
  equations.
- Do not claim Report 1 implements or validates MHD.
- Do not introduce MHD test results or MHD benchmark performance.

Worker summary must report:

- the exact MHD equation/constraint included;
- how the Report 1 boundary is stated;
- which MHD citation, if any, supports the sentence.

---

## Worker C: Section 2.3 HRSC and Benchmark Literature

Assigned region:

```latex
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>
```

Goal:

- Keep this as thematic literature/background, not a test-case catalogue.
- Explain why finite-volume HRSC/Godunov-type methods are appropriate for
  discontinuous compressible flows.
- Mention that Riemann-solver methods are central because interface fluxes
  determine shock/contact treatment.
- Mention standard benchmark sources only at a high level:
  Sod/Toro for 1D Riemann problems and Liska-Wendroff for 2D Euler Riemann
  configurations.
- If HLL/HLLC is mentioned, define or cite it before use and keep detailed HLLC
  mechanics for Chapter 3.

Constraints:

- Do not describe Toro3/Toro5/LW3/LW12 in detail; Chapter 4/5 own case details.
- Do not rederive MUSCL-Hancock, CFL, HLLC, Rusanov, or limiter formulas.
- Do not use this section as a mini Chapter 3.

Worker summary must report:

- which method/benchmark sources were cited;
- how detailed case descriptions were avoided;
- whether HLLC appears and, if so, how it is introduced safely.

---

## Worker D: Section 2.4 Floating-Point Arithmetic and Reproducibility

Assigned region:

```latex
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Goal:

- Cover the project brief's floating-point background requirement.
- Define binary32 and binary64 using both significand length and exponent
  range:
  binary32 has a 24-bit significand including the hidden bit and normal exponent
  range roughly `-126` to `+127`; binary64 has a 53-bit significand and normal
  exponent range roughly `-1022` to `+1023`.
- Define unit roundoff under round-to-nearest: approximately `2^-24` for
  binary32 and `2^-53` for binary64.
- Include the supervisor's non-associativity example or an equivalent one:
  `(1e-18 + 1) - 1` versus `1e-18 + (1 - 1)`.
- Explain that non-associativity can change more than the last few digits in a
  nonlinear time-dependent solver, but the report measures the size rather than
  assuming growth.
- Distinguish `-O3` from `-Ofast`: normal `-O3` does not allow the same
  reassociation/approximation freedoms as fast-math/`-Ofast`.
- Mention FMA contraction, reciprocal/division, square-root approximations, and
  parallel reduction/order effects.
- Introduce Verificarlo and Monte Carlo arithmetic if Chapter 4/6 will rely on
  them. State explicitly that Verificarlo `p32` is a virtual mantissa setting,
  not IEEE fp32.
- End with the practical design question: which variables, regions,
  operations, and compiler/device settings can be relaxed without exceeding
  the discretisation/reference error scale?
- Use Brogi et al. as the main CFD-specific reduced/mixed precision source and,
  if space allows, Wang, Xia, and Chen as a compressible finite-volume
  hybrid-precision example. General floating-point and numerical-linear-algebra
  references are not enough for a CFD conclusion. These CFD sources still do
  not prove this report's HRSC cases; frame Report 1 as supplying controlled
  Euler evidence, not as proving a general mixed-precision CFD result.

Constraints:

- Keep this as background, not Chapter 5 result interpretation.
- Do not discuss linear-algebra-specific findings as CFD conclusions; use
  Goldberg/Higham/IEEE only for transferable floating-point principles.
- Keep to about 300-360 counted words.

Worker summary must report:

- where exponent ranges, unit roundoff, non-associativity, `-O3`/`-Ofast`,
  reciprocal/sqrt, Verificarlo/MCA, and `p32 != fp32` are addressed;
- whether Brogi et al. and optional Wang/Xia/Chen were used only for
  CFD-specific background, not for this report's result claims;
- which citations support which claims;
- whether the paragraph remains within word budget.

---

## Worker E: Section 2.5 Report 1 Gap

Assigned region:

```latex
% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Goal:

- End Chapter 2 with a short synthesis paragraph.
- Group the literature into:
  method foundations, benchmark design, and floating-point reliability.
- State the gap: Report 1 measures precision and hardware sensitivity under
  controlled Euler validation tests.
- Point forward to Chapters 3-5 without using "chapter owner" language:
  Chapter 3 defines the method, Chapter 4 defines the experimental design, and
  Chapter 5 reports measured validation and precision results.
- Keep MHD as future context, not a completed result.

Constraints:

- No new citations unless a sentence needs support.
- No detailed result claims or numerical values.
- Keep to about 70-110 counted words.

Worker summary must report:

- the final gap sentence;
- whether the chapter-to-chapter transition avoids internal planning language;
- whether MHD remains future/context only.

---

## Main-Agent Integration Review

After each worker:

1. Re-read only the edited section and the preceding/following section heading.
2. Check that the section satisfies its worker goals.
3. Check that the section does not duplicate Chapter 3/4/5 responsibilities.
4. If the section fails, dispatch a focused repair worker before continuing.
5. Record a short continuity note for the next worker.

The main agent must not directly rewrite failed prose. It must request a worker
repair.

After all workers:

1. Read full Chapter 2 for flow and terminology consistency.
2. Ensure all TODO/drafting comments have been removed from manuscript-facing
   text.
3. Confirm terms introduced in Chapter 2 support later chapters:
   Euler variables, ideal-gas closure, ideal MHD constraint, HRSC/Godunov
   context, binary32/binary64, unit roundoff, Verificarlo/MCA.
4. Confirm Chapter 2 does not contain implementation, design-matrix, or result
   material that belongs in Chapters 3-5.

---

## Required Three-Round Self-Check

Do not stop after worker edits. Complete all three self-check rounds. If any
round scores below 95/100, dispatch a focused repair worker and rerun that round
once. If after three full rounds the chapter still cannot reach 95/100, stop and
explain exactly which requirement blocks it.

### Round 1: Brief, Handbook, and Supervisor Coverage

Score Chapter 2 against the project brief, handbook, `manuscript_outline.md`,
and `supervisor_feedback_map.md` Chapter 2 requirements.

Checklist:

- Brief Literature/background [20%] bullets are visibly covered:
  Euler overview; ideal-MHD overview; finite-volume/HRSC overview;
  floating-point arithmetic and hardware/compiler/thread-ordering effects.
- Handbook background/literature and presentation expectations are met:
  clear English, acknowledged sources, concise structure, no raw AI prose.
- 2.1 defines `\gamma`, pressure, and total energy.
- 2.2 includes an ideal-MHD equation block or compact conservation form and
  explains `\nabla\cdot B=0`.
- 2.3 stays literature/background, not Chapter 3 method derivation or Chapter 5
  case-result description.
- 2.4 includes exponent ranges, unit roundoff, non-associativity example,
  `-O3`/`-Ofast`, reciprocal/square-root, Verificarlo/MCA, and `p32 != fp32`.
- 2.4 includes at least one CFD-specific precision source unless the worker
  gives a clear reason not to use it; Brogi et al. is the default.
- 2.5 states the Report 1 gap without internal planning language.

Pass threshold: 95/100.

### Round 2: Citation, Style, and Word-Budget Audit

Checklist:

- Every citation supports a specific sentence and appears in
  `references.bib`.
- Author-name prose is used where it improves clarity for specific methods,
  benchmarks, or tools.
- No unsupported citation decoration or broad literature padding.
- Prose passes `writing-literature-review`: topic sentences are clear, sources
  are grouped by function, and the gap statement follows from the literature.
- The chapter reads as background/literature, not as a mini Chapter 3 method
  derivation, Chapter 4 design chapter, or Chapter 5 result preview.
- Prose passes `academic-english-style`: careful hedging, no journalistic
  phrasing, no unsupported certainty.
- Prose passes `avoiding-ai-flavor`: no generic filler, marketing confidence,
  repeated template rhythm, or paragraph detached from this project.
- Chapter 2 remains within 850-950 counted-word target or reports why the
  equation blocks make local counting uncertain.

Pass threshold: 95/100.

### Round 3: Mechanical, LaTeX, and Forbidden-Token Check

Run from repository root:

```powershell
git diff --check -- report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```

Expected: no whitespace or patch-format warnings introduced by this pass.

```powershell
rg -n "TODO|LLM|drafting comment|week7|week8|week9|D1|D2|HLLC-fill|config12|LW12/config12|P1|USE_GPU|fp32 L1 error|fp64 L1 error" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```

Expected: no manuscript-facing hits.

Check citations:

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "^@" report1/phd-thesis-template-2.4/References/references.bib
```

Check labels/equations for obvious conflicts:

```powershell
rg -n "\\\\label|\\\\ref|\\\\begin\\{equation|\\\\begin\\{align" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
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

Pass threshold: no new Chapter 2 LaTeX errors, no forbidden-token hits, no
undefined citation introduced by this pass.

---

## Final Response Format

Respond in Chinese with:

- which C2 sections were drafted or revised by which worker;
- how the project brief, handbook, and supervisor requirements were addressed;
- how Draft 2 feedback was reflected without copying old prose;
- what sources/citations were used;
- whether any worker needed a repair pass;
- the three self-check scores and outcomes;
- compile/check results;
- remaining dependencies on Chapter 1, Chapter 3, Chapter 4, Chapter 5, or the
  References capitalization pass.

Do not claim the full report is finished.
