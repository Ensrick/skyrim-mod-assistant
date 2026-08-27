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

**Texture resolution policy (user, 2026-08-26): match the replaced source by
default.** Permit no more than one justified resolution step upward, cap
dedicated small-clutter textures at 1K on either axis, and cap every texture at
4K on either axis. Dimensions come from DDS headers rather than marketing
labels; rectangular atlases, companion maps, UV coverage, and actual added
detail are reviewed explicitly. The enforceable rules and exception evidence
requirements are in `docs/TEXTURE_POLICY.md`.

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

**1.7.99 ecosystem hold (rewritten 2026-08-26, receipts in
docs/HANDOFF-2026-08-27.md):** 15 mods are parked awaiting 1.7.99 builds
(modlist.txt `-` rows; ledger notes carry per-mod reasons), including the
Community Shaders RENDERER CORE (its 6 feature packs + Lux CS/Azurite III CS
stay enabled - inert/visual-mismatch only until core unparks), Proteus (no
build since 2024, closed source - campaign-pillar risk), SPID (po3 7.3.3
tagged upstream, release imminent), MCM Helper/OAR/Light Placer/CRD/EVLaS/
Display Tweaks/Scrambled Bugs/Bug Fixes/Skill Uncapper/TNG/JContainers.
UNPARKED 2026-08-26: SSE Engine Fixes 7.0.21 (official), PapyrusUtil 4.7
(official 1.7.99 build - Skyrim Unbound/NFF/CBBE-morph scripts unblocked).
JContainers 4.3.1 (author GitHub prerelease) installed but RE-PARKED: the
skse64 master plugin gate refuses it pending an AddressLibraryV5 compat
declaration - rebuild from source or await re-release. RaceMenu runs via
self-built skee64 (overlays OFF - engine NIF regression, no Bethesda hotfix);
official RaceMenu 1.7.99 is done per author, gated on the SKSE release.

---

## Tier 0 - engine floor (install before first real session)

| mod | id | status |
|---|---|---|
| SKSE64 2.3.0+ | 30379 | **SELF-BUILT master DEPLOYED 2026-08-26** (Ensrick/skse64 branch ensrick/headless-log-only = ianpatt@14db212 + log-only error reporting; CMake build, exports gate passed; fixes the official 2.3.0 GetNthTintMaskColor stale-offset Papyrus crash; Nexus 2.3.0 preserved as .bak.v2.3.0-nexus; official 2.3.1 release supersedes) |
| Address Library v12 | 32444 | **installed** |
| SSE Engine Fixes | 17230 | **installed** 7.0.21 beta (official 1.7.99 build; preloader retired) |
| Crash logger | 59818 | **installed** CrashLoggerSSE 1.25.0 + PDB pack 794129 (pack signature-mismatches the 1.7.99 exe - exe frames fall back to address-library IDs; self-built skse64 PDB deployed beside the dll) |
| USSEP | 266 | **installed** 4.3.9 (2026-08-21) |
| Bug Fixes SSE | 33261 | **PARKED 2026-08-25** - v10 popped at load on 1.7.99 (not address-independent after all); closed source, no rebuild path |
| Scrambled Bugs | 43532 | **PARKED 2026-08-25** - v21 popped at load on 1.7.99; open source (KernalsEgg/SKSE64Plugins), rebuild candidate |
| SSE Display Tweaks | 34705 | **PARKED 2026-08-25** - 0.5.16 popped at load on 1.7.99; open source, rebuild candidate |
| Skill Uncapper for AE | 82558 | **PARKED 2026-08-25** - 2.2.3 Rust versiondb asserts on address-library format 5; open source, porting work needed |

## Tier 1 - frameworks (everything else assumes these)

Installed and active: SkyUI, RaceMenu (`bExternalHeads=1`, overlays OFF),
UIExtensions, PapyrusUtil 4.7 (official 1.7.99), po3 Papyrus Extender, po3
Tweaks, ConsoleUtilSSE NG. JContainers 4.3.1 installed but PARKED (SKSE
master gate wants an AddressLibraryV5 declaration; rebuild or re-release).

| mod | id | status |
|---|---|---|
| MCM Helper | 53000 | **PARKED 2026-08-25** awaiting 1.7.99 build (ESL + BSA stay installed; local dll-target rebuild is the fallback path) |
| SPID | 36869 | **PARKED 2026-08-25**; po3 tagged 7.3.3 upstream 08-25 - release imminent |
| KID | 55728 | **installed** 4.1.0 (official 1.7.99) |
| Base Object Swapper | 60805 | **installed** 3.5.0 (official 1.7.99) |
| Open Animation Replacer | 92109 | **PARKED 2026-08-25** awaiting 1.7.99 build; open source, rebuild candidate |
| Pandora Behaviour Engine | 133232 | **installed** v4.4.0-beta; ONE interactive run via MO2 pending (headless --auto_run attempt timed out; only XPMSSE weapon styles depend on it) |
| XPMSSE | 1988 | **installed** (Extended + latest rig + RaceMenu MCM weapon styles); Skeleton Replacer HD 52845 layers on top later |
| FSMP | 57339 | in keeps - cloth-only policy, no body jiggle - install with first physics outfit |
| BodySlide and Outfit Studio | 201 | **installed** (tool; Curvy batch build pending) |
| Crafting Recipe Distributor | 52276 | **PARKED 2026-08-25** awaiting 1.7.99 build (po3 porting wave) |

## Tier 2 - identity systems (the premise)

Proteus 3.4.0 (**PARKED 2026-08-25**: no 1.7.99 build, closed source, author
silent since 2023 - PILLAR RISK, contingency decision pending; also needs
parked JContainers) + Nether's Follower Framework (installed+active; its
PapyrusUtil dependency satisfied by 4.7) + Skyrim Unbound Reborn
(installed+active; PapyrusUtil-dependent scripts unblocked by 4.7). Operating policy from the leak analysis: questlines are
**assigned to characters, not isolated** - quest state is save-global (DB is 1%
faction-gated, TG 6%), so one questline per character and content mods are
preferred quarantined (Vigilant: 3 NPCs in vanilla space out of 1,755). Main
quest deferred = no character reads as Dragonborn until late game, which is the
design, not a compromise.

## Tier 3 - decided content slots

| slot | decision | notes |
|---|---|---|
| Renderer | Community Shaders 1.8.3 + Skylighting/SSGI/Wetness/TerrainVariation/TerrainBlending/Upscaling + Particle Patch + ENB Light | CS CORE **PARKED 2026-08-25** - no 1.7.99 support yet (upstream draft PR #2674); feature packs stay enabled (inert without core); Lux CS/Azurite III CS esps render un-CS'd meanwhile; Hair Specular undecided-not-installed |
| Worldspaces | Bruma, Wyrmstooth, Beyond Reach, Moonpath, Gray Cowl 10th (141327), Vigilant (11849+11894 EN) | Falskaar and its 4 support mods skipped, evidence on file |
| Female body | CBBE Curvy, nude, vanilla outfit replacers, face pack, RaceMenu morphs | **installed** v2.0.3 |
| Female skin | Reverie: Athletic body normal, Sleek face, CBBE compat | **installed** v1.11.2 |
| Male body | HIMBO core 01b nude + BG-DG-DB refits + The New Gentleman 4.2.5 (framework, incl. Vigilant ini) | HIMBO **installed**; TNG **PARKED 2026-08-25** awaiting 1.7.99 dll (01b body renders without its genital counterpart until then; TNG MCM hotfix file 793745 queued for unpark) |
| Male skin | SkySight 2025 Ultra: HIMBO-Uncut, Clean+Hairy, vanilla head/age, default SSS | **installed** (6580) |
| Animation | Pandora | installed |
| Alternate start | Skyrim Unbound Reborn | installed; supports non-Dragonborn characters |
| Follower framework | NFF | forced by Proteus; **AFT (6656) is the one surviving loser - confirm skip** |
| Guards / Stormcloaks | Sons of Skyrim 2.0.2 + Xtudo Fixes 3.3 + More Patches 1.3.1 (Lux Orbis selection only) | **installed 2026-08-26**; historical-fantasy armor/weapon overhaul; standard predominantly 1K/2K textures; USSEP and Survival warm-keyword fixes forwarded; LOOT, master-order, and record-overlap audits clean |
| Killmoves | VioLens + Kaputt | 3 challengers in additive pool to check against the pair, low priority |
| Underlayers | Underwear.dll 1.3 as engine, pool TO BE overridden to 10 vanilla poor/common garments (Roughspun, Belted Tunic, Farm/Miner sets, Ragged Robes) + our Period Underlayers SPID config (bandits Roughspun, jarls/merchants Fine Clothes) | **installed** BUT audit 2026-08-26 found the pool override was NEVER WRITTEN - Underwear.ini still lists the mod's 4 default garments (user verdict on the resulting look: garbo). Implement the vanilla pool (form IDs via skyrim-record-cli, no guessed IDs) when TNG lands; Period Underlayers also inert until SPID unparks. User directive 2026-08-26: underwear system working AND full nudity possible -> HIMBO 01b + TNG rebuild (in flight) + removable garments |

## Tier 4 - the actual remaining work: 20 slot decisions

**A. Compare what's already in keeps** (9 slots, 33 mods):

| slot | candidates surviving in keeps | how it gets decided |
|---|---|---|
| Weather | **DECIDED 2026-08-23: Azurite III** + Azurite III CS 162153 (Dlizzio; incl. its own Darker Nights + IBL) + EVLaS + water fx fix - **installed** | swap same day: doodlum HDR 138991 + DrJacopo Darker Nights addon disabled (162153 page: incompatible) after user identified the mod he meant; rivals skipped per user order; Azurite Mists out (author: III needs no mist mods) |
| Landscape tex | **PROVISIONAL 2026-08-26: Vanaheimr Landscapes 5.5 PBR 2K**; previous six candidates retained pending repair/A-B | Best current art-direction fit and <=4K, but two shipped road meshes report Oldrim format; hold install until repaired/excluded and CS/PGPatcher path is ready. Evidence: `docs/LANDSCAPE-TREES-2026-08-26.md` |
| Interior lighting | **DECIDED 2026-08-23: Lux family** - Lux + Via + Orbis + Patch Hub + Lux CS + CC bundle (installing; dim beam/mist variants) | Lux re-entered via keeps and won on facts: every component active 2024-26, purpose-built CS bridge, hub officially patches Bruma/Wyrmstooth/Vigilant/Glenmoril/Unslaad (ELFX FOMOD: none). ELFX trio stays shelved as mid-save A/B fallback |
| Water | Cathedral Water, Simplicity of Sea, A Water Made For CS (3) | last two are CS-era; RWT purged |
| Horses | Convenient Horses, Simple Horse, Simplest Horses (3) | feature-set read; CH vs INIGO conflict already on file |
| Skeleton | XPMSSE + Skeleton Replacer HD (2) | layering question, not rivalry |
| Trees | **PROVISIONAL 2026-08-26: NotWL 3.14 + Nordic Cut 1.2.2 + Nature of the Mild Lands 3.14**; HLT retained as performance fallback | Nordic Cut restores mostly vanilla placement while retaining NotWL character. Base and PBR archives contain one 8K map; use the permitted downscale and hold PBR/animation. Not installed; new-game only. Evidence: `docs/LANDSCAPE-TREES-2026-08-26.md` |
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
