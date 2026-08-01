# Report 2 citation map

This file is a verification workspace, not a bibliography. Add a source only
after checking the original paper/book and recording the sentence it supports.

| Manuscript role | Candidate source family | Verification status |
|---|---|---|
| Ideal-MHD equations and wave structure | Standard MHD text / verified course source | TODO |
| GLM divergence cleaning | Dedner et al. (2002), DOI `10.1006/jcph.2001.6961` | VERIFIED for the mixed hyperbolic/parabolic GLM method; it does not justify the project-specific `glm_cr=0.18` choice. |
| Brio--Wu benchmark | Brio and Wu (1988), DOI `10.1016/0021-9991(88)90120-9` | VERIFIED: implemented left/right states, `Bx=0.75`, `gamma=2`, and `t=0.1` match the standard problem. |
| Orszag--Tang benchmark | Tóth (2000), DOI `10.1006/jcph.2000.6519` | VERIFIED after the explicit unit-square coordinate/time rescaling recorded below. |
| Kelvin--Helmholtz setup | Tricco (2019) smooth double-shear functional form; Frank et al. (1996) aligned weak-field MHD regime; Lecoanet et al. (2016) limitation | VERIFIED AS ADAPTED: no checked paper exactly matches all implemented parameters; the code/config are the exact setup authority. |
| Lecoanet KH IC reproduction | Lecoanet et al. (2016); Tricco (2019) mode diagnostic; Berlok and Pfrommer (2019) linear theory | VERIFIED, BOUNDED: exact unstratified smooth IC in the B=0 inviscid limit; early linear growth only, not the nonlinear diffusive/dye reference. |
| HLL/HLLD solvers | HLL source; Miyoshi and Kusano for HLLD | VERIFIED for the HLLD method name and ideal-MHD solver family; no cross-solver ranking is inherited. |
| MUSCL--Hancock GPU MHD context | Bard and Dorelli | VERIFIED for second-order CUDA MUSCL--Hancock ideal-MHD context; its GTX 480 speed-up is not transferable to this workstation. |
| Floating-point fundamentals | IEEE 754; Goldberg; Higham | Inherit only when a Report 2 sentence needs them |
| Monte Carlo arithmetic / Verificarlo | Denis et al. (2016), DOI `10.1109/ARITH.2016.31` | VERIFIED for Verificarlo's LLVM compiler instrumentation of Monte Carlo arithmetic; it does not make virtual p24 equivalent to IEEE fp32. |
| Reproducible reductions/OpenMP/MPI | Source tied to the exact claim | TODO |

Rules:

- Do not re-cite Report 1 background sources merely to recreate its literature
  review.
- Cite the benchmark/setup source that matches the implemented initial
  condition, not a convenient secondary paper.
- Bibliography entries are added to `References/references.bib` only after this
  map records a supported manuscript sentence.

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
