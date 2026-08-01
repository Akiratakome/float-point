# Combined Report 1 + Report 2 submission

Keep `report2/phd-thesis-template-2.4/thesis.tex` as the standalone Report 2
Overleaf main file. It is the source used for the 7,500-word Report 2 count and
should be shared with `srs53@cam.ac.uk`.

The final submitted report is assembled at PDF level so the two source trees,
labels, references, and page counters remain independent:

```text
Report 1 PDF -> explicit Part II divider -> standalone Report 2 PDF
```

## Local build

1. Compile the final Report 1 and standalone Report 2 PDFs.
2. From the repository root run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File report2/submission/prepare_and_build.ps1
   ```

3. Inspect `report2/submission/combined_submission.pdf` page by page.

The script validates the `%PDF-` header and copies the two PDFs into ignored
`inputs/` files before running two `pdflatex` passes so the Part I/Part II PDF
bookmarks are stable. No Perl-based `latexmk` installation is required.

## Overleaf workflow

1. Compile/download the standalone Report 2 PDF and record its Overleaf word
   count.
2. Upload the final Report 1 PDF as `inputs/report1.pdf` and standalone Report 2
   as `inputs/report2.pdf`.
3. Temporarily set `combined_submission.tex` as the main document and compile.
4. Download the combined PDF, then restore `thesis.tex` as the main Report 2
   source if further editing or word counting is required.

The official signed Report 2 declaration form is an external input. Submit it
separately or include it as instructed by course administration; the merge
wrapper does not invent or insert a signature.

Use `release_checklist.md` before submission.
