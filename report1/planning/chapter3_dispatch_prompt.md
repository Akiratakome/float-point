# Chapter 3 Dispatch Prompt

This is the Codex-ready master-agent prompt for drafting Chapter 3 of Report 1.
It follows the structure of `chapter5_dispatch_prompt.md`, but is scoped to the
mathematical-method chapter. The example Report 1 PDF is used only for structure:
its Chapter 3 places the numerical method before implementation and results, and
uses equations and short method subsections rather than a literature-style survey.

---

## Master prompt (paste below this line)

You are the main agent for the Report 1 drafting phase. Repository:

    c:\Users\tangy\Desktop\floatpoint

This round drafts only Chapter 3, "Numerical Method".

Target file: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

### Required reading

Read these files before dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/WRITING_AGENT.md`
5. `report1/planning/reportagents.md`
6. `report1/planning/manuscript_outline.md`
7. `experiments/report1_evidence_map.md`
8. `report1/references/reference.md`
9. `report1/planning/drafting_status.md`
10. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
11. Already drafted chapters that Chapter 3 must remain consistent with:
    - `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
    - `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
12. Relevant source files for method fidelity:
    - `src/euler/euler_solver.cpp`
    - `src/euler/euler_solver.hpp`
    - `src/euler/muscl.hpp`
    - `src/euler/hancock.hpp`
    - `src/euler/hllc.hpp`
    - `src/euler/rusanov.hpp`
    - `src/euler/euler_flux.hpp`
    - `src/gpu/euler_gpu_solver.hpp`
    - `src/gpu/euler_kernels.cu`
    - `CMakeLists.txt`

Lazy-load these style skills only when you are about to use them:

- `report1/skills/avoiding-ai-flavor/SKILL.md`
- `report1/skills/academic-english-style/SKILL.md`
- `report1/skills/scientific-writing-duke/SKILL.md`

### Hard rules

- Main agent does not write Chapter 3 prose. Its job is to read context,
  prepare the marker skeleton, dispatch workers, verify edits, enforce
  method/style/LaTeX consistency, run review rounds, and add only the BibTeX
  entries actually cited.
- Each section is written by exactly one worker. Workers run serially. Never
  spawn two workers against `chapter3.tex` at the same time.
- A worker may modify only the region between its assigned markers.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned marker region."
- Do not modify solver numerics, cfg defaults, experiment results, output
  formats, or raw artifacts. Do not move files under `experiments/`.
- Chapter 3 is mathematical method, not implementation detail. It may name the
  source files used to verify the method, but manuscript prose should not read
  like source-code documentation.
- Do not describe MHD as validated Report 1 evidence. MHD appears only as
  project context and Report 2 direction.
- Manuscript-facing prose, captions, labels, and figure paths must not contain:
  `week7`, `week8`, `D1`, `D2`, `HLLC-fill`, `config12`,
  `LW12/config12`, or `USE_GPU`.
- Use `ENABLE_CUDA`, not `USE_GPU`, if a compile flag must be named.
- Do not treat Verificarlo `p32` as IEEE fp32.
- Do not claim fp32 adequacy or CPU/GPU equivalence in Chapter 3. Chapter 3 may
  explain why those axes are measured later, but numerical claims belong to
  Chapters 5 and 6 and must be tied to evidence there.
- Do not write "as shown below" for sensitivity axes without completed evidence.
  In Chapter 3, measured axes are limited to the HLLC branch-rule comparison,
  compiler-flag comparison, HLLC-vs-Rusanov solver variation, and completed
  fp32 compiler-flag evidence. Limiter sensitivity has no completed result and
  must be framed as a method limitation, not as a measured axis.
- AI-assisted prose must pass `avoiding-ai-flavor`: no filler, no marketing
  tone, no unsupported confidence, and no generic paragraph that could fit an
  unrelated report.

### Chapter target and structure

Working target: 1,080-1,220 Overleaf-counted words. Hard upper: 1,220. The
per-worker prose lower bounds below sum to 1,080, and upper bounds sum to 1,205,
leaving a small buffer for equation text that Overleaf may count. Workers must
not undershoot their lower bound, and the main agent must reject a worker draft
whose counted words fall below the assigned lower bound and re-dispatch.

Purpose: demonstrate mathematical understanding of the finite-volume HRSC method
used to generate the Report 1 evidence. The chapter should be equation-led but
not equation-heavy. The example Report 1 PDF uses a conventional structure in
which numerical-method theory precedes implementation and validation; follow that
role, not its scientific content.

The chapter should do five things:

1. Define the finite-volume conservative update and notation.
2. Explain the second-order MUSCL-Hancock reconstruction and predictor.
3. Explain the HLLC flux choice, with Rusanov as a deliberate comparator.
4. State stability, limiting, and positivity caveats.
5. Identify finite-precision-sensitive algorithmic decisions before the
   implementation and results chapters quantify them.

### Allowed citation policy

Use `report1/references/reference.md` as the citation map. Add BibTeX entries
only for citations used in the final Chapter 3 draft.

Allowed citation keys for Chapter 3:

| key | source | use in Chapter 3 |
|-----|--------|------------------|
| `toro2009` | Toro, *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed., 2009 | finite-volume update, MUSCL-Hancock, CFL, HLLC, limiter discussion |
| `leveque_2002` | LeVeque, *Finite Volume Methods for Hyperbolic Problems*, 2002 | optional support for finite-volume conservation-law formulation |
| `vanleer_1979` | van Leer, JCP 32(1), 1979 | MUSCL reconstruction if the section cites the primary MUSCL source |
| `toro_spruce_speares_1994` | Toro, Spruce, and Speares, *Shock Waves* 4, 1994 | HLLC/contact restoration |
| `harten_lax_vanleer_1983` | Harten, Lax, and van Leer, *SIAM Review* 25(1), 1983 | optional HLL-family background if HLL is named |
| `goldberg_1991` | Goldberg, ACM Comput. Surv. 23(1), 1991 | finite-precision branch/rounding motivation |
| `higham_2002` | Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed., 2002 | disciplined rounding-error and stability language |
| `ieee754_2019` | IEEE Std 754-2019 | optional support only if IEEE semantics are explicitly named |
| `bard_dorelli_2014` | Bard and Dorelli, JCP 259, 2014 | optional MHD/GPU bridge only if citation cap allows |
| `dedner_2002` | Dedner et al., JCP 175, 2002 | optional divergence-cleaning mention only |
| `evans_hawley_1988` | Evans and Hawley, ApJ 332, 1988 | optional constrained-transport mention only |

The following keys from the allowed list are **not yet present** in
`report1/phd-thesis-template-2.4/References/references.bib` and must be added
only if actually cited: `vanleer_1979`, `toro_spruce_speares_1994`,
`harten_lax_vanleer_1983`, `dedner_2002`, `evans_hawley_1988`. The remaining
allowed keys (`toro2009`, `leveque_2002`, `goldberg_1991`, `higham_2002`,
`ieee754_2019`, `bard_dorelli_2014`) are already in `references.bib` from
Ch4/Ch5 use; do not duplicate them.

If a missing key is used, verify metadata from `report1/references/reference.md`,
add the entry to `references.bib`, and recompile. Do not add ornamental
citations.

Before the final response, the main agent must extract every `\cite*{...}` key
from `chapter3.tex` and confirm each appears in `references.bib`. Treat any
missing key as a blocking defect, not a cosmetic issue. Suggested commands:

    rg -no "\\\\cite[a-zA-Z]*\\{[^}]+\\}" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
    # for each key K printed above:
    rg -n "@\\w+\\{$K," report1/phd-thesis-template-2.4/References/references.bib

### LaTeX skeleton with markers

Before spawning any worker, main agent inspects `chapter3.tex`. The current
file is a placeholder: it contains only `\chapter{Numerical Method}`, five
empty `\section{...}` headings, and `% TODO` comments referring to
`manuscript_outline.md`. This counts as a placeholder and **must** be
overwritten. Specifically, treat the file as a placeholder if every section
body between consecutive `\section{...}` lines contains only comment lines
(`%` prefix), whitespace, or `\todo`/`% TODO` markers, and contains no
non-comment LaTeX prose. In that case, save a snapshot at
`report1/phd-thesis-template-2.4/Chapter3/chapter3_pre_dispatch_snapshot.tex`
and then rewrite `chapter3.tex` to exactly this marker skeleton (note: the
skeleton renames §3.4 to "Stability, Limiting, and Positivity" and adds a new
§3.6, which differs from the current placeholder; this is intentional and
matches `manuscript_outline.md` §3.4–§3.6).

If substantive Chapter 3 prose is already present (any non-comment, non-TODO
sentence inside a section body), stop and report instead of overwriting it.

```tex
%!TEX root = ../thesis.tex

\chapter{Numerical Method}

\section{Finite-Volume Update}
% <<SECTION_1_BEGIN>>
% (Worker 1 writes here.)
% <<SECTION_1_END>>

\section{MUSCL-Hancock Reconstruction and Predictor Step}
% <<SECTION_2_BEGIN>>
% (Worker 2 writes here.)
% <<SECTION_2_END>>

\section{HLLC and Rusanov Fluxes}
% <<SECTION_3_BEGIN>>
% (Worker 3 writes here.)
% <<SECTION_3_END>>

\section{Stability, Limiting, and Positivity}
% <<SECTION_4_BEGIN>>
% (Worker 4 writes here.)
% <<SECTION_4_END>>

\section{Precision-Sensitive Decision Points}
% <<SECTION_5_BEGIN>>
% (Worker 5 writes here.)
% <<SECTION_5_END>>

\section{Extension to Ideal MHD}
% <<SECTION_6_BEGIN>>
% (Worker 6 writes here.)
% <<SECTION_6_END>>
```

### Marker protocol

Worker instruction:

> Read the current `chapter3.tex` in full. Locate exactly your assigned markers
> `% <<SECTION_n_BEGIN>>` and `% <<SECTION_n_END>>`. Replace only the complete
> marker-bounded region, including the BEGIN and END marker lines. The new
> content must keep both marker lines verbatim at the start and end. Do not
> touch text outside those markers. Do not rename markers. Do not insert new
> `\section{}` commands; the section heading is already outside your region.
> If your assigned markers do not appear exactly once each, stop and report.

After each worker returns, main agent verifies with `rg` and file comparison:

- all six BEGIN markers and all six END markers still exist exactly once,
- the other five marker-bounded regions are byte-identical to the pre-worker
  snapshot,
- the worker's region begins with its BEGIN marker and ends with its END marker.

If any check fails, restore `chapter3.tex` from the pre-worker snapshot and
re-dispatch that worker.

### Method facts workers must preserve

- The report method is a finite-volume HRSC method for the compressible Euler
  equations with conserved variables consistent with Chapter 2.
- The scheme evolves cell averages with conservative flux differences.
- The main second-order method is MUSCL-Hancock: limited piecewise-linear
  reconstruction followed by a half-step predictor and a Riemann-solver flux.
- The implemented limiter path uses minbee/minmod-style limiting in the report
  path. Other limiter functions exist in source/tests, but there is no completed
  report evidence for limiter variation; do not present limiter comparison as a
  result.
- HLLC is the main flux for report validation because it resolves the contact
  wave better than HLL/Rusanov-type two-wave diffusion. Rusanov is a more
  diffusive comparator and a method-variation axis, not the main method.
- HLLC branch selection has a compile-time `<` versus `<=` variation controlled
  by `RIEMANN_STRICT_INEQUALITY`; this is separate from `STRICT_IEEE`.
- CPU and GPU method descriptions must stay consistent: the GPU path mirrors
  the CPU MUSCL-Hancock/HLLC structure for the tested report runs, but detailed
  dispatch and matched-binary evidence belongs in Chapter 4 and Chapter 5.
- CFL restriction is based on characteristic speeds such as `|u|+a` in 1D and
  directional speeds in 2D. Keep the statement qualitative unless the exact
  formula is verified from source.
- Positivity and stability should be framed as practical caveats for strong
  shocks/near-vacuum cases, not as proven guarantees.

### Worker specs

Give every worker the hard rules, marker protocol, method facts, citation
shortlist, and its own section spec below. Workers must read every source or
artifact in their spec. If a source contradicts this prompt, the worker stops
and reports.

#### Worker 1 - Finite-Volume Update

Assigned markers: `SECTION_1_BEGIN` to `SECTION_1_END`.

Write Section 3.1, working target 180-200 words plus equations. Define cell
averages, conserved state, numerical flux, grid spacings, and time step. Present
the 1D update and, if concise, the 2D unsplit-or-split flux-difference form used
for notation. Explain that conservation follows because neighbouring cells share
equal and opposite interface fluxes.

Requirements:

- Use notation that can carry forward to the Euler variables and Chapter 5
  metrics.
- Keep equations clear and limited to what is needed.
- Do not discuss implementation files except as private verification context.

Read:

- `src/euler/euler_solver.cpp`
- `src/euler/euler_solver.hpp`
- `src/euler/euler_flux.hpp`
- `report1/planning/manuscript_outline.md` Chapter 3

Allowed citations: `toro2009`, optionally `leveque_2002`.

#### Worker 2 - MUSCL-Hancock Reconstruction and Predictor Step

Assigned markers: `SECTION_2_BEGIN` to `SECTION_2_END`.

Write Section 3.2, working target 200-225 words. Explain how MUSCL-Hancock
raises the finite-volume method to second order in smooth regions: reconstruct
left/right interface states with a limited slope, evolve those states through a
half-step predictor, then pass predicted states to the Riemann solver. Mention
that the project brief favours MUSCL-Hancock because Riemann-solver behaviour is
central to the precision/hardware study. Do not introduce WAF or other
alternative second-order schemes; they are not used in the report evidence.

Requirements:

- Include a compact equation or short algorithm-style list only if it fits the
  word budget.
- State that limiting reduces oscillations near discontinuities but can reduce
  local order near extrema or shocks.
- Do not claim a measured limiter comparison.

Read:

- `src/euler/muscl.hpp`
- `src/euler/hancock.hpp`
- `src/gpu/euler_kernels.cu` only for consistency with the GPU mirror
- `report1/planning/reportagents.md` §3.2

Allowed citations: `toro2009`, `vanleer_1979`.

#### Worker 3 - HLLC and Rusanov Fluxes

Assigned markers: `SECTION_3_BEGIN` to `SECTION_3_END`.

Write Section 3.3, working target 200-225 words. Explain the role of the
Riemann solver in providing interface fluxes. Present HLLC as the main solver
for the validation evidence and explain contact restoration conceptually through
the left, contact, and right wave structure. Introduce Rusanov only as a
deliberately more diffusive comparator used later to separate method variation
from reproducibility drift.

Requirements:

- Do not derive the full HLLC star-state algebra unless needed; a concise
  conceptual description is enough.
- Make clear that HLLC branch decisions are revisited in Section 3.5.
- Do not overclaim HLLC superiority for all flows.

Read:

- `src/euler/hllc.hpp`
- `src/euler/rusanov.hpp`
- `src/euler/euler_solver.cpp`
- `experiments/report1_evidence_map.md` rows for solver variation

Allowed citations: `toro2009`, `toro_spruce_speares_1994`, optionally
`harten_lax_vanleer_1983`.

#### Worker 4 - Stability, Limiting, and Positivity

Assigned markers: `SECTION_4_BEGIN` to `SECTION_4_END`.

Write Section 3.4, working target 170-195 words. Describe CFL control, limiter
effects, dimensional sweeps if needed for clarity, and practical positivity or
near-vacuum caveats. Distinguish formal second-order behaviour in smooth regions
from reduced accuracy near shocks, contacts, and limiter activation.

Requirements:

- State the CFL idea in terms of signal speeds and cell size.
- Mention that strong discontinuities and near-vacuum states can stress the
  method; do not claim a proof of positivity.
- Keep boundary-condition detail for Chapter 4 unless a one-sentence method
  connection is necessary.

Read:

- `src/euler/euler_solver.cpp`, especially CFL calculation and sweeps
- `src/euler/muscl.hpp`
- `experiments/week8/toro2_lt_branch_retry/summary.md` only as evidence for
  why near-vacuum branch sensitivity matters later; do not quote detailed
  result values here unless the outline requires it. Reminder: the path
  contains `week8`, which is a forbidden manuscript-facing token. Read the
  summary for context only; never write the path, `week8`, or the directory
  name `toro2_lt_branch_retry` into the prose.

Allowed citations: `toro2009`, `vanleer_1979`, optionally `higham_2002` for
careful numerical-stability wording.

#### Worker 5 - Precision-Sensitive Decision Points

Assigned markers: `SECTION_5_BEGIN` to `SECTION_5_END`.

Write Section 3.5, working target 230-250 words. Explain why branch conditions,
tolerances, limiter decisions, reductions, and compiler options can be visible
in finite-precision runs. Use the project brief's `<` versus `<=` HLLC
wave-speed example. State explicitly which axes are measured in Report 1 and
which are concept-only.

Measured in Report 1:

- HLLC `<` versus `<=` branch-rule comparison, controlled by
  `RIEMANN_STRICT_INEQUALITY`.
- Compiler flags: O2/O3/Ofast and fast-math variants.
- HLLC versus Rusanov as method variation.
- fp32 compiler-flag sensitivity if the completed fp32 variation artifacts are
  used later.

Concept-only in Report 1:

- Exact-solver tolerances.
- Parallel-reduction order beyond the controlled CFL/reduction tests discussed
  in implementation.
- Limiter variation. Although `experiments/week9/variation_limiter/summary.md`
  exists and `manuscript_outline.md` §3.5 left this as a possible upgrade, the
  run does not isolate limiter choice from numerical-path changes; therefore
  Chapter 3 frames limiter sensitivity as a method limitation only. Do not
  read this as a contradiction with the outline; treat it as a deliberate
  scope tightening for Chapter 3 and stop only if `summary.md` evidence
  directly contradicts the limitation framing.

Requirements:

- Do not claim large effects; say the report measures selected effects.
- Do not use local evidence labels such as `D1` or week numbers.
- Do not confuse `RIEMANN_STRICT_INEQUALITY` with `STRICT_IEEE`.

Read:

- `CMakeLists.txt`
- `src/euler/hllc.hpp`
- `experiments/report1_evidence_map.md`
- `experiments/week7/report1_variation/summary.md`
- `experiments/week8/report1_variation_extend/summary.md`
- `experiments/week9/variation_fp32/summary.md`
- `experiments/week9/variation_fp32_extend/summary.md`
- `experiments/week9/variation_limiter/summary.md`

Allowed citations: `goldberg_1991`, `higham_2002`, optionally `ieee754_2019`
if IEEE semantics are named.

#### Worker 6 - Extension to Ideal MHD

Assigned markers: `SECTION_6_BEGIN` to `SECTION_6_END`.

Write Section 3.6, working target 100-110 words. This is a short bridge only.
Explain that the Euler method provides a controlled validation base for the
later ideal-MHD project, where additional wave families and the divergence-free
magnetic-field constraint introduce extra numerical choices. Mention divergence
cleaning or constrained transport only if cited, and do not present any MHD
validation as completed.

Requirements:

- Keep the section under 140 counted words.
- Do not name a chosen MHD method unless the report actually implements and
  validates it.
- Keep Bard and Dorelli citation use within the global citation cap: at most two
  appearances in the whole manuscript.

Read:

- `report1/planning/manuscript_outline.md` §3.6 and References Plan
- `report1/references/reference.md` MHD references

Allowed citations: optionally `bard_dorelli_2014`, `dedner_2002`,
`evans_hawley_1988`.

### Review rounds

Round 1: main agent reviews Chapter 3 against the hard rules, method facts,
forbidden tokens, marker integrity, equation notation, citation keys, and word
budget. Also compare terminology and claims against the completed Chapter 4 and
Chapter 5 drafts, especially MUSCL--Hancock--HLLC wording, CFL notation,
`STRICT_IEEE`, `RIEMANN_STRICT_INEQUALITY`, CPU/GPU scope, and fp32/fp64 scope.
Fix only integration defects, not worker ownership boundaries.

Round 2: spawn one independent `worker` as a reviewer. It must not edit files.
Give it Chapter 3, the hard rules, method facts, citation shortlist, and this
instruction:

> Review for mathematical inaccuracies, unsupported claims, forbidden manuscript
> labels, overclaiming about fp32/CPU-GPU/MHD, notation inconsistency, citation
> misuse, repeated AI-flavoured phrasing, and LaTeX risks. Return findings with
> file/line references. Do not modify files.

Main agent then fixes confirmed issues.

### Strict scoring and improvement iteration

After the worker draft and review rounds, the main agent must score Chapter 3
strictly against the Report 1 requirements before claiming it is ready. Use a
100-point rubric:

| Area | Points | What to check |
|------|--------|---------------|
| Mathematical correctness | 25 | Finite-volume update, MUSCL-Hancock, HLLC/Rusanov, CFL, and limiting are described accurately and with consistent notation. |
| Project-method fidelity | 20 | The prose matches the implemented report method without drifting into unused schemes or unmeasured axes. |
| Precision/hardware setup | 15 | Branch, compiler, solver, and precision-sensitive choices are introduced without making Chapter 5 result claims. |
| Scope control | 15 | MHD is future context; no fp32 adequacy, CPU/GPU equivalence, or unvalidated MHD claims appear. |
| Style and integrity | 15 | Prose passes `avoiding-ai-flavor`, is specific to this project, and avoids generic textbook padding. |
| LaTeX and citation correctness | 10 | Equations compile, citations are supported and present in `references.bib`, and labels/cross-references are stable. |

Then iterate:

1. Write a short self-review note with the score breakdown and top defects.
2. Revise Chapter 3 to address the highest-impact defects. The main agent may
   make only integration, notation, citation, LaTeX, and short style fixes.
   Substantive paragraph rewrites must be re-dispatched to the worker that owns
   the affected marker region.
3. Re-score with the same rubric.
4. Repeat until either the score is at least 90/100 or three improvement rounds
   have completed.

If the score remains below 90/100 after three rounds, stop iterating and report
why. Classify each remaining limitation as one of:

- writing/editing issue that can still be improved without new data,
- method-fidelity issue that needs more source-code reading,
- evidence-boundary issue that should be handled in Chapters 4-6 rather than
  Chapter 3.

### Verification before final response

Run these checks from the repository root:

```powershell
rg -n "week7" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "week8" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "\bD1\b" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "\bD2\b" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "config12" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "HLLC-fill" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "USE_GPU" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -nE "fp32 is (sufficient|adequate|enough|fine|acceptable|sufficiently accurate)" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -nE "fp32 (suffices|works|is OK|is fine)" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "hardware has no effect" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "MHD validation" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "Lyapunov exponent" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "\\cite[[:alpha:]]*(\\[[^]]*\\])*\\{[^}]+\\}" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

The forbidden-token commands should return no manuscript-facing hit. If a
forbidden token only appears in an explanatory comment left inside the `.tex`,
remove the comment. The citation command is expected to list any Chapter 3
citation uses; every listed key must be present in
`report1/phd-thesis-template-2.4/References/references.bib`.

Then compile. If any new BibTeX entry was added, run the full pdflatex/bibtex
sequence so undefined-citation warnings actually resolve (a single pdflatex
pass will not pick up new bib entries):

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If no bib entries were added, the single `pdflatex -draftmode` pass is
sufficient.

Report any compile errors with file:line and state whether they originate in
Chapter 3 prose or unrelated template/bibliography wiring.

### Final response

Respond in Chinese. Include:

- which worker wrote which section,
- files changed,
- current Chapter 3 quality score,
- score breakdown and number of improvement rounds completed,
- remaining improvement opportunities after the final review,
- citations added or still missing,
- verification command results,
- whether Chapter 3 should be followed by Chapter 4 or revised after Chapter 5
  result wording stabilises.

Do not commit.
