# MergeMapper 1.6.1 review — 2026-08-27

Decision: **retain as conditional source-available infrastructure; do not
install in the current profile.** MergeMapper is useful only after zMerge has
changed plugin names/FormIDs. The current profile has no merge output and is
nowhere near the full-plugin ceiling.

Sources:

- Nexus: [mod 74689](https://www.nexusmods.com/skyrimspecialedition/mods/74689)
- Source: [alandtse/MergeMapper](https://github.com/alandtse/MergeMapper)
- License: Apache-2.0; the repository license overrides the restrictive generic
  Nexus permission toggles as the author states on the Nexus page.

## What it does

MergeMapper reads zMerge's `merge.json`, `map.json`, and merge log files. When
at least one valid merge exists, it:

1. hooks Papyrus `Game.GetFormFromFile` so old plugin/FormID references can be
   translated automatically;
2. exposes an optional revisioned SKSE API for DLLs that explicitly integrate
   MergeMapper; and
3. logs source plugins that are still enabled redundantly beside their merged
   output.

It does **not** make every SKSE DLL merge-aware. Native plugins must explicitly
consume its API. It does not create merges, resolve record conflicts, or make a
bad merge safe.

If no zMerge output is found, 1.6.1 does not install its message listener or
Papyrus hook and reports that it is staying inactive.

## Current-need test

The headless MO2 inventory on 2026-08-27 reported:

- 168 discovered plugins;
- 82 enabled plugins;
- 26 enabled full-slot plugins;
- 56 enabled ESL/light plugins; and
- zero `merge.json`, `map.json`, or `merge - *` outputs in the managed instance
  or physical game Data directory.

The full-plugin limit is therefore not remotely under pressure. ESL conversion
and purpose-built conflict patches remain preferable because they preserve
provenance and simplify updates. MergeMapper should be added only if a future
load order has an evidenced zMerge requirement.

## Source and package verification

| Item | Evidence |
|---|---|
| Current release | 1.6.1, Nexus file 794335, uploaded 2026-08-24 |
| Exact source | tag `v1.6.1`, commit `b7312a3823f8b89d08a7f3a1b393471a2cf982c4` |
| Pinned CommonLib | `3d81614617910e7f34b33d8750881811b5e36445` (CommonLibSSE-NG v6.7.0) |
| Nexus archive SHA-256 | `80be7314c7b61117b01636cd51655630a126d34dceb4a189944acc2bec3ab408` |
| Nexus DLL SHA-256 | `e44206c9a54db3bd101913361ff0e86e3f3c2c801a82d976925cdede45473831` |
| Local source-build DLL SHA-256 | `95ca86a47f32d3655ce76bde3fe65f9a45acf0deb96352251e82e2a331e5cf42` |
| Local source-build archive SHA-256 | `42c632430e2c68bd3309e245aa86fc6ecb927a1bdd9bbf90f74b2dd53d424773` |

The official and local DLLs are both unsigned, identify as version 1.6.1, and
export the same three SKSE symbols: `SKSEPlugin_Load`, `SKSEPlugin_Query`, and
`SKSEPlugin_Version`. They have the same imported-library set. Different hashes
and small code-size differences are expected from separate MSVC/PDB builds and
are not evidence of different source.

The generated plugin declaration is structure-independent and uses Address
Library. The pinned CommonLib sets the Address Library v5 extended flag used by
Skyrim 1.7.99. The installed Address Library v12 includes
`versionlib-1-7-99-0.bin`, so the static dependency gate is satisfied. This is
not represented as an in-game runtime test.

The exact tag built successfully with MSVC 19.44 and the manifest-pinned vcpkg
baseline. Nothing was deployed into MO2 or Skyrim.

## Engineering findings before adoption

1. **There is no meaningful automated test suite.** `BUILD_TESTS` refers to an
   unset CMake source list, while the only file under `test/` is stale
   `HitCounterManager` sample code for headers absent from this project. The CI
   named “PR Test Build” compiles Release but runs no tests.
2. **The Papyrus hook is not null-safe.** Its diagnostic log permits a null
   mod-name pointer, but the mapping branch immediately dereferences that same
   pointer. A malformed/native call can crash rather than fall through.
3. **Failed JSON reads can reuse stale state.** `GetMerges()` reuses one
   `json_data` object for both metadata and maps and does not clear it when an
   open/parse fails. A damaged merge folder can therefore be processed using
   the prior document rather than being rejected atomically.
4. **An unused helper returns a dangling pointer.** The wide-string overload of
   `GetNewFormID` returns `c_str()` from a local `std::string`. It is not on the
   public interface or called by current code, but should be removed or fixed.
5. **Default logging is unnecessarily expensive.** The shipped YAML uses debug
   level and flushes at trace, so every logged lookup is immediately flushed
   when merges are active. A production build should default to info/warn and
   flush on error while retaining opt-in diagnostics.
6. **Fatal startup paths violate the background-error policy.** Logging and
   messaging initialization call CommonLib's `report_and_fail` on failure.
   Before adoption, our fork should convert recoverable setup failures into a
   clean inactive state with a durable log entry and no user-facing dialog.

## Adoption gate

If zMerge becomes necessary later:

1. fork the Apache-2.0 source under our GitHub organization;
2. add real parser, malformed-input, ambiguous-merge, light-plugin, null-input,
   and no-merge tests;
3. fix the findings above and default to quiet durable logs;
4. create merges only from a frozen source-plugin set and retain source plugin
   provenance in the manifest;
5. install our source-built package through MO2, never into game Data directly;
6. validate the merge and every native consumer in a disposable profile before
   allowing it near a campaign save.

Until that gate is triggered, installing MergeMapper would add a DLL that has
nothing to map. The source checkout and reproducible build evidence are enough.
