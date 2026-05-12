# Verificarlo Report 1 Refresh Audit

| precision | HLLC samples | Rusanov samples | status |
|---|---:|---:|---|
| p8 | 2 | 2 | exploratory; common subset |
| p16 | 3 | 3 | exploratory |
| p32 | 3 | 3 | exploratory |
| p24-real-float | 30 | 30 | Week 4/Athena metric source |
| p53 | 30 | 30 | Week 4/Athena metric source |

The refreshed Report 1 figures annotate sample counts. Do not present p8/p16/p32 as 30-sample production statistics.

For p8, the raw checkout has an extra Rusanov grid, but the analysed common subset used by the metrics and figures is n=2 per solver.
