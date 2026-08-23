# Supervisor review revision brief (2026-08-05)

Authoritative brief for the section-by-section revision of Report 2 in response
to the supervisor's review. Every writing agent MUST read this file in full
before editing, and must not exceed its assigned word budget.

Manuscript root: `report2/phd-thesis-template-2.4/`.

---

## 1. Hard constraints (non-negotiable)

- **Word count.** Formal maximum 7,500 words (Overleaf count, includes tables,
  captions and appendices; excludes bibliography). The local baseline before
  this revision round is `texcount -inc -sum thesis.tex = 7344`. The whole
  revision round has a **hard ceiling of +100 net words**. Display equations
  and inline maths are essentially free in `texcount`; prose is not. Prefer
  *replacing* prose with equations, and pay for every new explanatory sentence
  by deleting a redundant disclaimer.
- **No new experiments and no new numbers.** Every figure quoted here is from a
  logged packet. If a sentence you want to write is not supported by Section 3
  of this brief or by an existing packet summary, it belongs in
  limitations/future work, not in the results.
- **Do not change** solver numerics, cfg defaults, output formats, raw
  experiment artefacts, or any figure's underlying data.
- **Terminology.** "Accuracy" only against an exact or explicitly named
  numerical reference; otherwise discrepancy / difference / sensitivity /
  drift. Verificarlo `p24` is a *virtual* precision, not IEEE binary32. A
  fitted temporal rate is not a maximal Lyapunov exponent.
- **No repository internals in the prose.** No week numbers, packet names, run
  labels, script paths or source-file names in the manuscript body.
- Do not touch any section other than the one you are assigned. The working
  tree is shared; run `git diff -- <your file>` before you start and preserve
  any pre-existing changes.

## 2. What the supervisor asked for (the point of this round)

The headline instruction: **explain what the results mean rather than stating
numbers**, and place them in the wider context of numerical CFD — do the
findings confirm, contradict, or sit alongside what is known about algorithm
stability and computational accuracy?

Secondary, repeated instructions:

1. **More background and motivation** so a general reader understands the wider
   context and implications (carried over from the Report 1 assessors).
2. **Explain every acronym and piece of computer-science or physics jargon.**
   The supervisor specifically flagged "heteroscedastic", "Lyapunov exponent",
   "asymptotic regime", "corresponding gates", "block-aligned $N=8000$",
   "an asymptotic regime", "report-grade evidence", and
   "Local algebra was therefore tested before the complete device path".
3. **Stop announcing what the scope excludes.** It is normally obvious what was
   not done. Delete most such sentences; keep at most one statement of each
   genuinely load-bearing boundary, and prefer to carry it in the limitations /
   future-work material rather than repeating it in every results paragraph.
   This is the main source of the words needed to fund the new explanation.
4. **Do not confess to what the researcher failed to do.** Replace
   "was not recorded consistently enough to retrofit here" style sentences with
   either silence or a forward-looking future-work item.
5. **Do not cite specific source files.** A thesis does not refer to
   `src/...` or `scripts/...`.
6. Prefer "convergence rate" over "three-grid rates"; give a plausible physical
   or numerical reason whenever a number is surprising.
7. Turn "limitations" into "potential for future work" — a negative into a
   positive — and be more ambitious about what future work could cover.

## 3. Verified facts available for this revision

All of the following were verified against the source code and the logged
experiment artefacts on 2026-08-05. They may be used in the manuscript. Do not
add facts beyond this list without checking the packet yourself.

### 3.1 Solver implementation

**HLL signal speeds (as implemented).** Davis-type two-state estimate,
additionally clamped by the global GLM speed so that the fan always contains
the $\pm c_h$ waves:

```
S_L = min( min(v_xL - c_fL, v_xR - c_fR), -c_h )
S_R = max( max(v_xR + c_fR, v_xL + c_fL), +c_h )
```

with the fast magnetosonic speed

```
c_f = sqrt( 0.5 * [ (a^2 + c_A^2) + sqrt( (a^2 + c_A^2)^2 - 4 a^2 c_Ax^2 ) ] )
a^2 = gamma p / rho,  c_A^2 = |B|^2 / rho,  c_Ax^2 = B_n^2 / rho
```

and the standard HLL flux
`F = (S_R F_L - S_L F_R + S_L S_R (U_R - U_L)) / (S_R - S_L)`.
Left/right states are the MUSCL--Hancock predicted face states.

**HLLD (as implemented).** Full five-wave fan: $S_L$, $S_L^*$, $S_M$, $S_R^*$,
$S_R$, giving $F_L^*$, $F_L^{**}$, $F_R^{**}$, $F_R^*$. The GLM pair
$(B_n,\psi)$ is solved exactly first and re-imposed on every returned flux:

```
B_n*   = 0.5 (B_nL + B_nR) - 0.5 (psi_R - psi_L) / c_h
psi*   = 0.5 (psi_L + psi_R) - 0.5 c_h (B_nR - B_nL)
```

Outer speeds are the plain Davis estimate (no $\pm c_h$ clamp). With
$m_k = S_k - v_{xk}$ and total pressure $p_T = p + \tfrac12|\mathbf B|^2$:

```
S_M  = ( m_R rho_R v_xR - m_L rho_L v_xL - p_TR + p_TL )
       / ( m_R rho_R - m_L rho_L )
p_T* = ( m_R rho_R p_TL - m_L rho_L p_TR
         + rho_L rho_R m_R m_L (v_xR - v_xL) ) / ( m_R rho_R - m_L rho_L )
rho_k* = rho_k m_k / (S_k - S_M)
S_L* = S_M - |B_n| / sqrt(rho_L*),   S_R* = S_M + |B_n| / sqrt(rho_R*)
```

Fourteen guarded degeneracy tests protect these expressions (non-finite inputs;
$|m_R\rho_R-m_L\rho_L|$, $|S_k-S_M|$ and the Alfven denominator
$\rho_k m_k (S_k - S_M) - B_n^2$ each tested against a relative floor of
$64\varepsilon$; non-positive intermediate densities; non-finite intermediate
states or fluxes). When any test fires the **single interface** falls back to
HLL on the same GLM-split state.

**The `<=` versus `<` branch axis** is a build-time switch affecting four
comparisons: the HLL outer dispatcher (`S_L >= 0` / `S_R <= 0`), the HLLD outer
dispatcher, the HLLD Alfven tie (`S_L^* >= 0` / `S_R^* <= 0`) and the HLLD
contact tie (`S_M >= 0`). The flux is value-continuous across each tie, so the
two variants can only differ where rounding decides which side of an exact zero
a computed speed falls.

**GLM cleaning.** $c_h$ is recomputed every step as the maximum over all cells
of $|v_x| + c_{f,x}$ (and, in two dimensions, $|v_y| + c_{f,y}$); the same
$c_h$ sets $\Delta t = \mathrm{CFL}\, h / c_h$ and enters both sweeps and the
damping. Damping is applied once per step after both sweeps.

**Answer to "$c_r = 0$ gives infinities".** It does not, because the
implementation guards it: the damping routine returns immediately when
$c_h \le 0$ or $c_r \le 0$, so $\exp(-\Delta t\, c_h/c_r)$ is never evaluated
with a zero denominator and $\psi$ is left untouched. $c_r=0$ is therefore a
legitimate, supported *undamped control*, and this should be stated explicitly
rather than removed. Defaults: $c_r = 0.18$ in two dimensions, $c_r = 0$ in one
dimension.

**Justification of $c_r = 0.18$.** With the implementation's parameterisation
$c_p^2 = c_h c_r$, the setting $c_r = 0.18$ is exactly the ratio
$c_p^2/c_h = 0.18$ that Dedner et al. obtained from their numerical
experiments as a good compromise between damping strength and stability. Cite
`\citep{dedner2002glm}`. (Check `report2/references/reference.md` before
asserting anything else about that paper.)

**Answer to "does it abort?" — yes.** Three tiers. (i) Per cell: if a
slope-limited or predicted face state is non-physical, both faces revert to the
cell average (first order). (ii) Per line: if any cell in a row or column
update is non-physical, the whole line is recomputed with first-order HLL
fluxes on the raw cell states. (iii) After both sweeps and the damping, every
cell is re-tested; if any state is still non-finite or has $\rho \le 0$ or
$p \le 0$, the solver **raises an error and the run terminates with a
diagnosed numerical-failure status and a non-zero exit code**, reporting the
offending cell index and its density and pressure. There is no density or
pressure floor anywhere in the MHD path: the run stops rather than being
silently repaired. This matters — it is *why* the acceptance gates work, and it
actually fired (see 3.2 below).

**Reconstruction.** Minmod slopes are applied to the nine **conservative**
components, not to primitive variables.

**Threads.** There is no OpenMP work-sharing directive anywhere in the MHD code
path (the seven `#pragma omp` sites in the repository are all in the Euler
solver). The MHD binary is nonetheless compiled and linked with OpenMP enabled
and honours `OMP_NUM_THREADS` at the runtime level, so the thread sweep varies
only runtime setup, not the work decomposition. It is a genuine null control.

**CUDA path.** Mirrors boundary updates, minmod/Hancock reconstruction with the
per-cell physicality revert, the HLL flux including the $\pm c_h$ clamp and the
`<=`/`<` switch, both sweeps, the GLM damping guard, the step ordering and the
time-step formula. It does **not** implement the per-line first-order fallback
or the post-step physicality rejection, and does not implement HLLD. The
$c_h$ reduction is a two-stage parallel tree on the GPU against a sequential
row-major maximum on the CPU; because `max` is exactly associative in IEEE-754
for finite inputs, this reordering cannot itself introduce a rounding
difference — unlike a summation reduction. That is a genuinely useful point for
the discussion of why these two paths *can* agree bit-for-bit.

### 3.2 Why HLLD used CFL 0.2 in the resolution ladder — resolved

This answers the supervisor's questions on Sections 4.5, 5.2.2 and 5.5.

- The canonical case configurations all specify CFL 0.4. The **only** override
  is in the resolution-ladder experiment, which hard-codes CFL 0.2 for HLLD.
- The reason is recorded: an exploratory Orszag--Tang HLLD fp64 run at $512^2$
  and CFL 0.4 **terminated with a negative pressure** (reported at one cell,
  $\rho = 1.698$, $p = -0.306$). The same configuration at CFL 0.2 **also
  failed** ($\rho=1.774$, $p=-0.289$), so halving the CFL number was not by
  itself the fix.
- The actual fix was the numerical guard described in 3.1: the per-line
  first-order HLL fallback. With that guard in place the corrected binary
  completed $128^2$, $256^2$ and $512^2$ at CFL 0.2 (801, 1622 and 3277 steps).
- The Kelvin--Helmholtz HLLD ladder inherited CFL 0.2 mechanically, from a
  solver-keyed lookup, not from any KH-specific instability: the KH CFL sweep
  ran HLLD successfully at 0.2, 0.4, 0.6 and 0.8.
- **Therefore there is no contradiction** between Chapter 4 and Chapter 5. The
  Kelvin--Helmholtz precision comparison at $256^2$, $t=1.0$ genuinely used
  CFL 0.4 for both solvers, and the CFL sweep genuinely reached 0.8. Only the
  refinement ladder used 0.2. Say this plainly, once, in Section 4.5, and make
  the Chapter 5 sentences consistent with it.
- Honest boundary that must be preserved: the ladder's CFL asymmetry means HLL
  and HLLD refinement diagnostics are not directly comparable with each other.

### 3.3 Numbers verified against the logged packets

**Brio--Wu refinement against the aligned $N=8000$ fp64 comparator** (fp64,
CFL 0.4, $t=0.1$):

| $N$ | steps | mean $L_1(\rho)$ | mean $L_2(\rho)$ | $L_\infty(\rho)$ |
|---|---|---|---|---|
| 200 | 189 | 1.4806e-2 | 3.6416e-2 | 2.0835e-1 |
| 400 | 379 | 9.4633e-3 | 2.7137e-2 | 1.9148e-1 |
| 800 | 759 | 5.6417e-3 | 1.9230e-2 | 1.5468e-1 |

The quoted rates 0.70 and 0.46 are **least-squares slopes of
$\log_2(\text{error})$ against $\log_2 N$ over all three grids**, negated;
since the grids are equally spaced in $\log_2$ this equals
$\log_2(E_{200}/E_{800})/2$. Pairwise rates for $L_1$ are 0.646 (200→400) and
0.746 (400→800). "Block-aligned $N=8000$" means the 8000-cell reference is
conservatively block-averaged down onto the candidate grid — each candidate
cell is compared against the average of the $8000/N$ fine cells it contains —
so the two states are compared cell-for-cell on the coarse grid.

*Plausible, defensible explanation for rates below 1* (to be phrased as an
interpretation, not a proof): the Brio--Wu solution is piecewise discontinuous,
and for a shock-capturing scheme the formal second-order accuracy holds only in
smooth regions. Limiters reduce the scheme to first order at extrema and
discontinuities, and the classical result for a linearly degenerate contact
discontinuity is that a $p$-th order monotone scheme converges in $L_1$ at only
$O(h^{p/(p+1)})$, i.e. $h^{2/3} \approx 0.67$ for a second-order scheme — close
to the observed 0.70. The $L_2$ rate is lower still (0.46) because the squared
norm weights the smeared jump region more heavily than $L_1$ does. Brio--Wu
additionally contains a compound wave whose structure is slow to converge, and
the comparator shares the scheme's own discretisation bias. Cite
`\citep{toro2009riemann}` for the loss of formal order at discontinuities and
`\citep{torrilhon2003pseudo}` for MHD pseudo-convergence.

**Cross-system sensitivity.** fp32-vs-fp64 mean-relative $L_1(\rho)$ under
O2-default: Sod 1.466e-7, Liska--Wendroff Configuration 3 3.762e-7,
Brio--Wu 1.401e-7, Orszag--Tang 1.377e-7. Matching $L_\infty$:
3.837e-7, 5.254e-6, 1.075e-6, 3.565e-6.
Build pair (Ofast-fast vs O2-default) in fp32 mean-relative $L_1$: Sod exactly
0, LW3 5.124e-7, Brio--Wu 2.091e-7, OT 1.519e-7; in fp64 the same quantity lies
between 4.24e-17 and 4.21e-16.
**Resolution of the supervisor's Figure 5.1 query:** the bar above 4e-7 that he
noticed is the **LW3 build-pair bar at 5.124e-7**, which is a different series
from the fp32--fp64 bars. The text's stated range 1.377e-7 to 3.762e-7 is
correct for the fp32--fp64 series but reads as if it described the whole plot.
Fix by naming the series explicitly in the sentence, and by making the caption
distinguish the two series clearly.

**CPU/GPU repeats** (HLL; Brio--Wu $800\times1$, $t=0.1$, 759 steps;
Orszag--Tang $256^2$, $t=0.5$, 806 steps; $n=5$ per group; every group had zero
maximum ULP difference and zero absolute $L_\infty$ difference):

| Case | Precision | CPU median (s) | GPU median (s) |
|---|---|---|---|
| Brio--Wu | fp64 | 0.1621 | 0.3140 |
| Brio--Wu | fp32 | 0.1336 | 0.2740 |
| Orszag--Tang | fp64 | 27.511 | 4.456 |
| Orszag--Tang | fp32 | 20.971 | 3.536 |

Logged CPU/GPU median ratios: 0.510 and 0.488 (Brio--Wu fp64/fp32), 6.174 and
5.925 (Orszag--Tang fp64/fp32).
**Derived fp64→fp32 speed-ups** (ratios of the logged medians above, and the
answer to the supervisor's request): GPU 1.146x (Brio--Wu) and 1.260x
(Orszag--Tang); CPU 1.213x and 1.312x.
Raw Brio--Wu fp64 GPU repeats: 2.6952, 0.3169, 0.3140, 0.3054, 0.3069 s — the
outlier is the first repeat, i.e. first-touch device context creation.

*Defensible interpretation.* The Brio--Wu ratios below one are not a GPU defect:
the problem is 800 cells in one dimension, far below the occupancy at which the
device is usefully loaded, and the end-to-end timer includes device context
creation, per-step kernel launches over 759 steps, host--device transfers and
the required binary output. Fixed per-run and per-step overheads therefore
dominate a workload whose total CPU cost is only 0.16 s. The $256^2$
Orszag--Tang case has roughly two orders of magnitude more cells and 806 steps,
so the same fixed costs are amortised and the device's memory bandwidth
dominates. Equally informative is that the fp64→fp32 gain on the GPU is only
about 1.15--1.26x. A consumer GPU executes fp64 at a small fraction of its fp32
throughput, so a gain of that size shows this MUSCL--Hancock MHD kernel is not
limited by floating-point throughput at all; it is limited by memory traffic
and launch latency, and halving the size of each stored state buys roughly the
proportional bandwidth saving. That is consistent with the memory-bound
character reported for GPU MUSCL--Hancock MHD solvers
`\citep{bardDorelli2014gpu}`, and it is the reason single precision is worth
far less here than a peak-FLOP comparison would suggest.

**Kelvin--Helmholtz solver/precision timing** (CPU only, $256^2$, $t=1.0$,
CFL 0.4, one thread, one warm-up discarded, $n=5$): fp64 medians 34.484 s
(HLL) and 39.542 s (HLLD); fp32 medians 29.196 s and 34.254 s; all groups
1148 steps; all 20 outputs bit-identical within group. fp32 was 1.181x faster
for HLL and 1.154x for HLLD; HLLD cost 1.147x (fp64) and 1.173x (fp32) of HLL.

*Defensible interpretation.* These are CPU results and must be labelled as
such. A single-precision gain of about 1.15--1.18x on a CPU whose vector units
process twice as many binary32 as binary64 lanes indicates the same conclusion
as the GPU numbers: the stencil is limited by memory traffic and by scalar
non-vectorised work (square roots, branches, the guarded HLLD tests), not by
arithmetic throughput, so halving the data size recovers well under the
theoretical 2x. The 15--17% HLLD premium is modest for a solver that adds three
extra waves and fourteen guarded degeneracy tests per interface, which again
points to a memory-bound rather than flop-bound regime.

**Resolution dependence of the fp32--fp64 discrepancy** ($D_N$ = same-grid
density mean $L_1$; $E^{64}$ = matched fp64 $256^2$--$512^2$ adjacent-grid
difference; $S_N = D_N/E^{64}$):

| Case | Solver | $D_{128}$ | $D_{256}$ | $D_{512}$ | $E^{64}$ | $S_{512}$ |
|---|---|---|---|---|---|---|
| OT | HLL | 3.825e-7 | 7.896e-7 | 9.080e-6 | 7.722e-2 | 1.18e-4 |
| OT | HLLD | 2.147e-6 | 1.127e-5 | 5.554e-5 | 4.182e-2 | 1.33e-3 |
| KH | HLL | 1.357e-7 | 2.877e-7 | 8.498e-7 | 1.836e-3 | 4.63e-4 |
| KH | HLLD | 5.536e-7 | 1.078e-6 | 2.348e-6 | 8.496e-5 | 2.76e-2 |

$D_N$ **increases strictly monotonically with resolution in all four groups**,
and so does $S_N$. The largest $S_N$ is 2.76e-2, hence the "below 3%" statement.

*Defensible interpretation.* Yes, this is what one should expect, for three
compounding reasons. First, an explicit scheme at fixed CFL takes proportionally
more time steps as the grid is refined, so a refined run performs more rounding
operations per unit of simulated time and accumulates more of them. Second,
refinement resolves finer structures — thinner current sheets in Orszag--Tang,
sharper shear-layer roll-up in Kelvin--Helmholtz — with correspondingly larger
local gradients, and the rounding perturbation is advected and amplified in
those regions rather than diffused away. Third, the numerical dissipation that
would damp a small perturbation weakens as the grid is refined. The practically
important consequence is the direction of the trend: refining the grid reduces
discretisation error but *increases* the run-to-run separation between
precisions, so the two error sources converge towards each other and single
precision becomes relatively less benign at high resolution, not more. That is
the opposite of the intuition that a finer grid makes everything better, and it
is the single most transferable result in this section.

**Temporal fits** (fp32 vs fp64 density, HLL): Brio--Wu $N=800$, window
$[0.01,0.1]$, 15 aligned pairs, 13 used: mean-$L_1$ slope
$\lambda = 30.615$ with $R^2 = 0.963$; $L_\infty$ slope 18.579 with
$R^2 = 0.852$. Orszag--Tang $128^2$, window $[0.1,0.5]$, 25 aligned pairs, 10
used: slopes 0.02934 and $-0.04223$ with $R^2 = 0.0073$ and 0.0006.

*Interpretation of $\lambda = 30.6$.* The model is $\log e(t) = a + \lambda t$
with $t$ in code time units, so $\lambda$ has units of inverse code time and
$1/\lambda$ is an e-folding time: the fitted discrepancy grows by a factor of
$e$ every $1/30.6 \approx 0.033$ time units, i.e. by about **16x across the
fitted window** $\Delta t = 0.09$ (measured endpoint ratio 24x, larger than the
fit because the fit excludes both endpoints). In absolute terms the discrepancy
is still tiny — it grows from about 3.3e-9 to 7.9e-8 — so the useful statement
is about *shape*, not magnitude: on the shock-tube problem the fp32--fp64
separation grows systematically rather than saturating, which is what one
expects when a fixed rounding perturbation is carried by a moving discontinuity
whose numerical position differs by a fraction of a cell. On Orszag--Tang the
same model explains essentially none of the variation.

**Monte Carlo arithmetic** (Brio--Wu, $N=800$, $t=0.1$, $n=30$ samples per
block): p24 maximum density spreads 2.275e-6 (HLL) and 4.007e-6 (HLLD); p53
spreads 5.117e-15 and 8.442e-15; deterministic fp32--fp64 $L_\infty(\rho)$
1.075e-6 and 1.629e-6; hence the ratios 2.12 and 2.46.

*Interpretation of 2.12 and 2.46.* The comparison is between a stochastic
spread and a single deterministic difference, so the ratio is descriptive. Its
value is that it is of order one rather than orders of magnitude away: randomly
perturbing every operation at 24-bit significand precision moves the answer by
about twice as much as switching deterministically from binary64 to binary32
does. The deterministic fp32 result is therefore not a special or pathological
draw — it sits inside the cloud of results that 24-bit rounding alone can
produce. Equivalently, a single fp32 run gives no more information about the
answer than one sample from that cloud, which is the practical argument for
reporting a precision comparison as a distribution rather than a single number.
The p53 spreads are eight to nine orders of magnitude smaller, confirming that
the effect is a precision effect and not an instability of the case.

**KH CFL sweep** (fp32--fp64 density $L_\infty$, $256^2$, $t=1.0$): HLL
4.678e-6, 1.786e-6, 2.133e-6, 8.910e-7 at CFL 0.2, 0.4, 0.6, 0.8; HLLD
7.204e-6, 3.230e-6, 4.057e-6, 3.157e-6. Non-monotonic in both solvers. fp64
step counts 2296, 1148, 766, 574. All completed with finite positive states.

**Recorded environment.** Windows 10 build 26200; an Intel 64 family 6 model
198 processor; MSVC 19.51.36248.0. The GPU model, CUDA toolkit version and
driver version are **not** in the timing run metadata (only in project
documentation), so do not assert them as recorded metadata; if the GPU must be
identified, say that the device identity was not captured in the run record and
list it as a reproducibility gap.

### 3.4 Initial data, exactly as implemented

**Brio--Wu.** $x\in[0,1]$, $\gamma=2$, outflow boundaries, CFL 0.4, $t=0.1$,
$B_x = 0.75$ constant, $v_y=v_z=B_z=0$, $\psi=0$:

```
(rho, v_x, p, B_y) = (1,     0, 1,   +1)   for x <  0.5
(rho, v_x, p, B_y) = (0.125, 0, 0.1, -1)   for x >= 0.5
```

**Orszag--Tang.** Doubly periodic unit square, $\gamma=5/3$, CFL 0.4, $t=0.5$,
$c_r=0.18$, $v_z = B_z = 0$, $\psi = 0$:

```
rho = gamma^2 = 25/9,        p = gamma = 5/3,        B_0 = 1
v_x = -sin(2 pi y),          v_y =  sin(2 pi x)
B_x = -B_0 sin(2 pi y),      B_y =  B_0 sin(4 pi x)
```

Under $X = 2\pi x$, $Y = 2\pi y$ this is the original Orszag--Tang form
$v = (-\sin Y, \sin X)$, $B = B_0(-\sin Y, \sin 2X)$ on $[0,2\pi]^2$; note the
doubled wavenumber in $B_y$ only. Because $B_x$ depends only on $y$ and $B_y$
only on $x$, the cell-centred central-difference divergence is exactly zero at
$t=0$.

**Kelvin--Helmholtz** (project-defined smooth double shear layer). Doubly
periodic unit square, $\gamma=5/3$, CFL 0.4, $t=1.0$, $c_r=0.18$,
$U_0 = 0.5$, shear width $a = 0.025$, perturbation amplitude $\delta = 0.01$,
envelope width $s = 0.05$, $B_0 = 0.1$, layers at $y_1 = 0.25$, $y_2 = 0.75$:

```
rho = 1,   p = 1   (uniform: this is a pure velocity shear, no density jump)
v_x(y) = U_0 [ tanh((y - y_1)/a) - tanh((y - y_2)/a) - 1 ]
v_y(x,y) = delta sin(2 pi x) [ exp(-(y-y_1)^2/s^2) + exp(-(y-y_2)^2/s^2) ]
v_z = 0,  B_x = B_0 = 0.1,  B_y = B_z = 0,  psi = 0
```

so $v_x \to +U_0$ for $y_1 < y < y_2$ and $v_x \to -U_0$ outside, a shear jump
of $2U_0 = 1$ across each layer, a single-mode perturbation of one wavelength
across the box, and a uniform flow-aligned field giving an Alfven Mach number
of 5 and an exactly divergence-free initial state.

**Attribution warning.** The source and configuration record this case as a
project design; there is **no code or configuration citation to Tricco (2019)**.
The manuscript currently says the case is "adapted from" that work. Either
soften this to a statement that the smooth double-shear form follows the class
of smooth-profile MHD KH set-ups used in that literature, or drop the
attribution. Do not strengthen it. The Lecoanet et al. case is implemented
separately and is *not* the case shown in the Chapter 4 figure.

### 3.5 Literature comparisons that are safe to make

- **Brio--Wu.** The computed fp64 profiles reproduce the wave structure of the
  original solution — fast rarefaction, slow compound wave, contact
  discontinuity, slow shock, fast rarefaction — and are visually consistent with
  the figures in `\citep{brioWu1988}`. State this as qualitative agreement in
  wave structure, not as a quantitative accuracy claim.
- **Orszag--Tang.** The temperature field reproduces the interacting-shock and
  current-sheet topology of published calculations
  `\citep{toth2000divb,bardDorelli2014gpu}`.
- **Kelvin--Helmholtz.** `\citep{lecoanetEtAl2016kh}` is the standing warning
  that morphological agreement is not an accuracy measure for nonlinear KH
  evolution; `\citep{berlokPfrommer2019kh}` supplies the matched-initial-
  condition requirement for smooth linear comparisons;
  `\citep{frankEtAl1996kh}` covers the weak aligned-field regime, in which a
  field with Alfven Mach number 5 is too weak to suppress the instability but
  can still modify the nonlinear roll-up. Our single-mode, single-wavelength
  perturbation produces one vortex per layer, which is the expected qualitative
  outcome for that configuration.
- **Cross-code comparison.** `\citep{kritsukEtAl2011comparison}` compared nine
  MHD methods on common measures; `\citep{mignoneEtAl2007pluto,
  stoneEtAl2008athena,stoneEtAl2020athenapp}` are the independent-implementation
  targets.

## 4. Style requirements

- Academic English, present tense where it reads naturally for describing the
  method and the evidence; past tense is acceptable for what was measured.
- Write like a person, not like a model. No "it is important to note that", no
  "delve", no "leverage", no tricolon padding, no sentence that restates the
  previous sentence with different nouns. Vary sentence length. Do not open
  consecutive sentences with the same construction.
- Every number in the body must carry its case, baseline, metric and scope, but
  say it once — do not append a disclaimer to every sentence.
- Interpretation must be labelled as interpretation. Use "consistent with",
  "the likely reason is", "this points to" for mechanisms that were not
  isolated; reserve "shows" and "establishes" for what was measured directly.
- Explain jargon at first use, in the sentence, not in a parenthesis dump.
- British spelling, consistent with the existing text.

## 5. Reporting protocol for each writing agent

At the end of your task report:

1. The file you edited and the section label(s) you touched.
2. Your net word change, measured with
   `texcount -inc -sum <chapterfile>` before and after (report both numbers).
3. Every claim you added and the item in Section 3 of this brief that supports
   it.
4. Anything you could not do, and why. Never invent a number to fill a gap.
