#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('loot', 'synthesis', 'spriggit')]
    [string] $Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]] $ToolArguments = @(),

    [ValidateRange(0, 86400)]
    [int] $TimeoutSeconds = 0
)

$ErrorActionPreference = 'Stop'

$manifestPath = Join-Path $PSScriptRoot 'toolchain.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$entry = $manifest.tools.$Tool

if (-not $entry -or -not $entry.headlessLauncher) {
    throw "Tool '$Tool' is not approved for the hidden launcher."
}

$executable = [string] $entry.path
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Pinned executable is missing: $executable"
}

$actualHash = (Get-FileHash -LiteralPath $executable -Algorithm SHA256).Hash
if ($actualHash -ne [string] $entry.sha256) {
    throw "Checksum mismatch for '$Tool'. Expected $($entry.sha256), got $actualHash."
}

if ($entry.liblootPath) {
    $liblootPath = [string] $entry.liblootPath
    if (-not (Test-Path -LiteralPath $liblootPath -PathType Leaf)) {
        throw "Pinned libloot executable dependency is missing: $liblootPath"
    }
    $actualLiblootHash =
        (Get-FileHash -LiteralPath $liblootPath -Algorithm SHA256).Hash
    if ($actualLiblootHash -ne [string] $entry.liblootSha256) {
        throw "Checksum mismatch for '$Tool' libloot."
    }
}

$runId = '{0}-{1}-{2}' -f (
    [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'),
    $Tool,
    [Guid]::NewGuid().ToString('N').Substring(0, 8)
)
$runDirectory = Join-Path ([string] $manifest.runLogRoot) $runId
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

$processInfo = [System.Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = $executable
$processInfo.WorkingDirectory = if ($entry.workingDirectory) {
    [string] $entry.workingDirectory
} else {
    $runDirectory
}
$processInfo.UseShellExecute = $false
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.CreateNoWindow = $true
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

foreach ($argument in $ToolArguments) {
    [void] $processInfo.ArgumentList.Add($argument)
}

$pathPrefixes = @($entry.pathPrepend | Where-Object { $_ })
if ($pathPrefixes.Count -gt 0) {
    $processInfo.Environment['PATH'] = "$($pathPrefixes -join ';');$($processInfo.Environment['PATH'])"
}

if ($Tool -in @('synthesis', 'spriggit')) {
    $dotnetRoot = [string] $manifest.privateDotnetRoot
    $processInfo.Environment['DOTNET_ROOT'] = $dotnetRoot
    $processInfo.Environment['DOTNET_ROOT_X64'] = $dotnetRoot
    $processInfo.Environment['DOTNET_HOST_PATH'] = Join-Path $dotnetRoot 'dotnet.exe'
    $processInfo.Environment['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
    $processInfo.Environment['PATH'] = "$dotnetRoot;$($processInfo.Environment['PATH'])"
}

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $processInfo

try {
    if (-not $process.Start()) {
        throw "Failed to start '$Tool'."
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    if ($TimeoutSeconds -gt 0) {
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill($true)
            throw "Tool '$Tool' exceeded the $TimeoutSeconds-second timeout."
        }
    } else {
        $process.WaitForExit()
    }

    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $exitCode = $process.ExitCode
    if (
        $Tool -eq 'loot' -and
        $exitCode -eq 0 -and
        $stdout -match '(?m)^\[error\]\s'
    ) {
        $exitCode = 1
    }

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
        ExitCode = $exitCode
        RunDirectory = $runDirectory
        Stdout = Join-Path $runDirectory 'stdout.log'
        Stderr = Join-Path $runDirectory 'stderr.log'
    }

    exit $exitCode
}
finally {
    if (-not $process.HasExited) {
        $process.Kill($true)
        $process.WaitForExit(5000) | Out-Null
    }
    $process.Dispose()
}
