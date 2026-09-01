#Requires -Version 7.4

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ReferenceDirectory,
    [Parameter(Mandatory = $true)][string]$CandidateDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$versionHeader = Get-Content -LiteralPath (Join-Path $repoRoot "src/Version.h") -Raw
if ($versionHeader -notmatch 'Semantic\s*=\s*"([^"]+)"') {
    throw "Unable to read the Bounded Encounters semantic version."
}
$version = $Matches[1]
if ($versionHeader -notmatch 'SupportedRuntime\s*\{\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\}') {
    throw "Unable to read the Bounded Encounters Skyrim runtime."
}
$runtime = "$($Matches[1]).$($Matches[2]).$($Matches[3]).$($Matches[4])"

$referenceRoot = [System.IO.Path]::GetFullPath($ReferenceDirectory)
$candidateRoot = [System.IO.Path]::GetFullPath($CandidateDirectory)
foreach ($directory in @($referenceRoot, $candidateRoot)) {
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        throw "Package comparison directory is missing: $directory"
    }
    $item = Get-Item -LiteralPath $directory -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Package comparison directory is a reparse point: $directory"
    }
}

$binaryName = "BoundedEncounters-$version-Skyrim-$runtime-win64.zip"
$sourceName = "BoundedEncounters-$version-corresponding-source.zip"
$expectedNames = @(
    $binaryName,
    "$binaryName.sha256",
    $sourceName,
    "$sourceName.sha256")
[System.Array]::Sort[string]($expectedNames, [System.StringComparer]::Ordinal)

function Get-ExactFiles {
    param([Parameter(Mandatory = $true)][string]$Directory)

    $items = @(Get-ChildItem -LiteralPath $Directory -Force)
    foreach ($item in $items) {
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Package comparison directory contains a reparse point: $Directory :: $($item.Name)"
        }
        if ($item -isnot [System.IO.FileInfo]) {
            throw "Package comparison directory contains a non-file entry: $Directory :: $($item.Name)"
        }
    }
    $files = @($items)
    [string[]]$actualNames = @($files | ForEach-Object Name)
    [System.Array]::Sort[string]($actualNames, [System.StringComparer]::Ordinal)
    if ($actualNames.Count -ne $expectedNames.Count) {
        throw "Package comparison directory has an unexpected file count: $Directory"
    }
    for ($index = 0; $index -lt $expectedNames.Count; ++$index) {
        if ($actualNames[$index] -cne $expectedNames[$index]) {
            throw "Package comparison directory has an unexpected file set: $Directory"
        }
    }
    return $files
}

function Test-FilesByteEqual {
    param(
        [Parameter(Mandatory = $true)][string]$Left,
        [Parameter(Mandatory = $true)][string]$Right
    )

    $leftInfo = Get-Item -LiteralPath $Left
    $rightInfo = Get-Item -LiteralPath $Right
    if ($leftInfo.Length -ne $rightInfo.Length) {
        return $false
    }
    $leftStream = [System.IO.File]::OpenRead($Left)
    $rightStream = [System.IO.File]::OpenRead($Right)
    try {
        $leftBuffer = [byte[]]::new(1024 * 1024)
        $rightBuffer = [byte[]]::new(1024 * 1024)
        while ($true) {
            $leftRead = $leftStream.Read($leftBuffer, 0, $leftBuffer.Length)
            $rightRead = $rightStream.Read($rightBuffer, 0, $rightBuffer.Length)
            if ($leftRead -ne $rightRead) {
                return $false
            }
            if ($leftRead -eq 0) {
                return $true
            }
            for ($index = 0; $index -lt $leftRead; ++$index) {
                if ($leftBuffer[$index] -ne $rightBuffer[$index]) {
                    return $false
                }
            }
        }
    } finally {
        $rightStream.Dispose()
        $leftStream.Dispose()
    }
}

function Assert-SafeArchiveEntryPath {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string]$EntryPath,
        [AllowEmptyCollection()]
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.HashSet[string]]$CaseInsensitivePaths,
        [AllowEmptyCollection()]
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.HashSet[string]]$CaseInsensitiveDirectoryPrefixes
    )

    $segments = @($EntryPath.Split('/'))
    if ([string]::IsNullOrWhiteSpace($EntryPath) -or
        $EntryPath.Contains('\', [System.StringComparison]::Ordinal) -or
        [System.IO.Path]::IsPathRooted($EntryPath) -or
        $EntryPath.Contains(':', [System.StringComparison]::Ordinal) -or
        $EntryPath.StartsWith('/', [System.StringComparison]::Ordinal) -or
        @($segments | Where-Object { $_ -in @("", ".", "..") }).Count -ne 0 -or
        -not $CaseInsensitivePaths.Add($EntryPath)) {
        throw "Archive contains an unsafe or duplicate path: $ArchivePath :: $EntryPath"
    }
    foreach ($segment in $segments) {
        if ($segment.EndsWith('.', [System.StringComparison]::Ordinal) -or
            $segment.EndsWith(' ', [System.StringComparison]::Ordinal) -or
            $segment.IndexOfAny([char[]]'<>"|?*') -ge 0 -or
            @($segment.ToCharArray() | Where-Object { [int]$_ -lt 32 }).Count -ne 0 -or
            $segment -match '^(?i:con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)') {
            throw "Archive contains a path that is unsafe on Windows: $ArchivePath :: $EntryPath"
        }
    }
    if ($CaseInsensitiveDirectoryPrefixes.Contains($EntryPath)) {
        throw "Archive contains a file/directory prefix collision: $ArchivePath :: $EntryPath"
    }
    $prefix = ""
    for ($index = 0; $index -lt $segments.Count - 1; ++$index) {
        $prefix = if ($index -eq 0) {
            $segments[$index]
        } else {
            "$prefix/$($segments[$index])"
        }
        if ($CaseInsensitivePaths.Contains($prefix)) {
            throw "Archive contains a file/directory prefix collision: $ArchivePath :: $EntryPath"
        }
        $null = $CaseInsensitiveDirectoryPrefixes.Add($prefix)
    }
}

function Get-StreamSha256 {
    param([Parameter(Mandatory = $true)][System.IO.Stream]$Stream)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.Convert]::ToHexString(
            $algorithm.ComputeHash($Stream)).ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
    }
}

function ConvertFrom-StrictUtf8Bytes {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$Description,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if ($Bytes.Length -ge 3 -and
        $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
        throw "$Description must be UTF-8 without a BOM: $Context"
    }
    try {
        $text = [System.Text.UTF8Encoding]::new($false, $true).GetString($Bytes)
    } catch {
        throw "$Description is not valid UTF-8: $Context"
    }
    if ($text.Contains("`r", [System.StringComparison]::Ordinal)) {
        throw "$Description must use LF line endings: $Context"
    }
    return $text
}

function Read-StrictManifestText {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.Compression.ZipArchiveEntry]$Entry,
        [Parameter(Mandatory = $true)][string]$ArchivePath
    )

    $entryStream = $Entry.Open()
    $memory = [System.IO.MemoryStream]::new()
    try {
        $entryStream.CopyTo($memory)
        $bytes = $memory.ToArray()
    } finally {
        $memory.Dispose()
        $entryStream.Dispose()
    }
    return ConvertFrom-StrictUtf8Bytes `
        -Bytes $bytes `
        -Description "Archive manifest" `
        -Context "$ArchivePath :: $($Entry.FullName)"
}

function Assert-SiblingHash {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$ArchiveName
    )

    $archivePath = Join-Path $Directory $ArchiveName
    $hashPath = "$archivePath.sha256"
    $text = ConvertFrom-StrictUtf8Bytes `
        -Bytes ([System.IO.File]::ReadAllBytes($hashPath)) `
        -Description "Sibling hash file" `
        -Context $hashPath
    if (-not $text.EndsWith("`n", [System.StringComparison]::Ordinal) -or
        $text.EndsWith("`n`n", [System.StringComparison]::Ordinal) -or
        $text.Substring(0, $text.Length - 1).Contains("`n", [System.StringComparison]::Ordinal)) {
        throw "Sibling hash file must contain exactly one LF-terminated line: $hashPath"
    }
    $line = $text.Substring(0, $text.Length - 1)
    if ($line -cnotmatch '^([0-9a-f]{64})  (.+)$' -or $Matches[2] -cne $ArchiveName) {
        throw "Malformed sibling hash file: $hashPath"
    }
    $actual = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -cne $Matches[1]) {
        throw "Sibling hash does not match its archive: $hashPath"
    }
    return $actual
}

function Assert-ZipOrderingAndManifest {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )

    $stream = [System.IO.File]::OpenRead($ArchivePath)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $stream,
            [System.IO.Compression.ZipArchiveMode]::Read,
            $false)
        try {
            $caseInsensitivePaths = [System.Collections.Generic.HashSet[string]]::new(
                [System.StringComparer]::OrdinalIgnoreCase)
            $caseInsensitiveDirectoryPrefixes = [System.Collections.Generic.HashSet[string]]::new(
                [System.StringComparer]::OrdinalIgnoreCase)
            $entryPaths = [System.Collections.Generic.List[string]]::new()
            $entriesByPath = [System.Collections.Generic.Dictionary[
                string, System.IO.Compression.ZipArchiveEntry]]::new(
                [System.StringComparer]::Ordinal)
            $manifestEntry = $null
            $previousPath = $null
            foreach ($entry in $archive.Entries) {
                $path = $entry.FullName
                Assert-SafeArchiveEntryPath `
                    -ArchivePath $ArchivePath `
                    -EntryPath $path `
                    -CaseInsensitivePaths $caseInsensitivePaths `
                    -CaseInsensitiveDirectoryPrefixes $caseInsensitiveDirectoryPrefixes
                $timestamp = $entry.LastWriteTime
                if ($timestamp.Year -ne 1980 -or $timestamp.Month -ne 1 -or
                    $timestamp.Day -ne 1 -or $timestamp.Hour -ne 0 -or
                    $timestamp.Minute -ne 0 -or $timestamp.Second -ne 0 -or
                    $entry.ExternalAttributes -ne 0) {
                    throw "Archive entry metadata is not canonical: $ArchivePath :: $path"
                }
                if ($null -ne $previousPath -and
                    [System.StringComparer]::Ordinal.Compare($previousPath, $path) -ge 0) {
                    throw "Archive entries are not in strict ordinal path order: $ArchivePath :: $previousPath then $path"
                }
                $entryPaths.Add($path)
                $entriesByPath.Add($path, $entry)
                $previousPath = $path
                if ($path -ceq $ManifestPath) {
                    $manifestEntry = $entry
                }
            }
            if ($null -eq $manifestEntry) {
                throw "Archive manifest entry is missing: $ArchivePath :: $ManifestPath"
            }

            $manifestText = Read-StrictManifestText `
                -Entry $manifestEntry `
                -ArchivePath $ArchivePath
            if (-not $manifestText.EndsWith("`n", [System.StringComparison]::Ordinal) -or
                $manifestText.EndsWith("`n`n", [System.StringComparison]::Ordinal)) {
                throw "Archive manifest must end with exactly one LF: $ArchivePath :: $ManifestPath"
            }
            $manifestLines = @($manifestText.Substring(0, $manifestText.Length - 1).Split("`n"))
            $manifestPaths = [System.Collections.Generic.List[string]]::new()
            $previousManifestPath = $null
            foreach ($line in $manifestLines) {
                if ($line -cnotmatch '^([0-9a-f]{64})  (.+)$') {
                    throw "Archive manifest contains a malformed line: $ArchivePath :: $ManifestPath"
                }
                $expectedHash = $Matches[1]
                $path = $Matches[2]
                if ($null -ne $previousManifestPath -and
                    [System.StringComparer]::Ordinal.Compare($previousManifestPath, $path) -ge 0) {
                    throw "Archive manifest paths are not in strict ordinal order: $ArchivePath :: $previousManifestPath then $path"
                }
                $manifestPaths.Add($path)
                $previousManifestPath = $path

                if (-not $entriesByPath.ContainsKey($path) -or $path -ceq $ManifestPath) {
                    throw "Archive manifest names an absent or self-referential path: $ArchivePath :: $path"
                }
                $entryStream = $entriesByPath[$path].Open()
                try {
                    $actualHash = Get-StreamSha256 -Stream $entryStream
                } finally {
                    $entryStream.Dispose()
                }
                if ($actualHash -cne $expectedHash) {
                    throw "Archive manifest hash does not match its entry: $ArchivePath :: $path"
                }
            }

            [string[]]$expectedManifestPaths = @($entryPaths | Where-Object { $_ -cne $ManifestPath })
            if ($manifestPaths.Count -ne $expectedManifestPaths.Count) {
                throw "Archive manifest does not cover the exact non-manifest entry count: $ArchivePath"
            }
            for ($index = 0; $index -lt $expectedManifestPaths.Count; ++$index) {
                if ($manifestPaths[$index] -cne $expectedManifestPaths[$index]) {
                    throw "Archive manifest path set or order differs from the archive: $ArchivePath"
                }
            }
            return [pscustomobject]@{
                entryCount = $entryPaths.Count
                manifestEntryCount = $manifestPaths.Count
                ordinalOrderVerified = $true
                manifestHashesVerified = $true
                strictUtf8LfVerified = $true
                windowsSafePathsVerified = $true
                canonicalMetadataVerified = $true
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

function Get-ZipEntryHash {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string]$EntryPath
    )

    $stream = [System.IO.File]::OpenRead($ArchivePath)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $stream,
            [System.IO.Compression.ZipArchiveMode]::Read,
            $false)
        try {
            $caseInsensitivePaths = [System.Collections.Generic.HashSet[string]]::new(
                [System.StringComparer]::OrdinalIgnoreCase)
            $caseInsensitiveDirectoryPrefixes = [System.Collections.Generic.HashSet[string]]::new(
                [System.StringComparer]::OrdinalIgnoreCase)
            $selected = $null
            foreach ($entry in $archive.Entries) {
                $path = $entry.FullName
                Assert-SafeArchiveEntryPath `
                    -ArchivePath $ArchivePath `
                    -EntryPath $path `
                    -CaseInsensitivePaths $caseInsensitivePaths `
                    -CaseInsensitiveDirectoryPrefixes $caseInsensitiveDirectoryPrefixes
                if ($path -ceq $EntryPath) {
                    $selected = $entry
                }
            }
            if ($null -eq $selected) {
                throw "Required archive entry is missing: $ArchivePath :: $EntryPath"
            }
            $entryStream = $selected.Open()
            try {
                return Get-StreamSha256 -Stream $entryStream
            } finally {
                $entryStream.Dispose()
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

Add-Type -AssemblyName System.IO.Compression
$null = Get-ExactFiles -Directory $referenceRoot
$null = Get-ExactFiles -Directory $candidateRoot

$fileEvidence = @()
foreach ($name in $expectedNames) {
    $referencePath = Join-Path $referenceRoot $name
    $candidatePath = Join-Path $candidateRoot $name
    $referenceHash = (Get-FileHash -LiteralPath $referencePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $candidateHash = (Get-FileHash -LiteralPath $candidatePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($referenceHash -cne $candidateHash -or
        -not (Test-FilesByteEqual -Left $referencePath -Right $candidatePath)) {
        throw "Independent package candidates are not byte-identical: $name ($referenceHash != $candidateHash)"
    }
    $fileEvidence += [ordered]@{
        name = $name
        length = (Get-Item -LiteralPath $referencePath).Length
        sha256 = $referenceHash
    }
}

$binarySha256 = Assert-SiblingHash -Directory $referenceRoot -ArchiveName $binaryName
$null = Assert-SiblingHash -Directory $candidateRoot -ArchiveName $binaryName
$sourceSha256 = Assert-SiblingHash -Directory $referenceRoot -ArchiveName $sourceName
$null = Assert-SiblingHash -Directory $candidateRoot -ArchiveName $sourceName
$binaryArchivePath = Join-Path $referenceRoot $binaryName
$sourceArchivePath = Join-Path $referenceRoot $sourceName
$binaryOrdering = Assert-ZipOrderingAndManifest `
    -ArchivePath $binaryArchivePath `
    -ManifestPath "MANIFEST.sha256"
$sourceOrdering = Assert-ZipOrderingAndManifest `
    -ArchivePath $sourceArchivePath `
    -ManifestPath "SOURCE-MANIFEST.sha256"
$dllSha256 = Get-ZipEntryHash -ArchivePath $binaryArchivePath -EntryPath "SKSE/Plugins/BoundedEncounters.dll"
$simulatorSha256 = Get-ZipEntryHash -ArchivePath $binaryArchivePath -EntryPath "tools/BoundedEncounters.Simulate.exe"

[ordered]@{
    schemaVersion = 1
    version = $version
    runtime = $runtime
    referenceDirectory = $referenceRoot
    candidateDirectory = $candidateRoot
    byteIdentical = $true
    binaryArchiveSha256 = $binarySha256
    correspondingSourceArchiveSha256 = $sourceSha256
    dllSha256 = $dllSha256
    simulatorSha256 = $simulatorSha256
    ordering = [ordered]@{
        binary = $binaryOrdering
        correspondingSource = $sourceOrdering
    }
    files = $fileEvidence
} | ConvertTo-Json -Depth 6
