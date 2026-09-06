# Requested mods: current relevance and alternatives - 2026-09-06

Research requested by the owner: High Poly Project, Book Covers Skyrim, Ars Metallica, Animation Queue Fix, and Convenient Horses. **No installation, enable/disable, Keep/Skip change, mod-payload download, or game launch is authorized by this review.** The recommendations below are proposals for owner approval, not adoption decisions.

## What is actually commonplace?

We re-fetched 20 public Load Order Library exports from the existing survey's list families. Fifteen have available MO2 modlists dated 2025–26; nine of those were updated in 2026. Presence and valid text are checked, not export completeness. Two only supply plugin order and three are pre-2025 snapshots; they are excluded, not recorded as missing mods. [Full matrix, exact matching rows, dates, hashes, and reproduction command](REQUESTED-SLOTS-CENSUS-2026-09-06.md).

This is a convenience sample of curated lists, **not a popularity ranking, market share, proof of performance, or universal quality score**. Several lists share ancestry. Folder names cannot prove installed versions, hidden assets, FOMOD choices, winning meshes, or binary compatibility. The older August survey's n/19 and n/27 counts are a different dataset and must not be combined with these.

| Requested mod | Enabled main folders, 2025–26 / 15 | 2026-only / 9 | Conclusion |
|---|---:|---:|---|
| High Poly Project | 10 | 5 | Still common. A selective mesh layer, not universally replaced by MIC. |
| Book Covers Skyrim family | 7 standalone; **13 including LOTD** | 5 standalone; **8 including LOTD** | Still widely represented; LOTD bundles BCS. Delivery/patching route matters more than the age of its art. |
| Ars Metallica | 0 | 0 | Not the sampled-list default. Still a valid, fairly compact crafting design, not demonstrated broken or obsolete. |
| Animation Queue Fix | 15 | 9 | Strongest consensus in this group; current OAR also expects it for normal preloading. Verify the newly updated binary for our runtime. |
| Convenient Horses | 0 | 0 | Not the sampled default. Simplest Horses is the clear minimalist choice here, not a feature-complete successor to CH. |

Alternatives: MIC **3/15** (2/9); Crafting Recipe Distributor **4/15** (2/9); CCOR **1/15** (0/9); Simplest Horses **7/15** (5/9). The absence of CH, Immersive Horses, Press H, and A Horse's Life in these exact enabled-main matches is **not** an ecosystem-wide rejection. Visual-only lists are particularly weak negative evidence for gameplay mods.

Notable named evidence:

- HPP: LoreRim, Nolvus Awakening's dated export, Wunduniik, Apostasy, Anvil, Eldergleam, Mages & Vikings, Invicta, Vagabond Remastered, Tempus. LoreRim/Wunduniik include lower-poly coal overrides; several use a separate garlic replacement. Merely installing HPP does not mean keeping every mesh.
- MIC: Nordic Souls, CSVO, Vagabond Remastered. Vagabond's export includes **both MIC and HPP**, so these are not necessarily mutually exclusive packages. Invicta's MIC patch mentions are not counted as the main MIC package.
- Books: LoreRim, Nordic Souls, Wunduniik, Apostasy, Anvil, Mages & Vikings, Vagabond. “Book Covers Skyrim Updated” is a family match, not proof of a specific downloadable REDUX build. Vigilant/Unslaad-only cover mods are excluded from the BCS count.
- Bundled books: Nolvus, Septimus, Tuxborn, Kirbyking's, Invicta and Tempus additionally have enabled LOTD main folders. [LOTD officially incorporates BCS and Lost Library](https://www.nexusmods.com/skyrimspecialedition/articles/1494). The union is **13/15 recognized BCS-provider routes (8/9 in 2026)**, not just seven; this still does not establish each final texture winner. No double-counting, and patch-only LOTD mentions in LoreRim are excluded.
- Horses: LoreRim, Nordic Souls, Nolvus, Wunduniik, Tuxborn, Kirbyking's, Invicta use Simplest Horses. LoreRim's **disabled** Press H option is not counted as adoption.

## High Poly Project: use selectively, not reflexively reject it

[HPP](https://www.nexusmods.com/skyrimspecialedition/mods/12029) remains v5.3 (2021-10-22). The relevant continuing support is [Xtudo's fixes](https://www.nexusmods.com/skyrimspecialedition/mods/63425), v2.7 (2026-01-20), addressing textures, collision, UV/shading and chopping/firewood issues, with Campfire and MLO2 compatibility options. Both systems matter in our build. [Skurkbro's fixes](https://www.nexusmods.com/skyrimspecialedition/mods/64137) address additional hay/firewood issues and are described as complementary, not an automatic replacement for Xtudo's set.

The geometry objection is specific, not a claim that all HPP assets perform badly. [Garlic — A Garlic Mod](https://www.nexusmods.com/skyrimspecialedition/mods/78848) publishes a comparison of 92,694 triangles/five draw calls for an HPP garlic braid against 5,016/two in its replacement. [Less Poly Coal](https://www.nexusmods.com/skyrimspecialedition/mods/164303) is another targeted option. A 1K texture cap does not reduce geometry costs. Do not turn an author's mesh comparison into an unmeasured FPS promise on this machine.

[MIC](https://www.nexusmods.com/skyrimspecialedition/mods/131131), v0.6.4 (2026-01-18), is a maintained collection of selected mesh improvements/fixes, not a guaranteed complete HPP replacement or uniformly lower-poly pack. [Nordic Souls 3.0](https://github.com/Geborgen/nordic-souls/blob/main/CHANGELOG.md#version-300) removed HPP/fixes and added MIC. [Lexy's July 2026 changelog](https://lexyslotd.com/changelogs/10th-july-2026/) removed HPP/fixes as no longer needed. Conversely, [Nolvus Ascension's installation instructions](https://www.nolvus.net/guide/asc/visuals/models) deliberately hide HPP's ingredients directory and several mushroom meshes while retaining other content. Ascension is historical corroboration, not proof of current Awakening installation choices.

**Recommendation:** retain HPP and MIC as candidate asset sources. HPP has the stronger prevalence evidence; MIC is an alternative/overlapping curated layer. Before approval for this build, compare their actual remaining coverage against SMIM, SMIM Quality Addon, Assorted Mesh Fixes and Unofficial Material Fix, then propose exact winners and any required Xtudo/Campfire/MLO2 pieces. Keep existing approved specialist meshes as explicit protected winners. No blanket overwrite order or automatic extra mod adoption has been chosen.

MIC's own requirements/options include SMIM, BOS, AE content and lighting compatibility; it is not a dependency-free swap. A newer name also does not imply the same job: [Project Polygon](https://www.nexusmods.com/skyrimspecialedition/mods/174178?tab=description), v3.1 (2026-03-31), targets Nordic-ruin exteriors, snowdrifts, volcanic terrain and related meshes rather than wholesale clutter. It is not a demonstrated HPP successor, and reported vertex-color issues still merit checking before any adoption.

## Book Covers Skyrim: the art is not obsolete

[BCS](https://www.nexusmods.com/skyrimspecialedition/mods/901), v4.2 (2017-12-03), supplies individually recognizable cover art; vanilla upscales are not equivalent coverage. Current support includes [Vanilla-like Tweaks and Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/59669), v1.8 (2026-04-27), [SkyPatched](https://www.nexusmods.com/skyrimspecialedition/mods/109254), and [SkyPatched Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814), v1.0.3 (2026-05-22).

Two defensible routes, not a collection of patches to install together indiscriminately:

1. Original plugin plus specifically applicable USSEP/CRF/other compatibility patches. It intentionally edits more than model paths, including titles; decide whether those changes are wanted.
2. BCS assets plus the matching SkyPatched resource plugin/configuration and Missing Books. This is a promising fit with our installed SkyPatcher, but **the treasure-map repair needs its matching ESP-FE variant as well as INIs**. Verify BSA loading and the matching ESLfy/non-ESLfy resource IDs; do not blindly discard every plugin.

The old [local BCS audit](../records/book-covers-audit-2026-09-03.md) has been corrected: LOOT `clean:` CRC entries are recognized-clean files, not instructions to QuickAutoClean; its published coverage arithmetic did not establish a valid denominator; BSHeartland is Bruma; and frequency/noise metrics did not establish that printed book art was objectively bad. No automatic cleaning or texture-quality rejection follows from those old claims.

LOTD users must not add this route by rote: [Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814) explicitly identifies LOTD incompatibility/redundancy because those model edits are already included. LOTD is not present as an enabled named mod in our Default profile; it remains a critical survey interpretation distinction.

[Better Books and Letters](https://www.nexusmods.com/skyrimspecialedition/mods/68909) is a vanilla-style upscale alternative or potential shared-paper layer, not a replacement for hundreds of unique covers. [BCS PBR](https://www.nexusmods.com/skyrimspecialedition/mods/155254?tab=files) has separate Original and Lost Library files: the page's dependency list alone does not prove Original requires adding Lost Library. It needs an actual PBR pipeline/payload review, not adoption merely because we run Community Shaders. [Updated REDUX](https://www.nexusmods.com/skyrimspecialedition/mods/69568) is currently hidden, so a list's historical folder name does not make it an obtainable default recommendation. Lost Library is additional reading content and remains a separate owner decision.

**Recommendation:** BCS remains a good visual candidate. Prefer evaluating the corrected SkyPatched route for this setup, while retaining the original-plus-patches route as valid. Appearance, original/desaturated covers, title changes, page paper and Lost Library remain owner choices. No other book mod or upscale is automatically approved.

## Ars Metallica: still competent, but decide what crafting should do

| Option | Current version/date verified | Scope and cost |
|---|---|---|
| [Ars Metallica](https://www.nexusmods.com/skyrimspecialedition/mods/321) | 2.0.8, 2024-07-22 | Salvage, arrows/lockpicks/faction recipes and Smithing XP for related work. Material perks gate raw-ore smelting. Mining scripts, workstations and some creature loot extend its conflict surface beyond recipes. |
| [CCOR](https://www.nexusmods.com/skyrimspecialedition/mods/28608) | 2.6.4, 2026-06-24 | Broad configurable crafting, mining, salvage, jewelry and artifact upgrading; WACCF requirement and substantial compatibility work. Not simply a newer lightweight Ars. |
| [Crafting Recipe Distributor](https://www.nexusmods.com/skyrimspecialedition/mods/52276) | 4.1.0, 2026-01-20 | Generates salvage/missing tempering recipes, including mod equipment. Framework, not an XP/perk/progression overhaul. Rules and exceptions need balancing. |
| [Simple Smithing Overhaul Simplified](https://www.nexusmods.com/skyrimspecialedition/mods/55333) | 1.3.3 | Narrower recipes/salvage/artifact progression without WACCF; Adamant patch support discontinued. Not established as the new consensus. |
| [Heim](https://www.nexusmods.com/skyrimspecialedition/mods/54207) | 1.4, 2022-06-07 | Manuals/schematics as progression; additional equipment needs integration. A different design, not automatic modernization. |

These designs are not interchangeable. Our slow-progression/limited-inventory economy can be undermined by generous salvage yields or added mining/tanning/smelting XP. [Experience from mining tanning and smelting](https://www.nexusmods.com/skyrimspecialedition/mods/132881) is a modular candidate if that XP is wanted, not a required addition. [Crafting Skill Overhaul Updated](https://www.nexusmods.com/skyrimspecialedition/mods/180707), despite its May 2026 release, explicitly targets 1.6.1170 and describes limited playtesting; it is not a ready 1.7.104 recommendation.

**Recommendation:** select required functions first: salvage/tempering coverage, XP, perk/material gates, manual-based learning and artifact upgrading. CRD/our recipes are a promising integration foundation; choose progression separately. Ars is a valid compact alternative, and CCOR the larger configurable one. Zero Ars matches in this sample does not mean it is defective. CRD is physically installed here but **disabled in Default/modlist.txt**; the ledger's enabled claim is stale. This research does not repair or enable it. Ars script redistribution permissions also need review before promising a distributable modified build.

## Animation Queue Fix: highest-priority candidate

[AQF 1.0.2](https://www.nexusmods.com/skyrimspecialedition/mods/82395), released **2026-08-31**, explicitly adds **1.7.99+** support. Our previous 1.0.1 loader rejection is historical evidence, not a present-tense reason to reject 1.0.2 or assume a private rebuild is needed. [Source commit 26b5f0f](https://github.com/ersh1/AnimationQueueFix/commit/26b5f0fbe66b21696fa5f2ed2fc261d1ebb74a46) updates CommonLib and uses the new Address Library/no-struct declarations. Current source licensing is GPL-3.0-or-later with stated exceptions, not MIT.

[OAR](https://www.nexusmods.com/skyrimspecialedition/mods/92109) still lists AQF for normal preloading; its experimental skip-preloading alternative is discouraged. AQF advances queued loading work promptly; [Engine Fixes' AnimationLoadSignedCrash](https://github.com/aers/EngineFixesSkyrim64/blob/master/src/fixes/animation_load_signed_crash.h) fixes a different signed/unsigned problem. Neither OAR nor that similarly named fix supersedes AQF. [Lexy's guide](https://lexyslotd.com/guide/mod-installation-part-1/) lists AQF separately; [Nolvus Awakening](https://www.nolvus.net/awakening) still lists the older 1.0.1, which demonstrates usage but not current-runtime readiness.

**Local evidence:** AQF remains absent; the old archive is not an installation. The latest inspected SKSE log loads OAR 3.2.1, with effective `bDisablePreloading=false`. **Author/source compatibility is corroborated, but the shipped 1.0.2 DLL and an actual launch have NOT been verified in this review.**

**Recommendation:** verify official 1.0.2 first, then seek approval/admission through the normal installation checks. This is the strongest practical candidate among the five. Issue #129 and the SkyParkour ledger note need their historical/current distinction updated when the installation task is taken up; their old failed-binary evidence must remain intact.

## Convenient Horses and what people use instead

| Option | Current version/date verified | Best fit and caveat |
|---|---|---|
| [Convenient Horses](https://www.nexusmods.com/skyrimspecialedition/mods/9519) | 7.1, 2022-01-07 | Training, equipment/storage, stabling, follower horses, mounted harvesting/interaction and charge attacks. Full role-play system with an introductory quest; no SKSE dependency of its own. |
| [Simplest Horses](https://www.nexusmods.com/skyrimspecialedition/mods/54225) | 0.9.5, 2022-12-14 | Strongest sampled default: follow/wait, inventory, recall and naming with a small interaction surface. Not horse survival or a complete limited-storage economy. Requires SKSE/SPID/MCM Helper. |
| [Press H to Horse](https://www.nexusmods.com/skyrimspecialedition/mods/81195) | 2.3.9, 2026-05-17 | AE horse/equipment/hostler system, selectable owned horses and limited pack capacity; armored mode sacrifices ordinary storage. Requires a fresh game and relevant CC/dependencies. |
| [A Horse's Life](https://www.nexusmods.com/skyrimspecialedition/mods/146675) | 1.3, 2025-05-19 | Feeding/grooming/hoof care, traits, ownership, taming, barding and equipment-dependent capacity. Most relevant richer survival candidate, with more compatibility/settings work. |
| [Immersive Horses](https://www.nexusmods.com/skyrimspecialedition/mods/13402) | 3.0, 2018-06-01 | Herd ownership/adoption/theft/breed stats and commands. SKSE/SkyUI/PapyrusUtil; another framework supplies follower riding packages. Old does not mean invalid. |

There is explicit migration evidence, not just an inference from endorsements. [Nordic Souls 3.2.0](https://github.com/Geborgen/nordic-souls/blob/c6e2dc06231e78fdb5c2ce916de8882d3808b45d/CHANGELOG.md#version-320) replaced A Horse's Life with Simplest Horses plus Followers Ride Horses to simplify its system. That is a design choice, not a finding that AHL is broken. [STEP's administrator discussion](https://stepmodifications.org/forum/topic/16624-simplest-horses-and-other-mounts-by-hackfield/) records accepting Simplest Horses to replace CH for 2.0; this is historical guide-decision evidence, not another export count. [Tuxborn's horse guide](https://tuxborn.org/wiki/general-content-topics/horses-and-other-mounts/) and [Nolvus Ascension](https://www.nolvus.net/guide/asc/gameplay/misc) also document Simplest Horses.

Important fit checks:

- [Press H source](https://github.com/TateTaylorOH/Press-H-to-Horse/tree/fd21564595d73964ffb497f39da77eb8aa51e5dd) sets saddle capacity and rejects ordinary stored items in armored mode. Wild Horses (`ccbgssse034-mntuni.esl`) is an ESP master; MCM Helper/UIExtensions and vanilla/CC script interactions still need review. No DLL in the source tree does not prove all dependencies work on 1.7.104. Treat bonuses also affect XP and need a decision.
- [AHL's feature guide](https://www.nexusmods.com/skyrimspecialedition/articles/10074) offers optional care/needs and traits; immortality, recall, debuffs and equipment capacity should be deliberate choices. Its horse-coat management can require integration with retextures. Its published Bruma/CRF/CC support is useful, but not proof of our entire combination.
- [CH's optional files](https://www.nexusmods.com/skyrimspecialedition/mods/9519?tab=files): the **Special Edition Patch** is for downgraded pre-AE game assets, not our current 1.7 setup. The **Anniversary Edition Patch** is a distinct paid-Creations integration option with its own requirements.
- [NFF](https://www.nexusmods.com/skyrimspecialedition/mods/55653) is already active and supplies follower mount/riding controls. Do not add [Followers Ride Horses](https://www.nexusmods.com/skyrimspecialedition/mods/139368) merely because Nordic Souls uses it. Assign exactly one controller per follower; use the documented riding-only/exemption settings where appropriate.

**Recommendation:** Simplest Horses if the goal is unobtrusive control; Press H if limited pack capacity/equipment tradeoffs are central; A Horse's Life if maintaining a horse should be a real survival activity. CH remains worth choosing specifically for training/mounted interaction. None is a drop-in, proven Proteus solution. Before any adoption, test purchase/payment with weighted regional coins, capacity enforcement, storage through death/dismissal/save/reload/new-land travel, and especially ownership/herd/inventory isolation when switching Proteus player characters. Remote recall or unlimited inventory must not silently bypass the owner's intended travel economy.

## Decisions left with the owner

1. Approve AQF admission after release-binary inspection, or keep it research-only for now.
2. HPP selective coverage versus MIC-led mesh layer; no additional mesh replacements approved yet.
3. BCS visual/delivery route; separately choose cover style, names, shared paper and Lost Library.
4. Crafting functions and progression rules before selecting Ars/CCOR/modular recipes.
5. Minimal horse controls versus limited pack roles versus horse-care survival; define recall, immortality and Proteus ownership behavior.

All five remain proposals. This review changes documentation and research tooling only and does not alter the existing build or curator state. Research scripts retain a small selected public-evidence JSON locally, not a full modlist/archive cache. Seven offline parser/census tests cover enabled/disabled separation, patch exclusion, numbered names, missing authors, bundled-provider recognition and denominator exclusions; binary/in-game compatibility remains outside this research verification.
