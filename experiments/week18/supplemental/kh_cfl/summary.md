# Week 18 Kh Cfl

- Gate pass: `True`
- Rows: `16`
- Schema: `hrsc.week18-supplemental` version `1`

| solver | CFL | steps fp64/fp32 | divB max fp64/fp32 | Linf rho fp32 vs fp64 |
|---|---:|---:|---:|---:|
| hll | 0.2 | 2296/2296 | 7.708000e-04/7.709000e-04 | 4.677651e-06 |
| hll | 0.4 | 1148/1148 | 6.714000e-04/6.721000e-04 | 1.786043e-06 |
| hll | 0.6 | 766/766 | 6.525000e-04/6.542000e-04 | 2.133123e-06 |
| hll | 0.8 | 574/574 | 6.775000e-04/6.817000e-04 | 8.909591e-07 |
| hlld | 0.2 | 2296/2296 | 5.294000e-03/5.300000e-03 | 7.204343e-06 |
| hlld | 0.4 | 1148/1148 | 4.228000e-03/4.233000e-03 | 3.230010e-06 |
| hlld | 0.6 | 766/766 | 3.995000e-03/3.990000e-03 | 4.056968e-06 |
| hlld | 0.8 | 574/574 | 3.490000e-03/3.484000e-03 | 3.157430e-06 |

Boundary: this is a CFL-sensitivity study, not a formal temporal-convergence result.
