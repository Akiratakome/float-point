param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$reportDir = Join-Path $repoRoot "report2\phd-thesis-template-2.4"
$miktexBin = "C:\Users\tangy\AppData\Local\Programs\MiKTeX\miktex\bin\x64"

if (-not (Test-Path (Join-Path $miktexBin "pdflatex.exe"))) {
    throw "MiKTeX was not found at $miktexBin"
}

if ($Clean) {
    Get-ChildItem $reportDir -File | Where-Object {
        $_.Extension -in ".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".lof", ".log", ".lot", ".out", ".toc"
    } | Remove-Item -Force
}

$env:Path = "$miktexBin;$env:Path"
Push-Location $reportDir
try {
    & (Join-Path $miktexBin "pdflatex.exe") -interaction=nonstopmode -halt-on-error thesis.tex
    if ($LASTEXITCODE -ne 0) { throw "First pdflatex pass failed with exit code $LASTEXITCODE" }
    & (Join-Path $miktexBin "pdflatex.exe") -interaction=nonstopmode -halt-on-error thesis.tex
    if ($LASTEXITCODE -ne 0) { throw "Second pdflatex pass failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}

Write-Output (Join-Path $reportDir "thesis.pdf")
