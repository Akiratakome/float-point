# Phase A3 Execution Summary
**Execution Date**: 2026-04-29  
**Status**: ✅ COMPLETE

## Execution Timeline

| Time | Action | Status |
|------|--------|--------|
| 17:22 | SLURM jobs completed on Athena | ✓ 60/60 samples |
| 17:30 | SNR metric computation (p24-real-float) | ✓ Generated snr_scalars.csv |
| 17:31 | LoSoS metric computation (p24-real-float) | ✓ Generated losos_scalars.csv |
| 17:32 | Merged LoSoS (p53 + p24 combined) | ✓ Created losos_merged_p53_p24.csv |
| 17:33 | Generated A4 headline table | ✓ A4_headline_table_p24.md |

## Inputs

### SLURM Job IDs
- **10085**: HLLC × 30 samples → 30 grid.bin files
- **10086**: Rusanov × 30 samples → 30 grid.bin files
- **Result**: All 60 tasks completed successfully, elapsed ~2.2–2.5 min per sample

### Configuration
- **Solver**: HLLC, Rusanov
- **Case**: LW Config 3 (200×200 grid, 2D advection)
- **Precision**: binary32 (IEEE 754 float via Verificarlo p24 backend)
- **Backend**: `libinterflop_mca.so --mode=mca --precision-binary32=24`
- **Ensemble size**: 30 samples per solver

### Reference Data
- **Reference grid**: 800² block-averaged fine reference (`u_ref_200_blockavg.npz`)
- **Truncation error (s_req)**: From `s_req_lw_config3_200.csv` (reference-anchored)

## Outputs Generated

### CSV Files (8 rows each per solver)

| File | Size | Description |
|------|------|-------------|
| `snr_scalars.csv` | 759 B | 2 solvers × 4 variables: σ_FP_L1, σ_FP_max, sample count |
| `losos_scalars.csv` | 1.8 KB | 2 solvers × 4 variables: s_worst_q05, reliability, accuracy |
| `losos_merged_p53_p24.csv` | 3.4 KB | 16 rows: p53 (8) + p24-real-float (8) merged |

### Markdown Deliverables

| File | Content |
|------|---------|
| `A4_headline_table_p24.md` | **2-row headline table**: HLLC + Rusanov with regime classification |

### Visualizations

| Plot | Description |
|------|-------------|
| `sigma_fp_heatmap.png` | FP noise amplitude spatial map (200×200) |
| `losos_reliability_heatmap.png` | Min significant digits per cell |
| `losos_accuracy_heatmap.png` | Truncation error magnitude map |
| `losos_worst_heatmap.png` | Ceiling on reliable significant digits |

## Key Results

### Regime Classification

**Both solvers: ROUND-OFF-LIMITED**

```
┌────────┬────────────────┬──────────────┬─────────┬──────────┐
│ Solver │   Precision    │ s_worst_q05  │ s_req   │ Margin   │
├────────┼────────────────┼──────────────┼─────────┼──────────┤
│ HLLC   │ p24-real-float │     1.54 sd  │ 3.13 sd │ -1.59 sd │
│        │                │              │         │ (deficit)│
├────────┼────────────────┼──────────────┼─────────┼──────────┤
│ RUSANOV│ p24-real-float │     1.23 sd  │ 2.95 sd │ -1.72 sd │
│        │                │              │         │ (deficit)│
└────────┴────────────────┴──────────────┴─────────┴──────────┘
```

### Interpretation
- **Margin < 0**: FP precision insufficient for truncation error control
- **HLLC -1.59**: Needs 1.59 more significant digits than available
- **RUSANOV -1.72**: Even lower SNR makes situation worse
- **Implication**: binary32 inappropriate for this test case; double (p53) or higher required

## Quality Assurance

### Data Integrity ✓
- All 60 grid.bin files present (validated: `find . -name grid.bin | wc -l` = 60)
- Seed independence verified per solver (60 unique seeds checked)
- File sizes consistent (HLLC: 600 KB/sample, Rusanov: 600 KB/sample)
- Total: 38 MB with no corrupted reads

### Computation Validation ✓
- SNR calculation: ✓ Loaded 30 samples per solver, computed σ_FP_L1 per variable
- LoSoS calculation: ✓ Compared to 800² reference, computed 5th percentile of min(s_reliability, s_accuracy)
- Regime classification: ✓ Applied thresholds from `_tradeoff_thresholds.py`
- CSV merge: ✓ No duplicate rows, proper header preservation

## Integration Notes

### What Changed
- **Code**: NONE (no solver modifications)
- **Architecture**: NONE (pipeline structure unchanged)
- **Added Files**:
  - `experiments/week4/A4_headline_table_p24.md` (headline result)
  - `experiments/week4/metrics/snr_scalars.csv` (p24 metric)
  - `experiments/week4/metrics/losos_scalars.csv` (p24 metric)
  - `experiments/week4/metrics/losos_merged_p53_p24.csv` (unified data)
  - Heatmap PNG files (4 visualizations)

### Backwards Compatibility ✓
- All results placed in `experiments/week4/` (existing analysis directory)
- No modification to build directories or test cases
- Existing p53 data (`losos_lw_config3_200.csv`) untouched
- New p24 rows appended only to merged CSV for cross-precision comparison

## Next Steps for User

1. **Pull from git**: `git pull origin week4-implementation`
2. **Review headline table**: `cat experiments/week4/A4_headline_table_p24.md`
3. **Analyze visualizations**: Open heatmaps in `experiments/week4/metrics/`
4. **Compare precisions**: Use `losos_merged_p53_p24.csv` for side-by-side p53 vs p24 analysis
5. **Update A4 conclusions**: Incorporate round-off-limited finding into final write-up

## Validation Commands (user can run locally after pull)

```bash
# Verify files present
find experiments/week4/metrics -name "*p24*" -o -name "*merged*" | wc -l

# Check headline table
head -5 experiments/week4/A4_headline_table_p24.md

# Verify data consistency
python -c "import pandas as pd; df=pd.read_csv('experiments/week4/metrics/losos_merged_p53_p24.csv'); print(df.groupby('precision').size())"
# Expected output: p24-real-float 8, p53 8 (or similar)

# Regenerate table if needed
python scripts/figures/tradeoff_summary_table.py \
  --snr-csv experiments/week4/metrics/snr_scalars.csv \
  --losos-csv experiments/week4/metrics/losos_merged_p53_p24.csv \
  --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
  --N 200 \
  --out my_test_table.md
```

---

**Prepared by**: Agent  
**For**: User at /home/raid/yt455/floatpoint  
**Git Integration**: Ready for push to week4-implementation branch
