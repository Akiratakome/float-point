# Project Index — `floatpoint`

> Agent-facing entry point. **Read this first**, then `AGENTS.md` and `docs/HARNESS.md`.

**What this repository is.** A workload-agnostic *numerical qualification harness*: it
measures how precision, compiler semantics, device math flags, parallelism and hardware
change a computed result, and it records enough provenance for those measurements to be
re-run and audited. The pipeline is the deliverable; a solver or a model is only a
workload plugged into it.

**Central claim under test.** *Under which conditions is a computation bit-for-bit
reproducible, which mechanisms break that, and what does restoring it cost?*

**Two workload families.**

| # | Family | Status | Role |
|---|---|---|---|
| 1 | **HRSC solver** — CPU/CUDA compressible Euler + ideal MHD | **delivered** | Numerically sensitive non-ML stress workload; source of the existing evidence base |
| 2 | **LLM inference** — PyTorch eager / vLLM | **planned** | Primary workload for the current phase; extends the same method to a Transformer |

Family 2 keeps Family 1 in the tree deliberately: it proves the harness is not hard-coded
to one workload, and it lets the same determinism question be answered on two unrelated
computations.

**Status legend used throughout:** **[delivered]** exists and has committed evidence ·
**[planned]** designed, not yet implemented.

---

## 1. Where to look — by concern

| If you need… | Read |
|---|---|
| Hard rules for agents working here | [`../AGENTS.md`](../AGENTS.md) |
| Canonical pipeline, run contract, build semantics, manifests | [`HARNESS.md`](HARNESS.md) |
| Script ownership, canonical entry points, legacy boundaries | [`../scripts/README.md`](../scripts/README.md) |
| Shared harness contracts and validation | [`../scripts/harness/`](../scripts/harness/) |
| Experiment artefact layout and retention rules | [`../experiments/README.md`](../experiments/README.md) |
| Delivered evidence and its claim boundaries | §6 below, then the packet's own `summary.md` |
| Compute resources (local + CSC) | §4 below |
| Family 2 execution plan and decision records | [`aiinfra/PLAN.md`](aiinfra/PLAN.md), [`aiinfra/ADR.md`](aiinfra/ADR.md) |
| Manuscript and figures | [`../dissertation/phd-thesis-template-2.4/`](../dissertation/phd-thesis-template-2.4/) |

---

## 2. Architecture

```text
                 config -> build -> run -> measure -> aggregate -> plot
                   |        |       |        |           |          |
  workload  -------+--------+-------+        |           |          |
  (HRSC | LLM)                      |        |           |          |
                                    v        v           v          v
                            run-record   metrics    summary.*   figures
                             schema v1                          + manifest
                                    |                                |
                                    +----- experiment-manifest ------+
                                            (lifecycle + retention)
```

| Layer | Location | Responsibility |
|---|---|---|
| Workload — solver | `src/` | Euler + ideal MHD, CPU and CUDA, build-time precision |
| Workload — LLM **[planned]** | `scripts/aiinfra/backends/` | eager / vLLM adapters behind one interface |
| Execution contracts | `scripts/harness/` | `RunSpec`/`RunRecord`, failure taxonomy, artifact freshness, build semantics, manifest validation |
| Matrix driver | `scripts/run_matrix.py`, `scripts/build_matrix.py`, `scripts/build_all.sh` | Materialise configs, execute, write metadata — never edits a source cfg |
| Measurement | `scripts/metrics/`, `scripts/regression/` | Reusable metrics and packet-specific analysers |
| Aggregation | `scripts/aggregate_metrics.py`, `scripts/regression/matrix_summary_report.py` | Combine summaries |
| Presentation | `scripts/figures/` | Plots with source gates and SHA-256 manifests |
| Audit | `scripts/audit_experiments.py`, `scripts/harness/experiment_manifest.py` | Read-only lifecycle and retention checks |

**Failure taxonomy** (`scripts/harness/contracts.py`): `configuration_error`,
`unsupported_capability`, `numerical_failure`, `incomplete_run`, `infrastructure_error`,
`artifact_error`, `schema_error`. A capability a device does not have produces a
*structured record*, not a blank cell.

**Manifest lifecycle** (`scripts/harness/experiment_manifest.py`): `canonical`,
`provenance`, `superseded`, `invalid`, `generated`.

---

## 3. Repository scale (measured 2026-08-24)

| Item | Count |
|---|---|
| Commits (since 2026-04-02) | 547 |
| `src/` C++/CUDA | 8,076 lines |
| `scripts/` Python/Shell/Slurm/PowerShell | 166 files, 35,617 lines |
| Catch2 test files | 48 |
| pytest modules | 59 |
| Run records (`experiments/**/metadata.json`) | 1,065 |
| Aggregated evidence packets (`summary.json`) | 85 |
| Committed figures (PNG) | 110 |

---

## 4. Compute resources

### 4.1 Local workstation

| Layer | Value |
|---|---|
| Processor | Intel Core Ultra 9 275HX, 24 cores |
| Device | NVIDIA GeForce RTX 5070 Laptop GPU, `sm_120`, driver 32.0.15.9191 |
| OS | Windows 11, build 10.0.26200 |
| Host compiler | MSVC 19.51.36248.0 (toolset 14.51.36231) |
| Device compiler | CUDA Toolkit 13.3, `CMAKE_CUDA_ARCHITECTURES=120` |
| Stochastic arithmetic | Verificarlo 2.5.1 (Docker) |
| Project Python | `C:/Users/tangy/miniconda3/envs/floatpoint/python.exe` (3.11, has pytest) |

MSVC is not on a bare PowerShell `PATH`. Load the developer environment first:

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
where cl
```

### 4.2 Cambridge LSC/CSC (public documentation, checked 2026-08-24)

| Plane | Host | Spec | Limits |
|---|---|---|---|
| Control | `athena` | Xeon E5-2430 v2, 6 cores, 32 GB | Submit / inspect / aggregate only |
| CPU compute | `csc-mphil` = phy-cerberus4/5/6 | Xeon Gold 5418Y, 48 cores, 248 GB | max 48 cores, **6 h** |
| GPU compute | `csc-mphil-gpu` = phy-thetis / phy-damysus | 2 × RTX 5090 32 GB (`sm_120`), 32 cores, 128 GB | **max 2 GPUs**, **6 h** |
| CPU (LSC) | `lsc` = phy-cerberus7/8 | as above | max 48 cores, 36 h |
| Ampere | `lovelace` (direct SSH, **not** Slurm) | Xeon Silver 4314, 32 cores, 257 GB, 2 × A30 24 GB (`sm_80`) | shared machine; use `nice -19` |

- Submit with `--clusters=CSC`; request GPUs with `--gpus=N`. Reference job scripts live at
  `/lsc/opt/slurm/slurm_lsc.sh` and `/lsc/opt/slurm/slurm_gpu.sh`.
- **Nodes are non-exclusive** — up to four separate jobs per node. Any timing claim must
  carry a co-tenancy record.
- Cluster toolchain: GCC 13.2/14.2/15.2, Clang 18.1, CUDA 12.5/12.6/12.9/13.1,
  OpenMPI 4.1.6, CMake 3.28.3, Python 3.12.3, Verificarlo 2.4.0 (`/lsc/opt/verificarlo-2.4.0`).
- Node-local scratch is `/local/data`; it is **not backed up** and no quota is published.
- Multi-node GPU jobs are **not documented** — treat as unverified until probed. Multi-node
  CPU MPI is documented and available.

### 4.3 Accelerator differences that drive experiment design

| | A30 (`sm_80`, datacenter) | RTX 5090 (`sm_120`, consumer) |
|---|---|---|
| Memory / bandwidth | 24 GB HBM2 / 933 GB/s | 32 GB GDDR7 / 1792 GB/s (**1.92×**) |
| FP8 | not supported | supported |
| FP64 | 5.2 TF (1:2) | ~1.64 TF (1:64, third-party figure) |

The 1.92× bandwidth ratio is the upper-bound anchor for every memory-bound throughput
claim; the FP8 gap is what exercises the `unsupported_capability` path.

---

## 5. Build matrix (Family 1)

| Build dir | `FLOAT_PRECISION` | Use |
|---|---|---|
| `build-double/` | double | Canonical CPU baseline |
| `build-float/` | float | Precision-axis counterpart |
| `build-cuda*/` | double/float | Opt-in CUDA paths |
| `build-vfc-p53/` | double | Verificarlo MCA (auto-recreated by the driver) |

All build directories are `.gitignore`d and disposable.

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-double
bash scripts/build_all.sh          # full CPU matrix under build-matrix/
```

Controlled axes: precision · `OPT_LEVEL` in {O2,O3,Ofast} · `FAST_MATH` · `STRICT_IEEE` ·
`RIEMANN_STRICT_INEQUALITY` · `GPU_FMA_CONTRACT` · `GPU_FAST_MATH` · `ENABLE_OPENMP` ·
`HLLD_COUNTERS`. CMake writes `build_semantics.json`; **directory names are labels, not
proof of compiler behaviour** — the recorded `effective_math_mode` is the authority.

---

## 6. Delivered evidence (Family 1)

Headline results, each bound to its packet. Figures below come from the committed
`summary.json`, which is the authority when a prose document disagrees.

| Result | Packet | Boundary |
|---|---|---|
| Matched CPU/GPU HLL outputs are bit-identical (`ulp_max=0`, `L1=L∞=0`) **only with `--fmad=false`**; restoring nvcc's default breaks it in all 4 pairs (fp32 density `L∞`: Brio–Wu 2.265e-6, OT 2.074e-5) | `experiments/week20/gpu_fma_contraction/` | Brio–Wu 1D and Orszag–Tang 2D, HLL only |
| Relaxed device math does not accumulate monotonically: `--use_fast_math` sits *closer* to the host baseline than contraction alone | `experiments/week21/gpu_fast_math/` | Same two cases |
| OT 2D GPU speed-up 5.609× (double) / 5.655× (float); Brio–Wu 1D GPU is **slower** (0.066× / 0.518×) — launch and transfer dominate a small mesh | `experiments/week16/cpu_gpu_hardware_axis/` | Single-core CPU baseline, so these are serial-host ratios |
| KH 256² wall-time medians (n=5 after one warm-up): HLL 34.484 s (fp64) / 29.196 s (fp32); HLLD 39.542 s / 34.254 s; within-group ULP drift 0 | `experiments/week18/kh_solver_timing/` | One workstation, single thread |
| Euler OpenMP thread axis is bitwise identical (`ulp_max=0`) at 1/2/4/8 threads while really parallelising: 4.79× (fp64) and 4.54× (fp32) at 8 threads over one thread | `experiments/week21/euler_openmp_thread_axis/` | Euler HLLC, LW config 3 at 200²; speed-up measured against one thread, not the serial build |
| Discrepancy is spatially concentrated: 38% of HLLD's total on 1% of cells, vs 6% for HLL | `experiments/week21/precision_localisation/` | OT 256² |
| CP Alfvén converges towards second order (pairwise 1.706→1.886, fitted 1.818); fp32 leaves the fp64 curve at N=2048, and fp64 on 4096 cells beats fp32 on 8192 | `experiments/week21/cp_alfven_convergence/` | One smooth case; orders still rising |
| Build-semantics isolation, one axis at a time, over 8 clean MSVC builds | `experiments/week20/brio_wu_build_semantics/` | Single compiler; no performance claim |
| Verificarlo MCA on CSC: reference quad backend ≈417× slower than native (24.0 vs 0.0575 s/step); made feasible under the 6 h cap by splitting each block into its own Slurm array task | `experiments/report2_w16_verificarlo_findings/` | KH 256², t=1.0 |

Other retained packets: `week15/mhd_temporal_divergence/` (fixed-window negative result),
`week18/{supplemental,euler_mhd_cross_system,resolution_ladder,report2_publication_figures}/`,
`week19/lecoanet_kh_linear_reproduction/`,
`week21/{hlld_decision_counts,implementation_temporal,resolution_ladder_hll_cfl02}/`,
`week22/mhd_saturation_grid_solver_*/`, and the Report 1 closeout under `experiments/report1/`.

---

## 7. Planned work (Family 2) — **[planned]**

**Execution plan: [`aiinfra/PLAN.md`](aiinfra/PLAN.md). Decision records: [`aiinfra/ADR.md`](aiinfra/ADR.md).**
Both passed design review on 2026-08-24; step 0 (a one-day spike proving the headline phenomenon
exists) and step 1 (additive harness generalisation) are unblocked and depend on nothing unverified.

Local execution plan: [`aiinfra/plans/2026-08-25-local-core-steps-0-3.md`](aiinfra/plans/2026-08-25-local-core-steps-0-3.md).

The remaining planned components use this target layout, so new files land where the harness expects them:

```text
configs/aiinfra/              # model pins, workload matrices, thresholds
scripts/aiinfra/              # config, result schema, backends/, determinism, fidelity,
                              # noise floor, aggregate, profile, serve
scripts/cluster/aiinfra/      # Slurm wrappers for csc-mphil-gpu
src/ai_kernels/               # batch-invariant reduction (Triton + CUDA)
tests/py/test_aiinfra_*.py
experiments/aiinfra/          # generated; only summaries/manifests/figures committed
docs/aiinfra/                 # architecture, environment matrix, reproduction, results
```

Sequence and gates:

1. **Additive generalisation of the harness.** **[delivered]** `run_matrix.py` gains an optional
   `arguments` array and `artifact_kind`; `runner.py` gains `kind=workload completed=N
   expected=N`; a `workload_result` validator is added. *Gate:* every existing HRSC matrix
   builds a byte-identical command and all current tests stay green.
2. **Determinism and fidelity.** Repeat-sampled unique-output counts, a same-configuration
   noise floor, then a breakage matrix over batch size, concurrency, backend, TP degree
   and hardware. *Gate:* at least one variable reproducibly turns one unique output into
   several, on two devices, with the noise floor quantified first.
3. **Coverage.** Batch-invariant operator (Triton + CUDA), Nsight/roofline attribution of
   the decode bandwidth ratio, a precision/quantisation matrix gated by FP8 availability,
   and intra-node TP=2 with NCCL microbenchmarks.
4. **Optional, requires explicit approval:** compile-time-optional MPI in the HRSC solver,
   to measure reduction-order effects on multi-node CPU. The default single-process path
   must stay byte-identical.

**Scope honesty, to be repeated in any outward-facing material:** distributed coverage
stops at intra-node 2-GPU tensor parallelism plus multi-node CPU MPI. No multi-node GPU,
no RDMA/InfiniBand, no scaling curves, no distributed *training* framework experience.

---

## 8. Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `No CMAKE_CXX_COMPILER could be found` | Bare PowerShell has not loaded VS BuildTools | Run through `VsDevCmd.bat` (§4.1) |
| `python: command not found` in a shell script | Microsoft Store Python stub on `PATH` | Set `PYTHON` to the Miniconda path, or rely on the script's `resolve_python` |
| Header-only edits never rebuild; `ninja: no work to do`; stale binaries | ninja's MSVC header-dependency database is empty (`ninja -t deps` shows `#deps 0`): the localised `cl /showIncludes` prefix recorded at configure time does not byte-match build-time output on this zh-CN workstation | Delete and re-configure the build dir from the same console; verify `ninja -t deps <obj>` reports nonzero deps before trusting incremental builds |
| Bash redirect of `hrsc.exe` output produces 0 bytes | MSYS pipe handle quirk under PowerShell-spawned bash | Drive long pipelines from PowerShell directly |
| `pytest` reports hundreds of setup errors with `PermissionError: [WinError 5]` | The default basetemp under `%TEMP%\pytest-of-<user>` has become unreadable | `pytest.ini` pins `--basetemp=.pytest_tmp` inside the repository, so a fresh clone works; pass your own `--basetemp` to override |
| A CSC timing number looks anomalous | Node was shared (up to 4 jobs per node) | Check the co-tenancy record; re-run on a quiet node and mark the polluted run non-headline |

---

## 9. Historical documents

The weekly planning material from the MSc report cycle (`docs/weekN/`, `docs/emails/`,
`docs/experiment_logs/`, `docs/requirement/`, `docs/superpowers/`) is **not part of this
project's architecture** and is no longer in the working tree. It stays reachable through
git history if a past decision needs tracing; do not link to it from current documents.

The manuscript under `dissertation/` and the committed packets under `experiments/` remain
authoritative for Family 1 results. Where a prose document and a committed `summary.json`
disagree, **the `summary.json` wins** — §6 above was re-derived from the summaries on
2026-08-24, which corrected a previously published OT GPU speed-up pair (`5.965×/6.353×`)
that no committed summary supports.

---

*Last updated: 2026-08-24.*
