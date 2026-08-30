# Orc Strongholds AIO 1.2.1 exact plugin and patch audit

Status: **research complete; hold for a user decision and controlled validation.**
This is a read-only 2026-08-29 audit of Nexus SSE `150246`, its current public
repair/compatibility files, and only the combinations relevant to the active or
planned modlist. Nothing was installed or enabled in `Default`; no Keep/Skip,
curator, game, UI, vendor, or load-order state was changed.

**Superseding tree decision, 2026-08-30:** full Nature of the Wild Lands 3.14
is the selected tree stack; Nordic Cut is not installed and must not be used as
the Orc compatibility master. Any future Orc Strongholds adoption must
re-audit the normal full-NotWL patch branch.

## Executive result

`Orc Strongholds - All In One.esp` v1.2.1 is structurally loadable as a Skyrim
1.71 ESP-FE today, but it is not a low-risk light plugin. It contains 4,099
records, 151 navmeshes, 3,035 new records, and 2,776 new temporary placed
references. Its new FormIDs already reach the light-plugin ceiling `0xFFF`.
All current IDs are legal, but future sequential additions cannot remain light
without deliberately filling gaps or splitting the project.

The plugin's local NAVI map, NAVM door-triangle indices, and door-reference
resolution pass static structural checks. That does **not** prove that an NPC
can traverse the rebuilt Largashbur layout. Multiple users reported Atub
wandering away during The Cursed Tribe in May-July 2026. The main plugin does
not directly override Atub or DA06, while it substantially replaces the
stronghold's exterior navmesh. No current public patch repairs or even changes
the retained Largashbur NAVM payloads. If the route failure reproduces, the
responsible repair is Creation Kit navmesh visualization, topology repair, and
finalization followed by a fresh quest route—not a speculative Atub package
override in xEdit.

The most comprehensive current public fix, Alaxouche's 1.4.2 **Fixes and
Optimization**, is a same-name replacement for the main ESP, not an overlay.
It removes extraneous records, incorporates the later standalone Dushnikh Yal
land fix, adjusts terrain and misplaced references, and supplies corrected or
optimized meshes. It is technically preferable to the untouched main for a
trial, but it crosses this project's preferred immutable-vendor/owned-overlay
boundary: the cleanup cannot be recreated completely in a later ESL, and the
author does not grant modification or redistribution permission. It would
have to remain a separately fetched Nexus dependency unless the curator
explicitly accepts a private local transformation.

Current USSEP, Lux Orbis, and Nordic Cut compatibility is ordinary headless
patch work. Lux Via is the exception: the older official patch carries four
Largashbur LAND winners that conflict with four newer terrain winners in the
1.4.2 replacement. It must not simply win after that replacement; an owned
LAND reconciliation and visual seam route are needed. None of these patches
resolves the reported Atub route.

## Decision packet

No Keep/Skip recommendation is made. Before any trial, the user needs to decide
whether the modlist may depend on Alaxouche's separately downloaded same-name
replacement main. If yes, the technically coherent starting candidate is:

1. original v1.2.1 assets plus Alaxouche's 1.4.2 replacement ESP/mesh payload;
2. the current collection's USSEP and Lux Orbis patches;
3. Nordic Cut 1.2.2's bundled Orc Strongholds patch if that planned tree
   architecture is selected;
4. no standalone ZX Fixes, because its four LAND records are already present
   in the replacement main;
5. no blind use of the old Lux Via patch until its LAND data is reconciled;
6. no Cursed Tribe Quest Expansion patch unless that separate quest mod is
   actually selected.

That is a candidate for a disposable validation profile, not authority to
install it into `Default`.

## Audit basis and provenance

Current Nexus metadata was queried through the authenticated API. Archives were
downloaded to the durable MO2 download cache and extracted only to an ignored
temporary audit directory. Plugins were parsed directly and the two main-plugin
variants were serialized with the source-built Spriggit CLI. Hashes below are
the exact audited artifacts.

| Nexus component | Current audited file | Archive SHA-256 | Plugin SHA-256 |
|---|---|---|---|
| Orc Strongholds AIO | 1.2.1, file `636197` | `0823B5D95476EF49C0F362F57360CCFEE82E862CEA8E6E21454B89D21582D0D4` | `7BAEE63C4CC2AD39AE5B1B56A7D836CCAA7E22C5066D5D76640DBB1B4AEFC004` |
| Patch Collection | 1.4.2, file `785364` | `08CD6EF7FBDE9490A5DAE8DE0DE58DE21EE98901E96E62CBF8637191117736B6` | replacement main: `FCE65B8D913883E65F51C111534ED8415A236FBD8926B20C1CC4C4807EA87990` |
| Fixes and Optimization | 1.4.2, file `785365` | `894FF740BAF7BB8A0101D50CBD522D2D41982D558DC323401EE8FF7AA9DB373A` | same replacement main as above |
| Author NotWL optional | 1.1, file `627972` | `3ED92B9AADDBC482976CA836317C0398545B4F0ED51748D8CB29534BF9AED611` | `AF09F28D2AEA8EF639DABF8F02A402EB855EC3EF8811323DEAEB840C7CFD00F3` |
| Author Lux Via optional | 1.1, file `627975` | `3D9A34B4662AFAB13DE33B5741D0CC5DDBEDC853ADBABC3E90AD326C604D688E` | `7774D0B8D1D81041E72FC581B2B5081DF8D6534DFDFC8058054FA7D8F932ACC1` |
| Author Lux Orbis optional | 1.2, file `636167` | `5CF8B4A74AA59800BFFB72D02940A551760FE4E327A287BF8C4CA81CA66FA71C` | `473EEE34016ADBA1F992156C64F9393E6D835EF53BF7065EB0456E248FCCDE98` |
| ZX Fixes | 1.0, file `792041` | `51F545DA963A940F67D52F176B36E731BBECF38B09653D50B5A2AC3671922FEC` | `C6F32D34846777CB60DD7EC77F2DFA32994A0CF4DB2F12871507BB62B7210FD6` |
| TCTQE standalone patch | 1.0, file `717600` | `73AF0C4D100E03E3B4BEE65A1E1D4D0DAA52F4C9DA14FE4132D0E962FF69FA01` | `E88BD8AB54BE14A9BA477B26E1D6BC25A284F946477E78DDE9D25F538EDFEFC2` |

The current `Default` profile has USSEP 4.3.9, Lux, Lux Orbis, and Lux Via.
Neither Orc Strongholds nor The Cursed Tribe Quest Expansion is installed.
Nature of the Wild Lands 3.14 plus Nordic Cut 1.2.2 is a leading but still
deferred tree-stack candidate, so both the normal and Nordic-specific tree
patches were inspected without treating either as selected. The runtime is
1.7.104, which supports the 1.71 extended light-plugin range and does not need
BEES for these files.

## Main plugin anatomy

The v1.2.1 plugin is header version 1.71, flagged Small/ESL but not ESM, and has
only the five official game masters. Its exact record inventory is:

| Signature | Count | Material detail |
|---|---:|---|
| REFR | 3,695 | 2,819 new local, 807 Skyrim overrides, 69 Update overrides |
| NAVM | 151 | 59 new local, 92 Skyrim overrides |
| STAT | 56 | all new local |
| CELL | 54 | all overrides |
| ACHR | 40 | 29 new local |
| NPC_ | 32 | all new local |
| LAND | 29 | overrides |
| PACK | 19 | all new local |
| TXST | 5 | all new local |
| CONT / DOOR / ACTI | 4 each | all new local |
| TREE | 2 | new local |
| WRLD / FACT / MISC / NAVI | 1 each | mixed override/new as appropriate |

There are 3,035 new records total. The local FormID range is `0x001` through
`0xFFF`, with 1,061 gaps. The current records therefore fit the v1.71 light
range exactly, but the plugin has consumed the highest legal local ID. The
header's `NextObjectID` is stale and outside that range (`0x1F1E7`; the fixed
replacement says `0x2E4E7`). Runtime validity follows the actual record IDs,
not this authoring hint, but the stale value is a maintenance trap. Records
must never be compacted or reassigned after a save.

### Reference-handle pressure

The new placed-reference population is:

- 2,819 REFR: 72 persistent and 2,747 temporary;
- 29 ACHR: all temporary;
- 2,776 new temporary placed references in total.

Because the plugin is ESP-FE, not ESM, its temporary placed references are
loaded under ordinary non-master behavior rather than the on-demand behavior
used by master files. Skyrim has a finite reference-handle pool. There is no
responsible universal per-plugin failure threshold, so this count is cumulative
load-order pressure—not proof that this mod alone will exhaust handles.

Changing the main to ESM+ESL is mechanically possible headlessly and this main
does not add new CELL or WRLD records, but it is not an overlay repair. It
changes the main file's load-order class and must be delivered upstream or as
an explicitly approved private vendor transformation with full regression.
It is classified below as **vendor-bound headless work**, not as an owned ESL.

## The 1.4.2 replacement main

Both 1.4.2 archives contain the same replacement `Orc Strongholds - All In
One.esp`; the FOMOD copies it over that destination name. It is not a patch that
can simply load after the untouched vendor plugin. Its record inventory falls
from 4,099 to 4,063 by removing exactly 36 records:

- 23 vanilla NAVM overrides;
- 12 CELL overrides, several in unrelated locations such as Icerunner,
  Ivarstead, Bleakwind Basin, Darkfall Cave, Arkngthamz, and Reachcliff;
- one disabled local placed reference `000852` in an unrelated cell.

It adds no records. It also regenerates NAVI for the removed navmeshes, changes
terrain height data, moves initially disabled vanilla objects to a safe hidden
Z position, corrects floating objects and torches, adds object bounds to one
new Largashbur archer, and includes replacement fixed/optimized meshes. Its four
Dushnikh Yal LAND payloads are exactly identical to the later ZX Fixes plugin.

The repair is broader than its short description, but it still does not fix
the reported route in a demonstrable way: every one of the 128 NAVM records
retained in the replacement has the exact same CRC payload as v1.2.1. The fix
only removes 23 other NAVM overrides. All retained Largashbur navmesh topology
is unchanged.

Removing records from their originating plugin cannot be faithfully represented
by a later owned ESL. A late patch may forward ordinary winning fields, but it
cannot make the originating main cease defining those NAVM/CELL/local records.
This is why the cleanup is vendor-bound even though the technical edit itself
can be done headlessly. The patch-collection author requires permission for
modification and does not grant asset redistribution; a public modlist may
fetch this file as a Nexus dependency but must not bundle or fork its payload.

## NAVM, NAVI, and doors

The main contains 150 compressed navmeshes plus one deleted vanilla navmesh
override. Its sole NAVI override has version 12 and 170 MapInfo entries: 111
vanilla entries and one for each of the 59 new local navmeshes. There are no
orphan local MapInfo entries.

Eighteen door triangles are distributed across nine navmeshes. Every triangle
index is within its navmesh's triangle array, every local door reference
resolves within the plugin, and every master door reference resolves through
the declared masters. Every edge from a new local navmesh targets a navmesh
present in the main. Five new navmeshes have no edge links; that can be valid
for intentionally isolated islands and is not by itself a defect.

Largashbur is a substantial topology rebuild, not a few decoration records:

| Exterior cell | Main's navmesh set |
|---|---|
| LargashburExterior01 `(33,-27)` | vanilla overrides `0E0C0E`, `0E0C0D`, `0E0C0C`; locals `000316`, `00031A`, `00031B` |
| LargashburExterior02 `(32,-27)` | `105266`, `0B33C1`, `059DAD`; local `000319` |
| LargashburExterior03 `(33,-28)` | `105275`, `105274`, `0B2997`, `0B2996`, `0B2995`, `097601`; locals `000317`, `000318` |
| LargashburExterior04 `(32,-28)` | `105265`, `0596C0` |

Local NAVM `000316` alone has 149 vertices, 161 triangles, and 10 edge links.
Local `000317` has 101 vertices, 128 triangles, nine edge links, and two door
triangles. Static schema consistency cannot establish that their borders,
portals, height changes, and preferred route form a traversable quest path.
If a border, island, or door portal is wrong, Creation Kit topology editing and
finalization are required; xEdit field forwarding is not a safe substitute.

## Atub and The Cursed Tribe

Current main-mod posts contain three independent confirmations of the same
failure surface:

- 21 May 2026: Atub wanders away because of pathing during The Cursed Tribe;
- 2 June: another user reports the same issue;
- 24 July: another exact report, after the author had been unable to reproduce
  it on 22 May.

The plugin contains no QUST records and does not override Atub `019E18`, DA06,
or her ordinary base packages `028D4B`, `01B210`, and `01E606`. Quest aliases
can supply active packages at runtime, so changing Atub's base NPC or ordinary
package list would be speculative and could mask rather than repair the route.
The stronghold's rebuilt environment/navmesh is the direct conflict surface.

Neither public The Cursed Tribe Quest Expansion patch addresses this vanilla
route. They move quest-expansion actors and markers into the new physical
layout. The current collection version has seven records; the separately
published Nexus 171734 plugin has 33 records and is the more comprehensive
candidate if TCTQE is later selected. They share six records, so they must not
be stacked blindly. Neither contains NAVM or NAVI.

The present result is therefore **unresolved and not statically certifiable**.
A disposable new world must run DA06 from approach through Atub's ritual. If
the failure appears, capture the failing segment and repair/finalize the
relevant navmesh in the CK, then repeat with followers and stronghold residents.

## Relevant current patch matrix

| Combination | Exact current result | Repair class / action boundary |
|---|---|---|
| USSEP 4.3.9 | Collection patch: 38 records (9 CELL, 28 REFR, 1 WRLD), no NAVM/NAVI. Its 36 substantive intersections and all targets still exist in current USSEP. The collection predates 4.3.9 by 17 days, but the 4.3.9 changelog has no stronghold-target change. | Ordinary headless semantic winner audit. Suitable public dependency candidate; final current-master check still required after selection. |
| Lux Orbis | Current collection patch: 75 records (14 CELL, 60 REFR, 1 WRLD), no NAVM/NAVI. It is an exact superset of the author's older 59-record optional and adds/fixes exterior light references. | Use the current collection variant, not both. Headlessly patchable; no CK indicated. |
| Lux Via | The author's May 2025 patch has 12 records: 4 CELL, 4 LAND, 3 REFR, 1 WRLD. No newer current-collection Lux Via patch exists. | Do not load blindly after the August 2026 replacement main. Reconcile LAND headlessly, then visually validate seams. |
| NotWL 3.14 + Nordic Cut 1.2.2 | Nordic Cut's bundled Orc patch has 38 records (11 CELL, 26 REFR, 1 WRLD), exact Orc/NotWL/Nordic masters, and all five targeted Orc-local references still exist in the replacement main. | This is the current tailored candidate. It supersedes the author's NotWL 3.12 optional and the generic collection's non-Nordic NotWL patch. Do not stack placement patches. |
| Generic NotWL patch | Current collection plugin has 46 records and no Nordic Cut master; the page labels it NotWL 3.0. It shares only 16 records with the Nordic-specific plugin. | Relevant only to a non-Nordic tree architecture after a current-version audit. Not the planned Nordic-stack answer. |
| ZX Fixes | Nine-record ESP-FE with four Dushnikh Yal LAND overrides. Every normalized LAND field is byte-semantically identical to the 1.4.2 replacement main. | Redundant with the replacement main; use only with untouched v1.2.1. Do not combine. |
| TCTQE | Collection patch has 7 records; standalone Nexus 171734 has 33 and was published later. Neither touches NAVM/NAVI or vanilla Atub packages. TCTQE is not installed. | No current action. If TCTQE is selected, audit the standalone as the leading placement candidate and do not stack both. |

### Lux Via terrain collision in detail

For every affected Largashbur LAND record, the old Lux Via compatibility patch,
the original v1.2.1 main, and the 1.4.2 replacement have three distinct final
height-map payloads:

| LAND | v1.2.1 height hash | 1.4.2 replacement | old Lux Via patch |
|---|---|---|---|
| `00CD3C` | `4721570FB9` | `EEB2AFA9DA` | `2EFACAD950` |
| `00CD3D` | `08DE748383` | `FC0E5E0404` | `1E5E162B1A` |
| `00CD5D` | `7058AE960C` | `92E9135D1A` | `A2D4ED6996` |
| `00CD5E` | `F54A5D11CD` | `D5CDFBCDE3` | `4D29247CBD` |

The old patch was authored against the old terrain, so its winning state would
overwrite all four newer replacement-main winners. A proper owned repair must
reconcile per-vertex LAND deltas/borders with the Lux Via references, then check
the Largashbur road and cell borders in game. This is headless data work plus a
visual acceptance route; it becomes CK work only if the geometry/navmesh itself
also needs editing.

## Exact repair classification

| Finding | Owned ESL / headless patch | Vendor-bound headless change | Creation Kit required |
|---|:---:|:---:|:---:|
| USSEP ordinary REFR/CELL/WRLD winners | Yes | No | No |
| Lux Orbis light/reference winners | Yes | No | No |
| Nordic Cut/NotWL placements and headers | Yes, using exact public patch plus a small final winner if needed | No | No |
| Lux Via four-cell LAND reconciliation | Yes, with exact delta work and visual seam validation | No | Not initially |
| Ownership, enable-state, placement, package, door-link, and ordinary field conflicts | Yes, when semantics are known | No | No |
| Removing the originating main's 23 NAVM, 12 CELL, and one local REFR definitions | No; an overlay cannot erase their origin | Yes: replacement/cleaned main | No |
| ESM+ESL conversion to reduce temporary-reference pressure | No; it changes the main's load class | Yes: upstream or expressly approved private main | No, but full runtime regression is mandatory |
| Atub base NPC/package override | Mechanically yes, but **not an evidenced repair** | No | No |
| Broken navmesh islands, borders, topology, portals, or door triangles if reproduced | No | No | **Yes: edit, finalize, and route-test** |
| New/changed occlusion or large geometry | Record inspection can triage it | Possibly | CK if topology/occlusion authoring is needed |

No public patch currently justifies claiming that the DA06 route is fixed.

## Validation gate after a user decision

Any candidate must remain out of the main profile until it passes a disposable
new-world route:

- trigger The Cursed Tribe normally and observe Atub from approach through the
  complete ritual sequence, with no console teleport or dev-room bypass;
- test followers, residents, combatants, and the player through every stronghold
  gate and door, especially all Largashbur cell borders;
- walk every Dushnikh Yal and Largashbur terrain seam, including the Lux Via
  road approach, at multiple camera angles;
- inspect exterior lights at dusk/night and confirm Nordic Cut/NotWL trees do
  not block routes or clip structures;
- run the final selected load order through xEdit error/deleted-reference checks
  and LOOT diagnostics;
- regenerate grass/LOD/DynDOLOD only after the landscape/tree/layout stack is
  frozen, then repeat the seam and route sweep.

Static NAVI and door-index checks are necessary, but passing them is not an
acceptance substitute.

## Distribution and ownership boundary

- The original author and Alaxouche remain the owners of their archives.
- Alaxouche's current permissions do not authorize this project to modify or
  redistribute the replacement plugin or meshes.
- A public modpack may express these files as externally fetched Nexus
  dependencies, subject to Nexus/author terms, and may ship a genuinely owned
  compatibility ESL containing only this project's new patch work.
- The project must not publish a silently modified copy of either main plugin.
- A local ESM+ESL conversion or cleaned main, if ever explicitly authorized,
  must be tracked as non-redistributable unless upstream licensing changes.

## Primary/current sources

- [Orc Strongholds - All In One](https://www.nexusmods.com/skyrimspecialedition/mods/150246),
  its [current files](https://www.nexusmods.com/skyrimspecialedition/mods/150246?tab=files),
  and [current posts](https://www.nexusmods.com/skyrimspecialedition/mods/150246?tab=posts)
- [Orc Strongholds AIO Patch Collection / Fixes and Optimization](https://www.nexusmods.com/skyrimspecialedition/mods/160944)
- [Orc Strongholds AIO - ZX Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/186438)
- [Orc Strongholds AIO - The Cursed Tribe Quest Expansion Patch](https://www.nexusmods.com/skyrimspecialedition/mods/171734)
- [Nature of the Wild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/63604)
  and [Nordic Cut](https://www.nexusmods.com/skyrimspecialedition/mods/161936)
- [xEdit: Managing Mod Files](https://tes5edit.github.io/docs/8-managing-mod-files.html)
  and [xEdit releases](https://github.com/TES5Edit/TES5Edit/releases)
- [DynDOLOD large-reference documentation](https://dyndolod.info/Help/Large-References)
- [USSEP 4.3.9 release/changelog](https://www.afkmods.com/index.php?/topic/10216-relz-unofficial-skyrim-special-edition-patch/)
