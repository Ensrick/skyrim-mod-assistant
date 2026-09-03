# Cloak layer install

Install date: 2026-09-02, 18:39-18:41 local (UTC-5).

Runtime: Skyrim SE `1.7.104.0` / SKSE `2.3.1`. MO2 instance
`mo2-instances\skyrim-se`, profile `Default`.

Authorisation: the user, 2026-09-02, *"Yeah, go ahead, and install"*, on the
stack in `records/cloak-layer-audit-2026-09-02.md` §"Recommended stack".
Work claim held by `claude-cloak` for the whole batch and released at the end.

**Verification status: UNVERIFIED.** No launch was performed - the user asked to
hold it. This batch joins Run For Your Lives 4.0.7 and the two dialogue mods in
the queue for the next `audit/launch_verify.py` run.

---

## What landed

Eight MO2 mods, seven Nexus ids, four new plugins. Ledger rows in
`records/installed-mods.json`, each carrying a `note` that states what was
omitted and why.

| # | MO2 mod | Nexus | file | version | size | transaction | plugins |
|---|---|---:|---:|---|---:|---|---|
| 1 | Cloaks of Skyrim | 6369 | 18422 | 1.2.1 | 75.63 MB | `20260902T233922427Z-ad3dd7aa5a6c` | **none** |
| 2 | ElSopa - Cloaks of Skyrim Retextured 2K | 42558 | 170809 | 1.0 | 191.12 MB | `20260902T233936333Z-fa06bbdb5efe` | none |
| 3 | ElSopa - Cloaks of Skyrim Retextured Mesh Update 1.2 | 42558 | 263634 | 1.2 | 0.32 MB | `20260902T233952259Z-780376765150` | none |
| 4 | Cloaks of Skyrim Retextured - Female Mesh Patch | 85932 | 363920 | 1.0.0 | 0.05 MB | `20260902T233957487Z-77c5e90e6553` | none |
| 5 | RMB SPCH - Cloaks of Skyrim | 116030 | 749413 | 1.5.3 | 0.03 MB | `20260902T234003286Z-42b8ec555365` | `Cloaks - RMB SPCH.esp` |
| 6 | More Scarves | 149259 | 723968 | 1.4.0 | 95.6 MB | `20260902T234010569Z-8b537ded63dd` | `moe-scarves.esl` |
| 7 | Pelts o Plenty - Fur Pelt Gear | 120726 | 704702 | 4.3.1 | 705.81 MB | `20260902T234023119Z-01251598cc1d` | `Pelt Cloaks.esp` |
| 8 | RMB SPCH - Pelts o Plenty | 179354 | 749409 | 1.1.0 | 0.01 MB | `20260902T234027735Z-456f9c725cbf` | `RMB SPCH - Pelt Cloaks.esp` |

Archive SHA-256, as installed:

```
6369-18422.rar     03ef0b317a28bab42eb226c774e3fda1b3a522f14b0d6c38a53bc2a32d5cbab9
42558-170809.7z    5200f9ea5e4a9d64b05df3e72fc90c53d1e9e78ed650e48e4ee57629fc9d6cab
42558-263634.7z    df8822b5fcba8120e0cb52629b8183287d21c50928f93f6fb017dc56a1c251f6
85932-363920.7z    2e2a264fe4134a2d0feb9fbd82a790cb610b3ad06b54df7d2ccec4718b12a898
116030-749413.zip  6b7e6d867f4a2438cb10d8045119671e8d1af0bba71b8f95436f10cf15037e88
149259-723968.7z   9b909da46bae6f083c4e28a9f81c02609ea8e3b0adf78b56452467bb98cc2c35
120726-704702.zip  cd48e207533666c39bb99e5cdebc2a7c2db9252484006de9dbfa5e225495e1a1
179354-749409.zip  9c6a59d38304e2b6fa77f6a3368599fa4b3e7b2e5e81f1497c776c3d1da8ca71
```

## What did NOT land, and why

| Held | Reason |
|---|---|
| **Artesian Cloaks `17416`** | Directed by the team lead: textures-over-physics until [#193](https://github.com/Ensrick/skyrim-mod-assistant/issues/193) ports its SMP meshes onto ElSopa's texture paths. Its 391 NIFs and ElSopa's 394 replace 381 of the same files. **Consequence: no cloak in this build simulates.** All 366 Cloaks of Skyrim cloaks render on the vanilla `SkirtBBone01-03` chain, i.e. canned skirt animation only. Pelts 'o' Plenty and More Scarves bring their own SMP and are unaffected. |
| **RMB SPIDified - Sons of Skyrim `83340`** | **My call, against the brief - flagged, not worked around.** See below. [#195](https://github.com/Ensrick/skyrim-mod-assistant/issues/195). |
| **Pelts 'o' Plenty Survival Fix `164077`** | **My call, on evidence.** See below. Reported on [#189](https://github.com/Ensrick/skyrim-mod-assistant/issues/189). |
| Cloaks of Skyrim's eight ESPs | By design, per the audit. Omitted at install time by FOMOD plan, so none exists in the tree. |
| ElSopa's 394 Oldrim meshes | Omitted from the 2k texture install by FOMOD plan; the SSE conversion arrives as mod 3. |
| ElSopa 4k / 1k / 512 tiers | 2k chosen by measurement in the audit §7. |
| More Scarves `_3BA`, `_BHUNP` | No 3BA, BHUNP or OBody in this build. |
| RMB SPCH `01 Tweaks - Disallow Enchanting`, `- Weaker Enchants`, `- Names`, `02 Description Framework` | See "Decisions the record did not settle". |

---

## Decisions the record did not settle

### 1. RMB SPIDified - Sons of Skyrim 83340: held, against instruction

The brief called this "not optional". Reading the archive changed the picture,
so I stopped rather than proceed: **its `00 Core` replaces the installed Sons of
Skyrim plugin, it does not shim it.**

| plugin | records | contents |
|---|---:|---|
| installed `NW_Sons_of_Skyrim.esp` (sha256 `0610d825...8bc246`) | **971** | 201 NPC_, 60 PlacedObject, 53 Outfit, 130 LVLI, 3 Cell, 10 Container, 2 LeveledNpc, 130 ARMO |
| 83340's `NW_Sons_of_Skyrim.esp` (sha256 `4699975e...29689b`) | **634** | **0** NPC_, **0** PlacedObject, 18 Outfit, 121 LVLI, **0** Cell, 113 ARMO |

`RMB SPID - Sons of Skyrim.esp` (239 records: 150 LVLI, 88 Outfit, 1 ARMO)
masters `NW_Sons_of_Skyrim.esp` and is built against the stripped one. The
package further ships `00 Disable Vanilla Guard Outfits` (36 SkyPatcher configs
removing vanilla guard outfits from the leveled lists), per-hold rural/urban
outfit injection, four helmet-frequency variants, Stormcloak weapon and reward
configs, and crafting tweaks. That is a guard-distribution overhaul across all
nine holds, not a cloak patch - and `Sons of Skyrim v2.0 - My patches and fixes
SE by Xtudo` 104126 is installed and forwards records from the 971-record
version.

I also rejected the partial route of installing only
`RMB SPID - Sons of Skyrim.esp` against the unstripped plugin: its 88 Outfit and
150 LVLI records point at FormIDs in a plugin it does not match, and that fails
silently as wrong outfits rather than loudly.

**Effect of holding it:** the two `00 Shared` configs installed with RMB SPCH -
Cloaks of Skyrim and RMB SPCH - Pelts o Plenty target
`RMB SPID - Sons of Skyrim.esp` and `RMB SPID - NordwarUA GAR - Outfits.esp` and
are inert. Cloaks of Skyrim's hold cloaks are still distributed, by RMB SPCH's
own 20 leveled lists and the `RMB SPID - Core Definitions.esp` framework; what
does not happen is the merge into Sons of Skyrim's own per-hold guard cloak
lists. Guards keep wearing Sons of Skyrim's own eleven slot-46 hold cloaks.

Tracked with the full evidence on
[#195](https://github.com/Ensrick/skyrim-mod-assistant/issues/195).

### 2. Pelts 'o' Plenty Survival Fix 164077: not installed

The brief asked me to check it applies before authoring anything under #189. It
does not.

Both plugins hold 419 records. The differences, read from the archives:

- **Its only record additions are Frostfall keywords** -
  `FrostfallIsCloakFur` (`CC0E1E:Update.esm`) and
  `FrostfallEnableKeywordProtection` (`CC0E28:Update.esm`). Frostfall is not in
  this build; the survival stack is Starfrost 2.0.0 + Survival Mode Improved
  1.7.0.
- **It moves every cloak from biped slot 57 to slot 46.**
  `BodyTemplate.FirstPersonFlags` goes from `134217728` to `65536` on
  `FoxPeltCloak`, `BearPeltCloak` and the rest - onto the Cloaks of Skyrim and
  Bocksten slot.
- Base Pelts already carries the warmth keywords it would supposedly fix:
  `Survival_ArmorWarm` (`002ED9:Update.esm`) plus `ClothingBody`,
  `ArmorClothing`, `VendorItemArmor`, `ArmorMaterialHide`. That is the **warm**
  tier, one better than the `Survival_ArmorCold` RMB gives the Cloaks of Skyrim
  records.

Reported on [#189](https://github.com/Ensrick/skyrim-mod-assistant/issues/189).

### 3. RMB SPCH FOMOD options

Recorded in `records/fomod-plans/116030-rmb-spch-cloaks-of-skyrim.json`.

**Taken - `01 Tweaks - Generic`.** It fixes two record defects rather than
changing taste: it clears the biped slot-40 (tail) flag that base Cloaks of
Skyrim sets on 339 of its 366 items, which is what hides Khajiit and Argonian
tails under a cloak, and it removes the `ClothingNecklace` keyword the 2017 mod
wrongly puts on every cloak. It also adds `Survival_ArmorCold` + `ClothingBody`
(a warmth floor #189 will raise), removes `ArmorMaterialHide`/`Leather`, sets
weight 2.0 and adds pick-up/put-down sounds.

**Omitted - `01 Tweaks - Disallow Enchanting` and `01 Tweaks - Weaker
Enchants`.** Both belong to one open question: audit shortlist item 4, whether
generic cloaks stay enchantable. Weakening only the eight authored enchanted
pairs while leaving all 122 cloaks freely enchantable would be incoherent, so
both wait for that answer. Reversible - each is a single config file.

**Omitted - `01 Tweaks - Names`.** A cosmetic rename of vendor item names
("Ashland Tribal Wrap", "Black Cloak of Magic Minor Suppression"). Nobody asked
for it.

**Omitted - `02 Description Framework`.** Its required mod is not installed, so
the configs would do nothing.

### 4. More Scarves female route is unfinished

`_VanillaF` is installed as the starting shape. This build runs CBBE Curvy +
Reverie, and the archive ships the slider data for exactly this case - 84 `.osd`
and 5 `.osp` under `CalienteTools/BodySlide`, now at
`mods\More Scarves\CalienteTools`. The BodySlide build against the installed
preset is owed, tracked on
[#196](https://github.com/Ensrick/skyrim-mod-assistant/issues/196). The male
route needs nothing: `_HIMBO` matches the installed HIMBO + SkySight stack.

More Scarves' `__loweredHood` Dynamic Armor Variants configs and its
`HT_ArmorHood` KID rule are installed but **inert**: Helmet Toggle 2 is not in
this build, so nothing consumes `HT_HiddenHelmetPlayer`.

---

## Resolved order

**Plugins** (244 active; positions are indices into the active list):

| pos | plugin | why there |
|---:|---|---|
| 26 | `RMB SPID - Core Definitions.esp` | already installed; must precede RMB SPCH - it holds the `RMB_Sublist_CLO_*` lists the CoS configs inject into |
| 81 | `NW_Sons_of_Skyrim.esp` | unchanged, 971 records |
| 240 | `Cloaks - RMB SPCH.esp` | ESL-flagged, 294 new records, zero overrides |
| 241 | `moe-scarves.esl` | |
| 242 | `Pelt Cloaks.esp` | must precede its patch |
| 243 | `RMB SPCH - Pelt Cloaks.esp` | masters `Pelt Cloaks.esp` |

**Mod priority** - `modlist.txt` stores highest priority first, so line 2 wins
every asset conflict against line 9:

```
line 2  RMB SPCH - Pelts o Plenty
line 3  Pelts o Plenty - Fur Pelt Gear
line 4  More Scarves
line 5  RMB SPCH - Cloaks of Skyrim
line 6  Cloaks of Skyrim Retextured - Female Mesh Patch
line 7  ElSopa - Cloaks of Skyrim Retextured Mesh Update 1.2
line 8  ElSopa - Cloaks of Skyrim Retextured 2K
line 9  Cloaks of Skyrim
```

That is exactly the order the audit required, and it fell out of the install
sequence rather than needing a manual move: female patch over mesh update over
ElSopa textures over base Cloaks of Skyrim. No LOOT sort was run - the two
master constraints (`Core Definitions` before `RMB SPCH`, `Pelt Cloaks.esp`
before its patch) already hold, and `verify_order` reads CLEAN.

## Gates

| gate | result |
|---|---|
| `install_mod.py --verify` | **`0 problem(s)`** - 258 mods, 328 plugins discovered, 8 deliberately off (none of them from this batch) |
| `verify_order.py` | **CLEAN** - 244 active plugins, 328 discoverable |
| `file_conflicts.py` | 41,771 files, 2,827 collisions, 27 critical; **2 critical rows touch this batch, both benign** - see below |
| `keep_coverage.py` | **7 violations, all expected**: 6369, 42558, 85932, 116030, 120726, 149259, 179354. `install_mod` queued every one to the relay spool (`decisions-pending.json`, 7 entries, verified); the extension applies them on the next Nexus page load. Nothing to do by hand - `docs/CURATION_POLICY.md` puts the Keep at the end of the install and this is that step in flight. |
| launch verification | **not run** - user asked to hold it. Batch is `UNVERIFIED`. |

### The two critical file conflicts are false positives

```
SKSE/Plugins/SkyPatcher/leveledList/Cloaks - Common/RMB SPID - Sons of Skyrim.esp.ini
SKSE/Plugins/SkyPatcher/leveledList/Cloaks - Common/RMB SPID - NordwarUA GAR - Outfits.esp.ini
```

Both are shipped by RMB SPCH - Cloaks of Skyrim and RMB SPCH - Pelts o Plenty,
and Pelts wins on priority. They are **byte-identical** between the two packages
(`78f754364dab31c4...` and `d01916fab91e35b4...`, `diff` empty), which is what
the RMB FOMOD claims: *"These files can overwrite or be overwritten safely, as
they are shared / included in other SPCH patches."* Verified rather than
believed. No Cloaks of Skyrim content is lost, and both files are inert anyway
while 83340 is held.

### Asset conflicts, all intended

| winner | overridden | files |
|---|---|---:|
| ElSopa Mesh Update 1.2 | Cloaks of Skyrim | 348 |
| Female Mesh Patch | Cloaks of Skyrim | 48 |
| Female Mesh Patch | ElSopa Mesh Update 1.2 | 46 |
| ElSopa 2K | Cloaks of Skyrim | 30 |

394 = 348 + 46, so every ElSopa mesh is live except the 46 the female patch
supersedes. The texture number is the interesting one: **ElSopa overrides only
30 of Cloaks of Skyrim's 137 textures by path**, because ElSopa renamed the set -
the other 142 of his 172 land on new paths, and 101 base CoS textures stay on
disk but are referenced by no surviving mesh. That matches the audit's coverage
finding exactly.

## Slot 31 outcome, and a correction to my own tooling

The brief asked for the slot-31 hood collision between Pelts 'o' Plenty, More
Scarves and Helmet Toggle. Answer: it is real, ordinary, and Helmet Toggle is not
part of it yet.

Re-swept the whole live order after the install
(`records-work/cloak-audit-2026-09-02/slot_scan2.py`, output
`slot-contention-2.txt`):

| slot | ARMO | plugins | who |
|---:|---:|---:|---|
| 31 (hair/hood) | **588** | 24 | Vigilant 193, BSHeartland 138, USSEP 102, Sons of Skyrim 31, arnima 30, Xtudo SoS fixes 28, **Pelt Cloaks.esp 10**, Steel Plate 8, ... **moe-scarves.esl 3** |
| 45 (neck) | **14** | 3 | **moe-scarves.esl 12**, USSEP 1 (`Dragon_Purple_BloodWingLFXArmor`), BSHeartland 1 (`CYRHorseSaddleImperial`) |
| 46 (chest/cloak) | **142** | 4 | **Cloaks - RMB SPCH.esp 122**, Sons of Skyrim 14, Campfire 4, Scale Nord 2 |
| 57 | **112** | 2 | **Pelt Cloaks.esp 109**, Inigo 3 (`MrDragonfly*`) |

Reading:

- **Slot 31 is the vanilla helmet and hood slot.** 588 items across 24 plugins is
  not a defect, it is what that slot is for. Pelts' 10 fur hoods
  (`FurPeltHoodGoat`, `FurPeltHoodBear`, ...) and More Scarves' 3 hooded capes
  (`_MOE_cape001AM`, `_MOE_cape002gAM`, `_MOE_cape002rAM`) compete with every
  helmet in the game, and with each other. That is ordinary wear-time
  exclusivity: a fur hood or a hooded cape, not both. Nothing in the build
  currently gives one NPC both, because neither mod has NPC distribution
  installed - Pelts' SPID add-on was not taken and More Scarves' SkyPatcher
  config is vendor-only.
- **Helmet Toggle 2 is not installed**, so the third party to this collision does
  not exist yet. More Scarves' `HT_ArmorHood` KID rule and its three Dynamic
  Armor Variants entries are on disk and inert. When Helmet Toggle is adopted it
  will need an explicit rule for Pelts' 10 slot-31 hoods, which ship no lowered
  variant.
- **Slot 45 is effectively free for More Scarves.** The only other two holders
  are a dragon-wing effect armor and a horse saddle.
- Slot 46 and slot 57 match the pre-install audit exactly, with the new plugins
  added on top.

**Correction to my own tooling, stated because a number in the audit could have
been wrong.** The first sweep (`slot_scan.py`, 2026-09-02 afternoon) parsed
`BodyTemplate.FirstPersonFlags` as an integer only. The record CLI returns
Mutagen's symbolic name instead when exactly one well-known flag is set - `Hair`,
`Body` and so on - and those rows were silently skipped by an `except: continue`.
`slot_scan2.py` handles both. The published slot 45 / 46 / 57 figures in
`records/cloak-layer-audit-2026-09-02.md` are unaffected and stand: nothing in the
live order used the symbolic form for those three slots, and the corrected counts
reproduce them exactly (46: 14 + 4 + 2 = 20 before this install; 57: 3). The
defect only ever hid slot 31, which that sweep did not cover. It did bite once
today, on a first pass over the installed Pelts plugin that reported 109 items
and no hoods; the number in this record is from the fixed scanner.

## Mesh format check

One non-SSE mesh exists anywhere in the installed cloak stack:
`Cloaks of Skyrim\meshes\Clothes\cloaksofskyrim\cloakmblack2.nif`, NIF user
version 34, the single Oldrim file base Cloaks of Skyrim has always shipped
(audit §1). It is **unreachable**: `Cloaks - RMB SPCH.esp` names 253 mesh paths
and that is not one of them, so no record renders it. ElSopa's 394 Special
Edition meshes and the female patch's 48 are all user version 100, as is
everything in More Scarves and Pelts 'o' Plenty. Zero reachable Oldrim geometry.
