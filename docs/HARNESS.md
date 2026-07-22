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
