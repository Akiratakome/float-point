# Report 2 deterministic + MCA precision gate

Source-integrity audit pass: `True`. Same-scope promotion: `2/4`.

| case | solver | deterministic scope | MCA scope | det. rows | MCA samples | status |
|---|---|---|---|---:|---:|---|
| Brio-Wu | HLL | 800, t=0.1 | 800, t=0.1 | 24 | 30+30 | `report-grade` |
| Brio-Wu | HLLD | 800, t=0.1 | 800, t=0.1 | 24 | 30+30 | `report-grade` |
| Orszag-Tang | HLL | 256x256, t=0.5 | 64x64, t=0.05 | 24 | 30+30 | `provisional-reduced-scope` |
| Orszag-Tang | HLLD | 256x256, t=0.5 | 64x64, t=0.05 | 24 | 30+30 | `provisional-reduced-scope` |

## Review conclusion

- Brio-Wu HLL and HLLD pass a same-configuration deterministic-plus-MCA gate and can be treated as report-grade bounded precision evidence.
- Orszag-Tang HLL and HLLD have complete source packets, but the reduced 64x64/t=0.05 MCA runs do not close the 256x256/t=0.5 deterministic evidence. They remain provisional.
- OT deterministic and MCA magnitudes must not be ratioed or combined as if they came from one configuration.

This audit establishes packet completeness and scope alignment only; it is not an exact-solution accuracy test or a universal solver/precision ranking.
