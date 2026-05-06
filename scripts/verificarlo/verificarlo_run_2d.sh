#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# verificarlo_run_2d.sh — Week 4 Task A3 local 2D MCA runner (smoke/feasibility).
#
# Builds (once) with verificarlo-c++ into build-vfc-p53 — the same directory
# used by scripts/verificarlo/noise_floor_run.sh — and fires N independent MCA samples of
# a 2D Liska-Wendroff config, each with a fresh /dev/urandom seed. Raw 2D
# outputs are written as binary grids:
#   $OUT/sample_NN/grid.bin
# Seeds are written as per-sample CSV files:
#   $OUT/seeds/seed_NN.csv
#
# SLURM production is explicitly out of scope for this script; analysis is
# deferred to a Week 5 2D analyzer (compute_noise_floor.py is 1D-only).
#
# Usage (from repo root, inside WSL / Docker-Verificarlo):
#     bash scripts/verificarlo/verificarlo_run_2d.sh \
#         [--config CFG] [--solver hllc|rusanov] \
#         [--samples N] [--out OUTDIR]
#
# Defaults:
#     --config    tests/cases/liska_wendroff_2d/config3.cfg
#     --solver    omitted by default; effective solver comes from config
#                 (config3.cfg currently sets solver = rusanov)
#                 If --solver is given without --config, script auto-selects
#                 the bundled config whose solver matches --solver.
#                 If both --solver and --config are given, --solver overrides
#                 solver in the copied per-sample run.cfg.
#     --samples   required (no default; pass 3 for smoke or 5 for feasibility)
#     --out       experiments/week4/2d_vfc/smoke/<test>/<solver-effective>
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Repo-root guard ───────────────────────────────────────────────────────────
if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: must be run from repo root (CMakeLists.txt not found here)" >&2
    exit 1
fi

# ── Defaults ──────────────────────────────────────────────────────────────────
CFG_BUNDLED_A="tests/cases/liska_wendroff_2d/config3.cfg"
CFG_BUNDLED_B="tests/cases/liska_wendroff_2d/config3_rusanov.cfg"
CFG_DEFAULT_BASE="$CFG_BUNDLED_A"

CONFIG=""
SOLVER=""
N_SAMPLES=""
OUT_DIR=""

# ── Arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            [[ $# -lt 2 ]] && { echo "ERROR: --config requires a value" >&2; exit 2; }
            CONFIG="$2"; shift 2 ;;
        --solver)
            [[ $# -lt 2 ]] && { echo "ERROR: --solver requires a value" >&2; exit 2; }
            SOLVER="$2"; shift 2 ;;
        --samples)
            [[ $# -lt 2 ]] && { echo "ERROR: --samples requires a value" >&2; exit 2; }
            N_SAMPLES="$2"; shift 2 ;;
        --out)
            [[ $# -lt 2 ]] && { echo "ERROR: --out requires a value" >&2; exit 2; }
            OUT_DIR="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,/^$/p' "$0" | sed -n '/^# Usage/,/^# ───/p'
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Usage: bash scripts/verificarlo/verificarlo_run_2d.sh [--config CFG] [--solver hllc|rusanov] [--samples N] [--out OUTDIR]" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$N_SAMPLES" ]]; then
    echo "ERROR: --samples is required (use 3 for smoke, 5 for feasibility)." >&2
    exit 2
fi
if ! [[ "$N_SAMPLES" =~ ^[0-9]+$ ]] || [[ "$N_SAMPLES" -le 0 ]]; then
    echo "ERROR: --samples must be a positive integer (got '$N_SAMPLES')." >&2
    exit 2
fi

# Resolve solver vs config interaction.
if [[ -n "$SOLVER" ]] && [[ "$SOLVER" != "hllc" && "$SOLVER" != "rusanov" ]]; then
    echo "ERROR: --solver must be 'hllc' or 'rusanov' (got '$SOLVER')" >&2
    exit 2
fi

read_solver_from_cfg() {
    local cfg="$1"
    awk -F= '/^[[:space:]]*solver[[:space:]]*=/ {gsub(/[[:space:]]/,"",$2); print $2; exit}' "$cfg"
}

pick_bundled_config_for_solver() {
    local wanted="$1"
    local candidate cfg_solver
    for candidate in "$CFG_BUNDLED_A" "$CFG_BUNDLED_B"; do
        [[ -f "$candidate" ]] || continue
        cfg_solver="$(read_solver_from_cfg "$candidate")"
        if [[ "$cfg_solver" == "$wanted" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

if [[ -z "$CONFIG" ]]; then
    if [[ -n "$SOLVER" ]]; then
        if ! CONFIG="$(pick_bundled_config_for_solver "$SOLVER")"; then
            echo "ERROR: no bundled config declares solver='$SOLVER' among:" >&2
            echo "       $CFG_BUNDLED_A" >&2
            echo "       $CFG_BUNDLED_B" >&2
            exit 2
        fi
    else
        CONFIG="$CFG_DEFAULT_BASE"
    fi
fi

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: CONFIG not found: $CONFIG" >&2
    exit 1
fi

CONFIG_SOLVER="$(read_solver_from_cfg "$CONFIG")"
if [[ -n "$CONFIG_SOLVER" ]] && [[ "$CONFIG_SOLVER" != "hllc" && "$CONFIG_SOLVER" != "rusanov" ]]; then
    echo "ERROR: solver in config must be hllc or rusanov (got '$CONFIG_SOLVER' in '$CONFIG')." >&2
    exit 2
fi

if [[ -n "$SOLVER" ]]; then
    SOLVER_EFFECTIVE="$SOLVER"
    SOLVER_SOURCE="cli"
else
    SOLVER_EFFECTIVE="$CONFIG_SOLVER"
    SOLVER_SOURCE="config"
fi

if [[ -z "${SOLVER_EFFECTIVE:-}" ]]; then
    echo "ERROR: no solver resolved. Add 'solver = hllc|rusanov' to '$CONFIG' or pass --solver." >&2
    exit 2
fi
if [[ "$SOLVER_EFFECTIVE" != "hllc" && "$SOLVER_EFFECTIVE" != "rusanov" ]]; then
    echo "ERROR: effective solver must be hllc or rusanov (got '$SOLVER_EFFECTIVE')." >&2
    exit 2
fi

# Derive test name from cfg (for default OUT_DIR).
TEST_NAME="$(awk -F= '/^[[:space:]]*test[[:space:]]*=/ {gsub(/[[:space:]]/,"",$2); print $2; exit}' "$CONFIG")"
if [[ -z "${TEST_NAME:-}" ]]; then
    TEST_NAME="unknown"
fi

if [[ -z "$OUT_DIR" ]]; then
    OUT_DIR="experiments/week4/2d_vfc/smoke/${TEST_NAME}/${SOLVER_EFFECTIVE}"
fi

mkdir -p "$OUT_DIR"
mkdir -p "${OUT_DIR}/seeds"

# ── cmake bootstrap (see noise_floor_run.sh for rationale) ───────────────────
NEED_CMAKE_MIN="3.18"
have_new_cmake() { command -v cmake >/dev/null 2>&1 && \
    [[ "$(printf '%s\n' "$NEED_CMAKE_MIN" "$(cmake --version|head -1|awk '{print $3}')" | sort -V | head -1)" == "$NEED_CMAKE_MIN" ]]; }
if ! have_new_cmake; then
    echo "[bootstrap] cmake >= ${NEED_CMAKE_MIN} missing; pip3 install cmake ..."
    pip3 install --quiet --upgrade cmake
    export PATH="/usr/local/bin:${PATH}"
fi

# ── Build (idempotent; shares build dir with noise_floor_run.sh) ──────────────
BUILD_DIR="build-vfc-p53"
if [[ ! -d "$BUILD_DIR" ]]; then
    echo "[build] $BUILD_DIR not present; configuring + building with verificarlo-c++"
    CXX=verificarlo-c++ cmake -S . -B "$BUILD_DIR" \
        -DCMAKE_BUILD_TYPE=Release \
        -DFLOAT_PRECISION=double
    cmake --build "$BUILD_DIR" -j
else
    echo "[build] reusing existing $BUILD_DIR"
fi

HRSC="${BUILD_DIR}/hrsc"
if [[ ! -x "$HRSC" ]]; then
    echo "ERROR: $HRSC missing or not executable after build" >&2
    exit 1
fi

# ── MCA backend base (seed appended per-sample via --seed=<N>) ────────────────
# See scripts/verificarlo/noise_floor_run.sh comment for seed-mechanism rationale:
# VFC_BACKENDS_SEED env var is silently ignored by interflop_mca; the seed
# must be inlined in VFC_BACKENDS as --seed=<decimal uint64>.
VFC_BASE="libinterflop_mca.so --mode=rr --precision-binary64=53"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
echo "[mca] VFC_BASE=${VFC_BASE}"
echo "[cfg] CONFIG=${CONFIG}  CONFIG_SOLVER=${CONFIG_SOLVER:-unset}  SOLVER_EFFECTIVE=${SOLVER_EFFECTIVE} (source=${SOLVER_SOURCE})  SAMPLES=${N_SAMPLES}  OUT=${OUT_DIR}"
if [[ -n "$SOLVER" && -n "$CONFIG_SOLVER" && "$SOLVER" != "$CONFIG_SOLVER" ]]; then
    echo "[cfg] note: --solver=${SOLVER} overrides config solver=${CONFIG_SOLVER} in generated run.cfg"
fi

# ── Run N samples with independent /dev/urandom seeds ─────────────────────────
for k in $(seq 1 "$N_SAMPLES"); do
    # 63-bit seed (mask top bit): interflop_mca --seed uses signed int64.
    SEED_RAW="$(od -An -N8 -tu8 /dev/urandom | tr -d ' \n')"
    SEED_DEC=$(( SEED_RAW & 0x7FFFFFFFFFFFFFFF ))
    SEED_HEX="$(printf '%016x' "$SEED_DEC")"
    export VFC_BACKENDS="${VFC_BASE} --seed=${SEED_DEC}"
    export VERIFICARLO_MCA_SEED="0x${SEED_HEX}"
    export VFC_BACKEND_SEED="0x${SEED_HEX}"

    SAMPLE_ID="$(printf '%02d' "$k")"
    SAMPLE_DIR="${OUT_DIR}/sample_${SAMPLE_ID}"
    SAMPLE_FILE="${SAMPLE_DIR}/grid.bin"
    SAMPLE_CFG="${SAMPLE_DIR}/run.cfg"
    SEED_CSV="${OUT_DIR}/seeds/seed_${SAMPLE_ID}.csv"
    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    mkdir -p "$SAMPLE_DIR"

    cp "$CONFIG" "$SAMPLE_CFG"
    {
        echo "solver = ${SOLVER_EFFECTIVE}"
        echo "output_format = binary"
        echo "output_file = ${SAMPLE_FILE}"
    } >> "$SAMPLE_CFG"

    "$HRSC" "$SAMPLE_CFG" > /dev/null

    {
        echo "sample_id,seed_dec,seed_hex,timestamp_utc"
        echo "${SAMPLE_ID},${SEED_DEC},0x${SEED_HEX},${TIMESTAMP}"
    } > "$SEED_CSV"
    echo "  ${k}/${N_SAMPLES} done (seed=${SEED_DEC})"
done

echo "[done] raw 2D binary samples + per-sample seeds in ${OUT_DIR}"
echo "[note] analysis deferred to Week 5 2D analyzer (1D compute_noise_floor.py N/A)"
