#Requires -Version 7.4

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Import-Module (Join-Path $PSScriptRoot "DeterministicFileOrder.psm1") -Force

$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$workRoot = Join-Path $temporaryBase (
    "BoundedEncounters-file-order-test-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path (Join-Path $workRoot "docs/release") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $workRoot "SKSE/Plugins") -Force | Out-Null
try {
    foreach ($relativePath in @(
            "z.txt",
            "docs/test-plan.md",
            "docs/release/artifacts.md",
            "SKSE/Plugins/BoundedEncounters.dll",
            "A.txt",
            ".hidden.txt")) {
        [System.IO.File]::WriteAllText(
            (Join-Path $workRoot $relativePath),
            $relativePath,
            [System.Text.UTF8Encoding]::new($false))
    }
    if ($IsWindows) {
        $hiddenItem = Get-Item -LiteralPath (Join-Path $workRoot ".hidden.txt") -Force
        $hiddenItem.Attributes = $hiddenItem.Attributes -bor [System.IO.FileAttributes]::Hidden
    }

    [string[]]$expected = @(
        ".hidden.txt",
        "A.txt",
        "SKSE/Plugins/BoundedEncounters.dll",
        "docs/release/artifacts.md",
        "docs/test-plan.md",
        "z.txt")
    $runs = @()
    $assertions = 0
    for ($run = 0; $run -lt 5; ++$run) {
        [string[]]$actual = @(Get-FilesSortedOrdinal -Root $workRoot | ForEach-Object {
                [System.IO.Path]::GetRelativePath($workRoot, $_.FullName).Replace('\', '/')
            })
        if ($actual.Count -ne $expected.Count) {
            throw "Ordinal file ordering returned an unexpected file count."
        }
        ++$assertions
        for ($index = 0; $index -lt $expected.Count; ++$index) {
            if ($actual[$index] -cne $expected[$index]) {
                throw "Ordinal file ordering mismatch at index $index`: $($actual[$index]) != $($expected[$index])"
            }
            ++$assertions
        }
        $runs += ,$actual
    }

    $objectValues = @(
        [pscustomobject]@{ key = "b"; marker = 1 },
        [pscustomobject]@{ key = "A"; marker = 2 },
        [pscustomobject]@{ key = "b"; marker = 3 },
        [pscustomobject]@{ key = "a"; marker = 4 })
    [int[]]$expectedMarkers = @(2, 4, 1, 3)
    [int[]]$actualMarkers = @(Get-ObjectsSortedByOrdinalKey `
        -Values $objectValues `
        -KeySelector { param($value) $value.key } | ForEach-Object marker)
    if ($actualMarkers.Count -ne $expectedMarkers.Count) {
        throw "Ordinal object ordering returned an unexpected value count."
    }
    ++$assertions
    for ($index = 0; $index -lt $expectedMarkers.Count; ++$index) {
        if ($actualMarkers[$index] -ne $expectedMarkers[$index]) {
            throw "Ordinal object ordering mismatch at index $index."
        }
        ++$assertions
    }

    $missingRejected = $false
    try {
        $null = @(Get-FilesSortedOrdinal -Root (Join-Path $workRoot "missing"))
    } catch {
        $missingRejected = $true
    }
    if (-not $missingRejected) {
        throw "A missing ordering root was not rejected fail-closed."
    }
    ++$assertions

    [ordered]@{
        assertions = $assertions
        repeatedRuns = $runs.Count
        orderedPaths = $runs[0]
        orderedObjectMarkers = $actualMarkers
        missingRootGate = "passed"
    } | ConvertTo-Json -Depth 4
} finally {
    $resolvedWorkRoot = [System.IO.Path]::GetFullPath($workRoot)
    if ($resolvedWorkRoot.StartsWith($temporaryBase, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedWorkRoot).StartsWith(
            "BoundedEncounters-file-order-test-",
            [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedWorkRoot -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        throw "Refusing to remove unexpected file-order test directory: $resolvedWorkRoot"
    }
}
