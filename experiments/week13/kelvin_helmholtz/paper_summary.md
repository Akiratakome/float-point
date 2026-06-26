# Week 13 Kelvin-Helmholtz Paper-Style Figures

Paper anchor: Kelvin-Helmholtz is used here as a 2D ideal-MHD shear-layer morphology benchmark following Frank et al. 1996. Lecoanet et al. 2015 is recorded as the limitation anchor: inviscid KH comparisons are sensitive to perturbations and regularisation, so this packet is bounded morphology and diagnostic evidence, not a full convergence claim.

This packet is generated from the local `256^2` HLL Kelvin-Helmholtz run using `tests/cases/kelvin_helmholtz_2d/kh.cfg` at `t=1.0`. It is paper-style morphology evidence and does not claim that the full `512^2` self-reference validation gate passed.

## Local run diagnostic

`[mhd] t=1.000000 steps=1148 divB_mean=4.411e-05 divB_max=6.714e-04`

## Figures

- `experiments/week13/kelvin_helmholtz/figures/kh_density_bmag.png`
- `experiments/week13/kelvin_helmholtz/figures/kh_divb.png`
- `experiments/week13/kelvin_helmholtz/figures/kh_paper_style.png`

## Pending validation

The full `mhd_kh_2d.py` validation still requires the `512^2` self-reference run from `kh_ref.cfg` plus the `glm_cr=0` diagnostic control. Those runs are intentionally not launched by `--paper-figures-only`; the `512^2` gate remains pending under the local runtime policy for this workstation.
