# Week 7 Build Matrix Record

Build entry point: `scripts/build_all.sh`

CPU variant naming follows `scripts/build_matrix.py`:

`cpu-{precision}-{opt_level}-{ieee|fastmath}-{leq|strict}`

The trailing `leq|strict` controls `RIEMANN_STRICT_INEQUALITY` (HLLC `<=` vs `<`), not IEEE strictness.

CUDA strict builds are produced on CSC by `scripts/cluster/build_gpu_csc.sh` and are not rebuilt locally.

Local invocation note: `bash scripts/build_all.sh` failed before configuration because the working-tree script was checked out with CRLF endings and Linux bash read `pipefail\r`. The tracked script was not modified; the matrix was built by executing the same script content through `tr -d '\r' < scripts/build_all.sh | bash`.

Success marker: the normalized build command exited 0 on 2026-05-10T14:41:42+01:00 from PowerShell spawning GNU bash 5.2.21 under WSL2 (`Linux Beren 6.6.87.2-microsoft-standard-WSL2`). All 24 `build-matrix/` variants configured and built successfully.

## Produced Build Directories

Output from `Get-ChildItem build-matrix -Directory | Select-Object -ExpandProperty Name`:

```text
cpu-double-O2-fastmath-leq
cpu-double-O2-fastmath-strict
cpu-double-O2-ieee-leq
cpu-double-O2-ieee-strict
cpu-double-O3-fastmath-leq
cpu-double-O3-fastmath-strict
cpu-double-O3-ieee-leq
cpu-double-O3-ieee-strict
cpu-double-Ofast-fastmath-leq
cpu-double-Ofast-fastmath-strict
cpu-double-Ofast-ieee-leq
cpu-double-Ofast-ieee-strict
cpu-float-O2-fastmath-leq
cpu-float-O2-fastmath-strict
cpu-float-O2-ieee-leq
cpu-float-O2-ieee-strict
cpu-float-O3-fastmath-leq
cpu-float-O3-fastmath-strict
cpu-float-O3-ieee-leq
cpu-float-O3-ieee-strict
cpu-float-Ofast-fastmath-leq
cpu-float-Ofast-fastmath-strict
cpu-float-Ofast-ieee-leq
cpu-float-Ofast-ieee-strict
```

## Skipped Variants and Reason

No CPU matrix variants under `build-matrix/` were skipped.

The host compiler accepted the STRICT_IEEE GNU/Clang CPU probe, so the script also produced the two legacy STRICT_IEEE CPU build directories outside `build-matrix/`:

```text
build-cpu-strict-double
build-cpu-strict-float
```

CUDA STRICT_IEEE local builds were skipped because CUDA is optional on this host:

```text
WARNING: nvcc not found; skipping CUDA STRICT_IEEE builds.
```
