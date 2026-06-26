# Week 13 MHD Verificarlo Smoke

Status: `completed`

Produced 3 Verificarlo MCA sample grids with runner `docker`.

- runner: `docker`
- samples: 3
- rho_mean_spread: 2.220446049250313e-16

## Samples

| sample | rc | grid_status | rho_min | rho_max | rho_mean |
|---|---:|---|---:|---:|---:|
| sample_01 | 0 | read | 0.11716054488890904 | 1.0 | 0.5624999999999999 |
| sample_02 | 0 | read | 0.11716054488890926 | 0.9999999999999999 | 0.5624999999999998 |
| sample_03 | 0 | read | 0.11716054488890867 | 1.0 | 0.5625 |

Generated artifacts include `environment.json`, `summary.json`, per-sample `config.cfg`, logs, and `metadata.json`. Binary grids are transient.
