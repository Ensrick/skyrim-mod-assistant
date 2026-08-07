#requires -Version 7.0
[CmdletBinding()]
param(
    [string] $WorkRoot = (Join-Path $PSScriptRoot '..\..\work\lost-longswords'),
    [string] $NifTool = 'nif-port-cli.exe',
    [string] $RecordTool = 'skyrim-record-cli.exe',
    [string] $SkyrimMaster = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\Skyrim.esm'
)

$ErrorActionPreference = 'Stop'
foreach ($toolVariable in @('NifTool', 'RecordTool')) {
    $toolPath = Get-Variable -Name $toolVariable -ValueOnly
    if (-not [System.IO.Path]::IsPathFullyQualified($toolPath)) {
        $resolvedTool = Get-Command $toolPath -CommandType Application -ErrorAction SilentlyContinue
        if ($resolvedTool) {
            Set-Variable -Name $toolVariable -Value $resolvedTool.Source
        }
    }
}

foreach ($requiredTool in @($NifTool, $RecordTool)) {
    if (-not (Test-Path -LiteralPath $requiredTool -PathType Leaf)) {
        throw "Required CLI was not found: $requiredTool"
    }
}
$work = [System.IO.Path]::GetFullPath($WorkRoot)
$privatePort = Join-Path $work 'private-port'
$modRoot = Join-Path $privatePort 'mod'
$validationSource = Join-Path $privatePort 'validation-source'
$plugin = Join-Path $modRoot 'LostLongSwords.esp'

$meshOutput = @(& $NifTool inspect (Join-Path $modRoot 'meshes'))
if ($LASTEXITCODE -ne 0) { throw 'NIF inspection failed.' }
$meshes = @($meshOutput | ForEach-Object { $_ | ConvertFrom-Json })
if ($meshes.Count -ne 11) { throw "Expected 11 meshes, found $($meshes.Count)." }
foreach ($mesh in $meshes) {
    if (-not $mesh.valid -or $mesh.unknownBlocks -or -not $mesh.isSSE -or
        $mesh.streamVersion -ne 100 -or -not $mesh.sseGeometryCompatible) {
        throw "Invalid SSE mesh: $($mesh.path)"
    }
    foreach ($texture in $mesh.textures) {
        if ($texture -notmatch '^(?i)textures\\weapons\\') { continue }
        $assetPath = Join-Path $modRoot ($texture -replace '\\', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $assetPath -PathType Leaf)) {
            throw "Unresolved custom texture reference in $($mesh.path): $texture"
        }
    }
}

$textures = @(Get-ChildItem (Join-Path $modRoot 'textures') -Recurse -Filter *.dds -File)
if ($textures.Count -ne 66) { throw "Expected 66 textures, found $($textures.Count)." }
$ddsFormats = @{}
foreach ($texture in $textures) {
    $bytes = [IO.File]::ReadAllBytes($texture.FullName)
    if ($bytes.Length -lt 128 -or [Text.Encoding]::ASCII.GetString($bytes, 0, 4) -ne 'DDS ') {
        throw "Invalid DDS header: $($texture.FullName)"
    }
    $headerSize = [BitConverter]::ToUInt32($bytes, 4)
    $height = [BitConverter]::ToUInt32($bytes, 12)
    $width = [BitConverter]::ToUInt32($bytes, 16)
    $pixelFormatSize = [BitConverter]::ToUInt32($bytes, 76)
    if ($headerSize -ne 124 -or $pixelFormatSize -ne 32 -or $width -eq 0 -or $height -eq 0) {
        throw "Malformed DDS fields: $($texture.FullName)"
    }
    $fourCc = [Text.Encoding]::ASCII.GetString($bytes, 84, 4).Trim([char]0)
    if (-not $ddsFormats.ContainsKey($fourCc)) { $ddsFormats[$fourCc] = 0 }
    $ddsFormats[$fourCc]++
}

$weaponOutput = @(& $RecordTool weapons $plugin)
if ($LASTEXITCODE -ne 0) { throw 'Plugin record inspection failed.' }
$weapons = @($weaponOutput | ForEach-Object { $_ | ConvertFrom-Json })
if ($weapons.Count -ne 12) { throw "Expected 12 weapons, found $($weapons.Count)." }
if ($weapons.editorId -match '(?i)dragonbone') { throw 'Dragonbone weapon remains in the binary plugin.' }
if ($weapons.animationType | Where-Object { $_ -ne 'TwoHandSword' }) {
    throw 'A surviving weapon is not configured for two-handed sword animation.'
}
if ($weapons.skill | Where-Object { $_ -ne 'TwoHanded' }) {
    throw 'A surviving weapon does not use the Two-Handed skill.'
}
$linkAudit = (& $RecordTool audit-links $SkyrimMaster $plugin) | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $linkAudit.unresolved.Count -ne 0) {
    throw 'The plugin contains unresolved form links.'
}

if (rg -l -i 'dragonbone|009F45|009F46|009F47|009F48|FormVersion: 40' $validationSource) {
    throw 'Removed content or an LE form version remains after binary round-trip.'
}
$header = Get-Content (Join-Path $validationSource 'RecordData.yaml') -Raw
if ($header -notmatch '(?m)^    Version: 1\.7\r?$') {
    throw 'The binary plugin header is not Skyrim SE header version 1.7.'
}

$report = [ordered]@{
    auditedAt = [DateTime]::UtcNow.ToString('o')
    plugin = [ordered]@{
        path = $plugin
        sha256 = (Get-FileHash $plugin -Algorithm SHA256).Hash
        formVersion = 44
        headerVersion = 1.7
        weapons = $weapons.Count
        records = $linkAudit.records
        linksChecked = $linkAudit.linksChecked
        unresolvedLinks = $linkAudit.unresolved.Count
        allTwoHanded = $true
        dragonboneRemoved = $true
        spriggitRoundTripPassed = $true
    }
    assets = [ordered]@{
        meshes = $meshes.Count
        allSseStream100 = $true
        allReloadedWithoutUnknownBlocks = $true
        textures = $textures.Count
        ddsFormats = $ddsFormats
        customTextureReferencesResolved = $true
    }
}
$reportPath = Join-Path $privatePort 'audit-report.json'
[IO.File]::WriteAllText(
    $reportPath,
    ($report | ConvertTo-Json -Depth 8),
    [Text.UTF8Encoding]::new($false)
)
$report
