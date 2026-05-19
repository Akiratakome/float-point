# Report 1 Drafting Status

Last updated: 2026-05-19.

## Current State

- `report1/INDEX.md` is the entry point for Report 1 reading and drafting.
- Core planning files now live under `report1/planning/`.
- Official requirements PDFs now live under `report1/requirements/`.
- The working reference map now lives at `report1/references/reference.md`.
- The example report now lives at `report1/examples/Project-Report-1-example.pdf`.
- Writing skills remain under `report1/skills/`; source notes are isolated under `report1/skills/source-notes/`.

## Chapter Drafting Progress

| Ch | Title | Status | Notes |
| --- | --- | --- | --- |
| 1 | Introduction | not started | placeholder file only |
| 2 | Background and Governing Equations | not started | placeholder file only |
| 3 | Numerical Method | **finished (2026-05-19, uncommitted)** | finite-volume update, MUSCL--Hancock/minbee reconstruction, HLLC/Rusanov fluxes, CFL/positivity, dimensional splitting, precision-sensitive branch/fast-math axes, MHD context; texcount text approx. 906 |
| 4 | Implementation and Experimental Design | **finished (2026-05-18, commit `8a19a50`)** | self-score 100/100; OpenMP/MPI strategy, STRICT_IEEE flag inventory, Kahan summation, CUDA $16\times16$ blocks, 5 implementation features, $1600^2$/$N{=}800$ reference strategy; counted words 1157 |
| 5 | Validation and Precision Results | **finished (commit `f5d18f7`)** | LW3 1600² reference, validation matrix `tab:validation-matrix`, fp32/fp64 + CPU/GPU + branch/compiler variation results |
| 6 | Discussion | not started | placeholder file only |
| 7 | Conclusion | not started | placeholder file only |

## LaTeX Workspace

- Root file: `report1/phd-thesis-template-2.4/thesis.tex`.
- Configuration/package map: `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`.
- Title metadata placeholder: `report1/phd-thesis-template-2.4/thesis-info.tex`.
- Declaration: `report1/phd-thesis-template-2.4/Declaration/declaration.tex`.
- Word-count declaration placeholder: `report1/phd-thesis-template-2.4/WordCount/wordcount.tex`.
- Abstract placeholder: `report1/phd-thesis-template-2.4/Abstract/abstract.tex`.
- Preamble: `algorithm` + `algpseudocode` packages enabled for Chapter 4 pseudocode.
- Bibliography keys verified and in use by Ch4/Ch5: `toro2009`, `sod_1978`, `liska_wendroff_2003`, `ieee754_2019`, `goldberg_1991`, `higham_2002`, `bard_dorelli_2014`, `zhang_etal_2019`, `parker_1997`, `denis_etal_2016`.
- Latest draft build: `pdflatex -draftmode -interaction=nonstopmode thesis.tex` exits 0; Chapter 3 has no remaining overfull boxes after compression, with remaining layout warnings in later chapters.

## Sample Content

- Original CUED template chapter files, appendix files, and sample bibliography are quarantined in `report1/phd-thesis-template-2.4/SampleContent/template-originals/`.
- `thesis.tex` no longer includes the dedication page or sample appendices.

## Remaining Placeholders

- Replace `Author Name Placeholder` in `thesis-info.tex` and `Declaration/declaration.tex`.
- Confirm whether to keep or remove the acknowledgements page.
- Insert the final Overleaf counted-text value into `WordCount/wordcount.tex`.
- Add figures referenced by Chapter 5 once final-evidence selections are locked in `experiments/report1_evidence_map.md`.

## Next Drafting Step

Chapters 3--5 are complete, with Chapter 3 now providing the method background referenced by the evidence-bearing Chapters 4 and 5. The next drafting target is **Chapter 2 (Background and Governing Equations)**, followed by Ch1 (Introduction), then Ch6 (Discussion) and Ch7 (Conclusion). The Abstract is written last. Read `report1/INDEX.md`, then `report1/planning/manuscript_outline.md`, then the relevant chapter dispatch prompt before adding prose.
