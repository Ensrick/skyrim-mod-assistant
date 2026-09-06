[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $CommonLibRoot,

    [string] $OutputRoot = (Join-Path $PSScriptRoot 'work'),

    [string] $Cmake = '',

    [string] $VcpkgRoot = '',

    [string] $Generator = '',

    [Parameter(Mandatory = $true)]
    [string] $RuntimeConfig,

    [switch] $Clean
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$expectedCommit = '90a64a4d65ce659a139137c968f42151bb6ecec9'
$sourceRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$commonRoot = [System.IO.Path]::GetFullPath($CommonLibRoot)
$output = [System.IO.Path]::GetFullPath($OutputRoot)
$runtimeConfigPath = [System.IO.Path]::GetFullPath($RuntimeConfig)

if ($output.Equals($sourceRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'OutputRoot must not be the native source directory'
}
if (-not (Test-Path -LiteralPath $runtimeConfigPath -PathType Leaf)) {
    throw "RuntimeConfig is unavailable: $runtimeConfigPath"
}

function Get-InputSnapshot {
    $outputPrefix = $output.TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
        [System.IO.Path]::DirectorySeparatorChar
    [ordered]@{
        runtimeConfig = [ordered]@{
            path = $runtimeConfigPath
            sha256 = (Get-FileHash -LiteralPath $runtimeConfigPath -Algorithm SHA256).Hash
            bytes = (Get-Item -LiteralPath $runtimeConfigPath).Length
        }
        sourceInputs = @(
            Get-ChildItem -LiteralPath $sourceRoot -Recurse -File |
                Where-Object {
                    -not $_.FullName.StartsWith($outputPrefix, [System.StringComparison]::OrdinalIgnoreCase) -and
                    $_.FullName -notmatch '[\\/](build|work)[^\\/]*[\\/]'
                } |
                Sort-Object FullName |
                ForEach-Object {
                    [ordered]@{
                        relativePath = [System.IO.Path]::GetRelativePath($sourceRoot, $_.FullName).Replace('\', '/')
                        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                        bytes = $_.Length
                    }
                }
        )
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $commonRoot 'CMakeLists.txt') -PathType Leaf)) {
    throw "CommonLibRoot is not a CommonLib source checkout: $commonRoot"
}

$actualCommit = (& git -C $commonRoot rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $expectedCommit) {
    throw "CommonLib commit mismatch: expected $expectedCommit, got '$actualCommit'"
}
$commonTrackedStatus = (& git -C $commonRoot status --porcelain=v1 --untracked-files=no 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $commonTrackedStatus) {
    throw "CommonLib tracked checkout is not clean: '$commonTrackedStatus'"
}

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
    throw 'vswhere is unavailable; a supported existing MSVC toolchain cannot be identified'
}
$vsInstall = (& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1)
if ($LASTEXITCODE -ne 0 -or -not $vsInstall) {
    throw 'No installed x64 MSVC toolchain was found'
}
if (-not $Cmake) {
    $Cmake = Join-Path $vsInstall 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
}
$cmakePath = [System.IO.Path]::GetFullPath($Cmake)
if (-not (Test-Path -LiteralPath $cmakePath -PathType Leaf)) {
    throw "CMake executable is unavailable: $cmakePath"
}
if (-not $VcpkgRoot) {
    $VcpkgRoot = Join-Path $vsInstall 'VC\vcpkg'
}
$vcpkgPath = [System.IO.Path]::GetFullPath($VcpkgRoot)
if (-not (Test-Path -LiteralPath (Join-Path $vcpkgPath 'scripts\buildsystems\vcpkg.cmake') -PathType Leaf)) {
    throw "vcpkg toolchain is unavailable: $vcpkgPath"
}
if (-not $Generator) {
    $version = (& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion | Select-Object -First 1)
    $major = ([version]$version).Major
    $capabilities = & $cmakePath -E capabilities | ConvertFrom-Json
    $matches = @($capabilities.generators | Where-Object name -Match "^Visual Studio $major ")
    if ($matches.Count -ne 1) {
        throw "CMake has no unambiguous generator for installed Visual Studio major $major"
    }
    $Generator = $matches[0].name
}

# Freeze exact consumer inputs before CMake can read them. Recomputing the
# snapshot after all tests prevents a concurrent edit from being attested as
# though it produced the emitted DLL.
$inputSnapshot = Get-InputSnapshot
$inputSnapshotJson = $inputSnapshot | ConvertTo-Json -Depth 8 -Compress

$build = Join-Path $output 'build'
if ($Clean -and (Test-Path -LiteralPath $build)) {
    $resolvedBuild = [System.IO.Path]::GetFullPath($build)
    $resolvedOutput = [System.IO.Path]::GetFullPath($output)
    if (-not $resolvedBuild.StartsWith($resolvedOutput + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean a build directory outside OutputRoot: $resolvedBuild"
    }
    Remove-Item -LiteralPath $resolvedBuild -Recurse -Force
}

New-Item -ItemType Directory -Path $build -Force | Out-Null

& $cmakePath -S $sourceRoot -B $build -G $Generator -A x64 `
    "-DCMAKE_TOOLCHAIN_FILE=$(Join-Path $vcpkgPath 'scripts\buildsystems\vcpkg.cmake')" `
    '-DVCPKG_TARGET_TRIPLET=x64-windows-static' `
    "-DCOMMONLIBSSE_ROOT=$commonRoot"
if ($LASTEXITCODE -ne 0) { throw "CMake configure failed with exit code $LASTEXITCODE" }

$cachePath = Join-Path $build 'CMakeCache.txt'
$generatorInstanceLine = Get-Content -LiteralPath $cachePath |
    Where-Object { $_ -like 'CMAKE_GENERATOR_INSTANCE:INTERNAL=*' } |
    Select-Object -First 1
if (-not $generatorInstanceLine) {
    throw 'Configured Visual Studio generator instance is absent from CMakeCache.txt'
}
$generatorInstance = $generatorInstanceLine.Substring($generatorInstanceLine.IndexOf('=') + 1)

& $cmakePath --build $build --config Release --target EnsrickCurrencyPolicyTests EnsrickCurrencyConfigTests EnsrickCurrencyDenominations
if ($LASTEXITCODE -ne 0) { throw "Native build failed with exit code $LASTEXITCODE" }

& (Join-Path $build 'Release\EnsrickCurrencyPolicyTests.exe')
if ($LASTEXITCODE -ne 0) { throw "Native policy tests failed with exit code $LASTEXITCODE" }

& (Join-Path $build 'Release\EnsrickCurrencyConfigTests.exe') $runtimeConfigPath
if ($LASTEXITCODE -ne 0) { throw "Native runtime-config test failed with exit code $LASTEXITCODE" }

$inputSnapshotAfter = Get-InputSnapshot
$inputSnapshotAfterJson = $inputSnapshotAfter | ConvertTo-Json -Depth 8 -Compress
if ($inputSnapshotJson -cne $inputSnapshotAfterJson) {
    throw 'Native source or runtime configuration changed during build/test; refusing a stale receipt'
}
$finalCommonCommit = (& git -C $commonRoot rev-parse HEAD 2>&1 | Out-String).Trim()
$finalCommonTrackedStatus = (& git -C $commonRoot status --porcelain=v1 --untracked-files=no 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $finalCommonCommit -ne $actualCommit -or $finalCommonTrackedStatus) {
    throw 'Pinned CommonLib tracked state changed during build/test; refusing a stale receipt'
}

$dll = Join-Path $build 'Release\EnsrickCurrencyDenominations.dll'
if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) {
    throw "Expected plugin DLL was not produced: $dll"
}

$receipt = [ordered]@{
    schemaVersion = 1
    sourceRoot = $sourceRoot
    commonLibRoot = $commonRoot
    commonLibCommit = $actualCommit
    commonLibTrackedStatus = 'clean'
    commonLibLicense = [ordered]@{
        expression = 'GPL-3.0-or-later WITH Modding-Exception AND GPL-3.0-Linking-Exception-with-Corresponding-Source'
        copyingSha256 = (Get-FileHash -LiteralPath (Join-Path $commonRoot 'COPYING') -Algorithm SHA256).Hash
        exceptionsSha256 = (Get-FileHash -LiteralPath (Join-Path $commonRoot 'EXCEPTIONS.md') -Algorithm SHA256).Hash
    }
    toolchain = [ordered]@{
        discoveryVisualStudio = $vsInstall
        generatorInstance = $generatorInstance
        cmake = $cmakePath
        vcpkg = $vcpkgPath
        generator = $Generator
        triplet = 'x64-windows-static'
        msvcRuntime = 'MultiThreaded release / MultiThreadedDebug debug'
    }
    runtime = '1.7.104.0'
    skse = '2.3.1'
    runtimeConfig = $inputSnapshot.runtimeConfig
    sourceInputs = $inputSnapshot.sourceInputs
    dll = [ordered]@{
        relativePath = 'SKSE/Plugins/EnsrickCurrencyDenominations.dll'
        sha256 = (Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash
        bytes = (Get-Item -LiteralPath $dll).Length
    }
}
$receiptPath = Join-Path $output 'native-build-receipt.json'
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8NoBOM
Write-Host "PASS: native bridge built and policy tests passed"
Write-Host "DLL: $dll"
Write-Host "Receipt: $receiptPath"
