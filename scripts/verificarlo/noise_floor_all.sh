#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# noise_floor_all.sh — dispatch MCA p=53 noise-floor runs for A2-S2.
#
# Loops over the 4 test configs × 2 solvers (8 runs total), each producing
# 30 MCA p=53 samples → per-cell std field → noise_floor.npz.
#
# Usage (inside the verificarlo/verificarlo:latest container, from repo root):
#   docker run --rm -v "$(pwd)":/work -w /work \
#       verificarlo/verificarlo:latest \
#       bash scripts/verificarlo/noise_floor_all.sh
#
# Runtime: ~2–4 hours on laptop (240 MCA p=53 runs total).
# Output:  experiments/week4/noise_floor/<test>/<solver>/{sample_NN.txt, seeds.csv, noise_floor.npz}
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: must run from repo root (CMakeLists.txt not found here)" >&2
    exit 1
fi

# verificarlo/verificarlo:latest ships without cmake; install once per container
# (idempotent — dpkg-query early-exits if already present).
if ! command -v cmake >/dev/null 2>&1; then
    echo "[setup] cmake not found; installing via apt (one-time per container) ..."
    apt-get update -qq && apt-get install -y --no-install-recommends cmake ninja-build >/dev/null
fi

CFG_DIR="tests/cases/toro_1d"
OUT_BASE="experiments/week4/noise_floor"
N_SAMPLES="${N_SAMPLES:-30}"

TESTS=(sod stationary_contact toro2 toro4)
SOLVERS=(hllc rusanov)

mkdir -p "$OUT_BASE"

for test in "${TESTS[@]}"; do
    for solver in "${SOLVERS[@]}"; do
        if [[ "$solver" == "hllc" ]]; then
            cfg="${CFG_DIR}/${test}.cfg"
        else
            cfg="${CFG_DIR}/${test}_${solver}.cfg"
        fi

        if [[ ! -f "$cfg" ]]; then
            echo "[SKIP] ${test}/${solver}: cfg not found at ${cfg}" >&2
            continue
        fi

        out_dir="${OUT_BASE}/${test}/${solver}"
        echo ""
        echo "=================================================================="
        echo "  ${test} / ${solver}  (N=${N_SAMPLES})  cfg=${cfg}"
        echo "  → ${out_dir}"
        echo "=================================================================="

        bash scripts/verificarlo/noise_floor_run.sh "$cfg" "$solver" "$out_dir" "$N_SAMPLES"
    done
done

echo ""
echo "=================================================================="
echo "  A2-S2 overnight batch complete."
echo "  Next: python scripts/figures/plot_divergence_marker.py --mode noise_floor ..."
echo "=================================================================="
