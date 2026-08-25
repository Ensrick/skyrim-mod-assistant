# One-shot Skyrim launcher: seed plugin activation, cycle Steam, launch, verify.
# Born 2026-08-25: 1.7.99 "Creations" runtime reads LocalAppData Plugins.txt
# which MO2 2.5.2 does not virtualize; Steam wedges after collisions/kills.
param([int]$WaitSeconds = 200)
$ErrorActionPreference = 'SilentlyContinue'
$G = "C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition"
$PROF = "C:\Users\danjo\source\repos\mo2-instances\skyrim-se\profiles\Default"

Write-Host "[1] closing stale chain"
Stop-Process -Name SkyrimSE, ModOrganizer, skse64_loader -Force
Start-Sleep -Seconds 3

Write-Host "[2] seeding game-side Plugins.txt from profile"
$stars = Get-Content "$PROF\plugins.txt" | Where-Object { $_.StartsWith('*') }
$hdr = "# This file is used by Skyrim to keep track of your downloaded content."
Set-Content "$env:LOCALAPPDATA\Skyrim Special Edition\Plugins.txt" -Value (@($hdr) + $stars) -Encoding utf8
Write-Host ("    {0} plugins seeded" -f @($stars).Count)

Write-Host "[3] cycling Steam (clears wedged launcher state)"
& "$env:ProgramFiles(x86)\Steam\steam.exe" -shutdown 2>$null
& "C:\Program Files (x86)\Steam\steam.exe" -shutdown
$t = 45
while ((Get-Process steam) -and $t -gt 0) { Start-Sleep -Seconds 3; $t -= 3 }
if (Get-Process steam) { Stop-Process -Name steam, steamwebhelper -Force; Start-Sleep -Seconds 3 }
Start-Process "C:\Program Files (x86)\Steam\steam.exe" -ArgumentList '-silent'
$t = 90
while (-not (Get-Process steamwebhelper) -and $t -gt 0) { Start-Sleep -Seconds 3; $t -= 3 }
Start-Sleep -Seconds 12
Write-Host "    steam ready"

Write-Host "[4] launching"
Start-Process "steam://rungameid/489830"
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$best = 0; $mem = 0; $verdict = "no process appeared"
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 8
    $p = Get-Process SkyrimSE | Sort-Object StartTime | Select-Object -Last 1
    if ($p) {
        $best = [int]((Get-Date) - $p.StartTime).TotalSeconds
        $mem = [int]($p.WorkingSet64 / 1MB)
        $verdict = "running"
        if ($best -gt 75 -and $mem -gt 1500) { $verdict = "STABLE"; break }
    }
    elseif ($best -gt 0) { $verdict = "died at ${best}s"; break }
}
Write-Host ("[5] VERDICT: {0} (uptime {1}s, {2}MB)" -f $verdict, $best, $mem)
exit $(if ($verdict -eq 'STABLE') { 0 } else { 1 })
