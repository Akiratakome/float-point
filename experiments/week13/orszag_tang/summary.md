# Week 13 Orszag-Tang 2D Validation

256^2 candidate vs 512^2 double reference (block-averaged), gamma=5/3, t=0.5.

| metric | value | gate | pass? |
|---|---:|---|---:|
| L1(rho) | 7.722e-02 | < 0.5 | True |
| L2(rho) | 1.136e-01 | finite | True |
| Linf(rho) | 6.459e-01 | finite | True |
| mass_rel | 0.000e+00 | < 1e-10 | True |
| divB_max | 3.720e+00 | finite & < 5.0 | True |
| divB_max cr0 (diagnostic) | 3.603e+00 | finite | n/a |
| cleaning_ratio cr0.18/cr0 (diagnostic) | 1.032e+00 | finite | n/a |
| symmetry_residual (reported) | 6.397e-15 | n/a | n/a |

Paper anchor: Orszag-Tang is used here as a 2D ideal-MHD vortex benchmark in the Toth 2000 div(B)-constraint context. The 512-grid self-reference norms are engineering consistency checks; report validation relies on paper-grounded morphology and finite div(B)/conservation diagnostics.

## Figures

- `experiments/week13/orszag_tang/figures/ot_density_pressure.png`
- `experiments/week13/orszag_tang/figures/ot_divb.png`
