# HLLD Diagnostic Figures

These PNGs are diagnostic figures for the Week 13 deferred-HLLD decision. They
support inspection of the HLL-vs-HLLD Orszag-Tang comparison, but they are not
production validation and do not adopt HLLD for subsequent precision-study
runs.

Inputs:

- `../ot_256_hll.bin`
- `../ot_256_hlld.bin`

Figures:

- `rho_hll_hlld_diff.png`: HLL density, HLLD density, and HLLD-HLL density.
- `divb_hll_hlld.png`: log10-scaled abs(divB) for HLL and HLLD.

Derived with periodic central differences from Bx/By using the binary header
spacing (`dx=0.00390625`, `dy=0.00390625`) to match the
Orszag-Tang periodic cfg.

Diagnostic values:

| metric | value |
|---|---:|
| grid | 256x256 |
| t | 0.5 |
| L1(rho) HLLD-HLL | 9.434e-02 |
| Linf(rho) HLLD-HLL | 8.460e-01 |
| mean abs(divB) HLL | 1.223e-01 |
| mean abs(divB) HLLD | 2.901e-01 |
| max abs(divB) HLL | 3.720e+00 |
| max abs(divB) HLLD | 3.429e+01 |
