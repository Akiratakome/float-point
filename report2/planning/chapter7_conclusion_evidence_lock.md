# Chapter 7 Conclusion Evidence Lock

This table is the hard gate for drafting Chapter 7 and the abstract. It follows
the status and claim boundaries in
`docs/experiment_logs/report2_evidence_map.md` (last audited 2026-07-31).
Chapter 7 may synthesise the rows below but may not add a result, combine
unmatched scopes, or promote provisional evidence.

| Allowed claim | Exact summary/figure | Required metric | Scope sentence | Excluded generalisation |
|---|---|---|---|---|
| The implemented ideal-MHD paths are sufficiently validated for the controlled comparisons used in this report. | `experiments/week12/brio_wu_1d/summary.md`; `experiments/week12/mhd_2d/brio_wu_2d/summary.md`; `experiments/week12/mhd_2d/divb_clean/summary.md`; `experiments/week18/resolution_ladder/summary.md`; Chapter 4 Figure `fig:ch4-validation-refinement-glm`, Figure `fig:ch4-resolution-precision` and Table `tab:ch4-cpu-gpu`. | Brio--Wu numerical-reference L1/L2 trend; transverse-invariance and GLM-divergence gates; 24/24 three-resolution completions; zero maximum ULP in the covered CPU/GPU validation pairs. | This validation applies to the declared Brio--Wu, Orszag--Tang and Kelvin--Helmholtz configurations and to the bounded HLL CUDA cases tested. | Universal correctness; an exact two-dimensional solution; asymptotic convergence; HLLD-on-GPU or KH-on-GPU validation. |
| Matched saved-state comparisons distinguish detectable precision and selected build-semantic responses from null repeat, covered device and requested-thread comparisons. | `experiments/week18/euler_mhd_cross_system/summary.md`; `experiments/week20/brio_wu_build_semantics/summary.md`; `experiments/week18/supplemental/summary.md`; Chapter 5 Figure `fig:ch5-cross-system`, Section `sec:ch5-build-sensitivity`, Figure `fig:ch5-hardware` and Section `sec:ch5-thread-cfl`. | Matched density mean-relative L1/Linf or absolute norms for precision/build pairs; maximum ULP and absolute drift for repeat, CPU/GPU and requested-thread pairs. | The comparison is restricted to the named cases, baselines, one MSVC build matrix, the validated HLL device rows and the current serial-sweep MHD implementation. | A universal axis ranking; compiler-wide behaviour; hardware independence; parallel OpenMP or MPI reproducibility; accuracy inferred from cross-variant discrepancy. |
| In all 12 resolution-ladder cells, the density mean-L1 fp32--fp64 discrepancy is below 3% of the matched fp64 finest adjacent-grid refinement scale. | `experiments/week18/resolution_ladder/summary.md`; Chapter 5 Figure `fig:ch5-precision-refinement`. | $S_N=D_N/E^{64}_{256,512}$, spanning $4.95\times10^{-6}$ to $2.76\times10^{-2}$ for the 12 matched cells. | The ratio is a within-case, within-solver engineering context for OT/KH at the declared resolutions, final times and solver-specific CFL values. | Exact error; fp32 adequacy; asymptotic convergence; comparison of solver accuracy; transfer to other cases or grids. |
| GPU timing is workload-dependent on the tested workstation: it is slower for Brio--Wu but faster for the $256^2$ Orszag--Tang workload, while saved same-precision states remain identical in the covered rows. | `experiments/week18/supplemental/summary.md`; Chapter 5 Figure `fig:ch5-hardware`. | Five-repeat median CPU/GPU wall-time ratio and IQR; ratios 0.510/0.488 for Brio--Wu fp64/fp32 and 6.174/5.925 for OT; maximum ULP $=0$. | These subprocess timings cover HLL Brio--Wu and OT in fp64/fp32 on one workstation and include required output. | General GPU speed-up; kernel-only performance; other devices, HLLD, KH or cross-machine portability. |
| The predeclared Orszag--Tang log-linear discrepancy-growth contrast is not supported in the fixed window. | `experiments/week15/mhd_temporal_divergence/summary.md`; Chapter 5 Figure `fig:ch5-temporal`. | OT mean-L1/Linf fixed-window $R^2=0.0073/0.0006$ from 25 aligned pairs; Brio--Wu values are reported only within its own time coordinate. | This is a negative result for the declared fp32--fp64 engineering fit and observation window. | A formal Lyapunov exponent; physical instability rate; a general OT/KH ordering; explanatory use of the OT fitted slope. |
| Same-scope deterministic and MCA comparison is available for Brio--Wu HLL and HLLD, whereas OT and KH MCA remain separately scoped. | `experiments/week18/precision_mca_gate/summary.md`; `experiments/week15/brio_wu_precision_pilot_p1/summary.md`; `experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.md`; Chapter 5 Table `tab:ch5-mca-primary`. | Brio--Wu $N=800$, $t=0.1$, N=30 p53/p24 blocks; p24 maximum spreads are 2.12 and 2.46 times the deterministic fp32--fp64 Linf values for HLL/HLLD. | The comparison provides an order-of-magnitude stochastic context only for the matched Brio--Wu rows. | Identifying virtual p24 with IEEE fp32; merging OT $256^2,t=0.5$ deterministic and $64^2,t=0.05$ MCA; full-scale KH MCA; solver ranking. |

## Headline selection for Chapter 7

Use three synthesis findings rather than reproducing all six rows:

1. Validation establishes the boundary within which matched sensitivity can be
   interpreted.
2. Controlled comparisons separate non-zero precision/build responses from
   null repeat/device/thread saved-state comparisons, while timing remains
   workload-dependent.
3. Resolution and time provide essential context: the 12 mean-L1 precision
   differences remain below 3% of the matched refinement scale, and the planned
   Orszag--Tang log-linear temporal contrast is not observed.

The Brio--Wu MCA row may support the third finding, but it must not become a
cross-case stochastic headline.

## Future-work lock

Future work must follow directly from a stated limitation and name a concrete
experiment:

1. Compare saved density and magnetic fields with an independent
   two-dimensional ideal-MHD code under matched equations, initial conditions,
   grids and final times. Use declared mean-$L_1$/$L_\infty$ and divergence
   diagnostics; treat the external calculation as a numerical comparator, not
   an exact solution.
2. Repeat the matched Brio--Wu/Orszag--Tang timing mini-matrix on a second
   machine with matched effective semantics; separately repeat the one-axis
   build matrix with a second toolchain. This keeps hardware and compiler
   portability as distinct tests.
3. Run deterministic and N=30 MCA comparisons at the same grid and final time
   for Orszag--Tang and Kelvin--Helmholtz before making cross-case stochastic
   claims.
4. Add an actual parallel MHD work-sharing or MPI path, then test saved-state
   sensitivity across thread/rank counts and reduction orderings.

HLLD-on-GPU and KH-on-GPU remain valid extensions, but they are lower-priority
coverage work unless Chapter 7 explicitly ties them to the bounded device
limitation. No future-work item may be written as though its result already
exists.

## Explicit exclusions

- Do not use `experiments/week17/report2_synthesis/figures/axis_ranking.png`.
- Do not headline provisional OT deterministic/MCA combinations or full-scale
  KH MCA.
- Do not convert discrepancy into exact error or claim fp32 adequacy.
- Do not claim asymptotic convergence, formal Lyapunov behaviour, a universal
  solver/hardware ranking, or cross-machine portability.
