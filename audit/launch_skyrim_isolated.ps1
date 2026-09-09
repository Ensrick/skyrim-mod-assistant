#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateRange(30, 600)]
    [int] $WaitSeconds = 120,
    [ValidatePattern('^[A-Za-z0-9 _-]+$')]
    [string] $TestProfileName = 'Codex Smoke - Muted',
    [ValidatePattern('^[A-Za-z0-9 _-]+$')]
    [string] $SourceProfileName = 'Default',
    [ValidatePattern('^[A-Za-z0-9_-]+$')]
    [string] $LoadTestSave,
    [string] $ClaimOwner = $env:SKYRIM_CLAIM_OWNER
)

$ErrorActionPreference = 'Stop'

$instance = 'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
$smokeProfileName = $TestProfileName
if ($smokeProfileName -eq 'Default' -or $smokeProfileName -eq $sourceProfileName) {
    throw 'Tests must not overwrite Default or their source profile.'
}
$sourceProfile = Join-Path $instance ('profiles\' + $sourceProfileName)
$profile = Join-Path $instance ('profiles\' + $smokeProfileName)
$game = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
$controller = Join-Path $instance 'MO2Headless.exe'
$loader = Join-Path $game 'skse64_loader.exe'
$python = 'C:\Users\danjo\AppData\Local\Programs\Python\Python313\python.exe'
if (-not $ClaimOwner) { throw 'Supply -ClaimOwner for an already-held instance claim.' }
$claimStatus = & $python (Join-Path $PSScriptRoot 'claim.py') check --owner $ClaimOwner
if ($LASTEXITCODE -ne 0 -or $claimStatus -notmatch '^mine:') {
    throw 'Acquire the instance claim before running isolated tests.'
}

foreach ($required in @($controller, $loader, (Join-Path $sourceProfile 'plugins.txt'))) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required launch input is missing: $required"
    }
}

$alreadyRunning = @(Get-Process -Name SkyrimSE, ModOrganizer, MO2Headless -ErrorAction SilentlyContinue)
if ($alreadyRunning.Count -gt 0) {
    throw 'Skyrim or MO2 is already running; the isolated test will not touch it.'
}

if (-not (Get-Process -Name steam -ErrorAction SilentlyContinue)) {
    throw 'Steam is not running; refusing to start it on the interactive desktop.'
}

# A hidden desktop suppresses windows, not audio.  Keep a dedicated profile so
# smoke-test audio can be disabled without changing the player's Default
# profile or persistent game preferences.  Refresh its load-order inputs on
# every run so it tests the current Default profile rather than a stale clone.
if (-not (Test-Path -LiteralPath $profile -PathType Container)) {
    & $controller profile-create $smokeProfileName --clone $sourceProfileName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not create the muted smoke-test profile.'
    }
}

foreach ($fileName in @('modlist.txt', 'plugins.txt', 'loadorder.txt', 'lockedorder.txt')) {
    $source = Join-Path $sourceProfile $fileName
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $profile $fileName) -Force
    }
}

$documents = [Environment]::GetFolderPath([Environment+SpecialFolder]::MyDocuments)
$gameSettings = Join-Path $documents 'My Games\Skyrim Special Edition'
$pendingPilot = Join-Path $gameSettings 'SKSE\MenuPilot\commands.jsonl'
if (Test-Path -LiteralPath $pendingPilot) {
    throw 'An unclaimed MenuPilot batch exists. Archive it before launching a different session.'
}
foreach ($fileName in @('Skyrim.ini', 'SkyrimPrefs.ini', 'SkyrimCustom.ini')) {
    $source = Join-Path $sourceProfile $fileName
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        $source = Join-Path $gameSettings $fileName
    }
    if ($fileName -eq 'SkyrimCustom.ini' -and -not (Test-Path -LiteralPath $source)) { continue }
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required game settings file is missing: $source"
    }
    Copy-Item -LiteralPath $source -Destination (Join-Path $profile $fileName) -Force
}

$profileSettingsPath = Join-Path $profile 'settings.ini'
$profileSettings = Get-Content -LiteralPath $profileSettingsPath -Raw
$profileSettings = [Regex]::Replace(
    $profileSettings,
    '(?im)^LocalSettings\s*=\s*(?:true|false)\s*$',
    'LocalSettings=true'
)
if ($profileSettings -notmatch '(?im)^LocalSettings\s*=') {
    throw 'Muted smoke profile has no LocalSettings field to isolate.'
}
$profileSettings = [Regex]::Replace($profileSettings,
    '(?im)^LocalSaves\s*=\s*(?:true|false)\s*$', 'LocalSaves=true')
if ($profileSettings -notmatch '(?im)^LocalSaves=true\s*$') {
    throw 'Test profile must isolate saves from the player profile.'
}
New-Item -ItemType Directory -Force (Join-Path $profile 'saves') | Out-Null
if ($LoadTestSave) {
    $testSavePath = Join-Path $profile ('saves\' + $LoadTestSave + '.ess')
    & $python (Join-Path $PSScriptRoot 'save_plugin_gate.py') $testSavePath --profile $sourceProfile | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Test save failed plugin admission; no launch.' }
}
[IO.File]::WriteAllText(
    $profileSettingsPath,
    $profileSettings,
    [Text.UTF8Encoding]::new($false)
)

$smokePrefsPath = Join-Path $profile 'SkyrimPrefs.ini'
$smokePrefs = Get-Content -LiteralPath $smokePrefsPath -Raw
$smokePrefs = [Regex]::Replace(
    $smokePrefs,
    '(?im)^fAudioMasterVolume\s*=\s*[^\r\n]+',
    'fAudioMasterVolume=0.0000'
)
if ($smokePrefs -notmatch '(?im)^fAudioMasterVolume\s*=\s*0(?:\.0+)?\s*$') {
    throw 'Could not force zero master volume in the isolated smoke profile.'
}
[IO.File]::WriteAllText(
    $smokePrefsPath,
    $smokePrefs,
    [Text.UTF8Encoding]::new($false)
)

$activePlugins = @(
    Get-Content -LiteralPath (Join-Path $sourceProfile 'plugins.txt') |
        Where-Object { $_.StartsWith('*') }
)
if ($activePlugins.Count -eq 0) {
    throw 'The Default profile has no readable active plugin entries.'
}

$pluginTarget = Join-Path $env:LOCALAPPDATA 'Skyrim Special Edition\Plugins.txt'
$pluginExisted = Test-Path -LiteralPath $pluginTarget
$pluginOriginal = if ($pluginExisted) { [IO.File]::ReadAllBytes($pluginTarget) } else { $null }
$pluginHeader = '# This file is used by Skyrim to keep track of your downloaded content.'

if (-not ('QuietWorker' -as [type])) {
    Add-Type -Path (Join-Path $PSScriptRoot 'QuietWorker.cs')
}

$env:SKSE_AUTOMATION_SILENT_UI = '1'
Get-ChildItem Env: | Where-Object {
    $_.Name -like 'SKYRIM_LAUNCH_PROBE_*' -or $_.Name -like 'SKYRIM_MENU_PILOT_*'
} | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
if ($LoadTestSave) { $env:SKYRIM_LAUNCH_PROBE_AUTOLOAD = $LoadTestSave }
$arguments = @(
    '-p', ('"' + $smokeProfileName + '"'),
    '--timeout', [string]$WaitSeconds,
    'run', ('"' + $loader + '"'),
    '--cwd', ('"' + $game + '"')
) -join ' '

$startedAt = Get-Date
$organizerPath = Join-Path $instance 'ModOrganizer.ini'
$organizerOriginal = [IO.File]::ReadAllBytes($organizerPath)
try {
    [IO.File]::WriteAllLines($pluginTarget, @($pluginHeader) + $activePlugins,
        [Text.UTF8Encoding]::new($false))
    # MO2's checkSteam advisory offers No="Continue" without elevation.
    # Select that documented, non-elevating option for this isolated run only.
    # Never restart Steam, answer UAC, or change a security setting here.
    $organizerText = [Text.UTF8Encoding]::new($false, $true).GetString($organizerOriginal)
    $choice = 'steamAdminQuery\skse64_loader.exe=65536'
    if ($organizerText -match '(?m)^steamAdminQuery\\skse64_loader\.exe=') {
        $organizerText = [Regex]::Replace($organizerText,
            '(?m)^steamAdminQuery\\skse64_loader\.exe=[^\r\n]*', $choice)
    } elseif ($organizerText -match '(?m)^\[DialogChoices\]\r?$') {
        $organizerText = [Regex]::Replace($organizerText,
            '(?m)^\[DialogChoices\]\r?$', ('[DialogChoices]' + "`r`n" + $choice))
    } else {
        $organizerText += "`r`n[DialogChoices]`r`n" + $choice + "`r`n"
    }
    [IO.File]::WriteAllText($organizerPath, $organizerText, [Text.UTF8Encoding]::new($false))
    $exitCode = [QuietWorker]::Run(
        $controller,
        $arguments,
        $instance,
        [uint32](($WaitSeconds + 30) * 1000)
    )
} finally {
    # QuietWorker owns only its suspended-then-assigned process tree. Never
    # kill processes by name/start time: another session could start meanwhile.
    for ($attempt=0; $attempt -lt 20; ++$attempt) {
        try {
            [IO.File]::WriteAllBytes($organizerPath, $organizerOriginal)
            if ($pluginExisted) { [IO.File]::WriteAllBytes($pluginTarget, $pluginOriginal) }
            elseif (Test-Path -LiteralPath $pluginTarget) { Remove-Item -LiteralPath $pluginTarget }
            if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($organizerPath))) -ne
                [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($organizerOriginal))) {
                throw 'MO2 INI restoration mismatch.'
            }
            break
        } catch {
            if ($attempt -eq 19) { throw }
            Start-Sleep -Milliseconds 250
        }
    }
}

[pscustomobject]@{
    Desktop = 'Private QuietWorker desktop; never switched to the interactive desktop'
    ControllerExitCode = $exitCode
    StartedAt = $startedAt.ToUniversalTime().ToString('o')
    FinishedAt = [DateTime]::UtcNow.ToString('o')
    Certification = 'NONE: inspect fresh LaunchProbe, MenuPilot and crash evidence separately.'
}

# A controller timeout is NOT a successful game test (it can be a hidden
# advisory waiting forever). Preserve the exit status instead of normalizing
# 75/124 to success; gameplay certification comes from runtime evidence.
exit ([int]$exitCode)
