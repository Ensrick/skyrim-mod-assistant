#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$PluginPath = "$PSScriptRoot\artifacts\WeaponBalancePatch.esp",
    [string]$SelectionReportPath = "$PSScriptRoot\artifacts\selection-report.json",
    [string]$BuildManifestPath = "$PSScriptRoot\artifacts\build-manifest.json",
    [string]$FinalWinnerAuditPath = "$PSScriptRoot\artifacts\final-winner-audit.json",
    [string]$OutputPath = "$PSScriptRoot\artifacts\Ensrick-Weapon-Speed-Balance-0.2.0.zip",
    [string]$Instance = '',
    [string]$Profile = 'Default',
    [string]$InstalledModName = 'Ensrick - Weapon Speed Balance',
    [switch]$AllowPendingFinalAudit,
    [switch]$ReplaceExistingArchive
)

$ErrorActionPreference = 'Stop'
$expectedPluginName = 'WeaponBalancePatch.esp'

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Test-PathWithin {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Root
    )
    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar)
    return $fullPath.StartsWith(
        "$fullRoot$([IO.Path]::DirectorySeparatorChar)",
        [StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoReparseTraversal {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Boundary
    )
    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullBoundary = [IO.Path]::GetFullPath($Boundary).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar)
    if (-not (Test-PathWithin $fullPath $fullBoundary)) {
        throw "Path escapes its owned boundary ${fullBoundary}: $fullPath"
    }
    $cursor = $fullPath
    while ($true) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing path that traverses a reparse point: $cursor"
            }
        }
        if ($cursor.Equals($fullBoundary, [StringComparison]::OrdinalIgnoreCase)) { break }
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent.Equals($cursor, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Could not prove path containment below ${fullBoundary}: $fullPath"
        }
        $cursor = $parent
    }
}

$artifactRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'artifacts'))
$PluginPath = [IO.Path]::GetFullPath($PluginPath)
$SelectionReportPath = [IO.Path]::GetFullPath($SelectionReportPath)
$BuildManifestPath = [IO.Path]::GetFullPath($BuildManifestPath)
$FinalWinnerAuditPath = [IO.Path]::GetFullPath($FinalWinnerAuditPath)
$OutputPath = [IO.Path]::GetFullPath($OutputPath)

if (-not (Test-PathWithin $OutputPath $artifactRoot)) {
    throw "Package output must remain below the owned artifact root: $artifactRoot"
}
Assert-NoReparseTraversal $OutputPath $PSScriptRoot
if ([IO.Path]::GetFileName($PluginPath) -cne $expectedPluginName) {
    throw "Plugin filename must be exactly $expectedPluginName."
}

$inputPaths = @($PluginPath, $SelectionReportPath, $BuildManifestPath, $FinalWinnerAuditPath)
foreach ($inputPath in $inputPaths) {
    if ($OutputPath.Equals($inputPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Package output must not alias an input artifact: $inputPath"
    }
}
foreach ($required in @($PluginPath, $SelectionReportPath, $BuildManifestPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required build artifact does not exist: $required"
    }
    if (-not (Test-PathWithin $required $artifactRoot)) {
        throw "Package inputs must remain below the owned artifact root: $required"
    }
    Assert-NoReparseTraversal $required $PSScriptRoot
}

$manifest = Get-Content -Raw -LiteralPath $BuildManifestPath | ConvertFrom-Json
$pluginHash = Get-Sha256 $PluginPath
$selectionReportHash = Get-Sha256 $SelectionReportPath
if ($manifest.outputPlugin -cne $expectedPluginName -or
    $manifest.pluginSha256 -ne $pluginHash) {
    throw 'Plugin identity/hash differs from build-manifest.json.'
}
if ($manifest.selectionReportSha256 -ne $selectionReportHash) {
    throw 'Selection-report hash differs from build-manifest.json.'
}
if ($manifest.schemaVersion -ne 2 -or $manifest.generatorVersion -ne '0.2.0' -or
    -not $manifest.eslFlagged -or $manifest.ownLightFormCount -ne 0 -or
    -not $manifest.onlySpeedSemanticComparison -or
    -not $manifest.deterministicDoubleBuild) {
    throw 'Build manifest does not satisfy the 0.2 release invariants.'
}

$archiveInputs = [Collections.Generic.List[object]]::new()
$archiveInputs.Add([pscustomobject]@{
    Source = $PluginPath
    Entry = $expectedPluginName
})
$archiveInputs.Add([pscustomobject]@{
    Source = $SelectionReportPath
    Entry = 'EnsrickMetadata/selection-report.json'
})
$archiveInputs.Add([pscustomobject]@{
    Source = $BuildManifestPath
    Entry = 'EnsrickMetadata/build-manifest.json'
})

if ($manifest.finalWinningSpeedGate -eq 'pass') {
    if (-not (Test-PathWithin $FinalWinnerAuditPath $artifactRoot)) {
        throw "Final-winner receipt must remain below the owned artifact root: $FinalWinnerAuditPath"
    }
    Assert-NoReparseTraversal $FinalWinnerAuditPath $PSScriptRoot
    if (-not (Test-Path -LiteralPath $FinalWinnerAuditPath -PathType Leaf)) {
        throw 'The manifest records a passing final-winner gate, but its receipt is absent.'
    }
    if (-not $manifest.finalWinnerAuditSha256 -or
        $manifest.finalWinnerAuditSha256 -ne (Get-Sha256 $FinalWinnerAuditPath)) {
        throw 'Final-winner audit hash differs from build-manifest.json.'
    }
    $archiveInputs.Add([pscustomobject]@{
        Source = $FinalWinnerAuditPath
        Entry = 'EnsrickMetadata/final-winner-audit.json'
    })

    $auditScript = Join-Path $PSScriptRoot 'audit.ps1'
    $freshnessArguments = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-File', $auditScript,
        '-FreshnessOnly', '-Profile', $Profile, '-ArtifactRoot', $artifactRoot,
        '-InstalledModName', $InstalledModName
    )
    if ($Instance) { $freshnessArguments += @('-Instance', $Instance) }
    $freshnessOutput = & (Join-Path $PSHOME 'pwsh.exe') @freshnessArguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Release freshness gate failed: $($freshnessOutput -join [Environment]::NewLine)"
    }
} elseif ($AllowPendingFinalAudit) {
    if (Test-Path -LiteralPath $FinalWinnerAuditPath -PathType Leaf) {
        throw 'A final-winner receipt exists while the manifest gate is pending; audit or remove the stale receipt.'
    }
} else {
    throw 'Final-winner audit is pending. Use -AllowPendingFinalAudit only for a non-release candidate package.'
}

if (Test-Path -LiteralPath $OutputPath) {
    if (-not $ReplaceExistingArchive) {
        throw "Package output already exists: $OutputPath. Pass -ReplaceExistingArchive to replace this exact file."
    }
    if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
        throw "Existing package output is not a regular file: $OutputPath"
    }
    Remove-Item -LiteralPath $OutputPath -Force
}

$outputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$archiveStream = [IO.File]::Open(
    $OutputPath,
    [IO.FileMode]::CreateNew,
    [IO.FileAccess]::ReadWrite,
    [IO.FileShare]::None)
try {
    $archive = [IO.Compression.ZipArchive]::new(
        $archiveStream,
        [IO.Compression.ZipArchiveMode]::Create,
        $true)
    try {
        foreach ($archiveInput in @($archiveInputs | Sort-Object Entry)) {
            $entry = $archive.CreateEntry(
                $archiveInput.Entry,
                [IO.Compression.CompressionLevel]::Optimal)
            $entry.LastWriteTime = [DateTimeOffset]::new(
                1980, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
            $inputStream = [IO.File]::OpenRead($archiveInput.Source)
            $entryStream = $entry.Open()
            try {
                $inputStream.CopyTo($entryStream)
            } finally {
                $entryStream.Dispose()
                $inputStream.Dispose()
            }
        }
    } finally {
        $archive.Dispose()
    }
} finally {
    $archiveStream.Dispose()
}

Write-Host "Packaged $OutputPath"
Write-Host "SHA256 $(Get-Sha256 $OutputPath)"
