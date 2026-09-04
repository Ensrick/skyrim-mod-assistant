#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$PluginPath = "$PSScriptRoot\artifacts\WeaponBalancePatch.esp",
    [string]$OutputPath = "$PSScriptRoot\artifacts\Ensrick-Weapon-Speed-Balance-0.1.0.zip"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $PluginPath -PathType Leaf)) {
    throw "Plugin does not exist: $PluginPath"
}

$staging = Join-Path $PSScriptRoot 'work\package'
if (Test-Path -LiteralPath $staging) {
    Remove-Item -LiteralPath $staging -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $staging | Out-Null
Copy-Item -LiteralPath $PluginPath -Destination (Join-Path $staging 'WeaponBalancePatch.esp')

if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
}

# Compress-Archive preserves the source timestamp, producing a different
# release hash after an otherwise identical rebuild. Write the single-entry
# archive directly with a fixed ZIP timestamp instead.
$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}
$archiveStream = [System.IO.File]::Open(
    $OutputPath,
    [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::ReadWrite,
    [System.IO.FileShare]::None)
try {
    $archive = [System.IO.Compression.ZipArchive]::new(
        $archiveStream,
        [System.IO.Compression.ZipArchiveMode]::Create,
        $true)
    try {
        $entry = $archive.CreateEntry(
            'WeaponBalancePatch.esp',
            [System.IO.Compression.CompressionLevel]::Optimal)
        $entry.LastWriteTime = [DateTimeOffset]::new(1980, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
        $inputStream = [System.IO.File]::OpenRead($PluginPath)
        $entryStream = $entry.Open()
        try {
            $inputStream.CopyTo($entryStream)
        } finally {
            $entryStream.Dispose()
            $inputStream.Dispose()
        }
    } finally {
        $archive.Dispose()
    }
} finally {
    $archiveStream.Dispose()
}

Write-Host "Packaged $OutputPath"
Write-Host "SHA256 $((Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath).Hash)"
