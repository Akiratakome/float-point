# Week 4 Float-vs-Double Regression (Raw Data Log)

## 1D convergence regression

Run:

```bash
bash scripts/float_regression_1d.sh
```

Expected outputs:

- `experiments/week4/float_regression/1d/{sod,toro2,toro3,toro4,toro5,stationary_contact}_{double,float}.csv`
- `experiments/week4/float_regression/1d/summary.md`
- `experiments/week4/float_regression/1d/summary.json`

Latest 1D result table is generated at:

- `experiments/week4/float_regression/1d/summary.md`

## 2D regression (LW Config 3)

Run:

```bash
bash scripts/float_regression_2d.sh
```

Expected outputs:

- `experiments/week4/float_regression/2d/reference_800.bin`
- `experiments/week4/float_regression/2d/{double,float}_{200,400}.bin`
- `experiments/week4/float_regression/2d/summary.md`
- `experiments/week4/float_regression/2d/summary.json`

Latest 2D result table (L1/L2/Linf + SSIM + shock offsets) is generated at:

- `experiments/week4/float_regression/2d/summary.md`

2D phase-error heatmaps (4 per candidate: rho/u/v/p) are generated under:

- `experiments/week4/float_regression/2d/phase_error_heatmaps/`

## Direct metric helper commands

```bash
python scripts/downsample_2d.py \
  --candidate experiments/week4/float_regression/2d/float_200.bin \
  --reference experiments/week4/float_regression/2d/reference_800.bin

python scripts/phase_error_metrics.py \
  --candidate experiments/week4/float_regression/2d/float_200.bin \
  --reference experiments/week4/float_regression/2d/double_200.bin
```

## Rationale: SSIM scalar over axis-aligned W1 (this week)

- This week uses **SSIM single scalar** as a lean 2D similarity supplement to L1/L2/Linf.
- Axis-aligned W1 is kept out of the Week 4 pipeline because its projection assumptions are brittle for non-axis-aligned shock topology in general 2D flows.
- Phase/amplitude topology-level decomposition is deferred.

## Future work note (Report 2)

- Extend from SSIM scalar to factor-level analysis (luminance / contrast / structure).
- Revisit phase-topology metrics for 2D shock structures with robust geometric handling.

