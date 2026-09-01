Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Utf8StringSha256 {
    param([Parameter(Mandatory = $true)][string]$Value)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return [System.Convert]::ToHexString($algorithm.ComputeHash($bytes)).ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
    }
}

function ConvertTo-NormalizedText {
    param([Parameter(Mandatory = $true)][string]$Value)

    $normalized = $Value.Replace("`r`n", "`n").Replace("`r", "`n")
    if (-not $normalized.EndsWith("`n", [System.StringComparison]::Ordinal)) {
        $normalized += "`n"
    }
    return $normalized
}

function Set-NoteProperty {
    param(
        [Parameter(Mandatory = $true)][psobject]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)]$Value
    )

    $existing = $Object.PSObject.Properties[$Name]
    if ($null -eq $existing) {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    } else {
        $existing.Value = $Value
    }
}

function Sort-StringsOrdinal {
    param([AllowEmptyCollection()][string[]]$Values)

    [string[]]$copy = @($Values)
    [System.Array]::Sort[string]($copy, [System.StringComparer]::Ordinal)
    return ,$copy
}

function Sort-ObjectsByOrdinalKey {
    param(
        [AllowEmptyCollection()][object[]]$Values,
        [Parameter(Mandatory = $true)][scriptblock]$KeySelector
    )

    $decorated = [System.Collections.Generic.List[object]]::new()
    $ordinal = 0
    foreach ($value in @($Values)) {
        $decorated.Add([pscustomobject]@{
                key = [string](& $KeySelector $value)
                ordinal = $ordinal
                value = $value
            })
        ++$ordinal
    }
    $comparison = [System.Comparison[object]]{
        param($left, $right)
        $result = [System.StringComparer]::Ordinal.Compare([string]$left.key, [string]$right.key)
        if ($result -ne 0) {
            return $result
        }
        return [int]$left.ordinal - [int]$right.ordinal
    }
    $decorated.Sort($comparison)
    return ,@($decorated | ForEach-Object { $_.value })
}

function Write-NormalizedVcpkgSpdx {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][string]$PackageName,
        [Parameter(Mandatory = $true)][string]$Triplet,
        [Parameter(Mandatory = $true)][string]$Abi,
        [Parameter(Mandatory = $true)][string]$VcpkgBaseline,
        [Parameter(Mandatory = $true)][System.DateTimeOffset]$SourceTimestamp
    )

    foreach ($identifier in @(
            [ordered]@{ name = "PackageName"; value = $PackageName; pattern = '^[a-z0-9][a-z0-9-]*$' },
            [ordered]@{ name = "Triplet"; value = $Triplet; pattern = '^[A-Za-z0-9][A-Za-z0-9-]*$' },
            [ordered]@{ name = "Abi"; value = $Abi; pattern = '^[0-9a-f]{64}$' },
            [ordered]@{ name = "VcpkgBaseline"; value = $VcpkgBaseline; pattern = '^[0-9a-f]{40}$' })) {
        if ([string]$identifier.value -cnotmatch [string]$identifier.pattern) {
            throw "Unsafe or malformed $($identifier.name) for SPDX normalization: $($identifier.value)"
        }
    }
    if (-not (Test-Path -LiteralPath $InputPath -PathType Leaf)) {
        throw "Installed vcpkg SPDX input is missing: $InputPath"
    }

    $document = Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
    $declaredSchema = if ($null -eq $document.PSObject.Properties['$schema']) {
        ""
    } else {
        [string]$document.'$schema'
    }
    if ($declaredSchema -cne "https://raw.githubusercontent.com/spdx/spdx-spec/v2.2.1/schemas/spdx-schema.json" -or
        [string]$document.spdxVersion -cne "SPDX-2.2" -or
        [string]$document.dataLicense -cne "CC0-1.0" -or
        [string]$document.SPDXID -cne "SPDXRef-DOCUMENT") {
        throw "Installed vcpkg SPDX document has an unsupported identity: $InputPath"
    }
    # vcpkg's generator adds a JSON-Schema convenience property that is not a
    # member of the SPDX 2.2 JSON model itself. Validate the reviewed value
    # above, then omit it from the schema-valid deterministic projection.
    $document.PSObject.Properties.Remove('$schema')
    $rawNamespace = [string]$document.documentNamespace
    $parsedNamespace = $null
    if (-not [System.Uri]::TryCreate($rawNamespace, [System.UriKind]::Absolute, [ref]$parsedNamespace)) {
        throw "Installed vcpkg SPDX document namespace is not an absolute URI: $InputPath"
    }
    $rawCreated = [string]$document.creationInfo.created
    $parsedCreated = [System.DateTimeOffset]::MinValue
    if (-not [System.DateTimeOffset]::TryParse(
            $rawCreated,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::AssumeUniversal,
            [ref]$parsedCreated)) {
        throw "Installed vcpkg SPDX creation time is invalid: $InputPath"
    }

    $binaryPackages = @($document.packages | Where-Object {
            [string]$_.SPDXID -ceq "SPDXRef-binary"
        })
    if ($binaryPackages.Count -ne 1) {
        throw "Installed vcpkg SPDX document must contain exactly one binary package: $InputPath"
    }
    $binaryPackage = $binaryPackages[0]
    if ([string]$binaryPackage.name -cne "${PackageName}:${Triplet}" -or
        [string]$binaryPackage.versionInfo -cne $Abi) {
        throw "Installed vcpkg SPDX binary package does not match the reviewed package identity: $InputPath"
    }
    if ($null -ne $binaryPackage.PSObject.Properties["packageVerificationCode"] -or
        $null -ne $binaryPackage.PSObject.Properties["licenseInfoFromFiles"]) {
        throw "Installed vcpkg SPDX binary package acquired unsupported file-analysis summaries: $InputPath"
    }

    $allFileIds = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal)
    $binaryFileIds = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal)
    foreach ($file in @($document.files)) {
        $fileId = [string]$file.SPDXID
        if ([string]::IsNullOrWhiteSpace($fileId) -or -not $allFileIds.Add($fileId)) {
            throw "Installed vcpkg SPDX document contains a missing or duplicate file SPDXID: $InputPath"
        }
        if ($fileId -match '^SPDXRef-binary-file-[0-9]+$') {
            $sha256Checksums = @($file.checksums | Where-Object {
                    [string]$_.algorithm -ceq "SHA256" -and
                    [string]$_.checksumValue -cmatch '^[0-9a-f]{64}$'
                })
            if ($sha256Checksums.Count -ne 1) {
                throw "Installed binary file lacks one valid SHA-256 checksum in vcpkg SPDX: $fileId"
            }
            $null = $binaryFileIds.Add($fileId)
        } elseif ($fileId.StartsWith("SPDXRef-binary-file-", [System.StringComparison]::Ordinal)) {
            throw "Installed vcpkg SPDX document contains an unexpected binary-file identifier: $fileId"
        }
    }
    if ($binaryFileIds.Count -eq 0) {
        throw "Installed vcpkg SPDX document contains no binary-package files to normalize: $InputPath"
    }

    $binaryContainmentCounts = @{}
    foreach ($fileId in $binaryFileIds) {
        $binaryContainmentCounts[$fileId] = 0
    }
    foreach ($relationship in @($document.relationships)) {
        $sourceId = [string]$relationship.spdxElementId
        $targetId = [string]$relationship.relatedSpdxElement
        $sourceClaimsBinaryFile = $sourceId.StartsWith(
            "SPDXRef-binary-file-",
            [System.StringComparison]::Ordinal)
        $targetClaimsBinaryFile = $targetId.StartsWith(
            "SPDXRef-binary-file-",
            [System.StringComparison]::Ordinal)
        if (($sourceClaimsBinaryFile -and -not $binaryFileIds.Contains($sourceId)) -or
            ($targetClaimsBinaryFile -and -not $binaryFileIds.Contains($targetId))) {
            throw "Installed vcpkg SPDX relationship references an unknown binary-file identifier: $InputPath"
        }
        $referencesRemovedFile = $binaryFileIds.Contains($sourceId) -or $binaryFileIds.Contains($targetId)
        if (-not $referencesRemovedFile) {
            continue
        }
        if ($sourceId -cne "SPDXRef-binary" -or
            [string]$relationship.relationshipType -cne "CONTAINS" -or
            -not $binaryFileIds.Contains($targetId)) {
            throw "Installed vcpkg SPDX binary file participates in an unsupported relationship: $InputPath"
        }
        $binaryContainmentCounts[$targetId] = [int]$binaryContainmentCounts[$targetId] + 1
    }
    foreach ($fileId in $binaryFileIds) {
        if ([int]$binaryContainmentCounts[$fileId] -ne 1) {
            throw "Installed vcpkg SPDX binary file does not have exactly one package containment: $fileId"
        }
    }

    $document.files = @($document.files | Where-Object {
            -not $binaryFileIds.Contains([string]$_.SPDXID)
        })
    $document.relationships = @($document.relationships | Where-Object {
            -not $binaryFileIds.Contains([string]$_.spdxElementId) -and
            -not $binaryFileIds.Contains([string]$_.relatedSpdxElement)
        })

    $normalizationNotice =
        "Deterministic audit derivative generated by Bounded Encounters packaging. " +
        "The vcpkg UUID and wall-clock creation time were normalized with SOURCE_DATE_EPOCH. " +
        "Per-run installed binary-file entries were omitted; the exact ABI and installed file-name inventory are retained separately."
    $existingCreationComment = if ($null -eq $document.creationInfo.PSObject.Properties["comment"]) {
        ""
    } else {
        [string]$document.creationInfo.comment
    }
    $creationComment = if ([string]::IsNullOrWhiteSpace($existingCreationComment)) {
        $normalizationNotice
    } else {
        $existingCreationComment.TrimEnd() + "`n" + $normalizationNotice
    }
    Set-NoteProperty -Object $document.creationInfo -Name "comment" -Value $creationComment

    $existingBinaryComment = if ($null -eq $binaryPackage.PSObject.Properties["comment"]) {
        ""
    } else {
        [string]$binaryPackage.comment
    }
    $binaryComment = if ([string]::IsNullOrWhiteSpace($existingBinaryComment)) {
        $normalizationNotice
    } else {
        $existingBinaryComment.TrimEnd() + "`n" + $normalizationNotice
    }
    Set-NoteProperty -Object $binaryPackage -Name "comment" -Value $binaryComment
    Set-NoteProperty -Object $binaryPackage -Name "filesAnalyzed" -Value $false
    Set-NoteProperty -Object $binaryPackage -Name "licenseConcluded" -Value "NOASSERTION"

    if ($null -ne $document.creationInfo.PSObject.Properties["creators"]) {
        $document.creationInfo.creators = Sort-StringsOrdinal -Values @($document.creationInfo.creators)
    }
    foreach ($package in @($document.packages)) {
        if ($null -ne $package.PSObject.Properties["checksums"]) {
            $package.checksums = Sort-ObjectsByOrdinalKey -Values @($package.checksums) -KeySelector {
                param($checksum)
                "{0}`0{1}" -f [string]$checksum.algorithm, [string]$checksum.checksumValue
            }
        }
        if ($null -ne $package.PSObject.Properties["externalRefs"]) {
            $package.externalRefs = Sort-ObjectsByOrdinalKey -Values @($package.externalRefs) -KeySelector {
                param($reference)
                "{0}`0{1}`0{2}" -f [string]$reference.referenceCategory,
                    [string]$reference.referenceType,
                    [string]$reference.referenceLocator
            }
        }
    }
    foreach ($file in @($document.files)) {
        if ($null -ne $file.PSObject.Properties["checksums"]) {
            $file.checksums = Sort-ObjectsByOrdinalKey -Values @($file.checksums) -KeySelector {
                param($checksum)
                "{0}`0{1}" -f [string]$checksum.algorithm, [string]$checksum.checksumValue
            }
        }
    }
    $document.packages = Sort-ObjectsByOrdinalKey -Values @($document.packages) -KeySelector {
        param($package)
        [string]$package.SPDXID
    }
    $document.files = Sort-ObjectsByOrdinalKey -Values @($document.files) -KeySelector {
        param($file)
        [string]$file.SPDXID
    }
    $document.relationships = Sort-ObjectsByOrdinalKey -Values @($document.relationships) -KeySelector {
        param($relationship)
        "{0}`0{1}`0{2}" -f [string]$relationship.spdxElementId,
            [string]$relationship.relationshipType,
            [string]$relationship.relatedSpdxElement
    }

    $document.creationInfo.created = $SourceTimestamp.ToUniversalTime().ToString(
        "yyyy-MM-dd'T'HH:mm:ss'Z'",
        [System.Globalization.CultureInfo]::InvariantCulture)
    $document.documentNamespace = "urn:spdx:bounded-encounters:normalization-seed"
    $namespaceSeed = ConvertTo-NormalizedText -Value ($document | ConvertTo-Json -Depth 100)
    $namespaceDigest = Get-Utf8StringSha256 -Value $namespaceSeed
    $document.documentNamespace =
        "https://github.com/Ensrick/skyrim-mod-assistant/spdx/vcpkg/" +
        "$VcpkgBaseline/$PackageName/$Triplet/$Abi/$namespaceDigest"

    $outputContent = ConvertTo-NormalizedText -Value ($document | ConvertTo-Json -Depth 100)
    $outputParent = Split-Path -Parent $OutputPath
    if ([string]::IsNullOrWhiteSpace($outputParent) -or
        -not (Test-Path -LiteralPath $outputParent -PathType Container)) {
        throw "Normalized SPDX output parent is missing: $OutputPath"
    }
    [System.IO.File]::WriteAllText(
        $OutputPath,
        $outputContent,
        [System.Text.UTF8Encoding]::new($false))

    return [pscustomobject]@{
        schemaVersion = 1
        outputPath = [System.IO.Path]::GetFullPath($OutputPath)
        documentNamespace = [string]$document.documentNamespace
        sourceDateEpoch = $SourceTimestamp.ToUnixTimeSeconds()
        omittedBinaryFileCount = $binaryFileIds.Count
        retainedFileCount = @($document.files).Count
        sha256 = (Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

Export-ModuleMember -Function Write-NormalizedVcpkgSpdx
