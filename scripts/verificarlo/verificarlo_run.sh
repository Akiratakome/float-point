#!/usr/bin/env bash
# Verificarlo MCA sampling for 1D Toro tests.
set -euo pipefail

N_SAMPLES=30
PRECISION=53
MCA_MODE="mca"
TESTS="sod toro2 toro3 toro4 toro5"
SOLVER=""
INST_FMA=0
REAL_FLOAT=0
COMPARE_FLOAT=0

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXP_DIR="${ROOT}/experiments/verificarlo"
CFG_DIR="${ROOT}/tests/cases/toro_1d"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--samples)   N_SAMPLES="$2"; shift 2 ;;
        -p|--precision) PRECISION="$2"; shift 2 ;;
        -m|--mode)      MCA_MODE="$2"; shift 2 ;;
        -t|--test)      TESTS="$2"; shift 2 ;;
        -s|--solver)    SOLVER="$2"; shift 2 ;;
        --inst-fma)     INST_FMA=1; shift ;;
        --real-float)   REAL_FLOAT=1; shift ;;
        --compare-float) COMPARE_FLOAT=1; shift ;;
        -h|--help)
            echo "Usage: $0 [-n samples] [-p precision] [-m mode] [-t test] [-s solver] [--inst-fma] [--real-float] [--compare-float]"
            echo "  -n  Number of MCA samples (default: 30)"
            echo "  -p  Mantissa precision bits (default: 53 for double build path)"
            echo "  -m  MCA mode for libinterflop_mca (default: mca)"
            echo "  -t  Test name(s): sod toro2 toro3 toro4 toro5 (default: all)"
            echo "  -s  Solver: hllc (default) or rusanov (uses *_rusanov.cfg files)"
            echo "  --inst-fma      Instrument FMA operations in Verificarlo build"
            echo "  --real-float    Build/run FLOAT_PRECISION=float with MCA backend"
            echo "  --compare-float Run both modes into deterministic subdirs:"
            echo "                  real_float/ and vprec_p24/"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ "$COMPARE_FLOAT" -eq 1 && "$REAL_FLOAT" -eq 1 ]]; then
    echo "INFO: --compare-float implies both modes; ignoring standalone --real-float."
fi

if [[ "$SOLVER" != "" && "$SOLVER" != "hllc" && "$SOLVER" != "rusanov" ]]; then
    echo "ERROR: --solver must be hllc or rusanov (got '${SOLVER}')." >&2
    exit 2
fi

if ! [[ "$N_SAMPLES" =~ ^[0-9]+$ ]] || [[ "$N_SAMPLES" -le 0 ]]; then
    echo "ERROR: --samples must be a positive integer." >&2
    exit 2
fi

if ! [[ "$PRECISION" =~ ^[0-9]+$ ]] || [[ "$PRECISION" -le 0 ]]; then
    echo "ERROR: --precision must be a positive integer." >&2
    exit 2
fi

CFG_SUFFIX=""
[[ "$SOLVER" == "rusanov" ]] && CFG_SUFFIX="_rusanov"

if ! command -v verificarlo-c++ >/dev/null 2>&1; then
    echo "ERROR: verificarlo-c++ not found in PATH." >&2
    exit 1
fi
if ! command -v cmake >/dev/null 2>&1; then
    echo "ERROR: cmake not found in PATH." >&2
    exit 1
fi

mkdir -p "${EXP_DIR}"

build_hrsc() {
    local build_dir="$1"
    local float_precision="$2"
    local -a cmake_args
    cmake_args=(
        -S "${ROOT}"
        -B "${build_dir}"
        -DCMAKE_BUILD_TYPE=Release
        -DENABLE_OPENMP=OFF
        "-DFLOAT_PRECISION=${float_precision}"
    )
    if [[ "$INST_FMA" -eq 1 ]]; then
        cmake_args+=("-DCMAKE_CXX_FLAGS=--inst-fma")
    fi
    CXX=verificarlo-c++ cmake "${cmake_args[@]}"
    cmake --build "${build_dir}" -j
    local hrsc="${build_dir}/hrsc"
    if [[ ! -x "${hrsc}" ]]; then
        echo "ERROR: expected executable not found: ${hrsc}" >&2
        exit 1
    fi
}

run_mode() {
    local mode_label="$1"
    local build_dir="$2"
    local float_precision="$3"
    local vfc_backends="$4"
    local out_dir="$5"
    local hrsc

    echo ""
    echo "============================================================"
    echo "  Verificarlo run mode: ${mode_label}"
    echo "  Samples:      ${N_SAMPLES}"
    echo "  Float build:  ${float_precision}"
    echo "  Mode:         ${MCA_MODE}"
    echo "  Solver:       ${SOLVER:-hllc}"
    echo "  Tests:        ${TESTS}"
    echo "  Build dir:    ${build_dir}"
    echo "  Output dir:   ${out_dir}"
    echo "============================================================"

    build_hrsc "${build_dir}" "${float_precision}"
    hrsc="${build_dir}/hrsc"
    mkdir -p "${out_dir}"

    export OMP_NUM_THREADS=1
    export VFC_BACKENDS="${vfc_backends}"
    echo "[mca] VFC_BACKENDS=${VFC_BACKENDS}"

    for test in ${TESTS}; do
        local cfg="${CFG_DIR}/${test}${CFG_SUFFIX}.cfg"
        if [[ ! -f "${cfg}" ]]; then
            echo "  [SKIP] ${test}: config not found at ${cfg}"
            continue
        fi
        local test_dir="${out_dir}/${test}"
        mkdir -p "${test_dir}"
        echo "  --- ${test} (${N_SAMPLES} samples) ---"
        for i in $(seq 1 "${N_SAMPLES}"); do
            local outfile="${test_dir}/run_$(printf '%03d' "${i}").txt"
            "${hrsc}" "${cfg}" > "${outfile}" 2>/dev/null
            if (( i % 10 == 0 )) || (( i == N_SAMPLES )); then
                echo "    ${i}/${N_SAMPLES} done"
            fi
        done
    done

    echo "  --- IEEE reference run ---"
    export VFC_BACKENDS="libinterflop_ieee.so"
    for test in ${TESTS}; do
        local cfg="${CFG_DIR}/${test}${CFG_SUFFIX}.cfg"
        [[ ! -f "${cfg}" ]] && continue
        local ref_file="${out_dir}/${test}/reference_ieee.txt"
        "${hrsc}" "${cfg}" > "${ref_file}" 2>/dev/null
    done
}

TAG_BASE="p${PRECISION}_${MCA_MODE}"
[[ "$INST_FMA" -eq 1 ]] && TAG_BASE="${TAG_BASE}_fma"
[[ -n "$CFG_SUFFIX" ]] && TAG_BASE="${TAG_BASE}_rusanov"

if [[ "$COMPARE_FLOAT" -eq 1 ]]; then
    TAG_COMPARE="p24_${MCA_MODE}"
    [[ "$INST_FMA" -eq 1 ]] && TAG_COMPARE="${TAG_COMPARE}_fma"
    [[ -n "$CFG_SUFFIX" ]] && TAG_COMPARE="${TAG_COMPARE}_rusanov"
    if [[ "$PRECISION" -ne 24 ]]; then
        echo "INFO: --compare-float uses fixed p24 in both modes; ignoring --precision=${PRECISION}."
    fi
    OUT_DIR="${EXP_DIR}/runs_compare_${TAG_COMPARE}"
    run_mode \
        "real_float" \
        "${ROOT}/build-vfc-real" \
        "float" \
        "libinterflop_mca.so --mode=${MCA_MODE} --precision-binary32=24" \
        "${OUT_DIR}/real_float"
    run_mode \
        "vprec_p24" \
        "${ROOT}/build-vfc-vprec" \
        "double" \
        "libinterflop_vprec.so --precision-binary64=24" \
        "${OUT_DIR}/vprec_p24"
else
    if [[ "$REAL_FLOAT" -eq 1 ]]; then
        EFF_FLOAT_PREC="${PRECISION}"
        if [[ "$EFF_FLOAT_PREC" -gt 24 ]]; then
            echo "INFO: --real-float with precision>${24} is clamped to 24 for binary32."
            EFF_FLOAT_PREC=24
        fi
        MODE_TAG="real_float"
        TAG_REAL="p${EFF_FLOAT_PREC}_${MCA_MODE}"
        [[ "$INST_FMA" -eq 1 ]] && TAG_REAL="${TAG_REAL}_fma"
        [[ -n "$CFG_SUFFIX" ]] && TAG_REAL="${TAG_REAL}_rusanov"
        OUT_DIR="${EXP_DIR}/runs_${MODE_TAG}_${TAG_REAL}"
        run_mode \
            "${MODE_TAG}" \
            "${ROOT}/build-vfc-real" \
            "float" \
            "libinterflop_mca.so --mode=${MCA_MODE} --precision-binary32=${EFF_FLOAT_PREC}" \
            "${OUT_DIR}"
    else
        MODE_TAG="double_mca"
        OUT_DIR="${EXP_DIR}/runs_${MODE_TAG}_${TAG_BASE}"
        run_mode \
            "${MODE_TAG}" \
            "${ROOT}/build-vfc-p53" \
            "double" \
            "libinterflop_mca.so --mode=${MCA_MODE} --precision-binary64=${PRECISION}" \
            "${OUT_DIR}"
    fi
fi

echo ""
echo "============================================================"
echo "All samples saved under: ${OUT_DIR}"
echo "Analyse baseline: python scripts/verificarlo/verificarlo_analysis.py --vfc-dir ${OUT_DIR}"
if [[ "$COMPARE_FLOAT" -eq 1 ]]; then
    echo "Compare modes:    python scripts/figures/plot_real_vs_vprec.py ${OUT_DIR}/real_float ${OUT_DIR}/vprec_p24 --tests sod"
fi
echo "============================================================"
