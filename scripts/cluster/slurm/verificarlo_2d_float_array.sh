#!/bin/bash
# Week 4/5 A4 real-float p24 MCA production for LW Config 3 on CSC Athena.
#
# Each SLURM array task runs one independent native binary32 MCA sample.
# Output layout matches the p53 A3 analyzer contract:
#   <out>/<solver>/sample_NN/{run.cfg,grid.bin}
#   <out>/<solver>/seeds/seed_NN.csv

#SBATCH --job-name=vfc2df32
#SBATCH --output=logs/vfc2df32_%A_%a.out
#SBATCH --error=logs/vfc2df32_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=12:00:00

set -euo pipefail

CONFIG=${1:?"usage: sbatch --array=1-30 $0 <cfg> <hllc|rusanov> [out_base]"}
SOLVER=${2:?"usage: sbatch --array=1-30 $0 <cfg> <hllc|rusanov> [out_base]"}
OUT_BASE=${3:-experiments/week4/2d_vfc_float_p24}

if [[ "$SOLVER" != "hllc" && "$SOLVER" != "rusanov" ]]; then
    echo "ERROR: solver must be hllc or rusanov (got '$SOLVER')" >&2
    exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: cfg not found: $CONFIG" >&2
    exit 2
fi
if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: run from repository root." >&2
    exit 2
fi

VFC_ROOT=${VFC_ROOT:-/lsc/opt/verificarlo-2.4.0}
if [[ -x "${VFC_ROOT}/bin/verificarlo-c++" ]]; then
    export PATH="${VFC_ROOT}/bin:${PATH}"
    export LD_LIBRARY_PATH="${VFC_ROOT}/lib:${LD_LIBRARY_PATH:-}"
fi
if ! command -v verificarlo-c++ >/dev/null 2>&1; then
    echo "ERROR: verificarlo-c++ not found. Expected ${VFC_ROOT}/bin/verificarlo-c++." >&2
    exit 3
fi
if [[ ! -x /usr/bin/clang++ ]]; then
    echo "ERROR: /usr/bin/clang++ is required by the CSC Verificarlo wrapper." >&2
    exit 3
fi

SAMPLE_ID=${SLURM_ARRAY_TASK_ID:?"must be launched via sbatch --array"}
SAMPLE_TAG="$(printf '%02d' "$SAMPLE_ID")"

OUT_DIR="${OUT_BASE}/${SOLVER}/sample_${SAMPLE_TAG}"
SEED_DIR="${OUT_BASE}/${SOLVER}/seeds"
mkdir -p "$OUT_DIR" "$SEED_DIR" logs

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

SEED_RAW="$(od -An -N8 -tu8 /dev/urandom | tr -d ' \n')"
SEED_DEC=$(( SEED_RAW & 0x7FFFFFFFFFFFFFFF ))
SEED_HEX="$(printf '%016x' "$SEED_DEC")"
export VFC_BACKENDS="libinterflop_mca.so --mode=mca --precision-binary32=24 --seed=${SEED_DEC}"
export VERIFICARLO_MCA_SEED="0x${SEED_HEX}"
export VFC_BACKEND_SEED="0x${SEED_HEX}"

SEED_CSV="${SEED_DIR}/seed_${SAMPLE_TAG}.csv"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

SAMPLE_FILE="${OUT_DIR}/grid.bin"
SAMPLE_CFG="${OUT_DIR}/run.cfg"
cp "$CONFIG" "$SAMPLE_CFG"
{
    echo "solver = ${SOLVER}"
    echo "output_format = binary"
    echo "output_file = ${SAMPLE_FILE}"
} >> "$SAMPLE_CFG"

BUILD_DIR=${VFC_FLOAT_BUILD_DIR:-build-vfc-real-float-p24}
HRSC="${BUILD_DIR}/hrsc"

echo "[vfc2df32] task=${SAMPLE_TAG} solver=${SOLVER} seed=${SEED_DEC}"
echo "[vfc2df32] verificarlo-c++=$(command -v verificarlo-c++)"
echo "[vfc2df32] cfg=${CONFIG} sample_cfg=${SAMPLE_CFG} out=${SAMPLE_FILE}"

if [[ ! -x "$HRSC" ]]; then
    echo "ERROR: ${HRSC} is missing. Prebuild once before sbatch:" >&2
    echo "  CXX=${VFC_ROOT}/bin/verificarlo-c++ cmake -S . -B ${BUILD_DIR} -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=float -DENABLE_OPENMP=OFF" >&2
    echo "  cmake --build ${BUILD_DIR} -j" >&2
    exit 4
fi

if "$HRSC" "$SAMPLE_CFG" > "${OUT_DIR}/stdout.txt" 2> "${OUT_DIR}/stderr.txt"; then
    {
        echo "sample_id,seed_dec,seed_hex,timestamp_utc"
        echo "${SAMPLE_TAG},${SEED_DEC},0x${SEED_HEX},${TIMESTAMP}"
    } > "$SEED_CSV"
    echo "[vfc2df32] task=${SAMPLE_TAG} completed"
else
    rc=$?
    rm -f "$SAMPLE_FILE"
    echo "[vfc2df32] task=${SAMPLE_TAG} failed rc=${rc}; see ${OUT_DIR}/stderr.txt" >&2
    exit "$rc"
fi
