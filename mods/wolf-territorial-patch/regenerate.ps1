#requires -Version 7.0
<#
Regenerate "Ensrick Wolf Territorial Patch.esp" (issue #42) from the live MO2 profile.

  pwsh ./mods/wolf-territorial-patch/regenerate.ps1 `
    -ToolchainManifest C:/path/toolchain.json `
    -InstanceRoot C:/path/mo2-instances/skyrim-se `
    -DataFolder "C:/.../Skyrim Special Edition/Data"

1. verifies the pinned MO2 and Spriggit hashes;
2. writes work/effective-loadorder.txt = the profile's active plugins (plugins.txt
   '*' rows + Skyrim.ccc) in loadorder.txt order, minus the output plugin;
3. builds the locked .NET generator (warnings are errors);
4. runs the wolf record audit through the MO2 VFS (work/wolf-audit.json);
5. generates the plugin twice through the VFS and requires byte-identical output;
6. link-audits the output against the full load order;
7. serializes with Spriggit, round-trips it, and requires identical trees;
8. writes a deterministic one-file zip and work/regeneration-result.json.

Nothing here deletes recursively: a previous work/package/spriggit tree is renamed
to <name>.bak.v<stamp> (repo rule).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $ToolchainManifest,
    [Parameter(Mandatory)] [string] $InstanceRoot,
    [Parameter(Mandatory)] [string] $DataFolder,
    [string] $Profile = 'Default',
    [string] $Version = '0.1.0'
)

$ErrorActionPreference = 'Stop'
$pluginName = 'Ensrick Wolf Territorial Patch.esp'
$ownedRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$generatorFolder = Join-Path $PSScriptRoot 'generator'
$project = Join-Path $generatorFolder 'WolfTerritorialPatcher.csproj'
$executable = Join-Path $generatorFolder 'bin\Release\net9.0\WolfTerritorialPatcher.exe'
$work = Join-Path $PSScriptRoot 'work'
$package = Join-Path $PSScriptRoot 'package'
$spriggitText = Join-Path $PSScriptRoot 'spriggit'
$policy = Join-Path $PSScriptRoot 'policy.json'
$output = Join-Path $package $pluginName
$effectiveLoadOrder = Join-Path $work 'effective-loadorder.txt'
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')

function Assert-OwnedPath([string] $Path) {
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($ownedRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to touch a path outside the owned patch folder: $resolved"
    }
}

function Reset-OwnedDirectory([string] $Path) {
    # Rename, never recurse-delete (repo rule #1).
    Assert-OwnedPath $Path
    if (Test-Path -LiteralPath $Path) {
        Rename-Item -LiteralPath $Path -NewName ((Split-Path -Leaf $Path) + ".bak.v$stamp")
    }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function ConvertTo-Win32CommandLineArgument([AllowEmptyString()][string] $Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $quoted = [System.Text.StringBuilder]::new(); [void] $quoted.Append('"'); $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $backslashes++; continue }
        if ($character -eq '"') { [void] $quoted.Append(('\' * (($backslashes * 2) + 1))); [void] $quoted.Append('"') }
        else { [void] $quoted.Append(('\' * $backslashes)); [void] $quoted.Append($character) }
        $backslashes = 0
    }
    [void] $quoted.Append(('\' * ($backslashes * 2))); [void] $quoted.Append('"')
    return $quoted.ToString()
}

function Invoke-HiddenProcess {
    param([string] $FileName, [string[]] $Arguments, [string] $WorkingDirectory, [string] $LogStem, [hashtable] $Environment = @{})
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    foreach ($argument in $Arguments) { [void] $startInfo.ArgumentList.Add($argument) }
    foreach ($entry in $Environment.GetEnumerator()) { $startInfo.Environment[[string] $entry.Key] = [string] $entry.Value }
    $process = [System.Diagnostics.Process]::new(); $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) { throw "Failed to start $FileName" }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync(); $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.GetAwaiter().GetResult(); $stderr = $stderrTask.GetAwaiter().GetResult()
        [System.IO.File]::WriteAllText("$LogStem.stdout.log", $stdout, [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText("$LogStem.stderr.log", $stderr, [System.Text.UTF8Encoding]::new($false))
        if ($process.ExitCode -ne 0) { throw "$FileName failed with exit code $($process.ExitCode). See $LogStem.stderr.log" }
        return $stdout
    } finally {
        if (-not $process.HasExited) { $process.Kill($true); $process.WaitForExit(5000) | Out-Null }
        $process.Dispose()
    }
}

function Invoke-Mo2Child {
    param([string] $ChildPath, [string[]] $ChildArguments, [string] $ChildWorkingDirectory, [string] $LogStem)
    $childCommandLine = ($ChildArguments | ForEach-Object { ConvertTo-Win32CommandLineArgument ([string] $_) }) -join ' '
    $arguments = @('--root', $InstanceRoot, '-p', $Profile, '--timeout', '600', 'run', $ChildPath, '--arguments', $childCommandLine, '--cwd', $ChildWorkingDirectory)
    $stdout = Invoke-HiddenProcess -FileName ([string] $manifest.tools.mo2.path) -Arguments $arguments `
        -WorkingDirectory (Split-Path -Parent ([string] $manifest.tools.mo2.path)) -LogStem $LogStem -Environment $processEnvironment
    $envelope = ($stdout -split "`r?`n" | Where-Object { $_.Trim().StartsWith('{') } | Select-Object -Last 1) | ConvertFrom-Json
    if (-not $envelope.ok) { throw "MO2 run failed: $stdout" }
    $inner = ($envelope.stdout -split "`r?`n" | Where-Object { $_.Trim().StartsWith('{"exitCode"') } | Select-Object -Last 1) | ConvertFrom-Json
    if ($inner -and $inner.exitCode -ne 0) { throw "Child exited $($inner.exitCode): $($envelope.stderr)" }
    return $envelope
}

function Get-TreeDigest([string] $Path) {
    [string[]] $files = Get-ChildItem -LiteralPath $Path -Recurse -File | Select-Object -ExpandProperty FullName
    [System.Array]::Sort($files, [System.StringComparer]::OrdinalIgnoreCase)
    $lines = $files | ForEach-Object {
        $relative = [System.IO.Path]::GetRelativePath($Path, $_).Replace('\', '/')
        "$relative`t$((Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash)"
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes))
}

function New-DeterministicArchive([string] $PluginPath, [string] $ArchivePath) {
    Assert-OwnedPath $ArchivePath
    if (Test-Path -LiteralPath $ArchivePath) { Remove-Item -LiteralPath $ArchivePath -Force }
    Add-Type -AssemblyName System.IO.Compression
    $stream = [System.IO.File]::Open($ArchivePath, [System.IO.FileMode]::CreateNew)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new($stream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            $entry = $archive.CreateEntry($pluginName, [System.IO.Compression.CompressionLevel]::Optimal)
            $entry.LastWriteTime = [DateTimeOffset]::new(2000, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
            $entryStream = $entry.Open()
            try { $source = [System.IO.File]::OpenRead($PluginPath); try { $source.CopyTo($entryStream) } finally { $source.Dispose() } }
            finally { $entryStream.Dispose() }
        } finally { $archive.Dispose() }
    } finally { $stream.Dispose() }
}

foreach ($required in @($ToolchainManifest, $project, $policy, $InstanceRoot, $DataFolder)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required path does not exist: $required" }
}
$manifest = Get-Content -LiteralPath $ToolchainManifest -Raw | ConvertFrom-Json
foreach ($toolName in @('mo2', 'spriggit')) {
    $tool = $manifest.tools.$toolName
    if (-not $tool -or -not (Test-Path -LiteralPath ([string] $tool.path) -PathType Leaf)) { throw "Pinned tool is missing: $toolName" }
    if ((Get-FileHash -LiteralPath ([string] $tool.path) -Algorithm SHA256).Hash -ne [string] $tool.sha256) { throw "Pinned tool hash mismatch: $toolName" }
}
$dotnetRoot = [string] $manifest.privateDotnetRoot
$dotnet = Join-Path $dotnetRoot 'dotnet.exe'
if (-not (Test-Path -LiteralPath $dotnet -PathType Leaf)) { throw "Pinned private .NET executable is missing: $dotnet" }
if (Get-Process -Name 'ModOrganizer' -ErrorAction SilentlyContinue) { throw 'MO2 GUI is running; refusing an ambiguous VFS generation.' }
if (Get-Process -Name 'SkyrimSE' -ErrorAction SilentlyContinue) { throw 'The game is running; refusing.' }

Reset-OwnedDirectory $work
Reset-OwnedDirectory $package

# 2. effective load order = active plugins of the profile in loadorder.txt order
$profileFolder = Join-Path (Join-Path $InstanceRoot 'profiles') $Profile
$pluginsFile = Join-Path $profileFolder 'plugins.txt'
$loadOrderFile = Join-Path $profileFolder 'loadorder.txt'
$activeNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($base in @('Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm')) { [void] $activeNames.Add($base) }
foreach ($line in Get-Content -LiteralPath $pluginsFile) { $t = $line.Trim(); if ($t.StartsWith('*')) { [void] $activeNames.Add($t.TrimStart('*')) } }
$ccc = Join-Path (Split-Path -Parent $DataFolder) 'Skyrim.ccc'
if (Test-Path -LiteralPath $ccc) { foreach ($line in Get-Content -LiteralPath $ccc) { $n = $line.Trim().TrimStart('*'); if ($n) { [void] $activeNames.Add($n) } } }
$ordered = [System.Collections.Generic.List[string]]::new()
$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $loadOrderFile) {
    $name = $line.Trim().TrimStart('*')
    if (-not $name -or $name.StartsWith('#') -or $name -ieq $pluginName) { continue }
    if ($activeNames.Contains($name) -and $seen.Add($name)) { $ordered.Add("*$name") }
}
$missing = @($activeNames | Where-Object { $_ -ine $pluginName -and -not $seen.Contains($_) } | Sort-Object)
if ($missing.Count -gt 0) { throw "loadorder.txt omits active plugins: $($missing -join ', ')" }
[System.IO.File]::WriteAllLines($effectiveLoadOrder, $ordered, [System.Text.UTF8Encoding]::new($false))

$processEnvironment = @{
    DOTNET_ROOT = $dotnetRoot; DOTNET_ROOT_X64 = $dotnetRoot; DOTNET_HOST_PATH = $dotnet
    DOTNET_CLI_HOME = Join-Path $work 'dotnet-home'; DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    PATH = "$dotnetRoot;$env:PATH"
}

# 3. build
Invoke-HiddenProcess -FileName $dotnet -Arguments @('build', $project, '-c', 'Release', '-p:RestoreLockedMode=true', '-nologo') `
    -WorkingDirectory $generatorFolder -LogStem (Join-Path $work 'build') -Environment $processEnvironment | Out-Null

# 4. record audit through the VFS
$auditJson = Join-Path $work 'wolf-audit.json'
Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit', $DataFolder, $effectiveLoadOrder, $auditJson) `
    -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work 'audit') | Out-Null

# 5. two generations, byte-identical
$runOutputs = @()
foreach ($run in 1..2) {
    $runFolder = Join-Path $work "generation-$run"
    New-Item -ItemType Directory -Path $runFolder -Force | Out-Null
    $runOutput = Join-Path $runFolder $pluginName
    $runOutputs += $runOutput
    Invoke-Mo2Child -ChildPath $executable -ChildArguments @(
        'run-patcher',
        '--DataFolderPath', $DataFolder,
        '--GameRelease', 'SkyrimSE',
        '--LoadOrderFilePath', $effectiveLoadOrder,
        '--OutputPath', $runOutput,
        '--ModKey', $pluginName,
        '--PatcherName', 'EnsrickWolfTerritorialPatch',
        '--PersistencePath', (Join-Path $runFolder 'persistence'),
        '--ExtraDataFolder', $PSScriptRoot
    ) -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work "generation-$run") | Out-Null
}
$hashes = @($runOutputs | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
if ($hashes[0] -ne $hashes[1]) { throw "Determinism failure: generation hashes differ ($($hashes -join ', '))." }
Copy-Item -LiteralPath $runOutputs[0] -Destination $output -Force

# 6. link audit
$linkEnvelope = Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit-links', $DataFolder, $effectiveLoadOrder, $output) `
    -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work 'link-audit')
$linkAudit = (@($linkEnvelope.stdout -split "`r?`n" | Where-Object { $_.Trim().StartsWith('{"records"') })[0]) | ConvertFrom-Json
if ($linkAudit.unresolved.Count -ne 0) { throw "Link audit found $($linkAudit.unresolved.Count) unresolved links." }

# 7. spriggit serialize + checked round trip
Reset-OwnedDirectory $spriggitText
$spriggit = [string] $manifest.tools.spriggit.path
$spriggitArgs = @('--GameRelease', 'SkyrimSE', '--PackageName', 'Spriggit.Yaml.Skyrim', '--PackageVersion', '0.41.0', '--Check', '--ErrorOnUnknown')
Invoke-HiddenProcess -FileName $spriggit -Arguments (@('serialize', '--InputPath', $output, '--OutputPath', $spriggitText) + $spriggitArgs) `
    -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'spriggit-serialize') -Environment $processEnvironment | Out-Null
$roundtripFolder = Join-Path $work 'spriggit-roundtrip'; $roundtripText = Join-Path $work 'spriggit-roundtrip-text'
New-Item -ItemType Directory -Path $roundtripFolder, $roundtripText -Force | Out-Null
$roundtripPlugin = Join-Path $roundtripFolder $pluginName
Invoke-HiddenProcess -FileName $spriggit -Arguments @('deserialize', '--InputPath', $spriggitText, '--OutputPath', $roundtripPlugin, '--PackageName', 'Spriggit.Yaml.Skyrim', '--PackageVersion', '0.41.0', '--BackupDays', '0') `
    -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'spriggit-deserialize') -Environment $processEnvironment | Out-Null
Invoke-HiddenProcess -FileName $spriggit -Arguments (@('serialize', '--InputPath', $roundtripPlugin, '--OutputPath', $roundtripText) + $spriggitArgs) `
    -WorkingDirectory $PSScriptRoot -LogStem (Join-Path $work 'spriggit-reserialize') -Environment $processEnvironment | Out-Null
$spriggitDigest = Get-TreeDigest $spriggitText
$roundtripDigest = Get-TreeDigest $roundtripText
if ($spriggitDigest -ne $roundtripDigest) { throw "Spriggit checked round-trip failed: $spriggitDigest != $roundtripDigest" }

# 8. deterministic archive + result
$archive = Join-Path $package "Ensrick-Wolf-Territorial-Patch-$Version.zip"
New-DeterministicArchive -PluginPath $output -ArchivePath $archive
$generationLog = Get-Content -LiteralPath (Join-Path $work 'generation-1.stdout.log') -Raw
$result = [ordered]@{
    schemaVersion = 1
    plugin = $pluginName
    version = $Version
    profile = $Profile
    effectiveLoadOrderEntries = $ordered.Count
    effectiveLoadOrderSha256 = (Get-FileHash -LiteralPath $effectiveLoadOrder -Algorithm SHA256).Hash
    pluginsTxtSha256 = (Get-FileHash -LiteralPath $pluginsFile -Algorithm SHA256).Hash
    policySha256 = (Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash
    deterministicRuns = 2
    sha256 = $hashes[0]
    bytes = (Get-Item -LiteralPath $output).Length
    spriggitTreeSha256 = $spriggitDigest
    archive = $archive
    archiveSha256 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
    archiveBytes = (Get-Item -LiteralPath $archive).Length
    linksChecked = [int] $linkAudit.linksChecked
    unresolvedLinks = [int] $linkAudit.unresolved.Count
    records = [int] $linkAudit.records
    generatedUtc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
}
[System.IO.File]::WriteAllText((Join-Path $work 'regeneration-result.json'), (($result | ConvertTo-Json -Depth 5) + "`n"), [System.Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 5
