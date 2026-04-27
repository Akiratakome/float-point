# Email draft: Week-4 progress update (2026-04-23)

**To:** Philip Blakely (supervisor)
**From:** Yudong Tang
**Subject:** Week 4 progress — divergence markers, 2D Verificarlo on Liska-Wendroff, and first pass at the "how many significant figures?" question
**Attachments (8):**
- `sod_rho_noise_floor.png`, `stationary_contact_rho_noise_floor.png`, `toro4_rho_noise_floor.png`
  (MCA-calibrated divergence figures; the Stage-1 `visible`-threshold version was sent yesterday)
- `heatmap_density_hllc_vs_rusanov.png`, `slice_y0.5_comparison.png`
  (2D Liska-Wendroff Config 3 production results)
- `snr_local_heatmap.png`
  (per-cell signal-to-noise field for the accuracy-vs-robustness question)
- `lw_config3_200.md` (headline conclusion table — 2 rows, HLLC double + Rusanov double)
- `pareto_lw_config3_200.png` (sigma_FP × s_worst_q05 with s_req(N) band)

---

Dear Philip,

Thank you for yesterday's note confirming Rusanov as the underlying solver
and raising the two open questions on balancing accuracy vs FP-sensitivity
and on the required number of significant figures. This email summarises
what I have done since Monday, answers each of your questions with data
from this week's runs, and flags the limitations I have not yet been able
to resolve.

## 1. What was completed this week

1. **Rusanov promoted to the default solver** across the configuration
   layer (commit `fc581dc`). HLLC still runs whenever a cfg file says
   `solver=hllc`, so every existing comparison is preserved bit-for-bit.

2. **Divergence-marker tool (two-stage delivery).** Stage 1 (visible
   threshold `|a−b| > 10⁻³·max(|a|,|b|)`) was the figure I emailed
   yesterday. Stage 2 replaces the fixed threshold with a statistically
   calibrated **MCA noise floor** — for each (test, solver) I ran 30
   Verificarlo MCA samples at `p=53` (full-double random rounding) and
   computed the per-cell standard deviation across samples. The
   divergence tolerance at cell *i* is then
   `3·max(σ_HLLC(i), σ_Rusanov(i)) + k_grad·|∇avg(i)| + abs_floor`,
   i.e. 3-σ on top of a gradient-absorption term that accounts for the
   fact that a 1-cell shock-position offset between solvers is not a
   genuine disagreement. The tool has three modes (`noise_floor`,
   `strict_fp`, `visible`) and an 8-case pytest suite.

3. **2D Verificarlo on Liska-Wendroff Config 3 (200²).** New IC + cfg
   files, unit test, 2D runner, binary output format (little-endian
   header, numpy-compatible). After a smoke run at 40²×3 samples
   (local WSL+Docker, 23 s wall-clock, σ(ρ) ≈ 10⁻¹⁵ as expected for
   MCA p=53) I moved to production at 200²×30 samples for HLLC and
   Rusanov — **60 runs total, both solvers now complete** on the
   Cambridge LSC `lovelace` node. Seeds are 64-bit `/dev/urandom`
   draws, PRNG thread-isolated (`OMP_NUM_THREADS=1`,
   `OPENBLAS_NUM_THREADS=1`), all 30 seeds per solver verified
   distinct.

4. **Analysis tools for the two open questions** (both field-first,
   i.e. per-cell statistics computed on the sample axis *before*
   any spatial aggregation — the reverse order cancels anti-correlated
   FP noise and underestimates solver sensitivity; a regression test
   guards against that mistake): `scripts/snr_metric.py` for
   signal-to-noise, `scripts/losos_metric.py` for the three-field
   significant-digit measure (see §3 below).

## 2. How to read the attached figures

- **`sod_rho_noise_floor.png` / `stationary_contact_rho_noise_floor.png`
  / `toro4_rho_noise_floor.png`** — HLLC and Rusanov density profiles
  overlaid, with the MCA 3-σ tolerance envelope drawn as a band and a
  red "x" placed at every cell whose |HLLC − Rusanov| difference
  escapes the envelope. Y-axis is ρ; x-axis is position.
  *What these prove:* on all three tests the HLLC/Rusanov difference
  at shocks and contacts stays within the gradient-absorption term
  (see §4 — this is actually a limitation), so no "x" markers appear
  at present; the visible-mode figure from yesterday already shows
  where the solvers differ at the presentation level (10⁻³ relative).

- **`heatmap_density_hllc_vs_rusanov.png`** — side-by-side
  2D density at *t*=0.3 for Config 3 at 200². The four-shock
  interaction pattern is reproduced for both solvers and is visually
  consistent with Liska & Wendroff (2003) Fig. 3. Rusanov noticeably
  smears the shock fronts relative to HLLC.

- **`slice_y0.5_comparison.png`** — 1D slice along *y*=0.5 with both
  solvers overlaid and the divergence-marker tool run on the slice.
  Useful for reading numerical values of the HLLC–Rusanov gap
  cell-by-cell.

- **`snr_local_heatmap.png`** — the per-cell SNR field
  SNR(i) = |mean_s[U_s(i)] − U_ref(i)| / σ_s[U_s(i)], i.e. the ratio
  of systematic (truncation) error to random (MCA FP) error at
  every cell. Bright regions are truncation-dominated; dim regions
  are round-off-dominated. Currently the whole domain is bright:
  for both solvers σ_FP(ρ) is ≈ 10⁻¹¹ (L1) while truncation against
  the high-resolution reference is at the percent level, so we are
  very far from the round-off floor at double precision on 200².

## 3. Answers to your two open questions

### 3.1 "How to balance accuracy vs FP-sensitivity?"

I started by pursuing a linear-combination scalar `S = ‖E_trunc‖ + α·‖σ_FP‖`
and abandoned it: the two terms have mixed physical meaning
(systematic offset vs random noise) and the choice of α is subjective,
so the resulting ranking is not defensible to a reader who prefers a
different α. Instead I am now reporting **two independent, dimensionless
numbers per (solver, precision, grid):**

| Quantity | Definition | What it answers |
|---|---|---|
| `σ_FP_L1`      | spatial L1 of per-cell MCA std across 30 samples | how much round-off noise the solver emits |
| `μ_trunc_L1`   | spatial L1 of (sample mean − reference)         | how far the solver is from the correct answer |

Values from the production run (Liska-Wendroff Config 3, 200², double):

| Solver  | σ_FP_L1 (ρ) | σ_FP_L1 (p) | μ_trunc_L1 (ρ) | μ_trunc_L1 (p) |
|---------|-------------|-------------|----------------|----------------|
| HLLC    | 5.22×10⁻¹¹  | 2.48×10⁻¹¹  | 150.6          | 129.5          |
| Rusanov | 2.28×10⁻¹¹  | 2.11×10⁻¹¹  | 150.6          | 129.5          |

Observations:

- **Rusanov's round-off noise is ~2.3× lower than HLLC on ρ**, ~1.2× on
  pressure. The 1D pattern (HLLC is the more FP-sensitive solver) therefore
  extends to 2D.
- The `μ_trunc_L1` columns are currently identical because the "reference"
  I used is the MCA-sample mean, which is not independent of the solver.
  A proper truncation figure needs a high-resolution **HLLC-double**
  reference at 800² (and a separate Rusanov-800² reference) so each
  solver is compared to an own-scheme converged solution; this is on the
  list for next week.
- **Update (2026-04-26):** the `μ_trunc_L1` column above used a self-referenced sample mean and is **superseded** by the 800²-block-averaged-reference values now in `experiments/week4/metrics/s_req_lw_config3_200.csv`. The reference-anchored μ_trunc_L1 (rho) is **277.3** for HLLC and **418.0** for Rusanov; full breakdown in the headline table at `docs/week4/tradeoff_summary_tables/lw_config3_200.md`.

So the Rusanov-vs-HLLC trade-off as I currently measure it is
**"HLLC is 2× noisier but captures shocks sharper"**, and the
SNR heatmap lets the reader see which region drives each term.

### 3.2 "How many significant figures do we need?"

I think the honest answer is *it depends on the grid*, and the
quantitative version of that answer is

`s_req(N) = −log₁₀(‖E_trunc(N)‖ / ‖U_ref‖) + 1`

i.e. the number of decimal digits at which the solver's truncation
error lives, plus one digit of safety so that round-off sits ~10×
below truncation and does not contaminate a log-log convergence fit.
On 200² Config 3 the measured values (rho, against the 800² block-averaged
own-scheme reference) are:

| Solver  | s_req(N=200) | s_worst_q05 | s_worst − s_req | regime |
|---------|--------------|-------------|-----------------|----------------------|
| HLLC    | 3.13         | 1.54        | −1.59           | round-off-limited    |
| Rusanov | 2.95         | 1.23        | −1.72           | round-off-limited    |

Both solvers are **accuracy-limited at this grid**: the truncation
error sets the floor at ~3 sig digits, and the worst-5%-cell
trustworthy digits sit ~1.6 below that — i.e. the FP precision is
*not* the binding constraint at 200² Config 3 (margin is negative
because s_worst_q05 is bounded by accuracy, which depends on cell
position relative to shocks rather than on FP type). Float32 would
not improve any term, and the next gain comes from grid refinement.
The full headline table is at `docs/week4/tradeoff_summary_tables/lw_config3_200.md`;
HLLC float / Rusanov float rows wait on the B1 PrecisionConfig refactor.

I want to emphasise that `s_req(N)` answers the accuracy question
only. If you also care about **bitwise reproducibility** across
machines/compilers, that is a separate axis (`s_reliability_q05 ≥
15 for double / ≥ 7 for float`) and I report it separately rather
than fold it into the same number.

## 4. Limitations and what they block

- **`k_grad = 1.0` absorbs all shock-region differences** in the
  noise-floor divergence figures (the `|∇avg|` term outweighs the 3-σ
  term by ~14 orders of magnitude at every shock cell). This is the
  designed behaviour (it prevents a 1-cell shock offset from being
  flagged as divergence) but it means the noise-floor figures
  currently show "no divergence detected" across all three 1D tests.
  Calibrating `k_grad` from the noise-floor data itself, or running
  with `k_grad = 0` to see the pure statistical boundary, is Week-5
  work.
- **Toro Test 2 was dropped from the 1D MCA suite.** Under MCA p=53
  stochastic rounding, the near-vacuum interface produces negative-ρ
  excursions in some samples, which destabilise the CFL-limited `dt`;
  one sample ran for 29 min before I stopped it. Fixes for next week:
  either a `ρ_floor` in `cons_to_prim`, or substitute Toro Test 5 in
  the suite. This does not affect the Sod / stationary-contact /
  Lax results above.
- **Local Verificarlo build (Clang 7.0.1 in the v2.4.0 Docker image)
  segfaults on Config 3 at N ≥ 200**, regardless of the interflop
  backend and even in IEEE passthrough. The native Windows build runs
  the same problem end-to-end in 10 s, so the failure is in the
  Verificarlo-instrumented codegen. I reproduced end-to-end
  production on Cambridge's `lovelace` node (Verificarlo 2.4.0 on
  Clang 18.1.3), which works. I will document the Clang-7 regression
  for future reference but will not spend more time on it.
- **`μ_trunc` reference is now an 800² block-averaged own-scheme run**
  (`experiments/week4/reference/{hllc,rusanov}_800.bin` block-averaged
  4×4 to 200²). The earlier "self-referenced sample mean ⇒ μ_trunc ≈ 0"
  limitation is **closed**. N=400 / N=800 rows still pending — see plan
  §7 deferral list.
- **FORCE** has not been implemented this week, per your 2026-04-17
  decision to stay with Rusanov. The existing `FluxScheme` enum is
  still ready for a drop-in if you change your mind; estimated
  effort to add is <1 day.

## 5. Plan for next week

- Generate own-scheme 800² double references for both solvers and
  populate the `s_req(N)` / `s_worst_q05` / regime summary table so
  that the "how many significant figures" question has a numeric
  answer in every cell of the test matrix.
- Calibrate `k_grad` against the noise-floor data (fit
  `σ_FP(i) ∝ |∇U(i)|` in smooth regions) and regenerate the
  divergence-marker figures with the fitted value; we should then
  start seeing "x" markers where the solvers genuinely disagree
  beyond physical shock-position uncertainty.
- Add the float32 build (explicit `EulerSolver` instantiation + CMake
  `FLOAT_PRECISION` switch) so I can compare the 200² Config 3 result
  at float vs double, which is the concrete test of whether the
  `s_req(200²) ≈ 3.5` prediction above is correct.
- Add a 2D Kelvin-Helmholtz case (periodic BCs are already in the
  branch) as a second 2D Verificarlo test so we have a chaotic /
  long-time-integration case to sit alongside Config 3's shock-
  dominated case.

Happy to share any of the underlying data (npz / CSV / sample
files) if a specific detail would be useful.

Best,
Yudong
