#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: run from repository root." >&2
    exit 1
fi

GENERATOR="${GENERATOR:-Ninja}"
BUILD_TYPE="${BUILD_TYPE:-Release}"

python - <<'PY' | while IFS=$'\t' read -r name build_dir args_json; do
import json
from scripts.build_matrix import generate_variants

for v in generate_variants():
    print(f"{v.name}\t{v.build_dir}\t{json.dumps(v.cmake_args())}")
PY
    mapfile -t cmake_args < <(python -c 'import json,sys; print("\n".join(json.loads(sys.argv[1])))' "$args_json")
    echo "==> configure ${name}"
    cmake -B "$build_dir" -G "$GENERATOR" -DCMAKE_BUILD_TYPE="$BUILD_TYPE" "${cmake_args[@]}"
    echo "==> build ${name}"
    cmake --build "$build_dir"
done
