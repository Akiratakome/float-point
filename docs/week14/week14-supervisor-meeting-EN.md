# Week 14 Supervisor Meeting
> **Historical snapshot:** This dated meeting document preserves what was known
> at the time. It is not the current Report 2 status. See
> [report2_evidence_map.md](../experiment_logs/report2_evidence_map.md) for
> current evidence, supersession, and claim boundaries.

> Generated 2026-07-02. Figures live under `experiments/week14/`; all numbers were cross-checked
> against each experiment's `summary.json`. Everything this week was run on the **cheapest case —
> Brio–Wu 1D (a 1D MHD shock tube) + the HLL solver + CPU only** — to quantify how much
> floating-point precision actually matters, as groundwork for Report 2.

---

## One-line summary

This week produced **three experiment groups, six figures**, answering "is our solution right, and how
much do precision / compiler / threading each matter"; along the way we **found and fixed a real bug** —
the Verificarlo low-precision sampling was never actually taking effect, which is why p24 and p53 looked
identical. After the fix, p24 finally separates from p53.

---

## What we actually did

1. **Check the baseline**: plot the Brio–Wu profile and compare its shape to the classic Brio & Wu (1988) result.
2. **Quantify precision effects**: same case, vary precision (float/double), compiler optimisation (O2/Ofast),
   and one inequality in the solver (`<=` / `<`), and measure the point-wise difference.
3. **Three supplemental experiments**: can mesh refinement rescue float, does error drift grow with run time,
   are results identical across threads.
4. **Stochastic-rounding noise floor**: use Verificarlo to perturb every FP op and see how many significant
   digits survive — **and this is where we caught and fixed a precision-setting bug**.

---

## The six figures: how to read them, what they show

Each figure starts with a **one-line takeaway**, then **how to read it**.

### A — Is our solution right? `mhd_precision_pilot/literature_validation/brio_wu_reference_profile.png`

- **One line**: our Brio–Wu result reproduces the textbook/paper wave structure — the shape is correct.
- **How to read**: four curves (density, x-velocity, y-magnetic-field, pressure) vs position x, at t=0.1, grid 800.
  You can see Brio–Wu's signature features: the small density "hump" (~0.83, the compound wave), the middle plateau,
  the contact discontinuity and fast rarefaction on the right; the y-field flips from +1 to −0.5 to −1. These match
  Brio & Wu (1988).
- **Boundary**: this is a **morphology-level** (benchmark shape) match, not a point-wise comparison to an exact
  solution — Brio–Wu has no simple closed-form solution, and the literature even warns its Riemann problem is
  non-unique (Takahashi & Yamada 2012). So the claim is "reproduces the standard benchmark's wave pattern," not
  "agrees point-wise with an exact solution."

### B — Precision vs compiler vs solver-branch: which matters most? `mhd_precision_pilot/figures/deterministic_norms.png`

- **One line**: **precision (float vs double) dominates overwhelmingly**; compiler optimisation barely matters; the
  `<=`/`<` inequality makes no difference at all on this case.
- **How to read**: four subplots (density/By/pressure/vx), y-axis is "error vs the double baseline" (log scale),
  x-axis is the 7 variants. The shape is a **big step**: the double variants sit very low (~1e-15, essentially the
  double-precision limit), then the float variants jump up by ~9 orders of magnitude to ~1e-6 and stay flat.
- **Three specifics**:
  1. float lands at ~1e-6 immediately, ~a billion times larger than double — **precision is the dominant factor**.
  2. O2 → Ofast adds only ~1e-15 jitter (operation reordering); negligible.
  3. `<=` → `<` (a wave-speed boundary case in the solver) — **every pair is bit-identical**, so that branch is never
     triggered on Brio–Wu and doesn't affect the result.
- **Boundary**: this compares to *our own* double baseline — an engineering-consistency check, not a validation
  against an exact solution.

### C — Can mesh refinement rescue float precision? `mhd_supplemental/resolution_ladder/figure.png`

- **One line**: **No.** float error hits a "floor" that no amount of refinement beats; double keeps converging.
- **How to read**: x-axis is grid count nx (200/400/800/1600), y-axis is "L1 error vs reference". The orange line
  (float) is essentially flat (stuck around ~10⁻³); the blue line (double) keeps dropping with nx, reaching ~0 at
  the reference resolution.
- **What it shows**: refining the mesh reduces discretisation error but **cannot remove float round-off** — once
  round-off exceeds discretisation error, paying for finer meshes is wasted. This is the key argument for
  "should we trade accuracy for float's speed?"
- **Caveat (a figure problem)**: the y-axis runs down to 10⁻²⁸¹ because the reference-resolution point underflows to
  ~0 and wrecks the scale, making it hard to read. **Worth re-plotting** (drop/clip the reference point); I can do that.

### D — Does error snowball the longer we run? `mhd_supplemental/time_sliced_drift/figure.png`

- **One line**: **Yes, but only for float.** float error grows steadily with simulation time; double stays at 0.
- **How to read**: x-axis is end time t_end (0.02→0.10), y-axis is By error. The two double lines (O2, Ofast) sit at 0;
  the two float lines (O2, Ofast) climb from ~2.5e-7 to ~1.5e-6.
- **What it shows**: float round-off **accumulates and drifts over time** — worse the longer you run; double shows no
  visible drift over this window. Long-time integration in float must account for this drift.

### E — Do threads change the result? `mhd_supplemental/thread_repro/figure.png`

- **One line**: **No** — 1/2/4/8 threads give bit-identical results; fully reproducible.
- **How to read**: x-axis is thread count OMP_NUM_THREADS (1/2/4/8), y-axis is "error vs the single-thread result" —
  it is exactly 0 everywhere.
- **What it shows**: parallelism introduces no nondeterminism (no "summation-order jitter"); results are deterministic.
  Strong backing for experiment reproducibility.

### F — How many significant digits survive + the bug we fixed: `mhd_precision_pilot/figures/mca_noise_floor.png`

- **One line (before the fix — i.e. the currently committed figure)**: p24 and p53 are almost the same height —
  **that is itself the symptom of the bug**.
- **How to read**: left = "result spread" at each precision (lower = more stable, more significant digits),
  right = signal-to-noise ratio. The two groups (p24 = float surrogate, p53 = double) are nearly equal (~5e-15).
- **What we should have seen**: p53 (double) spread ~5e-15 (≈ machine precision, normal); p24 (emulating float's
  24-bit precision) **should** be ~1e-7 (2⁻²⁴). Both being equal means the "lower precision" never took effect.
- **Root cause (nailed this week)**: the sampler set precision via the old Verificarlo env var
  `VFC_MCA_PRECISION_BINARY64=24`, but this project runs **Verificarlo 2.5.1**, whose backend only honours the
  command-line arg `--precision-binary64=24` and **silently ignores that env var**. So both p24 and p53 ran at the
  default 53-bit precision → of course they matched.
- **Fix**: put precision into the backend argument (consistent with every other Verificarlo runner in the repo):
  `VFC_BACKENDS='libinterflop_mca.so --mode=mca --precision-binary64=24'`. Wrote a failing test first to reproduce
  the bad command, then fixed it; **11 unit tests pass**.
- **Re-run confirmation (post-fix, 4 samples)**: p24 density spread jumped from 5.4e-15 to **9.3e-7** (~8 orders of
  magnitude higher, exactly the 2⁻²⁴ ≈ single-precision scale), SNR ≈ 7.5e6 (~7 significant digits, exactly what
  single precision should give); p53 stays at **5.2e-15** (machine precision, unchanged). They now clearly separate —
  **the fix works**. p24's 9.3e-7 also matches the deterministic float error (~1e-6 in figure B), so the two methods
  corroborate each other. (Official 8-sample evidence and `mca_noise_floor.png` still to be refreshed — see below.)

---

## What we can tell the supervisor (and what we won't)

**Can say**:

- Brio–Wu HLL runs, is finite, and reproduces the Week-14 reference anchor (759 steps, divB bound 4.4e-14).
- The waveform reproduces the classic Brio & Wu (1988) structure.
- Precision is the dominant factor for the solution (~9 orders of magnitude); compiler optimisation is negligible;
  the solver's inequality branch makes no difference.
- float has an "accuracy floor" (mesh refinement can't beat it) and its error drifts with time; double is stable and
  bit-reproducible across threads.
- Stochastic-rounding noise floor: double sits at machine precision — **and we fixed the bug that stopped
  low-precision sampling from taking effect this week**.

**Won't say** (avoid over-claiming):

- No claim of point-wise agreement with an exact Riemann solution; no claim that HLLD is superior or production-ready;
- No 2D / GPU / larger-scale (P1/P2) conclusions.

---

## Next steps

1. **Refresh the official MCA evidence**: re-sample 8 samples with the fixed sampler, update `mca_noise_floor.png` and
   `summary.json` so the real p24/p53 separation lands in the official figure.
2. **Re-plot the resolution-ladder figure** (C) to fix the y-axis wrecked by the underflow point.
3. (Optional, Week 15+) point the same pipeline at OT / KH 2D and close the 512² convergence gates.

---

## References

- Brio & Wu (1988), *JCP* 75, 400, DOI `10.1016/0021-9991(88)90120-9` — 1D ideal-MHD shock-tube benchmark.
- Stone et al. (2008), Athena code paper, arXiv:0804.0402 — modern MHD code test-suite context.
- Mignone et al. (2007), PLUTO code paper, arXiv:astro-ph/0701854 — Godunov shock-capturing benchmark context.
- Takahashi & Yamada (2012), arXiv:1210.5584 — caution on Brio–Wu Riemann-problem non-uniqueness.
