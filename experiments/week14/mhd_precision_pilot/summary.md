# MHD Precision Pilot Summary

- Experiment: week14-mhd-precision-pilot
- Case: brio_wu_1d
- Solver: hll
- Reference: cpu-double-O2-ieee-leq
- Git commit: 734629799b9e2469e71780a4b8a5caff76e7ee8c

## G0

- Pass: True

## Deterministic variants

| variant | precision | opt | fastmath | riemann | finite | rc | steps | divB_max | walltime_s | is_reference | L1_rho | L2_rho | Linf_rho | L1_By | L2_By | Linf_By | L1_p | L2_p | Linf_p | L1_vx | L2_vx | Linf_vx |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | double | O2 | False | leq | True | 0 | 759 | 4.441e-14 | 0.18336329993326217 | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-O2-ieee-strict | double | O2 | False | strict | True | 0 | 759 | 4.441e-14 | 0.1811578000197187 | False | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-Ofast-ieee-leq | double | Ofast | False | leq | True | 0 | 759 | 0.0 | 0.18268530000932515 | False | 2.3708465746175025e-16 | 3.908165291135101e-16 | 1.887379141862766e-15 | 2.714104982426413e-16 | 4.627319025766094e-16 | 2.3314683517128287e-15 | 2.982336599899327e-16 | 5.009862177271393e-16 | 2.4424906541753444e-15 | 5.728074416794512e-16 | 9.483426881781895e-16 | 3.858025010572419e-15 |
| cpu-double-Ofast-ieee-strict | double | Ofast | False | strict | True | 0 | 759 | 0.0 | 0.1673935999860987 | False | 2.3708465746175025e-16 | 3.908165291135101e-16 | 1.887379141862766e-15 | 2.714104982426413e-16 | 4.627319025766094e-16 | 2.3314683517128287e-15 | 2.982336599899327e-16 | 5.009862177271393e-16 | 2.4424906541753444e-15 | 5.728074416794512e-16 | 9.483426881781895e-16 | 3.858025010572419e-15 |
| cpu-float-O2-ieee-leq | float | O2 | False | leq | True | 0 | 759 | 0.0 | 0.1385556000750512 | False | 7.882574032899722e-08 | 1.432129132030242e-07 | 1.075167475605987e-06 | 9.221763949358817e-08 | 1.745171052894174e-07 | 9.56222249715033e-07 | 1.1417617451681677e-07 | 1.8612459959573686e-07 | 8.4764803021109e-07 | 1.947204960684316e-07 | 3.2743802518208345e-07 | 1.5686030066033863e-06 |
| cpu-float-O2-ieee-strict | float | O2 | False | strict | True | 0 | 759 | 0.0 | 0.13633070001378655 | False | 7.882574032899722e-08 | 1.432129132030242e-07 | 1.075167475605987e-06 | 9.221763949358817e-08 | 1.745171052894174e-07 | 9.56222249715033e-07 | 1.1417617451681677e-07 | 1.8612459959573686e-07 | 8.4764803021109e-07 | 1.947204960684316e-07 | 3.2743802518208345e-07 | 1.5686030066033863e-06 |
| cpu-float-Ofast-ieee-leq | float | Ofast | False | leq | True | 0 | 759 | 0.0 | 0.1372351999161765 | False | 9.321573716049016e-08 | 1.7337094612448776e-07 | 9.29133896931944e-07 | 9.908299169114333e-08 | 1.7749541009053786e-07 | 1.5097946416409158e-06 | 1.1045826874132166e-07 | 1.8724045416042503e-07 | 1.5346323517517746e-06 | 1.7620903126125794e-07 | 3.00867610133495e-07 | 1.9830211069882253e-06 |
| cpu-float-Ofast-ieee-strict | float | Ofast | False | strict | True | 0 | 759 | 0.0 | 0.146999099990353 | False | 9.321573716049016e-08 | 1.7337094612448776e-07 | 9.29133896931944e-07 | 9.908299169114333e-08 | 1.7749541009053786e-07 | 1.5097946416409158e-06 | 1.1045826874132166e-07 | 1.8724045416042503e-07 | 1.5346323517517746e-06 | 1.7620903126125794e-07 | 3.00867610133495e-07 | 1.9830211069882253e-06 |

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
