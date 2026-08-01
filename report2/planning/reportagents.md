# Report 2 Working Requirements

This file is the compact requirements synthesis for collaborators working on
Report 2 of *Effect of Floating-Point Precision and Hardware on HRSC Schemes*.
It does not replace the official project brief or course handbook.

## 1. Binding sources

1. `docs/requirement/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf`
2. Current course handbook/administrative clarification available to the student
3. `docs/requirement/Coding_and_submission_guidelines.pdf`
4. `docs/experiment_logs/report2_evidence_map.md` for evidential status
5. `docs/HARNESS.md` for experiment and metadata contracts

If derived planning disagrees with an official source, the official source wins.
The current administrative clarification and Course Handbook pp. 11--12 are
synthesised in `report2/requirements/submission_format_2026-07-28.md`.

## 2. Report 2 marking allocation

The supervisor brief assigns:

- **Project development [20%]**: explain how representative changes were
  selected within the available time and how Report 1 informed the direction.
- **Computational results [40%]**: validate CPU/GPU MHD implementations and
  explore accuracy or discrepancy across hardware, compiler settings, precision,
  and implementation changes; cover a compact range of Euler and ideal-MHD
  cases, include 1D and 2D MHD cases, and quantify time growth where present.
- **Conclusions and future work [20%]**: compare the influence of tested axes and
  discuss reproducibility across nominally equivalent implementations.
- **Quality of write-up [20%]**: structure, completeness, language, figures,
  tables, and references.

The chapter structure must make these four categories visible. Chapters 4 and 5
therefore remain separate results chapters.

## 3. Format and integrity constraints

- Report 2 has a 7,500-word formal maximum as counted by its independent
  Overleaf project. Tables, figure legends/captions, and appendices count;
  bibliography does not. Keep the internal target at or below 7,200 words.
- Use 12-point type, one-and-a-half or double spacing, A4, and at least 2 cm
  margins.
- Keep Report 2 as an independent Overleaf project shared with
  `srs53@cam.ac.uk` for review and word counting.
- The final submission PDF contains Report 1, an explicit Part II divider, and
  Report 2. The combined PDF is not the Report 2 word-count input.
- Keep the required title page and originality declaration, record the Report 2
  Overleaf word count, and submit the official signed declaration/cover sheet
  separately or embedded. Never fabricate a signature.
- The final report must be the student's own connected scientific account.
- AI assistance may organise, check, or propose structure; AI-generated prose is
  not accepted as submission text. The student rewrites and verifies it.

## 4. Report 1 non-repetition lock

Report 2 may summarise a Report 1 conclusion only when it explains a later
decision. It must not recreate:

- the Euler equation/background chapter;
- the generic finite-volume derivation;
- the full MUSCL--Hancock or HLLC derivation;
- the general IEEE floating-point survey;
- the Report 1 Euler validation narrative or figures;
- the Report 1 conclusion as a second literature review.

Common method material is cited back to Report 1 or compressed into one bridge
sentence. New space goes to ideal MHD, divergence control, HLL/HLLD development,
MHD validation, systematic variation, time evolution, and reproducibility.

## 5. Evidence-status rules

- `report-grade`: may support the bounded claim named in the evidence map.
- `validation`: supports correctness/measurement readiness, not a precision or
  hardware headline unless separately promoted.
- `provisional`: may be described as an observation but not elevated to a final
  unified claim.
- `negative-result`: report the tested hypothesis and its bounded failure.
- `morphology-only`: supports qualitative structure only.
- `invalid` and `superseded`: excluded from conclusions; retained for provenance.
- `deferred`: future work, never written as completed work.

No status is inherited by a neighbouring solver, test case, resolution,
precision, or device.

## 6. Terminology locks

- Use `fp32`/`fp64` for actual storage/arithmetic builds.
- Use “virtual precision p24/p53” for Verificarlo settings.
- Use “accuracy” only when a valid reference permits an error statement.
- Use “discrepancy”, “drift”, or “sensitivity” for cross-variant comparisons.
- Use “engineering growth rate” for the fixed-window temporal fits unless a
  formal Lyapunov analysis is added.
- Use “two-resolution sensitivity gate”, not “convergence”, for a 256/512 pair.
- HLLD is an analysed CPU solver unless evidence explicitly promotes another
  role. Do not imply HLLD GPU coverage.
- Two-dimensional physical-domain L1/L2 uses `dx*dy`, or the report explicitly
  declares a mean norm. Historical 2D L1/L2 computed with `dx` only is excluded;
  Linf remains usable because it has no cell-measure weight.

## 7. Chapter responsibility lock

- **C1:** question, Report 1 transition, scope, contribution, roadmap.
- **C2:** project development and new ideal-MHD implementation only.
- **C3:** complete experimental design, metrics, references, and exclusions.
- **C4:** MHD validation results only.
- **C5:** systematic precision/hardware/compiler/implementation/time results.
- **C6:** synthesis and reproducibility implications; no new results.
- **C7:** aim, bounded answers, contribution, limitations, future work.

## 8. Figure/table rules

- Every item carries one distinct claim.
- Every item is named and interpreted in the surrounding prose.
- Captions state comparison, metric, baseline, and scope without reproducing a
  paragraph.
- Axes include units or state nondimensionalization.
- Development smokes and provenance plots normally remain outside main text.
- Internal week/task labels never appear in captions or legends.

## 9. Code-submission connection

The report should enable assessors to identify the configurations and scripts
that generate reported results. The appendix maps figures/tables to configs,
summaries, metadata, and reproduction commands. Large grids, build directories,
executables, and unrelated Git history are not report artefacts.

The separate code-submission bundle is frozen before the report release
candidate. Its manifest lists source, retained configs/matrices, canonical
analysis scripts, environment/build instructions, summary checksums, and the
commands used to verify the bundle.

The release package also includes the combined Report 1 + Report 2 PDF, the
standalone Report 2 PDF used for word-count verification, and the signed
declaration/word-count documents required by the course.
