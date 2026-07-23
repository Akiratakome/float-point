# Week 16 Kelvin-Helmholtz 2D Validation

256^2 candidate vs 512^2 double reference (block-averaged), gamma=5/3, t=1.
Mode: report-grade.

| metric | value | gate | pass? |
|---|---:|---|---:|
| L1(rho) | 1.836e-03 | < 0.2 | True |
| L2(rho) | 2.249e-03 | finite | True |
| Linf(rho) | 6.376e-03 | finite | True |
| mass_rel | 0.000e+00 | < 1e-10 | True |
| divB_max | 6.714e-04 | finite & < 5.0 | True |
| divB_max cr0 (diagnostic) | 7.736e-04 | finite | n/a |
| cleaning_ratio cr0.18/cr0 (diagnostic) | 8.679e-01 | finite | n/a |
| reflect_y_residual (reported) | 6.514e-03 | n/a | n/a |
