#requires -Version 7.0
<#
Rebuild and validate the owned currency integration package without modifying
vendor mod folders or the live MO2 profile.

  pwsh ./mods/currency-integration/regenerate.ps1 `
    -ToolchainManifest ./toolchain.json `
    -InstanceRoot ../mo2-instances/skyrim-se `
    -GameRoot "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition"

The pipeline verifies pinned tools and Papyrus inputs, compiles all four packaged
scripts twice, normalizes deterministic PEX header metadata, generates the main
ESP and the regional-purse companion ESP twice, checks exact records/links and
the main ESP's SEQ, performs checked Spriggit semantic roundtrips, and creates
the deterministic archive twice.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $ToolchainManifest,
    [Parameter(Mandatory)] [string] $InstanceRoot,
    [Parameter(Mandatory)] [string] $GameRoot,
    [string] $Profile = 'Default',
    [string] $Version = '0.4.0'
)

$ErrorActionPreference = 'Stop'
$pluginName = 'Ensrick Currency Integration Patch.esp'
$regionalPursePluginName = 'Ensrick Currency Regional Purses.esp'
$scriptName = 'Ensrick_CurrencyRuntimeDefaultsAlias'
$dramCostScriptName = 'DES_DramCurrencySwapper'
$ulfricCostScriptName = 'DES_UlfricCurrencySwapper'
$madranShimName = 'DES_MadranSwapper'
$ownedRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$toolchainManifestPath = [IO.Path]::GetFullPath($ToolchainManifest)
$toolchainRepositoryRoot = Split-Path -Parent $toolchainManifestPath
$reposRoot = [IO.Path]::GetFullPath((Join-Path $toolchainRepositoryRoot '..'))
$generatorFolder = Join-Path $ownedRoot 'generator'
$project = Join-Path $generatorFolder 'CurrencyIntegrationPatcher.csproj'
$executable = Join-Path $generatorFolder 'bin\Release\net9.0\CurrencyIntegrationPatcher.exe'
$policy = Join-Path $ownedRoot 'policy.json'
$inputsPath = Join-Path $ownedRoot 'build-inputs.json'
$manifestPath = Join-Path $ownedRoot 'manifest.json'
$packagedScripts = [ordered]@{
    $scriptName = Join-Path $ownedRoot "papyrus\$scriptName.psc"
    $dramCostScriptName = Join-Path $ownedRoot "papyrus\$dramCostScriptName.psc"
    $ulfricCostScriptName = Join-Path $ownedRoot "papyrus\$ulfricCostScriptName.psc"
    $madranShimName = Join-Path $ownedRoot "papyrus\$madranShimName.psc"
}
$normalizer = Join-Path $ownedRoot 'normalize_pex.py'
$package = Join-Path $ownedRoot 'package'
$work = Join-Path $ownedRoot 'work'
$effectiveLoadOrder = Join-Path $work 'effective-loadorder.txt'
$dataFolder = Join-Path $GameRoot 'Data'
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')

function Assert-OwnedPath([string] $Path) {
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($ownedRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to write outside the owned integration folder: $resolved"
    }
}

function Reset-OwnedDirectory([string] $Path) {
    Assert-OwnedPath $Path
    if (Test-Path -LiteralPath $Path) {
        Rename-Item -LiteralPath $Path -NewName ((Split-Path -Leaf $Path) + ".bak.v$stamp")
    }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function ConvertTo-Win32CommandLineArgument([AllowEmptyString()][string] $Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $quoted = [Text.StringBuilder]::new(); [void] $quoted.Append('"'); $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $backslashes++; continue }
        if ($character -eq '"') {
            [void] $quoted.Append(('\' * (($backslashes * 2) + 1))); [void] $quoted.Append('"')
        } else {
            [void] $quoted.Append(('\' * $backslashes)); [void] $quoted.Append($character)
        }
        $backslashes = 0
    }
    [void] $quoted.Append(('\' * ($backslashes * 2))); [void] $quoted.Append('"')
    return $quoted.ToString()
}

function Invoke-HiddenProcess {
    param(
        [string] $FileName,
        [string[]] $Arguments,
        [string] $WorkingDirectory,
        [string] $LogStem,
        [hashtable] $Environment = @{}
    )
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    foreach ($argument in $Arguments) { [void] $startInfo.ArgumentList.Add($argument) }
    foreach ($entry in $Environment.GetEnumerator()) {
        $startInfo.Environment[[string] $entry.Key] = [string] $entry.Value
    }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) { throw "Failed to start $FileName" }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        [IO.File]::WriteAllText("$LogStem.stdout.log", $stdout, [Text.UTF8Encoding]::new($false))
        [IO.File]::WriteAllText("$LogStem.stderr.log", $stderr, [Text.UTF8Encoding]::new($false))
        if ($process.ExitCode -ne 0) {
            throw "$FileName failed with exit code $($process.ExitCode). See $LogStem.stderr.log"
        }
        return $stdout
    } finally {
        if (-not $process.HasExited) { $process.Kill($true); $process.WaitForExit(5000) | Out-Null }
        $process.Dispose()
    }
}

function Invoke-Mo2Child {
    param([string] $ChildPath, [string[]] $ChildArguments, [string] $ChildWorkingDirectory, [string] $LogStem)
    $childCommandLine = ($ChildArguments | ForEach-Object {
        ConvertTo-Win32CommandLineArgument ([string] $_
        )
    }) -join ' '
    $arguments = @('--root', $InstanceRoot, '-p', $Profile, '--timeout', '600', 'run',
        $ChildPath, '--arguments', $childCommandLine, '--cwd', $ChildWorkingDirectory)
    $stdout = Invoke-HiddenProcess -FileName ([string] $toolchain.tools.mo2.path) -Arguments $arguments `
        -WorkingDirectory (Split-Path -Parent ([string] $toolchain.tools.mo2.path)) -LogStem $LogStem `
        -Environment $processEnvironment
    $envelope = ($stdout -split "`r?`n" | Where-Object { $_.Trim().StartsWith('{') } |
        Select-Object -Last 1) | ConvertFrom-Json
    if (-not $envelope.ok) { throw "MO2 run failed: $stdout" }
    if ($envelope.stateDelta.orderChanged -or $envelope.stateDelta.newlyActive.Count -or
        $envelope.stateDelta.restored.Count -or $envelope.stateDelta.appended.Count) {
        throw "MO2 child changed profile state: $($envelope.stateDelta | ConvertTo-Json -Compress)"
    }
    return $envelope
}

function Get-PscTreeDigest([string] $Path) {
    $files = @(Get-ChildItem -LiteralPath $Path -File -Filter '*.psc' | Sort-Object Name)
    $lines = $files | ForEach-Object {
        "$($_.Name)`t$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function Get-TreeDigest([string] $Path) {
    [string[]] $files = Get-ChildItem -LiteralPath $Path -Recurse -File | Select-Object -ExpandProperty FullName
    [Array]::Sort($files, [StringComparer]::OrdinalIgnoreCase)
    $lines = $files | ForEach-Object {
        "$([IO.Path]::GetRelativePath($Path, $_).Replace('\', '/'))`t$((Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash)"
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function Write-ModuleManifestAtomic {
    $manifestTemp = "$manifestPath.tmp.$stamp"
    Assert-OwnedPath $manifestTemp
    [IO.File]::WriteAllText($manifestTemp,
        (($moduleManifest | ConvertTo-Json -Depth 12) + "`n"), [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($manifestTemp, $manifestPath, $true)
}

foreach ($required in @($toolchainManifestPath, $InstanceRoot, $GameRoot, $dataFolder, $project,
        $policy, $inputsPath, $normalizer, $package) + @($packagedScripts.Values)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required path does not exist: $required" }
}
if (Get-Process -Name 'ModOrganizer' -ErrorAction SilentlyContinue) {
    throw 'MO2 GUI is running; refusing an ambiguous VFS generation.'
}
if (Get-Process -Name 'SkyrimSE' -ErrorAction SilentlyContinue) {
    throw 'The game is running; refusing generation.'
}

$toolchain = Get-Content -LiteralPath $toolchainManifestPath -Raw | ConvertFrom-Json
foreach ($toolName in @('mo2', 'spriggit')) {
    $tool = $toolchain.tools.$toolName
    if (-not $tool -or -not (Test-Path -LiteralPath ([string] $tool.path) -PathType Leaf)) {
        throw "Pinned tool is missing: $toolName"
    }
    if ((Get-FileHash -LiteralPath ([string] $tool.path) -Algorithm SHA256).Hash -ne [string] $tool.sha256) {
        throw "Pinned tool hash mismatch: $toolName"
    }
}
$dotnetRoot = [string] $toolchain.privateDotnetRoot
$dotnet = Join-Path $dotnetRoot 'dotnet.exe'
if (-not (Test-Path -LiteralPath $dotnet -PathType Leaf)) { throw "Pinned private .NET is missing: $dotnet" }
$python = (Get-Command py.exe -ErrorAction Stop).Source
$inputs = Get-Content -LiteralPath $inputsPath -Raw | ConvertFrom-Json
$moduleManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (-not [string]::Equals([string] $moduleManifest.version, $Version, [StringComparison]::Ordinal)) {
    throw "Requested version $Version differs from manifest version $($moduleManifest.version)."
}
$caprica = Join-Path $reposRoot ([string] $inputs.papyrusCompiler.relativePathFromRepos)
$flags = Join-Path $GameRoot ([string] $inputs.flags.relativePathFromGame)
if ((Get-FileHash -LiteralPath $caprica -Algorithm SHA256).Hash -ne [string] $inputs.papyrusCompiler.sha256) {
    throw 'Caprica hash differs from build-inputs.json.'
}
if ((Get-FileHash -LiteralPath $flags -Algorithm SHA256).Hash -ne [string] $inputs.flags.sha256) {
    throw 'Papyrus flags hash differs from build-inputs.json.'
}
$septimBaseline = $inputs.septimWeightBaseline
$septimBaselinePath = Join-Path $InstanceRoot ([string] $septimBaseline.sourceRelativePathFromInstance)
if (-not (Test-Path -LiteralPath $septimBaselinePath -PathType Leaf)) {
    throw "Pinned ECE Septim-weight baseline is missing: $septimBaselinePath"
}
if ((Get-Item -LiteralPath $septimBaselinePath).Length -ne [long] $septimBaseline.sourceBytes) {
    throw 'ECE Septim-weight baseline byte count differs from build-inputs.json.'
}
if ((Get-FileHash -LiteralPath $septimBaselinePath -Algorithm SHA256).Hash -ne
    [string] $septimBaseline.sourceSha256) {
    throw 'ECE Septim-weight baseline hash differs from build-inputs.json.'
}
foreach ($sourcePin in $inputs.mintCompatibilitySources) {
    $sourcePath = Join-Path $InstanceRoot ([string] $sourcePin.sourceRelativePathFromInstance)
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Pinned M.I.N.T. compatibility source is missing: $sourcePath"
    }
    if ((Get-Item -LiteralPath $sourcePath).Length -ne [long] $sourcePin.sourceBytes) {
        throw "$($sourcePin.script): pinned source byte count differs from build-inputs.json."
    }
    if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne
        [string] $sourcePin.sourceSha256) {
        throw "$($sourcePin.script): pinned source hash differs from build-inputs.json."
    }
}

$importFolders = [Collections.Generic.List[string]]::new()
$importFolders.Add((Join-Path $ownedRoot 'papyrus'))
foreach ($import in $inputs.papyrusImports) {
    $folder = if ($import.relativePathFromInstance) {
        Join-Path $InstanceRoot ([string] $import.relativePathFromInstance)
    } else {
        Join-Path $GameRoot ([string] $import.relativePathFromGame)
    }
    if (-not (Test-Path -LiteralPath $folder -PathType Container)) { throw "Papyrus import is missing: $folder" }
    $count = @(Get-ChildItem -LiteralPath $folder -File -Filter '*.psc').Count
    if ($count -ne [int] $import.pscFiles) { throw "$($import.name): expected $($import.pscFiles) PSC files, found $count." }
    $digest = Get-PscTreeDigest $folder
    if ($digest -ne [string] $import.treeSha256) { throw "$($import.name): source-tree hash differs from build-inputs.json." }
    $importFolders.Add($folder)
}

Reset-OwnedDirectory $work
$profileFolder = Join-Path (Join-Path $InstanceRoot 'profiles') $Profile
$pluginsFile = Join-Path $profileFolder 'plugins.txt'
$loadOrderFile = Join-Path $profileFolder 'loadorder.txt'
foreach ($required in @($pluginsFile, $loadOrderFile)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Profile file is missing: $required" }
}

# Effective order: base masters, Skyrim.ccc in official order, then active MO2
# plugins in loadorder.txt order. The owned output is never an input.
$active = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $pluginsFile) {
    $trimmed = $line.Trim()
    if ($trimmed.StartsWith('*')) { [void] $active.Add($trimmed.TrimStart('*')) }
}
$ordered = [Collections.Generic.List[string]]::new()
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
function Add-EffectivePlugin([string] $Name) {
    if ($Name -and $Name -ine $pluginName -and $Name -ine $regionalPursePluginName -and
        $seen.Add($Name)) { $ordered.Add("*$Name") }
}
foreach ($base in @('Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm')) {
    Add-EffectivePlugin $base
}
$ccc = Join-Path $GameRoot 'Skyrim.ccc'
if (Test-Path -LiteralPath $ccc) {
    foreach ($line in Get-Content -LiteralPath $ccc) { Add-EffectivePlugin $line.Trim().TrimStart('*') }
}
foreach ($line in Get-Content -LiteralPath $loadOrderFile) {
    $name = $line.Trim().TrimStart('*')
    if ($name -and -not $name.StartsWith('#') -and $active.Contains($name)) { Add-EffectivePlugin $name }
}
$missing = @($active | Where-Object {
    $_ -ine $pluginName -and $_ -ine $regionalPursePluginName -and -not $seen.Contains($_)
} | Sort-Object)
if ($missing.Count) { throw "loadorder.txt omits active plugins: $($missing -join ', ')" }
[IO.File]::WriteAllLines($effectiveLoadOrder, $ordered, [Text.UTF8Encoding]::new($false))

$processEnvironment = @{
    DOTNET_ROOT = $dotnetRoot
    DOTNET_ROOT_X64 = $dotnetRoot
    DOTNET_HOST_PATH = $dotnet
    DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    PATH = "$dotnetRoot;$env:PATH"
}

Invoke-HiddenProcess -FileName $dotnet -Arguments @('build', $project, '-c', 'Release',
    '-p:RestoreLockedMode=true', '-nologo') -WorkingDirectory $generatorFolder `
    -LogStem (Join-Path $work 'build') -Environment $processEnvironment | Out-Null

# Compile every owned script twice. Normalize Caprica's PEX header timestamp,
# source path, user and machine to audited release metadata. This keeps
# identical source byte-identical across worktrees, clone paths and builders.
$pexRuns = @{}
foreach ($packagedScriptName in $packagedScripts.Keys) {
    $pexRuns[$packagedScriptName] = [Collections.Generic.List[string]]::new()
}
foreach ($run in 1..2) {
    $outputFolder = Join-Path $work "papyrus-$run"
    New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
    foreach ($packagedScriptName in $packagedScripts.Keys) {
        $packagedSource = [string] $packagedScripts[$packagedScriptName]
        $compilerArguments = @('--ignorecwd', '--quiet', '--game', 'skyrim',
            '--import', ($importFolders -join ';'), '--flags', $flags, '--strict=1',
            '--enable-ck-optimizations=0', '--enable-debug-info=0', '--all-warnings-as-errors')
        $compilerArguments += @('--output', $outputFolder, $packagedSource)
        $compileLogStem = Join-Path $work "papyrus-$run-$packagedScriptName"
        Invoke-HiddenProcess -FileName $caprica -Arguments $compilerArguments `
            -WorkingDirectory $ownedRoot -LogStem $compileLogStem | Out-Null
        $pex = Join-Path $outputFolder "$packagedScriptName.pex"
        $normalizedSourceName = "$($inputs.papyrusCompiler.normalizedSourcePrefix)/$packagedScriptName.psc"
        Invoke-HiddenProcess -FileName $python -Arguments @('-3', $normalizer, $pex,
            '--source-name', $normalizedSourceName,
            '--user-name', ([string] $inputs.papyrusCompiler.normalizedUserName),
            '--machine-name', ([string] $inputs.papyrusCompiler.normalizedMachineName)) `
            -WorkingDirectory $ownedRoot -LogStem (Join-Path $work "normalize-pex-$run-$packagedScriptName") | Out-Null
        $pexRuns[$packagedScriptName].Add($pex)
    }
}
$pexHashes = @{}
foreach ($packagedScriptName in $packagedScripts.Keys) {
    $hashes = @($pexRuns[$packagedScriptName] | ForEach-Object {
        (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
    })
    if ($hashes[0] -ne $hashes[1]) {
        throw "$packagedScriptName PEX determinism failure: $($hashes -join ', ')"
    }
    $pexHashes[$packagedScriptName] = $hashes[0]
}

# Generate the main plugin twice through the profile's virtual filesystem, then
# build each companion from the exact paired main output. The companion only
# clones pinned Skyrim FLORs and links to reviewed source/main forms, so it does
# not resolve arbitrary VFS winners while building.
$pluginRuns = @()
$regionalPursePluginRuns = @()
foreach ($run in 1..2) {
    $outputFolder = Join-Path $work "generation-$run"
    New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
    $output = Join-Path $outputFolder $pluginName
    $pluginRuns += $output
    Invoke-Mo2Child -ChildPath $executable -ChildArguments @(
        'run-patcher', '--DataFolderPath', $dataFolder, '--GameRelease', 'SkyrimSE',
        '--LoadOrderFilePath', $effectiveLoadOrder, '--OutputPath', $output,
        '--ModKey', $pluginName, '--PatcherName', 'EnsrickCurrencyIntegrationPatch',
        '--PersistencePath', (Join-Path $outputFolder 'persistence'),
        '--ExtraDataFolder', $ownedRoot
    ) -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work "generation-$run") | Out-Null
    $regionalPurseOutput = Join-Path $outputFolder $regionalPursePluginName
    $regionalPursePluginRuns += $regionalPurseOutput
    Invoke-HiddenProcess -FileName $executable -Arguments @('--build-regional-purses',
        $dataFolder, $output, $policy, $regionalPurseOutput) -WorkingDirectory $generatorFolder `
        -LogStem (Join-Path $work "regional-purses-$run") -Environment $processEnvironment | Out-Null
}
$pluginHashes = @($pluginRuns | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
if ($pluginHashes[0] -ne $pluginHashes[1]) { throw "ESP determinism failure: $($pluginHashes -join ', ')" }
$regionalPursePluginHashes = @($regionalPursePluginRuns | ForEach-Object {
    (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
})
if ($regionalPursePluginHashes[0] -ne $regionalPursePluginHashes[1]) {
    throw "Regional-purse ESP determinism failure: $($regionalPursePluginHashes -join ', ')"
}

$packageScripts = Join-Path $package 'Scripts'
$packageSeq = Join-Path $package 'SEQ'
New-Item -ItemType Directory -Path $packageScripts, $packageSeq -Force | Out-Null
$packagePlugin = Join-Path $package $pluginName
$packageRegionalPursePlugin = Join-Path $package $regionalPursePluginName
$packagePexFiles = @{}
$packageSeqFile = Join-Path $packageSeq 'Ensrick Currency Integration Patch.seq'
$packageTranslation = Join-Path $package ([string] $inputs.translationOverride.path)
$packageTranslations = Split-Path -Parent $packageTranslation
Copy-Item -LiteralPath $pluginRuns[0] -Destination $packagePlugin -Force
Copy-Item -LiteralPath $regionalPursePluginRuns[0] -Destination $packageRegionalPursePlugin -Force
# The native single-ledger owner replaces every previously packaged ECE/Ohzer
# transaction PEX. Clear only this owned package's script payload before copying
# the deterministic four-script compatibility set.
foreach ($stalePex in @(Get-ChildItem -LiteralPath $packageScripts -File -Filter '*.pex')) {
    Assert-OwnedPath $stalePex.FullName
    Remove-Item -LiteralPath $stalePex.FullName -Force
}
foreach ($packagedScriptName in $packagedScripts.Keys) {
    $packagePexFiles[$packagedScriptName] = Join-Path $packageScripts "$packagedScriptName.pex"
    Copy-Item -LiteralPath $pexRuns[$packagedScriptName][0] `
        -Destination $packagePexFiles[$packagedScriptName] -Force
}
$packagePex = $packagePexFiles[$scriptName]
$moduleManifest.runtimePatch.sha256 = $pluginHashes[0]
$moduleManifest.runtimePatch.bytes = (Get-Item -LiteralPath $packagePlugin).Length
if (-not $moduleManifest.PSObject.Properties['regionalPursePatch']) {
    $moduleManifest | Add-Member -NotePropertyName regionalPursePatch -NotePropertyValue ([pscustomobject]@{})
}
$moduleManifest.regionalPursePatch = [ordered]@{
    plugin = $regionalPursePluginName
    sha256 = $regionalPursePluginHashes[0]
    bytes = (Get-Item -LiteralPath $packageRegionalPursePlugin).Length
    eslFlagged = $true
    records = 405
    ownedRecords = 405
    recordsByType = [ordered]@{ FLOR = 15; LVLI = 390 }
    directMasters = @('Skyrim.esm', 'Update.esm', 'BSAssets.esm',
        'exchangeCurrency_patch_COIN.esp', $pluginName)
    seqFileRelativeFormIds = @()
}
$moduleManifest.papyrusScripts = @($packagedScripts.Keys | ForEach-Object {
    [ordered]@{
        script = $_
        file = "Scripts/$_.pex"
        sha256 = [string] $pexHashes[$_]
        bytes = (Get-Item -LiteralPath $packagePexFiles[$_]).Length
        deterministicCompilations = 2
        normalizedCompileUnixTime = 946684800
    }
})
New-Item -ItemType Directory -Path $packageTranslations -Force | Out-Null
$translationLines = @($inputs.translationOverride.lines | ForEach-Object { [string] $_ })
$translationContent = ($translationLines -join "`r`n") + "`r`n"
[IO.File]::WriteAllText($packageTranslation, $translationContent, [Text.UnicodeEncoding]::new($false, $true))
$i4Override = $inputs.inventoryInjectorOverride
$i4Source = Join-Path $InstanceRoot ([string] $i4Override.sourceRelativePathFromInstance)
if (-not (Test-Path -LiteralPath $i4Source -PathType Leaf)) {
    throw "Pinned ECE I4 source is missing: $i4Source"
}
if ((Get-FileHash -LiteralPath $i4Source -Algorithm SHA256).Hash -ne [string] $i4Override.sourceSha256) {
    throw 'ECE I4 source hash differs from build-inputs.json.'
}
$i4SourceText = [IO.File]::ReadAllText($i4Source, [Text.UTF8Encoding]::new($false))
$i4Needle = [string] $i4Override.sourceText
$i4Replacement = [string] $i4Override.replacementText
$i4Occurrences = ([regex]::Matches($i4SourceText, [regex]::Escape($i4Needle))).Count
if ($i4Occurrences -ne [int] $i4Override.expectedReplacements) {
    throw "ECE I4 source has $i4Occurrences matching labels; expected $($i4Override.expectedReplacements)."
}
$packageI4 = Join-Path $package ([string] $i4Override.outputPath)
New-Item -ItemType Directory -Path (Split-Path -Parent $packageI4) -Force | Out-Null
[IO.File]::WriteAllText($packageI4, $i4SourceText.Replace($i4Needle, $i4Replacement),
    [Text.UTF8Encoding]::new($false))
$cdfOverride = $inputs.containerDistributionOverride
$cdfSource = Join-Path $InstanceRoot ([string] $cdfOverride.sourceRelativePathFromInstance)
if (-not (Test-Path -LiteralPath $cdfSource -PathType Leaf)) {
    throw "Pinned C.O.I.N. CDF source is missing: $cdfSource"
}
if ((Get-FileHash -LiteralPath $cdfSource -Algorithm SHA256).Hash -ne [string] $cdfOverride.sourceSha256) {
    throw 'C.O.I.N. CDF source hash differs from build-inputs.json.'
}
if ([string] $cdfOverride.mode -ne 'empty-mask') {
    throw 'C.O.I.N. CDF override must use the reviewed empty-mask mode.'
}
$packageCdf = Join-Path $package ([string] $cdfOverride.outputPath)
New-Item -ItemType Directory -Path (Split-Path -Parent $packageCdf) -Force | Out-Null
[IO.File]::WriteAllText($packageCdf, "{`n  `"rules`": []`n}`n", [Text.UTF8Encoding]::new($false))
if ((Get-Item -LiteralPath $packageCdf).Length -ne [long] $cdfOverride.outputBytes -or
    (Get-FileHash -LiteralPath $packageCdf -Algorithm SHA256).Hash -ne [string] $cdfOverride.outputSha256) {
    throw 'Generated C.O.I.N. CDF empty-mask bytes/hash differ from build-inputs.json.'
}
$cdfFolder = Split-Path -Parent $packageCdf
$cdfMasks = @(Get-ChildItem -LiteralPath $cdfFolder -File -Filter '*.json' | Sort-Object Name)
if ($cdfMasks.Count -ne 14) { throw "Expected exactly fourteen currency CDF masks, found $($cdfMasks.Count)." }
foreach ($cdfMask in $cdfMasks) {
    $cdfJson = Get-Content -LiteralPath $cdfMask.FullName -Raw | ConvertFrom-Json
    if (@($cdfJson.rules).Count -ne 0) {
        throw "$($cdfMask.Name): legacy CDF currency mutation remains active; native ownership requires an empty mask."
    }
}
$kidOverride = $inputs.keywordDistributorOverride
$kidSource = Join-Path $InstanceRoot ([string] $kidOverride.sourceRelativePathFromInstance)
if (-not (Test-Path -LiteralPath $kidSource -PathType Leaf)) {
    throw "Pinned ECE KID source is missing: $kidSource"
}
if ((Get-FileHash -LiteralPath $kidSource -Algorithm SHA256).Hash -ne [string] $kidOverride.sourceSha256) {
    throw 'ECE KID source hash differs from build-inputs.json.'
}
$kidSourceText = [IO.File]::ReadAllText($kidSource, [Text.UTF8Encoding]::new($false))
$kidNeedle = [string] $kidOverride.sourceText
$kidReplacement = [string] $kidOverride.replacementText
$kidOccurrences = ([regex]::Matches($kidSourceText, [regex]::Escape($kidNeedle))).Count
if ($kidOccurrences -ne [int] $kidOverride.expectedReplacements) {
    throw "ECE KID source has $kidOccurrences Gyldenhul assignments; expected $($kidOverride.expectedReplacements)."
}
$packageKid = Join-Path $package ([string] $kidOverride.outputPath)
[IO.File]::WriteAllText($packageKid, $kidSourceText.Replace($kidNeedle, $kidReplacement),
    [Text.UTF8Encoding]::new($false))
if ((Get-FileHash -LiteralPath $packageKid -Algorithm SHA256).Hash -ne [string] $kidOverride.outputSha256) {
    throw 'Generated ECE KID override hash differs from build-inputs.json.'
}
Invoke-HiddenProcess -FileName $executable -Arguments @('--write-seq', $packagePlugin, $packageSeqFile) `
    -WorkingDirectory $generatorFolder -LogStem (Join-Path $work 'seq') | Out-Null
$seqFiles = @(Get-ChildItem -LiteralPath $packageSeq -File -Filter '*.seq')
if ($seqFiles.Count -ne 1 -or $seqFiles[0].Name -ne 'Ensrick Currency Integration Patch.seq') {
    throw 'Only the main currency runtime quest may ship a SEQ; the regional-purse companion has no startup quest.'
}

$auditOutput = Join-Path $work 'plugin-audit.json'
Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit-plugin', $dataFolder,
    $effectiveLoadOrder, $packagePlugin, $policy, $packageSeqFile, $auditOutput) `
    -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work 'plugin-audit') | Out-Null
$audit = Get-Content -LiteralPath $auditOutput -Raw | ConvertFrom-Json
$moduleManifest.runtimePatch.records = [int] $audit.records
$moduleManifest.runtimePatch.ownedRecords = 1623
$moduleManifest.runtimePatch.recordsByType = [ordered]@{
    ACTI = 3; LVLI = 1605; MISC = 55; GLOB = 1; COBJ = 42
    QUST = 5; KYWD = 1; DIAL = 20; INFO = 40
}
$moduleManifest.runtimePatch.deletedRecords = [int] $audit.deletedRecords
$moduleManifest.runtimePatch.disabledCurrencyToIngotRecipes = [int] $audit.disabledCurrencyToIngotRecipeCount
$moduleManifest.runtimePatch.disabledModernBankRecipes = [int] $audit.disabledModernBankRecipeCount
$moduleManifest.runtimePatch.disabledMintExchangeInfos = @($audit.disabledMintExchangeInfos).Count
$moduleManifest.runtimePatch.backendRetargetedServiceInfos = @($audit.mintBackendConditionInfos).Count
$moduleManifest.runtimePatch.directMasters = @($audit.masters)
$moduleManifest.runtimePatch.seqFileRelativeFormIds = @([string] $audit.runtimeQuest.seqFileRelativeFormId)
$linkEnvelope = Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit-links',
    $dataFolder, $effectiveLoadOrder, $packagePlugin) -ChildWorkingDirectory $generatorFolder `
    -LogStem (Join-Path $work 'link-audit')
$linkLine = @($linkEnvelope.stdout -split "`r?`n" | Where-Object { $_.Trim().StartsWith('{"records"') })[0]
$linkAudit = $linkLine | ConvertFrom-Json
if ($linkAudit.unresolved.Count) { throw "Link audit found $($linkAudit.unresolved.Count) unresolved links." }
$regionalLinkEnvelope = Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit-links',
    $dataFolder, $effectiveLoadOrder, $packageRegionalPursePlugin, $packagePlugin) `
    -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work 'regional-purse-link-audit')
$regionalLinkLine = @($regionalLinkEnvelope.stdout -split "`r?`n" |
    Where-Object { $_.Trim().StartsWith('{"records"') })[0]
$regionalLinkAudit = $regionalLinkLine | ConvertFrom-Json
if ($regionalLinkAudit.unresolved.Count) {
    throw "Regional-purse link audit found $($regionalLinkAudit.unresolved.Count) unresolved links."
}

# Checked Spriggit serialize -> deserialize -> serialize semantic roundtrip for
# both independently loadable ESPFE outputs.
$spriggit = [string] $toolchain.tools.spriggit.path
$spriggitArgs = @('--GameRelease', 'SkyrimSE', '--PackageName', 'Spriggit.Yaml.Skyrim',
    '--PackageVersion', '0.41.0', '--Check', '--ErrorOnUnknown')
$spriggitDigests = @{}
foreach ($spriggitTarget in @(
    [pscustomobject]@{ Key = 'main'; Path = $packagePlugin },
    [pscustomobject]@{ Key = 'regional-purses'; Path = $packageRegionalPursePlugin }
)) {
    $key = [string] $spriggitTarget.Key
    $targetPath = [string] $spriggitTarget.Path
    $spriggitText = Join-Path $work "spriggit-$key-source"
    $roundtripPluginFolder = Join-Path $work "spriggit-$key-roundtrip"
    $roundtripText = Join-Path $work "spriggit-$key-roundtrip-text"
    New-Item -ItemType Directory -Path $spriggitText, $roundtripPluginFolder, $roundtripText -Force | Out-Null
    Invoke-HiddenProcess -FileName $spriggit -Arguments (@('serialize', '--InputPath', $targetPath,
        '--OutputPath', $spriggitText) + $spriggitArgs) -WorkingDirectory $ownedRoot `
        -LogStem (Join-Path $work "spriggit-$key-serialize") -Environment $processEnvironment | Out-Null
    $roundtripPlugin = Join-Path $roundtripPluginFolder ([IO.Path]::GetFileName($targetPath))
    Invoke-HiddenProcess -FileName $spriggit -Arguments @('deserialize', '--InputPath', $spriggitText,
        '--OutputPath', $roundtripPlugin, '--PackageName', 'Spriggit.Yaml.Skyrim',
        '--PackageVersion', '0.41.0', '--BackupDays', '0') -WorkingDirectory $ownedRoot `
        -LogStem (Join-Path $work "spriggit-$key-deserialize") -Environment $processEnvironment | Out-Null
    Invoke-HiddenProcess -FileName $spriggit -Arguments (@('serialize', '--InputPath', $roundtripPlugin,
        '--OutputPath', $roundtripText) + $spriggitArgs) -WorkingDirectory $ownedRoot `
        -LogStem (Join-Path $work "spriggit-$key-reserialize") -Environment $processEnvironment | Out-Null
    $spriggitDigest = Get-TreeDigest $spriggitText
    $roundtripDigest = Get-TreeDigest $roundtripText
    if ($spriggitDigest -ne $roundtripDigest) {
        throw "$key Spriggit semantic roundtrip differs: $spriggitDigest != $roundtripDigest"
    }
    $spriggitDigests[$key] = $spriggitDigest
}

# Independent binary/FLOR/probability gate. It reads the original Skyrim
# English STRINGS member directly from the pinned game archive in memory and
# must pass on the exact paired ESPs before either can enter a release archive.
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $ownedRoot '..\..'))
$purseGate = Join-Path $repositoryRoot 'audit\currency_purse_gate.py'
$purseAuditOutput = Join-Path $work 'regional-purse-independent-audit.json'
$runtimeConfig = Join-Path $package 'SKSE\Plugins\EnsrickCurrencyDenominations.json'
$skyrimMaster = Join-Path $dataFolder 'Skyrim.esm'
$skyrimInterfaceArchive = Join-Path $dataFolder 'Skyrim - Interface.bsa'
foreach ($required in @($purseGate, $runtimeConfig, $skyrimMaster, $skyrimInterfaceArchive)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Independent regional-purse audit input is missing: $required"
    }
}
Invoke-HiddenProcess -FileName $python -Arguments @('-3', $purseGate,
    '--companion', $packageRegionalPursePlugin, '--main', $packagePlugin,
    '--skyrim', $skyrimMaster, '--strings-archive', $skyrimInterfaceArchive,
    '--policy', $policy, '--config', $runtimeConfig, '--output', $purseAuditOutput) `
    -WorkingDirectory $repositoryRoot -LogStem (Join-Path $work 'regional-purse-independent-audit') | Out-Null
$purseProof = Get-Content -LiteralPath $purseAuditOutput -Raw | ConvertFrom-Json
if ([string] $purseProof.status -ne 'offline-binary-and-exact-probability-pass; not in-game verification' -or
    [string] $purseProof.companionSha256 -ne $regionalPursePluginHashes[0] -or
    [string] $purseProof.mainSha256 -ne $pluginHashes[0] -or
    [int] $purseProof.ownedRecords -ne 405 -or [int] $purseProof.floraClones -ne 15 -or
    [int] $purseProof.reachableLists -ne 390 -or @($purseProof.purses).Count -ne 15) {
    throw 'Independent regional-purse binary/FLOR/probability audit contract failed.'
}

# Static package gate and two archive creations must be byte-identical.
$bosGenerator = Join-Path $ownedRoot 'generate_bos.py'
if (-not (Test-Path -LiteralPath $bosGenerator -PathType Leaf)) {
    throw "Deterministic BOS generator is missing: $bosGenerator"
}
Invoke-HiddenProcess -FileName $python -Arguments @('-3', $bosGenerator, '--check') `
    -WorkingDirectory $ownedRoot -LogStem (Join-Path $work 'bos-check') | Out-Null
Write-ModuleManifestAtomic
Invoke-HiddenProcess -FileName $python -Arguments @('-3', (Join-Path $ownedRoot 'validate.py')) `
    -WorkingDirectory $ownedRoot -LogStem (Join-Path $work 'validate') | Out-Null
$buildScript = Join-Path $ownedRoot 'build.py'
Invoke-HiddenProcess -FileName $python -Arguments @('-3', $buildScript) -WorkingDirectory $ownedRoot `
    -LogStem (Join-Path $work 'archive-1') | Out-Null
$archive = Join-Path $work "Ensrick-Regional-Currency-Integration-$Version.zip"
$archiveHash1 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
Invoke-HiddenProcess -FileName $python -Arguments @('-3', $buildScript) -WorkingDirectory $ownedRoot `
    -LogStem (Join-Path $work 'archive-2') | Out-Null
$archiveHash2 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
if ($archiveHash1 -ne $archiveHash2) { throw "Archive determinism failure: $archiveHash1 != $archiveHash2" }
$archiveBytes = (Get-Item -LiteralPath $archive).Length
$packageFileCount = @(Get-ChildItem -LiteralPath $package -Recurse -File).Count

# Commit the release receipt atomically from the archive that was actually
# produced. This prevents package changes from leaving hand-maintained stale
# manifest metadata behind.
$moduleManifest.archive.fileName = [IO.Path]::GetFileName($archive)
$moduleManifest.archive.files = $packageFileCount
$moduleManifest.archive.bytes = $archiveBytes
$moduleManifest.archive.sha256 = $archiveHash1
Write-ModuleManifestAtomic
$releaseManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ([string] $releaseManifest.archive.fileName -ne [IO.Path]::GetFileName($archive) -or
    [int] $releaseManifest.archive.files -ne $packageFileCount -or
    [long] $releaseManifest.archive.bytes -ne $archiveBytes -or
    [string] $releaseManifest.archive.sha256 -ne $archiveHash1) {
    throw 'Atomic release-manifest verification failed.'
}

$result = [ordered]@{
    schemaVersion = 1
    version = $Version
    profile = $Profile
    effectiveLoadOrderEntries = $ordered.Count
    plugin = $pluginName
    pluginSha256 = $pluginHashes[0]
    pluginBytes = (Get-Item -LiteralPath $packagePlugin).Length
    papyrusScripts = @($packagedScripts.Keys | ForEach-Object {
        [ordered]@{
            path = "Scripts/$_.pex"
            sha256 = [string] $pexHashes[$_]
            bytes = (Get-Item -LiteralPath $packagePexFiles[$_]).Length
        }
    })
    deterministicPluginRuns = 2
    deterministicRegionalPursePluginRuns = 2
    deterministicPexRuns = 2
    records = [int] $audit.records
    disabledRecipes = [int] $audit.disabledRecipeCount
    deletedRecords = [int] $audit.deletedRecords
    linksChecked = [int] $linkAudit.linksChecked
    engineIntrinsicLinks = [int] $linkAudit.engineIntrinsic.Count
    unresolvedLinks = [int] $linkAudit.unresolved.Count
    seqFileRelativeFormIds = @([string] $audit.runtimeQuest.seqFileRelativeFormId)
    regionalPursePlugin = $regionalPursePluginName
    regionalPursePluginSha256 = $regionalPursePluginHashes[0]
    regionalPursePluginBytes = (Get-Item -LiteralPath $packageRegionalPursePlugin).Length
    regionalPurseRecords = [int] $regionalLinkAudit.records
    regionalPurseLinksChecked = [int] $regionalLinkAudit.linksChecked
    regionalPurseUnresolvedLinks = [int] $regionalLinkAudit.unresolved.Count
    regionalPurseIndependentAudit = $purseAuditOutput
    regionalPurseIndependentAuditSha256 = (Get-FileHash -LiteralPath $purseAuditOutput -Algorithm SHA256).Hash
    regionalPurseVerifierSha256 = [string] $purseProof.verifierSha256
    spriggitTreeSha256 = [string] $spriggitDigests['main']
    regionalPurseSpriggitTreeSha256 = [string] $spriggitDigests['regional-purses']
    archive = $archive
    archiveSha256 = $archiveHash1
    archiveBytes = $archiveBytes
    packageFiles = $packageFileCount
    generatedUtc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
}
[IO.File]::WriteAllText((Join-Path $work 'regeneration-result.json'),
    (($result | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 5
