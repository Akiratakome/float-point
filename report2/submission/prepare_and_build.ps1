param(
    [string]$ReportOnePdf = "../../report1/phd-thesis-template-2.4/thesis.pdf",
    [string]$ReportTwoPdf = "../phd-thesis-template-2.4/thesis.pdf"
)

$submissionRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputRoot = Join-Path $submissionRoot "inputs"
New-Item -ItemType Directory -Force -Path $inputRoot | Out-Null

function Copy-ValidatedPdf {
    param(
        [string]$Source,
        [string]$Destination
    )

    $resolvedSource = (Resolve-Path -LiteralPath (Join-Path $submissionRoot $Source)).Path
    $header = [System.IO.File]::ReadAllBytes($resolvedSource)[0..4]
    $signature = [System.Text.Encoding]::ASCII.GetString($header)
    if ($signature -ne "%PDF-") {
        throw "Input is not a PDF: $resolvedSource"
    }
    Copy-Item -LiteralPath $resolvedSource -Destination $Destination -Force
}

Copy-ValidatedPdf -Source $ReportOnePdf -Destination (Join-Path $inputRoot "report1.pdf")
Copy-ValidatedPdf -Source $ReportTwoPdf -Destination (Join-Path $inputRoot "report2.pdf")

$pdfLatexCommand = Get-Command pdflatex -ErrorAction Stop
Push-Location $submissionRoot
try {
    # Two passes stabilize the Part I/Part II PDF bookmarks. Direct pdflatex
    # avoids requiring latexmk's separate Perl runtime.
    foreach ($pass in 1..2) {
        & $pdfLatexCommand.Source -interaction=nonstopmode -halt-on-error combined_submission.tex
        if ($LASTEXITCODE -ne 0) {
            throw "Combined submission LaTeX pass $pass failed with exit code $LASTEXITCODE"
        }
    }
}
finally {
    Pop-Location
}

Write-Output (Join-Path $submissionRoot "combined_submission.pdf")
