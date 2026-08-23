# Orszag--Tang HLLD fp64 positivity-guard completion

The corrected conservative update completed the HLLD fp64 Orszag--Tang runs at
128, 256, and 512 with CFL 0.2 through `t=0.5`. The 512 run completed in 3277
steps; its saved fp64 grid is finite with `rho_min=1.0976039403` and
`pressure_min=0.3798552929`.

The adjacent-grid density mean-L1 differences are `0.07514601996` and
`0.04181536595`, giving the bounded three-grid diagnostic `p=0.8456635061`.
This is a self-refinement result, not an exact-solution error or proof of an
asymptotic convergence regime.

Run configs, stdout/stderr, metadata, and the retained 512 grid are under this
directory. The final binary SHA-256 is
`6cb38f91936bfa749a61fd37cfe0986d14aeec1c45764442071ea9092f0d3ccd`.
