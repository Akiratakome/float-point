# MHD Temporal Divergence

| case | samples | lambda L1 | lambda Linf | n_fit L1 | n_fit Linf | fit window |
|---|---:|---:|---:|---:|---:|---|
| brio_wu_1d | 15 | 30.6153 | 18.5791 | 13 | 13 | [0.01, 0.1] |
| orszag_tang_2d | 25 | 0.0293431 | -0.0422334 | 10 | 10 | [0.1, 0.5] |

- Mode: report-grade
- Technical pass: True
- Report-grade pass: True
- Gate pass: True
- Figure: `figures/temporal_divergence.png`

Technical pass checks case presence, finite nonnegative drift samples, and a positive Orszag-Tang L1 fit. Report-grade pass additionally requires exact samples, aligned series, finite fits, sufficient fit counts, and 80 successful provenance-complete runs. Neither gate requires OT>Brio-Wu ordering or a positive Orszag-Tang Linf fit.

Bounded result: the planned OT>Brio-Wu L1 contrast is not observed under the fixed fit windows (OT 0.0293431 vs Brio-Wu 30.6153).
The OT Linf fit is -0.0422334. Fit quality is not independently gated or quantified, so physical interpretation is limited to these deterministic fixed-window engineering fits.

The fitted lambda is a Lyapunov-like engineering growth rate of an fp32-vs-fp64 perturbation, not a formal maximal Lyapunov exponent.
