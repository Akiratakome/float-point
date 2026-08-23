# Lecoanet KH Linear-Reproduction Packet

This packet reproduces the smooth unstratified initial condition from Lecoanet et al. (2016) on `[0,1] x [0,2]` and measures the early `k=2*pi` transverse-velocity mode using the Tricco (2019) convolution.

It is an **initial-condition and early linear-growth reproduction**, not a reproduction of the nonlinear `Re=1e5` reference: the current solver does not include explicit viscosity, thermal diffusion, or passive dye.

- Grid: `64 x 128`; HLL FP64, periodic.
- Fitted growth rate: `1.078761`; literature linear value: `3.227`; relative difference: `66.571%`.
- Fit window: `t >= 0.25`; the earlier seed-adjustment transient is retained but excluded from the exponential fit.
- Log-linear fit R2: `0.964822`.
- Gate: `False` (strictly increasing positive mode in the declared fit window, finite positive state, positive finite fit with R2 >= 0.98).

| time | steps | mode amplitude | rho min | rho max |
|---:|---:|---:|---:|---:|
| 0.000 | 0 | 9.33688409e-03 | 1.00000000e+00 | 1.00000000e+00 |
| 0.250 | 204 | 7.40768864e-03 | 9.93086259e-01 | 1.00116417e+00 |
| 0.500 | 407 | 9.20979635e-03 | 9.91078442e-01 | 1.00170771e+00 |
| 0.750 | 611 | 1.12025241e-02 | 9.90166297e-01 | 1.00246319e+00 |
| 1.000 | 814 | 1.70507778e-02 | 9.88821881e-01 | 1.00245885e+00 |

Sources: Lecoanet et al. (2016), DOI `10.1093/mnras/stv2564`; Tricco (2019), DOI `10.1093/mnras/stz2042`.
