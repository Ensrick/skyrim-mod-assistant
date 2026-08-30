# Landscape and tree stack decision — updated 2026-08-30

Status: **installed and enabled in MO2 `Default`**.

## Decided foundation

- **Landscape and architecture:** [Skyland AIO](https://www.nexusmods.com/skyrimspecialedition/mods/34179) 1K 4.32, file `443516`, is the broad vanilla/DLC base. It is installed after SMIM with Skyland's SMIM compatibility selected.
- **Trees and placements:** full [Nature of the Wild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/63604) 3.14, file `661793`, using its normal dense placements and ordinary main textures.
- **Controlled diversity:** [Traverse the Ulvenwald](https://www.nexusmods.com/skyrimspecialedition/mods/57874) 3.3.2 supplies assets only, while [Tree Diversity Project](https://www.nexusmods.com/skyrimspecialedition/mods/155974) 1.0.1 performs its official `NOTWL base + Ulvenwald swap` BOS configuration. `Ulvenwald.esp` is deliberately disabled.
- **Not selected:** Nordic Cut is rejected from this stack and is not installed. Nature of Mild Lands is not installed or authorized. Vanaheimr, Skyland complex parallax, Skyland LODs, Skyland Bits and Bobs, tree animation, tree PBR, Seasons, autumn textures, and grass remain outside this installation.

This replaces the former provisional Vanaheimr + Mild Lands + Nordic Cut proposal. Nordic Cut must not be used as a dependency, patch master, or placement winner for the selected full-NotWL stack.

## Exact installed inputs

| Component | Nexus file | SHA-256 | Installed role |
|---|---:|---|---|
| Skyland AIO 1K 4.32 | `443516` | `490F02EC34487FA9CFFD76E9CCFB69A2C17AD5207A2416CC6B1AAD027D15D734` | Broad architecture/landscape base; no plugin. |
| Nature of the Wild Lands 3.14 | `661793` | `86B83A9A3B26D5A54DBB3EA40C4E638B18E7BE4BA47F880FEA6779ECB011054A` | Full main plugin, meshes/textures, shipped DynDOLOD rules/hybrid meshes, and ENB Light nirnroot mesh. |
| NotWL official patch collection 3.10 | `613478` | `F9D60425DDF14C73D353E6B47BC676573DF4088C4F6AA2D28D04FA159B157880` | Only Bruma, CC Tundra Homestead, Cutting Room Floor, and Lux Via patches whose exact masters are active. |
| Grand Solitude Patch Collection 1.5 | `797296` | `FE58C5ACA1025688AE74BA54DF312135EE8715792AC3FD49B6A3FEBFC0E64233` | Adds the normal full-NotWL Grand Solitude patch, not a Nordic-specific patch. |
| NotWL – Solitude Docks Patch 1 | `433438` | `6BFB0D45E3481D100F5BEBFB2C02C75B6D322F2FC9266BC59E08F7D48CE85A29` | Current full placement cleanup; its 19 NotWL target FormIDs still exist in 3.14. |
| Traverse the Ulvenwald 3.3.2 | `444742` | `6FD168C2F063A3C8DD4D3D5B8D1BC5D596B76721F3364542ACA80056DB0A7379` | Lowest-priority asset dependency; autumn/no-Seasons aspen selection. Its full placement plugin is installed but deliberately disabled. |
| Tree Diversity Project 1.0.1 | `680001` | `606224ADE3AEE68444C681453712635DC45C4E66456D06E35EC7509F38185FCD` | ESL-flagged record library plus the NotWL-base/Ulvenwald-swap BOS INI; no vanilla dummy and no Seasons files. |

## Skyland FOMOD boundary

The deterministic plan is `records/fomod-plans/34179-skyland-aio-1k-4.32.json`. It selects the full landscape and vanilla/DLC architecture, Blended Roads compatibility, the SMIM patch, grey vanilla mountains, grey farmhouses/towns, and the normal city/dungeon/ship/shack/tent/window coverage. It omits Skyland water colouring, road signs and lit-sign options, dirt roads, night sky, lanterns, addons, and pre-generated LOD.

Consequently Water for ENB remains the only provider of `textures/water/defaultwater.dds` and `textures/water/riverflow.dds`; Skyking Signs/Unique Signs remain later dedicated sign winners. Skyland wins its intended 74 DDS and 15 NIF overlaps with SMIM, while Lux/Lux Orbis and the existing targeted fix layer win their narrow lighting/mesh paths.

## NotWL FOMOD and compatibility boundary

The deterministic main and patch plans are:

- `records/fomod-plans/63604-nature-of-the-wild-lands-3.14.json`
- `records/fomod-plans/63604-nature-of-the-wild-lands-active-patches-3.10.json`
- `records/fomod-plans/157450-grand-solitude-patches.json`

The full main uses the ordinary roughly 2K-bark/1K-leaf texture defaults. It does not select autumn, Seasons, animation, PBR, Nordic Cut, or Mild Lands. No separate Snazzy patch is applicable because the active Snazzy Solitude set is interiors/separated houses; no Water for ENB tree-placement plugin is required. Bruma is handled by the exact official patch. Beyond Reach and Wyrmstooth are separate worldspaces and have no current full-NotWL placement patch requirement in this profile.

LOOT places `Nature of the Wild Lands.esp` early, ahead of Lux Orbis, Lux, Water for ENB, and the owned compatibility outputs. This preserves the tree additions while allowing the specialized CELL/WRLD water and lighting semantics to win. Official placement patches then win the intended Bruma, Tundra Homestead, CRF, Lux Via, Grand Solitude, and Solitude Docks records. The post-sort audit found no missing masters or parser failures, so no new owned ESP-FE was warranted.

## Ulvenwald diversity boundary

The deterministic plans are:

- `records/fomod-plans/57874-ulvenwald-3.3.2-assets.json`
- `records/fomod-plans/155974-tree-diversity-project-notwl-ulvenwald.json`

Ulvenwald is deliberately the lowest-priority managed asset source. This is
stricter than merely placing it below NotWL: its two shared SMIM meshes now lose
to SMIM, so the disabled placement mod cannot create unrelated furniture or
driftwood replacements. The 12 selected Ulvenwald tree models still resolve
from unique paths; the thirteenth selected model is NotWL's willow. Their 39
referenced DDS paths resolve with zero missing files (33 Ulvenwald, 6 NotWL).

Tree Diversity Project's plugin is already ESL-flagged. It contains 515 new
`STAT`/`TREE` records, zero overrides, zero placed references, zero cells,
worldspaces, navmeshes, scripts, or quests. The selected INI has 14 active swaps
to 13 unique targets. This means it changes the model chosen for existing NotWL
objects at runtime without adding a second placement ecosystem. Only the NotWL
patch family remains applicable.

## Texture-policy overlay

The 413-texture NotWL main has one policy violation: `textures/true forest/log/log01.dds` is 8192×8192 BC7 with 14 mips. The immutable vendor payload remains untouched. A separate local overlay, `Ensrick - Nature of the Wild Lands Texture Cap`, deterministically converts only that map to 4096×4096 BC7 with 13 mips:

`texconv -w 4096 -h 4096 -f BC7_UNORM -m 0 -y -nologo`

Two clean builds were byte-identical at SHA-256 `C86C89277B4DFADB7FF62451CB0B953007D956208B8BDEE2295154D44D118D2E`. The overlay is local-only and may not be redistributed with vendor assets.

## Remaining validation

Static installation is complete. Runtime acceptance remains deliberately separate because this task did not launch the game: measure frame-time/VRAM and inspect tree clipping, wind behavior, shadows, LOD transitions, routes, and the Grand Solitude/Docks/Bruma/Tundra/CRF/Lux Via areas on the next disposable visual-validation pass. Generate final TexGen/DynDOLOD only after the grass choice and all worldspace placements are frozen.

Foundation evidence is in `records/skyland-notwl-foundation-install-2026-08-30.md`; the diversity-layer transaction and validation evidence is in `records/notwl-ulvenwald-tree-diversity-2026-08-30.md`.
