# Matrix Summary Report

## Runs

| name | precision | build | nx | ny | t_end | total_s | integral_min | integral_max |
|---|---|---|---:|---:|---:|---:|---:|---:|
| lw3-n200-gpu-double-strict | double | cuda-double-strict | 200 | 200 | 0.3 | 0.184288 | 0.1341063034931487 | 2.255677266652683 |
| lw3-n400-gpu-double-strict | double | cuda-double-strict | 400 | 400 | 0.3 | 0.540408 | 0.13414936629842453 | 2.2556396971843986 |
| lw3-n200-gpu-float-strict | float | cuda-float-strict | 200 | 200 | 0.30000001192092896 | 0.0740718 | 0.13410624774639818 | 2.2556772166709322 |
| lw3-n400-gpu-float-strict | float | cuda-float-strict | 400 | 400 | 0.30000001192092896 | 0.3533 | 0.13414932168324303 | 2.2556396808192987 |

## Pairs

| pair_label | left | right | l1 | linf | ulp_max | philip_ratio |
|---|---|---|---:|---:|---:|---:|
| lw3-n200-gpu-strict | lw3-n200-gpu-double-strict | lw3-n200-gpu-float-strict | 2.584873e-07 | 1.317301e-05 | n/a | n/a |
| lw3-n400-gpu-strict | lw3-n400-gpu-double-strict | lw3-n400-gpu-float-strict | 3.243139e-07 | 2.450523e-05 | n/a | n/a |
