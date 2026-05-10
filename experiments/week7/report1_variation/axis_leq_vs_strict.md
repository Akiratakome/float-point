# Matrix Summary Report

## Runs

| name | precision | build | nx | ny | t_end | total_s | integral_min | integral_max |
|---|---|---|---:|---:|---:|---:|---:|---:|
| sod-cpu-double-O2-ieee-leq-hllc | double | cpu-double-O2-ieee-leq | 200 | 1 | 0.25 | 0.00986804 | 0.0 | 1.3750000000000002 |
| sod-cpu-double-O3-ieee-leq-hllc | double | cpu-double-O3-ieee-leq | 200 | 1 | 0.25 | 0.00938632 | 0.0 | 1.3750000000000002 |
| sod-cpu-double-Ofast-fastmath-leq-hllc | double | cpu-double-Ofast-fastmath-leq | 200 | 1 | 0.25 | 0.00919854 | 0.0 | 1.3750000000000002 |
| sod-cpu-double-O2-ieee-strict-hllc | double | cpu-double-O2-ieee-strict | 200 | 1 | 0.25 | 0.00986589 | 0.0 | 1.3750000000000002 |
| sod-cpu-double-O2-ieee-leq-rusanov | double | cpu-double-O2-ieee-leq | 200 | 1 | 0.25 | 0.0087228 | 0.0 | 1.3750000000000002 |
| stationary_contact-cpu-double-O2-ieee-leq-hllc | double | cpu-double-O2-ieee-leq | 200 | 1 | 0.5 | 0.0125849 | 0.0 | 2.5000000000000004 |
| stationary_contact-cpu-double-O3-ieee-leq-hllc | double | cpu-double-O3-ieee-leq | 200 | 1 | 0.5 | 0.0124147 | 0.0 | 2.5000000000000004 |
| stationary_contact-cpu-double-Ofast-fastmath-leq-hllc | double | cpu-double-Ofast-fastmath-leq | 200 | 1 | 0.5 | 0.0101064 | 0.0 | 2.5000000000000004 |
| stationary_contact-cpu-double-O2-ieee-strict-hllc | double | cpu-double-O2-ieee-strict | 200 | 1 | 0.5 | 0.00993962 | 0.0 | 2.5000000000000004 |
| stationary_contact-cpu-double-O2-ieee-leq-rusanov | double | cpu-double-O2-ieee-leq | 200 | 1 | 0.5 | 0.0145659 | 0.0 | 2.5000000000000004 |
| lw3-n200-cpu-double-O2-ieee-leq-hllc | double | cpu-double-O2-ieee-leq | 200 | 200 | 0.3 | 0.615973 | 0.1341063034931487 | 2.255677266652683 |
| lw3-n200-cpu-double-O3-ieee-leq-hllc | double | cpu-double-O3-ieee-leq | 200 | 200 | 0.3 | 0.511775 | 0.1341063034931487 | 2.255677266652683 |
| lw3-n200-cpu-double-Ofast-fastmath-leq-hllc | double | cpu-double-Ofast-fastmath-leq | 200 | 200 | 0.3 | 0.532344 | 0.13410630349314873 | 2.255677266652683 |
| lw3-n200-cpu-double-O2-ieee-strict-hllc | double | cpu-double-O2-ieee-strict | 200 | 200 | 0.3 | 0.672099 | 0.1341063034931487 | 2.255677266652683 |
| lw3-n200-cpu-double-O2-ieee-leq-rusanov | double | cpu-double-O2-ieee-leq | 200 | 200 | 0.3 | 0.465201 | 0.13406347120126913 | 2.255708637512586 |

## Pairs

| pair_label | left | right | l1 | linf | ulp_max | philip_ratio |
|---|---|---|---:|---:|---:|---:|
| axis_leq_vs_strict | sod-cpu-double-O2-ieee-leq-hllc | sod-cpu-double-O2-ieee-strict-hllc | 0.000000e+00 | 0.000000e+00 | 0.0 | n/a |
| axis_leq_vs_strict | stationary_contact-cpu-double-O2-ieee-leq-hllc | stationary_contact-cpu-double-O2-ieee-strict-hllc | 0.000000e+00 | 0.000000e+00 | 0.0 | n/a |
| axis_leq_vs_strict | lw3-n200-cpu-double-O2-ieee-leq-hllc | lw3-n200-cpu-double-O2-ieee-strict-hllc | 5.025431e-16 | 2.042810e-14 | 21.427856397714137 | n/a |
