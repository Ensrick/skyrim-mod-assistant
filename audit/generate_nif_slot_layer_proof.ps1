[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $Instance,
    [Parameter(Mandatory)] [string] $GameData,
    [Parameter(Mandatory)] [string] $Receipt,
    [Parameter(Mandatory)] [string] $Output,
    [Parameter(Mandatory)] [string] $ToolBin,
    [string] $Repository = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$slot = 58
$profile = Join-Path $Instance 'profiles\Default'
$mods = Join-Path $Instance 'mods'
$overwrite = Join-Path $Instance 'overwrite'
$game = Split-Path -Parent $GameData
$ownedConfig = 'skse/plugins/skypatcher/armor/ensrick full cloak exclusivity/full cloaks.ini'

function Get-LinkResolvedPath([string] $Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetPathRoot($full)
    $current = $root
    $parts = $full.Substring($root.Length).Split(
        [IO.Path]::DirectorySeparatorChar, [StringSplitOptions]::RemoveEmptyEntries)
    for ($index = 0; $index -lt $parts.Count; $index++) {
        $current = Join-Path $current $parts[$index]
        if (-not (Test-Path -LiteralPath $current)) {
            for ($remaining = $index + 1; $remaining -lt $parts.Count; $remaining++) {
                $current = Join-Path $current $parts[$remaining]
            }
            break
        }
        $item = Get-Item -LiteralPath $current -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $target = $item.ResolveLinkTarget($true)
            if ($null -eq $target) { throw "Could not resolve output reparse point: $current" }
            $current = $target.FullName
        }
    }
    return [IO.Path]::GetFullPath($current)
}

function Test-PathWithin([string] $Candidate, [string] $Root) {
    $candidateFull = (Get-LinkResolvedPath $Candidate).TrimEnd('\', '/')
    $rootFull = (Get-LinkResolvedPath $Root).TrimEnd('\', '/')
    return $candidateFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase) -or
        $candidateFull.StartsWith($rootFull + [IO.Path]::DirectorySeparatorChar,
                                  [StringComparison]::OrdinalIgnoreCase)
}

if (Test-Path -LiteralPath $Output) {
    throw "Output must be a new file; refusing to replace an existing path: $Output"
}
$outputParent = Split-Path -Parent ([IO.Path]::GetFullPath($Output))
if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) {
    throw "Output parent must already exist: $outputParent"
}
if ((Test-PathWithin $Output $Instance) -or (Test-PathWithin $Output $GameData)) {
    throw 'Output must remain outside the MO2 instance and game Data, including through reparse points'
}

function Get-Sha256Bytes([byte[]] $Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

function Get-Sha256File([string] $Path) {
    $stream = [IO.File]::OpenRead($Path)
    try {
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream))
    }
    finally {
        $stream.Dispose()
    }
}

function Get-PhysicalReference([string] $Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $instanceRoot = [IO.Path]::GetFullPath($Instance).TrimEnd('\') + '\'
    $dataRoot = [IO.Path]::GetFullPath($GameData).TrimEnd('\') + '\'
    if ($full.StartsWith($instanceRoot, [StringComparison]::OrdinalIgnoreCase)) {
        return [ordered]@{ root = 'instance'; relativePath = $full.Substring($instanceRoot.Length).Replace('\', '/') }
    }
    if ($full.StartsWith($dataRoot, [StringComparison]::OrdinalIgnoreCase)) {
        return [ordered]@{ root = 'gameData'; relativePath = $full.Substring($dataRoot.Length).Replace('\', '/') }
    }
    throw "Input is outside the declared instance and game Data roots: $full"
}

function Add-FileBinding([Collections.Generic.Dictionary[string, object]] $Bindings,
                         [string] $Kind, [string] $Path) {
    $physical = Get-PhysicalReference $Path
    $key = "$($physical.root)|$($physical.relativePath)"
    $hash = Get-Sha256File $Path
    if ($Bindings.ContainsKey($key)) {
        if ($Bindings[$key].sha256 -ne $hash) { throw "Input changed during proof: $Path" }
        return
    }
    $Bindings.Add($key, [pscustomobject][ordered]@{
        kind = $Kind
        root = $physical.root
        relativePath = $physical.relativePath
        sha256 = $hash
        size = (Get-Item -LiteralPath $Path).Length
    })
}

function Get-CurrentProfileFingerprint {
    $fingerprintCode = @'
import json, sys
sys.path.insert(0, sys.argv[1])
import cloak_exclusivity as c
print(json.dumps(c.profile_fingerprint(c.Path(sys.argv[2]), c.Path(sys.argv[3])), separators=(",", ":")))
'@
    $raw = & py -3 -c $fingerprintCode (Join-Path $Repository 'audit') $Instance $GameData
    if ($LASTEXITCODE -ne 0) { throw 'Current cloak_exclusivity.profile_fingerprint failed' }
    return ([string]::Join('', $raw) | ConvertFrom-Json -Depth 100)
}

# Load the exact already-built parser and its direct format dependencies.
[Environment]::CurrentDirectory = $toolBin
foreach ($name in @('NiflySharp.dll', 'Mutagen.Bethesda.Kernel.dll',
                     'Mutagen.Bethesda.Core.dll', 'Mutagen.Bethesda.Skyrim.dll',
                     'housecarl-core.dll')) {
    [Reflection.Assembly]::LoadFrom((Join-Path $toolBin $name)) | Out-Null
}

$sourceReceipt = Get-Content -LiteralPath $Receipt -Raw | ConvertFrom-Json -Depth 100
$receiptModels = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($value in $sourceReceipt.participatingModelPaths) {
    [void]$receiptModels.Add(([string]$value).Replace('/', '\').ToLowerInvariant())
}

# Derive the explicit ARMA model set from the receipt's record graph rather
# than assuming participatingModelPaths is pre- or post-weight expansion.
$targetArmors = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($armor in $sourceReceipt.fullCloaks) { [void]$targetArmors.Add([string]$armor.formKey) }
$targetAddons = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($declaration in $sourceReceipt.reservation.declarations) {
    if ($declaration.type -eq 'ARMO' -and $targetArmors.Contains([string]$declaration.formKey)) {
        foreach ($armature in $declaration.armatures) { [void]$targetAddons.Add([string]$armature) }
    }
}
$explicit = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($declaration in $sourceReceipt.reservation.declarations) {
    if ($declaration.type -eq 'ARMA' -and $targetAddons.Contains([string]$declaration.formKey)) {
        foreach ($model in $declaration.models) {
            $normalized = ([string]$model).Replace('/', '\').ToLowerInvariant()
            if (-not $normalized.StartsWith('meshes\')) { $normalized = 'meshes\' + $normalized }
            [void]$explicit.Add($normalized)
        }
    }
}
if ($explicit.Count -ne 302) { throw "Expected 302 explicit ARMA model paths from the record graph, got $($explicit.Count)" }

$all = [Collections.Generic.HashSet[string]]::new($explicit, [StringComparer]::OrdinalIgnoreCase)
$companionOf = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($value in @($explicit)) {
    if ($value -match '_1\.nif$') {
        $companion = $value -replace '_1\.nif$', '_0.nif'
        if ($all.Add($companion)) { $companionOf.Add($companion, $value) }
    }
}
if ($all.Count -ne 576 -or $companionOf.Count -ne 274) {
    throw "Unexpected weighted mesh closure: $($all.Count) total, $($companionOf.Count) derived"
}
if (-not ($receiptModels.SetEquals($explicit) -or $receiptModels.SetEquals($all))) {
    throw "Receipt model scope is neither the explicit 302 paths nor expanded 576-path closure"
}
$fingerprintBefore = Get-CurrentProfileFingerprint

$warnings = [Collections.Generic.List[string]]::new()
$composition = [HousecarlCore.Mo2LoadOrder]::ReadComposition($profile, $warnings)
$archiveDiscovery = [HousecarlCore.ArchiveDiscovery]::Discover($profile, $mods, $GameData, $overwrite, $game)
if ($warnings.Count -or $archiveDiscovery.Warnings.Count) {
    throw "Incomplete profile/archive discovery: $($warnings + $archiveDiscovery.Warnings -join '; ')"
}
$resolver = [HousecarlCore.AssetResolver]::Build(
    $overwrite, $mods, $GameData, $composition.EnabledMods, $archiveDiscovery.Archives)

$bindings = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::OrdinalIgnoreCase)
$assets = [Collections.Generic.List[object]]::new()
$partitionCounts = [Collections.Generic.Dictionary[string, int]]::new([StringComparer]::OrdinalIgnoreCase)
$present = 0
$absent = 0
$loose = 0
$packed = 0

try {
    if ($resolver.ReadIncomplete) { throw "BSA table scan incomplete: $($resolver.BsaFailures -join '; ')" }
    foreach ($relative in @($all | Sort-Object)) {
        $resolution = $resolver.ResolveForPlacement($relative)
        if ($resolution.ReadIncomplete) { throw "BSA resolution incomplete for $relative" }
        $base = [ordered]@{
            relativePath = $relative.Replace('\', '/')
            explicitArmaPath = $explicit.Contains($relative)
            weightedCompanionOf = if ($companionOf.ContainsKey($relative)) { $companionOf[$relative].Replace('\', '/') } else { $null }
        }
        if ($resolution.Sources.Count -eq 0) {
            $base.state = 'absent'
            $assets.Add([pscustomobject]$base)
            $absent++
            continue
        }

        $winner = $resolution.Sources[0]
        $read = [HousecarlCore.AssetResolver]::ReadPlacementSource($winner)
        if ($null -ne $read.Item2) { throw "Could not read $relative from $($winner.ProviderName): $($read.Item2)" }
        [byte[]]$bytes = $read.Item1
        $inspection = [HousecarlCore.NifService]::Inspect($bytes)
        if ($null -ne $inspection.Error) { throw "NIF parse failed for ${relative}: $($inspection.Error)" }
        if ($null -eq $inspection.Inspect) { throw "NIF parser returned no model for $relative" }
        $parts = @($inspection.Inspect.Shapes | ForEach-Object { $_.Partitions } |
                   ForEach-Object { [int]$_.BodyPartId } | Sort-Object -Unique)
        foreach ($part in $parts) {
            $key = [string]$part
            if (-not $partitionCounts.ContainsKey($key)) { $partitionCounts.Add($key, 0) }
            $partitionCounts[$key]++
        }
        if ($parts -contains $slot) { throw "Reserved partition $slot already present in $relative" }

        $base.state = 'present'
        $base.parseSucceeded = $true
        $base.sha256 = Get-Sha256Bytes $bytes
        $base.partitionSlots = $parts
        $base.providerName = $winner.ProviderName
        $base.providerCount = $resolution.Sources.Count
        if ([string]$winner.Kind -eq 'Loose') {
            $source = Get-PhysicalReference $winner.LooseFilePath
            $base.providerKind = 'loose'
            $base.sourceRoot = $source.root
            $base.sourceRelativePath = $source.relativePath
            Add-FileBinding $bindings 'winning-loose-nif' $winner.LooseFilePath
            $loose++
        }
        else {
            $source = Get-PhysicalReference $winner.ArchivePath
            $base.providerKind = 'bsa'
            $base.sourceRoot = $source.root
            $base.sourceRelativePath = $source.relativePath
            $base.archiveEntryPath = $winner.EntryPath.Replace('\', '/')
            Add-FileBinding $bindings 'participating-bsa' $winner.ArchivePath
            $packed++
        }
        $assets.Add([pscustomobject]$base)
        $present++
    }
}
finally {
    $resolver.Dispose()
}

# Enumerate the actual winning loose SkyPatcher INIs and retain the exact files
# containing biped directives. All 34 config hashes are also covered by the
# imported profile fingerprint below.
$roots = [Collections.Generic.List[object]]::new()
$roots.Add([pscustomobject]@{ name = 'overwrite'; path = $overwrite })
foreach ($line in [IO.File]::ReadAllLines((Join-Path $profile 'modlist.txt'), [Text.Encoding]::UTF8)) {
    if ($line.StartsWith('+')) {
        $name = $line.Substring(1).Trim()
        if ($name -and -not $name.EndsWith('_separator', [StringComparison]::OrdinalIgnoreCase)) {
            $roots.Add([pscustomobject]@{ name = $name; path = Join-Path $mods $name })
        }
    }
}
$roots.Add([pscustomobject]@{ name = 'Data'; path = $GameData })
$configs = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($root in $roots) {
    $base = Join-Path $root.path 'SKSE\Plugins\SkyPatcher'
    if (-not (Test-Path -LiteralPath $base -PathType Container)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $base -Filter '*.ini' -File -Recurse | Sort-Object FullName) {
        $relative = [IO.Path]::GetRelativePath($root.path, $file.FullName).Replace('\', '/').ToLowerInvariant()
        if ($relative -eq $ownedConfig) { continue }
        if (-not $configs.ContainsKey($relative)) {
            $configs.Add($relative, [pscustomobject]@{ provider = $root.name; path = $file.FullName })
        }
    }
}
$bipedConfigs = [Collections.Generic.List[object]]::new()
$bipedLines = 0
foreach ($pair in $configs.GetEnumerator() | Sort-Object Key) {
    $active = @([IO.File]::ReadAllLines($pair.Value.path) | Where-Object {
        $line = $_.Trim()
        $line -and -not $line.StartsWith(';') -and
            $line -match '(?i)\b(filterByBipedSlots(?:Excluded|Or)?|bipedSlotsTo(?:Add|Remove))\s*='
    })
    if ($active.Count) {
        $physical = Get-PhysicalReference $pair.Value.path
        Add-FileBinding $bindings 'winning-biped-skypatcher-config' $pair.Value.path
        $bipedLines += $active.Count
        $bipedConfigs.Add([pscustomobject][ordered]@{
            relativePath = $pair.Key
            providerName = $pair.Value.provider
            sourceRoot = $physical.root
            sourceRelativePath = $physical.relativePath
            sha256 = Get-Sha256File $pair.Value.path
            activeDirectiveLines = $active
        })
    }
}

$skyResolution = $null
foreach ($root in $roots) {
    $candidate = Join-Path $root.path 'SKSE\Plugins\SkyPatcher.dll'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $skyResolution = [pscustomobject]@{ provider = $root.name; path = $candidate }
        break
    }
}
if ($null -eq $skyResolution) { throw 'Winning SkyPatcher.dll not found' }
$skyPhysical = Get-PhysicalReference $skyResolution.path
Add-FileBinding $bindings 'winning-skypatcher-dll' $skyResolution.path

$fingerprint = Get-CurrentProfileFingerprint
$beforeCanonical = $fingerprintBefore | ConvertTo-Json -Depth 100 -Compress
$afterCanonical = $fingerprint | ConvertTo-Json -Depth 100 -Compress
if ($beforeCanonical -cne $afterCanonical) {
    throw 'Profile inputs changed during the all-layer proof; discard the output and retry'
}

if ($present + $absent -ne $all.Count -or $partitionCounts.ContainsKey([string]$slot)) {
    throw 'Layer proof totals or reserved-partition assertion failed'
}
# Currency 0.3.0 adds exactly one reviewed MISC-only file. It changes no biped
# operations; pin that additional input rather than waiving the snapshot count.
$currencyConfigKey = 'skse/plugins/skypatcher/misc/zz_ensrick_currency_moderndenominations.ini'
$expectedConfigCount = 34
if ($configs.ContainsKey($currencyConfigKey)) {
    if ((Get-Sha256File $configs[$currencyConfigKey].path) -ne
        '4BA56920F2C5DC6903F9DDA9B1733F836A0604B56D496992D2C8D76844EAF77E') {
        throw 'Currency denomination config changed; review its biped impact before reserving the slot'
    }
    $expectedConfigCount = 35
}
if ($bipedConfigs.Count -ne 1 -or $bipedLines -ne 5 -or $configs.Count -ne $expectedConfigCount) {
    throw "Unexpected SkyPatcher config state: $($configs.Count) winners, $($bipedConfigs.Count) biped configs, $bipedLines lines"
}

$proof = [ordered]@{
    schemaVersion = 1
    proofKind = 'full-cloak-biped-slot-all-layer-reservation'
    status = 'PASS'
    slot = $slot
    scope = 'Exact current MO2 profile; participating cloak ARMA model paths plus deterministic _0 weighted companions only.'
    profileFingerprint = $fingerprint
    sourceReceipt = [ordered]@{
        root = 'repository'
        relativePath = [IO.Path]::GetRelativePath($Repository, $Receipt).Replace('\', '/')
        sha256 = Get-Sha256File $Receipt
    }
    parser = [ordered]@{
        service = 'HousecarlCore.NifService (NiflySharp)'
        housecarlCoreSha256 = Get-Sha256File (Join-Path $toolBin 'housecarl-core.dll')
        niflySharpSha256 = Get-Sha256File (Join-Path $toolBin 'NiflySharp.dll')
    }
    weightedCompanionRule = 'For every explicit ARMA path ending _1.nif, audit the same path ending _0.nif.'
    counts = [ordered]@{
        explicitArmaModelPaths = $explicit.Count
        derivedWeightZeroCompanions = $companionOf.Count
        auditedModelPaths = $all.Count
        present = $present
        absent = $absent
        looseWinners = $loose
        bsaWinners = $packed
        nifParseErrors = 0
        reservedPartitionHits = 0
        winningSkyPatcherConfigs = $configs.Count
        bipedDirectiveConfigs = $bipedConfigs.Count
        activeBipedDirectiveLines = $bipedLines
    }
    partitionFileCounts = [ordered]@{}
    assets = @($assets)
    fileBindings = @($bindings.Values | Sort-Object root, relativePath)
    runtime = [ordered]@{
        skyPatcherDll = [ordered]@{
            providerName = $skyResolution.provider
            sourceRoot = $skyPhysical.root
            sourceRelativePath = $skyPhysical.relativePath
            sha256 = Get-Sha256File $skyResolution.path
        }
        winningBipedConfigs = @($bipedConfigs)
    }
    absenceSemantics = 'Absent rows are sentinels, not working-asset claims. A newly resolving provider invalidates this proof.'
    limitations = @(
        'Slot 58 is historically used for left/secondary arm equipment; this is a current-profile reservation, not a universal convention.',
        'Static record, mesh, and parser-input proof does not replace an in-game equip/re-equip acceptance test.'
    )
}
foreach ($key in $partitionCounts.Keys | Sort-Object { [int]$_ }) {
    $proof.partitionFileCounts[$key] = $partitionCounts[$key]
}

$json = $proof | ConvertTo-Json -Depth 100
[IO.File]::WriteAllText($Output, $json + "`n", [Text.UTF8Encoding]::new($false))
Write-Output ($proof.counts | ConvertTo-Json -Compress)
Write-Output "proof=$Output"
