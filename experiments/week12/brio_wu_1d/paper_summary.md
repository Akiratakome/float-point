# Brio-Wu Paper-Style Validation Profiles

Paper anchor: Brio & Wu 1988, DOI `10.1016/0021-9991(88)90120-9`.

The figure `figures/brio_wu_paper_profiles.png` is generated from this repository's Week 12 HLL Brio-Wu output, not copied from the paper. It plots the 800-cell profiles for density `rho`, velocity `vx`, transverse magnetic field `By`, and pressure `p` at `t=0.1` with `gamma=2`.

Self-reference convergence against the local N=8000 double run remains secondary engineering evidence. The paper-grounded validation claim is limited to qualitative Brio-Wu wave-structure agreement plus the local divergence sentinel.

## Artefacts

- Binary input: `experiments/week12/brio_wu_1d/bw_800.bin`
- Paper-style figure: `experiments/week12/brio_wu_1d/figures/brio_wu_paper_profiles.png`
- Existing self-reference summary: `experiments/week12/brio_wu_1d/summary.md`

## Brio-Wu sentinel

`[mhd] t=0.100000 steps=759 divB_mean=3.339e-16 divB_max=4.441e-14`
