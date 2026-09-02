[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$SessionRoot = 'C:\Users\danjo\.codex\sessions'
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($SessionRoot).TrimEnd('\') + '\'
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    throw "Session root does not exist: $root"
}

$targets = [Collections.Generic.List[object]]::new()
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.jsonl' -Force) {
    $resolved = [IO.Path]::GetFullPath($file.FullName)
    if (-not $resolved.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside session root: $resolved"
    }

    $stream = [IO.FileStream]::new(
        $resolved,
        [IO.FileMode]::Open,
        [IO.FileAccess]::Read,
        [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
    )
    $reader = [IO.StreamReader]::new($stream)
    try {
        $metadata = $reader.ReadLine()
    }
    finally {
        $reader.Dispose()
    }

    # A subagent rollout is an internal fork. Root task rollouts do not carry
    # either marker and are intentionally preserved.
    $isSubagent = $metadata -match '"thread_source"\s*:\s*"subagent"' -or
        $metadata -match '"source"\s*:\s*\{\s*"subagent"'
    if ($isSubagent) {
        $targets.Add([pscustomobject]@{
            Path = $resolved
            Bytes = [int64]$file.Length
        })
    }
}

$bytes = [int64](($targets | Measure-Object -Property Bytes -Sum).Sum)
$result = [ordered]@{
    mode = if ($Apply) { 'apply' } else { 'dry-run' }
    sessionRoot = $root
    targetKind = 'subagent rollout JSONL only'
    files = $targets.Count
    logicalBytes = $bytes
    logicalGiB = [math]::Round($bytes / 1GB, 3)
    rootRolloutsPreserved = $true
}

if ($Apply) {
    foreach ($target in $targets) {
        Remove-Item -LiteralPath $target.Path -Force
    }
    $remaining = Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.jsonl' -Force
    $remainingBytes = [int64](($remaining | Measure-Object -Property Length -Sum).Sum)
    $result.remainingRolloutFiles = $remaining.Count
    $result.remainingLogicalBytes = $remainingBytes
    $result.remainingLogicalGiB = [math]::Round($remainingBytes / 1GB, 3)
}

[pscustomobject]$result | ConvertTo-Json
