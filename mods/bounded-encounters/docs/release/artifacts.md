# Build artifacts and reproducible packaging

`tools/package.ps1` converts a tested CMake staging tree into a deterministic,
allowlisted MO2 archive and a matching full corresponding-source archive. It
does not discover or write to Skyrim, MO2, Vortex, Steam, or Nexus, and it makes
no network requests.

## Prerequisites

1. Build and test with `tools/build.bat`.
2. Commit the exact release inputs.
3. Confirm `build/release/stage` contains the DLL, JSON configuration, simulator,
   license, and readme produced by CMake.
4. Keep the pinned vcpkg checkout and its populated `buildtrees` available. The
   packager resolves it from `VCPKG_ROOT`, `BE_VCPKG_ROOT`, or
   `build/release/CMakeCache.txt`; all supplied locations must agree.
5. Set `VCPKG_BINARY_SOURCES=clear` for the clean build and release packaging.
   A clean/public package is rejected without that exact cache-disabled value;
   `-AllowDirty` can only produce a non-release engineering artifact.
6. Preserve `tools/build.log` from that build. Packaging requires the completion
   marker, zero restored packages, and exact source-build/install operations for
   the eight direct packages and two host helpers; it records the log SHA-256
   and parsed audit but does not distribute the path-bearing log.
7. Run packaging from PowerShell 7.4 or newer. PowerShell 7.4 is the minimum
   because that release moved `Test-Json` to JsonSchema.NET; packaging records
   the PowerShell, implementing-assembly, and JsonSchema.NET versions used.

From the canonical monorepo checkout:

```powershell
Set-Location .\mods\bounded-encounters
pwsh -NoProfile -File .\tools\package.ps1
```

The default output directory is `build/release/packages`. A normal artifact
requires a clean Git commit. `-AllowDirty` is available only for local
engineering builds: dirty inputs add `-dirty`; a clean input with binary-cache
use permitted adds `-nonrelease`. Both write `releaseEligible: false` into
`BUILD-INFO.json`.

Optional inputs:

```powershell
pwsh -NoProfile -File .\tools\package.ps1 `
  -StageRoot .\build\release\stage `
  -OutputDirectory .\build\release\packages `
  -Version 0.1.0-alpha.1 `
  -Runtime 1.7.104.0
```

Set `SOURCE_DATE_EPOCH` to control generated metadata and provenance. If it is
absent, the script uses the release commit timestamp. Every ZIP entry is
deliberately fixed to the minimum DOS wall time, `1980-01-01 00:00:00`, and the
packager verifies that value after writing both archives. ZIP does not preserve
a timezone; using the fixed past value prevents extraction in another timezone
from creating future-dated CMake inputs.

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
licenses/MinHook/LICENSE.txt
licenses/vcpkg/<direct-dependency>/copyright
MANIFEST.sha256
README.md
SBOM.spdx.json
THIRD-PARTY-NOTICES.md
```

The script copies only this allowlist. It requires MinHook's license and the
vcpkg-installed license text for every direct manifest dependency. It rejects
Bethesda plugin/archive formats, debug symbols, object/linker products, logs,
and saves. The alpha packager also rejects a shipping configuration that is not
valid against the bundled declared Draft 2020-12 JSON Schema or is not enabled,
observe-only schema version 1 with debug logging off, the reviewed 256-unit
maximum navmesh-snap distance, and the five official masters in the reviewed
source-allowlist order. CI exercises this gate in both package runs. Promoting a
future active-by-default release requires a deliberate package-policy review.

The reviewed schema was also independently validated offline with Ajv 8.17.1
in strict Draft 2020-12 mode (`validateSchema: true`, followed by compilation
and instance validation). That audit returned both `schemaValid: true` and
`instanceValid: true`. The SHA-256 of the temporary npm-resolution lock bytes
used for that audit was
`579f4da41fe0760afec8540eb80e02cf5c8adda27e3fe199c57a225220035d19`.
This is independent review evidence, not a portable cache path, repository
dependency, or release-time npm requirement; the offline package gate remains
PowerShell 7.4+ `Test-Json` backed by JsonSchema.NET.

The sibling corresponding-source archive is named
`BoundedEncounters-<version>-corresponding-source.zip`. Its top-level layout is:

```text
README-CORRESPONDING-SOURCE.md
SOURCE-MANIFEST.sha256
SOURCE-PROVENANCE.json
project/                                      # tracked project source/build files
build/ci/bounded-encounters.yml               # exact monorepo release workflow
dependencies/CommonLibSSE-NG/                # pinned tracked fork source
dependencies/MinHook/                        # pinned tracked v1.3.4 source
dependencies/vcpkg/<direct-dependency>/
  source/                                     # exact post-patch source tree
  port/                                       # exact baseline port recipe
  installed/copyright
  installed/vcpkg.spdx.json
  installed/vcpkg_abi_info.txt
  installed/info-list.txt
  installed/status.txt
  installed/features/<feature>.status.txt     # exact reviewed feature stanzas
  installed/upstream-resource-provenance.json
  PROVENANCE.json
dependencies/vcpkg/<build-helper>/
  port/                                       # exact source-free helper recipe
  installed/x64-windows/share/<helper>/       # full installed control scripts
  installed/info-list.txt
  installed/status.txt
  PROVENANCE.json
build/vcpkg/BASELINE.txt
build/vcpkg/LICENSE.txt
build/vcpkg/triplets/x64-windows-static-md.cmake
build/vcpkg/triplets/x64-windows.cmake
build/vcpkg/scripts/                           # pinned tracked script sources
```

The project tree excludes its CommonLib gitlink because the exact CommonLib tree
is included separately. CommonLib's nested OpenVR gitlink is recorded in
provenance and omitted because VR is disabled and OpenVR source is not compiled.
`COPYING` and `EXCEPTIONS.md` are required in both archives. MinHook's exact
tracked source is pinned to `v1.3.4` commit
`c3fcafdc10146beb5919319d0683e44e3c30d537`; its license is also required in
both archives. CommonLib compiles `hde64.c`, whose direct source/header closure
is `hde64.c`, `hde64.h`, `pstdint.h`, and `table64.h`. The project root
predeclares that immutable commit before adding CommonLib; packaging gates the
predeclaration, the CommonLib recipe, and the actual fetched checkout. The
tracked monorepo workflow controlling tagged builds is copied separately under
`build/ci/` and fingerprinted (and index-byte verified for clean releases).

For each direct vcpkg dependency, packaging requires exactly one source tree
whose reviewed file count and whole-tree SHA-256 match the release policy. It
also checks the installed version, port version, ABI, status, SPDX port and
binary records, upstream-resource records, installed/buildtree ABI metadata,
baseline port-tree object, and installed file-inventory name. Missing,
mismatched, or ambiguous input fails packaging. Source inputs containing Windows
reparse points are rejected.

The two host-only helper packages are source-free ports: they fetch no upstream
tree and install CMake control scripts. Packaging validates each helper's exact
version and port tree, derives its host-specific ABI from status, requires that
ABI to equal both installed and buildtree ABI-file hashes, and retains its full
installed share tree, SPDX/license, inventory, status, recipe, tool-version/hash
evidence, and provenance. It also gates the exact ten base packages plus the
`spdlog:fmt` and `spdlog:tz-offset` feature stanzas.

The pinned target and host triplets and all other tracked vcpkg scripts are
included and fingerprinted. The baseline's two tracked
`tls12-download*.exe` general-purpose downloader binaries are omitted from the
source archive; exact Git object IDs, SHA-256 values, and exclusion reasons are
recorded, and the reviewed build does not use them. No PE binaries are permitted
in the corresponding-source archive.

## Reconstructing the source layout

The archive's generated `README-CORRESPONDING-SOURCE.md` gives exact `pwsh`
commands and requires PowerShell 7.4+ in an x64 Visual Studio 2022 developer
environment. The reconstruction first validates every manifest hash and proves
that the listed paths exactly equal the extracted file set, rejecting
duplicate, rooted, or escaping entries. It fails if
`project/extern/CommonLibSSE-NG/` already exists, then copies the exact bundled
dependency there without nesting. Strictly after manifest validation and before
any mutation, it sets every verified extracted file and directory to a fixed
past UTC modification time and checks none is newer than the normalization
cutoff. This independently prevents local-time extraction from causing a
Ninja/CMake regeneration loop without changing file bytes. It then checks out
and bootstraps vcpkg at the recorded baseline, sets
`VCPKG_BINARY_SOURCES=clear`, asserts the checkout HEAD equals that baseline,
and configures the project with both. Every native clone/checkout/bootstrap/
configure/build/test command is fail-fast on a nonzero exit code.

```text
-DFETCHCONTENT_SOURCE_DIR_HDE64=<archive>/dependencies/MinHook
-DFETCHCONTENT_FULLY_DISCONNECTED=ON
```

Those options force CommonLib to consume the bundled MinHook tree without a
FetchContent clone. vcpkg still resolves through its pinned checkout and may
obtain registry archives, but the reviewed reconstruction disables its binary
cache. The archived `port/` recipes, post-patch `source/` trees, helper control
scripts, and vcpkg scripts are audit copies identified by
`SOURCE-PROVENANCE.json`; they do not masquerade as a supported vcpkg offline
overlay or tool installation.

The corresponding-source archive is not a turnkey offline compiler image. It
does not bundle Visual Studio, CMake, Ninja, the vcpkg executable/registry data,
upstream download archives, or vcpkg binary-cache state. Although exact helper
port and installed-script closures are present, they are not a pre-seeded tool
installation. A fully offline rebuild therefore requires tools and downloads
to be pre-seeded independently and is not claimed or tested. The packaging
operation itself is offline and never downloads missing inputs.

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
SHA-1/SHA-256 values, the source commit, pinned CommonLibSSE-NG and MinHook
commits, every direct vcpkg dependency's exact resolved version, port version,
license, port-tree object and ABI provenance, and both build helpers as
build-only dependencies. The main package declares the original project's MIT
license but conservatively concludes `NOASSERTION` for the analyzed combined
payload; its comment and the linked-package records preserve CommonLib's GPL
terms and unchanged custom Modding Exception without inventing a standard SPDX
exception identifier.

For the initial runtime target, the actual CommonLibSSE-NG build pin is Ensrick
fork commit `a9d7d4523d5e1abc8b296bd99683b7df11df652f`. Its reviewed direct parent is
upstream `v7.0.0` commit `8b032fa992750d654d6d38a33731714d8b86be1f`.
Packaging rejects a different build commit, base commit, or submodule URL, so a
dependency upgrade requires a deliberate source and documentation change.

`BUILD-INFO.json` records the supported runtime, source commit, dirty status,
`SOURCE_DATE_EPOCH`, CommonLib and MinHook pins, resolved vcpkg baseline,
target/host triplets, direct dependencies and build helpers, whether the binary
cache-disabled source build was verified from `tools/build.log`, that log's
SHA-256/cache audit, and the safety-critical shipping configuration mode and
source allowlist, including the reviewed maximum navmesh-snap distance. It also
records the exact CMake, Ninja, MSVC compiler/tools, Windows SDK, PowerShell,
`Test-Json` implementing assembly, and JsonSchema.NET versions observed by the
reviewed build and package gates.

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
- tracked project, monorepo release-workflow, CommonLibSSE-NG, and MinHook source
  bytes;
- exact vcpkg post-patch source, port recipe, installed SPDX/license/provenance,
  status, inventory, and ABI metadata bytes;
- exact build-helper ports, installed control scripts, host status/inventory/ABI
  metadata, pinned vcpkg scripts (minus recorded unused PE exclusions), and
  target/host triplets;
- the same completed cache-disabled `tools/build.log` bytes (only its hash and
  parsed package-operation audit enter the archives);
- `SOURCE_DATE_EPOCH`;
- PowerShell/.NET compression implementation; and
- packaging-script version.

The MSVC linker and compiler reproducibility flags address binary timestamps,
but reproducibility must still be verified by two clean builds. A successful
second build is evidence, not an assumption.
