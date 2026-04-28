# Week 4 A3 — 2D Verificarlo production report (raw-data summary)

Date: 2026-04-23  
Case: Liska-Wendroff Config 3 (`nx=200`, `ny=200`, `t_end=0.3`)  
Solvers: HLLC, Rusanov  
Pipeline: per-sample `grid.bin` + per-sample `seed_NN.csv`, then `scripts/verificarlo_analysis_2d.py`

## 1) Sample completeness

Observed under `experiments/week4/2d_vfc_cluster/`:

| solver | sample dirs (`sample_01..30`) | `grid.bin` count | `seed_*.csv` count |
|---|---:|---:|---:|
| hllc | 30 | 30 | 30 |
| rusanov | 30 | 30 | 30 |

Both solvers satisfy `N=30` with contiguous IDs (01..30).

## 2) Analysis outputs

Generated (and regenerated) successfully by:
```bash
python scripts/verificarlo_analysis_2d.py \
    --root experiments/week4/2d_vfc_cluster \
    --expected-n 30 \
    --out-dir experiments/week4/figures/a3
```

Produced figures:
- `experiments/week4/figures/a3/heatmap_density_hllc_vs_rusanov.png`
- `experiments/week4/figures/a3/heatmap_pressure_hllc_vs_rusanov.png`
- `experiments/week4/figures/a3/slice_y0.5_comparison.png`

## 3) Robustness fix applied for A4 handoff

The analyzer now fails fast if actual sample stacks are not exactly `expected_n`
(instead of silently averaging fewer runs). It also cross-checks seed-row count
against stacked sample count per solver.

This closes a hidden risk for A4 metrics: partial sample sets can no longer
enter SNR/LoSoS analysis unnoticed.

## 4) Runtime-accounting note

This run path is currently on Cambridge LSC lovelace (single-node parallel),
not a SLURM cluster. `experiments/week4/2d_vfc_cluster/sacct_report.txt` is
kept as a compatibility path and explicitly marked N/A for `sacct`.
