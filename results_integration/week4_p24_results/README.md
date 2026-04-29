# Week 4 Phase A3 Results Integration
**Date**: 2026-04-29  
**Task**: Verificarlo binary32 (p24-real-float) MCA Analysis for LW Config 3

## Overview

This folder contains the complete results from Phase A3: generating and analyzing 60 MCA samples (HLLC ×30 + Rusanov ×30) using Verificarlo's binary32 precision with p24 MCA backend.

## File Organization

### `results_p24/` - Primary Results

| File | Description |
|------|-------------|
| `A4_headline_table_p24.md` | **A4 Headline Table**: Summary conclusion with regime classification (round-off-limited for both solvers) |
| `snr_scalars_p24.csv` | SNR metrics: FP noise floor (σ_FP_L1, σ_FP_max) per variable |
| `losos_scalars_p24.csv` | LoSoS metrics: significant digit statistics (s_worst_q05, reliability, accuracy) per variable |
| `losos_merged_p53_p24.csv` | **Combined LoSoS data**: p53 (existing) + p24-real-float rows for unified analysis |

### `analysis/` - Visualizations

**Heatmaps:**
- `sigma_fp_heatmap.png` - FP noise spatial distribution across 200×200 grid
- `losos_reliability_heatmap.png` - Cell-wise minimum significant digits (reliability floor)
- `losos_accuracy_heatmap.png` - Truncation error vs FP noise trade-off visualization
- `losos_worst_heatmap.png` - Worst-case significant digits (reliability ∧ accuracy)

## Key Findings

### Regime Classification
```
Solver   | Precision      | s_worst_q05 | s_req | Margin | Regime
---------|----------------|-------------|-------|--------|------------------
HLLC     | p24-real-float |     1.54    | 3.13  |  -1.59 | round-off-limited
RUSANOV  | p24-real-float |     1.23    | 2.95  |  -1.72 | round-off-limited
```

Both solvers exhibit **round-off-limited** behavior: available significant digits (s_worst_q05) fall below required precision (s_req) for satisfactory truncation error control.

### Precision Comparison
- **FP Noise (σ_FP_L1)**: Rusanov lower (8.2e-03) than HLLC (3.0e-02), but insufficient
- **Truncation Error (μ_trunc_L1)**: HLLC smaller (2.77e+02) than Rusanov (4.18e+02), yet both exceed available digits
- **Root Cause**: binary32 (24-bit mantissa) insufficient for 200² LW Config 3 grid

## Data Provenance

**Source Configuration**: LW Config 3 (Liska-Wendroff 2D Advection)
- Grid resolution: 200×200 cells
- Solver: HLLC, Rusanov
- Precision: binary32 (IEEE 754 float)
- Samples: 30 per solver
- Backend: Verificarlo 2.4.0 MCA p24

**References**:
- Reference grid: 800×200² block-averaged (fine-grid reference)
- Metrics computed via:
  - `scripts/metrics/snr_metric.py` (FP noise floor)
  - `scripts/metrics/losos_metric.py` (significant digit distribution)
  - `scripts/metrics/s_req_metric.py` (truncation error requirement)

## Integration Steps (for local pull)

1. **Clone/Pull**: `git pull origin week4-implementation`
2. **Access Results**: Files staged in `experiments/week4/metrics/` and `experiments/week4/A4_headline_table_p24.md`
3. **Use in Analysis**:
   - Headline table ready for A4 conclusions
   - LoSoS merged CSV enables cross-precision (p53 vs p24) comparisons
   - Heatmaps suitable for presentation/documentation

## Script Execution Reference

```bash
# SNR Metric (FP noise)
python scripts/metrics/snr_metric.py \
  --root experiments/week4/2d_vfc_float_p24 \
  --out-dir experiments/week4/metrics \
  --precision-label p24-real-float

# LoSoS Metric (significant digits)
python scripts/metrics/losos_metric.py \
  --root experiments/week4/2d_vfc_float_p24 \
  --reference experiments/week4/metrics/u_ref_200_blockavg.npz \
  --out-dir experiments/week4/metrics \
  --precision-label p24-real-float

# Headline Table
python scripts/figures/tradeoff_summary_table.py \
  --snr-csv experiments/week4/metrics/snr_scalars.csv \
  --losos-csv experiments/week4/metrics/losos_merged_p53_p24.csv \
  --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
  --N 200 \
  --out experiments/week4/A4_headline_table_p24.md
```

## Notes

- No architecture or solver code changes made
- All files integrate seamlessly with existing workflow
- p53 LoSoS data (existing) merged with p24 results for unified analysis
- Regime classification uses thresholds from `scripts/_tradeoff_thresholds.py`
- Full per-variable breakdown retained in source CSVs (8 rows per solver)

---

**Status**: COMPLETE ✅  
**Next Steps**: Prepare final A4 conclusions combining p53 and p24-real-float regimes
