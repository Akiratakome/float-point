# PNG -> generating script map (report1 Ch5/Ch6 figures)

Inventory built in P2.1 and refreshed in the P2 follow-up. The 14 stems below
are those included via `\includegraphics{Figs/report1/<stem>.png}` in Chapter 5
or Chapter 6. Stems present in `Figs/report1/` but not included in either
chapter are listed under "unreferenced PNGs" and are out of scope for P2.

State legend:
- **vector**: PDF is a true matplotlib vector PDF written via `_style.save_pair`.
- **PIL wrapper**: PDF is a one-page wrapper around the legacy bitmap PNG
  (kept when no in-repo script reproduces the original plot semantics).

## Chapter 5

- `sod_comparison` -> `analysis/plot_1d.py` (**vector**, regenerated in P2
  follow-up; uses `experiments/report1_fp32_fp64_time_drift/runs/sod-cpu-double/grid.bin`,
  N=200, t=0.25)
- `toro3_comparison` -> `analysis/plot_1d.py` (**vector**, regenerated in P2
  follow-up; uses
  `experiments/add_experiment/toolchain_toro35/runs/toro3-double-cpu/toro3_double_cpu.bin`,
  N=200, t=0.012)
- `toro5_comparison` -> `analysis/plot_1d.py` (**vector**, regenerated in P2
  follow-up; uses
  `experiments/add_experiment/toolchain_toro35/runs/toro5-double-cpu/toro5_double_cpu.bin`,
  N=200, t=0.035)
- `lw3_n400_double_rho_schlieren` -> `scripts/figures/plot_2d.py --field schlieren`
  (**vector**, regenerated in P2 follow-up; uses
  `experiments/week9/cpu_gpu_midtime_n400/runs/lw3-n400-t4-cpu-double-strict-hllc/grid.bin`,
  N=400, t=0.3, fp64)
- `lw12_n400_double_rho_schlieren` -> `scripts/figures/plot_2d.py --field schlieren`
  (**vector**, regenerated in P2 follow-up; uses
  `experiments/week9/cpu_gpu_midtime_n400/runs/lw12-n400-t4-cpu-double-strict-hllc/grid.bin`,
  N=400, t=0.25, fp64)
- `float_double_over_reference_bar` -> `scripts/figures/report1_d2_replots.py`
  (plot_fmd_bar) (**vector**)
- `lw12_n400_fp32_minus_fp64_rho` -> `experiments/week9/lw_precision_heatmaps/make_heatmaps.py`
  (**vector**)
- `density_hllc_vs_rusanov_200` -> *no exact-matching script in repo* (**PIL
  wrapper**, kept). The candidate `scripts/verificarlo/verificarlo_analysis_2d.py`
  produces a 2x2 heatmap (mean + significant-digits) labelled
  `heatmap_density_hllc_vs_rusanov.png`, whereas the Ch5 PNG is a simple 1x2
  side-by-side HLLC/Rusanov density heatmap with a single shared colour bar.
  Different plot semantics; PIL wrapper kept to avoid changing what readers see.
- `drift_timeseries_l1_selected` -> *no exact-matching script in repo* (**PIL
  wrapper**, kept). The candidate `scripts/figures/plot_drift_timeseries.py`
  produces a single-panel L1-drift line plot of all `pairs` mixed together
  (output stems `drift_timeseries_l1.png` and `drift_timeseries_l1_normalized.png`),
  whereas the Ch5 PNG is a 2-panel (Density / Pressure) view over the Toro test
  family with a "Case" legend and an "O2 strict-IEEE vs Ofast+fast-math drift"
  suptitle — i.e. a "selected" subset/aggregation. PIL wrapper kept.

## Chapter 6 (Direction-2 / MCA group)

All five are produced by `scripts/figures/report1_d2_replots.py` (**vector**):

- `sigma_fp_vs_precision` -> `report1_d2_replots.py` (plot_sigma)
- `losos_quantiles_rho` -> `report1_d2_replots.py` (plot_losos_quantiles)
- `region_losos_margin_rho_p32` -> `report1_d2_replots.py` (plot_region_losos)
- `noise_to_error_ratio_heatmap_grid_rho` -> `report1_d2_replots.py` (plot_noise_ratio_heatmap_grid)
- `region_noise_to_error_ratio_precision_grid_rho` -> `report1_d2_replots.py` (plot_region_noise_ratio_precision_grid)

## Unreferenced PNGs in Figs/report1/ (out of scope for P2)

- `pressure_hllc_vs_rusanov_200` — companion to density_hllc_vs_rusanov_200, not included
- `drift_timeseries_l1` — superseded by `_selected` variant in Ch5
- `drift_timeseries_l1_normalized` — superseded by `_selected` variant in Ch5
- `vfc_sod_overlay` — 1D VFC overlay, not included in current Ch5

## Fallback strategy

For Ch5 stems where no in-repo script reproduces the original plot semantics,
the P2 fallback (and what is still in use for `density_hllc_vs_rusanov_200` and
`drift_timeseries_l1_selected`) is a one-page PDF wrapper generated from the
existing PNG via PIL. That PDF carries the bitmap unchanged but lets graphicx
pick the PDF in preference to the PNG once `\DeclareGraphicsExtensions` lists
`.pdf` first.

## Data-dependency notes

- The N=200 fp64 grids used for `sod_comparison`, `toro3_comparison`, and
  `toro5_comparison` are NOT in `experiments/week4/float_regression/1d/` (those
  are N=800). The reproducible N=200 inputs live under
  `experiments/report1_fp32_fp64_time_drift/` and
  `experiments/add_experiment/toolchain_toro35/` and were used by the P2
  follow-up regeneration. Initial-condition primitives for the exact Riemann
  solver are baked into the `--rhoL/uL/pL/rhoR/uR/pR` flags of `plot_1d.py`.
- `analysis/plot_1d.py` originally imported `scripts.verify_toro` and
  `analysis.compare.read_binary`. The P2 follow-up inlined `read_binary` and
  switched to the correct `scripts/regression/verify_toro` location, and added
  a `--save-pair <outdir>/<stem>` flag that routes saves through
  `scripts/figures/_style.save_pair`.
- `scripts/figures/plot_2d.py` gained a `--save-pair <outdir>` flag and now
  applies `_style.apply()` on import; the default cmap is `SEQUENTIAL_CMAP`
  (viridis), unchanged from the legacy default but now sourced from `_style`.
- `make_heatmaps.py` also defines an `lw3` case whose `grid.bin` paths do
  not exist in this workspace. That case will fail at runtime; the `lw12`
  case (the one Ch5 actually uses) succeeds.
- `report1_d2_replots.py` reads MCA samples from
  `experiments/week7/2d_vfc_precision_sweep/p{8,16,32}/{hllc,rusanov}/sample_*/grid.bin`,
  the Pareto CSV at `experiments/week7/pareto_full/pareto_lw3_full.csv`, the
  2D float-regression summary at `experiments/week4/float_regression/2d/summary.json`,
  and the reference NPZ at `experiments/week4/metrics/u_ref_200_blockavg.npz`.
  All present.
- `report1_d2_replots.py` writes to `experiments/week7/report1_d2_replots/` by
  default; we invoke it with `--out-dir report1/phd-thesis-template-2.4/Figs/report1`
  so the regenerated artefacts land directly in the thesis tree.
