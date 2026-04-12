#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Verificarlo Monte Carlo Arithmetic (MCA) sampling for HRSC solver
#
# Usage (inside WSL2 or Linux with Verificarlo installed):
#   cd /path/to/floatpoint
#   bash scripts/verificarlo_run.sh              # default: 30 samples, all tests
#   bash scripts/verificarlo_run.sh -n 50        # 50 samples
#   bash scripts/verificarlo_run.sh -t sod       # only Sod test
#   bash scripts/verificarlo_run.sh -p 24        # simulate float32 (24-bit mantissa)
#
# All output goes to experiments/verificarlo/ (gitignored).
# Uses configs from tests/cases/toro_1d/ (solver defaults to setprecision(17)).
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
N_SAMPLES=30
PRECISION=53          # binary64 mantissa bits (53 = full double, 24 = float32)
MCA_MODE="mca"        # mca | ieee | mca-rr (relative rounding)
TESTS="sod toro2 toro3 toro4 toro5"
INST_FMA=""           # set to "--inst-fma" to instrument FMA operations

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP_DIR="${ROOT}/experiments/verificarlo"
CFG_DIR="${ROOT}/tests/cases/toro_1d"

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--samples)   N_SAMPLES="$2";  shift 2 ;;
        -p|--precision) PRECISION="$2";  shift 2 ;;
        -m|--mode)      MCA_MODE="$2";   shift 2 ;;
        -t|--test)      TESTS="$2";      shift 2 ;;
        --inst-fma)     INST_FMA="--inst-fma"; shift ;;
        -h|--help)
            echo "Usage: $0 [-n samples] [-p precision] [-m mode] [-t test] [--inst-fma]"
            echo "  -n  Number of MCA samples (default: 30)"
            echo "  -p  Mantissa precision bits (default: 53=double, 24=float)"
            echo "  -m  MCA mode: mca | ieee | mca-rr (default: mca)"
            echo "  -t  Test name(s): sod toro2 toro3 toro4 toro5 (default: all)"
            echo "  --inst-fma  Instrument FMA operations"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Tag for output directory (allows multiple runs with different settings)
TAG="p${PRECISION}_${MCA_MODE}"
[[ -n "$INST_FMA" ]] && TAG="${TAG}_fma"
OUT_DIR="${EXP_DIR}/runs_${TAG}"

# ── Check Verificarlo is available ────────────────────────────────────────────
if ! command -v verificarlo-c++ &>/dev/null; then
    echo "ERROR: verificarlo-c++ not found in PATH."
    echo "Install: https://github.com/verificarlo/verificarlo"
    echo "Docker:  docker run -v \$(pwd):/work -w /work verificarlo/verificarlo bash scripts/verificarlo_run.sh"
    exit 1
fi

echo "============================================================"
echo "  Verificarlo MCA Sampling"
echo "  Samples:   ${N_SAMPLES}"
echo "  Precision: ${PRECISION} bits (mantissa)"
echo "  Mode:      ${MCA_MODE}"
echo "  FMA:       ${INST_FMA:-off}"
echo "  Tests:     ${TESTS}"
echo "  Output:    ${OUT_DIR}"
echo "============================================================"

# ── Build with Verificarlo ────────────────────────────────────────────────────
echo ""
echo "[1/3] Building with Verificarlo compiler..."

HRSC="${EXP_DIR}/hrsc_vfc"
verificarlo-c++ -O2 -std=c++17 ${INST_FMA} \
    -I"${ROOT}/src" -I"${ROOT}/tests/cases/toro_1d" \
    "${ROOT}/src/main.cpp" -o "${HRSC}" 2>&1

if [[ ! -x "$HRSC" ]]; then
    echo "ERROR: Build failed."
    exit 1
fi
echo "Build OK: ${HRSC}"

# ── Configure MCA backend ────────────────────────────────────────────────────
export VFC_BACKENDS="libinterflop_mca.so --mode=${MCA_MODE} --precision-binary64=${PRECISION}"
echo ""
echo "[2/3] VFC_BACKENDS=${VFC_BACKENDS}"

# ── Run MCA samples ──────────────────────────────────────────────────────────
echo ""
echo "[3/3] Running MCA samples..."

for test in ${TESTS}; do
    cfg="${CFG_DIR}/${test}.cfg"
    if [[ ! -f "$cfg" ]]; then
        echo "  [SKIP] ${test}: config not found at ${cfg}"
        continue
    fi

    test_dir="${OUT_DIR}/${test}"
    mkdir -p "${test_dir}"

    echo ""
    echo "  --- ${test} (${N_SAMPLES} samples) ---"

    for i in $(seq 1 "${N_SAMPLES}"); do
        outfile="${test_dir}/run_$(printf '%03d' $i).txt"
        "${HRSC}" "${cfg}" > "${outfile}" 2>/dev/null
        if (( i % 10 == 0 )) || (( i == N_SAMPLES )); then
            echo "    ${i}/${N_SAMPLES} done"
        fi
    done
done

# ── IEEE reference run (no perturbation) ──────────────────────────────────────
echo ""
echo "  --- IEEE reference run (no perturbation) ---"
export VFC_BACKENDS="libinterflop_ieee.so"
for test in ${TESTS}; do
    cfg="${CFG_DIR}/${test}.cfg"
    [[ ! -f "$cfg" ]] && continue
    ref_file="${OUT_DIR}/${test}/reference_ieee.txt"
    "${HRSC}" "${cfg}" > "${ref_file}" 2>/dev/null
done

echo ""
echo "============================================================"
echo "  All samples saved to: ${OUT_DIR}/"
echo "  Analyse: python scripts/verificarlo_analysis.py --vfc-dir ${OUT_DIR}"
echo "============================================================"
