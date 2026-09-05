#requires -Version 7.0
[CmdletBinding()]
param(
    [string] $PolicyPath = (Join-Path $PSScriptRoot 'private-curation-policy.json'),
    [string] $ProposalPath = (Join-Path $PSScriptRoot 'curation-proposal.json'),
    [string] $OutputRoot = (Join-Path $PSScriptRoot '..\..\work\lost-longswords\private-curation'),
    [string] $Spriggit = (Join-Path $PSScriptRoot '..\..\..\skyrim-tools-builds\Spriggit-0.41.0-cli-secure\Spriggit.CLI.exe'),
    [string] $RecordTool = (Join-Path $PSScriptRoot '..\..\..\skyrim-tools-builds\skyrim-record-cli-bb9aafb\skyrim-record-cli.exe'),
    [string] $SkyrimMaster = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\Skyrim.esm',
    [switch] $Clean
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Utf8NoBom {
    param([Parameter(Mandatory)][string] $Path, [Parameter(Mandatory)][AllowEmptyString()][string] $Text)
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Invoke-Checked {
    param([Parameter(Mandatory)][string] $Tool, [Parameter(Mandatory)][string[]] $Arguments)
    & $Tool @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Tool $($Arguments -join ' ')"
    }
}

function Convert-FormKeyToSkyPatcher {
    param([Parameter(Mandatory)][string] $FormKey)
    $separator = $FormKey.IndexOf(':')
    if ($separator -lt 1 -or $separator -eq ($FormKey.Length - 1)) {
        throw "Invalid FormKey: $FormKey"
    }
    $id = $FormKey.Substring(0, $separator)
    $plugin = $FormKey.Substring($separator + 1)
    if ($id -notmatch '^[0-9A-Fa-f]{1,8}$') { throw "Invalid FormID in FormKey: $FormKey" }
    return "$plugin|$($id.ToUpperInvariant())"
}

function Get-TreeFingerprint {
    param([Parameter(Mandatory)][string] $Root)
    $rows = foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName) {
        [pscustomobject]@{
            path = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\', '/')
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        }
    }
    return @($rows)
}

function Assert-OwnedPath {
    param(
        [Parameter(Mandatory)][string] $Path,
        [Parameter(Mandatory)][string] $OwnerRoot,
        [switch] $AllowOwnerRoot
    )
    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $fullOwner = [IO.Path]::GetFullPath($OwnerRoot).TrimEnd('\')
    if ($fullPath -eq $fullOwner) {
        if (-not $AllowOwnerRoot) { throw "Refusing an operation against the owned root itself: $fullPath" }
        return
    }
    if (-not $fullPath.StartsWith("$fullOwner\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes its exact owned root: $fullPath (root $fullOwner)"
    }
}

function Assert-NoReparseTraversal {
    param(
        [Parameter(Mandatory)][string] $Path,
        [Parameter(Mandatory)][string] $Boundary
    )
    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $fullBoundary = [IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    Assert-OwnedPath -Path $fullPath -OwnerRoot $fullBoundary -AllowOwnerRoot
    $cursor = $fullPath
    while (-not (Test-Path -LiteralPath $cursor)) {
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) { throw "Could not find an existing ancestor for $fullPath" }
        $cursor = $parent
    }
    while ($true) {
        $item = Get-Item -LiteralPath $cursor -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing a path with a reparse-point traversal: $cursor"
        }
        if ($cursor -eq $fullBoundary) { break }
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            throw "Path traversal did not reach its exact boundary: $fullPath (boundary $fullBoundary)"
        }
        $cursor = [IO.Path]::GetFullPath($parent).TrimEnd('\')
    }
}

function Invoke-RecordJsonLines {
    param(
        [Parameter(Mandatory)][string] $Tool,
        [Parameter(Mandatory)][string] $Command,
        [Parameter(Mandatory)][string] $Plugin,
        [string[]] $ExtraArguments = @()
    )
    $arguments = @($Command, $Plugin) + @($ExtraArguments)
    $lines = @(& $Tool @arguments)
    if ($LASTEXITCODE -ne 0) { throw "Record CLI command failed: $Command $Plugin" }
    foreach ($line in $lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) { $line | ConvertFrom-Json -Depth 100 }
    }
}

function Invoke-RecordJsonDocument {
    param(
        [Parameter(Mandatory)][string] $Tool,
        [Parameter(Mandatory)][string] $Command,
        [Parameter(Mandatory)][string] $Plugin,
        [string[]] $ExtraArguments = @()
    )
    $arguments = @($Command, $Plugin) + @($ExtraArguments)
    $text = (& $Tool @arguments) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Record CLI command failed: $Command $Plugin" }
    return $text | ConvertFrom-Json -Depth 100
}

function Assert-ObjectPropertiesEqual {
    param(
        [Parameter(Mandatory)] $Expected,
        [Parameter(Mandatory)] $Actual,
        [string[]] $Ignore = @(),
        [Parameter(Mandatory)][string] $Context
    )
    $ignored = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $Ignore) { [void]$ignored.Add($name) }
    $expectedProperties = @($Expected.PSObject.Properties | Where-Object { -not $ignored.Contains($_.Name) })
    $actualNames = @($Actual.PSObject.Properties | Where-Object { -not $ignored.Contains($_.Name) } | ForEach-Object Name | Sort-Object)
    if ((@($expectedProperties.Name | Sort-Object) -join '|') -ne ($actualNames -join '|')) {
        throw "$Context property set differs."
    }
    foreach ($property in $expectedProperties) {
        $expectedJson = $property.Value | ConvertTo-Json -Depth 100 -Compress
        $actualJson = $Actual.($property.Name) | ConvertTo-Json -Depth 100 -Compress
        if ($expectedJson -ne $actualJson) {
            throw "$Context field $($property.Name) differs."
        }
    }
}

function Get-WeaponSourceFile {
    param([Parameter(Mandatory)][string] $WeaponRoot, [Parameter(Mandatory)][string] $FormKey)
    $matches = @(
        Get-ChildItem -LiteralPath $WeaponRoot -Filter '*.yaml' -File |
            Where-Object {
                (Get-Content -LiteralPath $_.FullName -TotalCount 1) -eq "FormKey: $FormKey"
            }
    )
    if ($matches.Count -ne 1) {
        throw "Expected one weapon YAML for $FormKey; found $($matches.Count)."
    }
    return $matches[0]
}

function Write-CuratedWeapon {
    param(
        [Parameter(Mandatory)][IO.FileInfo] $Source,
        [Parameter(Mandatory)] $Rule,
        [Parameter(Mandatory)][string] $Destination
    )
    $lines = [Collections.Generic.List[string]]::new()
    foreach ($line in [IO.File]::ReadAllLines($Source.FullName)) { [void] $lines.Add($line) }
    $section = ''
    $changed = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $line = $lines[$index]
        if ($line -match '^([A-Za-z][A-Za-z0-9]*):(?:\s.*)?$') { $section = $Matches[1] }
        $field = $null
        $value = $null
        if ($section -eq 'BasicStats' -and $line -match '^  Damage:\s') {
            $field = 'Damage'; $value = [string]$Rule.damage
        }
        elseif ($section -eq 'Data' -and $line -match '^  Speed:\s') {
            $field = 'Speed'; $value = ([double]$Rule.speed).ToString('0.################', [Globalization.CultureInfo]::InvariantCulture)
        }
        elseif ($section -eq 'Data' -and $line -match '^  Reach:\s') {
            $field = 'Reach'; $value = ([double]$Rule.reach).ToString('0.################', [Globalization.CultureInfo]::InvariantCulture)
        }
        elseif ($section -eq 'Data' -and $line -match '^  Stagger:\s') {
            $field = 'Stagger'; $value = ([double]$Rule.stagger).ToString('0.################', [Globalization.CultureInfo]::InvariantCulture)
        }
        if ($null -ne $field) {
            if (-not $changed.Add($field)) { throw "Duplicate $field field in $($Source.Name)." }
            $lines[$index] = "  ${field}: $value"
        }
    }
    if ($changed.Count -ne 4) {
        throw "Expected to own exactly Damage, Speed, Reach, and Stagger in $($Source.Name); found $($changed -join ', ')."
    }
    Write-Utf8NoBom -Path $Destination -Text (($lines -join "`n") + "`n")
}

function Write-LeveledItemYaml {
    param(
        [Parameter(Mandatory)][string] $FormKey,
        [Parameter(Mandatory)][string] $EditorId,
        [Parameter(Mandatory)] $Flags,
        [Parameter(Mandatory)] $Entries,
        [Parameter(Mandatory)][double] $ChanceNone,
        $ChanceNoneGlobalFormKey,
        [Parameter(Mandatory)][string] $Destination
    )
    if ($null -ne $ChanceNoneGlobalFormKey) {
        throw "A global-backed ChanceNone is unsupported by this private emitter: $FormKey ($ChanceNoneGlobalFormKey)"
    }
    $yaml = [Collections.Generic.List[string]]::new()
    [void]$yaml.Add("FormKey: $FormKey")
    [void]$yaml.Add("EditorID: $EditorId")
    [void]$yaml.Add('FormVersion: 44')
    $chanceText = $ChanceNone.ToString('0.################', [Globalization.CultureInfo]::InvariantCulture)
    [void]$yaml.Add("ChanceNone: $chanceText")
    [void]$yaml.Add('Flags:')
    foreach ($flag in @($Flags)) { [void]$yaml.Add("- $flag") }
    [void]$yaml.Add('Entries:')
    foreach ($entry in @($Entries)) {
        if ($null -eq $entry.referenceFormKey) { throw "Null leveled-list reference in $FormKey." }
        [void]$yaml.Add('- Data:')
        [void]$yaml.Add("    Level: $($entry.level)")
        [void]$yaml.Add("    Reference: $($entry.referenceFormKey)")
        [void]$yaml.Add("    Count: $($entry.count)")
    }
    Write-Utf8NoBom -Path $Destination -Text (($yaml -join "`n") + "`n")
}

function Get-ReviewedLeveledItemRow {
    param(
        [Parameter(Mandatory)][string] $Tool,
        [Parameter(Mandatory)][string] $Plugin,
        [Parameter(Mandatory)][string] $FormKey,
        [Parameter(Mandatory)][string] $EditorId
    )
    $rows = @(Invoke-RecordJsonLines -Tool $Tool -Command 'leveled-items' -Plugin $Plugin)
    $matches = @($rows | Where-Object formKey -eq $FormKey)
    if ($matches.Count -ne 1) { throw "Expected one typed source record for $FormKey; found $($matches.Count)." }
    $row = $matches[0]
    if ($row.editorId -ne $EditorId -or $row.type -ne 'LeveledItem') {
        throw "Typed source identity differs for $FormKey."
    }
    if ($null -ne $row.chanceNoneGlobalFormKey) {
        throw "Global-backed ChanceNone is unsupported for ${FormKey}: $($row.chanceNoneGlobalFormKey)"
    }
    if ([double]$row.chanceNone -lt 0 -or [double]$row.chanceNone -gt 1) {
        throw "ChanceNone is outside 0..1 for $FormKey."
    }
    $raw = Invoke-RecordJsonDocument -Tool $Tool -Command 'record-fields' -Plugin $Plugin -ExtraArguments @($FormKey)
    $supportedNames = @(
        'ChanceNone', 'EditorID', 'Entries', 'Flags', 'FormKey', 'FormVersion',
        'Global', 'IsCompressed', 'IsDeleted', 'MajorRecordFlagsRaw', 'ObjectBounds',
        'SkyrimMajorRecordFlags', 'StaticRegistration', 'Version2', 'VersionControl'
    )
    $rawNames = @($raw.fields.PSObject.Properties.Name | Sort-Object)
    if (($rawNames -join '|') -ne (@($supportedNames | Sort-Object) -join '|')) {
        throw "Source $FormKey has fields outside the reviewed typed LVLI emitter: $($rawNames -join ', ')"
    }
    if ($raw.fields.FormVersion -notin @(40, 44) -or $raw.fields.IsCompressed -or $raw.fields.IsDeleted -or
        $raw.fields.MajorRecordFlagsRaw -ne 0 -or [string]$raw.fields.SkyrimMajorRecordFlags -ne '0' -or
        -not $raw.fields.Global.IsNull -or
        [string]$raw.fields.ObjectBounds.First -ne '0, 0, 0' -or [string]$raw.fields.ObjectBounds.Second -ne '0, 0, 0' -or
        @($raw.fields.Entries).Count -ne @($row.entries).Count) {
        throw "Source $FormKey uses unsupported non-default LVLI metadata."
    }
    return $row
}

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$workRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot 'work\lost-longswords'))
$output = [IO.Path]::GetFullPath($OutputRoot)
$policyFile = [IO.Path]::GetFullPath($PolicyPath)
$proposalFile = [IO.Path]::GetFullPath($ProposalPath)

if ($output -ne (Join-Path $workRoot 'private-curation')) {
    throw "Output must be the exact isolated generated directory: $(Join-Path $workRoot 'private-curation')"
}
if ((Get-Item -LiteralPath $workRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw "The Lost LongSwords work root may not be a reparse point: $workRoot"
}
if (-not (Test-Path -LiteralPath $SkyrimMaster -PathType Leaf)) {
    throw "Skyrim master was not found for output-link validation: $SkyrimMaster"
}
foreach ($tool in @($Spriggit, $RecordTool)) {
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) { throw "Required pinned tool not found: $tool" }
}
$expectedRecordToolSha = 'AF77A44CB037348ECBF63C01B206A0B41F514017B59DB6825AFA8B573534FD85'
$actualRecordToolSha = (Get-FileHash -LiteralPath $RecordTool -Algorithm SHA256).Hash
if ($actualRecordToolSha -ne $expectedRecordToolSha) {
    throw "Record graph CLI hash mismatch: expected $expectedRecordToolSha, got $actualRecordToolSha"
}
$recordToolAssembly = Join-Path (Split-Path -Parent $RecordTool) 'skyrim-record-cli.dll'
$expectedRecordToolAssemblySha = '4A21F63F30C7DBE901EFBCCEA2AD721CD094E0B8C82B50EA0F4A2E3EB4B1F3FA'
if (-not (Test-Path -LiteralPath $recordToolAssembly -PathType Leaf)) {
    throw "Record graph CLI assembly is missing: $recordToolAssembly"
}
$actualRecordToolAssemblySha = (Get-FileHash -LiteralPath $recordToolAssembly -Algorithm SHA256).Hash
if ($actualRecordToolAssemblySha -ne $expectedRecordToolAssemblySha) {
    throw "Record graph CLI assembly hash mismatch: expected $expectedRecordToolAssemblySha, got $actualRecordToolAssemblySha"
}

$policy = Get-Content -Raw -LiteralPath $policyFile | ConvertFrom-Json -Depth 30
$proposalHash = (Get-FileHash -LiteralPath $proposalFile -Algorithm SHA256).Hash
if ($proposalHash -ne $policy.proposalSha256) {
    throw "The approved proposal changed: policy pins $($policy.proposalSha256), current file is $proposalHash. Review and refresh the policy before building."
}
if ($policy.output.plugin -ne 'Ensrick Lost LongSwords Curation.esp') {
    throw "Unexpected output ModKey in policy: $($policy.output.plugin)"
}
if ($policy.stormcloakOutput.plugin -ne 'Ensrick Lost LongSwords Stormcloak Distribution.esp') {
    throw "Unexpected Stormcloak output ModKey in policy: $($policy.stormcloakOutput.plugin)"
}

$validationSource = [IO.Path]::GetFullPath((Join-Path $repoRoot $policy.source.validationTree))
$vendorPlugin = Join-Path (Split-Path -Parent $validationSource) "mod\$($policy.source.plugin)"
if (-not (Test-Path -LiteralPath $vendorPlugin -PathType Leaf)) { throw "Immutable source plugin not found: $vendorPlugin" }
$vendorHash = (Get-FileHash -LiteralPath $vendorPlugin -Algorithm SHA256).Hash
if ($vendorHash -ne $policy.source.pluginSha256) {
    throw "Immutable source plugin hash mismatch: expected $($policy.source.pluginSha256), got $vendorHash"
}
$providerInputs = [ordered]@{}
foreach ($provider in $policy.masterForwarding.providers) {
    $providerPath = if ($provider.plugin -eq 'Skyrim.esm') {
        [IO.Path]::GetFullPath($SkyrimMaster)
    }
    else {
        [IO.Path]::GetFullPath((Join-Path $repoRoot "..\$($provider.pathAtReview)"))
    }
    if (-not (Test-Path -LiteralPath $providerPath -PathType Leaf)) {
        throw "Master-forwarding input was not found: $providerPath"
    }
    $providerHash = (Get-FileHash -LiteralPath $providerPath -Algorithm SHA256).Hash
    if ($providerHash -ne $provider.pluginSha256AtReview) {
        throw "Master-forwarding input changed for $($provider.plugin): expected $($provider.pluginSha256AtReview), got $providerHash"
    }
    $providerInputs[$provider.plugin] = [pscustomobject]@{ path = $providerPath; sha256 = $providerHash }
}
$stormSourceInputs = [ordered]@{}
$stormSourceDescriptors = @(
    [pscustomobject]@{
        plugin = $policy.compatibility.sonsOfSkyrimPlugin
        sha256 = $policy.compatibility.sonsOfSkyrimSha256AtReview
        path = $policy.compatibility.sonsOfSkyrimPathAtReview
    },
    [pscustomobject]@{
        plugin = $policy.compatibility.sonsLuxOrbisPatchPlugin
        sha256 = $policy.compatibility.sonsLuxOrbisPatchSha256AtReview
        path = $policy.compatibility.sonsLuxOrbisPatchPathAtReview
    }
)
foreach ($descriptor in $stormSourceDescriptors) {
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $repoRoot "..\$($descriptor.path)"))
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Stormcloak clone source not found: $sourcePath" }
    $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
    if ($sourceHash -ne $descriptor.sha256) {
        throw "Stormcloak clone source changed for $($descriptor.plugin): expected $($descriptor.sha256), got $sourceHash"
    }
    $stormSourceInputs[$descriptor.plugin] = [pscustomobject]@{ path = $sourcePath; sha256 = $sourceHash }
}

if (Test-Path -LiteralPath $output) {
    if (-not $Clean) { throw "Output exists. Pass -Clean to replace only this generated directory: $output" }
    $resolvedParent = [IO.Path]::GetFullPath((Split-Path -Parent $output))
    if ($resolvedParent -ne $workRoot) { throw "Refusing recursive removal outside exact generated parent: $resolvedParent" }
    Assert-NoReparseTraversal -Path $output -Boundary $workRoot
    Remove-Item -LiteralPath $output -Recurse -Force
}

$patchSource = Join-Path $output 'patch-source'
$stormPatchSource = Join-Path $output 'stormcloak-patch-source'
$modRoot = Join-Path $output 'mod'
$pluginPath = Join-Path $modRoot $policy.output.plugin
$stormPluginPath = Join-Path $modRoot $policy.stormcloakOutput.plugin
New-Item -ItemType Directory -Path (Join-Path $patchSource 'Weapons'), (Join-Path $patchSource 'LeveledItems'), (Join-Path $stormPatchSource 'LeveledItems'), $modRoot -Force | Out-Null

# Bind every copied vendor record to the immutable binary rather than trusting
# a previously generated validation tree.
$freshVendorSource = Join-Path $output 'vendor-proof-source'
Invoke-Checked -Tool $Spriggit -Arguments @('serialize', '-i', $vendorPlugin, '-o', $freshVendorSource, '-g', 'SkyrimSE', '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0', '-u')
$cachedVendorFingerprint = @(Get-TreeFingerprint -Root $validationSource)
$freshVendorFingerprint = @(Get-TreeFingerprint -Root $freshVendorSource)
if (($cachedVendorFingerprint | ConvertTo-Json -Depth 5 -Compress) -ne ($freshVendorFingerprint | ConvertTo-Json -Depth 5 -Compress)) {
    throw 'Cached validation source differs from a fresh serialization of the immutable vendor binary.'
}
$masterForwardSourceRows = @{}
foreach ($record in $policy.masterForwarding.records) {
    if ($record.type -ne 'LeveledItem') {
        throw "Only reviewed typed LeveledItem forwarding is supported; got $($record.type)."
    }
    $providerPath = $providerInputs[$record.provider].path
    $row = Get-ReviewedLeveledItemRow -Tool $RecordTool -Plugin $providerPath -FormKey $record.formKey -EditorId $record.editorId
    $flags = @(([string]$row.flags -split ',\s*') | Where-Object { $_ })
    $parts = $record.formKey -split ':', 2
    $fileName = "$($record.editorId) - $($parts[0])_$($parts[1]).yaml"
    Write-LeveledItemYaml -FormKey $record.formKey -EditorId $record.editorId -Flags $flags -Entries $row.entries `
        -ChanceNone ([double]$row.chanceNone) -ChanceNoneGlobalFormKey $row.chanceNoneGlobalFormKey `
        -Destination (Join-Path $patchSource "LeveledItems\$fileName")
    $masterForwardSourceRows[$record.formKey] = $row
}

$masterYaml = ($policy.output.masters | ForEach-Object { "  - Master: $_`n    FileSize: 0" }) -join "`n"
$header = @"
SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.41
ModKey: $($policy.output.plugin)
GameRelease: SkyrimSE
ModHeader:
  Flags:
  - Small
  FormVersion: 44
  Stats:
    Version: 1.7
  Author: Ensrick
  Description: 'PRIVATE Lost LongSwords curation: reviewed weapon fields and owned soldier probability lists. Requires the separately installed vendor assets/plugin and SkyPatcher.'
  MasterReferences:
$masterYaml
"@
Write-Utf8NoBom -Path (Join-Path $patchSource 'RecordData.yaml') -Text ($header.TrimStart() + "`n")
$meta = [ordered]@{
    PackageName = 'Spriggit.Yaml.Skyrim'
    Version = '0.41.0'
    Release = 'SkyrimSE'
    ModKey = $policy.output.plugin
}
Write-Utf8NoBom -Path (Join-Path $patchSource 'spriggit-meta.json') -Text (($meta | ConvertTo-Json) + "`n")

$stormMasterYaml = ($policy.stormcloakOutput.masters | ForEach-Object { "  - Master: $_`n    FileSize: 0" }) -join "`n"
$stormHeader = @"
SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.41
ModKey: $($policy.stormcloakOutput.plugin)
GameRelease: SkyrimSE
ModHeader:
  Flags:
  - Small
  FormVersion: 44
  Stats:
    Version: 1.7
  Author: Ensrick
  Description: 'PRIVATE isolated Stormcloak soldier distribution for Lost LongSwords. Requires LostLongSwords.esp, Sons of Skyrim, the companion early curation ESP, and SkyPatcher.'
  MasterReferences:
$stormMasterYaml
"@
Write-Utf8NoBom -Path (Join-Path $stormPatchSource 'RecordData.yaml') -Text ($stormHeader.TrimStart() + "`n")
$stormMeta = [ordered]@{
    PackageName = 'Spriggit.Yaml.Skyrim'
    Version = '0.41.0'
    Release = 'SkyrimSE'
    ModKey = $policy.stormcloakOutput.plugin
}
Write-Utf8NoBom -Path (Join-Path $stormPatchSource 'spriggit-meta.json') -Text (($stormMeta | ConvertTo-Json) + "`n")

$weaponRoot = Join-Path $freshVendorSource 'Weapons'
foreach ($rule in $policy.weapons) {
    $source = Get-WeaponSourceFile -WeaponRoot $weaponRoot -FormKey $rule.formKey
    Write-CuratedWeapon -Source $source -Rule $rule -Destination (Join-Path $patchSource "Weapons\$($source.Name)")
}

foreach ($list in $policy.ownedLeveledItems) {
    $fileName = "$($list.editorId) - $(($list.formKey -split ':', 2)[0])_$($policy.output.plugin).yaml"
    Write-LeveledItemYaml -FormKey $list.formKey -EditorId $list.editorId -Flags $list.flags -Entries $list.entries `
        -ChanceNone 0 -ChanceNoneGlobalFormKey $null -Destination (Join-Path $patchSource "LeveledItems\$fileName")
}

$stormCloneSourceRows = @{}
$stormExpectedEntries = @{}
foreach ($list in $policy.stormcloakOwnedLeveledItems) {
    $sourceInput = $stormSourceInputs[$list.sourceProvider]
    if ($null -eq $sourceInput) { throw "No pinned Stormcloak source input for $($list.sourceProvider)." }
    $sourceRow = Get-ReviewedLeveledItemRow -Tool $RecordTool -Plugin $sourceInput.path -FormKey $list.sourceFormKey -EditorId $list.sourceEditorId
    $entries = [Collections.Generic.List[object]]::new()
    foreach ($entry in @($sourceRow.entries)) {
        [void]$entries.Add([pscustomobject]@{
            level = [int]$entry.level
            count = [int]$entry.count
            referenceFormKey = [string]$entry.referenceFormKey
        })
    }
    if ($list.transform.kind -eq 'append') {
        if (@($entries | Where-Object referenceFormKey -eq $list.transform.entry.referenceFormKey).Count -ne 0) {
            throw "Stormcloak append target already exists in $($list.sourceFormKey)."
        }
        [void]$entries.Add([pscustomobject]@{
            level = [int]$list.transform.entry.level
            count = [int]$list.transform.entry.count
            referenceFormKey = [string]$list.transform.entry.referenceFormKey
        })
    }
    elseif ($list.transform.kind -eq 'replaceExactlyOnce') {
        $replaced = 0
        foreach ($entry in $entries) {
            if ($entry.referenceFormKey -eq $list.transform.from) {
                $entry.referenceFormKey = [string]$list.transform.to
                $replaced++
            }
        }
        if ($replaced -ne 1) {
            throw "Expected exactly one $($list.transform.from) in $($list.sourceFormKey); replaced $replaced."
        }
    }
    else { throw "Unsupported Stormcloak clone transform: $($list.transform.kind)" }
    $flags = @(([string]$sourceRow.flags -split ',\s*') | Where-Object { $_ })
    $parts = $list.formKey -split ':', 2
    $fileName = "$($list.editorId) - $($parts[0])_$($parts[1]).yaml"
    Write-LeveledItemYaml -FormKey $list.formKey -EditorId $list.editorId -Flags $flags -Entries $entries `
        -ChanceNone ([double]$sourceRow.chanceNone) -ChanceNoneGlobalFormKey $sourceRow.chanceNoneGlobalFormKey `
        -Destination (Join-Path $stormPatchSource "LeveledItems\$fileName")
    $stormCloneSourceRows[$list.formKey] = $sourceRow
    $stormExpectedEntries[$list.formKey] = @($entries)
}

Invoke-Checked -Tool $Spriggit -Arguments @('deserialize', '-i', $patchSource, '-o', $pluginPath, '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0')
Invoke-Checked -Tool $Spriggit -Arguments @('deserialize', '-i', $stormPatchSource, '-o', $stormPluginPath, '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0')

$configRoot = Join-Path $modRoot 'SKSE\Plugins\SkyPatcher'
$leveledLines = [Collections.Generic.List[string]]::new()
[void]$leveledLines.Add('; Generated from private-curation-policy.json. Removal pass precedes approved additions.')
foreach ($edge in @($policy.vendorLeveledEdges) + @($policy.excludedInternalEdges)) {
    [void]$leveledLines.Add("filterByLLs=$(Convert-FormKeyToSkyPatcher $edge.target):removeFromLLs=$(Convert-FormKeyToSkyPatcher $edge.remove)")
}
[void]$leveledLines.Add('')
[void]$leveledLines.Add('; Curated nonmilitary and specialist routes; military soldiers use isolated owned lists.')
foreach ($edge in $policy.safeLeveledAdditions) {
    [void]$leveledLines.Add("filterByLLs=$(Convert-FormKeyToSkyPatcher $edge.target):addOnceToLLs=$(Convert-FormKeyToSkyPatcher $edge.add)~$($edge.level)~$($edge.count)")
}
Write-Utf8NoBom -Path (Join-Path $configRoot 'leveledList\zz Ensrick Lost LongSwords Curation\Ensrick Lost LongSwords Curation.ini') -Text (($leveledLines -join "`n") + "`n")

$npcLines = [Collections.Generic.List[string]]::new()
[void]$npcLines.Add('; Remove vendor named-NPC injections, then branch only reviewed ordinary soldier templates and inheritors.')
foreach ($op in $policy.npcOperations) {
    if ($null -ne $op.PSObject.Properties['remove']) {
        [void]$npcLines.Add("filterByNpcs=$(Convert-FormKeyToSkyPatcher $op.target):objectsToRemove=$(Convert-FormKeyToSkyPatcher $op.remove)")
    }
    elseif ($null -ne $op.PSObject.Properties['replace']) {
        [void]$npcLines.Add("filterByNpcs=$(Convert-FormKeyToSkyPatcher $op.target):objectsToReplace=$(Convert-FormKeyToSkyPatcher $op.replace)~$(Convert-FormKeyToSkyPatcher $op.with)")
    }
    else { throw "Unsupported NPC operation for $($op.target)" }
}
Write-Utf8NoBom -Path (Join-Path $configRoot 'npc\zz Ensrick Lost LongSwords Curation\Ensrick Lost LongSwords Curation.ini') -Text (($npcLines -join "`n") + "`n")

$containerLines = foreach ($op in $policy.containerOperations) {
    "filterByContainers=$(Convert-FormKeyToSkyPatcher $op.target):removeFromContainers=$(Convert-FormKeyToSkyPatcher $op.remove)"
}
Write-Utf8NoBom -Path (Join-Path $configRoot 'container\zz Ensrick Lost LongSwords Curation\Ensrick Lost LongSwords Curation.ini') -Text (($containerLines -join "`n") + "`n")

$constructibleLines = foreach ($op in $policy.disabledConstructibleObjects) {
    "filterByCobjs=$(Convert-FormKeyToSkyPatcher $op.formKey):workbenchKeyword=null"
}
Write-Utf8NoBom -Path (Join-Path $configRoot 'constructibleObject\zz Ensrick Lost LongSwords Curation\Ensrick Lost LongSwords Curation.ini') -Text (($constructibleLines -join "`n") + "`n")

# A missing/unknown selector can turn a mutating SkyPatcher line into a
# catch-all. Require exactly one recognized nonempty selector and one reviewed
# action on every generated active line, and explicitly ban the unsafe token.
$configContracts = @(
    [pscustomobject]@{ name = 'leveledList'; lines = @($leveledLines); pattern = '^filterByLLs=[^:]+:(removeFromLLs|addOnceToLLs)=[^:]+$' },
    [pscustomobject]@{ name = 'npc'; lines = @($npcLines); pattern = '^filterByNpcs=[^:]+:(objectsToRemove|objectsToReplace)=[^:]+$' },
    [pscustomobject]@{ name = 'container'; lines = @($containerLines); pattern = '^filterByContainers=[^:]+:removeFromContainers=[^:]+$' },
    [pscustomobject]@{ name = 'constructibleObject'; lines = @($constructibleLines); pattern = '^filterByCobjs=[^:]+:workbenchKeyword=null$' }
)
foreach ($contract in $configContracts) {
    foreach ($line in $contract.lines) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith(';')) { continue }
        if ($line -match 'filterByConstructibleObjects' -or $line -notmatch $contract.pattern) {
            throw "Unsafe or unsupported $($contract.name) SkyPatcher line: $line"
        }
    }
}

# A two-generation strict round trip catches schema drift and non-deterministic source.
$roundTripA = Join-Path $output 'roundtrip-a'
$roundTripPluginRoot = Join-Path $output 'roundtrip-plugin'
$roundTripPlugin = Join-Path $roundTripPluginRoot $policy.output.plugin
$roundTripB = Join-Path $output 'roundtrip-b'
New-Item -ItemType Directory -Path $roundTripPluginRoot -Force | Out-Null
Invoke-Checked -Tool $Spriggit -Arguments @('serialize', '-i', $pluginPath, '-o', $roundTripA, '-g', 'SkyrimSE', '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0', '-u')
Invoke-Checked -Tool $Spriggit -Arguments @('deserialize', '-i', $roundTripA, '-o', $roundTripPlugin, '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0')
Invoke-Checked -Tool $Spriggit -Arguments @('serialize', '-i', $roundTripPlugin, '-o', $roundTripB, '-g', 'SkyrimSE', '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0', '-u')
$fingerprintA = @(Get-TreeFingerprint -Root $roundTripA)
$fingerprintB = @(Get-TreeFingerprint -Root $roundTripB)
if (($fingerprintA | ConvertTo-Json -Depth 5 -Compress) -ne ($fingerprintB | ConvertTo-Json -Depth 5 -Compress)) {
    throw 'Spriggit strict two-generation round-trip fingerprint mismatch.'
}

$stormRoundTripA = Join-Path $output 'stormcloak-roundtrip-a'
$stormRoundTripPluginRoot = Join-Path $output 'stormcloak-roundtrip-plugin'
$stormRoundTripPlugin = Join-Path $stormRoundTripPluginRoot $policy.stormcloakOutput.plugin
$stormRoundTripB = Join-Path $output 'stormcloak-roundtrip-b'
New-Item -ItemType Directory -Path $stormRoundTripPluginRoot -Force | Out-Null
Invoke-Checked -Tool $Spriggit -Arguments @('serialize', '-i', $stormPluginPath, '-o', $stormRoundTripA, '-g', 'SkyrimSE', '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0', '-u')
Invoke-Checked -Tool $Spriggit -Arguments @('deserialize', '-i', $stormRoundTripA, '-o', $stormRoundTripPlugin, '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0')
Invoke-Checked -Tool $Spriggit -Arguments @('serialize', '-i', $stormRoundTripPlugin, '-o', $stormRoundTripB, '-g', 'SkyrimSE', '-p', 'Spriggit.Yaml.Skyrim', '-v', '0.41.0', '-u')
$stormFingerprintA = @(Get-TreeFingerprint -Root $stormRoundTripA)
$stormFingerprintB = @(Get-TreeFingerprint -Root $stormRoundTripB)
if (($stormFingerprintA | ConvertTo-Json -Depth 5 -Compress) -ne ($stormFingerprintB | ConvertTo-Json -Depth 5 -Compress)) {
    throw 'Stormcloak ESPFE Spriggit strict two-generation round-trip fingerprint mismatch.'
}

$pluginInfo = Invoke-RecordJsonDocument -Tool $RecordTool -Command 'plugin-info' -Plugin $pluginPath
$builtRecords = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'records' -Plugin $pluginPath)
$weapons = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'weapons' -Plugin $pluginPath)
$leveled = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'leveled-items' -Plugin $pluginPath)
$stormPluginInfo = Invoke-RecordJsonDocument -Tool $RecordTool -Command 'plugin-info' -Plugin $stormPluginPath
$stormBuiltRecords = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'records' -Plugin $stormPluginPath)
$stormLeveled = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'leveled-items' -Plugin $stormPluginPath)

$expectedRecords = @(
    @($policy.weapons | ForEach-Object { [pscustomobject]@{ formKey = $_.formKey; type = 'Weapon'; editorId = $_.editorId } })
    @($policy.ownedLeveledItems | ForEach-Object { [pscustomobject]@{ formKey = $_.formKey; type = 'LeveledItem'; editorId = $_.editorId } })
    @($policy.masterForwarding.records | ForEach-Object { [pscustomobject]@{ formKey = $_.formKey; type = $_.type; editorId = $_.editorId } })
)
if ($pluginInfo.records -ne $expectedRecords.Count -or $builtRecords.Count -ne $expectedRecords.Count) {
    throw "Unexpected built plugin record count: header=$($pluginInfo.records), enumerated=$($builtRecords.Count), expected=$($expectedRecords.Count)"
}
$expectedKeys = @($expectedRecords.formKey | Sort-Object)
$actualKeys = @($builtRecords.formKey | Sort-Object)
if (($expectedKeys -join '|') -ne ($actualKeys -join '|')) {
    throw 'Built plugin FormKey inventory differs from the exact policy inventory.'
}
foreach ($expected in $expectedRecords) {
    $matches = @($builtRecords | Where-Object formKey -eq $expected.formKey)
    if ($matches.Count -ne 1 -or $matches[0].type -ne $expected.type -or $matches[0].editorId -ne $expected.editorId) {
        throw "Built identity differs for $($expected.formKey)."
    }
}
$actualTypeCounts = @{}
foreach ($group in @($builtRecords | Group-Object type)) { $actualTypeCounts[$group.Name] = $group.Count }
foreach ($property in $policy.output.expectedRecordTypes.PSObject.Properties) {
    if ($actualTypeCounts[$property.Name] -ne [int]$property.Value) {
        throw "Unexpected $($property.Name) count: $($actualTypeCounts[$property.Name]); expected $($property.Value)."
    }
    [void]$actualTypeCounts.Remove($property.Name)
}
if ($actualTypeCounts.Count -ne 0) {
    throw "Built plugin contains an unexpected record type: $($actualTypeCounts.Keys -join ', ')"
}
if (($pluginInfo.masters -join '|') -ne ($policy.output.masters -join '|')) {
    throw "Unexpected master order: $($pluginInfo.masters -join ', ')"
}

$stormExpectedRecords = @(
    $policy.stormcloakOwnedLeveledItems | ForEach-Object {
        [pscustomobject]@{ formKey = $_.formKey; type = 'LeveledItem'; editorId = $_.editorId }
    }
)
if ($stormPluginInfo.records -ne $stormExpectedRecords.Count -or $stormBuiltRecords.Count -ne $stormExpectedRecords.Count) {
    throw "Unexpected Stormcloak plugin record count: header=$($stormPluginInfo.records), enumerated=$($stormBuiltRecords.Count), expected=$($stormExpectedRecords.Count)"
}
$stormExpectedKeys = @($stormExpectedRecords.formKey | Sort-Object)
$stormActualKeys = @($stormBuiltRecords.formKey | Sort-Object)
if (($stormExpectedKeys -join '|') -ne ($stormActualKeys -join '|')) {
    throw 'Stormcloak plugin FormKey inventory differs from the exact policy inventory.'
}
foreach ($expected in $stormExpectedRecords) {
    $matches = @($stormBuiltRecords | Where-Object formKey -eq $expected.formKey)
    if ($matches.Count -ne 1 -or $matches[0].type -ne $expected.type -or $matches[0].editorId -ne $expected.editorId) {
        throw "Stormcloak plugin identity differs for $($expected.formKey)."
    }
}
$stormActualTypeCounts = @{}
foreach ($group in @($stormBuiltRecords | Group-Object type)) { $stormActualTypeCounts[$group.Name] = $group.Count }
foreach ($property in $policy.stormcloakOutput.expectedRecordTypes.PSObject.Properties) {
    if ($stormActualTypeCounts[$property.Name] -ne [int]$property.Value) {
        throw "Unexpected Stormcloak $($property.Name) count: $($stormActualTypeCounts[$property.Name]); expected $($property.Value)."
    }
    [void]$stormActualTypeCounts.Remove($property.Name)
}
if ($stormActualTypeCounts.Count -ne 0) {
    throw "Stormcloak plugin contains an unexpected record type: $($stormActualTypeCounts.Keys -join ', ')"
}
if (($stormPluginInfo.masters -join '|') -ne ($policy.stormcloakOutput.masters -join '|')) {
    throw "Unexpected Stormcloak master order: $($stormPluginInfo.masters -join ', ')"
}

$stormCloneSemanticChecks = 0
foreach ($list in $policy.stormcloakOwnedLeveledItems) {
    $sourceRow = $stormCloneSourceRows[$list.formKey]
    $builtMatch = @($stormLeveled | Where-Object formKey -eq $list.formKey)
    if ($null -eq $sourceRow -or $builtMatch.Count -ne 1) {
        throw "Could not compare one source and one built Stormcloak list for $($list.formKey)."
    }
    $builtRow = $builtMatch[0]
    Assert-ObjectPropertiesEqual -Expected $sourceRow -Actual $builtRow `
        -Ignore @('plugin', 'formKey', 'editorId', 'entries') -Context "Stormcloak clone preservation $($list.formKey)"
    $expectedEntriesJson = ConvertTo-Json -InputObject @($stormExpectedEntries[$list.formKey]) -Depth 10 -Compress
    $builtEntriesJson = ConvertTo-Json -InputObject @($builtRow.entries) -Depth 10 -Compress
    if ($expectedEntriesJson -ne $builtEntriesJson) {
        throw "Stormcloak clone entries differ for $($list.formKey)."
    }
    $stormCloneSemanticChecks++
}

# The nine WEAP overrides are exact fresh vendor projections. Only the four
# approved fields may differ; every other field exposed by the typed reader
# must survive unchanged.
$sourceWeapons = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'weapons' -Plugin $vendorPlugin)
foreach ($rule in $policy.weapons) {
    $sourceMatch = @($sourceWeapons | Where-Object formKey -eq $rule.formKey)
    $builtMatch = @($weapons | Where-Object formKey -eq $rule.formKey)
    if ($sourceMatch.Count -ne 1 -or $builtMatch.Count -ne 1) {
        throw "Could not compare one source and one built weapon for $($rule.formKey)."
    }
    $builtWeapon = $builtMatch[0]
    foreach ($field in @('damage', 'speed', 'reach', 'stagger')) {
        if ([double]$builtWeapon.$field -ne [double]$rule.$field) {
            throw "Built weapon $($rule.formKey) has unexpected $field=$($builtWeapon.$field)."
        }
    }
    Assert-ObjectPropertiesEqual -Expected $sourceMatch[0] -Actual $builtWeapon -Ignore @('source', 'damage', 'speed', 'reach', 'stagger') -Context "Weapon preservation $($rule.formKey)"
}

# Each current master forward is generated from, then compared with, the
# complete typed functional semantics of its pinned provider binary.
$masterForwardSemanticChecks = 0
foreach ($record in $policy.masterForwarding.records) {
    if ($record.type -ne 'LeveledItem') {
        throw "Private master forwarding currently supports only reviewed LeveledItem semantics; got $($record.type)."
    }
    $providerMatch = @($masterForwardSourceRows[$record.formKey])
    $builtMatch = @($leveled | Where-Object formKey -eq $record.formKey)
    if ($providerMatch.Count -ne 1 -or $builtMatch.Count -ne 1) {
        throw "Could not compare one provider and one built leveled item for $($record.formKey)."
    }
    Assert-ObjectPropertiesEqual -Expected $providerMatch[0] -Actual $builtMatch[0] -Ignore @('plugin') -Context "Master forward $($record.formKey)"
    $masterForwardSemanticChecks++
}

# Resolve every FormLink in every output record against the exact declared
# master binaries, the immutable vendor, or the output itself.
$identityInputs = [ordered]@{ 'Skyrim.esm' = [IO.Path]::GetFullPath($SkyrimMaster) }
foreach ($provider in $policy.masterForwarding.providers) {
    $identityInputs[$provider.plugin] = $providerInputs[$provider.plugin].path
}
$identityInputs[$policy.source.plugin] = $vendorPlugin
$identityInputs[$policy.output.plugin] = $pluginPath
$allowedIdentityPlugins = @($policy.output.masters) + @($policy.output.plugin)
if ((@($identityInputs.Keys | Sort-Object) -join '|') -ne (@($allowedIdentityPlugins | Sort-Object) -join '|')) {
    throw 'Output-link identity inputs do not exactly match declared masters plus the output plugin.'
}
$identities = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$identityCounts = [ordered]@{}
foreach ($entry in $identityInputs.GetEnumerator()) {
    $records = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'records' -Plugin $entry.Value)
    foreach ($record in $records) { [void]$identities.Add($record.formKey) }
    $identityCounts[$entry.Key] = $records.Count
}
$linkRows = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'record-links' -Plugin $pluginPath)
if ($linkRows.Count -ne $builtRecords.Count) {
    throw "Output link inventory has $($linkRows.Count) records; expected $($builtRecords.Count)."
}
$linkEdgesChecked = 0
foreach ($record in $linkRows) {
    foreach ($link in @($record.links)) {
        if (-not $identities.Contains([string]$link.formKey)) {
            throw "Unresolved output link $($link.formKey) from $($record.formKey)."
        }
        $linkEdgesChecked++
    }
}

$stormIdentityInputs = [ordered]@{
    'Skyrim.esm' = [IO.Path]::GetFullPath($SkyrimMaster)
    $policy.source.plugin = $vendorPlugin
    $policy.compatibility.sonsOfSkyrimPlugin = $stormSourceInputs[$policy.compatibility.sonsOfSkyrimPlugin].path
    $policy.stormcloakOutput.plugin = $stormPluginPath
}
$stormAllowedIdentityPlugins = @($policy.stormcloakOutput.masters) + @($policy.stormcloakOutput.plugin)
if ((@($stormIdentityInputs.Keys | Sort-Object) -join '|') -ne (@($stormAllowedIdentityPlugins | Sort-Object) -join '|')) {
    throw 'Stormcloak output-link identity inputs do not exactly match declared masters plus the output plugin.'
}
$stormIdentities = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$stormIdentityCounts = [ordered]@{}
foreach ($entry in $stormIdentityInputs.GetEnumerator()) {
    $records = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'records' -Plugin $entry.Value)
    foreach ($record in $records) { [void]$stormIdentities.Add($record.formKey) }
    $stormIdentityCounts[$entry.Key] = $records.Count
}
$stormLinkRows = @(Invoke-RecordJsonLines -Tool $RecordTool -Command 'record-links' -Plugin $stormPluginPath)
if ($stormLinkRows.Count -ne $stormBuiltRecords.Count) {
    throw "Stormcloak output link inventory has $($stormLinkRows.Count) records; expected $($stormBuiltRecords.Count)."
}
$stormLinkEdgesChecked = 0
foreach ($record in $stormLinkRows) {
    foreach ($link in @($record.links)) {
        if (-not $stormIdentities.Contains([string]$link.formKey)) {
            throw "Unresolved Stormcloak output link $($link.formKey) from $($record.formKey)."
        }
        $stormLinkEdgesChecked++
    }
}

$report = [ordered]@{
    schemaVersion = 1
    builtAtUtc = [DateTime]::UtcNow.ToString('o')
    status = 'offline-built-builder-validation-passed-profile-validation-pending'
    issue = $policy.issue
    proposalSha256 = $proposalHash
    policySha256 = (Get-FileHash -LiteralPath $policyFile -Algorithm SHA256).Hash
    immutableVendorPluginSha256 = $vendorHash
    masterForwardingInputs = @($policy.masterForwarding.providers | ForEach-Object {
        [ordered]@{ plugin = $_.plugin; sha256 = $providerInputs[$_.plugin].sha256; records = @($policy.masterForwarding.records | Where-Object provider -eq $_.plugin).Count }
    })
    stormcloakCloneInputs = @($stormSourceDescriptors | ForEach-Object {
        [ordered]@{
            plugin = $_.plugin
            sha256 = $stormSourceInputs[$_.plugin].sha256
            recordsCloned = @($policy.stormcloakOwnedLeveledItems | Where-Object sourceProvider -eq $_.plugin).Count
        }
    })
    sourceProjection = [ordered]@{
        weaponsCopiedFromFreshVendorSerialization = @($policy.weapons).Count
        weaponOwnedFields = @('damage', 'speed', 'reach', 'stagger')
        weaponOtherTypedFieldsPreserved = $true
        masterForwardSemanticChecks = $masterForwardSemanticChecks
        masterForwardIgnoredBinaryBookkeeping = @('FormVersion', 'Version2', 'VersionControl')
        auditedNoOpCellForwardsOmitted = @($policy.masterForwarding.auditedNoOpCellOverlaps).Count
        masterForwardGeneratedFromPinnedTypedProvider = $true
        masterForwardUnsupportedMetadataRejected = $true
        stormcloakCloneSemanticChecks = $stormCloneSemanticChecks
        stormcloakTransforms = @($policy.stormcloakOwnedLeveledItems | ForEach-Object {
            [ordered]@{
                outputFormKey = $_.formKey
                sourceFormKey = $_.sourceFormKey
                sourceProvider = $_.sourceProvider
                transform = $_.transform
            }
        })
    }
    output = [ordered]@{
        plugin = $policy.output.plugin
        path = $pluginPath
        sha256 = (Get-FileHash -LiteralPath $pluginPath -Algorithm SHA256).Hash
        records = $pluginInfo.records
        recordTypes = $pluginInfo.recordTypes
        masters = @($pluginInfo.masters)
        smallFlagConfirmedByRoundTripSource = (Get-Content -Raw -LiteralPath (Join-Path $roundTripA 'RecordData.yaml')) -match '(?m)^  - Small\r?$|^  Flags:\r?\n  - Small'
    }
    stormcloakOutput = [ordered]@{
        plugin = $policy.stormcloakOutput.plugin
        path = $stormPluginPath
        sha256 = (Get-FileHash -LiteralPath $stormPluginPath -Algorithm SHA256).Hash
        records = $stormPluginInfo.records
        recordTypes = $stormPluginInfo.recordTypes
        masters = @($stormPluginInfo.masters)
        loadOrder = $policy.stormcloakOutput.loadOrder
        smallFlagConfirmedByRoundTripSource = (Get-Content -Raw -LiteralPath (Join-Path $stormRoundTripA 'RecordData.yaml')) -match '(?m)^  - Small\r?$|^  Flags:\r?\n  - Small'
    }
    outputLinkClosure = [ordered]@{
        declaredMasterAndOutputIdentityCounts = $identityCounts
        outputRecordsChecked = $linkRows.Count
        edgesChecked = $linkEdgesChecked
        unresolved = 0
        skyrimMasterSha256 = (Get-FileHash -LiteralPath $SkyrimMaster -Algorithm SHA256).Hash
    }
    stormcloakOutputLinkClosure = [ordered]@{
        declaredMasterAndOutputIdentityCounts = $stormIdentityCounts
        outputRecordsChecked = $stormLinkRows.Count
        edgesChecked = $stormLinkEdgesChecked
        unresolved = 0
    }
    configOperations = [ordered]@{
        leveledRemovals = @($policy.vendorLeveledEdges).Count + @($policy.excludedInternalEdges).Count
        leveledAdditions = @($policy.safeLeveledAdditions).Count
        approvedSemanticSubstitutions = @($policy.approvedSemanticSubstitutions).Count
        npc = @($policy.npcOperations).Count
        container = @($policy.containerOperations).Count
        constructibleObjectDisabled = @($policy.disabledConstructibleObjects).Count
        placedReferencesDisabled = 0
        placedReferencesRetained = @($policy.retainedPlacedReferences).Count
    }
    probabilities = [ordered]@{
        imperialLongswordAtLevel5Plus = '1/12 of the selected ordinary-soldier weapon slot (8.333%); 0 below level 5'
        stormcloakLongswordConditional2H = '1/4 of the SoS two-handed sublist'
        stormcloakLongswordOrdinaryMixedStyle = '1/3 parent chance times 1/4 sublist chance = 1/12 (8.333%)'
    }
    gates = [ordered]@{
        sourceAssetsCopied = $false
        sourceFormsCompactedOrDeleted = $false
        sourcePluginMutated = $false
        validSourcePlacementsRetained = $true
        spriggitTwoGenerationRoundTripBothOutputs = $true
        exactRecordInventoryBothOutputs = $true
        weaponFourFieldProjection = $true
        masterForwardSemanticEquality = $true
        stormcloakCloneSemanticEquality = $true
        outputLinkClosureBothOutputs = $true
        runtimeValidationStillRequired = $true
        liveInstallPerformed = $false
        vendorLoadOrderGate = $policy.compatibility.vendorLoadOrderGate
    }
    tools = [ordered]@{
        spriggit = $Spriggit
        recordCli = $RecordTool
        recordCliSha256 = $actualRecordToolSha
        recordCliAssemblySha256 = $actualRecordToolAssemblySha
    }
}
Write-Utf8NoBom -Path (Join-Path $output 'build-report.json') -Text (($report | ConvertTo-Json -Depth 12) + "`n")
$report
