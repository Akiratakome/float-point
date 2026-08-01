# Project Architecture Convergence Design

**Date:** 2026-07-22  
**Status:** Approved design  
**Scope:** Harness, application interfaces, documentation, and experiments

## Context

The repository is a numerical experiment harness whose deliverable is the full
`config -> build -> run -> measure -> aggregate -> plot` pipeline. Euler already
uses shared helpers under `src/app`, while MHD has a separate executable and a
separate Python regression harness. Those paths duplicate configuration
materialization, process execution, provenance capture, output handling, and
completion checks. Compiler matrix labels also treat `Ofast` and `FAST_MATH` as
if they were independent even though `Ofast` already enables fast floating-point
semantics on supported compilers.

The experiment tree contains valuable historical evidence as well as generated
artifacts. Its lifecycle is currently inferred mainly from paths and prose. That
makes cleanup risky and makes it harder for tooling to decide which results are
authoritative.

## Goals

1. Establish one additive, versioned contract for build, run, provenance, and
   completion metadata.
2. Make Euler and MHD use common application-level configuration, output,
   diagnostics, and completion interfaces without changing solver numerics.
3. Preserve existing script paths, configuration defaults, binary formats, and
   summary fields.
4. Record actual compiler and floating-point semantics for new runs.
5. Give experiment packages a machine-readable lifecycle and retention policy.
6. Clarify the responsibility of the project index, harness guide, evidence
   maps, and weekly working notes.

## Non-Goals

- Expanding the bounded GPU HLL MHD path into a generic GPU matrix, including
  HLLD-on-GPU, Kelvin--Helmholtz-on-GPU, or GPU MCA.
- Changing numerical expressions, algorithms, tolerances, or existing cfg
  defaults.
- Renaming or moving historical experiment packages in bulk.
- Rewriting historical result metadata or relabeling historical directories.
- Deleting generated or nested build artifacts during the convergence change.
- Promoting single-run GPU wall-clock measurements as report-grade performance
  evidence; performance claims require the later matched repeated-run protocol.

## Chosen Approach

Use contract-first staged convergence. Shared contracts and compatibility tests
are introduced first. Existing Euler, MHD, and regression entry points then
adapt to those contracts incrementally. Directory cleanup follows only after
the contracts and reference audit exist.

This approach has a lower numerical and evidence risk than moving application
code first, and it avoids the broken links and ambiguous provenance that would
result from directory-first cleanup.

## Target Architecture

```text
experiment definition
        |
        v
shared harness contracts
  config overlay
  build semantics
  run record / metadata
  completion gates
        |
        +--------------------+
        |                    |
        v                    v
   Euler app adapter    MHD app adapter
        |                    |
        v                    v
   CPU / existing GPU   CPU / bounded HLL GPU
        |
        v
measure -> aggregate -> plot
        |
        v
experiment manifest + evidence map
```

### Python Harness Boundary

`scripts/harness/` owns non-numerical runner infrastructure:

- typed run and build records;
- cfg overlay materialization;
- subprocess execution and timeout handling;
- Git and environment provenance capture;
- metadata serialization and compatibility reading;
- completion and required-artifact gates.

`scripts/run_matrix.py` remains the canonical generic matrix entry point.
`scripts/regression/_mhd_harness.py` keeps its import path and public behavior,
but becomes a compatibility facade over the shared harness. Existing callers do
not need to migrate in the same commit.

### C++ Application Boundary

`src/app/` owns application-level interfaces shared by Euler and MHD:

- parsing and validating common run configuration;
- selecting output behavior and writing established output formats;
- collecting application diagnostics;
- reporting run progress and completion status.

Euler and MHD adapters translate the common interface into solver-specific
configuration. Numerical algorithms remain in their current numerical modules.
No solver source is moved merely to make the directory tree look symmetric.

## Harness Contracts

### RunSpec

`RunSpec` describes requested execution rather than observed results. It
contains the executable, source cfg, cfg overrides, device, output locations,
timeout, working directory, and required artifacts. The original cfg remains
unchanged; overrides are materialized into a run-local cfg.

### BuildSemantics

`BuildSemantics` records both requested build controls and effective behavior:

- compiler identity and version;
- build type and optimization level;
- requested `FAST_MATH` value;
- compiler flags relevant to floating-point behavior;
- effective math mode, such as `strict`, `precise`, or `fast`;
- evidence used to derive the effective mode.

For new runs, `Ofast` is always represented as effective fast math where the
toolchain maps it to `-Ofast` or equivalent. `Ofast + FAST_MATH=OFF` is not
described as IEEE. Existing paths and historical labels are retained and are
not reinterpreted in place.

### RunRecord

`RunRecord` describes observed execution. Its canonical fields include:

- schema name and version;
- run identity and timestamps;
- command and working directory;
- Git commit and dirty-state indication;
- requested `RunSpec` and effective `BuildSemantics`;
- process exit code, standard output, standard error, and elapsed wall time;
- final simulation state needed for completion checks;
- status, structured failure reason, and produced artifacts.

Serialization is additive. Readers accept current legacy aliases including
`raw_output` and `output_binary`, and `timing.total_s` and `elapsed_wall_s`.
Writers retain legacy fields required by existing summaries while adding the
canonical representation. Historical files are not bulk rewritten.

### Completion Gate

A run is successful only when all applicable conditions hold:

1. the process exits successfully;
2. final time, time step, and required diagnostics are finite;
3. final time reaches `t_end` within the established application tolerance;
4. required artifacts exist and can be parsed;
5. the selected capability is supported.

Aggregation rejects incompatible schemas, unsuccessful runs, and incomplete
required artifacts by default. Any future override must be explicit and must be
recorded in aggregate metadata.

## Device Behavior

The common application configuration recognizes `device=cpu|gpu`. Existing cfg
files that omit it continue to select CPU.

- Euler keeps its existing CPU and GPU paths. A GPU run that stops before
  `t_end`, encounters a non-finite time step, or otherwise fails the completion
  gate returns failure and cannot produce an authoritative successful record.
- MHD defaults to CPU and exposes an opt-in CUDA path only for `riemann=hll`.
  The validated application scope is Brio--Wu 1D and Orszag--Tang 2D in fp32
  and fp64. HLLD-on-GPU is rejected before simulation; Kelvin--Helmholtz and a
  generic GPU experiment matrix remain outside the validated evidence scope.

This design separates the shared interface from the deliberately bounded GPU
MHD capability. A supported dispatch path is not evidence for unvalidated
case, solver, precision, or performance combinations.

## Error Model

Errors are classified so callers can distinguish invalid experiments from
solver failures and infrastructure failures:

- `configuration_error`: invalid or inconsistent input detected before run;
- `unsupported_capability`: valid request not implemented by the selected app;
- `numerical_failure`: non-finite state, invalid time step, or solver-reported
  numerical failure;
- `incomplete_run`: process returned without reaching the requested end state;
- `infrastructure_error`: launch, timeout, filesystem, or process failure;
- `artifact_error`: required output missing or unparsable;
- `schema_error`: metadata cannot be safely consumed.

Failure records retain the command, process status, standard output, standard
error, and available provenance. Failed or incomplete results are not promoted
into successful aggregates.

## Experiment Lifecycle

Each promoted experiment package gains a lightweight manifest. The manifest
records:

- experiment ID, report ownership, and purpose;
- entry points for config, build, run, measure, aggregate, and plot;
- inputs, outputs, and required evidence artifacts;
- Git, platform, compiler, and tool provenance where applicable;
- lifecycle status and retention policy;
- replacement reference when superseded.

Allowed lifecycle states are:

- `canonical`: current authoritative evidence or reproducible workflow;
- `provenance`: retained to explain or reproduce canonical evidence;
- `superseded`: valid historical work replaced by an identified package;
- `invalid`: retained for audit but excluded from conclusions and aggregation;
- `generated`: reproducible output that is not itself a source definition.

Lifecycle is determined by the manifest, not solely by directory naming.
Manifests are added incrementally to formal experiment packages; the design does
not require every historical scratch directory to be normalized immediately.

The 36 known nested build directories are registered as cleanup candidates.
References are audited before deletion. Any deletion occurs in a separate,
reviewable commit and never removes report evidence or required provenance.

## Documentation Responsibilities

- `docs/INDEX.md` is the project navigation and points to current authoritative
  architecture, harness, report, and evidence entry points.
- `docs/HARNESS.md` defines the pipeline, shared contracts, metadata schema,
  compatibility guarantees, and normal invocation paths.
- Report evidence maps connect claims to canonical experiment artifacts; they
  do not redefine the harness architecture.
- Weekly documents remain chronological work records and do not act as the
  current project architecture specification.

Documentation links use stable existing paths. Historical references are
preserved unless a verified replacement and compatibility path exist.

## Migration Sequence

1. Add contract and compatibility tests for metadata, cfg overlays, and legacy
   imports.
2. Introduce shared Python harness contracts and migrate `run_matrix.py`.
3. Convert the MHD regression harness into a compatibility facade.
4. Add common C++ application configuration, diagnostics, output, and completion
   interfaces; adapt Euler and MHD without altering numerical kernels.
5. Enforce Euler GPU completion and the bounded MHD GPU HLL capability gate.
6. Record effective compiler/math semantics for new matrix runs.
7. Add manifests to promoted experiment packages and update project docs.
8. Produce the nested-build reference audit and cleanup candidate report.

Each phase must leave existing public paths usable and must pass its focused
compatibility tests before the next phase begins.

## Verification

### Contract Tests

- Legacy and canonical metadata both deserialize into the same canonical model.
- Writers preserve fields consumed by existing scripts and summaries.
- Config overlays do not mutate source cfg files or change unspecified defaults.
- Old MHD harness imports and invocation paths remain valid.
- Unsupported, incomplete, and failed runs cannot enter successful aggregates.

### Application Tests

- Existing Euler and MHD CPU baselines remain unchanged within their current
  established comparisons.
- Euler GPU returns failure when it does not reach `t_end` or observes a
  non-finite time step.
- MHD defaults to CPU; the CUDA-enabled HLL path passes its bounded Brio--Wu
  and Orszag--Tang CPU/GPU checks, while HLLD-on-GPU is rejected.
- Existing binary output and summary formats remain readable by current tools.

### Build Tests

- `Ofast` records effective fast floating-point semantics even when
  `FAST_MATH=OFF`.
- Existing build matrix paths remain available.
- Test source discovery updates when new unit tests are added; CMake discovery
  behavior is corrected without changing production target semantics.

### Documentation and Experiment Tests

- Manifests validate against the defined schema and allowed lifecycle states.
- Canonical evidence paths exist and remain linked from their evidence maps.
- Relative Markdown links pass the repository link audit.
- Generated/build cleanup candidates are reported separately from retained
  evidence.

### Verification Commands

The implementation plan will select repository-native commands for focused
tests, followed by the complete Python suite and CPU C++ suite. CUDA tests run
when the environment provides a supported toolchain and device; otherwise the
skip and its reason are recorded. No report evidence is regenerated merely to
complete the architecture convergence.

## Acceptance Criteria

The convergence is complete when:

1. one shared harness contract serves generic matrix and MHD regression paths;
2. existing public paths, cfg defaults, binary formats, and summary fields are
   compatible;
3. Euler and MHD expose common application-level run behavior while numerical
   kernels remain unchanged;
4. incomplete Euler GPU runs and unsupported MHD GPU combinations cannot be
   recorded as success, while the bounded HLL GPU path remains opt-in;
5. new builds record effective floating-point semantics correctly;
6. promoted experiments have validated lifecycle manifests;
7. project docs have non-overlapping responsibilities and valid links;
8. nested build artifacts have an audited cleanup report, with deletion deferred
   to a separate commit;
9. focused and full available test suites pass, with unavailable CUDA coverage
   explicitly documented.
