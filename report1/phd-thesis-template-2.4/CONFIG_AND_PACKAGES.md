# LaTeX Configuration and Package Map

This file is the maintenance guide for the Report 1 LaTeX workspace. It keeps
configuration discoverable without moving the template paths that `thesis.tex`
and the CUED class expect.

## Do Not Move

These paths are compile-facing and should remain stable unless `thesis.tex`,
`thesis-info.tex`, and the CUED class are updated together:

| Path | Purpose |
|---|---|
| `thesis.tex` | Root compile file and chapter include order. |
| `thesis-info.tex` | Title-page metadata, author placeholder, degree, supervisor, date, PDF metadata. |
| `Preamble/preamble.tex` | Report-level packages and LaTeX settings. Edit here for packages, tables, units, spacing, and referencing. |
| `Classes/PhDThesisPSnPDF.cls` | CUED thesis/report class. Treat as vendor template code. |
| `Classes/glyphtounicode.tex` | PDF text extraction support loaded by the class. |
| `sty/breakurl.sty` | Local fallback package from the original template. Do not use unless needed by the template. |
| `Figs/` | Crest and template figure search path used by the title page/class. |
| `References/references.bib` | Working BibTeX file for verified report references. |
| `Variables.ini` | Makefile configuration. Keep at workspace root because `Makefile` includes it by name. |
| `Makefile`, `compile-thesis.sh`, `compile-thesis-windows.bat` | Existing compile helpers. |

## Package Policy

- Add writing-time packages in `Preamble/preamble.tex`, not in individual chapters.
- Prefer established packages already present: `caption`, `subcaption`, `booktabs`,
  `multirow`, `siunitx`, and `enumitem`.
- Before adding algorithm or pseudocode packages, remember that pseudocode text is
  counted by Overleaf Word Count for this report.
- Keep bibliography handling on the current natbib path unless there is a clear
  reason to switch the whole template to biblatex.

## Generated Files

The following are build products and should not be treated as source:

- `thesis.aux`, `thesis.log`, `thesis.toc`, `thesis.lof`, `thesis.lot`
- `thesis.bbl`, `thesis.blg`
- `thesis.fls`, `thesis.fdb_latexmk`
- `thesis.idx`, `thesis.ind`, `thesis.ilg`
- `thesis.nlo`, `thesis.nls`, `thesis.nlg`
- `thesis.out`
- `thesis.synctex.gz` and editor-created Synctex busy files
- `thesis.pdf` when generated locally

The local `.gitignore` covers these transient files. The existing tracked
`thesis.ps` is inherited from the template and is not part of the Report 1 source
workflow; do not cite or edit it for manuscript content.

## Safe Editing Pattern

1. Edit `thesis-info.tex` for metadata placeholders.
2. Edit `Preamble/preamble.tex` for package/config changes.
3. Edit chapter files under `Chapter1/` through `Chapter7/` for manuscript prose.
4. Compile from this directory with `pdflatex thesis.tex` or an existing helper.
5. If a package or path change is made, run `pdflatex -draftmode -interaction=nonstopmode thesis.tex` before continuing prose work.
