# Week 18 KH solver and precision timing

Gate pass: `True`.

| solver | precision | median (s) | IQR (s) | min-max (s) | max ULP between repeats |
|---|---|---:|---:|---:|---:|
| HLL | FP64 | 34.484 | 0.103 | 34.367-34.735 | 0 |
| HLL | FP32 | 29.196 | 0.801 | 28.911-29.858 | 0 |
| HLLD | FP64 | 39.542 | 0.197 | 39.040-39.662 | 0 |
| HLLD | FP32 | 34.254 | 0.158 | 34.197-34.667 | 0 |

FP32 speed-up: HLL `1.181x`, HLLD `1.154x`.
HLLD/HLL cost: FP64 `1.147x`, FP32 `1.173x`.

Five repeats on one workstation support a bounded KH CPU comparison; they do not establish cross-machine performance portability.
