# MHD Precision Pilot Summary

- Experiment: week14-mhd-precision-pilot
- Case: brio_wu_1d
- Solver: hlld
- Reference: cpu-double-O2-ieee-leq
- Git commit: 0ab957cfb2a10fcfaeef5867a8deaa601259118e

## G0

- Pass: True

## Deterministic variants

| variant | precision | opt | fastmath | riemann | finite | rc | steps | divB_max | walltime_s | is_reference | L1_rho | L2_rho | Linf_rho | L1_By | L2_By | Linf_By | L1_p | L2_p | Linf_p | L1_vx | L2_vx | Linf_vx |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | double | O2 | False | leq | True | 0 | 761 | 0.0 | 0.5740517000667751 | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-O2-ieee-strict | double | O2 | False | strict | True | 0 | 761 | 0.0 | 0.49297100002877414 | False | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| cpu-double-Ofast-ieee-leq | double | Ofast | False | leq | True | 0 | 761 | 0.0 | 0.5720879000145942 | False | 4.3506864777498324e-16 | 7.087352401676692e-16 | 4.413136522884997e-15 | 4.007991855070614e-16 | 7.238188114797011e-16 | 7.327471962526033e-15 | 3.8698211302090615e-16 | 7.413466965664634e-16 | 1.099120794378905e-14 | 6.611848401013742e-16 | 1.1849893967008378e-15 | 1.1400602684119576e-14 |
| cpu-double-Ofast-ieee-strict | double | Ofast | False | strict | True | 0 | 761 | 0.0 | 0.5497290999628603 | False | 4.3506864777498324e-16 | 7.087352401676692e-16 | 4.413136522884997e-15 | 4.007991855070614e-16 | 7.238188114797011e-16 | 7.327471962526033e-15 | 3.8698211302090615e-16 | 7.413466965664634e-16 | 1.099120794378905e-14 | 6.611848401013742e-16 | 1.1849893967008378e-15 | 1.1400602684119576e-14 |
| cpu-float-O2-ieee-leq | float | O2 | False | leq | True | 0 | 761 | 0.0 | 0.4219525000080466 | False | 1.529375126651472e-07 | 2.6454001408204743e-07 | 1.6292663023165233e-06 | 1.470276280944479e-07 | 2.6175836803156965e-07 | 2.559658266551579e-06 | 1.4493721714084844e-07 | 2.531007853982971e-07 | 2.496143179153698e-06 | 2.459988003599735e-07 | 4.1719298973158255e-07 | 2.3276200024069382e-06 |
| cpu-float-O2-ieee-strict | float | O2 | False | strict | True | 0 | 761 | 0.0 | 0.410743199987337 | False | 1.529375126651472e-07 | 2.6454001408204743e-07 | 1.6292663023165233e-06 | 1.470276280944479e-07 | 2.6175836803156965e-07 | 2.559658266551579e-06 | 1.4493721714084844e-07 | 2.531007853982971e-07 | 2.496143179153698e-06 | 2.459988003599735e-07 | 4.1719298973158255e-07 | 2.3276200024069382e-06 |
| cpu-float-Ofast-ieee-leq | float | Ofast | False | leq | True | 0 | 761 | 0.0 | 0.43438290001358837 | False | 1.4711969440078646e-07 | 2.6044893634236064e-07 | 1.5022835266886858e-06 | 1.4915071128218256e-07 | 2.587801956186335e-07 | 2.2214077394222542e-06 | 1.5390568750644392e-07 | 2.7052576485298305e-07 | 2.9497551895518725e-06 | 2.702887698501943e-07 | 5.186630585020054e-07 | 4.804245626932602e-06 |
| cpu-float-Ofast-ieee-strict | float | Ofast | False | strict | True | 0 | 761 | 0.0 | 0.4109850999666378 | False | 1.4711969440078646e-07 | 2.6044893634236064e-07 | 1.5022835266886858e-06 | 1.4915071128218256e-07 | 2.587801956186335e-07 | 2.2214077394222542e-06 | 1.5390568750644392e-07 | 2.7052576485298305e-07 | 2.9497551895518725e-06 | 2.702887698501943e-07 | 5.186630585020054e-07 | 4.804245626932602e-06 |

## MCA

| name | status | reason | n | runner | mca_evidence_generated | spread_rho | spread_By | spread_p | spread_vx | snr_rho | snr_By | snr_p | rho_mean_spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| p24 | completed | Produced 8 Verificarlo MCA sample grids with runner `docker`. | 8 | docker | True | 5.230880824303713e-06 | 1.5754372845684098e-05 | 1.9676320460471303e-05 | 2.5862873255675058e-05 | 862388.0521914961 | 1873587.0005376555 | 1351618.8517051437 | 1.798161095578621e-07 |
| p53 | completed | Produced 8 Verificarlo MCA sample grids with runner `docker`. | 8 | docker | True | 1.1095874382657468e-14 | 3.285917208965409e-14 | 4.2185302750711745e-14 | 5.627772498044672e-14 | 368479258156141.5 | 835318934884552.2 | 512928195805202.56 | 3.3306690738754696e-16 |

## Ordering flags

| axis | precision | opt | riemann | ieee_variant | fastmath_variant | ieee_Linf_rho | fastmath_Linf_rho |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Claim buckets

- morphology: Report only morphology after G0 passes and deterministic rows are finite.
- precision_noise: Precision-noise claims remain provisional until MCA depth is evaluated.
- self_reference: Reference claims are anchored to the cpu double O2 IEEE leq run.
