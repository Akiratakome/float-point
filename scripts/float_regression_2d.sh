#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: run from repository root." >&2
    exit 1
fi

CFG_BASE="tests/cases/liska_wendroff_2d"
OUT_DIR="experiments/week4/float_regression/2d"

# Pick a real Python (see float_regression_1d.sh for rationale).
resolve_python() {
    if [[ -n "${PYTHON:-}" ]] && command -v "$PYTHON" >/dev/null 2>&1; then echo "$PYTHON"; return; fi
    for cand in py python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then
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

"$BUILD_DOUBLE" "${CFG_BASE}/config3_ref800.cfg"

for res in 200 400; do
    "$BUILD_DOUBLE" "${CFG_BASE}/config3_n${res}.cfg"
    cp "${OUT_DIR}/candidate_${res}.bin" "${OUT_DIR}/double_${res}.bin"
    "$BUILD_FLOAT" "${CFG_BASE}/config3_n${res}.cfg"
    cp "${OUT_DIR}/candidate_${res}.bin" "${OUT_DIR}/float_${res}.bin"
done

"$PY" scripts/float_regression_report.py --mode 2d --input "$OUT_DIR"

