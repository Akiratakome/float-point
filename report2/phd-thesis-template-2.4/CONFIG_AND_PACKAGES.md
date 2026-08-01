# Report 2 LaTeX configuration

- Root file: `thesis.tex`
- Metadata: `thesis-info.tex`
- Shared class: `Classes/PhDThesisPSnPDF.cls`
- Packages and style: `Preamble/preamble.tex`
- Bibliography: `References/references.bib`
- Figures: `Figs/`
- Chapter source: `Chapter1/` through `Chapter7/`

The class and preamble are inherited mechanically from the Report 1 template so
the two reports use consistent typography. Their scientific structures and
manuscript text are independent.

Build products (`*.aux`, `*.log`, `*.pdf`, etc.) are ignored and must not be
committed. Use `scripts/build_report2.ps1` when compilation is required.
