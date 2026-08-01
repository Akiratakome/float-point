# Report 2 Manuscript Outline and Writing Plan

This is the canonical section-by-section plan for Report 2. The manuscript
files remain structure-only until the relevant evidence gate is satisfied.

## Drafting order and final order

Evidence-driven drafting order:

1. Chapter 4: MHD validation results skeleton
2. Chapter 5: systematic results skeleton
3. Chapter 3: experimental design and measurement protocol
4. Chapter 2: project development
5. Chapter 6: discussion
6. Chapter 1: introduction and Report 1 transition
7. Chapter 7: conclusion and future work
8. Abstract, references, appendix, and final editing

Final report order is Chapters 1--7 as listed above.

## Global writing and evidence rules

- Follow the chapter responsibility lock in `planning/reportagents.md`.
- Use `docs/experiment_logs/report2_evidence_map.md` as the status authority.
- Use `experiments/week18/report2_publication_figures/figure_manifest.json` as
  the figure-source, importance, hash, and claim-boundary authority.
- Do not repeat Report 1 theory, background, Euler validation, or discussion.
- Every numerical sentence names a metric, comparison baseline, and tested scope.
- Every result paragraph follows: question -> figure/table -> observation ->
  interpretation boundary. This is the results application of
  `scientific-writing-duke`.
- Internal week numbers and gate nicknames stay in this plan only.
- Negative results remain visible; do not change an analysis window after seeing
  the outcome unless the change is declared as a separate sensitivity study.
- AI-assisted prose is rewritten by the student and checked with
  `avoiding-ai-flavor` before it enters a review draft.

## Skill usage rule

| Drafting task | Primary skill | Optional companion | Structural effect |
|---|---|---|---|
| Introduction | `writing-introduction` | `academic-english-style` | Narrowing funnel: context -> gap -> aim -> scope. |
| Report 1 transition/literature | `writing-literature-review` | `academic-english-style` | Select only sources/old results that justify a decision. |
| Development/methodology | `scientific-writing-duke` | `academic-english-style` | Concrete actor, action verb, known-to-new sequence. |
| Validation/results | `scientific-writing-duke` | `academic-english-style` | Figure/table named, interpreted, and bounded. |
| Discussion | `scientific-writing-duke` | `academic-english-style` | Synthesis by question, not case-by-case repetition. |
| Conclusion | `writing-conclusion` | `academic-english-style` | Aim -> findings -> implication -> limits -> next step. |
| Final edit | `editing-academic-prose` | then `avoiding-ai-flavor` | Remove wordiness, generic filler, and unsupported confidence. |

Use one primary and at most one companion skill in a single pass.

## Word-budget lock

The controlling cap is 7,500 Report 2 words using the independent Overleaf
project count. Tables, figure legends/captions, and appendices count;
bibliography does not. The 5% no-deduction tolerance is not a writing target.
The allocation below retains integration margin below the formal maximum.

| Part | Working range | Hard upper |
|---|---:|---:|
| Abstract | 170--190 | 200 |
| Chapter 1 | 430--480 | 500 |
| Chapter 2 | 850--920 | 950 |
| Chapter 3 | 820--880 | 900 |
| Chapter 4 | 1,150--1,220 | 1,250 |
| Chapter 5 | 1,850--1,950 | 2,000 |
| Chapter 6 | 680--730 | 750 |
| Chapter 7 | 340--380 | 400 |
| Appendix | 180--230 | 250 |
| **Hard-upper sum** | | **7,200** |

Tables and captions follow the current course counting clarification but remain
concise. If the report exceeds budget, remove duplicated Report 1 material and
repeated result narration before cutting evidence-bearing interpretation.

## Standalone and combined deliverables

- `report2/phd-thesis-template-2.4/thesis.tex` remains the standalone Report 2
  Overleaf main file and the only document used for the Report 2 word count.
- The final submission PDF contains the Report 1 PDF, an explicit Part II
  divider, and the standalone Report 2 PDF, assembled through
  `report2/submission/combined_submission.tex`.
- PDF-level assembly keeps the two source trees, bibliographies, labels, and
  page numbering isolated. It does not authorise duplication of Report 1 prose
  in Report 2.
- The official signed Report 2 declaration/cover sheet must be supplied by the
  student and submitted separately or embedded. The repository contains only
  the required originality wording, not a signature.

## Requirement-to-chapter coverage

| Brief/marking requirement | Primary owner | Required visible evidence |
|---|---|---|
| Project development [20%] | Chapter 2 | Report 1 decision mapping; MHD/GLM, HLL/HLLD, CPU/OpenMP/CUDA development and gates. |
| Computational results [40%] | Chapters 4--5 | CPU/GPU MHD validation; 1D and 2D MHD cases; compact Euler--MHD range; precision, compiler, implementation, hardware, temporal and resolution effects. |
| Conclusions and future work [20%] | Chapters 6--7 | Matched-axis synthesis, reproducibility implications, explicit limitations and prioritised experiments. |
| Quality of write-up [20%] | All chapters | Single ownership of methods/results, claim-bounded figures, traceable references, appendix provenance and word-budget compliance. |

## Core evidence routing

These paths are planning locators only; manuscript prose uses scientific names.

| Evidence role | Authority | Planned owner |
|---|---|---|
| Report 1 transition | Report 1 conclusion and `report1_evidence_map.md` | C1/C2 |
| 1D MHD validation | `experiments/week12/brio_wu_1d/summary.md` | C4 |
| 2D invariance/GLM | `experiments/week12/mhd_2d/.../summary.md` | C4 |
| HLLD divB follow-up | `experiments/week13/hlld_divb_followup/summary.md` | C2/C4 |
| Brio--Wu deterministic/MCA | Week-15 HLL/HLLD P1 summaries + `experiments/week18/precision_mca_gate/summary.json` | C5; report-grade bounded scope |
| Orszag--Tang deterministic/MCA | Week-15 HLL/HLLD headline/MCA summaries + unified scope audit | C5; provisional reduced-scope boundary |
| Temporal discrepancy | `experiments/week15/mhd_temporal_divergence/summary.md` | C5; negative result |
| Matched CPU/GPU | `experiments/week16/cpu_gpu_hardware_axis/summary.md` | C5 |
| Repeated timing/thread/CFL | `experiments/week18/supplemental/` | C5 |
| Euler--MHD cross-system matrix | `experiments/week18/euler_mhd_cross_system/summary.md` | C3/C5; report-grade bounded sensitivity |
| Brio--Wu direct build semantics | `experiments/week20/brio_wu_build_semantics/summary.md` | C3/C5; report-grade one-axis-at-a-time density response |
| MHD three-resolution ladder | `experiments/week18/resolution_ladder/summary.md` | C4/C5; 24/24 runs and eight complete groups |
| Kelvin--Helmholtz validation/precision | `experiments/week16/kelvin_helmholtz_precision/` | C4/C5 |
| 2D 512 consolidation | `experiments/week16/ot_kh_512_consolidation/summary.md` | C4 |
| Report-facing synthesis | `experiments/week17/report2_synthesis/summary.md` | C6; no new evidence |
| CSC reduced MCA findings | `experiments/week18/csc_findings_synthesis/summary.md` | C5; validation scope |

## Candidate figure and table plan

The candidate pool is not a commitment. Main text keeps only distinct claims.

| Candidate | Type | Claim role | Chapter |
|---|---|---|---|
| Report 1 -> Report 2 decision map | Compact table | Shows why MHD/temporal/hardware axes were selected | 1/2 |
| MHD implementation delta | Diagram/table | Shows only components added after Report 1 | 2 |
| Experiment matrix | Table | Single owner of cases and variation axes | 3 |
| Euler--MHD cross-system sensitivity | Compact table/plot | Demonstrates the required range without repeating Report 1 validation | 5 |
| Reference/evidence hierarchy | Table | Exact vs numerical vs morphology-only evidence | 3 |
| Brio--Wu refinement | Plot/table | 1D MHD validation | 4 |
| GLM/invariance diagnostics | Plot/table | 2D method validation | 4 |
| OT/KH morphology pair | Figure | Qualitative structure, explicitly not accuracy | 4 |
| OT/KH 256--512 gate | Table | Two-resolution sensitivity | 4 |
| OT/KH three-resolution ladder | Plot/table | Resolution dependence across eight complete groups | 4/5 |
| Deterministic precision effects | Cross-case table/plot | fp32/fp64 baseline discrepancy | 5 |
| Compiler/branch matched comparisons | Table | Bounded secondary-axis differences | 5 |
| CPU/GPU correctness and timing | Table/plot | Correctness separate from performance | 5 |
| Temporal discrepancy curves | Figure | Time evolution and negative contrast | 5 |
| MCA spread comparison | Figure/table | Full vs reduced evidence clearly separated | 5 |
| Thread/CFL robustness | Compact table/plot | Covered reproducibility and sensitivity | 5 |
| Matched-axis synthesis | Table | Compare only commensurate metrics; no arbitrary cross-metric ordinal ranking | 6 |

## Chapter 1: Introduction and Project Transition

Working target: 430--480 words. Draft after Chapters 4--6.

### 1.1 Reproducibility question

- **Write:** Narrow from reproducibility of published HRSC algorithms to the
  ideal-MHD precision/hardware question.
- **Do not write:** Generic Euler/HRSC tutorial or result values.
- **Sources:** Project brief plus only literature needed to locate the question.
- **Skill:** `writing-introduction` + `academic-english-style`.
- **Prompt:** Build a narrowing funnel: computational reproducibility context,
  unresolved implementation sensitivity, and the exact Report 2 question.

### 1.2 How Report 1 informed Report 2

- **Write:** One short signpost stating that Report 1 findings determined the
  Report 2 design; point to Section 2.1 for the full decision map.
- **Do not write:** Report 1 results chapter summary.
- **Evidence:** Report 1 conclusion and evidence map.
- **Skill:** `writing-literature-review` + `academic-english-style`.
- **Gate:** Every Report 1 statement must explain a Report 2 decision.

### 1.3 Research questions and scope

- **Write:** Questions covering MHD validation, systematic variation, time
  evolution, and implementation reproducibility. Name exclusions.
- **Do not write:** Answers or promised universal conclusions.
- **Skill:** `writing-introduction`.

### 1.4 Contributions and report structure

- **Write:** Contributions only after result/discussion chapters stabilize;
  roadmap Chapters 2--7.
- **Do not write:** Novelty claims without a literature check.
- **Skill:** `writing-introduction` + `academic-english-style`.

## Chapter 2: Project Development: Ideal-MHD Solver

Working target: 850--920 words. Owns the brief's Project Development [20%].

### 2.1 Development priorities after Report 1

- **Write:** Own the full compact mapping from each selected Report 1 finding or
  limitation to a Report 2 implementation/experiment decision, followed by the
  selection criteria: representative physics, numerical risk, hardware
  comparability, runtime, and evidence value. Explain omitted axes here once.
- **Evidence:** Project schedule, Report 1 conclusions, current architecture.
- **Do not write:** Full experiment results or chronological week diary.
- **Skill:** `scientific-writing-duke`.

### 2.2 Ideal-MHD and GLM additions

- **Write:** Only new state variables, flux/source additions, divergence
  constraint, GLM split, and checks relative to the Report 1 Euler code.
- **Sources:** Verified MHD/GLM references and relevant source paths.
- **Do not write:** Repeat finite-volume/MUSCL--Hancock derivation.
- **Planned visual:** Implementation-delta diagram.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 2.3 HLL and HLLD solver paths

- **Write:** Why both solvers exist, what wave information differs, how each is
  used in the study, and why HLLD is not silently the production default.
- **Evidence:** Source/tests and HLLD follow-up validation.
- **Do not write:** Comparative result ranking; Chapter 5 owns it.
- **Skill:** `scientific-writing-duke`.

### 2.4 CPU, OpenMP, and CUDA implementation

- **Write:** MHD CPU path, bounded HLL GPU path, mirrored semantics, device
  dispatch, and deterministic choices relevant to comparison.
- **Boundary:** No HLLD/KH/GPU-MCA claim without matching evidence.
- **Skill:** `scientific-writing-duke`.

### 2.5 Testing and development gates

- **Write:** Unit tests, physical-state checks, invariance, divergence-control,
  completion attestation, and regression strategy.
- **Do not write:** Result tables that belong to Chapter 4.
- **Skill:** `scientific-writing-duke`.

## Chapter 3: Experimental Design and Reproducibility Methodology

Working target: 820--880 words. Single owner of the design matrix.

### 3.1 Research questions and controlled axes

- **Write:** Map each research question to precision, solver, compiler/math mode,
  branch rule, hardware, thread count, CFL, resolution, and time.
- **Boundary:** Distinguish primary axes, supplemental robustness axes, and
  deferred axes.
- **Planned visual:** Master experiment matrix.
- **Skill:** `scientific-writing-duke`.

### 3.2 Test-case matrix

- **Write:** Sod and Liska--Wendroff Config. 3 as compact Euler continuity cases,
  plus Brio--Wu, Orszag--Tang, and Kelvin--Helmholtz for ideal MHD; list
  dimension, purpose, solver/device coverage, grid, end time, and boundaries.
- **Euler continuity:** Describe only the new matched cross-system matrix. Do
  not repeat Report 1 Euler theory, validation narrative, or figures.
- **Sources:** Exact benchmark/setup references used by the code.
- **Skill:** `scientific-writing-duke`.

### 3.3 Build and run matrix

- **Write:** What changes and what remains fixed; actual build semantics rather
  than directory labels; baseline definition per solver.
- **Boundary:** “Ofast-ieee” style names are labels, not semantic proof.
- **Skill:** `scientific-writing-duke`.

### 3.4 Reference hierarchy and validation gates

- **Write:** Exact/aligned high-resolution references, self-reference gates,
  morphology-only checks, invariance gates, and completion gates.
- **Boundary:** Two resolutions do not establish asymptotic convergence.
- **Planned visual:** Evidence hierarchy table.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 3.5 Metrics and statistical treatment

- **Write:** Norm definitions, conserved quantities, ULP distance, div(B), wall
  time summaries, MCA spread, sample counts, temporal fitting protocol.
- **Boundary:** Separate error from discrepancy; state fit-quality limitations.
- **Norm-definition lock:** For a same-grid field difference
  $d_{ij}=q_{ij}-q^{ref}_{ij}$, an explicitly named mean norm is
  $L_{1,\mathrm{mean}}=N^{-1}\sum|d_{ij}|$ and
  $L_{2,\mathrm{mean}}=(N^{-1}\sum d_{ij}^{2})^{1/2}$, where
  $N=N_xN_y$. A physical-domain norm is
  $L_{1,\Omega}=\sum|d_{ij}|\,\Delta x\Delta y$ and
  $L_{2,\Omega}=(\sum d_{ij}^{2}\,\Delta x\Delta y)^{1/2}$;
  $L_{\infty}=\max|d_{ij}|$ is
  unchanged by cell measure. Do not use an unqualified “L1” or “L2” when the
  distinction matters.
- **Figure 4.2 metric lock:** the three-grid packet block-averages the finer
  density to the coarser grid and uses the **mean absolute density difference**
  $L_{1,\mathrm{mean}}$. Its displayed diagnostic is
  $p_{\mathrm{obs}}=\log_2(E_{128,256}/E_{256,512})$. This is neither a relative norm nor a
  physical-domain integral and is not an asserted asymptotic order.
- **Metric audit:** Two-dimensional physical-domain L1/L2 must use cell area
  `dx*dy` (or an explicitly declared mean norm). Historical Week-15/16 2D
  L1/L2 values produced before the area fix are excluded from new comparisons;
  their Linf values remain dimensionally unaffected. Use the new Week-18
  summaries: cross-system uses its declared mean-relative density metrics,
  whereas the three-resolution ladder uses mean absolute density differences.
- **Skill:** `scientific-writing-duke`.

### 3.6 Harness, metadata, and retention

- **Write:** `config -> build -> run -> measure -> aggregate -> plot`, run
  records, manifests, gates, binary hashes, and transient-grid retention.
- **Do not write:** Operational command catalogue; appendix owns reproduction.
- **Skill:** `scientific-writing-duke`.

### 3.7 Deliberate exclusions

- **Write:** Why MPI, broad GPU matrix, HLLD-on-GPU, cross-architecture testing,
  and formal Lyapunov analysis are outside the completed design.
- **Boundary:** Isolation is not evidence that omitted axes have no effect.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 4: MHD Validation Results

Working target: 1,150--1,220 words. Draft first.

Every section follows: purpose -> figure/table -> quantitative observation ->
validation implication -> boundary.

### 4.1 Validation hierarchy overview

- **Write:** One paragraph pointing back to Chapter 3 and ordering evidence from
  local property checks to benchmark/reference comparisons.
- **Do not write:** Repeat matrix rationale.
- **Skill:** `scientific-writing-duke`.

### 4.2 One-dimensional Brio--Wu validation

- **Write:** Refinement/aligned-reference evidence, fields shown, error trend,
  and what it validates.
- **Evidence:** `experiments/week12/brio_wu_1d/summary.md`.
- **Boundary:** Numerical reference, not an exact MHD solution or precision
  headline.
- **Planned item:** Refinement table plus one profile figure if distinct.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 4.3 Two-dimensional invariance and divergence control

- **Write:** Transverse-invariance and GLM decay gates before turbulent tests.
- **Evidence:** Week-12 2D summaries.
- **Boundary:** Does not establish OT/KH precision adequacy.
- **Skill:** `scientific-writing-duke`.

### 4.4 Matched CPU/GPU implementation validation

- **Write:** Validate the bounded HLL GPU implementation against the matched CPU
  path in fp32 and fp64 before using hardware timing results in Chapter 5.
- **Evidence:** Week-16 hardware-axis correctness gate and Week-18 repeated
  hardware packet.
- **Boundary:** Brio--Wu and Orszag--Tang HLL only; no HLLD/KH GPU claim.
- **Skill:** `scientific-writing-duke`.

### 4.5 Orszag--Tang validation

- **Write:** Morphology, completion, conservation/divergence diagnostics, and
  256/512 sensitivity.
- **Evidence:** OT morphology, HLLD follow-up, consolidation summaries, and the
  completed three-resolution ladder, including the repaired HLLD/fp64/512 run.
- **Boundary:** Separate morphology-only from quantitative gate; no asymptotic
  convergence claim.
- **Skill:** `scientific-writing-duke`.

### 4.6 Kelvin--Helmholtz validation

- **Write:** Positivity/completion, mean and maximum divergence diagnostics,
  adjacent-grid density differences, and solver scope for the completed
  project-defined MHD double-shear matrix.
- **Evidence:** KH validation, consolidation, and the complete three-resolution
  ladder.
- **Boundary:** The project MHD double-shear case remains an adaptation.
  Independent literature-growth checks enter the manuscript only after a
  predeclared quantitative agreement gate passes. Validation does not promote
  full-scale MCA or GPU coverage.
- **Skill:** `scientific-writing-duke`.

### 4.7 Validation limits

- **Write:** Reference uncertainty, two-resolution limitation, morphology role,
  div(B) interpretation, and unvalidated combinations.
- **Do not write:** Future-work shopping list; Chapter 7 owns priorities.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 5: Precision, Hardware, and Implementation Results

Working target: 1,850--1,950 words. Draft second.

### 5.1 Result matrix overview

- **Write:** Questions and order; point to Chapter 3 matrix.
- **Do not write:** Findings before their evidence sections.
- **Skill:** `scientific-writing-duke`.

### 5.2 Euler--MHD cross-system sensitivity

- **Write:** Compare matched density discrepancies for Sod, Liska--Wendroff,
  Brio--Wu, and Orszag--Tang across fp32/fp64 and O2-default/Ofast-fast builds.
  Use this compact range to satisfy the brief without re-running Report 1's
  validation narrative.
- **Evidence:** `experiments/week18/euler_mhd_cross_system/summary.md` (16/16
  completion-attested runs).
- **Boundary:** The Euler cases use HLLC and the MHD cases use HLL, so the table
  supports bounded cross-system sensitivity, not accuracy or a universal
  system/solver ranking.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.3 Deterministic fp32--fp64 sensitivity

- **Write:** Same-solver, same-case baseline comparisons for Brio--Wu, OT, and
  KH; matched norms and fields; relation to validation scale where permitted.
- **Evidence:** Week-15/16 precision packets and the Week-18 precision/MCA scope gate.
- **Boundary:** The unified audit promotes the two same-scope Brio--Wu rows;
  both OT rows remain provisional because deterministic 256^2/t=0.5 and MCA
  64^2/t=0.05 scopes differ. Do not use historical 2D L1/L2 values affected by
  the pre-audit cell-measure error; use Linf or a corrected new summary.
- **Planned item:** Non-ranking result-scope matrix; keep unmatched and
  provisional rows visibly separate.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.4 Compiler and branch-rule sensitivity

- **Write:** First identify the O2-default/Ofast-fast pair as a composite
  comparison, then report the direct `/O2`--`/Ox`, compiler-default--`/fp:fast`,
  and `<`--`<=` Brio--Wu pairs that hold the other recorded axes fixed.
- **Evidence:** `experiments/week20/brio_wu_build_semantics/summary.md`; eight
  clean MSVC builds and 16/16 completion-attested HLL/HLLD, fp64/fp32 runs.
- **Boundary:** Zero and non-zero density responses are valid; they are not
  compiler-wide, performance, accuracy, or portability conclusions.
- **Skill:** `scientific-writing-duke`.

### 5.5 HLL and HLLD comparison

- **Write:** Solver-dependent differences under matched configurations.
- **Boundary:** A solver change is method variation, not reproducibility drift;
  do not infer a general ranking from unmatched cases.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.6 Matched CPU/GPU correctness and performance

- **Write:** Same-precision ULP/norm comparison, then repeated timing; state
  workload size and timing protocol.
- **Evidence:** CPU/GPU axis and repeated timing summaries.
- **Boundary:** HLL Brio--Wu/OT only unless evidence map changes; correctness
  equality is not universal hardware independence.
- **Planned items:** Correctness table and repeated timing plot/table.
- **Skill:** `scientific-writing-duke`.

### 5.7 Resolution dependence of discrepancies

- **Write:** Present fp32/fp64 density separation across 128, 256, and 512 for
  matched OT/KH and HLL/HLLD paths, then distinguish observed refinement trends
  from convergence order.
- **Evidence:** `experiments/week18/resolution_ladder/summary.md`; all eight
  planned three-grid groups and all 12 same-grid fp32/fp64 density-pair cells
  complete.
- **Boundary:** Treat each observed order as a bounded self-refinement
  diagnostic, not an asymptotic convergence proof, and do not call
  cross-precision separation discretisation error.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.8 Growth of discrepancies with time

- **Write:** Hypothesis, fixed sampling/windows, aligned curves, fitted rates,
  negative cross-case contrast, and fit-quality limitations.
- **Evidence:** Temporal divergence summary.
- **Boundary:** Engineering rate, not formal maximal Lyapunov exponent.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.9 Monte Carlo arithmetic

- **Write:** p53 noise floor, p24 virtual precision, sample count, fieldwise
  spread, and relationship to deterministic fp32/fp64 differences.
- **Boundary:** Clearly separate full packets, reduced validation, invalid old
  runs, and blocked full-scale KH work.
- **Planned item:** Evidence-status-aware MCA table.
- **Skill:** `scientific-writing-duke`.

### 5.10 Thread-count and CFL sensitivity

- **Write:** OpenMP reproducibility separately from performance scaling; CFL
  sensitivity separately from formal time convergence.
- **Evidence:** Supplemental summaries.
- **Boundary:** No MPI conclusion; non-monotonic results remain non-monotonic.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 5.11 Cross-axis summary

- **Write:** Use `chapter5_result_scope_matrix.md` as a non-ranking coverage aid;
  retain it in the main text only if the MCA status table moves to the Appendix.
- **Do not write:** Rank axes by incomparable metrics or provisional packets.
- **Skill:** `scientific-writing-duke`.

## Chapter 6: Discussion: Reproducibility Across Implementations

Working target: 680--730 words. Introduces no new results.

### 6.1 Meaning of the validation evidence

- **Write:** How Chapter 4 limits and enables Chapter 5 interpretation.
- **Skill:** `scientific-writing-duke`.

### 6.2 Relative importance of the tested axes

- **Write:** Synthesis across matched evidence, including null and negative
  results; explain why the available metrics do not support a unified ranking.
- **Do not write:** Case-by-case replay.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 6.3 Accuracy, discrepancy, and performance trade-offs

- **Write:** What can and cannot be traded, distinguishing numerical-reference
  error, cross-variant drift, and runtime.
- **Boundary:** Do not equate faster with scientifically adequate.
- **Skill:** `scientific-writing-duke`.

### 6.4 Reproducibility of a published algorithm

- **Write:** Why algorithm name alone is insufficient; specify precision,
  effective compiler semantics, branch rule, solver, hardware path, scheduling,
  configs, reference, and metadata needed for reproduction.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

### 6.5 Limitations

- **Write:** Bound claims by solver, case, grid, time, hardware, sample count,
  fit quality, and unavailable axes. Link each limitation to a conclusion.
- **Do not write:** Apologetic chronology.
- **Skill:** `scientific-writing-duke` + `academic-english-style`.

## Chapter 7: Conclusions and Future Work

Working target: 340--380 words. Use `writing-conclusion` inverted funnel.

### 7.1 Aim and evidence base

- **Write:** One compact restatement matching Chapter 1 language.
- **Do not write:** New background, literature, or method summary.
- **Skill:** `writing-conclusion`.

### 7.2 Answers to the research questions

- **Write:** Two or three load-bearing findings admitted by the conclusion lock;
  report findings directly and hedge broader implications.
- **Skill:** `writing-conclusion` + `academic-english-style`.

### 7.3 Contribution and claim boundaries

- **Write:** What the controlled harness/evidence now makes knowable, then the
  narrowest boundaries that materially constrain it.
- **Skill:** `writing-conclusion`.

### 7.4 Prioritised future work

- **Write:** Specific next experiment for each principal limitation, ordered by
  impact on the report's conclusions.
- **Do not write:** Generic “more work is needed”.
- **Skill:** `writing-conclusion` + `academic-english-style`.

## Conclusion evidence lock

Before Chapter 7 or the abstract is drafted, create a table with:

| Allowed claim | Exact summary/figure | Required metric | Scope sentence | Excluded generalisation |
|---|---|---|---|---|

Populate it only from the current evidence map. Provisional observations may be
mentioned as provisional in Chapters 5--6 but do not become headline conclusion
claims without promotion.

## Abstract

Working target: 170--190 words. Write last.

Required moves: question, new ideal-MHD development, validation/result scope,
two or three quantitative headline findings, principal boundary, contribution.
No citations and no Report 1 background recap. Use `academic-english-style`,
then `avoiding-ai-flavor` after the student rewrite.

## References plan

Use `report2/references/reference.md`. Citation functions by chapter:

| Chapter | Citation role |
|---|---|
| 1 | Locate reproducibility question and Report 1 transition. |
| 2 | Support MHD/GLM/HLL/HLLD technical choices. |
| 3 | Support benchmark definitions, metrics, MCA, and reproducibility methods. |
| 4 | Cite benchmark sources where interpreting validation structure. |
| 5 | Cite numerical-analysis tools only where needed; results cite project artefacts through prose provenance, not bibliography. |
| 6 | Support broader reproducibility interpretation sparingly. |
| 7 | Normally no new citations. |

## Appendix and code-submission plan

Working target: 180--230 counted words, hard maximum 250.

- Map every final figure/table to its config or matrix, analysis script,
  machine-readable summary, run metadata, and one reproduction command.
- State retained and removed artefacts; do not include build directories,
  executables, large grids, or an operational command catalogue.
- Prepare a separate code-submission manifest containing source, configs,
  canonical scripts, environment/build instructions, and summary checksums.
- Keep the appendix structure-only until the final figure/table set is locked.

## Drafting milestones

1. **2026-07-27 -- supervisor draft (past due):** the requested review copy was
   due to Philip. Send the current reviewable draft immediately and identify
   incomplete sections or provisional evidence in the covering message.
2. **2026-07-28 -- evidence/word/design lock:** freeze the selected figures,
   Chapter 3 matrix, metric definitions, exclusions, and current Overleaf
   count. Preserve negative results and provisional evidence labels.
3. **2026-07-29 to 2026-07-30 -- results and development revision:** complete
   Chapters 4--5 from locked summaries, then Chapter 2. Do not add optional
   experiments that cannot change or validate a load-bearing conclusion.
4. **By 2026-07-31 -- supervisor feedback:** receive and triage feedback into
   required scientific corrections, clarity changes, and optional polish.
5. **2026-08-01 to 2026-08-02 -- synthesis:** revise Chapter 6, write the
   Chapter 1 transition/refined-methodology introduction where needed, lock
   Chapter 7 claims, then write the abstract.
6. **2026-08-03 -- figure/reference pass:** captions, references, provenance,
   cross-references, and appendix map.
7. **2026-08-04 -- code-submission bundle:** freeze manifest, configs, scripts,
   checksums, environment/build instructions, and reproduction checks.
8. **2026-08-05 -- student author rewrite:** connected prose, integrity and
   AI-flavour checks; confirm every supervisor comment is resolved or logged.
9. **2026-08-06 -- release candidate:** clean compile, word count, format,
   link, figure/table, declaration, combined-PDF, and archive verification.
10. **2026-08-07 -- final submission:** submit the combined Part I + Part II
    report and required supporting bundle. Retain the standalone Part II PDF
    and its Overleaf word-count record.
11. **2026-08-08 to 2026-08-11 -- poster review:** derive the poster only from
    final evidence and obtain supervisor comments without changing archived
    report claims silently.
12. **2026-08-12 -- poster submission.**

## Final self-review checklist

- [ ] Report 2 marking categories are visible in the chapter structure.
- [ ] Report 1 material appears only where it motivates a Report 2 decision.
- [ ] Project development explains selection under the available time.
- [ ] MHD CPU/GPU validation scope is explicit.
- [ ] The computational-results range includes compact Euler continuity plus
      both 1D and 2D MHD cases without repeating Report 1.
- [ ] Precision, compiler, hardware, solver/branch, time, and supplemental axes
      are distinguished rather than collapsed.
- [ ] Every use of “accuracy” names an exact or numerical reference.
- [ ] Virtual p24/p53 is not presented as IEEE fp32/fp64.
- [ ] Two-resolution evidence is not called asymptotic convergence.
- [ ] No historical 2D L1/L2 affected by the old `dx`-only weighting is used;
      corrected mean/area norms or Linf are identified explicitly.
- [ ] Temporal fits are not called formal Lyapunov exponents.
- [ ] Provisional, validation, negative, invalid, and deferred evidence retains
      its status in prose and conclusions.
- [ ] Every figure/table is interpreted and linked to one claim.
- [ ] No internal week/task/gate labels appear in manuscript prose.
- [ ] Chapter 6 adds no result and Chapter 7 adds no analysis.
- [ ] References support exact sentences and match implemented setups.
- [ ] Word count and format satisfy current official guidance.
- [ ] Standalone Report 2 Overleaf count is at most 7,500 words and records the
      count/date; tables, captions, and appendices are included.
- [ ] Combined PDF contains Report 1, an unmistakable Part II divider, and the
      final standalone Report 2 PDF in that order.
- [ ] Supervisor draft was sent; feedback is tracked and every required change
      is resolved or explicitly documented before the release candidate.
- [ ] The signed official Report 2 declaration/cover sheet and word-count
      declaration are present as required; no placeholder signature remains.
- [ ] Appendix provenance and the separate code-submission manifest reproduce
      every retained result from config to summary/plot.
- [ ] Final prose is the student's own verified writing.
