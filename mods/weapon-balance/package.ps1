#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$PluginPath = "$PSScriptRoot\artifacts\WeaponBalancePatch.esp",
    [string]$SelectionReportPath = "$PSScriptRoot\artifacts\selection-report.json",
    [string]$BuildManifestPath = "$PSScriptRoot\artifacts\build-manifest.json",
    [string]$FinalWinnerAuditPath = "$PSScriptRoot\artifacts\final-winner-audit.json",
    [string]$OutputPath = "$PSScriptRoot\artifacts\Ensrick-Weapon-Speed-Balance-0.3.0.zip",
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

function Get-LocalizedSidecarInventory([string]$PluginPath) {
    $pluginFullPath = [IO.Path]::GetFullPath($PluginPath)
    $stringsRoot = Join-Path (Split-Path -Parent $pluginFullPath) 'Strings'
    if (-not (Test-Path -LiteralPath $stringsRoot)) { return @() }
    if (-not (Test-Path -LiteralPath $stringsRoot -PathType Container)) {
        throw "Localized sidecar root is not a directory: $stringsRoot"
    }
    Assert-NoReparseTraversal $stringsRoot $PSScriptRoot
    $stem = [IO.Path]::GetFileNameWithoutExtension($pluginFullPath)
    $pattern = '^' + [regex]::Escape($stem) +
        '_(?<language>[A-Za-z][A-Za-z0-9_]*)\.(?<kind>STRINGS|ILSTRINGS|DLSTRINGS)$'
    $caseInsensitivePattern = '(?i)' + $pattern
    $rows = [Collections.Generic.List[object]]::new()
    foreach ($item in Get-ChildItem -LiteralPath $stringsRoot -Force | Sort-Object Name) {
        if (-not [regex]::IsMatch($item.Name, $caseInsensitivePattern)) { continue }
        $match = [regex]::Match($item.Name, $pattern)
        if (-not $match.Success) {
            throw "Localized sidecar has noncanonical casing: $($item.FullName)"
        }
        if ($item.PSIsContainer) {
            throw "Localized sidecar path is not a regular file: $($item.FullName)"
        }
        Assert-NoReparseTraversal $item.FullName $PSScriptRoot
        $kind = $match.Groups['kind'].Value
        $rows.Add([pscustomobject]@{
            relativePath = "Strings/$($item.Name)"
            language = $match.Groups['language'].Value
            source = switch ($kind) {
                'STRINGS' { 'Normal' }
                'ILSTRINGS' { 'IL' }
                'DLSTRINGS' { 'DL' }
                default { throw "Unsupported localized sidecar kind: $kind" }
            }
            bytes = [long]$item.Length
            sha256 = Get-Sha256 $item.FullName
            fullPath = $item.FullName
        })
    }
    return @($rows | Sort-Object relativePath)
}

function Get-LocalizedSidecarDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object relativePath | ForEach-Object {
        "$($_.relativePath)|$($_.language)|$($_.source)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
}

function Get-InputLocalizationPhysicalDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object provider, kind, relativePath | ForEach-Object {
        "$($_.provider)|$($_.kind)|$($_.relativePath)|$($_.winningProvider)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
}

function Get-InputLocalizationContractDigest($Contract) {
    $node = [System.Text.Json.Nodes.JsonNode]::Parse(
        ($Contract | ConvertTo-Json -Depth 20 -Compress))
    if ($null -eq $node -or -not $node.AsObject().Remove('sha256')) {
        throw 'Input-localization-resource contract does not contain its aggregate hash.'
    }
    $options = [System.Text.Json.JsonSerializerOptions]::new()
    $options.PropertyNamingPolicy = [System.Text.Json.JsonNamingPolicy]::CamelCase
    $options.WriteIndented = $true
    $canonical = $node.ToJsonString($options)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($canonical)))
}

function Assert-LocalizedSidecarShape($Inventory, [string]$Context) {
    $rows = @($Inventory)
    if ($rows.Count -eq 0) { throw "$Context contains no localized sidecars." }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($row in $rows) {
        if (-not $seen.Add([string]$row.relativePath)) {
            throw "$Context has a duplicate localized sidecar path: $($row.relativePath)"
        }
        if ([long]$row.bytes -le 0) { throw "$Context has an empty localized sidecar: $($row.relativePath)" }
    }
    foreach ($group in @($rows | Group-Object language)) {
        $sources = @($group.Group.source | Sort-Object)
        if ($group.Count -ne 3 -or ($sources -join '|') -cne 'DL|IL|Normal') {
            throw "$Context must contain an exact STRINGS/ILSTRINGS/DLSTRINGS trio for $($group.Name)."
        }
    }
}

function Assert-LocalizedSidecarsEqual($Expected, $Actual, [string]$Context) {
    $expectedRows = @($Expected | Sort-Object relativePath)
    $actualRows = @($Actual | Sort-Object relativePath)
    if ($expectedRows.Count -ne $actualRows.Count) {
        throw "$Context localized sidecar count differs: expected $($expectedRows.Count), got $($actualRows.Count)."
    }
    for ($index = 0; $index -lt $expectedRows.Count; $index++) {
        foreach ($field in @('relativePath', 'language', 'source', 'bytes', 'sha256')) {
            if ([string]$expectedRows[$index].$field -cne [string]$actualRows[$index].$field) {
                throw "$Context localized sidecar differs at index $index field $field."
            }
        }
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
if ($manifest.schemaVersion -ne 3 -or $manifest.generatorVersion -ne '0.3.0' -or
    -not $manifest.eslFlagged -or $manifest.ownLightFormCount -ne 0 -or
    -not $manifest.onlySpeedSemanticComparison -or
    -not $manifest.deterministicDoubleBuild -or -not $manifest.localized) {
    throw 'Build manifest does not satisfy the 0.3 localized release invariants.'
}
$manifestSidecars = @($manifest.localizedSidecars)
Assert-LocalizedSidecarShape $manifestSidecars 'Build manifest'
if ($manifest.localizedSidecarsSha256 -cne (Get-LocalizedSidecarDigest $manifestSidecars)) {
    throw 'Build manifest localized-sidecar aggregate hash is invalid.'
}
$manifestLanguages = @($manifestSidecars.language | Sort-Object -Unique)
if ((@($manifest.translationLanguages) -join '|') -cne ($manifestLanguages -join '|')) {
    throw 'Build manifest translation-language inventory differs from its sidecars.'
}
$inputTranslationSemantics = $manifest.inputTranslationSemantics
$inputLocalizationResources = $manifest.inputLocalizationResources
if ($null -eq $inputTranslationSemantics -or
    $inputTranslationSemantics.schemaVersion -ne 1 -or
    [string]$inputTranslationSemantics.sha256 -notmatch '^[A-F0-9]{64}$' -or
    $null -eq $inputLocalizationResources -or
    $inputLocalizationResources.schemaVersion -ne 1 -or
    (Get-InputLocalizationContractDigest $inputLocalizationResources) -cne
        [string]$inputLocalizationResources.sha256) {
    throw 'Build manifest input-localization provenance is invalid.'
}
$physicalProviders = @($manifest.inputLocalizationResourceProviders)
if ($manifest.inputLocalizationResourceProvidersSha256 -cne
    (Get-InputLocalizationPhysicalDigest $physicalProviders)) {
    throw 'Build manifest input-localization physical-provider hash is invalid.'
}
$semanticProviders = @($inputTranslationSemantics.providers |
    Where-Object sourceUsesLocalization | Sort-Object provider)
$resourceProviders = @($inputLocalizationResources.providers | Sort-Object provider)
if ($semanticProviders.Count -ne $resourceProviders.Count) {
    throw 'Build manifest translation/resource provider counts differ.'
}
for ($index = 0; $index -lt $resourceProviders.Count; $index++) {
    if (-not $semanticProviders[$index].provider.Equals(
            $resourceProviders[$index].provider, [StringComparison]::OrdinalIgnoreCase) -or
        (@($semanticProviders[$index].languages) -join '|') -cne
            (@($resourceProviders[$index].languages) -join '|')) {
        throw "Build manifest translation/resource provider differs at index $index."
    }
}
$actualSidecars = @(Get-LocalizedSidecarInventory $PluginPath)
Assert-LocalizedSidecarShape $actualSidecars 'Package input'
Assert-LocalizedSidecarsEqual $manifestSidecars $actualSidecars 'Package input'
foreach ($sidecar in $actualSidecars) {
    if (-not (Test-PathWithin $sidecar.fullPath $artifactRoot)) {
        throw "Localized sidecar must remain below the owned artifact root: $($sidecar.fullPath)"
    }
    if ($OutputPath.Equals($sidecar.fullPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Package output must not alias a localized sidecar: $($sidecar.fullPath)"
    }
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
foreach ($sidecar in $actualSidecars) {
    $archiveInputs.Add([pscustomobject]@{
        Source = $sidecar.fullPath
        Entry = $sidecar.relativePath
    })
}

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
