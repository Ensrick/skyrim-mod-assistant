#Requires -Version 7.0

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

                $input = [System.IO.File]::OpenRead($file.FullName)
                $output = $entry.Open()
                try {
                    $input.CopyTo($output)
                } finally {
                    $output.Dispose()
                    $input.Dispose()
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
$zipTimestamp = if ($sourceTimestamp -lt $minimumZipTimestamp) {
    $minimumZipTimestamp
} else {
    $sourceTimestamp
}

$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$workRoot = Join-Path $temporaryBase ("BoundedEncounters-package-" + [System.Guid]::NewGuid().ToString("N"))
$payloadRoot = Join-Path $workRoot "payload"
$commonLibSourcePayloadRoot = Join-Path $workRoot "commonlib-source"

New-Item -ItemType Directory -Path $payloadRoot,$commonLibSourcePayloadRoot -Force | Out-Null
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

    $shippingConfig = Get-Content -LiteralPath (
        Join-Path $payloadRoot "SKSE/Plugins/BoundedEncounters.json") -Raw | ConvertFrom-Json
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
        $shippingAllowedSourcePlugins.Count -ne $expectedAllowedSourcePlugins.Count) {
        throw "The alpha package requires enabled observe-only schema 1 defaults and the reviewed official-master source allowlist."
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

    $vcpkgManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "vcpkg.json") -Raw |
        ConvertFrom-Json
    $vcpkgShareRoot = Join-Path $RepoRoot "build/release/vcpkg_installed/x64-windows-static-md/share"
    $dependencyLicenses = @{
        "directxmath" = "MIT"
        "directxtk" = "MIT"
        "fmt" = "MIT"
        "nlohmann-json" = "MIT"
        "rapidcsv" = "BSD-3-Clause"
        "simpleini" = "MIT"
        "spdlog" = "MIT"
        "xbyak" = "BSD-3-Clause"
    }
    foreach ($dependency in $vcpkgManifest.dependencies) {
        $dependencyName = if ($dependency -is [string]) { $dependency } else { [string]$dependency.name }
        if (-not $dependencyLicenses.ContainsKey($dependencyName)) {
            throw "No reviewed SPDX license mapping exists for vcpkg dependency: $dependencyName"
        }
        $copyrightSource = Join-Path $vcpkgShareRoot "$dependencyName/copyright"
        if (-not (Test-Path -LiteralPath $copyrightSource -PathType Leaf)) {
            throw "Required vcpkg dependency license is missing: $dependencyName/copyright"
        }
        $copyrightDestination = Join-Path $payloadRoot "licenses/vcpkg/$dependencyName/copyright"
        New-Item -ItemType Directory -Path (Split-Path -Parent $copyrightDestination) -Force | Out-Null
        Copy-Item -LiteralPath $copyrightSource -Destination $copyrightDestination
    }

    $commonLibRepositoryRoot = [System.IO.Path]::GetFullPath(
        (Join-Path $RepoRoot "extern/CommonLibSSE-NG"))
    $commonLibTrackedFiles = @(& git -C $commonLibRepositoryRoot ls-files)
    if ($LASTEXITCODE -ne 0 -or $commonLibTrackedFiles.Count -eq 0) {
        throw "Unable to enumerate pinned CommonLibSSE-NG corresponding source."
    }
    $excludedGitlinks = @()
    foreach ($relativePath in ($commonLibTrackedFiles | Sort-Object)) {
        $source = [System.IO.Path]::GetFullPath((Join-Path $commonLibRepositoryRoot $relativePath))
        if (-not $source.StartsWith(
                $commonLibRepositoryRoot + [System.IO.Path]::DirectorySeparatorChar,
                [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Unsafe CommonLibSSE-NG source path: $relativePath"
        }
        if (Test-Path -LiteralPath $source -PathType Container) {
            $excludedGitlinks += $relativePath.Replace('\', '/')
            continue
        }
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Tracked CommonLibSSE-NG source file is missing: $relativePath"
        }
        $destination = Join-Path $commonLibSourcePayloadRoot $relativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }
    foreach ($requiredSourceFile in @("COPYING", "EXCEPTIONS.md", "CMakeLists.txt")) {
        if (-not (Test-Path -LiteralPath (Join-Path $commonLibSourcePayloadRoot $requiredSourceFile) -PathType Leaf)) {
            throw "Corresponding-source payload is incomplete: $requiredSourceFile"
        }
    }

    $sourceProvenance = [ordered]@{
        schemaVersion = 1
        component = "CommonLibSSE-NG"
        repository = "https://github.com/Ensrick/CommonLibSSE-NG"
        branch = "ensrick/no-modal-errors-v7"
        commit = $commonLibCommit
        upstream = [ordered]@{
            repository = "https://github.com/alandtse/CommonLibSSE-NG"
            tag = $commonLibUpstreamTag
            commit = $commonLibParentCommit
        }
        modification = "Opt-in COMMONLIBSSE_NO_MODAL_ERRORS failure path"
        license = "GPL-3.0-or-later"
        exceptionFile = "EXCEPTIONS.md"
        bundledFor = [ordered]@{
            project = "Bounded Encounters"
            version = $Version
            sourceCommit = $commit
        }
        excludedGitlinks = @($excludedGitlinks)
        exclusionReason = "Nested gitlink content is not compiled into the Skyrim AE build and is not copied; Skyrim VR support is disabled."
        sourceDateEpoch = $epoch
    }
    Write-Utf8NoBomLf -Path (Join-Path $commonLibSourcePayloadRoot "SOURCE-PROVENANCE.json") -Content (
        $sourceProvenance | ConvertTo-Json -Depth 8)
    $sourceReadme = @"
# CommonLibSSE-NG corresponding source

This archive accompanies Bounded Encounters $Version. It contains the tracked
source used for the statically linked CommonLibSSE-NG portion of the binary:
Ensrick fork commit $commonLibCommit. The fork commit is based directly on
upstream $commonLibUpstreamTag commit $commonLibParentCommit and adds the
opt-in COMMONLIBSSE_NO_MODAL_ERRORS failure path.

CommonLibSSE-NG is licensed under GPL-3.0-or-later with the Modding Exception in
EXCEPTIONS.md. COPYING and EXCEPTIONS.md are the controlling terms. The original
Bounded Encounters source and build recipe are available at
https://github.com/Ensrick/skyrim-mod-assistant/tree/$commit/mods/bounded-encounters.

SOURCE-PROVENANCE.json identifies any excluded nested gitlink. Gitlink content
is excluded only when it is not compiled into the supported Skyrim AE build;
Skyrim VR support is disabled.
"@
    Write-Utf8NoBomLf -Path (Join-Path $commonLibSourcePayloadRoot "README-CORRESPONDING-SOURCE.md") -Content $sourceReadme

    $sourceManifestFiles = Get-ChildItem -LiteralPath $commonLibSourcePayloadRoot -File -Recurse |
        Where-Object { $_.Name -ne "SOURCE-MANIFEST.sha256" } |
        Sort-Object { Get-RelativeSlashPath -Base $commonLibSourcePayloadRoot -Path $_.FullName }
    $sourceManifestLines = foreach ($file in $sourceManifestFiles) {
        $relativePath = Get-RelativeSlashPath -Base $commonLibSourcePayloadRoot -Path $file.FullName
        "$(Get-FileSha256 -Path $file.FullName)  $relativePath"
    }
    Write-Utf8NoBomLf -Path (Join-Path $commonLibSourcePayloadRoot "SOURCE-MANIFEST.sha256") -Content (
        $sourceManifestLines -join "`n")
    foreach ($line in $sourceManifestLines) {
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') {
            throw "Internal corresponding-source manifest format failure: $line"
        }
        $expectedHash = $Matches[1]
        $relativePath = $Matches[2]
        $actualHash = Get-FileSha256 -Path (Join-Path $commonLibSourcePayloadRoot $relativePath)
        if ($actualHash -ne $expectedHash) {
            throw "Internal corresponding-source manifest verification failed: $relativePath"
        }
    }

    $vcpkgConfiguration = Get-Content -LiteralPath (Join-Path $RepoRoot "vcpkg-configuration.json") -Raw |
        ConvertFrom-Json
    $vcpkgBaseline = [string]$vcpkgConfiguration.'default-registry'.baseline

    $metadata = [ordered]@{
        schemaVersion = 1
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
            vcpkgBaseline = $vcpkgBaseline
        }
        shippingConfiguration = [ordered]@{
            schemaVersion = $shippingConfig.schemaVersion
            enabled = $shippingConfig.enabled
            observeOnly = $shippingConfig.observeOnly
            allowedSourcePlugins = $shippingAllowedSourcePlugins
        }
        releaseEligible = (-not $isDirty)
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
        }
    )
    $relationships += [ordered]@{
        spdxElementId = "SPDXRef-Package-BoundedEncounters"
        relationshipType = "STATIC_LINK"
        relatedSpdxElement = "SPDXRef-Package-CommonLibSSE-NG"
    }

    foreach ($dependency in $vcpkgManifest.dependencies) {
        $dependencyName = if ($dependency -is [string]) { $dependency } else { [string]$dependency.name }
        $dependencyId = "SPDXRef-Package-vcpkg-" + ($dependencyName -replace '[^A-Za-z0-9.-]', '-')
        $dependencyPackages += [ordered]@{
            name = $dependencyName
            SPDXID = $dependencyId
            versionInfo = "vcpkg-baseline-$vcpkgBaseline"
            downloadLocation = "https://github.com/microsoft/vcpkg"
            filesAnalyzed = $false
            licenseConcluded = $dependencyLicenses[$dependencyName]
            licenseDeclared = $dependencyLicenses[$dependencyName]
            copyrightText = "NOASSERTION"
        }
        $relationships += [ordered]@{
            spdxElementId = "SPDXRef-Package-BoundedEncounters"
            relationshipType = "DEPENDS_ON"
            relatedSpdxElement = $dependencyId
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
        licenseConcluded = "MIT"
        licenseDeclared = "MIT"
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
    $dirtySuffix = if ($isDirty) { "-dirty" } else { "" }
    $archiveName = "BoundedEncounters-$Version-Skyrim-$Runtime-win64$dirtySuffix.zip"
    $archivePath = Join-Path $OutputDirectory $archiveName
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    New-DeterministicZip -PayloadRoot $payloadRoot -ArchivePath $archivePath -Timestamp $zipTimestamp

    $archiveHash = Get-FileSha256 -Path $archivePath
    $hashPath = "$archivePath.sha256"
    Write-Utf8NoBomLf -Path $hashPath -Content "$archiveHash  $archiveName"

    $commonLibSourceArchiveName = "BoundedEncounters-$Version-CommonLibSSE-NG-a9d7d452-source$dirtySuffix.zip"
    $commonLibSourceArchivePath = Join-Path $OutputDirectory $commonLibSourceArchiveName
    if (Test-Path -LiteralPath $commonLibSourceArchivePath) {
        Remove-Item -LiteralPath $commonLibSourceArchivePath -Force
    }
    New-DeterministicZip `
        -PayloadRoot $commonLibSourcePayloadRoot `
        -ArchivePath $commonLibSourceArchivePath `
        -Timestamp $zipTimestamp
    $commonLibSourceArchiveHash = Get-FileSha256 -Path $commonLibSourceArchivePath
    $commonLibSourceHashPath = "$commonLibSourceArchivePath.sha256"
    Write-Utf8NoBomLf `
        -Path $commonLibSourceHashPath `
        -Content "$commonLibSourceArchiveHash  $commonLibSourceArchiveName"

    [ordered]@{
        archive = $archivePath
        sha256 = $archiveHash
        hashFile = $hashPath
        correspondingSourceArchive = $commonLibSourceArchivePath
        correspondingSourceSha256 = $commonLibSourceArchiveHash
        correspondingSourceHashFile = $commonLibSourceHashPath
        sourceCommit = $commit
        sourceDateEpoch = $epoch
        releaseEligible = (-not $isDirty)
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
