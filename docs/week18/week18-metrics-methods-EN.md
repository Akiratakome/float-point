# Week 18 Metric Definitions and Interpretation

> This appendix defines every numerical and performance indicator used in the Week 18 supervisor report. The purpose is to make each number reproducible and to prevent a metric from supporting a broader claim than its definition allows.

## 1. Notation and primitive fields

A saved MHD cell contains the conserved state

\[
U=(\rho,\rho v_x,\rho v_y,\rho v_z,B_x,B_y,B_z,E,\psi).
\]

The report compares physically interpretable primitive fields. For every cell:

\[
v_x=(\rho v_x)/\rho,
\qquad
p=(\gamma-1)\left[E-\tfrac12\rho(v_x^2+v_y^2+v_z^2)-\tfrac12(B_x^2+B_y^2+B_z^2)\right].
\]

`rho` and `By` are read directly from conserved components 0 and 5. This conversion is implemented in `scripts/metrics/mhd_fields.py`. Comparing primitive fields is preferable to comparing total energy alone because density, velocity, magnetic field, and pressure have direct physical interpretations.

## 2. Deterministic FP32-versus-FP64 differences

For a field `q` on the same grid and at the same final time, define the pointwise difference

\[
d_j=q^{FP32}_j-q^{FP64}_j,
\]

where `j` indexes cells. FP64 is a project baseline, not an exact solution.

The standard discrete summaries are:

\[
L_{1,mean}=\frac{1}{N_c}\sum_j |d_j|,
\qquad
L_{2,RMS}=\sqrt{\frac{1}{N_c}\sum_j d_j^2},
\qquad
L_\infty=\max_j |d_j|.
\]

- `L1_mean` answers: what is the typical absolute cell error?
- `L2_RMS` gives more weight to moderately large errors while remaining a global summary.
- `Linf` answers: what is the worst local difference anywhere in the domain?

The new CSC triangulation and KH timing figures use `Linf`, because local extrema matter in shock/shear problems and the value is independent of how many cells are summed. The 256-versus-512 engineering gates in `mhd_kh_2d.py` and `mhd_orszag_tang_2d.py` use the mean/RMS definitions above after block-averaging the fine grid.

Historical deterministic precision packets call `scripts/metrics/mhd_fields.py::field_norms`, whose `L1` and `L2` use the repository's earlier `sum*dx` convention. Those values are valid only for the same-grid comparisons for which they were generated and must not be mixed with mean-normalised cross-resolution values. Report headlines therefore use `Linf` when combining packets.

## 3. ULP distance and bitwise reproducibility

ULP means “unit in the last place.” For two arrays with the same dtype, their IEEE bit patterns are transformed into a monotonically ordered integer representation and the absolute integer distance is computed cell by cell:

\[
ULP_{max}=\max_j |I(a_j)-I(b_j)|.
\]

The sign-bit transformation in `scripts/regression/mhd_gpu_hardware_axis.py::max_ulp_distance` preserves numerical ordering across negative and positive values.

- `0 ULP` means every stored floating-point value is bit-for-bit identical.
- A nonzero ULP value measures representational distance at the field value's local exponent; it is not a physical error norm.

ULP is used for same-precision CPU/GPU, thread-count, and repeated-run checks. It is not used for FP32-versus-FP64 because those arrays have different formats.

## 4. MCA spread and SNR

For `n` Verificarlo samples of field `q`, compute per-cell sample mean and unbiased sample standard deviation:

\[
\mu_j=\frac{1}{n}\sum_{s=1}^{n}q_{s,j},
\qquad
\sigma_j=\sqrt{\frac{1}{n-1}\sum_{s=1}^{n}(q_{s,j}-\mu_j)^2}.
\]

The reported MCA spread is

\[
spread_q=\max_j \sigma_j.
\]

It reports the largest stochastic-rounding sensitivity anywhere in the domain. The maximum is deliberately conservative for shocks and shear layers, where a spatial average can hide a small unstable region.

The CSC smoke SNR is

\[
SNR_q=\frac{mean_j(|\mu_j|)}{mean_j(\sigma_j)},
\]

with `sqrt(eps_float64)` used only when the denominator is exactly zero. Larger SNR means the field magnitude is large relative to MCA variability. This is a numerical signal-to-noise ratio, not an observational or physical turbulence SNR.

The density-mean spread is

\[
\max_s mean_j(\rho_{s,j})-\min_s mean_j(\rho_{s,j}),
\]

which checks whether stochastic arithmetic changes the domain-average density.

These calculations are implemented in `scripts/metrics/mhd_fields.py`; per-cell standard deviation uses `ddof=1` in `scripts/metrics/snr_metric.py`. With only N=4 CSC smoke samples, spread and SNR validate direction and toolchain operation but do not support tight confidence intervals.

## 5. Precision and solver ratios

The p24/p53 amplification is

\[
A_q=spread_q^{p24}/spread_q^{p53},
\qquad
D_q=\log_{10}(A_q).
\]

`Aq` is a noise amplification factor; `Dq` states how many decimal orders of magnitude separate the two spreads. It does not by itself equal digits lost in the physical solution.

The HLLD/HLL p24 ratio is

\[
R_q=spread_{q,HLLD}^{p24}/spread_{q,HLL}^{p24}.
\]

It isolates solver-path sensitivity at the same case, grid, final time, backend, virtual precision, and sample count. It supports only a bounded solver comparison.

The deterministic/MCA triangulation ratio is

\[
T_q=L_\infty(q_{FP32}-q_{FP64})/spread_q^{p24}.
\]

A value near one means two independent methods identify the same numerical scale. Equality is not expected because deterministic rounding difference and stochastic sample spread are different estimators.

## 6. Runtime statistics

The harness measures subprocess wall time from solver launch through completion and required binary output. It is an end-to-end experiment time, not a kernel-only microbenchmark.

For each solver/precision group, one warm-up is excluded and five measured times `t1...t5` are retained. The report uses:

\[
t_{med}=median(t_i),
\qquad
IQR=Q_{75}(t_i)-Q_{25}(t_i).
\]

The figure draws asymmetric error bars from Q25 to Q75. Median and IQR are used because wall times can be skewed by operating-system scheduling and five samples do not justify a normal-distribution assumption.

Performance ratios are:

\[
S_{FP32}=t_{med,FP64}/t_{med,FP32},
\qquad
C_{HLLD}=t_{med,HLLD}/t_{med,HLL}.
\]

A value above one means FP32 is faster in the first ratio, or HLLD is more expensive in the second. CPU/GPU speed-up uses the analogous `CPU median/GPU median` definition.

All timing comparisons require the same case, grid, final time, CFL, thread count, and output path semantics. The KH timing experiment fixes `OMP_NUM_THREADS=1`, `256^2`, `t=1.0`, and CFL=0.4. Five repeats on one workstation do not imply portable performance on another CPU.

## 7. Solver diagnostics and gates

### Physical-state gate

A run is usable only if all conserved values are finite and

\[
\min_j \rho_j>0,
\qquad
\min_j p_j>0.
\]

This detects NaN/Inf, negative density, and negative pressure. Passing means the output is admissible for comparison; it does not prove accuracy.

### Step count

`steps` is the number of CFL-controlled timesteps required to reach `t_end`. Equal step counts remove one confounder when precision or solver timings are compared. Step count is not itself an error metric.

### Magnetic divergence

The code uses centred interior differences:

\[
(\nabla\cdot B)_{i,j}=\frac{B_{x,i+1,j}-B_{x,i-1,j}}{2\Delta x}+\frac{B_{y,i,j+1}-B_{y,i,j-1}}{2\Delta y}.
\]

`divB_mean` is the interior mean of its absolute value and `divB_max` is the interior maximum. This checks the discrete solenoidal constraint and is implemented in `src/utils/error_norms.hpp`. It is a diagnostic of magnetic consistency, not FP32/FP64 error.

### Relative mass error

For periodic validation cases:

\[
mass_{rel}=|M(t)-M(0)|/|M(0)|.
\]

It checks conservation. A small value does not imply pointwise accuracy.

### Gate pass

A gate is a logical conjunction of matrix completeness, successful process exit, physical-state checks, required diagnostics, and experiment-specific thresholds. It means the evidence packet satisfies its predeclared acceptance contract. It does not mean every possible scientific claim is true.

## 8. Temporal-divergence fit

For positive FP32/FP64 error samples in the fixed preregistered time window, the temporal experiment fits

\[
\log e(t)=a+\lambda t
\]

by least squares. `lambda` is therefore a bounded Lyapunov-like engineering slope. It is not a formal maximal Lyapunov exponent because the perturbation, norm, time window, and nonlinear regime are fixed by this numerical experiment.

## 9. Interpretation rule

Use each metric only for the question it answers:

| Question | Primary metric | Why |
|---|---|---|
| Are two same-precision outputs identical? | max ULP | Exact representational comparison |
| How large is the worst FP32/FP64 local change? | Linf | Conservative local bound |
| What is the typical same-grid difference? | mean L1 / RMS L2 | Domain-wide magnitude |
| How sensitive is the computation to stochastic rounding? | MCA spread and SNR | Sample variability per cell before spatial aggregation |
| Is the result faster? | median wall time, IQR, speed-up | Robust repeated end-to-end timing |
| Is the MHD state admissible? | finite, rho_min, p_min | Necessary physical sanity checks |
| Is magnetic divergence controlled? | divB_mean, divB_max | Discrete solenoidal diagnostic |
| Has the full scientific conclusion been established? | experiment gate plus claim boundary | Prevents smoke or validation evidence from being over-promoted |