# Week 14 - HLL MHD Precision Pilot (Brio-Wu 1D)

Harness pilot for Report 2 MHD floating-point precision study. HLL solver, CPU
only. `summary.json` is authoritative; `summary.csv` is a flattened
convenience view.

## Commands

Deterministic P0 build-axis run without MCA sampling:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --skip-mca
```

Deterministic P0 run with 8 requested MCA samples:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --samples 8
```

MCA blocks may be `completed` or `blocked_environment`; a clean environment
block is valid and non-failing for G0.

## Outputs

- `summary.json`: authoritative structured payload with deterministic rows,
  MCA blocks, gates, and claim buckets.
- `summary.csv`: flattened deterministic build-axis table for quick inspection.
- `summary.md`: human-readable gate, row, MCA, ordering-flag, and claim-bucket
  summary.
- `matrix.json`: reproducible Brio-Wu matrix manifest for the selected phase.
- `figures/deterministic_norms.png`: deterministic non-reference norms by
  build variant.
- `figures/mca_noise_floor.png`: MCA spread and SNR summary when completed MCA
  evidence is available.

## Claim Buckets

- `morphology`: report only after G0 passes and deterministic rows are finite.
- `self_reference`: claims are anchored to `cpu-double-O2-ieee-leq`.
- `precision_noise`: provisional until MCA depth is evaluated.

## Transient Grids And Builds

Run directories keep metadata, stdout, stderr, and generated cfgs. Raw
`runs/*/grid.bin` files are transient, ignored, and deleted by the pilot unless
`--keep-grids` is passed; rerun the commands above to regenerate grids when
needed. Build directories, including `build-matrix/`, are not committed and can
be recreated by the harness.
