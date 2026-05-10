# Week 7 Report 1 Aggregate Evidence

Purpose: route generated Week 7 experiment artefacts into Report 1 evidence sections. Narrative routing only; raw payloads live in matrix summaries.

## Included Matrix Families

| Family | Matrix summary | Report 1 evidence purpose |
|---|---|---|
| Smoke | `experiments/week7/report1_smoke/matrix_summary.json` | Sanity route for the Week 7 Report 1 harness path across representative 1D and 2D cases. |
| 1D validation | `experiments/week7/report1_validation_1d/matrix_summary.json` | Section 4 precision-axis evidence for Toro 1D double-vs-float rows. |
| 2D CPU | `experiments/week7/report1_validation_2d/matrix_summary.json` | Section 4 precision-axis evidence for Liska-Wendroff Config 3 CPU double-vs-float rows. |
| 2D GPU | `experiments/week7/report1_validation_2d_gpu/matrix_summary.json` | Section 4 precision-axis evidence for Liska-Wendroff Config 3 GPU strict double-vs-float rows. |
| 2D HLLC strict preflight | `experiments/week7/report1_validation_2d_hllc_strict/matrix_summary.json` | Section 4 CPU-to-GPU strict preflight support for the HLLC 2D path at 200^2 and 400^2. |
| Variation | `experiments/week7/report1_variation/matrix_summary.json` | Section 2 and cross-cutting evidence for compiler, fast-math, branch-rule, and implementation-axis comparisons. |
| 1600^2 GPU reference candidate | `experiments/week7/reference_1600/matrix_summary.json` | Section 4 high-resolution GPU reference candidate for lower-resolution LW3 comparisons. |

## GPU Evidence Routing

- Week 6 regression: `experiments/week6/regression/summary.md` remains the baseline strict CPU-vs-GPU regression evidence for GPU bring-up.
- Week 6 CSC smoke: `experiments/week6/csc_smoke/summary.md` remains the CSC environment and smoke-run evidence.
- Task 9 device report: `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` routes the HLLC strict CPU-to-GPU preflight rows at 200^2 and 400^2.
- 1600 summary: `experiments/week7/reference_1600/summary.md` routes the 1600^2 GPU-produced reference candidate and its provenance.

## Interpretation Rules

- Treat HLLC-vs-Rusanov rows as numerical-method comparisons, not ULP gates.
- Treat compiler rows as implementation-axis sensitivity evidence; they do not replace precision-axis validation rows.
- Treat `<=` vs `<` rows as branch-rule sensitivity evidence, not solver default changes.
- Treat `stationary_contact` Philip-ratio-style adequacy claims as n/a unless an explicit reference metric is later produced.
- Treat the 1600^2 GPU artefact as a GPU reference candidate with Week 6 and Task 9 preflight support, not as a full CPU/GPU matrix and not as CPU-equivalent proof.
