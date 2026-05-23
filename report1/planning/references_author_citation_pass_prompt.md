# References Capitalization and Author-Name Citation Pass Prompt

This prompt is for a focused bibliography and citation-style pass after the
Chapter 5 supervisor-feedback update. It is not a content rewrite prompt.

---

## Master prompt

You are Codex in:

```text
c:\Users\tangy\Desktop\floatpoint
```

Run a controlled References capitalization and author-name citation pass for
Cambridge MPhil Report 1.

Primary files:

```text
report1/phd-thesis-template-2.4/References/references.bib
report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Read first:

1. `docs/INDEX.md`
2. `docs/HARNESS.md`
3. `report1/INDEX.md`
4. `report1/planning/reportagents.md`
5. `report1/planning/manuscript_outline.md`
6. `report1/planning/supervisor_feedback_map.md`
7. `report1/planning/supervisorguide.md`
8. `report1/references/reference.md`
9. `report1/phd-thesis-template-2.4/CONFIG_AND_PACKAGES.md`
10. `report1/phd-thesis-template-2.4/References/references.bib`

Do not read `report1/planning/old/` unless the user explicitly asks for an
archival comparison.

Read before editing prose:

```text
report1/skills/avoiding-ai-flavor/SKILL.md
report1/skills/academic-english-style/SKILL.md
```

## Scope

Allowed edits:

- Protect technical capitalization in `references.bib` title and booktitle
  fields.
- Convert selected parenthetical citations into author-name prose where the
  sentence introduces a specific method, benchmark, solver, or tool.
- Make tiny surrounding sentence edits needed for grammar after citation-style
  conversion.

Not allowed:

- Do not add new scientific claims.
- Do not change numerical values, evidence interpretation, figure/table content,
  solver descriptions, or chapter structure.
- Do not modify solver code, experiment outputs, raw artifacts, or anything
  under `experiments/`.
- Do not prune uncited BibTeX entries in this pass unless the user explicitly
  asks. Report uncited entries separately if found.
- Do not switch the template from natbib to biblatex. The current template uses
  natbib and `apalike`.

## Part A: BibTeX Capitalization Pass

Open:

```text
report1/phd-thesis-template-2.4/References/references.bib
```

Protect technical strings in `title` and `booktitle` fields using braces so
BibTeX style files do not lowercase them. Apply this where the string appears
as a technical initialism, named method, standard, format, tool, or benchmark
dimension.

Required protection candidates:

```text
{HLL}
{HLLC}
{GPU}
{CUDA}
{MHD}
{IEEE}
{AMReX}
{MUSCL-Hancock}
{1D}
{2D}
{Euler}
{Verificarlo}
{ARITH}
```

Known likely edits:

- `liska_wendroff_2003`: protect `{1D}`, `{2D}`, `{Euler}`.
- `toro_spruce_speares_1994`: protect `{HLL}`.
- `bard_dorelli_2014`: protect `{GPU}` and `{MUSCL-Hancock}` if those strings
  remain in the title.
- `zhang_etal_2019`: protect `{AMReX}`.
- `ieee754_2019`: protect `{IEEE}`.
- `denis_etal_2016`: protect `{Verificarlo}`, `{IEEE}`, and `{ARITH}` where
  present.
- Keep existing `{MHD}` protection in `dedner_2002`.

Rules:

- Do not change author names, DOI values, journal names, years, pages, or keys
  unless there is a clear typo and `reference.md` supports the correction.
- Do not over-brace ordinary English words.
- Preserve existing BibTeX keys.

## Part B: Author-Name Citation Pass

Inspect active manuscript-facing chapter files only:

```text
report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
report1/phd-thesis-template-2.4/Chapter7/chapter7.tex
```

Do not edit snapshot files such as `chapter3_pre_dispatch_snapshot.tex` or
template originals under `SampleContent/`.

Use author-name prose when a sentence introduces a specific named method,
benchmark, solver, or tool. Natbib is available, so `\citet{...}` can be used
where the grammar is natural. A sentence may also use plain prose plus
`\citep{...}` if that reads better.

Preferred patterns:

- "Toro's exact Riemann solutions ..." with `\citep{toro2009}` or
  `\citet{toro2009}`.
- "Sod's shock-tube problem ..." with `\citep{sod_1978}`.
- "Liska and Wendroff's configurations ..." with
  `\citep{liska_wendroff_2003}`.
- "Harten, Lax, and van Leer introduced ..." with
  `\citep{harten_lax_vanleer_1983}` or `\citet{harten_lax_vanleer_1983}`.
- "Toro, Spruce, and Speares' HLLC restoration ..." with
  `\citep{toro_spruce_speares_1994}`.
- "van Leer's MUSCL reconstruction ..." with `\citep{vanleer_1979}`.
- "Denis et al.'s Verificarlo ..." with `\citep{denis_etal_2016}`.
- "Parker's Monte Carlo arithmetic ..." with `\citep{parker_1997}`.
- "Dedner et al.'s hyperbolic divergence cleaning ..." with
  `\citep{dedner_2002}`.
- "Evans and Hawley's constrained transport ..." with
  `\citep{evans_hawley_1988}`.

Keep parenthetical citations when:

- the source supports a general background sentence rather than introducing a
  named method;
- multiple sources jointly support a broad point;
- converting the sentence would make the prose longer or awkward;
- the chapter section is still a placeholder and citation context is unstable.

Do not force every citation into `\citet`. The goal is readability, not a
mechanical replacement.

## Citation-Set Rules

- Do not add a citation merely because a source exists in `reference.md`.
- Do not cite AMReX unless the report actually discusses AMReX in the final
  implementation narrative.
- Do not cite `wolf_etal_1985` or `eckmann_ruelle_1985` in Chapter 5 unless the
  user explicitly asks for a chaos-theory framing.
- If a citation key appears in a manuscript file but is absent from
  `references.bib`, either add a verified BibTeX entry from `reference.md` or
  remove/replace the citation if it is unsupported. Report the choice.
- If a BibTeX entry is present but uncited, leave it in place for now and report
  it as an optional cleanup item.

## Review Workflow

1. Baseline scan:

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter1 report1/phd-thesis-template-2.4/Chapter2 report1/phd-thesis-template-2.4/Chapter3 report1/phd-thesis-template-2.4/Chapter4 report1/phd-thesis-template-2.4/Chapter5 report1/phd-thesis-template-2.4/Chapter6 report1/phd-thesis-template-2.4/Chapter7
```

2. BibTeX capitalization scan:

```powershell
rg -n "title\\s*=|booktitle\\s*=" report1/phd-thesis-template-2.4/References/references.bib
```

3. Edit `references.bib` capitalization first.

4. Edit citation prose in active chapter files.

5. Re-scan citations and manually inspect every changed sentence. Confirm that:

- the citation supports the sentence;
- author names are spelled consistently;
- no sentence became wordier without purpose;
- no numerical or evidence claim changed;
- no author-name citation is used before the method/tool is defined.

6. Check citation keys:

```powershell
rg -n "\\\\cite|citet|citep" report1/phd-thesis-template-2.4/Chapter1 report1/phd-thesis-template-2.4/Chapter2 report1/phd-thesis-template-2.4/Chapter3 report1/phd-thesis-template-2.4/Chapter4 report1/phd-thesis-template-2.4/Chapter5 report1/phd-thesis-template-2.4/Chapter6 report1/phd-thesis-template-2.4/Chapter7
rg -n "^@" report1/phd-thesis-template-2.4/References/references.bib
```

7. Run a forbidden-citation check for Chapter 5:

```powershell
rg -n "wolf_etal|eckmann|Lyapunov exponent|Lyapunov-like" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Expected: no hits.

8. Compile with bibliography:

```powershell
Set-Location report1/phd-thesis-template-2.4
pdflatex -draftmode -interaction=nonstopmode thesis.tex
bibtex thesis
pdflatex -draftmode -interaction=nonstopmode thesis.tex
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

If compilation fails, fix only citation/BibTeX issues introduced by this pass
unless the failure is clearly pre-existing.

## Final Response Format

Respond in Chinese with:

- which files changed;
- which BibTeX capitalization fixes were made;
- which chapters received author-name citation edits;
- any citation keys added, removed, or left uncited;
- whether Chapter 5 remains free of chaos-theory citations;
- bibliography compile result and any remaining warnings.

Do not claim the full report is finished.
