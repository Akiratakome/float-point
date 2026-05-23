# Chapter 5 Supervisor-Feedback Execution Prompt

This prompt is for the next writing window. It follows the dispatch and
verification flow of `report1/planning/chapter5_dispatch_prompt.md`, but the
content requirements come from the updated supervisor-feedback map, the current
Chapter 5 text, and the evidence files. Do not use the older Chapter 5 planning
content as the source of truth for this round.

---

## Master prompt

You are the main agent for a supervisor-feedback revision of Report 1 Chapter 5.
Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

This round revises only Chapter 5, "Validation and Precision Results". The
purpose is to apply the updated supervisor comments in:

```text
report1/planning/supervisor_feedback_map.md
```

The original supervisor guide has been copied into:

```text
report1/planning/supervisorguide.md
```

Use it only to verify the map if there is an ambiguity. Treat
`report1/planning/supervisor_feedback_map.md` as the actionable writing plan for
this round.

Older planning material has been archived under:

```text
report1/planning/old/
```

Do not use archived plans as the source of truth for Chapter 5 content.

Do not base the content decisions on the older Chapter 5 plan. Use the older
`chapter5_dispatch_prompt.md` only as a model for workflow: read requirements,
dispatch serial section-scoped workers, preserve evidence boundaries, and verify
the LaTeX result.

### Required reading

Read these files before editing or dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/planning/reportagents.md`
5. `report1/planning/manuscript_outline.md`
6. `report1/planning/supervisor_feedback_map.md`
7. `report1/planning/supervisorguide.md`
8. `experiments/report1_evidence_map.md`
9. `report1/references/reference.md`
10. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
11. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison. It is not part of this Chapter 5 execution plan.

Read these style skills before editing manuscript prose, and read them again
before final prose polishing:

```text
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/academic-english-style/SKILL.md
```

### Main-agent role

- Do not rewrite the whole chapter in one pass.
- Dispatch section-scoped workers serially; never let two workers edit
  `chapter5.tex` at the same time.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned section."
- Workers may edit only their assigned section marker region.
- The main agent integrates results, runs checks, and performs small consistency
  fixes after workers finish.
- Do not modify solver numerics, cfg defaults, experiment output formats, raw
  experiment artifacts, or anything under `experiments/`.
- Manuscript-facing derived figures may be regenerated only under
  `report1/phd-thesis-template-2.4/Figs/report1/` when the supervisor's
  readability requirement cannot be met by LaTeX scaling alone. Use existing
  evidence data or existing plotting scripts where possible, record the command
  or script used in the final response, and do not modify raw artifacts or files
  under `experiments/`.
- The section-marker restriction applies to LaTeX manuscript edits. A worker
  assigned to a figure-readability task may also create or replace the specific
  manuscript-facing figure file under `Figs/report1/` if the global figure rule
  above is satisfied.

### Current section markers

Use the actual current Chapter 5 markers:

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

% <<SECTION_6_BEGIN>>
...
% <<SECTION_6_END>>
```

Do not remove these markers.

### Chapter 5 ownership

Chapter 5 owns results only:

- 1D and 2D Euler validation evidence.
- fp32/fp64 result comparison against reference or discretisation scales.
- matched strict CPU/GPU saved-output comparisons.
- compiler, branch-rule, solver, and finite-time drift sensitivity results.

Chapter 5 must not:

- repeat Chapter 4's design-matrix rationale;
- derive the numerical method from Chapter 3;
- use Verificarlo virtual precision as IEEE fp32 evidence;
- make MHD results claims;
- write Chapter 6-style synthesis;
- generalise beyond tested Euler cases, tested precisions, tested grids, tested
  compiler settings, and named evidence artifacts.

### Hard language and evidence rules

- Every numerical result must trace to `experiments/report1_evidence_map.md` or
  an artifact named in `supervisor_feedback_map.md`.
- Do not use manuscript-facing internal labels:
  `week7`, `week8`, `week9`, `D1`, `D2`, `HLLC-fill`, `config12`,
  `LW12/config12`, `P1`, or `USE_GPU`.
- Use "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)" at first mention, then "LW3" and
  "LW12".
- Verificarlo `p32` is not IEEE fp32. Chapter 5 should not rely on `p32` for
  any direct fp32/fp64 conclusion.
- Avoid labels such as "fp32 L1 error" or "fp64 L1 error" unless the error is
  genuinely against a reference. For pairwise precision comparisons, name both
  states: fp32--fp64 final-state difference.
- Do not use "Lyapunov exponent" or "Lyapunov-like". The time-series fits, if
  retained, are finite-time drift slopes over saved checkpoints.
- Do not cite `wolf_etal_1985` or `eckmann_ruelle_1985` in Chapter 5.
- Compiler flags must not appear as long prose lists. If Chapter 5 needs them,
  refer to Chapter 3/4, or use a compact code-like block/table.
- Every figure/table retained in Chapter 5 must be interpreted in prose.
- All plots must be readable in the compiled PDF without zooming. If LaTeX
  scaling cannot make an existing figure readable, regenerate only a
  manuscript-facing derived figure under `Figs/report1/` from existing evidence
  data, or report the remaining figure-generation dependency.
- AI-assisted prose must satisfy `avoiding-ai-flavor`: no generic filler,
  marketing tone, unsupported confidence, or template-like paragraphs.

### Evidence by worker

Before editing, each worker must read `experiments/report1_evidence_map.md` and
then inspect the evidence artifacts assigned below. If a value in the current
chapter contradicts an artifact, correct the manuscript value and mention the
correction in the worker summary. If an expected artifact is missing, stop and
report the gap rather than inventing a value.

| Worker | Required evidence artifacts |
|---|---|
| A, 1D validation | `experiments/week7/report1_validation_1d/summary.md`; `experiments/week4/float_regression/1d/summary.md` and related CSVs referenced there |
| B, 2D validation | `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/summary.md`; `experiments/week8/report1_2d_config12_fill/config12_reference_metrics.csv` |
| C, fp32/fp64 comparison | `experiments/week4/float_regression/1d/summary.md`; `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/summary.md`; `experiments/week8/report1_2d_config12_fill/config12_reference_metrics.csv` |
| D, CPU/GPU comparison | `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`; `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`; `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`; `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md`; `experiments/week9/cpu_gpu_midtime/summary.md`; `experiments/week9/cpu_gpu_midtime_n400/summary.md` |
| E, variation table and flag boundary | `experiments/week7/report1_variation/summary.md`; `experiments/week8/report1_variation_extend/summary.md`; `experiments/week9/variation_fp32/summary.md`; `experiments/week9/variation_fp32_extend/summary.md`; `experiments/week9/variation_limiter/summary.md` |
| F, drift and non-completion boundary | `experiments/week7/lyapunov_1d_full/summary.md`; `experiments/week7/lyapunov_1d_full/timeout_notes.json`; `experiments/week8/toro2_lt_branch_retry/summary.md`; `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png` |

---

## Worker A: Section 5.2 1D Validation Captions and Metric Clarity

Assigned region:

```latex
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Goal:

- Keep the existing 1D validation argument, but fix supervisor-facing clarity.
- Revise captions for Sod, Toro3, and Toro5 so each states resolution, output
  time, MUSCL-Hancock, HLLC, and exact Riemann reference. Look up resolution
  and output time from the assigned evidence or Chapter 4 context; if output
  time cannot be verified, do not invent it and report the gap in the worker
  summary.
- Revise the 1D table caption so `L_1` is clearly a conservative-state
  fp64--fp32 final-state difference, while `R_\rho^{\mathrm{exact}}` is the
  density reference-scaled ratio.
- Keep author-name citation style where helpful: Sod's shock tube and Toro's
  Riemann tests.

Constraints:

- Do not change numerical values unless you verify a correction from evidence.
- Do not call pairwise fp64--fp32 differences "fp32 error" or "fp64 error".
- Do not add method derivation.

---

## Worker B: Section 5.3 2D Validation Table, Captions, and Figure Size

Assigned region:

```latex
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>
```

Goal:

- Round displayed table values to 3-4 significant figures where precision is
  not needed for the argument.
- Add HLLC, grid, time, and numerical-reference details to LW3/LW12 captions.
- Increase the LaTeX figure widths if the schlieren plots are too small.
- Preserve the boundary that LW12 uses an `800^2` fp64 numerical reference, not
  an exact solution.
- Use "Liska and Wendroff's configurations" style when introducing the
  benchmark source.

Constraints:

- Do not infer convergence order.
- Do not use `config12` anywhere in manuscript-facing text, captions, labels, or
  figure paths.
- Do not create or modify raw experiment artifacts.
- If width changes alone do not make the plots readable, the main agent may
  regenerate manuscript-facing derived figures under `Figs/report1/` from
  existing evidence data, subject to the global figure rule above.

---

## Worker C: Section 5.4 fp32/fp64 Interpretation and Heatmap Readability

Assigned region:

```latex
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Goal:

- Keep this section focused on direct IEEE fp32/fp64 comparisons.
- Add the bounded LW12 interpretation requested by the supervisor: the
  upper-right localisation suggests precision sensitivity where reconstructed
  states feed HLLC wave-speed or flux decisions, but it does not prove a
  specific HLLC branch changed.
- Increase the LW12 heatmap width if needed for readability.
- Keep stationary-contact infinite-ratio wording as a degenerate-reference
  case, not a precision adequacy ratio.

Constraints:

- Do not use Verificarlo `p32` as direct fp32 evidence.
- Do not state that fp32 is generally sufficient.
- Do not add broad floating-point background that belongs in Chapter 2 or 6.
- If width changes alone do not make the heatmap readable, report whether a
  manuscript-facing derived figure should be regenerated under `Figs/report1/`.

---

## Worker D: Section 5.5 CPU/GPU Evidence Compression

Assigned region:

```latex
% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Goal:

- Reduce the low-information all-zero presentation while preserving the result.
- Prefer one compact coverage/zero-drift table plus a short saved-checkpoint
  sentence, or otherwise make the two-table structure clearly non-repetitive.
- Keep the required toolchain footnote:
  Toro3/Toro5 use Windows BuildTools; Sod/LW3/LW12 use Linux/WSL; each
  within-case CPU/GPU comparison uses one matched binary/configuration.
- Preserve the saved-output boundary: checkpoint comparisons do not prove
  equality of all intermediate stage values inside a time step.

Constraints:

- Use "comparisons" or "entries" instead of generic "rows" where possible.
- Use `ENABLE_CUDA` if a build flag must be named; do not write `USE_GPU`.
- Do not generalise to all devices, all compilers, non-strict builds, or MHD.

---

## Worker E: Section 5.6 Variation Evidence Table and Compiler-Flag Boundary

Assigned region:

```latex
% <<SECTION_6_BEGIN>>
...
% <<SECTION_6_END>>
```

Scope for this worker:

- Edit only the first part of Section 5.6: from
  `\subsection*{Compiler, branch-rule, and solver variation}` up to, but not
  including, `\subsection*{Time-resolved drift and Toro2 branch stability}`.
  If the subsection heading has been changed by an earlier edit, stop and ask
  the main agent to identify the new boundary before editing.

Goal:

- Replace the current range-style Table 5.5 with a supervisor-safe
  presentation:
  - either one single-case per-axis table for the case with the clearest or
    largest verified change in the assigned artifacts;
  - or separate 1D and 2D summaries;
  - or a short text statement with actual values if the evidence is not worth a
    full table.
- Do not mix 1D and 2D results into one range table as the main evidence.
- Remove internal wording such as "P1 probe"; use "supplementary GPU flag
  probe" or a plain description.
- Keep compiler flags out of long prose sequences. Refer to Chapter 3/4 flag
  listing if one exists; otherwise keep this section result-facing.
- Keep HLLC-vs-Rusanov framed as deliberate solver variation, not
  reproducibility drift.
- Fix the Figure 5.8 readability issue identified by the supervisor. Enlarge
  the HLLC/Rusanov visual comparison if it remains in the main text. If density
  and pressure show the same qualitative feature, prefer a density-only main
  figure and move the pressure comparison out of the main text, unless the
  pressure panel supports a distinct sentence in the prose.
- Keep limiter variation as status/limitation only; do not claim a limiter
  sensitivity result.

Constraints:

- Do not edit the drift table/figure unless needed to avoid duplicate claims;
  Worker F handles that.
- If Figure 5.8 needs a manuscript-facing derived replacement, write it only
  under `report1/phd-thesis-template-2.4/Figs/report1/` and preserve the raw
  experiment artifacts.
- Do not use `D1`, `D2`, `week7`, `week8`, `week9`, `P1`, or `config12` in
  manuscript-facing text.

---

## Worker F: Section 5.6 Drift, Figure 5.9, and Toro-123/Toro2 Boundary

Assigned region:

```latex
% <<SECTION_6_BEGIN>>
...
% <<SECTION_6_END>>
```

Scope for this worker:

- Edit only the second part of Section 5.6: from
  `\subsection*{Time-resolved drift and Toro2 branch stability}` to
  `% <<SECTION_6_END>>`.
- Before editing, reread Worker E's final Section 5.6 text so the transition
  paragraph does not duplicate or contradict the variation-table discussion.

Goal:

- Remove the main-text drift-slope table unless it supports a claim that the
  figure cannot support. If removed, replace it with a short qualitative
  ordering statement supported by Figure 5.9 or evidence text.
- Enlarge Figure 5.9 to `\textwidth` or otherwise make it more readable.
- If the figure shows fewer visible curves than legend entries because curves
  overlap, say so in the caption or prose.
- Keep drift language finite-time and checkpoint-based.
- For Toro-123/Toro2 non-completion, either verify a `dt`/intermediate-output
  diagnostic from existing artifacts or use limitation wording:
  "non-completion within the 600 s limit was observed; the mechanism was not
  diagnosed in Report 1."

Constraints:

- Do not explain the non-completion mechanism unless evidence exists.
- Default to the limitation wording above unless the assigned artifacts
  explicitly contain `dt` traces or intermediate-output diagnostics. Timing-only
  retry evidence is enough to report non-completion, but not enough to explain
  why it happened.
- Do not cite chaos-theory papers.
- Do not write "Lyapunov exponent" or "Lyapunov-like".

---

## Main-Agent Integration Tasks

After all workers finish:

1. Read the full Chapter 5 once for flow.
2. Remove duplicate prose introduced by adjacent workers.
3. Confirm Section 5.1 still functions as a short overview and does not
   duplicate Chapter 4's design matrix.
4. Confirm Chapter 5 ends with a local result boundary, not a Chapter 6
   synthesis paragraph.
5. Confirm no citation was added without checking:

```text
report1/references/reference.md
report1/phd-thesis-template-2.4/References/references.bib
```

---

## Verification Commands

Run from repository root unless otherwise stated.

### Forbidden/internal language

```powershell
rg -n "week7|week8|week9|D1|D2|HLLC-fill|config12|LW12/config12|P1|USE_GPU|fp32 L1 error|fp64 L1 error|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: no manuscript-facing hits. A hit inside a quoted checklist or comment
still needs manual review.

### Pairwise metric wording

```powershell
rg -n "fp32 error|fp64 error|p32|Verificarlo|rows" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: no misleading fp32/fp64 error wording; any `p32`/Verificarlo mention
must distinguish virtual precision from IEEE fp32; "rows" should be limited to
specific table context.

### Figures

```powershell
rg -n "\\includegraphics" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

For each referenced figure, confirm the file exists under:

```text
report1/phd-thesis-template-2.4/
```

If a figure is unreadable after LaTeX scaling, regenerate only a
manuscript-facing derived figure under `Figs/report1/` from existing evidence
data or existing plotting scripts, then rerun the figure-path check. If
regeneration is not possible without modifying raw artifacts or files under
`experiments/`, record the remaining dependency in the final response.

### Citations

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Confirm each cited key exists in:

```text
report1/phd-thesis-template-2.4/References/references.bib
```

### LaTeX compile

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

Fix only Chapter 5 problems unless the failure is clearly a pre-existing
unrelated issue.

---

## Final Response Format

Respond in Chinese with:

- which Chapter 5 sections were changed;
- which supervisor issues were fixed;
- which evidence boundaries were enforced;
- any remaining dependency on Chapter 3/4/6 or figure regeneration;
- any figure-generation commands or scripts used for derived manuscript-facing
  figures;
- verification and compile results.

Do not claim the full report is finished.
