#!/bin/bash
#SBATCH --job-name=hrsc-ref1600
#SBATCH --partition=csc-mphil-gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=experiments/week7/reference_1600/slurm_logs/%j.out
#SBATCH --error=experiments/week7/reference_1600/slurm_logs/%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
mkdir -p experiments/week7/reference_1600/slurm_logs

if type module >/dev/null 2>&1; then
    module purge || true
    module load cuda/12.9 || module load cuda || true
else
    echo "INFO: module command unavailable; continuing with PATH/CUDA_HOME probes" >&2
fi

if ! command -v nvcc >/dev/null 2>&1; then
    for cuda_home in "${HRSC_CUDA_HOME:-/lsc/opt/cuda-12.9}" /lsc/opt/cuda-12.9 /usr/local/cuda; do
        if [ -x "${cuda_home}/bin/nvcc" ]; then
            export HRSC_CUDA_HOME="${cuda_home}"
            export CUDA_HOME="${cuda_home}"
            export CUDAToolkit_ROOT="${cuda_home}"
            export PATH="${cuda_home}/bin:${PATH}"
            export LD_LIBRARY_PATH="${cuda_home}/lib64:${LD_LIBRARY_PATH:-}"
            break
        fi
    done
fi

echo "INFO: hostname=$(hostname)"
echo "INFO: SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
echo "INFO: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

nvidia-smi
if command -v nvcc >/dev/null 2>&1; then
    echo "INFO: nvcc=$(command -v nvcc)"
    nvcc --version
else
    echo "WARN: nvcc not found; reference run continues because binaries may already be built" >&2
fi

python scripts/run_matrix.py experiments/week7/reference_1600/matrix.json
