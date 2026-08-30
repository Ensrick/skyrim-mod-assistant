# Cutting Room Floor 3.1.26 compatibility audit

Audit date: 2026-08-30  
Game/runtime: Skyrim Special Edition 1.7.99  
MO2 instance/profile: `mo2-instances/skyrim-se` / `Default`  
Outcome: three exact official compatibility plugins installed; one owned
semantic merge remains required before this is a clean long-playthrough
baseline  
Tracker: [issue #71](https://github.com/Ensrick/skyrim-mod-assistant/issues/71)

## Executive verdict

Cutting Room Floor (CRF) 3.1.26 itself is current for this installation and its
declared requirements are satisfied by Skyrim 1.7.99 and USSEP 4.3.9. The
core-only FOMOD choice is correct because neither RS Children nor Skyrim
Bridges is installed. CRF contains no native DLL, but it does ship 81 compiled
Papyrus scripts (and 81 matching source files) in its BSA, so the author's
warning not to uninstall it mid-save matters.

The active profile was missing three exact, non-subjective official patches.
They have now been installed and enabled:

1. Interesting NPCs - Cutting Room Floor Patch 1.0;
2. Lux - Cutting Room Floor, from Lux Patch Hub 7.1; and
3. Lux - Skyrim Unbound, from Lux Patch Hub 7.1.

Those patches close Jenassa persistence/bed ownership and the intended Lux
interior-lighting integration, but they do not cover every active-profile
semantic conflict. Four conflict families remain: the new Dark Chasm cell
location is erased by Water for ENB, NFF has a stale WhiterunLocation baseline,
Lux drops several CRF location edits, and Skyrim Unbound drops one CRF dialogue
condition. The correct repair is one small separate override-only ESP-FE that
merges individual fields. Simply making CRF win would break the later mods'
intentional changes.

**First-playthrough risk:** no launch blocker or missing master was found, and
the remaining conflicts are not evidence of save corruption. However, this is
only a **conditional hold** for a long first playthrough: restored CRF content
can have incorrect location membership or dialogue state until issue #71 is
implemented and tested. CRF should not be removed after beginning a real save.

## Exact installed inputs

| Input | Current file | Relevant facts |
|---|---|---|
| [Cutting Room Floor](https://www.nexusmods.com/skyrimspecialedition/mods/276) | 3.1.26, Nexus file 796288, updated 2026-08-28 | SHA-256 `5a007881a7239bdb2e71e7803b0435c0d882ddfe2d47390254252aedf14a3911`; transaction `20260830T145141131Z-f640a5af31c9`; lowercase `cutting room floor.esp`; 4,796 records; 225 BSA entries; no DLL. |
| USSEP | 4.3.9 | Satisfies CRF 3.1.26's minimum. |
| [Lux Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/113002) | 7.1, Nexus file 695703, updated 2026-08-28 | SHA-256 `90a71f107383b46eb9a7d1927037e96046de6a5f2d110af96c147e0729490fc4`; reinstalled from the retained immutable archive with only exact active-plugin selections added. |
| [Interesting NPCs](https://www.nexusmods.com/skyrimspecialedition/mods/29194) | 4.5 main + 4.54 update | The page's official CRF patch remains the current published patch. |
| [Water for ENB](https://www.nexusmods.com/skyrimspecialedition/mods/37061) | 2.21, Shades of Skyrim | Current plugin intentionally wins water/cubemap fields and supports the Community Shaders route; it predates CRF 3.1.26's Dark Chasm addition. |
| [Skyrim Unbound Reborn](https://www.nexusmods.com/skyrimspecialedition/mods/27962) | 3.0.17 | Current 2026 release; the current Lux hub supplies its Lux patch. |
| [Nether's Follower Framework](https://www.nexusmods.com/skyrimspecialedition/mods/55653) | 2.8.6 | Current files expose no CRF compatibility plugin. |

CRF's current readme requires Skyrim 1.7.99 or newer and USSEP 4.3.9 or
newer, directs CRF to load early, forbids extracting the BSAs, and warns against
mid-save uninstall. Version 3.1.23 folded the former RS Children and Skyrim
Bridges patches into the main FOMOD; 3.1.24 supplied the Small World/city fix;
3.1.26 added the Soul Cairn Dark Chasm and gilded wristguards.

## Official patch disposition

### Installed

| Plugin | Archive inspection | Disposition |
|---|---|---|
| `3DNPC - CRF Patch.esp` | ESL-flagged; masters are `Skyrim.esm`, `3DNPC.esp`, and `Cutting Room Floor.esp`; two override records only; no scripts or assets; installed plugin SHA-256 `11d1a9b98a48a76bfdf31374b1063b8524e9d390b55ed276a9a390986bbc4b2b`. It restores Jenassa's persistent flag while retaining CRF's linked-bed edit. | Installed as `Interesting NPCs - Cutting Room Floor Patch`; transaction `20260830T151425265Z-3f0b434e9fc7`. The underlying CRF Jenassa edit is still present in 3.1.26, so the 2020 publication date does not make this patch obsolete. |
| `Lux - Cuting Room Floor.esp` | ESL-flagged; masters are Skyrim, Dawnguard, Lux Resources, CRF, and Lux; 763 records (550 new, 213 overrides), no loose scripts/assets; installed plugin SHA-256 `8236dec68efa187fdae11482cba6f6e41f51d8e2880d67977ac23965510851b0a`. It covers 15 CRF-added interiors plus the Hall of Countenance and Solitude Thalmor HQ. | Selected from the current Lux 7.1 FOMOD and enabled; Lux Patch Hub transaction `20260830T151432646Z-57394b534ecf`. |
| `Lux - Skyrim Unbound patch.esp` | ESL-flagged; masters are Skyrim, Dawnguard, Skyrim Unbound, and Lux; 26 records (five new, 21 overrides), no loose scripts/assets; installed plugin SHA-256 `89979c57b5bfa4d0acca3b5bc43d371b29496313efff9b0d45efa3b56f3f1d2e`. | Selected from the current Lux 7.1 FOMOD and enabled in the same transaction. |

The final order is CRF at load-order line 30, the 3DNPC patch at 83, Skyrim
Unbound at 84, Lux at 86, the Lux CRF patch at 120, the Lux Unbound patch at
121, and Water for ENB Shades at 122. This satisfies every inspected patch's
master order.

### Rejected, obsolete, or not applicable

- CRF's integrated RS Children and Skyrim Bridges components were correctly
  left unselected: neither master is installed. Old separate downloads for
  these combinations are superseded by CRF 3.1.23's FOMOD integration.
- [Cutting Room Floor - Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/110591)
  1.0 does not address the active conflicts. Its documented targets include
  Guards Armor Replacer, Cloaks of Skyrim, New Legion, USMP, Triumvirate and
  other absent mods—not Sons of Skyrim, NFF, Water for ENB, or Skyrim Unbound.
- The current [AI Overhaul official patch hub](https://www.nexusmods.com/skyrimspecialedition/mods/35823)
  still describes its CRF patch against CRF 3.1.11. AI Overhaul is not active,
  so installing that patch would add an absent master and solve no current
  conflict.
- [Water for ENB USSEP and Location Patches](https://www.nexusmods.com/skyrimspecialedition/mods/50394)
  explains the correct XLCN-forwarding principle but publishes patches only
  for USSEP, Millwater Retreat, Moon and Star, and Oakwood. It has no CRF/Dark
  Chasm patch.
- NFF 2.8.6's current three-file page contains no CRF patch. No current
  authoritative NFF/CRF plugin was found.
- Generic legacy CRF patches were not installed by title-matching. A patch was
  accepted only when its masters, records, flags, payload, and active-version
  semantics matched this exact profile.

## Whole-profile record audit

The final parse covered 121 active plugins with zero parser failures. There are
272 CRF shared-record chains; 116 have a later winning plugin. Winner counts are
not defect counts: most later winners are intentional lighting, water, outfit,
or alternate-start edits.

### Unresolved semantic merges

| Record | Current winner | Lost CRF intent | Required treatment |
|---|---|---|---|
| `CELL 006439:Dawnguard.esm`, `SoulCairnZcell01` | Water for ENB | CRF 3.1.26 adds XLCN `CRFDLC1SoulCairnDarkChasmLocation` (`005900:cutting room floor.esp`); Water wins with null Location. | Preserve every intended Water/cubemap field and restore CRF's XLCN. This is a high-confidence regression caused by CRF being newer than Water 2.21. |
| `LCTN 018A56:Skyrim.esm`, `WhiterunLocation` | NFF | NFF's raw arrays omit CRF's three appended `ACPR` entries and its `ACEC` block, demonstrating an older baseline rather than an intentional CRF rejection. | Merge NFF's intentional follower-framework values with the current CRF/location arrays; do not flip the whole winner. |
| `LCTN 019260:Skyrim.esm`, `KilkreathRuinsLocation` | Lux | CRF's Herebane-related persistent-actor addition and three removals. | Retain Lux's location data and CRF's actor membership deltas. |
| `LCTN 01F7FD:Skyrim.esm`, `DushnikhYalBurguksLonghouseLocation` | Lux | CRF's removal of location reference `06A904`. | Retain Lux additions and CRF's removal. |
| `CELL 0DD216:Skyrim.esm`, `SolitudeHalloftheDeadCatacombs` | Lux | CRF assigns `SolitudeCemetaryLocation` (`02008C`); Lux assigns `SolitudeHalloftheDeadLocation` (`0200A1`). | Validate mourning/location semantics in game before selecting XLCN; this is the one genuinely semantic choice rather than a mechanical union. |
| `INFO 02129C:Skyrim.esm` | Skyrim Unbound | CRF replaces the USSEP/player-level check with a `GetDead` test on Tasius so the line cannot fire after his death. Unbound restores the old test and adds its alternate-start global. | Preserve Unbound's alternate-start condition and add CRF's Tasius-dead condition. |

These records are tracked in issue #71. The intended patch must remain a
separate owned plugin, preferably ESP-FE, and must not contain new forms,
scripts, quests, scenes, aliases, persistent references, or NAVM.

### Intentional or benign winners

- Lux's ordinary CELL winners account for nearly all 155 selected-field CELL
  divergences in the pre-patch semantic scan: 139 are lighting templates,
  image spaces, cell lighting, sky/weather, and lighting flags. These are Lux's
  purpose, not lost CRF content. The official Lux CRF patch supplies its custom
  CRF-interior placements and preserves CRF owner/location values in the
  Solitude Thalmor HQ.
- Water for ENB's other CELL/WRLD differences are intended water height/type,
  cubemap, and distant-water data. Only the newly added Dark Chasm XLCN is a
  demonstrated CRF loss.
- Sons of Skyrim intentionally replaces four Stormcloak leveled lists and seven
  outfits. Its dialogue conditions preserve CRF logic while adding Sons armor
  alternatives; one sleeved-armor condition disappears because Sons replaces
  that item. No CRF patch is warranted.
- `Varinia.esp`'s Orthorn reference (`02A389`) is field-identical to CRF's
  payload.
- Skyking Signs cell/world headers preserve the inspected semantic fields;
  child placed-reference groups merge at runtime.
- Lux Orbis CS and Lux Via exterior CELL headers retain the relevant CRF
  fields. The only shared CRF/Lux Via NAVM (`0EA082`) is byte-identical by CRC
  and must not be regenerated or patched.
- NFF, Varinia, Skyking Signs, Sons, Lux Orbis CS, Lux Via, Water, and the Lux
  patches introduce no CRF-related native DLL compatibility problem.

The current conflict scanner keys FormKeys with case-sensitive master strings.
Both inspected third-party CRF patches name their master `Cutting Room
Floor.esp`, while CRF 3.1.26 ships `cutting room floor.esp`. Windows resolves
these as the same file, but the audit therefore undercounts some Lux-patch
chains. Those 15 CRF custom CELL overrides were verified directly. This also
creates a Linux/Steam Deck portability question that must be tested on the
intended deployment filesystem; CRF 3.1.19 explicitly changed to the lowercase
filename, but the current Lux hub and old 3DNPC patch still carry uppercase
master casing.

## Asset conflicts

CRF's BSAs contain 225 entries: 81 compiled scripts, 81 source scripts, 44
meshes, 18 textures, and one sound. Exact active-file comparison found:

- CBBE wins two loose female sleeved-Stormcloak cuirass meshes;
- the active HIMBO refits win four male/first-person sleeved-Stormcloak meshes;
- CRF loads after USSEP and correctly wins 18 purposeful script, mesh, and
  facegen overlaps in their BSAs; and
- Beyond Reach's `arnima.bsa` overlaps one vanilla quest script,
  `scripts/qf_weroad02_001027a5.pex`. The payloads are not identical (CRF:
  2,205 bytes, SHA-256 `11a3fcf6bc34057204466c27299d0a638594954f47967a73ac915700db36c5fc`;
  Beyond Reach: 1,903 bytes, SHA-256
  `ccdd14ddc4ac1c6839105d5395b163d0b0fce512d61263948977f488dffaebff`).
  CRF's later BSA correctly wins this vanilla CRF quest script; no Beyond
  Reach quest record depends on replacing it.

No CRF asset overlap exists with SMIM, Lux, Lux Orbis, Lux Via, Water for ENB,
Skyking Signs, Sons of Skyrim, Varinia, or Interesting NPCs. The CBBE/HIMBO
winners are intentional body-refit replacements, not missing CRF assets.

## LOOT and integrity checks

LOOT completed with exit code 0 after the official patches were installed. It
recognizes CRF and all three compatibility plugins as active and identifies the
patches as light where applicable. It reports no CRF-specific missing master,
dirty-plugin, or compatibility message. Its masterlist recognizes the current
CRF clean CRC `0x98C35BF6`. The only global warning is the already documented
Engine Fixes Part 2 warning, which is not a CRF finding and is inapplicable to
the current Engine Fixes 7 beta arrangement.

LOOT metadata is supporting evidence, not proof: the semantic field comparison
above is what exposed the Dark Chasm, NFF, Lux-location, and Unbound losses.
`records/installed-mods.json` passes ledger verification after the installation.

The sort wrapper exposed an independent tooling defect: it silently enabled
`PROTEUS.esp`, `QuickLootIE.esp`, `TerrainHelper.esp`, and `Ensrick Lux Water CS
Patch.esp`, all of which were deliberately disabled. They were immediately
disabled again through journaled transactions and their final state was
verified. [Issue #73](https://github.com/Ensrick/skyrim-mod-assistant/issues/73)
tracks the required fail-closed state-preservation fix. No game was launched.

## Distribution and ownership boundary

CRF's vendor documentation forbids redistributing CRF or placing it inside a
mod pack. It additionally requires advance author permission before publishing
a compatibility patch, with attribution, source-page links, and the author's
support boundary observed. The current Lux hub also forbids reuploading or
modifying its files without permission, and NFF forbids modification/asset use
without permission.

Accordingly:

- every downloaded vendor archive and plugin remains immutable;
- the proposed compatibility output must be a new, separate owned plugin;
- a private profile-specific build may be generated and tested;
- it must not be uploaded or embedded in a public modpack until CRF patch
  permission is documented; and
- public packaging should reproduce the tracked downloads/FOMOD selections and
  fetch restricted dependencies rather than repack them.

## Required acceptance route

After issue #71's patch is generated, re-run the link/master/conflict audits and
test in a disposable new game: Dark Chasm entry/location behavior; Jenassa and
her Drunken Huntsman bed; Thalmor HQ ownership/trespass across Civil War state;
Tasius dialogue before and after death; Herebane/Kilkreath; Dushnikh; and
Whiterun CRF restored-home/location membership. Promote the output only after
those checks pass.

## Sources

- [Cutting Room Floor — Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/276)
- [Cutting Room Floor — AFK Mods](https://www.afkmods.com/index.php?/files/file/1894-cutting-room-floor/)
- [Lux Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/113002)
- [Lux documentation](https://www.nexusmods.com/skyrimspecialedition/mods/43158)
- [Interesting NPCs files](https://www.nexusmods.com/skyrimspecialedition/mods/29194?tab=files)
- [Water for ENB](https://www.nexusmods.com/skyrimspecialedition/mods/37061)
- [Water for ENB USSEP and Location Patches](https://www.nexusmods.com/skyrimspecialedition/mods/50394)
- [Skyrim Unbound Reborn](https://www.nexusmods.com/skyrimspecialedition/mods/27962)
- [Nether's Follower Framework](https://www.nexusmods.com/skyrimspecialedition/mods/55653)
- [Cutting Room Floor Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/110591)
- [AI Overhaul official patch hub](https://www.nexusmods.com/skyrimspecialedition/mods/35823)
