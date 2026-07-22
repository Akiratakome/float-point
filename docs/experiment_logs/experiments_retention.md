# Experiments Retention And Cleanup

Purpose: define what should remain under `experiments/` now that Report 1 is
complete and Report 2 code work is about to start.

This document does not change solver numerics, cfg defaults, or output formats.
It classifies artefacts so cleanup can be done without losing report evidence.

Report 2 lifecycle manifests use these five values: `canonical` (current
authority), `provenance` (retained historical support), `superseded` (replaced
by a named manifest), `invalid` (not evidentially usable), and `generated`
(reproducible generated material). Validate them with
`python -m pytest tests/py/test_experiment_manifests.py -q`.

## Canonical Evidence

Use [report1_evidence_map.md](report1_evidence_map.md) as the current source of
truth for Report 1 artefact priority.

Priority meanings:

- `P0`: core Report 1 evidence. Keep summaries, metadata, CSV/JSON, and figures.
- `P1`: useful support or provenance. Keep compact summaries and selected figures.
- `P2`: backup/provenance. Keep only if it explains a later result or is cheap.
- `P3`: do not use directly. Safe cleanup candidate after confirming no report
  or script references it.

## Keep By Default

- `summary.md`, `summary.json`, `summary.csv`.
- `matrix.json`, `matrix_summary.json`.
- generated `config.cfg`, `metadata.json`, `stdout.txt`, `stderr.txt` for retained
  runs.
- final report figures and source CSVs used to generate them.
- promoted reference grids explicitly named in summaries, for example the LW3
  1600^2 reference candidate and LW12 N=800 reference, unless the user decides
  to archive them externally.

## Cleanup Candidates

The current read-only candidate inventory is
[experiment_cleanup_candidates.md](experiment_cleanup_candidates.md). It is a
discovery report only: every candidate still requires a reference audit before
any action, and no deletion is performed by the audit.

Do not delete these blindly; inspect first and remove only after confirming they
are not needed for a pending report figure or rerun.

| path | status | recommended action |
|---|---|---|
| `experiments/report1/review3/add_experiment/builds/` | misplaced build directory | delete or move outside `experiments/`; build dirs are reproducible and should not be retained as experiment artefacts |
| `experiments/_archive/duplicates/c2_bundle_for_download/` | duplicate download bundle | delete after confirming canonical Verificarlo / Week 7 artefacts exist |
| `experiments/_scratch/tmp_convergence_check/` | temporary scratch output | delete after confirming no active script reads it |
| `experiments/report1/review3/*` | report-review working artefacts | keep only if needed for Report 1 provenance; do not use as Report 2 canonical evidence |
| `experiments/week9/lw_precision_heatmaps/summary.md` LW3 row | failed local figure attempt | do not cite; retain only as failed-attempt provenance if desired |
| unreferenced `grid.bin` files below retained run folders | transient grids | delete unless promoted as reference data in a summary |

## Wrong Locations

- Report-facing evidence maps belong under `docs/experiment_logs/`, not under
  `experiments/`.
- Build outputs belong under root-level ignored build directories such as
  `build-*` or `build-matrix/`, not under `experiments/`.
- Agent process files belong outside permanent project docs. If retained, they
  should be in a clearly named archive, not in the main index.

## Report 2 Starting Rule

Report 2 experiment work should create new folders under `experiments/report2_*`
or `experiments/week12+/*` and follow:

```text
config -> build -> run -> measure -> aggregate -> plot
```

Raw grids should be transient. Keep metadata, scalar summaries, logs, and report
figures.
