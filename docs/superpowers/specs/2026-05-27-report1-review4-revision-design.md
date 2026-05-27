# Report 1 Review 4 Revision — Design

**Date:** 2026-05-27
**Branch:** `report`
**Target manuscript:** `report1/phd-thesis-template-2.4/`
**Source of review:** `review.md` at repo root (supervisor: Philip)
**Deadline:** 2026-05-29
**Wordcount baseline:** **7825 words** (user-confirmed at 2026-05-27 review-4 start)
**Hard cap:** **7850 words** (Overleaf wordcount standard, excludes figures/tables/captions)
**Safety target:** ≤ 7820 (gives 30-word margin to absorb late copy-edit drift)
**Scope:** Manuscript-only edits, preamble formatting change, two short `lstlisting` blocks. No solver/cfg/harness changes. Every batch targets a specific `\section{...}` or `\paragraph{...}` marker — never a whole chapter.

## 1. Review items addressed

### From `review.md` (supervisor)

| Item | Philip's request | Batches |
|---|---|---|
| R1 | Ch1 too abrupt — needs physical-application motivation + reproducibility framing; should read as high-level overview | 1 |
| R2 | §2.4: define significand/exponent, remove "roughly", explicit Sterbenz + Kahan references; Verificarlo as its own subsection | 2a, 2b |
| R3 | Page 16 (Ch3 §"Precision-Sensitive Decision Points"): explain `RIEMANN_STRICT_INEQUALITY` with code example | 3a |
| R4 | Page 19 (Ch4 §"Implementation Route…"): cite Boost::Multiprecision | 3b |
| R5 | §4.2 (Ch4 §"Algorithmic Structure…") fragmented short sentences; "cell-major" duplicated; group by ideas. Same applies to later §4.x. | 4, 5 |
| R6 | Table 5.7 etc.: use `$9.34\times10^{-8}$`, not `9.34e-8` | 7 |
| R7 | Ch6: define LoSoS before first use; other undefined concepts | 6 |
| R8 | Add code samples (e.g. templated solver) to break up wordy sections | 3a, 3b |

### User-added (style and Ch2 substantive gaps)

| Item | Requirement | Batches |
|---|---|---|
| U1 | Eliminate AI tone; deliver real coherence/readability polish; mix long and short sentences; clear subject every sentence; default to short | **8 (dedicated)** + style gates on every batch + Phase 2.5 residual audit |
| U2 | Target specific section, not whole chapter | enforced in every batch envelope (§4) |
| U3 | Ch2 lacks **finite-volume derivation overview** (rubric explicit requirement; currently deferred to Ch3 only) | **2c** (new) |
| U4 | Ch2 §"Ideal-MHD Project Context" missing: Alfvén / fast / slow magnetosonic physical meaning; Euler-vs-MHD structural difference (non-strict hyperbolicity, degenerate waves); CT vs GLM vs Powell trade-off comparison | **2d** (new) |
| U5 | Ch2 §"Floating-Point…": clarify "unbiased exponent" wording; deepen parallel-reduction non-associativity discussion citing Demmel & Nguyen ReproBLAS and Collange et al. 2015; mention Kulisch accumulator / exact dot product; cite Revol & Théveny 2014; **make binary32 and binary64 exponent-range phrasing consistent** | **2e** (new) |
| U6 | Add missing key references: Einfeldt 1988 (HLLE), Collange et al. 2015 (GPU/multicore parallel reductions), Bailey et al. (High-Precision Computation), Revol & Théveny 2014, Villa/Chatterjee GPU reproducibility | **2d, 2e, 3a** + new bib entries |
| U7 | Add nothing first, then **audit for redundant viewpoints and zero-information sentences** — let cuts be data-driven, not pre-locked | **Phase 1.5** (new) |
| U8 | After cuts, do a second **residual AI-tone audit** across the whole manuscript — Batch 8 catches grep-able stuff; this catches what survived | **Phase 2.5** (new) |

## 2. Word-budget model

**Baseline: 7825. Cap: 7850. Safety target: 7820. Working headroom on entry: 25 words.**

Summing every batch budget in §4 honestly: raw additions **+1030**, raw subtractions **−330** built into the batches themselves, net Phase 1 delta **+700**. Subtotal after Phase 1 ≈ **8525**. Required Phase 2 compression to land at 7820: **−705 words**. That is roughly **8 %** of the post-Phase-1 manuscript — still a real reshape, but reachable from a redundancy audit without contortion.

**Tightenings applied:**

- Batch 1 trimmed from +200 raw to **+140 raw** (≈140-word §1.1 instead of ≈200-word): one citation per cluster, no "Anderson aerodynamics" fallback, shorter motivation closer. Saves 60 raw words.
- Batch 2d trimmed from +260 raw to **+180 raw** by replacing three CT/GLM/Powell trade-off paragraphs with one short prose paragraph plus a 3-row comparison table (table prose lives in caption, not counted by texcount). Saves 80 raw words.

Combined headroom recovered vs. the un-tightened version: **140 raw words**, reducing the Phase 2 compression target from −845 to −705.

| Phase | Δ words (net) | Running total |
| --- | --- | --- |
| Baseline (pre-revision) | — | 7825 |
| Batch 1 (Ch1 §1.1 + polish, **tightened**) | +110 | 7935 |
| Batch 2a (§"Floating-Point…" polish) | +40 | 7975 |
| Batch 2b (new §"Verificarlo…") | +180 | 8155 |
| Batch 2c (new §"Finite-Volume Derivation Overview") | +140 | 8295 |
| Batch 2d (MHD depth, **tightened** via comparison table) | +100 | 8395 |
| Batch 2e (FP depth + consistency) | +130 | 8525 |
| Batch 3a (Ch3 RIEMANN_STRICT listing) | +80 | 8605 |
| Batch 3b (Ch4 HRSC_REAL listing + Boost cite) | +60 | 8665 |
| Batch 4 (§"Algorithmic Structure" reflow) | −80 | 8585 |
| Batch 5 (Ch4 later sections reflow) | −40 | 8545 |
| Batch 6 (Ch6 first-use definitions) | +40 | 8585 |
| Batch 7 (preamble — texcount-neutral) | 0 | 8585 |
| Batch 8 (anti-AI polish, all chapters) | −60 | **8525** |
| Phase 1.5 redundancy audit → Phase 2 cuts (data-driven) | **−705** (target) | — |
| **Final delivered** | — | **≈ 7820** (cap-compliant with 30-word margin) |

**Per user instruction (U7): no cut candidates are pre-locked.** Phase 1.5 audits the post-Phase-1 manuscript fresh and produces a prioritized cut list. Phase 2 executes against that list. The likely heaviest cut zones, but not committed in advance:

- Cross-chapter overlap between Ch2 (now-expanded MHD overview) and Ch3 §"Extension to Ideal MHD" — likely large savings once Ch2 covers physical-meaning material that Ch3 currently restates.
- Hedge sentences across Ch4–Ch6 of the form "this is not a claim of X; rather…" repeated for the same caveat.
- Long table captions whose final clause restates the prose surrounding the table.
- Ch6 §"Limitations and Report 2 Direction" item-4 sub-clauses (stderr timing alignment).
- Ch7 §"Key Findings" — currently restates Ch5 and Ch6 quantitative results that already appear with their tables.

Worst case: if Phase 1.5 only finds ~300 words of true redundancy, the spec escalates to the user with a list of borderline cuts before continuing.

## 3. Anti-AI-tone rules (operational gate for U1)

Every batch envelope includes the rules below. Batch 8 is the dedicated polish pass that runs the grep across all chapter files. Hits in the forbidden list fail the audit gate and trigger a fix-up sub-agent.

### Why this matters (style philosophy)

AI prose reads flat because every sentence carries about the same weight. Human academic prose has lifts and dips. A long, branching sentence sets up an idea; a five-word sentence lands it. A formal definition gets followed by a plain-language gloss. The vocabulary stays inside the reader's working set — no thesaurus reaches — but the *order* in which words arrive is not the most predictable order.

**Three principles, in priority order:**

1. **Default to short.** Most sentences should run 8–18 words. Long sentences are seasoning, not the meal. If a 35-word sentence cannot be split, split it anyway and accept the slight redundancy.
2. **Vary the rhythm.** Within a paragraph, mix short and long. Avoid four short sentences in a row (sounds choppy and AI-clipped) and avoid three long sentences in a row (sounds AI-bloated). A useful target: each paragraph has at least one sentence ≤ 10 words and at least one sentence ≥ 20 words.
3. **Every sentence has a clear subject.** No floating "It is clear that…", no "There exists…", no agent-free passive when an agent exists. The CFL scan does something; the limiter chooses something; the GPU writes something. Name them.

### Vocabulary: unexpected, not elevated

Add a small handful of plain words that are slightly off-register from the surrounding formal prose. The goal is to break the "every word is the most predictable next word" pattern.

- Acceptable swaps (plain register): `notice` (for `observe`), `match` (for `correspond to`), `hits` (for `attains`), `pick up` (for `incorporate`), `drop` (for `decrease`), `sit at` (for `are located at`), `gap` (for `discrepancy`), `lines up with` (for `is consistent with`).
- Unacceptable (too elevated, sounds AI-generated): `ostensibly`, `notwithstanding`, `pursuant to`, `quintessential`, `nuanced` (the LLM tell), `intricate`, `paradigm`, `multifaceted`.
- Frequency rule: use one or two of the plain-register swaps per major prose paragraph. Not every sentence — that swings to casual and breaks the academic balance.

### Subject-clarity gate (manual review per paragraph)

For each sentence, the sub-agent must be able to name the subject in one or two words. Sentences that fail:

- "It is the case that the saved state differs…" → the saved state differs.
- "There exists a degenerate ratio…" → the stationary-contact ratio is degenerate.
- "What follows is a description of…" → describe it; no announcement.
- Long subject-verb separation (subject in line 1, verb in line 3) — split the sentence.

### Sentence-length gate (per paragraph)

- Average target: 12–16 words/sentence.
- Maximum: 30 words for a single sentence. Anything longer must be split, even at the cost of one connective word.
- Within each paragraph of 4+ sentences: at least one short (≤ 10 words) and at least one long-ish (≥ 20 words). No paragraph may consist of all-short or all-long sentences.

### Forbidden patterns (case-insensitive grep gate, zero hits required)

```
in this section,
in this chapter,
it is worth noting that
it should be noted that
importantly,
notably,
crucially,
of note,
the following discussion
as we shall see
we now turn to
may potentially
could possibly
leverages
showcases
facilitates
in order to                    # almost always "to"
a wide range of                # filler
plays a crucial role
plays a key role
plays an important role
plays a significant role
delve into
delve deeper
robust                         # used as filler; OK only when load-bearing
seamless
furthermore,\s                 # paragraph-initial only
moreover,\s                    # paragraph-initial only
additionally,\s                # paragraph-initial only
```

Compound rules (manual review, not pure grep):

- No paragraph that opens by restating its `\section{...}` heading.
- No sentence that uses `\citep{}` more than twice without doing real work between citations.
- No three-in-a-row "X, Y, and Z" tricolon in the same paragraph.
- No run of more than four short sentences (< 12 words each); break the rhythm.
- `demonstrates` → prefer `shows` unless the demonstration is the actual content.
- `utilise / utilises` → `use / uses`.
- `methodology` → `method` unless distinguishing from `methods`.

### Style targets (positive guidance for sub-agents)

- **Default short.** Most sentences 8–18 words. Long sentences as accents only.
- **Vary the rhythm.** Within every prose paragraph of 4+ sentences, at least one ≤ 10 words and at least one ≥ 20 words. The MUSCL-Hancock paragraphs in Ch3 §"MUSCL-Hancock Reconstruction and Predictor Step" already model this well — keep that paragraph as the calibration target.
- **Name the subject.** `the solver`, `Table 5.5`, `the matched build`, `the kernel`, `Philip's review`. Avoid `this approach`, `the present study`, `the proposed framework`, `it`-with-no-antecedent.
- **Active voice where an agent exists.** The harness runs; the compiler contracts; the GPU writes. Passive only when the subject is genuinely impersonal (the time step is selected, the file is saved).
- **One or two plain-register words per paragraph.** "Drop", "gap", "match", "lines up with", "hits". Not "ostensibly", not "intricate", not "nuanced".
- **Citations earn their place.** `\citep{toro2009}` after a routine numerical-method statement is fine; three citations in one paragraph is not.
- **No throat-clearing openers.** `In this section, we describe…` → just describe it.
- **No paragraph opens by restating its `\section{}` heading.** If the heading says "Two-Dimensional Euler Validation", the first sentence is not "The two-dimensional Euler validation results are…".

## 4. Batches

Workflow architecture is the **serial sub-agent + main-process audit** pattern from `docs/superpowers/specs/2026-05-26-report1-review3-revision-plan.md` §0. Each batch envelope contains: target file paths, target `\section{}` / `\paragraph{}` markers, verbatim replace-text or insert-text, required hedges, forbidden phrases (the list in §3), word-delta budget, acceptance criteria. Main process runs `texcount` + grep audits between batches; no batch proceeds until the prior batch passes.

### Batch 1 — Ch1 expansion and reflow

**Target sections:**

- `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex`
  - Insert new `\section{Physical Applications and Reproducibility}` **before** existing `\section{Context: HRSC Schemes for Discontinuous Compressible Flows}` (currently line 5).
  - Anti-AI polish on existing `\section{Context: HRSC Schemes for Discontinuous Compressible Flows}` (line 5) and `\section{Precision and Hardware Reproducibility Problem}` (line 10). Leave `\section{Report Scope and Contribution}` and `\section{Report Structure}` untouched except for grep-forbidden tokens.

**Content of new §1.1 (≈ 140 words, 2 tight paragraphs):**

- ¶1 (≈ 75 words): Compressible-Euler/HRSC applications stated compactly — external aerodynamics (supersonic intakes, hypersonic re-entry), turbine-cascade shocks, inertial-confinement-fusion implosions, astrophysical jets and shock-bubble interactions. One citation per cluster max (Bard & Dorelli for GPU-HRSC precedent; Liska & Wendroff for 2D benchmark context). Close with one sentence on why fast and accurate solutions matter — design loops, operating envelopes.
- ¶2 (≈ 65 words): Numerical-implementation choices vary between researchers, hardware vendors, and compiler toolchains. Two binary builds of the same algorithm can disagree from precision, FMA contraction, reduction ordering, or branch-rule choices near zero wave speeds. That variability is the question Report 1 quantifies on a controlled Euler validation suite. Forward-reference: §"Report Scope and Contribution".

**Budget:** +140 / −30 (the −30 is grep-forbidden-token removal in the two existing sections).

**Acceptance:** texcount delta within ±10 of budget; grep returns zero hits for forbidden list inside `Chapter1/chapter1.tex`; pdflatex builds.

### Batch 2a — Ch2 §"Floating-Point Arithmetic and Reproducibility" polish

**Target section:** `Chapter2/chapter2.tex` `\section{Floating-Point Arithmetic and Reproducibility}` (line 119) and its `\paragraph{Virtual precision versus IEEE binary32.}` (line 163).

**Edits:**

1. First sentence of the section: define **significand** and **exponent** explicitly before stating the binary32/binary64 widths. Example wording (sub-agent may polish but must preserve substance):
   > A floating-point number is stored as a sign bit, an integer-encoded *exponent*, and a *significand* — the leading binary digits of the value. The number of bits in each field fixes the precision and dynamic range of the format.
2. Line 124: remove "roughly". The exponent range is exact (`−126` to `+127` for binary32 normals, `−1022` to `+1023` for binary64 normals).
3. Add an explicit citation for Sterbenz's lemma — add `sterbenz_1974` to `References/references.bib` (Sterbenz, *Floating-Point Computation*, Prentice-Hall, 1974) and `\citep{sterbenz_1974}` on the sentence that states the lemma.
4. Add `\citep{kahan_1965,higham_2002}` on the compensated-summation sentence (kahan_1965 already in bib).
5. Trim the `\paragraph{Virtual precision versus IEEE binary32.}` block by ~20 words — the Verificarlo background it currently carries is now hosted in new §2.5 (Batch 2b). Leave only the comparison between fp32 storage and `p32` virtual precision.

**Budget:** +60 / −20.

**Acceptance:** "roughly" absent in this section; `sterbenz_1974` present in `references.bib` and cited once in this section; significand and exponent each appear in the first three sentences.

### Batch 2b — Ch2 new §"Verificarlo and Monte Carlo Arithmetic"

**Target:** insert new `\section{Verificarlo and Monte Carlo Arithmetic}` in `Chapter2/chapter2.tex`, **after** `\section{Floating-Point Arithmetic and Reproducibility}` ends at line 176, **before** the chapter closes.

**Content (≈ 180 words, 3 paragraphs):**

- ¶1: What Verificarlo is and who built it. "Verificarlo is an open-source LLVM-based instrumentation tool developed by Denis, Castro Lopez, Petit, Fèvre, and Lamotte, distributed under the GPLv3 \citep{denis_etal_2016}. It replaces individual floating-point operations with instrumented variants at compile time, so the resulting binary can probe rounding sensitivity without changes to the application source."
- ¶2: Monte Carlo Arithmetic (MCA), virtual precision, and sample-count rule. Cite Parker 1997 and Sohier et al. 2021 — both already in bib. State the three MCA operators (Random Rounding RR, Monte Carlo Arithmetic MCA, Precision Bounding PB), the virtual-precision parameter `t`, and the distribution-free sample-count rule `n_min = ⌈log(1−c)/log(p)⌉`.
- ¶3: Features used in this report. The `vfc_ccompiler` toolchain in MCA-RR mode at `t ∈ {8, 16, 32, 53}`, n = 30 seeds per (precision, solver) configuration; the `significantdigits` package for LoSoS computation. Note that `libinterflop`'s PRNG is not thread-safe, so MCA runs are serial. Forward-reference: Chapter 4 §"Precision and Hardware Variants" applies these settings to LW3.

**Budget:** +180 / 0.

**Acceptance:** new section exists; first paragraph names at least three developers and one citation; references to RR/MCA/PB operators present; cross-reference to Ch4 §"Precision and Hardware Variants" present.

### Batch 2c — Ch2 new §"Finite-Volume Derivation Overview"

**Why:** rubric explicitly requires "Finite-volume schemes, basic overview of derivation" in the literature-review/background chapter. The current Ch2 has no such overview — the derivation appears only in Ch3 §"Finite-Volume Update". Reviewer-level structural gap (U3).

**Target:** `Chapter2/chapter2.tex`, insert new `\section{Finite-Volume Derivation Overview}` **between** `\section{HRSC and Benchmark Literature}` (line 95) and `\section{Floating-Point Arithmetic and Reproducibility}` (line 119). Renumbering happens automatically.

**Content (≈ 140 words, 2 paragraphs):**

- ¶1: From conservation law to integral form. Start with the generic 1D conservation law $\partial_t U + \partial_x F(U) = 0$. Integrate over a control volume $[x_{i-1/2}, x_{i+1/2}] \times [t^n, t^{n+1}]$. Show the integral form. Define the cell average $\bar U_i^n$. Result: the discrete update $\bar U_i^{n+1} = \bar U_i^n - (\Delta t/\Delta x)(\widehat F_{i+1/2} - \widehat F_{i-1/2})$, with $\widehat F$ the time-averaged interface flux. Cite Toro 2009, LeVeque 2002.
- ¶2: Why this matters here. Conservation lives at face level — shared faces cancel pairwise, leaving boundary fluxes only. Interface fluxes come from a Riemann problem at the discontinuity. The reconstruction order, the Riemann solver, and the time integrator are the three knobs the rest of the report varies. Forward-reference: Chapter 3 §"Finite-Volume Update" gives the 2D extension and operator-splitting form used by the implementation.

**Budget:** +140 / 0.

**Acceptance:** new section exists; integral form and cell-average appear; Toro 2009 and LeVeque 2002 cited; forward-reference to Ch3 §"Finite-Volume Update" resolves. The derivation here is **overview-level**, not a re-statement of the full Ch3 derivation — explicit gate: section length must stay under 160 words.

### Batch 2d — Ch2 §"Ideal-MHD Project Context" depth additions

**Target:** `Chapter2/chapter2.tex` `\section{Ideal-MHD Project Context}` (line 52, ending around line 93).

**Three insertions, in order:**

1. **Physical meaning of the MHD wave speeds** (≈ 80 words). Insert after the conservation form is stated (around current line 78). One paragraph: Alfvén speed $c_A = |B_\parallel|/\sqrt{\rho}$ is the propagation speed of incompressible transverse magnetic perturbations along the field; fast magnetosonic $c_f$ and slow magnetosonic $c_s$ are the bounding compressible waves with field-aligned and cross-field couplings; the entropy/contact mode advects with the flow. Cite Toro 2009 (MHD chapter) and Miyoshi & Kusano 2005.

2. **Euler-vs-MHD structural difference** (≈ 70 words). Insert one short paragraph after the wave-speed paragraph. Key points: ideal MHD is **not strictly hyperbolic** — fast and Alfvén waves can coincide when $B_\perp = 0$ (degenerate cases), and slow and Alfvén can coincide when $B_\parallel = 0$. This breaks the clean three-wave HLLC picture from Euler. The seven-wave fan in Ch3 §"Extension to Ideal MHD" assumes the non-degenerate case. Cite Brio & Wu 1988 (degenerate MHD Riemann structure) — add bib entry if missing.

3. **CT vs GLM vs Powell trade-off** (≈ 30 words of prose + a 3-row caption-less comparison table that doesn't count toward texcount). Replace the current single-paragraph divergence-control remark (around current line 88–92) with one short prose paragraph that points the reader to the comparison table, then the table itself. The table has three rows (one per scheme) and three columns: divergence-error treatment, mesh requirement, trade-off. Cite Evans & Hawley 1988 (CT), Dedner 2002 (GLM), Powell 1999 + Tóth 2000 (Powell eight-wave).

   The prose paragraph itself stays short — about three sentences — because the table carries the comparison. The point is that cell-centred (GLM, Powell) and staggered (CT) split the design space, and each scheme accepts a different trade.

**Budget:** +180 / −80 (the existing thin paragraph on cleaning is removed; the comparison table absorbs the trade-off detail without counting toward texcount).

**Acceptance:** Alfvén / fast / slow physical meaning appears with units; non-strict-hyperbolicity is named; CT vs GLM vs Powell each described in 1–3 sentences each with one trade-off each; Brio & Wu 1988 cited (bib entry added if missing); section length stays under 320 words total.

### Batch 2e — Ch2 §"Floating-Point Arithmetic and Reproducibility" depth + consistency

**Target:** `Chapter2/chapter2.tex` `\section{Floating-Point Arithmetic and Reproducibility}` (line 119) — this is a follow-up to Batch 2a (significand/exponent + Sterbenz + Kahan). Batch 2e adds the *deeper* content U5 asks for.

**Edits:**

1. **Exponent-range wording consistency and "unbiased" clarification.** Replace the two-sentence block at lines 123–126 with one block that:
   - Names the exponent as the **unbiased exponent $e$**, defined by the IEEE-754 encoding $E - \text{bias}$.
   - Uses identical phrasing for both formats: "binary32 has a 24-bit significand and a normal unbiased exponent range $e \in [-126, +127]$; binary64 has a 53-bit significand and a normal unbiased exponent range $e \in [-1022, +1023]$." Same prepositional structure, same use of the $\in$ symbol, identical sign-convention on the upper bound.
2. **Reduction-order / non-associativity depth** (≈ 90 words). Expand the current paragraph at lines 146–157 with two added sentences:
   - The non-associativity of summation means parallel reductions (warp reductions, OpenMP `reduction(+)`, MPI `MPI_Reduce`) depend on the order in which partial sums combine. Different thread counts, block sizes, or NUMA topologies can produce different bit patterns from the same input. Cite Collange et al. 2015 (add bib entry).
   - Reproducible reductions need an explicit construction: Demmel & Nguyen's ReproBLAS uses pre-rounding to a fixed split; Revol & Théveny 2014 build reproducible summation from interval-arithmetic bounds. Cite both — Demmel & Nguyen already in bib as `demmel_nguyen_2013` (verify); Revol & Théveny entry to be added.
3. **Kulisch accumulator / exact dot product** (≈ 30 words). One short sentence added at the end of the same paragraph: "At the hardware end, a Kulisch-style exact accumulator stores the full-precision partial sum in a wide fixed-point register, eliminating rounding inside the reduction at the cost of register width. The present solver does not use one." Cite Kulisch 2013 (add bib entry).
4. **Boost.Multiprecision / High-precision computation context.** One short sentence after the Verificarlo subsection cross-reference (or in the existing virtual-precision paragraph): "Higher-precision routes — `Boost.Multiprecision`, `MPFR`, software fp128 — are surveyed in Bailey, Borwein, and Borwein's *High-Precision Computation* and provide a path beyond binary64 not exercised here." Cite Bailey et al. (add bib entry).

**New bibliography entries** (add to `References/references.bib` if missing — main process verifies each `@key` against current bib before the batch):

- `collange_etal_2015` — Collange, Defour, Graillat, Iakymchuk, "Numerical reproducibility for the parallel reductions on multi- and many-core architectures", *Parallel Computing*, 2015.
- `revol_theveny_2014` — Revol & Théveny, "Numerical reproducibility and parallel computations: Issues for interval algorithms", *IEEE Transactions on Computers*, 2014.
- `kulisch_2013` — Kulisch, *Computer Arithmetic and Validity: Theory, Implementation, and Applications*, 2nd ed., De Gruyter, 2013.
- `bailey_borwein_borwein_2015` — Bailey, Borwein, "High-Precision Computation: Mathematical Physics and Dynamics", *Applied Mathematics and Computation*, or the book chapter equivalent.
- `brio_wu_1988` — Brio & Wu, "An upwind differencing scheme for the equations of ideal magnetohydrodynamics", *Journal of Computational Physics*, 1988 (for Batch 2d's degeneracy reference).
- `einfeldt_1988` — Einfeldt, "On Godunov-type methods for gas dynamics", *SIAM Journal on Numerical Analysis*, 1988 (for HLLE — used in Batch 3a's HLL-family historical citation if room allows; otherwise cite from Ch3 §"HLLC and Rusanov Fluxes" without text expansion).

**Budget:** +150 / −20 (the consistency-fix block trims ~20 words; the three depth additions sum to ~150).

**Acceptance:** "unbiased" appears explicitly with both formats; the binary32 and binary64 exponent-range sentences use identical structure; Collange 2015 + Revol-Théveny 2014 + Kulisch + Bailey + Brio-Wu + Einfeldt all present in `references.bib`; reduction-order paragraph now cites at least two of {Collange, Demmel-Nguyen, Revol-Théveny}; Kulisch accumulator named once with the explicit "not used here" caveat.

### Batch 3a — Ch3 §"Precision-Sensitive Decision Points" code listing

**Target:** `Chapter3/chapter3.tex` `\section{Precision-Sensitive Decision Points}` (line 385), specifically the area around `\paragraph{Method components and build switches.}` (line 457) and `tab:precision-macros` (line 490).

**Edits:**

1. Replace the `\texttt{RIEMANN\_STRICT\_INEQUALITY}` row in `tab:precision-macros` with a slightly shorter cell that points to a new listing.
2. Insert immediately before `tab:precision-macros`:
   - Two short sentences: what the macro does (toggles `<` vs `≤` in the HLLC branch dispatcher), where it lives in the source (`src/euler/euler_solver.cpp`), and why it matters (changes one comparator at the wave-speed-near-zero boundary).
   - A `lstlisting` block, ~6–8 lines, showing the `#ifdef RIEMANN_STRICT_INEQUALITY` branch from the actual source file. Caption: "HLLC branch rule: baseline `\le` vs strict `<` selected by `RIEMANN\_STRICT\_INEQUALITY`."
3. Cross-reference from this new block to Ch5 §"Toro Test 2 Branch Stability" (where the strict-`<` failure is analysed).

**Code source:** verify exact macro use in `src/euler/euler_solver.cpp` before pasting — the listing must reflect actual source, not a stylised version.

**Budget:** +80 / 0.

**Acceptance:** `lstlisting` block compiles via `listings` package; `RIEMANN_STRICT_INEQUALITY` appears in the listing exactly as in source; cross-reference to Toro Test 2 Branch Stability resolves.

### Batch 3b — Ch4 §"Implementation Route and Comparability Principle" code listing + Boost cite

**Target:** `Chapter4/chapter4.tex` `\section{Implementation Route and Comparability Principle}` (line 5, ending around line 29).

**Edits:**

1. Immediately after the precision/CUDA tabular at lines 10–20, insert a `lstlisting` block (~6–8 lines) showing the `HRSC_REAL` type definition and the templated conserved-state struct from `src/euler/euler_solver.hpp`. Caption: "Compile-time precision selection and the templated conserved-state container."
2. Sentence at line 23–24 ("Higher-precision extensions, such as a Boost::Multiprecision route, are outside the Report 1 evidence scope.") — add `\citep{maddock_boost_multiprecision}` after "Boost::Multiprecision". Add the entry to `references.bib`:
   ```bibtex
   @misc{maddock_boost_multiprecision,
     author = {John Maddock and Christopher Kormanyos},
     title  = {Boost.Multiprecision},
     year   = {2024},
     howpublished = {\url{https://www.boost.org/doc/libs/release/libs/multiprecision/}},
     note   = {Accessed 2026-05-27}
   }
   ```

**Code source:** verify the actual `HRSC_REAL` definition in `src/euler/euler_solver.hpp` before pasting.

**Budget:** +60 / 0.

**Acceptance:** `lstlisting` renders; `maddock_boost_multiprecision` entry compiles in references.bib and `\citep{}` resolves; `Boost::Multiprecision` text now has a citation.

### Batch 4 — Ch4 §"Algorithmic Structure of the Implementation" reflow (Philip's main §4.2 critique)

**Target:** `Chapter4/chapter4.tex` `\section{Algorithmic Structure of the Implementation}` (line 31, ending around line 136).

**Edits:** Re-cluster the current 6+ fragmented prose paragraphs into **three** coherent paragraphs, in this order:

1. **Data layout and per-cell arithmetic.** The cell-major layout, the four Euler variables per cell, the same indexing for CPU loops and GPU kernels, the comparability-not-throughput trade-off. Currently split between lines 40–44 and a duplicate sentence around line 107. **Eliminate the duplicate "cell-major" mention.**
2. **CFL selection, write path, and time accumulation.** The CFL scan as ordered max/min, no FP summation reductions on the write path, Kahan-compensated time counter. Currently scattered across lines 45–60 and 107.
3. **CUDA/OpenMP threading, warp divergence, and MPI absence.** The kernel decomposition for CUDA (boundary, face-state, flux, conservative update, block-wise CFL reduction), the HLLC flux kernel as principal warp-divergence site, OpenMP static schedule for CPU sweeps, `reduction(max:…)` is a deterministic comparison, MCA serial PRNG, no MPI. Currently scattered across lines 107–114.

Algorithm 1 (`alg:step-dispatch`), Algorithm 2 (`alg:muscl-hancock`), and Algorithm 3 (`alg:hllc-flux-select`) stay where they are.

**Budget:** 0 / −80 (net consolidation; the duplicate "cell-major" sentence and the looped short sentences contribute most of the reduction).

**Acceptance:** the string "cell-major" appears at most twice in this section (once in the data-layout paragraph, once in the CUDA paragraph for context); paragraph count in this section is 3 prose paragraphs + 3 algorithm environments; texcount drops by 60–100 words.

### Batch 5 — Ch4 later sections: same-style reflow

**Target sections (`Chapter4/chapter4.tex`):**

- `\section{Precision and Hardware Variants}` (line 138).
- `\section{Test-Case Matrix and Metrics}` (line 205).
- `\section{Reference-Solution Strategy}` (line 292).
- `\section{Regression and Reproducibility Harness}` (line 327).

**Edits:** lighter-touch version of Batch 4. For each section, identify any run of four or more short sentences and merge into longer coherent paragraphs grouped by idea (precision axis / hardware axis / compiler axis; references for 1D / for 2D LW3 / for 2D LW12; etc.). Apply forbidden-phrase grep.

**Budget:** 0 / −40.

**Acceptance:** each of the four target sections passes the forbidden-phrase grep gate; texcount drops by 30–60 words combined.

### Batch 6 — Ch6 first-use definitions + Verificarlo cross-ref

**Target sections (`Chapter6/chapter6.tex`):**

- `\section{Precision Adequacy and Region-Aware Diagnostics}` (line 5), specifically lines 18 (LoSoS) and 20 (`s_req`).
- `\paragraph{Ratio framing.}` (line 47).
- `\section{Hardware and Implementation Sensitivity}` (line 66) — light coherence pass only.

**Edits:**

1. Before line 18 (current first use of LoSoS), insert ~25 words: "The **loss-of-significance score** (LoSoS) for a quantity $q$ at cell $\mathbf{x}$ is $\mathrm{LoSoS}(\mathbf{x}) = -\log_{10}\bigl(\sigma_{\mathrm{FP},q}(\mathbf{x})/|q(\mathbf{x})|\bigr)$, the number of base-10 digits of $q$ that remain significant under the MCA noise scale $\sigma_{\mathrm{FP},q}$ defined in Chapter 4." Verify exact definition against `scripts/figures/report1_d2_replots.py` or whichever script computes the field before locking the formula.
2. Before line 20 (current first use of $s_{\mathrm{req}}$), insert ~15 words defining it (number of significant digits required at the chosen reference error scale). Cite Sohier et al. 2021 (already in bib).
3. Update the Verificarlo first prose mention in this chapter to `\citet{denis_etal_2016}` style with explicit cross-reference: "(see Chapter 2 §\emph{Verificarlo and Monte Carlo Arithmetic})".
4. Apply anti-AI-tone grep to all three target sections.

**Budget:** +40 / 0.

**Acceptance:** LoSoS and $s_{\mathrm{req}}$ each have a definition sentence before any later use; Verificarlo cross-reference resolves; forbidden-phrase grep clean.

### Batch 7 — Preamble: siunitx scientific-notation switch + listings setup

**Target files:**

- `report1/phd-thesis-template-2.4/Preamble/preamble.tex` (currently configures siunitx at lines 102–109; does not load `listings`).

**Edits:**

1. Modify the existing `\sisetup{...}` block at lines 102–109:
   - Replace `output-exponent-marker = \ensuremath{\mathrm{e}}` with `output-exponent-marker = {}` (so the exponent renders as a true superscripted power-of-ten, not the literal `e`).
   - Add `scientific-notation = true` so all `S`-column values render as `$X.XX\times10^{Y}$`.
   - Keep `exponent-product = \times` (already present).
   - Keep `table-format = 1.3e-2` and the other alignment settings (these still parse the `e-2` style on input, even when output is scientific).
2. Add `\usepackage{listings}` and a `fpListing` listings style block:
   ```latex
   \usepackage{listings}
   \lstdefinestyle{fpListing}{
     basicstyle      = \ttfamily\footnotesize,
     keywordstyle    = \color{fpDarkBlue}\bfseries,
     commentstyle    = \color{fpGray}\itshape,
     stringstyle     = \color{fpCyanGreen},
     showstringspaces= false,
     frame           = lines,
     framerule       = 0.4pt,
     rulecolor       = \color{fpGray},
     numbers         = none,
     captionpos      = b,
     breaklines      = true,
     language        = C++,
   }
   ```
3. Build pass: run `pdflatex` and visually verify Tables 5.1, 5.3, 5.4, 5.5, 5.6, 5.7 render `$9.34\times10^{-8}$`-style entries.

**Budget:** 0 / 0 (preamble change does not count in texcount).

**Acceptance:** pdflatex clean build; spot-check at least three result-table entries in the rendered PDF for `\times 10^{...}` formatting.

### Batch 8 — Anti-AI-tone polish across all subsections (dedicated U1 batch)

**Target files:** every chapter file.

**Sub-batches (one sub-agent dispatch per chapter file to keep diffs reviewable):**

- 8a: `Chapter1/chapter1.tex` — all four (now five) sections.
- 8b: `Chapter2/chapter2.tex` — all four (now five) sections.
- 8c: `Chapter3/chapter3.tex` — all six sections + their `\paragraph{}` blocks.
- 8d: `Chapter4/chapter4.tex` — all six sections (light-touch follow-up to Batches 3b/4/5).
- 8e: `Chapter5/chapter5.tex` — all seven sections + two `\subsection*{}` blocks.
- 8f: `Chapter6/chapter6.tex` — all three sections (light-touch follow-up to Batch 6).
- 8g: `Chapter7/chapter7.tex` — all three sections.
- 8h: `Abstract/abstract.tex` — same gate.

Each sub-batch gets the forbidden-phrase list from §3 and the style targets. Sub-agent runs:

1. Grep the forbidden list in the target file; for each hit, rewrite the sentence preserving substance.
2. Subject-clarity pass: for each sentence, name the subject in one or two words. If you can't, rewrite.
3. Length pass: split any sentence over 30 words. If a paragraph has 4+ sentences and none ≤ 10 words, add a short one (or split a medium one). If a paragraph has no sentence ≥ 20 words, glue two related short ones with a real connective.
4. Rhythm pass: no run of 4+ short sentences and no run of 3+ long sentences inside a paragraph.
5. Plain-register vocabulary: introduce 1–2 plain swaps per major paragraph from the acceptable list in §3 ("drop", "gap", "match", "lines up with", "hits"). One per paragraph minimum, two maximum.
6. Paragraph-opener pass: no paragraph opens by restating its `\section{}` heading; rewrite openers that do.
7. Tricolon audit: cap "X, Y, and Z" patterns at 2 per paragraph.
8. Replace `utilise/utilises`, `leverages`, `showcases`, `facilitates`, and marketing `demonstrates`.

**Budget:** 0 / −60 (net consolidation expected; the rhythm and length rules push toward shorter sentences and naturally shed a few words per section).

**Acceptance per sub-batch:**

- Forbidden-phrase grep returns zero hits in the touched file.
- texcount delta within ±15 of sub-batch budget.
- pdflatex builds.
- Sub-agent reports, for each prose subsection: (a) longest sentence word count, (b) shortest sentence word count, (c) paragraph count. The main process spot-checks that no reported longest > 30 words and that paragraphs with ≥ 4 sentences satisfy the rhythm rule.

## 5. Phase 1.5 — Redundancy and zero-info audit (U7)

**Trigger:** runs unconditionally after Batch 8, before any cuts. Per user instruction U7, cuts are data-driven from this audit, not pre-locked in advance.

**Procedure (main process, single read-through of the post-Phase-1 manuscript):**

1. Snapshot the post-Phase-1 manuscript wordcount. Expected: ~8285 words.
2. Read each chapter end-to-end with fresh eyes. For each section, build two lists:
   - **Redundant-viewpoint list.** Sentences or paragraphs that restate a claim made earlier in the report. Format: `Ch_X §"...", line range, claim restated, where it first appeared`.
   - **Zero-info list.** Sentences that, if deleted, lose nothing the reader needs. Common patterns: meta-restatement of the section purpose; "this is not a claim of X" hedges already established three paragraphs earlier; table captions that paraphrase the surrounding prose verbatim; transition sentences that announce what the next paragraph will say.
3. Cross-chapter overlap pass. For each pair (Ch_i, Ch_j) where i < j, list any concept covered in both with similar wording. Most likely hot spots:
   - Ch2 §"Ideal-MHD Project Context" (after Batch 2d expansion) vs Ch3 §"Extension to Ideal MHD".
   - Ch5 §"Validation Overview" vs Ch6 §"Precision Adequacy and Region-Aware Diagnostics" opening.
   - Ch5 §"Matched CPU/GPU Comparison" closing vs Ch6 §"Hardware and Implementation Sensitivity".
   - Ch6 §"Limitations…" vs Ch7 §"Limitation and Next Step".
4. Output: `experiments/review4_redundancy_audit.md` containing the prioritized cut list. Each entry has (file, line range, current word count, proposed replacement word count, brief rationale). Total proposed cuts must reach **≥ 465 words** to hit the 7820 target.
5. If the audit produces < 465 cuttable words, escalate to the user with the partial list and a small set of borderline candidates (footnote material, citation density, secondary qualifying clauses) before continuing.

**Deliverable:** `experiments/review4_redundancy_audit.md` (≈ 50–80 line items expected).

## 6. Phase 2 — Compression (driven by Phase 1.5 audit)

**Procedure:**

1. Execute the cuts in `experiments/review4_redundancy_audit.md`, highest-priority first (largest savings + least information loss).
2. After every ~150 words of cuts, run `texcount` to see remaining gap.
3. Stop when texcount ≤ 7820 with at least 5-word buffer.
4. Do not exceed the proposed cut list — if you bottom out at, say, 7835 with all proposals executed, escalate; do not improvise additional cuts.

**Acceptance:** texcount ≤ 7820; every cut in the audit list either executed (and a line in the cut log records old/new word count) or explicitly skipped with reason; no batch-1-through-8 additions undone.

## 7. Phase 2.5 — Residual AI-tone audit (U8)

**Trigger:** runs unconditionally after Phase 2 cuts. Per user instruction U8, this catches what survived Batch 8's grep gate.

**Procedure (main process, single targeted read of every prose subsection):**

1. Read each `\section{}` and `\paragraph{}` block. For each, flag any of the following that grep cannot catch:
   - **Rhythm flatness.** A paragraph where all sentences land in the 15–22 word band — no variation.
   - **Subject drift.** A sentence whose subject is "this", "it", "the comparison", "the analysis" without a clear antecedent in the same or previous sentence.
   - **Citation as filler.** A `\citep{}` that adds no information beyond a name the reader has already seen three times.
   - **Hedge stacking.** Two hedges in one sentence ("may also potentially", "could reasonably be expected to").
   - **Tonal whiplash.** A formal-academic sentence followed immediately by a chatty plain-register sentence without a bridge.
   - **Predictable next-word patterns.** Sentences where every word is the most likely next word given the prior — the tell of an LLM rewrite. Inject a plain-register word from the §3 acceptable list, or restructure.
2. For each flag, rewrite in place. Track changes in `experiments/review4_residual_polish.md` (one line per change: file, line, old → new).
3. Build pass after rewrites; texcount delta must be ±20 words from Phase 2 endpoint.

**Acceptance:** at least one flag found and addressed per chapter (Ch1–Ch7), or an explicit statement that the chapter passes clean; texcount remains ≤ 7820; pdflatex builds.

## 8. Phase 3 — final audit

Main process, no further .tex edits:

1. `texcount -inc -sum -1 report1/phd-thesis-template-2.4/thesis.tex` ≤ **7820** (hard cap 7850, safety target 7820).
2. `pdflatex` (or equivalent build chain) clean: no missing refs, no missing citations, no overfull/underfull boxes beyond pre-revision baseline.
3. Grep audits across all chapter files:
   - Forbidden-phrase list from §3 — zero hits.
   - `9.34e-8`-style machine-notation strings — zero hits outside `lstlisting` environments.
   - `LoSoS` and `s_{\mathrm{req}}` each appear with a definition before any later use (regex check on Ch6).
   - `RIEMANN_STRICT_INEQUALITY` cross-reference from Ch3 listing to Ch5 §"Toro Test 2 Branch Stability" resolves.
4. Sentence-length and rhythm spot-check (manual, ~5 minutes):
   - Pick 3 prose paragraphs at random across Ch1–Ch7. Each must contain at least one sentence ≤ 10 words and at least one sentence ≥ 20 words. None over 30 words.
   - Confirm every sentence in the sample has a nameable subject.
5. Citation check (every new bib key from §1 mapped to ≥ 1 `\citep{}` in the touched chapter):
   - `sterbenz_1974`, `maddock_boost_multiprecision` cited (Batches 2a, 3b).
   - `denis_etal_2016` cited in new §"Verificarlo and Monte Carlo Arithmetic" (Batch 2b).
   - `kahan_1965` cited explicitly on the compensated-summation sentence (Batch 2a).
   - `collange_etal_2015`, `revol_theveny_2014`, `kulisch_2013` cited in §"Floating-Point Arithmetic and Reproducibility" reduction-order paragraph (Batch 2e).
   - `bailey_borwein_borwein_2015` cited near the higher-precision-route sentence (Batch 2e).
   - `brio_wu_1988` cited in §"Ideal-MHD Project Context" Euler-vs-MHD structural difference paragraph (Batch 2d).
   - `einfeldt_1988` cited at least once (Ch2 or Ch3 HLL-family reference).
6. Visual spot-check on the rendered PDF for: Ch1 reads top-down as an overview; new Ch2 sections (Finite-Volume Derivation Overview, Verificarlo and Monte Carlo Arithmetic) appear in the ToC; the two `lstlisting` blocks render legibly; Tables 5.1–5.7 use $X.XX\times10^{Y}$ formatting; MHD wave-speed physical-meaning paragraph reads as background, not method.

## 9. Non-goals

- No new experiments, no new figures beyond regenerating existing ones if the siunitx change accidentally reflows a table.
- No solver / cfg / harness / build-system changes.
- No new chapters or new sections beyond §1.1 "Physical Applications and Reproducibility", new Ch2 §"Finite-Volume Derivation Overview" (Batch 2c), and new Ch2 §"Verificarlo and Monte Carlo Arithmetic" (Batch 2b).
- No restructuring of Chapter 5 — it survived three prior review rounds intact; touched only by Batch 7 (table format) and Batch 8e (tone polish).
- No re-running the MCA experiment matrix or rebuilding figures from raw data.

## 10. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Phase 1.5 redundancy audit finds < 765 cuttable words (the post-Phase-1 overshoot) | **medium** | Escalate to user with the partial cut list before continuing; do not improvise additional cuts. Two escalation levers documented in §2: re-trim Batch 1's Ch1 §1.1; or pull additional content from Ch7 §"Key Findings" which currently restates Ch5/Ch6 quantitative results. |
| New Ch2 substantive sections (2c, 2d, 2e) push manuscript past 8585 before any cuts | **high** | Built into the spec: Phase 1 finishes at ~8585, Phase 1.5 + Phase 2 do the heavy compression. |
| Ch3 §"Extension to Ideal MHD" overlaps too heavily with new Ch2 MHD content after Batch 2d | medium | Phase 1.5 explicitly flags this pair; expect a 60–100 word collapse in Ch3 to one short summary paragraph that defers to Ch2. |
| siunitx scientific-notation switch reflows table widths | low | Build pass after Batch 7; if reflow occurs, narrow column widths case-by-case. |
| `lstlisting` blocks push a figure or table to a new page in a way that creates a long stretch of whitespace | low | Use `[tbp]` placement; sub-agent must check the resulting PDF. |
| Anti-AI grep rule eats genuine domain phrasing (e.g. "robust" in a legitimate "robust HLLC wave-speed estimate" sentence) | medium | Manual review on every hit; the grep gate is a signal, not an auto-rewrite. |
| Source-file listings drift from actual source | low | Each listing batch (3a, 3b) is required to read the source file before pasting; sub-agent envelope cites the exact source path and line range. |
| Adding §1.1 breaks `Report Structure` line about "Chapters~2--4 establish background, method, and design" | none | Chapter 1 sections don't appear in that summary; ToC auto-renumbers. |

## 11. Out of scope (deferred to Report 2 if relevant)

- Cross-compiler matrix (Philip raised this in earlier rounds; deferred and noted in Ch6 limitations).
- AMR / AMReX comparison.
- MHD validation (entire Report 2 scope).
- Quad-precision via Boost.Multiprecision (now cited, but evidence-out-of-scope statement retained).
