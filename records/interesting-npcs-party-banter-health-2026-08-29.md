# Interesting NPCs and Party Banter health audit

Read-only audit completed 2026-08-29 for Skyrim SE/AE runtime `1.7.104`.
Nothing was installed, no curator Keep/Skip state was changed, and no game or
visible mod-manager process was launched.

## Decision

| Mod | Decision now | Why |
|---|---|---|
| [Interesting NPCs SE (3DNPC)](https://www.nexusmods.com/skyrimspecialedition/mods/29194) | **Hold** | It remains a substantial, technically viable quest/NPC expansion with a living patch ecosystem, but its frozen base plugin is enormous and permanent-save territory. The city plan and shared-world/PROTEUS replacement are not settled enough to accept that footprint yet. |
| [Interesting NPCs Party Banter](https://www.nexusmods.com/skyrimspecialedition/mods/104014) | **Hold; conditional Keep if 3DNPC passes** | Its ESP-FE is small, source-included, and technically low risk. It is worthwhile only if the base mod stays and the playthrough regularly uses two or more of its supported followers. The spliced dialogue needs an audio audition before a quality decision. |

This is not a recommendation to Skip either mod permanently. It is a
stability-first recommendation not to put them into the current live profile
or an established save while major city and multi-character systems are still
changing.

## Current official files and provenance

### Interesting NPCs

- Current install is **both** main file `308366`, version `4.5`, uploaded
  2022-08-18, and update file `377786`, version `4.54`, uploaded 2023-04-13.
- The Nexus page header still says `4.53`; the actual update file is `4.54`.
- Main archive SHA-256:
  `346dba78593e2b5d386b789cc7a00899241baf8d6df6f29c9e3bde31384af050`.
- Update archive SHA-256:
  `c5198e3bb31f005522f7faacc282b8ce92eac40ca35c4ff981d113db9a1937ab`.
- The base page was last updated in 2023 and its posts are disabled. The
  companion-fix ecosystem is still active: several relevant patches were
  updated in 2024-2026.

### Party Banter

- Current file is `468839`, `ESPFE-1.0.4`, uploaded 2024-02-08. Do not use the
  simultaneous full-ESP file `468837`.
- Archive SHA-256:
  `2451ef9ead0576259c1571071a7e98bd7eac6e9169321ea6d79e25213bd09049`.
- It has no DLL or runtime-specific native dependency, so its 2024 date does
  not by itself make it obsolete on runtime `1.7.104`.

## Base-mod footprint

Headless parsing of the current `3DNPC.esp` found:

- ESM-flagged full plugin; not ESL and not a candidate for ESL conversion;
- 102,131 records: 100,837 new and 1,294 overrides;
- 759 NPCs, 489 quests, 2,599 quest aliases, 1,180 scenes, 14,641 dialogue
  topics, 26,809 dialogue responses, and 2,481 packages;
- 528 cells, 195 navmeshes, 41 landscape records, 14 worldspaces, and 48,322
  placed references; and
- no deleted records detected by the local parser.

The packed install expands to about 2.87 GiB. Its archives contain 644 FaceGen
meshes, 644 FaceTint textures, roughly 43,945 FUZ voice assets, and 6,908 PEX
files. Most PEX files are generated dialogue/quest fragments; 504 are other
custom scripts. The raw script count therefore overstates steady Papyrus load,
but the plugin's quest, alias, cell, navmesh, and persistent-reference surface
is genuinely large.

This is not evidence that 3DNPC constantly consumes large FPS or Papyrus time.
It is evidence that conflicts and save-state consequences are broad. Treat it
as a new-game, remain-installed-for-the-life-of-the-save mod. The official page
also recommends a new game for intended behavior; its more optimistic uninstall
language is not an acceptable basis for a stability-first list this complex.

## Writing and voice: fact versus taste

Factual signals are strong but do not settle taste: the official description
advertises 250+ voiced NPCs, 25+ followers, 50+ quests, and 80+ voice actors;
Nexus reports about 1.54 million unique downloads and 44,191 endorsements. The
author also explains that the project began before they had much modding
experience, which helps explain elaborate quest prerequisites and wiki-like
discovery requirements.

An 80-plus-actor anthology cannot have one uniform performance, recording
chain, or writing style. Whether its verbose, branching conversations feel
like welcome role-playing or slow the game down is a preference, not a
technical defect. A fair decision needs an isolated new-game audition covering
at least two ordinary NPCs, one super follower, and one quest before committing
the live list.

## Required and conditional patch stack

If 3DNPC is eventually approved, install the following in a fresh test profile
in this order, with each patch after all of its masters:

1. 3DNPC main `308366`, then update `377786` overwriting it.
2. [Interesting NPCs ILS Freeze Fix](https://www.nexusmods.com/skyrimspecialedition/mods/131848),
   file `553928`, version `0.1.1`. **Required.** Its ESP-FE has only three
   overrides and fixes the known Rift Watchtower/Snapleg Cave infinite-load
   path caused by 3DNPC moving vanilla Orc reference `000D1F56` between cells.
3. [Abandoned Prison combat fix](https://www.nexusmods.com/skyrimspecialedition/mods/129827),
   file `544787`, version `1.0.0`. **Required with Skyrim Unbound.** Its four
   overrides prevent Fjona's Familiar and the prison bandits from entering an
   endless fight. The current alternate-start room makes this directly
   relevant.
4. [3DNPC Script Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/87245),
   file `473807`, version `2.1`: select the Cat and Mouse quest script fix.
   Treat the optional Barbas dialogue-performance fix as **Hold** because it
   requires the native [Rogue's Gallery](https://www.nexusmods.com/skyrimspecialedition/mods/99482)
   DLL. Rogue's Gallery is source-available and CommonLibSSE-NG based, but its
   shipped 2023 binary has not yet been rebuilt and smoke-tested on `1.7.104`.
5. Re-run the NFF `2.8.6b` FOMOD and select its native `3DNPC` support scripts
   (`30 iNPC/Scripts`). The current recorded NFF plan omits them. NFF's scripts
   must overwrite the corresponding 3DNPC scripts; do not invent a generic
   follower-framework patch.
6. Select `Lux - 3DNPC patch.esp` from the current Lux Patch Hub `7.1`.
   **Required with Lux.** It is ESL-flagged but substantial: 2,994 records,
   including 68 cells and 2,908 placed references. Do **not** select Lux's
   `3DNPC Alternate Start` patch; it is for the separate
   `3DNPC Alternative Locations.esp`, not Skyrim Unbound.
7. If vanilla Survival Mode remains, add
   [3DNPC - Survival Mode](https://www.nexusmods.com/skyrimspecialedition/mods/73584),
   file `308490`, version `1.00`. It is a six-record ESP-FE that gives six
   3DNPC food items Survival hunger effects. This is a completeness patch, not
   a stability fix.
8. Add only the city/interior patches required by the final city stack:
   - Grand Solitude: use `Grand Solitude - 3DNPC patch.esp` from
     [Grand Solitude Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/157450),
     current file `797296`, version `1.5`. It has 37 overrides and no new
     records. If JK's Bards College is also selected, use the collection's
     explicit Grand Solitude + JK's Bards College + 3DNPC consistency patch.
   - JK's Skyrim: use the current
     [JK's Skyrim Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/154077)
     3DNPC option. JK's individual interiors require their own current patch
     collection options; do not assume the exterior patch covers them.
   - Re-audit any other city, inn, palace, college, or interior overhaul. Some
     3DNPC quest triggers depend on persistent furniture/placed references, so
     resolving only visible clipping is not sufficient.
9. If full AI Overhaul is later installed, use the AI Overhaul option from
   [3DNPC Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/89307),
   file `508515`, version `1.8.1`, rather than the stale 2020 patch on the base
   page. AI Overhaul is not active now, so install neither today. AI Overhaul
   Lite does not need that patch.
10. `3DNPCs Fixes and Tweaks` file `691176`, version `6.2`, is **optional and
    decision-bearing**, not a blind bug-fix requirement. Its 125-record ESP-FE
    also changes ownership, packages, inventory/merchant behavior, spells,
    dialogue, and an ending. Review those gameplay choices individually before
    adding it; several changes need a new game to take full effect.

Bruma, Beyond Reach, and Wyrmstooth are separate worldspaces and are not masters
of 3DNPC, so there is no direct plugin dependency or blanket compatibility
patch. 3DNPC followers can travel there, but they do not gain authored quest or
location commentary. New-land locations may also lack vanilla keywords used
by generic banter conditions. Check any future crossover addon individually.

The planned shared-world persona system is the larger conceptual boundary:
3DNPC quests, relationships, persistent aliases, and NPC memory live in the
world save. They will not automatically become per-player-character state.
There is no proven hard conflict with PROTEUS, but the replacement system must
explicitly define which 3DNPC state is shared before this mod can be signed off.

## Party Banter technical and content audit

The current ESP-FE is valid ESL form `1.7`, uses compact-range FormIDs, and has
729 wholly new records with zero overrides or deletions: 320 dialogue topics,
365 responses, 38 scenes, two quests, one package, and three globals. Its only
external master is `3DNPC.esp` in addition to Skyrim/Dawnguard.

The archive includes 44 compiled scripts and their sources, 364 FUZ files, and
five WAV/LIP pairs. The scripts are chiefly generated topic fragments. The
small custom control surface is event/scene driven; no continuous polling loop
was found. The two controller quests are start-game-enabled and run once, and
one alias repair script runs on load. Runtime overhead should be minor.

The banter is intentionally rare: idle starters generally combine a less-than
one-percent random test with a second 15-50-percent random test, have a 24-hour
reset, and check proximity/scene/dialogue state. There is no MCM or frequency
control. Combat-to-normal scenes are similarly gated. That reduces spam but
may make the mod appear inactive during a short test.

Transcript inspection found 38 scenes and about 326 scene lines. The dialogue
is assembled from original 3DNPC recordings rather than generated voice. It is
mostly character-specific, but textual evidence shows imperfect joins and
editing: e.g. `Advenuring`, `tarvern`, `College if taking`, `don't get wrong`,
and doubled spaces. Archive inspection cannot judge room-tone cuts, cadence,
or audible splice quality; those require headphones and an in-game audition.

The page advertises Amalee, Anum-La, Rumarin, Valgus, and Zora. The plugin also
contains a Morndas alias and a 16-line Morndas scene despite documentation
describing her as future work. Qa'Dojo has only dummy/unused WAV/LIP material.
This is a documentation/content inconsistency, not a stability fault.

Because the scenes target specific placed followers, the mod has little value
for a lone-follower playthrough and does not create general banter for NFF,
Varinia, or new-land followers. Its conditions verify nearby actors and scene
state; they do not consistently prove every actor is actively recruited. Use
the ESP-FE from the start of a new test game and never switch between its full
ESP and ESP-FE variants mid-save.

## Stability-first validation gate

Before changing Keep or installing either mod:

1. Freeze the city/interior list and the shared-world persona-state rules.
2. Build a separate disposable new-game MO2 profile with the exact stack above.
3. Run master/order, asset-conflict, and xEdit conflict checks; inspect every
   cell/navmesh/persistent-reference winner involving the chosen city stack.
4. Exercise Abandoned Prison, Rift Watchtower/Snapleg Cave, one inn/city altered
   by the final overhaul stack, one 3DNPC quest chain, dismissal/re-recruitment
   through NFF support, and save/reload cycles.
5. Add Party Banter ESP-FE only after the base test passes; recruit at least two
   supported super followers and audition several idle and post-combat scenes.
6. Accept 3DNPC into the real list only if its writing/voice audition passes and
   the persona system can preserve its world-global quest state safely.

## Evidence integrity

All listed archives were obtained through the local read-only Nexus audit
cache. No API credential was printed, copied to this repository, or embedded
in this report. Vendor archives and extracted assets remain unmodified and are
not suitable for redistribution without their respective permissions.
