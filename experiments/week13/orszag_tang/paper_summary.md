# Week 13 Orszag-Tang Paper-Style Figures

Paper anchor: Orszag-Tang is used here as a 2D ideal-MHD vortex benchmark in the Toth 2000 div(B)-constraint context. The 512-grid self-reference norms are engineering consistency checks; report validation relies on paper-grounded morphology and finite div(B)/conservation diagnostics.

This packet is generated from the local `256^2` HLL Orszag-Tang run. It is paper-grounded morphology evidence, not a completed 512-grid self-reference validation gate.

## Local run diagnostic

`[mhd] t=0.500000 steps=806 divB_mean=1.225e-01 divB_max=3.720e+00`

## Figures

- `experiments/week13/orszag_tang/figures/ot_density_pressure.png`
- `experiments/week13/orszag_tang/figures/ot_divb.png`
- `experiments/week13/orszag_tang/figures/ot_paper_style.png`

## Pending validation

The full `mhd_orszag_tang_2d.py` validation still requires the `512^2` reference and `glm_cr=0` control run. On this workstation the full run exceeded the local 20 minute command budget after completing the `256^2` candidate, so the self-reference gate is not recorded here.
