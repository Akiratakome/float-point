#!/usr/bin/env bash
set -euo pipefail

# Idempotent CUDA strict-IEEE build script for CSC Athena.
# Usage: bash scripts/cluster/build_gpu_csc.sh [double|float|both]

PRECISION="${1:-both}"
ARCH="${HRSC_CUDA_ARCH:-120}"
CUDA_HOME_CANDIDATE="${HRSC_CUDA_HOME:-/lsc/opt/cuda-12.9}"

case "${PRECISION}" in
    double|float|both) ;;
    *)
        echo "usage: $0 [double|float|both]" >&2
        exit 2
        ;;
esac

if type module >/dev/null 2>&1; then
    module purge || true
    module load cuda/12.9 || module load cuda || true
    module load gcc || true
    module load cmake || true
    module load ninja || true
else
    echo "INFO: module command unavailable; continuing with PATH/CUDA_HOME probes" >&2
fi

if ! command -v nvcc >/dev/null 2>&1; then
    for cuda_home in "${CUDA_HOME_CANDIDATE}" /lsc/opt/cuda-12.9 /usr/local/cuda; do
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

if ! command -v nvcc >/dev/null 2>&1; then
    echo "ERROR: nvcc not found. Set HRSC_CUDA_HOME to the CSC CUDA install, e.g. /lsc/opt/cuda-12.9" >&2
    exit 1
fi

if ! command -v cmake >/dev/null 2>&1; then
    echo "ERROR: cmake not found in PATH" >&2
    exit 1
fi

if ! command -v ninja >/dev/null 2>&1; then
    echo "ERROR: ninja not found in PATH; this script configures with -G Ninja" >&2
    exit 1
fi

echo "INFO: hostname=$(hostname)"
echo "INFO: precision=${PRECISION}"
echo "INFO: HRSC_CUDA_ARCH=${ARCH}"
echo "INFO: nvcc=$(command -v nvcc)"
nvcc --version
nvidia-smi || echo "WARN: nvidia-smi unavailable on this node; expected on CSC login nodes" >&2

build_one() {
    local prec="$1"
    local dir="build-cuda-${prec}-strict"

    cmake -B "${dir}" -G Ninja \
        -DFLOAT_PRECISION="${prec}" \
        -DENABLE_CUDA=ON \
        -DSTRICT_IEEE=ON \
        -DENABLE_OPENMP=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES="${ARCH}" \
        -DCMAKE_CUDA_COMPILER="$(command -v nvcc)"

    if [ -n "${HRSC_BUILD_JOBS:-}" ]; then
        cmake --build "${dir}" -j "${HRSC_BUILD_JOBS}"
    else
        cmake --build "${dir}" --parallel
    fi
}

case "${PRECISION}" in
    double) build_one double ;;
    float)  build_one float ;;
    both)   build_one double; build_one float ;;
esac

echo "INFO: build complete: build-cuda-{double,float}-strict/hrsc"
