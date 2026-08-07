#requires -Version 7.0
[CmdletBinding()]
param(
    [string] $WorkRoot = (Join-Path $PSScriptRoot '..\..\work\lost-longswords'),
    [string] $OutputRoot = (Join-Path $PSScriptRoot '..\..\work\lost-longswords\private-port'),
    [switch] $Clean
)

$ErrorActionPreference = 'Stop'
$work = [System.IO.Path]::GetFullPath($WorkRoot)
$output = [System.IO.Path]::GetFullPath($OutputRoot)
if (-not $output.StartsWith($work + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Output must remain under the Lost LongSwords work directory: $work"
}
if (Test-Path -LiteralPath $output) {
    if (-not $Clean) {
        throw "Output already exists. Pass -Clean to replace only this generated directory: $output"
    }
    Remove-Item -LiteralPath $output -Recurse -Force
}

$pluginSource = Join-Path $output 'plugin-source'
$modRoot = Join-Path $output 'mod'
$validationSource = Join-Path $output 'validation-source'
New-Item -ItemType Directory -Path $pluginSource, $modRoot | Out-Null

$sourceYaml = Join-Path $work 'comparison\original-yaml'
$excludedRecords = [System.Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
@(
    'Weapons\DragonboneLongSword - 009F46_LostLongSwords.esp.yaml',
    'Statics\1stPersonDragonboneLongSword - 009F45_LostLongSwords.esp.yaml',
    'ConstructibleObjects\RecipeArmorDragonboneLongsword - 009F47_LostLongSwords.esp.yaml',
    'ConstructibleObjects\TemperWeaponDragonboneLongSword - 009F48_LostLongSwords.esp.yaml'
) | ForEach-Object { [void] $excludedRecords.Add($_) }

foreach ($file in Get-ChildItem -LiteralPath $sourceYaml -Recurse -File) {
    $relative = [System.IO.Path]::GetRelativePath($sourceYaml, $file.FullName)
    if ($excludedRecords.Contains($relative)) { continue }
    $destination = Join-Path $pluginSource $relative
    New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $destination
}

# Spriggit preserves the source form versions verbatim. These changes perform the
# plugin-side LE-to-SE conversion that the 2024 Nexus upload did not perform.
foreach ($file in Get-ChildItem -LiteralPath $pluginSource -Recurse -Filter *.yaml -File) {
    $text = [System.IO.File]::ReadAllText($file.FullName)
    $text = $text.Replace('FormVersion: 40', 'FormVersion: 44')
    if ($file.Name -eq 'RecordData.yaml') {
        $text = $text.Replace('    Version: 0.94', '    Version: 1.7')
    }
    [System.IO.File]::WriteAllText($file.FullName, $text, [Text.UTF8Encoding]::new($false))
}

function Copy-AssetTreeExceptDragon {
    param([string] $Source, [string] $Destination)
    $dragonRoot = [System.IO.Path]::GetFullPath((Join-Path $Source 'weapons\dragon'))
    foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File) {
        if ($file.FullName.StartsWith($dragonRoot + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        $relative = [System.IO.Path]::GetRelativePath($Source, $file.FullName)
        $target = Join-Path $Destination $relative
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $target
    }
}

Copy-AssetTreeExceptDragon `
    -Source (Join-Path $work 'converted-meshes') `
    -Destination (Join-Path $modRoot 'meshes')
Copy-AssetTreeExceptDragon `
    -Source (Join-Path $work 'original-bsa\textures') `
    -Destination (Join-Path $modRoot 'textures')

$remainingDragon = @(
    Get-ChildItem -LiteralPath $pluginSource, $modRoot -Recurse -File |
        Where-Object {
            $_.FullName -match '(?i)dragonbone|[\\/]weapons[\\/]dragon[\\/]'
        }
)
if ($remainingDragon.Count -ne 0) {
    throw "Dragonbone assets or records remain: $($remainingDragon.FullName -join ', ')"
}
if (rg -l -i 'dragonbone|009F45|009F46|009F47|009F48' $pluginSource) {
    throw 'A Dragonbone text reference remains in the staged plugin source.'
}

[pscustomobject]@{
    PluginSource = $pluginSource
    ModRoot = $modRoot
    ValidationSource = $validationSource
    Meshes = @(Get-ChildItem (Join-Path $modRoot 'meshes') -Recurse -Filter *.nif -File).Count
    Textures = @(Get-ChildItem (Join-Path $modRoot 'textures') -Recurse -Filter *.dds -File).Count
}
