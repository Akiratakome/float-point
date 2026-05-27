# Report 1 Review Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Absorb the highest-value review feedback into the current Report 1 LaTeX draft while keeping Overleaf counted text below 7800 and preserving the existing solver, cfg defaults, output formats, and evidence artifacts.

**Architecture:** This plan adapts `docs/superpowers/plans/2026-05-25-report1-trim.md` to the current post-trim manuscript state. It uses replacement-style edits, table/caption/footnote density, and one serial subagent per subsection-sized write scope. The controller reviews each subagent result before dispatching the next task.

**Tech Stack:** LaTeX source under `report1/phd-thesis-template-2.4/`; bibliography in `References/references.bib`; evidence map in `experiments/report1_evidence_map.md`; verification with `rg`, `texcount`, and `pdflatex`.

**Current baseline:** Local `texcount -inc -total thesis.tex` reports `Words in text: 7697`, `Words in headers: 188`, and `Words outside text: 726`. The goal is net-neutral or net-negative counted prose. Local `texcount` is a proxy; Overleaf counted text remains controlling.

**Execution policy:** Do not create commits during execution unless the user explicitly asks. The current worktree is dirty, so each subagent must report exact files changed and the controller must avoid staging unrelated changes.

---

## Standing Instructions for Every Subagent

Each subagent prompt must include these instructions:

```text
You are editing a LaTeX report manuscript. Work only in the file(s) assigned to this task.

Constraints:
- Do not change solver code, cfg defaults, experiment artifacts, or output formats.
- Do not edit unrelated sections.
- Do not change \label{}, \ref{}, or citation keys unless this task explicitly requests it.
- Do not invent new numerical claims. Every added number must come from the evidence file named in the task.
- Prefer replacement edits over insertions. If you add counted prose, remove comparable repeated prose in the same subsection.
- Prefer captions, table notes, and footnotes for method parameters where the report already interprets the result in prose.
- Keep MHD as Report 2 context only. Do not claim MHD validation.
- Do not use internal manuscript-facing labels: week*, D1, D2, HLLC-fill, config12, USE_GPU, Toro123, or Toro 123.
- Do not use AI-flavoured filler or broad claims. Keep claims scoped to tested cases.

Return:
- Files changed.
- Before/after excerpt for each edit.
- Approximate counted-word delta.
- Which review point the edit addresses.
- Any citation keys added or removed.
```

For tasks that touch citations, add:

```text
Before adding a citation, verify the BibTeX key exists in report1/phd-thesis-template-2.4/References/references.bib. If the key is missing, report it and do not invent a new entry unless this task explicitly assigns bibliography editing.
```

---

## Controller Preflight

**Files:** none.

- [ ] **Step 1: Record current word count.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -total thesis.tex
```

Expected current baseline: `Words in text: 7697`.

- [ ] **Step 2: Record forbidden-label baseline.**

Run from repo root:

```powershell
rg -n "Toro 123|Toro123|config12|week[0-9]|D1|D2|USE_GPU|HLLC-fill" report1/phd-thesis-template-2.4 -g "*.tex"
```

Expected: no `config12`, `week*`, `D1`, `D2`, `USE_GPU`, or `HLLC-fill` in manuscript-facing `.tex`; known remaining issues may include `Toro2`/`Toro4` terminology and must be fixed in Task 1.

- [ ] **Step 3: Record current git state without changing it.**

Run:

```powershell
git status --short
```

Expected: dirty worktree may contain unrelated user or prior-agent changes. Do not revert or stage them.

---

## Task 1: Chapter 5 Naming Consistency

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Read evidence if needed: `experiments/week8/toro2_lt_branch_retry/summary.md`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter5 only.

Edits:
1. Replace the section heading `\section{Toro2 Branch Stability}` with `\section{Toro Test 2 Branch Stability}`.
2. In that section, replace `Toro~123` with `Toro Test 2`, and write the first mention as `Toro Test 2, the symmetric near-vacuum problem`.
3. In the time-resolved drift paragraph, replace `Sod, Toro2, and Toro4 remain lower` with terminology that makes clear these are supporting one-dimensional drift-probe cases, not headline validation cases. Use `Sod and the lower-drift supporting Toro cases remain lower` unless the surrounding sentence needs a tighter rewrite.
4. Do not change figure filenames or evidence paths.

Goal: net zero or net negative counted words.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "Toro 123|Toro123|Toro2|Toro4" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: no `Toro 123`/`Toro123`; remaining `Toro2`/`Toro4` only acceptable if inside evidence-path comments, which should not exist in this file.

---

## Task 2: Chapter 3 Dimensional Splitting and CFL Boundary

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter3 §3.1 and §3.4 only.

Edits:
1. Strengthen the dimensional-splitting statement after the finite-volume update: state that the implementation uses alternating directional sweeps, not an unsplit transverse-flux scheme.
2. In §3.4, keep the current CFL formula as the split-update per-direction restriction. Add one bounded sentence: the report does not use the split form to claim a global unsplit second-order-in-time proof; the two-dimensional accuracy is checked against numerical references in Chapter 5.
3. Remove or compress one repeated stability sentence in the same area to offset the addition.

Goal: net change no more than +35 counted words.
```

- [ ] **Step 2: Controller review.**

Check for overclaim:

```powershell
rg -n "unsplit|Strang|second-order.*proof|dimensionally split|directional" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: the text distinguishes split from unsplit and does not claim a global unsplit proof.

---

## Task 3: Chapter 3 HLLC, Rusanov, and Positivity Micro-Fixes

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- Optional modify only if citation metadata is already verified: `report1/phd-thesis-template-2.4/References/references.bib`

- [ ] **Step 1: Verify available citation keys.**

Run:

```powershell
rg -n "batten|roe_1981|einfeldt|brackbill" report1/phd-thesis-template-2.4/References/references.bib report1/references/reference.md
```

Expected: `Roe` may exist only in notes; do not add a new BibTeX entry unless metadata is verified in this task.

- [ ] **Step 2: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter3 §3.3 and §3.4 only.

Edits:
1. After the HLLC star-state equation, add or replace one short explanatory sentence: the prefactor multiplies the whole vector, and the fourth entry is the specific total-energy form.
2. In the Rusanov paragraph, write `Rusanov, also called the local Lax--Friedrichs flux, ...`.
3. In the positivity paragraph, state compactly that no explicit positivity limiter or general positivity proof is claimed.
4. If a verified Batten et al. 1997 key already exists, cite it for HLLC wave-speed/positivity context. If not, leave the sentence uncited or cite existing Toro/Higham context only where appropriate.

Goal: net change no more than +30 counted words.
```

- [ ] **Step 3: Controller review.**

Check:

```powershell
rg -n "local Lax|prefactor|specific total-energy|positivity limiter|positivity proof" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: each review point is covered once, without a long literature digression.

---

## Task 4: Chapter 2 Floating-Point Background Density

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter2 §2.3 and §2.4 only.

Edits:
1. Remove the meta-comment phrase `without requiring the background chapter to catalogue individual test cases` and rewrite the sentence as a normal benchmark-literature sentence.
2. Add one compact definition of the Sterbenz exact-subtraction condition before Chapter3 uses it.
3. Add one compact subnormal/gradual-underflow/flush-to-zero sentence that prepares the later `--ftz=false` strict CUDA flag.
4. Keep Verificarlo p32 versus IEEE fp32 distinction intact.

Goal: net change no more than +20 counted words by cutting the meta-comment and compressing existing wording.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "without requiring the background|Sterbenz|subnormal|underflow|flush-to-zero|p32.*IEEE|IEEE.*p32" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```

Expected: meta-comment gone; Sterbenz and subnormal/FTZ appear once; p32 remains distinct from IEEE fp32.

---

## Task 5: Chapter 4 Implementation Route and Hardware Framing

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
- Evidence context: `experiments/report1_runtime_minimatrix/summary.md`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter4 §4.1, §4.2, and the runtime table caption only.

Edits:
1. Strengthen the stand-alone route justification in §4.1 with two precise ideas: uniform-grid validation avoids AMR reference-attribution complexity, and source-level FP controls/CPU-CUDA branch parity are easier to expose in the stand-alone code.
2. Compress the long CUDA paragraph in §4.2 by removing repeated throughput explanation while preserving: kernel separation, HLLC warp-divergence site, cell-major comparability choice, shared-memory CFL reduction only, and ordered comparisons for `Delta t`.
3. In the runtime table lead-in or caption, include the hardware/toolchain context already supported by evidence: NVIDIA RTX 4060 Laptop GPU, CUDA 12.5/GCC 13 containerized environment.
4. Revise the fp64 GPU≈CPU explanation to be cautious: consumer-GPU fp64 throughput plus current memory/layout choices. Do not write that fp64 bandwidth is proven saturated.

Goal: net change no more than +30 counted words; ideally net negative by compressing the CUDA paragraph.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "AMReX|stand-alone|RTX 4060|CUDA 12.5|GCC 13|saturating|consumer|warp-divergence|cell-major" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: stronger justification, no overconfident saturation claim.

---

## Task 6: Chapter 4 Metrics, MCA, SSIM, and Scaled-ULP Terminology

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter4 §4.3, §4.4, §4.6 only.

Edits:
1. State that MCA diagnostics use two or three samples per virtual precision where quantiles are reported, so they are spatial diagnostics rather than confidence intervals.
2. Define SSIM at first use with implementation parameters: `skimage.metrics.structural_similarity`, `gaussian_weights=True`, `sigma=1.5`, and `data_range=max(reference)-min(reference)`.
3. Clarify that the reported ULP quantity is a scaled ULP ratio derived from `Linf / (eps * maxabs)` rather than an integer adjacent-float distance. Use wording that can support decimal values such as 29.9.
4. Keep the exact variable names in tables unless a cross-chapter terminology task changes them consistently.

Goal: net change no more than +40 counted words, using table/caption notes where possible.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "two or three samples|confidence|SSIM|structural_similarity|gaussian_weights|sigma=1.5|scaled ULP|adjacent-float|eps" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Expected: MCA, SSIM, and scaled-ULP definitions are explicit enough to answer the review.

---

## Task 7: Cross-Chapter Scaled-ULP Terminology Sweep

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Abstract/abstract.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: only sentences/table captions that define or interpret `\mathrm{ULP}_{\max}`.

Edits:
1. Do not change numerical values.
2. Do not rename the symbol everywhere if that would be invasive. Instead, ensure the first definition says it is a scaled ULP-ratio diagnostic, not an integer float-distance count.
3. In captions or prose where decimal values appear, use `scaled ULP ratio` or `ULP-scaled ratio` rather than implying integer ULP distance.
4. Keep the zero CPU/GPU result readable: `\mathrm{ULP}_{\max}=0` remains valid because zero scaled ratio means byte-identical saved states in the paired comparisons.

Goal: net change no more than +20 counted words.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "ULP|ULP-scaled|scaled ULP|adjacent" report1/phd-thesis-template-2.4/Abstract report1/phd-thesis-template-2.4/Chapter4 report1/phd-thesis-template-2.4/Chapter5 report1/phd-thesis-template-2.4/Chapter6 report1/phd-thesis-template-2.4/Chapter7
```

Expected: decimal ULP values are not presented as integer adjacent-representable counts.

---

## Task 8: Chapter 5 Evidence Density

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Evidence: `experiments/report1_reference_self_convergence/summary.md`
- Evidence: `experiments/report1_fp32_fp64_time_drift/summary.md`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter5 §5.3 and §5.4 only.

Edits:
1. Add one compact LW3 self-convergence statement using these exact evidence values: rho L1 decreases from `3.304289e-03` for 400-vs-800 to `2.392109e-03` for 800-vs-1600, with observed order about `0.47`. State that this supports a numerical-reference hierarchy, not an exact-solution proof.
2. In the fp32/fp64 time-drift sentence, keep it as saved-state precision drift. If adding numbers, use the existing final values already in the draft or these evidence values: Sod rho final L1 `8.247902e-08`, Toro5 rho final L1 `2.555750e-06`, Toro5 pressure final L1 `1.982099e-04`.
3. Remove one repeated caveat in the same subsection to offset the addition.

Goal: net change no more than +50 counted words.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "3.304|2.392|0.47|saved-state precision drift|Toro5 pressure" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: evidence appears with correct scope and no exact-reference overclaim.

---

## Task 9: Chapter 6 and Chapter 7 Limitation Tightening

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex`
- Evidence: `experiments/report1_toolchain_sanity_toro35/summary.md`
- Evidence: `experiments/report1_shock_bubble_support/summary.md`
- Evidence: `experiments/report1_limiter_variation_optin/summary.md`

- [ ] **Step 1: Dispatch serial subagent.**

Subagent task:

```text
Apply the standing instructions.

Scope: Chapter6 §6.3/§6.4 and Chapter7 conclusion paragraph only.

Edits:
1. Remove the LaTeX TODO comment about panel merge; it must not remain in final manuscript source.
2. Keep shock-bubble and limiter evidence as support/limitation, not part of the five-case validation matrix.
3. Add one compact toolchain sanity sentence only if it can replace an existing toolchain caveat: WSL/GCC strict CPU reruns for Toro3/Toro5 matched existing strict CPU saved outputs with zero drift, but this is CPU-only sanity evidence, not general cross-toolchain equivalence.
4. Ensure Chapter7 does not introduce new evidence beyond Chapter6 and does not claim MHD validation.

Goal: net change no more than +20 counted words; prefer net negative by replacing duplicated caveats.
```

- [ ] **Step 2: Controller review.**

Check:

```powershell
rg -n "TODO|shock-bubble|limiter|toolchain|cross-toolchain|MHD validation|five-case" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Expected: no TODO; support evidence remains bounded.

---

## Task 10: Bibliography Micro-Pass

**Files:**
- Modify only if needed: `report1/phd-thesis-template-2.4/References/references.bib`
- Modify only if needed: chapter citation sites created by Tasks 3-9

- [ ] **Step 1: Controller verifies used citation keys.**

Run:

```powershell
rg -o "\\cite[p|t]?\\{[^}]+\\}" report1/phd-thesis-template-2.4 -g "*.tex"
rg -n "@(article|book|inproceedings|misc|manual|techreport)\\{" report1/phd-thesis-template-2.4/References/references.bib
```

- [ ] **Step 2: Dispatch subagent only if a needed key is missing or unused citations became problematic.**

Subagent task:

```text
Apply the standing instructions.

Scope: bibliography consistency only.

Rules:
1. Do not add broad literature-review citations just to satisfy the review.
2. Add a BibTeX entry only if a manuscript sentence directly cites it and metadata is available from a reliable note or existing verified source.
3. Preferred additions only if used: Roe 1981 for approximate Riemann solver background; Batten et al. 1997 for HLLC wave-speed/positivity context; Brackbill and Barnes 1980 for MHD divergence-force motivation.
4. If metadata is not verified, report the missing citation and leave the prose using existing citations or no citation.
```

Expected: compact bibliography with no invented keys.

---

## Final Verification Gate

- [ ] **Step 1: Forbidden label and overclaim scan.**

Run:

```powershell
rg -n "Toro 123|Toro123|config12|week[0-9]|D1|D2|HLLC-fill|USE_GPU" report1/phd-thesis-template-2.4 -g "*.tex"
rg -n "generally adequate|hardware has no effect|MHD validation has been completed|p32.*IEEE fp32|IEEE fp32.*p32" report1/phd-thesis-template-2.4 -g "*.tex"
```

Expected: no hits.

- [ ] **Step 2: Word count.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -total thesis.tex
```

Expected: `Words in text` remains below 7800 and preferably does not exceed the starting 7697.

- [ ] **Step 3: Draft compile.**

Run:

```powershell
cd report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Expected: no fatal errors, no new undefined references or citations.

- [ ] **Step 4: Source hygiene.**

Run:

```powershell
git diff -- report1/phd-thesis-template-2.4
git status --short
```

Expected: only manuscript/bibliography edits from this plan are present in the report workspace; unrelated dirty files remain unstaged.

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|---|---|
| Use current trim-plan constraints, not old 8564-word baseline | Controller Preflight |
| One serial subagent per subsection-sized scope | Tasks 1-9 |
| Keep Overleaf counted text below 7800 | Final Verification Gate |
| Fix Toro naming and internal labels | Task 1 |
| Address dimensional splitting review point | Task 2 |
| Address HLLC/Rusanov/positivity review points | Task 3 |
| Address floating-point background gaps | Task 4 |
| Address AMReX/hardware/runtime review points | Task 5 |
| Address MCA/SSIM/ULP review points | Tasks 6-7 |
| Add 2D self-convergence/time-drift evidence density | Task 8 |
| Bound shock-bubble/limiter/toolchain support evidence | Task 9 |
| Keep bibliography compact and verified | Task 10 |

### Placeholder Scan

The plan contains no unresolved placeholders. Conditional tasks specify exact conditions and fallback behavior.

### Risk Controls

- The plan avoids commits because the current worktree is dirty.
- Tasks touching the same file are serial.
- Chapter 4 is split into separate implementation-route and metrics/terminology tasks.
- New citations are optional unless metadata is verified.
- Every added number is tied to a named evidence file.
