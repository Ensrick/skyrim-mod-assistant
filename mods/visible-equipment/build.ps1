[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$CommonLibRoot,
    [Parameter(Mandatory)][string]$VcpkgRoot,
    [Parameter(Mandatory)][string]$Cmake,
    [Parameter(Mandatory)][string]$BuildDirectory,
    [string]$Generator = '',
    [switch]$AllowUnpinnedCommonLib
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$source = $PSScriptRoot
$build = [IO.Path]::GetFullPath($BuildDirectory)
if (-not $Generator) {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    if (-not (Test-Path -LiteralPath $vswhere)) { throw 'vswhere unavailable; specify a supported Generator' }
    $version = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion
    if ($LASTEXITCODE -ne 0 -or -not $version) { throw 'No installed x64 MSVC toolchain found' }
    $major = ([version]($version | Select-Object -First 1)).Major
    $capabilities = & $Cmake -E capabilities | ConvertFrom-Json
    $matches = @($capabilities.generators | Where-Object name -Match "^Visual Studio $major ")
    if ($matches.Count -ne 1) { throw "CMake has no unambiguous generator for installed Visual Studio major $major" }
    $Generator = $matches[0].name
}
$toolchain = Join-Path $VcpkgRoot 'scripts/buildsystems/vcpkg.cmake'
if (-not (Test-Path -LiteralPath $toolchain)) { throw "vcpkg toolchain missing: $toolchain" }
if (-not (Test-Path -LiteralPath (Join-Path $CommonLibRoot 'CMakeLists.txt'))) { throw "CommonLibSSE-NG checkout missing: $CommonLibRoot" }

# The same global flags CommonLibSSE-NG's own presets use; per-target warnings
# and /Brepro are set in CMakeLists.txt so the library is not built /WX.
$cxxFlags = '/permissive- /Zc:preprocessor /EHsc /MP -DWIN32_LEAN_AND_MEAN -DNOMINMAX -DUNICODE -D_UNICODE'
$configureArgs = @(
    '-S', $source, '-B', $build, '-G', $Generator, '-A', 'x64',
    "-DCOMMONLIB_ROOT=$CommonLibRoot",
    "-DCMAKE_TOOLCHAIN_FILE=$toolchain",
    '-DVCPKG_TARGET_TRIPLET=x64-windows-static',
    "-DCMAKE_CXX_FLAGS=$cxxFlags"
)
if ($AllowUnpinnedCommonLib) { $configureArgs += '-DVISIBLE_EQUIPMENT_ALLOW_UNPINNED_COMMONLIB=ON' }
& $Cmake @configureArgs
if ($LASTEXITCODE -ne 0) { throw 'Configure failed' }
& $Cmake --build $build --config Release --parallel
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
& (Join-Path (Split-Path $Cmake) 'ctest.exe') --test-dir $build -C Release --output-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }

$package = Join-Path $build 'VisibleEquipment-0.0.1-win64.zip'
if (Test-Path -LiteralPath $package) { throw "Package exists; choose a fresh build directory: $package" }
$share = Join-Path $build 'vcpkg_installed/x64-windows-static/share'
$files = [ordered]@{
    'SKSE/Plugins/VisibleEquipment.dll' = Join-Path $build 'Release/VisibleEquipment.dll'
    'SKSE/Plugins/VisibleEquipment.ini' = Join-Path $source 'VisibleEquipment.ini'
    'README.md' = Join-Path $source 'README.md'
    'LICENSE' = Join-Path $source '../../LICENSE'
    'LICENSE-CommonLibSSE-NG.txt' = Join-Path $CommonLibRoot 'COPYING'
    'LICENSE-CommonLibSSE-NG-EXCEPTIONS.md' = Join-Path $CommonLibRoot 'EXCEPTIONS.md'
    'LICENSE-spdlog.txt' = Join-Path $share 'spdlog/copyright'
    'LICENSE-fmt.txt' = Join-Path $share 'fmt/copyright'
}
foreach ($entry in $files.GetEnumerator()) {
    if (-not (Test-Path -LiteralPath $entry.Value)) { throw "Package input missing: $($entry.Key) <- $($entry.Value)" }
}
Add-Type -AssemblyName System.IO.Compression
$stream = [IO.File]::Open($package, [IO.FileMode]::CreateNew)
$zip = [IO.Compression.ZipArchive]::new($stream, [IO.Compression.ZipArchiveMode]::Create, $false)
try {
    foreach ($entry in $files.GetEnumerator()) {
        $item = $zip.CreateEntry($entry.Key, [IO.Compression.CompressionLevel]::Optimal)
        $item.LastWriteTime = [DateTimeOffset]::new(2026, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
        $inputStream = [IO.File]::OpenRead($entry.Value)
        $outputStream = $item.Open()
        try { $inputStream.CopyTo($outputStream) } finally { $inputStream.Dispose(); $outputStream.Dispose() }
    }
} finally { $zip.Dispose(); $stream.Dispose() }
Get-FileHash -LiteralPath $package, $files['SKSE/Plugins/VisibleEquipment.dll'] -Algorithm SHA256
