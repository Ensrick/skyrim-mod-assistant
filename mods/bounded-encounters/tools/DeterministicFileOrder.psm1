Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RelativeSlashPathForOrdering {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Path
    )

    return [System.IO.Path]::GetRelativePath($Base, $Path).Replace('\', '/')
}

function Get-FilesSortedOrdinal {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Root)

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
    if (-not (Test-Path -LiteralPath $resolvedRoot -PathType Container)) {
        throw "File-ordering root is missing: $resolvedRoot"
    }
    $rootItem = Get-Item -LiteralPath $resolvedRoot -Force
    if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "File-ordering root is a reparse point: $resolvedRoot"
    }

    $decorated = [System.Collections.Generic.List[object]]::new()
    $caseInsensitivePaths = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase)
    $items = @(Get-ChildItem -LiteralPath $resolvedRoot -Force -Recurse)
    foreach ($item in $items) {
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "File-ordering tree contains a reparse point: $resolvedRoot :: $($item.FullName)"
        }
    }
    foreach ($file in @($items | Where-Object { $_ -is [System.IO.FileInfo] })) {
        $key = Get-RelativeSlashPathForOrdering -Base $resolvedRoot -Path $file.FullName
        if ([string]::IsNullOrWhiteSpace($key) -or
            [System.IO.Path]::IsPathRooted($key) -or
            $key.Contains(':', [System.StringComparison]::Ordinal) -or
            $key.StartsWith('../', [System.StringComparison]::Ordinal) -or
            @($key.Split('/') | Where-Object { $_ -in @("", ".", "..") }).Count -ne 0) {
            throw "File tree produced an unsafe relative path: $resolvedRoot :: $key"
        }
        if (-not $caseInsensitivePaths.Add($key)) {
            throw "File tree contains a case-insensitive duplicate path: $resolvedRoot :: $key"
        }
        $decorated.Add([pscustomobject]@{
                key = $key
                file = $file
            })
    }

    $comparison = [System.Comparison[object]]{
        param($left, $right)
        [System.StringComparer]::Ordinal.Compare([string]$left.key, [string]$right.key)
    }
    $decorated.Sort($comparison)
    foreach ($entry in $decorated) {
        $entry.file
    }
}

function Get-ObjectsSortedByOrdinalKey {
    [CmdletBinding()]
    param(
        [AllowEmptyCollection()][object[]]$Values,
        [Parameter(Mandatory = $true)][scriptblock]$KeySelector
    )

    $decorated = [System.Collections.Generic.List[object]]::new()
    $ordinal = 0
    foreach ($value in @($Values)) {
        $decorated.Add([pscustomobject]@{
                key = [string](& $KeySelector $value)
                ordinal = $ordinal
                value = $value
            })
        ++$ordinal
    }
    $comparison = [System.Comparison[object]]{
        param($left, $right)
        $result = [System.StringComparer]::Ordinal.Compare(
            [string]$left.key,
            [string]$right.key)
        if ($result -ne 0) {
            return $result
        }
        return [int]$left.ordinal - [int]$right.ordinal
    }
    $decorated.Sort($comparison)
    foreach ($entry in $decorated) {
        $entry.value
    }
}

Export-ModuleMember -Function Get-FilesSortedOrdinal, Get-ObjectsSortedByOrdinalKey
