# Speaker script - 10-minute mid-term presentation

**Yudong Tang - Dr. Philip Blakely - 05.06.2026**
Target: about 1100 spoken words. Plain spoken English, short sentences.

---

## 1 - Title (~0:25)
Good morning. I am Yudong Tang. My project studies how floating-point precision
and hardware affect shock-capturing CFD schemes.

The question is simple. If I run the same solver in single precision, on a GPU,
or with different compiler flags, does the answer change? And if it changes, is
that change large compared with the numerical error?

## 2 - Background (~0:45)
GPUs are much faster in single precision than in double precision. So fp32 is
attractive for CFD, but I need evidence before I use it.

There is also a reproducibility issue. Floating-point arithmetic is rounded, and
addition is not associative. A compiler can change operation order, use FMA, or
allow fast-math transformations. In shock problems, small differences usually
appear near shocks and contacts.

So I ask three questions. Is fp32 accurate enough? Can CPU and GPU agree
bit-for-bit under controlled flags? And where does precision matter in the flow?

## 3 - Numerical method (~0:50)
I first fix the method. I solve the two-dimensional Euler equations for an ideal
gas. The conserved variables are density, momentum, and energy.

I use a finite-volume method. Each cell stores an average state, and fluxes
through the faces update that state. This is suitable for shocks because it is
conservative.

The scheme is MUSCL-Hancock. It reconstructs left and right states at each face,
then predicts them by a half time step. I use a minmod limiter to reduce
oscillations near shocks.

At the face I use HLLC as the main Riemann solver. HLLC keeps the contact wave.
Rusanov is my comparison solver. It is more diffusive, so it gives a useful
method-change scale.

## 4 - Floating-point details, and how it is tested (~0:45)
Precision enters the solver in several places. Every operation is rounded.
Binary32 has a 24-bit significand, while binary64 has a 53-bit significand.

The pressure is also recovered from total energy by subtracting kinetic energy.
When those terms are close, the subtraction can lose leading digits. That
pressure then goes into the sound speed and the HLLC wave-speed estimates.

For the experiments, I keep one code path and change one axis at a time:
precision, device, solver, or compiler flags. I measure L1, L-infinity, and ULP.
I use exact references in 1D, and high-resolution double references in 2D.

## 5 - Validation: 1D shock tubes (~0:30)
Before I read any precision result, I check that the solver behaves correctly.

This slide shows Sod's shock tube at 200 cells, final time 0.25, and CFL 0.8.
The black line is the exact Riemann solution. The numerical solution follows the
rarefaction, contact, and shock in the right order.

The jumps are smeared over a few cells, which is expected. This gives me the
discretisation-error scale for the precision comparisons.

## 6 - Validation: 2D Riemann problem (~0:50)
The next test is Liska-Wendroff configuration 3. This run uses a 400 by 400 grid,
final time 0.3, and CFL 0.5.

The left image is the published Liska-Wendroff WAFT result. The right image is my
MUSCL-Hancock-HLLC run. I am not claiming the same code or the same numerical
method. I use the published figure as a visual benchmark for the wave pattern.

The colour shows pressure, and the contours show density. The key features are
the diamond-shaped shock interaction near the centre and the curved structures
inside it.

For the numerical check, I compare the 400 squared run with a 1600 squared double
reference. The density L1 error drops from 200 squared to 400 squared, and the
image SSIM improves. So this is a numerical-reference check, not an exact
solution proof.

## 7 - Finding 1: single vs double precision (~0:45)
The first result is fp32 versus fp64.

In the 1D cases, the fp32-fp64 difference is much smaller than the exact-solution
error. The reference-scaled density ratios are below 10 to the minus 4. So single
precision is below the method-error scale.

The 2D figure shows where the difference sits. It plots the density difference
between fp32 and fp64, with double-precision density contours on top.

The pattern is not uniform. The signal is concentrated near shocks and contacts.
Smooth regions are much quieter. So the remaining precision signal follows the
fronts.

## 8 - Finding 2: CPU vs GPU, and what breaks the match (~0:50)
The second result is about hardware.

With the matched strict-IEEE build, CPU and GPU saved outputs are bit-identical.
L1 is zero, L-infinity is zero, and maximum ULP is zero. This holds at final time
and at saved checkpoints for the five tested cases.

This statement is about saved states, not every temporary value inside one time
step. The solver also avoids the main reduction problem. The state is written
cell by cell. The CFL step uses max and min comparisons, not a summation tree.

But the build matters. When I enable fast-math, the saved state changes. In the
plot, the x-axis is normalised time and the y-axis is L1 drift on a log scale.
The curves grow with time, especially in pressure for stronger shock cases. So
the device is not the main issue here. The build flags are.

## 9 - How big are these effects? Solver vs the rest (~0:35)
This slide puts the effects on one scale.

The largest visible change is not CPU versus GPU. It is changing the solver from
HLLC to Rusanov. This is expected because Rusanov is more diffusive.

The figure shows LW3 at 200 squared cells, final time 0.3, in double precision.
This is a method change, not a reproducibility failure.

Fast-math is smaller than the solver change, but it is still real. The
fp32-fp64 difference is smaller again. The matched strict CPU-GPU difference is
zero in saved outputs.

## 10 - Verificarlo: Monte-Carlo arithmetic (~0:50)
So far I have compared deterministic runs. I also want to know where rounding
sensitivity lives. For that I use Verificarlo.

Verificarlo is an LLVM-based floating-point instrumentation tool. It replaces
normal floating-point operations with controlled versions, so I can test how
rounding affects the code without rewriting the solver.

Here I use its Monte-Carlo arithmetic mode. The solver is run 30 times with
random rounding. I test virtual precision levels p8, p16, p32, and p53. These are
virtual mantissa widths, not IEEE fp32 production runs.

For each cell, I divide the ensemble spread by the reference error. I call this
ratio eta. If eta is greater than 1, rounding noise is larger than the
reference-error scale, so that cell is precision-limited in this diagnostic.

## 11 - Where precision matters: results (~0:35)
This slide shows the Verificarlo result by region for LW3 density.

The regions are smooth cells, transition cells, and shock-front cells. The bars
show eta, and the labels show the percentage of precision-limited cells.

At p8, many cells are precision-limited. At p16, the sensitive area becomes
smaller. At p32, it reaches zero for this diagnostic.

The order is important. Smooth cells clear first. The shock-front region is the
hardest one. This agrees with the direct fp32-fp64 map.

## 12 - Conclusions and Report 2 (~0:40)
I will finish with three points.

First, single precision is accurate enough for these Euler tests compared with
the discretisation error. But its small error is concentrated near shocks and
contacts.

Second, CPU and GPU agree bit-for-bit on saved outputs under matched strict-IEEE
flags. When I allow fast-math, the answer changes. So reproducibility is mainly a
build-control issue here.

Third, Verificarlo helps me locate sensitivity. It points to the fronts as the
most sensitive regions.

For Report 2, I will extend the drift-in-time method to ideal MHD. MHD has more
wave families and the divergence-free magnetic-field constraint, so long-time
separation should be more interesting.

Thank you. I am happy to take questions.

---

## If you run over time
Drop slide 9, or make slides 10 and 11 shorter by saying only the definition of
eta and the main regional result.

## Backup notes for questions
- 1D shock tubes use CFL 0.8.
- LW3 uses CFL 0.5.
- LW12 uses CFL 0.4.
- The Liska-Wendroff images are visual benchmarks, not exact code matches.
- Verificarlo p32 is virtual precision, not IEEE binary32.
- The CPU/GPU claim is for saved states and saved checkpoints.
