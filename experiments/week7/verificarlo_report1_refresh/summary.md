# Verificarlo Report 1 Refresh Summary

Purpose: normalized Report 1 precision-sweep table after the 1600^2 reference refresh.

| solver | precision | samples | sigma_fp_l1 | s_worst_q05 | s_req | precision_margin | regime |
|---|---|---:|---:|---:|---:|---:|---|
| hllc | p8 | 2 | 1650.6 | 0.728032 | 3.07455 | -2.34652 | precision-adequacy deficit |
| hllc | p16 | 3 | 9.49699 | 1.53753 | 3.07455 | -1.53702 | precision-adequacy deficit |
| hllc | p24-real-float | 30 | 0.0295552 | 1.54217 | 3.07455 | -1.53238 | precision-adequacy deficit |
| hllc | p32 | 3 | 0.000142547 | 1.54217 | 3.07455 | -1.53238 | precision-adequacy deficit |
| hllc | p53 | 30 | 5.216e-11 | 1.54217 | 3.07455 | -1.53238 | precision-adequacy deficit |
| rusanov | p8 | 2 | 670.99 | 0.766484 | 2.8773 | -2.11082 | precision-adequacy deficit |
| rusanov | p16 | 3 | 4.12486 | 1.23056 | 2.8773 | -1.64674 | precision-adequacy deficit |
| rusanov | p24-real-float | 30 | 0.00819946 | 1.23019 | 2.8773 | -1.64711 | precision-adequacy deficit |
| rusanov | p32 | 3 | 6.01971e-05 | 1.23019 | 2.8773 | -1.64711 | precision-adequacy deficit |
| rusanov | p53 | 30 | 2.278e-11 | 1.23019 | 2.8773 | -1.64711 | precision-adequacy deficit |

p8/p16/p32 rows are exploratory virtual-precision rows with small sample counts.
Use `precision_margin = s_worst_q05 - s_req` as the precision-adequacy wording.
