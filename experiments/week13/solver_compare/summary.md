# Week 13 HLLD-vs-HLL Comparison (Orszag-Tang 256^2, t=0.5)

| metric | value |
|---|---:|
| L1(rho) HLLD-HLL | 9.434e-02 |
| Linf(rho) HLLD-HLL | 8.460e-01 |
| divB_max HLL | 3.720e+00 |
| divB_max HLLD | 3.429e+01 |
| HLLD finite | True |
| steps HLL | 806 |
| steps HLLD | 813 |

## Decision

- [ ] HLLD validated and adopted for remaining MHD work, OR
- [x] HLLD deferred; HLL remains the production solver (fallback per overall.md).

Rationale: HLLD completed the Orszag-Tang candidate run with a finite density
field, but its reported divB_max was 3.429e+01 versus 3.720e+00 for HLL on the
same grid/config. Keep HLL as the production solver for the next MHD precision
study step until the HLLD div(B) behavior is understood.

## Diagnostic figures

- `figures/rho_hll_hlld_diff.png`
- `figures/divb_hll_hlld.png`

These figures support the deferred-HLLD decision; they are not production
validation.
