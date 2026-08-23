# Report 2 figures

Add only report-facing figures selected in
`report2/planning/manuscript_outline.md`. Copying every experiment plot into the
manuscript is not an evidence-selection strategy. Record the generating summary
and script in the appendix evidence map.

## Additional review figures added on 2026-08-03

These assets answer the explicit request for visible OT/KH numerical fields and
comparisons. They are copies of logged experiment outputs, not generated
illustrations.

| Manuscript asset | Experiment source | Evidence use | SHA-256 |
|---|---|---|---|
| `ch4_brio_wu_profiles.png` | `experiments/week12/brio_wu_1d/figures/brio_wu_profiles.png` | $N=800$ profiles against the block-aligned $N=8000$ internal comparator | `1E84FD9AFCA4BC5B9AEE23B16270BFBC2A2116096FCD44E09A19A006C25184DB` |
| `ch4_orszag_tang_morphology.png` | `experiments/week13/orszag_tang/figures/ot_paper_style.png` | 256/512 internal-comparator morphology only | `E640194A73CA4C91F00E7216B42D515A3539DFC0BBD76348588F911A0562F139` |
| `ch4_orszag_tang_solver_comparison.png` | `experiments/week13/solver_compare/figures/ot_temperature_mk_fig12.png` | HLL/HLLD/internal-comparator context | `DE19CB88011FEC81C07BF69CBF335A3BAA4EDBBD755FF4504E52819E073EB10E` |
| `ch4_kelvin_helmholtz_morphology.png` | `experiments/week13/kelvin_helmholtz/figures/kh_paper_style.png` | Project-defined KH morphology only; 24 linearly spaced density contours | `A66A0BB7E4E2BD7691C571870DB13CD67F87E017C596329360160B5232A5BBCB` |
| `ch5_build_semantics.pdf` | `experiments/week20/brio_wu_build_semantics/figures/brio_build_semantics.pdf` | Direct one-axis response; exact zeros are shown in a separate bit-identical row rather than on the log axis | `F301464F952E1DA16866901C1A772F5B3878815B1EECD17C710E2FC1B58E27CB` |
| `ch5_kh_cfl.png` | `experiments/week18/supplemental/kh_cfl/figures/kh_cfl.png` | CFL sensitivity and step count | `ECBF7A05B4DA99053EA76F98236347511FAC90BE1975BECEDAEDEACE1AD4AA68` |

The build-semantics asset was regenerated with the `plot` function in
`scripts/regression/mhd_brio_build_semantics.py` from the unchanged
`summary.json` (SHA-256 `81C256C558278620B2F0CDC87B781159DD8B0EF0FF596A5BAEA90F780536CA7E`),
without rebuilding or rerunning the solver.  Its review PNG has SHA-256
`CF56968FC4DCE28854063AC31F486B948C31795D4D063647320E824B57BB6E99`.

Two further additions are native LaTeX tables in Chapter 3: the completed
test-case matrix and the controlled-axis comparison contract. Together with the
six figures above, this is an eight-item figure/table expansion.
