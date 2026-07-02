# Week 14 Supplemental MHD Evidence

- Git commit: `5ccf559ca4effb7f88bb2f8adc0f1a7c7bcf3f05`
- Report 2 requirement mapping:
  - resolution ladder: grid-convergence context for Brio-Wu MHD precision comparisons.
  - time-sliced drift: temporal growth of deterministic fp32/fp64 and build-flag drift.
  - thread reproducibility: OpenMP reproducibility check against the one-thread reference.
- Docker Verificarlo MCA remains formal evidence from the Week14 summary; these deterministic supplemental runs do not replace it.

## Suite Outputs
- resolution ladder: `resolution_ladder/summary.json`, `resolution_ladder/figure.png` (8 rows)
- time sliced drift: `time_sliced_drift/summary.json`, `time_sliced_drift/figure.png` (20 rows)
- thread repro: `thread_repro/summary.json`, `thread_repro/figure.png` (4 rows)

## Headline Checks
- resolution ladder: finite 8/8; max |divB| 8.882e-14; max Linf(By) 3.690e-01; max thread Linf(rho) 0.000e+00
- time sliced drift: finite 20/20; max |divB| 2.384e-05; max Linf(By) 1.510e-06; max thread Linf(rho) 0.000e+00
- thread repro: finite 4/4; max |divB| 4.441e-14; max Linf(By) 0.000e+00; max thread Linf(rho) 0.000e+00

## How To Read The Figures
- `resolution_ladder/figure.png`: x-axis is grid resolution; y-axis is density L1 error against the nx=1600 fp64 reference projected to the same grid. A downward trend indicates the measured precision effect is not just a coarse-grid artifact.
- `time_sliced_drift/figure.png`: x-axis is t_end; y-axis is By Linf drift against the fp64 O2 reference at the same time. Growth with time shows how deterministic precision/build choices separate as the shock tube evolves.
- `thread_repro/figure.png`: x-axis is OMP_NUM_THREADS; y-axis is rho Linf drift against the one-thread fp64 O2 reference. Near-zero values support CPU-thread reproducibility for this Week-14 pilot case.

## Interpretation Boundary
- These plots are supplemental deterministic evidence for Report 2 discussion: they explain grid sensitivity, temporal drift, and CPU threading effects on the Brio-Wu HLL pilot.
- They do not broaden the Week-14 claim to 2D, GPU, HLLD, or Lyapunov behavior.
- Stochastic precision evidence remains the Docker Verificarlo MCA packet recorded by the Week-14 main summary.
- Binary grids are transient: each grid is measured, summarized, and then deleted unless an explicit keep-grids run is requested.
