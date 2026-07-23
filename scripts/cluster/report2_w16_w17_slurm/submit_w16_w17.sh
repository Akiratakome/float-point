#!/usr/bin/env bash
set -euo pipefail

# Submitted MCA jobs use the shared Apptainer environment in env.sh.
MODE="${1:-full}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../../.."

case "${MODE}" in
    smoke)
        SMOKE_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_kh_smoke_mca.slurm)"
        echo "submitted smoke MCA array: ${SMOKE_JOB}"
        ;;
    full)
        FULL_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_kh_full_mca.slurm)"
        PACKET_JOB="$(sbatch --parsable --dependency=afterok:${FULL_JOB} scripts/cluster/report2_w16_w17_slurm/run_kh_packets_from_mca.slurm)"
        FIG_JOB="$(sbatch --parsable --dependency=afterok:${PACKET_JOB} scripts/cluster/report2_w16_w17_slurm/run_w17_synthesis_and_figures.slurm)"
        echo "submitted full MCA array: ${FULL_JOB}"
        echo "submitted KH packet array: ${PACKET_JOB}"
        echo "submitted W17 synthesis job: ${FIG_JOB}"
        ;;
    both)
        SMOKE_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_kh_smoke_mca.slurm)"
        FULL_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_kh_full_mca.slurm)"
        PACKET_JOB="$(sbatch --parsable --dependency=afterok:${FULL_JOB} scripts/cluster/report2_w16_w17_slurm/run_kh_packets_from_mca.slurm)"
        FIG_JOB="$(sbatch --parsable --dependency=afterok:${PACKET_JOB} scripts/cluster/report2_w16_w17_slurm/run_w17_synthesis_and_figures.slurm)"
        echo "submitted smoke MCA array: ${SMOKE_JOB}"
        echo "submitted full MCA array: ${FULL_JOB}"
        echo "submitted KH packet array: ${PACKET_JOB}"
        echo "submitted W17 synthesis job: ${FIG_JOB}"
        ;;
    *)
        echo "usage: $0 [smoke|full|both]" >&2
        exit 2
        ;;
esac
