# Review 4 — Phase 2.5 Residual AI-tone Polish

**Date:** 2026-05-27 (executed 2026-05-28)
**Pre-Phase-2.5 body count:** 7858
**Post-Phase-2.5 body count:** 7859
**Net delta:** +1 word
**Budget:** net-neutral (±20 words) — PASS
**Hard cap:** 7875 — PASS (7859 ≤ 7875)
**Build:** `pdflatex -interaction=nonstopmode thesis.tex` → exit 0, no Fatal, no new undefined refs

## Per-chapter findings

### Abstract
- PASSES CLEAN. Checked: sentence-length variation (mix of short/long present:
  "Three findings stand out." opens with 4-word sentence followed by 23-word
  follow-up; final paragraph mixes 13- and 28-word sentences). Subjects
  explicit throughout (matched comparisons, direct fp32/fp64 differences,
  implementation sensitivity). No hedge stacking. No tonal whiplash.

### Chapter 1
- chapter1.tex:7 | subject-drift | "Each consumer runs design loops or
  operating-envelope sweeps that need fast and accurate solutions." →
  "Every one of these users runs design loops or operating-envelope sweeps
  that need fast, accurate solutions." (replace vague "consumer" with concrete
  back-reference to the listed application domains)
- chapter1.tex:21 | rhythm-flatness | Three flat 15–22 word sentences in a row
  in §"Precision and Hardware Reproducibility Problem" — merged "Two runs
  may use the same reconstruction... They can still differ because..." into
  one connected sentence using "yet still" while flipping the opener to
  active form ("the finite-volume algorithm alone does not guarantee
  reproducibility").

### Chapter 2
- chapter2.tex:141 | subject-drift | "this is a local scale, not a
  solution-error bound..." → "the roundoff bound is a local scale, not a
  solution-error bound..." ("this" had a unit-roundoff antecedent two
  clauses back; naming the subject removes the ambiguity)
- chapter2.tex:205 | rhythm-flatness + predictable-pattern | "It replaces
  individual floating-point operations with instrumented variants at compile
  time. The resulting instrumented binary can probe rounding sensitivity
  without touching the application source." → "It swaps individual
  floating-point operations for instrumented variants at compile time, and
  the resulting binary can probe rounding sensitivity without touching
  application source." (merged two flat 17-/15-word sentences; swapped
  "replaces" → "swaps" for plain register; dropped redundant
  "instrumented" on second mention)

### Chapter 3
- chapter3.tex:434 | hedge-stacking | "may only affect results when one of
  the computed wave speeds is very close to zero" → "affects results only
  when one of the computed wave speeds sits very close to zero" (dropped
  "may"; replaced "is" with plain-register "sits"; reordered "only" to
  scope the conditional rather than the verb)
- chapter3.tex:313 | rhythm-flatness | "...comparison in Chapter~5 therefore
  isolates the contact-resolving path rather than ranking accuracy." →
  "...isolates the contact-resolving path; it does not rank accuracy."
  (semicolon split adds a 6-word short sentence to break the 18-word
  pattern that dominated the preceding lines)

### Chapter 4
- chapter4.tex:41 | rhythm-flatness + predictable-pattern | "The executable
  reads the configuration, selects the initial condition, boundary modes,
  flux solver, and device. It then dispatches to the CPU solver..." → "The
  executable reads the configuration and picks up the initial condition,
  boundary modes, flux solver, and device, then dispatches to the CPU
  solver..." (merged a flat 18-word list-sentence with the dispatch
  sentence; injected plain-register verb "picks up")

### Chapter 5
- chapter5.tex:273 | tonal-whiplash | "Three matched-binary properties make
  this absence of saved-state divergence expected:" → "Three matched-binary
  properties make the absence of saved-state divergence expected:"
  ("this absence" felt bureaucratic; "the absence" is cleaner antecedent
  to the just-stated zero result). Also tightened "listed in the table" →
  "in the table" (3 words).
- chapter5.tex:322 | rhythm-flatness | "The zero O2--O3 comparison shows
  that changing optimisation level alone did not alter the saved final
  state..." → "O2 versus O3 is bit-identical: changing optimisation level
  alone did not alter the saved final state..." (replaced predictable
  "The X shows that Y" opener with a 5-word punchy subject + colon, then
  the explanation; introduces sentence-length variation into a paragraph
  that was otherwise 22/24/19 words)

### Chapter 6
- chapter6.tex:69 | subject-drift | "These results do not establish
  equality of all intermediate stage values..." → "The matched table does
  not establish equality of all intermediate stage values..." ("These
  results" was a vague back-reference; "The matched table" names the
  Table~\ref{tab:ch5-cpu-gpu} subject explicitly, matching the previous
  sentence's "(Table~\ref{tab:ch5-cpu-gpu})")
- chapter6.tex:71 | rhythm-flatness | "Branch-rule entries test an
  implementation choice whose effect is smaller or absent in completed
  comparisons. The branch-rule axis is method variation." → "...comparisons,
  so the branch-rule axis is method variation." (merged two short flat
  sentences with a real connective rather than two flat declaratives; one
  fewer mini-paragraph break in flat-rhythm territory)

### Chapter 7
- chapter7.tex:12 | rhythm-flatness | "Together these findings give a
  bounded Euler baseline. The later precision and hardware study builds on
  it." → "Together these findings give a bounded Euler baseline on which
  the later precision and hardware study builds." (merged two short
  sentences into one ~20-word sentence; removes flat
  short-short-short rhythm that closed §"Key Findings"; cleaner antecedent
  than "it" pointing back at "baseline")

## Summary

- Flags found and addressed: 11 across Ch1-Ch7 (Abstract passes clean)
- Net delta: +1 word (well within ±20 budget)
- Final body count: 7859 / 7875 cap (16 words headroom)
- pdflatex build: clean, exit 0
