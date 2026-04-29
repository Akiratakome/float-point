# Project Index — `floatpoint`

> Agent-facing entry point. **Read this first** before exploring; it points to the canonical doc/data for every concern.

**Project**: Effect of Floating-Point Precision and Hardware on HRSC Schemes (MSc, 20 weeks)
**Reports**: Report 1 due 2026-05-29 (Week 10) · Report 2 due 2026-08-07 (Week 20)
**Repo root**: `c:/Users/tangy/Desktop/floatpoint`
**Default branch**: `main` · **Active dev branch**: `week4-implementation`

---

## 1. Where to look — by concern

| If you need… | Read |
|---|---|
| Project requirements, deliverables, deadlines | [requirement/overall.md](requirement/overall.md) |
| Coding conventions, style, FP guidance | [requirement/coding guidance.md](requirement/coding%20guidance.md) |
| Project briefs (PDFs from supervisor) | [requirement/](requirement/) (`*.pdf`) |
| What's been done so far this project | per-week `weekN-summary.md` (see §2) |
| What's planned this week | per-week `weekN-plan.md` (see §2) |
| Supervisor correspondence | [emails/](emails/) (named `weekN_<topic>_YYYY-MM-DD.md`) |
| Raw experiment data logs (deliverable artefacts) | [experiment_logs/](experiment_logs/) (named `weekN_<phase>_<topic>.md`) |
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

Week 4 also keeps:
- [week4-verification.md](week4/week4-verification.md) — manual verification checklist (Phase B/C reproduction recipe)
- [week3_to_week4_bridge.md](week4/week3_to_week4_bridge.md) — Week 3 → Week 4 state migration

---

## 3. Code structure quick-reference

```
src/
├── core/           # types.hpp (TimeReal=double, NgHost), grid.hpp, vec.hpp,
│                   # eos.hpp, boundary.hpp (Outflow/Periodic/Reflective per-axis)
├── euler/          # euler_solver.{hpp,cpp} (split for explicit instantiation)
│                   # hllc.hpp, rusanov.hpp, muscl.hpp, hancock.hpp,
│                   # euler_flux.hpp, exact_riemann.hpp
├── utils/          # io.hpp (binary reader/writer; auto-creates parent dir),
│                   # config.hpp (key=value parser)
└── main.cpp        # cfg-driven entry; selects test, solver, BCs, precision
                    # via HRSC_REAL macro from cmake/PrecisionConfig.cmake

tests/
├── unit/           # Catch2 (115 cases / 3660 assertions)
│                   # test_boundary.cpp (10 cases / 572 assertions covers
│                   # outflow/periodic/reflective × 1D/2D/dispatcher/MHD-shape)
├── cases/
│   ├── toro_1d/    # sod, toro2-5, stationary_contact (+ rusanov twins)
│   │               # convergence_*.cfg drive resolutions = 50,100,200,400,800
│   └── liska_wendroff_2d/  # config3_n200, config3_n400, config3_ref800
└── py/             # Python-level tests (pytest): test_ssim_scalar, test_snr_*,
                    # test_losos_*, test_s_req_*, test_plot_divergence_marker
```

---

## 4. Build matrix

| Build dir | `FLOAT_PRECISION` | Use |
|---|---|---|
| `build-double/` | double | Phase B canonical, baseline reference for Phase C |
| `build-float/` | float | Phase B canonical, float regression candidate |
| `build-vfc-p53/` | double | Verificarlo MCA p=53 (auto-recreated by `scripts/verificarlo/verificarlo_run.sh`) |

All build dirs are `.gitignore`'d. Build via:
```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double
```

---

## 5. Common-task cheatsheet

| Task | Command |
|---|---|
| Build both precisions | `cmake -B build-double -G Ninja -DFLOAT_PRECISION=double && cmake --build build-double && cmake -B build-float -G Ninja -DFLOAT_PRECISION=float && cmake --build build-float` |
| Run all unit tests | `./build-double/unit_tests -r compact && ./build-float/unit_tests -r compact` |
| Run Sod 1D | `./build-double/hrsc tests/cases/toro_1d/sod.cfg` |
| 1D float regression (6 Toro cases × 2 precisions × 5 N) | `bash scripts/regression/float_regression_1d.sh` |
| 2D LW Config 3 float regression (n200/n400 + 800² ref) | `bash scripts/regression/float_regression_2d.sh` |
| Verificarlo MCA noise floor | `bash scripts/verificarlo/verificarlo_run.sh -t sod -n 30` |
| Verificarlo real-float vs VPREC | `bash scripts/verificarlo/verificarlo_run.sh --compare-float -t "sod stationary_contact"` |

For the full step-by-step manual recipe see [week4/week4-verification.md](week4/week4-verification.md).

---

## 6. Data products map

| Where to find | What's there |
|---|---|
| `experiments/week4/float_regression/1d/` | Phase C1 1D: 12 CSVs (sod, toro2-5, stationary_contact × {double, float}) + summary.{md,json} |
| `experiments/week4/float_regression/2d/` | Phase C1 2D: reference_800.bin + 4 candidates + 16 difference heatmaps + summary.{md,json} |
| `experiments/week4/figures/a4_pareto/` | A4 σ_FP × s_worst Pareto figure (`pareto_lw_config3_200.png`) |
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
| `bash scripts/foo.sh: python: command not found` | Microsoft Store Python stub on PATH (no real interpreter) | Set `PYTHON=/c/Users/.../anaconda3/python.exe` or rely on the script's `resolve_python` (skips WindowsApps) |
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

*Last updated: 2026-04-28 (post-Week-4 reorganization).*
