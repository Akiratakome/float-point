# Report 1 Review 4 Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the Report-1 LaTeX manuscript at ≤ 7820 words by 2026-05-29, addressing all eight items in `review.md` plus user-added Ch2 substantive gaps (finite-volume derivation, MHD depth, floating-point depth) and anti-AI tone polish.

**Architecture:** Serial sub-agent + main-process audit pattern. Each batch is one sub-agent dispatch with a verbatim envelope (target sections, replace/insert text, forbidden phrases, word-delta budget, acceptance criteria). Main process gates each batch on texcount delta + grep audits + pdflatex build before dispatching the next. After all 14 content batches, Phase 1.5 produces a data-driven redundancy audit, Phase 2 executes cuts to land at the safety target, Phase 2.5 catches surviving AI tone, Phase 3 verifies the whole pipeline.

**Tech Stack:** LaTeX (PhDThesisPSnPDF class), BibTeX, siunitx, listings; `texcount` for word measurement; `pdflatex` for build verification; PowerShell-compatible commands on Windows.

**Spec:** [docs/superpowers/specs/2026-05-27-report1-review4-revision-design.md](../specs/2026-05-27-report1-review4-revision-design.md)

---

## File structure

**Manuscript files (chapter prose):**

- `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex` — Batches 1, 8a
- `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` — Batches 2a, 2b, 2c, 2d, 2e, 8b
- `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` — Batch 3a, 8c
- `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` — Batches 3b, 4, 5, 8d
- `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` — Batch 8e
- `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` — Batches 6, 8f
- `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex` — Batch 8g
- `report1/phd-thesis-template-2.4/Abstract/abstract.tex` — Batch 8h

**Configuration files:**

- `report1/phd-thesis-template-2.4/Preamble/preamble.tex` — Batch 7 (siunitx scientific-notation, listings setup)
- `report1/phd-thesis-template-2.4/References/references.bib` — Batches 2a, 2d, 2e, 3b (new bib entries: `sterbenz_1974`, `maddock_boost_multiprecision`, `collange_etal_2015`, `revol_theveny_2014`, `kulisch_2013`, `bailey_borwein_borwein_2015`, `brio_wu_1988`, `einfeldt_1988`)

**Audit deliverables (created during execution):**

- `experiments/review4_redundancy_audit.md` — Phase 1.5 cut list
- `experiments/review4_residual_polish.md` — Phase 2.5 change log
- `experiments/review4_baseline.txt` — Phase 0 texcount snapshot

**Source files (read-only references for listings):**

- `src/euler/hllc.hpp:62-67, 79-84` — `RIEMANN_STRICT_INEQUALITY` `#ifdef` block (for Batch 3a listing)
- `src/main.cpp:30-36` — `HRSC_REAL` typedef + `using Real = HRSC_REAL` (for Batch 3b listing)

---

## Task 0: Pre-flight — baseline, source verification, bib audit

**Files:**
- Create: `experiments/review4_baseline.txt`
- Read-only: `report1/phd-thesis-template-2.4/References/references.bib`, `src/euler/hllc.hpp`, `src/main.cpp`

- [ ] **Step 1: Snapshot baseline wordcount**

Run:
```powershell
texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex > experiments/review4_baseline.txt
Get-Content experiments/review4_baseline.txt
```
Expected: a single integer near 7825. Record it. If the number differs from 7825 by more than 50, stop and ask the user before continuing — the budget model assumes 7825.

- [ ] **Step 2: Verify source files for code listings**

Run:
```powershell
Select-String -Pattern "RIEMANN_STRICT_INEQUALITY" -Path src/euler/hllc.hpp
Select-String -Pattern "HRSC_REAL" -Path src/main.cpp
```
Expected: hits at `hllc.hpp` lines 63 and 80 (the two `#ifdef` blocks); hits at `main.cpp` lines 30, 31, 36.

- [ ] **Step 3: Audit `references.bib` for the eight new entries**

Run:
```powershell
$keys = @("sterbenz_1974","maddock_boost_multiprecision","collange_etal_2015","revol_theveny_2014","kulisch_2013","bailey_borwein_borwein_2015","brio_wu_1988","einfeldt_1988")
foreach ($k in $keys) {
  $hit = Select-String -Pattern "^@\w+\{$k," -Path report1/phd-thesis-template-2.4/References/references.bib
  if ($hit) { Write-Output "EXISTS: $k" } else { Write-Output "MISSING: $k" }
}
```
Expected: every entry reports `MISSING:` (since these are new). Record the list; subsequent batches add them.

- [ ] **Step 4: Verify already-cited entries still resolve**

Run:
```powershell
$existing = @("kahan_1965","parker_1997","denis_etal_2016","sohier_etal_2021","demmel_nguyen_2013","toro2009","leveque_2002","miyoshi_kusano_2005","dedner_2002","evans_hawley_1988","powell_1999","toth_2000","liska_wendroff_2003","bard_dorelli_2014")
foreach ($k in $existing) {
  $hit = Select-String -Pattern "^@\w+\{$k," -Path report1/phd-thesis-template-2.4/References/references.bib
  if ($hit) { Write-Output "OK: $k" } else { Write-Output "BROKEN: $k" }
}
```
Expected: every entry reports `OK:`. Any `BROKEN:` blocks the relevant batch.

- [ ] **Step 5: Confirm clean pdflatex baseline build**

Run (from the manuscript directory):
```powershell
cd report1/phd-thesis-template-2.4
pdflatex -interaction=nonstopmode thesis.tex | Select-Object -Last 30
cd ../..
```
Expected: build completes (may have warnings, but no `Fatal error`). Capture any pre-existing overfull/underfull warnings — those are the **baseline** any later batch must not exceed.

- [ ] **Step 6: Commit the pre-flight artifact**

```powershell
git add experiments/review4_baseline.txt
git commit -m "review4 pre-flight: texcount baseline + source/bib audit"
```

---

## Task 1: Batch 1 — Ch1 new §"Physical Applications and Reproducibility" + polish

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex`

**Targets:** insert new `\section{Physical Applications and Reproducibility}` **before** line 5 (`\section{Context: HRSC Schemes for Discontinuous Compressible Flows}`); apply anti-AI grep polish to existing sections at lines 5 and 10.

**Budget:** +140 raw / −30 = **net +110 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex
```
Record as `pre_b1`. Expected: 7825.

- [ ] **Step 2: Dispatch sub-agent with envelope**

Use the Agent tool (general-purpose) with this prompt verbatim:

```
You are inserting one new \section into Chapter1/chapter1.tex of a LaTeX manuscript and polishing two existing sections. No other files. Read the target file first; do not invent line numbers.

TARGET FILE: report1/phd-thesis-template-2.4/Chapter1/chapter1.tex

EDIT 1 — INSERT new \section before line 5. Content (~140 words, 2 tight paragraphs):

\section{Physical Applications and Reproducibility}
% <<SECTION_NEW_BEGIN>>
Compressible-Euler and HRSC methods underpin engineering and scientific calculations across several settings. External aerodynamics rely on them for supersonic intakes and hypersonic re-entry vehicles; turbomachinery analysis uses them to capture shocks inside transonic compressor and turbine cascades; inertial-confinement fusion modelling needs them at strongly imploding interfaces; astrophysical simulations of jets and shock--bubble interactions sit on the same numerical core~\citep{liska_wendroff_2003,bard_dorelli_2014}. Each of these consumers runs design loops or operating-envelope sweeps that need both fast and accurate solutions.
%
The implementation choices behind those solutions vary between research groups, hardware vendors, and compiler toolchains. Two binary builds of the same algorithm can disagree from precision, FMA contraction, reduction ordering, or branch-rule choices near zero wave speeds. That variability is the question Report 1 quantifies on a controlled Euler validation suite (see Section~\emph{Report Scope and Contribution}).
% <<SECTION_NEW_END>>

EDIT 2 — polish existing \section{Context: HRSC Schemes for Discontinuous Compressible Flows} (line 5) and \section{Precision and Hardware Reproducibility Problem} (line 10). Apply this forbidden-phrase grep gate (case-insensitive, zero hits required after polish):

  in this section, | in this chapter, | it is worth noting that | it should be noted that | importantly, | notably, | crucially, | of note, | the following discussion | as we shall see | we now turn to | may potentially | could possibly | leverages | showcases | facilitates | in order to | a wide range of | plays a (crucial|key|important|significant) role | delve into | delve deeper | seamless | (furthermore,|moreover,|additionally,)\s   <-- only paragraph-initial

For each hit, rewrite the sentence preserving substance. Goals: every sentence has a clear nameable subject; vary sentence length (default short, 8-18 words; at least one sentence ≤ 10 and one ≥ 20 per 4+ sentence paragraph; max 30); introduce one or two plain-register words per paragraph from this acceptable list: drop, gap, match, lines up with, hits, sit at, notice. Avoid elevated traps: ostensibly, nuanced, intricate, multifaceted, paradigm. Do NOT touch \section{Report Scope and Contribution} or \section{Report Structure} except for forbidden-phrase removal.

ACCEPTANCE (you must check before returning):
- texcount delta in [+90, +130] (target +110)
- grep -i for the forbidden list returns 0 hits in Chapter1/chapter1.tex
- new section has exactly two paragraphs between the BEGIN/END markers
- pdflatex builds (run: cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex)

Report back: actual texcount delta; any forbidden-phrase rewrites with old → new shown.
```

- [ ] **Step 3: Audit gate — wordcount delta**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
$delta = $post - $pre_b1
Write-Output "Batch 1 delta: $delta (target +110, range +90..+130)"
```
Expected: delta in [+90, +130]. If outside, dispatch a fix-up sub-agent before continuing.

- [ ] **Step 4: Audit gate — forbidden-phrase grep**

```powershell
$pat = "in this section,|in this chapter,|it is worth noting that|it should be noted that|importantly,|notably,|crucially,|of note,|the following discussion|as we shall see|we now turn to|may potentially|could possibly|leverages|showcases|facilitates|delve into|delve deeper"
$hits = Select-String -Pattern $pat -Path report1/phd-thesis-template-2.4/Chapter1/chapter1.tex -CaseSensitive:$false
if ($hits) { Write-Output "FAIL: forbidden phrases remain"; $hits } else { Write-Output "PASS: forbidden grep clean" }
```
Expected: `PASS`.

- [ ] **Step 5: Build verification**

```powershell
cd report1/phd-thesis-template-2.4
pdflatex -interaction=nonstopmode thesis.tex | Select-String "Error|Warning" | Select-Object -Last 20
cd ../..
```
Expected: no `Fatal error`; warnings ≤ baseline.

- [ ] **Step 6: Commit**

```powershell
git add report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
git commit -m "report1 review4 Batch 1: Ch1 new section + grep polish"
```

---

## Task 2a: Batch 2a — Ch2 §"Floating-Point Arithmetic and Reproducibility" polish

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` (`\section` at line 119 and `\paragraph{Virtual precision versus IEEE binary32.}` at line 163)
- Modify: `report1/phd-thesis-template-2.4/References/references.bib` (add `sterbenz_1974`)

**Budget:** +60 raw / −20 = **net +40 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b2a = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Add `sterbenz_1974` to references.bib**

Append to `report1/phd-thesis-template-2.4/References/references.bib`:

```bibtex
@book{sterbenz_1974,
  author    = {Pat H. Sterbenz},
  title     = {Floating-Point Computation},
  publisher = {Prentice-Hall},
  year      = {1974},
  address   = {Englewood Cliffs, NJ}
}
```

- [ ] **Step 3: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
TARGET SECTION: \section{Floating-Point Arithmetic and Reproducibility} starting at line 119

Four edits inside that section ONLY (do not touch other sections):

EDIT 1: replace the first sentence (currently begins "IEEE floating-point arithmetic uses finite significand and exponent fields...") with a two-sentence opener that defines significand and exponent in plain words BEFORE giving widths. Suggested wording:

  A floating-point number is stored as a sign bit, an integer-encoded \emph{exponent} that fixes the power-of-two scale, and a \emph{significand} that carries the leading binary digits of the value. The field widths chosen by the format set both the relative precision and the dynamic range available to the update.

EDIT 2: locate the sentence "binary32 has a 24-bit significand and normal exponent range roughly $-126$ to $+127$, while binary64 has a 53-bit significand and range $-1022$ to $+1023$". Remove the word "roughly" and tighten the wording so the two halves of the sentence use the same prepositional structure. Note: Batch 2e will later rewrite this whole block for "unbiased exponent" consistency — DO NOT do that work here, just remove "roughly".

EDIT 3: on the sentence introducing Sterbenz's lemma (currently "Sterbenz's lemma gives the narrow exact case: for positive floating-point $x$ and $y$, $x-y$ is exact when $y/2 \le x \le 2y$."), add citation: change to "...Sterbenz's lemma~\citep{sterbenz_1974} gives the narrow exact case...".

EDIT 4: on the compensated-summation sentence (currently "Compensated (Kahan) summation tracks lost low-order bits in a correction term..."), append "...\citep{kahan_1965,higham_2002}." if not already there.

EDIT 5 (trim): in the \paragraph{Virtual precision versus IEEE binary32.} block (starts line 163), remove approximately 20 words of Verificarlo background — that material moves to the new \section{Verificarlo and Monte Carlo Arithmetic} added by Batch 2b. Keep only the binary32-vs-p32 comparison. Specifically: the Verificarlo tool description, MCA-RR description, and noise-model background can shrink to one sentence ("Verificarlo's MCA-RR operator (introduced in Section~\emph{Verificarlo and Monte Carlo Arithmetic}) draws an independent random rounding per elementary operation, sampled at virtual mantissa widths").

ACCEPTANCE:
- texcount delta in [+25, +55] (target +40)
- "roughly" absent from this section
- Sterbenz sentence cites \citep{sterbenz_1974}
- Kahan summation sentence cites \citep{kahan_1965,higham_2002}
- significand and exponent each defined in the first two sentences
- pdflatex builds

Report back actual delta and the list of edits made.
```

- [ ] **Step 4: Audit gates**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 2a delta: $($post - $pre_b2a) (target +40)"
Select-String -Pattern "roughly" -Path report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
Select-String -Pattern "sterbenz_1974" -Path report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```
Expected: delta in [+25, +55]; no "roughly" hits; `sterbenz_1974` cited at least once.

- [ ] **Step 5: Build + commit**

```powershell
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter2/chapter2.tex report1/phd-thesis-template-2.4/References/references.bib
git commit -m "report1 review4 Batch 2a: Ch2 floating-point polish + Sterbenz cite"
```

---

## Task 2b: Batch 2b — Ch2 new §"Verificarlo and Monte Carlo Arithmetic"

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` (insert new `\section` after current §"Floating-Point Arithmetic and Reproducibility" closes at line 176)

**Budget:** +180 raw / 0 = **net +180 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b2b = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter2/chapter2.tex

INSERT a new \section AFTER the existing \section{Floating-Point Arithmetic and Reproducibility} closes (after the % <<SECTION_4_END>> marker, currently line 176), BEFORE the chapter ends. Content (~180 words, exactly 3 paragraphs):

\section{Verificarlo and Monte Carlo Arithmetic}
% <<SECTION_VERIFICARLO_BEGIN>>
Verificarlo is an open-source LLVM-based instrumentation tool developed by Denis, Castro Lopez, Petit, F\`evre, Lamotte and collaborators \citep{denis_etal_2016}. It replaces individual floating-point operations with instrumented variants at compile time, so the resulting binary can probe rounding sensitivity without touching the application source. The tool covers binary32 and binary64 inputs and exposes its instrumentation through a drop-in compiler wrapper called \texttt{verificarlo-c} / \texttt{verificarlo-c++}.

Verificarlo's diagnostic engine is Monte Carlo Arithmetic, introduced by \citet{parker_1997}. MCA replaces each rounded operation with a perturbed variant drawn from one of three operators: random rounding (RR) perturbs only the output, MCA perturbs both input and output, and precision bounding (PB) perturbs only the inputs. Each operator targets a chosen virtual mantissa width $t$, so a single binary can be sampled at $t \in \{8, 16, 32, 53\}$ without recompilation between samples. The distribution-free sample-count rule of \citet{sohier_etal_2021} is $n_{\min} = \lceil \log(1-c)/\log(p)\rceil$ for probability level $p$ and confidence $c$, and ships with the \texttt{significantdigits} Python package used downstream.

This report uses MCA-RR at $t \in \{8, 16, 32, 53\}$ with $n=30$ seeds per (precision, solver) configuration. The \texttt{significantdigits} package supplies the loss-of-significance score used in Chapter~6. Note that \texttt{libinterflop}, the runtime library Verificarlo loads, exposes a non-thread-safe PRNG, so MCA runs are serial in this report. Chapter~4 Section~\emph{Precision and Hardware Variants} applies these settings to LW3 density.
% <<SECTION_VERIFICARLO_END>>

ACCEPTANCE:
- texcount delta in [+160, +200] (target +180)
- new section has exactly 3 paragraphs between markers
- \citep{denis_etal_2016}, \citep{parker_1997}, \citep{sohier_etal_2021} all present
- RR, MCA, PB operators all named
- forward-reference to Chapter 4 §"Precision and Hardware Variants" present
- pdflatex builds; new section appears in ToC
```

- [ ] **Step 3: Audit gates**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 2b delta: $($post - $pre_b2b) (target +180)"
Select-String -Pattern "Verificarlo and Monte Carlo Arithmetic" -Path report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```
Expected: delta in [+160, +200]; section heading appears once.

- [ ] **Step 4: Build + commit**

```powershell
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
git commit -m "report1 review4 Batch 2b: Ch2 new section Verificarlo and Monte Carlo Arithmetic"
```

---

## Task 2c: Batch 2c — Ch2 new §"Finite-Volume Derivation Overview"

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` (insert between line 95 §"HRSC and Benchmark Literature" close and line 119 §"Floating-Point Arithmetic and Reproducibility")

**Budget:** +140 raw / 0 = **net +140 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b2c = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter2/chapter2.tex

INSERT a new \section BETWEEN \section{HRSC and Benchmark Literature} (ends at the % <<SECTION_3_END>> marker, around line 117) AND \section{Floating-Point Arithmetic and Reproducibility} (starts at line 119). Content (~140 words, 2 paragraphs):

\section{Finite-Volume Derivation Overview}
% <<SECTION_FV_BEGIN>>
A scalar conservation law $\partial_t U + \partial_x F(U) = 0$ becomes a finite-volume scheme through one integration. Pick a control cell $C_i = [x_{i-1/2}, x_{i+1/2}]$ and a step $[t^n, t^{n+1}]$, integrate the law over the rectangle, and apply the divergence theorem on the flux term. The result is the cell-average update $\bar U_i^{n+1} = \bar U_i^n - (\Delta t/\Delta x)(\widehat F_{i+1/2} - \widehat F_{i-1/2})$, where $\bar U_i^n$ is the spatial average over $C_i$ at $t^n$ and $\widehat F_{i \pm 1/2}$ is the time-averaged interface flux \citep{toro2009,leveque_2002}.

Conservation now lives at face level: shared faces contribute equal and opposite fluxes to adjacent cells, so summing the update collapses interior exchanges and leaves only boundary contributions. The interface flux $\widehat F$ comes from a local Riemann problem at the cell boundary. The three knobs the rest of this report varies sit inside this picture --- the reconstruction order, the Riemann solver, and the time integrator. The two-dimensional extension, operator splitting, and the explicit MUSCL--Hancock predictor land in Chapter~3 Section~\emph{Finite-Volume Update}.
% <<SECTION_FV_END>>

ACCEPTANCE:
- texcount delta in [+120, +160] (target +140)
- exactly 2 paragraphs between markers
- \citep{toro2009,leveque_2002} present
- forward-reference to Chapter 3 §"Finite-Volume Update" present
- section length stays under 160 words (texcount on the snippet only)
- pdflatex builds; ToC shows the new section
```

- [ ] **Step 3: Audit + build + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 2c delta: $($post - $pre_b2c) (target +140)"
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
git commit -m "report1 review4 Batch 2c: Ch2 new section Finite-Volume Derivation Overview"
```

---

## Task 2d: Batch 2d — Ch2 §"Ideal-MHD Project Context" depth + comparison table

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` (§"Ideal-MHD Project Context", lines 52–93)
- Modify: `report1/phd-thesis-template-2.4/References/references.bib` (add `brio_wu_1988`)

**Budget:** +180 raw / −80 = **net +100 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b2d = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Add `brio_wu_1988` to references.bib**

Append:
```bibtex
@article{brio_wu_1988,
  author  = {Moysey Brio and C. C. Wu},
  title   = {An upwind differencing scheme for the equations of ideal magnetohydrodynamics},
  journal = {Journal of Computational Physics},
  volume  = {75},
  number  = {2},
  pages   = {400--422},
  year    = {1988},
  doi     = {10.1016/0021-9991(88)90120-9}
}
```

- [ ] **Step 3: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
TARGET SECTION: \section{Ideal-MHD Project Context} (line 52, ends around line 93)

Three insertions and one replacement INSIDE this section ONLY:

INSERTION 1 (after the conservation form is fully stated, before the divergence-cleaning sentence — i.e., between current lines 78 and 79). New paragraph (~80 words):

\paragraph{Physical meaning of the MHD wave speeds.}
With the field decomposed into components parallel and perpendicular to the propagation direction, the Alfv\'en speed $c_A = |B_\parallel|/\sqrt{\rho}$ is the propagation speed of incompressible transverse magnetic perturbations along the field. The fast and slow magnetosonic speeds $c_f, c_s$ are the bounding compressible waves that mix gas-pressure and magnetic-pressure restoring forces, with $c_f \ge \max(a, c_A) \ge c_s$. The entropy/contact mode advects with the bulk flow at speed $u_n$ \citep{toro2009,miyoshi_kusano_2005}.

INSERTION 2 (immediately after INSERTION 1). New paragraph (~70 words):

\paragraph{Euler-vs-MHD structural difference.}
Ideal MHD is not strictly hyperbolic: fast and Alfv\'en wave speeds coincide when the transverse field $B_\perp$ vanishes, and slow and Alfv\'en coincide when the parallel field $B_\parallel$ vanishes. These degeneracies break the clean three-wave HLLC picture inherited from Euler. The seven-wave fan shown in Chapter~3 Section~\emph{Extension to Ideal MHD} assumes the non-degenerate case \citep{brio_wu_1988}.

REPLACEMENT 3 (replaces the existing single-paragraph divergence-control remark — around current lines 88-92, ending at the end of the \section block; do not touch the % <<SECTION_2_END>> marker location). New content: one short prose paragraph + one comparison table. The table caption carries the trade-off detail so the prose stays under 30 words.

Cell-centred and staggered formulations split the design space for $\nabla \cdot \mathbf{B}$ control. Constrained transport keeps the divergence at machine zero on a staggered mesh, while hyperbolic cleaning and the eight-wave source approach work on the same cell-centred grid as the gas variables. Table~\ref{tab:ch2-divB-comparison} summarises the trade-offs.

\begin{table}[htbp]
\centering
\small
\begin{tabularx}{\textwidth}{@{}l>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X@{}}
\toprule
Scheme & Divergence treatment & Mesh requirement & Trade-off \\
\midrule
Constrained transport \citep{evans_hawley_1988} & Discrete divergence preserved at machine zero by face-centred update & Staggered mesh; field components live on cell faces & Mesh staggering complicates AMR, interpolation, and ghost-cell handling \\ \addlinespace
Hyperbolic cleaning / GLM \citep{dedner_2002} & Divergence error transported and damped through an auxiliary scalar field $\psi$ & Cell-centred; standard finite-volume mesh & Divergence error never strictly zero; cleaning wave speed $c_h$ adds a CFL constraint \\ \addlinespace
Powell eight-wave \citep{powell_1999,toth_2000} & Divergence error advected with the bulk flow via added source terms & Cell-centred; standard finite-volume mesh & Strict conservation is sacrificed across strong shocks \\
\bottomrule
\end{tabularx}
\caption[Divergence-control approaches for ideal MHD]{Divergence-control approaches for ideal MHD: constrained transport, hyperbolic (Dedner/GLM) cleaning, and Powell eight-wave source terms. Cell-centred (Dedner, Powell) and staggered (CT) split the design space; each scheme accepts a different trade between exact divergence zero, mesh complexity, and conservation across shocks.}
\label{tab:ch2-divB-comparison}
\end{table}

ACCEPTANCE:
- texcount delta in [+80, +120] (target +100)
- "Alfv\'en", "fast magnetosonic", "slow magnetosonic" each appear with their meaning
- "not strictly hyperbolic" appears once with the degenerate-case explanation
- \citep{brio_wu_1988} present
- new table tab:ch2-divB-comparison exists, has exactly 3 rows
- the old single-paragraph divergence-cleaning remark is removed (the one starting "Brackbill and Barnes showed that..." — that may stay, but the Powell/Dedner trade-off prose is replaced by the table)
- pdflatex builds; table renders without overfull warnings
```

- [ ] **Step 4: Audit + build + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 2d delta: $($post - $pre_b2d) (target +100)"
Select-String -Pattern "Alfv|magnetosonic|not strictly hyperbolic|brio_wu_1988" -Path report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Overfull|Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter2/chapter2.tex report1/phd-thesis-template-2.4/References/references.bib
git commit -m "report1 review4 Batch 2d: Ch2 MHD physical meaning + divB comparison table"
```

---

## Task 2e: Batch 2e — Ch2 §"Floating-Point" depth + exponent-range consistency

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex` (§"Floating-Point Arithmetic and Reproducibility")
- Modify: `report1/phd-thesis-template-2.4/References/references.bib` (add `collange_etal_2015`, `revol_theveny_2014`, `kulisch_2013`, `bailey_borwein_borwein_2015`, `einfeldt_1988`)

**Budget:** +150 raw / −20 = **net +130 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b2e = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Add five bib entries**

Append to `references.bib`:

```bibtex
@article{collange_etal_2015,
  author  = {Sylvain Collange and David Defour and Stef Graillat and Roman Iakymchuk},
  title   = {Numerical reproducibility for the parallel reductions on multi- and many-core architectures},
  journal = {Parallel Computing},
  volume  = {49},
  pages   = {83--97},
  year    = {2015},
  doi     = {10.1016/j.parco.2015.09.001}
}

@article{revol_theveny_2014,
  author  = {Nathalie Revol and Philippe Th\'eveny},
  title   = {Numerical reproducibility and parallel computations: Issues for interval algorithms},
  journal = {IEEE Transactions on Computers},
  volume  = {63},
  number  = {8},
  pages   = {1915--1924},
  year    = {2014},
  doi     = {10.1109/TC.2014.2322593}
}

@book{kulisch_2013,
  author    = {Ulrich Kulisch},
  title     = {Computer Arithmetic and Validity: Theory, Implementation, and Applications},
  edition   = {2},
  publisher = {De Gruyter},
  year      = {2013},
  address   = {Berlin}
}

@article{bailey_borwein_borwein_2015,
  author  = {David H. Bailey and Jonathan M. Borwein},
  title   = {High-Precision Arithmetic in Mathematical Physics},
  journal = {Mathematics},
  volume  = {3},
  number  = {2},
  pages   = {337--367},
  year    = {2015},
  doi     = {10.3390/math3020337}
}

@article{einfeldt_1988,
  author  = {Bernd Einfeldt},
  title   = {On {G}odunov-type methods for gas dynamics},
  journal = {SIAM Journal on Numerical Analysis},
  volume  = {25},
  number  = {2},
  pages   = {294--318},
  year    = {1988},
  doi     = {10.1137/0725021}
}
```

- [ ] **Step 3: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
TARGET SECTION: \section{Floating-Point Arithmetic and Reproducibility} (line 119)

This is a follow-up to Batch 2a. Three substantive edits and one consistency fix:

EDIT 1 — exponent-range consistency + "unbiased" clarification. Locate the sentence (already Batch-2a-polished, "roughly" removed) that gives binary32 and binary64 widths. Replace the binary32+binary64 widths sentence(s) with one block using identical phrasing for both:

  The number stored is encoded as a sign bit, a biased exponent field, and a significand field; the IEEE-754 unbiased exponent $e$ is recovered from the stored value by subtracting the format-specific bias. Under round-to-nearest arithmetic, binary32 has a 24-bit significand and a normal unbiased exponent range $e \in [-126, +127]$, while binary64 has a 53-bit significand and a normal unbiased exponent range $e \in [-1022, +1023]$ \citep{ieee754_2019,goldberg_1991}.

EDIT 2 — deepen the parallel-reduction non-associativity paragraph (around current line 146-157, the paragraph beginning "Compiler and device choices add variation."). Add the following two sentences inside that paragraph (after the "Reproducible summation algorithms..." sentence):

  Parallel reductions inherit this sensitivity directly: warp reductions, OpenMP \texttt{reduction(+)}, and \texttt{MPI\_Reduce} all combine partial sums in an order set by thread count, block size, or NUMA topology, so the same input can produce different bit patterns across runs \citep{collange_etal_2015}. Reproducible reductions need an explicit construction, exemplified by ReproBLAS-style pre-rounded splits \citep{demmel_nguyen_2013} and the interval-arithmetic approach of \citet{revol_theveny_2014}.

EDIT 3 — add one short sentence at the end of the same paragraph:

  A Kulisch-style exact accumulator instead stores the full-precision partial sum in a wide fixed-point register, eliminating rounding inside the reduction at the cost of register width \citep{kulisch_2013}; the present solver does not use one.

EDIT 4 — add one sentence inside the \paragraph{Virtual precision versus IEEE binary32.} block (or just after, before the section closes). It contextualises the higher-precision-routes survey:

  Higher-precision routes -- \texttt{Boost.Multiprecision}, \texttt{MPFR}, software fp128 -- are surveyed by \citet{bailey_borwein_borwein_2015} and provide a path beyond binary64 not exercised here.

OPTIONAL CITATION (only if it fits naturally; do not force): \citep{einfeldt_1988} can be added to the HLL-family reference in Chapter 3 §"HLLC and Rusanov Fluxes" (line 209 area). If Chapter 3 work is out of scope for this batch, leave einfeldt_1988 unused — Batch 3a will catch it.

ACCEPTANCE:
- texcount delta in [+110, +150] (target +130)
- "unbiased" appears explicitly with both binary32 and binary64
- binary32 and binary64 width sentences use identical "...has a N-bit significand and a normal unbiased exponent range $e \in [...,...]$" structure
- \citep{collange_etal_2015}, \citep{revol_theveny_2014}, \citep{kulisch_2013}, \citep{bailey_borwein_borwein_2015} all present in this section
- "Kulisch" named once with the "not used here" caveat
- pdflatex builds
```

- [ ] **Step 4: Audit + build + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 2e delta: $($post - $pre_b2e) (target +130)"
Select-String -Pattern "unbiased|Kulisch|collange_etal_2015" -Path report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal|undefined" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter2/chapter2.tex report1/phd-thesis-template-2.4/References/references.bib
git commit -m "report1 review4 Batch 2e: Ch2 floating-point depth (Collange, Revol-Theveny, Kulisch, Bailey)"
```

---

## Task 3a: Batch 3a — Ch3 §"Precision-Sensitive Decision Points" RIEMANN_STRICT_INEQUALITY listing

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (§"Precision-Sensitive Decision Points" line 385 area, before `tab:precision-macros` at line 490)
- Read-only: `src/euler/hllc.hpp:62-67, 79-84`

**Budget:** +80 raw / 0 = **net +80 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b3a = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Read source-file lines (must paste verbatim into listing)**

The exact source from `src/euler/hllc.hpp` lines 62-67 (first `#ifdef` block) is:
```cpp
#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL < Real(0) && Real(0) < S_star) {
#else
    if (SL <= Real(0) && Real(0) <= S_star) {
#endif
```

Confirm before pasting:
```powershell
Select-String -Pattern "RIEMANN_STRICT_INEQUALITY" -Path src/euler/hllc.hpp -Context 0,4 | Select-Object -First 8
```

- [ ] **Step 3: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
TARGET SECTION: \section{Precision-Sensitive Decision Points} (line 385)
INSERTION POINT: immediately before \begin{table}[htbp] at line 490 (the table containing tab:precision-macros)

INSERT this prose + lstlisting:

\paragraph{Strict-inequality branch rule.}
The macro \texttt{RIEMANN\_STRICT\_INEQUALITY} toggles the HLLC branch dispatcher between the baseline non-strict comparator (\(\le\)) and the strict variant (\(<\)) at the wave-speed-near-zero boundary. The macro is read in \texttt{src/euler/hllc.hpp} (Listing~\ref{lst:strict-ineq}); flipping it changes one comparator per branch decision and otherwise leaves the flux algebra untouched. The downstream consequence is analysed in Chapter~5 Section~\emph{Toro Test 2 Branch Stability}.

\begin{lstlisting}[style=fpListing,
  caption={HLLC branch dispatcher: baseline ($\le$) vs strict ($<$) selected at compile time by \texttt{RIEMANN\_STRICT\_INEQUALITY} (\texttt{src/euler/hllc.hpp}, first of two parallel blocks).},
  label=lst:strict-ineq]
#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL < Real(0) && Real(0) < S_star) {
#else
    if (SL <= Real(0) && Real(0) <= S_star) {
#endif
\end{lstlisting}

Optionally, in the existing tab:precision-macros table at line 490, you may shorten the RIEMANN_STRICT_INEQUALITY row's "Build effect" cell to "Selects the strict $<$ HLLC branch rule (see Listing~\ref{lst:strict-ineq})." — this is a small redundancy elimination, not required.

OPTIONAL: while in this section, you may add \citep{einfeldt_1988} to any HLL-family reference in Chapter 3 §"HLLC and Rusanov Fluxes" (around line 209) where the sentence cites the HLL framework. One natural spot: the sentence "The Harten--Lax--van Leer (HLL) family gives a standard approximate-flux framework, and the HLLC extension..." — append \citep{einfeldt_1988} after harten_lax_vanleer_1983. This is for U6 coverage.

ACCEPTANCE:
- texcount delta in [+60, +100] (target +80)
- new lstlisting block compiles (requires \usepackage{listings} from Batch 7 preamble — if Batch 7 has not yet run, this build will fail; that is expected and Batch 7 will resolve it before Task 12)
- \ref{lst:strict-ineq} resolves; cross-ref to Chapter 5 §"Toro Test 2 Branch Stability" resolves
- pdflatex builds (allow listings undefined warning if Batch 7 has not yet run; otherwise must be clean)
```

- [ ] **Step 4: Audit + commit (build may fail until Batch 7 runs — note that in commit message)**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 3a delta: $($post - $pre_b3a) (target +80)"
Select-String -Pattern "lst:strict-ineq" -Path report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "report1 review4 Batch 3a: Ch3 RIEMANN_STRICT_INEQUALITY listing (listings pkg added in Batch 7)"
```

---

## Task 3b: Batch 3b — Ch4 §"Implementation Route" HRSC_REAL listing + Boost cite

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (§"Implementation Route and Comparability Principle", lines 5-29)
- Modify: `report1/phd-thesis-template-2.4/References/references.bib` (add `maddock_boost_multiprecision`)
- Read-only: `src/main.cpp:30-36`

**Budget:** +60 raw / 0 = **net +60 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b3b = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Add Boost.Multiprecision bib entry**

Append to `references.bib`:
```bibtex
@misc{maddock_boost_multiprecision,
  author       = {John Maddock and Christopher Kormanyos},
  title        = {Boost.Multiprecision},
  year         = {2024},
  howpublished = {\url{https://www.boost.org/doc/libs/release/libs/multiprecision/}},
  note         = {Accessed 2026-05-27}
}
```

- [ ] **Step 3: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
TARGET SECTION: \section{Implementation Route and Comparability Principle} (line 5, ends ~line 29)

TWO EDITS:

EDIT 1 — Boost citation. Locate the sentence at lines 22-24 reading "Higher-precision extensions, such as a Boost::Multiprecision route, are outside the Report 1 evidence scope." Change to:

  Higher-precision extensions, such as a Boost.Multiprecision route \citep{maddock_boost_multiprecision}, are outside the Report~1 evidence scope.

EDIT 2 — Insert a lstlisting block immediately AFTER the small tabular at lines 10-20 (the table showing FLOAT_PRECISION compile options), BEFORE the paragraph beginning "This design keeps the precision comparison...". Content (verbatim from src/main.cpp lines 30-36):

\begin{lstlisting}[style=fpListing,
  caption={Compile-time precision selection (\texttt{src/main.cpp}). The build system sets \texttt{HRSC\_REAL} via \texttt{-DFLOAT\_PRECISION=float|double}; every solver object in the main translation unit then uses the single \texttt{Real} alias.},
  label=lst:hrsc-real]
#ifndef HRSC_REAL
#define HRSC_REAL double   // fallback if built without PrecisionConfig
#endif

using Real = HRSC_REAL;
\end{lstlisting}

ACCEPTANCE:
- texcount delta in [+40, +80] (target +60)
- \citep{maddock_boost_multiprecision} present in the Boost sentence
- new lstlisting lst:hrsc-real exists, contains the 5 lines from src/main.cpp verbatim
- pdflatex builds (listings warning OK until Batch 7 runs)
```

- [ ] **Step 4: Audit + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 3b delta: $($post - $pre_b3b) (target +60)"
Select-String -Pattern "maddock_boost_multiprecision|lst:hrsc-real" -Path report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/References/references.bib
git commit -m "report1 review4 Batch 3b: Ch4 HRSC_REAL listing + Boost.Multiprecision cite"
```

---

## Task 4: Batch 4 — Ch4 §"Algorithmic Structure of the Implementation" reflow

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (§"Algorithmic Structure of the Implementation", lines 31-136)

**Budget:** 0 / −80 = **net −80 words** (consolidation; eliminates duplicate "cell-major" mention).

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b4 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
TARGET SECTION: \section{Algorithmic Structure of the Implementation} (line 31, ends around line 136)

This is the section Philip's review flagged for fragmented short sentences and the "cell-major" duplication. Three goals:

1. Eliminate the duplicate "cell-major" mention. The string appears at line 40 and again near line 107. Keep ONE primary mention (in the data-layout paragraph) and one secondary cross-reference (in the CUDA paragraph) — or one mention total if it reads cleanly.

2. Re-cluster the existing prose into exactly THREE coherent paragraphs in this order, keeping Algorithms 1, 2, and 3 in their current positions:

   PARAGRAPH A — Data layout and per-cell arithmetic.
   Subject: the conservative array, the cell-major indexing, the same indexing on CPU loops and GPU kernels, the comparability trade-off vs structure-of-arrays. ~80 words.

   PARAGRAPH B — CFL selection, write path, and time accumulation.
   Subject: the CFL scan as ordered max/min (with Eq. \ref{eq:ch4-cfl-scan}), the conserved-state write path with no FP summation reductions, the Kahan-compensated simulation-time counter. ~80 words.

   PARAGRAPH C — CUDA/OpenMP threading, warp divergence, and MPI absence.
   Subject: the kernel decomposition (boundary, face-state, flux, conservative update, block-wise CFL reduction), the HLLC flux kernel as the principal warp-divergence site, the OpenMP static schedule and reduction(max:...) deterministic comparison, the libinterflop serial-PRNG constraint, the no-MPI scope. ~100 words.

3. Apply the forbidden-phrase grep gate from the spec §3 and the rhythm rules (default short 8-18 words; per 4+ sentence paragraph, at least one ≤ 10 and one ≥ 20; max 30 words per sentence; one or two plain-register words per paragraph from: drop, gap, match, lines up with, hits, sit at, notice).

ACCEPTANCE:
- texcount delta in [-100, -60] (target -80)
- Select-String -Pattern "cell-major" returns at most 2 matches in this section
- exactly 3 prose paragraphs + Algorithms 1, 2, 3 in the section body
- forbidden-phrase grep returns 0 hits in this section
- pdflatex builds; Algorithm cross-references still resolve
```

- [ ] **Step 3: Audit + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 4 delta: $($post - $pre_b4) (target -80)"
$cm = (Select-String -Pattern "cell-major" -Path report1/phd-thesis-template-2.4/Chapter4/chapter4.tex).Count
Write-Output "cell-major hits in Chapter4: $cm (must be <= 2)"
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "report1 review4 Batch 4: Ch4 Algorithmic Structure reflow (3 paragraphs, dedup cell-major)"
```

---

## Task 5: Batch 5 — Ch4 later sections reflow

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` — four sections: `\section{Precision and Hardware Variants}` (line 138), `\section{Test-Case Matrix and Metrics}` (line 205), `\section{Reference-Solution Strategy}` (line 292), `\section{Regression and Reproducibility Harness}` (line 327)

**Budget:** 0 / −40 = **net −40 words** (lighter-touch reflow than Batch 4).

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b5 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
TARGET SECTIONS:
  - \section{Precision and Hardware Variants} (line 138, ends ~line 203)
  - \section{Test-Case Matrix and Metrics} (line 205, ends ~line 290)
  - \section{Reference-Solution Strategy} (line 292, ends ~line 325)
  - \section{Regression and Reproducibility Harness} (line 327, ends ~line 354)

Philip's review said the §4.2 paragraph-reflow criticism applies to these later sections too. Lighter touch than Batch 4 — these are less fragmented but still suffer from short-sentence runs.

For each of the four sections:
1. Identify any run of 4+ short sentences (each < 12 words) and merge into longer coherent sentences grouped by idea.
2. Identify any paragraph that opens by restating the \section heading — rewrite the opener.
3. Apply the forbidden-phrase grep gate from spec §3.
4. Apply rhythm and plain-register-vocabulary rules per the §3 style targets.

DO NOT remove any factual claim, table reference, equation reference, or citation. The goal is consolidation and rhythm, not content cuts.

ACCEPTANCE:
- texcount delta in [-55, -25] (target -40)
- forbidden-phrase grep returns 0 hits in each of the 4 sections
- no paragraph opens by restating its section heading
- pdflatex builds; all \ref and \citep still resolve
```

- [ ] **Step 3: Audit + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 5 delta: $($post - $pre_b5) (target -40)"
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "undefined|Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "report1 review4 Batch 5: Ch4 later sections light reflow"
```

---

## Task 6: Batch 6 — Ch6 LoSoS definition + concept first-use audit

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` (§"Precision Adequacy and Region-Aware Diagnostics", line 5)

**Budget:** +40 raw / 0 = **net +40 words**.

- [ ] **Step 1: Snapshot pre-batch wordcount**

```powershell
$pre_b6 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Verify LoSoS definition against figure-generation script (if present)**

```powershell
Select-String -Pattern "losos|LoSoS|loss.of.significance" -Path scripts/figures/report1_d2_replots.py -SimpleMatch:$false -CaseSensitive:$false
```
Expected: definition either matches `-log10(sigma/|q|)` or similar. Note the exact formula for the sub-agent envelope.

- [ ] **Step 3: Dispatch sub-agent with envelope**

Agent prompt verbatim:

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
TARGET SECTION: \section{Precision Adequacy and Region-Aware Diagnostics} (line 5)

THREE EDITS:

EDIT 1 — LoSoS definition. Currently the term "LoSoS" first appears around line 18 ("The loss-of-significance score LoSoS gives a complementary view..."). INSERT a definition sentence BEFORE that line, at the end of the paragraph that introduces \sigma_FP (around line 17, after the figure ref):

  The \emph{loss-of-significance score} (LoSoS) for a primitive component $q$ at cell $\mathbf{x}$ is $\mathrm{LoSoS}(\mathbf{x}) = -\log_{10}\!\bigl(\sigma_{\mathrm{FP},q}(\mathbf{x})/|q(\mathbf{x})|\bigr)$ --- the number of base-10 digits of $q$ that remain significant under the MCA noise scale $\sigma_{\mathrm{FP},q}$ defined in Chapter~4 Section~\emph{Precision and Hardware Variants} \citep{sohier_etal_2021}.

EDIT 2 — define $s_{\mathrm{req}}$. The term appears at line 20 ("The required-significant-digits threshold $s_{\mathrm{req}}$..."). The current sentence already names it but does not say what value or how it is chosen. Add a clause:

  The required-significant-digits threshold $s_{\mathrm{req}}$ --- the number of significant digits a downstream consumer needs at the chosen reference-error scale --- turns LoSoS into a regional margin.

EDIT 3 — Verificarlo cross-reference. Locate the first prose mention of Verificarlo in this chapter (probably around the MCA toolchain reference at line 8). Add an explicit cross-reference: "...(see Chapter~2 Section~\emph{Verificarlo and Monte Carlo Arithmetic})".

ALSO apply the forbidden-phrase grep gate from spec §3 and the rhythm rules across the whole §"Precision Adequacy and Region-Aware Diagnostics" section.

ACCEPTANCE:
- texcount delta in [+25, +55] (target +40)
- "LoSoS" defined before any later use in this chapter (regex check: the definition line must precede line 18-ish later uses)
- $s_{\mathrm{req}}$ has a one-line definition before its first computational use
- Verificarlo cross-reference resolves to new Ch2 section from Batch 2b
- forbidden-phrase grep returns 0 hits in this section
- pdflatex builds
```

- [ ] **Step 4: Audit + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 6 delta: $($post - $pre_b6) (target +40)"
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "undefined|Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "report1 review4 Batch 6: Ch6 LoSoS + s_req definitions + Verificarlo crossref"
```

---

## Task 7: Batch 7 — Preamble siunitx scientific-notation + listings setup

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Preamble/preamble.tex`

**Budget:** 0 / 0 = **net 0 words** (preamble changes do not count toward texcount).

- [ ] **Step 1: Snapshot pre-batch wordcount (sanity check)**

```powershell
$pre_b7 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Read current siunitx config**

```powershell
Select-String -Pattern "sisetup|usepackage\{siunitx\}" -Path report1/phd-thesis-template-2.4/Preamble/preamble.tex -Context 1,8
```
Expected: existing block at lines 91 and 102-109. The current `output-exponent-marker = \ensuremath{\mathrm{e}}` is what produces the "9.34e-8" style.

- [ ] **Step 3: Edit preamble — switch siunitx + add listings**

Edit `report1/phd-thesis-template-2.4/Preamble/preamble.tex`.

REPLACE the existing `\sisetup{...}` block (lines 102-109) with:
```latex
% siunitx alignment for tables — scientific-notation output for review 4
\sisetup{
  table-format            = 1.3e-2,
  table-number-alignment  = center,
  scientific-notation     = true,
  exponent-product        = \times,
  output-exponent-marker  = {},
  detect-weight           = true,
  detect-family           = true,
}
```

ADD immediately after the siunitx block, before the next package:
```latex
% Code listings for review 4
\usepackage{listings}
\lstdefinestyle{fpListing}{
  basicstyle       = \ttfamily\footnotesize,
  keywordstyle     = \color{fpDarkBlue}\bfseries,
  commentstyle     = \color{fpGray}\itshape,
  stringstyle      = \color{fpCyanGreen},
  showstringspaces = false,
  frame            = lines,
  framerule        = 0.4pt,
  rulecolor        = \color{fpGray},
  numbers          = none,
  captionpos       = b,
  breaklines       = true,
  language         = C++,
}
```

- [ ] **Step 4: Build verification + visual spot check**

```powershell
cd report1/phd-thesis-template-2.4
pdflatex -interaction=nonstopmode thesis.tex | Select-String "Error|Fatal|undefined" | Select-Object -Last 30
cd ../..
```
Expected: clean build. Open the resulting `thesis.pdf` and visually verify:
- Tables 5.1, 5.3, 5.4, 5.5, 5.6, 5.7 render `$X.XX\times10^{-Y}$` formatting (no literal "e" in entries).
- The two listings from Batches 3a, 3b render with monospace text and the fpListing frame.

If any table column overflows due to wider scientific-notation output, narrow that specific column width in the table source (not in the preamble).

- [ ] **Step 5: Wordcount sanity + commit**

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 7 delta: $($post - $pre_b7) (target 0)"
git add report1/phd-thesis-template-2.4/Preamble/preamble.tex
git commit -m "report1 review4 Batch 7: preamble siunitx scientific-notation + listings pkg"
```

---

## Task 8: Batch 8 — Anti-AI-tone polish across all chapters (8 sub-batches)

**Files:** every chapter file + abstract. Each sub-batch is one sub-agent dispatch on one file.

**Budget:** 0 / −60 total across all sub-batches = **net −60 words** (rhythm + length rules naturally compress).

Each sub-batch follows the same envelope. The envelope below is for **8c (Chapter 3)** as the template; copy and substitute the file path and section list for the other sub-batches.

- [ ] **Step 1: Snapshot pre-batch wordcount (once, before 8a)**

```powershell
$pre_b8 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

### Sub-batches 8a through 8h

For each row below, dispatch the envelope (next step), wait for completion, audit, commit, then proceed to the next row:

| Sub-batch | File | Sections to polish |
|---|---|---|
| 8a | `Chapter1/chapter1.tex` | All 5 sections (now including new §"Physical Applications and Reproducibility") |
| 8b | `Chapter2/chapter2.tex` | All 5 sections (now including new §"Finite-Volume Derivation Overview" and §"Verificarlo and Monte Carlo Arithmetic") |
| 8c | `Chapter3/chapter3.tex` | All 6 sections + their `\paragraph{}` blocks |
| 8d | `Chapter4/chapter4.tex` | All 6 sections (light-touch follow-up to Batches 3b/4/5) |
| 8e | `Chapter5/chapter5.tex` | All 7 sections + 2 `\subsection*{}` blocks |
| 8f | `Chapter6/chapter6.tex` | All 3 sections (light-touch follow-up to Batch 6) |
| 8g | `Chapter7/chapter7.tex` | All 3 sections |
| 8h | `Abstract/abstract.tex` | Whole abstract |

- [ ] **Step 2: Per-sub-batch envelope (template — substitute file path)**

Agent prompt verbatim (example for 8c — Chapter 3):

```
TARGET FILE: report1/phd-thesis-template-2.4/Chapter3/chapter3.tex

This is the dedicated anti-AI-tone polish pass. Do NOT change any factual claim, equation, table reference, figure reference, or citation. The goal is rhythm, subject clarity, and forbidden-phrase removal.

EIGHT-STEP PROCEDURE:

1. Grep this case-insensitive forbidden list in the file; for every hit, rewrite the sentence preserving substance:
   in this section, | in this chapter, | it is worth noting that | it should be noted that | importantly, | notably, | crucially, | of note, | the following discussion | as we shall see | we now turn to | may potentially | could possibly | leverages | showcases | facilitates | in order to | a wide range of | delve into | delve deeper | seamless | plays a (crucial|key|important|significant) role
   Also paragraph-initial only: furthermore, | moreover, | additionally,

2. Subject-clarity pass: for each sentence, name the subject in one or two words ("the solver", "Table 5.5", "the matched build", "the kernel"). Sentences whose subject is "this", "it", "the comparison", or "the analysis" without a clear antecedent get rewritten. Sentences starting "It is the case that..." or "There exists..." get rewritten with a named subject.

3. Length pass: split any sentence over 30 words. If a paragraph has 4+ sentences and none ≤ 10 words, add a short one or split a medium one. If a paragraph has no sentence ≥ 20 words, glue two related short ones with a real connective (because, since, while, after).

4. Rhythm pass: no run of 4+ short sentences and no run of 3+ long sentences inside a paragraph.

5. Plain-register vocabulary: introduce 1-2 plain swaps per major paragraph from this acceptable list: drop, gap, match, lines up with, hits, sit at, notice, pick up. AVOID elevated traps: ostensibly, nuanced, intricate, multifaceted, paradigm, quintessential. The goal is to break the "every word is the most predictable next word" pattern, not to sound clever.

6. Paragraph-opener pass: no paragraph opens by restating its \section{} heading. If the heading says "HLLC and Rusanov Fluxes" the first sentence is not "The HLLC and Rusanov fluxes are...".

7. Tricolon audit: cap "X, Y, and Z" patterns at 2 per paragraph.

8. Replace: utilise/utilises → use/uses; leverages → uses; showcases → shows; facilitates → lets/enables; marketing "demonstrates" (where "shows" fits) → shows; methodology → method (unless distinguishing).

REPORT BACK:
- texcount delta for this file
- for each prose subsection: longest sentence word count, shortest sentence word count, paragraph count
- list of forbidden-phrase rewrites with old → new (no more than 10 lines)

ACCEPTANCE:
- texcount delta in [-15, +5] for this file (this sub-batch is consolidation, not addition)
- forbidden-phrase grep returns 0 hits
- no reported longest sentence > 30 words
- no paragraph with ≥ 4 sentences fails the ≤10 / ≥20 rhythm rule
- pdflatex builds (run after this sub-batch)
```

- [ ] **Step 3: Per-sub-batch audit + commit**

After each sub-batch completes:

```powershell
$post = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Sub-batch 8X delta: $($post - $pre_subbatch)"
$forbidden = "in this section,|in this chapter,|it is worth noting|it should be noted|importantly,|notably,|crucially,|of note,|delve into|may potentially|could possibly|leverages|showcases|facilitates"
Select-String -Pattern $forbidden -Path report1/phd-thesis-template-2.4/<CHAPTER>/chapter*.tex -CaseSensitive:$false
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/<CHAPTER>/chapter*.tex
git commit -m "report1 review4 Batch 8X: anti-AI polish <Chapter X>"
```

- [ ] **Step 4: After all 8 sub-batches, summary check**

```powershell
$post_b8 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Batch 8 total delta: $($post_b8 - $pre_b8) (target -60)"
Write-Output "Post-Phase-1 wordcount: $post_b8 (expected ~8525)"
```
Expected: ~8525. If over 8550, escalate to user before Phase 1.5.

---

## Task 9: Phase 1.5 — Redundancy and zero-info audit

**Files:**
- Create: `experiments/review4_redundancy_audit.md`
- Read-only: all chapter files

- [ ] **Step 1: Snapshot post-Phase-1 wordcount**

```powershell
$post_p1 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Post-Phase-1: $post_p1; target after Phase 2: 7820; gap to cut: $($post_p1 - 7820)"
```
Expected gap: ~705 words.

- [ ] **Step 2: Dispatch redundancy-audit sub-agent**

Agent prompt verbatim:

```
You are auditing the post-Phase-1 Report 1 manuscript for cuttable material. Total cut target: roughly 705 words.

INPUTS:
- All chapter files under report1/phd-thesis-template-2.4/Chapter1/ through Chapter7/ and Abstract/abstract.tex.

PROCEDURE:

1. Read each chapter end-to-end with fresh eyes. For each section, build two lists:

   REDUNDANT-VIEWPOINT LIST: sentences or paragraphs that restate a claim made earlier in the report. Format per entry:
     - file:lines | claim restated | first appearance (file:lines) | proposed cut wordcount

   ZERO-INFO LIST: sentences that, if deleted, lose nothing the reader needs. Common patterns: meta-restatement of the section purpose; "this is not a claim of X" hedges already established three paragraphs earlier; table captions that paraphrase the surrounding prose verbatim; transition sentences that announce what the next paragraph will say.

2. Cross-chapter overlap pass. For each pair (Ch_i, Ch_j) where i < j, list any concept covered in both with similar wording. Hot spots to check first:
   - Ch2 §"Ideal-MHD Project Context" (after Batch 2d expansion) vs Ch3 §"Extension to Ideal MHD"
   - Ch5 §"Validation Overview" vs Ch6 §"Precision Adequacy..." opening
   - Ch5 §"Matched CPU/GPU Comparison" closing vs Ch6 §"Hardware and Implementation Sensitivity"
   - Ch6 §"Limitations..." vs Ch7 §"Limitation and Next Step"

3. OUTPUT to experiments/review4_redundancy_audit.md a markdown table with columns:
   Priority | File | Lines | Current words | Proposed words | Cut delta | Type | Rationale

   Priority 1 = high-confidence cut (clear redundancy, no information loss).
   Priority 2 = medium-confidence cut (some judgment call, reader could miss the omitted clause).
   Priority 3 = low-confidence cut (only if needed to hit budget).

   Sum the Priority 1 cuts; that subtotal must be ≥ 500 words for the audit to be sufficient. Sum across all priorities must be ≥ 705 words.

4. If the audit total falls short of 705, also list a "borderline" section at the end with cuts that need user approval (e.g., trimming a citation, removing a secondary qualifying clause that the reviewer might want).

DELIVERABLE: experiments/review4_redundancy_audit.md

NO EDITS to .tex files in this phase. The audit is read-only.
```

- [ ] **Step 3: Verify the audit deliverable**

```powershell
Get-Content experiments/review4_redundancy_audit.md | Select-Object -First 50
```
Expected: a markdown table with ≥ 705 words total proposed cuts, ≥ 500 of which are Priority 1.

- [ ] **Step 4: Commit the audit deliverable**

```powershell
git add experiments/review4_redundancy_audit.md
git commit -m "report1 review4 Phase 1.5: redundancy audit (target -705 words)"
```

- [ ] **Step 5: If audit total < 705, escalate to user before Phase 2**

If the audit produces less than 705 cuttable words, stop. Present the partial list and the borderline candidates to the user; do not improvise additional cuts in Phase 2.

---

## Task 10: Phase 2 — Execute cuts driven by the audit

**Files:** chapter files identified in `experiments/review4_redundancy_audit.md` (variable)

- [ ] **Step 1: Snapshot pre-Phase-2 wordcount**

```powershell
$pre_p2 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Pre-Phase-2: $pre_p2; target: 7820; gap: $($pre_p2 - 7820)"
```

- [ ] **Step 2: Dispatch cut-execution sub-agent**

Agent prompt verbatim:

```
You are executing the cut list in experiments/review4_redundancy_audit.md against the Report 1 manuscript. Goal: land texcount ≤ 7820 with at least a 5-word buffer.

PROCEDURE:

1. Read experiments/review4_redundancy_audit.md fully.

2. Execute Priority 1 cuts first, in the order they appear in the audit. After every ~150 words of cuts, run texcount and re-evaluate the remaining gap.

3. Once Priority 1 is exhausted, execute Priority 2 cuts only until texcount ≤ 7820 with 5+ word buffer.

4. If texcount ≤ 7820 before all proposed cuts are executed, STOP. Do not exceed the proposed cut list. Note in your report which cuts were skipped.

5. If texcount > 7820 after all Priority 1 + 2 cuts, ESCALATE: do NOT improvise additional cuts. Report the gap to the user.

6. For each cut, log a one-line entry in experiments/review4_cut_log.md with format:
   - file:lines | old_word_count | new_word_count | delta | priority | rationale_one_sentence

ACCEPTANCE:
- texcount ≤ 7820 (with 5+ word safety buffer, so ≤ 7815 preferred)
- experiments/review4_cut_log.md exists with one line per executed cut
- pdflatex builds; no \ref or \citep newly undefined
- no Batch-1-through-8 ADDITIONS are undone (cuts target only material flagged in the audit, which is by construction pre-Phase-1 content + post-Phase-1 redundancies; new sections from Batches 1, 2b, 2c, 2d table stay intact)
```

- [ ] **Step 3: Verify target reached**

```powershell
$post_p2 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Post-Phase-2: $post_p2 (target ≤ 7820)"
if ($post_p2 -gt 7820) { Write-Output "FAIL: still over budget" } else { Write-Output "PASS" }
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "undefined|Fatal" ; cd ../..
```
Expected: `PASS`; no undefined references.

- [ ] **Step 4: Commit**

```powershell
git add report1/phd-thesis-template-2.4/Chapter*/chapter*.tex experiments/review4_cut_log.md
git commit -m "report1 review4 Phase 2: data-driven cuts to land at ≤ 7820 words"
```

---

## Task 11: Phase 2.5 — Residual AI-tone audit

**Files:**
- Create: `experiments/review4_residual_polish.md`
- Modify (if needed): any chapter file flagged by the audit

- [ ] **Step 1: Snapshot pre-Phase-2.5 wordcount**

```powershell
$pre_p25 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
```

- [ ] **Step 2: Dispatch residual-audit sub-agent**

Agent prompt verbatim:

```
You are auditing the post-Phase-2 Report 1 manuscript for AI-tone residue that grep cannot catch. Read every \section and \paragraph block across all chapter files plus the Abstract.

INPUTS:
- All files under report1/phd-thesis-template-2.4/Chapter1/ through Chapter7/ and Abstract/abstract.tex.

PROCEDURE:

For each section, flag any of the following (manual judgment — grep cannot catch these):
- RHYTHM FLATNESS: a paragraph where every sentence lands in the 15-22 word band with no variation.
- SUBJECT DRIFT: a sentence whose subject is "this", "it", "the comparison", "the analysis" without a clear antecedent.
- CITATION FILLER: a \citep{} that adds no information beyond a name the reader has already seen three times in nearby text.
- HEDGE STACKING: two hedges in one sentence ("may also potentially", "could reasonably be expected to").
- TONAL WHIPLASH: a formal-academic sentence followed immediately by a chatty plain-register sentence without a bridge.
- PREDICTABLE NEXT-WORD PATTERNS: sentences where every word is the most likely next word given the prior. Inject a plain-register word from the acceptable list (drop, gap, match, hits, sit at, notice) or restructure.

For each flag, REWRITE in place. Track changes in experiments/review4_residual_polish.md with one line per change:
  - file:lines | old → new (truncate each side to 80 chars if needed)

ACCEPTANCE:
- at least one flag found and addressed per chapter (Ch1-Ch7), OR an explicit "PASSES CLEAN" line in the polish log for that chapter
- texcount delta in [-20, +20] from pre-Phase-2.5 (this is polish, not addition)
- pdflatex builds
```

- [ ] **Step 3: Verify wordcount holds + commit**

```powershell
$post_p25 = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "Phase 2.5 delta: $($post_p25 - $pre_p25) (target ±20)"
if ($post_p25 -gt 7820) { Write-Output "FAIL: wordcount drift exceeded budget" } else { Write-Output "PASS" }
cd report1/phd-thesis-template-2.4 && pdflatex -interaction=nonstopmode thesis.tex | Select-String "Fatal" ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter*/chapter*.tex report1/phd-thesis-template-2.4/Abstract/abstract.tex experiments/review4_residual_polish.md
git commit -m "report1 review4 Phase 2.5: residual AI-tone polish (manual rewrites)"
```

---

## Task 12: Phase 3 — Final audit

- [ ] **Step 1: Wordcount confirmation**

```powershell
$final = (texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex)
Write-Output "FINAL wordcount: $final"
if ($final -le 7820) { Write-Output "PASS (≤ 7820 safety target)" }
elseif ($final -le 7850) { Write-Output "BORDERLINE (between 7820 and 7850 cap)" }
else { Write-Output "FAIL: over 7850 cap"; exit 1 }
```

- [ ] **Step 2: Clean pdflatex build**

```powershell
cd report1/phd-thesis-template-2.4
pdflatex -interaction=nonstopmode thesis.tex > $null
bibtex thesis
pdflatex -interaction=nonstopmode thesis.tex > $null
pdflatex -interaction=nonstopmode thesis.tex | Select-String "Error|Fatal|undefined|Warning.*Citation|Warning.*Reference"
cd ../..
```
Expected: no `Fatal`, no `undefined` citations or references. Overfull/underfull warnings should be ≤ pre-revision baseline.

- [ ] **Step 3: Forbidden-phrase global grep**

```powershell
$pat = "in this section,|in this chapter,|it is worth noting that|it should be noted that|importantly,|notably,|crucially,|of note,|the following discussion|as we shall see|we now turn to|may potentially|could possibly|leverages|showcases|facilitates|delve into|delve deeper|seamless"
$hits = Select-String -Pattern $pat -Path report1/phd-thesis-template-2.4/Chapter*/chapter*.tex,report1/phd-thesis-template-2.4/Abstract/abstract.tex -CaseSensitive:$false
if ($hits) { Write-Output "FAIL: forbidden phrases remain"; $hits } else { Write-Output "PASS: forbidden grep clean across manuscript" }
```
Expected: `PASS`.

- [ ] **Step 4: Machine-notation grep (the `9.34e-8` pattern)**

```powershell
$enot = Select-String -Pattern "\d\.\d+e-\d" -Path report1/phd-thesis-template-2.4/Chapter*/chapter*.tex | Where-Object { $_.Line -notmatch "lstlisting|verbatim" }
if ($enot) { Write-Output "FAIL: machine-notation strings outside listings"; $enot } else { Write-Output "PASS: scientific notation everywhere" }
```
Expected: `PASS`.

- [ ] **Step 5: Concept-definition-before-use checks**

```powershell
# LoSoS must be defined before any post-definition usage in Ch6
$ch6 = Get-Content report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
$defLine = ($ch6 | Select-String "loss.of.significance score" | Select-Object -First 1).LineNumber
$useLine = ($ch6 | Select-String "LoSoS" | Where-Object { $_.LineNumber -ne $defLine } | Select-Object -First 1).LineNumber
if ($defLine -lt $useLine) { Write-Output "PASS: LoSoS defined before first use" } else { Write-Output "FAIL: LoSoS used before definition" }
```
Expected: `PASS`.

- [ ] **Step 6: Citation check — every new bib key cited at least once**

```powershell
$newkeys = @("sterbenz_1974","maddock_boost_multiprecision","collange_etal_2015","revol_theveny_2014","kulisch_2013","bailey_borwein_borwein_2015","brio_wu_1988","einfeldt_1988")
foreach ($k in $newkeys) {
  $bibhit = Select-String -Pattern "^@\w+\{$k," -Path report1/phd-thesis-template-2.4/References/references.bib
  $citehit = Select-String -Pattern "\\citep?\{[^}]*\b$k\b" -Path report1/phd-thesis-template-2.4/Chapter*/chapter*.tex
  if ($bibhit -and $citehit) { Write-Output "OK: $k" } else { Write-Output "MISSING: $k (bib=$($bibhit.Count -gt 0); cite=$($citehit.Count -gt 0))" }
}
```
Expected: every key reports `OK:`.

- [ ] **Step 7: Manual rhythm + subject spot-check (5 minutes)**

Open the rendered PDF. Pick 3 prose paragraphs at random across Ch1–Ch7:
- Each must contain at least one sentence ≤ 10 words and at least one sentence ≥ 20 words.
- None over 30 words.
- Every sentence has a nameable subject.
- New §1.1 reads as a high-level overview (Philip's R1).
- New Ch2 §"Verificarlo and Monte Carlo Arithmetic" and §"Finite-Volume Derivation Overview" appear in the ToC.
- The two `lstlisting` blocks (3a, 3b) render legibly.
- Tables 5.1, 5.3, 5.4, 5.5, 5.6, 5.7 use `$X.XX\times10^{Y}$` formatting.

If any check fails, dispatch a targeted fix sub-agent.

- [ ] **Step 8: Final commit + tag**

```powershell
git add -A
git commit -m "report1 review4 Phase 3: final audit passed (wordcount $final ≤ 7820)" --allow-empty
git tag -a review4-final -m "Report 1 Review 4 revision: addresses all review.md items + Ch2 substantive gaps + anti-AI polish"
```

---

## Self-review

**Spec coverage:**
- R1 Ch1 overview → Task 1 ✓
- R2 §2.4 polish + Verificarlo subsection → Tasks 2a + 2b ✓
- R3 RIEMANN_STRICT listing → Task 3a ✓
- R4 Boost cite → Task 3b ✓
- R5 §4.2 reflow → Tasks 4, 5 ✓
- R6 e-notation → Task 7 ✓
- R7 LoSoS definition → Task 6 ✓
- R8 code samples → Tasks 3a, 3b ✓
- U1 anti-AI tone → Task 8 + Phase 2.5 (Task 11) ✓
- U2 section-level targeting → every batch envelope names `\section{}` / `\paragraph{}` markers ✓
- U3 finite-volume derivation → Task 2c ✓
- U4 MHD depth → Task 2d ✓
- U5 floating-point depth + consistency → Task 2e ✓
- U6 missing citations → bib entries added in Tasks 2a, 2d, 2e, 3b; cite check in Task 12 Step 6 ✓
- U7 data-driven cuts → Phase 1.5 (Task 9) → Phase 2 (Task 10) ✓
- U8 residual AI audit → Phase 2.5 (Task 11) ✓

**Placeholder scan:** every batch has exact file paths, verbatim sub-agent envelopes, exact PowerShell commands with expected output, exact commit messages. No "TBD" or "add error handling" placeholders found.

**Type consistency:** the bib keys, section markers, listing labels (`lst:strict-ineq`, `lst:hrsc-real`), and table label (`tab:ch2-divB-comparison`) are used consistently across the tasks that reference them.

**One known dependency:** Batch 3a and 3b insert `lstlisting` blocks that require `\usepackage{listings}` from Batch 7. The execution order (3a → 3b → 4 → 5 → 6 → 7) means the pdflatex build at the end of 3a, 3b, 4, 5, 6 will warn about the listings package — that is expected and resolved by Batch 7. The plan flags this explicitly in the relevant tasks.
