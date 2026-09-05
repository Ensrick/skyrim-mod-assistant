#requires -Version 7.0
$ErrorActionPreference = 'Stop'

function Invoke-Generator([string[]]$Arguments) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = (Get-Command pwsh).Source
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in @('-NoLogo', '-NoProfile', '-NonInteractive', '-File', $generator) + $Arguments) {
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
$generator = Join-Path $moduleRoot 'generate.ps1'
$artifactRoot = [IO.Path]::GetFullPath((Join-Path $moduleRoot 'artifacts'))
$tempBoundary = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$ownedTestRoot = [IO.Path]::GetFullPath((Join-Path $artifactRoot (
    "_generation-safety-" + [guid]::NewGuid())))
$externalTestRoot = [IO.Path]::GetFullPath((Join-Path $tempBoundary (
    "weapon-balance-safety-" + [guid]::NewGuid())))
try {
    $offlineData = Join-Path $externalTestRoot 'offline-data'
    New-Item -ItemType Directory -Force -Path $ownedTestRoot, $offlineData | Out-Null

    # Regression: validation must reject an input/output alias before the
    # replacement switch can delete the input file.
    $aliasPath = Join-Path $ownedTestRoot 'WeaponBalancePatch.esp'
    [IO.File]::WriteAllText($aliasPath, "*Skyrim.esm`n", [Text.UTF8Encoding]::new($false))
    $aliasHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $aliasPath).Hash
    $aliasResult = Invoke-Generator @(
        '-ExecutionMode', 'Offline', '-DataFolder', $offlineData,
        '-LoadOrderFile', $aliasPath, '-OutputPath', $aliasPath,
        '-SelectionReportPath', (Join-Path $ownedTestRoot 'selection-report.json'),
        '-BuildManifestPath', (Join-Path $ownedTestRoot 'build-manifest.json'),
        '-ReplaceExistingArtifacts')
    if ($aliasResult.ExitCode -eq 0 -or $aliasResult.Output -notmatch 'aliases the offline load-order input') {
        throw "Generator did not reject the input/output alias: $($aliasResult.Output)"
    }
    if (-not (Test-Path -LiteralPath $aliasPath -PathType Leaf) -or
        (Get-FileHash -Algorithm SHA256 -LiteralPath $aliasPath).Hash -ne $aliasHash) {
        throw 'Generator changed/deleted the aliased load-order input before rejecting it.'
    }

    # Regression: lexical containment is not enough when a child directory is
    # a junction to a location outside the owned artifact tree.
    $junctionTarget = Join-Path $externalTestRoot 'junction-target'
    $junctionPath = Join-Path $ownedTestRoot 'redirect'
    New-Item -ItemType Directory -Path $junctionTarget | Out-Null
    New-Item -ItemType Junction -Path $junctionPath -Target $junctionTarget | Out-Null
    $loadOrder = Join-Path $externalTestRoot 'plugins.txt'
    [IO.File]::WriteAllText($loadOrder, "*Skyrim.esm`n", [Text.UTF8Encoding]::new($false))
    $junctionResult = Invoke-Generator @(
        '-ExecutionMode', 'Offline', '-DataFolder', $offlineData,
        '-LoadOrderFile', $loadOrder,
        '-OutputPath', (Join-Path $junctionPath 'WeaponBalancePatch.esp'),
        '-SelectionReportPath', (Join-Path $ownedTestRoot 'junction-report.json'),
        '-BuildManifestPath', (Join-Path $ownedTestRoot 'junction-manifest.json'))
    if ($junctionResult.ExitCode -eq 0 -or $junctionResult.Output -notmatch 'reparse point') {
        throw "Generator did not reject reparse traversal: $($junctionResult.Output)"
    }
    if (Test-Path -LiteralPath (Join-Path $junctionTarget 'WeaponBalancePatch.esp')) {
        throw 'Generator wrote through the rejected junction.'
    }

    # Regression: live mode requires a matching, sufficiently long-lived real
    # claim before it creates any candidate artifact.
    $instance = Join-Path $externalTestRoot 'instance'
    $profile = Join-Path $instance 'profiles\Default'
    $gameData = Join-Path $externalTestRoot 'game\Data'
    New-Item -ItemType Directory -Force -Path $profile, $gameData | Out-Null
    [IO.File]::WriteAllText((Join-Path $instance 'MO2Headless.exe'), 'fixture')
    [IO.File]::WriteAllText((Join-Path $profile 'plugins.txt'), '')
    [IO.File]::WriteAllText((Join-Path $profile 'modlist.txt'), '')
    [IO.File]::WriteAllText((Join-Path $instance 'ModOrganizer.ini'),
        'gamePath=' + [Convert]::ToBase64String(
            [Text.Encoding]::UTF8.GetBytes((Split-Path -Parent $gameData))))
    $claimOutput = Join-Path $ownedTestRoot 'claim\WeaponBalancePatch.esp'
    $claimResult = Invoke-Generator @(
        '-ExecutionMode', 'MO2Vfs', '-AllowLiveProfileAccess',
        '-ClaimOwner', 'fixture-owner', '-Instance', $instance, '-Profile', 'Default',
        '-OutputPath', $claimOutput,
        '-SelectionReportPath', (Join-Path $ownedTestRoot 'claim\selection-report.json'),
        '-BuildManifestPath', (Join-Path $ownedTestRoot 'claim\build-manifest.json'))
    if ($claimResult.ExitCode -eq 0 -or $claimResult.Output -notmatch 'no active work claim') {
        throw "Generator did not reject absent live claim: $($claimResult.Output)"
    }
    if (Test-Path -LiteralPath $claimOutput) {
        throw 'Generator created an artifact without a live-instance claim.'
    }

    Write-Host 'PASS: generator rejects aliases before deletion, reparse traversal, and unclaimed live access.'
} finally {
    if ($junctionPath -and (Test-Path -LiteralPath $junctionPath)) {
        $junctionItem = Get-Item -LiteralPath $junctionPath -Force
        if (($junctionItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) {
            throw "Safety fixture path unexpectedly stopped being a junction: $junctionPath"
        }
        [IO.Directory]::Delete([IO.Path]::GetFullPath($junctionPath), $false)
    }
    $cleanupTargets = @(
        [pscustomobject]@{ path = $ownedTestRoot; boundary = $artifactRoot; prefix = '_generation-safety-' },
        [pscustomobject]@{ path = $externalTestRoot; boundary = $tempBoundary; prefix = 'weapon-balance-safety-' })
    foreach ($cleanup in $cleanupTargets) {
        if ($cleanup.path -and (Test-Path -LiteralPath $cleanup.path)) {
            $cleanupRoot = Assert-CleanupTarget $cleanup.path $cleanup.boundary $cleanup.prefix
            [IO.Directory]::Delete($cleanupRoot, $true)
        }
    }
}
