# Report 1 MHD, Citation, and Hardware Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use the remaining counted-word margin to strengthen the Report 1 MHD background/method framing, dimensional-splitting caveat, citation base, and local/CSC hardware provenance without changing unrelated sections or reducing the current manuscript word count.

**Architecture:** This is a tightly scoped manuscript polish. It modifies only `Chapter2`, `Chapter3`, `Chapter4`, and `References/references.bib`; it does not touch solver code, cfg defaults, output formats, raw experiment artifacts, figures, or unrelated report sections. The target counted text is `>= 7667` and `<= 7800` by local `texcount -inc -total thesis.tex`; Overleaf word count remains controlling.

**Tech Stack:** LaTeX source under `report1/phd-thesis-template-2.4/`; bibliography in `References/references.bib`; evidence context from `experiments/week7/reference_1600/summary.md`, `experiments/week6/csc_smoke/summary.md`, and local Windows hardware probe; verification with `rg`, `texcount`, `bibtex`, and `pdflatex -draftmode`.

---

## Current Baseline

Recorded before this plan was written:

```text
texcount -inc -total thesis.tex
Words in text: 7667
Words in headers: 190
Words outside text (captions, etc.): 726
```

Final accepted local range:

```text
7667 <= Words in text <= 7800
```

Preferred landing range:

```text
7710 <= Words in text <= 7770
```

The current worktree is dirty. Do not revert, stage, or commit unrelated changes.

---

## Verified Source Decisions

Use these citation decisions during implementation:

| Candidate | Decision | Reason |
|---|---|---|
| Brackbill and Barnes 1980 | Add and cite | Core motivation for nonzero `\nabla\cdot B` causing unphysical magnetic-monopole forces. DOI verified as `10.1016/0021-9991(80)90079-0`. |
| Batten et al. 1997 | Add and cite | High-value HLLC wavespeed reference. DOI verified as `10.1137/S1064827593260140`. |
| Kahan 1965 | Add and cite | Algorithm 1 uses compensated summation. Use for original Kahan citation; keep Higham for modern FP reference. |
| Roe 1981 | Add and cite only at existing `Roe-type solvers` mention | Foundational approximate Riemann solver reference. DOI verified as `10.1016/0021-9991(81)90128-5`. |
| Einfeldt 1988 | Do not add in this pass | Real and relevant to HLLE/positivity, but current text does not need another HLL-family branch under the 100-word budget. |
| Colella and Woodward 1984 | Do not add in this pass | Real PPM reference, but Report 1 implements MUSCL-Hancock, not PPM. |
| Klöwer 2021/2022 climate precision | Do not add in this pass | The proposed "2022 Nature Computational Science reduced precision climate models" wording is not accurate enough; not needed for the MHD-focused gap. |
| Demmel and Nguyen 2013 | Already present | Keep current reproducible-reduction citation. |

Important wording constraint:

```text
Do not write that GLM-Dedner is simply "an evolution of Powell".
Write that Powell/eight-wave and Dedner/GLM are related cell-centred divergence-control approaches, but not identical.
```

---

## Standing Instructions for Every Subagent

Every subagent prompt must include:

```text
You are editing a LaTeX Report 1 manuscript. Work only in the file(s) and subsection(s) assigned to this task.

Hard constraints:
- Do not change solver code, cfg defaults, experiment artifacts, output formats, or figure files.
- Do not edit unrelated report sections.
- Do not change labels, refs, or numerical values unless the task explicitly requests it.
- Do not delete existing evidence or caveats unless the replacement preserves the same scope and is net non-negative in counted words.
- Do not claim MHD validation.
- Do not claim CPU/GPU equality beyond saved outputs and matched runs.
- Do not claim the CSC 1600^2 GPU reference is CPU-equivalent.
- Keep the final manuscript at least the current 7667 counted words and below 7800.
- Prefer one focused replacement over several scattered insertions.

Return:
- Files changed.
- Subsections changed.
- Before/after excerpt for each edit.
- Estimated counted-word delta.
- Citation keys added or used.
- Any risk that the edit may have touched unrelated content.
```

For citation tasks, also include:

```text
Before adding or using a citation key, verify it exists in `report1/phd-thesis-template-2.4/References/references.bib` after the bibliography task has run. Do not invent citation keys in prose.
```

---

## Controller Preflight

**Files:** none.

- [ ] **Step 1: Confirm current word count.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -total thesis.tex
```

Expected before edits:

```text
Words in text: 7667
```

- [ ] **Step 2: Confirm dirty worktree and do not clean it.**

Run:

```powershell
git status --short
```

Expected: dirty worktree may contain unrelated prior changes. Do not revert or stage unrelated files.

- [ ] **Step 3: Confirm current missing citation keys.**

Run:

```powershell
rg -n "brackbill|batten|kahan_1965|roe_1981|einfeldt|colella|klower|kloewer" report1/phd-thesis-template-2.4/References/references.bib
```

Expected before Task 1: no keys for `brackbill_barnes_1980`, `batten_etal_1997`, `kahan_1965`, or `roe_1981`.

---

## Task 1: Bibliography Micro-Packet

**Files:**
- Modify: `report1/phd-thesis-template-2.4/References/references.bib`

**Scope:** Add only the four approved BibTeX entries. Do not reorder the whole file.

- [ ] **Step 1: Dispatch bibliography subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: bibliography only.

Add these entries near related numerical-method/MHD/FP entries. Preserve existing entries unchanged.

@article{brackbill_barnes_1980,
  author  = {Brackbill, J. U. and Barnes, D. C.},
  title   = {The Effect of Nonzero {$\nabla\cdot B$} on the Numerical Solution of the Magnetohydrodynamic Equations},
  journal = {Journal of Computational Physics},
  volume  = {35},
  number  = {3},
  pages   = {426--430},
  year    = {1980},
  doi     = {10.1016/0021-9991(80)90079-0}
}

@article{batten_etal_1997,
  author  = {Batten, P. and Clarke, N. and Lambert, C. and Causon, D. M.},
  title   = {On the Choice of Wavespeeds for the {HLLC} Riemann Solver},
  journal = {SIAM Journal on Scientific Computing},
  volume  = {18},
  number  = {6},
  pages   = {1553--1570},
  year    = {1997},
  doi     = {10.1137/S1064827593260140}
}

@article{kahan_1965,
  author  = {Kahan, W.},
  title   = {Pracniques: Further Remarks on Reducing Truncation Errors},
  journal = {Communications of the ACM},
  volume  = {8},
  number  = {1},
  pages   = {40},
  year    = {1965}
}

@article{roe_1981,
  author  = {Roe, P. L.},
  title   = {Approximate Riemann Solvers, Parameter Vectors, and Difference Schemes},
  journal = {Journal of Computational Physics},
  volume  = {43},
  number  = {2},
  pages   = {357--372},
  year    = {1981},
  doi     = {10.1016/0021-9991(81)90128-5}
}

Do not add Einfeldt, Colella--Woodward, or Klower/Paxton in this pass.
Expected counted-word delta: 0 because bibliography is excluded.
```

- [ ] **Step 2: Controller review.**

Run:

```powershell
rg -n "brackbill_barnes_1980|batten_etal_1997|kahan_1965|roe_1981|einfeldt|colella|klower|kloewer" report1/phd-thesis-template-2.4/References/references.bib
```

Expected: four approved keys exist; no new Einfeldt/Colella/Klower keys.

---

## Task 2: Chapter 2 §2.2 MHD Divergence-Control Background

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`

**Scope:** Only `\section{Ideal-MHD Project Context}`. Do not edit §2.1, §2.3, or §2.4.

- [ ] **Step 1: Dispatch Chapter 2 subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter2 only, section `Ideal-MHD Project Context`.

Replace only the paragraph beginning:
"The constraint \(\nabla\cdot\mathbf{B}=0\) states that the magnetic field is solenoidal."
through the current final sentence:
"Eight-wave formulations ... Report~2 MHD extension."

Use this replacement text, adjusting line breaks only:

The constraint \(\nabla\cdot\mathbf{B}=0\) states that the magnetic field is solenoidal. Brackbill and Barnes showed that nonzero numerical divergence introduces magnetic-monopole forces into the momentum balance, so divergence control is not only a cosmetic field-cleaning issue~\citep{brackbill_barnes_1980}. Report~1 does not implement or validate MHD; for Report~2, the main choices are constrained transport, which preserves a staggered discrete divergence constraint~\citep{evans_hawley_1988}, Dedner/GLM cleaning, which transports and damps divergence error through an added scalar field~\citep{dedner_2002}, and Powell eight-wave source terms, which advect divergence error with the flow but sacrifice strict conservation across shocks~\citep{powell_1999,toth_2000}. These cell-centred cleaning approaches are related, but Powell and Dedner are not identical formulations. The corresponding Riemann-solver candidate is HLLD~\citep{miyoshi_kusano_2005}; Bard and Dorelli provide a GPU MUSCL--Hancock ideal-MHD precedent~\citep{bard_dorelli_2014}.

Constraints:
- Do not add MHD validation language.
- Do not write that GLM-Dedner is an evolution of Powell.
- Keep the paragraph under 160 words.
- Expected counted-word delta: +45 to +75.
```

- [ ] **Step 2: Controller review.**

Run:

```powershell
rg -n "Brackbill|Powell and Dedner|not identical|HLLD|MHD validation|implement or validate MHD" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```

Expected: Brackbill motivation appears once; "not identical" appears once; no MHD validation claim.

---

## Task 3: Chapter 3 Dimensional-Splitting Caveat

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

**Scope:** Only §3.1 finite-volume update paragraph and §3.4 CFL/stability paragraph.

- [ ] **Step 1: Dispatch Chapter 3 splitting subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter3 §3.1 and §3.4 only.

Edit 1, §3.1:
Keep the existing statement that the implementation uses alternating directional sweeps rather than an unsplit transverse-flux scheme. Do not expand it unless needed for grammar.

Edit 2, §3.4:
Replace the current sentence:
"This report does not use the split form to claim a global unsplit second-order-in-time proof; two-dimensional accuracy is checked against numerical references in Chapter~5."

with:
"This report does not use the split form to claim a global unsplit or Strang-split second-order-in-time theorem; Chapter~5 demonstrates observed two-dimensional benchmark agreement against numerical references instead."

Constraints:
- Do not alter the CFL equations or labels.
- Do not add a new paragraph.
- Expected counted-word delta: +5 to +12.
```

- [ ] **Step 2: Controller review.**

Run:

```powershell
rg -n "unsplit|Strang|second-order-in-time theorem|observed two-dimensional benchmark agreement|numerical references" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: the caveat distinguishes observed benchmark agreement from a 2D second-order theorem.

---

## Task 4: Chapter 3 MHD Method Boundary and Riemann-Solver Citation

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

**Scope:** Only `\section{Extension to Ideal MHD}`.

- [ ] **Step 1: Dispatch Chapter 3 MHD subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter3 section `Extension to Ideal MHD` only.

Edit the paragraph after Eq.~\ref{eq:ch3-dedner-cleaning}. Preserve the Dedner equation exactly.

Required changes:
1. Add `\citep{roe_1981}` to the existing "Roe-type solvers" mention.
2. Replace the short sentence "These are Report~2 concerns." and the surrounding final framing with a more explicit Report 2 boundary.

Use wording close to:
"HLL gives a simpler but more diffusive bound \citep{harten_lax_vanleer_1983}; HLLD \citep{miyoshi_kusano_2005} and Roe-type solvers \citep{roe_1981} aim to retain more MHD wave structure, while GLM-Dedner cleaning and constrained transport treat divergence error differently. Report~1 does not derive an MHD finite-volume update, discrete GLM source treatment, HLLD star states, or a divergence diagnostic; those are Report~2 implementation and validation tasks."

Constraints:
- Do not remove the statement that Report 1 evidence remains Euler-only.
- Do not claim MHD validation.
- Do not add equations for HLLD star states or GLM source discretisation.
- Expected counted-word delta: +20 to +35.
```

- [ ] **Step 2: Controller review.**

Run:

```powershell
rg -n "roe_1981|finite-volume update|GLM source|HLLD star|divergence diagnostic|Euler-only|MHD validation" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: explicit non-derivation boundary appears once; Euler-only remains.

---

## Task 5: Chapter 3 HLLC Citation and Algorithm 1 Kahan Citation

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

**Scope:** Chapter 3 HLLC subsection; Chapter 4 Algorithm 1 comment only.

- [ ] **Step 1: Dispatch citation-use subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope:
- Chapter3: only the HLLC paragraph around the wave-speed/contact-restoration discussion.
- Chapter4: only Algorithm~\ref{alg:step-dispatch}, the Kahan compensation comment.

Edits:
1. In Chapter3 HLLC prose, add `\citep{batten_etal_1997}` where wave-speed choice or HLLC contact restoration is discussed. Prefer replacing an existing citation group with `\citep{toro_spruce_speares_1994,batten_etal_1997,toro2009}` rather than adding a new sentence.
2. In Chapter4 Algorithm 1, change the compensated summation citation from `\citep{higham_2002}` to `\citep{kahan_1965,higham_2002}`.

Constraints:
- No new explanatory paragraph.
- No change to algorithm steps.
- Expected counted-word delta: 0 to +5.
```

- [ ] **Step 2: Controller review.**

Run:

```powershell
rg -n "batten_etal_1997|kahan_1965" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: `batten_etal_1997` appears in Chapter 3; `kahan_1965` appears in Algorithm 1.

---

## Task 6: Chapter 4 Local and CSC Hardware Provenance

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

**Evidence to read before editing:**
- `experiments/week7/reference_1600/summary.md`
- `experiments/week6/csc_smoke/summary.md`
- Local hardware probe already recorded by controller:
  - CPU: `13th Gen Intel(R) Core(TM) i9-13900H`, 14 cores / 20 logical processors.
  - GPU: `NVIDIA GeForce RTX 4060 Laptop GPU`, driver `32.0.15.6607`.

**Scope:** Only §4.4 runtime table lead-in/caption and §4.5 reference-solution strategy. Do not edit §4.1, §4.2, §4.3, or §4.6.

- [ ] **Step 1: Dispatch Chapter 4 hardware subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter4 §4.4 and §4.5 only.

Edit 1, runtime table lead-in:
Replace the current sentence beginning:
"Table~\ref{tab:ch4-runtime-minimatrix} reports wall-clock timing metadata from one NVIDIA RTX 4060 Laptop GPU..."

with:
"Table~\ref{tab:ch4-runtime-minimatrix} reports wall-clock timing metadata from the local Intel Core i9-13900H host and NVIDIA RTX 4060 Laptop GPU in a containerized CUDA 12.5/GCC 13 environment (strict HLLC, five repeats per row); the fp64 LW3 row shows GPU \(\approx\) CPU, so the rows are computational-cost context, not a portable timing result."

Edit 2, reference-solution strategy:
After the existing LW3/LW12 reference paragraph, add one bounded CSC provenance sentence:
"The LW3 \(1600^2\) reference is a CSC RTX 5090 strict-HLLC GPU reference candidate with CPU/GPU preflight support, not a CPU-equivalent proof."

Constraints:
- Do not claim CSC and local hardware are directly comparable.
- Do not claim the CSC 1600^2 row proves CPU/GPU equality.
- Do not alter numerical table values.
- Expected counted-word delta: +25 to +45.
```

- [ ] **Step 2: Controller review.**

Run:

```powershell
rg -n "i9-13900H|RTX 4060|CUDA 12.5|GCC 13|RTX 5090|CPU-equivalent proof|reference candidate" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: local CPU/GPU and CSC RTX 5090 are both present; the CSC statement is bounded.

---

## Task 7: Word-Count Balancing Gate

**Files:** only if needed, and only after Tasks 1-6.

- [ ] **Step 1: Run word count.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -total thesis.tex
```

Expected accepted range:

```text
7667 <= Words in text <= 7800
```

- [ ] **Step 2: If word count is below 7667, add a bounded sentence.**

Only if the count falls below baseline, dispatch a balancing subagent:

```text
Apply the standing instructions.

Scope: Chapter2 §2.2 only.

Add exactly one sentence after the MHD divergence-control paragraph:
"This is why Report~2 must validate divergence control, Riemann-solver choice, and hardware sensitivity together rather than treating MHD as a direct Euler extension."

Expected counted-word delta: +23.
Do not make this edit unless local texcount is below 7667.
```

- [ ] **Step 3: If word count is above 7800, stop.**

Do not delete content ad hoc. Report the overage and identify the smallest single sentence to compress, but wait for controller approval before editing.

---

## Final Verification Gate

- [ ] **Step 1: Citation-key scan.**

Run:

```powershell
rg -n "brackbill_barnes_1980|batten_etal_1997|kahan_1965|roe_1981" report1/phd-thesis-template-2.4 -g "*.tex" -g "*.bib"
rg -n "einfeldt|colella|klower|kloewer" report1/phd-thesis-template-2.4 -g "*.tex" -g "*.bib"
```

Expected: approved keys appear; skipped optional sources do not appear.

- [ ] **Step 2: Forbidden-claim scan.**

Run:

```powershell
rg -n "MHD validation has been completed|MHD validation|CPU-equivalent proof|hardware has no effect|generally adequate|p32.*IEEE fp32|IEEE fp32.*p32|GLM.*evolution of Powell|Dedner.*evolution of Powell" report1/phd-thesis-template-2.4 -g "*.tex" -g "!SampleContent/**" -g "!Classes/**"
```

Expected: no overclaims. The phrase "not a CPU-equivalent proof" may appear and is acceptable.

- [ ] **Step 3: Word count.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -total thesis.tex
```

Expected:

```text
7667 <= Words in text <= 7800
```

- [ ] **Step 4: Bibliography and draft compile.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Expected: no fatal LaTeX errors and no new undefined citation warnings for `brackbill_barnes_1980`, `batten_etal_1997`, `kahan_1965`, or `roe_1981`.

- [ ] **Step 5: Diff hygiene.**

Run:

```powershell
git diff -- report1/phd-thesis-template-2.4/Chapter2/chapter2.tex report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/References/references.bib
git status --short
```

Expected: only the planned report files are changed by this pass; unrelated dirty files remain untouched.

---

## Self-Review

### Spec Coverage

| User requirement | Plan task |
|---|---|
| Similar precision to existing Report 1 revision plan | Full task/checkbox format, subagent prompts, verification gates |
| Use subagents to modify relevant subsections | Tasks 1-7 dispatch subsection-scoped subagents |
| Do not delete unrelated material | Standing instructions and per-task scopes |
| Do not modify unrelated subsections | Each task names exact chapter section scope |
| Strict word count, no less than current and no more than 7800 | Baseline, Task 7, Final Verification Gate |
| Use remaining 100-ish words mainly for MHD | Tasks 2 and 4 are the main positive word deltas |
| Add MHD divergence-control depth | Task 2 and Task 4 |
| Add Brackbill & Barnes | Task 1 and Task 2 |
| Correct Powell/Dedner relationship | Task 2 wording constraint |
| Clarify no MHD FV/GLM/HLLD derivation | Task 4 |
| Clarify dimensional splitting and 2D accuracy claim | Task 3 |
| Add verified citations without hallucination | Verified Source Decisions and Task 1 |
| Add CPU/GPU local and CSC hardware settings | Task 6 |

### Placeholder Scan

No task contains `TBD`, `TODO`, or unspecified "add appropriate text" instructions. Conditional Task 7 gives exact text and exact trigger conditions.

### Risk Controls

- Bibliography additions are zero counted words.
- Counted-word additions are concentrated in Chapter 2/3/4 only.
- The plan avoids optional citation stuffing under the word budget.
- CSC hardware wording is explicitly bounded as a reference-candidate provenance note, not hardware equivalence evidence.
- No solver, cfg, experiment, or figure edits are included.

