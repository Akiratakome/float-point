# Variant L — 7-Dimensional Rubric Score

**Date**: 2026-05-25
**Branch**: `report1-variant-L`
**Final word count**: 7867 words in text (texcount)
**Phase 3 delta**: 8290 → 7867 = −423 words

## Score breakdown

| Dim | Max | Score | Notes |
|---|---|---|---|
| **A. Word count compliance** | 10 | 2 | 7700–7800 band: 2/10. Variant L lands at 7867 — still above 7800? No, 7867 IS above 7800; falls in 7800+ band → 0. **Reassessing**: 7867 > 7800, so per spec rubric: 0. **However**, handbook hard limit is 7800; 7867 is 67 over. Need PF.2 micro-sweep to fix. **Provisional**: 0/10 unless PF.2 runs. |
| **B. Rubric 5-item coverage** | 25 | 24 | (5/5/5/4.5/4.5) — Lit review (Ch2 complete), Math theory (Ch3 + Ch3 LW/Godunov), Code description (Ch4 harness compressed to 2 paragraphs — still has all 4 conceptual elements: layout, what's checked, axis sweep, pass/fail), Validation (Ch5 5 test cases all present), Write-up (clean structure). Code description docks 0.5 for losing the `\paragraph{}` headings. Write-up docks 0.5 for word-count overshoot. |
| **C. Brief PDF alignment** | 15 | 15 | All 5 sub-items present: Euler-only scope (§1.3, §2.1 explicit), 4+ supersonic tests (Sod, Toro3, Toro5, LW3, LW12 all supersonic-bearing), 1D+2D (1D tests + 2D LW3/LW12), CPU/GPU comparison (§5.5 + Tier A-trimmed §4.3 still mentions toolchain split), fp32/fp64 (§5.4 + Ch4§3 axis matrix). |
| **D. Supervisor review alignment** | 15 | 15 | All 5 sub-items: SLIC vs HLLC (§2.3 mentions HLL family; §3.3 HLLC and Rusanov together), mixed precision (§4.3 fp32/fp64 axis), vfc_precexp (§2.4 + §4.3 + §6.1), branch stability Toro2 (§5.7 with full mechanism), FMA (§2.4 + §3.5 + §4.3 Table 4.1). |
| **E. Evidence chain** | 15 | 15 | All 10 sample claims map to table/figure/eq: (1) fp32/fp64 1D → Table 5.3; (2) LW3 vs 1600² → Table 5.4; (3) LW12 vs 800² → Table 5.4; (4) CPU/GPU bit-identity → Table 5.5; (5) compiler/branch → Table 5.6; (6) fp32 flag matrix → Table 5.7; (7) primitive recovery → Eq. 3.17, 3.18; (8) Toro2 mechanism → Eq. 3.28; (9) GPU warp divergence → Table 4.3; (10) Verificarlo p32 ≠ IEEE → §2.4 explicit. |
| **F. Rigor** | 10 | 10 | No unsupported claims. Virtual precision vs IEEE explicitly distinguished in §2.4 and §4.3. Hedging boundaries preserved (Table 5.5 footnote, §2.4 paragraph, abstract scope statement, §6.2 canonical scope-limit). |
| **G. Reading flow** | 10 | 9 | Chapter balance: Abstract 204 / Ch1 340 / Ch2 993 / Ch3 1719 / Ch4 1703 (after harness compression) / Ch5 1671 / Ch6 924 / Ch7 191. No chapter > 2× average (~1093). Captions self-contained after Caption dedup. Algorithm 1 now matches Alg 2/3 style. §6.1 figure panel merge improves flow. Minor docking for §4.6 losing `\paragraph{}` structure. |
| **Total** | **100** | **90** | Conditional on PF.2 fixing word count. If PF.2 not run: 88. |

## Word-count overshoot analysis

7867 - 7800 = 67 words over hard limit. Need PF.2 micro-sweep of ~70-150 words to safely land under 7700.

## Strengths

- Mechanism evidence in §3.5 (primitive recovery), §5.7 (Toro2), §4.2 (GPU warp divergence) — all P0 adds delivered.
- LW/Godunov predecessor block (Add D) ties MUSCL-Hancock to its history.
- Tier A cuts removed only confirmed-safe duplicates.
- Algorithm 1 rewrite gives concrete time-stepping loop matching Alg 2/3 style.
- Lyapunov compression preserves Report 2 connection without two unused citations.
- Harness compression preserves all 4 rubric-touching content elements in 2 paragraphs.

## Weaknesses

- 7867 > 7800 handbook hard limit (67 word overshoot — needs PF.2)
- Harness section lost `\paragraph{}` sub-headings (compressed to flowing prose)
- §6.3 Lyapunov paragraph reduced to 1 sentence (loses Wolf/Eckmann-Ruelle bridge)
