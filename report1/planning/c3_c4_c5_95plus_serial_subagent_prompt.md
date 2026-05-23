# C3-C5 95+ Serial Subagent Revision Prompt

This prompt is for a main agent that will revise Report 1 Chapters 3, 4, and 5
through serial section-scoped subagents. The purpose is not a broad rewrite. The
purpose is to close the remaining gaps against the original project PDF,
supervisor feedback, Report 1 writing skills, formatting/word-count constraints,
and chapter-ownership boundaries.

Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript files:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Do not modify:

```text
experiments/
src/
tests/
cfg files
solver numerics
experiment output formats
raw experiment artifacts
```

Manuscript-facing derived figure files under
`report1/phd-thesis-template-2.4/Figs/report1/` may be inspected, but do not
regenerate figures in this prompt unless a later user explicitly asks for
figure regeneration.

## Main-Agent Mandate

The main agent must:

1. Read all required context before dispatching workers.
2. Dispatch exactly one worker at a time.
3. Never allow two workers to edit the same file concurrently.
4. After each worker returns, inspect only the edited region plus one paragraph
   before and after it.
5. Reject and repair any worker output that violates the original PDF,
   supervisor feedback, chapter ownership, evidence boundaries, or writing
   skills.
6. Maintain a short integration note after each worker.
7. Run the final verification and strict score against the original PDF.

The main agent may make mechanical integration edits only:

- marker preservation;
- fixing a broken reference caused by a worker edit;
- correcting whitespace or a one-word forbidden-token replacement;
- replacing a duplicate phrase introduced at a boundary.

Any substantive prose, table, or equation change must be made by the relevant
section-scoped worker.

Tell every worker:

```text
You are not alone in the codebase. Edit only your assigned section or local
paragraph. Do not revert or overwrite changes outside your scope. Do not modify
solver numerics, cfg defaults, experiment artifacts, or anything under
experiments/.
```

## Required Reading

Before dispatching workers, the main agent reads:

```text
docs/INDEX.md
docs/HARNESS.md
report1/INDEX.md
report1/planning/reportagents.md
report1/planning/manuscript_outline.md
report1/planning/supervisor_feedback_map.md
report1/planning/supervisorguide.md
experiments/report1_evidence_map.md
report1/references/reference.md
report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
report1/phd-thesis-template-2.4/References/references.bib
```

Use `pdftotext` if the PDF text needs to be inspected locally.

Read these skills before any prose edit:

```text
report1/skills/scientific-writing-duke/SKILL.md
report1/skills/academic-english-style/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
```

Skill use:

- `scientific-writing-duke`: methods/results paragraph logic.
- `academic-english-style`: hedging, scope, and academic stance.
- `avoiding-ai-flavor`: final acceptance gate for each edited paragraph.

## Original PDF Requirements To Enforce

Use this as the strict baseline, not the old `draft2.pdf`.

### Mathematical Theory [20%]

Chapter 3 must visibly cover:

- a second-order explicit finite-volume method;
- MUSCL-Hancock or equivalent Riemann-solver-based method;
- HLLC as the main approximate Riemann solver, with Rusanov only as comparator;
- MHD-specific numerical variations, including wave families and divergence
  cleaning;
- algorithmic points that can be varied, especially `<` versus `<=` and other
  precision-sensitive decisions.

### Code Description [20%]

Chapter 4 must visibly cover:

- the stand-alone implementation route;
- how CPU/GPU and fp32/fp64 variants are selected;
- how the same nominal algorithm is kept comparable;
- the reproducibility/testing framework;
- how compiler options and floating-point tolerances or branch choices are
  explored;
- how exact or converged reference solutions are determined.

### Validation [20%]

Chapter 5 must visibly cover:

- at least four Euler ideal-gas test cases;
- both 1D and 2D tests;
- supersonic waves;
- CPU and GPU evaluation;
- quantified CPU/GPU differences;
- single-vs-double precision accuracy comparison.

### Quality of Write-Up [20%]

Chapters 3-5 must:

- use readable equations, tables, figures, and captions;
- define terms before use;
- avoid internal planning labels;
- keep claims bounded to evidence;
- avoid AI-flavoured prose;
- compile cleanly.

## Supervisor Feedback To Enforce

The workers must close the remaining C3-C5 feedback gaps:

- C3: add Dedner-style divergence-cleaning extra equation with `\psi`.
- C3: remove overfull long flag-list line and avoid "rows" as a generic word.
- C4: add concise reproducibility/testing framework paragraph.
- C4: make supersonic-wave coverage explicit and auditable.
- C4: number the remaining displayed equations.
- C5: remove duplicate ratio definition and refer back to C4.
- C5: compress CPU/GPU zero-drift prose.
- C5: reduce repeated numeric prose in the variation section.

Already-fixed items must stay fixed:

- `p32` is not IEEE fp32.
- `ENABLE_CUDA`, not `USE_GPU`.
- no `config12`; use "Liska-Wendroff configuration 12 (LW12)" or "LW12".
- no `week7`, `week8`, `D1`, `D2`, `HLLC-fill`, `P1`, or "Lyapunov-like".
- no claim of MHD validation.
- no claim that fp32 is generally adequate.
- no claim that hardware has no effect generally.

## Chapter Ownership Boundary

- C3 owns theory and method choices.
- C4 owns implementation, reproducibility harness, design matrix, metrics, and
  reference strategy.
- C5 owns measured results and evidence-bound interpretation.

Cross-chapter links expected after this pass:

- C3 MUSCL-Hancock/HLLC/Rusanov/CFL theory appears in C4 algorithm and C5
  validation/variation.
- C4 `R_{\mathrm{ref}}` definition is used by C5 instead of being redefined.
- C4 matched-device definition is respected by C5 CPU/GPU claims.
- C4 reference strategy is reflected in C5 exact-reference and numerical-reference
  interpretation.

## Preflight Checks

Before dispatching Worker 1, run:

```powershell
rg -n "% <<SECTION_[0-9]+_(BEGIN|END)>>" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Confirm:

- Chapter 3 has 6 begin markers and 6 end markers.
- Chapter 4 has 5 begin markers and 5 end markers.
- Chapter 5 has 6 begin markers and 6 end markers.

Run baseline word counts:

```powershell
texcount -inc -sum -merge -q report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
texcount -inc -sum -merge -q report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
texcount -inc -sum -merge -q report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Record baseline text-word counts in the final response.

Run baseline forbidden-token check:

```powershell
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|well resolved in binary64|vertical interface" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected before editing: no manuscript-facing hits. If hits exist, record them
and repair only if within the worker scopes below.

## Serial Worker Plan

### Worker 1: C3 §3.6 MHD Cleaning Equation

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Assigned region:

```latex
\section{Extension to Ideal MHD}
% <<SECTION_6_BEGIN>>
...
% <<SECTION_6_END>>
```

Worker must read:

```text
report1/planning/supervisor_feedback_map.md
report1/references/reference.md
report1/phd-thesis-template-2.4/References/references.bib
```

Task:

- Add one compact Dedner-style cleaning equation.
- Define `\psi`, `c_h`, and `\tau`.
- Keep the current Report 1 boundary that MHD is not validated here.
- Do not add new MHD evidence or imply MHD implementation.
- Keep section near 210-230 prose words by compressing nearby prose.

Use this mathematical form unless a better existing local phrasing is already
present:

```latex
\begin{equation}\label{eq:ch3-dedner-cleaning}
  \partial_t \mathbf{B}
  + \nabla\cdot(\mathbf{u}\mathbf{B}-\mathbf{B}\mathbf{u})
  + \nabla\psi = 0,
  \qquad
  \partial_t \psi + c_h^2\nabla\cdot\mathbf{B} = -\psi/\tau .
\end{equation}
```

Acceptance criteria:

- `\label{eq:ch3-dedner-cleaning}` exists.
- `\psi`, `c_h`, and `\tau` are defined.
- `\citet{dedner_2002}` or `\citep{dedner_2002}` remains.
- `\citet{evans_hawley_1988}` or `\citep{evans_hawley_1988}` remains.
- Report 1 Euler-only validation boundary remains.

Main-agent review after Worker 1:

- Check the equation is correct enough for conceptual Report 1 context.
- Check no MHD validation claim entered.
- Check the section did not grow into a mini MHD method chapter.

### Worker 2: C3 §3.5 Variation-Axis Compression

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Assigned local scope:

```latex
\paragraph{Method components and build switches.}
...
\paragraph{Variation axes by status.}
...
% <<SECTION_5_END>>
```

Task:

- Replace "compiler-flag rows" with "compiler-flag comparisons".
- Replace the long `itemize` variation list with a compact paragraph.
- Preserve the measured / concept-only / Report 2 distinction.
- Preserve `RIEMANN_STRICT_INEQUALITY`, `STRICT_IEEE`, and `FAST_MATH`.
- Do not remove the near-zero caveat for `<` versus `<=` earlier in §3.5.

Suggested paragraph:

```latex
\paragraph{Variation axes by status.}
Measured Report~1 axes are the HLLC branch rule, gcc
\texttt{-O2}/\texttt{-O3}/\texttt{-Ofast} with fast-math, HLLC versus
Rusanov, and fp32/fp64. Concept-only axes are exact-Riemann stopping
tolerances, limiter choice, and CPU/GPU reduction ordering. Report~2 axes are
CPU architecture and \texttt{-mtune}/vectorisation, MPI/OpenMP thread-count
variation, and Boost::Multiprecision quad precision.
```

Acceptance criteria:

- No generic "rows" remains in C3.
- No long itemized flag line remains.
- The overfull hbox risk is reduced.
- C3 text word count decreases relative to baseline unless Worker 1's equation
  offsets it.

Main-agent review after Worker 2:

- Confirm C3 still covers the original PDF mathematical-theory bullets.
- Confirm §3.5 is method-level, not a results paragraph.

### Worker 3: C4 §4.2 Reproducibility Harness and Equation Numbering

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Assigned region:

```latex
\section{Algorithmic Structure of the Implementation}
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Worker must read:

```text
docs/HARNESS.md
report1/planning/supervisor_feedback_map.md
```

Task:

- Add a compact reproducibility/testing-framework paragraph.
- Convert the CFL display equation to a numbered equation with label
  `eq:ch4-cfl-scan`.
- Compress at least 60 words from §4.2 so the section does not grow.
- Keep CUDA/thread block/OpenMP definitions.
- Keep CFL as max/min comparison, not summation sensitivity.
- Do not cite source paths.

Required harness paragraph, adapted only for flow:

```latex
Reproducibility follows the harness sequence: configuration, build, run,
measurement, aggregation, and plotting. Matrix runs copy the source
configuration into a generated run directory rather than editing it in place,
then save stdout, stderr, binary path, precision, device, build label, command,
and output path as metadata. Chapter~5 uses the aggregated summaries and
report-facing figures from these runs, not raw grids as direct evidence.
```

Required equation form:

```latex
\begin{equation}\label{eq:ch4-cfl-scan}
  \Delta t = C_{\mathrm{CFL}}
  \min\left(\frac{\Delta x}{\max_{i,j}(|u|+c)},
             \frac{\Delta y}{\max_{i,j}(|v|+c)}\right),
\end{equation}
```

Acceptance criteria:

- C4 visibly satisfies the original PDF testing/reproducibility requirement.
- `eq:ch4-cfl-scan` exists.
- No source-path explanation is introduced.
- §4.2 does not become longer overall.

Main-agent review after Worker 3:

- Confirm C4 still owns implementation/design, not results.
- Confirm C5 can later point to the harness/design without redefining it.

### Worker 4: C4 §4.4 Supersonic Coverage and `R_ref` Numbering

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Assigned region:

```latex
\section{Test-Case Matrix and Metrics}
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Task:

- Make the supersonic-wave requirement explicit and auditable.
- Convert the `R_{\mathrm{ref}}` display to a numbered equation with label
  `eq:ch4-rref`.
- Do not widen the table.
- Do not add new result values.
- Do not use `config12`.

Required supersonic sentence, adapted only for flow:

```latex
The supersonic-wave requirement is met by four entries in this matrix: Toro3
has a right-running supersonic shock, Toro5 has colliding supersonic shocks,
and LW3 and LW12 contain supersonic quadrant-interface shocks in Liska and
Wendroff's initial states. Sod is retained as the lower-severity exact-reference
baseline rather than as the main supersonic example.
```

Required equation form:

```latex
\begin{equation}\label{eq:ch4-rref}
R_{\mathrm{ref}} =
\frac{\|U_{\mathrm{fp32}}-U_{\mathrm{fp64}}\|_1}
     {\|U_{\mathrm{fp64}}-U_{\mathrm{ref}}\|_1}.
\end{equation}
```

Acceptance criteria:

- Toro3, Toro5, LW3, and LW12 are named as supersonic cases.
- `eq:ch4-rref` exists.
- C4 does not report measured result values.
- Design matrix remains readable.

Main-agent review after Worker 4:

- Confirm the original PDF validation test-case requirement is now auditable
  from C4 before C5.
- Confirm C5 can reference `eq:ch4-rref`.

### Worker 5: C5 §5.4 Remove Duplicate Metric Definition

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Assigned region:

```latex
\section{Single- and Double-Precision Comparison}
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Task:

- Remove the duplicate unnumbered ratio equation from C5.
- Replace it with a cross-reference to `Equation~\ref{eq:ch4-rref}`.
- Keep all LW3, LW12, Sod, Toro3, Toro5, and stationary-contact interpretation.
- Keep the statement that fp32 is not generally sufficient.
- Keep the bounded LW12 interpretation: precision sensitivity near reconstructed
  states and HLLC wave-speed/flux decisions, but no branch-change proof.

Replacement sentence:

```latex
Using the reference-scaled ratio defined in Equation~\ref{eq:ch4-rref},
Fig.~\ref{fig:ch5-float-double-over-reference} reports the direct IEEE
fp32--fp64 density comparison for LW3.
```

Acceptance criteria:

- No `equation*` ratio definition remains in §5.4.
- C5 explicitly reflects C4 metric architecture.
- No direct fp32 claim uses Verificarlo `p32`.

Main-agent review after Worker 5:

- Confirm C5 is result-facing, not design-defining.
- Confirm no measured values were changed accidentally.

### Worker 6: C5 §5.5 CPU/GPU Compression

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Assigned region:

```latex
\section{Matched CPU/GPU Comparison}
% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Task:

- Keep the CPU/GPU coverage table and toolchain footnote.
- Replace repetitive zero-drift prose after the table with one dense bounded
  paragraph.
- Preserve saved-output and checkpoint boundaries.
- Do not generalise to all devices, compilers, solvers, or MHD.

Required replacement paragraph:

```latex
All 14 final-output comparisons in Table~\ref{tab:ch5-cpu-gpu} are zero in
\(L_1\), \(L_\infty\), and \(\mathrm{ULP}_{\max}\). The 40 saved-checkpoint
comparisons for Sod, LW3, and LW12 are also zero. These statements are bounded
to matched within-case binaries, listed precisions, strict-HLLC builds, and
saved outputs; they do not imply equality of unsaved intermediate stages or of
other devices, compilers, solvers, or cases.
```

Acceptance criteria:

- Toolchain footnote remains.
- Saved-output boundary remains.
- CPU/GPU result remains quantified.
- Prose is shorter than before.

Main-agent review after Worker 6:

- Confirm original PDF CPU/GPU quantification remains satisfied.
- Confirm supervisor low-information zero-table concern remains addressed.

### Worker 7: C5 §5.6 Variation-Prose Compression

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Assigned local scope:

```latex
\subsection*{Compiler, branch-rule, and solver variation}
```

Stop before:

```latex
\subsection*{Time-resolved drift and Toro2 branch stability}
```

Task:

- Keep the variation tables.
- Remove prose that repeats table values unnecessarily.
- Keep actual values in the tables.
- Keep HLLC versus Rusanov framed as method variation.
- Keep compiler flags referenced through C3/C4 rather than listed in prose.
- Do not edit the drift subsection.

Replacement paragraph after `tab:ch5-variation`:

```latex
The zero O2--O3 comparison shows that changing optimisation level alone did not
alter the saved final state in the tested IEEE builds. The branch-rule axis is
zero for the one-dimensional cases and only roundoff-scale for LW3. Fast-math
produces the largest CPU-fp64 HLLC drift on Toro5, while the HLLC--Rusanov
entry is much larger because the flux formula has changed. These are screening
metrics, not convergence studies or estimates of uncertainty across compilers
and platforms.
```

Acceptance criteria:

- No values needed for supervisor feedback are lost; they remain in tables.
- Prose interprets scale and category rather than repeating table rows.
- No "P1 probe" or other internal label appears.
- C5 word count decreases.

Main-agent review after Worker 7:

- Confirm §5.6 still satisfies the original PDF compiler/options/implementation
  variation direction.
- Confirm no drift/non-completion boundary was damaged.

## Main-Agent Integration Pass

After Worker 7:

1. Re-read the opening paragraph of C3, C4, and C5.
2. Re-read all edited sections.
3. Check cross-chapter chain:
   - C3 theory is reflected in C4 implementation and C5 results.
   - C4 design matrix, metrics, matched-device definition, and reference
     strategy are reflected in C5.
   - C5 does not redefine C4's design or C3's method.
4. Fix only local transition issues.
5. If a substantive problem remains, dispatch a focused repair worker before
   running final verification.

## Final Verification

Run from repository root.

### Forbidden/Internal Language

```powershell
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|well resolved in binary64|vertical interface" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: no manuscript-facing hits.

### `p32` and Generalisation Check

```powershell
rg -n "p32|Verificarlo|fp32 is generally|fp32 is adequate|hardware has no effect|MHD validation|generally sufficient" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:

- Any `p32` hit distinguishes virtual mantissa from IEEE fp32.
- Any "generally sufficient" hit must be a negative boundary sentence.
- No MHD validation claim.

### AI-Flavor and Supervisor Wording Check

```powershell
rg -n "delve|leverage|unlock|groundbreaking|transformative|seamless|remarkable|extremely|incredibly|undoubtedly|it is important to note|landscape|robust|comprehensive|cutting-edge|\brows\b|\bRows\b" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:

- No banned AI-flavor terms.
- No generic "rows"; replace with "comparisons", "entries", or "table
  entries" if found.

### Equation Check

```powershell
rg -n -F '\[' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n -F '\]' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:

- C3 and C4 should have no unnumbered display-equation `\[` / `\]` hits.
- C5 should not contain the removed §5.4 unnumbered ratio equation.
- Bracket hits inside matrix row spacing such as `\\[2pt]` are acceptable.

### Word Count

```powershell
texcount -inc -sum -merge -q report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
texcount -inc -sum -merge -q report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
texcount -inc -sum -merge -q report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:

| Chapter | Preferred | Acceptable |
|---|---:|---:|
| C3 text words | <= 1350 | <= 1380 if MHD equation is the only excess |
| C4 text words | <= 1150 | <= 1200 if reproducibility paragraph remains dense |
| C5 text words | <= 1950 | must not exceed 1950 |

If a chapter exceeds the acceptable limit, dispatch a focused compression worker
for the edited section that caused the excess.

### Compile

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Expected:

- exit code 0;
- no undefined citations;
- no undefined references;
- no new overfull hbox in edited regions.

If citations were changed, run:

```powershell
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

## Strict Final Scoring Against Original PDF

Score C3, C4, and C5 independently after verification. Use the original PDF as
the highest-priority assessment source, supervisor feedback as required
refinement, and `report1/skills` as prose-quality gates.

### Chapter 3 Score

| Area | Points |
|---|---:|
| Second-order Riemann-solver-based method, MUSCL-Hancock, HLLC/Rusanov | 25 |
| MHD numerical variation and Dedner/Evans-Hawley divergence-control context | 20 |
| Algorithmic variation points: `<` vs `<=`, FMA, compiler/build switches, concept/future axes | 20 |
| Supervisor fixes and term definitions | 15 |
| Style, citations, equation numbering, word budget, compile | 20 |

95+ requires:

- Dedner `\psi` equation present.
- No result claims in C3.
- No overfull hbox from edited flag list.
- C3 remains concise enough for the global word budget.

### Chapter 4 Score

| Area | Points |
|---|---:|
| Stand-alone implementation route and CPU/GPU/fp32/fp64 controls | 20 |
| Reproducibility/testing framework and modification axes | 25 |
| Metrics, matched-device definition, flags, Verificarlo/MCA boundary | 20 |
| Test matrix, supersonic coverage, reference strategy, downsampling | 20 |
| Style, chapter ownership, word budget, compile | 15 |

95+ requires:

- Harness/reproducibility paragraph present.
- Supersonic wave requirement auditable from C4.
- `p32 != fp32` retained.
- C4 defines design and metrics without presenting results.

### Chapter 5 Score

| Area | Points |
|---|---:|
| Euler validation coverage: >=4 cases, 1D/2D, supersonic waves | 20 |
| CPU/GPU quantified comparison | 20 |
| fp32/fp64 accuracy comparison against reference/discretisation scale | 20 |
| Variation axes: compiler, branch, solver, drift/non-completion boundary | 20 |
| Interpretation, C4 linkage, style, figure/table readability, compile | 20 |

95+ requires:

- C5 uses C4 metric/reference architecture instead of redefining it.
- CPU/GPU zero-drift claim is compact, quantified, and bounded.
- Variation prose interprets rather than repeats table values.
- No general fp32, hardware, or MHD claims.

If any chapter scores below 95:

1. Identify the single highest-impact defect.
2. Dispatch one focused repair worker for that local defect.
3. Re-run the relevant verification commands.
4. Re-score.
5. Stop after two repair rounds and report any remaining blocker.

## Final Response Format

Respond in Chinese.

Include:

- list of workers dispatched and the section each edited;
- exact local edits made;
- original PDF requirement gaps closed;
- supervisor-feedback gaps closed;
- C3/C4/C5 baseline and final word counts;
- forbidden-token, `p32`, AI-flavor, equation, and compile results;
- final C3/C4/C5 scores against the original PDF;
- remaining risks and whether they block 95+.

Do not claim the full Report 1 is complete unless Chapters 1, 2, 6, 7/front
matter, abstract, references, and final Overleaf counted-word declaration have
also been checked.
