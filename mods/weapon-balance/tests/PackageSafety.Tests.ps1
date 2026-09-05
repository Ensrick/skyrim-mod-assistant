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

$moduleRoot = Split-Path -Parent $PSScriptRoot
$packager = Join-Path $moduleRoot 'package.ps1'
$fixtureRoot = Join-Path (Join-Path $moduleRoot 'artifacts') (
    '_package-safety-' + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $fixtureRoot | Out-Null
    $plugin = Join-Path $fixtureRoot 'WeaponBalancePatch.esp'
    $report = Join-Path $fixtureRoot 'selection-report.json'
    $manifest = Join-Path $fixtureRoot 'build-manifest.json'
    $finalReceipt = Join-Path $fixtureRoot 'final-winner-audit.json'
    $archive = Join-Path $fixtureRoot 'candidate.zip'
    [IO.File]::WriteAllText($plugin, 'fixture-plugin')
    [IO.File]::WriteAllText($report, '{"fixture":true}')
    $manifestValue = [ordered]@{
        schemaVersion = 2
        generatorVersion = '0.2.0'
        outputPlugin = 'WeaponBalancePatch.esp'
        pluginSha256 = Sha $plugin
        selectionReportSha256 = Sha $report
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

    $manifestHash = Sha $manifest
    $alias = Invoke-Packager ($common + @(
        '-OutputPath', $manifest, '-AllowPendingFinalAudit', '-ReplaceExistingArchive'))
    if ($alias.ExitCode -eq 0 -or $alias.Output -notmatch 'must not alias' -or
        (Sha $manifest) -ne $manifestHash) {
        throw 'Packager did not reject an output/input alias before replacement.'
    }

    Write-Host 'PASS: candidate archive contains its metadata and package writes fail closed.'
} finally {
    if (Test-Path -LiteralPath $fixtureRoot) {
        [IO.Directory]::Delete([IO.Path]::GetFullPath($fixtureRoot), $true)
    }
}
