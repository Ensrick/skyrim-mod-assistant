#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$PluginPath = "$PSScriptRoot\artifacts\WeaponBalancePatch.esp",
    [string]$RecordTool = 'C:\Users\danjo\source\repos\skyrim-tools-builds\skyrim-record-cli-1f3c8d9\skyrim-record-cli.exe'
)

$ErrorActionPreference = 'Stop'

foreach ($required in @($PluginPath, $RecordTool)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file does not exist: $required"
    }
}

$pluginInfo = (& $RecordTool plugin-info $PluginPath) | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    throw "Plugin metadata inspection failed with exit code $LASTEXITCODE"
}
$recordTypeNames = @($pluginInfo.recordTypes.PSObject.Properties.Name)
if ($recordTypeNames.Count -ne 1 -or $recordTypeNames[0] -notmatch '^Weapon') {
    throw "Patch contains record types other than Weapon."
}

$targets = @{
    '01E713:Skyrim.esm' = 1.25
    '01E711:Skyrim.esm' = 1.0
    '01E712:Skyrim.esm' = 0.9375
    '01E714:Skyrim.esm' = 15.0 / 17.0
    '06D931:Skyrim.esm' = 0.8
    '06D932:Skyrim.esm' = 20.0 / 26.0
    '06D930:Skyrim.esm' = 20.0 / 28.0
}
$counts = @{}
foreach ($keyword in $targets.Keys) { $counts[$keyword] = 0 }
$fallbackTargets = @{
    'OneHandDagger' = 1.25
    'OneHandSword' = 1.0
    'OneHandAxe' = 0.9375
    'OneHandMace' = 15.0 / 17.0
    'TwoHandSword' = 0.8
}

$weapons = @(& $RecordTool weapons $PluginPath | ForEach-Object { $_ | ConvertFrom-Json })
if ($LASTEXITCODE -ne 0) {
    throw "Weapon inspection failed with exit code $LASTEXITCODE"
}
if ($weapons.Count -eq 0) {
    throw 'Patch contains no weapon overrides.'
}

foreach ($weapon in $weapons) {
    $classes = @($weapon.keywords | Where-Object {
        $null -ne $_ -and $targets.ContainsKey([string]$_)
    })
    if ($classes.Count -gt 1) {
        throw "Weapon $($weapon.formKey) has multiple standard class keywords."
    }
    if ($classes.Count -eq 1) {
        $keyword = $classes[0]
        $expected = [double]$targets[$keyword]
        $counts[$keyword]++
    } elseif ($fallbackTargets.ContainsKey([string]$weapon.animationType)) {
        $expected = [double]$fallbackTargets[[string]$weapon.animationType]
    } else {
        throw "Weapon $($weapon.formKey) has neither one standard class keyword nor an unambiguous animation fallback."
    }
    if ([Math]::Abs([double]$weapon.speed - $expected) -gt 0.0001) {
        throw "Weapon $($weapon.formKey) speed $($weapon.speed) != expected $expected."
    }
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PluginPath).Hash
Write-Host "PASS: $($weapons.Count) weapon overrides, all class speeds exact; Weapon records only."
foreach ($keyword in $targets.Keys | Sort-Object) {
    Write-Host "  $keyword = $($counts[$keyword])"
}
Write-Host "Masters: $($pluginInfo.masters.Count)"
Write-Host "SHA256: $hash"
