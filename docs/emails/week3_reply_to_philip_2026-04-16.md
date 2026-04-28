# Reply to Philip — Stationary Contact Results + CFL Tip

---

Dear Philip,

Thank you for the suggestions and the CFL tip for the 123 test — I hadn't considered reducing the time-step for the initial transient, and it's a good idea. I'll implement a CFL ramp (e.g. CFL=0.16 for the first 5 steps, then CFL=0.8) and re-run the Rusanov 123 test to see if it survives the initial near-vacuum formation.

I've completed the **stationary contact** Verificarlo analysis. Below are the detailed results — I think they turned out to be quite interesting.

---

## Stationary Contact: Verificarlo MCA Results

### Setup

The test is: ρ_L=1.0, ρ_R=0.5, u=0, p=1.0 — a single stationary contact discontinuity at x=0.5. No shocks, no rarefactions. I ran 30 MCA samples with both HLLC and Rusanov at two precision levels (p=53 double, p=24 float32).

### Result 1: Verificarlo can detect the contact interface location

The significant-digits profile for **HLLC density** shows a sharp V-shaped dip at exactly x=0.5:

| Region | HLLC p53 sig digits (ρ) | HLLC p24 sig digits (ρ) |
|--------|------------------------|------------------------|
| Left side (ρ=1.0, x<0.4) | 14.58 | 5.86 |
| **Contact (x~0.5)** | **13.44** | **4.95** |
| Right side (ρ=0.5, x>0.6) | 14.44 | 5.74 |

The dip is ~1.1 sig digits at double precision and ~0.9 sig digits at float32. This means the contact position is **identifiable purely from the FP precision data** — you don't need to look at the solution values, just the precision profile.

See: **`vfc_stationary_contact_zoom.png`** (attached) — Top-left panel (ρ, p53): the HLLC blue line dips sharply at the green dashed line (x=0.5), while the Rusanov red line is flat. Top-right panel: same pattern at float32 but more pronounced.

### Result 2: Precision reveals which side is denser

The left side (ρ=1.0) consistently has **higher sig digits** than the right side (ρ=0.5): 14.58 vs 14.44 at p53, 5.86 vs 5.74 at p24. This is a direct consequence of the metric being relative — `s = -log10(σ/|μ|)` — so higher absolute values give lower relative error. The precision profile tells you which side is "above" and which is "below."

See: **`vfc_stationary_contact_spatial.png`** — Top row (density): the HLLC blue line sits systematically higher for x<0.5 than x>0.5. The asymmetry is visible at both precision levels.

### Result 3: Rusanov cannot detect the interface

Rusanov smears the contact over ~10 cells, so its sig-digit profile is nearly flat — no spike, no left/right asymmetry. This is visible in:

- **`vfc_stationary_contact_overlay.png`** — Top row = HLLC, bottom row = Rusanov. In the density panels (left column): HLLC shows a razor-sharp transition at x=0.5 with tight MCA sample clustering on both sides (grey lines); Rusanov shows a smooth sigmoid spread over x ≈ 0.45–0.55. The HLLC velocity panel (middle) shows nearly zero scatter (S*=0 exactly), while Rusanov shows visible grey noise around u=0.

- **`vfc_stationary_contact_std.png`** — Top-left panel (absolute σ(ρ), p53): HLLC (blue) has a sharp spike at x=0.5, jumping ~2 orders of magnitude above background. Rusanov (red) has no spike. Bottom-left panel (relative std): HLLC shows both the contact spike AND the left/right level difference (left side lower because |μ| is larger).

### Result 4: Pressure is not affected

Both schemes show flat, high sig digits for pressure (~14.6 at p53, ~5.9 at p24) across the entire domain. This is expected — pressure is p=1.0 everywhere (continuous across the contact), so there is no FP sensitivity from the pressure field. The contact only affects density.

See: **`vfc_stationary_contact_zoom.png`** — Bottom row (pressure): both HLLC and Rusanov are flat.

### Conclusion

The stationary contact is an interesting case because it isolates a single feature — the density discontinuity — with no shocks or rarefactions to confound the analysis. The results show that:

1. **Verificarlo MCA can serve as a discontinuity detector**: the precision profile maps directly to the solution structure, with dips at discontinuities and level shifts reflecting solution magnitude.
2. **HLLC preserves this structure** because it resolves the contact sharply (1–2 cells). Rusanov's numerical diffusion destroys it.
3. The contact itself is **not particularly FP-unstable** — the dip is only ~1 sig digit, and even at float32 precision the solution retains ~5 sig digits everywhere. The HLLC branch conditions remain stable (consistent with the unstable-branch analysis on the Sod test).

---

## Regarding Your Other Suggestions

- **FORCE instead of Rusanov**: HLLC remains the primary solver throughout — all existing results are unchanged. On the FORCE question: Rusanov is the centred-flux component of FORCE (`F_LF = 0.5*(F_L+F_R) - 0.5*S_max*(U_R-U_L)`), while the full FORCE flux averages a Lax-Friedrichs step with a Richtmyer (Lax-Wendroff) step: `F_FORCE = 0.5*(F_LF + F_RI)`. Since the Rusanov comparison already shows that the centred flux has identical FP sensitivity to HLLC, and FORCE is an average of Rusanov with a second-order centred flux, I'd expect FORCE to fall in the same range. That said, if you'd like a direct FORCE comparison for completeness (or because it's closer to what the spec calls "SLIC"), I can implement the FORCE flux as a third drop-in option alongside HLLC and Rusanov — the code structure already supports this via the `FluxScheme` enum. Please let me know if you'd like me to proceed with that.
- **2D Verificarlo tests**: will start this soon.
- **Report writing**: I'll begin the literature review and numerical methods sections.
- **123 test CFL ramp**: I'll try your suggestion of reducing the time-step by a factor of 5 for the first 5 steps and report back.

All plots are in `experiments/week4_rusanov/plots/`. I can send any of them in higher resolution if needed.

Best regards,
Yudong
