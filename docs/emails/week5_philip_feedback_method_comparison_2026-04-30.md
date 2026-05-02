# Float-vs-Double Regression: Method Comparison

**Date:** 2026-04-30
**Driver:** Philip's 2026-04-30 supervisor feedback.
**Status:** Decision proposal pending supervisor sign-off.

## Recommendation

Adopt Philip's metric as the canonical float-regression signal, and keep the
legacy per-side ratio as a secondary diagnostic in the same summary.

## Metrics Compared

Legacy:

`||sim_float - exact||_1 / ||sim_double - exact||_1`

Philip:

`||sim_float - sim_double||_1 / ||sim_double - exact||_1`

For 2D, `exact` is approximated by the existing `reference_800.bin`
downsampled to the candidate grid.

## Numbers: 1D Toro Suite at N=800

| test | legacy L1_rho ratio | Philip L1_rho ratio | comment |
|------|--------------------:|--------------------:|---------|
| sod | 1.000005e+00 | 1.060036e-04 | Legacy is dominated by discretization error. |
| toro2 | 9.998672e-01 | 2.347006e-04 | Largest non-contact rho Philip ratio in 1D. |
| toro3 | 9.999988e-01 | 1.364064e-05 | Philip exposes the precision delta hidden by legacy. |
| toro4 | 1.000001e+00 | 7.181764e-06 | Smallest non-contact rho Philip ratio. |
| toro5 | 1.000004e+00 | 3.913105e-05 | Legacy remains effectively 1. |
| stationary_contact | 1.000000e+00 | 1.000000e+00 | Degenerate denominator: double-vs-exact rho error is zero, so this case should be treated separately. |

## Numbers: 2D Liska-Wendroff Config 3

| resolution | legacy double L1_rho | legacy float L1_rho | Philip L1_rho ratio | comment |
|------------|---------------------:|--------------------:|--------------------:|---------|
| 200 | 6.878316e-03 | 6.878377e-03 | 5.120465e-05 | Float and double have almost identical ref error, but nonzero direct drift. |
| 400 | 3.304289e-03 | 3.304381e-03 | 1.386519e-04 | Ratio increases with resolution as truncation error shrinks. |

## Why Prefer Philip's Metric

1. It isolates the quantity the regression is meant to measure: the arithmetic
   precision difference between float and double.
2. It avoids the legacy failure mode where float and double both track the same
   discretization error, making the ratio round to approximately 1.
3. It reuses the same trusted reference already used by the old metric; only
   the numerator changes.

## Why Keep the Legacy Metric

The legacy metric still detects a different failure mode: one precision build
could regress in convergence behavior while the direct float-vs-double
difference remains small. It is cheap to keep and useful as a secondary check.

## Open Questions for Philip

- Should stationary-contact-style zero-denominator cases be excluded from the
  canonical Philip pass/fail table or reported with an explicit degenerate-case
  marker?
- For 2D shock-dominated cases, should we also report an Linf Philip variant to
  catch localized cell-level divergence?
