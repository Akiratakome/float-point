# Chapter 5 Dispatch Prompt

This is the Codex-ready master-agent prompt for drafting Chapter 5 of Report 1. Working as As a Cambridge master student studying Scientific Computing.
It is self-contained: worker tasks are included inline, worker edits are serial,
and all evidence/citation constraints needed for the dispatch are listed here.

---

## Master prompt (paste below this line)

You are the main agent for the Report 1 drafting phase. Repository:

    c:\Users\tangy\Desktop\floatpoint

This round drafts only Chapter 5, "Validation and Precision Results".

Target file: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

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
10. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

Lazy-load these style skills only when you are about to use them:

- `report1/skills/avoiding-ai-flavor/SKILL.md`
- `report1/skills/academic-english-style/SKILL.md`
- `report1/skills/scientific-writing-duke/SKILL.md`

### Hard rules

- Main agent does not write Chapter 5 prose. Its job is to read context,
  prepare the marker skeleton, dispatch workers, verify edits, enforce
  evidence/style/LaTeX consistency, run review rounds, and add only the BibTeX
  entries actually cited.
- Each section is written by exactly one worker. Workers run serially. Never
  spawn two workers against `chapter5.tex` at the same time.
- A worker may modify only the region between its assigned markers.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned marker region."
- Do not modify solver numerics, cfg defaults, experiment results, output
  formats, or raw artifacts. Do not move files under `experiments/`.
- Do not describe planned supplementary experiments as completed.
- Do not write MHD as a completed Report 1 result.
- Manuscript-facing prose, captions, labels, and figure paths must not contain:
  `week7`, `week8`, `D1`, `D2`, `HLLC-fill`, `config12`,
  `LW12/config12`, or `USE_GPU`.
- Manuscript prose uses "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)".
- Verificarlo `p32` is virtual precision, never IEEE fp32.
- "CPU/GPU zero drift" is bounded to matched CPU/GPU strict-HLLC runs,
  final-time conservative state, the tested cases, and the tested precisions.
  Do not extend it to intermediate time, non-strict builds, MHD, or untested
  cases.
- `experiments/week7/report1_validation_1d/summary.md` pair L1 is the
  fp64-fp32 final-state difference, not a separate fp32 or fp64 exact error.
- 1D exact/reference-scaled numerical values must come from
  `experiments/week4/float_regression/1d/summary.md` or its CSVs.
- LW12 reference is an N=800 numerical reference, not an exact solution.
- AI-assisted prose must pass `avoiding-ai-flavor`: no filler, no marketing
  tone, no unsupported confidence, and no generic paragraph that could fit an
  unrelated report.

### Verified artifact coverage

Workers must take coverage from this table and from the evidence checklist
below. If a row a worker needs is absent, the worker stops and reports.

Figures already present under `report1/phd-thesis-template-2.4/Figs/report1/`:

- `sod_comparison.png`
- `toro3_comparison.png`
- `toro5_comparison.png`
- `lw3_n400_double_rho_schlieren.png`
- `lw12_n400_double_rho_schlieren.png`
- `drift_timeseries_l1_normalized.png`
- `float_double_over_reference_bar.png`

Workers reference these by `Figs/report1/<name>.png`. Do not rename figure
files. If a worker needs a new figure, it stops and reports.

CPU/GPU device-comparison coverage (HLLC strict, final-time conservative state,
matched within-case binary differing only by runtime device switch):

| case  | precision | N       | drift                | toolchain  | evidence file |
|-------|-----------|---------|----------------------|------------|---------------|
| Sod   | fp64      | 200     | bit-identical zero   | Linux/WSL  | `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` |
| Sod   | fp32      | 200     | bit-identical zero   | Linux/WSL  | same |
| Toro3 | fp64      | 200     | zero L1/Linf/ULP     | Windows BT | `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md` |
| Toro3 | fp32      | 200     | zero                 | Windows BT | same |
| Toro5 | fp64      | 200     | zero                 | Windows BT | same |
| Toro5 | fp32      | 200     | zero                 | Windows BT | same |
| LW3   | fp64      | 200,400 | zero                 | Linux/WSL  | `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` |
| LW3   | fp32      | 200,400 | bit-identical zero   | Linux/WSL  | `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` |
| LW12  | fp64      | 200,400 | zero                 | Linux/WSL  | `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` |
| LW12  | fp32      | 200,400 | zero                 | Linux/WSL  | same |

There is no fp32 final-time variation row for compiler/branch sensitivity in
the current artifacts. Worker 6 reports CPU double only for variation rows
unless a completed supplementary artifact is found and explicitly cited.

### Allowed citation policy

`report1/phd-thesis-template-2.4/References/references.bib` is currently empty.
For Chapter 5, allowed `\cite{...}` keys are restricted to this shortlist.
Workers may not add new keys or BibTeX entries. If a worker believes a cite is
needed beyond this list, it stops and reports.

| key | source | use in Chapter 5 |
|-----|--------|------------------|
| `toro2009` | Toro, *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed., 2009 | Toro tests, wave speeds, shock-tube framing |
| `liska_wendroff_2003` | Liska and Wendroff, SIAM J. Sci. Comput. 25(3), 2003 | LW3 and LW12 2D Riemann configurations |
| `sod_1978` | Sod, JCP 27(1), 1978 | Sod shock tube |
| `ieee754_2019` | IEEE Std 754-2019 | fp32/fp64 format definition if needed |
| `goldberg_1991` | Goldberg, ACM Comput. Surv. 23(1), 1991 | rounding/cancellation framing if needed |

Main agent adds actual BibTeX entries to `references.bib` after worker edits,
and only for keys cited in the final Chapter 5 draft. Do not pre-populate the
`.bib` file

### LaTeX skeleton with markers

Before spawning any worker, main agent rewrites `chapter5.tex` to exactly this
marker skeleton:

```tex
%!TEX root = ../thesis.tex

\chapter{Validation and Precision Results}

\section{Validation Matrix}
% <<SECTION_1_BEGIN>>
% (Worker 1 writes here.)
% <<SECTION_1_END>>

\section{One-Dimensional Euler Validation}
% <<SECTION_2_BEGIN>>
% (Worker 2 writes here.)
% <<SECTION_2_END>>

\section{Two-Dimensional Euler Validation}
% <<SECTION_3_BEGIN>>
% (Worker 3 writes here.)
% <<SECTION_3_END>>

\section{Single- and Double-Precision Comparison}
% <<SECTION_4_BEGIN>>
% (Worker 4 writes here.)
% <<SECTION_4_END>>

\section{Matched CPU/GPU Comparison}
% <<SECTION_5_BEGIN>>
% (Worker 5 writes here.)
% <<SECTION_5_END>>

\section{Compiler, Branch, Solver, and Drift-Growth Sensitivity}
% <<SECTION_6_BEGIN>>
% (Worker 6 writes here.)
% <<SECTION_6_END>>
```

### Marker protocol

Worker instruction:

> Read the current `chapter5.tex` in full. Locate exactly your assigned markers
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

If any check fails, restore `chapter5.tex` from the pre-worker snapshot and
re-dispatch that worker

### Evidence checklist

Before dispatching, confirm these files exist and read the key numbers:

- `experiments/week7/report1_validation_1d/summary.md`
- `experiments/week3/week3_validation/plots/sod_comparison.png`
- `experiments/week3/week3_validation/plots/toro3_comparison.png`
- `experiments/week3/week3_validation/plots/toro5_comparison.png`
- `experiments/week4/float_regression/1d/summary.md`
- `experiments/week7/report1_validation_2d/summary.md`
- `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho_schlieren.png`
- `experiments/week4/float_regression/2d/summary.md`
- `experiments/week8/report1_2d_config12_fill/summary.md`
- `experiments/week8/report1_2d_config12_fill/precision_summary.md`
- `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`
- `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png`
- `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`
- `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`
- `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`
- `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md`
- `experiments/week7/report1_variation/summary.md`
- `experiments/week8/report1_variation_extend/summary.md`
- `experiments/week7/lyapunov_1d_full/summary.md`
- `experiments/week8/toro2_lt_branch_retry/summary.md`
- `experiments/week7/report1_d2_replots/float_double_over_reference.csv`
- `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png`

### Worker specs

Give every worker the hard rules, marker protocol, verified coverage table,
citation shortlist, and its own section spec below. Each worker must read every
artifact in its spec. Workers must not copy numeric values from this prompt
without checking the artifact. If an artifact contradicts this prompt, the
worker stops and reports.

#### Worker 1 - Validation Matrix

Assigned markers: `SECTION_1_BEGIN` to `SECTION_1_END`.

Write Section 5.1, working target 220-300 words plus one compact LaTeX table if
needed. Introduce Chapter 5 as a controlled study, not a sequence of plots.
Separate four questions: solver correctness, fp32/fp64 accuracy, CPU/GPU
reproducibility, and sensitivity to selected implementation/compiler
variations. Define or refer to the metrics used later: L1, Linf, ULP, SSIM, and
reference/discretisation-scaled ratios. Include a compact validation matrix if
it is useful; otherwise write a short prose overview and leave detailed tables
to later sections. Do not use local week labels.

Evidence to read:

- `experiments/report1_evidence_map.md`
- `experiments/week7/report1_validation_1d/summary.md`
- `experiments/week7/report1_validation_2d/summary.md`
- `experiments/week8/report1_2d_config12_fill/summary.md`
- all CPU/GPU evidence files in the coverage table

#### Worker 2 - One-Dimensional Euler Validation

Assigned markers: `SECTION_2_BEGIN` to `SECTION_2_END`.

Write Section 5.2, working target 300-380 words. Start with why the 1D tests
come before precision/hardware interpretation. Interpret Sod, Toro3, and Toro5.
When introducing Toro3 and Toro5, name the supersonic structures explicitly:
Toro3 has a right-running supersonic shock; Toro5 involves collision of
supersonic shocks. Include figure references for `sod_comparison.png`,
`toro3_comparison.png`, and `toro5_comparison.png` only if the section actually
discusses them.

Must include at least three checked numerical values:

- one fp64-fp32 final-state L1 difference from
  `experiments/week7/report1_validation_1d/summary.md`,
- one exact/reference-scaled 1D value from
  `experiments/week4/float_regression/1d/summary.md` or its CSVs,
- one CPU/GPU drift value from
  `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`.

Do not call the fp64-fp32 pair value a separate fp64 or fp32 exact error. Avoid
"looks good"; state which waves are captured and how the metrics support
validation.

Allowed citations: `sod_1978`, `toro2009`.

#### Worker 3 - Two-Dimensional Euler Validation

Assigned markers: `SECTION_3_BEGIN` to `SECTION_3_END`.

Write Section 5.3, working target 300-380 words. Treat LW3 and LW12 as separate
2D Riemann configurations. Introduce each as "Liska-Wendroff configuration 3
(LW3)" and "Liska-Wendroff configuration 12 (LW12)"; do not write `config12`.
Name the supersonic shock segments along the quadrant interfaces when
introducing each case. Interpret the N=400 double-precision schlieren figures
for LW3 and LW12 by naming visible wave structures, then connect the visual
evidence to quantitative metrics.

For LW12, verify and report the N=800-reference comparison: rho L1
double-reference error decreases from about `2.95e-3` at N=200 to about
`1.33e-3` at N=400, and rho SSIM increases from about `0.989` to about
`0.996`. State that this is a higher-resolution numerical reference, not an
exact solution.

Evidence to read:

- `experiments/week7/report1_validation_2d/summary.md`
- `experiments/week4/float_regression/2d/summary.md`
- `experiments/week8/report1_2d_config12_fill/summary.md`
- `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`
- the LW3 and LW12 figure files listed above

Allowed citation: `liska_wendroff_2003`.

#### Worker 4 - Single- and Double-Precision Comparison

Assigned markers: `SECTION_4_BEGIN` to `SECTION_4_END`.

Write Section 5.4, working target 280-360 words. Compare fp32 and fp64 by
asking whether the fp32-fp64 gap is smaller than, larger than, or comparable to
reference/discretisation error for the tested cases. Use
`float_double_over_reference_bar.png` if it is discussed in prose.

Required caveats:

- The 1D `stationary_contact` row has `L1_p fmd/d_err = inf` because the
  double-vs-reference error is zero on an exact-stationary case. Treat it as a
  degenerate-reference row, not as a quantitative adequacy ratio.
- For LW3, the 2D float-double/reference `L1_rho` ratio grows from about
  `4.5e-5` at N=200 to about `9.3e-5` at N=400 because reference error shrinks
  faster than float-double drift.
- For LW12, the same direction appears against the N=800 reference:
  `L1_rho` ratio about `4.63e-5` at N=200 and about `1.30e-4` at N=400.
- End with one pointer sentence that Section 6.2 interprets the spatial
  structure of precision sensitivity using Verificarlo virtual-precision
  diagnostics. Do not include region-aware LoSoS margins or p32 interpretation
  in Chapter 5.

Evidence to read:

- `experiments/week7/report1_validation_1d/summary.md`
- `experiments/week7/report1_validation_2d/summary.md`
- `experiments/week8/report1_2d_config12_fill/precision_summary.md`
- `experiments/week4/float_regression/1d/summary.md`
- `experiments/week4/float_regression/2d/summary.md`
- `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`
- `experiments/week7/report1_d2_replots/float_double_over_reference.csv`

Allowed citations if needed: `ieee754_2019`, `goldberg_1991`.

#### Worker 5 - Matched CPU/GPU Comparison

Assigned markers: `SECTION_5_BEGIN` to `SECTION_5_END`.

Write Section 5.5, working target 280-360 words plus one compact table if
needed. Quantify CPU/GPU differences for Sod, Toro3, Toro5, LW3, and LW12 under
`solver=hllc` and `STRICT_IEEE=ON` in fp32 and fp64. Use the coverage table as
the scope, but verify the values in the files. Report zero L1/Linf/ULP drift
only where the summaries show it. Bound the claim to final-time conservative
state, tested cases, tested precisions, strict HLLC, and matched within-case
binaries.

The CPU/GPU table must carry one footnote stating:

- Toro3/Toro5 were built with Windows BuildTools.
- Sod/LW3/LW12 were built with Linux/WSL.
- Each within-case CPU/GPU comparison uses one matched binary, so bit-identity
  is claimed within a case, not across toolchains.

If an intermediate-time CPU/GPU supplementary artifact has completed, add one
sentence reporting it. If not, keep the final-time-only boundary explicit.
Do not use local week numbers or internal fill names.

Evidence to read: all four CPU/GPU files in the coverage table.

Allowed citations if needed: `goldberg_1991`.

#### Worker 6 - Compiler, Branch, Solver, and Drift-Growth Sensitivity

Assigned markers: `SECTION_6_BEGIN` to `SECTION_6_END`.

Write Section 5.6, working target 360-460 words. Split the section internally
with two `\subsection*{...}` headings:

1. `Compiler, branch-rule, and solver variation`
2. `Time-resolved drift and Toro2 branch stability`

For the first part, build around one summary table or compact prose-table
covering Sod, stationary_contact, LW3-N200, Toro3, and Toro5 under:

- `<=` vs `<` HLLC wave-speed branch, mapped to
  `RIEMANN_STRICT_INEQUALITY`,
- O2/O3/Ofast and fast-math compiler comparisons,
- HLLC vs Rusanov as deliberate method variation, not reproducibility drift.

State once that rows are CPU double only unless a completed fp32 supplementary
artifact is found and explicitly added as a tagged row. Use descriptive labels:
"branch-rule comparison", "compiler-flag comparison", "solver-variation
comparison". Do not write `D1`, `D2`, or week labels.

For the second part, use `drift_timeseries_l1_normalized.png` and the Toro2
retry summary. Constraints:

- Fitted lambda values are finite-time slopes from 10 synchronized checkpoints;
  do not use the term "Lyapunov exponent" in manuscript prose.
- Toro2 under `<` did not complete; the independent retry reproduces
  non-completion of `<` while `<=` completes in about `0.13 s` under the same
  toolchain. Report this as branch-specific stability degradation on the
  near-vacuum 123 case, not as zero drift.
- Keep the time-resolved subsection under 200 counted words.

Evidence to read:

- `experiments/week7/report1_variation/summary.md`
- `experiments/week8/report1_variation_extend/summary.md`
- `experiments/week7/lyapunov_1d_full/summary.md`
- `experiments/week8/toro2_lt_branch_retry/summary.md`
- `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png`

Allowed citations if needed: `goldberg_1991`.

### Review rounds

Round 1: main agent reviews Chapter 5 against the hard rules, evidence list,
forbidden tokens, marker integrity, figure references, citation keys, and word
budget. Fix only integration defects, not worker ownership boundaries.

Round 2: spawn one independent `worker` as a reviewer. It must not edit files.
Give it Chapter 5, the evidence checklist, the hard rules, and this instruction:

> Review for unsupported claims, forbidden manuscript labels, wrong fp32/fp64
> wording, CPU/GPU overgeneralisation, missing table/figure interpretation,
> citation-key violations, and LaTeX risks. Return findings with file/line
> references. Do not modify files.

Main agent then fixes confirmed issues.

### Strict scoring and improvement iteration

After the worker draft and review rounds, the main agent must score Chapter 5
strictly against the Report 1 requirements before claiming it is ready. Use a
100-point rubric:

| Area | Points | What to check |
|------|--------|---------------|
| Evidence fidelity | 25 | Every numerical claim is traceable to a listed artifact; no planned result is presented as completed; fp64-fp32, CPU/GPU, and reference-error quantities are named correctly. |
| Validation coverage | 20 | Sod, Toro3, Toro5, LW3, and LW12 are covered; supersonic-wave requirements are explicit; CPU/GPU and fp32/fp64 scope is bounded to tested cases. |
| Interpretation quality | 20 | Figures and tables are interpreted rather than merely displayed; claims compare against metrics, reference error, or discretisation error. |
| Style and integrity | 15 | Prose passes `avoiding-ai-flavor`, avoids generic filler, and reads like a restrained technical report. |
| LaTeX and citation correctness | 10 | Figures compile, labels/captions are stable, citations use only allowed keys, and `references.bib` contains only cited entries. |
| Scope control | 10 | No forbidden manuscript labels, no overclaiming for MHD, intermediate time, non-strict builds, untested cases, or virtual p32. |

Then iterate:

1. Write a short self-review note with the score breakdown and the top defects.
2. Revise Chapter 5 to address the highest-impact defects.
3. Re-score with the same rubric.
4. Repeat until either the score is at least 90/100 or three improvement rounds
   have completed.

If the score remains below 90/100 after three rounds, stop iterating and report
why. Classify each remaining limitation as one of:

- writing/editing issue that can still be improved without new data,
- evidence interpretation issue that needs more careful reading of existing
  artifacts,
- evidence gap that likely needs a new experiment or regenerated figure/table.

After the final review, explicitly ask: "What would most improve Chapter 5 if
more time were available?" Answer it in the final response. If new experiment
results would materially improve the chapter, do not invent them and do not run
them unless the user asks; instead name the exact missing experiment, expected
artifact location, and the claim it would support.

### Verification before final response

Run these checks from the repository root:

```powershell
rg -n "week7" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "week8" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "\bD1\b" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "\bD2\b" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "config12" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "HLLC-fill" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "USE_GPU" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "fp32 L1 error" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "fp64 L1 error" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n "Lyapunov exponent" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n -U "LW12(.|\n)*config12" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Each command should return no manuscript-facing hit. If a forbidden token only
appears in an explanatory comment left inside the `.tex`, remove the comment.

Then compile:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Report any compile errors with file:line and state whether they originate in
Chapter 5 prose or unrelated template/bibliography wiring.

### Final response

Respond in Chinese. Include:

- which worker wrote which section,
- files changed,
- current Chapter 5 quality score,
- score breakdown and number of improvement rounds completed,
- remaining improvement opportunities after the final review,
- figures/tables/citations/experiments still missing,
- whether supplementary experiments are advised,
- if supplementary experiments are advised, the exact experiment/output needed
  and which claim it would strengthen,
- verification command results,
- which chapter to draft next.

Do not commit.
