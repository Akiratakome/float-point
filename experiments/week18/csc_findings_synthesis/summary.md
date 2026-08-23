# CSC KH MCA findings synthesis

Combined gate: `True`.

| solver | field | p53 spread | p24 spread | p24/p53 | deterministic Linf | det./p24 |
|---|---|---:|---:|---:|---:|---:|
| HLL | rho | 4.797e-16 | 1.431e-07 | 2.984e+08 | 3.119e-07 | 2.18 |
| HLL | vx | 1.509e-15 | 4.087e-07 | 2.708e+08 | 1.903e-07 | 0.47 |
| HLL | By | 2.655e-17 | 1.087e-08 | 4.096e+08 | 1.188e-08 | 1.09 |
| HLL | p | 5.439e-16 | 1.832e-07 | 3.368e+08 | 2.686e-07 | 1.47 |
| HLLD | rho | 1.243e-15 | 4.291e-07 | 3.452e+08 | 7.429e-07 | 1.73 |
| HLLD | vx | 3.952e-15 | 1.677e-06 | 4.243e+08 | 3.280e-07 | 0.20 |
| HLLD | By | 6.494e-17 | 2.109e-08 | 3.247e+08 | 2.404e-08 | 1.14 |
| HLLD | p | 8.133e-16 | 2.675e-07 | 3.289e+08 | 3.589e-07 | 1.34 |

## Claim boundary

The 64^2, t=0.05, N=4 result validates the pipeline and provides reduced-case directional evidence only; it does not promote the full 256^2, t=1.0, N=30 KH MCA claim.
