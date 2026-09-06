# Inigo buries the Bloodchill Cavern entrance: cause and our own fix (2026-09-06)

Replaces Elianora's `Inigo - Bloodchill Manor Patch` ([58317](https://www.nexusmods.com/skyrimspecialedition/mods/58317))
after the user's standing exclusion of that author (`docs/EXCLUDED_AUTHORS.md`).
The user's ask: *"We need a different patch or to make our own. I don't trust or
use anything from Elianora."* There is no third-party alternative - the only
other mod in this space, [138140](https://www.nexusmods.com/skyrimspecialedition/mods/138140)
(justasucc, navmesh), lists 58317 as "Absolutely required" - so we built ours.

## Root cause, which neither Nexus page states

`Inigo.esp` declares **only `Skyrim.esm` and `Update.esm` as masters**
(`skyrim-record-cli plugin-info`). The Creation Kit therefore wrote its
`LAND 00009FC4` and `NAVM 001062F7` from the *Skyrim.esm* versions of those
records, silently discarding `Dawnguard.esm`'s. Dawnguard is what digs the
ravine that the Creation Club entrance sits in, so Inigo's copies fill it back
in - and, loading later, win.

Measured, not assumed (cell 008FC4 `LangleyPath3`, grid 15,16):

| Record | Skyrim.esm | Dawnguard.esm | Inigo.esp |
|---|---|---|---|
| `LAND 009FC4` VHGT at the door | 2500-2850 | 1768-2100 | **identical to Skyrim.esm, 0/1089 vertices differ** |
| `LAND 009FC4` VNML / VCLR | - | own | byte-identical to Skyrim.esm |
| Texture layers | top-left base `06A1AF` | top-left base `00089B`, extra layer `01B082` | the **vanilla** arrangement |
| `NAVM 1062F7` | 253 verts / 313 tris | 277 / 346 | 257 / 321 |
| Navmesh within 200u of `RockCaveEntrance02` | 4 verts, z 2356-2691 | 7 verts, z 1863-1924 | 4 verts, z 2356-2691 |

The entrance blocker `CCEEJSSE005_EntranceBlocker` (`0153C3:Dawnguard.esm`,
base `MountainTrimSlab_LightSN`) sits at z 1998.2; the cave-entrance static
`RockCaveEntrance02_HeavySN` at (63012, 66893, 1985). Under Inigo the ground
over both is ~2500-2850 and the navmesh is the hillside, which is why followers
could not path in even after Elianora's terrain fix - the gap 138140 exists to
fill. `ccEEJSSE005-Cave.esm` itself contains **zero LAND records** (2,756
records, none `Landscape`), so the CC never sculpted anything: it was built
against Dawnguard's ground.

What Elianora's 9-record patch did instead: hand-sculpted a fresh bowl down to
z 1624 (171 vertices changed vs vanilla, 247 vs Dawnguard), blended two
neighbouring cells (`009FC5`, `009FE3` - which nobody else overrides), moved
`RockPileS04Snow01Heavy_SN` 15 units, re-pointed two `XLRL` location references
from the CC's location to Inigo's, and left the navmesh alone. It also does not
restore Dawnguard's `01B082` texture layer.

## What we ship

`Ensrick Inigo Bloodchill Landscape Forward.esp` - ESL-flagged, 20,300 bytes,
4 records, 0 new forms, masters `Skyrim.esm, Update.esm, Dawnguard.esm,
Inigo.esp`. Source and rationale: `mods/inigo-bloodchill-landscape/build.py`.

| Record | Copied from | Edit |
|---|---|---|
| `WRLD 0000003C` Tamriel | `Ensrick General Compatibility Patch.esp` | none - byte copy of the current WRLD winner |
| `CELL 00008FC4` | `Inigo.esp` | `XLCN` master index 02 -> 03 only |
| `LAND 00009FC4` | `Dawnguard.esm` | none |
| `NAVM 001062F7` | `Dawnguard.esm` | none |

Because Skyrim replaces records whole rather than merging fields, the
structural `WRLD` parent a cell patch must carry would beat the real WRLD
Tamriel winner if this plugin ever sorted last - and it *does* sort last
(plugins.txt 275 of 275). Copying that winner's record verbatim makes the
parent a no-op at any position; its subrecords resolve to `Skyrim.esm` forms
only, so no extra master is pulled in. Re-run `build.py` if the General
Compatibility Patch (#47) is regenerated with different WRLD data.

Nothing here is authored: every record is a byte copy of a record already on
disk, and none of it is Elianora's.

**Trade-off, deliberate:** Dawnguard's navmesh does not contain the 4 vertices
/ 8 triangles Inigo's CK cut around three stone-wall statics
(`StonewallLong01Snow`, `StonewallEndL01Snow`, `StockadeWoodbeam03Light_SN`) at
(65200, 68400), ~3,000 units from the entrance. NPCs may clip that wall corner.
Weighed against a Creation Club home whose door no follower can reach.

## Verification

- Two builds byte-identical: sha256 `287c43a7f3e5eaa58f341a633fe468bc521a68aa06d47b286d236e2953f4e7ca`.
- `LAND` and `NAVM` compared subrecord-by-subrecord against `Dawnguard.esm`: identical.
- Heights decoded and diffed: 0 of 1089 vertices differ from Dawnguard.
- Navmesh decoded: 277 verts / 346 tris, same as Dawnguard, 7 verts at z 1863-1924 by the door.
- Mutagen (`skyrim-record-cli plugin-info`): 4 records, masters as declared, `CELL` Location resolves to `07FF4F:Inigo.esp`.
- Spriggit 0.41.0 `serialize --Check --ErrorOnUnknown`: exit 0 (checked text round-trip).
- Full active load order re-scanned: only this plugin overrides `LAND 009FC4` / `NAVM 1062F7`; USSEP and Inigo touch `CELL 008FC4` earlier.
- `install_mod.py --verify`: `0 problem(s)`.
- **In game: NOT verified.** No launch has been run since the swap.

## Instance changes

| Step | Transaction |
|---|---|
| `mod-stage` at priority 166, enabled | `20260906T195302045Z-bdd12762aebb` |
| `plugin-enable` | `20260906T195305626Z-16b9d4e22ea8` |
| `plugin-disable Eli_InigoBloodchillPatch.esp` | `20260906T195316743Z-a5d718e9e5e0` |
| `mod-disable Inigo - Bloodchill Manor Patch` | `20260906T195316820Z-f85e7e76b2c4` |
| `mod-trash` (recoverable) | `20260906T195320022Z-44a3cd70f0f4` |

The stale `Eli_InigoBloodchillPatch.esp` row was then removed from
`plugins.txt` and `loadorder.txt` with Python (CRLF preserved); both files were
backed up as `.bak.v20260906T195353Z-pre-eli-removal`. Work claim
`claude/inigo-bloodchill` held throughout; no MO2 GUI or game process was
running.

## Open

- In-game check: enter Bloodchill Cavern with a follower and confirm the door is
  clear and the follower walks in rather than teleporting.
- The wall corner at (65200, 68400) during Inigo's quest, for clipping.
