# Report 1 Reference Map

This file is a working reference map for Report 1 of *Effect of Floating-Point Precision and Hardware on HRSC Schemes*. It is not a bibliography file and should not be copied into the report verbatim. Use it to decide what each citation is meant to support.

Principle: cite fewer sources, but make each citation do visible work. A 7,500-word Report 1 should normally need a compact set of well-chosen references rather than a long survey bibliography.

## Priority Levels

| Level | Use in Report 1 |
|---|---|
| Core | Expected or strongly justified for this project; normally cite unless the corresponding topic is absent. |
| Conditional | Cite only if the report discusses that method, tool, benchmark, or implementation choice. |
| Lead only | Do not cite until independently verified from the publisher, arXiv, IEEE/ACM/SIAM, or library metadata. |

## Core References

These are the safest backbone for Report 1.

- **Toro, E. F.** *Riemann Solvers and Numerical Methods for Fluid Dynamics: A Practical Introduction*, 3rd ed., Springer, 2009.  
  Use for: finite-volume formulation, MUSCL-Hancock, limiter/reconstruction discussion, exact/approximate Riemann solvers, HLLC, and 1D shock-tube validation context.

- **Liska, R. and Wendroff, B.** "Comparison of Several Difference Schemes on 1D and 2D Test Problems for the Euler Equations," *SIAM Journal on Scientific Computing*, 25(3), 995-1017, 2003. doi:`10.1137/S1064827502402120`.  
  Use for: 2D Euler benchmark selection and comparison framing. Particularly relevant for the Liska-Wendroff 2D configurations used in the experiments.

- **Bard, C. M. and Dorelli, J. C.** "A simple GPU-accelerated two-dimensional MUSCL-Hancock solver for ideal magnetohydrodynamics," *Journal of Computational Physics*, 259, 444-460, 2014. doi:`10.1016/j.jcp.2013.12.006`.  
  Use for: GPU implementation context, MUSCL-Hancock on accelerator hardware, and the project brief's longer-term MHD motivation. Do not overclaim: Report 1 is mainly Euler validation unless the text explicitly connects to MHD.

- **Goldberg, D.** "What Every Computer Scientist Should Know About Floating-Point Arithmetic," *ACM Computing Surveys*, 23(1), 5-48, 1991. doi:`10.1145/103162.103163`.  
  Use for: binary floating-point representation, rounding, cancellation, and why fp32/fp64 differences are expected.

- **IEEE Computer Society.** *IEEE Standard for Floating-Point Arithmetic*, IEEE Std 754-2019, 2019. doi:`10.1109/IEEESTD.2019.8766229`.  
  Use for: formal definitions of binary floating-point formats, rounding modes, exceptional values, and IEEE semantics.

- **Higham, N. J.** *Accuracy and Stability of Numerical Algorithms*, 2nd ed., SIAM, 2002.  
  Use for: numerical error language, stability/conditioning distinction, and disciplined discussion of rounding error without hand-waving.

## HRSC and Riemann-Solver Theory

Use this group to support the mathematical-theory and code-description sections. Do not cite every item if Toro already supports the point sufficiently.

- **Harten, A., Lax, P. D. and van Leer, B.** "On upstream differencing and Godunov-type schemes for hyperbolic conservation laws," *SIAM Review*, 25(1), 35-61/62, 1983.  
  Use for: HLL-family fluxes and the conservation-law setting.

- **Toro, E. F., Spruce, M. and Speares, W.** "Restoration of the contact surface in the HLL-Riemann solver," *Shock Waves*, 4, 25-34, 1994. doi:`10.1007/BF01414629`.  
  Use for: HLLC specifically, especially if HLLC is presented as the main solver choice.

- **Roe, P. L.** "Approximate Riemann solvers, parameter vectors, and difference schemes," *Journal of Computational Physics*, 43, 357-372, 1981.  
  Use for: approximate Riemann solver background if contrasting Roe/HLL/HLLC or explaining why a different solver was chosen.

- **van Leer, B.** "Towards the ultimate conservative difference scheme. V. A second-order sequel to Godunov's method," *Journal of Computational Physics*, 32(1), 101-136, 1979. doi:`10.1016/0021-9991(79)90145-1`.  
  Use for: MUSCL reconstruction and second-order extension of Godunov methods.

- **Sod, Gary A.** "A survey of several finite difference methods for systems of nonlinear hyperbolic conservation laws," *Journal of Computational Physics*, 27(1), 1-31, 1978. doi:`10.1016/0021-9991(78)90023-2`.  
  Use for: Sod shock tube only if this test appears in the validation suite. Verified publisher metadata gives author "Gary A Sod", volume 27, issue 1, April 1978, pages 1-31. Suggested BibTeX key if used: `SOD19781`.

## Floating-Point, Precision, and Reliability

Use this group to make the precision discussion rigorous. Avoid generic statements such as "GPU is less accurate"; specify the mechanism being discussed.

- **Higham, N. J. and Mary, T.** "Mixed precision algorithms in numerical linear algebra," *Acta Numerica*, 31, 347-414, 2022. doi:`10.1017/S0962492922000022`.  
  Use for: broader mixed-precision framing. This is useful background, but Report 1 should still ground claims in the project's Euler experiments.

- **Higham, N. J. and Mary, T.** "A new approach to probabilistic rounding error analysis," *SIAM Journal on Scientific Computing*, 41, A2815-A2835, 2019.  
  Use for: probabilistic rounding-error framing if stochastic arithmetic or repeated perturbation runs are discussed. Verify DOI before adding to `.bib`.

- **Parker, D. S.** *Monte Carlo Arithmetic: Exploiting Randomness in Floating-Point Arithmetic*, UCLA Computer Science Department Technical Report CSD-970002, 1997.  
  Use for: historical Monte Carlo arithmetic background if Verificarlo/MCA is introduced.

- **Denis, C., de Oliveira Castro, P. and Petit, E.** "Verificarlo: checking floating point accuracy through Monte Carlo Arithmetic."  
  Use for: Verificarlo methodology if the report discusses or uses Verificarlo. There are two citable records; choose one deliberately in `references.bib`, rather than mixing fields from both:
  - Published proceedings version: *2016 IEEE 23rd Symposium on Computer Arithmetic (ARITH)*, 55-62, 2016. doi:`10.1109/ARITH.2016.31`.
  - arXiv version: arXiv:`1509.01347` `[cs.MS]`, submitted 2015 and last revised as v4 in 2018; arXiv DOI `10.48550/arXiv.1509.01347`. If using the user's arXiv BibTeX, keep it as an `@misc` arXiv entry with `year={2018}` and no IEEE proceedings DOI.

## Benchmark and Validation References

Use only the benchmarks that actually appear in the validation chapter and experiments.

- **Woodward, P. and Colella, P.** "The numerical simulation of two-dimensional fluid flow with strong shocks," *Journal of Computational Physics*, 54, 115-173, 1984.  
  Use for: double Mach reflection, forward-facing step, interacting blast waves, or other strong-shock 2D validation cases if included.

- **Shu, C.-W. and Osher, S.** "Efficient implementation of essentially non-oscillatory shock-capturing schemes," *Journal of Computational Physics*, 77, 439-471, 1988.  
  Use for: Shu-Osher shock-density wave if included.

- **LeVeque, R. J.** *Finite Volume Methods for Hyperbolic Problems*, Cambridge University Press, 2002.  
  Use for: alternative textbook support for finite-volume conservation-law exposition. Usually optional if Toro is already doing the main work.

## MHD References

Report 1 should not look like an MHD dissertation unless the text explicitly connects Euler work to the full project trajectory. Use this section for brief motivation or future-work framing.

- **Brio, M. and Wu, C. C.** "An upwind differencing scheme for the equations of ideal magnetohydrodynamics," *Journal of Computational Physics*, 75, 400-422, 1988. doi:`10.1016/0021-9991(88)90120-9`.  
  Use for: Brio-Wu shock tube if MHD validation is discussed.

- **Orszag, S. A. and Tang, C.-M.** "Small-scale structure of two-dimensional magnetohydrodynamic turbulence," *Journal of Fluid Mechanics*, 90(1), 129-143, 1979. doi:`10.1017/S002211207900210X`.  
  Use for: Orszag-Tang vortex if MHD validation is discussed.

- **Dedner, A., Kemm, F., Kroener, D., Munz, C.-D., Schnitzer, T. and Wesenberg, M.** "Hyperbolic divergence cleaning for the MHD equations," *Journal of Computational Physics*, 175, 645-673, 2002.  
  Use for: divergence-cleaning discussion only.

- **Evans, C. R. and Hawley, J. F.** "Simulation of magnetohydrodynamic flows: a constrained transport method," *Astrophysical Journal*, 332, 659-677, 1988.  
  Use for: constrained-transport comparison only.

## Frameworks, Hardware, and Reproducibility

These should support implementation choices, not replace experiment evidence.

- **Zhang, W. et al.** "AMReX: a framework for block-structured adaptive mesh refinement," *Journal of Open Source Software*, 4(37), 1370, 2019. doi:`10.21105/joss.01370`.  
  Use for: AMReX only if the report discusses AMReX or uses it in the implementation.

- **Demmel, J. and Nguyen, H. D.** "Fast reproducible floating-point summation," 21st IEEE Symposium on Computer Arithmetic, 2013.  
  Use for: reproducibility issues in floating-point reductions if parallel reductions or non-deterministic accumulation order are discussed. Verify final citation metadata before adding.

- **NVIDIA / Intel compiler and hardware white papers** are lead-only unless a precise vendor document is actually used.  
  Use for: FMA, GPU fp64 throughput, or compiler floating-point semantics only after verifying the exact current document title, URL, version, and date. Prefer primary hardware manuals or compiler documentation over informal web pages.

## Course and Project Documents

These are binding for the project but are not normally bibliography items unless the report style requires internal documents to be cited.

- `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`  
  Use for: project aims, required Report 1 validation scope, expected comparison across precision and hardware, and supervisor-specified references.

- `report1/requirements/SciComp_Mphil_Handbook-2025-26.pdf`  
  Use for: word limit, formatting, submission process, declaration, deadline, and general marking context.

- `docs/requirement/Coding_and_submission_guidelines.pdf`  
  Use for: code archive, README, reproducibility, and submission-integrity expectations.

- `report1/examples/Project-Report-1-example.pdf`  
  Use only as a structural example. It must not be treated as a source of scientific content or project-specific requirements.

## Suggested Citation Map by Section

- **Introduction:** project brief, Toro, Goldberg/IEEE, Bard and Dorelli if motivating the hardware/MHD trajectory.
- **Literature/background:** Toro, Liska-Wendroff, Goldberg, Higham, IEEE 754; add HLLC/MUSCL primary papers only where they support a specific technical claim.
- **Mathematical theory:** Toro, van Leer, Harten-Lax-van Leer, Toro-Spruce-Speares, Higham.
- **Code description:** Toro for algorithmic structure; Bard and Dorelli for GPU-solver comparison only if relevant; AMReX only if used/discussed.
- **Validation:** Liska-Wendroff, Sod, Woodward-Colella, Shu-Osher, or other benchmark-origin references only for tests actually run.
- **Precision/hardware analysis:** Goldberg, IEEE 754, Higham, Verificarlo/Parker only if stochastic arithmetic or accuracy tooling is actually used.
- **Conclusion/future work:** brief return to Bard and Dorelli / MHD references only if the text explains how Report 1 sets up Report 2.

## Before Adding to `references.bib`

1. Prefer publisher, DOI, arXiv, IEEE/ACM/SIAM/Cambridge/Springer, or university-library metadata.
2. Copy BibTeX from the publisher where possible; do not hand-type DOI strings unless necessary.
3. Do not cite a reference just because it is in this file. Each citation should support a sentence in the report.
4. Drop any source whose role cannot be explained in one sentence.
5. Keep lead-only entries out of the bibliography until verified.

Last updated: 2026-05-17.
