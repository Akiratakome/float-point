# Week 12 Summary - MHD Solver Foundation (1D skeleton + 2D machinery)

Week 12 delivered an additive ideal-MHD path for Report 2 — a validated 1D solver
(Part 1) and the 2D machinery with GLM divergence cleaning (Part 2) — while keeping
the existing Euler executable and cfg defaults unchanged.

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

## Part 2 — 2D Machinery + GLM Divergence Cleaning

Delivered (Tasks 11–19): `mhd_swap_xy`/`mhd_swap_xy_prim` rotation (`mhd_flux.hpp`),
`glm_damp` (`src/mhd/glm.hpp`), a state-based `(i,j)`-general solver refactor, the
2D constructor, the rotate-and-reuse `y_sweep`, a 2D CFL that includes the
y-direction fast speed (guarded by `ny>1` so 1D stays bit-identical), periodic +
ψ=0-ghost boundary conditions, the `divb_blob` case, and the validation driver
`scripts/regression/mhd_2d_week12.py`.

**Approach (canonical Dedner):** the 1D hyperbolic ψ–B flux coupling is left
untouched; multi-D cleaning emerges from the summed x/y sweeps plus an analytic
parabolic damping `ψ ← ψ·exp(−Δt·c_h²/c_p²)` (cfg knob `glm_cr`, default 0.18).
Full-grid `div(B)` is the diagnostic. (Documented deviation from overall.md's
literal "separate div(B) source step", which would double-count the flux coupling.)

**Validation:**

- *2D Brio-Wu (800×4, periodic-y):* exactly transverse-invariant (rows identical
  to machine zero); row-0 matches the 1D run to mean Δρ = 3.5e-4. Confirms the
  y-sweep does not corrupt the validated x-physics.
- *div(B)-cleaning (128², doubly periodic Gaussian Bx bump):* `max|∇·B|` at t=0.5
  drops from 3.03 (control `glm_cr=0`) to 0.27 (`glm_cr=0.18`) — a ~11× reduction;
  cleaning is non-monotone in `glm_cr` (0.18 beats 0.36). Figures:
  `experiments/week12/mhd_2d/figures/divb_cleaning_{decay,heatmap}.png`.

**1D regression gate held throughout:** Brio-Wu stays bit-identical
(`steps=759`, `divB_max=4.441e-14`). Full MHD suite: 32 cases / 13942 assertions.

Supervisor update: `docs/emails/week12_progress_to_philip_2026-06-18.md`.

## Not Attempted (carried to Week 13)

- HLLD 5-wave solver (HLL is the current scheme).
- Physical 2D benchmarks: Orszag-Tang, Kelvin-Helmholtz.
- Reflective MHD boundary condition.
- GPU MHD.
- Full run-matrix (systematic precision/hardware/compiler) integration.
- 2nd-order Strang splitting (currently Lie).
