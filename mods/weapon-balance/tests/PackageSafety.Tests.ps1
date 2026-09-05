#requires -Version 7.0
$ErrorActionPreference = 'Stop'

function Invoke-Packager([string[]]$Arguments) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = (Get-Command pwsh).Source
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in @('-NoLogo', '-NoProfile', '-NonInteractive', '-File', $packager) + $Arguments) {
        [void]$start.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::Start($start)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        Output = $stdout + $stderr
    }
}

function Sha([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function SidecarDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object relativePath | ForEach-Object {
        "$($_.relativePath)|$($_.language)|$($_.source)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
}

function PhysicalResourceDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object provider, kind, relativePath | ForEach-Object {
        "$($_.provider)|$($_.kind)|$($_.relativePath)|$($_.winningProvider)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
}

function ResourceContractDigest($Contract) {
    $node = [System.Text.Json.Nodes.JsonNode]::Parse(
        ($Contract | ConvertTo-Json -Depth 20 -Compress))
    [void]$node.AsObject().Remove('sha256')
    $options = [System.Text.Json.JsonSerializerOptions]::new()
    $options.PropertyNamingPolicy = [System.Text.Json.JsonNamingPolicy]::CamelCase
    $options.WriteIndented = $true
    $canonical = $node.ToJsonString($options)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($canonical)))
}

function Assert-CleanupTarget([string]$Path, [string]$Boundary, [string]$Prefix) {
    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $fullBoundary = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $fullPath.StartsWith($fullBoundary + '\', [StringComparison]::OrdinalIgnoreCase) -or
        -not [IO.Path]::GetFileName($fullPath).StartsWith($Prefix, [StringComparison]::Ordinal)) {
        throw "Refusing cleanup outside the exact generated fixture root: $fullPath"
    }
    return $fullPath
}

$moduleRoot = Split-Path -Parent $PSScriptRoot
$packager = Join-Path $moduleRoot 'package.ps1'
$fixtureBoundary = [IO.Path]::GetFullPath((Join-Path $moduleRoot 'artifacts'))
$fixtureRoot = [IO.Path]::GetFullPath((Join-Path $fixtureBoundary (
    '_package-safety-' + [guid]::NewGuid())))
try {
    New-Item -ItemType Directory -Path $fixtureRoot | Out-Null
    $plugin = Join-Path $fixtureRoot 'WeaponBalancePatch.esp'
    $report = Join-Path $fixtureRoot 'selection-report.json'
    $manifest = Join-Path $fixtureRoot 'build-manifest.json'
    $finalReceipt = Join-Path $fixtureRoot 'final-winner-audit.json'
    $archive = Join-Path $fixtureRoot 'candidate.zip'
    $stringsRoot = Join-Path $fixtureRoot 'Strings'
    New-Item -ItemType Directory -Path $stringsRoot | Out-Null
    [IO.File]::WriteAllText($plugin, 'fixture-plugin')
    [IO.File]::WriteAllText($report, '{"fixture":true}')
    $sidecars = @(
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_English.DLSTRINGS'; language = 'English'; source = 'DL' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_English.ILSTRINGS'; language = 'English'; source = 'IL' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_English.STRINGS'; language = 'English'; source = 'Normal' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_Spanish_Mexico.DLSTRINGS'; language = 'Spanish_Mexico'; source = 'DL' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_Spanish_Mexico.ILSTRINGS'; language = 'Spanish_Mexico'; source = 'IL' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_Spanish_Mexico.STRINGS'; language = 'Spanish_Mexico'; source = 'Normal' }
    )
    foreach ($sidecar in $sidecars) {
        $sidecarPath = Join-Path $fixtureRoot $sidecar.relativePath
        [IO.File]::WriteAllText($sidecarPath, "fixture-$($sidecar.source)")
        $sidecar.bytes = (Get-Item -LiteralPath $sidecarPath).Length
        $sidecar.sha256 = Sha $sidecarPath
    }
    $resourceContract = [ordered]@{
        schemaVersion = 1
        providers = @()
        looseFiles = @()
        archives = @()
        resolutions = @()
    }
    $resourceContract.sha256 = ResourceContractDigest $resourceContract
    $physicalResources = @()
    $manifestValue = [ordered]@{
        schemaVersion = 3
        generatorVersion = '0.3.0'
        outputPlugin = 'WeaponBalancePatch.esp'
        pluginSha256 = Sha $plugin
        selectionReportSha256 = Sha $report
        localized = $true
        translationLanguages = @('English', 'Spanish_Mexico')
        localizedSidecars = $sidecars
        localizedSidecarsSha256 = SidecarDigest $sidecars
        inputTranslationSemantics = [ordered]@{
            schemaVersion = 1
            records = 0
            fields = 0
            values = 0
            languages = @()
            providers = @()
            sha256 = ('A' * 64)
        }
        inputLocalizationResources = $resourceContract
        inputLocalizationResourceProviders = $physicalResources
        inputLocalizationResourceProvidersSha256 = PhysicalResourceDigest $physicalResources
        eslFlagged = $true
        ownLightFormCount = 0
        onlySpeedSemanticComparison = $true
        deterministicDoubleBuild = $true
        finalWinningSpeedGate = 'pending installation at final plugin priority'
    }
    [IO.File]::WriteAllText($manifest, ($manifestValue | ConvertTo-Json -Depth 5))

    $common = @(
        '-PluginPath', $plugin, '-SelectionReportPath', $report,
        '-BuildManifestPath', $manifest, '-FinalWinnerAuditPath', $finalReceipt)
    $result = Invoke-Packager ($common + @(
        '-OutputPath', $archive, '-AllowPendingFinalAudit'))
    if ($result.ExitCode -ne 0) {
        throw "Candidate package fixture failed: $($result.Output)"
    }
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        $entries = @($zip.Entries | ForEach-Object FullName | Sort-Object)
    } finally {
        $zip.Dispose()
    }
    $expected = @(
        'EnsrickMetadata/build-manifest.json',
        'EnsrickMetadata/selection-report.json',
        'Strings/WeaponBalancePatch_English.DLSTRINGS',
        'Strings/WeaponBalancePatch_English.ILSTRINGS',
        'Strings/WeaponBalancePatch_English.STRINGS',
        'Strings/WeaponBalancePatch_Spanish_Mexico.DLSTRINGS',
        'Strings/WeaponBalancePatch_Spanish_Mexico.ILSTRINGS',
        'Strings/WeaponBalancePatch_Spanish_Mexico.STRINGS',
        'WeaponBalancePatch.esp')
    if (($entries -join '|') -cne ($expected -join '|')) {
        throw "Candidate package entries differ: $($entries -join ', ')"
    }

    $archiveHash = Sha $archive
    $existing = Invoke-Packager ($common + @(
        '-OutputPath', $archive, '-AllowPendingFinalAudit'))
    if ($existing.ExitCode -eq 0 -or $existing.Output -notmatch 'already exists' -or
        (Sha $archive) -ne $archiveHash) {
        throw 'Packager did not fail closed on an existing archive.'
    }

    $tamperedSidecar = Join-Path $stringsRoot 'WeaponBalancePatch_English.STRINGS'
    [IO.File]::WriteAllText($tamperedSidecar, 'tampered')
    $tamperedArchive = Join-Path $fixtureRoot 'tampered.zip'
    $tampered = Invoke-Packager ($common + @(
        '-OutputPath', $tamperedArchive, '-AllowPendingFinalAudit'))
    if ($tampered.ExitCode -eq 0 -or $tampered.Output -notmatch 'localized sidecar differs' -or
        (Test-Path -LiteralPath $tamperedArchive)) {
        throw 'Packager did not reject a tampered localized sidecar before archive creation.'
    }
    [IO.File]::WriteAllText($tamperedSidecar, 'fixture-Normal')

    $manifestHash = Sha $manifest
    $alias = Invoke-Packager ($common + @(
        '-OutputPath', $manifest, '-AllowPendingFinalAudit', '-ReplaceExistingArchive'))
    if ($alias.ExitCode -eq 0 -or $alias.Output -notmatch 'must not alias' -or
        (Sha $manifest) -ne $manifestHash) {
        throw 'Packager did not reject an output/input alias before replacement.'
    }

    Write-Host 'PASS: candidate archive includes exact localized sidecars and package writes fail closed.'
} finally {
    if (Test-Path -LiteralPath $fixtureRoot) {
        $cleanupRoot = Assert-CleanupTarget $fixtureRoot $fixtureBoundary '_package-safety-'
        [IO.Directory]::Delete($cleanupRoot, $true)
    }
}
