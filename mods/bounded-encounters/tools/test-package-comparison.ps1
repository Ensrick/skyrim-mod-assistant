#Requires -Version 7.4

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression

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
$binaryName = "BoundedEncounters-$version-Skyrim-$runtime-win64.zip"
$sourceName = "BoundedEncounters-$version-corresponding-source.zip"
$comparator = Join-Path $PSScriptRoot "compare-package-directories.ps1"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$canonicalTimestamp = [System.DateTimeOffset]::new(
    1980, 1, 1, 0, 0, 0, [System.TimeSpan]::Zero)

function ConvertTo-Utf8Bytes {
    param([Parameter(Mandatory = $true)][string]$Value)

    return ,$utf8NoBom.GetBytes($Value)
}

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.Convert]::ToHexString(
            $algorithm.ComputeHash($Bytes)).ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
    }
}

function Get-ManifestBytes {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.Dictionary[string, byte[]]]$PayloadEntries,
        [Parameter(Mandatory = $true)][string]$Mode
    )

    [string[]]$paths = @($PayloadEntries.Keys)
    [System.Array]::Sort[string]($paths, [System.StringComparer]::Ordinal)
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($path in $paths) {
        $lines.Add("$(Get-BytesSha256 -Bytes $PayloadEntries[$path])  $path")
    }
    switch ($Mode) {
        "unordered" {
            $first = $lines[0]
            $lines[0] = $lines[1]
            $lines[1] = $first
        }
        "stale-hash" {
            $lines[0] = ("0" * 64) + $lines[0].Substring(64)
        }
        "missing" {
            $lines.RemoveAt($lines.Count - 1)
        }
        { $_ -in @("valid", "crlf", "bom", "invalid-utf8") } {}
        default { throw "Unknown manifest fixture mode: $Mode" }
    }

    $separator = if ($Mode -ceq "crlf") { "`r`n" } else { "`n" }
    [byte[]]$content = ConvertTo-Utf8Bytes -Value (
        [string]::Join($separator, $lines) + $separator)
    if ($Mode -ceq "invalid-utf8") {
        return ,([byte[]]@(0xFF, 0xFE, 0x0A))
    }
    if ($Mode -cne "bom") {
        return ,$content
    }
    $withBom = [byte[]]::new($content.Length + 3)
    $withBom[0] = 0xEF
    $withBom[1] = 0xBB
    $withBom[2] = 0xBF
    [System.Array]::Copy($content, 0, $withBom, 3, $content.Length)
    return ,$withBom
}

function New-TestArchive {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.Dictionary[string, byte[]]]$PayloadEntries,
        [Parameter(Mandatory = $true)][string]$ManifestMode,
        [Parameter(Mandatory = $true)][string]$ArchiveMode,
        [Parameter(Mandatory = $true)][string]$MetadataMode
    )

    $entries = [System.Collections.Generic.Dictionary[string, byte[]]]::new(
        [System.StringComparer]::Ordinal)
    foreach ($path in $PayloadEntries.Keys) {
        $entries.Add($path, $PayloadEntries[$path])
    }
    $entries.Add($ManifestPath, (Get-ManifestBytes `
            -PayloadEntries $PayloadEntries `
            -Mode $ManifestMode))
    [string[]]$entryPaths = @($entries.Keys)
    [System.Array]::Sort[string]($entryPaths, [System.StringComparer]::Ordinal)
    if ($ArchiveMode -ceq "unordered") {
        $first = $entryPaths[1]
        $entryPaths[1] = $entryPaths[2]
        $entryPaths[2] = $first
    } elseif ($ArchiveMode -cne "ordered") {
        throw "Unknown archive fixture mode: $ArchiveMode"
    }

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
            foreach ($path in $entryPaths) {
                $entry = $archive.CreateEntry(
                    $path,
                    [System.IO.Compression.CompressionLevel]::NoCompression)
                $entry.LastWriteTime = if ($MetadataMode -ceq "wrong-timestamp" -and
                    $path -ceq $entryPaths[0]) {
                    [System.DateTimeOffset]::new(
                        1981, 1, 1, 0, 0, 0, [System.TimeSpan]::Zero)
                } else {
                    $canonicalTimestamp
                }
                $entry.ExternalAttributes = if ($MetadataMode -ceq "nonzero-attributes" -and
                    $path -ceq $entryPaths[0]) { 32 } else { 0 }
                if ($MetadataMode -notin @("canonical", "wrong-timestamp", "nonzero-attributes")) {
                    throw "Unknown metadata fixture mode: $MetadataMode"
                }
                $entryStream = $entry.Open()
                try {
                    $bytes = $entries[$path]
                    $entryStream.Write($bytes, 0, $bytes.Length)
                } finally {
                    $entryStream.Dispose()
                }
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

function Write-SiblingHash {
    param([Parameter(Mandatory = $true)][string]$ArchivePath)

    $name = Split-Path -Leaf $ArchivePath
    $hash = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText(
        "$ArchivePath.sha256",
        "$hash  $name`n",
        $utf8NoBom)
}

function New-TestPackageDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$CaseName
    )

    New-Item -ItemType Directory -Path $Directory | Out-Null
    $binaryPayload = [System.Collections.Generic.Dictionary[string, byte[]]]::new(
        [System.StringComparer]::Ordinal)
    $binaryPayload.Add(
        "SKSE/Plugins/BoundedEncounters.dll",
        (ConvertTo-Utf8Bytes -Value "test-dll"))
    $binaryPayload.Add("docs/readme.txt", (ConvertTo-Utf8Bytes -Value "test-doc"))
    $binaryPayload.Add(
        "tools/BoundedEncounters.Simulate.exe",
        (ConvertTo-Utf8Bytes -Value "test-simulator"))

    switch ($CaseName) {
        "trailing-dot" {
            $binaryPayload.Add("bad", (ConvertTo-Utf8Bytes -Value "one"))
            $binaryPayload.Add("bad.", (ConvertTo-Utf8Bytes -Value "two"))
        }
        "trailing-space" {
            $binaryPayload.Add("bad ", (ConvertTo-Utf8Bytes -Value "bad"))
        }
        "prefix-collision" {
            $binaryPayload.Add("a", (ConvertTo-Utf8Bytes -Value "one"))
            $binaryPayload.Add("a/b", (ConvertTo-Utf8Bytes -Value "two"))
        }
        "case-alias" {
            $binaryPayload.Add("docs/A.txt", (ConvertTo-Utf8Bytes -Value "one"))
            $binaryPayload.Add("docs/a.txt", (ConvertTo-Utf8Bytes -Value "two"))
        }
        "drive-path" {
            $binaryPayload.Add("C:/bad", (ConvertTo-Utf8Bytes -Value "bad"))
        }
        "device-name" {
            $binaryPayload.Add("docs/CON.txt", (ConvertTo-Utf8Bytes -Value "bad"))
        }
        "superscript-device-name" {
            $binaryPayload.Add("docs/COM¹.txt", (ConvertTo-Utf8Bytes -Value "bad"))
        }
        "invalid-character" {
            $binaryPayload.Add("docs/bad?.txt", (ConvertTo-Utf8Bytes -Value "bad"))
        }
    }

    $manifestMode = switch ($CaseName) {
        "unordered-manifest" { "unordered" }
        "stale-hash" { "stale-hash" }
        "crlf-manifest" { "crlf" }
        "bom-manifest" { "bom" }
        "invalid-utf8-manifest" { "invalid-utf8" }
        "missing-manifest-entry" { "missing" }
        default { "valid" }
    }
    $archiveMode = if ($CaseName -ceq "unordered-zip") { "unordered" } else { "ordered" }
    $metadataMode = switch ($CaseName) {
        "wrong-timestamp" { "wrong-timestamp" }
        "nonzero-attributes" { "nonzero-attributes" }
        default { "canonical" }
    }

    $binaryPath = Join-Path $Directory $binaryName
    New-TestArchive `
        -ArchivePath $binaryPath `
        -ManifestPath "MANIFEST.sha256" `
        -PayloadEntries $binaryPayload `
        -ManifestMode $manifestMode `
        -ArchiveMode $archiveMode `
        -MetadataMode $metadataMode

    $sourcePayload = [System.Collections.Generic.Dictionary[string, byte[]]]::new(
        [System.StringComparer]::Ordinal)
    $sourcePayload.Add("docs/source.txt", (ConvertTo-Utf8Bytes -Value "source-doc"))
    $sourcePayload.Add("src/main.cpp", (ConvertTo-Utf8Bytes -Value "source-code"))
    $sourcePath = Join-Path $Directory $sourceName
    New-TestArchive `
        -ArchivePath $sourcePath `
        -ManifestPath "SOURCE-MANIFEST.sha256" `
        -PayloadEntries $sourcePayload `
        -ManifestMode "valid" `
        -ArchiveMode "ordered" `
        -MetadataMode "canonical"
    Write-SiblingHash -ArchivePath $binaryPath
    Write-SiblingHash -ArchivePath $sourcePath
    $binarySidecar = "$binaryPath.sha256"
    if ($CaseName -in @(
            "sidecar-crlf",
            "sidecar-bom",
            "sidecar-invalid-utf8",
            "sidecar-extra-lf")) {
        $hash = (Get-FileHash -LiteralPath $binaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
        [byte[]]$sidecarBytes = switch ($CaseName) {
            "sidecar-crlf" {
                ConvertTo-Utf8Bytes -Value "$hash  $binaryName`r`n"
            }
            "sidecar-bom" {
                $content = ConvertTo-Utf8Bytes -Value "$hash  $binaryName`n"
                $withBom = [byte[]]::new($content.Length + 3)
                $withBom[0] = 0xEF
                $withBom[1] = 0xBB
                $withBom[2] = 0xBF
                [System.Array]::Copy($content, 0, $withBom, 3, $content.Length)
                ,$withBom
            }
            "sidecar-invalid-utf8" {
                ,([byte[]]@(0xFF, 0xFE, 0x0A))
            }
            "sidecar-extra-lf" {
                ConvertTo-Utf8Bytes -Value "$hash  $binaryName`n`n"
            }
        }
        [System.IO.File]::WriteAllBytes($binarySidecar, $sidecarBytes)
    }
}

$cases = @(
    [ordered]@{ name = "valid"; expected = $null },
    [ordered]@{ name = "unordered-zip"; expected = "not in strict ordinal path order" },
    [ordered]@{ name = "unordered-manifest"; expected = "manifest paths are not in strict ordinal order" },
    [ordered]@{ name = "stale-hash"; expected = "manifest hash does not match its entry" },
    [ordered]@{ name = "crlf-manifest"; expected = "must use LF line endings" },
    [ordered]@{ name = "bom-manifest"; expected = "must be UTF-8 without a BOM" },
    [ordered]@{ name = "invalid-utf8-manifest"; expected = "is not valid UTF-8" },
    [ordered]@{ name = "missing-manifest-entry"; expected = "does not cover the exact non-manifest entry count" },
    [ordered]@{ name = "trailing-dot"; expected = "unsafe on Windows" },
    [ordered]@{ name = "trailing-space"; expected = "unsafe on Windows" },
    [ordered]@{ name = "prefix-collision"; expected = "file/directory prefix collision" },
    [ordered]@{ name = "case-alias"; expected = "unsafe or duplicate path" },
    [ordered]@{ name = "drive-path"; expected = "unsafe or duplicate path" },
    [ordered]@{ name = "device-name"; expected = "unsafe on Windows" },
    [ordered]@{ name = "superscript-device-name"; expected = "unsafe on Windows" },
    [ordered]@{ name = "invalid-character"; expected = "unsafe on Windows" },
    [ordered]@{ name = "wrong-timestamp"; expected = "metadata is not canonical" },
    [ordered]@{ name = "nonzero-attributes"; expected = "metadata is not canonical" },
    [ordered]@{ name = "sidecar-crlf"; expected = "Sibling hash file must use LF line endings" },
    [ordered]@{ name = "sidecar-bom"; expected = "Sibling hash file must be UTF-8 without a BOM" },
    [ordered]@{ name = "sidecar-invalid-utf8"; expected = "Sibling hash file is not valid UTF-8" },
    [ordered]@{ name = "sidecar-extra-lf"; expected = "must contain exactly one LF-terminated line" })

$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$workRoot = Join-Path $temporaryBase (
    "BoundedEncounters-comparison-test-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workRoot | Out-Null
$assertions = 0
$rejectedCases = [System.Collections.Generic.List[string]]::new()
try {
    foreach ($case in $cases) {
        $caseRoot = Join-Path $workRoot $case.name
        $referenceRoot = Join-Path $caseRoot "reference"
        $candidateRoot = Join-Path $caseRoot "candidate"
        New-TestPackageDirectory -Directory $referenceRoot -CaseName $case.name
        New-Item -ItemType Directory -Path $candidateRoot | Out-Null
        foreach ($file in Get-ChildItem -LiteralPath $referenceRoot -File -Force) {
            Copy-Item -LiteralPath $file.FullName -Destination $candidateRoot
        }

        if ($null -eq $case.expected) {
            $report = (& $comparator `
                    -ReferenceDirectory $referenceRoot `
                    -CandidateDirectory $candidateRoot | Out-String) | ConvertFrom-Json
            foreach ($value in @(
                    $report.byteIdentical,
                    $report.ordering.binary.ordinalOrderVerified,
                    $report.ordering.binary.manifestHashesVerified,
                    $report.ordering.binary.strictUtf8LfVerified,
                    $report.ordering.binary.windowsSafePathsVerified,
                    $report.ordering.binary.canonicalMetadataVerified,
                    $report.ordering.correspondingSource.ordinalOrderVerified,
                    $report.ordering.correspondingSource.manifestHashesVerified,
                    $report.ordering.correspondingSource.strictUtf8LfVerified,
                    $report.ordering.correspondingSource.windowsSafePathsVerified,
                    $report.ordering.correspondingSource.canonicalMetadataVerified)) {
                if ($value -ne $true) {
                    throw "Valid comparison fixture did not report every required gate."
                }
                ++$assertions
            }
            continue
        }

        $rejected = $false
        try {
            $null = & $comparator `
                -ReferenceDirectory $referenceRoot `
                -CandidateDirectory $candidateRoot
        } catch {
            if ($_.Exception.Message -notmatch [regex]::Escape([string]$case.expected)) {
                throw "Fixture '$($case.name)' failed for the wrong reason: $($_.Exception.Message)"
            }
            $rejected = $true
        }
        if (-not $rejected) {
            throw "Malformed comparison fixture was accepted: $($case.name)"
        }
        $rejectedCases.Add($case.name)
        ++$assertions
    }

    [ordered]@{
        assertions = $assertions
        validFixture = "passed"
        rejectedCases = $rejectedCases
    } | ConvertTo-Json -Depth 4
} finally {
    $resolvedWorkRoot = [System.IO.Path]::GetFullPath($workRoot)
    if ($resolvedWorkRoot.StartsWith($temporaryBase, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedWorkRoot).StartsWith(
            "BoundedEncounters-comparison-test-",
            [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedWorkRoot -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        throw "Refusing to remove unexpected package-comparison test directory: $resolvedWorkRoot"
    }
}
