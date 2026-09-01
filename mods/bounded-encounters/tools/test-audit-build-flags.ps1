[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$auditScript = Join-Path $PSScriptRoot "audit-build-flags.ps1"
$powershellExe = Join-Path $env:SystemRoot "System32/WindowsPowerShell/v1.0/powershell.exe"
if (-not (Test-Path -LiteralPath $auditScript -PathType Leaf)) {
    throw "Build-flag audit script is missing: $auditScript"
}
if (-not (Test-Path -LiteralPath $powershellExe -PathType Leaf)) {
    throw "Windows PowerShell 5.1 is unavailable: $powershellExe"
}

$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$tempRoot = Join-Path $tempBase ("bounded-encounters-build-flag-audit-" + [guid]::NewGuid().ToString("N"))
$sourceDirectory = Join-Path $tempRoot "source with spaces"
$buildDirectory = Join-Path $sourceDirectory "build/release"
$reportPath = Join-Path $buildDirectory "build-flag-audit.json"
$outsideReportPath = Join-Path $tempRoot "escaped-audit.json"
$implicitOptionVariables = @("CL", "_CL_", "LINK", "_LINK_")
$savedEnvironment = [ordered]@{}
$script:assertionCount = 0

function Assert-True {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Condition,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if (-not $Condition) {
        throw "Assertion failed: $Message"
    }
    ++$script:assertionCount
}

function Write-Utf8Lf {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Content
    )

    $normalized = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    [System.IO.File]::WriteAllText(
        $Path,
        $normalized,
        [System.Text.UTF8Encoding]::new($false))
}

function Clear-ImplicitOptionEnvironment {
    foreach ($name in $implicitOptionVariables) {
        [System.Environment]::SetEnvironmentVariable(
            $name,
            $null,
            [System.EnvironmentVariableTarget]::Process)
    }
}

function Get-DefaultCompileFlags {
    $sourceForFlag = $sourceDirectory.Replace(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar)
    return "/experimental:deterministic /cgthreads1 `"/pathmap:$sourceForFlag=.`""
}

function Get-DefaultNinja {
    param(
        [string]$LinkFlags = "/machine:x64 /Brepro",
        [string]$LinkPath = "/LIBPATH:`"C:/library path`"",
        [string]$LinkLibraries = "Example.lib"
    )

    return @"
build Example.dll Example.lib: CXX_SHARED_LIBRARY_LINKER__Example_Release Example.obj
  LINK_FLAGS = $LinkFlags
  LINK_PATH = $LinkPath
  LINK_LIBRARIES = $LinkLibraries
build Example.exe: CXX_EXECUTABLE_LINKER__ExampleTool_Release ExampleTool.obj
  LINK_FLAGS = $LinkFlags
  LINK_PATH = $LinkPath
  LINK_LIBRARIES = $LinkLibraries
build ExampleModule.dll: C_MODULE_LIBRARY_LINKER__ExampleModule_Release ExampleModule.obj
  LINK_FLAGS = $LinkFlags
  LINK_PATH = $LinkPath
  LINK_LIBRARIES = $LinkLibraries
"@
}

function Get-DefaultRules {
    param(
        [string]$SurfaceExpression = '$LINK_FLAGS $LINK_PATH $LINK_LIBRARIES',
        [string]$AdditionalProperties = ""
    )

    return @"
rule CXX_SHARED_LIBRARY_LINKER__Example_Release
  command = link.exe `$in /out:`$TARGET_FILE $SurfaceExpression
$AdditionalProperties
rule CXX_EXECUTABLE_LINKER__ExampleTool_Release
  command = link.exe `$in /out:`$TARGET_FILE $SurfaceExpression
$AdditionalProperties
rule C_MODULE_LIBRARY_LINKER__ExampleModule_Release
  command = link.exe `$in /out:`$TARGET_FILE $SurfaceExpression
$AdditionalProperties
"@
}

function Write-Fixture {
    param(
        [string]$CompileFlags = (Get-DefaultCompileFlags),
        [string]$Ninja = (Get-DefaultNinja),
        [string]$Rules = (Get-DefaultRules),
        [string[]]$AdditionalCacheLines = @()
    )

    New-Item -ItemType Directory -Path $sourceDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $buildDirectory -Force | Out-Null
    foreach ($path in @($reportPath, $outsideReportPath)) {
        if (Test-Path -LiteralPath $path) {
            [System.IO.File]::Delete($path)
        }
    }

    $sourceFile = Join-Path $sourceDirectory "Example.cpp"
    $command = "cl.exe /nologo $CompileFlags /c `"$sourceFile`""
    $commands = @(
        [ordered]@{
            directory = $buildDirectory
            command = $command
            file = $sourceFile
        }
    )
    $compileJson = ($commands | ConvertTo-Json -Depth 4).TrimEnd() + "`n"
    Write-Utf8Lf -Path (Join-Path $buildDirectory "compile_commands.json") -Content $compileJson

    $sourceForCache = $sourceDirectory.Replace(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar)
    $cacheLines = @("CMAKE_HOME_DIRECTORY:INTERNAL=$sourceForCache") + $AdditionalCacheLines
    Write-Utf8Lf `
        -Path (Join-Path $buildDirectory "CMakeCache.txt") `
        -Content (($cacheLines -join "`n") + "`n")
    Write-Utf8Lf -Path (Join-Path $buildDirectory "build.ninja") -Content ($Ninja.TrimEnd() + "`n")
    New-Item -ItemType Directory -Path (Join-Path $buildDirectory "CMakeFiles") -Force | Out-Null
    Write-Utf8Lf `
        -Path (Join-Path $buildDirectory "CMakeFiles/rules.ninja") `
        -Content ($Rules.TrimEnd() + "`n")
}

function Invoke-Audit {
    param(
        [string]$RequestedOutputPath = $reportPath
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $powershellExe `
            -NoLogo `
            -NoProfile `
            -ExecutionPolicy Bypass `
            -File $auditScript `
            -BuildDirectory $buildDirectory `
            -OutputPath $RequestedOutputPath 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    return [pscustomobject]@{
        exitCode = $exitCode
        output = $output
    }
}

function Assert-CanonicalReport {
    Assert-True (Test-Path -LiteralPath $reportPath -PathType Leaf) "successful audit writes its report"
    [byte[]]$bytes = [System.IO.File]::ReadAllBytes($reportPath)
    Assert-True ($bytes.Length -gt 1) "audit report is nonempty"
    Assert-True (-not ($bytes.Length -ge 3 -and
            $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)) "audit report has no UTF-8 BOM"
    Assert-True (@($bytes | Where-Object { $_ -eq 13 }).Count -eq 0) "audit report contains no CR bytes"
    Assert-True ($bytes[$bytes.Length - 1] -eq 10) "audit report ends with LF"
    Assert-True ($bytes[$bytes.Length - 2] -ne 10) "audit report has exactly one final LF"

    $strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
    $report = $strictUtf8.GetString($bytes) | ConvertFrom-Json
    Assert-True ([int]$report.schemaVersion -eq 3) "audit report uses schema version 3"
    Assert-True ([string]$report.status -ceq "pass") "audit report records pass status"
    Assert-True ([int]$report.compileCommandCount -eq 1) "audit report records the compile command count"
    Assert-True ([int]$report.linkCommandCount -eq 3) "audit report records all C/C++ executable/shared/module link records"
    Assert-True `
        (@($report.auditedLinkVariables) -join "," -ceq "LINK_FLAGS,LINK_PATH,LINK_LIBRARIES") `
        "audit report records every expanded linker variable surface"
}

function Invoke-PositiveCase {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Arrange
    )

    Clear-ImplicitOptionEnvironment
    & $Arrange
    $result = Invoke-Audit
    Assert-True ($result.exitCode -eq 0) "$Name succeeds under Windows PowerShell 5.1; output: $($result.output)"
    Assert-CanonicalReport
    Write-Output "PASS: $Name"
}

function Invoke-NegativeCase {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Arrange,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedPattern,
        [string]$RequestedOutputPath = $reportPath,
        [bool]$SeedStaleReport = $true
    )

    Clear-ImplicitOptionEnvironment
    & $Arrange
    if ($SeedStaleReport) {
        Write-Utf8Lf -Path $RequestedOutputPath -Content "stale-pass`n"
    }
    $result = Invoke-Audit -RequestedOutputPath $RequestedOutputPath
    Assert-True ($result.exitCode -ne 0) "$Name fails closed"
    Assert-True ($result.output -match $ExpectedPattern) "$Name reports the expected failure; output: $($result.output)"
    if ($SeedStaleReport) {
        Assert-True (-not (Test-Path -LiteralPath $RequestedOutputPath)) "$Name removes a stale success report before auditing"
    } else {
        Assert-True (-not (Test-Path -LiteralPath $RequestedOutputPath)) "$Name does not create an escaped output"
    }
    Write-Output "PASS: $Name"
}

foreach ($name in $implicitOptionVariables) {
    $savedEnvironment[$name] = [System.Environment]::GetEnvironmentVariable(
        $name,
        [System.EnvironmentVariableTarget]::Process)
}

try {
    New-Item -ItemType Directory -Path $tempRoot | Out-Null

    Invoke-PositiveCase -Name "slash options and quoted source path" -Arrange {
        Write-Fixture
    }
    Invoke-PositiveCase -Name "dash option spellings" -Arrange {
        $sourceForFlag = $sourceDirectory.Replace(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar)
        Write-Fixture `
            -CompileFlags "-experimental:deterministic -cgthreads1 `"-pathmap:$sourceForFlag=.`"" `
            -Ninja (Get-DefaultNinja -LinkFlags "-machine:x64 -Brepro")
    }

    Invoke-NegativeCase -Name "missing deterministic compiler mode" -Arrange {
        $flags = (Get-DefaultCompileFlags).Replace("/experimental:deterministic ", "")
        Write-Fixture -CompileFlags $flags
    } -ExpectedPattern "deterministic"

    Invoke-NegativeCase -Name "conflicting codegen thread count" -Arrange {
        Write-Fixture -CompileFlags ((Get-DefaultCompileFlags) + " -cgthreads4")
    } -ExpectedPattern "cgthreads"

    Invoke-NegativeCase -Name "wrong-case codegen option" -Arrange {
        $flags = (Get-DefaultCompileFlags).Replace("/cgthreads1", "/CGTHREADS1")
        Write-Fixture -CompileFlags $flags
    } -ExpectedPattern "cgthreads"

    Invoke-NegativeCase -Name "slash GL" -Arrange {
        Write-Fixture -CompileFlags ((Get-DefaultCompileFlags) + " /GL")
    } -ExpectedPattern "GL-family"

    Invoke-NegativeCase -Name "dash GL" -Arrange {
        Write-Fixture -CompileFlags ((Get-DefaultCompileFlags) + " -GL")
    } -ExpectedPattern "GL-family"

    Invoke-NegativeCase -Name "irrelevant pathmap source" -Arrange {
        Write-Fixture -CompileFlags "/experimental:deterministic /cgthreads1 /pathmap:C:/wrong-source=."
    } -ExpectedPattern "CMAKE_HOME_DIRECTORY"

    Invoke-NegativeCase -Name "duplicate pathmap" -Arrange {
        Write-Fixture -CompileFlags ((Get-DefaultCompileFlags) + " /pathmap:C:/wrong-source=.")
    } -ExpectedPattern "duplicate /pathmap"

    Invoke-NegativeCase -Name "hidden compiler response file" -Arrange {
        Write-Fixture -CompileFlags ((Get-DefaultCompileFlags) + " @hidden.rsp")
    } -ExpectedPattern "response file"

    Invoke-NegativeCase -Name "missing production links" -Arrange {
        Write-Fixture -Ninja "# no production link records"
    } -ExpectedPattern "contains no executable"

    Invoke-NegativeCase -Name "link record without LINK_FLAGS" -Arrange {
        Write-Fixture -Ninja "build Example.dll: CXX_SHARED_LIBRARY_LINKER__Example_Release Example.obj"
    } -ExpectedPattern "has no LINK_FLAGS"

    Invoke-NegativeCase -Name "missing Brepro" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkFlags "/machine:x64")
    } -ExpectedPattern "Brepro"

    Invoke-NegativeCase -Name "conflicting Brepro" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkFlags "/Brepro -Brepro-")
    } -ExpectedPattern "Brepro"

    Invoke-NegativeCase -Name "slash LTCG" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkFlags "/Brepro /LTCG")
    } -ExpectedPattern "LTCG-family"

    Invoke-NegativeCase -Name "dash LTCG" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkFlags "-Brepro -LTCG:incremental")
    } -ExpectedPattern "LTCG-family"

    Invoke-NegativeCase -Name "hidden linker response file" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkFlags "/Brepro @hidden.rsp")
    } -ExpectedPattern "response file"

    Invoke-NegativeCase -Name "LTCG hidden in LINK_LIBRARIES" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkLibraries "Example.lib /LTCG")
    } -ExpectedPattern "LTCG-family"

    Invoke-NegativeCase -Name "Brepro override hidden in LINK_LIBRARIES" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkLibraries "Example.lib /Brepro-")
    } -ExpectedPattern "Brepro"

    Invoke-NegativeCase -Name "response file hidden in LINK_PATH" -Arrange {
        Write-Fixture -Ninja (Get-DefaultNinja -LinkPath "@hidden.rsp")
    } -ExpectedPattern "response file"

    Invoke-NegativeCase -Name "missing LINK_LIBRARIES" -Arrange {
        $ninja = (Get-DefaultNinja) -replace '(?m)^\s+LINK_LIBRARIES\s*=.*\r?\n?', ''
        Write-Fixture -Ninja $ninja
    } -ExpectedPattern "exactly one LINK_LIBRARIES"

    Invoke-NegativeCase -Name "reordered linker rule surfaces" -Arrange {
        Write-Fixture -Rules (Get-DefaultRules `
                -SurfaceExpression '$LINK_FLAGS $LINK_LIBRARIES $LINK_PATH')
    } -ExpectedPattern "audited order"

    Invoke-NegativeCase -Name "Ninja linker response metadata" -Arrange {
        Write-Fixture -Rules (Get-DefaultRules -AdditionalProperties "  rspfile = hidden.rsp")
    } -ExpectedPattern "Ninja response file"

    foreach ($environmentVariable in $implicitOptionVariables) {
        Invoke-NegativeCase -Name "nonempty $environmentVariable environment" -Arrange {
            Write-Fixture
            [System.Environment]::SetEnvironmentVariable(
                $environmentVariable,
                "-cgthreads4",
                [System.EnvironmentVariableTarget]::Process)
        } -ExpectedPattern ([regex]::Escape("$environmentVariable environment variable is nonempty"))
    }

    Invoke-NegativeCase -Name "duplicate CMAKE_HOME_DIRECTORY" -Arrange {
        Write-Fixture -AdditionalCacheLines @("CMAKE_HOME_DIRECTORY:INTERNAL=C:/other")
    } -ExpectedPattern "exactly one CMAKE_HOME_DIRECTORY"

    Invoke-NegativeCase `
        -Name "output path escape" `
        -Arrange { Write-Fixture } `
        -ExpectedPattern "must remain inside" `
        -RequestedOutputPath $outsideReportPath `
        -SeedStaleReport $false

    Write-Output "Build-flag audit tests passed: $script:assertionCount assertions."
} finally {
    foreach ($name in $implicitOptionVariables) {
        [System.Environment]::SetEnvironmentVariable(
            $name,
            $savedEnvironment[$name],
            [System.EnvironmentVariableTarget]::Process)
    }

    if (Test-Path -LiteralPath $tempRoot) {
        $resolvedTempRoot = [System.IO.Path]::GetFullPath($tempRoot)
        $tempPrefix = $tempBase.TrimEnd(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
        if (-not $resolvedTempRoot.StartsWith($tempPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not ([System.IO.Path]::GetFileName($resolvedTempRoot)).StartsWith(
                "bounded-encounters-build-flag-audit-",
                [System.StringComparison]::Ordinal)) {
            throw "Refusing to remove an unexpected test directory: $resolvedTempRoot"
        }
        Remove-Item -LiteralPath $resolvedTempRoot -Recurse -Force
    }
}

# Negative fixtures intentionally leave the last launched Windows PowerShell
# process with a nonzero exit code. GitHub's pwsh wrapper propagates the ambient
# LASTEXITCODE after a sourced script, so clear it only after every assertion and
# cleanup step has completed successfully.
$global:LASTEXITCODE = 0
