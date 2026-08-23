# Lecoanet KH Linear-Reproduction Packet

This packet reproduces the smooth unstratified initial condition from Lecoanet et al. (2016) on `[0,1] x [0,2]` and measures the early `k=2*pi` transverse-velocity mode using the Tricco (2019) convolution.

It is an **initial-condition and early linear-growth reproduction**, not a reproduction of the nonlinear `Re=1e5` reference: the current solver does not include explicit viscosity, thermal diffusion, or passive dye.

- Grid: `256 x 512`; HLL FP64, periodic.
- Fitted growth rate: `2.731296`; literature linear value: `3.227`; relative difference: `15.361%`.
- Fit window: `t >= 0.25`; the earlier seed-adjustment transient is retained but excluded from the exponential fit.
- Log-linear fit R2: `0.990938`.
- Gate: `True` (strictly increasing positive mode in the declared fit window, finite positive state, positive finite fit with R2 >= 0.98).

| time | steps | mode amplitude | rho min | rho max |
|---:|---:|---:|---:|---:|
| 0.000 | 0 | 9.34088661e-03 | 1.00000000e+00 | 1.00000000e+00 |
| 0.250 | 814 | 8.29234775e-03 | 9.98178426e-01 | 1.00042469e+00 |
| 0.500 | 1628 | 1.39938630e-02 | 9.96256226e-01 | 1.00091052e+00 |
| 0.750 | 2443 | 2.83059376e-02 | 9.94519549e-01 | 1.00187447e+00 |
| 1.000 | 3259 | 6.38537550e-02 | 9.89812009e-01 | 1.00461424e+00 |

Sources: Lecoanet et al. (2016), DOI `10.1093/mnras/stv2564`; Tricco (2019), DOI `10.1093/mnras/stz2042`.
