#!/usr/bin/env bash
#SBATCH --job-name=hrsc-kh-smoke-mca
#SBATCH --array=0-1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=04:00:00
#SBATCH --output=experiments/week16/kelvin_helmholtz_precision/csc_mca_smoke/slurm_logs/%A_%a.out
#SBATCH --error=experiments/week16/kelvin_helmholtz_precision/csc_mca_smoke/slurm_logs/%A_%a.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
source scripts/cluster/report2_w16_w17_slurm/env.sh
hrsc_cluster_setup
hrsc_require_apptainer_image
hrsc_print_context

mkdir -p experiments/week16/kelvin_helmholtz_precision/csc_mca_smoke/slurm_logs

SOLVERS=(hll hlld)
SOLVER="${SOLVERS[${SLURM_ARRAY_TASK_ID}]}"
OUT="experiments/week16/kelvin_helmholtz_precision/csc_mca_smoke/${SOLVER}"

"${HRSC_PYTHON}" scripts/verificarlo/mhd_precision_sampling.py \
    --out "${OUT}" \
    --samples "${HRSC_KH_SMOKE_SAMPLES}" \
    --solver "${SOLVER}" \
    --case scripts/cluster/report2_w16_w17_slurm/cfg/kh_64_t005.cfg \
    --experiment week16-kelvin-helmholtz-mca-smoke-csc \
    --image "${HRSC_VFC_IMAGE}" \
    --jobs "${HRSC_MCA_JOBS}"
