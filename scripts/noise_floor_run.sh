#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# noise_floor_run.sh — MCA p=53 noise-floor sampling for a single (test, solver).
#
# Stage 2 (A2-S2). Builds once with verificarlo-c++, then runs the solver N
# times with independent /dev/urandom seeds, recording each seed to a CSV for
# provenance. Finally calls scripts/compute_noise_floor.py to emit the .npz
# noise-floor envelope consumed by scripts/plot_divergence_marker.py
# (mode=noise_floor).
#
# Usage (run inside WSL / Docker-Verificarlo from repo root):
#     bash scripts/noise_floor_run.sh <TEST_CFG> <SOLVER> <OUT_DIR> [N_SAMPLES]
#
# Arguments:
#     TEST_CFG   : path to HRSC config file, e.g. tests/cases/toro_1d/sod.cfg
#     SOLVER     : solver tag for provenance ('hllc' | 'rusanov'); the actual
#                  solver is determined by the config file's contents.
#     OUT_DIR    : output directory; samples + seeds.csv + noise_floor.npz here.
#     N_SAMPLES  : MCA sample count (default 30 per plan §A2.1).
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Arg parsing ───────────────────────────────────────────────────────────────
if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "Usage: $0 <TEST_CFG> <SOLVER> <OUT_DIR> [N_SAMPLES]" >&2
    exit 2
fi

TEST_CFG="$1"
SOLVER="$2"
OUT_DIR="$3"
N_SAMPLES="${4:-30}"           # Stage 2 default per plan §A2.1

if [[ ! -f "$TEST_CFG" ]]; then
    echo "ERROR: TEST_CFG not found: $TEST_CFG" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

# ── cmake bootstrap ──────────────────────────────────────────────────────────
# verificarlo/verificarlo:latest is built on Ubuntu 20.04 whose apt cmake is
# 3.16; this repo's CMakeLists.txt requires >= 3.18. pip3's manylinux wheel
# ships a prebuilt cmake into /usr/local/bin (no compile, ~5s first time,
# instant afterwards). Idempotent — skips if cmake >= 3.18 already on PATH.
NEED_CMAKE_MIN="3.18"
have_new_cmake() { command -v cmake >/dev/null 2>&1 && \
    [[ "$(printf '%s\n' "$NEED_CMAKE_MIN" "$(cmake --version|head -1|awk '{print $3}')" | sort -V | head -1)" == "$NEED_CMAKE_MIN" ]]; }
if ! have_new_cmake; then
    echo "[bootstrap] cmake >= ${NEED_CMAKE_MIN} missing; pip3 install cmake ..."
    pip3 install --quiet --upgrade cmake
    export PATH="/usr/local/bin:${PATH}"
fi

# ── Build (idempotent) ────────────────────────────────────────────────────────
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

# ── PRNG thread isolation (matches verificarlo_run_2d.sh / SLURM array) ──────
# Plan §A2.5 / §A3.3: libinterflop's MCA PRNG is not documented thread-safe,
# and compute_dt()'s OpenMP `reduction(max:...)` would non-deterministically
# reorder additions across threads — both contaminate the per-cell std field.
# Pin to one thread; per-sample independence comes from the /dev/urandom seed
# loop below, not from in-process parallelism.
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# ── MCA backend base string (seed appended per-sample via --seed=<N>) ─────────
# Verificarlo's interflop_mca reads seed from the backend CLI flag --seed=<N>,
# NOT from the VFC_BACKENDS_SEED env var (empirically verified 2026-04-22:
# two runs with identical VFC_BACKENDS_SEED produced non-identical outputs;
# two runs with identical --seed=<N> inline in VFC_BACKENDS produced
# bit-identical outputs with the banner reporting `seed = <N> (fixed)`).
# If seed is omitted, the backend auto-seeds from system entropy per process —
# that gives independent samples but loses reproducibility.
VFC_BASE="libinterflop_mca.so --mode=rr --precision-binary64=53"
echo "[mca] VFC_BASE=${VFC_BASE}"

# ── Seeds CSV (header) ────────────────────────────────────────────────────────
# seed_dec is the decimal uint64 actually passed to --seed=; seed_hex preserved
# for human debug. Both reference the same 64-bit draw from /dev/urandom.
SEEDS_CSV="${OUT_DIR}/seeds.csv"
echo "sample_id,seed_dec,seed_hex,timestamp_utc" > "$SEEDS_CSV"

# ── Run N samples with independent /dev/urandom seeds ────────────────────────
echo "[run] N_SAMPLES=${N_SAMPLES}  TEST_CFG=${TEST_CFG}  SOLVER=${SOLVER}"
for k in $(seq 1 "$N_SAMPLES"); do
    # 63-bit seed from the kernel's CSPRNG; one draw per sample.
    # -tu8 emits unsigned decimal; interflop_mca's --seed parser is signed
    # int64, so values > 2^63-1 get rejected as "invalid value". Mask the top
    # bit down to 63 bits — still > 2^62 ≈ 4.6e18 entropy, far above any
    # birthday-collision concern at N=30.
    SEED_RAW="$(od -An -N8 -tu8 /dev/urandom | tr -d ' \n')"
    SEED_DEC=$(( SEED_RAW & 0x7FFFFFFFFFFFFFFF ))
    SEED_HEX="$(printf '%016x' "$SEED_DEC")"
    export VFC_BACKENDS="${VFC_BASE} --seed=${SEED_DEC}"

    SAMPLE_ID="$(printf '%02d' "$k")"
    SAMPLE_FILE="${OUT_DIR}/sample_${SAMPLE_ID}.txt"
    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    "$HRSC" "$TEST_CFG" > "$SAMPLE_FILE"

    echo "${SAMPLE_ID},${SEED_DEC},0x${SEED_HEX},${TIMESTAMP}" >> "$SEEDS_CSV"

    if (( k % 10 == 0 )) || (( k == N_SAMPLES )); then
        echo "  ${k}/${N_SAMPLES} samples complete"
    fi
done

# ── Analysis: per-cell std → noise_floor.npz ─────────────────────────────────
NPZ_OUT="${OUT_DIR}/noise_floor.npz"
echo "[analysis] computing per-cell std → ${NPZ_OUT}"
python3 scripts/compute_noise_floor.py \
    --samples "${OUT_DIR}"/sample_??.txt \
    --seeds   "$SEEDS_CSV" \
    --out     "$NPZ_OUT" \
    --solver  "$SOLVER" \
    --cfg     "$TEST_CFG"

echo "[done] ${NPZ_OUT}"
