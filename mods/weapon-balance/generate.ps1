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

function Get-LocalizedSidecarInventory([string]$PluginPath) {
    $pluginFullPath = [IO.Path]::GetFullPath($PluginPath)
    $pluginDirectory = Split-Path -Parent $pluginFullPath
    $stringsRoot = Join-Path $pluginDirectory 'Strings'
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

function Assert-LocalizedSidecarShape($Inventory, [string]$Context) {
    $rows = @($Inventory)
    if ($rows.Count -eq 0) { throw "$Context emitted no localized sidecars." }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($row in $rows) {
        if (-not $seen.Add([string]$row.relativePath)) {
            throw "$Context has a duplicate localized sidecar path: $($row.relativePath)"
        }
        if ([long]$row.bytes -le 0) {
            throw "$Context has an empty localized sidecar: $($row.relativePath)"
        }
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

function Get-InputResourceLayers {
    $layers = [Collections.Generic.List[object]]::new()
    if ($ExecutionMode -eq 'MO2Vfs') {
        $modlistFile = Join-Path $profileFolder 'modlist.txt'
        if (-not (Test-Path -LiteralPath $modlistFile -PathType Leaf)) {
            throw "MO2 profile modlist is absent: $modlistFile"
        }
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
    }
    $layers.Add([pscustomobject]@{
        root = $DataFolder
        provider = if ($ExecutionMode -eq 'MO2Vfs') { 'game-data' } else { 'offline-data' }
    })
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

function Resolve-InputResourceWinner([string]$RelativePath, $Layers) {
    $normalized = ConvertTo-SafeResourceRelativePath $RelativePath
    foreach ($layer in @($Layers)) {
        if (-not (Test-Path -LiteralPath $layer.root -PathType Container)) { continue }
        $candidate = [IO.Path]::GetFullPath((Join-Path $layer.root $normalized.Replace('/', '\')))
        if (-not (Test-PathWithin $candidate $layer.root) -or
            $candidate.Equals([IO.Path]::GetFullPath($layer.root), [StringComparison]::OrdinalIgnoreCase)) {
            throw "Localization resource path escapes its source layer: $normalized"
        }
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $item = Get-Item -LiteralPath $candidate -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing localization resource winner that is a reparse point: $candidate"
            }
            return [pscustomobject]@{
                relativePath = $normalized
                fullPath = $item.FullName
                provider = $layer.provider
                bytes = [long]$item.Length
                sha256 = Get-Sha256 $item.FullName
            }
        }
    }
    return $null
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
            $relative = "Strings/$($item.Name)"
            $winners[$item.Name] = [pscustomobject]@{
                relativePath = $relative
                fullPath = $item.FullName
                provider = $layer.provider
                bytes = [long]$item.Length
                sha256 = Get-Sha256 $item.FullName
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
    if (@($iniMethod).Count -ne 1) {
        throw 'Pinned Mutagen GetIniListings API shape changed.'
    }
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
        throw 'Candidate audit has no valid input-localization-resource contract.'
    }
    if ((Get-InputLocalizationContractDigest $Contract) -cne [string]$Contract.sha256) {
        throw 'Candidate audit input-localization-resource aggregate hash is invalid.'
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
        if ([string]::IsNullOrWhiteSpace($providerName)) {
            throw 'Input-localization provider has no identity.'
        }
        $providerResolutions = @($resolutions | Where-Object {
            $_.provider.Equals($providerName, [StringComparison]::OrdinalIgnoreCase)
        })
        if ($providerResolutions.Count -ne $candidatePaths.Count) {
            throw "Input-localization candidate/resolution count differs for $providerName."
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
        $looseWinners = @(Get-ProviderLooseResourceWinners $providerName $layers)
        $looseByPath = [Collections.Generic.Dictionary[string, object]]::new(
            [StringComparer]::OrdinalIgnoreCase)
        foreach ($winner in $looseWinners) {
            $looseByPath[$winner.relativePath] = $winner
            $physical.Add([pscustomobject]@{
                provider = $providerName
                kind = 'loose'
                relativePath = $winner.relativePath
                winningProvider = $winner.provider
                bytes = $winner.bytes
                sha256 = $winner.sha256
            })
        }
        foreach ($candidate in $candidatePaths) {
            $relative = ConvertTo-SafeResourceRelativePath ([string]$candidate)
            if (-not $metadata.ContainsKey($relative)) {
                throw "Input-localization candidate lacks resolution metadata: ${providerName}:$relative"
            }
            if ($looseByPath.ContainsKey($relative)) {
                $winner = $looseByPath[$relative]
                $meta = $metadata[$relative]
                $currentLoose.Add([pscustomobject]@{
                    provider = $providerName
                    relativePath = $meta.relativePath
                    language = $meta.language
                    source = $meta.source
                    bytes = $winner.bytes
                    sha256 = $winner.sha256
                })
            }
        }

        $expectedArchives = @($Contract.archives | Where-Object {
            $_.provider.Equals($providerName, [StringComparison]::OrdinalIgnoreCase)
        })
        $expectedByPath = [Collections.Generic.Dictionary[string, object]]::new(
            [StringComparer]::OrdinalIgnoreCase)
        foreach ($expected in $expectedArchives) {
            $relative = ConvertTo-SafeResourceRelativePath ([string]$expected.relativePath)
            if (-not $expectedByPath.TryAdd($relative, $expected)) {
                throw "Duplicate input-localization archive: ${providerName}:$relative"
            }
        }
        foreach ($archive in @(Get-ApplicableArchiveWinners $providerName $archiveSnapshot)) {
            $archiveMatches = Get-ArchiveLocalizationMatches `
                $archive $providerName $metadata $archiveContentCache
            if ($archiveMatches.providerMatches.Count -eq 0) { continue }
            if (-not $archiveHashCache.ContainsKey($archive.fullPath)) {
                $archiveHashCache[$archive.fullPath] = Get-Sha256 $archive.fullPath
            }
            $archive | Add-Member -NotePropertyName sha256 -NotePropertyValue `
                $archiveHashCache[$archive.fullPath] -Force
            $physical.Add([pscustomobject]@{
                provider = $providerName
                kind = 'archive'
                relativePath = $archive.relativePath
                winningProvider = $archive.provider
                bytes = $archive.bytes
                sha256 = $archive.sha256
            })
            if ($archiveMatches.candidateMatches.Count -gt 0) {
                $currentArchives.Add([pscustomobject]@{
                    provider = $providerName
                    relativePath = $archive.relativePath
                    bytes = $archive.bytes
                    sha256 = $archive.sha256
                    matchedEntries = @($archiveMatches.candidateMatches)
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
        $resolution = if ($loose.Count -gt 0) {
            'loose'
        } elseif ($archiveMatches.Count -eq 0) {
            'absent'
        } elseif ($archiveMatches.Count -eq 1) {
            'archive'
        } else {
            'ambiguous-archives'
        }
        $selected = if ($resolution -eq 'loose') {
            "loose:$($loose[0].relativePath)"
        } elseif ($resolution -eq 'archive') {
            "archive:$($archiveMatches[0].relativePath)"
        } else {
            $null
        }
        [pscustomobject]@{
            provider = [string]$expected.provider
            relativePath = [string]$expected.relativePath
            language = [string]$expected.language
            source = [string]$expected.source
            resolution = $resolution
            selectedContainer = $selected
            availableContainers = $available
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
            $expectedContainers = @($expectedRows[$index].availableContainers | Sort-Object)
            $actualContainers = @($actualRows[$index].availableContainers | Sort-Object)
            if (($expectedContainers -join '|') -cne ($actualContainers -join '|')) {
                throw "$Context available containers differ at index $index."
            }
        }
    }
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
    $winningIndex = [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase)
    if ($ExecutionMode -eq 'MO2Vfs') {
        $modlistFile = Join-Path $profileFolder 'modlist.txt'
        if (-not (Test-Path -LiteralPath $modlistFile -PathType Leaf)) {
            throw "MO2 profile modlist is absent: $modlistFile"
        }
        $enabledMods = @(Get-Content -LiteralPath $modlistFile |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_.StartsWith('+') } |
            ForEach-Object { $_.Substring(1) })
        $wanted = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase)
        foreach ($line in $Lines) { [void]$wanted.Add($line.TrimStart('*')) }
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
        # Each snapshot builds one precedence index. MO2's highest-priority
        # enabled layer is encountered first, so later layers cannot replace it.
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
    }
    $inventory = foreach ($line in $Lines) {
        $pluginName = $line.TrimStart('*')
        $winner = $null
        $provider = $null
        if ($ExecutionMode -eq 'MO2Vfs' -and $winningIndex.ContainsKey($pluginName)) {
            $winner = $winningIndex[$pluginName].path
            $provider = $winningIndex[$pluginName].provider
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
    if ($null -ne $script:inputLocalizationResources) {
        $currentLocalization = Assert-InputLocalizationResourcesCurrent `
            $script:inputLocalizationResources $script:inputLocalizationResourceProviders
        if ((Get-InputLocalizationPhysicalDigest $currentLocalization.physicalProviders) -ne
            $script:initialLocalizationResourceProviderDigest) {
            throw 'Input localization resources/providers changed during generation; discard the candidate.'
        }
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
$secondStringsRoot = Join-Path $determinismFolder 'Strings'
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
$localizedStringsRoot = Join-Path (Split-Path -Parent $OutputPath) 'Strings'
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
foreach ($metadataPath in @($SelectionReportPath, $BuildManifestPath)) {
    if (Test-PathWithin $metadataPath $localizedStringsRoot) {
        throw "Metadata output may not occupy the generated localized-sidecar namespace: $metadataPath"
    }
}
$existingLocalizedSidecars = @(Get-LocalizedSidecarInventory $OutputPath)
if ($existingLocalizedSidecars.Count -gt 0 -and -not $ReplaceExistingArtifacts) {
    throw 'Generated localized sidecars already exist; pass -ReplaceExistingArtifacts to replace the exact owned files.'
}
if ($ExecutionMode -eq 'Offline' -and @($requestedOutputs | Where-Object {
        $_.Equals($LoadOrderFile, [StringComparison]::OrdinalIgnoreCase)
    }).Count -gt 0) {
    throw 'An output path aliases the offline load-order input.'
}
$ownedWriteTargets = @(
    $workFolder, $effectiveLoadOrder, $persistence, $generationLog, $auditLog,
    $auditReceiptPath, $determinismFolder, $secondPlugin, $secondReport,
    $secondStringsRoot, $secondPersistence, $secondGenerationLog,
    $localizedStringsRoot, $patcherFolder,
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
foreach ($sidecar in $existingLocalizedSidecars) {
    Assert-NoReparseTraversal $sidecar.fullPath $PSScriptRoot
    Remove-Item -LiteralPath $sidecar.fullPath -Force
}
foreach ($folder in @(
    (Split-Path -Parent $OutputPath),
    (Split-Path -Parent $SelectionReportPath),
    (Split-Path -Parent $BuildManifestPath),
    $localizedStringsRoot,
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
        '--Localize', 'true',
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
$localizedSidecars = @(Get-LocalizedSidecarInventory $OutputPath)
Assert-LocalizedSidecarShape $localizedSidecars 'Primary generation'

foreach ($writeTarget in @($auditReceiptPath, $auditLog)) {
    Assert-NoReparseTraversal $writeTarget $PSScriptRoot
}
Invoke-Patcher $patcher @(
    'audit-build', $DataFolder, $effectiveLoadOrder, $OutputPath,
    $settingsPath, $SelectionReportPath, $auditReceiptPath
) $patcherFolder $auditLog
$audit = Get-Content -Raw -LiteralPath $auditReceiptPath | ConvertFrom-Json
$currentPluginHash = Get-Sha256 $OutputPath
$currentReportHash = Get-Sha256 $SelectionReportPath
if ($audit.schemaVersion -ne 3 -or -not $audit.localized -or
    $audit.pluginSha256 -ne $currentPluginHash -or
    $audit.selectionReportSha256 -ne $currentReportHash -or
    $audit.settingsSha256 -ne (Get-Sha256 $settingsPath)) {
    throw 'Candidate plugin, settings, or selection report changed after semantic audit.'
}
Assert-LocalizedSidecarShape @($audit.localizedSidecars) 'Candidate audit receipt'
Assert-LocalizedSidecarsEqual @($audit.localizedSidecars) $localizedSidecars 'Candidate audit receipt'
$localizedLanguages = @($localizedSidecars.language | Sort-Object -Unique)
if ((@($audit.translationLanguages) -join '|') -cne ($localizedLanguages -join '|')) {
    throw 'Candidate audit translation-language inventory differs from generated sidecars.'
}
$inputTranslationSemantics = $audit.inputTranslationSemantics
if ($null -eq $inputTranslationSemantics -or
    $inputTranslationSemantics.schemaVersion -ne 1 -or
    [string]$inputTranslationSemantics.sha256 -notmatch '^[A-F0-9]{64}$') {
    throw 'Candidate audit has no valid input-translation-semantics receipt.'
}
$inputLocalizationResources = $audit.inputLocalizationResources
$semanticLocalizedProviders = @($inputTranslationSemantics.providers |
    Where-Object sourceUsesLocalization | Sort-Object provider)
$resourceProviders = @($inputLocalizationResources.providers | Sort-Object provider)
if ($semanticLocalizedProviders.Count -ne $resourceProviders.Count) {
    throw 'Input translation semantics and physical localization provider counts differ.'
}
for ($index = 0; $index -lt $resourceProviders.Count; $index++) {
    if (-not $semanticLocalizedProviders[$index].provider.Equals(
            $resourceProviders[$index].provider, [StringComparison]::OrdinalIgnoreCase) -or
        (@($semanticLocalizedProviders[$index].languages) -join '|') -cne
            (@($resourceProviders[$index].languages) -join '|')) {
        throw "Input translation semantics and physical localization provider differ at index $index."
    }
}
$inputLocalizationState = Assert-InputLocalizationResourcesCurrent $inputLocalizationResources
$inputLocalizationResourceProviders = @($inputLocalizationState.physicalProviders)
$initialLocalizationResourceProviderDigest = Get-InputLocalizationPhysicalDigest `
    $inputLocalizationResourceProviders
$currentLocalizedSidecarDigest = Get-LocalizedSidecarDigest $localizedSidecars

if ($VerifyDeterminism) {
    foreach ($writeTarget in @(
        $determinismFolder, $secondPlugin, $secondReport, $secondPersistence,
        $secondStringsRoot, $secondGenerationLog)) {
        Assert-NoReparseTraversal $writeTarget $PSScriptRoot
    }
    foreach ($sidecar in @(Get-LocalizedSidecarInventory $secondPlugin)) {
        Assert-NoReparseTraversal $sidecar.fullPath $PSScriptRoot
        Remove-Item -LiteralPath $sidecar.fullPath -Force
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
            '--Localize', 'true',
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
    $secondLocalizedSidecars = @(Get-LocalizedSidecarInventory $secondPlugin)
    Assert-LocalizedSidecarShape $secondLocalizedSidecars 'Determinism generation'
    Assert-LocalizedSidecarsEqual $localizedSidecars $secondLocalizedSidecars 'Determinism gate'
}

if ($ExecutionMode -eq 'MO2Vfs') { Assert-LiveInstanceClaim }
Assert-InputSnapshotUnchanged
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
    schemaVersion = 3
    generatorVersion = '0.3.0'
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
    localized = $true
    translationLanguages = $localizedLanguages
    localizedSidecars = @($localizedSidecars | ForEach-Object {
        [ordered]@{
            relativePath = $_.relativePath
            language = $_.language
            source = $_.source
            bytes = $_.bytes
            sha256 = $_.sha256
        }
    })
    localizedSidecarsSha256 = $currentLocalizedSidecarDigest
    inputTranslationSemantics = $inputTranslationSemantics
    inputLocalizationResources = $inputLocalizationResources
    inputLocalizationResourceProviders = @($inputLocalizationResourceProviders | ForEach-Object {
        [ordered]@{
            provider = $_.provider
            kind = $_.kind
            relativePath = $_.relativePath
            winningProvider = $_.winningProvider
            bytes = $_.bytes
            sha256 = $_.sha256
        }
    })
    inputLocalizationResourceProvidersSha256 = $initialLocalizationResourceProviderDigest
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
$finalLocalizedSidecars = @(Get-LocalizedSidecarInventory $OutputPath)
Assert-LocalizedSidecarsEqual $localizedSidecars $finalLocalizedSidecars 'Manifest write gate'

Write-Host "Generated and audited $OutputPath"
Write-Host "Plugin SHA256 $(Get-Sha256 $OutputPath)"
Write-Host "Input order $($inputLines.Count) entries, SHA256 $(Get-Sha256 $effectiveLoadOrder)"
Write-Host "Build manifest $BuildManifestPath"
