# reportagents.md — Working Requirements for Cambridge MPhil Scientific Computing Project Report 1

This file is a working synthesis for any AI agent or human collaborator working on **Report 1** of the dissertation project *"Effect of Floating-Point Precision and Hardware on HRSC Schemes"*. It focuses on report writing requirements, marking expectations, and thesis-style presentation. It is not a substitute for the official PDFs. Where a writing or assessment rule is contested, the official project brief and handbook win.

Binding sources (consult before deviating):
- `Effect of Floating-Point precision and hardware on HRSC Schemes.pdf` — project brief from supervisor Dr Philip Blakely (CSC). Defines scope, required content, Report 1 marking breakdown, and supervisor-specified references.
- `SciComp_Mphil_Handbook-2025-26.pdf` — course handbook. Defines word limit, layout, assessment process, writing expectations, and key dates.
- `../docs/requirement/Coding_and_submission_guidelines.pdf` — use only for writing-integrity points that affect the report text, especially TurnItIn anonymity and AI-generated text boundaries.

Supporting sources:
- `phd-thesis-template-2.4/` — CUED LaTeX template. The expected typesetting framework.
- `Project-Report-1-example.pdf` — unrelated example report (Davison-Petch 2024, contrails / IMEX). Use **structure only**, not content; topic is not ours and it does not create requirements.

---

## 1. Project identity

- **Title (working):** Effect of Floating-Point Precision and Hardware on HRSC Schemes
- **Degree:** MPhil in Scientific Computing, Department of Physics, University of Cambridge
- **Supervisor:** Dr Philip Blakely (CSC)
- **Project type:** *Code development and exploration* (per brief). Not theoretical.
- **Report 1 due:** Friday 29/05/2026 (handbook p.15)
- **Mid-term presentation:** week of 01–05/06/2026; 10-minute presentation followed by 5 minutes of questions/discussion, and comments feed into Report 1 evaluation (handbook pp.10, 13, 15).
- **Report 2 due:** Friday 07/08/2026 (handbook p.15)
- **Assessment weight:** each project report carries **25%** of the total overall credit (handbook pp.10, 25).
- **Assessment marking:** by two project assessors who are **not** the supervisor and are not anyone closely associated with the supervision process (handbook p.10).

---

## 2. Hard constraints (non-negotiable)

### 2.1 Word count

- **Maximum: 7,500 words** per report. Current course clarification for this project: the controlling count is Overleaf Word Count / counted text; tables and figure captions are not counted. Bibliography is excluded.
- Penalty schedule (handbook p.11):
  - up to +5% (≤7,875 words): no penalty
  - +5% to +10% (7,876–8,250): **−10 percentage points**
  - +10% to +20% (8,251–9,000): **−20 percentage points**
  - +20% or more (9,001+): **resubmit within 48 h**, plus the above penalty if still over after resubmission.
- The figure of merit is the Overleaf counted-word result, not pages and not a `texcount` mode that includes table cells or figure captions.
- Maintain a defensible Overleaf wordcount declaration for the final report.

### 2.2 Page layout

- 12-point font (handbook p.11)
- 1.5 or double line spacing
- Margins at least 2 cm on all sides
- Use the local CUED template `phd-thesis-template-2.4/` for the title page. If manually checking the generated page, the handbook rule is: **author's name**, **approved** project title, and degree at the **top**; supervisor name at the **bottom right-hand corner** (handbook p.11).

### 2.3 Front matter

Required front matter:

1. **Title page** — generated from the CUED template, with author's name, approved title, and degree at the top; supervisor name at the bottom right-hand corner.
2. **Declaration** — include the handbook wording (handbook p.12):
   > "This project report is substantially my own work and conforms to the University of Cambridge's guidelines on plagiarism. Where reference has been made to other research this is acknowledged in the text and bibliography."
3. **Wordcount declaration** — maintain a reliable Overleaf Word Count value for the counted text, excluding bibliography and excluding tables/figure captions under the current course clarification.

Template/example-derived conventions, useful but not binding unless CSC admin specifies them:

1. Include "Report 1", Department of Physics, University of Cambridge, "This dissertation is submitted for the degree of Master of Philosophy", and month/year on the title page if using the CUED template. These are template/example conventions, not independent handbook requirements.
2. Include a brief acknowledgements page if appropriate.
3. Include a concise abstract that states the question, methods, headline findings, and contribution.
4. Include table of contents, list of figures, and list of tables if the template generates them cleanly.

The template should handle most front-matter mechanics. Do not spend report-planning effort redesigning the title page; spend it on content, evidence, and structure.

### 2.4 Authorship, anonymity, and finality

- Project reports must be connected accounts of the student's own work, written by the student (handbook p.11).
- The project report title page must use the author's name as required by the handbook. Do not use a Blind Grading Number or BGN as the author identifier.
- AI-generated text must not be submitted as original assessed work. AI assistance, if used, must remain within University and course expectations; the final report must be the student's own scientific writing.
- Changes made to the content of Report 1 after its first submission will not be marked. Later developments can be explained in Report 2 rather than rewriting Report 1 retrospectively (handbook p.11).

---

## 3. Report 1 content allocation and marking emphasis

For Report 1 content allocation, follow the project brief's five **20%** categories below. The handbook also defines the general criteria that assessors use across the project reports, so a strong Report 1 must satisfy both the brief-specific category split and the broader handbook criteria.

### 3.1 Literature review and background [20%]

This section should establish why the project is scientifically and computationally worth doing. It must not become a generic textbook survey.

Must cover:
- Compressible Euler equations for ideal gas as the Report 1 validation system.
- Ideal-MHD equations as the wider project target, including why divergence control matters.
- Finite-volume HRSC methods as the natural numerical setting for discontinuities and shocks.
- Floating-point arithmetic as a source of reproducibility and accuracy questions across precision, hardware, compiler options, and parallel ordering.

Writing standard:
- Move from broad context to this project's exact question: how precision and hardware affect HRSC solutions.
- Use references to support choices, not to decorate paragraphs. A useful citation should explain why a method, benchmark, or error concept matters here.
- Keep MHD background proportional. Report 1 can motivate MHD, but the load-bearing validation evidence is Euler unless actual MHD results are shown.
- End the background with the gap Report 1 addresses: a controlled, quantified comparison of Euler HRSC results across CPU/GPU and fp32/fp64.

### 3.2 Mathematical theory [20%]

This section should show that the method is understood, not merely implemented.

Must cover:
- Conservation-law form, cell averages, numerical fluxes, and the update formula used in the finite-volume method.
- Description of the chosen second-order explicit method. The brief writes: "Description of the chosen explicit method, such as MUSCL-Hancock or WAF (must be Riemann-solver based)." **MUSCL-Hancock is strongly suggested** by the brief because Riemann-solver complexity is of particular interest; SLIC alone is not suitable. WAF is named as the only other acceptable example in the brief's marking text. Any equivalent method must still be at least second order and Riemann-solver based.
- Riemann solver choice. The brief says HLLC or the exact Riemann solver are most suitable; if another approximate solver is used, justify the choice rather than presenting it as the brief's preferred option.
- Limiter/reconstruction choices, CFL condition, and any assumptions needed for stability or positivity.
- MHD-specific variations at conceptual level only where relevant: different Riemann solvers, divergence-cleaning approaches, or constrained transport.
- Algorithmic decision points that could affect later precision studies, such as `<` versus `<=` in wave-speed tests, exact-solver tolerances, limiter branches, and reductions.

Writing standard:
- Define variables before using them; keep notation consistent across equations, captions, and text.
- Include enough equations or pseudocode for an assessor to understand the method without reading the source code.
- Distinguish mathematical truncation error, discretisation error, floating-point roundoff, and implementation/hardware differences.
- State limitations honestly: e.g. which discontinuities are expected to be difficult, where exact solutions exist, and where convergence-based references are needed.

### 3.3 Code description [20%]

This is a report-writing section about the implementation choices that affect the scientific evidence.

Must cover:
- The implementation route: AMReX if used, or stand-alone code if that is the chosen route. Explain why the choice supports CPU/GPU comparison, precision switching, and controlled experiments.
- The algorithmic structure at report level: reconstruction, Riemann solve, update, boundary conditions, output quantities, and where fp32/fp64 or CPU/GPU variants enter.
- A short source-code explanation of the most important implementation path, supported by pseudocode rather than raw code listings. Anchor this explanation to `src/main.cpp`, `src/euler/euler_solver.cpp`, `src/euler/hancock.hpp`, `src/euler/muscl.hpp`, `src/euler/hllc.hpp`, `src/gpu/euler_gpu_solver.cu`, `src/gpu/euler_kernels.cu`, `src/core/boundary.hpp`, and `src/utils/io.hpp`.
- How the same nominal algorithm is kept comparable across hardware and precision. The assessor needs to know what is intentionally held fixed and what is varied.
- The experiment organisation used to support claims: test-case matrix, precision matrix, hardware matrix, compiler-option or tolerance variations if used.
- How the exact or appropriately converged reference solution is determined. This is load-bearing because every accuracy comparison depends on the reference.

Writing standard:
- Explain design choices in terms of evidence quality: reproducibility, comparability, and error measurement.
- Keep operational details out unless they are necessary to interpret a result.
- Do not describe implementation features that do not affect the reported numerical results.
- If a method differs between CPU and GPU, say so explicitly and explain how that affects interpretation.

### 3.4 Validation [20%]

This is the most evidence-heavy section. It should read as a controlled validation study, not as a gallery of plots.

Must cover:
- At least **four test cases** for Euler ideal gas, including supersonic waves; the set must include **both 1D and 2D** tests.
- Each test evaluated on **both CPU and GPU**.
- Single- and double-precision accuracy comparison.
- Quantified CPU-GPU differences. Visual similarity is not enough.
- Reference-solution strategy for each test: analytic solution where available; otherwise sufficiently converged numerical reference or published benchmark comparison.

Writing standard:
- Start with a compact validation matrix: test name, dimension, physical feature, reference solution, metrics, hardware, precision.
- For each test, state the purpose before showing results. Example purposes: contact preservation, shock resolution, rarefaction, 2D interaction, supersonic structure, hardware sensitivity.
- Use numerical metrics consistently, such as L1/L2/L∞ error, max absolute difference, conserved-quantity drift, shock/contact position error, or normed CPU-GPU difference.
- Pair plots with tables. Plots show structure; tables carry the quantitative comparison.
- Discuss failures, near-equalities, and ambiguous differences. A small CPU-GPU difference still needs a scale: relative to solution magnitude, discretisation error, or fp32/fp64 gap.
- Avoid claiming hardware effects from a single picture. If a difference grows over time, quantify the time evolution.

### 3.5 Quality of write-up [20%]

This category is not cosmetic. It controls whether assessors can follow the argument and trust the evidence.

Must cover:
- A clear report narrative: motivation -> method -> implementation choices and pseudocode -> validation evidence -> bounded conclusions.
- Logical section order and signposting. Each chapter should state its role in answering the project question.
- Figure and table quality: self-contained captions, labelled axes, units or nondimensional quantities, readable legends, and consistent notation.
- Complete but selective referencing. The bibliography should support the actual argument rather than display everything read.
- Explicit links between claims and evidence. Avoid leaving the assessor to infer why a plot or table matters.

Writing standard:
- Use precise scientific verbs: "compares", "quantifies", "bounds", "indicates", "is consistent with"; avoid promotional or absolute language.
- Do not hide uncertainty. The handbook explicitly rewards awareness and quantification of errors and ambiguities.
- Keep paragraphs topic-led. A paragraph should usually open with the claim or purpose, then give evidence.
- Prefer concise, specific sentences over broad academic filler.

### 3.6 Handbook general marking criteria

The handbook states that project reports, presentations, and viva should demonstrate:

1. Awareness of the background science and critical understanding of relevant literature.
2. Understanding of the computational techniques used, including limitations.
3. Accurate description, validation, and interpretation of computational results.
4. Awareness of errors and ambiguities in computational techniques, with quantification where appropriate.
5. Convincing conclusions based on the evidence presented.
6. Clear presentation, including structure, writing quality, figures/tables, length control, and consistent references.

To pass the research project component, the report should broadly meet these criteria; distinction-level work should meet them fully and make a useful contribution to the field (handbook p.14).

---

## 4. Suggested chapter structure for Report 1

Use `report1/manuscript_outline.md` as the detailed chapter-by-chapter writing plan. The structure below is the same final report order in compact form. Word allocation is illustrative — adjust to evidence, never to fill a quota.

| Chapter | Topic | Approx. words (hard upper) | Anchors |
|---|---|---|---|
| 1 | **Introduction** — context, gap, aim, scope, report structure | 600-720 (720) | brief §3.1 motivation |
| 2 | **Background and governing equations** — compressible Euler equations, ideal-MHD context (≤ 140 w), HRSC background, floating-point reproducibility (300-360 w) | 780-880 (880) | brief §3.1 bullets 1-4 |
| 3 | **Numerical method** — finite-volume framework, MUSCL-Hancock, HLLC, limiter/stability choices, precision-sensitive decision points, MHD bridge (≤ 140 w) | 1,080-1,220 (1,220) | brief §3.2 |
| 4 | **Implementation and experimental design** — stand-alone route, key code path with pseudocode (pseudocode IS counted), comparability principle, test matrix incl. supersonic column, reference-solution methodology | 1,000-1,130 (1,130) | brief §3.3 |
| 5 | **Validation and precision results** — selected Euler cases (Sod, Toro3, Toro5, LW3, LW12), CPU/GPU comparison with toolchain footnote, fp32/fp64 quantification, compiler/branch/solver variation, time-resolved drift | 1,750-1,900 (1,900) | brief §3.4 |
| 6 | **Discussion** — synthesis, precision effects relative to numerical error (incl. Verificarlo virtual-precision regional interpretation), hardware/implementation sensitivity, limitations | 600-720 (720) | handbook criteria 3-5 |
| 7 | **Conclusion** — evidence-bounded findings and next project direction | 330-430 (430) | continuity with Report 2 |
| Abstract | Compact paragraph, ≥ 2 specific numerical values | 180-220 (220) | quality [20%] |
| Refs | Bibliography | — | excluded from word count |

Total per-chapter hard-upper sum: **7,220 words**, leaving ~280 words of cushion under the 7,500 Overleaf cap. Working drafting target: **≤ 7,400 Overleaf-counted words**. Tables and figure captions are not counted under the current course clarification, so the results chapter should target a figure/table-heavy density (modelled on the Davison-Petch example, about 20-24 main items). Pseudocode/algorithm-environment bodies ARE counted by Overleaf Word Count — the Ch. 4 cap above already absorbs this.

Use the CUED template for formatting. Do not let the template's default chapter files determine the intellectual structure; the chapter structure above should be driven by the project brief and evidence.

---

## 5. Required content checklist (mapped to brief)

Every item below must appear somewhere in the report. Tick as drafted.

**Background and theory**
- [ ] Compressible Euler equations in conservation form for the 1D and 2D settings used in validation.
- [ ] Ideal-MHD equations with divergence-free constraint on B.
- [ ] Finite-volume derivation: cell averages, fluxes, conservation form.
- [ ] Floating-point arithmetic: IEEE-754 binary32 vs binary64, FMA, rounding modes.
- [ ] Hardware/compiler/thread-ordering effects on simple expressions (e.g. associativity of summation).

**Method**
- [ ] MUSCL-Hancock (or equivalent) algorithm spelled out.
- [ ] HLLC (or exact) Riemann solver derivation or summary.
- [ ] MHD divergence-control options discussed only as later-project context unless actual MHD evidence is added; do not present a chosen Report 1 MHD method without implementation and validation evidence.
- [ ] Summary of algorithmic decision points that could be varied: tolerances, `<` vs `<=`, etc.

**Implementation description in the report**
- [ ] Framework or implementation choice described only insofar as it affects the reported numerical method and evidence.
- [ ] Key implementation path explained with pseudocode, centred on CPU `step`/sweep logic and the corresponding GPU mirror.
- [ ] Single- and double-precision comparison setup described clearly.
- [ ] Reproducibility of the reported experiments explained at the level needed to support the written claims.
- [ ] Reference-solution determination explained (analytic where available; high-resolution convergence study otherwise).

**Validation (at least four Euler cases, 1D + 2D, CPU + GPU, fp32 + fp64, supersonic waves)**

- [ ] 1D test cases: main selected set includes Sod, Toro3, and Toro5; additional Toro rows may appear only as supporting evidence if their caveats are explained.
- [ ] 2D test cases: main selected set includes two Liska-Wendroff Riemann configurations, LW3 and LW12 (unified prose label; never "config12" or "LW12/config12"); shock-bubble is optional future/supporting evidence unless it receives the same CPU/GPU and fp32/fp64 treatment.
- [ ] Validation matrix table contains "supersonic Y/N (and which wave)" and "basis for supersonic label" columns; Toro3, Toro5, LW3, and LW12 are each marked Y with the supersonic wave named and supported by a Mach value, wave-speed diagnostic, initial-state source, or benchmark citation.
- [ ] Prose names supersonic wave structures at first mention of Toro3 (right-running supersonic shock), Toro5 (collision of supersonic shocks), LW3 (supersonic quadrant-interface shocks), and LW12 (supersonic quadrant-interface shocks). Brief's "include supersonic waves" requirement is satisfied four times in prose, not only in the matrix, and the evidence basis is auditable rather than asserted.
- [ ] For each: tabulated L1 / L2 / L∞ errors or equivalent quantitative metric.
- [ ] Single vs double precision comparison with quantified difference.
- [ ] CPU vs GPU comparison with quantified difference; CPU/GPU table carries a footnote stating the toolchain split (Windows BuildTools for Toro3/Toro5; Linux/WSL for Sod/LW3/LW12) and the matched-binary principle.

**Argument and assessment**
- [ ] Each of the five 20% brief categories has visible coverage.
- [ ] Each of the six handbook criteria is satisfied by explicit text or evidence.
- [ ] The conclusion answers the project question using Report 1 evidence only.
- [ ] Claims about precision or hardware are scaled against an error metric or reference solution.
- [ ] References are used where they change or justify a technical decision.

---

## 6. Writing style and prose quality

Refer to the writing skills toolkit in `report1/skills/`:

- `report1-context/SKILL.md` — the constraint summary (this file is the long form).
- `writing-introduction/SKILL.md` — narrowing-funnel structure for Chapter 1.
- `writing-literature-review/SKILL.md` — for the background chapter and the lit review embedded in the introduction.
- `writing-conclusion/SKILL.md` — for the closing chapter.
- `academic-english-style/SKILL.md` — canonical hedging ladder, I/we/passive choice, collocations.
- `editing-academic-prose/SKILL.md` — line-edit pass, wordiness, non-native slips.
- `scientific-writing-duke/SKILL.md` — Gopen-Swan reader-expectation principles for results paragraphs.
- `avoiding-ai-flavor/SKILL.md` — mandatory check for every AI-assisted paragraph before it is accepted into the manuscript; remove AI-flavored phrasing, extreme adjectives, generic filler, and topic-agnostic prose.

**Voice expectations:**

- The report should sound like careful, precise, student-authored scientific prose, not a marketing post or a generic polished AI draft.
- Every generated paragraph must pass `avoiding-ai-flavor/SKILL.md`, not only the final full draft. If a paragraph contains banned vocabulary, repeated triadic rhythm, empty framing, or a claim stronger than its evidence, rewrite it before using it.
- Hedge numerical claims. The handbook (p.14) marks for "**awareness of errors and ambiguities** and ability to quantify those errors" — over-confident claims work against this.
- Use concrete numerical-methods vocabulary (CFL, L1 error, condition number, ULP, FMA, bit-loss) rather than generic academese.
- Cite real numbers from the actual experiments. Do not paste illustrative placeholders.

**Forbidden words/phrases in the candidate's own voice** (see `avoiding-ai-flavor/SKILL.md` for the full table): *delve, leverage, harness, navigate (figurative), unlock, groundbreaking, unprecedented, transformative, revolutionary, seamless, remarkable, extremely, incredibly, absolutely, definitively, undoubtedly, robust (loose), comprehensive (loose), cutting-edge (loose), it is important to note that, tapestry, landscape (non-literal)*.

---

## 7. Report-writing checklist

Run through this list before treating the report draft as ready for supervisor or internal review.

**Word and format**
- [ ] Wordcount, checked with Overleaf Word Count and verified against the current course clarification, is **≤ 7,500 counted words**. Tables and figure captions are not included in the controlling value.
- [ ] 12-point font, 1.5 or double spacing, ≥ 2 cm margins.
- [ ] Title page: author's name, approved title, and degree at the top; supervisor at bottom right. Use the author's name, not BGN.
- [ ] Declaration page present with verbatim handbook wording; signed cover sheet included if required by the submission portal.
- [ ] No Blind Grading Number or BGN is used as the report author identifier.

**Content (project brief)**
- [ ] All five marking-scheme sections present and roughly balanced (5 × 20%).
- [ ] At least 4 Euler test cases required by the brief; the planned main set now uses 5 evidence-complete tests: Sod, Toro3, Toro5, LW3, and LW12 (unified prose label), each with CPU + GPU and fp32 + fp64 quantitative comparison. The set includes four explicitly supersonic entries (Toro3, Toro5, LW3, LW12); Sod is reported with its actual Mach/wave context rather than used as a bare supersonic tick.
- [ ] Reference-solution method explicitly described.
- [ ] Floating-point background section discusses hardware, compiler, thread ordering.
- [ ] Bibliography curated and verified (see `reference.md` after vetting it for hallucinations).
- [ ] Internal planning labels such as week numbers, D1/D2-style labels, and local experiment nicknames are not used in manuscript prose or captions. Use descriptive scientific labels instead.

**Style and integrity**
- [ ] Mandatory `avoiding-ai-flavor/SKILL.md` pass has been applied to every AI-assisted section — no extreme adjectives, no AI-tell verbs, no repeated triadic rhythm, no marketing tone, and no generic paragraph detached from this project.
- [ ] Every figure has a caption, units on axes, legend if multi-line.
- [ ] Every cited source appears in the bibliography; bibliography style consistent.
- [ ] Conclusions are bounded by the evidence actually shown in Report 1.
- [ ] Any later project direction is framed as future work rather than as completed Report 1 evidence.

---

## 8. What this file is not

- This file is **not** a substitute for reading the source PDFs. Read them.
- This file is **not** stable. When supervisor feedback or course administration updates contradict it, update this file and the corresponding section of `report1/skills/report1-context/SKILL.md`.
- This file is **only** for report-writing requirements and assessment expectations.

Last updated: 2026-05-17, derived from the 2025-26 handbook, the project brief, the coding guidelines, and the example report.
