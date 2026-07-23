#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-artifacts/report2_w16_w17_csc_bundle.tar.gz}"
mkdir -p "$(dirname "${OUT}")"
TMP="$(mktemp)"
LIST="$(mktemp)"
trap 'rm -f "${TMP}" "${LIST}"' EXIT

{
    printf '%s\n' CMakeLists.txt
    find cmake src scripts tests docs -type f
    find experiments/week15 experiments/week16 experiments/week17 -type f \
        \( -name 'summary.json' -o -name 'summary.csv' -o -name 'summary.md' \
           -o -name 'environment.json' -o -name 'manifest.json' -o -name 'README.md' \
           -o -name '*.png' -o -name '*.cfg' \)
} | sort -u > "${LIST}"

tar \
    --exclude "build-*" \
    --exclude "build-matrix" \
    --exclude "tmp*" \
    --exclude "grid.bin" \
    --exclude "*/grid.bin" \
    -czf "${TMP}" -T "${LIST}"

mv "${TMP}" "${OUT}"
trap - EXIT

echo "${OUT}"
