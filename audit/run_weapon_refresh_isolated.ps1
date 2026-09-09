#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ClaimOwner,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$Batch,
    [ValidateSet('Generate', 'FinalWinners')][string]$Action = 'Generate',
    [switch]$Worker
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$instance = 'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
$python = 'C:\Users\danjo\AppData\Local\Programs\Python\Python313\python.exe'
$pwsh = (Get-Process -Id $PID).Path
$logDirectory = Join-Path $repo "records-work\$Batch"
$artifact = Join-Path $repo "mods\weapon-balance\artifacts\$Batch"
if ($ClaimOwner -notmatch '^[A-Za-z0-9_][A-Za-z0-9_/-]*$') { throw 'Unsafe owner argument.' }
$claim = & $python (Join-Path $PSScriptRoot 'claim.py') check --owner $ClaimOwner
if ($LASTEXITCODE -ne 0 -or ($claim -join "`n") -notmatch '^mine:') { throw 'Claim must already be held.' }
Add-Type -Path (Join-Path $PSScriptRoot 'QuietWorker.cs')

if ($Worker) {
    if (-not [QuietWorker]::IsPrivateWorkerDesktop()) { throw 'Worker requires its private desktop; use the parent entry point.' }
    Start-Transcript -LiteralPath (Join-Path $logDirectory 'worker.log') -NoClobber | Out-Null
    try {
        if ($Action -eq 'FinalWinners') {
            & (Join-Path $repo 'mods\weapon-balance\audit.ps1') -FinalWinners `
                -Instance $instance -Profile Default -AllowLiveProfileAccess -ClaimOwner $ClaimOwner
            exit $LASTEXITCODE
        }
        & (Join-Path $repo 'mods\weapon-balance\generate.ps1') -ExecutionMode MO2Vfs `
            -Instance $instance -Profile Default -AllowLiveProfileAccess -ClaimOwner $ClaimOwner `
            -OutputPath (Join-Path $artifact 'WeaponBalancePatch.esp') `
            -SelectionReportPath (Join-Path $artifact 'selection-report.json') `
            -BuildManifestPath (Join-Path $artifact 'build-manifest.json')
        exit 0
    } catch {
        $_ | Out-String | Write-Output
        exit 1
    } finally { Stop-Transcript | Out-Null }
}

if (@(Get-Process -Name SkyrimSE,ModOrganizer,MO2Headless -ErrorAction SilentlyContinue).Count) {
    throw 'A game/controller session already exists; do not overlap it.'
}
if (Test-Path -LiteralPath $logDirectory) { throw 'Batch must be new; preserve earlier evidence.' }
New-Item -ItemType Directory -Path $logDirectory | Out-Null
$ini = Join-Path $instance 'ModOrganizer.ini'
$original = [IO.File]::ReadAllBytes($ini)
[IO.File]::WriteAllBytes((Join-Path $logDirectory 'ModOrganizer.before.ini'), $original)
try {
    # MO2 spawn.cpp documents No=Continue, without elevation. This is only
    # the Steam access advisory, NOT consent to elevate or restart Steam.
    # Reject non-UTF8 rather than silently corrupting the temporary config.
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($original)
    $choice = 'steamAdminQuery\WeaponBalancePatcher.exe=65536'
    if ($text -match '(?m)^steamAdminQuery\\WeaponBalancePatcher\.exe=') {
        $text = [regex]::Replace($text, '(?m)^steamAdminQuery\\WeaponBalancePatcher\.exe=[^\r\n]*', $choice)
    } elseif ($text -match '(?m)^\[DialogChoices\]\r?$') {
        $text = [regex]::Replace($text, '(?m)^\[DialogChoices\]\r?$', ('[DialogChoices]' + "`r`n" + $choice))
    } else { $text += "`r`n[DialogChoices]`r`n" + $choice + "`r`n" }
    [IO.File]::WriteAllText($ini, $text, [Text.UTF8Encoding]::new($false))
    $arguments = '-NoProfile -NonInteractive -File "' + $PSCommandPath + '" -Worker -ClaimOwner "' + $ClaimOwner + '" -Batch ' + $Batch + ' -Action ' + $Action
    $code = [QuietWorker]::Run($pwsh, $arguments, $repo, 900000)
} finally {
    # Job termination can briefly leave an exiting child holding the file.
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        try {
            [IO.File]::WriteAllBytes($ini, $original)
            if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($ini))) -ne
                [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($original))) {
                throw 'Restored MO2 configuration does not match its before-image.'
            }
            break
        } catch {
            if ($attempt -eq 19) { throw }
            Start-Sleep -Milliseconds 250
        }
    }
}
Get-Content -LiteralPath (Join-Path $logDirectory 'worker.log') -Tail 20 -ErrorAction SilentlyContinue
Write-Output "Isolated worker exit: $code; log directory: $logDirectory"
exit $code
