# Week 14 - HLL MHD Precision Pilot (Brio-Wu 1D)

Harness pilot for Report 2 MHD floating-point precision study. HLL solver, CPU
only. `summary.json` is authoritative; `summary.csv` is a flattened
convenience view.

## Commands

Formal P0 evidence run with Docker Verificarlo MCA:

```powershell
docker build -f scripts/verificarlo/Dockerfile.cmake -t floatpoint-verificarlo-cmake:week14 scripts/verificarlo
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --samples 8 --mca-image floatpoint-verificarlo-cmake:week14
```

Supervisor-facing literature validation packet:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_literature_validation.py --binary .\build-matrix\cpu-double-O2-ieee-leq\hrsc_mhd.exe
```

`--skip-mca` remains a diagnostic harness escape hatch for blocked local
environments, but it is not the Week-14 supervisor evidence path. The committed
P0 evidence requires completed Docker Verificarlo MCA blocks.

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
- `literature_validation/supervisor_validation.md`: short supervisor-facing
  literature comparison and claim-boundary note.
- `literature_validation/brio_wu_reference_profile.png`: reference HLL
  Brio-Wu primitive-field profile (`rho`, `vx`, `By`, `p`) for visual benchmark
  comparison.

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

## Phase scaling (no new code)

- **P1 (deterministic breadth, 24 variants):**
  use `mhd_precision_pilot.py --phase p1` only with a working Docker
  Verificarlo path or with an explicitly folded completed MCA summary. Review
  `gates.G1.ordering_flags` (fastmath/ieee inversions) before making any
  ordering claim.
- **P2 (MCA depth):** run the sampler once --
  `mhd_precision_sampling.py --samples 30 --image floatpoint-verificarlo-cmake:week14`
  (writes `mca/summary.json`) -- then fold it without re-sampling:
  `mhd_precision_pilot.py --phase p0 --mca-summary experiments/week14/mhd_precision_pilot/mca/summary.json`.
  `blocked_environment` is still representable by the schema, but it is not a
  completed supervisor evidence packet.
