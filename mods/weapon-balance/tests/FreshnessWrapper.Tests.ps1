#requires -Version 7.0
$ErrorActionPreference = 'Stop'

function Sha([string]$Path) {
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Digest([string[]]$Lines) {
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Lines -join "`n") + "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function InventoryDigest($Inventory) {
    Digest @($Inventory | ForEach-Object {
        "$($_.plugin)|$($_.provider)|$($_.sha256)"
    })
}

function SidecarDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object relativePath | ForEach-Object {
        "$($_.relativePath)|$($_.language)|$($_.source)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
}

function PhysicalResourceDigest($Inventory) {
    $content = ((@($Inventory | Sort-Object provider, kind, relativePath | ForEach-Object {
        "$($_.provider)|$($_.kind)|$($_.relativePath)|$($_.winningProvider)|$($_.bytes)|$($_.sha256)"
    }) -join "`n") + "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($content)))
}

function ResourceContractDigest($Contract) {
    $node = [System.Text.Json.Nodes.JsonNode]::Parse(
        ($Contract | ConvertTo-Json -Depth 20 -Compress))
    [void]$node.AsObject().Remove('sha256')
    $options = [System.Text.Json.JsonSerializerOptions]::new()
    $options.PropertyNamingPolicy = [System.Text.Json.JsonNamingPolicy]::CamelCase
    $options.WriteIndented = $true
    $canonical = $node.ToJsonString($options)
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($canonical)))
}

function SourceFingerprint([string]$Root) {
    $paths = @(
        'generate.ps1', 'audit.ps1', 'package.ps1', 'global.json',
        'README.md', 'DECISIONS.md',
        'src\WeaponBalancePatcher\WeaponBalancePatcher.csproj',
        'src\WeaponBalancePatcher\packages.lock.json',
        'src\WeaponBalancePatcher\settings.json',
        'tests\WeaponBalancePatcher.Tests\WeaponBalancePatcher.Tests.csproj',
        'tests\WeaponBalancePatcher.Tests\packages.lock.json'
    )
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $Root 'src\WeaponBalancePatcher') `
        -Filter '*.cs' -File | ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName) })
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $Root 'tests\WeaponBalancePatcher.Tests') `
        -Filter '*.cs' -File | ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName) })
    $paths += @(Get-ChildItem -LiteralPath (Join-Path $Root 'tests') `
        -Filter '*.ps1' -File | ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName) })
    $files = @($paths | Sort-Object -Unique | ForEach-Object {
        [ordered]@{ path = $_.Replace('\', '/'); sha256 = Sha (Join-Path $Root $_) }
    })
    [ordered]@{
        files = $files
        sha256 = InventoryDigest @($files | ForEach-Object {
            [pscustomobject]@{ plugin = $_.path; provider = 'source'; sha256 = $_.sha256 }
        })
    }
}

function FileSnapshot([string]$Root) {
    @((Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName | ForEach-Object {
        "$([IO.Path]::GetRelativePath($Root, $_.FullName))|$(Sha $_.FullName)"
    })) -join "`n"
}

function Assert-CleanupTarget([string]$Path, [string]$Boundary, [string]$Prefix) {
    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $fullBoundary = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    if (-not $fullPath.StartsWith($fullBoundary + '\', [StringComparison]::OrdinalIgnoreCase) -or
        -not [IO.Path]::GetFileName($fullPath).StartsWith($Prefix, [StringComparison]::Ordinal)) {
        throw "Refusing cleanup outside the exact generated fixture root: $fullPath"
    }
    return $fullPath
}

function Invoke-Audit([string]$AuditPath, [string]$InstancePath, [string]$ArtifactPath) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = (Get-Command pwsh).Source
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in @(
        '-NoProfile', '-File', $AuditPath, '-FreshnessOnly',
        '-Instance', $InstancePath, '-Profile', 'Default', '-ArtifactRoot', $ArtifactPath)) {
        [void]$start.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::Start($start)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    [pscustomobject]@{ ExitCode = $process.ExitCode; Stdout = $stdout; Stderr = $stderr }
}

$moduleRoot = Split-Path -Parent $PSScriptRoot
$audit = Join-Path $moduleRoot 'audit.ps1'
$tempBoundary = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$testRoot = [IO.Path]::GetFullPath((Join-Path $tempBoundary (
    "weapon-balance-freshness-" + [guid]::NewGuid())))
try {
    $instance = Join-Path $testRoot 'instance'
    $profile = Join-Path $instance 'profiles\Default'
    $data = Join-Path $testRoot 'game\Data'
    $artifact = Join-Path $testRoot 'artifacts'
    $installed = Join-Path $instance 'mods\Ensrick - Weapon Speed Balance'
    foreach ($folder in @(
        $profile, $data, $artifact, $installed, (Join-Path $instance 'overwrite'),
        (Join-Path $artifact 'Strings'), (Join-Path $installed 'Strings'))) {
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
    }
    [IO.File]::WriteAllText((Join-Path $instance 'ModOrganizer.ini'),
        'gamePath=' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Split-Path $data))))
    [IO.File]::WriteAllText((Join-Path $profile 'plugins.txt'), "*WeaponBalancePatch.esp`n")
    [IO.File]::WriteAllText((Join-Path $profile 'modlist.txt'), "+Ensrick - Weapon Speed Balance`n")

    $baseNames = @('Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm')
    foreach ($name in $baseNames) {
        [IO.File]::WriteAllBytes((Join-Path $data $name), [Text.Encoding]::UTF8.GetBytes("fixture-$name"))
    }
    $sourceStringsRoot = Join-Path $data 'Strings'
    New-Item -ItemType Directory -Path $sourceStringsRoot | Out-Null
    $sourceString = Join-Path $sourceStringsRoot 'Update_English.STRINGS'
    [IO.File]::WriteAllText($sourceString, 'source-English')
    $outputBytes = [Text.Encoding]::UTF8.GetBytes('fixture-output')
    [IO.File]::WriteAllBytes((Join-Path $artifact 'WeaponBalancePatch.esp'), $outputBytes)
    [IO.File]::WriteAllBytes((Join-Path $installed 'WeaponBalancePatch.esp'), $outputBytes)
    [IO.File]::WriteAllText((Join-Path $artifact 'selection-report.json'), '{}')
    [IO.File]::WriteAllText((Join-Path $artifact 'final-winner-audit.json'), '{"status":"pass"}')
    $sidecars = @(
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_English.DLSTRINGS'; language = 'English'; source = 'DL' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_English.ILSTRINGS'; language = 'English'; source = 'IL' },
        [ordered]@{ relativePath = 'Strings/WeaponBalancePatch_English.STRINGS'; language = 'English'; source = 'Normal' }
    )
    foreach ($sidecar in $sidecars) {
        foreach ($root in @($artifact, $installed)) {
            [IO.File]::WriteAllText((Join-Path $root $sidecar.relativePath), "fixture-$($sidecar.source)")
        }
        $artifactSidecar = Join-Path $artifact $sidecar.relativePath
        $sidecar.bytes = (Get-Item -LiteralPath $artifactSidecar).Length
        $sidecar.sha256 = Sha $artifactSidecar
    }
    $sourceRelative = 'Strings/Update_English.STRINGS'
    $sourceContract = [ordered]@{
        schemaVersion = 1
        providers = @([ordered]@{
            provider = 'Update.esm'
            languages = @('English')
            candidateRelativePaths = @(
                'Strings/Update_English.DLSTRINGS',
                'Strings/Update_English.ILSTRINGS',
                $sourceRelative)
        })
        looseFiles = @([ordered]@{
            provider = 'Update.esm'; relativePath = $sourceRelative
            language = 'English'; source = 'Normal'
            bytes = (Get-Item -LiteralPath $sourceString).Length; sha256 = Sha $sourceString
        })
        archives = @()
        resolutions = @(
            [ordered]@{
                provider = 'Update.esm'; relativePath = 'Strings/Update_English.DLSTRINGS'
                language = 'English'; source = 'DL'; resolution = 'absent'
                selectedContainer = $null; availableContainers = @()
            },
            [ordered]@{
                provider = 'Update.esm'; relativePath = 'Strings/Update_English.ILSTRINGS'
                language = 'English'; source = 'IL'; resolution = 'absent'
                selectedContainer = $null; availableContainers = @()
            },
            [ordered]@{
                provider = 'Update.esm'; relativePath = $sourceRelative
                language = 'English'; source = 'Normal'; resolution = 'loose'
                selectedContainer = "loose:$sourceRelative"
                availableContainers = @("loose:$sourceRelative")
            })
    }
    $sourceContract.sha256 = ResourceContractDigest $sourceContract
    $sourcePhysical = @([ordered]@{
        provider = 'Update.esm'; kind = 'loose'; relativePath = $sourceRelative
        winningProvider = 'game-data'; bytes = (Get-Item -LiteralPath $sourceString).Length
        sha256 = Sha $sourceString
    })

    $inputLines = @($baseNames | ForEach-Object { "*$_" })
    $inventory = @($baseNames | ForEach-Object {
        [ordered]@{ plugin = $_; provider = 'game-data'; sha256 = Sha (Join-Path $data $_) }
    })
    $source = SourceFingerprint $moduleRoot
    $manifest = [ordered]@{
        schemaVersion = 3
        generatorVersion = '0.3.0'
        outputPlugin = 'WeaponBalancePatch.esp'
        inputLoadOrderEntries = $inputLines.Count
        inputLoadOrderSha256 = Digest $inputLines
        inputPluginBinaries = $inventory
        inputPluginBinariesSha256 = InventoryDigest $inventory
        sourceFingerprint = $source
        settingsSha256 = Sha (Join-Path $moduleRoot 'src\WeaponBalancePatcher\settings.json')
        selectionReportSha256 = Sha (Join-Path $artifact 'selection-report.json')
        pluginSha256 = Sha (Join-Path $artifact 'WeaponBalancePatch.esp')
        localized = $true
        translationLanguages = @('English')
        localizedSidecars = $sidecars
        localizedSidecarsSha256 = SidecarDigest $sidecars
        inputTranslationSemantics = [ordered]@{
            schemaVersion = 1
            records = 1
            fields = 2
            values = 1
            languages = @('English')
            providers = @([ordered]@{
                provider = 'Update.esm'; sourceUsesLocalization = $true
                records = 1; fields = 2; values = 1; languages = @('English')
            })
            sha256 = ('B' * 64)
        }
        inputLocalizationResources = $sourceContract
        inputLocalizationResourceProviders = $sourcePhysical
        inputLocalizationResourceProvidersSha256 = PhysicalResourceDigest $sourcePhysical
        finalWinningSpeedGate = 'pass'
        finalWinnerAuditSha256 = Sha (Join-Path $artifact 'final-winner-audit.json')
    }
    [IO.File]::WriteAllText((Join-Path $artifact 'build-manifest.json'),
        ($manifest | ConvertTo-Json -Depth 20))

    $before = FileSnapshot $testRoot
    $result = Invoke-Audit $audit $instance $artifact
    if ($result.ExitCode -ne 0) {
        throw "Freshness fixture failed: $($result.Stdout) $($result.Stderr)"
    }
    $parsed = $result.Stdout | ConvertFrom-Json
    if ($parsed.vfsUsed -ne $false -or $parsed.filesWritten -ne 0) {
        throw 'Freshness result did not declare no-VFS/no-write behavior.'
    }
    $after = FileSnapshot $testRoot
    if ($before -ne $after) { throw 'FreshnessOnly changed a fixture file.' }

    $metadata = Join-Path $artifact 'EnsrickMetadata'
    New-Item -ItemType Directory -Path $metadata | Out-Null
    foreach ($metadataName in @(
        'selection-report.json', 'build-manifest.json', 'final-winner-audit.json')) {
        Move-Item -LiteralPath (Join-Path $artifact $metadataName) `
            -Destination (Join-Path $metadata $metadataName)
    }
    $packagedBefore = FileSnapshot $testRoot
    $packagedResult = Invoke-Audit $audit $instance $artifact
    if ($packagedResult.ExitCode -ne 0) {
        throw "Packaged-layout freshness fixture failed: $($packagedResult.Stdout) $($packagedResult.Stderr)"
    }
    $packagedAfter = FileSnapshot $testRoot
    if ($packagedBefore -ne $packagedAfter) {
        throw 'FreshnessOnly changed a packaged-layout fixture file.'
    }

    [IO.File]::WriteAllText($sourceString, 'changed-source-with-same-plugin')
    $sourceDrift = Invoke-Audit $audit $instance $artifact
    if ($sourceDrift.ExitCode -eq 0 -or
        ($sourceDrift.Stdout + $sourceDrift.Stderr) -notmatch 'input localization resources differ') {
        throw 'Source localization-table drift with unchanged plugin bytes was not rejected.'
    }
    [IO.File]::WriteAllText($sourceString, 'source-English')

    $newLanguage = Join-Path $sourceStringsRoot 'Update_German.STRINGS'
    [IO.File]::WriteAllText($newLanguage, 'source-German')
    $languageDrift = Invoke-Audit $audit $instance $artifact
    if ($languageDrift.ExitCode -eq 0 -or
        ($languageDrift.Stdout + $languageDrift.Stderr) -notmatch 'input localization resources differ') {
        throw 'A newly appearing provider-language table was not rejected.'
    }
    Remove-Item -LiteralPath $newLanguage

    $overwriteSourceStrings = Join-Path $instance 'overwrite\Strings'
    New-Item -ItemType Directory -Path $overwriteSourceStrings | Out-Null
    [IO.File]::WriteAllText((Join-Path $overwriteSourceStrings 'Update_English.STRINGS'), 'source-English')
    $sourceShadow = Invoke-Audit $audit $instance $artifact
    if ($sourceShadow.ExitCode -eq 0 -or
        ($sourceShadow.Stdout + $sourceShadow.Stderr) -notmatch 'input localization resources differ') {
        throw 'Source localization-table provider shadowing was not rejected.'
    }
    Remove-Item -LiteralPath $overwriteSourceStrings -Recurse

    $artifactString = Join-Path $artifact 'Strings\WeaponBalancePatch_English.STRINGS'
    $installedString = Join-Path $installed 'Strings\WeaponBalancePatch_English.STRINGS'
    [IO.File]::WriteAllText($artifactString, 'tampered-artifact')
    $artifactDrift = Invoke-Audit $audit $instance $artifact
    if ($artifactDrift.ExitCode -eq 0 -or
        ($artifactDrift.Stdout + $artifactDrift.Stderr) -notmatch 'localized sidecar artifact differs') {
        throw 'Candidate localized-sidecar byte drift was not rejected.'
    }
    [IO.File]::WriteAllText($artifactString, 'fixture-Normal')

    [IO.File]::WriteAllText($installedString, 'tampered-installed')
    $installedDrift = Invoke-Audit $audit $instance $artifact
    if ($installedDrift.ExitCode -eq 0 -or
        ($installedDrift.Stdout + $installedDrift.Stderr) -notmatch 'installed localized sidecar drift') {
        throw 'Installed localized-sidecar byte drift was not rejected.'
    }
    [IO.File]::WriteAllText($installedString, 'fixture-Normal')

    Remove-Item -LiteralPath $installedString
    $missingSidecar = Invoke-Audit $audit $instance $artifact
    if ($missingSidecar.ExitCode -eq 0 -or
        ($missingSidecar.Stdout + $missingSidecar.Stderr) -notmatch 'installed localized sidecar drift') {
        throw 'A missing installed localized sidecar was not rejected.'
    }
    [IO.File]::WriteAllText($installedString, 'fixture-Normal')

    $overwriteStrings = Join-Path $instance 'overwrite\Strings'
    New-Item -ItemType Directory -Path $overwriteStrings | Out-Null
    [IO.File]::WriteAllText(
        (Join-Path $overwriteStrings 'WeaponBalancePatch_English.STRINGS'), 'fixture-Normal')
    $sidecarShadow = Invoke-Audit $audit $instance $artifact
    if ($sidecarShadow.ExitCode -eq 0 -or
        ($sidecarShadow.Stdout + $sidecarShadow.Stderr) -notmatch 'not mod:Ensrick - Weapon Speed Balance') {
        throw 'Overwrite shadowing of an installed localized sidecar was not rejected.'
    }
    Remove-Item -LiteralPath $overwriteStrings -Recurse

    $extraSidecar = Join-Path $installed 'Strings\WeaponBalancePatch_French.STRINGS'
    [IO.File]::WriteAllText($extraSidecar, 'stale-extra')
    $extra = Invoke-Audit $audit $instance $artifact
    if ($extra.ExitCode -eq 0 -or
        ($extra.Stdout + $extra.Stderr) -notmatch 'installed localized sidecar drift') {
        throw 'An extra matching installed localized sidecar was not rejected.'
    }
    Remove-Item -LiteralPath $extraSidecar

    [IO.File]::WriteAllText((Join-Path $data 'Update.esm'), 'changed-input')
    $stale = Invoke-Audit $audit $instance $artifact
    if ($stale.ExitCode -eq 0 -or ($stale.Stdout + $stale.Stderr) -notmatch 'input plugin') {
        throw 'Same-name input binary drift was not rejected.'
    }

    [IO.File]::WriteAllBytes((Join-Path $data 'Update.esm'),
        [Text.Encoding]::UTF8.GetBytes('fixture-Update.esm'))
    [IO.File]::WriteAllText((Join-Path $instance 'overwrite\WeaponBalancePatch.esp'), 'shadow')
    $shadow = Invoke-Audit $audit $instance $artifact
    if ($shadow.ExitCode -eq 0 -or ($shadow.Stdout + $shadow.Stderr) -notmatch 'actual output file winner') {
        throw 'Overwrite shadowing of the installed output was not rejected.'
    }

    Remove-Item -LiteralPath (Join-Path $instance 'overwrite\WeaponBalancePatch.esp')
    Remove-Item -LiteralPath $sourceString
    $metadataManifest = Join-Path $metadata 'build-manifest.json'
    $zeroCandidateContract = [ordered]@{
        schemaVersion = 1
        providers = @([ordered]@{
            provider = 'Update.esm'; languages = @(); candidateRelativePaths = @()
        })
        looseFiles = @(); archives = @(); resolutions = @()
    }
    $zeroCandidateContract.sha256 = ResourceContractDigest $zeroCandidateContract
    $manifest.inputTranslationSemantics = [ordered]@{
        schemaVersion = 1; records = 1; fields = 2; values = 0
        languages = @(); providers = @([ordered]@{
            provider = 'Update.esm'; sourceUsesLocalization = $true
            records = 1; fields = 2; values = 0; languages = @()
        }); sha256 = ('C' * 64)
    }
    $manifest.inputLocalizationResources = $zeroCandidateContract
    $manifest.inputLocalizationResourceProviders = @()
    $manifest.inputLocalizationResourceProvidersSha256 = PhysicalResourceDigest @()
    [IO.File]::WriteAllText($metadataManifest, ($manifest | ConvertTo-Json -Depth 20))
    $zeroCandidates = Invoke-Audit $audit $instance $artifact
    if ($zeroCandidates.ExitCode -ne 0) {
        throw "A valid zero-candidate localized provider was rejected: $($zeroCandidates.Stdout) $($zeroCandidates.Stderr)"
    }

    $emptyContract = [ordered]@{
        schemaVersion = 1; providers = @(); looseFiles = @(); archives = @(); resolutions = @()
    }
    $emptyContract.sha256 = ResourceContractDigest $emptyContract
    $manifest.inputTranslationSemantics = [ordered]@{
        schemaVersion = 1; records = 0; fields = 0; values = 0
        languages = @(); providers = @(); sha256 = ('D' * 64)
    }
    $manifest.inputLocalizationResources = $emptyContract
    $manifest.inputLocalizationResourceProviders = @()
    $manifest.inputLocalizationResourceProvidersSha256 = PhysicalResourceDigest @()
    [IO.File]::WriteAllText($metadataManifest, ($manifest | ConvertTo-Json -Depth 20))
    $emptyResources = Invoke-Audit $audit $instance $artifact
    if ($emptyResources.ExitCode -ne 0) {
        throw "A valid empty localization-resource contract was rejected: $($emptyResources.Stdout) $($emptyResources.Stderr)"
    }

    Write-Host 'PASS: FreshnessOnly is no-VFS/no-write and rejects input, plugin, and localized-sidecar drift.'
} finally {
    if (Test-Path -LiteralPath $testRoot) {
        $cleanupRoot = Assert-CleanupTarget $testRoot $tempBoundary 'weapon-balance-freshness-'
        Remove-Item -LiteralPath $cleanupRoot -Recurse -Force
    }
}
