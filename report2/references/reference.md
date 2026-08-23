# Report 2 citation map

This file is a verification workspace, not a bibliography. Add a source only
after checking the original paper/book and recording the sentence it supports.

| Manuscript role | Candidate source family | Verification status |
|---|---|---|
| Ideal GLM--MHD state and wave structure | Dedner et al. (2002); Miyoshi and Kusano (2005) | VERIFIED for the nine-variable GLM extension, divergence-cleaning pair and ideal-MHD wave structure; project discretisation and fallback details remain code-specific. |
| GLM divergence cleaning | Dedner et al. (2002), DOI `10.1006/jcph.2001.6961` | VERIFIED for the mixed hyperbolic/parabolic GLM method; it does not justify the project-specific `glm_cr=0.18` choice. |
| Brio--Wu benchmark | Brio and Wu (1988), DOI `10.1016/0021-9991(88)90120-9` | VERIFIED: implemented left/right states, `Bx=0.75`, `gamma=2`, and `t=0.1` match the standard problem. |
| MHD Riemann pseudo-convergence | Torrilhon (2003), DOI `10.1016/S0021-9991(03)00347-4` | VERIFIED for non-uniform/pseudo-convergence of finite-volume ideal-MHD Riemann calculations; it motivates caution about same-scheme refinement but does not prove that the present Brio--Wu run follows the same failure mode. |
| Orszag--Tang benchmark | Tóth (2000), DOI `10.1006/jcph.2000.6519` | VERIFIED after the explicit unit-square coordinate/time rescaling recorded below. |
| Kelvin--Helmholtz setup | Tricco (2019) smooth double-shear functional form; Frank et al. (1996) aligned weak-field MHD regime; Lecoanet et al. (2016) limitation | VERIFIED AS ADAPTED: no checked paper exactly matches all implemented parameters; the code/config are the exact setup authority. |
| Lecoanet KH IC reproduction | Lecoanet et al. (2016); Tricco (2019) mode diagnostic; Berlok and Pfrommer (2019) linear theory | VERIFIED, BOUNDED: exact unstratified smooth IC in the B=0 inviscid limit; early linear growth only, not the nonlinear diffusive/dye reference. |
| HLL/HLLD solvers | Harten, Lax and van Leer (1983), DOI `10.1137/1025002`; Miyoshi and Kusano (2005) | VERIFIED for the HLL two-signal-speed construction and the HLLD ideal-MHD solver family; no cross-solver ranking is inherited. |
| MUSCL--Hancock GPU MHD context | Bard and Dorelli | VERIFIED for second-order CUDA MUSCL--Hancock ideal-MHD context; its GTX 480 speed-up is not transferable to this workstation. |
| Floating-point fundamentals | IEEE 754-2019; Goldberg (1991); Higham (2002) | VERIFIED for standard formats/operations, rounding effects and numerical-stability context; these sources do not predict the experiment-specific discrepancy magnitudes. |
| Monte Carlo arithmetic / Verificarlo | Denis et al. (2016), DOI `10.1109/ARITH.2016.31` | VERIFIED for Verificarlo's LLVM compiler instrumentation of Monte Carlo arithmetic; it does not make virtual p24 equivalent to IEEE fp32. |
| Reproducibility terminology | Plesser (2018), DOI `10.3389/fninf.2017.00076` | VERIFIED for the history and coexistence of conflicting reproducibility/replicability terminology; the report therefore declares an operational usage rather than claiming a universal taxonomy. |
| Reproducible computational records | Sandve et al. (2013), DOI `10.1371/journal.pcbi.1003285` | VERIFIED for retaining programs, parameters and manual procedures; the report's exact metadata schema remains project-specific. |
| Cross-code MHD comparison | Kritsuk et al. (2011), DOI `10.1088/0004-637X/737/1/13` | VERIFIED for comparing nine MHD methods on a shared turbulence benchmark with common statistical measures; it supplies comparison design context, not a ranking transferable to this project. |
| Divergence-control alternatives | Powell et al. (1999); Evans and Hawley (1988); Balsara and Spicer (1999); Londrillo and Del Zanna (2004); Gardiner and Stone (2005) | VERIFIED for eight-wave transport and constrained-transport method families; no source establishes that the project GLM choice is superior. |
| Independent MHD implementations | Mignone et al. (2007); Stone et al. (2008, 2020) | VERIFIED for the PLUTO, Athena and Athena++ Godunov MHD frameworks; they are comparison candidates, not exact references. |
| Reproducibility principles | Peng (2011); Stodden et al. (2016); Wilson et al. (2017); Benureau and Rougier (2018) | VERIFIED for disclosure of code/data/workflows and distinctions among rerunning, reproduction and replication; sufficiency of this repository remains a project claim. |
| Reproducible reductions/OpenMP/MPI | Collange et al. (2015), DOI `10.1016/j.parco.2015.09.001` | VERIFIED for order-dependent floating-point reductions and deterministic summation; the present MHD kernels do not exercise a parallel reduction and make no MPI result claim. |

Rules:

- Do not re-cite Report 1 background sources merely to recreate its literature
  review.
- Cite the benchmark/setup source that matches the implemented initial
  condition, not a convenient secondary paper.
- Bibliography entries are added to `References/references.bib` only after this
  map records a supported manuscript sentence.

## Full bibliography expansion audit (2026-08-03)

This historical expansion brought the manuscript bibliography to 33 cited
entries. The entries below that were inserted at that stage were checked
against the publisher, standards body, institutional record, or author record;
candidate sources that were reviewed but not cited were deliberately not added
to `references.bib`.

| Key | Verified metadata | Manuscript use |
|---|---|---|
| `powellEtAl1999adaptiveMhd` | JCP 154(2), 284--309, DOI `10.1006/jcph.1999.6299` | Eight-wave divergence treatment context. |
| `evansHawley1988ct` | ApJ 332, 659--677, DOI `10.1086/166684` | Original constrained-transport context. |
| `balsaraSpicer1999ct` | JCP 149(2), 270--292, DOI `10.1006/jcph.1998.6153` | Godunov/CT coupling context. |
| `gardinerStone2005ct` | JCP 205(2), 509--539, DOI `10.1016/j.jcp.2004.11.016` | Unsplit Godunov/CT alternative. |
| `londrilloDelZanna2004uct` | JCP 195(1), 17--48, DOI `10.1016/j.jcp.2003.09.016` | Upwind constrained transport. |
| `stoneEtAl2008athena` | ApJS 178(1), 137--177, DOI `10.1086/588755` | Independent MHD implementation candidate. |
| `mignoneEtAl2007pluto` | ApJS 170(1), 228--242, DOI `10.1086/513316` | Independent MHD implementation candidate. |
| `stoneEtAl2020athenapp` | ApJS 249(1), article 4, DOI `10.3847/1538-4365/ab929b` | Modern independent MHD framework candidate. |
| `goldberg1991floatingPoint` | ACM Computing Surveys 23(1), 5--48, DOI `10.1145/103162.103163` | Floating-point rounding context. |
| `higham2002accuracy` | SIAM, 2nd ed., ISBN `978-0-89871-521-7`, DOI `10.1137/1.9780898718027` | Numerical stability and finite-precision context. |
| `ieee7542019` | IEEE Std 754-2019, DOI `10.1109/IEEESTD.2019.8766229` | Standard arithmetic/format context. |
| `collangeEtAl2015reduction` | Parallel Computing 49, 83--97, DOI `10.1016/j.parco.2015.09.001` | Order-dependent parallel reductions. |

Bibliographic verification does not validate a manuscript claim by itself.
Each citation above is used only for the narrow role in the final column; all
project-specific numerical values remain bound to experiment summaries.

## Submission citation audit (2026-08-03)

- The manuscript contains 34 distinct citation keys and the bibliography now
  contains the same 34 keys: no missing and no uncited entries.
- Author, title, venue, year, volume/issue, pages and DOI/URL fields of the 33
  pre-existing entries were rechecked against their DOI registry or publisher
  records. No metadata correction was required. DOI resolution links are the
  `https://doi.org/<doi>` forms recorded throughout this file; the sole URL-only
  record was checked against the current
  [Microsoft `/fp` documentation](https://learn.microsoft.com/en-us/cpp/build/reference/fp-specify-floating-point-behavior).
- `torrilhon2003pseudo` was added from the
  [Elsevier article record](https://doi.org/10.1016/S0021-9991(03)00347-4):
  M. Torrilhon, *Journal of Computational Physics* 192(1), 73--94 (2003).
  Its claim lock is limited to the documented possibility of non-uniform
  ``pseudo-convergence'' in finite-volume ideal-MHD Riemann problems.

## Chapter 6 verified source and claim lock

Checked on 2026-08-03 against the original publisher pages and article text.

### Reproducibility terminology --- `plesser2018reproducibility`

- **Source:** H. E. Plesser, *Frontiers in Neuroinformatics* 11, 76 (2018),
  DOI [`10.3389/fninf.2017.00076`](https://doi.org/10.3389/fninf.2017.00076).
- **Verified support:** reproducibility and replicability have acquired
  conflicting meanings across disciplines and policy documents.
- **Allowed manuscript sentence:** "Reproducibility terminology differs across
  fields, so the distinctions here are operational rather than universal."
- **Boundary:** the article does not select or validate this report's metadata
  fields, evidence gates or definitions.

### Computational record keeping --- `sandveEtAl2013reproducible`

- **Source:** G. K. Sandve, A. Nekrutenko, J. Taylor and E. Hovig, *PLoS
  Computational Biology* 9(10), e1003285 (2013), DOI
  [`10.1371/journal.pcbi.1003285`](https://doi.org/10.1371/journal.pcbi.1003285).
- **Verified support:** the rules call for recording program versions,
  parameters, intermediate results and manual procedures in reproducible
  computational workflows.
- **Allowed manuscript sentence:** "The harness follows practical guidance to
  retain programs, parameters and manual procedures."
- **Boundary:** the paper does not establish that this project's retained
  artefacts are sufficient, correct or independently reproducible.

### Shared MHD comparison design --- `kritsukEtAl2011comparison`

- **Source:** A. G. Kritsuk et al., *The Astrophysical Journal* 737(1), 13
  (2011), DOI
  [`10.1088/0004-637X/737/1/13`](https://doi.org/10.1088/0004-637X/737/1/13).
- **Verified support:** nine numerical MHD methods were compared on one
  isothermal magnetized turbulence problem using common statistical measures.
- **Allowed manuscript sentence:** "Shared benchmarks and diagnostics enable
  cross-code MHD comparison."
- **Boundary:** the paper studies a different problem and metric set. It does
  not support a universal ordering of methods or any numerical result in this
  report.

## Chapter 5 verified source and claim lock

Checked on 2026-07-30 against the IEEE DOI metadata and the authors' arXiv
version.

### Verificarlo --- `denisEtAl2016verificarlo`

- **Source:** C. Denis, P. de Oliveira Castro and E. Petit, *2016 IEEE 23rd
  Symposium on Computer Arithmetic (ARITH)*, 55--62 (2016), DOI
  [`10.1109/ARITH.2016.31`](https://doi.org/10.1109/ARITH.2016.31); author
  version [`arXiv:1509.01347`](https://arxiv.org/abs/1509.01347).
- **Verified support:** Verificarlo is an LLVM compiler extension that applies
  Monte Carlo arithmetic instrumentation and can capture the numerical effect
  of compiler optimisations.
- **Allowed manuscript sentence:** "The MCA runs used Verificarlo compiler
  instrumentation."
- **Boundary:** the source does not show that this project's configurations,
  samples or spread values are correct. Those claims remain tied to the logged
  experiment artefacts. Virtual p24 is not treated as IEEE fp32.

## Chapter 4 verified source and claim lock

Checked on 2026-07-28 against the original articles or publisher/author copies
and against `src/mhd/mhd_solver.cpp` plus the canonical case cfgs.

### GLM divergence cleaning — `dedner2002glm`

- **Source:** A. Dedner et al., *Journal of Computational Physics* 175,
  645--673 (2002), DOI
  [`10.1006/jcph.2001.6961`](https://doi.org/10.1006/jcph.2001.6961).
- **Verified support:** the method couples a generalized Lagrange multiplier to
  MHD so divergence errors are transported and damped; the mixed
  hyperbolic/parabolic form is the relevant method family.
- **Allowed manuscript sentence:** “The implementation uses the mixed
  hyperbolic/parabolic GLM approach of Dedner et al. to transport and damp
  numerical divergence errors.”
- **Not supported by the paper:** that `glm_cr=0.18` is theoretically optimal,
  or that the project’s Gaussian `Bx` disturbance is copied from Dedner et al.
  The parameter and diagnostic disturbance are project choices and must be
  reported as such.

### HLL — `hartenLaxVanLeer1983`

- **Source:** A. Harten, P. D. Lax and B. van Leer, *SIAM Review* 25,
  35--61 (1983), DOI
  [`10.1137/1025002`](https://doi.org/10.1137/1025002).
- **Verified support:** the paper develops the HLL approximate Riemann-solver
  framework in which two bounding signal speeds enclose a single intermediate
  state.
- **Allowed manuscript sentence:** “HLL encloses the wave fan between two
  signal speeds and supplies a compact two-wave flux.”
- **Boundary:** the source does not validate this project’s MHD wave-speed
  estimates, GLM coupling, fallback policy or numerical results.

### HLLD — `miyoshiKusano2005hlld`

- **Source:** T. Miyoshi and K. Kusano, *Journal of Computational Physics* 208,
  315--344 (2005), DOI
  [`10.1016/j.jcp.2005.02.017`](https://doi.org/10.1016/j.jcp.2005.02.017).
- **Verified support:** the paper develops the multi-state HLLD approximate
  Riemann solver for ideal MHD and motivates its discontinuity-resolving wave
  structure.
- **Boundary:** the source does not justify ranking this project’s HLLD and HLL
  runs when their CFL values differ.

### CUDA MUSCL--Hancock MHD context — `bardDorelli2014gpu`

- **Source:** C. M. Bard and J. C. Dorelli, *Journal of Computational Physics*
  259, 444--460 (2014), DOI
  [`10.1016/j.jcp.2013.12.006`](https://doi.org/10.1016/j.jcp.2013.12.006).
- **Verified support:** the paper implements a two-dimensional second-order
  MUSCL--Hancock ideal-MHD solver with HLL fluxes, Dedner divergence cleaning,
  and CUDA, providing a close algorithmic implementation comparison for the
  bounded GPU path. Its Figure 3 also records the evolution of a $512^2$
  Orszag--Tang calculation, which may support a qualitative topology statement.
- **Boundary:** its GTX 480 hardware, CPU baseline, optimisation choices, and
  reported speed-up differ from the present experiment and are not used as a
  quantitative performance baseline. Its Orszag--Tang panels are not treated as
  a cell-wise reference unless normalization, field, and time are explicitly
  aligned.

### Brio--Wu — `brioWu1988`

- **Source:** M. Brio and C. C. Wu, *Journal of Computational Physics* 75,
  400--422 (1988), DOI
  [`10.1016/0021-9991(88)90120-9`](https://doi.org/10.1016/0021-9991(88)90120-9).
- **Implementation match:** `rho_L/rho_R=1/0.125`, `p_L/p_R=1/0.1`,
  `By_L/By_R=1/-1`, zero velocity, uniform `Bx=0.75`, `gamma=2`, with the
  discontinuity translated to `x=0.5` on `[0,1]`; the reported state is at
  `t=0.1`.
- **Allowed manuscript sentence:** “The one-dimensional validation uses the
  standard Brio--Wu coplanar MHD Riemann problem.”
- **Boundary:** the project compares against its aligned `N=8000` numerical
  reference, not an exact Brio--Wu solution.

### Orszag--Tang — `toth2000divb`

- **Source:** G. Tóth, *Journal of Computational Physics* 161, 605--652
  (2000), DOI
  [`10.1006/jcph.2000.6519`](https://doi.org/10.1006/jcph.2000.6519),
  Section 6.4.
- **Source setup:** on `[0,2*pi]^2`, Tóth gives `rho=25/9`, `p=5/3`,
  `vx=-sin(y)`, `vy=sin(x)`, `Bx=-sin(y)`, `By=sin(2x)`, `gamma=5/3`, with
  periodic boundaries.
- **Implementation match:** the code uses `[0,1]^2` and substitutes
  `X=2*pi*x`, `Y=2*pi*y`, so its trigonometric arguments are exactly the
  unit-square form of the same fields. The corresponding time mapping is
  `T=2*pi*t`; hence the project’s `t=0.5` is Tóth’s `T=pi`, approximately the
  paper’s late comparison time `3.14`.
- **Allowed manuscript sentence:** “The Orszag--Tang case is the Tóth (2000)
  normalization rescaled from `[0,2*pi]^2` to the periodic unit square.”
- **Boundary:** the project’s 256/512 and three-grid comparisons use its own
  numerical references and do not inherit Tóth’s reported convergence order.

### Kelvin--Helmholtz — `tricco2019kh`, `frankEtAl1996kh`,
`lecoanetEtAl2016kh`, `berlokPfrommer2019kh`

- **Functional-form source:** Tricco (2019), DOI
  [`10.1093/mnras/stz2042`](https://doi.org/10.1093/mnras/stz2042), equations
  7--8, records the smooth periodic double-shear form used for `vx` and the
  localized sinusoidal perturbation used for `vy`.
- **MHD context source:** Frank et al. (1996), DOI
  [`10.1086/177009`](https://doi.org/10.1086/177009), supports the use of a
  periodic, equal-density hyperbolic-tangent shear layer with an aligned weak
  magnetic field and includes an Alfvén-Mach-5 case.
- **Limitation source:** Lecoanet et al. (2016), DOI
  [`10.1093/mnras/stv2564`](https://doi.org/10.1093/mnras/stv2564), shows why
  nonlinear KH comparisons require a carefully defined smooth setup,
  controlled diffusion, and a numerical reference; morphology alone is not an
  accuracy measure.
- **Exact project setup:** `src/mhd/mhd_solver.cpp` is authoritative for
  `rho=p=1`, `gamma=5/3`, `U0=0.5`, `a=0.025`, `delta=0.01`, `s=0.05`,
  `B0=0.1`, and interfaces at `y=0.25,0.75` on the periodic unit square.
- **Required manuscript wording:** call this “a project-defined smooth,
  periodic MHD double-shear benchmark adapted from the cited KH test families.”
  Do not write “the Frank et al. setup”, “the Dedner et al. setup”, or imply an
  exact reproduction of Lecoanet et al.
- **Boundary:** because the project omits explicit physical viscosity and
  thermal diffusion, its three-grid behavior is an engineering self-refinement
  diagnostic rather than convergence to the Lecoanet reference solution.

#### Independent Lecoanet initial-condition reproduction

- **Exact IC match:** the separate `kelvin_helmholtz_lecoanet` test uses
  `[0,1] x [0,2]`, `rho=1`, `p=10`, `u_flow=1`, `A=0.01`, `a=0.05`,
  `sigma=0.2`, interfaces at `y=0.5,1.5`, `gamma=5/3`, and periodic boundaries,
  matching the unstratified Lecoanet initial condition. `B=0` selects the
  inviscid hydrodynamic limit of the ideal-MHD solver.
- **Diagnostic match:** `scripts/regression/mhd_lecoanet_kh_reproduction.py`
  implements the Tricco (2019) weighted `k=2*pi` mode amplitude and compares
  its fitted early growth with the Berlok--Pfrommer value `gamma=3.227`.
- **Observed packet:** at `128 x 256`, HLL fp64 gives a positive fitted rate
  `gamma=2.193155` over `t=0.25--1.0`, with `R^2=0.989882`; the 32.0% lower
  rate is retained as a solver/resolution diagnostic, not hidden by the gate.
- **Allowed manuscript sentence:** “A separate B=0 check exactly reproduced
  the smooth unstratified Lecoanet initial condition and showed log-linear
  growth of its seeded transverse mode over the declared early-time window.”
- **Required boundary:** this does not reproduce the nonlinear `Re=10^5`
  reference solution because the solver has no explicit viscosity, thermal
  diffusion, or passive dye; do not call the fitted rate agreement with
  `3.227`.
