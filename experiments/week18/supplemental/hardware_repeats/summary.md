# Week 18 Hardware Repeats

- Gate pass: `True`
- Rows: `40`
- Schema: `hrsc.week18-supplemental` version `1`

| case | precision | repeats | CPU median (s) | GPU median (s) | speedup median | IQR | max ULP |
|---|---|---:|---:|---:|---:|---:|---:|
| brio_wu_1d | double | 5 | 0.162080 | 0.313989 | 0.5103 | 0.0299 | 0 |
| brio_wu_1d | float | 5 | 0.133630 | 0.273986 | 0.4877 | 0.0071 | 0 |
| orszag_tang_2d | double | 5 | 27.511403 | 4.456371 | 6.1735 | 0.4608 | 0 |
| orszag_tang_2d | float | 5 | 20.971179 | 3.536256 | 5.9246 | 0.0209 | 0 |
