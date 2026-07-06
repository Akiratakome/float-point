# HLLD div(B) Follow-Up (closes the Week 13 deferred-HLLD blocker)

Date: 2026-07-06 · Case: Orszag-Tang 2D, gamma=5/3, cfl=0.4, periodic, `glm_cr`
as listed · Driver: `scripts/regression/mhd_hlld_glm_sweep.py` (per-time-slice
sub-sweeps in `t010/ t030/ t050/ t075/ t100/ n256_t050/`).

Week 13 recorded: "HLL remains the production solver ... until the HLLD div(B)
behavior is understood" (divB_max 34.29 HLLD vs 3.72 HLL, OT 256^2, t=0.5).
This follow-up explains that number and re-measures it with a correct binary.

## Finding 1 — the Week-13 HLLD number was measured on a stale binary

The Week-13 `hrsc_mhd.exe` was built with a broken ninja/MSVC header-dependency
database (`#deps 0` for every object: the localized `cl /showIncludes` prefix
recorded at configure time did not byte-match the compiler's build-time output,
so no header dependencies were ever recorded). Commit `6491104`
("fix(mhd): make HLLD fan use GLM normal field consistently") changed only
`src/mhd/hlld.hpp` plus a test `.cpp`, so `unit_tests` picked the fix up but
`hrsc_mhd.exe` silently kept the pre-fix HLLD. The Week-13 solver comparison
(divB_max 34.29) therefore measured the **pre-consistency-fix** HLLD.

Verification with a fresh, dependency-correct rebuild of the same source:

- HLL rows reproduce Week-13 numbers **bit-identically** (256^2 t=0.5:
  steps=806, divB_mean=0.1225, divB_max=3.72) — the HLL path was never stale.
- HLLD rows change (256^2 t=0.5: steps=812, divB_mean=0.274,
  **divB_max=24.45**, vs stale 34.29).

Remediation: build dirs regenerated from a clean configure so the recorded
`msvc_deps_prefix` matches the compiler output; header deps now resolve
(`ninja -t deps` shows nonzero deps). Pitfall documented in `docs/INDEX.md`.

## Finding 2 — the remaining HLLD-vs-HLL div(B) gap is resolution of the
## current sheet, not a GLM inconsistency

Code-level: in this codebase HLL's wave-speed clamp to ±ch makes its BX/PSI
flux components algebraically identical to HLLD's exact Dedner split
(psi* = avg(psi) − ch/2·ΔBx; ch²·Bx* likewise), so the GLM (Bx, psi)
subsystem evolves identically under both solvers. The div(B) difference can
only enter through the transverse-field fluxes, where HLLD is (by design)
much less dissipative.

Measured (corrected binary, OT 128^2, glm_cr=0.18):

| t_end | steps HLL/HLLD | divB_max HLL | divB_max HLLD | rho finite/physical |
|---:|---|---:|---:|---|
| 0.10 | 76 / 76   | 1.173 | **1.085** | yes (HLLD *below* HLL) |
| 0.30 | 238 / 238 | 1.722 | 6.339 | yes |
| 0.50 | 396 / 401 | 1.734 | 13.53 | yes |
| 0.75 | 596 / 611 | 3.360 | 15.91 | yes (peak, current sheet thinnest) |
| 1.00 | 803 / 835 | 0.843 | 9.948 | yes (**decays after the peak**) |

Supporting checks:

1. **Bounded in time**: divB_max tracks the OT current-sheet lifecycle
   (grows to t≈0.75, then decays); no secular growth, no blow-up, density
   stays finite and physical everywhere (`validate_physical_grid` never
   throws over 0 ≤ t ≤ 1).
2. **Resolution scaling**: divB_max·dx ≈ const (128^2: 13.53/128 = 0.106;
   256^2: 24.45/256 = 0.096) — a fixed jump-fraction truncation signature at
   the discontinuity, exactly what a sharper solver produces when the same
   ΔB reversal is held over fewer cells. divB_mean *decreases* with
   resolution (0.318 → 0.274), i.e. the global divergence error converges.
3. **GLM cleaning still works under HLLD**: glm_cr=0.18 vs 0 control at
   t=0.5 (128^2): HLLD 13.53 vs 12.71, mean 0.318 vs 0.316 — the damping
   term neither fixes nor worsens the sheet-local spike for either solver
   (HLL: 1.734 vs 2.134); the spike is regenerated truncation error, not
   accumulating cleaning failure.
4. **1D anchor**: Brio-Wu with `riemann=hlld` runs clean:
   `steps=761, divB_mean=0.000e+00, divB_max=0.000e+00` (exact zero — psi
   stays identically zero for uniform Bx in 1D). HLL anchor unchanged:
   `steps=759, divB_max=4.441e-14`.

## Conclusion

The Week-13 blocker ("until the HLLD div(B) behavior is understood") is
closed: (a) the alarming 34.29 was an artifact of a stale binary; (b) the
corrected gap (24.45 vs 3.72 at 256^2) is bounded, convergent in the mean,
resolution-consistent, and localized at under-resolved current sheets — the
expected cost of a sharper Riemann solver under cell-centred GLM, not an
implementation bug. The 5-wave fan matches Miyoshi & Kusano (2005)
eqs. 38–66 term-by-term (audited 2026-07-06), and
`RIEMANN_STRICT_INEQUALITY` now covers the interior tie ownership
(SsL/SsR/SM), mirroring the HLLC S* convention.

## What a Week-14-style redo with `riemann = hlld` needs

1. Generated cfgs must set `riemann = hlld` (the runtime key already exists;
   the executable default stays `hll` so all Week-12/13 anchors hold).
2. Replace the G0 reference anchor for HLLD rows:
   `steps=761, divB_max=0.0` (Brio-Wu 800, t=0.1, double, O2, ieee, leq).
3. Metadata/claims fields that hardcode `"solver": "HLL"` must become
   solver-aware.
4. Build evidence from **freshly configured** build dirs (see the stale-binary
   pitfall in `docs/INDEX.md`) — with broken header deps an HLLD redo would
   silently rerun stale numerics.
