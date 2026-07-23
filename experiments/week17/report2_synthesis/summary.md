# Week 17 Report 2 Results Synthesis

This packet synthesizes committed Week 15-16 evidence. It does not rerun solvers or widen claim boundaries.

## Axis Ranking

| rank | axis | status | bounded result | authority |
|---:|---|---|---|---|
| 1 | `precision` | `bounded_primary_effect` | float_rows_depart_from_double_baselines_in_available_packets | `multiple committed Week 15-16 precision summaries` |
| 2 | `compiler_flags` | `bounded_cpu_deterministic_variation` | optimization_and_fastmath_change_some deterministic packets but do not form a unified report-grade gate | `multiple committed Week 15-16 precision summaries` |
| 3 | `hardware` | `report-grade` | bit_exact_for_covered_hll_cases | `experiments/week16/cpu_gpu_hardware_axis/summary.json` |
| 4 | `implementation_variant` | `small_or_zero_in_available_packets` | leq_vs_strict differences are small relative to precision effects in the available CPU packets | `multiple committed Week 15-16 precision summaries` |

## Temporal Divergence

| case | samples | lambda_l1 | lambda_linf | authority |
|---|---:|---:|---:|---|
| `brio_wu_1d` | 15 | 3.061535e+01 | 1.857906e+01 | `experiments/week15/mhd_temporal_divergence/summary.json` |
| `orszag_tang_2d` | 25 | 2.934310e-02 | -4.223342e-02 | `experiments/week15/mhd_temporal_divergence/summary.json` |

The planned Orszag-Tang > Brio-Wu temporal-divergence contrast was not observed.

## 512 Grid Gates

| case | L1 rho | Linf rho | divB max | gate |
|---|---:|---:|---:|---|
| `orszag_tang` | 7.721667e-02 | 6.459439e-01 | 3.720000e+00 | `True` |
| `kelvin_helmholtz` | 1.836380e-03 | 6.375538e-03 | 6.714000e-04 | `True` |

## MPI Omission

single-node OpenMP and CUDA isolate precision, compiler, and hardware effects without MPI reduction-order variability

## Claim Boundaries

- `kh_mca`: `blocked_environment`
- `asymptotic_convergence`: `False`
- `formal_lyapunov_exponent`: `False`
- `hll_gpu_scope`: `['brio_wu_1d', 'orszag_tang_2d']`
- `hll_gpu_excluded`: `['hlld_on_gpu', 'kh_on_gpu', 'gpu_mca', 'broad_gpu_matrix']`
- `provisional_rows_promoted`: `False`
