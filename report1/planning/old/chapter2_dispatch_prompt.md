# Chapter 2 Dispatch Prompt

This is the Codex-ready master-agent prompt for drafting Chapter 2 of Report 1.
It follows the structure of `chapter5_dispatch_prompt.md`, but is scoped to the
background, literature, and governing-equation chapter. The example Report 1 PDF
is used only for structure: it puts contextual background before method,
implementation, and tests, and it separates governing equations from later
numerical-method detail. Do not reuse its scientific content.

---

## Master prompt (paste below this line)

You are the main agent for the Report 1 drafting phase. Repository:

    c:\Users\tangy\Desktop\floatpoint

This round drafts only Chapter 2, "Background and Governing Equations". In the
planning outline, treat this chapter as "Background and Literature Context":
it is the main literature/background chapter, with only minimal governing
definitions.

Target file: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`

### Required reading

Read these files before dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/WRITING_AGENT.md`
5. `report1/planning/reportagents.md`
6. `report1/planning/manuscript_outline.md`
7. `experiments/report1_evidence_map.md`
8. `report1/references/reference.md`
9. `report1/planning/drafting_status.md`
10. `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
11. Already drafted chapters that Chapter 2 must remain consistent with:
    - `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
    - `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
    - `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
12. Optionally inspect `report1/examples/Project-Report-1-example.pdf` only for structure if PDF tooling is readily available:
    front matter, table-of-contents style, and the way background/governing
    equations prepare later methods and tests. Do not copy scientific content,
    phrasing, citations, or topic structure from the example report. Do not
    block drafting if the PDF cannot be inspected quickly.

Lazy-load these style skills only when you are about to use them:

- `report1/skills/avoiding-ai-flavor/SKILL.md`
- `report1/skills/academic-english-style/SKILL.md`
- `report1/skills/writing-literature-review/SKILL.md`

### Hard rules

- Main agent does not draft Chapter 2 prose. Its job is to read context,
  prepare the marker skeleton, dispatch workers, verify edits, enforce
  literature/style/LaTeX consistency, run review rounds, and add only the
  BibTeX entries actually cited. It may make local integration edits after
  review, but must not add new claims, new citations, or rewrite whole
  paragraphs without redispatching the responsible worker.
- Each section is written by exactly one worker. Workers run serially. Never
  spawn two workers against `chapter2.tex` at the same time.
- A worker may modify only the region between its assigned markers.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned marker region."
- Do not modify solver numerics, cfg defaults, experiment results, output
  formats, or raw artifacts. Do not move files under `experiments/`.
- Chapter 2 is the main literature/background chapter, with minimal governing
  definitions. It is not a finite-volume derivation, not an HLLC explanation,
  not an implementation chapter, and not a results chapter. Detailed
  MUSCL-Hancock, HLLC, CFL, implementation, and validation evidence belong to
  Chapters 3--5.
- Do not describe MHD as validated Report 1 evidence. MHD appears only as
  project context and Report 2 direction.
- Manuscript-facing prose, captions, labels, and figure paths must not contain:
  `week7`, `week8`, `D1`, `D2`, `HLLC-fill`, `config12`,
  `LW12/config12`, or `USE_GPU`.
- Use `ENABLE_CUDA`, not `USE_GPU`, if a compile flag must be named.
- Compiler-flag literals (`-Ofast`, `--use_fast_math`, `-ffp-contract`, `-O3`)
  are explicitly permitted as Chapter 2 prose tokens; they are not internal
  implementation labels and reviewers must not flag them as scope leaks.
- This dispatch prompt may impose tighter local drafting limits than
  `manuscript_outline.md` for Chapter 2. If it conflicts with
  `reportagents.md`, `report1/WRITING_AGENT.md`, or the substantive chapter
  plan in `manuscript_outline.md`, stop and report the conflict rather than
  silently choosing this prompt.
- Do not treat Verificarlo `p32` as IEEE fp32.
- Do not claim fp32 adequacy, CPU/GPU equivalence, or hardware neutrality in
  Chapter 2. The chapter may explain why these effects are plausible and worth
  measuring; quantitative claims belong to Chapters 5 and 6.
- Every citation must support a specific sentence. Avoid source lists and
  chronological paper summaries.
- Do not invent citations or citation keys. Use only verified sources from
  `report1/references/reference.md` and keys confirmed in `references.bib`.
- AI-assisted prose must pass `avoiding-ai-flavor`: no filler, no marketing
  tone, no unsupported confidence, and no generic paragraph that could fit an
  unrelated report.

### Chapter target and structure

Working target: 950-1,050 Overleaf-counted words. Hard upper: 1,100. The worker
targets below are advisory ranges, not additive entitlements: their upper ends
sum above the chapter cap once the Euler equation block is included. The main
agent must check total length after each worker and compress before continuing
if the chapter is drifting above budget. If the draft approaches 1,050 counted
words, compress Section 2.1, Section 2.3, and Section 2.5 before weakening the
floating-point mechanism coverage in Section 2.4. Equation text may be counted
by Overleaf, so prose should stay below about 1,000 words when Section 2.1 uses a
displayed equation block.

Purpose: satisfy the literature/background marking category while setting up
only the equations and concepts needed later. The chapter should narrow from
the Euler validation system to the finite-volume HRSC literature and
floating-point reproducibility literature, then state the Report 1 gap.
Equations are minimal; derivations belong to Chapter 3.

The chapter should do five things:

1. Define the compressible Euler system used as the Report 1 validation system,
   using only the minimum equations needed for later notation.
2. Position ideal MHD as the wider project target, with divergence control as a
   future-project issue.
3. Explain why finite-volume HRSC and Riemann-solver methods are the relevant
   method family for shocks and contacts, without deriving the update or HLLC
   flux.
4. Explain the floating-point mechanisms that can change simple expressions and
   time-dependent solvers: binary32/binary64, rounding, non-associativity, FMA,
   compiler flags, and parallel ordering.
5. End with a clear gap statement: Report 1 measures precision and hardware
   sensitivity for controlled Euler HRSC validation tests.

### Allowed citation policy

Use `report1/references/reference.md` as the citation map. Add BibTeX entries
only for citations used in the final Chapter 2 draft.

Allowed citation keys for Chapter 2:

| key | source | use in Chapter 2 |
|-----|--------|------------------|
| `toro2009` | Toro, *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed., 2009 | Euler equations, finite-volume HRSC context, shock-tube framing |
| `sod_1978` | Sod, JCP 27(1), 1978 | optional support only if Sod shock-tube validation is named |
| `liska_wendroff_2003` | Liska and Wendroff, SIAM J. Sci. Comput. 25(3), 2003 | 2D Euler benchmark motivation in the gap paragraph |
| `harten_lax_vanleer_1983` | Harten, Lax, and van Leer, SIAM Review 25(1), 1983 | HLL-family / Godunov-type finite-volume background |
| `vanleer_1979` | van Leer, JCP 32(1), 1979 | MUSCL / second-order conservative reconstruction background |
| `goldberg_1991` | Goldberg, ACM Comput. Surv. 23(1), 1991 | binary floating-point, rounding, cancellation, non-associativity |
| `ieee754_2019` | IEEE Std 754-2019 | binary32/binary64 and round-to-nearest-even semantics |
| `higham_2002` | Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed., 2002 | disciplined language for rounding error, stability, and accumulation |
| `bard_dorelli_2014` | Bard and Dorelli, JCP 259, 2014 | optional MHD/GPU motivation only if the manuscript-wide Bard citation cap has room after Chapter 3 |
| `dedner_2002` | Dedner et al., JCP 175, 2002 | normally leave to Chapter 3; use only if Chapter 2 explicitly names divergence cleaning and the wording does not duplicate Chapter 3 |
| `evans_hawley_1988` | Evans and Hawley, ApJ 332, 1988 | normally leave to Chapter 3; use only if Chapter 2 explicitly names constrained transport and the wording does not duplicate Chapter 3 |

All listed keys are already present in `report1/phd-thesis-template-2.4/References/references.bib`
at the time this prompt was written. Do not duplicate entries. If the file has
changed, verify every cited key before compiling.

Citation caps:

- `bard_dorelli_2014`: prefer zero citations in Chapter 2 because Chapter 3
  already uses Bard and Dorelli for the Report 2 MHD/GPU bridge; use at most
  one only if the current manuscript-wide count remains within the cap in
  `manuscript_outline.md`.
- `goldberg_1991`, `ieee754_2019`, and `higham_2002`: use where they support
  distinct floating-point claims, not as decorative background.
- Do not cite MHD divergence-control references unless the section explicitly
  names divergence cleaning or constrained transport. Prefer not to name those
  methods in Chapter 2 because Chapter 3 already carries the MHD-method bridge.

Before the final response, the main agent must extract every `\cite*{...}` key
from `chapter2.tex` and confirm each appears in `references.bib`. Treat any
missing key as a blocking defect, not a cosmetic issue. Suggested commands:

    rg -no "\\\\cite[a-zA-Z]*\\{[^}]+\\}" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
    # for each key K printed above:
    rg -n "@\\w+\\{$K," report1/phd-thesis-template-2.4/References/references.bib

### LaTeX skeleton with markers

Before spawning any worker, main agent inspects `chapter2.tex`. The current
file is a placeholder if every section body between consecutive `\section{...}`
lines contains only comment lines (`%` prefix), whitespace, or TODO markers, and
contains no non-comment LaTeX prose. If the file is a placeholder, save a
snapshot at:

`report1/phd-thesis-template-2.4/Chapter2/chapter2_pre_dispatch_snapshot.tex`

Then rewrite `chapter2.tex` to exactly this marker skeleton. The fifth section
is added deliberately because `manuscript_outline.md` requires a gap statement.

If substantive Chapter 2 prose is already present, stop and report instead of
overwriting it.

```tex
%!TEX root = ../thesis.tex

\chapter{Background and Governing Equations}

\section{Compressible Euler Equations}
% <<SECTION_1_BEGIN>>
% (Worker 1 writes here.)
% <<SECTION_1_END>>

\section{Ideal-MHD Context}
% <<SECTION_2_BEGIN>>
% (Worker 2 writes here.)
% <<SECTION_2_END>>

\section{Finite-Volume HRSC Methods}
% <<SECTION_3_BEGIN>>
% (Worker 3 writes here.)
% <<SECTION_3_END>>

\section{Floating-Point Arithmetic and Reproducibility}
% <<SECTION_4_BEGIN>>
% (Worker 4 writes here.)
% <<SECTION_4_END>>

\section{Report 1 Gap}
% <<SECTION_5_BEGIN>>
% (Worker 5 writes here.)
% <<SECTION_5_END>>
```

### Marker protocol

Worker instruction:

> Read the current `chapter2.tex` in full. Locate exactly your assigned markers
> `% <<SECTION_n_BEGIN>>` and `% <<SECTION_n_END>>`. Replace only the complete
> marker-bounded region, including the BEGIN and END marker lines. The new
> content must keep both marker lines verbatim at the start and end. Do not
> touch text outside those markers. Do not rename markers. Do not insert new
> `\section{}` commands; the section heading is already outside your region.
> If your assigned markers do not appear exactly once each, stop and report.

After each worker returns, main agent verifies with `rg` and file comparison:

- all five BEGIN markers and all five END markers still exist exactly once,
- before dispatching each worker, save an immediate snapshot named
  `report1/phd-thesis-template-2.4/Chapter2/chapter2_before_worker_N.tex`;
- the other four marker-bounded regions are byte-identical to that immediate
  pre-worker snapshot,
- the worker's region begins with its BEGIN marker and ends with its END marker.

If any check fails, restore `chapter2.tex` from that immediate pre-worker
snapshot and re-dispatch that worker. Do not restore from the initial placeholder
snapshot after later workers have already succeeded.

### Worker specs

Give every worker the hard rules, marker protocol, allowed citation policy, and
its own section spec below. Workers must read every source listed in their spec.
Workers must not copy wording from this prompt or from the example PDF. If an
artifact, drafted chapter, or source file contradicts this prompt, the worker
stops and reports.

#### Worker 1 - Compressible Euler Equations

Assigned markers: `SECTION_1_BEGIN` to `SECTION_1_END`.

Write Section 2.1, working target 150-185 counted words plus one compact
equation block (use `equation` or `align` to match Chapter 3 style). Present
the compressible Euler equations as the governing system for the 1D and 2D
validation settings, but keep this as background rather than the detailed
method derivation. Define the conservative state and ideal-gas closure; include
fluxes only in compact vector form or by reference to the standard conservation
law, because Chapter 3 owns the full flux matrices and finite-volume update.
Explain why Euler is the Report 1 validation system: it contains shocks,
contacts, and rarefactions relevant to HRSC validation while remaining simpler
than ideal MHD.

Do not derive eigenvalues, finite-volume updates, CFL conditions, HLLC wave
speeds, or the MUSCL-Hancock update; those belong to Chapter 3. Do not
duplicate the full flux-matrix exposition in Chapter 3. Do not introduce new
result claims. Use notation that can be reused in Chapter 3.

Sources to read:

- `report1/planning/manuscript_outline.md` §2.1
- `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
- `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

Allowed citations: `toro2009`; `sod_1978` only if Sod is named.

#### Worker 2 - Ideal-MHD Context

Assigned markers: `SECTION_2_BEGIN` to `SECTION_2_END`.

Write Section 2.2, hard target 100-135 counted words. Explain ideal MHD as the
wider project target and mention the divergence-free magnetic-field constraint.
Keep MHD as context for Report 2, not as the main evidence of Report 1. This
section should be a short bridge, not an MHD method survey.

Prefer zero citations here if the paragraph can rely on Chapter 3 for MHD
method references. Do not name divergence cleaning or constrained transport in
Chapter 2 unless needed to clarify the divergence-control issue; those method
references are already carried in Chapter 3. Prefer no equation unless it can
be written compactly as the constraint `\nabla\cdot\mathbf{B}=0`.

Sources to read:

- `report1/planning/manuscript_outline.md` §2.2
- `report1/references/reference.md` MHD references section

Allowed citations: prefer none; `bard_dorelli_2014` only if the manuscript-wide
Bard citation cap has room after Chapter 3; `dedner_2002` or
`evans_hawley_1988` only if a divergence-control method is explicitly named and
the wording does not duplicate Chapter 3.

#### Worker 3 - Finite-Volume HRSC Methods

Assigned markers: `SECTION_3_BEGIN` to `SECTION_3_END`.

Write Section 2.3, working target 170-220 counted words. Make it a thematic
literature paragraph, not a chronology. Explain why finite-volume HRSC methods
are suitable for discontinuous compressible flows: they update cell averages by
interface fluxes and can preserve conservation across shocks and contacts.

Close by motivating Chapter 3, where the finite-volume update,
MUSCL-Hancock reconstruction, and HLLC/Rusanov fluxes are described in detail.
Do not duplicate Chapter 3 derivations, the HLLC/Rusanov formulas, or Chapter 4
implementation prose.

Sources to read:

- `report1/planning/manuscript_outline.md` §2.3
- `report1/references/reference.md` HRSC and Riemann-solver theory section
- `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

Allowed citations: `toro2009`, `harten_lax_vanleer_1983`, `vanleer_1979`.

#### Worker 4 - Floating-Point Arithmetic and Reproducibility

Assigned markers: `SECTION_4_BEGIN` to `SECTION_4_END`.

Write Section 2.4, working target 310-350 counted words (hard cap 360; if the
chapter total has already reached 980, compress to 290-310 instead). This is the load-bearing
background subsection for the brief's requirement to discuss floating-point
arithmetic and how hardware, compiler options, and parallel-thread ordering can
affect simple expressions and algorithms.

Required content:

- binary32 versus binary64 storage and unit roundoff,
- round-to-nearest-even IEEE semantics,
- one-sentence example of non-associativity, such as `(a+b)+c` differing from
  `a+(b+c)` in finite precision,
- FMA and `-ffp-contract` as a source of different rounded results,
- compiler-option families such as `-Ofast` and `--use_fast_math`,
- parallel reduction or thread/block ordering as an arithmetic-order issue,
- a hedge: these mechanisms make differences possible, but the size and growth
  of the difference in the HRSC solver is an empirical question measured later.

Do not use this section to report Chapter 5 results. Do not say fp32 is adequate
or inadequate in general. Do not imply that GPU differences are always large.

Sources to read:

- `report1/planning/manuscript_outline.md` §2.4
- `report1/references/reference.md` floating-point section
- Chapter 5 floating-point/compiler variation paragraphs for consistency only:
  `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

Allowed citations: `goldberg_1991`, `ieee754_2019`, `higham_2002`.

#### Worker 5 - Report 1 Gap

Assigned markers: `SECTION_5_BEGIN` to `SECTION_5_END`.

Write Section 2.5, working target 110-145 counted words. Synthesize the chapter
without listing papers. Group the literature into method foundations, benchmark
design, and floating-point reliability. Then state the gap: Report 1 isolates
how the same nominal HRSC computation behaves across precision and hardware
under controlled Euler validation tests.

The paragraph should prepare the reader for Chapter 3 and for the validation
matrix in Chapters 4--5. It must not introduce new results, new benchmarks, or
unverified MHD claims.

Sources to read:

- `report1/planning/manuscript_outline.md` §2.5
- `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
- `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- `experiments/report1_evidence_map.md` only to understand the scope of tested
  Euler evidence; do not cite internal paths in prose.

Allowed citations: `toro2009`, `liska_wendroff_2003`, `goldberg_1991`,
`higham_2002`. Use at most two citation keys in this 85-115 word paragraph,
and each must serve a specific sentence-level claim, not appear as a list tail.

### Review rounds

Round 1: main agent reviews Chapter 2 against the hard rules, citation policy,
forbidden tokens, marker integrity, equation notation, and word budget. Fix only
integration defects, not worker ownership boundaries.

Round 2: spawn one independent reviewer subagent, using the `worker` role if it
is available in the current Codex environment. It must not edit files; its only
output is a findings list. Give it Chapter 2, the hard rules, the allowed
citation table, and this instruction:

> Review for literature-review structure, unsupported claims, overlong MHD
> context, duplicated Chapter 3/4/5 material, forbidden manuscript labels, wrong
> fp32/p32 wording, citation-key violations, AI-flavoured prose, and LaTeX risks.
> Return findings with file/line references. Do not modify files.

Main agent then fixes confirmed issues.
Fixes here mean local integration edits only: duplicate phrase removal,
overlong sentence trimming, citation-key correction, marker repair, or a small
word-budget cut. Redispatch the responsible worker if the fix would add a new
technical claim or materially rewrite a section.

### Strict scoring and improvement iteration

After the worker draft and review rounds, the main agent must score Chapter 2
strictly against the Report 1 requirements before claiming it is ready. Use a
100-point rubric:

| Area | Points | What to check |
|------|--------|---------------|
| Background coverage | 25 | Euler, MHD context, HRSC methods, and floating-point reproducibility are all present at the promised depth. |
| Literature synthesis | 20 | Sources are grouped by technical role, not listed chronologically; every citation supports a sentence. |
| Scope control | 20 | MHD is context only; no Chapter 5 result claims, no fp32 adequacy claim, no hardware overgeneralisation. |
| Technical correctness | 15 | Euler variables/fluxes/closure are correct; floating-point mechanisms are named accurately. |
| Style and integrity | 10 | Prose passes `avoiding-ai-flavor` and reads like restrained student-authored technical writing. |
| LaTeX and citation correctness | 10 | Equations compile, citation keys exist, labels are stable, and forbidden tokens are absent. |

Then iterate:

1. Write a short self-review note with the score breakdown and the top defects.
2. Revise Chapter 2 to address the highest-impact defects.
3. Re-score with the same rubric.
4. Repeat until either the score is at least 90/100 or three improvement rounds
   have completed.

If the score remains below 90/100 after three rounds, stop iterating and report
why. Classify each remaining limitation as one of:

- writing/editing issue that can still be improved without new data,
- citation/evidence interpretation issue that needs more careful reading of
  existing sources,
- scope issue that likely requires a decision about what to defer to later
  chapters.

### Verification before final response

Run these checks from the repository root:

```powershell
rg -n "week7" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "week8" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "\bD1\b" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "\bD2\b" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "config12" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "HLLC-fill" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "USE_GPU" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "fp32 L1 error" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "fp64 L1 error" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n "p32" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
rg -n -U "LW12(.|\n)*config12" report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
```

Each command should return no manuscript-facing hit. If a forbidden token only
appears in an explanatory comment left inside the `.tex`, remove the comment.
After Chapter 2 passes, also run the same forbidden-token search against all
manuscript-facing chapter files:

```powershell
rg -n "week7|week8|\bD1\b|\bD2\b|config12|HLLC-fill|USE_GPU|fp32 L1 error|fp64 L1 error|p32" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Treat hits introduced by this Chapter 2 drafting task as blocking defects.
Report unrelated pre-existing hits separately and do not rewrite other chapters
unless the user explicitly asks.

Then check the prose word count and compile (bibtex pass included so any
newly cited key is link-checked, not only string-matched). `texcount` is only a
local drafting proxy; the final report word count remains controlled by
Overleaf counted text under the course clarification:

```powershell
texcount -1 -sum -merge -inc report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If the `texcount` total exceeds 1,050, compress before declaring the chapter
ready (see ceilings in the "Chapter target and structure" section). If
`bibtex` reports an undefined citation, treat it as a blocking defect rather
than a warning.

Report any compile errors with file:line and state whether they originate in
Chapter 2 prose or unrelated template/bibliography wiring.

### Final response

Respond in Chinese. Include:

- which worker wrote which section,
- files changed,
- current Chapter 2 quality score,
- score breakdown and number of improvement rounds completed,
- remaining improvement opportunities after the final review,
- citations used and whether any BibTeX entries were added,
- whether MHD scope remained within context/future-work bounds,
- verification command results,
- which chapter to draft next.

Do not commit.
