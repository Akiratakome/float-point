#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# run_lovelace_parallel.sh — Week 4 A3 2D MCA production on Cambridge LSC
# lovelace.lsc.phy.private.cam.ac.uk (64 cores / 251 GB, no SLURM).
#
# Single-node parallel substitute for scripts/slurm/verificarlo_2d_array.sh:
# spawns N independent worker processes (xargs -P), each with its own
# /dev/urandom seed inlined into VFC_BACKENDS. Output layout and per-sample
# seed-CSV format match the SLURM script exactly, so the same analyzer chain
# (scripts/io_helper.py etc.) works unchanged on results from either path.
#
# Usage (from repo root on lovelace):
#     bash scripts/run_lovelace_parallel.sh \
#         --config tests/cases/liska_wendroff_2d/config3.cfg \
#         --solver hllc --samples 30 --parallel 30
#     bash scripts/run_lovelace_parallel.sh \
#         --config tests/cases/liska_wendroff_2d/config3_rusanov.cfg \
#         --solver rusanov --samples 30 --parallel 30
#
# Expected wall-clock per solver at 200²: ≈ per-sample wall-clock
# (all 30 samples finish concurrently) — ballpark 5 min × 1 wave ≈ 5 min.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Repo-root guard ───────────────────────────────────────────────────────────
if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: must be run from repo root (CMakeLists.txt not found here)" >&2
    exit 1
fi

# ── Defaults ──────────────────────────────────────────────────────────────────
CONFIG=""
SOLVER=""
N_SAMPLES=30
N_PARALLEL=""
OUT_BASE="experiments/week4/2d_vfc_cluster"

# ── Arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)    CONFIG="$2";     shift 2 ;;
        --solver)    SOLVER="$2";     shift 2 ;;
        --samples)   N_SAMPLES="$2";  shift 2 ;;
        --parallel)  N_PARALLEL="$2"; shift 2 ;;
        --out)       OUT_BASE="$2";   shift 2 ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$CONFIG" || -z "$SOLVER" ]]; then
    echo "ERROR: --config and --solver are required" >&2
    exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: cfg not found: $CONFIG" >&2
    exit 2
fi
if [[ "$SOLVER" != "hllc" && "$SOLVER" != "rusanov" ]]; then
    echo "ERROR: --solver must be hllc|rusanov (got $SOLVER)" >&2
    exit 2
fi
if ! [[ "$N_SAMPLES" =~ ^[0-9]+$ ]] || [[ "$N_SAMPLES" -le 0 ]]; then
    echo "ERROR: --samples must be a positive integer (got $N_SAMPLES)" >&2
    exit 2
fi
if [[ -z "$N_PARALLEL" ]]; then
    # Default: min(samples, nproc-ish). Cap at nproc so we never oversubscribe.
    AVAIL_CORES="$(nproc 2>/dev/null || echo 4)"
    if [[ "$N_SAMPLES" -lt "$AVAIL_CORES" ]]; then
        N_PARALLEL="$N_SAMPLES"
    else
        N_PARALLEL="$AVAIL_CORES"
    fi
fi
if ! [[ "$N_PARALLEL" =~ ^[0-9]+$ ]] || [[ "$N_PARALLEL" -le 0 ]]; then
    echo "ERROR: --parallel must be a positive integer (got $N_PARALLEL)" >&2
    exit 2
fi

# ── Verificarlo on PATH? ──────────────────────────────────────────────────────
if ! command -v verificarlo-c++ >/dev/null 2>&1; then
    # Fallback: look for the LSC install path (harmless on other hosts).
    if [[ -x /lsc/opt/verificarlo-2.4.0/bin/verificarlo-c++ ]]; then
        export PATH="/lsc/opt/verificarlo-2.4.0/bin:${PATH}"
        export LD_LIBRARY_PATH="/lsc/opt/verificarlo-2.4.0/lib:${LD_LIBRARY_PATH:-}"
    else
        echo "ERROR: verificarlo-c++ not on PATH and not at /lsc/opt/verificarlo-2.4.0." >&2
        echo "       export PATH=<path-to-verificarlo>/bin:\$PATH first." >&2
        exit 3
    fi
fi

# ── Build (shared between solvers; safe to re-enter) ──────────────────────────
BUILD_DIR="build-vfc-p53"
HRSC="${BUILD_DIR}/hrsc"
if [[ ! -x "$HRSC" ]]; then
    echo "[build] configuring + building with verificarlo-c++"
    CXX=verificarlo-c++ cmake -S . -B "$BUILD_DIR" \
        -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=double
    cmake --build "$BUILD_DIR" -j
fi
if [[ ! -x "$HRSC" ]]; then
    echo "ERROR: $HRSC missing after build" >&2
    exit 1
fi

# ── Output layout (matches SLURM array for analyzer parity) ───────────────────
OUT_DIR="${OUT_BASE}/${SOLVER}"
SEED_DIR="${OUT_DIR}/seeds"
LOG_DIR="logs/lovelace_$(date -u +%Y%m%dT%H%M%SZ)_${SOLVER}"
mkdir -p "$OUT_DIR" "$SEED_DIR" "$LOG_DIR"

# ── PRNG thread isolation (must be in env before xargs spawns workers) ───────
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

export CONFIG SOLVER OUT_DIR SEED_DIR LOG_DIR HRSC

echo "[lovelace] solver=${SOLVER}  cfg=${CONFIG}  N=${N_SAMPLES}  parallel=${N_PARALLEL}"
echo "[lovelace] out=${OUT_DIR}  logs=${LOG_DIR}"
echo "[lovelace] verificarlo-c++: $(command -v verificarlo-c++)"
START_TS=$(date +%s)

# ── Worker body (bash -c invoked by xargs; argv: $1 = sample_id) ──────────────
run_one() {
    local SAMPLE_ID="$1"
    local TAG=$(printf '%02d' "$SAMPLE_ID")
    local SAMPLE_DIR="${OUT_DIR}/sample_${TAG}"
    local SAMPLE_FILE="${SAMPLE_DIR}/grid.bin"
    local SAMPLE_CFG="${SAMPLE_DIR}/run.cfg"
    local SEED_CSV="${SEED_DIR}/seed_${TAG}.csv"
    local LOG_OUT="${LOG_DIR}/task_${TAG}.out"
    local LOG_ERR="${LOG_DIR}/task_${TAG}.err"
    mkdir -p "$SAMPLE_DIR"

    # 63-bit seed; interflop_mca --seed uses signed int64 so mask the top bit.
    local SEED_RAW SEED_DEC SEED_HEX
    SEED_RAW="$(od -An -N8 -tu8 /dev/urandom | tr -d ' \n')"
    SEED_DEC=$(( SEED_RAW & 0x7FFFFFFFFFFFFFFF ))
    SEED_HEX="$(printf '%016x' "$SEED_DEC")"

    # VFC_BACKENDS must include --seed inline (env-only VFC_BACKENDS_SEED is
    # silently ignored by interflop_mca — confirmed in 1D runners).
    local VFC_BASE="libinterflop_mca.so --mode=rr --precision-binary64=53"
    export VFC_BACKENDS="${VFC_BASE} --seed=${SEED_DEC}"

    # Overlay cfg: force binary output path per sample so the base cfg stays read-only.
    cp "$CONFIG" "$SAMPLE_CFG"
    {
        echo "solver = ${SOLVER}"
        echo "output_format = binary"
        echo "output_file = ${SAMPLE_FILE}"
    } >> "$SAMPLE_CFG"

    local TIMESTAMP
    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    if "$HRSC" "$SAMPLE_CFG" > "$LOG_OUT" 2> "$LOG_ERR"; then
        # Only write the seed CSV on success; a missing seed_NN.csv in the
        # analyzer's load_seeds() then flags the exact task that failed.
        {
            echo "sample_id,seed_dec,seed_hex,timestamp_utc"
            echo "${TAG},${SEED_DEC},0x${SEED_HEX},${TIMESTAMP}"
        } > "$SEED_CSV"
        echo "OK    task=${TAG} seed=${SEED_DEC}"
    else
        local RC=$?
        # Remove any partial output so stack_samples() doesn't stitch it.
        rm -f "$SAMPLE_FILE"
        echo "FAIL  task=${TAG} rc=${RC} stderr=${LOG_ERR}"
        return "$RC"
    fi
}
export -f run_one

# ── Dispatch: N samples across N_PARALLEL workers ─────────────────────────────
# xargs exits 123 if any child returned non-zero; `set -o pipefail` (top of
# file) propagates that through the `| tee` pipeline to $? below.
SUMMARY="${LOG_DIR}/summary.txt"
if seq 1 "$N_SAMPLES" | xargs -n1 -P "$N_PARALLEL" \
        bash -c 'run_one "$@"' _ | tee "$SUMMARY"; then
    STATUS=0
else
    STATUS=$?
fi

END_TS=$(date +%s)
ELAPSED=$(( END_TS - START_TS ))

N_OK=$(grep -c '^OK '   "$SUMMARY" || true)
N_FAIL=$(grep -c '^FAIL ' "$SUMMARY" || true)

echo "----"
echo "[lovelace] elapsed=${ELAPSED}s  OK=${N_OK}/${N_SAMPLES}  FAIL=${N_FAIL}"
echo "[lovelace] output: ${OUT_DIR}"
echo "[lovelace] seeds:  ${SEED_DIR}"
echo "[lovelace] logs:   ${LOG_DIR}"

if [[ "$N_FAIL" -gt 0 ]]; then
    echo "[lovelace] WARNING: ${N_FAIL} task(s) failed — inspect ${LOG_DIR}/task_*.err"
    echo "[lovelace] re-run only failed tasks with:"
    echo "    # e.g. retry samples 07 and 19 (keep other results):"
    echo "    # rm -rf ${OUT_DIR}/sample_07 ${OUT_DIR}/sample_19"
    echo "    # (then rerun the same command; completed samples are re-written idempotently)"
fi

exit "$STATUS"
