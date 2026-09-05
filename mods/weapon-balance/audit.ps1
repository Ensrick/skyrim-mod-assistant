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

function Get-LocalizedSidecarInventory([string]$PluginPath, [string]$Boundary) {
    $pluginFullPath = [IO.Path]::GetFullPath($PluginPath)
    $stringsRoot = Join-Path (Split-Path -Parent $pluginFullPath) 'Strings'
    if (-not (Test-Path -LiteralPath $stringsRoot)) { return @() }
    if (-not (Test-Path -LiteralPath $stringsRoot -PathType Container)) {
        throw "Localized sidecar root is not a directory: $stringsRoot"
    }
    Assert-NoReparseTraversal $stringsRoot $Boundary
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
        Assert-NoReparseTraversal $item.FullName $Boundary
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
            sha256 = Get-FileSha256 $item.FullName
        })
    }
    return @($rows | Sort-Object relativePath)
}

function Get-Mo2LocalizedSidecarInventory {
    $stem = [IO.Path]::GetFileNameWithoutExtension($outputPlugin)
    $pattern = '^' + [regex]::Escape($stem) +
        '_(?<language>[A-Za-z][A-Za-z0-9_]*)\.(?<kind>STRINGS|ILSTRINGS|DLSTRINGS)$'
    $caseInsensitivePattern = '(?i)' + $pattern
    $modlistFile = Join-Path $profileFolder 'modlist.txt'
    if (-not (Test-Path -LiteralPath $modlistFile -PathType Leaf)) {
        throw "MO2 profile modlist is absent: $modlistFile"
    }
    $enabledMods = @(Get-Content -LiteralPath $modlistFile |
        ForEach-Object { $_.Trim() } | Where-Object { $_.StartsWith('+') } |
        ForEach-Object { $_.Substring(1) })
    $layers = [Collections.Generic.List[object]]::new()
    $layers.Add([pscustomobject]@{ root = Join-Path $Instance 'overwrite'; provider = 'overwrite' })
    foreach ($modName in $enabledMods) {
        $layers.Add([pscustomobject]@{
            root = Join-Path (Join-Path $Instance 'mods') $modName
            provider = "mod:$modName"
        })
    }
    $layers.Add([pscustomobject]@{ root = $dataFolder; provider = 'game-data' })
    $winners = [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    foreach ($layer in $layers) {
        $stringsRoot = Join-Path $layer.root 'Strings'
        if (-not (Test-Path -LiteralPath $stringsRoot -PathType Container)) { continue }
        $stringsRootItem = Get-Item -LiteralPath $stringsRoot -Force
        if (($stringsRootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing localized sidecar root that is a reparse point: $stringsRoot"
        }
        foreach ($item in Get-ChildItem -LiteralPath $stringsRoot -Force | Sort-Object Name) {
            if (-not [regex]::IsMatch($item.Name, $caseInsensitivePattern)) { continue }
            $match = [regex]::Match($item.Name, $pattern)
            if (-not $match.Success) {
                throw "Localized sidecar has noncanonical casing: $($item.FullName)"
            }
            if ($item.PSIsContainer -or
                ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Localized sidecar winner is not a regular non-reparse file: $($item.FullName)"
            }
            if ($winners.ContainsKey($item.Name)) { continue }
            $kind = $match.Groups['kind'].Value
            $winners[$item.Name] = [pscustomobject]@{
                relativePath = "Strings/$($item.Name)"
                language = $match.Groups['language'].Value
                source = switch ($kind) {
                    'STRINGS' { 'Normal' }
                    'ILSTRINGS' { 'IL' }
                    'DLSTRINGS' { 'DL' }
                    default { throw "Unsupported localized sidecar kind: $kind" }
                }
                bytes = [long]$item.Length
                sha256 = Get-FileSha256 $item.FullName
                provider = $layer.provider
            }
        }
    }
    return @($winners.Values | Sort-Object relativePath)
}

function Get-LocalizedSidecarDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object relativePath | ForEach-Object {
        "$($_.relativePath)|$($_.language)|$($_.source)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($content))
}

function Get-WinningSidecarDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object relativePath | ForEach-Object {
        "$($_.relativePath)|$($_.language)|$($_.source)|$($_.bytes)|$($_.sha256)|$($_.provider)"
    }) -join "`n") + "`n")
    return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($content))
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

function Assert-InstalledLocalizedSidecars($Expected) {
    $actual = @(Get-Mo2LocalizedSidecarInventory)
    Assert-LocalizedSidecarShape $actual 'Installed localized sidecar winners'
    Assert-LocalizedSidecarsEqual $Expected $actual 'Installed localized sidecar winners'
    foreach ($row in $actual) {
        if ($row.provider -cne "mod:$InstalledModName") {
            throw "Installed localized sidecar winner $($row.relativePath) is $($row.provider), not mod:$InstalledModName."
        }
    }
    return $actual
}

function Get-InputResourceLayers {
    $modlistFile = Join-Path $profileFolder 'modlist.txt'
    if (-not (Test-Path -LiteralPath $modlistFile -PathType Leaf)) {
        throw "MO2 profile modlist is absent: $modlistFile"
    }
    $layers = [Collections.Generic.List[object]]::new()
    $layers.Add([pscustomobject]@{
        root = Join-Path $Instance 'overwrite'
        provider = 'overwrite'
    })
    foreach ($modName in @(Get-Content -LiteralPath $modlistFile |
            ForEach-Object { $_.Trim() } | Where-Object { $_.StartsWith('+') } |
            ForEach-Object { $_.Substring(1) })) {
        $layers.Add([pscustomobject]@{
            root = Join-Path (Join-Path $Instance 'mods') $modName
            provider = "mod:$modName"
        })
    }
    $layers.Add([pscustomobject]@{ root = $dataFolder; provider = 'game-data' })
    return @($layers)
}

function ConvertTo-SafeResourceRelativePath([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or
        [IO.Path]::IsPathFullyQualified($RelativePath)) {
        throw "Localization resource path is not a safe relative path: $RelativePath"
    }
    $normalized = $RelativePath.Replace('\', '/').TrimStart('/')
    $segments = @($normalized.Split('/', [StringSplitOptions]::RemoveEmptyEntries))
    if ($segments.Count -lt 1 -or @($segments | Where-Object { $_ -in @('.', '..') }).Count -gt 0) {
        throw "Localization resource path contains invalid traversal: $RelativePath"
    }
    return $normalized
}

function Get-ProviderLooseResourceWinners([string]$ProviderPlugin, $Layers) {
    $stem = [IO.Path]::GetFileNameWithoutExtension($ProviderPlugin)
    $pattern = '^' + [regex]::Escape($stem) +
        '_(?<language>[A-Za-z][A-Za-z0-9_]*)\.(?<kind>STRINGS|ILSTRINGS|DLSTRINGS)$'
    $winners = [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    foreach ($layer in @($Layers)) {
        $stringsRoot = Join-Path $layer.root 'Strings'
        if (-not (Test-Path -LiteralPath $stringsRoot -PathType Container)) { continue }
        Assert-NoReparseTraversal $stringsRoot $layer.root
        foreach ($item in Get-ChildItem -LiteralPath $stringsRoot -Force | Sort-Object Name) {
            $match = [regex]::Match($item.Name, $pattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)
            if (-not $match.Success -or $winners.ContainsKey($item.Name)) { continue }
            if ($item.PSIsContainer) {
                throw "Localization resource winner is not a regular file: $($item.FullName)"
            }
            Assert-NoReparseTraversal $item.FullName $layer.root
            $winners[$item.Name] = [pscustomobject]@{
                relativePath = "Strings/$($item.Name)"
                fullPath = $item.FullName
                provider = $layer.provider
                bytes = [long]$item.Length
                sha256 = Get-FileSha256 $item.FullName
            }
        }
    }
    return @($winners.Values | Sort-Object relativePath)
}

function Import-ArchiveRuntime {
    if ('Mutagen.Bethesda.Archives.Archive' -as [type]) { return }
    foreach ($name in @(
        'System.IO.Abstractions.dll', 'Testably.Abstractions.FileSystem.Interface.dll',
        'TestableIO.System.IO.Abstractions.dll', 'TestableIO.System.IO.Abstractions.Wrappers.dll',
        'Noggog.CSharpExt.dll', 'Mutagen.Bethesda.Kernel.dll', 'Mutagen.Bethesda.Core.dll')) {
        $path = Join-Path $patcherFolder $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required archive inventory runtime is absent: $path"
        }
        [void][Reflection.Assembly]::LoadFrom($path)
    }
    if (-not ('Mutagen.Bethesda.Archives.Archive' -as [type])) {
        throw 'Could not load the pinned Mutagen archive inventory runtime.'
    }
}

function Get-ArchiveSnapshot($Layers) {
    $winners = [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    foreach ($layer in @($Layers)) {
        if (-not (Test-Path -LiteralPath $layer.root -PathType Container)) { continue }
        foreach ($item in Get-ChildItem -LiteralPath $layer.root -File -Filter '*.bsa' -Force) {
            if (-not $winners.ContainsKey($item.Name)) {
                $winners[$item.Name] = [pscustomobject]@{
                    relativePath = $item.Name
                    fullPath = $item.FullName
                    layerRoot = $layer.root
                    provider = $layer.provider
                    bytes = [long]$item.Length
                }
            }
        }
    }
    if ($winners.Count -eq 0) {
        return [pscustomobject]@{ winners = $winners; iniListings = $null }
    }
    Import-ArchiveRuntime
    $release = [Mutagen.Bethesda.GameRelease]::SkyrimSE
    $iniMethod = [Mutagen.Bethesda.Archives.Archive].GetMethods() | Where-Object {
        $_.Name -eq 'GetIniListings' -and $_.GetParameters().Count -eq 2
    }
    if (@($iniMethod).Count -ne 1) { throw 'Pinned Mutagen GetIniListings API shape changed.' }
    $iniListings = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    foreach ($fileName in @($iniMethod.Invoke($null, @($release, $null)))) {
        [void]$iniListings.Add($fileName.String)
    }
    return [pscustomobject]@{ winners = $winners; iniListings = $iniListings }
}

function Get-ApplicableArchiveWinners([string]$ProviderPlugin, $Snapshot) {
    if ($Snapshot.winners.Count -eq 0) { return @() }
    $release = [Mutagen.Bethesda.GameRelease]::SkyrimSE
    $modKey = [Mutagen.Bethesda.Plugins.ModKey]::FromFileName($ProviderPlugin)
    return @($Snapshot.winners.Values | Where-Object {
        $Snapshot.iniListings.Contains($_.relativePath) -or
        [Mutagen.Bethesda.Archives.Archive]::IsApplicable(
            $release, $modKey, [Noggog.FileName]::new($_.relativePath))
    } | Sort-Object relativePath)
}

function Get-ArchiveLocalizationMatches(
    $Archive, [string]$ProviderPlugin, $CandidateMetadata, $ContentCache) {
    Import-ArchiveRuntime
    if (-not $ContentCache.ContainsKey($Archive.fullPath)) {
        Assert-NoReparseTraversal $Archive.fullPath $Archive.layerRoot
        $reader = [Mutagen.Bethesda.Archives.Archive]::CreateReader(
            [Mutagen.Bethesda.GameRelease]::SkyrimSE,
            [Noggog.FilePath]::new($Archive.fullPath), $null)
        $stringEntries = @($reader.Files | ForEach-Object {
            $relative = $_.Path.Replace('\', '/').TrimStart('/')
            if ($relative -match '(?i)^Strings/.+\.(STRINGS|ILSTRINGS|DLSTRINGS)$') {
                [pscustomobject]@{ file = $_; relativePath = $relative }
            }
        })
        $ContentCache[$Archive.fullPath] = $stringEntries
    }
    $candidateMatches = [Collections.Generic.List[object]]::new()
    $providerMatches = [Collections.Generic.List[string]]::new()
    $stem = [IO.Path]::GetFileNameWithoutExtension($ProviderPlugin)
    $pattern = '^Strings/' + [regex]::Escape($stem) +
        '_(?<language>[A-Za-z][A-Za-z0-9_]*)\.(?<kind>STRINGS|ILSTRINGS|DLSTRINGS)$'
    foreach ($entry in @($ContentCache[$Archive.fullPath])) {
        $file = $entry.file
        $relative = $entry.relativePath
        if ([regex]::IsMatch(
                $relative, $pattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            $providerMatches.Add($relative)
        }
        if (-not $CandidateMetadata.ContainsKey($relative)) { continue }
        $metadata = $CandidateMetadata[$relative]
        $bytes = $file.GetBytes()
        $candidateMatches.Add([pscustomobject]@{
            relativePath = $relative
            language = $metadata.language
            source = $metadata.source
            bytes = [long]$file.Size
            sha256 = [Convert]::ToHexString(
                [Security.Cryptography.SHA256]::HashData([byte[]]$bytes))
        })
    }
    return [pscustomobject]@{
        candidateMatches = @($candidateMatches | Sort-Object relativePath)
        providerMatches = @($providerMatches | Sort-Object -Unique)
    }
}

function Get-InputLocalizationPhysicalState($Contract) {
    if ($null -eq $Contract -or $Contract.schemaVersion -ne 1 -or
        [string]$Contract.sha256 -notmatch '^[A-F0-9]{64}$') {
        throw 'Build manifest has no valid input-localization-resource contract.'
    }
    if ((Get-InputLocalizationContractDigest $Contract) -cne [string]$Contract.sha256) {
        throw 'Build manifest input-localization-resource aggregate hash is invalid.'
    }
    $providers = @($Contract.providers)
    $resolutions = @($Contract.resolutions)
    $layers = @(Get-InputResourceLayers)
    $archiveSnapshot = Get-ArchiveSnapshot $layers
    $archiveContentCache = [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    $archiveHashCache = [Collections.Generic.Dictionary[string, string]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    $currentLoose = [Collections.Generic.List[object]]::new()
    $currentArchives = [Collections.Generic.List[object]]::new()
    $physical = [Collections.Generic.List[object]]::new()
    foreach ($provider in $providers) {
        $providerName = [string]$provider.provider
        $candidatePaths = @($provider.candidateRelativePaths)
        $providerResolutions = @($resolutions | Where-Object {
            $_.provider.Equals($providerName, [StringComparison]::OrdinalIgnoreCase)
        })
        if ([string]::IsNullOrWhiteSpace($providerName) -or
            $providerResolutions.Count -ne $candidatePaths.Count) {
            throw "Input-localization provider contract is incomplete: $providerName"
        }
        $metadata = [Collections.Generic.Dictionary[string, object]]::new(
            [StringComparer]::OrdinalIgnoreCase)
        foreach ($resolution in $providerResolutions) {
            $relative = ConvertTo-SafeResourceRelativePath ([string]$resolution.relativePath)
            if (-not $metadata.TryAdd($relative, [pscustomobject]@{
                    relativePath = $relative
                    language = [string]$resolution.language
                    source = [string]$resolution.source
                })) {
                throw "Duplicate input-localization candidate: ${providerName}:$relative"
            }
        }
        foreach ($candidate in $candidatePaths) {
            $relative = ConvertTo-SafeResourceRelativePath ([string]$candidate)
            if (-not $metadata.ContainsKey($relative)) {
                throw "Input-localization candidate lacks resolution metadata: ${providerName}:$relative"
            }
        }
        $expectedArchivePaths = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase)
        foreach ($expectedArchive in @($Contract.archives | Where-Object {
                $_.provider.Equals($providerName, [StringComparison]::OrdinalIgnoreCase)
            })) {
            $relative = ConvertTo-SafeResourceRelativePath ([string]$expectedArchive.relativePath)
            if (-not $expectedArchivePaths.Add($relative)) {
                throw "Duplicate input-localization archive: ${providerName}:$relative"
            }
        }
        $looseWinners = @(Get-ProviderLooseResourceWinners $providerName $layers)
        $looseByPath = [Collections.Generic.Dictionary[string, object]]::new(
            [StringComparer]::OrdinalIgnoreCase)
        foreach ($winner in $looseWinners) {
            $looseByPath[$winner.relativePath] = $winner
            $physical.Add([pscustomobject]@{
                provider = $providerName; kind = 'loose'; relativePath = $winner.relativePath
                winningProvider = $winner.provider; bytes = $winner.bytes; sha256 = $winner.sha256
            })
        }
        foreach ($candidate in $candidatePaths) {
            $relative = ConvertTo-SafeResourceRelativePath ([string]$candidate)
            if (-not $looseByPath.ContainsKey($relative)) { continue }
            $winner = $looseByPath[$relative]
            $meta = $metadata[$relative]
            $currentLoose.Add([pscustomobject]@{
                provider = $providerName; relativePath = $meta.relativePath
                language = $meta.language; source = $meta.source
                bytes = $winner.bytes; sha256 = $winner.sha256
            })
        }
        foreach ($archive in @(Get-ApplicableArchiveWinners $providerName $archiveSnapshot)) {
            $matches = Get-ArchiveLocalizationMatches `
                $archive $providerName $metadata $archiveContentCache
            if ($matches.providerMatches.Count -eq 0) { continue }
            if (-not $archiveHashCache.ContainsKey($archive.fullPath)) {
                $archiveHashCache[$archive.fullPath] = Get-FileSha256 $archive.fullPath
            }
            $archive | Add-Member -NotePropertyName sha256 -NotePropertyValue `
                $archiveHashCache[$archive.fullPath] -Force
            $physical.Add([pscustomobject]@{
                provider = $providerName; kind = 'archive'; relativePath = $archive.relativePath
                winningProvider = $archive.provider; bytes = $archive.bytes; sha256 = $archive.sha256
            })
            if ($matches.candidateMatches.Count -gt 0) {
                $currentArchives.Add([pscustomobject]@{
                    provider = $providerName; relativePath = $archive.relativePath
                    bytes = $archive.bytes; sha256 = $archive.sha256
                    matchedEntries = @($matches.candidateMatches)
                })
            }
        }
    }
    $currentResolutions = @($resolutions | ForEach-Object {
        $expected = $_
        $loose = @($currentLoose | Where-Object {
            $_.provider.Equals($expected.provider, [StringComparison]::OrdinalIgnoreCase) -and
            $_.relativePath.Equals($expected.relativePath, [StringComparison]::OrdinalIgnoreCase)
        })
        $archiveMatches = @($currentArchives | Where-Object {
            $_.provider.Equals($expected.provider, [StringComparison]::OrdinalIgnoreCase) -and
            @($_.matchedEntries | Where-Object {
                $_.relativePath.Equals($expected.relativePath, [StringComparison]::OrdinalIgnoreCase)
            }).Count -gt 0
        })
        $available = @($loose | ForEach-Object { "loose:$($_.relativePath)" }) +
            @($archiveMatches | ForEach-Object { "archive:$($_.relativePath)" })
        $available = @($available | Sort-Object)
        $resolution = if ($loose.Count -gt 0) { 'loose' } elseif ($archiveMatches.Count -eq 0) {
            'absent'
        } elseif ($archiveMatches.Count -eq 1) { 'archive' } else { 'ambiguous-archives' }
        $selected = if ($resolution -eq 'loose') {
            "loose:$($loose[0].relativePath)"
        } elseif ($resolution -eq 'archive') {
            "archive:$($archiveMatches[0].relativePath)"
        } else { $null }
        [pscustomobject]@{
            provider = [string]$expected.provider; relativePath = [string]$expected.relativePath
            language = [string]$expected.language; source = [string]$expected.source
            resolution = $resolution; selectedContainer = $selected
            availableContainers = @($available)
        }
    } | Sort-Object provider, relativePath)
    return [pscustomobject]@{
        looseFiles = @($currentLoose | Sort-Object provider, relativePath)
        archives = @($currentArchives | Sort-Object provider, relativePath)
        resolutions = $currentResolutions
        physicalProviders = @($physical | Sort-Object provider, kind, relativePath)
    }
}

function Assert-InputLocalizationRowsEqual($Expected, $Actual, [string[]]$Fields, [string]$Context) {
    $expectedRows = @($Expected | Sort-Object provider, relativePath)
    $actualRows = @($Actual | Sort-Object provider, relativePath)
    if ($expectedRows.Count -ne $actualRows.Count) {
        throw "$Context count differs: expected $($expectedRows.Count), got $($actualRows.Count)."
    }
    for ($index = 0; $index -lt $expectedRows.Count; $index++) {
        foreach ($field in $Fields) {
            if ($field -in @('matchedEntries', 'availableContainers')) { continue }
            if ([string]$expectedRows[$index].$field -cne [string]$actualRows[$index].$field) {
                throw "$Context differs at index $index field $field."
            }
        }
        if ($Fields -contains 'matchedEntries') {
            Assert-InputLocalizationRowsEqual @($expectedRows[$index].matchedEntries) `
                @($actualRows[$index].matchedEntries) `
                @('relativePath', 'language', 'source', 'bytes', 'sha256') `
                "$Context matched entries at index $index"
        }
        if ($Fields -contains 'availableContainers') {
            if ((@($expectedRows[$index].availableContainers | Sort-Object) -join '|') -cne
                (@($actualRows[$index].availableContainers | Sort-Object) -join '|')) {
                throw "$Context available containers differ at index $index."
            }
        }
    }
}

function Get-InputLocalizationPhysicalDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object provider, kind, relativePath | ForEach-Object {
        "$($_.provider)|$($_.kind)|$($_.relativePath)|$($_.winningProvider)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($content))
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
    return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($canonical))
}

function Assert-InputLocalizationResourcesCurrent($Contract, $ExpectedPhysicalProviders = $null) {
    $state = Get-InputLocalizationPhysicalState $Contract
    Assert-InputLocalizationRowsEqual @($Contract.looseFiles) @($state.looseFiles) `
        @('provider', 'relativePath', 'language', 'source', 'bytes', 'sha256') `
        'Input localization loose files'
    Assert-InputLocalizationRowsEqual @($Contract.archives) @($state.archives) `
        @('provider', 'relativePath', 'bytes', 'sha256', 'matchedEntries') `
        'Input localization archives'
    Assert-InputLocalizationRowsEqual @($Contract.resolutions) @($state.resolutions) `
        @('provider', 'relativePath', 'language', 'source', 'resolution',
            'selectedContainer', 'availableContainers') `
        'Input localization resolutions'
    if ($null -ne $ExpectedPhysicalProviders) {
        Assert-InputLocalizationRowsEqual @($ExpectedPhysicalProviders) @($state.physicalProviders) `
            @('provider', 'kind', 'relativePath', 'winningProvider', 'bytes', 'sha256') `
            'Input localization physical providers'
    }
    return $state
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
    $wanted = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    foreach ($line in $Lines) { [void]$wanted.Add($line.TrimStart('*')) }
    $winningIndex = [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    $layers = [Collections.Generic.List[object]]::new()
    $layers.Add([pscustomobject]@{
        root = Join-Path $Instance 'overwrite'
        provider = 'overwrite'
    })
    foreach ($modName in $enabledMods) {
        $layers.Add([pscustomobject]@{
            root = Join-Path (Join-Path $Instance 'mods') $modName
            provider = "mod:$modName"
        })
    }
    # Build a fresh precedence index for this exact snapshot. Keeping it local
    # ensures every before/after gate re-reads the profile and winning files.
    foreach ($layer in $layers) {
        if (-not (Test-Path -LiteralPath $layer.root -PathType Container)) { continue }
        foreach ($file in Get-ChildItem -LiteralPath $layer.root -File -Force) {
            if ($wanted.Contains($file.Name) -and -not $winningIndex.ContainsKey($file.Name)) {
                $winningIndex[$file.Name] = [pscustomobject]@{
                    path = $file.FullName
                    provider = $layer.provider
                }
            }
        }
    }
    $inventory = foreach ($line in $Lines) {
        $pluginName = $line.TrimStart('*')
        $winner = $null
        $provider = $null
        if ($winningIndex.ContainsKey($pluginName)) {
            $winner = $winningIndex[$pluginName].path
            $provider = $winningIndex[$pluginName].provider
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
    $currentArtifactSidecars = @(Get-LocalizedSidecarInventory $script:pluginPath $script:ArtifactRoot)
    if ((Get-LocalizedSidecarDigest $currentArtifactSidecars) -ne $script:auditArtifactSidecarDigest) {
        throw 'Candidate localized sidecar bytes/inventory changed during VFS audit; discard its result.'
    }
    if ($script:auditIncludesOutput) {
        $currentInstalledSidecars = @(Assert-InstalledLocalizedSidecars $script:manifestSidecars)
        if ((Get-WinningSidecarDigest $currentInstalledSidecars) -ne $script:auditInstalledSidecarDigest) {
            throw 'Installed localized sidecar winners changed during VFS audit; discard its result.'
        }
    }
    $currentInputLocalization = Assert-InputLocalizationResourcesCurrent `
        $script:manifestInputLocalizationResources `
        $script:manifestInputLocalizationResourceProviders
    if ((Get-InputLocalizationPhysicalDigest $currentInputLocalization.physicalProviders) -ne
        $script:auditInputLocalizationPhysicalDigest) {
        throw 'Input localization resource bytes/providers changed during VFS audit; discard its result.'
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
$manifestSidecars = @($manifest.localizedSidecars)
if ($manifest.schemaVersion -ne 3 -or $manifest.generatorVersion -ne '0.3.0' -or
    -not $manifest.localized) {
    throw 'Build manifest does not declare the required 0.3 localized-output contract.'
}
Assert-LocalizedSidecarShape $manifestSidecars 'Build manifest'
if ($manifest.localizedSidecarsSha256 -cne (Get-LocalizedSidecarDigest $manifestSidecars)) {
    throw 'Build manifest localized-sidecar aggregate hash is invalid.'
}
$manifestLanguages = @($manifestSidecars.language | Sort-Object -Unique)
if ((@($manifest.translationLanguages) -join '|') -cne ($manifestLanguages -join '|')) {
    throw 'Build manifest translation-language inventory differs from its sidecars.'
}
$manifestInputTranslationSemantics = $manifest.inputTranslationSemantics
if ($null -eq $manifestInputTranslationSemantics -or
    $manifestInputTranslationSemantics.schemaVersion -ne 1 -or
    [string]$manifestInputTranslationSemantics.sha256 -notmatch '^[A-F0-9]{64}$') {
    throw 'Build manifest has no valid input-translation-semantics receipt.'
}
$manifestInputLocalizationResources = $manifest.inputLocalizationResources
$manifestInputLocalizationResourceProviders = @($manifest.inputLocalizationResourceProviders)
if ($manifest.inputLocalizationResourceProvidersSha256 -cne
    (Get-InputLocalizationPhysicalDigest $manifestInputLocalizationResourceProviders)) {
    throw 'Build manifest input-localization physical-provider aggregate hash is invalid.'
}
$semanticLocalizedProviders = @($manifestInputTranslationSemantics.providers |
    Where-Object sourceUsesLocalization | Sort-Object provider)
$resourceProviders = @($manifestInputLocalizationResources.providers | Sort-Object provider)
if ($semanticLocalizedProviders.Count -ne $resourceProviders.Count) {
    throw 'Build manifest translation semantics and localization resource provider counts differ.'
}
for ($index = 0; $index -lt $resourceProviders.Count; $index++) {
    if (-not $semanticLocalizedProviders[$index].provider.Equals(
            $resourceProviders[$index].provider, [StringComparison]::OrdinalIgnoreCase) -or
        (@($semanticLocalizedProviders[$index].languages) -join '|') -cne
            (@($resourceProviders[$index].languages) -join '|')) {
        throw "Build manifest translation/resource provider differs at index $index."
    }
}
$inputLocalizationError = $null
$currentInputLocalizationState = $null
try {
    $currentInputLocalizationState = Assert-InputLocalizationResourcesCurrent `
        $manifestInputLocalizationResources $manifestInputLocalizationResourceProviders
} catch {
    $inputLocalizationError = $_.Exception.Message
}
$artifactSidecarError = $null
$artifactSidecars = @()
try {
    $artifactSidecars = @(Get-LocalizedSidecarInventory $pluginPath $ArtifactRoot)
    Assert-LocalizedSidecarShape $artifactSidecars 'Artifact localized sidecars'
    Assert-LocalizedSidecarsEqual $manifestSidecars $artifactSidecars 'Artifact localized sidecars'
} catch {
    $artifactSidecarError = $_.Exception.Message
}

if ($FreshnessOnly) {
    $failures = [Collections.Generic.List[string]]::new()
    if ($artifactSidecarError) {
        $failures.Add("localized sidecar artifact differs: $artifactSidecarError")
    }
    if ($inputLocalizationError) {
        $failures.Add("input localization resources differ: $inputLocalizationError")
    }
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
    try {
        [void](Assert-InstalledLocalizedSidecars $manifestSidecars)
    } catch {
        $failures.Add("installed localized sidecar drift: $($_.Exception.Message)")
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
        inputLocalizationResourcesMatch = $true
        localizedSidecarsMatch = $true
        finalWinningSpeedReceiptMatches = $true
        vfsUsed = $false
        filesWritten = 0
    } | ConvertTo-Json
    exit 0
}

if ($artifactSidecarError) {
    throw "Localized sidecar artifact differs: $artifactSidecarError"
}
if ($inputLocalizationError) {
    throw "Input localization resources differ: $inputLocalizationError"
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
$auditArtifactSidecarDigest = Get-LocalizedSidecarDigest $artifactSidecars
$auditInputLocalizationPhysicalDigest = Get-InputLocalizationPhysicalDigest `
    $currentInputLocalizationState.physicalProviders
if ($FinalWinners) {
    $installedSidecars = @(Assert-InstalledLocalizedSidecars $manifestSidecars)
    $auditInstalledSidecarDigest = Get-WinningSidecarDigest $installedSidecars
}
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
Assert-LiveInstanceClaim
Assert-AuditSnapshotUnchanged
Write-Host "PASS: final-winner audit recorded; rerun -FreshnessOnly for the no-write gate."
