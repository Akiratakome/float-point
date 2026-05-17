# Report 1 Manuscript Outline and Writing Plan

This document is the working manuscript plan for Report 1 of *Effect of Floating-Point Precision and Hardware on HRSC Schemes*. It follows the evidence-driven drafting order:

1. Validation and precision results
2. Implementation and experimental design
3. Numerical method
4. Background and literature
5. Introduction
6. Discussion and conclusion
7. Abstract, references, and final editing

The final report order is different from the drafting order:

1. Introduction
2. Background and governing equations
3. Numerical method
4. Implementation and experimental design
5. Validation and precision results
6. Discussion
7. Conclusion

Target counted length: keep the Overleaf Word Count result strictly below 7,500 words. Course clarification for this report: use Overleaf's counted text result as the controlling count; **tables and figure captions are not counted**, but **pseudocode/algorithm-environment bodies are counted** because Overleaf Word Count treats their text content as ordinary prose. Bibliography is excluded. Working target: ≤ 7,400 Overleaf-counted words after final edit, with a hard internal stop at 7,420 leaving an ~80-word revision margin. Because tables and captions are free, this report should carry a figure/table-heavy results chapter modelled on the Davison-Petch example (target 20-24 main figures/tables): every figure or table must still be interpreted in prose, but evidence density in the results chapter is not constrained by word budget the way prose density is.

Write in the local CUED template at `report1/phd-thesis-template-2.4/`. Use the template for front matter, chapter structure, references, and final LaTeX word-count checking; do not let the template's sample chapter content determine the intellectual structure of the report.

## Global Requirements

Use these constraints throughout.

- Report 1 must visibly cover the project brief's five 20% categories:
  - literature review and background
  - mathematical theory
  - code/implementation description as reported evidence
  - validation
  - quality of write-up
- Report 1 must also satisfy the handbook's six general criteria:
  - background science and relevant literature
  - understanding of computational techniques and limitations
  - accurate description, validation, and interpretation of computational results
  - awareness and quantification of errors and ambiguities
  - convincing evidence-based conclusions
  - clear presentation, appropriate length, figures/tables, and references
- The report must be a connected account of the student's own work.
- The title page must use the author's name, the approved project title, and the degree as required by the handbook. Do not use a Blind Grading Number or BGN as the author identifier for this project report.
- Use the CUED template for front matter; do not spend drafting effort redesigning the title page.
- Keep implementation discussion at report level: algorithm, comparison design, metrics, reference solution, and interpretation.
- Every figure or table must be named in prose, interpreted, and tied to a claim.
- Every hardware or precision claim must be scaled against a metric, reference solution, or discretisation error.
- Do not claim that the project brief's CPU/GPU validation requirement is satisfied until the selected set of at least four Euler tests has documented CPU and GPU evaluation.
- Use `report1/reference.md` as the citation map. Add a citation only when it supports a sentence.
- Internal planning labels such as `week7`, `week8`, `D1`, `D2`, "HLLC-fill", or other local experiment nicknames must not appear in manuscript prose, captions, headings, or bibliography entries. They may appear only in this plan and in private drafting notes as evidence-location hints. In the report, replace them with descriptive labels such as "the one-dimensional validation summary", "the matched CPU/GPU comparison", "the two-dimensional precision diagnostic", or "the compiler-variation experiment".
- **Naming convention for 2D Riemann cases (binding for all prose, captions, headings, axis labels, and bibliography).** Refer to the two 2D Liska-Wendroff cases as "Liska-Wendroff configuration 3" (abbreviated LW3 after first mention) and "Liska-Wendroff configuration 12" (abbreviated LW12 after first mention). Do not write "config12", "config 12", "LW12/config12", or "configuration-12 case" anywhere in the manuscript. Internal evidence paths under `experiments/.../report1_2d_config12_fill/` retain the directory name but the prose label is always "Liska-Wendroff configuration 12 / LW12".
- **Toolchain split disclosure (binding for all CPU/GPU prose, tables, and the conclusion evidence lock).** The CPU/GPU matched-binary runs use two toolchains: Toro3 and Toro5 were built with Windows BuildTools; Sod, LW3, and LW12 were built with the Linux/WSL toolchain. Each within-case CPU-vs-GPU comparison uses one binary per case (so bit-identity is preserved within a case). This split must be stated in Chapter 4 (implementation), repeated as a footnote on the Chapter 5 CPU/GPU table, and named in the Chapter 7 evidence lock boundary line. Do not bury it inside a single prompt.
- Every AI-assisted draft paragraph must satisfy `report1/skills/avoiding-ai-flavor/SKILL.md` before it is treated as usable prose. This is a mandatory gate, not only a final polish step: remove banned vocabulary, generic filler, marketing confidence, repeated triadic rhythm, and any claim that is stronger than the figure, table, proof, or citation supporting it. AI-generated text must not be submitted as original assessed work; every AI-assisted paragraph is rewritten in the student's own voice before insertion (handbook integrity rule; `report1/reportagents.md` §2.4).
- Formatting compliance is checked against the handbook and current course clarification before submission, not delegated entirely to the CUED template: 12-point font, 1.5 or double line spacing, ≥ 2 cm margins on all sides, title page with author name and supervisor name in the handbook-required positions, declaration page with the verbatim handbook wording, and an Overleaf Word Count declaration. The template defaults are verified against these requirements at the start of layout work.
- Variation-axis scope is bounded explicitly. The brief lists possible axes: resolution, fp precision (single/double; quad via Boost::Multiprecision), compiler options (e.g. `-Ofast`, `--use_fast_math`), CPU architecture/vectorisation (e.g. `-mtune`), MPI/OpenMP thread count or scheduling, Riemann-solver tolerance and `<` vs `<=` branch tests, and time evolution of differences. Report 1 covers compiler flags (O2/O3/Ofast plus fast-math), `<` vs `<=` HLLC branch, HLLC vs Rusanov as method variation, fp32 vs fp64, Verificarlo-driven virtual precision p8/p16/p24/p32/p53 for the 2D LW3 case, and finite-time drift growth on the 1D Toro cases. Quad precision, `-mtune` / vectorisation, and explicit MPI/OpenMP thread-count variation are out of scope for Report 1 and identified as Report 2 candidates.

## Core Evidence Set

Prioritise these P0 artifacts from `experiments/report1_evidence_map.md`.

| Evidence role | Artifact | Intended use |
|---|---|---|
| 1D validation matrix | `experiments/week7/report1_validation_1d/summary.md` | Main 1D fp32/fp64 validation table |
| 1D exact-reference visual | `experiments/week3/week3_validation/plots/sod_comparison.png` | Baseline exact-solution validation figure |
| 1D strong-wave visual | `experiments/week3/week3_validation/plots/toro3_comparison.png`; `experiments/week3/week3_validation/plots/toro5_comparison.png` | Supersonic/strong-wave validation figure |
| 1D float/reference adequacy | `experiments/week4/float_regression/1d/summary.md` | Compare float-double gaps with reference/discretisation error |
| 2D validation matrix | `experiments/week7/report1_validation_2d/summary.md`; `experiments/week8/report1_2d_config12_fill/precision_summary.md` | Main 2D fp32/fp64 validation tables for LW3 and LW12 |
| 2D visual | `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho_schlieren.png`; `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png`; `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho.png` | Main 2D LW3 and LW12 validation figures |
| 2D float/reference adequacy | `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md` | 2D reference comparison against high-resolution numerical references |
| CPU/GPU quantification | `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`; `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`; `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`; `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` | Required CPU-GPU quantitative comparison for Sod, Toro3, Toro5, LW3, and LW12 under `solver=hllc`, `STRICT_IEEE=ON`. In manuscript prose, call these "matched CPU/GPU HLLC strict comparisons"; do not mention directory week numbers or local fill names. |
| Regression/reproducibility | `experiments/week6/regression/summary.md` | Support implementation/testing description |
| Variation axes (Sod/stationary_contact/LW3-N200) | `experiments/week7/report1_variation/summary.md` | Compiler flags (O2/O3/Ofast plus fast-math), HLLC `<` vs `<=` wave-speed branch (`RIEMANN_STRICT_INEQUALITY` ON vs OFF, file `axis_leq_vs_strict.*`), and HLLC vs Rusanov as method variation. CPU double only. The "leq" vs "strict" suffix on the build name controls only the HLLC wave-speed branch and is unrelated to `STRICT_IEEE`. |
| Variation axes (Toro3/Toro5 extension) | `experiments/week8/report1_variation_extend/summary.md` | Same axes (`<=` vs `<`, O2 vs O3, O2 vs Ofast-fastmath) applied to Toro3 and Toro5 so the variation matrix spans the same selected cases as the validation matrix. CPU double only. HLLC `<=` vs `<` and O2 vs O3 are zero drift on Toro3 and Toro5; O2 vs Ofast-fastmath produces the largest non-stationary final-time drift in the combined matrix on these two cases (L1 ~2-5e-13, Linf ~3-7e-11). |
| Drift growth | `experiments/week7/lyapunov_1d_full/summary.md`; `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png` | Time-evolution of implementation sensitivity on the 1D Toro cases. Toro2 `<` branch did not complete in the original harness; see `experiments/week8/toro2_lt_branch_retry/` for an independent attempt and its outcome. |
| Precision adequacy | `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png` | Clear fp32 adequacy comparison |
| Region-aware precision | `experiments/week7/report1_d2_replots/region_losos_margin_rho_p32.png` | Region-aware significant-digit margin |
| Spatial noise/error | `experiments/week7/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png` | Spatial interpretation of FP noise relative to error |

## Figure and Table Plan

Main text should be selective but evidence-rich. Let LaTeX number figures and tables automatically; do not hard-code final figure/table numbers in draft prose. The sample Report 1 PDF uses 20+ figures/tables in a results-heavy report, and the current course word-count clarification means tables and captions do not consume the Overleaf counted-word budget. A strong version should therefore target around 20-24 main figures/tables, provided each one carries a distinct claim, is interpreted in prose, and does not duplicate another visual. Duplicate heatmaps or provenance plots can move to an appendix if layout becomes crowded.

| Candidate item | Type | Content | Likely chapter |
|---|---|---|---|
| Validation matrix | Table | Test case, dimension, physical feature, reference, metric, hardware, precision | Ch. 4 or Ch. 5 |
| 1D exact-reference validation | Plot | Sod plus at least one strong Toro case | Ch. 5 |
| 1D precision/error summary | Table | fp32/fp64 quantitative errors from the 1D validation summary | Ch. 5 |
| 2D LW3 validation | Plot | N=400 double schlieren | Ch. 5 |
| 2D LW12 validation | Plot/table | N=400 double density/schlieren plus fp32/fp64 and N=800-reference summary | Ch. 5 |
| CPU-GPU quantitative comparison | Table | L1/Linf/ULP or available CPU-GPU metrics | Ch. 5 |
| Finite-volume method schematic | Figure or algorithm box | Cell averages, interface fluxes, and conservative update | Ch. 3 |
| Implementation pseudocode | Algorithm box | Config -> CPU/GPU dispatch -> CFL -> sweep -> output | Ch. 4 |
| MUSCL-Hancock code path | Pseudocode or compact flow table | Reconstruction, half-step predictor, HLLC/Rusanov flux, conservative update | Ch. 4 |
| HLLC branch decision | Small equation/table | Wave-speed branch rule and `<` vs `<=` sensitivity point | Ch. 3 or Ch. 5 |
| Variation or drift summary | Plot/table | Compiler/branch/solver variation or drift-timeseries evidence | Ch. 5 or Ch. 6 |
| Precision adequacy | Plot | float-double/reference adequacy, region-aware precision, or spatial noise/error | Ch. 5 or Ch. 6 |

Keep captions concise even though they are not counted by the Overleaf word-count rule, because assessors still read them as part of presentation quality. Use figures where they carry evidence or explain method mechanics; do not add decorative plots. If the report becomes visually crowded, move duplicate heatmaps or detailed variation plots to appendix and keep the main text focused on validation, precision, hardware, and method interpretation.

Validation gate: the selected Euler set is now Sod, Toro3, Toro5, LW3, and LW12. The current evidence set has matched CPU/GPU entries for all five selected tests: Sod and LW3 fp32 in `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`, Toro3/Toro5 in `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`, LW3 fp64 in `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`, and LW12 in `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md`. Final validation claims must still be bounded to this selected set unless further device evidence is added. The path names are evidence locators only; do not mention their week labels in the manuscript.

## Skill Usage Rule

Use one or two skills per writing pass:

| Drafting task | Primary skill | Optional companion |
|---|---|---|
| Introduction | `writing-introduction` | `report1-context` |
| Background/literature | `writing-literature-review` | `academic-english-style` |
| Numerical method | `scientific-writing-duke` | `academic-english-style` |
| Implementation/experimental design | `scientific-writing-duke` | `academic-english-style` |
| Validation/results | `scientific-writing-duke` | `academic-english-style` |
| Discussion | `scientific-writing-duke` | `academic-english-style` |
| Conclusion | `writing-conclusion` | `report1-context` |
| Final editing | `editing-academic-prose` | then `avoiding-ai-flavor` |

All prompts below inherit the `avoiding-ai-flavor` gate. If a generated paragraph contains banned vocabulary, empty framing, unsupported confidence, or a sentence that could fit an unrelated dissertation, rewrite it immediately before adding it to the manuscript. Per-paragraph compliance is mandatory; the final-editing row above is a re-check, not a substitute for in-drafting compliance.

Per-paragraph constraints that prompts inherit:

- Every paragraph must name at least one specific method, test case, metric, figure, or citation; a paragraph that could be pasted into an unrelated dissertation is rewritten.
- Banned vocabulary from `avoiding-ai-flavor/SKILL.md` (delve, leverage, unlock, robust [loose], comprehensive [loose], significant [no number], landscape [non-literal], …) is checked against the table, not from memory.
- No triadic "X, Y, and Z" rhythm in three consecutive sentences; vary clause length.
- Restate contributions and abstract in at most two-item lists when possible; if a three-item list is necessary, vary the surrounding sentences so it is not part of a triadic cadence.

## Word Budget Lock

Chapter caps below are the per-chapter Overleaf-counted upper bounds; their max sum is **7,220**, leaving ~280 words of revision margin under the 7,500 hard cap. Pseudocode lines count as ordinary prose (see Global Requirements), so the §4.2 budget already absorbs the algorithm box.

| Chapter | Range | Hard upper |
|---|---|---|
| Abstract | 180-220 | 220 |
| Ch. 1 Introduction | 600-720 | 720 |
| Ch. 2 Background | 780-880 | 880 |
| Ch. 3 Numerical method | 1,080-1,220 | 1,220 |
| Ch. 4 Implementation (incl. pseudocode) | 1,000-1,130 | 1,130 |
| Ch. 5 Validation and precision results | 1,750-1,900 | 1,900 |
| Ch. 6 Discussion | 600-720 | 720 |
| Ch. 7 Conclusion | 330-430 | 430 |
| Front matter (declaration, abstract heading) | n/a | n/a |
| **Sum (max)** | | **7,220** |

Lower-bound sum is 6,320, upper-bound sum is 7,220. The extra 280-word headroom between 7,220 and 7,500 absorbs unexpected pseudocode overrun, equation labels Overleaf treats as words, and one round of supervisor-requested additions. If a section pushes against its hard upper, cut from §6.x synthesis or §2.2 MHD context before touching evidence-bearing sections (§5.x).

## Chapter 1: Introduction

Working target: 600-720 counted words (hard upper 720). Draft after Chapters 3-6 are stable.

Purpose: narrow from HRSC methods and floating-point reproducibility to this Report 1 study.

### 1.1 Context: HRSC schemes for discontinuous compressible flows

**Topic sentence:** High-resolution shock-capturing schemes are used because compressible flows can contain shocks, contacts, and rarefactions that standard smooth-solution discretisations do not handle reliably.

**Figure/table:** None.

**Citations:** Toro; van Leer or Harten-Lax-van Leer if needed.

**Scoring alignment:** Literature/background [20%]; handbook criterion 1.

**Requirements:** Establish the numerical context without giving a full textbook derivation.

**Prompt:**
```text
Using `writing-introduction` and `academic-english-style`, draft Section 1.1 for a Cambridge MPhil Report 1. Open with HRSC schemes for discontinuous compressible flows, then narrow to finite-volume Riemann-solver methods. Use Toro as the main citation. Keep the paragraph citation-driven and avoid journalistic language. End by preparing the transition to hardware and floating-point reproducibility.
```

**Skill:** `writing-introduction` + `academic-english-style`.

### 1.2 Problem: precision and hardware can affect reproducibility

**Topic sentence:** Even when two runs implement the same numerical algorithm, floating-point precision, compiler choices, and hardware execution order can change the computed solution.

**Figure/table:** None.

**Citations:** Goldberg; IEEE 754; Higham.

**Scoring alignment:** Literature/background [20%]; handbook criteria 1 and 4.

**Requirements:** Explain why this matters for CPU/GPU and fp32/fp64 studies, without overclaiming that all hardware differences are large.

**Prompt:**
```text
Using `writing-introduction` and `academic-english-style`, draft Section 1.2. Explain why floating-point precision, compiler settings, and hardware execution order can affect numerical reproducibility in finite-volume solvers. Cite Goldberg, IEEE 754, and Higham. Hedge empirical claims and connect the issue to CPU/GPU and fp32/fp64 comparisons.
```

**Skill:** `writing-introduction` + `academic-english-style`.

### 1.3 Project gap and Report 1 scope

**Topic sentence:** The project addresses this reproducibility question for HRSC schemes by measuring how Euler solutions change across precision and hardware under controlled validation tests.

**Figure/table:** None.

**Citations:** Project brief; Liska-Wendroff for 2D Euler tests; Bard and Dorelli only for wider GPU/MHD motivation.

**Scoring alignment:** Literature/background [20%]; validation [20%]; handbook criteria 1, 3, 4.

**Requirements:** State that Report 1 focuses on Euler validation while positioning MHD as the longer project direction.

**Prompt:**
```text
Using `writing-introduction` and `report1-context`, draft Section 1.3. State the gap as a controlled measurement problem: how precision and hardware affect HRSC solutions. Make clear that Report 1 focuses on Euler ideal-gas validation in 1D and 2D, while ideal MHD motivates the later project trajectory. Do not promise results that are not in the evidence map.
```

**Skill:** `writing-introduction` + `report1-context`.

### 1.4 Contributions and chapter roadmap

**Topic sentence:** Report 1 contributes validation evidence for a selected Euler HRSC test matrix, a controlled precision/hardware comparison, and an evidence base for later MHD work.

**Figure/table:** None.

**Citations:** None unless a contribution sentence depends on a benchmark source.

**Scoring alignment:** All five 20% categories; handbook criteria 3, 5, 6.

**Requirements:** Use 3 contribution bullets or one compact paragraph. Avoid novelty overclaim.

**Prompt:**
```text
Using `writing-introduction` and `academic-english-style`, write a concise contribution and roadmap section. State three contributions: validation evidence for a selected Euler HRSC test matrix; quantified fp32/fp64 and CPU/GPU comparisons; analysis of selected compiler/implementation variation axes. Then foreshadow Chapters 2-7. Use restrained language and avoid claiming novelty beyond the evidence.
```

**Skill:** `writing-introduction` + `academic-english-style`.

## Chapter 2: Background and Governing Equations

Working target: 780-880 counted words (hard upper 880).

Purpose: satisfy background/literature and set up the equations and concepts used later.

### 2.1 Compressible Euler equations

**Topic sentence:** The Euler equations provide the Report 1 validation system because they contain the shock, contact, and rarefaction structures targeted by HRSC methods while remaining simpler than ideal MHD.

**Figure/table:** Optional equation block only.

**Citations:** Toro; Sod if introducing shock-tube validation.

**Scoring alignment:** Literature/background [20%]; mathematical theory [20%]; handbook criteria 1 and 2.

**Requirements:** Present conservation form for 1D and 2D settings, define conservative variables and fluxes, state ideal-gas closure.

**Prompt:**
```text
Using `writing-literature-review` and `academic-english-style`, draft Section 2.1. Present the compressible Euler equations in conservation form for the 1D and 2D validation settings. Define conservative variables, fluxes, and the ideal-gas equation of state. Explain why Euler is the Report 1 validation system. Keep the section concise and tied to later validation.
```

**Skill:** `writing-literature-review` + `academic-english-style`.

### 2.2 Ideal MHD as wider project target

Working sub-target: ≤ 140 counted words. This is context only; the section must not expand into MHD methodology.

**Topic sentence:** Ideal MHD extends the Euler system by coupling fluid motion to magnetic fields, and this makes divergence control a central issue for the later project stages.

**Figure/table:** Optional equation block if space allows; otherwise prose.

**Citations:** Bard and Dorelli (one citation only in this section); Dedner/Evans-Hawley only if divergence cleaning is named; Brio-Wu/Orszag-Tang only if benchmarks are discussed.

**Scoring alignment:** Literature/background [20%]; mathematical theory [20%].

**Requirements:** Keep ≤ 140 words and ≤ 1 citation. Report 1 should not read as MHD validation. Do not introduce method names that the report does not use.

**Prompt:**
```text
Using `writing-literature-review` and `academic-english-style`, draft Section 2.2. Explain ideal MHD as the wider project target and mention the divergence-free magnetic-field constraint. Keep MHD as context for Report 2, not as the main evidence of Report 1. Cite Bard and Dorelli for GPU/MHD motivation and cite divergence-control references only if the text specifically names a method.
```

**Skill:** `writing-literature-review` + `academic-english-style`.

### 2.3 HRSC finite-volume methods

**Topic sentence:** Finite-volume HRSC methods are appropriate because they update cell averages through numerical fluxes and can preserve conservation across discontinuities.

**Figure/table:** Optional schematic/pseudocode later in Ch. 3; none needed here.

**Citations:** Toro; Harten-Lax-van Leer; van Leer.

**Scoring alignment:** Literature/background [20%]; mathematical theory [20%]; handbook criterion 2.

**Requirements:** Do not rederive the full method here; introduce why finite-volume/Riemann-solver methods are the relevant family.

**Prompt:**
```text
Using `writing-literature-review` and `academic-english-style`, draft Section 2.3 as a thematic literature paragraph, not a chronology. Explain why finite-volume HRSC methods suit discontinuous compressible flows. Cite Toro as the main source, with Harten-Lax-van Leer and van Leer only where their specific contribution matters. Close by motivating the more detailed method chapter.
```

**Skill:** `writing-literature-review` + `academic-english-style`.

### 2.4 Floating-point arithmetic and reproducibility

Working target: 300-360 counted words. This subsection carries the brief's Literature/Background [20%] bullet "a brief discussion of floating-point arithmetic, and what effect different hardware, compiler options, and parallel-thread ordering may have on the result of simple expressions and algorithms." Treat it as a small standalone block, not a stub.

**Topic sentence:** Floating-point arithmetic introduces small local rounding differences that can become measurable in nonlinear time-dependent solvers.

**Figure/table:** None required; one short equation or numerical demonstration of non-associativity is allowed if it stays within the word budget.

**Citations:** Goldberg; IEEE 754-2019; Higham; Higham and Mary only if mixed/probabilistic precision is discussed.

**Scoring alignment:** Literature/background [20%]; validation [20%]; handbook criteria 1 and 4.

**Requirements:** Cover, at conceptual level: binary32 versus binary64 storage and unit roundoff; round-to-nearest-even semantics; non-associativity of `(a+b)+c` versus `a+(b+c)` as the underlying mechanism the brief asks about for "simple expressions and algorithms"; FMA and `-ffp-contract` behaviour; compiler options such as `-Ofast` and `--use_fast_math` and how they relax IEEE semantics; reduction order across parallel threads or GPU blocks. Each mechanism must be named; do not collapse them into a single paragraph of generalities. Hedge: differences exist mechanically, but whether they grow in a given solver is an empirical question the rest of the report measures.

**Prompt:**
```text
Using `writing-literature-review` and `academic-english-style`, draft Section 2.4 in 320-400 counted words. Open with binary32/binary64 storage and unit roundoff. Then give a one-sentence example of how a simple expression such as a finite-difference sum changes under reordering or FMA fusion, citing the brief's explicit interest in "the result of simple expressions and algorithms". Continue with FMA / `-ffp-contract`, compiler-option families (`-Ofast`, `--use_fast_math`), and parallel reduction order. Cite Goldberg, IEEE 754-2019, and Higham each at least once and only when supporting a specific claim. Hedge: local differences can become measurable in nonlinear solvers, but the report measures the size rather than assuming it.
```

**Skill:** `writing-literature-review` + `academic-english-style`.

### 2.5 Gap statement for this report

**Topic sentence:** Existing numerical-method references establish the algorithms and benchmarks, but Report 1 isolates how the same nominal HRSC computation behaves across precision and hardware.

**Figure/table:** None.

**Citations:** Toro; Liska-Wendroff; Goldberg/Higham; project brief.

**Scoring alignment:** Literature/background [20%]; quality [20%]; handbook criterion 5.

**Requirements:** Link literature limitations directly to the report's validation matrix.

**Prompt:**
```text
Using `writing-literature-review`, draft Section 2.5 as the synthesis paragraph for the background chapter. Do not list papers. Group the literature into method foundations, benchmark design, and floating-point reliability. Then state the gap: Report 1 measures precision and hardware sensitivity under controlled Euler validation tests.
```

**Skill:** `writing-literature-review`.

## Chapter 3: Numerical Method

Working target: 1,080-1,220 counted words (hard upper 1,220).

Purpose: demonstrate mathematical understanding of the method used to generate the evidence.

### 3.1 Finite-volume update

**Topic sentence:** The numerical method evolves cell averages by balancing fluxes across cell interfaces, which makes the update naturally conservative.

**Figure/table:** Equation block for semi/discrete finite-volume update.

**Citations:** Toro; LeVeque optional.

**Scoring alignment:** Mathematical theory [20%]; handbook criterion 2.

**Requirements:** Define cell averages, numerical flux, time step, and CFL dependence.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 3.1. Present the finite-volume update for hyperbolic conservation laws, define the cell average and numerical flux, and connect the update to conservation. Use equations sparingly but clearly. Keep notation consistent with the later Euler variables.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 3.2 MUSCL-Hancock reconstruction and predictor

**Topic sentence:** MUSCL-Hancock raises the method to second order by reconstructing limited interface states and evolving them through a half-step predictor.

**Figure/table:** Pseudocode box or algorithm table.

**Citations:** Toro; van Leer.

**Scoring alignment:** Mathematical theory [20%]; code description [20%].

**Requirements:** Describe reconstruction, slope limiting, predictor, interface states, and why SLIC alone is not the chosen focus. The brief also names WAF as an acceptable explicit Riemann-solver-based example; mention it only as an alternative unless it is used in the evidence.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 3.2. Explain MUSCL-Hancock reconstruction and the half-step predictor in a way an assessor can follow without source code. Include the role of slope limiting and interface states. Mention that the project brief strongly suggests MUSCL-Hancock because Riemann-solver behaviour is central. If WAF is mentioned, identify it only as another brief-approved Riemann-solver-based option unless it is used in the report evidence.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 3.3 Riemann solver choice

**Topic sentence:** The Riemann solver determines the interface flux and is therefore a key algorithmic choice for both shock resolution and sensitivity studies.

**Figure/table:** Optional table comparing exact, HLLC, Rusanov/HLL if used.

**Citations:** Toro; Toro-Spruce-Speares for HLLC; Harten-Lax-van Leer if HLL is discussed.

**Scoring alignment:** Mathematical theory [20%]; code description [20%].

**Requirements:** State chosen solver. If HLLC is used, explain contact restoration and why it is suitable. If solver variation includes Rusanov, frame as method variation rather than reproducibility drift.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 3.3. Explain the chosen Riemann solver and why it is suitable for the Euler tests. If HLLC is used, explain contact preservation at a conceptual level and cite Toro-Spruce-Speares. If Rusanov appears later as a variation axis, identify it as a deliberately more diffusive comparator rather than the main method.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 3.4 Stability, limiters, and positivity

**Topic sentence:** The method's accuracy and stability depend on limiter choices, time-step restrictions, and treatment of strong discontinuities.

**Figure/table:** None or small table of method settings.

**Citations:** Toro; van Leer.

**Scoring alignment:** Mathematical theory [20%]; handbook criteria 2 and 4.

**Requirements:** Explain CFL, limiter role, possible loss of accuracy near extrema/discontinuities, and any positivity/stability caveats actually relevant to the implementation.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 3.4. Describe how CFL choice and limiting affect stability and accuracy. Distinguish formal second-order accuracy in smooth regions from reduced accuracy near shocks and contacts. Keep claims bounded to the method and tests in this report.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 3.5 Floating-point-sensitive algorithmic decisions

**Topic sentence:** Some algorithmic branches can be mathematically minor but numerically visible when wave speeds or tolerance tests are close to threshold values.

**Figure/table:** Link forward to variation table in Ch. 5/6.

**Citations:** Goldberg; Higham; project brief for `<` vs `<=` example.

**Scoring alignment:** Mathematical theory [20%]; validation [20%]; handbook criterion 4.

**Requirements:** Discuss `<` vs `<=`, exact-solver tolerances, limiter branches, reductions, and compiler options as possible sensitivity axes. **Scope statement (binding):** in Report 1, only `<` vs `<=` (HLLC wave-speed branch), compiler flags (O2/O3/Ofast±fast-math), HLLC-vs-Rusanov solver variation, and — if the supplementary minmod/vanleer experiment completes — limiter choice carry quantitative evidence. Exact-solver tolerances and parallel-reduction order are introduced as concepts only and explicitly marked as not measured in this report. Do not write "as the experiments below show" for the unmeasured axes.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 3.5. Explain why branch conditions, tolerances, limiter decisions, reductions, and compiler options may produce measurable differences in finite-precision runs. Use the project brief's `<` versus `<=` example. State explicitly which of these axes the report measures (HLLC branch rule, compiler flags, HLLC-vs-Rusanov, limiter if the supplementary run completes) and which are introduced at concept level only (tolerances, reductions). Do not claim large effects; state that the report measures their effect in selected cases.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 3.6 MHD extensions and Report 2 bridge

Working sub-target: ≤ 140 counted words.

**Topic sentence:** The Euler method forms the controlled validation base for later MHD work, where additional wave families and divergence control introduce further numerical choices.

**Figure/table:** None.

**Citations:** Bard and Dorelli only if no Bard-and-Dorelli citation has yet appeared in §1.3 or §2.2 (cap: Bard and Dorelli at most twice in the whole manuscript, see References Plan); Dedner/Evans-Hawley only if named.

**Scoring alignment:** Literature/background [20%]; mathematical theory [20%]; conclusion/future direction.

**Requirements:** Keep ≤ 140 words. This is conceptual bridge, not current validation evidence. Do not name an MHD method that the report does not use.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 3.6 as a short bridge. Explain that the Euler solver provides a controlled base for later ideal-MHD work, where additional waves and divergence control will add algorithmic choices. Avoid presenting MHD as already validated unless evidence exists in the report.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 4: Implementation and Experimental Design

Working target: 1,000-1,130 counted words (hard upper 1,130). **Pseudocode is counted by Overleaf Word Count**: budget at most ~100 counted words across all algorithm boxes in this chapter (≈ 15 lines at average density), so the prose budget is effectively 880-1,030 words. Verify Overleaf's counted-text behaviour for the `algorithmic` environment once during the Word-Budget Lock milestone before drafting §4.2.

Purpose: explain the implementation choices that make the evidence interpretable. This chapter is about the report's scientific design, not how to run the code.

This chapter carries the project brief's **Code description [20%]** requirement. It should therefore be specific enough for assessors to understand how the reported method and comparisons were produced, while remaining focused on interpretation and evidence quality.

### 4.1 Implementation route and comparability principle

**Topic sentence:** The implementation was organised so that precision and hardware could be varied while the nominal numerical algorithm remained comparable.

**Figure/table:** Candidate validation/test matrix can be introduced here.

**Citations:** AMReX citation only if AMReX is actually used/discussed; Bard and Dorelli for GPU-solver context if relevant.

**Scoring alignment:** Code description [20%]; handbook criteria 2, 3, 4.

**Requirements:** Explain AMReX or stand-alone route only insofar as it affects CPU/GPU, precision switching, and experiment control. If AMReX is discussed, note that the brief advises AMReX for hardware portability but does not expect AMR to be used. **Stand-alone code path is the chosen route for Report 1.** The brief's Code Description [20%] sub-bullet "ease of implementation and optimization features used" must be answered explicitly by naming these four features (all four are required, not optional):

1. fp32/fp64 templating in the CPU and GPU solver so the same source file produces both precisions through a single build flag.
2. CUDA-capable build switching via CMake (`ENABLE_CUDA=ON/OFF`) plus runtime `device=cpu/gpu` selection in CUDA-enabled binaries, producing matched within-case CPU/GPU comparisons from one source tree.
3. The Python-driven regression harness that re-runs the validation matrix and checks outputs against stored references.
4. The matched-binary CPU-vs-GPU switch: each within-case CPU/GPU comparison is run from one binary so that bit-identity claims are not confused with toolchain or compiler-flag differences.

This list satisfies the brief's sub-bullet; do not delegate it to the LLM prompt. The **toolchain split disclosure** from Global Requirements is also stated here in one sentence: Toro3 and Toro5 binaries are produced on Windows BuildTools, Sod/LW3/LW12 on Linux/WSL.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 4.1. Explain the implementation route and the comparability principle: the nominal algorithm should remain fixed while precision, hardware, and selected implementation choices vary. Mention AMReX only if it was used or directly relevant; if mentioned, state that the project brief advises AMReX for hardware portability but does not expect AMR. If the implementation is stand-alone (not AMReX), the section must also satisfy the brief's Code Description bullet by describing the ease-of-implementation and optimization features actually used — CPU/CUDA build switching, fp32/fp64 templating, the regression harness, the matched binary CPU-vs-GPU switch — and explain how each supports controlled comparison. Keep the section focused on interpretation and evidence quality, not on operational setup.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 4.2 Algorithmic structure of the implementation

**Topic sentence:** Each run follows the same sequence of reconstruction, Riemann solve, update, boundary treatment, and output measurement.

**Figure/table:** Algorithm table or flow diagram if useful; include at least one pseudocode box for the report-level implementation path.

**Citations:** Toro for algorithmic structure.

**Scoring alignment:** Code description [20%]; mathematical theory [20%].

**Requirements:** Describe computational stages at report level and anchor them to the most important source paths. The key code to explain is:

- `src/main.cpp`: configuration parsing and CPU/GPU dispatch (`parse_flux`, `parse_boundary`, `run_normal`, `run_normal_gpu`, and `main`). Use this to explain how the same test, solver, boundary condition, precision build, and output mode are selected for comparable runs.
- `src/euler/euler_solver.cpp`: CPU time step and sweep logic (`compute_dt`, `step`, `x_sweep`, `y_sweep`). Use this for the main pseudocode because it shows CFL selection, boundary application, dimensional splitting, MUSCL-Hancock face states, Riemann fluxes, conservative update, and Kahan time accumulation.
- `src/euler/hancock.hpp` and `src/euler/muscl.hpp`: reconstruction plus half-step predictor. Use only the essential equations or pseudocode, not a line-by-line translation.
- `src/euler/hllc.hpp`: HLLC wave-speed calculation and flux-region branch. Use this to connect the method description to the `<` vs `<=` sensitivity axis.
- `src/gpu/euler_gpu_solver.cu` and `src/gpu/euler_kernels.cu`: GPU mirror of the CPU step and per-face kernels (`EulerGpuSolver::step`, `sweep_x_gpu`, `sweep_y_gpu`, `hllc_flux_x_gpu`, `hllc_flux_y_gpu`). Explain that the GPU path mirrors the CPU algorithm while exposing hardware comparison.
- `src/core/boundary.hpp` and `src/utils/io.hpp`: boundary handling and binary output only where they affect validation, reference comparison, or CPU/GPU comparability.

The pseudocode should be concise and should not include internal project labels or repository-management detail.

**Hard length constraints (Overleaf counts pseudocode):**

- One CPU pseudocode box for `EulerSolver::step` plus sweep: ≤ 12 algorithm lines, each ≤ ~7 words, so ≤ ~85 counted words.
- One GPU-mirror paragraph (no second algorithm box): ≤ 60 prose words.
- Surrounding §4.2 prose excluding the algorithm box: ≤ 200 words.
- Total §4.2 counted contribution: ≈ 280-345 words.

**Prompt:**
```text
Using `scientific-writing-duke`, draft Section 4.2. Describe the implementation at report level: configuration dispatch, reconstruction, Riemann solve, update, boundary treatment, output quantities, and metric collection. Include exactly one pseudocode box based on `EulerSolver::step` and the sweep functions (≤ 12 algorithm lines, ≤ 7 words per line, total ≤ ~85 counted words), and exactly one short paragraph (≤ 60 words) explaining how the GPU path mirrors the same algorithm through per-face CUDA kernels (do not add a second algorithm box). Surrounding prose excluding the algorithm box must stay ≤ 200 words. Make clear where this mirrors the numerical method chapter and where implementation choices enter the evidence.
```

**Skill:** `scientific-writing-duke`.

### 4.3 Precision and hardware variants

**Topic sentence:** The experimental design compares fp32 and fp64 calculations on CPU and GPU so that precision and hardware effects can be separated as far as the available evidence allows.

**Figure/table:** Candidate precision/hardware matrix.

**Citations:** IEEE 754; Goldberg; Higham.

**Scoring alignment:** Code description [20%]; validation [20%]; handbook criteria 3, 4.

**Requirements:** Define fp32/fp64, CPU/GPU comparisons, and what is held fixed. Note any known limitations if hardware paths differ.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 4.3. Explain the fp32/fp64 and CPU/GPU variant matrix. State what is held fixed, what is changed, and how the comparison should be interpreted. Cite IEEE 754, Goldberg, or Higham for floating-point concepts. Hedge any claim that cannot be fully separated experimentally.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 4.4 Test-case matrix and metrics

**Topic sentence:** The validation suite was selected to cover 1D and 2D Euler behaviour, including shocks, contacts, rarefactions, and supersonic wave structures.

**Figure/table:** Validation matrix table with the following columns (binding): case, dimension, physical feature, **supersonic? (Y/N + which wave)**, **basis for supersonic label** (Mach value, wave speed, initial-state reference, or benchmark citation), reference solution, metrics, hardware (CPU/GPU), precision (fp32/fp64). The "supersonic" column is a binding brief checkbox and must not rely on assertion alone.

**Citations:** Sod; Toro; Liska-Wendroff; Woodward-Colella/Shu-Osher only if those tests are actually used.

**Scoring alignment:** Validation [20%]; quality [20%]; handbook criteria 3, 4, 6.

**Requirements:** Include at least four Euler tests, 1D + 2D, **supersonic waves**, CPU/GPU, fp32/fp64. Define metrics such as L1/L2/Linf, max difference, ULP if used. The validation matrix must show CPU and GPU coverage for each selected test, not only for a subset.

**Supersonic checkbox (binding mapping for the brief's explicit "supersonic waves" requirement):**

- Toro3 (Toro test 3, modified Sod with very strong right-going shock): supersonic right-running shock. Mark Y in the validation matrix, name the supersonic wave in §5.2 prose at first mention of Toro3, and give the basis for the label from the Toro initial states, a computed post-shock Mach number, or a wave-speed diagnostic.
- Toro5 (Toro test 5, collision of strong shocks): supersonic left- and right-running shocks. Mark Y, name the supersonic waves in §5.2 prose, and give the basis from the Toro test definition or measured wave-speed/Mach information.
- LW3 (Liska-Wendroff configuration 3): contains supersonic shock segments along quadrant interfaces. Mark Y, name the supersonic structures in §5.3 prose, and cite the Liska-Wendroff configuration or a case-specific diagnostic as the basis.
- LW12 (Liska-Wendroff configuration 12): contains supersonic shock segments. Mark Y, name them in §5.3 prose, and cite the Liska-Wendroff configuration or a case-specific diagnostic as the basis.
- Sod: subsonic-to-mildly-supersonic post-shock state depending on convention. Mark with explicit Mach value rather than a bare "supersonic" tick.

The brief's "supersonic waves" requirement is therefore met explicitly four times in the matrix (Toro3, Toro5, LW3, LW12) before Sod is considered, and the supersonic claim is named in prose at least four times across §5.2 and §5.3. The matrix must include the basis column so the label is auditable.

**Prompt:**
```text
Using `scientific-writing-duke`, draft Section 4.4 around a validation matrix table with these columns: case, dimension, physical feature, supersonic Y/N (and which wave), basis for supersonic label, reference solution, metrics, hardware, precision. Introduce each test by its purpose rather than by file name. Define the metrics used to quantify accuracy and CPU-GPU/precision differences. Ensure the matrix explicitly satisfies the project brief: at least four Euler ideal-gas cases, both 1D and 2D, including supersonic waves (Toro3, Toro5, LW3, LW12 each marked Y with the named supersonic wave and an auditable Mach/wave-speed/source basis), with each selected test evaluated on both CPU and GPU.
```

**Skill:** `scientific-writing-duke`.

### 4.5 Reference-solution strategy

**Topic sentence:** Reference solutions are needed to distinguish physical/numerical error from hardware or precision drift.

**Figure/table:** Candidate validation matrix column or separate small table: analytic/reference strategy by test.

**Citations:** Toro for exact Riemann; Liska-Wendroff for 2D benchmark; Higham for error framing.

**Scoring alignment:** Code description [20%]; validation [20%]; handbook criteria 3 and 4.

**Requirements:** Explain analytic references where available and high-resolution/converged references otherwise. Avoid overclaiming "exact" for 2D unless it is exact.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 4.5. Explain how reference solutions are determined for each test class. Use "exact" only for analytic/exact Riemann references; use "appropriately converged" or "high-resolution reference" for 2D or non-analytic cases. Explain why the reference choice is load-bearing for precision and hardware comparisons.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 5: Validation and Precision Results

Working target: 1,750-1,900 counted words (hard upper 1,900). Figures and tables in this chapter are not counted (course clarification), so this chapter may carry a large fraction of the report's 20+ figure/table count. Each figure/table must still be interpreted in prose.

Purpose: satisfy the evidence-heavy validation requirement. Draft this chapter first.

### 5.1 Validation overview

**Topic sentence:** The validation results are organised to separate solver correctness, precision effects, hardware differences, and selected implementation-variation axes.

**Figure/table:** Candidate validation matrix if not already in Ch. 4; otherwise refer back to it by its final LaTeX number.

**Citations:** None unless referencing benchmark sources.

**Scoring alignment:** Validation [20%]; quality [20%]; handbook criteria 3, 4, 6.

**Requirements:** Preview the result structure. Define metrics before using them.

**Prompt:**
```text
Using `scientific-writing-duke`, draft Section 5.1. Introduce the validation chapter as a controlled study, not a sequence of plots. Explain the four evidence questions: correctness, fp32/fp64 accuracy, CPU/GPU reproducibility, and sensitivity to selected implementation/compiler variations. Define the metrics or point to where they were defined.
```

**Skill:** `scientific-writing-duke`.

### 5.2 One-dimensional Euler validation

**Topic sentence:** The 1D tests verify that the solver captures standard shock-tube structures before precision and hardware effects are interpreted.

**Figure/table:** Candidate 1D exact-reference figure: Sod plus one or two Toro comparison plots; candidate 1D precision/error summary table.

**Evidence:** `experiments/week3/week3_validation/plots/sod_comparison.png`; `experiments/week3/week3_validation/plots/toro3_comparison.png`; `experiments/week3/week3_validation/plots/toro5_comparison.png`; `experiments/week7/report1_validation_1d/summary.md`; `experiments/week4/float_regression/1d/summary.md`; `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`.

**Citations:** Sod; Toro.

**Scoring alignment:** Validation [20%]; mathematical theory [20%]; handbook criteria 3, 4.

**Requirements:** Explicitly include at least three 1D tests in the main text or summary table: Sod, Toro3, and Toro5. Use the full 1D validation summary as supporting evidence if additional 1D cases are discussed. Interpret shocks, contacts, rarefactions, and quantify errors. Use the 1D device summary to state that Toro3 and Toro5 have matched CPU/GPU evaluations in both fp64 and fp32 under the strict HLLC setup. Do not refer to evidence by week number in prose.

**Supersonic prose requirement (binding):** Name the supersonic wave structures explicitly when introducing Toro3 (right-running supersonic shock) and Toro5 (collision of two supersonic shocks). This is how the brief's "include supersonic waves" requirement is met in prose; do not leave it to the reader to infer from the Mach values.

**Hard-number prepopulation (writer reads the summary and fills in; do not fabricate):** Section 5.2 must contain at least three numerical values pulled directly from the listed summary files — one fp64-fp32 final-state L1 difference from `experiments/week7/report1_validation_1d/summary.md` for Sod or Toro3, one exact/reference-scaled 1D value from `experiments/week4/float_regression/1d/summary.md` or its CSVs, and one CPU-GPU drift value (expected zero L1/Linf/ULP) from `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`. Do not call the Week 7 fp64/fp32 pair value a separate "fp64 error" or "fp32 error"; it is a double-versus-float difference. Numbers must be cited from the summary, not paraphrased ("comparable to discretisation error" without a number is not acceptable).

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 5.2 from the 1D validation evidence. Start with the purpose of the 1D tests, then interpret the Sod and selected Toro figures. When introducing Toro3 and Toro5, name the supersonic wave structure (Toro3: right-running supersonic shock; Toro5: collision of supersonic shocks) and give the matrix basis for the supersonic label. Use at least three numerical values: one fp64-fp32 final-state L1 difference from `experiments/week7/report1_validation_1d/summary.md`, one exact/reference-scaled 1D validation or adequacy value from `experiments/week4/float_regression/1d/summary.md` or its CSVs, and one CPU-GPU drift value from `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`; read them from the files, do not paraphrase. Avoid saying the plots "look good"; state which waves are captured and how the error metrics support validation.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.3 Two-dimensional Euler validation

**Topic sentence:** The 2D validation extends the assessment from shock-tube profiles to interacting multidimensional wave structures.

**Figure/table:** Candidate 2D validation figures: LW3 N=400 double schlieren; LW12 N=400 double density or schlieren; 2D reference-scaled precision table.

**Evidence:** `experiments/week7/report1_validation_2d/summary.md`; `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho_schlieren.png`; `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/summary.md`; `experiments/week8/report1_2d_config12_fill/precision_summary.md`; `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`; `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png`; `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho.png`.

**Citations:** Liska-Wendroff.

**Scoring alignment:** Validation [20%]; handbook criteria 3, 4.

**Requirements:** Explain what each 2D case tests. LW3 remains the established precision-diagnostic case with existing Verificarlo and high-resolution-reference evidence; LW12 adds a second 2D Riemann configuration with matched CPU/GPU and fp32/fp64 strict-HLLC evidence. Quantify reference comparisons where available: LW3 against the existing high-resolution reference and LW12 against the N=800 numerical reference. Do not rely on visual structure alone. Use the unified naming "Liska-Wendroff configuration 12 (LW12)" — do not write "config12".

**Supersonic prose requirement (binding):** Name the supersonic shock segments along quadrant interfaces in LW3 and LW12 when introducing each case. This is the 2D side of the brief's "include supersonic waves" checkbox.

**Prompt:**
```text
Using `scientific-writing-duke`, draft Section 5.3. Introduce the Liska-Wendroff 2D cases as multidimensional Euler validation problems. Treat Liska-Wendroff configuration 3 (LW3) and Liska-Wendroff configuration 12 (LW12) as two separate 2D Riemann configurations, not as one generic "2D case". When introducing each, name the supersonic shock structures along the quadrant interfaces. Interpret the N=400 double-precision schlieren/density figures by naming the visible wave structures, then connect each visual result to quantitative summary metrics. For LW12, use the N=800-reference summary: rho L1 double-reference error decreases from about 2.95e-3 at N=200 to 1.33e-3 at N=400, and rho SSIM increases from about 0.989 to 0.996. State clearly that the reference is a higher-resolution numerical reference, not an exact solution. Do not write "config12" or "LW12/config12".
```

**Skill:** `scientific-writing-duke`.

### 5.4 Single- versus double-precision comparison

**Topic sentence:** The fp32/fp64 comparison measures whether precision-induced differences are small or large relative to reference or discretisation error.

**Figure/table:** Candidate 1D/2D precision summary table; candidate precision-adequacy figure `float_double_over_reference_bar.png`.

**Evidence:** `experiments/week7/report1_validation_1d/summary.md`; `experiments/week7/report1_validation_2d/summary.md`; `experiments/week8/report1_2d_config12_fill/precision_summary.md`; `experiments/week4/float_regression/1d/summary.md`; `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`; `experiments/week7/report1_d2_replots/float_double_over_reference.csv`; `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png`; `experiments/week7/report1_d2_replots/region_losos_quantiles_rho.csv`; `experiments/week7/report1_d2_replots/summary.md`.

**Citations:** Goldberg; IEEE 754; Higham.

**Scoring alignment:** Validation [20%]; literature/background [20%]; handbook criteria 3, 4, 5.

**Requirements:** Avoid "fp32 is accurate enough" unless scoped to tested cases. Use direct fp32/fp64 ratios to reference/discretisation error for fp32 claims. **Scope of §5.4 (binding):** §5.4 covers only the direct fp32-vs-fp64 comparison against reference/discretisation error, including (a) the `stationary_contact` degenerate-reference row and (b) the resolution-dependent ratio behaviour. The Verificarlo virtual-precision regional discussion (LoSoS, region-aware margin, p32 vs IEEE binary32) is **moved to §6.2** so that §5.4 keeps a clean fp32/fp64-vs-reference narrative. §5.4 ends with one pointer sentence that the virtual-precision diagnostic in §6.2 explains the spatial structure of precision sensitivity.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 5.4. Compare fp32 and fp64 using quantitative summaries and the float-double/reference figure. First read the relevant metrics, then state whether the precision gap is smaller than, larger than, or comparable to the reference/discretisation error for the tested cases. Two caveats must appear explicitly: (1) the 1D `stationary_contact` row in `experiments/week4/float_regression/1d/summary.md` has L1_p fmd/d_err = inf because the double-vs-reference error is zero on this exact-stationary case; do not present this as a quantitative ratio, treat it as a degenerate-reference row; (2) the 2D float-double / reference ratio for LW3 grows with resolution (`L1_rho` ≈ 4.5e-5 at N=200, ≈ 9.3e-5 at N=400) because the reference error shrinks faster than the float-double drift; the same direction is seen in LW12 (`L1_rho` ratio ≈ 4.63e-5 at N=200 and ≈ 1.30e-4 at N=400 against the N=800 reference), so scope the adequacy claim to the tested resolutions and report the direction of change. End with one pointer sentence to §6.2 noting that the spatial structure of precision sensitivity is interpreted there using Verificarlo virtual-precision diagnostics; do not include the region-aware margin numbers or "p32" interpretation in §5.4 itself.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.5 CPU-GPU comparison

**Topic sentence:** The CPU-GPU comparison tests whether the same nominal algorithm produces measurably different results across hardware.

**Figure/table:** Candidate CPU-GPU quantitative comparison table: L1/Linf/ULP or available metrics.

**Evidence:** `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` (Sod fp32+fp64 and LW3 fp32 N=200/N=400 HLLC strict); `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md` (Toro3, Toro5 fp32+fp64 HLLC strict); `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` (LW3 fp64 N=200/N=400 HLLC strict); `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` (LW12 fp32+fp64 N=200/N=400 HLLC strict). `experiments/week6/regression/summary.md` remains as Rusanov strict provenance only and is not cited in the HLLC reproducibility claim.

**Citations:** Goldberg/Higham for numerical framing; Bard and Dorelli only for GPU solver context.

**Scoring alignment:** Validation [20%]; code description [20%]; handbook criteria 3, 4.

**Requirements:** Must quantify CPU-GPU difference for the selected five-case set. The current matched-device evidence supports Sod, Toro3, Toro5, LW3, and LW12; report zero L1/Linf/ULP drift where the summaries show it, but keep the claim scoped to the listed strict-device runs, final-time conservative state, and tested precisions.

**Toolchain footnote (binding for the §5.5 table):** the CPU-vs-GPU table in §5.5 must carry a footnote stating the toolchain split (Toro3/Toro5: Windows BuildTools; Sod/LW3/LW12: Linux/WSL) and the matched-binary principle (one binary per within-case CPU/GPU comparison). This is the §5.5 instance of the toolchain split disclosure declared in Global Requirements.

**Optional supplementary evidence (use only if the planned mid-time CPU/GPU experiment in `experiments/report1_evidence_map.md` "Planned supplementary experiments" has completed):** add one additional row stating CPU-GPU drift at intermediate-time checkpoints for the same selected cases, bounding the "final-time only" caveat. If this experiment has not produced an output by drafting time, omit the row and keep the explicit "final-time conservative state" boundary unchanged.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 5.5. Use the CPU-vs-GPU summaries to quantify differences, not just state visual agreement. State that all five selected cases (Sod, Toro3, Toro5, LW3, LW12) are covered by matched CPU/GPU runs under `solver=hllc` and `STRICT_IEEE=ON` in both fp32 and fp64: Sod fp32+fp64 and LW3 fp32 N=200/N=400 from the matched HLLC strict device-comparison summary, Toro3/Toro5 from the 1D device summary, LW3 fp64 N=200/N=400 from the 2D HLLC strict device summary, and LW12 fp32+fp64 N=200/N=400 from the LW12 device-comparison summary. Carry a single footnote on the CPU-vs-GPU table stating the toolchain split (Toro3/Toro5 on Windows BuildTools; Sod/LW3/LW12 on Linux/WSL) and the matched-binary principle (one binary per within-case comparison). Report zero L1/Linf/ULP drift only where the evidence files show it (here, zero on the conservative state at final time for all five cases in both precisions), then state what this does and does not imply about intermediate-time outputs, other compiler settings, untested cases, non-strict builds, or future MHD cases. If the planned intermediate-time supplementary experiment has completed, add one sentence reporting whether mid-evolution snapshots remain bit-identical; otherwise keep the final-time-only boundary explicit. Use the unified naming "LW12", not "config12". Do not mention local week numbers or internal experiment nicknames.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.6 Compiler, branch, and solver variation

**Topic sentence:** Selected implementation variations provide a controlled way to test whether small algorithmic or compiler choices can exceed precision or hardware drift.

**Figure/table:** Variation summary table or drift-timeseries figure.

**Evidence:** `experiments/week7/report1_variation/summary.md`; `experiments/week8/report1_variation_extend/summary.md`; `experiments/week7/report1_variation/axis_o2_vs_ofast.*`; `experiments/week7/report1_variation/axis_leq_vs_strict.*`; `experiments/week7/report1_variation/axis_hllc_vs_rusanov.*`; `experiments/week7/lyapunov_1d_full/summary.md`; `experiments/week7/lyapunov_1d_full/timeout_notes.json`; `experiments/week8/toro2_lt_branch_retry/summary.md`; `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png`.

**Citations:** Higham; Goldberg; project brief for variation examples.

**Scoring alignment:** Mathematical theory [20%]; validation [20%]; code description [20%]; handbook criteria 3, 4.

**Requirements:** Treat HLLC-vs-Rusanov as method variation, not reproducibility drift. Treat zero results as valid findings if measured. Cover the brief's suggested sensitivity axes where evidence exists: compiler options, simple Riemann-solver branch/tolerance changes, resolution or time evolution, and hardware. Floating-point precision is covered directly in §5.4; §5.6 must not imply that the compiler/branch/solver variation table covers fp32 unless the planned fp32 compiler-flag supplementary run has completed and is explicitly added as a tagged row.

**Structure (binding): split §5.6 into two subsubsections to keep prompts and prose manageable.**

- §5.6a "Compiler, branch-rule, and solver variation" — final-time variation table on Sod, stationary_contact, LW3-N200, Toro3, Toro5. CPU double only. Carry the brief's `<` vs `<=` mapping (HLLC wave-speed branch, `RIEMANN_STRICT_INEQUALITY` CMake option) and the HLLC-vs-Rusanov framing as method variation. If the planned fp32 × compiler-flag supplementary experiment has completed, add it as one row of the same table with a column note that this row is fp32 (all other rows remain CPU double).
- §5.6b "Time-resolved drift and the Toro2 `<` non-completion" — drift-timeseries figure, the side-by-side Toro2 `<` non-completion vs `<=` completion, and the explicit warning that fitted λ are finite-time slopes from 10 checkpoints, not Lyapunov exponents.

**Prompt for §5.6a:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft §5.6a "Compiler, branch-rule, and solver variation". Build the section around one summary table covering Sod, stationary_contact, LW3-N200, Toro3, and Toro5 under three axes: `<=` vs `<` HLLC wave-speed branch (map this to `RIEMANN_STRICT_INEQUALITY`; cite the brief's note that the branch only matters when wave speeds are close to zero), O2 vs O3 vs Ofast±fast-math compiler flags, and HLLC vs Rusanov as method variation. All rows are CPU double; state this once explicitly. If the planned fp32 × compiler-flag supplementary experiment has produced a result, add a single fp32 row with a clear precision-column tag. Distinguish reproducibility drift (branch, compiler) from deliberate method changes (HLLC vs Rusanov). Use descriptive labels ("branch-rule comparison", "compiler-flag comparison", "solver-variation comparison"); no week numbers, no D1/D2-style shorthand.
```

**Prompt for §5.6b:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft §5.6b "Time-resolved drift and Toro2 branch stability". Use the drift-timeseries figure for the 1D Toro cases under `<=` and the independent retry summary for Toro2 under `<`. Three constraints: (1) the fitted λ values are finite-time slopes from 10 synchronized checkpoints, so report them as case-ordering evidence (which cases are more sensitive) rather than as Lyapunov exponents — do not use the term "Lyapunov exponent" in the prose. (2) Toro2 under `<` did not complete (timeout after writing only the first two checkpoints); the independent retry reproduces non-completion of `<` while `<=` completes in ~0.13 s under the same toolchain. Report this as branch-specific stability degradation on the near-vacuum 123 case, consistent with the brief's note that `<` vs `<=` matters when wave speeds approach zero; do not report Toro2 `<` as a zero-drift row. (3) Keep prose to ≤ 200 counted words; the figure carries the case-ordering claim.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 6: Discussion

Working target: 600-720 counted words (hard upper 720).

Purpose: synthesise results without repeating them. Explain what the validation evidence means for the project question.

### 6.1 What the validation establishes

**Topic sentence:** The validation evidence supports the use of the solver and test matrix as a basis for measuring precision and hardware effects.

**Figure/table:** Refer back to core validation figures/tables; no new figure needed.

**Citations:** None unless re-grounding in benchmark literature.

**Scoring alignment:** Validation [20%]; handbook criteria 3 and 5.

**Requirements:** Synthesis, not restatement. Explain why correctness evidence is sufficient for Report 1.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 6.1. Synthesize what the 1D and 2D validation evidence establishes. Do not repeat every result. Explain why the solver and test matrix are adequate for measuring the precision and hardware effects required in Report 1.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 6.2 Precision effects relative to numerical error

**Topic sentence:** The precision results are most meaningful when interpreted relative to discretisation or reference error rather than as raw float-double differences.

**Figure/table:** Refer to float-double/reference figure; optionally region-aware precision figure.

**Citations:** Higham; Goldberg.

**Scoring alignment:** Validation [20%]; handbook criteria 4 and 5.

**Requirements:** Discuss ratios and regimes. Include any low-precision or region-aware finding only if it clarifies precision sensitivity or the limits of the direct fp32/fp64 comparison; direct fp32 adequacy claims must use real fp32/fp64 evidence. **§6.2 now owns the Verificarlo virtual-precision regional interpretation** (moved from §5.4); §5.4 ends with a pointer to §6.2.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 6.2. Interpret the fp32/fp64 results relative to reference or discretisation error. Use the float-double/reference ratio for direct fp32 claims. The region-aware precision figure is owned by this section: state explicitly that it is a Verificarlo virtual-precision diagnostic and that virtual p32 is not IEEE binary32/fp32. Report the regional margins from the LoSoS summary: at virtual p32 the HLLC LoSoS median margin is positive in the smooth region (~+1.9 digits) and negative in the transition (~-0.17) and discontinuity (~-1.76) regions; this is a spatially non-uniform statement about the diagnostic precision sweep, not a universal "fp32 is adequate" claim. If referring to `experiments/week7/verificarlo_report1_refresh/summary.md`, explain that **every** precision row (including p53) shows a worst-q05 precision-adequacy deficit because the q05 statistic is dominated by shock/contact cells whose discretisation-side error is independent of FP precision; do not present the deficit table as evidence that fp32 is inadequate for production runs. Mention that the available MCA quantiles are descriptive summaries of a small sample set. Keep the conclusion scoped to the tested cases and the tested precisions.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 6.3 Hardware and implementation sensitivity

**Topic sentence:** Hardware differences must be interpreted alongside compiler and implementation choices, because the latter can create comparable or larger drift in some regimes.

**Figure/table:** Variation/drift figure.

**Citations:** Goldberg; Higham; Demmel/Nguyen only if reductions/reproducibility are discussed explicitly.

**Scoring alignment:** Code description [20%]; validation [20%]; handbook criteria 3, 4, 5.

**Requirements:** Compare CPU-GPU, compiler flags, branch rules, solver variation. Avoid universal claims.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 6.3. Compare the CPU-GPU findings with compiler/branch/solver variation. Explain whether hardware differences are smaller, larger, or comparable to other variation axes in the tested evidence. Make clear which conclusions are specific to strict double, fp32, selected test cases, or selected compilers.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

### 6.4 Limitations and implications for Report 2

**Topic sentence:** The Report 1 conclusions are limited by the Euler test suite and selected hardware/precision axes, but they define a controlled baseline for later MHD work.

**Figure/table:** None.

**Citations:** Bard and Dorelli; MHD references only if future tests are named.

**Scoring alignment:** Handbook criteria 4 and 5; conclusion/future direction.

**Requirements:** Limitations should bound claims, not apologise. Future work must follow from evidence.

**Prompt:**
```text
Using `scientific-writing-duke` and `academic-english-style`, draft Section 6.4. State the main limitations: Euler-focused validation, selected test cases, selected hardware/compiler axes, and reference-solution assumptions. Then explain how these limitations define the next MHD experiments rather than weakening Report 1. Avoid generic "more research is needed" phrasing.
```

**Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 7: Conclusion

Working target: 330-430 counted words (hard upper 430).

Purpose: answer the introduction's question with bounded claims and a concrete next step.

### Conclusion evidence lock

Use only these conclusion claims unless a later evidence review adds a new artifact to the outline. The conclusion and abstract must not convert planned work, missing device coverage, or template examples into completed Report 1 results.

| Allowed conclusion claim | Evidence that must be checked | Boundary |
|---|---|---|
| 1D Euler validation is documented for the selected 1D cases, including Sod and strong Toro cases. | `experiments/week7/report1_validation_1d/summary.md`; `experiments/week3/week3_validation/plots/sod_comparison.png`; `experiments/week3/week3_validation/plots/toro3_comparison.png`; `experiments/week3/week3_validation/plots/toro5_comparison.png` | Treat as solver/precision validation unless matched CPU and GPU evidence is also shown for the same case. |
| 2D Euler validation is documented for two Liska-Wendroff Riemann configurations, LW3 and LW12. | `experiments/week7/report1_validation_2d/summary.md`; `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho_schlieren.png`; `experiments/week7/report1_validation_2d_gpu/summary.md`; `experiments/week8/report1_2d_config12_fill/summary.md`; `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`; `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png` | Do not generalise from these two configurations to all 2D Riemann problems or to shock-bubble/MHD. LW12 uses an N=800 numerical reference, not an exact solution. Use the unified prose label "LW12" (the directory name `report1_2d_config12_fill` is internal). |
| CPU-GPU differences are quantified for the selected cases with matched device runs under `solver=hllc`, `STRICT_IEEE=ON`. | `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` (Sod fp32+fp64; LW3 fp32 N=200/N=400); `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md` (Toro3, Toro5 fp32+fp64); `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` (LW3 fp64 N=200/N=400); `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` (LW12 fp32+fp64 N=200/N=400) | Supports Sod, Toro3, Toro5, LW3, and LW12 in both fp32 and fp64, each showing zero L1/Linf/ULP drift on the conservative state at final time. **Toolchain split boundary (binding):** Toro3/Toro5 binaries are produced on Windows BuildTools; Sod/LW3/LW12 on Linux/WSL. Each within-case CPU-vs-GPU comparison uses one binary, so bit-identity holds within a case independently of cross-case toolchain differences. Do not generalise to untested Toro/LW cases, to non-strict builds, to intermediate-time outputs (unless the planned intermediate-time supplementary experiment has completed and is cited explicitly), or to MHD. `experiments/week6/regression/summary.md` is Rusanov strict and is not part of this claim. |
| fp32/fp64 differences can be compared with reference or discretisation error in the tested cases. | `experiments/week4/float_regression/1d/summary.md`; `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`; `experiments/week7/report1_d2_replots/float_double_over_reference.csv`; `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png` | State the measured scope and variables; do not say fp32 is generally adequate for HRSC or MHD. Direct fp32 claims must come from real fp32/fp64 runs, not from virtual p32 diagnostics. |
| Region-aware virtual-precision diagnostics show spatially non-uniform precision sensitivity in LW3. | `experiments/week7/report1_d2_replots/region_losos_quantiles_rho.csv`; `experiments/week7/report1_d2_replots/summary.md`; `experiments/week7/report1_d2_replots/region_losos_margin_rho_p32.png`; `experiments/week7/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png` | Treat `p32` as Verificarlo virtual precision, not IEEE binary32. Use these figures to discuss spatial structure and diagnostic sensitivity only; note the small MCA sample counts if quantiles are reported. |
| Compiler, branch-rule, solver, and drift-growth variation axes were measured as sensitivity evidence. | `experiments/week7/report1_variation/summary.md`; `experiments/week8/report1_variation_extend/summary.md`; `experiments/week7/lyapunov_1d_full/summary.md`; `experiments/week8/toro2_lt_branch_retry/summary.md` | Compare axes only where the same metric and setup make the comparison meaningful. Variation rows are CPU double only unless explicitly stated. Report Toro2 `<` as non-completion/stability degradation, not as a zero-drift row. |

Do not write conclusion claims that MHD validation has been completed, that the full Euler catalogue has CPU-GPU coverage, that HLLC is universally superior, that hardware has no effect, or that fp32 is adequate outside the measured cases.

### 7.1 Restate aim and evidence base

**Topic sentence:** This report examined how precision and hardware affect a Riemann-solver-based HRSC method under controlled Euler validation tests.

**Figure/table:** None.

**Citations:** None unless briefly naming benchmark source.

**Scoring alignment:** Handbook criterion 5; quality [20%].

**Requirements:** No new literature. No new results.

**Prompt:**
```text
Using `writing-conclusion` and `report1-context`, draft the opening of the conclusion. Restate the aim in the same terms as the introduction: precision, hardware, HRSC schemes, and controlled Euler validation. Do not introduce new citations or new evidence.
```

**Skill:** `writing-conclusion` + `report1-context`.

### 7.2 Key findings

**Topic sentence:** The main findings are that Euler validation and fp32/fp64 comparisons are documented for the tested cases, while CPU-GPU claims must be restricted to the cases with matched device evidence.

**Figure/table:** Refer verbally to key figures/tables; do not add new visuals.

**Citations:** None.

**Scoring alignment:** Validation [20%]; handbook criteria 3 and 5.

**Requirements:** Use 2-4 findings only. Include numbers only from the evidence lock above.

**Prompt:**
```text
Using `writing-conclusion` and `academic-english-style`, draft the key-findings paragraph. Name only the load-bearing results in the conclusion evidence lock: 1D/2D validation, fp32/fp64 comparison, CPU-GPU quantification for matched device runs, and selected variation axes. Include representative numerical values only when they appear in the listed evidence files. Hedge implications but report measured findings directly.
```

**Skill:** `writing-conclusion` + `academic-english-style`.

### 7.3 Contribution, limitations, and next step

**Topic sentence:** Together, the results provide a controlled Euler baseline for the wider MHD precision/hardware study.

**Figure/table:** None.

**Citations:** Bard and Dorelli only if the MHD/GPU next step is explicitly connected.

**Scoring alignment:** Handbook criteria 4 and 5; quality [20%].

**Requirements:** End with one concrete next step into Report 2. Do not overclaim.

**Prompt:**
```text
Using `writing-conclusion` and `academic-english-style`, draft the final conclusion paragraph. Synthesize the contribution as a controlled Euler baseline for later MHD precision/hardware work. State the main limitation in neutral terms and give one concrete next step for Report 2, such as extending the validated framework to ideal-MHD tests with divergence control. End with a clear, evidence-bounded take-home sentence.
```

**Skill:** `writing-conclusion` + `academic-english-style`.

## Abstract

Working target: 180-220 counted words (hard upper 220). Write last.

**Topic sentence:** Not applicable; the abstract should be a single compact paragraph.

**Figure/table:** None.

**Citations:** Usually none.

**Scoring alignment:** Quality [20%]; handbook criterion 6.

**Requirements:** Include problem, method, validation scope, headline results, and contribution. Avoid literature review and excessive detail. **Must contain at least two specific numerical values** taken from the conclusion evidence lock — for example, one CPU-GPU drift magnitude (expected zero L1/Linf/ULP for the matched five-case set) and one fp32 vs fp64 ratio against reference (e.g., the LW12 N=400 ratio ≈ 1.30e-4). Abstracts without numbers default to AI-flavoured hedge language and are flagged in the avoiding-ai-flavor self-review.

**Prompt:**
```text
Using `academic-english-style`, write a 180-220 word abstract for Report 1. Include: the project problem, the Euler HRSC validation scope (Sod, Toro3, Toro5, LW3, LW12 — using unified naming, not "config12"), the CPU/GPU and fp32/fp64 comparison design, the strongest quantitative findings allowed by the conclusion evidence lock, and the contribution to the later MHD precision/hardware study. Include at least two specific numerical values (one CPU-GPU drift, one fp32-vs-fp64-vs-reference ratio) drawn from the conclusion evidence lock; do not paraphrase magnitudes. Do not include citations. Keep claims bounded to the tested cases and do not imply completed MHD validation.
```

**Skill:** `academic-english-style`.

## References Plan

Use `report1/reference.md` as the citation map.

| Report section | Core citations | Conditional citations |
|---|---|---|
| Introduction | Toro; Goldberg; IEEE 754-2019; Higham | Bard and Dorelli for GPU/MHD motivation |
| Background | Toro; Liska-Wendroff; Goldberg; Higham; IEEE 754-2019 | van Leer; Harten-Lax-van Leer; MHD references if named |
| Numerical method | Toro; van Leer; Toro-Spruce-Speares | Roe; Harten-Lax-van Leer; Dedner/Evans-Hawley if MHD methods named |
| Implementation design | Toro; IEEE 754-2019; Goldberg | AMReX if used; Bard and Dorelli if GPU solver context matters; Denis et al. (Verificarlo) if the harness uses MCA grids |
| Validation | Sod; Toro; Liska-Wendroff | Denis et al. (Verificarlo) and Parker (Monte Carlo Arithmetic) when introducing sigma_FP / LoSoS / noise-to-error figures, because those derive from MCA precision sweeps; Woodward-Colella/Shu-Osher only if those tests are used |
| Discussion | Higham; Goldberg | Denis et al. (Verificarlo) if region-margin or sigma_FP figures appear in §6.2; Demmel/Nguyen if reproducible reductions are explicitly discussed |
| Conclusion | Usually none | Bard and Dorelli only for a concrete MHD next step |

Rules:

- Do not cite a source unless it supports a specific sentence.
- Do not include lead-only references in the bibliography until verified.
- Prefer non-integral citations for established technical facts and integral citations when the author's stance matters.
- Keep the bibliography compact. A strong Report 1 does not need a long survey list.

Citation caps (binding for high-frequency or motivation-only references):

- **Bard and Dorelli (2014):** at most **two** appearances in the whole manuscript. Each must connect to a specific technical decision (e.g., "MUSCL-Hancock on GPU" or "MHD-on-accelerator motivation for Report 2"), not to generic "motivation". Suggested placement: §1.3 *or* §2.2, plus §6.4 / §7.3 if explicitly bridging into Report 2.
- **Higham (2002):** prefer at most three appearances; each must support a specific numerical-error claim, not provide background atmosphere.
- **Goldberg (1991) and IEEE 754-2019:** prefer at most two appearances each across the report; they support §2.4 and one §6.2 sentence.
- **Toro (2009):** uncapped because it underwrites finite-volume, MUSCL-Hancock, HLLC, Sod, and Toro tests; but each citation should still attach to a specific equation, algorithm, or test definition rather than appear as decoration.

## Drafting Milestones

Use these milestones in order.

1. **Evidence lock**
   - Finalise main figures/tables.
   - Write one claim per figure/table.
   - Confirm every required Report 1 validation axis is covered.
   - Lock the main-text Euler set as Sod, Toro3, Toro5, LW3, and LW12 unless a later evidence review gives a stronger replacement.
   - Confirm CPU/GPU evidence remains traceable for every selected test: Sod, Toro3, Toro5, LW3, and LW12.

2. **Word-budget lock**
   - Allocate counted-word targets before drafting full prose using the per-chapter caps in the Word Budget Lock block at the top of this file.
   - Keep the Overleaf Word Count target ≤ 7,400 counted words to preserve ≥ 80 words of revision margin under the 7,500 hard cap.
   - Tables and figure captions are not counted under the current course clarification, but keep them concise for presentation quality.
   - **Pseudocode IS counted.** Before drafting §4.2, paste a 5-line throwaway `algorithm` block into the Overleaf draft and verify that Overleaf Word Count increases by ~5 × words/line; if Overleaf is configured differently, recalibrate the §4.2 cap before drafting.
   - Use the figure/table headroom: tables and captions are free, so a results-chapter density of 20-24 main figures/tables (as in the Davison-Petch example) is appropriate provided each item carries a distinct claim; move duplicate heatmaps or provenance-only visuals to appendix rather than deleting load-bearing evidence.

3. **Supplementary experiments (run before §5.5/§5.6/§3.5 drafting, ideally during the evidence-lock milestone).** See `experiments/report1_evidence_map.md` § "Planned supplementary experiments" for full specification. Each entry below should produce one summary file that the relevant outline section can cite; if any run does not complete, leave the section's optional-evidence paragraph out and keep the existing scoped wording.

    - **Intermediate-time CPU/GPU snapshots** on Sod and LW3 (and ideally LW12) at 3-5 mid-evolution checkpoints, comparing L1/Linf/ULP between matched CPU and GPU binaries. Output: `experiments/<weekN>/cpu_gpu_midtime/summary.md`. Used by §5.5 to bound the "final-time only" caveat and by §6.3 to discuss whether device drift accumulates in time.
    - **fp32 × compiler-flag mini-matrix** on Sod (and optionally Toro3) under fp32, varying O2/O3/Ofast±fast-math, all CPU. Output: `experiments/<weekN>/variation_fp32/summary.md`. Used by §5.6a as one additional fp32 row in the variation table and by §6.3 to compare "compiler flag effect vs precision effect".
    - **Limiter variation** on Sod (and optionally LW3-N200) under fp32 and fp64, varying minmod vs van Leer (and any other limiter actually implemented), CPU double + fp32. Output: `experiments/<weekN>/variation_limiter/summary.md`. Used by §3.5 to upgrade the "limiter branch" axis from a conceptual mention to a quantitative entry, and by §5.6a as an additional row if it materially changes drift.

    Each summary must include: case, axis, precision, hardware, L1/Linf/ULP for the conservative state at final time (or per checkpoint for the intermediate-time experiment), and one sentence on interpretation. All three are CPU-only by default; the intermediate-time experiment requires GPU as well.

4. **Results skeleton**
   - Write Chapter 5 section headings.
   - Add figure/table placeholders.
   - Write one topic sentence per paragraph.

5. **Results full draft**
   - Draft Sections 5.1-5.6.
   - Use numeric evidence from summaries, not memory.
   - Apply `scientific-writing-duke`.

6. **Implementation design draft**
   - Draft Chapter 4 around comparability, test matrix, and reference solution.
   - Keep the section focused on interpretation and evidence quality.

7. **Numerical method draft**
   - Draft Chapter 3 with equations/pseudocode.
   - Ensure variables and notation match Chapter 5 metrics.

8. **Background draft**
   - Draft Chapter 2 thematically, not chronologically.
   - End with a gap statement.

9. **Introduction draft**
   - Draft Chapter 1 after the evidence and contribution are clear.
   - Use narrowing funnel.

10. **Discussion and conclusion**
    - Draft Chapter 6 as synthesis.
    - Draft Chapter 7 with the conclusion six-move structure.

11. **Abstract**
    - Write last, after findings are stable.

12. **Assessment pass**
    - Check five 20% brief categories.
    - Check six handbook criteria.
    - Check the Overleaf Word Count result remains below 7,500.

13. **Reference pass**
    - Verify each citation supports a sentence.
    - Remove unused or ornamental citations.

14. **Figure/table pass**
    - Captions self-contained.
    - Axes and units/nondimensional quantities labelled.
    - Each figure/table interpreted in prose.

15. **Style pass**
    - Use `editing-academic-prose`.
    - Then use `avoiding-ai-flavor`.

## Final Self-Review Checklist

Content and evidence:

- [ ] The report states a clear question about precision, hardware, and HRSC schemes.
- [ ] Euler validation is clearly the Report 1 evidence base.
- [ ] MHD is present as project context/future direction, not as unearned Report 1 evidence.
- [ ] At least five Euler tests are discussed, with both 1D and 2D included; the selected set is Sod, Toro3, Toro5, LW3, and LW12 unless a stronger evidence-complete set replaces it. Prose uses the unified label "LW12" (not "config12" or "LW12/config12").
- [ ] **Supersonic waves** are named in prose for Toro3, Toro5, LW3, and LW12; the validation matrix has a "supersonic Y/N (and which wave)" column. Brief checkbox satisfied four times.
- [ ] CPU and GPU results are quantitatively compared for every selected validation test (Sod, Toro3, Toro5, LW3, LW12) under `solver=hllc` and `STRICT_IEEE=ON`, in both fp32 and fp64.
- [ ] Toolchain split disclosure appears in Chapter 4 implementation prose, as a footnote on the §5.5 CPU/GPU table, and as a boundary line in the Chapter 7 evidence lock — three places, consistent wording.
- [ ] Single and double precision are quantitatively compared. Region-dependent precision adequacy is acknowledged.
- [ ] Verificarlo `p32` is described as virtual precision, not as IEEE binary32/fp32; direct fp32 claims come only from real fp32/fp64 runs.
- [ ] Final-time `<` vs `<=` HLLC branch rows may cite `report1_variation/axis_leq_vs_strict`; time-resolved branch evidence and the Toro2 `<` non-completion must cite `lyapunov_1d_full` and `toro2_lt_branch_retry`. Toro2 `<` is reported as non-completion/stability degradation rather than a zero-drift result.
- [ ] Figures derived from Verificarlo MCA grids cite Denis et al. (2016) and Parker (MCA 1997) at least once.
- [ ] Each figure/table has a claim attached.
- [ ] Each precision/hardware claim is scaled against a metric or reference.
- [ ] Method theory explains the algorithm sufficiently without source code.
- [ ] Implementation description explains comparability and evidence quality. If the implementation is stand-alone, ease-of-implementation/optimization features are described as the brief requires.
- [ ] The discussion separates findings from implications.
- [ ] The conclusion introduces no new evidence.
- [ ] The bibliography is compact and verified.
- [ ] Prose avoids overclaiming, generic academic filler, and AI-flavoured phrasing.

Formatting and integrity (handbook compliance):

- [ ] 12-point font, 1.5 or double line spacing, ≥ 2 cm margins on all sides.
- [ ] Title page: author's name, approved project title, and degree at the top; supervisor name at the bottom right corner; "Report 1" identification present if the template renders it. Use the author's name, not BGN.
- [ ] Declaration page present with the verbatim handbook wording: "This project report is substantially my own work and conforms to the University of Cambridge's guidelines on plagiarism. Where reference has been made to other research this is acknowledged in the text and bibliography."
- [ ] Wordcount declaration recorded from Overleaf Word Count. The controlling Overleaf counted-text value is ≤ 7,500; the drafting target is ≤ 7,400 (per-chapter caps in the Word Budget Lock block sum to 7,220). Do not use a `texcount` mode that counts table cells or figure captions as the controlling value, because current course clarification says tables and captions are not counted. **Pseudocode IS counted** by Overleaf Word Count — §4.2 budget already absorbs this.
- [ ] Abstract contains at least two specific numerical values drawn from the conclusion evidence lock (one CPU-GPU drift, one fp32-vs-fp64-vs-reference ratio).
- [ ] No Blind Grading Number or BGN is used as the author identifier.
- [ ] No AI-generated paragraph is left as raw output; every AI-assisted paragraph has been rewritten in the student's own voice and passed `avoiding-ai-flavor/SKILL.md`.
