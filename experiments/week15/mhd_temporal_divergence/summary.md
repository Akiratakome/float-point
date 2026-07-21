# MHD Temporal Divergence

| case | samples | lambda L1 | lambda Linf | fit window |
|---|---:|---:|---:|---|
| brio_wu_1d | 15 | 30.6153 | 18.5791 | [0.01, 0.1] |
| orszag_tang_2d | 25 | 0.0293431 | -0.0422334 | [0.1, 0.5] |

- Gate pass: True
- Figure: `figures/temporal_divergence.png`

The gate checks technical completeness, finite nonnegative drift samples, and a positive Orszag-Tang L1 fit. It does not require OT>Brio-Wu ordering or a positive Orszag-Tang Linf fit.

Bounded result: the planned OT>Brio-Wu L1 contrast is not observed under the fixed fit windows (OT 0.0293431 vs Brio-Wu 30.6153), and the OT Linf fit is -0.0422334. Fit quality is not independently gated or quantified, so physical interpretation is limited to these deterministic fixed-window engineering fits.

The fitted lambda is a Lyapunov-like engineering growth rate of an fp32-vs-fp64 perturbation, not a formal maximal Lyapunov exponent.
