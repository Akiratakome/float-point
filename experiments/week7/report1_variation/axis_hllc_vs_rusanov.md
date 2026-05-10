# Matrix Summary Report

Note: HLLC vs Rusanov compares two different numerical schemes under the same
build and source cfg. Pairwise ULP gating is not meaningful for this axis; use
the L1/Linf values as scheme-sensitivity diagnostics only.

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
| axis_hllc_vs_rusanov | sod-cpu-double-O2-ieee-leq-hllc | sod-cpu-double-O2-ieee-leq-rusanov | 1.200910e-03 | 1.931639e-02 | 34797311823648.695 | n/a |
| axis_hllc_vs_rusanov | stationary_contact-cpu-double-O2-ieee-leq-hllc | stationary_contact-cpu-double-O2-ieee-leq-rusanov | 2.196637e-03 | 2.306215e-01 | 415450739567204.1 | n/a |
| axis_hllc_vs_rusanov | lw3-n200-cpu-double-O2-ieee-leq-hllc | lw3-n200-cpu-double-O2-ieee-leq-rusanov | 8.582604e-03 | 1.451405e+00 | 1522436855039603.8 | n/a |
