# Chronicles of Steel: conversion and repair intake

Audited 2026-09-05. Requested by the user: investigate Oldrim pages 12506 and
103289, determine whether both are needed, and perform proper conversion and
bug repair. Status: **private equipment review build; not installed**. The
choice between equipment only, Nord only, and the full faction overhaul is
pending. Nothing here selects final NPC distribution or changes the live game.

Tracking: [issue #238](https://github.com/Ensrick/skyrim-mod-assistant/issues/238).

## Source choice

Use [103289, Weapons of War (Finale)](https://www.nexusmods.com/skyrim/mods/103289)
as the source candidate. It supersedes
[12506, Realswords Nord](https://www.nexusmods.com/skyrim/mods/12506).
Neither download is an SSE port.

| Evidence | 12506 | 103289 |
| --- | --- | --- |
| Published version | 1.0, 2012 | Final, 2020; bundled readme says 1.1 |
| Plugin structure | TCOSS.esp | TCOSS.esm and two ESP modules |
| Weapon records in main plugin | 79 | 381, including 83 Nord records |
| NIFs / DDS | 151 / 66 | 950 / 317 |
| Record format | Form 40 | Form 43 |
| Asset format | LE stream 83 | LE stream 83; BSA version 104 |

All 79 original weapons are represented in Finale. 78 retain their EditorIDs;
`RSNordNaegling` becomes `RSNordNaegling2H` at the same local FormID. Finale adds
four one-handed Naegling variants. Of 217 original assets, 216 paths remain:
150 overlapping meshes and 47 textures changed, and 19 textures are identical.
The omitted `axebeardedworn.nif` has no plugin reference. Installing both would
duplicate the collection and introduce competing distribution.

The other currently available SE route found is the
[Vaultman30 Weapon Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/24567?tab=files).
Its `TCOSS.esp` structure and source link belong to the older branch. It is a
large multi-author replacer, not a standalone conversion of Finale. No current
standalone Finale SE release was located; that search is not proof none exists.

## Exact input provenance

| Input | Nexus file ID | SHA-256 |
| --- | --- | --- |
| The Chronicles of Steel - Skyrim-12506-1-0.rar | 41729 | D14982E1729DC3336B0394C17A46FC792C28041B8D0AD8463DC416F03D40982B |
| Weapons of War-103289-Final-1591581196.zip | 1000320407 | CED4BA4A8FB6705C62706FF2F80FA988E1520917470D3A31171A78ED25568CF5 |
| TCOSS.esm, from Finale | above | F3F2D205BBEB6A884497DCA7ACB4DAA5AC243D7AFF1FF7330E6A6F740002EDF0 |
| TCOSS - ChroniclesOfSteel.esp | above | D41E6108C37403A7A16BB27E0D3018D9DFB040F5FD3B26DC6AA13520BB3678A9 |
| TCOSS - Weapons Of War.esp | above | F2554912BCD78F190D7BA0591421ABE33D5C803320EE412E3647977867D1A59F |
| TCOSS.bsa | above | 73BA09B6A2EBEC21EC0449DDD85BBA6C67621AA2FF149407B7DA3FC0AA6B9F99 |

Archives, extracted files, serialized vendor records, converted assets and
generated plugins remain under ignored `work/chronicles-of-steel/`. Oldrim IDs
must not be written into the SSE-only curator: SSE 12506 is a different page.
MO2, the installed ledger, and Keep have not been changed by this intake.

## Confirmed defects and limits

1. **Old magic-bow texture missing.** The 2012 `bowmagic.nif` and
   `bowmagic2.nif` point to absent `nordbow_em.dds`. Finale corrects them to its
   included `nordbowmagic_em.dds`. Use the revised assets. File conversion alone
   cannot supply an absent material.
2. **Worn battleaxe statistics.** `RSNordAxeWar2HWorn` (01241A) has zero stagger,
   critical damage and critical multiplier in Finale. Its 2012 version has
   stagger 1.15, critical damage 10, multiplier 1; its current new/old siblings
   have stagger 1.15 and critical damage 12/9. The review build restores those
   three worn-axe fields as a candidate repair. Its speed change (0.8 to 1.0)
   remains for the broader balance review; author intent for the regression is
   not established.
3. **Missing race-perk script.** The Chronicles module's player alias references
   `TCOSS_RSRaceQuestScript`, with populated properties, but no PSC or PEX is
   shipped. That quest is not Start Game Enabled and has no incoming reference.
   This dormant feature is outside the equipment build.
4. **Dangling outfit reference.** `5rArmorImperialSpearmanOutfit` references
   nonexistent `008F88:TCOSS.esm`. Its spearman template chain has no incoming
   placed-actor/leveled-NPC reference. It is omitted with NPC/outfit content.
5. **Orphan dog skin texture missing.** `SkinDogCollar` -> `NakedDogCollarAA` ->
   `dog with collar04.nif` references missing `dog_hound_n.dds`. The armor has
   no incoming reference. It and four other creature body skins are excluded
   from the equipment review, with their identities retained in the report.
6. **Three textures have no mip chain:** `legiongladiusold_em.dds`,
   `axebeardedplainold_em.dds`, `norland_n.dds`. All three are in the review
   payload. A pinned texture tool and a format/normal-aware mip repair are
   still required. Existing texture resolution is preserved and is at most 4K.
7. **Full-port world risk.** Finale's master contains 7,390 records, including
   5,216 placed objects, five cells and a navmesh. The WoW module adds world,
   quest, NPC and faction edits and contains six deleted custom-reference
   overrides. Those are not grounds for blind cleaning. A full conversion
   needs semantic conflict review, appropriate CK work and runtime testing.
8. **Visual checks remain.** The old author reported floating sheaths, grip
   alignment and inventory orientation problems. Finale's readme records some
   scabbard transparency/reflectivity/path fixes. No automated check here
   proves the remaining weapon grips, scabbards, blood UVs or worn armor look
   correct, nor that the armors fit the installed bodies or support SMP.

The original master has 36,869 resolved form links against installed Skyrim.esm.
That does not clear its two modules: the dangling outfit is in their combined
definition/reference graph. Similarly, counting all non-custom texture paths
as vanilla would have missed the broken dog normal map; the base-game BSAs were
actually indexed to resolve external references.

## Review build and verification

`ports/chronicles-of-steel/prepare-review.py` prepares an isolated equipment
candidate from the hash-pinned ESM, both ESPs and BSA. It applies the modules in
archive/readme order (master, Chronicles, Weapons of War) for equipment-record
winners. It starts with equipment and recipes, follows every custom FormKey
dependency, and rejects dependencies outside equipment record classes.

The candidate contains 381 weapons, 143 armor/shield/clothing records and eight
ammunition records: **532 items, 1,441 total records**. This includes source
test/prototype items and animal equipment for inspection; it is not an approval
of those items for distribution. Each item is inventoried with full source and
review FormKeys, source winner, models/slots/stats and unresolved role/balance.
Source recipes are retained for review, not approved as final acquisition.

The generated plugin is `Ensrick TCOSS Equipment Review.esp`, light flagged,
Form 44, with IDs 0x800-0xDA0 and Skyrim.esm as its only master. It has no NPC,
quest, outfit, leveled-list, CELL, WRLD, NAVM or placed-reference records. Its
11,506 form links resolve. Five non-inventory creature skins are explicitly
excluded; armor weight-slider partners are accounted for.

894 selected meshes are converted and reloaded as SSE stream 100, with 270
source textures. All included assets move under `ensrick/tcossreview`, and the
plugin models and NIF texture references are redirected accordingly. This
prevents bundled vanilla-path assets from replacing the current modlist's
Imperial gloves, cubemaps or other art. Unbundled vanilla model/texture paths
remain references to the base game and are verified against its archives.

`verify-review.py` checks actual binary record IDs, counts, format and light
flag; confirms the record set after a strict Spriggit roundtrip; compares 2,361
opaque byte-array fields; checks the worn-axe repair; reinspects final remapped
NIFs and texture closure; and inventories texture formats/resolution/mip gaps.
Structural success does not clear the mip, visual, balance, distribution or
runtime gates. No game launch was performed for this intake.

Final local candidate: `work/chronicles-of-steel/equipment-review-v5/mod/`.
Plugin SHA-256:
`96C9201B05C07A7CAB2B14A12781682D6B1C3239E8350C372E72FA9BFA441127`.
Two independent builds matched all **1,165 payload-file hashes**. A subsequent
binary -> YAML -> binary roundtrip preserved every byte of all 1,442 major
record headers and payloads (including TES4); the whole-file hash differs
because of group metadata. `verification.json` records the structural PASS
and explicitly leaves installation, runtime and visual verification false.

## Implementation rationale and tool limits

CK-native implementation: create new equipment records, point models at the
locally converted assets, and set balance/distribution through ordinary weapon,
armor, recipe and leveled-list data. No Papyrus or SKSE DLL is required for that
equipment layer. The CK Weapon and LeveledItem wiki pages were consulted but
returned errors/403 during this audit; local Skyrim records, the original mods,
and the pinned serializers provide the concrete field definitions.

The small Python recipe is justified by a rule-based closure across more than
1,400 records, deterministic FormID remapping and hundreds of asset dependencies.
It uses the existing Spriggit and NIF tools rather than adding a .NET project.
The full mod's world/navmesh and quest behavior are not approximated in code.

Changing a plugin header to 44 is not by itself a conversion. Here the selected
equipment data is parsed and written with the SkyrimSE schema, then checked
again in its binary form. This does not establish equivalent behavior for the
abandoned full ESM/ESP stack.

CAO is an alternative asset tool, not a runtime dependency and not mandatory
when this local recipe is used. The project already uses its source-built
`nif-port-cli` (nifly/SSE NIF Optimizer) and Spriggit. CAO alone does not rebuild
plugins, repair scripts/links or ensure an archive is loaded by a renamed plugin.

## Publication and open decisions

Both source pages reserve third-party asset rights. Finale's generic fields
permit credited fixes, while its asset-reuse terms and author notes still
require permission/contact. Original art is by Waalx, port/integration by
Shingouki, with other contributors credited in the source readme.

The repository may carry this original recipe, factual reports and hashes.
The review plugin is locally derived from vendor records, not yet an
independently authored distributable plugin. It and the NIF/DDS payload must
not be committed or uploaded. A public release needs a rights decision or
permission and a confirmed local reconstruction workflow. Requiring an
original download does not itself grant permission to publish a derivative.

- [ ] User selects equipment-only, Nord-only, or full-overhaul scope.
- [ ] Resolve mipmap repair with a pinned tool and correct channel handling.
- [ ] Review test/prototype content, armor/body compatibility, physics and slots.
- [ ] Normalize item statistics against current modlist baselines.
- [ ] Assign per-item roles and acquisition; integrate with No Mere Bandits.
- [ ] Audit Sons of Skyrim/Imperial equipment distributors and active patches.
- [ ] Complete visual and disposable-save gameplay testing.
- [ ] Install through the normal transaction, ledger and game-aware Keep process.
- [ ] Resolve publication rights and package only the permitted deliverables.
