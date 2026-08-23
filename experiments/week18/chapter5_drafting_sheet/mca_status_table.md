# Table 5.1 candidate: MCA evidence status

| case | solver | virtual_precision | samples | scope | status | allowed_use | source |
|---|---|---|---|---|---|---|---|
| brio_wu_1d | hll | p53 | 30 | test=brio_wu, nx=800, t_end=0.1, cfl=0.4, riemann=hll | report-grade | bounded deterministic-plus-MCA result | experiments/week18/precision_mca_gate/summary.json |
| brio_wu_1d | hll | p24 | 30 | test=brio_wu, nx=800, t_end=0.1, cfl=0.4, riemann=hll | report-grade | bounded deterministic-plus-MCA result | experiments/week18/precision_mca_gate/summary.json |
| brio_wu_1d | hlld | p53 | 30 | test=brio_wu, nx=800, t_end=0.1, cfl=0.4, riemann=hlld | report-grade | bounded deterministic-plus-MCA result | experiments/week18/precision_mca_gate/summary.json |
| brio_wu_1d | hlld | p24 | 30 | test=brio_wu, nx=800, t_end=0.1, cfl=0.4, riemann=hlld | report-grade | bounded deterministic-plus-MCA result | experiments/week18/precision_mca_gate/summary.json |
| orszag_tang_2d | hll | p53 | 30 | test=orszag_tang, nx=64, ny=64, t_end=0.05, cfl=0.4, riemann=hll | provisional-reduced-scope | reduced-scope context only; do not merge with deterministic headline | experiments/week18/precision_mca_gate/summary.json |
| orszag_tang_2d | hll | p24 | 30 | test=orszag_tang, nx=64, ny=64, t_end=0.05, cfl=0.4, riemann=hll | provisional-reduced-scope | reduced-scope context only; do not merge with deterministic headline | experiments/week18/precision_mca_gate/summary.json |
| orszag_tang_2d | hlld | p53 | 30 | test=orszag_tang, nx=64, ny=64, t_end=0.05, cfl=0.4, riemann=hlld | provisional-reduced-scope | reduced-scope context only; do not merge with deterministic headline | experiments/week18/precision_mca_gate/summary.json |
| orszag_tang_2d | hlld | p24 | 30 | test=orszag_tang, nx=64, ny=64, t_end=0.05, cfl=0.4, riemann=hlld | provisional-reduced-scope | reduced-scope context only; do not merge with deterministic headline | experiments/week18/precision_mca_gate/summary.json |
| kelvin_helmholtz_2d | hll | p53+p24 | 4 | case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4 | validation | pipeline and reduced-case directional evidence only | experiments/week18/csc_findings_synthesis/summary.json |
| kelvin_helmholtz_2d | hlld | p53+p24 | 4 | case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4 | validation | pipeline and reduced-case directional evidence only | experiments/week18/csc_findings_synthesis/summary.json |
| kelvin_helmholtz_2d | hll | p53 | 30 | case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4 | reduced-scope-provenance | local Docker toolchain and reduced-case noise-scale provenance only | experiments/week16/kelvin_helmholtz_precision/mca_smoke/hll/summary.json |
| kelvin_helmholtz_2d | hll | p24 | 30 | case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4 | reduced-scope-provenance | local Docker toolchain and reduced-case noise-scale provenance only | experiments/week16/kelvin_helmholtz_precision/mca_smoke/hll/summary.json |
| kelvin_helmholtz_2d | hlld | p53 | 30 | case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4 | reduced-scope-provenance | local Docker toolchain and reduced-case noise-scale provenance only | experiments/week16/kelvin_helmholtz_precision/mca_smoke/hlld/summary.json |
| kelvin_helmholtz_2d | hlld | p24 | 30 | case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4 | reduced-scope-provenance | local Docker toolchain and reduced-case noise-scale provenance only | experiments/week16/kelvin_helmholtz_precision/mca_smoke/hlld/summary.json |
| kelvin_helmholtz_2d | hll | p53+p24 | 0 | grid=256x256, t=1.0 | blocked | limitation only; no MCA numerical claim | experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.json |
| kelvin_helmholtz_2d | hlld | p53+p24 | 0 | grid=256x256, t=1.0 | blocked | limitation only; no MCA numerical claim | experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.json |
