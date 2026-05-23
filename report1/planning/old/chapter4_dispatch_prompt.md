# Chapter 4 Dispatch Prompt

This is the Codex-ready master-agent prompt for drafting Chapter 4 of Report 1.
It follows `report1/planning/manuscript_outline.md` and mirrors the serial
worker/marker protocol used by `chapter5_dispatch_prompt.md`.

---

## Master prompt (paste below this line)

You are the main agent for the Report 1 drafting phase. Repository:

    c:\Users\tangy\Desktop\floatpoint

This round drafts only Chapter 4, "Implementation and Experimental Design".

Target file: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

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
10. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
11. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

Read these implementation files only to support Chapter 4 claims:

- `CMakeLists.txt`
- `cmake/PrecisionConfig.cmake`
- `cmake/CompilerFlags.cmake`
- `src/main.cpp`
- `src/euler/euler_solver.cpp`
- `src/euler/hancock.hpp`
- `src/euler/muscl.hpp`
- `src/euler/hllc.hpp`
- `src/gpu/euler_gpu_solver.cu`
- `src/gpu/euler_kernels.cu`
- `src/gpu/euler_kernels.cuh`
- `src/core/boundary.hpp`
- `src/utils/io.hpp`
- `scripts/build_all.sh`
- `scripts/regression/float_regression_report.py`

Lazy-load these style skills only when you are about to use them:

- `report1/skills/avoiding-ai-flavor/SKILL.md`
- `report1/skills/academic-english-style/SKILL.md`
- `report1/skills/scientific-writing-duke/SKILL.md`

### Hard rules

- Main agent does not write Chapter 4 prose. Its job is to read context,
  prepare the marker skeleton, dispatch workers, verify edits, enforce
  evidence/style/LaTeX consistency, run review rounds, and check citations.
  During improvement rounds, the main agent may make only integration edits:
  trimming, de-duplicating, fixing LaTeX/citation issues, and correcting
  source-backed wording. If a change requires new section-level prose, re-run
  the owning worker rather than editing freely.
- Each section is written by exactly one worker. Workers run serially. Never
  spawn two workers against `chapter4.tex` at the same time.
- A worker may modify only the region between its assigned markers.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned marker region."
- Do not modify solver numerics, cfg defaults, experiment results, output
  formats, or raw artifacts. Do not move files under `experiments/`.
- Chapter 4 explains the evidence-producing implementation and experimental
  design; it is not a user manual and should not become a command recipe.
- Stand-alone code path is the chosen Report 1 route. Mention AMReX only as a
  project-brief context or comparison point if needed; do not imply AMReX was
  used in the Report 1 experiments.
- Manuscript-facing prose, captions, labels, and figure paths must not contain:
  any `weekN` label, `D1`, `D2`, `HLLC-fill`, `config12`,
  `LW12/config12`, or `USE_GPU`.
- Manuscript prose uses "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)".
- Use `ENABLE_CUDA`, not `USE_GPU`, for the build option.
- Verificarlo `p32` is virtual precision, never IEEE fp32.
- "CPU/GPU zero drift" is bounded to matched CPU/GPU strict-HLLC runs,
  final-time or checkpointed conservative state as explicitly stated by the
  evidence, the tested cases, and the tested precisions. Do not generalise to
  stage-by-stage identity, non-strict builds, MHD, or untested cases.
- The CPU/GPU toolchain split must be disclosed: Toro3/Toro5 use Windows
  BuildTools; Sod/LW3/LW12 use Linux/WSL. Each within-case CPU/GPU comparison
  uses one matched binary.
- `experiments/week7/report1_validation_1d/summary.md` pair L1 is the
  fp64-fp32 final-state difference, not a separate fp32 or fp64 exact error.
- AI-assisted prose must pass `avoiding-ai-flavor`: no filler, no marketing
  tone, no unsupported confidence, and no generic paragraph that could fit an
  unrelated report.

### Chapter scope and word budget

Working target: 1000-1130 counted words. Overleaf counts pseudocode, so keep
the single pseudocode block to at most about 80 counted words. Section targets
below are deliberately tight and sum to 930-1125 counted words; if a worker
writes a table, keep it compact because tables are excluded from the controlling
Overleaf count but still affect presentation. The chapter should answer the Code
Description 20% requirement by explaining the implementation choices that make
the validation and precision evidence interpretable.

### Required implementation coverage

Workers must cover these four ease-of-implementation and optimization features:

1. fp32/fp64 templating in CPU and GPU solver code, selected by
   `FLOAT_PRECISION`.
2. CUDA-capable build switching via `ENABLE_CUDA=ON/OFF`, plus runtime
   `device=cpu/gpu` selection in CUDA-enabled binaries.
3. Python-driven regression/report harness that reruns validation matrices and
   compares outputs against references.
4. Matched-binary CPU-vs-GPU switch: each within-case CPU/GPU comparison is run
   from one binary, separating device switching from compiler/toolchain changes.

Workers must also explain the selected variation axes without changing code:

- `STRICT_IEEE=ON` for strict floating-point build controls,
- `RIEMANN_STRICT_INEQUALITY` for the HLLC `<` versus `<=` branch rule,
- HLLC versus Rusanov as deliberate solver/method variation,
- O2/O3/Ofast and fast-math compiler-flag comparisons,
- fp32 versus fp64 precision builds.

### Evidence and source coverage

Use these files as authoritative coverage. If a worker needs a row or claim not
covered here, it stops and reports.

| Evidence/source | Use in Chapter 4 |
|---|---|
| `CMakeLists.txt` | `ENABLE_CUDA`, `STRICT_IEEE`, `RIEMANN_STRICT_INEQUALITY`, solver libraries, CUDA source inclusion |
| `cmake/PrecisionConfig.cmake` | `FLOAT_PRECISION=float/double`, `HRSC_REAL`, `HRSC_PRECISION_NAME` |
| `cmake/CompilerFlags.cmake` | strict-IEEE CPU/CUDA flag intent |
| `src/main.cpp` | cfg parsing, `solver`, boundary selection, `device=cpu/gpu`, CPU/GPU dispatch, output writing |
| `src/euler/euler_solver.cpp` | CPU timestep structure, CFL, sweeps, boundary application, conservative update |
| `src/euler/hancock.hpp`, `src/euler/muscl.hpp` | reconstruction and half-step predictor |
| `src/euler/hllc.hpp` | HLLC wave-speed branch and `RIEMANN_STRICT_INEQUALITY` sensitivity axis |
| `src/gpu/euler_gpu_solver.cu`, `src/gpu/euler_kernels.cu/.cuh` | GPU mirror of CPU step, per-face kernels, device comparison basis |
| `src/core/boundary.hpp`, `src/utils/io.hpp` | boundary handling and binary output as comparability controls |
| `scripts/build_all.sh` | build matrix provenance |
| `scripts/regression/float_regression_report.py` | metric/report generation, device pairing, precision/reference comparisons |
| `tests/cases/toro_1d/toro_tests.hpp` | Toro initial states for auditable strong/supersonic-wave basis |
| `tests/cases/liska_wendroff_2d/lw_tests.hpp` | LW3/LW12 initial states for auditable benchmark-wave basis |
| `experiments/report1_evidence_map.md` | evidence routing and P0/P1 scope |
| `experiments/week6/regression/summary.md` | regression harness provenance only; not HLLC strict CPU/GPU claim |
| `experiments/week4/float_regression/1d/summary.md` | 1D exact-reference and float-double/reference provenance |
| `experiments/week4/float_regression/2d/summary.md` | 2D high-resolution-reference and float-double/reference provenance |
| `experiments/week7/report1_validation_1d/summary.md` | 1D validation matrix provenance |
| `experiments/week7/report1_validation_2d/summary.md` | LW3 validation matrix provenance |
| `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md` | Toro3/Toro5 matched CPU/GPU HLLC strict summary |
| `experiments/week7/report1_validation_1d_device/matrix.json` | Toro3/Toro5 Windows BuildTools matched-binary provenance |
| `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` | LW3 fp64 matched CPU/GPU HLLC strict summary |
| `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` | Sod fp32/fp64 and LW3 fp32 matched CPU/GPU HLLC strict summary |
| `experiments/week8/report1_2d_config12_fill/summary.md` | LW12 validation matrix provenance |
| `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md` | LW12 N=800 numerical-reference provenance |
| `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` | LW12 matched CPU/GPU HLLC strict summary |
| `experiments/week9/cpu_gpu_midtime/summary.md`, `experiments/week9/cpu_gpu_midtime_n400/summary.md` | checkpointed CPU/GPU evidence, if mentioned |
| `experiments/week9/variation_fp32/summary.md`, `experiments/week9/variation_fp32_extend/summary.md` | fp32 compiler-flag variation, if mentioned |

### Allowed citation policy

`report1/phd-thesis-template-2.4/References/references.bib` is already
populated. Workers may cite only existing keys and only when the citation
supports a sentence. For Chapter 4, allowed keys are:

| key | use in Chapter 4 |
|-----|------------------|
| `toro2009` | finite-volume/MUSCL-Hancock/HLLC algorithm structure |
| `ieee754_2019` | fp32/fp64 definitions |
| `goldberg_1991` | floating-point reproducibility and rounding framing |
| `higham_2002` | error/stability language |
| `liska_wendroff_2003` | LW3/LW12 benchmark source |
| `sod_1978` | Sod shock tube source |
| `bard_dorelli_2014` | GPU MUSCL-Hancock context if relevant |
| `zhang_etal_2019` | AMReX context only if AMReX is explicitly discussed as not used |

Workers may not invent citation keys or bibliography metadata. If a worker
believes a citation beyond this list is needed, it stops and reports the exact
claim needing support. The main agent may add a BibTeX entry only after checking
`report1/references/reference.md` or another primary/publisher source and must
run a final citation-key and BibTeX syntax check.

### LaTeX skeleton with markers

Step 0 before spawning any worker:

1. Snapshot the current `chapter4.tex` content.
2. Overwrite `chapter4.tex` with exactly this marker skeleton.
3. Run `rg -n "% <<SECTION_[1-5]_(BEGIN|END)>>" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`.
4. Confirm the command returns exactly 10 lines.
5. Dispatch Worker 1 only after the marker check passes.

```tex
%!TEX root = ../thesis.tex

\chapter{Implementation and Experimental Design}

\section{Implementation Route and Comparability Principle}
% <<SECTION_1_BEGIN>>
% (Worker 1 writes here.)
% <<SECTION_1_END>>

\section{Algorithmic Structure of the Implementation}
% <<SECTION_2_BEGIN>>
% (Worker 2 writes here.)
% <<SECTION_2_END>>

\section{Precision and Hardware Variants}
% <<SECTION_3_BEGIN>>
% (Worker 3 writes here.)
% <<SECTION_3_END>>

\section{Test-Case Matrix and Metrics}
% <<SECTION_4_BEGIN>>
% (Worker 4 writes here.)
% <<SECTION_4_END>>

\section{Reference-Solution Strategy}
% <<SECTION_5_BEGIN>>
% (Worker 5 writes here.)
% <<SECTION_5_END>>
```

### Marker protocol

Worker instruction:

> Read the current `chapter4.tex` in full. Locate exactly your assigned markers
> `% <<SECTION_n_BEGIN>>` and `% <<SECTION_n_END>>`. Replace only the complete
> marker-bounded region, including the BEGIN and END marker lines. The new
> content must keep both marker lines verbatim at the start and end. Do not
> touch text outside those markers. Do not rename markers. Do not insert new
> `\section{}` commands; the section heading is already outside your region.
> If your assigned markers do not appear exactly once each, stop and report.

After each worker returns, main agent verifies with `rg` and file comparison:

- all five BEGIN markers and all five END markers still exist exactly once,
- the other four marker-bounded regions are byte-identical to the pre-worker
  snapshot,
- the worker's region begins with its BEGIN marker and ends with its END marker.

If any check fails, restore `chapter4.tex` from the pre-worker snapshot and
re-dispatch that worker.

### Worker specs

Give every worker the hard rules, marker protocol, implementation/source
coverage table, citation shortlist, and its own section spec below. Each worker
must read every source/evidence file in its spec. Workers must not copy numeric
or technical claims from this prompt without checking the source. If a source
contradicts this prompt, the worker stops and reports.

#### Worker 1 - Implementation Route and Comparability Principle

Assigned markers: `SECTION_1_BEGIN` to `SECTION_1_END`.

Write Section 4.1, working target 190-230 words. Explain why Report 1 uses the
stand-alone code path: the implementation is organised so precision, hardware,
and selected implementation choices can vary while the nominal finite-volume
algorithm remains comparable. Mention AMReX only as project-brief context, and
state clearly that AMR/AMReX is not the route used for the reported Euler
evidence.

Must explicitly cover all four Code Description features:

- fp32/fp64 templating through one precision build flag,
- `ENABLE_CUDA` build switch and runtime `device=cpu/gpu`,
- Python regression/report harness,
- matched-binary CPU/GPU comparison principle.

Include the toolchain split disclosure in one sentence. Keep the prose about
scientific comparability, not operational build instructions.

Sources to read: `report1/planning/manuscript_outline.md`, `CMakeLists.txt`,
`cmake/PrecisionConfig.cmake`, `src/main.cpp`, `scripts/build_all.sh`,
`experiments/report1_evidence_map.md`.

Allowed citations if needed: `bard_dorelli_2014`, `zhang_etal_2019`.

#### Worker 2 - Algorithmic Structure of the Implementation

Assigned markers: `SECTION_2_BEGIN` to `SECTION_2_END`.

Write Section 4.2, working target 250-305 counted words including pseudocode.
Describe the report-level implementation path: configuration dispatch,
boundary treatment, CFL step selection, reconstruction, Hancock predictor,
Riemann flux, conservative update, output, and metric collection.

Include exactly one pseudocode box based on `EulerSolver::step` and the sweep
functions. Constraints:

- use a compile-safe structure already supported by the template, such as a
  `quote` block with short numbered lines, unless the main agent first enables
  an algorithm package in `Preamble/preamble.tex`;
- no more than 12 algorithm lines,
- each line about 7 words or fewer,
- total pseudocode about 80 counted words or fewer,
- no second algorithm box.

After the pseudocode, include one GPU-mirror paragraph of 60 words or fewer
explaining that the CUDA path mirrors the CPU sweep through per-face kernels.
Do not describe every kernel line-by-line. Connect `hllc.hpp` to the `<` versus
`<=` branch-sensitivity axis.

Sources to read: `src/main.cpp`, `src/euler/euler_solver.cpp`,
`src/euler/hancock.hpp`, `src/euler/muscl.hpp`, `src/euler/hllc.hpp`,
`src/gpu/euler_gpu_solver.cu`, `src/gpu/euler_kernels.cu`,
`src/gpu/euler_kernels.cuh`, `src/core/boundary.hpp`, `src/utils/io.hpp`.

Allowed citation: `toro2009`.

#### Worker 3 - Precision and Hardware Variants

Assigned markers: `SECTION_3_BEGIN` to `SECTION_3_END`.

Write Section 4.3, working target 170-210 words. Do not add a second matrix
unless it replaces prose without increasing length. Explain the fp32/fp64 and CPU/GPU variant matrix. State what is held
fixed and what is changed:

- same cfg-selected test/solver/boundary setup,
- precision selected at build time through `FLOAT_PRECISION`,
- CPU/GPU selected at runtime in CUDA-enabled binaries,
- strict build controls through `STRICT_IEEE=ON` where used,
- compiler and branch-rule variants isolated as separate variation axes.

Hedge any claim that cannot be fully separated experimentally. State that
matched CPU/GPU claims are within-case and within-binary, while cross-case
toolchain differences are disclosed rather than hidden.

Sources to read: `cmake/PrecisionConfig.cmake`, `cmake/CompilerFlags.cmake`,
`CMakeLists.txt`, `src/main.cpp`,
`experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`,
`experiments/week7/report1_validation_1d_device/matrix.json`,
`experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`,
`experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`,
`experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md`,
`experiments/week9/cpu_gpu_midtime/summary.md`, and
`experiments/week9/cpu_gpu_midtime_n400/summary.md`.

Allowed citations if needed: `ieee754_2019`, `goldberg_1991`, `higham_2002`.

#### Worker 4 - Test-Case Matrix and Metrics

Assigned markers: `SECTION_4_BEGIN` to `SECTION_4_END`.

Write Section 4.4, working target 220-290 counted words plus a compact
experimental-design matrix table. Chapter 4 owns the design matrix: it states
which cases, axes, references, and metrics the experiments are meant to cover.
Chapter 5 owns the results/evidence matrix and already contains
`tab:validation-matrix`; do not duplicate that label or contradict those rows.
The Chapter 4 design matrix must use a distinct label and have these columns:

- case,
- dimension,
- physical feature,
- supersonic? (Y/N plus which wave),
- basis for supersonic label,
- reference solution,
- metrics,
- hardware,
- precision.

The matrix must include Sod, Toro3, Toro5, LW3, and LW12. It must explicitly
show CPU and GPU coverage for each selected test, and fp32/fp64 coverage. It
must meet the brief's supersonic-wave requirement by marking and naming:

- Toro3: right-running supersonic shock,
- Toro5: collision of supersonic shocks,
- LW3: supersonic shock segments along quadrant interfaces,
- LW12: supersonic shock segments along quadrant interfaces.

For Sod, use an explicit Mach/wave-speed basis rather than a bare "supersonic"
tick. Define L1, Linf, ULP, SSIM, and reference/discretisation-scaled ratios
only as needed for Chapter 5 readability. Do not write local artifact labels in
the table.

Sources to read: `experiments/report1_evidence_map.md`,
`report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`,
`tests/cases/toro_1d/toro_tests.hpp`,
`tests/cases/liska_wendroff_2d/lw_tests.hpp`,
`experiments/week7/report1_validation_1d/summary.md`,
`experiments/week7/report1_validation_2d/summary.md`,
`experiments/week8/report1_2d_config12_fill/summary.md`,
`experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`,
`experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`,
`experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`,
`experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md`,
`experiments/week4/float_regression/1d/summary.md`,
`experiments/week4/float_regression/2d/summary.md`, and
`experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`.
When using `experiments/week7/report1_validation_1d/summary.md`, remember that
the pair L1 is fp64-fp32 final-state difference, not a separate fp32 or fp64
exact error.

Allowed citations: `sod_1978`, `toro2009`, `liska_wendroff_2003`.

#### Worker 5 - Reference-Solution Strategy

Assigned markers: `SECTION_5_BEGIN` to `SECTION_5_END`.

Write Section 4.5, working target 100-170 words. Explain why reference
solutions are needed to separate numerical/reference error from hardware or
precision drift. Use "exact" only for analytic/exact Riemann references. Use
"high-resolution reference" or "N=800 numerical reference" for 2D cases and
for LW12. State that the reference strategy is load-bearing for
float-double/reference ratios and for interpreting whether a drift is small.

Cover:

- 1D exact Riemann references for Sod/Toro-type shock tubes where used,
- high-resolution/converged numerical references for LW3,
- LW12 N=800 numerical reference,
- final-state conservative-state comparison for CPU/GPU rows,
- checkpointed CPU/GPU summaries only if used to bound time-evolution claims.

Sources to read: `experiments/week4/float_regression/1d/summary.md`,
`experiments/week4/float_regression/2d/summary.md`,
`experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`,
`experiments/week9/cpu_gpu_midtime/summary.md`,
`experiments/week9/cpu_gpu_midtime_n400/summary.md`.

Allowed citations if needed: `toro2009`, `liska_wendroff_2003`, `higham_2002`.

### Review rounds

Round 1: main agent reviews Chapter 4 against the hard rules, source/evidence
coverage, forbidden tokens, marker integrity, table compactness, citation keys,
pseudocode length, Chapter 5 consistency, and word budget. Fix only integration
defects, not worker ownership boundaries. If a section needs substantive new
prose, restore the pre-review snapshot for that section and re-dispatch the
owning worker with the specific defect.

Round 2: spawn one independent reviewing subagent (worker role: reviewer). It must not edit files.
Give it Chapter 4, the current Chapter 5 validation-matrix section, the
source/evidence coverage table, the hard rules, and this instruction:

> Review for unsupported implementation claims, missing Code Description
> features, wrong CPU/GPU or fp32/fp64 wording, missing toolchain disclosure,
> AMReX overclaiming, forbidden manuscript labels, table/pseudocode bloat,
> citation-key violations, Chapter 5 matrix contradictions or duplicate labels,
> and LaTeX risks. Return findings with file/line references. Do not modify
> files.

Main agent then fixes confirmed issues.

### Strict scoring and improvement iteration

After the worker draft and review rounds, the main agent must score Chapter 4
strictly against the Report 1 requirements before claiming it is ready. Use a
100-point rubric:

| Area | Points | What to check |
|------|--------|---------------|
| Implementation fidelity | 25 | Code path, build flags, cfg dispatch, CPU/GPU path, and harness descriptions match the source files. |
| Experimental design clarity | 20 | Precision, hardware, solver, compiler, branch, reference, and metric axes are separated clearly. |
| Code Description coverage | 20 | All four required implementation/optimization features are explicit and tied to comparability. |
| Evidence and scope control | 15 | No raw or planned artifact is overclaimed; toolchain split and reference limitations are stated. |
| Style and word budget | 10 | Prose is concise, non-generic, and under the 1130 counted-word hard limit including pseudocode. |
| LaTeX and citation correctness | 10 | Tables/pseudocode compile, citations use only allowed keys, and forbidden manuscript labels are absent. |

Then iterate:

1. Write a short self-review note with the score breakdown and top defects.
2. Address the highest-impact defects. Use direct edits only for integration
   issues; re-dispatch the owning worker for new section-level prose.
3. Re-score with the same rubric.
4. Repeat until either the score is at least 95/100 or three improvement rounds
   have completed.

If the score remains below 95/100 after three rounds, stop iterating and report
why. Classify each remaining limitation as one of:

- writing/editing issue that can still be improved without new data,
- implementation/source-reading issue that needs more careful checking,
- evidence gap that likely needs a new experiment, regenerated table, or
  additional figure.

After the final review, explicitly ask: "What would most improve Chapter 4 if
more time were available?" Answer it in the final response. If new experiment
results would materially improve the chapter, do not invent them and do not run
them unless the user asks; instead name the exact missing experiment, expected
artifact location, and the claim it would support.

### Verification before final response

Run these checks from the repository root:

```powershell
rg -n "week[0-9]+" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n "\bD1\b" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n "\bD2\b" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n -i "config\s*12|configuration-12|LW12/config12" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n "HLLC-fill" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n "USE_GPU" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n -U -i "p32(.|\n){0,120}IEEE fp32|IEEE fp32(.|\n){0,120}p32" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -n "\\label\\{tab:validation-matrix\\}" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Each command should return no manuscript-facing hit. If a forbidden token only
appears in an explanatory comment left inside the `.tex`, remove the comment.
The final label check prevents Chapter 4 from duplicating the existing Chapter 5
validation-matrix label; use a Chapter-4-specific label if the design matrix is
kept in Chapter 4.

Then compile:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Report any compile errors with file:line and state whether they originate in
Chapter 4 prose or unrelated template/bibliography wiring.

### Final response

Respond in Chinese. Include:

- which worker wrote which section,
- files changed,
- current Chapter 4 quality score,
- score breakdown and number of improvement rounds completed,
- remaining improvement opportunities after the final review,
- figures/tables/citations/experiments still missing,
- whether supplementary experiments are advised,
- if supplementary experiments are advised, the exact experiment/output needed
  and which claim it would strengthen,
- verification command results,
- which chapter to draft next.

Do not commit.
