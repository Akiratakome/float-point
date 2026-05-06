#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# verificarlo_2d_array.sh — Week 4 A3 CSC SLURM array job (2D MCA production).
#
# Submits an N-task SLURM array where each task runs ONE independent MCA
# sample of a 2D Liska-Wendroff config. Per-task seed comes from /dev/urandom
# and is inlined in VFC_BACKENDS (VFC_BACKENDS_SEED env var is silently
# ignored by interflop_mca — the seed MUST be passed as --seed=<decimal>).
# See scripts/verificarlo/noise_floor_run.sh and scripts/verificarlo/verificarlo_run_2d.sh for the
# same mechanism used locally; keeping parity ensures local smoke / feasibility
# and cluster production share one analyzer chain.
#
# Submission (from repo root on the cluster login node):
#     sbatch --array=1-30 scripts/slurm/verificarlo_2d_array.sh \
#         tests/cases/liska_wendroff_2d/config3.cfg          hllc
#     sbatch --array=1-30 scripts/slurm/verificarlo_2d_array.sh \
#         tests/cases/liska_wendroff_2d/config3_rusanov.cfg  rusanov
#
# Array tasks run CONCURRENTLY (see week4-plan §A3.0): --time=12:00:00 is the
# per-task wall-clock cap, NOT the whole batch. N=30 is fixed (χ² 90% CI σ±15%).
# ──────────────────────────────────────────────────────────────────────────────

#SBATCH --job-name=vfc2d
#SBATCH --output=logs/vfc2d_%A_%a.out
#SBATCH --error=logs/vfc2d_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1                 # PRNG thread isolation; parallelism via array
#SBATCH --mem=8G
#SBATCH --time=12:00:00                   # per-task cap — array tasks run concurrently

set -euo pipefail

CONFIG=${1:?"usage: sbatch --array=1-30 $0 <cfg> <hllc|rusanov> [out_base]"}
SOLVER=${2:?"usage: sbatch --array=1-30 $0 <cfg> <hllc|rusanov> [out_base]"}
OUT_BASE=${3:-experiments/week4/2d_vfc_cluster}

if [[ "$SOLVER" != "hllc" && "$SOLVER" != "rusanov" ]]; then
    echo "ERROR: solver must be hllc or rusanov (got '$SOLVER')" >&2
    exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: cfg not found: $CONFIG" >&2
    exit 2
fi

SAMPLE_ID=${SLURM_ARRAY_TASK_ID:?"must be launched via sbatch --array"}
SAMPLE_TAG="$(printf '%02d' "$SAMPLE_ID")"

OUT_DIR="${OUT_BASE}/${SOLVER}/sample_${SAMPLE_TAG}"
SEED_DIR="${OUT_BASE}/${SOLVER}/seeds"
mkdir -p "$OUT_DIR" "$SEED_DIR" logs

# ── Verificarlo toolchain resolution ──────────────────────────────────────────
# Preferred path: site module (Week 3 supervisor email mentioned
#   /lsc/opt/verificarlo-2.4.0). After `module load verificarlo-2.4.0`,
# verificarlo-c++ is on PATH and libinterflop_mca.so is auto-discovered.
#
# Fallback: Singularity image copied to the cluster (see scripts/slurm/README.md).
# Detection is explicit — no silent fallback that changes which Verificarlo
# version is used.
if command -v verificarlo-c++ >/dev/null 2>&1; then
    RUNNER="native"
elif command -v singularity >/dev/null 2>&1 && [[ -f verificarlo.sif ]]; then
    RUNNER="singularity"
else
    echo "ERROR: no verificarlo-c++ on PATH and no verificarlo.sif at repo root." >&2
    echo "       Load the site module (e.g. 'module load verificarlo-2.4.0') or" >&2
    echo "       stage the Singularity image (see scripts/slurm/README.md)."       >&2
    exit 3
fi

# ── PRNG thread isolation (Round 3 — see week4-plan §A3.2) ────────────────────
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# ── Per-task seed via /dev/urandom (63-bit; top bit masked for signed int64) ──
SEED_RAW="$(od -An -N8 -tu8 /dev/urandom | tr -d ' \n')"
SEED_DEC=$(( SEED_RAW & 0x7FFFFFFFFFFFFFFF ))
SEED_HEX="$(printf '%016x' "$SEED_DEC")"
VFC_BASE="libinterflop_mca.so --mode=rr --precision-binary64=53"
export VFC_BACKENDS="${VFC_BASE} --seed=${SEED_DEC}"
# Defensive: both env names seen across vfc versions; logged for traceability.
export VERIFICARLO_MCA_SEED="0x${SEED_HEX}"
export VFC_BACKEND_SEED="0x${SEED_HEX}"

# ── Per-task seed CSV (no shared file → no flock races on Lustre/GPFS/NFS) ────
SEED_CSV="${SEED_DIR}/seed_${SAMPLE_TAG}.csv"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
    echo "sample_id,seed_dec,seed_hex,timestamp_utc"
    echo "${SAMPLE_TAG},${SEED_DEC},0x${SEED_HEX},${TIMESTAMP}"
} > "$SEED_CSV"

# ── Per-sample run.cfg overlays the base cfg with binary output path ──────────
SAMPLE_FILE="${OUT_DIR}/grid.bin"
SAMPLE_CFG="${OUT_DIR}/run.cfg"
cp "$CONFIG" "$SAMPLE_CFG"
{
    echo "solver = ${SOLVER}"
    echo "output_format = binary"
    echo "output_file = ${SAMPLE_FILE}"
} >> "$SAMPLE_CFG"

BUILD_DIR="build-vfc-p53"
HRSC="${BUILD_DIR}/hrsc"

echo "[vfc2d] task=${SAMPLE_TAG} solver=${SOLVER} runner=${RUNNER} seed=${SEED_DEC}"
echo "[vfc2d] cfg=${CONFIG}  sample_cfg=${SAMPLE_CFG}  out=${SAMPLE_FILE}"

build_and_run_native() {
    if [[ ! -x "$HRSC" ]]; then
        CXX=verificarlo-c++ cmake -S . -B "$BUILD_DIR" \
            -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=double
        cmake --build "$BUILD_DIR" -j
    fi
    "$HRSC" "$SAMPLE_CFG" > /dev/null
}

build_and_run_singularity() {
    singularity exec verificarlo.sif bash -c "
        set -euo pipefail
        export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
        export VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
        export VFC_BACKENDS='${VFC_BACKENDS}'
        if [[ ! -x '${HRSC}' ]]; then
            CXX=verificarlo-c++ cmake -S . -B '${BUILD_DIR}' \
                -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=double
            cmake --build '${BUILD_DIR}' -j
        fi
        '${HRSC}' '${SAMPLE_CFG}' > /dev/null
    "
}

case "$RUNNER" in
    native)      build_and_run_native ;;
    singularity) build_and_run_singularity ;;
esac

echo "[vfc2d] task=${SAMPLE_TAG} completed"
