# Week 4 C2 — Real Float vs VPREC p24 (Raw Experiment Log)

This note is a **raw experiment log style** record for comparing:

- `real_float`: Verificarlo build with `FLOAT_PRECISION=float`
- `vprec_p24`: Verificarlo build with `FLOAT_PRECISION=double` + `libinterflop_vprec.so --precision-binary64=24`

## 1) Run compare workflow

From repo root (Linux/WSL/Docker Verificarlo environment), for 1D Toro-style tests:

```bash
bash scripts/verificarlo_run.sh --compare-float -n 30 -t "sod stationary_contact"
```

Output root is deterministic and mode-tagged, for example:

```text
experiments/verificarlo/runs_compare_p53_mca/
  real_float/<test>/run_*.txt
  vprec_p24/<test>/run_*.txt
```

## 2) Plot + summary JSON

```bash
python scripts/plot_real_vs_vprec.py \
  experiments/verificarlo/runs_compare_p53_mca/real_float \
  experiments/verificarlo/runs_compare_p53_mca/vprec_p24 \
  --tests sod stationary_contact
```

Default output directory:

```text
docs/week4/figures/real_float_vs_vprec/
```

Generated artifacts:

- `<test>_real_vs_vprec_sigdigits.png` (rho/u/p per-cell overlay)
- `real_vs_vprec_summary.json`

JSON includes per variable:

- `min_sig_digits`
- `median_sig_digits`

for both modes.

Latest comparison summary file:

- `docs/week4/figures/real_float_vs_vprec/real_vs_vprec_summary.json`

## 2b) LW3 comparison path (2D, existing tooling)

LW3 is covered via the dedicated 2D regression workflow (not limited to Sod/Toro 1D):

```bash
bash scripts/float_regression_2d.sh
```

This produces:

- `experiments/week4/float_regression/2d/reference_800.bin`
- `experiments/week4/float_regression/2d/{double,float}_{200,400}.bin`
- `experiments/week4/float_regression/2d/summary.{md,json}` (including phase-error metrics and heatmaps)

Equivalent direct report command (if binaries already exist):

```bash
python scripts/float_regression_report.py --mode 2d --input experiments/week4/float_regression/2d
```

## 3) Interpretation notes

- If profiles and min/median significant digits are close, VPREC p24 is a good proxy for real-float behavior.
- Large systematic gaps indicate potential simulation bias (or setup mismatch) and should be investigated.
- VPREC traces can be deterministic in some environments; when sample variance is exactly zero,
  the plotting script emits a warning and leaves those significant-digit points undefined.
- Script fails fast on missing runs, bad file format, or mismatched cell counts/grids.

## 4) Conclusion logging

Record the run conclusion directly from `real_vs_vprec_summary.json`:

- If real_float and vprec_p24 min/median significant digits remain close across Sod and LW3-related runs, keep VPREC p24 as valid proxy.
- If gaps are systematic, keep both pipelines and report discrepancy in Week 4 summary.
