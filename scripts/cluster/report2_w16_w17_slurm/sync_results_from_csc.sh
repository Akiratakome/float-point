#!/usr/bin/env bash
set -euo pipefail

: "${CSC_TARGET:?set CSC_TARGET, e.g. user@csc:/scratch/project/floatpoint}"

rsync -az \
    --include "*/" \
    --include "summary.*" \
    --include "environment.json" \
    --include "*.png" \
    --include "slurm_logs/***" \
    --include "csc_slurm_logs/***" \
    --exclude "grid.bin" \
    --exclude "*" \
    "${CSC_TARGET%/}/experiments/week16/kelvin_helmholtz_precision/" \
    "experiments/week16/kelvin_helmholtz_precision/"

rsync -az \
    --include "*/" \
    --include "summary.*" \
    --include "manifest.json" \
    --include "README.md" \
    --include "*.png" \
    --include "csc_slurm_logs/***" \
    --exclude "grid.bin" \
    --exclude "*" \
    "${CSC_TARGET%/}/experiments/week17/" \
    "experiments/week17/"
