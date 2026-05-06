# Week 4 A4 p24 Real-Float Athena Execution Summary

**Execution date:** 2026-04-29  
**Status:** complete  
**Case:** Liska-Wendroff Config 3, `200 x 200`, `t_end = 0.3`  
**Precision:** native binary32 with Verificarlo MCA p24  
**Backend:** `libinterflop_mca.so --mode=mca --precision-binary32=24`

## Execution Timeline

| Time | Action | Status |
|---|---|---|
| 17:22 | Athena SLURM jobs completed | 60/60 samples |
| 17:30 | SNR metric computation | `snr_scalars.csv` generated |
| 17:31 | LoSoS metric computation | `losos_scalars.csv` generated |
| 17:32 | p53 + p24 LoSoS merge | `a4_losos_with_float.csv` generated |
| 17:33 | A4 headline table | regenerated in `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` |

## Athena Jobs

| Job | Solver | Samples | Result |
|---|---|---:|---|
| 10085 | HLLC | 30 | success |
| 10086 | Rusanov | 30 | success |

All 60 `grid.bin` samples were present during analysis. Seed independence was
checked per solver before SNR/LoSoS computation.

## Canonical Outputs

| Path | Purpose |
|---|---|
| `experiments/week4/metrics/a4_float_p24/snr_scalars.csv` | p24-real-float SNR and `sigma_FP` rows |
| `experiments/week4/metrics/a4_float_p24/losos_scalars.csv` | p24-real-float LoSoS rows |
| `experiments/week4/metrics/a4_losos_with_float.csv` | merged p53 + p24 LoSoS rows |
| `experiments/week4/metrics/a4_snr_with_float.csv` | headline SNR input with p53 rho bridge + p24 rows |
| `experiments/week4/figures/a4_float_p24/*.png` | p24-real-float heatmaps |
| `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` | official four-row A4 headline table |

## Headline Result

Both p24-real-float rows remain `round-off-limited` by the dynamic
`s_req(N=200)` criterion:

| Solver | s_worst_q05 | s_req | margin |
|---|---:|---:|---:|
| HLLC | 1.54 | 3.13 | -1.59 |
| Rusanov | 1.23 | 2.95 | -1.72 |

For the headline rho row, `s_worst_q05` is accuracy-limited rather than
reliability-limited. The p24-vs-p53 difference is therefore clearest in
`sigma_FP_L1`: HLLC increases from `5.216e-11` to `2.956e-02`, and Rusanov
from `2.278e-11` to `8.199e-03`.

## Reproducibility

Regenerate the official table from the canonical CSVs:

```bash
python scripts/figures/tradeoff_summary_table.py \
  --snr-csv experiments/week4/metrics/a4_snr_with_float.csv \
  --losos-csv experiments/week4/metrics/a4_losos_with_float.csv \
  --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
  --N 200 \
  --out docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md
```
