# Week 7 1600^2 GPU Reference Candidate

Purpose: supervisor-requested high-resolution GPU reference candidate for Report 1.

## Run

- Experiment: `week7-reference-1600`.
- Run: `lw3-n1600-gpu-double-strict`.
- Case: Liska-Wendroff 2D Config 3.
- Resolution: 1600x1600.
- Solver: HLLC.
- Boundary condition: outflow.
- Precision/build: GPU double, `STRICT_IEEE=ON`, `build-cuda-double-strict/hrsc`.
- Source cfg: `tests/cases/liska_wendroff_2d/config3_n1600.cfg` (new in this commit).
- Generated cfg: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/config.cfg`.
- Output grid: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/reference_1600.bin`.

Provenance note: `metadata.json` records the solver run against git commit
`030db9d` (the Task 10 gate decision). This artefact commit preserves the new
source cfg, generated cfg, metadata, stdout/stderr, and matrix summary used for
the run.

## Gate And Interpretation

Task 9 passed both HLLC strict CPU-to-GPU preflight rows at n200 and n400 with zero deltas and `gate_passed` true, as recorded in `experiments/week7/reference_1600/gate_decision.md`.

Week 6 (`experiments/week6/regression/summary.md`) established strict GPU smoke support, and Task 9 adds an HLLC strict preflight at 200^2/400^2. This 1600^2 artefact is still GPU-produced. Treat it as a GPU high-resolution reference candidate with Task 9 preflight support, not CPU-equivalent proof. Do not call it CPU-equivalent unless a matching 1600^2 CPU strict run is later produced.

## Actual Runtime And Hardware

- Submitted via SLURM job: `10556`.
- Node: `phy-damysus`.
- GPU allocation: `CUDA_VISIBLE_DEVICES=0`.
- Hardware observed by `nvidia-smi`: NVIDIA GeForce RTX 5090, 32607 MiB memory.
- Driver/CUDA reported by `nvidia-smi`: driver 580.95.05, CUDA 13.0.
- CUDA compiler used for environment probe: `/lsc/opt/cuda-12.9/bin/nvcc`, CUDA compilation tools 12.9, V12.9.41.
- Solver timing: `total_s=14.1705`, `gpu_run_s=14.1705`.
- Completed steps: 2316, final time `t = 0.3`.
- Return code: 0.

## Artefacts

- Matrix: `experiments/week7/reference_1600/matrix.json`.
- Matrix summary: `experiments/week7/reference_1600/matrix_summary.json`.
- Metadata: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/metadata.json`.
- Stdout: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/stdout.txt`.
- Stderr/timing: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/stderr.txt`.
- SLURM logs: `experiments/week7/reference_1600/slurm_logs/10556.out` and `experiments/week7/reference_1600/slurm_logs/10556.err` (local/untracked evidence).
- Reference grid: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/reference_1600.bin`.

The binary grid (`reference_1600.bin`) remains out of git by default. Use this 1600^2 grid only as a reference base for lower-resolution LW3 candidates. Do not use it to claim CPU-vs-GPU equality or compiler sensitivity unless matching 1600^2 candidate rows are explicitly run.
