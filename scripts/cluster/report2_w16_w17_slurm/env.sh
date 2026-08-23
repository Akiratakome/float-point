#!/usr/bin/env bash
set -euo pipefail

export HRSC_REPO_ROOT="${HRSC_REPO_ROOT:-${SLURM_SUBMIT_DIR:-$(pwd)}}"
export HRSC_VFC_IMAGE="${HRSC_VFC_IMAGE:-${HRSC_REPO_ROOT}/verificarlo-cmake.sif}"
export HRSC_PYTHON="${HRSC_PYTHON:-python3}"
export HRSC_MCA_JOBS="${HRSC_MCA_JOBS:-${SLURM_CPUS_PER_TASK:-8}}"
export HRSC_KH_FULL_SAMPLES="${HRSC_KH_FULL_SAMPLES:-30}"
export HRSC_KH_SMOKE_SAMPLES="${HRSC_KH_SMOKE_SAMPLES:-30}"
export HRSC_TIMING_REPEATS="${HRSC_TIMING_REPEATS:-5}"
export HRSC_KH_SAMPLE_TIMEOUT_S="${HRSC_KH_SAMPLE_TIMEOUT_S:-14400}"
export HRSC_VFC_BACKEND_LIB="${HRSC_VFC_BACKEND_LIB:-libinterflop_mca.so}"
export HRSC_VFC_RUNNER="${HRSC_VFC_RUNNER:-apptainer}"

hrsc_cluster_setup() {
    cd "${HRSC_REPO_ROOT}"
    if type module >/dev/null 2>&1; then
        module purge || true
        module load gcc || true
        module load cmake || true
        module load ninja || true
        module load python || true
        module load cuda || true
        if [[ "${HRSC_VFC_RUNNER}" == "apptainer" ]]; then
            module load apptainer || module load singularity || true
        fi
    fi

    if ! command -v "${HRSC_PYTHON}" >/dev/null 2>&1; then
        echo "ERROR: HRSC_PYTHON=${HRSC_PYTHON} is not executable" >&2
        exit 1
    fi
    if [[ "${HRSC_VFC_RUNNER}" == "apptainer" ]]; then
        if ! command -v apptainer >/dev/null 2>&1; then
            echo "ERROR: apptainer is not in PATH; load the CSC container module first" >&2
            exit 1
        fi
    elif ! command -v verificarlo-c++ >/dev/null 2>&1; then
        echo "ERROR: HRSC_VFC_RUNNER=native but verificarlo-c++ is not in PATH" >&2
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
    if [[ "${HRSC_VFC_RUNNER}" != "apptainer" ]]; then
        return 0
    fi
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
    echo "INFO: HRSC_VFC_RUNNER=${HRSC_VFC_RUNNER}"
    echo "INFO: HRSC_PYTHON=$(${HRSC_PYTHON} --version 2>&1)"
    if [[ "${HRSC_VFC_RUNNER}" == "apptainer" ]]; then
        echo "INFO: HRSC_VFC_IMAGE=${HRSC_VFC_IMAGE}"
        echo "INFO: apptainer=$(command -v apptainer)"
        apptainer --version || true
    else
        echo "INFO: verificarlo-c++=$(command -v verificarlo-c++)"
        verificarlo-c++ --version || true
    fi
}
