# Week 14 Plan: MHD Precision Pilot

> Current evidence status is maintained in the [Report 2 evidence map](../experiment_logs/report2_evidence_map.md).

## Scope

Week 14 planned an HLL-first, CPU-only Brio-Wu 1D precision pilot following the
experiment harness flow: `config -> build -> run -> measure -> aggregate -> plot`.
The original design is [2026-07-01-week14-mhd-plan-design.md](../superpowers/specs/2026-07-01-week14-mhd-plan-design.md), and the operational plan is
[2026-07-01-week14-mhd-precision-pilot.md](../superpowers/plans/2026-07-01-week14-mhd-precision-pilot.md).

The later HLLD diagnostic extension is retained at
[experiments/week14/mhd_precision_pilot_hlld/summary.md](../../experiments/week14/mhd_precision_pilot_hlld/summary.md).
It is diagnostic provenance, not a production-default decision.

## Completion Status

| Item | Status | Routing |
|---|---|---|
| HLL CPU Brio-Wu deterministic/G0 pilot | executed | [Week 14 HLL summary](../../experiments/week14/mhd_precision_pilot/summary.md) |
| HLLD diagnostic extension | executed | [Week 14 HLLD summary](../../experiments/week14/mhd_precision_pilot_hlld/summary.md) |
| Week 14 pilot/smoke package | superseded | Replaced by the Week 15 24-variant and N=30 CPU packages. |
| Week 14 HLL MCA p24 interpretation | invalid | The instrumentation did not take effect; it is excluded from Report 2 claims. |
| GPU, hardware, 2D report-grade, and 512^2 work | deferred | See the [Report 2 evidence map](../experiment_logs/report2_evidence_map.md). |
