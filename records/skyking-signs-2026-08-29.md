# Skyking Signs installation record

The user explicitly selected both sign mods for Keep and installation on
2026-08-29. The archives were obtained through the authenticated Nexus API and
installed through the headless MO2 controller into the `Default` profile. No
game process was running, no GUI was opened, and no vendor file was edited.

## Exact sources

| Mod | Nexus file | Version | SHA-256 |
|---|---:|---:|---|
| Skyking Signs (112902) | 639271 | 2.1 | `32115EF5522F5B095B7C4357D5F9BD4BD101564F3E43CF2571086B67FC11609C` |
| Skyking Unique Signs (114940) | 639272 | 2.1 | `CB6BB2884498FAA44675C447F755837688003235351FA755F6547EA496E588DB` |

The byte-for-byte installed payload tree digests are
`4C40A36FE6EFB9BEA2863527EDCB1063F12DB6232846326854C984C1F9748DB9`
for Skyking Signs and
`5D36366570C3C1D947D9AE48D3C0376A6069D30D08C12468377CCA418CA99E84`
for Skyking Unique Signs. Both installed trees exactly match the selected
archive mappings with no missing, additional, or modified payload file.

Both Nexus pages prohibit redistribution and require permission to modify or
reuse their assets. A public modpack must fetch the exact external files and
replay the committed FOMOD plans; it must not bundle either vendor payload.

## Deterministic choices

- Skyking Signs: main meshes and textures, plus the supplied complex-parallax
  meshes and textures.
- Skyking Unique Signs: its current integrated BOS payload, ESL-flagged resource
  plugin, and the supplied complex-parallax meshes.
- No optional compatibility archive was installed in the original transaction.
  This intentionally excluded the Bruma, Legacy of the Dragonborn, Books of
  Skyrim, Interesting NPCs, RedBag's
  Falkreath, No Snow Under the Roof, Saints and Seducers Extended Cut,
  Winterhold Restored, Capital Windhelm Expansion, and Enhanced Solitude
  patches until their matching base mods are explicitly selected.

The user approved the Bruma compatibility file on 2026-08-30. The author's
current `Skyking Signs - Bruma Patch` (optional Nexus file `481004`, version
`1.0`) was installed as a separate immutable vendor mod and enabled in the
`Default` profile. Archive SHA-256 is
`FF49B5C37FDD58B1111088093CD2175E59356402D0B3B67DF00A69A828628AC9`;
the headless install transaction is `20260830T023339490Z-5d453c949c7a`.
`Skyking Signs - Bruma.esp` is ESL-flagged, has only `Skyrim.esm` and
`BSHeartland.esm` as masters, and contains one `MSTT` override correcting the
Snowstone Rest sign. It adds no forms and contains no scripts, quests, cells,
navmeshes, deleted records, or executable code.

The active source-built Community Shaders contains Extended Materials support;
the sign archives supply their own parallax-ready meshes, so neither PGPatcher
nor another unapproved runtime requirement is needed. Base Object Swapper 3.5.0
is already active for Unique Signs. The latest Community Shaders runtime log
also confirms that `ExtendedMaterials` loaded and validated successfully.

## Payload and compatibility audit

- Skyking Signs resolves to 106 files: 46 NIF meshes and 60 DDS textures. The
  textures are BC7 and no larger than 2048 pixels (plus one 1x1 cubemap). All
  46 meshes parse as Skyrim SE stream version 100.
- Skyking Unique Signs resolves to 31 files: 15 NIF meshes, 14 BC7 2048-square
  textures, one BOS INI, and one plugin. All 15 meshes parse as Skyrim SE
  stream version 100.
- The Unique Signs plugin has only the five official masters, is already
  ESL-flagged, contains 14 new object records in the compact FormID range, and
  has no overrides, deleted records, scripts, quests, cells, or navmeshes.
- Its BOS INI performs 14 exact reference swaps; every destination FormID is
  one of the plugin's 14 records. Spriggit 0.41.0 completed strict serialization
  and checked deserialization successfully.
- Skyking Signs intentionally wins 44 sign-mesh paths from SMIM. No other active
  managed mod collides with the selected files. Unique Signs has no current
  managed-file collisions.

MO2 audit passed with zero errors, the full installed-mod verification reported
zero problems, LOOT 0.29.6 recognized `Skykings Unique Signs.esp` as a light
plugin with no plugin-specific messages, and the selected MO2 profile remained
`Default`. LOOT's existing global Engine Fixes Part 2 warning and ENB Light's
Particle Patch warning are unrelated to these installations.

## Curator delivery

The repository records the user's Keep decision now. No live curator delta was
queued because the relay lacks a fresh, compare-and-set report for these two
mods. This avoids a delayed background write overwriting a newer decision while
the user continues reviewing the Keep list. Apply only an exact per-mod Keep
delta after re-reading current curator state.
