# Week 12/13 Paper-Grounded MHD Benchmark Matrix

This matrix maps each local validation run to the literature benchmark it is
allowed to support. Local plots are generated from this repository's solver
outputs; paper figures are not copied.

Current evidence was audited with:

```powershell
git ls-files docs/week12 docs/week13 experiments/week12 experiments/week13 scripts/regression | Sort-Object
```

The audit shows tracked Week 12 Brio-Wu and GLM-cleaning summaries/figures, plus
the Week 13 HLLD-vs-HLL solver-comparison summary. Orszag-Tang and
Kelvin-Helmholtz report summaries are planned follow-up evidence, not current
paper-grounded validation artefacts.

| local case | production solver | literature anchor | cfg/time | report figure target | current evidence | claim boundary |
|---|---|---|---|---|---|---|
| Brio-Wu 1D | HLL | Brio & Wu 1988, DOI `10.1016/0021-9991(88)90120-9`; standard-problem discussion in Takahashi & Yamada 2012 | `tests/cases/brio_wu_1d/brio_wu.cfg`, `t=0.1` | four-panel profiles: rho, vx, By, p | Week 12 self-reference convergence, Brio-Wu profile/convergence figures, and divB sentinel | validates qualitative wave structure and divergence sentinel; self-reference norms are secondary |
| GLM div(B) cleaning | HLL | Dedner et al. 2002, DOI `10.1006/jcph.2001.6961` | Gaussian divB blob sweep, `glm_cr={0,0.18,0.36}` | divB decay curve and heatmap | Week 12 GLM sweep summary, decay figure, heatmap, generated cfgs, stdout/stderr, and metadata | demonstrates local cleaning behaviour, not physical MHD benchmark accuracy |
| Orszag-Tang 2D | HLL | Toth 2000, DOI `10.1006/jcph.2000.6519`; Orszag-Tang vortex benchmark context | `tests/cases/orszag_tang_2d/orszag_tang.cfg`, `t=0.5` | density/pressure/divB maps | run in Task 3 | validates benchmark morphology and finite diagnostics; 512-grid self-reference is secondary |
| Kelvin-Helmholtz 2D | HLL | Frank et al. 1996, arXiv `astro-ph/9510115`; Lecoanet et al. 2015, arXiv `1509.03630` limitation | `tests/cases/kelvin_helmholtz_2d/kh.cfg`, `t=1.0` | density, magnetic field magnitude, divB maps | run in Task 4 | bounded morphology/stability evidence; avoid overclaiming convergence because KH can be ill-posed |
| HLLD diagnostic | HLLD only as diagnostic | Miyoshi & Kusano 2005, DOI `10.1016/j.jcp.2005.02.017` | OT `256^2`, `t=0.5`, `riemann=hll|hlld` | HLL/HLLD rho diff and divB comparison | Week 13 solver_compare summary with finite HLLD run and elevated divB relative to HLL | HLLD executable but deferred for production due elevated divB |
