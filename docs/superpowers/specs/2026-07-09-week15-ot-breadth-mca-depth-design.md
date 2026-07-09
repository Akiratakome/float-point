# Week 15 — Orszag-Tang 2D Breadth (P1) + MCA-Depth (N≈30) Scale-Up Design

**Date:** 2026-07-09
**Branch base:** `week12-mhd-implementation` (solver-aware OT precision smoke landed: `db4f88b`, `8d0a81a`)
**Requirement:** [overall.md](../../requirement/overall.md) §Week 15 — "Systematic Precision Study - Primary Axes", full opt×fastmath fan; Report 2 "Computational Results" (40%). Report 2 due 2026-08-07; data collection ends ~07/19.
**Harness contract:** [HARNESS.md](../../HARNESS.md) — `config → build → run → measure → aggregate → plot`.
**Decisions carried forward:** [2026-07-08-week15-ot-2d-precision-design.md](2026-07-08-week15-ot-2d-precision-design.md) — dual-solver (HLL/HLLD) OT 2D pilot at P0 scale (8 variants, gate128 + headline256, MCA n=3) is done and G0-passing. This spec scales the **same** packets to the Week-14-defined P1 (24-variant breadth) and P2 (N≈30 MCA depth) tiers — the tiers were designed in [2026-07-01-week14-mhd-plan-design.md](2026-07-01-week14-mhd-plan-design.md) §3 but never executed at any scale, 1D or 2D.

**Sub-project scope note:** this is sub-project 1 of a 4-item Week-15/16 plan the user approved (order: OT breadth+depth → GPU MHD → KH 2D matrix → GPU MHD precision packets). This spec covers only sub-project 1.

---

## 1. Goal & scope boundary

Turn the existing OT 2D P0 pilot packets into report-grade evidence by running the deterministic fan at full breadth (adds `O3` and `fastmath=True`, 8→24 variants) and the MCA sampler at statistically stable depth (`n=3`→`n=30`), for **both** solvers, on the **headline256** profile only.

### In scope

- Extend `mhd_orszag_tang_precision_smoke.py` so its deterministic plan/runner can select the Week-14-defined `"p1"` variant set (already implemented in `mhd_precision_pilot.select_variants`) instead of hardcoding `"p0"`.
- Run 24-variant deterministic breadth on `headline256` (256², t=0.5) for `hll` and `hlld`, written to a **new** subdir so the existing 8-variant `headline256` P0 evidence is preserved unchanged.
- Add a soft, non-blocking ordering-flag report (fastmath vs ieee) to the breadth summary, reusing `mhd_precision_pilot_core.ordering_flags` — no new metric code needed, the OT row schema already carries the required keys (`precision`, `opt`, `fastmath`, `riemann`, `Linf_rho`).
- Run the MCA sampler (`mhd_precision_sampling.py`, already CLI-complete for `--samples`/`--solver`/`--case`) at `--samples 30` for both solvers against the existing `orszag_tang_mca64.cfg`, written to a new `mca_n30/` subdir alongside the existing `mca/` (n=3) evidence.

### Out of scope

- `gate128` profile (stays P0-only; it exists for fast iteration, not report evidence).
- Any GPU, Kelvin-Helmholtz, 512² convergence, or Lyapunov work (separate sub-projects/weeks).
- Changing anchors, solver numerics, or existing cfg defaults.

### Unchanged surface (hard constraint)

`src/mhd/*` numerics, `tests/cases/orszag_tang_2d/orszag_tang.cfg` and `orszag_tang_mca64.cfg`, the existing `gate128` and `headline256` (P0) evidence directories, `io.hpp` output format, `build_all.sh`.

---

## 2. Verified preconditions (facts this design relies on)

| Fact | Evidence |
|---|---|
| `select_variants("p1")` already returns the full unfiltered 24-variant set (`generate_variants()`); `select_variants("p0")` returns the 8-variant fan. Both exist today. | [scripts/regression/mhd_precision_pilot.py:64-70](../../../scripts/regression/mhd_precision_pilot.py#L64-L70) |
| `mhd_orszag_tang_precision_smoke.deterministic_plan()` and `run_deterministic()` both hardcode `select_variants("p0")` — this is the only place P1 needs threading through. | [scripts/regression/mhd_orszag_tang_precision_smoke.py:149-154,472](../../../scripts/regression/mhd_orszag_tang_precision_smoke.py#L149) |
| `mhd_precision_pilot_core.ordering_flags(rows)` is solver/case-agnostic — it only reads `variant, precision, opt, riemann, fastmath, Linf_rho` from each row dict, all of which `measure_pair()` already populates for OT rows. | [scripts/regression/mhd_precision_pilot_core.py](../../../scripts/regression/mhd_precision_pilot_core.py) |
| `mhd_precision_sampling.py` CLI already accepts `--samples`, `--solver {hll,hlld}`, `--case`, `--experiment`, and `resolve_output_dir` already solver-suffixes the default output path. No sampler code change is needed for N=30. | [scripts/verificarlo/mhd_precision_sampling.py](../../../scripts/verificarlo/mhd_precision_sampling.py) (`parse_args`, `main`) |
| OT anchors are already defined for both solvers at both profiles (`OT_ANCHORS` dict, `headline`: `hll`→(806, 3.72), `hlld`→(812, 24.45)); breadth rows reuse the same anchor since profile/solver are unchanged, only the variant axis grows. | [scripts/regression/mhd_orszag_tang_precision_smoke.py:26-31](../../../scripts/regression/mhd_orszag_tang_precision_smoke.py#L26) |
| Existing headline256 8-variant deterministic run wall-time is ~22-28s/variant; 24 variants ≈ 4x the execution time of the existing P0 packet, plus 16 additional clean build cycles (stale-binary pitfall requires fresh `build_variant()` configures). | [experiments/week15/orszag_tang_precision_smoke/headline256/summary.md](../../../experiments/week15/orszag_tang_precision_smoke/headline256/summary.md) |
| Existing MCA n=3 packets (both solvers) are `completed` via Docker runner on `orszag_tang_mca64.cfg` (64², t=0.05); N=30 is a 10x sample-count increase on the same cfg/runner path, no new environment risk. | [experiments/week15/orszag_tang_precision_smoke/mca/summary.json](../../../experiments/week15/orszag_tang_precision_smoke/mca/summary.json) |

---

## 3. Architecture & components

### 3.1 `mhd_orszag_tang_precision_smoke.py` — thread a `variant_set` parameter

- `deterministic_plan(solver="hll", profile="gate", variant_set="p0")` — passes `variant_set` to `select_variants(variant_set)` instead of the hardcoded `"p0"` literal. Default unchanged so existing P0 callers/tests are untouched.
- `run_deterministic(..., variant_set="p0", ...)` — same threading; `variants=None` path now calls `select_variants(variant_set)` instead of the hardcoded `select_variants("p0")`.
- `resolve_output_dir` / packet path: add a breadth-specific subdir suffix so P1 evidence never collides with P0. Concretely, `main()` computes the packet dir as `resolve_output_dir(args.out, args.solver) / PROFILES[profile]["subdir"]` today; for `--phase p1` it becomes `.../headline256_p1/`. `gate128_p1` is never produced (gate stays P0-only per scope).
- `write_outputs()` gains a soft `gates.G1` block: `{"ordering_flags": mhd_precision_pilot_core.ordering_flags(rows)}`, populated only when `variant_set == "p1"` (P0 has no fastmath axis, so it would always be empty there — omit rather than emit a trivially-empty block).
- CLI: `parse_args()` adds `--phase {p0,p1}` (default `p0`, matching the existing `mhd_precision_pilot.py` convention already used for Brio-Wu). `main()` passes it through and selects the packet subdir accordingly.

### 3.2 MCA sampler — no code change

Invoked twice (hll, hlld) with `--samples 30 --case tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg --out experiments/week15/orszag_tang_precision_smoke[_hlld]/mca_n30`. The existing `mca/` (n=3) directories are left in place for provenance/comparison (smoke-vs-depth).

### 3.3 Evidence directory layout (additive only)

```
experiments/week15/orszag_tang_precision_smoke/        # HLL (existing, untouched)
├── gate128/                                            # P0, unchanged
├── headline256/                                        # P0, unchanged
├── headline256_p1/          # NEW: 24-variant breadth, same anchor as headline256
│   runs/<variant>/{config.cfg,stdout,stderr,metadata.json}  (grid.bin TRANSIENT)
│   summary.{json,csv,md} + figures/ + gates.G1.ordering_flags
├── mca/                                                # n=3, unchanged
└── mca_n30/                                            # NEW: n=30 per precision
experiments/week15/orszag_tang_precision_smoke_hlld/    # HLLD, same additive layout
```

---

## 4. Gates, claim buckets, success criteria

**G0 (hard, unchanged mechanism):** every row finite, reference row reproduces the existing (solver, headline) anchor exactly on `steps`, within 5% rtol on `divB_max`. Applies identically at 24-variant scale — more variants does not relax the gate.

**G1 (soft, new for this packet):** `ordering_flags` across the O2/O3/Ofast × ieee/fastmath grid, non-blocking, held back from report claims until reviewed (same discipline as Week 14).

**G2 (MCA depth sanity):** `p53` spread ≈ machine epsilon, `p24` spread ≈ float-surrogate magnitude (~2⁻²⁴-like above p53), consistent in direction with the existing n=3 packets but now from a stable N=30 mean.

**Claim buckets (unchanged from the 2026-07-08 design):** morphology / self-reference / precision-noise, now backed by full-breadth + depth-stable evidence instead of an 8-point/n=3 pilot.

**Success criteria:** 2 breadth packets (`headline256_p1`, HLL + HLLD) with G0 pass and a populated G1 ordering-flag report; 2 MCA-depth blocks (`mca_n30`, HLL + HLLD) `completed` with n=30 each precision; existing P0 packets untouched; regression README + INDEX §6 register the new paths; full `tests/py` suite green.

**Estimated wall time:** ~1-1.5h build+run per solver for the 24-variant breadth (≈2-3h both solvers); MCA N=30 likely several hours per solver at Docker/64² scale — run in background/overnight, both solvers can run sequentially or overlapped if Docker resource limits allow.

---

## 5. Error handling

| Failure | Behavior |
|---|---|
| G0 anchor fails at 24-variant scale | Exit 1; investigate (same anchor as the already-passing P0 packet, so a failure here points at a build-freshness or cfg-drift bug, not a new physics finding); never loosen tolerance. |
| A variant build/run fails mid-breadth | `run_case`/`build_variant` raise with existing error paths; packet aborts, no partial summary (matches existing P0 behavior). |
| Docker unavailable for N=30 MCA | Sampler records `blocked_environment` per precision (existing, non-failing outcome); packet is not supervisor-ready until rerun with Docker. |
| N=30 run exceeds practical wall-time | Not a code failure; run in background via the existing CLI, no new retry/timeout logic needed (matches Week-14 precedent of just running long jobs to completion). |

---

## 6. Testing strategy

Unit tests (no real builds/subprocesses), extending `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

- `deterministic_plan(variant_set="p1")` returns 24 rows, reference first, and includes variants with `fast_math=True` and `opt="O3"` that `variant_set="p0"` (default, unchanged) does not.
- `run_deterministic(..., variant_set="p1", ...)` with injected fake builder/runner/reader produces 24 measured rows and calls the builder once per variant (24 times).
- `write_outputs()` includes a non-empty `gates.G1.ordering_flags` key when passed P1-shaped rows (i.e., rows containing both `fastmath=True` and `fastmath=False` siblings at the same precision/opt/riemann) and omits/empties it for P0-shaped rows.
- `parse_args(["--phase", "p1", ...])` parses correctly and `main()`'s packet-path computation appends `_p1` to the profile subdir only when phase is `p1`.
- No new tests needed for the MCA sampler (CLI already covered by existing `test_mhd_precision_sampling.py`; N=30 is a runtime argument, not new code).

Evidence-run verification is command-level (G0/G1/G2 summary check + `.bin` hygiene sweep + full `pytest tests/py`), matching the existing OT packet precedent.

---

## 7. Docs registration

- `scripts/regression/README.md`: add the `--phase p1` flag and `mca_n30` sampler invocation under the existing OT precision-smoke entry.
- `docs/INDEX.md` §6: add the `experiments/week15/orszag_tang_precision_smoke[_hlld]/headline256_p1/` and `mca_n30/` data-products rows.
- Final report notes this closes the Week-14-deferred P1/P2 tiers for the OT 2D case (Brio-Wu 1D P1/P2 remain undone — out of scope here, flagged as a residual gap if not picked up separately).

---

## 8. References

- [2026-07-01-week14-mhd-plan-design.md](2026-07-01-week14-mhd-plan-design.md) §3 — original P1/P2 tier definitions (never executed).
- [2026-07-08-week15-ot-2d-precision-design.md](2026-07-08-week15-ot-2d-precision-design.md) — the P0 dual-solver OT pilot this spec scales up.
- [overall.md](../../requirement/overall.md) §Week 15 — primary-axis sweep requirement.
