# Week 18 Bilingual Supervisor Report and Supplemental Experiments Design

## Purpose

Produce English and Chinese supervisor-meeting documents that mirror the
content form of `docs/week14/week14-supervisor-meeting-EN.md`, while reporting
the current Week 16/17 evidence and three focused supplemental experiments.
The documents must be suitable for speaking directly in a meeting and must
state claim boundaries next to every result.

## Deliverables

- `docs/week18/week18-supervisor-meeting-EN.md`
- `docs/week18/week18-supervisor-meeting-ZH.md`
- Three reproducible supplemental evidence packets under
  `experiments/week18/`
- Publication-style figures generated from machine-readable summaries
- CSC Slurm entries for experiments that require the remote GPU or full
  Verificarlo MCA runtime

## Required Report Form

Both language versions use the Week 14 sequence and level of detail:

1. document title and dated evidence note;
2. `One-line summary`;
3. `What we actually did`;
4. `The figures: how to read them, what they show`;
5. `What we can tell the supervisor (and what we won't)`;
6. `Next steps`;
7. `References`.

Each figure subsection begins with a one-line conclusion, explains axes and
marks, states what the evidence establishes, and ends with an explicit
interpretation boundary where needed. The Chinese version is a faithful
technical counterpart of the English version, not a shortened summary.

## Evidence Narrative

The report presents only bounded conclusions supported by current summaries:

- precision is the dominant observed axis in the committed packets;
- CPU and GPU are bit-exact for the covered same-precision HLL Brio-Wu and
  Orszag-Tang runs, while GPU speedup is meaningful only for the 2D case;
- the fixed-window temporal-divergence study did not observe the planned
  Orszag-Tang-greater-than-Brio-Wu contrast;
- Kelvin-Helmholtz has completed deterministic precision and 256-to-512
  validation evidence;
- reduced 64-squared Kelvin-Helmholtz MCA supports toolchain and noise-floor
  feasibility only;
- full 256-squared, t=1.0, N=30 Kelvin-Helmholtz MCA remains unclaimed until
  the CSC jobs complete;
- two resolutions do not establish asymptotic convergence.

## Supplemental Experiments

### Repeated Hardware Timing

Repeat the covered CPU/GPU HLL cases for both precisions and report median
wall time, interquartile range, per-run speedup, and same-precision ULP
agreement. A timing conclusion is reportable only when all runs complete,
the existing correctness gate remains satisfied, and the requested repeat
count is present. Remote GPU execution is routed through Slurm when the local
GPU environment is unavailable.

### Two-Dimensional Thread Reproducibility

Run the selected Orszag-Tang and Kelvin-Helmholtz CPU HLL cases with
`OMP_NUM_THREADS` equal to 1, 2, 4, and 8 in float and double. Compare each
saved solution with the same-precision single-thread result using exact
equality, ULP maximum, and absolute norms. The experiment measures
implementation reproducibility only; it does not imply MPI reproducibility.

### Kelvin-Helmholtz CFL Sensitivity

Run Kelvin-Helmholtz with CFL values 0.2, 0.4, 0.6, and 0.8 for HLL and HLLD
in float and double, using copied generated configs rather than changing the
canonical case config. Measure completion, steps, wall time, physical-state
checks, divergence diagnostics, and fp32-versus-fp64 density differences
within each CFL value. The analysis separates time-step sensitivity from the
precision comparison without claiming formal temporal convergence.

## Pipeline and Storage

Every experiment follows:

`config -> build -> run -> measure -> aggregate -> plot`

Each packet retains generated configs, run metadata, logs, `summary.json`,
`summary.csv`, `summary.md`, and figures. Large `grid.bin` files are removed
after measurement unless an explicit retained reference is required. Existing
solver numerics, output schemas, and cfg defaults remain unchanged.

## Failure and Claim Handling

Incomplete local or CSC runs remain machine-readable blocked results and do
not silently disappear. The report distinguishes measured results from queued
or planned work. A supplemental figure is included as evidence only after its
summary gate passes; otherwise the meeting document identifies it as pending
and preserves the existing no-claim boundary.

## Verification

- Unit tests cover generated matrix shape, copied-config overrides,
  aggregation gates, and report data-source references.
- Shell and Slurm scripts pass syntax checks.
- Every number in both meeting documents is checked against a named
  `summary.json`.
- English and Chinese documents contain matching figure order, numerical
  values, supported claims, excluded claims, and references.
- Figures are visually inspected for legibility and misleading encodings.

