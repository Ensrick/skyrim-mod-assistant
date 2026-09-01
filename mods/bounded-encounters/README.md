# Bounded Encounters

Bounded Encounters is an open-source SKSE plugin for Skyrim Special Edition
and Anniversary Edition. It grows encounter populations with the player while
preserving authored enemy selection, using separate configurable curves and
hard safety limits for ordinary enemies, animals and beasts, and large
creatures.

The project is under active development. Its first packaged build is a test
candidate, not a finished balance recommendation or a Nexus release.

## Design

Skyrim usually represents an encounter as multiple placed actor or leveled-
actor references. A leveled list generally selects what one reference becomes;
it does not expose one universal encounter-size value. Bounded Encounters
therefore evaluates each eligible authored source once per cell per plugin
session and may add independently resolved companion actors.

For a category with rate `r`, player level `L`, and baseline level `B`, the
linear model is:

```text
progress = max(0, L - B)
expected extras per source = progress * r
```

The integer portion is guaranteed and the fractional portion is compared with
one deterministic threshold derived from the configured seed and source. A
result of `1.45` means one extra actor plus a 45% chance of a second. Reusing the
same threshold across player levels keeps the uncapped result monotonic instead
of rerolling a source at every level. Added actors are marked and never become
new multiplication sources. A separately domain-separated deterministic rank
decides which successful rolls survive a saturated cell cap.

When an authored actor came from a leveled-actor list, the plugin reuses that
original list so the companion is resolved independently instead of blindly
cloning the already-selected bandit. Independent resolution can legitimately
select the same list entry again; diversity is possible, not guaranteed. The
initial safety candidate rejects fixed resolved sources; expanding those
requires a separately reviewed policy.

## Safety defaults

The plugin fails closed. It excludes:

- dragons;
- unique, essential, protected, and non-respawning actor bases;
- persistent references and actors held by quest aliases;
- location-reference bosses;
- summoned or commanded actors;
- player teammates, dead actors, and actors that are not hostile to the player;
- every actor created by Bounded Encounters itself.

The shipping configuration is observe-only: it audits sources and calculated
counts but creates no actors. Its source allowlist contains only the five
official masters, so mod-authored references are excluded until reviewed and
explicitly admitted.

Audit output is headless and bounded: the plugin uses an 8 MiB rotating log,
keeps the active file plus two rotated archives (three files, about 24 MiB
maximum), and rotates a nonempty log when a new process opens it. Default
observe-only logging emits one cell summary per evaluated cell; per-source
FormID detail requires `debugLogging: true`. Exception diagnostics are capped
at 4 KiB before reaching any log sink, including malformed-configuration
errors. It does not use modal error dialogs, and it refuses to load if the
bounded audit log cannot be established.

Configuration places independent limits on extras per source, category, cell,
and interior/exterior population. Active test mode also rejects a spawn when
the nearest navmesh vertex lies beyond the configured distance from the planned
position, and an unregistered created reference is rolled back on every failure
path. Exclusion always wins over classification.

## Configuration and simulator

The runtime reads:

```text
Data/SKSE/Plugins/BoundedEncounters.json
```

The archive also ships `BoundedEncounters.schema.json` beside the configuration
for editor validation and automation.

The same configuration is consumed by `BoundedEncounters.Simulate.exe`, which
prints uncapped expectations, deterministic fractional-capacity projections,
and sampled populations without launching Skyrim. A fractional-capacity
projection is not labeled as the statistical expectation after capped
Bernoulli outcomes. The shipped configuration is deliberately conservative and
remains easy to revise after playtesting. Simulator projections do not create
actors even when `observeOnly` is `false`.

## Building

Requirements:

- Visual Studio 2022 Build Tools with the x64 C++ workload;
- CMake and Ninja (the Visual Studio bundled copies work);
- vcpkg;
- the pinned Ensrick CommonLibSSE-NG no-modal-errors fork at commit
  `a9d7d4523d5e1abc8b296bd99683b7df11df652f`, based directly on upstream
  `v7.0.0` commit `8b032fa992750d654d6d38a33731714d8b86be1f`.

Root CMake predeclares CommonLib's hde64 FetchContent dependency at immutable
MinHook commit `c3fcafdc10146beb5919319d0683e44e3c30d537` before adding CommonLib.

Run `tools/build.bat`. The script performs a clean Release configuration,
builds the plugin and simulator, runs unit tests, and stages an MO2-ready tree
under `build/release/stage`. It never copies files into Skyrim or a mod manager.
Tagged release builds set `VCPKG_BINARY_SOURCES=clear`; release packaging
rejects a clean/public artifact without that exact cache-disabled policy and a
complete `tools/build.log` proving all ten reviewed vcpkg packages were built
and installed with zero binary-cache restores.

## Runtime scope

The initial compatibility target is Steam Skyrim `1.7.104.0`, SKSE `2.3.1`,
and Address Library format 5. The build pins Ensrick's one-commit
CommonLibSSE-NG no-modal-errors fork at
`a9d7d4523d5e1abc8b296bd99683b7df11df652f`. Its upstream base is `v7.0.0`
commit `8b032fa992750d654d6d38a33731714d8b86be1f`, so both the actual build input
and its upstream provenance are reviewable. Additional runtimes are not
claimed until they receive their own build and game tests.

## Project documentation

- [Architecture and design](docs/architecture.md)
- [Configuration reference](docs/configuration.md)
- [Runtime compatibility matrix](docs/compatibility.md)
- [Spawn lifecycle and save safety](docs/save-lifecycle.md)
- [Verification and test plan](docs/test-plan.md)
- [Build-artifact format](docs/release/artifacts.md)
- [Nexus prerelease checklist](docs/release/nexus-prerelease-checklist.md)

## Publication boundary

The repository contains original source, configuration, tests, and build
recipes. It contains no Bethesda assets and no third-party mod payload. A
future Nexus package will be built from a tagged GitHub release only after an
in-game stability and save-integrity test.

Original Bounded Encounters source is MIT-licensed. Release binaries statically
link the pinned Ensrick CommonLibSSE-NG fork, which remains GPL-3.0-or-later
with its upstream Modding Exception. Each binary release must retain the GPL
and exception texts and ship a matching corresponding-source archive for the
actual fork commit. That source archive also closes over the project, MinHook
`hde64`, every direct vcpkg dependency, the two source-free vcpkg CMake helper
ports and installed scripts, and the pinned vcpkg build scripts/triplets used by
the reviewed build, plus the exact monorepo release workflow. It is not a
bundled compiler or turnkey offline build environment. See
[Third-party notices](THIRD-PARTY-NOTICES.md) and
[Build-artifact format](docs/release/artifacts.md).

Canonical publication lives in the
[skyrim-mod-assistant monorepo](https://github.com/Ensrick/skyrim-mod-assistant)
under `mods/bounded-encounters`; standalone development checkouts are not a
separate release authority.
