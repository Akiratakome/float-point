# Week 7 Supervisor Response

## Criterion for the regime label

The current A4 table labels a row using

`margin = s_worst_q05 - s_req(N)`.

Here `s_req(N) = -log10(||E_trunc(N)||_1) + 1`, so it is a truncation-anchored target for how many significant digits the FP path needs to avoid dominating the grid-resolution error. A negative margin means the 5th-percentile worst-cell significant-digit estimate is below that target.

For Report 1, describe this first as a precision-adequacy margin before calling it round-off limited. The phrase round-off limited can be misleading when the same row also has truncation-dominated bulk error. The safer sentence is: "at this resolution, the significant-digit margin is below the truncation anchored target, while the bulk L1 error remains dominated by truncation."

No code or output-format change is required for this terminology clarification. Future outputs may add an explicit `precision_margin` column if needed, but the existing `regime` column should remain unchanged for traceability.

## Degenerate denominators

Ratio pass/fail metrics such as Philip `fmd/d_err` exclude any row whose
denominator is zero or too small to support a meaningful ratio. If a script
needs a default tolerance, use a scale-aware guard such as
`denominator <= max(1e-300, 1e-12 * reference_scale)`; otherwise mark the row
degenerate. When the ratio denominator is zero, `gate_status` should be
excluded/degenerate regardless of variable.

Per-cell relative significant-digit and LoSoS reliability metrics use a
separate noise-floor policy. Define `field_scale` as the domain max absolute
mean of that variable over non-ghost cells for the run, or 1.0 if that max is
zero or nonfinite. Define `rel_floor=1e-12` unless an experiment-specific
value is recorded. A cell is near-zero when
`abs(mean_cell) <= max(abs_floor, rel_floor * field_scale)`. Near-zero cells
or variables are diagnostic only, not pass/fail evidence. Suggested
`abs_floor` defaults are `1e-14` for double-like p53 and `1e-6` for p24/float,
unless an experiment-specific floor is recorded.

Density is positive and is therefore generally the least degenerate variable.
However, the stationary-contact exact-density denominator can still be zero in
the Philip metric, so stationary-contact density should be reported as an
absolute or sensitivity diagnostic rather than ratio pass/fail evidence in
that case. Velocity relative significant-digit metrics remain diagnostic when
their mean is near the noise floor.

Future JSON summaries may add explicit `excluded_reason` fields for these
cases if that becomes useful. Existing Markdown columns should remain stable;
any new columns should be appended at the end.

## Why Rusanov can look cleaner

Rusanov is more diffusive than HLLC. Extra dissipation smooths sharp gradients
and reduces local amplification of round-off noise near shocks and contacts.
The plausible mechanism is not more accurate physics; it damps high-frequency
structure before EOS pressure calculation and reconstruction stages can amplify
small perturbations.

This is an interpretation of measured data, not a solver recommendation: HLLC
remains sharper and generally more accurate in these validation tests.

Supporting rho-only derived check for LW Config 3 at 200^2, computed from:

- `experiments/week4/metrics/a4_snr_with_float.csv`
- `experiments/week4/metrics/a4_losos_with_float.csv`
- `experiments/week4/metrics/s_req_lw_config3_200.csv`

| Precision | sigma_FP_L1 HLLC | sigma_FP_L1 Rusanov | sigma ratio HLLC/Rusanov | truncation penalty Rusanov/HLLC | s_worst_q05 HLLC | s_worst_q05 Rusanov | digit delta Rusanov-HLLC |
|---|---:|---:|---:|---:|---:|---:|---:|
| p53 | 5.216e-11 | 2.278e-11 | 2.29 | 1.51 | 1.542 | 1.230 | -0.312 |
| p24-real-float | 2.956e-02 | 8.199e-03 | 3.60 | 1.51 | 1.542 | 1.230 | -0.312 |

The truncation penalty uses the rho `mu_trunc_l1` ratio from
`s_req_lw_config3_200.csv`; the same ratio is obtained from `E_trunc` because
both values share the same reference normalization. A copy of this derived
calculation is saved in `experiments/week7/rusanov_noise/summary.csv`.

| Evidence | Interpretation |
|---|---|
| Rusanov has larger deterministic truncation error than HLLC: rho `mu_trunc_l1` is 418.0 vs 277.3, a 1.51x penalty. | Cleaner noise is bought by diffusivity, not by a more accurate physical solution. |
| Rusanov has lower `sigma_FP_L1` in the LW3 rho rows: 2.278e-11 vs 5.216e-11 at p53, and 8.199e-03 vs 2.956e-02 at p24-real-float. | Round-off variance is damped by the smoother numerical state. |
| C2 shows pressure and other variables are most sensitive near discontinuities; on Sod, Rusanov is about 0.2 significant digits cleaner than HLLC. | EOS subtraction remains a likely amplification point, and smoothing discontinuities can reduce the measured variance before EOS and reconstruction effects grow. |
| Stationary-contact `u` in C2 is degenerate/noise-floor: the sign of the real-vs-double gap flips between HLLC and Rusanov and should not be overread. | The cleaner-Rusanov statement should be based on non-degenerate rho/p and Sod-style flow, not near-zero relative metrics. |
| Rusanov fails or degrades where excessive diffusion is harmful, including the earlier near-vacuum Toro 2 failure and smeared stationary-contact density. | Noise reduction is not general superiority; it is a trade-off against sharp contact and shock resolution. |

## Task 4 - Precision Metrics Inform Drift Results

The Week 7 drift artefact is a synchronized final-state smoke, not a fitted
time-series result. Each reported pair has one matched final time, so the
growth rate is listed as `not fitted`; no lambda value should be inferred
until synchronized multi-time checkpoints or multiple exact-final-time samples
are available.

Precision-adequacy metrics answer a different question from the drift smoke.
The drift L1 value says whether two outputs differ at the measured time. The
precision-adequacy margin and `sigma_FP_L1` say whether that difference is
important relative to the truncation target, and whether the emitted FP noise
is plausible as a controlling error source. The degenerate denominator policy
still applies: Philip ratios are excluded when the reference denominator is
zero or unavailable, so CPU/GPU strict rows with no exact reference should not
be turned into pass/fail ratio evidence.

| case | pair | precision/build delta | L1 drift at final time | fitted lambda | sigma_FP_L1 or Philip ratio | interpretation |
|---|---|---|---:|---|---|---|
| sod | CPU strict vs GPU strict | double | 0.000000e+00 | not fitted | Philip ratio n/a; exact reference unavailable | Week 6 strict device path is bitwise identical for this smoke row, so the GPU path is not yet evidence for reproducibility divergence. |
| sod | CPU strict vs GPU strict | float | 0.000000e+00 | not fitted | Philip ratio n/a; exact reference unavailable | Same conclusion at p24/float: strict CPU/GPU execution has zero measured final-state drift in the available Week 6 artefact. |
| lw3 | CPU strict vs GPU strict | double | 0.000000e+00 | not fitted | Philip ratio n/a; exact reference unavailable | The 2D strict device smoke is also zero drift, so larger future drift should be sought first in branch rules, compiler flags, fast-math, or longer synchronized windows. |
| lw3 | CPU strict vs GPU strict | float | 0.000000e+00 | not fitted | Philip ratio n/a; exact reference unavailable | Float strict CPU/GPU agreement keeps the Week 6 GPU path out of the current reproducibility-divergence source list. |
| sod | HLLC vs Rusanov CPU strict smoke | solver branch delta | 4.134993e-03 | not fitted | no Week 4 1D precision-adequacy summary present in this worktree | This is a scheme-difference smoke, not a hardware drift claim; the single synchronized final time checks the pipeline but cannot support growth-rate interpretation. |
| lw3 | HLLC vs Rusanov CPU strict smoke | solver branch delta | 1.229633e-02 | not fitted | p53 sigma_FP_L1 HLLC 5.216e-11, Rusanov 2.278e-11; precision-adequacy margins -1.588 and -1.722 | The solver difference is much larger than p53 emitted FP noise. The negative precision-adequacy margins explain that the delivered significant digits sit below the truncation-anchored target, while Rusanov's cleaner noise is bought with a 1.51x truncation penalty. |
| lw3 | HLLC vs Rusanov CPU strict smoke | solver branch delta with p24-real-float adequacy context | 1.229633e-02 | not fitted | p24-real-float sigma_FP_L1 HLLC 2.956e-02, Rusanov 8.199e-03; sigma ratio 3.60 | At p24-real-float, emitted FP noise is comparable to or larger than the smoke drift scale, so precision adequacy is material to interpretation rather than a cosmetic nonzero-difference report. |

The CPU/GPU strict pair has zero, or at most ULP-level, drift in the Week 6
strict smoke rows and therefore is not yet the source of reproducibility
divergence. The Week 7 Task 3 pipeline now rejects mismatched checkpoint times,
so it is ready for synchronized multi-time runs where compiler flags,
branch-rule changes, fast-math, and longer GPU/CPU windows can be tested
without mixing unequal physical times.

The important distinction for Report 1 is that precision-adequacy and Pareto
metrics explain whether observed drift matters relative to the truncation
target, not merely whether it is nonzero. A nonzero drift can be expected when
the solver branch changes from HLLC to Rusanov; a precision-adequacy deficit
then says that the available significant digits are below the
truncation-anchored demand. Conversely, the current strict CPU/GPU smoke rows
show no final-state drift, so they should be reported as reproducibility
evidence for the strict GPU path rather than as evidence of a hidden GPU
divergence mechanism.

## Task 5 - Full Pareto Example For Philip

Generated artefacts:

- `experiments/week7/pareto_full/pareto_lw3_full_logx.png`
- `experiments/week7/pareto_full/pareto_lw3_full_twopanel.png`
- `experiments/week7/pareto_full/pareto_lw3_full.csv`
- `experiments/week7/pareto_full/summary.md`

The Pareto plot demonstrates the trade-off between emitted FP noise
(`sigma_FP_L1`, x-axis) and delivered significant digits (`s_worst_q05`,
y-axis). The horizontal `s_req(N)` target marks the significant digits implied
by truncation error at the same grid resolution. This is the precision demand
that the FP path should meet if it is not to fall below the truncation-anchored
target.

Log scaling on the FP-noise axis is required because p24-real-float and p53
differ by many orders of magnitude in emitted noise. In the Week 4 A4 headline
rho rows reused here, p24-real-float moves the point far to the right while
the delivered `s_worst_q05` remains below `s_req(N)`. The two-panel output
therefore shows both the raw trade-off and the precision-adequacy margin
`s_worst_q05 - s_req(N)`.

No Verificarlo rerun was performed. The script reuses:

- `experiments/week4/metrics/a4_snr_with_float.csv`
- `experiments/week4/metrics/a4_losos_with_float.csv`
- `experiments/week4/metrics/s_req_lw_config3_200.csv`
