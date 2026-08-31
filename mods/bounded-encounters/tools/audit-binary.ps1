#Requires -Version 5.1

[CmdletBinding()]
param(
    [string]$DllPath = "",
    [string]$GeneratedMetadataPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($DllPath)) {
    $DllPath = Join-Path $repoRoot "build/release/BoundedEncounters.dll"
} elseif (-not [System.IO.Path]::IsPathRooted($DllPath)) {
    $DllPath = Join-Path $repoRoot $DllPath
}
if ([string]::IsNullOrWhiteSpace($GeneratedMetadataPath)) {
    $GeneratedMetadataPath = Join-Path $repoRoot "build/release/__BoundedEncountersPlugin.cpp"
} elseif (-not [System.IO.Path]::IsPathRooted($GeneratedMetadataPath)) {
    $GeneratedMetadataPath = Join-Path $repoRoot $GeneratedMetadataPath
}
$DllPath = [System.IO.Path]::GetFullPath($DllPath)
$GeneratedMetadataPath = [System.IO.Path]::GetFullPath($GeneratedMetadataPath)

foreach ($required in @($DllPath, $GeneratedMetadataPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required binary-audit input is missing: $required"
    }
}

function Find-Dumpbin {
    $command = Get-Command dumpbin.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio/Installer/vswhere.exe"
    if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
        throw "dumpbin.exe is unavailable and vswhere.exe was not found"
    }
    $installation = (& $vswhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($installation)) {
        throw "No Visual Studio installation with the x64 C++ tools was found"
    }

    $toolsRoot = Join-Path $installation "VC/Tools/MSVC"
    $candidate = Get-ChildItem -LiteralPath $toolsRoot -Directory |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName "bin/Hostx64/x64/dumpbin.exe" } |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        throw "The Visual Studio x64 dumpbin.exe could not be located"
    }
    return $candidate
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace("-", "").ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

$dumpbin = Find-Dumpbin
$headers = (& $dumpbin /nologo /headers $DllPath | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "dumpbin /headers failed"
}
if ($headers -notmatch '(?m)^\s*File Type:\s+DLL\s*$' -or
    $headers -notmatch '(?m)^\s*8664 machine \(x64\)\s*$') {
    throw "BoundedEncounters.dll is not an x64 PE DLL"
}

$exportOutput = (& $dumpbin /nologo /exports $DllPath | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "dumpbin /exports failed"
}
$exports = [System.Text.RegularExpressions.Regex]::Matches(
    $exportOutput,
    '(?m)^\s+\d+\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+(SKSEPlugin_[A-Za-z0-9_]+)\s*$') |
    ForEach-Object { $_.Groups[1].Value } |
    Sort-Object -Unique
$expectedExports = @("SKSEPlugin_Load", "SKSEPlugin_Query", "SKSEPlugin_Version")
$exportDifference = Compare-Object -ReferenceObject $expectedExports -DifferenceObject @($exports)
if (@($exports).Count -ne $expectedExports.Count -or $exportDifference) {
    throw "Unexpected SKSE export set: $($exports -join ', ')"
}

$importOutput = (& $dumpbin /nologo /imports $DllPath | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "dumpbin /imports failed"
}
$forbiddenImports = @(
    'MessageBoxA', 'MessageBoxW', 'MessageBeep',
    'ShellExecuteA', 'ShellExecuteW', 'ShellExecuteExA', 'ShellExecuteExW',
    'WinExec', 'CreateProcessA', 'CreateProcessW',
    'PlaySoundA', 'PlaySoundW', 'Beep',
    'SetForegroundWindow', 'ShowWindow'
)
$foundForbidden = foreach ($symbol in $forbiddenImports) {
    if ($importOutput -match ('(?m)\b' + [regex]::Escape($symbol) + '\b')) {
        $symbol
    }
}
if ($foundForbidden) {
    throw "Forbidden modal/focus/process/audio imports found: $($foundForbidden -join ', ')"
}

$metadata = Get-Content -LiteralPath $GeneratedMetadataPath -Raw
foreach ($requiredPattern in @(
        'RuntimeCompatibility\s*=\s*\{\s*REL::Version\{\s*1,\s*7,\s*104,\s*0\s*\}\s*\}',
        'MinimumSKSEVersion\s*=\s*REL::Version\{\s*2,\s*3,\s*1,\s*0\s*\}'
    )) {
    if ($metadata -notmatch $requiredPattern) {
        throw "Generated SKSE metadata does not contain the exact reviewed runtime gate"
    }
}

[ordered]@{
    dll = $DllPath
    sha256 = Get-Sha256 -Path $DllPath
    machine = "x64"
    exports = @($exports)
    forbiddenImports = @()
    skyrimRuntime = "1.7.104.0"
    minimumSkse = "2.3.1.0"
} | ConvertTo-Json -Depth 4
