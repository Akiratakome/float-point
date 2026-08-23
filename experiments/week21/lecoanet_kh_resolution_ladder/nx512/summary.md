# Lecoanet KH Linear-Reproduction Packet

This packet reproduces the smooth unstratified initial condition from Lecoanet et al. (2016) on `[0,1] x [0,2]` and measures the early `k=2*pi` transverse-velocity mode using the Tricco (2019) convolution.

It is an **initial-condition and early linear-growth reproduction**, not a reproduction of the nonlinear `Re=1e5` reference: the current solver does not include explicit viscosity, thermal diffusion, or passive dye.

- Grid: `512 x 1024`; HLL FP64, periodic.
- Fitted growth rate: `2.888236`; literature linear value: `3.227`; relative difference: `10.498%`.
- Fit window: `t >= 0.25`; the earlier seed-adjustment transient is retained but excluded from the exponential fit.
- Log-linear fit R2: `0.990477`.
- Gate: `True` (strictly increasing positive mode in the declared fit window, finite positive state, positive finite fit with R2 >= 0.98).

| time | steps | mode amplitude | rho min | rho max |
|---:|---:|---:|---:|---:|
| 0.000 | 0 | 9.34108326e-03 | 1.00000000e+00 | 1.00000000e+00 |
| 0.250 | 1628 | 8.34659408e-03 | 9.98861418e-01 | 1.00051104e+00 |
| 0.500 | 3256 | 1.44292461e-02 | 9.97062701e-01 | 1.00172750e+00 |
| 0.750 | 4885 | 3.04979378e-02 | 9.95240873e-01 | 1.00289370e+00 |
| 1.000 | 6520 | 7.21862637e-02 | 9.89580433e-01 | 1.00666723e+00 |

Sources: Lecoanet et al. (2016), DOI `10.1093/mnras/stv2564`; Tricco (2019), DOI `10.1093/mnras/stz2042`.
