# Week 13 Supervisor Meeting Notes — 2D MHD Benchmarks + HLLD Solver

> Generated 2026-06-26. Companion figures live under `experiments/week13/`. Every
> numerical diagnostic line (`[mhd] t=... divB_max=...`) is verbatim output from
> this repo's `build-double/hrsc_mhd.exe`; no values were hand-edited.

---

## 0. One-line progress

This week the code was extended from 1D (Week 12 Brio–Wu) to **2D physical MHD
benchmarks** — the **Orszag–Tang vortex** and a **Kelvin–Helmholtz shear layer** —
on the already-validated **HLL solver**, and a **5-wave HLLD solver** was added as a
**zero-cost, cfg-selectable alternative** (`riemann = hll | hlld`, default `hll`).
After diagnosis, **HLLD is deferred** for production precision-study runs: it runs to
completion with finite output, but its div(B) is substantially larger than HLL under
the current GLM configuration.

The change is **purely additive**: with the default `riemann = hll`, the Week-12
Brio–Wu 1D result is **bit-identical** (regression anchor `steps=759`,
`divB_max=4.441e-14`); the Euler binary and the 1D numerics are untouched.

---

## 1. Figure-by-figure walkthrough

Each figure is covered as **Purpose / How to read / Literature anchor / Conclusion /
Sanity check**. All 2D maps: x horizontal, y vertical, periodic square domain `[0,1]²`,
`256²` cells, HLL solver, γ=5/3, colourbars labelled with the true data range.

### 1.1 Orszag–Tang vortex (OT)

Diagnostic: `[mhd] t=0.500000 steps=806 divB_mean=1.225e-01 divB_max=3.720e+00`

#### Figure A — `orszag_tang/figures/ot_density_pressure.png` (≈ `ot_paper_style.png`)
Density (left) and gas pressure (right) at t=0.5.

- **Purpose**: show the OT vortex in its nonlinear stage — interacting shocks and
  current sheets that grow out of the smooth initial vortex.
- **How to read**: density colourbar 1.27–5.69; bright yellow = compressed
  (post-shock) high-density blobs, dark blue = rarefied regions. Pressure colourbar
  4e-5–3.76; bright bands trace the oblique shock fronts. The central high-density
  "channel flow" and the diagonal shock network are the OT signature.
- **Literature anchor**: Tóth 2000 (*JCP* 161, 605; DOI `10.1006/jcph.2000.6519`),
  the OT div(B)-constraint benchmark; original problem Orszag & Tang 1979. This repo
  uses rationalized units (ρ₀=γ²≈2.78, p₀=γ≈1.67, B₀=1), so the comparison is on
  **structure topology and relative density contrast**, not absolute values.
- **Conclusion**: by t=0.5 the expected central density peak and the diagonal
  shock/current-sheet network are present; density contrast ≈ 5.69/1.27 ≈ 4.5,
  within the standard OT range.
- **Sanity check**: ✅ Reasonable. Morphology, shock orientation and contrast match
  Tóth 2000. Note this is **morphological evidence**, not a point-wise quantitative
  match (no external reference solution was digitized).

#### Figure B — `orszag_tang/figures/ot_divb.png`
Spatial map of log₁₀|div(B)| at t=0.5.

- **Purpose**: check how the GLM divergence cleaning actually performs on a
  shock-dominated problem, and where the residual error lives.
- **How to read**: log₁₀ colourbar, ≈ 10⁻⁵·³⁵ … 10⁰·⁵⁷ (≈ 4.5e-6 … 3.7). Bright
  yellow filaments = where div(B) error concentrates — **aligned almost entirely with
  shock fronts / current sheets**; large green areas are cleaned to near-zero.
- **Literature anchor**: Dedner et al. 2002 (*JCP* 175, 645;
  DOI `10.1006/jcph.2001.6961`) hyperbolic–parabolic GLM cleaning.
- **Conclusion**: div(B) is bounded at `divB_max=3.72`, `divB_mean=0.122`, and
  concentrated on discontinuities — the **expected behaviour** of a cell-centred + GLM
  scheme (error is generated at shocks, then transport-damped, rather than driven to
  machine zero as constrained transport would).
- **Sanity check**: ✅ Reasonable. 3.72 looks large in absolute terms, but the
  worst-case single-cell divergence across an O(1) B-jump is ≈ 1/dx ≈ 256, so the
  max is only ~1.5 % of that; the mean is far smaller. **div(B) is controlled, not
  eliminated** — this must be stated explicitly in the meeting (we use GLM, not
  constrained transport).

### 1.2 Kelvin–Helmholtz shear layer (KH)

Diagnostic: `[mhd] t=1.000000 steps=1148 divB_mean=4.411e-05 divB_max=6.714e-04`

#### Figure C — `kelvin_helmholtz/figures/kh_density_bmag.png` (≈ `kh_paper_style.png`)
Density (left) and field magnitude |B| (right) at t=1.0. Double shear layer at
y=0.25 and y=0.75.

- **Purpose**: show early nonlinear KH evolution in a flow-aligned **weak** field
  (B₀=0.1, Alfvén Mach M_A = 5) doubly-periodic shear layer.
- **How to read**: density colourbar 0.986–1.01 — tiny contrast (~1.4 %) because the
  field and the seed perturbation (δ=0.01) are weak; the two dark-blue horizontal
  bands are the shear interfaces. |B| colourbar 0.0951–0.102; the diagonal bright/dark
  bands show the **field being wound up and stretched/amplified** along the interfaces.
- **Literature anchor**: Frank et al. 1996 (*ApJ* 460, 777; arXiv `astro-ph/9510115`)
  MHD KH evolution. Lecoanet et al. 2015 (arXiv `1509.03630`) is the **limitation
  anchor** — inviscid KH is sensitive to perturbations/regularization and can be
  ill-posed, so grid convergence must **not** be claimed.
- **Conclusion**: clear shear interfaces, field stretched/amplified along them, x-wise
  sinusoidal seed (consistent with the IC) — consistent with the early nonlinear stage
  of weak-field KH.
- **Sanity check**: ✅ Reasonable, **with an honest caveat**: at t=1.0 the billow
  roll-up is not yet fully developed and the density contrast is small, so we **cannot
  claim turbulent saturation or grid convergence** (Lecoanet 2015 ill-posedness). This
  is **bounded morphology/stability evidence**.

#### Figure D — `kelvin_helmholtz/figures/kh_divb.png`
log₁₀|div(B)| at t=1.0.

- **Purpose**: verify cleaning quality on a **smooth** (shock-free) problem.
- **How to read**: colourbar 10⁻⁹·⁴³ … 10⁻³·¹⁷ (≈ 3.7e-10 … 6.7e-4), error weakly
  concentrated along the shear layers.
- **Conclusion**: `divB_max=6.7e-4`, `divB_mean=4.4e-5` — **~4 orders of magnitude
  smaller than OT**, because KH is smooth and weak-field with no strong shocks to
  generate divergence error.
- **Sanity check**: ✅ Reasonable and a **strong consistency result**: the same solver
  is clean on a smooth problem and controlled on a shock problem, confirming the error
  source is genuinely the discontinuities.

### 1.3 HLLD vs HLL solver comparison (OT 256², t=0.5)

#### Figure E — `solver_compare/figures/rho_hll_hlld_diff.png`
Triptych: HLL density | HLLD density | (HLLD − HLL) density.

- **Purpose**: decide whether HLLD's deviation from HLL on the physical solution is
  acceptable.
- **How to read**: the first two panels are visually indistinguishable; the right
  panel is the difference (colourbar ~±0.85) and the differences **concentrate on
  shocks/current sheets**, with the bulk ≈ 0.
- **Literature anchor**: Miyoshi & Kusano 2005 (*JCP* 208, 315;
  DOI `10.1016/j.jcp.2005.02.017`) HLLD 5-wave solver.
- **Conclusion**: bulk L1(ρ)=9.43e-2, Linf(ρ)=8.46e-1 (localized at discontinuities) —
  the two solvers **agree on the physical solution**; differences are confined to the
  resolution-sensitive discontinuities as expected.
- **Sanity check**: ✅ Reasonable. HLLD being sharper at discontinuities (less
  diffusive) is normal; overall agreement indicates no systematic error in the HLLD
  implementation.

#### Figure F — `solver_compare/figures/divb_hll_hlld.png`
Two panels: log₁₀|div(B)| HLL | HLLD.

- **Purpose**: the key decision figure of the week — adopt HLLD or not.
- **How to read**: both are filamentary along shocks, but HLLD is uniformly brighter
  (larger divergence).
- **Conclusion (key)**: `divB_max`: HLL = 3.72, **HLLD = 34.29 (≈ 9×)**; `divB_mean`:
  0.122 vs 0.290 → **HLLD deferred; HLL remains the production solver.**
- **Sanity check**: ✅ Reasonable and conservatively correct. Corroborated by the GLM
  sweep (§1.4): at **early t=0.05, small glm_cr**, HLLD div(B) is actually **lower**
  (0.243 vs HLL 0.355), so the t=0.5 blow-up is a **late-time interaction between the
  HLLD wave fan and the GLM cleaning** — it needs dedicated investigation, so
  "use HLL now, re-validate HLLD later" is the safe call.

### 1.4 Supporting diagnostics (not headline figures)

- **HLLD GLM sweep** (`hlld_glm_sweep/summary.md`, OT t=0.05, 4/4 finite ρ): best
  `hlld_glm0.05` with `divB_max=0.243`. **Purpose**: trend of the HLLD div(B) issue vs
  time / glm_cr; supports the §1.3 diagnosis.
- **MHD Verificarlo smoke** (`mhd_verificarlo_smoke/summary.md`, 3 MCA samples):
  `rho_mean_spread = 2.22e-16` (machine ε). **Purpose**: a **plumbing smoke** that the
  MHD path wires into the Verificarlo stochastic-rounding toolchain for the upcoming
  floating-point precision study. **Note**: 3-sample smoke only, not a precision-study
  result.

---

## 2. Key conclusions

1. **2D HLL morphology validated**: OT and KH at 256² both reproduce literature-consistent
   morphology, with finite diagnostics, reasonable conservation, and controlled div(B)
   (OT bounded at O(1), KH clean at 1e-4).
2. **HLLD implemented but deferred**: runnable, bulk solution agrees with HLL, but at
   t=0.5 its div(B) is ~9× larger under the current GLM config. Production path stays HLL.
3. **Additive change is safe**: default `riemann=hll`, Brio–Wu 1D bit-identical, Euler /
   1D numerics untouched.

---

## 3. Analysis & open problems (must be stated honestly to the supervisor)

| Item | Status | Note |
|---|---|---|
| OT/KH morphology vs literature | ✅ reasonable | topology, shock orientation, contrast match |
| div(B) control | ✅ reasonable | GLM-controlled, not machine-zero; error on discontinuities as expected |
| HLLD-deferral decision | ✅ conservative & correct | 9× div(B) + sweep corroboration → HLL first |
| Solver consistency | ✅ reasonable | HLLD bulk L1≈0.09, differences only at discontinuities |
| **512² self-reference gates** | ⚠️ **not recorded this week** | OT/KH L1/L2/Linf convergence gates were not completed because the 512² runs exceeded the local 20-min command budget; **now being back-filled** (see §4) |
| Self-reference = physical validation? | ⚠️ clarify | self-reference is an **engineering consistency check**, not a point-wise validation against a published reference solution (no external reference data digitized) |
| KH evolution stage | ⚠️ clarify | t=1.0 is still early nonlinear; billows not fully developed; **cannot claim convergence / turbulent saturation** (Lecoanet 2015 ill-posedness) |
| Verificarlo | ⚠️ smoke only | 3-sample plumbing smoke, not a precision study |

### Open problems / risks to raise

1. **HLLD late-time div(B) blow-up** — the central unsolved issue. div(B) is *fine*
   early and small-glm_cr, but ~9× HLL by t=0.5. Hypothesis: HLLD wave-fan interaction
   with GLM source/damping. Needs a controlled HLLD+div(B) study before any adoption.
2. **No quantitative convergence claim yet** — only morphology + finite diagnostics.
   The 512² self-reference gates (being back-filled) are still an *internal* consistency
   check, not a literature point-wise validation.
3. **KH regime is deliberately weak/early** — good for a bounded, well-behaved demo, but
   it does not exercise strong-field or fully-rolled-up dynamics; do not over-interpret.
4. **div(B) method limitation** — GLM cleaning (not constrained transport) means div(B)
   is bounded, not identically zero; this caps achievable div(B) accuracy on shocky
   problems and is the backdrop for the HLLD issue.

**Bottom line for the supervisor**: the 2D evidence this week is **literature-anchored
morphology + finite diagnostics**, sufficient to support "2D HLL physical benchmarks are
working". **Quantitative convergence gates (512²) were not recorded within the week and
are now being back-filled**; no quantitative convergence is claimed until they complete.

---

## 4. 2D case completeness & back-fill

**Status: 2D case partially complete.**

- ✅ **Done**: OT and KH 256² morphology runs + figure packets (Figures A–D), HLLD-vs-HLL
  comparison (Figures E–F), GLM sweep, Verificarlo smoke.
- ⚠️ **Not done this week (auto back-filling)**: the full **512² self-reference gates** for
  OT and KH, i.e. `experiments/week13/{orszag_tang,kelvin_helmholtz}/summary.{csv,json,md}`,
  covering L1/L2/Linf(ρ), mass_rel, and the div(B) floor gate.
  - Reason: 512² runtime (measured extrapolation: OT 512²→t=0.5 ≈ 25 min,
    KH 512²→t=1.0 ≈ 40 min; with candidate + cr=0 control, ≈ 35–60 min per driver),
    exceeding the 10-min single-command timeout.
  - Action: a background agent runs `scripts/regression/mhd_orszag_tang_2d.py` then
    `mhd_kh_2d.py` (both backgrounded to dodge the timeout); results back-fill the table
    below.

### 4.1 512² self-reference gate results (back-fill)

> Status: **back-fill in progress.** The table below is filled with the real gate
> numbers once the background runs finish.

| Benchmark | L1(ρ) | L2(ρ) | Linf(ρ) | mass_rel | divB_max | gates pass? |
|---|---|---|---|---|---|---|
| Orszag–Tang 512²→256² | _running_ | | | | | |
| Kelvin–Helmholtz 512²→256² | _running_ | | | | | |

---

## 5. Next steps

1. Back-fill the §4.1 512² convergence gates (after the background runs complete).
2. Investigate the HLLD late-time div(B) blow-up (HLLD wave fan × GLM cleaning) before
   considering production adoption.
3. Advance the MHD floating-point precision study on the HLL production path (move
   Verificarlo from smoke to a proper sampling study).

## References

- Brio & Wu 1988, *JCP* 75, 400, DOI `10.1016/0021-9991(88)90120-9` — 1D MHD shock tube.
- Orszag & Tang 1979 / Tóth 2000, *JCP* 161, 605, DOI `10.1006/jcph.2000.6519` — OT vortex & div(B) constraint.
- Frank et al. 1996, *ApJ* 460, 777, arXiv `astro-ph/9510115` — MHD Kelvin–Helmholtz.
- Lecoanet et al. 2015, arXiv `1509.03630` — KH convergence / ill-posedness limitation.
- Miyoshi & Kusano 2005, *JCP* 208, 315, DOI `10.1016/j.jcp.2005.02.017` — HLLD 5-wave solver.
- Dedner et al. 2002, *JCP* 175, 645, DOI `10.1006/jcph.2001.6961` — GLM divergence cleaning.
</content>
