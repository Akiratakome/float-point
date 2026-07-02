# MHD Precision Pilot Summary

- Experiment: week14-mhd-precision-pilot
- Case: brio_wu_1d
- Solver: hll
- Reference: cpu-double-O2-ieee-leq
- Git commit: 8eee31318fa512c2a69d012726eb7699d7c8b0c2

## G0

- Pass: True

## Deterministic variants

| variant | precision | opt | fastmath | riemann | finite | rc | steps | divB_max | walltime_s | is_reference | L1_rho | L2_rho | Linf_rho | L1_By | L2_By | Linf_By | L1_p | L2_p | Linf_p | L1_vx | L2_vx | Linf_vx |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | double | O2 | False | leq | True | 0 | 759 | 4.441e-14 | 0.1899307999992743 | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-O2-ieee-strict | double | O2 | False | strict | True | 0 | 759 | 4.441e-14 | 0.16580690001137555 | False | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-Ofast-ieee-leq | double | Ofast | False | leq | True | 0 | 759 | 4.441e-14 | 0.1693470999598503 | False | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-Ofast-ieee-strict | double | Ofast | False | strict | True | 0 | 759 | 4.441e-14 | 0.18615139997564256 | False | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-float-O2-ieee-leq | float | O2 | False | leq | True | 0 | 759 | 0.0 | 0.148184800054878 | False | 7.882574032899722e-08 | 1.432129132030242e-07 | 1.075167475605987e-06 | 9.221763949358817e-08 | 1.745171052894174e-07 | 9.56222249715033e-07 | 1.1417617451681677e-07 | 1.8612459959573686e-07 | 8.4764803021109e-07 | 1.947204960684316e-07 | 3.2743802518208345e-07 | 1.5686030066033863e-06 |
| cpu-float-O2-ieee-strict | float | O2 | False | strict | True | 0 | 759 | 0.0 | 0.1419288000324741 | False | 7.882574032899722e-08 | 1.432129132030242e-07 | 1.075167475605987e-06 | 9.221763949358817e-08 | 1.745171052894174e-07 | 9.56222249715033e-07 | 1.1417617451681677e-07 | 1.8612459959573686e-07 | 8.4764803021109e-07 | 1.947204960684316e-07 | 3.2743802518208345e-07 | 1.5686030066033863e-06 |
| cpu-float-Ofast-ieee-leq | float | Ofast | False | leq | True | 0 | 759 | 0.0 | 0.13939570006914437 | False | 7.882574032899722e-08 | 1.432129132030242e-07 | 1.075167475605987e-06 | 9.221763949358817e-08 | 1.745171052894174e-07 | 9.56222249715033e-07 | 1.1417617451681677e-07 | 1.8612459959573686e-07 | 8.4764803021109e-07 | 1.947204960684316e-07 | 3.2743802518208345e-07 | 1.5686030066033863e-06 |
| cpu-float-Ofast-ieee-strict | float | Ofast | False | strict | True | 0 | 759 | 0.0 | 0.14348929992411286 | False | 7.882574032899722e-08 | 1.432129132030242e-07 | 1.075167475605987e-06 | 9.221763949358817e-08 | 1.745171052894174e-07 | 9.56222249715033e-07 | 1.1417617451681677e-07 | 1.8612459959573686e-07 | 8.4764803021109e-07 | 1.947204960684316e-07 | 3.2743802518208345e-07 | 1.5686030066033863e-06 |

## MCA

| name | status | reason | n | runner | mca_evidence_generated | spread_rho | spread_By | spread_p | spread_vx | snr_rho | snr_By | snr_p | rho_mean_spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| p24 | blocked_environment | MCA skipped via --skip-mca | 0 |  | False |  |  |  |  |  |  |  |  |
| p53 | blocked_environment | MCA skipped via --skip-mca | 0 |  | False |  |  |  |  |  |  |  |  |

## Ordering flags

| axis | precision | opt | riemann | ieee_variant | fastmath_variant | ieee_Linf_rho | fastmath_Linf_rho |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Claim buckets

- morphology: Report only morphology after G0 passes and deterministic rows are finite.
- precision_noise: Precision-noise claims remain provisional until MCA depth is evaluated.
- self_reference: Reference claims are anchored to the cpu double O2 IEEE leq run.
