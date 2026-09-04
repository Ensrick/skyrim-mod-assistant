#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Instance = 'C:\Users\danjo\source\repos\mo2-instances\skyrim-se',
    [string]$Profile = 'Default',
    [string]$Configuration = 'Release',
    [string]$OutputPath = "$PSScriptRoot\artifacts\WeaponBalancePatch.esp"
)

$ErrorActionPreference = 'Stop'

function ConvertTo-Win32CommandLineArgument {
    param([AllowEmptyString()][string]$Value)

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }

    $quoted = [System.Text.StringBuilder]::new()
    [void]$quoted.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }
        if ($character -eq '"') {
            [void]$quoted.Append(('\' * (($backslashes * 2) + 1)))
            [void]$quoted.Append('"')
        } else {
            [void]$quoted.Append(('\' * $backslashes))
            [void]$quoted.Append($character)
        }
        $backslashes = 0
    }
    [void]$quoted.Append(('\' * ($backslashes * 2)))
    [void]$quoted.Append('"')
    return $quoted.ToString()
}

$project = Join-Path $PSScriptRoot 'src\WeaponBalancePatcher\WeaponBalancePatcher.csproj'
$patcherFolder = Join-Path $PSScriptRoot "src\WeaponBalancePatcher\bin\$Configuration\net9.0"
$patcher = Join-Path $patcherFolder 'WeaponBalancePatcher.exe'
$settingsFolder = Join-Path $patcherFolder 'Data'
$mo2 = Join-Path $Instance 'MO2Headless.exe'
$profileFolder = Join-Path (Join-Path $Instance 'profiles') $Profile
$pluginsFile = Join-Path $profileFolder 'plugins.txt'
$ini = Join-Path $Instance 'ModOrganizer.ini'
$workFolder = Join-Path $PSScriptRoot 'work'
$effectiveLoadOrder = Join-Path $workFolder 'plugins-with-creation-club.txt'
$persistence = Join-Path $workFolder 'persistence'
$logPath = Join-Path $workFolder 'generation.log'

foreach ($required in @($project, $mo2, $pluginsFile, $ini)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file does not exist: $required"
    }
}

$gamePathLine = Get-Content -LiteralPath $ini |
    Where-Object { $_ -match '^gamePath=' } |
    Select-Object -First 1
if (-not $gamePathLine) {
    throw "ModOrganizer.ini has no gamePath entry: $ini"
}

$serializedGamePath = $gamePathLine.Substring('gamePath='.Length)
if ($serializedGamePath -match '^@ByteArray\((?<path>.*)\)$') {
    # Current MO2 writes Qt's @ByteArray(...) form and escapes path separators.
    $gameRoot = $Matches.path.Replace('\\', '\')
} else {
    # Retain compatibility with older local instances that stored this value as Base64.
    try {
        $gameRoot = [System.Text.Encoding]::UTF8.GetString(
            [System.Convert]::FromBase64String($serializedGamePath))
    } catch {
        throw "Unsupported gamePath encoding in ${ini}: $serializedGamePath"
    }
}
if (-not [System.IO.Path]::IsPathFullyQualified($gameRoot)) {
    throw "Decoded gamePath is not absolute: $gameRoot"
}
$dataFolder = Join-Path $gameRoot 'Data'
$creationClubFile = Join-Path $gameRoot 'Skyrim.ccc'

New-Item -ItemType Directory -Force -Path (
    Split-Path -Parent $OutputPath), $workFolder, $persistence | Out-Null

Push-Location $PSScriptRoot
try {
    dotnet restore $project --locked-mode --nologo
    if ($LASTEXITCODE -ne 0) {
        throw "Patcher restore failed with exit code $LASTEXITCODE"
    }
    dotnet build $project -c $Configuration --nologo --no-restore
    if ($LASTEXITCODE -ne 0) {
        throw "Patcher build failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

foreach ($required in @($patcher, $settingsFolder, $dataFolder)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required generated/runtime path does not exist: $required"
    }
}

$orderedPlugins = [System.Collections.Generic.List[string]]::new()
$seenPlugins = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase)

if (Test-Path -LiteralPath $creationClubFile -PathType Leaf) {
    foreach ($line in Get-Content -LiteralPath $creationClubFile) {
        $pluginName = $line.Trim().TrimStart('*')
        if ($pluginName -and $seenPlugins.Add($pluginName)) {
            $orderedPlugins.Add("*$pluginName")
        }
    }
}

foreach ($line in Get-Content -LiteralPath $pluginsFile) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith('#')) {
        continue
    }
    $pluginName = $trimmed.TrimStart('*')
    if ($seenPlugins.Add($pluginName)) {
        $orderedPlugins.Add($trimmed)
    }
}

[System.IO.File]::WriteAllLines($effectiveLoadOrder, $orderedPlugins)

$toolArguments = @(
    'run-patcher',
    '--DataFolderPath', $dataFolder,
    '--ExtraDataFolder', $settingsFolder,
    '--GameRelease', 'SkyrimSE',
    '--LoadOrderFilePath', $effectiveLoadOrder,
    '--OutputPath', $OutputPath,
    '--ModKey', 'WeaponBalancePatch.esp',
    '--PatcherName', 'WeaponBalancePatch',
    '--PersistencePath', $persistence
)
$childArguments = ($toolArguments | ForEach-Object {
    ConvertTo-Win32CommandLineArgument ([string]$_)
}) -join ' '

$result = & $mo2 --root $Instance --profile $Profile --timeout 600 run $patcher `
    --arguments $childArguments --cwd $patcherFolder 2>&1
$exitCode = $LASTEXITCODE
$result | Tee-Object -FilePath $logPath
if ($exitCode -ne 0) {
    throw "VFS generation failed with exit code $exitCode. See $logPath"
}

if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
    throw "Patcher reported success but did not create $OutputPath"
}

Write-Host "Generated $OutputPath"
Write-Host "SHA256 $((Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath).Hash)"
