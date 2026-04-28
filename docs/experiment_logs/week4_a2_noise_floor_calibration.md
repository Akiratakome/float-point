# Week 4 A2 — Noise-floor calibration note (`k_grad`)

Date: 2026-04-23  
Scope: A2-S2 data currently available in `experiments/week4/noise_floor/`:
- `sod` (hllc, rusanov)
- `stationary_contact` (hllc, rusanov)
- `toro4` (hllc, rusanov)

`toro2` is still excluded in this dataset because the MCA run is unstable/slow under the current toolchain (see `docs/week4/a2_s2_delivery.md`).

## Method

For each `(test, solver, variable)` pair (`variable ∈ {rho, p}`):

1. Load `noise_floor.npz` (`rho_std`, `p_std`).
2. Load `sample_01.txt` and compute `|∇u|` on the same 1D grid.
3. Fit `noise_floor ≈ k_grad * |∇u|` through the origin in cells where
   both terms are non-zero (`|∇u| > 1e-12`, `noise_floor > 0`).

This is a diagnostic fit only (raw-data log), not a final Report-1 claim.

## Results (selected)

| test | solver | var | max std | median std | `k_fit` | corr |
|---|---|---:|---:|---:|---:|---:|
| sod | hllc | rho | 2.95e-15 | 4.12e-16 | 4.87e-14 | 0.381 |
| sod | hllc | p | 4.53e-15 | 2.56e-16 | 4.09e-14 | 0.741 |
| sod | rusanov | rho | 2.58e-15 | 2.96e-16 | 3.81e-14 | 0.698 |
| sod | rusanov | p | 3.85e-15 | 1.94e-16 | 3.57e-14 | 0.811 |
| toro4 | hllc | rho | 2.08e-15 | 2.41e-16 | 4.83e-15 | 0.894 |
| toro4 | hllc | p | 4.79e-15 | 1.17e-15 | 6.29e-15 | 0.596 |
| toro4 | rusanov | rho | 2.09e-15 | 1.67e-16 | 5.41e-15 | 0.899 |
| toro4 | rusanov | p | 5.09e-15 | 9.20e-16 | 6.62e-15 | 0.712 |

Global pooled fit (all valid points): `k_global ≈ 7.05e-15`.

## Decision for A4 handoff

The fitted slope is many orders smaller than the current plotting `k_grad=1.0`
because this raw fit is performed directly on physical field gradients while
the detector also includes an absolute floor and mode-specific envelopes.
The current dataset does **not** support replacing `k_grad=1.0` with a single
stable universal fitted value.

Therefore, for the Week-4 → A4 handoff:
- keep detector default `k_grad=1.0` for continuity;
- treat this file as calibration evidence and caveat;
- revisit with expanded test coverage (add the missing 4th test lane) before
  final Report-1 metric locking.
