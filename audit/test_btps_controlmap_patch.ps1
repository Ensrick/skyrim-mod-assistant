#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$patch = Join-Path $PSScriptRoot '../patches/btps/control-map-offset-1.7.104.patch'
# Test the exact published production helper and tests, without downloading or
# rebuilding the vendor plugin. Extract only added files into a new temp root.
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('btps-controlmap-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $scratch | Out-Null
Push-Location $scratch
try {
    git init --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Temporary repository initialization failed.' }
    git apply --include=src/lib/ControlMapLayout.h --include=tests/CMakeLists.txt --include=tests/control_map_layout.cpp $patch
    if ($LASTEXITCODE -ne 0) { throw 'Published regression payload does not apply.' }
    cmake -S tests -B build -A x64
    if ($LASTEXITCODE -ne 0) { throw 'Regression configure failed.' }
    cmake --build build --config Release
    if ($LASTEXITCODE -ne 0) { throw 'Regression build failed.' }
    ctest --test-dir build -C Release --output-on-failure
    if ($LASTEXITCODE -ne 0) { throw 'Production control-map regression failed.' }
} finally {
    Pop-Location
    # Retain small diagnostics on failure or success; never recursively remove
    # an inferred path. CI runners discard their own ephemeral workspace.
    Write-Host "Regression work directory: $scratch"
}
