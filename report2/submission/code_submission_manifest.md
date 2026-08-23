# Report 2 code-submission manifest

**Status:** `draft`

**Prepared:** 2026-08-03

**Release state:** not frozen

This file describes the intended Report 2 code and evidence bundle. It is not
a release attestation. At preparation time, `git rev-parse HEAD` returned
`4427aa904bd79fdd763f4dd095b9d69204d218cc`, but the worktree was dirty. That
commit is an observation only and must not be used as the submitted revision.
The release commit and clean-worktree check must be recorded during the freeze
procedure below.

The status and claim boundaries remain those in
`docs/experiment_logs/report2_evidence_map.md`. In particular, lifecycle
manifests and paper importance do not promote `provisional`, `validation`,
`negative-result`, `superseded`, or `invalid` evidence.

## Pipeline and source entry points

The submission follows the repository contract
`config -> build -> run -> measure -> aggregate -> plot`.

| Layer | Retained entry points |
|---|---|
| Source and configuration | `CMakeLists.txt`, `cmake/PrecisionConfig.cmake`, `cmake/CompilerFlags.cmake`, `src/main.cpp`, `src/mhd_main.cpp`, and the implementation under `src/app/`, `src/core/`, `src/euler/`, `src/mhd/`, `src/gpu/`, and `src/utils/` |
| Build | `scripts/build_all.sh` and `scripts/build_matrix.py`; direct CMake builds remain supported |
| Run | `scripts/run_matrix.py` and the versioned contracts under `scripts/harness/` |
| Read and measure | `scripts/io_helper.py` and reusable metrics under `scripts/metrics/` |
| Aggregate | `scripts/aggregate_metrics.py`, `scripts/regression/matrix_summary_report.py`, and the packet-specific scripts listed below |
| Plot and tables | `scripts/figures/report2_publication_figures.py` and `scripts/figures/report2_chapter4_cpu_gpu_table.py` |

The CPU executables are `hrsc` for Euler and `hrsc_mhd` for ideal MHD.
`ENABLE_CUDA=ON` additionally enables the opt-in CUDA targets. The Report 2
device claim is restricted to the HLL Brio--Wu and Orszag--Tang rows; it does
not include HLLD or Kelvin--Helmholtz on the GPU.

## Report-facing configurations, matrices, and drivers

Retain these source configurations:

- `tests/cases/toro_1d/sod.cfg`
- `tests/cases/liska_wendroff_2d/config3_n200.cfg`
- `tests/cases/brio_wu_1d/brio_wu.cfg`
- `tests/cases/brio_wu_1d/brio_wu_ref.cfg`
- `tests/cases/brio_wu_1d/brio_wu_2d.cfg`
- `tests/cases/mhd_divb_clean/divb_blob.cfg`
- `tests/cases/orszag_tang_2d/orszag_tang.cfg`
- `tests/cases/orszag_tang_2d/orszag_tang_ref.cfg`
- `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg`
- `tests/cases/kelvin_helmholtz_2d/kh.cfg`
- `tests/cases/kelvin_helmholtz_2d/kh_ref.cfg`
- `tests/cases/kelvin_helmholtz_lecoanet_2d/lecoanet_unstratified.cfg`

Retain the explicit report-facing matrices:

- `experiments/week15/brio_wu_precision_pilot_p1/matrix.json`
- `experiments/week15/brio_wu_precision_pilot_hlld_p1/matrix.json`
- `experiments/week18/euler_mhd_cross_system/matrix.json`
- `experiments/week18/resolution_ladder_pair_completion/matrix.json`

The pair-completion matrix is retained as repair provenance. Its referenced
$512^2$ comparison grid is a non-submission transient artefact; retaining the
matrix does not authorise adding that large grid to the bundle.

Several later packets generate their matrix and copied `config.cfg` files from
the base configurations rather than storing a separate input matrix. Their
canonical packet drivers are:

| Evidence packet | Canonical analysis/run driver | Evidence status boundary |
|---|---|---|
| Brio--Wu reference validation | `scripts/regression/mhd_brio_wu_1d.py` | `validation` |
| Two-dimensional invariance and GLM validation | `scripts/regression/mhd_2d_week12.py` | `validation` |
| Brio--Wu deterministic/MCA packets | `scripts/regression/mhd_precision_pilot.py` | HLL/HLLD Week-15 packets are `report-grade` only under the unified scope gate |
| Fixed-window temporal discrepancy | `scripts/regression/mhd_temporal_divergence.py` | `negative-result`; no formal Lyapunov claim |
| Bounded HLL CPU/GPU axis | `scripts/regression/mhd_gpu_hardware_axis.py` | named Brio--Wu/Orszag--Tang rows only |
| Repeated hardware, requested-thread, and CFL checks | `scripts/regression/mhd_week18_supplemental.py` | `report-grade` within the named workstation/configurations |
| Euler--MHD range comparison | `scripts/regression/report2_cross_system.py` | discrepancy, not cross-system accuracy |
| OT/KH three-resolution ladder | `scripts/regression/mhd_week18_resolution_ladder.py` | no asymptotic-convergence or fp32-adequacy claim |
| Deterministic/MCA scope audit | `scripts/regression/report2_precision_mca_gate.py` | Brio--Wu promoted; both OT rows remain `provisional` |
| KH solver/precision timing | `scripts/regression/mhd_week18_kh_timing.py` | one workstation and one fixed KH setup |
| Lecoanet KH linear reproduction | `scripts/regression/mhd_lecoanet_kh_reproduction.py` | `validation`; not the nonlinear diffusive/dye reference |
| Direct Brio--Wu build semantics | `scripts/regression/mhd_brio_build_semantics.py` | one MSVC matrix; no compiler-wide claim |
| Seven publication figures | `scripts/figures/report2_publication_figures.py` | source-audited figure routing only |

Retain the packet `manifest.json` files and validate them through
`scripts/harness/experiment_manifest.py`; they describe lifecycle and
retention, while the evidence map remains the claim-status authority.

## Environment, build, and tests

Minimum CPU environment:

- Git, CMake 3.18 or newer, Ninja, and a C++17 compiler;
- Python 3 with `numpy`, `matplotlib`, and `scikit-image` from
  `analysis/requirements.txt`, plus `pytest` for the Python tests;
- Bash for `scripts/build_all.sh`. On Windows, load the Visual Studio developer
  environment before configuring MSVC builds.

CUDA is optional. Reproducing the bounded GPU packet additionally requires a
CUDA-capable system and an architecture-compatible CUDA Toolkit; the recorded
workstation evidence used CUDA 13.3 and `CMAKE_CUDA_ARCHITECTURES=120`.
Verificarlo/Docker and the documented CSC environment are separate optional
requirements for MCA reproduction and are not prerequisites for deterministic
CPU validation.

In the current Windows workspace, the unqualified `python` command resolves to
an unusable WindowsApps stub. Use the project interpreter explicitly:

```powershell
$report2Python = "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe"
& $report2Python -m pytest tests\py -q
```

The portable command blocks below use `python` as a placeholder for a working
Python 3 interpreter; substitute the environment-specific executable when
necessary.

Example clean CPU builds from the repository root:

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double
cmake -B build-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-float
```

Run the compiled unit tests (`.exe` suffix on Windows) and Python checks:

```bash
./build-double/unit_tests -r compact
./build-float/unit_tests -r compact
python -m pytest tests/py -q
python -m pytest tests/py/test_experiment_manifests.py -q
```

The complete CPU build-axis matrix is generated with:

```bash
bash scripts/build_all.sh
```

Build directory names are labels. The effective compiler and math semantics in
`build_semantics.json` and run metadata are the authority.

## Publication-figure and source-summary SHA-256 authority

The following values are copied from
`experiments/week18/report2_publication_figures/figure_manifest.json`; they are
not newly assigned release hashes. A read-only check on 2026-08-03 found every
listed source, PNG, and PDF equal to its recorded value. The PDF is the
manuscript asset and the PNG is the review copy.

| Figure ID | Source summary SHA-256 | PNG SHA-256 | PDF SHA-256 |
|---|---|---|---|
| `validation_refinement_glm` | `experiments/week12/brio_wu_1d/summary.json`: `3ce57bdc28d983e0e5ad463df4fa5940a2d7a0c52cdc14c92a907fb201be3ed7`; `experiments/week12/mhd_2d/divb_clean/summary.json`: `de05960d8a4fc2c033ff1fc0ee4d89364dac171b757af1dd28013ba0b2c5cc56` | `6ca294624bbc277652388f2de71170700f3cf749cf36fe2c35965911e3abb8f1` | `ec6b99ddbc188b28aeb4115ef67ba9a9e77b5cf33a4f5db79e44325b1d94e2bd` |
| `cross_system_sensitivity` | `experiments/week18/euler_mhd_cross_system/summary.json`: `ecc1b611488d0991216791436cd8eb32ed1d50303e183a4cdb80bf857c121180` | `436ef2cf9090c9265a352aaeab4ecbfc36f2759c8b82dbe6155ec09dca7b98bf` | `beb1b8d134470983c1987cffa795456e2e354df75239571e8d47b243f7003e8d` |
| `hardware_reproducibility` | `experiments/week18/supplemental/hardware_repeats/summary.json`: `1f34c63d524b5389bd9fc887bdc60540e01f463941286d8f8fe3e7af92b07ab4` | `2407eeb682c35d0531d70a785581453f10f2a7415721de5a324a721693affdc5` | `643820272d5a8cedc0ca6235a280b66d751fc4764fe65b80fe6c13ad470aba7c` |
| `resolution_precision` | `experiments/week18/resolution_ladder/summary.json`: `1b50afecf4b974261860fd82999c5a7319104a43182bedb057ee97fb0d9855f8` | `c336b74b0eb71116b37d59f5b9ffcd43318c66acc0a418309a8d4c1271d702b7` | `36c516bdd93a30a13861430752bd7b7f732f1f12b91253ae616fc59b8850c017` |
| `temporal_discrepancy` | `experiments/week15/mhd_temporal_divergence/summary.json`: `a30954ea36c6e64848ff983e3441989ec7830f9169af06540d80319abaf9f656` | `c6d919991777659cad893d88792d3cef209232bf533102bd65f1986ce85b5257` | `901f855f9ea612da2886c6632c400f2f56403bc67ee7fd8ddfb847fb6831d2bf` |
| `precision_refinement_context` | `experiments/week18/resolution_ladder/summary.json`: `1b50afecf4b974261860fd82999c5a7319104a43182bedb057ee97fb0d9855f8` | `d2eee5423c09bd8710bb3f2a87b1e624019cdb84efc1d5ee0c90c72d4e7ff735` | `51ad93f4fd9ebba37fe868da105e360a29785b82dd7faf57af2a6d001914c68c` |
| `kh_timing` | `experiments/week18/kh_solver_timing/summary.json`: `4520a16231bd1ac2bc2ab54507f174ec05217e96b49e075459b286c11394bbc8` | `7b8a955536c8fdb35b1f5f873a4f2f4ca82e339d208eea78e1c98e01a22f16c1` | `12e0140c6302bbbcd98ce8845c2a46a483c6632dcadcf598b7f2cf09fea85358` |

Other key scalar authorities remain the bounded summary files named by the
evidence map, notably `experiments/week18/precision_mca_gate/summary.json` and
`experiments/week20/brio_wu_build_semantics/summary.json`. They are not part of
the seven-figure hash manifest and must not be assigned the figure manifest's
release authority.

## Retained and excluded artefacts

| Retain | Exclude from the code bundle |
|---|---|
| Source, CMake files, tests, base cfgs, explicit matrices, harness and packet scripts | `build-*`, `build-matrix/`, CMake caches, executables, object files, and other generated build products |
| Lifecycle manifests; generated per-run cfgs; completion-attested metadata; relevant stdout/stderr; scalar `summary.json`, `summary.csv`, and `summary.md` files | Large transient `grid.bin` outputs, warm-up grids, and unanalysed raw fields |
| The seven audited publication PNG/PDF pairs and their `figure_manifest.json` | `experiments/week17/report2_synthesis/figures/axis_ranking.png`, which ranks incomparable metrics |
| Valid bounded provenance needed to audit corrected pairs or MCA scope | Week-14 invalid HLL MCA values as evidence; superseded pilots as current results; failed replay output as an authoritative replacement |
| Report-facing table/figure generators and compact audit figures where named by the evidence map | Full-scale KH MCA claims, unmatched OT deterministic/MCA combinations, and any file that implies p24 equals IEEE fp32 |

Ignored local metadata may be included only when it is named by an evidence
package and is small enough for the submission channel. Do not add large grids
merely because an ignored run directory exists.

## Minimum validation and reproduction commands

The following audit uses stored scalar evidence and does not rerun large grids:

```bash
python -m pytest tests/py/test_experiment_manifests.py -q
python scripts/audit_experiments.py --format markdown
python scripts/regression/report2_precision_mca_gate.py
python scripts/figures/report2_publication_figures.py --out experiments/week18/report2_publication_figures
python scripts/figures/report2_chapter4_cpu_gpu_table.py
```

The last three commands rewrite derived summaries, figures, or table files.
Run them only in a clean reproduction checkout or after preserving the audited
submission artefacts.

A compact end-to-end matrix example is:

```bash
bash scripts/build_all.sh
python scripts/run_matrix.py experiments/week18/euler_mhd_cross_system/matrix.json
python scripts/regression/report2_cross_system.py --root experiments/week18/euler_mhd_cross_system
python scripts/figures/report2_publication_figures.py --out experiments/week18/report2_publication_figures
```

The packet-specific full reruns are intentionally separate because their
runtime and hardware requirements differ:

```bash
python scripts/regression/mhd_temporal_divergence.py
python scripts/regression/mhd_week18_resolution_ladder.py
python scripts/regression/mhd_week18_supplemental.py all --repeats 5
python scripts/regression/mhd_week18_kh_timing.py --repeats 5
```

These drivers remove transient grids by default where documented. Do not add
`--keep-grids` to a submission run unless a specific metric audit requires it.
MCA and CUDA reruns require their recorded specialised environments and are not
silently substituted by deterministic CPU commands.

## Release-freeze record

Before changing this manifest from `draft` to a release record:

1. Complete the intended source, report, and evidence edits, then run the
   minimum tests and figure/source hash audit.
2. Confirm that no untracked submission files or accidental large artefacts
   remain and that `git diff --check` passes.
3. Commit the exact submission state.
4. Record the output of `git rev-parse HEAD` below as the release commit.
5. Record `git status --porcelain=v1` as empty. A non-empty result means the
   bundle is not frozen.
6. Recompute the SHA-256 values in `figure_manifest.json`; if any source or
   figure changes, regenerate the seven-figure set and review it before
   updating the recorded hashes.
7. Record the archive filename and its SHA-256 after packaging. Do not include
   build directories or transient grids in that archive.

Freeze commands:

```bash
git diff --check
git status --porcelain=v1
git rev-parse HEAD
python -m pytest tests/py/test_experiment_manifests.py -q
python -m pytest tests/py -q
```

Release fields (deliberately unset while this manifest is a draft):

- Release commit: `UNSET`
- Clean-worktree check: `NOT RUN FOR RELEASE`
- Archive filename: `UNSET`
- Archive SHA-256: `UNSET`
- Figure/source hash recheck: `NOT RUN FOR RELEASE`
