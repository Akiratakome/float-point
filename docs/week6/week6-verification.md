# Week 6 Verification Recipe

**Date**: 2026-05-05 (Week 6)
**Spec**: [week6-plan.md](week6-plan.md)
**Branch**: `week5-implementation`
**Scope**: strict CPU/CUDA builds, unit tests, WSL CPU-vs-GPU smoke/regression,
CSC replay workflow, G5 byte-identity record, and G6 timing emit.

Run commands from the repository root. The pipeline shape remains:

```text
config -> build -> run -> measure -> aggregate -> plot
```

Keep output formats stable. Do not change existing cfg defaults for verification:
CPU remains the default device, and CUDA/profiling paths are opt-in only.

---

## Phase A: Build matrix (CPU strict + CUDA strict)

```bash
# Local WSL:
cmake -B build-cpu-strict-double  -G Ninja -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake -B build-cpu-strict-float   -G Ninja -DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake -B build-cuda-double-strict -G Ninja -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DENABLE_CUDA=ON
cmake -B build-cuda-float-strict  -G Ninja -DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DENABLE_CUDA=ON

for D in build-cpu-strict-double build-cpu-strict-float \
         build-cuda-double-strict build-cuda-float-strict; do
    cmake --build "$D" -j
done

# CSC:
ssh csc-athena
cd ~/floatpoint && git pull
bash scripts/cluster/build_gpu_csc.sh both
```

Expected end-state:

- 4 local build dirs green: `build-cpu-strict-double`,
  `build-cpu-strict-float`, `build-cuda-double-strict`,
  `build-cuda-float-strict`.
- 2 CSC build dirs green from `build_gpu_csc.sh both`:
  `build-cuda-double-strict`, `build-cuda-float-strict`.
- The CUDA path is opt-in through `-DENABLE_CUDA=ON`; default CPU builds remain
  unchanged.

Observed local state available on 2026-05-05: the four local strict build
directories exist in this worktree.

---

## Phase B: Unit tests

```bash
./build-cpu-strict-double/unit_tests  -r compact
./build-cpu-strict-float/unit_tests   -r compact
./build-cuda-double-strict/unit_tests "[gpu]" -r compact
./build-cuda-float-strict/unit_tests  "[gpu]" -r compact
```

Expected:

- CPU strict double and float tests are green.
- CUDA strict double and float `[gpu]` tests are green, including the 39 new
  Week 6 GPU cases.
- The CPU-only builds do not require CUDA to run their non-`[gpu]` tests.

Observed evidence where available:

- Local scratch logs in this worktree record `Passed all 159 test cases with
  71516 assertions.` for a full test run.
- A prior full-test scratch log records `Passed all 148 test cases with 71470
  assertions.` before later Week 6 cases landed.

Do not commit scratch logs; rerun the commands above during final handoff and
record fresh output in the Week 6 summary if needed.

---

## Phase C: Local WSL smoke/regression matrix

```bash
python scripts/run_matrix.py experiments/week6/smoke/matrix.json

python scripts/run_matrix.py experiments/week6/regression/matrix.json
python scripts/regression/float_regression_report.py \
    --mode device \
    --cpu experiments/week6/regression/runs/sod-cpu-strict-d/sod.bin \
          experiments/week6/regression/runs/sod-cpu-strict-f/sod.bin \
          experiments/week6/regression/runs/lw3-cpu-strict-d/lw3.bin \
          experiments/week6/regression/runs/lw3-cpu-strict-f/lw3.bin \
    --gpu experiments/week6/regression/runs/sod-gpu-strict-d/sod.bin \
          experiments/week6/regression/runs/sod-gpu-strict-f/sod.bin \
          experiments/week6/regression/runs/lw3-gpu-strict-d/lw3.bin \
          experiments/week6/regression/runs/lw3-gpu-strict-f/lw3.bin \
    --output experiments/week6/regression/summary

cat experiments/week6/regression/summary.md
```

Expected:

- Smoke matrix: 8 runs complete with `returncode: 0`.
- Regression report: 4 CPU-vs-GPU same-precision pairs, all
  `gate_passed=True`.

Observed evidence in `experiments/week6/regression/summary.md`:

- `sod` double: `ulp_max=0.000000e+00`, `gate_passed=True`.
- `sod` float: `ulp_max=0.000000e+00`, `gate_passed=True`.
- `lw3` double: `ulp_max=0.000000e+00`, `gate_passed=True`.
- `lw3` float: `ulp_max=0.000000e+00`, `gate_passed=True`.

---

## Phase D: CSC smoke matrix

CSC environment reference: [csc_gpu_environment.md](csc_gpu_environment.md).
The observed partition is `csc-mphil-gpu`; do not use the stale plan default
`ampere`.

```bash
# On laptop: push branch first if CSC has not seen these commits.
git push origin week5-implementation

# On CSC:
ssh csc-athena
cd ~/floatpoint
git fetch origin
git checkout week5-implementation
git pull --ff-only
bash scripts/cluster/build_gpu_csc.sh both
mkdir -p experiments/week6/csc_smoke/slurm_logs
sbatch scripts/cluster/run_gpu_smoke.slurm
squeue -u "$USER"

# After completion, on laptop:
rsync -avz csc-athena:~/floatpoint/experiments/week6/csc_smoke/ \
           experiments/week6/csc_smoke/

python scripts/regression/float_regression_report.py \
    --mode device \
    --cpu experiments/week6/regression/runs/sod-cpu-strict-d/sod.bin \
          experiments/week6/regression/runs/sod-cpu-strict-f/sod.bin \
          experiments/week6/regression/runs/lw3-cpu-strict-d/lw3.bin \
          experiments/week6/regression/runs/lw3-cpu-strict-f/lw3.bin \
    --gpu experiments/week6/csc_smoke/runs/sod-gpu-csc-d/sod.bin \
          experiments/week6/csc_smoke/runs/sod-gpu-csc-f/sod.bin \
          experiments/week6/csc_smoke/runs/lw3-gpu-csc-d/lw3.bin \
          experiments/week6/csc_smoke/runs/lw3-gpu-csc-f/lw3.bin \
    --output experiments/week6/csc_smoke/summary

cat experiments/week6/csc_smoke/summary.md
```

Expected:

- CSC builds produce 2 CUDA strict build dirs.
- SLURM smoke produces 4 CSC GPU runs: `sod` double/float and `lw3`
  double/float.
- CSC-vs-WSL `ulp_max` is recorded for all 4 pairs. A non-zero CSC-vs-WSL
  value is a research data point, not an automatic failure.

Known caveat: `csc_run_pending` until the branch is pushed and replayed on CSC,
or until the queued SLURM job completes. If still pending at closeout, schedule
Week 7 D1 replay with the exact Phase D workflow above.

---

## Reference md5s (G5 byte-identity)

Recorded local G5 byte-identity evidence:

```text
DC775038D2AF265936AE473233E6A01C  build-double/hrsc.exe
FD58E1A9398178E54E5B761AE9D87959  experiments/week6/baseline/sod_pre_t1_stdout.txt
FD58E1A9398178E54E5B761AE9D87959  experiments/week6/baseline/sod_day1_done_stdout.txt
FD58E1A9398178E54E5B761AE9D87959  experiments/week6/baseline/sod_post_t1_stdout.txt
FD58E1A9398178E54E5B761AE9D87959  experiments/week6/baseline/sod_post_t9_stdout.txt
```

The stdout md5 stayed identical before T1, after T1, at D1 completion, and
after T9. This is the stable byte-identity gate for the default CPU path.
`stderr` includes timing output and is expected to vary; do not use stderr
timing md5 as a byte-identity gate.

Record or refresh values with PowerShell:

```powershell
Get-FileHash -Algorithm MD5 build-double/hrsc.exe
Get-FileHash -Algorithm MD5 `
    experiments/week6/baseline/sod_pre_t1_stdout.txt, `
    experiments/week6/baseline/sod_day1_done_stdout.txt, `
    experiments/week6/baseline/sod_post_t1_stdout.txt, `
    experiments/week6/baseline/sod_post_t9_stdout.txt
```

Linux/WSL equivalent:

```bash
md5sum build-double/hrsc.exe \
       experiments/week6/baseline/sod_pre_t1_stdout.txt \
       experiments/week6/baseline/sod_day1_done_stdout.txt \
       experiments/week6/baseline/sod_post_t1_stdout.txt \
       experiments/week6/baseline/sod_post_t9_stdout.txt
```

Expected: Week 6 default CPU output matches the recorded Week 5 baseline for
the same binary/output artefact. The compatibility rule is strict: default CPU
behavior is unchanged; CUDA (`device=gpu`) and profiling
(`-DHRSC_ENABLE_PROFILING=ON` or runtime profiling knobs) are opt-in only and
default OFF.

---

## Phase E: G6 timing emit

```bash
cmake -B build-prof -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DHRSC_ENABLE_PROFILING=ON
cmake --build build-prof

HRSC_ENABLE_PROFILING=ON ./build-prof/hrsc tests/cases/toro_1d/sod.cfg 2>&1 | grep timing
```

Expected: timing output includes 5 phase lines or fields for:

- `bc`
- `cfl`
- `flux`
- `update`
- `total`

The normal non-profiling build must continue to emit stable existing output
formats; profiling details are only for profiling-enabled runs.

---

## Cleanup

Large Week 6 smoke/regression grids are transient once summaries are written.
Keep `metadata.json`, `stdout.txt`, `stderr.txt`, `matrix_summary.json`, and
`summary.{md,json,csv}`; delete binary grids under Week 6 run directories after
the summaries have been checked.

```bash
test -f experiments/week6/smoke/matrix_summary.json
test -f experiments/week6/regression/summary.md

find experiments/week6 -path '*/runs/*/*.bin' -print
find experiments/week6 -path '*/runs/*/*.bin' -delete
find experiments/week6 -path '*/runs/*/*.bin' | wc -l
```

PowerShell equivalent:

```powershell
if (-not (Test-Path experiments/week6/smoke/matrix_summary.json)) { throw "missing smoke matrix summary" }
if (-not (Test-Path experiments/week6/regression/summary.md)) { throw "missing regression summary" }

Get-ChildItem experiments/week6 -Recurse -Filter *.bin |
    Where-Object { $_.FullName -match '\\runs\\' } |
    Remove-Item

(Get-ChildItem experiments/week6 -Recurse -Filter *.bin |
    Where-Object { $_.FullName -match '\\runs\\' }).Count
```

Expected cleanup result: `0` Week 6 run-directory `.bin` files remain. Do not
delete summaries, run metadata, configs, logs, or any explicit reference
artefact needed to reproduce a metric.
