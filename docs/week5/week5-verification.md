# Week 5 Verification Recipe

**Date**: 2026-04-30 (Week 5, Day 5)
**Spec**: [week5-plan.md](week5-plan.md)
**Branch**: `week4-implementation`
**Scope**: Week 5 2D tests, GPU skeleton, timing probes, harness smoke, and plotting smoke.

This is the manual reproduction recipe for Week 5. Run commands from the
repository root. The pipeline shape remains:

```text
config -> build -> run -> measure -> aggregate -> plot
```

Large smoke grids are transient. Keep metadata, summaries, and figures; delete
smoke `grid.bin` files after aggregation and plotting. Baseline grids under
`experiments/week5/baselines/` are reference data and are not removed by the
smoke cleanup command below.

---

## Environment

| Check | Command | Expected |
|---|---|---|
| Branch | `git rev-parse --abbrev-ref HEAD` | `week4-implementation` |
| Python packages | `python -c "import numpy, matplotlib, skimage; print('ok')"` | `ok` |
| CMake | `cmake --version` | CMake available |
| CUDA toolkit | `nvcc --version` | CUDA available for `ENABLE_CUDA=ON` |
| Git state | `git status --short` | Review unrelated local changes before starting |

Notes:

- Existing build directories may be reused, but each `cmake -B ...` command
  below should still be run so options are explicit in the cache.
- MSVC classic OpenMP defaults to serial fallback in this tree. Use
  `-DHRSC_MSVC_OPENMP_LLVM=ON` only when intentionally opting into the LLVM
  OpenMP runtime on MSVC.

---

## Build

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double

cmake -B build-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-float

cmake -B build-double-prof -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DHRSC_ENABLE_PROFILING=ON
cmake --build build-double-prof

cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda
```

Expected:

- `build-double`, `build-float`, and `build-double-prof` produce `hrsc.exe`
  and `unit_tests.exe`.
- `build-double-prof` configures with `HRSC_ENABLE_PROFILING=ON`.
- `build-cuda` produces `gpu_smoke.exe` and CUDA-enabled `unit_tests.exe`.

---

## Unit tests

```bash
./build-double/unit_tests.exe -r compact
./build-double-prof/unit_tests.exe -r compact
./build-float/unit_tests.exe -r compact
./build-cuda/unit_tests.exe "[gpu]" -r compact
python -m pytest tests/py/test_plot_2d.py -v
```

Expected:

- CPU unit tests pass in double, float, and profiling builds.
- Profiling build includes the guarded `ProfilingRegistry` and `ScopedTimer`
  tests.
- CUDA `[gpu]` is **2 cases / 400 assertions**. The earlier 800-assertion
  plan double-counted the same byte-equality checks.
- `test_plot_2d.py` passes for `rho`, `p`, `vmag`, and `schlieren`.

---

## Solver baselines

### Liska-Wendroff Config 6

```bash
./build-double/hrsc.exe tests/cases/liska_wendroff_2d/config6_n200.cfg
./build-double/hrsc.exe tests/cases/liska_wendroff_2d/config6_n400.cfg
./build-float/hrsc.exe tests/cases/liska_wendroff_2d/config6_n200.cfg
./build-float/hrsc.exe tests/cases/liska_wendroff_2d/config6_n400.cfg
```

Expected: each run prints `Finished:` and a `[timing] total_s=...` line on
stderr.

Caveat: the float and double Config 6 cfg files write to the same baseline
paths:

- `experiments/week5/baselines/lw_config6_n200/grid.bin`
- `experiments/week5/baselines/lw_config6_n400/grid.bin`

If you need the kept baseline grids to be double precision after checking the
float path, rerun the two double commands before plotting or archiving.

Config 6 SSIM record:

- Existing `lw_config6_n200` baseline self-comparison sanity check:
  `L1_rho=0.000000e+00`, `ssim_rho=1.000000`,
  `ssim_fallback_used=false`.
- Week 5 does not threshold-gate Config 6 SSIM. The exact float-vs-double SSIM
  is not recoverable from current kept artefacts without regenerating grids:
  smoke `grid.bin` files are deleted transient outputs, and the baseline Config
  6 float/double runs share the same `grid.bin` paths. Record the float-vs-double
  value during any human walkthrough that preserves both precision grids.

### Shock-Bubble

```bash
./build-double/hrsc.exe tests/cases/shock_bubble/shock_bubble_n400x100.cfg
./build-double/hrsc.exe tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg
```

Expected: each run prints `Finished:` and `[timing] total_s=...`; outputs land
under:

- `experiments/week5/baselines/shock_bubble_n400x100_hllc/grid.bin`
- `experiments/week5/baselines/shock_bubble_n400x100_rusanov/grid.bin`

### Reference Figures

Generate 12 baseline PNGs:

```bash
mkdir -p experiments/week5/baselines/figures
for N in 200 400; do
  for FIELD in rho p schlieren; do
    python scripts/figures/plot_2d.py \
      experiments/week5/baselines/lw_config6_n${N}/grid.bin \
      --field ${FIELD} \
      --out experiments/week5/baselines/figures/lw_config6_n${N}_${FIELD}.png
  done
done
for SOLVER in hllc rusanov; do
  for FIELD in rho p schlieren; do
    python scripts/figures/plot_2d.py \
      experiments/week5/baselines/shock_bubble_n400x100_${SOLVER}/grid.bin \
      --field ${FIELD} \
      --out experiments/week5/baselines/figures/shock_bubble_n400x100_${SOLVER}_${FIELD}.png
  done
done
find experiments/week5/baselines/figures -maxdepth 1 -name '*.png' | wc -l
```

PowerShell count equivalent:

```powershell
(Get-ChildItem experiments/week5/baselines/figures -Filter *.png).Count
```

Expected: `12`.

Visual checks:

- Config 6 `rho`: four-contact structure, sharper at `n400` than `n200`.
- Config 6 `p`: nearly uniform pressure.
- Shock-bubble HLLC: sharper compressed bubble and transmitted shock.
- Shock-bubble Rusanov: visibly more diffuse than HLLC.

---

## Harness matrix smoke

```bash
python scripts/run_matrix.py experiments/week5/smoke/matrix.json --dry-run
python scripts/run_matrix.py experiments/week5/smoke/matrix.json

python scripts/aggregate_metrics.py \
  --output experiments/week5/smoke/summary.json \
  experiments/week5/smoke/runs/*/metadata.json

mkdir -p experiments/week5/smoke/figures
for name in lw3-d-200 lw3-f-200 lw6-d-200 lw6-f-200 sb-d-400 sb-f-400; do
  python scripts/figures/plot_2d.py \
    experiments/week5/smoke/runs/${name}/grid.bin \
    --field rho \
    --out experiments/week5/smoke/figures/${name}_rho.png
done

find experiments/week5/smoke/figures -maxdepth 1 -name '*_rho.png' | wc -l
```

PowerShell count equivalent:

```powershell
(Get-ChildItem experiments/week5/smoke/figures -Filter '*_rho.png').Count
```

Expected:

- Dry-run materializes per-run cfg and metadata without solving.
- Live run writes six `grid.bin` files plus `stdout.txt`, `stderr.txt`, and
  `metadata.json`.
- `matrix_summary.json` records the 6-run matrix execution.
- `summary.json` aggregates 6 entries.
- Six smoke `rho` PNGs are generated.
- Each live run metadata records command, git commit, generated cfg, raw output
  path, return code, and `timing.total_s`.

Cleanup smoke grids only after `matrix_summary.json`, `summary.json`, and all
six smoke figures exist:

```bash
test -f experiments/week5/smoke/matrix_summary.json
test -f experiments/week5/smoke/summary.json
test "$(find experiments/week5/smoke/figures -maxdepth 1 -name '*_rho.png' | wc -l)" -eq 6
find experiments/week5/smoke/runs -name 'grid.bin' -delete
find experiments/week5/smoke/runs -name 'grid.bin' | wc -l
test -f experiments/week5/baselines/lw_config6_n200/grid.bin
```

PowerShell cleanup equivalent:

```powershell
if (-not (Test-Path experiments/week5/smoke/matrix_summary.json)) { throw "missing smoke matrix summary" }
if (-not (Test-Path experiments/week5/smoke/summary.json)) { throw "missing smoke summary" }
if ((Get-ChildItem experiments/week5/smoke/figures -Filter '*_rho.png').Count -ne 6) { throw "missing smoke figures" }
Get-ChildItem experiments/week5/smoke/runs -Recurse -Filter grid.bin | Remove-Item
(Get-ChildItem experiments/week5/smoke/runs -Recurse -Filter grid.bin).Count
Test-Path experiments/week5/baselines/lw_config6_n200/grid.bin
```

Expected cleanup result: smoke grid count is `0`; baseline grid exists. This
confirms transient smoke grids were removed while baseline grids were left
untouched.

---

## plot_2d.py smoke

```bash
python -m pytest tests/py/test_plot_2d.py -v
```

Expected: all plot smoke tests pass.

Implementation notes to verify during review:

- `plot_2d.py` uses `io_helper.read_binary`.
- `schlieren` computes `np.gradient(rho, dx, axis=1)` and
  `np.gradient(rho, dy, axis=0)`, so gradients use physical grid spacing.
- PNG extent is based on `header.nx * header.dx` and `header.ny * header.dy`.

---

## Known differences/follow-ups

- GPU `[gpu]` currently reports 2 cases / 400 assertions. The 800 count in the
  implementation plan was a double-count.
- `HRSC_MSVC_OPENMP_LLVM` is opt-in. With classic MSVC OpenMP and default
  options, CPU builds use the serial fallback rather than forcing an OpenMP
  runtime.
- ScopedTimer probes are currently 3 phases: `bc`, `cfl`, and `sweep`. The
  probes are still recorded under `HRSC_ENABLE_PROFILING=ON`; the finer
  reconstruction/riemann/update split is deferred.
- `plot_2d.py` schlieren uses physical `dx`/`dy` gradients, not index-space
  gradients.
- Config 6 float and double baseline runs write the same `grid.bin` paths. Copy
  or rerun double last if both precision artifacts must be compared later.
- Config 6 SSIM sanity is recorded for the existing n200 baseline
  self-comparison (`ssim_rho=1.000000`, fallback not used). The float-vs-double
  SSIM remains record-only and must be captured in a walkthrough that preserves
  both precision grids.
