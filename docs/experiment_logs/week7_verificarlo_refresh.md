# Week 7 Verificarlo Refresh

Purpose: consolidate Verificarlo-derived Report 1 figures after the 1600^2 reference refresh.

## Included Figures

| figure | source | report use |
|---|---|---|
| `precision_sweep_losos_rho.png` | p8/p16/p32 LoSoS plus Pareto p24/p53 rows | Delivered digits vs virtual precision |
| `precision_sweep_sigma_fp_rho.png` | SNR/LoSoS metric CSVs | Emitted FP noise vs virtual precision |
| `hllc_rusanov_accuracy_noise_tradeoff.png` | normalized `summary.csv` | Rusanov noise reduction vs truncation penalty |
| `pareto_precision_adequacy_twopanel.png` | `experiments/week7/pareto_full/pareto_lw3_full_twopanel.png` | Preferred Report 1 Pareto figure |
| `hllc_rusanov_points_*.png` | Week 3 HLLC/Rusanov text outputs | Point-style comparison figures, without overwriting historical plots |

## Supervisor Requests

| request | status | evidence |
|---|---|---|
| Philip metric | satisfied for regenerated regression summaries | `experiments/week4/float_regression/*/summary.md` when present; refreshed scripts keep the reference-aware interpretation |
| 1600^2 reference | satisfied for `s_req` and 2D regression; Week 4 p53 heatmap rerun depends on MCA sample recovery | `experiments/week4/metrics/s_req_lw_config3_200.csv` |
| Rusanov cleaner explanation | satisfied as interpretation, not recommendation | `experiments/week7/rusanov_noise/summary.csv`; `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_accuracy_noise_tradeoff.png` |
| Pareto figure | satisfied; use the two-panel figure in the report | `experiments/week7/verificarlo_report1_refresh/figures/pareto_precision_adequacy_twopanel.png` |
| drift growth rate | not satisfied; correctly reported `n/a` | `experiments/week7/drift/summary.md` |

## Source Heatmap Policy

The refresh bundle copies Week 7 p8/p16/p32 heatmaps from existing sample-backed outputs. These rows are exploratory and must be captioned with sample counts. The older Week 4 LoSoS accuracy heatmap is not promoted as a final 1600^2 figure unless the original Week 4 MCA grids are recovered or rerun.

For velocity LoSoS heatmaps, capped `s_accuracy=16` means display saturation caused by exact or near-exact agreement in quiet or zero-velocity regions, not proof of 16 true digits.

## GPU Mixed-Precision Design Status

The current CUDA Euler path is validation evidence, not a mixed-precision implementation. Week 3 Verificarlo evidence indicates that the Riemann solver branch structure is not the dominant FP bottleneck; the safer design implication is to keep mixed-precision experiments focused on reconstruction, Hancock predictor, and EOS pressure paths first, while preserving the current strict CPU/GPU validation kernels as the baseline.

No GPU kernel precision changes are made by this refresh. Any later mixed-precision CUDA implementation requires a separate experiment plan and CPU/GPU regression gate.
