# Week 14 — HLL Production MHD Precision-Study Pilot Design

**Date:** 2026-07-01
**Branch base:** `week12-mhd-implementation` (Week 13 complete; see [week13-summary.md](../../week13/week13-summary.md))
**Requirement:** [overall.md](../../requirement/overall.md) §Phase 2 (Report 2) — systematic precision study on the MHD path; §Week 14 experiment infrastructure. Report 2 "Computational Results" (40%) is the target evidence.
**Harness contract:** [HARNESS.md](../../HARNESS.md) — `config → build → run → measure → aggregate → plot`; per-run generated cfg + stdout/stderr + metadata + summary; transient grids; no committed build dirs.
**Coding guidance:** [coding guidance.md](../../requirement/coding%20guidance.md) — no magic numbers, cfg-driven, comments explain *why*, modular, no committed build artifacts.
**Week 13 decision carried forward:** HLL is the production MHD solver; **HLLD stays diagnostic/deferred** (elevated Orszag-Tang div(B): 34.29 vs 3.72). No decision record here changes that.

---

## 1. Goal & scope boundary

Deliver a **thin, end-to-end, claim-bounded pilot of the HLL MHD floating-point
precision-study harness on Brio-Wu 1D**, proving the whole
`config → build → run → measure → aggregate → plot` pipeline on the cheapest
validated MHD case before any expensive 2D / 512² / cluster / GPU run. The
deliverable is the **harness**, not new solver physics.

The Week 14 objective (chosen by the supervisor from the A/B/C/D menu) is **A —
start the HLL production MHD precision-study matrix**. The route selection was
**"try all three"**, synthesised as a *phased, gated* plan: Route 3 (a thin
combined pilot) is the framing that proves the schema; Route 1 (deterministic
build-axis breadth) and Route 2 (Verificarlo MCA depth) are the two strands that
expand on top of the proven schema — all on Brio-Wu 1D, all gated, nothing
expensive this week.

### In scope (Week 14)

- **Brio-Wu 1D only**, **HLL only**, **CPU only** — the containment boundary.
- Deterministic build-axis fan (Route 1) + Verificarlo MCA sampling (Route 2),
  sequenced pilot-first (Route 3).
- One experiment directory with a single unified, claim-bucketed
  `summary.{csv,json,md}` fusing both strands.

### Out of scope (deferred to Week 15+), stated so the plan cannot quietly grow

- OT/KH 2D precision runs; any 512² reference run; GPU MHD; HLLD (stays
  diagnostic/deferred); temporal-divergence / Lyapunov (Week 16); the full
  48-variant scale.

### Unchanged surface (hard constraint)

- `src/mhd/*` solver numerics, `tests/cases/brio_wu_1d/brio_wu.cfg` and **all**
  cfg defaults, the `io.hpp` output header/format, `build_all.sh`, and the Euler
  `hrsc` path. No change to solver numerics, cfg defaults, or output formats
  unless the supervisor explicitly asks.

---

## 2. Verified preconditions (facts this plan relies on)

| Fact | Evidence |
|---|---|
| `hrsc_mhd` is a default `add_executable` target with no guarding option, so `build_all.sh` (`cmake --build`, no `--target`) already builds it in every variant dir. | [CMakeLists.txt:103](../../../CMakeLists.txt#L103) |
| The `<=` vs `<` implementation axis is real for the HLL MHD flux (`RIEMANN_STRICT_INEQUALITY` branches the `SL`/`SR` sign test). Effect is near-zero except when a wave speed is exactly 0 — precisely the FP-sensitive branch the project studies; a legitimate, claim-bounded axis. | [src/mhd/hll.hpp:24-30](../../../src/mhd/hll.hpp#L24-L30) |
| Build-variant naming is `{hardware}-{precision}-{opt}-{math}-{riemann}`, so the reference row label is `cpu-double-O2-ieee-leq`. | [scripts/build_matrix.py:17-21](../../../scripts/build_matrix.py#L17-L21) |
| Brio-Wu 1D regression anchor (HLL, default): `steps=759`, `divB_max≈4.441e-14`. | [week13-supervisor-meeting-EN.md](../../week13/week13-supervisor-meeting-EN.md) §0 |
| Verificarlo MHD path exists with a `blocked_environment` / `runnable_environment` / `blocked_run` / `completed` status vocabulary; p=24 is a **virtual-precision surrogate on the double build** (vary `VFC_MCA_PRECISION_BINARY64`, not the build precision); shared helpers in `scripts/regression/_mhd_harness.py`. | [scripts/verificarlo/mhd_verificarlo_smoke.py](../../../scripts/verificarlo/mhd_verificarlo_smoke.py) |

---

## 3. Phased plan with gates

Everything runs on Brio-Wu 1D, HLL, CPU. Each phase logs generated cfg +
stdout/stderr + metadata; grids stay transient (see §6 `--keep-grids`); build
dirs stay uncommitted.

| Phase | Route | What runs | Gate to advance |
|---|---|---|---|
| **P0 — Combined pilot** | 3 | 8 deterministic variants `{float,double}×{O2,Ofast}×{leq,strict}`, fastmath OFF **+** tiny MCA `p=53` (N≈8) & `p=24` (N≈8) | **G0 (hard):** all runs finite; `cpu-double-O2-ieee-leq` reproduces the Brio-Wu anchor (`steps=759`, `divB_max≈4.441e-14`) within tolerance; the unified summary schema validates end-to-end, **including a cleanly-represented `blocked_environment` MCA outcome** |
| **P1 — Deterministic breadth** | 1 | Expand to the full CPU fan `{float,double}×{O2,O3,Ofast}×{ieee,fastmath}×{leq,strict}` = 24 variants | **G1:** *(hard)* all runs finite **and** reference-anchor reproduced; *(soft)* flag and explain any fastmath/ieee ordering inversion — do **not** advance to report claims on the ordering until reviewed. Ordering is **not** a hard gate unless a specific metric + tolerance is later formalized. |
| **P2 — Verificarlo depth** | 2 | Scale MCA to N≈30 at `p=53` + `p=24`; noise floor + SNR + field-specific spreads | **G2:** `p=53` spread ≈ machine ε (sanity); `p=24` spread ≈ float-surrogate magnitude; N large enough for a stable mean. `blocked_environment` is a valid, non-failing outcome. |

**Dependency:** P1 and P2 both depend only on **G0**; P2 may overlap P1. If G0
fails, stop and repair the harness — do **not** scale a broken schema (scaling
only multiplies bad evidence).

**G1 rationale (soft ordering):** floating-point behaviour can be non-monotone,
so "fastmath ≥ ieee divergence" is a useful **sanity flag**, not a correctness
gate. Inversions are recorded in `gates.G1.ordering_flags` with an explanation
and held back from report claims pending review.

---

## 4. Experiment directory layout

```
experiments/week14/mhd_precision_pilot/
├── matrix.json                     # run_matrix.py input (deterministic variants)
├── runs/<variant>/                 # config.cfg, stdout.txt, stderr.txt, metadata.json, grid.bin (TRANSIENT)
├── mca/{p53,p24}/sample_NN/        # config.cfg, logs, metadata.json, grid.bin (TRANSIENT)
├── mca/environment.json            # verificarlo/docker env + runner probes (inherited pattern)
├── summary.{csv,json,md}           # unified: deterministic rows + MCA aggregate + gates + claim buckets
└── figures/
    ├── precision_variant_norms.png # per-variant L1/Linf bars, grouped by precision
    └── mca_noise_floor.png         # p53 vs p24 spread band
```

Grids are transient analysis inputs and are not committed; build dirs are
`.gitignore`'d and deletable.

---

## 5. Fields & metrics

**Diagnostic fields (Brio-Wu quartet, continuity with Week 12):**

- **Gating core:** `rho`, `By`, `p`.
- **Non-gating continuity field:** `vx` — computed and reported to restore the
  Week-12 `rho, vx, By, p` quartet, but drives **no gate** and need not appear in
  every figure.

**Deterministic measure (each run vs `cpu-double-O2-ieee-leq`):**
`L1/L2/Linf` of `rho, By, p` (+ `vx` reported), `divB_max`, `divB_mean`,
`walltime_s`, `steps`, `finite`, `rc`. The reference row is self-delta zero by
construction and must additionally match the Brio-Wu anchor. Norm math reuses
`src/utils/error_norms.hpp` semantics via the Python metric layer; grids are read
with [scripts/io_helper.py](../../../scripts/io_helper.py).

**Stochastic measure (MCA, per virtual precision):** field-specific
`spread_rho, spread_By, spread_p` (+ optional `spread_vx`) and
`snr_rho, snr_By, snr_p`, keeping `rho_mean_spread` for continuity with the
Week-13 smoke. SNR reuses [scripts/metrics/snr_metric.py](../../../scripts/metrics/snr_metric.py).

---

## 6. Unified summary schema + claim buckets

**`summary.json` is authoritative** because it carries nested gates, MCA
aggregates, and claim buckets. `summary.csv` is a **flattened row-wise**
convenience view (one row per deterministic run + MCA aggregate rows) and is
**not** authoritative. `matrix_summary_report.py` **may be reused only for
generic run/pair checks**; it is Euler-shaped (`rho, rhou, rhov, E`) and is
**not** the authoritative deterministic consumer — Week 14's authoritative
deterministic summary is produced by the new MHD precision-pilot aggregator
(§7).

```json
{
  "experiment": "week14-mhd-precision-pilot",
  "case": "brio_wu_1d", "solver": "hll",
  "reference": "cpu-double-O2-ieee-leq", "git_commit": "…",
  "deterministic": [
    {"variant":"cpu-double-O2-ieee-leq","precision":"double","opt":"O2",
     "fastmath":false,"riemann":"leq","is_reference":true,"finite":true,"rc":0,
     "steps":759,"walltime_s":…,"divB_max":…,"divB_mean":…,
     "L1_rho":0.0,"L2_rho":0.0,"Linf_rho":0.0,"L1_By":…,"Linf_By":…,
     "L1_p":…,"Linf_p":…,"L1_vx":…,"Linf_vx":…}
    /* … remaining variants carry deltas vs the reference row … */
  ],
  "mca": {
    "p53": {"status":"completed","n":30,"runner":"docker","finite":true,
            "rho_mean_spread":…,"spread_rho":…,"spread_By":…,"spread_p":…,
            "snr_rho":…,"snr_By":…,"snr_p":…,"mca_evidence_generated":true},
    "p24": {"status":"completed","n":30,"runner":"docker","finite":true,
            "rho_mean_spread":…,"spread_rho":…,"spread_By":…,"spread_p":…,
            "snr_rho":…,"snr_By":…,"snr_p":…,"mca_evidence_generated":true}
  },
  "gates": {
    "G0": {"pass":true,"anchor_reproduced":true,"schema_valid":true,
           "mca_representable":true},
    "G1": {"all_finite":true,"anchor_ok":true,
           "ordering_flags":[/* {axis, variants, metric, note} — non-blocking */]},
    "G2": {"p53_near_eps":true,"p24_float_scale":true,"n_stable":true}
  },
  "claims": {
    "morphology": "Brio-Wu wave structure vs Brio & Wu 1988 — established Week 12, referenced only.",
    "self_reference": "Deterministic deltas are precision/compiler/implementation deltas vs the double baseline (engineering consistency), NOT a point-wise match to an exact solution.",
    "precision_noise": "MCA noise floor + SNR = significant-digits-actually-delivered evidence."
  }
}
```

**`blocked_environment` is a first-class, non-failing MCA outcome.** When no
Verificarlo runner is discoverable, the `mca.<p>` block records
`status:"blocked_environment"`, null field spreads, and
`mca_evidence_generated:false`; the deterministic strand still runs and G0 passes
on schema validity provided the blocked state is cleanly represented. P0 fails
**only** if the schema cannot represent blocked MCA — never merely because
runner discovery was unavailable. (`blocked_run` is the analogous outcome for a
runner that was found but whose build/sample failed.)

**Three claim buckets, each tagged so nothing overclaims across them:**

- **morphology** — Brio-Wu wave structure vs literature (Week-12 evidence; only referenced).
- **self-reference validation** — deterministic deltas vs `cpu-double-O2-ieee-leq`; an engineering-consistency measure, *not* validation against an exact/analytic solution.
- **precision/noise** — MCA noise floor + SNR; the distinctive "achievable digits" Report-2 evidence.

---

## 7. New code, additive changes & untouched surface

**New code (all harness-layer; no solver/cfg/output change):**

| Artifact | Role | Lifecycle |
|---|---|---|
| `experiments/week14/mhd_precision_pilot/matrix.json` | Deterministic run matrix, consumed by existing `run_matrix.py`. | generated input |
| `scripts/regression/mhd_precision_pilot.py` | **Authoritative** Week-14 aggregator/driver: field norms (`rho/By/p` gate + `vx` continuity) vs `cpu-double-O2-ieee-leq`, divB, walltime, steps; folds the MCA aggregate; emits unified `summary.{csv,json,md}` + gates + claim buckets. Processes grids **iteratively** (load → norm → append → **delete unless `--keep-grids`**) per the overall.md batch rule. | canonical |
| `scripts/verificarlo/mhd_precision_sampling.py` | N-sample MHD MCA sampler (`p=53` / `p=24`), emits field-specific `spread_*` / `snr_*`. Inherits the Week-13 status vocabulary (`blocked_environment` / `runnable_environment` / `blocked_run` / `completed`) and runner-probe pattern. Added **alongside** `mhd_verificarlo_smoke.py`, which stays intact. | canonical |
| thin plot fns → `figures/precision_variant_norms.png`, `figures/mca_noise_floor.png` | pilot figures; reuse [scripts/io_helper.py](../../../scripts/io_helper.py) and existing plotting conventions. | generated |

**One additive, back-compatible harness change (approved):** add an **optional**
`filter=` kwarg to `build_matrix.generate_variants()` so P0 can request its
8-variant subset instead of hand-written CMake. The spec constrains it:

- **Default behaviour is unchanged** (byte-identical to today's full 24-variant
  output) and is covered by a regression test (§8).
- The filter **only selects from the already-defined variant space** — it adds
  no variants and defines no new axes.
- It **does not alter** compiler flags, cfgs, solver numerics, or output formats.

**Stays untouched:** `src/mhd/*` numerics; `brio_wu.cfg` and all cfg defaults;
the `io.hpp` output header; `build_all.sh`; the Euler `hrsc` path.
`matrix_summary_report.py` is reused only for generic run/pair checks, never
authoritative here.

---

## 8. Verification (evidence before claims)

- **pytest `tests/py/test_mhd_precision_pilot_summary.py`:** feed synthetic
  run/MCA dirs → assert `summary.json` structure, gate logic, claim buckets,
  field-norm math, and a cleanly-represented `blocked_environment` MCA block.
- **pytest for `build_matrix.generate_variants(filter=…)`:** default output is
  unchanged (full 24-variant set, order-stable); the P0 filter returns **exactly**
  the 8 expected variants (`{float,double}×{O2,Ofast}×{leq,strict}`, fastmath OFF).
- **G0 anchor assertion:** the reference run reproduces the Brio-Wu anchor
  (`steps=759`, `divB_max≈4.441e-14`) within tolerance.
- **Pilot-of-the-pilot smoke:** run the aggregator on a 2-variant + 2-sample
  micro config before the 8-variant / N≈8 P0.
- **No-Euler-regression:** default `hrsc` untouched (scripts-only change);
  existing unit tests remain green.

---

## 9. Risks → mitigations

| Risk | Mitigation |
|---|---|
| Verificarlo docker runtime for N≈30 | 1D only; cap/scale N; run in background; P2 gates on a stable mean; `blocked_environment` degrades cleanly. |
| 24 build dirs disk pressure | sequential builds; gitignored/deletable; P0 builds only 8. |
| fastmath/ieee non-monotonicity | soft `ordering_flags` (G1), never a hard gate. |
| Transient-grid discipline | aggregator deletes grids post-norm unless `--keep-grids`; `.gitignore` keeps grids + build dirs out of commits. |
| Scope creep to 2D / 512² / GPU | explicit out-of-scope list (§1) + phase gates (§3). |
| `matrix_summary_report.py` Euler-shape mismatch | resolved by the new authoritative aggregator (§7). |

---

## 10. Week 15 handoff

The same pipeline and `summary.json` schema re-point at OT/KH 2D (OT already has
a 512²→256² block-averaged reference; the **KH 512² self-reference gate is still
open** and is the one validation gap to close), add the full opt×fastmath fan at
2D, and later GPU MHD once it is built. The three claim buckets carry over
unchanged.

---

## 11. Open decisions — resolved

- **Objective:** A — HLL production MHD precision-study matrix.
- **Route:** all three, phased pilot → breadth → depth on Brio-Wu 1D.
- **Diagnostic fields:** `rho/By/p` gate + `vx` continuity.
- **Authoritative summary:** new `mhd_precision_pilot.py` aggregator; `summary.json`
  authoritative, `summary.csv` convenience.
- **MCA schema:** field-specific `spread_*`/`snr_*`, `rho_mean_spread` retained;
  `blocked_environment` representable and non-failing.
- **G1:** hard finite + reference anchor; soft ordering flag unless formalized.
- **build_matrix filter:** additive optional kwarg, default-preserving,
  regression-tested.
- **Grid deletion:** default delete after norms, `--keep-grids` escape hatch.

## 12. References

- Brio & Wu 1988, *JCP* 75, 400, DOI `10.1016/0021-9991(88)90120-9` — 1D MHD shock tube.
- Dedner et al. 2002, *JCP* 175, 645, DOI `10.1006/jcph.2001.6961` — GLM divergence cleaning.
- Miyoshi & Kusano 2005, *JCP* 208, 315, DOI `10.1016/j.jcp.2005.02.017` — HLLD (deferred/diagnostic).
- [overall.md](../../requirement/overall.md) §Phase 2 — systematic precision study; Verificarlo Tier-1 methodology.
- [week13-summary.md](../../week13/week13-summary.md), [paper_benchmark_matrix.md](../../week13/paper_benchmark_matrix.md) — Week 13 handoff and claim boundaries.
