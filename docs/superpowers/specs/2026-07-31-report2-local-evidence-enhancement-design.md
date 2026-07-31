# Report 2 Local Evidence Enhancement Design

**Date:** 2026-07-31

**Status:** accepted design direction; implementation plan pending user review

**Goal:** strengthen the Report 2 reproducibility argument with bounded
methodology additions and one locally executable CPU/GPU workload-size
experiment, without changing solver numerics, existing configuration defaults,
or output formats.

## 1. Decision and rationale

The completed Chapters 4 and 5 already cover the required Euler/MHD, 1D/2D,
precision, solver, compiler/build, hardware, temporal, MCA, thread-count, CFL,
and resolution axes. Adding another physical case would dilute the explanation
within the remaining word budget. The selected enhancement therefore has two
parts:

1. clarify experimental units, analysis freeze, validity limits, and evidence
   traceability in Chapters 3 and 6 and the Appendix; and
2. replace the current two-workload CPU/GPU timing contrast with a unified,
   warm-up-controlled HLL packet that retains the Brio--Wu anchor and adds an
   Orszag--Tang resolution ladder.

The hardware ladder is the preferred new experiment because the existing
result changes direction between the small Brio--Wu workload and the
$256^2$ Orszag--Tang workload. A same-case $128^2/256^2/512^2$ ladder can test
whether relative CPU/GPU wall time changes with workload size without claiming
to identify a transfer, launch, I/O, or kernel-level cause.

Repeated build-semantics timing remains optional future work. It is not part of
this design because Chapter 5 is already close to its word and figure budget,
and the isolated output-semantics packet already closes the more important
causal attribution gap.

## 2. Scope

### In scope

- HLL only, using the already validated CPU and CUDA MHD paths.
- IEEE fp64 and fp32 builds.
- Brio--Wu at $N=800$, $t=0.1$, CFL 0.4, outflow boundaries.
- Orszag--Tang at $128^2$, $256^2$, and $512^2$, $t=0.5$, CFL 0.4,
  periodic boundaries and the existing GLM setting.
- CPU and GPU execution on the current RTX 5070 Laptop GPU workstation.
- One excluded warm-up and five measured repetitions per
  case/resolution/precision/device group.
- End-to-end subprocess wall time through required binary output.
- Same-precision CPU/GPU saved-state ULP and absolute-difference checks.
- Within-group repeatability, completion, step-count, and finite/positive-state
  gates.
- Machine-readable summaries, retained metadata/configs/logs, a report figure,
  evidence-map integration, and bounded manuscript interpretation.
- Chapter 3, Chapter 5, Chapter 6, and Appendix updates described below.

### Out of scope

- HLLD-on-GPU, Kelvin--Helmholtz-on-GPU, GPU MCA, or a generic GPU matrix.
- Kernel-only timing, profiler instrumentation, energy measurement, or memory
  bandwidth attribution.
- Changes to solver algorithms, arithmetic order, cfg defaults, binary layout,
  or existing historical summaries.
- Other GPUs, CPUs, compilers, operating systems, or cross-machine
  portability claims.
- A speed-up monotonicity pass criterion or a post-hoc resolution substitution.
- Build-semantics repeated timing, MPI, full-scale KH MCA, and new physical
  cases.

## 3. Manuscript content additions

### 3.1 Chapter 3: experimental units and analysis freeze

Chapter 3 keeps its existing seven-section structure and 900-word hard upper.
The new material replaces lower-value detail rather than adding a new section.

In Section 3.5, add a compact distinction between three experimental units:

- a deterministic run produces one saved numerical state and does not acquire
  a confidence interval from its grid cells;
- a timing repetition samples end-to-end runtime under one fixed binary,
  configuration, machine, and protocol; and
- an MCA sample is one stochastic-arithmetic realisation, not an independent
  physical-flow experiment.

State that grid cells are spatial observations within one run, not independent
replicates. Timing groups report median and IQR. The new workload packet uses
one excluded warm-up and five measured repetitions in every group; it remains
separate from the historical no-warm-up hardware packet. MCA sample counts and
virtual precision remain attached to every stochastic result.

In Section 3.6, add one analysis-freeze sentence: comparison baselines,
resolution cells, fit windows, scope-alignment rules, and technical gates are
declared before inspecting the new aggregate result. A negative or incomplete
outcome remains visible and does not trigger a changed window, grid, or gate.

Table 3.1 identifies the added OT CPU/GPU resolution coverage but does not list
timing values. The evidence hierarchy remains unchanged. To retain the word
budget, remove the unused numerical-SNR definition and compress repeated
metric-boundary sentences.

### 3.2 Chapter 5: hardware result integration

The new packet becomes the primary source for the repeated hardware timing
paragraph and Figure 5.3. It contains the current Brio--Wu and $256^2$
Orszag--Tang scopes under a uniform warm-up policy, plus $128^2$ and $512^2$
Orszag--Tang.

Figure 5.3 contains two panels:

1. median CPU and GPU wall time with IQR for the three OT resolutions; and
2. paired CPU/GPU median wall-time ratio versus OT resolution, with the
   $y=1$ crossover reference and a separately labelled Brio--Wu anchor.

The prose answers only whether relative device timing changes across the tested
OT resolutions. It reports saved-state agreement before interpreting timing.
It does not explain the cause of the trend and does not combine Brio--Wu and OT
into one fitted scaling law. The historical hardware packet remains provenance
and is not silently rewritten.

### 3.3 Chapter 6: threats to validity

Add one short, structured validity paragraph:

- **construct validity:** saved-state discrepancy is not exact-state accuracy,
  and subprocess time is not kernel throughput;
- **internal validity:** the matched ladder isolates case, resolution,
  precision, and device as declared, but thermal state, operating-system load,
  output cost, transfer, and launch overhead remain aggregated; and
- **external validity:** one laptop workstation, one CUDA stack, HLL, and two
  cases do not establish portable hardware performance.

This paragraph synthesises existing limitations and the new ladder. It adds no
new numerical result.

### 3.4 Appendix: environment and evidence traceability

Add one compact table mapping the hardware figure to:

- CPU/GPU model and relevant driver/CUDA/compiler versions;
- source commit and build semantics;
- binary and generated-config hashes;
- experiment summary and figure manifest;
- reproduction entry point; and
- timing scope, warm-up/repeat policy, and retained/deleted artefacts.

The Appendix supplies routing, not a command catalogue. Large grids remain
transient after their metrics and hashes have been recorded.

## 4. Experiment matrix and protocol

### 4.1 Matrix

The packet contains 16 measured groups:

| Case scope | Resolutions | Precisions | Devices | Groups |
|---|---|---|---|---:|
| Brio--Wu | $N=800$ | fp64, fp32 | CPU, GPU | 4 |
| Orszag--Tang | $128^2$, $256^2$, $512^2$ | fp64, fp32 | CPU, GPU | 12 |

Each group has one warm-up plus five measured runs. Warm-ups retain config,
stdout/stderr, status, and timing metadata for audit but do not enter medians,
IQRs, or repeat counts. The full execution therefore consists of 16 warm-ups
and 80 measured runs.

HLL, CFL, end time, boundary conditions, GLM parameters, effective build
semantics, source commit, and output requirements remain fixed within each
case/resolution/precision CPU/GPU comparison. CPU runs set and record
`OMP_NUM_THREADS=1`; GPU runs record the same requested thread environment as
non-operative context rather than treating it as a GPU tuning axis.

### 4.2 Execution order

The design uses blocked paired repetitions to reduce systematic ordering bias:

1. execute one warm-up for every group;
2. for each case/resolution/precision cell, run five CPU/GPU pairs;
3. alternate device order between odd and even repeat numbers; and
4. record pair identifier, execution order, start/end time, and environment in
   metadata.

The pairing supports a median and IQR of the five CPU/GPU time ratios as well
as separate CPU and GPU medians. It does not make the five repetitions
independent hardware environments.

### 4.3 Metrics

For every measured run, record:

- completion status, final time, steps, precision tag, and required output;
- finite/positive-state diagnostics and existing divergence diagnostics;
- subprocess wall time including launch, solver execution, transfer where
  applicable, and required binary output;
- binary and generated-config hashes; and
- case, resolution, precision, device, repeat, pair, and execution order.

For every same-precision CPU/GPU pair, compute maximum ULP and absolute
$L_\infty$ over the saved conservative state. For each device group, compare
measured repeats with the first measured run to establish within-group saved-
state repeatability.

Aggregates report:

- CPU and GPU median wall time and IQR;
- the median and IQR of paired CPU/GPU wall-time ratios;
- maximum CPU/GPU ULP and absolute $L_\infty$;
- maximum within-group repeat ULP;
- matched step-count status; and
- complete/failed group counts.

No fitted hardware-scaling exponent is required. The three OT resolutions are
a bounded workload ladder, not a performance model.

## 5. Harness and artefact design

Implement the packet as a new dedicated workflow rather than changing the
stored Week-18 summary contract. Use these locations:

- driver/aggregator/plotter:
  `scripts/regression/mhd_hardware_workload_ladder.py`;
- tests: `tests/py/test_mhd_hardware_workload_ladder.py`;
- outputs: `experiments/week20/hardware_workload_ladder/`.

The workflow reuses the canonical MHD run, binary-reading, field, and ULP
helpers. It emits:

- `summary.json`, `summary.csv`, and `summary.md`;
- `figures/hardware_workload_ladder.png` and vector PDF;
- generated configs, stdout/stderr, and metadata for warm-up and measured runs;
- an experiment lifecycle manifest; and
- no retained `grid.bin` files after successful measurement unless a failed
  pair requires bounded debugging and is explicitly recorded.

The schema must distinguish warm-up and measured records. Resume uses exact
identity over source commit, binary hash, generated-config hash, case,
resolution, precision, device, repeat role, and repeat number. A stale or
partially matching record is not reused.

## 6. Preconditions and gates

### 6.1 Build and smoke preconditions

Before timing:

1. cleanly configure and build the four CPU/CUDA fp64/fp32 binaries from the
   same source commit, or prove their freshness and effective semantics through
   the existing build records;
2. record compiler, CUDA toolkit, driver, CPU, GPU, and operating-system data;
3. run the relevant CPU tests and CUDA GPU smoke tests; and
4. execute one Brio--Wu and one OT $128^2$ smoke per precision/device, followed
   by one OT $512^2$ GPU smoke per precision.

A smoke failure stops the full matrix. Resolutions, tolerances, and grids are
not changed to obtain a positive result.

### 6.2 Technical gate

The technical gate requires:

- all 16 warm-ups and all 80 measured runs recorded;
- every measured run completion-attested at the declared final time;
- finite conservative states with positive density and thermal pressure;
- correct fp32/fp64 output precision tags;
- matching CPU/GPU step counts within each paired cell;
- all required metadata, hashes, logs, and summaries present; and
- exactly five measured repetitions per group.

### 6.3 Correctness gate

The report-facing hardware timing gate additionally requires zero maximum ULP
and zero absolute difference for each same-precision CPU/GPU saved-state pair,
consistent with the already validated HLL path. It also requires zero
within-group repeat ULP. If a non-zero value occurs, retain the packet as a
bounded diagnostic and investigate before using its timing as headline
evidence; do not silently widen a tolerance.

### 6.4 Result-neutral gate

The gate does **not** require GPU speed-up, a crossover, monotonic growth of the
CPU/GPU ratio, or fp32/fp64 ordering. Any complete and technically valid trend,
including a flat or negative one, is reportable.

## 7. Failure handling and stopping rules

- The full packet begins only after reduced smokes pass.
- The local execution budget is two hours of solver wall-clock time. If this
  budget is reached, finish the active CPU/GPU pair, stop, retain all metadata,
  and mark the matrix incomplete.
- CUDA out-of-memory, non-finite state, missing completion, step mismatch, or
  saved-state drift stops dependent runs for the affected cell and preserves
  its artefacts.
- A failed $512^2$ cell is not replaced by $384^2$ or a shorter final time.
- Interrupted valid groups may resume only through exact metadata identity.
- Incomplete or failed evidence may be mentioned as a limitation but does not
  replace the current report-grade hardware result.

## 8. Verification strategy

Before real runs, automated tests cover:

- exact 16-group matrix construction and 80 measured records;
- warm-up exclusion from aggregates;
- alternating CPU/GPU order and pair identifiers;
- config generation for Brio--Wu and all OT resolutions;
- precision/device binary selection and recorded thread environment;
- median/IQR and paired-ratio aggregation;
- ULP, absolute-difference, step-count, completion, and physical-state gates;
- resume identity and stale-record rejection;
- summary schema, CSV/Markdown rendering, figure creation, and grid cleanup;
- result-neutral behaviour for speed-up, crossover, and ordering; and
- fake-run integration from config generation through retained summaries.

After implementation, verification proceeds in this order:

1. targeted Python tests for the new workflow;
2. existing harness, MHD hardware-axis, supplemental, manifest, and publication-
   figure tests;
3. clean CPU unit tests and CUDA GPU smoke tests;
4. reduced real smokes;
5. full local matrix;
6. independent aggregation from retained metadata;
7. evidence-map, figure-manifest, manuscript, bibliography, and PDF build tests;
8. manual inspection of the vector PDF, table/figure references, claim
   boundaries, and standalone Report 2 word count.

## 9. Deliverables and completion criteria

Completion requires:

- the tested workload-ladder workflow and lifecycle manifest;
- a complete, machine-readable 16-group/80-measurement packet, or an explicitly
  bounded failed/incomplete packet;
- audited PNG/PDF figure assets and updated figure manifest;
- updated evidence map and experiment index routing;
- Chapter 3 experimental-unit and analysis-freeze text within its 900-word cap;
- Chapter 5 hardware result and figure integration without duplicating the old
  packet;
- Chapter 6 validity synthesis;
- Appendix environment/provenance routing;
- passing relevant tests and standalone LaTeX/BibTeX compilation; and
- student rewrite, fact-check, and final Overleaf word-count approval.

The enhancement is successful if it yields a complete result-neutral hardware
ladder whose interpretation remains bounded to the tested HLL cases,
resolutions, precisions, device implementations, timing scope, and workstation.
If a hard gate fails, success instead means the failure is fully preserved and
the existing report-grade claims remain unchanged.
