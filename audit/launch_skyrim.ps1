# One-shot Skyrim launcher: claim, scrub, sync INIs, seed plugin activation,
# cycle Steam, launch, verify.
# Born 2026-08-25: 1.7.99 "Creations" runtime reads LocalAppData Plugins.txt
# which MO2 2.5.2 does not virtualize; Steam wedges after collisions/kills.
# Hardened 2026-09-01 (#103, #141, #143):
#   [0] refuses to run under another owner's instance claim (audit/claim.py)
#   [0] scrubs SKYRIM_LAUNCH_PROBE_* / SKYRIM_MENU_PILOT_* out of the
#       environment BEFORE Steam is restarted. Steam is a long-lived
#       environment reservoir: on 2026-09-01 a restarted Steam inherited the
#       harness's autoload variable and every later launch, including the
#       user's own, loaded a broken save 1.5 s after the menu. Those variables
#       now reach only the game process this script spawns directly (-Direct).
#   [2] copies the profile's skyrim.ini/skyrimprefs.ini over the Documents pair
#       when they differ (dated .bak of the Documents copy), so a launch that
#       reads Documents still reads the profile's values (#143 interim).
#   [5] -Direct spawns the game through MO2Headless run -> ModOrganizer.exe
#       headless-run -> skse64_loader.exe with the harness variables set on
#       that child only. Without -Direct the Steam chain is used and no
#       harness variable can reach the game (by design).
#   #227's disposable lane supplies -ProfileName, -NoIniSync, -NoSteamCycle
#       and -RefuseExistingProcesses. It runs the script itself on a hidden
#       desktop, never edits Default/Documents, and fails instead of killing a
#       process that appeared in the preflight/launch gap.
param(
    [int]$WaitSeconds = 200,
    [ValidatePattern('^[^\\/:*?"<>|]+$')]
    [string]$ProfileName = 'Default',
    [switch]$AllowInteractiveDesktop,
    [switch]$Direct,
    [switch]$NoIniSync,
    [switch]$NoSteamCycle,
    [switch]$RefuseExistingProcesses,
    [switch]$IgnoreClaim
)
$ErrorActionPreference = 'SilentlyContinue'

if (-not $AllowInteractiveDesktop) {
    Write-Error 'Blocked: autonomous Skyrim launches may not use the active desktop. Pass -AllowInteractiveDesktop only after the user explicitly authorizes an interactive launch.'
    exit 64
}

$G = "C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition"
$INSTANCE = "C:\Users\danjo\source\repos\mo2-instances\skyrim-se"
$PROF = Join-Path $INSTANCE ("profiles\" + $ProfileName)
$DOCSINI = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Skyrim Special Edition'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

Write-Host "[0] instance claim"
$claimArgs = @('check')
if ($env:SKYRIM_CLAIM_OWNER) { $claimArgs += @('--owner', $env:SKYRIM_CLAIM_OWNER) }
$claimOut = (& py -3 "$PSScriptRoot\claim.py" @claimArgs 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    if ($IgnoreClaim) {
        Write-Host "    WARNING launching under another owner's claim (-IgnoreClaim): $claimOut"
    } else {
        Write-Host "[ABORT] $claimOut - acquire it first (py -3 audit/claim.py acquire --owner NAME --purpose ...) or wait"
        exit 75
    }
} else {
    Write-Host "    $claimOut"
}

# Harvest the harness variables, then REMOVE them from this process so the
# Steam restart below cannot inherit them. They are re-applied to the direct
# child only. SKSE_AUTOMATION_SILENT_UI stays: it only suppresses plugin popups
# (log instead of modal UI) and is wanted on every launch, user's included.
$harness = @{}
foreach ($v in Get-ChildItem Env: | Where-Object {
        $_.Name -like 'SKYRIM_LAUNCH_PROBE_*' -or $_.Name -like 'SKYRIM_MENU_PILOT_*' -or
        $_.Name -eq 'SKYRIM_CLAIM_OWNER' }) {
    $harness[$v.Name] = $v.Value
    Remove-Item -LiteralPath "Env:\$($v.Name)"
}
$env:SKSE_AUTOMATION_SILENT_UI = '1'
Write-Host ("    scrubbed {0} harness var(s) from the Steam environment: {1}" -f $harness.Count,
    $(if ($harness.Count) { ($harness.Keys | Sort-Object) -join ', ' } else { 'none present' }))

Write-Host "[1] launch-chain ownership"
$existing = @(Get-Process -Name SkyrimSE, ModOrganizer, skse64_loader, MO2Headless -ErrorAction SilentlyContinue)
if ($RefuseExistingProcesses -and $existing.Count -gt 0) {
    Write-Host ("[ABORT] existing launch-chain process(es): {0}; refusing to kill or launch" -f
        (($existing | ForEach-Object { "{0}:{1}" -f $_.ProcessName, $_.Id }) -join ', '))
    exit 75
}
if (-not $RefuseExistingProcesses) {
    Stop-Process -Name SkyrimSE, ModOrganizer, skse64_loader -Force
}
$t = 15
while ((Get-Process MO2Headless) -and $t -gt 0) { Start-Sleep -Seconds 1; $t -= 1 }   # a direct-chain wrapper exits by itself once the game is gone
if (Get-Process MO2Headless -ErrorAction SilentlyContinue) {
    if ($RefuseExistingProcesses) {
        Write-Host "[ABORT] MO2Headless.exe remained running; refusing to overlap it"
        exit 75
    }
    Write-Host "    WARNING MO2Headless.exe still running (a mutation in progress?) - not killing it"
}
Start-Sleep -Seconds 3

Write-Host "[2] profile INIs -> Documents (profile is the source of truth, #143)"
$profileSettingsPath = Join-Path $PROF 'settings.ini'
if (-not (Test-Path -LiteralPath $profileSettingsPath -PathType Leaf)) {
    Write-Host "[ABORT] profile '$ProfileName' does not exist or has no settings.ini"
    exit 66
}
$ownerLine = Select-String -Path $profileSettingsPath -Pattern '^LocalSettings\s*=\s*(\w+)' | ForEach-Object { $_.Matches[0].Groups[1].Value }
Write-Host ("    settings.ini LocalSettings={0} ({1})" -f $ownerLine,
    $(if ("$ownerLine" -ieq 'true') { 'MO2 maps the Documents INI paths onto the profile copies for its launches' } else { 'the game reads the Documents copies; the sync below is what keeps them right' }))
if ($NoIniSync) {
    Write-Host "    sync skipped (-NoIniSync)"
} else {
    foreach ($pair in @(@('skyrim.ini', 'Skyrim.ini'), @('skyrimprefs.ini', 'SkyrimPrefs.ini'), @('skyrimcustom.ini', 'SkyrimCustom.ini'))) {
        $src = Join-Path $PROF $pair[0]
        $dst = Join-Path $DOCSINI $pair[1]
        if (-not (Test-Path -LiteralPath $src)) { continue }
        $same = (Test-Path -LiteralPath $dst) -and
            ((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash)
        if ($same) { Write-Host ("    {0}: identical" -f $pair[1]); continue }
        if (Test-Path -LiteralPath $dst) {
            Copy-Item -LiteralPath $dst -Destination "$dst.bak.v$stamp-presync" -Force
        }
        Copy-Item -LiteralPath $src -Destination $dst -Force
        Write-Host ("    {0}: DIFFERED - profile copy written over Documents (old copy kept as {0}.bak.v{1}-presync)" -f $pair[1], $stamp)
    }
}

Write-Host "[3] seeding game-side Plugins.txt from profile"
$stars = Get-Content "$PROF\plugins.txt" | Where-Object { $_.StartsWith('*') }
if (@($stars).Count -eq 0) {
    # a failed read must never seed an empty file - that deactivates every plugin
    Write-Host "[ABORT] profile plugins.txt unreadable or has no active plugins - not seeding"
    exit 1
}
$hdr = "# This file is used by Skyrim to keep track of your downloaded content."
[IO.File]::WriteAllLines("$env:LOCALAPPDATA\Skyrim Special Edition\Plugins.txt", @($hdr) + $stars)
Write-Host ("    {0} plugins seeded" -f @($stars).Count)

Write-Host "[4] Steam readiness"
if ($NoSteamCycle) {
    if (-not (Get-Process steam -ErrorAction SilentlyContinue)) {
        Write-Host "[ABORT] Steam is not already running; -NoSteamCycle forbids starting it"
        exit 75
    }
    Write-Host "    cycle skipped; existing Steam left untouched"
} else {
    & "C:\Program Files (x86)\Steam\steam.exe" -shutdown
    $t = 45
    while ((Get-Process steam) -and $t -gt 0) { Start-Sleep -Seconds 3; $t -= 3 }
    if (Get-Process steam) { Stop-Process -Name steam, steamwebhelper -Force; Start-Sleep -Seconds 3 }
    Start-Process "C:\Program Files (x86)\Steam\steam.exe" -ArgumentList '-silent'
    $t = 90
    while (-not (Get-Process steamwebhelper) -and $t -gt 0) { Start-Sleep -Seconds 3; $t -= 3 }
    Start-Sleep -Seconds 12
    Write-Host "    steam ready"
}

if ($Direct) {
    Write-Host "[5] launching DIRECT: MO2Headless run -> headless-run -> skse64_loader (harness env on this child only)"
    $controller = "$INSTANCE\MO2Headless.exe"
    $loader = "$G\skse64_loader.exe"
    foreach ($required in @($controller, "$INSTANCE\ModOrganizer.exe", $loader)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { Write-Host "[ABORT] missing $required"; exit 66 }
    }
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $controller
    $psi.WorkingDirectory = $INSTANCE
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    foreach ($a in @('--root', $INSTANCE, '-p', $ProfileName, '--timeout', '0', 'run', $loader, '--cwd', $G)) {
        [void] $psi.ArgumentList.Add($a)
    }
    foreach ($k in $harness.Keys) { $psi.Environment[$k] = $harness[$k] }
    $psi.Environment['SKSE_AUTOMATION_SILENT_UI'] = '1'
    $wrapper = [System.Diagnostics.Process]::Start($psi)
    if (-not $wrapper) { Write-Host "[ABORT] could not start MO2Headless run"; exit 74 }
    Write-Host ("    wrapper pid {0}; env on child: {1}" -f $wrapper.Id, (($harness.Keys | Sort-Object) -join ', '))
} else {
    Write-Host "[5] launching via Steam (steam://rungameid/489830; no harness variable reaches the game on this chain)"
    Start-Process "steam://rungameid/489830"
}
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
Write-Host ("[6] VERDICT: {0} (uptime {1}s, {2}MB)" -f $verdict, $best, $mem)
exit $(if ($verdict -eq 'STABLE') { 0 } else { 1 })
