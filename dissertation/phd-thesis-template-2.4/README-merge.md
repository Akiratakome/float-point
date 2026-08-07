# Combined dissertation source (Part I + Part II)

Single Overleaf-ready project holding Report 1 as **Part I — First report**
(Chapters 1–7) and Report 2 as **Part II — Second report** (Chapters 8–14),
with shared front matter, one bibliography and merged appendices.

Compile with `pdflatex → bibtex → pdflatex → pdflatex` on `thesis.tex`
(Overleaf: set the main document to `thesis.tex`; the default pdfLaTeX recipe
handles the rest).

## Layout

| Path | Contents |
|---|---|
| `thesis.tex` | Master file; `\part{First report}` / `\part{Second report}` |
| `thesis-info.tex` | Combined title, author, supervisor, date |
| `Declaration/`, `Acknowledgement/`, `Abstract/` | Shared front matter; one abstract covers both parts |
| `Report1/chapter1..7.tex` | Report 1 chapters, **byte-identical to the submitted Report 1** |
| `Report2/chapter1..7.tex` | Report 2 chapters (+ two `\input` tables) |
| `Appendix1/` | Report 1 supplementary figures (Appendix A) |
| `Appendix2/` | Report 2 MCA scope table (Appendix B) |
| `Appendix3/` | Report 2 execution record and evidence map (Appendix C) |
| `References/references.bib` | Merged, de-duplicated bibliography |
| `Figs/report1/`, `Figs/report2/` | Figures, kept in separate subdirectories |

## What changed relative to the two standalone projects

Report 1 chapter sources are unchanged. Everything below is confined to the
shared scaffolding or to the Part II copies.

1. **Front matter shared.** One title page, declaration, acknowledgement and
   abstract. The abstract is new: it covers both parts and replaces the two
   separate abstracts, which saves roughly 80 words.
2. **Bibliography merged.** 60 entries, all cited. Eighteen works appeared in
   both `.bib` files under different keys (for example `toro2009` and
   `toro2009riemann`); the Report 1 key wins and the Part II sources were
   rewritten to match, so no work is listed twice. Style is `plainnat`,
   matching the `numbered` class option.
3. **Cross-references repaired.** Report 2's chapters are numbered 8–14 here,
   so its hard-coded `Chapter~N` references were converted to
   `\ref{}` cross-references and two missing chapter labels
   (`chap:development`, `chap:methodology`) were added. Report 1's hard-coded
   numbers still point at Chapters 1–7 and needed no change.
4. **Include paths updated** for the four `\input` files that moved with the
   Part II chapters and Appendix C.
5. **Spacing.** `\onehalfspacing` is enabled, as the handbook requires. The
   standalone Report 1 project had it commented out, so Part I paginates
   differently here than in its own PDF.
6. **Dropped** the `index` class option, `\printnomenclature` and
   `\printthesisindex`, which the standalone Report 1 project carried but never
   populated.
7. **Appendix C added** (`Appendix3/`), holding the Part II execution and
   arithmetic record and the evidence map. It is referenced from the
   reproducibility discussion in Chapter 13.

## Word count

`texcount -inc -sum thesis.tex` reports **15,099** words in text (excluding
captions, tables, headers and the bibliography). The two standalone projects
count 7,762 and 7,552 on the same basis.

## Still to do before submission

- Take the authoritative Overleaf word count and record it on the declaration.
- Obtain, sign and attach the official declaration / Certificate of Submission.
