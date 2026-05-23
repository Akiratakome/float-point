# Chapter 7 Dispatch Prompt

This prompt drafts a compressed Conclusion chapter for Report 1. The
supervisor reviewed Draft 2 and suggested removing Chapter 7 entirely or
compressing it; the user has chosen to **retain a compressed Chapter 7**
of 150-200 counted words. The conclusion must summarise the load-bearing
content of Chapters 1-6, cover both the reproducibility-and-drift
direction (matched-binary CPU/GPU plus compiler / branch / solver /
fp32-flag / finite-time-drift sensitivity) and the precision-adequacy
direction (direct fp32/fp64 vs reference scale plus the region-aware
Verificarlo diagnostics), without ever using the planning labels for
those directions.

It follows the dispatch and verification flow of
`report1/planning/chapter6_dispatch_prompt.md`. Content requirements come
from the manuscript-outline §7 plan, the supervisor-feedback map, the
supervisor guide, the finalised Chapters 1-6, and the locked
conclusion-evidence list.

---

## Master prompt

You are the main agent for the Report 1 Chapter 7 conclusion-writing
round. Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

This round rewrites Chapter 7 in full. The existing 490-word three-section
draft is replaced by a 150-200-word compressed Conclusion. Chapters 1-6,
Chapter 1's roadmap, and `thesis.tex` are left untouched in this round.

### Required reading

Read these files before drafting:

1. `docs/INDEX.md`
2. `report1/INDEX.md`
3. `report1/planning/reportagents.md`
4. `report1/planning/manuscript_outline.md` — §7 "Chapter 7:
   Conclusion" plus the **Conclusion evidence lock** table
5. `report1/planning/supervisor_feedback_map.md` — Chapter 7 block
6. `report1/planning/supervisorguide.md` — supervisor's wording
7. `experiments/report1_evidence_map.md` — confirm every quoted number
   traces to a listed artifact
8. `report1/references/reference.md`
9. `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`
   — verify the five 20% brief categories and the six handbook
   criteria are still satisfied after the new conclusion is in place
10. `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex` — the
    introduction's aim and contribution wording, which the conclusion
    must echo without reintroducing
11. `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
12. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
13. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
14. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
15. `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` — the
    synthesis the conclusion sits on top of; do not duplicate Chapter 6
    mechanism explanations or numerical discussion
16. `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex` — the
    existing draft, replaced wholesale in this round

### Required skills (invoke before drafting)

The drafting worker invokes these three skills, in this order, and
states the invocation explicitly in the dispatch summary:

```text
report1/skills/writing-conclusion/SKILL.md
report1/skills/report1-context/SKILL.md
report1/skills/academic-english-style/SKILL.md
```

The `writing-conclusion` skill is the primary skill for this round; its
six moves (restate aim → key findings → implication/contribution →
calibrate → limitations → future work) define the section internals
below. The `report1-context` skill anchors the aim and contribution
language to the introduction's wording so the conclusion answers the
question the introduction posed. The `academic-english-style` skill
controls hedge placement and prose tightness.

Read these style skills as the final pass:

```text
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/editing-academic-prose/SKILL.md
```

### Main-agent role

- Dispatch one worker (Worker R-B) for the chapter rewrite, then run
  the verification block.
- Do not modify Chapter 1, Chapter 2, Chapter 3, Chapter 4, Chapter 5,
  Chapter 6, `thesis.tex`, raw experiment artifacts, or anything under
  `experiments/`.
- Do not regenerate figures or tables; the conclusion is text-only.
- Confirm the worker invoked the three required skills before writing
  prose; if not, restart the worker with the explicit skill-invocation
  reminder.

### Section markers and chapter scope

Replace the entire body of `Chapter7/chapter7.tex` between
`\chapter{Conclusion}` and end of file with the following marker
skeleton, then fill the markers per the worker goal:

```latex
%!TEX root = ../thesis.tex

\chapter{Conclusion}

\section{Aim and Evidence Base}
% <<SECTION_1_BEGIN>>
% <<SECTION_1_END>>

\section{Key Findings}
% <<SECTION_2_BEGIN>>
% <<SECTION_2_END>>

\section{Limitation and Next Step}
% <<SECTION_3_BEGIN>>
% <<SECTION_3_END>>
```

Total counted-word target across §7.1-§7.3: **150-200 words**, hard
upper 200. Tables, equations, and figures are not used in this chapter.

### Conclusion ownership

Chapter 7 owns:

- a synthesis-shaped restatement of the report's aim that
  recognisably answers the question the introduction posed (Move 1 of
  `writing-conclusion`);
- two or three load-bearing findings drawn from the Conclusion
  evidence lock (Move 2), which together cover **both** of the
  evidence directions used in the project:
  1. the **reproducibility-and-drift direction** — matched-binary
     CPU/GPU saved-output bit-identity within each tested case, plus
     selected compiler / branch / solver / fp32-flag / finite-time
     drift sensitivity (this is the planning-label "D1" direction,
     **but the label itself must not appear in the prose**);
  2. the **precision-adequacy direction** — direct fp32/fp64
     differences scaled against reference or discretisation error,
     plus the region-aware Verificarlo / MCA diagnostics that locate
     precision pressure on shock-interaction fronts in LW3 (this is
     the planning-label "D2" direction, **also forbidden in the
     prose**);
- a one-clause statement of the report's contribution (Move 3): a
  bounded Euler baseline for the wider precision/hardware study;
- a single calibrating sentence (Move 4) that places the hedge on the
  implication, not on the finding;
- one short paragraph of bounded limitations (Move 5);
- one concrete Report 2 next step (Move 6) tied to the limitation;
- one declarative take-home sentence that closes the chapter forward,
  not backward.

Chapter 7 must not:

- repeat Chapter 6's mechanism explanations, equation references, or
  detailed numerical discussion;
- restate Chapter 5's per-case validation tables;
- introduce any new figure, table, equation, or citation that is not
  already in the active manuscript citation set;
- claim that MHD validation has been completed;
- claim that the full Euler catalogue has CPU-GPU coverage;
- claim that HLLC is universally superior;
- claim that hardware has no effect on shock-capturing codes in
  general;
- claim that fp32 is adequate outside the measured cases;
- use the planning labels "D1" or "D2", the priority labels "P0"
  through "P3", week labels, or any of the other internal vocabulary
  listed under "Hard language and evidence rules" below.

### Conclusion evidence lock (binding)

Every claim in the new Chapter 7 must trace to one of the six allowed
claims below, copied verbatim from `manuscript_outline.md`'s
**Conclusion evidence lock**:

1. 1D Euler validation is documented for the selected 1D cases,
   including Sod and the strong Toro cases.
2. 2D Euler validation is documented for two Liska-Wendroff Riemann
   configurations, LW3 and LW12; LW12 uses an 800-square fp64
   numerical reference, not an exact solution.
3. CPU-GPU differences are quantified for the selected cases with
   matched device runs under `solver=hllc`, `STRICT_IEEE=ON`.
   Toolchain split: Toro3 and Toro5 use Windows BuildTools; Sod, LW3,
   and LW12 use Linux/WSL. Each within-case CPU/GPU comparison uses
   one matched binary/configuration, so bit-identity holds within a
   case independently of cross-case toolchain differences.
4. fp32/fp64 differences can be compared with reference or
   discretisation error in the tested cases. Direct fp32 claims come
   from real fp32/fp64 runs, not from Verificarlo virtual `p32`.
5. Region-aware virtual-precision diagnostics show spatially
   non-uniform precision sensitivity in LW3. Verificarlo `p32` is
   virtual precision, not IEEE binary32.
6. Compiler, branch-rule, solver, and drift-growth variation axes
   were measured as sensitivity evidence.

If a sentence the worker wants to write cannot be traced to one of
these six items, the sentence is cut.

### Coverage of Chapters 1-6 (binding)

The conclusion's three sections together must visibly summarise the
load-bearing content of every preceding chapter. The mapping below is
how the worker checks the coverage; it is not a templated outline,
because the conclusion is one short narrative, not a per-chapter
checklist.

| Source chapter | What the conclusion must echo (in prose, briefly) |
|---|---|
| Chapter 1 (Introduction) | the framing question — how precision and hardware affect a Riemann-solver-based HRSC method on a controlled Euler validation suite — restated in the same vocabulary the introduction used |
| Chapter 2 (Background) | implicit: the Euler validation scope and the floating-point arithmetic framing that justifies treating precision as a measurable axis (no new literature) |
| Chapter 3 (Numerical method) | implicit: the MUSCL-Hancock + HLLC method as the *what* whose precision and hardware behaviour was measured (no method derivation) |
| Chapter 4 (Implementation and experimental design) | implicit: the matched-binary CPU/GPU design and the reference-scaled metric framework that made the precision and hardware comparisons interpretable (no design-matrix repetition) |
| Chapter 5 (Validation and precision results) | the validated Euler set (Sod, Toro3, Toro5, LW3, LW12) named once at first finding mention; the matched strict-HLLC CPU/GPU bit-identity finding; the direct fp32/fp64-vs-reference reading; the compiler / branch / solver / fp32-flag / finite-time-drift sensitivity observation |
| Chapter 6 (Discussion) | the precision-adequacy synthesis (region-aware diagnostics locating precision pressure on shock-interaction fronts) and the implementation-vs-precision sensitivity reading; no mechanism re-explanation |

The validated Euler set "Sod, Toro3, Toro5, LW3, LW12" may be named
once if it fits inside the word budget; otherwise the conclusion may
say "the selected one- and two-dimensional Euler cases" and let
Chapter 5 carry the case names.

### Hard language and evidence rules

These rules apply throughout. They are the same set the Chapter 6
dispatch uses and are reproduced here so this prompt is self-contained.

- Do not use manuscript-facing internal labels. All of the following
  are writing-planning vocabulary only and must not appear in
  Chapter 7 prose, captions, or headings:
  - week labels: `week2`, `week3`, `week4`, `week5`, `week6`, `week7`,
    `week8`, `week9`;
  - evidence-priority labels: `P0`, `P1`, `P2`, `P3`;
  - direction labels: `D1`, `D2` — these are the project's planning
    names for the reproducibility/drift and precision-adequacy
    directions; the directions themselves are summarised in the
    findings, but the labels never appear in the prose;
  - case nicknames and harness names: `HLLC-fill`, `config12`,
    `LW12/config12`;
  - internal probe labels: `P1 probe`;
  - source-code constants: `USE_GPU` (use `ENABLE_CUDA` if a build
    flag must be named).
- Use "Liska-Wendroff configuration 3 (LW3)" and "Liska-Wendroff
  configuration 12 (LW12)" at first mention in Chapter 7, then "LW3"
  and "LW12".
- Verificarlo `p32` is virtual mantissa precision, not IEEE
  binary32/fp32. If §7.2 mentions Verificarlo or `p32` at all, state
  this distinction inline in one short clause, or point to
  Chapter 2 §2.4 or Chapter 6 §6.2 without re-deriving it.
- Do not call pairwise fp32-fp64 differences "fp32 error" or
  "fp64 error".
- Do not use "Lyapunov exponent" or "Lyapunov-like".
- Do not cite `wolf_etal_1985` or `eckmann_ruelle_1985`.
- Saved-checkpoint CPU/GPU evidence does not prove equality of all
  intermediate stage values inside a time step. If §7.2 mentions
  CPU/GPU bit-identity, state this boundary in one short clause.
- Do not write template openers: "In conclusion", "To summarise",
  "This report has shown that", "This study has demonstrated that".
  The first sentence of §7.1 instead restates the aim directly.
- Citations: usually none. The Bard and Dorelli (2014) citation may
  be used **at most once** in §7.3 to support the MHD-on-accelerator
  Report 2 next step, but only after verifying the active-manuscript
  appearance count remains ≤ 2 across the full manuscript.
- AI-assisted prose must satisfy `avoiding-ai-flavor`: no generic
  filler, no marketing tone, no unsupported confidence, no triadic
  "X, Y, and Z" cadence in three consecutive sentences, and no
  sentence that could be pasted into an unrelated dissertation.

### Word-budget lock

Current Overleaf-counted state reported by the user before this round
starts: Chapters 1-5 plus the legacy Chapter 7 stub together count
**6415** words. After the Chapter 6 round adds 850-950 words (working
target) and this round replaces the legacy ~490-word Chapter 7 with a
150-200-word compressed Conclusion, the projected total is
approximately **6925-7075** counted words. This sits comfortably below
the 7400 drafting target and the 7500 hard cap. The main agent verifies
the actual Overleaf-counted total against this projection in the final
response.

The 150-200-word target is split across the three sections as:

| Section | Working range |
|---|---|
| §7.1 Aim and Evidence Base | 30-45 |
| §7.2 Key Findings | 80-110 |
| §7.3 Limitation and Next Step | 35-55 |
| **Sum** | **145-210** (target 150-200) |

If the section sum lands above 200, compress §7.2 first by tightening
the two findings before touching §7.1 or §7.3. Do not cut below 150
because the chapter must still cover both evidence directions, the
contribution, the limitation, and the next step in a way an external
reader can follow without rereading Chapter 6.

---

## Worker R-B: Rewrite Chapter 7 as a 150-200-word compressed Conclusion

Assigned region: the entire body of `Chapter7/chapter7.tex` between
the `\chapter{Conclusion}` line and end of file. Replace the existing
~490-word three-section draft wholesale.

### Skill invocation (do this first)

Before writing any prose, invoke the three required skills in this
order. Confirmation in the dispatch summary is **not** a one-line
"skills invoked"; it is a per-skill mapping table reporting which
sentence in the final draft carries which skill move:

| Skill | What the worker reports |
|---|---|
| `writing-conclusion` | Six-move mapping table — exactly which sentence (quoted) carries Move 1, which carries Move 2 (per finding), Move 3, Move 4, Move 5, Move 6. |
| `report1-context` | One quote from §7.1 that re-uses a phrase from Chapter 1 §1.3 verbatim, plus the source line number. |
| `academic-english-style` | One sentence in the draft that originally read with a hedge on the finding, rewritten so the hedge sits on the contribution / next step instead — quoted before and after. If the first draft already had hedges correctly placed, the worker reports "no rewrite needed; hedge on Move 3 / Move 6, finding sentences carry no may/might/can". |

If the worker cannot fill all three rows of this table, the skills
were not actually applied and the worker restarts.

1. `report1/skills/writing-conclusion/SKILL.md` — the primary skill;
   follow its six-move order (restate aim → key findings →
   implication/contribution → calibrate → limitations → future work)
   and the worked-example annotation pattern. The skill warns against
   summary creep, flat finding lists, over-hedging, under-hedging the
   implication, apologetic limitations, generic future work, and the
   absence of a take-home sentence; this worker applies those rules.
2. `report1/skills/report1-context/SKILL.md` — anchor the aim and
   contribution vocabulary to the Report 1 introduction. The
   conclusion must visibly answer the introduction's question, using
   the introduction's terms ("how precision and hardware affect a
   Riemann-solver-based HRSC method on a controlled Euler validation
   suite").
3. `report1/skills/academic-english-style/SKILL.md` — control hedge
   placement (the hedge goes on the implication, not on the finding)
   and prose tightness so 150-200 counted words still carry the six
   moves.

### Drafting goal

Insert the section-marker skeleton from the master prompt, then fill
the three marker regions as follows.

#### §7.1 Aim and Evidence Base (30-45 counted words)

Move 1 of `writing-conclusion`. One short paragraph:

- restate the report's aim in the same vocabulary as the introduction
  (precision and hardware on a Riemann-solver-based HRSC method;
  controlled Euler validation);
- name the evidence base in one clause — the selected one- and
  two-dimensional Euler cases, plus the matched within-case CPU/GPU
  saved-output comparisons and the region-aware precision diagnostics.

Do not introduce new evidence, new citations, or template openers.
Do not write "This study examined" or "In this report".

#### §7.2 Key Findings (80-110 counted words)

Moves 2 and 3 of `writing-conclusion`. **Three findings** are the
default, because the reproducibility-and-drift direction splits
naturally into a device finding and an implementation-sensitivity
finding; stacking both into one finding produces an overlong sentence
and crowds out the precision-adequacy finding. Use two findings only
if the word budget cannot accommodate three short ones (typical
three-finding budget: 25-30 words per finding + 15-20 words for the
contribution = 90-110 words). Each finding is one short sentence and
traces to the Conclusion evidence lock. The three findings **must
together cover both evidence directions**, summarised below in the
descriptive vocabulary the prose uses (the planning labels "D1" and
"D2" never appear in the prose):

- **Finding 1 — Matched within-case CPU/GPU device reproducibility.**
  Draws on lock items 1, 2, 3. One short sentence stating that matched
  strict-HLLC CPU/GPU saved outputs (final and saved checkpoints) were
  bit-identical within each tested case under the within-case
  toolchain boundary, with the boundary stated once in a subordinate
  clause so the result is not over-generalised. Anchor with the
  concrete metric "zero L1, L∞, and ULP_max across the tested
  matched-binary set" — this is the **required reproducibility-side
  numerical anchor**.

- **Finding 2 — Implementation-and-compiler sensitivity sits at
  roundoff to compiler-flag scale, ordered by wave-structure
  severity.** Draws on lock item 6. One short sentence registering
  that compiler optimisation level (O2 vs O3) was bit-identical
  across the tested set, while fast-math produced the largest
  non-stationary drift and HLLC vs Rusanov dominated as deliberate
  method variation. No specific numbers are required here; the
  qualitative ordering "O2/O3 = 0; fast-math > 0; HLLC vs Rusanov
  much larger" is enough.

- **Finding 3 — Precision adequacy against the available reference
  scale, with region-aware diagnostics locating the pressure.** Draws
  on lock items 4 and 5. One sentence (or two short ones) carrying
  the direct fp32/fp64-vs-reference reading and the region-aware
  Verificarlo / MCA diagnostic conclusion: the precision drift sat
  below the reference / discretisation error scale in the tested
  cases, with the residual pressure localising on the
  shock-interaction fronts of LW3, consistent with the LW12
  upper-right localisation already shown in Chapter 5 §5.4. Anchor
  with the concrete number **LW12 N=400 reference-scaled density
  ratio of `1.30e-4`** — this is the **required precision-side
  numerical anchor**. State the Verificarlo `p32` vs IEEE fp32
  distinction in one short clause so virtual-precision evidence is
  not read as direct fp32 evidence.

After the three findings, add the one-clause **contribution**
sentence (Move 3): the report contributes a bounded Euler baseline
for the later precision and hardware study, not a general statement
about all HRSC schemes, all hardware, or untested MHD configurations.

**Numerical-anchor rule (binding).** §7.2 must contain at least two
specific quantitative anchors: the "zero L1/L∞/ULP_max" CPU/GPU
identity statement in Finding 1, and the LW12 N=400 density ratio
`1.30e-4` in Finding 3. A draft without both anchors is rejected by
the verification block; an anchor-less Conclusion is what the
`writing-conclusion` skill calls a "flat finding-list" and is the
single failure mode most likely to drop the manuscript below the
Quality of write-up target.

**Edge-case ban.** §7.2 must **not** name Toro2's strict-`<`
non-completion, the stationary-contact infinite-ratio degenerate
case, the Toro 123 test, the supplementary GPU strict-vs-fast probe,
the limiter-axis status, or any per-case sub-finding that the
supervisor flagged as "limitation/status only". Those belong to
Chapter 5 §5.6 (where they already appear) and the Chapter 6 §6.4
limitation list. Mentioning them here breaks the inverted-funnel
shape required by `writing-conclusion` and consumes 25-40 of the 200
counted words without adding a take-home claim.

#### §7.3 Limitation and Next Step (35-55 counted words)

Moves 4, 5, and 6 of `writing-conclusion`. One short paragraph:

- Move 4 (calibrate): the hedge sits on the implication, not on the
  findings — the bounded Euler baseline is offered "for the
  configurations tested" rather than as a universal HRSC result;
- Move 5 (limitation): name one bounded limitation that covers the
  tested-Euler-cases / tested-precisions / tested-compilers /
  saved-output-checkpoints / LW3-MCA-diagnostic-grid scope. State the
  Toro2 strict `<` non-completion only if there is still room; it is
  optional here because Chapter 6 §6.4 already carries it;
- Move 6 (future work): one concrete Report 2 next step. Generic
  "extend to MHD" is rejected by the `writing-conclusion` skill's
  "generic future work" common-mistake rule. The next step must name
  **at least one concrete artefact** the Report 2 work will produce:
  for example, "an Orszag-Tang MHD validation entry with hyperbolic
  Dedner-type divergence cleaning on the same matched-binary
  CPU/GPU framework", or "a Brio-Wu shock-tube precision-adequacy
  comparison against the same Verificarlo / MCA diagnostic chain".
  Pick one such artefact and name it; do not list both. Do not
  promise MHD validation in Report 1. If a citation is added here,
  it is at most one Bard and Dorelli (2014) citation subject to the
  active-manuscript ≤ 2 cap.

End §7.3 with one declarative **take-home sentence** that a reader
could quote out of context. The take-home sentence closes the chapter
forward, not backward, and does not contain new evidence. **Quotable
self-test (binding):** in the dispatch summary, the worker writes the
take-home sentence on its own line, isolated from the surrounding
paragraph, and confirms in one sentence that the isolated form still
parses, still makes a specific claim, and still bounds the claim to
the tested scope. If the isolated sentence reads as filler ("This
report contributes ..."), as a generic platitude ("Further work is
needed ..."), or as a sentence that requires the preceding paragraph
to make sense, the worker rewrites it before submission.

### Constraints

- The total counted-word target across §7.1-§7.3 is **150-200**. If
  the prose passes 200, compress; do not push above 200.
- No tables, no figures, no equation blocks.
- No `\citep` / `\citet` citations except at most one Bard and
  Dorelli (2014) citation in §7.3 (subject to the cap).
- Do not duplicate Chapter 6 synthesis prose. The conclusion is short
  and outcome-facing; it does not reopen mechanism discussion.
- Do not write template openers ("In conclusion", "To summarise",
  "This report has shown that", "This study has demonstrated that").
- Do not write any sentence whose claim is not covered by the
  Conclusion evidence lock.
- Do not write the strings "D1" or "D2" anywhere in the prose,
  captions, or headings. The two evidence directions are described
  in plain language (reproducibility-and-drift; precision adequacy
  with region-aware diagnostics).
- Do not write the priority strings "P0", "P1", "P2", or "P3" in the
  prose. Use "the matched within-case CPU/GPU comparisons", "the
  region-aware precision diagnostic", and so on.

---

## Main-Agent Integration Tasks

After Worker R-B finishes:

1. Read the new `Chapter7/chapter7.tex` end-to-end.
2. **Six-moves audit.** Confirm that all six writing-conclusion moves
   are present in order:
   - Move 1 (restate aim) — §7.1 first sentence echoes the
     introduction's vocabulary;
   - Move 2 (key findings) — §7.2 carries two (or three) findings,
     each traced to one or more Conclusion evidence-lock items;
   - Move 3 (implication / contribution) — §7.2 closing carries the
     bounded-baseline contribution sentence;
   - Move 4 (calibrate) — the hedge sits on the contribution / next
     step, not on the findings;
   - Move 5 (limitation) — §7.3 names one bounded limitation;
   - Move 6 (future work) — §7.3 names the MHD Report 2 next step.
3. **Direction-coverage audit.** Confirm that §7.2 covers both
   evidence directions:
   - reproducibility / drift direction (matched CPU/GPU bit-identity
     plus compiler / branch / solver / fp32-flag / drift sensitivity);
   - precision-adequacy direction (direct fp32/fp64-vs-reference plus
     region-aware Verificarlo diagnostics on the fronts).
4. **Duplication audit.** Confirm that:
   - the toolchain-split boundary appears once in Chapter 7 (and was
     already present in Chapter 4 and Chapter 5 §5.5);
   - the MHD next-step sentence does not duplicate Chapter 6 §6.4
     verbatim;
   - any single numerical value used (for example, LW12 `1.30e-4`)
     appears at most twice across Chapters 5-7 combined.
5. **Forbidden-language sweep.** Run the grep block below; expect
   zero manuscript-facing hits.
6. **Evidence-lock trace.** For each sentence in Chapter 7, name in
   the dispatch summary which of the six evidence-lock items it
   traces to.
7. **Citation-cap audit.** Confirm the Bard and Dorelli active count
   across `Chapter*/chapter*.tex` (excluding `.snapshots`) is ≤ 2.
8. **Overleaf-count verification.** Confirm the actual Chapter 7
   counted-word total is in 150-200, and the full manuscript total is
   in the projected 6925-7075 band. If above 7400, record the
   overshoot.

Do not change Chapter 1, Chapter 2, Chapter 3, Chapter 4, Chapter 5,
Chapter 6, or `thesis.tex` in this round.

---

## Verification Commands

Run from repository root unless otherwise stated.

### Forbidden / internal language

```powershell
rg -n "week[2-9]|\bP[0-3]\b|\bD[12]\b|HLLC-fill|config12|LW12/config12|P1 probe|USE_GPU|fp32 L1 error|fp64 L1 error|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|In conclusion|To summarise|This report has shown|This study has demonstrated" report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Expected: no manuscript-facing hits. The `\bD[12]\b` pattern catches
the direction labels "D1" and "D2".

### Edge-case-ban grep (§7.2 must not name limitation-only cases)

```powershell
rg -n "Toro2|Toro 2|Toro-2|Toro123|Toro 123|Toro-123|stationary[_ ]contact|GPU strict-vs-fast|GPU flag probe|limiter[- ]selection|limiter-axis" report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Expected: zero hits. These cases are limitation-only material that
already lives in Chapter 5 §5.6 and Chapter 6 §6.4; mentioning them
in the conclusion breaks the inverted-funnel shape required by
`writing-conclusion`.

### Required numerical anchors (binding)

```powershell
rg -n "1\.30[eE]-?0?4|1\.30\\\\times10\^\{-4\}|1\.30 ?\\\\cdot ?10\^\{-4\}|L_1 ?= ?0|L_\\\\infty ?= ?0|ULP[_ ]?max ?= ?0|zero L_1|bit-identical" report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Expected: at least one match for the precision-side anchor (the
LW12 N=400 density ratio `1.30e-4` or its LaTeX `1.30\times10^{-4}`
form), **and** at least one match for the reproducibility-side
anchor (zero L1/L∞/ULP_max or "bit-identical"). A draft without
both anchors is what `writing-conclusion` calls a "flat finding-list"
and is rejected.

### Verificarlo / fp32 distinction (if §7.2 mentions either)

```powershell
rg -n "p32|Verificarlo|fp32|MCA" report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Expected: if any of these terms appears, the chapter keeps the
IEEE-fp32 vs virtual `p32` distinction visible, either inline or by
pointing to Chapter 2 §2.4 or Chapter 6 §6.2.

### Aim-vocabulary echo

```powershell
rg -n "precision|hardware|HRSC|Euler|Riemann" report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
rg -n "precision|hardware|HRSC|Euler|Riemann" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

Expected: §7.1 reuses the introduction's core terms (precision,
hardware, HRSC, Euler, Riemann-solver) at least once; if any of these
five terms is missing from §7.1, the aim restate is too weak.

### Citation count audit (Bard and Dorelli cap)

```powershell
rg -n "bard_dorelli" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex --glob "!*.snapshots*"
```

Expected count across the active manuscript after this round: ≤ 2.

### Word count (informal section sanity)

```powershell
rg -nU "<<SECTION_[1-3]_BEGIN>>([\s\S]*?)<<SECTION_[1-3]_END>>" report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Inspect each marker region. The Overleaf counted-text value remains
the controlling number; this is only a local sanity check.

### LaTeX compile

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

Fix only Chapter 7 problems unless the failure is clearly a
pre-existing unrelated issue.

---

## Final Response Format

Respond in Chinese with:

- the **skill-application table** from the Skill invocation section
  filled in completely: six-move mapping for `writing-conclusion`
  (sentence-by-sentence quotes), the C1 §1.3 verbatim phrase for
  `report1-context` with line number, and the hedge-placement
  before/after for `academic-english-style`. A one-line "skills
  invoked" sentence is not acceptable;
- the three section drafts in full, with the counted word total per
  section and the chapter total;
- the six-moves audit result (which sentence carries each of the six
  writing-conclusion moves);
- the direction-coverage audit result: name the sentence that
  carries the device-reproducibility part (Finding 1), the sentence
  that carries the implementation-sensitivity part (Finding 2), and
  the sentence that carries the precision-adequacy part (Finding 3);
  confirm that neither label "D1" nor "D2" appears in the prose, and
  that the two required numerical anchors (zero L1/L∞/ULP_max and
  LW12 `1.30e-4`) are present;
- the edge-case-ban audit result: confirm zero mentions of Toro2,
  Toro123, stationary_contact, GPU flag probe, or limiter-axis;
- the **quotable take-home self-test**: write the take-home sentence
  on its own line, isolated from the surrounding paragraph, plus one
  sentence confirming it still parses, still makes a specific claim,
  and still bounds the claim to the tested scope when read alone;
- the Conclusion evidence-lock trace, sentence by sentence (each
  sentence cites one of the six lock items by number);
- the duplication audit result (toolchain-split appearance count
  across the active manuscript; LW12 `1.30e-4` appearance count
  across Chapters 5-7; MHD next-step phrasing comparison with
  Chapter 6 §6.4);
- citation-cap status (Bard and Dorelli active count);
- the actual Overleaf-counted total for the full manuscript after
  this round, with the projection range (6925-7075), and any
  overshoot above 7400 if present;
- LaTeX compile result.

Do not claim Report 1 is finished unless every check passed and the
full-manuscript total is at or below 7400 counted words against the
drafting target.
