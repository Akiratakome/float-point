#!/usr/bin/env bash
set -euo pipefail

export HRSC_REPO_ROOT="${HRSC_REPO_ROOT:-${SLURM_SUBMIT_DIR:-$(pwd)}}"
export HRSC_VFC_IMAGE="${HRSC_VFC_IMAGE:-${HRSC_REPO_ROOT}/verificarlo-cmake.sif}"
export HRSC_PYTHON="${HRSC_PYTHON:-python3}"
export HRSC_MCA_JOBS="${HRSC_MCA_JOBS:-${SLURM_CPUS_PER_TASK:-8}}"
export HRSC_KH_FULL_SAMPLES="${HRSC_KH_FULL_SAMPLES:-30}"
export HRSC_KH_SMOKE_SAMPLES="${HRSC_KH_SMOKE_SAMPLES:-30}"

hrsc_cluster_setup() {
    cd "${HRSC_REPO_ROOT}"
    if type module >/dev/null 2>&1; then
        module purge || true
        module load gcc || true
        module load cmake || true
        module load ninja || true
        module load python || true
        module load apptainer || module load singularity || true
    fi

    if ! command -v "${HRSC_PYTHON}" >/dev/null 2>&1; then
        echo "ERROR: HRSC_PYTHON=${HRSC_PYTHON} is not executable" >&2
        exit 1
    fi
    if ! command -v apptainer >/dev/null 2>&1; then
        echo "ERROR: apptainer is not in PATH; load the CSC container module first" >&2
        exit 1
    fi
    if ! command -v cmake >/dev/null 2>&1; then
        echo "ERROR: cmake is not in PATH" >&2
        exit 1
    fi
    if ! command -v ninja >/dev/null 2>&1; then
        echo "ERROR: ninja is not in PATH" >&2
        exit 1
    fi
}

hrsc_require_apptainer_image() {
    if [[ ! -f "${HRSC_VFC_IMAGE}" ]]; then
        echo "ERROR: HRSC_VFC_IMAGE does not exist: ${HRSC_VFC_IMAGE}" >&2
        echo "Create or copy verificarlo-cmake.sif before submitting MCA jobs." >&2
        exit 1
    fi
}

hrsc_print_context() {
    echo "INFO: hostname=$(hostname)"
    echo "INFO: SLURM_JOB_ID=${SLURM_JOB_ID:-none}"
    echo "INFO: SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID:-none}"
    echo "INFO: HRSC_REPO_ROOT=${HRSC_REPO_ROOT}"
    echo "INFO: HRSC_VFC_IMAGE=${HRSC_VFC_IMAGE}"
    echo "INFO: HRSC_PYTHON=$(${HRSC_PYTHON} --version 2>&1)"
    echo "INFO: apptainer=$(command -v apptainer)"
    apptainer --version || true
}
