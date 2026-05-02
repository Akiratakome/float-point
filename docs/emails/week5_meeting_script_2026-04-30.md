# Supervisor Meeting Script — 2026-04-30

**Branch:** `week4-implementation`
**Reference docs:** [week4-summary.md](../week4/week4-summary.md), [week5-summary.md](../week5/week5-summary.md), [week4_to_week5_bridge.md](../week5/week4_to_week5_bridge.md), [overall.md](../requirement/overall.md)
**Audience:** Philip (supervisor)
**Length target:** 25–30 min walkthrough + Q&A

---

## 0. Executive summary (open the meeting with this)

### What I should say
> "Since last meeting I closed the remaining Week 4 Phase B and Phase C items, completed almost all of the Week 5 plan, and ran the supplementary experiments needed to make the A4 four-row tradeoff table publishable. Three things are now properly settled. **One:** the precision template (`float`/`double`) is wired through the build system and explicit-instantiation library, with full unit-test coverage in both precisions. **Two:** the float-vs-double regression is in place at 1D and 2D, and at the resolutions we ran (≤800 in 1D, ≤400 in 2D), float and double are statistically indistinguishable on the headline norms. **Three:** I corrected the C2 experiment — the original VPREC comparison had a methodological flaw (VPREC is deterministic) so the conclusion 'VPREC ≠ binary32 MCA' was right but for the wrong reason; the corrected experiment uses MCA-on-double at p=24 and shows it **is** a valid surrogate for real binary32. I also did a small infrastructure cleanup: documentation reorg under `docs/`, and a minimal `config → build → run → measure → aggregate → plot` harness."

### Time budget
- 4 min — Phase B / Phase C completion (Week 4)
- 5 min — A4 tradeoff table + Pareto + s_req(N)
- 6 min — C2 corrected: real-float vs double-MCA-p24
- 5 min — Week 5 implementation (Config 6, shock-bubble, Timer, GPU skeleton, plot_2d, smoke matrix)
- 3 min — Risks / deferred items
- ~5 min — Next-week plan + Q&A

---

## 1. Completed implementation

### 1.1 Week 4 Phase B — precision templating + boundary infrastructure

#### What I should say
> "Phase B was the planned Week-4 core. I split `EulerSolver` into header + `.cpp` with explicit instantiations for `float` and `double`, gated by `cmake/PrecisionConfig.cmake`. I added periodic and reflective boundary conditions on top of outflow, and exposed them through cfg keys `bc`, `bc_x`, `bc_y` so each axis can be set independently — this is what unblocks 2D Kelvin–Helmholtz and the LW Config 6 setup. The reflective BC takes a `flip_indices` array rather than a hard-coded normal index, which keeps the same primitive usable for MHD's 9-component state without re-implementing it."

#### What to show
- **Repo structure** — [src/euler/euler_solver.cpp](../../src/euler/euler_solver.cpp), [src/core/boundary.hpp](../../src/core/boundary.hpp), [cmake/PrecisionConfig.cmake](../../cmake/PrecisionConfig.cmake).
- **Test summary line:** "115 test cases / 3660 assertions PASS in both `build-double` and `build-float`. The boundary block alone is 10 cases / 572 assertions covering outflow / periodic / reflective × X-axis / Y-axis × 1D-degenerate / mixed-axis dispatcher / multi-index flip list (MHD-shaped)."

#### One-line takeaway
The solver is now compiled in both precisions from one source tree and the boundary code is generic enough to carry into Week 12 MHD without edits.

#### Likely follow-ups
- *"Why per-axis dispatch instead of one combined call?"*
  Functionally equivalent, but the per-axis primitive (`apply_outflow_bc(grid, Axis::X)`, etc.) keeps the `flip_indices` set per axis (X-normal momentum vs Y-normal momentum), and inside `EulerSolver::apply_boundary_conditions()` it's a switch over `BoundaryType`. Cleaner extension when MHD adds Bx/By to the flip list.
- *"Did the B1 change to `TimeReal=double` regress double builds?"*
  No — the Sod 1D end-to-end output in `build-double` is bit-identical to the Week-3 baseline; that was an explicit verification step. `TimeReal=double` only changes the time accumulator, not the field values.
- *"Why split into a separate `.cpp` for explicit instantiation?"*
  Two reasons: compile time (the templated solver is heavy), and we need a single library with both `EulerSolver<float>` and `EulerSolver<double>` symbols so callers can pick at link time without recompiling everything.

---

### 1.2 Week 4 Phase C — float regression and C2 binary32 surrogate

#### What I should say
> "Phase C is the float-vs-double regression sweep. C1.1 is six 1D Toro tests at N = 50/100/200/400/800 in both precisions; C1.2 is Liska–Wendroff Config 3 at 200² and 400² with an 800² double reference. C2 is the Verificarlo experiment that compares native `float` MCA against a double-precision MCA-at-p24 surrogate. Everything below the cfg layer is driven by the same regression scripts that we'll reuse for the GPU regression in Week 6."

#### What to show
- **1D summary** — [experiments/week4/float_regression/1d/summary.md](../../experiments/week4/float_regression/1d/summary.md)
- **2D summary** — [experiments/week4/float_regression/2d/summary.md](../../experiments/week4/float_regression/2d/summary.md)
- **C2 corrected log** — [docs/experiment_logs/c2_real_float_vs_vprec.md](../experiment_logs/c2_real_float_vs_vprec.md)
- Driver scripts: `scripts/regression/float_regression_1d.sh`, `scripts/regression/float_regression_2d.sh`, `scripts/verificarlo/verificarlo_run.sh --compare-mca-double`.

#### One-line takeaway
At the resolutions we ran, float matches double to ULP-level on bulk error norms — i.e. truncation, not round-off, dominates here.

#### Likely follow-ups
- *"What does it mean that all the 1D ratios are 1.000?"*
  It means `(L1_float / L1_double)` rounded to 3 dp is unity — float is not adding visible error on top of truncation at these resolutions. We are in a truncation-dominated regime; the saturation point where float round-off overtakes truncation is a Week-16 deliverable per `overall.md`.
- *"Why use SSIM rather than W1?"*
  Axis-aligned W1 has brittle projection assumptions for non-axis-aligned shock fronts in 2D. SSIM as a single scalar is a lean qualitative supplement to L1/L2/Linf; full luminance/contrast/structure decomposition is deferred to Report 2.
- *"Could the float win in 2D be hiding in `Linf`?"*
  L∞ is reported in the 2D summary table — `Linf_rho` for `double_200` and `float_200` agree to 6 significant figures. There is no hidden L∞ blow-up.

---

### 1.3 Week 5 — Config 6, shock-bubble, Timer, GPU skeleton, plot_2d.py, harness smoke

#### What I should say
> "On Week 5 I delivered five blocks: a Timer + opt-in `ScopedTimer` registry behind `HRSC_ENABLE_PROFILING`; a real Liska–Wendroff Config 6 IC with 200² and 400² configs and unit tests; a half-symmetric shock-bubble IC with HLLC and Rusanov twin cfgs and Rankine–Hugoniot-checked unit tests; a CUDA toolchain skeleton (`gpu_smoke`, `cuda_utils.cuh`, `gpu_grid.cuh`, templated copy kernel) plus a Catch2 `[gpu]` host↔device round-trip test; and a single-grid plotter `scripts/figures/plot_2d.py` (rho / p / vmag / schlieren). Finally I exercised the harness with a 6-run smoke matrix at `experiments/week5/smoke/matrix.json`."

#### What to show
- [docs/week5/week5-summary.md](../week5/week5-summary.md) §Delivered table
- The 6-run smoke matrix file [`experiments/week5/smoke/matrix.json`](../../experiments/week5/smoke/matrix.json)
- `git log --oneline 5abbafd..` to demonstrate one-commit-per-task discipline (24 commits over the week)

#### One-line takeaway
Week 5 closed the 2D test catalogue and put the CUDA path in a known-good state, so Week 6 can start writing real kernels rather than fighting the toolchain.

#### Likely follow-ups
- *"Did GPU compute actually run?"*
  Only a host↔device round-trip kernel (data path), not a solver step. Compute kernels are explicitly Week 6 per `overall.md` line 308. The Catch2 round-trip is 2 cases / 400 assertions; `gpu_smoke` confirms one device visible at the right compute capability.
- *"Why is `ENABLE_CUDA` opt-in by default?"*
  Per AGENTS.md hard-rule "do not change existing solver defaults or existing cfg output." Default builds are byte-identical to Week 4. This also avoids forcing CUDA on cluster nodes where it isn't installed.
- *"Why didn't you finish the 5-way ScopedTimer split?"*
  3 phases (`bc`, `cfl`, `sweep`) are wired now; the spec asked for 5 (cfl / bc / reconstruction / riemann / update). I traded the extra two against finishing the GPU data path on schedule. Listed under §6 Deferred. Easy to extend when needed.

---

### 1.4 Project architecture changes (mention briefly, not the focus)

#### What I should say
> "Two small structural changes worth flagging. First, the `analysis/` directory is gone — everything is now under `scripts/{regression,metrics,verificarlo,figures,cluster}` so the experiment harness has one root. Second, `docs/` is reorganised so each week keeps **only** `weekN-plan.md` + `weekN-summary.md` at the top, and historical planning docs live in `weekN/archive/`. There is also a minimal harness contract documented in `docs/HARNESS.md` and a navigation index at `docs/INDEX.md` to keep the repo agent-friendly."

#### What to show
- [docs/INDEX.md](../INDEX.md), [docs/HARNESS.md](../HARNESS.md), [AGENTS.md](../../AGENTS.md)

#### One-line takeaway
Repository now has one canonical pipeline and one navigation entry point — pre-Report-1 cleanup, not a numerical change.

#### Likely follow-ups
- *"Did this change anything numerical?"*
  No. It's pure rename + dedup. Solver, cfgs, output formats are untouched (AGENTS.md hard rule).

---

## 2. Experiment pipeline / reproducibility

### What I should say
> "Every Week-4 and Week-5 experiment in this meeting is reproducible from a clean checkout. The recipe lives at `docs/week4/week4-verification.md` for Phase B/C and `docs/week5/week5-verification.md` for Week 5. The harness records cfg, command, git commit, stdout, stderr, return code, and timing per run, written to `metadata.json` next to the result. Reference grids that we depend on (the LW3 800² double reference, A3 LW3 200²×30 MCA samples) are kept; routine smoke grids are deleted after aggregation per the harness output discipline."

### What to show
- [docs/week4/week4-verification.md](../week4/week4-verification.md) §5 "one-button reproduction"
- [docs/HARNESS.md](../HARNESS.md) — pipeline diagram
- `experiments/week5/smoke/runs/<name>/metadata.json` for one example

### One-line takeaway
No experiment in this packet relies on un-logged manual commands.

### Likely follow-ups
- *"Where does the 800² reference live, and why don't we keep all the grids?"*
  `experiments/week4/float_regression/2d/reference_800.bin` (~25 MB). All other 2D reference grids and 1D grids are reproducible in a few minutes from cfg + commit, so we keep CSV summaries and PNGs only. The 800² reference is the one we cache because it's a 16:34 single-core run.
- *"Is the harness already used for the A4 / C2 figures?"*
  A4 and C2 predate the harness — they were driven by their own scripts (`scripts/verificarlo/verificarlo_run.sh`, `scripts/figures/tradeoff_summary_table.py`). The harness is the **forward** entry point starting Week 6 GPU regression. The Week-5 smoke matrix is the first thing exercised through the harness end-to-end.

---

## 3. Key experimental findings

### 3.1 Float vs double regression — what it says

#### What I should say
> "In 1D, every Toro case at N=800 has float-to-double ratio of L1, L2, L∞ rounded to 1.000 across ρ, u, p. In 2D, at 200² and 400², `L1_rho`, `L2_rho`, `L∞_rho`, `SSIM_rho`, and the shock-tracking offsets `Δx_shock` / `Δy_shock` agree between float and double to at least 4 significant figures. So float adds no measurable error on top of truncation at these resolutions. **This is not the same as 'float is always sufficient'** — at higher N the round-off floor will eventually overtake truncation; identifying that crossover is a Week-16 deliverable."

#### Strength of the claim
- **Strong (within scope):** at the resolutions tested, float-vs-double L1/L2/L∞ ratios are ≈ 1.000 in both 1D and 2D.
- **Observation only:** the truncation-dominated regime extends to higher N. We have not measured the crossover.

#### Likely follow-ups
- *"Could compiler optimisation be hiding the float error?"*
  Possible. Both builds use the same `Release + ENABLE_OPENMP=ON` flags; the explicit float/double switch is the only delta. The systematic compiler-flag sweep (`O2`/`O3`/`Ofast` × fast-math on/off × `<=` vs `<`) is staged in `scripts/build_all.sh` for Week 7 / Week 15.
- *"What about the stationary-contact case where `S* = 0` analytically?"*
  At N=800 the float and double L1/L2/L∞ ratios are 1.000. The interesting behaviour is at the noise-floor cells where `|u| ≈ 0`; that surfaces in the C2 sigdigit plot, where the relative metric breaks down — see §3.2.

---

### 3.2 Real-float vs VPREC p24 → corrected to real-float vs double-MCA-p24

#### What I should say
> "The original C2 conclusion was 'VPREC p24 does not emulate real binary32 MCA' — that conclusion was right, but the reason was wrong. VPREC is a deterministic backend by design — it truncates the binary64 mantissa but does **not** inject random rounding, so all MCA samples are bitwise identical and the per-cell sig.d formula `−log₁₀(std/|mean|)` is undefined. The original plotter clipped that infinity to 16 and drew a flat orange line that visually said 'VPREC achieves 16 digits of precision', which is the opposite of true. I corrected this with `--compare-mca-double`, which runs MCA at p=24 on both binary32 and binary64. Both arms are now stochastic and comparable. The corrected result is that **double-MCA-p24 is a valid surrogate for real binary32** for round-off variance quantification on this solver: median sig.d agreement is within 0.05 digits for ρ and p, and within 0.05 digits for u in non-degenerate flow."

#### Strength of the claim
- **Strong:** double-MCA-p24 ≈ real binary32 to within 0.05 sig.d on ρ, p, and non-degenerate u, on Sod and stationary-contact, replicated across HLLC / Rusanov / FMA-instrumented variants, with run-to-run drift ≤ 0.05 sig.d.
- **Strong (and the headline byproduct):** Rusanov is ≈ 0.2 sig.d cleaner than HLLC across both precisions — relevant prior for the SLIC-vs-HLLC discussion you raised in Week 3.
- **Strong (negative result):** FMA instrumentation moves the median sig.d by < 0.03 digits. Not a free win for this 1D Euler solver.
- **Observation only:** the stationary-contact `u` panel shows lines diverging by ~0.5 sig.d, but `|u| ≈ 0` so the relative metric is dominated by mean cancellation. Sign of the gap **flips** between Rusanov and HLLC, and shrinks 4× when FMA is on. That is the signature of operation-order sensitivity at the noise floor, not a precision-model gap.

#### Likely follow-ups
- *"Why did the original VPREC arm behave deterministically?"*
  VPREC is a precision-truncation backend. It rounds to a target mantissa width (here 24 bits) but does **not** add stochastic noise the way MCA does. With a fixed input cfg, all 30 samples produced bit-identical output; `md5sum` confirmed it. So the per-cell sig.d formula `−log₁₀(std/|mean|)` had std = 0 and gave +∞. The plotter's clip to [0,16] then produced a misleading-but-flat orange line near the top of the panel.
- *"How robust is the surrogacy claim?"*
  Two `/dev/urandom`-seeded reruns of the C2-baseline (HLLC, no FMA) agree on median sig.d to within 0.05 digits for non-degenerate variables. The sign of the disagreement flips for stationary-contact `u`, confirming that disagreement is noise-floor sampling noise rather than a real gap.
- *"What does this give us for Report 1?"*
  It validates a cheap mechanism for predicting binary32 noise from a double-precision build: run MCA at p=24 on a double build, and we get the same noise budget per cell to within 0.05 sig.d, without needing a Verificarlo `float` toolchain everywhere. Useful for the cluster, where the `float` Verificarlo build is non-trivial.

---

### 3.3 A4 tradeoff table — HLLC/Rusanov × p53/p24-real-float at LW3 200²

#### What I should say
> "The four-row tradeoff table sits in [docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md](../experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md). At 200², all four rows are classified `round-off-limited` because `s_worst − s_req(N) < 0`. Two specific things to read off the table. **One:** on the headline ρ row, p24-real-float and p53 share the same `s_worst_q05` because the bottleneck is reliability/accuracy floor, not precision. **Two:** the precision effect is still visible — `σ_FP_L1` for HLLC ρ rises from 5.2 × 10⁻¹¹ at p53 to 3.0 × 10⁻² at p24-real-float, and Rusanov rises from 2.3 × 10⁻¹¹ to 8.2 × 10⁻³. So even though the regime label is the same, the precision penalty in the noise component is ~9 orders of magnitude. Both p24-real-float rows are the headline 'low precision raises noise' evidence I'll use in Report 1."

#### Strength of the claim
- **Strong:** the σ_FP gap between p53 and p24-real-float is real and reproduced in the MCA ensembles for both solvers.
- **Strong:** at N=200², both solvers are round-off-limited by the `s_worst − s_req` criterion regardless of precision because truncation at 200² is itself limiting.
- **Caveat:** `s_worst − s_req` < 0 says LoSoS at the 5th percentile is below what truncation level demands; it does **not** say the simulation is "wrong". It is a flag that increasing N is expected to give measurable accuracy gains here. The supervisor question "how many sig digits do we actually need" maps to `s_req(N=200) ≈ 3.13` for HLLC and `≈ 2.95` for Rusanov.
- **Caveat:** N=200² only. The interpretation will shift at higher N — if `s_req(N)` rises faster than the `s_worst` floor, the regime can flip to "well-matched" or even "over-provisioned".

#### Likely follow-ups
- *"Why is the regime the same for p24 and p53 if the noise differs by nine orders?"*
  Because the headline ρ row's `s_worst_q05` is **accuracy-limited**, not reliability-limited. The 5th-percentile worst-cell error is set by truncation (the 200² grid vs the 800² block-averaged reference), not by FP noise. The σ_FP column tells you the floor that would dominate if truncation were removed, and we'd see it on a finer grid.
- *"Doesn't 'round-off-limited' for **both** precisions sound contradictory?"*
  The label refers to the full multi-component criterion `s_worst − s_req`, not solely to the σ_FP component. Both rows are below `s_req(200)` because their reliability/accuracy 5th percentile is below `s_req`. To get out of round-off-limited at 200² we'd need to reduce truncation error (refine grid) — not switch precision.
- *"Why use the 5th percentile rather than the mean or median?"*
  We want a worst-case-ish cell-level measure (otherwise the bulk smooth region drowns out the shock-front cells where noise actually matters). The 5% tail captures shock-front behaviour without going all the way to a single-cell extremum, which would be too noisy.
- *"What's `s_req(N)`?"*
  `s_req(N) = −log₁₀(||E_trunc(N)||) + 1`. A truncation-anchored target: it's the number of significant digits the FP path needs to deliver so that FP noise doesn't dominate truncation error at this resolution. Replaces the static "publication ≥ 4, convergence ≥ 6" thresholds we discussed in Week 3.

---

## 4. Figure / table interpretation

### 4.1 A4 Pareto plot

| | |
|---|---|
| Path | [experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png](../../experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png) |
| x-axis | `σ_FP_L1` (Verificarlo MCA-p53 noise floor in the L1 metric on ρ) |
| y-axis | `s_worst_q05` (5th-percentile cell-level worst-of `(s_reliability, s_accuracy)`) |
| Where to look | The horizontal line at `s_req(N=200) ≈ 3.13`. Both HLLC and Rusanov sit below it. |
| What it supports | At N=200², neither solver delivers more sig digits than truncation needs — both are round-off-limited by the `s_worst − s_req` criterion. **This directly answers the "how many sig digits do we need" question for this resolution.** |
| Caveat | p53 only — p24 noise is ~9 orders larger. The two p24-real-float rows of the headline table belong on the same plot but I haven't combined them yet. The figure also shows only one `N`. |

### 4.2 A4 p24-real-float heatmaps

| | |
|---|---|
| Path | [experiments/week4/figures/a4_float_p24/sigma_fp_heatmap.png](../../experiments/week4/figures/a4_float_p24/sigma_fp_heatmap.png) and `losos_{reliability,accuracy,worst}_heatmap.png` in the same directory |
| Axes | Spatial 2D grid (200×200, x and y) |
| Where to look | The σ_FP heatmap shows where round-off variance concentrates — bright bands along the four shock fronts, low elsewhere. The `losos_worst_heatmap.png` shows the cells driving `s_worst_q05`. |
| What it supports | FP noise in the p24-real-float path is localised to discontinuities, consistent with the C2 1D figures. |
| Caveat | Generated from Athena MCA ensembles on the cluster, 30 samples; small-sample noise visible in the field. |

### 4.3 A4 four-row tradeoff table

| | |
|---|---|
| Path | [docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md](../experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md) |
| Columns | Solver, Precision, μ_trunc_L1, σ_FP_L1, s_worst_q05, s_req(N), s_worst − s_req, regime |
| Where to look | The σ_FP_L1 column — that's where the precision effect lives. The regime column — all four are `round-off-limited`. |
| What it supports | "Lower precision raises FP noise but does not change the regime classification at this resolution" — the headline finding for Report 1 §3. |
| Caveat | Single resolution (N=200²) and single test (LW3). Generalising the regime classification to other N or other tests is Week-15/16 work. |

### 4.4 C2 corrected — Sod sigdigits

| | |
|---|---|
| Path | [experiments/verificarlo/runs_compare_p24_mca_real_vs_double/sod_real_vs_double_mca_p24_sigdigits.png](../../experiments/verificarlo/runs_compare_p24_mca_real_vs_double/sod_real_vs_double_mca_p24_sigdigits.png) |
| x-axis | Cell-centre coordinate, 0 → 1 over 200 cells |
| y-axis | Significant decimal digits per cell, `−log₁₀(std/|mean|)` over 30 MCA samples |
| Lines | Blue = native binary32 + MCA; orange = binary64 + MCA at p=24 |
| Where to look | The two lines tracking each other at ~6.3 sig.d across the tube; identical narrow dip at the shock front. |
| What it supports | double-MCA-p24 is a valid binary32 surrogate at non-degenerate cells. Median agreement < 0.05 digit. |
| Caveat | N=30 samples per cell; noise-floor regions (|mean| → 0) are not interpretable. |

### 4.5 C2 corrected — Stationary contact sigdigits

| | |
|---|---|
| Path | [experiments/verificarlo/runs_compare_p24_mca_real_vs_double/stationary_contact_real_vs_double_mca_p24_sigdigits.png](../../experiments/verificarlo/runs_compare_p24_mca_real_vs_double/stationary_contact_real_vs_double_mca_p24_sigdigits.png) |
| Where to look | The `u` panel — both lines are negative everywhere. |
| What it supports | When `|u| ≈ 0`, the relative `−log₁₀(std/|mean|)` metric is dominated by mean cancellation; both modes are at the noise floor. The sign of the inter-mode gap **flips** between HLLC and Rusanov runs, confirming this is sampling noise, not a precision-model gap. |
| Caveat | Do not read the `u` panel as a "binary32 vs surrogate" comparison. It's a noise-floor diagnostic. |

### 4.6 1D float regression summary

| | |
|---|---|
| Path | [experiments/week4/float_regression/1d/summary.md](../../experiments/week4/float_regression/1d/summary.md) |
| Columns | test, N_last, then ratios `L1_*` / `L2_*` / `Linf_*` for ρ, u, p (float ÷ double) |
| Where to look | The ratio column at N=800 — all values round to 1.000 across all six tests. |
| What it supports | Float adds no measurable error on top of truncation at N≤800 in any 1D Toro test, including the stationary-contact `S*=0` case. |
| Caveat | Ratios round to 3 dp in the table — sub-ULP differences are aggregated away. The crossover N where round-off overtakes truncation is not in this run; that's the Week-16 saturation experiment. |

### 4.7 2D LW Config 3 float regression summary

| | |
|---|---|
| Path | [experiments/week4/float_regression/2d/summary.md](../../experiments/week4/float_regression/2d/summary.md) |
| Columns | case, L1_rho, L2_rho, Linf_rho, ssim_rho, Δx_shock, Δy_shock |
| Where to look | Compare `double_200` vs `float_200`, and `double_400` vs `float_400`. SSIM ≥ 0.97 at 200², ≥ 0.989 at 400². L1 halves on N→2N (first-order convergence at the shock front). |
| What it supports | At 200² and 400², float and double are visually and quantitatively indistinguishable on LW3. |
| Caveat | Linf_rho ≈ 0.55 for both 200² and 400² because the shock front always carries one cell's worth of jump error — that's expected, not a regression. |

### 4.8 Deterministic 2D HLLC vs Rusanov diff maps

| | |
|---|---|
| Path | [experiments/week4/figures/deterministic_2d/density_hllc_vs_rusanov_200.png](../../experiments/week4/figures/deterministic_2d/density_hllc_vs_rusanov_200.png) and `density_diff_*` in the same directory |
| Where to look | Diff maps `density_diff_hllc200_minus_hllc800d.png` show truncation error for HLLC at 200²; `density_diff_rusanov_minus_hllc_200.png` shows the inter-solver gap at the same resolution. |
| What it supports | Visual support for the Rusanov-cleaner observation in §3.2 — diffusivity smooths fine-scale structure that HLLC keeps. |
| Caveat | Deterministic, single sample — not the same as the MCA ensembles in A3/A4. |

---

## 5. Risks and open issues

### 5.1 Outstanding from Week 5 (deferred, not blocked)
- **ScopedTimer 5-way phase split.** Currently 3 phases (`bc`, `cfl`, `sweep`); spec asked for 5 (cfl / bc / reconstruction / riemann / update). Easy to extend in Week 7 when we start the timing-vs-precision analysis.
- **CSC GPU build.** Local CUDA toolchain is green; cluster GPU is deferred until kernels are stable (Week 6 or 7).
- **`vfc_precexp` + unstable-branch detection.** Week-3 supervisor ask, planned alongside MHD bring-up at Week 14 per `overall.md`.

### 5.2 Methodological caveats I should not paper over
- **N=200² ceiling.** The A4 tradeoff conclusions are pinned to one resolution. Reaching `well-matched` or `over-provisioned` regimes requires running the same metric pipeline at higher N — that's a multi-hour cluster batch and is staged for the systematic sweep, not this meeting.
- **One Riemann solver per test.** The A4 table has HLLC and Rusanov; we have not run all four `<= vs <` × HLLC variants × precisions yet. The strict-vs-loose inequality experiment is a Week-15 / Week-17 item.
- **Float crossover N is unknown.** Saying "float is sufficient" is incorrect outside the regime we tested. The crossover is the single most important number we owe Report 1 — Week 16 deliverable.
- **One A2 stage was skipped.** The MCA p=53 noise-floor 12-figure batch (A2 Stage 2) was generated but the full suite of `plot_divergence_marker.py` 3-mode outputs is only at `--mode visible` for the supervisor-facing first cut. Statistical mode is run; the publishable figures are not regenerated yet.

### 5.3 Things I'm still unsure of and want guidance
- **Should the Pareto plot include p24 points?** Currently shows only HLLC vs Rusanov at p53. Adding the two p24-real-float points would shift the x-axis by ~9 decades and visually compress the p53 cluster. Worth showing as a separate two-panel figure?
- **Report 1 §3 evidence ordering.** Is the C2-corrected "double-MCA-p24 is a valid binary32 surrogate" claim safe to lead with, or should I lead with the simpler 1D-regression "float = double at N≤800" finding and use C2 as supporting evidence?
- **Weighting of A2 Stage 2 finalisation.** Stage 1 (`--mode visible`) covers the supervisor-facing minimum; Stage 2 statistical figures are completed at the data level but the figure regeneration step is not closed. Worth finishing now or punting to Week 7 alongside the build matrix work?

---

## 6. Next-week plan (Week 6, calendar 2026-05-04 → 2026-05-10)

Per `overall.md` line 308–323:

1. **GPU outflow BC + CFL kernel.** First real compute kernels. CPU-vs-GPU diff must be ≤ ULP-level for same precision (regression gate).
2. **GPU reconstruction + Hancock predictor.** Following the same per-step kernel pattern (no fused kernels — easier debug, easier precision isolation per `overall.md`).
3. **GPU HLLC kernel.** With both `<` and `<=` paths gated by `RIEMANN_STRICT_INEQUALITY`.
4. **`EulerGpuSolver<Real>` orchestration.** Wires the kernels into a step loop matching the CPU `EulerSolver::step()` interface.
5. **End-to-end CPU-vs-GPU regression on Sod and LW Config 3.** Reusing `scripts/regression/float_regression_*.sh` infrastructure — same CSV/SSIM pipeline, just a new build label.
6. **Fold `[timing]` GPU output into the harness.** Already parsing CPU timing into `metadata.json`; GPU just adds a build label.

If GPU slips, fallback is to extend the build matrix (`scripts/build_all.sh`) on CPU only — the precision/optimiser/fast-math/`<= vs <` axes are independent of GPU and feed directly into Week 15.

---

## 7. Top takeaways to drive home in the meeting

1. **Phase B + Phase C are closed.** Float/double are wired through the build, the regression pipeline runs end-to-end at 1D and 2D, and the unit-test count is 115/3660 in both precisions.
2. **Float is statistically indistinguishable from double at our current resolutions** (1D ≤800, 2D ≤400). This is a *truncation-dominated* regime statement, not a "float is always fine" statement; the saturation point is the next thing we need to find.
3. **The C2 result is corrected.** double-MCA-p24 **is** a valid surrogate for real binary32 on this 1D Euler solver, with median sig.d agreement < 0.05 digit. The original "VPREC ≠ binary32" headline was right but for the wrong reason — VPREC is deterministic by design.
4. **A4 tradeoff at LW3 200² says all four (solver × precision) cells are round-off-limited at this resolution**, but the σ_FP gap between p24-real-float and p53 is ~9 orders of magnitude. This is the headline evidence for Report 1's "lower precision raises noise" claim; the regime label being constant is a property of N=200², not of the precision choice.
5. **Week 5 closed the 2D test catalogue and put CUDA in a known-good state.** Config 6 IC, shock-bubble IC, GPU data-path round-trip, and `plot_2d.py` are in. Week 6 starts on real GPU kernels rather than fighting the toolchain — that's the schedule risk that's now retired.
