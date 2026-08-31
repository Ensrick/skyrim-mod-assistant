# Build artifacts and reproducible packaging

`tools/package.ps1` converts a tested CMake staging tree into a deterministic,
allowlisted MO2 archive and a matching CommonLibSSE-NG corresponding-source
archive. It does not discover or write to Skyrim, MO2, Vortex, Steam, or Nexus.

## Prerequisites

1. Build and test with `tools/build.bat`.
2. Commit the exact release inputs.
3. Confirm `build/release/stage` contains the DLL, JSON configuration, simulator,
   license, and readme produced by CMake.
4. Run packaging from PowerShell 7 or newer.

From the canonical monorepo checkout:

```powershell
Set-Location .\mods\bounded-encounters
pwsh -NoProfile -File .\tools\package.ps1
```

The default output directory is `build/release/packages`. A normal artifact
requires a clean Git commit. `-AllowDirty` is available only for local
engineering builds: it adds `-dirty` to the filename and writes
`releaseEligible: false` into `BUILD-INFO.json`.

Optional inputs:

```powershell
pwsh -NoProfile -File .\tools\package.ps1 `
  -StageRoot .\build\release\stage `
  -OutputDirectory .\build\release\packages `
  -Version 0.1.0-alpha.1 `
  -Runtime 1.7.104.0
```

Set `SOURCE_DATE_EPOCH` to control generated metadata and ZIP entry timestamps.
If it is absent, the script uses the release commit timestamp. The ZIP timestamp
is clamped to 1980 because that is the earliest date representable by the ZIP
format.

## Archive layout

```text
SKSE/Plugins/BoundedEncounters.dll
SKSE/Plugins/BoundedEncounters.json
SKSE/Plugins/BoundedEncounters.schema.json
tools/BoundedEncounters.Simulate.exe
docs/architecture.md
docs/compatibility.md
docs/configuration.md
docs/save-lifecycle.md
docs/test-plan.md
docs/release/artifacts.md
docs/release/nexus-prerelease-checklist.md
BUILD-INFO.json
LICENSE
licenses/CommonLibSSE-NG/COPYING
licenses/CommonLibSSE-NG/EXCEPTIONS.md
licenses/CommonLibSSE-NG/LICENSE-MIT
licenses/CommonLibSSE-NG/LICENSES-README.md
licenses/vcpkg/<direct-dependency>/copyright
MANIFEST.sha256
README.md
SBOM.spdx.json
THIRD-PARTY-NOTICES.md
```

The script copies only this allowlist. It requires the vcpkg-installed license
text and a reviewed SPDX license mapping for every direct manifest dependency.
It rejects Bethesda plugin/archive formats, debug symbols, object/linker
products, logs, and saves. The alpha packager also rejects a shipping
configuration that is not enabled, observe-only schema version 1 with the five
official masters in the reviewed source-allowlist order. Promoting a future
active-by-default release requires a deliberate package-policy review.

The sibling corresponding-source archive is named
`BoundedEncounters-<version>-CommonLibSSE-NG-a9d7d452-source.zip`. It contains
every available tracked file from the actual Ensrick fork build commit
`a9d7d4523d5e1abc8b296bd99683b7df11df652f`, plus:

```text
README-CORRESPONDING-SOURCE.md
SOURCE-MANIFEST.sha256
SOURCE-PROVENANCE.json
```

A nested gitlink omitted from the source bundle is recorded in provenance and
excluded only when it is not compiled into the supported build, whether or not
the checkout populated it. The current omitted OpenVR gitlink is not used
because VR support is disabled. `COPYING` and `EXCEPTIONS.md` are required in
both the corresponding-source archive and binary archive.

## Integrity files

`MANIFEST.sha256` contains sorted lowercase SHA-256 entries for every other file
in the archive. Paths use forward slashes and are relative to the archive root.
The sibling `.zip.sha256` file verifies the archive itself.

Example archive verification:

```powershell
$expected = (Get-Content .\BoundedEncounters-*.zip.sha256).Split(' ')[0]
$actual = (Get-FileHash .\BoundedEncounters-*.zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw 'Archive hash mismatch' }
```

`SBOM.spdx.json` is an SPDX 2.3 document. It inventories payload files, their
SHA-1/SHA-256 values, the source commit, pinned CommonLibSSE-NG commit, and
direct vcpkg dependency names/baseline. A dependency version represented only
by the vcpkg baseline is not a claim about the exact resolved port version; CI
and vcpkg build logs remain the resolution evidence.

For the initial runtime target, the actual CommonLibSSE-NG build pin is Ensrick
fork commit `a9d7d4523d5e1abc8b296bd99683b7df11df652f`. Its reviewed direct parent is
upstream `v7.0.0` commit `8b032fa992750d654d6d38a33731714d8b86be1f`.
Packaging rejects a different build commit, base commit, or submodule URL, so a
dependency upgrade requires a deliberate source and documentation change.

`BUILD-INFO.json` records the supported runtime, source commit, dirty status,
`SOURCE_DATE_EPOCH`, pinned build inputs, and the safety-critical shipping
configuration mode and source allowlist.

The package command returns JSON containing paths and hashes for both archives
and their sibling `.sha256` files. Attach the binary, corresponding source, and
both hashes to the same GitHub release. A Nexus binary must retain a public,
same-version link to those artifacts (or upload the source archive alongside
it).

## Reproducibility scope

The script fixes entry order, paths, timestamps, text encoding, and manifest
order. Byte-identical archives require the same:

- source commit and submodule commits;
- staged binary bytes;
- configuration and documentation bytes;
- tracked CommonLibSSE-NG source bytes;
- `SOURCE_DATE_EPOCH`;
- PowerShell/.NET compression implementation; and
- packaging-script version.

The MSVC linker and compiler reproducibility flags address binary timestamps,
but reproducibility must still be verified by two clean builds. A successful
second build is evidence, not an assumption.
