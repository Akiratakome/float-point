#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: run from repository root." >&2
    exit 1
fi

CFG_DIR="tests/cases/toro_1d"
OUT_DIR="experiments/week4/float_regression/1d"
TESTS=(sod toro2 toro3 toro4 toro5 stationary_contact)

# Pick a real Python: prefer $PYTHON env var, else py launcher, else python3,
# else python. On MSYS/Git-Bash the bare `python` may resolve to the
# Microsoft Store stub (no real interpreter), so fall through to alternatives.
resolve_python() {
    if [[ -n "${PYTHON:-}" ]]; then
        if command -v "$PYTHON" >/dev/null 2>&1 || [[ -x "$PYTHON" ]]; then
            echo "$PYTHON"
            return
        fi
    fi
    for cand in py python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then
            # MSYS path: pruning the WindowsApps stub
            local p; p="$(command -v "$cand")"
            case "$p" in *WindowsApps*) continue;; esac
            echo "$cand"; return
        fi
    done
    echo "ERROR: no python interpreter found (set PYTHON=...)" >&2
    exit 1
}
PY="$(resolve_python)"

# Resolve binary path on both Linux (no suffix) and MSYS/Cygwin (.exe).
resolve_bin() {
    local base="$1"
    if   [[ -x "${base}" ]];     then echo "${base}"
    elif [[ -x "${base}.exe" ]]; then echo "${base}.exe"
    else
        echo "ERROR: expected binary at ${base} (or ${base}.exe)" >&2
        exit 1
    fi
}
BUILD_DOUBLE="$(resolve_bin build-double/hrsc)"
BUILD_FLOAT="$(resolve_bin build-float/hrsc)"

mkdir -p "$OUT_DIR"

run_with_dump() {
    local bin="$1"
    local cfg="$2"
    local tag="$3"
    local out_csv="$4"
    if [[ "$bin" == *.exe ]] && grep -qi microsoft /proc/version 2>/dev/null; then
        # WSL interop does not reliably propagate inline env assignments to
        # Win32 .exe children, so set them inside cmd.exe for this case.
        local bin_win="${bin//\//\\}"
        local cfg_win="${cfg//\//\\}"
        cmd.exe /C "set HRSC_DUMP_DIR=${OUT_DIR}&& set HRSC_DUMP_TAG=${tag}&& ${bin_win} ${cfg_win}" > "$out_csv"
    else
        HRSC_DUMP_DIR="$OUT_DIR" HRSC_DUMP_TAG="$tag" "$bin" "$cfg" > "$out_csv"
    fi
}

for test in "${TESTS[@]}"; do
    cfg="${CFG_DIR}/convergence_${test}.cfg"
    if [[ ! -f "$cfg" ]]; then
        echo "ERROR: missing config $cfg" >&2
        exit 1
    fi
    run_with_dump "$BUILD_DOUBLE" "$cfg" "double" "${OUT_DIR}/${test}_double.csv"
    run_with_dump "$BUILD_FLOAT" "$cfg" "float" "${OUT_DIR}/${test}_float.csv"
done

"$PY" scripts/regression/float_regression_report.py --mode 1d --input "$OUT_DIR"
