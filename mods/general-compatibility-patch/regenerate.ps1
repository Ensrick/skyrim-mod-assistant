#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $ToolchainManifest,

    [Parameter(Mandatory)]
    [string] $InstanceRoot,

    [string] $SortedProfile = 'Compatibility Audit LOOT Rules 2026-08-29',

    [string] $ActiveSourceProfile = 'Default',

    [Parameter(Mandatory)]
    [string] $DataFolder
)

$ErrorActionPreference = 'Stop'
$pluginName = 'Ensrick General Compatibility Patch.esp'
$ownedRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$generatorFolder = Join-Path $PSScriptRoot 'generator'
$project = Join-Path $generatorFolder 'GeneralCompatibilityPatcher.csproj'
$executable = Join-Path $generatorFolder 'bin\Release\net9.0\GeneralCompatibilityPatcher.exe'
$work = Join-Path $PSScriptRoot 'work'
$package = Join-Path $PSScriptRoot 'package'
$output = Join-Path $package $pluginName
$spriggitText = Join-Path $PSScriptRoot 'spriggit'
$effectiveLoadOrder = Join-Path $work 'effective-sorted-loadorder.txt'

function Assert-OwnedPath {
    param([Parameter(Mandatory)][string] $Path)

    $resolved = [System.IO.Path]::GetFullPath($Path)
    $prefix = $ownedRoot.TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to mutate a path outside the owned patch folder: $resolved"
    }
}

function Reset-OwnedDirectory {
    param([Parameter(Mandatory)][string] $Path)

    Assert-OwnedPath $Path
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

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

function Invoke-HiddenProcess {
    param(
        [Parameter(Mandatory)][string] $FileName,
        [Parameter(Mandatory)][string[]] $Arguments,
        [Parameter(Mandatory)][string] $WorkingDirectory,
        [Parameter(Mandatory)][string] $LogStem,
        [hashtable] $Environment = @{}
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    foreach ($argument in $Arguments) {
        [void] $startInfo.ArgumentList.Add($argument)
    }
    foreach ($entry in $Environment.GetEnumerator()) {
        $startInfo.Environment[[string] $entry.Key] = [string] $entry.Value
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "Failed to start $FileName"
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        [System.IO.File]::WriteAllText("$LogStem.stdout.log", $stdout, [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText("$LogStem.stderr.log", $stderr, [System.Text.UTF8Encoding]::new($false))
        if ($process.ExitCode -ne 0) {
            throw "$FileName failed with exit code $($process.ExitCode). See $LogStem.stderr.log"
        }
        return $stdout
    }
    finally {
        if (-not $process.HasExited) {
            $process.Kill($true)
            $process.WaitForExit(5000) | Out-Null
        }
        $process.Dispose()
    }
}

function Invoke-Mo2Child {
    param(
        [Parameter(Mandatory)][string] $ChildPath,
        [Parameter(Mandatory)][string[]] $ChildArguments,
        [Parameter(Mandatory)][string] $ChildWorkingDirectory,
        [Parameter(Mandatory)][string] $LogStem,
        [Parameter(Mandatory)][pscustomobject] $Manifest
    )

    $childCommandLine = ($ChildArguments | ForEach-Object {
        ConvertTo-Win32CommandLineArgument ([string] $_)
    }) -join ' '

    $arguments = @(
        '--root', $InstanceRoot,
        '-p', $SortedProfile,
        '--timeout', '600',
        'run', $ChildPath,
        '--arguments', $childCommandLine,
        '--cwd', $ChildWorkingDirectory
    )
    $dotnetRoot = [string] $Manifest.privateDotnetRoot
    $invoke = @{
        FileName = [string] $Manifest.tools.mo2.path
        Arguments = $arguments
        WorkingDirectory = Split-Path -Parent ([string] $Manifest.tools.mo2.path)
        LogStem = $LogStem
        Environment = @{
            DOTNET_ROOT = $dotnetRoot
            DOTNET_ROOT_X64 = $dotnetRoot
            DOTNET_HOST_PATH = Join-Path $dotnetRoot 'dotnet.exe'
            DOTNET_CLI_TELEMETRY_OPTOUT = '1'
            PATH = "$dotnetRoot;$env:PATH"
        }
    }
    return Invoke-HiddenProcess @invoke
}

function Get-TreeDigest {
    param([Parameter(Mandatory)][string] $Path)

    $lines = Get-ChildItem -LiteralPath $Path -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $relative = [System.IO.Path]::GetRelativePath($Path, $_.FullName).Replace('\', '/')
            $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            "$relative`t$hash"
        }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes))
}

function New-DeterministicArchive {
    param(
        [Parameter(Mandatory)][string] $PluginPath,
        [Parameter(Mandatory)][string] $ArchivePath
    )

    Assert-OwnedPath $ArchivePath
    if (Test-Path -LiteralPath $ArchivePath) {
        Remove-Item -LiteralPath $ArchivePath -Force
    }
    Add-Type -AssemblyName System.IO.Compression
    $stream = [System.IO.File]::Open($ArchivePath, [System.IO.FileMode]::CreateNew)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $stream,
            [System.IO.Compression.ZipArchiveMode]::Create,
            $false)
        try {
            $entry = $archive.CreateEntry($pluginName, [System.IO.Compression.CompressionLevel]::Optimal)
            $entry.LastWriteTime = [DateTimeOffset]::new(2000, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
            $entryStream = $entry.Open()
            try {
                $source = [System.IO.File]::OpenRead($PluginPath)
                try { $source.CopyTo($entryStream) } finally { $source.Dispose() }
            }
            finally { $entryStream.Dispose() }
        }
        finally { $archive.Dispose() }
    }
    finally { $stream.Dispose() }
}

foreach ($required in @($ToolchainManifest, $project, $InstanceRoot, $DataFolder)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required path does not exist: $required"
    }
}

$manifest = Get-Content -LiteralPath $ToolchainManifest -Raw | ConvertFrom-Json
foreach ($toolName in @('mo2', 'spriggit', 'skyrimRecordCli')) {
    $tool = $manifest.tools.$toolName
    if (-not $tool -or -not (Test-Path -LiteralPath ([string] $tool.path) -PathType Leaf)) {
        throw "Pinned tool is missing: $toolName"
    }
    $actual = (Get-FileHash -LiteralPath ([string] $tool.path) -Algorithm SHA256).Hash
    if ($actual -ne [string] $tool.sha256) {
        throw "Pinned tool hash mismatch: $toolName"
    }
}

$dotnet = Join-Path ([string] $manifest.privateDotnetRoot) 'dotnet.exe'
if (-not (Test-Path -LiteralPath $dotnet -PathType Leaf)) {
    throw "Pinned private .NET executable is missing: $dotnet"
}

$runningMo2 = Get-Process -Name 'ModOrganizer' -ErrorAction SilentlyContinue
if ($runningMo2) {
    throw 'MO2 is already running; refusing an ambiguous background VFS generation.'
}

Reset-OwnedDirectory $work
Reset-OwnedDirectory $package

$sortedProfileFolder = Join-Path (Join-Path $InstanceRoot 'profiles') $SortedProfile
$activeProfileFolder = Join-Path (Join-Path $InstanceRoot 'profiles') $ActiveSourceProfile
$sortedFile = Join-Path $sortedProfileFolder 'loadorder.txt'
$activeFile = Join-Path $activeProfileFolder 'plugins.txt'
foreach ($required in @($sortedFile, $activeFile)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required profile file does not exist: $required"
    }
}

$activeNames = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $activeFile) {
    $trimmed = $line.Trim()
    if ($trimmed.StartsWith('*')) {
        [void] $activeNames.Add($trimmed.TrimStart('*'))
    }
}
$ccc = Join-Path (Split-Path -Parent $DataFolder) 'Skyrim.ccc'
if (Test-Path -LiteralPath $ccc) {
    foreach ($line in Get-Content -LiteralPath $ccc) {
        $name = $line.Trim().TrimStart('*')
        if ($name) { [void] $activeNames.Add($name) }
    }
}

$ordered = [System.Collections.Generic.List[string]]::new()
$seen = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $sortedFile) {
    $name = $line.Trim().TrimStart('*')
    if (-not $name -or $name.StartsWith('#')) { continue }
    if ($activeNames.Contains($name) -and $seen.Add($name)) {
        $ordered.Add("*$name")
    }
}
$missing = @($activeNames | Where-Object { -not $seen.Contains($_) } | Sort-Object)
if ($missing.Count -gt 0) {
    throw "The sorted profile omits active plugins: $($missing -join ', ')"
}
[System.IO.File]::WriteAllLines($effectiveLoadOrder, $ordered, [System.Text.UTF8Encoding]::new($false))

$processEnvironment = @{
    DOTNET_ROOT = [string] $manifest.privateDotnetRoot
    DOTNET_ROOT_X64 = [string] $manifest.privateDotnetRoot
    DOTNET_HOST_PATH = $dotnet
    DOTNET_CLI_HOME = Join-Path $work 'dotnet-home'
    DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    PATH = "$([string] $manifest.privateDotnetRoot);$env:PATH"
}
Invoke-HiddenProcess -FileName $dotnet -Arguments @(
    'build', $project, '-c', 'Release', '-p:RestoreLockedMode=true'
) -WorkingDirectory $generatorFolder -LogStem (Join-Path $work 'build') -Environment $processEnvironment | Out-Null
$selfTest = @{
    FileName = $executable
    Arguments = @('--self-test')
    WorkingDirectory = $generatorFolder
    LogStem = Join-Path $work 'self-test'
}
Invoke-HiddenProcess @selfTest | Out-Null

$runOutputs = @()
foreach ($run in 1..2) {
    $runFolder = Join-Path $work "generation-$run"
    New-Item -ItemType Directory -Path $runFolder -Force | Out-Null
    $runOutput = Join-Path $runFolder $pluginName
    $runOutputs += $runOutput
    $generate = @{
        ChildPath = $executable
        ChildArguments = @(
            'run-patcher',
            '--DataFolderPath', $DataFolder,
            '--GameRelease', 'SkyrimSE',
            '--LoadOrderFilePath', $effectiveLoadOrder,
            '--OutputPath', $runOutput,
            '--ModKey', $pluginName,
            '--PatcherName', 'EnsrickGeneralCompatibilityPatch',
            '--PersistencePath', (Join-Path $runFolder 'persistence')
        )
        ChildWorkingDirectory = $generatorFolder
        LogStem = Join-Path $work "generation-$run"
        Manifest = $manifest
    }
    Invoke-Mo2Child @generate | Out-Null
}

$hashes = @($runOutputs | ForEach-Object {
    (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
})
if ($hashes[0] -ne $hashes[1]) {
    throw "Determinism failure: generation hashes differ ($($hashes -join ', '))."
}
Copy-Item -LiteralPath $runOutputs[0] -Destination $output -Force

$linkAuditInvocation = @{
    ChildPath = $executable
    ChildArguments = @('--audit-links', $DataFolder, $effectiveLoadOrder, $output)
    ChildWorkingDirectory = $generatorFolder
    LogStem = Join-Path $work 'link-audit'
    Manifest = $manifest
}
$linkAuditEnvelope = (Invoke-Mo2Child @linkAuditInvocation) | ConvertFrom-Json
$linkAuditLine = @($linkAuditEnvelope.stdout -split "`r?`n" | Where-Object {
    $_.Trim().StartsWith('{')
})[0]
$linkAudit = $linkAuditLine | ConvertFrom-Json
if ($linkAudit.unresolved.Count -ne 0) {
    throw "Link audit found $($linkAudit.unresolved.Count) unresolved links."
}

Reset-OwnedDirectory $spriggitText
$spriggit = [string] $manifest.tools.spriggit.path
Invoke-HiddenProcess -FileName $spriggit -Arguments @(
    'serialize',
    '--InputPath', $output,
    '--OutputPath', $spriggitText,
    '--GameRelease', 'SkyrimSE',
    '--PackageName', 'Spriggit.Yaml.Skyrim',
    '--PackageVersion', '0.41.0',
    '--Check',
    '--ErrorOnUnknown'
) -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'spriggit-serialize') -Environment $processEnvironment | Out-Null

$roundtripFolder = Join-Path $work 'spriggit-roundtrip'
$roundtripText = Join-Path $work 'spriggit-roundtrip-text'
Reset-OwnedDirectory $roundtripFolder
Reset-OwnedDirectory $roundtripText
$roundtripPlugin = Join-Path $roundtripFolder $pluginName
Invoke-HiddenProcess -FileName $spriggit -Arguments @(
    'deserialize',
    '--InputPath', $spriggitText,
    '--OutputPath', $roundtripPlugin,
    '--PackageName', 'Spriggit.Yaml.Skyrim',
    '--PackageVersion', '0.41.0',
    '--BackupDays', '0'
) -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'spriggit-deserialize') -Environment $processEnvironment | Out-Null
Invoke-HiddenProcess -FileName $spriggit -Arguments @(
    'serialize',
    '--InputPath', $roundtripPlugin,
    '--OutputPath', $roundtripText,
    '--GameRelease', 'SkyrimSE',
    '--PackageName', 'Spriggit.Yaml.Skyrim',
    '--PackageVersion', '0.41.0',
    '--Check',
    '--ErrorOnUnknown'
) -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'spriggit-reserialize') -Environment $processEnvironment | Out-Null

$spriggitDigest = Get-TreeDigest $spriggitText
$roundtripDigest = Get-TreeDigest $roundtripText
if ($spriggitDigest -ne $roundtripDigest) {
    throw "Spriggit checked round-trip failed: $spriggitDigest != $roundtripDigest"
}

$archive = Join-Path $work 'Ensrick-General-Compatibility-Patch-0.1.0.zip'
New-DeterministicArchive -PluginPath $output -ArchivePath $archive
$python = (Get-Command py.exe -CommandType Application -ErrorAction Stop).Source
$auditOutput = Invoke-HiddenProcess -FileName $python -Arguments @(
    '-3',
    (Join-Path $PSScriptRoot 'audit.py'),
    '--plugin', $output,
    '--load-order', $effectiveLoadOrder,
    '--record-cli', ([string] $manifest.tools.skyrimRecordCli.path),
    '--decisions', (Join-Path $PSScriptRoot '..\..\records\synthesis\compatibility-sweep-2026-08-29\decisions.json'),
    '--archive', $archive,
    '--instance-root', $InstanceRoot,
    '--provider-profile', $ActiveSourceProfile,
    '--data-folder', $DataFolder
) -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'record-audit')
$recordAudit = $auditOutput | ConvertFrom-Json
if (-not $recordAudit.ok) {
    throw 'Independent record/package audit failed.'
}
$result = [ordered]@{
    schemaVersion = 1
    plugin = $pluginName
    profile = $SortedProfile
    activeSourceProfile = $ActiveSourceProfile
    effectiveLoadOrderEntries = $ordered.Count
    deterministicRuns = 2
    sha256 = $hashes[0]
    bytes = (Get-Item -LiteralPath $output).Length
    spriggitTreeSha256 = $spriggitDigest
    archiveSha256 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
    archiveBytes = (Get-Item -LiteralPath $archive).Length
    linksChecked = [int] $linkAudit.linksChecked
    unresolvedLinks = [int] $linkAudit.unresolved.Count
    selectedFieldsChecked = [int] $recordAudit.selectedFieldsChecked
    waterFieldsComparedToFinalWinner = [int] $recordAudit.worldspaceWaterFieldsComparedToFinalWinner
    newForms = [int] $recordAudit.newForms
}
$resultPath = Join-Path $work 'regeneration-result.json'
[System.IO.File]::WriteAllText(
    $resultPath,
    ($result | ConvertTo-Json -Depth 5) + "`n",
    [System.Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 5
