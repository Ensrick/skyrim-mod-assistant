#requires -Version 7.0
<#
Rebuild and validate the owned currency integration package without modifying
vendor mod folders or the live MO2 profile.

  pwsh ./mods/currency-integration/regenerate.ps1 `
    -ToolchainManifest ./toolchain.json `
    -InstanceRoot ../mo2-instances/skyrim-se `
    -GameRoot "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition"

The pipeline verifies pinned tools and Papyrus inputs, compiles all three packaged
helpers twice, normalizes deterministic PEX header metadata, generates the ESP twice through
the MO2 VFS, checks exact records/links/SEQ, performs a checked Spriggit semantic
roundtrip, and creates the deterministic archive twice.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $ToolchainManifest,
    [Parameter(Mandatory)] [string] $InstanceRoot,
    [Parameter(Mandatory)] [string] $GameRoot,
    [string] $Profile = 'Default',
    [string] $Version = '0.2.5'
)

$ErrorActionPreference = 'Stop'
$pluginName = 'Ensrick Currency Integration Patch.esp'
$scriptName = 'Ensrick_CurrencyRuntimeDefaultsAlias'
$ohzerScriptName = 'Ensrick_OhzerCurrencyScript'
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
$source = Join-Path $ownedRoot "papyrus\$scriptName.psc"
$ohzerSource = Join-Path $ownedRoot "papyrus\$ohzerScriptName.psc"
$madranShimSource = Join-Path $ownedRoot "papyrus\$madranShimName.psc"
$ownedScripts = [ordered]@{
    $scriptName = $source
    $ohzerScriptName = $ohzerSource
    $madranShimName = $madranShimSource
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

foreach ($required in @($toolchainManifestPath, $InstanceRoot, $GameRoot, $dataFolder, $project,
        $policy, $inputsPath, $source, $ohzerSource, $madranShimSource, $normalizer, $package)) {
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
    if ($Name -and $Name -ine $pluginName -and $seen.Add($Name)) { $ordered.Add("*$Name") }
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
$missing = @($active | Where-Object { $_ -ine $pluginName -and -not $seen.Contains($_) } | Sort-Object)
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
foreach ($ownedScriptName in $ownedScripts.Keys) {
    $pexRuns[$ownedScriptName] = [Collections.Generic.List[string]]::new()
}
foreach ($run in 1..2) {
    $outputFolder = Join-Path $work "papyrus-$run"
    New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
    foreach ($ownedScriptName in $ownedScripts.Keys) {
        $ownedSource = [string] $ownedScripts[$ownedScriptName]
        Invoke-HiddenProcess -FileName $caprica -Arguments @('--ignorecwd', '--quiet', '--game', 'skyrim',
            '--import', ($importFolders -join ';'), '--flags', $flags, '--strict=1',
            '--all-warnings-as-errors', '--enable-ck-optimizations=0', '--enable-debug-info=0',
            '--output', $outputFolder, $ownedSource) -WorkingDirectory $ownedRoot `
            -LogStem (Join-Path $work "papyrus-$run-$ownedScriptName") | Out-Null
        $pex = Join-Path $outputFolder "$ownedScriptName.pex"
        $normalizedSourceName = "$($inputs.papyrusCompiler.normalizedSourcePrefix)/$ownedScriptName.psc"
        Invoke-HiddenProcess -FileName $python -Arguments @('-3', $normalizer, $pex,
            '--source-name', $normalizedSourceName,
            '--user-name', ([string] $inputs.papyrusCompiler.normalizedUserName),
            '--machine-name', ([string] $inputs.papyrusCompiler.normalizedMachineName)) `
            -WorkingDirectory $ownedRoot -LogStem (Join-Path $work "normalize-pex-$run-$ownedScriptName") | Out-Null
        $pexRuns[$ownedScriptName].Add($pex)
    }
}
$pexHashes = @{}
foreach ($ownedScriptName in $ownedScripts.Keys) {
    $hashes = @($pexRuns[$ownedScriptName] | ForEach-Object {
        (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
    })
    if ($hashes[0] -ne $hashes[1]) {
        throw "$ownedScriptName PEX determinism failure: $($hashes -join ', ')"
    }
    $pexHashes[$ownedScriptName] = $hashes[0]
}

# Generate the plugin twice through the profile's virtual filesystem.
$pluginRuns = @()
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
}
$pluginHashes = @($pluginRuns | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash })
if ($pluginHashes[0] -ne $pluginHashes[1]) { throw "ESP determinism failure: $($pluginHashes -join ', ')" }

$packageScripts = Join-Path $package 'Scripts'
$packageSeq = Join-Path $package 'SEQ'
New-Item -ItemType Directory -Path $packageScripts, $packageSeq -Force | Out-Null
$packagePlugin = Join-Path $package $pluginName
$packagePex = Join-Path $packageScripts "$scriptName.pex"
$packageOhzerPex = Join-Path $packageScripts "$ohzerScriptName.pex"
$packageMadranShimPex = Join-Path $packageScripts "$madranShimName.pex"
$packageSeqFile = Join-Path $packageSeq 'Ensrick Currency Integration Patch.seq'
$packageTranslation = Join-Path $package ([string] $inputs.translationOverride.path)
$packageTranslations = Split-Path -Parent $packageTranslation
Copy-Item -LiteralPath $pluginRuns[0] -Destination $packagePlugin -Force
Copy-Item -LiteralPath $pexRuns[$scriptName][0] -Destination $packagePex -Force
Copy-Item -LiteralPath $pexRuns[$ohzerScriptName][0] -Destination $packageOhzerPex -Force
Copy-Item -LiteralPath $pexRuns[$madranShimName][0] -Destination $packageMadranShimPex -Force
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
$cdfSourceText = [IO.File]::ReadAllText($cdfSource, [Text.UTF8Encoding]::new($false))
$cdfNeedle = [string] $cdfOverride.sourceText
$cdfReplacement = [string] $cdfOverride.replacementText
$cdfOccurrences = ([regex]::Matches($cdfSourceText, [regex]::Escape($cdfNeedle))).Count
if ($cdfOccurrences -ne [int] $cdfOverride.expectedReplacements) {
    throw "C.O.I.N. CDF source has $cdfOccurrences malformed Drakr removals; expected $($cdfOverride.expectedReplacements)."
}
$packageCdf = Join-Path $package ([string] $cdfOverride.outputPath)
New-Item -ItemType Directory -Path (Split-Path -Parent $packageCdf) -Force | Out-Null
[IO.File]::WriteAllText($packageCdf, $cdfSourceText.Replace($cdfNeedle, $cdfReplacement),
    [Text.UTF8Encoding]::new($false))
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

$auditOutput = Join-Path $work 'plugin-audit.json'
Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit-plugin', $dataFolder,
    $effectiveLoadOrder, $packagePlugin, $policy, $packageSeqFile, $auditOutput) `
    -ChildWorkingDirectory $generatorFolder -LogStem (Join-Path $work 'plugin-audit') | Out-Null
$linkEnvelope = Invoke-Mo2Child -ChildPath $executable -ChildArguments @('--audit-links',
    $dataFolder, $effectiveLoadOrder, $packagePlugin) -ChildWorkingDirectory $generatorFolder `
    -LogStem (Join-Path $work 'link-audit')
$linkLine = @($linkEnvelope.stdout -split "`r?`n" | Where-Object { $_.Trim().StartsWith('{"records"') })[0]
$linkAudit = $linkLine | ConvertFrom-Json
if ($linkAudit.unresolved.Count) { throw "Link audit found $($linkAudit.unresolved.Count) unresolved links." }

# Checked Spriggit serialize -> deserialize -> serialize semantic roundtrip.
$spriggit = [string] $toolchain.tools.spriggit.path
$spriggitText = Join-Path $work 'spriggit-source'
$roundtripPluginFolder = Join-Path $work 'spriggit-roundtrip'
$roundtripText = Join-Path $work 'spriggit-roundtrip-text'
New-Item -ItemType Directory -Path $spriggitText, $roundtripPluginFolder, $roundtripText -Force | Out-Null
$spriggitArgs = @('--GameRelease', 'SkyrimSE', '--PackageName', 'Spriggit.Yaml.Skyrim',
    '--PackageVersion', '0.41.0', '--Check', '--ErrorOnUnknown')
Invoke-HiddenProcess -FileName $spriggit -Arguments (@('serialize', '--InputPath', $packagePlugin,
    '--OutputPath', $spriggitText) + $spriggitArgs) -WorkingDirectory $ownedRoot `
    -LogStem (Join-Path $work 'spriggit-serialize') -Environment $processEnvironment | Out-Null
$roundtripPlugin = Join-Path $roundtripPluginFolder $pluginName
Invoke-HiddenProcess -FileName $spriggit -Arguments @('deserialize', '--InputPath', $spriggitText,
    '--OutputPath', $roundtripPlugin, '--PackageName', 'Spriggit.Yaml.Skyrim',
    '--PackageVersion', '0.41.0', '--BackupDays', '0') -WorkingDirectory $ownedRoot `
    -LogStem (Join-Path $work 'spriggit-deserialize') -Environment $processEnvironment | Out-Null
Invoke-HiddenProcess -FileName $spriggit -Arguments (@('serialize', '--InputPath', $roundtripPlugin,
    '--OutputPath', $roundtripText) + $spriggitArgs) -WorkingDirectory $ownedRoot `
    -LogStem (Join-Path $work 'spriggit-reserialize') -Environment $processEnvironment | Out-Null
$spriggitDigest = Get-TreeDigest $spriggitText
$roundtripDigest = Get-TreeDigest $roundtripText
if ($spriggitDigest -ne $roundtripDigest) {
    throw "Spriggit semantic roundtrip differs: $spriggitDigest != $roundtripDigest"
}

# Static package gate and two archive creations must be byte-identical.
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
$manifestTemp = "$manifestPath.tmp.$stamp"
Assert-OwnedPath $manifestTemp
[IO.File]::WriteAllText($manifestTemp,
    (($moduleManifest | ConvertTo-Json -Depth 12) + "`n"), [Text.UTF8Encoding]::new($false))
[IO.File]::Move($manifestTemp, $manifestPath, $true)
$releaseManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ([string] $releaseManifest.archive.fileName -ne [IO.Path]::GetFileName($archive) -or
    [int] $releaseManifest.archive.files -ne $packageFileCount -or
    [long] $releaseManifest.archive.bytes -ne $archiveBytes -or
    [string] $releaseManifest.archive.sha256 -ne $archiveHash1) {
    throw 'Atomic release-manifest verification failed.'
}

$audit = Get-Content -LiteralPath $auditOutput -Raw | ConvertFrom-Json
$result = [ordered]@{
    schemaVersion = 1
    version = $Version
    profile = $Profile
    effectiveLoadOrderEntries = $ordered.Count
    plugin = $pluginName
    pluginSha256 = $pluginHashes[0]
    pluginBytes = (Get-Item -LiteralPath $packagePlugin).Length
    pex = "Scripts/$scriptName.pex"
    pexSha256 = [string] $pexHashes[$scriptName]
    pexBytes = (Get-Item -LiteralPath $packagePex).Length
    ownedScripts = @(
        [ordered]@{
            path = "Scripts/$scriptName.pex"
            sha256 = [string] $pexHashes[$scriptName]
            bytes = (Get-Item -LiteralPath $packagePex).Length
        },
        [ordered]@{
            path = "Scripts/$ohzerScriptName.pex"
            sha256 = [string] $pexHashes[$ohzerScriptName]
            bytes = (Get-Item -LiteralPath $packageOhzerPex).Length
        },
        [ordered]@{
            path = "Scripts/$madranShimName.pex"
            sha256 = [string] $pexHashes[$madranShimName]
            bytes = (Get-Item -LiteralPath $packageMadranShimPex).Length
        }
    )
    deterministicPluginRuns = 2
    deterministicPexRuns = 2
    records = [int] $audit.records
    disabledRecipes = [int] $audit.disabledRecipeCount
    deletedRecords = [int] $audit.deletedRecords
    linksChecked = [int] $linkAudit.linksChecked
    engineIntrinsicLinks = [int] $linkAudit.engineIntrinsic.Count
    unresolvedLinks = [int] $linkAudit.unresolved.Count
    seqFileRelativeFormIds = @(
        [string] $audit.runtimeQuest.seqFileRelativeFormId
        [string] $audit.ohzerQuest.seqFileRelativeFormId
    )
    spriggitTreeSha256 = $spriggitDigest
    archive = $archive
    archiveSha256 = $archiveHash1
    archiveBytes = $archiveBytes
    packageFiles = $packageFileCount
    generatedUtc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
}
[IO.File]::WriteAllText((Join-Path $work 'regeneration-result.json'),
    (($result | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 5
