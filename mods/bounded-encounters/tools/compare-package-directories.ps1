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

    $nestedDirectories = @(Get-ChildItem -LiteralPath $Directory -Directory -Force -Recurse)
    if ($nestedDirectories.Count -ne 0) {
        throw "Package comparison directory contains nested directories: $Directory"
    }
    $files = @(Get-ChildItem -LiteralPath $Directory -File -Force)
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

function Assert-SiblingHash {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$ArchiveName
    )

    $archivePath = Join-Path $Directory $ArchiveName
    $hashPath = "$archivePath.sha256"
    $line = (Get-Content -LiteralPath $hashPath -Raw).Replace("`r`n", "`n").Replace("`r", "`n").TrimEnd("`n")
    if ($line -cnotmatch '^([0-9a-f]{64})  (.+)$' -or $Matches[2] -cne $ArchiveName) {
        throw "Malformed sibling hash file: $hashPath"
    }
    $actual = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -cne $Matches[1]) {
        throw "Sibling hash does not match its archive: $hashPath"
    }
    return $actual
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
            $selected = $null
            foreach ($entry in $archive.Entries) {
                $path = $entry.FullName
                if ([string]::IsNullOrWhiteSpace($path) -or
                    $path.Contains('\', [System.StringComparison]::Ordinal) -or
                    [System.IO.Path]::IsPathRooted($path) -or
                    $path.StartsWith('/', [System.StringComparison]::Ordinal) -or
                    @($path.Split('/') | Where-Object { $_ -in @("", ".", "..") }).Count -ne 0 -or
                    -not $caseInsensitivePaths.Add($path)) {
                    throw "Archive contains an unsafe or duplicate path: $ArchivePath :: $path"
                }
                if ($path -ceq $EntryPath) {
                    $selected = $entry
                }
            }
            if ($null -eq $selected) {
                throw "Required archive entry is missing: $ArchivePath :: $EntryPath"
            }
            $entryStream = $selected.Open()
            try {
                $algorithm = [System.Security.Cryptography.SHA256]::Create()
                try {
                    return [System.Convert]::ToHexString(
                        $algorithm.ComputeHash($entryStream)).ToLowerInvariant()
                } finally {
                    $algorithm.Dispose()
                }
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
    files = $fileEvidence
} | ConvertTo-Json -Depth 6
