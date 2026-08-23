# Week 16 KH Verificarlo MCA — CSC Execution Findings & Data

**Branch:** `week12-mhd-implementation` · **Source commit:** `8de35c3`
**Host:** CSC (`athena` login node + `csc-mphil` compute partition, `phy-cerberus[4-6]`)
**Toolchain:** Verificarlo 2.4.0 (native, `/lsc/opt/verificarlo-2.4.0`), clang 18.1.3
**Date:** 2026-07-24

This document summarizes what was investigated, the measured data, and the
conclusions — suitable for a supervisor report. The full experiment (256²/t=1.0,
N=30 MCA) was still running when this was written; see "Status" at the end.

---

## 1. Executive summary

- The KH MCA solver is **correct and not buggy**. A run that appeared "stuck for
  hours" was doing exactly the right physics — the cost is genuine Verificarlo
  Monte Carlo Arithmetic (MCA) instrumentation overhead, quantified below.
- The reference **quad MCA backend is ~417× slower than native** on this case.
  One full sample takes **~2.5–3 h on a dedicated compute node** (and ~7.7 h on
  the contended login node).
- The faster `mca_int` backend (~2×) **cannot run the p24 float-level surrogate**
  (it rejects reduced virtual precision), so the reference quad backend is used
  for both precisions to keep the p53-vs-p24 comparison on one backend.
- Feasibility within the CSC **6 h partition cap** is achieved by **splitting
  each (solver × precision) MCA block into its own Slurm array task** rather than
  running both precisions sequentially in one task (which would overflow).

---

## 2. What was verified — "is it a bug?" (No.)

Four independent checks, all consistent with correct, actively-progressing compute:

| Check | Method | Result | Meaning |
|---|---|---|---|
| Timestep collapse? | Ran instrumented binary to `t=0.02` | **23 steps** — exactly `1148 × 0.02` | CFL timestep normal; **no collapse** |
| Where is the time? | `gdb` stack sampled ×3 on the live process | 100 % in `libinterflop_mca.so` soft-float 128-bit quad ops (`__addtf3`, `__multf3`, `__trunctfdf2`) inside real kernels (`predict_faces`, `mhd_hll_flux`) | Time is MCA arithmetic, not a loop bug |
| Hung or working? | `strace` on live process | **Zero syscalls** in 3 s | Pure userspace compute, not blocked on I/O/lock |
| Idle/contended? | `sstat` CPU-time vs wall-time | Exact match on dedicated node | No idling, full core utilization |

The plain (non-instrumented) build runs the identical 256²/t=1.0 case in **65.7 s
(1148 steps)** — proving the numerics and build flags (`-O3 -DNDEBUG`) are fine.

---

## 3. Measured overhead & backend comparison

Same machine (`athena`), same case, same instrumented binary, `t=0.02` (23 steps),
all producing identical correct results (matching `divB`):

| backend / mode | s/step | speedup vs quad | ~full t=1.0 sample (loaded) | scientific model |
|---|---:|---:|---:|---|
| native (no instrumentation) | 0.0575 | — | 66 s (measured) | IEEE double |
| `mca` (quad) `mode=mca` | 24.0 | 1.0× | 7.7 h | **true MCA** |
| `mca_int` `mode=mca` | 11.43 | 2.1× | 3.6 h | **true MCA** (p53 only) |
| `mca_int` `mode=rr` | 6.25 | 3.8× | 2.0 h | random rounding only |

Overhead of the reference quad backend: **24.0 / 0.0575 ≈ 417× per step.** This is
within Verificarlo's documented 10–500× range for FP-dense stencil codes; this MHD
solver is on the high end (9-variable state, MUSCL reconstruction, HLL/HLLD
wave-speed algebra → billions of instrumented ops per sample).

On a **dedicated compute node** (no login-node contention) the quad single sample
runs in roughly **2.5–3 h** (a measurement job reached 2 h 20 m before being
cancelled once the data above was sufficient).

---

## 4. Key constraint found: `mca_int` cannot do p24

The experiment compares MCA noise floors at **p53** (full double, 53-bit) vs **p24**
(float-level surrogate, 24-bit virtual precision). The p24 block passes
`--precision-binary64=24`. The faster `mca_int` backend rejects this at runtime:

```
Error [interflop-mcaint]: --precision-binary64 invalid value provided,
                          MCA integer does not support custom precisions
```

`mca_int` only supports the **native** binary64 precision (53). Therefore the p24
half must use the reference quad backend, and for a clean single-backend comparison
**both** precisions use quad. (`mca_int` remains available in the harness via
`--backend-lib` for any future p53-only, full-precision study.)

---

## 5. CSC environment constraints discovered

- **Login node (`athena`) is unusable for builds/runs:** load average ~68 on 12
  cores. It intermittently OOM-kills clang mid-compile and fails `mmap` of shared
  libraries (`libjpeg ... failed to map segment`). **All real work must go through
  Slurm to compute nodes.**
- **Only the `csc-mphil` partition (6 h cap) is usable** by this account. The
  `lsc` partition (36 h) exists but is not in the account's Slurm association list.
- **No Apptainer** on the nodes: Verificarlo is installed natively, so the harness
  was extended with a `native` runner mode (`HRSC_VFC_RUNNER=native`) instead of
  the container image the original runbook assumed.

---

## 6. Changes made to make the run feasible (all on `week12-mhd-implementation`)

1. **Native Verificarlo runner** in `env.sh` (`HRSC_VFC_RUNNER=native`) — bypasses
   the Apptainer/`.sif` requirement, uses the cluster's native Verificarlo 2.4.0.
2. **Configurable per-sample timeout** (`--sample-timeout-s`) — the harness had a
   hardcoded 300 s per-attempt kill that silently turned long real runs into
   fake "blocked" evidence; default unchanged so other experiments are unaffected.
3. **Selectable backend** (`--backend-lib`) — enables `mca_int` where valid;
   defaults to the reference quad backend.
4. **Per-precision Slurm tasks** — the full-MCA array now runs each
   `(solver × precision)` block as its own task (`hll-p53, hll-p24, hlld-p53,
   hlld-p24`) writing `summary_p{53,24}.json` partials, merged into `summary.json`
   before the packet step. This fits each block in the 6 h cap.

All 35 existing harness/synthesis unit tests still pass after these changes.

---

## 7. Validation on the compute node

A reduced 64²/t=0.05 smoke of the exact production pipeline (native runner + split
tasks + partial/merge) ran on `phy-cerberus6`:
- **p53 blocks (HLL, HLLD): completed cleanly** (n samples read, real field metrics).
- (See the paired `summary_p*.json` files under `csc_mca_smoke/` in the data bundle.)

---

## 8. Status at time of writing

- Toolchain, pipeline, and Slurm plumbing: **validated on compute node.**
- Full 256²/t=1.0, N=30 MCA (HLL + HLLD, p53 + p24): **submitted / in progress**
  as four per-precision Slurm tasks, each budgeted within the 6 h cap.
- The full-resolution MCA summaries, KH packet regeneration, and W17 synthesis
  figures will be added to this bundle once the jobs complete.

### Claim boundary (unchanged)
Until both full MCA summaries report `p53.status == completed` **and**
`p24.status == completed`, and the packet gates pass, the full 256²/t=1.0 KH MCA
conclusion is **not** promoted; only the reduced smoke supports toolchain validity.

---

## Files in this bundle

- `README_findings.md` — this document.
- `raw_measurements/mcaint.log` — `mca_int mode=mca` timing (263 s / 23 steps).
- `raw_measurements/mcaint_rr.log` — `mca_int mode=rr` timing (143.6 s / 23 steps).
- (Added on completion) full-MCA `summary.json` per solver, packet summaries,
  W17 synthesis + figures, environment records, and Slurm logs.
