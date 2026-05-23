# Supervisor Feedback Map

Source feedback:

- Supervisor guide: `report1\planning\supervisorguide.md`
- Feedback target: discarded `report1\draft2.pdf`
- Current writing workspace: `report1/phd-thesis-template-2.4/`

This file converts the supervisor's Draft 2 comments into writing actions for
future Report 1 agents. It is not manuscript prose. Use it together with
`report1/planning/manuscript_outline.md`, `report1/planning/reportagents.md`,
and `experiments/report1_evidence_map.md`.

Update note:

- This map includes the later supervisor update in
  `C:/Users/tangy/Desktop/supervisorguide.md`, including the Chapter 5 table and
  figure readability comments, the Chapter 6/7 consolidation advice, and the
  global citation/style requirements.

## Binding Global Rules

1. Remove all TODO or LLM-directive text from manuscript-facing files before
   submission. The Draft 2 Word Count Declaration and Abstract were explicitly
   flagged as LLM directives.
2. Define specialist terms before using them. This applies especially to CFL,
   TVD, HLLC, CUDA, thread block, OpenMP schedule, Verificarlo, MCA, SSIM, unit
   roundoff, and build flags.
3. Avoid using "rows" as a general manuscript word. Prefer "comparisons",
   "entries", "cases", "experiments", or "table entries", depending on the
   context.
4. Add interpretation after tables. Do not repeat the numbers in prose without
   explaining the relative size, test purpose, or evidence boundary.
5. Use code snippets sparingly when they clarify project-specific constructs
   such as `FLOAT_PRECISION`, `STRICT_IEEE`, `FAST_MATH`, and
   `RIEMANN_STRICT_INEQUALITY`.
6. Present compiler flags and compile-time switches as short code listings,
   code-like blocks, or compact tables. Do not bury long flag sequences in a
   sentence.
7. Do not direct assessors to source files as the explanation. Summarise the
   implementation in the report, or show a short code-like excerpt if needed.
8. Keep precision and hardware claims scoped to tested Euler cases, tested
   precisions, tested compiler settings, and named evidence artifacts.
9. Use author-name prose when citing specific methods, solvers, or benchmark
   families. Prefer forms such as "Toro's exact Riemann solutions", "Sod's shock
   tube", "Liska and Wendroff's configurations", or "Denis et al.'s
   Verificarlo" before the citation, rather than relying only on parenthetical
   citations.
10. Protect technical capitalization in BibTeX titles with braces, e.g. `{HLL}`,
   `{HLLC}`, `{GPU}`, `{CUDA}`, `{MHD}`, `{IEEE}`, `{AMReX}`, `{MUSCL-Hancock}`,
   `{1D}`, `{2D}`, and `{Euler}`.
11. All plots must be readable in the submitted PDF without zooming. Axes,
   legends, right-side labels, and annotations need to be large enough after
   LaTeX scaling.
12. Define Verificarlo/MCA and the distinction between Verificarlo `p32` and
   IEEE binary32 before Chapter 6 relies on that distinction. `p32` is a virtual
   mantissa setting used for MCA-style diagnostics, not an IEEE fp32 run.
13. If Chapter 7 is deleted, merged, or heavily compressed, update the Chapter 1
   roadmap so the report structure remains accurate.

## Front Matter

### Word Count Declaration

Supervisor issue:

- Draft 2 contained instruction-like TODO text.

Required action:

- Replace placeholder text with a formal word-count declaration using the final
  Overleaf counted-text value.
- Do not include instructions about how to fill the value in the submitted
  manuscript.

Current status:

- `WordCount/wordcount.tex` still needs a final non-directive version.

### Abstract

Supervisor issue:

- Draft 2 contained instruction-like TODO text.

Required action:

- Write the abstract last, after Chapters 3-7 are stable.
- Include bounded quantitative claims only; do not leave drafting instructions
  in the file.

Current status:

- `Abstract/abstract.tex` still needs a final abstract.

## Chapter 1: Introduction

### 1.1 Context and Motivation

Supervisor issue:

- Add background on why compressible Euler equations are solved.
- Give applications and the need for simulations to be fast but accurate enough
  to compare with experiments or benchmark references.
- Connect this to the question of how much numerical precision is needed.

Required action:

- Start from compressible flows with shocks/contact waves and practical
  simulation constraints.
- Introduce the speed/accuracy tradeoff before discussing fp32/fp64 and GPU
  hardware.

Current status:

- Current Chapter 1 is not yet drafted; this must be included in the first
  writing pass.

### 1.2 Precision and Hardware Reproducibility Problem

Supervisor issue:

- Add background and existing work on finite-precision and mixed-precision use
  in CFD solutions.
- Identify papers or codes where this has been done, and state limitations of
  the existing work.

Required action:

- Add a compact CFD/HRSC-focused precision literature paragraph.
- General floating-point references are not enough. Do not present linear
  algebra mixed-precision claims as CFD conclusions.

Current status:

- Add this to Chapter 1 or Chapter 2.4 depending on final word budget.

### 1.3 CUDA and GPU Background

Supervisor issue:

- Mention CUDA/GPUs and give background on different precision performance.
- Mention that fp32/fp64 performance can vary significantly across GPUs, even
  between cards from similar generations.

Required action:

- Define CUDA as the NVIDIA GPU programming model used for this project.
- Explain that GPU precision throughput and device math behaviour motivate
  measurement rather than assumption.
- Any specific hardware-family comparison needs a source.

Current status:

- Not yet covered in current Chapter 1.

### 1.4 Report Roadmap

Supervisor issue:

- Avoid internal planning phrasing such as "Chapter 4 is the owner of ...".

Required action:

- Use ordinary report language: "Chapter 4 defines the experimental design used
  in Chapter 5."

## Chapter 2: Background and Literature Context

### 2.1 Compressible Euler Equations

Supervisor issue:

- Define `\gamma`.
- Explain how pressure `p` and total energy `E` are related.

Required action:

- Define `\gamma` as the ratio of specific heats.
- State `E = rho e + 1/2 rho (u^2 + v^2)` and
  `p = (gamma - 1) rho e`, or the equivalent closure.

Current status:

- Must be added when Chapter 2 is drafted.

### 2.2 Ideal-MHD Project Context

Supervisor issue:

- Give ideal-MHD equations rather than only a verbal description.
- Explain what `div B = 0` means and why preserving it matters.

Required action:

- Include a compact ideal-MHD equation block or tightly written conservation
  form.
- Explain that `nabla dot B = 0` is the solenoidal magnetic-field constraint;
  numerical divergence errors can contaminate magnetic forces and wave
  propagation.
- Keep the boundary clear: Report 1 does not validate MHD.

Current status:

- The outline should treat the MHD equation block as required, not optional.

### 2.3 HRSC and Benchmark Literature

Supervisor issue:

- Some Draft 2 material summarised Chapter 3 or test-case descriptions.
- Do not use HLLC before defining or referencing it.
- Put detailed Toro/Liska-Wendroff test descriptions near the experimental
  design or results, not in the background literature section.

Required action:

- Keep Chapter 2.3 focused on literature context: finite-volume methods,
  Godunov-type HRSC schemes, Riemann solvers, and standard benchmark role.
- Move case-specific statements to Chapter 4 or Chapter 5.

Current status:

- Apply during Chapter 2 drafting and Chapter 3/4 planning.

### 2.4 Floating-Point Arithmetic and Reproducibility

Supervisor issue:

- Mention exponent ranges as well as significand length.
- Define unit roundoff.
- Make the "practical design question" explicit.
- Do not discuss linear algebra-specific content when the reference is from
  linear algebra; use only transferable points.
- Non-associativity can change more than the last few digits.
- Relate `-Ofast` to `-O3`; reordering is not allowed in the same way under
  normal `-O3`.
- Mention affected operations such as reciprocal and square root.

Required action:

- Give binary32/binary64 significand and exponent range.
- Define unit roundoff.
- Define Verificarlo and MCA early enough that Chapter 4/5/6 can use them
  without stopping to introduce them.
- State explicitly that Verificarlo `p32` is not IEEE binary32/fp32; it is a
  virtual mantissa precision used in MCA diagnostics.
- Include the supervisor's example in prose or equivalent:
  `(1e-18 + 1) - 1` versus `1e-18 + (1 - 1)`.
- Explain that `-Ofast`/fast-math can permit reassociation and approximations
  that are not allowed under stricter optimisation.
- Make the design question concrete: which variables, regions, operations, and
  compiler/device settings can be reduced or relaxed without exceeding the
  discretisation/reference error scale?

Current status:

- Add explicit items to Chapter 2.4 prompt before drafting.

### 2.5 Report 1 Gap

Supervisor issue:

- Not directly named, but feedback implies the gap needs clearer connection to
  the background literature.

Required action:

- End Chapter 2 with a short gap statement connecting HRSC methods, CFD
  finite-precision work, and this report's Euler precision/hardware evidence.

Current status:

- Current `Chapter2/chapter2.tex` may need a 2.5 section placeholder.

## Chapter 3: Numerical Method

### 3.1 Finite-Volume Update

Supervisor issue:

- Define the CFL constraint earlier.
- Number all displayed equations, not only equations explicitly cited.

Required action:

- Move or preview the CFL time-step dependence in Section 3.1.
- Number major displayed equations: compact Euler form, fluxes, cell average,
  numerical flux, finite-volume update, and CFL relation.
- Cite the finite-volume/Godunov background using author-name prose where the
  text is introducing a specific method or source tradition.

Current status:

- Current Chapter 3 still only numbers selected equations; needs a numbering
  pass.

### 3.2 MUSCL-Hancock Reconstruction and Limiting

Supervisor issue:

- Explain why slope limiting is needed before using it.

Required action:

- Add a short explanation that unlimited reconstruction near shocks/contacts can
  create new extrema or oscillations.
- Define TVD at first use: Total Variation Diminishing. State the scalar
  intuition without claiming a full nonlinear Euler proof.
- Use author-name prose for van Leer/Toro-style method citations where
  applicable.

Current status:

- Current text partially covers limiting but should be strengthened.

### 3.3 HLLC and Rusanov Fluxes

Supervisor issue:

- "Vertical" is redundant.
- "Davis-style" wave-speed estimate needs a reference.
- The HLLC approximate-solution inequalities and flux-selection inequalities
  in Draft 2 used `<` and `<=` inconsistently, creating overlap/undefined
  boundary cases.

Required action:

- Replace "vertical interface" with "interface".
- Add or verify a Davis wave-speed reference before citing "Davis".
- Write HLLC branch conditions as mutually exclusive ordered cases, or explain
  that the implementation uses ordered branches and Section 3.5 tests the
  strict-inequality variant.
- Use author-name prose for Harten-Lax-van Leer, Toro-Spruce-Speares, and Davis
  when introducing those fluxes or wave-speed estimates.

Current status:

- Current Chapter 3 still needs this pass.

### 3.4 Stability, Limiting, and Positivity

Supervisor issue:

- The `max_ij max(nu_x, nu_y) <= C_CFL` statement was not equivalent to the
  preceding formula.
- Define TVD.

Required action:

- Use an unambiguous CFL formula, e.g.
  `Delta t = C_CFL / max_ij max((|u|+c)/dx, (|v|+c)/dy)`,
  or the equivalent nested-minimum form.
- Define `nu_x` and `nu_y` only after the time-step formula makes the bound
  direct.

Current status:

- Needs correction.

### 3.5 Precision-Sensitive Decision Points

Supervisor issue:

- Replace "well resolved in binary64 can lose accuracy in binary32" with
  "sufficiently accurate in binary64, but insufficiently so in binary32".
- FMA accuracy and behaviour depend on hardware/compiler choices.
- Explain `RIEMANN_STRICT_INEQUALITY`, `STRICT_IEEE`, and `FAST_MATH`, with
  code examples if useful.
- Increase spacing in Table 3.1.

Required action:

- Add short code-like examples for the branch-rule macro and the strict/fast
  precision-control switches.
- Explain strict flags and fast-math flags at report level, preferably as a
  listing/table rather than a long sentence.
- Add table row spacing with `\addlinespace` or `\arraystretch`.
- Consider adding an "exact Riemann solver tolerances" entry if it remains a
  conceptual axis in the outline.

Current status:

- Current Chapter 3 explains some concepts but lacks code examples and table
  spacing.

### 3.6 Extension to Ideal MHD

Supervisor issue:

- Expand to a similar level of conceptual detail as Euler.
- Define wave speeds and describe the divergence-cleaning extra equation.

Required action:

- Add compact fast/slow magnetosonic speed context or formula.
- Describe Dedner-type cleaning with scalar `psi` and its role in advecting and
  damping divergence errors.
- Keep the evidence boundary: MHD is project context and future work, not a
  Report 1 validation result.

Current status:

- Current Chapter 3 needs more detail, but word budget must be protected.

## Chapter 4: Implementation and Experimental Design

### Chapter-Level Caution: CFL Reduction

Supervisor issue:

- Reduction ordering for CFL should not be framed as finite-precision summation
  sensitivity because CFL uses min/max, not a sum.

Required action:

- State that CFL selection is a deterministic max/min comparison, not the same
  class as summation-order sensitivity.

### 4.1 Implementation Route

Supervisor issue:

- AMReX does not need to be mentioned if not used.
- Give code examples of `FLOAT_PRECISION`.
- Reference or bound Boost::Multiprecision.
- Explain toolchain split and why some tests used WSL and some Windows
  BuildTools; ideally use the same compiler for all tests.

Required action:

- Delete AMReX or compress it to one non-essential context sentence.
- Add a short CMake/C++ snippet showing `-DFLOAT_PRECISION=float/double` mapped
  to `HRSC_REAL`. Also show `ENABLE_CUDA` if this is the clearest place to
  define the backend switch.
- If Boost::Multiprecision is mentioned, state that it is out of Report 1
  evidence scope unless actually used.
- If no same-toolchain rerun is done, downgrade all CPU/GPU wording to
  "within-case matched binary evidence" and repeat the toolchain limitation in
  Chapters 4, 5, and 7.
- Replace vague "toolchain split" phrasing with a plain statement: Toro3/Toro5
  use Windows BuildTools, while Sod/LW3/LW12 use Linux/WSL; each CPU/GPU
  comparison is made within one matched binary/configuration.

Current status:

- Current Chapter 4 partially satisfies this but lacks code example and
  toolchain explanation.

### 4.2 Algorithmic Structure

Supervisor issue:

- Do not refer assessors directly to source-code paths.
- Define CUDA, thread blocks, OpenMP schedules, Verificarlo, and MCA.
- Some implementation details are academically irrelevant.

Required action:

- Replace source-path references with functional descriptions.
- Define CUDA as the NVIDIA GPU programming model/backend used here.
- Define thread blocks as GPU thread tiles and OpenMP static schedules as fixed
  CPU loop assignment.
- State that the CFL selection uses max/min comparisons, not summation
  reduction, and that deterministic selection is the relevant implementation
  property here.
- Introduce Verificarlo and MCA in Chapter 1 or 2; Chapter 4 can then refer
  back to that background.

Current status:

- Current Chapter 4 has improved but still has terms needing definitions.

### 4.3 Precision, Hardware, and Diagnostic Axes

Supervisor issue:

- Explain "matched device evidence".
- Explain compiler flags such as `-ffp-contract=off`.
- Section may be better as tables/axes plus equations rather than wordy prose.

Required action:

- Define matched device comparison as same case, same executable, same
  precision/configuration, changing only runtime device selection.
- Present compiler flags in a short listing or compact table, then add short
  meanings:
  - `-ffp-contract=off`: disables FMA contraction.
  - `-fno-fast-math`: prevents fast-math transformations.
  - `--fmad=false`: disables CUDA FMA contraction where applied.
  - `--ftz=false`: preserves subnormal values.
  - `--prec-div=true`, `--prec-sqrt=true`: request precise division/square root.
- Keep MCA explanation equation-led where possible.
- Cite Verificarlo/MCA using author-name prose where a specific tool or method
  is being introduced.

Current status:

- Needs definition and compression pass.

### 4.4 Test-Case Matrix and Metrics

Supervisor issue:

- Define SSIM.
- Explain what `R_ref` means when small or large.
- Add spacing/lines to table.
- Give Toro and Liska-Wendroff initial conditions here or in Chapter 5.
- Avoid "rows" before the reader has a clear table context.
- Explain how the N=800 fp64 reference is translated to lower resolution:
  cell-averaging, point sampling, or another method.

Required action:

- Define SSIM as an image-structure similarity score, with values near 1
  meaning closer structural agreement to the reference image.
- Define `R_ref = ||U_fp32 - U_fp64||_1 / ||U_fp64 - U_ref||_1`; values below
  1 mean precision gap is smaller than the reference/discretisation error,
  values near or above 1 mean it is comparable to or larger than that scale,
  and zero denominators are degenerate cases.
- Add table spacing.
- Add compact initial-condition table or prose for Toro3, Toro5, LW3, and LW12.
- State reference mapping: for LW12 N=800 to N=400/N=200, conserved variables
  are block-averaged over integer blocks (2x2 or 4x4) before primitive-variable
  norms/SSIM are computed, if this matches the evidence scripts.
- Also state the LW3 mapping if used: `1600 -> 400/200` uses `4x4/8x8` integer
  block averaging of conserved variables before primitive-variable metrics.
- Avoid oversized matrices set in very small font. Split the table, increase
  row spacing, or move detail to prose if readability suffers.

Current status:

- Current Chapter 4 has matrix and metrics but still lacks several definitions
  and the reference downsampling explanation.

## Chapter 5: Validation and Precision Results

### 5.1 Validation Overview

Supervisor issue:

- "Chapter 4 is the owner of ..." is unusual phrasing.

Current status:

- Mostly fixed in current Chapter 5. It now says Chapter 4 fixes the design
  matrix and Chapter 5 interprets measured outputs.

Remaining action:

- If Chapter 4 explains initial conditions and reference mapping, keep 5.1
  short. Do not reintroduce design-matrix rationale in Chapter 5.

### 5.2 One-Dimensional Euler Validation

Supervisor issue:

- Table 5.1 is useful, but the variable behind `L_1` is unclear.
- The paragraph before the table largely repeated numbers rather than
  interpreting them.
- Figures 5.1-5.3 should be larger.
- Put resolution and output times in captions rather than figure titles.
- Mention solver and Riemann solver.

Current status:

- Current prose interprets wave structure and reference scale better than
  Draft 2.
- Figure width is already large.
- Captions still need `N`, output time, MUSCL-Hancock, HLLC, and exact Riemann
  reference details.

Required action:

- Update captions for Sod, Toro3, and Toro5.
- Clarify table caption: `L_1` is on conservative state unless the density
  ratio is explicitly named.

### 5.3 Two-Dimensional Euler Validation

Supervisor issue:

- Table 5.2 needs more interpretation and probably fewer displayed digits.
- Schlieren plots should be black-and-white for comparison with literature.
- Captions should name the Riemann solver.

Current status:

- Current prose interprets LW3/LW12 structure and relative error scales.
- Table still uses many digits.
- Captions still omit solver/time details.

Required action:

- Round table values to 3-4 significant figures for readability.
- Add HLLC, grid, time, and reference details to captions.
- Check actual figure files for black-and-white schlieren suitability.
- Increase figure widths if the submitted PDF cannot be read without zooming.

### 5.4 Single- and Double-Precision Comparison

Supervisor issue:

- Add interpretation, especially for the LW12 density difference in the
  upper-right region.
- Explain how this relates to waves and precision-sensitive algorithmic parts,
  without overclaiming HLLC branch evidence.
- Figure 5.7 was washed out in Draft 2.

Current status:

- Current prose says the difference localises near the upper-right
  shock-interaction region.
- It still needs one cautious sentence linking that localisation to
  reconstructed states and HLLC wave-speed/flux decisions.

Required action:

- Add bounded interpretation: localisation suggests precision sensitivity where
  reconstructed states feed HLLC flux/wave-speed decisions; it does not prove a
  specific HLLC branch changed unless branch-count evidence is added.
- Check whether the heatmap colormap is clear enough in the generated PDF.

### 5.5 Matched CPU/GPU Comparison

Supervisor issue:

- All-zero tables have low information density.
- The no-difference result should be stated more succinctly.

Current status:

- Current C5 has better evidence boundaries and checkpoint wording.
- It still has two all-zero tables.

Required action:

- Compress final-time CPU/GPU evidence into a coverage table or a concise
  sentence plus footnote.
- Keep the toolchain split footnote and saved-output checkpoint boundary.
- Do not expand zero metrics into several prose sentences.
- Use "comparisons" or "entries" rather than "rows" unless referring to a
  specific table row.

### 5.6 Compiler, Branch, Solver, and Drift Sensitivity

Supervisor issue:

- If `L_1` and `L_infty` ranges are mentioned, give actual values for the
  different tests.
- Table 5.5 is confusing when it mixes 1D and 2D cases as ranges. Do not use a
  cross-case range table as the main evidence table.
- Figure 5.8 needs to be larger, at least about double the Draft 2 size. If
  density and pressure show the same structure, consider showing density only.
- Compiler flags should not be written as a long sentence. Use a code listing,
  code-like block, or compact flag table in Chapter 3/4, then refer back to it
  here.
- Figure 5.9 is useful because it shows no rapid divergence over the tested
  runtime, but the right-side labels are too small and overlapping labels make
  the visible curve count ambiguous.
- The best-fit slope table adds little. It should be removed from the main
  text, moved to an appendix/supplement only if needed, or replaced by a short
  qualitative ordering statement.
- Toro-123/Toro2 non-completion must not be explained mechanistically unless
  `dt` traces, intermediate outputs, or another diagnostic artifact is inspected.

Current status:

- Current fp32 compiler table gives per-case values.
- The CPU-fp64 variation table still uses ranges and mixes dimensions.
- The current drift-slope table remains in the main text.
- Current wording has removed the "Lyapunov-like" framing.
- The current text still contains an internal-style "P1 probe" label, which is
  not suitable manuscript prose.

Required action:

- Replace Table 5.5 with one of:
  - a single-case per-axis table for the case that changes most clearly;
  - separate 1D and 2D tables;
  - or a short text statement plus the actual values, if the evidence is not
    important enough for a table.
- Do not mix 1D and 2D results into one range unless the prose explicitly says
  this is only a coarse coverage statement and not a diagnostic comparison.
- Enlarge Figure 5.8 and consider density-only presentation if pressure repeats
  the same visual information.
- Remove the main-text drift-slope table unless it supports a claim that Figure
  5.9 cannot support.
- Enlarge or redesign Figure 5.9. Its caption must explain if multiple curves
  overlap exactly, so fewer curves are visually distinguishable than legend
  entries.
- Avoid internal evidence-priority labels such as "P1"; use "supplementary GPU
  flag probe" or a plain description.
- For Toro-123/Toro2 non-completion, either inspect existing logs or add a small
  diagnostic that records `dt`/intermediate outputs. If that is not done, write:
  "non-completion within the 600 s limit was observed; the mechanism was not
  diagnosed in Report 1."

## Chapter 6: Discussion

### 6.1 What the Results Show

Supervisor issue:

- Draft 2 Chapter 6 had a useful summary of the analysis approach.
- The current LaTeX Chapter 6 is not yet written to that standard.

Required action:

- Rebuild Chapter 6 as synthesis, not a second results chapter.
- Start from the validation scope and evidence design: which cases were tested,
  what references were used, and what precision/hardware axes were actually
  measured.
- Summarise the result pattern with bounded claims and specific numbers only
  where they change the conclusion.

Current status:

- `Chapter6/chapter6.tex` still needs a substantive discussion pass.

### 6.2 Precision Interpretation

Supervisor issue:

- Draft 2's summary was useful, but the report must explain how Verificarlo
  `p32` differs from IEEE fp32 before relying on that point.

Required action:

- State that IEEE fp32/fp64 experiments are direct binary-format comparisons,
  while Verificarlo `p8/p16/p32/p53` are virtual mantissa settings used for MCA
  diagnostics.
- Do not use `p32` results as proof that IEEE fp32 is or is not sufficient.
- Connect precision conclusions to reference-scaled error, localised LW12
  structure, strict/fast flags, and branch-rule sensitivity.

### 6.3 Hardware Interpretation

Supervisor issue:

- The CPU/GPU conclusion is acceptable only if the boundary is clear.

Required action:

- State that the saved-output CPU/GPU comparisons were bit-identical for the
  tested matched binaries/configurations.
- Preserve the toolchain split and checkpoint-boundary caveats.
- Do not generalise to all GPUs, all compilers, or unsaved intermediate states.

### 6.4 Limitations and Future Work

Supervisor issue:

- The limitation/future-work summary was useful but should be logically ordered.

Required action:

- Group limitations by evidence type: reference/discretisation limits,
  compiler/toolchain limits, diagnostic precision limits, runtime/non-completion
  limits, and MHD scope.
- Keep MHD as future work unless validated MHD evidence is added.
- If Toro-123/Toro2 non-completion remains undiagnosed, list it as a limitation,
  not as evidence for a specific mechanism.

## Chapter 7: Conclusion

Supervisor issue:

- Draft 2 Chapter 7 repeated Chapter 6 less clearly.
- The supervisor suggested removing Chapter 7 entirely unless it has a distinct
  function.

Required action:

- Preferred route: merge the conclusion into the end of Chapter 6 and delete or
  disable a separate Chapter 7 if the template/report structure allows it.
- If a separate Chapter 7 is retained, compress it to roughly 150-220 words and
  make it do only three things:
  - answer the report question in one bounded paragraph;
  - give two or three evidence-backed findings;
  - state the immediate future-work boundary, especially MHD.
- Do not repeat mechanism explanations, tables, or detailed numeric discussion
  from Chapter 6.
- If Chapter 7 is removed or shortened, update the Chapter 1 roadmap.

Current status:

- Current Chapter 7 should be treated as high-risk for repetition until Chapter
  6 is rebuilt.

## References

Supervisor issue:

- Protect capitalization in BibTeX titles, e.g. `{HLL}` rather than `HLL`.
- In manuscript prose, use author names for specific methods and benchmark
  problems where that improves readability.

Required action:

- Run a BibTeX capitalization pass over `References/references.bib`.
- Protect important technical strings in titles/booktitles:
  `{HLL}`, `{HLLC}`, `{GPU}`, `{CUDA}`, `{MHD}`, `{IEEE}`, `{AMReX}`,
  `{MUSCL-Hancock}`, `{1D}`, `{2D}`, `{Euler}`, `{Verificarlo}`.
- Do not change citation set unless a chapter edit introduces or removes a
  citation.
- In Chapters 1-5, prefer prose forms such as "Sod's shock-tube problem",
  "Toro's exact Riemann solver/test cases", "Liska and Wendroff's
  configurations", "Harten, Lax, and van Leer's flux", and "Denis et al.'s
  Verificarlo" when introducing those specific sources.

Known candidates:

- `liska_wendroff_2003`: protect `{1D}`, `{2D}`, `{Euler}`.
- `toro_spruce_speares_1994`: protect `{HLL}`.
- `bard_dorelli_2014`: protect `{GPU}` and `{MUSCL-Hancock}` if present in
  title.
- `zhang_etal_2019`: protect `{AMReX}`.
- `ieee754_2019`: protect `{IEEE}`.
- `denis_etal_2016`: protect `{Verificarlo}`, `{IEEE}`, and `{ARITH}` if
  present in title/booktitle.

## Recommended Execution Order

1. Apply the urgent Chapter 5 readability and evidence-boundary fixes:
   - 5.2 captions and 1D metric clarity;
   - 5.3 significant figures, captions, and 2D figure sizing;
   - 5.4 LW12 upper-right interpretation and heatmap sizing;
   - 5.5 zero-table compression;
   - 5.6 Table 5.5 replacement, Figure 5.8/Figure 5.9 readability, removal or
     demotion of the drift-slope table, and Toro-123/Toro2 limitation wording.
2. Run the BibTeX capitalization pass and a prose-citation pass for author-name
   method/test citations.
3. Update Chapter 4 dispatch prompt and then revise Chapter 4, because Chapter
   5 depends on Ch4 for flags, matched-device definitions, metrics, and
   reference mapping.
4. Update Chapter 3 dispatch prompt and then revise Chapter 3, especially
   HLLC branch conditions, CFL definition, numbered equations, and code-like
   precision-sensitive switches.
5. Update Chapter 2 dispatch prompt with the supervisor requirements, then
   draft/revise Chapter 2. Include the required ideal-MHD equation block and
   the Verificarlo/MCA/p32 distinction.
6. Draft Chapter 1 using the added applications, CFD precision literature, and
   CUDA/GPU background requirements. Keep the roadmap consistent with the final
   Chapter 6/7 decision.
7. Rebuild Chapter 6 as synthesis and decide whether Chapter 7 should be
   removed, merged, or compressed.
8. Replace front matter placeholders and write the abstract last.

## Suggested Next Subagent Split

Use these scopes for the next writing window. Each worker should edit only its
assigned section and should not touch raw experiment artifacts.

1. C5 Worker A: revise 5.2 captions and the 1D table caption so resolution,
   output time, MUSCL-Hancock, HLLC, exact reference, and conservative-state
   metric definition are explicit.
2. C5 Worker B: revise 5.3 values/captions/figure widths; round table values to
   3-4 significant figures and ensure 2D schlieren plots are readable.
3. C5 Worker C: revise 5.4 heatmap interpretation and sizing; add the bounded
   statement that localisation suggests sensitivity where reconstructed states
   feed HLLC wave-speed/flux decisions, but does not prove a branch change.
4. C5 Worker D: compress 5.5 CPU/GPU all-zero evidence while preserving the
   matched-binary and saved-output caveats.
5. C5 Worker E: rewrite 5.6 variation evidence by replacing the range table,
   removing internal labels such as "P1", and referring to a flag listing in
   Chapter 3/4 rather than writing flag sequences in prose.
6. C5 Worker F: rewrite 5.6 drift/non-completion discussion by deleting or
   demoting the slope table, enlarging or redesigning Figure 5.9, explaining
   overlapping curves, and using limitation wording for Toro-123/Toro2 unless a
   `dt`/intermediate-output diagnostic is added.
7. References Worker: protect BibTeX capitalization and adjust manuscript
   citations to author-name prose where the text introduces specific methods or
   benchmark problems.
8. C3/C4 Planning Worker: update `chapter3_dispatch_prompt.md` and
   `chapter4_dispatch_prompt.md` with the new supervisor constraints before any
   full rewrite.

## Verification Checklist for Future Agents

Before claiming a chapter satisfies the supervisor feedback:

- Search for manuscript-facing TODO or LLM-directive text.
- Search for excessive "rows" usage and replace where possible.
- Search for internal labels such as `week7`, `week8`, `D1`, `D2`,
  `HLLC-fill`, `config12`, `P1`, and `USE_GPU`.
- Search for `p32` and confirm each use distinguishes it from IEEE fp32.
- Confirm key terms are defined before first use.
- Confirm every table has prose interpretation, not just repeated numbers.
- Confirm captions include enough metadata for standalone reading.
- Confirm plots are readable in the compiled PDF without zooming.
- Confirm compiler flags appear as a listing/table/code-like block rather than
  a long sentence.
- Compile with:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

- If citations changed, run `bibtex thesis` and rerun `pdflatex` twice.
