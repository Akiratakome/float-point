# Week 15-16 Evidence Completion Design

**Date:** 2026-07-21
**Goal:** Close the remaining report-evidence gaps identified after the Week 15
CPU precision study: temporal divergence, GPU HLL MHD and the hardware axis,
Kelvin-Helmholtz report-grade evidence, and bounded 512^2 conclusions.

**Existing designs reused:**

- `2026-07-09-mhd-temporal-divergence-lyapunov-design.md`
- `2026-07-09-gpu-mhd-hll-design.md`
- `2026-06-25-week13-mhd-hlld-2d-benchmarks-design.md`
- `2026-07-08-week15-ot-2d-precision-design.md`

This document fixes the cross-project order, gates, and evidence contract. It
does not replace the detailed temporal-divergence or GPU implementation designs.

## 1. Scope and order

Work proceeds in five independently verifiable phases:

1. Complete CPU temporal-divergence evidence for Brio-Wu and Orszag-Tang.
2. Implement and validate the CUDA HLL MHD solver.
3. Produce the CPU-versus-GPU hardware-axis evidence packet.
4. Produce report-grade Kelvin-Helmholtz CPU precision evidence.
5. Consolidate the Orszag-Tang and Kelvin-Helmholtz 512^2 conclusions and
   update the evidence index and supervisor-facing report material.

Each phase is committed and verified before the next expensive phase starts.
The order is evidence-first: the partially started, CPU-only temporal analysis
lands before the higher-risk GPU implementation.

### In scope

- HLL GPU MHD for Brio-Wu 1D and Orszag-Tang 2D, float and double.
- Same-precision CPU-versus-GPU accuracy and performance measurements.
- CPU Kelvin-Helmholtz HLL and HLLD deterministic 24-variant packets.
- CPU Kelvin-Helmholtz HLL and HLLD MCA at p53 and p24 with N=30, provided
  the prerequisite physical and numerical gates pass.
- A 256^2 candidate versus 512^2 reference comparison for Kelvin-Helmholtz,
  plus consolidation of the existing Orszag-Tang 512^2 reference evidence.

### Out of scope

- HLLD-on-GPU.
- GPU-side MCA; Verificarlo remains a CPU tool in this project.
- A full optimizer/compiler matrix on GPU whose flags are not comparable to
  the established CPU build matrix.
- Changing solver numerics, existing cfg defaults, or binary output formats.
- Claiming a formal maximal Lyapunov exponent. The fitted quantity remains a
  Lyapunov-like engineering growth rate of a precision perturbation.

## 2. Canonical data flow

Every evidence-producing phase follows:

`config -> build -> run -> measure -> aggregate -> plot`

Generated configs, stdout/stderr, binary hashes, git commit, runtime metadata,
and summary files travel together. Transient `.bin` grids are measured and
deleted by default; a documented keep option is allowed for debugging. Build
directories and transient grids are never committed.

### 2.1 Temporal divergence

`scripts/regression/mhd_temporal_divergence.py` generates a monotone set of
`t_end` slices from the validated case cfgs, runs the canonical fp32 and fp64
CPU HLL binaries, and delegates pair metrics and exponential fits to
`scripts/metrics/drift_timeseries.py`. It emits `summary.json`, `summary.csv`,
`summary.md`, and `figures/temporal_divergence.png` under
`experiments/week15/mhd_temporal_divergence/`.

The driver must preserve all non-harness cfg values. Pairing uses documented
time and spatial tolerances because fp32 and fp64 runs can end at slightly
different header times and store rounded grid spacing.

### 2.2 GPU HLL MHD

The CUDA implementation mirrors the existing Euler GPU architecture and reuses
the existing MHD `HD_FUNC` arithmetic. Separate kernels perform reconstruction,
Hancock prediction, HLL fluxes, conservative updates, the GLM source step, and
a fixed-order CFL reduction. `MhdGpuSolver<Real>` owns device residency and is
selected through `device=cpu|gpu` in `hrsc_mhd`.

All GPU code is guarded by `ENABLE_CUDA` and `HRSC_HAS_CUDA`. CPU-only builds,
the default CPU dispatch, and existing outputs remain unchanged.

### 2.3 Hardware-axis packet

The validated GPU solver runs Brio-Wu and Orszag-Tang in float and double using
the same case parameters and same-precision CPU baselines. The packet records
field error, ULP maxima, step count, final time, `divB` diagnostics, wall time,
and speedup. It reuses the established summary schemas and adds hardware-axis
fields as an additive schema extension; all existing field names and binary
formats remain unchanged.

### 2.4 Kelvin-Helmholtz packet

The existing 256^2 HLL morphology run is not sufficient for a precision claim.
First, `mhd_kh_2d.py` must complete its 256^2-versus-512^2 HLL reference gate,
mass-conservation gate, finite/positive-state checks, and bounded `divB` gate.
Only after these pass may the precision harness generate, per solver:

- the 24 deterministic O2/O3/Ofast x ieee/fastmath x leq/strict variants;
- p53 and p24 MCA packets with N=30;
- unified summaries and report-style figures.

HLLD remains a studied CPU solver axis, not the production default. If its KH
anchor gate fails, the HLLD packet is retained as bounded diagnostic evidence
and is excluded from report-grade comparative claims.

### 2.5 512^2 consolidation

The final phase combines the existing Orszag-Tang 512^2 reference with the new
Kelvin-Helmholtz reference result. It reports only 256^2-versus-512^2
self-reference sensitivity and does not imply asymptotic convergence from two
resolutions. The project index and Week 15/16 report material link directly to
the committed summaries and figures.

## 3. Gates and failure handling

### Temporal divergence gates

- Pure driver helpers pass unit tests.
- A fake-run integration test validates config generation, command execution,
  aggregation, cleanup, and output schema.
- A real short-run smoke passes before the full slice plan starts.
- All drift values are finite. The Orszag-Tang fitted growth window has a
  positive slope; Brio-Wu is reported as the non-chaotic control without
  forcing a zero or negative slope.

### GPU gates

- CUDA 13.3 and the existing `gpu_smoke` target pass on the RTX 5070.
- Each kernel is developed against a CPU oracle test before end-to-end runs.
- The target is same-precision `ulp_max=0`. If exact equality is unattainable,
  the smallest justified tight tolerance is recorded with root-cause analysis;
  tolerances are never silently widened.
- Brio-Wu and Orszag-Tang pass for float and double, with matching step counts
  and bounded `divB` diagnostics.
- The full CPU suite remains green in a non-CUDA build.

### Kelvin-Helmholtz and 512^2 gates

- Non-finite states, failed conservation, failed `divB`, or failed reference
  gates stop the downstream deterministic matrix and MCA runs.
- Every expensive run starts with a reduced-grid or reduced-sample smoke.
- Valid existing runs are resumed or reused by metadata identity rather than
  recomputed.
- Failed and interrupted runs retain configs, logs, and metadata, but their
  results do not enter headline conclusions.

## 4. Verification strategy

Verification scales with each phase:

- Python unit and integration tests for harness logic and summary schemas.
- Catch2 per-kernel CUDA tests and float/double end-to-end GPU tests.
- Small real-run smoke tests before full evidence generation.
- Evidence audits for expected row counts, N=30 sample counts, gate status,
  required metadata, figure presence, and absence of committed `.bin` grids.
- Final CPU full-suite and CUDA `[gpu]` suite runs before completion is claimed.

## 5. Deliverables

Completion requires all of the following, subject to explicit gate outcomes:

- Temporal-divergence driver, tests, summaries, and figure.
- GPU HLL MHD source, tests, `device=gpu` dispatch, and validation summary.
- Brio-Wu and Orszag-Tang CPU-versus-GPU hardware-axis packet.
- Kelvin-Helmholtz validation, deterministic precision packets, MCA packets,
  summaries, and figures.
- A bounded 512^2 comparison note for Orszag-Tang and Kelvin-Helmholtz.
- Updated `docs/INDEX.md`, regression documentation, and Week 15/16
  supervisor-facing material with supported and deferred claims separated.

The work is complete when all applicable gates pass, or when a hard gate fails
and the resulting bounded negative result is fully documented. A failed hard
gate never becomes a positive claim by reducing the acceptance standard.
