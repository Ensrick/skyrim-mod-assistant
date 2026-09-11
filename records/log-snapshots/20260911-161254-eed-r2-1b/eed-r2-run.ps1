# EED R2 verification orchestrator (#269): one isolated private-desktop launch,
# fresh Skyrim Unbound character, the plugin's own self-test, a 180 s soak, a
# Journal quit, and an archive of every log. Refuses to launch unless the
# installed DLL is byte-identical to the receipt's clean-build hash, the load
# order verifies CLEAN (#253), the claim is held, and no game is running.
#
# Run as three foreground phases so no single call exceeds a tool timeout:
#   pwsh -NoProfile -File records-work/eed-r2-run.ps1 -Attempt 1 -Phase launch   (gates, launch, main menu, character, Begin)
#   pwsh -NoProfile -File records-work/eed-r2-run.ps1 -Attempt 1 -Phase test     (self-test summary, inventory dump)
#   pwsh -NoProfile -File records-work/eed-r2-run.ps1 -Attempt 1 -Phase soak     (180 s soak, quit, archive, verdict inputs)
# State between phases lives in records-work/eed-r2-state-<Attempt>.json.
#
# Every MenuPilot step is one call of records-work/eed-r2-ui.ps1 and is echoed
# here with its readback. Stops at the first step whose readback is wrong.
param(
  [Parameter(Mandatory)][string]$Attempt,
  [Parameter(Mandatory)][ValidateSet('launch','test','soak')][string]$Phase,
  [string]$ClaimOwner = 'fable/eed-r2',
  [string]$Receipt = 'records/source-builds/ensrick-equipment-display-r2.json',
  [string]$Stamp = (Get-Date -Format 'yyyyMMdd'),
  [int]$WaitSeconds = 900,
  [int]$SoakSeconds = 180,
  [int]$SelfTestBudgetSeconds = 180
)
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\danjo\source\repos\skyrim-mod-assistant'
$py = 'C:\Users\danjo\AppData\Local\Programs\Python\Python313\python.exe'
$instance = 'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
$installedDll = Join-Path $instance 'mods\Ensrick - Equipment Display\SKSE\Plugins\EnsrickEquipmentDisplay.dll'
$docs = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Skyrim Special Edition'
$skseDir = Join-Path $docs 'SKSE'
$probe = Join-Path $skseDir 'LaunchProbe.log'
$pluginLog = Join-Path $skseDir 'EnsrickEquipmentDisplay.log'
$pilotLog = Join-Path $skseDir 'MenuPilot\menupilot.log'
$ui = Join-Path $root 'records-work\eed-r2-ui.ps1'
$launcher = Join-Path $root 'audit\launch_skyrim_isolated.ps1'
$statePath = Join-Path $root "records-work\eed-r2-state-$Attempt.json"
$profileName = "Fable EED R2 $Attempt $Stamp"

function Say($text) { Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $text) }
function Fail($text) { Say "FAIL: $text"; throw $text }
function Sha($path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
# Only lines stamped after $since count: the probe and plugin logs are truncated
# by their writers at the NEXT launch, so a fresh run reads a stale file first
# (launch 1 matched a MAIN_MENU_OPEN from another session's 13:10 launch).
function LineTime([string]$line) {
  if ($line -match '^\[(?:(\d{4}-\d{2}-\d{2}) )?(\d{2}:\d{2}:\d{2}\.\d{3})\]') {
    $date = if ($Matches[1]) { $Matches[1] } else { (Get-Date).ToString('yyyy-MM-dd') }
    return [datetime]::ParseExact("$date $($Matches[2])", 'yyyy-MM-dd HH:mm:ss.fff', $null)
  }
  return [datetime]::MinValue
}
function WaitFor([string]$file, [string]$pattern, [int]$seconds, [string]$what) {
  $since = $script:since
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $file) {
      $hit = Select-String -LiteralPath $file -Pattern $pattern -SimpleMatch | Where-Object { (LineTime $_.Line) -ge $since } | Select-Object -Last 1
      if ($hit) { Say "$what : $($hit.Line)"; return $hit.Line }
    }
    Start-Sleep -Seconds 2
  }
  Fail "timed out after $seconds s waiting for '$pattern' (after $($since.ToString('HH:mm:ss'))) in $file ($what)"
}
function Pilot([string[]]$arguments) {
  Say ("pilot: " + ($arguments -join ' '))
  & pwsh -NoProfile -File $ui -OwnedPid $script:gamePid -ClaimOwner $ClaimOwner @arguments 2>&1 | ForEach-Object { Say "  $_" }
  if ($LASTEXITCODE -ne 0) { Fail "pilot step failed: $($arguments -join ' ')" }
}
function NewCrashLogs([datetime]$since) {
  Get-ChildItem -LiteralPath $skseDir -Filter 'crash-*.log' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $since }
}
function SaveState($state) { $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8 }
function LoadState() {
  if (-not (Test-Path -LiteralPath $statePath)) { Fail "no state file $statePath; run -Phase launch first" }
  $s = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
  $script:gamePid = [int]$s.gamePid
  $script:since = ([datetime]$s.startedAt).AddSeconds(-5)
  if (-not (Get-Process -Id $script:gamePid -ErrorAction SilentlyContinue)) { Fail "SkyrimSE $($script:gamePid) is not running" }
  return $s
}

Set-Location $root

switch ($Phase) {
'launch' {
  # --- Preconditions -------------------------------------------------------
  $claim = & $py (Join-Path $root 'audit\claim.py') check --owner $ClaimOwner
  if ($LASTEXITCODE -ne 0 -or $claim -notmatch '^mine:') { Fail "claim $ClaimOwner not held ($claim)" }
  Say "claim: $claim"

  $running = @(Get-Process -Name SkyrimSE, ModOrganizer, MO2Headless -ErrorAction SilentlyContinue)
  if ($running.Count -gt 0) { Fail ("game or MO2 already running: " + (($running | ForEach-Object { "$($_.Name) $($_.Id)" }) -join ', ')) }

  $receiptPath = Join-Path $root $Receipt
  if (-not (Test-Path -LiteralPath $receiptPath)) { Fail "receipt missing: $receiptPath" }
  $expected = (Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json).dllSha256.ToLowerInvariant()
  if ($expected -notmatch '^[0-9a-f]{64}$') { Fail "receipt dllSha256 is not a sha256: '$expected'" }
  if (-not (Test-Path -LiteralPath $installedDll)) { Fail "installed DLL missing: $installedDll" }
  $installed = Sha $installedDll
  if ($installed -ne $expected) { Fail "installed DLL $installed != receipt clean-build $expected; only clean bytes may be launched" }
  Say "hash gate: installed DLL == receipt clean build $expected"

  $order = & $py (Join-Path $root 'audit\verify_order.py') 2>&1
  if ($LASTEXITCODE -ne 0 -or ($order -join "`n") -notmatch 'CLEAN') { Fail ("verify_order not CLEAN (#253):`n" + ($order -join "`n")) }
  Say "verify_order: CLEAN"

  $pending = Join-Path $skseDir 'MenuPilot\commands.jsonl'
  if (Test-Path -LiteralPath $pending) { Fail "stale MenuPilot batch at $pending" }

  $startedAt = Get-Date
  $script:since = $startedAt.AddSeconds(-5)
  $archive = Join-Path $root ("records\log-snapshots\" + $startedAt.ToString('yyyyMMdd-HHmmss') + "-eed-r2-$Attempt")
  New-Item -ItemType Directory -Force -Path $archive | Out-Null
  $launcherOut = Join-Path $archive 'launcher-output.log'
  $launcherErr = Join-Path $archive 'launcher-error.log'

  # --- Launch (detached, so this shell's own timeout cannot kill the tree) --
  Say "launching isolated: profile '$profileName', WaitSeconds $WaitSeconds"
  # ShellExecute (no -Redirect*, no -NoNewWindow) so the launcher tree inherits
  # none of this shell's pipes: with inherited handles the caller of this script
  # blocked until the game exited (launches 1 and 1b). The inner pwsh redirects
  # its own output to the archive.
  $inner = "& '" + $launcher + "' -WaitSeconds " + $WaitSeconds + " -TestProfileName '" + $profileName + "' -SourceProfileName Default -ClaimOwner '" + $ClaimOwner + "' *> '" + $launcherOut + "'"
  $launch = Start-Process -FilePath 'pwsh' -PassThru -WindowStyle Hidden -ArgumentList @('-NoProfile', '-Command', $inner)
  Say "launcher pwsh pid $($launch.Id)"

  $menuLine = WaitFor $probe 'MAIN_MENU_OPEN' 180 'main menu'
  $menuSeconds = -1
  if ($menuLine -match '\+(\d+)ms') { $menuSeconds = [int]$Matches[1] / 1000.0; Say ("main menu at t+{0:N1} s ({1})" -f $menuSeconds, $(if ($menuSeconds -lt 60) { 'under 60 s' } else { 'OVER 60 s' })) }
  Start-Sleep -Seconds 3
  $game = @(Get-Process -Name SkyrimSE -ErrorAction SilentlyContinue)
  if ($game.Count -ne 1) { Fail "expected exactly one SkyrimSE, found $($game.Count)" }
  $script:gamePid = $game[0].Id
  Say "SkyrimSE pid $gamePid"
  SaveState @{ gamePid = $gamePid; launcherPid = $launch.Id; archive = $archive; startedAt = $startedAt.ToString('o'); menuSeconds = $menuSeconds; profile = $profileName }

  # --- Pilot: fresh character through Skyrim Unbound ------------------------
  Pilot @('-Action', 'MainNew')
  Pilot @('-Action', 'New')
  WaitFor $probe 'MENU_OPEN name="RaceSex Menu"' 90 'race menu' | Out-Null
  Start-Sleep -Seconds 4
  Pilot @('-Action', 'Race')
  WaitFor $probe 'MENU_CLOSE name="RaceSex Menu"' 60 'race menu closed' | Out-Null
  Start-Sleep -Seconds 4
  Pilot @('-Action', 'MCM')
  Start-Sleep -Seconds 1
  Pilot @('-Action', 'Begin', '-Count', '1')
  Say "phase launch done; next: -Phase test"
}
'test' {
  $s = LoadState
  # --- The plugin's self-test runs on its own clock; wait for its summary ----
  WaitFor $pluginLog 'selftest: armed' 120 'self-test armed' | Out-Null
  $summary = WaitFor $pluginLog 'selftest: complete' $SelfTestBudgetSeconds 'self-test summary'
  Start-Sleep -Seconds 3
  Pilot @('-Action', 'Inventory')
  $s | Add-Member -NotePropertyName summary -NotePropertyValue $summary -Force
  $s | Add-Member -NotePropertyName testDoneAt -NotePropertyValue (Get-Date).ToString('o') -Force
  SaveState $s
  Say "phase test done; next: -Phase soak"
}
'soak' {
  $s = LoadState
  $startedAt = [datetime]$s.startedAt
  $archive = $s.archive
  # --- Soak ----------------------------------------------------------------
  Say "soak $SoakSeconds s"
  $soakEnd = (Get-Date).AddSeconds($SoakSeconds)
  while ((Get-Date) -lt $soakEnd) {
    Start-Sleep -Seconds 15
    if (-not (Get-Process -Id $gamePid -ErrorAction SilentlyContinue)) { Fail "SkyrimSE $gamePid exited during the soak" }
    $crashes = @(NewCrashLogs $startedAt)
    if ($crashes.Count -gt 0) { Fail ("crash log during the soak: " + ($crashes.Name -join ', ')) }
    Say "alive"
  }

  # --- Quit ----------------------------------------------------------------
  Pilot @('-Action', 'Quit')
  $deadline = (Get-Date).AddSeconds(90)
  while ((Get-Date) -lt $deadline -and (Get-Process -Id $gamePid -ErrorAction SilentlyContinue)) { Start-Sleep -Seconds 3 }
  if (Get-Process -Id $gamePid -ErrorAction SilentlyContinue) { Say "WARNING: SkyrimSE $gamePid still running 90 s after the quit; not killed (#164)" } else { Say "SkyrimSE gone" }
  $launcherProc = Get-Process -Id ([int]$s.launcherPid) -ErrorAction SilentlyContinue
  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline -and $launcherProc -and -not $launcherProc.HasExited) { Start-Sleep -Seconds 3; $launcherProc = Get-Process -Id ([int]$s.launcherPid) -ErrorAction SilentlyContinue }
  Say ("launcher pwsh {0}" -f $(if ($launcherProc) { 'still running' } else { 'exited' }))

  # --- Archive -------------------------------------------------------------
  Start-Sleep -Seconds 2
  foreach ($f in @($probe, $pluginLog, $pilotLog, (Join-Path $skseDir 'skse64.log'), (Join-Path $skseDir 'PopupGuard.log'),
                   (Join-Path $skseDir 'CrashLogger.log'), (Join-Path $docs 'Logs\Script\Papyrus.0.log'))) {
    if (Test-Path -LiteralPath $f) { Copy-Item -LiteralPath $f -Destination $archive -Force }
  }
  Get-ChildItem -LiteralPath $skseDir -Filter 'EnsrickEquipmentDisplay_*.txt' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $startedAt } | Copy-Item -Destination $archive -Force
  NewCrashLogs $startedAt | Copy-Item -Destination $archive -Force
  Copy-Item -LiteralPath $ui, $PSCommandPath, $statePath -Destination $archive -Force

  $errors = @(Select-String -LiteralPath (Join-Path $archive 'EnsrickEquipmentDisplay.log') -Pattern '\[error\]|\[critical\]').Count
  $crashCount = @(NewCrashLogs $startedAt).Count
  $popup = @(Get-Content -LiteralPath (Join-Path $archive 'PopupGuard.log') -ErrorAction SilentlyContinue | Where-Object { $_ -match 'INTERCEPT|MessageBox' }).Count
  $controller = Get-Content -LiteralPath (Join-Path $archive 'launcher-output.log') -ErrorAction SilentlyContinue | Where-Object { $_ -match 'ControllerExitCode' }
  Say "archive: $archive"
  Say ("verdict inputs: main menu t+{0} s; plugin [error]/[critical] lines {1}; new crash logs {2}; PopupGuard intercept lines {3}; {4}; self-test: {5}" -f $s.menuSeconds, $errors, $crashCount, $popup, ($controller -join ' '), $s.summary)
}
}
