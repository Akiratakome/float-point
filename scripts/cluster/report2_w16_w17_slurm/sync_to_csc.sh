#!/usr/bin/env bash
set -euo pipefail

: "${CSC_TARGET:?set CSC_TARGET, e.g. user@csc:/scratch/project/floatpoint}"

rsync -az \
    --exclude "build-*/" \
    --exclude "build-matrix/" \
    --exclude "tmp*/" \
    --exclude "**/grid.bin" \
    --exclude "**/runs/*/grid.bin" \
    ./ "${CSC_TARGET%/}/"
