# Week 13 HLLD GLM Sweep

This is a local diagnostic sweep for Orszag-Tang MHD GLM cleaning. HLLD remains diagnostic/deferred, and this sweep is not production adoption.

- completed runs: 2/2
- finite rho grids: 2/2
- HLLD production status: deferred

## Best finite HLLD diagnostic

- run: `hlld_glm0.18`
- glm_cr: 0.18
- divB_max: 9.948

## Runs

| run | riemann | glm_cr | rc | t | steps | divB_mean | divB_max | finite_rho | rho_min | rho_max |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| hll_glm0.18 | hll | 0.18 | 0 | 1 | 803 | 0.09361 | 0.8427 | True | 1.16049 | 4.09833 |
| hlld_glm0.18 | hlld | 0.18 | 0 | 1 | 835 | 0.3258 | 9.948 | True | 0.837919 | 4.37597 |

Generated artifacts: `summary.csv`, `summary.json`, per-run `config.cfg`, `stderr.txt` logs, and `metadata.json`. `stdout.txt` is a local run artifact when non-empty. Binary grids are transient analysis inputs and are not intended for commit.
