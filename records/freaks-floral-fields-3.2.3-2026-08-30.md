# Freak's Floral Fields 3.2.3 adoption record — 2026-08-30

## Decision

Freak's Floral Fields (FFF) 3.2.3 is the adopted Skyrim grass overhaul. Its
official Floral Solstheim 1.0.1 and Floral Veil 1.0 modules extend that choice
to Solstheim and the Soul Cairn. The installed composition favors realistic
regional identity and variety over the FOMOD's more saturated fantasy choices.
It uses the current required DrJacopo 3D Grass Library mesh package and the
existing Community Shaders and Base Object Swapper foundation.

Sources:

- [Freak's Floral Fields, Nexus 125349](https://www.nexusmods.com/skyrimspecialedition/mods/125349), main file 788926, version 3.2.3
- [DrJacopo's 3D Grass Library - Meshes, Nexus 80687](https://www.nexusmods.com/skyrimspecialedition/mods/80687), file 689307, version 16.53
- [Freak's Floral Solstheim, Nexus 138161](https://www.nexusmods.com/skyrimspecialedition/mods/138161), file 606593, version 1.0.1
- [Freak's Floral Veil, Nexus 154137](https://www.nexusmods.com/skyrimspecialedition/mods/154137), file 644292, version 1.0

## Exact install

| Package | Archive SHA-256 | MO2 transaction | Result |
|---|---|---|---|
| DrJacopo's 3D Grass Library - Meshes 16.53 | `5026606FAAE2B72CC796242DBC2E3F13D0A22133F9AFAFE6E2A9A71ECB298C68` | `20260831T031543157Z-dfbb6e446aec` | enabled, priority 37, no plugin |
| Freak's Floral Fields 3.2.3 | `D82616F1F6D25A392E86B2BA1B18F21E464A401F3909910E866E25D493EBBB9C` | `20260831T031907014Z-8713a863cda7` | enabled, priority 38, seven light plugins |
| Ensrick - Freak's Floral Fields Texture Cap | effective DDS SHA-256 `E4CC21AE1BFC1E1FEF15448362BA44244DAC72BF7439CF38BE4D74BC6BDFB3AF` | `20260831T032550872Z-ca076a6653fb` | enabled, priority 39, one-file local overlay |
| Freak's Floral Solstheim 1.0.1 | `D2CC68C96BF2257E23DE6F149B735912A3EFFFD99FA9C762081CDDD9DFB61488` | `20260831T035601955Z-fe9256c7f7cc` | enabled, one light plugin |
| Freak's Floral Veil 1.0 | `2C873BBCA96797BCF4CBE66831628DD444ACC04E65F50F9C80D765E478E8C6EE` | `20260831T035603759Z-3a6d28bf30d7` | enabled, one light plugin |

The deterministic FOMOD mapping is
[`records/fomod-plans/125349-freaks-floral-fields.json`](fomod-plans/125349-freaks-floral-fields.json).
Selections:

- 2K atlas tier;
- no Seasons support;
- dirt-cliff grass enabled;
- Realistic Tundra;
- Realistic Pine;
- Realistic Rift;
- yellow Rift leaves at the 2K tier;
- Realistic Mix Marsh;
- Mixed Reach;
- Volcanic Wasteland;
- Brown/Dead Snow Grass.

FFF's installed INI owns `iMaxGrassTypesPerTexure=15` and
`iMinGrassSize=60`; the profile INIs were not edited separately.

The two module mappings are
[`records/fomod-plans/138161-freaks-floral-solstheim.json`](fomod-plans/138161-freaks-floral-solstheim.json)
and
[`records/fomod-plans/154137-freaks-floral-veil.json`](fomod-plans/154137-freaks-floral-veil.json).
The Solstheim plan deliberately omits the archive's stray `meta.ini`. Both
modules ship `iMinGrassSize=60`, so density remains coherent across all three
worldspace layers.

## Plugin result

LOOT completed with exit code 0. Final verification reports no order violation;
the current profile may continue gaining independently approved plugins. Its
report identifies all nine Floral plugins as light masters. In the post-install
`plugins.txt` snapshot:

- `Freak's Floral Fields.esp` — line 56;
- `Freak's Floral Solstheim.esp` — line 59;
- the six selected FFF regional ESPs — lines 154–159;
- `Freak's Floral Veil.esp` — line 161.

The nine ESPFE files consume light-plugin indices, not nine full plugin slots.

## Asset and conflict audit

- FFF intentionally wins 44 mesh and 5 texture paths from its required
  DrJacopo library. This is the expected library/customization relationship.
- The local texture-cap overlay intentionally wins exactly one FFF texture.
- FFF appears in no native, Papyrus, behavior, interface, configuration, or
  other critical file conflict.
- MO2Headless final audit returned `errors: []`.
- The effective FFF texture set contains 129 DDS files, has zero texture axis
  above 4096, and has a maximum effective axis of 4096.
- Floral Solstheim contains 35 BC7 DDS files and Floral Veil contains 21; each
  has a maximum axis of 4096 and therefore needs no texture-cap overlay.
- The modules deliberately layer over shared FFF/library meshes and textures.
  Eighty-three overlapping series files are byte-identical. The remaining
  module-specific differences follow the author's required library -> FFF ->
  Solstheim/Veil order; no critical file conflict was found.
- Floral Veil introduces no shared FormKey conflict in the managed profile.
  Floral Solstheim's expected CELL/LAND chains were checked semantically: later
  patches discard no selected cell-header grass edit. The final worldspace map
  bounds belong to the existing general compatibility patch and do not replace
  grass data.

The selected 2K FOMOD tier's `textures/Landscape/grass/Twigs_Freak.dds` is a
4096x8192 BC7 atlas and breaches the project's absolute 4096-axis cap. The
separate owned overlay supplies the same archive's 1K-tier version at
2048x4096, BC7, with 13 mip levels. The vendor installation is unmodified.

The separate `Freak's Floral Fields - Dirtcliffs02 Fix` (Nexus 173097, file
724092) is not installed. Its sole mesh has SHA-256
`6BF25786028FA8C1A235A2BF86A7B410552A28141138A58C84D09B6676945479`,
byte-identical to the corresponding mesh already shipped by FFF 3.2.3. It is
therefore superseded upstream rather than an outstanding dependency.

## Deliberately deferred

The approved worldspace coverage is complete for Skyrim, Solstheim, and the
Soul Cairn. The following remain separate decisions rather than inferred parts
of that approval:

- No Grass In Objects, its FFF bounds patch, and any generated grass cache;
- Grass FPS Booster;
- Seasons support and other FOMOD fantasy variants.

Bruma and other new-land mods must not be assumed covered.

## Publication boundary and rollback

FFF, its two worldspace modules, and the DrJacopo library remain author-hosted
dependencies. Do not commit or bundle their archives, plugins, meshes, or
textures. The one-file texture overlay is also not distributable as an asset:
a public installer must fetch FFF file 788926 from its authorized source and
reproduce the lower-tier atlas extraction locally. The recipe and hash may be
distributed.

Rollback is five independent disables, in this order: Floral Veil, Floral
Solstheim, texture-cap overlay, FFF, then DrJacopo library. No vendor files were
overwritten and no physical game `Data` deployment was performed.

## Remaining acceptance test

The static installation is complete. The foreground test should cover tundra,
pine forest, Rift, marsh, Reach, volcanic tundra, snowy ground, dirt cliffs,
representative Solstheim ash/coast cells, and the Soul Cairn while recording
frame time, density, pop-in, floating grass, landscape seams, and obvious biome
mismatches. Grass cache and final DynDOLOD generation remain deferred until the
exterior stack is frozen.

## Texture-cap source (recorded 2026-09-02, #160)

The one-file overlay `Ensrick - Freak's Floral Fields Texture Cap` is the
vendor archive's own 1K-tier atlas placed at the 2K-tier path, unmodified:

- archive `Freaks Floral Fields-125349-3-2-3-1786549491.zip` (file 788926),
  SHA-256 `D82616F1F6D25A392E86B2BA1B18F21E464A401F3909910E866E25D493EBBB9C`,
  2,160,876,699 bytes;
- entry `Freak's Floral Fields/textures 1k/textures/Landscape/grass/Twigs_Freak.dds`,
  SHA-256 `E4CC21AE1BFC1E1FEF15448362BA44244DAC72BF7439CF38BE4D74BC6BDFB3AF`,
  11,184,996 bytes, copied verbatim to `textures/Landscape/grass/Twigs_Freak.dds`;
- the `textures 2k` and `textures 4k` entries for the same file are one
  identical 4096x8192 atlas (`68F811AD853162F5019E228491661574166DBB24D8367F28C9EE749308791103`,
  44,739,428 bytes), so the 1K tier is the only lower-resolution source.

The extracted entry's hash equals the installed file. The machine-readable
form is the `recipe` field on the overlay's row in `records/installed-mods.json`.
