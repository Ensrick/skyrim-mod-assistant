# Modern physics cloak and weather-driven hood research

Audit date: 2026-08-30

Runtime: Skyrim Special Edition `1.7.104.0` / SKSE `2.3.1` / Address Library
format 5

Tracker: [issue #95](https://github.com/Ensrick/skyrim-mod-assistant/issues/95)

Disposition: research only; no candidate was installed and no Nexus page was
changed to Keep or Skip

## Executive recommendation

The best near-term design is a layered system, not a single cloak overhaul:

1. retain the installed [FSMP](https://www.nexusmods.com/skyrimspecialedition/mods/57339)
   4.1.1 physics runtime;
2. audition [More Scarves](https://www.nexusmods.com/skyrimspecialedition/mods/149259)
   1.4.0 as the first hooded-cape/scarf asset family and
   [Bocksten Cloak](https://www.nexusmods.com/skyrimspecialedition/mods/138180)
   1.1 as the ordinary unhooded cloth cloak;
3. use [Helmet Toggle 2](https://www.nexusmods.com/skyrimspecialedition/mods/100617)
   3.6.2 with Dynamic Armor Variants for player/follower raised and lowered
   hood states; and
4. hold generic NPC weather injection until one of the modern native
   frameworks has a licensed, source-matched build for runtime 1.7.104.

This is not yet an installation recommendation. The current official Dynamic
Armor Variants binary cannot load on the present runtime. The new GPL
[1.7.99 compatibility build](https://www.nexusmods.com/skyrimspecialedition/mods/189578)
passes the static 1.7.104 gate and is the most credible bridge, but it still
needs a foreground log/smoke test before adoption.

The broad NPC candidates are genuinely modern, but neither released build is
usable on the current game as shipped. Seasonal Clothing Framework 1.0.1 and
WeatherBehaviorNG 2.5.1 were compiled before CommonLibSSE-NG gained Address
Library format-5 support on 2026-08-21. Their public repositories also have no
software license, and WeatherBehaviorNG's public source trails its Nexus binary.
They must not be installed, forked, or repackaged on assumptions.

## Current profile facts

| Component | Current state | Relevance |
|---|---|---|
| FSMP | Installed and enabled, Nexus 57339 file 795580, version 4.1.1 | Current GPL physics runtime; no replacement is needed. |
| Starfrost | Installed and enabled, version 2.0.0 | Uses the native Survival warmth system and recommends 25-50 warmth for cloaks. |
| Survival Mode Improved | Installed and enabled, version 1.7.0 | Provides the current needs/cold implementation. |
| KID | Installed and enabled, version 4.1.0 | Can tag assets without editing vendor plugins. |
| SPID | Installed and enabled, version 7.3.3 | Its DLL is now physically correct at `SKSE/Plugins`; the earlier staging defect is resolved. |
| SkyPatcher | Installed and enabled, version 7.0.3 | Its DLL is now physically correct at `SKSE/Plugins`; use for owned distribution rules where supported. |
| OAR / Pandora | Installed and enabled | Suitable animation and behavior-generation base for Helmet Toggle. |
| po3 Papyrus Extender / po3 Tweaks | Installed and enabled | Helmet Toggle and Seasonal Clothing Framework dependencies respectively. |
| SKSE Menu Framework | Installed and enabled | Seasonal Clothing Framework's configuration UI dependency. |
| IED | Installed but disabled in `Default` | Equipped cloaks do not need IED. Helmet Toggle hand/waist props are unavailable until IED is separately restored. |
| Community Shaders Wetness Effects | Installed and enabled | Visual wetness only; it does not create a gameplay wetness need or waterproofing mechanic. |

The current profile contains no Dynamic Armor Variants, Helmet Toggle,
Dynamic Lowered Hoods, Offset Movement Animation, cloak, or scarf package.

## Exact artifacts inspected

These archives were downloaded only to the MO2 download/audit cache and
extracted outside the `mods` directory. They were not installed or enabled.

| Candidate | Exact artifact | SHA-256 |
|---|---|---|
| WeatherBehaviorNG 2.5.1 | Nexus 175377 file 750568, `175377-750568.zip` | `2DCF786A049EFE6CE561206D1D1B85F50B466D464F9DDAED03170E935643A8FD` |
| Helmet Toggle 2 3.6.2 | Nexus 100617 file 793507, `100617-793507.zip` | `A3C94D158AEE63BE04484FCA225C5FD408AFC20C61F2A167771BFAF1020DF229` |
| Dynamic Armor Variants 1.0.5 | Nexus 65963 file 322509, `65963-322509.7z` | `092D403E3619AD4A9C69F39B7B712A61B4EC7B72FFF3E80EF2B6A044B0080AFC` |
| DAV 1.7.99 compatibility patch 1.1 | Nexus 189578 file 795486, `189578-795486.zip` | `8E169AB5788530665AE192BD348190CCFCDCBCC6004B34F6179C462423F901C6` |
| Seasonal Clothing Framework 1.0.1 | Nexus 186269 file 780931, `186269-780931.zip` | `B61C329C9AB57E14E4C804F1C8F4916D11420F782E8521516E9E1737CD2E02D1` |
| Dynamic Armor Variants Extended 1.7.5 | GitHub release `v1.7.5` | `38438E139ADCCF6EB91EAB202ACA8F00AED3B359DC02E41041F50E34FB735F62` |

Native DLL results:

| DLL | SHA-256 | Static 1.7.104 result | Effective conclusion |
|---|---|---|---|
| WeatherBehaviorNG 2.5.1 | `4FF6A634740D2A46D7DD741C52A0C42C53B12B74A53FD31FB5A0D478E6C1D5B4` | SKSE metadata admits the DLL | Compiled 2026-05-10, before format 5; cannot parse the current Address Library. Hold. |
| Seasonal Clothing Framework 1.0.1 `WeatherBehavior.dll` | `A59C48FC6C93AA8C05634CE9E452E2891775454E3777E36BE755F6C3A34E73F6` | SKSE metadata admits the DLL | Its pinned CommonLib submodule is 2026-02-15, before format 5. Hold. |
| Official DAV 1.0.5 | `0F28EFCAD16B3FE401001F13CBAD5DCB46B288DB6BBCC0BEBE906A1C8E2A461B` | Fails the current gate | Published for 1.6.629-1.6.659. Do not use as the winning DLL. |
| DAV 1.7.99 compatibility DLL 1.1 | `2B1E0C640290BDD08A86F5F142D5FE01BC2CD791B3FBAB4ACD82160A06EEF622` | Pass: `versionIndependence=5`, `versionIndependenceEx=2` | CommonLibSSE-NG format-5 rebuild; credible on 1.7.104 but not yet runtime-smoked. |
| DAV Extended 1.7.5 | `7751F52D588212CFE4D57EBA8C5D8B31D507BE7BE81753A5B4C23B892FA97080` | SKSE metadata admits the DLL | April 2026 build predates format 5. The current release is not a substitute. |

The distinction between "SKSE admits this DLL" and "its statically linked
CommonLib can parse Address Library format 5" matters. The former alone is not
a usable-runtime verdict.

## Candidate assessment

### FSMP 4.1.1

FSMP remains the correct current physics foundation. The installed 4.1.1 file
was published on 2026-08-26 and its GPL source is active at
[DaymareOn/hdtSMP64](https://github.com/DaymareOn/hdtSMP64). This does not make
unbounded crowd physics free: cloth collision, bone counts, actor count, and
distance all affect frametime. Keep FSMP distance activation and measure 1%
lows in cities and battles.

Worn cloak meshes do not require DynDOLOD. Actor LOD generally does not render
these accessories.

### More Scarves 1.4.0

More Scarves is the best first hooded-cape candidate because it is recent,
modest in scope, visually authored from scratch, and directly supports the
desired presentation stack:

- 12 items: eight scarves, one gaiter, and three hooded capes;
- 2K textures, matching the project's texture policy;
- FSMP on all but the gaiter;
- prebuilt and BodySlide support for vanilla female/male, CBBE 3BA, BHUNP,
  HIMBO, and OBody workflows;
- Khajiit and Argonian support;
- raised and lowered hooded-cape shapes in 1.4.0 for DAV/Helmet Toggle;
- Survival-related keywords, tanning-rack recipes, and an optional SkyPatcher
  vendor distribution file.

The author intentionally omits physics collision for performance. That
reduces cost but makes arm, shoulder, weapon, and armor clipping a known visual
tradeoff. The page also documents unstable first-person behavior in some
camera/animation scenes. Exact testing against the current first-person camera
stack is mandatory.

All pieces use slot 45; hooded capes also use hair and long-hair slots. A real
helmet or unsupported hairstyle therefore needs a fail-closed rule. The file
is CC BY-SA 4.0; redistributed derivatives require attribution, change notice,
and share-alike licensing.

### Bocksten Cloak 1.1

Bocksten is a convincing ordinary cloth cloak rather than a fantasy armor
piece. It has nine 2K colors, FSMP, weight sliders, male/female meshes, slot 46,
Survival keywords, inventory models, and linen/dye crafting recipes. It does
not contain a hood or a lowered state.

The Nexus permissions forbid uploading the file elsewhere and require author
permission to modify it, while allowing credited asset use. A public modpack
should fetch the original archive and distribute only an owned form/config
patch unless the author grants broader permission.

### Pelts 'o' Plenty 4.3.1

Pelts 'o' Plenty is a stronger modern cold-region candidate than immediately
falling back to Winter Is Coming. It was updated in January 2026 and provides
over 100 survival-compatible physics fur pieces for male and female actors,
including hoods, full/short/trimmed/heavy cloaks, and mantles. It is ESL-flagged
and has permissive credited-use instructions.

The breadth also creates risk:

- version 4.1 moved the pieces to slot 57, so Survival Control Panel's slot-46
  cloak logic cannot be assumed to recognize them;
- it requires a skeleton/FSMP visual route and a dedicated current-body audit;
- putting these physics pieces on a large share of a crowd could be expensive;
- the current archive is split between gear/resources plus the 4.3.2 female
  trimmed-wolf hotfix, so all three artifacts would be required.

Treat it as a regional/heavy-fur expansion after More Scarves and Bocksten are
proven, not as automatic global distribution.

### Cloaks of Skyrim / Winter Is Coming / Artesian

Cloaks of Skyrim still has unmatched faction and unique-cloak breadth, but its
base plugin/assets are from 2017. The current
[RMB SPCH patch](https://www.nexusmods.com/skyrimspecialedition/mods/116030)
1.5.3 replaces its invasive leveled-list path with ESP-FE/SkyPatcher-style
integration and warmth fixes. It is worth revisiting only if the user wants its
heraldry and named cloaks.

Winter Is Coming is similarly old but supplies recognizable fur cloaks and
hoods. Its current
[RMB SPCH patch](https://www.nexusmods.com/skyrimspecialedition/mods/116029)
1.4.6 modernizes distribution/warmth. It should compete directly with Pelts
'o' Plenty in a visual/performance audition rather than be installed by habit.

Artesian Cloaks can add HDT-SMP meshes to both legacy families. Its own page
warns that physics on every NPC cloak may cost substantial performance. Any
legacy family should use a bounded actor-density policy rather than universal
physics.

The May 2026 Cloaks of Skyrim HD SSE PBR package is not yet a baseline. Its
current integration reports around ParallaxGen and Artesian need resolution
before a stable pack should rely on it.

## Raised and lowered hoods: what the engine can do

Skyrim cannot deform a single hood mesh between raised and lowered states.
Every working implementation needs two prepared Armor Addon meshes:

- raised mesh: covers the head and normally hides hair/long-hair slots;
- lowered mesh: rests on the shoulders/back and restores the head/hair.

Dynamic Armor Variants changes the Armor Addon used to render an equipped
armor item. This is the correct mechanism for keeping the same inventory form,
enchantment, value, and warmth while changing only presentation. OAR/DAR can
play the equip or lowering gesture and gate it by state, but cannot perform the
mesh substitution by itself.

Papyrus equip/unequip or form swapping is a fallback, not the preferred player
implementation. It changes actual equipment, can flicker or fight outfit and
wig systems, can affect enchantment/warmth state, and must persist exactly what
was displaced. A manual raised/lowered pair is the safest no-native fallback,
but adds inventory clutter, is easy to forget, and gives no automatic NPC
behavior.

### Helmet Toggle 2 3.6.2

Helmet Toggle is the current maintained presentation layer. Its 2026-08-22
archive contains ESP/Papyrus sources, DAV configuration, KID/SPID/FLM rules,
OAR animations, IED presets, and optional MCM Helper integration. It supports:

- player, followers, and optional NPC management;
- rain, snow, cold region, season, combat, dialogue, and safe-location states;
- first-person equip/unequip animations;
- lowered More Scarves and Winter Is Coming hood models;
- supported wigs, Helm Hair, masks, visors, and current failure guards.

Its hard requirements not already in the profile are DAV and Offset Movement
Animation. Dynamic Lowered Hoods supplies the vanilla lowered mesh set. FLM,
KID, SPID, and IED are recommended but not all are hard runtime requirements.

Dynamic NPC Hairstyles can keep its dynamic hair while headgear is hidden, but
the Helmet Toggle author explicitly says lowered hood models do not work with
that system. Unsupported wigs and hairstyle systems therefore remain an
acceptance gate.

Start with player and followers only. Do not let Helmet Toggle and an NPC
weather injector manage the same actor or headgear form.

### DAV runtime choice

Official DAV 1.0.5 is MIT and remains the canonical configs/scripts/assets,
but its released DLL supports only the 1.6.629-1.6.659 family. The new
Juan-MZ compatibility package contains only a rebuilt DLL, retains the
original mod as a hard requirement, publishes full source under GPL-3.0+, and
ports the code to CommonLibSSE-NG with format-5 support. The DLL's version data
passes the current 1.7.104 loader gate.

The page advertises 1.7.99, not the later 1.7.104 hotfix. Because the DLL uses
Address Library IDs rather than a single executable whitelist, it is a
credible 1.7.104 candidate, but only a foreground launch and hook exercise can
prove it. The rollout must keep the upstream 1.0.5 vendor payload immutable and
place the GPL compatibility DLL in a separate overlay.

Dynamic Armor Variants Extended is a GPL fork with additional API and variant
features, but its April 2026 release predates the format-5 transition. It is not
the current binary answer. A future rebuild could be evaluated separately;
the project's low adoption and self-described AI-assisted changes warrant a
full code/test review first.

## Generic NPC weather systems

### Seasonal Clothing Framework 1.0.1

Seasonal Clothing Framework has the cleaner modpack-facing design:

- JSON presets select exact armor Editor IDs rather than broad inferred pools;
- rules cover weather, season, chance, everyone versus followers, and a
  shareable preset name;
- it only uses free slots, skips player/children/creatures/dead/disabled actors,
  and does not displace existing equipment;
- choices are deterministic per NPC;
- it serializes actor/item state through SKSE, resolves FormIDs on load, and
  tracks whether each copy was injected so it can remove only its own items;
- it performs no per-frame work; a sleeping worker schedules one bounded game-
  thread pass at the configured interval.

The exact 1.0.1 binary was built from the 2026-07-25 source state. Its pinned
CommonLibSSE-NG commit is from 2026-02-15. Format-5 support was not added to that
library until 2026-08-21, so the release cannot load against the current
Address Library even though its SKSE version metadata is permissive.

The repository has no license and the Nexus author instruction is "please ask
i probably wont say no." A public fork or redistributed rebuild therefore
requires permission/license clarification. The current rule schema also lacks
regional, faction, named-NPC, and explicit exclusion filters; an owned pack
would need those capabilities before broad use.

### WeatherBehaviorNG 2.5.1

WeatherBehaviorNG is more turnkey. It uses KID-tagged item pools and SPID
exclusions, adds/removes gear at runtime, supports rain/snow/seasonal/regional
profiles, stabilizes per-NPC selection, manages wigs, rejects unsafe body-slot
accessories, pauses around inventory-like menus, and exposes radius/cooldown/
density settings. Its FOMOD already includes a More Scarves KID patch.

However:

- file 750568 was compiled on 2026-05-10, before the format-5 runtime;
- the public repository has no license;
- the repository stops at commit `4d46c7b0a9b1095c447bb093b980e90aadf075cd`
  and documents approximately version 2.2, while Nexus ships 2.5.1;
- the exact 2.5.1 source, including later wig/seasonal/cleanup changes, is not
  available for source-to-binary review.

Nexus grants credited upload and modification permission, but the unlicensed,
lagging source makes a public code fork or custom binary an avoidable risk.
Wait for an author build/clarification or build a separately owned implementation
from requirements, not copied code.

Never run Seasonal Clothing Framework and WeatherBehaviorNG together on the
same actors. Both take ownership of runtime weather equipment.

## Survival, warmth, and wetness

Starfrost 2.0 standardizes base warmth by armor weight and recommends a cloak
value between 25 and 50. The proposed owned balance tiers are:

| Class | Warmth | Examples |
|---|---:|---|
| Thin | 25 | linen cape, short fashion cape, light scarf ensemble |
| Lined | 35 | full wool/cloth cloak, Bocksten-style ordinary winter cloak |
| Heavy | 50 | full fur expedition cloak, thick regional pelt cloak |

[Survival Control Panel](https://www.nexusmods.com/skyrimspecialedition/mods/41891)
1.1.2 is the Starfrost author's recommended mechanism. It can assign warmth to
slot-46 cloaks and expose the value in Survival UI. It is MIT-source, but the
published 2022 DLL only targets the old runtime family. It needs a separate
1.7.104 source port, static audit, and foreground smoke before use. Slot-45 More
Scarves and slot-57 Pelts 'o' Plenty also require explicit verification; do not
assume a slot-46 hook covers them.

Community Shaders Wetness Effects can make cloak materials look wet. It does
not make a wet cloak colder, add a wetness meter, or provide waterproofing. A
gameplay wetness system would be a separate survival feature with its own user
decision, compatibility matrix, and balance tests. Do not reintroduce the
heavy Wet and Cold runtime solely for gear behavior; its assets can be treated
separately if permissions allow.

## Distribution, crafting, and economy policy

Use owned SkyPatcher/KID/SPID configuration and an owned ESP-FE only where the
runtime patchers cannot express the needed semantics. Never edit or repack a
vendor plugin in place.

Initial distribution rules:

- ordinary linen/wool cloaks: clothing/general-goods vendors and a restrained
  share of civilian travelers;
- fur cloaks: cold holds, hunters, wilderness travelers, cold-region guards and
  patrols;
- faction heraldry: members of that faction only;
- unique cloaks: placed rewards, named NPCs, or quests—not generic vendor pools;
- beast races: only forms with proven race meshes;
- exclude children, prisoners, beggars/drunks where context requires it,
  mannequins, transformations, unsafe body-slot outfits, named/special NPCs
  without an explicit rule, and actors already wearing a conflicting item.

Start at 20-35% of generic nearby NPCs in bad weather and 40-60% of selected
cold-region guard/patrol cohorts. These are test values, not final promises.
Reduce density based on 1% low FPS and stuck-equipment results.

Crafting should remain material and regional:

- thin cloak: two or three linen/leather components plus ordinary dye;
- lined cloak: more linen/wool equivalent plus leather strips;
- heavy fur: appropriate pelt plus lining/leather;
- luxury colors: costly, plausible dyes.

More Scarves currently uses some extreme cotton/flower counts. Normalize those
recipes in an owned patch instead of accepting them unchanged.

Slot 45/46/57 accessories introduce an additional enchantment opportunity.
Generic cloaks should be non-enchantable by default to avoid free power creep.
Authored unique cloaks may remain enchantable if the user chooses that rule.

## IED, bodies, hair, first person, and clipping

Equipped cloaks are ordinary armor and render without IED. An IED rule for the
same slot/form can create a duplicate; disable it. Helmet Toggle's optional IED
feature is different: it shows the temporarily hidden helmet at the waist or
in the hand during animations. That cosmetic feature is currently unavailable
because IED is disabled.

Every selected mesh must be checked against:

- current HIMBO male and current female-body routes;
- vanilla body fallback and beast races;
- hair, long hair, wigs, circlets, masks, hoods, and hooded robes;
- heavy collars, pauldrons, backpacks, bandoliers, shields, quivers, swords,
  greatswords, and IED placements;
- standing/walking/running/sprinting, sneaking, sitting, riding, combat,
  killmoves, harvesting, crafting, dialogue, and ragdoll/death;
- first-person arms/camera and any improved-camera path.

Physics clipping cannot be eliminated generically. Collision-enabled cloth
costs more and still cannot understand arbitrary armor silhouettes. Prefer
well-shaped no-collision meshes, sensible actor density, and documented visual
exceptions over pretending a universal mesh patch exists.

## Save and performance safety

The final system must prove all of these on a disposable existing save and a
new game:

- save during rain with injected/equipped gear, reload, clear the weather, and
  confirm only injected copies disappear;
- fast travel, interior/exterior transition, cell unload/reload, follower
  dismissal/recruitment, actor death, resurrection, transformation, and combat;
- enable/disable the weather framework in its UI and verify delayed actors are
  cleaned when they next load;
- remove a source armor plugin from a disposable profile and verify unresolved
  serialized FormIDs are ignored safely;
- 20-minute Whiterun, Solitude, and Riften routes plus a dense battle while
  recording average FPS, 1% low, papyrus backlog, FSMP/native logs, and stuck
  items;
- rollback the entire cloak layer and confirm the previous profile and save
  remain usable.

Prefer FSMP distance activation and avoid collision-rich physics on every NPC.
No launch was performed during this research.

## Publication and permissions

| Component | Publication posture |
|---|---|
| FSMP | GPL source; include license/notices if redistributing any built derivative. Prefer Nexus fetch for the vendor runtime. |
| More Scarves | CC BY-SA 4.0; patches/assets may be redistributed with attribution, change notice, and compatible share-alike licensing. |
| Bocksten Cloak | Fetch original. Do not upload or modify vendor files without permission; owned form/config patches may reference it. |
| Pelts 'o' Plenty | Credited use is broadly allowed, but preserve credits for every upstream asset contributor. Prefer original fetch. |
| Helmet Toggle 2 | Credited patches/asset use are allowed, but its borrowed animations belong to TheCyclist; do not assume those animations can be independently repackaged. |
| Official DAV | MIT source. Preserve copyright/license. |
| DAV 1.7.99 compatibility patch | GPL-3.0+ source and notices. Keep as a separate overlay over the immutable official vendor payload. |
| Seasonal Clothing Framework | Public source has no license; Nexus says to ask. Do not fork/rebuild for public distribution without clarification. |
| WeatherBehaviorNG | Nexus permits credited modifications, but GitHub source is unlicensed and behind the binary. Do not present a fork as cleanly open source without author clarification. |
| Survival Control Panel | MIT source; a current port is legally feasible, but still requires engineering and runtime validation. |

A public collection/installer should fetch restricted original archives and
ship only owned ESP-FE/config/source-compatible overlays. Nothing in this
research authorizes redistributing vendor assets.

## Acceptance checklist

- [ ] User chooses the asset breadth and automatic-hood scope.
- [ ] Every approved archive/FOMOD selection is recorded with exact file ID,
      hash, dependency, and rollback transaction.
- [ ] Every installed Nexus page becomes Keep only after successful install;
      research-only candidates remain unclassified.
- [ ] DAV compatibility overlay reaches the main menu on 1.7.104 without a
      popup and produces a clean load/hook log.
- [ ] Helmet Toggle raises/lowers the selected hooded capes in rain, snow,
      clear weather, interiors, cold regions, combat, dialogue, first person,
      third person, and across save/load.
- [ ] A real helmet or incompatible wig blocks the hood safely; no bald,
      invisible-head, stripped-body, or duplicated-equipment state occurs.
- [ ] Mesh-only hood changes preserve warmth, enchantments, value, and the
      inventory item.
- [ ] NPC framework, if later adopted, cleans injected items across every save,
      load, unload, clear-weather, death, and disable route.
- [ ] No duplicate IED/equipped-cloak rendering.
- [ ] Warmth tiers read exactly as 25/35/50 under Starfrost, including explicit
      handling for slot 45 and slot 57.
- [ ] Body, beast-race, armor, weapon, backpack, quiver, animation, and
      first-person visual routes pass.
- [ ] Dense-city and battle 1% lows remain within the accepted budget and logs
      contain no native error or papyrus backlog.
- [ ] New-game, existing-save, and rollback tests pass.
- [ ] Publication manifest contains only licensed owned outputs and points to
      original downloads for restricted vendor content.

## Decisions still needed

1. More Scarves + Bocksten only, or add Pelts 'o' Plenty and/or legacy
   faction families?
2. Automatic hood scope: player only, player plus followers, or generic NPCs
   after a runtime-safe framework exists?
3. Keep generic cloaks non-enchantable, or accept the extra enchant slot?
4. Authorize a 1.7.104 Survival Control Panel port after candidate selection?
5. If no author-updated NPC framework arrives, request permission to port
   Seasonal Clothing Framework or commission a clean owned implementation?
6. Approve the proposed 25/35/50 warmth tiers and starting NPC density?

No candidate has been installed or curated. These are explicit future gates.
