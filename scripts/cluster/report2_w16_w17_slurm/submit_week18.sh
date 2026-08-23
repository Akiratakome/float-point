#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../../.."

HARDWARE_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_week18_hardware_repeats.slurm)"
CPU_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_week18_cpu_robustness.slurm)"
MCA_JOB="$(sbatch --parsable scripts/cluster/report2_w16_w17_slurm/run_kh_full_mca.slurm)"
PACKET_JOB="$(sbatch --parsable --dependency=afterok:${MCA_JOB} scripts/cluster/report2_w16_w17_slurm/run_kh_packets_from_mca.slurm)"

echo "submitted Week 18 hardware repeats: ${HARDWARE_JOB}"
echo "submitted Week 18 CPU robustness: ${CPU_JOB}"
echo "submitted full KH MCA array: ${MCA_JOB}"
echo "submitted KH packet array: ${PACKET_JOB}"

