# BASELINE - the build manifest

2026-08-23. This document is the modlist, built top-down from requirements.
The keep list is not a to-do queue: it is an **approved-parts inventory** that
gets consulted when a line in this manifest wants filling. Anything in keeps
that no line ever pulls simply never gets installed, and that is fine.

**The arithmetic that dissolves the overwhelm** (1,071 keeps as of today):

| bucket | count | decisions required |
|---|---|---|
| already installed | 8 | 0 |
| claimed by decided slots | 10 | 0 |
| rivals awaiting a slot decision | 33 | **9 slot picks** |
| attached (follow whichever rival wins) | 12 | 0 |
| loser of a decided slot (AFT) | 1 | confirm skip |
| additive pool - textures, fixes, QoL, quests | **1,007** | **0** |

**Selection principle (user, 2026-08-23): prefer open source where possible** -
source availability is a first-class tiebreaker between rivals so problems can
be fixed via Claude instead of waiting on authors. Risk register (corrected
2026-08-23 after actually checking): RaceMenu skee64 IS source-available
(expired6978/SKSE64Plugins; author committed "Update RM to 1.7.99" on
2026-08-23 itself - self-buildable from the author's own port ahead of the
gated Nexus release). Proteus is MIT (phenderix/PROTEUS, Papyrus scripts);
only its small Nightfallstorm-converted SKSE DLL has no located source yet.
No fully-closed load-bearing mods remain confirmed in the build.

Nothing else "still needs review". The unreviewed Nexus catalogue is consulted
only per-slot during gap searches, never wholesale - that lesson is paid for.

The August purge deleted rivals *and* some decided winners (CBBE's base mod,
Pandora, the male skin, the crash logger). Those show below as **GAP**: decided
on paper, absent from keeps, re-acquire at install time. This is why the build
runs from this manifest downward, not from the keep list upward.

`[verify]` = old SKSE DLL; check `SKSEPlugin_Version` export at install (the
address-independence test). Never pre-filter on it - but 2026-08-23's first
launch proved it necessary-NOT-sufficient: version data can still whitelist
older runtimes, and address-library format bumps bite at load. The real gate
is `py -3 audit/launch_triage.py` after EVERY launch (parses skse64.log).
`py -3 audit/plugin_watch.py` polls the blocked pages for new uploads.

**1.7.99 ecosystem hold (2026-08-23 launch triage):** four DLLs refused the
new runtime and are parked: SSE Engine Fixes 7.0.20 (address library format 5
unsupported; MO2 mod DISABLED to kill the popup, preloader in game root is a
harmless no-op), RaceMenu RESTORED 2026-08-24 via self-built skee64 from the author's own
1.7.99 commit (records/selfbuild-2026-08-24-skse-skee64.md; overlay NIF
regression untested in-game), PapyrusUtil 4.6 and JContainers 4.2.13.1 (SKSE
disables the DLLs silently; mods left enabled - scripts are inert without
them). Consequences until updates land: NO character creation via RaceMenu,
Proteus (JContainers) and NFF (PapyrusUtil) storage broken - shakedown is
VISUALS ONLY, do not build real characters yet.

---

## Tier 0 - engine floor (install before first real session)

| mod | id | status |
|---|---|---|
| SKSE64 2.3.0 | 30379 | **SELF-BUILT master 2026-08-24** (ianpatt/skse64@14db212 incl. Expired PC-offset fixes; Nexus 2.3.0 backed up beside it; official release supersedes) |
| Address Library v12 | 32444 | **installed** |
| SSE Engine Fixes | 17230 | **PARKED 2026-08-23** - 7.0.20 rejects address library format 5 (1.7.99); mod disabled, preloader stays; watcher armed |
| Crash logger | 59818 | **installed** CrashLoggerSSE 1.25.0 (updated for 1.7.99 two days ago; Trainwreck stale since 2024) |
| USSEP | 266 | **installed** 4.3.9 (2026-08-21) |
| Bug Fixes SSE | 33261 | **installed** v10, address-independent |
| Scrambled Bugs | 43532 | **installed** v21, address-independent |
| SSE Display Tweaks | 34705 | **installed** 0.5.16, address-independent - config pass pending (fps cap / borderless decisions) |
| Skill Uncapper for AE | 82558 | **installed** 2.2.3, address-independent |

## Tier 1 - frameworks (everything else assumes these)

Installed: SkyUI, RaceMenu (`bExternalHeads=1` set), UIExtensions, JContainers,
PapyrusUtil, po3 Papyrus Extender, po3 Tweaks, ConsoleUtilSSE NG.

| mod | id | status |
|---|---|---|
| MCM Helper | 53000 | **installed** (ESL + BSA) |
| SPID | 36869 | **installed** |
| KID | 55728 | **installed** |
| Base Object Swapper | 60805 | **installed** |
| Open Animation Replacer | 92109 | **installed** |
| Pandora Behaviour Engine | 133232 | **installed** v4.4.0-beta; ONE interactive run via MO2 pending (headless --auto_run attempt timed out; only XPMSSE weapon styles depend on it) |
| XPMSSE | 1988 | **installed** (Extended + latest rig + RaceMenu MCM weapon styles); Skeleton Replacer HD 52845 layers on top later |
| FSMP | 57339 | in keeps - cloth-only policy, no body jiggle - install with first physics outfit |
| BodySlide and Outfit Studio | 201 | **installed** (tool; Curvy batch build pending) |
| Crafting Recipe Distributor | 52276 | **installed** |

## Tier 2 - identity systems (the premise) - all installed

Proteus 3.4.0 + Nether's Follower Framework (its hard requirement) + Skyrim
Unbound Reborn. Operating policy from the leak analysis: questlines are
**assigned to characters, not isolated** - quest state is save-global (DB is 1%
faction-gated, TG 6%), so one questline per character and content mods are
preferred quarantined (Vigilant: 3 NPCs in vanilla space out of 1,755). Main
quest deferred = no character reads as Dragonborn until late game, which is the
design, not a compromise.

## Tier 3 - decided content slots

| slot | decision | notes |
|---|---|---|
| Renderer | Community Shaders 1.8.3 + Skylighting/SSGI/Wetness/TerrainVariation/TerrainBlending/Upscaling + Particle Patch + ENB Light | **installed** 2026-08-23; Hair Specular undecided-not-installed; effects-11 pipeline NOT in stable core - Lux CS Effect 11 flip parked |
| Worldspaces | Bruma, Wyrmstooth, Beyond Reach, Moonpath, Gray Cowl 10th (141327), Vigilant (11849+11894 EN) | Falskaar and its 4 support mods skipped, evidence on file |
| Female body | CBBE Curvy, nude, vanilla outfit replacers, face pack, RaceMenu morphs | **installed** v2.0.3 |
| Female skin | Reverie: Athletic body normal, Sleek face, CBBE compat | **installed** v1.11.2 |
| Male body | HIMBO core 01b nude + BG-DG-DB refits + The New Gentleman 4.2.5 (framework, incl. Vigilant ini) | **installed** |
| Male skin | SkySight 2025 Ultra: HIMBO-Uncut, Clean+Hairy, vanilla head/age, default SSS | **installed** (6580) |
| Animation | Pandora | installed |
| Alternate start | Skyrim Unbound Reborn | installed; supports non-Dragonborn characters |
| Follower framework | NFF | forced by Proteus; **AFT (6656) is the one surviving loser - confirm skip** |
| Killmoves | VioLens + Kaputt | 3 challengers in additive pool to check against the pair, low priority |
| Underlayers | Underwear.dll 1.3 as engine, pool overridden to 10 vanilla poor/common garments (Roughspun, Belted Tunic, Farm/Miner sets, Ragged Robes) + our Period Underlayers SPID config (bandits Roughspun, jarls/merchants Fine Clothes) | **installed**; skimpy default meshes inert, TNG patch unnecessary (full-coverage); v1.3 is a "test version for 1.7.99" - watch first session; expand tiers with modded garment packs later |

## Tier 4 - the actual remaining work: 20 slot decisions

**A. Compare what's already in keeps** (9 slots, 33 mods):

| slot | candidates surviving in keeps | how it gets decided |
|---|---|---|
| Weather | **DECIDED 2026-08-23: Azurite III** + Azurite III CS 162153 (Dlizzio; incl. its own Darker Nights + IBL) + EVLaS + water fx fix - **installed** | swap same day: doodlum HDR 138991 + DrJacopo Darker Nights addon disabled (162153 page: incompatible) after user identified the mod he meant; rivals skipped per user order; Azurite Mists out (author: III needs no mist mods) |
| Landscape tex | Majestic Mtns, Cathedral Landscapes, aMidianBorn B&L, Majestic Landscapes, Gecko's 4K, RUSTIC MOUNTAINS (6) | file-level: coverage overlap + the audit tooling; mountains vs full-landscape are partly complementary |
| Interior lighting | **DECIDED 2026-08-23: Lux family** - Lux + Via + Orbis + Patch Hub + Lux CS + CC bundle (installing; dim beam/mist variants) | Lux re-entered via keeps and won on facts: every component active 2024-26, purpose-built CS bridge, hub officially patches Bruma/Wyrmstooth/Vigilant/Glenmoril/Unslaad (ELFX FOMOD: none). ELFX trio stays shelved as mid-save A/B fallback |
| Water | Cathedral Water, Simplicity of Sea, A Water Made For CS (3) | last two are CS-era; RWT purged |
| Horses | Convenient Horses, Simple Horse, Simplest Horses (3) | feature-set read; CH vs INIGO conflict already on file |
| Skeleton | XPMSSE + Skeleton Replacer HD (2) | layering question, not rivalry |
| Trees | SFO, Happy Little Trees (2) | NotWL purged despite its Wyrmstooth patch - candidate to re-enter |
| Combat feel | Wildcat, Smilodon (2) | same author, heavy vs light - read + play |
| Crafting | Ars Metallica, CCOR (2) | CCOR pulls WACCF family, already kept |

**A2. Slots discovered by the overnight keep review** (docs/KEEP_REVIEW.md sec E):
standing stones (3 rivals kept), religion (Wintersun vs Trua), vampire overhaul
(4 rivals kept, gates Proteus vampire patches), children policy, dragon package
layering, stagger (POISE vs combat-feel built-ins), and the CACO seam (CACO
overlaps iNeed food + CCOR crafting - decide CACO first).

**B. Gap-search slots** (11) - the purge or the original sweep left nothing/one:
perks (0 of 5 remain), grass (0), cities (0), camera (0), enemies (0), UI skin
(0), combat framework (0), architecture (0), survival (0 rivals; SMI-SKSE +
Starfrost + Campfire recommendation stands in `SURVIVAL_COMPARISON.md`,
Campfire kept), magic (Odin survives, Mysticism purged), sound (ISC survives,
AOS purged - both-with-patch was the note), college (JK's survives).

OVERNIGHT UPDATE: the gap-search half is largely done - the candidates were in
the undecided pool all along. docs/SLOT_CANDIDATES.md maps ~30 slots to their
harvested candidates (Lux, Mysticism, Folkvangr, NotWL, Skyland, NORDIC UI,
Valhalla, SunHelm, Vokrii/Adamant/Ordinator all alive there). Remaining work
per slot is comparison, not search.

## Decision order

1. **Interior lighting** - most patch-heavy slot, gates cities
2. Weather - in-game eyes, A/B protocol via console bridge
3. Landscape / trees / grass cluster - then DynDOLOD once, not per-change
4. Water
5. Gameplay cluster: perks, magic, combat framework + feel, survival confirm
6. Cities, per city, after lighting
7. Small slots: crafting, horses, college, camera, sound, UI skin, enemies, killmove challengers

## Standing tools

Install: `py -3 audit/install_mod.py <id> "<name>" [--prefer rx] [--plan file]`
then `--sort` (LOOT + re-enable), `--verify`, ledger in
`records/installed-mods.json`. Comparison: `audit/inspect_mod.py`,
`worldspace.py`, `ecosystem.py`, `integration.py`, `playfeel.py`. In-game:
`audit/console.py` writes `claude.txt`, run with `bat claude`.
