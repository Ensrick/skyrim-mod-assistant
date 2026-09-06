# Pure fixture tests. No game, live MO2 read/write, or vendor input required.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'generate_nif_slot_layer_proof.ps1'
$tokens = $null
$parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Layer-proof script does not parse' }
foreach ($name in @('Get-Sha256File', 'Get-ReviewedBookConfigSpecifications', 'Get-ReviewedBookConfigAdmissions')) {
    $function = @($ast.FindAll({ param($node)
        $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name
    }, $true))
    if ($function.Count -ne 1) { throw "Expected one production function: $name" }
    . ([scriptblock]::Create($function[0].Extent.Text))
}

function Assert-Equal($Actual, $Expected, [string] $Label) {
    if ($Actual -ne $Expected) { throw "$Label : expected $Expected, got $Actual" }
}
function Assert-Throws([scriptblock] $Code, [string] $Pattern) {
    $caught = $null
    try { & $Code | Out-Null } catch { $caught = $_.Exception.Message }
    if (-not $caught -or $caught -notmatch $Pattern) { throw "Expected error matching '$Pattern', got '$caught'" }
}

$tempParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$testRoot = Join-Path $tempParent ('skyrim-cloak-config-tests-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testRoot) | Out-Null
try {
    $path = Join-Path $testRoot 'fixture.ini'
    $key = 'skse/plugins/skypatcher/book/book covers skyrim/fixture.ini'
    $valid = "; original synthetic fixture`nfilterByBooks=Fixture.esm|123:model=clutter\books\fixture.nif:inventoryArt=FixtureArt`n"
    [IO.File]::WriteAllText($path, $valid, [Text.UTF8Encoding]::new($false))
    $configs = @{ $key = @{ path = $path } }
    $specs = @{ $key = @{ sha256 = Get-Sha256File $path; lines = 1 } }
    $result = @(Get-ReviewedBookConfigAdmissions $configs $specs)
    Assert-Equal $result.Count 1 'Exact reviewed BOOK file admitted'
    Assert-Equal $result[0].activeDirectiveLines 1 'BOOK directive count retained'
    Assert-Equal @(Get-ReviewedBookConfigAdmissions @{} $specs).Count 0 'Absent optional file does not raise allowance'
    Assert-Equal @(Get-ReviewedBookConfigAdmissions @{ renamed = @{ path = $path } } $specs).Count 0 'Renamed file not admitted'

    [IO.File]::AppendAllText($path, '; harmless edit still requires review')
    Assert-Throws { Get-ReviewedBookConfigAdmissions $configs $specs } 'config changed'
    $specs[$key].sha256 = Get-Sha256File $path
    $specs[$key].lines = 2
    Assert-Throws { Get-ReviewedBookConfigAdmissions $configs $specs } 'directive count changed'

    foreach ($bad in @(
        'filterByArmors=Fixture.esm|123:bipedSlotsToAdd=28',
        'filterByBooks=Fixture.esm|123:bipedSlotsToAdd=28',
        'filterByBooks=Fixture.esm|123:unknownOperation=value',
        'filterByBooks=Fixture.esm|123:model=',
        'filterByBooks=Fixture.esm|123:malformed',
        'filterByBooks=Fixture.esm|123:model=book.nif:filterByBipedSlots=28'
    )) {
        [IO.File]::WriteAllText($path, $bad, [Text.UTF8Encoding]::new($false))
        $specs[$key].sha256 = Get-Sha256File $path
        $specs[$key].lines = 1
        Assert-Throws { Get-ReviewedBookConfigAdmissions $configs $specs } 'non-BOOK selector|unreviewed operation'
    }
    $production = Get-ReviewedBookConfigSpecifications
    Assert-Equal $production.Count 5 'Only five reviewed BCS files'
    Assert-Equal ($production.Values | Measure-Object lines -Sum).Sum 909 'Exact vendor directive total'
    foreach ($entry in $production.GetEnumerator()) {
        if ($entry.Key -notlike 'skse/plugins/skypatcher/book/book covers skyrim/*' -or
            $entry.Value.sha256 -cnotmatch '^[0-9A-F]{64}$') { throw 'Malformed production allowlist' }
    }
    Write-Output 'PASS: 15 book-only admission assertions; no game or MO2 access.'
}
finally {
    $resolved = [IO.Path]::GetFullPath($testRoot)
    if ([IO.Path]::GetDirectoryName($resolved) -ne $tempParent.TrimEnd('\', '/') -or
        [IO.Path]::GetFileName($resolved) -notmatch '^skyrim-cloak-config-tests-[0-9a-f]{32}$') {
        throw 'Unsafe synthetic fixture cleanup path'
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
