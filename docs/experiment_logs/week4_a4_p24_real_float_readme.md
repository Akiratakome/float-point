# Week 4 A4 p24 Real-Float Reading Guide

This log explains how to read the Athena p24-real-float outputs after they were
moved into the canonical Week-4 experiment locations.

## Files

| Path | Meaning |
|---|---|
| `experiments/week4/metrics/a4_float_p24/snr_scalars.csv` | p24-real-float FP noise scalars |
| `experiments/week4/metrics/a4_float_p24/losos_scalars.csv` | p24-real-float LoSoS scalars |
| `experiments/week4/metrics/a4_losos_with_float.csv` | p53 + p24 LoSoS rows |
| `experiments/week4/metrics/a4_snr_with_float.csv` | SNR input used by the official four-row table |
| `experiments/week4/figures/a4_float_p24/sigma_fp_heatmap.png` | spatial FP noise map |
| `experiments/week4/figures/a4_float_p24/losos_reliability_heatmap.png` | sample-clustering significant digits |
| `experiments/week4/figures/a4_float_p24/losos_accuracy_heatmap.png` | reference-accuracy significant digits |
| `experiments/week4/figures/a4_float_p24/losos_worst_heatmap.png` | `min(reliability, accuracy)` significant digits |
| `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` | official four-row A4 conclusion table |

## How To Read The Figures

`sigma_fp_heatmap.png`:

- Bright regions have larger random round-off variation across the MCA samples.
- Compare HLLC and Rusanov at the same color scale. Lower `sigma_FP` means
  better reproducibility under the same precision.
- p24-real-float is expected to be much brighter than p53; that is the
  measured precision effect, not a failure.

`losos_reliability_heatmap.png`:

- Measures how tightly the 30 MCA samples cluster.
- Low values identify cells where binary32 round-off strongly affects the
  computed state.

`losos_accuracy_heatmap.png`:

- Measures how close the MCA sample mean is to the 800² block-averaged
  reference.
- Low values usually track shocks and contact structures where truncation error
  dominates.

`losos_worst_heatmap.png`:

- Uses `min(s_reliability, s_accuracy)` per cell.
- This is the conservative "digits actually trustworthy" view.

## How To Read The Headline Table

Columns:

- `mu_trunc_L1`: physical discretisation error against the 800² reference.
- `sigma_FP_L1`: total FP noise over the MCA ensemble.
- `s_worst_q05`: trustworthy digits in the worst 5% of cells.
- `s_req(N)`: digits required to match the grid truncation level.
- `s_worst - s_req`: completion gate margin.

Regimes:

- `round-off-limited`: precision is below the truncation target.
- `marginal`: barely enough precision.
- `well-matched`: precision roughly matches the grid error.
- `over-provisioned`: more FP precision than this grid can use.

For the headline rho row, p24 and p53 share the same `s_worst_q05` because
`s_worst` is accuracy-limited. The precision contrast is instead in
`sigma_FP_L1`, where p24-real-float is many orders of magnitude noisier than
p53.
