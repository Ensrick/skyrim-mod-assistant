#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Instance = '',
    [string]$Profile = 'Default',
    [string]$ArtifactRoot = "$PSScriptRoot\artifacts",
    [string]$InstalledModName = 'Ensrick - Weapon Speed Balance',
    [switch]$FreshnessOnly,
    [switch]$Candidate,
    [switch]$FinalWinners,
    [switch]$AllowLiveProfileAccess,
    [string]$ClaimOwner = $env:SKYRIM_CLAIM_OWNER
)

$ErrorActionPreference = 'Stop'
$outputPlugin = 'WeaponBalancePatch.esp'

function Find-WorkspacePath {
    param([string]$RelativePath, [ValidateSet('Leaf', 'Container')][string]$PathType)
    $cursor = [System.IO.DirectoryInfo]::new((Resolve-Path -LiteralPath $PSScriptRoot).Path)
    while ($null -ne $cursor) {
        $candidate = Join-Path $cursor.FullName $RelativePath
        if (Test-Path -LiteralPath $candidate -PathType $PathType) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
        $cursor = $cursor.Parent
    }
    throw "Could not locate workspace-relative path: $RelativePath"
}

function Get-GameRoot([string]$IniPath) {
    $line = Get-Content -LiteralPath $IniPath |
        Where-Object { $_ -match '^gamePath=' } | Select-Object -First 1
    if (-not $line) { throw "ModOrganizer.ini has no gamePath entry: $IniPath" }
    $serialized = $line.Substring('gamePath='.Length)
    if ($serialized -match '^@ByteArray\((?<path>.*)\)$') {
        $root = $Matches.path.Replace('\\', '\')
    } else {
        $root = [System.Text.Encoding]::UTF8.GetString(
            [System.Convert]::FromBase64String($serialized))
    }
    if (-not [System.IO.Path]::IsPathFullyQualified($root)) {
        throw "Decoded gamePath is not absolute: $root"
    }
    return $root
}

function Get-NormalizedLoadOrder {
    param([string]$PluginsFile, [string]$CreationClubFile, [bool]$IncludeOutput)
    $ordered = [System.Collections.Generic.List[string]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase)
    foreach ($name in @('Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm')) {
        if ($seen.Add($name)) { $ordered.Add("*$name") }
    }
    if (Test-Path -LiteralPath $CreationClubFile -PathType Leaf) {
        foreach ($line in Get-Content -LiteralPath $CreationClubFile) {
            $name = $line.Trim().TrimStart('*')
            if ($name -and $seen.Add($name)) { $ordered.Add("*$name") }
        }
    }
    foreach ($line in Get-Content -LiteralPath $PluginsFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed.StartsWith('*')) { continue }
        $name = $trimmed.TrimStart('*')
        if (-not $IncludeOutput -and
            $name.Equals($outputPlugin, [StringComparison]::OrdinalIgnoreCase)) { continue }
        if ($seen.Add($name)) { $ordered.Add("*$name") }
    }
    return $ordered.ToArray()
}

function Get-BytesSha256([byte[]]$Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

function Get-NormalizedDigest([string[]]$Lines) {
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Lines -join "`n") + "`n")
    return Get-BytesSha256 $bytes
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Test-PathWithin([string]$Path, [string]$Root) {
    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    return $fullPath.Equals($fullRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $fullPath.StartsWith($fullRoot + '\', [StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoReparseTraversal([string]$Path, [string]$Boundary) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullBoundary = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
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

function Get-InventoryDigest($Inventory) {
    $content = (($Inventory | ForEach-Object {
        "$($_.plugin)|$($_.provider)|$($_.sha256)"
    }) -join "`n") + "`n"
    return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($content))
}

function Get-PluginInventory([string[]]$Lines) {
    $modlistFile = Join-Path $profileFolder 'modlist.txt'
    if (-not (Test-Path -LiteralPath $modlistFile -PathType Leaf)) {
        throw "MO2 profile modlist is absent: $modlistFile"
    }
    # MO2 writes highest-priority enabled mods first. Overwrite wins above them.
    $enabledMods = @(Get-Content -LiteralPath $modlistFile |
        ForEach-Object { $_.Trim() } | Where-Object { $_.StartsWith('+') } |
        ForEach-Object { $_.Substring(1) })
    $inventory = foreach ($line in $Lines) {
        $pluginName = $line.TrimStart('*')
        $winner = $null
        $provider = $null
        $overwriteCandidate = Join-Path (Join-Path $Instance 'overwrite') $pluginName
        if (Test-Path -LiteralPath $overwriteCandidate -PathType Leaf) {
            $winner = $overwriteCandidate
            $provider = 'overwrite'
        }
        if (-not $winner) {
            foreach ($modName in $enabledMods) {
                $candidate = Join-Path (Join-Path (Join-Path $Instance 'mods') $modName) $pluginName
                if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                    $winner = $candidate
                    $provider = "mod:$modName"
                    break
                }
            }
        }
        if (-not $winner) {
            $candidate = Join-Path $dataFolder $pluginName
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $winner = $candidate
                $provider = 'game-data'
            }
        }
        if (-not $winner) { throw "Could not resolve enabled plugin binary: $pluginName" }
        [ordered]@{
            plugin = $pluginName
            provider = $provider
            sha256 = Get-FileSha256 $winner
        }
    }
    return @($inventory)
}

function Get-SourceFingerprint {
    $paths = @(
        'generate.ps1', 'audit.ps1', 'package.ps1', 'global.json',
        'README.md', 'DECISIONS.md',
        'src\WeaponBalancePatcher\WeaponBalancePatcher.csproj',
        'src\WeaponBalancePatcher\packages.lock.json',
        'src\WeaponBalancePatcher\settings.json',
        'tests\WeaponBalancePatcher.Tests\WeaponBalancePatcher.Tests.csproj',
        'tests\WeaponBalancePatcher.Tests\packages.lock.json'
    )
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'src\WeaponBalancePatcher') `
        -Filter '*.cs' -File | ForEach-Object {
            [IO.Path]::GetRelativePath($PSScriptRoot, $_.FullName)
        })
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'tests\WeaponBalancePatcher.Tests') `
        -Filter '*.cs' -File | ForEach-Object {
            [IO.Path]::GetRelativePath($PSScriptRoot, $_.FullName)
        })
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'tests') `
        -Filter '*.ps1' -File | ForEach-Object {
            [IO.Path]::GetRelativePath($PSScriptRoot, $_.FullName)
        })
    $files = @($paths | Sort-Object -Unique | ForEach-Object {
        $relative = $_.Replace('\', '/')
        $full = Join-Path $PSScriptRoot $_
        [ordered]@{ path = $relative; sha256 = Get-FileSha256 $full }
    })
    return [ordered]@{
        files = $files
        sha256 = Get-InventoryDigest @($files | ForEach-Object {
            [pscustomobject]@{ plugin = $_.path; provider = 'source'; sha256 = $_.sha256 }
        })
    }
}

function ConvertTo-Win32CommandLineArgument([AllowEmptyString()][string]$Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $quoted = [Text.StringBuilder]::new(); [void]$quoted.Append('"'); $slashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $slashes++; continue }
        if ($character -eq '"') {
            [void]$quoted.Append(('\' * (($slashes * 2) + 1))); [void]$quoted.Append('"')
        } else {
            [void]$quoted.Append(('\' * $slashes)); [void]$quoted.Append($character)
        }
        $slashes = 0
    }
    [void]$quoted.Append(('\' * ($slashes * 2))); [void]$quoted.Append('"')
    return $quoted.ToString()
}

function Assert-LiveInstanceClaim {
    if ([string]::IsNullOrWhiteSpace($ClaimOwner)) {
        throw 'VFS audit requires -ClaimOwner or SKYRIM_CLAIM_OWNER.'
    }
    $claimPath = Join-Path $Instance '.assistant-claim.json'
    if (-not (Test-Path -LiteralPath $claimPath -PathType Leaf)) {
        throw "Live MO2 instance has no active work claim: $claimPath"
    }
    try { $claim = Get-Content -Raw -LiteralPath $claimPath | ConvertFrom-Json }
    catch { throw "Live MO2 instance claim is unreadable: $($_.Exception.Message)" }
    if ($claim.owner -ne $ClaimOwner) {
        throw "Live MO2 instance claim belongs to '$($claim.owner)', not '$ClaimOwner'."
    }
    $expires = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse([string]$claim.expiresAt, [ref]$expires) -or
        $expires -le [DateTimeOffset]::Now.AddMinutes(12)) {
        throw "Live MO2 instance claim for '$ClaimOwner' expires too soon ($($claim.expiresAt)); renew it."
    }
    if ($claim.pidBound) {
        $claimPid = 0
        if (-not [int]::TryParse([string]$claim.pid, [ref]$claimPid) -or $claimPid -le 0) {
            throw "Live MO2 instance claim has an invalid bound PID '$($claim.pid)'."
        }
        if (-not (Get-Process -Id $claimPid -ErrorAction SilentlyContinue)) {
            throw "Live MO2 instance claim is bound to dead PID $claimPid."
        }
    }
}

function Assert-AuditSnapshotUnchanged {
    $lines = Get-NormalizedLoadOrder $pluginsFile $creationClubFile $script:auditIncludesOutput
    if ((Get-NormalizedDigest $lines) -ne $script:auditOrderDigest -or
        (Get-InventoryDigest (Get-PluginInventory $lines)) -ne $script:auditInventoryDigest) {
        throw 'Live plugin order/bytes/winning providers changed during VFS audit; discard its result.'
    }
}

function Invoke-VfsAudit([string[]]$Arguments) {
    if (-not $AllowLiveProfileAccess) {
        throw 'VFS audit requires explicit -AllowLiveProfileAccess and the live-instance claim.'
    }
    Assert-LiveInstanceClaim
    Assert-AuditSnapshotUnchanged
    $child = ($Arguments | ForEach-Object {
        ConvertTo-Win32CommandLineArgument ([string]$_)
    }) -join ' '
    $result = & $mo2 --root $Instance --profile $Profile --timeout 600 run $patcher `
        --arguments $child --cwd $patcherFolder 2>&1
    $result | Write-Output
    if ($LASTEXITCODE -ne 0) { throw "VFS audit failed with exit code $LASTEXITCODE." }
    Assert-LiveInstanceClaim
    Assert-AuditSnapshotUnchanged
}

if (-not ($FreshnessOnly -or $Candidate -or $FinalWinners)) {
    $FreshnessOnly = $true
}
if (@($FreshnessOnly, $Candidate, $FinalWinners).Where({ $_ }).Count -ne 1) {
    throw 'Choose exactly one of -FreshnessOnly, -Candidate, or -FinalWinners.'
}
if (-not $Instance) { $Instance = Find-WorkspacePath 'mo2-instances\skyrim-se' 'Container' }
$Instance = (Resolve-Path -LiteralPath $Instance).Path
$ArtifactRoot = [IO.Path]::GetFullPath($ArtifactRoot)
$profileFolder = Join-Path (Join-Path $Instance 'profiles') $Profile
$pluginsFile = Join-Path $profileFolder 'plugins.txt'
$ini = Join-Path $Instance 'ModOrganizer.ini'
$gameRoot = Get-GameRoot $ini
$creationClubFile = Join-Path $gameRoot 'Skyrim.ccc'
$dataFolder = Join-Path $gameRoot 'Data'
$pluginPath = Join-Path $ArtifactRoot $outputPlugin
$directManifestPath = Join-Path $ArtifactRoot 'build-manifest.json'
$packagedMetadataRoot = Join-Path $ArtifactRoot 'EnsrickMetadata'
$packagedManifestPath = Join-Path $packagedMetadataRoot 'build-manifest.json'
$metadataRoot = $ArtifactRoot
if ($FreshnessOnly) {
    $hasDirectManifest = Test-Path -LiteralPath $directManifestPath -PathType Leaf
    $hasPackagedManifest = Test-Path -LiteralPath $packagedManifestPath -PathType Leaf
    if ($hasDirectManifest -and $hasPackagedManifest) {
        throw 'Artifact root has both developer and packaged manifests; layout is ambiguous.'
    }
    if ($hasPackagedManifest) { $metadataRoot = $packagedMetadataRoot }
}
$reportPath = Join-Path $metadataRoot 'selection-report.json'
$manifestPath = Join-Path $metadataRoot 'build-manifest.json'
$settingsSource = Join-Path $PSScriptRoot 'src\WeaponBalancePatcher\settings.json'
$patcherFolder = Join-Path $PSScriptRoot 'src\WeaponBalancePatcher\bin\Release\net9.0'
$patcher = Join-Path $patcherFolder 'WeaponBalancePatcher.exe'
$mo2 = Join-Path $Instance 'MO2Headless.exe'

foreach ($required in @($pluginsFile, $ini, $pluginPath, $reportPath, $manifestPath, $settingsSource)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file does not exist: $required"
    }
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$inputLines = Get-NormalizedLoadOrder $pluginsFile $creationClubFile $false
$currentInputHash = Get-NormalizedDigest $inputLines

if ($FreshnessOnly) {
    $failures = [Collections.Generic.List[string]]::new()
    if ($manifest.inputLoadOrderEntries -ne $inputLines.Count) {
        $failures.Add("input count $($inputLines.Count) != manifest $($manifest.inputLoadOrderEntries)")
    }
    if ($manifest.inputLoadOrderSha256 -ne $currentInputHash) {
        $failures.Add("input order/hash differs")
    }
    $currentInventory = Get-PluginInventory $inputLines
    if ($manifest.inputPluginBinariesSha256 -ne (Get-InventoryDigest $currentInventory)) {
        $failures.Add("input plugin bytes or winning providers differ")
    }
    $manifestInventory = @($manifest.inputPluginBinaries)
    if ($manifestInventory.Count -ne $currentInventory.Count) {
        $failures.Add("input plugin binary inventory count differs")
    } else {
        for ($index = 0; $index -lt $currentInventory.Count; $index++) {
            $expected = $manifestInventory[$index]
            $actual = $currentInventory[$index]
            if (-not $expected.plugin.Equals($actual.plugin, [StringComparison]::OrdinalIgnoreCase) -or
                $expected.provider -ne $actual.provider -or $expected.sha256 -ne $actual.sha256) {
                $failures.Add("input plugin winner differs at index $index ($($actual.plugin))")
                break
            }
        }
    }
    $currentSource = Get-SourceFingerprint
    if ($manifest.sourceFingerprint.sha256 -ne $currentSource.sha256) {
        $failures.Add("generator/policy/test source fingerprint differs")
    }
    if ($manifest.settingsSha256 -ne (Get-FileSha256 $settingsSource)) {
        $failures.Add("settings hash differs")
    }
    if ($manifest.selectionReportSha256 -ne (Get-FileSha256 $reportPath)) {
        $failures.Add("selection-report hash differs")
    }
    if ($manifest.pluginSha256 -ne (Get-FileSha256 $pluginPath)) {
        $failures.Add("candidate plugin hash differs")
    }

    $activeProfilePlugins = @(Get-Content -LiteralPath $pluginsFile |
        ForEach-Object { $_.Trim() } | Where-Object { $_.StartsWith('*') } |
        ForEach-Object { $_.TrimStart('*') })
    $outputOccurrences = @($activeProfilePlugins | Where-Object {
        $_.Equals($outputPlugin, [StringComparison]::OrdinalIgnoreCase)
    })
    if ($outputOccurrences.Count -ne 1 -or
        -not $activeProfilePlugins[-1].Equals($outputPlugin, [StringComparison]::OrdinalIgnoreCase)) {
        $failures.Add("output plugin is not the unique final active profile plugin")
    }
    $outputInventory = @(Get-PluginInventory @("*$outputPlugin"))
    if ($outputInventory.Count -ne 1 -or
        $outputInventory[0].provider -ne "mod:$InstalledModName") {
        $failures.Add("actual output file winner is not mod:$InstalledModName")
    } elseif ($manifest.pluginSha256 -ne $outputInventory[0].sha256) {
        $failures.Add("actual installed output winner hash differs from candidate")
    }
    $finalReceipt = Join-Path $metadataRoot 'final-winner-audit.json'
    if ($manifest.finalWinningSpeedGate -ne 'pass' -or
        -not (Test-Path -LiteralPath $finalReceipt -PathType Leaf)) {
        $failures.Add("final-winning-speed receipt is absent or pending")
    } elseif ($manifest.finalWinnerAuditSha256 -ne (Get-FileSha256 $finalReceipt)) {
        $failures.Add("final-winning-speed receipt hash differs")
    }
    if ($failures.Count -gt 0) {
        throw "Weapon balance artifact is stale: $($failures -join '; ')."
    }
    [ordered]@{
        status = 'pass'
        mode = 'freshness-only'
        inputLoadOrderEntries = $inputLines.Count
        inputLoadOrderSha256 = $currentInputHash
        outputPluginLast = $true
        installedArtifactMatches = $true
        inputPluginBinariesMatch = $true
        sourceFingerprintMatches = $true
        finalWinningSpeedReceiptMatches = $true
        vfsUsed = $false
        filesWritten = 0
    } | ConvertTo-Json
    exit 0
}

if (-not $AllowLiveProfileAccess) {
    throw 'VFS audit requires explicit -AllowLiveProfileAccess and the live-instance claim.'
}
Assert-LiveInstanceClaim
foreach ($required in @($patcher, $mo2)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required VFS audit tool does not exist: $required"
    }
}

$ownedArtifactRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'artifacts'))
if (-not $ArtifactRoot.Equals($ownedArtifactRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Candidate/final audit artifacts must use the owned root: $ownedArtifactRoot"
}
$workFolder = Join-Path $PSScriptRoot 'work'
Assert-NoReparseTraversal $workFolder $PSScriptRoot
Assert-NoReparseTraversal $ArtifactRoot $PSScriptRoot

if ($Candidate) {
    $auditIncludesOutput = $false
    $auditLines = $inputLines
    $loadOrderAuditPath = Join-Path $workFolder 'plugins-input.txt'
} else {
    $auditIncludesOutput = $true
    $auditLines = Get-NormalizedLoadOrder $pluginsFile $creationClubFile $true
    $loadOrderAuditPath = Join-Path $workFolder 'plugins-final.txt'
}
$finalReceiptPath = Join-Path $ArtifactRoot 'final-winner-audit.json'
$temporaryFinalReceiptPath = Join-Path $workFolder 'final-winner-audit.candidate.json'
Assert-NoReparseTraversal $loadOrderAuditPath $PSScriptRoot
if ($FinalWinners) {
    foreach ($writeTarget in @(
        $temporaryFinalReceiptPath, $finalReceiptPath, $manifestPath)) {
        Assert-NoReparseTraversal $writeTarget $PSScriptRoot
    }
    if (Test-Path -LiteralPath $finalReceiptPath -PathType Container) {
        throw "Final-winner receipt path is a directory: $finalReceiptPath"
    }
}
$auditOrderDigest = Get-NormalizedDigest $auditLines
$auditInventoryDigest = Get-InventoryDigest (Get-PluginInventory $auditLines)
$manifestInitialHash = Get-FileSha256 $manifestPath
Assert-LiveInstanceClaim
Assert-AuditSnapshotUnchanged

# The claim and the full order/provider/byte snapshot are established before
# any work file is created.
Assert-NoReparseTraversal $workFolder $PSScriptRoot
New-Item -ItemType Directory -Force -Path $workFolder | Out-Null
Assert-NoReparseTraversal $loadOrderAuditPath $PSScriptRoot
[IO.File]::WriteAllText(
    $loadOrderAuditPath,
    ($auditLines -join "`n") + "`n",
    [Text.UTF8Encoding]::new($false))

if ($Candidate) {
    Invoke-VfsAudit @(
        'audit-build', $dataFolder, $loadOrderAuditPath, $pluginPath,
        $settingsSource, $reportPath, '-'
    )
    exit 0
}

Assert-NoReparseTraversal $temporaryFinalReceiptPath $PSScriptRoot
Invoke-VfsAudit @(
    'audit-final-winners', $dataFolder, $loadOrderAuditPath, $settingsSource,
    $reportPath, $temporaryFinalReceiptPath
)
if (-not (Test-Path -LiteralPath $temporaryFinalReceiptPath -PathType Leaf)) {
    throw 'Final-winner audit succeeded without producing its temporary receipt.'
}
Assert-LiveInstanceClaim
Assert-AuditSnapshotUnchanged
if ((Get-FileSha256 $manifestPath) -ne $manifestInitialHash) {
    throw 'Build manifest changed during final-winner audit; discard the result.'
}
Assert-NoReparseTraversal $finalReceiptPath $PSScriptRoot
[IO.File]::WriteAllBytes(
    $finalReceiptPath,
    [IO.File]::ReadAllBytes($temporaryFinalReceiptPath))
$manifest.finalWinningSpeedGate = 'pass'
$manifest | Add-Member -NotePropertyName finalWinnerAuditSha256 `
    -NotePropertyValue (Get-FileSha256 $finalReceiptPath) -Force
Assert-NoReparseTraversal $manifestPath $PSScriptRoot
[IO.File]::WriteAllText(
    $manifestPath, ($manifest | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Write-Host "PASS: final-winner audit recorded; rerun -FreshnessOnly for the no-write gate."
