# Grounded progression research (issue #226)

**Date:** 2026-09-04
**Scope:** AUDIT ONLY. Nothing installed, no profile file mutated, no launch, no
curator decision changed, no instance claim taken, no commit.
**Inputs:** five measurement passes plus three adversarial reviews, all three of
which refuted part of the surveys. Corrections are applied below and listed in
section 9.
**Instruments:** `skyrim-record-cli-1f3c8d9` (`plugin-info`, `records`,
`record-fields`, `record-selected-fields-by-type`), raw binary walks of
`Skyrim.esm` (869,688 records / 5,118 `NPC_` / 375 `PERK`), Nexus v1 API and
GraphQL, and DLL/INI string tables from shipped archives. Archives went to the
MO2 download/audit cache; extraction was outside `mods\`.

---

## 1. Recommendation, up front: DEFER the perk slot, do the scaling half now

**Do not install a perk overhaul.** Not Adamant, not Ordinator, not Vokrii, not
Requiem. Three independent reasons, each measured:

1. **A perk overhaul cannot deliver three of your four stated requirements.**
   Ordinator, Vokrii and Adamant contain **zero `Npc` records and zero `Race`
   records**. Ordinator and Vokrii contain **zero GameSettings**; Adamant has 12
   and all 12 are player-side (`fArmorRatingPCMax`, `fDamagePCSkillMax`,
   `fAlchemySkillFactor`, smithing caps, pickpocket). So `fNPCHealthLevelBonus`,
   `ACBS.HealthOffset` and `RACE.Starting.Health` - the three fields that
   actually make the sponge - are untouched by every candidate in the field.
   [MEASURED]

2. **Vanilla already implements "level buys capability, not padding" on the
   enemy side, and every candidate overwrites it.** Parsing `PRKR` across all
   5,118 `NPC_` records: `Armsman00/20/40/60/80`, `Barbarian00/20/80`,
   `Overdraw00/20/80`, `AgileDefender00/20` and `CriticalCharge` are carried by
   **zero NPCs**. What enemies actually carry is capability:
   `Bladesman30` (`05F56F`) 206 NPCs, `HackAndSlash30` (`03FFFA`) 199,
   `BoneBreaker30` (`05F592`) 124, `DeepWounds30` (`03AF83`) 114,
   `MatchingSet` (`051B17`) 13. Bethesda withholds flat damage multipliers from
   NPCs entirely. All three overhauls override all five of those FormKeys -
   Adamant turns the 206-NPC `Bladesman30` into `MAG_KeenEdge01` "Swords and
   daggers deal three times more critical damage". Filling the slot silently
   rewrites the one vanilla system that already matches your design, in a
   direction no survey evaluated. [MEASURED]

3. **Your own stated reason.** You stopped authoring an overhaul because you
   have not played enough recently to know how progression should feel. The
   build is a played baseline, not a hole: `profiles/Default/modlist.txt` has
   257 enabled mods with no gameplay overhaul of any kind, and `CHANGELOG.md`
   checkpoint 2026-08-29 records main menu reached, save loaded, session played
   to 18:40. Deferral costs nothing measurable: both Ordinator and Vokrii state
   verbatim "Can be installed during your playthrough", so the mod installs later
   exactly as it would today. Installing now costs something: both also state
   "If your character is level 2 or higher, installing the mod will start a perk
   refund process" and "Refund your perk points before uninstalling" - a scripted,
   save-mutating operation that must be unwound by script. [MEASURED]

**What to do instead, in order:**

1. Author the NPC-scaling configs (section 5). Config only, no plugin, no new
   dependency, fully reversible.
2. Play the rescaled build. That is the only instrument that answers "how should
   progression feel".
3. Revisit perks after that, with the option of a 25-record hand-authored ESP
   (section 5.4) instead of an overhaul.

---

## 2. The oil perk is Ordinator's. That anchors your taste boundary

**[MEASURED]** [Ordinator - Perks of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1137)
9.35.0, PERK record `059808`, EditorID
`ORD_Alc90_WalkingDisaster_Perk_90_OrdASISExclude`, Name "Walking Disaster",
Description verbatim: *"In combat, periodically spill a random oil puddle on the
ground. Puddles last 60 seconds."* Alchemy tree, skill 90. Two siblings in the
same tree: `058D19` Elemental Oil (*"You may choose a power: 'Fire Oil', 'Frost
Oil' or 'Shock Oil'. At will, create a pool of oil that lasts 20 seconds..."*)
and `058D2A` The Alchemist's Cookbook. Source archive
`downloads\1137-675234.zip`, sha256
`b25314839e9f52e1a2c20dae96d224b4f4cf07345acee0a8b55dd11d687c3c99`, Nexus file
675234 uploaded 2025-10-12.

Ordinator carries 27 of 828 perks with active-power phrasing (Trained Rabbit,
Death's Emperor, Philosopher's Stone, Dimension Door, Horn of Sovngarde), 41
scripted perk quests, and a damage ceiling of 200%.

**Fairness note [MEASURED]:** the common claim that Ordinator forces tree-dumping
via a bigger Armsman is **false**. Its player-facing One-Handed Mastery is 2
points for +50% (`00B149` -> `00B14A`, NextPerk Null); the 100/125% ladder
records are the NPC-only `_OrdASISExclude` set, confirmed from the `AVOneHanded`
perk-tree node list (`00B149` present, `0BABE4` absent), not from the EditorID
suffix. Ordinator fails your bar on gimmick content, not on a mandatory tax.

**And the boundary generalises.** Refuter 2 re-dumped Vokrii's 426 PERK records
and found the same class of perk under different wording:

- **Death's Emperor**, two ranks, Pickpocket tree, with a dedicated
  `VKR_DeathsEmperor_Quest`. The cursed septim you rejected in Ordinator.
- **Lockdown / Hotwire / Overdrive** - lockpick a Dwemer automaton to shut it
  down, then reprogram it to follow you. `Overdrive` is Vokrii-exclusive:
  Vokrii has *more* of this than the mod rejected for it.
- **Speak with Animals / Beastmaster** - tame an animal as a Wild Companion.
  Same archetype as Ordinator's Trained Rabbit.
- **Spider Hunter**, **Scroll Hunter** ("10% chance to find a random scroll on
  the corpses of people you kill"), **Dungeon Master**, **Master Thief** - all
  Vokrii-exclusive, absent from Ordinator.
- **Ki Strike** - "Power attacks with two empty hands deal 60 points of random
  elemental damage", an unarmed monk build inside the Light Armor tree.
- **Intervention** (Restoration): *"Once every 30 minutes, a higher power brings
  you back with full Health upon death"*, with `VKR_Intervention_Quest`. A free
  resurrection on a timer, in a build running Starfrost 2.0.0 + Survival Mode
  Improved 1.7.0.

The earlier "1 of 426 gimmick perks" figure was a grep artifact: the search
vocabulary was "at will / once a day / appears in your inventory / choose a
power", and Vokrii phrases its gimmicks as "Can tame", "Can lockpick", "brings
you back", "find a random". The one hit it did return,
`VKR_Enc_old_ChargeTap_Perk`, carries the `old` prefix used to mark cut records.

**Conclusion:** the oil perk was an example of a class, not the class itself.
Vokrii passes the literal oil grep and fails the category it stood for.

---

## 3. Which mods can be ADOPTED, and which are blocked

### 3.1 Perk overhauls: none are both available and grounded

| Mod | Verdict | Receipt |
|---|---|---|
| [Adamant 6.0.4](https://www.nexusmods.com/skyrimspecialedition/mods/30191) | **Blocked twice** | Hard-masters `MysticismMagic.esp` (plugin-info masters list, measured twice independently) and overrides 229 Mysticism records; its FOMOD has exactly one Main File with no Mysticism-free route. Separately, its required [Scrambled Bugs](https://www.nexusmods.com/skyrimspecialedition/mods/43532) is installed-but-**disabled** here (`installed-mods.json`: `"version": "21", "enabled": false`, parked 2026-08-25 on the #87 DLL gate); upstream has shipped nothing since 2023-03-14; Adamant's own FOMOD says "Without these settings, several Adamant perks will not function." |
| [Ordinator 9.35.0](https://www.nexusmods.com/skyrimspecialedition/mods/1137) | **Rejected on taste** | `059808` Walking Disaster, plus 26 other active-power perks. Your named example. |
| [Vokrii 3.8.2](https://www.nexusmods.com/skyrimspecialedition/mods/26176) | **Rejected on taste, and stale** | Section 2 above. Also: only current MAIN file is fid 258362, uploaded **2022-01-21**, 4.5 years, and the ecosystem survey places it on STEP alone. Same currency filter that dropped Falskaar. |
| [Master of One 2.1.0](https://www.nexusmods.com/skyrimspecialedition/mods/47024) | **Rejected on design** | Punishing generalists is the *intent*: `moo_archery_marksman5` = "Deal twice as much damage with bows, but half damage with melee weapons other than daggers", and 8 further perks pair "150% more damage" with "-50% to other weapon types". 498 endorsements / 23,483 downloads, absent from all 19 surveyed lists. |
| [Requiem 6.0.2](https://www.nexusmods.com/skyrimspecialedition/mods/60888) | **Not measured, and out of scope** | 200 MB single monolithic ESP, requires a new game, would displace Starfrost + SMI. Its own page: *"you are defined by your perks, as skills primarily allow you to unlock perks, but affect little else"* - the opposite of your structural objection. Its perk shape was **not** measured this pass; treat any claim about it as unverified. |
| Vokord 1.92, Vokriinator, Vokriinator Black | **Rejected** | All master Ordinator, and Vokord's `Vokriinator.esp` (389 PERK) overrides none of `058D19`/`058D2A`/`059808` - the oil perks survive intact. All three also master Mysticism. |
| [Natural Learning 1.1.0](https://www.nexusmods.com/skyrimspecialedition/mods/148990) | **Closest to your words, unmeasured** | Not a perk overhaul and does not contest the slot. No perk points at all; One-Handed at skill 100 totals +12% base damage, +40% crit damage, +2% crit chance, +5% power-attack damage. Page: *"There are no perk points to spend, no abilities to toggle - just organic character growth."* **INFERRED**: nobody opened its plugin. It needs its own measured pass before it could be adopted. |

Two prompt names could not be resolved: **"Vanilla Perk Trees Expanded"**
returns `totalCount 0` on a Nexus SSE name search (broadened "Perk Trees"
returns 6 mods, none by that name), and **"SkyRem"** returns 16 SSE mods, none of
which is a perk overhaul (it is an immersion/economy/class series). If you have a
specific page in mind, a URL settles it in one call.

### 3.2 Combat: Blade and Blunt is NOT recommended today

[Blade and Blunt 4.0.3](https://www.nexusmods.com/skyrimspecialedition/mods/34549)
is the only combat mod measured that moves outcome toward armor
(`fArmorScalingFactor` 0.12 -> 0.15, `fArmorBaseFactor` 0.03 -> 0, two-stage cap
confirmed from the DLL string table: "Setting max armor rating to 75" and
"...to 90"). It also adds 56 new perks and overrides exactly one vanilla perk
(`crNerfDamage05`), so it would not constrain the perk decision.

**But it is blocked and it misbehaves by default:**

- **Dependencies absent or parked.** Its page requires Scrambled Bugs (parked on
  #87 - the *same* gate used to disqualify Adamant), Actor Value Generator,
  Lexicon SKSE and Dual Casting Fix. Grep of `records/installed-mods.json` (278
  rows): Actor Value Generator 0, Lexicon 0, Dual Casting Fix 0, TrueHUD 0.
  The archive ships `main/SKSE/Plugins/ActorValueData/BladeAndBlunt_AVG.toml`
  and its DLL sets `StaggerBarAV = StaggerPoints`, an AV that only exists via
  AVG. [MEASURED]
- **It ships player-level rubber-banding turned ON.** The Nexus page says
  *"This option is disabled by default"*; the v4.0.3 archive's own
  `main/SKSE/Plugins/BladeAndBlunt.ini` line 6 reads
  `bLevelBasedDifficulty = true`. The feature ramps difficulty at player levels
  10/20/30/40/50. That is the exact shape used to reject Level Matters, Dynamic
  Stat Scaler, Real Time NPC Stat Scaler and Dynamic NPC Scaling. [MEASURED]

If it is ever revisited the conditions are explicit: install AVG (84743),
Lexicon SKSE (153176) and Dual Casting Fix (92454), resolve #87 for Scrambled
Bugs, and set `bLevelBasedDifficulty = false` as a recorded build decision.

Its attack commitment is **12 MovementType records** - data, not an animation
graph, so the MCO/BFCO/SkySA/SCAR filter does not automatically catch it - and
[a first-party revert](https://www.nexusmods.com/skyrimspecialedition/mods/83356)
covers 10 of those 12 (uncovered: `NPC_Blocking_ShieldCharge_MT` `0EF541`,
`NPC_BowDrawn_QuickShot_MT` `0EF542`). Whether the residual is acceptable is
yours to call.

**Rejected outright:** [Wildcat 7.1.0](https://www.nexusmods.com/skyrimspecialedition/mods/1368)
and [Smilodon](https://www.nexusmods.com/skyrimspecialedition/mods/2824) both set
`fNPCHealthLevelBonus` **5 -> 6**, a 20% increase in exactly the level-driven
padding you object to. Neither mod page mentions armor rating; both change it
(`fArmorScalingFactor` 0.125, `fShieldScalingFactor` 0.2 -> 0.075). [MEASURED]
One idea from Smilodon is worth stealing as data rather than installing: it
handles large creatures by **damage reduction** (-50% to dragon / centurion /
giant / mammoth) instead of health inflation, which is closer to "sponges only
for big monsters" than a health pool is.

### 3.3 Scaling: what is adoptable

- [Arena 1.2.0](https://www.nexusmods.com/skyrimspecialedition/mods/33487)
  (Simon Magus, 9,445 endorsements) tiers dungeons by enemy type. Its stated
  requirement is "Requires SKSE." only - **no Adamant or Mysticism master**, so
  it is available regardless of the perk decision. Its design statement is your
  principle in someone else's words: *"each enemy type has a natural ceiling for
  how high it can scale."* **Its plugin was NOT opened by any pass** - the tier
  numbers circulating (bandits ~5, draugr ~10, ...) are STEP/search summary, not
  measurement. [INFERRED]
- [Enemy Releveler 2.1.0](https://www.nexusmods.com/skyrimspecialedition/mods/32211)
  compresses per-faction level ranges (bandits [1,28] -> [2,15]). Since health is
  a function of level, this attacks the ladder from the other end.
- [EEOS 2.02](https://www.nexusmods.com/skyrimspecialedition/mods/37228) is the
  released implementation of "level buys capability" - 1,069 distribution lines,
  981 with an explicit actor-level filter, zero plugins and zero scripts. But
  **[MEASURED]** it is 950 Spell / 55 Shout / 50 Perk / 4 Item, and all 38 FOMOD
  options are magic/shout mod addons. It is a caster-diversity mod that needs a
  magic overhaul this build does not have. Adopt the *technique*, not the mod.
- [NPC Stat Rescaler - Synthesis](https://www.nexusmods.com/skyrimspecialedition/mods/174057)
  is the right shape but **fails this project's own currency filter**: 19
  endorsements, 310 total downloads (Nexus API, 2026-09-04). The upstream zEdit
  original (24254) is 573 / 23,204 and needs a GUI Electron app not in the
  toolchain. Keep it as an optional bulk pre-pass only; see section 5.1 for why
  SkyPatcher is the better lever anyway. Modelling its published defaults on the
  measured formula also shows it does **not** fix the inversion: the draugr boss
  lands at ~433 HP against a ~330 HP giant, still 1.3x. [INFERRED, arithmetic on
  the published formula; the patcher was never run]

---

## 4. Your stat model, point by point: what is achievable and what is not

### 4.1 The measured vanilla formula

```
Health  = RACE.Starting.Health  + ACBS.HealthOffset  + (Level-1) * ( fNPCHealthLevelBonus + iAVDhmsLevelUp * Hw/(Hw+Mw+Sw) )
Magicka = RACE.Starting.Magicka + ACBS.MagickaOffset + (Level-1) * (                        iAVDhmsLevelUp * Mw/(Hw+Mw+Sw) )
Stamina = RACE.Starting.Stamina + ACBS.StaminaOffset + (Level-1) * (                        iAVDhmsLevelUp * Sw/(Hw+Mw+Sw) )
```

`fNPCHealthLevelBonus` = 5 (`023BB9:Skyrim.esm`), `iAVDhmsLevelUp` = 10
(`021A73:Skyrim.esm`), `fPCHealthLevelBonus` = 0 (`10CFB7`). Fitted against the
1,315 auto-calc, static-level, non-template-inheriting NPCs: health 1,041 exact,
1,311/1,315 within +/-1 (all residuals exactly 0.333 or 0.667). Worked receipt:
Alvor (`013475`), level 10, `VendorBlacksmith` weights 2/1/2, Nord base 50/50/50,
offsets 0 -> predicted 131/68/86, DNAM reads **131/68/86**. [MEASURED]

Note the correction: the widely-repeated "class adds 0-5 HP/level" prose gives
Alvor 113, not 131. The fitted class term `10 * Hw/(Hw+Mw+Sw)` is right.

### 4.2 Where the sponge actually lives

Decomposing the 319,452 total health of those 1,315 NPCs:

| source | share |
|---|---|
| `ACBS.HealthOffset`, hand-authored per record | **39.0%** |
| `RACE.Starting.Health` | 26.0% |
| flat `fNPCHealthLevelBonus` x (L-1) | 18.2% |
| class-weighted `iAVDhmsLevelUp` x (L-1) | 16.7% |

1,946 of 5,118 NPCs carry a nonzero `HealthOffset` (max +30,000). **A GMST-only
edit reaches 18.2% of the problem.** The worst single case decomposes
910 offset / 440 level / 50 race - the offset is 65%. Zeroing
`fNPCHealthLevelBonus` alone (which is all that
[Proper NPC health rescaling](https://www.nexusmods.com/skyrimspecialedition/mods/56121)
is - one record) removes 220 HP and leaves that draugr at 1,180 against a 591
giant, still double. [MEASURED]

The inversion you object to, in two records:

- `EncGiant03` (`030438`): GiantRace, **Size=ExtraLarge, BaseMass=4**, base
  health 250, HealthOffset **0**, level 32 -> **591 HP**, **0 perks**.
- `EncDraugr05Boss1HEbony` (`0DDD60`): DraugrRace, **Size=Medium, BaseMass=1**,
  base health 50, HealthOffset **+910**, level 45 -> **1,400 HP**, **1 perk**.

A Medium, mass-1 undead has 2.37x the health of an ExtraLarge, mass-4 giant, and
the entire difference is one hand-typed field.

And the ladders: bandits tier 1 (lvl 1) median 35 -> tier 6 (lvl 25-28) 489, 14x.
Draugr tier 1 50 -> tier 5 (lvl 30-45) 1,000-1,400, 20-28x. Forsworn 50 ->
455-623. Dragons 905 -> 3,071. [MEASURED]

### 4.3 Verdict on each of your four points

| Your requirement | Status | Receipt |
|---|---|---|
| **Enemies must not be damage sponges** | **ACHIEVABLE, config only** | 57.2% of the vanilla pool is padding you can remove: 39.0% `HealthOffset` + 18.2% GMST. Only **276** records carry offset >= 200, and they collapse into ~101 EditorID prefixes dominated by Draugr 03-05 and Thalmor/Vampire/Warlock top tiers. Reachable with a few dozen SkyPatcher `filterByEditorIdContains` lines. |
| **Health correlates with body size** | **HALF-VANILLA, rest must be authored** | Vanilla RACE records already carry `Size` and `BaseMass` next to `Starting`, and health tracks size: Small median 37-38, Medium 50, Large 225, ExtraLarge 500. Mammoth/Dragon 500, Giant 250, Bear 150-200, Troll 150-250, Draugr 50, Wolf 12, Skeever 15, Chicken 5. **But it is loose** (the Medium bucket spans 5 to 1,000) and has one flagrant violation: `DragonPriestRace` is **Size=Medium, Height 1.0, 1000 starting health** - double a dragon. **No released mod ranks health by body size** - that is a negative search result [INFERRED], not proof of absence. Closest is [Creature Size Variants](https://www.nexusmods.com/skyrimspecialedition/mods/17736), which is random variation on top of vanilla values via a Papyrus cloak. This is the authoring gap, and it is a data table. |
| **Health and stamina grow in very small increments with level** | **ACHIEVABLE, with one coupling to watch** | NPC side is the two GMSTs above. Player side is `iAVDhmsLevelUp` = 10, **the same constant that drives the NPC class-weighted term** - lowering it to shrink NPC growth also shrinks your own level-up gain. [Geometric Stat Growth](https://www.nexusmods.com/skyrimspecialedition/mods/92868) owns the player half but compounds by percentage, which is directionally opposite to "very small increments". |
| **Magicka starts at 0 and climbs stably** | **ALREADY VANILLA for NPCs; player side NOT VERIFIED** | `RACE.Starting.Magicka == 0` for **43 of 99** races (Giant, Bear, Draugr, Wolf, Troll...), and their classes carry Magicka weight 0, so it never grows. For the player: all playable races carry `Starting` 50/50/50 in the RACE record. **I did not verify what the player actually starts with in game, nor whether a separate term is added on top.** Do not act on this line without a check. |
| **Level buys perks, not padding** | **ALREADY VANILLA, and the overhauls break it** | Section 1, point 2. Also: perk count on NPC records rises with level (median level: 0 perks -> 1, 6 perks -> 19, 10 -> 39, 12 -> 46), and 1,620 of 5,118 NPCs carry at least one perk. Vanilla Forsworn is your design working - level 1 -> 46, perks 0 -> 16, offset never above 100 and back to 0 at the top tier. Vanilla Draugr is its opposite - level 1 -> 30, offset 0 -> +660, perks flat at 1 the whole way. |

---

## 5. What would have to be AUTHORED, kept as small as the doctrine demands

Rule 0 first: vanilla already implements most of this, and every lever is an
existing field. Rule 3: the deliverable is config files, not a program.

### 5.1 The lever is SkyPatcher, already installed and already switched on

**[MEASURED]** from the shipped `SkyPatcher.dll` string table (7.0.3):

- `race/` configs accept `startingHealth`, `startingHealthMult`,
  `startingStamina`, `startingMagicka`, `regenHealth`, `baseMass`,
  `weightMale/Female`, `heightMale/Female`, `damageUnarmed`,
  `filterByRacesExcluded`.
- `npc/` configs accept `changeStats` (health, healthmult, calchealth,
  byclassmagicka, byclassstamina), `healthBonus`, `staminaBonus`,
  `magickaBonus`, `levelRange`, `perksToAdd`, `setPcLevelMult`,
  `setAutoCalcStats`, `calcLevelMin/Max`, with filters `filterByRaces`,
  `filterByEditorIdContains`, `filterByClass`, `filterByCombatStyle`,
  `filterByFactionsOr`, `filterByPCLevelMult`.
- `mods\SkyPatcher\SKSE\Plugins\SkyPatcher.ini` already has
  `iEnableNPCPatching=1`, `iEnableRacePatching=1`, `iRefreshNPCStats=1`.

This adds **zero new dependencies and zero adoption risk**, which is why it beats
making a 310-download Synthesis fork the linchpin of the build. The project
already authors SkyPatcher configs (`Ensrick - Cloaks of Skyrim Unique
Placement`).

**SPID cannot do this half.** Its distributable sections, read from the shipped
DLL, are Spell / Perk / Item / Shout / Package / Outfit / SleepOutfit / Keyword /
Faction / Skin / DeathItem. There is no stat channel. KID does keywords.
[MEASURED] SPID *can* gate a perk on actor level
(`LookupFilters.cpp:58`, `LookupConfigs.h:471-481`), which is the technique EEOS
uses - relevant later, not now.

### 5.2 Artifact 1: a SkyPatcher `race/` INI, ~40-60 lines

One `filterByRaces=<Race>:startingHealth=<n>` per creature race, seeded from the
measured vanilla table, correcting the races where vanilla contradicts itself
(`DragonPriestRace` first). This is the only genuinely new authoring in the whole
plan, and it is a data table, not code.

### 5.3 Artifact 2: a SkyPatcher `npc/` INI, ~15-25 lines

`filterByEditorIdContains` entries against the ~101 offset-bearing EditorID
prefixes, scaling or zeroing `healthBonus` on the top tiers. Optionally paired
with a one-record GMST edit setting `fNPCHealthLevelBonus` to 0.

Also in scope for conversion under rule 3: `Ensrick Guard Scaling Patch.esp` is
three `calcLevelMin` values on three NPC template records, built via a Synthesis
generator. Three SkyPatcher `npc/` lines replace it.

### 5.4 Artifact 3, LATER and only if a playthrough says so: a 25-record ESP

If, after playing the rescaled build, the tree tax still bothers you: the whole
structural objection is **25 records, one float and one pointer each**.
`Armsman00` (`0BABE4`) has exactly one effect - `PerkEntryPointModifyValue`,
entry point 35 (attack damage), function 3 (multiply), `EPFT=1`, `EPFD = 1.2` -
plus one `NextPerk` pointer to `079343`. Five families (Armsman, Barbarian,
Overdraw, AgileDefender, Juggernaut) x five ranks. Truncating or flattening those
is a spriggit YAML edit, and it leaves the vanilla enemy capability perks
(656 NPC placements) untouched. [MEASURED]

**[INFERRED / could not determine]** I did **not** decode the entry-point shape
that would make a bonus scale off the skill actor value the way Vokrii's single
Mastery perk does. Flattening or truncating the ladder is one float and one
pointer; making it scale with skill is a different entry-point shape that was not
verified. I also could not determine whether a perk-record edit takes effect on
an existing save without a refund cycle - that needs a launch, which is out of
scope here.

### 5.5 What NOT to build

No generator. No .NET project. No perk overhaul. **No NPC-perk SPID config until
the perk slot is decided** - the perk FormIDs to distribute depend entirely on
which overhaul (if any) wins, and distributing vanilla Armsman/Overdraw would
reproduce the exact "massive bonuses to damage" shape you rejected, on enemies
Bethesda deliberately withheld them from.

---

## 6. Magic-slot foreclosure: only Adamant forces the decision

You are leaning Apocalypse and possibly Odin. Measured, from plugin masters and
record intersections:

- **Adamant forecloses it twice.** `Adamant.esp` hard-masters
  `MysticismMagic.esp`, so installing Adamant fills the magic slot. And Mysticism
  collides with Odin on **353 vanilla records** (112 Spell, 89 MagicEffect), with
  the author writing verbatim: *"I do not recommend combining Mysticism with Odin
  and will not offer support for users who try to do this."* Adamant itself
  collides with Odin on 112 vanilla records (49 Spell) with **no patch on either
  page**. So Adamant does not merely fill the magic slot, it specifically kills
  Odin.
- **Ordinator and Vokrii foreclose nothing.** Both master only Skyrim/Update/DLC,
  both ship as ESP + 2 BSA with no INI/DLL/SPID config, and both have **live
  first-party patches for BOTH Apocalypse and Odin** (Apocalypse-Ordinator fid
  709656, Apocalypse-Vokrii fid 624685, Odin-Ordinator fid 658698, Odin-Vokrii
  fid 664485).
- **Apocalypse is clean against everything.** Shared vanilla records: Vokrii 0,
  Ordinator 2, Adamant 15, Odin 28 - and the Adamant/Odin overlaps are entirely
  injected keyword rows in Update.esm space (`MAG_ScrollType*`, `MAG_StaffType*`,
  `Futhark_InjectedKeyword_*`), the shared cross-author vocabulary block, benign
  by design.
- **No magic overhaul competes for the perk slot.** Odin's 18 PERK records and
  Mysticism's 26 are all internal `ODN_`/`MAG_` controllers with zero vanilla
  skill-tree overrides.
- **If Mysticism ever does arrive**, note it overlaps `Ensrick - Weapon Speed
  Balance` on 7 WEAP records (`MAG_Wrathman*`, `MAG_BoundWeapon*`); Adamant adds
  4 more of the same family. Vokrii, Ordinator, Odin and Apocalypse overlap it on
  **zero**.

**Bottom line: leaving the perk slot empty forecloses nothing.** The only path
that forces an early magic decision is the one that is already blocked.

**Correction to a prior record.** `records/apocalypse-inclusion-principle-2026-09-04.md`
cites the live "Sorcerer - Apocalypse Patch" as evidence that SimonMagus's team
ships code for Apocalypse. The blessing quote stands and reproduces
byte-for-byte, but that patch hard-masters `MysticismMagic.esp` and
`Sorcerer.esp` and is generated by a Synthesis patcher that auto-patches "every
mod in your load order that adds scrolls or staves" - machine-generated
staff/scroll integration, inert in a build with neither mod, not a hand-authored
endorsement. The record's actual load-bearing evidence (zero vanilla overrides,
Dragonborn-only dependency) is untouched.

---

## 7. Adjacent facts worth carrying forward

- **The scaling slot is untouched, not just empty.** grep across all 284
  installed mods for `fNPCHealthLevelBonus`, `iAVDhmsLevelUp` and
  `fLeveledActorMult` returns **zero files**. [MEASURED]
- **A live check worth one console command.** `Ensrick Guard Scaling Patch.esp`
  sets `CalcMinLevel` 20 -> 5 on three guard templates but leaves `DNAM` Health
  at the vanilla level-20 bake of **252**. If the engine recomputes from GMSTs at
  spawn, a level-5 guard is `50 + 50 + 4*8 = 132`; if it reads the DNAM cache,
  guards are still 252. One `getav health` on a low-level Whiterun guard settles
  it, and it determines whether the whole GMST approach works at all. The
  recompute claim is **[INFERRED]** from two third-party sources (Nexus article
  6618 and mod 56121), never verified here.
- **#212 sits under any lethality claim.** `WeaponBalancePatch.esp` is 3,007 WEAP
  records; of 1,567 vanilla overrides, **speed differs on 1,567 and damage on 8**.
  Its undocumented policy is speed-spread compression (dagger 1.3 -> 1.25,
  greatsword 0.7 -> 0.8, battleaxe 0.6/0.7 -> 0.7143/0.7692), which is a DPS
  change: heavy melee +10% to +19%, daggers -4%. Record-level conflict with the
  combat mods is at most one weapon (`IronGreatsword` `01359D`, vs Blade and
  Blunt). [MEASURED]
- **The #87 Scrambled Bugs gate should be decided once, not twice.** It currently
  blocks Adamant and Blade and Blunt with the same evidence.
- **Actively opposed to your model, so nobody proposes them later:**
  [Level Matters](https://www.nexusmods.com/skyrimspecialedition/mods/189613),
  [Dynamic Stat Scaler](https://www.nexusmods.com/skyrimspecialedition/mods/140409),
  [Real Time NPC Stat Scaler](https://www.nexusmods.com/skyrimspecialedition/mods/184693)
  (bakes changes into the save),
  [Dynamic NPC Scaling](https://www.nexusmods.com/skyrimspecialedition/mods/180306)
  (converts static NPCs *into* scaling actors),
  [Skyrim Revamped Rebalanced and Releveled](https://www.nexusmods.com/skyrimspecialedition/mods/27201)
  (Dragon Priests min 60 / max 150 / x1.5), and
  [SkyValor](https://www.nexusmods.com/skyrimspecialedition/mods/106240) (right
  mechanism, wrong numbers: level-1 bandit 300 HP, dragons 3000-7000, and it
  recommends Valhalla Combat and MCO, both hard-filtered here).
- **Dead end, recorded so it is not re-found:** "Diverse Racial Starting Stats
  Skypatched" (170051) returns `status: removed`, `available: false` from the
  API, and its files endpoint 403s.

---

## 8. Honest counterweights to my own recommendation

- **Deferring does not fix the structural objection.** Vanilla's Armsman ladder
  is x2.00 for five points and it is fully live on the player. If you want that
  flattened, something has to change - it just does not have to be an overhaul,
  and section 5.4 is the 25-record version.
- **The ecosystem majority ships one.** Survey line 45: Adamant 9/19, Ordinator
  4/19 + Lexy, Vokrii STEP only, Requiem 3. At most 2 of 19 lists ship none.
  "No overhaul" is a minority position. The countervailing receipt is
  [Eldergleam](https://www.nexusmods.com/skyrimspecialedition/mods/105778) (1,660
  mods), which deliberately ships none "so users can add their own".
- **Adamant genuinely has the cleanest content.** 0 of 491 perks use active-power
  phrasing; 0 hits for teleport/conjure/puddle/rabbit/banner; its Alchemy tree is
  Green Thumb, Purity, Potency, Apothecary, Chemist; its damage ceiling is 80%
  with no figure at or above 100%; and its page states its anti-power-creep
  target numerically ("At 100 Alchemy... equal to Vanilla with 100 skill and all
  perks"). If the Mysticism master and the #87 gate ever clear, it is the one to
  re-examine - accepting that it fills the magic slot and kills Odin. Note also
  that its "twice as much damage" Skirmisher/Barbarian/Marksman records are
  **inert leftovers with zero perk entry points** - 113 of its 491 perks have no
  effects at all, and citing those descriptions against it would be a false
  accusation.

---

## 9. What the refuters struck, explicitly

All three adversarial passes returned `refuted=true`. Corrections applied above:

**Struck from Angle 3 (combat):**
- "bLevelBasedDifficulty is off by default" - **FALSE**, taken from the mod page;
  the shipped `BladeAndBlunt.ini` line 6 reads `true`.
- "BnB Adept stays 1.00/1.00, difficulty comes from armor not damage multipliers"
  - true of the plugin GMSTs, false of the mod as shipped.
- "class Health weight 0-5, so NPCs gain 5-10 HP/level" - UESP prose tagged
  MEASURED; predicts Alvor at 113, the record says 131.
- "level-50 bandit ~490 HP, ~90% level padding" - built on that wrong term and on
  a level encounter zones do not produce.
- "vanilla's size layer is intact and correct; what breaks it is the level term"
  - refuted on its own example: the worst draugr is 910 offset (65%) vs 440 level
  (31%). Angle 3 never mentions `HealthOffset`.
- The 500/1000 armor breakpoints and the 0.03%/point rate - mod-page copy, not
  measurement (the 75/90 caps ARE corroborated by DLL strings).
- "12-15% damage reduction free just for being dressed" - rests on UESP's hidden
  +25/piece, never derived from `fArmorBaseFactor`.
- Blade and Blunt's dependencies were listed but **installed state was never
  checked**.

**Struck from Angle 1 (perks):**
- "Vokrii: 1 of 426 perks uses active-power phrasing" - grep vocabulary too
  narrow; 15 live gimmick perks found, and the single reported hit is a cut
  record.
- "Vokrii's whole One-Handed tree is martial and mundane" - true of that tree,
  used to characterise the mod; the gimmicks live in Lockpicking, Speech,
  Pickpocket, Alteration, Illusion and Restoration.
- "Vokrii does not punish generalists" - 17 perks gated on wearing ALL Heavy or
  ALL Light Armor, against 10 in vanilla (two of those quest rewards).
- Crit ceiling understated: missing Deadly Bash "fifteen times as much damage",
  Torch Bash "ten times", Coup de Grace 10x, Telekinetic Force +500 points.
- "Vokrii is structurally closest to level-buys-capability" - the orphaned-ladder
  topology is **real and confirmed across all 18 trees** (every rank-2 mastery
  has in-degree 0), but the surviving single Mastery perk is +100% damage and
  +500% crit damage at skill 100, against vanilla's largest single rank of +20%.
  The point cost fell 5x; the magnitude did not fall at all.
- Method note: the `_OrdASISExclude` conclusion was correct but was reached from
  a naming convention. It has since been confirmed from `AVOneHanded` tree nodes.

**Struck from Angle 5 / cross-cutting:**
- NPC Stat Rescaler - Synthesis measured at 19 endorsements / 310 downloads and
  recommended anyway, while 498/23,483 was called "the thinnest ecosystem
  currency of anything here". Demoted to optional; SkyPatcher takes its place.
- "Armsman (all 4 ranks)" - Armsman has five ranks; all five are zero.
- Arena's tier scheme was tagged MEASURED but sourced to a STEP/search summary
  with the plugin never opened.
- General rule adopted from this: **an author's statement about his own shipped
  file never carries a MEASURED tag.** The `bLevelBasedDifficulty` case proves a
  page can be wrong about its own default.

**Struck from the framing shared by all four angles:** that #226 requires filling
a "perk slot". Three of your four stated requirements are NPC-scaling facts that
no perk overhaul can address, and every candidate ranking scored the player's
trees while silently rewriting the five vanilla capability perks carried by 656
NPC placements.

**What survived and got stronger:** the Adamant/Mysticism master (measured twice
from the plugin), the fitted health formula (Alvor 131/68/86 exact), the
giant-vs-draugr inversion, the oil perk attribution, and "vanilla withholds flat
damage perks from every NPC" (stronger than reported - rank 1 of every family is
also zero).

---

## 10. Questions only you can answer

1. **Do you want to play the current build first?** That is my recommendation and
   your own stated blocker. If you would rather have something changed before the
   next session, say so and I will land the SkyPatcher scaling configs (sections
   5.2-5.3) as the smallest useful step.
2. **Body-size health table: whose numbers?** The vanilla table is broadly right
   and specifically wrong in places. Do you want me to propose a corrected table
   for you to edit, or would you rather write the target values yourself for the
   dozen races you care about (giant, mammoth, dragon, troll, bear, draugr,
   wolf, skeever)?
3. **Sponges "only for large monsters" - which mechanism?** Smilodon's answer is
   flat damage reduction for giants/dragons/mammoths/centurions rather than a
   bigger health pool. Do you want big monsters to have big health, big damage
   *resistance*, or both?
4. **The `iAVDhmsLevelUp` coupling.** Shrinking NPC class-weighted growth also
   shrinks your own +10 per level-up. Do you want the player's growth reduced
   alongside, or held at vanilla?
5. **#87, Scrambled Bugs.** It blocks Adamant and Blade and Blunt with the same
   evidence, and upstream has been dead since 2023-03-14. Do we keep it parked
   indefinitely, or is finding/building a working 1.7.104 build worth a pass?
6. **"Vanilla Perk Trees Expanded"** returned zero results on a Nexus SSE name
   search. If you had a specific page in mind, a URL resolves it in one call.
7. **When perks do come up again: overhaul, or 25 records?** Section 5.4 flattens
   your exact objection without importing 1,455-5,014 records, a scripted refund
   quest, or a rewrite of the enemy perk layer. Is that the shape you want, or do
   you want the wider content an overhaul brings?

---

**Files touched by this audit:** this record only. Archives went to
`mo2-instances\skyrim-se\downloads\`; extractions to
`skyrim-mod-assistant\records-work\suite-coherence-2026-09-04\` and session
scratchpads, all outside `mods\`. No profile file, no plugin order, no curator
decision, no claim, no commit.
