# Week 12 Summary - 1D MHD Walking Skeleton

Week 12 delivered an additive 1D ideal-MHD path for Report 2 while keeping the existing Euler executable and cfg defaults unchanged.

## Delivered

- MHD core files: `src/mhd/mhd_state.hpp`, `src/mhd/mhd_flux.hpp`, `src/mhd/hll.hpp`, `src/mhd/mhd_reconstruct.hpp`, `src/mhd/mhd_solver.hpp`, `src/mhd/mhd_solver.cpp`.
- Executable and diagnostics: `src/mhd_main.cpp` for `hrsc_mhd`, plus `src/utils/error_norms.hpp` for `compute_divB_norms`.
- Tests and cfgs: `tests/unit/test_mhd_*.cpp`, `tests/unit/test_divb.cpp`, `tests/cases/brio_wu_1d/brio_wu.cfg`, `tests/cases/brio_wu_1d/brio_wu_ref.cfg`.
- Validation/docs: `scripts/regression/mhd_brio_wu_1d.py`, `docs/INDEX.md`, and `docs/week12/week12-summary.md`.

## Brio-Wu Validation

Density errors compare each candidate against a block-averaged aligned N=8000 double reference from `experiments/week12/brio_wu_1d/summary.md`.

| N | reference N | L1(rho) | L2(rho) | Linf(rho) |
|---:|---:|---:|---:|---:|
| 200 | 8000 | 1.480554e-02 | 3.641584e-02 | 2.083493e-01 |
| 400 | 8000 | 9.463267e-03 | 2.713726e-02 | 1.914836e-01 |
| 800 | 8000 | 5.641658e-03 | 1.923045e-02 | 1.546849e-01 |

The real Brio-Wu sentinel run completed with:

```text
[mhd] t=0.100000 steps=759 divB_mean=3.339e-16 divB_max=4.441e-14
```

Generated cfgs, stdout, stderr, metadata, and scalar summaries live under `experiments/week12/brio_wu_1d/`. Binary grids remain ignored/transient and are not committed. N=8000 was run locally for this one Week 12 validation; larger or repeated reference sweeps should move to CSC.

## Indexing Decision

Task 6 fixed the interface convention: interface `i` uses the right face of cell `i-1` and the left face of cell `i`. Ghost access is guarded by outflow boundary conditions before reconstruction. Physical flux fallback is used at the pre-flux domain edges, and `Bx`/`psi` stay 1D-invariant on the no-GLM-source path.

## Not Attempted

- GLM source-step integration.
- 2D MHD cases.
- HLLD.
- GPU MHD.
- Full run-matrix integration.
