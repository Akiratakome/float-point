# Report 2 Evidence Map

> Current status authority for Report 2. Requirements and dated meeting reports
> are historical inputs; experiment summaries remain the numerical authority.
> Last audited: 2026-07-23 on `week16-remaining-evidence`.

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
Lifecycle manifests complement this bounded evidence inventory; they do not
replace statuses such as `provisional` or `negative-result`, nor do they widen
the claims supported by a summary. The manifests describe retention and
pipeline ownership while this map remains the authority for evidential status.

## Evidence inventory

All paths below are repository-relative. `Tracked` means a committed authority;
`local ignored` means retained outside Git; `transient` means grids are not a
durable evidence product.

| Evidence | Status | Authority and facts | Supported claim | Excluded claims | Supersedes | Provenance | Retention |
|---|---|---|---|---|---|---|---|
| Week 12 Brio-Wu 1D | `validation` | `experiments/week12/brio_wu_1d/summary.md`; HLL Brio-Wu, N=200/400/800 candidates against block-averaged aligned N=8000 double reference. | The 1D MHD implementation has monotonic L1/L2 convergence on this validation setup. | A Report 2 precision headline or an exact MHD-solution precision error. | Earlier walking-skeleton output is not a current precision package. | No embedded generating commit; tracked Git history is provenance. | Tracked summary; referenced grids are provenance/transient. |
| Week 12 2D invariance/GLM | `validation` | `experiments/week12/mhd_2d/brio_wu_2d/summary.md` and `experiments/week12/mhd_2d/divb_clean/summary.md`; transverse-invariance and div(B)-decay gates. | The 2D extension preserves the tested invariant state and the GLM cleaning diagnostic decays as gated. | OT/KH precision adequacy, convergence, or hardware evidence. | None. | No embedded generating commit; tracked Git history is provenance. | Tracked summaries and figure grids. |
| Week 13 HLLD divB follow-up | `validation` | `experiments/week13/hlld_divb_followup/summary.md`; 128^2 and 256^2 OT follow-up, including HLLD 256^2 t=0.5: 812 steps, divB_mean=0.274, divB_max=24.45. | HLLD's apparent issue was a stale-binary interpretation; remaining div(B) is resolution-consistent and localized at current sheets. | HLLD precision sensitivity, production-default status, or CPU/GPU equivalence. | The stale-binary Week 13 interpretation. | No embedded generating commit; tracked Git history is provenance. The summary records solver-fix commit `6491104` as interpretive provenance. | Tracked summary and diagnostic provenance. |
| Week 13 OT morphology | `morphology-only` | `experiments/week13/orszag_tang/paper_summary.md`; local 256^2 HLL OT at t=0.5, 806 steps. | The 256^2 HLL result supplies paper-grounded OT morphology. | A completed 512^2 self-reference gate, precision claim, or asymptotic convergence. | None. | No embedded generating commit; tracked Git history is provenance. | Tracked summary and figures; no retained report-grade reference grid. |
| Week 13 KH morphology | `morphology-only` | `experiments/week13/kelvin_helmholtz/paper_summary.md`; local 256^2 HLL KH at t=1.0, 1148 steps. | The result supplies KH morphology. | A precision claim, completed 512^2 self-reference gate, or convergence claim. | None. | No embedded generating commit; tracked Git history is provenance. | Tracked summary and figures. |
| Week 14 HLL MCA | `invalid` | `experiments/week14/mhd_precision_pilot/summary.md`; nominal p24/p53 N=8 Docker MCA rows. | No Report 2 evidential claim. | Any p24 noise/spread interpretation: p24 instrumentation did not take effect. | Replaced by Week 15 HLL N=30 p24/p53 MCA in `experiments/week15/brio_wu_precision_pilot_p1/summary.md`. | Summary embeds generating commit `76d5e381b9074476526d6014d4e3fc98d2e7deae`. | Tracked historical summary; retain for diagnosis only. |
| Week 14 pilots/smokes | `superseded` | `experiments/week14/mhd_precision_pilot/summary.md` and `experiments/week14/mhd_precision_pilot_hlld/summary.md`; eight deterministic variants and N=8 MCA probes. | Development provenance, including the deterministic G0 pilot. | Report-grade deterministic/MCA conclusions. | Week 15 24-variant, N=30 Brio-Wu packages; Week 14 HLL MCA is also invalid. | Summaries embed generating commits `76d5e381b9074476526d6014d4e3fc98d2e7deae` and `0ab957cfb2a10fcfaeef5867a8deaa601259118e`. | Tracked summaries; development assets retained. |
| Week 15 Brio-Wu HLL | `provisional` | `experiments/week15/brio_wu_precision_pilot_p1/summary.md`, `summary.csv`, `summary.json`; 24 deterministic CPU variants plus Docker Verificarlo p53 and p24 N=30. | Bounded CPU HLL deterministic and MCA observations against the project baseline. | A unified Report 2 precision gate or exact MHD-solution error. | Week 14 HLL pilot and invalid N=8 MCA interpretation. | Summary embeds generating commit `3728e1babddb799292b891a63b5e7022300a1171`. | Tracked: `summary.md`, `summary.csv`, `summary.json`, `figures/deterministic_norms.png`, `figures/mca_noise_floor.png`; local ignored: `runs/` and `mca/` configs, logs, and metadata; transient: generated run outputs/grids. |
| Week 15 Brio-Wu HLLD | `provisional` | `experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.md`, `summary.csv`, `summary.json`; 24 deterministic CPU variants plus Docker Verificarlo p53 and p24 N=30. | Bounded CPU HLLD deterministic and MCA observations against the project baseline. | A unified Report 2 precision gate, production-default promotion, or exact MHD-solution error. | Week 14 HLLD pilot/smoke. | Summary embeds generating commit `76a168749269046c7a0c00b42f5cb2527689a11d`. | Tracked: `summary.md`, `summary.csv`, `summary.json`, `figures/deterministic_norms.png`, `figures/mca_noise_floor.png`; local ignored: `runs/` and `mca/` configs, logs, and metadata; transient: generated run outputs/grids. |
| Week 15 OT HLL | `provisional` | `experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.md`; 24 deterministic 256^2 CPU variants, G0 pass, 806-step reference. MCA authority is separate: `experiments/week15/orszag_tang_precision_smoke/mca_n30/summary.json`, p53/p24 N=30. | Bounded deterministic HLL sensitivity and separate N=30 MCA observations. | One unified deterministic-plus-MCA gate, exact-reference accuracy, or 512^2 convergence. | Week 15 gate128/headline smoke packages and the 2026-07-02 OT plan. | Deterministic summary embeds generating commit `4d9697b933f5fa3e12164a3b05b814a7a191073c`; MCA summary JSON has no generating commit, so tracked Git history is its provenance. | Tracked deterministic summary/figures and MCA summary, configs, logs, and metadata; generated grids are removed/transient. |
| Week 15 OT HLLD | `provisional` | `experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.md`; 24 deterministic 256^2 CPU variants, G0 pass, 812-step reference. MCA authority is separate: `experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/summary.json`, p53/p24 N=30. | Bounded deterministic HLLD sensitivity and separate N=30 MCA observations. | One unified deterministic-plus-MCA gate, production-default promotion, exact-reference accuracy, or 512^2 convergence. | Week 15 gate128/headline smoke packages and the 2026-07-02 OT plan. | Deterministic summary embeds generating commit `0221e05cc75394ac76f1d79afbc53cdd30550177`; MCA summary JSON has no generating commit, so tracked Git history is its provenance. | Tracked deterministic summary/figures and MCA summary, configs, logs, and metadata; generated grids are removed/transient. |
| Temporal divergence | `negative-result` | `experiments/week15/mhd_temporal_divergence/summary.md`; 80 successful provenance-complete runs, Brio-Wu 15 paired samples over [0.01, 0.1], OT 25 over [0.1, 0.5]. | Fixed-window fp32-vs-fp64 Lyapunov-like engineering fits; the planned OT > Brio-Wu contrast was not observed. | A formal maximal Lyapunov exponent, a physical instability rate, or general OT/KH ordering. | `experiments/week15/mhd_temporal_divergence_smoke/summary.md` is smoke provenance only. | Summary JSON embeds generation checkout `cf50f837dd2e74040c06f86af2f3c21a9b70ed58` and recorded run checkout `c26ab4a286066655b32f08cb6d22324bd922f99c`. | Tracked summary/figure; configs, stdout/stderr logs, and metadata are local ignored; grids are transient and removed. |
| GPU HLL MHD | `validation` | `src/gpu/mhd_gpu_solver.{hpp,cu}`, `src/gpu/mhd_kernels.{cuh,cu}`, and `[gpu][mhd]` unit tests; CUDA Toolkit 13.3 targets RTX 5070 sm_120 using `CMAKE_CUDA_ARCHITECTURES=120`; `gpu_smoke` passes; Brio-Wu 1D and Orszag-Tang 2D HLL CPU-vs-GPU validation passes in float and double, with the covered tests bit-exact. | The opt-in `hrsc_mhd` `device=gpu` HLL path reproduces the CPU HLL validation cases covered by the GPU gate. | HLLD-on-GPU, KH-on-GPU validation, performance, matched hardware-axis evidence, GPU precision sweeps, or a Report 2 hardware conclusion. | The planned-only GPU row. | Tracked Git history and validation commands are provenance; no generated experiment package exists yet. | Tracked source/tests/docs; transient validation grids are removed. |
| CPU/GPU hardware axis | `report-grade` | `experiments/week16/cpu_gpu_hardware_axis/summary.md`, `summary.csv`, `summary.json`; matched HLL Brio-Wu 1D and Orszag-Tang 2D CPU/GPU runs in float and double. Gate `G-GPU` passes with `ulp_max=0` in all four rows; OT GPU speedups are 5.965x double and 6.353x float, while Brio-Wu launch overhead makes the 1D GPU rows slower. | The validated opt-in HLL GPU path has bounded same-precision CPU/GPU correctness and timing evidence for the covered Brio-Wu and OT cases. | HLLD-on-GPU, KH-on-GPU, GPU MCA, a broad GPU performance matrix, or precision conclusions beyond the covered matched cases. | The deferred hardware-axis row. | Summary embeds generating commit `2514e74bfd850d7134e5346e3845ca01c285606e`; tracked Git history records the later evidence commit. | Tracked summary and figures; generated grids are removed/transient; run configs, logs, and metadata are local ignored provenance. |
| KH report-grade precision | `provisional` | `experiments/week16/kelvin_helmholtz_precision/validation/summary.md` passes the 256^2-vs-512^2 validation gate. `experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.md` and `experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.md` record 24 deterministic CPU variants per solver with finite/positive states and fixed 1148-step completion. HLL float Linf(rho) is about 1.8e-6; HLLD float Linf(rho) is about 3.2e-6 to 4.3e-6. MCA rows are schema-complete but `blocked_environment` because the local Docker daemon is unavailable. | KH has a completed 512^2 validation gate and bounded deterministic precision sensitivity packets for HLL and HLLD. | Report-grade KH deterministic-plus-MCA precision, MCA noise-floor interpretation, KH-on-GPU, or production-default HLLD promotion. | The morphology-only KH row for deterministic validation and precision sensitivity. | Validation summary embeds generating commit `3fe51d033d0584ef5f0604189d47305ab872f191`; deterministic summaries embed `2082dd5e2825a42038c8e9ceb050092c6211adc8`; Docker failure is recorded as `blocked_environment`. | Tracked summaries and figures; run configs, logs, and metadata are local ignored; generated grids are removed/transient. |
| OT/KH 512^2 consolidation | `report-grade` | `experiments/week16/ot_kh_512_consolidation/summary.md`, `summary.csv`, `summary.json`; consolidates `experiments/week13/orszag_tang/summary.json` and `experiments/week16/kelvin_helmholtz_precision/validation/summary.json`. Both 256^2-vs-512^2 gates pass: OT L1(rho)=7.722e-02, divB_max=3.720; KH L1(rho)=1.836e-03, divB_max=6.714e-04; both have mass_rel=0. | Both 2D MHD benchmark self-reference gates are complete, and the consolidation provides a bounded engineering sensitivity checkpoint. | Asymptotic convergence, exact-solution accuracy, precision adequacy, or a physical instability ordering from only two resolutions. | The deferred 512^2 consolidation row. | Consolidation summary embeds generating commit `8a4b1d1c256781e8b6ab84f574f616760b8bab28`; source summaries embed their own run commits. | Tracked summary files; source run configs, logs, and metadata are local ignored; generated grids are removed/transient. |
| Week 17 Report 2 synthesis | `report-grade` | `experiments/week17/report2_synthesis/summary.md`, `summary.csv`, `summary.json`; read-only synthesis of committed Week 15-16 evidence. | Report-facing ranking and claim-boundary synthesis for the existing evidence inventory. | New numerical evidence, KH MCA, asymptotic convergence, or promotion of provisional deterministic-plus-MCA rows. | None. | Summary embeds current synthesis checkout and source summary paths. | Tracked summary files and figures. |

## Current Report 2 claim boundaries

- Precision effects are measured against project baselines, not exact MHD solutions.
- HLLD is an analysed CPU solver but is not silently promoted to the production default.
- Temporal rates are bounded Lyapunov-like engineering fits.
- A formal maximal Lyapunov exponent is not claimed.
- The planned OT > Brio-Wu contrast was not observed.
- GPU HLL MHD validation and matched hardware-axis evidence are available only for the covered HLL Brio-Wu and Orszag-Tang cases.
- KH supports morphology, 512^2 validation, and deterministic CPU precision sensitivity; KH MCA remains unavailable on this workstation because Docker is blocked.
- The OT/KH 512^2 gates are complete, but two resolutions do not establish asymptotic convergence.
- Week 17 synthesis is an aggregate/report-facing packet; it does not introduce new numerical evidence or promote provisional source rows.

The temporal package has a technical and report-grade gate for its bounded
engineering analysis, but its row remains `negative-result` because the planned
cross-case contrast was not observed. The four Week 15 Brio-Wu/OT
deterministic-plus-MCA rows remain `provisional` until a machine-readable
unified gate and authoritative combined summary exist.

## Plan and retention routing

| Planning asset | Current routing | Scope |
|---|---|---|
| `docs/superpowers/specs/2026-07-21-week15-16-completion-design.md` | `executed with one environment blocker` | Temporal phase, hardware-axis evidence, KH 512^2 validation/deterministic precision, and 512^2 consolidation are complete; KH MCA is blocked by the local Docker daemon and is not used for a report-grade MCA claim. |
| `docs/superpowers/specs/2026-07-09-gpu-mhd-hll-design.md` and `docs/superpowers/plans/2026-07-09-gpu-mhd-hll.md` | `executed for validation and bounded hardware axis` | GPU HLL MHD implementation, Brio-Wu/Orszag-Tang CPU-vs-GPU validation, and the matched Week 16 hardware-axis packet are complete. |
| `docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md` | `superseded` | Replaced by the solver-aware 2026-07-08 and breadth/MCA-depth 2026-07-09 packages. |

For temporal divergence, generated configs, stdout/stderr logs, and per-run
metadata remain local ignored assets. The committed summary embeds generated
config and metadata text; no transient grids are retained. Historical summaries
remain unchanged at their original paths and are numerical authorities only
within the bounds assigned above.
