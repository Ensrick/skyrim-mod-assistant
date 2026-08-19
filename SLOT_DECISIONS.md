# Slot decisions - mutually exclusive candidates

Generated 2026-08-19 from the live curator database (2,200 keeps, 1,135 skips, 11 trims).

**How this was built.** A regex pass over mod names assigns each keep to a functional slot
(recall-oriented, name only - matching on summaries put Xtudo armor sets into `needs-survival`
because they mention "Warm keyword for the Survival mod"). A second pass separates roles:
*rivals* compete for the slot, *attached* mods follow whichever rival wins, *utilities* make the
slot work regardless of winner. Role separation is judgment, not regex. Scripts live in the
session scratchpad (`classify_slots2.py`); this file is the curated layer on top.

**Decision rule.** Pick one rival per slot. Everything in "attached" survives or dies with your
pick, so it needs no separate decision. Nothing here is auto-skipped: losers get marked only
after you choose.

---

## Tier 1 - gates the rest of the build

### Renderer: settled
Community Shaders 1.8.3. Sky Sync, Light Limit Fix, grass lighting/collision, SSS, water effects,
cloud shadows and terrain shadows all ship in core; only Skylighting, SSGI, Wetness Effects,
Terrain Blending, Terrain Variation, Hair Specular and Upscaling remain separate downloads.

### Weather (9 rivals)
| ID | Mod | Endorse | Updated |
|---|---|---|---|
| 2187 | Vivid Weathers Definitive Edition | 106,756 | |
| 12125 | Obsidian Weathers and Seasons | 62,756 | |
| 24791 | Cathedral Weathers and Seasons | 46,313 | |
| 2237 | Climates of Tamriel SE | 34,668 | |
| 7895 | Dolomite Weathers (NLVA II) | 12,926 | |
| 42731 | Azurite Weathers and Seasons | 11,747 | |
| 11578 | Mythical Ages | 7,665 | |
| 63116 | RAID Weathers | 3,215 | |
| 58782 | Weather of World | 2,544 | |

Attached: Cathedral Weathers MCM (24940), Darker Nights for Obsidian (15137), Dolomite
Precipitation (8006), Azurite Mists (106559). Additive regardless of winner: True Storms (2472,
thunder/rain layer with patches for most weather mods), Obsidian Mountain Fogs (13539), Wonders
of Weather (13044).

Deciding factor: whether the weather mod ships Community Shaders-aware interiors and how its
night brightness reads without ENB. Cathedral and Azurite are the two built for the CS era.

### Interior lighting (5 rivals)
| ID | Mod | Endorse |
|---|---|---|
| 2424 | Enhanced Lights and FX | 139,018 |
| 844 | Realistic Lighting Overhaul SSE | 61,284 |
| 43158 | Lux | 31,189 |
| 8586 | Relighting Skyrim SE | 21,777 |
| 16830 | Luminosity Lighting Overhaul | 12,657 |

Attached: ELFX Shadows (63790) and ELFX Enhancer (16618) require ELFX; Lux Via (63588), Lux Orbis
(56095) and Lux CS (153919) are Lux family companions, not competitors - Lux CS specifically
targets Community Shaders.

This is the single most patch-heavy slot in the game. Whichever wins dictates city-overhaul
patches downstream, so it should be decided before the city stack.

### Body and skeleton
- **Skeleton (3):** XPMSSE (1988), Skeleton Replacer HD (52845), Maximum Skeletons D-Won (75307).
  Five attached XPMSSE script/patch mods follow XPMSSE.
- **Female body (2 base):** CBBE 3BA (30174), CBBE SMP (29023). The other 30 matches in this slot
  are armor conversions that consume the body rather than compete with it.
- **Male body:** HIMBO refits dominate the keep list, which implies HIMBO.

### Animation framework: settled
Pandora Behaviour Engine Plus (133232). FNIS and Nemesis are not in the keep list.

### Combat framework (2 rivals, then movesets follow)
MCO Universal Support (85491) vs BFCO Universal Support (120091). The eight ADXP/MCO/BFCO moveset
packs in the keep list attach to whichever framework wins - several support both.

---

## Tier 2 - visual stack

### Grass (5 rivals)
Verdant (2296), Folkvangr (44899), Veydosebrom Regions (26293), Northern Grass (25459), Origins Of
Forest (45719).
Utilities that stay regardless: Landscape Fixes For Grass Mods (9005), No Grass In Objects (42161),
Grass FPS Booster (20082), No grass in caves (12431).

### Trees and flora (6 rivals)
Skyrim Flora Overhaul (2154), Skyrim 3D Trees and Plants (12371), Happy Little Trees (50961),
Nature of the Wild Lands (63604), Enhanced Landscapes (18162), Sprigganlands (187865).

### Landscape textures (14 rivals)
Majestic Mountains (11052), Skyland Landscape (3820), Cathedral Landscapes (21954), Skyrim 3D
Landscapes (18247), Vivid Landscapes (5488), Real Mountains (3704), Tamrielic Textures (32973),
Septentrional (29842), Northern Shores (27041), Skyking Fantasia (107256), Gecko's 4K Mountains
(1799), RUSTIC MOUNTAINS (4896), Majestic Landscapes (41857), aMidianBorn Buildings and Landscapes
(38019).
Not rivals: Terrain LOD redone (9135) and xLODGen Resource (54680) are LOD-side; Terrain Variation
and Terrain Blending are Community Shaders features; Majestic Mountains Complex Material (87547)
attaches to Majestic Mountains.

### Architecture textures - bundle vs modules
Skyland AIO (34179, updated 2026-08-18) against the individual Skyland modules you also kept:
Skyland Whiterun (13015), Skyland Imperial Forts and Dungeons (16354), Skyland Nordic Ruins
(19116), Skyland Solitude (24252). The AIO contains these; the only reason to keep modules is if
you want another author's textures for specific areas.

### Water (4 rivals)
Realistic Water Two (2182), Cathedral Water Overhaul (22962), Simplicity of Sea (56520), A Water
Made For CS (172959). Better Water (28221) attaches to RWT.
Note: the last two are the Community Shaders-era entries.

### Cities (per city, 4 families + standalones)
JK's family is 30+ modules covering individual buildings, so it counts as one decision that then
resolves per city. Rivals per city: JK's, The Great City of X, The Great Town of X, Dawn of
Skyrim, plus standalone overhauls. This slot is best decided city by city after lighting.

---

## Tier 3 - gameplay systems

### Survival needs (5 rivals)
Survival Mode Improved - SKSE (78244), SunHelm (39414), iNeed Continued (19390), Realistic Needs
and Diseases AIO (3487), plus Last Seed and Starfrost from the earlier teardown.
Campfire (667) and Frostfall are additive layers, not rivals.
Prior analysis in `SURVIVAL_COMPARISON.md` recommends SMI-SKSE + Starfrost + KID + Campfire.

### Perks (5 rivals)
Ordinator (1137), Adamant (30191), Vokrii (26176), Ascension (89223), Vokriinator Choice Cuts
(26702, a merge of Ordinator+Vokrii+Adamant). Path of Sorcery (6660) is magic-perk-only and can
coexist with a non-magic perk overhaul.

### Magic (2 true rivals)
Odin (46000) vs Mysticism (27839). Apocalypse (1090) and Triumvirate (39170) are additive spell
packs that patch against either. Spell Research (20983) is a discovery system, orthogonal.

### Combat feel (4 rivals)
Wildcat (1368), Smilodon (2824, the same author's lighter alternative), Valhalla Combat (64741),
Blade and Blunt (34549). Mortal Enemies (4881) and Bow Rapid Combo (89308) are additive.

### Alternate start (3 rivals)
Live Another Life (272), Realm of Lorkhan (18223), Skyrim Unbound Reborn (27962). New Beginnings
(4939) is a LAL extension.

### Camera (4 rivals)
SmoothCam (41252), Improved Camera SE (93962), 3PCO (18515), Customizable Camera (12201).
Alternate Conversation Camera (21220) and its Improved variant (68210) are a separate pair.

### Followers, crafting, sound, enemies
- Follower framework: AFT (6656) vs iAFT (14722), the latter a maintained fork.
- Crafting: Ars Metallica (321) vs Complete Crafting Overhaul Remastered (28608).
- Sound: Immersive Sounds Compendium (523) vs Audio Overhaul for Skyrim (12466). A compatibility
  patch exists, so this can be a both-with-patch rather than either-or. Lucidity (1841) is additive.
- Enemies: Skyrim Revamped (14598) vs High Level Enemies (3231). Lawless (88080) is bandit-only.

### College of Winterhold (4 rivals)
Immersive College of Winterhold (17004), Magical College of Winterhold (1539), Obscure's College
of Winterhold (20514), JK's College of Winterhold (65676). Quest Expansion (66666) and Praedy's
College (46334) are additive against most of them.

### UI
SkyUI (12604) is the framework, not a rival. Skin rivals: NORDIC UI (49881), Dear Diary (23010),
Dear Diary Dark Mode (60837), Untarnished UI (75188). SkyHUD (463) is HUD layout and pairs with
any of them. moreHUD (12688) + moreHUD Inventory (18619) are one family; iHUD (12440) is separate.

### Horses (two sub-slots)
Feature mods: Convenient Horses (9519), Immersive Horses (13402), Simplest Horses (54225), Simple
Horse (12650). Visual: HD Reworked Horses (28249) vs Realistic Horse Breeds (7685).

### Killmoves
VioLens (668), Kaputt (78063), Heart Breaker (1847), Maximum Carnage (43494), Dismembering
Framework (126203). You already decided VioLens + Kaputt together; the other three need checking
against that pair rather than against each other.

---

## Resolved during this pass

| Mod | Verdict | Evidence |
|---|---|---|
| 6532 Skyrim Unbound | skip | Author: "no longer under active development... check out Skyrim Unbound Reborn" |
| 8889 Skyrim Skill Uncapper | skip | v1.1.0 from 2017, SE-only; 82558 supports 1.6.317+ |

## Coverage and gaps

372 of 2,200 keeps landed in a slot; the other 1,828 are additive (armor sets, standalone
retextures, patches, quests, player homes, utilities) and need no exclusivity decision.

Known recall gaps: mods whose names don't carry the slot keyword are missed, and NPC visual
overhauls (Pandorable, Bijin and the like) conflict per-NPC rather than per-slot, which name
matching can't model. Those need file-level overlap analysis instead - index each archive's
`meshes/actors/character/facegendata` paths and compare.
