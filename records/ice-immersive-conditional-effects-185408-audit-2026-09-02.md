# ICE - Immersive Conditional Effects 1.0 exact-release audit

Audit date: 2026-09-02

Runtime target: Skyrim Special Edition `1.7.104.0` / SKSE `2.3.1` /
Address Library format 5

Tracker: [issue #95](https://github.com/Ensrick/skyrim-mod-assistant/issues/95)

Disposition: **HOLD / do not install.** The exact current archive was retained in
the MO2 download cache for inspection only. Nothing was copied to `mods`, no
plugin was activated, and Nexus 185408 was not marked Keep or Skip.

## Executive verdict

ICE has a good high-level idea and is materially lighter than the old Wet and
Cold actor-polling design. Its own records are ESL-safe, its Papyrus source is
included, its MCM and SPID/KID configuration are understandable, and it has no
native DLL/runtime-version hazard.

Version 1.0 nevertheless fails this project's quality gate. The plugin carries
54 broad, non-identical Dragonborn overrides (the Solstheim worldspace plus 53
exterior cells). Most deliberately redraw a vanilla weather region, but one
cell loses all eight of its existing weather, audio, border, and navmesh region
assignments. Its advertised dependency list also omits a runtime needed to
populate most of its face-cover weather list, its cold-weather items have no
Survival warmth integration, and its SPID mannequin exclusion uses the wrong
EditorID. It permanently injects equipment into NPC inventories, which can
expose the items on corpses or mannequins.

Do not paper over the destructive record or broad cell conflict surface with a
blind downstream conflict patch. A clean vendor release should preserve every
unrelated region assignment and document why its snow-region remap is needed.
Nexus permissions require the author's permission before modifying or
redistributing the file, so an owned clean-room alternative or an author update
is preferable.

## Exact artifact

| Field | Value |
|---|---|
| Nexus page | [185408](https://www.nexusmods.com/skyrimspecialedition/mods/185408) |
| Version | `1` / changelog `1.0.0` |
| Main file | Nexus file `776380` |
| Uploaded | 2026-07-14 |
| Archive | `185408-776380.zip` |
| Archive size | 63.6 MB |
| SHA-256 | `C7147C0DE837E25ED42E27A74E3E9EFE0C463089DB3FEC5F1B86E3EFC7C525E8` |

The archive is in
`mo2-instances/skyrim-se/downloads/185408-776380.zip`; extraction and Spriggit
serialization were performed outside the active MO2 `mods` directory.

## Plugin audit

`ICE.esp` is ESL-flagged and has six masters: Skyrim, Update, Dawnguard,
HearthFires, Dragonborn, and `ccQDRSSE001-SurvivalMode.esl`. It contains 244
new records and 54 overrides:

| Record type | New | Overrides |
|---|---:|---:|
| ARMA | 100 | 0 |
| ARMO | 32 | 0 |
| ARTO | 27 | 0 |
| CELL | 53 | 53 |
| FLST | 8 | 0 |
| GLOB | 12 | 0 |
| KYWD | 8 | 0 |
| MGEF | 9 | 0 |
| PERK | 1 | 0 |
| QUST | 3 | 0 |
| SPEL | 3 | 0 |
| TXST | 41 | 0 |
| WRLD | 1 | 1 |

There are no placed references, navmeshes, or deleted records. All 54
overrides differ from the current Dragonborn master; none is an identical-to-
master record that can be dismissed as harmless noise.

The Solstheim implementation is the blocker:

- `DLC2SolstheimWorld` changes the localized `FULL` string ID to literal
  English `Solstheim`. This is a localization regression on the parent
  worldspace record.
- Of the 53 exterior cells, 52 deliberately remap
  `WeatherDLC2SolstheimSnow` (`Dragonborn.esm` FormID `029F3B`): 36 gain the
  region and 16 lose it. That is feature-related rather than random, because
  ICE's cold spell tests this same region. It is nevertheless a broad CELL/XCLR
  conflict surface for every Solstheim landscape, weather, sound, and region
  patch.
- Dragonborn cell `0000EE52` (grid `7,12`) is not part of that coherent remap.
  ICE removes its complete eight-entry XCLR list and supplies no replacement.
  The deleted assignments are `WeatherVolcanicAsh01`,
  `WeatherDLC2SolstheimMtns`, `Region332`, `DLC2SolstheimBorderRegion`,
  `DLC2NavmeshRegion`, `AudioExtDLC2Ashlands`, `WeatherVolcanicAsh02`, and
  `AudioExtMountainsHeavy01`. That can change unrelated weather, audio, border,
  and navigation-region behavior and is a destructive override.
- The cell records are CK-resaved from form version 43 to 44. Their XCLC land-
  flag byte remains zero; only the three unused bytes change, so that specific
  binary difference is noise rather than a gameplay defect.

Spriggit 0.41.0 serialized the plugin and passed its lossless round-trip
validation. The override finding therefore does not depend on a lossy parser.

The Survival Mode master is unnecessary in the inspected release: no serialized
record references it. The 32 clothing records likewise contain no Survival
warmth/cold keyword. A slot-46 cloak visually appearing in snow is not the same
as providing warmth under Starfrost/Survival Mode Improved.

## Runtime and script design

The page says the mod uses “almost no scripts” and that nothing runs on a loop.
The exact archive contains nine compiled PEX files plus all nine PSC sources.
Champollion decompilation shows shipped binaries following the included sources;
debug line mappings correspond to the source operations, and eight binaries
were compiled immediately before release. The unused rain script dates to
2025-09-08.

The actual design is still comparatively lightweight, but it is not
scriptless:

- SPID distributes one condition-driven ability to every eligible NPC.
- Starting and ending gear effects run per-actor Papyrus that searches the
  inventory, adds an ICE item when absent, force-equips it, and later unequips
  it.
- `ICE_BlizzardMonitor` polls current weather every 10 real seconds for the
  lifetime of its quest. This is a single small loop, not a Wet and Cold-style
  actor sweep.
- Cleanup retries up to three times after load. It does not remove the injected
  gear from inventory. Retaining the item makes the NPC's visual choice stable,
  but also makes the injection persistent and potentially lootable.

Cold-state evaluation is anchored to the player: the player's location/height
grants a perk and NPC effects test that perk. This is reasonable for nearby
loaded actors, but there is no explicit interior condition in the cold ability;
unusual high-coordinate interiors need a runtime test.

The face-cover script declares helmet, clothing-head, circlet, and mask keyword
properties. Only helmet and clothing-head are bound in the plugin; circlet and
mask are null. KID's slot-44 blocker partly compensates, but the plugin wiring
does not match the source's stated compatibility checks.

## Dependency and configuration audit

Declared page requirements are SPID, KID, and MCM Helper, with Dynamic Armor
Variants optional. The archive also ships `ICE_FLM.ini`, but the page does not
list FormList Manipulator as a requirement and the current profile does not
have it installed.

That omission changes functionality. `ICE_FaceCoverWeathers` contains only
SkyrimStormSnow in the ESP. `ICE_FLM.ini` supplies the other blizzard and
Solstheim ash-weather entries. Without FormList Manipulator, the advertised
plural blizzard/ashstorm behavior is incomplete.

The distribution/configuration layer contains avoidable defects:

- `ICE_DISTR.ini` tries to exclude `MannequinRace`, but the actual vanilla
  EditorID is Bethesda's `ManakinRace`. The exclusion therefore cannot match,
  consistent with users finding ICE gear in mannequin inventories.
- the optional DAV file correctly uses `ManakinRace`, but duplicates its player
  exclusion and embeds one-off exclusions for Auri, Eris, Ulfric, a custom
  gilded race, and the Abandoned Shack. Those are harmless when resolved as
  intended, but read like an unpolished personal compatibility list rather than
  a documented general policy.

The rain-distribution line is commented out, yet a stale `ICE_RainCloak` source
and binary ship in the archive. This agrees with the page: rain gear is planned
for 1.1, not implemented in 1.0.

## Assets

The archive contains 168 NIFs and 93 DDS files. The usable textures are mostly
2K or smaller and do not overwrite vanilla paths. That fits the project's
resolution policy. However, the package contains considerable legacy Wet and
Cold material not referenced by this plugin, including backpack, soggy-feet,
breath, and other assets.

All eight cloak meshes use the vanilla skirt-bone chain and ship without SMP
configuration. They have canned skeletal movement, not modern FSMP cloth
physics. Other asset findings are lower severity: 70 diffuse maps have no
matching normal map, four texture sets use lower-resolution normals, one DDS is
uncompressed, and the legacy breath diffuse shows JPEG-style blocking.

## Community evidence and maturity

This is the only public release, about seven weeks old at audit time, with zero
formal bug reports and a small comment sample. One user reports excellent
performance, which is consistent with the architecture. Other comments report
or ask about mannequins and escaped prisoners receiving gear, confirm that
Seasons of Skyrim is unsupported, ask for actual Survival warmth, and await
rain support. These reports align with the static audit rather than resolving
its concerns.

## Reconsideration gate

Re-audit ICE after an author update only if it:

1. preserves all unrelated region assignments, repairs cell `0000EE52`, keeps
   the Solstheim worldspace name localized, documents/justifies the other 52
   weather-region edits, and removes the unused Survival master;
2. lists FormList Manipulator as required or moves the complete weather list
   into the plugin/configuration of declared dependencies;
3. binds all declared compatibility properties, fixes the SPID mannequin
   exclusion, and cleans up or documents the DAV conditions;
4. documents persistent inventory injection and demonstrates mannequin,
   prisoner, corpse-loot, follower, child, and cleanup behavior;
5. adds tested Starfrost/Survival warmth values or explicitly limits itself to
   visual NPC dressing; and
6. passes a foreground disposable-save test across exterior/interior weather,
   fast travel, unload/reload, death, and save/load.

Until then, retain FSMP and the separate cloak-system plan in issue #95. Do not
install Wet and Cold as a fallback merely because ICE 1.0 failed review.
