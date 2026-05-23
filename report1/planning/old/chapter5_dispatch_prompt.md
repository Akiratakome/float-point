# Chapter 5 Update Dispatch Prompt

This is the Codex-ready master-agent prompt for revising Chapter 5 of Report 1
after the updated chapter responsibilities and supplementary evidence plan. It
is a revision prompt, not a first-draft prompt: `Chapter5/chapter5.tex` already
contains prose, tables, figures, and worker markers.

The chapter is written from the position of a Cambridge MPhil student in
Scientific Computing. Every result claim must be bounded by the evidence map.

---

## Master prompt (paste below this line)

You are the main agent for the Report 1 Chapter 5 update round. Repository:

    c:\Users\tangy\Desktop\floatpoint

This round revises only Chapter 5, "Validation and Precision Results", to match
the updated planning documents, the current Chapter 5 content, and the revised
chapter ownership:

- Chapter 4 owns implementation, experimental design, validation matrix,
  reference strategy, metric definitions, and comparability rationale.
- Chapter 5 owns validation and precision results only.
- Chapter 6 owns synthesis, interpretation across axes, and broader limitations.

Target file:

    report1/phd-thesis-template-2.4/Chapter5/chapter5.tex

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

### Main-agent role

- Do not redraft the whole chapter yourself. Prepare the update scope, dispatch
  serial workers, verify edits, enforce evidence/style/LaTeX consistency, and
  add only BibTeX entries actually cited in the final chapter.
- Each worker edits only its assigned marker region.
- Workers run serially. Never spawn two workers against `chapter5.tex` at the
  same time.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned marker region."
- If the existing marker skeleton is present, keep it. Do not delete existing
  results simply because the old prompt was a drafting prompt. Revise the
  content to match the current plan.

### Chapter 5 ownership lock

Chapter 5 should answer four result questions:

1. Do the selected Euler cases validate the implementation against analytic,
   exact-Riemann, or higher-resolution numerical references?
2. How large are fp32/fp64 differences compared with the selected validation or
   reference scale?
3. What do matched strict CPU/GPU runs show for the tested cases and saved
   checkpoints?
4. Which compiler, branch-rule, solver, and time-resolved variation axes show
   sensitivity, and where are the limits of that evidence?

Chapter 5 should not:

- repeat Chapter 4's design-matrix rationale;
- repeat Chapter 3's numerical-method derivation;
- synthesize "what this means for the whole project" beyond short local
  implications;
- make Report 2 or MHD claims;
- use Verificarlo virtual precision as evidence for IEEE fp32 behaviour;
- add broad statements about hardware or precision beyond the tested cases.

Target compression: keep Chapter 5 close to the updated outline budget
(about 1,950 counted words). Tables and captions are excluded by the current
course clarification, but long table notes and algorithm-like text can still
inflate the manuscript. Prefer precise result sentences over explanatory filler.

### Hard rules

- Do not modify solver numerics, cfg defaults, experiment outputs, output
  formats, or raw artifacts. Do not move files under `experiments/`.
- Do not write MHD as a completed Report 1 result.
- Manuscript-facing prose, captions, labels, and figure paths must not contain:
  `week7`, `week8`, `week9`, `D1`, `D2`, `HLLC-fill`, `config12`,
  `LW12/config12`, or `USE_GPU`.
- Manuscript prose uses "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)" at first mention, and "LW3"/"LW12"
  afterwards.
- Verificarlo `p32` is virtual precision, never IEEE fp32. Chapter 5 only gives
  a one-sentence pointer to the Chapter 6 Verificarlo discussion if needed.
- Avoid misleading metric labels such as "fp32 L1 error" or "fp64 L1 error"
  when the value is a comparison between two states. Name both compared states.
- `experiments/week7/report1_validation_1d/summary.md` pair L1 values are
  fp64-fp32 final-state differences, not separate fp32 or fp64 exact errors.
- 1D exact/reference-scaled numerical values must come from
  `experiments/week4/float_regression/1d/summary.md` or its CSVs.
- LW12 reference is an N=800 numerical reference, not an exact solution.
- CPU/GPU identity is bounded to matched CPU/GPU strict-HLLC runs, the tested
  cases, the tested precisions, and saved conservative-state outputs. The
  checkpoint summaries support saved-output checkpoint identity only; they do
  not prove stage-by-stage identity inside a time step.
- The CPU/GPU toolchain split must be named in the Section 5.5 table footnote:
  Toro3/Toro5 use Windows BuildTools; Sod/LW3/LW12 use Linux/WSL; each
  within-case CPU/GPU comparison uses one matched binary pair.
- Compiler/branch/solver variation rows from the older matrix are CPU double
  unless explicitly tagged otherwise.
- The completed fp32 compiler variation rows must be tagged as fp32 compiler
  sensitivity, not mixed into the CPU-double matrix.
- Limiter variation is a limitation/status item only. Do not claim a limiter
  sensitivity result.
- Do not use "Lyapunov exponent" or "Lyapunov-like" in Chapter 5 prose,
  captions, or labels. The drift-growth fits are finite-time slopes over saved
  checkpoints. Use them only as case-ordering or sensitivity evidence.
- Do not cite `wolf_etal_1985` or `eckmann_ruelle_1985` in Chapter 5 unless a
  human reviewer explicitly asks for a chaos-theory framing. The current Chapter
  5 update should remove that framing.
- AI-assisted prose must pass `avoiding-ai-flavor`: no generic filler, no
  marketing tone, no unsupported confidence, and no paragraph that could fit an
  unrelated report.

### Current Chapter 5 update targets

The current `chapter5.tex` already contains all six result sections. The update
round should keep the useful result material and fix these known risks:

1. Section 5.1 currently contains a full validation-matrix table. The updated
   outline makes Chapter 4 the single design-matrix owner. Compress Section 5.1
   into a result overview and cite Chapter 4's matrix instead of repeating
   selection rationale. If Chapter 4 does not yet contain the matrix, keep only
   a minimal interim coverage table and mark it as temporary in the dispatch
   notes, not in manuscript prose.
2. Section 5.5 already includes final-time and checkpoint CPU/GPU rows. Revise
   wording so checkpoint identity is saved-output evidence, not proof of
   internal time-step identity.
3. Section 5.6 currently risks over-interpreting time-resolved drift with
   "Lyapunov-like" language. Replace this with finite-time drift-slope language
   and remove chaos-theory citations from Chapter 5.
4. Section 5.6 should end with a local result boundary, not a Chapter 6-style
   synthesis paragraph.
5. Any figure/table retained in Chapter 5 must be interpreted in prose with at
   least one number or concrete visual feature.

### Verified artifact coverage

Use this evidence table together with `experiments/report1_evidence_map.md`.
If a needed row is absent or contradicts the prompt, stop and report the gap.

| Evidence role | Artifact |
|---|---|
| 1D fp64-fp32 final-state comparison | `experiments/week7/report1_validation_1d/summary.md` |
| 1D exact/reference-scaled regression values | `experiments/week4/float_regression/1d/summary.md` and CSVs |
| Toro3/Toro5 CPU/GPU strict-HLLC comparison | `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md` |
| LW3 validation and fp32/fp64 comparison | `experiments/week4/float_regression/2d/summary.md`; `experiments/week7/report1_validation_2d/summary.md` |
| LW12 validation against N=800 reference | `experiments/week8/report1_2d_config12_fill/summary.md`; `experiments/week8/report1_2d_config12_fill/config12_reference_metrics.csv` |
| Sod and LW3 strict-HLLC CPU/GPU coverage | `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` |
| LW3 fp64 CPU/GPU strict-HLLC coverage | `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` |
| LW12 CPU/GPU strict-HLLC coverage | `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` |
| Saved-checkpoint CPU/GPU coverage | `experiments/week9/cpu_gpu_midtime/summary.md`; `experiments/week9/cpu_gpu_midtime_n400/summary.md` |
| CPU-double compiler/branch/solver variation | `experiments/week7/report1_variation/summary.md`; `experiments/week8/report1_variation_extend/summary.md` |
| fp32 compiler-flag variation | `experiments/week9/variation_fp32/summary.md`; `experiments/week9/variation_fp32_extend/summary.md` |
| Limiter variation status | `experiments/week9/variation_limiter/summary.md` |
| Time-resolved drift slopes | `experiments/week7/lyapunov_1d_full/summary.md`; `experiments/week7/lyapunov_1d_full/timeout_notes.json`; `experiments/week8/toro2_lt_branch_retry/summary.md` |
| Drift-timeseries figure | `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png` |

Figures currently expected under
`report1/phd-thesis-template-2.4/Figs/report1/`:

- `sod_density_exact_hllc.png`
- `toro3_density_exact_hllc.png`
- `toro5_density_exact_hllc.png`
- `lw3_n400_double_schlieren.png`
- `lw12_n400_double_schlieren.png`
- `float_double_over_reference_bar.png`
- `lw12_n400_fp32_minus_fp64_rho.png`
- `drift_timeseries_l1_normalized.png`
- `density_hllc_vs_rusanov_200.png`
- `pressure_hllc_vs_rusanov_200.png`

If a figure is missing, do not invent it or change raw experiments. Either use
an existing verified figure or leave a precise TODO in the dispatch notes.

### Citation policy for Chapter 5

Chapter 5 should be citation-light because it is a results chapter. Use
citations only where they support a specific sentence.

Allowed Chapter 5 citation keys, subject to `reference.md` and actual `.bib`
availability:

- `sod_1978` for Sod's shock-tube problem.
- `toro2009` for Toro shock-tube tests and exact-Riemann comparison context.
- `liska_wendroff_2003` for 2D Riemann configurations.
- `leveque_2002` only if needed for finite-volume validation or shock-capturing
  interpretation.
- `higham_2002`, `goldberg_1991`, or `ieee754_2019` only if a precision/error
  sentence in Section 5.4 needs it.

Do not add new broad literature citations in Chapter 5. Move synthesis-oriented
citations to Chapters 2, 3, or 6.

### Marker regions

The existing Chapter 5 marker layout is expected to be:

```latex
% === CH5-SEC1-VALIDATION-MATRIX-START ===
...
% === CH5-SEC1-VALIDATION-MATRIX-END ===

% === CH5-SEC2-1D-VALIDATION-START ===
...
% === CH5-SEC2-1D-VALIDATION-END ===

% === CH5-SEC3-2D-VALIDATION-START ===
...
% === CH5-SEC3-2D-VALIDATION-END ===

% === CH5-SEC4-PRECISION-COMPARISON-START ===
...
% === CH5-SEC4-PRECISION-COMPARISON-END ===

% === CH5-SEC5-CPU-GPU-START ===
...
% === CH5-SEC5-CPU-GPU-END ===

% === CH5-SEC6-VARIATION-START ===
...
% === CH5-SEC6-VARIATION-END ===
```

If the marker names differ slightly, inspect the file and adapt. Do not remove
the markers; they are useful for serial revision.

---

## Worker 1: Section 5.1 Validation Overview

Assigned region:

```latex
% === CH5-SEC1-VALIDATION-MATRIX-START ===
...
% === CH5-SEC1-VALIDATION-MATRIX-END ===
```

Update goal:

- Change this from a duplicated design-matrix section into a short validation
  overview.
- State the four evidence questions for Chapter 5.
- Point to Chapter 4 for test-selection rationale, metric definitions, and the
  validation matrix.
- If a coverage table remains, it must be compact and result-facing: cases,
  evidence role, and where the result appears. It must not repeat the full
  design rationale or reference-strategy prose.

Required constraints:

- Keep this section short, about 180-240 counted words if possible.
- Do not hard-code final figure/table numbers.
- Do not use internal labels or local experiment names.
- Do not claim that Chapter 5 itself defines the design matrix if Chapter 4 is
  the owner.

Suggested local output:

- One paragraph introducing the result chapter.
- Optional compact coverage table only if it is clearly useful and not already
  duplicated in Chapter 4.
- One transition sentence into the 1D validation evidence.

---

## Worker 2: Section 5.2 One-Dimensional Euler Validation

Assigned region:

```latex
% === CH5-SEC2-1D-VALIDATION-START ===
...
% === CH5-SEC2-1D-VALIDATION-END ===
```

Update goal:

- Keep the Sod, Toro3, and Toro5 validation results.
- Verify all quoted numbers against the evidence files before editing.
- Preserve the distinction between fp64-fp32 final-state differences and
  exact/reference-scaled validation values.
- Name the supersonic structures required by the brief:
  Toro3 has a right-running supersonic shock; Toro5 has colliding supersonic
  shocks.

Numbers currently present in the draft that must be re-checked:

- Sod fp64-fp32 final-state L1 difference: about `8.743340e-08`.
- Toro3 fp64-fp32 final-state L1 difference: about `6.386967e-05`.
- Toro5 fp64-fp32 final-state L1 difference: about `1.296410e-04`.
- Toro3 density exact/reference ratio: about `1.364064e-05`.
- Toro5 density exact/reference ratio: about `3.913105e-05`.
- Toro3/Toro5 CPU/GPU L1/Linf/ULP drift: zero where the evidence shows zero.

Required constraints:

- Do not say the plots "look good" or "validate" without a number.
- Do not call pair L1 values fp32 error or fp64 error.
- Keep method derivation out of this section.
- Keep citation use specific: Toro/Sod citations only where needed.

---

## Worker 3: Section 5.3 Two-Dimensional Euler Validation

Assigned region:

```latex
% === CH5-SEC3-2D-VALIDATION-START ===
...
% === CH5-SEC3-2D-VALIDATION-END ===
```

Update goal:

- Treat LW3 and LW12 as separate 2D Riemann validation cases.
- Verify all LW3 and LW12 numbers against evidence.
- State that LW12 uses an N=800 numerical reference, not an exact solution.
- Name visible or measured structures without over-claiming physical
  interpretation.

Numbers currently present in the draft that must be re-checked:

- LW3 fp64 density L1 against reference decreases from about `7.89e-3` at
  N=200 to `4.95e-3` at N=400.
- LW3 density SSIM increases from about `0.966` to `0.982`.
- LW3 fp64-fp32 conservative-state L1 at N=400 is about `3.24e-7`.
- LW12 rho L1 against the N=800 reference decreases from about `2.95e-3` to
  `1.33e-3`.
- LW12 rho SSIM increases from about `0.989` to `0.996`.
- LW12 reference-scaled fp32-fp64 density ratio at N=400 is about `1.30e-4`.

Required constraints:

- Do not write `config12` in prose, captions, labels, or figure paths exposed
  to the manuscript.
- Use "Liska-Wendroff configuration 12 (LW12)" at first mention.
- Do not infer convergence order unless a fitted convergence study supports it.

---

## Worker 4: Section 5.4 Single- and Double-Precision Comparison

Assigned region:

```latex
% === CH5-SEC4-PRECISION-COMPARISON-START ===
...
% === CH5-SEC4-PRECISION-COMPARISON-END ===
```

Update goal:

- Keep Section 5.4 focused on direct real fp32/fp64 comparison against
  validation or reference scales.
- Keep Verificarlo virtual-precision regional interpretation out of this
  section except for one pointer sentence to Chapter 6.
- Interpret the bar figure and LW12 fp32-minus-fp64 heatmap if retained.
- State adequacy only within tested cases and resolutions.

Required facts and caveats:

- The 1D `stationary_contact` row has an infinite ratio because the
  double-vs-reference denominator is zero on an exact stationary case. Treat it
  as a degenerate-reference row, not a quantitative adequacy ratio.
- LW3 reference-scaled fp32/fp64 density ratios are approximately `4.47e-5`
  at N=200 and `9.25e-5` at N=400.
- LW12 ratios are approximately `4.63e-5` at N=200 and `1.30e-4` at N=400
  against the N=800 reference.
- A rising ratio with resolution should be stated as a boundary, not a failure
  or a general trend beyond the tested grid sizes.

Required constraints:

- Do not treat Verificarlo `p32` as IEEE fp32.
- Do not say "fp32 is accurate enough" without the tested-case boundary and a
  metric.
- Do not add broad floating-point background that belongs in Chapters 2/6.

---

## Worker 5: Section 5.5 Matched CPU/GPU Comparison

Assigned region:

```latex
% === CH5-SEC5-CPU-GPU-START ===
...
% === CH5-SEC5-CPU-GPU-END ===
```

Update goal:

- Use both final-time CPU/GPU evidence and completed saved-checkpoint evidence.
- Keep the claim bounded to matched strict-HLLC CPU/GPU runs and saved
  conservative-state outputs.
- Ensure the CPU/GPU table has the required toolchain footnote.

Required evidence coverage:

- Final-time strict-HLLC zero drift for Sod, Toro3, Toro5, LW3, and LW12 where
  the evidence files show L1/Linf/ULP zero.
- Saved-checkpoint zero drift for Sod, LW3, and LW12 from:
  `experiments/week9/cpu_gpu_midtime/summary.md`
  and `experiments/week9/cpu_gpu_midtime_n400/summary.md`.

Required boundary sentence:

- The checkpoint rows compare saved outputs at synchronized checkpoints; they
  do not prove equality of all intermediate stage values inside a time step and
  do not extend to non-strict builds, untested cases, other compilers, or MHD.

Required constraints:

- Use `ENABLE_CUDA` if a build flag must be named.
- Do not write `USE_GPU`.
- Do not present the Windows/Linux toolchain split as a weakness in the
  within-case comparison; state it as a boundary on cross-case generalisation.

---

## Worker 6: Section 5.6 Compiler, Branch, Solver, and Drift Sensitivity

Assigned region:

```latex
% === CH5-SEC6-VARIATION-START ===
...
% === CH5-SEC6-VARIATION-END ===
```

Update goal:

- Keep this as a result section for sensitivity axes, not a broad discussion.
- Split the prose internally into:
  1. compiler, branch-rule, solver, and fp32 compiler variation;
  2. time-resolved drift and Toro2 branch-stability boundary.
- End with a local result boundary. Move cross-axis interpretation to Chapter 6.

Required coverage:

- CPU-double compiler/branch/solver variation from:
  `experiments/week7/report1_variation/summary.md`
  and `experiments/week8/report1_variation_extend/summary.md`.
- fp32 compiler variation from:
  `experiments/week9/variation_fp32/summary.md`
  and `experiments/week9/variation_fp32_extend/summary.md`.
- Limiter variation status from:
  `experiments/week9/variation_limiter/summary.md`, as limitation only.
- HLLC-vs-Rusanov is deliberate method variation, not reproducibility drift.
- Toro2 with strict `<` branch did not complete in the available evidence;
  report it as branch-specific stability degradation, not as a zero-drift row.
- Time-resolved drift fits are finite-time slopes from saved checkpoints. They
  are not Lyapunov exponents.

Required corrections to the current draft:

- Remove "Lyapunov-like" wording.
- Remove or relocate `wolf_etal_1985` and `eckmann_ruelle_1985` citations from
  Chapter 5.
- If the GPU strict-vs-fast probe remains, label it as optional/P1 build-control
  evidence and keep the caveat that the current result is affected by diagnostic
  printing / timeout behaviour. Do not let it carry a main hardware conclusion.
- Do not claim limiter sensitivity.

Required constraints:

- Do not use internal labels such as `D1`, `D2`, `week7`, `week8`, or `week9`
  in manuscript prose.
- Do not over-explain the compiler matrix mechanics; Chapter 4 owns design.
- Keep this section result-dense and under control. Prefer one compact table
  plus one drift figure over multiple repetitive paragraphs.

---

## Review and verification rounds

After all worker edits, the main agent must run these checks before finalising
the chapter update:

1. Evidence trace check:
   - Every numerical claim in Chapter 5 has a named artifact in the evidence
     map or in this dispatch prompt.
   - Every retained figure/table is interpreted in prose.
   - All fp32/fp64 claims name the compared states or reference scale.
2. Chapter ownership check:
   - Section 5.1 no longer duplicates the full Chapter 4 design rationale.
   - Chapter 5 does not contain broad Chapter 6 synthesis.
   - Verificarlo virtual-precision interpretation remains in Chapter 6.
3. Forbidden language check:
   - Search manuscript-facing Chapter 5 text for internal labels and banned
     terms:

```powershell
rg -n "week7|week8|week9|D1|D2|HLLC-fill|config12|LW12/config12|USE_GPU|fp32 L1 error|fp64 L1 error|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

4. Figure path check:

```powershell
rg -n "\\includegraphics" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Confirm every referenced figure file exists under
`report1/phd-thesis-template-2.4/Figs/report1/`.

5. Citation check:

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Confirm every citation key exists in `References/references.bib` and is
justified by `report1/references/reference.md`.

6. LaTeX compile check:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If compilation fails, inspect the log and fix only Chapter 5 issues unless the
failure is clearly caused by a pre-existing unrelated file.

### Final response format

Report back in Chinese with:

- which Chapter 5 sections were updated;
- which evidence boundaries were enforced;
- any remaining Chapter 4/6 dependencies that affect Chapter 5 wording;
- compile/check results;
- no claim that the full report is finished unless every relevant check passed.
