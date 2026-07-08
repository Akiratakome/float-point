# Week 15 — Solver-Aware Orszag-Tang 2D Precision Smoke Design

**Date:** 2026-07-08
**Branch base:** `week12-mhd-implementation` (Week 14 P0 pilot complete; HLLD div(B) blocker closed 2026-07-06)
**Requirement:** [overall.md](../../requirement/overall.md) §Phase 2 — systematic precision study must cover MHD in 1D **and** 2D; Report 2 "Computational Results" (40%) is the target evidence. Report 2 due 2026-08-07; per the writing-buffer policy, data collection ends ~07/19, so Week 15 and Week 16 are the last two data weeks.
**Harness contract:** [HARNESS.md](../../HARNESS.md) — `config → build → run → measure → aggregate → plot`; per-run generated cfg + stdout/stderr + metadata + summary; transient grids; no committed build dirs.
**Decisions carried forward:** the 2026-07-06 follow-up ([summary](../../../experiments/week13/hlld_divb_followup/summary.md)) closed the Week-13 deferred-HLLD blocker — the alarming divB_max was a stale-binary artifact and the corrected HLLD-vs-HLL gap is bounded, convergent-in-mean, resolution-consistent truncation at under-resolved current sheets. **HLL stays the production default**; Week 15 adopts HLLD as a *studied axis* (dual-solver), not as the default.
**Supersedes:** [2026-07-02-week15-ot-2d-precision-smoke plan](../plans/2026-07-02-week15-ot-2d-precision-smoke.md) (written pre-HLLD-clearance; HLL-only; its sampler task conflicts with the in-flight `--solver` work).

---

## 1. Goal & scope boundary

Point the Week-14 Brio-Wu precision-pilot methodology at the first 2D MHD
case. Deliverable: a claim-bounded, gated Orszag-Tang 2D evidence packet —
deterministic build-axis fan **per solver** plus Verificarlo MCA — proving the
2D leg of the Report-2 precision study on CPU before any GPU/KH/cluster work.

### In scope (Week 15)

- **Orszag-Tang 2D only, CPU only.**
- Deterministic P0 fan `{double,float} × {O2,Ofast} × ieee × {leq,strict}`
  (8 variants), run **once per solver** (`hll`, `hlld` via the runtime
  `riemann` cfg key), each row measured against the **same-solver**
  `cpu-double-O2-ieee-leq` reference.
- Two deterministic profiles per solver:
  - **gate** — 128², `t_end=0.1`: seconds per run, fast iteration/debugging.
  - **headline** — 256², `t_end=0.5`: report-grade, same scale as the Week-13
    benchmark figures and the MK2005 comparison, drift fully developed.
- Docker Verificarlo MCA per solver: `p53` + `p24`, **n=3 samples** each, on a
  dedicated 64² / `t_end=0.05` cfg, experiment label `week15-mhd-mca`.
- Landing the in-flight working-tree changes first (prerequisite, §3).

### Out of scope (stated so the plan cannot quietly grow)

GPU MHD; Kelvin-Helmholtz; 512² convergence runs; Lyapunov/temporal-divergence
fitting (Week 16); cluster runs; changing the production solver default;
MCA sample depth beyond n=3 (magnitude-level claims only).

### Unchanged surface (hard constraint)

`src/mhd/*` numerics, every **existing** cfg file, the `io.hpp` output format,
`build_all.sh`, the Euler path, and all committed Week-12/13/14 evidence.
Adding one new cfg file (`orszag_tang_mca64.cfg`, §4) is explicitly allowed.

---

## 2. Verified preconditions (facts this design relies on)

| Fact | Evidence |
|---|---|
| HLLD is numerically cleared: bounded-in-time divB, mean-convergent, `divB_max·dx ≈ const`; 5-wave fan audited term-by-term vs Miyoshi & Kusano (2005); `RIEMANN_STRICT_INEQUALITY` now covers HLLD interior tie ownership (SsL/SsR/SM). | [hlld_divb_followup/summary.md](../../../experiments/week13/hlld_divb_followup/summary.md), commits `8b91e51`, `06f2079` |
| OT anchors exist at both profiles (double build, cfl=0.4, glm_cr=0.18): 128²/t=0.1 → `steps=76`, `divB_max` 1.173 (HLL) / 1.085 (HLLD); 256²/t=0.5 → `steps=806/812`, `divB_max` 3.72 / 24.45. | follow-up summary, Findings 1–2 tables |
| The working tree (uncommitted, 73 tests green on 2026-07-08) already threads `--solver hll\|hlld` through `mhd_precision_pilot.py`, `mhd_precision_pilot_core.py` (HLLD anchor `steps=761, divB_max=0.0`), `mhd_precision_sampling.py`, and `mhd_verificarlo_smoke.py`; the HLLD Brio-Wu pilot evidence is already generated (G0 pass, MCA p53/p24 completed, n=8, docker). | `git status` / `git diff HEAD`; [experiments/week14/mhd_precision_pilot_hlld/summary.md](../../../experiments/week14/mhd_precision_pilot_hlld/summary.md) |
| `mhd_verificarlo_smoke.py` already accepts `--case` and `--solver`; only the sampler wrapper hardcodes `case=DEFAULT_CASE` (Brio-Wu) and the `week14-mhd-mca` label. | [scripts/verificarlo/mhd_precision_sampling.py](../../../scripts/verificarlo/mhd_precision_sampling.py) `_sample_args` |
| Reusable pilot machinery: `build_variant()` (clean cmake configure+build per variant into `build-matrix/<name>/`), `select_variants("p0")` (the 8-variant fan), `ordered_variants_reference_first()`, `REFERENCE = "cpu-double-O2-ieee-leq"`. | [scripts/regression/mhd_precision_pilot.py](../../../scripts/regression/mhd_precision_pilot.py), `mhd_precision_pilot_core.py` |
| Shared measurement layer is shape-agnostic (works for 2D): `field_norms` / `mhd_primitive_fields` (rho, By, p, vx), `point_symmetry_residual`, `read_binary` returns `(GridHeader{nx,ny,dx,dy,…}, data[ny,nx,nvars])`, numpy-only `plot_heatmap_panels` (supports `log10` panels). | `scripts/metrics/mhd_fields.py`, `scripts/regression/_mhd_harness.py`, `scripts/io_helper.py`, `scripts/regression/mhd_paper_figures.py` |
| Stale-binary pitfall: ninja/MSVC header-dep tracking can silently break on this zh-CN workstation; evidence builds must come from freshly configured build dirs. | [docs/INDEX.md](../../INDEX.md) §7 |
| Docker Verificarlo works on this machine; the most recent completed MCA evidence (2026-07-06 HLLD pilot) used image `verificarlo/verificarlo:cmake` (`floatpoint-verificarlo-cmake:week14` is the earlier Week-14 image). | `experiments/week14/mhd_precision_pilot*/mca/p53/environment.json` |

---

## 3. Prerequisite: land the in-flight work first

The new driver imports the in-flight solver-axis interfaces, so the working
tree must be committed before feature work starts — in reviewable slices, not
one blob:

1. Solver axis: pilot + core + pilot plots + sampler + smoke + their 5 test files.
2. HLLD Brio-Wu pilot evidence (`git add -f`, no `.bin`) + the Week-13 summary decision-update hunk.
3. MK2005 paper-style renderer + OT/KH driver tweaks + regression README + refreshed Week-13 figure PNGs.
4. Resolution-ladder log-axis fix + its test + refreshed figure.
5. Outstanding Week-13/14 docs (meeting notes, prompts, Week-14 spec/plan).

The superseded 2026-07-02 Week-15 plan gets a banner; the 2026-07-08 draft
plan (uncommitted) is rewritten by the implementation plan produced from this
spec.

---

## 4. Architecture & components

### 4.1 New driver — `scripts/regression/mhd_orszag_tang_precision_smoke.py`

One clear responsibility: orchestrate the OT deterministic fan for one
`(solver, profile)` pair and write a gated, claim-bounded summary. Chosen over
generalizing `mhd_precision_pilot.py` (touching the Week-14 evidence
generator risks regressions; 1D/2D gate differences would bloat its core) and
over the generic `run_matrix.py` (which has no anchor gate, no same-solver
reference measurement, no claim buckets).

- **CLI:** `--solver {hll,hlld}` × `--profile {gate,headline}`,
  `--out` (default derived), `--keep-grids`. No free-form grid overrides —
  profiles are the only sanctioned configurations (YAGNI; ad-hoc debugging
  edits the profile constants locally).
- **Profiles:** `gate` = 128², t_end=0.1; `headline` = 256², t_end=0.5. Both
  override `tests/cases/orszag_tang_2d/orszag_tang.cfg` in-memory
  (`nx`, `ny`, `t_end`, `riemann`, output keys) via `replace_or_append_cfg`.
- **Anchors keyed by (solver, profile)** (from §2): reference row must match
  `steps` exactly and `divB_max` within **5 % rtol**.
- **Reuse:** `select_variants("p0")` + `ordered_variants_reference_first` +
  `build_variant` for builds; `run_case` for execution/metadata;
  `read_binary` + `field_norms` + `point_symmetry_residual` for measurement;
  `plot_heatmap_panels` for figures. Builder/runner/reader are injectable
  parameters for unit tests.
- **Measurement per row:** `L1/L2/Linf` of `rho, By, p, vx` vs the
  same-solver reference, `steps`, `divB_mean`, `divB_max`, `walltime_s`,
  `finite`, `symmetry_residual_rho`, `is_reference`.
- **Figures per packet:** density+pressure heatmap of the reference; log10
  |drift| maps (rho, By) of `cpu-float-O2-ieee-leq` vs the reference.
- **Exit code:** 0 only if the G0 anchor gate passes.

### 4.2 Sampler passthrough — `scripts/verificarlo/mhd_precision_sampling.py`

Minimal generalization on top of the in-flight `--solver`:
`sample_precision(..., case=DEFAULT_CASE, experiment=WEEK14_MCA_EXPERIMENT)`
plus CLI `--case` / `--experiment`. Week-14 defaults unchanged (existing
callers and tests stay green).

### 4.3 New cfg — `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg`

Same physics as `orszag_tang.cfg` but 64² / `t_end=0.05`, because the
deterministic OT cfg (256², t=0.5) is far too expensive under Verificarlo
instrumentation. The deterministic runs do **not** use this file.

---

## 5. Data flow & experiment directory layout

```
experiments/week15/orszag_tang_precision_smoke/        # HLL
├── gate128/      runs/<variant>/{config.cfg,stdout,stderr,metadata.json}  (grid.bin TRANSIENT)
│                 summary.{json,csv,md} + figures/
├── headline256/  same layout
└── mca/          p53/ p24/ (runs, environment.json) + summary.json        # n=3, 64² cfg
experiments/week15/orszag_tang_precision_smoke_hlld/   # HLLD, same layout
```

Run order per solver: gate first (fail fast), then headline, then MCA.
Before any evidence run, delete the 8 P0 `build-matrix` dirs so
`build_variant()` reconfigures from clean (stale-binary pitfall, INDEX §7);
all builds happen from a VS-dev-environment console. Grids are deleted after
measurement unless `--keep-grids`; evidence is committed with `git add -f`
(`experiments/` is gitignored); `.bin` files are never committed.

---

## 6. Gates, claim buckets, success criteria

**G0 (hard, per packet):** every row finite **and** the reference row
reproduces its (solver, profile) anchor — `steps` exact, `divB_max` within
5 % rtol. On failure: exit 1, investigate (fresh build? cfg drift vs the
follow-up?), **never widen the tolerance**.

**Claim buckets:**

- *morphology / engineering consistency* — deltas are against the same-solver
  fp64 reference, not an exact solution.
- *precision axis* — fp32 rows are expected orders of magnitude above fp64
  rows (Brio-Wu: ~1e-6 vs ~1e-15); report per profile.
- *implementation axis* — `leq` vs `strict` deltas, reported explicitly per
  solver. On Brio-Wu this axis was identically zero; `8b91e51` made it real
  for HLLD interior ties, so **any nonzero 2D result is new, report-worthy
  signal** (and a zero result is a legitimate negative finding).
- *precision noise (MCA)* — magnitude-level only at n=3: `p24` spread should
  sit ~2⁻²⁴-like above `p53`, mirroring Week 14. `blocked_environment` is a
  valid recorded outcome, but the packet is not supervisor-ready without a
  Docker rerun.

**Success criteria:** 4 deterministic packets (2 solvers × 2 profiles) with
G0 pass; 2 MCA blocks `completed` (n=3 each precision); leq/strict deltas
measured and reported; evidence committed; regression README + INDEX §6
registered; 2026-07-02 plan bannered as superseded; full `tests/py` suite
green. Estimated wall time: builds ~15 min + deterministic ~30–50 min + MCA
~0.5–1 h.

---

## 7. Error handling

| Failure | Behavior |
|---|---|
| Anchor gate fails | Driver exits 1; stop, investigate build freshness / cfg drift; do not loosen `divB` rtol or steps equality. |
| A variant run returns nonzero / missing grid | `run_case` raises with the stderr path (existing behavior); packet aborts — no partial summaries. |
| Non-finite fields in any row | Row recorded `finite=false`, norms zeroed; G0 fails (finite is part of the gate). |
| Docker unavailable for MCA | Sampler records `blocked_environment` (valid, non-failing); summary notes the packet is not supervisor-ready. |
| Stale binaries | Prevented structurally: build-matrix dirs deleted before evidence runs; `build_variant` reconfigures from clean. |

---

## 8. Testing strategy

TDD throughout. Unit tests (no real builds, no subprocesses) with injected
fakes for builder/runner/reader cover: plan generation (8 variants, reference
first, solver/profile stamping, invalid solver rejected); cfg override
hygiene (only harness keys touched); measurement schema and norm values on
synthetic grids; anchor-gate pass/fail per (solver, profile); JSON-safe
summary serialization (numpy scalars, `allow_nan=False`); figure files
non-empty; grid deletion vs `--keep-grids`; sampler case/experiment
passthrough (existing Week-14 sampler tests must stay green — new params all
default). Evidence-run verification is command-level (summary gate check +
`.bin` hygiene sweep + full pytest), not unit-tested.

---

## 9. Docs registration

- Banner on `docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md` (superseded, do not execute).
- `scripts/regression/README.md`: register the new driver under "Report 2 MHD Validation".
- `docs/INDEX.md` §6: add the `experiments/week15/orszag_tang_precision_smoke[_hlld]/` data-products row.
- Final report to the supervisor lists deferred candidates for Week 16: KH 2D packet, 512² convergence gate, GPU MHD, temporal divergence/Lyapunov.
