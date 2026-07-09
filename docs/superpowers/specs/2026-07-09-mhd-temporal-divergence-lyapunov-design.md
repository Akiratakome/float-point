# MHD Temporal Divergence + Lyapunov Exponent — Design

**Date:** 2026-07-09
**Requirement:** [overall.md](../../requirement/overall.md) §Week 16 C — "Temporal Divergence + Lyapunov Exponent Fitting" (core, 40% Computational Results). `temporal_divergence.py`: output at many time steps, compute ‖u_A − u_B‖ per primary axis, fit `log(error) = λt + c` to extract a Lyapunov-like exponent.
**Context:** CPU-only, autonomous — runs while the GPU sub-project's CUDA install proceeds. Uses the Week-15 report-grade cases (Brio-Wu 1D, Orszag-Tang 2D) already validated.

---

## 1. Goal & scope

Quantify how fast a floating-point precision difference (fp32 vs fp64) grows in
time, and extract a Lyapunov-like growth rate λ per case. The headline contrast:
**chaotic 2D (Orszag-Tang) should show exponential growth (λ > 0) until
saturation; the non-chaotic 1D shock tube (Brio-Wu) should not** — evidence that
precision differences amplify chaotically in turbulent MHD.

### In scope
- Primary axis pair: **fp32 vs fp64** (`cpu-float-O2-ieee-leq` vs `cpu-double-O2-ieee-leq` build-matrix binaries).
- Cases: **Orszag-Tang 2D** (128², chaotic — headline) and **Brio-Wu 1D** (native, non-chaotic control). HLL solver.
- Emit per-case λ (from L1 and Linf of ρ), the drift time-series, a `log(drift)`-vs-`t` figure with the fitted λ line, and a λ table.

### Out of scope
- GPU / hardware-axis temporal divergence (later, once GPU lands).
- Kelvin-Helmholtz (optional follow-up; KH matrix not yet done).
- Other axis pairs (fastmath-vs-ieee, etc.) — fp32-vs-fp64 first.
- Changing solver numerics or the MHD driver (**no C++ change** — see §2).

---

## 2. Approach: multiple-run time-slicing (no C++ change)

`hrsc_mhd` writes only a final-time grid (no `output_times` checkpoint support,
unlike the Euler `hrsc`). Rather than add checkpointing to the MHD driver, run
each (case, precision) to a **series of t_end values** `t_1 < … < t_N` (one run
per slice), producing one grid per slice — the Week-14 `time_sliced_drift`
pattern, now on the chaotic 2D case and with a λ fit. Cheap at 128² OT (~seconds
per run; ~25 slices × 2 precisions ≈ minutes).

**Pairing tolerance:** fp32 and fp64 runs to the same target `t_end` land at
slightly different header times (different per-precision dt sequences, overshoot
< dt) and store dx/dy in their own precision. So the pair entries use **loose
tolerances** — `time_tolerance ≈ 2e-3` (a few dt) and `spatial_tolerance ≈ 1e-5`
(fp32 dx rounding) — otherwise `compute_l1_linf_pair`'s strict 1e-12 checks
would reject the pair. The fit x-value is the mean header time (≈ target t_end).

---

## 3. Reuse (metric layer already exists)

`scripts/metrics/drift_timeseries.py` already provides the entire Lyapunov layer:
- `compute_l1_linf_pair(a, b, variable, gamma, time_tolerance, spatial_tolerance)` — |ρ_A − ρ_B| L1/Linf at one time.
- `fit_exponential_growth(times, errors, fit_window)` — `np.polyfit(t, log(e), 1)` → `{"lambda": slope, …}`.
- `analyse_pair(entry, …)` — pairs a/b series, sorts by time, returns `lambda_l1`, `lambda_linf`, the `times`/`l1`/`linf` series, and per-sample rows.

The new code is only the **driver**: generate per-slice cfgs, run the two
precision binaries, assemble `analyse_pair` entries with loose tolerances, fit,
and plot. `analyse_pair` is already unit-tested; the driver's pure parts (slice
plan, pair-entry assembly) get new unit tests, and the evidence run is
command-level.

---

## 4. Components

- **`scripts/regression/mhd_temporal_divergence.py`** (new): case configs (OT 128² t∈[~0.05,1.0] ×~25; Brio-Wu 1D native t∈[~0.01,0.1] ×~15); per-slice cfg generation (override `nx/ny/t_end/riemann/output_file`); run via the fp32/fp64 build-matrix binaries; iterative grid handling (delete after norms unless `--keep-grids`); assemble `analyse_pair` entries (loose tolerances); emit `summary.{json,md}` with per-case `lambda_l1`/`lambda_linf` + series.
- **Figure** `figures/temporal_divergence.png`: `log10(L1 drift of ρ)` vs `t` per case, with the fitted λ line and λ annotated; OT (growth) vs Brio-Wu (flat/linear) contrast. Academic-paper style (matches `week15_report_figures.py`).
- **Findings note** appended to the Week-15 supervisor material.

Evidence dir: `experiments/week15/mhd_temporal_divergence/` (gitignored; `git add -f` summaries/figure, never `.bin`).

---

## 5. Gates & success criteria

- **Sanity:** OT fp32-vs-fp64 drift grows with time and yields a **positive λ** over the growth window (before saturation); Brio-Wu 1D shows a much smaller / non-exponential λ. All drift values finite.
- **Deliverable:** `summary.json` with per-case λ (L1 + Linf); the log-drift-vs-t figure with fit; a λ table; committed evidence. Reuses validated cases (build-matrix binaries) and the tested drift_timeseries metric layer.
- Interpretation boundary: λ is a **Lyapunov-*like*** growth rate of a precision perturbation (engineering measure), not a formal maximal Lyapunov exponent from tangent-space integration; stated as such.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| fp32/fp64 header time/dx mismatch rejects pairs | loose `time_tolerance`/`spatial_tolerance` in pair entries (§2). |
| Drift saturates early → λ fit contaminated by the plateau | fit on a `fit_window` restricted to the growth phase (analyse_pair supports `fit_window`); pick it from the series. |
| 128² too coarse to show clean exponential growth | 128² OT is chaotic enough for a first λ; note grid-sensitivity; 256² is a follow-up if needed. |
| Disk from many transient grids | iterative delete after norms (`--keep-grids` escape hatch), per overall.md batch rule. |
