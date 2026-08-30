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

**Compatibility-label rule (user, 2026-08-27): never exclude a mod merely
because its title says “for ENB” or uses other legacy ecosystem wording.** The
title is not a dependency declaration. Read the current requirements,
description, file variants, and shipped payload before deciding. ENB-named
textures, meshes, particle-light assets, water mods, weather plugins, and even
presets may work with Community Shaders. Effects 11 - Community Shaders
(179824) can run almost all ENB presets without ENBSeries; ENBSeries itself is
still mutually exclusive with Community Shaders.

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

**1.7.99 ecosystem hold (rewritten 2026-08-26, re-audited 2026-08-30 in
issue #79, receipts in docs/HANDOFF-2026-08-27.md):** mods parked awaiting
1.7.99/1.7.104 builds (modlist.txt `-` rows; ledger notes carry per-mod
reasons). The gate is `skse64/PluginManager.cpp:657-668`: a plugin claiming
`kVersionIndependent_AddressLibraryPostAE` without
`kVersionIndependentEx_AddressLibraryV5` is refused ONLY if its PE
TimeDateStamp falls in `[520128000, 1748217600)` (2025-05-26 cutoff). Read the
exported `SKSEPlugin_Version` bytes before parking anything - three parks were
inferred rather than observed.

STILL PARKED, gate genuinely FAILS (stamp inside the window, no V5 flag):
EVLaS (2022-09-18), Skill Uncapper 2.2.3 (2023-09-26), Scrambled Bugs 21
(2023-03-10), Bug Fixes SSE 10 (2023-03-10). Parking is not an acceptable
holding state - all four are rebuild candidates tracked in #87. Correction:
Bug Fixes SSE IS open source (`KernalsEgg/SKSE64Plugins/BugFixesSSE`); the
earlier "closed source, no rebuild path" note was wrong. Only EVLaS has no
public source. Neither KernalsEgg's repo nor the Rust Uncapper carries a
LICENSE - settle terms before shipping a rebuilt binary publicly.

UNPARKED 2026-08-30, all three were parked on inference and pass the gate:
MCM Helper 1.6.3 (#83, viEx=3 - sets the V5 flag outright), OAR 3.2.0 (#84 -
framework is live but no OAR/DAR config folder exists yet, so it drives
nothing), CRD (#85 - no `Data/CraftingRecipeDistributor` configs installed, so
it distributes nothing). Enabling preserves mod priority; a `--replace`
reinstall does NOT - it re-stages at top priority, which silently hoisted MCM
Helper to priority 166 until it was restored to 22.

SUPERSEDED ROWS, correctly left off: the Nexus `Community Shaders` row is
replaced by the enabled `Community Shaders AIO - 1.7.99 Source Build`
(v1.8.0.0, live per CommunityShaders.log), and the `SSE Display Tweaks` row by
the enabled `SSE Display Tweaks Official` (v1305). Base `Proteus` and
`JContainers SE` DLLs fail the gate but are outvoted by the enabled Ensrick
1.7.104 native overlays, which pass. SPID 7.0.0 and TNG pass and are active.

UNPARKED 2026-08-30: Light Placer 4.2.1 (#79) - `versionIndependence=5`,
`versionIndependenceEx=0`, PE stamp 1778212284 (2026-05-08), above the cutoff
so the V5 branch never fires. It drives the Lux CS ISL layer: `Lux CS.ini`
`[LightBlackList]` disables the vanilla/USSEP light refs and the 9 JSONs in
`Lux CS/LightPlacer/` attach the replacements. Base Lux/Orbis/Via never needed
it. Runtime confirmation still owed via launch_triage.

UNPARKED 2026-08-26: SSE Engine Fixes 7.0.21 (official), PapyrusUtil 4.7
(official 1.7.99 build - Skyrim Unbound/NFF/CBBE-morph scripts unblocked).
JContainers 4.3.1 (author GitHub prerelease) installed but RE-PARKED: the
skse64 master plugin gate refuses it pending an AddressLibraryV5 compat
declaration - rebuild from source or await re-release. RaceMenu runs via
self-built skee64 (overlays OFF - engine NIF regression, no Bethesda hotfix);
official RaceMenu 1.7.99 is done per author, gated on the SKSE release.

---

**Anniversary Edition: all 74 Creation Club items are installed and active**
(verified 2026-08-29 against the game Data folder and `Skyrim.ccc`). A CC
requirement is therefore never a blocker and never needs raising with the user.
Note CC plugins load via `Skyrim.ccc`, not `plugins.txt`, so MO2's plugin list
shows zero `cc*` rows by design - confirm CC presence from the game folder, and
resolve which CC item owns an asset by indexing the BSAs rather than guessing
from the in-game name.

## Tier 0 - engine floor (install before first real session)

| mod | id | status |
|---|---|---|
| SKSE64 2.3.0+ | 30379 | **SELF-BUILT master DEPLOYED 2026-08-26** (Ensrick/skse64 branch ensrick/headless-log-only = ianpatt@14db212 + log-only error reporting; CMake build, exports gate passed; fixes the official 2.3.0 GetNthTintMaskColor stale-offset Papyrus crash; Nexus 2.3.0 preserved as .bak.v2.3.0-nexus; official 2.3.1 release supersedes) |
| Address Library v12 | 32444 | **installed** |
| SSE Engine Fixes | 17230 | **installed** 7.0.21 beta (official 1.7.99 build; preloader retired) |
| Crash logger | 59818 | **installed** CrashLoggerSSE 1.25.0 + PDB pack 794129 (pack signature-mismatches the 1.7.99 exe - exe frames fall back to address-library IDs; self-built skse64 PDB deployed beside the dll) |
| USSEP | 266 | **installed** 4.3.9 (2026-08-21) |
| Bug Fixes SSE | 33261 | **PARKED, gate FAILS (#87)** - vi=5, viEx=0, PE stamp 2023-03-10, inside SKSE's reject window. Open source after all (`KernalsEgg/SKSE64Plugins/BugFixesSSE`) - rebuild candidate; repo has no LICENSE file |
| Scrambled Bugs | 43532 | **PARKED, gate FAILS (#87)** - vi=5, viEx=0, PE stamp 2023-03-10, inside the reject window; open source (`KernalsEgg/SKSE64Plugins/ScrambledBugs`), rebuild candidate, no LICENSE file |
| SSE Display Tweaks | 34705 | row PARKED but **superseded 2026-08-30 (#79)**: the enabled `SSE Display Tweaks Official` (v1305, PE stamp 2026-08-29) passes the gate and is active. Leaving the old row off is correct, not a park |
| Skill Uncapper for AE | 82558 | **PARKED, gate FAILS (#87)** - vi=1, viEx=1, PE stamp 2023-09-26, inside the reject window; its Rust versiondb ALSO asserts on address-library format 5, so the gate is the smaller half. Source `TheDreadedAndy/SkyrimAEUncapper-Rust`, no LICENSE file |

## Tier 1 - frameworks (everything else assumes these)

Installed and active: SkyUI, RaceMenu (`bExternalHeads=1`, overlays OFF),
UIExtensions, PapyrusUtil 4.7 (official 1.7.99), po3 Papyrus Extender, po3
Tweaks, ConsoleUtilSSE NG. JContainers 4.3.1 installed but PARKED (SKSE
master gate wants an AddressLibraryV5 declaration; rebuild or re-release).

| mod | id | status |
|---|---|---|
| MCM Helper | 53000 | **installed** official 1.6.3 (Skyrim SE 1.7.99+, verified against live 1.7.104 + SKSE 2.3.1 + Address Library v12 + SkyUI 6.11); official ESL/BSA FOMOD selection, clean static audits, foreground MCM/settings-write smoke still required; record: `records/mcm-helper-1.6.3-2026-08-30.md` |
| SPID | 36869 | **installed** 7.0.0 and ACTIVE (verified 2026-08-30 #79: vi=5, viEx=2, compatibleVersions 1.7.104) |
| KID | 55728 | **installed** 4.1.0 (official 1.7.99) |
| Base Object Swapper | 60805 | **installed** 3.5.0 (official 1.7.99) |
| Open Animation Replacer | 92109 | **installed** 3.2.0, **UNPARKED 2026-08-30** (#84) - PE stamp 2026-07-26, above the reject window. No OAR/DAR config folder exists yet, so it drives nothing until an OAR-dependent mod arrives |
| Pandora Behaviour Engine | 133232 | **installed** v4.4.0-beta; ONE interactive run via MO2 pending (headless --auto_run attempt timed out; only XPMSSE weapon styles depend on it) |
| XPMSSE | 1988 | **installed** (Extended + latest rig + RaceMenu MCM weapon styles); Skeleton Replacer HD 52845 layers on top later |
| FSMP | 57339 | **installed** 4.1.1 AVX on Skyrim 1.7.104 + SKSE 2.3.1; cloth/hair physics only, no body jiggle; 3 ms auto-adjust budget and helmet-hair suppression active |
| Vanilla Hair Remake SMP | 63979 | **installed** 1.0.3 player replacer + 1.0.1 NPC FaceGen package; VHR main wins 93 shared XMLs, owned loose compatibility layer preserves 29 USSEP faces and repairs 3 stale XML references; foreground hair/helmet/Proteus smoke remains #27 |
| BodySlide and Outfit Studio | 201 | **installed** (tool; Curvy batch build pending) |
| Crafting Recipe Distributor | 52276 | **installed**, **UNPARKED 2026-08-30** (#85) - PE stamp 2026-01-20, above the reject window. No `Data/CraftingRecipeDistributor` configs installed, so it distributes nothing yet |

## Tier 2 - identity systems (the premise)

Proteus (base 3.4.0 DLL fails the gate - vi=1, viEx=1, PE stamp 2022-10-14 -
but the enabled `Proteus 1.7.104 Native Overlay - Ensrick` PASSES and logged
`loaded correctly` on 2026-08-28, as did the JContainers overlay it needs;
verified 2026-08-30 #79. Interactive character-switch acceptance test from
docs/RUNTIME-ISSUES-2026-08-28.md is still the open item, not the load) + Nether's Follower Framework (installed+active; its
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
| Renderer | Community Shaders 1.8.3 + Skylighting/SSGI/Wetness/TerrainVariation/TerrainBlending/Upscaling + Particle Patch + ENB Light | CS CORE is LIVE via the enabled `Community Shaders AIO - 1.7.99 Source Build` (v1.8.0.0, viEx=3, confirmed running in CommunityShaders.log 2026-08-29); the parked Nexus row is a superseded duplicate, not a missing renderer; Hair Specular undecided-not-installed |
| Worldspaces | Bruma, Wyrmstooth, Beyond Reach, Moonpath, Gray Cowl 10th (141327), Vigilant (11849+11894 EN) | Falskaar and its 4 support mods skipped, evidence on file |
| Female body | CBBE Curvy, nude, vanilla outfit replacers, face pack, RaceMenu morphs | **installed** v2.0.3 |
| Female skin | Reverie: Athletic body normal, Sleek face, CBBE compat | **installed** v1.11.2 |
| Male body | HIMBO core 01b nude + BG-DG-DB refits + The New Gentleman 4.2.5 (framework, incl. Vigilant ini) | HIMBO **installed**; TNG **installed** and ACTIVE (verified 2026-08-30 #79: vi=5, viEx=2, PE stamp 2026-08-26 - passes the gate) |
| Male skin | SkySight 2025 Ultra: HIMBO-Uncut, Clean+Hairy, vanilla head/age, default SSS | **installed** (6580) |
| Animation | Pandora | installed |
| Alternate start | Skyrim Unbound Reborn | installed; supports non-Dragonborn characters |
| Follower framework | NFF | active; deterministic FOMOD now includes its native Interesting NPCs support scripts. Varinia remains outside NFF and uses her own framework. |
| NPC/quest expansion | Interesting NPCs 4.5 + 4.54 | **installed 2026-08-30** with ILS, Skyrim Unbound prison, Cat-and-Mouse, Survival, NFF, Lux, and Skyking patches; new-game/permanent-save scale. Party Banter remains undecided. |
| Received-hit camera effects | Disable Screen Blood + No More Blur on Hit + 3rd Person Camera Stagger Remover | **installed 2026-08-30** as three immutable vendor mods; record-only/animation-only and save-neutral, pending foreground feel test. |
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
| Water | **DECIDED 2026-08-27: Water for ENB 2.21, Natural Shades of Skyrim for CS, 2K, transparent 2K waterfall/effects add-on with parallax; USSEP + Beyond Reach + Bruma + Wyrmstooth patches** | The ENB-named parent explicitly supports CS and is current as of 2026-08-15; Slightly Brighter Water FX Fix parked because its waterfall meshes overlap the selected add-on |
| Horses | Convenient Horses, Simple Horse, Simplest Horses (3) | feature-set read; CH vs INIGO conflict already on file |
| Skeleton | XPMSSE + Skeleton Replacer HD (2) | layering question, not rivalry |
| Trees | **PROVISIONAL: NotWL 3.14 family; exact placement profile still requires the user's call** | The current NotWL main file already uses its standard 2K bark and 1K leaf profile. Mild Lands is held outside both Keep and Skip until performance is measured; it halves all 413 texture dimensions (mostly 1K/512, 44 at 2K, one at 4K). Nordic Cut restores vanilla placement for most normal trees while retaining NotWL debris/shrubs and stronger spruce silhouettes; it reduces placement conflicts but is not a guaranteed FPS improvement. Full NotWL versus Nordic Cut remains undecided and uninstalled; either path requires a new game and dedicated DynDOLOD. Evidence: `records/tree-overhaul-and-morthal-cypress-audit-2026-08-29.md`. |
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
Campfire kept), magic (Odin survives, Mysticism purged), **sound - SLOT CLOSED
2026-08-30**, college (JK's survives).

The old "AOS purged" note here was stale: Audio Overhaul moved to 4.1.3 in
2023 and is actively maintained. The both-with-patch note was the right one and
the stack is now **installed**: Sound Record Distributor 1.5.4 (77815) + ISC 3.0
(523) + AOS 4.1.3 (12466) + the AOS-ISC Integration patch 1.1.0 (36761). No AOS
weather patch, per the AOS page's own instruction to drop them on the SRD path -
Azurite Weathers III needs none. Acoustic Space Improvement Fixes (78992) is a
separate undecided slot and needs a Lux patch. Evidence:
`records/sound-stack-2026-08-30.md`; the ISC-versus-USSEP record question is
issue #89. SRD passes the PluginManager gate outright - it declares
`kVersionIndependentEx_AddressLibraryV5` and ships an empty
`compatibleVersions` array, so there is no whitelist to refuse it on.

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
