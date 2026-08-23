# Brio--Wu direct build-semantics comparison

Gate pass: `True`. Source commit: `0fe1239a942e852c092eec9a0ab9849bbbc71dfd`.

| solver | precision | isolated axis | mean L1(rho) | Linf(rho) |
|---|---|---|---:|---:|
| HLL | FP64 | /Ox versus /O2 | 0.000e+00 | 0.000e+00 |
| HLL | FP64 | /fp:fast versus compiler default | 2.371e-16 | 1.887e-15 |
| HLL | FP64 | < versus <= in the Riemann branch | 0.000e+00 | 0.000e+00 |
| HLL | FP32 | /Ox versus /O2 | 0.000e+00 | 0.000e+00 |
| HLL | FP32 | /fp:fast versus compiler default | 1.176e-07 | 1.311e-06 |
| HLL | FP32 | < versus <= in the Riemann branch | 0.000e+00 | 0.000e+00 |
| HLLD | FP64 | /Ox versus /O2 | 0.000e+00 | 0.000e+00 |
| HLLD | FP64 | /fp:fast versus compiler default | 4.351e-16 | 4.413e-15 |
| HLLD | FP64 | < versus <= in the Riemann branch | 4.684e-16 | 3.886e-15 |
| HLLD | FP32 | /Ox versus /O2 | 0.000e+00 | 0.000e+00 |
| HLLD | FP32 | /fp:fast versus compiler default | 2.091e-07 | 1.729e-06 |
| HLLD | FP32 | < versus <= in the Riemann branch | 2.078e-07 | 2.608e-06 |

## Claim boundary

Each comparison changes one recorded build axis on MSVC for one Brio--Wu CPU configuration. The deterministic output result is not a compiler-wide, performance, accuracy, or portability claim.
