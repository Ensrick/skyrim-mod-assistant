#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('Offline', 'MO2Vfs')][string]$ExecutionMode = 'Offline',
    [string]$Instance = '',
    [string]$Profile = 'Default',
    [string]$DataFolder = '',
    [string]$LoadOrderFile = '',
    [string]$Configuration = 'Release',
    [string]$OutputPath = "$PSScriptRoot\artifacts\WeaponBalancePatch.esp",
    [string]$SelectionReportPath = "$PSScriptRoot\artifacts\selection-report.json",
    [string]$BuildManifestPath = "$PSScriptRoot\artifacts\build-manifest.json",
    [bool]$VerifyDeterminism = $true,
    [switch]$AllowLiveProfileAccess,
    [string]$ClaimOwner = $env:SKYRIM_CLAIM_OWNER,
    [switch]$ReplaceExistingArtifacts
)

$ErrorActionPreference = 'Stop'
$outputPlugin = 'WeaponBalancePatch.esp'

function Find-WorkspacePath {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [ValidateSet('Any', 'Leaf', 'Container')][string]$PathType = 'Any'
    )

    $cursor = [System.IO.DirectoryInfo]::new((Resolve-Path -LiteralPath $PSScriptRoot).Path)
    while ($null -ne $cursor) {
        $candidate = Join-Path $cursor.FullName $RelativePath
        $exists = switch ($PathType) {
            'Leaf' { Test-Path -LiteralPath $candidate -PathType Leaf }
            'Container' { Test-Path -LiteralPath $candidate -PathType Container }
            default { Test-Path -LiteralPath $candidate }
        }
        if ($exists) { return (Resolve-Path -LiteralPath $candidate).Path }
        $cursor = $cursor.Parent
    }
    throw "Could not locate workspace-relative path: $RelativePath"
}

function ConvertTo-Win32CommandLineArgument {
    param([AllowEmptyString()][string]$Value)

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $quoted = [System.Text.StringBuilder]::new()
    [void]$quoted.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $backslashes++; continue }
        if ($character -eq '"') {
            [void]$quoted.Append(('\' * (($backslashes * 2) + 1)))
            [void]$quoted.Append('"')
        } else {
            [void]$quoted.Append(('\' * $backslashes))
            [void]$quoted.Append($character)
        }
        $backslashes = 0
    }
    [void]$quoted.Append(('\' * ($backslashes * 2)))
    [void]$quoted.Append('"')
    return $quoted.ToString()
}

function Get-GameRoot {
    param([Parameter(Mandatory)][string]$IniPath)

    $line = Get-Content -LiteralPath $IniPath |
        Where-Object { $_ -match '^gamePath=' } | Select-Object -First 1
    if (-not $line) { throw "ModOrganizer.ini has no gamePath entry: $IniPath" }
    $serialized = $line.Substring('gamePath='.Length)
    if ($serialized -match '^@ByteArray\((?<path>.*)\)$') {
        $root = $Matches.path.Replace('\\', '\')
    } else {
        try {
            $root = [System.Text.Encoding]::UTF8.GetString(
                [System.Convert]::FromBase64String($serialized))
        } catch {
            throw "Unsupported gamePath encoding in ${IniPath}: $serialized"
        }
    }
    if (-not [System.IO.Path]::IsPathFullyQualified($root)) {
        throw "Decoded gamePath is not absolute: $root"
    }
    return $root
}

function Get-NormalizedLoadOrder {
    param(
        [Parameter(Mandatory)][string]$PluginsFile,
        [Parameter(Mandatory)][string]$CreationClubFile,
        [Parameter(Mandatory)][bool]$IncludeOutput
    )

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
            $name.Equals($outputPlugin, [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        if ($seen.Add($name)) { $ordered.Add("*$name") }
    }
    return $ordered.ToArray()
}

function Get-OfflineNormalizedLoadOrder {
    param([Parameter(Mandatory)][string]$Path)

    $rawLines = @(Get-Content -LiteralPath $Path |
        ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith('#') })
    $unstarred = @($rawLines | Where-Object { -not $_.StartsWith('*') })
    if ($unstarred.Count -gt 0) {
        throw "Offline load order must be normalized enabled-only; unstarred entries: $($unstarred -join ', ')"
    }
    $ordered = [Collections.Generic.List[string]]::new()
    $seen = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    foreach ($baseMaster in @(
        'Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm')) {
        if ($seen.Add($baseMaster)) { $ordered.Add("*$baseMaster") }
    }
    foreach ($rawLine in $rawLines) {
        $pluginName = $rawLine.TrimStart('*')
        if (-not $pluginName.Equals($outputPlugin, [StringComparison]::OrdinalIgnoreCase) -and
            $seen.Add($pluginName)) {
            $ordered.Add("*$pluginName")
        }
    }
    return $ordered.ToArray()
}

function Write-NormalizedLoadOrder {
    param([string]$Path, [string[]]$Lines)
    $content = ($Lines -join "`n") + "`n"
    [System.IO.Directory]::CreateDirectory((Split-Path -Parent $Path)) | Out-Null
    [System.IO.File]::WriteAllText($Path, $content, [System.Text.UTF8Encoding]::new($false))
}

function Invoke-Patcher {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$LogPath
    )
    if ($script:ExecutionMode -eq 'MO2Vfs') { Assert-LiveInstanceClaim }
    Assert-InputSnapshotUnchanged
    if ($script:ExecutionMode -eq 'MO2Vfs') {
        $childArguments = ($Arguments | ForEach-Object {
            ConvertTo-Win32CommandLineArgument ([string]$_)
        }) -join ' '
        $result = & $script:mo2 --root $script:Instance --profile $script:Profile --timeout 600 run `
            $Executable --arguments $childArguments --cwd $WorkingDirectory 2>&1
        Assert-LiveInstanceClaim
    } else {
        Push-Location $WorkingDirectory
        try { $result = & $Executable @Arguments 2>&1 } finally { Pop-Location }
    }
    Assert-InputSnapshotUnchanged
    $exitCode = $LASTEXITCODE
    $result | Tee-Object -FilePath $LogPath
    if ($exitCode -ne 0) {
        throw "Headless command failed with exit code $exitCode. See $LogPath"
    }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Get-NormalizedDigest([string[]]$Lines) {
    $content = (($Lines -join "`n") + "`n")
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
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

function Assert-LiveInstanceClaim {
    if ($ExecutionMode -ne 'MO2Vfs') { return }
    if ([string]::IsNullOrWhiteSpace($ClaimOwner)) {
        throw 'MO2Vfs generation requires -ClaimOwner or SKYRIM_CLAIM_OWNER.'
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

function Get-InventoryDigest($Inventory) {
    $content = (($Inventory | ForEach-Object {
        "$($_.plugin)|$($_.provider)|$($_.sha256)"
    }) -join "`n") + "`n"
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($content)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function Get-PluginInventory([string[]]$Lines) {
    $enabledMods = @()
    if ($ExecutionMode -eq 'MO2Vfs') {
        $modlistFile = Join-Path $profileFolder 'modlist.txt'
        if (-not (Test-Path -LiteralPath $modlistFile -PathType Leaf)) {
            throw "MO2 profile modlist is absent: $modlistFile"
        }
        $enabledMods = @(Get-Content -LiteralPath $modlistFile |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_.StartsWith('+') } |
            ForEach-Object { $_.Substring(1) })
    }
    $inventory = foreach ($line in $Lines) {
        $pluginName = $line.TrimStart('*')
        $winner = $null
        $provider = $null
        if ($ExecutionMode -eq 'MO2Vfs') {
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
        }
        if (-not $winner) {
            $candidate = Join-Path $DataFolder $pluginName
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $winner = $candidate
                $provider = if ($ExecutionMode -eq 'MO2Vfs') { 'game-data' } else { 'offline-data' }
            }
        }
        if (-not $winner) { throw "Could not resolve enabled plugin binary: $pluginName" }
        [ordered]@{
            plugin = $pluginName
            provider = $provider
            sha256 = Get-Sha256 $winner
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
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
            throw "Source fingerprint file is absent: $relative"
        }
        [ordered]@{ path = $relative; sha256 = Get-Sha256 $full }
    })
    return [ordered]@{
        files = $files
        sha256 = Get-InventoryDigest @($files | ForEach-Object {
            [pscustomobject]@{ plugin = $_.path; provider = 'source'; sha256 = $_.sha256 }
        })
    }
}

function Assert-InputSnapshotUnchanged {
    $lines = if ($ExecutionMode -eq 'MO2Vfs') {
        Get-NormalizedLoadOrder $pluginsFile $creationClubFile $false
    } else {
        Get-OfflineNormalizedLoadOrder $LoadOrderFile
    }
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes((($lines -join "`n") + "`n"))))
    if ($digest -ne $script:initialInputDigest) {
        throw 'Input plugin name/order changed during generation; discard the candidate.'
    }
    $inventory = Get-PluginInventory $lines
    if ((Get-InventoryDigest $inventory) -ne $script:initialInventoryDigest) {
        throw 'Input plugin bytes/winning providers changed during generation; discard the candidate.'
    }
    if ((Get-SourceFingerprint).sha256 -ne $script:initialSourceDigest) {
        throw 'Generator/policy/test source changed during generation; discard the candidate.'
    }
}

$project = Join-Path $PSScriptRoot 'src\WeaponBalancePatcher\WeaponBalancePatcher.csproj'
$patcherFolder = Join-Path $PSScriptRoot "src\WeaponBalancePatcher\bin\$Configuration\net9.0"
$patcher = Join-Path $patcherFolder 'WeaponBalancePatcher.exe'
$settingsFolder = Join-Path $patcherFolder 'Data'
$settingsPath = Join-Path $settingsFolder 'settings.json'
$workFolder = Join-Path $PSScriptRoot 'work'
$effectiveLoadOrder = Join-Path $workFolder 'plugins-input.txt'
$persistence = Join-Path $workFolder 'persistence'
$generationLog = Join-Path $workFolder 'generation.log'
$auditLog = Join-Path $workFolder 'candidate-audit.log'
$auditReceiptPath = Join-Path $workFolder 'candidate-audit.json'
$determinismFolder = Join-Path $workFolder 'determinism'
$secondPlugin = Join-Path $determinismFolder $outputPlugin
$secondReport = Join-Path $determinismFolder 'selection-report.json'
$secondPersistence = Join-Path $determinismFolder 'persistence'
$secondGenerationLog = Join-Path $determinismFolder 'generation.log'

if ($ExecutionMode -eq 'MO2Vfs') {
    if (-not $AllowLiveProfileAccess) {
        throw 'MO2Vfs generation requires explicit -AllowLiveProfileAccess and the live-instance claim.'
    }
    if (-not $Instance) {
        $Instance = Find-WorkspacePath 'mo2-instances\skyrim-se' 'Container'
    }
    $Instance = (Resolve-Path -LiteralPath $Instance).Path
    $mo2 = Join-Path $Instance 'MO2Headless.exe'
    $profileFolder = Join-Path (Join-Path $Instance 'profiles') $Profile
    $pluginsFile = Join-Path $profileFolder 'plugins.txt'
    $ini = Join-Path $Instance 'ModOrganizer.ini'
    foreach ($required in @($mo2, $pluginsFile, $ini)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Required live-profile file does not exist: $required"
        }
    }
    $gameRoot = Get-GameRoot $ini
    $DataFolder = Join-Path $gameRoot 'Data'
    $creationClubFile = Join-Path $gameRoot 'Skyrim.ccc'
} else {
    if (-not $DataFolder -or -not $LoadOrderFile) {
        throw 'Offline generation requires explicit -DataFolder and -LoadOrderFile.'
    }
    $DataFolder = (Resolve-Path -LiteralPath $DataFolder).Path
    $LoadOrderFile = (Resolve-Path -LiteralPath $LoadOrderFile).Path
}
if (-not (Test-Path -LiteralPath $project -PathType Leaf)) {
    throw "Required project does not exist: $project"
}
$DataFolder = (Resolve-Path -LiteralPath $DataFolder -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $DataFolder -PathType Container)) {
    throw "Input Data folder does not exist: $DataFolder"
}
$artifactRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'artifacts'))
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
$SelectionReportPath = [IO.Path]::GetFullPath($SelectionReportPath)
$BuildManifestPath = [IO.Path]::GetFullPath($BuildManifestPath)
if ([IO.Path]::GetFileName($OutputPath) -cne $outputPlugin) {
    throw "Output plugin filename must be exactly $outputPlugin."
}
$requestedOutputs = @($OutputPath, $SelectionReportPath, $BuildManifestPath)
$requestedOutputSet = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase)
foreach ($requestedOutput in $requestedOutputs) {
    if (-not $requestedOutputSet.Add($requestedOutput)) {
        throw 'Output plugin, selection report, and build manifest paths must be distinct.'
    }
}
foreach ($path in $requestedOutputs) {
    if (-not (Test-PathWithin $path $artifactRoot) -or
        $path.Equals($artifactRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Generated artifacts must stay under $artifactRoot; refused $path"
    }
    Assert-NoReparseTraversal $path $PSScriptRoot
    if (Test-PathWithin $path $DataFolder) {
        throw "Generated artifact may not be inside the input Data folder: $path"
    }
    if ($ExecutionMode -eq 'MO2Vfs' -and (Test-PathWithin $path $Instance)) {
        throw "Generated artifact may not be inside the live MO2 instance: $path"
    }
    if (Test-Path -LiteralPath $path) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Generated artifact path exists but is not a regular file: $path"
        }
        if (-not $ReplaceExistingArtifacts) {
            throw "Generated artifact already exists; pass -ReplaceExistingArtifacts to replace the exact validated path: $path"
        }
    }
}
if ($ExecutionMode -eq 'Offline' -and @($requestedOutputs | Where-Object {
        $_.Equals($LoadOrderFile, [StringComparison]::OrdinalIgnoreCase)
    }).Count -gt 0) {
    throw 'An output path aliases the offline load-order input.'
}
$ownedWriteTargets = @(
    $workFolder, $effectiveLoadOrder, $persistence, $generationLog, $auditLog,
    $auditReceiptPath, $determinismFolder, $secondPlugin, $secondReport,
    $secondPersistence, $secondGenerationLog, $patcherFolder,
    (Join-Path $PSScriptRoot 'src\WeaponBalancePatcher\obj'))
foreach ($writeTarget in $ownedWriteTargets) {
    Assert-NoReparseTraversal $writeTarget $PSScriptRoot
}

if ($ExecutionMode -eq 'MO2Vfs') {
    Assert-LiveInstanceClaim
    $inputLines = Get-NormalizedLoadOrder $pluginsFile $creationClubFile $false
} else {
    $inputLines = Get-OfflineNormalizedLoadOrder $LoadOrderFile
}
$inputInventory = Get-PluginInventory $inputLines
$sourceFingerprint = Get-SourceFingerprint
$initialInputDigest = Get-NormalizedDigest $inputLines
$initialInventoryDigest = Get-InventoryDigest $inputInventory
$initialSourceDigest = $sourceFingerprint.sha256
if ($ExecutionMode -eq 'MO2Vfs') {
    Assert-LiveInstanceClaim
}
Assert-InputSnapshotUnchanged

# All aliases, path types, reparse traversal, inputs, and any live claim have
# now been validated. Destructive replacement is limited to these exact files.
foreach ($path in $requestedOutputs) {
    Assert-NoReparseTraversal $path $PSScriptRoot
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
    }
}
foreach ($folder in @(
    (Split-Path -Parent $OutputPath),
    (Split-Path -Parent $SelectionReportPath),
    (Split-Path -Parent $BuildManifestPath),
    $workFolder,
    $persistence)) {
    Assert-NoReparseTraversal $folder $PSScriptRoot
    if ($folder) { New-Item -ItemType Directory -Force -Path $folder | Out-Null }
}
Assert-NoReparseTraversal $effectiveLoadOrder $PSScriptRoot
Write-NormalizedLoadOrder $effectiveLoadOrder $inputLines

Push-Location $PSScriptRoot
try {
    Assert-NoReparseTraversal $patcherFolder $PSScriptRoot
    Assert-NoReparseTraversal (Join-Path $PSScriptRoot 'src\WeaponBalancePatcher\obj') $PSScriptRoot
    dotnet restore $project --locked-mode --nologo
    if ($LASTEXITCODE -ne 0) { throw "Patcher restore failed with exit code $LASTEXITCODE" }
    dotnet build $project -c $Configuration --nologo --no-restore
    if ($LASTEXITCODE -ne 0) { throw "Patcher build failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
foreach ($required in @($patcher, $settingsPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required generated/runtime file does not exist: $required"
    }
}
if ((Get-SourceFingerprint).sha256 -ne $initialSourceDigest) {
    throw 'Generator/policy/test source changed during build; discard the candidate.'
}
if ($ExecutionMode -eq 'MO2Vfs') {
    Assert-LiveInstanceClaim
}
Assert-InputSnapshotUnchanged
$oldReportEnvironment = $env:WEAPON_BALANCE_REPORT_PATH
try {
    foreach ($writeTarget in @($OutputPath, $SelectionReportPath, $persistence, $generationLog)) {
        Assert-NoReparseTraversal $writeTarget $PSScriptRoot
    }
    $env:WEAPON_BALANCE_REPORT_PATH = [System.IO.Path]::GetFullPath($SelectionReportPath)
    Invoke-Patcher $patcher @(
        'run-patcher',
        '--DataFolderPath', $DataFolder,
        '--ExtraDataFolder', $settingsFolder,
        '--GameRelease', 'SkyrimSE',
        '--LoadOrderFilePath', $effectiveLoadOrder,
        '--OutputPath', $OutputPath,
        '--ModKey', $outputPlugin,
        '--PatcherName', 'WeaponBalancePatch',
        '--PersistencePath', $persistence
    ) $patcherFolder $generationLog
} finally {
    $env:WEAPON_BALANCE_REPORT_PATH = $oldReportEnvironment
}
foreach ($required in @($OutputPath, $SelectionReportPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Patcher reported success but did not create $required"
    }
}

foreach ($writeTarget in @($auditReceiptPath, $auditLog)) {
    Assert-NoReparseTraversal $writeTarget $PSScriptRoot
}
Invoke-Patcher $patcher @(
    'audit-build', $DataFolder, $effectiveLoadOrder, $OutputPath,
    $settingsPath, $SelectionReportPath, $auditReceiptPath
) $patcherFolder $auditLog

if ($VerifyDeterminism) {
    foreach ($writeTarget in @(
        $determinismFolder, $secondPlugin, $secondReport, $secondPersistence,
        $secondGenerationLog)) {
        Assert-NoReparseTraversal $writeTarget $PSScriptRoot
    }
    New-Item -ItemType Directory -Force -Path $determinismFolder, $secondPersistence | Out-Null
    $oldReportEnvironment = $env:WEAPON_BALANCE_REPORT_PATH
    try {
        $env:WEAPON_BALANCE_REPORT_PATH = $secondReport
        Invoke-Patcher $patcher @(
            'run-patcher',
            '--DataFolderPath', $DataFolder,
            '--ExtraDataFolder', $settingsFolder,
            '--GameRelease', 'SkyrimSE',
            '--LoadOrderFilePath', $effectiveLoadOrder,
            '--OutputPath', $secondPlugin,
            '--ModKey', $outputPlugin,
            '--PatcherName', 'WeaponBalancePatch',
            '--PersistencePath', $secondPersistence
        ) $patcherFolder $secondGenerationLog
    } finally {
        $env:WEAPON_BALANCE_REPORT_PATH = $oldReportEnvironment
    }
    if ((Get-Sha256 $OutputPath) -ne (Get-Sha256 $secondPlugin)) {
        throw 'Determinism gate failed: two generated plugins differ.'
    }
    if ((Get-Sha256 $SelectionReportPath) -ne (Get-Sha256 $secondReport)) {
        throw 'Determinism gate failed: two selection reports differ.'
    }
}

if ($ExecutionMode -eq 'MO2Vfs') { Assert-LiveInstanceClaim }
Assert-InputSnapshotUnchanged
$audit = Get-Content -Raw -LiteralPath $auditReceiptPath | ConvertFrom-Json
$currentPluginHash = Get-Sha256 $OutputPath
$currentReportHash = Get-Sha256 $SelectionReportPath
if ($audit.pluginSha256 -ne $currentPluginHash -or
    $audit.selectionReportSha256 -ne $currentReportHash -or
    $audit.settingsSha256 -ne (Get-Sha256 $settingsPath)) {
    throw 'Candidate plugin, settings, or selection report changed after semantic audit.'
}
$auditInputs = @($audit.inputBinaries)
if ($auditInputs.Count -ne $inputInventory.Count) {
    throw "VFS/offline audit input count $($auditInputs.Count) differs from resolved inventory $($inputInventory.Count)."
}
for ($index = 0; $index -lt $inputInventory.Count; $index++) {
    if (-not $auditInputs[$index].plugin.Equals(
            $inputInventory[$index].plugin, [StringComparison]::OrdinalIgnoreCase) -or
        $auditInputs[$index].sha256 -ne $inputInventory[$index].sha256) {
        throw "Resolved plugin winner differs from patcher-visible input at index ${index}: $($inputInventory[$index].plugin)."
    }
}
$manifest = [ordered]@{
    schemaVersion = 2
    generatorVersion = '0.2.0'
    outputPlugin = $outputPlugin
    profile = $Profile
    inputLoadOrderEntries = $inputLines.Count
    inputLoadOrderSha256 = Get-Sha256 $effectiveLoadOrder
    inputPluginBinaries = $inputInventory
    inputPluginBinariesSha256 = Get-InventoryDigest $inputInventory
    sourceFingerprint = $sourceFingerprint
    settingsSha256 = Get-Sha256 $settingsPath
    selectionReportSha256 = $currentReportHash
    pluginSha256 = $currentPluginHash
    records = $audit.records
    recordsByType = $audit.recordTypes
    eslFlagged = $audit.eslFlagged
    ownLightFormCount = $audit.ownLightFormCount
    mastersCount = $audit.mastersCount
    explicitRules = $audit.explicitRules
    onlySpeedSemanticComparison = $audit.onlySpeedSemanticComparison
    deterministicDoubleBuild = [bool]$VerifyDeterminism
    finalWinningSpeedGate = 'pending installation at final plugin priority'
    executionMode = $ExecutionMode
}
Assert-NoReparseTraversal $BuildManifestPath $PSScriptRoot
if ($ExecutionMode -eq 'MO2Vfs') { Assert-LiveInstanceClaim }
Assert-InputSnapshotUnchanged
[System.IO.File]::WriteAllText(
    $BuildManifestPath,
    ($manifest | ConvertTo-Json -Depth 10),
    [System.Text.UTF8Encoding]::new($false))
if ((Get-Sha256 $OutputPath) -ne $currentPluginHash -or
    (Get-Sha256 $SelectionReportPath) -ne $currentReportHash) {
    throw 'Candidate plugin or selection report changed while the manifest was written.'
}

Write-Host "Generated and audited $OutputPath"
Write-Host "Plugin SHA256 $(Get-Sha256 $OutputPath)"
Write-Host "Input order $($inputLines.Count) entries, SHA256 $(Get-Sha256 $effectiveLoadOrder)"
Write-Host "Build manifest $BuildManifestPath"
