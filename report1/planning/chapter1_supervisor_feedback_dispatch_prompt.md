# Chapter 1 Supervisor-Feedback Execution Prompt

This prompt is for drafting/revising Report 1 Chapter 1 after the supervisor
feedback round. It follows the serial worker/marker workflow used by
`report1/planning/old/chapter4_dispatch_prompt.md` and the newer supervisor
feedback prompts for Chapters 2--5. The content requirements come from the
current outline, the supervisor feedback map, the supervisor guide, Draft 2,
the official project brief, and the current state of Chapters 2--7.

This is not a content plan based on archived prompts. Older plans under
`report1/planning/old/` are workflow references only.

---

## Master prompt

You are the main agent for Report 1 Chapter 1, "Introduction". Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

This round drafts/revises only Chapter 1. The actionable requirements come
from:

```text
report1/planning/manuscript_outline.md
report1/planning/supervisor_feedback_map.md
report1/planning/supervisorguide.md
report1/draft2.pdf
report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf
report1/requirements/SciComp_Mphil_Handbook-2025-26.pdf
```

Use `report1/planning/supervisor_feedback_map.md` as the actionable map. Use
`report1/planning/supervisorguide.md` and `report1/draft2.pdf` only to verify
what the supervisor was responding to. Use the official PDFs to resolve any
conflict in requirements. Do not copy Draft 2 prose directly into the final
manuscript; the Draft 2 introduction is useful only as a record of the prior
narrative and of what feedback needs to improve.

### Required reading

Read these files before dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/WRITING_AGENT.md`
5. `report1/planning/reportagents.md`
6. `report1/planning/manuscript_outline.md`
7. `report1/planning/supervisor_feedback_map.md`
8. `report1/planning/supervisorguide.md`
9. `experiments/report1_evidence_map.md`
10. `report1/references/reference.md`
11. `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex`
12. `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
13. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
14. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
15. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
16. `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`
17. `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex`
18. `report1/phd-thesis-template-2.4/thesis.tex`
19. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`
20. `report1/phd-thesis-template-2.4/References/references.bib`
21. `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`
22. `report1/requirements/SciComp_Mphil_Handbook-2025-26.pdf`
23. `report1/draft2.pdf`

If PDF text extraction is needed, use `pdftotext` or another local text
extraction method. Do not quote long passages from the PDFs; use them to verify
requirements and prior draft state.

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison.

Use the Report 1 skills with the same restraint as
`report1/planning/manuscript_outline.md`: each section worker should use at
most two drafting skills. Read these skills before assigning or reviewing the
corresponding work:

```text
report1/skills/writing-introduction/SKILL.md
report1/skills/academic-english-style/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/report1-context/SKILL.md
```

Use `writing-introduction` as the primary drafting skill for every Chapter 1
worker. Use `report1-context` when scope, word budget, or MHD/Euler boundary is
being checked. Use `academic-english-style` for hedging and sentence control in
style review or when a worker's assigned section explicitly needs it. Use
`avoiding-ai-flavor` as a paragraph-level acceptance gate after drafting, not
as a substitute for student rewriting. Do not ask a worker to stack all four
skills into one prose pass.

Skill assignment by worker:

| Worker | Drafting skills | Final gate |
|---|---|---|
| A, context and motivation | `writing-introduction` + `academic-english-style` | `avoiding-ai-flavor` paragraph check |
| B, precision and hardware problem | `writing-introduction` + `academic-english-style` | `avoiding-ai-flavor` paragraph check |
| C, scope and contribution | `writing-introduction` + `report1-context` | `avoiding-ai-flavor` paragraph check |
| D, roadmap | `writing-introduction` + `report1-context` | `avoiding-ai-flavor` paragraph check |

The main-agent final review may use `academic-english-style` and
`report1-context` together to check hedging, word budget, and scope, then apply
`avoiding-ai-flavor` as the last prose-quality gate.

### Main-agent role

The main agent must not directly rewrite Chapter 1 prose. Its role is:

- read the required context;
- create or repair the Chapter 1 marker skeleton if needed;
- dispatch one subagent per section, serially;
- review each returned section before dispatching the next worker;
- if a section fails the requirements, send it back to the same worker or a new
  worker with a focused repair prompt;
- maintain chapter-level continuity notes between workers;
- run the final three-round self-check and compile verification.

The main agent may make only mechanical non-prose changes if needed for
integration: preserving markers, repairing section headings, fixing
cross-reference syntax, or removing leftover TODO comments. Any substantive
prose, citation-context change, or roadmap rewrite must be made by the owning
section worker.

Tell every worker:

```text
You are not alone in the codebase; do not revert or overwrite edits outside your assigned Chapter 1 section.
```

Workers run serially. Never allow two workers to edit `chapter1.tex` at the
same time.

### Required Chapter 1 section skeleton

The current Chapter 1 may still contain TODO comments and no markers. The main
agent should create this marker skeleton before dispatch if it is absent:

```latex
\section{Context: HRSC Schemes for Discontinuous Compressible Flows}
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>

\section{Precision and Hardware Reproducibility Problem}
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>

\section{Report Scope and Contribution}
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>

\section{Report Structure}
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Do not leave TODO, "drafting comment", LLM directive text, or worker
instructions in manuscript-facing Chapter 1.

### Chapter 1 ownership

Chapter 1 owns:

- broad motivation: why compressible Euler simulations and HRSC methods matter;
- practical speed/accuracy framing before the precision and GPU discussion;
- a compact statement of the precision/hardware reproducibility problem;
- a selective pointer to CFD reduced/mixed-precision and GPU context;
- Report 1 aim, scope, contribution, and evidence boundary;
- a report roadmap consistent with the final active chapter structure.

Chapter 1 must not:

- derive Euler, finite-volume, MUSCL-Hancock, HLLC, CFL, or MHD equations;
  Chapters 2 and 3 own those;
- define the implementation route, design matrix, metrics, reference mapping,
  compiler flags, or matched-device protocol; Chapter 4 owns those;
- report numerical values or interpret figures/tables; Chapter 5 owns those;
- synthesize results, limitations, or recommendations in Chapter 6/7 style;
- claim MHD validation or completed MHD evidence;
- make broad claims that fp32 is generally adequate or that hardware has no
  effect;
- rely on Verificarlo `p32` as IEEE fp32 evidence;
- use internal planning language such as "chapter owner" or "evidence lock" in
  manuscript prose.

Working word target: 500-600 Overleaf-counted words. This is a hard
introduction budget, not a writing entitlement. Suggested section budgets:

- 1.1 context and applications: 125-160 words.
- 1.2 precision, CFD reduced precision, CUDA/GPU motivation: 160-210 words.
- 1.3 scope and contribution: 140-175 words.
- 1.4 report structure: 70-95 words.

No figures or tables should be needed in Chapter 1. Do not add result numbers.

### Draft 2 and current-manuscript state

Draft 2 already had a short introduction with the four current section
headings. The supervisor's feedback indicates that it was too thin in three
places:

- it did not sufficiently explain why compressible Euler equations are solved,
  including applications and the need for simulations to be fast but accurate
  enough for experimental or benchmark comparison;
- it did not give enough background on finite-precision or mixed-precision CFD
  work, and general floating-point sources alone are not enough;
- it did not give enough CUDA/GPU background or explain why fp32/fp64
  performance and arithmetic behaviour motivate measurement.

The current manuscript has substantial material in Chapters 2--5, a placeholder
Chapter 6, and a draft Chapter 7. Chapter 1 must therefore open the report
without duplicating those chapters. Its roadmap must be checked against
`thesis.tex`: if Chapter 7 remains included, describe Chapter 6 as discussion
and Chapter 7 as a short conclusion; if Chapter 7 is removed or merged later,
update Section 1.4 accordingly.

### Project-brief and handbook compliance

Chapter 1 contributes to the project brief's Literature review and background
[20%] category and to the Quality of write-up [20%] category. It should make
the report's central question visible before the technical chapters:

```text
How do floating-point precision and hardware/backend choices affect the saved
solutions of a Riemann-solver-based HRSC Euler validation suite, when
differences are interpreted against reference or discretisation error scales?
```

The handbook requires a connected account of the student's work, clear
structure, appropriate length, and properly acknowledged sources. Chapter 1
should therefore be selective and scope-setting, not a literature catalogue.

### Pre-dispatch plan audit

Before creating the Chapter 1 marker skeleton, the main agent must explicitly
check this prompt against the governing requirements:

| Requirement source | Chapter 1 prompt coverage to confirm |
|---|---|
| Project brief, Report 1 literature/background | C1 motivates Euler/HRSC, floating-point arithmetic, hardware/compiler/thread-order effects, and points to C2/C3 for governing equations and finite-volume derivation. |
| Project brief, validation/code categories | C1 states the question and scope only; C4/C5 retain the design matrix, CPU/GPU quantification, fp32/fp64 comparison, and reproducibility harness details. |
| Project brief tools section | C1 may mention Verificarlo/RAPTOR only as precision-diagnostic context; it must not claim either tool produced direct IEEE fp32 evidence or completed validation. |
| Supervisor Chapter 1 feedback | C1 must add applications/speed-accuracy motivation, CFD finite/mixed precision literature, and CUDA/GPU background. |
| `report1/skills` | C1 uses `writing-introduction` for the funnel, `report1-context` for scope, `academic-english-style` where hedging is needed, and `avoiding-ai-flavor` as a gate; no raw AI prose is accepted. |
| Chapter responsibility lock | C1 remains problem entry, scope, contribution, and roadmap; method, implementation, results, and discussion content remain in C2--C7. |

If any row above is not covered, repair this prompt before dispatching workers.

### Hard rules

- Do not modify solver numerics, cfg defaults, experiment output formats, raw
  artifacts, or anything under `experiments/`.
- Do not write MHD as a completed Report 1 result.
- Do not use manuscript-facing internal labels: `week7`, `week8`, `week9`,
  `D1`, `D2`, `HLLC-fill`, `config12`, `LW12/config12`, `P1`, or `USE_GPU`.
- Use `ENABLE_CUDA`, not `USE_GPU`, if a CUDA build switch must be named.
- Prefer not to name build switches in Chapter 1; leave them to Chapter 4
  unless one is essential for scope.
- Do not treat Verificarlo `p32` as IEEE fp32.
- Do not use product-family hardware claims such as "enterprise Ampere versus
  consumer RTX 3000" unless the worker has a verified primary/vendor source and
  the main agent approves adding it. The default is a source-bounded general
  statement: fp32/fp64 throughput and device math behaviour can differ across
  GPU hardware, so this report measures rather than assumes reproducibility.
- Use author-name prose where natural: Toro for HRSC/Riemann-solver context,
  Brogi et al. for CFD reduced/mixed-precision context, Wang/Xia/Chen for
  heterogeneous hybrid-precision finite-volume context, Bard and Dorelli for
  GPU MUSCL-Hancock/MHD project context, Goldberg/Higham/IEEE for
  floating-point background.
- Use citations only where they support a specific sentence. Do not decorate
  the introduction with broad citation clusters.
- AI-assisted prose must pass `avoiding-ai-flavor`: no generic filler,
  marketing tone, unsupported confidence, repeated template rhythm, or
  paragraph that could fit an unrelated dissertation.

### Citation policy

Use `report1/references/reference.md` before adding or changing citations.
Workers may cite only existing keys from `References/references.bib` unless the
main agent verifies and adds a new entry from a primary source.

Likely allowed citation roles for Chapter 1:

| key | use in Chapter 1 |
|-----|------------------|
| `toro2009` | HRSC, finite-volume/Riemann-solver context, Euler shock-tube background |
| `liska_wendroff_2003` | 2D Euler benchmark family if naming the validation scope |
| `goldberg_1991` | floating-point rounding and non-associativity framing |
| `ieee754_2019` | binary32/binary64 standards if formats are named |
| `higham_2002` | numerical error and stability language |
| `brogi_etal_2024` | CFD-specific reduced/mixed-precision background and case-specific validation need |
| `wang_xia_chen_2025` | heterogeneous hybrid-precision finite-volume compressible-flow context |
| `bard_dorelli_2014` | GPU MUSCL-Hancock and MHD longer-project motivation |
| `denis_etal_2016`, `parker_1997` | Verificarlo/MCA only if introduced in the introduction; normally Chapter 2/4 can own these |

Do not cite AMReX in Chapter 1 unless AMReX is explicitly discussed. The
current Report 1 route is stand-alone code.

RAPTOR is named in the project brief as a possible precision-exploration tool,
but this prompt does not assume a verified bibliography key or any Report 1
RAPTOR result. If Worker B wants to name RAPTOR in manuscript prose, it must
state that it is project context or a possible tool only, not evidence used in
Chapter 5; if a citation is needed, the worker must stop and ask the main agent
to verify the source before adding a BibTeX entry.

Before dispatch, the main agent should check that the likely keys exist:

```powershell
rg -n -F "{toro2009," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{liska_wendroff_2003," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{goldberg_1991," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{ieee754_2019," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{higham_2002," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{brogi_etal_2024," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{wang_xia_chen_2025," report1/phd-thesis-template-2.4/References/references.bib
rg -n -F "{bard_dorelli_2014," report1/phd-thesis-template-2.4/References/references.bib
```

If a key is missing, do not cite it until it is verified and added.

### Marker protocol and pre-step snapshot

Before dispatching any worker:

1. Snapshot the current `chapter1.tex` to a temporary file under the repository
   (for example
   `report1/phd-thesis-template-2.4/Chapter1/.snapshots/preC1.tex`, not
   committed) so that a failed worker edit can be reverted byte-for-byte.
2. Create or repair the Chapter 1 marker skeleton if needed.
3. Confirm with:

```powershell
rg -n "% <<SECTION_[1-4]_(BEGIN|END)>>" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

Expected: exactly 8 marker lines.

Tell every worker this exact instruction, in addition to the assignment:

> Read the current `chapter1.tex` in full. Locate exactly your assigned
> markers `% <<SECTION_n_BEGIN>>` and `% <<SECTION_n_END>>`. Replace only
> the complete marker-bounded region, including the BEGIN and END marker
> lines. The new content must keep both marker lines verbatim at the start
> and end. Do not touch text outside those markers. Do not rename markers.
> Do not insert new `\section{}` commands; the section heading is already
> outside your region. If your assigned markers do not appear exactly once
> each, stop and report.

After each worker returns, the main agent verifies:

- all four BEGIN markers and all four END markers still exist exactly once;
- the other three marker-bounded regions are byte-identical to the pre-worker
  snapshot;
- the worker's region begins with its BEGIN marker and ends with its END
  marker.

If any check fails, restore `chapter1.tex` from the snapshot and re-dispatch
that worker with a focused defect prompt.

---

## Worker A: Section 1.1 Context: HRSC Schemes for Discontinuous Compressible Flows

Assigned region:

```latex
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>
```

Goal:

- Open with why compressible-flow simulations are needed, not with floating
  point. Mention practical simulation constraints: flows may contain shocks,
  contacts, and rarefactions, and the numerical result must be accurate enough
  to compare with experiments, exact Riemann references, or benchmark
  references while still running in feasible time.
- Give a small number of application contexts without overdeveloping them:
  high-speed gas dynamics, aerospace/engineering compressible flow, and the
  later plasma/MHD direction are enough. If a worker cannot support a specific
  application with an allowed citation, write it generically and do not add a
  source-free detailed claim.
- Introduce HRSC finite-volume/Riemann-solver methods as the suitable numerical
  setting, using Toro as the main source.
- End with the transition: the same features that make HRSC useful also make
  precision/backend reproducibility worth measuring.

Constraints:

- Keep this section about 125-160 words.
- Do not derive the Euler equations; Chapter 2 owns that.
- Do not name HLLC unless the sentence is necessary. Chapter 3 introduces the
  solver.
- Do not report result values or validation cases in detail.

Worker summary must report:

- how compressible-flow applications were introduced;
- where the speed/accuracy tradeoff appears;
- which citation supports the HRSC/Riemann-solver statement.

---

## Worker B: Section 1.2 Precision and Hardware Reproducibility Problem

Assigned region:

```latex
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Goal:

- State the reproducibility problem: two runs can implement the same nominal
  finite-volume algorithm but differ because binary format, compiler
  transformations, fused operations, approximate device operations, or
  parallel ordering change rounded arithmetic.
- Give the supervisor-requested background on finite-precision or
  mixed-precision CFD. Use Brogi et al. as the default CFD-specific source and
  Wang, Xia, and Chen as an optional second source for compressible
  finite-volume/hybrid-precision context. Make clear that these papers motivate
  case-specific validation; they do not prove this report's fp32 adequacy.
- Mention CUDA/GPU motivation in one or two sentences. Define CUDA briefly as
  the NVIDIA GPU programming model/backend used in the project if it is first
  introduced here; otherwise leave the fuller definition to Chapter 4.
- Explain that fp32/fp64 performance and arithmetic behaviour can differ across
  GPU hardware, so CPU/GPU and fp32/fp64 effects should be measured rather
  than assumed. Do not name specific GPU product families unless a verified
  source is added.
- Mention precision-diagnostic tooling only at introduction level. If
  Verificarlo or RAPTOR is named, frame it as project precision-diagnostic
  context and hand detailed definitions to Chapter 2 or Chapter 4. State
  explicitly that direct fp32 evidence in this report comes from real
  fp32/fp64 runs, not from virtual-precision diagnostics.
- Use Goldberg, IEEE 754, or Higham only for general floating-point mechanisms,
  not as CFD-specific evidence.

Constraints:

- Keep this section about 160-210 words.
- Do not list compiler flags; Chapter 3/4 own the flags.
- Do not explain Verificarlo/MCA mechanics here; Chapter 2/4 own the
  definitions and equations. If virtual precision is mentioned, state that it
  is not IEEE fp32.
- Do not claim that hardware differences are always large.

Worker summary must report:

- which CFD precision papers were used and what each supports;
- how CUDA/GPU background was introduced;
- whether Verificarlo/RAPTOR was mentioned, and if so how it was bounded;
- whether any hardware-specific performance claim was avoided or flagged;
- whether the section remains introduction-level rather than Chapter 2 detail.

---

## Worker C: Section 1.3 Report Scope and Contribution

Assigned region:

```latex
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>
```

Goal:

- State the aim in one clear sentence: Report 1 measures how precision and
  hardware/backend choices affect a Riemann-solver-based HRSC method on a
  controlled Euler validation suite.
- Make the scope boundary explicit:
  - Report 1 evidence is Euler ideal-gas validation in 1D and 2D.
  - MHD motivates the longer project and Report 2 direction.
  - No MHD validation is claimed in Report 1.
- State contributions in restrained terms. Use either one compact paragraph or
  a short two- or three-item list. Acceptable contribution content:
  - selected Euler validation evidence for the stand-alone HRSC solver;
  - quantified fp32/fp64 and matched CPU/GPU saved-output comparisons;
  - measured sensitivity to selected compiler, solver, and branch-rule
    variations.
- Do not include numerical values; Chapter 5 owns them.
- Avoid novelty claims. Do not write "first", "novel", "comprehensive", or
  similar language unless a citation and evidence support the claim, which is
  unlikely here.

Constraints:

- Keep this section about 140-175 words.
- Do not describe the design matrix, exact metrics, or reference downsampling;
  Chapter 4 owns those.
- Do not use internal labels or "evidence lock" language.
- Keep claims bounded to tested cases and saved outputs.

Worker summary must report:

- the final aim sentence;
- the exact MHD boundary wording;
- whether contributions were written as prose or a list;
- any claim that was intentionally hedged.

---

## Worker D: Section 1.4 Report Structure

Assigned region:

```latex
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Goal:

- Write a compact roadmap in ordinary report language.
- Make the roadmap consistent with the active `thesis.tex` includes and the
  current Chapter 6/7 decision.
- If Chapter 7 remains active, use this structure:
  - Chapter 2 reviews governing background and literature context.
  - Chapter 3 defines the numerical method.
  - Chapter 4 defines the implementation and experimental design.
  - Chapter 5 reports validation and precision/hardware results.
  - Chapter 6 discusses interpretation and limitations.
  - Chapter 7 gives a short conclusion and Report 2 direction.
- If Chapter 7 is removed or merged later, update this section so it does not
  promise a separate conclusion chapter.

Constraints:

- Keep this section about 70-95 words.
- Do not use "Chapter 4 owns..." or other internal planning phrasing.
- Do not preview result numbers.
- Do not describe the abstract, front matter, or appendices unless they are
  relevant to the report structure.

Worker summary must report:

- whether Chapter 7 was active in `thesis.tex`;
- the roadmap wording for Chapter 6/7;
- confirmation that no internal planning language remains.

---

## Main-Agent Integration Review

After each worker:

1. Re-read only the edited section and one neighbouring section heading.
2. Check that the section satisfies its worker goals.
3. Check that the section does not duplicate Chapter 2/3/4/5/6/7
   responsibilities.
4. If the section fails, dispatch a focused repair worker before continuing.
5. Record a short continuity note for the next worker.

After all workers:

1. Read the full Chapter 1 for funnel structure:
   context -> reproducibility problem -> gap/scope/contribution -> roadmap.
2. Confirm the introduction follows the current state of Chapters 2--7 without
   overpromising completed discussion or conclusion work.
3. Confirm the supervisor's Chapter 1 feedback is visibly addressed:
   applications/speed-accuracy motivation, CFD precision literature, and
   CUDA/GPU background.
4. Confirm no Draft 2 prose has been copied without rewriting.
5. Confirm no TODO/drafting comments remain in manuscript-facing text.

---

## Required Three-Round Self-Check

Do not stop after worker edits. Complete all three self-check rounds. If any
round scores below 95/100, dispatch a focused repair worker and rerun that
round once. If after three full rounds the chapter still cannot reach 95/100,
stop and explain exactly which requirement blocks it.

### Round 1: Brief, Handbook, and Supervisor Coverage

Score Chapter 1 against the project brief, handbook, `manuscript_outline.md`,
and `supervisor_feedback_map.md` Chapter 1 requirements.

Checklist:

- Introduction has a narrowing funnel from compressible HRSC context to the
  precision/hardware question.
- 1.1 explains why compressible Euler-type simulations are run and why fast
  but accurate computation matters.
- 1.1 introduces HRSC/Riemann-solver methods without deriving them.
- 1.2 includes CFD-specific finite/reduced/mixed precision background, not only
  Goldberg/IEEE/Higham.
- 1.2 includes CUDA/GPU motivation at introduction level.
- 1.2 avoids unverified product-family performance claims.
- 1.3 states aim, scope, and contribution without result numbers.
- 1.3 keeps MHD as context/future work only.
- 1.4 roadmap matches the active chapter structure and avoids internal
  planning phrasing.
- Chapter remains inside the 500-600 word target or reports a justified local
  overrun for main-agent compression.

Pass threshold: 95/100.

### Round 2: Citation, Style, and Voice Audit

Checklist:

- Every citation supports a specific sentence and appears in
  `References/references.bib`.
- Brogi et al. and optional Wang/Xia/Chen are used only as CFD precision
  background, not as evidence for this report's solver.
- Bard and Dorelli are used only for GPU/MUSCL-Hancock/MHD project context if
  included.
- Author-name prose is used where it improves readability for specific methods
  or sources.
- The introduction is selective, not a miniature literature review.
- Prose passes `writing-introduction`: context, gap, aim, and scope are placed
  in that order.
- Prose passes `academic-english-style`: careful hedging, no journalistic
  phrasing, no unsupported certainty.
- Prose passes `avoiding-ai-flavor`: no generic filler, marketing confidence,
  repeated template rhythm, or paragraph detached from this project.

Pass threshold: 95/100.

### Round 3: Mechanical, LaTeX, and Forbidden-Token Check

Run from repository root:

```powershell
git diff --check -- report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

Expected: no whitespace or patch-format warnings introduced by this pass.

```powershell
rg -n "TODO|LLM|drafting comment|week7|week8|week9|D1|D2|HLLC-fill|config12|LW12/config12|P1|USE_GPU|fp32 L1 error|fp64 L1 error" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

Expected: no manuscript-facing hits.

Check for Verificarlo/fp32 wording if those terms appear:

```powershell
rg -n -U -i "p32(.|\n){0,120}IEEE fp32|IEEE fp32(.|\n){0,120}p32" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

Expected: no hit equating virtual p32 with IEEE fp32.

Check citation keys:

```powershell
rg -n -F "\cite" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
rg -n "^@" report1/phd-thesis-template-2.4/References/references.bib
```

Check roadmap against active includes:

```powershell
rg -n "\\include|\\input|Chapter[1-7]" report1/phd-thesis-template-2.4/thesis.tex
rg -n "Chapter~[2-7]|Chapter [2-7]" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

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

Pass threshold: no new Chapter 1 LaTeX errors, no forbidden-token hits, no
undefined citation introduced by this pass.

---

## Strict scoring and improvement iteration

After the three self-check rounds, the main agent scores Chapter 1 against the
Report 1 requirements before claiming it is ready. Use a 100-point rubric:

| Area | Points | What to check |
|------|--------|---------------|
| Supervisor-feedback coverage | 25 | Applications/speed-accuracy motivation, CFD precision literature, and CUDA/GPU background are all present. |
| Introduction funnel and scope | 20 | Context narrows to gap, aim, contribution, and roadmap without method/result duplication. |
| Evidence boundary | 20 | Euler-only Report 1 scope, MHD future boundary, no unsupported fp32/hardware generalisation. |
| Citation discipline | 15 | Every citation supports a sentence; CFD precision and GPU sources are used for the right role. |
| Style and word budget | 10 | Prose is concise, non-generic, and within 500-600 words. |
| LaTeX and forbidden-token correctness | 10 | Markers preserved, no TODO/internal labels, citations compile, roadmap matches `thesis.tex`. |

Iterate:

1. Write a short self-review note with the score breakdown and top defects.
2. Address the highest-impact defects. Use direct integration edits only for
   marker/whitespace/citation-key syntax issues; re-dispatch the owning worker
   for new section-level prose.
3. Re-score with the same rubric.
4. Repeat until either the score is at least 95/100 or three improvement rounds
   have completed.

If the score remains below 95/100 after three rounds, stop iterating and report
exactly which requirement blocks it. Classify each remaining limitation as one
of:

- writing/editing issue that can still be improved without new sources;
- citation/source issue that needs a verified additional reference;
- structural issue caused by unresolved Chapter 6/7 organisation.

After the final review, explicitly ask: "What would most improve Chapter 1 if
more time were available?" Answer it in the final response. Do not invent
sources or results.

---

## Final response format

Respond in Chinese with:

- which C1 sections were drafted or revised by which worker;
- how the supervisor's Chapter 1 feedback was addressed;
- how Draft 2 was used without copying old prose;
- what citations/sources were used and what each supports;
- whether any worker needed a repair pass;
- the three self-check scores and outcomes;
- the final rubric score breakdown and number of improvement rounds completed;
- compile/check results;
- remaining dependencies on Chapter 2, Chapter 6/7, or the References
  capitalization pass.

Do not claim the full report is finished. Do not commit.
