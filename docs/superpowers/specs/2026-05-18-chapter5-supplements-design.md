# Chapter 5 Supplements — Design

Date: 2026-05-18
Owner: Yudong Tang
Repo: `c:\Users\tangy\Desktop\floatpoint`
Target: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

## Goal

Lift Chapter 5 review score from 87/100 toward 95/100 by:

1. Running four supplementary experiments locally (WSL + laptop CUDA) and integrating only the successful ones.
2. Adding a complete Lyapunov-like growth-rate table sourced from existing `experiments/week7/lyapunov_1d_full/` artifacts, with proper citation to literature.
3. Applying P0/P1 edits identified in the review.
4. Producing a compiled PDF.

## Hard rules

- **Silent revert on experiment failure.** If a supplementary experiment fails or its build does not compile, omit any reference to it from the chapter. Do NOT write apologetic or "attempted but" language. Keep the existing chapter text for that area.
- **No hallucinated references.** Every new BibTeX entry MUST include a verifiable DOI, URL, or ISBN. Subagents must verify via WebFetch before writing.
- **Citation whitelist now expanded** with: `leveque_2002`, `higham_2002` (already present, will keep), plus new Lyapunov refs from the verified literature (Wolf 1985, Eckmann–Ruelle 1985).
- **Terminology**: use "finite-time Lyapunov-like growth rate" with literature citation. Do not call it a "Lyapunov exponent" without the "-like" qualifier.
- **Forbidden tokens** (must remain absent): `week7`, `week8`, `week9`, `D1`, `D2`, `config12`, `HLLC-fill`, `USE_GPU`.
- **CPU/GPU zero-drift bounding** must be preserved; do not extend to untested cases/precisions.
- **Do not modify** solver numerics, cfg defaults, raw artifacts under `experiments/`.

## Architecture: 3 phases, 6 subagents

### Phase 1: 4 parallel subagents (no GPU contention)

#### Subagent A — fp32 compiler-flag extension
- **Task**: extend `experiments/week9/variation_fp32/` matrix to add Toro5 (N=200), Sod (N=400), LW3 (N=200) under O2/O3/Ofast+fast-math fp32 CPU builds.
- **Inputs**: existing `variation_fp32/matrix.json` as template; cfg files under `tests/cases/`.
- **Output**: `experiments/week9/variation_fp32_extend/summary.md` (pair table with L1, Linf, ULP_max).
- **Failure mode**: if any build or run fails, abort subagent and report no-extension.

#### Subagent B — LW3/LW12 fp32-fp64 difference heatmaps
- **Task**: post-process existing CPU fp32 and fp64 N=400 grid.bin files for LW3 and LW12; emit per-variable difference heatmaps for ρ.
- **Inputs**: `experiments/week7/report1_validation_2d/runs/lw3-n400-cpu-*/grid.bin`, `experiments/week8/report1_2d_config12_fill/runs/lw12-n400-cpu-*/grid.bin`.
- **Output**: 2 PNG files in `Figs/report1/` named `lw3_n400_fp32_minus_fp64_rho.png`, `lw12_n400_fp32_minus_fp64_rho.png`, plus `experiments/week9/lw_precision_heatmaps/summary.md` documenting min/max diff and L_inf location.
- **Failure mode**: if grid.bin readers don't exist, abort.

#### Subagent C — Lyapunov-like table completion + reference verification
- **Task**: 
  1. Build a complete table (case × variable × axis) from `experiments/week7/lyapunov_1d_full/summary.md`.
  2. Verify and emit BibTeX entries for `wolf_et_al_1985` and `eckmann_ruelle_1985` with DOIs (must WebFetch doi.org to confirm).
- **Output**: `docs/superpowers/specs/lyapunov_table_draft.md` + verified `.bib` snippet returned in subagent report.
- **Failure mode**: if DOI verification fails for a reference, exclude that reference and report.

#### Subagent D — P0/P1 chapter text edits
- **Task**: apply the following edits to `chapter5.tex`:
  1. Fix Toro5ρ omission in Lyapunov ordering ([chapter5.tex:436-438](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L436)).
  2. §5.4: drop or substantiate "Pressure and velocity ratios remain of the same order" line.
  3. §5.1 Table 5.1: mention stationary_contact as control case in caption.
  4. Delete Fig 5.7 (`drift_timeseries_l1.png`) or convert to subfigure of Fig 5.6.
  5. §5.5: clarify "LW3 is split by precision because..." sentence.
  6. §5.6: rephrase "Toro2 branch-rule run is not a zero-drift row".
  7. Table 5.4 footnote: switch from `minipage` to `tablenotes`/standard form if `threeparttable` is loaded by template; otherwise keep but improve formatting.
- **Output**: chapter5.tex patched.
- **Failure mode**: if file structure unexpected, report no-edit.

### Phase 2: 2 sequential subagents (GPU exclusive)

#### Subagent E — CPU/GPU midtime N=400 extension
- **Task**: extend `experiments/week9/cpu_gpu_midtime/` to add LW3-N400 and LW12-N400 at the same 4 checkpoint times (t1–t4), both fp32 and fp64, both CPU and CUDA.
- **Output**: `experiments/week9/cpu_gpu_midtime_n400/summary.md`.
- **Timeout**: 30 min wall. If exceeded, abort and revert.

#### Subagent F — GPU strict-vs-fast comparison
- **Task**: build a CUDA non-strict + fast-math variant; compare against existing strict CUDA on Sod-N200 and LW3-N200 in fp32.
- **Output**: `experiments/week9/gpu_strict_vs_fast/summary.md`.
- **Timeout**: 20 min wall. If build fails, abort and revert; do NOT add chapter text about this experiment.

### Phase 3: main agent integration

1. For each successful Phase 1/2 result, write a small chapter5.tex insertion (new mini-table or expanded existing table). For failures, leave existing text untouched.
2. Update `references.bib` with any new verified entries.
3. Run forbidden-token grep over chapter5.tex.
4. Compile via `pdflatex` × 3 + `bibtex` × 1 in `report1/phd-thesis-template-2.4/`.
5. If compilation fails, fix LaTeX errors (escape characters, missing packages) and retry up to 3 times.
6. Deliver `thesis.pdf` + a diff summary to user.

## Sub-section integration plan (success cases only)

| Experiment | Where in chapter |
|---|---|
| A: fp32 ext | Replace Table 5.6 ([chapter5.tex:408-422](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L408)) with full case coverage |
| B: heatmaps | New subfigure pair under §5.4 (after Fig 5.5) |
| C: Lyapunov table | New table in §5.6 second subsection; add Wolf/Eckmann–Ruelle cites at slope definition |
| D: P0/P1 edits | In place |
| E: midtime N=400 | Add 2 rows to Table 5.5 ([chapter5.tex:316-323](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L316)) |
| F: GPU strict-vs-fast | New paragraph in §5.6 first subsection or new table row |

## Verification gates

- After each subagent: main agent uses Read/Grep to confirm
  - Output file exists at expected path
  - Numerical values are within plausible physical/numerical bounds
  - No forbidden tokens in any text the subagent wrote
- After Phase 3: `pdflatex` must produce `thesis.pdf` without unresolved `??` citation marks
- Final: forbidden-token grep returns zero matches

## Out of scope

- MHD anything
- Verificarlo virtual-precision (handled in Chapter 6)
- Solver code changes
- New cases beyond what's in current validation matrix
