#requires -Version 7.0
<#
Rebuild "Ensrick - Tomebound Redundancy Patch.esp" from the committed spriggit/ tree.

  pwsh ./mods/tomebound-redundancy/regenerate.ps1
  pwsh ./mods/tomebound-redundancy/regenerate.ps1 -ToolchainManifest ../../toolchain.json

The YAML tree is the source of truth; the plugin is a build artifact. This script
verifies the pinned Spriggit hash, builds twice, and requires the two builds to be
byte-identical before it keeps either of them.

To regenerate the YAML tree itself (only needed when Tomebound or Apocalypse are
updated), serialize both mods with Spriggit and run build_spriggit.py; see README.

Nothing here deletes recursively: an existing package/ is renamed to
package.bak.v<stamp> (repo rule #1).
#>
[CmdletBinding()]
param(
    [string] $ToolchainManifest = (Join-Path $PSScriptRoot '../../toolchain.json')
)

$ErrorActionPreference = 'Stop'
$pluginName = 'Ensrick - Tomebound Redundancy Patch.esp'
$ownedRoot  = [System.IO.Path]::GetFullPath($PSScriptRoot)
$spriggitIn = Join-Path $PSScriptRoot 'spriggit'
$package    = Join-Path $PSScriptRoot 'package'
$output     = Join-Path $package $pluginName
$stamp      = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')

function Assert-OwnedPath([string] $Path) {
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($ownedRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to touch a path outside the owned patch folder: $resolved"
    }
}

$manifest = Get-Content -LiteralPath $ToolchainManifest -Raw | ConvertFrom-Json
$spriggit = $manifest.tools.spriggit
if (-not (Test-Path -LiteralPath $spriggit.path)) { throw "Spriggit not found at $($spriggit.path)" }
$have = (Get-FileHash -LiteralPath $spriggit.path -Algorithm SHA256).Hash
if ($have -ne $spriggit.sha256) {
    throw "Spriggit hash mismatch. Expected $($spriggit.sha256), found $have."
}
Write-Host "Spriggit $($spriggit.version) verified."

if (-not (Test-Path -LiteralPath (Join-Path $spriggitIn 'RecordData.yaml'))) {
    throw "No spriggit source tree at $spriggitIn"
}

# Rename, never recurse-delete.
Assert-OwnedPath $package
if (Test-Path -LiteralPath $package) {
    Rename-Item -LiteralPath $package -NewName ("package.bak.v$stamp")
}
New-Item -ItemType Directory -Path $package -Force | Out-Null

$scratch = Join-Path ([System.IO.Path]::GetTempPath()) "tbr-$stamp"
New-Item -ItemType Directory -Path $scratch -Force | Out-Null
$second = Join-Path $scratch $pluginName

foreach ($target in @($output, $second)) {
    & $spriggit.path deserialize -i $spriggitIn -o $target `
        -p Spriggit.Yaml.Skyrim -v $spriggit.version | Out-Null
    if (-not (Test-Path -LiteralPath $target)) { throw "Spriggit produced no plugin at $target" }
}

$a = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash
$b = (Get-FileHash -LiteralPath $second -Algorithm SHA256).Hash
if ($a -ne $b) { throw "Non-deterministic build: $a vs $b" }

# ESL flag (0x200) must be set: this patch must never consume a full plugin slot.
$header = [System.IO.File]::ReadAllBytes($output)[8..11]
$flags  = [BitConverter]::ToUInt32($header, 0)
if (-not ($flags -band 0x200)) { throw "Output is not ESL-flagged (header flags 0x{0:X8})" -f $flags }

[pscustomobject]@{
    plugin       = $pluginName
    sha256       = $a
    bytes        = (Get-Item -LiteralPath $output).Length
    eslFlagged   = $true
    deterministic = $true
} | ConvertTo-Json
