# Week 7 Operational Plan

**Scope:** supervisor-response evidence for Report 1, kept inside the harness
discipline: `config -> build -> run -> measure -> aggregate -> plot`.

| Day | Priority |
|---|---|
| D1 | Freeze the Week 6 CPU/GPU strict baseline and draft the supervisor-response explanation skeleton. |
| D2 | Lock the precision-adequacy wording: regime criterion, degenerate denominators, noise-floor handling, and the Rusanov-cleaner trade-off explanation. |
| D3 | Build the drift time-series checks, including checkpoint-time compatibility tests and the smallest deterministic matrix dry-run. |
| D4 | Run the deterministic drift matrix locally, keeping synchronized final-state evidence and metadata rather than manual one-off comparisons. |
| D5 | Aggregate drift plus precision metrics, then write the interpretation that separates final-state drift from fitted growth-rate claims. |
| D6 | Add optional full Pareto supervisor artefacts; defer CSC/GPU extension unless the local matrix remains clean and reproducible. |
| D7 | Clean up large transient grids and assemble the final Report 1 evidence index for Week 7 supervisor-response material. |

## Deliverable Targets

- Supervisor-response log: terminology, denominator policy, Rusanov noise
  interpretation, drift interpretation, and Pareto explanation.
- Drift pipeline evidence: synchronized-time checks before comparing outputs.
- Pareto artefacts: full LW3 precision trade-off plot/data derived from
  existing Week 4 metrics, without rerunning Verificarlo.
- Cleanup pass: retain summaries, metadata, figures, and small CSV artefacts;
  remove large grids unless they are explicit reference data.
