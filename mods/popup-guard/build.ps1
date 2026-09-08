[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SkseSdkRoot,
    [Parameter(Mandatory)][string]$VcpkgRoot,
    [Parameter(Mandatory)][string]$Cmake,
    [Parameter(Mandatory)][string]$BuildDirectory,
    [string]$Generator = ''
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
& $Cmake -S $source -B $build -G $Generator -A x64 "-DSKSE_SDK_ROOT=$SkseSdkRoot" `
    "-DCMAKE_TOOLCHAIN_FILE=$toolchain" '-DVCPKG_TARGET_TRIPLET=x64-windows-static'
if ($LASTEXITCODE -ne 0) { throw 'Configure failed' }
& $Cmake --build $build --config Release
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
& (Join-Path (Split-Path $Cmake) 'ctest.exe') --test-dir $build -C Release --output-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }

$package = Join-Path $build 'PopupGuard-0.1.0-win64.zip'
if (Test-Path -LiteralPath $package) { throw "Package exists; choose a fresh build directory: $package" }
$minhookLicense = Join-Path $build 'vcpkg_installed/x64-windows-static/share/minhook/copyright'
if (-not (Test-Path -LiteralPath $minhookLicense)) { throw "MinHook license missing: $minhookLicense" }
$files = [ordered]@{
    'SKSE/Plugins/!PopupGuard.dll' = Join-Path $build 'Release/!PopupGuard.dll'
    'SKSE/Plugins/PopupGuard.ini' = Join-Path $source 'PopupGuard.ini'
    'README.md' = Join-Path $source 'README.md'
    'LICENSE' = Join-Path $source '../../LICENSE'
    'LICENSE-MinHook.txt' = $minhookLicense
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
Get-FileHash -LiteralPath $package, $files['SKSE/Plugins/!PopupGuard.dll'] -Algorithm SHA256
