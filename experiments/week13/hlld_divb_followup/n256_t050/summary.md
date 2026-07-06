# Week 13 HLLD GLM Sweep

This is a local diagnostic sweep for Orszag-Tang MHD GLM cleaning. HLLD remains diagnostic/deferred, and this sweep is not production adoption.

- completed runs: 1/1
- finite rho grids: 1/1
- HLLD production status: deferred

## Best finite HLLD diagnostic

- run: `hlld_glm0.18`
- glm_cr: 0.18
- divB_max: 24.45

## Runs

| run | riemann | glm_cr | rc | t | steps | divB_mean | divB_max | finite_rho | rho_min | rho_max |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| hlld_glm0.18 | hlld | 0.18 | 0 | 0.5 | 812 | 0.274 | 24.45 | True | 1.16554 | 6.19707 |

Generated artifacts: `summary.csv`, `summary.json`, per-run `config.cfg`, `stderr.txt` logs, and `metadata.json`. `stdout.txt` is a local run artifact when non-empty. Binary grids are transient analysis inputs and are not intended for commit.
