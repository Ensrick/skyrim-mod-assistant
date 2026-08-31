#Requires -Version 7.4

[CmdletBinding()]
param(
    [string]$StageRoot = "",
    [string]$OutputDirectory = "",
    [string]$Version = "0.1.0-alpha.1",
    [string]$Runtime = "1.7.104.0",
    [switch]$AllowDirty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($StageRoot)) {
    $StageRoot = Join-Path $RepoRoot "build/release/stage"
} elseif (-not [System.IO.Path]::IsPathRooted($StageRoot)) {
    $StageRoot = Join-Path $RepoRoot $StageRoot
}
$StageRoot = [System.IO.Path]::GetFullPath($StageRoot)

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $RepoRoot "build/release/packages"
} elseif (-not [System.IO.Path]::IsPathRooted($OutputDirectory)) {
    $OutputDirectory = Join-Path $RepoRoot $OutputDirectory
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)

if ($Version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$') {
    throw "Version is not a supported semantic-version string: $Version"
}
if ($Runtime -notmatch '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$') {
    throw "Runtime must contain four numeric components: $Runtime"
}
if (-not (Test-Path -LiteralPath $StageRoot -PathType Container)) {
    throw "Staged build is missing: $StageRoot. Run tools/build.bat first."
}

function Write-Utf8NoBomLf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $normalized = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    if (-not $normalized.EndsWith("`n", [System.StringComparison]::Ordinal)) {
        $normalized += "`n"
    }
    [System.IO.File]::WriteAllText(
        $Path,
        $normalized,
        [System.Text.UTF8Encoding]::new($false))
}

function Get-RelativeSlashPath {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Path
    )

    return [System.IO.Path]::GetRelativePath($Base, $Path).Replace('\', '/')
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-FileSha1 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA1).Hash.ToLowerInvariant()
}

function Get-StringSha256 {
    param([Parameter(Mandatory = $true)][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return [System.Convert]::ToHexString($algorithm.ComputeHash($bytes)).ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
    }
}

function Assert-X64Pe {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][bool]$ExpectDll
    )

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 256 -or $bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) {
        throw "Payload is not a valid PE image: $Path"
    }
    $peOffset = [System.BitConverter]::ToInt32($bytes, 0x3C)
    if ($peOffset -lt 0 -or $peOffset + 26 -gt $bytes.Length -or
        $bytes[$peOffset] -ne 0x50 -or $bytes[$peOffset + 1] -ne 0x45 -or
        $bytes[$peOffset + 2] -ne 0 -or $bytes[$peOffset + 3] -ne 0) {
        throw "Payload has an invalid PE header: $Path"
    }
    $machine = [System.BitConverter]::ToUInt16($bytes, $peOffset + 4)
    $optionalMagic = [System.BitConverter]::ToUInt16($bytes, $peOffset + 24)
    $characteristics = [System.BitConverter]::ToUInt16($bytes, $peOffset + 22)
    $isDll = ($characteristics -band 0x2000) -ne 0
    if ($machine -ne 0x8664 -or $optionalMagic -ne 0x020B) {
        throw "Payload is not a 64-bit PE32+ image: $Path"
    }
    if ($isDll -ne $ExpectDll) {
        $expectedKind = if ($ExpectDll) { "DLL" } else { "executable" }
        throw "Payload PE kind does not match expected ${expectedKind}: $Path"
    }
}

function Test-IsPortableExecutable {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::Read)
    try {
        if ($stream.Length -lt 64) {
            return $false
        }
        $header = [byte[]]::new(64)
        if ($stream.Read($header, 0, $header.Length) -ne $header.Length -or
            $header[0] -ne 0x4D -or $header[1] -ne 0x5A) {
            return $false
        }
        $peOffset = [System.BitConverter]::ToInt32($header, 0x3C)
        if ($peOffset -lt 0 -or [long]$peOffset + 4 -gt $stream.Length) {
            return $false
        }
        $null = $stream.Seek($peOffset, [System.IO.SeekOrigin]::Begin)
        $signature = [byte[]]::new(4)
        return $stream.Read($signature, 0, $signature.Length) -eq $signature.Length -and
            $signature[0] -eq 0x50 -and $signature[1] -eq 0x45 -and
            $signature[2] -eq 0 -and $signature[3] -eq 0
    } finally {
        $stream.Dispose()
    }
}

function Get-GitValue {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $result = & git -C $RepoRoot @Arguments 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        return (($result | Out-String).Trim())
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

function Get-CmakeCacheValue {
    param(
        [Parameter(Mandatory = $true)][string]$CachePath,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (-not (Test-Path -LiteralPath $CachePath -PathType Leaf)) {
        throw "CMake cache is missing: $CachePath"
    }
    $pattern = '^' + [System.Text.RegularExpressions.Regex]::Escape($Name) + ':[^=]*=(.*)$'
    $matchingLines = @(Get-Content -LiteralPath $CachePath | Where-Object { $_ -match $pattern })
    if ($matchingLines.Count -gt 1) {
        throw "CMake cache contains more than one '$Name' entry."
    }
    if ($matchingLines.Count -eq 0) {
        return $null
    }
    $null = $matchingLines[0] -match $pattern
    return $Matches[1]
}

function Assert-NoReparseAncestors {
    param([Parameter(Mandatory = $true)][string]$Path)

    $currentPath = [System.IO.Path]::GetFullPath($Path)
    while ($true) {
        $item = Get-Item -LiteralPath $currentPath -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not permitted in release source paths: $currentPath"
        }
        $parent = [System.IO.Directory]::GetParent($currentPath)
        if ($null -eq $parent) {
            break
        }
        $currentPath = $parent.FullName
    }
}

function Assert-NoReparsePoints {
    param([Parameter(Mandatory = $true)][string]$Root)

    Assert-NoReparseAncestors -Path $Root
    $rootItem = Get-Item -LiteralPath $Root -Force
    if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Reparse-point source root is not permitted: $Root"
    }
    foreach ($item in Get-ChildItem -LiteralPath $Root -Force -Recurse) {
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not permitted in release source inputs: $($item.FullName)"
        }
    }
}

function Assert-SafeContainedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $normalizedRoot = [System.IO.Path]::GetFullPath($Root)
    Assert-NoReparseAncestors -Path $normalizedRoot
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $normalizedRoot $RelativePath))
    if (-not $candidate.StartsWith(
            $normalizedRoot + [System.IO.Path]::DirectorySeparatorChar,
            [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe source path escapes its root: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Required source file is missing: $candidate"
    }
    $currentPath = $candidate
    while ($true) {
        $item = Get-Item -LiteralPath $currentPath -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not permitted in source paths: $currentPath"
        }
        if ($currentPath.TrimEnd('\', '/') -ieq $normalizedRoot.TrimEnd('\', '/')) {
            break
        }
        $parentPath = Split-Path -Parent $currentPath
        if ([string]::IsNullOrWhiteSpace($parentPath) -or $parentPath -eq $currentPath) {
            throw "Unable to prove the source path remains below its root: $candidate"
        }
        $currentPath = $parentPath
    }
    return $candidate
}

function Get-TreeFingerprint {
    param([Parameter(Mandatory = $true)][string]$Root)

    Assert-NoReparsePoints -Root $Root
    $normalizedRoot = [System.IO.Path]::GetFullPath($Root)
    [string[]]$relativePaths = @([System.IO.Directory]::EnumerateFiles(
            $normalizedRoot,
            '*',
            [System.IO.SearchOption]::AllDirectories) | ForEach-Object {
            Get-RelativeSlashPath -Base $normalizedRoot -Path $_
        })
    [System.Array]::Sort[string]($relativePaths, [System.StringComparer]::Ordinal)
    [string[]]$manifestLines = @(foreach ($relativePath in $relativePaths) {
        $source = Assert-SafeContainedFile -Root $normalizedRoot -RelativePath $relativePath
        "$(Get-FileSha256 -Path $source)  $relativePath"
    })
    $manifestText = if ($manifestLines.Count -eq 0) {
        ""
    } else {
        ($manifestLines -join "`n") + "`n"
    }
    return [ordered]@{
        fileCount = $relativePaths.Count
        sha256 = Get-StringSha256 -Value $manifestText
        manifestLines = @($manifestLines)
    }
}

function Copy-DirectoryTree {
    param(
        [Parameter(Mandatory = $true)][string]$SourceRoot,
        [Parameter(Mandatory = $true)][string]$DestinationRoot
    )

    $fingerprint = Get-TreeFingerprint -Root $SourceRoot
    foreach ($line in $fingerprint.manifestLines) {
        if ($line -notmatch '^[0-9a-f]{64}  (.+)$') {
            throw "Internal source-tree manifest format failure: $line"
        }
        $relativePath = $Matches[1]
        $source = Assert-SafeContainedFile -Root $SourceRoot -RelativePath $relativePath
        $destination = Join-Path $DestinationRoot $relativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }
    $copiedFingerprint = Get-TreeFingerprint -Root $DestinationRoot
    if ($copiedFingerprint.fileCount -ne $fingerprint.fileCount -or
        $copiedFingerprint.sha256 -ne $fingerprint.sha256) {
        throw "Copied source tree does not match its input: $SourceRoot"
    }
    return $fingerprint
}

function Copy-GitTrackedFiles {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$DestinationRoot,
        [hashtable]$AllowedGitlinks = @{},
        [string[]]$Pathspec = @('.'),
        [string]$StripPrefix = '',
        [switch]$RequireIndexBytes
    )

    $repositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
    Assert-NoReparseAncestors -Path $repositoryRoot
    $lines = @(& git -C $repositoryRoot ls-files -s -- $Pathspec)
    if ($LASTEXITCODE -ne 0 -or $lines.Count -eq 0) {
        throw "Unable to enumerate tracked source in $repositoryRoot"
    }
    $excludedGitlinks = @()
    foreach ($line in $lines) {
        if ($line -notmatch '^(\d{6}) ([0-9a-f]{40,64}) \d+\t(.+)$') {
            throw "Unexpected git index entry in ${repositoryRoot}: $line"
        }
        $mode = $Matches[1]
        $objectId = $Matches[2]
        $relativePath = $Matches[3].Replace('\', '/')
        if ($mode -eq '160000') {
            if (-not $AllowedGitlinks.ContainsKey($relativePath) -or
                [string]$AllowedGitlinks[$relativePath] -ne $objectId) {
                throw "Unreviewed or mismatched gitlink in source input: $relativePath@$objectId"
            }
            $excludedGitlinks += $relativePath
            continue
        }
        if ($mode -notin @('100644', '100755', '120000')) {
            throw "Unsupported git file mode $mode for $relativePath"
        }

        $source = Assert-SafeContainedFile -Root $repositoryRoot -RelativePath $relativePath
        if ($RequireIndexBytes) {
            $workingObjectId = (& git -C $repositoryRoot hash-object -- $relativePath).Trim()
            if ($LASTEXITCODE -ne 0 -or $workingObjectId -ne $objectId) {
                throw "Tracked dependency source differs from its pinned index: $relativePath"
            }
        }
        $destinationRelativePath = $relativePath
        if (-not [string]::IsNullOrWhiteSpace($StripPrefix)) {
            $normalizedPrefix = $StripPrefix.Replace('\', '/').TrimEnd('/') + '/'
            if (-not $relativePath.StartsWith($normalizedPrefix, [System.StringComparison]::Ordinal)) {
                throw "Tracked path does not have the required strip prefix '$normalizedPrefix': $relativePath"
            }
            $destinationRelativePath = $relativePath.Substring($normalizedPrefix.Length)
            if ([string]::IsNullOrWhiteSpace($destinationRelativePath)) {
                throw "Tracked source path became empty after prefix removal: $relativePath"
            }
        }
        $destination = Join-Path $DestinationRoot $destinationRelativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }
    return @($excludedGitlinks)
}

function Read-VcpkgStatusEntries {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "vcpkg installed status database is missing: $Path"
    }
    $normalized = (Get-Content -LiteralPath $Path -Raw).Replace("`r`n", "`n").Replace("`r", "`n")
    $entries = @()
    foreach ($paragraph in ($normalized -split "`n{2,}")) {
        if ([string]::IsNullOrWhiteSpace($paragraph)) {
            continue
        }
        $entry = [ordered]@{}
        $lastKey = $null
        foreach ($line in ($paragraph -split "`n")) {
            if ($line -match '^([^:]+):\s?(.*)$') {
                $lastKey = $Matches[1]
                $entry[$lastKey] = $Matches[2]
            } elseif ($line -match '^\s+(.*)$' -and $null -ne $lastKey) {
                $entry[$lastKey] = [string]$entry[$lastKey] + "`n" + $Matches[1]
            } else {
                throw "Malformed vcpkg status line: $line"
            }
        }
        $entries += $entry
    }
    return $entries
}

function ConvertTo-VcpkgStatusParagraph {
    param([Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary]$Entry)

    $lines = foreach ($key in $Entry.Keys) {
        $valueLines = ([string]$Entry[$key]).Split("`n")
        "${key}: $($valueLines[0])"
        foreach ($continuation in ($valueLines | Select-Object -Skip 1)) {
            " $continuation"
        }
    }
    return ($lines -join "`n") + "`n"
}

function Resolve-VcpkgRoot {
    param([Parameter(Mandatory = $true)][string]$CachePath)

    $records = @()
    foreach ($candidate in @(
            [ordered]@{ source = 'VCPKG_ROOT'; value = $env:VCPKG_ROOT },
            [ordered]@{ source = 'BE_VCPKG_ROOT'; value = $env:BE_VCPKG_ROOT },
            [ordered]@{ source = 'CMakeCache:Z_VCPKG_ROOT_DIR'; value = Get-CmakeCacheValue -CachePath $CachePath -Name 'Z_VCPKG_ROOT_DIR' })) {
        if (-not [string]::IsNullOrWhiteSpace([string]$candidate.value)) {
            if (-not [System.IO.Path]::IsPathRooted([string]$candidate.value)) {
                throw "Vcpkg root candidate is not absolute ($($candidate.source)): $($candidate.value)"
            }
            $records += [ordered]@{
                source = $candidate.source
                path = [System.IO.Path]::GetFullPath([string]$candidate.value)
            }
        }
    }

    $toolchain = Get-CmakeCacheValue -CachePath $CachePath -Name 'CMAKE_TOOLCHAIN_FILE'
    if (-not [string]::IsNullOrWhiteSpace($toolchain)) {
        $toolchainPath = [System.IO.Path]::GetFullPath($toolchain)
        $toolchainRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $toolchainPath))
        $records += [ordered]@{
            source = 'CMakeCache:CMAKE_TOOLCHAIN_FILE'
            path = [System.IO.Path]::GetFullPath($toolchainRoot)
        }
    }
    if ($records.Count -eq 0) {
        throw "Unable to resolve VCPKG_ROOT from the environment or CMake cache."
    }

    $groups = @($records | Group-Object { ([string]$_.path).TrimEnd('\', '/').ToLowerInvariant() })
    if ($groups.Count -ne 1) {
        $details = ($records | ForEach-Object { "$($_.source)=$($_.path)" }) -join '; '
        throw "Ambiguous or mismatched VCPKG_ROOT candidates: $details"
    }
    $resolved = [System.IO.Path]::GetFullPath([string]$records[0].path)
    if (-not (Test-Path -LiteralPath $resolved -PathType Container) -or
        -not (Test-Path -LiteralPath (Join-Path $resolved 'scripts/buildsystems/vcpkg.cmake') -PathType Leaf)) {
        throw "Resolved VCPKG_ROOT is not a complete vcpkg checkout: $resolved"
    }
    Assert-NoReparseAncestors -Path $resolved
    return $resolved
}

function New-DeterministicZip {
    param(
        [Parameter(Mandatory = $true)][string]$PayloadRoot,
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][System.DateTimeOffset]$Timestamp
    )

    Add-Type -AssemblyName System.IO.Compression
    $stream = [System.IO.File]::Open(
        $ArchivePath,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $stream,
            [System.IO.Compression.ZipArchiveMode]::Create,
            $false)
        try {
            $files = Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse |
                Sort-Object { Get-RelativeSlashPath -Base $PayloadRoot -Path $_.FullName }
            foreach ($file in $files) {
                $relativePath = Get-RelativeSlashPath -Base $PayloadRoot -Path $file.FullName
                $entry = $archive.CreateEntry(
                    $relativePath,
                    [System.IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = $Timestamp
                $entry.ExternalAttributes = 0

                $inputStream = [System.IO.File]::OpenRead($file.FullName)
                $output = $entry.Open()
                try {
                    $inputStream.CopyTo($output)
                } finally {
                    $output.Dispose()
                    $inputStream.Dispose()
                }
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

function Assert-DeterministicZipMetadata {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][System.DateTimeOffset]$ExpectedTimestamp
    )

    $stream = [System.IO.File]::OpenRead($ArchivePath)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $stream,
            [System.IO.Compression.ZipArchiveMode]::Read,
            $false)
        try {
            if ($archive.Entries.Count -eq 0) {
                throw "Deterministic ZIP contains no entries: $ArchivePath"
            }
            foreach ($entry in $archive.Entries) {
                $actual = $entry.LastWriteTime
                if ($actual.Year -ne $ExpectedTimestamp.Year -or
                    $actual.Month -ne $ExpectedTimestamp.Month -or
                    $actual.Day -ne $ExpectedTimestamp.Day -or
                    $actual.Hour -ne $ExpectedTimestamp.Hour -or
                    $actual.Minute -ne $ExpectedTimestamp.Minute -or
                    $actual.Second -ne $ExpectedTimestamp.Second -or
                    $entry.ExternalAttributes -ne 0) {
                    throw "ZIP metadata is not normalized for entry $($entry.FullName) in $ArchivePath"
                }
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

$versionHeader = Get-Content -LiteralPath (Join-Path $RepoRoot "src/Version.h") -Raw
if ($versionHeader -notmatch 'Semantic\s*=\s*"([^"]+)"' -or $Matches[1] -ne $Version) {
    throw "Package version '$Version' does not match src/Version.h."
}
$runtimeComponents = $Runtime.Split('.')
$runtimePattern = 'SupportedRuntime\s*\{\s*' + (($runtimeComponents | ForEach-Object {
    [System.Text.RegularExpressions.Regex]::Escape($_)
}) -join '\s*,\s*') + '\s*\}'
if ($versionHeader -notmatch $runtimePattern) {
    throw "Package runtime '$Runtime' does not match src/Version.h."
}
$vcpkgManifestForVersion = Get-Content -LiteralPath (Join-Path $RepoRoot "vcpkg.json") -Raw |
    ConvertFrom-Json
if ([string]$vcpkgManifestForVersion.'version-string' -ne $Version) {
    throw "Package version '$Version' does not match vcpkg.json."
}
$cmakeSource = Get-Content -LiteralPath (Join-Path $RepoRoot "CMakeLists.txt") -Raw
$baseVersion = $Version.Split('-')[0]
if ($cmakeSource -notmatch 'project\(BoundedEncounters\s+VERSION\s+([0-9]+\.[0-9]+\.[0-9]+)\b' -or
    $Matches[1] -ne $baseVersion) {
    throw "Package base version '$baseVersion' does not match CMakeLists.txt."
}

$commit = Get-GitValue -Arguments @("rev-parse", "HEAD")
$status = Get-GitValue -Arguments @("status", "--porcelain=v1", "--untracked-files=normal")
$isDirty = [string]::IsNullOrWhiteSpace($commit) -or -not [string]::IsNullOrWhiteSpace($status)
if ($isDirty -and -not $AllowDirty) {
    throw "Release packaging requires a clean Git commit. Commit the release inputs or pass -AllowDirty for a non-release local artifact."
}
$binaryCacheDisabled = $env:VCPKG_BINARY_SOURCES -ceq "clear"
if (-not $binaryCacheDisabled) {
    if (-not $AllowDirty) {
        throw "Release packaging requires VCPKG_BINARY_SOURCES=clear so the reviewed dependency build cannot restore binary-cache packages."
    }
    Write-Warning "VCPKG_BINARY_SOURCES is not exactly 'clear'; this engineering package is not release eligible."
}
$releaseEligible = -not $AllowDirty -and -not $isDirty -and $binaryCacheDisabled
if ([string]::IsNullOrWhiteSpace($commit)) {
    $commit = "UNCOMMITTED"
}

$epoch = 0L
if (-not [string]::IsNullOrWhiteSpace($env:SOURCE_DATE_EPOCH)) {
    if (-not [long]::TryParse($env:SOURCE_DATE_EPOCH, [ref]$epoch) -or $epoch -lt 0) {
        throw "SOURCE_DATE_EPOCH must be a non-negative integer."
    }
} else {
    $commitEpoch = Get-GitValue -Arguments @("show", "-s", "--format=%ct", "HEAD")
    if ([string]::IsNullOrWhiteSpace($commitEpoch) -or
        -not [long]::TryParse($commitEpoch, [ref]$epoch) -or $epoch -lt 0) {
        $epoch = 0L
    }
}

$sourceTimestamp = [System.DateTimeOffset]::FromUnixTimeSeconds($epoch).ToUniversalTime()
$minimumZipTimestamp = [System.DateTimeOffset]::new(
    1980, 1, 1, 0, 0, 0, [System.TimeSpan]::Zero)
$zipTimestamp = $minimumZipTimestamp

$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$workRoot = Join-Path $temporaryBase ("BoundedEncounters-package-" + [System.Guid]::NewGuid().ToString("N"))
$payloadRoot = Join-Path $workRoot "payload"
$correspondingSourcePayloadRoot = Join-Path $workRoot "corresponding-source"

New-Item -ItemType Directory -Path $payloadRoot,$correspondingSourcePayloadRoot -Force | Out-Null
try {
    $payload = @(
        [ordered]@{ source = "SKSE/Plugins/BoundedEncounters.dll"; destination = "SKSE/Plugins/BoundedEncounters.dll" },
        [ordered]@{ source = "SKSE/Plugins/BoundedEncounters.json"; destination = "SKSE/Plugins/BoundedEncounters.json" },
        [ordered]@{ source = "SKSE/Plugins/BoundedEncounters.schema.json"; destination = "SKSE/Plugins/BoundedEncounters.schema.json" },
        [ordered]@{ source = "tools/BoundedEncounters.Simulate.exe"; destination = "tools/BoundedEncounters.Simulate.exe" },
        [ordered]@{ source = "LICENSE"; destination = "LICENSE" },
        [ordered]@{ source = "README.md"; destination = "README.md" }
    )

    foreach ($item in $payload) {
        $source = Join-Path $StageRoot $item.source
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Required staged payload is missing: $($item.source)"
        }
        $destination = Join-Path $payloadRoot $item.destination
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }

    Assert-X64Pe -Path (Join-Path $payloadRoot "SKSE/Plugins/BoundedEncounters.dll") -ExpectDll $true
    Assert-X64Pe -Path (Join-Path $payloadRoot "tools/BoundedEncounters.Simulate.exe") -ExpectDll $false

    foreach ($sourceControlledFile in @(
            [ordered]@{ staged = "SKSE/Plugins/BoundedEncounters.json"; repository = "config/BoundedEncounters.json" },
            [ordered]@{ staged = "SKSE/Plugins/BoundedEncounters.schema.json"; repository = "config/BoundedEncounters.schema.json" },
            [ordered]@{ staged = "LICENSE"; repository = "LICENSE" },
            [ordered]@{ staged = "README.md"; repository = "README.md" })) {
        $stagedHash = Get-FileSha256 -Path (Join-Path $payloadRoot $sourceControlledFile.staged)
        $repositoryHash = Get-FileSha256 -Path (Join-Path $RepoRoot $sourceControlledFile.repository)
        if ($stagedHash -ne $repositoryHash) {
            throw "Staged file is stale or modified: $($sourceControlledFile.staged). Rebuild before packaging."
        }
    }

    $shippingConfigPath = Join-Path $payloadRoot "SKSE/Plugins/BoundedEncounters.json"
    $shippingSchemaPath = Join-Path $payloadRoot "SKSE/Plugins/BoundedEncounters.schema.json"
    $shippingConfigJson = Get-Content -LiteralPath $shippingConfigPath -Raw
    $shippingSchemaJson = Get-Content -LiteralPath $shippingSchemaPath -Raw
    $shippingSchema = $shippingSchemaJson | ConvertFrom-Json
    if ([string]$shippingSchema.'$schema' -cne "https://json-schema.org/draft/2020-12/schema") {
        throw "Shipping schema must declare JSON Schema Draft 2020-12."
    }
    try {
        $shippingSchemaValid = $shippingConfigJson |
            Test-Json -SchemaFile $shippingSchemaPath -ErrorAction Stop
    } catch {
        throw "Shipping configuration failed its declared Draft 2020-12 JSON Schema: $($_.Exception.Message)"
    }
    if (-not $shippingSchemaValid) {
        throw "Shipping configuration failed its declared Draft 2020-12 JSON Schema."
    }
    $testJsonCommand = Get-Command Test-Json -ErrorAction Stop
    $testJsonAssembly = $testJsonCommand.ImplementingType.Assembly
    $jsonSchemaNetReferences = @($testJsonAssembly.GetReferencedAssemblies() |
        Where-Object { $_.Name -eq 'JsonSchema.Net' })
    if ($jsonSchemaNetReferences.Count -ne 1) {
        throw "Test-Json is not backed by the reviewed JsonSchema.NET implementation."
    }
    $schemaValidationEvidence = [ordered]@{
        draft = "https://json-schema.org/draft/2020-12/schema"
        engine = "PowerShell Test-Json (JsonSchema.NET)"
        powershellVersion = $PSVersionTable.PSVersion.ToString()
        implementingAssembly = $testJsonAssembly.GetName().Name
        implementingAssemblyVersion = $testJsonAssembly.GetName().Version.ToString()
        jsonSchemaNetVersion = $jsonSchemaNetReferences[0].Version.ToString()
        valid = $true
    }
    $shippingConfig = $shippingConfigJson | ConvertFrom-Json
    $expectedAllowedSourcePlugins = @(
        "Skyrim.esm",
        "Update.esm",
        "Dawnguard.esm",
        "HearthFires.esm",
        "Dragonborn.esm"
    )
    $shippingAllowedSourcePlugins = @($shippingConfig.allowedSourcePlugins)
    if ($shippingConfig.schemaVersion -ne 1 -or
        $shippingConfig.enabled -ne $true -or
        $shippingConfig.observeOnly -ne $true -or
        $shippingConfig.debugLogging -ne $false -or
        [double]$shippingConfig.limits.maximumNavmeshSnapDistance -ne 256.0 -or
        $shippingAllowedSourcePlugins.Count -ne $expectedAllowedSourcePlugins.Count) {
        throw "The alpha package requires enabled observe-only schema 1 defaults, debug logging off, the reviewed 256-unit navmesh-snap bound, and the official-master source allowlist."
    }
    for ($index = 0; $index -lt $expectedAllowedSourcePlugins.Count; ++$index) {
        if ([string]$shippingAllowedSourcePlugins[$index] -cne $expectedAllowedSourcePlugins[$index]) {
            throw "The alpha package source allowlist does not match the reviewed official-master order."
        }
    }

    $repositoryPayload = @(
        [ordered]@{ source = "THIRD-PARTY-NOTICES.md"; destination = "THIRD-PARTY-NOTICES.md" },
        [ordered]@{ source = "docs/architecture.md"; destination = "docs/architecture.md" },
        [ordered]@{ source = "docs/configuration.md"; destination = "docs/configuration.md" },
        [ordered]@{ source = "docs/compatibility.md"; destination = "docs/compatibility.md" },
        [ordered]@{ source = "docs/save-lifecycle.md"; destination = "docs/save-lifecycle.md" },
        [ordered]@{ source = "docs/test-plan.md"; destination = "docs/test-plan.md" },
        [ordered]@{ source = "docs/release/artifacts.md"; destination = "docs/release/artifacts.md" },
        [ordered]@{ source = "docs/release/nexus-prerelease-checklist.md"; destination = "docs/release/nexus-prerelease-checklist.md" }
    )
    foreach ($item in $repositoryPayload) {
        $source = Join-Path $RepoRoot $item.source
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Required repository payload is missing: $($item.source)"
        }
        $destination = Join-Path $payloadRoot $item.destination
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }

    $forbidden = Get-ChildItem -LiteralPath $payloadRoot -File -Recurse |
        Where-Object { $_.Extension.ToLowerInvariant() -in @(
            ".bsa", ".esm", ".esp", ".esl", ".pdb", ".lib", ".exp", ".obj", ".log", ".sav") }
    if ($forbidden) {
        $paths = ($forbidden | ForEach-Object {
            Get-RelativeSlashPath -Base $payloadRoot -Path $_.FullName
        }) -join ", "
        throw "Forbidden payload file type detected: $paths"
    }

    $commonLibCommit = Get-GitValue -Arguments @("-C", "extern/CommonLibSSE-NG", "rev-parse", "HEAD")
    if ([string]::IsNullOrWhiteSpace($commonLibCommit)) {
        $commonLibCommit = "NOASSERTION"
    }
    $commonLibParentCommit = Get-GitValue -Arguments @(
        "-C", "extern/CommonLibSSE-NG", "rev-parse", "HEAD^")
    $expectedCommonLibCommit = "a9d7d4523d5e1abc8b296bd99683b7df11df652f"
    $expectedCommonLibUpstreamCommit = "8b032fa992750d654d6d38a33731714d8b86be1f"
    $expectedCommonLibForkRepository = "https://github.com/Ensrick/CommonLibSSE-NG.git"
    $commonLibUpstreamTag = Get-GitValue -Arguments @(
        "-C", "extern/CommonLibSSE-NG", "describe", "--tags", "--exact-match", $expectedCommonLibUpstreamCommit)
    $gitTopLevel = Get-GitValue -Arguments @("rev-parse", "--show-toplevel")
    if ([string]::IsNullOrWhiteSpace($gitTopLevel)) {
        throw "Unable to resolve the Git top-level directory."
    }
    $gitModulesPath = Join-Path $gitTopLevel ".gitmodules"
    $commonLibSubmoduleUrl = Get-GitValue -Arguments @(
        "config", "-f", $gitModulesPath, "--get", "submodule.mods/bounded-encounters/extern/CommonLibSSE-NG.url")
    if ([string]::IsNullOrWhiteSpace($commonLibSubmoduleUrl)) {
        $commonLibSubmoduleUrl = Get-GitValue -Arguments @(
            "config", "-f", $gitModulesPath, "--get", "submodule.extern/CommonLibSSE-NG.url")
    }
    if ($commonLibCommit -ne $expectedCommonLibCommit -or
        $commonLibParentCommit -ne $expectedCommonLibUpstreamCommit -or
        $commonLibUpstreamTag -ne "v7.0.0" -or
        $commonLibSubmoduleUrl -ne $expectedCommonLibForkRepository) {
        throw "CommonLibSSE-NG pin does not match the reviewed Ensrick fork commit and upstream v7.0.0 base."
    }

    foreach ($licenseFile in @(
            [ordered]@{ source = "COPYING"; destination = "licenses/CommonLibSSE-NG/COPYING" },
            [ordered]@{ source = "EXCEPTIONS.md"; destination = "licenses/CommonLibSSE-NG/EXCEPTIONS.md" },
            [ordered]@{ source = "licenses/LICENSE-MIT"; destination = "licenses/CommonLibSSE-NG/LICENSE-MIT" },
            [ordered]@{ source = "licenses/README.md"; destination = "licenses/CommonLibSSE-NG/LICENSES-README.md" })) {
        $source = Join-Path $RepoRoot ("extern/CommonLibSSE-NG/" + $licenseFile.source)
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Required CommonLibSSE-NG licensing file is missing: $($licenseFile.source)"
        }
        $destination = Join-Path $payloadRoot $licenseFile.destination
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }

    $vcpkgConfiguration = Get-Content -LiteralPath (Join-Path $RepoRoot "vcpkg-configuration.json") -Raw |
        ConvertFrom-Json
    $vcpkgBaseline = [string]$vcpkgConfiguration.'default-registry'.baseline
    $expectedVcpkgBaseline = "fab1c6dc7a944372a90a1e19ab5e8e32cd658fc2"
    if ($vcpkgBaseline -ne $expectedVcpkgBaseline -or
        [string]$vcpkgConfiguration.'default-registry'.repository -ne "https://github.com/microsoft/vcpkg" -or
        [string]$vcpkgConfiguration.'default-registry'.kind -ne "git") {
        throw "vcpkg registry configuration does not match the reviewed release baseline."
    }

    $triplet = "x64-windows-static-md"
    $cmakeCachePath = Join-Path $RepoRoot "build/release/CMakeCache.txt"
    if ((Get-CmakeCacheValue -CachePath $cmakeCachePath -Name "VCPKG_TARGET_TRIPLET") -ne $triplet) {
        throw "CMake cache does not identify the reviewed vcpkg target triplet: $triplet"
    }
    $expectedInstalledRoot = [System.IO.Path]::GetFullPath(
        (Join-Path $RepoRoot "build/release/vcpkg_installed"))
    $cachedInstalledRoot = Get-CmakeCacheValue -CachePath $cmakeCachePath -Name "VCPKG_INSTALLED_DIR"
    if ([string]::IsNullOrWhiteSpace($cachedInstalledRoot)) {
        $cachedInstalledRoot = Get-CmakeCacheValue -CachePath $cmakeCachePath -Name "_VCPKG_INSTALLED_DIR"
    }
    if ([string]::IsNullOrWhiteSpace($cachedInstalledRoot) -or
        [System.IO.Path]::GetFullPath($cachedInstalledRoot) -ne $expectedInstalledRoot) {
        throw "CMake cache vcpkg installation root does not match build/release/vcpkg_installed."
    }

    $vcpkgRoot = Resolve-VcpkgRoot -CachePath $cmakeCachePath
    $vcpkgGitTopLevel = (& git -C $vcpkgRoot rev-parse --show-toplevel).Trim()
    $vcpkgCommit = (& git -C $vcpkgRoot rev-parse HEAD).Trim()
    $vcpkgStatus = (& git -C $vcpkgRoot status --porcelain=v1 --untracked-files=no | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or
        [System.IO.Path]::GetFullPath($vcpkgGitTopLevel) -ne [System.IO.Path]::GetFullPath($vcpkgRoot) -or
        $vcpkgCommit -ne $expectedVcpkgBaseline -or
        -not [string]::IsNullOrWhiteSpace($vcpkgStatus)) {
        throw "VCPKG_ROOT must be a clean checkout at the reviewed baseline $expectedVcpkgBaseline."
    }

    $vcpkgManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "vcpkg.json") -Raw |
        ConvertFrom-Json
    $expectedDependencies = @(
        [ordered]@{
            name = "directxmath"; version = "2026-06-12"; portVersion = 0; license = "MIT"
            portTree = "46a960c8f364162407b24f188a2aeea4608f4cf7"
            sourcePattern = '^jun2026-[0-9a-f]{10}\.clean$'; sourceFileCount = 87
            sourceTreeSha256 = "c82d46eba86d9a98602340c6492e6ee243a94d77451bb7f174d1544efa1a9c1c"
        },
        [ordered]@{
            name = "directxtk"; version = "2026-05-07"; portVersion = 1; license = "MIT"
            portTree = "2bd837ddca7efd128c2db51fe75993737c92451c"
            sourcePattern = '^may2026-[0-9a-f]{10}\.clean$'; sourceFileCount = 227
            sourceTreeSha256 = "47634c06605bf54a7e68bcc55482b63a74147f8a26f58a3d4e91d7c4f85891e7"
        },
        [ordered]@{
            name = "fmt"; version = "12.2.0"; portVersion = 0; license = "MIT"
            portTree = "823af43db9df2c4be15c4331b36b3cc419afa02c"
            sourcePattern = '^12\.2\.0-[0-9a-f]{10}\.clean$'; sourceFileCount = 142
            sourceTreeSha256 = "96137451412e2a3efe9f402e7aa002cf9916d00b8b5fd2a5654a7e08b7884342"
        },
        [ordered]@{
            name = "nlohmann-json"; version = "3.12.0"; portVersion = 2; license = "MIT"
            portTree = "ac3b8821cf486e45dd543bef2a4ba1d1ba230258"
            sourcePattern = '^v3\.12\.0-[0-9a-f]{10}\.clean$'; sourceFileCount = 1163
            sourceTreeSha256 = "f0ffac2eddc982a07b07f9c8e601175d5d2e1f8eafa671b6b885b3ae0ea5875b"
        },
        [ordered]@{
            name = "rapidcsv"; version = "8.99"; portVersion = 0; license = "BSD-3-Clause"
            portTree = "16013fe8f02522b49064d1170099b921e1d476ac"
            sourcePattern = '^v8\.99-[0-9a-f]{10}\.clean$'; sourceFileCount = 159
            sourceTreeSha256 = "6a6454fe758bdca3914747b839283af3b49759568ebda02b714bcf0551c3a512"
        },
        [ordered]@{
            name = "simpleini"; version = "4.26"; portVersion = 0; license = "MIT"
            portTree = "11e04f01aa0c87a74f9581cc81358e373dcbd317"
            sourcePattern = '^v4\.26-[0-9a-f]{10}\.clean$'; sourceFileCount = 38
            sourceTreeSha256 = "e9ea33c8f66c2a3d93fdf8ac8521f0746e38f4d39aca0ce4f295c146b20eac4d"
        },
        [ordered]@{
            name = "spdlog"; version = "1.17.0"; portVersion = 1; license = "MIT"
            portTree = "c42bb1e74ab55b299d7fe52e68d0ab7b5dee165c"
            sourcePattern = '^v1\.17\.0-[0-9a-f]{10}\.clean$'; sourceFileCount = 177
            sourceTreeSha256 = "b7cb21c50d4b657b231657f8104d76360a6ee3125ffb3fbc3f793474782e8c1a"
        },
        [ordered]@{
            name = "xbyak"; version = "7.28"; portVersion = 0; license = "BSD-3-Clause"
            portTree = "fe843e85888a7fa80dddd77627ee4f0572fbd9b4"
            sourcePattern = '^v7\.28-[0-9a-f]{10}\.clean$'; sourceFileCount = 149
            sourceTreeSha256 = "371161b17c138003496e267932eebe937b296512d040b2868e081a85ec542343"
        }
    )
    $helperTriplet = "x64-windows"
    $expectedBuildHelpers = @(
        [ordered]@{
            name = "vcpkg-cmake"; version = "2024-04-23"; portVersion = 0; license = "MIT"
            portTree = "e74aa1e8f93278a8e71372f1fa08c3df420eb840"
            controlScripts = @(
                "vcpkg-port-config.cmake",
                "vcpkg_cmake_build.cmake",
                "vcpkg_cmake_configure.cmake",
                "vcpkg_cmake_install.cmake")
            copyrightSource = "vcpkg-license"
        },
        [ordered]@{
            name = "vcpkg-cmake-config"; version = "2024-05-23"; portVersion = 0; license = "MIT"
            portTree = "97a63e4bc1a17422ffe4eff71da53b4b561a7841"
            controlScripts = @(
                "vcpkg-port-config.cmake",
                "vcpkg_cmake_config_fixup.cmake")
            copyrightSource = "port"
        }
    )
    $manifestDependencyNames = @($vcpkgManifest.dependencies | ForEach-Object {
            if ($_ -is [string]) { [string]$_ } else { [string]$_.name }
        })
    if ($manifestDependencyNames.Count -ne $expectedDependencies.Count) {
        throw "The direct vcpkg dependency set changed without a source-closure policy update."
    }
    for ($index = 0; $index -lt $expectedDependencies.Count; ++$index) {
        if ($manifestDependencyNames[$index] -cne [string]$expectedDependencies[$index].name) {
            throw "The direct vcpkg dependency list or reviewed order changed at index $index."
        }
    }

    [string[]]$expectedSourceBuildSpecs = @($expectedBuildHelpers | ForEach-Object {
            "$($_.name):${helperTriplet}@$($_.version)"
        }) + @($expectedDependencies | ForEach-Object {
            $packageName = if ([string]$_.name -eq "spdlog") {
                "spdlog[core,fmt,tz-offset]"
            } else {
                [string]$_.name
            }
            $portVersionSuffix = if ([int]$_.portVersion -eq 0) {
                ""
            } else {
                "#$($_.portVersion)"
            }
            "${packageName}:${triplet}@$($_.version)$portVersionSuffix"
    })
    [System.Array]::Sort[string]($expectedSourceBuildSpecs, [System.StringComparer]::Ordinal)
    $toolchainEvidence = [ordered]@{
        cmakeVersion = $null
        ninjaVersion = $null
        msvcCompilerVersion = $null
        msvcToolsVersion = $null
        windowsSdkVersion = $null
        complete = $false
    }
    $compilerMetadataFiles = @(Get-ChildItem `
            -LiteralPath (Join-Path $RepoRoot "build/release/CMakeFiles") `
            -Filter "CMakeCXXCompiler.cmake" `
            -File `
            -Recurse)
    if ($compilerMetadataFiles.Count -eq 1) {
        $compilerMetadata = Get-Content -LiteralPath $compilerMetadataFiles[0].FullName -Raw
        $compilerVersionMatches = [regex]::Matches(
            $compilerMetadata,
            '(?m)^set\(CMAKE_CXX_COMPILER_VERSION "([0-9]+(?:\.[0-9]+)+)"\)\s*$')
        if ($compilerVersionMatches.Count -eq 1) {
            $toolchainEvidence.msvcCompilerVersion = $compilerVersionMatches[0].Groups[1].Value
        }
    }
    $buildLogPath = Join-Path $RepoRoot "tools/build.log"
    $buildLogAudit = [ordered]@{
        path = "tools/build.log"
        sha256 = $null
        complete = $false
        restoredPackageCount = $null
        sourceBuiltPackages = @()
        installOperations = @()
        toolchain = $toolchainEvidence
        verifiedCacheDisabledSourceBuild = $false
    }
    if (Test-Path -LiteralPath $buildLogPath -PathType Leaf) {
        $buildLogPath = Assert-SafeContainedFile -Root $RepoRoot -RelativePath "tools/build.log"
        $buildLog = (Get-Content -LiteralPath $buildLogPath -Raw).Replace("`r`n", "`n").Replace("`r", "`n")
        $buildLogAudit.sha256 = Get-FileSha256 -Path $buildLogPath
        $buildLogAudit.complete = $buildLog -match '(?m)^=== ALL_DONE ===\s*$' -and
            $buildLog -notmatch '(?m)^\*\*\*BUILD_FAILED\*\*\*'
        $restoredCounts = @([regex]::Matches(
                $buildLog,
                '(?m)^Restored\s+([1-9][0-9]*)\s+package(?:\(s\))?\b') | ForEach-Object {
                [int]$_.Groups[1].Value
            })
        $buildLogAudit.restoredPackageCount = if ($restoredCounts.Count -eq 0) {
            0
        } else {
            ($restoredCounts | Measure-Object -Sum).Sum
        }
        $buildLogAudit.sourceBuiltPackages = @($buildLog -split "`n" | ForEach-Object {
                if ($_ -match '^Building\s+(.+)\.\.\.\s*$') { $Matches[1] }
            } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        $buildLogAudit.installOperations = @($buildLog -split "`n" | ForEach-Object {
                if ($_ -match '^Installing\s+[0-9]+/[0-9]+\s+(.+)\.\.\.\s*$') { $Matches[1] }
            } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        foreach ($toolField in @(
                [ordered]@{ property = 'cmakeVersion'; pattern = '(?ms)^BE_CMAKE_VERSION_BEGIN\s*\ncmake version ([0-9]+(?:\.[0-9]+)+(?:-[0-9A-Za-z.]+)?).*?^BE_CMAKE_VERSION_END\s*$' },
                [ordered]@{ property = 'ninjaVersion'; pattern = '(?m)^BE_NINJA_VERSION_BEGIN\s*\n([0-9]+(?:\.[0-9]+)+)\s*\nBE_NINJA_VERSION_END\s*$' },
                [ordered]@{ property = 'msvcToolsVersion'; pattern = '(?m)^BE_VCTOOLS_VERSION=([0-9]+(?:\.[0-9]+)+)\\?\s*$' },
                [ordered]@{ property = 'windowsSdkVersion'; pattern = '(?m)^BE_WINDOWS_SDK_VERSION=([0-9]+(?:\.[0-9]+)+)\\?\s*$' })) {
            $toolMatches = [regex]::Matches($buildLog, [string]$toolField.pattern)
            if ($toolMatches.Count -eq 1) {
                $toolchainEvidence[[string]$toolField.property] = $toolMatches[0].Groups[1].Value
            }
        }
        $toolchainValues = @(
            $toolchainEvidence.cmakeVersion,
            $toolchainEvidence.ninjaVersion,
            $toolchainEvidence.msvcCompilerVersion,
            $toolchainEvidence.msvcToolsVersion,
            $toolchainEvidence.windowsSdkVersion)
        $toolchainEvidence.complete = @($toolchainValues | Where-Object {
                -not [string]::IsNullOrWhiteSpace([string]$_)
            }).Count -eq $toolchainValues.Count
        [string[]]$actualSourceBuildSpecs = @($buildLogAudit.sourceBuiltPackages)
        [string[]]$actualInstallSpecs = @($buildLogAudit.installOperations)
        [System.Array]::Sort[string]($actualSourceBuildSpecs, [System.StringComparer]::Ordinal)
        [System.Array]::Sort[string]($actualInstallSpecs, [System.StringComparer]::Ordinal)
        $sourceBuildSetMatches = $actualSourceBuildSpecs.Count -eq $expectedSourceBuildSpecs.Count
        $installSetMatches = $actualInstallSpecs.Count -eq $expectedSourceBuildSpecs.Count
        if ($sourceBuildSetMatches -and $installSetMatches) {
            for ($index = 0; $index -lt $expectedSourceBuildSpecs.Count; ++$index) {
                if ($actualSourceBuildSpecs[$index] -cne $expectedSourceBuildSpecs[$index]) {
                    $sourceBuildSetMatches = $false
                }
                if ($actualInstallSpecs[$index] -cne $expectedSourceBuildSpecs[$index]) {
                    $installSetMatches = $false
                }
            }
        }
        $buildLogAudit.verifiedCacheDisabledSourceBuild =
            $buildLogAudit.complete -and
            $buildLogAudit.restoredPackageCount -eq 0 -and
            $toolchainEvidence.complete -and
            $sourceBuildSetMatches -and
            $installSetMatches
    }
    if (-not $buildLogAudit.verifiedCacheDisabledSourceBuild) {
        $releaseEligible = $false
        if (-not $AllowDirty) {
            throw "Release packaging requires tools/build.log to prove the exact toolchain and a complete cache-disabled source build of the reviewed ten-package vcpkg closure."
        }
        Write-Warning "tools/build.log does not prove a complete cache-disabled source build; this engineering package is not release eligible."
    }

    $projectSourceRoot = Join-Path $correspondingSourcePayloadRoot "project"
    $projectExcludedGitlinks = @(Copy-GitTrackedFiles `
            -RepositoryRoot $RepoRoot `
            -DestinationRoot $projectSourceRoot `
            -AllowedGitlinks @{ "extern/CommonLibSSE-NG" = $commonLibCommit })
    if ($projectExcludedGitlinks.Count -ne 1 -or
        $projectExcludedGitlinks[0] -ne "extern/CommonLibSSE-NG") {
        throw "Project source closure did not exclude exactly the separately bundled CommonLib gitlink."
    }
    $monorepoGitmodules = Assert-SafeContainedFile -Root $gitTopLevel -RelativePath ".gitmodules"
    Copy-Item -LiteralPath $monorepoGitmodules -Destination (
        Join-Path $projectSourceRoot "MONOREPO.gitmodules")
    $projectSourceFingerprint = Get-TreeFingerprint -Root $projectSourceRoot

    $ciWorkflowSourceRoot = Join-Path $correspondingSourcePayloadRoot "build/ci"
    $ciWorkflowPathspec = ".github/workflows/bounded-encounters.yml"
    $ciWorkflowExcludedGitlinks = @(if ($isDirty) {
        Copy-GitTrackedFiles `
                -RepositoryRoot $gitTopLevel `
                -DestinationRoot $ciWorkflowSourceRoot `
                -Pathspec $ciWorkflowPathspec `
                -StripPrefix ".github/workflows"
    } else {
        Copy-GitTrackedFiles `
                -RepositoryRoot $gitTopLevel `
                -DestinationRoot $ciWorkflowSourceRoot `
                -Pathspec $ciWorkflowPathspec `
                -StripPrefix ".github/workflows" `
                -RequireIndexBytes
    })
    if ($ciWorkflowExcludedGitlinks.Count -ne 0) {
        throw "Unexpected gitlink in the bounded-encounters release workflow closure."
    }
    $ciWorkflowFingerprint = Get-TreeFingerprint -Root $ciWorkflowSourceRoot
    if ($ciWorkflowFingerprint.fileCount -ne 1 -or
        -not (Test-Path -LiteralPath (
                Join-Path $ciWorkflowSourceRoot "bounded-encounters.yml") -PathType Leaf)) {
        throw "The bounded-encounters release workflow closure is incomplete."
    }

    $commonLibRepositoryRoot = [System.IO.Path]::GetFullPath(
        (Join-Path $RepoRoot "extern/CommonLibSSE-NG"))
    $commonLibStatus = (& git -C $commonLibRepositoryRoot status --porcelain=v1 --untracked-files=all | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not [string]::IsNullOrWhiteSpace($commonLibStatus)) {
        throw "Pinned CommonLibSSE-NG source checkout must be clean."
    }
    $commonLibSourceRoot = Join-Path $correspondingSourcePayloadRoot "dependencies/CommonLibSSE-NG"
    $excludedGitlinks = @(Copy-GitTrackedFiles `
            -RepositoryRoot $commonLibRepositoryRoot `
            -DestinationRoot $commonLibSourceRoot `
            -AllowedGitlinks @{ "extern/openvr" = "60eb187801956ad277f1cae6680e3a410ee0873b" })
    if ($excludedGitlinks.Count -ne 1 -or $excludedGitlinks[0] -ne "extern/openvr") {
        throw "CommonLibSSE-NG source closure did not exclude exactly its uncompiled OpenVR gitlink."
    }
    foreach ($requiredSourceFile in @("COPYING", "EXCEPTIONS.md", "CMakeLists.txt")) {
        if (-not (Test-Path -LiteralPath (Join-Path $commonLibSourceRoot $requiredSourceFile) -PathType Leaf)) {
            throw "CommonLibSSE-NG corresponding source is incomplete: $requiredSourceFile"
        }
    }
    $commonLibSourceFingerprint = Get-TreeFingerprint -Root $commonLibSourceRoot

    $fetchContentBase = Get-CmakeCacheValue -CachePath $cmakeCachePath -Name "FETCHCONTENT_BASE_DIR"
    if ([string]::IsNullOrWhiteSpace($fetchContentBase) -or
        -not [System.IO.Path]::IsPathRooted($fetchContentBase)) {
        throw "CMake cache does not identify an absolute FetchContent source root."
    }
    $minHookRoot = [System.IO.Path]::GetFullPath((Join-Path $fetchContentBase "hde64-src"))
    $expectedMinHookRoot = [System.IO.Path]::GetFullPath(
        (Join-Path $RepoRoot "build/release/_deps/hde64-src"))
    $expectedMinHookCommit = "c3fcafdc10146beb5919319d0683e44e3c30d537"
    $minHookCommit = (& git -C $minHookRoot rev-parse HEAD).Trim()
    $minHookTag = (& git -C $minHookRoot describe --tags --exact-match HEAD).Trim()
    $minHookOrigin = (& git -C $minHookRoot config --get remote.origin.url).Trim()
    $minHookStatus = (& git -C $minHookRoot status --porcelain=v1 --untracked-files=all | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or
        $minHookRoot -ne $expectedMinHookRoot -or
        $minHookCommit -ne $expectedMinHookCommit -or
        $minHookTag -ne "v1.3.4" -or
        $minHookOrigin.TrimEnd('/') -ne "https://github.com/TsudaKageyu/minhook.git" -or
        -not [string]::IsNullOrWhiteSpace($minHookStatus)) {
        throw "Fetched MinHook source does not match the reviewed v1.3.4 hde64 input."
    }
    $rootHde64Declarations = [regex]::Matches(
        $cmakeSource,
        '(?ims)^[ \t]*FetchContent_Declare\(\s*hde64\b.*?^[ \t]*\)')
    $commonLibAddSubdirectoryIndex = $cmakeSource.IndexOf(
        'add_subdirectory(extern/CommonLibSSE-NG)',
        [System.StringComparison]::Ordinal)
    if ($rootHde64Declarations.Count -ne 1 -or
        $commonLibAddSubdirectoryIndex -lt 0 -or
        $rootHde64Declarations[0].Index -gt $commonLibAddSubdirectoryIndex -or
        $rootHde64Declarations[0].Value -notmatch '(?s)GIT_REPOSITORY\s+https://github\.com/TsudaKageyu/minhook\.git\s+GIT_TAG\s+c3fcafdc10146beb5919319d0683e44e3c30d537\s+SOURCE_SUBDIR\s+src/hde') {
        throw "Root CMake must predeclare hde64 at the immutable reviewed MinHook commit before adding CommonLibSSE-NG."
    }
    $commonLibCmake = Get-Content -LiteralPath (Join-Path $commonLibRepositoryRoot "CMakeLists.txt") -Raw
    if ($commonLibCmake -notmatch '(?s)FetchContent_Declare\(\s*hde64.*?GIT_TAG\s+v1\.3\.4' -or
        $commonLibCmake -notmatch 'target_sources\([^\r\n]+hde64\.c') {
        throw "Pinned CommonLib build recipe no longer proves the reviewed MinHook hde64 input."
    }
    $minHookSourceRoot = Join-Path $correspondingSourcePayloadRoot "dependencies/MinHook"
    $null = Copy-GitTrackedFiles `
        -RepositoryRoot $minHookRoot `
        -DestinationRoot $minHookSourceRoot
    if (-not (Test-Path -LiteralPath (Join-Path $minHookSourceRoot "src/hde/hde64.c") -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $minHookSourceRoot "src/hde/hde64.h") -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $minHookSourceRoot "src/hde/pstdint.h") -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $minHookSourceRoot "src/hde/table64.h") -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $minHookSourceRoot "LICENSE.txt") -PathType Leaf)) {
        throw "MinHook corresponding source is incomplete or contains an unexpected gitlink."
    }
    $minHookSourceFingerprint = Get-TreeFingerprint -Root $minHookSourceRoot
    $minHookBinaryLicense = Join-Path $payloadRoot "licenses/MinHook/LICENSE.txt"
    New-Item -ItemType Directory -Path (Split-Path -Parent $minHookBinaryLicense) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $minHookRoot "LICENSE.txt") -Destination $minHookBinaryLicense

    $vcpkgInstalledRoot = $expectedInstalledRoot
    $vcpkgShareRoot = Join-Path $vcpkgInstalledRoot "$triplet/share"
    $vcpkgStatusPath = Join-Path $vcpkgInstalledRoot "vcpkg/status"
    $vcpkgStatusEntries = @(Read-VcpkgStatusEntries -Path $vcpkgStatusPath)
    $baseStatusEntries = @($vcpkgStatusEntries | Where-Object { -not $_.Contains("Feature") })
    [string[]]$expectedBaseStatusKeys = @(
        $expectedDependencies | ForEach-Object { "$($_.name)|$triplet" }
    ) + @(
        $expectedBuildHelpers | ForEach-Object { "$($_.name)|$helperTriplet" }
    )
    [string[]]$actualBaseStatusKeys = @($baseStatusEntries | ForEach-Object {
            "$($_['Package'])|$($_['Architecture'])"
        })
    [System.Array]::Sort[string]($expectedBaseStatusKeys, [System.StringComparer]::Ordinal)
    [System.Array]::Sort[string]($actualBaseStatusKeys, [System.StringComparer]::Ordinal)
    if ($actualBaseStatusKeys.Count -ne 10 -or
        $actualBaseStatusKeys.Count -ne $expectedBaseStatusKeys.Count) {
        throw "The installed vcpkg status database must contain exactly the eight reviewed targets and two reviewed build helpers."
    }
    for ($index = 0; $index -lt $expectedBaseStatusKeys.Count; ++$index) {
        if ($actualBaseStatusKeys[$index] -cne $expectedBaseStatusKeys[$index]) {
            throw "The installed vcpkg base-package closure does not match the reviewed ten-package set."
        }
    }
    $featureStatusEntries = @($vcpkgStatusEntries | Where-Object { $_.Contains("Feature") })
    [string[]]$expectedFeatureStatusKeys = @(
        "spdlog|fmt|$triplet",
        "spdlog|tz-offset|$triplet"
    )
    [string[]]$actualFeatureStatusKeys = @($featureStatusEntries | ForEach-Object {
            "$($_['Package'])|$($_['Feature'])|$($_['Architecture'])"
        })
    [System.Array]::Sort[string]($expectedFeatureStatusKeys, [System.StringComparer]::Ordinal)
    [System.Array]::Sort[string]($actualFeatureStatusKeys, [System.StringComparer]::Ordinal)
    if ($vcpkgStatusEntries.Count -ne 12 -or
        $actualFeatureStatusKeys.Count -ne $expectedFeatureStatusKeys.Count) {
        throw "The installed vcpkg status database must contain exactly ten base and two reviewed feature entries."
    }
    for ($index = 0; $index -lt $expectedFeatureStatusKeys.Count; ++$index) {
        if ($actualFeatureStatusKeys[$index] -cne $expectedFeatureStatusKeys[$index]) {
            throw "The installed vcpkg feature closure does not match spdlog:fmt and spdlog:tz-offset."
        }
    }
    foreach ($featureEntry in $featureStatusEntries) {
        $featureName = [string]$featureEntry["Feature"]
        $expectedDepends = if ($featureName -eq "fmt") { "fmt" } else { $null }
        $actualDepends = if ($featureEntry.Contains("Depends")) {
            [string]$featureEntry["Depends"]
        } else {
            $null
        }
        if ([string]$featureEntry["Package"] -ne "spdlog" -or
            [string]$featureEntry["Multi-Arch"] -ne "same" -or
            [string]$featureEntry["Status"] -ne "install ok installed" -or
            $actualDepends -ne $expectedDepends) {
            throw "The installed vcpkg feature status changed for spdlog:$featureName."
        }
    }
    $resolvedDependencies = @()
    foreach ($expectedDependency in $expectedDependencies) {
        $dependencyName = [string]$expectedDependency.name
        $installedEntries = @($vcpkgStatusEntries | Where-Object {
                $_["Package"] -eq $dependencyName -and
                $_["Architecture"] -eq $triplet -and
                -not $_.Contains("Feature")
            })
        if ($installedEntries.Count -ne 1) {
            throw "Expected exactly one installed base status entry for $dependencyName."
        }
        $installedEntry = $installedEntries[0]
        $installedPortVersion = if ($installedEntry.Contains("Port-Version")) {
            [int]$installedEntry["Port-Version"]
        } else {
            0
        }
        $installedAbi = [string]$installedEntry["Abi"]
        if ([string]$installedEntry["Version"] -ne [string]$expectedDependency.version -or
            $installedPortVersion -ne [int]$expectedDependency.portVersion -or
            $installedAbi -notmatch '^[0-9a-f]{64}$' -or
            [string]$installedEntry["Multi-Arch"] -ne "same" -or
            [string]$installedEntry["Status"] -ne "install ok installed") {
            throw "Installed version or ABI does not match the reviewed $dependencyName build."
        }

        $actualPortTree = (& git -C $vcpkgRoot rev-parse "HEAD:ports/$dependencyName").Trim()
        if ($LASTEXITCODE -ne 0 -or $actualPortTree -ne [string]$expectedDependency.portTree) {
            throw "vcpkg port recipe tree does not match the reviewed $dependencyName input."
        }

        $sourceTreeParent = Join-Path $vcpkgRoot "buildtrees/$dependencyName/src"
        if (-not (Test-Path -LiteralPath $sourceTreeParent -PathType Container)) {
            throw "vcpkg post-patch source parent is missing for $dependencyName."
        }
        $sourceCandidates = @()
        foreach ($candidate in Get-ChildItem -LiteralPath $sourceTreeParent -Directory -Force) {
            if ($candidate.Name -notmatch [string]$expectedDependency.sourcePattern) {
                continue
            }
            $candidateFingerprint = Get-TreeFingerprint -Root $candidate.FullName
            $sourceCandidates += [ordered]@{
                path = $candidate.FullName
                directory = $candidate.Name
                fileCount = $candidateFingerprint.fileCount
                sha256 = $candidateFingerprint.sha256
            }
        }
        $matchingSourceCandidates = @($sourceCandidates | Where-Object {
                $_.fileCount -eq [int]$expectedDependency.sourceFileCount -and
                $_.sha256 -eq [string]$expectedDependency.sourceTreeSha256
            })
        if ($sourceCandidates.Count -ne 1 -or $matchingSourceCandidates.Count -ne 1) {
            $candidateDetails = ($sourceCandidates | ForEach-Object {
                    "$($_.directory):$($_.fileCount):$($_.sha256)"
                }) -join "; "
            throw "Expected one unambiguous exact post-patch source tree for $dependencyName; found $($sourceCandidates.Count) matching-name candidate(s), of which $($matchingSourceCandidates.Count) matched the reviewed fingerprint. Candidates: $candidateDetails"
        }
        $selectedSource = $matchingSourceCandidates[0]

        $dependencySourceRoot = Join-Path $correspondingSourcePayloadRoot "dependencies/vcpkg/$dependencyName"
        $copiedSourceFingerprint = Copy-DirectoryTree `
            -SourceRoot $selectedSource.path `
            -DestinationRoot (Join-Path $dependencySourceRoot "source")
        if ($copiedSourceFingerprint.sha256 -ne [string]$expectedDependency.sourceTreeSha256) {
            throw "Copied post-patch source fingerprint changed for $dependencyName."
        }

        $portPathspec = "ports/$dependencyName"
        $portExcludedGitlinks = @(Copy-GitTrackedFiles `
                -RepositoryRoot $vcpkgRoot `
                -DestinationRoot (Join-Path $dependencySourceRoot "port") `
                -Pathspec $portPathspec `
                -StripPrefix $portPathspec `
                -RequireIndexBytes)
        if ($portExcludedGitlinks.Count -ne 0) {
            throw "Unexpected gitlink in vcpkg port recipe: $dependencyName"
        }

        $shareRoot = Join-Path $vcpkgShareRoot $dependencyName
        $installedMetadataFiles = @(
            "copyright",
            "vcpkg.spdx.json",
            "vcpkg_abi_info.txt"
        )
        foreach ($metadataFile in $installedMetadataFiles) {
            $source = Assert-SafeContainedFile -Root $shareRoot -RelativePath $metadataFile
            $destination = Join-Path $dependencySourceRoot "installed/$metadataFile"
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Copy-Item -LiteralPath $source -Destination $destination
        }

        $buildtreeAbiInfo = Assert-SafeContainedFile `
            -Root (Join-Path $vcpkgRoot "buildtrees/$dependencyName") `
            -RelativePath "$triplet.vcpkg_abi_info.txt"
        $installedAbiInfo = Join-Path $shareRoot "vcpkg_abi_info.txt"
        $buildtreeAbiInfoHash = Get-FileSha256 -Path $buildtreeAbiInfo
        $installedAbiInfoHash = Get-FileSha256 -Path $installedAbiInfo
        if ($buildtreeAbiInfoHash -ne $installedAbi -or
            $installedAbiInfoHash -ne $installedAbi) {
            throw "Status ABI does not equal both installed and buildtree ABI metadata for $dependencyName."
        }

        $spdxDocument = Get-Content -LiteralPath (Join-Path $shareRoot "vcpkg.spdx.json") -Raw |
            ConvertFrom-Json
        $spdxPortPackages = @($spdxDocument.packages | Where-Object { $_.SPDXID -eq "SPDXRef-port" })
        $spdxBinaryPackages = @($spdxDocument.packages | Where-Object { $_.SPDXID -eq "SPDXRef-binary" })
        $expectedVersionInfo = if ([int]$expectedDependency.portVersion -eq 0) {
            [string]$expectedDependency.version
        } else {
            "$($expectedDependency.version)#$($expectedDependency.portVersion)"
        }
        if ($spdxPortPackages.Count -ne 1 -or
            $spdxBinaryPackages.Count -ne 1 -or
            [string]$spdxPortPackages[0].name -ne $dependencyName -or
            [string]$spdxPortPackages[0].versionInfo -ne $expectedVersionInfo -or
            [string]$spdxPortPackages[0].downloadLocation -ne "git+https://github.com/microsoft/vcpkg@$actualPortTree" -or
            [string]$spdxBinaryPackages[0].versionInfo -ne $installedAbi) {
            throw "Installed SPDX provenance does not match the reviewed $dependencyName resolution."
        }
        $resourcePackages = @($spdxDocument.packages | Where-Object {
                [string]$_.SPDXID -like "SPDXRef-resource-*"
            })
        if ($resourcePackages.Count -eq 0) {
            throw "Installed upstream resource provenance is empty for $dependencyName."
        }
        $resourceProvenance = [ordered]@{
            schemaVersion = 1
            extractedFrom = "installed/vcpkg.spdx.json"
            packages = $resourcePackages
        }
        Write-Utf8NoBomLf `
            -Path (Join-Path $dependencySourceRoot "installed/upstream-resource-provenance.json") `
            -Content ($resourceProvenance | ConvertTo-Json -Depth 10)

        $infoDirectory = Join-Path $vcpkgInstalledRoot "vcpkg/info"
        $infoListName = "${dependencyName}_$($expectedDependency.version)_${triplet}.list"
        $matchingInfoLists = @(Get-ChildItem -LiteralPath $infoDirectory -File -Filter "${dependencyName}_*_${triplet}.list")
        if ($matchingInfoLists.Count -ne 1 -or $matchingInfoLists[0].Name -cne $infoListName) {
            throw "Installed file inventory is missing, mismatched, or ambiguous for $dependencyName."
        }
        Copy-Item -LiteralPath $matchingInfoLists[0].FullName -Destination (
            Join-Path $dependencySourceRoot "installed/info-list.txt")
        Write-Utf8NoBomLf `
            -Path (Join-Path $dependencySourceRoot "installed/status.txt") `
            -Content (ConvertTo-VcpkgStatusParagraph -Entry $installedEntry)
        $dependencyFeatures = @()
        $dependencyFeatureEntries = @($featureStatusEntries | Where-Object {
                $_["Package"] -eq $dependencyName -and $_["Architecture"] -eq $triplet
            } | Sort-Object { [string]$_["Feature"] })
        if ($dependencyFeatureEntries.Count -ne 0) {
            New-Item -ItemType Directory -Path (
                Join-Path $dependencySourceRoot "installed/features") -Force | Out-Null
        }
        foreach ($featureEntry in $dependencyFeatureEntries) {
            $featureName = [string]$featureEntry["Feature"]
            if ($featureName -notmatch '^[a-z0-9-]+$') {
                throw "Unsafe vcpkg feature name in reviewed status closure: $featureName"
            }
            Write-Utf8NoBomLf `
                -Path (Join-Path $dependencySourceRoot "installed/features/$featureName.status.txt") `
                -Content (ConvertTo-VcpkgStatusParagraph -Entry $featureEntry)
            $dependencyFeatures += [ordered]@{
                name = $featureName
                depends = if ($featureEntry.Contains("Depends")) {
                    [string]$featureEntry["Depends"]
                } else {
                    $null
                }
            }
        }

        $copyrightSource = Join-Path $shareRoot "copyright"
        $copyrightDestination = Join-Path $payloadRoot "licenses/vcpkg/$dependencyName/copyright"
        New-Item -ItemType Directory -Path (Split-Path -Parent $copyrightDestination) -Force | Out-Null
        Copy-Item -LiteralPath $copyrightSource -Destination $copyrightDestination

        $dependencyProvenance = [ordered]@{
            schemaVersion = 1
            name = $dependencyName
            version = [string]$expectedDependency.version
            portVersion = [int]$expectedDependency.portVersion
            triplet = $triplet
            abi = $installedAbi
            license = [string]$expectedDependency.license
            vcpkgBaseline = $vcpkgBaseline
            portTree = $actualPortTree
            postPatchSourceDirectory = [string]$selectedSource.directory
            postPatchSourceFileCount = [int]$selectedSource.fileCount
            postPatchSourceTreeSha256 = [string]$selectedSource.sha256
            features = $dependencyFeatures
        }
        Write-Utf8NoBomLf `
            -Path (Join-Path $dependencySourceRoot "PROVENANCE.json") `
            -Content ($dependencyProvenance | ConvertTo-Json -Depth 6)
        $resolvedDependencies += $dependencyProvenance
    }

    $resolvedBuildHelpers = @()
    foreach ($expectedHelper in $expectedBuildHelpers) {
        $helperName = [string]$expectedHelper.name
        $installedEntries = @($vcpkgStatusEntries | Where-Object {
                $_["Package"] -eq $helperName -and
                $_["Architecture"] -eq $helperTriplet -and
                -not $_.Contains("Feature")
            })
        if ($installedEntries.Count -ne 1) {
            throw "Expected exactly one installed base status entry for build helper $helperName."
        }
        $installedEntry = $installedEntries[0]
        $installedPortVersion = if ($installedEntry.Contains("Port-Version")) {
            [int]$installedEntry["Port-Version"]
        } else {
            0
        }
        $installedAbi = [string]$installedEntry["Abi"]
        if ([string]$installedEntry["Version"] -ne [string]$expectedHelper.version -or
            $installedPortVersion -ne [int]$expectedHelper.portVersion -or
            $installedAbi -notmatch '^[0-9a-f]{64}$' -or
            [string]$installedEntry["Multi-Arch"] -ne "same" -or
            [string]$installedEntry["Status"] -ne "install ok installed") {
            throw "Installed version or ABI does not match the reviewed $helperName build helper."
        }

        $actualPortTree = (& git -C $vcpkgRoot rev-parse "HEAD:ports/$helperName").Trim()
        if ($LASTEXITCODE -ne 0 -or $actualPortTree -ne [string]$expectedHelper.portTree) {
            throw "vcpkg port recipe tree does not match the reviewed $helperName build helper."
        }
        $helperBuildtreeRoot = Join-Path $vcpkgRoot "buildtrees/$helperName"
        if (Test-Path -LiteralPath (Join-Path $helperBuildtreeRoot "src")) {
            throw "The reviewed source-free helper port unexpectedly has a post-patch source directory: $helperName"
        }

        $helperClosureRoot = Join-Path $correspondingSourcePayloadRoot "dependencies/vcpkg/$helperName"
        $portPathspec = "ports/$helperName"
        $portExcludedGitlinks = @(Copy-GitTrackedFiles `
                -RepositoryRoot $vcpkgRoot `
                -DestinationRoot (Join-Path $helperClosureRoot "port") `
                -Pathspec $portPathspec `
                -StripPrefix $portPathspec `
                -RequireIndexBytes)
        if ($portExcludedGitlinks.Count -ne 0) {
            throw "Unexpected gitlink in vcpkg build-helper port recipe: $helperName"
        }
        $portFingerprint = Get-TreeFingerprint -Root (Join-Path $helperClosureRoot "port")

        $shareRoot = Join-Path $vcpkgInstalledRoot "$helperTriplet/share/$helperName"
        Assert-NoReparsePoints -Root $shareRoot
        $infoDirectory = Join-Path $vcpkgInstalledRoot "vcpkg/info"
        $infoListName = "${helperName}_$($expectedHelper.version)_${helperTriplet}.list"
        $matchingInfoLists = @(Get-ChildItem -LiteralPath $infoDirectory -File -Filter "${helperName}_*_${helperTriplet}.list")
        if ($matchingInfoLists.Count -ne 1 -or $matchingInfoLists[0].Name -cne $infoListName) {
            throw "Installed file inventory is missing, mismatched, or ambiguous for build helper $helperName."
        }
        $inventoryLines = @(Get-Content -LiteralPath $matchingInfoLists[0].FullName |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        [string[]]$inventoryFiles = @($inventoryLines | Where-Object { -not $_.EndsWith('/') })
        $expectedSharePrefix = "$helperTriplet/share/$helperName/"
        if ($inventoryFiles.Count -eq 0 -or
            @($inventoryFiles | Where-Object {
                    -not $_.StartsWith($expectedSharePrefix, [System.StringComparison]::Ordinal)
                }).Count -ne 0) {
            throw "Installed file inventory escapes or omits the reviewed share tree for build helper $helperName."
        }
        [string[]]$actualShareFiles = @([System.IO.Directory]::EnumerateFiles(
                $shareRoot, '*', [System.IO.SearchOption]::AllDirectories) | ForEach-Object {
                Get-RelativeSlashPath -Base $vcpkgInstalledRoot -Path $_
            })
        [System.Array]::Sort[string]($inventoryFiles, [System.StringComparer]::Ordinal)
        [System.Array]::Sort[string]($actualShareFiles, [System.StringComparer]::Ordinal)
        if ($inventoryFiles.Count -ne $actualShareFiles.Count) {
            throw "Installed inventory count does not match the share tree for build helper $helperName."
        }
        for ($index = 0; $index -lt $inventoryFiles.Count; ++$index) {
            if ($inventoryFiles[$index] -cne $actualShareFiles[$index]) {
                throw "Installed inventory does not match the share tree for build helper $helperName."
            }
        }
        [string[]]$expectedControlScripts = @($expectedHelper.controlScripts)
        [string[]]$actualControlScripts = @($actualShareFiles | ForEach-Object {
                [System.IO.Path]::GetFileName([string]$_)
            } | Where-Object { $_.EndsWith('.cmake', [System.StringComparison]::Ordinal) })
        [System.Array]::Sort[string]($expectedControlScripts, [System.StringComparer]::Ordinal)
        [System.Array]::Sort[string]($actualControlScripts, [System.StringComparer]::Ordinal)
        if ($actualControlScripts.Count -ne $expectedControlScripts.Count) {
            throw "Installed control-script count changed for build helper $helperName."
        }
        $controlScriptHashes = @()
        for ($index = 0; $index -lt $expectedControlScripts.Count; ++$index) {
            if ($actualControlScripts[$index] -cne $expectedControlScripts[$index]) {
                throw "Installed control-script set changed for build helper $helperName."
            }
            $scriptName = [string]$expectedControlScripts[$index]
            $portScript = Assert-SafeContainedFile `
                -Root (Join-Path $vcpkgRoot "ports/$helperName") `
                -RelativePath $scriptName
            $installedScript = Assert-SafeContainedFile `
                -Root $shareRoot `
                -RelativePath $scriptName
            $portScriptHash = Get-FileSha256 -Path $portScript
            if ((Get-FileSha256 -Path $installedScript) -ne $portScriptHash) {
                throw "Installed control script does not equal its pinned port input: $helperName/$scriptName"
            }
            $controlScriptHashes += [ordered]@{
                path = $scriptName
                sha256 = $portScriptHash
            }
        }
        $copyrightInput = if ([string]$expectedHelper.copyrightSource -eq "vcpkg-license") {
            Assert-SafeContainedFile -Root $vcpkgRoot -RelativePath "LICENSE.txt"
        } else {
            Assert-SafeContainedFile `
                -Root (Join-Path $vcpkgRoot "ports/$helperName") `
                -RelativePath "copyright"
        }
        $installedCopyright = Assert-SafeContainedFile -Root $shareRoot -RelativePath "copyright"
        $copyrightHash = Get-FileSha256 -Path $copyrightInput
        if ((Get-FileSha256 -Path $installedCopyright) -ne $copyrightHash) {
            throw "Installed helper copyright does not equal its pinned recipe input: $helperName"
        }
        foreach ($relativeInstalledPath in $inventoryFiles) {
            $source = Assert-SafeContainedFile `
                -Root $vcpkgInstalledRoot `
                -RelativePath $relativeInstalledPath
            $destination = Join-Path $helperClosureRoot "installed/$relativeInstalledPath"
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Copy-Item -LiteralPath $source -Destination $destination
        }
        Copy-Item -LiteralPath $matchingInfoLists[0].FullName -Destination (
            Join-Path $helperClosureRoot "installed/info-list.txt")
        Write-Utf8NoBomLf `
            -Path (Join-Path $helperClosureRoot "installed/status.txt") `
            -Content (ConvertTo-VcpkgStatusParagraph -Entry $installedEntry)

        $buildtreeAbiInfo = Assert-SafeContainedFile `
            -Root $helperBuildtreeRoot `
            -RelativePath "$helperTriplet.vcpkg_abi_info.txt"
        $installedAbiInfo = Assert-SafeContainedFile `
            -Root $shareRoot `
            -RelativePath "vcpkg_abi_info.txt"
        if ((Get-FileSha256 -Path $buildtreeAbiInfo) -ne $installedAbi -or
            (Get-FileSha256 -Path $installedAbiInfo) -ne $installedAbi) {
            throw "Status ABI does not equal both installed and buildtree ABI metadata for build helper $helperName."
        }

        $spdxDocument = Get-Content -LiteralPath (Join-Path $shareRoot "vcpkg.spdx.json") -Raw |
            ConvertFrom-Json
        $spdxPortPackages = @($spdxDocument.packages | Where-Object { $_.SPDXID -eq "SPDXRef-port" })
        $spdxBinaryPackages = @($spdxDocument.packages | Where-Object { $_.SPDXID -eq "SPDXRef-binary" })
        $expectedVersionInfo = if ([int]$expectedHelper.portVersion -eq 0) {
            [string]$expectedHelper.version
        } else {
            "$($expectedHelper.version)#$($expectedHelper.portVersion)"
        }
        $resourcePackages = @($spdxDocument.packages | Where-Object {
                [string]$_.SPDXID -like "SPDXRef-resource-*"
            })
        if ($spdxPortPackages.Count -ne 1 -or
            $spdxBinaryPackages.Count -ne 1 -or
            $resourcePackages.Count -ne 0 -or
            [string]$spdxPortPackages[0].name -ne $helperName -or
            [string]$spdxPortPackages[0].versionInfo -ne $expectedVersionInfo -or
            [string]$spdxPortPackages[0].downloadLocation -ne "git+https://github.com/microsoft/vcpkg@$actualPortTree" -or
            [string]$spdxPortPackages[0].licenseConcluded -ne [string]$expectedHelper.license -or
            [string]$spdxBinaryPackages[0].versionInfo -ne $installedAbi) {
            throw "Installed SPDX provenance does not match the reviewed $helperName build helper."
        }

        $abiLines = @(Get-Content -LiteralPath $installedAbiInfo)
        $cmakeEvidence = @($abiLines | Where-Object { $_ -match '^cmake\s+(.+)$' })
        $powerShellEvidence = @($abiLines | Where-Object { $_ -match '^powershell\s+(.+)$' })
        if ($cmakeEvidence.Count -ne 1 -or $powerShellEvidence.Count -ne 1) {
            throw "Build-helper ABI metadata does not contain unambiguous CMake and PowerShell version evidence: $helperName"
        }
        $null = $cmakeEvidence[0] -match '^cmake\s+(.+)$'
        $cmakeVersion = $Matches[1]
        $null = $powerShellEvidence[0] -match '^powershell\s+(.+)$'
        $powerShellVersion = $Matches[1]
        $acquiredPrograms = @($abiLines | Where-Object {
                $_ -match '^vcpkg_find_acquire_program\(([^)]+)\)\s+([0-9a-f]{64})$'
            } | ForEach-Object {
                $null = $_ -match '^vcpkg_find_acquire_program\(([^)]+)\)\s+([0-9a-f]{64})$'
                [ordered]@{ name = $Matches[1]; sha256 = $Matches[2] }
            })
        $installedShareFingerprint = Get-TreeFingerprint -Root (
            Join-Path $helperClosureRoot "installed/$helperTriplet/share/$helperName")
        $helperProvenance = [ordered]@{
            schemaVersion = 1
            kind = "build-helper"
            name = $helperName
            version = [string]$expectedHelper.version
            portVersion = [int]$expectedHelper.portVersion
            triplet = $helperTriplet
            abi = $installedAbi
            license = [string]$expectedHelper.license
            vcpkgBaseline = $vcpkgBaseline
            portTree = $actualPortTree
            portFileCount = $portFingerprint.fileCount
            portTreeSha256 = $portFingerprint.sha256
            installedShareFileCount = $installedShareFingerprint.fileCount
            installedShareTreeSha256 = $installedShareFingerprint.sha256
            controlScripts = $controlScriptHashes
            copyrightSha256 = $copyrightHash
            postPatchSourcePresent = $false
            postPatchSourceReason = "This helper port installs tracked vcpkg CMake control scripts and fetches no upstream source tree."
            toolEvidence = [ordered]@{
                cmakeVersion = $cmakeVersion
                powerShellVersion = $powerShellVersion
                acquiredPrograms = $acquiredPrograms
            }
        }
        Write-Utf8NoBomLf `
            -Path (Join-Path $helperClosureRoot "PROVENANCE.json") `
            -Content ($helperProvenance | ConvertTo-Json -Depth 8)
        $resolvedBuildHelpers += $helperProvenance
    }

    $vcpkgBuildMetadataRoot = Join-Path $correspondingSourcePayloadRoot "build/vcpkg"
    $null = Copy-GitTrackedFiles `
        -RepositoryRoot $vcpkgRoot `
        -DestinationRoot $vcpkgBuildMetadataRoot `
        -Pathspec "triplets/$triplet.cmake" `
        -RequireIndexBytes
    $null = Copy-GitTrackedFiles `
        -RepositoryRoot $vcpkgRoot `
        -DestinationRoot $vcpkgBuildMetadataRoot `
        -Pathspec "triplets/$helperTriplet.cmake" `
        -RequireIndexBytes
    $vcpkgScriptBinaryExclusions = @(
        [ordered]@{
            path = "scripts/tls12-download.exe"
            gitObject = "7bcfc74d9de9a6b65952e0e2fa102768fa96ad77"
            sha256 = "de0b9b6656c9e9fc9db4271610a09c2ae27d07c5a4757e94b2e0314a9dda6ee4"
            reason = "Tracked general-purpose TLS downloader binary; it is not compiled into or invoked by the reviewed build."
        },
        [ordered]@{
            path = "scripts/tls12-download-arm64.exe"
            gitObject = "9df2283e6dda9efda623c6c36933f0fd0e0233c0"
            sha256 = "5b6269a6619953e70edf223dd6c9b0440d913f24706f6529e9156e2492455fc7"
            reason = "Tracked general-purpose ARM64 TLS downloader binary; it is not compiled into or invoked by the reviewed x64 build."
        }
    )
    foreach ($excludedBinary in $vcpkgScriptBinaryExclusions) {
        $indexEntries = @(& git -C $vcpkgRoot ls-files -s -- ([string]$excludedBinary.path))
        if ($LASTEXITCODE -ne 0 -or $indexEntries.Count -ne 1 -or
            $indexEntries[0] -notmatch '^100644 ([0-9a-f]{40}) 0\t(.+)$' -or
            $Matches[1] -ne [string]$excludedBinary.gitObject -or
            $Matches[2] -cne [string]$excludedBinary.path) {
            throw "The reviewed vcpkg script-binary exclusion changed: $($excludedBinary.path)"
        }
        $excludedPath = Assert-SafeContainedFile `
            -Root $vcpkgRoot `
            -RelativePath ([string]$excludedBinary.path)
        if ((Get-FileSha256 -Path $excludedPath) -ne [string]$excludedBinary.sha256) {
            throw "The reviewed vcpkg script-binary exclusion bytes changed: $($excludedBinary.path)"
        }
    }
    $vcpkgScriptsExcludedGitlinks = @(Copy-GitTrackedFiles `
            -RepositoryRoot $vcpkgRoot `
            -DestinationRoot (Join-Path $vcpkgBuildMetadataRoot "scripts") `
            -Pathspec @(
                "scripts",
                ":(exclude)scripts/tls12-download.exe",
                ":(exclude)scripts/tls12-download-arm64.exe") `
            -StripPrefix "scripts" `
            -RequireIndexBytes)
    if ($vcpkgScriptsExcludedGitlinks.Count -ne 0) {
        throw "Unexpected gitlink in the pinned vcpkg scripts closure."
    }
    $null = Copy-GitTrackedFiles `
        -RepositoryRoot $vcpkgRoot `
        -DestinationRoot $vcpkgBuildMetadataRoot `
        -Pathspec "LICENSE.txt" `
        -RequireIndexBytes
    Write-Utf8NoBomLf -Path (Join-Path $vcpkgBuildMetadataRoot "BASELINE.txt") -Content $vcpkgBaseline
    $vcpkgScriptsFingerprint = Get-TreeFingerprint -Root (Join-Path $vcpkgBuildMetadataRoot "scripts")
    $unexpectedVcpkgScriptBinaries = @(Get-ChildItem `
            -LiteralPath (Join-Path $vcpkgBuildMetadataRoot "scripts") `
            -File `
            -Recurse | Where-Object { $_.Extension -in @('.exe', '.dll') })
    if ($vcpkgScriptsFingerprint.fileCount -ne 821 -or
        $unexpectedVcpkgScriptBinaries.Count -ne 0) {
        throw "The pinned vcpkg tracked-script source closure changed or contains an unexpected PE binary."
    }
    $targetTripletSha256 = Get-FileSha256 -Path (
        Join-Path $vcpkgBuildMetadataRoot "triplets/$triplet.cmake")
    $helperTripletSha256 = Get-FileSha256 -Path (
        Join-Path $vcpkgBuildMetadataRoot "triplets/$helperTriplet.cmake")

    $sourceProvenance = [ordered]@{
        schemaVersion = 3
        bundle = [ordered]@{
            project = "Bounded Encounters"
            version = $Version
            sourceCommit = $commit
            dirty = $isDirty
            sourceDateEpoch = $epoch
        }
        project = [ordered]@{
            repository = "https://github.com/Ensrick/skyrim-mod-assistant"
            path = "mods/bounded-encounters"
            sourceFileCount = $projectSourceFingerprint.fileCount
            sourceTreeSha256 = $projectSourceFingerprint.sha256
            excludedGitlinks = $projectExcludedGitlinks
        }
        ciWorkflow = [ordered]@{
            path = ".github/workflows/bounded-encounters.yml"
            archivePath = "build/ci/bounded-encounters.yml"
            fileCount = $ciWorkflowFingerprint.fileCount
            treeSha256 = $ciWorkflowFingerprint.sha256
            indexBytesVerified = -not $isDirty
        }
        commonLibSseNg = [ordered]@{
            repository = "https://github.com/Ensrick/CommonLibSSE-NG"
            branch = "ensrick/no-modal-errors-v7"
            commit = $commonLibCommit
            upstreamRepository = "https://github.com/alandtse/CommonLibSSE-NG"
            upstreamTag = $commonLibUpstreamTag
            upstreamCommit = $commonLibParentCommit
            modification = "Opt-in COMMONLIBSSE_NO_MODAL_ERRORS failure path"
            license = "GPL-3.0-or-later"
            exceptionFile = "EXCEPTIONS.md"
            sourceFileCount = $commonLibSourceFingerprint.fileCount
            sourceTreeSha256 = $commonLibSourceFingerprint.sha256
            excludedGitlinks = $excludedGitlinks
            exclusionReason = "OpenVR is not compiled because Skyrim VR support is disabled."
        }
        minHook = [ordered]@{
            repository = "https://github.com/TsudaKageyu/minhook"
            tag = $minHookTag
            commit = $minHookCommit
            rootCmakeImmutablePinVerified = $true
            license = "BSD-2-Clause"
            compiledFiles = @(
                "src/hde/hde64.c",
                "src/hde/hde64.h",
                "src/hde/pstdint.h",
                "src/hde/table64.h"
            )
            sourceFileCount = $minHookSourceFingerprint.fileCount
            sourceTreeSha256 = $minHookSourceFingerprint.sha256
        }
        vcpkg = [ordered]@{
            repository = "https://github.com/microsoft/vcpkg"
            baseline = $vcpkgBaseline
            checkoutCommit = $vcpkgCommit
            targetTriplet = $triplet
            targetTripletSha256 = $targetTripletSha256
            hostTriplet = $helperTriplet
            hostTripletSha256 = $helperTripletSha256
            binaryCacheDisabled = $binaryCacheDisabled -and $buildLogAudit.verifiedCacheDisabledSourceBuild
            packagingEnvironmentBinaryCacheDisabled = $binaryCacheDisabled
            buildLogAudit = $buildLogAudit
            trackedScriptsFileCount = $vcpkgScriptsFingerprint.fileCount
            trackedScriptsTreeSha256 = $vcpkgScriptsFingerprint.sha256
            excludedTrackedScriptBinaries = $vcpkgScriptBinaryExclusions
            dependencies = $resolvedDependencies
            buildHelpers = $resolvedBuildHelpers
        }
    }
    Write-Utf8NoBomLf `
        -Path (Join-Path $correspondingSourcePayloadRoot "SOURCE-PROVENANCE.json") `
        -Content ($sourceProvenance | ConvertTo-Json -Depth 10)
    $sourceReadmeTemplate = @'
# Bounded Encounters corresponding source

This archive accompanies Bounded Encounters {{VERSION}}. It contains the tracked
Bounded Encounters project source/build scripts and its monorepo release
workflow, the exact pinned CommonLibSSE-NG source (excluding only the uncompiled
OpenVR gitlink), the exact tracked MinHook v1.3.4 source used for hde64, and the
exact post-patch source trees for all eight direct vcpkg manifest dependencies.
It also contains the two source-free vcpkg CMake helper ports and their complete
installed control-script trees.

Each direct vcpkg dependency directory also retains its exact port recipe,
installed SPDX document, upstream-resource provenance, copyright/license text,
ABI metadata, installed file inventory, base/feature status stanzas, and a
machine-readable provenance record. The source-free helper directories retain
their full installed share trees and equivalent host metadata. build/vcpkg
records the pinned baseline, target and host triplets, and all tracked vcpkg
scripts except two reviewed downloader PEs.

SOURCE-PROVENANCE.json identifies every reviewed version, commit, ABI, port
tree, and source-tree fingerprint. SOURCE-MANIFEST.sha256 verifies every other
file in this archive. Provenance also records the SHA-256 and parsed cache audit
of tools/build.log: all ten reviewed packages must have source-build and install
operations and none may be restored. The path-bearing log itself is not
distributed. No network access is performed by the packager.

CommonLibSSE-NG remains GPL-3.0-or-later with its unchanged Modding Exception.
MinHook/hde64 is BSD-2-Clause. The direct vcpkg dependencies retain their own
license files and SPDX metadata in their respective directories.

## Reconstructing the source layout

From the extracted archive in `pwsh` (PowerShell 7.4 or newer), the reviewed
online reconstruction is:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion -lt [version]"7.4") {
  throw "The reviewed reconstruction requires PowerShell 7.4 or newer."
}

function Invoke-Checked {
  param([scriptblock]$Command, [string]$Description)
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "Native command failed ($LASTEXITCODE): $Description"
  }
}

$bundleRoot = (Resolve-Path .).Path
$manifestPath = Join-Path $bundleRoot "SOURCE-MANIFEST.sha256"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw "SOURCE-MANIFEST.sha256 is missing."
}
$listedPaths = [System.Collections.Generic.HashSet[string]]::new(
  [System.StringComparer]::Ordinal)
$bundlePrefix = $bundleRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
foreach ($line in Get-Content -LiteralPath $manifestPath) {
  if ($line -notmatch '^([0-9a-f]{64})  (.+)$') {
    throw "Malformed SOURCE-MANIFEST entry: $line"
  }
  $expectedHash = $Matches[1]
  $relativePath = $Matches[2]
  $segments = @($relativePath.Split('/'))
  if ([System.IO.Path]::IsPathRooted($relativePath) -or
      $relativePath.Contains('\') -or $relativePath.Contains(':') -or
      $segments.Count -eq 0 -or
      @($segments | Where-Object { $_ -in @('', '.', '..') }).Count -ne 0 -or
      $relativePath -ceq "SOURCE-MANIFEST.sha256" -or
      -not $listedPaths.Add($relativePath)) {
    throw "Unsafe or duplicate SOURCE-MANIFEST path: $relativePath"
  }
  $candidate = [System.IO.Path]::GetFullPath(
    (Join-Path $bundleRoot $relativePath.Replace('/', '\')))
  if (-not $candidate.StartsWith($bundlePrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
      -not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
    throw "SOURCE-MANIFEST path escapes the bundle or is missing: $relativePath"
  }
  $actualHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualHash -cne $expectedHash) {
    throw "SOURCE-MANIFEST hash mismatch: $relativePath"
  }
}
$actualPaths = [System.Collections.Generic.HashSet[string]]::new(
  [System.StringComparer]::Ordinal)
foreach ($file in Get-ChildItem -LiteralPath $bundleRoot -File -Recurse) {
  if ($file.FullName -ceq $manifestPath) {
    continue
  }
  $relativePath = [System.IO.Path]::GetRelativePath($bundleRoot, $file.FullName).Replace('\', '/')
  if (-not $actualPaths.Add($relativePath)) {
    throw "Duplicate extracted source path: $relativePath"
  }
}
if ($listedPaths.Count -ne $actualPaths.Count -or
    @($actualPaths | Where-Object { -not $listedPaths.Contains($_) }).Count -ne 0) {
  throw "Extracted source files do not exactly match SOURCE-MANIFEST.sha256."
}
# ZIP stores a timezone-less DOS wall time. Normalize only after every archive
# byte and path has passed the manifest gate so local-time extraction cannot
# future-date CMake inputs and force an unbounded Ninja regeneration loop.
$normalizedSourceTimestampUtc = [DateTime]::new(
  2000, 1, 1, 0, 0, 0, [DateTimeKind]::Utc)
$verifiedExtractedItems = @(Get-ChildItem -LiteralPath $bundleRoot -Force -Recurse)
foreach ($item in $verifiedExtractedItems) {
  $item.LastWriteTimeUtc = $normalizedSourceTimestampUtc
}
$bundleRootItem = Get-Item -LiteralPath $bundleRoot -Force
$bundleRootItem.LastWriteTimeUtc = $normalizedSourceTimestampUtc
$normalizationCutoffUtc = [DateTime]::UtcNow
$normalizedItems = @($bundleRootItem) +
  @(Get-ChildItem -LiteralPath $bundleRoot -Force -Recurse)
if (@($normalizedItems | Where-Object {
      $_.LastWriteTimeUtc -ne $normalizedSourceTimestampUtc -or
      $_.LastWriteTimeUtc -gt $normalizationCutoffUtc
    }).Count -ne 0) {
  throw "Verified source timestamp normalization failed."
}
Write-Output (
  "Verified fixed-past source timestamps: {0:o}; itemCount={1}" -f
    $normalizedSourceTimestampUtc,
    $normalizedItems.Count)
if ($env:VSCMD_ARG_TGT_ARCH -cne "x64") {
  throw "Run these commands from an x64 Visual Studio 2022 developer environment."
}
foreach ($tool in @(
    "cl.exe", "lib.exe", "link.exe", "mt.exe", "rc.exe",
    "git.exe", "cmake.exe", "ctest.exe", "ninja.exe")) {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
    throw "Required build tool is unavailable: $tool"
  }
}
$commonLibDestination = Join-Path $bundleRoot "project/extern/CommonLibSSE-NG"
if (Test-Path -LiteralPath $commonLibDestination) {
  throw "Refusing to nest or overwrite an existing CommonLibSSE-NG destination."
}
New-Item -ItemType Directory (Split-Path -Parent $commonLibDestination) -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $bundleRoot "dependencies/CommonLibSSE-NG") -Destination $commonLibDestination -Recurse

$vcpkgRoot = Join-Path $bundleRoot "vcpkg"
if (Test-Path -LiteralPath $vcpkgRoot) {
  throw "Refusing to overwrite an existing vcpkg checkout."
}
Invoke-Checked { git clone https://github.com/microsoft/vcpkg.git $vcpkgRoot } "Clone vcpkg"
Invoke-Checked { git -C $vcpkgRoot checkout --detach {{VCPKG_BASELINE}} } "Check out the reviewed vcpkg baseline"
$actualVcpkgCommit = (git -C $vcpkgRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualVcpkgCommit -cne "{{VCPKG_BASELINE}}") {
  throw "Reconstructed vcpkg checkout does not equal the reviewed baseline."
}
Invoke-Checked { & (Join-Path $vcpkgRoot "bootstrap-vcpkg.bat") -disableMetrics } "Bootstrap vcpkg"
$env:VCPKG_ROOT = $vcpkgRoot
$env:VCPKG_BINARY_SOURCES = "clear"

$configureStartUtc = [DateTime]::UtcNow
$bundleFilesBeforeConfigure = @(
  Get-ChildItem -LiteralPath $bundleRoot -File -Force -Recurse)
if (@($bundleFilesBeforeConfigure | Where-Object {
      $_.LastWriteTimeUtc -gt $configureStartUtc
    }).Count -ne 0) {
  throw "A reconstructed build input is newer than the configure start time."
}
Write-Output (
  "Verified reconstructed inputs are not newer than configure start: {0:o}; fileCount={1}" -f
    $configureStartUtc,
    $bundleFilesBeforeConfigure.Count)

Set-Location (Join-Path $bundleRoot "project")
Invoke-Checked { cmake --fresh --preset release "-DFETCHCONTENT_SOURCE_DIR_HDE64=$bundleRoot/dependencies/MinHook" -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DCOMMONLIB_PREBUILT=OFF -DENABLE_SKYRIM_VR=OFF } "Configure Bounded Encounters"
Invoke-Checked { cmake --build .\build\release } "Build Bounded Encounters"
Invoke-Checked { ctest --test-dir .\build\release --output-on-failure } "Test Bounded Encounters"
```

The copied CommonLib tree is the exact fork source; the recorded OpenVR gitlink
is intentionally absent because VR is disabled and no OpenVR source is
compiled. The project root itself predeclares hde64 at the immutable reviewed
commit before CommonLib's tag-based declaration. The explicit CMake override
and `FETCHCONTENT_FULLY_DISCONNECTED=ON` independently force CommonLib to
consume the bundled MinHook tree without a FetchContent network request. Each
direct vcpkg dependency's port/ directory is the exact baseline
recipe and source/ is its exact post-patch audit tree. The two build-helper
directories contain their exact ports, installed host control scripts, SPDX,
status, inventory, ABI, and provenance. Verify them against
SOURCE-PROVENANCE.json.

After manifest verification and before any build mutation, the commands set
every verified extracted file and directory to a fixed past UTC modification
time. ZIP's DOS timestamp has no timezone; this metadata-only normalization
prevents local-time extraction from future-dating CMake inputs and forcing an
unbounded Ninja regeneration loop. It does not change manifest-covered bytes.

This is a complete source/provenance closure for the reviewed binary inputs,
not a turnkey offline compiler environment. Visual Studio, CMake, Ninja, the
vcpkg executable/registry data, downloaded upstream archives, and binary-cache
state are not bundled. The exact helper port/control-script closure and tracked
vcpkg scripts are audit source, not a pre-seeded tool installation. The two
tracked general-purpose TLS downloader executables are intentionally omitted;
their Git object IDs and SHA-256 values are recorded in SOURCE-PROVENANCE.json,
and neither is used by the reviewed build. The commands above obtain required
online inputs while forcing dependencies to build with the binary cache off. A
fully offline rebuild requires tools and downloads to be pre-seeded
independently and has not been claimed or tested; tools/package.ps1 itself
makes no network calls.
'@
    $sourceReadme = $sourceReadmeTemplate.
        Replace("{{VERSION}}", $Version).
        Replace("{{VCPKG_BASELINE}}", $vcpkgBaseline)
    Write-Utf8NoBomLf `
        -Path (Join-Path $correspondingSourcePayloadRoot "README-CORRESPONDING-SOURCE.md") `
        -Content $sourceReadme

    $sourcePeFiles = @(Get-ChildItem -LiteralPath $correspondingSourcePayloadRoot -File -Recurse |
        Where-Object {
            $_.Extension.ToLowerInvariant() -in @('.exe', '.dll', '.sys', '.com') -or
            (Test-IsPortableExecutable -Path $_.FullName)
        })
    if ($sourcePeFiles.Count -ne 0) {
        $sourcePePaths = ($sourcePeFiles | ForEach-Object {
                Get-RelativeSlashPath -Base $correspondingSourcePayloadRoot -Path $_.FullName
            }) -join ', '
        throw "Corresponding-source closure contains a forbidden PE file: $sourcePePaths"
    }

    $sourceManifestFiles = Get-ChildItem -LiteralPath $correspondingSourcePayloadRoot -File -Recurse |
        Where-Object { $_.Name -ne "SOURCE-MANIFEST.sha256" } |
        Sort-Object { Get-RelativeSlashPath -Base $correspondingSourcePayloadRoot -Path $_.FullName }
    $sourceManifestLines = foreach ($file in $sourceManifestFiles) {
        $relativePath = Get-RelativeSlashPath -Base $correspondingSourcePayloadRoot -Path $file.FullName
        "$(Get-FileSha256 -Path $file.FullName)  $relativePath"
    }
    Write-Utf8NoBomLf `
        -Path (Join-Path $correspondingSourcePayloadRoot "SOURCE-MANIFEST.sha256") `
        -Content ($sourceManifestLines -join "`n")
    foreach ($line in $sourceManifestLines) {
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') {
            throw "Internal corresponding-source manifest format failure: $line"
        }
        $expectedHash = $Matches[1]
        $relativePath = $Matches[2]
        $actualHash = Get-FileSha256 -Path (Join-Path $correspondingSourcePayloadRoot $relativePath)
        if ($actualHash -ne $expectedHash) {
            throw "Internal corresponding-source manifest verification failed: $relativePath"
        }
    }

    $metadata = [ordered]@{
        schemaVersion = 3
        name = "Bounded Encounters"
        version = $Version
        runtime = [ordered]@{
            skyrim = $Runtime
            skse = "2.3.1"
            addressLibraryFormat = 5
        }
        source = [ordered]@{
            repository = "https://github.com/Ensrick/skyrim-mod-assistant"
            path = "mods/bounded-encounters"
            commit = $commit
            dirty = $isDirty
            sourceDateEpoch = $epoch
        }
        buildInputs = [ordered]@{
            commonLibSseNgRepository = "https://github.com/Ensrick/CommonLibSSE-NG"
            commonLibSseNgCommit = $commonLibCommit
            commonLibSseNgUpstreamTag = $commonLibUpstreamTag
            commonLibSseNgUpstreamCommit = $commonLibParentCommit
            minHookRepository = "https://github.com/TsudaKageyu/minhook"
            minHookTag = $minHookTag
            minHookCommit = $minHookCommit
            minHookRootCmakeImmutablePinVerified = $true
            minHookCompiledSources = @(
                "src/hde/hde64.c",
                "src/hde/hde64.h",
                "src/hde/pstdint.h",
                "src/hde/table64.h"
            )
            vcpkgRepository = "https://github.com/microsoft/vcpkg"
            vcpkgBaseline = $vcpkgBaseline
            vcpkgCheckoutCommit = $vcpkgCommit
            vcpkgTargetTriplet = $triplet
            vcpkgHostTriplet = $helperTriplet
            vcpkgBinaryCacheDisabled = $binaryCacheDisabled -and $buildLogAudit.verifiedCacheDisabledSourceBuild
            vcpkgPackagingEnvironmentBinaryCacheDisabled = $binaryCacheDisabled
            vcpkgBuildLogAudit = $buildLogAudit
            vcpkgDependencies = $resolvedDependencies
            vcpkgBuildHelpers = $resolvedBuildHelpers
        }
        shippingConfiguration = [ordered]@{
            schemaVersion = $shippingConfig.schemaVersion
            enabled = $shippingConfig.enabled
            observeOnly = $shippingConfig.observeOnly
            debugLogging = $shippingConfig.debugLogging
            maximumNavmeshSnapDistance = [double]$shippingConfig.limits.maximumNavmeshSnapDistance
            allowedSourcePlugins = $shippingAllowedSourcePlugins
            schemaValidation = $schemaValidationEvidence
        }
        releaseEligible = $releaseEligible
    }
    Write-Utf8NoBomLf -Path (Join-Path $payloadRoot "BUILD-INFO.json") -Content (
        $metadata | ConvertTo-Json -Depth 8)

    $analyzedFiles = Get-ChildItem -LiteralPath $payloadRoot -File -Recurse |
        Sort-Object { Get-RelativeSlashPath -Base $payloadRoot -Path $_.FullName }
    $spdxFiles = @()
    $relationships = @(
        [ordered]@{
            spdxElementId = "SPDXRef-DOCUMENT"
            relationshipType = "DESCRIBES"
            relatedSpdxElement = "SPDXRef-Package-BoundedEncounters"
        }
    )
    $sha1Values = @()
    foreach ($file in $analyzedFiles) {
        $relativePath = Get-RelativeSlashPath -Base $payloadRoot -Path $file.FullName
        $identifierHash = (Get-StringSha256 -Value $relativePath).Substring(0, 16)
        $fileId = "SPDXRef-File-$identifierHash"
        $sha256 = Get-FileSha256 -Path $file.FullName
        $sha1 = Get-FileSha1 -Path $file.FullName
        $sha1Values += $sha1
        $fileType = if ($file.Extension.ToLowerInvariant() -in @(".dll", ".exe")) {
            "BINARY"
        } else {
            "TEXT"
        }
        $spdxFiles += [ordered]@{
            fileName = "./$relativePath"
            SPDXID = $fileId
            checksums = @(
                [ordered]@{ algorithm = "SHA256"; checksumValue = $sha256 },
                [ordered]@{ algorithm = "SHA1"; checksumValue = $sha1 }
            )
            fileTypes = @($fileType)
            licenseConcluded = "NOASSERTION"
            licenseInfoInFiles = @("NOASSERTION")
            copyrightText = "NOASSERTION"
        }
        $relationships += [ordered]@{
            spdxElementId = "SPDXRef-Package-BoundedEncounters"
            relationshipType = "CONTAINS"
            relatedSpdxElement = $fileId
        }
    }

    $verificationInput = (($sha1Values | Sort-Object) -join "")
    $sha1Algorithm = [System.Security.Cryptography.SHA1]::Create()
    try {
        $verificationCode = [System.Convert]::ToHexString(
            $sha1Algorithm.ComputeHash([System.Text.Encoding]::ASCII.GetBytes($verificationInput))).ToLowerInvariant()
    } finally {
        $sha1Algorithm.Dispose()
    }

    $dependencyPackages = @(
        [ordered]@{
            name = "CommonLibSSE-NG (Ensrick no-modal-errors fork)"
            SPDXID = "SPDXRef-Package-CommonLibSSE-NG"
            versionInfo = $commonLibCommit
            downloadLocation = "https://github.com/Ensrick/CommonLibSSE-NG/tree/$commonLibCommit"
            filesAnalyzed = $false
            licenseConcluded = "GPL-3.0-or-later"
            licenseDeclared = "GPL-3.0-or-later"
            copyrightText = "NOASSERTION"
            sourceInfo = "Pinned Ensrick fork commit $commonLibCommit; direct parent is upstream v7.0.0 commit $commonLibParentCommit."
            licenseComments = "Distributed with the unchanged upstream EXCEPTIONS.md Modding Exception; exact fork corresponding source is emitted beside the binary archive."
        },
        [ordered]@{
            name = "MinHook hde64"
            SPDXID = "SPDXRef-Package-MinHook-hde64"
            versionInfo = "1.3.4"
            downloadLocation = "https://github.com/TsudaKageyu/minhook/tree/$minHookCommit"
            filesAnalyzed = $false
            licenseConcluded = "BSD-2-Clause"
            licenseDeclared = "BSD-2-Clause"
            copyrightText = "Copyright (C) 2009-2017 Tsuda Kageyu; hde64 portions copyright (c) 2008-2009 Vyacheslav Patkov"
            sourceInfo = "Pinned MinHook v1.3.4 commit $minHookCommit; only the hde64 decoder is compiled by CommonLibSSE-NG."
        }
    )
    $relationships += [ordered]@{
        spdxElementId = "SPDXRef-Package-BoundedEncounters"
        relationshipType = "STATIC_LINK"
        relatedSpdxElement = "SPDXRef-Package-CommonLibSSE-NG"
    }
    $relationships += [ordered]@{
        spdxElementId = "SPDXRef-Package-BoundedEncounters"
        relationshipType = "STATIC_LINK"
        relatedSpdxElement = "SPDXRef-Package-MinHook-hde64"
    }

    foreach ($dependency in $resolvedDependencies) {
        $dependencyName = [string]$dependency.name
        $dependencyId = "SPDXRef-Package-vcpkg-" + ($dependencyName -replace '[^A-Za-z0-9.-]', '-')
        $dependencyVersionInfo = if ([int]$dependency.portVersion -eq 0) {
            [string]$dependency.version
        } else {
            "$($dependency.version)#$($dependency.portVersion)"
        }
        $dependencyPackages += [ordered]@{
            name = $dependencyName
            SPDXID = $dependencyId
            versionInfo = $dependencyVersionInfo
            downloadLocation = "git+https://github.com/microsoft/vcpkg@$($dependency.portTree)"
            filesAnalyzed = $false
            licenseConcluded = [string]$dependency.license
            licenseDeclared = [string]$dependency.license
            copyrightText = "NOASSERTION"
            sourceInfo = "Resolved by vcpkg baseline $vcpkgBaseline for $triplet; ABI $($dependency.abi); exact post-patch source is in the corresponding-source archive."
            externalRefs = @(
                [ordered]@{
                    referenceCategory = "PACKAGE-MANAGER"
                    referenceType = "purl"
                    referenceLocator = "pkg:vcpkg/$dependencyName@$($dependency.version)?port_version=$($dependency.portVersion)&triplet=$triplet"
                }
            )
        }
        $relationships += [ordered]@{
            spdxElementId = "SPDXRef-Package-BoundedEncounters"
            relationshipType = "DEPENDS_ON"
            relatedSpdxElement = $dependencyId
        }
    }

    foreach ($helper in $resolvedBuildHelpers) {
        $helperName = [string]$helper.name
        $helperId = "SPDXRef-Package-vcpkg-build-helper-" + (
            $helperName -replace '[^A-Za-z0-9.-]', '-')
        $helperVersionInfo = if ([int]$helper.portVersion -eq 0) {
            [string]$helper.version
        } else {
            "$($helper.version)#$($helper.portVersion)"
        }
        $dependencyPackages += [ordered]@{
            name = $helperName
            SPDXID = $helperId
            versionInfo = $helperVersionInfo
            downloadLocation = "git+https://github.com/microsoft/vcpkg@$($helper.portTree)"
            filesAnalyzed = $false
            licenseConcluded = [string]$helper.license
            licenseDeclared = [string]$helper.license
            copyrightText = "NOASSERTION"
            sourceInfo = "Source-free vcpkg build helper resolved at baseline $vcpkgBaseline for $helperTriplet; ABI $($helper.abi). Exact port and installed control-script closure are in the corresponding-source archive."
            externalRefs = @(
                [ordered]@{
                    referenceCategory = "PACKAGE-MANAGER"
                    referenceType = "purl"
                    referenceLocator = "pkg:vcpkg/$helperName@$($helper.version)?port_version=$($helper.portVersion)&triplet=$helperTriplet"
                }
            )
        }
        $relationships += [ordered]@{
            spdxElementId = $helperId
            relationshipType = "BUILD_DEPENDENCY_OF"
            relatedSpdxElement = "SPDXRef-Package-BoundedEncounters"
        }
    }

    $documentNamespaceSuffix = Get-StringSha256 -Value "$Version|$Runtime|$commit"
    $mainPackage = [ordered]@{
        name = "Bounded Encounters"
        SPDXID = "SPDXRef-Package-BoundedEncounters"
        versionInfo = $Version
        downloadLocation = "https://github.com/Ensrick/skyrim-mod-assistant/tree/$commit/mods/bounded-encounters"
        filesAnalyzed = $true
        packageVerificationCode = [ordered]@{
            packageVerificationCodeValue = $verificationCode
            packageVerificationCodeExcludedFiles = @("SBOM.spdx.json", "MANIFEST.sha256")
        }
        licenseConcluded = "NOASSERTION"
        licenseDeclared = "MIT"
        licenseComments = "The original Bounded Encounters source is declared MIT. The analyzed distribution includes a DLL statically linked with GPL-3.0-or-later CommonLibSSE-NG under its unchanged EXCEPTIONS.md; linked and dependency packages below retain their controlling terms. No standard SPDX exception identifier is asserted for that custom text."
        copyrightText = "Copyright (c) 2026 Ensrick"
        externalRefs = @(
            [ordered]@{
                referenceCategory = "PACKAGE-MANAGER"
                referenceType = "purl"
                referenceLocator = "pkg:github/Ensrick/skyrim-mod-assistant@$commit#mods/bounded-encounters"
            }
        )
    }

    $sbom = [ordered]@{
        spdxVersion = "SPDX-2.3"
        dataLicense = "CC0-1.0"
        SPDXID = "SPDXRef-DOCUMENT"
        name = "BoundedEncounters-$Version"
        documentNamespace = "https://github.com/Ensrick/skyrim-mod-assistant/spdx/bounded-encounters/$documentNamespaceSuffix"
        creationInfo = [ordered]@{
            created = $sourceTimestamp.ToString("yyyy-MM-ddTHH:mm:ssZ", [System.Globalization.CultureInfo]::InvariantCulture)
            creators = @("Tool: BoundedEncounters/tools/package.ps1", "Organization: Ensrick")
        }
        packages = @($mainPackage) + $dependencyPackages
        files = $spdxFiles
        relationships = $relationships
    }
    Write-Utf8NoBomLf -Path (Join-Path $payloadRoot "SBOM.spdx.json") -Content (
        $sbom | ConvertTo-Json -Depth 12)

    $manifestFiles = Get-ChildItem -LiteralPath $payloadRoot -File -Recurse |
        Where-Object { $_.Name -ne "MANIFEST.sha256" } |
        Sort-Object { Get-RelativeSlashPath -Base $payloadRoot -Path $_.FullName }
    $manifestLines = foreach ($file in $manifestFiles) {
        $relativePath = Get-RelativeSlashPath -Base $payloadRoot -Path $file.FullName
        "$(Get-FileSha256 -Path $file.FullName)  $relativePath"
    }
    Write-Utf8NoBomLf -Path (Join-Path $payloadRoot "MANIFEST.sha256") -Content (
        $manifestLines -join "`n")

    foreach ($line in $manifestLines) {
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') {
            throw "Internal manifest format failure: $line"
        }
        $expectedHash = $Matches[1]
        $relativePath = $Matches[2]
        $actualHash = Get-FileSha256 -Path (Join-Path $payloadRoot $relativePath)
        if ($actualHash -ne $expectedHash) {
            throw "Internal manifest verification failed: $relativePath"
        }
    }

    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $nonReleaseSuffix = if ($isDirty) {
        "-dirty"
    } elseif (-not $releaseEligible) {
        "-nonrelease"
    } else {
        ""
    }
    $archiveName = "BoundedEncounters-$Version-Skyrim-$Runtime-win64$nonReleaseSuffix.zip"
    $archivePath = Join-Path $OutputDirectory $archiveName
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    New-DeterministicZip -PayloadRoot $payloadRoot -ArchivePath $archivePath -Timestamp $zipTimestamp
    Assert-DeterministicZipMetadata -ArchivePath $archivePath -ExpectedTimestamp $zipTimestamp

    $archiveHash = Get-FileSha256 -Path $archivePath
    $hashPath = "$archivePath.sha256"
    Write-Utf8NoBomLf -Path $hashPath -Content "$archiveHash  $archiveName"

    $correspondingSourceArchiveName = "BoundedEncounters-$Version-corresponding-source$nonReleaseSuffix.zip"
    $correspondingSourceArchivePath = Join-Path $OutputDirectory $correspondingSourceArchiveName
    if (Test-Path -LiteralPath $correspondingSourceArchivePath) {
        Remove-Item -LiteralPath $correspondingSourceArchivePath -Force
    }
    New-DeterministicZip `
        -PayloadRoot $correspondingSourcePayloadRoot `
        -ArchivePath $correspondingSourceArchivePath `
        -Timestamp $zipTimestamp
    Assert-DeterministicZipMetadata `
        -ArchivePath $correspondingSourceArchivePath `
        -ExpectedTimestamp $zipTimestamp
    $correspondingSourceArchiveHash = Get-FileSha256 -Path $correspondingSourceArchivePath
    $correspondingSourceHashPath = "$correspondingSourceArchivePath.sha256"
    Write-Utf8NoBomLf `
        -Path $correspondingSourceHashPath `
        -Content "$correspondingSourceArchiveHash  $correspondingSourceArchiveName"

    [ordered]@{
        archive = $archivePath
        sha256 = $archiveHash
        hashFile = $hashPath
        correspondingSourceArchive = $correspondingSourceArchivePath
        correspondingSourceSha256 = $correspondingSourceArchiveHash
        correspondingSourceHashFile = $correspondingSourceHashPath
        sourceCommit = $commit
        sourceDateEpoch = $epoch
        releaseEligible = $releaseEligible
    } | ConvertTo-Json -Depth 4
} finally {
    $resolvedWorkRoot = [System.IO.Path]::GetFullPath($workRoot)
    if ($resolvedWorkRoot.StartsWith($temporaryBase, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedWorkRoot).StartsWith("BoundedEncounters-package-", [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedWorkRoot -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        throw "Refusing to remove unexpected packaging work directory: $resolvedWorkRoot"
    }
}
