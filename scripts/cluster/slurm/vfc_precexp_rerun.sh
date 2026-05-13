#!/usr/bin/env bash
#SBATCH --job-name=hrsc-vfc-precexp
#SBATCH --output=experiments/week7/vfc_precexp/logs/slurm-%j.out
#SBATCH --error=experiments/week7/vfc_precexp/logs/slurm-%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
OUT="${OUT:-${ROOT}/experiments/week7/vfc_precexp}"
LOG="${OUT}/logs"
SCRIPT_DIR="${OUT}/scripts"
BUILD_DIR="${ROOT}/build-vfc-precexp"

mkdir -p "${LOG}" "${SCRIPT_DIR}" "${OUT}/reference"

{
  date -u
  hostname
  command -v verificarlo-c++ || true
  command -v vfc_precexp || true
  verificarlo-c++ --version || true
  vfc_precexp --help | head -80 || true
  cmake --version || true
  git rev-parse HEAD || true
} > "${OUT}/logs/environment.txt" 2>&1

cat > "${OUT}/scripts/exrun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="$1"
ROOT="${ROOT:-$(pwd)}"
OUT="${OUT:-${ROOT}/experiments/week7/vfc_precexp}"

mkdir -p "${OUTPUT_DIR}"
python "${ROOT}/scripts/verificarlo/precexp_prepare_cfg.py" \
  --source "${OUT}/config.cfg" \
  --output "${OUTPUT_DIR}/config.cfg" \
  --grid "${OUTPUT_DIR}/grid.bin"
"${ROOT}/build-vfc-precexp/hrsc" "${OUTPUT_DIR}/config.cfg" > "${OUTPUT_DIR}/stdout.txt" 2> "${OUTPUT_DIR}/stderr.txt"
EOF
chmod +x "${OUT}/scripts/exrun"

cat > "${OUT}/scripts/excmp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

REF_DIR="$1"
CUR_DIR="$2"

python "${ROOT}/scripts/verificarlo/precexp_compare.py" \
  --reference "${REF_DIR}/grid.bin" \
  --candidate "${CUR_DIR}/grid.bin" \
  --density-l1-rel-max 1.0e-2 \
  --pressure-linf-rel-max 5.0e-2
EOF
chmod +x "${OUT}/scripts/excmp"

cmake -S "${ROOT}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DFLOAT_PRECISION=double \
  -DENABLE_OPENMP=OFF \
  -DCMAKE_CXX_COMPILER=verificarlo-c++ \
  > "${LOG}/configure_stdout.txt" \
  2> "${LOG}/configure_stderr.txt"

cmake --build "${BUILD_DIR}" -j1 \
  > "${LOG}/build_stdout.txt" \
  2> "${LOG}/build_stderr.txt"

cp "${ROOT}/tests/cases/toro_1d/sod.cfg" "${OUT}/config.cfg"
python "${ROOT}/scripts/verificarlo/precexp_prepare_cfg.py" \
  --source "${OUT}/config.cfg" \
  --output "${OUT}/reference/config.cfg" \
  --grid "${OUT}/reference/grid.bin"

"${BUILD_DIR}/hrsc" "${OUT}/reference/config.cfg" > "${OUT}/reference/stdout.txt" 2> "${OUT}/reference/stderr.txt"

ROOT="${ROOT}" OUT="${OUT}" vfc_precexp \
  --exrun "${SCRIPT_DIR}/exrun" \
  --excmp "${SCRIPT_DIR}/excmp" \
  "${OUT}/reference" \
  > "${LOG}/vfc_precexp_stdout.txt" \
  2> "${LOG}/vfc_precexp_stderr.txt"
