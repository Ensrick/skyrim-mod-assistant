[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SkseSdkRoot,
    [Parameter(Mandatory)][string]$Cmake,
    [Parameter(Mandatory)][string]$BuildDirectory
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$source = $PSScriptRoot
$build = [IO.Path]::GetFullPath($BuildDirectory)
& $Cmake -S $source -B $build -G 'Visual Studio 17 2022' -A x64 "-DSKSE_SDK_ROOT=$SkseSdkRoot"
if ($LASTEXITCODE -ne 0) { throw 'Configure failed' }
& $Cmake --build $build --config Release
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
& (Join-Path (Split-Path $Cmake) 'ctest.exe') --test-dir $build -C Release --output-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }

$package = Join-Path $build 'WindowFocusGuard-0.1.0-win64.zip'
if (Test-Path -LiteralPath $package) { throw "Package exists; choose a fresh build directory: $package" }
$files = [ordered]@{
    'SKSE/Plugins/WindowFocusGuard.dll' = Join-Path $build 'Release/WindowFocusGuard.dll'
    'README.md' = Join-Path $source 'README.md'
    'LICENSE' = Join-Path $source '../../LICENSE'
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
Get-FileHash -LiteralPath $package, $files['SKSE/Plugins/WindowFocusGuard.dll'] -Algorithm SHA256
