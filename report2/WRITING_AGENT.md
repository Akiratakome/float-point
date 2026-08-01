# Report 2 Writing Agent

Read `docs/INDEX.md`, `docs/HARNESS.md`, `report2/INDEX.md`, and
`report2/planning/manuscript_outline.md` before editing manuscript files. Read
`report2/skills/README.md` before selecting a drafting or editing skill.

Hard rules:

- Do not change solver numerics, cfg defaults, output formats, or raw experiment
  artefacts while writing.
- Treat `docs/experiment_logs/report2_evidence_map.md` as the evidence-status
  authority. A local summary does not silently promote a provisional claim.
- Do not repeat Report 1's Euler equations, generic finite-volume derivation,
  MUSCL--Hancock derivation, HLLC tutorial, or general floating-point survey.
- Chapter 2 describes development choices; Chapter 3 owns the experiment
  matrix; Chapters 4--5 own results; Chapter 6 introduces no new evidence;
  Chapter 7 introduces no new analysis.
- Use “accuracy” only against an exact or explicitly defined numerical
  reference. Otherwise write discrepancy, difference, sensitivity, or drift.
- Verificarlo `p24` is virtual precision, not IEEE binary32/fp32.
- Two resolutions provide an engineering sensitivity gate, not asymptotic
  convergence.
- A fitted temporal rate is not a formal maximal Lyapunov exponent.
- Do not use week numbers, P0/P1, G0/G1, packet names, or local run labels in
  manuscript prose. They are allowed only in planning/evidence locators.
- Every figure/table must be introduced, interpreted, and tied to a bounded
  claim.
- For Chapter 4, learn the project voice from Report 1 Chapters 5 and 6 and use
  Report 1 Chapter 4 only for terminology continuity. Copy neither sentences
  nor Euler facts; follow `report2/planning/chapter4_writing_plan.md` Section 0.
- AI-assisted text is planning material until rewritten by the student in their
  own voice and checked with `avoiding-ai-flavor`.

The `.tex` chapter files are intentionally structure-only at this stage.
