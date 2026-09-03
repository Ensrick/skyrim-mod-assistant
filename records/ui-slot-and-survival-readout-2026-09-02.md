# UI slot and survival readout - 2026-09-02

Audit only. Nothing installed, no profile file touched, no launch, no curator
change. Archives were downloaded into the MO2 download cache
(`mo2-instances\skyrim-se\downloads`) and extracted to a scratch directory
outside `mods\`.

Driven by two user statements, 2026-09-02:

> "the lack of being able to see exactly how hungry or warm/cold my character is
> gets frustrating. I don't need to see the numbers, but having a bar for it
> would be nice."

> "One thing I don't like with UI overhauls is floating healthbars, it looks
> terrible."

## 0. What the build carries today

From `profiles\Default\modlist.txt` and `records\installed-mods.json`:

| slot | installed | source |
|---|---|---|
| menus | SkyUI 6.11 (12604) | vendor |
| menu extension | UIExtensions 1.2.0 (17561) | vendor |
| character | RaceMenu 0.4.20.0 (19080) + `RaceMenu 1.7.104 Native Overlay - Ensrick` | vendor + Ensrick rebuild |
| SKSE config UI | SKSE Menu Framework 3.13-Hotfix2 (120352) | vendor |
| MCM | MCM Helper 1.6.3 (53000) | vendor |
| loot | `QuickLoot IE - Ensrick 1.7.99` | Ensrick source build |
| survival | Survival Mode Improved SKSE 1.7.0 (78244), Starfrost 2.0.0 (97536), Campfire 1.12.1SEVR (667), Simple Hunting Overhaul 1.16 (95943), CC `ccqdrsse001-survivalmode` | vendor |

There is **no HUD layer at all** - no TrueHUD, no moreHUD, no widget framework,
no needs readout of any kind. The hunger/warmth information exists only as the
vanilla Survival Mode attribute-bar tinting, which is exactly what the user is
complaining he cannot read.

## 1. The survival readout

### What this build actually populates

The readout question is decided by which globals carry live values here, not by
which survival mod is "in charge". Dumped `GLOB` records from all three layers:

| global | CC `ccqdrsse001` | SMI override | Starfrost override | effective |
|---|---|---|---|---|
| `Survival_HungerNeedValue` | 145 | 60 | **0** | Starfrost |
| `Survival_HungerNeedMaxValue` | 1000 | 468 | **120** | Starfrost |
| `Survival_ColdNeedValue` | 55 | **55** | - | SMI |
| `Survival_ColdNeedMaxValue` | 1000 | **900** | - | SMI |
| `Survival_ExhaustionNeedValue` | 140 | 85 | **75** | Starfrost |
| `Survival_ExhaustionNeedMaxValue` | 960 | 578 | **600** | Starfrost |

Both halves of the pair the user wants - hunger and cold - are live vanilla
`Survival_*NeedValue` / `Survival_*NeedMaxValue` globals with sane ranges. This
matters because it decides which widget mods can work at all:

- **Anything that reads the `Survival_*NeedValue` / `*MaxValue` pair renders a
  true proportional bar here.**
- Anything that reads Starfrost's *magic effects* renders discrete stages, not a
  bar - and Starfrost only applies its display effects from **stage 3**, so
  there is no readout at all until the character is already badly off.

`SURVIVAL_COMPARISON.md` recorded that Starfrost 2.0.0 "consolidated its Hunger
onto SM's native infrastructure"; the global dump above is the confirmation, and
it is the single most useful fact in this record.

### Candidates, measured

| id | mod | version | updated | mechanism | DLL | gate |
|---|---|---|---|---|---|---|
| 36457 | iWant Widgets | 1.33 | 2024-06-04 | Papyrus + SWF widget library, **native meters** | **none** | n/a - no DLL |
| 36460 | iWant Status Bars | 2.09 | 2022-11-22 | state-icon manager on top of iWant Widgets, up to 10 states | **none** | n/a - no DLL |
| 96410 | iWant Widgets NG | 1.2.8 | 2024-06-07 | native accelerator for iWant (optional) | `IWantWidgetsNative.dll` | **FAIL** |
| 162769 | iWant Widgets for Starfrost | 2.0 | 2026-08-23 | reads Starfrost **magic effects**, 4-stage icons | none | n/a |
| 91878 | SMI UI Widgets for Needs Display | 1.0/1.11 | 2023-05-25 | iWant state icons off SMI globals | none | n/a |
| 185796 | Survival Mode Prisma Widgets | 1.3 | 2026-08-14 | reads `Survival_*NeedValue`/`MaxValue`, **true draining bars** | requires Prisma UI | **blocked** |
| 148718 | Prisma UI | 1.4.1 | 2026-03-27 | HTML/CSS/JS UI framework | `PrismaUI.dll` | **FAIL** |
| 167538 | Skyrim Party Sheet | 3.1 | 2026-07-29 | all-in-one party/player HUD incl. survival | `SkyrimPartySheet.dll` | **FAIL** |
| 41891 | Survival Control Panel | 1.1.2 | 2022-10-02 | Survival feature framework, **not a readout** | yes | not re-tested; see below |

### Gate results, with PE stamps

Run with `py -3 audit/skse_version_data.py` under the corrected reject window
(upper bound 2026-08-21, the day CommonLibSSE-NG gained Address Library format 5
support - `audit/skse_version_data.py`, #197):

| DLL | PE TimeDateStamp | UTC | versionIndependence / Ex | V5 bit | verdict |
|---|---|---|---|---|---|
| `TrueHUD.dll` 1.1.10 | 1788028501 | **2026-08-29 18:35:01Z** | 1 / 3 | **YES** | **PASS (version independent)** |
| `AHZmoreHUDPlugin.dll` 5.4.2.0 | 1788128891 | **2026-08-30 22:28:11Z** | 1 / 1 | no | **PASS** - stamp is after the support date, which is what makes it safe |
| `PrismaUI.dll` 1.4.1 | 1774640351 | 2026-03-27 19:39:11Z | 1 / 1 | no | **FAIL** - addrlib-v5 flag missing AND stamp inside reject window |
| `SkyrimPartySheet.dll` 3.1.0.0 | 1785256641 | 2026-07-28 16:37:21Z | 1 / 1 | no | **FAIL** - same reason |
| `IWantWidgetsNative.dll` 1.2.4 | 1717743913 | 2024-06-07 07:05:13Z | 1 / 1 | no | **FAIL** - same reason |

Archive hashes for the record:

    62775-798218.7z  TrueHUD 1.1.10            sha256 ad10182e0806c47998bc6bf7badd34b8160c9ff008b85b796245e031a77ceed5
    12688-797906.7z  moreHUD 5.4.2.0           sha256 957434d70f8bbbcdd1506d963b161f9d480e0f60a9586411fd86f923a8d1ada1
    148718-735761.zip Prisma UI 1.4.1          sha256 791414f212fd5d3a807d801ec8ae725d39ec510c7b033da6338733779bf28b68
    167538-782487.zip Skyrim Party Sheet 3.1   sha256 a0d4813fff189e04739cbb65eb74e90742e026df074f70995e91656195a18230
    96410-509224.zip IWant Widgets NG 1.2.8    sha256 d32d3c2ae6b3d12dd84a3bf5010869b8cc963782cb8edad4ad526933a64a09fc
    36457-508135.7z  iWant Widgets 1.33        sha256 192ff1953e67b3c8a1543102ff283d4920a0f107bb602acb28e3a2f83f0c8eb7
    36460-333629.7z  iWant Status Bars 2.09    sha256 34c1ab6f8b165ee2d1ff725881b90b8985047655e95c62b18b16ef1b5ace76e7

Three of five fail, and all three fail for the same reason. They are **rebuild
candidates, not installs** - but Prisma UI's rebuild has a licence problem (see
below), and Party Sheet's payload is far wider than a needs readout.

### The Survival Control Panel question, resolved

Prior research (`docs/DEFERRED_DECISIONS.md`, cloak thread) left "authorize a
1.7.104 Survival Control Panel port" open. **It is not the route for this
request, for a reason that has nothing to do with the port.** Survival Control
Panel (41891) is a *configuration framework* - "a framework for mods and players
to customize native Survival Mode features like Sleep to Level Up, with added
support for cloaks". It exposes settings and a cloak warmth slot. It renders no
hunger or warmth meter. Porting it would answer the cloak question in #95; it
would not put a bar on screen. The two questions should stop travelling together.

### What the widget mods actually draw

- **`iWant Widgets for Starfrost` 2.0 (162769)** is the natural-looking answer
  and is the wrong one. Reading its script
  (`Source/Scripts/iWant_Starfrost_Widgets.psc`), it watches
  `MAG_HungerStage03/04/05DisplayEffect`, `MAG_ColdStage3/4/5DisplayEffect`,
  `MAG_ExhaustionStage3/4/5DisplayEffect` and `MAG_StarfrostInjuryEffect01-03`,
  and drives a 4-state icon that is **invisible at state 0**. The character is
  already at hunger stage 3 before anything appears. It is a warning light, not
  a gauge.
- **`SMI UI Widgets` (91878)** is the same shape - iWant *state icons* off SMI's
  globals. `iWant Status Bars`' own API describes its unit as "a set of widgets
  ... loaded into a **state icon**" with up to ten states.
- **`Survival Mode Prisma Widgets` 1.3 (185796)** is the only shipped mod that
  draws a real continuously-filling bar off the exact global pair this build
  populates. Its author states the contract explicitly: "This mod technically
  works with ANYTHING that has the same editorid survival global values ... like
  for example `Survival_HungerNeedValue` + `Survival_HungerNeedMaxValue`". Its
  position, size and opacity are configured in the SKSE menu - **SKSE Menu
  Framework is already installed**. It is blocked only by Prisma UI's DLL.

### Prisma UI as a rebuild: licence blocks the shipping half

Prisma UI is source-available at `github.com/PrismaUI-SKSE/framework` (full C++,
CMake, `src/`). The **Prisma UI License** permits "modify the framework for your
own **private** use" and "share and distribute the **original, official**
framework files", and restricts "publicly release or distribute your own
modified versions without explicit written permission". It also embeds the
Ultralight SDK under the Ultralight Free License.

Consequence under `docs/CURATION_POLICY.md` ("Every fix is a shippable patch or
a reproducible recipe") and the 2026-09-02 eligibility ruling (#160): a locally
rebuilt `PrismaUI.dll` would be **`local-only`** - it cannot be packaged in the
Ensrick collection, and the "installer regenerates it from source" recipe form
is at best a grey reading of "private use". That is a user decision, not a
technical one, and it is the single thing standing between this build and the
readout he asked for.

### Recommendation for the survival readout

**Author `Ensrick - Survival Meters`, a small Papyrus quest on top of iWant
Widgets 1.33 (36457).** No SKSE DLL is involved anywhere in this route.

Why this is the right shape rather than a workaround:

- iWant Widgets has **native meters**. Its API ships
  `setMeterPercent(Int id, Int percent)` - "Sets the percentage of the meter to
  fill" - plus `setMeterColors(light, dark, flash)` and `doMeterFlash`. That is
  a true fill bar, not a state icon; `iWant Status Bars` (36460) is the
  *icon* layer built on top and is not needed for this.
- The mod ships **no DLL**: an `.esl`, one SWF, and Papyrus. Requirement is
  SkyUI, which is installed. `iWant Widgets NG` is only an optional native
  accelerator and is the piece that fails the gate - it is declined, not needed.
- It is **MIT licensed** ("You may freely modify and distribute it as you see
  fit", `documentation/README.html`), so it is a clean vendor row and our widget
  is `distributable` Ensrick work rather than `local-only`.
- The data contract is the verified global pair above:
  `Survival_HungerNeedValue / Survival_HungerNeedMaxValue` and
  `Survival_ColdNeedValue / Survival_ColdNeedMaxValue`. Poll on
  `RegisterForSingleUpdate`, compute the percentage, call `setMeterPercent`.
  No numbers on screen, which is what he asked for.

Fallback if he would rather not wait for an owned widget: **Survival Mode Prisma
Widgets + a local Prisma UI 1.4.1 rebuild**, accepted as `local-only` and
therefore excluded from anything shared. That is a real trade and his call.

Explicitly **not** recommended: `iWant Widgets for Starfrost` (invisible until
stage 3), `Skyrim Party Sheet` (fails the gate, and its payload is a whole party
HUD the user did not ask for).

## 2. Is NORDIC UI "the meta"?

No, and the survey is right. `docs/ECOSYSTEM-SURVEY-2026-08-30.md` records
**NORDIC UI 0/19** across the surveyed exports, against SkyUI 19/19, TrueHUD
17/19, moreHUD 17/19, UIExtensions 17/19, MCM Helper 16/19. The addendum
qualifies it precisely: NORDIC UI "survives only in Invicta's alpha export"
(Load Order Library alpha 0.9.8.6.1, 2026-07-15) - no *released* list ships it.

The Nexus record explains why without needing the survey at all: NORDIC UI -
Interface Overhaul (**49881**) is v2.4.1, **last updated 2021-08-14** - five
years stale - and its own summary is "Replaces *everything*. Requires SkyUI and
**SkyHUD**." SkyHUD is a `hudmenu.swf` replacer, which puts it in direct
competition with the HUD layer this build is about to adopt, and NORDIC UI's
own HUD carries enemy health bars (mod 54779 exists solely to patch moreHUD's
bars into NORDIC UI's).

So NORDIC UI is famous, well-liked, and the wrong pick here: it is stale, it
demands a HUD replacer, and it ships the exact thing the user says he hates.
Its endorsement count (24,381) is the "meta" impression; it is a 2021 number.

## 3. The skin

Judged against his stated taste, not popularity. All four are SkyUI *menu*
replacers - they do not touch the HUD - so the floating-bar objection does not
discriminate between them.

| id | skin | version | updated | endorsements | note |
|---|---|---|---|---|---|
| 60837 | Dear Diary Dark Mode | 1.1.1 | 2022-11-05 | 13,770 | the ancestor of the other two; largest patch ecosystem |
| 75188 | Untarnished UI | 1.1.6 | 2023-07-01 | 7,319 | "flat and modern ... **while feeling similar to its original style**", based on DDDM |
| 130983 | Edge UI | **0.6.1** | 2024-10-09 | 4,969 | "inspired by modern AAA games like God Of War, Assassin's Creed, Horizon and Elden Ring ... **This is still a WIP, as the author is a newbie in coding and designing**" |
| 49881 | NORDIC UI | 2.4.1 | 2021-08-14 | 24,381 | see above |

**Recommendation: Untarnished UI (75188).** The deciding argument is his own
taste as recorded elsewhere in this project: the vanilla-shape preference that
protects vanilla iron armour and vanilla steel gauntlets in
`docs/PATCH_INTENTS.md`, and the distance-detail rule that rejects "matte,
single-tone" modern flatness. Untarnished's stated design goal is the only one
of the three that names staying close to the original style. Edge UI is
explicitly styled after modern AAA games, is still 0.x, and its author's own
page calls it a work in progress by a self-described newbie - that is the
opposite end of the same axis, and it is a low-currency bet as well. Dear Diary
Dark Mode is the safe third choice and the one with the deepest patch ecosystem
if a specific patch is ever the blocker.

This is a taste call and the user should overrule it freely; the survey ties
DDDM and Untarnished at 7/19 and puts Edge UI at 3/19, so ecosystem weight does
not decide it either.

Note if Untarnished is chosen: `RaceMenu - Untarnished UI - DIP Patch` (97347,
updated 2026-04-21) exists and matters here, because RaceMenu is installed with
an Ensrick native overlay on top.

## 4. The floating-healthbar problem

**TrueHUD's floating bars can be switched off with one flag, and the mod keeps
everything that makes it near-universal.** Receipt, from the shipped
`MCM/Config/TrueHUD/settings.ini` in TrueHUD 1.1.10:

    [Main]
    bEnableActorInfoBars = 1
    bEnableBossBars      = 1
    bEnablePlayerWidget  = 1
    bEnableRecentLoot    = 1
    bEnableFloatingText  = 0

The four features are independent booleans. `bEnableActorInfoBars = 0` removes
the entire floating world-space bar system (the `[ActorInfoBars]` block's 33
keys - `uInfoBarDisplayHostiles`, `bInfoBarDisplayPhantomBars`,
`bInfoBarScaleWithDistance`, `fInfoBarOffsetZ` and the rest - all become inert).
`bEnableFloatingText` is **already 0 by default**, so floating damage numbers
are off out of the box.

What survives with actor info bars off:

- the **player widget** - a repositionable health/magicka/stamina bar group,
  fixed to the HUD, not floating over anything;
- **boss bars** - a single anchored bar at the top of the screen, again not
  world-space;
- the **recent loot** log;
- the **API**, which is the real reason TrueHUD is in 17 of 19 lists: other SKSE
  plugins draw their special-resource bars through it.

So the answer is "install it and turn one flag off", not "skip it". MCM Helper
is already installed, so the setting is reachable in-game and the shipped
`settings.ini` can be pre-set as an Ensrick config overlay (`distributable`).

moreHUD SE (12688, 5.4.2.0, DLL stamped 2026-08-30, **PASS**) extends the
crosshair/target readout with text - level, ingredient effects, read-book state.
It does not add world-space bars. `[unverified]` beyond the package inspection:
its display code lives in `AHZmoreHUD.bsa` and was not decompiled.

## 5. Recommended UI stack

In adoption order, all of it gated or DLL-free:

1. **TrueHUD 1.1.10 (62775)** - gate PASS, PE 2026-08-29, V5 bit set - shipped
   with an Ensrick config overlay setting `bEnableActorInfoBars = 0`.
2. **moreHUD SE 5.4.2.0 (12688)** - gate PASS, PE 2026-08-30.
3. **iWant Widgets 1.33 (36457)** - no DLL, MIT, requires SkyUI.
4. **`Ensrick - Survival Meters`** - owned Papyrus widget on iWant's
   `setMeterPercent`, reading the verified `Survival_*NeedValue` /
   `*MaxValue` pairs. Hunger and cold first; exhaustion is free once the
   scaffolding exists.
5. **Untarnished UI 1.1.6 (75188)** plus its RaceMenu DIP patch (97347) - taste,
   deferred to the user.

Deliberately excluded: NORDIC UI (stale, needs SkyHUD, ships enemy bars),
Prisma UI + Prisma Widgets (DLL fails the gate; rebuild is `local-only` under
its licence), Skyrim Party Sheet (DLL fails the gate), iWant Widgets NG (DLL
fails the gate, optional anyway), iWant Widgets for Starfrost (stage-3 icons,
not a gauge), Survival Control Panel (a config framework, not a readout).

## 6. Questions only the user can answer

1. **Skin:** Untarnished UI, Dear Diary Dark Mode, or none? The three are a
   taste choice, not a quality ranking.
2. **Prisma UI:** accept a `local-only` rebuilt DLL - excluded from anything
   shared - to get Prisma Widgets now, or wait for the owned iWant meter widget
   which is distributable? Or ask StarkMP for written redistribution
   permission?
3. **Meter placement and style:** how many meters on screen at once (hunger and
   cold only, or exhaustion too), always visible or fading in above a threshold,
   and where.
4. **TrueHUD player widget:** with floating enemy bars off, does he still want
   TrueHUD's *own* player health/magicka/stamina bars, or only the API plus
   boss bars with the vanilla player HUD left alone?

## 7. Tracked as issues

- Author `Ensrick - Survival Meters` on iWant Widgets - the hunger/warmth bar.
- Adopt TrueHUD with `bEnableActorInfoBars = 0` as a shipped config overlay.
- Adopt moreHUD SE.
- Prisma UI 1.7.104 rebuild - gate FAIL plus a licence question, so it is a
  decision issue rather than a build issue.
