# Figure Scripts

This directory contains both reusable plotters and report-specific production
scripts. Keep new Report 2 figures close to the data product that owns them, and
promote only reusable plotting code back into this directory.

## Reusable Or Forward-Looking

| Script | Use |
|---|---|
| `plot_2d.py` | Canonical single-grid 2D plotter. |
| `plot_drift_timeseries.py` | Drift-over-time plots from summary data. |
| `pareto_full_example.py`, `pareto_plot.py` | Pareto-style precision/accuracy plots. |
| `plot_divergence_marker.py` | Larger diagnostic plotter with pytest coverage. |
| `_style.py` | Shared styling helper for current figure scripts. |

## Report 1 / Presentation Provenance

These scripts generate or refresh Report 1, appendix, poster, or talk figures.
They are useful for reproducibility, but they should not be extended as Report 2
analysis entry points. Tracked Report 1 scripts have been moved to
`scripts/provenance/report1/figures/`; the paths below are compatibility
wrappers:

- `report1_d2_replots.py`
- `report1_appendix_figures.py`
- `verificarlo_report1_refresh.py`
- `ch3_hllc_fan.py`
- `ch3_mhd_seven_wave_fan.py`
- `ch4_architecture_workflow.py`
- `compose_lw_comparison.py`
- `plot_drift_l1_native.py`
- `plot_fp32_fp64_all5.py`
- `plot_fp32_fp64_split.py`
- `plot_lw12_self_convergence.py`
- `plot_lw_style.py`
- `replot_verificarlo_for_talk.py`

Some of these may be untracked in a local working tree. Decide whether to keep,
archive, or delete them before starting Report 2 figure work.

## Maintenance Rule

When a figure script hard-codes `report1/`, `experiments/week4/`, or
`experiments/week7/`, treat it as provenance. For new work, pass input and output
paths as CLI arguments and save outputs under the owning experiment directory.
