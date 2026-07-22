# Report 2 Evidence Map

> Current status authority for Report 2. Requirements and dated meeting reports
> are historical inputs; experiment summaries remain the numerical authority.
> Last audited: 2026-07-22 on `week16-evidence-completion`.

## Status vocabulary

| Status | Meaning |
|---|---|
| `report-grade` | Machine-readable gate and evidence package support the bounded claim. |
| `provisional` | Data exist, but the authoritative gate or combined summary is incomplete. |
| `validation` | Supports solver/method correctness, not a precision-axis headline claim. |
| `morphology-only` | Supports qualitative benchmark structure only. |
| `negative-result` | A gated analysis did not observe the planned contrast; report the bounded result. |
| `invalid` | Known configuration or instrumentation defect prevents evidential use. |
| `superseded` | Replaced by a named stronger package; retained only for provenance. |
| `deferred` | Planned Report 2 work not yet implemented. |

A status applies only to the bounded claim in the same inventory row. It does
not promote a related solver, case, precision axis, or retained asset.

## Evidence inventory

All paths below are repository-relative. `Tracked` means a committed authority;
`local ignored` means retained outside Git; `transient` means grids are not a
durable evidence product.

| Evidence | Status | Authority and sample/resolution facts | Supported claim | Excluded claim | Superseded assets | Retention |
|---|---|---|---|---|---|---|
| Week 12 Brio-Wu 1D | `validation` | `experiments/week12/brio_wu_1d/summary.md`; HLL Brio-Wu, N=200/400/800 candidates against block-averaged aligned N=8000 double reference. | The 1D MHD implementation has monotonic L1/L2 convergence on this validation setup. | A Report 2 precision headline or an exact MHD-solution precision error. | Earlier walking-skeleton output is not a current precision package. | Tracked summary; referenced grids are provenance/transient. |
| Week 12 2D invariance/GLM | `validation` | `experiments/week12/mhd_2d/brio_wu_2d/summary.md` and `experiments/week12/mhd_2d/divb_clean/summary.md`; transverse-invariance and div(B)-decay gates. | The 2D extension preserves the tested invariant state and the GLM cleaning diagnostic decays as gated. | OT/KH precision adequacy, convergence, or hardware evidence. | None. | Tracked summaries and figure grids. |
| Week 13 HLLD divB follow-up | `validation` | `experiments/week13/hlld_divb_followup/summary.md`; 128^2 and 256^2 OT follow-up, including HLLD 256^2 t=0.5: 812 steps, divB_mean=0.274, divB_max=24.45. | HLLD's apparent issue was a stale-binary interpretation; remaining div(B) is resolution-consistent and localized at current sheets. | HLLD precision sensitivity, production-default status, or CPU/GPU equivalence. | The stale-binary Week 13 interpretation. | Tracked summary and diagnostic provenance. |
| Week 13 OT morphology | `morphology-only` | `experiments/week13/orszag_tang/paper_summary.md`; local 256^2 HLL OT at t=0.5, 806 steps. | The 256^2 HLL result supplies paper-grounded OT morphology. | A completed 512^2 self-reference gate, precision claim, or asymptotic convergence. | None. | Tracked summary and figures; no retained report-grade reference grid. |
| Week 13 KH morphology | `morphology-only` | `experiments/week13/kelvin_helmholtz/paper_summary.md`; local 256^2 HLL KH at t=1.0, 1148 steps. | The result supplies KH morphology. | A precision claim, completed 512^2 self-reference gate, or convergence claim. | None. | Tracked summary and figures. |
| Week 14 HLL MCA | `invalid` | `experiments/week14/mhd_precision_pilot/summary.md`; nominal p24/p53 N=8 Docker MCA rows. | No Report 2 evidential claim. | Any p24 noise/spread interpretation: p24 instrumentation did not take effect. | Replaced by Week 15 HLL N=30 p24/p53 MCA in `experiments/week15/brio_wu_precision_pilot_p1/summary.md`. | Tracked historical summary; retain for diagnosis only. |
| Week 14 pilots/smokes | `superseded` | `experiments/week14/mhd_precision_pilot/summary.md` and `experiments/week14/mhd_precision_pilot_hlld/summary.md`; eight deterministic variants and N=8 MCA probes. | Development provenance, including the deterministic G0 pilot. | Report-grade deterministic/MCA conclusions. | Week 15 24-variant, N=30 Brio-Wu packages; Week 14 HLL MCA is also invalid. | Tracked summaries; development assets retained. |
| Week 15 Brio-Wu HLL | `provisional` | `experiments/week15/brio_wu_precision_pilot_p1/summary.md`; 24 deterministic CPU variants plus Docker Verificarlo p53 and p24 N=30. | Bounded CPU HLL deterministic and MCA observations against the project baseline. | A unified Report 2 precision gate or exact MHD-solution error. | Week 14 HLL pilot and invalid N=8 MCA interpretation. | Tracked summary/figures; run artefacts are provenance. |
| Week 15 Brio-Wu HLLD | `provisional` | `experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.md`; 24 deterministic CPU variants plus Docker Verificarlo p53 and p24 N=30. | Bounded CPU HLLD deterministic and MCA observations against the project baseline. | A unified Report 2 precision gate, production-default promotion, or exact MHD-solution error. | Week 14 HLLD pilot/smoke. | Tracked summary/figures; run artefacts are provenance. |
| Week 15 OT HLL | `provisional` | `experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.md`; 24 deterministic 256^2 CPU variants, G0 pass, 806-step reference. MCA authority is separate: `experiments/week15/orszag_tang_precision_smoke/mca_n30/summary.json`. | Bounded deterministic HLL sensitivity and separate N=30 MCA observations. | One unified deterministic-plus-MCA gate, exact-reference accuracy, or 512^2 convergence. | Week 15 gate128/headline smoke packages and the 2026-07-02 OT plan. | Tracked summaries/JSON/figures; sampled outputs are local or transient. |
| Week 15 OT HLLD | `provisional` | `experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.md`; 24 deterministic 256^2 CPU variants, G0 pass, 812-step reference. MCA authority is separate: `experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/summary.json`. | Bounded deterministic HLLD sensitivity and separate N=30 MCA observations. | One unified deterministic-plus-MCA gate, production-default promotion, exact-reference accuracy, or 512^2 convergence. | Week 15 gate128/headline smoke packages and the 2026-07-02 OT plan. | Tracked summaries/JSON/figures; sampled outputs are local or transient. |
| Temporal divergence | `negative-result` | `experiments/week15/mhd_temporal_divergence/summary.md`; 80 successful provenance-complete runs, Brio-Wu 15 paired samples over [0.01, 0.1], OT 25 over [0.1, 0.5]. | Fixed-window fp32-vs-fp64 Lyapunov-like engineering fits; the planned OT > Brio-Wu contrast was not observed. | A formal maximal Lyapunov exponent, a physical instability rate, or general OT/KH ordering. | `experiments/week15/mhd_temporal_divergence_smoke/summary.md` is smoke provenance only. | Tracked summary/figure; configs, stdout/stderr logs, and metadata are local ignored; grids are transient and removed. |
| GPU HLL MHD | `deferred` | `docs/superpowers/specs/2026-07-09-gpu-mhd-hll-design.md` and `docs/superpowers/plans/2026-07-09-gpu-mhd-hll.md`; no implementation package. | The scoped GPU work is planned. | GPU HLL MHD correctness, precision, or performance. | None. | Tracked design/plan only. |
| CPU/GPU hardware axis | `deferred` | Depends on validated GPU HLL MHD and a matched CPU/GPU evidence package. | The dependency and missing evidence are explicit. | Any hardware conclusion. | None. | Deferred; no Report 2 hardware asset. |
| KH report-grade precision | `deferred` | Current authority remains `experiments/week13/kelvin_helmholtz/paper_summary.md`, a 256^2 morphology packet. | KH morphology is available. | KH precision sensitivity or report-grade validation. | None. | Tracked morphology material; report-grade package deferred. |
| OT/KH 512^2 consolidation | `deferred` | Week 13 OT/KH summaries identify 512^2 self-reference work as pending. | Two-resolution sensitivity can be assessed only after the complete 256^2/512^2 packages exist. | Asymptotic convergence from two resolutions. | None. | Deferred; no completed consolidated package. |

## Current Report 2 claim boundaries

- Precision effects are measured against project baselines, not exact MHD solutions.
- HLLD is an analysed CPU solver but is not silently promoted to the production default.
- Temporal rates are bounded Lyapunov-like engineering fits.
- A formal maximal Lyapunov exponent is not claimed.
- The planned OT > Brio-Wu contrast was not observed.
- GPU and hardware conclusions are unavailable.
- KH supports morphology only.
- Two resolutions do not establish asymptotic convergence.

The temporal package has a technical and report-grade gate for its bounded
engineering analysis, but its row remains `negative-result` because the planned
cross-case contrast was not observed. The four Week 15 Brio-Wu/OT
deterministic-plus-MCA rows remain `provisional` until a machine-readable
unified gate and authoritative combined summary exist.

## Plan and retention routing

| Planning asset | Current routing | Scope |
|---|---|---|
| `docs/superpowers/specs/2026-07-21-week15-16-completion-design.md` | `partially executed` | Temporal phase completed; GPU HLL MHD, hardware-axis evidence, KH report-grade precision, and 512^2 consolidation remain deferred. |
| `docs/superpowers/specs/2026-07-09-gpu-mhd-hll-design.md` and `docs/superpowers/plans/2026-07-09-gpu-mhd-hll.md` | `planned` | GPU HLL MHD implementation and its validation package. |
| `docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md` | `superseded` | Replaced by the solver-aware 2026-07-08 and breadth/MCA-depth 2026-07-09 packages. |

For temporal divergence, generated configs, stdout/stderr logs, and per-run
metadata remain local ignored assets. The committed summary embeds generated
config and metadata text; no transient grids are retained. Historical summaries
remain unchanged at their original paths and are numerical authorities only
within the bounds assigned above.
