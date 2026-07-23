# HRSC Experiment Harness

This repository is an experiment harness. The solver is one component; the
pipeline is the deliverable.

Canonical pipeline:

```text
config -> build -> run -> measure -> aggregate -> plot
```

## Entry Points

For script ownership and legacy/provenance boundaries, see
`scripts/README.md`.

| Step | Canonical entry |
|---|---|
| Build matrix | `scripts/build_all.sh` |
| Run matrix | `python scripts/run_matrix.py <matrix.json>` |
| Aggregate summaries | `python scripts/aggregate_metrics.py --output <out.json> <summary.json>...` |
| Existing 1D regression | `bash scripts/regression/float_regression_1d.sh` |
| Existing 2D regression | `bash scripts/regression/float_regression_2d.sh` |
| Matrix scalar report | `python scripts/regression/matrix_summary_report.py <matrix_summary.json>` |
| 2D plotting | `python scripts/figures/plot_2d.py <grid.bin> --field rho --out <figure.png>` |
| Experiment lifecycle audit | `python scripts/audit_experiments.py --format markdown` |

## Run Contract

New harness metadata uses schema `{"name": "hrsc.run-record", "version": 1}`.
The canonical fields are `status`, `artifacts.primary_output`,
`timing.elapsed_wall_s`, `failure`, `completion`, and `build_semantics`.
Legacy fields remain accepted and are normalized without changing their stored
values:

| Canonical field | Legacy aliases |
|---|---|
| `artifacts.primary_output` | `raw_output`, `output_binary` |
| `timing.elapsed_wall_s` | top-level `elapsed_wall_s`, `timing.total_s` |
| `status` | inferred from `returncode` when absent |

Migrated Euler and MHD application paths emit structured completion/success
status after the application completion gate (`require_run_complete`) gates
their final outputs. Their metadata
has `status=success`, `completion.reported=true`, and the required structured
completion fields. The generic runner also preserves legacy zero-returncode
records from programs that emit no structured status; those records remain
`status=success` with `completion.reported=false`.

The current generic `matrix_summary_report.py` consumer calls
`require_successful_metadata` for compatibility. That function accepts
normalized legacy success and does **not** enforce `completion.reported=true`;
its output alone is not completion-attested. Any workflow making a
completion-attested or report-grade claim must explicitly filter or validate
`completion.reported=true`, the required completion fields, and the required
fresh artifacts. This distinction documents consumer policy without changing
the generic runner or compatibility behavior.

## Build Semantics

Historical build directory names remain stable, including names such as
`Ofast-ieee`. They are labels, not proof of the compiler mode. The harness
records the effective math mode separately in `build_semantics` (`strict`,
`fast`, or `compiler-default`) together with requested axes and compiler
evidence.

| Application/device | Support status | Entry rule |
|---|---|---|
| Euler / CPU | supported; default | standard CPU matrix |
| Euler / GPU | supported as opt-in CUDA correctness path | explicitly enable CUDA |
| MHD / CPU | supported | use the MHD application contract |
| MHD / GPU | supported as bounded HLL correctness path | opt-in CUDA path; Brio-Wu and Orszag-Tang only |

## Experiment Manifests And Retention

Report 2 experiment lifecycle manifests use
`hrsc.experiment-manifest` schema version 1 and one of five lifecycle values:
`canonical`, `provenance`, `superseded`, `invalid`, or `generated`.
Validate the 13 promoted Report 2 lifecycle manifests enumerated by Task 9
from the repository root with:

```bash
python -m pytest tests/py/test_experiment_manifests.py -q
```

The current cleanup audit is read-only and reports candidates for a separate
reference check at
[`experiment_cleanup_candidates.md`](experiment_logs/experiment_cleanup_candidates.md).

## Build Axes

`scripts/build_all.sh` creates CPU builds under `build-matrix/` for:

- precision: `double`, `float`
- optimisation: `O2`, `O3`, `Ofast`
- fast math: `OFF`, `ON`
- HLLC branch rule: `<=`, `<`

The canonical CPU matrix remains the default harness path. Euler CUDA and
opt-in HLL MHD CUDA correctness paths exist. Week 16 adds a bounded matched
CPU/GPU HLL hardware-axis packet for Brio-Wu 1D and Orszag-Tang 2D, but a
generic GPU matrix, HLLD-on-GPU, KH-on-GPU, and GPU MCA remain out of scope; see
`docs/experiment_logs/report2_evidence_map.md`.

## Run Matrix Schema

Minimal JSON:

```json
{
  "experiment": "week5-smoke",
  "output_root": "experiments/week5/smoke",
  "runs": [
    {
      "name": "sod-double",
      "binary": "build-double/hrsc",
      "config": "tests/cases/toro_1d/sod.cfg",
      "precision": "double",
      "build": "cpu-double-O2-ieee-leq",
      "output_file": "grid.bin"
    }
  ]
}
```

For each run, `run_matrix.py` writes:

- `config.cfg`: copied source cfg, with `output_format=binary` and
  `output_file=<run_dir>/<output_file>` only when `output_file` is requested.
- `stdout.txt` and `stderr.txt`
- `metadata.json`: experiment name, git commit, binary, source cfg, generated
  cfg, precision, build label, command, return code, and raw output path.

The source cfg is never edited in place.

## Output Discipline

Each experiment directory should keep:

- run metadata
- scalar summaries (`summary.csv`, `summary.json`, `summary.md`)
- report figures

Large grids are transient unless they are explicit reference data needed to
reproduce a metric. If a grid is not analysed, do not keep it.

## Script Path Discipline

Many docs, tests, shell scripts, and experiment logs invoke scripts by path.
Do not physically move established script entry points during an experiment
unless the matching tests, cluster scripts, and canonical docs are updated in the
same change. Historical logs under `docs/experiment_logs/` and
`experiments/**/summary.md` are provenance; prefer adding a current pointer over
rewriting old commands.

## Compatibility Rule

The harness must not change existing solver defaults or existing cfg output.
New CMake flags in `cmake/CompilerFlags.cmake` are opt-in: default CMake builds
keep the previous compiler behaviour unless `OPT_LEVEL` or `FAST_MATH` is
passed explicitly.
