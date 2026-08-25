# Scripts Architecture

This directory is the experiment harness layer. Keep new work in the existing
pipeline shape:

```text
config -> build -> run -> measure -> aggregate -> plot
```

The solver lives under `src/`; scripts should configure, execute, measure, and
summarise runs without changing solver numerics or cfg defaults.

## Canonical Entry Points

Use these first for new Report 2 work.

| Step | Script | Notes |
|---|---|---|
| Build | `build_all.sh`, `build_matrix.py` | CPU build matrix and build labels. |
| Run | `run_matrix.py` | Copies cfgs into run directories, writes metadata, and never edits source cfgs. |
| Run (LLM workload) | `aiinfra/run_workload.py` | Matrix entry point for workload family 2; writes a validated `workload_result.json` beside its config. |
| Probe (environment) | `aiinfra/environment.py` | Read-only device/toolchain probe. Installs nothing, downloads nothing. |
| Shared harness contracts | `harness/` | Versioned run metadata, config materialization, process execution, build semantics, and manifest validation. |
| Read grids | `io_helper.py` | Shared binary-grid reader and primitive conversion helpers. |
| Measure | `metrics/` | Reusable scalar metrics and reference comparisons. |
| Summarise | `regression/matrix_summary_report.py` | Preferred matrix-summary consumer for new harness runs. |
| Summarise (MHD precision) | `regression/mhd_precision_pilot.py` | **canonical** Week-14 MHD precision-study aggregator; authoritative `summary.json`. `matrix_summary_report.py` is generic-checks-only here. |
| Summarise (MHD temporal) | `regression/mhd_temporal_divergence.py` | **canonical** fixed-window, provenance-gated fp32/fp64 HLL temporal driver. |
| Summarise (Report 2 cross-system) | `regression/report2_cross_system.py` | **canonical packet-specific** analyzer for the Week-18 Euler--MHD matrix; requires completion-attested metadata and removes transient grids after aggregation. |
| Run/summarise (MHD resolution) | `regression/mhd_week18_resolution_ladder.py` | **canonical packet-specific** OT/KH three-resolution driver; records incomplete groups and numerical failures instead of dropping them. |
| Reproduce (Lecoanet KH linear stage) | `regression/mhd_lecoanet_kh_reproduction.py` | **canonical packet-specific** exact smooth-IC and early-mode-growth driver; retains the rate discrepancy and excludes the nonlinear diffusive/dye reference claim. |
| Aggregate | `aggregate_metrics.py` | Thin JSON combiner for multiple summaries. |
| Plot (Report 2 publication set) | `figures/report2_publication_figures.py` | Audits stored source summaries, then writes seven 320-dpi PNG/vector-PDF pairs plus a claim/provenance/hash manifest. |
| Table (Report 2 Chapter 4 CPU/GPU) | `figures/report2_chapter4_cpu_gpu_table.py` | Generates the bounded four-row HLL correctness table directly from the CPU/GPU hardware-axis summary and rejects step or saved-state mismatches. |
| Plot | `figures/plot_2d.py` plus selected `figures/` helpers | Keep generated figures under the owning experiment/report directory. |

The architecture overview is [`docs/INDEX.md`](../docs/INDEX.md) section 2.
Lifecycle manifests live with the experiment packets and are validated by
the shared `scripts/harness/experiment_manifest.py` module. The read-only
candidate report is generated with:

```bash
python scripts/audit_experiments.py --format markdown
```

The audit requires a human reference check and performs no deletion or move.

## Directory Roles

| Directory | Role | Report 2 guidance |
|---|---|---|
| `metrics/` | Reusable numerical metrics. | Extend here when a metric is independent of one report figure. |
| `regression/` | Validation and summary reports. | Prefer `matrix_summary_report.py`; keep `float_regression_report.py` for Report 1/Week 4 compatibility. |
| `verificarlo/` | Verificarlo, MCA, and precexp drivers. | Prefer the `precexp_*` and metricised outputs for new analysis; older `verificarlo_analysis*` scripts are provenance. |
| `figures/` | Plot generators. | Reusable plotters stay top-level; Report 1 final/talk scripts are provenance and should not become Report 2 entry points. |
| `diagnostics/` | One-off investigations. | Treat as provenance unless a diagnostic is promoted into `metrics/` or `regression/`. |
| `cluster/` | CSC/Lovelace/SLURM helpers. | Check `cluster/README.md` before reuse; some scripts target old Week 4 paths. |

## Lifecycle Labels

Use these labels in new README notes, summaries, and plans:

- **canonical**: safe default for new work.
- **compatibility**: still tested or useful, but tied to an older output layout.
- **provenance**: kept to reproduce a past figure, report, or cluster run.
- **generated**: cache or build output; do not commit.

## Known Maintenance Hotspots

- `figures/report1_d2_replots.py` is a large Report 1 figure-production script.
  Do not extend it for Report 2; extract reusable logic into smaller helpers if
  the same plot style is needed again.
- `regression/float_regression_report.py` overlaps conceptually with
  `regression/matrix_summary_report.py`. New matrix-based runs should use the
  latter; keep the former for old Week 4/Report 1 layouts.
- `verificarlo/verificarlo_analysis.py` and
  `verificarlo/verificarlo_analysis_2d.py` are older analysis entry points.
  Prefer metric scripts under `metrics/` when adding new diagnostics.
- `cluster/rsync_from_cluster.sh` is not a generic sync helper; it targets old
  Week 4 Verificarlo artefacts.

## Import And Path Policy

Existing scripts are commonly invoked by path, for example:

```bash
python scripts/run_matrix.py experiments/week7/report1_smoke/matrix.json
```

Do not move existing script paths casually. If a script is physically moved,
update:

- pytest imports and `tests/py/conftest.py`
- shell and SLURM scripts under `scripts/cluster/`
- canonical docs such as `docs/INDEX.md` and `docs/HARNESS.md`
- new experiment plans

Commands recorded in `experiments/**/summary.md` are provenance. Prefer adding
a note that a path was historical instead of rewriting old records.

## Provenance Archive

Report 1-specific Python scripts that were likely to be mistaken for reusable
Report 2 entry points now live under `scripts/provenance/report1/`. The old
paths remain as compatibility wrappers, so historical commands and pytest
imports continue to work.

Do not add new analysis to the wrappers. Edit the archived source only when
reproducing or repairing Report 1 artefacts.
