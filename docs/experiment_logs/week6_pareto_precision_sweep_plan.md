# Week 7 Pareto Precision Sweep Plan

Goal: extend the full Pareto example beyond the currently validated p53 and
p24-real-float rows, adding real A4 LW Config 3 points for p32, p16, and p8.

Current status:

- `scripts/figures/pareto_full_example.py` plots any precision labels supplied
  through a normalized input CSV.
- The default Week 4 metric CSVs currently contain the validated p53 and
  p24-real-float headline rho rows used by the Week 7 example.
- No p32, p16, or p8 A4 metric rows are currently checked in, so the published
  Week 7 figure must not show those labels until the corresponding runs exist.

Required rows for each new precision label:

- `solver`: `hllc` and `rusanov`
- `precision_label`: recommended labels `p32`, `p16`, and `p8`
- `variable`: `rho`
- `sigma_fp_l1`: from the same A4 emitted-noise aggregation path as
  `experiments/week4/metrics/a4_snr_with_float.csv`
- `s_worst_q05`: from the same losos aggregation path as
  `experiments/week4/metrics/a4_losos_with_float.csv`
- `s_req`: reuse the LW Config 3 N=200 truncation requirement in
  `experiments/week4/metrics/s_req_lw_config3_200.csv`

Execution notes:

- Keep solver numerics and existing cfg defaults unchanged.
- Run the extra precision cases through the existing
  `config -> build -> run -> measure -> aggregate -> plot` harness path.
- Store configs, command logs, seeds, replicate counts, and summary metadata
  beside the generated metrics.
- Keep transient grid files out of git; only commit small metric CSVs, figures,
  logs, and summaries.

Plot integration:

1. Append the new p32, p16, and p8 rows to a normalized Pareto input CSV with
   columns:
   `solver,precision_label,sigma_fp_l1,s_worst_q05,s_req,regime`.
2. Generate the figure with:
   `python scripts/figures/pareto_full_example.py --input <csv> --output experiments/week7/pareto_full`.
3. If the rows are added to the Week 4 metric CSVs instead, request them with:
   `python scripts/figures/pareto_full_example.py --output experiments/week7/pareto_full --precisions p53,p32,p24-real-float,p16,p8`.
4. Treat a missing-row error as a data gap, not a plotting bug.

