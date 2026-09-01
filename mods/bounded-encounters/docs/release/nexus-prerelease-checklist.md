# Nexus prerelease checklist

This checklist is intentionally conservative. Do not publish to Nexus until the
user has verified the GitHub test candidate in game. A GitHub alpha is not a
Nexus release approval.

## Source and governance

- [ ] Release commit is reviewed and reachable from `main`.
- [ ] Required branch checks pass.
- [ ] The semantic release version agrees in `Version.h`, `vcpkg.json`,
      documentation, archive names, and scoped tag
      `bounded-encounters/v<version>`; its numeric base agrees with CMake and
      SKSE plugin metadata.
- [ ] Annotated tag is signed or created by the protected release workflow.
- [ ] GitHub release is marked prerelease for alpha/beta artifacts.
- [ ] MIT license and third-party notices are current; CommonLibSSE-NG is
      identified as GPL-3.0-or-later with its Modding Exception.
- [ ] Repository contains no Bethesda assets, Nexus payloads, API keys, saves,
      logs, personal paths, or private test data.
- [ ] All included code has clear provenance and redistribution permission.

## Build and artifact

- [ ] Build starts from a clean tagged checkout with recursive submodules.
- [ ] Tagged build and packaging run with `VCPKG_BINARY_SOURCES=clear`; the build
      log contains actual dependency `Building` lines and zero restored packages,
      and `BUILD-INFO.json` records `vcpkgBinaryCacheDisabled: true`.
- [ ] CommonLibSSE-NG is the Ensrick no-modal-errors fork at
      `a9d7d4523d5e1abc8b296bd99683b7df11df652f`, its direct parent is upstream
      `v7.0.0` commit `8b032fa992750d654d6d38a33731714d8b86be1f`, and the vcpkg baseline matches
      the release notes.
- [ ] Release tests and simulator smoke test pass.
- [ ] Archive is produced only by `tools/package.ps1`.
- [ ] Three isolated, cache-disabled builds of the exact commit produce identical
      four-file release directories, including byte-identical DLL and simulator
      payloads; a signed-tag build also matches the canonical successful
      protected-main artifact for that commit.
- [ ] Binary and corresponding-source ZIP entries are in strict ordinal path
      order, and each internal manifest lists its exact non-manifest path set in
      the same strict ordinal order.
- [ ] The independent comparison gate recomputes every internal hash, enforces
      canonical UTF-8-without-BOM/LF manifests and normalized ZIP metadata, and
      requires canonical one-line sibling hashes while rejecting Windows-unsafe
      or ambiguous extraction paths.
- [ ] `MANIFEST.sha256` verifies every payload file.
- [ ] SPDX SBOM parses and identifies the release commit.
- [ ] Binary archive contains the verbatim CommonLibSSE-NG `COPYING` and
      `EXCEPTIONS.md` files.
- [ ] Binary archive contains MinHook v1.3.4's verbatim `LICENSE.txt`, and its
      SHA-256 agrees with the copy in the corresponding-source archive.
- [ ] Binary archive retains the vcpkg-provided copyright/license file for every
      direct build dependency, and SBOM license identifiers match those texts.
- [ ] Deterministic corresponding-source archive contains the tracked project,
      full tracked Ensrick CommonLib fork at the exact build commit (including
      the no-modal patch), tracked MinHook v1.3.4 source, and the exact
      post-patch source tree for all eight direct vcpkg dependencies.
- [ ] Project CMake predeclares hde64 at immutable MinHook commit
      `c3fcafdc10146beb5919319d0683e44e3c30d537` before CommonLib, and the source
      archive retains the exact monorepo release workflow under `build/ci/`.
- [ ] Each bundled direct vcpkg dependency has its exact resolved version, port
      version, ABI, baseline port tree, port recipe, deterministic installed-SPDX
      projection, upstream-resource provenance, license, status stanza, and file
      inventory.
- [ ] Installed status contains exactly the reviewed ten base packages and only
      the `spdlog:fmt` and `spdlog:tz-offset` feature stanzas.
- [ ] Corresponding source includes both exact source-free vcpkg CMake helper
      ports, their complete installed host share trees/SPDX/license/inventory/
      status/ABI provenance, both target and host triplets, and the pinned
      tracked vcpkg scripts.
- [ ] The only omitted tracked vcpkg scripts are the two reviewed unused
      `tls12-download*.exe` PEs; provenance records their Git object IDs, hashes,
      and reasons, and the source archive contains no PE binaries.
- [ ] The corresponding-source archive and `.sha256` are attached beside every
      GitHub binary release and retained while the binary is distributed.
- [ ] Extract the actual corresponding-source ZIP into a fresh directory,
      verify every entry against `SOURCE-MANIFEST.sha256`, populate
      `project/extern/CommonLibSSE-NG` exactly as documented, and exercise the
      documented reconstruction through at least a clean CMake configure
      (preferably build and CTest). Record whether acceptance was configure-only
      or a complete build-and-test run. Confirm every ZIP entry uses the fixed
      1980 wall time, verified extracted inputs are normalized to the documented
      fixed-past UTC time before configure, and CMake does not regenerate in a
      loop; do not imply an offline rebuild.
- [ ] Archive contains only `SKSE/Plugins`, optional offline `tools`, license,
      readme, notices, release documentation, manifest, and SBOM.
- [ ] No tool deploys into Skyrim or an MO2/Vortex directory.
- [ ] Archive SHA-256 is recorded in GitHub release notes.
- [ ] Shipping JSON remains `observeOnly: true`, has `debugLogging: false`, and
      keeps `maximumNavmeshSnapDistance: 256.0`; its source allowlist contains
      only the five official masters.
- [ ] Packaging validates the shipping JSON against the bundled declared Draft
      2020-12 schema under PowerShell 7.4+ `Test-Json`/JsonSchema.NET before
      applying the stricter alpha release-policy gates, and `BUILD-INFO.json`
      records the validator/toolchain versions used.
- [ ] Independent strict Draft 2020-12 validation with Ajv 8.17.1 reports both
      the schema and shipping instance valid; retain its evidence separately
      without adding npm or a temporary cache path as a release dependency.

## Runtime and compatibility

- [ ] Tested Skyrim executable is exactly `1.7.104.0`.
- [ ] Tested SKSE is exactly `2.3.1`.
- [ ] Matching Address Library format-5 database is installed.
- [ ] Unsupported runtimes fail closed without a modal dialog.
- [ ] Clean log shows configuration, runtime gate, hooks, and event registration.
- [ ] Compatibility page contains no untested claims.
- [ ] Required Nexus dependencies are linked rather than bundled.

## Functional and save testing

- [ ] Every scenario in `docs/test-plan.md` passes.
- [ ] Dragons, bosses, unique/essential/protected/quest actors, summons,
      commanded actors, and teammates remain excluded.
- [ ] Leveled sources reroll companions rather than cloning resolved actors when
      the original leveled form is available; the post-create actor retains that
      exact leveled-source identity, while selecting the same NPC entry remains
      a valid independent outcome.
- [ ] Generated actors never multiply generated actors.
- [ ] Observe-only matrix creates zero actors before active testing begins.
- [ ] Non-allowlisted mod-authored and fixed resolved sources remain excluded.
- [ ] Per-source, category, additions, and total-hostile caps hold.
- [ ] Save/quit/reload and revert tests pass with live and dead generated actors.
- [ ] Save inspection finds no serialized generated references.
- [ ] Uninstall test passes on a disposable save made after a clean quit.
- [ ] Endurance target for the intended release channel is met.
- [ ] User explicitly approves the tested package for Nexus upload.

## Nexus page and files

- [ ] Mod description explains per-source linear scaling and hard caps without
      promising a fixed encounter multiplier.
- [ ] Requirements, supported runtime, install path, upgrade steps, and uninstall
      warning are prominent.
- [ ] Nexus lists the matching corresponding-source archive as an optional file
      or links directly to the same-version GitHub release that permanently
      hosts it.
- [ ] Alpha/beta status and disposable-save recommendation are prominent.
- [ ] Default numbers are labeled test defaults, not a final balance guarantee.
- [ ] Configuration reference and source repository are linked.
- [ ] Permissions match MIT for original source and clarify that dependencies and
      Bethesda assets are not included.
- [ ] File name includes semantic version and runtime target.
- [ ] GitHub tag, commit, archive SHA-256, and manifest are linked in changelog.
- [ ] No optional files silently replace a newer main file.
- [ ] A rollback copy of the prior Nexus artifact and description is retained.

## Post-publication

- [ ] Download the published Nexus archive and verify its SHA-256/content.
- [ ] Verify the public corresponding-source link without an authenticated
      maintainer session.
- [ ] Install that downloaded archive into a clean disposable profile.
- [ ] Perform one launch, encounter, save, quit, and reload smoke test.
- [ ] Watch crash/save-integrity reports before promoting channels.
- [ ] Triage reports with exact runtime/config/log details; do not infer support
      from endorsement count alone.
