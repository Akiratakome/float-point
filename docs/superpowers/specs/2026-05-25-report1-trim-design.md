# Report 1 Trim — Design Spec

**Date**: 2026-05-25
**Owner**: Yudong Tang
**Target file tree**: `report1/phd-thesis-template-2.4/`
**Status**: Approved (Section 1–5), pending writing-plans

---

## 1. Problem Statement

Current Report 1 LaTeX source has **8564 words in text** (texcount, excluding captions, headers, math). Handbook hard penalty threshold is **7800 words**; preferred target is **7400–7500**, acceptable range is **≤7700**. Reduction required: **~864 words minimum** (to hit 7700), **~1064 ideal** (to hit 7500).

Constraints:

- Must preserve all rubric coverage (Lit review, Math theory, Code description, Validation, Write-up quality — each 20%).
- Must preserve alignment with brief PDF (`report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`):
  - 4+ Euler test cases with supersonic waves, both 1D and 2D
  - CPU/GPU comparison
  - fp32/fp64 accuracy comparison
  - Reproducibility framework discussion
- Must preserve alignment with supervisor (Philip) feedback: SLIC vs HLLC, mixed precision, vfc_precexp, branch stability, FMA.
- Must preserve strict virtual-precision vs IEEE binary32 distinction (supervisor flagged as critical).
- All quantitative claims must map to a table/figure/equation.

## 2. Strategy Overview

Three phases with checkpoints. Per-subsection subagent execution, serial. Two-variant comparison for Phase 3.

```
Phase 1 (review3 换证据) → CHECKPOINT 1
  → Phase 2 (密度精修) → CHECKPOINT 2
    → Phase 3 双 Variant (L vs H 对比)
      → 选 winner → 微调 → FINAL SCORING
```

## 3. Subagent Protocol

### 3.1 Per-subagent prompt contract

Each subagent receives:

1. Target paragraph (file:line precise)
2. Upstream/downstream reference relationships (which sections cite this; will refs still resolve after edit?)
3. Before/after target text (or transformation rule)
4. Boundary constraints: no equation-number changes unless task-explicit; no table edits; no `\bibitem` edits; no citation-key changes.
5. Return format: original text + new text + word delta + 1–2 sentence justification.

### 3.2 Trust boundary

**No pre-review (subagent autonomous)**:
- Duplicate/restatement deletions
- Caption deduplication
- Tier A hard cuts

**Pre-review required (P0 — main agent reviews diff before write)**:
- §3.5 primitive recovery enhanced (Add A)
- §4.2 GPU warp divergence analysis (Add C)
- §5.7 Toro2 mechanism analysis (Add B)
- Algorithm 1 rewrite
- Ch3§2 equation block consolidation (eqn ref grep required)
- Ch3§3.2 LW/Godunov comparison block (Add D)
- Phase 3 Tier B items

### 3.3 Checkpoint protocol

Between phases, **main agent** (not subagent) executes:

| # | Check | Tool |
|---|---|---|
| 1 | Word count | `texcount -inc thesis.tex` |
| 2 | Rubric 5-item coverage | Read chapter heading + key sections |
| 3 | Evidence chain: claim → table/figure/eq mapping | `grep \ref{}` |
| 4 | Brief PDF alignment (5 sub-items) | Compare against brief |
| 5 | Supervisor review alignment (5 sub-items) | Compare against memory file |
| 6 | Rigor: unsupported claims, virtual-precision vs IEEE | Read key sections |
| 7 | LaTeX compile sanity | Optional pdflatex |

Check 7 only at Phase 3 final.

## 4. Phase 1 — review3.md Package

Net delta: **−497 words** (cut −757, add +260). Phase 1 end prediction: **~8067 words**.

### Task list (16 items)

| # | Touchpoint | Type | Operation | Δwords | Risk |
|---|---|---|---|---|---|
| 1 | Ch1§1.1 `chapter1.tex:7-16` | Cut | First two motivation sentences compressed to one | -50 | Low |
| 2 | Ch1§1.3 `chapter1.tex:33-35` | Cut | Final sentence "The contribution is therefore a bounded baseline..." | -32 | Low |
| 3 | Ch1§1.4 `chapter1.tex:39-44` | Cut | Compress entire section to one sentence | -50 | Low |
| 4 | Ch2§2.5 `chapter2.tex:175-182` | Cut | Delete entire section (already covered in §1.3 + §2.2) | -80 | Low |
| 5 | Ch3§3.3 `chapter3.tex:295-299` | Cut | Compress Rusanov framing to single sentence | -40 | Low |
| 6 ⚠️ | Ch3§3.5 `chapter3.tex:391-396` | Replace (Add A) | Replace weak primitive-recovery paragraph with mechanistic version: kinetic→total energy ratio, high-Mach regions in LW12/Toro5, sound-speed coupling to HLLC Eq. 3.17 | +70 net | **P0 review** |
| 7 | Ch4§4.1 `chapter4.tex:8-17, 45-54` | Cut | Cut AMReX justification opening paragraph + closing "stand-alone is a control" paragraph; replace with one sentence | -140 | Low |
| 8 ⚠️ | Ch4§4.2 `chapter4.tex:124-135` | Replace (Add C) | Replace CUDA block-size enumeration with warp-divergence analysis tied to Table 4.3 fp64 LW3 GPU≈CPU evidence | +70 net | **P0 review** |
| 9 | Ch5§5.2 `chapter5.tex:31-40` | Cut | Remove inline numeric recap (8.74e-8 etc.), refer to Table 5.3 | -60 | Low |
| 10 | Ch5§5.3 `chapter5.tex:174-196` | Cut | Remove SSIM/L1 numeric recap, refer to Table 5.4 | -60 | Low |
| 11 | Ch5§5.5 `chapter5.tex:349-350` | Cut | "A separate audit consolidates 52 hash-backed..." sentence | -35 | Low |
| 12 ⚠️ | Ch5§5.7 `chapter5.tex:513-524` | Replace (Add B) | Replace observational-only Toro2 paragraph with mechanism (u_L≈-u_R, S_*≈0, N_* and D_* collapse, Eq. 3.28); keep "observed non-completion" wording | +100 net | **P0 review** |
| 13 | Ch6§6.1 `chapter6.tex:25-34` | Cut | Remove specific digit numbers; preserve ordinal claims; refer to Figs 6.3/6.4 | -80 | Low |
| 14 | Ch6§6.3 + Ch7§7.3 | Cut | Replace §7.3 limitation paragraph with "See §6.3"; keep §6.3 enumerate | -50 | Low |
| 15 | Full-doc hedging sweep | Cut | Remove only 2x+ repeated boundary statements; preserve §2.4 virtual-precision section, Table 5.5 footnote, abstract main boundary | -80 | Medium |
| 16 | Ch2§2.2 `chapter2.tex:90-91` | Add | One-sentence citation of Powell 1999 (MHD eight-wave context, for Report 2) | +20 | Low |

### Phase 1 round scheduling

```
Round A (low risk, batch dispatch):  #1 → #2 → #3 → #4 → #16
Round B (low risk, batch dispatch):  #5 → #9 → #10 → #11 → #13 → #14
Round C (P0, draft + review):        #6 → #8 → #12
Round D (medium risk, hedging):      #15 (detailed prompt)
Round E (low risk):                  #7
→ CHECKPOINT 1
```

## 5. Phase 2 — Density Refinements

Net delta: **−30 words** (cut −90, add +60). Phase 2 end prediction: **~8037 words**.

### Task list (6 items)

| # | Touchpoint | Type | Operation | Δwords | Risk |
|---|---|---|---|---|---|
| 17 ⚠️ | Ch3§3.2 `chapter3.tex:116-143` | Compress | Inline Eq. 3.7 into Eq. 3.8; keep Eq. 3.9 (minmod def); delete Eq. 3.10 (ratio form), mention as single inline sentence. **Subagent must first grep `\ref{eq:ch3-onesided-jumps}` and `\ref{eq:ch3-limiter-ratio}` to verify no downstream refs** | -40 | **P0 review** |
| 18 | Ch3§3.5 `chapter3.tex:488-497` | Cut | Delete final paragraph "Variation axes by status" (Ch4§3 covers same matrix) | -50 | Low |
| 19 ⚠️ | Ch4§4.2 Algorithm 1 `chapter4.tex:93-104` | Rewrite | Rewrite Algorithm 1 to match alg2/3 style: explicit Kahan accumulation variables, Δt clip to t_end, x/y sweep alternation, explicit ghost-cell refill. ≤15 lines. Algorithm body does not count in "words in text" | 0 | **P0 review** |
| 20 | Ch6§6.1 `chapter6.tex:11-78` | Modify | Delete Fig 6.1 (vfc_sod_overlay) and its prose reference; merge Figs 6.3 (losos_quantiles) + 6.4 (region_losos_margin) into single subfigure panel with `% TODO: panel-merge in figure pipeline` marker | 0 | Medium (ref check) |
| 21 | Captions, multi-file | Modify | Strip "computed with the MUSCL–Hancock scheme and the HLLC Riemann solver" from Fig 5.1/5.2/5.3/5.4/5.5 captions (prose has it); same for Fig 3.1/3.2 | 0 (caption count) | Low |
| 22 ⚠️ | Ch3§3.2 end `chapter3.tex:186` | Add (Add D) | Insert ~80-word Predecessors block + 2 formulas: Godunov (1st-order Riemann-flux update) and Lax-Wendroff (2nd-order centred). Closing sentence: MUSCL-Hancock = limited piecewise-linear + Riemann-solver flux | +60 | **P0 review** |

### Phase 2 round scheduling

```
Round F (low risk):           #18 → #21
Round G (P0):                 #17 → #19 → #22
Round H (medium risk, fig):   #20
→ CHECKPOINT 2
```

## 6. Phase 3 — Two-Variant Comparison

Phase 2 end prediction: **~8037 words**. Phase 3 target: **≤7700** (handbook tolerance is 7800; we aim 7400–7700).

### Variant L (light cut, preserve framework discussion)

| Phase 3 operation | Δwords |
|---|---|
| Tier A (4 confirmed-safe items) | -140 |
| Ch6§3 Lyapunov paragraph → 1 sentence | -60 |
| Ch5§5 sanity check paragraph → 1 sentence | -50 |
| Ch4§6 Regression harness — light cut (4 paragraphs → 2) | -150 |
| **Subtotal** | **-400** |

Variant L end: **~7637 words** (margin 63 below 7700).

**Tier A breakdown**:
1. Ch4§3 hardware environment paragraph `chapter4.tex:287-295` (-50)
2. Ch6§1 "and the corresponding pressure ratio is comparable at R_p..." (-15)
3. Ch5§3 "Pressure ratios in Table 5.4 provide a second-field check..." (-25)
4. Ch5§4 "The pressure ratios in Table 5.4 remain below..." numeric recap (-50)

### Variant H (heavy cut, compact)

| Phase 3 operation | Δwords |
|---|---|
| Tier A (4 confirmed-safe items) | -140 |
| Ch6§3 Lyapunov paragraph → 1 sentence | -60 |
| Ch4§6 Regression harness — heavy cut (4 paragraphs → 1 merged) | -250 |
| Ch4§1 AMReX justification — full delete (replace with one sentence) | -80 |
| **Subtotal** | **-530** |

Variant H end: **~7507 words** (margin 193 below 7700).

### Comparison protocol

After both variants applied (each on its own git branch), main agent applies the **7-dimensional rubric** (Section 7) to each variant **independently**. Variant with higher total wins.

```
git checkout -b report1-variant-L
  [execute Phase 3 Variant L subagents]
  texcount + 7-dim scoring → score_L
  git commit "phase3 variant L"

git checkout main
git checkout -b report1-variant-H
  [execute Phase 3 Variant H subagents]
  texcount + 7-dim scoring → score_H
  git commit "phase3 variant H"

if score_L >= score_H:
  git checkout main && git merge report1-variant-L
  git branch -D report1-variant-H
else:
  git checkout main && git merge report1-variant-H
  git branch -D report1-variant-L
```

Post-merge: if winner end-count is still above 7500, run final light hedging sweep to land ≤ 7500.

## 7. Final Scoring Rubric (CHECKPOINT FINAL)

Applied **after Phase 3 winner is merged**. Also applied to each variant during Phase 3 comparison.

| Dimension | Max | Scoring |
|---|---|---|
| **A. Word count compliance** | 10 | 7400–7500: 10; 7500–7550: 7; 7550–7700: 5; 7700–7800: 2; >7800: 0 |
| **B. Rubric 5-item coverage** | 25 | 5 items × 5: lit review / math theory / code description / validation / write-up quality |
| **C. Brief PDF alignment** | 15 | 5 sub-items × 3: Euler-only scope, 4+ supersonic tests, 1D+2D, CPU/GPU, fp32/fp64 |
| **D. Supervisor review alignment** | 15 | 5 sub-items × 3: SLIC vs HLLC, mixed precision, vfc_precexp, branch stability (Toro2), FMA |
| **E. Evidence chain completeness** | 15 | Sample 10 quantitative claims; each claim → table/figure/equation map, 1.5 each |
| **F. Rigor** | 10 | Unsupported claims (-2 each); virtual precision vs IEEE distinction (must be ≥1 explicit mention); hedging boundaries preserved |
| **G. Reading flow** | 10 | Chapter balance (no chapter >2× average); section transitions; figure-text correspondence; caption self-containment |
| **Total** | **100** | ≥85 publication-ready; 75–85 ship with minor polish; <75 re-review |

**Target**: ≥90.

## 8. External Constraints

- **No figure regeneration**: This plan touches `.tex` only. Phase 2 #20 figure merge is marked `% TODO: panel-merge in figure pipeline` for a follow-up task.
- **No .bib edits**: When removing `\citep{}`, leave the corresponding `.bib` entry intact for later re-use.
- **No equation renumbering**: Equation deletions must be checked against the full ref graph; if a downstream ref exists, do not delete (escalate to user).
- **One file at a time**: Subagents work on one file. No cross-file edits in a single subagent task.

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Subagent over-cuts hedging boundaries | Detailed prompt for #15 listing **must-preserve** boundary sentences |
| Equation ref grep misses a citation | #17 / #22 subagents must report grep output; main agent verifies before approve |
| Phase 3 variant comparison ties | Final tiebreaker: Variant L (preserves more rubric content) wins ties |
| Algorithm 1 rewrite changes algorithmic behavior claim | #19 P0 review: ensure algorithm reflects actual implementation, not a redesign |
| LW/Godunov insertion changes math-theory rubric mark | #22 P0 review: keep insertion ≤ 80 words; cite Toro for both predecessors |

## 10. Execution Plan Reference

Detailed implementation plan to be produced by `superpowers:writing-plans` skill, derived from this design.

Expected plan structure: Phase 1 (5 rounds) → CHECKPOINT 1 → Phase 2 (3 rounds) → CHECKPOINT 2 → Phase 3 (2 branches) → comparison → merge → final scoring.
