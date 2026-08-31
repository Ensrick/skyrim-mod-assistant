# Configuration reference

The runtime reads `Data/SKSE/Plugins/BoundedEncounters.json`. When installed as
an MO2 mod, the archive root is the virtual `Data` directory, so the file is
located at `SKSE/Plugins/BoundedEncounters.json` inside the mod.

`BoundedEncounters.schema.json` is shipped beside it for JSON-aware editors,
continuous integration, and external validators. The runtime parser still
performs its own validation; the schema is not a substitute for fail-closed
runtime checks. Schema and parser changes must ship in the same version.

The first test candidate supports schema version `1` only. Unknown schema
versions and invalid values disable loading rather than being guessed at.

## Population model

Each eligible authored source has this expected extra count:

```text
uncapped = max(0, playerLevel - baselineLevel) * ratePerLevel
expected = min(uncapped, maxMultiplier - 1, maxExtrasPerSource)
```

The shipping values are conservative test defaults, not final balance
recommendations. Values outside the strict ranges below are rejected.

For example, the default general curve at player level 10 is
`(10 - 1) * 0.05 = 0.45`: each eligible source has a deterministic 45% chance
to add one companion. At level 30 the expectation is 1.45: one companion plus
a 45% chance of a second, subject to caps. A source uses the same deterministic
threshold at both levels, so its uncapped result cannot decrease merely because
the player leveled up.

## Root fields

| Field | Type | Default | Meaning |
| --- | --- | ---: | --- |
| `schemaVersion` | integer | `1` | Configuration contract version. Only `1` is accepted. |
| `enabled` | boolean | `true` | Master runtime switch. `false` preserves plugin loading and logging but suppresses population changes. |
| `observeOnly` | boolean | `true` | Audits eligible sources and planned counts without creating actors. The shipping alpha stays in this mode. |
| `debugLogging` | boolean | `false` | Enables diagnostic detail. Leave off for routine play. |
| `seed` | unsigned 64-bit integer | `1869507693` | Stable user-controlled input to deterministic per-source thresholds. Changing it reshuffles fractional outcomes. |
| `curves` | object | — | Per-category growth controls. |
| `limits` | object | — | Interior/exterior and placement safety bounds. |
| `exclusions` | object | — | Fail-closed actor exclusions. |
| `allowedSourcePlugins` | non-empty string array | five official masters | Reviewed defining and effective providers whose authored references and leveled-source graph may be considered. |
| `deniedPlugins` | string array | `[]` | Source plugins whose actors must never be expanded. Use plugin filenames, including `.esm`, `.esp`, or `.esl`. |

`observeOnly` does not disable classification or planning. It records source
and cell audits but returns before actor creation. Set it to `false` only in a
dedicated disposable test profile after reviewing observe-only logs; the
configuration is loaded at startup rather than hot-reloaded.

## Curves

The supported keys are `general`, `animalBeast`, and `giantMammoth`.

| Field | Type | Valid range | Meaning |
| --- | --- | --- | --- |
| `enabled` | boolean | — | Enables this category. |
| `ratePerLevel` | number | `0.0` through `1.0` | Linear expected extras added per player level above baseline. `0` disables growth. |
| `baselineLevel` | integer | `1` through `1000` | Player levels at or below this value receive no extras from the curve. |
| `maxMultiplier` | number | `1.0` through `10.0` | Caps the expected total population relative to one source. A fractional expectation can still round up on its deterministic threshold; use `maxExtrasPerSource` for a hard actor-count bound. |
| `maxExtrasPerSource` | integer | `1` through `32` | Hard per-source addition cap. |
| `maxExtrasPerCell` | integer | `1` through `256` | Hard additions cap for this category within one processed cell. |

Shipping test defaults:

| Category | Rate/level | Baseline | Maximum multiplier | Extras/source | Extras/cell |
| --- | ---: | ---: | ---: | ---: | ---: |
| `general` | `0.05` | `1` | `3.0` | `2` | `12` |
| `animalBeast` | `0.025` | `1` | `2.0` | `1` | `6` |
| `giantMammoth` | `0.01` | `1` | `1.5` | `1` | `2` |

`general` is the catch-all eligible hostile class, including ordinary humanoid
and undead encounters. `animalBeast` receives the lower wildlife curve.
Giants and mammoths receive their own stricter curve. Dragons remain excluded,
not a fourth curve.

## Limits

| Field | Type | Range | Default | Meaning |
| --- | --- | --- | ---: | --- |
| `maxAdditionalInterior` | integer | `1` through `256` | `12` | Global additions admitted in one interior cell. |
| `maxAdditionalExterior` | integer | `1` through `256` | `20` | Global additions admitted in one exterior cell. |
| `maxHostilesInterior` | integer | `1` through `512` | `24` | Total-hostile ceiling used before adding actors in an interior. Must be at least `maxAdditionalInterior`. |
| `maxHostilesExterior` | integer | `1` through `512` | `40` | Total-hostile ceiling used before adding actors in an exterior. Must be at least `maxAdditionalExterior`. |
| `maximumExteriorDistance` | number | `0` through `100000` | `12000.0` | Maximum world-unit distance from the player for an exterior source to be considered. |
| `placementRadiusMin` | number | `0` through `100000` | `96.0` | Minimum offset from the source actor for a generated companion. |
| `placementRadiusMax` | number | minimum through `100000` | `256.0` | Maximum offset from the source actor. |

Category caps, global addition caps, and hostile ceilings are cumulative safety
limits, not population targets. The lowest applicable remaining capacity wins.

## Exclusions

Schema version 1 requires every exclusion to be exactly `true`. Disabling one is
not a supported tuning option in the first test candidate; doing so makes the
configuration invalid and disables encounter scaling.

| Field | Excludes |
| --- | --- |
| `dragons` | Actors classified as dragons. |
| `unique` | Unique actor bases, normally named hand-authored NPCs. |
| `essential` | Actor bases protected from death by the engine. |
| `protected` | Protected actor bases. |
| `nonRespawning` | Actor bases that are not intended to respawn. |
| `persistentReferences` | References with persistent lifetime. |
| `questAliases` | References currently held by quest aliases. |
| `locationBosses` | Actors marked with a boss location-reference type. |
| `summons` | Summoned actors. |
| `commandedActors` | Actors controlled by another actor or effect. |

Some safety rules are unconditional even though they have no JSON switch:
generated actors cannot be sources; dead actors and player teammates are not
sources; and unsafe or unresolved engine data is rejected.

## Source-plugin policy

`allowedSourcePlugins` is a required, non-empty allowlist. It compares the
case-insensitive full filename of both the defining plugin and the effective
winning provider. The same rule is applied to the resolved actor base and every
form reachable through the leveled-template graph before active creation. The
shipping list therefore admits only wholly official-game source graphs:

```json
"allowedSourcePlugins": [
  "Skyrim.esm",
  "Update.esm",
  "Dawnguard.esm",
  "HearthFires.esm",
  "Dragonborn.esm"
]
```

A mod-added reference is therefore excluded by default even if it uses a
vanilla actor base. An official record overridden by an unlisted patch is also
excluded rather than treated as unchanged. Add a plugin only after its
encounter and lifecycle design has been reviewed on a disposable profile.

Use `deniedPlugins` for mods whose encounter scripting or actor lifecycle must
remain authoritative. Example:

```json
"deniedPlugins": [
  "ExampleQuestMod.esp",
  "ExampleSpawner.esl"
]
```

The deny check covers the defining and final provider for the actor reference,
resolved actor base, and spawn source. Denial wins if a filename is present in
both lists. Both arrays use case-insensitive full plugin filenames, not paths or
partial names. Entries must be non-empty and case-insensitively unique. The
runtime parser enforces the stronger case-insensitive rule even though JSON
Schema `uniqueItems` alone compares strings case-sensitively.

## Safe tuning workflow

1. Keep every exclusion enabled and `observeOnly` set to `true`.
2. Run the simulator against a copied configuration.
3. Adjust one category at a time.
4. Keep per-source caps small; use cell caps as a second boundary.
5. Review observe-only logs across representative interiors and exteriors.
6. If the audit is correct, set `observeOnly` to `false` only in a disposable
   test profile and repeat the matrix.
7. Review logs for exclusion, allowlist, and cap behavior.
8. Start a new test save after changing classification or lifecycle behavior.

Simulator usage:

```powershell
.\BoundedEncounters.Simulate.exe .\BoundedEncounters.json 8 1869507693
```

Arguments are the configuration path, authored source count, and optional seed.
The source count is `1` through `100000`; the optional seed is a decimal
unsigned 64-bit integer. The simulator prints JSON to standard output and never
edits the supplied file. It always models outcomes and never creates actors,
regardless of `observeOnly`.
