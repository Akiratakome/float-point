# 1600^2 Reference Candidate Gate Decision

Purpose: decide whether the 1600^2 GPU run can be used as a CPU-anchored reference candidate.

## Inputs

- Week 6 strict GPU smoke: experiments/week6/regression/summary.md
- Week 7 HLLC strict preflight: experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md

## Decision

- If Task 9 passes: proceed with Task 11 as a GPU high-resolution reference candidate anchored by Week 6 smoke and HLLC strict preflight.
- If Task 9 fails: stop; Task 11 is not part of the Report 1 reference-base pipeline. Any later GPU-only exploratory run requires explicit override and must be documented outside this gate decision.

## Recorded Outcome

Task 9 passed: both n200 and n400 HLLC strict CPU<->GPU preflight rows passed with zero deltas and `gate_passed` true.

Task 11 is allowed to proceed as a GPU high-resolution reference candidate anchored by Week 6 strict smoke and the Week 7 HLLC strict preflight. This is not CPU-equivalent proof.
