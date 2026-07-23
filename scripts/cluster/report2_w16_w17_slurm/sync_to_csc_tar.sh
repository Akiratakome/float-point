#!/usr/bin/env bash
set -euo pipefail

: "${CSC_TARGET:?set CSC_TARGET, e.g. csc-athena:~/floatpoint}"

if [[ "${CSC_TARGET}" != *:* ]]; then
    echo "ERROR: CSC_TARGET must look like host:/path or host:~/path" >&2
    exit 2
fi

REMOTE_HOST="${CSC_TARGET%%:*}"
REMOTE_PATH="${CSC_TARGET#*:}"

case "${REMOTE_PATH}" in
    *" "*)
        echo "ERROR: CSC_TARGET path must not contain spaces" >&2
        exit 2
        ;;
esac

tar \
    --exclude "build-*" \
    --exclude "build-matrix" \
    --exclude "tmp*" \
    --exclude "grid.bin" \
    --exclude "*/grid.bin" \
    -czf - . | ssh "${REMOTE_HOST}" "mkdir -p ${REMOTE_PATH} && tar -xzf - -C ${REMOTE_PATH}"
