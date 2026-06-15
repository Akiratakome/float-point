# Mid-term presentation — execution plan

**Talk:** Effect of Floating-Point Precision and Hardware on HRSC Schemes
**Author:** Yudong Tang · **Supervisor:** Dr. Philip Blakely · **Date:** 05.06.2026
**Limit:** 10 min, strictly timed · 10 frames + backups · Beamer (MPhil template)

## Design
10-frame deck on `BeamerMPhilTemplate`, ordered on Philip's running sheet:
setup → validation → baseline-required findings → extensions → conclusions.
Plain academic English script (~1,450 words), embedded as `\note{}` and in `script.md`.
One message + one figure per slide (timing is tight: 10 slides ≈ 10 min).

## Slide map  (13 main + 5 backup; figures on results, basics are text)
1.  Title
2.  Background / why precision + hardware + reproducibility   [text]
3.  Numerical method (FV + MUSCL–Hancock + HLLC + Rusanov)    [text]
4.  Floating-point details + how it's tested                 [text]
5.  Implementation pipeline · `ch4_architecture_workflow`     [figure, 15s glance]
6.  Validation 1D · `sod_comparison`                         [text+fig]
7.  Validation 2D · `lw3_n400_comparison`                    [text+fig]
    — baseline-required findings —
8.  fp32 vs fp64 · `fp32_fp64_density_differences_2d_pair`    [text+fig]
9.  CPU vs GPU 0/0/0; fast-math breaks it · `drift_timeseries_l1_native` [text+fig]
10. Solver vs the rest (hierarchy) · `density_hllc_vs_rusanov_200` [text+fig]
    — extensions (thesis highlights) —
11. Toro-2 `<` vs `≤` branch flip · `appendix_toro2_branch_trace` [text+fig]
12. Verificarlo region maps · `region_noise_to_error_ratio_precision_grid_rho` [text+fig]
13. Conclusions + Report 2                                   [text]

Backup: HLLC wave fan, Toro3 1D, LoSoS quantiles, ideal-MHD seven-wave fan.

Timing: script ≈ 1301 words → ~9.0 min pure + transitions ≈ 9:50–10:00 live.
Cut valves if over 10:00: slide 10 (hierarchy) or slide 12 (Verificarlo).

## Stages — all complete
- [x] **0** Scaffold  [x] **1** Title+Background  [x] **2** Method/FP/Validation
- [x] **3** Findings  [x] **4** Extensions  [x] **5** Conclusions+backups+script
- [x] **6** Timing pass → ~9:30–9:45, in the ≥9:30 / ≤10:00 window

## Build
`cd presentation1/talk && latexmk -pdf talk.tex` (MiKTeX, local). Self-contained `figs/`.

## Risks
- 10 slides vs 10 min → one-message slides; slide 9 is the "cut to backup" valve.
- Verify each rendered frame; don't overfill.
