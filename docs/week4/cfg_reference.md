# Week 4 cfg Reference

This is the Week-4 snapshot of runtime cfg keys used by the solver and
experiment harness. Source cfg files are never edited in place by the harness;
`scripts/run_matrix.py` copies them into each run directory before applying
run-local output settings.

## Solver Runtime Keys

| Key | Type | Default | Allowed / Meaning |
|---|---|---|---|
| `mode` | string | `normal` | `normal`, `convergence` |
| `test` | string | required | `sod`, `toro2`, `toro3`, `toro4`, `toro5`, `stationary_contact`, `lw_config3` |
| `nx`, `ny` | integer | `200`, `1` | Grid size. `ny=1` is the 1D path. |
| `xmin`, `xmax`, `ymin`, `ymax` | real | `0`, `1`, `0`, `1` | Domain bounds. |
| `gamma` | real | `1.4` | Ideal-gas ratio, must be greater than 1. |
| `cfl` | real | `0.8` | CFL factor. |
| `t_end` | real | `0.2` | End time. |
| `solver` | string | `rusanov` | `hllc` or `rusanov`. HLLC test cfgs pin this explicitly. |
| `limiter` | string | `minbee` | CPU-only opt-in limiter selection: `minbee`/`minmod`, `vanleer`/`van_leer`, `superbee`, or `vanalbada`/`van_albada`. GPU runs currently support only the default `minbee` path. |
| `bc` | string | `outflow` | Shortcut for both axes: `outflow`, `periodic`, `reflective`. |
| `bc_x`, `bc_y` | string | value of `bc` | Per-axis override for boundary conditions. |
| `resolutions` | integer list | none | Comma-separated convergence resolutions. |
| `output_format` | string | text stdout | `binary` writes a grid file. |
| `output_file` | path | none | Required when `output_format=binary`; parent directories are auto-created. |
| `output_precision` | integer | `17` | Text output precision. |

## Build Precision

| CMake option | Values | Meaning |
|---|---|---|
| `FLOAT_PRECISION` | `double`, `float` | Defines `HRSC_REAL` for one build tree. |
| `ENABLE_OPENMP` | `ON`, `OFF` | Enables OpenMP loops where available. |
| `OPT_LEVEL` | `O2`, `O3`, `Ofast` | Optional compiler optimisation axis. |
| `FAST_MATH` | `ON`, `OFF` | Optional fast-math compiler axis. |
| `RIEMANN_STRICT_INEQUALITY` | `ON`, `OFF` | HLLC branch rule `<` vs `<=`. |

## Harness Outputs

For scripted runs, keep outputs in the standard flow:

```text
config -> build -> run -> measure -> aggregate -> plot
```

Each retained experiment directory should include scalar summaries and enough
metadata to reproduce the run. Large transient grids and MCA `sample_*/grid.bin`
files are not committed.
