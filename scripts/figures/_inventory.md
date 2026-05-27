# PNG -> generating script map (report1 Ch5/Ch6 figures)

Inventory built in P2.1. The 14 stems below are those included via
`\includegraphics{Figs/report1/<stem>.png}` in Chapter 5 or Chapter 6.
Stems present in `Figs/report1/` but not included in either chapter are
listed under "unreferenced PNGs" and are out of scope for P2.

## Chapter 5

- `sod_comparison` -> <no script found in repo> (PNG checked in at commit f5d18f7)
- `toro3_comparison` -> <no script found in repo> (PNG checked in at f5d18f7)
- `toro5_comparison` -> <no script found in repo> (PNG checked in at f5d18f7)
- `lw3_n400_double_rho_schlieren` -> <no script found in repo> (PNG checked in at f5d18f7)
- `lw12_n400_double_rho_schlieren` -> <no script found in repo> (PNG checked in at f5d18f7)
- `float_double_over_reference_bar` -> `scripts/figures/report1_d2_replots.py` (plot_fmd_bar)
- `lw12_n400_fp32_minus_fp64_rho` -> `experiments/week9/lw_precision_heatmaps/make_heatmaps.py`
- `density_hllc_vs_rusanov_200` -> <no script found in repo> (PNG checked in at f5d18f7)
- `drift_timeseries_l1_selected` -> <no script found in repo> (PNG checked in at f5d18f7)

## Chapter 6 (Direction-2 / MCA group)

All five are produced by `scripts/figures/report1_d2_replots.py`:

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

For the 7 Ch5 stems without a script, we'll generate a one-page PDF wrapper
from the existing PNG (PIL-based, since `magick` is not installed on this
Windows box). That PDF carries the bitmap unchanged but lets graphicx pick
the PDF in preference to the PNG once `\DeclareGraphicsExtensions` lists
`.pdf` first.

## Data-dependency notes

- `make_heatmaps.py` also defines an `lw3` case whose `grid.bin` paths do
  not exist in this workspace. That case will fail at runtime; the `lw12`
  case (the one Ch5 actually uses) succeeds.
- `report1_d2_replots.py` reads MCA samples from
  `experiments/week7/2d_vfc_precision_sweep/p{8,16,32}/{hllc,rusanov}/sample_*/grid.bin`,
  the Pareto CSV at `experiments/week7/pareto_full/pareto_lw3_full.csv`, the
  2D float-regression summary at `experiments/week4/float_regression/2d/summary.json`,
  and the reference NPZ at `experiments/week4/metrics/u_ref_200_blockavg.npz`.
  All present.
- The script writes to `experiments/week7/report1_d2_replots/` by default; we
  invoke it with `--out-dir report1/phd-thesis-template-2.4/Figs/report1` so
  the regenerated artefacts land directly in the thesis tree.
