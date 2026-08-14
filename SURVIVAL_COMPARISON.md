# Survival Mods - Empirical Teardown Comparison

Compiled **2026-08-14**. Method: downloaded each mod's current MAIN file via the Nexus v1 API
(per `NEXUS_API.md`; SHA256 + file IDs recorded in `work/survival-comparison/archives/manifest.json`,
ignored), extracted all seven archives, parsed plugin headers (ESL/ESM flags, record counts, masters),
enumerated scripts inside BSAs, dumped SKSE DLL strings, and read every ini/FOMOD. Baseline is the
CC Survival Mode + Camping content already installed (`ccqdrsse001-survivalmode.esl`,
`ccqdrsse002-firewood.esl`, verified in game Data).

## The field

| Mod | ID | Version (file) | Last update | Core plugin | ESL? | Scripts | Native code |
|---|---|---|---|---|---|---|---|
| Survival Mode Improved - SKSE | 78244 | 1.6.6 | 2026-06 | 274 records | **yes** | 4 pex | **758 KB DLL** (AE+SE builds) |
| Starfrost - A Survival Overhaul | 97536 | 2.0.0 | 2026-08 | 474 records | **yes** (all 3 esps) | 21 pex | rides SMI's DLL |
| SunHelm Survival | 39414 | 3.1.4 | 2022-08 | 531 records | no | 38 pex | none |
| Frostfall | 671 | 3.4.1SE | 2016-12 | 1303 records | no | 91 pex | none |
| Last Seed (Aytrus continuation) | 56393 | 5.3 | 2024-07 | 2182 records | no | 133 pex | none |
| iNeed - Food Water and Sleep | 645 | 1.90A1 | 2017-10 | 551 (+4.3k Extended) | no | 27 pex | none |
| Realistic Needs and Diseases AIO | 3487 | 1.0.5c | 2023-09 | 1220 records | no | 53 pex | none |
| CC Survival Mode (baseline, owned) | - | AE | - | ccqdrsse001 esl | esl | in BSA | engine-native hooks |

## Mechanics coverage

| Mechanic | CC SM | SMI | Starfrost | SunHelm | Frostfall | Last Seed | iNeed | RND |
|---|---|---|---|---|---|---|---|---|
| Hunger | y | y | y (rebalanced) | y | - | y | y | y |
| Thirst | - | - | - | **y** | - | **y** | **y** | **y** |
| Sleep/exhaustion | y | y | y | y (fatigue) | - | y | y | y |
| Cold/exposure | y | y (rebuilt) | y (armor-weight warmth) | y (own system) | **y (deepest: wetness, coverage, climate zones)** | - | - | - |
| Wetness | - | - | - | - | **y** | - | - | - |
| Disease overhaul | harsher vanilla | y (hit-event based) | y | y (progression) | - | y (progression) | basic | y (progression + inebriation) |
| Injury need | - | ini hooks | **y (optional module)** | - | - | - | - | - |
| Food spoilage | - | - | - | - | - | y | y | y |
| Camping skill/XP | - | - | - | y (Campfire skill esp) | y (endurance XP) | - | - | - |

## Teardown findings (what the archives actually contain)

### Survival Mode Improved - SKSE 1.6.6
- One ESL-flagged esp (274 records) over the CC esl + a 758 KB CommonLibSSE-NG DLL; 4 Papyrus scripts total. FOMOD picks AE vs SE DLL; AE build covers 1.6.1170.
- DLL strings prove **hardcoded integrations**: `Campfire.esm`, `Campsite.esp`, `ccqdrsse002-firewood.esl` (CC Camping), Wyrmstooth + Bruma region data loaders, `ObsidianWeathers.esp`, `SnowOverSkyrim.esp`, `Undeath.esp`, `The Path of Transcendence.esp`, `Starfrost.esp`, Address Library (`versionlib-{}.bin`).
- Ini config surface: fast-travel toggle, auto-enable, carry-weight-penalty toggle, disease hit-event toggle, per-need vampire behavior, injury AV percents, blizzard wind-speed threshold, warmth-rating cap, and **full per-month season multipliers with a prebuilt Seasons of Skyrim profile**.
- No MCM: configured via ini + the vanilla Survival settings. Cost: 0 load slots (ESL), ~0 Papyrus load.

### Starfrost 2.0.0
- Three ESL-flagged esps + 21 `mag_` scripts + a 2-line KID ini. **Core Starfrost.esp masters are only vanilla + ccqdrsse001 + SurvivalModeImproved.esp - the core does NOT require Simonrim.** Only the optional `StarfrostInjuries.esp` pulls `Pilgrim.esp`, `MysticismMagic.esp`, `BladeAndBlunt.esp`; optional `StarfrostVanillaHunger.esp` keeps vanilla hunger pacing (no Gourmet needed).
- KID distributes warmth by armor class (`ArmorClothing` -> Cold, `ArmorHeavy` -> Warm): warmth follows build, not fur aesthetics. Requires Keyword Item Distributor.
- Ships an overriding SMI ini: max attribute penalty softened 1.0 -> 0.5, vampire cold off, food poisoning forced on. "Survival Lite" is a config philosophy, implemented in data.

### SunHelm 3.1.4 (colinswrath's pre-SMI system)
- 531-record esp (not ESL) + 38 scripts (hunger/thirst/fatigue/cold/disease/region/weather systems, MCM, widgets). All-in-one incl. **thirst**, the one need CC SM lacks.
- FOMOD includes `SunHelmForceDisableCold.esp` (pair with Frostfall), a **Campfire skill tree esp**, Wyrmstooth patch, and third-party compat esps. Superseded by SMI for cold-on-SM users, but still the lightest all-in-one WITH thirst.

### Frostfall 3.4.1SE
- 1303-record esp requiring `Campfire.esm` + **91 scripts**: exposure, coverage, climate, clothing datastore, armor-protection datastore, five "fallback receiver" event-bus scripts, two MCM panels. The deepest exposure simulation (wetness, gear coverage, per-region climate) and the heaviest Papyrus footprint in the field; untouched since 2016. Needs the Unofficial SSE Update patch on current runtimes.

### Last Seed 5.3
- 2182-record core esp (masters include `Campfire.esm` - **Campfire is required**) + **112 `_Seed_` scripts** + iWant widgets + 32 FOMOD patch esps (CACO, Requiem, Bruma, Falskaar, Hunterborn, Skills of the Wild, YOT, wells, inn meals...). Needs + wellness + disease + spoilage, no cold (designed to sit beside Frostfall). The maintained heir to Chesko's needs design; heavyweight, huge compat web, mostly non-ESL patches.

### iNeed 1.90 Alpha 1
- 551-record esp + 27 scripts; food/water/sleep, spoilage, basic disease, shelter detection; three "Extended" variants (~4.3k records) add food coverage. Compact but **alpha since 2017**; the classic lightweight pick before SunHelm existed.

### RND All-In-One 1.0.5c
- 1220-record esp with **USSEP as a hard master** (disqualifying for this no-USSEP list) + 53 scripts using timer-based polling (`rnd_hungertimerscript` etc.). LE-era design, repacked 2023.

## Decision frame for this modlist

Target scale: **1000-2000 plugins** ("minimal" relative to 8-10k builds, not a small list).
Hard constraints: no USSEP (kills RND), CC content owned, SkyUI 6.11 + Address Library pinned,
Campfire decision pending. At this scale the deciding criteria are **patch-ecosystem reach, full
esp-slot economy (~250 full slots against thousands of ESLs), and Papyrus budget shared with
hundreds of other script mods** - not raw mod count.

Two coherent endpoint stacks, one middle option:

1. **Modern native stack: SMI-SKSE + Starfrost core (+VanillaHunger, skip Injuries) + Campfire.**
   Zero full slots, ~25 scripts total, maintained 2026. The big-list advantage is structural:
   Starfrost's KID rule assigns warmth by armor class, so **every armor mod in a 2000-plugin list is
   covered automatically, no per-mod patches**; SMI's weather/worldspace integrations (Obsidian,
   Wyrmstooth, Bruma) are compiled in. Gap: no thirst, and cold simulation is simpler than
   Frostfall's (no wetness/coverage).
2. **Classic deep-sim stack: Campfire + Frostfall (+ Unofficial SSE Update + Script Optimization) +
   Last Seed.** Richest simulation (wetness, gear coverage, spoilage, wellness) and at this scale
   Last Seed's 32-patch FOMOD web (CACO, Hunterborn, Requiem, Bruma, Falskaar, SotW...) flips from
   liability to asset - it is built to sit inside big lists. Cost: 3 full esp slots, ~340 Papyrus
   scripts sharing the VM with the rest of the list, a 2016 exposure engine, and Frostfall warmth
   needs its datastore/patch route for mod-added armor (the ecosystem exists but is per-mod).
3. **Middle: SunHelm** - one full slot, all-in-one WITH thirst, moderate scripts, its own compat
   patch hub, Campfire skill esp included; cold layer can be disabled later if migrating to SMI.
4. **Skip regardless of scale**: RND (USSEP master), iNeed (2017 alpha, superseded by
   SunHelm/Last Seed).

The stacks are mutually exclusive at the cold layer (two exposure systems cannot coexist), but
either pairs with Campfire.

One list-direction criterion: the build aims to replace as much vanilla content as possible with
diverse, high-performance assets. Rule-driven systems (KID warmth by armor class, BOS-style swaps)
absorb asset churn automatically; datastore/per-mod-patch systems (Frostfall warmth values, Last
Seed food patches) need a patch touch every time a replacer swaps or adds items. Weight that by how
often the asset layer will change.

## Verdict against the owner's stated goals (2026-08-14)

Goals: comprehensive and in-depth; no player burden or tedium; seamless; no save restrictions.

That maps to **Stack 1 almost verbatim** - Starfrost's stated design goal is "Survival mechanics
with the least amount of tedium possible," and the teardown shows it is implemented as data over
SMI's native engine (penalty cap softened to 0.5, vampire cold off, food poisoning kept for depth):

- **SMI-SKSE + Starfrost core + KID** (+ StarfrostVanillaHunger until a food overhaul is chosen)
- **Campfire** for opt-in camping depth; Skills of the Wild later if progression depth is wanted
- Save restrictions: **none exist in any Skyrim candidate** (save-locking is a Fallout 4 Survival
  trait). CC SM's fast-travel lock is a one-line SMI ini toggle (`bDisableFastTravel`).
- Deliberately skipped as tedium engines: thirst micromanagement (SunHelm/Last Seed/iNeed), food
  spoilage timers, Frostfall's wetness/firewood micro-loop.

Archives + extracted trees stay in ignored `work/survival-comparison/` for deeper record-level
diffing (xEdit/Spriggit) if wanted.
