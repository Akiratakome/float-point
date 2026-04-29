# HRSC Experiment Harness

This repository is an experiment harness. The solver is one component; the
pipeline is the deliverable.

Canonical pipeline:

```text
config -> build -> run -> measure -> aggregate -> plot
```

## Entry Points

| Step | Canonical entry |
|---|---|
| Build matrix | `scripts/build_all.sh` |
| Run matrix | `python scripts/run_matrix.py <matrix.json>` |
| Aggregate summaries | `python scripts/aggregate_metrics.py --output <out.json> <summary.json>...` |
| Existing 1D regression | `bash scripts/regression/float_regression_1d.sh` |
| Existing 2D regression | `bash scripts/regression/float_regression_2d.sh` |

## Build Axes

`scripts/build_all.sh` creates CPU builds under `build-matrix/` for:

- precision: `double`, `float`
- optimisation: `O2`, `O3`, `Ofast`
- fast math: `OFF`, `ON`
- HLLC branch rule: `<=`, `<`

GPU is intentionally not included in the first harness pass because the GPU
solver is still a Week 5/6 bring-up item.

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

## Compatibility Rule

The harness must not change existing solver defaults or existing cfg output.
New CMake flags in `cmake/CompilerFlags.cmake` are opt-in: default CMake builds
keep the previous compiler behaviour unless `OPT_LEVEL` or `FAST_MATH` is
passed explicitly.
