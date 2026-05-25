# Report 1 Trim — Final Scoring (Post-Merge)

**Date**: 2026-05-25
**Branch**: `report` (Variant L merged + PF.2 micro-sweep)
**Final word count**: **7697 words in text**

## Per-chapter breakdown (texcount "Words in text")

| File | Words | Headers | Floats | Inline math | Display math |
|---|---|---|---|---|---|
| Abstract | 204 | 1 | 0 | 7 | 0 |
| Chapter 1 | 340 | 5 | 0 | 0 | 0 |
| Chapter 2 | 993 | 6 | 0 | 24 | 4 |
| Chapter 3 | 1663 | 15 | 5 | 65 | 31 |
| Chapter 4 | 1620 | 7 | 3 | 87 | 2 |
| Chapter 5 | 1626 | 10 | 16 | 132 | 0 |
| Chapter 6 | 964 | 5 | 4 | 26 | 1 |
| Chapter 7 | 191 | 4 | 0 | 6 | 0 |
| **Sum (incl. front matter)** | **7697** | **54** | **28** | **347** | **38** |

## Trajectory

| Phase | End count | Net delta |
|---|---|---|
| Start | 8564 | — |
| Phase 1 (review3 package + 3 P0 adds) | 8311 | −253 |
| Phase 2 (eqn compress, alg rewrite, fig merge, LW/Godunov add) | 8290 | −21 |
| Variant L Phase 3 (Tier A + Lyapunov + sanity + harness light) | 7867 | −423 |
| PF.2 micro-sweep | **7697** | −170 |
| **Cumulative** | **7697** | **−867** |

## 7-Dimensional Final Score

| Dim | Max | Score | Notes |
|---|---|---|---|
| **A. Word count compliance** | 10 | 5 | 7697 sits in 7550–7700 band → 5/10. Could optionally micro-sweep further to 7400–7500 for full 10, but PF.2 already at 11 cuts; further trimming risks content damage. |
| **B. Rubric 5-item coverage** | 25 | 24 | Lit review (Ch2 complete, Powell added). Math theory (Ch3 + LW/Godunov + Algorithm rewrite). Code description (Ch4 §4.6 harness 2 paragraphs preserves layout/checks/sweep/pass-fail). Validation (5 cases × CPU/GPU × fp32/fp64 + 4 supersonic). Write-up (clean structure, captions tightened). |
| **C. Brief PDF alignment** | 15 | 15 | Euler-only scope, 4+ supersonic (Toro3/Toro5/LW3/LW12), 1D+2D, CPU/GPU §5.5, fp32/fp64 §5.4. |
| **D. Supervisor review alignment** | 15 | 15 | SLIC vs HLLC (Ch2 HLL family + Ch3 HLLC), mixed precision (§4.3 axis), vfc_precexp (§2.4 + §4.3 + §6.1), branch stability §5.7 (Toro2 mechanism with N_*/D_* analysis), FMA (§3.5 + Table 4.1). |
| **E. Evidence chain** | 15 | 15 | 10 sampled quantitative claims all map: (1) 1D fp32/fp64→Table 5.3; (2) LW3→Table 5.4; (3) LW12→Table 5.4; (4) CPU/GPU→Table 5.5; (5) compiler→Table 5.6; (6) fp32 flags→Table 5.7; (7) primitive recovery→Eq 3.16,3.17; (8) Toro2→Eq 3.27; (9) GPU warp divergence→Table 4.3; (10) p32 vs IEEE→§2.4. |
| **F. Rigor** | 10 | 10 | No unsupported claims. Virtual precision vs IEEE explicit (§2.4 dedicated paragraph + §4.3 reminder). Hedging boundaries preserved (Table 5.5 footnote, abstract scope statement, §6.2 canonical scope-limit). |
| **G. Reading flow** | 10 | 9 | Chapter balance excellent (Ch3 1663, Ch4 1620, Ch5 1626 within 3% of each other). Captions self-contained. Algorithm 1/2/3 stylistically consistent. §6.1 subfigure panel merge improves flow. Minor docking for §4.6 losing `\paragraph{}` structure. |
| **Total** | **100** | **93** | Publication-ready (≥85 threshold). |

## Substantive additions delivered

| ID | Section | What was added | Evidence link |
|---|---|---|---|
| Add A | §3.5 | Primitive recovery mechanism: kinetic→total energy cancellation → fp32 accuracy loss → HLLC star-state propagation | Eq. 3.16, 3.17; Fig 5.7 (LW12 heatmap) |
| Add B | §5.7 | Toro2 branch-collapse mechanism: N_* = 0 by symmetry, D_* = -2ρa finite, computed S_* sign set by N_* rounding noise | Eq. 3.27 (N_*/D_* decomposition) |
| Add C | §4.2 | GPU warp-divergence analysis + memory-bound throughput rationale | Algorithm 3 (HLLC branch); Table 4.3 (fp64 LW3 GPU≈CPU, fp32 LW3 GPU faster) |
| Add D | §3.2 | Godunov/Lax-Wendroff predecessor block: 2 display equations + 80-word comparison | Eq. 3.6 (Godunov), Eq. 3.7 (LW); van Leer 1979 citation |
| ref | §2.2 | Powell 1999 eight-wave formulation citation (Report 2 context) | references.bib added |

## Algorithm 1 rewrite

Previously: 7-line dispatch bullet list. Now: function-style `AdvanceToFinalTime` with explicit Kahan compensation, Δt clip to t_end, dimensional-split sweep alternation, ghost-cell refill, Kahan-add time accumulation. Matches the style of Algorithm 2 (MUSCL-Hancock face-state) and Algorithm 3 (HLLC flux selection).

## Figure changes

- **Deleted**: Fig 6.1 (vfc_sod_overlay) — illustrative-only, not validation-bearing.
- **Merged**: Fig 6.3 (losos_quantiles) + Fig 6.4 (region_losos_margin) into single subfigure panel with parent label `fig:ch6-losos-combined`.
- **Caption dedup**: Fig 3.2, 5.1, 5.2, 5.3, 5.4, 5.5 (removed "computed with MUSCL-Hancock + HLLC" restatement since prose covers it).

## Known follow-ups

- Figure pipeline: `% TODO: panel-merge in figure pipeline` marker at Fig 6.3+6.4 indicates the two PNGs currently share one figure environment but are not yet physically merged into a single composite PNG. Cosmetic only.
- powell_1999 .bib entry verified; pdflatex warning will resolve on bibtex pass + 2 pdflatex runs.

## Reproducibility

All changes committed on the `report` branch. Spec doc: `docs/superpowers/specs/2026-05-25-report1-trim-design.md`. Plan doc: `docs/superpowers/plans/2026-05-25-report1-trim.md`. Variant scores: `2026-05-25-variant-L-score.md` and `2026-05-25-variant-H-score.md`.

Git commit trail from `report` branch HEAD backward: PF.2 micro-sweep → Variant L merge → Variant L sequence → CHECKPOINT 2 → Phase 2 sequence → CHECKPOINT 1 → Phase 1 P0 + low-risk + hedging.

**Status: Publication-ready, 93/100, 7697 words (under 7800 hard limit by 103, under 7700 soft target by 3).**
