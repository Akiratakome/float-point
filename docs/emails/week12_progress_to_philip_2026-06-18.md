# Week 12 Progress — Report 2 (Ideal-MHD) Kick-off

**To:** Philip
**From:** beren
**Date:** 2026-06-18
**Phase:** Report 2, Week 12 — MHD solver foundation

---

## Summary

Report 2 work has started and the **MHD solver foundation is complete for Week 12**.
The **1D ideal-MHD solver is validated** against the Brio-Wu shock tube, and the
**2D machinery (Y-sweep + GLM divergence cleaning) is now implemented and
validated** — including a quantitative demonstration that GLM cleaning reduces
`∇·B` by ~11× versus a no-cleaning control. Everything reuses the precision-generic,
hardware-portable framework from Report 1 (templated on `Real`, same binary IO and
harness). This note reports both the 1D and 2D results, with four figures.

Everything here is additive: the Report-1 Euler executable, tests, and results
are untouched, so all Report-1 evidence remains reproducible. The 1D Brio-Wu
result is bit-for-bit unchanged as the 2D code landed (a hard regression gate).

---

## What is done (1D MHD)

A standalone `hrsc_mhd` solver with:

- 9-variable ideal-MHD state `(rho, rho·v_xyz, B_xyz, E, psi)` with a GLM
  (`psi`) field carried from the start for divergence cleaning;
- **HLL** Riemann solver (the safe baseline; HLLD is planned for Week 13) with
  fast-magnetosonic wave-speed estimates;
- **MUSCL-Hancock** 2nd-order reconstruction (minmod), matching the Euler scheme;
- a `compute_divB_norms` diagnostic (mean/max |∇·B|).

It is exercised in both `float` and `double` and leaves the Euler path unchanged.

## Validation — Brio-Wu shock tube (gamma = 2, t = 0.1)

**Figure 1 — solution profiles** (`experiments/week12/brio_wu_1d/figures/brio_wu_profiles.png`):
N=800 (double) against an N=8000 self-converged double reference. All the
characteristic Brio-Wu structure is reproduced in the right places — fast
rarefaction, the compound wave (~x=0.47), contact discontinuity, slow shock
(~x=0.65), and the transverse field `B_y` flipping +1 → −1.

**Figure 2 — self-convergence** (`experiments/week12/brio_wu_1d/figures/brio_wu_convergence.png`):
density L1/L2 error vs N=8000 reference, log-log.

Quantitative results (density error vs the N=8000 reference):

| N | L1 | L2 | L∞ |
|---:|---:|---:|---:|
| 200 | 1.48e-02 | 3.64e-02 | 2.08e-01 |
| 400 | 9.46e-03 | 2.71e-02 | 1.91e-01 |
| 800 | 5.64e-03 | 1.92e-02 | 1.55e-01 |

- **Monotone convergence** in L1 and L2; observed L1 order ≈ **0.70**. This
  sub-first-order rate is expected: HLL is diffusive and the solution is
  dominated by discontinuities (shock + contact + compound wave), which cap the
  attainable L1 order. HLLD (Week 13) should sharpen the contact and improve this.
- **Divergence stays clean**: for N=800, `max|∇·B| ≈ 4.4e-14`,
  `mean|∇·B| ≈ 3.3e-16` — round-off level, as expected in 1D where `B_x` is
  constant by construction.

All runs are saved with full provenance (generated cfg, stdout/stderr,
`metadata.json` with git commit + binary/cfg SHA-256, and `summary.{csv,json,md}`)
under `experiments/week12/brio_wu_1d/`.

---

## 2D MHD machinery + GLM divergence cleaning (done + validated)

The 2D extension follows the canonical Dedner mixed-GLM approach: the y-sweep
reuses the 1D flux/HLL by rotation (mirroring the Euler solver), and an analytic
parabolic damping stage `ψ ← ψ·exp(−Δt·c_h²/c_p²)` is applied each step. The 1D
hyperbolic ψ–B coupling is left untouched, so 1D Brio-Wu stays bit-identical.

**Check 1 — 2D does not corrupt the 1D physics.** Running Brio-Wu on an 800×4
grid (periodic in y) is **exactly transverse-invariant** (every row identical to
machine zero) and its row-0 profile matches the 1D run to a mean density
difference of 3.5e-4 and max density difference of 7.0e-3 under the stricter 2D
CFL. This confirms the y-sweep + rotation are correct.

**Check 2 — GLM cleaning works (key result).** On a doubly-periodic 128² grid
seeded with a Gaussian `B_x` bump (a known nonzero `∇·B`), GLM cleaning drives the
divergence down strongly, while the no-damping control merely advects it:

| time | c_r = 0 (control) | c_r = 0.18 | c_r = 0.36 |
|---:|---:|---:|---:|
| 0.05 | 2.98 | 2.53 | 2.55 |
| 0.10 | 4.44 | 2.44 | 3.31 |
| 0.20 | 2.99 | 1.06 | 1.84 |
| 0.35 | 2.98 | 0.66 | 1.43 |
| 0.50 | 3.03 | **0.27** | 0.84 |

(values are `max|∇·B|`.) The control stays ~3 throughout; `c_r=0.18` reduces it
**~11×** by t=0.5. Interestingly the cleaning is **non-monotone in `c_r`** —
`c_r=0.18` outperforms the stronger `c_r=0.36`, i.e. there is an effective optimal
damping. This `c_r` knob is exposed in the config, so its effect can be folded
into the systematic study later.

**Figure 3 — div(B) decay** (`experiments/week12/mhd_2d/figures/divb_cleaning_decay.png`):
the table above plotted vs time.

**Figure 4 — div(B) field at t=0.5** (`experiments/week12/mhd_2d/figures/divb_cleaning_heatmap.png`):
control vs cleaned on a shared colour scale — the cleaned run's divergence is
visibly washed out (peak 3.07 → 0.27).

## Next (Week 13)

- HLLD 5-wave solver (with HLL fallback retained);
- Orszag-Tang vortex and Kelvin-Helmholtz 2D validation;
- begin the systematic precision/hardware/compiler study on the MHD cases.

## Notes / caveats

- The 2D `divb_blob` is a **synthetic divergence-cleaning test**, not a physical
  benchmark — it isolates the GLM behaviour. The physical 2D benchmarks
  (Orszag-Tang, Kelvin-Helmholtz) come in Week 13.
- The MHD scheme uses **HLL** (diffusive). HLLD (Week 13) should sharpen contacts.
- All validation is currently CPU/double on the local machine; the precision ×
  hardware × compiler sweep is the Week 14+ systematic study.
- MPI remains intentionally out of scope (single-node OpenMP+CUDA), to be
  justified explicitly in Report 2.

---

*Figures regenerated by `scripts/figures/plot_brio_wu_1d.py` (1D) and
`scripts/figures/plot_mhd_2d_week12.py` (2D) from the committed experiment
summaries; binary grids are reproducible via `scripts/regression/mhd_brio_wu_1d.py`
and `scripts/regression/mhd_2d_week12.py`.*
