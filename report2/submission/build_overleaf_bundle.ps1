param(
    [string]$OutputName = "combined_submission_overleaf.zip"
)

$submissionRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputPath = Join-Path $submissionRoot $OutputName
$requiredFiles = @(
    "combined_submission.tex",
    "README.md",
    "inputs/README.md",
    "inputs/report1.pdf",
    "inputs/report2.pdf"
)

foreach ($relativePath in $requiredFiles) {
    $absolutePath = Join-Path $submissionRoot $relativePath
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
        throw "Missing Overleaf bundle input: $absolutePath"
    }
}

foreach ($relativePath in @("inputs/report1.pdf", "inputs/report2.pdf")) {
    $absolutePath = Join-Path $submissionRoot $relativePath
    $header = [System.IO.File]::ReadAllBytes($absolutePath)[0..4]
    if ([System.Text.Encoding]::ASCII.GetString($header) -ne "%PDF-") {
        throw "Bundle input is not a PDF: $absolutePath"
    }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$outputStream = [System.IO.File]::Open(
    $outputPath,
    [System.IO.FileMode]::Create,
    [System.IO.FileAccess]::ReadWrite,
    [System.IO.FileShare]::None
)
$outputArchive = New-Object System.IO.Compression.ZipArchive(
    $outputStream,
    [System.IO.Compression.ZipArchiveMode]::Create
)
try {
    foreach ($relativePath in $requiredFiles) {
        $absolutePath = Join-Path $submissionRoot $relativePath
        $entryName = $relativePath.Replace("\", "/")
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $outputArchive,
            $absolutePath,
            $entryName,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $outputArchive.Dispose()
    $outputStream.Dispose()
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($outputPath)
try {
    $entryNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
    foreach ($relativePath in $requiredFiles) {
        if ($relativePath -notin $entryNames) {
            throw "Overleaf bundle is missing archive entry: $relativePath"
        }
    }
}
finally {
    $archive.Dispose()
}

Write-Output $outputPath
