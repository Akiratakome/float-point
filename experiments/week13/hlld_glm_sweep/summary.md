# Week 13 HLLD GLM Sweep

This is a local diagnostic sweep for Orszag-Tang MHD GLM cleaning. HLLD remains diagnostic/deferred, and this sweep is not production adoption.

- completed runs: 4/4
- finite rho grids: 4/4
- HLLD production status: deferred

## Best finite HLLD diagnostic

- run: `hlld_glm0.05`
- glm_cr: 0.05
- divB_max: 0.2431

## Runs

| run | riemann | glm_cr | rc | t | steps | divB_mean | divB_max | finite_rho | rho_min | rho_max |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| hll_glm0.05 | hll | 0.05 | 0 | 0.05 | 19 | 0.05007 | 0.3549 | True | 2.44905 | 3.61343 |
| hll_glm0.18 | hll | 0.18 | 0 | 0.05 | 19 | 0.04532 | 0.4709 | True | 2.44907 | 3.61354 |
| hlld_glm0.05 | hlld | 0.05 | 0 | 0.05 | 19 | 0.04496 | 0.2431 | True | 2.44061 | 3.71349 |
| hlld_glm0.18 | hlld | 0.18 | 0 | 0.05 | 19 | 0.04057 | 0.3397 | True | 2.44044 | 3.71361 |

Generated artifacts: `summary.csv`, `summary.json`, per-run `config.cfg`, `stderr.txt` logs, and `metadata.json`. `stdout.txt` is a local run artifact when non-empty. Binary grids are transient analysis inputs and are not intended for commit.
