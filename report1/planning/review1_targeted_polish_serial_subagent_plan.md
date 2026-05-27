# Review1 Targeted Polish Serial Subagent Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the high-ROI gaps identified in `review1.md` without broad
rewriting, while keeping every added claim tied to a citation, metric, figure,
table, or named evidence artifact.

**Architecture:** Treat the evidence gates as closed before writing, then
dispatch one subsection-scoped writing worker at a time. Each worker edits only
the named local section or paragraph and leaves the rest of the chapter intact.
Shock-bubble and runtime evidence enter the manuscript only at the strength
allowed by the completed gate results.

**Tech Stack:** LaTeX in `report1/phd-thesis-template-2.4`, BibTeX, TikZ,
Python experiment harness, CMake/Ninja CPU builds, WSL/GCC strict CPU evidence,
and containerized CUDA 12.5/GCC 13 runtime evidence.

---

## Scope Decisions and Closed Evidence Gates

- HLLC star-state formula: **no change required**. Current Equation
  `eq:ch3-hllc-ustark` is the standard Toro form and is readable after the
  previous line-break cleanup.
- MHD extension: **accept compactly**. Add a seven-wave fan, the wave-speed
  list, and verified references, but keep MHD as Report 2 context. Do not add
  MHD validation claims.
- Runtime: **Gate B passed for compact support only**. Use
  `experiments/report1_runtime_minimatrix/summary.md`, generated inside the
  containerized CUDA 12.5.1/GCC 13 environment, as controlled wall-clock timing
  metadata for Sod \(N=800\) and LW3 \(N=400\). It is not a tuned performance
  benchmark and must not be mixed with historical `timing.total_s` metadata.
- Shock-bubble: **Gate C did not pass promotion**. Use
  `experiments/report1_shock_bubble_reference_upgrade/summary.md` only as
  support/appendix evidence: 400x100 and 800x200 fp64 CPU HLLC runs completed,
  but the 1600x400 self-convergence row and shock-bubble CPU/GPU rows are not
  available. Do not move shock-bubble into the five-case main validation
  matrix.
- Verified citations: **accept selectively**. Add only references that support
  a sentence in the current report: NVIDIA CUDA FP behavior, MHD divergence and
  HLLD context, and reproducible/reduction behavior if explicitly discussed.
- Toro3/Toro5 toolchain split: **Gate A passed for method-sanity support**.
  Use `experiments/report1_toolchain_sanity_toro35/summary.md` for one scoped
  sentence: the additional WSL/GCC strict CPU rerun retained the same
  fp64-vs-fp32 ranking and matched the report values to printed precision. Do
  not generalise this into a cross-toolchain or CPU/GPU bit-identity claim.

## Evidence Logic Locks

- Complete evidence that may be used:
  - Gate A: Toro3/Toro5 additional WSL/GCC strict CPU sanity check.
  - Gate B: containerized CUDA runtime mini-matrix for compact computational
    cost context.
  - Gate C: shock-bubble 400x100 versus 800x200 fp64 CPU support check only.
- Incomplete evidence that must not be used:
  - No shock-bubble 1600x400 self-convergence rate.
  - No shock-bubble CPU/GPU hardware comparison.
  - No general runtime benchmark, scaling claim, or multi-device performance
    conclusion.
  - No MHD validation or MHD solver result.
  - No claim that saved-state CPU/GPU identity proves identity of primitive
    variables, wave-speed estimates, or intermediate stages.

## Current Baseline

- User-reported Overleaf count: 7144 counted words.
- Local `texcount -inc -sum -q thesis.tex`: 7166 text words plus 184 headers.
- Local forbidden-token scan over manuscript-facing directories: zero hits.
- Native Windows CUDA/MSVC was not used for runtime evidence; the accepted
  runtime packet is the Docker CUDA 12.5/GCC 13 mini-matrix.

## Required Reading for Main Agent and Workers

```text
docs/INDEX.md
docs/HARNESS.md
report1/INDEX.md
report1/planning/reportagents.md
report1/planning/manuscript_outline.md
experiments/report1_evidence_map.md
report1/references/reference.md
report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf
report1/skills/scientific-writing-duke/SKILL.md
report1/skills/academic-english-style/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
```

Tell every worker:

```text
Edit only your assigned file and local section. Do not rewrite chapters. Do not
modify solver numerics, cfg defaults, raw existing experiment artifacts, or
anything outside your scope. Every added precision/hardware claim must point to
a citation, metric, figure, table, or named evidence artifact. Keep manuscript
labels such as week7, week8, D1, D2, HLLC-fill, config12, and USE_GPU out of
prose, captions, headings, and conclusions.
```

## Preflight Checks

Run from repo root before any worker:

```powershell
texcount -inc -sum -q report1/phd-thesis-template-2.4/thesis.tex
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|well resolved in binary64|vertical interface" report1/phd-thesis-template-2.4/Chapter* report1/phd-thesis-template-2.4/Abstract
Push-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
Pop-Location
```

Expected:

- Count remains below the 7500 hard cap.
- Forbidden-token scan has zero manuscript hits.
- `pdflatex` exits 0 from `report1/phd-thesis-template-2.4`.

---

## Evidence Gate A: Toro3/Toro5 Toolchain Sanity Check

**Purpose:** Test the review concern that Toro3/Toro5 were produced under a
different toolchain. This is a sanity check for qualitative consistency, not
evidence of cross-toolchain reproducibility.

**Status:** Completed. Use only
`experiments/report1_toolchain_sanity_toro35/summary.md`.

**Files:**

- Create: `experiments/report1_toolchain_sanity_toro35/matrix.json`
- Create: `experiments/report1_toolchain_sanity_toro35/summary.md`
- Create: `experiments/report1_toolchain_sanity_toro35/metrics.csv`
- Read: `tests/cases/toro_1d/toro3.cfg`
- Read: `tests/cases/toro_1d/toro5.cfg`
- Read: `experiments/week7/report1_validation_1d_device/`

- [x] **Step A1: Build WSL strict CPU double and float**

```powershell
wsl bash -lc "cd /mnt/c/Users/tangy/Desktop/floatpoint && cmake -S . -B build-wsl-report1-double-strict -G Ninja -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON && cmake --build build-wsl-report1-double-strict"
wsl bash -lc "cd /mnt/c/Users/tangy/Desktop/floatpoint && cmake -S . -B build-wsl-report1-float-strict -G Ninja -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=float -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON && cmake --build build-wsl-report1-float-strict"
```

Expected: both builds exit 0.

- [x] **Step A2: Run Toro3/Toro5 under the WSL strict CPU builds**

Create the matrix file:

```json
{
  "experiment": "report1_toolchain_sanity_toro35",
  "output_root": "experiments/report1_toolchain_sanity_toro35",
  "runs": [
    {
      "name": "toro3-wsl-double-strict",
      "binary": "build-wsl-report1-double-strict/hrsc",
      "config": "tests/cases/toro_1d/toro3.cfg",
      "precision": "double",
      "build": "wsl-gcc-strict-cpu-double",
      "output_file": "grid.bin"
    },
    {
      "name": "toro3-wsl-float-strict",
      "binary": "build-wsl-report1-float-strict/hrsc",
      "config": "tests/cases/toro_1d/toro3.cfg",
      "precision": "float",
      "build": "wsl-gcc-strict-cpu-float",
      "output_file": "grid.bin"
    },
    {
      "name": "toro5-wsl-double-strict",
      "binary": "build-wsl-report1-double-strict/hrsc",
      "config": "tests/cases/toro_1d/toro5.cfg",
      "precision": "double",
      "build": "wsl-gcc-strict-cpu-double",
      "output_file": "grid.bin"
    },
    {
      "name": "toro5-wsl-float-strict",
      "binary": "build-wsl-report1-float-strict/hrsc",
      "config": "tests/cases/toro_1d/toro5.cfg",
      "precision": "float",
      "build": "wsl-gcc-strict-cpu-float",
      "output_file": "grid.bin"
    }
  ]
}
```

Run:

```powershell
wsl bash -lc "cd /mnt/c/Users/tangy/Desktop/floatpoint && python3 scripts/run_matrix.py experiments/report1_toolchain_sanity_toro35/matrix.json"
```

Expected: `matrix_summary.json` contains four successful runs and
`timing.total_s` for each run.

- [x] **Step A3: Compare against the existing Windows/BuildTools strict CPU
      Toro3/Toro5 outputs**

Use the existing binary metric helper used for previous report packets. If no
single reusable compare script exists, write a local one-off analysis script
inside `experiments/report1_toolchain_sanity_toro35/` that reads the binary
grid headers and computes conservative-state L1, Linf, and ULPmax exactly as
the earlier audit packets do.

Expected interpretation:

- Result: all four checked saved conservative states are finite and
  bit-identical between the existing strict CPU outputs and WSL/GCC strict CPU
  reruns. The fp64-vs-fp32 L1 values reproduce the report values to printed
  precision.
- Manuscript logic: use as a CPU-only sanity check against the toolchain-split
  concern, not as a general cross-toolchain reproducibility result.

- [x] **Step A4: Write `summary.md`**

The summary must include:

```text
Purpose: CPU-only toolchain sanity check for Toro3/Toro5.
Scope: WSL/GCC strict CPU builds compared with existing report Toro3/Toro5 evidence.
Non-claim: this is not a CPU/GPU or cross-toolchain bit-identity claim.
Result: complete / finite / qualitative ranking retained, with L1/Linf/ULPmax table.
Manuscript use: one sentence in Chapter 4 or 5 only if the check passes.
```

## Evidence Gate B: Controlled Runtime Mini-Matrix

**Purpose:** Decide whether a runtime row/table can be added without turning a
controlled numerical report into a weak performance claim.

**Status:** Completed in a Docker CUDA environment. Use only
`experiments/report1_runtime_minimatrix/summary.md`.

**Files:**

- Create: `experiments/report1_runtime_minimatrix/matrix.json`
- Create: `experiments/report1_runtime_minimatrix/summary.md`
- Optional create: `experiments/report1_runtime_minimatrix/timing.csv`

- [x] **Step B1: Try strict CUDA builds**

```powershell
cmake -S . -B build-report1-cuda-double-strict -G Ninja -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_CUDA=ON -DENABLE_OPENMP=ON
cmake --build build-report1-cuda-double-strict
cmake -S . -B build-report1-cuda-float-strict -G Ninja -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=float -DSTRICT_IEEE=ON -DENABLE_CUDA=ON -DENABLE_OPENMP=ON
cmake --build build-report1-cuda-float-strict
```

Outcome:

- Native Windows CUDA/MSVC did not form the accepted runtime evidence because
  the local CUDA 12.3 / MSVC 19.44 pairing failed the compiler probe.
- The accepted evidence uses `nvidia/cuda:12.5.1-devel-ubuntu24.04` with
  GCC 13.2 and CUDA 12.5.82, strict HLLC, five repeats per row.

- [x] **Step B2: Run repeated same-toolchain timings**

Minimum cases:

```text
Sod N=800 fp64/fp32 CPU/GPU strict HLLC
LW3 N=400 fp64/fp32 CPU/GPU strict HLLC
```

Run at least five repeats per row by using separate run names. Use
`scripts/run_matrix.py` so each run captures `metadata.json` and
`timing.total_s`.

Outcome:

- Rows available: Sod \(N=800\) and LW3 \(N=400\), fp64/fp32, CPU/GPU, five
  repeats each.
- The same rows also report zero saved-state CPU/GPU L1/Linf/ULPmax over the
  repeated runs.
- Use only the median and min--max wall-clock timings as computational-cost
  context.

- [x] **Step B3: Decide manuscript use**

Acceptance gate for inclusion:

- Same machine, same source revision, same strict-HLLC build family.
- At least five repeats per row.
- CPU and GPU rows are available for the same cases and precisions.
- Timing text says "wall-clock timing metadata" rather than "performance
  conclusion" unless the setup is controlled enough to justify stronger words.

Gate decision: include at most one small table or one compact sentence. The
language must say "wall-clock timing metadata" or "computational-cost context",
not "benchmark", "speedup conclusion", or "performance portability".

## Evidence Gate C: Shock-Bubble Reference Upgrade

**Purpose:** Determine whether shock-bubble can move beyond appendix/support.

**Status:** Partially completed; promotion failed. Use only
`experiments/report1_shock_bubble_reference_upgrade/summary.md` as support.

**Files:**

- Existing support: `experiments/report1_shock_bubble_support/summary.md`
- Optional create: `experiments/report1_shock_bubble_reference_upgrade/`

- [x] **Step C1: Run CPU high-resolution reference if time permits**

Create 800x200 and optionally 1600x400 generated configs inside the new
experiment folder by copying the existing source config into run directories
through `scripts/run_matrix.py`; do not edit the source cfg.

Minimum run set:

```text
HLLC fp64 400x100, 800x200, and 1600x400 if runtime allows.
Rusanov fp64 400x100 and 800x200 if runtime allows.
```

Outcome:

- HLLC fp64 CPU 400x100 and 800x200 completed and are finite.
- Conservative-state 400x100 versus block-averaged 800x200 differences are
  available.
- The 1600x400 row did not complete inside the polishing window, so no
  self-convergence rate is available.

- [ ] **Step C2: Attempt strict GPU rows only if needed for future work**

Minimum GPU rows:

```text
HLLC fp64/fp32 400x100 strict CPU/GPU
```

Outcome for this plan: no shock-bubble GPU rows were added. Do not make a
shock-bubble hardware claim in the manuscript.

- [x] **Step C3: Decide manuscript use**

Promotion gate:

- High-resolution numerical reference or self-convergence exists.
- CPU/GPU strict-HLLC fp32/fp64 rows exist or the text explicitly avoids
  hardware claims for shock-bubble.
- A figure exists with clear morphology and no exact-solution claim.

Gate decision: retain support-only language. The only allowed strengthened
sentence is that a higher-resolution fp64 CPU run at 800x200 was used as a
supporting morphology/reference check for the 400x100 shock-bubble packet.

---

## Worker 1: References BibTeX, Verified Only

**Files:**

- Modify: `report1/phd-thesis-template-2.4/References/references.bib`

**Local scope:** Append or insert only the missing BibTeX entries. Do not
reformat existing entries.

**Task:** Add only the citation keys that will be cited by Workers 2--5. If a
later worker does not cite an added key, the main agent removes that key before
final verification.

Required entries:

```bibtex
@misc{whitehead_fitflorea_2011,
  author       = {Whitehead, Nathan and Fit-Florea, Alex},
  title        = {Precision and Performance: Floating Point and {IEEE} 754 Compliance for {NVIDIA} {GPUs}},
  howpublished = {{NVIDIA} white paper},
  year         = {2011},
  url          = {https://docs.nvidia.com/cuda/archive/11.2.1/pdf/Floating_Point_on_NVIDIA_GPU.pdf},
}

@article{toth_2000,
  author  = {T{\'o}th, G{\'a}bor},
  title   = {The $\nabla\cdot B=0$ Constraint in Shock-Capturing Magnetohydrodynamics Codes},
  journal = {Journal of Computational Physics},
  volume  = {161},
  number  = {2},
  pages   = {605--652},
  year    = {2000},
  doi     = {10.1006/jcph.2000.6519},
}

@article{miyoshi_kusano_2005,
  author  = {Miyoshi, Takahiro and Kusano, Kanya},
  title   = {A Multi-State {HLL} Approximate Riemann Solver for Ideal Magnetohydrodynamics},
  journal = {Journal of Computational Physics},
  volume  = {208},
  number  = {1},
  pages   = {315--344},
  year    = {2005},
  doi     = {10.1016/j.jcp.2005.02.017},
}

@article{powell_etal_1999,
  author  = {Powell, Kenneth G. and Roe, Philip L. and Linde, Timur J. and Gombosi, Tamas I. and De Zeeuw, Darren L.},
  title   = {A Solution-Adaptive Upwind Scheme for Ideal Magnetohydrodynamics},
  journal = {Journal of Computational Physics},
  volume  = {154},
  number  = {2},
  pages   = {284--309},
  year    = {1999},
  doi     = {10.1006/jcph.1999.6299},
}

```

Acceptance criteria:

- Every added key is cited at least once by later workers, or it is removed.
- No citation is added only to inflate bibliography length.
- Do not add `demmel_nguyen_2013` unless Worker 4 or 5 explicitly adds a
  reproducible-summation/reduction sentence that needs it.
- `bibtex thesis` reports no missing entry after later workers.

Word delta: 0.

## Worker 2: Chapter 2 Floating-Point and GPU Background

**Files:**

- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`

**Local scope:** Only
`\section{Floating-Point Arithmetic and Reproducibility}` between
`% <<SECTION_4_BEGIN>>` and `% <<SECTION_4_END>>`.

**Task:** Add high-density definitions for catastrophic cancellation, Kahan /
compensated summation, ULP, and CUDA arithmetic behavior without changing other
Chapter 2 sections.

Required content constraints:

- Define catastrophic cancellation once and connect it to subtracting nearly
  equal quantities.
- Define compensated/Kahan summation because Algorithm 1 uses it for time.
- Define ULP as "units in the last place" because tables use `ULPmax`.
- Cite `whitehead_fitflorea_2011` only for CUDA/GPU IEEE behavior, FMA, and
  precision/performance context.
- Do not add Sterbenz lemma unless it can be used in one sentence; otherwise it
  is low ROI for this report.

Word delta cap: +85.

Acceptance criteria:

- `Kahan`, `catastrophic cancellation`, and `ULP` each appear exactly once in
  Chapter 2 prose.
- CUDA arithmetic sentence has `\citep{whitehead_fitflorea_2011}`.
- The paragraph still distinguishes IEEE fp32 from Verificarlo `p32`.

## Worker 3: Chapter 3 MHD Extension, Seven-Wave Diagram

**Files:**

- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`

**Local scope:** Only `\section{Extension to Ideal MHD}` between
`% <<SECTION_6_BEGIN>>` and `% <<SECTION_6_END>>`.

**Task:** Increase information density without changing report scope.

Required additions:

- Add the seven ideal-MHD characteristic speeds in compact form:

```latex
u_n-c_f,\quad u_n-c_a,\quad u_n-c_s,\quad u_n,\quad
u_n+c_s,\quad u_n+c_a,\quad u_n+c_f .
```

- Add a small TikZ seven-wave fan figure with labels
  \(u_n\pm c_f\), \(u_n\pm c_a\), \(u_n\pm c_s\), and \(u_n\).
- Cite `toth_2000` for the divergence constraint survey, `powell_etal_1999`
  for eight-wave context if named, and `miyoshi_kusano_2005` for HLLD.
- Keep Dedner and CT as alternative divergence-control strategies.
- Preserve the statement that Report 1 evidence remains Euler-only.

Word delta cap: +70 counted words. Figure caption is allowed but should be
descriptive rather than defensive.

Acceptance criteria:

- `fig:ch3-mhd-seven-wave-fan` exists and is referenced once.
- No sentence says or implies MHD validation was run.
- The section remains below approximately 340 counted words.

## Worker 4: Chapter 4 Harness, Metrics, Verificarlo, and Runtime Boundary

**Files:**

- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

**Local scope:** Only these existing local paragraphs:

- In `\section{Algorithmic Structure of the Implementation}`: the paragraph
  around binary output, ordered sweep/CFL, and Kahan timing discussion.
- In `\section{Precision and Hardware Variants}`: the existing Verificarlo
  paragraph.
- In `\section{Test-Case Matrix and Metrics}`: the metric-definition paragraph
  and, if included, a small runtime-support table immediately after the matrix
  table. Do not alter the rest of Chapter 4.

**Task:** Address implementation-detail concerns with dense, evidence-bound
sentences.

Required additions:

- State that the CPU/GPU comparison writes binary conservative-state grids and
  metrics are computed from saved states, not from rounded text output.
- Add `ULPmax` definition if Worker 2 leaves the metric definition in Chapter 4
  instead of Chapter 2; avoid duplicate definitions.
- State Verificarlo mode and small sample limitation in design, before the
  Discussion caveat.
- Because Gate B passed, add one compact runtime table or one sentence with the
  median/min--max values from
  `experiments/report1_runtime_minimatrix/summary.md`, scoped to controlled
  wall-clock timing in a containerized CUDA 12.5/GCC 13 environment.

Word delta cap: +130 if a small runtime table is added.

Acceptance criteria:

- No mixed-toolchain historical timings are presented as performance evidence.
- `ENABLE_CUDA` is the only GPU build-switch spelling.
- Verificarlo `p32` remains virtual precision, not IEEE fp32.

## Worker 5: Chapter 5 CPU/GPU Mechanism and Toolchain Sanity

**Files:**

- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

**Local scope:** Only `\section{Matched CPU/GPU Comparison}` and one nearby
toolchain-scope sentence in the same section if needed. Do not edit the 1D, 2D,
precision, or drift-growth sections.

**Task:** Make the zero-drift claim more credible without broadening it.

Required mechanism sentence:

```text
The bit-identity result is plausible here because the comparison is restricted
to saved conservative states from matched strict builds, the update has no
floating-point summation reduction in the conserved-state write-out path, and
the global CFL selection is an ordered max/min-style decision rather than an
unordered sum.
```

Rewrite into the student's voice and keep it concise.

Gate A use:

- Because Gate A passed, add one sentence that Toro3/Toro5 were sanity-checked
  under an additional WSL/GCC strict CPU build and retained the same
  qualitative fp64-vs-fp32 ranking.
- Do not cite the bit-identical CPU-only rerun as a general cross-toolchain
  guarantee; keep the sentence scoped to this sanity packet.

Word delta cap: +75.

Acceptance criteria:

- Claim remains limited to saved conservative states, not intermediate
  primitive variables or wave-speed estimates.
- Fast CUDA counterexample evidence remains visible as a control.
- No cross-toolchain bit-identity claim is introduced.

## Worker 6: Chapter 6 Shock-Bubble and Limitation Framing

**Files:**

- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

**Local scope:** Only the shock-bubble/limitation sentences inside
`\section{Hardware and Implementation Sensitivity}` and
`\section{Limitations and Report 2 Direction}`. Do not rewrite either section.

**Task:** Integrate shock-bubble only at the strength supported by Gate C.

Because Gate C did not pass promotion:

- Keep shock-bubble as support only.
- State that it adds morphology and method-sensitivity context with an
  800x200 fp64 CPU support check, but lacks the 1600 self-convergence and
  device matrix required for main validation.

Word delta cap: +55.

Acceptance criteria:

- No exact shock-bubble solution is implied.
- No GPU shock-bubble claim appears unless Gate C GPU rows exist.
- The support/appendix role is clear.

## Worker 7: Optional Caption Cleanup and Defensive-Language Trim

**Files:**

- Modify only local captions/prose in:
  - `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
  - `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

**Local scope:** Only captions or sentences touched by Workers 4--6, plus
duplicated caveats immediately adjacent to those edits. Do not perform a broad
style pass.

**Task:** Recover word budget and improve readability.

Targets:

- Move limitations out of captions when the same limitation appears in nearby
  prose.
- Trim duplicated "bounded to..." disclaimers.
- Do not delete necessary scope limits for CPU/GPU, Verificarlo, or MHD.

Word delta target: -60 to -120.

Acceptance criteria:

- Every figure/table remains interpreted in prose.
- Limitations are still present once near the result.
- No result claim becomes broader after the trim.

---

## Main-Agent Integration Review After Each Worker

1. Inspect only the edited region plus one paragraph before/after.
2. Check word delta against the worker cap.
3. Run forbidden-token scan.
4. Run `pdflatex -draftmode -interaction=nonstopmode thesis.tex` from
   `report1/phd-thesis-template-2.4` after any LaTeX or BibTeX change.
5. Reject worker output that adds unsupported claims, unused citations, broad
   MHD claims, or mixed-toolchain runtime claims.

## Final Verification

Run from `report1/phd-thesis-template-2.4`:

```powershell
pdflatex -draftmode -interaction=nonstopmode thesis.tex
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
texcount -inc -sum -q thesis.tex
```

Run from repo root:

```powershell
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|well resolved in binary64|vertical interface|TODO|drafting comment" report1/phd-thesis-template-2.4/Chapter* report1/phd-thesis-template-2.4/Abstract
rg -n "whitehead_fitflorea_2011|toth_2000|miyoshi_kusano_2005|powell_etal_1999" report1/phd-thesis-template-2.4/Chapter* report1/phd-thesis-template-2.4/Abstract report1/phd-thesis-template-2.4/References/references.bib
```

Final acceptance:

- Overleaf counted text remains below 7500.
- Every new citation key is cited exactly where it supports a sentence.
- No MHD validation claim is introduced.
- Runtime is included only as Gate B's containerized computational-cost context.
- Shock-bubble remains support/appendix only; no main-validation promotion.
- Toro3/Toro5 toolchain concern is addressed only as Gate A's scoped CPU sanity
  check.
