[CmdletBinding()]
param(
    [string]$DataFolder = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data',
    [string]$LoadOrderFile = "$env:LOCALAPPDATA\Skyrim Special Edition\Plugins.txt",
    [string]$OutputPath = "$PSScriptRoot\package\KatanaTwoHandedPatch.esp",
    [Parameter(Mandatory)]
    [string]$PatcherFolder
)

$ErrorActionPreference = 'Stop'

$patcher = Join-Path $PatcherFolder 'KatanaTwoHandedPatcher.exe'
$settingsFolder = Join-Path $PatcherFolder 'Data'
$persistence = Join-Path $PSScriptRoot 'work\persistence'
$outputDirectory = Split-Path -Parent $OutputPath
$effectiveLoadOrder = Join-Path $PSScriptRoot 'work\plugins-with-creation-club.txt'
$gameRoot = Split-Path -Parent $DataFolder
$creationClubFile = Join-Path $gameRoot 'Skyrim.ccc'

foreach ($requiredPath in @($patcher, $DataFolder, $LoadOrderFile, $settingsFolder)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required path does not exist: $requiredPath"
    }
}

New-Item -ItemType Directory -Force -Path $outputDirectory, $persistence | Out-Null

# Skyrim's official Creation Club load order lives in Skyrim.ccc and may not be
# repeated in plugins.txt. Synthesis's direct CLI expects one explicit list.
$orderedPlugins = [System.Collections.Generic.List[string]]::new()
$seenPlugins = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase)

if (Test-Path -LiteralPath $creationClubFile) {
    foreach ($line in Get-Content -LiteralPath $creationClubFile) {
        $pluginName = $line.Trim().TrimStart('*')
        if ($pluginName -and $seenPlugins.Add($pluginName)) {
            $orderedPlugins.Add("*$pluginName")
        }
    }
}

foreach ($line in Get-Content -LiteralPath $LoadOrderFile) {
    $trimmedLine = $line.Trim()
    if (-not $trimmedLine -or $trimmedLine.StartsWith('#')) {
        continue
    }

    $pluginName = $trimmedLine.TrimStart('*')
    if ($seenPlugins.Add($pluginName)) {
        $orderedPlugins.Add($trimmedLine)
    }
}

[System.IO.File]::WriteAllLines($effectiveLoadOrder, $orderedPlugins)

& $patcher run-patcher `
    --DataFolderPath $DataFolder `
    --ExtraDataFolder $settingsFolder `
    --GameRelease SkyrimSE `
    --LoadOrderFilePath $effectiveLoadOrder `
    --OutputPath $OutputPath `
    --ModKey KatanaTwoHandedPatch.esp `
    --PatcherName KatanaTwoHandedPatch `
    --PersistencePath $persistence

if ($LASTEXITCODE -ne 0) {
    throw "Katana patch generation failed with exit code $LASTEXITCODE"
}

Write-Host "Generated $OutputPath"
