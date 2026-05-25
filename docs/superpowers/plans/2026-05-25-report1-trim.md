# Report 1 Trim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce Report 1 LaTeX source from 8564 → ≤7700 words (target 7400–7500) while strengthening evidence chain via three substantive replacements (primitive recovery, GPU warp-divergence, Toro2 mechanism) and a new LW/Godunov predecessor block.

**Architecture:** Three phases with checkpoints. One subagent per `.tex` file per related-edit batch, serial execution. P0 (math/algorithm/replacement) tasks: subagent drafts → main agent reviews diff → write. Phase 3 uses git branches for L/H variant comparison; winner merged to `report` branch.

**Tech Stack:** LaTeX source files in `report1/phd-thesis-template-2.4/`. Tools: `Edit`, `Read`, `Grep`, `Bash` (`texcount`, `git`). Subagent type: `general-purpose`.

**Branch context:** Working on branch `report`. Phase 3 creates `report1-variant-L` and `report1-variant-H` branches, then merges winner back.

**Spec reference:** `docs/superpowers/specs/2026-05-25-report1-trim-design.md`

---

## Cross-cutting subagent prompt requirements

Every subagent prompt MUST include the following standing instructions verbatim:

> You are editing a LaTeX thesis. Use only the `Edit` tool for changes; do NOT use `Write` to rewrite whole files. Constraints:
> - Do not change `\label{}`, `\ref{}`, or `\citep{}` keys unless this task explicitly requests it.
> - Do not change equation numbering (deleting an equation only allowed if you first grep for downstream `\ref{<label>}` and find zero hits; report grep output before editing).
> - Do not edit `.bib` files; if you remove a citation, leave the `.bib` entry alone.
> - Preserve mathematical content exactly; replace prose only.
> - Keep paragraph structure (`\paragraph{}` headings, blank-line breaks).
> - After editing, use `Read` to verify the edited region looks correct.
> - Report: original text (excerpt), new text (excerpt), net word delta, 1–2 sentence justification.
> - Use the `superpowers:verification-before-completion` skill before claiming completion if your task touches equation/figure/table refs.

For ADD-type tasks (new prose insertions), additionally:

> Mirror the surrounding chapter's tone and equation-density. Cite via `\citep{key}` matching keys already in `report1/phd-thesis-template-2.4/References/references.bib`. Do not invent new citation keys.

---

## Phase 1 — review3.md Package

**Goal:** Cut ~757 words of repetition/restatement; add ~260 words of mechanistic evidence (A/B/C/Powell). Net −497.

**Expected end state:** ~8067 words.

---

### Task P1.1: Chapter 1 cuts (#1, #2, #3)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter1.tex with three independent cuts:

CUT #1 — §1.1, lines 7-16. Compress the first two sentences (from "Compressible-flow simulations are needed when laboratory measurements..." through "...non-physical oscillations.") into a single opening sentence. Replace with:
"Compressible HRSC methods evolve conserved cell averages with Riemann-solver fluxes, capturing shocks and contact discontinuities without tracking them explicitly~\citep{toro2009}."
Keep the rest of §1.1 unchanged.

CUT #2 — §1.3, lines 33-35. Delete the final sentence: "The contribution is therefore a bounded baseline for the later project rather than a general statement about all HRSC schemes, all hardware, or untested MHD configurations."

CUT #3 — §1.4, lines 39-44. Replace the entire content of §1.4 with one sentence:
"Chapters~2--4 establish background, method, and design; Chapters~5--6 present results and discussion; Chapter~7 concludes."

Report the three before/after excerpts and total word delta (expected ~−132).
```

- [ ] **Step 2: Verify**

```bash
cd report1/phd-thesis-template-2.4 && texcount -inc -1 Chapter1/chapter1.tex 2>&1 | head -5
```
Expected: word count for chapter1 dropped by ~130 from baseline 447.

- [ ] **Step 3: Read modified file**

Read `Chapter1/chapter1.tex` to confirm cuts applied and structure intact.

- [ ] **Step 4: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
git commit -m "Ch1 trim: motivation, scope tail, structure summary"
```

---

### Task P1.2: Chapter 2 — §2.5 delete + Powell add (#4, #16)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter2.tex with two changes:

CUT #4 — §2.5 "Report 1 Gap", lines 175-182. Delete the entire \section{Report 1 Gap} block including the section heading and its contents. (Gap is already covered in §1.3 and §2.2; the section restates without adding evidence.)

ADD #16 — §2.2 end, near line 91. After the sentence ending "...is provided by \citet{bard_dorelli_2014}.", add one sentence:
"Eight-wave formulations \citep{powell_1999} provide an alternative MHD HRSC framework with built-in cleaning, noted here for the Report~2 MHD extension."

Note: powell_1999 must exist in references.bib. If it does not, report missing key and skip the add (do NOT invent the key).

Report before/after excerpts and word delta (expected ~−60).
```

- [ ] **Step 2: Verify references.bib has powell_1999**

```bash
grep -n "powell_1999" report1/phd-thesis-template-2.4/References/references.bib
```
If no match: subagent should have skipped the add. Manual add to .bib is a separate task.

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
git commit -m "Ch2 trim: drop §2.5 gap restatement; add Powell 1999 ref for Report 2"
```

---

### Task P1.3: Chapter 3 §3.3 Rusanov compression (#5)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter3.tex §3.3, lines 295-299. Replace the closing paragraph that begins "This form is useful for comparison because it has a single local signal-speed penalty..." (the entire paragraph through "...described by \citet{toro2009}.") with one sentence:

"Rusanov has no contact-wave branch and stronger numerical diffusion than HLLC \citep{harten_lax_vanleer_1983,toro2009}, which makes the HLLC/Rusanov comparison in Chapter~5 an isolation of the contact-resolving path rather than an accuracy ranking."

Report before/after and word delta (expected ~−40).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "Ch3 §3.3: compress Rusanov framing"
```

---

### Task P1.4: Chapter 4 §4.1 AMReX paragraphs (#7)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter4.tex §4.1 with two cuts and one preserve:

CUT — opening paragraph, lines 8-20 (from "The project brief advises the AMReX block-structured..." through "...the single scalar type in the solver:"). Replace with this opening:

"Report~1 uses a stand-alone CPU/CUDA Euler implementation. The brief permits this, and source-level control of the precision-sensitive decision points enumerated in Section~\ref{sec:precision-sensitive-decisions} (FMA contraction, HLLC branch rule, fast-math reassociation) is easier than through a framework's flux abstraction. The real type is selected at configuration time and is then used as the single scalar type in the solver:"

CUT — closing paragraph, lines 45-54 (from "The stand-alone route is therefore a control..." through "...Euler precision baseline is established."). Delete entirely.

CUT — the four-bullet feature list (currently lines 21-32 area, the "1. fp32/fp64 source-level templating..." enumerate block). Compress to a single sentence after the macro table:

"Four design features make the comparison auditable: source-level \texttt{HRSC\_REAL} templating, the \texttt{ENABLE\_CUDA} build switch with runtime \texttt{device=cpu/gpu} selection, a Python regression harness, and matched-binary CPU/GPU outputs."

Report before/after and word delta (expected ~−140).
```

- [ ] **Step 2: Verify**

```bash
texcount -inc -1 report1/phd-thesis-template-2.4/Chapter4/chapter4.tex 2>&1 | head -5
```
Expected: chapter4 word count drops by ~140 from 1934 baseline.

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "Ch4 §4.1: trim AMReX justification, compress feature list"
```

---

### Task P1.5: Chapter 5 §5.2 and §5.3 numeric recap cuts (#9, #10)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter5.tex with two cuts:

CUT #9 — §5.2, lines 31-44. Replace the third paragraph beginning "The numerical summaries support the same interpretation. At $N=200$..." through "...for these matched cases." with:

"The numerical summaries support the same interpretation. At $N=200$, the conservative-state fp64--fp32 $L_1$ difference spans $\sim10^{-8}$ to $\sim10^{-4}$ across Sod, Toro3, and Toro5; the corresponding reference-scaled density ratios at $N=800$ remain below $10^{-4}$ (Table~\ref{tab:ch5-1d-summary}). These are pairwise precision differences, not separate exact-solution errors. The matched CPU/GPU HLLC comparisons give $L_1=0$, $L_\infty=0$, and $\mathrm{ULP}_{\max}=0$ for both Toro3 and Toro5 in fp64 and fp32 at final time, so the later hardware discussion starts from zero-drift saved one-dimensional final states for these matched cases."

CUT #10 — §5.3, lines 174-196. In the LW3 and LW12 description paragraphs, remove specific numeric values (e.g., "7.89×10^{-3}", "4.95×10^{-3}", "0.966 to 0.982", "2.95×10^{-3}", "1.33×10^{-3}", "0.989 to about 0.996", "3.24×10^{-7}", "1.30×10^{-4}") and replace each numeric clause with a trend statement that points to Table~\ref{tab:ch5-2d-summary}. Keep the qualitative structure (LW3 topology description, LW12 topology description, fp32-fp64 below reference scale).

Example replacement for LW3 paragraph end (keep wording close to existing style): "Against the $1600^2$ numerical reference, the fp64 density $L_1$ error decreases and SSIM increases between $N=200$ and $N=400$ (Table~\ref{tab:ch5-2d-summary}); the same-resolution fp64--fp32 conservative-state $L_1$ difference at $N=400$ remains well below the reference-scale density error."

Same pattern for LW12 paragraph.

Report before/after and word delta (expected ~−120 combined).
```

- [ ] **Step 2: Verify table refs intact**

```bash
grep -c "tab:ch5-1d-summary\|tab:ch5-2d-summary" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```
Expected: ≥2 references each.

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "Ch5 §5.2/§5.3: dedup numeric recap, defer to tables"
```

---

### Task P1.6: Chapter 5 §5.5 audit sentence (#11)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter5.tex §5.5. In the paragraph at lines 347-365 that begins "All 14 final-output comparisons in Table 5.5 are zero in...", delete the sentence:

"A separate audit consolidates 52 hash-backed CPU/GPU metric pairs and two metrics-only LW3 fp64 rows whose raw grids are absent from the working tree."

Keep all other content in that paragraph unchanged.

Report before/after and word delta (expected ~−35).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "Ch5 §5.5: remove internal audit accounting"
```

---

### Task P1.7: Chapter 6 §6.1 LoSoS digit numbers (#13)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter6.tex §6.1 with three numeric removals, preserving ordinal claims:

REMOVE 1 — line 25 region. Replace "for HLLC the median LoSoS rises from about 1.3 digits at \texttt{p8} to about 4.0 digits at \texttt{p32}, while the lower quantiles remain closer to the front-sensitive part of the field." with:
"for HLLC the median LoSoS rises with virtual precision, while lower quantiles stay closer to the front-sensitive part of the field (Fig.~\ref{fig:ch6-losos-quantiles})."

REMOVE 2 — line 34 region. Replace "the smooth interior has a positive median margin of about 1.9 digits, the transition/contact band is slightly negative at about $-0.2$ digits, and the shock-front band is negative at about $-1.8$ digits." with:
"the smooth interior keeps a positive margin while the shock-front band is negative; the transition/contact band sits in between (Fig.~\ref{fig:ch6-region-losos})."

REMOVE 3 — line 34 region (next sentence). Replace "cells with MCA noise above the reference-error scale fall from 61.26\% at \texttt{p8} to 43.51\% at \texttt{p16} and 0\% at \texttt{p32}." with:
"the fraction of cells with MCA noise above the reference-error scale drops monotonically with virtual precision (Fig.~\ref{fig:ch6-noise-error})."

Report before/after and word delta (expected ~−80).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "Ch6 §6.1: defer specific LoSoS digits to figures"
```

---

### Task P1.8: §6.3/§7.3 dedup (#14)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter7.tex §7.3 "Limitation and Next Step". Replace the existing limitations paragraph (preserving the section heading) with two sentences:

"Detailed limitations are listed in Section~\ref{sec:ch6-limits}. Report~2 will extend the framework to ideal-MHD validation with divergence control, applied to the same matched-binary CPU/GPU framework used here."

The §6.3 chapter6.tex content stays unchanged; this edit is only in chapter7.tex.

Note: §6.3 may not have an explicit \label{sec:ch6-limits}. Before editing, run:
  grep -n "label{sec:ch6-limits}\|section{Limitations" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
If the label is missing, also add `\label{sec:ch6-limits}` to the §6.3 section heading line in chapter6.tex. Report grep output and any added label.

Report before/after and word delta (expected ~−50).
```

- [ ] **Step 2: Verify**

```bash
grep -n "sec:ch6-limits" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```
Expected: label in chapter6, ref in chapter7.

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
git commit -m "Ch7 §7.3: point to §6.3 instead of restating limitations"
```

---

### Task P1.P0a: §3.5 primitive recovery enhanced (Add A, #6) — P0

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

- [ ] **Step 1: Dispatch subagent in DRAFT MODE**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

DRAFT MODE: Do NOT write to the file. Return the proposed replacement text only.

Target: chapter3.tex §3.5 lines 391-396, the paragraph beginning "Primitive recovery is one place where small relative changes can become method-visible. The pressure calculation subtracts kinetic energy from total energy..." through "...sampled by the flux."

Goal: Replace this 50-word weak paragraph with a ~120-word mechanistic version that:
1. Names the pressure formula p = (γ-1)(E - ½ρ(u²+v²)) and identifies E - ½ρ|u|² as the cancellation site.
2. Identifies which test cases this matters for: high-Mach regions of LW12 (the upper-right interaction near the shock arc) and Toro5 (colliding-shock star state), where kinetic energy approaches total energy.
3. Connects to sound speed a = √(γp/ρ), feeding into HLLC wave-speed estimates (cite Eq.~\ref{eq:ch3-hllc-wavespeeds}) and S* (cite Eq.~\ref{eq:ch3-hllc-sstar}), amplifying the branch-sensitivity already discussed.
4. Mentions fp32 implications explicitly: fp32 representation of recovered p in these regions inherits reduced relative accuracy, propagating to wave-speed and branch decisions.
5. Cite \citep{higham_2002} for cancellation.

Match the surrounding paragraph density and tone. Use \paragraph{Primitive recovery.} as the lead-in. Net target: existing ~50 words → ~120 words (net +70).

Return:
- Original paragraph (excerpt)
- Proposed replacement (full text)
- Word count of new paragraph
- Citation keys used
```

- [ ] **Step 2: Review draft**

Main agent reviews:
- Does the replacement cite Eq.~\ref{eq:ch3-hllc-wavespeeds} and Eq.~\ref{eq:ch3-hllc-sstar}?
- Are all citation keys present in references.bib?
- Length within ±15 words of 120?
- Tone matches surrounding text?

If issues, send refinement request to same subagent.

- [ ] **Step 3: Apply edit**

```
Subagent prompt:

Apply the approved draft text to chapter3.tex §3.5 lines 391-396, replacing the existing paragraph "Primitive recovery is one place..." entirely.
```

- [ ] **Step 4: Verify**

```bash
grep -n "Primitive recovery" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
grep -c "hllc-wavespeeds\|hllc-sstar" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

- [ ] **Step 5: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "Ch3 §3.5: replace primitive-recovery prose with mechanism (Add A)"
```

---

### Task P1.P0b: §4.2 GPU warp-divergence (Add C, #8) — P0

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch subagent in DRAFT MODE**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

DRAFT MODE: return proposed text only.

Target: chapter4.tex §4.2 lines 124-135, the paragraph beginning "The CUDA path uses separate kernels for boundary handling, face-state construction, flux evaluation, and conservative updates. Reconstruction, flux, and update kernels use 16×16 thread blocks; boundary kernels use 128 threads; and the CFL kernel uses 256 threads with shared memory..."

Goal: Replace the thread-block enumeration paragraph (~110 words) with a ~180-word warp-divergence + memory-bound analysis that:
1. States kernel decomposition (boundary / face-state / flux / update) but without specific block-size numbers.
2. Identifies HLLC branch (Algorithm~\ref{alg:hllc-flux-select}) as a warp-divergence site in mixed-state regions where different threads hit different `if` branches.
3. Notes the cell-major layout is a CPU/GPU comparability choice (same indexing both sides), not a throughput-optimal SoA design.
4. Notes shared memory is used only for CFL block reduction, not as a tiled stencil cache; global memory dominates traffic.
5. Connects to Table~\ref{tab:ch4-runtime-minimatrix}: the fp64 LW3 row showing GPU ≈ CPU is consistent with memory-bound behavior at fp64 bandwidth limit, while fp32 LW3 GPU < CPU is consistent with bandwidth headroom freeing up.
6. Keep the existing sentence "CPU and CUDA share the HLLC branch-rule sensitivity axis" (or equivalent) somewhere in the new paragraph.
7. In the CUDA CFL stage, note "ordered comparisons make the selected ∆t independent of block order" (preserve this claim).

Return:
- Original paragraph (full)
- Proposed replacement (full)
- Word counts (old, new)
- Verify Table 4.3 and Algorithm 3 refs resolve
```

- [ ] **Step 2: Review draft**

Main agent checks: warp divergence claim correct? Table 4.3 reference present? Algorithm ref correct? No new unsupported claim about throughput?

- [ ] **Step 3: Apply edit**

- [ ] **Step 4: Verify and commit**

```bash
grep -n "warp divergence\|memory-bound\|Algorithm.*hllc" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "Ch4 §4.2: replace block-size enumeration with warp-divergence analysis (Add C)"
```

---

### Task P1.P0c: §5.7 Toro2 mechanism (Add B, #12) — P0

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [ ] **Step 1: Dispatch subagent in DRAFT MODE**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

DRAFT MODE: return proposed text only.

Target: chapter5.tex §5.7 "Toro2 Branch Stability", lines 513-524 (entire section content).

Goal: Replace the observational-only paragraph (~95 words) with a ~200-word mechanism analysis that:
1. Restates the observation first: under the same CPU-fp64 toolchain and default CFL, the baseline ≤ branch finishes Toro 123 in ~0.13 s; the strict < branch did not produce a final grid.bin within 600 s.
2. Adds mechanism (citing Eq.~\ref{eq:ch3-hllc-sstar} and Eq.~\ref{eq:ch3-sstar-decomp}): Toro 123 is a symmetric expansion centered at u_L ≈ -u_R, so S_L and S_R have nearly equal magnitudes and S_* sits arbitrarily close to zero. In this configuration, both N_* (numerator) and D_* (denominator) of Eq.~\ref{eq:ch3-sstar-decomp} approach zero; the ratio is ill-conditioned and the rounded sign of S_* can flip between successive sub-steps.
3. Connects to the branch test: at the equality S_* = 0, the ≤ branch routes through F_*L by convention (since 0 ≤ S_*), while < routes through F_*R; rounded sign-flips at every step cause CFL collapse via successive flux-update inconsistency and time-step shrinkage.
4. Keeps "observed non-completion" framing — DO NOT claim the mechanism is proven; explicitly say "this is consistent with the observation but not directly logged".
5. Note that a stage-resolved diagnostic to confirm the trigger is deferred to Report 2.

Return draft + word count + verify both equation refs present.
```

- [ ] **Step 2: Review draft**

Main agent checks: equation refs (3.17 = eq:ch3-hllc-sstar, 3.28 = eq:ch3-sstar-decomp) correctly cited; mechanism claim properly hedged (no overclaim); preserved "observed non-completion" language.

- [ ] **Step 3: Apply edit**

- [ ] **Step 4: Verify and commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "Ch5 §5.7: add Toro2 branch-collapse mechanism to observation (Add B)"
```

---

### Task P1.9: Hedging sweep (#15)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Hedging deduplication sweep. Goal: remove duplicated boundary statements that appear 2+ times across the document. PRESERVE the canonical first occurrence in each thread; remove only repeated copies.

MUST PRESERVE (do NOT touch):
- §2.4 "Virtual precision versus IEEE binary32" paragraph (lines ~160-172 in chapter2.tex) — this is supervisor-flagged critical.
- Table~5.5 footnote (chapter5.tex ~lines 333-339) about toolchain boundary.
- Abstract sentence "equality is claimed only for saved states, not for unsaved intermediate values".
- §5.5 list-item phrasing about ordered max/min reduction.

CANDIDATES TO REVIEW (sample, find and assess each):
1. chapter5.tex §5.5 final paragraph (~lines 374-386): "Saved-checkpoint coverage is uneven by design" segment — this is detailed accounting; if the same info appears in the Table~5.5 footnote, prune the prose version.
2. chapter5.tex §5.5 mid: "The zero-drift statement is bounded to matched within-case strict-HLLC binaries and saved conservative states; it does not cover unsaved primitive states, wave-speed estimates, sub-step values, or other devices, compilers, and solvers." — if §6.2 makes the same claim, prune one.
3. chapter6.tex §6.1 end: "These ratios also compress spatial structure into a norm, so the following diagnostics locate precision pressure rather than introduce a separate IEEE-fp32 claim." — if this idea recurs in §6.2, prune.
4. chapter5.tex §5.4 (~line 268): "These measurements show that, for the tested Euler cases..." — if reduced from a long hedge to two clauses, prune.

For each candidate, report:
- File:line
- Action taken (cut / kept / reworded)
- Word delta

Total target: ~−80 words. Do NOT exceed −100. Err on side of preservation.
```

- [ ] **Step 2: Review subagent report**

Verify no must-preserve item was touched; spot-check sample sentences.

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "Trim: remove repeated hedging across §5.5/§6.1/§6.2"
```

---

### CHECKPOINT 1

- [ ] **Step 1: Run texcount**

```bash
cd report1/phd-thesis-template-2.4 && texcount -inc -sum thesis.tex 2>&1 | grep -E "^Words in text|^Sum count"
```
Expected: Words in text ≈ 8067 (±30).

- [ ] **Step 2: 7-dim manual check**

Read in order:
- Abstract (preserved)
- Ch1 (compressed §1.4)
- Ch2 (no §2.5, Powell present)
- Ch3 (§3.3 compressed, §3.5 primitive recovery enhanced)
- Ch4 (§4.1 trimmed, §4.2 warp divergence added)
- Ch5 (§5.2/§5.3 deferred to tables, §5.5 audit gone, §5.7 mechanism added)
- Ch6 (§6.1 numbers removed, hedging trimmed)
- Ch7 (§7.3 points to §6.3)

Verify no broken refs:
```bash
cd report1/phd-thesis-template-2.4 && grep -rE "\\\\(ref|cref|label){[^}]*}" Chapter*.tex --include="*.tex" | wc -l
```

- [ ] **Step 3: Compile check (optional, if Phase 1 ends close to expected)**

```bash
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex > /tmp/latex.log 2>&1; tail -20 /tmp/latex.log
```
Look for unresolved references or undefined commands. If fatal errors, fix before Phase 2.

- [ ] **Step 4: If checkpoint passes, proceed to Phase 2**

If word count > 8150 (Phase 1 underperformed), pause and re-evaluate before Phase 2.

---

## Phase 2 — Density Refinements

**Goal:** Compress equation block, delete redundant axis listing, rewrite Algorithm 1, merge figures, dedup captions, add LW/Godunov predecessor block.

**Expected end state:** ~8037 words (Phase 1: 8067, plus net +60 from #22 and net −90 from #17/#18).

---

### Task P2.1: §3.2 equation block consolidation (#17) — P0

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

- [ ] **Step 1: Pre-check — grep equation refs**

```bash
cd report1/phd-thesis-template-2.4 && grep -rn "eq:ch3-onesided-jumps\|eq:ch3-limiter-ratio" --include="*.tex"
```
Expected: only the definitions themselves; if downstream `\ref{}` exists, abort the deletion.

- [ ] **Step 2: Dispatch subagent in DRAFT MODE**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

DRAFT MODE: return proposed equation block + surrounding prose.

Target: chapter3.tex §3.2 lines 116-143, the four-equation block (Eq. 3.7 one-sided jumps, Eq. 3.8 sigma=minmod, Eq. 3.9 minmod definition, Eq. 3.10 ratio form).

Goal:
1. Inline Eq. 3.7 (one-sided jumps) into Eq. 3.8: rewrite Eq. 3.8 as
   \[\sigma_i^{(k)} = \operatorname{minmod}\left(\bar U_i^{(k),n} - \bar U_{i-1}^{(k),n},\; \bar U_{i+1}^{(k),n} - \bar U_i^{(k),n}\right)\]
   Delete the standalone Eq. 3.7 block (and its label eq:ch3-onesided-jumps).
2. Keep Eq. 3.9 (minmod case definition) unchanged.
3. Delete Eq. 3.10 (ratio form) entirely, replacing the surrounding prose with one inline sentence: "Equivalently, $\sigma_i^{(k)} = \Phi(r_i^{(k)})\,\delta^+U_i^{(k)}$ with $\Phi(r) = \max(0, \min(1, r))$ for $r_i^{(k)} = \delta^- U_i^{(k)} / \delta^+ U_i^{(k)}$, the standard limited-slope form."
4. Verify no `\ref{eq:ch3-onesided-jumps}` or `\ref{eq:ch3-limiter-ratio}` exists elsewhere; report grep output.
5. Renumbering of remaining equations is automatic in LaTeX; do NOT manually renumber.

Return: draft + grep output + word delta (target −40).
```

- [ ] **Step 3: Review draft**

Main agent checks: equation merge is mathematically equivalent; deleted labels have no downstream refs.

- [ ] **Step 4: Apply edit and verify**

```bash
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex > /tmp/latex.log 2>&1; grep -E "undefined|multiply defined" /tmp/latex.log | head
```
Expected: no new undefined refs.

- [ ] **Step 5: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "Ch3 §3.2: consolidate 4 limiter equations into 2 (inline jumps, drop ratio form)"
```

---

### Task P2.2: §3.5 "Variation axes by status" delete (#18)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter3.tex §3.5. Delete the final paragraph beginning with the `\paragraph{Variation axes by status.}` heading (around lines 488-497), including the heading itself. Content runs from "Variation axes by status. Measured Report~1 axes are the HLLC branch rule, gcc..." through "...are Report~2 axes."

Reason: Ch4§3 enumerates the same matrix; this is duplication.

Report before/after and word delta (expected ~−50).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "Ch3 §3.5: drop variation-axes paragraph (duplicate of §4.3)"
```

---

### Task P2.3: Algorithm 1 rewrite (#19) — P0

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch subagent in DRAFT MODE**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

DRAFT MODE: return proposed Algorithm 1 body only.

Target: chapter4.tex lines 93-104, the `\begin{algorithm}...Algorithm 1 "Report-Level Solver Dispatch"...\end{algorithm}` block.

Goal: Rewrite Algorithm 1 to match the concrete-content style of Algorithm 2 (face-state) and Algorithm 3 (HLLC). Current Algorithm 1 is 7 lines of high-level dispatch ("Read configuration / Select CPU or CUDA / Fill ghost cells..."). Replace with a ≤15-line algorithm that contains real computational steps:

Required content:
- Function header: AdvanceToFinalTime(U⁰, t_end, CCFL)
- Initialize: t ← 0; n_step ← 0; c ← 0 (Kahan compensation)
- While t < t_end:
  - Compute Δt from CFL scan (cite Eq. \eqref{eq:ch4-cfl-scan})
  - Δt ← min(Δt, t_end − t)  // clip
  - If 2D and n_step is even: U ← XSweep(U, Δt); refill ghosts; U ← YSweep(U, Δt); refill ghosts
  - Else if 2D: U ← YSweep(U, Δt); refill ghosts; U ← XSweep(U, Δt); refill ghosts
  - Else: U ← XSweep(U, Δt); refill ghosts
  - (t, c) ← KahanAdd(t, Δt, c)  // compensated time
  - n_step ← n_step + 1
- Return U

Use the same `algorithmic` environment style as Algorithm 2 and 3 (function/state/if/while/return). The XSweep and YSweep should be capitalized procedure names; Kahan accumulation can reference \citep{higham_2002} in the caption or as comment.

Keep the algorithm caption: "Report-Level Solver Dispatch" or rename to "Time-stepping loop (one-dimensional or dimensionally-split 2D)" if clearer.

Return: full algorithm body draft + 1-sentence justification of the new structure.
```

- [ ] **Step 2: Review draft**

Main agent checks: algorithm reflects actual implementation (alternating sweeps, Kahan time, ghost refill); ≤15 lines; no new claims about behavior not supported elsewhere.

- [ ] **Step 3: Apply edit and commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "Ch4 Algorithm 1: rewrite to match Algorithm 2/3 concrete-content style"
```

---

### Task P2.4: §6.1 figure merge (#20)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter6.tex §6.1:

ACTION 1 — Delete Fig 6.1 (vfc_sod_overlay): remove the `\begin{figure}...\label{fig:ch6-vfc-sod-overlay}\end{figure}` block at lines 11-16. In the preceding prose (line 9), the sentence "The Sod overlay in Fig.~\ref{fig:ch6-vfc-sod-overlay} shows how the ensemble spread and significant-digit estimates are read from a one-dimensional diagnostic before the same idea is used on LW3." — replace with: "Verificarlo MCA gives an ensemble spread per cell; before extending to LW3, the same idea is read off a one-dimensional Sod diagnostic."

ACTION 2 — Merge Fig 6.3 (losos_quantiles, lines 27-32) and Fig 6.4 (region_losos_margin, lines 36-41) into a single `\begin{figure}` with two `\subfigure` (or `\begin{minipage}`) panels:
```latex
\begin{figure}[htbp]
\centering
\begin{subfigure}[b]{0.48\textwidth}
  \centering
  \includegraphics[width=\textwidth]{Figs/report1/losos_quantiles_rho.png}
  \caption{Quantile view of raw LoSoS.}
  \label{fig:ch6-losos-quantiles}
\end{subfigure}
\hfill
\begin{subfigure}[b]{0.48\textwidth}
  \centering
  \includegraphics[width=\textwidth]{Figs/report1/region_losos_margin_rho_p32.png}
  \caption{Region-aware margin at \texttt{p32}.}
  \label{fig:ch6-region-losos}
\end{subfigure}
\caption{LoSoS for LW3 density under MCA: quantile distribution (left) and region-aware margin against $s_{\mathrm{req}}$ at virtual precision \texttt{p32} (right).}
\label{fig:ch6-losos-combined}
% TODO: panel-merge in figure pipeline (currently two separate PNGs sharing one figure environment)
\end{figure}
```

Verify subfigure labels still resolve: `\ref{fig:ch6-losos-quantiles}` and `\ref{fig:ch6-region-losos}` must still exist (they are inside the subfigure blocks).

Ensure `\usepackage{subcaption}` is in the preamble; if not, report so it can be added separately.

Report before/after fig environment count and any preamble issues.
```

- [ ] **Step 2: Verify subcaption package**

```bash
grep -n "subcaption\|subfigure" report1/phd-thesis-template-2.4/Preamble/preamble.tex 2>/dev/null
```
If subcaption not in preamble, add it as a separate small edit in this commit.

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git add report1/phd-thesis-template-2.4/Preamble/preamble.tex  # if modified
git commit -m "Ch6 §6.1: drop Sod MCA fig; merge LoSoS quantile + region-margin into subfigure"
```

---

### Task P2.5: Caption dedup (#21)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Caption dedup. Five figures in chapter5.tex have captions that repeat "computed with the MUSCL--Hancock scheme and the HLLC Riemann solver" while the surrounding prose has just said the same.

Targets:
- Fig 5.1 caption: "Sod's shock-tube problem at $N=200$ and output time $t=0.25$, computed with the MUSCL--Hancock scheme and the HLLC Riemann solver. The plotted reference is Toro's exact Euler Riemann solution."
  Change to: "Sod's shock-tube problem at $N=200$ and $t=0.25$; reference is Toro's exact Riemann solution."

- Fig 5.2 caption: similar pattern, change to: "Toro3 at $N=200$ and $t=0.012$; reference is Toro's exact Riemann solution. Case includes a right-running supersonic shock."

- Fig 5.3 caption: change to: "Toro5 at $N=200$ and $t=0.035$; reference is Toro's exact Riemann solution (colliding-shock test)."

- Fig 5.4 caption: change to: "LW3 density schlieren at $400^2$ cells and $t=0.3$, fp64. Reference: $1600^2$ fp64 (Table~\ref{tab:ch5-2d-summary})."

- Fig 5.5 caption: change to: "LW12 density schlieren at $400^2$ cells and $t=0.25$, fp64. Reference: higher-resolution $800^2$ fp64 (not an exact solution)."

Also chapter3.tex:
- Fig 3.1 caption: keep — already minimal.
- Fig 3.2 caption: shorten "Three-wave HLLC structure at an interface: left and right acoustic waves with speeds $S_L$ and $S_R$ bound two star states $U_{*L}$ and $U_{*R}$, separated by a contact discontinuity moving at $S_*$. The sign of these three speeds selects the interface flux in HLLC." → "HLLC interface fan: $S_L, S_*, S_R$ separate $U_L, U_{*L}, U_{*R}, U_R$. The sign of these three speeds selects the flux branch (Eq.~\eqref{eq:ch3-hllc-fluxselect})."

Caption text is counted separately from main text words; this is for reading flow, not main word count. Report each caption before/after.
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "Caption dedup: Fig 3.2, 5.1-5.5 — strip method restatement"
```

---

### Task P2.6: §3.2 LW/Godunov predecessor block (Add D, #22) — P0

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

- [ ] **Step 1: Dispatch subagent in DRAFT MODE**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

DRAFT MODE: return proposed insertion text.

Target: chapter3.tex §3.2 end (after line 186, the sentence "The construction applies identically in the $y$-direction." and before §3.3 heading).

Goal: Insert a ~80-word "Predecessors and contrast" paragraph with two display equations comparing MUSCL-Hancock with its predecessors:

Required content:
1. Open with `\paragraph{Predecessors.}` heading.
2. Mention Godunov's first-order method: piecewise-constant data, Riemann-solver flux at each interface, leading to:
   \[U_i^{n+1} = U_i^n - \frac{\Delta t}{\Delta x}\left[\widehat F(U_i, U_{i+1}) - \widehat F(U_{i-1}, U_i)\right]\]
   Note that piecewise constancy makes Godunov first-order, smearing contacts. Cite \citep{toro2009}.
3. Mention Lax–Wendroff: second-order centred update without limiter:
   \[U_i^{n+1} = U_i^n - \frac{\Delta t}{2\Delta x}(F_{i+1} - F_{i-1}) + \frac{\Delta t^2}{2\Delta x^2}\left[A_{i+1/2}(F_{i+1} - F_i) - A_{i-1/2}(F_i - F_{i-1})\right]\]
   with $A = \partial F / \partial U$. Note Lax–Wendroff is oscillatory near discontinuities because it lacks a limiter. Cite \citep{toro2009}.
4. Close with one sentence: MUSCL-Hancock = limited piecewise-linear reconstruction (vs Godunov constant) + Riemann-solver flux (vs Lax-Wendroff centred), gaining both second-order smooth accuracy and TVD discontinuity behavior \citep{vanleer_1979}.

Total budget: ~80 words of prose + 2 display equations. Do NOT cite Lax-Wendroff 1960 directly (no .bib entry); Toro covers both. Equation labels:
- Godunov: `eq:ch3-godunov`
- Lax-Wendroff: `eq:ch3-lax-wendroff`

Return: full insertion draft.
```

- [ ] **Step 2: Review draft**

Main agent checks: math correctness, citation keys exist, word budget ≤90.

- [ ] **Step 3: Apply edit and commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "Ch3 §3.2: add Godunov/Lax-Wendroff predecessor comparison block (Add D)"
```

---

### CHECKPOINT 2

- [ ] **Step 1: texcount**

```bash
cd report1/phd-thesis-template-2.4 && texcount -inc -sum thesis.tex 2>&1 | grep -E "^Words in text|^Sum count"
```
Expected: ~8037 (Phase 1: 8067 + Phase 2 net −30).

- [ ] **Step 2: LaTeX compile**

```bash
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex > /tmp/latex.log 2>&1; grep -E "undefined|multiply defined|Error" /tmp/latex.log | head -20
```
Expected: no fatal errors. Warning-level undefined refs would be a real problem now (must fix before Phase 3).

- [ ] **Step 3: Variant selection decision**

Use the Phase 2 end count to confirm Phase 3 variant scope:
- If 7977–8100: both variants land below 7700, run both for comparison
- If <7900: Variant L alone may suffice; consider skipping Variant H
- If >8200: Phase 1/2 underperformed; investigate before Phase 3

If both variants planned, proceed.

---

## Phase 3 — Variant L (Light cut, preserve framework)

**Branch:** `report1-variant-L` (off current `report` branch HEAD after Phase 2)

**Expected end state:** ~7637 words.

---

### Task P3L.0: Create variant-L branch

- [ ] **Step 1: Branch**

```bash
cd c:/Users/tangy/Desktop/floatpoint
git checkout -b report1-variant-L
```

---

### Task P3L.1: Tier A — 4 confirmed-safe cuts

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Apply 4 Tier-A cuts (each confirmed safe; total ~−140 words):

CUT 1 — chapter4.tex §4.3 (around lines 287-295). Delete the paragraph beginning "The hardware environment for every reported run is fixed: Intel-class x86_64 host CPU, NVIDIA RTX 4060 Laptop GPU (CUDA compute capability 8.9), CUDA toolkit 12.5..." through "...cross-device portability is outside scope." Hardware info is in Table 4.3 caption and §6.3.

CUT 2 — chapter6.tex §6.1 first paragraph (line 7). Delete the clause "and the corresponding pressure ratio is comparable at $R_p \approx 1.13\times10^{-4}$" within the existing sentence about the largest density ratio. Keep the rest of the sentence intact.

CUT 3 — chapter5.tex §5.3 (around line 219-221). Delete the sentence "Pressure ratios in Table~\ref{tab:ch5-2d-summary} provide a second-field check on the same fp32--fp64 scale, without adding an independent convergence claim for the numerical references."

CUT 4 — chapter5.tex §5.4 (around lines 255-258). Delete the sentence "The pressure ratios in Table~\ref{tab:ch5-2d-summary} remain below the same available fp64-reference scale for the tested grids: LW3 gives $R_p=1.34\times10^{-5}$ and $2.59\times10^{-5}$, while LW12 gives $R_p=3.85\times10^{-5}$ and $1.13\times10^{-4}$ from $200^2$ to $400^2$."

Report each cut and net word delta (expected ~−140).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4 report1/phd-thesis-template-2.4/Chapter5 report1/phd-thesis-template-2.4/Chapter6
git commit -m "[L] Tier A cuts: hardware env, pressure-ratio recap"
```

---

### Task P3L.2: §6.3 Lyapunov compression

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter6.tex §6.3, the final paragraph (around lines 112-125). The current paragraph mentions Lyapunov-exponent estimates with two citations (wolf_etal_1985, eckmann_ruelle_1985). Replace the entire final paragraph (from "Report~2 should extend the framework to ideal-MHD tests with divergence control..." through "...Report~2 will pick it up on the MHD test set.") with:

"Report~2 will extend the Chapter~5 drift-time-series to the MHD test set, where chaotic dynamics motivate Lyapunov-type long-time separation estimates rather than finite-time drift only; Dedner-type cleaning \citep{dedner_2002} or constrained transport \citep{evans_hawley_1988} and the HLLD scheme \citep{miyoshi_kusano_2005} are the candidate MHD-side choices."

Remove the wolf_etal_1985 and eckmann_ruelle_1985 \citep{} keys (.bib entries remain untouched).

Report before/after and word delta (expected ~−60).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "[L] Ch6 §6.3: compress Lyapunov paragraph to one sentence"
```

---

### Task P3L.3: §5.5 sanity check compression

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter5.tex §5.5. Locate the paragraph beginning "As a CPU-only sanity check, an additional WSL/GCC strict CPU rerun of Toro3 and Toro5 retained the same qualitative fp64-vs-fp32 ranking..." (around lines 374-386). Compress this paragraph (sanity check + uneven coverage explanation) into one sentence:

"A CPU-only sanity check (WSL/GCC strict CPU rerun of Toro3 and Toro5) matched the existing strict CPU outputs with zero saved-state drift, and saved-checkpoint coverage is uneven only by design (Sod, LW3, LW12 were re-run with checkpoints; Toro3 and Toro5 emit final output only)."

Report before/after and word delta (expected ~−50).
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "[L] Ch5 §5.5: compress sanity-check + coverage paragraph"
```

---

### Task P3L.4: §4.6 Regression harness — light cut (4 → 2 paragraphs)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter4.tex §4.6 "Regression and Reproducibility Harness" (lines 351-402). Current section has 4 `\paragraph{}` blocks: Layout / What is checked / How the axes are swept / What pass/fail means.

Goal: Compress to TWO paragraphs (no `\paragraph{}` headings, just flowing prose):

PARAGRAPH 1 (combines Layout + What is checked):
"A Python regression harness drives the validation matrix and turns each configuration into an auditable record. The C++ entry point in \texttt{src/} is built by CMake; \texttt{scripts/regression/} carries case-level drivers, and \texttt{tests/py/} holds the \texttt{pytest} units that re-run those drivers on stored references. For one-dimensional cases, the harness reads \texttt{grid.bin} for the candidate run and the analytic exact Riemann solution at the same final time and grid, computes density, momentum, and energy $L_1$, $L_\infty$, and $\mathrm{ULP}_{\max}$, and asserts that each metric is below a per-case tolerance recorded in the test source. For two-dimensional cases, \texttt{run\_comparison.py} block-averages the high-resolution fp64 reference to the candidate grid and reports $L_1$, $L_\infty$, $\mathrm{ULP}_{\max}$, and SSIM; matched CPU/GPU pairs are byte-compared on \texttt{grid.bin}."

PARAGRAPH 2 (combines axis sweep + pass/fail):
"Compiler-flag, branch-rule, device, and precision axes are not hand-driven; each combination is a row in a configuration sweep loaded by \texttt{run\_comparison.py} or the \texttt{precexp} driver, with build label, compiler version, flags, precision, device, command line, and binary hash recorded before metrics are written. A regression failure is one of three things: a metric assert above its stored tolerance, a missing artifact, or a configuration mismatch (precision, device, or solver differing from the manifest), so the matched CPU/GPU zero-drift table in Chapter~5 is the saved output of the harness re-run, not a one-off measurement."

Net target: ~−150 words. Report before/after.
```

- [ ] **Step 2: Verify**

```bash
texcount -inc -1 report1/phd-thesis-template-2.4/Chapter4/chapter4.tex 2>&1 | head -3
```

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "[L] Ch4 §4.6: compress harness section from 4 paragraphs to 2"
```

---

### Task P3L.5: Variant L scoring

- [ ] **Step 1: texcount**

```bash
cd report1/phd-thesis-template-2.4 && texcount -inc -sum thesis.tex 2>&1 | grep "^Words in text"
```
Expected: ~7637.

- [ ] **Step 2: Apply 7-dimensional rubric (Section 7 of spec)**

Read through the variant. For each of A–G, assign a score:
- A. Word count compliance (10): if 7400–7500, 10; 7500–7550, 7; 7550–7700, 5; >7700, 0
- B. Rubric 5-item coverage (25): 5 each — lit review / math theory / code description / validation / write-up
- C. Brief PDF alignment (15): 3 each — Euler scope / 4+ supersonic / 1D+2D / CPU+GPU / fp32+fp64
- D. Supervisor review alignment (15): 3 each — SLIC vs HLLC / mixed precision / vfc_precexp / branch stability / FMA
- E. Evidence chain (15): sample 10 quantitative claims, 1.5 each
- F. Rigor (10): unsupported claims −2 each, virtual-precision distinction must be ≥1, hedging boundaries preserved
- G. Reading flow (10): chapter balance, section transitions, figure-text correspondence, captions

Save the score breakdown to `docs/superpowers/specs/2026-05-25-variant-L-score.md`.

- [ ] **Step 3: Commit score**

```bash
git add docs/superpowers/specs/2026-05-25-variant-L-score.md
git commit -m "[L] Variant L scoring breakdown"
```

---

## Phase 3 — Variant H (Heavy cut, compact)

**Branch:** `report1-variant-H` (off `report` branch HEAD after Phase 2 — NOT off variant-L)

**Expected end state:** ~7507 words.

---

### Task P3H.0: Switch to main and create variant-H branch

- [ ] **Step 1: Return to main and branch**

```bash
cd c:/Users/tangy/Desktop/floatpoint
git checkout report
git checkout -b report1-variant-H
```

---

### Task P3H.1: Tier A — 4 confirmed-safe cuts

Same as P3L.1 — identical Tier A cuts apply.

- [ ] **Step 1: Dispatch subagent** with same prompt as P3L.1.

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4 report1/phd-thesis-template-2.4/Chapter5 report1/phd-thesis-template-2.4/Chapter6
git commit -m "[H] Tier A cuts: hardware env, pressure-ratio recap"
```

---

### Task P3H.2: §6.3 Lyapunov compression

Same as P3L.2.

- [ ] **Step 1: Dispatch subagent** with same prompt as P3L.2.

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "[H] Ch6 §6.3: compress Lyapunov paragraph to one sentence"
```

---

### Task P3H.3: §4.6 Regression harness — heavy cut (4 → 1 paragraph)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter4.tex §4.6 "Regression and Reproducibility Harness" (lines 351-402). Compress the entire 4-paragraph section into a SINGLE paragraph (no `\paragraph{}` headings):

"A Python regression harness drives the validation matrix: \texttt{scripts/regression/} case drivers re-run each configuration against stored references and \texttt{tests/py/} \texttt{pytest} units enforce per-case tolerances on density, momentum, and energy $L_1$, $L_\infty$, and $\mathrm{ULP}_{\max}$. Two-dimensional comparisons add block-averaged $L_1$, $L_\infty$, $\mathrm{ULP}_{\max}$, and SSIM via \texttt{run\_comparison.py}; matched CPU/GPU pairs are byte-compared on \texttt{grid.bin}. Each axis combination (compiler, flag, branch rule, device, precision) is a sweep row that records build label, compiler version, flags, command line, and binary hash so any failure can be re-run from its captured invocation; the matched CPU/GPU zero-drift table in Chapter~5 is the saved output of this harness, not a one-off measurement."

Net target: ~−250 words. Report before/after.
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "[H] Ch4 §4.6: compress harness section to one paragraph"
```

---

### Task P3H.4: §4.1 AMReX paragraph full delete

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch subagent**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

Edit chapter4.tex §4.1. After Phase 1 Task P1.4 (which already trimmed AMReX paragraphs), the opening still contains a multi-sentence justification. Reduce the §4.1 opening (before the table) to ONE sentence:

"Report~1 uses a stand-alone CPU/CUDA Euler implementation; the brief permits this, and source-level control of precision-sensitive decisions (Section~\ref{sec:precision-sensitive-decisions}) is easier than through a framework's flux abstraction. The real type is selected at configuration time and is then used as the single scalar type in the solver:"

Then keep the existing compile-time-definition table unchanged.

After the table, the existing prose continues with "This design keeps the precision comparison to two storage formats..." — keep that paragraph and the toolchain-boundary paragraph and the four-feature compressed sentence (the result of P1.4).

Goal: cut an additional ~80 words from the opening prose alone, beyond P1.4.

Report before/after.
```

- [ ] **Step 2: Commit**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "[H] Ch4 §4.1: reduce AMReX framing to one sentence"
```

---

### Task P3H.5: Variant H scoring

- [ ] **Step 1: texcount**

```bash
cd report1/phd-thesis-template-2.4 && texcount -inc -sum thesis.tex 2>&1 | grep "^Words in text"
```
Expected: ~7507.

- [ ] **Step 2: Apply 7-dimensional rubric**

Same scoring procedure as P3L.5. Save to `docs/superpowers/specs/2026-05-25-variant-H-score.md`.

- [ ] **Step 3: Commit score**

```bash
git add docs/superpowers/specs/2026-05-25-variant-H-score.md
git commit -m "[H] Variant H scoring breakdown"
```

---

## Phase 3 Finalization

### Task PF.1: Compare scores and merge winner

- [ ] **Step 1: Read both score breakdowns side by side**

```bash
diff -y docs/superpowers/specs/2026-05-25-variant-L-score.md docs/superpowers/specs/2026-05-25-variant-H-score.md | head -80
```

- [ ] **Step 2: Compute total scores**

For each variant, sum A+B+C+D+E+F+G out of 100.

Tiebreaker (if equal): Variant L wins ties (preserves more rubric content).

- [ ] **Step 3: Merge winner to `report` branch**

```bash
cd c:/Users/tangy/Desktop/floatpoint
git checkout report
# Replace WINNER with report1-variant-L or report1-variant-H
git merge --no-ff WINNER -m "Phase 3 merge: WINNER selected by 7-dim rubric"
# Delete loser
git branch -D report1-variant-L  # or -H, whichever lost
```

- [ ] **Step 4: Confirm clean state**

```bash
git status
texcount -inc -sum report1/phd-thesis-template-2.4/thesis.tex 2>&1 | grep "^Words in text"
```

---

### Task PF.2: Final hedging micro-sweep (if needed)

**Condition:** Only run this task if the winning variant's word count is still > 7500 after merge.

- [ ] **Step 1: Identify ~30-50 words of remaining hedging**

```
Subagent prompt:

[Insert cross-cutting standing instructions here]

The current word count is N (replace with actual). Goal: reduce by ~M words to land at 7450–7480.

Find 3-5 specific sentences across §5 and §6 that are still redundant hedging or restatement and cut them. For each candidate, report:
- File:line
- Sentence to cut
- Why it's redundant (cite the duplicate location)
- Word delta

Do NOT touch must-preserve sentences (same list as P1.9: §2.4 virtual-precision paragraph, Table 5.5 footnote, abstract main boundary, §5.5 ordered max/min reduction).

If you cannot find M words to cut without touching must-preserve sentences, report so explicitly — do not over-cut.
```

- [ ] **Step 2: Apply approved cuts**

- [ ] **Step 3: Commit**

```bash
git add report1/phd-thesis-template-2.4/
git commit -m "Final micro-sweep: hedging trim to land in 7450-7480"
```

---

### Task PF.3: Final scoring and report

- [ ] **Step 1: Run final scoring on `report` branch HEAD**

Apply the 7-dim rubric one more time. Save final score to `docs/superpowers/specs/2026-05-25-report1-trim-final-score.md`.

- [ ] **Step 2: Generate final report**

```
Subagent prompt:

Generate a one-page summary report covering:
1. Starting word count (8564) → final word count (texcount output)
2. Net delta per phase: Phase 1, Phase 2, Phase 3 (winner), Final sweep
3. Three new substantive additions (A primitive recovery, B Toro2 mechanism, C GPU warp divergence, D LW/Godunov)
4. Final 7-dim score breakdown
5. Known follow-ups: figure-pipeline panel merge for losos figures (Phase 2 #20 marker), any leftover TODO markers

Save to docs/superpowers/specs/2026-05-25-report1-trim-final-report.md.
```

- [ ] **Step 3: LaTeX compile and PDF generation**

```bash
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex && bibtex thesis && pdflatex -interaction=nonstopmode thesis.tex && pdflatex -interaction=nonstopmode thesis.tex
ls -la thesis.pdf
```

- [ ] **Step 4: Final commit**

```bash
git add docs/superpowers/specs/2026-05-25-report1-trim-final-score.md docs/superpowers/specs/2026-05-25-report1-trim-final-report.md
git commit -m "Final score and report for Report 1 trim project"
```

---

## Self-Review (executed by writing-plans skill)

### Spec coverage check

| Spec section | Plan task |
|---|---|
| §2 Strategy: 3 phases | Phase 1 / 2 / 3 sections |
| §3.1 Subagent contract | Cross-cutting standing instructions block |
| §3.2 Trust boundary (P0 review) | DRAFT MODE steps in P1.P0a/b/c, P2.1, P2.3, P2.6 |
| §3.3 Checkpoint protocol | CHECKPOINT 1, CHECKPOINT 2 sections |
| §4 Phase 1 task list (16 items) | Tasks P1.1 through P1.9 + P1.P0a/b/c (covers all 16 items) |
| §5 Phase 2 task list (6 items) | Tasks P2.1 through P2.6 |
| §6 Phase 3 two-variant | Tasks P3L.0–5 and P3H.0–5 |
| §7 Final scoring rubric | Task PF.3 + Variant scoring P3L.5 / P3H.5 |
| §8 External constraints | Standing instructions enforce these |
| §9 Risk mitigations | Pre-grep step in P2.1, DRAFT MODE for P0 |

All spec items mapped to plan tasks. ✓

### Placeholder scan

- No "TBD" / "TODO" / "implement later" present in the plan body itself.
- `% TODO: panel-merge in figure pipeline` in P2.4 is an intentional inline marker for a separate downstream task (figure pipeline), per spec §8. Not a plan placeholder.

### Type consistency

- Variant L / H branch names consistent throughout (`report1-variant-L`, `report1-variant-H`).
- Equation labels consistent: `eq:ch3-onesided-jumps`, `eq:ch3-limiter-ratio`, `eq:ch3-hllc-wavespeeds`, `eq:ch3-hllc-sstar`, `eq:ch3-sstar-decomp`, `eq:ch4-cfl-scan`.
- Figure labels consistent: `fig:ch6-vfc-sod-overlay`, `fig:ch6-losos-quantiles`, `fig:ch6-region-losos`, `fig:ch6-losos-combined`.
- Score file names consistent: `2026-05-25-variant-L-score.md`, `2026-05-25-variant-H-score.md`, `2026-05-25-report1-trim-final-score.md`.

All consistent. ✓
