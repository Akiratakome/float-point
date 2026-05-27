# CSC Review 3 Experiment Execution Plan

Date: 2026-05-26

Purpose: close the remaining Review 3 experimental-design risks without
changing solver numerics, existing cfg defaults, or output formats. The plan
uses the repository harness discipline:

```text
config -> build -> run -> measure -> aggregate -> plot
```

The work is scoped to CSC runs. Raw build directories and large transient grids
must not be committed. Each accepted experiment must keep copied configs,
metadata, logs, scalar summaries, and only the grids needed for reproducible
metrics.

## Review Risks Addressed

| risk | current state | target evidence |
|---|---|---|
| Toro3/Toro5 toolchain split | Existing report evidence used Windows BuildTools, while Sod/LW3/LW12 used Linux/WSL. A CPU-only WSL/GCC sanity check already showed zero saved-state drift, but it is not a Linux CPU/GPU replacement. | CSC/Linux strict CPU-GPU final-state comparisons for Toro3/Toro5 in fp64 and fp32. |
| Toro3/Toro5 final-output-only evidence | Existing CPU/GPU evidence has no saved checkpoints for Toro3/Toro5. | CSC/Linux checkpointed CPU-GPU comparisons at several output times. |
| LW3 1600^2 reference provenance | LW3 high-resolution fp64 reference was generated on RTX 5090, while local validation/performance hardware is RTX 4060 Laptop. | CSC strict CPU-vs-RTX5090 preflight at lower LW3 resolution before relying on the GPU reference path. |
| LW12 missing 1600^2 hierarchy | Current LW12 reference is 800^2 fp64. This is defensible as a Report 1 limitation, but reviewer may ask why LW12 was not checked like LW3. | Conditional 400->800->1600 LW12 hierarchy if timing and storage are acceptable. |

## Tier A: Toro3/Toro5 Unified CSC Toolchain

### A1. Final-State CPU/GPU Strict Comparison

Run matrix:

| case | precision | solver | device | output |
|---|---|---|---|---|
| Toro3 | fp64 | HLLC | CPU strict | final grid |
| Toro3 | fp64 | HLLC | GPU strict | final grid |
| Toro3 | fp32 | HLLC | CPU strict | final grid |
| Toro3 | fp32 | HLLC | GPU strict | final grid |
| Toro5 | fp64 | HLLC | CPU strict | final grid |
| Toro5 | fp64 | HLLC | GPU strict | final grid |
| Toro5 | fp32 | HLLC | CPU strict | final grid |
| Toro5 | fp32 | HLLC | GPU strict | final grid |

Build requirements:

- Linux/CSC toolchain only.
- `STRICT_IEEE=ON`.
- HLLC branch rule stays at the report baseline.
- No source cfg files edited in place; generated cfg copies write under the
  experiment directory.

Output directory:

```text
experiments/review3_csc_toolchain_toro35/
```

Required artefacts:

- `matrix.json`
- copied generated cfgs per run
- `environment.txt` with hostname, git commit, compiler, CMake, CUDA, Slurm,
  GPU model
- `summary.md`
- `summary.json`
- `metrics.csv`
- Slurm stdout/stderr logs

Metrics:

- finite check
- CPU vs GPU conservative-state `L1`
- CPU vs GPU `Linf`
- CPU vs GPU `ULPmax`
- return code and final-time check

Pass condition:

- All runs complete with finite saved states.
- CPU/GPU drift is zero or explicitly roundoff-scale.
- If nonzero, the result is still usable only if the magnitude is smaller than
  the fp32/fp64 or reference/discretisation scale already reported.

Manuscript use if passed:

> Toro3 and Toro5 were rerun on the CSC Linux strict toolchain for both CPU and
> GPU, removing the historical Windows-BuildTools dependence from the
> report-facing CPU/GPU evidence.

### A2. Saved-Checkpoint CPU/GPU Comparison

Run only after A1 passes.

Add generated cfg copies with checkpoint times. Use four checkpoints:

```text
0.25 t_end, 0.50 t_end, 0.75 t_end, t_end
```

Do not edit the source cfg files. The output file names should include case,
precision, device, and checkpoint time.

Output directory:

```text
experiments/review3_csc_toolchain_toro35_checkpoints/
```

Required artefacts:

- `matrix.json`
- generated cfg copies
- `checkpoint_metrics.csv`
- `summary.md`
- `summary.json`
- `environment.txt`
- logs

Metrics:

- per-checkpoint CPU/GPU `L1`
- per-checkpoint CPU/GPU `Linf`
- per-checkpoint CPU/GPU `ULPmax`
- header time match
- finite check

Pass condition:

- All checkpoints exist for both CPU and GPU.
- Drift is zero or explicitly roundoff-scale at every checkpoint.

Manuscript use if passed:

> Saved-output identity is now available for Toro3 and Toro5 as well as Sod,
> LW3, and LW12; the hardware claim remains limited to saved states, not
> internal stage-by-stage identity.

## Tier B: LW3 RTX 5090 Reference-Path Preflight

Purpose: separate reference generation on RTX 5090 from local RTX 4060 Laptop
validation/performance claims.

Run matrix:

| case | resolution | precision | solver | device | output |
|---|---:|---|---|---|---|
| LW3 | 400^2 | fp64 | HLLC | CPU strict | final grid |
| LW3 | 400^2 | fp64 | HLLC | GPU strict RTX 5090 | final grid |

Optional extension if runtime is small:

| case | resolution | precision | solver | device | output |
|---|---:|---|---|---|---|
| LW3 | 800^2 | fp64 | HLLC | CPU strict | final grid |
| LW3 | 800^2 | fp64 | HLLC | GPU strict RTX 5090 | final grid |

Output directory:

```text
experiments/review3_csc_lw3_5090_preflight/
```

Metrics:

- CPU vs GPU `L1`, `Linf`, `ULPmax`
- finite check
- final-time/header check
- wall-clock time recorded as provenance, not as the main performance table

Pass condition:

- `N=400` CPU/GPU difference is zero or roundoff-scale.
- `N=800` is optional; do not block the manuscript on it.

Manuscript use if passed:

> The RTX 5090 was used only for high-resolution fp64 numerical-reference
> generation. The same CSC strict CPU/GPU path was checked at lower LW3
> resolution before relying on the GPU-generated reference.

If failed:

- Do not use the RTX 5090 reference as CPU-equivalent evidence.
- Keep the reference as a numerical candidate and explicitly state that its
  generation path is GPU-only.

## Tier C: Conditional LW12 1600^2 Reference Hierarchy

Purpose: decide whether LW12 can be upgraded from an 800^2 numerical reference
to a 400->800->1600 hierarchy.

This tier is conditional because it can change the manuscript numbers and may
increase revision work. It should be run only after Tier A and Tier B have
completed or are clearly blocked.

### C0. Timing and Storage Sanity

Run a single LW12 `800^2` fp64 strict GPU job first.

Record:

- wall-clock time
- peak memory if available
- output file size
- final-time/header check
- Slurm node and GPU model

Proceed to `1600^2` only if:

- `800^2` completes cleanly;
- projected runtime for `1600^2` fits the CSC time limit with margin;
- projected output size is acceptable;
- there is enough time left to recompute metrics and update the manuscript.

### C1. LW12 1600^2 Reference Candidate

Run matrix:

| case | resolution | precision | solver | device | output |
|---|---:|---|---|---|---|
| LW12 | 1600^2 | fp64 | HLLC | GPU strict RTX 5090 | reference candidate |
| LW12 | 1600^2 | fp64 | Rusanov | GPU strict RTX 5090 | optional reference candidate |

HLLC is the minimum required row if the report only uses HLLC for the relevant
LW12 reference comparison. Rusanov is optional unless the manuscript uses
Rusanov-specific LW12 reference-scaled metrics.

Output directory:

```text
experiments/review3_csc_lw12_1600_reference/
```

Required artefacts:

- generated cfg copies for `400^2`, `800^2`, and `1600^2` comparisons
- `environment.txt`
- `reference_manifest.json`
- `self_convergence.csv`
- `reference_scaled_ratios.csv`
- `summary.md`
- `summary.json`
- optional plots only if they replace report figures

Metrics:

- `400^2` vs block-averaged `800^2`
- `800^2` vs block-averaged `1600^2`
- observed L1 self-convergence order
- updated fp32/fp64 drift over 1600-derived reference error
- finite check and final-time/header check

Decision gate after C1:

| result | manuscript decision |
|---|---|
| 1600^2 clean and self-convergence interpretable | Replace LW12 800^2 reference numbers with 1600-derived hierarchy and update Chapter 5/6. |
| 1600^2 clean but convergence still slow | Use as evidence, but write a caveat that LW12 remains slowly convergent under L1. |
| 1600^2 fails or does not finish | Keep existing 800^2 reference and report LW12 1600^2 as deferred. |

Expected manuscript impact if accepted:

- Section 4 reference strategy: change LW12 from 800^2-only to hierarchy-backed
  numerical reference.
- Section 5 LW12 results: update reference-scaled ratios.
- Section 6 limitations: replace "LW12 lacks 1600^2 self-convergence" with a
  more precise statement about the observed hierarchy and its convergence rate.

## Tier D: Optional LW3 Timing Split

Purpose: explain why fp64 LW3 `N=400` GPU timing can be comparable to CPU timing.

Run only if profiling is easy on CSC.

Measure:

- end-to-end wall-clock time
- compute/kernel time if the code exposes timers or profiler output
- host-device transfer time if available
- GPU model, CUDA version, compiler, CPU model

Do not block the manuscript on this tier. If unavailable, phrase timing as
end-to-end implementation timing rather than peak hardware performance.

Output directory:

```text
experiments/review3_csc_lw3_timing_split/
```

## Execution Order

1. Tier A1: Toro3/Toro5 final-state CPU/GPU strict comparison.
2. Tier A2: Toro3/Toro5 checkpoint comparison, only if A1 passes.
3. Tier B: LW3 `N=400` RTX 5090 reference-path preflight.
4. Tier C0: LW12 `800^2` timing/storage sanity.
5. Tier C1: LW12 `1600^2` reference candidate, only if C0 passes.
6. Tier D: LW3 timing split, only if profiler/timer setup is low-cost.

## Stop Conditions

Stop and summarize instead of expanding the matrix if any of these occur:

- CSC queue time threatens the report deadline.
- A build or solver failure requires code changes to solver numerics.
- LW12 `800^2` timing projects `1600^2` beyond the Slurm time limit.
- Reference metrics cannot be recomputed before manuscript editing starts.
- Any result changes the conclusion enough that it needs a larger rewrite than
  the remaining word budget allows.

## CSC Prompt To Run

Use this prompt for the CSC agent/session:

```text
You are running Review 3 supplementary experiments for the floatpoint HRSC
repository on CSC. Do not edit solver numerics or source cfg defaults. Follow
the harness pipeline: config -> build -> run -> measure -> aggregate -> plot.

First read docs/INDEX.md and docs/HARNESS.md. Then execute:

1. Create experiments/review3_csc_toolchain_toro35/ and run Toro3/Toro5 strict
   HLLC CPU-vs-GPU final-state comparisons on CSC/Linux for fp64 and fp32.
   Save matrix.json, generated cfgs, environment.txt, logs, metrics.csv,
   summary.json, and summary.md. Metrics must include finite check, final-time
   check, L1, Linf, and ULPmax.

2. If step 1 passes, create
   experiments/review3_csc_toolchain_toro35_checkpoints/ and rerun Toro3/Toro5
   with generated cfg copies containing output_times at 0.25, 0.50, 0.75, and
   1.00 of each case final time. Compare CPU/GPU saved checkpoints with L1,
   Linf, and ULPmax.

3. Create experiments/review3_csc_lw3_5090_preflight/ and run LW3 N=400 fp64
   strict HLLC CPU-vs-RTX5090 GPU final-state comparison. N=800 is optional
   only if runtime is small. This is reference-path provenance, not the timing
   performance table.

4. Create experiments/review3_csc_lw12_1600_reference/. First run LW12 800^2
   fp64 strict GPU as a timing/storage sanity check. Only if it completes
   comfortably, run LW12 1600^2 fp64 strict HLLC GPU reference candidate.
   Rusanov 1600^2 is optional unless needed by existing report metrics.
   Compute 400->800 and 800->1600 L1 self-convergence, observed order, and
   updated fp32/fp64 reference-scaled ratios.

5. Optional: create experiments/review3_csc_lw3_timing_split/ and record
   end-to-end vs kernel/compute timing for LW3 N=400 fp64 if profiling is
   already available.

Do not upload report1 or build directories. Do not keep large transient grids
unless they are explicit reference candidates or needed for metrics. At the
end, produce one top-level summary with pass/fail status for each tier and
clear manuscript-use recommendations.
```

## Final Acceptance Checklist

- [ ] Every experiment directory has `environment.txt`.
- [ ] Every run uses copied/generated cfg files, not edited source cfgs.
- [ ] Every accepted comparison has scalar CSV and Markdown summary.
- [ ] Large grids are either ignored or explicitly marked as reference data.
- [ ] Toro3/Toro5 CSC CPU/GPU evidence can replace the Windows BuildTools
      evidence in the manuscript.
- [ ] LW3 RTX 5090 reference path is separated from RTX 4060 Laptop validation.
- [ ] LW12 1600^2 is used only if it completes cleanly and the metrics are
      recomputed before manuscript editing.
