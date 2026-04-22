# Email draft: A2-S1 visible divergence marker (2026-04-22)

**To:** Philip (supervisor)
**From:** Yudong Tang
**Subject:** Week 4 A2 Stage 1 — HLLC vs Rusanov first-divergence markers

Dear Philip,

Following your 2026-04-17 note on marking the first point where HLLC and
Rusanov diverge, I attach a Stage-1 figure covering Sod and the stationary
contact on {ρ, p}. Red "x" marks the first index where
|a − b| exceeds the visible threshold 1e-3 · max(|a|, |b|); this is a
presentation-level criterion, explicitly non-statistical, so the supervisor
can inspect where the two solvers first disagree visually.

Stage 2 (MCA p=53 noise-floor calibration via Verificarlo, 30 samples per
solver × test) is running overnight; I will resend the same figure with
statistically-grounded thresholds within 1–2 days. The visible-mode plot is
a fallback that remains callable via `--mode visible`.

Interim observations:
- **Sod shock tube**: first divergence appears at i=38 (x≈0.193) for ρ and
  i=37 (x≈0.188) for p — both just left of the rarefaction fan's leading
  edge. Rusanov's extra numerical dissipation visibly smears the fan earlier
  than HLLC.
- **Stationary contact**: first divergence in ρ is at i=85 (x≈0.427), right
  at the contact discontinuity — HLLC resolves the sharp jump while Rusanov
  smears it significantly (Δρ ≈ 0.001 at the leading cell). Pressure shows
  no divergence at the 1e-3 threshold, confirming that both solvers preserve
  the stationary pressure balance equally well; the only difference between
  them is the contact smearing.

Best,
Yudong

---

## Attachment
`experiments/week4_vfc/divergence_marker/visible/hllc_vs_rusanov_sod_statcontact.png`

## Figure caption
Stage 1 visible threshold: |a-b| > 1e-3 * max(|a|,|b|). MCA noise-floor
calibration (Stage 2) follows within 1–2 days.
