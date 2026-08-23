# Lecoanet KH Linear-Reproduction Packet

This packet reproduces the smooth unstratified initial condition from Lecoanet et al. (2016) on `[0,1] x [0,2]` and measures the early `k=2*pi` transverse-velocity mode using the Tricco (2019) convolution.

It is an **initial-condition and early linear-growth reproduction**, not a reproduction of the nonlinear `Re=1e5` reference: the current solver does not include explicit viscosity, thermal diffusion, or passive dye.

- Grid: `128 x 256`; HLL FP64, periodic.
- Fitted growth rate: `2.193155`; literature linear value: `3.227`; relative difference: `32.037%`.
- Fit window: `t >= 0.25`; the earlier seed-adjustment transient is retained but excluded from the exponential fit.
- Log-linear fit R2: `0.989882`.
- Gate: `True` (strictly increasing positive mode in the declared fit window, finite positive state, positive finite fit with R2 >= 0.98).

| time | steps | mode amplitude | rho min | rho max |
|---:|---:|---:|---:|---:|
| 0.000 | 0 | 9.34009672e-03 | 1.00000000e+00 | 1.00000000e+00 |
| 0.250 | 407 | 8.05459796e-03 | 9.96509115e-01 | 1.00060207e+00 |
| 0.500 | 814 | 1.23242386e-02 | 9.94614186e-01 | 1.00086845e+00 |
| 0.750 | 1221 | 2.12930522e-02 | 9.93345851e-01 | 1.00148886e+00 |
| 1.000 | 1629 | 4.17459037e-02 | 9.90552788e-01 | 1.00297563e+00 |

Sources: Lecoanet et al. (2016), DOI `10.1093/mnras/stv2564`; Tricco (2019), DOI `10.1093/mnras/stz2042`.
