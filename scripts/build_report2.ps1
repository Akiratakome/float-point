param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$reportDir = Join-Path $repoRoot "report2\phd-thesis-template-2.4"
$miktexBin = "C:\Users\tangy\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
$pdfLatex = Join-Path $miktexBin "pdflatex.exe"
$bibTex = Join-Path $miktexBin "bibtex.exe"

if (-not (Test-Path $pdfLatex) -or -not (Test-Path $bibTex)) {
    throw "MiKTeX was not found at $miktexBin"
}

if ($Clean) {
    $cleanDirs = @(
        $reportDir,
        (Join-Path $reportDir "Declaration"),
        (Join-Path $reportDir "Acknowledgement"),
        (Join-Path $reportDir "Abstract"),
        (Join-Path $reportDir "Chapter1"),
        (Join-Path $reportDir "Chapter2"),
        (Join-Path $reportDir "Chapter3"),
        (Join-Path $reportDir "Chapter4"),
        (Join-Path $reportDir "Chapter5"),
        (Join-Path $reportDir "Chapter6"),
        (Join-Path $reportDir "Chapter7"),
        (Join-Path $reportDir "Appendix1")
    )
    foreach ($cleanDir in $cleanDirs) {
        Get-ChildItem -LiteralPath $cleanDir -File | Where-Object {
            $_.Extension -in ".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".lof", ".log", ".lot", ".out", ".toc"
        } | Remove-Item -Force
    }
}

$env:Path = "$miktexBin;$env:Path"
Push-Location $reportDir
try {
    & $pdfLatex -interaction=nonstopmode -halt-on-error thesis.tex
    if ($LASTEXITCODE -ne 0) { throw "First pdflatex pass failed with exit code $LASTEXITCODE" }

    & $bibTex thesis
    if ($LASTEXITCODE -ne 0) { throw "BibTeX failed with exit code $LASTEXITCODE" }

    & $pdfLatex -interaction=nonstopmode -halt-on-error thesis.tex
    if ($LASTEXITCODE -ne 0) { throw "Second pdflatex pass failed with exit code $LASTEXITCODE" }
    & $pdfLatex -interaction=nonstopmode -halt-on-error thesis.tex
    if ($LASTEXITCODE -ne 0) { throw "Third pdflatex pass failed with exit code $LASTEXITCODE" }

    $unresolved = Select-String -Path "thesis.log" -Pattern @(
        "Package natbib Warning: Citation .* undefined",
        "Package natbib Warning: There were undefined citations",
        "LaTeX Warning: Reference .* undefined",
        "LaTeX Warning: There were undefined references"
    )
    if ($unresolved) {
        $details = ($unresolved | ForEach-Object { $_.Line.Trim() }) -join [Environment]::NewLine
        throw "Unresolved citations or cross-references remain:`n$details"
    }
}
finally {
    Pop-Location
}

Write-Output (Join-Path $reportDir "thesis.pdf")
