# tarlazo Catalog Review - Keep / Skip / Conditional

Reviewed **2026-08-14** against `INVENTORY.md` (27-mod baseline, Skyrim SE 1.6.1170, **no USSEP installed**).
Source: Nexus GraphQL API, uploader `tarlazo`: 144 mods listed, 124 visible (116 Skyrim SE + 8 Oblivion; ~20 hidden/unlisted).
Download/endorsement counts are API data; verdicts are suggestions. Claims about other-mod overlap marked [unverified] where not confirmed.

**Author profile:** almost everything is a surgical, ESL-flagged (ESP-FE) script/placement fix or micro-immersion tweak. Actively publishing (3 new mods in Aug 2026). Because your list deliberately has **no USSEP**, his standalone fixes are a natural fit: they patch individual annoyances without a 60k-record master.

## TL;DR shortlist (my picks for your list)

Strong adds (bug/script fixes, near-zero risk): **Navigator**, **dunPOISoldiersRaidOnStart Script Tweak**, **Dwemer Gates Don't Reset**, **TrapSwingingWall Script Fix**, **Source of Stalhrim Quest Fix**, **Teldryn Serious Patch**, **Standing Ambusher Fix**, **The Clever Prisoner**, **DLC2 March of the Dead Fix**, **Vampire Allies Factions Fix**, **Irkngthand's Possible Bugs Fix**, **Disintegrate Perk Fix**, **Here We Go Again - World Interactions**, **Reset Random Dialogue Scenes**.
QoL worth a look: **Convenient Carriages**, **State Your Claw**, **Courier Notification** (SKSE, you have the stack), **Rent Room Dialogue Tweak**, **Good Dog**.

## 1. Bug / script fixes - recommend by default

| Mod | ID | DL | Note |
|---|---|---|---|
| Navigator - Navmesh Fixes | 52641 | 3.7M | His flagship. Navmesh-only fixes. Caveat: navmesh edits conflict with city/settlement overhauls editing the same cells; you run none today, so clean. |
| dunPOISoldiersRaidOnStart Script Tweak | 62925 | 1.7M | Stops a vanilla POI quest script misbehaving. |
| Dwemer Gates Don't Reset | 26331 | 1.7M | Dwemer shortcut gates stay open across cell resets. |
| Source of Stalhrim Quest Fix | 32329 | 1.2M | Un-sticks "A New Source of Stalhrim". |
| TrapSwingingWall Script Fix | 61978 | 992k | Kills spike-wall trap scripts that stay active forever. |
| Teldryn Serious Patch | 32415 | 925k | Collision markers so NPCs don't fall off the DB boat battle. |
| The Clever Prisoner | 84348 | 606k | Fixes dumb prisoner AI in WE09/WE31 encounters. |
| Standing Ambusher Fix | 74492 | 558k | Fixes ambush draugr standing outside sarcophagi. |
| Halldir's Cairn CTD Fix | 29149 | 402k | FaceGen files only, no plugin. Only needed if you actually CTD there; zero-cost insurance. |
| DLC2 March of the Dead Fix | 53336 | 388k | Carius' note can't be lost to despawning ash. |
| Irkngthand's Possible Bugs Fix | 62841 | 158k | Mercer-missing + water script failsafes. |
| Reset Random Dialogue Scenes | 34961 | 114k | Re-arms one-shot city conversation scenes. |
| Here We Go Again - World Interactions | 37207 | 88k | Makes one-time world-interaction quests repeatable. Possible overlap with USSEP fixes [unverified], but you have no USSEP, so moot. |
| Vampire Allies Factions Fix | 67995 | 89k | Faction patch so vampire allies coexist. |
| Trespass | 36842 | 43k | Fort-soldier trespass aggression fix. |
| Disintegrate Perk Fix | 180591 | 0.6k | New (2026); fixes double remains from Disintegrate. |
| Ultimate Mannequin Fix and Overhaul | 61851 | 21k | Only matters once you use player homes with mannequins. |
| Standing items: Animated Static Reload Fix etc. | - | - | Already covered in your inventory; no overlap with the above. |

## 2. QoL / convenience - taste, but high quality

| Mod | ID | DL | Note |
|---|---|---|---|
| Convenient Carriages | 12693 | 739k | His flagship QoL mod: 26 destinations, driver AI. The alternative ecosystem pick is CFTO; pick one, not both. Supersedes his own "Followers Sit on Carriages". |
| State Your Claw | 65150 | 249k | Puzzle door tells you which claw it needs. |
| Courier Notification | 91678 | 123k | On-screen name of what the courier gave you. Requires SKSE (you have it). |
| Rent Room Dialogue Tweak | 34470 | 114k | Auto-closes dialogue after renting a room. |
| Fugitive Piss Off | 30215 | 185k | Stops the Fugitive WE interrupting combat. |
| Horses Follow Through Doors | 68338 | 95k | Horse follows into load-door areas (Dayspring Canyon). |
| Arniel's Quest Speed-up | 30518 | 49k | Skips find-the-courier stage if you have Keening. |
| Don't Push Me Around | 52874 | 48k | NPC push-around mitigation. |
| Gift from a Friend | 53812 | 26k | Friend gifts without force-greet. |
| Thieves Guild's Automatic Secret Passage | 92181 | 21k | Faction-gated auto door in the graveyard. |
| Mr. Ebony... Get Lost | 52510 | 370k | Skip or play the Ebony Warrior. |
| No Nagging in Taverns | 64490 | 2k | Disables "You want a drink?" pestering. |
| No More Friendly Fire Complaints | 25576 | 4.4k | Silences follower friendly-fire barks. |
| For the Love of Talos | 67962 | 1.3k | Heimskr, quieter. |
| Relaxed Vendors | 30509 | 2.4k | Less frequent street-vendor calls, MCM version. |

## 3. Immersion micro-tweaks - pure taste, all tiny ESP-FE

High-download flavor: **Good Dog** (711k, bark reduction), **The Stumbling Sabrecat** (610k), **burn Burn BURN** (649k), **Welcome Back to the Bee and Barb** (467k), **The Last Journey** (400k), **Taarie's Dialogue Fix** (391k), **Respect for the Arch-Mage** (371k), **The Last Swim** (234k), **Bury Sinderion** (233k), **Food for the Thirsty** (226k), **Goldenglow Is Yours** (210k), **Niyya's New Clothes** (209k).

Alt-quest content: **Muiri's Revenge** (116k, Mourning Never Comes without DB), **Innocence Lost Alternative** (25k, destroy-DB-friendly), **Riftweald is MINE**, **R.I.P. Mercer Frey**.

Long tail (browse if the theme appeals): Vigilants Pursuing Vampire, Thieves, Headie Rides Again, Who Killed the Dragon, Relaxed Khajiits, Serana and Valerica Sandbox, Misty and Florian, Just Married, Bassianus, Fjona the Bard, Ange the Wanderer, Thief of Sweetrolls, Befriend Those Poor Draugrs, Sluggish Undeads, The Kjenstag Ruins, Odahviing's Casualty, The Lonely Horse, Guard Distributor, Block or Lock Doors and Gates, Big Bad Bug (MCM insect/fish resizing), Bugs, Breezehome Stability, Glowing Alendriel's Ring, Faldenthz (small Dwemer dungeon, ESM), Just My Imagination (sneak-detection overhaul: gameplay changer, not a fix), Scroll Up (power fantasy), Heavy and Light Armor Perks Tweak, Dastardly Invisible Traps (difficulty), Pinky Biggy and Wobbly (joke mod).

## 4. Post-Civil War set - only if you finish the CW questline

| Mod | ID | DL |
|---|---|---|
| After the Civil War - Siege Damage Repairs | 20668 | 3.5M |
| Military Camps Begone | 68520 | 475k |
| No Siege Barricades Leftovers | 182331 | 0.3k |
| Excuse Me | 67219 | 265k |
| Respect for the Legate | 30185 | 1.1M (Imperial path flavor) |

These are his second-most-downloaded cluster and the community standard for post-war cleanup. Zero value until a playthrough actually ends the war.

**Alternatives on SE (checked 2026-08-14):** only one real competitor exists: **Immersive Civil War Cleanup - SSE** (153928, 1.3k dl, port of telamont's LE mod) - talk to Tullius/Ulfric after the questline and the battle damage is tidied up on request, no repair-crew simulation. The LE-era options (Civil War Repairs = Solitude/Windhelm Repaired + Whiterun Repaired Plus; Steam Workshop "Civil War Cleanup") have no SE ports on Nexus. tarlazo's set is the SE standard by ~2500x downloads and has an Extended Repair Times addon (85667). Adjacent but not siege repair: Kynareth Replaces Talos - Civil War Consequence (91440); Siberpunk's Environs series (world-heals-over-time for non-CW damage, pairs thematically).

## 5. Conditional - only with the named mod installed (you currently run NONE of these hosts)

| Patch | Host mod required |
|---|---|
| Bruma and Other Patches for Convenient Horses (13812, 585k) | Convenient Horses + Beyond Skyrim: Bruma etc. |
| Convenient Horses Follower Tweaks (57908) | Convenient Horses |
| Better Dynamic Snow in New Lands (22741) | Better Dynamic Snow + Wyrmstooth/Falskaar/etc. |
| A Few Water Edge Fixes (60370) | new-land mods |
| BS-Bruma Ugly Love Script Fix (52506) | Beyond Skyrim: Bruma |
| The Mad Shaman (62624) | Beyond Reach |
| Falskaar Runaway Cattle Fix (66181) | Falskaar |
| Moon and Star - Moss Creek Camp (90145) | Moon and Star |
| The Hanging Gardens - Convenient Boat (36289) | The Hanging Gardens |
| Lord Hammet's Armor (57257) | Hammet's Dungeon Packs |
| Ahbiilok - Duathand-Zel Quest Markers (86332) | Ahbiilok |
| Four Skull Lookout with iNPCs (59255) | Interesting NPCs |
| Purewater RUN (57784) | vanilla or iNPCs versions |
| SkyTEST Riften Puppies / Chicks / Rabbits (30334/37739/36093) | SkyTEST |
| Plump Cathedral 3D Plants (75312) | Cathedral 3D plant mods |

## 6. Visual / audio environment - taste; superseded if you ever add overhauls

| Mod | ID | DL | Superseded by |
|---|---|---|---|
| Dead Shrubs Replacer | 33842 | 274k | any flora/landscape overhaul |
| Reduced Fire-Candle-Torch Glow | 28596 | 198k | Embers XD or a lighting overhaul |
| No More Bloom and HDR Redux | 60001 | 22k | ENB / Community Shaders post-processing |
| No Exterior Mists | 58807 | 1.3k | weather overhauls handle mist their own way |
| The Dragon Bridge | 63858 | 158k | standalone repave, fine alone |
| Snowy Boethiah / Snowy Reach Trees / Reach Trees Placement Fix | 59663/61695/24563 | 127k/52k/2.7k | fine alone |
| Rumble Crumble (30565), Much More Quiet Draugr Shouts (30176), Break the Wind (60640), Quiet in Riften (68304) | - | small | audio-taste, fine alone |
| Cool Beds | 33799 | 1.9k | any bedding retexture |

## 7. Skip

- **Followers Sit on Carriages** (166738): explicitly the standalone offshoot for people NOT running Convenient Carriages; redundant if you take CC.
- **Dynamic Bards** (77410): requires USSEP, which you don't run.
- **Tenuous Nirnroots** (33598): its purpose is reverting a USSEP change; meaningless without USSEP.
- **DefaultActivateSelf Tweak** (90955): author's own summary says "only for complete noobs".
- **8 Oblivion mods** (Shadowbanish Quest Markers, Find the Trainers, Populated Priory of the Nine, etc.): wrong game.

## Interactions with your current 27-mod inventory

- **No conflicts spotted**: nothing in your inventory (frameworks, crash fixes, SMP, retextures, Alternate Perspective) touches the records these fixes edit, with one watch item: Navigator's navmesh edits vs. Alternate Perspective's world edits [unverified - check on install; LOOT will flag if a patch exists].
- His newer mods lean on frameworks you already have (BOS, SkyPatcher, SKSE), so no new dependency tree.
- Everything ESP-FE = zero load-order slots consumed.
