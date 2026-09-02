#Requires -Version 5.1

[CmdletBinding()]
param(
    [string]$SimulatorPath = "",
    [string]$ConfigPath = "",
    [UInt64]$PrimarySeed = 1869507693,
    [UInt64]$AlternateSeed = 1869507694
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($SimulatorPath)) {
    $SimulatorPath = Join-Path $repoRoot "build/release/BoundedEncounters.Simulate.exe"
} elseif (-not [System.IO.Path]::IsPathRooted($SimulatorPath)) {
    $SimulatorPath = Join-Path $repoRoot $SimulatorPath
}
if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $ConfigPath = Join-Path $repoRoot "config/BoundedEncounters.json"
} elseif (-not [System.IO.Path]::IsPathRooted($ConfigPath)) {
    $ConfigPath = Join-Path $repoRoot $ConfigPath
}
$SimulatorPath = [System.IO.Path]::GetFullPath($SimulatorPath)
$ConfigPath = [System.IO.Path]::GetFullPath($ConfigPath)

if (-not (Test-Path -LiteralPath $SimulatorPath -PathType Leaf)) {
    throw "Simulator executable is missing: $SimulatorPath"
}
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Configuration file is missing: $ConfigPath"
}
if ($PrimarySeed -eq $AlternateSeed) {
    throw "PrimarySeed and AlternateSeed must differ."
}

$sourceCounts = @(1, 4, 8, 16, 64)
$expectedLevels = @(1, 5, 10, 20, 30, 40, 50, 75, 100)
$categoryNames = @("general", "animalBeast", "giantMammoth")
$environmentNames = @("interior", "exterior")
$caseNames = @("authoredPopulationOnly", "constrainedAttachedArea")
$tolerance = 1.0e-9
$checks = 0

function Assert-Condition {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $script:checks++
    if (-not $Condition) {
        throw "Simulator audit failed: $Message"
    }
}

function Assert-Near {
    param(
        [Parameter(Mandatory = $true)][double]$Actual,
        [Parameter(Mandatory = $true)][double]$Expected,
        [Parameter(Mandatory = $true)][string]$Message
    )

    Assert-Condition -Condition ([Math]::Abs($Actual - $Expected) -le $script:tolerance) -Message $Message
}

function Invoke-Simulator {
    param(
        [Parameter(Mandatory = $true)][UInt32]$SourceCount,
        [Parameter(Mandatory = $true)][UInt64]$Seed
    )

    $lines = @(& $script:SimulatorPath $script:ConfigPath $SourceCount $Seed 2>&1)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Simulator exited $exitCode for sourceCount=$SourceCount seed=$Seed`: $($lines -join ' ')"
    }
    $raw = ($lines -join "`n") + "`n"
    try {
        $document = $raw | ConvertFrom-Json
    } catch {
        throw "Simulator emitted invalid JSON for sourceCount=$SourceCount seed=$Seed`: $($_.Exception.Message)"
    }
    return [pscustomobject]@{
        Raw = $raw
        Document = $document
    }
}

function Assert-RunContract {
    param(
        [Parameter(Mandatory = $true)]$Run,
        [Parameter(Mandatory = $true)][UInt32]$SourceCount,
        [Parameter(Mandatory = $true)]$Config
    )

    $document = $Run.Document
    Assert-Condition -Condition ([UInt32]$document.schemaVersion -eq 1) -Message "schemaVersion must be 1"
    Assert-Condition -Condition ([UInt32]$document.sourceCount -eq $SourceCount) -Message "sourceCount echo mismatch"
    Assert-Condition -Condition ([bool]$document.configurationMode.enabled -eq [bool]$Config.enabled) -Message "enabled mode mismatch"
    Assert-Condition -Condition ([bool]$document.configurationMode.observeOnly -eq [bool]$Config.observeOnly) -Message "observeOnly mode mismatch"
    Assert-Condition -Condition (-not [string]::IsNullOrWhiteSpace([string]$document.repeatability.fingerprint)) -Message "repeatability fingerprint is missing"

    foreach ($categoryName in $categoryNames) {
        $rows = @($document.categories.$categoryName)
        $curve = $Config.curves.$categoryName
        Assert-Condition -Condition ($rows.Count -eq $expectedLevels.Count) -Message "$categoryName level count mismatch"
        Assert-Condition -Condition ([UInt32]$document.categoryCellCaps.$categoryName -eq [UInt32]$curve.maxExtrasPerCell) -Message "$categoryName cap mismatch"

        [double]$previousExpected = -1.0
        [double]$previousProjection = -1.0
        [UInt64]$previousSampled = 0
        for ($index = 0; $index -lt $rows.Count; ++$index) {
            $row = $rows[$index]
            Assert-Condition -Condition ([UInt32]$row.level -eq [UInt32]$expectedLevels[$index]) -Message "$categoryName level ordering mismatch"
            Assert-Condition -Condition ([UInt32]$row.authoredSources -eq $SourceCount) -Message "$categoryName authored source count mismatch"
            Assert-Condition -Condition ([double]$row.uncappedExpectedExtras + $tolerance -ge $previousExpected) -Message "$categoryName expectation decreased at level $($row.level)"
            Assert-Condition -Condition ([double]$row.cappedFractionalCapacityExtras + $tolerance -ge $previousProjection) -Message "$categoryName fractional-capacity projection decreased at level $($row.level)"
            Assert-Condition -Condition ([double]$row.cappedFractionalCapacityExtras -le ([double]$curve.maxExtrasPerCell + $tolerance)) -Message "$categoryName fractional-capacity projection exceeded its category cap at level $($row.level)"
            Assert-Condition -Condition ([UInt64]$row.sampledExtras -ge $previousSampled) -Message "$categoryName sampled count decreased at level $($row.level)"
            Assert-Condition -Condition ([UInt64]$row.sampledExtras -le [UInt64]$curve.maxExtrasPerCell) -Message "$categoryName category cap exceeded at level $($row.level)"
            Assert-Condition -Condition ([UInt64]$row.sampledExtras -le ([UInt64]$SourceCount * [UInt64]$curve.maxExtrasPerSource)) -Message "$categoryName per-source aggregate cap exceeded at level $($row.level)"
            Assert-Near -Actual ([double]$row.sampledTotal) -Expected ([double]$SourceCount + [double]$row.sampledExtras) -Message "$categoryName sampled total mismatch at level $($row.level)"
            Assert-Near -Actual ([double]$row.uncappedExpectedTotal) -Expected ([double]$SourceCount + [double]$row.uncappedExpectedExtras) -Message "$categoryName uncapped expected total mismatch at level $($row.level)"
            Assert-Near -Actual ([double]$row.cappedFractionalCapacityTotal) -Expected ([double]$SourceCount + [double]$row.cappedFractionalCapacityExtras) -Message "$categoryName fractional-capacity total mismatch at level $($row.level)"
            $previousExpected = [double]$row.uncappedExpectedExtras
            $previousProjection = [double]$row.cappedFractionalCapacityExtras
            $previousSampled = [UInt64]$row.sampledExtras
        }
    }

    foreach ($environmentName in $environmentNames) {
        foreach ($caseName in $caseNames) {
            $case = $document.mixedCategoryAudit.environments.$environmentName.$caseName
            $capacity = $case.capacity
            $rows = @($case.levels)
            Assert-Condition -Condition ($rows.Count -eq $expectedLevels.Count) -Message "$environmentName/$caseName level count mismatch"
            Assert-Condition -Condition ([UInt32]$capacity.effectiveAdditionalCap -le [UInt32]$capacity.additionalCellCap) -Message "$environmentName/$caseName effective cap exceeds additional cap"
            Assert-Condition -Condition ([UInt32]$capacity.effectiveAdditionalCap -le [UInt32]$capacity.remainingHostileCapacity) -Message "$environmentName/$caseName effective cap exceeds hostile capacity"
            Assert-Condition -Condition ([UInt32]$capacity.effectiveAdditionalCap -le [UInt32]$capacity.remainingGlobalActiveOwnedCapacity) -Message "$environmentName/$caseName effective cap exceeds active-owned capacity"
            Assert-Condition -Condition ([UInt32]$capacity.effectiveAdditionalCap -le [UInt32]$capacity.perEvaluationCap) -Message "$environmentName/$caseName effective cap exceeds evaluation cap"

            [double]$previousUncapped = -1.0
            [double]$previousProjection = -1.0
            foreach ($row in $rows) {
                Assert-Condition -Condition ([double]$row.uncappedExpectedExtras + $tolerance -ge $previousUncapped) -Message "$environmentName/$caseName uncapped expectation decreased at level $($row.level)"
                Assert-Condition -Condition ([double]$row.cappedFractionalCapacityExtras + $tolerance -ge $previousProjection) -Message "$environmentName/$caseName fractional-capacity projection decreased at level $($row.level)"
                Assert-Condition -Condition ([UInt32]$row.sampledExtras -le [UInt32]$capacity.effectiveAdditionalCap) -Message "$environmentName/$caseName sampled additions exceed effective cap at level $($row.level)"
                Assert-Condition -Condition ([double]$row.cappedFractionalCapacityExtras -le ([double]$capacity.effectiveAdditionalCap + $tolerance)) -Message "$environmentName/$caseName fractional-capacity projection exceeds effective cap at level $($row.level)"
                Assert-Near -Actual ([double]$row.sampledCellHostiles) -Expected ([double]$capacity.existingCellHostiles + [double]$row.sampledExtras) -Message "$environmentName/$caseName sampled hostile total mismatch at level $($row.level)"
                Assert-Near -Actual ([double]$row.sampledEligiblePopulation) -Expected ([double]$SourceCount + [double]$row.sampledExtras) -Message "$environmentName/$caseName sampled eligible total mismatch at level $($row.level)"
                if ([UInt32]$capacity.remainingHostileCapacity -eq 0 -or [UInt32]$capacity.remainingGlobalActiveOwnedCapacity -eq 0) {
                    Assert-Condition -Condition ([UInt32]$row.sampledExtras -eq 0) -Message "$environmentName/$caseName exhausted capacity admitted actors at level $($row.level)"
                }
                foreach ($categoryName in $categoryNames) {
                    Assert-Condition -Condition ([UInt32]$row.byCategory.$categoryName.sampledExtras -le [UInt32]$Config.curves.$categoryName.maxExtrasPerCell) -Message "$environmentName/$caseName/$categoryName category cap exceeded at level $($row.level)"
                }
                $previousUncapped = [double]$row.uncappedExpectedExtras
                $previousProjection = [double]$row.cappedFractionalCapacityExtras
            }
        }
    }
}

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$summaries = @()
$seedChangedAnySample = $false

foreach ($sourceCount in $sourceCounts) {
    $primary = Invoke-Simulator -SourceCount $sourceCount -Seed $PrimarySeed
    $repeat = Invoke-Simulator -SourceCount $sourceCount -Seed $PrimarySeed
    $alternate = Invoke-Simulator -SourceCount $sourceCount -Seed $AlternateSeed

    Assert-Condition -Condition ($primary.Raw -ceq $repeat.Raw) -Message "same-input output was not byte-identical for sourceCount=$sourceCount"
    Assert-RunContract -Run $primary -SourceCount $sourceCount -Config $config
    Assert-RunContract -Run $alternate -SourceCount $sourceCount -Config $config

    foreach ($categoryName in $categoryNames) {
        $primaryRows = @($primary.Document.categories.$categoryName)
        $alternateRows = @($alternate.Document.categories.$categoryName)
        for ($index = 0; $index -lt $primaryRows.Count; ++$index) {
            $left = $primaryRows[$index]
            $right = $alternateRows[$index]
            Assert-Near -Actual ([double]$left.expectedExtrasPerSource) -Expected ([double]$right.expectedExtrasPerSource) -Message "$categoryName per-source expectation changed with seed"
            Assert-Near -Actual ([double]$left.uncappedExpectedExtras) -Expected ([double]$right.uncappedExpectedExtras) -Message "$categoryName uncapped expectation changed with seed"
            Assert-Near -Actual ([double]$left.cappedFractionalCapacityExtras) -Expected ([double]$right.cappedFractionalCapacityExtras) -Message "$categoryName fractional-capacity projection changed with seed"
            if ([UInt32]$left.sampledExtras -ne [UInt32]$right.sampledExtras) {
                $seedChangedAnySample = $true
            }
        }
    }

    foreach ($environmentName in $environmentNames) {
        foreach ($caseName in $caseNames) {
            $primaryRows = @($primary.Document.mixedCategoryAudit.environments.$environmentName.$caseName.levels)
            $alternateRows = @($alternate.Document.mixedCategoryAudit.environments.$environmentName.$caseName.levels)
            for ($index = 0; $index -lt $primaryRows.Count; ++$index) {
                Assert-Near -Actual ([double]$primaryRows[$index].uncappedExpectedExtras) -Expected ([double]$alternateRows[$index].uncappedExpectedExtras) -Message "$environmentName/$caseName uncapped expectation changed with seed"
                if ([UInt32]$primaryRows[$index].sampledExtras -ne [UInt32]$alternateRows[$index].sampledExtras) {
                    $seedChangedAnySample = $true
                }
            }
        }
    }

    $summaries += [ordered]@{
        sourceCount = $sourceCount
        primaryFingerprint = [string]$primary.Document.repeatability.fingerprint
        alternateFingerprint = [string]$alternate.Document.repeatability.fingerprint
    }
}

Assert-Condition -Condition $seedChangedAnySample -Message "alternate seed did not change any sampled result"

# Exercise the documented command-line rejection boundary without accepting a
# partial or defaulted source count. Windows PowerShell promotes native stderr
# to an error record, so temporarily keep it non-terminating while retaining
# and checking the process exit code.
function Assert-RejectedSourceCount {
    param([Parameter(Mandatory = $true)][string]$Value)

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        @(& $SimulatorPath $ConfigPath $Value $PrimarySeed 2>&1) | Out-Null
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    Assert-Condition -Condition ($exitCode -eq 64) -Message "source-count $Value did not fail with command-line exit 64"
}

Assert-RejectedSourceCount -Value "0"
Assert-RejectedSourceCount -Value "100001"

[ordered]@{
    schemaVersion = 1
    passed = $true
    checks = $checks
    sourceCounts = $sourceCounts
    levels = $expectedLevels
    primarySeed = $PrimarySeed
    alternateSeed = $AlternateSeed
    alternateSeedChangedSample = $seedChangedAnySample
    runs = $summaries
} | ConvertTo-Json -Depth 6
