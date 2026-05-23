# Abstract Dispatch Prompt

This prompt writes the final Report 1 abstract. It follows the dispatch style of
`report1/planning/old/chapter5_dispatch_prompt.md` and
`report1/planning/chapter7_dispatch_prompt.md`, but the scope is deliberately
smaller: replace the abstract placeholder only, after Chapters 1--7 are stable.

The supervisor explicitly flagged the Draft 2 abstract as LLM-directive text, so
this round must remove the placeholder and leave a student-authored scientific
abstract, not instructions.

---

## Master prompt

You are the main agent for the Report 1 abstract-writing round. Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

This round replaces only the body inside `\begin{abstract}` and
`\end{abstract}`. Do not edit Chapters 1--7, `thesis.tex`, bibliography files,
figures, raw experiment artifacts, solver code, cfg defaults, or anything under
`experiments/`.

### Required reading

Read these files before drafting:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/planning/reportagents.md`
5. `report1/planning/manuscript_outline.md` -- especially the Abstract block and
   the conclusion evidence lock
6. `report1/planning/supervisor_feedback_map.md` -- Front Matter / Abstract plus
   global style and terminology rules
7. `report1/planning/supervisorguide.md` -- supervisor comments on Draft 2
8. `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`
   -- project brief and Report 1 marking categories
9. `experiments/report1_evidence_map.md` -- trace every result claim
10. `report1/references/reference.md` -- confirm that the abstract should not
    introduce citations
11. `report1/draft2.pdf` -- confirm the old abstract was a TODO/LLM directive
12. `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex` -- aim, scope, and
    contribution language
13. `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
14. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
15. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
16. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
17. `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`
18. `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex` -- current compressed
    conclusion; the abstract should be consistent with it but not copy it
19. `report1/phd-thesis-template-2.4/Abstract/abstract.tex` -- placeholder to
    replace

### Required skills

Invoke these skills before drafting:

```text
report1/skills/academic-english-style/SKILL.md
report1/skills/report1-context/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
```

Use `academic-english-style` for hedge placement and concise scientific
phrasing. Use `report1-context` only to check Report 1 scope, word-count, and
marking constraints. Use `avoiding-ai-flavor` as a hard post-draft gate: the
abstract must not contain generic AI-shaped prose, marketing confidence, or a
sentence that could be pasted into an unrelated dissertation.

### Pre-draft manuscript audit

Before drafting the abstract, perform a strict cross-chapter audit. The abstract
must summarise the manuscript that exists; it must not repair missing argument
links by adding claims that are absent from the chapters.

Check these points and record pass/fail in the worker notes:

1. **Chapter independence.** Chapter 1 states scope and contribution; Chapter 2
   supplies background; Chapter 3 owns numerical method; Chapter 4 owns
   implementation, design matrix, metrics, and reference strategy; Chapter 5
   owns validation/results; Chapter 6 owns synthesis; Chapter 7 owns the
   compressed answer and next step. If the abstract would need to repeat a whole
   Chapter 4 design table, Chapter 5 result table, or Chapter 6 mechanism
   explanation to make sense, the chapter dependency is not clean enough.
2. **Chapter links.** Each abstract clause must have a clear source chapter:
   problem and scope from Chapter 1, Euler/MHD and floating-point context from
   Chapter 2, MUSCL--Hancock/HLLC method from Chapter 3, stand-alone CPU/CUDA
   design and metrics from Chapter 4, measured results from Chapter 5, synthesis
   boundaries from Chapter 6, and final take-home boundary from Chapter 7.
3. **Evidence grounding.** Every claim about precision, hardware, compiler flags,
   virtual precision, or MHD direction must be backed by an equation, method
   definition, metric, table, figure, citation, or named evidence artifact in
   the manuscript. If no such support exists, cut the claim from the abstract.
4. **Original requirement coverage.** Confirm that the abstract visibly covers
   the Report 1 brief: Euler background/validation system, finite-volume HRSC
   method, implementation framework choice, single/double precision comparison,
   CPU/GPU comparison, at least four Euler tests including 1D and 2D cases with
   supersonic waves, and bounded future MHD context.
5. **Supervisor feedback coverage.** Confirm that the abstract has no TODO/LLM
   directive, defines no term before the chapters define it, avoids the word
   "rows" unless referring to a specific table row, avoids unsupported hardware
   generalisation, and keeps Verificarlo `p32` distinct from IEEE fp32 if the
   diagnostic is mentioned.

If any item fails, do not draft the final abstract yet. Either tighten the
abstract scope to the material already supported by Chapters 1--7, or report the
chapter-level gap as a blocker for a 95+ abstract.

### Abstract ownership

The abstract owns a compact whole-report summary:

- project problem: precision and hardware/backend effects in HRSC schemes;
- implementation and method: a stand-alone CPU/CUDA Euler code using a
  second-order finite-volume MUSCL--Hancock method with HLLC on a controlled
  Euler validation suite;
- validation scope: Sod, Toro3, Toro5, Liska-Wendroff configuration 3 (LW3), and
  Liska-Wendroff configuration 12 (LW12);
- comparison design: real fp32/fp64 builds, matched strict-HLLC CPU/GPU saved
  outputs, compiler/branch/solver variation, and Verificarlo/MCA diagnostics;
- headline findings: two or three bounded quantitative results from the evidence
  lock;
- contribution: a bounded Euler baseline for the later MHD precision/hardware
  study.

The abstract must not:

- include citations;
- include a literature review;
- include tables, figures, equations, or bullet lists;
- introduce new results not present in Chapters 5--7;
- repeat Chapter 7 sentence-for-sentence;
- claim MHD validation has been completed;
- claim fp32 is generally adequate;
- claim hardware has no effect generally;
- claim equality of unsaved intermediate time-step stages;
- treat Verificarlo `p32` as IEEE fp32.

### Word-budget lock

Target length: **180--210 Overleaf-counted words**, hard upper 210. The abstract
is one paragraph inside the existing `abstract` environment. The controlling
word count remains Overleaf counted text; local shell word counts are only a
sanity check.

Before accepting a 200+ word abstract, check the full-manuscript budget. If the
current Chapters 1--7 already place the projected Overleaf count above the
7,400 drafting target or close to the 7,500 hard cap, the abstract target
tightens to **180--190 words** and the final response must identify the
chapter-level compression blockers. The abstract must not compensate for an
over-budget manuscript by deleting required numerical anchors, but it should not
consume avoidable budget either.

Suggested internal allocation:

| Move | Approx. words |
|---|---:|
| Problem and method | 35--45 |
| Validation and comparison scope | 45--55 |
| Headline findings with numbers | 65--80 |
| Contribution and boundary | 25--35 |

If over 210 words, compress the setup first. Do not cut the two required
numerical anchors or the MHD boundary.

### Evidence lock for the abstract

Use only these result claims unless a later evidence review updates
`manuscript_outline.md` and `experiments/report1_evidence_map.md`.

1. Euler validation is documented for the selected one-dimensional cases,
   including Sod, Toro3, and Toro5.
2. Euler validation is documented for two Liska-Wendroff two-dimensional Riemann
   configurations, LW3 and LW12; LW12 uses an \(800^2\) fp64 numerical
   reference, not an exact solution.
3. Matched strict-HLLC CPU/GPU saved-output comparisons are quantified for Sod,
   Toro3, Toro5, LW3, and LW12 in fp32 and fp64. All covered final-output
   comparisons have \(L_1=0\), \(L_\infty=0\), and
   \(\mathrm{ULP}_{\max}=0\). Saved-checkpoint comparisons for Sod, LW3, and
   LW12 are also zero, but only for saved outputs.
4. Direct fp32/fp64 differences are compared with reference or discretisation
   error in the tested cases. The LW12 \(400^2\) density reference-scaled ratio
   is \(1.30\times10^{-4}\); LW3 \(400^2\) has
   \(R_\rho=9.25\times10^{-5}\). Direct fp32 claims come only from real
   fp32/fp64 runs.
5. Region-aware Verificarlo/MCA diagnostics show spatially non-uniform precision
   sensitivity in LW3. Verificarlo `p32` is a virtual mantissa setting, not IEEE
   binary32.
6. Compiler, branch-rule, solver, fp32-flag, and finite-time drift axes were
   measured as sensitivity evidence. O2/O3 comparisons were bit-identical where
   tested; fast-math changed non-stationary saved states; HLLC--Rusanov is
   method variation rather than reproducibility drift.

The abstract must include at least two numerical anchors:

- CPU/GPU: zero \(L_1\), \(L_\infty\), and \(\mathrm{ULP}_{\max}\) for the
  matched strict-HLLC saved outputs within the tested scope.
- Precision/reference: LW12 \(400^2\) density ratio
  \(1.30\times10^{-4}\) against the \(800^2\) fp64 reference.

Optional third numerical anchor if the prose remains under 210 words:

- LW3 \(400^2\) density ratio \(9.25\times10^{-5}\), or the Ch. 6
  Verificarlo/MCA statement that HLLC cells with MCA noise above the
  reference-error scale fall to 0% at virtual `p32`.

### 95+ scoring rubric and iteration gate

After drafting, score the abstract out of 100 using this rubric. Be severe: a
short abstract can only score 95+ if it is complete, bounded, readable, and
traceable.

| Criterion | Points | 95+ standard |
|---|---:|---|
| Brief and supervisor compliance | 20 | Covers the Report 1 problem, Euler scope, CPU/GPU, fp32/fp64, and future MHD boundary; contains no TODO, LLM directive, or forbidden internal wording. |
| Evidence and numerical grounding | 25 | Includes both required numerical anchors and traces every result clause to the evidence lock without overclaiming. |
| Chapter-role coherence | 15 | Reflects the actual chapter responsibilities and does not import unsupported material or duplicate Chapter 7 wording. |
| Logic and contribution | 15 | Moves from problem to method, scope, results, and contribution in one coherent paragraph, with the contribution bounded to Report 1 evidence. |
| Style and academic voice | 15 | Uses precise technical language, appropriate hedge placement, no AI-flavoured filler, no ornamental adjectives, and no repeated triadic rhythm. |
| Word count and LaTeX format | 10 | One paragraph in the `abstract` environment, no citations, no lists, local sanity count 180--210, tightened to 180--190 if the full manuscript is over budget. |

Acceptance threshold:

- **95--100:** accept after verification commands pass.
- **90--94:** revise once unless the remaining issue is only a known
  chapter-level blocker outside the abstract scope.
- **Below 90:** revise before any final response.

Iteration limit:

1. **Round 1:** draft and score.
2. **Round 2:** fix all criteria scoring below full marks; rescore.
3. **Round 3:** final tightening only. If the score is still below 95 after
   Round 3, do not lower the standard. Report the blockers and the exact
   chapter/evidence edits needed before the abstract can reach 95+.

### Terminology rules

- First mention: "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)". Afterwards use LW3 and LW12.
- Use "fp32/fp64", "IEEE binary32/binary64", or "single/double precision"
  consistently. Do not call a pairwise difference "fp32 error" or "fp64 error".
- Use `ENABLE_CUDA`, not `USE_GPU`, if the CUDA build flag must be named. The
  abstract normally does not need build-flag names.
- Refer to CPU/GPU equality as "matched strict-HLLC saved-output comparisons" or
  "saved outputs", not as full algorithmic identity.
- Keep MHD as future direction only.
- Do not use internal labels: `week7`, `week8`, `week9`, `D1`, `D2`, `P0`,
  `P1`, `P2`, `P3`, `HLLC-fill`, `config12`, `LW12/config12`, `P1 probe`, or
  `USE_GPU`.
- Avoid template openers such as "This report presents a comprehensive study",
  "In this work", "This study has demonstrated", or "In conclusion".

---

## Worker A: Draft the Abstract

Assigned region:

```latex
\begin{abstract}
...
\end{abstract}
```

Replace the placeholder text with one paragraph of 180--210 counted words.

### Drafting moves

1. Start with the question and method in one sentence. The sentence should echo
   Chapter 1's wording: precision, hardware/backend choices, a
   Riemann-solver-based HRSC method, and controlled Euler validation.
2. State the validation scope in one sentence: Sod, Toro3, Toro5, LW3, and
   LW12; include that LW12 uses a numerical reference if the sentence mentions
   reference quality.
3. State the comparison design in one sentence: the stand-alone CPU/CUDA route,
   real fp32/fp64 builds, matched strict-HLLC CPU/GPU saved-output comparisons,
   and selected implementation sensitivity axes. Mention Verificarlo/MCA only if
   the paragraph has space and the `p32` distinction can remain clear.
4. State two or three headline findings. Include both required numerical
   anchors exactly, without paraphrasing the magnitude away.
5. Close with the contribution and boundary: a bounded Euler baseline for the
   later MHD precision/hardware study, not a completed MHD result.

### Required self-review loop

Run the 95+ rubric after each draft. For every criterion below full marks, write
one concrete edit and apply it before the next round. Stop after at most three
rounds. The worker notes must include the score table for each round, not only
the final score.

### Style constraints

- One paragraph only.
- No citations.
- No first-person singular.
- Prefer precise verbs: "examines", "compares", "quantifies", "bounds",
  "indicates", "uses".
- Put hedges on implications, not on measured findings. For example, "The
  evidence provides a bounded baseline..." is better than "The CPU/GPU outputs
  may be zero...".
- Do not include a three-sentence run of triadic "X, Y, and Z" lists.
- The paragraph must include at least one method name, at least two test-case
  labels, and at least two numerical values.

---

## Main-agent verification tasks

After Worker A finishes:

1. Read the abstract aloud once for flow and once for evidence. Remove any
   sentence that sounds like generic thesis prose rather than this project.
2. Confirm that the old TODO/LLM-directive text is gone.
3. Confirm that the abstract is one paragraph and 180--210 counted words by a
   local sanity count, tightened to 180--190 if the full-manuscript budget is
   at risk. Note that Overleaf remains controlling.
4. Trace every result clause to one of the six abstract evidence-lock items.
5. Confirm both numerical anchors appear:
   - zero \(L_1\), \(L_\infty\), and \(\mathrm{ULP}_{\max}\);
   - LW12 \(400^2\) density ratio \(1.30\times10^{-4}\).
6. Confirm that Verificarlo `p32`, if mentioned, is described as virtual
   precision rather than IEEE fp32.
7. Confirm no citations were introduced.
8. Confirm no forbidden internal labels or wording appear.
9. Run the full-manuscript rough word-count sanity command below and identify
   chapter-level budget blockers. Do not treat the rough count as controlling,
   but do not ignore a large overshoot.
10. Confirm the 95+ rubric was applied for up to three rounds and that the final
   abstract either scores at least 95 or has named blockers.
11. Run the LaTeX compile command from the template directory.

---

## Verification commands

Run from the repository root unless otherwise stated.

### Placeholder / directive sweep

```powershell
rg -n "TODO|LLM|directive|Write this last|Insert the final|placeholder" report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: zero hits.

### Forbidden/internal language

```powershell
rg -n "week[2-9]|\bP[0-3]\b|\bD[12]\b|HLLC-fill|config12|LW12/config12|P1 probe|USE_GPU|fp32 L1 error|fp64 L1 error|Lyapunov exponent|Lyapunov-like|In conclusion|To summarise|This report has shown|This study has demonstrated|comprehensive|groundbreaking|robust" report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: zero hits. If "robust" appears as part of a citation key or package
path, ignore only after checking it is not manuscript prose.

### Required numerical anchors

```powershell
rg -n "1\.30\\times10\^\{-4\}|1\.30e-4|zero .*L_1|L_1=0|L_\\infty=0|ULP|bit-identical" report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: at least one match for the LW12 precision/reference anchor and at
least one match for the CPU/GPU zero-drift anchor.

### Citation ban

```powershell
rg -n "\\\\cite|\\\\citet|\\\\citep" report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: zero hits.

### p32/fp32 distinction

```powershell
rg -n "p32|Verificarlo|MCA|fp32" report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: if `p32`, Verificarlo, or MCA appears, the surrounding sentence keeps
virtual precision distinct from IEEE fp32. Direct fp32 claims must refer to real
fp32/fp64 runs.

### Rough local word-count sanity

```powershell
$text = Get-Content -Raw report1/phd-thesis-template-2.4/Abstract/abstract.tex
$body = [regex]::Match($text, '(?s)\\begin\{abstract\}(.*?)\\end\{abstract\}').Groups[1].Value
$plain = $body -replace '\\[a-zA-Z]+\*?(\\[[^\\]]*\\])?(\\{[^}]*\\})?', ' ' -replace '[{}$\\_^]', ' ' -replace '\s+', ' '
($plain.Trim() -split '\s+').Count
```

Expected: local sanity count near 180--210. Overleaf counted text remains the
controlling count.

### Full-manuscript rough budget sanity

```powershell
$files = @(
  'report1/phd-thesis-template-2.4/Abstract/abstract.tex',
  'report1/phd-thesis-template-2.4/Chapter1/chapter1.tex',
  'report1/phd-thesis-template-2.4/Chapter2/chapter2.tex',
  'report1/phd-thesis-template-2.4/Chapter3/chapter3.tex',
  'report1/phd-thesis-template-2.4/Chapter4/chapter4.tex',
  'report1/phd-thesis-template-2.4/Chapter5/chapter5.tex',
  'report1/phd-thesis-template-2.4/Chapter6/chapter6.tex',
  'report1/phd-thesis-template-2.4/Chapter7/chapter7.tex'
)
foreach ($f in $files) {
  $text = Get-Content -Raw $f
  $text = $text -replace '(?m)^%.*$', ' '
  $text = $text -replace '(?s)\\begin\{(figure|table|algorithm)[^}]*\}.*?\\end\{\1\}', ' '
  $text = $text -replace '\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' '
  $text = $text -replace '[{}$\\_^&%#~]', ' '
  $text = $text -replace '\s+', ' '
  $count = if ($text.Trim().Length -eq 0) { 0 } else { ($text.Trim() -split '\s+').Count }
  "{0}: {1}" -f $f, $count
}
```

Expected: use only as a warning signal. If the rough total is well above the
7,400 drafting target, the final response must say which chapters need
compression before submission and keep the abstract near the lower end of its
range.

### LaTeX compile

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If compilation fails, inspect `thesis.log` and fix only abstract-related errors
unless the failure is clearly pre-existing.

---

## Final response format

Respond in Chinese with:

- the final abstract text;
- local word-count sanity result and the reminder that Overleaf is controlling;
- full-manuscript rough budget sanity result and whether the abstract was held
  to 180--190 because of budget risk;
- the two required numerical anchors and their evidence-lock items;
- the three-round scoring table, including any criteria that lost points and
  the edits made between rounds;
- sentence-by-sentence evidence trace;
- chapter-role audit result: whether the abstract's claims map cleanly to
  Chapters 1--7 without excessive overlap or unsupported leaps;
- confirmation that no citations, TODO/LLM directives, internal labels, or MHD
  validation claims remain;
- whether Verificarlo/p32 is mentioned and, if so, how the fp32 distinction is
  protected;
- LaTeX compile result.

Do not claim the full report is finished unless every abstract check passes and
the full-manuscript word count remains below the project target.
