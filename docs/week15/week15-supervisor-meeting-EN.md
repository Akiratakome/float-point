# Week 15 Supervisor Meeting Report
> **Historical snapshot:** This dated meeting document preserves what was known
> at the time. It is not the current Report 2 status. See
> [report2_evidence_map.md](../experiment_logs/report2_evidence_map.md) for
> current evidence, supersession, and claim boundaries.

> Prepared on 9 July 2026. The figures are in `docs/week15/figures/` and use an
> academic-paper style. All numerical values have been checked against their
> respective `summary.json` files.
>
> This week, the precision study was upgraded from a smoke test to
> **report-grade evidence**. The Week 14 study covered only the one-dimensional
> Brio–Wu problem, 8 build variants, and Monte Carlo Arithmetic (MCA) with
> \(n=8\). The new study covers **both 1D Brio–Wu and 2D Orszag–Tang, both HLL
> and HLLD solvers, the full set of 24 build variants, and MCA with \(N=30\)**,
> all on the CPU.

---

## Executive summary

This week, three of the four main axes in the systematic precision study were
developed into report-grade evidence: numerical precision, compiler
optimisation and fast math, and solver branch inequalities. These axes were
tested in both one and two dimensions with two Riemann solvers, producing six
publication-style figures. Every evidence packet passed its hard G0 anchor
gate, which checks that the reference run reproduces its validated baseline.

The engineering workflow also improved substantially. Verificarlo sampling was
parallelised across 16 containers instead of running serially on one core, and
an intermittent robustness problem in p24 sampling was fixed. The only main
axis not yet covered is hardware, specifically CPU versus GPU. The GPU MHD
design and implementation plan are complete, and CUDA installation is in
progress.

---

## Work completed this week

1. **Expanded the deterministic precision matrix to all 24 variants.** Each
   test case now covers
   `{float,double} × {O2,O3,Ofast} × {ieee,fastmath} × {leq,strict}`, compared
   pointwise with the double-precision baseline. Week 14 covered only 8
   variants.
2. **Increased random-rounding sampling to \(N=30\).** The MCA study was
   upgraded from the Week 14 smoke test at \(n=8\) to \(N=30\), providing a
   more stable estimate of how many significant digits the simulation actually
   retains.
3. **Covered both dimensions and both solvers.** The study now includes the 1D
   Brio–Wu and 2D Orszag–Tang problems with both HLL and HLLD, giving four
   report-grade evidence packets. All four passed the G0 gate.
4. **Improved the experiment harness.** MCA sampling now supports `--jobs 16`
   rather than running serially on one core. I also diagnosed and fixed an
   intermittent p24 stall: under low precision, rounding could occasionally
   drive a CFL time step close to zero. The retry allowance was increased from
   3 to 6.
5. **Prepared the GPU MHD work.** An HLL-first design specification and a
   ten-task implementation plan are ready. CUDA installation has begun so that
   the hardware axis can be added next.

---

## Six figures: how to read them and what they show

For each figure, I first give the main conclusion and then explain how to read
the evidence.

### Figure A — Which axis matters most? `figures/fig1_precision_axis.png`

- **Main conclusion:** **Precision overwhelmingly dominates.** In both 1D and
  2D, changing from double to float creates a clear step of approximately 8–9
  orders of magnitude.
- **How to read the figure:** Panel (a) shows Brio–Wu 1D and panel (b) shows
  Orszag–Tang 2D. The vertical axis is the \(L_\infty(\rho)\) difference from
  the double-precision baseline on a logarithmic scale. The horizontal axis
  contains the 24 variants: the 12 double variants in blue on the left and the
  12 float variants in red on the right. The double cluster lies around
  \(10^{-14}\)–\(10^{-17}\), close to machine precision; the dashed line at
  \(10^{-15}\) is a guide. The float cluster jumps to approximately \(10^{-6}\)
  in 1D and \(10^{-5}\) in 2D.
- **Interpretation boundary:** These are differences from our own
  double-precision baseline. They measure **engineering consistency**, not
  pointwise agreement with an exact solution.

### Figure B — How many significant digits remain? `figures/fig2_mca_noise_floor.png`

- **Main conclusion:** **fp64 retains approximately 15 significant digits,
  whereas fp32 retains only about 6–7.** Their noise floors differ by roughly
  nine orders of magnitude, consistently across all four evidence packets.
- **How to read the figure:** The horizontal axis contains four groups:
  Brio–Wu HLL, Brio–Wu HLLD, Orszag–Tang HLL, and Orszag–Tang HLLD. Each group
  has two bars: p53, the double-precision surrogate, in blue, and p24, the
  single-precision surrogate, in red. The logarithmic vertical axis shows the
  density spread across \(N=30\) MCA samples. All p53 results are close to
  \(10^{-15}\), while all p24 results are close to \(10^{-6}\), with a stable
  separation.
- **What this establishes:** MCA measures the number of trustworthy digits
  delivered by the simulation without requiring a reference solution. This is
  the most distinctive evidence for Report 2: the result is now statistically
  stable at \(N=30\) and consistent across two solvers and two dimensions.
- **Independent agreement:** The p24 spread of approximately \(10^{-6}\)
  agrees closely with the deterministic float difference of approximately
  \(10^{-6}\) in Figure A. Two independent methods therefore support the same
  conclusion.

### Figure C — How large is the compiler optimisation / fast-math effect? `figures/fig3_compiler_axis.png`

- **Main conclusion:** **The compiler axis is real but secondary**, about two
  orders of magnitude smaller than the precision axis. The fast-math effect is
  also **non-monotonic**: in some variants, the measured difference is smaller
  than under strict IEEE arithmetic.
- **How to read the figure:** Panel (a) shows Brio–Wu HLLD and panel (b) shows
  Orszag–Tang HLLD, using only float variants. Blue denotes strict IEEE
  arithmetic and red denotes fast math. The Brio–Wu panel varies around
  \(1.5\)–\(1.9\times10^{-6}\), and some red bars are lower than their blue
  counterparts. The Orszag–Tang panel is nearly flat, showing that the compiler
  axis is negligible relative to the fp32 noise floor in this 2D case.
- **What this establishes:** The “\(N\) fast-math ordering flags” in the figure
  title identify automatically detected non-monotonic points: Brio–Wu has 4
  flags for HLL and 6 for HLLD, while Orszag–Tang has 0 for HLL and 4 for HLLD.
  Floating-point reassociation can naturally produce this behaviour. We report
  these points explicitly rather than silently treating them as noise. The
  five-wave HLLD fan appears more sensitive than HLL in these observations.
- **Interpretation boundary:** These are soft, non-blocking flags. They support
  a report finding of a secondary, non-monotonic compiler axis, but not a
  strong causal claim.

### Figure D — How much speed-up does fp32 provide? `figures/fig4_walltime.png`

- **Main conclusion:** **On the CPU, fp32 is only 1.06–1.34× faster than
  fp64.** Compared with a loss of approximately nine orders of magnitude in
  precision, fp32 offers a poor trade-off on the CPU.
- **How to read the figure:** The horizontal axis shows the four evidence
  packets. The vertical axis is the speed-up, defined as fp64 wall time divided
  by fp32 wall time; the dashed line at 1.0 indicates no speed-up. Absolute
  timings are printed inside the bars: approximately 0.15 s for the 1D cases
  and 27 s for the 2D cases.
- **What this establishes:** This quantifies whether float is worthwhile as a
  speed optimisation. On the CPU, the speed gain is small while the precision
  loss is substantial. The architectural throughput advantage of fp32 is more
  likely to appear on a GPU, which motivates the next stage of the study.

### Figure E — What does the 2D test case look like? `figures/fig5_ot_hll_reference_fields.png`

- **Main conclusion:** The density and pressure fields in the 2D Orszag–Tang
  calculation reproduce the characteristic vortex structures reported in the
  literature.
- **How to read the figure:** The pseudocolour panels show density and pressure
  from the double-precision reference solution at \(256^2\) and \(t=0.5\).
  They display the current sheets and vortices characteristic of the
  Orszag–Tang problem.
- **Interpretation boundary:** Orszag–Tang has no closed-form solution. This is
  a reproduction of the published **morphology**, not a claim of pointwise
  agreement with an exact solution.

### Figure F — How strongly does 2D chaotic flow amplify fp32 drift? `figures/fig6_ot_hll_fp32_drift.png`

- **Main conclusion:** **The 2D chaotic flow amplifies fp32 drift to
  approximately \(3\times10^{-3}\)** in Orszag–Tang HLLD, far above the
  approximately \(10^{-6}\) level observed in 1D. This motivates the temporal
  divergence study.
- **How to read the figure:** The logarithmic heatmaps show the absolute density
  and \(B_y\) drift in float relative to the fp64 reference. The largest
  differences are concentrated around under-resolved current sheets.
- **What this suggests:** The 2D chaotic flow appears to amplify
  precision-induced differences strongly, particularly around current sheets.
  This observation motivates the Week 16 temporal-divergence and Lyapunov-like
  analysis, which will fit
  \(\log(\mathrm{error})=\lambda t+c\). The exponent has not yet been measured.

---

## Claims supported by the current evidence

- All four evidence packets—Brio–Wu and Orszag–Tang, each with HLL and
  HLLD—passed the G0 anchor gate and produced finite, reproducible results. The
  validated anchors are 759 steps for 1D; 806 steps with
  \(\mathrm{div}B_{\max}=3.72\) for Orszag–Tang HLL; and 812 steps with
  \(\mathrm{div}B_{\max}=24.45\) for Orszag–Tang HLLD.
- Precision is the dominant axis, with a difference of approximately nine
  orders of magnitude. At \(N=30\), MCA consistently indicates approximately
  15 significant digits for fp64 and 6–7 for fp32 across both dimensions and
  both solvers.
- Compiler optimisation and fast math form a secondary axis and produce
  non-monotonic ordering flags, which have been recorded explicitly.
- On the CPU, fp32 provides only a 1.06–1.34× speed-up.
- The 2D chaotic case amplifies fp32 drift to approximately
  \(3\times10^{-3}\), motivating the planned temporal-divergence analysis.
- The experiment harness now samples MCA with 16 concurrent containers and is
  more robust to intermittent p24 stalls through the retry increase from 3 to
  6.

## Claims not yet supported

- I do not claim pointwise convergence to an exact solution. Brio–Wu and
  Orszag–Tang have been checked against published morphology only.
- I do not claim that HLLD is superior or production-ready. HLL remains the
  production default.
- There are not yet any GPU or hardware-axis results.
- The Lyapunov-like or temporal-divergence fit is planned for Week 16 and has
  not yet been completed.
- No conclusion is drawn yet for Kelvin–Helmholtz or a \(512^2\) grid.

---

## Next steps

1. **GPU MHD: complete the hardware axis.** Port HLL to the GPU first, add a
   same-precision CPU-versus-GPU ULP regression gate, and then run Brio–Wu 1D
   and Orszag–Tang 2D on the GPU. HLLD on the GPU will follow later. The design
   and implementation plan are complete, and CUDA installation is in progress.
2. **Kelvin–Helmholtz 2D.** Upgrade the second 2D MHD case, currently validated
   only by morphology, to the same 24-variant matrix and \(N=30\) MCA study.
3. **Temporal divergence and a Lyapunov-like exponent in Week 16.** Fit
   \(\log(\mathrm{error})=\lambda t+c\) for chaotic Orszag–Tang and
   Kelvin–Helmholtz flows. The approximately \(3\times10^{-3}\) drift in
   Figure F provides the starting point.

---

## References

- Brio, M., and Wu, C. C. (1988). *Journal of Computational Physics*, 75, 400.
  DOI: `10.1016/0021-9991(88)90120-9`. One-dimensional ideal-MHD shock-tube
  benchmark.
- Orszag, S. A., and Tang, C.-M. (1979). *Journal of Fluid Mechanics*, 90, 129.
  Two-dimensional MHD vortex benchmark.
- Dedner, A., et al. (2002). *Journal of Computational Physics*, 175, 645.
  DOI: `10.1006/jcph.2001.6961`. GLM divergence cleaning.
- Miyoshi, T., and Kusano, K. (2005). *Journal of Computational Physics*, 208,
  315. Five-wave HLLD solver; GPU support is future work.
- Denis, C., Castro, P., and Petit, E. (2016). Verificarlo, a Monte Carlo
  Arithmetic tool for random-rounding analysis.
