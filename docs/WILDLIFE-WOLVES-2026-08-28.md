# Wolf spawning and wildlife design — 2026-08-28

Tracker: [GitHub issue #42](https://github.com/Ensrick/skyrim-mod-assistant/issues/42)

## Vanilla record audit

The installed `Skyrim.esm` does not make ordinary wolves disappear at a high
player level.

`LCharWolf` (`0B83C2`) contains three level-1 entries: ordinary wolf, red wolf,
and another ordinary-wolf weighting entry. Its flags are
`CalculateFromAllLevelsLessThanOrEqualPlayer` and
`CalculateForEachItemInCount`, with zero chance of no spawn. Once the list is
eligible, a high-level player still qualifies for all three level-1 entries.

The special lists are similarly persistent:

| Leveled list | Entries | Consequence |
|---|---|---|
| `LCharWolf` (`0B83C2`) | Wolf level 1, red wolf level 1, wolf level 1 | Ordinary wilderness wolf lists remain eligible at every higher level. |
| `DunCragslaneLCharPitWolf` (`0E160C`) | Wolf level 1, ice wolf level 5; calculate from all lower levels | Ordinary wolves remain in the pool after ice wolves become eligible. |
| `DunDarkshadeCopseLCharWolf` (`023BC0`) | Wolf level 1 | This dungeon list always resolves to the ordinary wolf. |

This answers only vanilla list behavior. A placed reference can still fail to
return if its reference/base does not respawn or its encounter zone never
resets. By default, uncleared cells reset after 10 in-game days and cleared
cells after 30; creatures normally respawn when the cell resets. Encounter-zone
level itself remains locked after first visit.

The same audit must be repeated against Bruma, Wyrmstooth, Beyond Reach, and
every other adopted worldspace. Their authors can use different fixed actors,
leveled lists, scripts, factions, or no-respawn references.

## Behavior audit

Vanilla ordinary wolf (`EncWolf`) and red wolf (`EncWolfRed`) records are level
2, respawning, auto-calculated, and marked `Unaggressive`; ice wolf is level 6
and `VeryAggressive`. Ordinary bears are also marked `Unaggressive`. Both
families share Creature, Predator, and Spriggan Predator factions, but each has
its own species faction.

Therefore, making wolves "behave like bears" is not safely solved by changing
one aggression enum. Detection distance, warning/combat behavior, faction
relationships, encounter placement, and any race/behavior data must be tested.
At minimum, ice-wolf aggression is a concrete difference; ordinary wolves need
an in-game approach/retreat test before changing records that already claim to
be unaggressive.

## Preferred implementation

Create a load-order-aware generated compatibility patch instead of adopting a
broad animal overhaul:

1. Discover wolf actors, races, and leveled lists by explicit form links plus a
   reviewed include/exclude manifest—not editor-ID substring alone.
2. Preserve quest, summoned, spirit, dead, companion, scripted, and unique
   wolves unless deliberately approved.
3. Normalize only the selected wildlife actors' aggression/faction behavior and
   preserve each worldspace mod's visuals, stats, placement, and scripts.
4. Keep wolves in their existing leveled lists; do not replace the wildlife
   population with a single global list.
5. Test warning distance, pack assistance, flee/return behavior, follower and
   summon interactions, hunting, cell reset, and save/reload in every adopted
   worldspace.

The hostile-population deficit should be solved separately through issue #43's
selective humanoid/undead spawning. Wolves should not remain routine enemies
merely to keep the wilderness combat count high.

---

# Appendix - 2026-09-02: visuals, behaviour numbers, and the spawn arithmetic

Audit-only pass answering the four requirements the user added to
[#42](https://github.com/Ensrick/skyrim-mod-assistant/issues/42) on 2026-09-02.
Nothing installed, no profile file touched, no launch. Everything below is
measured from `Skyrim.esm`, from the installed load order, or from mod archives
downloaded to the MO2 download cache and extracted to a scratch directory.

Method: plugin records read with
`skyrim-tools-builds\skyrim-record-cli-1f3c8d9\skyrim-record-cli.exe` and with a
raw subrecord walker (ACHR NAME/DATA, NPC_ AIDT/TPLT/SNAM, FACT XNAM, LVLN
LVLO/LVLF); assets with `audit/inspect_mod.py`, `audit/mip_retention.py` and
`audit/modasset.py`; DDS baselines extracted from `Skyrim - Textures1.bsa`.

## 1. Visuals - the wolf that does not read as a monster

### The field, with confirmed Nexus ids

Every id below was confirmed against
`GET /v1/games/skyrimspecialedition/mods/{id}.json`.

| id | mod | version | last updated | endorsements | what it is |
|---|---|---|---|---|---|
| 182994 | [Canidae - A Wolf Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/182994) | 2.25 | 2026-08-29 | 819 | new wolf **mesh + textures**, wolf-only |
| 56361 | [Fluffworks (Fluffy Animals)](https://www.nexusmods.com/skyrimspecialedition/mods/56361) | 1.0 (file 1.1f) | 2022-03-02 | 11,396 | fur **shells** over the vanilla animal meshes |
| 88138 | [Fluffworks - Tweaks and Expansion](https://www.nexusmods.com/skyrimspecialedition/mods/88138) | 4.6 | 2026-06-09 | 1,613 | Fluffworks addon |
| 64445 | [Fluffworks - Auto Patches](https://www.nexusmods.com/skyrimspecialedition/mods/64445) | 2.3 | 2026-06-29 | 4,735 | Fluffworks patch hub |
| 184334 | [Canidae - Fluff AF Patch](https://www.nexusmods.com/skyrimspecialedition/mods/184334) | 1 | 2026-08-04 | 171 | Canidae meshes with Fluffworks shells |
| 68069 | [Wolves of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/68069) | 2.1 | 2026-01-11 | 4,784 | mesh + texture replacer |
| 63378 | [Real Fur for Wolves](https://www.nexusmods.com/skyrimspecialedition/mods/63378) | 1.1 | 2022-02-17 | 1,068 | remesh/retexture |
| 21075 | [Savage Wolves](https://www.nexusmods.com/skyrimspecialedition/mods/21075) | 1.7 | 2020-05-30 | 4,215 | **replaces the wolf skeleton** |
| 73400 | [Pelage](https://www.nexusmods.com/skyrimspecialedition/mods/73400) | 1.0 | 2023-03-23 | 598 | Fluffworks-style shells for non-vanilla creatures |
| 6824 / 13241 | [Better Skyrim Wolves](https://www.nexusmods.com/skyrimspecialedition/mods/6824) / [SSE Wolves Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/13241) | 1.1 | 2017 | - | LE-era, superseded |

None of these carries a curator decision today
(`nexus-local-curator/scripts/curator_state.py`: all eleven report "no
decision"), and no creature texture or mesh mod is installed - the wolf visual
slot is empty.

### What FluffWorks actually does to a wolf

The user named FluffWorks as the shape of the answer. Measured, it is **not** a
new wolf; it is the vanilla wolf with fur added:

- `meshes/actors/canine/character assets wolf/wolf.nif` - vanilla has 2
  `BSTriShape` shapes, Fluffworks has **18**. The 16 extra shapes are the
  shell-texturing layers. Same bone list, same silhouette, same head.
- Fluffworks ships **no wolf diffuse at all** - only `wolf_shell.dds`,
  `wolfblack_shell.dds`, `wolfred_shell.dds`. The base skin stays vanilla
  `textures/actors/wolf/wolf.dds`.
- 27 of 27 Fluffworks textures ship with no normal map; 4 show JPEG blocking
  (`textures/actors/fox/fox_shell.dds`, grid ratio 1.43).

So Fluffworks fixes "mangy" and does not fix "monster". The vanilla wolf head,
proportions and pose - which is what reads as a monster - survive it intact. It
is also, by the author's own compatibility note, incompatible with wolf
retextures that are not vanilla upscales.

### Canidae 2.25 measured

`py -3 audit/inspect_mod.py "182994:Canidae"` on the 144.5 MB FOMOD
(`Canidae - A Wolf Replacer 182994 2.25 2026-08-29T21-48Z kATsMWwgS.rar`):

- 190 `.nif`, 40 `.dds`, 7 ESP-FE plugins, all of the plugins optional.
- **The core "Wolf Replacer" option is meshes and textures only - no plugin.**
  It writes 12 mesh files: the four wolf actor NIFs, the wolf `skeleton.nif`,
  two BYOH trophies, two BYOH interior mounts, two wall mounts and the wolf load
  screen. Every plugin (Red Wolf Leveled List Addon, Pelt Replacer, and the DAV
  / Immersive Creatures / A Dog's Life / Embers XD / Enderal patches) is a
  separate FOMOD checkbox.
- The new wolf mesh is real work: 8 `BSTriShape` shapes with
  `BSDismemberSkinInstance` and 8 texture sets, against vanilla's 2 shapes and 1
  texture set. Dismemberment data means it is ready for a gore framework.
- `skeleton.nif` **is** overwritten, but it is not a bone change: identical byte
  length (29,086), identical block histogram (53 `NiNode`, 22
  `bhkCapsuleShape`, 22 `bhkRigidBody`, 9 ragdoll + 12 hinge constraints) and an
  **identical bone-name string table** versus the vanilla file. The bytes differ
  only in transform data - a scale/pose edit. No bone is added or removed, so
  Pandora/OAR creature behaviour (which keys off `.hkx`, not this NIF) is
  unaffected. It does still claim the file, so it would conflict with any
  creature-skeleton replacer - Skeleton Replacer HD is the one already tracked
  in `BASELINE.md`.

**Distance test** (`docs/CURATION_POLICY.md`, "Textures are judged at
distance"). Canidae routes its meshes to new texture paths
(`textures/aaaamv/woof/`), so `inspect_mod.py` reports "0 of 40 textures replace
a vanilla asset" and skips the comparison entirely. Pairing each one by hand to
the vanilla texture it displaces, at matched pixel size, minimum over mips
512-128 px, against the project's 0.70 floor:

| Canidae texture | vanilla baseline | hf ratio | tone ratio | verdict |
|---|---|---|---|---|
| `wolf_head.dds` | `wolf.dds` | **x0.90** | x0.93 | pass |
| `wolf_body.dds` | `wolf.dds` | **x0.70** | x0.79 | pass, exactly on the floor |
| `wolf_body.dds` | `wolfred.dds` | **x0.85** | x1.11 | pass |
| `blackwolf_head.dds` | `wolfblack.dds` | **x0.77** | x0.86 | pass |
| `blackwolf_body.dds` | `wolfblack.dds` | **x0.54** | x0.79 | **FAIL** |
| `icewolf_body.dds` | `wolf.dds` | **x0.97** | x1.24 | pass |
| `icewolf_head.dds` | `wolf.dds` | **x1.40** | x1.57 | pass |

One texture fails, and it is salvageable rather than disqualifying. Running the
project's own recipe:

    py -3 audit/mip_retention.py <blackwolf_body.dds> --resharpen <out.dds> --unsharp 1.0

lifts it from **x0.54 to x0.89** at 512-128 px (mip-2 retention 0.38 -> 0.61).
That is a `recipe`-class Ensrick artifact under `REDISTRIBUTION.md`: the
installer regenerates it locally, no vendor bytes shipped.

**Defects found in Canidae, with the file named:**

- `meshes/actors/canine/character assets wolf/wolffire.nif` is **NIF user
  version 83 (Oldrim, `NiTriShape`) and skinned** - the conjured Flame Familiar.
  It is the **only** Oldrim mesh in the core option (11 of 12 are version 100).
  The other 38 Oldrim meshes in the archive are all inside patch folders we
  would not select (`pfiles/dbp` dog backpacks 26, `pfiles/doglife` 8,
  `pfiles/exd` 2, `pfiles/immc` 2). Fix is a one-file `nif-port-cli` pass.
- 24 of 30 diffuse textures ship with no matching normal map (e.g.
  `textures/aaaamv/woof/blackwolf_body.dds`).
- `textures/aaaamv/woof/icewolf_head.dds` ships with no mipmaps - shimmers in
  motion.
- 2 normals have a solid alpha channel, so gloss is uniform:
  `plaguewolfbody_n.dds` (patch file, not core).
- 2 textures show JPEG blocking: `plaguewolffur.dds` (grid ratio 1.41).
- `rope_n.dds` looks embossed from its diffuse (X/Y correlation 0.78) and is
  half the diffuse resolution - a pelt-patch file, not core.

### The rivals fail the project's own distance test outright

- **[Wolves of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/68069) 2.1 (68069)**: `wolf_n.dds` is **x0.46** of vanilla at
  mid/far - it goes matte at play distance. It also ships `wolf_n.dds` at 1024
  px against vanilla's 2048, `wolf_sk.dds` at **40 px** against vanilla's 512,
  two uncompressed textures costing roughly 11 MB of VRAM, five
  non-power-of-two textures, and 9 of 30 sampled textures carrying far less
  detail than their stored size (`wolfblack.dds` 4096 px, detail index 0.31).
  Mean detail index 1.59 against Canidae's 6.12.
- **[Real Fur for Wolves](https://www.nexusmods.com/skyrimspecialedition/mods/63378) 1.1 (63378)**: median x0.76 at mid/far but 5 of 10
  textures soft or upscaled, and 10 of 10 diffuses ship with no normal - one of
  them falls back to the vanilla normal, which will not match the new art.
- **[Savage Wolves](https://www.nexusmods.com/skyrimspecialedition/mods/21075) 1.7 (21075)**: replaces the wolf **skeleton** by design. That
  is the one change class this build cannot absorb quietly, and it has not been
  touched since 2020-05-30.

### Visual recommendation

**[Canidae - A Wolf Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/182994) 2.25 (182994), core "Wolf Replacer" option only**,
declining every FOMOD plugin, plus two Ensrick recipe fixes:

1. re-generate `blackwolf_body.dds`'s mip chain with the `--resharpen` recipe
   above (measured x0.54 -> x0.89);
2. convert `wolffire.nif` to SSE format with `nif-port-cli`.

Reasons: it is the only candidate that changes the *shape*, which is the actual
complaint; it is the only one still being updated (2026-08-29, four days before
this audit); its core option ships **no plugin at all**, so it cannot collide
with the behaviour patch below; and six of its seven measured textures clear the
distance floor.

Decline `Canidae - Red Wolf Leveled List Addon` (a FOMOD option of 182994) specifically: it *adds* the
unused red wolf to leveled lists, pushing wolf frequency the wrong way while #42
is trying to lower it.

Fluffworks is a legitimate second lane, not a rival: [`Canidae - Fluff AF Patch`](https://www.nexusmods.com/skyrimspecialedition/mods/184334) (184334, 2026-08-04) exists precisely to put Fluffworks shells on Canidae's
meshes. It should be a separate decision after Canidae has been seen in motion,
because it costs frames (the author quotes 2-7 fps per animal for the Quality
build) and its benefit is fur volume, not shape.

**Only the user can settle:** whether Canidae's wolf reads as "a real wolf"
rather than "a different monster" - the numbers say the art is competent and
holds up at distance, they cannot say it looks right; and whether the fur volume
of the Fluff AF patch is worth the frames.

## 2. Behaviour - where "territorial like a bear" actually lives

The 2026-08-28 audit was right that this is not one enum. Here are the numbers.

### AI Data, side by side

`skyrim-record-cli record-fields Skyrim.esm <EditorID>`:

| actor | FormID | Aggression | AggroRadiusBehavior | Warn | WarnOrAttack | Attack | Confidence | Combat style |
|---|---|---|---|---|---|---|---|---|
| `EncWolf` | 023ABE | Unaggressive | **true** | **0** | 2000 | 1500 | Foolhardy | `csWolf` 057BE8 |
| `EncWolfRed` | 10FE05 | *inherits* | *inherits* | - | - | - | - | *inherits* |
| `EncWolfIce` | 023ABF | **VeryAggressive** | **false** | 0 | 0 | 0 | Foolhardy | `csWolf_Ice` 0E8C3D |
| `EncBear` | 023A8A | Unaggressive | true | **2500** | 2000 | 1500 | Foolhardy | `csBear` 08E665 |
| `EncSabreCat` | 023AB5 | Unaggressive | true | 0 | 2000 | 1500 | Foolhardy | `csSabreCat` 01CDE6 |
| `EncHorker` | 023AB1 | **Aggressive** | true | 850 | 640 | **320** | Average | `csHorker` 0CDE5E |

Three findings that change the shape of the patch:

1. **The wolf/bear difference is one number, and it is not the aggression enum:
   `Warn`.** Bears have a 2500-unit warning band - the rear-up-and-growl stage -
   before the 2000 warn-or-attack and 1500 attack bands. Wolves have **no warn
   stage at all** (`Warn = 0`), so they cross straight into attack at 1500 units
   (about 21 m at 1 unit = 1.428 cm). That is exactly the felt difference the
   user described, and it is measurable.
2. **The horker, which he also named, is the territorial extreme, and it is
   `Aggressive`, not `Unaggressive`:** it attacks, but only inside **320 units**
   (about 4.6 m). "Territorial" in vanilla is encoded as a short attack radius,
   not as a low aggression enum.
3. **`EncWolfRed` inherits AI Data from `EncWolf` through its template**
   (`TemplateFlags = Stats, Factions, SpellList, AIData, AIPackages, BaseData,
   Inventory, Script, DefPackList, AttackData, Keywords`; `Template = 023ABE`).
   One record edit therefore covers ordinary and red wolves. `EncWolfIce` has
   `TemplateFlags = 0` and must be edited separately if it is to change at all.

Combat styles differ too, and in a way that matches the complaint: `csWolf` and
`csWolf_Ice` set `DATA flags = 0x2` (flanking) with `FlankDistance 0.5` and
`StalkTime 0.4`; `csBear` and `csHorker` set `0x1` (dueling) with
`FlankDistance 0.2 / 0.0`. Wolves circle and flank as a pack; bears come at you
head-on. That is worth keeping - it is what makes a wolf pack a wolf pack.

### Factions - the "they attack everything" half

Wolves and bears carry an **identical** faction set apart from the species
faction (`NPC_ SNAM`):

    EncWolf      CreatureFaction, PredatorFaction, SprigganPredatorFaction, WolfFaction
    EncBear      BearFaction, CreatureFaction, PredatorFaction, SprigganPredatorFaction
    EncSabreCat  CreatureFaction, PredatorFaction, SabreCatFaction, SprigganPredatorFaction
    EncHorker    CreatureFaction, HorkerFaction, HunterPreyFaction, PreyFaction

and the only hostility in that set is `PredatorFaction -> PreyFaction = Enemy`
(`FACT 02E893 XNAM`). Elk, deer and horkers are in `PreyFaction`; that relation
is why wolves hunt them - and bears and sabre cats hunt them through the very
same relation. `WolfFaction` (`03E691`) contains no hostility at all: its
relations are Ally to itself and to `PlayerWerewolfFaction`, and Friend to the
werewolf, vampire, vampire-thrall and prisoner factions.

**Conclusions for the patch:**

- Nothing in any faction makes a wolf hostile to the *player*. Player hostility
  is entirely AI Data plus the aggro radius. So the "everything attacks them"
  half is a consequence, not a cause: the wolf opens at 1500 units with no
  warning and everything nearby responds. Shorten the radius and most of it goes
  away on its own.
- **Do not touch `PredatorFaction`.** Editing it to stop wolves hunting would
  also neuter bears and sabre cats, and it is overridden today by **Unofficial
  Skyrim Modders Patch** (verified: USMP ships `FACT 000013 CreatureFaction`,
  `02E893 PredatorFaction`, `02E894 PreyFaction`, `03E093
  SprigganPredatorFaction` and `03E691 WolfFaction`, adding `FULL` names and
  `CRVA`/`VENV` blocks while leaving the `XNAM` relations at vanilla values).
  A faction edit would have to forward all of that for no gain.

### What a narrow generated patch would contain

Four records, and only four, in an ESP-FE:

1. `NPC_ 023ABE EncWolf` - raise `Warn` from **0 to 2500** (bear parity, giving
   a warning stage) and shorten `Attack` from **1500** toward the horker's
   **320**. The honest first build is bear-parity warn plus a shortened attack
   band; 640 then 320 are the numbers to try. `EncWolfRed` follows for free
   through the template.
2. `NPC_ 023ABF EncWolfIce` - a decision point, not a default. Today it is
   `VeryAggressive` with `AggroRadiusBehavior = false`, i.e. it attacks on sight
   at any range. Leaving it alone keeps a genuinely dangerous wolf in the snow,
   which is arguably what the user wants once ordinary wolves calm down.
3. `NPC_ 0010F2A2 EncWolf_Indoor` and `0010F2A3 EncWolfIce_Indoor` - the dungeon
   variants. They carry their own template flags and will silently keep the old
   behaviour unless checked.
4. Nothing else. No faction record, no combat style, no race, no leveled list.

**Records the patch must forward.** Scanning the 231 of 243 active plugins
whose first master is `Skyrim.esm` (the other 12 are DLC/CC/worldspace-rooted
and cannot override a `Skyrim.esm` FormID as index 00) for overrides of the
wolf, predator-list, faction, combat-style and race records returns exactly
two:

- `unofficial skyrim special edition patch.esp` overrides six `NPC_` records -
  `LvlAnimalCanyonPredator`, `LvlAnimalCoastSnowPredator`,
  `LvlAnimalForestPredator`, `LvlAnimalHillsPredator`,
  `LvlAnimalMountainSnowPredator`, `LvlAnimalPlainsPredator`.
- `Unofficial Skyrim Modders Patch.esp` overrides the five creature `FACT`
  records listed above.

Neither touches `EncWolf` itself, so the behaviour half of the patch conflicts
with nothing currently installed.

**Only the user can settle:** the actual attack radius. 1500 units is "charges
you across a field"; 320 is "you basically stepped on it". That is play-feel and
needs an approach/retreat test in the field before it is fixed.

## 3. Fewer encounters, packs kept at 2-3

### How wolves actually get into the world

Measured over `Skyrim.esm` (10,504 `ACHR` refs in total):

- **113 wolf refs by base**, of which 69 are hand-placed `EncWolf`, 5
  `EncWolfIce` and 3 `LvlWolf`; the rest are dungeon, quest, spirit and summon
  variants.
- `LCharWolf` (`0B83C2`) is placed **zero** times. It is referenced only as a
  template by `LvlWolf` and `dunBloodletThrone_LvlWolf`. It is not the
  wilderness population - the 2026-08-28 audit of its flags is correct, but it
  is not the lever.
- The wilderness population is **666 placed refs on the regional predator
  actors**: `LvlAnimalForestPredator` 180, `LvlAnimalMountainSnowPredator` 143,
  `LvlAnimalPlainsPredator` 105, `LvlAnimalCanyonPredator` 90,
  `LvlAnimalCoastSnowPredator` 86, `LvlAnimalForestSnowPredator` 30,
  `LvlAnimalHillsPredator` 29, `LvlAnimalSnowFields` 5. Each of those is an
  `NPC_` whose `TPLT` points at the matching `LCharAnimal*Predator` leveled
  list, and **each ref rolls that list independently**.

### Why frequency and pack size pull against each other - and by how much

`LCharAnimalForestPredator` (`042297`) is 26 entries, `LVLF = 3`
(`CalculateFromAllLevelsLessThanOrEqualPlayer` + `CalculateForEachItemInCount`),
chance-none 0%, of which **4 are level-1 `EncWolf`**. At level 1 only 5 entries
are eligible, so a roll is 80% wolf; at level 35 all 26 are eligible and a roll
is 15% wolf. Summed over all 666 refs using each list's own eligibility:

| player level | expected wolf spawn points | wolf share of predator points |
|---|---|---|
| 1-5 | **535** | 80.3% |
| 10 | 417 | 62.6% |
| 15 | 244 | 36.6% |
| 20 | 202 | 30.3% |
| 30 | 163 | 24.4% |
| 35+ | 151 | 22.6% |

Plus the 74 hand-placed `EncWolf`/`EncWolfIce` refs, which never change.

That is the arithmetic behind the complaint, and it also shows why a list-side
edit is the wrong tool: dropping wolf entries from `LCharAnimalForestPredator`
lowers frequency, but because every ref in a cluster rolls separately, a
three-point site stops resolving to three wolves and starts resolving to a wolf,
a bear and a spider. Pack size is destroyed to buy frequency.

### Vanilla pack structure, measured

Single-linkage clustering of the 666 predator refs by 3D position within each
worldspace, 2000-unit link radius (about 29 m):

    666 refs -> 406 clusters
      size 1: 205 clusters (205 refs)
      size 2: 146 clusters (292 refs)
      size 3:  51 clusters (153 refs)
      size 4:   4 clusters  (16 refs)

Stable across link radius: at 1200 units it is 258/146/54/5, at 3000 units
197/159/60/7. The hand-placed wolf refs alone cluster to 17 singletons, 14
pairs, 8 triples and 2 quads - the same shape.

So **the 2-3 pack the user wants already exists**: it is the 201 clusters of
size 2-4. What produces the "wolves everywhere" feel is the 205 **singleton**
spawn points scattered between them.

### The encounter-side proposal

Retire spawn points **cluster-wise**, not ref-wise, and retire singletons first:

- Set `Initially Disabled` on all **205 singleton-cluster refs**. Never delete -
  a deleted `ACHR` is a UDR, and this build already runs `Navigator` and USSEP
  to clean up after Bethesda's.
- Result: **461 refs in 201 clusters, mean pack 2.29, every surviving site at
  least 2.** No lone predator anywhere in the wilderness.
- Wolf effect at the current list weights: **-165 wolf spawn points at level 1**
  (535 -> 370), **-62 at level 20** (202 -> 140), **-46 at level 35** (151 ->
  104). A flat 31% cut, with pack size not merely preserved but raised.
- If 31% is not enough, the next tranche is a fraction of the 146 pairs, chosen
  by region so no area empties out. Triples and quads are never touched - they
  are the thing being protected.

To make a surviving wolf site read as a *wolf pack* rather than a mixed predator
site, re-point the refs of a chosen subset of clusters from `LvlAnimal*Predator`
to `LvlWolf`, whose template is `LCharWolf`. That keeps wolves inside an
existing vanilla list, as the preferred implementation requires, and guarantees
every ref in that cluster resolves to a wolf.

One mechanism was checked and ruled out: spawning 2-3 actors from a single ref
via an `LVLN` entry count. **No vanilla `LVLN` uses count > 1** - 0 of 527 lists
- so there is no in-engine precedent to copy, and whether the engine honours the
count field for `LVLN` at all is `[unverified]`.

### Adopted worldspaces

| plugin | own wolf records | placed refs | consequence |
|---|---|---|---|
| `BSHeartland.esm` (Bruma) | `CYREncWolf`, `CYREncWolfTimber`, `CYREncWolfHighland`, `CYREncWolfDire`, `CYRLvlWolf`, `CYRLCharWolf`, +5 | 47 on its own bases, 3 on vanilla predator lists | **needs its own overrides** - a vanilla-record patch does almost nothing here |
| `Wyrmstooth.esp` | none | `EncWolf` 2, `EncWolfIce` 1, 11 on vanilla predator lists | covered automatically by the vanilla patch |
| `arnima.esm` (Beyond Reach) | `EncWolfarnima`, `EncWolfarnima2`, `EncWolfarnimamother`, `EncWolfarnimashaman`, `EncWolfArnimaQuest`, `arnimaboywolf`, `wolfshamanArnima` | 27 vanilla wolf refs (`EncWolf` 18, `EncWolfIce` 7, `EncWolfRed` 2) plus 17 on its own quest wolves | the vanilla patch covers the 27; the seven named actors are quest/unique and **must be preserved** |
| `Gray Fox Cowl.esm` | `manny_GF_Animal_DesertWolf` | 41 | a separate species-flavoured actor; its own decision |
| `Vigilant.esm`, `moonpath.esp` | none | none | nothing to do |

## 4. The hole this leaves for #43

Retiring the 205 singleton clusters removes **205 wilderness spawn points, 31%
of the exterior predator population**. At level 20 about **62** of those would
have been wolves and about **143** bears, sabre cats, trolls, spiders and
skeevers; at level 1 the split is roughly 165 wolves to 40 others.

That is the size of the hole to hand to
[#43 (Bounded Encounters)](https://github.com/Ensrick/skyrim-mod-assistant/issues/43):
**205 discrete, already navmeshed, already encounter-zoned exterior positions**,
with worldspace and coordinates recoverable from the same scan, distributed
across forest (180-ref pool), mountain-snow (143), plains (105), canyon (90),
coast-snow (86), forest-snow (30) and hills (29). They need no new placement
work - they need a different base actor.

## Open questions only the user can answer

1. Does Canidae's wolf read as a real wolf to him, in motion, at play distance?
2. Fluff AF patch or not - fur volume against 2-7 fps per animal?
3. Attack radius: bear parity (`Warn 2500`, attack at 1500) or horker-like
   (attack at 320-640)? Play-feel; needs a field test.
4. Should `EncWolfIce` stay `VeryAggressive` - does the snow keep a wolf that
   still hunts on sight?
5. Is a 31% cut in wilderness predator sites the right size, or should the
   second tranche (pairs) be planned now?

---

# Built - 2026-09-03: the behaviour patch is in, the thinning patch is staged

Constraint change from the user before bed, 2026-09-02: *"don't pickup new mods
without permissions, just suggest no mods"* and *"If there's solutions that don't
require downloading mods, implement them as best you can."* So section 1 above is a
**suggestion with links**, nothing installed; sections 2 and 3 were ours to build, and
they were built with the frameworks already in the profile. Details, policy and
reproduction: `mods/wolf-territorial-patch/README.md`.

## `Ensrick Wolf Territorial Patch.esp` - installed, enabled, launch-verified

ESL-flagged, override-only, **9 `NPC_` records**, 3,959 bytes, sha256
`63745001DEF4FFCE2634E399B17A0B5CD82968EA8C7063558EE092EA1069A899`. Masters
`Skyrim.esm`, `BSHeartland.esm`, `arnima.esm`, `Gray Fox Cowl.esm`.

The rule, applied to the eight ambient wolf bases in section 2's table plus Bruma's,
Beyond Reach's and the Gray Cowl's own wolves:

| field | vanilla wolf | patched | vanilla bear | vanilla horker |
|---|---:|---:|---:|---:|
| `Warn` | 0 | **2500** | 2500 | 850 |
| `WarnOrAttack` | 2000 | **1200** | 2000 | 640 |
| `Attack` | 1500 | **640** | 1500 | 320 |

A wolf now growls from about 36 m and attacks at about 9 m instead of 21 m.
`Aggression` stays `Unaggressive`, `csWolf`'s flanking data is untouched so packs still
flank, and **no faction record was edited** - the section-2 finding that
`PredatorFaction -> PreyFaction = Enemy` is shared with bears and sabre cats held, so
touching it would have neutered them too.

Targets, all verified to carry the identical vanilla signature before anything was
written: `EncWolf` (107 placed refs), `manny_GF_Animal_DesertWolf` (41), `CYREncWolf`
(15), `CYREncWolfTimber` (4), `EncWolfarnima2` (3), `EncWolfarnima` (1),
`CYREncWolfHighland` and `CYREncWolfDire` (leveled-list only). Eleven more records
follow through their templates and the generator **measures** that set rather than
trusting the policy. One heir was deliberately removed from it: `SummonFireStorm`, the
conjured Flaming Familiar, is de-inherited and pinned to the old numbers, because a
summon answers to its summoner and not to a territory.

52 wolf records are excluded with a reason each, including `EncWolfIce` - still
`VeryAggressive` with the aggro radius off, i.e. hostile on sight at any range. That
one is deliberately left as an open question below.

Receipts: two byte-identical generations, 117 links checked / 0 unresolved, Spriggit
0.41.0 checked round-trip, `audit/verify_order.py` CLEAN over 244 active plugins,
`install_mod.py --verify` 0 problems, `audit/preflight.py` clean (4 pre-existing
warnings). **Launch verification PASS** - main menu **31.9 s**, save loaded **40.6 s** -
`records/launch-verify-20260902-233602.md`.

Rollback is disabling one mod row.

## `Ensrick Wolf Encounter Thinning.esp` - generated, staged, NOT installed

191 placed-actor `Initially Disabled` overrides (381 records including parent cells),
171,679 bytes, sha256
`739AAFE6545B7B463E57BA512F35950A69550D92D582B5697105F423CB620ED3`, in
`mods/wolf-territorial-patch/thinning/package/`.

Section 3's proposal, measured against the live load order rather than `Skyrim.esm`
alone: **622 exterior references** on the seven wolf-bearing regional predator actors
form **387 clusters** at a 2000-unit link radius - 203 singletons, 137 pairs, 43
triples, 4 quads. Retiring the singleton clusters removes **191 references (30.7%)**
and leaves **431 references in 196 clusters, every surviving site at least 2**.
Twelve singleton clusters were held back because their one reference is persistent or
enable-parented.

Three things the generator does that the prose proposal did not spell out:

1. Ineligible references (171 persistent, 13 enable-parented, 1 already disabled) still
   **count towards cluster size** even though they are never retired. Excluding them
   from the clustering instead turns a pair into a fake singleton - that mistake
   produced a 71.6% cut on the first run and the 40% guard rail caught it.
2. A cluster holding an untouchable reference is left **whole**, so no encounter is
   half-retired.
3. `LCharAnimalForestSnowPredator` has **0 wolf entries**, so its 30 placed references
   are out of scope entirely.

It is not installed because how much wilderness to empty is a taste decision, and
because the behaviour patch alone may change how crowded the wilderness feels. One
command installs it once the user says a number.

**Hand-off to [#43](https://github.com/Ensrick/skyrim-mod-assistant/issues/43) is now
exact: 191 discrete, already navmeshed, already encounter-zoned exterior positions**,
by region: forest 45, mountain-snow 41, canyon 34, plains 29, coast-snow 26, hills 15,
snowfields 1.

## What changed in the analysis above

Two numbers in section 3 were measured on `Skyrim.esm` alone and are superseded by the
load-order-wide generator run: 666 refs / 406 clusters / 205 singletons becomes **622
eligible-and-clustered refs / 387 clusters / 203 singletons**, and the retirement is
**191 (30.7%)** rather than 205 (31%). The shape of the finding is unchanged; the
difference is interior cells, the seven-base scope, and counting persistent references
as cluster members rather than as targets.

## Open questions, unchanged

1. Does Canidae's wolf read as a real wolf in motion, at play distance?
2. [Fluffworks](https://www.nexusmods.com/skyrimspecialedition/mods/56361) shells on top
   via the [Fluff AF patch](https://www.nexusmods.com/skyrimspecialedition/mods/184334) -
   worth 2-7 fps per animal?
3. **The attack radius.** 2500 / 1200 / 640 is shipped and needs a field test. 1500 is
   "charges you across a field", 320 is "you basically stepped on it".
4. Should `EncWolfIce` stay `VeryAggressive`?
5. Install the thinning patch at 30.7%, or a different cut?
6. New lever found while building: every wolf in the game is `Confidence = Foolhardy`,
   which is why they never break off a losing fight. Lowering it is a second,
   independent way to make them read as animals. Not touched.
