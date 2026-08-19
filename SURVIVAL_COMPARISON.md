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

## Close review - pros, cons, and quality/QA signals

Evidence base: plugin form versions, Papyrus source reading, BSA raw scans, packaging contents,
full changelog histories (v1 API), endorsement/unique-download ratios. All 44 plugins across the
seven archives are form version 44 (properly ported; no LE leftovers anywhere). Endorsement ratios
are NOT comparable across eras (2016 mods sit near 5-7%, 2022+ mods near 1.5% regardless of
quality); use changelog behavior instead.

### Survival Mode Improved - SKSE (2.3M dl)
**Pros:** near-everything lives in the DLL - only 4 Papyrus scripts (159 LOC), zero polling, zero
debug spam; ships a 6-function **global-native modder API** (`SurvivalModeImprovedApi.psc`) so other
mods can restore needs cleanly; ships PDBs for crash-log symbolication (community best practice);
36 changelog entries with mature engineering judgment - 1.6.6 *reverted* a minor bugfix because it
correlated with unreproducible CTDs ("not worth potential crashes"); actively removes vanilla SM's
scripts from aliases to prevent AV corruption; AE+SE dual builds in FOMOD.
**Cons:** no thirst; no MCM (ini only - config changes need a file edit, not in-game UI); CommonLib
DLL means each future runtime break waits on the author (single-maintainer bus factor); vanilla SM
look-and-feel retained.
**QA signals:** all positive. This is the cleanest engineering in the field.

### Starfrost 2.0.0 (196k unique dl)
**Pros:** all-ESL, tiny (474-record core, 21 scripts, all RegisterForSingleUpdate); v2.0.0 (Aug
2026) consolidated its Hunger onto SM's native infrastructure specifically to kill bugs (Hunger
progressing in Oblivion, stalling during waits) - architectural convergence, not divergence; KID
warmth-by-armor-class auto-covers any armor mod (ideal under heavy asset replacement); tuning
shipped as data (SMI ini override, penalty cap 0.5); modular FOMOD - Injury addon cleanly isolated
behind its 4 Simonrim masters, VanillaHunger addon removes the Gourmet assumption.
**Cons:** young v2 (4 days old at review); hunger balance still designed around Gourmet portions
even with VanillaHunger; adds KID as a dependency; SimonMagus's strong design opinions arrive with
it (no thirst by philosophy, specific debuff curves); no MCM by design.
**QA signals:** positive - 14 changelogs, each fix specific and testable. One `mag_simonisnice_script`
easter egg tells you the code is hand-written, not generated.

### SunHelm 3.1.4 (681k unique dl)
**Pros:** the only maintained-era all-in-one WITH thirst; clean system decomposition visible in
script names (separate cold/hunger/thirst/fatigue/region/weather systems); 47 changelogs; honest
release discipline (3.1.3a: "Sorry everyone, it was a mistake with the last upload"); modular esps
(force-disable-cold for Frostfall pairing, separate diseases, Campfire skill tree); vampire/lich/
werewolf edge cases explicitly scripted; final release even removed an accidentally-shipped stray
file - they audit their own packaging.
**Cons:** frozen since 2022-08 because the author moved on to SMI - it is the author's own
superseded system; full esp slot; all-Papyrus cold system duplicates what SM now does natively;
the odd `EWM_SunhelmSurvivalSE.esp` is a 354-byte header-only dummy plugin (harmless but inelegant).
**QA signals:** good hygiene, but "superseded by its own author" is the loudest signal here.

### Frostfall 3.4.1SE (779k unique dl)
**Pros:** still the deepest exposure simulation ever built for the game (wetness, gear coverage,
climate zones, rescue system); the architecture is genuinely professional - a five-script fallback
event bus, armor-protection datastores, 58 single-update registrations vs only 2 legacy
`RegisterForUpdate` sites; Chesko's engineering reputation is earned.
**Cons:** zero updates since 2016-12 and zero changelogs on SE; requires the third-party Unofficial
SSE Update (2021) just to fully function on current runtimes, and Script Optimization (2025) to fix
accumulated script errors - the mod now depends on community life support; 112 Debug.Trace call
sites in source (papyrus log noise when enabled); per-armor warmth datastore fights an
asset-replacement-heavy list; SkyUI-5-era meter widgets under SkyUI 6.x [untested against 6.11].
**QA signals:** excellent code from a departed author. "Abandonware with a fan-run pit crew."

### Last Seed 5.3 (62k unique dl)
**Pros:** the most feature-complete needs system (wellness, spoilage, per-food data, wells); 54
changelogs, active through 2024; 84 `GetFormFromFile` soft-dependency checks = patches degrade
gracefully; 32 curated compat patches is real ecosystem work; 5.3 tracked AE's update.esm water
record changes - they follow Bethesda updates.
**Cons - and this is where the QA flags live:** shipped a 1.3 MB `.psc.BACKUP` file, a Windows
`Source - Shortcut.lnk` from the author's desktop, a stray nested zip, and an xEdit `.pas` script;
`_Seed_FoodDatastoreHandler` (379 KB source, 125 KB **compiled and shipped**) opens with "NOT
CURRENTLY USED"; `_Seed_SpoilSystem_old.psc` dead legacy source shipped; 84 TODO/FIXME markers and
148 debug call sites across 32k LOC; 5.2.1 changed the plugin header version 1.71 -> 1.7 after
shipping CTDs to pre-1.6.1130 users; a patch esp still named `TaberuAnimation_iNeed Patch.esp`
(copy-pasted from an iNeed patch) and it is one of several patches left un-ESL-flagged.
**QA signals:** enthusiastic, feature-rich, sloppy. A working-directory snapshot, not a release
pipeline. Functional, but you will be the QA.

### iNeed 1.90 Alpha 1 (536k unique dl)
**Pros:** the most compact classic needs implementation (27 scripts); clean single-update
architecture; low debug noise (7 traces).
**Cons:** the original's MAIN file has been literally named "Alpha 1" since 2017 with no changelog
after 1.83 - abandoned mid-release; isoku is inactive on SE.
**QA signals:** was tidy for its day; the version string is the tombstone.
**Correction (2026-08-19):** the original is abandoned, but a maintained fork exists -
**iNeed - Food Water and Sleep - Continued** (19390, nodude2016, updated 2025-09-26). The
"iNeed is dead" framing above applies only to mod 645; the Continued fork is a live thirst-bearing
option alongside SunHelm and Last Seed. Verdict for this list is unchanged (thirst micromanagement
is the tedium we are avoiding), but it belongs in the field, not the graveyard.

### RND All-In-One 1.0.5c (141k unique dl)
**Pros:** the fullest disease/inebriation simulation of the classic era; 2023 repack keeps it
installable.
**Cons:** hard USSEP master (disqualifying here); LE-era timer-polling design (`rnd_hungertimerscript`
etc.); changelog shows the same "added back a missing interface file" fix twice in a row and a
vague "fixed some reported issues" - packaging fumbles with low-information notes.
**QA signals:** maintenance is custodial, not developmental.

### CC Survival Mode (owned baseline)
**Pros:** engine-native hooks, zero cost, Bethesda QA'd, the substrate SMI/Starfrost build on.
**Cons:** by itself: no thirst, blunt penalties, art-direction warmth (the exact thing Starfrost's
KID rule fixes), fast-travel lock not configurable without a tweak mod.

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
4. **Skip regardless of scale**: RND (USSEP master). iNeed's original (645) is abandoned at its
   2017 alpha, but see the correction below - its maintained fork (19390) is a live option if
   thirst is ever wanted.

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
