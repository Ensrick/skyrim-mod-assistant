# Baltimore Weapons 29612 installation and intake audit

Captured 2026-08-30 for the active `Default` MO2 profile. The user explicitly
approved Baltimore Weapons and marked it Keep. The vendor mod is installed and
enabled; integration and balance decisions are tracked on [GitHub issue
#66](https://github.com/Ensrick/skyrim-mod-assistant/issues/66).

## Source and transaction

| field | value |
|---|---|
| Nexus source | Skyrim Special Edition mod `29612`, **Baltimore Weapons**, Billyro |
| selected file | MAIN `109963`, version `1`, `Baltimore Weapons-29612-1-1570791119.7z` |
| file upload | 2019-10-11; the page and file inventory expose no newer official file |
| archive bytes / SHA-256 | 29,561,497 / `94C0CE2974B4B0E184BF9B3CDBD3617D2F948653DBBBD4AB76D2149FEE62510E` |
| MO2 folder | `Baltimore Weapons` |
| transaction | `20260830T144449367Z-bb2554c1b0d4` |
| installed UTC | `2026-08-30T14:44:51Z` |
| plugin | `Baltimore Weapons.esp`, SHA-256 `D88DFEA34204F8A59EF13E070B74C8C3B308CC432387E5C64A50AA0D001124B5` |
| payload | 24 vendor files, 94,605,265 bytes: one ESP, eight NIF, fifteen DDS |

Installation used `audit/install_mod.py` and the source-built headless MO2
controller. The archive remains in the ignored MO2 download cache, the vendor
payload is isolated in its own MO2 mod, and nothing was copied to the game
directory. `records/installed-mods.json` contains the exact transaction and
hash. The live curator reads `29612` as **Keep**.

## Exact plugin inventory

`Baltimore Weapons.esp` is a full, unflagged ESP with `Skyrim.esm` as its only
master. It contains 32 new records and no overrides:

| signature | count | purpose |
|---|---:|---|
| WEAP | 6 | two falchions, two daggers, two axes |
| ARMO / ARMA | 2 / 2 | two bucklers and their race armatures |
| STAT | 6 | first-person weapon models |
| COBJ | 16 | one forge recipe and one temper recipe per item |

There are no leveled lists, containers, placed references, NPCs, outfits,
quests, scripts, DLLs, cells, worldspaces, landscapes, or navmeshes. Therefore
all eight items are **deliberately craft-only as shipped**; none can appear in
world loot, merchant stock, or NPC equipment through this plugin.

The plugin is not ESL flagged. Four new local IDs are at or below `0xFFF`, but
28 are above it. It is technically compactable because it has only 32 new
records and no compacting-unsafe record types. Compacting the installed vendor
plugin is still prohibited: it would mutate vendor bytes and renumber FormIDs.
Slot pressure does not justify that migration today.

## Item records and initial roles

All weapons carry `WeaponMaterialSteel`, the correct weapon-type keyword, and
`VendorItemWeapon`. Both shields carry `ArmorMaterialSteel`, `ArmorShield`, and
`VendorItemArmor`; both are Heavy Armor on slot 39. Material, animation,
equipment-type, impact, sound, first-person model, and vendor semantics are
coherent.

Each pair shares one display name despite having different records and stats:
both falchions are “Baltimore Falchion,” both axes are “Baltimore Battleaxe,”
both daggers are “Baltimore Dagger,” and both shields are “Baltimore Buckler.”
The integration decision should give variants distinct player-facing names or
intentionally retain that ambiguity.

| item | FormKey | damage / armor | speed | reach | stagger | weight | value | critical | as shipped | initial modpack recommendation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1H falchion | `000D62:Baltimore Weapons.esp` | 13 | 1.0 | 1.0 | 0.75 | 10 | 250 | 4 | craft-only | generic, restricted professional/mercenary/privateer/veteran pool |
| 2H falchion | `000D66:Baltimore Weapons.esp` | 22 | 0.7 | 1.3 | 1.10 | 15 | 275 | 8 | craft-only | same generic family, with a higher level gate |
| long dagger | `001DA8:Baltimore Weapons.esp` | 10 | 1.2 | 0.8 | 0 | 3 | 275 | 2 | craft-only | generic, restricted rogue/mercenary/veteran pool |
| short dagger | `001DA9:Baltimore Weapons.esp` | 9 | 1.3 | 0.7 | 0 | 2 | 250 | 2 | craft-only | generic, separately tiered below the long dagger |
| 2H Dane axe | `001DAA:Baltimore Weapons.esp` | 23 | 0.7 | 1.3 | 1.15 | 15 | 275 | 8 | craft-only | generic Nordic raider/veteran/chief or custom-enemy pool |
| 1H Dane axe | `001DAB:Baltimore Weapons.esp` | 15 | 0.9 | 1.0 | 0.85 | 10 | 250 | 4 | craft-only | same cultural/role family, with a lower level gate |
| large buckler | `001DAC:Baltimore Weapons.esp` | 32 armor | n/a | n/a | n/a | 5 | 275 | n/a | craft-only | generic restricted shield pool; heavy/light identity unresolved |
| small buckler | `001DAD:Baltimore Weapons.esp` | 30 armor | n/a | n/a | n/a | 4 | 250 | n/a | craft-only | generic restricted shield pool, below the large variant |

Nothing in the names, art, or records establishes artifact, quest, Falmer,
Draugr, skeleton, or other creature ownership. The best initial fit is generic
but **selectively** distributed, with optional use by future custom enemy
templates. That is a recommendation only. The user's item-role decision remains
open for every row.

## Crafting and tempering

All forge recipes use `CraftingSmithingForge` and require Steel Smithing:

| items | recipe |
|---|---|
| 1H / 2H falchion | 5 steel ingots + 2 leather each |
| 1H axe | 3 steel ingots + 2 firewood |
| 2H axe | 4 steel ingots + 3 firewood |
| long / short dagger | 3 / 2 steel ingots + 1 firewood |
| each buckler | 5 steel ingots + 1 leather |

Every temper recipe consumes one steel ingot. Weapons use a grindstone;
bucklers use an armor workbench. The standard condition allows non-enchanted
items or enchanted items with Arcane Blacksmith. The steel material keyword
makes Steel Smithing the improvement-perk family.

## Balance comparison

Billyro's description says the stats equal Ebony. Base damage and shield armor
mostly do, but the overall package does not:

| vanilla baseline | damage / armor | weight | value | Baltimore comparison |
|---|---:|---:|---:|---|
| Ebony sword | 13 | 15 | 720 | 1H falchion matches damage at weight 10/value 250 |
| Ebony war axe | 15 | 17 | 865 | 1H axe matches damage at weight 10/value 250 |
| Ebony dagger | 10 | 5 | 290 | long dagger matches damage at weight 3; short is damage 9, weight 2 |
| Ebony greatsword | 22 | 22 | 1,440 | 2H falchion matches damage at weight 15/value 275 |
| Ebony battleaxe | 23 | 26 | 1,585 | 2H axe matches damage at weight 15/value 275 |
| Ebony shield | 32 | 14 | 750 | large buckler matches armor at weight 5/value 275; small has armor 30/weight 4 |

The player can therefore craft near-Ebony offensive/defensive power from cheap
steel immediately after Steel Smithing, while receiving exceptional carry
weight efficiency. Lower critical damage does not compensate for that early
base-power access. The owned patch must choose an honest steel-plus, mid-tier,
or rare high-tier baseline, then normalize damage/armor, critical damage,
weight, value, recipes, perk gates, rarity, and distribution together.

## Asset audit

All eight meshes are valid Skyrim SE stream-100 NIFs. They use unique paths,
are static rather than body/skeleton assets, and total 19,325 triangles. Meshes
range from 1,224 triangles per dagger variant to 3,508 for the 2H falchion.
They contain no Oldrim blocks, parallax flags, custom bones, or PBR material
references.

Each equipment family has diffuse, normal, and specular maps; the three extra
512-square files are cubemaps. All textures have complete mip chains. The
automated “missing normals” warning is a known false positive here because the
auditor pairs `name.dds` with `name_n.dds` while this pack uses the standard
`name_d.dds` / `name_n.dds` convention.

Real concerns remain:

- battleaxe and falchion diffuse maps are `8192x2048`, exceeding the project’s
  absolute 4K-per-axis texture ceiling;
- four normal maps are uncompressed, using about 53 MiB more VRAM than a
  suitable block-compressed representation;
- automated sampling identified unusually soft/upscaled detail and JPEG-source
  blocking in several maps; this needs visual A/B validation before any public
  optimization claim.

Any downscale/recompression must be a separate credited derivative overlay.
The vendor files remain untouched.

## Permissions and publication boundary

The Nexus description states, “Feel free to use, just give due credits.” The
project nevertheless uses the conservative default: the original archive is
an external Nexus dependency and is not bundled. An Ensrick-owned patch may
distribute original override records/configuration that reference the vendor
FormKeys. Recompressed textures or altered meshes are derivative assets and
require a release-time permission and credit review before publication.

## Verification

- headless MO2 transactional install and enable: **pass**;
- live `Default` mod and plugin state: **pass** (`+Baltimore Weapons`,
  `*Baltimore Weapons.esp`);
- ledger verification after LOOT and managed-plugin re-enable: **0 problems**;
- load/master order after the subsequent CRF installation: **117 active, 203
  discoverable, clean**;
- active record-conflict audit: **no Baltimore override chain**;
- active asset-path conflict audit: **no Baltimore collision**;
- strict Spriggit serialize/check/deserialize: **pass**;
- deleted records, unresolved masters, scripts, DLLs, or unsafe world edits:
  **none**;
- game launch/runtime test: **not run by design**.

LOOT emitted no Baltimore-specific message. Its one global warning about the
SSE Engine Fixes preloader predates and is unrelated to this mod.
