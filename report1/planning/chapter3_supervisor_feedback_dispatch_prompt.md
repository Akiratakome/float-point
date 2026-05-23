# Chapter 3 Supervisor-Feedback Execution Prompt

This prompt is for the next writing window after the Chapter 4 supervisor
feedback work. It follows the workflow style of
`report1/planning/chapter4_supervisor_feedback_dispatch_prompt.md` and
`report1/planning/chapter5_supervisor_feedback_dispatch_prompt.md`, but the
content requirements come from the supervisor-feedback map and the current
Chapter 3 text.

This is not a content plan based on archived prompts. Older plans under
`report1/planning/old/chapter3_dispatch_prompt.md` are archival only.

---

## Master prompt

You are the main agent for a supervisor-feedback revision of Report 1 Chapter 3.
Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

This round revises only Chapter 3, "Numerical Method". The actionable
requirements come from:

```text
report1/planning/supervisor_feedback_map.md
```

The original supervisor guide is:

```text
report1/planning/supervisorguide.md
```

Use the supervisor guide only to resolve ambiguity in the map. Do not use
`report1/planning/old/` as a content source.

### Required reading

Read these files before dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/planning/reportagents.md`
5. `report1/planning/manuscript_outline.md`
6. `report1/planning/supervisor_feedback_map.md`
7. `report1/planning/supervisorguide.md`
8. `report1/references/reference.md`
9. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
10. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
11. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
12. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`
13. `report1/phd-thesis-template-2.4/References/references.bib`

Read these implementation files only to support Chapter 3 claims, not to cite
source paths in the manuscript:

- `src/euler/hancock.hpp`
- `src/euler/muscl.hpp`
- `src/euler/hllc.hpp`
- `src/euler/rusanov.hpp`
- `src/euler/euler_solver.cpp`
- `cmake/CompilerFlags.cmake`
- `cmake/PrecisionConfig.cmake`
- `CMakeLists.txt`

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison.

Read these style skills before any manuscript prose is edited, and reread them
before final prose review:

```text
report1/skills/scientific-writing-duke/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/academic-english-style/SKILL.md
```

Use `scientific-writing-duke` for the method-derivation paragraphs, then
`academic-english-style` for hedging and sentence control, and finally
`avoiding-ai-flavor` as a paragraph-level acceptance gate.

Optional companion skills, lazy-loaded only if needed:

- `report1/skills/report1-context/SKILL.md` — load before §3.6 if the
  worker needs help keeping the MHD bridge within the Report 1 evidence
  boundary.
- `report1/skills/editing-academic-prose/SKILL.md` — load only in the
  main-agent integration pass for final-edit polish, not in worker
  drafting.

`report1/skills/writing-introduction/`, `writing-literature-review/`,
`writing-conclusion/`, and `source-notes/` are not used in this round
because Chapter 3 is method derivation, not introduction, literature,
conclusion, or source-mapping work.

### Main-agent role

The main agent must not directly rewrite Chapter 3 prose. Its role is:

- read the required context;
- identify current section boundaries and risks;
- dispatch one subagent per section, serially;
- review each returned section before dispatching the next worker;
- if a section fails the requirements, send it back to the same worker or a new
  worker with a focused repair prompt;
- maintain chapter-level continuity notes between workers;
- run the final three-round self-check and compile verification.

The main agent may make only mechanical non-prose changes if needed for
integration, such as preserving section markers after a worker edit, adding a
single missing BibTeX entry that workers have flagged (after verifying the
primary source via `report1/references/reference.md`), or running the global
equation-numbering pass described below. Any substantive prose, table,
algorithm, or new equation derivation change must be made by a section-scoped
worker.

Tell every worker:

```text
You are not alone in the codebase; do not revert or overwrite edits outside your assigned Chapter 3 section.
```

Workers run serially. Never allow two workers to edit `chapter3.tex` at the
same time.

### Current Chapter 3 section markers

Use the actual current markers:

```latex
% <<SECTION_1_BEGIN>>  ... % <<SECTION_1_END>>   (3.1 Finite-Volume Update)
% <<SECTION_2_BEGIN>>  ... % <<SECTION_2_END>>   (3.2 MUSCL-Hancock Reconstruction and Predictor Step)
% <<SECTION_3_BEGIN>>  ... % <<SECTION_3_END>>   (3.3 HLLC and Rusanov Fluxes)
% <<SECTION_4_BEGIN>>  ... % <<SECTION_4_END>>   (3.4 Stability, Limiting, and Positivity)
% <<SECTION_5_BEGIN>>  ... % <<SECTION_5_END>>   (3.5 Precision-Sensitive Decision Points)
% <<SECTION_6_BEGIN>>  ... % <<SECTION_6_END>>   (3.6 Extension to Ideal MHD)
```

Do not remove or rename these markers. Do not add new top-level `\section{}`
commands; section headings already live outside the worker regions.

### Chapter 3 ownership

Chapter 3 owns numerical-method theory only:

- finite-volume conservative update and CFL relation;
- MUSCL-Hancock reconstruction, slope limiting, and Hancock predictor;
- HLLC and Rusanov interface fluxes, including the wave-speed branch rule;
- stability, limiter role, and admissibility framing;
- precision-sensitive algorithmic decision points (branch rule, FMA, compiler
  flags) at *method* level;
- the conceptual extension to ideal MHD.

Chapter 3 must not:

- describe the implementation route, build flags table, or design matrix;
  these are Chapter 4;
- present Chapter 5 measured results as if they were method conclusions;
- cite source paths or claim implementation properties that Chapter 4 already
  owns;
- introduce the experimental matrix, SSIM, `R_ref`, or CPU/GPU coverage
  tables;
- describe Verificarlo `p32` as IEEE fp32, or as the fp32 axis of the report;
- claim MHD validation.

### Project-brief compliance mapping (Mathematical Theory [20%])

Chapter 3 is the chapter that satisfies the brief's Mathematical Theory
[20%] sub-bullets. Workers must ensure these three bullets remain visibly
covered:

| Brief sub-bullet | Required Chapter 3 location |
|---|---|
| (a) Description of the chosen explicit method (MUSCL-Hancock or WAF; must be Riemann-solver based). | §3.1 (finite-volume update), §3.2 (MUSCL-Hancock reconstruction and Hancock predictor), §3.3 (HLLC as the chosen Riemann solver; Rusanov as comparator). WAF may be named in §3.2 as another brief-approved Riemann-solver-based option only; it is not the report's method. |
| (b) MHD-specific numerical variations (different Riemann solvers, divergence cleaning). | §3.6 (ideal-MHD wave families, Dedner-style hyperbolic divergence cleaning, Evans-Hawley constrained transport, GPU MUSCL-Hancock context). |
| (c) Brief summary of algorithm points that could be varied (`<` vs `<=` or others). | §3.5 (precision-sensitive decision points, including HLLC branch rule, FMA, compiler-flag macros, and concept-only axes: exact-Riemann tolerances, limiter choice, parallel reduction ordering, CPU architecture / `-mtune`, MPI/OpenMP thread count). |

The brief also requires the explicit caveat that simple Riemann-solver
changes such as `<` vs `<=` "may only affect results when wave-speeds are
very close to zero". This caveat must remain in §3.5 prose.

Working word target: keep Chapter 3 inside the outline range of 1,200-1,350
Overleaf-counted words. The current `texcount -inc` reports 1,399 prose words,
so the chapter starts about 50 words above the hard upper. Workers expanding
§3.6 (Section 6) must be matched by compression in §3.5 (Section 5, currently
~355 words) so the chapter total moves back into the 1,200-1,350 range. Tables
and figure captions remain outside the controlling Overleaf count but still
need to be readable in the compiled PDF.

Section-level word-budget guardrails (counted words inside the marker region,
prose only):

- §3.1 may add at most ~15 words for the CFL preview sentence;
- §3.2 may add at most ~25 words for the "why limiting is needed" sentence and
  the TVD definition at first use;
- §3.3 should stay within its current ~225-word envelope while replacing
  "vertical interface" and rewriting the branch conditions;
- §3.4 should stay within its current envelope; do not re-derive material that
  has moved to §3.1;
- §3.5 is the compression target: aim for 260-290 prose words after the
  rewrite, even with the new code-like macro listing/table;
- §3.6 is the expansion target: aim for 195-225 prose words to reach
  Euler-comparable conceptual depth without making MHD look validated.

Numerical reconciliation for the chapter total (starting from the current
section counts 157 / 179 / 226 / 281 / 355 / 173 = 1,371):

- §3.1 add ≤ 15  →  ≈ 172
- §3.2 add ≤ 25  →  ≈ 204
- §3.3 net 0     →  ≈ 226
- §3.4 net 0 (compress only if needed during main-agent integration)
- §3.5 cut ~75   →  ≈ 280
- §3.6 add ~45   →  ≈ 218
- Projected total ≈ 1,328, inside the 1,200-1,350 window.

If §3.5 cannot reach 290 without losing the macro code-like fragments, main
agent must compress §3.4 by 20-40 words rather than allow §3.5 expansion.

### Hard rules

- Do not modify solver numerics, cfg defaults, experiment output formats, raw
  artifacts, or anything under `experiments/`.
- Do not change evidence artifacts to make the writing easier.
- Do not use manuscript-facing internal labels: `week7`, `week8`, `week9`,
  `D1`, `D2`, `HLLC-fill`, `config12`, `LW12/config12`, `P1`, or `USE_GPU`.
- Use `ENABLE_CUDA`, not `USE_GPU`; use `STRICT_IEEE`, `FAST_MATH`,
  `RIEMANN_STRICT_INEQUALITY` with this exact spelling for the implementation
  macros.
- Verificarlo virtual mantissa settings (`p8/p16/p32/p53`) belong to Chapter
  2/4; Chapter 3 should not introduce them. If §3.5 needs to refer to MCA at
  all, it does so by name only and points forward to Chapter 4.
- Replace "vertical interface" with "interface" in §3.3.
- Replace "well resolved in binary64 can lose accuracy in binary32" wording,
  wherever it appears, with "sufficiently accurate in binary64 but
  insufficiently so in binary32". Search the chapter once before drafting; if
  the phrase has already been removed, record this in the worker summary.
- Every displayed equation in Chapter 3 must be numbered. Workers must add
  `\label{eq:ch3-...}` to each `\begin{equation}` and convert each `\[ ... \]`
  in their assigned section to an `equation` environment with a label, unless
  the displayed block is a `cases`/`aligned` group that is logically one
  equation already inside an `equation`. The main agent runs a global pass at
  the end to verify all displays are numbered.
- HLLC branch conditions must be either mutually exclusive ordered cases or
  written as an "ordered branch" implementation with a single explicit
  cross-reference to the strict-inequality variant in §3.5. Do not leave
  overlapping `\le ... \le` regions undefined at equality.
- Author-name prose is required where Chapter 3 introduces a specific
  scheme, solver, or estimate: van Leer's slope limiter, Harten, Lax, and
  van Leer's flux, Toro, Spruce, and Speares' HLLC, Davis's wave-speed
  estimate, Dedner et al.'s divergence cleaning, and Evans and Hawley's
  constrained transport.
- The current `References/references.bib` does not contain `davis_1988`.
  Worker C must therefore *default* to the Toro-textbook attribution route:
  introduce the bound as "the Davis-style wave-speed bound as presented by
  \citet{toro2009}" and cite `toro2009`. Worker C must not invent a
  `davis_1988` key, must not add a BibTeX entry, and must not stop with a
  "missing key" report unless the main agent has separately verified a
  primary-source citation against `report1/references/reference.md` and
  decided to add the entry. The default outcome of this round is the
  Toro-attributed phrasing.
- TVD must be expanded at first use as "Total Variation Diminishing", with a
  one-sentence scalar intuition. Do not claim a full nonlinear Euler TVD
  proof.
- §3.5 must present `RIEMANN_STRICT_INEQUALITY`, `STRICT_IEEE`, and
  `FAST_MATH` as short code-like fragments or compact table entries, not as
  long sentences. Do not add `listings` or `minted` packages; use the
  template's existing `tabularx`/`tabular` environments with `\texttt{...}`
  cells, or short `verbatim`/inline `\texttt{...}` lines. Table 3.1 (or its
  successor) must use `\addlinespace`, `\renewcommand{\arraystretch}{1.16}`,
  or equivalent spacing so adjacent rows are visually separated.
- §3.6 must define MHD characteristic wave speeds at conceptual level (fast
  magnetosonic, Alfven, slow magnetosonic, contact/entropy) and describe
  Dedner-style hyperbolic divergence cleaning with the auxiliary scalar
  `\psi`, including its role in advecting and damping divergence errors. The
  section must still close with an explicit Report 1 evidence boundary:
  Report 1 does not validate MHD.
- AI-assisted prose must pass `avoiding-ai-flavor`: no generic filler, no
  marketing tone, no unsupported confidence, no template-like prose.

### Evidence and source context by worker

Workers should inspect only the evidence/source files relevant to their
section. If a required fact is not supported by a source the worker can read,
report the gap rather than inventing a detail.

| Worker | Required context |
|---|---|
| A, §3.1 finite-volume update | `supervisor_feedback_map.md` §3.1; current §3.1; `src/euler/euler_solver.cpp` only to confirm CFL preview wording matches §3.4 |
| B, §3.2 MUSCL-Hancock | `supervisor_feedback_map.md` §3.2; `src/euler/hancock.hpp`, `src/euler/muscl.hpp`; current §3.2 |
| C, §3.3 HLLC and Rusanov | `supervisor_feedback_map.md` §3.3; `src/euler/hllc.hpp`, `src/euler/rusanov.hpp`; current §3.3; `References/references.bib` for `toro_spruce_speares_1994`, `harten_lax_vanleer_1983`, and the Davis key check |
| D, §3.4 stability/limiting | `supervisor_feedback_map.md` §3.4; current §3.1 (to align CFL notation) and current §3.4 |
| E, §3.5 precision-sensitive points | `supervisor_feedback_map.md` §3.5; `src/euler/hllc.hpp` for the branch rule; `cmake/CompilerFlags.cmake`, `cmake/PrecisionConfig.cmake`, `CMakeLists.txt` for the strict/fast macros; current §3.5 |
| F, §3.6 MHD extension | `supervisor_feedback_map.md` §3.6; `References/references.bib` for `dedner_2002`, `evans_hawley_1988`, `bard_dorelli_2014`; current §3.6 |

### Allowed citation policy

`References/references.bib` is already populated. Workers may cite only
existing keys and only when the citation supports a sentence. For Chapter 3,
allowed keys are:

| key | use in Chapter 3 |
|-----|------------------|
| `toro2009` | finite-volume/MUSCL-Hancock/HLLC/exact-Riemann background |
| `leveque_2002` | finite-volume conservative update; stability framing |
| `vanleer_1979` | MUSCL slope limiting origin |
| `harten_lax_vanleer_1983` | HLL flux origin |
| `toro_spruce_speares_1994` | HLLC restoration of the contact wave |
| `davis_1988` | Davis wave-speed estimate (only if the key exists; otherwise see Hard Rules) |
| `dedner_2002` | hyperbolic divergence cleaning for ideal MHD |
| `evans_hawley_1988` | constrained-transport divergence control |
| `bard_dorelli_2014` | GPU MUSCL-Hancock context for MHD bridge |
| `ieee754_2019`, `goldberg_1991`, `higham_2002` | rounding model and FMA framing in §3.5 |

Workers may not invent citation keys or bibliography metadata. If a worker
needs a citation outside this list, it stops and reports the exact claim
needing support. Before Worker C and Worker F start, the main agent runs:

```powershell
rg -n -F '{davis_1988,' report1/phd-thesis-template-2.4/References/references.bib
rg -n -F '{evans_hawley_1988,' report1/phd-thesis-template-2.4/References/references.bib
rg -n -F '{dedner_2002,' report1/phd-thesis-template-2.4/References/references.bib
rg -n -F '{vanleer_1979,' report1/phd-thesis-template-2.4/References/references.bib
rg -n -F '{harten_lax_vanleer_1983,' report1/phd-thesis-template-2.4/References/references.bib
rg -n -F '{toro_spruce_speares_1994,' report1/phd-thesis-template-2.4/References/references.bib
```

(Verified at planning time: `davis_1988` is absent; Worker C must use the
Toro fallback. The other five keys are present in the current bib file.)

The main agent records each result and tells the corresponding worker which
keys are available. A worker may not cite a key that returned no match.

### Marker protocol and pre-step snapshot

Before dispatching any worker:

1. Snapshot the current `chapter3.tex` to a temporary file under the
   repository (for example `report1/phd-thesis-template-2.4/Chapter3/.snapshots/preR2.tex`,
   not committed) so that a failed worker edit can be reverted byte-for-byte.
2. Confirm with `rg -n "% <<SECTION_[1-6]_(BEGIN|END)>>"
   report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` that exactly 12
   marker lines are present.
3. Dispatch Worker A only after the marker check passes.

Tell every worker this exact instruction, in addition to the assignment:

> Read the current `chapter3.tex` in full. Locate exactly your assigned
> markers `% <<SECTION_n_BEGIN>>` and `% <<SECTION_n_END>>`. Replace only
> the complete marker-bounded region, including the BEGIN and END marker
> lines. The new content must keep both marker lines verbatim at the start
> and end. Do not touch text outside those markers. Do not rename markers.
> Do not insert new `\section{}` commands; the section heading is already
> outside your region. If your assigned markers do not appear exactly once
> each, stop and report.

After each worker returns, the main agent verifies:

- all six BEGIN markers and all six END markers still exist exactly once;
- the other five marker-bounded regions are byte-identical to the snapshot;
- the worker's region begins with its BEGIN marker and ends with its END
  marker.

If any check fails, restore `chapter3.tex` from the snapshot and re-dispatch
that worker with a focused defect prompt.

---

## Worker A: §3.1 Finite-Volume Update

Assigned region:

```latex
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>
```

Goal:

- Preview the CFL constraint here, after the conservative update is written
  down, so the reader meets it before the predictor and HLLC sections need it.
  Add one short sentence such as: "The explicit time step is controlled by a
  Courant-Friedrichs-Lewy (CFL) condition on local acoustic wave speeds; the
  full formula is given in Section~\ref{sec:ch3-stability}." Use a forward
  cross-reference to §3.4 rather than restating the formula.
- Number every displayed equation in the section by converting `\[ ... \]`
  blocks to `equation` environments with descriptive labels. Suggested
  labels: `eq:ch3-euler-2d`, `eq:ch3-euler-fluxes`, `eq:ch3-fv-integral`,
  `eq:ch3-cell-average`, `eq:ch3-interface-flux`, `eq:ch3-fv-update` (this
  one already exists; keep its existing label `eq:fv-update` and reuse it
  when later sections cross-reference). Do not introduce duplicate labels.
- Use author-name prose for the finite-volume background: "the standard
  finite-volume treatment of \citet{toro2009} and \citet{leveque_2002}"
  rather than bare parenthetical citations.

Constraints:

- Do not move the CFL formula itself out of §3.4.
- Do not add a new figure or table here.
- Do not extend the section beyond the current envelope plus the ~15-word CFL
  preview sentence.

Worker summary must report:

- the exact CFL preview sentence used;
- the new equation labels added;
- any equation label that already existed and was reused.

---

## Worker B: §3.2 MUSCL-Hancock Reconstruction and Predictor Step

Assigned region:

```latex
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Goal:

- Open the section with a one- or two-sentence motivation for slope limiting:
  unlimited piecewise-linear reconstruction near shocks and contacts can
  create new local extrema or oscillations, so a limiter is used to suppress
  them while keeping second-order accuracy in smooth monotone regions. Place
  this before the minbee/minmod formula.
- Expand TVD at first use as "Total Variation Diminishing" with a single
  sentence of scalar intuition. Do not claim a full nonlinear Euler TVD
  proof.
- Use author-name prose for the limiter and predictor lineage: "van Leer's
  MUSCL framework~\citep{vanleer_1979}" and "Toro's presentation
  \citep{toro2009}" where appropriate.
- If WAF is mentioned at all, name it once as another brief-approved
  Riemann-solver-based explicit method that is not the report's path. Do
  not cite WAF beyond a textbook reference and do not present any
  WAF-specific algebra.
- Number every displayed equation in this section by converting `\[ ... \]`
  to numbered `equation` environments. Suggested labels:
  `eq:ch3-onesided-jumps`, `eq:ch3-minmod-sigma`, `eq:ch3-minmod-def`,
  `eq:ch3-limiter-ratio`, `eq:ch3-reconstructed-states`,
  `eq:ch3-hancock-half-step-L`, `eq:ch3-hancock-half-step-R`,
  `eq:ch3-riemann-input`.

Constraints:

- Do not introduce a new limiter not used by the implementation. Other
  limiters (van Leer, superbee) may remain mentioned as alternatives but are
  not the report's path.
- Do not insert source-code paths.
- Keep the section inside the working envelope: add at most ~25 words for
  the motivation/TVD sentences.

Worker summary must report:

- the exact wording used to motivate limiting;
- the TVD definition sentence;
- the list of new equation labels.

---

## Worker C: §3.3 HLLC and Rusanov Fluxes

Assigned region:

```latex
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>
```

Goal:

- Replace "vertical interface" with "interface".
- Use author-name prose for the HLL family and the Davis estimate: "the HLLC
  construction introduced by \citet{toro_spruce_speares_1994} and presented
  in \citet{toro2009}", "the two-wave HLL flux of
  \citet{harten_lax_vanleer_1983}", and either "Davis's wave-speed estimate
  \citep{davis_1988}" or, if `davis_1988` is missing from
  `References/references.bib`, "the Davis-style wave-speed bound as presented
  by \citet{toro2009}". Workers must not invent the Davis citation key.
- Rewrite the HLLC branch conditions so they are unambiguous at zero. Use one
  of these two patterns, not both:
  - mutually exclusive ordered cases on the sampled flux with no equality
    overlap, for example
    `\widehat F_{\mathrm{HLLC}}=F_L` for `S_L \ge 0`,
    `F_{\ast L}` for `S_L < 0 \le S_\ast`,
    `F_{\ast R}` for `S_\ast < 0 \le S_R`,
    `F_R` for `S_R < 0`; or
  - an explicit statement that the implementation uses ordered branches and
    that §3.5 tests the strict-inequality variant
    (`RIEMANN_STRICT_INEQUALITY`).
- Number every displayed equation in this section using an `equation`
  environment with a label, including the Riemann initial state, the
  wave-speed estimates, the HLLC sampled solution, the flux-selection cases,
  the star-state closure, and the Rusanov flux.
- Keep the existing TikZ HLLC fan figure if it is still required; do not
  enlarge or rewrite that figure.

Constraints:

- Do not change the algebra of `S_L`, `S_R`, `S_\ast`, `U_{\ast K}`, or the
  Rusanov flux.
- Do not delete the cross-reference to §3.5 at the end of the section; the
  precision-sensitive discussion lives there.
- Do not call this section "implementation"; it remains method theory.

Worker summary must report:

- whether "vertical" was removed;
- which Davis citation route was used (existing key, Toro-attributed, or
  reported gap);
- the exact ordered-branch wording or mutually exclusive cases used for the
  flux selection;
- the new equation labels.

---

## Worker D: §3.4 Stability, Limiting, and Positivity

Assigned region:

```latex
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Goal:

- Order the CFL development so that the time-step formula is given first and
  the per-cell Courant numbers `\nu_{x,ij}`, `\nu_{y,ij}` are introduced only
  after the formula makes the bound
  `\max_{ij}\max(\nu_{x,ij},\nu_{y,ij}) \le C_{\mathrm{CFL}}` direct.
- Ensure the CFL formula matches the wording previewed in §3.1 (the §3.1
  worker uses a one-sentence forward reference; this section owns the
  formula).
- Number every displayed equation in this section with `equation` labels:
  the Courant-number definitions, the time-step formula, the primitive
  positivity condition.
- Define TVD at first use in §3.4 if it appears here before §3.2 in the
  reading order; otherwise simply use it after §3.2's definition. Do not
  duplicate the definition.
- Use `\label{sec:ch3-stability}` on this section so §3.1's forward
  cross-reference resolves.

Constraints:

- Do not re-derive the finite-volume update; §3.1 owns that.
- Do not introduce per-cell CFL traces or actual measured CFL values;
  Chapter 5 owns measured behaviour.
- Do not claim a positivity proof for MUSCL-Hancock + HLLC; the section
  already treats positivity carefully and that language must remain.

Worker summary must report:

- the final equation ordering for CFL definitions;
- whether `\label{sec:ch3-stability}` is in place;
- new equation labels added.

---

## Worker E: §3.5 Precision-Sensitive Decision Points

Assigned region:

```latex
% <<SECTION_5_BEGIN>>
...
% <<SECTION_5_END>>
```

Goal:

- Compress the section from ~355 to 280-310 prose words while adding the
  supervisor-required code-like fragments for `RIEMANN_STRICT_INEQUALITY`,
  `STRICT_IEEE`, and `FAST_MATH`.
- Replace any "well resolved in binary64 can lose accuracy in binary32"
  phrasing with "sufficiently accurate in binary64 but insufficiently so in
  binary32". Search the section before drafting.
- State explicitly that FMA accuracy and behaviour depend on hardware and
  compiler choices; a CPU FMA typically uses a higher-precision intermediate
  while a GPU FMA stays at the same precision throughout. Cite
  `ieee754_2019` and `higham_2002` only where the sentence directly needs
  them.
- Present the three macros as a compact table or short code-like block. Two
  acceptable patterns:
  - a 3-row `tabularx` with columns "Macro", "Build effect", "Tested in", and
    `\texttt{RIEMANN\_STRICT\_INEQUALITY}`,
    `\texttt{STRICT\_IEEE}`, `\texttt{FAST\_MATH}` in the rows; or
  - a `verbatim`/short `\texttt{...}` listing with one line per macro and a
    one-sentence explanation following it.
- Apply visible row spacing to Table 3.1 (or its successor table) using
  `\addlinespace` between rows and/or
  `\renewcommand{\arraystretch}{1.16}` so adjacent rows are clearly
  separated.
- Number all remaining displayed equations (rounding model, `S_\ast`
  perturbation, branch test) using `equation` environments with labels.
- Keep the chapter scope: this is method-level precision sensitivity, not
  implementation routing (Chapter 4) and not measured drift (Chapter 5).
- Preserve the brief's near-zero caveat: HLLC `<` vs `<=` and similar
  simple Riemann-solver changes "may only affect results when wave-speeds
  are very close to zero". Use that wording, or an equivalent phrasing
  ("only matter when one of the computed wave speeds is close to zero"),
  in §3.5 prose.
- Cover the brief's variation list at concept level in one short paragraph
  or list. The paragraph must distinguish three groups:
  - measured in Report 1: HLLC branch rule (`<` vs `<=`), compiler flags
    (gcc `-O2`/`-O3`/`-Ofast` with `--use_fast_math`), HLLC vs Rusanov,
    fp32 vs fp64;
  - introduced as concept only in this report: exact-Riemann tolerances,
    limiter choice, parallel reduction order across CPU threads or GPU
    blocks;
  - flagged as Report 2 axes only: CPU architecture / `-mtune` / explicit
    vectorisation; explicit MPI/OpenMP thread-count variation;
    Boost::Multiprecision quad precision.
  Do not claim a measured result for any axis in the second or third
  group.

Constraints:

- Do not add `listings` or `minted` to the preamble. Use existing
  `tabular`/`tabularx`/`verbatim` constructs.
- Do not introduce Verificarlo `p32/p16/p8` here; Chapter 4 owns those.
- Do not state that fast-math, strict-IEEE, or the strict branch produced a
  specific final-state drift value; refer those numbers to Chapter 5.
- Keep at most one new table in this section; the existing
  `tab:method-decision-points` may be kept, replaced, or merged with the
  macro listing, but only one method-component table should remain.

Worker summary must report:

- the final §3.5 word count (worker-estimated);
- which presentation pattern was used for the macros;
- the table spacing setting applied;
- the list of new equation labels.

---

## Worker F: §3.6 Extension to Ideal MHD

Assigned region:

```latex
% <<SECTION_6_BEGIN>>
...
% <<SECTION_6_END>>
```

Goal:

- Bring §3.6 to a similar conceptual depth as the Euler treatment without
  turning it into an MHD validation section.
- Write a compact ideal-MHD equation block in conservation form, or, if the
  word budget is tight, name the additional fluxes in prose. The MHD
  conserved state must include `\rho`, `\rho \mathbf{u}`, `E`, and
  `\mathbf{B}`; the additional fluxes must include magnetic pressure,
  magnetic tension, and induction terms.
- Describe the characteristic wave families that distinguish MHD from Euler:
  fast magnetosonic, Alfven, slow magnetosonic, and the contact/entropy
  mode. Do not give full eigenstructure derivations; one or two sentences
  with author-name attribution to a standard reference is enough.
- Describe the `\nabla\cdot\mathbf{B}=0` solenoidal constraint and explain
  why preserving it matters at the discrete level (spurious magnetic forces
  and wave-speed contamination if violated).
- Present Dedner et al.'s hyperbolic divergence cleaning at conceptual
  level: introduce an auxiliary scalar `\psi` that couples to the
  induction equation so that the resulting `\psi`-`\nabla\cdot\mathbf{B}`
  system advects and damps divergence errors at a chosen wave speed.
  Worker F may write either the parabolic-hyperbolic form
  `\psi_t + c_h^2 \nabla\cdot\mathbf{B} = -\psi/\tau` paired with the
  modified induction equation containing `\nabla\psi`, or a one-sentence
  conceptual description without the full algebra, whichever fits the
  ~220-word budget. Cite `\citet{dedner_2002}` once. The report does not
  need full eigenstructure or damping-rate derivations.
- Mention Evans and Hawley's constrained transport as the alternative
  divergence-control family, citing `\citet{evans_hawley_1988}` once.
- Close with an explicit Report 1 boundary statement: the validated evidence
  in later chapters is for Euler tests; MHD is the project context for
  Report 2 and is not validated here. Reference
  `\citet{bard_dorelli_2014}` only if needed for the GPU MUSCL-Hancock
  bridge sentence; do not introduce new MHD citations.
- Number every displayed equation in the section (MHD equation block,
  divergence-cleaning extension) with `equation` labels.

Constraints:

- Do not state or imply that MHD has been implemented, validated, or
  numerically compared in Report 1.
- Do not exceed ~230 prose words after the expansion; this is conceptual
  context, not a method derivation chapter.
- Do not add a new figure unless it is essential; a small equation block is
  sufficient.

Worker summary must report:

- whether an explicit equation block or pure prose was used for the MHD
  equations;
- the exact divergence-cleaning equation written and the scalar variable
  symbol used;
- the new equation labels.

---

## Main-Agent Integration Review

After each worker:

1. Re-read only the edited section and one paragraph before/after it.
2. Check that the section satisfies its worker goals.
3. Check that the section does not duplicate Chapter 4 implementation
   description or Chapter 5 result claims.
4. If the section fails, dispatch a focused repair worker before continuing.
5. Record a short continuity note for the next worker.

After all workers:

1. Read the full Chapter 3 for flow and consistency.
2. Run a global equation-numbering pass: every `\[ ... \]` block outside the
   already-numbered `equation`/`align` environments must be either converted
   to a numbered `equation` environment with a label, or, in the rare case
   where numbering would clutter a nested `cases` listing, demoted to an
   intentional inline display with a comment explaining why no number is
   given. The default is "number it".
3. Confirm that the §3.1 forward reference to §3.4 resolves through
   `\ref{sec:ch3-stability}` and that no broken `\ref`/`\eqref` remains.
4. Confirm that Chapter 4 dependencies are aligned: Chapter 3 owns method
   theory; Chapter 4 owns the design matrix, flag table, and matched-device
   definitions; Chapter 5 owns measured values.
5. Confirm no archived plan language or internal experiment label entered the
   manuscript.

---

## Required Three-Round Self-Check

Do not stop after worker edits. Complete all three self-check rounds. If any
round scores below 95/100, dispatch a focused repair worker and rerun that
round once. If after three full rounds the chapter still cannot reach
95/100, stop and explain exactly which requirement blocks it.

### Round 1: Supervisor-Requirement Coverage

Score Chapter 3 against `supervisor_feedback_map.md` §3.1-3.6 and the
chapter-level rules.

Checklist:

- §3.1: CFL previewed before any later use; finite-volume background cited
  with author-name prose; every displayed equation is numbered.
- §3.2: motivation for slope limiting given before the limiter formula; TVD
  expanded at first use; author-name prose for van Leer / Toro; every
  display numbered.
- §3.3: no "vertical" interface; Davis attribution either cited with an
  existing key or routed through Toro's textbook; HLLC branch conditions
  unambiguous at zero; author-name prose for HLL, Toro-Spruce-Speares, and
  Davis; every display numbered.
- §3.4: CFL formula consistent with §3.1 preview; `\nu_x`, `\nu_y` defined
  after the time-step formula; positivity language preserved; every display
  numbered; `\label{sec:ch3-stability}` present.
- §3.5: "sufficiently accurate in binary64 but insufficiently so in
  binary32" wording used (or absence of the old phrasing recorded); FMA
  hardware/compiler dependence stated; macros presented as compact code-like
  fragments or a table; table-spacing applied; ~280-310 word target met;
  every display numbered.
- §3.6: MHD conserved state and additional fluxes specified; characteristic
  wave families named; `\nabla\cdot\mathbf{B}=0` and its physical meaning
  stated; Dedner-style cleaning with scalar `\psi` written; Evans-Hawley
  constrained transport named; Report 1 evidence boundary explicit; every
  display numbered.

Pass threshold: 95/100.

### Round 2: Evidence, Citation, and Prose-Risk Audit

Checklist:

- Every citation supports the sentence in which it appears, and every key
  exists in `References/references.bib`.
- Author-name prose is used where the text introduces a specific scheme,
  solver, or estimate.
- Chapter 3 contains no implementation table, design matrix, or measured
  result that belongs to Chapter 4/5.
- Technical exposition follows `scientific-writing-duke`: topic sentences are
  concrete, paragraphs have one function each, and each derivation step
  feeds the next.
- Prose passes `avoiding-ai-flavor`: no generic filler, marketing tone,
  unsupported confidence, or repeated triadic rhythm.
- Word count risk is controlled: chapter total moves into the
  1,200-1,350-word window. If still above 1,350, identify the next
  compression target (most likely §3.5 or §3.4).
- All tables remain readable (no `\scriptsize`; `\small` is acceptable; row
  spacing applied where required).

Pass threshold: 95/100.

### Round 3: Mechanical, LaTeX, and Forbidden-Token Check

Run from repository root:

```powershell
git diff --check -- report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: no whitespace or patch-format warnings introduced by this pass.

```powershell
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n -i "config\s*12|configuration-12" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n "vertical interface|well resolved in binary64" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n -U -i "p32(.|\n){0,80}IEEE fp32|IEEE fp32(.|\n){0,80}p32" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Each command should return no manuscript-facing hit. The `p32` proximity
check confirms that Chapter 3 does not equate the Verificarlo virtual
mantissa with IEEE fp32; if `p32` appears at all, the surrounding sentence
must distinguish it from IEEE fp32.

Expected: no manuscript-facing hits.

Check that every displayed equation has a label. Use ripgrep's
`--fixed-strings` flag so the pattern is a literal backslash-bracket and
needs no shell-specific escaping:

```powershell
rg -n -F '\[' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n -F '\]' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: zero hits, because all displayed equations have been converted to
numbered `equation` environments. A residual hit must be justified in the
final response (for example a nested `cases` block that is already inside a
numbered `equation`).

Check citation keys (use single quotes and fixed-strings to avoid
PowerShell/bash backslash-escape differences):

```powershell
rg -n -F '\cite' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n '^@' report1/phd-thesis-template-2.4/References/references.bib
```

The first command matches `\cite`, `\citet`, and `\citep` because all share
the literal `\cite` prefix.

Check labels/cross-references:

```powershell
rg -n -F '\label' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n -F '\ref'   report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n -F '\eqref' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
rg -n -F 'sec:ch3-stability' report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

The last line confirms the §3.4 `\label{sec:ch3-stability}` is in place so
§3.1's forward `\ref` resolves.

Compile:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If citations changed, run:

```powershell
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Pass threshold: no new Chapter 3 LaTeX errors, no forbidden-token hits, no
undefined citation introduced by this pass.

---

## Strict Scoring and Improvement Iteration

After the three self-check rounds, the main agent scores Chapter 3 against
the Report 1 requirements before claiming it is ready. Use a 100-point
rubric:

| Area | Points | What to check |
|------|--------|---------------|
| Supervisor-feedback coverage | 30 | Every §3.1-3.6 supervisor item is addressed and verifiable in prose, equations, or table presentation. |
| Method-theory fidelity | 20 | Finite-volume update, MUSCL-Hancock, HLLC/Rusanov, CFL, limiting, and the MHD bridge are technically correct and self-consistent. |
| Author-name and citation prose | 10 | Specific schemes/solvers/estimates use author-name introductions; every cite key exists; no invented citations. |
| Precision/branch framing | 15 | §3.5 macros and FMA hardware/compiler caveat are stated correctly; `RIEMANN_STRICT_INEQUALITY`, `STRICT_IEEE`, and `FAST_MATH` appear as compact code-like fragments. |
| Style and word budget | 10 | Prose is concise, non-generic, passes `avoiding-ai-flavor`; chapter total inside 1,200-1,350 counted words. |
| LaTeX and forbidden-token correctness | 15 | All displays numbered; tables readable with row spacing; no forbidden manuscript labels; chapter compiles cleanly. |

Iterate:

1. Write a short self-review note with the score breakdown and top defects.
2. Address the highest-impact defects. Use direct integration edits only for
   marker/whitespace/equation-numbering issues; re-dispatch the owning
   worker for new section-level prose.
3. Re-score with the same rubric.
4. Repeat until either the score is at least 95/100 or three improvement
   rounds have completed.

If the score remains below 95/100 after three rounds, stop iterating and
report exactly which requirement blocks it. Classify each remaining
limitation as one of:

- writing/editing issue that can still be improved without new sources,
- citation/source issue that needs a verified BibTeX addition,
- structural issue that should be deferred to a coordinated Chapter 3/4/5
  pass.

After the final review, explicitly ask: "What would most improve Chapter 3
if more time were available?" Answer it in the final response. Do not invent
results or experiments.

---

## Final Response Format

Respond in Chinese with:

- which §3.1-§3.6 sections were revised by which worker;
- how each supervisor issue was addressed (with brief quotation of the new
  wording where useful);
- whether the Davis citation was added, routed through Toro, or reported as
  a gap;
- the new equation labels by section;
- whether `RIEMANN_STRICT_INEQUALITY`/`STRICT_IEEE`/`FAST_MATH` were
  presented as a table or a code-like listing;
- whether any worker needed a repair pass;
- the three self-check scores and outcomes;
- the rubric score breakdown and number of improvement rounds completed;
- compile/check results;
- remaining dependencies on Chapter 2 (Verificarlo/MCA introduction),
  Chapter 4 (design matrix and flag table), Chapter 5 (measured numbers),
  or the References capitalization pass.

Do not claim the full report is finished. Do not commit.
