#requires -Version 7.0
$ErrorActionPreference = 'Stop'

function Sha([string]$Path) {
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Digest([string[]]$Lines) {
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Lines -join "`n") + "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function InventoryDigest($Inventory) {
    Digest @($Inventory | ForEach-Object {
        "$($_.plugin)|$($_.provider)|$($_.sha256)"
    })
}

function SourceFingerprint([string]$Root) {
    $paths = @(
        'generate.ps1', 'audit.ps1', 'package.ps1', 'global.json',
        'README.md', 'DECISIONS.md',
        'src\WeaponBalancePatcher\WeaponBalancePatcher.csproj',
        'src\WeaponBalancePatcher\packages.lock.json',
        'src\WeaponBalancePatcher\settings.json',
        'tests\WeaponBalancePatcher.Tests\WeaponBalancePatcher.Tests.csproj',
        'tests\WeaponBalancePatcher.Tests\packages.lock.json'
    )
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $Root 'src\WeaponBalancePatcher') `
        -Filter '*.cs' -File | ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName) })
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $Root 'tests\WeaponBalancePatcher.Tests') `
        -Filter '*.cs' -File | ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName) })
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $Root 'tests') `
        -Filter '*.ps1' -File | ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName) })
    $files = @($paths | Sort-Object -Unique | ForEach-Object {
        [ordered]@{ path = $_.Replace('\', '/'); sha256 = Sha (Join-Path $Root $_) }
    })
    [ordered]@{
        files = $files
        sha256 = InventoryDigest @($files | ForEach-Object {
            [pscustomobject]@{ plugin = $_.path; provider = 'source'; sha256 = $_.sha256 }
        })
    }
}

function FileSnapshot([string]$Root) {
    @((Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName | ForEach-Object {
        "$([IO.Path]::GetRelativePath($Root, $_.FullName))|$(Sha $_.FullName)"
    })) -join "`n"
}

function Invoke-Audit([string]$AuditPath, [string]$InstancePath, [string]$ArtifactPath) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = (Get-Command pwsh).Source
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in @(
        '-NoProfile', '-File', $AuditPath, '-FreshnessOnly',
        '-Instance', $InstancePath, '-Profile', 'Default', '-ArtifactRoot', $ArtifactPath)) {
        [void]$start.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::Start($start)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    [pscustomobject]@{ ExitCode = $process.ExitCode; Stdout = $stdout; Stderr = $stderr }
}

$moduleRoot = Split-Path -Parent $PSScriptRoot
$audit = Join-Path $moduleRoot 'audit.ps1'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ("weapon-balance-freshness-" + [guid]::NewGuid())
try {
    $instance = Join-Path $testRoot 'instance'
    $profile = Join-Path $instance 'profiles\Default'
    $data = Join-Path $testRoot 'game\Data'
    $artifact = Join-Path $testRoot 'artifacts'
    $installed = Join-Path $instance 'mods\Ensrick - Weapon Speed Balance'
    foreach ($folder in @($profile, $data, $artifact, $installed, (Join-Path $instance 'overwrite'))) {
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
    }
    [IO.File]::WriteAllText((Join-Path $instance 'ModOrganizer.ini'),
        'gamePath=' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Split-Path $data))))
    [IO.File]::WriteAllText((Join-Path $profile 'plugins.txt'), "*WeaponBalancePatch.esp`n")
    [IO.File]::WriteAllText((Join-Path $profile 'modlist.txt'), "+Ensrick - Weapon Speed Balance`n")

    $baseNames = @('Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm')
    foreach ($name in $baseNames) {
        [IO.File]::WriteAllBytes((Join-Path $data $name), [Text.Encoding]::UTF8.GetBytes("fixture-$name"))
    }
    $outputBytes = [Text.Encoding]::UTF8.GetBytes('fixture-output')
    [IO.File]::WriteAllBytes((Join-Path $artifact 'WeaponBalancePatch.esp'), $outputBytes)
    [IO.File]::WriteAllBytes((Join-Path $installed 'WeaponBalancePatch.esp'), $outputBytes)
    [IO.File]::WriteAllText((Join-Path $artifact 'selection-report.json'), '{}')
    [IO.File]::WriteAllText((Join-Path $artifact 'final-winner-audit.json'), '{"status":"pass"}')

    $inputLines = @($baseNames | ForEach-Object { "*$_" })
    $inventory = @($baseNames | ForEach-Object {
        [ordered]@{ plugin = $_; provider = 'game-data'; sha256 = Sha (Join-Path $data $_) }
    })
    $source = SourceFingerprint $moduleRoot
    $manifest = [ordered]@{
        schemaVersion = 2
        outputPlugin = 'WeaponBalancePatch.esp'
        inputLoadOrderEntries = $inputLines.Count
        inputLoadOrderSha256 = Digest $inputLines
        inputPluginBinaries = $inventory
        inputPluginBinariesSha256 = InventoryDigest $inventory
        sourceFingerprint = $source
        settingsSha256 = Sha (Join-Path $moduleRoot 'src\WeaponBalancePatcher\settings.json')
        selectionReportSha256 = Sha (Join-Path $artifact 'selection-report.json')
        pluginSha256 = Sha (Join-Path $artifact 'WeaponBalancePatch.esp')
        finalWinningSpeedGate = 'pass'
        finalWinnerAuditSha256 = Sha (Join-Path $artifact 'final-winner-audit.json')
    }
    [IO.File]::WriteAllText((Join-Path $artifact 'build-manifest.json'),
        ($manifest | ConvertTo-Json -Depth 20))

    $before = FileSnapshot $testRoot
    $result = Invoke-Audit $audit $instance $artifact
    if ($result.ExitCode -ne 0) {
        throw "Freshness fixture failed: $($result.Stdout) $($result.Stderr)"
    }
    $parsed = $result.Stdout | ConvertFrom-Json
    if ($parsed.vfsUsed -ne $false -or $parsed.filesWritten -ne 0) {
        throw 'Freshness result did not declare no-VFS/no-write behavior.'
    }
    $after = FileSnapshot $testRoot
    if ($before -ne $after) { throw 'FreshnessOnly changed a fixture file.' }

    $metadata = Join-Path $artifact 'EnsrickMetadata'
    New-Item -ItemType Directory -Path $metadata | Out-Null
    foreach ($metadataName in @(
        'selection-report.json', 'build-manifest.json', 'final-winner-audit.json')) {
        Move-Item -LiteralPath (Join-Path $artifact $metadataName) `
            -Destination (Join-Path $metadata $metadataName)
    }
    $packagedBefore = FileSnapshot $testRoot
    $packagedResult = Invoke-Audit $audit $instance $artifact
    if ($packagedResult.ExitCode -ne 0) {
        throw "Packaged-layout freshness fixture failed: $($packagedResult.Stdout) $($packagedResult.Stderr)"
    }
    $packagedAfter = FileSnapshot $testRoot
    if ($packagedBefore -ne $packagedAfter) {
        throw 'FreshnessOnly changed a packaged-layout fixture file.'
    }

    [IO.File]::WriteAllText((Join-Path $data 'Update.esm'), 'changed-input')
    $stale = Invoke-Audit $audit $instance $artifact
    if ($stale.ExitCode -eq 0 -or ($stale.Stdout + $stale.Stderr) -notmatch 'input plugin') {
        throw 'Same-name input binary drift was not rejected.'
    }

    [IO.File]::WriteAllBytes((Join-Path $data 'Update.esm'),
        [Text.Encoding]::UTF8.GetBytes('fixture-Update.esm'))
    [IO.File]::WriteAllText((Join-Path $instance 'overwrite\WeaponBalancePatch.esp'), 'shadow')
    $shadow = Invoke-Audit $audit $instance $artifact
    if ($shadow.ExitCode -eq 0 -or ($shadow.Stdout + $shadow.Stderr) -notmatch 'actual output file winner') {
        throw 'Overwrite shadowing of the installed output was not rejected.'
    }

    Write-Host 'PASS: FreshnessOnly is no-VFS/no-write and rejects input-byte drift and output shadowing.'
} finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
