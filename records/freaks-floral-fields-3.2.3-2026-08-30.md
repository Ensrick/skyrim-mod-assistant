# Freak's Floral Fields 3.2.3 adoption record — 2026-08-30

## Decision

Freak's Floral Fields (FFF) 3.2.3 is the adopted Skyrim grass overhaul. The
installed composition favors realistic regional identity and variety over the
FOMOD's more saturated fantasy choices. It uses the current required
DrJacopo 3D Grass Library mesh package and the existing Community Shaders and
Base Object Swapper foundation.

Sources:

- [Freak's Floral Fields, Nexus 125349](https://www.nexusmods.com/skyrimspecialedition/mods/125349), main file 788926, version 3.2.3
- [DrJacopo's 3D Grass Library - Meshes, Nexus 80687](https://www.nexusmods.com/skyrimspecialedition/mods/80687), file 689307, version 16.53

## Exact install

| Package | Archive SHA-256 | MO2 transaction | Result |
|---|---|---|---|
| DrJacopo's 3D Grass Library - Meshes 16.53 | `5026606FAAE2B72CC796242DBC2E3F13D0A22133F9AFAFE6E2A9A71ECB298C68` | `20260831T031543157Z-dfbb6e446aec` | enabled, priority 37, no plugin |
| Freak's Floral Fields 3.2.3 | `D82616F1F6D25A392E86B2BA1B18F21E464A401F3909910E866E25D493EBBB9C` | `20260831T031907014Z-8713a863cda7` | enabled, priority 38, seven light plugins |
| Ensrick - Freak's Floral Fields Texture Cap | effective DDS SHA-256 `E4CC21AE1BFC1E1FEF15448362BA44244DAC72BF7439CF38BE4D74BC6BDFB3AF` | `20260831T032550872Z-ca076a6653fb` | enabled, priority 39, one-file local overlay |

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

## Plugin result

LOOT completed with exit code 0 and retained all 209 previously active
plugins. Its report identifies every FFF plugin as a light master:

- `Freak's Floral Fields.esp` — `plugins.txt` line 54;
- `Freak's Floral Fields- Realistic Tundra.esp` — line 150;
- `Freak's Floral Fields-  Realistic Pine.esp` — line 151 (the doubled space is the upstream filename);
- `Freak's Floral Fields- Realistic Rift.esp` — line 152;
- `Freak's Floral Fields- Mixed Reach.esp` — line 153;
- `Freak's Floral Fields- Volcanic Wasteland.esp` — line 154;
- `Freak's Floral Fields- Dead Snow Grass.esp` — line 155.

The seven ESPFE files consume light-plugin indices, not seven full plugin
slots.

## Asset and conflict audit

- FFF intentionally wins 44 mesh and 5 texture paths from its required
  DrJacopo library. This is the expected library/customization relationship.
- The local texture-cap overlay intentionally wins exactly one FFF texture.
- FFF appears in no native, Papyrus, behavior, interface, configuration, or
  other critical file conflict.
- MO2Headless final audit returned `errors: []`.
- The effective FFF texture set contains 129 DDS files, has zero texture axis
  above 4096, and has a maximum effective axis of 4096.

The selected 2K FOMOD tier's `textures/Landscape/grass/Twigs_Freak.dds` is a
4096x8192 BC7 atlas and breaches the project's absolute 4096-axis cap. The
separate owned overlay supplies the same archive's 1K-tier version at
2048x4096, BC7, with 13 mip levels. The vendor installation is unmodified.

The separate `Freak's Floral Fields - Dirtcliffs02 Fix` (Nexus 173097, file
724092) is not installed. Its sole mesh has SHA-256
`6BF25786028FA8C1A235A2BF86A7B410552A28141138A58C84D09B6676945479`,
byte-identical to the corresponding mesh already shipped by FFF 3.2.3. It is
therefore superseded upstream rather than an outstanding dependency.

## Deliberately not installed

No optional mod was inferred from the grass approval. In particular, the
following remain decisions rather than adopted content:

- Landscape Fixes for Grass Mods;
- No Grass In Objects, its FFF bounds patch, and any generated grass cache;
- Grass FPS Booster;
- FFF's separate Solstheim module;
- Seasons support and other FOMOD fantasy variants.

FFF covers Skyrim. Solstheim coverage is a separate future decision, and Bruma
must not be assumed covered.

## Publication boundary and rollback

FFF and the DrJacopo library remain author-hosted dependencies. Do not commit
or bundle their archives, plugins, meshes, or textures. The one-file texture
overlay is also not distributable as an asset: a public installer must fetch
FFF file 788926 from its authorized source and reproduce the lower-tier atlas
extraction locally. The recipe and hash may be distributed.

Rollback is three independent disables, in this order: texture-cap overlay,
FFF, then DrJacopo library. No vendor files were overwritten and no physical
game `Data` deployment was performed.

## Remaining acceptance test

The static installation is complete. The foreground test should cover tundra,
pine forest, Rift, marsh, Reach, volcanic tundra, snowy ground, and dirt
cliffs while recording frame time, density, pop-in, floating grass, landscape
seams, and obvious biome mismatches. Grass cache and final DynDOLOD generation
remain deferred until the exterior stack is frozen.
