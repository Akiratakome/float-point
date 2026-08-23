# Week 18 Supervisor Meeting

> Generated 24 July 2026. This document follows the same speaking format as
> the Week 14 supervisor meeting report. All numerical values were checked
> against the named `summary.json` files. The current status authority is
> `docs/experiment_logs/report2_evidence_map.md`.
>
> This week closes the Week 16/17 evidence synthesis and adds **100 new local
> solver executions**: 72 robustness runs, four deterministic runs matched
> exactly to the CSC smoke configuration, and 24 KH timing executions (four
> warm-ups plus 20 measured runs). On CSC, the native Verificarlo pipeline also
> completed 16 reduced-case sample grids across HLL/HLLD and p53/p24. The full
> 256^2, t=1.0, N=30 Kelvin-Helmholtz MCA matrix remains a separate CSC job.

---

## One-line summary

The main result remains that **precision is the dominant observed accuracy
axis**. The CSC native-Verificarlo smoke now supplies independent stochastic
evidence: across HLL/HLLD and four fields, p24 spread is 2.71e8-4.24e8 times
p53 spread, and matched local FP32-versus-FP64 differences lie within a factor
of 0.20-2.18 of the p24 spread. Repeated GPU timing, 0-ULP hardware/thread
comparisons, and the non-monotonic CFL result remain the supporting robustness
evidence. The new five-repeat KH timing shows FP32 speed-ups of 1.181x for
HLL and 1.154x for HLLD, while HLLD costs 14.7%-17.3% more than HLL.

---

## What we actually did

1. **Completed the hardware axis with repeated measurements.** The validated
   HLL CPU/GPU matrix was repeated five times for Brio-Wu and Orszag-Tang in
   float and double. The report now uses medians and interquartile ranges
   instead of a single wall-time measurement.
2. **Added two-dimensional thread reproducibility.** Orszag-Tang and
   Kelvin-Helmholtz were run in float and double with
   `OMP_NUM_THREADS = 1, 2, 4, 8`, and every result was compared with its
   same-case, same-precision one-thread reference.
3. **Added a Kelvin-Helmholtz CFL ladder.** HLL and HLLD were run at
   CFL = 0.2, 0.4, 0.6, and 0.8 in float and double. This separates time-step
   sensitivity from the precision comparison without changing the canonical
   `kh.cfg`.
4. **Consolidated the Week 16 Kelvin-Helmholtz evidence.** Both HLL and HLLD
   have complete 24-variant deterministic matrices and a passed 256^2 versus
   512^2 validation gate.
5. **Kept the unexpected temporal-divergence result.** The fixed-window fit
   did not observe the planned Orszag-Tang-greater-than-Brio-Wu ordering. It is
   reported as a bounded negative result, not removed.
6. **Validated the native CSC Verificarlo path.** CSC has no Docker or
   Apptainer, so the smoke used the installed Verificarlo 2.4.0 and clang
   18.1.3 directly. Four HLL/HLLD x p53/p24 blocks completed with N=4 samples.
7. **Ran a matched local triangulation experiment.** The exact CSC 64^2,
   t=0.05 configuration was run locally with HLL/HLLD in FP64 and FP32. All
   four runs completed in 15 steps with finite positive states.
8. **Quantified MCA cost and corrected the execution model.** Quad MCA costs
   24.0 s/step versus 0.0575 s/step natively in the measured short run, a
   417x overhead. Thirty samples run concurrently on 32 workers; p53 and p24
   are separate Slurm tasks to retain margin under the 6 h cap.
9. **Regenerated the figures after visual review.** Zero-valued ULP evidence
   is displayed explicitly as `0 ULP`, and the new MCA figures separate
   measured noise, deterministic triangulation, and execution cost.
10. **Added a controlled KH runtime comparison.** HLL/HLLD x FP64/FP32 at
   256^2, t=1.0, CFL=0.4 and one OpenMP thread were each warmed up once and
   measured five times. Every repeated output is bit-exact at 0 ULP.

---

## The figures: how to read them, what they show

Each figure starts with a **one-line takeaway**, followed by **how to read it**
and the interpretation boundary.

### A - Which experimental axis matters most? `experiments/week17/paper_figures/fig_w17_axis_synthesis.png`

- **One line:** **precision remains the dominant observed axis**; compiler
  choices are secondary, and the covered hardware axis changes performance
  but not the saved numerical result.
- **How to read:** the figure ranks the largest observed density differences
  collected by the Week 17 synthesis. Across the available packets, the
  largest double-precision \(L_\infty(\rho)\) difference is
  \(8.84\times10^{-12}\), whereas the largest float difference reaches
  \(3.12\times10^{-3}\). The largest recorded fast-math variation is
  \(6.45\times10^{-7}\), and the largest `<=` versus `<` branch variation is
  \(4.93\times10^{-7}\).
- **What it shows:** the scale separation is large enough that the central
  Report 2 conclusion is not based on one test case: changing numerical
  precision produces much larger observed differences than the compiler or
  branch variants in the current evidence.
- **Boundary:** this is a bounded ranking of the committed W15-W18 packets. It
  is not a universal theorem about all HRSC methods, compilers, or hardware,
  and it does not promote provisional rows in the evidence map.
- **Authority:** `experiments/week17/report2_synthesis/summary.json`.

### B - Is the GPU result reproducible, and is the speed-up real? `experiments/week18/supplemental/hardware_repeats/figures/hardware_repeats.png`

- **One line:** the covered CPU and GPU HLL solutions remain **bit-exact at
  0 ULP**, while five repetitions confirm a large GPU benefit only for the
  two-dimensional case.
- **How to read:** panel (a) shows median CPU wall time divided by median GPU
  wall time; the error bars show the interquartile spread of the five paired
  speed-ups. The dashed line at 1 means equal speed. Panel (b) displays the
  maximum same-precision ULP distance and labels every zero explicitly.
- **Specific results:** Orszag-Tang reaches a median speed-up of **6.17x**
  in double and **5.92x** in float. The corresponding median CPU/GPU times are
  27.51/4.46 s and 20.97/3.54 s. Brio-Wu reaches only 0.51x in double and
  0.49x in float, so the GPU is slower for this small 1D problem because
  launch and transfer overhead dominate.
- **What it shows:** the hardware conclusion is now supported by repeated
  timing rather than one run. Hardware is a strong performance axis for the
  larger 2D workload, but it is not an accuracy separator in the covered
  HLL path.
- **Boundary:** this does not cover HLLD on GPU, Kelvin-Helmholtz on GPU, GPU
  MCA, multiple GPU models, or a broad performance matrix.
- **Authority:** `experiments/week18/supplemental/hardware_repeats/summary.json`.

### C - Do OpenMP thread counts change the solution? `experiments/week18/supplemental/thread_repro/figures/thread_repro.png`

- **One line:** **No.** All 16 two-dimensional comparisons are bit-exact
  across 1, 2, 4, and 8 threads.
- **How to read:** panel (a) is a four-by-four grid: Orszag-Tang and
  Kelvin-Helmholtz, each in double and float, against four thread counts.
  Every cell reads `0 ULP`. Panel (b) shows wall time relative to the
  one-thread run.
- **Specific results:** every run completes with the same step count and a
  finite positive state; both the maximum ULP distance and maximum absolute
  difference are exactly zero. Runtime stays within approximately 3.5% of the
  one-thread baseline, so this build does not show meaningful thread scaling.
- **What it shows:** the tested OpenMP loop structure introduces no
  thread-ordering variability in the saved fields. This strengthens the
  reproducibility argument independently of the CPU/GPU comparison.
- **Boundary:** this is an OpenMP result for one workstation and the covered
  HLL cases. It does not establish MPI reduction-order reproducibility, and
  the near-flat timing is not presented as an OpenMP performance result.
- **Authority:** `experiments/week18/supplemental/thread_repro/summary.json`.

### D - Does changing the CFL number change the precision conclusion? `experiments/week18/supplemental/kh_cfl/figures/kh_cfl.png`

- **One line:** CFL changes the size of the fp32/fp64 difference, but the
  response is **non-monotonic**; lowering CFL does not automatically reduce
  floating-point drift.
- **How to read:** panel (a) shows the final
  \(L_\infty(\rho)\) difference between fp32 and fp64 for HLL and HLLD at four
  CFL values. Panel (b) shows the fp64 step count; HLL and HLLD coincide at
  2296, 1148, 766, and 574 steps.
- **Specific results:** HLL ranges from **8.91e-7** to **4.68e-6** across the
  ladder. HLLD ranges from **3.16e-6** to **7.20e-6**. All 16 runs complete
  with finite positive states. At the canonical CFL 0.4, the differences are
  \(1.79\times10^{-6}\) for HLL and \(3.23\times10^{-6}\) for HLLD.
- **What it shows:** time-step selection modulates the accumulated
  floating-point difference, and the more complex HLLD fan is larger than HLL
  at every tested CFL in this case. The non-monotonic curves argue against a
  simplistic claim that more time steps always improve precision agreement.
- **Boundary:** four CFL values at one grid and final time do not establish a
  temporal convergence order or a general HLL-versus-HLLD accuracy ranking.
- **Authority:** `experiments/week18/supplemental/kh_cfl/summary.json`.

### E - Is Kelvin-Helmholtz now a complete precision case? `experiments/week17/paper_figures/fig_w16_kh_precision_mca_boundary.png`

- **One line:** the deterministic Kelvin-Helmholtz matrix is complete, and the
  reduced MCA test shows the expected p24/p53 separation, but the **full
  256^2, t=1.0, N=30 MCA result remains unclaimed**.
- **How to read:** the deterministic panels compare all 24 CPU build variants
  with the same-grid fp64 reference for HLL and HLLD. Double variants stay at
  approximately \(2.00\times10^{-15}\) for HLL and
  \(9.99\times10^{-15}\) for HLLD, while float variants lie at
  \(1.79\)-\(1.82\times10^{-6}\) for HLL and
  \(3.23\)-\(4.32\times10^{-6}\) for HLLD.
- **MCA smoke result:** on the reduced 64^2, t=0.05 problem with N=30, HLL
  density spread changes from \(8.86\times10^{-16}\) at p53 to
  \(8.28\times10^{-8}\) at p24; HLLD changes from
  \(9.03\times10^{-16}\) to \(2.75\times10^{-7}\).
- **Validation context:** the independent 256^2-versus-512^2 gate passes with
  \(L_1(\rho)=1.836\times10^{-3}\), mass relative error zero, and
  \(\mathrm{div}B_{\max}=6.714\times10^{-4}\).
- **Boundary:** the reduced MCA experiment proves toolchain feasibility and
  the direction of the noise-floor separation only. It cannot replace the
  full-size, full-time stochastic experiment.
- **Authorities:** `experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.json`,
  `experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.json`, and
  `experiments/week16/kelvin_helmholtz_precision/validation/summary.json`.

### F - Did the chaotic 2D case diverge faster? `experiments/week15/mhd_temporal_divergence/figures/temporal_divergence.png`

- **One line:** **the planned contrast was not observed.** Over the fixed fit
  windows, Brio-Wu has a much larger fitted fp32/fp64 growth rate than
  Orszag-Tang.
- **How to read:** the curves show density drift versus time, and the fitted
  lines use the pre-declared windows [0.01, 0.1] for Brio-Wu and [0.1, 0.5]
  for Orszag-Tang. There are 15 paired Brio-Wu samples and 25 paired
  Orszag-Tang samples, generated by 80 provenance-complete runs.
- **Specific results:** the L1 fitted rate is **30.615** for Brio-Wu but only
  **0.0293** for Orszag-Tang. The Orszag-Tang \(L_\infty\) fitted rate is
  negative, \(-0.0422\), over its fixed window.
- **What it shows:** the visually chaotic 2D case does not automatically have
  a larger short-window precision-divergence fit. This is a useful negative
  result because it prevents the report from turning morphology into an
  unsupported sensitivity claim.
- **Boundary:** these are Lyapunov-like engineering fits for deterministic
  fp32-versus-fp64 perturbations. They are not formal maximal Lyapunov
  exponents or physical instability rates, and fit quality is not
  independently gated.
- **Authority:** `experiments/week15/mhd_temporal_divergence/summary.json`.

### G - Which final evidence gates are closed? `experiments/week17/paper_figures/fig_w17_gates_and_boundaries.png`

- **One line:** the hardware, OT/KH 512-grid, synthesis, and all three Week 18
  robustness gates pass; the only explicit core gap shown here is full
  Kelvin-Helmholtz MCA.
- **How to read:** positive gate markers identify evidence packages with
  complete machine-readable rows and passed checks. Boundary markers identify
  conclusions that remain excluded.
- **What it shows:** both OT and KH 256^2-versus-512^2 engineering gates pass,
  the W17 synthesis has all required source summaries, and the new Week 18
  combined supplemental gate passes after 72/72 successful runs.
- **Boundary:** two resolutions do not establish asymptotic convergence. Full
  256^2, t=1.0, N=30 KH MCA is still unclaimed until the CSC summaries report
  completed p53 and p24 blocks for both HLL and HLLD.
- **Authority:** `experiments/week18/supplemental/summary.json` and
  `experiments/week17/report2_synthesis/summary.json`.

### H - Does the CSC stochastic result agree with deterministic precision separation? `experiments/week18/csc_findings_synthesis/figures/csc_mca_precision_triangulation.png`

- **One line:** **Yes, on the reduced matched case.** p24 and p53 separate by
  8.43-8.63 decades, while the local FP32/FP64 differences are the same order
  of magnitude as the CSC p24 spread.
- **How to read:** panel (a) compares p24 spread for HLL and HLLD in density,
  x-velocity, transverse magnetic field, and pressure. Panel (b) gives the
  p24/p53 amplification in decades. Panel (c) places the local deterministic
  FP32/FP64 Linf difference against the CSC p24 MCA spread; the dashed diagonal
  denotes equal magnitude.
- **Specific results:** p24/p53 ratios range from **2.71e8 to 4.24e8**. HLLD
  p24 spread exceeds HLL by 3.00x in rho, 4.10x in vx, 1.94x in By, and 1.46x
  in pressure. The eight deterministic-to-p24 ratios range from **0.20 to
  2.18**, so all comparisons remain within one decade.
- **What it shows:** two independent methods now agree on the precision scale,
  and the more complex HLLD path is more MCA-sensitive than HLL for every
  measured field in this reduced configuration.
- **Boundary:** this is 64^2, t=0.05 with only N=4 MCA samples. It validates the
  native CSC pipeline and direction of the solver contrast; it is not the full
  KH stochastic conclusion and does not prove a general HLLD ranking.
- **Authority:** `experiments/week18/csc_findings_synthesis/summary.json` and
  `experiments/report2_w16_verificarlo_findings/smoke_validation_64sq/`.

### I - Was the long CSC runtime a stalled solver? `experiments/week18/csc_findings_synthesis/figures/csc_mca_cost_feasibility.png`

- **One line:** **No.** The process was active in MCA arithmetic; the measured
  slowdown is instrumentation cost, not a timestep-collapse or I/O bug.
- **How to read:** panel (a) compares seconds per step for native IEEE, quad
  MCA, MCA-int MCA, and MCA-int random rounding. Panel (b) shows the 2.5-3.0 h
  dedicated-node planning range for one concurrent N=30 precision block and
  why running p53 and p24 as separate tasks preserves margin below 6 h.
- **Specific results:** the short benchmark measured 0.0575 s/step natively,
  24.0 s/step for quad MCA, 11.43 s/step for MCA-int MCA, and 6.25 s/step for
  MCA-int random rounding. MCA-int cannot represent the required p24 virtual
  precision, so both p53 and p24 use quad for a controlled comparison.
- **Boundary:** login-node timings measure backend cost under contention; the
  2.5-3.0 h range is the observed dedicated-node planning value. It is not a
  general Verificarlo performance benchmark.
- **Authority:** `experiments/report2_w16_verificarlo_findings/README_findings.md`
  and its raw timing logs.

### J - What is the runtime cost of precision and solver choice? `experiments/week18/kh_solver_timing/figures/kh_solver_precision_timing.png`

- **One line:** FP32 gives a modest but repeatable CPU benefit, while HLLD is
  consistently more expensive and has the larger FP32/FP64 density separation
  on this KH configuration.
- **How to read:** panel (a) gives the median of five end-to-end wall times; the
  error bars run from Q25 to Q75. Panel (b) gives dimensionless speed/cost
  ratios, where the dashed line at one means no difference. Panel (c) places
  FP32 median runtime against the same-solver maximum density difference.
- **Measured values:** HLL takes **34.484 s (IQR 0.103 s)** in FP64 and
  **29.196 s (IQR 0.801 s)** in FP32. HLLD takes **39.542 s (IQR 0.197 s)**
  and **34.254 s (IQR 0.158 s)**. FP32 is therefore 1.181x faster for HLL and
  1.154x for HLLD. HLLD costs 1.147x HLL in FP64 and 1.173x in FP32.
- **Accuracy-cost reading:** the FP32/FP64 density Linf is 1.786e-6 for HLL
  and 3.230e-6 for HLLD. Thus HLL is both faster and closer to its FP64
  baseline in this bounded comparison; this is not a general solver ranking.
- **Why median/IQR:** wall times can be skewed by operating-system scheduling,
  and five samples do not justify assuming a normal distribution. Median is
  resistant to one slow run; IQR reports the middle 50% without deleting data.
- **Boundary:** the timer includes process startup, solver execution, and final
  binary output. It answers "how long does this experiment take?" rather than
  kernel-only throughput. One workstation and one KH case do not establish
  performance portability.
- **Authority:** `experiments/week18/kh_solver_timing/summary.json`.

## How every reported metric is calculated

The full derivation, implementation path, rationale, and interpretation limits
are in `docs/week18/week18-metrics-methods-EN.md`. The concise reading guide is:

1. **Primitive fields:** pressure is reconstructed from conserved total energy
   after subtracting kinetic and magnetic energy. This makes rho, vx, By, and p
   physically interpretable comparison fields.
2. **FP32/FP64 difference:** compute the pointwise same-grid difference first.
   `L1_mean` is mean absolute difference, `L2_RMS` is root-mean-square, and
   `Linf` is the maximum absolute cell difference. FP64 is a project baseline,
   not an exact solution.
3. **ULP:** transform equal-dtype IEEE values to ordered integers and take the
   maximum integer distance. `0 ULP` means bit-for-bit equality; ULP is not a
   physical norm and is not used across FP32/FP64 formats.
4. **MCA spread:** calculate unbiased sample standard deviation at every cell,
   then take its spatial maximum. The per-cell-first order prevents a spatial
   average from cancelling local stochastic sensitivity.
5. **MCA SNR:** mean absolute sample-mean field divided by mean per-cell sample
   standard deviation. It measures numerical signal relative to stochastic
   arithmetic variability, not physical turbulence noise.
6. **p24/p53 and HLLD/HLL ratios:** divide like-for-like spreads with all other
   settings fixed. Their log10 gives decimal orders of magnitude; it is not
   automatically the number of physically correct digits lost.
7. **Wall time:** exclude one warm-up, retain all five measured runs, report
   median and IQR=Q75-Q25. FP32 speed-up is `median(FP64)/median(FP32)`;
   HLLD cost is `median(HLLD)/median(HLL)` at fixed precision.
8. **Physical-state gate:** all values finite, minimum density positive, and
   pressure reconstructed from the conserved state positive. Passing makes a
   run admissible for analysis but does not prove accuracy.
9. **divB:** centred interior finite-difference divergence; report mean and
   maximum absolute value. It checks the discrete magnetic constraint, not
   precision error.
10. **Gate pass:** logical conjunction of matrix completeness, successful
    execution, physical checks, diagnostics, and declared thresholds. It never
    widens the separate claim boundary.

---

## What we can tell the supervisor (and what we won't)

**Can say:**

- Precision is the dominant observed numerical axis in the current Report 2
  packets; compiler and branch variations are secondary.
- For covered HLL Brio-Wu and Orszag-Tang cases, CPU and GPU outputs are
  bit-exact within the same precision. Five repetitions give robust 2D median
  speed-ups of 6.17x in fp64 and 5.92x in fp32.
- Orszag-Tang and Kelvin-Helmholtz remain bit-exact across 1, 2, 4, and 8
  OpenMP threads in both precisions.
- Kelvin-Helmholtz fp32/fp64 differences are finite and small across CFL
  0.2-0.8, but vary non-monotonically; HLLD is larger than HLL at every tested
  CFL in this bounded experiment.
- The temporal-divergence experiment produced a valid negative result: the
  planned Orszag-Tang-greater-than-Brio-Wu ordering was not observed.
- The 256^2-versus-512^2 OT and KH gates pass as engineering sensitivity
  checks.
- The CSC native-Verificarlo smoke completed all four reduced p53/p24 blocks;
  p24/p53 spread differs by 8.43-8.63 decades and matched deterministic runs
  corroborate the same error scale.
- On KH 256^2, five-repeat CPU timing gives FP32 speed-ups of 1.181x (HLL)
  and 1.154x (HLLD); HLLD costs 14.7%-17.3% more than HLL. All 20
  measured repeat outputs are 0 ULP within their solver/precision group.

**Won't say:**

- No claim of a formal Lyapunov exponent, physical instability rate, temporal
  convergence order, or asymptotic spatial convergence.
- No claim that HLLD is generally less accurate or less stable than HLL.
- No general GPU claim beyond the covered HLL cases and this workstation.
- No MPI reproducibility claim.
- No full Kelvin-Helmholtz MCA noise-floor conclusion: full
  **256^2, t=1.0, N=30 remains unclaimed** until CSC completion.

---

## Current problems, impact, and decisions

| Problem | Evidence now | Impact on Report 2 | Decision |
|---|---|---|---|
| Full KH MCA is incomplete | CSC has completed the 64^2, t=0.05, N=4 native-Verificarlo smoke; the full 256^2, t=1.0, N=30 four-block packet is not yet present | The full KH stochastic-noise conclusion remains unclaimed | Retrieve all HLL/HLLD x p53/p24 summaries and promote the result only after the combined gate passes |
| MCA runtime is expensive | Quad MCA costs 24.0 s/step versus 0.0575 s/step in the measured short run, about 417x overhead | A sequential full matrix cannot be treated like a normal solver sweep | Run 30 samples concurrently with 32 workers and split p53/p24 into separate Slurm tasks under the 6 h cap |
| The faster backend cannot represent p24 | `mca_int` rejects custom binary64 precision 24 | Mixing quad p24 with MCA-int p53 would confound backend and precision | Use the quad backend for both p53 and p24; retain MCA-int only for separate p53-only studies |
| N=4 is statistically weak | p24/p53 separation is large and consistent, but each CSC smoke block has four samples | Direction and toolchain operation are supported; tight confidence intervals and strong solver ranking are not | Use the smoke as validation evidence and add bootstrap/confidence intervals after N=30 samples return |
| OT/HLLD has an unresolved high-resolution stability boundary | Exploratory OT/HLLD/FP64 512^2 runs produced negative pressure at CFL 0.4 and 0.2 | This prevents using the exploratory HLLD resolution ladder as convergence evidence | Keep it outside the headline KH result and run a dedicated failure-time/positivity diagnosis before making any HLLD stability claim |
| FP64 is not an exact solution | FP32 differences are measured against the project FP64 baseline | Precision sensitivity cannot be called absolute physical error | Use “difference from FP64 baseline” consistently and keep exact-solution claims excluded |
| Two resolutions are insufficient for asymptotic convergence | The committed OT/KH gate compares 256^2 with 512^2 | The gate is an engineering sensitivity check only | Do not report a formal convergence order from this pair |
| Historical L1 conventions differ | Some deterministic packets use `sum*dx`; newer 256/512 gates use mean-normalised L1/RMS | L1 values from different packet families cannot be pooled directly | State the convention explicitly and use same-grid Linf for cross-packet headline comparisons |
| Performance scope is narrow | KH timing covers one workstation, CPU, one thread, one grid/case; FP32 speed-up is 1.154-1.181x | Results do not establish portable CPU/GPU or cross-machine performance | Report this as a bounded end-to-end timing result; leave multi-machine and HLLD/KH GPU timing as future work |
| The original temporal ordering was not observed | Fixed-window fits did not show OT growing faster than Brio-Wu | The planned hypothesis is unsupported | Retain it as a negative result rather than changing the fit window or removing the experiment |
| CSC code and evidence still need integration | Native-runner, timeout, backend, and partial-summary changes are retained in the CSC diff/findings bundle while the local worktree has overlapping changes | Blind patch application risks losing local or remote work | Integrate changes file by file, run the full tests, then merge the code and evidence packets deliberately |

The main reporting consequence is simple: **the deterministic, timing, hardware,
thread, CFL, and reduced CSC smoke conclusions can be presented within their
stated bounds; the full KH MCA and OT/HLLD high-resolution stability conclusions
cannot yet be promoted.**

---

## Next steps

1. **Monitor and retrieve the submitted full CSC chain.** Jobs 16440-16442 were
   submitted for the four full HLL/HLLD x p53/p24 blocks, packet generation,
   and W17 synthesis. The native runner uses 30 concurrent samples per block;
   do not resubmit the obsolete Apptainer workflow.
2. **Promote KH only after the full gate passes.** Both solvers must contain
   completed p53 and p24 N=30 blocks before the W17 synthesis and paper wording
   are regenerated. The N=4 smoke remains explicitly reduced-scope evidence.
3. **Add uncertainty once N=30 raw samples return.** Report confidence or
   bootstrap intervals for spread/SNR and the HLLD/HLL ratio; N=4 is too small
   for a strong statistical ranking.
4. **Prioritise synthesis over more local sweeps.** The matched deterministic
   experiment is complete. Additional local CFL, thread, or generic resolution
   sweeps have lower report value than closing the full MCA gate and updating
   the precision-versus-cost Pareto discussion.
5. **Keep the negative result visible.** Report the fixed-window temporal fit
   exactly as measured and put formal exponent estimation and MPI ordering in
   future work.

---

## References

- Brio, M., and Wu, C. C. (1988). *Journal of Computational Physics*, 75,
  400. DOI `10.1016/0021-9991(88)90120-9`.
- Orszag, S. A., and Tang, C.-M. (1979). *Journal of Fluid Mechanics*, 90,
  129.
- Dedner, A., et al. (2002). *Journal of Computational Physics*, 175, 645.
  DOI `10.1006/jcph.2001.6961`.
- Miyoshi, T., and Kusano, K. (2005). *Journal of Computational Physics*,
  208, 315. HLLD approximate Riemann solver.
- McNally, C. P., Lyra, W., and Passy, J.-C. (2012). *The Astrophysical
  Journal Supplement Series*, 201, 18. Kelvin-Helmholtz benchmark and
  reproducibility context.
- Denis, C., Castro, P., and Petit, E. (2016). Verificarlo: Monte Carlo
  Arithmetic for evaluating floating-point precision.

