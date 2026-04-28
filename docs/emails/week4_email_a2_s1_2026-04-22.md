# Email draft: A2-S1 visible divergence marker (2026-04-22)

**To:** Philip (supervisor)
**From:** Yudong Tang
**Subject:** Week 4 A2 Stage 1 — HLLC vs Rusanov first-divergence markers

Dear Philip,

Following your 2026-04-17 note on marking the point where HLLC and Rusanov
diverge, I attach a Stage-1 figure covering Sod and the stationary contact
on {ρ, p}. Every cell where |a − b| exceeds the visible threshold
1e-3 · max(|a|, |b|) carries a red "x"; each contiguous divergent run is
additionally labelled at its onset (dark-red cross + i, x), so every shock,
contact, and rarefaction crossing is called out rather than only the first.
This is a presentation-level criterion, explicitly non-statistical.

Stage 2 (MCA p=53 noise-floor calibration via Verificarlo, 30 samples per
solver × test) is running overnight; I will resend the same figure with
statistically-grounded thresholds within 1–2 days. The visible-mode plot
remains selectable via `--mode visible`.

Interim observations (at rel_tol = 1e-3, 200 cells):

- **Sod — ρ**: 81 divergent cells across 5 segments, onsets at
  x ≈ 0.192 (rarefaction head), 0.368 (rarefaction tail),
  0.628 and 0.682 (contact — two onsets because HLLC and Rusanov disagree on
  both sides of the contact), and 0.928 (shock front). Rusanov's broader
  dissipation stencil produces separate divergent runs at every wave
  structure.
- **Sod — p**: 63 divergent cells across 3 segments, onsets at
  x ≈ 0.188, 0.358, and 0.928. Pressure divergence does **not** appear at
  the contact, as expected since p is continuous across the contact
  discontinuity; the three segments correspond to rarefaction head,
  rarefaction tail, and shock front.
- **Stationary contact — ρ**: 33 divergent cells in a single segment with
  onset at x ≈ 0.428. Rusanov's numerical diffusion visibly smears the
  contact; HLLC keeps the jump tight.
- **Stationary contact — p**: no divergence — both solvers preserve the
  pressure-balance identically. The schemes differ only at the contact
  itself.

Best,
Yudong

---

## Attachment
`experiments/week4_vfc/divergence_marker/visible/hllc_vs_rusanov_sod_statcontact.png`

## Figure caption
Stage 1 visible threshold: |a-b| > 1e-3 * max(|a|,|b|). MCA noise-floor
calibration (Stage 2) follows within 1–2 days.
