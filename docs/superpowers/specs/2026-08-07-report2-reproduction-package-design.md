# Report 2 Reproduction Package — Design

**Date**: 2026-08-07
**Status**: approved (design), pending implementation plan
**Goal**: ship a minimal, self-contained code set that lets an examiner rebuild
and re-derive every Report 2 experimental result from zero on their own machine,
and tell them mechanically whether the reproduction succeeded.

---

## 1. Problem

The submitted tree is an experiment harness of ~100 Python scripts, 59 C++/CUDA
sources and a 295 MB `experiments/` tree. An examiner handed this repository
cannot tell which files matter, which results are re-derivable off the author's
workstation, or what "reproduced" means for a result whose claim is bitwise
agreement under MSVC 19.51.

Appendix 3 of the dissertation already records the authoritative mapping from
claim family to summary artefact to generator script
(`dissertation/phd-thesis-template-2.4/Appendix3/evidence_map_table.tex`). All
thirteen listed `summary.json` files exist in the tree. That table is the
backbone of this package; the package makes it executable.

Report 1 evidence was submitted separately and is **out of scope**. The Euler
solver is nevertheless retained — see §3.2.

---

## 2. Scope

### 2.1 Evidence families in scope

Thirteen families from the Appendix 3 evidence map, plus the Verificarlo MCA
packets that Chapter 5's MCA table and Appendix 2's MCA status table rest on.

| # | Family | Driver | Requirement |
|---|---|---|---|
| 1 | Brio–Wu / GLM | `scripts/regression/mhd_brio_wu_1d.py` | CPU |
| 2 | CP-Alfvén order + fp32 floor | `scripts/regression/mhd_cp_alfven_saturation.py` | CPU |
| 3 | KH growth-rate ladder | `scripts/regression/mhd_lecoanet_kh_growth_ladder.py` | CPU |
| 4 | Euler OpenMP thread axis | `scripts/regression/euler_openmp_thread_axis.py` | CPU + OpenMP |
| 5 | 2D resolution ladder | `scripts/regression/mhd_week18_resolution_ladder.py` | CPU |
| 6 | CPU/GPU state agreement | `scripts/regression/mhd_gpu_hardware_axis.py` | CUDA (optional) |
| 7 | Repeated hardware timing | `scripts/regression/mhd_week18_supplemental.py` | CPU (+CUDA for GPU rows) |
| 8 | KH solver timing | `scripts/regression/mhd_week18_kh_timing.py` | CPU |
| 9 | Temporal divergence fits | `scripts/regression/mhd_temporal_divergence.py` | CPU |
| 10 | Temporal saturation | `mhd_temporal_divergence.py` + `scripts/figures/report2_temporal_saturation.py` | CPU |
| 11 | Build semantics axis | `scripts/regression/mhd_brio_build_semantics.py` | CPU (self-builds 8 variants) |
| 12 | Device FMA contraction | `scripts/regression/mhd_gpu_fma_axis.py` | CUDA (optional) |
| 13 | CPU instruction-set axis | `scripts/regression/mhd_brio_cpu_arch.py` | CPU |
| 14 | MCA precision packets | `scripts/regression/mhd_precision_pilot.py`, `scripts/regression/report2_precision_mca_gate.py` | Docker + Verificarlo (optional) |

Report-facing figures: the seventeen `Figs/report2/ch4_*|ch5_*` assets, produced
by `scripts/figures/report2_publication_figures.py`,
`report2_kh_morphology.py`, `report2_saturation_grid_solver.py`,
`report2_temporal_saturation.py`, plus the six manually copied experiment plots
recorded with SHA-256 in `report2/phd-thesis-template-2.4/Figs/README.md`.

### 2.2 Out of scope

Report 1 evidence families (Toro, Liska–Wendroff, shock-bubble, Pareto
trade-off, Report 1 Verificarlo sweeps); CSC Slurm cluster routing
(`scripts/cluster/`); superseded and invalid experiment packets; every
`grid.bin`; the LaTeX manuscript build.

### 2.3 Target environments

Cross-platform. CPU path is required and must build under both MSVC and
GCC/Clang. CUDA and Verificarlo are optional modules that degrade to `SKIP`.

---

## 3. Architecture

### 3.1 Two halves

**Maintainer side** — `repro/`, lives in this repository, is not shipped:

```
repro/
  manifest.py       include globs, the 14 family definitions, reference artefact list
  export.py         resolves the Python import closure, stages dist/, writes the zip
  runner/           source of the code that IS shipped
    reproduce.py    single entry point, --tier smoke|core|full
    build.py        configures and builds the required variants
    capabilities.py environment probe (compiler, Ninja, CUDA, Docker, RAM)
    compare.py      reference vs local -> report
  tolerances.toml   claim table: type, paper value, tolerance, tier availability
  templates/
    README.md.in            examiner-facing, English
    QUICKSTART.zh.md.in     one-page Chinese quickstart
    REPRODUCE.md.in         tier and claim documentation
tests/py/test_repro_export.py
```

**Shipped package** — `dist/hrsc-report2-repro/`, ~15–25 MB:

```
hrsc-report2-repro/
  README.md  QUICKSTART.zh.md  REPRODUCE.md  requirements.txt
  reproduce.py
  CMakeLists.txt  cmake/  src/  external/catch2/  tests/  scripts/
  reference/
    summaries/<family>/summary.json
                                one per family for 1-13; family 14 ships the
                                five week15 deterministic + MCA packets named in
                                report2_precision_mca_gate.py's SPECS tuple
                                plus the week18 gate summary
    figures/                    the 17 report-facing assets
    figure_manifest.json        with source and asset SHA-256
    platform.json               the Appendix 3 execution record
    tolerances.toml
  results/                      comparison report and copied figures only
```

### 3.2 Why the Euler solver stays

Family 4 (Euler OpenMP thread axis) is a Report 2 evidence family and needs the
`hrsc` binary and `tests/cases/liska_wendroff_2d`. `unit_tests` links
`hrsc_euler` unconditionally. Dropping `src/euler/` would break both. The
README states this explicitly so the examiner does not read the Euler code as
re-submitted Report 1 evidence.

### 3.3 Layout preservation — no path rewriting

Every driver script computes `ROOT = Path(__file__).resolve().parents[2]` and
writes to hardcoded `experiments/weekN/...` paths. The package therefore keeps
the identical repo-relative layout: `scripts/regression/x.py` still resolves
`parents[2]` to the package root, and generated output still lands in
`experiments/weekN/...` inside the package.

**No driver script is edited.** This is the central constraint. Rewriting output
paths would fork the shipped scripts from the audited ones and violate the
"keep existing output formats stable" rule in `AGENTS.md`. Reference artefacts
live in a separate `reference/` tree precisely so they cannot collide with
freshly generated output. `results/` holds only `compare.py` products.

### 3.4 Import closure, not a hand-written file list

`export.py` seeds from the 18 driver and figure scripts, walks the AST of each
module's `import` statements, and follows every edge that resolves inside
`scripts/` — including the `sys.path.insert` sibling-directory imports used by
`mhd_precision_pilot.py` (`scripts/verificarlo`) and
`report2_publication_figures.py` (`scripts.regression.*`). Hand-listing is
rejected: one missing `io_helper` breaks the whole package, and `io_helper`,
`_mhd_harness`, `_style` and `mhd_fields` are imported 44, 25, 9 and 12 times
respectively across the tree.

`tests/py/*` is included for exactly those tests whose imports resolve inside
the closure.

Config discovery is the same principle: `export.py` greps the included drivers
for `tests/cases/...` paths and includes the referenced `.cfg` files, and
`test_repro_export.py` fails if any referenced config is absent from `dist/`.

---

## 4. Build matrix

`build.py` produces, with `-DCMAKE_BUILD_TYPE=Release`:

| Build dir | CMake args | Needed by |
|---|---|---|
| `build-double` | `-DFLOAT_PRECISION=double -DENABLE_OPENMP=OFF` | 1, 2, 3, 6, 7, 8, 12 |
| `build-float` | `-DFLOAT_PRECISION=float -DENABLE_OPENMP=OFF` | 2, 6, 7, 8, 12 |
| `build-double-omp` | `-DFLOAT_PRECISION=double -DENABLE_OPENMP=ON` | 4 |
| `build-float-omp` | `-DFLOAT_PRECISION=float -DENABLE_OPENMP=ON` | 4 |
| `build-matrix/cpu-double-O2-ieee-leq` | `-DFLOAT_PRECISION=double -DOPT_LEVEL=O2 -DFAST_MATH=OFF -DRIEMANN_STRICT_INEQUALITY=OFF -DENABLE_OPENMP=OFF` | 5, 9, 10 |
| `build-matrix/cpu-float-O2-ieee-leq` | as above, `float` | 5, 9, 10 |
| `build-sse2`, `build-sse2-float` | `-DCPU_ARCH=SSE2 -DOPT_LEVEL=O2 -DENABLE_OPENMP=OFF` | 13 |
| `build-avx2`, `build-avx2-float` | `-DCPU_ARCH=AVX2 -DOPT_LEVEL=O2 -DENABLE_OPENMP=OFF` | 13 |
| 8 build-semantics variants | driven by `mhd_brio_build_semantics.py` itself | 11 |
| `build-cuda`, `build-cuda-float` | `+ -DENABLE_CUDA=ON` | 6, 7, 12 (optional) |
| `build-cuda-fmad`, `build-cuda-fmad-float` | `+ -DENABLE_CUDA=ON -DGPU_FMA_CONTRACT=ON` | 12 (optional) |

`cmake/CompilerFlags.cmake` already maps all three flag axes to both
toolchains (`/arch:AVX2` ↔ `-mavx2`, `/Ox /fp:fast` ↔ `-Ofast`,
`/fp:fast` ↔ `-ffast-math`), so no CMake change is required.

### 4.1 The OpenMP portability trap

`ENABLE_OPENMP` defaults to `ON`. On MSVC, CMake emits a warning and silently
falls back to serial unless `HRSC_MSVC_OPENMP_LLVM=ON` — which is why the
author's MHD builds are serial, as Appendix 3 records. On Linux with GCC the
same default **actually enables OpenMP**, changing sweep reduction order and
therefore the numbers.

`build.py` must pass `-DENABLE_OPENMP=OFF` explicitly for every build except
the two `-omp` directories. `REPRODUCE.md` documents this as a known
platform difference. This is the single highest-risk portability defect found
during design.

---

## 5. Verification

### 5.1 Four claim types

`reference/tolerances.toml` assigns every claim exactly one type. `compare.py`
emits one row per claim: family, claim id, type, paper value, local value,
tolerance, verdict.

| Type | Comparison | Verdict values |
|---|---|---|
| `tolerance` | relative difference against the paper value | `PASS` / `FAIL` / `REDUCED` |
| `qualitative` | boolean or ordering assertion | `PASS` / `FAIL` |
| `platform_bound` | compared **only within the examiner's own toolchain**; the local finding is reported next to the paper's, never scored against it | `PLATFORM-BOUND` |
| `informational` | wall-clock; recorded, never scored | `INFO` |

`qualitative` carries the dissertation's main arguments and is the class that
survives a toolchain change. `platform_bound` exists because bitwise agreement
is a property of a specific compiled artefact; classifying those claims as
`tolerance` would manufacture spurious failures.

### 5.2 Claim table

Paper values below were read from the retained summaries and are the seed
content of `tolerances.toml`. Tolerances are set from the observed magnitude of
each quantity, with the rationale recorded inline in the TOML.

| Family | Claim | Type | Paper value | Tolerance |
|---|---|---|---|---|
| 1 | density `L1` vs aligned N=8000 reference, N=200/400/800 | `tolerance` | 0.014806 / 0.009463 / 0.005642 | 5 % rel |
| 1 | `L1` and `L2` strictly decreasing in N | `qualitative` | true | — |
| 2 | fp64/fp32 `L1` excess ratio within saturation tolerance | `tolerance` | `saturation_tolerance_rel` = 0.05 | as recorded |
| 2 | observed order, grids 32–512, fp64 / fp32 | `tolerance` | 1.8183 / 1.8174 (`r²` 0.9997) | 10 % rel |
| 2 | observed order, full range 32–8192, fp64 / fp32 | `tolerance` | 1.8990 / 1.6580 | 10 % rel |
| 2 | fp32 floor: full-range order degrades below fp64 while the 32–512 fit does not | `qualitative` | true | — |
| 3 | growth rate at nx = 64/128/256/512 | `tolerance` | 1.0788 / 2.1932 / 2.7313 / 2.8882 | 10 % rel |
| 3 | monotone approach to published 3.227 | `qualitative` | true | — |
| 3 | fit `R²` ≥ 0.96 at every resolution | `qualitative` | true | — |
| 4 | all thread counts bitwise identical (`ulp_max` = 0) | `qualitative` | true | — |
| 4 | serial binary matches 1-thread OpenMP binary | `qualitative` | true | — |
| 4 | per-thread median wall time | `informational` | 1.307 s at 1 thread, fp64 LW3 200² | — |
| 5 | gate `pass`, 8/8 complete groups, 12/12 precision-pair cells | `qualitative` | true | — |
| 5 | `positive_order_groups` = 8, `asymptotic_convergence` = false | `qualitative` | 8, false | — |
| 5 | `rho_l1_fp32_vs_fp64`, `rho_linf_fp32_vs_fp64` | `tolerance` | 5.554e-05, 0.05031 | 20 % rel |
| 6 | G-GPU gate: same-precision CPU vs GPU `ulp_max` = 0 | `platform_bound` | 0 | — |
| 6 | CPU and GPU step counts equal | `qualitative` | true | — |
| 6 | CPU/GPU wall times | `informational` | Brio–Wu fp64: 0.183 s CPU, 2.782 s GPU | — |
| 7 | `ulp_max` = 0 and `linf_abs` = 0 across 5 repeats | `platform_bound` | 0, 0 | — |
| 7 | median and IQR per case/precision | `informational` | Brio–Wu fp64 CPU 0.1621 s, IQR 0.00386 s | — |
| 8 | `Linf` ρ fp32 vs fp64, HLL / HLLD | `tolerance` | 1.786e-06 / 3.230e-06 | 25 % rel |
| 8 | repeat outputs bit-exact | `platform_bound` | true | — |
| 8 | fp32 speed-up, HLLD/HLL cost ratio | `informational` | 1.181 / 1.154, 1.147 / 1.173 | — |
| 9 | all gates pass, 80 provenance-complete runs | `qualitative` | true | — |
| 9 | Orszag–Tang positive λ over window [0.1, 0.5] | `qualitative` | true | — |
| 9 | **negative result**: `planned_ot_exceeds_brio_l1` = false | `qualitative` | false | — |
| 9 | `orszag_tang_linf_positive` = false | `qualitative` | false | — |
| 10 | fixed fit windows honoured: Brio–Wu [0.01, 0.1], OT [0.1, 0.5] | `qualitative` | true | — |
| 11 | `/Ox` vs `/O2` bit-identical | `platform_bound` | ρ `L1` = 0 exactly | — |
| 11 | `<` vs `<=` Riemann branch bit-identical | `platform_bound` | ρ `L1` = 0 exactly | — |
| 11 | fast-math perturbs at roundoff scale | `platform_bound` | ρ `L1` = 2.371e-16 (HLL fp64) | — |
| 11 | step counts equal within solver/precision | `qualitative` | true | — |
| 12 | `--fmad=false` → CPU/GPU bit-identical | `platform_bound` | true | — |
| 12 | `--fmad=true` → not bit-identical, roundoff-scale `Linf` | `platform_bound` | 4.219e-15 (HLL fp64) | — |
| 13 | AVX2 vs SSE2 bit-identical despite differing binaries | `platform_bound` | ρ `Linf` = 0, `binaries_differ` = true | — |
| 14 | `gate.audit_pass` | `qualitative` | true | — |
| 14 | **negative result**: `gate.full_matrix_promotion_pass` = false | `qualitative` | false | — |
| 14 | `report_grade_rows` / `expected_rows` | `qualitative` | 2 / 4 | — |
| 14 | Brio–Wu HLL and HLLD rows reach `status` = "report-grade" | `qualitative` | true | — |
| 14 | Orszag–Tang HLL and HLLD rows stay provisional (scope mismatch) | `qualitative` | true | — |

### 5.3 Two specific gating decisions

**Family 12 must not gate on `ulp_max`.** The retained summary records
`ulp_max: 8756652839418887962` for the `--fmad=true` fp64 row — a bit-pattern
subtraction artefact next to a genuine `linf_abs` of 4.219e-15. The stored
value is left untouched (`AGENTS.md`: do not change existing output formats);
`compare.py` gates family 12 on `bitwise_identical` and `linf_abs` instead, and
`REPRODUCE.md` notes why.

**Family 14 reproduces a partial gate, not a clean pass.** The retained gate
records `audit_pass = true` but `full_matrix_promotion_pass = false`, with 2 of
4 rows at report grade: the Orszag–Tang HLL and HLLD packets stay provisional
because the deterministic 256²/t=0.5 scope and the MCA 64²/t=0.05 scope do not
match. The package must reproduce that partial outcome, not paper over it. A
run that turned all four rows green would be a **failure** of fidelity, and
`compare.py` asserts the false value explicitly.

**Families 11 and 13 may legitimately differ on GCC/Clang.** The recorded
bit-identity of `/Ox` vs `/O2` and `/arch:AVX2` vs `/arch:SSE2` is an MSVC
result. `-O3` vs `-O2` and `-mavx2` vs `-msse2` change what GCC's auto-vectoriser
emits and can reorder reductions. Both are `platform_bound`: the package reports
the examiner's own finding and states that a difference there is an expected
toolchain result, not a failed reproduction.

---

## 6. Tiers

`reproduce.py --tier` selects one of three levels. Tier reduction only ever
shrinks resolution or repeat count; it never changes solver, CFL, or case.

| Tier | Budget | Content |
|---|---|---|
| `smoke` | ~5 min | `unit_tests`, `pytest tests/py`, Brio–Wu at N=200, divB-clean at reduced resolution. Proves the toolchain works. Runs no claim comparison beyond family 1. |
| `core` | ~1.5 h | All 14 families. KH ladder and resolution ladder truncated to 256²; timing repeats 5 → 2; family 2 grids truncated to 512. |
| `full` | ~1 day | Paper parameters: 512² grids, 5 repeats, family 2 to 8192. Pre-flight RAM check before the 512² runs. |

Claims whose family was tier-reduced are marked `REDUCED`, their tolerance
widened per `tolerances.toml`, and listed in a dedicated
"only fully attested at `--tier full`" section of `REPRODUCE.md`. Concretely:
family 3's nx=512 growth rate, family 5's 512² groups, and families 7 and 8's
IQR statistics are unavailable below `full`.

Recorded runtimes that inform these budgets: family 1 ≈ 10 s, family 2 ≈ 140 s,
family 9 ≈ 304 s over 160 runs, family 7 ≈ 286 s over 40 runs, family 8 ≈ 688 s
over 20 runs.

---

## 7. Degradation

`capabilities.py` probes before any build and prints a capability table:
C++ compiler and id, CMake, Ninja, Python 3 with numpy/matplotlib/pytest,
`nvcc`, `docker`, available RAM. `reproduce.py` then:

- no CUDA → families 6 and 12 `SKIP`; family 7's GPU rows `SKIP`, CPU rows run
- no Docker or Verificarlo image → family 14 falls back to **audit-only**:
  `report2_precision_mca_gate.py` is re-run against the shipped reference MCA
  summaries, so the examiner sees the gate logic execute and reach the recorded
  2-of-4 verdict, marked `SKIP (audit-only, no fresh MCA sampling)`
- no Ninja → fall back to the platform default CMake generator
- insufficient RAM for `--tier full` → refuse with the required figure, suggest `--tier core`

Every `SKIP` appears in the report with its cause. The run never fails halfway
through because of a missing optional dependency.

---

## 8. Documentation shipped

`README.md` (English) — what this is, what it is not, the Report 1 exclusion and
why `src/euler/` is nevertheless present, prerequisites, the three-command
quickstart, how to read the verdict table.

`REPRODUCE.md` — per-family instructions, the claim table of §5.2, the four
verdict types, the `full`-only claim list, the OpenMP default caveat of §4.1,
the `ulp_max` and GCC-vectoriser notes of §5.3, and the Appendix 3 execution
record for context.

`QUICKSTART.zh.md` — one page, Chinese: install, `python reproduce.py --tier
smoke`, where the report lands.

---

## 9. Testing

`tests/py/test_repro_export.py`, run from the repository root:

1. `export.py` produces a `dist/` tree containing every file `manifest.py`
   promises and nothing matching an exclusion glob (no `grid.bin`, no build dir,
   no `.worktrees`).
2. The Python import closure is complete: every `import` in every staged module
   resolves either to the stdlib, to a `requirements.txt` entry, or to a staged
   file.
3. Every `tests/cases/*.cfg` referenced by a staged driver is staged.
4. Every reference summary named in `manifest.py` is staged and is valid JSON.
5. `tolerances.toml` parses, and its claim ids exactly match the set
   `compare.py` produces — no orphan claims in either direction.
6. `compare.py` fed the reference summaries as if they were fresh output yields
   all `PASS` / `PLATFORM-BOUND` / `INFO` and no `FAIL`. This is the
   self-consistency check that the tolerances admit the paper's own numbers.
7. The staged tree configures and builds `hrsc`, `hrsc_mhd` and `unit_tests`,
   and `--tier smoke` completes with a zero exit code.

Item 6 is the load-bearing test: it catches a tolerance typo before the package
ever reaches an examiner.

---

## 10. Decisions taken

- **English README, Chinese quickstart.** The dissertation and supervisor
  correspondence are English; the Chinese page is a convenience, not the
  primary document.
- **No `grid.bin` shipped.** Only `summary.json`, the 17 report figures, and the
  figure manifest. This is what keeps the package at 15–25 MB rather than 295 MB.
- **Tolerances derived, not guessed.** Each value in `tolerances.toml` carries
  an inline comment naming the summary field it came from and why its band is
  what it is.
- **No driver script edited.** See §3.3.

## 11. Out of scope for this spec

Rebuilding the LaTeX manuscript; re-running Report 1 evidence; cluster
submission; a Docker image for the CPU path (the CPU path is plain CMake and
needs none); GPU coverage beyond the two families the harness already supports
(`docs/HARNESS.md` records HLLD-on-GPU, KH-on-GPU and GPU MCA as unsupported).
