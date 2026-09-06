<#
.SYNOPSIS
Build a user-local, one-byte Bruma iron helmet decapitation repair (#242).
.DESCRIPTION
Original MIT recipe, not permission to redistribute the generated vendor mesh.
Uses the existing HousecarlCore/NiflySharp parser; never launches a GUI or game.
Only the exact reviewed input hash is accepted. No ESP or equipment slots change.
The mesh's BSDismemberSkinInstance body-part ushort at offset586 is 31; set131.
All 99,650 other bytes, including partition flags and every geometry byte, remain.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $Instance,
    [Parameter(Mandatory)] [string] $GameData,
    [Parameter(Mandatory)] [string] $ToolBin,
    [Parameter(Mandatory)] [string] $Output
)
$ErrorActionPreference = 'Stop'
$relative = 'meshes/bscyrodiil/armor/iron/cyrironhelmet.nif'
$inputHash = '892AED580ACF254840E026CC0BA1919D29594C65E3448D69EE9290F16AC4968F'
$expectedLength = 99651
$offset = 586

function Get-PhysicalPath([string] $Path) {
    # Resolve each existing component so a junction cannot disguise a live target.
    $full = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetPathRoot($full)
    $current = $root
    foreach ($part in $full.Substring($root.Length).Split([char[]]@('\', '/'), [StringSplitOptions]::RemoveEmptyEntries)) {
        $current = Join-Path $current $part
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                $resolved = $item.ResolveLinkTarget($true)
                if ($null -eq $resolved) { throw "Cannot resolve reparse point: $current" }
                $current = $resolved.FullName
            }
        }
    }
    return [IO.Path]::GetFullPath($current).TrimEnd('\', '/')
}
function Get-Hash([byte[]] $Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

$destination = Get-PhysicalPath $Output
foreach ($protected in @($Instance, $GameData, $ToolBin)) {
    $boundary = Get-PhysicalPath $protected
    if ($destination.Equals($boundary, [StringComparison]::OrdinalIgnoreCase) -or
        $destination.StartsWith($boundary + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Output must be outside the live instance, game Data and tool directories'
    }
}
if (Test-Path -LiteralPath $destination) { throw 'Use a new output directory; existing output is never replaced' }

foreach ($name in @('NiflySharp.dll', 'Mutagen.Bethesda.Kernel.dll', 'Mutagen.Bethesda.Core.dll', 'Mutagen.Bethesda.Skyrim.dll', 'housecarl-core.dll')) {
    [Reflection.Assembly]::LoadFrom((Join-Path $ToolBin $name)) | Out-Null
}
$profile = Join-Path $Instance 'profiles/Default'
$mods = Join-Path $Instance 'mods'
$overwrite = Join-Path $Instance 'overwrite'
$warnings = [Collections.Generic.List[string]]::new()
$composition = [HousecarlCore.Mo2LoadOrder]::ReadComposition($profile, $warnings)
$discovery = [HousecarlCore.ArchiveDiscovery]::Discover($profile, $mods, $GameData, $overwrite, (Split-Path -Parent $GameData))
if ($warnings.Count -or $discovery.Warnings.Count) { throw 'Incomplete profile/archive discovery' }
$resolver = [HousecarlCore.AssetResolver]::Build($overwrite, $mods, $GameData, $composition.EnabledMods, $discovery.Archives)
try {
    if ($resolver.ReadIncomplete) { throw 'Incomplete BSA table scan' }
    $resolution = $resolver.ResolveForPlacement($relative)
    if ($resolution.ReadIncomplete -or $resolution.Sources.Count -eq 0) { throw 'Winning iron helmet mesh is unresolved' }
    $winner = $resolution.Sources[0]
    $read = [HousecarlCore.AssetResolver]::ReadPlacementSource($winner)
    if ($null -ne $read.Item2) { throw "Cannot read winning mesh: $($read.Item2)" }
    [byte[]] $original = $read.Item1
} finally { $resolver.Dispose() }
if ((Get-Hash $original) -ne $inputHash -or $original.Length -ne $expectedLength) {
    throw 'Winning helmet differs from the reviewed Bruma asset; re-audit before applying this recipe'
}
$before = [HousecarlCore.NifService]::Inspect($original)
if ($before.Error -or $null -eq $before.Inspect -or -not $before.Inspect.IsSkyrimSE) { throw 'Input NIF failed independent parser validation' }
$shape = @($before.Inspect.Shapes)
if ($shape.Count -ne 1 -or $shape[0].Name -cne 'INV.00' -or $shape[0].Partitions.Count -ne 1 -or
    $shape[0].Partitions[0].BodyPartId -ne 31 -or $shape[0].Partitions[0].PartFlags -ne 257 -or
    $shape[0].Bones.Count -ne 1 -or $shape[0].Bones[0] -cne 'NPC Head [Head]') {
    throw 'Input shape/partition/bone semantics differ from the reviewed asset'
}
# Structurally audited original block2 starts at560: one bone and one partition.
# Its 28 bytes end with uint16 PartFlags257 at584 and uint16 BodyPart31 at586.
if ([BitConverter]::ToUInt32($original, 572) -ne 1 -or
    [BitConverter]::ToUInt32($original, 580) -ne 1 -or
    [BitConverter]::ToUInt16($original, 584) -ne 257 -or
    [BitConverter]::ToUInt16($original, $offset) -ne 31) { throw 'Expected dismember block framing is absent' }
[byte[]] $patched = $original.Clone()
$patched[$offset] = 131
if ($patched.Length -ne $original.Length) { throw 'Unexpected file-size change' }
for ($i = 0; $i -lt $original.Length; $i++) {
    if ($i -ne $offset -and $patched[$i] -ne $original[$i]) { throw "Unrelated byte changed at $i" }
}
$after = [HousecarlCore.NifService]::Inspect($patched)
if ($after.Error -or $null -eq $after.Inspect -or -not $after.Inspect.IsSkyrimSE -or
    $after.Inspect.Shapes.Count -ne 1 -or $after.Inspect.Shapes[0].Name -cne 'INV.00' -or
    $after.Inspect.Shapes[0].Partitions.Count -ne 1 -or $after.Inspect.Shapes[0].Partitions[0].BodyPartId -ne 131 -or
    $after.Inspect.Shapes[0].Partitions[0].PartFlags -ne 257) { throw 'Output partition semantic read-back failed' }
$beforeModel = $before.Inspect | ConvertTo-Json -Depth 100 | ConvertFrom-Json -Depth 100
$afterModel = $after.Inspect | ConvertTo-Json -Depth 100 | ConvertFrom-Json -Depth 100
$afterModel.Shapes[0].Partitions[0].BodyPartId = 31
$afterModel.Shapes[0].Partitions[0].BodyPartName = 'SBP_31_HAIR'
if (($beforeModel | ConvertTo-Json -Depth 100 -Compress) -cne ($afterModel | ConvertTo-Json -Depth 100 -Compress)) {
    throw 'Independent semantic inspection found another change'
}

$manifest = [ordered]@{
    component = 'Ensrick - Bruma Iron Helmet Decapitation Repair'
    version = '0.1.0'
    issue = 'https://github.com/Ensrick/skyrim-mod-assistant/issues/242'
    distribution = 'recipe'
    redistributeGeneratedArchive = $false
    sourceRecipe = 'audit/repair_bruma_iron_helmet.ps1'
    sourceAsset = $relative
    inputSha256 = $inputHash
    outputSha256 = Get-Hash $patched
    fileSize = $expectedLength
    byteChanges = @([ordered]@{ offset = $offset; before = 31; after = 131 })
    semanticChange = 'INV.00 BSDismemberSkinInstance partition0 BodyPart31 to131; flags257 unchanged'
    verification = 'STATIC PASS; gameplay decapitation acceptance still required'
    vendorAssetsModifiedInPlace = $false
}
$mod = Join-Path $destination 'mod'
$meshOutput = Join-Path $mod $relative
[IO.Directory]::CreateDirectory((Split-Path -Parent $meshOutput)) | Out-Null
[IO.File]::WriteAllBytes($meshOutput, $patched)
$manifestPath = Join-Path $mod 'EnsrickBrumaIronHelmetRepair.manifest.json'
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 20) + "`n", [Text.UTF8Encoding]::new($false))
$package = Join-Path $destination 'Ensrick-Bruma-Iron-Helmet-Decapitation-Repair-0.1.0-USER-LOCAL.zip'
$archive = [IO.Compression.ZipFile]::Open($package, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in @(Get-ChildItem -LiteralPath $mod -File -Recurse | Sort-Object FullName)) {
        $entry = $archive.CreateEntry([IO.Path]::GetRelativePath($mod, $file.FullName).Replace('\', '/'), [IO.Compression.CompressionLevel]::Optimal)
        $entry.LastWriteTime = [DateTimeOffset]::new(2026, 9, 6, 0, 0, 0, [TimeSpan]::Zero)
        $stream = $entry.Open()
        try { $bytes = [IO.File]::ReadAllBytes($file.FullName); $stream.Write($bytes, 0, $bytes.Length) }
        finally { $stream.Dispose() }
    }
} finally { $archive.Dispose() }
$receipt = [ordered]@{ package = $package; packageSha256 = (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash;
    inputProvider = $winner; manifest = $manifest;
    parserSha256 = (Get-FileHash (Join-Path $ToolBin 'housecarl-core.dll') -Algorithm SHA256).Hash;
    niflySha256 = (Get-FileHash (Join-Path $ToolBin 'NiflySharp.dll') -Algorithm SHA256).Hash }
[IO.File]::WriteAllText((Join-Path $destination 'receipt.json'), ($receipt | ConvertTo-Json -Depth 30) + "`n", [Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 30
