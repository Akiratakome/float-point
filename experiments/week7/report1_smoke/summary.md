# Matrix Summary Report

## Runs

| name | precision | build | nx | ny | t_end | total_s | integral_min | integral_max |
|---|---|---|---:|---:|---:|---:|---:|---:|
| sod-cpu-double-o2-ieee-leq | double | cpu-double-O2-ieee-leq | 200 | 1 | 0.25 | 0.0542764 | 0.0 | 1.3750000000000002 |
| sod-cpu-float-o2-ieee-leq | float | cpu-float-O2-ieee-leq | 200 | 1 | 0.25 | 0.0944699 | 0.0 | 1.3750000825151776 |
| stationary-contact-cpu-double-o2-ieee-leq | double | cpu-double-O2-ieee-leq | 200 | 1 | 0.5 | 0.0142144 | 0.0 | 2.5000000000000004 |
| lw3-cpu-double-o2-ieee-leq | double | cpu-double-O2-ieee-leq | 200 | 200 | 0.3 | 0.194991 | 0.1341063034931487 | 2.255677266652683 |
| lw3-cpu-float-o2-ieee-leq | float | cpu-float-O2-ieee-leq | 200 | 200 | 0.30000001192092896 | 0.506345 | 0.13410624774639815 | 2.2556772166709322 |

## Pairs

| pair_label | left | right | l1 | linf | ulp_max | philip_ratio |
|---|---|---|---:|---:|---:|---:|
| sod-cpu-o2-ieee-leq | sod-cpu-double-o2-ieee-leq | sod-cpu-float-o2-ieee-leq | 8.743340e-08 | 1.064865e-06 | n/a | n/a |
| lw3-cpu-o2-ieee-leq | lw3-cpu-double-o2-ieee-leq | lw3-cpu-float-o2-ieee-leq | 2.584873e-07 | 1.317301e-05 | n/a | n/a |
