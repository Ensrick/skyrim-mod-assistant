# Approved installation batch — 2026-09-06

This is the handoff record for the owner's approved Book Covers Skyrim,
Animation Queue Fix, High Poly Project and subsequent Apocalypse request.
It separates installation status, static evidence, and unverified gameplay.
The installed-mod ledger and final root transaction receipts remain authoritative
after this snapshot; a prepared candidate is not an installed mod.

| Component | Status at this handoff | Remaining gate |
|---|---|---|
| Animation Queue Fix | Official 1.0.2 installed and enabled; Keep verified | Authorized runtime acceptance, tracked in [#129](https://github.com/Ensrick/skyrim-mod-assistant/issues/129) |
| Book Covers Skyrim + SkyPatched + Missing Books | Corrected exact-file installs completed; payload winners and dependent patch freshness passed static verification | Runtime acceptance; retained publication/compatibility caveats below |
| Apocalypse | Official 10.3.0 installed; vendor payload winners and dependent patch freshness passed static verification | Runtime acceptance; summoned-equipment and Locate Gold follow-up in #248 |
| High Poly Project and relevant fixes | **Not installed; pending owner subset-versus-hold decision** | [#246: decision and asset defects](https://github.com/Ensrick/skyrim-mod-assistant/issues/246) |
| Lucien follow-on | Main 1.7.2 installed by root; optional dialogue patches unselected | [#249: optional integrations, Lux, equipment and NFF safety](https://github.com/Ensrick/skyrim-mod-assistant/issues/249) |

No game was launched by these preparation tasks. **All gameplay, visual and
performance acceptance remains UNVERIFIED.** No Lost Library, book PBR or paper
upscaler, MIC, alternate garlic/coal mod, horse mod or crafting overhaul was
approved as part of this batch. Research frequency is not installation authority.
After the Lucien follow-on, root reported Keep coverage of **201 installed
Nexus IDs / 201 kept**, with no installed-ID gaps or skips. This is not a count
of MO2 folders or a runtime pass. The six newly installed Nexus identities
also have independently verified author-attributed live Keep journal rows.
Lucien's optional dialogue additions remain a separate owner decision.

Final bounded static gates reported by root:

- All **15 vendor runtime payload files** win with reviewed hashes, including
  the two Lucien files added after the original 13-file batch check.
- The owned weapon patch passed source and installed freshness verification:
  354 audited inputs, 4,212 output rows, and 13 new speed overrides.
- The owned cloak patch passed source/installed verification after transaction
  `20260906T210050324Z-568092e477fe`, with an empty failure list.
- Exactly 275 active profile plugins were synchronized to game-side activation
  without launching the game; the prior activation file was retained. Local
  receipt: `records-work/approved-activation-sync.json`.

These scoped checks do not resolve open gameplay issues or imply a global
preflight pass. The final aggregate static receipt remains root-owned.

## Book Covers Skyrim: exact route

[Book Covers Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/901)
provides Original assets. [SkyPatched](https://www.nexusmods.com/skyrimspecialedition/mods/109254)
requires those assets and the already installed
[SkyPatcher](https://www.nexusmods.com/skyrimspecialedition/mods/106659).
[Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814)
requires all three and supplies the matching treasure-map plugin. No Legacy
of the Dragonborn is active; that mod already provides BCS and would change
the appropriate integration route.

| Nexus SSE mod/file | Version | Deterministic selection |
|---|---|---|
| 901 / 40352 | 4.2 Original | `Book Covers Skyrim.bsa` and `Book Covers Skyrim - Textures.bsa`; omit original ESP |
| 109254 / 461289 | 4.2 main | Four `SKSE/Plugins/SkyPatcher/book/Book Covers Skyrim` INIs; omit non-ESL ESP |
| 109254 / 467900 | 1.0 ESLfy overlay | `Book Covers Skyrim.esp`, ESP-FE resource plugin |
| 149814 / 755004 | 1.0.3 | FOMOD required files plus `1-Treasure - OG ESPFE/BCS-SP_TreasureMaps.esp` |

Use four vendor MO2 rows with original archive provenance for three Nexus IDs.
The ESLfy archive contains **only the ESP**, so omitting main file461289 would
omit the four essential INIs. Missing Books' page header says1.0.2, but the
actual latest selected file/changelog is1.0.3, uploaded2026-05-22.

Durable controller mapping plans:

- [Original BSAs only](../records/fomod-plans/901-book-covers-original-assets.json)
- [SkyPatched main INIs only](../records/fomod-plans/109254-book-covers-skypatched-config.json)
- [SkyPatched ESLfy resource plugin](../records/fomod-plans/109254-book-covers-skypatched-eslfy.json)
- [Missing Books required files and OG ESPFE treasure maps](../records/fomod-plans/149814-book-covers-missing-books-og-espfe.json)

Corrected installation transactions:

| Component | Root transaction |
|---|---|
| Original assets | `20260906T204308682Z-a164235012fc` |
| Main INIs | `20260906T204331042Z-0da11d41ed8a` |
| ESLfy resource | `20260906T204331780Z-d7c016ab8d2c` |
| Missing Books / matching treasure patch | `20260906T204111718Z-a6a9068fa4e3` |

**Critical resource-ID correction:** ESLfy compacts **all 1,330 owned FormIDs**.
Their bodies and EditorIDs match original BCS, not their numeric IDs. Use the
FOMOD choices `Plugin Type = ESPFE` and `Treasure Maps = BCS - Original`.
Do not use the OG ESP or renamed REDUX variants, original BCS ESP, or patches
made against original BCS. Keep the filename `Book Covers Skyrim.esp` unchanged
and active so both same-name BSAs load; treasure ESP must follow its resource
master. The [older audit](../records/book-covers-audit-2026-09-03.md) is corrected
on this point; its historical acceptance claims are not reused.

Static proof:

- All four archives match fresh Nexus API sizes and pinned SHA-256. Explicit
  7-Zip test and fresh extraction returned exit0 for each; existing cache size
  alone was not considered verification.
- Two BSAs fully decoded into2,212 audited assets:641 NIF and1,571 DDS. All
  resource-record model paths and TXST texture paths resolve in supplied assets.
- Resource ESP has709 TXST and621 STAT, no BOOK/CELL/REFR/WRLD overrides.
  Treasure ESP has12 BOOKs; all36 BCS resource links resolve against ESLfy.
- Five INIs contain909 statements/899 distinct syntactic targets. With the
  treasure plugin, every original910 BCS BOOK FormKey is covered. There is
  **not** evidence that all books introduced by other mods are covered.
- INIs change only models, alternate textures and inventory art. The treasure
  plugin preserves current English names, value, weight, skills, flags,
  keywords, sounds and VMAD. Its removal of embedded map-image tags is
  intentional to prevent doubled drawings; do not forward those tags back.
  Its names are English, so a non-English release needs localization.
- Missing Books has one extra invalid target, `Skyrim.esm|1BEF1`; the correct
  `Dragonborn.esm|1BEF1` is already in the base Dragonborn INI. Public SkyPatcher
  [explicit-target processing](https://github.com/Zzyxz/SkyPatcher/blob/main/book.cpp)
  checks null/type and does not turn this pure explicit target into a catch-all.
  It is a documented no-op, not a missing cover. No vendor repair was made.
- Ten HearthFires targets repeat identical assignments. Two EditorIDs differ
  only by case; standard TESForm/BSFixedString lookup is case-insensitive.
  This is API-contract evidence, not an exact installed-DLL execution claim.
- Every DDS has a full mip chain.1,570 are <=1024. The only2048x1024 DDS is the
  readable Dragonstone parchment, matching actual Bethesda source dimensions
  and BC3 format. Under [texture policy](TEXTURE_POLICY.md), readable surfaces
  are not automatically small clutter; no upscale or downscale is required.

The chosen resource-only route intentionally omits original placement/physics
overrides. Do not add the optional Cell/World version without a new compatibility
decision. Runtime inspection must cover representative book types, all12 maps,
SkyPatcher initialization and placed-book behavior.

Local preparation evidence: `records-work/bcs-install-20260906/` contains
`archive-receipts.json`, `payload-manifest.json`, `asset-manifest.json`,
`audit-result.json`, `final-review.json`, four controller-compatible mapping
plans and the original selected payloads. These are local evidence/artifacts,
not public vendor downloads.

### Detected installer defect and recovery

The first live attempt passed an exact `--file-id` argument, but the helper
recognized only `--file` and silently ignored the unknown spelling. Automatic
selection installed Desaturated instead of approved Original assets and the
regular resource ESP instead of ESLfy. **No game was launched.** The mismatch
was detected against the audited selection; it was not a user preference change
or evidence that those alternative vendor variants are inherently broken.

Root replaced the incorrect selections using the exact audited files and
changed `audit/install_mod.py` to strict argparse with both supported aliases
and unknown-option rejection. Ledger replacement now keys the physical mod
folder, preventing another component of the same source archive from being
mistaken for the row being replaced. Independent review additionally caught
that zero could be interpreted as an absent file ID; root added positive-ID
validation and disabled argparse option abbreviation.

Eight passing offline tests in `audit/test_install_mod_arguments.py` now cover
selector aliases, unknown options, missing values, explicit automatic-selection
default, nonpositive IDs, abbreviated options, same-archive installations into
two distinct folders, and same-folder replacement preserving unrelated rows.
The two ledger tests exercise real `_install` selection with mocked modasset
import, archive open, controller, ledger and Keep boundaries: no live mutation,
credential read or network access occurs. This independently reviewed fix does
not constitute a full audit of every legacy installer transaction path.

[#247](https://github.com/Ensrick/skyrim-mod-assistant/issues/247), under lifecycle
tracker[#235](https://github.com/Ensrick/skyrim-mod-assistant/issues/235), records
the incident, source fix and recovery. Root's subsequent **13 runtime-payload
winner checks passed**, subsequently extended to **15 with Lucien**, including
exact Original file40352 BSA hashes and ESLfy file467900 resource ESP hash.
The incorrect Desaturated/non-ESL choices no longer win. The final owned
weapon/cloak source and installed freshness checks also passed; runtime
acceptance remains unverified. Do not replace a reviewed hash with an
accidentally selected file's hash to make the gate green.

## High Poly Project: held decision, not an installed full package

[HPP5.3](https://www.nexusmods.com/skyrimspecialedition/mods/12029) main file236420
was inspected alongside [Xtudo's fixes](https://www.nexusmods.com/skyrimspecialedition/mods/63425)
and [Skurkbro's fixes](https://www.nexusmods.com/skyrimspecialedition/mods/64137).
The precise pending decision, defect list and acceptance checklist are in
[#246](https://github.com/Ensrick/skyrim-mod-assistant/issues/246), related to
the broader baseline tracker[#107](https://github.com/Ensrick/skyrim-mod-assistant/issues/107).

| Fix source/file | Version | Relevance, not automatic adoption |
|---|---|---|
| Xtudo63425 / 333337 | 2.0 | Campfire AIO; requires existing Campfire |
| Xtudo63425 / 327730 | 1.21 | Author-supplied1K raw beef |
| Xtudo63425 / 327737 | 1.22 | Author-supplied1K Campfire wood |
| Xtudo63425 / 351809 | 2.2 | Missing wheat textures |
| Xtudo63425 / 675848 | 2.5 | Three MLO2 horn-candle meshes; only if candles retained |
| Xtudo63425 / 711810 | 2.7 | Animated wood, not included in AIO |
| Skurkbro64137 / 266372 | 1.01 actual file | Overlapping wood normals/hay fixes; no effective layer in conservative candidate |

Eight archives passed exact-size/SHA-256 and explicit7-Zip exit0 checks.
Full staged combination has318 effective files:183 NIF/133 DDS/2 ESP. It is
not install-ready:73 DDS exceed1K, cabbage's normal lacks mipmaps, and both
Windhelm throne meshes request missing
`textures/architecture/windhelm/sonsofskyrimfancybanner_n.dds`.

The conservative feasibility candidate has155 files:113 NIF/41 DDS/1 ESP-FE,
no missing referenced textures or mipless textures found, and all newly
supplied DDS <=1K. Entire dependent families are held together, including
Torpor's plugin when its model is omitted. This is a **substantial selection
requiring owner approval**, not a permission to silently trim the requested mod.

Dedicated small-clutter excesses include food, garlic and satchel. Furniture,
horn-candle/wine atlases, barrels and other shared/larger assets require
source-step and viewing-distance review; the conservative candidate's omission
does not declare all of them subject to a1K ceiling. Main HPP has contact-first
permissions; Xtudo/Skurkbro require permission to modify. No blanket derivative
asset permission was established, so no downscale or mesh repair was created.

Order/conflict gates before any selected installation:

- Use explicit mappings: the Plants FOMOD selection also bundles Statues,
  Wine Bottles, Dungeons and Furniture.
- Preserve AMF/UMF and SLWF cart repairs, plus Skyland tent/stonewall textures.
  Proposed base placement is after SMIM, before Skyland/MLO2/specific fixes;
  verify effective paths rather than relying on mod names.
- Full HPP overlaps eight Ulvenwald firewood/chopping paths, not tree meshes.
  Decide that wood winner explicitly. Do not change the tree overhaul.
- If candles are excluded, the MLO2 candle patch has no place in the install.
  If no Skurkbro file wins, do not register an empty installed layer.
- Campfire ESP has seven vanilla overrides, including FURN script data;
  it is not merely a model-path edit. Root must inspect winning fields.

Private evidence and exact source/effective plans are in
`records-work/hpp-install-20260906/HANDOFF.md`, `stage-summary.json`,
`stage-validation.json`, `texture-baselines.json` and per-archive receipts.
No full or conservative HPP option is runtime-validated.

## Animation Queue Fix: installed vendor1.0.2, runtime still open

[Official AQF](https://www.nexusmods.com/skyrimspecialedition/mods/82395)
file798212 was uploaded2026-08-31. Installed by transaction
`20260906T202745090Z-bd8e9a92185e` as `Animation Queue Fix`; enabled and Keep
confirmed by root. Existing SKSE2.3.1, Address Library for1.7.104 and MSVC
runtime satisfy the inspected prerequisite surface.

- Archive SHA-256: `B2DEFF34AA462D5D439F56FE5ED86B32028E959ED02D361CACDC51504BAB1B89`.
- DLL SHA-256: `EC6F0C63208BD6DF1B39D7E477C00125BED1FC32B8932C5EC568E8959DA3DBEE`.
- Actual export declares1.0.2.0, NoStruct plus AddressLibraryV5; version-independent
  admission passes for1.7.104 without changing loader gates or timestamps.
  AMD64 imports and matching vendor PDB GUID/age were checked.
- It supplies DLL/PDB only: no ESP, scripts or configuration. Installed OAR's
  normal preloading remains; AQF complements it, not replaces it.
- Source at [26b5f0f](https://github.com/ersh1/AnimationQueueFix/commit/26b5f0fbe66b21696fa5f2ed2fc261d1ebb74a46)
  agrees with release declarations. This is **not** a reproducible source-build
  claim, exact-hook disassembly proof, or an executed loader test.

The old1.0.1 gate failure is historical, not a current1.0.2 blocker. Keep[#129](https://github.com/Ensrick/skyrim-mod-assistant/issues/129)
open for authorized fresh-character/OAR/SkyParkour runtime testing. Source is
GPL-3.0-or-later with its stated modding/linking exceptions, not MIT. The Nexus
archive lacks license text; preserve source/license provenance separately and
do not repackage this vendor binary as our original work.

Local receipts: `records-work/aqf-install-20260906/intake.json` and
`verification.json`; their stage-time status strings predate root's installation.

## Apocalypse: installed 10.3.0; runtime and integration follow-up open

The approved [Apocalypse - Magic of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1090)
candidate is **10.3.0, file793875, uploaded 2026-08-23**, one full-slot ESP plus two BSAs, with Skyrim/Update/
Dragonborn masters. SkyUI is relevant for its MCM, not a hard dependency for
basic content. Do not add a perk/magic overhaul or NPC-spell-distribution mod
merely to install this additive pack.

Root installed it in transaction `20260906T204333169Z-65fc5e62e6cc`, before
Water for ENB's main plugin, while keeping the global weapon-balance patch last.
That order does not replace exact winning-field/script validation.

- Archive SHA-256: `738181F46EB4E6BDCDFC9DA9093972454A2A6E16C354C627A4CEEF9BD1894848`.
- ESP SHA-256: `B0A9632372F2117F7D96583E1522B42758F414129D3572F848B8F7AC65681384`.
- Inspection counts3,948 records/3,916 plugin-owned forms, no deleted records,
  95 weapons including70 staves, and183 DDS, none beyond4096. Eight DDS exceed
  1K and need their actual use/source judged, not a blanket clutter assumption.
- Remaining master-indexed declarations include intentionally injected keyword
  identities and structural records; a non-owned count is not automatically
  a conflict or cleaning instruction. Do not compact/ESL-flag this vendor ESP.
- Runtime distribution, summon equipment and existing script winners require
  root review; a low override count does not prove conflict-free integration.
  In particular, non-staff weapons mean the owned weapon-balance freshness
  audit must inspect selection/exclusions before regeneration.

Root owns final compatibility and install receipts, ledger/Keep/order,
effective BSA/script winners and dependent weapon/cloak proofs. Installation
does not establish gameplay acceptance. Local
`records-work/apocalypse-install-20260906/inspection.json` and
`script-inspection.json` are candidate evidence; the latter explicitly inventories
collisions rather than claiming every BSA is active or which script wins.
The [prior inclusion review](../records/apocalypse-inclusion-principle-2026-09-04.md)
provides context, not permission to waive those gates.

[#248](https://github.com/Ensrick/skyrim-mod-assistant/issues/248) records the
narrow summoned-equipment and Locate Gold/regional-currency follow-up under
[#215](https://github.com/Ensrick/skyrim-mod-assistant/issues/215). Trace and
classify internal/summoned gear before applying ordinary equipment balance or
distribution. Locate Gold's vanilla-coin coverage does not automatically cover
all owned physical regional denominations; inspect its exact mechanism before
designing a separate compatibility patch. No automatic NPC spell distribution,
conversion of internal equipment to bandit loot, or currency balance change is
authorized by that issue.

## Lucien follow-on: core installed, optional integrations held

[Lucien](https://www.nexusmods.com/skyrimspecialedition/mods/20035) main **1.7.2**,
file **770173** (2026-06-30), is installed by root in transaction
`20260906T204846860Z-135ab81f06a8`, before Skyrim Unbound/Lux winners.
Its two vendor files are `Lucien.esp` and `Lucien.bsa`; no DLL is shipped.
The plugin masters are the five official masters, with 19,205 records,
19,191 plugin-owned forms and no deleted records. Its 24 structure textures
at 2K and two 512-pixel face tints do not establish a texture-cap violation.

- Archive SHA-256: `2D9AC2131CE7EBF1316E8F3D7563D03397C7EB56FADF54CB5A8C06BA68EF977D`.
- ESP SHA-256: `A33E5FE06C36D4D2B504C8B00733AFAE0CA0F6002862E34FC135D6EAE5C0915A`.
- BSA SHA-256: `04CE9AF0E3A186179A021A4E8E661AF1687827AAD320D396E30CF27C776B4578`.

[#249](https://github.com/Ensrick/skyrim-mod-assistant/issues/249) tracks the
owner's optional dialogue choices: official Moonpath file67131 v1.0.0, Bruma
file338770 v1.6.3a and AE file293450 v1.6.3a. None was downloaded by the intake
agent or included in the core transaction. Verify actual matching content
before adopting any. Apocalypse training is built in, and Lucien 1.7 already
incorporates Dumzbthar room markers/Dwemer Ruin Redux; do not add superseded
standalone fixes as presumed requirements.

The raw `Lux - Lucien.esp` from current Lux Patch Hub 7.1/file695703 is
**held as outdated against Lucien 1.7.2**. Five referenced Lucien REFRs no
longer exist (`1B5D3F`, `202873`, `202874`, `202875`, `202878`), and three
Dumzbthar cells would lose new Lucien music. A music-only forward is not an
adequate repair. Lucien can retain its own dungeon lighting while a current,
permitted integration is evaluated. Evidence is in local
`records-work/lucien-install-20260906/lux-target-resolution.json`.

Root added an exact weapon-policy exclusion for Lucien's invisible Hunger
natural attack `2E447A:Lucien.esp`, preserving vendor speed **5**. The normal
Jailer's Battle Axe and 20 conventional Apocalypse melee weapons follow the
existing balancing policy. Weapon fixture tests and root's final source and
installed freshness verification passed. A separate refreshed
weapon-output review classified all 98 added WEAP records and verified only
13 speed overrides (12 Apocalypse weapons and the Jailer's Battle Axe).
The invisible Hunger attack is absent from the generated override plugin,
preserving speed 5, and the 15 prior manual rules remain unchanged. Evidence
is local `records-work/lucien-install-20260906/weapon-review.json`; this
bounded output check is not a global preflight or runtime pass. The control staff
and internal/quest armor must not be automatically treated as generic loot.

Lucien's author prohibits importing him into NFF management. Existing NFF
provides NoImport faction `5C4445` and IgnoreToken `1CFC8D`, but the intake
found no automatically assigned Lucien-specific exclusion. Use the supported
safety mechanism or enforce the no-import rule; do not invent a configuration
switch or claim protection is already applied. Any publication of modified
Lucien assets/patches requires attention to the author's consent terms.
Local main receipts are in `records-work/lucien-install-20260906/`; their
stage-time status strings predate the root installation. **No runtime test
was performed by this work.**

## Provenance, publication and test boundaries

The initial narrow author read found no stored exclusions for DanielCoffey
(901), Ershin (82395), EnaiSiaion (1090), or JosephRussell (20035). It did find
legacy raw Excluded entries for SICreef (user 2812107, mod 109254) and Hishigami
(user 2977510, mod 149814).

Root then refreshed the six existing Keep decisions through the supported
relay with official author metadata. The final independent read verified all
six exact live mod-journal rows: Keep status, Nexus username, user ID, and
profile URL, applying `shared.js`'s supported nested-author normalization.
**SICreef and Hishigami are both effectively not excluded**, because their
author identities now match the current Keep author index and the extension
intentionally filters kept authors out of its effective blocked list.

The raw legacy exclusions remain stored; no Include journal override or raw
entry deletion is claimed. Only `blockedAuthors`, `nlcAuthorDecision:*`, and
the six exact mod-journal keys were read; the large `modDecisions` value and
unrelated decisions were not read by this final check. No Firefox database,
extension code, or author-list mutation was made by the verification task.

Vendor archives, textures, meshes, PEX/ESP/DLL binaries and private generated
artifacts remain local; original sources/plans and receipts may be published
through normal repository review. Permissive vendor terms do not make vendor
files first-party artifacts or automatically authorize a license change.
BCS/Missing Books permit modification with attribution; upstream contributor
credits and noncommercial restrictions remain. HPP/fix permissions require
separate handling before derivatives. Follow [redistribution policy](../REDISTRIBUTION.md)
and [texture policy](TEXTURE_POLICY.md), including a tracked issue for any
future approved downscale.

Only root performs serialized live mutations, re-reads shared ledger/changelog,
reconciles Keeps after actual installs, and validates downstream patch freshness.
No preparation task edits Fable's render/input INIs or the four protected dirty
conflict reports. A passing static check is not a gameplay or global preflight
pass. The current currency build independently requires a fresh character or
an explicitly admitted save; no unattended visible/audible launch is permitted.
