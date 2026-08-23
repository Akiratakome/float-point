#!/usr/bin/env bash
#SBATCH --job-name=hrsc-w17-synthesis
#SBATCH --partition=csc-mphil
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --output=experiments/week17/csc_slurm_logs/%j.out
#SBATCH --error=experiments/week17/csc_slurm_logs/%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
source scripts/cluster/report2_w16_w17_slurm/env.sh
hrsc_cluster_setup
hrsc_print_context

mkdir -p experiments/week17/csc_slurm_logs

"${HRSC_PYTHON}" scripts/regression/report2_synthesis.py \
    --output-dir experiments/week17/report2_synthesis

"${HRSC_PYTHON}" scripts/figures/report2_w16_w17_paper_figures.py
