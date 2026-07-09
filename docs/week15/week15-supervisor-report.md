# Week 15 — MHD Floating-Point Precision Study: Report-Grade Results

**Date:** 2026-07-09  ·  **Scope of this report:** CPU precision study, 1D + 2D MHD, both Riemann solvers.

All numbers below come from committed, gated evidence packets (no hand-tuning).
Figures are in [figures/](figures/); every value is read from the run
`summary.json` files, not recomputed for the plots.

---

## 1. What changed this week

The MHD precision study moved from **smoke-scale** to **report-grade** on the CPU:

| | Before (Week 14) | Now (Week 15) |
|---|---|---|
| Deterministic fan | 8 variants (O2/Ofast × ieee × leq/strict) | **24 variants** (O2/O3/Ofast × ieee/fastmath × leq/strict) |
| MCA depth | n = 8 | **n = 30** (statistically stable) |
| 1D case (Brio-Wu) | smoke only | **full 24-variant + N=30 MCA**, both HLL & HLLD |
| 2D case (Orszag-Tang) | smoke only | **full 24-variant + N=30 MCA**, both HLL & HLLD |

Four primary axes of the systematic study are now covered on CPU: **precision**
(fp32/fp64), **compiler optimisation + fast-math** (O2/O3/Ofast × ieee/fastmath),
**implementation variation** (`<=` vs `<` in the Riemann fan), across **both
solvers** and **both a 1D and a 2D test** — satisfying the "range of tests in
1D and 2D" requirement. Every packet passes its hard **G0 anchor gate** (the
fp64 reference reproduces the physics anchor exactly).

The remaining primary axis — **hardware (CPU vs GPU)** — is not yet covered;
GPU MHD is the next sub-project (§4).

---

## 2. Primary findings

### Finding 1 — Precision is the dominant error axis
[fig1_precision_axis.png](figures/fig1_precision_axis.png)

Across all 24 variants the result splits cleanly into two clusters: **fp64
variants sit at machine-ε (≤ ~1e-14)**, **fp32 variants at ~1e-6 (1D) to ~1e-5
(2D)** — an **8–9 order-of-magnitude gap**. Compiler flags and the `<=`/`<`
implementation choice move results by *far* less than a change of precision. If
only one knob mattered, it is precision.

### Finding 2 — MCA quantifies the *achievable* significant digits (headline)
[fig2_mca_noise_floor.png](figures/fig2_mca_noise_floor.png)

Monte-Carlo Arithmetic (Verificarlo, N=30) measures the intrinsic round-off
noise floor independent of any reference:

| Packet | p53 spread (fp64) | p24 spread (fp32) | fp32 SNR | ⇒ fp32 digits |
|---|---|---|---|---|
| Brio-Wu 1D · HLL | 5.1e-15 | 2.3e-6 | 5.0e6 | ≈ 6–7 |
| Brio-Wu 1D · HLLD | 8.4e-15 | 4.0e-6 | 8.6e5 | ≈ 6 |
| Orszag-Tang 2D · HLL | 2.6e-15 | 9.8e-7 | 1.0e7 | ≈ 7 |
| Orszag-Tang 2D · HLLD | 3.7e-15 | 1.3e-6 | 7.3e6 | ≈ 6–7 |

**fp64 delivers ≈ 15 significant digits; fp32 delivers only ≈ 6–7.** This is the
distinctive Report-2 evidence — "how many digits does the simulation actually
deliver" — and it is now stable at N=30, consistent across both solvers and both
dimensionalities.

### Finding 3 — Compiler / fast-math is a real but secondary axis
[fig3_compiler_axis.png](figures/fig3_compiler_axis.png)

Within fp32, O2/O3/Ofast × ieee/fast-math produce a measurable spread
(~1.5–1.9e-6 on Brio-Wu HLLD), but two orders of magnitude smaller than the
precision gap. The soft **fast-math ordering flags** (Brio-Wu: 4 HLL / 6 HLLD;
Orszag-Tang: 0 HLL / 4 HLLD) record a **non-monotone** effect: fast-math
sometimes yields *lower* L∞ error than strict-IEEE. This is expected of
floating-point reassociation and is flagged, not silently claimed — worth
noting as a genuine finding rather than a bug. HLLD's richer 5-wave fan is more
sensitive to it than HLL.

### Finding 4 — fp32 buys only a modest speed-up
[fig4_walltime.png](figures/fig4_walltime.png)

On CPU, fp32 runs are only **1.06×–1.34×** faster than fp64. Set against the
~9-order precision loss (Finding 2), the accuracy-vs-performance trade-off on
CPU is unfavourable for fp32 — the interesting speed-up question moves to the
GPU, where fp32 throughput advantages are architectural (next sub-project).

### Cross-cutting observation — 2D chaos amplifies fp32 drift
The 2D Orszag-Tang **HLLD** fp32 deterministic drift reaches **~3e-3** at t=0.5,
far above the ~1e-5/1e-6 of the other cases, because the chaotic 2D flow grows
precision differences exponentially in under-resolved current sheets. See the
field morphology and fp32 drift maps:
[fig5_ot_hll_reference_fields.png](figures/fig5_ot_hll_reference_fields.png),
[fig6_ot_hll_fp32_drift.png](figures/fig6_ot_hll_fp32_drift.png). This
foreshadows the **temporal-divergence / Lyapunov-exponent** analysis planned for
Week 16.

---

## 3. Evidence provenance

| Packet | Path | Gate |
|---|---|---|
| Brio-Wu 1D HLL | `experiments/week15/brio_wu_precision_pilot_p1/` | G0 pass, 24 rows, MCA p53/p24 n=30 |
| Brio-Wu 1D HLLD | `experiments/week15/brio_wu_precision_pilot_hlld_p1/` | G0 pass, 24 rows, MCA p53/p24 n=30 |
| Orszag-Tang 2D HLL | `experiments/week15/orszag_tang_precision_smoke/headline256_p1/` + `mca_n30/` | G0 pass, 24 rows, MCA n=30 |
| Orszag-Tang 2D HLLD | `experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/` + `mca_n30/` | G0 pass, 24 rows, MCA n=30 |

Verificarlo MCA ran in Docker (`verificarlo/verificarlo:cmake`) with a new
`--jobs 16` parallel sampler (16 concurrent containers vs the previous
one-at-a-time), cutting sampling wall-time roughly proportionally on the 24-core
workstation. HLL and HLLD reuse the *same* 24 build binaries (the solver is a
runtime cfg key), so the HLLD packets add no build cost.

---

## 4. What's next (deferred, in priority order)

1. **GPU MHD (hardware axis)** — port the HLL solver to CUDA, add the CPU-vs-GPU
   same-precision ULP regression gate, then re-point Brio-Wu 1D + Orszag-Tang 2D
   at the GPU to complete the 4th primary axis. HLLD-on-GPU is a follow-up within
   that sub-project.
2. **Kelvin-Helmholtz 2D** — the second 2D MHD case (currently morphology-only),
   brought to the same 24-variant + N=30 treatment.
3. **Temporal divergence / Lyapunov exponents** (Week 16) — fit `log(error)=λt+c`
   on the chaotic Orszag-Tang / KH flows; the ~3e-3 fp32 drift above is the
   entry point.

## 5. Honest boundaries

- CPU only; **no GPU/hardware-axis data yet**.
- Deterministic fp32 deltas are engineering-consistency measures vs the
  same-solver fp64 reference, **not** point-wise matches to an exact solution
  (Brio-Wu has an analytic reference for morphology only; Orszag-Tang has no
  closed form — it is validated against literature morphology).
- MCA magnitude claims are solid at N=30; Lyapunov/temporal-divergence fitting
  is not yet done (Week 16).
- The `<=`/`<` implementation axis was numerically zero on the fp64 reference
  rows here; its fp32 effect is folded into the compiler-axis spread.
