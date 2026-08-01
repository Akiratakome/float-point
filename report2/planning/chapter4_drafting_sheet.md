# Chapter 4 drafting sheet

Internal preflight record for `chapter4_writing_plan.md`. This is not manuscript
prose. Report 1 Chapters 5 and 6 were used only as a voice/structure reference;
Report 1 Chapter 4 was used only for reference-strategy terminology.

| Section | Named evidence | Reported values | Baseline and scope | Claim boundary |
|---|---|---|---|---|
| 4.1 | Chapter 3 reference hierarchy | none | local property -> numerical reference -> device consistency -> 2D cases | no aggregate “all passed” claim |
| 4.2 | Figure 4.1(a) | density mean $L_1$: 0.01481 -> 0.005642; $L_2$: 0.03642 -> 0.01923 | $N=200,400,800$ against aligned, block-averaged $N=8000$ fp64 Brio--Wu reference | numerical reference, not exact solution or precision claim |
| 4.3 | Figure 4.1(b) and 2D Brio--Wu embedding | transverse maximum 0; mean/max density difference $3.550\times10^{-4}$/$7.034\times10^{-3}$; terminal `divB_max` 3.030/0.2678/0.8429 | $800\times4$ embedding; periodic disturbance at $t=0.5$, $c_r=0/0.18/0.36$ | $c_r=0.18$ is smaller only in this sweep, not globally optimal |
| 4.4 | Table 4.1 | four rows: matched steps, 0 ULP, absolute $L_\infty=0$ | HLL Brio--Wu/OT, fp64/fp32, saved local CPU/GPU outputs | excludes HLLD, KH, GPU MCA, portability and timing conclusions |
| 4.5 | Figure 4.2(a) | HLL `divB_mean` 0.1364 -> 0.1036 and `divB_max` 1.734 -> 7.729; HLL observed $p=0.639$; HLLD fp32/fp64 $p=0.846$; HLLD fp64 $512^2$: 3277 steps, $\rho_{\min}=1.098$, $p_{\min}=0.380$; audited HLL 256--512 pair has `mass_rel=0` | OT, $128^2/256^2/512^2$; 24/24 runs and 8/8 three-grid groups; HLL CFL 0.4, HLLD CFL 0.2 | morphology is qualitative; no exact-state accuracy or cross-solver ranking claim |
| 4.6 | Figure 4.2(a); independent Lecoanet packet | KH HLL `divB_mean` $6.877\times10^{-5}$ -> $2.305\times10^{-5}$ and `divB_max` $6.029\times10^{-4}$ -> $9.236\times10^{-4}$; HLLD fp64 mean $2.747\times10^{-4}$ -> $3.479\times10^{-5}$ and maximum $9.023\times10^{-3}$ -> $5.149\times10^{-3}$; audited HLL 256--512 pair has `mass_rel=0`; observed $p=0.919$ and 1.436--1.442; growth 2.193, $R^2=0.9899$, 32.0% low | project-defined MHD KH self-refinement; separate B=0 $128\times256$ early-time check | mean and maximum are separate diagnostics; no solver ranking or nonlinear Lecoanet reference reproduction |
| 4.7 | Figure/table boundaries above | 24/24 runs; 8/8 complete groups | audited mean/area metrics and unaffected $L_\infty$ only | no exact 2D error, asymptotic order, general hardware equivalence or untested coverage |

Skill sequence: `scientific-writing-duke` + `academic-english-style` for the
draft; `editing-academic-prose` for the structural revision; then
`avoiding-ai-flavor` as a separate acceptance pass. `report1-context` is not
loaded for Report 2.

Execution note (2026-07-28): the local fallback count is approximately 1,150
words including the generated table and captions. MiKTeX `texcount` could not
run because the local Perl engine is absent, so the controlling Overleaf count
remains an author/release check.
