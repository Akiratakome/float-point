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

# ── MCA backend: round-to-random at full binary64 mantissa (p=53) ─────────────
export VFC_BACKENDS="libinterflop_mca.so --mode=rr --precision-binary64=53"
echo "[mca] VFC_BACKENDS=${VFC_BACKENDS}"

# ── Seeds CSV (header) ────────────────────────────────────────────────────────
SEEDS_CSV="${OUT_DIR}/seeds.csv"
echo "sample_id,seed_hex,timestamp_utc" > "$SEEDS_CSV"

# ── Run N samples with independent /dev/urandom seeds ────────────────────────
echo "[run] N_SAMPLES=${N_SAMPLES}  TEST_CFG=${TEST_CFG}  SOLVER=${SOLVER}"
for k in $(seq 1 "$N_SAMPLES"); do
    # 64-bit hex seed from the kernel's CSPRNG; one draw per sample.
    SEED_HEX="$(od -An -N8 -tx8 /dev/urandom | tr -d ' \n')"
    export VFC_BACKENDS_SEED="0x${SEED_HEX}"

    SAMPLE_ID="$(printf '%02d' "$k")"
    SAMPLE_FILE="${OUT_DIR}/sample_${SAMPLE_ID}.txt"
    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    "$HRSC" "$TEST_CFG" > "$SAMPLE_FILE"

    echo "${SAMPLE_ID},0x${SEED_HEX},${TIMESTAMP}" >> "$SEEDS_CSV"

    if (( k % 10 == 0 )) || (( k == N_SAMPLES )); then
        echo "  ${k}/${N_SAMPLES} samples complete"
    fi
done

# ── Analysis: per-cell std → noise_floor.npz ─────────────────────────────────
NPZ_OUT="${OUT_DIR}/noise_floor.npz"
echo "[analysis] computing per-cell std → ${NPZ_OUT}"
python scripts/compute_noise_floor.py \
    --samples "${OUT_DIR}"/sample_??.txt \
    --seeds   "$SEEDS_CSV" \
    --out     "$NPZ_OUT" \
    --solver  "$SOLVER" \
    --cfg     "$TEST_CFG"

echo "[done] ${NPZ_OUT}"
