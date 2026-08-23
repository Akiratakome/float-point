#!/usr/bin/env bash
#SBATCH --job-name=hrsc-w18-hardware
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH --output=experiments/week18/csc_slurm_logs/%j-hardware.out
#SBATCH --error=experiments/week18/csc_slurm_logs/%j-hardware.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
source scripts/cluster/report2_w16_w17_slurm/env.sh
hrsc_cluster_setup
hrsc_print_context
mkdir -p experiments/week18/csc_slurm_logs

for PRECISION in double float; do
    cmake -S . -B "build-${PRECISION}" -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DFLOAT_PRECISION="${PRECISION}" \
        -DENABLE_OPENMP=ON
    cmake --build "build-${PRECISION}" --target hrsc_mhd

    CUDA_BUILD="build-cuda"
    if [[ "${PRECISION}" == "float" ]]; then
        CUDA_BUILD="build-cuda-float"
    fi
    cmake -S . -B "${CUDA_BUILD}" -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DFLOAT_PRECISION="${PRECISION}" \
        -DENABLE_CUDA=ON
    cmake --build "${CUDA_BUILD}" --target hrsc_mhd
done

"${HRSC_PYTHON}" scripts/regression/mhd_week18_supplemental.py hardware \
    --out experiments/week18/supplemental \
    --repeats "${HRSC_TIMING_REPEATS}"

