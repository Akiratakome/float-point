# Week 13 HLLD GLM Sweep

This is a local diagnostic sweep for Orszag-Tang MHD GLM cleaning. HLLD remains diagnostic/deferred, and this sweep is not production adoption.

- completed runs: 2/2
- finite rho grids: 2/2
- HLLD production status: deferred

## Best finite HLLD diagnostic

- run: `hlld_glm0.18`
- glm_cr: 0.18
- divB_max: 15.91

## Runs

| run | riemann | glm_cr | rc | t | steps | divB_mean | divB_max | finite_rho | rho_min | rho_max |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| hll_glm0.18 | hll | 0.18 | 0 | 0.75 | 596 | 0.1233 | 3.36 | True | 1.64978 | 4.88361 |
| hlld_glm0.18 | hlld | 0.18 | 0 | 0.75 | 611 | 0.3026 | 15.91 | True | 1.30405 | 5.74558 |

Generated artifacts: `summary.csv`, `summary.json`, per-run `config.cfg`, `stderr.txt` logs, and `metadata.json`. `stdout.txt` is a local run artifact when non-empty. Binary grids are transient analysis inputs and are not intended for commit.
