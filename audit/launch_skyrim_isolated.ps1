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

if (-not ('SkyrimIsolatedDesktop.Native' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace SkyrimIsolatedDesktop
{
    public static class Native
    {
        private const uint DESKTOP_ALL_ACCESS = 0x000F01FF;
        private const uint CREATE_NO_WINDOW = 0x08000000;
        private const uint STARTF_USESHOWWINDOW = 0x00000001;
        private const short SW_HIDE = 0;
        private const uint WAIT_TIMEOUT = 0x00000102;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct STARTUPINFO
        {
            public int cb;
            public string lpReserved;
            public string lpDesktop;
            public string lpTitle;
            public uint dwX;
            public uint dwY;
            public uint dwXSize;
            public uint dwYSize;
            public uint dwXCountChars;
            public uint dwYCountChars;
            public uint dwFillAttribute;
            public uint dwFlags;
            public short wShowWindow;
            public short cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public uint dwProcessId;
            public uint dwThreadId;
        }

        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr CreateDesktop(
            string name, IntPtr device, IntPtr devmode, uint flags,
            uint desiredAccess, IntPtr securityAttributes);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool CloseDesktop(IntPtr desktop);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool CreateProcess(
            string applicationName, string commandLine, IntPtr processAttributes,
            IntPtr threadAttributes, bool inheritHandles, uint creationFlags,
            IntPtr environment, string currentDirectory, ref STARTUPINFO startupInfo,
            out PROCESS_INFORMATION processInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool TerminateProcess(IntPtr process, uint exitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr handle);

        public static uint Run(string desktopName, string application, string arguments,
            string workingDirectory, uint timeoutMilliseconds)
        {
            IntPtr desktop = CreateDesktop(
                desktopName, IntPtr.Zero, IntPtr.Zero, 0,
                DESKTOP_ALL_ACCESS, IntPtr.Zero);
            if (desktop == IntPtr.Zero)
                throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateDesktop failed");

            PROCESS_INFORMATION process = new PROCESS_INFORMATION();
            try
            {
                STARTUPINFO startup = new STARTUPINFO();
                startup.cb = Marshal.SizeOf<STARTUPINFO>();
                startup.lpDesktop = "WinSta0\\" + desktopName;
                startup.dwFlags = STARTF_USESHOWWINDOW;
                startup.wShowWindow = SW_HIDE;
                string commandLine = "\"" + application + "\" " + arguments;

                if (!CreateProcess(application, commandLine, IntPtr.Zero, IntPtr.Zero,
                    false, CREATE_NO_WINDOW, IntPtr.Zero, workingDirectory,
                    ref startup, out process))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateProcess failed");

                uint wait = WaitForSingleObject(process.hProcess, timeoutMilliseconds);
                if (wait == WAIT_TIMEOUT)
                {
                    TerminateProcess(process.hProcess, 124);
                    WaitForSingleObject(process.hProcess, 5000);
                }

                uint exitCode;
                if (!GetExitCodeProcess(process.hProcess, out exitCode))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "GetExitCodeProcess failed");
                return exitCode;
            }
            finally
            {
                if (process.hThread != IntPtr.Zero) CloseHandle(process.hThread);
                if (process.hProcess != IntPtr.Zero) CloseHandle(process.hProcess);
                CloseDesktop(desktop);
            }
        }
    }
}
'@
}

$env:SKSE_AUTOMATION_SILENT_UI = '1'
Get-ChildItem Env: | Where-Object {
    $_.Name -like 'SKYRIM_LAUNCH_PROBE_*' -or $_.Name -like 'SKYRIM_MENU_PILOT_*'
} | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
if ($LoadTestSave) { $env:SKYRIM_LAUNCH_PROBE_AUTOLOAD = $LoadTestSave }
$desktopName = 'CodexSkyrimSmoke-' + [Guid]::NewGuid().ToString('N').Substring(0, 12)
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
    $organizerText = [Text.Encoding]::UTF8.GetString($organizerOriginal)
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
    $exitCode = [SkyrimIsolatedDesktop.Native]::Run(
        $desktopName,
        $controller,
        $arguments,
        $instance,
        [uint32](($WaitSeconds + 30) * 1000)
    )
} finally {
    # Diagnostic cleanup only: game processes present before this launch were
    # rejected. Fully verified process-tree ownership remains #227 work.
    Get-Process -Name SkyrimSE, skse64_loader -ErrorAction SilentlyContinue |
        Where-Object { $_.StartTime -ge $startedAt } | Stop-Process -Force
    [IO.File]::WriteAllBytes($organizerPath, $organizerOriginal)
    if ($pluginExisted) { [IO.File]::WriteAllBytes($pluginTarget, $pluginOriginal) }
    elseif (Test-Path -LiteralPath $pluginTarget) { Remove-Item -LiteralPath $pluginTarget }
}

[pscustomobject]@{
    Desktop = $desktopName
    ControllerExitCode = $exitCode
    StartedAt = $startedAt.ToUniversalTime().ToString('o')
    FinishedAt = [DateTime]::UtcNow.ToString('o')
    Certification = 'NONE: inspect fresh LaunchProbe, MenuPilot and crash evidence separately.'
}

# A controller timeout is NOT a successful game test (it can be a hidden
# advisory waiting forever). Preserve the exit status instead of normalizing
# 75/124 to success; gameplay certification comes from runtime evidence.
exit ([int]$exitCode)
