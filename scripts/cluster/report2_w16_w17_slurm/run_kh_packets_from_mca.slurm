#!/usr/bin/env bash
#SBATCH --job-name=hrsc-kh-packets
#SBATCH --array=0-1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=12:00:00
#SBATCH --output=experiments/week16/kelvin_helmholtz_precision/csc_packets/slurm_logs/%A_%a.out
#SBATCH --error=experiments/week16/kelvin_helmholtz_precision/csc_packets/slurm_logs/%A_%a.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
source scripts/cluster/report2_w16_w17_slurm/env.sh
hrsc_cluster_setup
hrsc_print_context

mkdir -p experiments/week16/kelvin_helmholtz_precision/csc_packets/slurm_logs

SOLVERS=(hll hlld)
SOLVER="${SOLVERS[${SLURM_ARRAY_TASK_ID}]}"
MCA_SUMMARY="experiments/week16/kelvin_helmholtz_precision/csc_mca/${SOLVER}/summary.json"

if [[ ! -f "${MCA_SUMMARY}" ]]; then
    echo "ERROR: missing Apptainer-produced MCA summary: ${MCA_SUMMARY}" >&2
    exit 1
fi

"${HRSC_PYTHON}" scripts/regression/mhd_kh_precision.py \
    --out experiments/week16/kelvin_helmholtz_precision/csc_packets \
    --solver "${SOLVER}" \
    --phase p1 \
    --mca-summary "${MCA_SUMMARY}"
