# UI slot and survival readout - 2026-09-02 (revised 2026-09-03)

Audit only. **Nothing was installed.** No profile file was touched by this record, no
launch, no curator change. Archives were downloaded into the MO2 download cache
(`mo2-instances\skyrim-se\downloads`) and extracted to a scratch directory outside
`mods\`.

Driven by two user statements, 2026-09-02:

> "the lack of being able to see exactly how hungry or warm/cold my character is gets
> frustrating. I don't need to see the numbers, but having a bar for it would be nice."

> "One thing I don't like with UI overhauls is floating healthbars, it looks terrible."

**Constraint, 2026-09-02 (revision reason):** *"don't pickup new mods without
permissions, just suggest no mods"*, with the exception of *"any requisite mods you
need to fix the issues with the mods we currently have"*. Everything below is therefore
a **suggestion with a link**, not a plan to install. Section 6 is the only part of this
record that can be done with what is already in the build, and it is not free of a
question either.

## 0. What the build carries today

From `profiles\Default\modlist.txt` and `records\installed-mods.json`:

| slot | installed | source |
|---|---|---|
| menus | [SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) 6.11 | vendor |
| menu extension | [UIExtensions](https://www.nexusmods.com/skyrimspecialedition/mods/17561) 1.2.0 | vendor |
| character | [RaceMenu](https://www.nexusmods.com/skyrimspecialedition/mods/19080) 0.4.20.0 + `RaceMenu 1.7.104 Native Overlay - Ensrick` | vendor + Ensrick rebuild |
| SKSE config UI | [SKSE Menu Framework](https://www.nexusmods.com/skyrimspecialedition/mods/120352) 3.13-Hotfix2 | vendor |
| MCM | [MCM Helper](https://www.nexusmods.com/skyrimspecialedition/mods/53000) 1.6.3 | vendor |
| loot | `QuickLoot IE - Ensrick 1.7.99` | Ensrick source build |
| survival | [Survival Mode Improved SKSE](https://www.nexusmods.com/skyrimspecialedition/mods/78244) 1.7.0, [Starfrost](https://www.nexusmods.com/skyrimspecialedition/mods/97536) 2.0.0, [Campfire](https://www.nexusmods.com/skyrimspecialedition/mods/667) 1.12.1SEVR, [Simple Hunting Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/95943) 1.16, CC `ccqdrsse001-survivalmode` | vendor |

There is **no HUD layer at all** - no TrueHUD, no moreHUD, no widget framework, no
needs readout of any kind. Hunger and warmth exist only as the vanilla Survival Mode
attribute-bar tinting, which is exactly what the user says he cannot read.

## 1. The survival readout

### What this build actually populates

The readout question is decided by which globals carry live values here, not by which
survival mod is nominally in charge. `GLOB` records dumped from all three layers:

| global | CC `ccqdrsse001` | SMI override | Starfrost override | effective |
|---|---|---|---|---|
| `Survival_HungerNeedValue` | 145 | 60 | **0** | Starfrost |
| `Survival_HungerNeedMaxValue` | 1000 | 468 | **120** | Starfrost |
| `Survival_ColdNeedValue` | 55 | **55** | - | SMI |
| `Survival_ColdNeedMaxValue` | 1000 | **900** | - | SMI |
| `Survival_ExhaustionNeedValue` | 140 | 85 | **75** | Starfrost |
| `Survival_ExhaustionNeedMaxValue` | 960 | 578 | **600** | Starfrost |

Both halves the user asked for - hunger and cold - are live vanilla
`Survival_*NeedValue` / `Survival_*MaxValue` pairs with sane ranges. That decides which
widget mods can work at all:

- **Anything that reads the value/max pair renders a true proportional bar here.**
- Anything that reads Starfrost's *magic effects* renders discrete stages, and
  Starfrost only applies its display effects from **stage 3** - so there is no readout
  at all until the character is already badly off.

`SURVIVAL_COMPARISON.md` recorded that Starfrost 2.0.0 "consolidated its Hunger onto
SM's native infrastructure"; the global dump is the confirmation, and it is the most
useful fact in this record.

### Candidates, measured

| mod | version | updated | mechanism | DLL | gate |
|---|---|---|---|---|---|
| [iWant Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/36457) (36457) | 1.33 | 2024-06-04 | Papyrus + SWF widget library with **native meters** | **none** | n/a |
| [iWant Status Bars](https://www.nexusmods.com/skyrimspecialedition/mods/36460) (36460) | 2.09 | 2022-11-22 | state-icon manager on top of iWant Widgets, up to 10 states | **none** | n/a |
| [iWant Widgets NG](https://www.nexusmods.com/skyrimspecialedition/mods/96410) (96410) | 1.2.8 | 2024-06-07 | optional native accelerator | yes | **FAIL** |
| [iWant Widgets for Starfrost](https://www.nexusmods.com/skyrimspecialedition/mods/162769) (162769) | 2.0 | 2026-08-23 | reads Starfrost **magic effects**, 4-stage icons | none | n/a |
| [SMI UI Widgets for Needs Display](https://www.nexusmods.com/skyrimspecialedition/mods/91878) (91878) | 1.0 / 1.11 | 2023-05-25 | iWant state icons off SMI globals | none | n/a |
| [Survival Mode Prisma Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/185796) (185796) | 1.3 | 2026-08-14 | reads the value/max pair, **true draining bars** | via Prisma UI | **blocked** |
| [Prisma UI](https://www.nexusmods.com/skyrimspecialedition/mods/148718) (148718) | 1.4.1 | 2026-03-27 | HTML/CSS/JS UI framework | yes | **FAIL** |
| [Skyrim Party Sheet](https://www.nexusmods.com/skyrimspecialedition/mods/167538) (167538) | 3.1 | 2026-07-29 | all-in-one party/player HUD including survival | yes | **FAIL** |
| [Survival Control Panel](https://www.nexusmods.com/skyrimspecialedition/mods/41891) (41891) | 1.1.2 | 2022-10-02 | Survival feature framework, **not a readout** | yes | see below |

### Gate results, with PE stamps

`py -3 audit/skse_version_data.py`, under the corrected reject window (upper bound
2026-08-21, the day CommonLibSSE-NG gained Address Library format 5 support - #197):

| DLL | PE TimeDateStamp | UTC | independence / Ex | V5 bit | verdict |
|---|---|---|---|---|---|
| `TrueHUD.dll` 1.1.10 | 1788028501 | **2026-08-29 18:35:01Z** | 1 / 3 | **YES** | **PASS (version independent)** |
| `AHZmoreHUDPlugin.dll` 5.4.2.0 | 1788128891 | **2026-08-30 22:28:11Z** | 1 / 1 | no | **PASS** - stamped after the support date, which is what makes it safe |
| `PrismaUI.dll` 1.4.1 | 1774640351 | 2026-03-27 19:39:11Z | 1 / 1 | no | **FAIL** - addrlib-v5 flag missing AND stamp inside the reject window |
| `SkyrimPartySheet.dll` 3.1.0.0 | 1785256641 | 2026-07-28 16:37:21Z | 1 / 1 | no | **FAIL** - same reason |
| `IWantWidgetsNative.dll` 1.2.4 | 1717743913 | 2024-06-07 07:05:13Z | 1 / 1 | no | **FAIL** - same reason |

Archive hashes for the record:

    62775-798218.7z   TrueHUD 1.1.10           sha256 ad10182e0806c47998bc6bf7badd34b8160c9ff008b85b796245e031a77ceed5
    12688-797906.7z   moreHUD 5.4.2.0          sha256 957434d70f8bbbcdd1506d963b161f9d480e0f60a9586411fd86f923a8d1ada1
    148718-735761.zip Prisma UI 1.4.1          sha256 791414f212fd5d3a807d801ec8ae725d39ec510c7b033da6338733779bf28b68
    167538-782487.zip Skyrim Party Sheet 3.1   sha256 a0d4813fff189e04739cbb65eb74e90742e026df074f70995e91656195a18230
    96410-509224.zip  iWant Widgets NG 1.2.8   sha256 d32d3c2ae6b3d12dd84a3bf5010869b8cc963782cb8edad4ad526933a64a09fc
    36457-508135.7z   iWant Widgets 1.33       sha256 192ff1953e67b3c8a1543102ff283d4920a0f107bb602acb28e3a2f83f0c8eb7
    36460-333629.7z   iWant Status Bars 2.09   sha256 34c1ab6f8b165ee2d1ff725881b90b8985047655e95c62b18b16ef1b5ace76e7

### The Survival Control Panel question, resolved

Prior research (`docs/DEFERRED_DECISIONS.md`, cloak thread) left "authorize a 1.7.104
[Survival Control Panel](https://www.nexusmods.com/skyrimspecialedition/mods/41891)
port" open. **It is not the route for this request**, and for a reason that has nothing
to do with the port: SCP is a *configuration* framework - "a framework for mods and
players to customize native Survival Mode features like Sleep to Level Up, with added
support for cloaks". It exposes settings and a cloak warmth slot. It renders no hunger
or warmth meter. Porting it would answer the cloak question in #95; it would not put a
bar on screen. The two questions should stop travelling together.

### What the widget mods actually draw

- **[iWant Widgets for Starfrost](https://www.nexusmods.com/skyrimspecialedition/mods/162769) 2.0**
  is the natural-looking answer and is the wrong one. Its script
  (`Source/Scripts/iWant_Starfrost_Widgets.psc`) watches
  `MAG_HungerStage03/04/05DisplayEffect`, `MAG_ColdStage3/4/5DisplayEffect`,
  `MAG_ExhaustionStage3/4/5DisplayEffect` and `MAG_StarfrostInjuryEffect01-03`, and
  drives a 4-state icon that is **invisible at state 0**. Nothing appears until the
  character is already at stage 3. It is a warning light, not a gauge.
- **[SMI UI Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/91878)** is the
  same shape - iWant *state icons* off SMI's globals. `iWant Status Bars`' own API
  describes its unit as "a set of widgets ... loaded into a **state icon**" with up to
  ten states.
- **[Survival Mode Prisma Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/185796) 1.3**
  is the only shipped mod that draws a real continuously-filling bar off exactly the
  global pair this build populates. Its author states the contract: "This mod
  technically works with ANYTHING that has the same editorid survival global values ...
  like for example `Survival_HungerNeedValue` + `Survival_HungerNeedMaxValue`".
  Position, size and opacity are configured in the SKSE menu, and **SKSE Menu Framework
  is already installed**. It is blocked only by Prisma UI's DLL.

### Prisma UI as a rebuild: the licence blocks the shipping half

Prisma UI is source-available at
[`github.com/PrismaUI-SKSE/framework`](https://github.com/PrismaUI-SKSE/framework) (full
C++, CMake, `src/`). The **Prisma UI License** permits "modify the framework for your
own **private** use" and "share and distribute the **original, official** framework
files", and restricts "publicly release or distribute your own modified versions
without explicit written permission". It also embeds the Ultralight SDK under the
Ultralight Free License.

Consequence under `docs/CURATION_POLICY.md` ("Every fix is a shippable patch or a
reproducible recipe") and the 2026-09-02 eligibility ruling (#160): a locally rebuilt
`PrismaUI.dll` would be **`local-only`** - it cannot be packaged in the Ensrick
collection, and "the installer rebuilds it from source" is at best a grey reading of
"private use". That is a user decision, not a technical one, and it is the single thing
standing between this build and the readout he asked for.

### Suggestion for the survival readout

**[iWant Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/36457) 1.33
(36457) plus a small owned Papyrus widget, `Ensrick - Survival Meters`.** No SKSE DLL
anywhere in this route. It needs the user's permission because iWant Widgets is a
download.

Why this shape rather than a workaround:

- iWant Widgets has **native meters**. Its API ships
  `setMeterPercent(Int id, Int percent)` - "Sets the percentage of the meter to fill" -
  plus `setMeterColors(light, dark, flash)` and `doMeterFlash`. That is a true fill bar,
  not a state icon; `iWant Status Bars` (36460) is the *icon* layer on top and is not
  needed for this.
- It ships **no DLL**: an `.esl`, one SWF and Papyrus. Its only requirement is SkyUI,
  which is installed.
  [iWant Widgets NG](https://www.nexusmods.com/skyrimspecialedition/mods/96410) is only
  an optional native accelerator and is the piece that fails the gate - declined, not
  needed.
- It is **MIT licensed** ("You may freely modify and distribute it as you see fit",
  `documentation/README.html`), so it is a clean vendor row and our widget is
  `distributable` Ensrick work rather than `local-only`.
- The data contract is the verified global pair above. Poll on
  `RegisterForSingleUpdate`, compute the percentage, call `setMeterPercent`. No numbers
  on screen, which is what he asked for.

Fallback if he would rather not wait for an owned widget:
[Survival Mode Prisma Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/185796)
plus a local [Prisma UI](https://www.nexusmods.com/skyrimspecialedition/mods/148718)
rebuild, accepted as `local-only` and therefore excluded from anything shared.

Explicitly **not** suggested:
[iWant Widgets for Starfrost](https://www.nexusmods.com/skyrimspecialedition/mods/162769)
(invisible until stage 3) and
[Skyrim Party Sheet](https://www.nexusmods.com/skyrimspecialedition/mods/167538) (fails
the gate, and its payload is a whole party HUD he did not ask for).

## 2. Is NORDIC UI "the meta"?

No, and the survey is right. `docs/ECOSYSTEM-SURVEY-2026-08-30.md` records **NORDIC UI
0/19** across the surveyed exports, against SkyUI 19/19, TrueHUD 17/19, moreHUD 17/19,
UIExtensions 17/19, MCM Helper 16/19. The addendum qualifies it precisely: NORDIC UI
"survives only in Invicta's alpha export" (Load Order Library alpha 0.9.8.6.1,
2026-07-15) - no *released* list ships it.

The Nexus record says why without needing the survey:
[NORDIC UI - Interface Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/49881)
(49881) is v2.4.1, **last updated 2021-08-14** - five years stale - and its own summary
is "Replaces *everything*. Requires SkyUI and **SkyHUD**." SkyHUD is a `hudmenu.swf`
replacer, which puts it in direct competition with the HUD layer this build would
otherwise adopt, and NORDIC UI's own HUD carries enemy health bars (mod
[54779](https://www.nexusmods.com/skyrimspecialedition/mods/54779) exists solely to
patch moreHUD's bars into it).

So NORDIC UI is famous, well-liked and the wrong pick here: stale, demands a HUD
replacer, and ships the exact thing the user says he hates. Its 24,381 endorsements are
the "meta" impression; they are a 2021 number.

## 3. The skin

Judged against his stated taste, not popularity. All four are SkyUI *menu* replacers -
they do not touch the HUD - so the floating-bar objection does not discriminate.

| skin | version | updated | endorsements | note |
|---|---|---|---|---|
| [Dear Diary Dark Mode](https://www.nexusmods.com/skyrimspecialedition/mods/60837) (60837) | 1.1.1 | 2022-11-05 | 13,770 | ancestor of the other two; largest patch ecosystem |
| [Untarnished UI](https://www.nexusmods.com/skyrimspecialedition/mods/75188) (75188) | 1.1.6 | 2023-07-01 | 7,319 | "flat and modern ... **while feeling similar to its original style**", based on DDDM |
| [Edge UI](https://www.nexusmods.com/skyrimspecialedition/mods/130983) (130983) | **0.6.1** | 2024-10-09 | 4,969 | "inspired by modern AAA games like God Of War, Assassins Creed, Horizon and Elden Ring ... **This is still a WIP, as the author is a newbie in coding and designing**" |
| [NORDIC UI](https://www.nexusmods.com/skyrimspecialedition/mods/49881) (49881) | 2.4.1 | 2021-08-14 | 24,381 | see above |

**Suggestion: [Untarnished UI](https://www.nexusmods.com/skyrimspecialedition/mods/75188).**
The deciding argument is his own taste as recorded elsewhere in this project: the
vanilla-shape preference that protects vanilla iron armour and steel gauntlets in
`docs/PATCH_INTENTS.md`, and the distance-detail rule that rejects "matte, single-tone"
modern flatness. Untarnished's stated design goal is the only one of the three that
names staying close to the original style. Edge UI is explicitly styled after modern
AAA games, is still 0.x, and its author's own page calls it a work in progress by a
self-described newbie - the opposite end of the same axis, and a low-currency bet.
Dear Diary Dark Mode is the safe third choice with the deepest patch ecosystem.

Taste call; overrule freely. The survey ties DDDM and Untarnished at 7/19 and puts Edge
UI at 3/19, so ecosystem weight does not decide it either.

If Untarnished is chosen,
[RaceMenu - Untarnished UI - DIP Patch](https://www.nexusmods.com/skyrimspecialedition/mods/97347)
(97347, updated 2026-04-21) matters here, because RaceMenu runs under an Ensrick native
overlay.

## 4. The floating-healthbar problem

**[TrueHUD](https://www.nexusmods.com/skyrimspecialedition/mods/62775)'s floating bars
can be switched off with one flag, and the mod keeps everything that makes it
near-universal.** Receipt, from the shipped `MCM/Config/TrueHUD/settings.ini` in
TrueHUD 1.1.10:

    [Main]
    bEnableActorInfoBars = 1
    bEnableBossBars      = 1
    bEnablePlayerWidget  = 1
    bEnableRecentLoot    = 1
    bEnableFloatingText  = 0

The four features are independent booleans. `bEnableActorInfoBars = 0` removes the
entire floating world-space bar system (the `[ActorInfoBars]` block's 33 keys -
`uInfoBarDisplayHostiles`, `bInfoBarDisplayPhantomBars`, `bInfoBarScaleWithDistance`,
`fInfoBarOffsetZ` and the rest - all become inert). `bEnableFloatingText` is **already
0 by default**, so floating damage numbers are off out of the box.

What survives with actor info bars off:

- the **player widget** - a repositionable health/magicka/stamina group, fixed to the
  HUD, not floating over anything;
- **boss bars** - a single anchored bar at the top of the screen, again not world-space;
- the **recent loot** log;
- the **API**, which is the real reason TrueHUD is in 17 of 19 lists: other SKSE plugins
  draw their special-resource bars through it.

So the answer is "install it and turn one flag off", not "skip it" - as a suggestion.
MCM Helper is already installed, so the setting is reachable in-game, and the shipped
`settings.ini` could be pre-set by an Ensrick config overlay (`distributable`) if he
adopts it.

[moreHUD SE](https://www.nexusmods.com/skyrimspecialedition/mods/12688) (12688,
5.4.2.0, DLL stamped 2026-08-30, **PASS**) extends the crosshair/target readout with
text - level, ingredient effects, read-book state. It does not add world-space bars.
`[unverified]` beyond package inspection: its display code lives in `AHZmoreHUD.bsa`
and was not decompiled.

## 5. Suggested UI stack (nothing installed)

In adoption order, all of it gated or DLL-free. **Every row needs the user's go-ahead.**

1. [TrueHUD](https://www.nexusmods.com/skyrimspecialedition/mods/62775) 1.1.10 (62775) -
   gate PASS, PE 2026-08-29, V5 bit set - with an Ensrick config overlay setting
   `bEnableActorInfoBars = 0`.
2. [moreHUD SE](https://www.nexusmods.com/skyrimspecialedition/mods/12688) 5.4.2.0
   (12688) - gate PASS, PE 2026-08-30.
3. [iWant Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/36457) 1.33
   (36457) - no DLL, MIT, requires SkyUI.
4. `Ensrick - Survival Meters` - owned Papyrus widget on iWant's `setMeterPercent`,
   reading the verified global pairs. Hunger and cold first; exhaustion is free once
   the scaffolding exists. This is **ours to build** once row 3 is approved.
5. [Untarnished UI](https://www.nexusmods.com/skyrimspecialedition/mods/75188) 1.1.6
   (75188) plus its
   [RaceMenu DIP patch](https://www.nexusmods.com/skyrimspecialedition/mods/97347)
   (97347) - taste, deferred to the user.

Deliberately excluded:
[NORDIC UI](https://www.nexusmods.com/skyrimspecialedition/mods/49881) (stale, needs
SkyHUD, ships enemy bars),
[Prisma UI](https://www.nexusmods.com/skyrimspecialedition/mods/148718) +
[Prisma Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/185796) (DLL fails
the gate; rebuild is `local-only` under its licence),
[Skyrim Party Sheet](https://www.nexusmods.com/skyrimspecialedition/mods/167538) (DLL
fails the gate),
[iWant Widgets NG](https://www.nexusmods.com/skyrimspecialedition/mods/96410) (DLL fails
the gate, optional anyway),
[iWant Widgets for Starfrost](https://www.nexusmods.com/skyrimspecialedition/mods/162769)
(stage-3 icons, not a gauge),
[Survival Control Panel](https://www.nexusmods.com/skyrimspecialedition/mods/41891) (a
config framework, not a readout).

## 6. What can be done with no new mod at all

Searched for this specifically after the 2026-09-03 constraint. The honest answer is
**one lever, and it needs a question answered before it is pulled.**

SkyUI, MCM Helper, SKSE Menu Framework, RaceMenu and UIExtensions cannot draw a HUD
meter between them: SkyUI's HUD extension has no public Papyrus API for arbitrary
meters, SKSE Menu Framework is an ImGui *config* menu that needs a plugin to host a
page, and neither Starfrost nor SMI ships an MCM (both are configured by ini). So a
bar genuinely cannot be produced from the installed set.

What *is* there: **Survival Mode Improved ships its own ambient-warmth indicator, and
it is threshold-gated.** From the effective ini (Starfrost's copy at higher priority
wins, and both copies carry the same value):

    [Cold Settings]
    #Warmth widget for ambient warmth will not appear if the ambient temp is higher than this threshold
    fAmbientWarmthWidgetColdLevelThreshold=200.0

Against `Survival_ColdNeedMaxValue = 900` and `Survival_ColdLevelInFreezingWater = 900`
(SMI), 200 is a low band, so the indicator is hidden across most of the map. Raising it
would show the ambient-warmth readout in far more places - which is adjacent to, though
not the same as, "how cold am I".

**Not changed, deliberately.** The comment's direction is ambiguous ("ambient temp
higher than this threshold" in a system where a *higher* number means *colder*), and
the only honest way to settle it is one in-game check. Changing a vendor ini blind, at
night, to a value whose sign I cannot prove, is exactly the kind of unverifiable edit
this project's rules exist to prevent. The change itself is one line in an Ensrick
config overlay - the same shape as `Ensrick - SSE Display Tweaks Configuration` - and
takes minutes once the direction is known.

## 7. Questions only the user can answer

1. **Permission to download anything at all** for this slot - the readout needs at
   minimum [iWant Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/36457).
2. **Skin:** Untarnished UI, Dear Diary Dark Mode, or none?
3. **Prisma UI:** accept a `local-only` rebuilt DLL - excluded from anything shared - to
   get Prisma Widgets now, or wait for the owned iWant meter widget which is
   distributable? Or ask StarkMP for written redistribution permission?
4. **Meter placement and style:** how many meters at once (hunger and cold only, or
   exhaustion too), always visible or fading in above a threshold, and where.
5. **TrueHUD player widget:** with floating enemy bars off, does he want TrueHUD's own
   player health/magicka/stamina bars, or only the API plus boss bars with the vanilla
   player HUD left alone?
6. **The ambient-warmth threshold** in section 6 - worth one in-game check on the next
   session?

## 8. Tracked as issues

- [#202](https://github.com/Ensrick/skyrim-mod-assistant/issues/202) `Ensrick - Survival
  Meters` on iWant Widgets - the hunger/warmth bar.
- [#205](https://github.com/Ensrick/skyrim-mod-assistant/issues/205) TrueHUD with
  `bEnableActorInfoBars = 0` as a shipped config overlay, plus moreHUD.
- [#203](https://github.com/Ensrick/skyrim-mod-assistant/issues/203) Prisma UI 1.7.104
  rebuild - a gate failure plus a licence question, so a decision issue rather than a
  build issue.
- Skin verdict folded into [#35](https://github.com/Ensrick/skyrim-mod-assistant/issues/35);
  component layer tracked on [#111](https://github.com/Ensrick/skyrim-mod-assistant/issues/111);
  survival readout on [#31](https://github.com/Ensrick/skyrim-mod-assistant/issues/31).
