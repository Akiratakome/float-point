# Experiments Directory

This directory contains generated experiment artefacts. Most of it is ignored by
git; only selected summaries, metadata, figures, and small source tables are
tracked.

For delivered evidence and its claim boundaries, use
[`../docs/INDEX.md`](../docs/INDEX.md) section 6.

Rules:

- Keep summaries, metadata, generated cfgs, logs, source CSV/JSON, and report
  figures.
- Keep promoted reference grids only when a summary explicitly names them.
- Do not keep build directories under `experiments/`.
- Treat unreferenced `grid.bin` files as transient.

## Current Top-Level Layout

| Path | Role |
|---|---|
| `weekN/` | Week-owned experiment packets and matrices. Keep these stable as weekly provenance. |
| `verificarlo/` | Cross-week Verificarlo/MCA runs that predate or span weekly folders. |
| `report1/` | Report 1 closeout evidence and review/fix artefacts consolidated from old top-level folders. |
| `_archive/` | Duplicate or download bundles kept only for temporary provenance. |
| `_scratch/` | Temporary local checks. Safe to delete after confirming no active task uses them. |

## Report 1 Consolidation

Old top-level `report1_*`, `review3_*`, and `add_experiment` folders were
merged to reduce top-level noise:

| Old pattern | New home |
|---|---|
| `report1_*` evidence packets | `report1/evidence/<topic>/` |
| `report1_hllc_s0_fix_*` | `report1/fixes/hllc_s0/<topic>/` |
| `review3_*` | `report1/review3/<topic>/` |
| `add_experiment` | `report1/review3/add_experiment/` |
| `c2_bundle_for_download` | `_archive/duplicates/c2_bundle_for_download/` |
| `tmp_convergence_check` | `_scratch/tmp_convergence_check/` |

Historical docs may still mention the old paths. Use this README and
[`../docs/INDEX.md`](../docs/INDEX.md) as the current path reference.
