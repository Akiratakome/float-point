# Report 1 — Revision Roadmap

**Mode:** `ars-revision` (high oversight, brief-driven review)
**Date:** 2026-05-24
**Source manuscript:** `report1/phd-thesis-template-2.4/` (chapters 1–7 + abstract, 27 bib entries)
**Brief:** `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf` (Report 1 marking rubric, 5 × 20 %)
**Due:** 2026-05-29 (5 days)

This document plays the role of an internal reviewer: I do not yet rewrite text;
I diagnose, prioritise, and propose targeted edits against the brief.
A response-letter skeleton at the end maps every brief bullet to the section
that already covers it (or doesn't).

---

## 1. Rubric coverage map

The brief allocates 20 % to each of five blocks. The thesis structure already
maps cleanly onto them:

| Brief block (Report 1, 20 % each) | Carrier chapter / section | Status |
|---|---|---|
| 1. Literature review and background | Ch 1 + Ch 2 (§2.1–2.4) | **Covered**; thin on MHD context and parallel-thread ordering |
| 2. Mathematical theory | Ch 3 (§3.1–3.6) | **Strong**; §3.5 "Precision-Sensitive Decision Points" is rubric-aligned |
| 3. Code description | Ch 4 (§4.1–4.5) | **Covered**; testing-framework description and AMReX-rejection rationale underweight |
| 4. Validation | Ch 5 + supporting parts of Ch 6 | **Covered**; one-sided device coverage and unsaved-state caveats need surfacing |
| 5. Quality of write-up | All chapters + abstract + bib | **OK but uneven**; abstract and Ch 1 are tight, Ch 6 prose is dense, three bib entries unused |

Overall: the thesis as it stands would not lose more than ~3 marks per block
in any one rubric line. The main risk is **block 4 (Validation)** where the
bit-identical CPU/GPU result is striking and demands more careful framing,
followed by **block 3 (Code description)** where the testing harness is
declared but not described.

---

## 2. Findings — prioritised

Findings are ranked by likely mark impact × ease of fix. **P1 = must-fix
before submission.** **P2 = should-fix.** **P3 = nice-to-have / polish.**

### P1 — Must-fix

**P1.1 Testing/regression framework is named but not described (Brief block 3).**
*Where:* [chapter4.tex:36-47](../phd-thesis-template-2.4/Chapter4/chapter4.tex#L36-L47) lists "a Python regression harness that re-runs the validation matrix and checks outputs against stored references" as one of four auditable features, but no subsection explains *what* it checks, *how* tolerances are set, or *how* a regression failure manifests. The brief asks explicitly for "what testing framework will be used to ensure all results are reproducible, and how ranges of modifications to compiler options or floating-point tolerances will be explored." This is a 20 %-block requirement.
*Fix:* Add a short Code-description subsection (≈ ½ page) immediately after §4.2 or at the end of §4.5, covering: harness entry point (likely `scripts/regression/report1_1d_feature_validation.py` and friends that already live in `scripts/`), what each regression assert checks (e.g. `L1`, `Linf`, `ULPmax` vs stored reference), pass/fail criteria, and how the compiler-flag axes are swept (matrix runner). Cross-reference `tests/py/test_report1_1d_feature_validation.py` and `tests/py/test_limiter_cfg.py` already in the tree.

**P1.2 AMReX-vs-stand-alone rationale is missing (Brief block 3).**
*Where:* The brief explicitly says "Use of the AMReX framework is advised" and asks the student to justify deviation. [chapter4.tex:7-12](../phd-thesis-template-2.4/Chapter4/chapter4.tex#L7-L12) commits to stand-alone but never says *why AMReX was rejected*. The current sentence "students may wish to write their own code which will be easier to customise and optimise" appears later in §4.2 only as a generic remark.
*Fix:* Two-sentence paragraph at the start of §4.1 (about 60–80 words): (a) AMReX would have given multi-arch compilation cheaply; (b) the chosen route trades that for full source control over the precision-sensitive decision points listed in §3.5 (FMA contraction, branch rule, fast-math, exact write-out path), which would have been harder to instrument inside a framework's flux abstraction. Mention that AMR is also explicitly out of scope per the brief.

**P1.3 Bit-identical CPU/GPU result needs a stronger pre-emptive defence (Brief block 4).**
*Where:* [chapter5.tex:296-352](../phd-thesis-template-2.4/Chapter5/chapter5.tex#L296-L352) (§5.5) and [chapter6.tex:81-86](../phd-thesis-template-2.4/Chapter6/chapter6.tex#L81-L86). The "zero everywhere" finding is real, but a reviewer's first reaction will be "the GPU is doing the same thing as the CPU because nothing important was actually offloaded." The thesis already lists the three structural reasons (matched binaries, no FP-sum reduction, ordered max/min CFL), but they are stated in one paragraph and may be missed.
*Fix:*
- (a) Hoist the three structural reasons into a labelled list with one sentence each.
- (b) Add the GPU build proof point that already exists: the GPU fast-vs-strict probe finding (`Linf=1.57e-5`, `ULPmax≈30.7` for LW3 fp32, [chapter5.tex:438-447](../phd-thesis-template-2.4/Chapter5/chapter5.tex#L438-L447)) — this is *evidence* that the GPU is doing arithmetic at all, since flipping `--fmad`/`--prec-div` perturbs it. Currently this is presented as a "build-control boundary" but should also be re-used here as "the GPU is genuinely active; the matched strict build is what hides the difference."
- (c) State explicitly (one sentence) that the matched-binary regime is the *only* regime for which the zero-drift claim is made; any cross-toolchain or unsaved-stage claim is outside scope.

**P1.4 Toro3/Toro5 lack saved-checkpoint CPU/GPU comparisons (Brief block 4).**
*Where:* [chapter5.tex:309-335](../phd-thesis-template-2.4/Chapter5/chapter5.tex#L309-L335) Table 5.3 shows "Saved checkpoints: none" for Toro3 and Toro5. The brief asks for time-evolution comparisons; the thesis currently has them only for Sod/LW3/LW12.
*Fix:* Two options, in order of preference:
  1. **Run them.** The 1D Toro cases are sub-second; producing 8–10 checkpoints each takes minutes. This closes the gap completely.
  2. If (1) is not feasible by Friday, add one sentence justifying the gap: "Toro3 and Toro5 were Windows-BuildTools binaries built before the checkpoint-emit option was uniformly enabled; the final-output zero-drift result is consistent with the saved-checkpoint behaviour of the Linux/WSL cases." This is acceptable but weaker.

**P1.5 Limiter-probe contradiction with §3.5 (Brief block 2 internal consistency).**
*Where:* [chapter3.tex:483](../phd-thesis-template-2.4/Chapter3/chapter3.tex#L483) says "limiter choice [remains] concept-only," but [chapter5.tex:450-453](../phd-thesis-template-2.4/Chapter5/chapter5.tex#L450-L453) reports a minbee-vs-van-Leer comparison (`L1` ranging 9.21e-4 to 1.71). One of these must change.
*Fix:* Update §3.5 status table — move limiter from "concept-only" to "measured (opt-in probe; method-sensitivity rather than reproducibility evidence)." Match Chapter 6 framing.

### P2 — Should-fix

**P2.1 Three bibliography entries are uncited (Brief block 5).**
*Where:* `zhang_etal_2019`, `wolf_etal_1985`, `eckmann_ruelle_1985` appear in [references.bib](../phd-thesis-template-2.4/References/references.bib) but are not invoked by any `\cite` in the main thesis. The brief explicitly grades on "suitability and quantity of references made."
*Fix:* Either cite them in a relevant place or delete them. Wolf and Eckmann–Ruelle suggest a Lyapunov / chaos angle that does not feature in Report 1; safer to delete. `zhang_etal_2019` should be checked against §2.4 or §3.5 — if it's a precision study it could anchor the "case-dependent fp32" sentence in §1.2.

**P2.2 Compiler-axis coverage is gcc-only and one-platform (Brief block 4).**
*Where:* [chapter5.tex:386-393](../phd-thesis-template-2.4/Chapter5/chapter5.tex#L386-L393) and [chapter6.tex:90](../phd-thesis-template-2.4/Chapter6/chapter6.tex#L90). The reviewer rubric does not require multi-compiler, but the Discussion already notes "one compiler family inside each case" — this is correctly acknowledged but only in one sentence buried in §6.3. Promote it to a numbered limitation in Ch 6 §6.3 so the reviewer sees it before they have to look for it.
*Fix:* Convert §6.3 limitations paragraph into a numbered list. This is also a write-up-quality (block 5) improvement.

**P2.3 GPU hardware identity is mentioned once and never specified beyond "RTX 4060 Laptop" (Brief block 5).**
*Where:* [chapter4.tex:277-280](../phd-thesis-template-2.4/Chapter4/chapter4.tex#L277-L280) cites the GPU in a runtime-table caption only.
*Fix:* Add a one-paragraph "Hardware environment" subsection (or one row in §4.1) listing: CPU model, GPU model, CUDA toolkit version (12.5), driver, gcc version (13), kernel, container image. This is standard reproducibility hygiene and will be visible in the marker's quick first pass.

**P2.4 Verificarlo's role vs IEEE-fp32 — clarification is repeated 4× but never stated once strongly (Brief blocks 1 + 5).**
*Where:* Abstract line 12; [chapter1.tex:21](../phd-thesis-template-2.4/Chapter1/chapter1.tex#L21); [chapter2.tex:152](../phd-thesis-template-2.4/Chapter2/chapter2.tex#L152); [chapter4.tex:200-204](../phd-thesis-template-2.4/Chapter4/chapter4.tex#L200-L204); [chapter6.tex:9](../phd-thesis-template-2.4/Chapter6/chapter6.tex#L9). The point is correct and important, but four near-identical disclaimers read as defensiveness.
*Fix:* Make the statement *once*, prominently, at first use in §2.4 (or §4.3) with one extra sentence on *why* `p32 ≠ IEEE fp32` (different rounding model: MCA-RR perturbs every operation independently; fp32 storage truncates every value). Then drop the repeats to a one-clause cross-reference: "(Verificarlo virtual precision, not IEEE fp32; see §2.4)".

**P2.5 §2.2 Ideal-MHD background is one page; consider moving Dedner/CT primer here from §3.6 (Brief block 1).**
*Where:* [chapter2.tex:52-85](../phd-thesis-template-2.4/Chapter2/chapter2.tex#L52-L85) introduces ideal-MHD in 30 lines; [chapter3.tex:488-549](../phd-thesis-template-2.4/Chapter3/chapter3.tex#L488-L549) gives much fuller treatment including Dedner, CT, HLLD, Bard–Dorelli. The brief lists "Overview of the Ideal-MHD equations" under *background*, not under *mathematical theory*. The Ch 3 material is structurally a Methods section for a system the thesis does not implement.
*Fix:* Either (a) leave as-is and add one paragraph to §2.2 mentioning HLLD/CT/Dedner by name so the literature-block coverage is visibly more complete, or (b) move the bulk of §3.6 to §2.2 and keep §3.6 to ½ page that just says "Report 2 will instantiate this from §2.2 onto the framework of §3.1–3.5." Option (a) is lower-risk.

### P3 — Polish

**P3.1 Abstract is over-packed (Brief block 5).**
The abstract names LW12 by full name twice, lists three orthogonal results in one sentence, and ends mid-clause. A revised abstract should follow the structure: (1) what was studied, (2) how, (3) what was measured, (4) headline finding, (5) what it bounds for Report 2.

**P3.2 "Auditable", "matched-binary", "saved-output" appear many times.**
Each of these terms is load-bearing on first mention, then becomes filler. After the first occurrence in §4.1 they can be dropped without loss; tighten Ch 5 §5.5 and Ch 6 §6.2.

**P3.3 Chapter 7 (Conclusion) is 18 lines.**
Acceptable in length, but the third section "Limitation and Next Step" can carry one extra sentence on the *specific* Report 2 numerical choice (Dedner with damping-time auto-selection from §3.6, or constrained transport) — currently "Dedner-type" is unforced.

**P3.4 Dimensional-splitting choice — Strang or simple alternation? (Brief block 2).**
[chapter3.tex:97-102](../phd-thesis-template-2.4/Chapter3/chapter3.tex#L97-L102) says "dimensionally split, not an unsplit method" and "alternating the sweep order reduces a fixed ordering bias." Strange wording — the reader does not know whether the ordering is Strang-symmetric `XYYX` over a double step or simple `XYXYXY…`. One added sentence resolves it.

**P3.5 Cross-references to figures use mixed numbering.**
Random spot-check: figure refs work, but in §5.6 there are several `Table \ref` calls that could be `Tab.` for consistency with §5.2. Low priority.

---

## 3. Section-by-section response-letter skeleton

This is the point-by-point mapping a future reviewer (or you, when handing in)
will expect. Brief bullets are quoted verbatim; the response gives the
location of the matching evidence after the P1/P2 fixes above are applied.

### Block 1 — Literature review and background

> "Overview of Euler's equations for compressible ideal-gas."

Addressed in §2.1 (`chapter2.tex:5–50`). Conservative two-dimensional form, ideal-gas closure, and reduction to 1D for shock-tube tests are stated. No revision needed.

> "Overview of the Ideal-MHD equations."

Addressed in §2.2; deeper treatment in §3.6. **P2.5** action: move HLLD/CT/Dedner naming into §2.2 so the *background* block reads complete on first pass.

> "Finite-volume schemes, basic overview of derivation."

Addressed in §3.1 with explicit cell-integration derivation. No revision needed.

> "A brief discussion of floating-point arithmetic, and what effect different hardware, compiler options, and parallel-thread ordering may have…"

Addressed in §2.4 (IEEE 754, non-associativity, Goldberg, Demmel–Nguyen on reproducible summation, Whitehead–Fit Florea on CUDA FMA, MCA primer). **P2.4** action: consolidate the Verificarlo-vs-IEEE-fp32 disclaimer to one strong statement here.

### Block 2 — Mathematical theory

> "Description of the chosen explicit method, such as MUSCL-Hancock or WAF (must be Riemann-solver based)."

Addressed in §3.1–3.4 (FV update, MUSCL–Hancock reconstruction and predictor, HLLC, Rusanov, CFL, positivity, limiter). No revision needed.

> "Discuss any numerical method variations specific to MHD."

Addressed in §3.6 (seven-wave fan, ∇·B constraint, Dedner GLM, constrained transport, HLLD precedent, Bard–Dorelli GPU precedent). **P2.5** may relocate this to §2.2.

> "Briefly summarise the points in the algorithms that could be varied in future investigations, such as `<` versus `<=`…"

Addressed in §3.5 (full table of method components × precision-sensitive points, plus build-switch macros). **This is a rubric-perfect match.** **P1.5** action: reconcile limiter status with Chapter 5.

### Block 3 — Code description

> "Discussion of the AMReX (or other) framework that has been chosen, and how it allows ease of implementing multi-core CPU and GPU algorithms…"

Partially addressed in §4.1 (stand-alone route, HRSC_REAL templating, ENABLE_CUDA switch, runtime device selection) and §4.2 (kernels, OpenMP, shared-memory CFL reduction). **P1.2** action: add explicit "why not AMReX" rationale at the head of §4.1.

> "Discussion of what testing framework will be used to ensure all results are reproducible, and how ranges of modifications to compiler options or floating-point tolerances will be explored. The way in which the exact or appropriately-converged solution has been determined should also be discussed."

The reference-solution half is **strongly addressed** in §4.5. The testing-framework half is **only declared** at §4.1 bullet 3. **P1.1** action: add the missing testing-framework subsection.

### Block 4 — Validation

> "Demonstration of correct results for at least four test-cases for Euler equations for ideal-gas, that include supersonic waves. This must include both 1D and 2D tests."

Five cases delivered (Sod, Toro3, Toro5, LW3, LW12); four contain supersonic waves; 1D + 2D both present. Rubric-cleared.

> "Evaluation of these tests on both CPU and GPU."

All five cases evaluated on both backends. **P2.3** action: state the hardware once explicitly.

> "Comparison of results on CPU and GPU, quantifying any differences between the results."

Done via L1/Linf/ULPmax tables. **P1.3** action: pre-empt the "is the GPU really doing the work?" reading. **P1.4** action: extend Toro3/Toro5 checkpoint coverage if time allows.

> "Compare the result accuracy between single and double precision."

Done via reference-scaled ratios R_ρ in §5.4 + table 5.2 + LW12 heatmap. Rubric-cleared.

### Block 5 — Quality of write-up

> Structure, layout, spelling/grammar, plots/tables, completeness, references.

Structure and figures are in good shape. **P2.1** (three uncited bib entries), **P3.1** (abstract polish), **P3.2** (terminology repetition) collectively close this block.

---

## 4. Suggested 5-day execution order

The submission deadline is **2026-05-29**. Reading order = priority order.

| Day | Task | Items |
|---|---|---|
| Mon 2026-05-25 | Re-run the 1D Toro checkpoint matrix; refresh tables 5.3 / 5.4 | P1.4 |
| Tue 2026-05-26 | Write testing-framework subsection in Ch 4; AMReX-rejection paragraph at §4.1 head | P1.1, P1.2 |
| Wed 2026-05-27 | Defence-of-zero-drift edits in §5.5 / §6.2; reconcile §3.5 limiter status; promote §6.3 limitations to a numbered list | P1.3, P1.5, P2.2 |
| Thu 2026-05-28 | Bib cleanup, Verificarlo-disclaimer consolidation, hardware paragraph, abstract rewrite | P2.1, P2.3, P2.4, P3.1, P3.2 |
| Fri 2026-05-29 | §2.2 MHD top-up paragraph, conclusion polish, final read-through, build PDF | P2.5, P3.3–P3.5 |

If only one day is available, do **P1.1 + P1.2 + P1.3** — these are the
highest-leverage marks defenses against the rubric blocks the thesis is
weakest in.

---

## 5. What is *not* recommended

- **Do not** restructure chapters. The 7-chapter layout is rubric-aligned.
- **Do not** add new test cases. Five is already above the minimum-four floor.
- **Do not** attempt MHD validation; the brief defers it to Report 2.
- **Do not** chase the bit-identical CPU/GPU result by introducing reduction-sum kernels just to see them break; the matched-binary discipline is the contribution, not a weakness.
- **Do not** rewrite the abstract until P1 edits land — its claims must match the revised body.

---

*End of revision roadmap. Awaiting your call on which P1 items to action first; I can apply any of them as `\sed`-style targeted edits or as full subsection rewrites.*
