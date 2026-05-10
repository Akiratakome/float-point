# Week 7 Baseline Verification

Purpose: confirm Week 6 compatibility before expanding Report 1 experiment matrices.

## Run Metadata

- Record commit: pre-metadata-amend Task 1 commit `471400f`; final amended commit SHA is reported in the task handoff because embedding a commit's own SHA changes the commit.
- Run date/time: 2026-05-10 14:24:01 +01:00.
- Platform/shell: Microsoft Windows 11 Home, version 10.0.26200, 64-bit; PowerShell 7.6.1.
- CMake: 3.29.2.
- Compiler: `C:/Strawberry/c/bin/c++.exe`, MinGW-W64 GCC 13.2.0.
- Python: 3.11.9.
- Worktree status at run time: `git status --short --branch` reported branch `week7` with unrelated pre-existing modified/deleted/untracked docs, Week 7 pareto, script, and Python-test files; those files were intentionally excluded from this Task 1 commit.
- Command results: CPU double configure/build/tests exit 0; CPU float configure/build/tests exit 0; Python tests exit 0 (`73 passed, 2 skipped`); Sod capture exit 0; MD5 check exit 0 with `FD58E1A9398178E54E5B761AE9D87959`.

## Commands

- Initial status check: `git status --short --branch`
- CPU double build: `cmake -B build-final-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF`
- CPU double compile: `cmake --build build-final-double --target unit_tests hrsc`
- CPU double tests: `.\build-final-double\unit_tests.exe -r compact`
  Result: 128 test cases / 11925 assertions passed.
- CPU float build: `cmake -B build-final-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF`
- CPU float compile: `cmake --build build-final-float --target unit_tests hrsc`
- CPU float tests: `.\build-final-float\unit_tests.exe -r compact`
  Result: 128 test cases / 11925 assertions passed.
- Python tests: `python -m pytest tests/py -q`
  Result: 73 passed, 2 skipped.
- Default Sod capture:
  `.\build-final-double\hrsc.exe tests/cases/toro_1d/sod.cfg > experiments/week7/report1_smoke/sod_default_stdout.txt 2> experiments/week7/report1_smoke/sod_default_stderr.txt`
- Default Sod MD5 check:
  `$captured = (Get-FileHash experiments/week7/report1_smoke/sod_default_stdout.txt -Algorithm MD5).Hash; $expected = "FD58E1A9398178E54E5B761AE9D87959"; if ($captured -ne $expected) { throw "Sod default stdout MD5 mismatch: captured=$captured expected=$expected" }`
- Default Sod stdout MD5: see `sod_default_md5.txt` (must equal `FD58E1A9398178E54E5B761AE9D87959`).
  The hash is over the byte-for-byte Windows/PowerShell CRLF capture in `sod_default_stdout.txt`, not an LF-normalized text hash.

## Compatibility

- Default device remains `cpu`.
- Existing source cfgs were not edited.
- Timing remains on stderr.
- Normal stdout and binary formats are unchanged.
- Build flags match the Week 6 compatibility baseline (`ENABLE_OPENMP=OFF`) under which the default Sod MD5 was recorded.

## Week 6 Evidence Reused

- `experiments/week6/regression/summary.md` (CPU strict <-> GPU strict, bit-identical at 200^2/400^2).
- `experiments/week6/csc_smoke/summary.md` (CSC RTX 5090 GPU strict smoke).
