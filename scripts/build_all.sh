#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: run from repository root." >&2
    exit 1
fi

GENERATOR="${GENERATOR:-Ninja}"
BUILD_TYPE="${BUILD_TYPE:-Release}"

resolve_python() {
    if [[ -n "${PYTHON:-}" ]]; then
        echo "$PYTHON"
        return 0
    fi

    local candidate
    local candidate_path
    for candidate in python3 python py; do
        if command -v "$candidate" >/dev/null 2>&1; then
            candidate_path="$(command -v "$candidate")"
            case "$candidate_path" in
                *WindowsApps*) continue ;;
            esac
            echo "$candidate"
            return 0
        fi
    done

    echo "ERROR: Python not found. Set PYTHON=/path/to/python." >&2
    return 1
}

PYTHON_BIN="$(resolve_python)"

variant_list="$(mktemp)"
probe_dir=""
cleanup() {
    rm -f "$variant_list"
    if [[ -n "$probe_dir" ]]; then
        rm -rf "$probe_dir"
    fi
}
trap cleanup EXIT

"$PYTHON_BIN" - <<'PY' > "$variant_list"
import json
from scripts.build_matrix import generate_variants

for v in generate_variants():
    print(f"{v.name}\t{v.build_dir}\t{json.dumps(v.cmake_args())}")
PY

append_variant() {
    local name="$1"
    local build_dir="$2"
    shift 2
    "$PYTHON_BIN" - "$name" "$build_dir" "$@" >> "$variant_list" <<'PY'
import json
import sys

print(f"{sys.argv[1]}\t{sys.argv[2]}\t{json.dumps(sys.argv[3:])}")
PY
}

strict_cpu_ok=0
probe_dir="$(mktemp -d)"
strict_cpu_flags=(
    -O2
    -ffp-contract=off
    -fno-fast-math
    -fexcess-precision=standard
    -fno-unsafe-math-optimizations
    -fno-strict-aliasing
)
if printf 'int main() { return 0; }\n' | "${CXX:-c++}" -x c++ "${strict_cpu_flags[@]}" -c -o "$probe_dir/strict_cpu_probe.o" - >/dev/null 2>&1; then
    strict_cpu_ok=1
else
    echo "WARNING: ${CXX:-c++} does not accept STRICT_IEEE GNU/Clang CPU flags; skipping STRICT_IEEE builds." >&2
fi
rm -rf "$probe_dir"
probe_dir=""

strict_cuda_ok=0
if [[ "$strict_cpu_ok" -eq 1 ]]; then
    if command -v nvcc >/dev/null 2>&1; then
        probe_dir="$(mktemp -d)"
        printf '__global__ void k() {}\nint main() { return 0; }\n' > "$probe_dir/strict_cuda_probe.cu"
        strict_cuda_flags=(
            --fmad=false
            --ftz=false
            --prec-div=true
            --prec-sqrt=true
        )
        strict_cuda_host_flags=()
        for flag in "${strict_cpu_flags[@]}"; do
            strict_cuda_host_flags+=("-Xcompiler=${flag}")
        done
        if nvcc "${strict_cuda_flags[@]}" "${strict_cuda_host_flags[@]}" -c "$probe_dir/strict_cuda_probe.cu" -o "$probe_dir/strict_cuda_probe.o" >/dev/null 2>&1; then
            strict_cuda_ok=1
        else
            echo "WARNING: nvcc does not accept STRICT_IEEE CUDA flags with GNU/Clang host forwards; skipping CUDA STRICT_IEEE builds." >&2
        fi
        rm -rf "$probe_dir"
        probe_dir=""
    else
        echo "WARNING: nvcc not found; skipping CUDA STRICT_IEEE builds." >&2
    fi
fi

if [[ "$strict_cpu_ok" -eq 1 ]]; then
    append_variant cpu-strict-double build-cpu-strict-double \
        -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON
    append_variant cpu-strict-float build-cpu-strict-float \
        -DFLOAT_PRECISION=float -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON

    if [[ "$strict_cuda_ok" -eq 1 ]]; then
        append_variant cuda-double-strict build-cuda-double-strict \
            -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_CUDA=ON -DENABLE_OPENMP=ON
        append_variant cuda-float-strict build-cuda-float-strict \
            -DFLOAT_PRECISION=float -DSTRICT_IEEE=ON -DENABLE_CUDA=ON -DENABLE_OPENMP=ON
    fi
fi

while IFS=$'\t' read -r name build_dir args_json; do
    mapfile -t cmake_args < <("$PYTHON_BIN" -c 'import json,sys; print("\n".join(json.loads(sys.argv[1])))' "$args_json")
    echo "==> configure ${name}"
    cmake -B "$build_dir" -G "$GENERATOR" -DCMAKE_BUILD_TYPE="$BUILD_TYPE" "${cmake_args[@]}"
    echo "==> build ${name}"
    cmake --build "$build_dir"
done < "$variant_list"
