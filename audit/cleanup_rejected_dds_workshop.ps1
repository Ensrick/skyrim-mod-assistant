[CmdletBinding()]
param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$auditRoot = 'C:\Users\danjo\source\repos\_audit\'
$downloadRoot = 'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\'
$ledgerPath = 'C:\Users\danjo\source\repos\skyrim-mod-assistant\records\installed-mods.json'
$targets = @(
    'C:\Users\danjo\source\repos\_audit\dds-workshop-npc-replacer-0.3',
    'C:\Users\danjo\source\repos\_audit\dds-workshop-npc-replacer-0.3-ae-port-stage',
    'C:\Users\danjo\source\repos\_audit\dds-workshop-npc-replacer-0.3-plugin-se-test',
    'C:\Users\danjo\source\repos\_audit\dds-workshop-npc-replacer-0.3-spriggit-le',
    'C:\Users\danjo\source\repos\_audit\dds-workshop-npc-replacer-0.3-spriggit-se-port',
    'C:\Users\danjo\source\repos\_audit\dds-workshop-eyesmod2-required-2k',
    'C:\Users\danjo\source\repos\_audit\eyesmod2-base-se-reference',
    'C:\Users\danjo\source\repos\_audit\eyesmod2-base-le-reference',
    'C:\Users\danjo\source\repos\_audit\dds-eye-shader-probe',
    'C:\Users\danjo\source\repos\_audit\alt2-cbbe-balanced-readme',
    'C:\Users\danjo\source\repos\_audit\dds-workshop-npc-replacer-0.55',
    'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\NPC_Mod_latest_build_0.55_August2022.7z',
    'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\NPC_Mod_build_0.5_July2022.7z',
    'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\NPC_Mod_build_0.3.7z',
    'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\ALT2_CBBE_2K-4K_Balanced_032022.7z',
    'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\6817-628151.7z',
    'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\downloads\Eyes_Mod_2_2K_oct2021.7z'
)

$ledger = Get-Content -LiteralPath $ledgerPath -Raw
$found = [Collections.Generic.List[object]]::new()
foreach ($path in $targets) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $item = Get-Item -LiteralPath $path -Force
    $resolved = [IO.Path]::GetFullPath($item.FullName)
    $insideKnownRoot = $resolved.StartsWith($auditRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $resolved.StartsWith($downloadRoot, [StringComparison]::OrdinalIgnoreCase)
    if (-not $insideKnownRoot) { throw "Refusing path outside cleanup roots: $resolved" }
    if (-not $item.PSIsContainer -and $ledger.Contains($item.Name)) {
        throw "Refusing archive named in installed-mods ledger: $($item.Name)"
    }
    $bytes = if ($item.PSIsContainer) {
        [int64]((Get-ChildItem -LiteralPath $resolved -Recurse -File -Force |
            Measure-Object -Property Length -Sum).Sum)
    }
    else { [int64]$item.Length }
    $found.Add([pscustomobject]@{ Path = $resolved; Bytes = $bytes })
}

$total = [int64](($found | Measure-Object -Property Bytes -Sum).Sum)
$result = [ordered]@{
    mode = if ($Apply) { 'apply' } else { 'dry-run' }
    scope = 'rejected DDS Workshop trial artifacts only'
    targets = $found.Count
    logicalBytes = $total
    logicalGiB = [math]::Round($total / 1GB, 3)
    installedModsTouched = $false
}

if ($Apply) {
    foreach ($target in $found) {
        Remove-Item -LiteralPath $target.Path -Recurse -Force
    }
    $result.removed = $found.Count
}

[pscustomobject]$result | ConvertTo-Json
