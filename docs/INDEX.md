# Project Index — `floatpoint`

> Agent-facing entry point. **Read this first** before exploring; it points to the canonical doc/data for every concern.

**Project**: Effect of Floating-Point Precision and Hardware on HRSC Schemes (MSc, 20 weeks)
**Reports**: Report 1 due 2026-05-29 (Week 10) · Report 2 due 2026-08-07 (Week 20)
**Repo root**: `c:/Users/tangy/Desktop/floatpoint`
**Default branch**: `main` · **Active branch**: `main`

---

## 1. Where to look — by concern

| If you need… | Read |
|---|---|
| Project requirements, deliverables, deadlines | [requirement/overall.md](requirement/overall.md) |
| Canonical experiment harness workflow | [HARNESS.md](HARNESS.md) |
| Script architecture, canonical entry points, legacy/provenance boundaries | [../scripts/README.md](../scripts/README.md) |
| Coding conventions, style, FP guidance | [requirement/coding guidance.md](requirement/coding%20guidance.md) |
| Project briefs (PDFs from supervisor) | [requirement/](requirement/) (`*.pdf`) |
| What's been done so far this project | per-week `weekN-summary.md` (see §2) |
| What's planned this week | per-week `weekN-plan.md` (see §2) |
| Supervisor correspondence + feedback artefacts | [emails/](emails/) — meeting scripts, replies, decision/comparison artefacts, supervisor-driven plans (named `weekN_<topic>_YYYY-MM-DD.md`) |
| Raw experiment data logs (deliverable artefacts) | [experiment_logs/](experiment_logs/) (named `weekN_<phase>_<topic>.md`) |
| Report 1 final evidence map (which artefact lives where, what is superseded) | [experiment_logs/report1_evidence_map.md](experiment_logs/report1_evidence_map.md) |
| Legacy Report 1 Week-7 task index | [experiment_logs/report1_evidence_index.md](experiment_logs/report1_evidence_index.md) |
| Report 2 starting point | [requirement/overall.md](requirement/overall.md) Phase 2 + Report 1 conclusions in [experiment_logs/report1_evidence_map.md](experiment_logs/report1_evidence_map.md) |
| Manual reproduction recipe (build → tests → regression) | [week4/week4-verification.md](week4/week4-verification.md) |
| How Week N's state evolved from Week N-1 | `weekN/weekN-1_to_weekN_bridge.md` (kept at the target week) |

---

## 2. Per-week navigation

**Convention** (post-2026-04-28 reorg): each week keeps **only** `weekN-plan.md` + `weekN-summary.md` at the top. Everything else lives in `archive/` (legacy planning docs, design notes, briefings) or in shared folders (`emails/`, `experiment_logs/`).

| Week | Plan | Summary | Archive |
|---|---|---|---|
| 1 | [week1-plan.md](week1/week1-plan.md) | [week1-summary.md](week1/week1-summary.md) | [week1/archive/](week1/archive/) |
| 2 | [week2-plan.md](week2/week2-plan.md) | [week2-summary.md](week2/week2-summary.md) | [week2/archive/](week2/archive/) |
| 3 | [week3-plan.md](week3/week3-plan.md) | [week3-summary.md](week3/week3-summary.md) | [week3/archive/](week3/archive/) |
| 4 | [week4-plan.md](week4/week4-plan.md) | [week4-summary.md](week4/week4-summary.md) | [week4/archive/](week4/archive/) |
| 5 | [week5-plan.md](week5/week5-plan.md) | [week5-summary.md](week5/week5-summary.md) | [week5/archive/](week5/archive/) |
| 6 | [week6-plan.md](week6/week6-plan.md) | [week6-summary.md](week6/week6-summary.md) | [week6/archive/](week6/archive/) |
| 7 | [week7-plan.md](week7/week7-plan.md) | Report 1 evidence complete; see [report1_evidence_map.md](experiment_logs/report1_evidence_map.md) | (none) |
| 12 | [week12-plan.md](week12/week12-plan.md) | [week12-summary.md](week12/week12-summary.md) | (none) |

Week 4 also keeps:
- [week4-verification.md](week4/week4-verification.md) — manual verification checklist (Phase B/C reproduction recipe)
- [week3_to_week4_bridge.md](week4/week3_to_week4_bridge.md) — Week 3 → Week 4 state migration
- [cfg_reference.md](week4/cfg_reference.md) — Week-4 snapshot of runtime cfg keys (referenced from `week4-plan.md`)

Week 5 pre-start bridge:
- [week4_to_week5_bridge.md](week5/week4_to_week5_bridge.md) — Week 4 → Week 5 handoff (delivered work, reusable interfaces, Week 5 gaps)
- [week5-verification.md](week5/week5-verification.md) — manual reproduction recipe for Week 5 (Phase A/B/C/D/E coverage)

Week 6 pre-start bridge:
- [week5_to_week6_bridge.md](week6/archive/week5_to_week6_bridge.md) — Week 5 → Week 6 handoff (delivered work, reusable interfaces, Week 6 GPU plan)

Week 6 deliverables:
- [week6-design.md](week6/archive/week6-design.md) — GPU Euler + CSC migration design
- [week6-verification.md](week6/archive/week6-verification.md) — Phase A-E reproduction recipe
- [csc_gpu_environment.md](week6/archive/csc_gpu_environment.md) — CSC GPU environment probe
- [week6-supervisor-plan.md](week6/archive/week6-supervisor-plan.md) — supervisor-response operational plan
- [week6_supervisor_response.md](experiment_logs/week6_supervisor_response.md) — supervisor-response evidence log
- [week6_pareto_precision_sweep_plan.md](experiment_logs/week6_pareto_precision_sweep_plan.md) — Pareto precision sweep extension plan

Week 7 deliverables:
- [week6_to_week7_bridge.md](week7/week6_to_week7_bridge.md) — Week 6 → Week 7 handoff (completed GPU baseline, reusable interfaces, Week 7 experiment guidance)
- [week7-plan.md](week7/week7-plan.md) — operational plan for supervisor-response evidence collection
- [week7_supervisor_response.md](experiment_logs/week7_supervisor_response.md) — supervisor-response evidence log
- [report1_evidence_map.md](experiment_logs/report1_evidence_map.md) — canonical Report 1 evidence map after Week 8/9 fill and final cleanup

Report 1 closeout / Report 2 transition:
- Report 1 is complete. Use [report1_evidence_map.md](experiment_logs/report1_evidence_map.md) as the current source of truth for Report 1 evidence priority and exclusions.
- Report 2 code work should start from [requirement/overall.md](requirement/overall.md) Phase 2, preserving the harness flow in [HARNESS.md](HARNESS.md).
- Week 12 delivers the 1D MHD walking skeleton for Report 2: additive 9-variable ideal-MHD state/flux/HLL/solver code, a cfg-driven `hrsc_mhd` executable, Brio-Wu validation, and a `divB` sentinel while leaving Report-1 Euler numerics untouched.

---

## 3. Code structure quick-reference

```
src/
├── app/            # cases registry; cfg parsing/validation; diagnostics;
│                   # output/checkpoint helpers for the hrsc executable
├── cases/          # production case IC definitions; tests/cases keeps
│                   # compatibility wrappers plus cfg files
├── core/           # types.hpp (TimeReal=double, NgHost), grid.hpp, vec.hpp,
│                   # eos.hpp, boundary.hpp (Outflow/Periodic/Reflective per-axis)
├── euler/          # euler_solver.{hpp,cpp} (split for explicit instantiation)
│                   # hllc.hpp, rusanov.hpp, muscl.hpp, hancock.hpp,
│                   # euler_flux.hpp, exact_riemann.hpp
├── gpu/            # opt-in CUDA Euler path: euler_gpu_solver.{hpp,cu},
│                   # euler_kernels.{cuh,cu}, gpu_grid/cuda utilities
├── utils/          # io.hpp (binary reader/writer; auto-creates parent dir),
│                   # config.hpp (key=value parser)
└── main.cpp        # cfg-driven executable entry; run dispatch and formatted
                    # output, with precision via HRSC_REAL from CMake

tests/
├── unit/           # Catch2 CPU default suite (136 cases / 12105 assertions)
│                   # test_boundary.cpp (10 cases / 572 assertions covers
│                   # outflow/periodic/reflective × 1D/2D/dispatcher/MHD-shape)
│                   # Week 6 adds opt-in [gpu] coverage when ENABLE_CUDA=ON
├── cases/
│   ├── toro_1d/    # cfgs plus wrapper to src/cases/euler/toro_tests.hpp
│   │               # convergence_*.cfg drive resolutions = 50,100,200,400,800
│   └── liska_wendroff_2d/  # cfgs plus wrapper to src/cases/euler/lw_tests.hpp
└── py/             # Python-level tests (pytest): test_ssim_scalar, test_snr_*,
                    # test_losos_*, test_s_req_*, test_plot_divergence_marker
```

Script harness:

```
scripts/
├── run_matrix.py, build_all.sh, build_matrix.py, aggregate_metrics.py, io_helper.py
│   # canonical build/run/read/aggregate entry points
├── metrics/        # reusable metric computations
├── regression/     # validation and summary reports; prefer matrix_summary_report.py
├── verificarlo/    # Verificarlo/MCA/precexp workflows
├── figures/        # reusable plotters plus Report 1 figure provenance
├── diagnostics/    # one-off investigations and evidence checks
└── cluster/        # CSC/Lovelace/SLURM helpers; read cluster/README.md first
```

For Report 2, start from `scripts/README.md` and prefer canonical harness
entry points over Report 1 provenance scripts.

---

## 4. Build matrix

| Build dir | `FLOAT_PRECISION` | Use |
|---|---|---|
| `build-double/` | double | Phase B canonical, baseline reference for Phase C |
| `build-float/` | float | Phase B canonical, float regression candidate |
| `build-cuda-*-strict/` | double/float | Week 6 opt-in CUDA strict-IEEE verification |
| `build-vfc-p53/` | double | Verificarlo MCA p=53 (auto-recreated by `scripts/verificarlo/verificarlo_run.sh`) |

All build dirs are `.gitignore`'d and can be deleted/recreated. Keep only the
build directories needed for the current verification task. Build via:
```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double
```

### Local Windows toolchain notes

On this workstation, a bare PowerShell may not expose the real C++ compiler or
Python. Check these local installations before concluding the environment is
missing:

- Visual Studio Build Tools root:
  `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`
- MSVC compiler observed:
  `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\cl.exe`
  (`cl` version `19.51.36248`).
- Miniconda Python:
  `C:\Users\tangy\miniconda3\python.exe` (`Python 3.13.13`).

To verify or build with MSVC from `cmd.exe`, first load the developer
environment:

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
where cl
cl /Bv
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-double
```

`c++` is not expected to be the compiler name in this MSVC setup; use the
developer environment so CMake can discover `cl`. For Python scripts, prefer the
full Miniconda path or set `PYTHON` explicitly:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" --version
$env:PYTHON = "C:\Users\tangy\miniconda3\python.exe"
```

---

## 5. Common-task cheatsheet

| Task | Command |
|---|---|
| Build both precisions | `cmake -B build-double -G Ninja -DFLOAT_PRECISION=double && cmake --build build-double && cmake -B build-float -G Ninja -DFLOAT_PRECISION=float && cmake --build build-float` |
| Build full CPU FP matrix | `bash scripts/build_all.sh` |
| Run all unit tests | `./build-double/unit_tests -r compact && ./build-float/unit_tests -r compact` |
| Run Sod 1D | `./build-double/hrsc tests/cases/toro_1d/sod.cfg` |
| 1D float regression (6 Toro cases × 2 precisions × 5 N) | `bash scripts/regression/float_regression_1d.sh` |
| 2D LW Config 3 float regression (n200/n400 + 1600² ref when available) | `bash scripts/regression/float_regression_2d.sh` |
| Verificarlo MCA noise floor | `bash scripts/verificarlo/verificarlo_run.sh -t sod -n 30` |
| Verificarlo real-float vs VPREC | `bash scripts/verificarlo/verificarlo_run.sh --compare-float -t "sod stationary_contact"` |

For the full step-by-step manual recipe see [week4/week4-verification.md](week4/week4-verification.md).

---

## 6. Data products map

| Where to find | What's there |
|---|---|
| `docs/experiment_logs/report1_evidence_map.md` | Canonical Report 1 evidence routing: P0/P1/P2/P3 artefacts, superseded results, exclusions, and current strongest claims |
| `experiments/week4/float_regression/1d/` | Phase C1 1D: 12 CSVs (sod, toro2-5, stationary_contact × {double, float}) + summary.{md,json} |
| `experiments/week4/float_regression/2d/` | Phase C1 2D: 4 candidates + 16 difference heatmaps + summary.{md,json}; current rerun uses the Week 7 1600² reference when available |
| `experiments/week8/report1_2d_config12_fill/` | Second 2D Euler Riemann evidence packet (LW12/config12): strict CPU/GPU, fp32/fp64, N=800 reference comparison, figures |
| `experiments/week9/cpu_gpu_midtime*/` | Checkpointed strict-HLLC CPU/GPU saved-output evidence for Sod, LW3, and LW12 |
| `experiments/report1/evidence/cpu_gpu_zero_drift_audit/` | Consolidated saved-output CPU/GPU zero-drift audit plus strict-vs-fast counterexamples |
| `experiments/report1/evidence/fp32_fp64_time_drift/` | CPU HLLC fp64-vs-fp32 saved-checkpoint drift evidence |
| `experiments/week4/figures/a4_pareto/` | A4 σ_FP × s_worst Pareto figure (`pareto_lw_config3_200.png`) |
| `experiments/week4/figures/a4_float_p24/` | A4 p24-real-float Athena heatmaps (σ_FP, LoSoS reliability/accuracy/worst) |
| `experiments/week4/metrics/` | A4 metrics: p53 LoSoS/s_req, p24-real-float SNR/LoSoS, merged CSVs for the four-row headline table |
| `experiments/week4/figures/deterministic_2d/` | A1 deterministic 2D plots (HLLC vs Rusanov density/pressure diff maps) |
| `experiments/verificarlo/runs_p53_mca[*]/` | A2 / A4 MCA samples (cross-week, 1D Toro × 30 samples × p53) |
| `experiments/verificarlo/runs_compare_p24_mca_real_vs_double*/` | C2 real-float vs p24-surrogate compare runs (baseline / fma / rusanov) |
| `experiments/week4/2d_vfc_cluster/` | A3 cluster outputs (200²×30 samples, LW Config 3) |

C2 main result log: [experiment_logs/c2_real_float_vs_vprec.md](experiment_logs/c2_real_float_vs_vprec.md).

---

## 7. Common pitfalls (from the 2026-04-28 review)

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot open file for writing: experiments/.../output.bin` | Old binary; cfg points at nested path with no `mkdir -p` | Rebuild — current `src/utils/io.hpp` auto-creates parent dirs |
| `bash scripts/foo.sh: python: command not found` | Microsoft Store Python stub on PATH (no real interpreter) | Set `PYTHON=/c/Users/tangy/miniconda3/python.exe` or rely on the script's `resolve_python` (skips WindowsApps) |
| CMake says `No CMAKE_CXX_COMPILER could be found` | Plain PowerShell has not loaded VS BuildTools paths | Run through `VsDevCmd.bat` from `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\` so CMake can find `cl` |
| Bash redirect `./build-double/hrsc.exe ... > out.csv` produces 0 bytes | MSYS pipe handle quirk under PowerShell-spawned bash | Drive long pipelines from PowerShell directly (works); native Linux/WSL also works |
| `unit_tests` boundary cases fail | Build out-of-date after BC changes | `cmake --build build-{double,float}` |

---

## 8. Active Plan files (planning-with-files-zh)

When a structured reorganization or multi-step task is in progress, three files live at repo root:

- `task_plan.md` — phase tracking, decisions, statuses
- `findings.md` — research/discovery notes
- `progress.md` — session log + commits

**These are workspace files, not project artefacts** — they may exist mid-task and disappear when complete. Do not link from permanent docs.

---

## 9. Skills hint

- For complex multi-step refactors: invoke `planning-with-files:planning-with-files-zh` (or `-zht` / English variant).
- For TDD or feature-by-feature work: `superpowers:test-driven-development` + `superpowers:subagent-driven-development`.
- Before running ultrareview: `/ultrareview <PR#>` — user-triggered, billed.

---

*Last updated: 2026-06-25 (added local Windows VS BuildTools + Miniconda notes for reproducible verification).*
