# Guard scaling record audit - 2026-09-02 (issue #51)

**User rule (verbatim, #51, 2026-08-29):** ordinary hold, city, Imperial and Stormcloak guards
match the player at 1:1 scaling, minimum effective level 5, no +20 level offset; named guards,
captains, commanders, quest actors and mod-added guard equivalents are audited separately.
Report that triggered the work (2026-09-01): "I tried attacking a single guard and it was like
fighting a level 20 at level 1."

## Verdict

The level-20 guard is **vanilla behaviour, not a mod override.** Every ordinary hold and city guard
in the load order takes its stats from one of two Skyrim.esm templates, `EncGuardImperialTemplate`
(0F6F37) and `EncGuardSonsTemplate` (0F6F38), which Bethesda set to *PC level x1.0, calc minimum 20,
maximum 50*. At player level 1 the engine clamps the guard to 20. The only override of those two
records in the profile is USSEP, which forwards the identical level data. No installed mod inflates
guard levels; Sons of Skyrim, its Xtudo fixes and USSEP override the *placed* guard records for
outfits, class and template-flag bits only, never the level fields and never the Stats inheritance.
Raven Rock's Redoran guards (`DLC2RRGuardTemplate`, Dragonborn.esm) carry the same 20-50 rule.

`Ensrick Guard Scaling Patch.esp` overrides those three templates to PC x1.0, min 5, max 50 (cap
kept). Everything else listed below is untouched.

## Method

- Generator: `mods/guard-scaling-patch/generator` (Mutagen 0.54.4 / Synthesis 0.36.6, locked), run through
  the MO2 VFS on profile `Default` with `MO2Headless run`; `--audit` walks every winning NPC_ record,
  collects anything whose EditorID, class or faction looks guard-like, and follows the *Use Stats*
  template chain (NPC_ templates and leveled-NPC templates) to the record whose ACBS the engine reads.
- Load order: 311 active plugins (plugins.txt `*` rows + Skyrim.ccc in loadorder.txt order);
  missing plugins: 0. Candidates collected: 1930 NPC_ records,
  1011 distinct stats-providing records, 256 leveled-NPC templates.
- Receipts: `mods/guard-scaling-patch/work/guard-audit.json` (full dump, every value in this report),
  `work/audit.stdout.log` (MO2 run envelope), `work/effective-loadorder.txt`, and the raw ACBS byte parse
  in the last section (independent of Mutagen).

## 1. The records that set ordinary guard levels (patched)

| record | vanilla (Skyrim.esm / DLC) | current winner | winner's value | patch sets | placed guards resolving here |
|---|---|---|---|---|---|
| `EncGuardImperialTemplate` (0F6F37:Skyrim.esm) | PC x1, min 20, max 50 (Skyrim.esm) | unofficial skyrim special edition patch.esp | PC x1, min 20, max 50 | PC x1, min 5, max kept (50) | 245 |
| `EncGuardSonsTemplate` (0F6F38:Skyrim.esm) | PC x1, min 20, max 50 (Skyrim.esm) | unofficial skyrim special edition patch.esp | PC x1, min 20, max 50 | PC x1, min 5, max kept (50) | 209 |
| `DLC2RRGuardTemplate` (0195AF:Dragonborn.esm) | PC x1, min 20, max 50 (Dragonborn.esm) | Dragonborn.esm | PC x1, min 20, max 50 | PC x1, min 5, max kept (50) | 17 |

Override chains (load order, every plugin that touches the record):

- `EncGuardImperialTemplate`: Skyrim.esm [PC x1, min 20, max 50; template flags: Traits, Factions, AIData, AIPackages, BaseData, Inventory, Script, DefPackList, AttackData, Keywords] -> unofficial skyrim special edition patch.esp [PC x1, min 20, max 50; template flags: Traits, Factions, AIData, AIPackages, BaseData, Inventory, Script, DefPackList, AttackData, Keywords]
- `EncGuardSonsTemplate`: Skyrim.esm [PC x1, min 20, max 50; template flags: Traits, Factions, AIData, AIPackages, BaseData, Inventory, Script, DefPackList, AttackData, Keywords] -> unofficial skyrim special edition patch.esp [PC x1, min 20, max 50; template flags: Traits, Factions, AIData, AIPackages, BaseData, Inventory, Script, DefPackList, AttackData, Keywords]
- `DLC2RRGuardTemplate`: Dragonborn.esm [PC x1, min 20, max 50; template flags: 0]

Class, combat style and factions the patch relies on (winner's values, forwarded unchanged):

| record | class | combat style | factions (rank) | ACBS flags |
|---|---|---|---|---|
| `EncGuardImperialTemplate` | CWSoldierClass | csHumanMeleeLvl2 | CrimeFactionImperial (-1), CWDialogueSoldierFaction (-1), CWImperialFaction (-1), CWImperialFactionNPC (-1), CWSoldierNoGuardDialogueFaction (1), IsGuardFaction (-1) | AutoCalcStats, LoopedScript, LoopedAudio |
| `EncGuardSonsTemplate` | CWSoldierClass | csHumanMeleeLvl2 | CrimeFactionSons (-1), CWDialogueSoldierFaction (-1), CWSoldierNoGuardDialogueFaction (1), CWSonsFaction (-1), CWSonsFactionNPC (-1), GuardDialogueFaction (-1), IsGuardFaction (-1) | AutoCalcStats, LoopedScript, LoopedAudio |
| `DLC2RRGuardTemplate` | CWSoldierClass | csHumanMeleeLvl2 | DLC2CrimeRavenRockFaction (0), DLC2RavenRockGuardFaction (0), IsGuardFaction (0), DLC2RRBulwarkFaction (0) | Respawn, AutoCalcStats, Protected |

## 2. How a placed guard reaches the template

`GuardWhiterunImperialPatrolDay` (0267EE:Skyrim.esm, winner Skyrim.esm) has template flags
`Traits, Stats, Factions, SpellList, AIData, ModelAnimation, BaseData, Inventory, Script, DefPackList, AttackData`, so its level comes from its template. The chain the audit followed:

```
NPC_ 0EA0A2:Skyrim.esm GuardWhiterunImperialTemplate -> NPC_ 01FC62:Skyrim.esm LvlGuardImperial -> LVLN 0E7B2C:Skyrim.esm LCharGuardImperial @1 -> NPC_ 0AA8D4:Skyrim.esm EncGuardImperialM01MaleNordCommander -> NPC_ 0F6F37:Skyrim.esm EncGuardImperialTemplate
```

`LCharGuardImperial` / `LCharGuardSons` are leveled-NPC lists whose entries are all at level 1 and
differ only by voice and face; every leaf inherits Stats from the two Enc templates.

Placed vanilla guard records (EditorID `Guard*`): 301. Stats providers among them:

| provider | placed guard records |
|---|---|
| `EncGuardSonsTemplate` | 155 |
| `EncGuardImperialTemplate` | 142 |
| `EncSoldierImperialTemplate` | 2 |
| `GuardWinterholdCollege` | 1 |
| `GuardWhiterunCityGeneric3dnpc` | 1 |

Plugins overriding those placed guard records, and what they change relative to Skyrim.esm:

| plugin | records overridden | level fields changed | template changed | Stats inheritance changed | template-flag bits changed | class changed |
|---|---|---|---|---|---|---|
| NW_Sons_of_Skyrim.esp | 142 | 0 | 0 | 0 | 89 | 95 |
| unofficial skyrim special edition patch.esp | 87 | 0 | 0 | 0 | 58 | 59 |
| NW_Sons_of_Skyrim - My fixes by Xtudo.esp | 40 | 0 | 0 | 0 | 25 | 22 |
| cutting room floor.esp | 1 | 1 | 0 | 0 | 0 | 0 |

Stats-inheritance or template changes across all overrides: 0. The one level change is
Cutting Room Floor on `GuardWinterholdCollege` (fixed L40 -> PC x1, 20-50), see section 4.

## 3. Named or essential actors that inherit stats from a patched template (affected, not edited)

| actor | name | flags | inherits from | winner |
|---|---|---|---|---|
| `ccBGSSSE058_AldepiusImperial` (00081E:ccbgssse058-ba_steel.esl) | Aldepius | Essential | EncGuardImperialTemplate | ccbgssse058-ba_steel.esl |
| `ccBGSSSE058_AldepiusSons` (000824:ccbgssse058-ba_steel.esl) | Aldepius | Essential | EncGuardSonsTemplate | ccbgssse058-ba_steel.esl |
| `DLC2PillarRRGuardC` (03CA53:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2PillarRRGuardB` (03CA52:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2PillarRRGuardA` (03CA51:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardTunnel` (033D11:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardPatrolBulwark02` (033D0D:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardPatrolBulwark` (033D09:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardBarracks` (0195B7:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardJail` (0195B6:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardPatrol` (0195B5:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardMarketExterior` (0195B4:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardGateExterior` (0195B3:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardTempleExterior` (0195B2:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardMorvaynManorExterior` (0195B1:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardMorvaynManorInterior` (0195B0:Dragonborn.esm) | None | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |
| `DLC2RRGuardTemplate` (0195AF:Dragonborn.esm) | Redoran Guard | Respawn, AutoCalcStats, Protected | DLC2RRGuardTemplate | Dragonborn.esm |

## 4. Excluded from the patch (listed in policy.json with the reason)

| record | name | current level rule | winner | reason |
|---|---|---|---|---|
| `GuardWinterholdCollege` (105CBB:Skyrim.esm) | College Guard | PC x1, min 20, max 50 | cutting room floor.esp | winner is Cutting Room Floor (vanilla fixed L40 -> CRF PCx1 [20-50]); CRF requires advance permission for compatibility patches (#71), so this patch keeps CRF out of its masters. One respawning College Guard stays at CRF's rule; tracked separately. |
| `EncSoldierImperialTemplate` (01FC5D:Skyrim.esm) | Imperial Soldier | PC x0.25, min 1, max 50 | Skyrim.esm | Imperial camp/fort soldier family, not a guard; PCx0.25 [1-50] in vanilla and already below the rule |
| `EncSoldierSonsTemplate` (027498:Skyrim.esm) | Stormcloak Soldier | PC x0.25, min 1, max 50 | NW_Sons_of_Skyrim.esp | Stormcloak camp/fort soldier family, not a guard; PCx0.25 [1-50] in vanilla (Sons of Skyrim forwards it unchanged) |
| `EncSiegeImperialArcherTemplate` (045BE0:Skyrim.esm) | Imperial Archer | PC x1, min 3, max 0 | Skyrim.esm | civil-war siege actor, not a guard; PCx1 [3-0] |
| `EncSiegeSonsArcherTemplate` (045BE4:Skyrim.esm) | Stormcloak Archer | PC x1, min 3, max 20 | NW_Sons_of_Skyrim.esp | civil-war siege actor, not a guard; PCx1 [3-20] |
| `CommanderCaius` (038257:Skyrim.esm) | Commander Caius | fixed L10 (calc 0-0) | unofficial skyrim special edition patch.esp | named guard commander, owns his stats (fixed L10) |
| `CaptainAldis` (041FB8:Skyrim.esm) | Captain Aldis | PC x1, min 5, max 15 | Skyrim.esm | named guard captain, owns his stats (PCx1 [5-15]) |
| `CaptainMetilius` (01C9F7:Skyrim.esm) | Captain Metilius | PC x0.8, min 10, max 30 | cutting room floor.esp | named captain, owns his stats (PCx0.8 [10-30], CRF winner) |
| `CommanderMaro` (01D4B5:Skyrim.esm) | Commander Maro | PC x1, min 10, max 30 | unofficial skyrim special edition patch.esp | named Penitus Oculatus commander, quest actor |
| `Sinmir` (0813B5:Skyrim.esm) | Sinmir | fixed L4 (calc 0-0) | Skyrim.esm | named actor, owns his stats |
| `DLC2RRModynVeleth` (0182AC:Dragonborn.esm) | Captain Veleth | PC x1, min 25, max 50 | unofficial skyrim special edition patch.esp | named Redoran captain, owns his stats (PCx1 [25-50]) |
| `ccBGSSSE058_AldepiusImperial` (00081E:ccbgssse058-ba_steel.esl) | Aldepius | fixed L1 (calc 0-0) | ccbgssse058-ba_steel.esl | Creation Club quest actor; not edited, but note he inherits stats from EncGuardImperialTemplate and therefore follows the new rule |
| `ccBGSSSE058_AldepiusSons` (000824:ccbgssse058-ba_steel.esl) | Aldepius | fixed L1 (calc 0-0) | ccbgssse058-ba_steel.esl | Creation Club quest actor; inherits stats from EncGuardSonsTemplate and therefore follows the new rule |
| `CYREncGuardImperialTemplate` (08C29F:BSHeartland.esm) | None | PC x1, min 15, max 50 | BSHeartland.esm | mod-added (Beyond Skyrim: Bruma) guard template, PCx1 [15-50]; audited separately |
| `CYREncGuardTemplate` (001973:BSHeartland.esm) | Guard | PC x1, min 0, max 0 | BSHeartland.esm | mod-added (Bruma) guard template, PCx1 [0-0]; audited separately |
| `GuardWhiterunCityGeneric3dnpc` (2616FF:3DNPC.esp) | Corpse | fixed L1 (calc 0-0) | 3DNPC.esp | Interesting NPCs corpse placeholder, fixed L1 |
| `WSStormGateGuard` (A69726:Grand Solitude - The Walls of High King Erling.esp) | Solitude Guard | fixed L1 (calc 0-0) | Grand Solitude - The Walls of High King Erling.esp | mod-added 'Solitude Guard' with CK-default class and fixed L1; audited separately (flagged as an outlier) |

## 5. Named vanilla guard-faction actors that own their stats (untouched)

Unique actors carrying a guard faction whose ACBS is their own (no Stats inheritance):

| actor | name | level rule | winner |
|---|---|---|---|
| `DLC2RRModynVeleth` (0182AC:Dragonborn.esm) | Captain Veleth | PC x1, min 25, max 50 | unofficial skyrim special edition patch.esp |
| `UrzogaGraShugurz` (0133BE:Skyrim.esm) | Urzoga gra-Shugurz | PC x1.2, min 20, max 50 | Skyrim.esm |
| `Murbul` (013B7A:Skyrim.esm) | Murbul | fixed L10 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Arob` (013B7B:Skyrim.esm) | Arob | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Gharol` (013B7C:Skyrim.esm) | Gharol | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Shel` (013B7D:Skyrim.esm) | Shel | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Umurn` (013B7E:Skyrim.esm) | Umurn | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Nagrub` (013B7F:Skyrim.esm) | Nagrub | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Oglub` (013B80:Skyrim.esm) | Oglub | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Ghorbash` (013B81:Skyrim.esm) | Ghorbash the Iron Hand | PC x1, min 10, max 30 | Unofficial Skyrim Modders Patch.esp |
| `C06KodlaksGhost` (01720B:Skyrim.esm) | None | via KodlakWhitemane | Skyrim.esm |
| `Sharamph` (019953:Skyrim.esm) | Sharamph | fixed L10 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Bagrak` (019955:Skyrim.esm) | Bagrak | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Shuftharz` (019957:Skyrim.esm) | Shuftharz | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Borgakh` (019959:Skyrim.esm) | Borgakh the Steel Heart | PC x1, min 10, max 30 | Unofficial Skyrim Modders Patch.esp |
| `Olur` (01995B:Skyrim.esm) | Olur | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Atub` (019E18:Skyrim.esm) | Atub | PC x1, min 10, max 30 | unofficial skyrim special edition patch.esp |
| `Ugor` (019E1A:Skyrim.esm) | Ugor | PC x1, min 10, max 30 | Unofficial Skyrim Modders Patch.esp |
| `Garakh` (019E1C:Skyrim.esm) | Garakh | fixed L6 (calc 6-30) | unofficial skyrim special edition patch.esp |
| `Lob` (019E1E:Skyrim.esm) | Lob | PC x1, min 10, max 30 | Unofficial Skyrim Modders Patch.esp |
| `Gularzob` (019E20:Skyrim.esm) | Gularzob | fixed L6 (calc 6-30) | unofficial skyrim special edition patch.esp |
| `Ogol` (019E22:Skyrim.esm) | Ogol | PC x1, min 10, max 30 | Unofficial Skyrim Modders Patch.esp |
| `KodlakWhitemane` (01A68E:Skyrim.esm) | Kodlak Whitemane | PC x1.1, min 10, max 50 | Skyrim.esm |
| `Skjor` (01A690:Skyrim.esm) | Skjor | PC x1, min 10, max 50 | Skyrim.esm |
| `Farkas` (01A692:Skyrim.esm) | Farkas | PC x1, min 8, max 50 | Unofficial Skyrim Modders Patch.esp |
| `Vilkas` (01A694:Skyrim.esm) | Vilkas | PC x1, min 8, max 50 | Unofficial Skyrim Modders Patch.esp |
| `AelaTheHuntress` (01A696:Skyrim.esm) | Aela the Huntress | PC x1, min 8, max 50 | Unofficial Skyrim Modders Patch.esp |
| `Bolar` (01B076:Skyrim.esm) | Bolar | fixed L10 (calc 6-30) | Skyrim.esm |
| `Yatul` (01B077:Skyrim.esm) | Yatul | fixed L6 (calc 1-30) | unofficial skyrim special edition patch.esp |
| `Urog` (01B078:Skyrim.esm) | Urog | fixed L6 (calc 1-30) | unofficial skyrim special edition patch.esp |
| `Dushnamub` (01B079:Skyrim.esm) | Dushnamub | fixed L6 (calc 6-30) | unofficial skyrim special edition patch.esp |
| `MulGroLargash` (01B07A:Skyrim.esm) | Mul gro-Largash | fixed L6 (calc 1-30) | unofficial skyrim special edition patch.esp |
| `GadbaGroLargash` (01B09A:Skyrim.esm) | Gadba gro-Largash | fixed L6 (calc 6-30) | unofficial skyrim special edition patch.esp |
| `CommanderCaius` (038257:Skyrim.esm) | Commander Caius | fixed L10 (calc 0-0) | unofficial skyrim special edition patch.esp |
| `Yamarz` (03BC26:Skyrim.esm) | Chief Yamarz | PC x1, min 6, max 20 | unofficial skyrim special edition patch.esp |
| `Sinmir` (0813B5:Skyrim.esm) | Sinmir | fixed L4 (calc 0-0) | Skyrim.esm |
| `C04DeadKodlak` (0AD3A5:Skyrim.esm) | None | via KodlakWhitemane | Skyrim.esm |
| `Mahk` (0C78BE:Skyrim.esm) | Mahk | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Dulug` (0C78C0:Skyrim.esm) | Dulug | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Ghak` (0C78C2:Skyrim.esm) | Ghak | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Gul` (0C78CA:Skyrim.esm) | Gul | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Ghamorz` (0C78CC:Skyrim.esm) | Ghamorz | fixed L6 (calc 15-30) | unofficial skyrim special edition patch.esp |
| `Mogdurz` (0C78DF:Skyrim.esm) | Mogdurz | fixed L6 (calc 1-30) | unofficial skyrim special edition patch.esp |
| `Bor` (0C78E1:Skyrim.esm) | Bor | fixed L6 (calc 6-30) | unofficial skyrim special edition patch.esp |
| `C06DeadKodlak` (0DCCC0:Skyrim.esm) | None | via KodlakWhitemane | Skyrim.esm |
| `Uglarz` (0E316F:Skyrim.esm) | Uglarz | fixed L15 (calc 0-0) | cutting room floor.esp |

## 6. Vanilla soldier and other uniformed families (not guards, untouched)

| template | name | level rule | winner | users |
|---|---|---|---|---|
| `EncSoldierImperialTemplate` (01FC5D:Skyrim.esm) | Imperial Soldier | PC x0.25, min 1, max 50 | Skyrim.esm | 157 |
| `EncPenitus00Template` (07D98C:Skyrim.esm) | Penitus Oculatus Agent | fixed L1 (calc 0-0) | Skyrim.esm | 28 |
| `EncDawnguard01TemplateMelee` (01421F:Dawnguard.esm) | None | fixed L1 (calc 0-0) | Dawnguard.esm | 25 |
| `EncDawnguard02TemplateMelee` (014220:Dawnguard.esm) | None | fixed L5 (calc 0-0) | Dawnguard.esm | 25 |
| `EncDawnguard03TemplateMelee` (014221:Dawnguard.esm) | None | fixed L9 (calc 0-0) | Dawnguard.esm | 25 |
| `EncDawnguard04TemplateMelee` (014222:Dawnguard.esm) | None | fixed L14 (calc 14-0) | Dawnguard.esm | 25 |
| `EncDawnguard05TemplateMelee` (014223:Dawnguard.esm) | None | fixed L19 (calc 0-0) | Dawnguard.esm | 25 |
| `EncDawnguard06TemplateMelee` (014224:Dawnguard.esm) | None | fixed L25 (calc 0-0) | Dawnguard.esm | 25 |
| `EncThalmor00MissileTemplate` (0728AC:Skyrim.esm) | Thalmor Soldier | fixed L4 (calc 0-0) | Skyrim.esm | 5 |
| `EncThalmor00WizardTemplate` (0728AD:Skyrim.esm) | Thalmor Wizard | fixed L4 (calc 0-0) | Skyrim.esm | 5 |
| `EncSiegeSonsArcherTemplate` (045BE4:Skyrim.esm) | Stormcloak Archer | PC x1, min 3, max 20 | NW_Sons_of_Skyrim.esp | 4 |
| `EncThalmor00MeleeTemplate` (02B124:Skyrim.esm) | Thalmor Soldier | fixed L4 (calc 0-0) | Skyrim.esm | 3 |
| `EncSiegeImperialArcherTemplate` (045BE0:Skyrim.esm) | Imperial Archer | PC x1, min 3, max 0 | Skyrim.esm | 3 |
| `EncSoldierSonsTemplate` (027498:Skyrim.esm) | Stormcloak Soldier | inherits Stats (PC x0.25, min 1, max 50 on record) | NW_Sons_of_Skyrim.esp | - |

Penitus Oculatus, Thalmor and Dawnguard use fixed per-tier levels (L1-L25 tiers) picked by leveled lists;
Imperial and Stormcloak soldiers scale at PC x0.25 from level 1. None of these is a hold guard and none
is above the user's rule, so none is edited.

## 7. Mod-added guard equivalents (audited, untouched)

Non-unique stats providers from non-vanilla plugins whose EditorID, class or faction is guard-like.
Levels are the winner's; `users` = candidate NPC_ records resolving to that provider.

### arnima.esm (100 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `ArnimaBloodySkeletonGuard` | Cursed Soul | PC x0.9, min 1, max 50 | Respawn, AutoCalcStats | 1 |
| `ArnimaImperialsoldier2OrcQ` | Imperial Soldier | PC x1, min 5, max 30 | AutoCalcStats | 1 |
| `ArnimaImperialsoldier3officerOrcQ` | Imperial Officer | PC x1, min 25, max 50 | AutoCalcStats | 1 |
| `ArnimaInncust3` | Inn Patron | fixed L6 (calc 5-25) | Female, AutoCalcStats | 1 |
| `ArnimaInncust4` | Inn Patron | fixed L6 (calc 5-25) | Female, AutoCalcStats | 1 |
| `ArnimaInncustomer1` | Inn Patron | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaInncustomer2` | Inn Patron | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaInncustomer3` | Inn Patron | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaInncustomer4` | Inn Patron | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaMQ14ReserveGuard` | Evermore Reservist Guard | PC x1.5, min 25, max 75 | AutoCalcStats | 1 |
| `ArnimaMQ14ReserveGuard2` | Evermore Reservist Guard | PC x1.5, min 25, max 75 | AutoCalcStats | 1 |
| `ArnimaSerf3` | Serf | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaSerf4` | Serf | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaShamanQuestMumGhost` | Kitye | fixed L6 (calc 5-25) | Female, AutoCalcStats, Invulnerable | 1 |
| `ArnimaTownDwellerDivideHang` | Town Dweller | fixed L4 (calc 0-0) | Respawn, AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `ArnimaTownLabourer` | Labourer | fixed L4 (calc 0-0) | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| ... 84 more in guard-audit.json | | | | |

### Vigilant.esm (33 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `zzzCHEncBelharzaGuard01` | Belharza's Royal Guard | fixed L30 (calc 12-17) | Respawn, AutoCalcStats | 5 |
| `zzzCHEncBelharzaGuard02` | None | fixed L35 (calc 12-17) | Respawn, AutoCalcStats | 5 |
| `zzzCHEncBelharzaGuard03` | None | fixed L40 (calc 12-17) | Respawn, AutoCalcStats | 5 |
| `zzzCHEncBelharzaGuard04` | None | fixed L45 (calc 12-17) | Respawn, AutoCalcStats | 5 |
| `zzzCHEncBelharzaGuard05` | None | fixed L50 (calc 12-17) | Respawn, AutoCalcStats | 5 |
| `zzzCHEncBelharzaGuard06` | None | fixed L55 (calc 12-17) | Respawn, AutoCalcStats | 5 |
| `zzzCHEncAmielGuard1H01` | None | fixed L40 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard1H02` | None | fixed L45 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard1H03` | None | fixed L50 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard1H04` | None | fixed L55 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard1H05` | None | fixed L60 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard2H01` | None | fixed L45 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard2H02` | None | fixed L50 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard2H03` | None | fixed L55 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard2H04` | None | fixed L60 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| `zzzCHEncAmielGuard2H05` | None | fixed L65 (calc 5-10) | Respawn, AutoCalcStats | 2 |
| ... 17 more in guard-audit.json | | | | |

### Wyrmstooth.esp (21 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `WTFortValusDayShift` | Fort Valus Guard | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| `WTFortValusNightShift` | Fort Valus Guard | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| `WTLvlCragwaterMarauderGateGuard` | Marauder Gate Guard | PC x1.1, min 5, max 40 | AutoCalcStats | 1 |
| `WTMoonwatchFortCommander` | Fort Commander | PC x1, min 25, max 50 | AutoCalcStats | 1 |
| `WTSoldierCamp` | Imperial Soldier | PC x1, min 10, max 25 | AutoCalcStats | 1 |
| `WTSoldierChillwater` | Imperial Soldier | PC x1, min 10, max 25 | AutoCalcStats | 1 |
| `WTSoldierDayShiftA` | Imperial Guard | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| `WTSoldierDayShiftB` | Imperial Guard | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| `WTSoldierDayShiftC` | Imperial Guard | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| `WTSoldierDragonBattleCartDriver` | Imperial Soldier | PC x1, min 10, max 25 | AutoCalcStats | 1 |
| `WTSoldierDragonBattleCartRider` | Imperial Soldier | PC x1, min 10, max 25 | AutoCalcStats | 1 |
| `WTSoldierDragonBattleMage1` | Imperial Mage | PC x1, min 10, max 25 | AutoCalcStats | 1 |
| `WTSoldierDragonBattleMage2` | Imperial Mage | PC x1, min 10, max 25 | Female, AutoCalcStats, OppositeGenderAnims | 1 |
| `WTSoldierDragonBattleSoldier` | Imperial Soldier | PC x1, min 10, max 25 | AutoCalcStats | 1 |
| `WTSoldierGronndalGrove` | Imperial Soldier | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| `WTSoldierMoonwatch` | Imperial Soldier | PC x1, min 10, max 25 | Respawn, AutoCalcStats | 1 |
| ... 5 more in guard-audit.json | | | | |

### BSHeartland.esm (15 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `CYREncSoldierImperialTemplate` | Imperial Soldier | PC x1, min 6, max 50 | AutoCalcStats, LoopedScript, LoopedAudio | 37 |
| `CYRFortPalePassMS01JailbreakReinforcementStormcloak01` | Stormcloak Breakaway | PC x1.5, min 18, max 50 | AutoCalcStats | 2 |
| `CYRFortPalePassMS01JailbreakReinforcementStormcloak02` | Stormcloak Breakaway | PC x1.5, min 18, max 50 | Female, AutoCalcStats | 2 |
| `CYRFortPalePassMS01JailbreakReinforcementStormcloak03` | Stormcloak Breakaway | PC x1.5, min 18, max 50 | AutoCalcStats | 2 |
| `CYREncGuardImperialTemplate` | None | PC x1, min 15, max 50 | AutoCalcStats, LoopedScript, LoopedAudio | 1 |
| `CYREncGuardTemplate` | Guard | PC x1, min 0, max 0 | AutoCalcStats | 1 |
| `CYRGuardBrumaGreatHallDay4Count` | Bruma Guard | PC x1.2, min 30, max 70 | Respawn, AutoCalcStats | 1 |
| `CYRGuardBrumaGreatHallDay5Count` | Bruma Guard | PC x1.2, min 30, max 70 | Respawn, AutoCalcStats | 1 |
| `CYRGuardBrumaLordsManorDay1` | Bruma Guard | PC x1.2, min 30, max 70 | Respawn, AutoCalcStats | 1 |
| `CYRGuardBrumaLordsManorDay2` | Bruma Guard | PC x1.2, min 30, max 70 | Respawn, AutoCalcStats | 1 |
| `CYRGuardBrumaLordsManorTreasureRoom` | Bruma Guard | PC x1.2, min 30, max 70 | Respawn, AutoCalcStats | 1 |
| `CYRLegionnaireCentosDurius` | Legionnaire Centos Durius | PC x1.7, min 30, max 70 | AutoCalcStats | 1 |
| `CYRTreasImperialMaleGuard_HauntedMine_Corpse_19` | Cidinroy Pevagan | fixed L1 (calc 0-0) | Respawn, AutoCalcStats | 1 |
| `CYRTreasImperialMaleGuard_HauntedMine_Ghost_19` | Cidinroy Pevagan | fixed L50 (calc 0-0) | Respawn, AutoCalcStats | 1 |
| `CYRWERoad03HighRockBodyguard` | Bodyguard | PC x1, min 10, max 40 | AutoCalcStats | 1 |

### 3DNPC.esp (6 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `GabaniaGuardMeleeTemplate` | Guard | PC x1.25, min 5, max 40 | Respawn, AutoCalcStats, LoopedScript, LoopedAudio | 14 |
| `GabaniaGuardMissileTemplate` | Guard | PC x1.25, min 5, max 40 | Respawn, AutoCalcStats, LoopedScript, LoopedAudio | 8 |
| `GuardWhiterunCityGeneric3dnpc` | Corpse | fixed L1 (calc 0-0) | 0 | 1 |
| `RothvineGuard3DNPC` | Guard | PC x1, min 0, max 25 | Female, AutoCalcStats | 1 |
| `RothvineGuard3DNPC_Male` | Guard | PC x1, min 0, max 25 | AutoCalcStats | 1 |
| `RothvineGuard3DNPC_Missile` | Guard | PC x1, min 0, max 25 | AutoCalcStats | 1 |

### ccasvsse001-almsivi.esm (6 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `ccASVSSE001_MaskBuyer` | Buyer | PC x1, min 4, max 100 | AutoCalcStats | 1 |
| `ccASVSSE001_OrdinatorGuard` | Ordinator | fixed L1 (calc 0-0) | 0 | 1 |
| `ccASVSSE001_OrdinatorGuardBarracks` | Ordinator | PC x1, min 0, max 0 | AutoCalcStats | 1 |
| `ccASVSSE001_OrdinatorGuardFemale` | Ordinator | fixed L1 (calc 0-0) | Female, OppositeGenderAnims | 1 |
| `ccASVSSE001_OrdinatorGuardMale` | Ordinator | fixed L1 (calc 0-0) | 0 | 1 |
| `ccASVSSE001_OrdinatorGuardPatrolFemale` | Ordinator | fixed L1 (calc 0-0) | Female, OppositeGenderAnims | 1 |

### BSAssets.esm (2 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `EncOgre05MorKhazgur` | Ogre Guard | fixed L35 (calc 10-0) | Respawn, AutoCalcStats, LoopedAudio | 3 |
| `EncOgre03Stronghold` | Ogre Guard | fixed L30 (calc 10-0) | Respawn, AutoCalcStats, LoopedAudio | 1 |

### ccbgssse058-ba_steel.esl (2 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `ccBGSSSE058_GuardDragonBridgeImperial` | Guard | fixed L1 (calc 0-0) | 0 | 1 |
| `ccBGSSSE058_GuardDragonBridgeSons` | Guard | fixed L1 (calc 0-0) | 0 | 1 |

### PROTEUS.esp (1 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `ZZDLC1EncGargoyle` | Gargoyle Brute | PC x1, min 1, max 500 | AutoCalcStats, UseTemplate, LoopedAudio | 1 |

### moonpath.esp (1 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `anvil_sabretiger_guard` | Pahmar Guard | fixed L6 (calc 0-0) | Respawn, AutoCalcStats, SimpleActor | 1 |

### Grand Solitude - The Walls of High King Erling.esp (1 providers)

| record | name | level rule | flags | users |
|---|---|---|---|---|
| `WSStormGateGuard` | Solitude Guard | fixed L1 (calc 0-0) | 0 | 1 |

Outliers worth a look, none edited by this patch: `WSStormGateGuard` (Grand Solitude, 'Solitude Guard',
fixed level 1, CK-default class) and the Creation Club Steel armour Dragon Bridge guards
(`ccBGSSSE058_GuardDragonBridge*`, fixed level 1). Bruma guards run PC x1 from 15 (`CYREncGuardImperialTemplate`)
and PC x1.2 from 30 (`CYRGuardBruma*`); Wyrmstooth guards PC x1 10-25; Beyond Reach guards PC x1.5 25-75.

## 8. Independent receipt: raw ACBS bytes

Decoded by `report.py` straight from the plugin files (record walk + zlib, no Mutagen). `levelRaw` is the
ACBS level field (x1000 when the PC Level Mult flag 0x80 is set).

| plugin | file sha256 | record | pcLevelMult | levelRaw | mult | calcMin | calcMax | template flags | Use Stats |
|---|---|---|---|---|---|---|---|---|---|
| Skyrim.esm | `E198C3B85E5E48E0...` | 01FC5D `EncSoldierImperialTemplate` | True | 250 | 0.25 | 1 | 50 | 0x0000 | False |
| Skyrim.esm | `E198C3B85E5E48E0...` | 027498 `EncSoldierSonsTemplate` | True | 250 | 0.25 | 1 | 50 | 0x001A | True |
| Skyrim.esm | `E198C3B85E5E48E0...` | 0F6F37 `EncGuardImperialTemplate` | True | 1000 | 1.0 | 20 | 50 | 0x1FB5 | False |
| Skyrim.esm | `E198C3B85E5E48E0...` | 0F6F38 `EncGuardSonsTemplate` | True | 1000 | 1.0 | 20 | 50 | 0x1FB5 | False |
| Skyrim.esm | `E198C3B85E5E48E0...` | 105CBB `GuardWinterholdCollege` | False | 40 | None | 0 | 0 | 0x0851 | False |
| Dragonborn.esm | `635F21A938A17B86...` | 0195AF `DLC2RRGuardTemplate` | True | 1000 | 1.0 | 20 | 50 | 0x0000 | False |
| unofficial skyrim special edition patch.esp | `7D7CEA13683EFF2C...` | 0F6F37 `EncGuardImperialTemplate` | True | 1000 | 1.0 | 20 | 50 | 0x1FB5 | False |
| unofficial skyrim special edition patch.esp | `7D7CEA13683EFF2C...` | 0F6F38 `EncGuardSonsTemplate` | True | 1000 | 1.0 | 20 | 50 | 0x1FB5 | False |
| cutting room floor.esp | `AD30BABF608A6986...` | 105CBB `GuardWinterholdCollege` | True | 1000 | 1.0 | 20 | 50 | 0x0851 | False |

## 9. Patch build

- `Ensrick Guard Scaling Patch.esp` v0.1.0: sha256 `686A3A857AFF1884E6DDC3ACAE687B1AE99DA2339DCB55F4BAA43B94DBDAA01C`, 3488 bytes, 3 NPC_ overrides,
  2 byte-identical generations, 73 links checked / 0 unresolved,
  Spriggit tree `A01DDEBBEFC30C972A835401BEAE3137F50C56FDE21DA80666F0DA12FA98D80D`, archive sha256 `29AC6B7E42DA9204949C6157E1EB4829A478B245E7B895F9D6D09CD02B5B5D14`.
- Inputs: effective load order 311 entries (`DE16F9103CEB2A39D68DE526DE45A5CFE3B4284A00053BDDE8D29A48485A23D7`),
  plugins.txt `EB2B8FAF7D284716820FC6E8A04C5074C9181B48CFAA224091A8F188EAFFF0A1`, policy.json `786D00F0B78266530AB4A79DCA336E4ACF75F84B2F5862FA26FBBF30769E0FF9`.

Generated 2026-09-01T23:36:32-05:00 by `mods/guard-scaling-patch/report.py`.
