[CmdletBinding()]
param(
    [string]$PluginPath = "$PSScriptRoot\package\KatanaTwoHandedPatch.esp",
    [string]$RecordTool = 'skyrim-record-cli.exe'
)

$ErrorActionPreference = 'Stop'

if (-not [System.IO.Path]::IsPathFullyQualified($RecordTool)) {
    $resolvedRecordTool = Get-Command $RecordTool -CommandType Application -ErrorAction SilentlyContinue
    if ($resolvedRecordTool) {
        $RecordTool = $resolvedRecordTool.Source
    }
}

foreach ($requiredPath in @($PluginPath, $RecordTool)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required file does not exist: $requiredPath"
    }
}

$expectedDamage = @{
    '03AEB9:Skyrim.esm' = 16
    '0C1989:Skyrim.esm' = 16
    '0F1AC1:Skyrim.esm' = 16
    '0F71CD:Skyrim.esm' = 16
    '0F71CE:Skyrim.esm' = 17
    '0F71CF:Skyrim.esm' = 18
    '0F71D0:Skyrim.esm' = 20
    '04A38F:Skyrim.esm' = 16
    '0EA29C:Skyrim.esm' = 18
    '014555:Dawnguard.esm' = 16
    '0067CF:Dawnguard.esm' = 14
    '000D61:ccBGSSSE005-Goldbrand.esl' = 21
    '000C92:ccBGSSSE013-Dawnfang.esl' = 20
    '000D63:ccBGSSSE013-Dawnfang.esl' = 20
}

$jsonLines = & $RecordTool weapons $PluginPath
if ($LASTEXITCODE -ne 0) {
    throw "Record inspection failed with exit code $LASTEXITCODE"
}

$weapons = @($jsonLines | ForEach-Object { $_ | ConvertFrom-Json })
if ($weapons.Count -ne $expectedDamage.Count) {
    throw "Expected $($expectedDamage.Count) weapon overrides, found $($weapons.Count)"
}

foreach ($weapon in $weapons) {
    if (-not $expectedDamage.ContainsKey($weapon.formKey)) {
        throw "Unexpected weapon override: $($weapon.formKey) ($($weapon.editorId))"
    }

    $checks = @{
        damage = [int]$weapon.damage -eq $expectedDamage[$weapon.formKey]
        speed = [Math]::Abs([double]$weapon.speed - 0.85) -lt 0.0001
        reach = [Math]::Abs([double]$weapon.reach - 1.20) -lt 0.0001
        stagger = [Math]::Abs([double]$weapon.stagger - 0.90) -lt 0.0001
        animation = $weapon.animationType -eq 'TwoHandSword'
        skill = $weapon.skill -eq 'TwoHanded'
        equipment = $weapon.equipmentType -eq '013F45:Skyrim.esm'
        critical = [int]$weapon.criticalDamage -eq [Math]::Floor([int]$weapon.damage / 2)
        greatswordKeyword = $weapon.keywords -contains '06D931:Skyrim.esm'
        katanaKeyword = $weapon.keywords -contains '000800:KatanaTwoHandedPatch.esp'
        removedSwordKeyword = $weapon.keywords -notcontains '01E711:Skyrim.esm'
    }

    $failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object Key)
    if ($failed.Count -gt 0) {
        throw "Audit failed for $($weapon.formKey) ($($weapon.editorId)): $($failed -join ', ')"
    }
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PluginPath).Hash
Write-Host "PASS: 14/14 katana overrides have the expected two-handed profile."
Write-Host "SHA256: $hash"
