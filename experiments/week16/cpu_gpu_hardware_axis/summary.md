# Week 16 MHD CPU/GPU Hardware Axis

- Mode: `report-grade`
- Commit: `0fe1239a942e852c092eec9a0ab9849bbbc71dfd`
- Gate: `G-GPU` pass = `True`
- ULP target: `0`

| case | precision | grid | steps cpu/gpu | ulp_max | linf_abs | speedup cpu/gpu | divB_max cpu/gpu | pass |
|---|---|---:|---:|---:|---:|---:|---:|---|
| brio_wu_1d | double | 800x1 | 759/759 | 0 | 0.000000e+00 | 0.066 | 4.441000e-14/4.441000e-14 | True |
| brio_wu_1d | float | 800x1 | 759/759 | 0 | 0.000000e+00 | 0.518 | 0.000000e+00/0.000000e+00 | True |
| orszag_tang_2d | double | 256x256 | 806/806 | 0 | 0.000000e+00 | 5.609 | 3.720000e+00/3.720000e+00 | True |
| orszag_tang_2d | float | 256x256 | 806/806 | 0 | 0.000000e+00 | 5.655 | 3.720000e+00/3.720000e+00 | True |

The gate is a same-precision correctness check for the validated HLL GPU path. It does not cover HLLD, KH-on-GPU, GPU MCA, or a broad performance study.

Generated `grid.bin` files are removed after measurement; run metadata, generated configs, stdout/stderr logs, summaries, and figures are retained.
