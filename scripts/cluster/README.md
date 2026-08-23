# Cluster Scripts

These scripts are cluster helpers, not canonical local entry points. Check paths
and scheduler assumptions before reuse.

## Current Reusable Helpers

| Script | Use |
|---|---|
| `build_gpu_csc.sh` | Build strict CUDA variants on CSC. |
| `run_gpu_smoke.slurm` | Week 6 GPU smoke template. |
| `run_reference_1600.slurm` | Week 7 1600^2 reference template. |
| `report2_w16_w17_slurm/` | Current Week 16/17 CSC Slurm package for KH MCA completion with Apptainer-backed Verificarlo, W17 synthesis, paper figures, and scoped result sync. |

## Legacy / Provenance Helpers

| Script | Why it is not generic |
|---|---|
| `rsync_from_cluster.sh` | Targets old Week 4 Verificarlo artefacts. Use explicit rsync commands for new experiments. |
| `run_lovelace_parallel.sh` | Single-node substitute for old Week 4/Lovelace Verificarlo runs. |
| `slurm/verificarlo_2d_array.sh` | Week 4 Verificarlo array workflow. |
| `slurm/verificarlo_2d_float_array.sh` | Week 4 A4 p24-real-float array workflow. |
| `slurm/vfc_precexp_rerun.sh` | Week 7 precexp rerun workflow; keep with its matching docs/tests. |

Do not reuse a legacy helper for Report 2 until its output roots, module setup,
and analysis commands have been checked against the current experiment plan.
