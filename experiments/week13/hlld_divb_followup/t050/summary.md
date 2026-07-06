# Week 13 HLLD GLM Sweep

This is a local diagnostic sweep for Orszag-Tang MHD GLM cleaning. HLLD remains diagnostic/deferred, and this sweep is not production adoption.

- completed runs: 4/4
- finite rho grids: 4/4
- HLLD production status: deferred

## Best finite HLLD diagnostic

- run: `hlld_glm0`
- glm_cr: 0
- divB_max: 12.71

## Runs

| run | riemann | glm_cr | rc | t | steps | divB_mean | divB_max | finite_rho | rho_min | rho_max |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| hll_glm0.18 | hll | 0.18 | 0 | 0.5 | 396 | 0.1364 | 1.734 | True | 1.28977 | 4.89142 |
| hll_glm0 | hll | 0 | 0 | 0.5 | 397 | 0.1497 | 2.134 | True | 1.28564 | 4.88783 |
| hlld_glm0.18 | hlld | 0.18 | 0 | 0.5 | 401 | 0.3184 | 13.53 | True | 1.28129 | 6.04506 |
| hlld_glm0 | hlld | 0 | 0 | 0.5 | 401 | 0.316 | 12.71 | True | 1.27762 | 6.05971 |

Generated artifacts: `summary.csv`, `summary.json`, per-run `config.cfg`, `stderr.txt` logs, and `metadata.json`. `stdout.txt` is a local run artifact when non-empty. Binary grids are transient analysis inputs and are not intended for commit.
