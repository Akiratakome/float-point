# Chapter 6 Dispatch Prompt

This prompt drives the first substantive draft of Report 1 Chapter 6,
"Discussion". The current `Chapter6/chapter6.tex` is a four-section TODO
skeleton; this round writes the actual synthesis prose under those headings,
applies the supervisor-feedback constraints, and prepares Chapter 6 as the
synthesis layer above the finalized Chapter 5 evidence.

It follows the dispatch and verification flow of
`report1/planning/chapter5_supervisor_feedback_dispatch_prompt.md`, but the
content requirements come from the manuscript outline's §6 plan, the supervisor
feedback map's Chapter 6 entries, the supervisor guide, the finalized Chapter
1-5 text, and the named evidence artifacts.

---

## Master prompt

You are the main agent for the Report 1 Chapter 6 drafting round. Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Target manuscript file:

```text
report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

This round drafts only Chapter 6, "Discussion". Chapter 6 is the synthesis
layer: it introduces no new results, no new figures, and no case-by-case
restatement of Chapter 5. It interprets what the validation, precision, and
hardware evidence already shown in Chapters 4 and 5 mean for the project
question, within the explicit boundaries of the tested cases.

### Required reading

Read these files before editing or dispatching workers:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/planning/reportagents.md`
5. `report1/planning/manuscript_outline.md` (especially the Chapter 6 plan
   and the Conclusion evidence lock under Chapter 7)
6. `report1/planning/supervisor_feedback_map.md` (Chapter 6 and Chapter 7
   entries, plus Binding Global Rules)
7. `report1/planning/supervisorguide.md` (use only to verify the map if
   ambiguous)
8. `experiments/report1_evidence_map.md`
9. `report1/references/reference.md`
10. `report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`
    (the project brief; check that the five 20% categories and the six
    handbook criteria are still satisfied after Chapter 6 is added)
11. `report1/phd-thesis-template-2.4/Chapter1/chapter1.tex`
12. `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
13. `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
14. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`
15. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
16. `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`
17. `report1/phd-thesis-template-2.4/Chapter7/chapter7.tex`
18. `report1/phd-thesis-template-2.4/References/references.bib`
19. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison. The old per-chapter dispatch prompts are no longer
authoritative.

Read these style skills before editing manuscript prose, and read them again
before final prose polishing:

```text
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/academic-english-style/SKILL.md
report1/skills/scientific-writing-duke/SKILL.md
```

### Main-agent role

- Do not draft the whole chapter in one pass. Dispatch the four section-scoped
  workers serially.
- Never let two workers edit `chapter6.tex` simultaneously.
- Tell every worker: "You are not alone in the codebase; do not revert or
  overwrite edits outside your assigned marker region."
- Workers edit only their assigned section marker region.
- The main agent integrates results, runs the verification block, and performs
  small consistency fixes only after workers finish.
- Do not modify solver numerics, cfg defaults, experiment output formats, raw
  experiment artifacts, or anything under `experiments/`.
- Chapter 6 is synthesis prose; it must not introduce new figures, new tables,
  or new evidence rows. If a worker believes a new figure is needed, stop and
  report the gap instead of regenerating any artifact.
- Citations are allowed only when they support a specific synthesis sentence
  and are already on the manuscript's existing citation list or in
  `report1/references/reference.md`. Do not introduce new bibliography entries
  in this round.
- The "no new figures" rule has a **scoped exception in §6.2 only**.
  Chapter 5 §5.4 closes with the sentence "Virtual-precision sensitivity
  maps are discussed separately in Chapter 6 rather than used as direct
  fp32 evidence here", explicitly delegating the region-aware precision
  diagnostic figures to §6.2. Worker B includes **two** of the existing
  diagnostic figures listed under "Approved §6.2 figures" below (a third
  is allowed only if the word budget still permits and it carries an
  otherwise-missing claim). The figure files already exist under
  `Figs/report1/`; their generation provenance is recorded in this
  prompt for traceability, not in the manuscript prose. Workers A, C,
  and D introduce no new figures.

### Approved §6.2 figures (existing under `Figs/report1/`)

The evidence map lists six region-aware Verificarlo / MCA diagnostic
figures at P0. One of them
(`float_double_over_reference_bar.png`) is already in Chapter 5 §5.4
carrying the direct fp32/fp64-vs-reference claim. The remaining five
have no other manuscript home, so §6.2 is the only place they can
appear without breaking the evidence-map P0 coverage. The original
"D2" label is planning vocabulary; introduce the figures in prose by
their content (for example "the LoSoS quantile view for LW3 density",
"the region-aware LoSoS-margin map at Verificarlo `p32`", "the σ\_FP
versus virtual-precision trend", "the noise-to-error spatial map across
virtual precisions"), not as "D2 figures".

**Required default set — four figures.** Worker B includes all four
unless a figure file is genuinely missing or unreadable, in which case
Worker B stops and reports the gap rather than silently dropping it.

| Figure file (under `Figs/report1/`) | Claim it carries | Role inside §6.2 |
|---|---|---|
| `sigma_fp_vs_precision.png` | `σ_FP` decreases as virtual precision rises; HLLC and Rusanov are contrasted on the same axes, so the curve also carries a solver-dependence reading | Block 2: anchors the σ\_FP local-roundoff-scale definition with a global trend; the HLLC-vs-Rusanov contrast links back to the Chapter 5 §5.6 method-variation evidence |
| `losos_quantiles_rho.png` | q05 / q25 / median significant-digit budget for LW3 density, used to avoid worst-cell artifacts | Block 3: gives the statistical view of LoSoS that the region figure cannot give; lets the prose qualify any quantile statement by the small MCA sample size |
| `region_losos_margin_rho_p32.png` | the per-region required-significant-digits margin at Verificarlo `p32` (smooth / transition / front bands) | Block 3: visual basis for the LoSoS / s\_req inline definitions and for the "where precision pressure concentrates" sentence |
| `noise_to_error_ratio_heatmap_grid_rho.png` | the spatial map of FP noise over physical / discretisation error across `p8 / p16 / p32` | Block 3: shows the spatial structure of the noise-to-error ratio and how it shrinks as virtual precision rises |

The four figures together cover the LoSoS direction (one quantile + one
region view), the σ\_FP direction (one global trend), and the
noise-to-error direction (one spatial heatmap), spanning all three
diagnostic vocabularies introduced in Block 2.

**Deliberately omitted P0 figure** (record in the dispatch summary
only; do *not* mention the omission in the manuscript prose).

| Figure file | Reason it is not included |
|---|---|
| `region_noise_to_error_ratio_precision_grid_rho.png` | This is the region-aggregated companion to the spatial heatmap. Its claim — the noise-to-error ratio resolved by region and virtual precision — is already supported by reading the region LoSoS margin (`region_losos_margin_rho_p32.png`) and the spatial noise heatmap (`noise_to_error_ratio_heatmap_grid_rho.png`) together. Including it would push §6.2 past its 430-500 word range without a new claim. |

This 4 + 1 split means §6.2 consumes five of the six region-aware P0
figures (the bar figure already in C5 plus the four required-default
figures above); the single P0 omission is documented above with a
reason. Worker B confirms in the dispatch summary that all four
required-default figures were included.

**Fallback only if a required-default figure file is genuinely missing
or unreadable after LaTeX scaling.** Stop and report the gap before
substituting; do not silently drop a required-default figure. If the
substitution is approved, substitute the omitted
`region_noise_to_error_ratio_precision_grid_rho.png` and retarget the
relevant Block 3 sentences. Record the substitution in the dispatch
summary.

Provenance to record in the dispatch summary (not in manuscript prose):
`experiments/week7/report1_d2_replots/summary.md` and the matching CSVs
`region_losos_quantiles_rho.csv` and `float_double_over_reference.csv`.

### LoSoS, s_req, and σ\_FP terminology lock (binding for §6.2 prose)

LoSoS, s\_req, and σ\_FP are project-specific Monte-Carlo-Arithmetic-derived
diagnostics. They are not standard literature terms, and the manuscript does
not currently define LoSoS or s\_req anywhere. Therefore:

- **σ\_FP** is already introduced in Chapter 4 §4.3 as
  `σ_FP,j = std_k(q_j^(k))`. §6.2 must not redefine it; instead cite "the
  σ\_FP local roundoff scale of Chapter~4 §4.3". The C4 definition is inline
  math without an equation label, so the reference must be textual (Chapter
  number plus section number), not `\eqref`.
- **R\_ref** is defined in Chapter 4 Equation~\ref{eq:ch4-rref}. §6.2 cites
  it via `\eqref{eq:ch4-rref}` rather than restating the formula.
- **LoSoS (Loss of Significance)** must be defined on its first §6.2 use, in
  one short clause: "the loss-of-significance score LoSoS, the number of
  significant digits lost relative to the field magnitude under MCA
  resampling". Cite Parker (1997) and Denis et al. (2016) at that first use.
- **s\_req (required significant digits)** must be defined on its first
  §6.2 use, in one short clause: "s\_req, the per-cell number of significant
  digits required so that the MCA-estimated rounding noise stays below the
  target ratio of the local field magnitude". Do not include the full
  derivation; this is a synthesis chapter.
- Use "Verificarlo virtual precision `p32`" (with backticks or `\texttt{}`)
  rather than bare `p32`, to keep the IEEE distinction visible on every
  mention.

The corresponding evidence files are
`experiments/week7/report1_d2_replots/region_losos_quantiles_rho.csv` and
`experiments/week7/report1_d2_replots/summary.md`. Quantitative values
quoted in §6.2 must trace to one of these files. The MCA sample size is
small (typically 30 samples); §6.2 must note this once when LoSoS or
σ\_FP quantiles are discussed.

### Chapter 6 section markers

The current Chapter 6 file uses bare TODO comments. Before Worker A starts,
the main agent inserts the marker block below into
`report1/phd-thesis-template-2.4/Chapter6/chapter6.tex` so that each worker
has a well-defined region. The TODO comments are removed at the same time;
the worker prose replaces them under the markers.

```latex
%!TEX root = ../thesis.tex

\chapter{Discussion}

\section{Validation as the basis for interpretation}
% <<SECTION_1_BEGIN>>
% <<SECTION_1_END>>

\section{Precision Adequacy and Region-Aware Diagnostics}
% <<SECTION_2_BEGIN>>
% <<SECTION_2_END>>

\section{Hardware and Implementation Sensitivity}
% <<SECTION_3_BEGIN>>
% <<SECTION_3_END>>

\section{Limitations and Report 2 Direction}
% <<SECTION_4_BEGIN>>
% <<SECTION_4_END>>
```

The section titles match the §6.1-§6.4 ownership in
`manuscript_outline.md`. Do not change them in this round once inserted.
Two titles are deliberately updated from the original
`Chapter6/chapter6.tex` stub so that the table of contents reflects the
final ownership: §6.1 from "Validation Scope" to "Validation as the
basis for interpretation" (synthesis framing); §6.2 from "Precision
Effects Relative to Numerical Error" to "Precision Adequacy and
Region-Aware Diagnostics" so the table of contents shows that the
precision-adequacy direction (region-aware Verificarlo diagnostics,
σ\_FP, LoSoS, s\_req, noise-to-error) lives here, not in Chapter 5. Do
not remove the markers once inserted.

### Chapter 6 ownership lock

Chapter 6 owns synthesis only:

- §6.1: how the validation evidence enables precision and hardware
  interpretation, including the validation scope (which cases were tested,
  which references were used, which axes were measured).
- §6.2: direct fp32/fp64 interpretation scaled against reference or
  discretisation error, **and** the Verificarlo virtual-precision regional
  interpretation, with an explicit distinction between Verificarlo `p32`
  (virtual mantissa) and IEEE binary32/fp32.
- §6.3: matched CPU/GPU evidence (final-time and saved-checkpoint), compiler,
  branch-rule, solver, fp32 compiler-flag, and finite-time drift sensitivity,
  read across axes rather than case-by-case.
- §6.4: bounded limitations grouped by evidence type, and the MHD Report 2
  direction.

Chapter 6 must not:

- repeat Chapter 5's case-by-case results;
- restate Chapter 4's design-matrix rationale or Chapter 3's method derivation;
- present `p32` virtual precision as IEEE fp32 evidence;
- present MHD as a completed Report 1 result;
- generalise beyond tested Euler cases, tested precisions, tested grids,
  tested compiler settings, tested toolchain, and named evidence artifacts;
- introduce new citations beyond the existing manuscript citation set.

### Word-budget lock

Current Overleaf-counted state (recorded before this round starts):
Chapters 1-5 plus the legacy Chapter 7 stub together count **6415**
words. The Report 1 hard cap is 7500 counted words and the drafting
target is 7400, so the remaining envelope for Chapter 6 plus any later
Chapter 7 revision is at most **1085** words against the hard cap, and
about **985** words against the drafting target.

Working target for Chapter 6: **850-950** counted words, hard upper
**1000**. This raises the original manuscript-outline range (650-750)
because §6.2 now owns the precision-adequacy direction (region-aware
Verificarlo / MCA diagnostics, σ\_FP, LoSoS, s\_req, and the
noise-to-error reading) for the whole report and requires detailed
elaboration. The remaining 85-235 words inside the chapter cap are held
back for two reasons: any Chapter 7 compression/merge that the
follow-up round needs to fit; and Overleaf-counting surprises in
algorithm and equation environments. Tables and figure captions are
excluded from the count; pseudocode lines are counted but Chapter 6
adds no pseudocode.

| Section | Working range |
|---|---|
| §6.1 Validation as the basis for interpretation | 100-120 |
| §6.2 Precision, Verificarlo virtual precision, and region-aware adequacy | 430-500 |
| §6.3 Hardware and implementation sensitivity | 220-250 |
| §6.4 Limitations and Report 2 direction | 100-130 |
| **Sum** | **850-1000** |

Compression order if the chapter total approaches the 1000 hard upper:
compress §6.3 first, then §6.1, then §6.4. Do not cut §6.2 below 430
words, because §6.2 is the load-bearing reason this chapter exists in
its expanded form. Do not cut the Verificarlo/IEEE-fp32 distinction, the
LoSoS / s\_req definitions, the σ\_FP cross-reference, or the
toolchain-split boundary under any budget pressure.

After this round, verify in Overleaf that Chapters 1-6 plus the legacy
Chapter 7 stub remain ≤ 7400 counted words (drafting target) and ≤ 7500
(hard cap). If the total exceeds 7400, log the exact value and do not
silently cut §6.2 detail; raise the overshoot in the final response so
the follow-up Chapter 7 round can absorb it.

### Hard language and evidence rules

- Every quantitative claim in Chapter 6 must correspond to an evidence file
  already named in `experiments/report1_evidence_map.md`, Chapter 5, or the
  Conclusion evidence lock in `manuscript_outline.md`. Do not invent numbers.
- Prefer qualitative synthesis. Quote a specific value only when it changes
  the conclusion (for example, the LW12 N=400 fp32-vs-fp64 reference-scaled
  ratio used in §6.2).
- Do not use manuscript-facing internal labels. All of the following are
  writing-planning vocabulary only and must not appear in Chapter 6 prose,
  captions, headings, figure labels, table notes, or bibliography entries:
  - week labels: `week2`, `week3`, `week4`, `week5`, `week6`, `week7`,
    `week8`, `week9`;
  - evidence-priority labels: `P0`, `P1`, `P2`, `P3` (these are
    `experiments/report1_evidence_map.md` priority tags, not paper
    content);
  - direction labels: `D1`, `D2` (these are evidence-map axis labels for
    "direct drift" and "precision adequacy"; in prose use descriptive
    forms such as "the precision-adequacy diagnostics" or "the
    reproducibility/drift evidence");
  - case nicknames and harness names: `HLLC-fill`, `config12`,
    `LW12/config12`;
  - build-priority/internal labels: `P1 probe`;
  - source-code constants used as labels: `USE_GPU` (the manuscript uses
    `ENABLE_CUDA` when a build flag must be named).
- Use "Liska-Wendroff configuration 3 (LW3)" and
  "Liska-Wendroff configuration 12 (LW12)" at first mention in this chapter,
  then "LW3" and "LW12".
- Verificarlo `p32` is virtual mantissa precision used for Monte Carlo
  Arithmetic diagnostics; it is **not** IEEE binary32/fp32. The first
  Verificarlo mention in §6.2 must state this explicitly. Direct IEEE fp32
  adequacy or inadequacy statements must come from real fp32/fp64 runs, not
  from `p32` diagnostics.
- Do not use "Lyapunov exponent" or "Lyapunov-like". Time-resolved evidence
  is finite-time drift over saved checkpoints.
- Do not cite `wolf_etal_1985` or `eckmann_ruelle_1985`.
- Compiler flags must not appear as long prose strings. If Chapter 6 needs to
  name a flag, refer back to the Chapter 3 / Chapter 4 listing or use a short
  in-line code form. Do not introduce a new flag listing or table.
- Use "comparisons", "entries", or "experiments" rather than the generic
  "rows" the supervisor flagged; "rows" is allowed only when pointing to a
  specific table.
- Use author-name prose when introducing specific methods or tools (for
  example, "Higham's", "Goldberg's", "Denis and colleagues' Verificarlo")
  before the citation, rather than relying only on parenthetical citations.
- Saved-checkpoint CPU/GPU evidence does not prove equality of intermediate
  stage values inside a time step. State this boundary whenever §6.3 reads
  the checkpoint evidence across axes.
- The CPU/GPU **toolchain split** must be named in §6.3: Toro3 and Toro5 use
  Windows BuildTools; Sod, LW3, and LW12 use Linux/WSL; each within-case
  CPU/GPU comparison uses one matched binary/configuration. This was promised
  in the manuscript outline as a three-place disclosure (Chapter 4, Chapter
  5, Chapter 6/7); §6.3 is the Chapter 6 instance.
- Bard and Dorelli (2014) is citation-capped at two appearances across the
  whole manuscript. Check Chapters 1-5 before reusing it in §6.4; do not push
  the count above two.
- AI-assisted prose must satisfy `avoiding-ai-flavor`: no generic filler, no
  marketing tone, no unsupported confidence, no triadic "X, Y, and Z" cadence
  in three consecutive sentences, and no paragraph that could fit an unrelated
  dissertation.

### Conclusion-merge coordination

The supervisor recommended either removing Chapter 7 entirely or compressing
it to 150-220 words. This dispatch round writes Chapter 6 first; Chapter 7
is handled in a separate pass. Two practical consequences for this round:

1. §6.4 should give a clean, self-contained limitations + Report 2 direction
   ending, so that if Chapter 7 is later removed, §6.4 already carries the
   forward-looking boundary.
2. Do not duplicate the Conclusion evidence-lock claims verbatim. §6.4 may
   summarise the boundaries; Chapter 7 (or its merge into §6.4) will quote
   the specific findings.

Do not delete or rewrite `Chapter7/chapter7.tex` in this round. If the
Chapter 1 roadmap references Chapter 7, leave it untouched until the Chapter
7 decision pass.

### P0 evidence coverage audit (compare against `experiments/report1_evidence_map.md`)

This table tracks which P0 evidence artifacts each Report 1 chapter
consumes, so this Chapter 6 round can see what is already used elsewhere
and what §6.2 brings in for the first time. "C5" means the artifact's
result is already cited/figured in Chapter 5; "C6 §6.x" means this round
adds the synthesis use; "—" means the artifact is not used in the main
text and should not be added in this round.

| P0 artifact (evidence map) | C5 use | C6 use (this round) |
|---|---|---|
| `week7/report1_validation_1d/summary.md` | §5.2 1D table | §6.1 (synthesis only, no values) |
| `week3/.../sod_comparison.png`, `toro3_comparison.png`, `toro5_comparison.png` | §5.2 figures | — (no re-use) |
| `week4/float_regression/1d/summary.md` | §5.4 1D ratios | §6.2 Block 1 (reference scale) |
| `week7/report1_validation_2d/summary.md` and LW3 schlieren | §5.3 LW3 table + figure | §6.1 (synthesis only) |
| `week4/float_regression/2d/summary.md` | §5.4 LW3 ratios | §6.2 Block 1 |
| `week8/.../report1_2d_config12_fill/summary.md` + LW12 schlieren | §5.3 LW12 table + figure | §6.1 |
| `week8/.../config12_reference_metrics.csv` and `reference_comparison/summary.md` | §5.4 LW12 ratios | §6.2 Block 1 (LW12 $R_\rho\approx 1.30\times10^{-4}$) |
| `week7/report1_validation_1d_device/.../toro3_toro5_hllc_strict.md` | §5.5 CPU/GPU table | §6.3 |
| `week7/report1_validation_2d_device/.../hllc_strict_double.md` | §5.5 | §6.3 |
| `week7/report1_validation_2d_gpu/summary.md` | upstream of §5.5 device file | — (covered transitively) |
| `week8/report1_device_hllc_fill/.../sod_lw3fp32_hllc_strict.md` | §5.5 | §6.3 |
| `week8/.../cpu_vs_gpu_config12_hllc_strict.md` | §5.5 | §6.3 |
| `week9/cpu_gpu_midtime/summary.md` and `cpu_gpu_midtime_n400/summary.md` | §5.5 saved-checkpoint sentence | §6.3 (saved-output boundary) |
| `week7/report1_variation/summary.md` and `axis_*` files | §5.6 variation table | §6.3 (compiler/branch synthesis) |
| `week8/report1_variation_extend/summary.md` | §5.6 Toro3/Toro5 fast-math entry | §6.3 |
| `week9/variation_fp32/summary.md` and `variation_fp32_extend/summary.md` | §5.6 fp32 flag table | §6.3 (fp32 compiler synthesis) |
| `week7/lyapunov_1d_full/summary.md` + drift figure | §5.6 drift figure | §6.3 (finite-time drift reading) |
| `week8/toro2_lt_branch_retry/summary.md` | §5.6 Toro2 non-completion sentence | §6.4 (runtime/non-completion limit) |
| `week7/report1_d2_replots/float_double_over_reference_bar.png` | §5.4 bar figure | §6.2 Block 1 (verbal cross-reference) |
| `week7/report1_d2_replots/sigma_fp_vs_precision.png` | — | **§6.2 Block 2 (required-default figure 1 of 4; new in this round)** |
| `week7/report1_d2_replots/losos_quantiles_rho.png` | — | **§6.2 Block 3 (required-default figure 2 of 4; new in this round)** |
| `week7/report1_d2_replots/region_losos_margin_rho_p32.png` | — | **§6.2 Block 3 (required-default figure 3 of 4; new in this round)** |
| `week7/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png` | — | **§6.2 Block 3 (required-default figure 4 of 4; new in this round)** |
| `week7/report1_d2_replots/region_noise_to_error_ratio_precision_grid_rho.png` | — | **deliberately omitted with documented reason** (region-aggregated companion to the spatial heatmap; the same region+precision claim is already supported by reading the region LoSoS margin and the spatial noise heatmap together; including it would push §6.2 past the 430-500 word range without adding a claim). Used as the readability fallback if `region_losos_margin_rho_p32.png` cannot be made legible. |
| `week7/report1_d2_replots/summary.md` + CSVs | upstream of region-aware figures | quoted only for sample-count and quantile values |
| `week9/gpu_strict_vs_fast/summary.md` (P1) | §5.6 "supplementary GPU flag probe" | §6.3 (build-control boundary, one sentence) |
| `week9/variation_limiter/summary.md` (P1) | §5.6 limitation sentence | §6.4 (limiter scope limit, one mention) |
| `week6/regression/summary.md` (P1 harness provenance) | C4 harness narrative | — (not synthesis evidence) |
| `week9/report1_square_figures/summary.md` (P1) | figure provenance only | — (not cited in prose) |

**P0 completeness rule.** If any artifact in the P0 rows above is
**not** already in Chapter 5 and is **not** picked up by §6.2 / §6.3 /
§6.4 here, stop and report the gap rather than silently dropping the
evidence. The four artifacts newly consumed in this round
(`sigma_fp_vs_precision.png`, `losos_quantiles_rho.png`,
`region_losos_margin_rho_p32.png`,
`noise_to_error_ratio_heatmap_grid_rho.png`) close the evidence-map P0
gap on the Verificarlo / MCA region-aware diagnostics; without them
Report 1 would omit four P0 evidence rows that the supervisor expects
§6.2 to interpret. The single P0 artifact that this round deliberately
does not include
(`region_noise_to_error_ratio_precision_grid_rho.png`) is the
region-aggregated companion to the spatial heatmap; the dispatch summary
must record this omission with its reason so the audit is complete.
After this round, **29 of 30 P0 artifacts in the evidence map have a
manuscript home**, and the single omission is documented and traceable.

### Evidence by worker

Before editing, each worker rereads `experiments/report1_evidence_map.md` and
the finalized Chapter 5 prose. Workers must not introduce evidence that is
not already in Chapter 5 or the Conclusion evidence lock.

| Worker | Required evidence anchors (already in C4/C5) |
|---|---|
| A, §6.1 Validation as the basis for interpretation | Chapter 4 design matrix and metric definitions; Chapter 5 §§5.1-5.3 1D/2D validation; `experiments/week7/report1_validation_1d/summary.md`; `experiments/week4/float_regression/1d/summary.md`; `experiments/week7/report1_validation_2d/summary.md`; `experiments/week8/report1_2d_config12_fill/summary.md`; `experiments/week8/report1_2d_config12_fill/config12_reference_metrics.csv` |
| B, §6.2 Precision and Verificarlo virtual precision | Chapter 5 §5.4 fp32/fp64 comparison; `experiments/week4/float_regression/1d/summary.md`; `experiments/week4/float_regression/2d/summary.md`; `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md`; `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png`; `experiments/week7/report1_d2_replots/region_losos_margin_rho_p32.png`; `experiments/week7/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png`; `experiments/week7/report1_d2_replots/region_losos_quantiles_rho.csv`; `experiments/week7/report1_d2_replots/summary.md` |
| C, §6.3 Hardware and implementation sensitivity | Chapter 5 §§5.5-5.6 CPU/GPU + variation evidence; `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`; `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`; `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md`; `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md`; `experiments/week9/cpu_gpu_midtime/summary.md`; `experiments/week9/cpu_gpu_midtime_n400/summary.md`; `experiments/week7/report1_variation/summary.md`; `experiments/week8/report1_variation_extend/summary.md`; `experiments/week9/variation_fp32/summary.md`; `experiments/week9/variation_fp32_extend/summary.md`; `experiments/week7/lyapunov_1d_full/summary.md`; `experiments/week8/toro2_lt_branch_retry/summary.md` |
| D, §6.4 Limitations and Report 2 direction | The Conclusion evidence lock in `manuscript_outline.md`; `experiments/week9/variation_limiter/summary.md` (limiter status only); the project brief PDF for the MHD scope; existing Chapter 2 §2.2 MHD framing for terminology consistency |

---

## Worker A: §6.1 Validation as the basis for interpretation

Assigned region:

```latex
% <<SECTION_1_BEGIN>>
...
% <<SECTION_1_END>>
```

Goal:

- Write the synthesis opener for Chapter 6 in 100-120 counted words.
- Frame §6.1 as **why the validation evidence makes the later interpretation
  possible**, not as a re-enumeration of the design matrix or the C5
  results. The design matrix is already in Chapter 4 Table~\ref{tab:ch4-design-matrix}
  and the four result questions are already in Chapter 5 §5.1. §6.1 does
  not restate them.
- Make exactly three synthesis points:
  1. exact-Riemann and high-resolution numerical references give the
     fp32/fp64 differences a meaningful scale through
     Equation~\ref{eq:ch4-rref}; without that scale, raw differences would
     be uninterpretable.
  2. matched within-case binaries make the CPU/GPU comparison a strict
     equality test rather than a cross-toolchain comparison.
  3. the variation and drift axes (compiler, branch, solver, fp32 compiler,
     finite-time drift) are read alongside the precision and device axes,
     so implementation-sensitivity claims can be compared on the same case
     set.
- Close with a one-sentence pointer that §6.2-§6.4 read the evidence axis by
  axis, not case by case.

Constraints:

- No new figures or tables; refer back to the Chapter 5 figures verbally if
  needed.
- Do not list the five cases by name (Sod/Toro3/Toro5/LW3/LW12) again; the
  reader already has them from Chapters 4 and 5. §6.1 is the synthesis
  opener, not a validation summary.
- Do not restate the four C5 result questions verbatim.
- Do not introduce new citations.
- Do not promise results that are not in the locked evidence.

---

## Worker B: §6.2 Precision Effects Relative to Numerical Error

Assigned region:

```latex
% <<SECTION_2_BEGIN>>
...
% <<SECTION_2_END>>
```

Section role: §6.2 is **the manuscript home for the precision-adequacy
direction of Report 1**. Chapter 5 §5.4 deliberately stops at direct IEEE
fp32/fp64 comparisons and closes with a pointer here; the region-aware
Verificarlo / MCA diagnostics, the σ\_FP noise scale, the
loss-of-significance score LoSoS, the required-significant-digits
threshold s\_req, and the noise-to-error spatial reading all appear in
this section for the first time and are not duplicated elsewhere. Treat
§6.2 as the most important section in Chapter 6, not as a paragraph of
synthesis hedge.

Goal:

- Develop the precision evidence in 430-500 counted words across three
  conceptual blocks: (i) direct IEEE fp32/fp64 against reference scale,
  (ii) the Verificarlo / MCA diagnostic chain and its vocabulary
  (σ\_FP, LoSoS, s\_req), and (iii) the region-aware noise-to-error
  reading that connects the diagnostic vocabulary to the LW3 spatial
  structure. The three blocks must be visibly distinct but connected; do
  not collapse them into one undifferentiated paragraph and do not pad
  with synthesis hedge.
- **Block 1 — Direct IEEE fp32/fp64 against reference scale (about
  110-140 counted words).** Open with the reference-scaled ratio of
  Equation~\ref{eq:ch4-rref}. The pairwise fp32-fp64 final-state
  differences in the tested cases are small relative to the
  reference/discretisation scale, but the LW12 N=400 density ratio
  $R_\rho \approx 1.30\times10^{-4}$ is quoted explicitly because it is
  the largest value in the tested-set and because the upper-right
  shock-interaction localisation in
  Fig.~\ref{fig:ch5-lw12-precision-heatmap} carries the most informative
  spatial signal. Note the rising-with-resolution pattern as a boundary
  (the reference error shrinks faster than the fp32-fp64 drift) rather
  than a failure. Use the §5.4 stationary-contact infinite ratio as a
  degenerate-reference example, not a precision-failure example. State
  the bounded LW12 interpretation once: the upper-right localisation
  suggests sensitivity where reconstructed states feed HLLC wave-speed or
  flux decisions, but it does not prove a specific HLLC branch changed in
  the available evidence. Close Block 1 with a one-sentence motivation
  for why a separate diagnostic chain is needed: direct fp32-fp64
  ratios collapse all spatial and operation-level information into a
  single norm, so a regionally and operationally resolved diagnostic is
  required to decide *where* precision pressure concentrates.

- **Block 2 — Verificarlo / MCA diagnostic chain and vocabulary (about
  150-180 counted words).** Introduce the diagnostic chain in one or two
  sentences: Parker's Monte Carlo Arithmetic perturbs each
  floating-point operation by an MCA noise model and produces an
  ensemble of perturbed runs; Denis and colleagues' Verificarlo
  implements this for compiled programs. Explain in one short sentence
  why this is the right tool here: a single-run rounding-error estimate
  cannot localise sensitivity, whereas an MCA ensemble produces a
  per-cell distribution from which spatial diagnostics can be built.
  Block 2 includes one figure — the σ\_FP versus virtual-precision
  trend (`sigma_fp_vs_precision.png`). Interpret it in two short
  sentences: σ\_FP decreases monotonically as the virtual mantissa
  precision rises, which confirms that the MCA noise scale tracks
  precision as expected; the HLLC and Rusanov curves on the same axes
  show that the noise scale also depends on the numerical flux, linking
  this block back to the Chapter 5 §5.6 HLLC-vs-Rusanov method-variation
  evidence.
  Re-anchor the virtual-mantissa labels `p8 / p16 / p32 / p53` to the
  Chapter 2 §2.4 background in one short reminder sentence: they are
  virtual mantissa precisions for diagnostics, not IEEE binary
  formats, and `p32` in particular must not be read as IEEE fp32. The
  diagnostic vocabulary follows in three short connected definitions:
  - cite Chapter 4 §4.3 for σ\_FP as the per-component sample standard
    deviation over the MCA ensemble, naming it the local roundoff scale;
  - define **LoSoS** inline on first use per the
    **LoSoS / s\_req / σ\_FP terminology lock** above: "the
    loss-of-significance score LoSoS, the number of significant digits
    lost relative to the field magnitude under MCA resampling";
  - define **s\_req** inline on first use: "s\_req, the per-cell number
    of significant digits required so that the MCA-estimated rounding
    noise stays below the target ratio of the local field magnitude".
    The s\_req margin in this section is therefore "available digits in
    a virtual precision minus s\_req", with the LW3 region figure
    showing this margin at `p32`.
  Add one sentence stating the MCA sample size (typically 30 samples per
  field per virtual precision in the LW3 diagnostic grid); use this to
  qualify any quantile statement that follows.

- **Block 3 — LoSoS, s\_req, and the region-aware noise-to-error reading
  (about 170-200 counted words).** Block 3 carries three figures (the
  planning label for the set is "D2"; the label does not appear in
  prose). Introduce them descriptively in this order, with at least one
  interpretive sentence each:
  - **`losos_quantiles_rho.png` — quantile view of LoSoS for LW3
    density.** Define LoSoS inline on first use per the
    **LoSoS / s\_req / σ\_FP terminology lock** above. State the q05
    / q25 / median trends across virtual precisions and note that the
    quantile view avoids the worst-cell artifact that single-statistic
    summaries can carry. This is also the natural place to state the
    MCA sample size (typically 30 samples per field per virtual
    precision) once, because the quantile figure is what makes the
    small-sample caveat visible.
  - **`region_losos_margin_rho_p32.png` — region-aware LoSoS margin
    map at Verificarlo `p32` for LW3 density.** Define s\_req inline
    on first use per the same terminology lock and state that the
    plotted margin is "available digits at `p32` minus s\_req". Name
    the three regions explicitly — smooth interior, transition /
    contact band, and shock front — and report the *direction* of the
    margin (positive margin in smooth interior, near-zero or negative
    margin on the shock front), using verified values from
    `experiments/week7/report1_d2_replots/region_losos_quantiles_rho.csv`
    to one significant figure. Do not over-quantify because the MCA
    sample size is small.
  - **`noise_to_error_ratio_heatmap_grid_rho.png` — noise-to-error
    spatial map across virtual precisions `p8 / p16 / p32` for LW3
    density.** State that the plotted ratio is FP noise over
    physical / discretisation error, then describe the progression: at
    low virtual precision the noise dominates the front and contact
    regions; the ratio shrinks rapidly as the virtual precision rises;
    by `p32` the ratio is below the chosen reference scale across most
    of the domain except on the strongest waves. This reading does
    **not** imply IEEE fp32 adequacy because `p32` is virtual.

  Close Block 3 with the cross-link to §5.4: the regional structure
  here is consistent with the LW12 upper-right localisation in the
  direct fp32-fp64 heatmap, so the two views tell the same spatial
  story through different diagnostic chains. End §6.2 with one sentence
  bounding the precision claim to the tested precisions, the tested
  cases, and the LW3 MCA diagnostic grid.

Figures — Worker B includes the **four-figure required default set**
specified in the "Approved §6.2 figures" table above. One figure
anchors Block 2 (`sigma_fp_vs_precision.png`) and three figures anchor
Block 3 (`losos_quantiles_rho.png`, `region_losos_margin_rho_p32.png`,
`noise_to_error_ratio_heatmap_grid_rho.png`). Together they consume
five of the six region-aware P0 figures listed in the evidence map
(the sixth, `float_double_over_reference_bar.png`, is already in
Chapter 5 §5.4); the single P0 omission
(`region_noise_to_error_ratio_precision_grid_rho.png`) is the
documented redundancy case. Constraints:

- Do not silently drop any of the four required-default figures. If a
  file is missing or fails the readability check after LaTeX scaling,
  stop and report the gap, then follow the fallback rule in the
  Approved §6.2 figures section.
- Do not exceed four figures. A fifth figure is allowed only if §6.2
  still has counted-word room inside the 430-500 range, the fifth
  figure carries a claim not already covered by the four
  required-default figures, and Worker B records the rationale in the
  dispatch summary.
- Each included figure must carry at least one interpretive sentence;
  a figure without interpretation is removed before the verification
  block runs.

Constraints:

- Allowed citations (only if they support a specific sentence and are
  already present in the manuscript citation set): Higham, Goldberg,
  Denis et al. (Verificarlo), Parker (MCA), Brogi et al. only if a §6.2
  sentence specifically draws on the OpenFOAM precision-validation
  conclusion (this is usually unnecessary because §2.4 carries that
  citation). Do not add new keys.
- Do not redefine `R_ref` or `σ_FP`. Reference Equation~\ref{eq:ch4-rref}
  and Chapter 4 §4.3 textually.
- Do not introduce internal evidence-priority labels such as `P0`, `P1`,
  `P2`, or `P3`, and do not use `D1` or `D2` direction labels in prose,
  captions, or figure labels. Use descriptive phrases such as "the
  precision-adequacy diagnostic", "the region-aware Verificarlo
  diagnostic", or "the noise-to-error reading" instead. The
  evidence-map priorities and direction labels are writing-planning
  vocabulary only.
- Do not write "fp32 is adequate" without the tested-case boundary and a
  metric.
- Do not call pairwise fp32-fp64 differences "fp32 error" or "fp64 error".
- Do not turn this section into a literature review of Brogi et al. or
  Wang/Xia/Chen; their role belongs in §2.4.
- Treat the rising LW12 ratio as a boundary statement, not as evidence
  that fp32 will fail at higher resolutions.
- σ\_FP, LoSoS, and s\_req each appear with their defined names and
  interpretations at least once in §6.2, because §6.2 is the only
  manuscript home of these diagnostics. A draft that omits any of the
  three is not acceptable.

---

## Worker C: §6.3 Hardware and Implementation Sensitivity

Assigned region:

```latex
% <<SECTION_3_BEGIN>>
...
% <<SECTION_3_END>>
```

Goal:

- Synthesise CPU/GPU, compiler, branch-rule, solver, fp32 compiler-flag, and
  finite-time drift evidence axis by axis in 220-250 counted words. Do not
  repeat Chapter 5 case-by-case.
- Open with the matched strict-HLLC CPU/GPU reading: saved final-time
  outputs are bit-identical (zero L1/Linf/ULP) for Sod, Toro3, Toro5, LW3,
  and LW12 in both fp32 and fp64; saved-checkpoint comparisons on Sod, LW3,
  and LW12 add saved-output checkpoint identity, but they do not prove
  equality of all intermediate stage values inside a time step.
- State the toolchain split as a bounded comparability statement, not a
  weakness within a case: Toro3/Toro5 use Windows BuildTools, while
  Sod/LW3/LW12 use Linux/WSL; each within-case CPU/GPU comparison uses one
  matched binary/configuration, so bit-identity holds within a case
  independently of cross-case toolchain differences.
- Read the compiler/branch/solver and fp32 compiler-flag evidence as showing
  that implementation choices can produce drift comparable to or larger than
  hardware drift in some regimes: the largest non-stationary CPU-double
  variation is on O2 vs Ofast-fastmath for Toro3/Toro5; the fp32 compiler
  rows are a separately tagged fp32 sensitivity result, not hardware
  evidence. HLLC vs Rusanov is deliberate method variation, not
  reproducibility drift.
- Close with the finite-time drift reading: drift growth over saved
  checkpoints on the 1D Toro cases is finite-time and case-dependent; Toro2
  with the strict `<` HLLC branch is reported as non-completion / stability
  degradation rather than a zero-drift result, because the mechanism was
  not diagnosed in Report 1.

Constraints:

- Allowed citations: Goldberg, Higham (use sparingly, supporting a specific
  numerical-error claim). Demmel and Nguyen may be cited only if reductions
  / reproducibility are explicitly discussed; the current Chapter 4 frames
  CFL as min/max comparison rather than summation reduction, so a Demmel
  citation here is usually unjustified.
- Use `ENABLE_CUDA` if a build flag must be named; do not write `USE_GPU`.
- Do not say "fp32 compiler flags amplify hardware drift" without naming the
  evidence axis.
- Do not present the toolchain split as a weakness of within-case
  comparisons.
- Do not introduce new figures or refer to a `P1 probe`. C5 already names
  the artifact as "supplementary GPU flag probe"; §6.3 reuses that exact
  phrase if the probe is mentioned, and frames its role as a build-control
  boundary on the zero-drift CPU/GPU statement, not a hardware result.
- Saved-checkpoint coverage is asymmetric (Sod, LW3, LW12 in both fp32 and
  fp64; Toro3 and Toro5 have final-output evidence only). State this once
  as a boundary; do not present the asymmetry as an unresolved gap.

---

## Worker D: §6.4 Limitations and Report 2 Direction

Assigned region:

```latex
% <<SECTION_4_BEGIN>>
...
% <<SECTION_4_END>>
```

Goal:

- Group limitations by evidence type in 100-130 counted words, then close
  with the MHD Report 2 direction.
- The limitation groups, in this order:
  1. reference/discretisation limits (LW12 N=800 is a numerical reference,
     not an exact solution; LW3 self-convergence is the only LW3 reference);
  2. compiler/toolchain limits (single compiler family inside each case;
     Windows-BuildTools vs Linux/WSL split across cases);
  3. diagnostic-precision limits (Verificarlo `p32` is virtual precision;
     small MCA sample counts in the region-margin diagnostics);
  4. runtime / non-completion limits (Toro-123 / Toro2 strict `<` did not
     complete inside the 600 s limit, mechanism not diagnosed in Report 1;
     limiter selection is conceptual / future work, not a measured result);
  5. scope limits (Euler ideal-gas validation only; matched CPU/GPU
     evidence covers the five selected cases; no MHD validation is claimed).
- Then state the Report 2 direction as a concrete next step: extend the
  validated framework to ideal-MHD tests with divergence control
  (Dedner-type cleaning or constrained transport are named as future
  numerical choices only). Do not promise MHD validation.

Constraints:

- Allowed citations: Bard and Dorelli currently appears **once** in the
  active manuscript (Chapter 4 §4.2 around the $16\times16$ thread-tile
  sentence), so §6.4 may use it at most one more time, and only if the
  MHD-on-accelerator next step is the specific point being supported.
  Re-verify with the grep in the verification block before inserting.
  Dedner / Evans-Hawley citations are allowed only if Chapter 3 §3.6 does
  not already name them; check before adding.
- Avoid "more research is needed" or generic future-work language.
- Do not introduce new results.
- Do not duplicate the Conclusion evidence-lock claims verbatim; this is
  the limitation/scope synthesis, not the conclusion.

---

## Main-Agent Integration Tasks

After all workers finish:

1. Read the full Chapter 6 once for flow. Confirm the four sections read as
   a single synthesis chapter, not as four independent paragraphs.
2. **Duplication audit.** Confirm that:
   - §6.1 does not re-list the five cases or re-state Chapter 4's design
     matrix or Chapter 5's four result questions;
   - §6.2 does not redefine `R_ref` or `σ_FP`, and does not relitigate the
     `p32` / IEEE-fp32 distinction beyond a single reminder sentence;
   - the toolchain-split sentence appears once, in §6.3 only;
   - the LW12 upper-right localisation interpretation appears once,
     either in §6.2 Block 1 or in §6.3's saved-output sentence, but not
     both;
   - the limiter-variation limitation appears once, in §6.4 only (Chapter
     5 §5.6 already carries it; §6.4 may name it but does not duplicate
     the Chapter 5 phrasing);
   - Toro2 strict `<` non-completion appears once, in §6.4 only.
3. Remove duplicate prose where adjacent workers restated the same boundary
   from a different angle.
4. Confirm Chapter 6 does not contain a case-by-case repetition of Chapter 5
   results.
5. Confirm the Overleaf-counted word total for Chapter 6 is within
   850-1000 (working target 850-950; hard upper 1000). Confirm that
   Chapters 1-6 plus the legacy Chapter 7 stub together remain
   ≤ 7400 counted words against the drafting target and ≤ 7500 against
   the hard cap. If the total exceeds 7400, record the exact overshoot
   in the final response so the follow-up Chapter 7 round can absorb it.
6. Confirm no new citation key was added without verification against:

```text
report1/references/reference.md
report1/phd-thesis-template-2.4/References/references.bib
```

7. Confirm the Verificarlo / IEEE-fp32 distinction is stated explicitly in
   §6.2, and the toolchain-split disclosure is stated explicitly in §6.3.
8. Confirm LoSoS and s\_req are defined on first use in §6.2; confirm
   `R_ref` is referenced via `\eqref{eq:ch4-rref}` rather than restated;
   confirm `σ_FP` is referenced as "Chapter~4 §4.3" rather than redefined.
9. Confirm each included §6.2 region-aware diagnostic figure is
   interpreted in prose; remove any figure without an interpretive
   sentence and adjust §6.2 to fit the 430-500 counted-word range. The
   manuscript prose must not call them "D2 figures"; that label is
   planning vocabulary only.
10. Update the Chapter 1 roadmap only if the Chapter 6 section structure
    has diverged from what Chapter 1 currently describes. Do not change
    Chapter 1, Chapter 7, or any other chapter prose in this round.

---

## Verification Commands

Run from repository root unless otherwise stated.

### Forbidden / internal language

```powershell
rg -n "week[2-9]|\bP[0-3]\b|\bD[12]\b|HLLC-fill|config12|LW12/config12|P1 probe|USE_GPU|fp32 L1 error|fp64 L1 error|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: no manuscript-facing hits. The `\bP[0-3]\b` pattern catches
the writing-planning priority tags (`P0`, `P1`, `P2`, `P3`) and the
`\bD[12]\b` pattern catches the evidence-direction labels (`D1`, `D2`);
neither set belongs in the report prose.

### Verificarlo / fp32 distinction

```powershell
rg -n "p32|Verificarlo|fp32|MCA" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: at least one sentence in §6.2 explicitly distinguishing Verificarlo
`p32` virtual precision from IEEE binary32/fp32. The reminder sentence
should appear once; do not re-derive the §2.4 background.

### LoSoS / s_req / σ_FP definition check

```powershell
rg -n "LoSoS|losos|s_req|s\\\\_req|sigma_\{?FP|σ_FP|Loss of Significance" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected:

- `LoSoS` and `s_req` each appear with an inline definition on first use
  (the wording from the **LoSoS / s_req / σ_FP terminology lock** above
  is the reference).
- `σ_FP` is referenced as "Chapter~4 §4.3" rather than redefined.

### `R_ref` cross-reference

```powershell
rg -n "R_\{?ref\}?|R_\{\\\\mathrm\{ref\}\}|eq:ch4-rref" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: §6.2 references the C4 ratio via `\eqref{eq:ch4-rref}` or by
naming it textually as "the reference-scaled ratio of Chapter~4
Equation~\eqref{eq:ch4-rref}". The formula is not restated.

### Approved §6.2 figure existence and required-default coverage

For each `\includegraphics` line that Worker B inserts, verify the file
exists, and confirm that all four required-default figures appear:

```powershell
rg -n "\\\\includegraphics" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
Get-ChildItem report1/phd-thesis-template-2.4/Figs/report1/ -Filter *losos*
Get-ChildItem report1/phd-thesis-template-2.4/Figs/report1/ -Filter *noise_to_error*
Get-ChildItem report1/phd-thesis-template-2.4/Figs/report1/ -Filter *sigma_fp*
rg -n "sigma_fp_vs_precision|losos_quantiles_rho|region_losos_margin_rho_p32|noise_to_error_ratio_heatmap_grid_rho" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected:

- every `\includegraphics` referenced figure file is present under
  `report1/phd-thesis-template-2.4/Figs/report1/`;
- the last grep matches all four required-default file names exactly
  once each;
- the file `region_noise_to_error_ratio_precision_grid_rho.png` is
  present in `Figs/report1/` for fallback availability but is *not*
  referenced from `chapter6.tex` (unless the readability fallback was
  invoked, in which case the dispatch summary records the substitution).

If a required-default file is missing, copy it from the provenance under
`experiments/week7/report1_d2_replots/` (or its `report1_square_figures`
re-render) into `Figs/report1/`; do not regenerate raw data and do not
modify anything under `experiments/`.

### Generic "rows" usage

```powershell
rg -n "\brows\b" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: zero, or only where pointing to a specific table.

### Toolchain split

```powershell
rg -n "Windows BuildTools|Linux/WSL|toolchain" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Expected: at least one §6.3 sentence naming the within-case matched-binary
boundary.

### Citation check

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

For each cited key, confirm it exists in
`report1/phd-thesis-template-2.4/References/references.bib` and is already
used elsewhere in the manuscript, or is justified by
`report1/references/reference.md`.

The Bard and Dorelli cap is two appearances across the active manuscript
(`.snapshots/` files are excluded). The current active count is **one**
(Chapter 4 §4.2, around the $16\times16$ thread-tile sentence), so §6.4
may use the citation at most one more time. Verify before and after the
Chapter 6 edits:

```powershell
rg -n "bard_dorelli" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex --glob "!*.snapshots*"
```

Expected count after this round: ≤ 2.

Higham (2002) is preferred at ≤ 3 active citations; Goldberg (1991) and
IEEE 754-2019 at ≤ 2 each. Recount these if §6.2 or §6.3 adds new uses:

```powershell
rg -n "higham_2002|goldberg_1991|ieee754_2019" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex --glob "!*.snapshots*"
```

### Word count (informal)

```powershell
rg -nU "<<SECTION_[1-4]_BEGIN>>([\s\S]*?)<<SECTION_[1-4]_END>>" report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Inspect the four marker regions and estimate counted words per section.
The Overleaf counted-text value remains the controlling number; this is
only a local sanity check.

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

Fix only Chapter 6 problems unless the failure is clearly a pre-existing
unrelated issue.

---

## Final Response Format

Respond in Chinese with:

- which Chapter 6 sections were drafted and at what counted-word size;
- which supervisor-feedback items were addressed (especially the §6.2
  Verificarlo / IEEE-fp32 distinction and the §6.3 toolchain-split
  disclosure);
- which of the approved §6.2 region-aware figures were actually
  included; confirm by file name that all **four** figures in the
  required-default set (`sigma_fp_vs_precision.png`,
  `losos_quantiles_rho.png`, `region_losos_margin_rho_p32.png`,
  `noise_to_error_ratio_heatmap_grid_rho.png`) are present, and quote
  the one-sentence interpretation that anchors each. Confirm that the
  single deliberately omitted P0 figure
  (`region_noise_to_error_ratio_precision_grid_rho.png`) was *not*
  included, or, if it was substituted in via the readability fallback,
  record which required-default figure it replaced and why;
- the exact first-use inline definitions used for LoSoS and s\_req, and
  the textual references used for `R_ref` and `σ_FP`;
- the P0 evidence audit result: confirm 29 of the 30 evidence-map P0
  artifacts now have a manuscript home (the single permitted exception
  is `region_noise_to_error_ratio_precision_grid_rho.png`, documented
  above as the region-aggregated companion to the spatial heatmap). If
  any other P0 row is unsatisfied, list it as a gap rather than as a
  silent drop;
- duplication audit result (Item 2 of Main-Agent Integration Tasks);
- citation-cap status for Bard and Dorelli (active count must be ≤ 2
  after this round) and for Higham/Goldberg/IEEE 754;
- any remaining dependency on Chapter 5 wording, the Chapter 7 merge
  decision, or future figure regeneration;
- verification and compile results.

Do not claim the full report is finished. Chapter 7 is handled in a
separate pass once the supervisor's remove-vs-compress decision is made.
