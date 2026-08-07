#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('loot', 'synthesis', 'spriggit')]
    [string] $Tool,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string] $Profile,

    [ValidateNotNullOrEmpty()]
    [string] $Instance,

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]] $ToolArguments = @(),

    [ValidateRange(0, 86400)]
    [int] $TimeoutSeconds = 0
)

$ErrorActionPreference = 'Stop'

function ConvertTo-Win32CommandLineArgument {
    param([AllowEmptyString()][string] $Value)

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }

    $quoted = [System.Text.StringBuilder]::new()
    [void] $quoted.Append('"')
    $backslashes = 0

    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }

        if ($character -eq '"') {
            [void] $quoted.Append(('\' * (($backslashes * 2) + 1)))
            [void] $quoted.Append('"')
        } else {
            [void] $quoted.Append(('\' * $backslashes))
            [void] $quoted.Append($character)
        }
        $backslashes = 0
    }

    [void] $quoted.Append(('\' * ($backslashes * 2)))
    [void] $quoted.Append('"')
    return $quoted.ToString()
}

$manifestPath = Join-Path $PSScriptRoot 'toolchain.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$mo2 = $manifest.tools.mo2
$entry = $manifest.tools.$Tool

foreach ($candidate in @(
    [pscustomobject]@{ Name = 'mo2'; Entry = $mo2 },
    [pscustomobject]@{ Name = $Tool; Entry = $entry }
)) {
    if (-not $candidate.Entry) {
        throw "Tool '$($candidate.Name)' is absent from the audited manifest."
    }

    $path = [string] $candidate.Entry.path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Pinned executable is missing: $path"
    }

    $actualHash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($actualHash -ne [string] $candidate.Entry.sha256) {
        throw "Checksum mismatch for '$($candidate.Name)'."
    }

    if ($candidate.Entry.liblootPath) {
        $liblootPath = [string] $candidate.Entry.liblootPath
        if (-not (Test-Path -LiteralPath $liblootPath -PathType Leaf)) {
            throw "Pinned libloot executable dependency is missing: $liblootPath"
        }
        $actualLiblootHash =
            (Get-FileHash -LiteralPath $liblootPath -Algorithm SHA256).Hash
        if ($actualLiblootHash -ne [string] $candidate.Entry.liblootSha256) {
            throw "Checksum mismatch for '$($candidate.Name)' libloot."
        }
    }
}

$mo2Path = [string] $mo2.path
$mo2GuiPath = if ($mo2.guiPath) { [string] $mo2.guiPath } else { $mo2Path }
$runningSameMo2 = Get-Process -Name 'ModOrganizer' -ErrorAction SilentlyContinue |
    Where-Object {
        try {
            [string]::Equals(
                $_.Path,
                $mo2GuiPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        } catch {
            $false
        }
    }

if ($runningSameMo2) {
    throw @"
The audited MO2 instance is already running. MO2 forwards command-line runs to
the primary process without a trustworthy completion result, so this launcher
refuses to claim an unattended run succeeded. Close that MO2 process before a
profile-mutating autonomous run.
"@
}

$runId = '{0}-mo2-{1}-{2}' -f (
    [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'),
    $Tool,
    [Guid]::NewGuid().ToString('N').Substring(0, 8)
)
$runDirectory = Join-Path ([string] $manifest.runLogRoot) $runId
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

$childArguments = (
    $ToolArguments |
        ForEach-Object { ConvertTo-Win32CommandLineArgument ([string] $_) }
) -join ' '

$processInfo = [System.Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = $mo2Path
$processInfo.WorkingDirectory = Split-Path -Parent $mo2Path
$processInfo.UseShellExecute = $false
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.CreateNoWindow = $true
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

$pathPrefixes = @($entry.pathPrepend | Where-Object { $_ })
if ($pathPrefixes.Count -gt 0) {
    $processInfo.Environment['PATH'] =
        "$($pathPrefixes -join ';');$($processInfo.Environment['PATH'])"
}

if ($Tool -in @('synthesis', 'spriggit')) {
    $dotnetRoot = [string] $manifest.privateDotnetRoot
    $processInfo.Environment['DOTNET_ROOT'] = $dotnetRoot
    $processInfo.Environment['DOTNET_ROOT_X64'] = $dotnetRoot
    $processInfo.Environment['DOTNET_HOST_PATH'] =
        Join-Path $dotnetRoot 'dotnet.exe'
    $processInfo.Environment['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
    $processInfo.Environment['PATH'] =
        "$dotnetRoot;$($processInfo.Environment['PATH'])"
}

if ($Instance) {
    [void] $processInfo.ArgumentList.Add('--root')
    [void] $processInfo.ArgumentList.Add($Instance)
}
[void] $processInfo.ArgumentList.Add('-p')
[void] $processInfo.ArgumentList.Add($Profile)
[void] $processInfo.ArgumentList.Add('--timeout')
[void] $processInfo.ArgumentList.Add([string] $TimeoutSeconds)
[void] $processInfo.ArgumentList.Add('run')
[void] $processInfo.ArgumentList.Add([string] $entry.path)
[void] $processInfo.ArgumentList.Add('--arguments')
[void] $processInfo.ArgumentList.Add($childArguments)
[void] $processInfo.ArgumentList.Add('--cwd')
[void] $processInfo.ArgumentList.Add(
    $(if ($entry.workingDirectory) {
        [string] $entry.workingDirectory
    } else {
        Split-Path -Parent ([string] $entry.path)
    })
)

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $processInfo

try {
    if (-not $process.Start()) {
        throw "Failed to start MO2 for '$Tool'."
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    if ($TimeoutSeconds -gt 0) {
        # MO2Headless owns the tool timeout; leave time for it to terminate the
        # child and return its structured result before killing the process tree.
        if (-not $process.WaitForExit(($TimeoutSeconds + 15) * 1000)) {
            $process.Kill($true)
            throw "MO2/$Tool exceeded the $TimeoutSeconds-second timeout."
        }
    } else {
        $process.WaitForExit()
    }

    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    [System.IO.File]::WriteAllText(
        (Join-Path $runDirectory 'stdout.log'),
        $stdout,
        [System.Text.UTF8Encoding]::new($false)
    )
    [System.IO.File]::WriteAllText(
        (Join-Path $runDirectory 'stderr.log'),
        $stderr,
        [System.Text.UTF8Encoding]::new($false)
    )

    [pscustomobject]@{
        Tool = $Tool
        Profile = $Profile
        Instance = $Instance
        ExitCode = $process.ExitCode
        RunDirectory = $runDirectory
    }

    exit $process.ExitCode
}
finally {
    if (-not $process.HasExited) {
        $process.Kill($true)
        $process.WaitForExit(5000) | Out-Null
    }
    $process.Dispose()
}
