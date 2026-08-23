#!/usr/bin/env bash
#SBATCH --job-name=hrsc-kh-full-mca
#SBATCH --partition=csc-mphil
#SBATCH --array=0-3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=06:00:00
#SBATCH --output=experiments/week16/kelvin_helmholtz_precision/csc_mca/slurm_logs/%A_%a.out
#SBATCH --error=experiments/week16/kelvin_helmholtz_precision/csc_mca/slurm_logs/%A_%a.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
source scripts/cluster/report2_w16_w17_slurm/env.sh
hrsc_cluster_setup
hrsc_require_apptainer_image
hrsc_print_context

mkdir -p experiments/week16/kelvin_helmholtz_precision/csc_mca/slurm_logs

SOLVERS=(hll hll hlld hlld)
PRECS=(53 24 53 24)
SOLVER="${SOLVERS[${SLURM_ARRAY_TASK_ID}]}"
PREC="${PRECS[${SLURM_ARRAY_TASK_ID}]}"
OUT="experiments/week16/kelvin_helmholtz_precision/csc_mca/${SOLVER}"

"${HRSC_PYTHON}" scripts/verificarlo/mhd_precision_sampling.py \
    --out "${OUT}" \
    --samples "${HRSC_KH_FULL_SAMPLES}" \
    --solver "${SOLVER}" \
    --precisions "${PREC}" \
    --case tests/cases/kelvin_helmholtz_2d/kh.cfg \
    --experiment week16-kelvin-helmholtz-mca-csc \
    --image "${HRSC_VFC_IMAGE}" \
    --jobs "${HRSC_MCA_JOBS}" \
    --sample-timeout-s "${HRSC_KH_SAMPLE_TIMEOUT_S}" \
    --backend-lib "${HRSC_VFC_BACKEND_LIB}"
