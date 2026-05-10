# Full Pareto Example For Philip

The plot demonstrates the trade-off between emitted FP noise (sigma_FP_L1, x-axis) and delivered significant digits (s_worst_q05, y-axis). The s_req(N) target marks the significant digits implied by truncation error at the same grid resolution.

Log scaling is required because p24-real-float and p53 differ by many orders of magnitude in emitted noise. The two-panel view separates the delivered digits from the precision-adequacy margin s_worst_q05 - s_req(N), avoiding ambiguous round-off-limited wording.

Included precision labels: p8, p16, p24-real-float, p32, p53.

Precision-adequacy margins in this input range from -2.40 to -1.59.
The plotted p24-real-float noise is about 1.30e+09 times the quietest p53 noise.
