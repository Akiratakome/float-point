#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# rsync_from_cluster.sh — pull Week 4 A3 2D MCA production results from CSC.
#
# Usage:
#     bash scripts/rsync_from_cluster.sh <csc-login>:/path/to/floatpoint
#
# Pulls:
#     <remote>/experiments/week4/2d_vfc_cluster/  →  experiments/week4/2d_vfc_cluster/
#
# Does NOT touch build dirs, .git, or source tree. Intended to be idempotent
# (rerun after adding more samples).
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REMOTE=${1:?"usage: $0 <csc-login>:/path/to/floatpoint"}

if [[ ! -f CMakeLists.txt ]]; then
    echo "ERROR: must be run from repo root (CMakeLists.txt not found)" >&2
    exit 1
fi

REMOTE_PATH="${REMOTE%/}/experiments/week4/2d_vfc_cluster/"
LOCAL_PATH="experiments/week4/2d_vfc_cluster/"
mkdir -p "$LOCAL_PATH"

echo "[rsync] ${REMOTE_PATH}  →  ${LOCAL_PATH}"
rsync -az --info=progress2 \
    --exclude 'build*' \
    "$REMOTE_PATH" "$LOCAL_PATH"

echo "[done] local layout:"
find "$LOCAL_PATH" -maxdepth 3 -type d | head -40
