[CmdletBinding()]
param(
    [string]$BuildDirectory,
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace BoundedEncounters
{
    public static class NativeCommandLine
    {
        [DllImport("shell32.dll", SetLastError = true)]
        private static extern IntPtr CommandLineToArgvW(
            [MarshalAs(UnmanagedType.LPWStr)] string commandLine,
            out int argumentCount);

        [DllImport("kernel32.dll")]
        private static extern IntPtr LocalFree(IntPtr memory);

        public static string[] Split(string commandLine)
        {
            int argumentCount;
            IntPtr argumentVector = CommandLineToArgvW(commandLine, out argumentCount);
            if (argumentVector == IntPtr.Zero)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            try
            {
                string[] arguments = new string[argumentCount];
                for (int index = 0; index < argumentCount; ++index)
                {
                    IntPtr argument = Marshal.ReadIntPtr(
                        argumentVector,
                        index * IntPtr.Size);
                    arguments[index] = Marshal.PtrToStringUni(argument);
                }
                return arguments;
            }
            finally
            {
                LocalFree(argumentVector);
            }
        }
    }
}
'@

function Get-NormalizedWindowsPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "A path used by the build-flag audit is empty."
    }
    $normalized = [System.IO.Path]::GetFullPath(
        $Value.Replace(
            [System.IO.Path]::AltDirectorySeparatorChar,
            [System.IO.Path]::DirectorySeparatorChar))
    $root = [System.IO.Path]::GetPathRoot($normalized)
    if ($normalized.Length -gt $root.Length) {
        $normalized = $normalized.TrimEnd(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar)
    }
    return $normalized
}

function Get-CommandArguments {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    [string[]]$arguments = [BoundedEncounters.NativeCommandLine]::Split($Command)
    if ($arguments.Count -eq 0) {
        throw "$Description contains no command-line arguments."
    }
    foreach ($argument in $arguments) {
        if ($argument.StartsWith("@", [System.StringComparison]::Ordinal)) {
            throw "$Description uses a response file whose options are not visible to this audit: $argument"
        }
    }
    return $arguments
}

function Get-OptionNames {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $options = [System.Collections.Generic.List[string]]::new()
    foreach ($argument in $Arguments) {
        if ($argument.Length -gt 1 -and
            ($argument[0] -eq [char]"/" -or $argument[0] -eq [char]"-")) {
            $options.Add($argument.Substring(1))
        }
    }
    return $options.ToArray()
}

if ([string]::IsNullOrWhiteSpace($BuildDirectory)) {
    $BuildDirectory = Join-Path $PSScriptRoot "../build/release"
}

$resolvedBuildDirectory = (Resolve-Path -LiteralPath $BuildDirectory).Path
$compileCommandsPath = Join-Path $resolvedBuildDirectory "compile_commands.json"
$buildNinjaPath = Join-Path $resolvedBuildDirectory "build.ninja"
$rulesNinjaPath = Join-Path $resolvedBuildDirectory "CMakeFiles/rules.ninja"
$cmakeCachePath = Join-Path $resolvedBuildDirectory "CMakeCache.txt"

$resolvedOutputPath = $null
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $outputCandidate = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
        $OutputPath
    } else {
        Join-Path (Get-Location).Path $OutputPath
    }
    $resolvedOutputPath = [System.IO.Path]::GetFullPath($outputCandidate)
    $buildPrefix = $resolvedBuildDirectory.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolvedOutputPath.StartsWith($buildPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Build-flag audit output must remain inside the configured build directory: $resolvedOutputPath"
    }
    if ($resolvedOutputPath.Equals($compileCommandsPath, [System.StringComparison]::OrdinalIgnoreCase) -or
        $resolvedOutputPath.Equals($buildNinjaPath, [System.StringComparison]::OrdinalIgnoreCase) -or
        $resolvedOutputPath.Equals($rulesNinjaPath, [System.StringComparison]::OrdinalIgnoreCase) -or
        $resolvedOutputPath.Equals($cmakeCachePath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Build-flag audit output must not overwrite one of its build-graph inputs: $resolvedOutputPath"
    }
    if (Test-Path -LiteralPath $resolvedOutputPath) {
        if (-not (Test-Path -LiteralPath $resolvedOutputPath -PathType Leaf)) {
            throw "Build-flag audit output already exists and is not a file: $resolvedOutputPath"
        }
        # Remove a stale report before auditing. File.Delete removes an output
        # symlink/hardlink itself before the new regular file is created.
        [System.IO.File]::Delete($resolvedOutputPath)
    }
}

foreach ($path in @($compileCommandsPath, $buildNinjaPath, $rulesNinjaPath, $cmakeCachePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "CMake did not produce a required build-graph input: $path"
    }
}

$implicitOptionVariables = @("CL", "_CL_", "LINK", "_LINK_")
foreach ($name in $implicitOptionVariables) {
    $value = [System.Environment]::GetEnvironmentVariable(
        $name,
        [System.EnvironmentVariableTarget]::Process)
    if ($null -ne $value -and $value.Length -gt 0) {
        throw "The $name environment variable is nonempty; MSVC would apply hidden options that are absent from the generated-command audit."
    }
}

$cmakeHomeValues = [System.Collections.Generic.List[string]]::new()
foreach ($line in (Get-Content -LiteralPath $cmakeCachePath)) {
    if ($line -match '^CMAKE_HOME_DIRECTORY:INTERNAL=(.*)$') {
        $cmakeHomeValues.Add($Matches[1])
    }
}
if ($cmakeHomeValues.Count -ne 1) {
    throw "CMakeCache.txt must contain exactly one CMAKE_HOME_DIRECTORY:INTERNAL record."
}
$expectedSourceDirectory = Get-NormalizedWindowsPath -Value $cmakeHomeValues[0]

$compileCommands = [System.Collections.Generic.List[object]]::new()
foreach ($entry in (Get-Content -LiteralPath $compileCommandsPath -Raw | ConvertFrom-Json)) {
    $compileCommands.Add($entry)
}
if ($compileCommands.Count -eq 0) {
    throw "compile_commands.json contains no production compile commands."
}

$auditedFiles = [System.Collections.Generic.List[string]]::new()
foreach ($entry in $compileCommands) {
    $file = [string]$entry.file
    $command = [string]$entry.command
    if ([string]::IsNullOrWhiteSpace($file) -or [string]::IsNullOrWhiteSpace($command)) {
        throw "compile_commands.json contains an entry without a file or command."
    }

    $description = "Compile command for '$file'"
    [string[]]$arguments = Get-CommandArguments -Command $command -Description $description
    [string[]]$options = Get-OptionNames -Arguments $arguments

    [string[]]$deterministicOptions = @($options | Where-Object {
            $_.StartsWith("experimental:deterministic", [System.StringComparison]::Ordinal)
        })
    if ($deterministicOptions.Count -ne 1 -or
        $deterministicOptions[0] -cne "experimental:deterministic") {
        throw "$description has missing, duplicate, or conflicting /experimental:deterministic flags."
    }

    [string[]]$codegenThreadOptions = @($options | Where-Object {
            $_.StartsWith("cgthreads", [System.StringComparison]::Ordinal)
        })
    if ($codegenThreadOptions.Count -ne 1 -or
        $codegenThreadOptions[0] -cne "cgthreads1") {
        throw "$description has missing, duplicate, or conflicting /cgthreads flags."
    }

    [string[]]$wholeProgramOptions = @($options | Where-Object {
            $_ -cmatch '^GL(?:$|[-:])'
        })
    if ($wholeProgramOptions.Count -ne 0) {
        throw "$description contains a /GL-family option; this release gate requires whole-program optimization to be absent."
    }

    [string[]]$pathMapOptions = @($options | Where-Object {
            $_.StartsWith("pathmap:", [System.StringComparison]::Ordinal)
        })
    if ($pathMapOptions.Count -ne 1) {
        throw "$description has missing or duplicate /pathmap flags."
    }
    $mapping = $pathMapOptions[0].Substring("pathmap:".Length)
    $equalsIndex = $mapping.LastIndexOf([char]"=")
    if ($equalsIndex -le 0 -or $equalsIndex -eq ($mapping.Length - 1)) {
        throw "$description has a malformed /pathmap flag."
    }
    $mappedSource = Get-NormalizedWindowsPath -Value $mapping.Substring(0, $equalsIndex)
    $mappedDestination = $mapping.Substring($equalsIndex + 1)
    if (-not $mappedSource.Equals($expectedSourceDirectory, [System.StringComparison]::OrdinalIgnoreCase) -or
        $mappedDestination -cne ".") {
        throw "$description does not map the configured CMAKE_HOME_DIRECTORY exactly to '.'."
    }

    $auditedFiles.Add($file)
}

$ninjaLines = @(Get-Content -LiteralPath $buildNinjaPath)
$rulesNinjaLines = @(Get-Content -LiteralPath $rulesNinjaPath)
$productionLinkRecords = [System.Collections.Generic.List[object]]::new()
for ($index = 0; $index -lt $ninjaLines.Count; ++$index) {
    if ($ninjaLines[$index] -notmatch '^build\s+.+:\s+((?:C|CXX)_(?:SHARED_LIBRARY|MODULE_LIBRARY|EXECUTABLE)_LINKER\S*)\b') {
        continue
    }
    $ruleName = $Matches[1]
    $surfaceValues = [ordered]@{
        LINK_FLAGS = [System.Collections.Generic.List[string]]::new()
        LINK_PATH = [System.Collections.Generic.List[string]]::new()
        LINK_LIBRARIES = [System.Collections.Generic.List[string]]::new()
    }
    for ($candidateIndex = $index + 1; $candidateIndex -lt $ninjaLines.Count; ++$candidateIndex) {
        $candidateLine = $ninjaLines[$candidateIndex]
        if ($candidateLine -match '^build\s+') {
            break
        }
        if ($candidateLine -match '^\s+(LINK_FLAGS|LINK_PATH|LINK_LIBRARIES)\s*=(.*)$') {
            $surfaceValues[$Matches[1]].Add($Matches[2].Trim())
        }
    }
    if ($surfaceValues.LINK_FLAGS.Count -ne 1) {
        throw "A production executable/shared/module-library link statement has no LINK_FLAGS record: $($ninjaLines[$index])"
    }
    if ($surfaceValues.LINK_PATH.Count -gt 1) {
        throw "A production link statement has duplicate LINK_PATH records: $($ninjaLines[$index])"
    }
    if ($surfaceValues.LINK_LIBRARIES.Count -ne 1) {
        throw "A production link statement must have exactly one LINK_LIBRARIES record: $($ninjaLines[$index])"
    }
    $productionLinkRecords.Add([pscustomobject]@{
            statement = $ninjaLines[$index]
            ruleName = $ruleName
            linkFlags = $surfaceValues.LINK_FLAGS[0]
            linkPath = if ($surfaceValues.LINK_PATH.Count -eq 1) { $surfaceValues.LINK_PATH[0] } else { "" }
            linkLibraries = $surfaceValues.LINK_LIBRARIES[0]
        })
}
if ($productionLinkRecords.Count -eq 0) {
    throw "build.ninja contains no executable, shared-library, or module-library link flag records."
}

foreach ($record in $productionLinkRecords) {
    $matchingRuleIndexes = [System.Collections.Generic.List[int]]::new()
    for ($index = 0; $index -lt $rulesNinjaLines.Count; ++$index) {
        if ($rulesNinjaLines[$index] -ceq "rule $($record.ruleName)") {
            $matchingRuleIndexes.Add($index)
        }
    }
    if ($matchingRuleIndexes.Count -ne 1) {
        throw "rules.ninja must contain exactly one rule definition for '$($record.ruleName)'."
    }

    $ruleProperties = [ordered]@{}
    for ($index = $matchingRuleIndexes[0] + 1; $index -lt $rulesNinjaLines.Count; ++$index) {
        $line = $rulesNinjaLines[$index]
        if ($line -match '^rule\s+' -or ($line.Length -gt 0 -and -not [char]::IsWhiteSpace($line[0]))) {
            break
        }
        if ($line -match '^\s+([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$') {
            $name = $Matches[1]
            if ($ruleProperties.Contains($name)) {
                throw "Linker rule '$($record.ruleName)' contains duplicate '$name' properties."
            }
            $ruleProperties[$name] = $Matches[2].Trim()
        }
    }
    if (-not $ruleProperties.Contains("command")) {
        throw "Linker rule '$($record.ruleName)' contains no command property."
    }
    if ($ruleProperties.Contains("rspfile") -or $ruleProperties.Contains("rspfile_content")) {
        throw "Linker rule '$($record.ruleName)' hides arguments in a Ninja response file."
    }

    $ruleCommand = [string]$ruleProperties.command
    $surfaceExpression = '$LINK_FLAGS $LINK_PATH $LINK_LIBRARIES'
    $surfaceIndex = $ruleCommand.IndexOf($surfaceExpression, [System.StringComparison]::Ordinal)
    if ($surfaceIndex -lt 0 -or
        $ruleCommand.LastIndexOf($surfaceExpression, [System.StringComparison]::Ordinal) -ne $surfaceIndex -or
        $ruleCommand.IndexOf("link.exe", [System.StringComparison]::OrdinalIgnoreCase) -lt 0 -or
        $ruleCommand.IndexOf("link.exe", [System.StringComparison]::OrdinalIgnoreCase) -gt $surfaceIndex) {
        throw "Linker rule '$($record.ruleName)' does not expose LINK_FLAGS, LINK_PATH, and LINK_LIBRARIES exactly once in the audited order after link.exe."
    }
    foreach ($surfaceVariable in @('$LINK_FLAGS', '$LINK_PATH', '$LINK_LIBRARIES')) {
        if ([regex]::Matches($ruleCommand, [regex]::Escape($surfaceVariable)).Count -ne 1) {
            throw "Linker rule '$($record.ruleName)' does not expose $surfaceVariable exactly once."
        }
    }
    if ($ruleCommand -match '(^|\s)@') {
        throw "Linker rule '$($record.ruleName)' contains an unaudited response-file token."
    }

    $expandedLinkSurface = @(
        [string]$record.linkFlags,
        [string]$record.linkPath,
        [string]$record.linkLibraries
    ) -join " "
    [string[]]$arguments = Get-CommandArguments `
        -Command ("link.exe " + $expandedLinkSurface) `
        -Description "Expanded link surface for '$($record.statement)'"
    [string[]]$options = Get-OptionNames -Arguments $arguments

    [string[]]$reproducibleLinkOptions = @($options | Where-Object {
            $_.StartsWith("Brepro", [System.StringComparison]::OrdinalIgnoreCase)
        })
    if ($reproducibleLinkOptions.Count -ne 1 -or
        -not $reproducibleLinkOptions[0].Equals("Brepro", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "A production link command has missing, duplicate, or conflicting /Brepro flags: $($record.statement)"
    }

    [string[]]$ltcgOptions = @($options | Where-Object {
            $_.StartsWith("LTCG", [System.StringComparison]::OrdinalIgnoreCase)
        })
    if ($ltcgOptions.Count -ne 0) {
        throw "A production link command contains an /LTCG-family option without a separately audited linker codegen control: $($record.statement)"
    }
}

$report = [ordered]@{
    schemaVersion = 3
    status = "pass"
    compileCommandCount = $auditedFiles.Count
    linkCommandCount = $productionLinkRecords.Count
    requiredCompileFlags = @(
        "/experimental:deterministic",
        "/cgthreads1",
        "/pathmap:<CMAKE_HOME_DIRECTORY>=."
    )
    forbiddenCompileFlags = @("/GL")
    requiredLinkFlags = @("/Brepro")
    forbiddenLinkFlags = @("/LTCG")
    auditedLinkVariables = @("LINK_FLAGS", "LINK_PATH", "LINK_LIBRARIES")
    forbiddenImplicitOptionEnvironment = $implicitOptionVariables
}
$json = ($report | ConvertTo-Json -Depth 4).Replace("`r`n", "`n").Replace("`r", "`n").TrimEnd() + "`n"

if ($null -ne $resolvedOutputPath) {
    [System.IO.File]::WriteAllText(
        $resolvedOutputPath,
        $json,
        [System.Text.UTF8Encoding]::new($false))
}

Write-Output $json.TrimEnd()
