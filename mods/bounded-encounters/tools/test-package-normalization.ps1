#Requires -Version 7.4

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Import-Module (Join-Path $PSScriptRoot "VcpkgSpdxNormalization.psm1") -Force

$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$workRoot = Join-Path $temporaryBase ("BoundedEncounters-normalization-test-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workRoot | Out-Null
try {
    function New-Fixture {
        param(
            [Parameter(Mandatory = $true)][string]$Namespace,
            [Parameter(Mandatory = $true)][string]$Created,
            [Parameter(Mandatory = $true)][string]$BinaryHash
        )

        return [ordered]@{
            '$schema' = "https://raw.githubusercontent.com/spdx/spdx-spec/v2.2.1/schemas/spdx-schema.json"
            spdxVersion = "SPDX-2.2"
            dataLicense = "CC0-1.0"
            SPDXID = "SPDXRef-DOCUMENT"
            documentNamespace = $Namespace
            name = "fixture"
            creationInfo = [ordered]@{
                creators = @("Tool: vcpkg-test")
                created = $Created
            }
            relationships = @(
                [ordered]@{
                    spdxElementId = "SPDXRef-port"
                    relationshipType = "GENERATES"
                    relatedSpdxElement = "SPDXRef-binary"
                },
                [ordered]@{
                    spdxElementId = "SPDXRef-port"
                    relationshipType = "CONTAINS"
                    relatedSpdxElement = "SPDXRef-port-file-0"
                },
                [ordered]@{
                    spdxElementId = "SPDXRef-binary"
                    relationshipType = "CONTAINS"
                    relatedSpdxElement = "SPDXRef-binary-file-0"
                })
            packages = @(
                [ordered]@{
                    name = "fixture"
                    SPDXID = "SPDXRef-port"
                    versionInfo = "1.0.0"
                    downloadLocation = "git+https://github.com/microsoft/vcpkg@1111111111111111111111111111111111111111"
                    licenseConcluded = "MIT"
                    licenseDeclared = "MIT"
                    copyrightText = "NOASSERTION"
                },
                [ordered]@{
                    name = "fixture:x64-windows-static-md"
                    SPDXID = "SPDXRef-binary"
                    versionInfo = ("a" * 64)
                    downloadLocation = "NOASSERTION"
                    licenseConcluded = "MIT"
                    licenseDeclared = "MIT"
                    copyrightText = "NOASSERTION"
                    comment = "Original stable comment."
                })
            files = @(
                [ordered]@{
                    fileName = "./portfile.cmake"
                    SPDXID = "SPDXRef-port-file-0"
                    checksums = @([ordered]@{ algorithm = "SHA256"; checksumValue = ("b" * 64) })
                    licenseConcluded = "NOASSERTION"
                    copyrightText = "NOASSERTION"
                },
                [ordered]@{
                    fileName = "./lib/fixture.lib"
                    SPDXID = "SPDXRef-binary-file-0"
                    checksums = @([ordered]@{ algorithm = "SHA256"; checksumValue = $BinaryHash })
                    licenseConcluded = "NOASSERTION"
                    copyrightText = "NOASSERTION"
                })
        }
    }

    function Write-Fixture {
        param(
            [Parameter(Mandatory = $true)]$Fixture,
            [Parameter(Mandatory = $true)][string]$Path
        )
        $content = ($Fixture | ConvertTo-Json -Depth 20).Replace("`r`n", "`n").Replace("`r", "`n") + "`n"
        [System.IO.File]::WriteAllText($Path, $content, [System.Text.UTF8Encoding]::new($false))
    }

    $inputA = Join-Path $workRoot "a.json"
    $inputB = Join-Path $workRoot "b.json"
    $outputA = Join-Path $workRoot "a.normalized.json"
    $outputB = Join-Path $workRoot "b.normalized.json"
    Write-Fixture -Path $inputA -Fixture (New-Fixture `
            -Namespace "https://spdx.org/spdxdocs/fixture-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" `
            -Created "2026-01-01T00:00:00Z" `
            -BinaryHash ("c" * 64))
    Write-Fixture -Path $inputB -Fixture (New-Fixture `
            -Namespace "https://spdx.org/spdxdocs/fixture-bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" `
            -Created "2099-12-31T23:59:59Z" `
            -BinaryHash ("d" * 64))

    $timestamp = [System.DateTimeOffset]::FromUnixTimeSeconds(1700000000)
    $commonArguments = @{
        PackageName = "fixture"
        Triplet = "x64-windows-static-md"
        Abi = ("a" * 64)
        VcpkgBaseline = ("1" * 40)
        SourceTimestamp = $timestamp
    }
    $resultA = Write-NormalizedVcpkgSpdx @commonArguments -InputPath $inputA -OutputPath $outputA
    $resultB = Write-NormalizedVcpkgSpdx @commonArguments -InputPath $inputB -OutputPath $outputB
    $outputABytes = [System.IO.File]::ReadAllBytes($outputA)
    $outputBBytes = [System.IO.File]::ReadAllBytes($outputB)
    if ($resultA.sha256 -cne $resultB.sha256 -or
        -not [System.Collections.StructuralComparisons]::StructuralEqualityComparer.Equals(
            $outputABytes,
            $outputBBytes)) {
        throw "Volatile vcpkg SPDX inputs did not normalize to byte-identical output."
    }

    $normalized = Get-Content -LiteralPath $outputA -Raw | ConvertFrom-Json
    $binaryPackage = @($normalized.packages | Where-Object SPDXID -ceq "SPDXRef-binary")
    $policyEvidence = [ordered]@{
        binaryPackageCount = $binaryPackage.Count
        filesAnalyzed = if ($binaryPackage.Count -eq 1) { $binaryPackage[0].filesAnalyzed } else { $null }
        binaryFileCount = @($normalized.files | Where-Object SPDXID -like "SPDXRef-binary-file-*").Count
        retainedPortFileCount = @($normalized.files | Where-Object SPDXID -ceq "SPDXRef-port-file-0").Count
        danglingBinaryRelationshipCount = @($normalized.relationships | Where-Object relatedSpdxElement -like "SPDXRef-binary-file-*").Count
        created = if ($normalized.creationInfo.created -is [System.DateTime]) {
            $normalized.creationInfo.created.ToUniversalTime().ToString(
                "yyyy-MM-dd'T'HH:mm:ss'Z'",
                [System.Globalization.CultureInfo]::InvariantCulture)
        } else {
            [string]$normalized.creationInfo.created
        }
        documentNamespace = [string]$normalized.documentNamespace
    }
    if ($policyEvidence.binaryPackageCount -ne 1 -or $policyEvidence.filesAnalyzed -ne $false -or
        [string]$binaryPackage[0].licenseConcluded -cne "NOASSERTION" -or
        $policyEvidence.binaryFileCount -ne 0 -or $policyEvidence.retainedPortFileCount -ne 1 -or
        $policyEvidence.danglingBinaryRelationshipCount -ne 0 -or
        $policyEvidence.created -cne "2023-11-14T22:13:20Z" -or
        $policyEvidence.documentNamespace -cnotmatch '^https://github\.com/Ensrick/skyrim-mod-assistant/spdx/vcpkg/') {
        throw "Normalized vcpkg SPDX output does not satisfy the reviewed policy: $($policyEvidence | ConvertTo-Json -Compress)"
    }

    $semanticInput = Join-Path $workRoot "semantic-change.json"
    $semanticOutput = Join-Path $workRoot "semantic-change.normalized.json"
    $semanticFixture = New-Fixture `
        -Namespace "https://spdx.org/spdxdocs/fixture-semantic" `
        -Created "2026-01-01T00:00:00Z" `
        -BinaryHash ("f" * 64)
    $semanticFixture.files[0].checksums[0].checksumValue = ("0" * 64)
    Write-Fixture -Path $semanticInput -Fixture $semanticFixture
    $semanticResult = Write-NormalizedVcpkgSpdx `
        @commonArguments `
        -InputPath $semanticInput `
        -OutputPath $semanticOutput
    if ($semanticResult.sha256 -ceq $resultA.sha256) {
        throw "A retained port/source checksum change disappeared during SPDX normalization."
    }

    $wrongAbiInput = Join-Path $workRoot "wrong-abi.json"
    $wrongAbiOutput = Join-Path $workRoot "wrong-abi.normalized.json"
    $wrongAbiFixture = New-Fixture `
        -Namespace "https://spdx.org/spdxdocs/fixture-wrong-abi" `
        -Created "2026-01-01T00:00:00Z" `
        -BinaryHash ("1" * 64)
    $wrongAbiFixture.packages[1].versionInfo = ("2" * 64)
    Write-Fixture -Path $wrongAbiInput -Fixture $wrongAbiFixture
    $wrongAbiRejected = $false
    try {
        $null = Write-NormalizedVcpkgSpdx `
            @commonArguments `
            -InputPath $wrongAbiInput `
            -OutputPath $wrongAbiOutput
    } catch {
        $wrongAbiRejected = $true
    }
    if (-not $wrongAbiRejected -or (Test-Path -LiteralPath $wrongAbiOutput)) {
        throw "A mismatched installed ABI was not rejected by SPDX normalization."
    }

    $invalidInput = Join-Path $workRoot "invalid.json"
    $invalidOutput = Join-Path $workRoot "invalid.normalized.json"
    $invalidFixture = New-Fixture `
        -Namespace "https://spdx.org/spdxdocs/fixture-invalid" `
        -Created "2026-01-01T00:00:00Z" `
        -BinaryHash ("e" * 64)
    $invalidFixture.relationships += [ordered]@{
        spdxElementId = "SPDXRef-binary-file-0"
        relationshipType = "GENERATED_FROM"
        relatedSpdxElement = "SPDXRef-port"
    }
    Write-Fixture -Path $invalidInput -Fixture $invalidFixture
    $rejected = $false
    try {
        $null = Write-NormalizedVcpkgSpdx @commonArguments -InputPath $invalidInput -OutputPath $invalidOutput
    } catch {
        $rejected = $true
    }
    if (-not $rejected -or (Test-Path -LiteralPath $invalidOutput)) {
        throw "Unsafe binary-file SPDX relationships were not rejected fail-closed."
    }

    $danglingInput = Join-Path $workRoot "dangling.json"
    $danglingOutput = Join-Path $workRoot "dangling.normalized.json"
    $danglingFixture = New-Fixture `
        -Namespace "https://spdx.org/spdxdocs/fixture-dangling" `
        -Created "2026-01-01T00:00:00Z" `
        -BinaryHash ("9" * 64)
    $danglingFixture.relationships += [ordered]@{
        spdxElementId = "SPDXRef-binary"
        relationshipType = "CONTAINS"
        relatedSpdxElement = "SPDXRef-binary-file-999"
    }
    Write-Fixture -Path $danglingInput -Fixture $danglingFixture
    $danglingRejected = $false
    try {
        $null = Write-NormalizedVcpkgSpdx `
            @commonArguments `
            -InputPath $danglingInput `
            -OutputPath $danglingOutput
    } catch {
        $danglingRejected = $true
    }
    if (-not $danglingRejected -or (Test-Path -LiteralPath $danglingOutput)) {
        throw "Dangling binary-file SPDX relationships were not rejected fail-closed."
    }

    [ordered]@{
        assertions = 19
        normalizedSha256 = $resultA.sha256
        semanticChangeSha256 = $semanticResult.sha256
        omittedBinaryFiles = $resultA.omittedBinaryFileCount
        retainedFiles = $resultA.retainedFileCount
        wrongAbiGate = "passed"
        negativeRelationshipGate = "passed"
        danglingRelationshipGate = "passed"
    } | ConvertTo-Json -Depth 4
} finally {
    $resolvedWorkRoot = [System.IO.Path]::GetFullPath($workRoot)
    if ($resolvedWorkRoot.StartsWith($temporaryBase, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedWorkRoot).StartsWith(
            "BoundedEncounters-normalization-test-",
            [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedWorkRoot -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        throw "Refusing to remove unexpected normalization-test directory: $resolvedWorkRoot"
    }
}
