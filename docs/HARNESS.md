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

A run is reportable only after the application completion gate has passed, the
required artifacts are valid and fresh, the process return code is zero, and
the normalized metadata status is `success`. A zero return code alone does not
override an explicit structured failure or an incomplete completion record.

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
| MHD / GPU | unsupported | fail explicitly; no GPU MHD implementation is implied |

## Experiment Manifests And Retention

Report 2 experiment lifecycle manifests use
`hrsc.experiment-manifest` schema version 1 and one of five lifecycle values:
`canonical`, `provenance`, `superseded`, `invalid`, or `generated`.
Validate all committed manifests from the repository root with:

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

The canonical CPU matrix remains the default harness path. The Euler CUDA
correctness path exists, but a report-grade generic GPU matrix and MHD GPU path
are not yet complete. Hardware-axis conclusions therefore remain deferred; see
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
