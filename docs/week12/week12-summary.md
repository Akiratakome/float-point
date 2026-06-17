# Week 12 Summary - 1D MHD Walking Skeleton

Week 12 delivered an additive 1D ideal-MHD path for Report 2 while keeping the existing Euler executable and cfg defaults unchanged.

## Delivered

- 9-variable MHD conserved state with primitive conversion, pressure, fast-speed helper, source-free GLM-compatible x-flux, and HLL flux.
- Minmod MUSCL reconstruction, 1D MUSCL-Hancock MHD solver, Brio-Wu initial condition, and `hrsc_mhd` cfg-driven executable.
- `compute_divB_norms` diagnostic and unit coverage for MHD state/flux/HLL/reconstruction/solver/divB.
- Brio-Wu production/reference cfgs and a local self-converged double validation harness producing L1/L2/Linf summaries.

## Brio-Wu Validation

Density errors compare each candidate against a block-averaged aligned N=8000 double reference from `experiments/week12/brio_wu_1d/summary.md`.

| N | reference N | L1(rho) | L2(rho) | Linf(rho) |
|---:|---:|---:|---:|---:|
| 200 | 8000 | 1.134358e-02 | 3.131551e-02 | 1.969059e-01 |
| 400 | 8000 | 6.791221e-03 | 2.266974e-02 | 1.931163e-01 |
| 800 | 8000 | 3.848017e-03 | 1.577020e-02 | 1.585979e-01 |

The real Brio-Wu sentinel run completed with:

```text
[mhd] t=0.100000 steps=760 divB_mean=0.000e+00 divB_max=0.000e+00
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
