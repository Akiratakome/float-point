# Report 1 Review-3 Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the review-3 revision spec to `report1/phd-thesis-template-2.4/` precisely at the subsection level, refresh the five Chapter 6 figures from `n = 30` MCA data, add LW12 1600² hierarchy + CSC reference / preflight / timing evidence, fix wording problems, add two missing BibTeX entries, and land the manuscript wordcount in `[7750, 7800]` words (hard cap 7800) — without touching solver numerics, cfg defaults, or harness code.

**Architecture:** Seven serial batches dispatched as sub-agents by the main process. Each batch performs (i) a pre-edit verification pass against the source spec, (ii) verbatim edits to one or more LaTeX files, (iii) a post-edit audit gate (forbidden-phrase grep + required-hedge grep + texcount delta + numeric traceability spot-check), (iv) a single commit. The main process never edits files; it only dispatches, audits, and dispatches fix-ups on gate failure. The Abstract is **not** edited but is grep-monitored after every batch for collateral exposure.

**Tech Stack:** LaTeX (MiKTeX `texcount`, `pdflatex`); BibTeX; PowerShell + Bash; ripgrep; git; no test framework — gates are grep + texcount + numeric traceability.

**Source spec:** [docs/superpowers/specs/2026-05-26-report1-review3-revision-plan.md](../specs/2026-05-26-report1-review3-revision-plan.md) — every text replacement, hedge, forbidden phrase, and numeric value below is sourced from this spec.

**Wordcount baseline:** 7697 (commit `9a48cbf`). Target window 7750–7800. Hard cap 7800.

---

## File Inventory

### Files edited (8)
- `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` — Eq 3.21 caption (Section *HLLC and Rusanov Fluxes*); cross-link at end of Section *Precision-Sensitive Decision Points*.
- `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` — Section *Implementation Route and Comparability Principle* toolchain paragraph; Section *Algorithmic Structure of the Implementation* Algorithm 1 caption; Section *Test-Case Matrix and Metrics* MCA paragraph; Section *Precision and Hardware Variants* after Table 4.3; Section *Reference-Solution Strategy*.
- `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` — Section *One-Dimensional Euler Validation* convergence-order paragraph + literature citation; Section *Two-Dimensional Euler Validation* "report-specific" wording fix + Table 5.4 LW12 self-convergence row + caveat; Section *Matched CPU/GPU Comparison* Table 5.5 column + caption + footnote + final paragraph; Section *Compiler, Branch, Solver, and Drift-Growth Sensitivity* Table 5.6 branch-rule row + prose.
- `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` — Section *Precision Adequacy and Region-Aware Diagnostics* LoSoS paragraph + new p32 sentence + new p8 caveat + Fig 6.1 caption; Section *Hardware and Implementation Sensitivity* WSL/GCC sanity sentence; Section *Limitations and Report 2 Direction* items 1, 2, 4.
- `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex` — Section *Limitations* toolchain clause.
- `report1/phd-thesis-template-2.4/References/references.bib` — two new entries.
- `report1/phd-thesis-template-2.4/Figs/report1/sigma_fp_vs_precision.png` (and 4 others) — replaced from `experiments/review3_mca_n30/report1_d2_replots/`.
- `report1/phd-thesis-template-2.4/Abstract/abstract.tex` — **not edited**; grep-monitored only.

### Files explicitly left alone
- `Chapter1/chapter1.tex`, `Chapter2/chapter2.tex` — out of scope.
- All cfg files, `src/`, `tests/`, `scripts/` — solver and harness off-limits.
- 11 figure files listed in spec §12.1 ("figures that do not change").

---

## Execution Rules (every batch must obey)

1. **Pre-edit verification:** For every targeted subsection, the sub-agent reads the current LaTeX, locates the verbatim `old_string` from this plan, and confirms it matches. If it does not match, the sub-agent stops and reports back; the main process re-syncs spec §11 and re-dispatches.
2. **Verbatim edits only:** No paraphrase. Use the exact text in this plan. Each `Edit` call uses `replace_all: false` so a non-match fails loud.
3. **No internal codenames in inserted text:** No `week N`, no `batch N`, no `pack A/B/C…`, no `review3`, no `report-facing`, no `legacy`. Hardware names stay in the existing draft form (`CSC`, `RTX 4060 Laptop GPU`, `RTX 5090`, `i9-13900H`, `AMD EPYC`).
4. **Post-edit audit gate (every batch):** Forbidden-phrase grep → 0 hits in touched files; required-hedge grep → ≥ 1 hit per applicable hedge; `texcount -inc -sum -1` delta within ± 10 of the batch budget; Abstract sentinel grep returns the four expected substrings unchanged.
5. **One commit per batch.** Commit message format: `report1 revision: <batch label>` (no internal codename leakage in commit messages either, since they're part of the project history).
6. **Failure handling:** If any gate fails, do not proceed to the next batch — open a fix-up step on the failing batch, re-run gates, then commit.

---

## Task 0: Branch + Pre-Flight

**Files:**
- Read: all 8 files listed in **File Inventory**.
- Modify: none.
- Snapshot: baseline `texcount` and commit hash.

- [ ] **Step 1: Confirm the git branch is clean enough to start.**

```bash
git status --short
git rev-parse --short HEAD
```

Expected: working tree may have unrelated unstaged changes (the manuscript baseline is at commit `9a48cbf`). Proceed only if the relevant manuscript files (`Chapter*/chapter*.tex`, `Abstract/abstract.tex`, `References/references.bib`, `Figs/report1/*.png`) match the commit-`9a48cbf` baseline this plan was written against. If they don't, stop and surface the mismatch.

- [ ] **Step 2: Snapshot baseline word counts per chapter.**

Run (from `report1/phd-thesis-template-2.4/`):

```bash
texcount -inc -sum -1 \
  Abstract/abstract.tex \
  Chapter1/chapter1.tex Chapter2/chapter2.tex Chapter3/chapter3.tex \
  Chapter4/chapter4.tex Chapter5/chapter5.tex Chapter6/chapter6.tex \
  Chapter7/chapter7.tex
```

Expected: `9003` total (full body text count). Record the per-file numbers (the spec's manuscript-body baseline of 7697 comes from a stricter `texcount` configuration; this plan uses the simpler `-1 -sum` count throughout for consistent deltas).

Save this baseline as `BASELINE_TEXCOUNT = 9003` for delta arithmetic in later batches. If `texcount` returns a different number, **do not adjust this plan's batch budgets** — instead, scale all budgets proportionally and surface to main process.

- [ ] **Step 3: Read the four Abstract sentinels and confirm they are present.**

Run from the repo root:

```bash
rg -nF '1600^2' report1/phd-thesis-template-2.4/Abstract/abstract.tex
rg -nF '800^2' report1/phd-thesis-template-2.4/Abstract/abstract.tex
rg -nF '1.30\times10^{-4}' report1/phd-thesis-template-2.4/Abstract/abstract.tex
rg -nF '\mathrm{ULP}_{\max}=0' report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: each grep returns exactly one line hit. Record the lines. These are the sentinel substrings; the Abstract-currency gate at the end of every later batch must reproduce them unchanged.

- [ ] **Step 4: Confirm the n=30 source figure directory exists with the expected five PNGs.**

```bash
ls experiments/review3_mca_n30/report1_d2_replots/sigma_fp_vs_precision.png \
   experiments/review3_mca_n30/report1_d2_replots/losos_quantiles_rho.png \
   experiments/review3_mca_n30/report1_d2_replots/region_losos_margin_rho_p32.png \
   experiments/review3_mca_n30/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png \
   experiments/review3_mca_n30/report1_d2_replots/region_noise_to_error_ratio_precision_grid_rho.png
```

Expected: five lines, no `No such file` errors. If any is missing, stop and surface.

- [ ] **Step 5: Confirm CFL values in cfg files.**

```bash
rg -n '^cfl' tests/cases/toro_1d/sod.cfg \
              tests/cases/liska_wendroff_2d/config3.cfg \
              tests/cases/liska_wendroff_2d/config12_n200.cfg \
              tests/cases/liska_wendroff_2d/config12_n400.cfg
```

Expected (verbatim values):
- `tests/cases/toro_1d/sod.cfg:8:cfl = 0.8`
- `tests/cases/liska_wendroff_2d/config3.cfg:10:cfl = 0.5`
- `tests/cases/liska_wendroff_2d/config12_n200.cfg:17:cfl = 0.4`
- `tests/cases/liska_wendroff_2d/config12_n400.cfg:17:cfl = 0.4`

If different, stop — the spec's "1D = 0.8, LW3 = 0.5, LW12 = 0.4" claim is no longer accurate and the plan must be updated before edits begin.

- [ ] **Step 6: Confirm the BibTeX file has none of the two new keys yet.**

```bash
rg -n '^@(inproceedings|article)\{(eccomas_2016_muscl|berthon_muscl_hancock)' \
  report1/phd-thesis-template-2.4/References/references.bib
```

Expected: no matches.

- [ ] **Step 7: No commit for this task (pre-flight only).**

---

## Task 1: Batch 0 — Numeric Writing Fixes

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (Section *HLLC and Rusanov Fluxes* Eq 3.21 caption; Section *Precision-Sensitive Decision Points* end of paragraph after Eq~\ref{eq:ch3-sstar-perturbation}).
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (Section *Algorithmic Structure of the Implementation* Algorithm 1 caption / surrounding paragraph).

**Word-Δ budget:** +50 / −0.

**Why this is Batch 0:** Zero evidence-dependency, smallest risk, smallest word delta.

- [ ] **Step 1: Read the current Eq 3.21 caption to confirm the verbatim text.**

```bash
sed -n '285,300p' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: line 291 contains `specific total-energy form. The contact pressure`. If not, stop.

- [ ] **Step 2: Replace "specific total-energy form" wording.**

Edit `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` with `replace_all: false`:

- `old_string`: (the verbatim sentence containing "specific total-energy form" — read it fully in Step 1 and supply both the sentence before and after the offending phrase to make the match unique)
- `new_string`: same surrounding sentence, with "the fourth entry is the specific total-energy form" replaced by:

> the fourth entry has units of energy density once the prefactor is included; the bracketed factor is total energy per unit mass plus the contact-pressure correction

(Keep all surrounding LaTeX exactly as is — only the offending phrase changes.)

- [ ] **Step 3: Read the end of Section *Precision-Sensitive Decision Points* "Branch sensitivity" paragraph.**

```bash
sed -n '440,460p' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: lines 443–457 contain Equation `eq:ch3-sstar-perturbation` and end the paragraph with `\citep{toro2009}.` on or near line 457. The cross-link sentence is to be inserted **after** the closing citation of that paragraph.

- [ ] **Step 4: Insert the §"Toro Test 2 Branch Stability" cross-link sentence.**

Edit `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` with `replace_all: false`:

- `old_string`: the exact sentence ending the Branch-sensitivity paragraph, ending in `\citep{toro2009}.` Use enough surrounding context to make the match unique.
- `new_string`: same sentence followed by a single space and the new sentence below (so it sits at the end of the same paragraph):

> When $N_\ast = 0$ exactly by symmetry (the degenerate case examined in Chapter 5 Section \emph{Toro Test 2 Branch Stability}), the relative perturbation in Equation~\ref{eq:ch3-sstar-perturbation} is undefined and the sign of the computed $S_\ast$ is set by accumulated rounding noise rather than by first-order linearisation.

- [ ] **Step 5: Read the current Algorithm 1 surroundings in Chapter 4.**

```bash
sed -n '60,115p' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: Algorithm 1 caption line, no `cfl` / `CFL` numerical value mentioned.

- [ ] **Step 6: Insert the per-case CFL sentence at the end of the paragraph immediately following Algorithm 1's `end{algorithm}` (line 111-ish), before the next subsection break.**

Edit `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` with `replace_all: false`:

- `old_string`: the exact final sentence of the paragraph that introduces or closes the Algorithm 1 environment. (Read it in Step 5.)
- `new_string`: same sentence followed by:

> The CFL coefficient is fixed per case: $C_{\mathrm{CFL}} = 0.8$ for the one-dimensional shock-tube tests, $C_{\mathrm{CFL}} = 0.5$ for LW3, and $C_{\mathrm{CFL}} = 0.4$ for LW12.

- [ ] **Step 7: Post-edit audit gate.**

Run from repo root:

```bash
rg -nF 'specific total-energy form' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n 'C_{\\mathrm{CFL}}\s*=\s*0\.8' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF 'Toro Test 2 Branch Stability' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected:
- First grep: **0 hits** (forbidden phrase gone).
- Second grep: ≥ 1 hit (CFL inserted).
- Third grep: ≥ 1 hit (cross-link inserted).

- [ ] **Step 8: Texcount delta gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Chapter3/chapter3.tex Chapter4/chapter4.tex
```

Expected: total increased by `+30` to `+60` (budget +50, tolerance ± 10 → accept `[40, 60]`; allow up to `+70` once for this batch since the cross-link sentence may run slightly long).

- [ ] **Step 9: Abstract sentinel re-check.**

Re-run the four `rg -nF` commands from Task 0 Step 3. Expected: identical line hits as before.

- [ ] **Step 10: Commit.**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex \
        report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "$(cat <<'EOF'
report1 revision: Chapter 3 Eq 3.21 caption fix, Toro 2 cross-link, per-case CFL

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Batch 1 — MCA n=30 Reframe + Figure Refresh

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (Section *Test-Case Matrix and Metrics* MCA paragraph, lines 186–202).
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` (Section *Precision Adequacy and Region-Aware Diagnostics* — LoSoS quantile sentence on line 18, Fig 6.1 caption on line 14, plus new p32 adequacy sentence and new p8 caveat sentence; Section *Limitations and Report 2 Direction* item 4).
- Replace (binary copy): five PNGs in `report1/phd-thesis-template-2.4/Figs/report1/`.

**Word-Δ budget:** +30 / −60 (net ≈ −30).

**Evidence:** `experiments/review3_mca_n30/summary.md` (`n = 30` seeds; no NaN/Inf; p8 header drift) and `experiments/review3_mca_n30/report1_d2_replots/summary.md` (p32 noise/error > 1 cells = 0 %).

- [ ] **Step 1: Read Chapter 4 lines 186–202 to confirm the verbatim MCA paragraph.**

```bash
sed -n '186,202p' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: paragraph contains `two or three samples per virtual precision are not statistically defensible` and `RAPTOR remains a possible future tool`. If either phrase is absent, stop.

- [ ] **Step 2: Replace the Chapter 4 MCA paragraph in one Edit.**

Edit `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` with `replace_all: false`:

- `old_string`: the verbatim paragraph from `Verificarlo runs are diagnostic, not real fp32/fp64 runs.` through `Direct fp32 claims come only from real fp32/fp64 comparisons against the chosen reference solution.`
- `new_string`:

> Verificarlo runs are diagnostic, not real fp32/fp64 runs. Following Parker's Monte Carlo arithmetic formulation~\citep{parker_1997} and Denis et al.'s Verificarlo tool~\citep{denis_etal_2016}, the solver is built through the MCA/virtual-precision toolchain in MCA mode with the random-rounding (RR) operator, and sampled with $n = 30$ independent seeds per (precision, solver) at virtual precisions \texttt{p8}, \texttt{p16}, \texttt{p32}, and \texttt{p53}, for both HLLC and Rusanov. The sample count exceeds the minimum recommended by~\citet{sohier_etal_2021} for the chosen significant-digits / confidence regime. For a primitive component $q_j$, the sample standard deviation $\sigma_{\mathrm{FP},j}=\operatorname{std}_k(q_j^{(k)})$ gives a local roundoff scale, used in Chapter~6 together with q05 / q25 / median spatial quantiles. The virtual-precision labels are diagnostic mantissa settings rather than IEEE storage formats (see Section~2.4); direct fp32 claims come only from real fp32/fp64 comparisons against the chosen reference solution.

(Note: this rewrite intentionally drops the "RAPTOR remains a possible future tool" sentence — it is one of the §8.1 compression candidates.)

- [ ] **Step 3: Read Chapter 6 lines 11–25 to confirm Fig 6.1 caption and the LoSoS quantile sentence.**

```bash
sed -n '11,25p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: line 14 contains the current Fig 6.1 caption starting `MCA-estimated $\sigma_{\mathrm{FP}}$ trend for LW3 density.`; line 18 contains `raw-field quantiles use only two or three samples per virtual precision`.

- [ ] **Step 4: Replace the Fig 6.1 caption (Chapter 6 line 14).**

Edit with `replace_all: false`:

- `old_string`: `\caption{MCA-estimated \(\sigma_{\mathrm{FP}}\) trend for LW3 density. The roundoff scale decreases with virtual precision for both HLLC and Rusanov. Differences between the curves reflect method variation: the arithmetic path changes, and Rusanov's extra diffusion smooths gradients, so lower or similar \(\sigma_{\mathrm{FP}}\) is not an accuracy ranking.}`
- `new_string`: `\caption{MCA-estimated \(\sigma_{\mathrm{FP},L_1}\) for LW3 density: the spatial mean of the per-cell sample standard deviation across $n = 30$ seeds. The roundoff scale decreases with virtual precision for both HLLC and Rusanov; differences between the curves reflect method variation (different arithmetic path; Rusanov's extra diffusion smooths gradients), so lower or similar \(\sigma_{\mathrm{FP},L_1}\) is not an accuracy ranking. Values near $10^{-11}$ at \texttt{p53} approach the fp64 noise floor and bound rather than measure the rounding scale at that precision.}`

- [ ] **Step 5: Replace the Chapter 6 LoSoS-quantile sentence (line 18).**

Edit with `replace_all: false`:

- `old_string`: `The raw-field quantiles use only two or three samples per virtual precision, so they are spatial diagnostics, not statistically meaningful distribution or confidence estimates.`
- `new_string`: `All MCA results in this chapter use $n = 30$ independent seeds per (precision, solver); the raw-field q05 / q25 / median quantiles are therefore distributional estimates within the sample-count guidance of~\citet{sohier_etal_2021}, not exploratory single-realisation snapshots.`

- [ ] **Step 6: Insert the new p32-adequacy sentence after the noise-to-error paragraph (after the sentence ending with `LW3 MCA grid.` on or near line 20).**

Edit with `replace_all: false`:

- `old_string`: `bounded to the tested precisions, cases, and LW3 MCA grid.`
- `new_string`: `bounded to the tested precisions, cases, and LW3 MCA grid. At \texttt{p32}, the fraction of LW3 cells with MCA noise above the reference-error scale is $0\,\%$ for both HLLC and Rusanov, supporting \texttt{p32} as adequate for this LW3 case at the tested resolution.`

- [ ] **Step 7: Insert the new p8 caveat sentence at the same insertion site (after the p32 sentence above).**

Edit with `replace_all: false`:

- `old_string`: `supporting \texttt{p32} as adequate for this LW3 case at the tested resolution.`
- `new_string`: `supporting \texttt{p32} as adequate for this LW3 case at the tested resolution. The \texttt{p8} curves are reported as a low-precision stress diagnostic only; the binary checkpoint header reaches $t \approx 0.3035$ while stderr stops at the requested $t = 0.3$, so \texttt{p8} quantiles must not be read as final-time equivalents to \texttt{p16} / \texttt{p32} / \texttt{p53}.`

- [ ] **Step 8: Read Chapter 6 limitations item 4 (lines 98–100) to confirm the verbatim text.**

```bash
sed -n '88,108p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: item 4 reads `Verificarlo \texttt{p32} is a virtual mantissa precision, distinct from IEEE binary32, and the two- or three-sample MCA diagnostics are spatial sensitivity maps rather than statistical distribution estimates.`

- [ ] **Step 9: Replace Chapter 6 limitations item 4.**

Edit with `replace_all: false`:

- `old_string`: `Verificarlo \texttt{p32} is a virtual mantissa precision, distinct\n        from IEEE binary32, and the two- or three-sample MCA diagnostics are\n        spatial sensitivity maps rather than statistical distribution estimates.`
- `new_string`: `Verificarlo \texttt{p32} is a virtual mantissa precision, distinct\n        from IEEE binary32; the $n = 30$ MCA diagnostics support sample-quantile\n        reading at \texttt{p16}, \texttt{p32}, and \texttt{p53}, while \texttt{p8}\n        is a low-precision stress diagnostic only because final-time alignment\n        is approximate (the binary checkpoint header reaches $t \\approx 0.3035$\n        while stderr stops at the requested $t = 0.3$).`

(Mind the LaTeX line-wrapping; use the indentation shown above to match the existing `enumerate` formatting.)

- [ ] **Step 10: Copy the five `n = 30` figure files in place.**

```bash
cp -f experiments/review3_mca_n30/report1_d2_replots/sigma_fp_vs_precision.png \
      report1/phd-thesis-template-2.4/Figs/report1/sigma_fp_vs_precision.png
cp -f experiments/review3_mca_n30/report1_d2_replots/losos_quantiles_rho.png \
      report1/phd-thesis-template-2.4/Figs/report1/losos_quantiles_rho.png
cp -f experiments/review3_mca_n30/report1_d2_replots/region_losos_margin_rho_p32.png \
      report1/phd-thesis-template-2.4/Figs/report1/region_losos_margin_rho_p32.png
cp -f experiments/review3_mca_n30/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png \
      report1/phd-thesis-template-2.4/Figs/report1/noise_to_error_ratio_heatmap_grid_rho.png
cp -f experiments/review3_mca_n30/report1_d2_replots/region_noise_to_error_ratio_precision_grid_rho.png \
      report1/phd-thesis-template-2.4/Figs/report1/region_noise_to_error_ratio_precision_grid_rho.png
```

- [ ] **Step 11: Verify the five figure mtimes are ≥ 2026-05-25.**

```bash
stat -c '%y %n' \
  report1/phd-thesis-template-2.4/Figs/report1/sigma_fp_vs_precision.png \
  report1/phd-thesis-template-2.4/Figs/report1/losos_quantiles_rho.png \
  report1/phd-thesis-template-2.4/Figs/report1/region_losos_margin_rho_p32.png \
  report1/phd-thesis-template-2.4/Figs/report1/noise_to_error_ratio_heatmap_grid_rho.png \
  report1/phd-thesis-template-2.4/Figs/report1/region_noise_to_error_ratio_precision_grid_rho.png
```

Expected: all five mtimes are dated 2026-05-25 or later.

- [ ] **Step 12: Post-edit audit gate.**

```bash
rg -nF 'two or three samples' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF 'two or three samples' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
rg -nF 'two- or three-sample MCA' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
rg -nF 'RAPTOR' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF '$n = 30$' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF '$n = 30$' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
rg -nF 'low-precision stress diagnostic' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
rg -nF 'sample-quantile' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected:
- First three: **0 hits** each (all forbidden phrases gone).
- Fourth: **0 hits** (RAPTOR sentence removed as part of compression).
- Remaining four: ≥ 1 hit each (new hedges present).

- [ ] **Step 13: Texcount delta gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Chapter4/chapter4.tex Chapter6/chapter6.tex
```

Expected: cumulative delta vs Task 0 baseline within `[−50, −10]` (budget −30, tolerance ± 20 because the Fig 6.1 caption is reasonably bulky).

- [ ] **Step 14: Abstract sentinel re-check (same 4 commands from Task 0 Step 3).**

Expected: identical hits.

- [ ] **Step 15: Commit.**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex \
        report1/phd-thesis-template-2.4/Chapter6/chapter6.tex \
        report1/phd-thesis-template-2.4/Figs/report1/sigma_fp_vs_precision.png \
        report1/phd-thesis-template-2.4/Figs/report1/losos_quantiles_rho.png \
        report1/phd-thesis-template-2.4/Figs/report1/region_losos_margin_rho_p32.png \
        report1/phd-thesis-template-2.4/Figs/report1/noise_to_error_ratio_heatmap_grid_rho.png \
        report1/phd-thesis-template-2.4/Figs/report1/region_noise_to_error_ratio_precision_grid_rho.png
git commit -m "$(cat <<'EOF'
report1 revision: MCA n=30 reframe and Chapter 6 figure refresh

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Batch 2 — Toolchain Consolidation

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (Section *Implementation Route and Comparability Principle* toolchain paragraph, lines 26–29).
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (Section *Matched CPU/GPU Comparison* footnote on lines 306–312 and final paragraph on lines 342–345).
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` (Section *Hardware and Implementation Sensitivity* sentence on line 80).
- Modify: `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex` (Section *Limitations* toolchain clause near line 12).
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` (Section *Limitations and Report 2 Direction* item 2 on lines 93–95).

**Word-Δ budget:** +20 / −60 (net ≈ −40).

**Evidence:** `experiments/add_experiment/toolchain_toro35/summary.md` (CSC strict Toro3/Toro5 CPU vs GPU zero in fp64/fp32) + `experiments/add_experiment/cpu_only_vs_cuda_cpu_sanity/summary.md` (CPU-only vs CUDA-enabled with `device=cpu` bit-identity on Toro3/Toro5 in fp64/fp32).

- [ ] **Step 1: Read Chapter 4 lines 20–35 to locate the toolchain paragraph.**

```bash
sed -n '20,35p' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: a paragraph mentioning Windows BuildTools for Toro3/Toro5 and Linux/WSL for the other cases. The exact wording in the existing draft is visible at lines 26–29.

- [ ] **Step 2: Replace the Chapter 4 toolchain paragraph.**

Edit with `replace_all: false`:

- `old_string`: the full verbatim paragraph from Step 1.
- `new_string`: the entire paragraph rewritten as:

> Toro3 and Toro5 were rerun on the CSC Linux strict-IEEE build for the matched CPU/GPU comparison reported in Chapter~5; Sod, LW3, and LW12 use Linux/WSL throughout. Each within-case CPU/GPU comparison stays within one matched binary, and the two toolchains are presented here as cross-hardware evidence (i9-13900H with RTX 4060 Laptop GPU, and an AMD EPYC host with RTX 5090 on CSC) rather than as a toolchain confound.

- [ ] **Step 3: Read Chapter 5 lines 306–316 (Table 5.5 footnote + caption).**

```bash
sed -n '305,318p' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: footnote begins `\emph{Footnote.} Toro3/Toro5 were built with Windows BuildTools;` and caption ends `…also have saved-checkpoint comparisons.}`.

- [ ] **Step 4: Replace the Chapter 5 Table 5.5 footnote.**

Edit with `replace_all: false`:

- `old_string`: `\emph{Footnote.} Toro3/Toro5 were built with Windows BuildTools;\nSod/LW3/LW12 were built with Linux/WSL; each within-case CPU/GPU comparison\nuses one matched binary pair, so the claim is limited to no observed saved-state\ndivergence within that matched case, not across toolchains.`
- `new_string`: `\emph{Footnote.} Toro3 and Toro5 are reported here from the CSC Linux strict-IEEE rerun, with four saved checkpoints in fp64 and fp32 and $L_1 = L_\infty = \mathrm{ULP}_{\max} = 0$ between the CPU and GPU saved states. A separate sanity check on the same CSC build showed that the CPU-only strict binary and the CUDA-enabled strict binary with $\texttt{device=cpu}$ produce bit-identical Toro3 and Toro5 saved states in both fp64 and fp32, so the CPU branch is not an artefact of running CPU code through a CUDA-enabled binary. Identity is restricted to saved conservative states under strict IEEE for the tested cases.`

- [ ] **Step 5: Edit the Table 5.5 caption to remove the "final-output only" clause.**

Edit `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` with `replace_all: false`:

- `old_string`: `; for Toro3 and Toro5 the evidence is final-output only, while Sod, LW3,\nand LW12 also have saved-checkpoint comparisons.}`
- `new_string`: ` across all five cases (saved final output plus checkpoints).}`

- [ ] **Step 6: Read Chapter 5 lines 340–347 (Matched CPU/GPU final paragraph).**

```bash
sed -n '340,348p' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: paragraph beginning `A CPU-only sanity check (WSL/GCC strict rerun of Toro3 and Toro5)`.

- [ ] **Step 7: Replace the Chapter 5 final paragraph of Section *Matched CPU/GPU Comparison*.**

Edit with `replace_all: false`:

- `old_string`: the verbatim paragraph from `A CPU-only sanity check (WSL/GCC strict rerun of Toro3 and Toro5)` through `…(Sod, LW3, LW12 with checkpoints; Toro3, Toro5\nfinal output only).`
- `new_string`:

> A separate sanity check on the CSC strict-IEEE build showed that the CPU-only binary and the CUDA-enabled binary with $\texttt{device=cpu}$ produce bit-identical Toro3 and Toro5 saved states in both fp64 and fp32; the CPU/GPU dispatch comparison is therefore not an artefact of running CPU code through a CUDA-enabled binary. The claim remains restricted to saved-state identity under strict IEEE for the tested cases.

- [ ] **Step 8: Read Chapter 6 line 80.**

```bash
sed -n '78,82p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: line 80 contains `WSL/GCC strict CPU reruns for Toro3 and Toro5 matched the existing strict CPU saved outputs with zero drift, but this is CPU-only sanity evidence, not general cross-toolchain equivalence.`

- [ ] **Step 9: Replace the Chapter 6 §"Hardware and Implementation Sensitivity" sentence.**

Edit with `replace_all: false`:

- `old_string`: `WSL/GCC strict CPU reruns for Toro3 and Toro5 matched the existing strict CPU saved outputs with zero drift, but this is CPU-only sanity evidence, not general cross-toolchain equivalence.`
- `new_string`: `A sanity check on the CSC strict-IEEE build showed that the CPU-only binary and the CUDA-enabled binary with $\texttt{device=cpu}$ produce bit-identical Toro3 and Toro5 saved states in fp64 and fp32, so the CPU/GPU dispatch comparison is not an artefact of running CPU code through a CUDA-enabled binary; the claim remains restricted to saved-state identity under strict IEEE for the tested cases.`

- [ ] **Step 10: Read Chapter 6 item 2 of the limitations list (lines 93–95).**

```bash
sed -n '92,97p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: item 2 contains `MSVC Build Tools for Toro3 and Toro5`.

- [ ] **Step 11: Append the CSC-rerun clause to item 2.**

Edit with `replace_all: false`:

- `old_string`: `Compiler evidence uses one compiler family inside each case (GCC~13\n        for the Linux/WSL cases, MSVC Build Tools for Toro3 and Toro5),\n        with no cross-compiler matrix.`
- `new_string`: `Compiler evidence uses one compiler family inside each case: GCC~13\n        for the Linux/WSL cases; the Toro3 and Toro5 saved-state evidence in\n        Chapter~5 now comes from the CSC Linux strict-IEEE rerun, with the\n        earlier MSVC Build Tools build retained only as a historical\n        comparator. No cross-compiler matrix is claimed.`

- [ ] **Step 12: Read Chapter 7 line 12.**

```bash
sed -n '8,18p' report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Expected: a phrase such as `within each tested case on its Windows BuildTools or Linux/WSL toolchain`.

- [ ] **Step 13: Replace the Chapter 7 toolchain clause.**

Edit with `replace_all: false`:

- `old_string`: `within each tested case on its Windows BuildTools or Linux/WSL toolchain`
- `new_string`: `within each tested case (the CSC Linux strict-IEEE rerun covers Toro3 and Toro5 final state plus four checkpoints; Sod, LW3, and LW12 are covered on the local Linux/WSL toolchain)`

- [ ] **Step 14: Post-edit audit gate.**

```bash
rg -nF 'Windows BuildTools' report1/phd-thesis-template-2.4
rg -nF 'WSL/GCC strict' report1/phd-thesis-template-2.4
rg -nF 'final output only' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -nF 'cross-toolchain equivalence' report1/phd-thesis-template-2.4
rg -nF 'CSC Linux strict-IEEE' report1/phd-thesis-template-2.4
rg -nF 'device=cpu' report1/phd-thesis-template-2.4
rg -nF 'historical\n        comparator' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected:
- First four: **0 hits** each.
- Fifth and sixth: ≥ 2 hits each (the phrase appears in multiple touched files).
- Seventh: ≥ 1 hit (Chapter 6 limitations item 2 updated). (The multiline grep flag may need `rg -nU` if running ripgrep < 13.)

- [ ] **Step 15: Texcount delta gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Chapter4/chapter4.tex Chapter5/chapter5.tex \
                        Chapter6/chapter6.tex Chapter7/chapter7.tex
```

Expected: cumulative delta vs Task 2 within `[−60, −20]`.

- [ ] **Step 16: Abstract sentinel re-check.**

Expected: identical hits as Task 0.

- [ ] **Step 17: Commit.**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex \
        report1/phd-thesis-template-2.4/Chapter5/chapter5.tex \
        report1/phd-thesis-template-2.4/Chapter6/chapter6.tex \
        report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
git commit -m "$(cat <<'EOF'
report1 revision: toolchain consolidation on CSC strict-IEEE rerun

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Batch 3 — Reference Provenance and LW12 1600² Hierarchy

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (Section *Reference-Solution Strategy*, lines 305–315).
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (Section *Two-Dimensional Euler Validation* — Table 5.4 lines 194–209 and surrounding LW12 prose on lines 178–188).
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` (Section *Limitations and Report 2 Direction* item 1 on lines 90–92).

**Word-Δ budget:** +90 / −20 (net ≈ +70).

**Evidence:** `experiments/add_experiment/lw3_5090_preflight/summary.md` (LW3 N=400 + N=800 fp64 CSC CPU vs RTX 5090 GPU zero) + `experiments/add_experiment/lw12_1600_reference/summary.md` + `…/reference_scaled_ratios.csv` (LW12 hierarchy with observed order 0.5348, R_ρ ratios).

- [ ] **Step 1: Read Chapter 4 lines 295–325 to locate the Reference-Solution Strategy section.**

```bash
sed -n '295,325p' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: the phrase `no analogous \(1600^2\) row is claimed\nfor LW12` is on lines 309–310 and `The LW3 \(1600^2\) reference is a CSC RTX 5090 strict-HLLC GPU reference\ncandidate with CPU/GPU preflight support` on lines 311–312.

- [ ] **Step 2: Replace the "no analogous 1600² row" sentence with the LW12 hierarchy summary.**

Edit with `replace_all: false`:

- `old_string`: `higher-resolution numerical reference; no analogous \(1600^2\) row is claimed\nfor LW12.`
- `new_string`: `higher-resolution numerical reference. LW12 is paired with both an \(800^2\) fp64 numerical reference and a complementary \(400^2 \to 800^2 \to 1600^2\) self-convergence hierarchy; the observed density \(L_1\) order is approximately \(0.535\), and the corresponding \(R_\rho\) against the \(1600^2\) field is \(\approx 8.53\times10^{-5}\) at \(N=400\) and \(\approx 3.37\times10^{-4}\) at \(N=800\). The slow \(L_1\) order is reported as a caveat on \(R_{\mathrm{ref}}\) magnitudes; LW12 is not claimed to be asymptotically converged.`

- [ ] **Step 3: Extend the LW3 1600² provenance sentence with the preflight evidence.**

Edit with `replace_all: false`:

- `old_string`: `The LW3 \(1600^2\) reference is a CSC RTX 5090 strict-HLLC GPU reference\ncandidate with CPU/GPU preflight support`
- `new_string`: `The LW3 \(1600^2\) reference is generated on the CSC strict-IEEE path with an RTX 5090, and is matched by a CPU vs RTX 5090 GPU preflight at \(N=400\) and \(N=800\) with \(L_1 = L_\infty = \mathrm{ULP}_{\max} = 0\) in fp64; the RTX 5090 is used here only for high-resolution reference generation, separately from the RTX 4060 Laptop GPU used for the matched CPU/GPU comparison study`

- [ ] **Step 4: Read Chapter 5 lines 178–209 (LW12 prose + Table 5.4).**

```bash
sed -n '178,210p' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: the LW12 prose paragraph (lines 178–188) plus the Table 5.4 environment with its current 4 data rows.

- [ ] **Step 5: Add two LW12 self-convergence rows to Table 5.4.**

Edit `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` with `replace_all: false`:

- `old_string`: `LW12 & $800^2$ fp64 & $400^2$ & $1.33\times10^{-3}$ & 0.9963 & $1.30\times10^{-4}$ & $1.13\times10^{-4}$ \\\n\bottomrule`
- `new_string`: `LW12 & $800^2$ fp64 & $400^2$ & $1.33\times10^{-3}$ & 0.9963 & $1.30\times10^{-4}$ & $1.13\times10^{-4}$ \\\nLW12 & self $800^2$ fp64 & $400^2$ & $2.32\times10^{-3}$ & --- & --- & --- \\\nLW12 & self $1600^2$ fp64 & $800^2$ & $1.60\times10^{-3}$ & --- & --- & --- \\\n\bottomrule`

(The two new rows give the self-convergence $L_1$ values from `lw12_1600_reference/summary.md`. Use `---` in the columns that do not apply at the self-convergence stage.)

- [ ] **Step 6: Append a caveat sentence immediately after Table 5.4's `\end{table}`.**

Edit with `replace_all: false`:

- `old_string`: `\label{tab:ch5-2d-summary}\n\end{table}`
- `new_string`: `\label{tab:ch5-2d-summary}\n\end{table}\n\nLW12 self-convergence is slow ($L_1$ order $\approx 0.535$); $R_\rho$ against the $1600^2$ reference should be read with this rate in mind rather than as exact-solution agreement.`

- [ ] **Step 7: Read Chapter 6 limitations item 1 (lines 89–93).**

```bash
sed -n '88,98p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: item 1 starts `LW12 uses an \(800^2\) fp64 numerical reference`.

- [ ] **Step 8: Replace Chapter 6 limitations item 1.**

Edit with `replace_all: false`:

- `old_string`: `LW12 uses an \(800^2\) fp64 numerical reference, not an exact\n        solution, and LW3 relies on high-resolution self-convergence\n        between \(400^2\), \(800^2\), and \(1600^2\) fp64 grids.`
- `new_string`: `LW12 is paired with an \(800^2\) fp64 numerical reference and a\n        \(400^2 \to 800^2 \to 1600^2\) self-convergence hierarchy with slow\n        \(L_1\) order \(\approx 0.535\); \(R_\rho\) magnitudes should be\n        interpreted against this rate rather than as exact-solution agreement.\n        LW3 retains the \(400^2/800^2/1600^2\) fp64 self-convergence\n        reference.`

- [ ] **Step 9: Post-edit audit gate.**

```bash
rg -nF 'no analogous \(1600^2\) row' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF 'reference candidate with CPU/GPU preflight support' report1/phd-thesis-template-2.4
rg -nF 'order \(\approx 0.535\)' report1/phd-thesis-template-2.4
rg -nF 'preflight at \(N=400\) and \(N=800\)' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF 'self $800^2$ fp64' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -nF 'self $1600^2$ fp64' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:
- First two: **0 hits**.
- Remaining four: ≥ 1 hit each.

- [ ] **Step 10: Texcount delta gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Chapter4/chapter4.tex Chapter5/chapter5.tex Chapter6/chapter6.tex
```

Expected: cumulative delta vs Task 3 within `[+60, +90]`.

- [ ] **Step 11: Abstract sentinel re-check.**

Expected: identical hits as Task 0.

- [ ] **Step 12: Commit.**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex \
        report1/phd-thesis-template-2.4/Chapter5/chapter5.tex \
        report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "$(cat <<'EOF'
report1 revision: LW12 1600 hierarchy and LW3 reference preflight evidence

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Batch 4 — GPU Timing Quantification + Cross-Hardware Framing

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (Section *Precision and Hardware Variants* — insert two sentences immediately after Table 4.3, which closes near line 290).

**Word-Δ budget:** +70 / −20 (net ≈ +50).

**Evidence:** `experiments/add_experiment/lw3_timing_split/summary.md` (CSC LW3 N=400 fp64 end-to-end: CPU 8.53 s, GPU 0.57 s).

- [ ] **Step 1: Read Chapter 4 lines 280–295.**

```bash
sed -n '280,295p' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: Table 4.3 ends with `\end{table}` near line 292, followed by a blank line and the next paragraph.

- [ ] **Step 2: Insert the timing-quantification sentences immediately after Table 4.3's closing brace.**

Edit `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` with `replace_all: false`:

- `old_string`: the exact `\end{table}` followed by the next paragraph's opening sentence (use enough context for a unique match).
- `new_string`: same `\end{table}`, plus a new paragraph inserted between the table and the original next paragraph:

> Quantitatively, the RTX 4060 Laptop GPU has a peak fp64 throughput of approximately $0.24$~TFLOPS, against approximately $1$~TFLOPS for the i9-13900H using AVX2; the GPU $\approx$ CPU fp64 result on this hardware is therefore consistent with consumer-fp64 throughput under the chosen memory layout rather than with a kernel-correctness anomaly. On the CSC strict-IEEE path (AMD EPYC host with an RTX 5090), the same fp64 LW3 $N=400$ case runs in $8.53$~s on CPU and $0.57$~s on GPU as end-to-end solver timing, confirming that an fp64-capable GPU dominates the same code path when the hardware allows it.

- [ ] **Step 3: Optionally, trim the existing hand-wave sentence about memory/layout (line 113-ish) if it is now redundant.**

```bash
sed -n '112,116p' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

If the line `Table~\ref{tab:ch4-runtime-minimatrix} is consistent with fp64 speedup being limited by consumer-GPU fp64 throughput plus the current memory/layout choices,` already conveys the same idea, leave it alone — the new paragraph supersedes it and the Batch 6 compression can trim it if needed.

- [ ] **Step 4: Post-edit audit gate.**

```bash
rg -nF '0.24~TFLOPS' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF '8.53' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF '0.57' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF 'end-to-end solver timing' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
rg -nF 'kernel-correctness anomaly' report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: ≥ 1 hit each.

- [ ] **Step 5: Texcount delta gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Chapter4/chapter4.tex
```

Expected: cumulative delta vs Task 4 within `[+40, +80]`.

- [ ] **Step 6: Abstract sentinel re-check.**

Expected: identical hits.

- [ ] **Step 7: Commit.**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "$(cat <<'EOF'
report1 revision: quantified GPU timing and cross-hardware framing

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Batch 5 — Branch-Rule + Toro3/5 Checkpoint Table + MUSCL Literature + BibTeX

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (Section *Matched CPU/GPU Comparison* Table 5.5 rows on lines 300–302; Section *Compiler, Branch, Solver, and Drift-Growth Sensitivity* Table 5.6 branch-rule row on line 367 and surrounding prose; Section *One-Dimensional Euler Validation* convergence-order paragraph near line 44–52; Section *Two-Dimensional Euler Validation* "report-specific" wording fix on line 165).
- Modify: `report1/phd-thesis-template-2.4/References/references.bib` (append two new entries).

**Word-Δ budget:** +60 / −30 (net ≈ +30).

**Evidence:** `experiments/add_experiment/toolchain_toro35_checkpoints/summary.md` (Toro3/Toro5 fp64/fp32 zero at 4 checkpoints) + `experiments/review3_local_fill/summary.md` (branch-rule expanded coverage) + user-verified BibTeX entries (Wellner 2016 ECCOMAS paper 9251; Berthon 2006 Numer. Math.).

- [ ] **Step 1: Read Chapter 5 lines 300–302 (Toro3 and Toro5 rows of Table 5.5).**

```bash
sed -n '299,303p' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:
```
Sod & fp32, fp64 & 2 at $N=200$ & 8 at $N=200$, to $t=0.25$ & zero \\
Toro3 & fp32, fp64 & 2 at $N=200$ & none & zero \\
Toro5 & fp32, fp64 & 2 at $N=200$ & none & zero \\
```

- [ ] **Step 2: Update Toro3 and Toro5 "Saved checkpoints" entries.**

Edit `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` with `replace_all: false`:

- `old_string`: `Toro3 & fp32, fp64 & 2 at $N=200$ & none & zero \\\nToro5 & fp32, fp64 & 2 at $N=200$ & none & zero \\`
- `new_string`: `Toro3 & fp32, fp64 & 2 at $N=200$ & 4 at $N=200$ (25/50/75/100\% of $t_{\mathrm{end}}$) & zero \\\nToro5 & fp32, fp64 & 2 at $N=200$ & 4 at $N=200$ (25/50/75/100\% of $t_{\mathrm{end}}$) & zero \\`

- [ ] **Step 3: Read Chapter 5 lines 360–386 (Table 5.6 + prose).**

```bash
sed -n '360,390p' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: branch-rule row reads `HLLC branch, $\leq$ vs $<$ & LW3, $200^2$ & $5.03\times10^{-16}$ & $2.04\times10^{-14}$ \\` followed by the rest of Table 5.6.

- [ ] **Step 4: Replace the branch-rule row of Table 5.6 with the expanded coverage row.**

Edit with `replace_all: false`:

- `old_string`: `HLLC branch, $\leq$ vs $<$ & LW3, $200^2$ & $5.03\times10^{-16}$ & $2.04\times10^{-14}$ \\`
- `new_string`: `HLLC branch, $\leq$ vs $<$ & Sod, stationary contact, Toro3, Toro5 = 0; LW3, $200^2$ & $5.03\times10^{-16}$ & $2.04\times10^{-14}$ \\`

- [ ] **Step 5: Read the prose paragraph following Table 5.6 (lines 381–386) and add the Toro 2 degenerate cross-reference.**

Edit with `replace_all: false`:

- `old_string`: `The branch-rule axis is\nzero for the one-dimensional cases and only roundoff-scale for LW3.`
- `new_string`: `The branch-rule axis is zero for the one-dimensional cases (Sod, stationary contact, Toro3, Toro5) and only roundoff-scale for LW3, with Toro 2 treated separately as the degenerate $N_\ast = 0$ case (see Section \emph{Toro Test 2 Branch Stability}: the strict $<$ branch does not complete within a 600~s wall-clock cap while the baseline $\leq$ branch completes in $\approx 0.125$~s).`

- [ ] **Step 6: Read the convergence-order paragraph in Chapter 5 Section *One-Dimensional Euler Validation* (lines 44–52).**

```bash
sed -n '40,55p' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: a paragraph that gives the 0.65–0.79 / 0.47 convergence orders and discusses the band/smooth split.

- [ ] **Step 7: Append the literature anchor sentence at the end of that paragraph.**

Edit with `replace_all: false`:

- `old_string`: the last sentence of the convergence-order paragraph (read it in Step 6 and supply the unique tail including the period).
- `new_string`: same final sentence followed by:

> The observed $L_1$ orders of $0.65$–$0.79$ in 1D and $\approx 0.47$ for LW3 in 2D are consistent with the near-first-order $L_1$ convergence reported in the literature for MUSCL-type schemes on shock-containing problems on uniform grids~\citep{eccomas_2016_muscl, berthon_muscl_hancock, toro2009, leveque_2002}.

- [ ] **Step 8: Fix the "report-specific" wording in Chapter 5 line 165.**

Edit with `replace_all: false`:

- `old_string`: `Against the report-specific $1600^2$ numerical reference`
- `new_string`: `Against the $1600^2$ fp64 numerical reference`

- [ ] **Step 9: Append the two BibTeX entries to `References/references.bib`.**

Read the last 10 lines of the file:

```bash
tail -n 10 report1/phd-thesis-template-2.4/References/references.bib
```

Then append (using `Edit` or `Write`-with-merge — do not overwrite the whole file) these two entries at the end of the file, preceded by one blank line:

```bibtex
@inproceedings{eccomas_2016_muscl,
  author    = {Wellner, Jens},
  title     = {Comparison of Finite Volume High-Order Schemes for the Two-Dimensional {E}uler Equations},
  booktitle = {{VII} European Congress on Computational Methods in Applied Sciences and Engineering ({ECCOMAS Congress 2016})},
  editor    = {Papadrakakis, M. and Papadopoulos, V. and Stefanou, G. and Plevris, V.},
  address   = {Crete Island, Greece},
  month     = jun,
  year      = {2016},
  pages     = {Paper 9251},
  note      = {DLR Institute of Propulsion Technology, Cologne, Germany}
}

@article{berthon_muscl_hancock,
  author  = {Berthon, Christophe},
  title   = {Why the {MUSCL--H}ancock scheme is {$L^1$}-stable},
  journal = {Numerische Mathematik},
  volume  = {104},
  number  = {1},
  pages   = {27--46},
  year    = {2006},
  doi     = {10.1007/s00211-006-0007-4}
}
```

- [ ] **Step 10: Post-edit audit gate.**

```bash
rg -nF 'report-specific' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -n '^@inproceedings\{eccomas_2016_muscl' report1/phd-thesis-template-2.4/References/references.bib
rg -n '^@article\{berthon_muscl_hancock' report1/phd-thesis-template-2.4/References/references.bib
rg -nF 'eccomas_2016_muscl' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -nF 'berthon_muscl_hancock' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -nF '4 at $N=200$ (25/50/75/100' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
rg -nF 'Sod, stationary contact, Toro3, Toro5 = 0' report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected:
- First grep: **0 hits**.
- Remaining six: ≥ 1 hit each (Toro3/5 row appears twice — once per case — so the sixth grep may show 2 hits).

- [ ] **Step 11: PDF round-trip sanity (citations must resolve).**

```bash
cd report1/phd-thesis-template-2.4 && \
  pdflatex -interaction=nonstopmode thesis.tex >/tmp/pdflatex.log 2>&1; \
  bibtex thesis >> /tmp/pdflatex.log 2>&1; \
  pdflatex -interaction=nonstopmode thesis.tex >> /tmp/pdflatex.log 2>&1; \
  pdflatex -interaction=nonstopmode thesis.tex >> /tmp/pdflatex.log 2>&1
grep -nE 'undefined citations|Citation .* undefined' /tmp/pdflatex.log || echo "OK: no undefined citations"
```

Expected: `OK: no undefined citations`. If the two new keys are reported undefined, stop and fix the BibTeX entries.

- [ ] **Step 12: Texcount delta gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Chapter5/chapter5.tex
```

Expected: cumulative delta vs Task 5 within `[+10, +50]`.

- [ ] **Step 13: Abstract sentinel re-check.**

Expected: identical hits.

- [ ] **Step 14: Commit.**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex \
        report1/phd-thesis-template-2.4/References/references.bib
git commit -m "$(cat <<'EOF'
report1 revision: Toro3/5 checkpoints, branch-rule coverage, MUSCL literature anchor

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Batch 6 — Compression Pass + Final Texcount Gate + Evidence Traceability

**Files:**
- Modify (compression only): `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (Section *Extension to Ideal MHD* — single literature sentence trim if needed); `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` (Section *Hardware and Implementation Sensitivity* — shock-bubble packet sentence; Section *Limitations and Report 2 Direction* item 6 if shock-bubble sentence removed).

**Word-Δ budget:** net to land final texcount in `[7750, 7800]`.

- [ ] **Step 1: Current total texcount.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Abstract/abstract.tex \
                        Chapter1/chapter1.tex Chapter2/chapter2.tex \
                        Chapter3/chapter3.tex Chapter4/chapter4.tex \
                        Chapter5/chapter5.tex Chapter6/chapter6.tex \
                        Chapter7/chapter7.tex
```

Record the current total. Compute the manuscript-body word count using the same conversion factor as the 7697 baseline (current `texcount -1` total minus the same constant overhead measured in Task 0). Call this `MS_NOW`.

If `MS_NOW <= 7800`, skip to Step 5 (compression not needed).

If `MS_NOW > 7800`, proceed to Step 2 to apply compression candidates in the order listed below until `MS_NOW` lands in `[7750, 7800]`.

- [ ] **Step 2: First compression candidate — drop the shock-bubble sentence in Chapter 6 Section *Hardware and Implementation Sensitivity*.**

Read Chapter 6 line 82:

```bash
sed -n '80,84p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: a sentence beginning `The shock-bubble packet adds an \(800\times200\) fp64 CPU HLLC morphology cross-check` and ending `…no CPU/GPU comparison is made.`

Edit with `replace_all: false`:

- `old_string`: the verbatim sentence including its trailing period.
- `new_string`: empty string (delete the sentence entirely; keep the surrounding paragraph intact).

Re-check `MS_NOW`. If `MS_NOW` is now in `[7750, 7800]`, skip to Step 5.

- [ ] **Step 3: Second compression candidate — delete Chapter 6 limitations item 6 (now redundant after the shock-bubble sentence is gone).**

Read Chapter 6 lines 103–106:

```bash
sed -n '101,108p' report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: item 6 reads `Limiter and shock-bubble results support method-sensitivity\n        interpretation but do not replace the validation suite.`

Edit with `replace_all: false`:

- `old_string`: `  \item Limiter and shock-bubble results support method-sensitivity\n        interpretation but do not replace the validation suite.\n`
- `new_string`: empty string.

Re-check `MS_NOW`. If now in `[7750, 7800]`, skip to Step 5.

- [ ] **Step 4: Third compression candidate — drop the `bard_dorelli_2014` GPU-precedent sentence in Chapter 3 Section *Extension to Ideal MHD* (only if still over budget).**

Search for it:

```bash
rg -nF 'bard_dorelli_2014' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

If found, read the full sentence and delete it via `Edit` with `replace_all: false`. Re-check `MS_NOW`.

If after Step 4 `MS_NOW` is still out of range, stop and surface to the main process — do not start cutting load-bearing content.

- [ ] **Step 5: Evidence-to-claim traceability spot-check (5 random items).**

For each of the following five items, open the cited `summary.md` file and confirm the inserted number exists verbatim there:

1. p32 noise-to-error > 1 cells = 0 % → `experiments/review3_mca_n30/report1_d2_replots/summary.md`
2. Toro3/Toro5 checkpoint zero → `experiments/add_experiment/toolchain_toro35_checkpoints/summary.md`
3. LW12 observed order 0.5348 → `experiments/add_experiment/lw12_1600_reference/summary.md`
4. LW3 N=400 fp64 CSC timing 8.53 s / 0.57 s → `experiments/add_experiment/lw3_timing_split/summary.md`
5. LW3 RTX 5090 preflight N=400 and N=800 zero → `experiments/add_experiment/lw3_5090_preflight/summary.md`

If any number does not match its source, stop and surface for re-spec.

- [ ] **Step 6: Final forbidden-phrase grep across the whole manuscript.**

```bash
for phrase in \
  'two or three samples' \
  'WSL/GCC strict' \
  'final-output only' \
  'no analogous \(1600^2\) row' \
  'specific total-energy form' \
  'C_CFL throughout' \
  'uniformly 0.8' \
  'Windows BuildTools' \
  'report-facing' \
  'report-specific'; do
    echo "=== $phrase ==="
    rg -nF "$phrase" report1/phd-thesis-template-2.4 || echo "OK: 0 hits"
done
```

Expected: every phrase reports `OK: 0 hits`.

- [ ] **Step 7: Final required-hedge grep across the whole manuscript.**

```bash
for phrase in \
  'saved conservative state' \
  '$n = 30$' \
  'sample-quantile' \
  'low-precision stress diagnostic' \
  'end-to-end solver timing' \
  'order $\approx 0.535$' \
  'preflight at \(N=400\)' \
  'spatial mean of the per-cell sample standard deviation'; do
    echo "=== $phrase ==="
    rg -nF "$phrase" report1/phd-thesis-template-2.4 || echo "MISSING"
done
```

Expected: every phrase prints ≥ 1 hit. Any `MISSING` line is a failure — stop and fix.

- [ ] **Step 8: Abstract sentinel final re-check.**

Re-run the four `rg -nF` commands from Task 0 Step 3. Expected: identical hits.

- [ ] **Step 9: Texcount final gate.**

```bash
cd report1/phd-thesis-template-2.4 && \
  texcount -inc -sum -1 Abstract/abstract.tex Chapter[1-7]/chapter*.tex
```

Convert to manuscript-body word count using the Task 0 conversion. Expected: `7750 ≤ MS_FINAL ≤ 7800`.

- [ ] **Step 10: Full PDF round-trip.**

```bash
cd report1/phd-thesis-template-2.4 && \
  pdflatex -interaction=nonstopmode thesis.tex >/tmp/final.log 2>&1; \
  bibtex thesis >> /tmp/final.log 2>&1; \
  pdflatex -interaction=nonstopmode thesis.tex >> /tmp/final.log 2>&1; \
  pdflatex -interaction=nonstopmode thesis.tex >> /tmp/final.log 2>&1
grep -cE 'undefined citations|Citation .* undefined|undefined references' /tmp/final.log
```

Expected: `0`.

- [ ] **Step 11: Commit compression pass (only if any compression edits were applied).**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex \
        report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "$(cat <<'EOF'
report1 revision: compression pass to land in 7750-7800 word window

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

If no compression edits were applied (i.e. `MS_NOW` was already in window after Batch 5), skip the commit and proceed to Task 8.

---

## Task 8: Final Verification + Handoff

**Files:**
- Read only.

- [ ] **Step 1: Print the final commit log for review.**

```bash
git log --oneline -n 10
```

Expected: at least 6 commits with `report1 revision:` prefix, in batch order.

- [ ] **Step 2: Render the PDF once more and visually inspect Chapter 6 figures.**

```bash
cd report1/phd-thesis-template-2.4 && \
  pdflatex -interaction=nonstopmode thesis.tex >/dev/null 2>&1
```

Open `thesis.pdf`. Spot-check: Fig 6.1 axis label matches the rewritten caption; Figs 6.2 / 6.3 / 6.4 reflect `n = 30` data (not single-realisation).

- [ ] **Step 3: Final spec coverage cross-check.**

Re-read [docs/superpowers/specs/2026-05-26-report1-review3-revision-plan.md](../specs/2026-05-26-report1-review3-revision-plan.md) §3 (subsection edit spec) and §9 (verification checklist). For each item, confirm a corresponding commit in the log. Any item without a commit is a coverage gap — surface to the user before claiming completion.

- [ ] **Step 4: Surface the final wordcount, PDF status, and a one-line summary per batch to the user.**

Format the report as:

```
Wordcount: <MS_FINAL> (target 7750-7800)
PDF: OK / FAIL (citations: <count> undefined, refs: <count> undefined)
Commits:
  - <hash> report1 revision: Chapter 3 Eq 3.21 caption fix, Toro 2 cross-link, per-case CFL
  - <hash> report1 revision: MCA n=30 reframe and Chapter 6 figure refresh
  - <hash> report1 revision: toolchain consolidation on CSC strict-IEEE rerun
  - <hash> report1 revision: LW12 1600 hierarchy and LW3 reference preflight evidence
  - <hash> report1 revision: quantified GPU timing and cross-hardware framing
  - <hash> report1 revision: Toro3/5 checkpoints, branch-rule coverage, MUSCL literature anchor
  - <hash> report1 revision: compression pass to land in 7750-7800 word window  (if applied)
```

- [ ] **Step 5: No commit for this task (verification + handoff only).**

---

## Self-Review

### Spec coverage map
- Spec §3.1 (Eq 3.21 caption) → Task 1 Steps 1–2 ✓
- Spec §3.2 (Toro 2 cross-link) → Task 1 Steps 3–4 ✓
- Spec §3.3 (per-case CFL) → Task 1 Steps 5–6 ✓
- Spec §3.4 (toolchain paragraph) → Task 3 Steps 1–2 ✓
- Spec §3.5 (MCA paragraph) → Task 2 Steps 1–2 ✓
- Spec §3.6 (GPU timing after Table 4.3) → Task 5 Steps 1–2 ✓
- Spec §3.7 (Reference-Solution Strategy LW12 + LW3 preflight) → Task 4 Steps 1–3 ✓
- Spec §3.8 (MUSCL literature) → Task 6 Steps 6–7 ✓
- Spec §3.9 (Table 5.4 LW12 rows + caveat) → Task 4 Steps 4–6 ✓
- Spec §3.10 (Table 5.5 + footnote + final paragraph) → Task 3 Steps 3–7 + Task 6 Steps 1–2 ✓
- Spec §3.11 (Table 5.6 branch-rule row + prose) → Task 6 Steps 3–5 ✓
- Spec §3.12 (Ch6 §"Precision Adequacy" + Fig 6.1 caption + p32 sentence + p8 caveat) → Task 2 Steps 3–7 ✓
- Spec §3.13 (Ch6 §"Hardware and Implementation Sensitivity") → Task 3 Steps 8–9 ✓
- Spec §3.14 (Ch6 limitations items 1, 2, 4) → Task 4 Steps 7–8 (item 1); Task 3 Steps 10–11 (item 2); Task 2 Steps 8–9 (item 4) ✓
- Spec §3.15 (Ch7 §"Limitations") → Task 3 Steps 12–13 ✓
- Spec §3.16 (BibTeX entries) → Task 6 Step 9 ✓
- Spec §11 (pre-execution audit results) → Task 0 + per-batch pre-edit verification step ✓
- Spec §12.1 (figure refresh) → Task 2 Steps 10–11 ✓
- Spec §12.2 (table updates) → Tasks 3, 4, 6 ✓
- Spec §12.3 (evidence-to-claim consistency) → Task 7 Step 5 ✓
- Spec §12.4 (explicit leave-outs) → respected by virtue of file inventory ✓
- Spec §13 (per-batch sub-agent protocol) → encoded as Execution Rules + the explicit pre-edit "Read" + post-edit grep / texcount / Abstract gates in every Task ✓

### Placeholder scan
- No `TBD`, `TODO`, `implement later`, `fill in details` strings in the plan body.
- All `old_string` / `new_string` text is given verbatim, except where Step 1 of each Task explicitly instructs the sub-agent to read the file first to supply the unique-context surrounding bytes — this is necessary because some target paragraphs are paraphrase-sensitive and must be matched against current bytes rather than against a stale plan transcription.

### Type / naming consistency
- Hedge phrases consistent across batches: `saved conservative state`, `$n = 30$`, `low-precision stress diagnostic`, `order $\approx 0.535$`, `end-to-end solver timing`, `preflight at $N=400$` all appear in the same form in every relevant Edit.
- Hardware names consistent: `CSC`, `RTX 4060 Laptop GPU`, `RTX 5090`, `i9-13900H`, `AMD EPYC` — no internal shorthand variants.
- BibTeX keys consistent: `eccomas_2016_muscl`, `berthon_muscl_hancock` referenced in Task 6 Step 7 and added in Task 6 Step 9 — names match.
- Texcount budget deltas sum check: Batch 0 (+50) + Batch 1 (−30) + Batch 2 (−40) + Batch 3 (+70) + Batch 4 (+50) + Batch 5 (+30) + Batch 6 (variable trim) → gross +130 before Batch 6 trim, matching the spec's §8 estimate.

---

**Plan complete and saved to [docs/superpowers/plans/2026-05-26-report1-review3-revision.md](2026-05-26-report1-review3-revision.md). Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
