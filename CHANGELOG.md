# Change log

**User directive (2026-08-31, verbatim):** "now we're keeping a changelog so we
can trace every change back to its source. With each change we must
successfully launch the game and load the save." Launch criterion, verbatim:
"It must reach the main menu in under 60 seconds or it's a failure."

Every entry carries:

- **What** changed - mod installed/removed/parked/unparked, INI key, tool
  change, generated patch or overlay, or a decision that changes build state.
- **Source** - who or what caused it: the user's words, the issue number, the
  agent/session, or the research record that justified it.
- **Verification** - `VERIFIED <date>` (main menu in under 60 seconds AND the
  save loaded), `UNVERIFIED`, or `FAILED <evidence>`.

Newest first. Times are local (UTC-5); `installedUtc` stamps in
`records/installed-mods.json` are UTC. Rules for landing new entries:
"Changelog discipline" in `docs/CURATION_POLICY.md`.

> **STATE (2026-09-01 17:28): VERIFIED BASELINE RESTORED.** The 08-31 failure
> wave was root-caused to the truncated `ccvsvsse004-beafarmer.bsa` (#142, no
> mod at fault) plus a LaunchProbe kPostLoadGame handler bug that AV'd only on
> successful loads. Both fixed; `records/launch-verify-20260901-172851.md` is
> the first full PASS (main menu 31.2s, save loaded 35.7s, success=1) over the
> restored 231-plugin modlist. The ~40 change batches of 08-30/31 are now
> covered by that PASS at the launch/load level; per-mod in-game behaviour
> remains individually unverified. Still open on #142: Creations re-download
> of Farming + re-enabling its 2 patch plugins.
>
> (Superseded warning of 2026-08-31 kept for history: everything between the
> 08-29 17:23 checkpoint and the 08-31 22:00 wave was UNVERIFIED and launches
> were failing on top of it.)

---

## 2026-09-05 16:02 - Private longsword curation and isolated soldier distribution installed (#237)

- **What:** Added `Ensrick - Lost LongSwords Curation (Private)` through the
  claimed headless controller, transaction `20260905T210155503Z-a6eaebf1b49c`.
  Two small ESPFEs (14 + 3 records), four SkyPatcher INIs/99 operations. Nine
  retained two-handed longswords use the approved Speed 1.0/damage-by-tier
  policy. Dwarven/Elven/Glass acquisition is suppressed; Dragonbone stays absent.
  Matching Imperial/Stormcloak swords have approximately 1/12 eligible ordinary
  soldier selection rates. Guard/commander/named military branches are excluded.
  The unsafe shared ordinary-bandit equipment route is deferred; clean boss,
  loot, smith, Skyforge and Silver Hand routes remain. Vendor assets/plugin and
  saved inventories are not edited. Early placement restores reviewed master
  fixes; a separate later Stormcloak plugin avoids illegal dependency ordering.
- **Source:** User approval of the September balance proposal and subsequent
  explicit request to distribute both faction longswords. Source `8716066`;
  complete hashes/order transactions in
  `records/source-builds/ensrick-lost-longswords-curation.json`.
- **Verification:** **UNVERIFIED in-game.** Both strict round trips, all 161
  output FormLinks, 99 native parser operations, 13 synthetic tests, planned
  graph 214/214 and initial installed graph 215/215 passed. All six installed
  files match the build. Order/ledger/Keep gates pass. No game was launched.
  Global balance regeneration is tracked separately under #239; do not confuse
  record-index balancing with measured swing cadence or stamina efficiency.

## 2026-09-03 16:54 - Regional currency stack v0.2.4 installed and save-load verified (#207)

- **What:** Installed the complete current C.O.I.N. 3.5.3 / M.I.N.T. 1.0.6 /
  ECE 4.1.1 regional-currency stack, WiZkiD Classic Gold Septim visuals, and
  required 1.7.104 native overlays. The owned 26-file v0.2.4 package remains at
  MO2 priority 274 and its 45-record ESPFE is plugin priority 265 (last).
  Final replacement transaction `20260903T215105935Z-e5b6eed589b6`; archive
  21,604 bytes, SHA-256
  `DF6991C75F05CEEFFF9F613735AA1DDF43E4EE03CB1FD2FAAF1688125D0A176B`.
  It implements the approved 75/20/5 loose Septim mix at 1/25/100 values,
  currency weights, cultural/ancient precedence, regional purses, ten one-way
  bank exchanges, and disables 17 smelting-arbitrage recipes. The last audit
  fixed Gyldenhul's contradictory Drakr keyword so all of its treasure remains
  Septim-routed and added a loader-only Ma'dran compatibility shim; vendor mod
  folders and WiZkiD assets remain separate and untouched.
- **Source:** User decision accepting +975% loose-coin inflation in exchange
  for weighted money, strict future inventory limits, and constrained loot;
  implementation and open gameplay matrix tracked by #207-#211.
- **Verification:** **VERIFIED 2026-09-03**. Deterministic double generation of
  the ESP and all three PEX files, exact 9-master/397-link audit (plus 13 engine
  PlayerRef links), zero unresolved links/deletions, checked Spriggit roundtrip,
  deterministic archive, MO2 audit with zero errors, and byte-identical live
  payload all pass. `records/launch-verify-20260903-165425.md`: main menu 46.6s,
  existing save loaded 57.1s; 41 DLLs were examined, 40 SKSE plugins loaded
  correctly, `msdia140.dll` was correctly ignored as a non-plugin dependency,
  and there were zero plugin refusals. Currency Swapper,
  CDF, BOS, KID, SkyPatcher and DDR loaded their currency paths, and the old
  `DES_MadranSwapper` Papyrus warning is absent. Targeted in-world exchanges,
  purse sampling, Proteus switching and new-land coverage remain explicit
  acceptance work, not launch blockers.

## 2026-09-03 16:51 - Container Distribution Framework 3.1.0 native overlay packaging completed (#207)

- **What:** The source-built `CDF 1.7.104 Native Overlay - Ensrick` was
  installed at 12:33 local by transaction
  `20260903T173349678Z-11a8d9fa5141`, at MO2 priority 275 over the untouched
  vendor mod at 271. Its DLL is 1,115,136 bytes, SHA-256
  `725295A4D0AFE3F58DE9E04D603ADB54A0943398A8324B497CEAFC69CD8F8542`.
  At 15:47, the live overlay gained its Apache-2.0 license and source notice;
  at 16:51, all four files were captured by final controller replacement
  `20260903T215113092Z-dcb18589028d`, with the full upstream base hash in that
  notice. Neither step altered the DLL, PDB, or vendor configuration. GitHub Actions run
  33783954157 built the exact overlay from Ensrick commit
  `5f2ddbb4abd27c00d2c4d8aff56bd95dcc61ffd0`.
- **Source:** Current-runtime/no-modal port required by the approved currency
  stack, tracked by #207. Full provenance and file hashes are in
  `records/source-builds/ensrick-cdf-1.7.104.json`.
- **Verification:** **VERIFIED 2026-09-03**. The framework launch/load gate in
  `records/launch-verify-20260903-135633.md` passed, and the later complete
  live payload is covered by `records/launch-verify-20260903-165425.md` (main
  menu 46.6 seconds, existing save loaded 57.1 seconds). CDF loaded the owned
  currency rules without a currency-specific configuration error. A real
  merchant/nonmerchant `onlyVendors` exercise remains a gameplay acceptance
  test.

## 2026-09-03 13:52 - Currency Swapper 2.2.0 native overlay installed for Skyrim 1.7.104 (#207)

- **What:** Added and enabled the separate `Currency Swapper 1.7.104 Native
  Overlay - Ensrick` at MO2 priority 277 above the untouched Nexus 127686 file
  749947 install. It contains only the CI-built DLL/PDB plus licensing, hashes,
  and port notes; the vendor package remains authoritative for its INI, scripts,
  source script, and Custom Console data. MO2Headless transaction
  `20260903T185226265Z-3a1e007e2cf7`. The installed DLL is 998,912 bytes,
  SHA-256 `8A7D4E67FB2E12B4CD6FBCDEDEE4F070D7695CE46C056D8374B9FD9337873017`.
  Ensrick PR 1 was squash-merged to the protected `release/2.2.0` branch as
  `7c60745046bdd90a0cd72b4d213becc1d0e4f4d3`; its green artifact-producing
  Actions run is 33789590452. The effective winner, exact 1.7.104 SKSE
  declaration, format-5 marker, 18 hook sites, three callable targets, and
  absence of MessageBox strings all passed. Build/default provenance is in
  `records/source-builds/ensrick-currency-swapper-1.7.104.json`.
- **Source:** User-approved full regional-currency setup and the current-runtime,
  no-background-popup requirements tracked by #207; source port/install under
  the existing `sol/currency-stack` profile claim.
- **Verification:** **VERIFIED 2026-09-03** at the launch/load gate:
  `records/launch-verify-20260903-135633.md` reached the main menu in 40.2
  seconds and loaded the save in 49.6 seconds. SKSE reports the plugin loaded
  correctly; `CurrencySwapper.log` confirms its INI read, all 18 hooks
  installed, and serialization registered without an error. Real barter,
  training, bounty, and exchange behavior remains a gameplay acceptance gate.

## 2026-09-03 13:04 - Dynamic Dialogue Replacer 1.4.1 native overlay installed for Skyrim 1.7.104 (#207)

- **What:** Added and enabled the separate `DDR 1.7.104 Native Overlay -
  Ensrick` at MO2 priority 276 above the untouched Nexus 135618 file 748293
  install. It contains only the CI-built DLL/PDB plus licensing and port notes;
  the vendor package remains authoritative for scripts and dialogue data.
  MO2Headless transaction `20260903T180450805Z-4ba902c6aa7f`. The installed
  DLL is 1,810,944 bytes, SHA-256
  `8167CE16D26CC6245D234E4B4CDF19F03F5CA120123AD06E051730F7271EE48C`.
  Ensrick PR 1 was merged as `d4951ac5c7f2373155ba89f0697918b6d536d854`;
  its green Actions run is 33786541714. The effective winner, exact 1.7.104
  SKSE metadata, format-5 marker, four hook sites, callable/vtable targets, and
  absence of MessageBox strings all passed. Build/default provenance is in
  `records/source-builds/ensrick-ddr-1.7.104.json`.
- **Source:** User-approved full regional-currency setup and the current-runtime,
  no-background-popup requirements tracked by #207; implementation authorized
  by the `sol/currency-stack` owner after the reproducible CI artifact passed.
- **Verification:** **VERIFIED 2026-09-03** at the launch/load gate:
  `records/launch-verify-20260903-135633.md` reached the main menu in 40.2
  seconds and loaded the save in 49.6 seconds. SKSE reports the plugin loaded
  correctly; `DynamicDialogueReplacer.log` confirms hooks installed, plugin
  load, and initialization of the Exchange Currency replacement file with one
  script. A real replaced-dialogue exercise remains a gameplay acceptance gate.

## 2026-09-03 00:05 - Ensrick Wolf Territorial Patch installed: wolves warn at 2500 and attack at 640 instead of 1500 (#42)

- **What:** New generated plugin `Ensrick Wolf Territorial Patch.esp` (ESL-flagged,
  override-only, **9 NPC_ records**, 3,959 bytes, sha256 `63745001...A899`, masters
  Skyrim.esm + BSHeartland.esm + arnima.esm + Gray Fox Cowl.esm) in local mod
  `Ensrick - Wolf Territorial Patch` (MO2Headless `mod-stage` tx
  `20260903T043304979Z-df62ddac4fa0`, priority 263; `plugin-enable` tx
  `20260903T043309857Z-d7b48a5d5a09`; 244 active plugins). **The wolf/bear difference
  is one AI Data field and it is not the aggression enum**: `EncWolf` (023ABE) and
  `EncBear` (023A8A) are both Unaggressive with AggroRadiusBehavior on, both
  WarnOrAttack 2000, both Attack 1500 - the difference is `Warn`, bear **2500** vs wolf
  **0**, so bears have a warning band and wolves cross straight into attack at 1500
  units (~21 m). `EncHorker`, the other actor the user named, is Aggressive but attacks
  only inside **320**. The patch sets the 8 ambient wolf bases to **2500 / 1200 / 640**:
  `EncWolf` (107 placed refs), `manny_GF_Animal_DesertWolf` (Gray Cowl, 41),
  `CYREncWolf` (Bruma, 15), `CYREncWolfTimber` (4), `EncWolfarnima2` (Beyond Reach, 3),
  `EncWolfarnima` (1), `CYREncWolfHighland` and `CYREncWolfDire` (leveled-list only).
  Aggression stays Unaggressive, `csWolf`'s flanking data (DATA 0x2, FlankDistance 0.5,
  StalkTime 0.4) is untouched so packs still flank, and **no faction record was edited**:
  `PredatorFaction -> PreyFaction = Enemy` is what makes wolves hunt deer and bears and
  sabre cats share it. Eleven records follow through their AI-data template and the
  generator *measures* that set from the load order rather than trusting the policy;
  one heir, `SummonFireStorm` (0877EB, the conjured Flaming Familiar), is deliberately
  de-inherited and pinned to the old 0/2000/1500. 52 wolf records excluded with a
  reason each in `mods/wolf-territorial-patch/policy.json` - `EncWolfIce`
  (VeryAggressive on purpose, open user decision), bandit/pit wolves, Companions spirit
  wolves, Howl summons, CC bone wolves, Beyond Reach quest wolves, 3DNPC named wolves,
  Proteus and BSAssets template zoos. Machine-readable audit
  `mods/wolf-territorial-patch/work/wolf-audit.json` (60 wolf records + 29 reference
  controls over 323 plugins, 24,207 placed actor refs). Generator, `policy.json` and
  Spriggit tree committed under `mods/wolf-territorial-patch/` (`regenerate.ps1`, 2
  byte-identical runs, 117 links / 0 unresolved, checked Spriggit round-trip); build
  record `records/source-builds/ensrick-wolf-territorial-patch.json`; ledger row
  `distribution: distributable`. LOOT rule added to `config/loot/userlist.yaml` and the
  live userlist (group `Ensrick Generated Patches`, after the Guard Scaling Patch); **no
  LOOT sort was run** - the plugin already lands last and `audit/verify_order.py` is
  CLEAN, so the rule takes effect at the next sort. Rollback: disable the one mod.
- **Also generated but NOT installed:** `Ensrick Wolf Encounter Thinning.esp` (191
  placed-actor Initially Disabled overrides, 381 records, sha256 `739AAFE6...0ED3`) in
  `mods/wolf-territorial-patch/thinning/package/`. 622 exterior refs on the seven
  wolf-bearing regional predator actors form 387 clusters at a 2000-unit link radius
  (203 singletons, 137 pairs, 43 triples, 4 quads); retiring the singleton clusters
  removes 191 refs (30.7%) and leaves 431 refs in 196 clusters, every surviving site >=
  2. Not installed because the cut size is a taste decision. Hands #43 exactly 191
  navmeshed, encounter-zoned exterior positions.
- **Source:** user design on #42 (2026-09-02, after playing): territorial like horkers
  and bears, "making everything attack them, and making them attack everything" is the
  objection; team-lead brief 2026-09-03 - suggest visual mods with links, but implement
  anything that needs no new download. The visual half (Canidae 182994) stays a
  suggestion and nothing was downloaded for it beyond the audit cache.
- **Verification:** VERIFIED 2026-09-03 00:00 - `launch_verify` PASS, main menu
  **31.9 s**, save loaded **40.6 s** (`kPostLoadGame success=1`), direct chain, claim
  `claude/wolves-ui`, preflight clean (4 pre-existing warnings), `install_mod.py
  --verify` 0 problems. Record: `records/launch-verify-20260902-233602.md`. The
  *behaviour* is not yet witnessed in-game: 2500/1200/640 is a play-feel choice and
  needs an approach/retreat test on a live wolf pack. Existing wolves in the save keep
  their loaded AI data until the cell resets.

## 2026-09-03 00:10 - UI slot and survival readout researched; nothing installed (#31, #35, #111)

- **What:** `records/ui-slot-and-survival-readout-2026-09-02.md` (revised under the
  2026-09-03 no-new-mods constraint; every mod named is a Nexus link and nothing was
  installed). The readout is possible: a `GLOB` dump across CC survival + SMI +
  Starfrost shows the live pairs are `Survival_HungerNeedValue`/`MaxValue` **0/120**
  (Starfrost) and `Survival_ColdNeedValue`/`MaxValue` **55/900** (SMI), so anything
  reading the value/max pair renders a true proportional bar. The obvious candidate is
  wrong: `iWant Widgets for Starfrost` 2.0 reads Starfrost's *magic effects* and is
  invisible below stage 3. `Survival Control Panel` is a configuration framework and
  renders no meter - that question is now closed and belongs only to #95. SKSE gate
  with PE stamps: **TrueHUD 1.1.10 PASS** (2026-08-29 18:35:01Z, V5 bit set),
  **moreHUD 5.4.2.0 PASS** (2026-08-30 22:28:11Z, stamped after the support date),
  **Prisma UI 1.4.1 FAIL** (2026-03-27), **Skyrim Party Sheet 3.1 FAIL** (2026-07-28),
  **iWant Widgets NG 1.2.8 FAIL** (2024-06-07). TrueHUD's floating bars are one flag -
  `bEnableActorInfoBars` in the shipped `MCM/Config/TrueHUD/settings.ini`, independent
  of `bEnableBossBars`, `bEnablePlayerWidget`, `bEnableRecentLoot` - so the user's
  "floating healthbars look terrible" does not cost us the mod. NORDIC UI declined:
  0/19 in the survey, v2.4.1 last updated 2021-08-14, requires SkyHUD, and ships enemy
  health bars. Suggested skin: Untarnished UI, on his own recorded vanilla-shape taste
  rather than counts. **Nothing installable without a download was found**: the one
  no-new-mod lever is SMI's own `fAmbientWarmthWidgetColdLevelThreshold=200.0`, and it
  was deliberately left alone because the comment's direction is ambiguous and only an
  in-game check settles it.
- **Source:** user 2026-09-02 - "having a bar for it would be nice", "I don't like ...
  floating healthbars"; team-lead constraint 2026-09-03.
- **Verification:** research only - no mod installed, no profile or INI file written,
  no launch of its own. Every DLL verdict carries its PE stamp; archive sha256s are in
  the record.

## 2026-09-02 23:45 - Wolf visuals/behaviour/spawns and the UI-plus-survival-readout audit (#42, #31, #35, #111)

- **What:** two research passes, no build state changed. (1) `docs/WILDLIFE-WOLVES-2026-08-28.md`
  gains a dated appendix answering the four requirements the user added to #42:
  **Canidae 2.25 (182994) core option** recommended for visuals (six of seven
  textures clear the 0.70 distance floor; `blackwolf_body.dds` fails at x0.54 and
  the `mip_retention.py --resharpen` recipe lifts it to x0.89); the wolf/bear
  behaviour gap measured as **one AI Data field** - `Warn` 0 vs 2500, with
  `EncHorker` attacking only inside 320 units - and the faction layer shown to
  need no edit; and the spawn arithmetic resolved to **666 placed predator refs
  in 406 clusters (205 singletons)**, with a singleton retirement cutting 31% of
  wilderness spawn sites while raising mean pack size to 2.29.
  (2) New `records/ui-slot-and-survival-readout-2026-09-02.md`: the effective
  `Survival_*NeedValue`/`MaxValue` globals dumped from CC + SMI + Starfrost prove
  a proportional readout is possible today; **TrueHUD 1.1.10 PASSes** the gate
  (PE 2026-08-29 18:35:01Z, V5 bit set) and its floating bars are one ini flag
  (`bEnableActorInfoBars`); **moreHUD 5.4.2.0 PASSes** (PE 2026-08-30 22:28:11Z);
  **Prisma UI 1.4.1, Skyrim Party Sheet 3.1 and iWant Widgets NG 1.2.8 FAIL**;
  NORDIC UI declined (v2.4.1, 2021-08-14, requires SkyHUD, ships enemy bars).
- **Source:** user messages 2026-09-02 (the #42 design comment; "having a bar for
  it would be nice"; "I don't like ... floating healthbars"), dispatched by the
  team lead as an audit-only research task.
- **Tracked:** #202 (Ensrick Survival Meters on iWant Widgets), #203 (Prisma UI
  gate + licence decision), #204 (Canidae adoption + two recipe fixes), #205
  (TrueHUD with actor info bars off); findings commented onto #42, #43, #31,
  #35, #111.
- **Verification:** research only - no mod installed, no profile or INI file
  written, no launch. Archives went to the MO2 download cache and were extracted
  to a scratch directory outside `mods\`; every DLL verdict carries its PE stamp
  and every texture verdict its measured ratio.

## 2026-09-03 17:35 - Better MessageBox Controls 1.2 installed (Nexus 1428)

- **What:** one file, `Interface\messagebox.swf`. No plugin, no DLL, so the
  2016-11-26 date carries no runtime risk on 1.7.104 - the same reasoning that
  applied to its sibling Better Dialogue Controls (1429). **Sole owner of that
  path in the load order** (`find -iname messagebox.swf` returns only this mod),
  and it is a different file from `dialoguemenu.swf`, so it complements 1429
  rather than competing with it. Transaction
  `20260903T223529943Z-22355591313e`. Gates after install:
  `install_mod --verify` `0 problem(s)`, `verify_order` CLEAN over 262 active
  plugins.
- **Source:** user, 2026-09-03 - *"What about Better MessageBox Controls?"* then
  *"Put it in"*. Rule 0 check recorded honestly: it scores **0 mentions across
  the 19 curated lists** in `docs/ECOSYSTEM-SURVEY-2026-08-30.md`, and is absent
  from `SLOT_CANDIDATES.md`. The nearest surveyed mod is **Yes I'm Sure NG**
  (8/19, STEP and Lexy), which is a different mechanic - it skips confirmation
  prompts rather than fixing how they are navigated. So the case for this is
  "the same fix the user already liked, applied to message boxes", not
  community consensus. Told to him that way before he chose.
- **Verification:** **UNVERIFIED** - no launch yet. Deliberately not burning one
  on a lone SWF; it rides the next launch. Its Keep is queued (12 in the relay
  batch) and applies on the next Nexus page load.

## 2026-09-02 23:18 - Cloak distribution rebalanced; guards stop wearing two cloaks (#200)

- **What:** New mod `Ensrick - Cloak Distribution Balance` (MO2Headless
  `mod-stage`, transaction `20260903T041656059Z-01212abd1ef0`, priority 260,
  modlist row 3), one SkyPatcher config at
  `SKSE\Plugins\SkyPatcher\leveledList\zz Ensrick Cloak Balance\`. No plugin, no
  vendor bytes; `zz` makes SkyPatcher process it after every RMB config, which
  `SkyPatcher.log` confirms. Full measurement:
  `records/cloak-distribution-2026-09-02.md`.
- **Two root causes, both read off the installed configs, not inferred.**
  (1) **chanceNone, not entry count, is the bigger lever.** Every
  [Pelts o Plenty](https://www.nexusmods.com/skyrimspecialedition/mods/120726)
  leveled list rolls `chanceNone 0`; the twenty
  [Cloaks of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/6369)
  lists roll **25 to 90** (`LitemCloaksCommon` 70, `LitemCloaksThalmor` 90) -
  2017 numbers from when that mod injected straight into vanilla lists and had
  to gate its own rarity, which inside RMB double-dips on one side only. Exact
  leveled-list probability over the patched graph: a generic NPC's cloak was
  **1.0% Cloaks of Skyrim, 54.8% fur**, which is the report *"I don't ever
  recall seeing the cloaks of skyrim"* measured. #200's 7:1 entry-count figure
  for `B6C` is correct and is the smaller half. (2) **Cloaks of Skyrim reaches
  two of RMB's eight generic buckets**; Pelts reaches all eight.
- **The doubles are Sons of Skyrim, and it is not a leveled-list roll.** All
  fourteen outfits RMB injects a guard cloak list into are
  [Sons of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/68656)
  overrides that already contain a Sons of Skyrim hold cloak, so RMB adds a
  second cloak beside one that is already there. Pelts is on biped slot **57**
  (all 109 cloaks, mantles and pauldrons; 10 hoods on 31), Sons of Skyrim on
  **46** - including `0_Fur_Collar_Brown` - so a guard wears both at once; when
  the roll comes up a Cloaks of Skyrim cloak instead, that is slot 46 too and
  one of the two ends up carried. The other 44 patched outfits hold no
  cloak-slot item, so bandits and faction NPCs were only ever getting one. This
  is exactly the merge `RMB SPIDified - Sons of Skyrim` 83340 performs and which
  this build does not have (#195).
- **Four dials, each one number, each its own labelled block in the ini.**
  `[1] GUARDS` `chanceNone=100` on `B6C..B74` (guards wear only the Sons of
  Skyrim cloak; 0 restores RMB's second one). `[2] RATIO` `chanceNone=0` on the
  twenty Cloaks of Skyrim lists (raise to make cloth rarer; 70 is roughly the
  vendor default). `[3] FREQUENCY` `chanceNone=55` on the outfit-facing lists
  (RMB ships 35). `[5] WARM PARITY` four `addToLLs` putting cloth into the warm
  buckets, commentable - kept on because leaving six of eight buckets fur-only
  is what made cloth invisible; #189 is where the warmth keyword gets settled
  properly.
- **Five vendor defects fixed on the way, block `[4]`, not dials.** The dead
  `Cloaks - Dawnguard.esp|800` repointed at `Cloaks - RMB SPCH.esp|984`
  (`DLC1LItemCloaksDawnguard`), which is why the Dawnguard bucket was 100% fur
  and why `SkyPatcher.log` prints `Form not found` every launch; the two "Dark"
  Cloaks of Skyrim lists added to the dark buckets RMB left entirely to fur;
  nine `removeFromLLs` dropping `RMB_PoP_*Trimmed_UNUSED` 802/806/807, whose
  entry lists are identical member-for-member to 803/801/800, from the buckets
  that carry the original; and `B96`/`B9B`/`B97`/`B99` opened to 0 because RMB
  puts 35 on **both** `B5F` and its children, so the frequency gate compounded
  and generic NPCs were 58% cloakless rather than 35%.
- **Result** (exact, `records-work/cloak-dist-2026-09-02/simulate.py`): 55.0% of
  every covered non-guard NPC has no cloak; Cloaks of Skyrim is **23.8%** of a
  generic NPC's cloaks (was 1.0%), 20-60% of a faction NPC's; guards wear
  exactly one cloak, the Sons of Skyrim one.
- **One assumption, stated because it is the thing that could be wrong:**
  SkyPatcher applying a later `chanceNone` over an earlier one. File order is
  proven from the log; last-write-wins is not provable from disk. If it is
  first-write-wins, dials 1-3 are no-ops and the `addToLLs`/`removeFromLLs`
  lines still apply. The first play session settles it - guards still carrying
  two cloaks is the tell.
- **Source:** user, 2026-09-02, in play - *"a lot of NPCs have the fur cloaks. I
  don't ever recall seeing the cloaks of skyrim"*, some NPCs carrying two fur
  cloaks, and cloaks on more NPCs than intended. #200; refs #95, #189, #195.
- **Verification:** **VERIFIED 2026-09-02 23:18** by
  `records/launch-verify-20260902-231840.md` - main menu 32.0 s, save loaded
  40.4 s, 243 active plugins (unchanged - no plugin added), 36 SKSE plugins
  checked, 0 refused, no crash log. `SkyPatcher.log` shows the config loaded and
  processed after `Headgear\` and every RMB config, with no errors of its own.
  `install_mod.py --verify` 0 problem(s), `verify_order.py` CLEAN,
  `file_conflicts.py` no collision on the new file. **In-game distribution is
  UNVERIFIED** - proving it needs NPCs walked past, not a save load.

## 2026-09-02 23:18 - The ten unique Cloaks of Skyrim cloaks can now place (#187)

- **What:** New mod `Ensrick - Cloaks of Skyrim Unique Placement` (MO2Headless
  `mod-stage`, transaction `20260903T041656164Z-60d394e33f30`, priority 261,
  modlist row 2), one SkyPatcher config at
  `SKSE\Plugins\SkyPatcher\npc\zz Ensrick Unique Cloaks\`. Ten
  `filterByNpcs` directives replacing the ten in
  [RMB SPCH - Cloaks of Skyrim 116030](https://www.nexusmods.com/skyrimspecialedition/mods/116030)
  1.5.3, which name `Skyrim.esm` for FormIDs that live in
  `Cloaks - RMB SPCH.esp`. His ten stay on disk and stay inert; ours do the work.
  New file, never an edit: 116030 forbids editing its files, and
  [Cloaks of Skyrim 6369](https://www.nexusmods.com/skyrimspecialedition/mods/6369)
  grants open permission for compatibility patches.
- **Both defects verified by record, not by reading:** all ten items resolve as
  ARMO on biped slot 46 in `Cloaks - RMB SPCH.esp` (`CloakCrimson` D6B,
  `CloakDragonPriest` 8EF, `CloakDPVokun` 8FF, `CloakDPRahgot` 901,
  `CloakDPOtar` 8FE, `CloakDPVolsung` 900, `CloakDPHevnoraak` 8F1,
  `CloakDPMorokei` 8FD, `CloakDPNahkriin` 8F3, `CloakDPKrosis` 8FC) and none
  exists in `Skyrim.esm`; all ten target NPCs resolve in `Skyrim.esm`. Krosis'
  truncated filter `Skyrim.esm|767` corrected to `100767`
  (`dunShearpointKrosisDragonPriest`); `000767` returns `Record not found`.
  The failure was silent - SkyPatcher logs no miss on an npc `objectsToAdd`,
  which is why nine dragon priests and Idolaf Battle-Born got nothing without
  a line of evidence anywhere.
- **Source:** #187, from `records/cloak-layer-audit-2026-09-02.md` section 2.
  These are the cloaks that audit measured as base Cloaks of Skyrim's best
  textures.
- **Verification:** **VERIFIED 2026-09-02 23:18** by the same
  `records/launch-verify-20260902-231840.md` PASS; `SkyPatcher.log` shows
  `npc\zz Ensrick Unique Cloaks\Ensrick - Unique Cloak Placement.ini` processed
  with no errors. **Placement itself is UNVERIFIED** - it needs a dragon priest
  visited or Idolaf inspected in Whiterun.

## 2026-09-02 23:18 - Death hounds stop dropping dog meat (#199)

- **What:** New mod `Ensrick - Death Hound Loot Fix` (MO2Headless `mod-stage`,
  transaction `20260903T041656278Z-bcda5604bcb0`, priority 262, modlist row 1),
  one SkyPatcher line removing `FoodDogMeat` (`0EDB2E:Skyrim.esm`) from
  `DLC1DeathItemDeathHound` (`00D6F7:Dawnguard.esm`).
- **The drop is vanilla Dawnguard, not a mod.** That list is
  `LootSmallTreasure10` + `FoodDogMeat` + `DLC1DeathHoundCollar` with `UseAll`
  set, and **nothing in the 327-plugin order overrides it** - it was checked
  against every plugin, not assumed.
  [Simple Hunting Overhaul 95943](https://www.nexusmods.com/skyrimspecialedition/mods/95943)
  1.16 overrides 24 death-item lists and the death hound is not one of them, a
  gap `records/simple-hunting-overhaul-95943-2026-08-30.md` recorded at adoption.
- **Why removal rather than an SHO harvest entry, the choice #199 asked for.**
  SHO's meat branch gates nothing: its player alias adds `_MeatTracker` and
  returns, and time plus hunting experience are charged only when a **pelt**
  reaches `GlobalCheck()`. Adding the death hound to SHO's meat formlist would
  leave the meat exactly as lootable as it is now and would only mean anything
  once the owned harvest-time extension in #72 exists. A death hound is an
  undead vampire creature with no pelt: edible meat is the odd entry on it, not
  the missing one. One line beats a formlist patch that would not change
  behaviour.
- **Deliberately left alone:** `LootSmallTreasure10` on the same list (SHO
  strips it from the animals it covers, but that is not what was reported), and
  `1AF87E:Vigilant.esm zzzCHDeathItemHound`, which has the same shape but is a
  different creature in a different mod.
- **Source:** user, 2026-09-02, in-game observation. #199.
- **Verification:** **VERIFIED 2026-09-02 23:18** by the same
  `records/launch-verify-20260902-231840.md` PASS; `SkyPatcher.log` shows the
  config processed last in the leveled-list pass with no errors. **The loot
  itself is UNVERIFIED** - it needs a death hound killed and looted.

## 2026-09-02 23:05 - Fix the SKSE gate that let Smart Talk through (#197)

- **What:** `audit/skse_version_data.py` carried a PE-stamp reject window of
  `520128000 <= stamp < 1748217600` - an upper bound of **2025-05-26**. Address
  Library format 5 support only landed in CommonLibSSE-NG on **2026-08-21**
  (alandtse/CommonLibVR `7b47c5a8f1`, release 6.4.0), so every DLL linked in the
  15 months between those dates without the V5 flag passed a gate that exists
  to catch exactly that. Bound raised to `1787270400` (2026-08-21). Revalidated
  against three known outcomes: **Smart Talk** (stamp 2025-12-22) now FAILs -
  it passed before and then aborted the SKSE load at plugin 28 of 36;
  **L3sNoLoot** (2026-03-01) now FAILs; **Better Jumping** (2026-08-29) still
  PASSes, which matters because it does not set the V5 bit either - being built
  after the support date is what makes it safe.
- **Blast radius: zero new failures.** Scanned all 40 SKSE DLLs across the 232
  enabled mods. Four fail, all pre-existing and none caused by this change:
  `JContainers SE`, `PapyrusUtil SE` and `RaceMenu` fail for a different reason
  (no version-independence flag and no explicit 1.7.104 entry), and `Proteus`
  (2022-10-14) was inside the old window too. All four are vendor rows shadowed
  by the `* 1.7.104 Native Overlay - Ensrick` mods at higher priority
  (modlist 145-149 vs 195/196/254/255), which is why the build loads 35 SKSE
  plugins with 0 refused.
- **Source:** #197. The user's launch died today on a DLL this gate had cleared;
  the doctrine "the gate is necessary and never sufficient" was correct, but the
  gate was also simply wrong and could be made right.
- **Verification:** tooling only, no build state changed - no mod installed,
  disabled or reordered, no profile or INI change. Validated against four DLLs
  with known real-world outcomes plus the full enabled-mod scan.

## 2026-09-02 22:39 - Open Animation Replacer UNPARKED on author release 3.2.1 (Nexus 92109, #140)

- **What:** [`Open Animation Replacer`](https://www.nexusmods.com/skyrimspecialedition/mods/92109) upgraded 3.2.0 -> **3.2.1** (Nexus file
  798222, uploaded 2026-08-31, `92109-798222.7z`, 8.09 MB, sha256
  `970cb6c3...907de8`) and **ENABLED** at modlist line 240 - the first time it
  has been active in this build. Installed with `--replace` over the parked
  3.2.0, transaction `20260903T033733283Z-de1db0b97e86`; modlist backed up to
  `profiles/Default/modlist.txt.bak.v20260902-pre-oar321`. DLL + PDB only, no
  ESP, so active plugins stay at 243. **No rebuild was needed and none was
  done:** the author shipped the fix. OAR 3.2.1's changelog line 1 is
  *"Updated to support runtime 1.7.99+"*, and commit `4d8c0f1b0` repoints
  `extern/CommonLibSSE` from `alandtse/CommonLibVR@539d4ce50` (2025-04-12) to
  `alandtse/CommonLibSSE-NG@fd60ebdfe` (2026-08-29) - past
  `7b47c5a8f` (2026-08-21), the commit that added Address Library format 5.
  Because it is an unmodified vendor release it carries **no `distribution:`
  class** per the `docs/PATCH_INTENTS.md` eligibility ruling; it is a vendor row
  with a source URL and archive hash.
- **Source:** user, 2026-09-02 - *"That right now is a major priority."* #140.
  Full audit: `records/oar-ied-rebuild-2026-09-02.md`.
- **Root cause of #140, now settled:** not OAR's own code. 3.2.0's CommonLib had
  no format-5 reader, so it hit `Unsupported address library format: 5` and
  raised the modal its `MessageBoxW` import provides; the SKSE plugin loop then
  blocked behind that message box forever, which is why the 14 plugins after it
  never loaded and no crash log was written. Proven from the binaries, not
  inferred: **`REL::IDDB::load_v5` and `header_v5_t` are present in the 3.2.1
  DLL's string table and absent from 3.2.0's.** The gate itself now agrees -
  re-run today, the parked 3.2.0 reads `VERDICT: FAIL [addrlib-v5 flag missing
  AND stamp inside reject window]`, where #140 had recorded a PASS for the same
  bytes. 3.2.1: PE stamp 1788193253 (2026-08-31 16:20:53Z),
  `versionIndependenceEx` 1 -> 3 (V5 bit YES), `compatibleVersions`
  1.6.1170.0 -> 1.7.99.0, `VERDICT: PASS`.
- **Verification:** **VERIFIED 2026-09-02 22:39** by
  `records/launch-verify-20260902-223914.md` - main menu 37.4 s, save loaded
  46.1 s, 243 active plugins, 36 SKSE plugins checked, **0 refused**, no crash
  log. Its own launch, not shared, per the Smart Talk (#197) lesson.
  `skse64.log`: `plugin OpenAnimationReplacer.dll (00000001
  OpenAnimationReplacer 03020010) loaded correctly (handle 16)`.
  `OpenAnimationReplacer.log` (which #140 never got far enough to write):
  `v3-2-1-0`, ini created, condition and function factories initialised,
  `Directory cache complete: 1 OAR directories, 164 animation hashes (3880ms)`,
  replacer-mod parse finished; **no** `Unsupported address library format` line.
  Untested: any actual replacer animation - none is installed yet (`1 OAR
  directories` is the plugin's own), so this proves the framework loads, not
  that a given animation mod behaves.

## 2026-09-02 22:39 - IED stays PARKED: the #94 blocker re-tested and still holds

- **What:** No change to [`Immersive Equipment Displays`](https://www.nexusmods.com/skyrimspecialedition/mods/62001) - it remains disabled at
  modlist line 165 and has never been active in this build, so the user's report
  that IED is not working is correct. **Nothing was installed and no overlay was
  attempted.** Update sweep: the newest Nexus file is still 1.7.4 from
  2023-12-10 (both `MAIN` files, 450464/450465, that date; no beta, optional,
  update or hotfix in any category). `SlavicPotato/ied-dev` `master` is alive at
  `d8e9d33` (2026-03-05) with **16 commits** post-dating the 1.7.4 upload
  (NPC mount tracking, conditional variable fixes, an inventory mode for
  variables), but it has no releases, no CI workflows and no submodules, so
  nothing there is buildable by anyone but the author.
- **Source:** user, 2026-09-02 - *"I also don't seem to have IED working."* #94.
  Full audit: `records/oar-ied-rebuild-2026-09-02.md`.
- **Why the rebuild is still impossible, counted fresh:** the vcxproj expects a
  sibling `sse-build-resources\` on every include path.
  `SlavicPotato/sse-build-resources` is 404. The tree `#include`s **74** distinct
  `ext/*.h`; our own already-extended fork `Ensrick/sse-build-resources`
  (`ensrick/1.7.99-format5`, a fork of the clayne 2022-02-12 mirror) has 58, so
  **51 are missing** - independently reproducing #94's number. 37 of them are
  reverse-engineered game-structure headers (`TES.h`, `Sky.h`,
  `ShadowSceneNode.h`, `BSAnimationGraphManager.h`, `hkaSkeleton.h`,
  `ImageSpaceManager.h`, ...) and 14 are the author's `stl_*` container layer.
  **New this pass:** Software Heritage was searched and does not have the
  repository either - the original origin was never archived (`NotFoundExc`),
  and all four archived forks resolve to snapshots at or before 2022-02-12
  (`pcbeard`'s is *older*, revision `3f24c03ce`, 2021-02-21). There is no copy
  left to find. Licence is **MIT (c) 2022 SlavicPotato**, so a rebuild would
  have been permitted and **distributable**; the licence is not the obstacle.
- **Why the withdrawn overlay is not a fallback:** setting
  `kVersionIndependentEx_AddressLibraryV5` is a declaration to SKSE's loader, not
  an implementation. It gets `SKSEPlugin_Load` running, which calls
  `CreateTrampolines` *before* IED's bundled `versiondb.h Load(2, ...)` fails on
  the format-5 file. SKSE then `FreeLibrary`s the plugin, the static
  `BranchTrampoline` destructor `VirtualFree`s a pool slice it does not own,
  Windows page-rounds the address and releases SKSE's whole shared 64 KB pool,
  and SKSE takes an AV writing its own core hooks about a second later
  (`records/upstream-issues/sse-build-resources-trampoline-setbase-free.md`,
  field crash `crash-2026-08-25-20-36-52.log`). That trades a clean refusal for
  taking SKSE down mid-session; it stays withdrawn.
- **Alternative, scoped not installed:** [`Simple Dual Sheath`](https://www.nexusmods.com/skyrimspecialedition/mods/50049) 1.5.9 (50049,
  already enabled and verified) covers unequipped left-hand weapon, shield and
  staff visibility. The only DLL-free route to IED's distinguishing feature
  (arbitrary items on arbitrary skeleton nodes, per actor) is
  [`All Geared Up Derivative SE - AllGUD`](https://www.nexusmods.com/skyrimspecialedition/mods/28833) (Nexus 28833, Kriffin 1.5.6) - Papyrus +
  skeleton + xEdit-generated meshes, no SKSE plugin, so the runtime is
  irrelevant to it; but it was last updated 2020-03-22 and needs a mesh
  generation pass over the whole installed gear set. Recommend it be scoped as
  its own piece of work, not bolted on.
- **Verification:** **n/a - no change to verify.** IED is inert while disabled;
  the 22:39 launch above covers the profile it sits in.
- **Unpark trigger:** an author release against a format-5 CommonLib, or
  `sse-build-resources` reappearing publicly at a 2023-or-later revision, or the
  author publishing `ext/` in any form.

## 2026-09-02 22:21 - Better Jumping SE 1.9.4 installed and ENABLED (Nexus 18967)

- **What:** `Better Jumping SE` 1.9.4 (Nexus 18967, file 796897 "Better Jumping
  NG"), DLL only - `SKSE/Plugins/BetterJumpingSE.dll` + its ini, no ESP, so
  active plugins stay at 243. Adds jump-while-sprinting plus a jump height
  multiplier and configurable multi-jump. Transaction
  `20260903T032143009Z-e6580748a488`. Nothing supersedes it: the alternatives
  are animation layers (Jump Behavior Overhaul 36889, Subtle Jump 38497, Dova
  Jump 125550, Run Sprint and Jump 15881) or a different mechanic (Movement
  Behavior Overhaul 38950, sprint stopping). 14 of 19 lists in
  `docs/ECOSYSTEM-SURVEY-2026-08-30.md` ship it, and it is on that survey's
  "SKSE fix set every list carries and this build lacks" list.
- **Source:** user, 2026-09-02 - *"I was wondering about the mod Better
  Jumping... unless there's a more comprehensive mod that covers movement"*,
  then *"Add Better Jumping"*.
- **Gate detail worth keeping:** `audit/skse_version_data.py` reads `VERDICT:
  PASS (version independent)`, but the load-bearing receipt is the **PE stamp,
  2026-08-29** - eight days AFTER CommonLibSSE-NG gained Address Library
  format 5 support on 2026-08-21. Smart Talk (#197) passed the identical gate
  with a PE stamp of 2025-12-22, eight months before format 5, and aborted the
  SKSE load. The build date discriminates where the version-independence flag
  does not; check it on every DLL adoption from here.
- **Verification:** **VERIFIED 2026-09-02 22:23** by
  `records/launch-verify-20260902-222306.md` - main menu 33.9 s, save loaded
  43.2 s, 243 active plugins, 35 SKSE plugins checked, 0 refused. Given #197
  this DLL got its own launch rather than riding on a shared one.

## 2026-09-02 19:05 - Smart Talk PARKED: it aborted the SKSE load; Better Dialogue Controls verified

- **What:** `SmartTalk.dll` killed the game at startup. `skse64.log` stops dead
  at plugin 28 of 36 with `SUPPRESSED PLUGIN UI [SmartTalk.dll]:
  REL/ID.h(223): failed to open address library file`, and the five plugins
  behind it never loaded. `versionlib-1-7-104-0.bin` IS present in the
  `Address Library` mod, so the file is not missing - SmartTalk's CommonLib
  cannot open it. Both `Smart Talk` and `Smart Talk - MCM Menu` disabled,
  `Smart Talk - MCM.esp` deactivated (transaction
  `20260903T000453920Z-e4b3b23dc78c`), both ledger rows marked
  `enabled: false` with the unpark trigger. Modlist backed up to
  `profiles/Default/modlist.txt.bak.v20260902-smarttalk`. Active plugins
  244 -> 243. **Better Dialogue Controls (1429) is untouched and stays
  enabled** - it is a pure SWF with no native code and had nothing to do with
  this.
- **Source:** user, 2026-09-02 - *"I hit play and it's not playing"*. Root cause
  found in `skse64.log`, not guessed. This session installed Smart Talk on a
  `audit/skse_version_data.py` `VERDICT: PASS (version independent)` and said at
  the time that the gate is necessary and never sufficient (#140, Open Animation
  Replacer passed the same gate and hung the load) - then installed it anyway
  into a build that already had three unverified batches stacked, so the user's
  first launch had four batches to bisect instead of one. The doctrine was right
  and was not followed.
- **Verification:** **VERIFIED 2026-09-02 19:06** by
  `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded
  46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That
  PASS also clears the whole backlog it was blocking: the eight cloak entries,
  Run For Your Lives 4.0.7, Better Dialogue Controls, and Sol's Weapon Speed
  Balance and Conditional Arrow Embedding. Immersive Armors and Immersive
  Weapons stay UNVERIFIED - they are installed disabled and inert, so no launch
  can cover them.
- **Unpark trigger:** an author rebuild of Smart Talk against format-5
  CommonLibSSE-NG, or our own rebuild from source if it is published - the same
  route that worked for Light Placer and Seasonal Clothing Framework.

## 2026-09-02 18:40 - RMB SPCH - Pelts o Plenty 1.1.0 installed and ENABLED (Claude, #95)

- **What:** `RMB SPCH - Pelts o Plenty` 1.1.0 (Nexus 179354, file 749409,
  `179354-749409.zip`, 0.01 MB, sha256 `9c6a59d3...8ca71`) installed at mod
  priority line 2 and enabled; `RMB SPCH - Pelt Cloaks.esp` active at position
  243, after its master `Pelt Cloaks.esp` at 242. FOMOD plan
  `records/fomod-plans/179354-rmb-spch-pelts-o-plenty.json`: core plus the
  shared SkyPatcher configs. It is a **patch, not a replacement** - 75 new
  leveled-item records, zero overrides. Its two `00 - Shared` configs are
  byte-identical to the ones RMB SPCH - Cloaks of Skyrim ships and are inert
  while RMB SPIDified - Sons of Skyrim (#195) is held.
- **Source:** user, 2026-09-02, *"Yeah, go ahead, and install"*, on the stack in
  `records/cloak-layer-audit-2026-09-02.md`. Install record
  `records/cloak-install-2026-09-02.md`.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:40 - Pelts 'o' Plenty 4.3.1 installed and ENABLED; Survival Fix 164077 rejected (Claude, #95)

- **What:** `Pelts o Plenty - Fur Pelt Gear` 4.3.1 (Nexus 120726, file 704702,
  `120726-704702.zip`, 705.81 MB, sha256 `cd48e207...95e1a1`) installed at mod
  priority line 3 and enabled; `Pelt Cloaks.esp` (ESL-flagged) active at 242.
  Fur-slot winner settled by the user the same day - *"I don't like the fake fur
  from winter is coming"* - so Winter Is Coming 4933 and RMB SPCH 116029 are out
  of the plan. 109 cloaks on biped slot 57, 10 hoods on slot 31, ships its own
  HDT-SMP configs. **The companion Survival Fix 164077 was deliberately NOT
  installed:** read against the base plugin (both 419 records) its only record
  additions are the Frostfall keywords `FrostfallIsCloakFur` and
  `FrostfallEnableKeywordProtection` - Frostfall is not in this build - and it
  rewrites `FirstPersonFlags` from `134217728` to `65536`, moving every cloak
  from slot 57 onto Cloaks of Skyrim's slot 46. Base Pelts already carries
  `Survival_ArmorWarm` + `ClothingBody`, the warm tier, so there was nothing to
  fix. Reported on #189.
- **Source:** user authorisation as above; the 164077 check was requested in the
  install brief. Evidence in `records/cloak-install-2026-09-02.md` §2.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:40 - More Scarves 1.4.0 installed and ENABLED (Claude, #95)

- **What:** `More Scarves` 1.4.0 (Nexus 149259, file 723968,
  `149259-723968.7z`, 95.6 MB, sha256 `9b909da4...cc2c35`) installed at mod
  priority line 4 and enabled; `moe-scarves.esl` active at 241. FOMOD plan
  `records/fomod-plans/149259-more-scarves.json`: `__main` + `_HIMBO` +
  `_VanillaF` + `__loweredHood`; `_3BA` and `_BHUNP` omitted because this build
  has no 3BA, BHUNP or OBody. 12 items - 3 hooded capes on slots 31/41/42/43/45
  and 9 scarves on 45. Two loose ends, both tracked: the female meshes are the
  vanilla shape and owe a BodySlide build against the installed CBBE Curvy
  preset (#196), and the `__loweredHood` Dynamic Armor Variants configs plus the
  `HT_ArmorHood` KID rule are installed but inert because Helmet Toggle 2 is not
  in this build.
- **Source:** user authorisation as above. Install record
  `records/cloak-install-2026-09-02.md`.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:40 - RMB SPCH - Cloaks of Skyrim 1.5.3 installed and ENABLED (Claude, #95)

- **What:** `RMB SPCH - Cloaks of Skyrim` 1.5.3 (Nexus 116030, file 749413,
  `116030-749413.zip`, 0.03 MB, sha256 `6b7e6d86...037e88`) installed at mod
  priority line 5 and enabled; `Cloaks - RMB SPCH.esp` (ESL-flagged) active at
  240, after `RMB SPID - Core Definitions.esp` at 26. This is the **record layer
  for Cloaks of Skyrim** and replaces its 2017 plugin: 294 records, all new,
  zero overrides, against `Cloaks.esp`'s 136 vanilla overrides. FOMOD plan
  `records/fomod-plans/116030-rmb-spch-cloaks-of-skyrim.json` - `00 Core` +
  `00 Shared` + `01 Tweaks - Generic` taken, the last because it clears the
  slot-40 tail flag base CoS sets on 339 of 366 items and removes the wrong
  `ClothingNecklace` keyword; `Disallow Enchanting` and `Weaker Enchants`
  omitted pending the open enchantability decision, `Names` omitted as an
  unrequested cosmetic rename, `Description Framework` omitted with its required
  mod absent. Known vendor defect carried in: its SkyPatcher npc config assigns
  the ten unique cloaks with form IDs that do not exist, so they are no-ops
  until #187.
- **Source:** user authorisation as above. Install record
  `records/cloak-install-2026-09-02.md` §3.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:39 - Cloaks of Skyrim Retextured Female Mesh Patch installed (Claude, #95)

- **What:** `Cloaks of Skyrim Retextured - Female Mesh Patch` 1.0.0 (Nexus
  85932, file 363920, `85932-363920.7z`, 0.05 MB, sha256 `2e2a264f...12a898`)
  installed at mod priority line 6, no plugin. 48 female hold-cloak meshes using
  ElSopa's texture names, user version 100, no SMP string. Wins 48 files over
  Cloaks of Skyrim and 46 over the ElSopa mesh update, which is the intended
  order.
- **Source:** user authorisation as above; listed as optional-but-take in
  `records/cloak-layer-audit-2026-09-02.md` §7.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:39 - ElSopa CoS Retextured Mesh Update 1.2 installed (Claude, #95)

- **What:** `ElSopa - Cloaks of Skyrim Retextured Mesh Update 1.2` (Nexus 42558,
  file 263634, `42558-263634.7z`, 0.32 MB, sha256 `df8822b5...c251f6`) installed
  at mod priority line 7, no plugin. **Mandatory, not optional:** its 394 NIFs
  are the Special Edition conversion (user version 100, `BSTriShape`) of the 394
  Oldrim meshes (user version 83, `NiTriShape`) that ship inside ElSopa's MAIN
  archives, and they are also what bind his 141 renamed texture paths. Wins 348
  mesh files over Cloaks of Skyrim; the other 46 go to the female patch above.
- **Source:** user authorisation as above. Evidence in
  `records/cloak-layer-audit-2026-09-02.md` §7.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:39 - ElSopa CoS Retextured 2K installed, textures only (Claude, #95)

- **What:** `ElSopa - Cloaks of Skyrim Retextured 2K` (Nexus 42558, file 170809,
  `42558-170809.7z`, 191.12 MB, sha256 `5200f9ea...9d6cab`) installed at mod
  priority line 8, no plugin, **172 textures and zero meshes**: FOMOD plan
  `records/fomod-plans/42558-elsopa-cos-retextured-2k.json` omits the archive's
  394 Oldrim meshes so no LE mesh exists in the tree even if the mesh update is
  later disabled. 2k tier chosen by measurement - the tiers read x0.99-x1.01
  against each other at every shared pixel size, base CoS UVs are 1024 so
  source-plus-one-step caps at 2048, and the 4k tier (2,130 MB) is the only one
  shipping files with no mip chain. It overrides only 30 of Cloaks of Skyrim's
  137 textures by path because ElSopa renamed the set; 101 base textures stay on
  disk referenced by no surviving mesh.
- **Source:** user, 2026-09-02, on this candidate: *"I think this looks really
  good."* Measurement in `records/cloak-layer-audit-2026-09-02.md` §7.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 18:39 - Cloaks of Skyrim 1.2.1 installed as an ASSET SOURCE, no plugin (Claude, #95)

- **What:** `Cloaks of Skyrim` 1.2.1 (Nexus 6369, file 18422, `6369-18422.rar`,
  75.63 MB, sha256 `03ef0b31...5cbab9`) installed at mod priority line 9 with
  **469 meshes, 137 textures and none of its eight ESPs**. FOMOD plan
  `records/fomod-plans/6369-cloaks-of-skyrim-assets-only.json` omits all three
  plugin option folders, so no Cloaks ESP exists in the tree to be enabled by
  accident - stronger than a `disabledPlugins` marker, and `plugins: []` in the
  ledger keeps `--verify` honest. Reason: `Cloaks.esp` writes 136 vanilla
  overrides (68 CELL, 47 OTFT, 10 NPC_, 4 WRLD) and 24 of its 62
  Outfit/Npc/LeveledItem overrides are already written live, 16 of them by
  `NW_Sons_of_Skyrim.esp`. The records come from `Cloaks - RMB SPCH.esp`
  instead. Its textures are superseded by ElSopa for the 101 of 137 files that
  mod replaces; the 36 dragon-priest meshes and 15 dragon-priest textures are
  still served from here because nothing else covers them.
- **Source:** user, 2026-09-02, *"Yeah, go ahead, and install"*. Evidence in
  `records/cloak-layer-audit-2026-09-02.md` §1-2, install record
  `records/cloak-install-2026-09-02.md`.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 17:55 - ElSopa CoS Retextured 42558 measured; enters the plan at 2k (Claude, #95)

- **What:** `records/cloak-layer-audit-2026-09-02.md` gains section 7. The user
  brought Cloaks Of Skyrim Retextured SE `42558` (ElSopa, v1.2) - *"I think this
  looks really good"* - as the direct test of the earlier finding that base CoS's
  pixels were fine and its rig was what aged. All four tiers plus the Mesh Update
  1.2 and the community female mesh patch `85932` were fetched to the download
  cache and extracted outside `mods`; nothing installed, no profile file touched,
  no launch. Because ElSopa renamed every texture, filename matching fails, so
  the pairing was taken from the meshes (one NIF's `BSShaderTextureSet` in each
  set names the same surface), giving **104 true base-to-ElSopa pairs** and a
  real replacer comparison rather than the cross-asset one used for the other
  candidates. Results: **x1.18 / x1.16 / x1.18 median hf** for the 1k / 2k / 4k
  tiers against the base texture each replaces in the 512-128 px band, with
  40-42 of 104 files still below x1.00; detail index **3.55 against base CoS's
  1.96**; 64 normal maps against base CoS's 8. **Tier decision: 2k, file
  `170809`** - tier-versus-tier is x0.99-x1.01 at every shared pixel size
  including 4k@2048 against the 2k tier's own top mip, base CoS UVs are 1024 so
  source-plus-one-step caps at 2048, the footprints are 34 / 138 / 538 / **2,130**
  MB, and the 4k tier is the only one shipping mip-less files (3 of 172).
  **Two structural findings.** (1) The Mesh Update 1.2 (`263634`) is mandatory,
  not optional: the 2020 MAIN archives ship **394 Oldrim-format meshes** (NIF
  user version 83, `NiTriShape`) and the update is their Special Edition
  conversion (user version 100, `BSTriShape`). (2) That update replaces **381 of
  Artesian `17416`'s 391 NIFs**, carries no HDT-SMP string, and binds ElSopa's
  141 renamed texture paths (169 of 169 resolve inside his own archive, 0 fall
  back to base CoS), so **ElSopa and Artesian are mutually exclusive as
  shipped** - whichever loads later wins outright. New job #193, an owned NIF
  texture-path port, class `recipe`. Adopting `42558` also shrinks #188: it
  retires 101 of base CoS's 137 textures, including **18 of the 19 no-mip and 38
  of the 46 uncompressed**, leaving 1 + 8 plus Pelts 'o' Plenty's 54.
  Cross-checked: neither ElSopa nor Artesian touches the 36 dragon-priest meshes
  or 15 dragon-priest textures, which section 1 measured as base CoS's best
  files.
- **Source:** team-lead task of 2026-09-02 relaying the user's candidate and his
  settled fur call (*"I don't like the fake fur from winter is coming"* - Pelts
  'o' Plenty wins, Winter Is Coming `4933` and RMB SPCH `116029` out). Tracker
  #95; verdict comment posted there and a scope-reduction comment on #188.
- **Verification:** **n/a** - nothing installed, enabled or configured, so no
  verification launch is owed. The ElSopa/Artesian overwrite behaviour and the
  4096 px level of the 4k tier are both marked `[unverified]` in the record.

## 2026-09-02 17:37 - EVG installed parked; Simple Combat Injuries 2.1 held (#33, #140)

- **What:** `EVG Conditional Idles` 1.51 (Nexus 34006, file 506946, SHA-256
  `657c6edcf3a2ab5e249278ab86b2a6fc15c5e0433211f6d7149306c0fa47fb61`)
  installed from a deterministic Core Modules FOMOD plan, then immediately
  parked. Its static audit found only 35 new records, no vanilla overrides,
  valid OAR/MCM JSON and supplied Papyrus source. It cannot function until
  Open Animation Replacer 3.2.0's load hang is resolved under #140, so both
  mod and plugin remain disabled. The stale plugin checkmark created during
  installation was cleared in MO2 transaction
  `20260902T223846040Z-5b38f180e7ad`; `install_mod --verify` then returned zero
  problems. Keep was queued through the curator relay and Keep coverage passed.
- **What:** `Simple Combat Injuries` 2.1 (Nexus 104843, file 749266, SHA-256
  `98ea4e1f3bdf98ce49a3af4281a329c63d3a75f67225e95c3924d89a61842e46`)
  received a full archive/plugin audit but was **not installed**. It is a clean,
  ESL-flagged, mostly record-driven implementation with no native DLL or
  vanilla overrides, but its hard-coded high injury rates, stackable NPC bleed,
  incomplete animation coverage and concussion blur/double-vision violate this
  build's design constraints. Full evidence is in
  `records/simple-combat-injuries-2.1-audit-2026-09-02.md`.
- **Source:** user, 2026-09-02 - *"EVG conditional idles it is for now. Look at
  simple combat injuries and see if it's a quality creation."* Issues #33 and
  #140.
- **Verification:** **UNVERIFIED/PARKED** for EVG; no launch can prove its
  behaviour while OAR is disabled. **N/A** for Simple Combat Injuries because
  it was inspected outside the profile and not installed. Spriggit round-trip
  passed.

## 2026-09-02 14:17 - Cloak layer audited; nothing installed (Claude, #95)

- **What:** `records/cloak-layer-audit-2026-09-02.md` added (research only, no
  build-state change). Audited Cloaks of Skyrim 6369, RMB SPCH 116030 1.5.3,
  Artesian Cloaks **17416** - the id 115097 that had been circulating for it is
  Immersive Equipping Animations (PTBR), a different mod - Cloaks of Skyrim HD
  SSE PBR 178993, More
  Scarves 149259, Bocksten 138180, Pelts 'o' Plenty 120726 and Winter Is Coming
  4933. Nine archives fetched to the MO2 download/audit cache and extracted to
  sibling `x*` directories; nothing entered the `mods` tree, no profile file was
  touched, no curator state changed, and the game was never launched. Headline
  measurements: distance detail (`audit/mip_retention.py`, n=10 diffuse maps per
  mod, matched pixel size against three vanilla clothing torso diffuses) ranks
  Winter Is Coming x0.94 > Pelts x0.75 > **base Cloaks of Skyrim x0.72** > More
  Scarves x0.46 > Bocksten x0.40 > **CoS HD SSE PBR x0.31**, i.e. the 2026 "HD
  PBR" pack reads 2.3x softer at play distance than the 2017 textures it
  replaces; `Cloaks.esp` writes 136 vanilla overrides (68 CELL, 47 OTFT, 10
  NPC_, 4 WRLD) where `Cloaks - RMB SPCH.esp` writes **zero**; all 366 CoS
  cloaks are rigged to `SkirtBBone01-03` with no SMP config anywhere, which is
  the actual ageing; Artesian's 391 NIFs are direct path replacers, so its ESP
  can be dropped and it coexists with RMB SPCH; FSMP is already bounded at 5
  skeletons / 3 ms / 500 units, so cloak crowd cost is a config question rather
  than a distribution one; Sons of Skyrim already ships 11 slot-46 hold cloaks.
  Six fix-up jobs opened as #187-#192, each classed per `docs/PATCH_INTENTS.md`.
- **Source:** team-lead task to work out a modernised cloak layer, from the
  user's words on Cloaks of Skyrim - *"I'm not the biggest fan of how some of
  them look. The mod has aged. Of course, I also need HDT-SMP physics and all
  that... maybe we can find updates and/or fix things up ourselves."* Tracker
  #95; verdict comment posted there.
- **Verification:** **n/a** - nothing was installed, enabled, parked or
  configured, so no verification launch is owed. Every runtime claim in the
  record is marked `[unverified]` and carries an issue.

## 2026-09-02 17:05 - Fur cloak slot settled: Pelts 'o' Plenty, Winter Is Coming out (#95)

- **What:** decision only, nothing installed. The fur slot in the cloak plan
  goes to **Pelts 'o' Plenty 4.3.1** (Nexus 120726). **Winter Is Coming**
  (4933) and its plugin patch **RMB SPCH - Winter is Coming 1.4.6** (116029)
  are out of the plan. The measured gap favoured WIC (hf x0.94 vs x0.75, tone
  x1.01 vs x1.07) and did not decide it - this was shortlist item 2 in
  `records/cloak-layer-audit-2026-09-02.md`, i.e. one of the five calls the
  audit deliberately left to the user's eye. Consequence: Pelts ships **54 of
  its 96 textures with no mip chain at all**, so #188 (mip regeneration) grows
  to cover Pelts alongside the 19 Cloaks of Skyrim textures shipped `mips=1`
  and the 46 uncompressed (~204 MB VRAM). Commented on #188.
- **Source:** user, 2026-09-02 - *"I don't like the fake fur from winter is
  coming. Pelts o Plenty is vastly superior."*
- **Verification:** N/A - a plan decision, no mod installed, no profile or INI
  change, no plugin change.

## 2026-09-02 14:06 - Dialogue controls: Better Dialogue Controls + Smart Talk adopted

- **What:** two mods on different layers, so they stack rather than compete.
  `Better Dialogue Controls` (Nexus 1429, file 11022, v1.2) is the SWF layer -
  the archive holds exactly one file, `Interface\dialoguemenu.swf` (24,551 B),
  no native code and no plugin, so it carries no runtime-version risk. Nothing
  else in the profile touches `dialoguemenu.swf` (`file_conflicts` reports no
  collision), because this build runs SkyUI + UIExtensions + RaceMenu with no
  Edge UI, Nordic UI or Dialogue Interface ReShaped. `Smart Talk` (Nexus
  161500, file 700903, v1.0.5) is the behaviour layer - `SmartTalk.dll` plus
  inis, no SWF at all - adding quest-line highlighting, reorderable options,
  pauses, skip/interrupt and controller support; its `SmartTalk_CustomUI.ini`
  is explicit support for coexisting with a replaced dialogue UI. Its optional
  MCM menu (file 682794, `Smart Talk - MCM.esp`, enabled) went in too because
  MCM Helper is enabled in this profile. Transactions
  `20260902T190555315Z-290d9a9ec2ee`, `...190559016Z-545178fdba58`,
  `...190606299Z-4848e7a531ab`. Gates after install: `install_mod --verify`
  `0 problem(s)`, `verify_order` CLEAN over 240 active plugins.
- **Source:** user, 2026-09-02 - *"Better dialogue controls looks really nice.
  Is that still the latest? 1429?"* then *"Ok, then add both."* 1429 is current:
  v1.2 is its only file and the page has not moved since 2016-11-26, which does
  not matter for a pure SWF. Convenient Dialogue UI (57943) was rejected as the
  alternative: same `dialoguemenu.swf` slot, so either/or, and older (v1.2,
  2021-11-07). Its "AE squeeze fix" (113031) is NOT a mark against it - that is
  a third-party file by GGenX8 whose own page title reads "(Redundant Read
  Desc)".
- **Verification:** **UNVERIFIED** - no launch yet, deliberately: the user asked
  to hold the verification launch while Sol lands their ore mods, so one launch
  will cover this, Run For Your Lives 4.0.7, and Sol's batch together.
  `audit/skse_version_data.py` on `SmartTalk.dll` (PE stamp 2025-12-22)
  reads `VERDICT: PASS (version independent)`, which is **necessary and never
  sufficient** - Open Animation Replacer passed the same gate and hung the load
  (#140), so Smart Talk is not proven until a PASS exists.
- **Open:** the curator Keep for 161500 was queued by `install_mod.py` and the
  relay confirms it served and applied both batches
  (`decisions-applied-20260902-140603.json`, `...-140608.json`), but
  `curator_state` still reads 172 live Keeps without it, so `keep_coverage`
  reports `installed with no Keep: 161500`. 1429's Keep landed normally in the
  same run. Likely a Firefox storage-flush lag rather than a lost decision -
  recheck before the verification launch, and do NOT re-queue blindly.

## 2026-09-02 13:52 - Run For Your Lives 4.0.7 installed and ENABLED (Sol, Nexus 2272)

- **What:** `Run For Your Lives` 4.0.7 (Nexus 2272, file 737640,
  `2272-737640.7z`, 100 KB, sha256 `127a6636...5e88e`) installed at mod
  priority 245 and **enabled**; `run for your lives.esp` is active at LOOT
  position 185. Arthmoor mod, and the author is not on the curator Excluded
  list. Sol's record audit reports **23 new records and zero overrides**, so it
  adds behaviour (townsfolk take cover during dragon and vampire attacks)
  without contesting any existing record - which is why LOOT could place it
  without a conflict decision. FOMOD plan
  `records/fomod-plans/2272-run-for-your-lives.json`. Keep 2272 verified;
  `keep_coverage` still reads clean (246 installed dirs, 171 Nexus ids, 171
  live Keeps, 0 violations) and `install_mod --verify` reads `0 problem(s)`.
- **Source:** installed by Sol (Codex) under their claim, 2026-09-02 13:52;
  ledger and changelog handed to this session per the coordination board.
- **Verification:** **VERIFIED 2026-09-02 19:06** by `records/launch-verify-20260902-190632.md` - main menu 35.3 s, save loaded 46.1 s, 243 active plugins, 0 refused by the SKSE loader, no crash log. That launch covers this whole batch at the launch/load level; per-item in-game behaviour is still untested.
## 2026-09-02 13:39 - Immersive Weapons 2 installed INACTIVE as a vendor source (Sol, #181)

- **What:** `Immersive Weapons` 2 (Nexus 16788, file 52498, `16788-52498.7z`,
  430 MB, sha256 `38ca9781...00e63`) installed at priority 244 and left
  **disabled**; `Immersive Weapons.esp` is inactive and undiscovered. The
  companion intake to Immersive Armors 3479 - both stay parked until the
  item-by-item equipment intake in #181 is done, per
  `docs/EQUIPMENT_INTAKE_POLICY.md`. MO2 transaction
  `20260902T183719292Z-a353c37bcfac`. Ledger row added here with the
  `enabled: false` marker; `install_mod --verify` reads `0 problem(s)`.
  With this row `audit/keep_coverage.py` reads **clean** for the first time
  since the doctrine landed: 245 installed directories, 170 Nexus ids, 40 own
  artifacts, 170 live Keeps, zero violations.
- **Source:** user authorised the adoption 2026-09-02 13:03; installed by Sol
  (Codex) under the `sol/immersive-weapons` claim; ledger and changelog handed
  to this session per the coordination board. Evidence: issue #181 comment
  5514530451 (archive and plugin hashes).
- **Verification:** UNVERIFIED, and inert - the mod is disabled and its plugin
  undiscovered, so it cannot affect a launch. It has had no PASS of its own and
  none of its items has been through equipment intake. Note this landed AFTER
  `records/launch-verify-20260902-133303.md`, so that PASS does not cover it.

## 2026-09-02 13:05 - Azurite III HDR archived out of the mods tree (explicit Skip)

- **What:** `Azurite III HDR` (Nexus 138991) removed from the MO2 instance.
  It was installed, disabled, and carrying an explicit user **Skip**; under the
  doctrine that everything installed must be a Keep, a rejected mod may not sit
  in `mods/`. Removed through MO2 so the `modlist.txt` edit is MO2's own and
  not a text edit: `MO2Headless mod-trash "Azurite III HDR" --yes`
  (transaction `20260902T180539373Z-051a9dd8d89e`) moved the folder to
  `.mo2-headless-trash\20260902T180539373Z-051a9dd8d89e-Azurite III HDR` and
  dropped the modlist line; that directory was then moved to
  `C:\Users\danjo\source\repos\mo2-instances\_archived-rejects\Azurite III HDR`
  (three files: `Azurite III - HDR.esp`, `Azurite III - HDR.ini`, `meta.ini`).
  **No active plugin changed** - the mod was disabled, so
  `Azurite III - HDR.esp` was never in `plugins.txt`. The ledger row for 138991
  is kept for provenance with `archivedUtc` / `archivedTo` and a note; it was
  already `enabled: false` with no plugins, so `install_mod --verify` still
  reads 0 problems. Rollback: move the folder back to
  `mo2-instances\skyrim-se\mods\Azurite III HDR`, then
  `MO2Headless.exe --root <instance> --profile Default mod-disable "Azurite III HDR"`
  to re-register it in its previous disabled state, then clear the two ledger
  fields.
- **Source:** team-lead, 2026-09-02, in the same task as the three adoptions
  below; the Skip and the supersession by Azurite III CS (162153, which bundles
  HDR) are recorded in `records/keep-install-audit-2026-09-02.md` section 2c.
  Full detail and the exact rollback in
  `records/adoption-2357-78772-51874-2026-09-02.md` section 5.
- **Verification:** VERIFIED 2026-09-02 13:33 by
  `records/launch-verify-20260902-133303.md` (main menu 35.0 s, save loaded
  50.3 s, 238 plugins, claim `adopt-2357-78772-51874`). No plugin, INI or
  profile setting changed by this entry, so the launch only had to prove the
  removal broke nothing.

## 2026-09-02 13:05 - Remiel 1.7.6 adopted (Nexus 51874) + hotfix + missing voice lines

- **What:** three mods installed and enabled from Nexus 51874 (Maplespice):
  `Remiel - Dwemer Specialist` (file 748194, v1.7.6, 498.9 MB, sha256
  `34c8591d...65f554`, plugins `HLIORemi.esp` + `HLIZRemiArnima.esp`,
  transaction `20260902T180449161Z-0364dded4535`),
  `Remiel - 1.7.6 Hotfix` (749437, `HLIONameFix.esp`,
  `20260902T180518703Z-5da5e666fcbd`) and `Remiel - Missing Voice Lines`
  (749439, 12 loose `.fuz`, `20260902T180519812Z-3beb4fd35f26`), the last two
  staged above the main mod so they win. FOMOD driven deterministically by
  `records/fomod-plans/51874-remiel.json`: main "Custom Voiced" plus the
  **Beyond Reach Commentary ESPFE** (the FOMOD marks it `Recommended` because
  `arnima.esm` is active). Every other option was excluded by the installer's
  own `fileDependency` rules - LOTD, Thogra, Timelost Dwemer, Lost Races of
  Nirn, Aethernautics, Automaton Glow and Dwemer Spectres all evaluate
  `NotUsable` here; Vanilla Looks, Relax Anywhere and the birthday hat are
  taste options and were not taken. **No DLL, no SKSE plugin, no framework
  requirement** ("None except the DLCs") - the archive is only ESP/BSA/NIF/DDS,
  so 1.7.104 has nothing to reject. **No body or skin refit needed:** she ships
  no body meshes and no skin textures, so she inherits CBBE Curvy + Reverie.
  LOOT placed `HLIORemi.esp` at 65, ahead of the whole Lux stack, which is what
  the audit required: `semantic_record_conflicts Cell HLIORemi.esp` reports 178
  field divergences and the anchor **wins none** - Lux keeps its lighting in
  every interior she touches, including the Silver-Blood Inn and all six
  Nchuand-Zel cells. Her 10 CELL wins are semantically identical to the mods
  they beat. Voice coverage 5,160 of 6,173 INFO (83%) against the same author's
  Varinia at 91%; the single missing facegen is `HLIOYazPlaceHolder`, an
  unreachable placeholder in the mod's own `HLIORemisMarkerRoom` holding cell
  for the Yazakh follower (68568, not installed). One tracked regression: she
  reverts 3DNPC's reposition of `T03MauriceREF` (#182). **Operational rule for
  the user: never import Remiel into NFF** - the author allows NFF to be
  installed (it is required for her Rumarin/Zora/Anum-La banter) but not to
  manage her, and NFF ships no file-level blacklist, so this is an in-game MCM
  discipline (added to #74 alongside Inigo and Varinia).
- **Source:** the user, 2026-09-02 - *"I'd also like to add 51874, the Remiel
  follower. Another excellent mod by Maplespice."* Audit:
  `records/adoption-2357-78772-51874-2026-09-02.md` section 3.
- **Verification:** VERIFIED 2026-09-02 13:33 by
  `records/launch-verify-20260902-133303.md` - main menu **35.0 s**, save loaded
  **50.3 s**, 238 plugins, 0 plugins refused by the SKSE loader, no crash log.
  `launch_triage` shows nothing attributable to Remiel. Post-launch gates
  re-read clean: `install_mod --verify` 0 problems, `verify_order` CLEAN, and
  `preflight` clean with the deliberate INI keys intact. Launch/load level
  only - her quest, her banter and the NFF discipline above are the user's to
  exercise in play.

## 2026-09-02 13:05 - Daedric Shrines - All in One 1.02 adopted, 2K variant (Nexus 78772)

- **What:** `Daedric Shrines - All in One` installed and enabled (file 536019,
  the **2K** package, v1.02, 142.73 MB, sha256 `8c2a3089...cdc042a`, plugin
  `man_DaedricShrines.esp`, transaction `20260902T180442879Z-8056fb24aa73`).
  The 4K package (536018) was rejected on `docs/TEXTURE_POLICY.md`: measured
  vanilla sources are 1024 for Boethiah/Meridia/Azura/Hircine/Malacath/Namira/
  Vaermina/Dagon and 2048 for Clavicus Vile and `mehrunesstatue01`, so 4K would
  put 15 sets two steps above source, while 2K is one step for most of them.
  The **main ESP was kept over the "No map markers" variant** (536023): the two
  carry an identical record set and differ only in 7 `MapMarker` refs, all of
  which have `Flags = "0"` - neither `Visible` nor `CanTravelTo`, i.e. ordinary
  undiscovered-location behaviour you have to explore to find. Its eight
  vanilla/CC mesh replacements are uncontested (a BSA sweep of every enabled mod
  plus the game archives shows the only other provider of each is the game
  itself) and it has 0 loose-file collisions. LOOT placed it at 63: after
  `Nature of the Wild Lands` (44) so its 17 reference edits win - four trees
  plus the Hircine/Namira/Peryite bone and pillar dressing, moved or disabled to
  clear the new statues' footprints - and before the whole Lux stack, so all 59
  semantic divergences after the anchor go to Lux / Lux Orbis CS / Ensrick Lux
  Water CS Patch and none to the shrine mod. Its 12 CELL "wins" over USSEP,
  Landscape and Water Fixes, LFfGM, Lux Orbis and 3DNPC are semantically null -
  the only variance is XCLR region-list ordering, same region set. Wintersun and
  Pilgrim patches not needed (neither mod is installed). Two follow-ups: the
  2K package still ships three 4096 sets (#184) and its statues measure soft at
  mid/far distance (#185); Xtudo's two live patch pages are unevaluated (#186).
- **Source:** the user, 2026-09-02 - *"Adopt those 2"* (with 2357). Audit:
  `records/adoption-2357-78772-51874-2026-09-02.md` section 2. No prior record
  existed; this is the first audit of the page.
- **Verification:** VERIFIED 2026-09-02 13:33 by
  `records/launch-verify-20260902-133303.md` (main menu 35.0 s, save loaded
  50.3 s, 238 plugins, no crash log, nothing in `launch_triage` attributable to
  it). Launch/load level only - how the statues actually sit at the four shrine
  sites where they win reference edits over Nature of the Wild Lands has not
  been seen. Records: `records/active-record-conflicts.json`,
  `records/cell-after-man-daedricshrines-esp.md`,
  `records/active-worldspace-conflicts.json`, `records/active-file-conflicts.json`.

## 2026-09-02 13:05 - Enhanced Blood Textures LITE 1.1 adopted (Nexus 2357)

- **What:** `Enhanced Blood Textures - Lite` installed and enabled (file
  **68999**, v1.1, 11.86 MB, sha256 `50f92930...0b89c87`, plugin
  `dD - Enhanced Blood Main LITE.esp`, transaction
  `20260902T180416816Z-30169f7890b9`), staged through
  `records/fomod-plans/2357-ebt-lite.json` so only the plugin and
  `data/textures` land as game data. The file id is pinned because the page has
  two `MAIN` files and `pick_file` would otherwise take the newer one, which is
  the full 4.0 build the blood audit told us not to choose. The archive audit
  did not contradict `records/blood-visuals-audit-2026-08-30.md` ranked decision
  #2, so Lite went in as directed. **Screen-effect policy held and measured:**
  EBT Lite sets 9 of the 15 `fBloodSplatter*` GMSTs non-zero and loses every one
  of them to `Disable Screen Blood.esp`, which LOOT placed at 122 against EBT's
  33; the one GMST that plugin does not cover, `iBloodSplatterMaxCount`, EBT
  *lowers* from vanilla 25 to 10, so it cannot re-enable anything. The optional
  `dD-No Screen Blood.esp` (64692) was therefore **not** installed - it is a
  strict superset of a plugin already in the order. **Optimised Scripts for EBT
  (76767) does not apply and was not installed:** it replaces five `zblood*.pex`
  files and EBT Lite ships no scripts at all (15 DDS + 1 ESP). Spider Blood Fix
  (114039) likewise does not apply - EBT Lite's 15 `BodyPartData` overrides
  contain no spider record. Total conflict surface across 238 plugins is 10
  FormKeys: the 8 screen-blood GMSTs above plus two Impact records, one an ITM
  and one a real trade - arrow hits use EBT's blade decal instead of its arrow
  decal so that Audio Overhaul and Immersive Sounds keep their sound edits
  (#183). Sanguine Symphony is not installed, so the "never mix" constraint
  holds. Texture measurement is poor and recorded as such (#185).
- **Source:** the user, 2026-09-02 - *"Adopt those 2"*. Prior research:
  `records/blood-visuals-audit-2026-08-30.md`. Audit:
  `records/adoption-2357-78772-51874-2026-09-02.md` section 1. Outcome recorded
  on #90.
- **Verification:** VERIFIED 2026-09-02 13:33 by
  `records/launch-verify-20260902-133303.md` (main menu 35.0 s, save loaded
  50.3 s, 238 plugins, no crash log). Launch/load level only - blood on screen
  during combat has not been seen.

## 2026-09-02 13:00 - Immersive Armors 8.1 installed INACTIVE as a vendor source (Sol, #181)

- **What:** `Immersive Armors` 8.1 (Nexus 3479, file 5924, `3479-5924.7z`,
  1,042 MB, sha256 `1a46ae23...b91f1`) installed at priority 239 and left
  **disabled**; both plugins (`Hothtrooper44_ArmorCompilation.esp`,
  `Hothtrooper44_Armor_Ecksstra.esp`) are inactive and undiscovered. Core FOMOD
  selection only, recorded at `records/fomod-plans/3479-immersive-armors-core.json`;
  the optional UNP body option was omitted because the decided stack is CBBE
  Curvy / HIMBO. It stays parked until the item-by-item equipment intake in #181
  is done, per `docs/EQUIPMENT_INTAKE_POLICY.md`. Nexus Keep queued and applied -
  under the new "Installed implies Keep" doctrine a disabled vendor source still
  carries its Keep. Ledger row added here with the `enabled: false` marker, so
  `install_mod --verify` reads the two inactive plugins as `mod parked` and
  still reports `0 problem(s)`.
- **Source:** user authorised the adoption 2026-09-02 12:56; built and installed
  by Sol (Codex) under the `sol/immersive-armors` claim; ledger and changelog
  handed to this session per the coordination board. Evidence: issue #181 and
  its comment 5514044962 (archive and file hashes).
- **Verification:** UNVERIFIED. The mod is inert (disabled, plugins
  undiscovered), so it cannot affect a launch, but it has had no PASS of its own
  and none of its items has been through equipment intake.

## 2026-09-02 12:45 - Weapon Speed Balance 0.1.0 installed and enabled (Sol, #180)

- **What:** `Ensrick - Weapon Speed Balance` 0.1.0, an Ensrick source-built
  normalizer, installed and **enabled**; `WeaponBalancePatch.esp` is active
  (plugins.txt line 238), sha256 `74532e43...5fa09`. 3,007 audited WEAP
  overrides set to exact class speeds across 35 resolved masters, deterministic
  generation verified by repeated plugin and package SHA-256 equality. No Nexus
  id, so keep coverage exempts it as an own artifact. Ledger row added here.
- **Source:** built and installed by Sol (Codex) under the
  `sol/weapon-balance` claim, 2026-09-02 12:45. Commits `449101d`, `1ad6299`;
  PR #179; tracker #180.
- **Verification:** UNVERIFIED at time of writing - it is active and therefore
  DOES affect the next launch. It will be covered by the adoption batch's
  verification launch (Enhanced Blood Textures / Daedric Shrines AIO / Remiel /
  Azurite archive), which means a FAILED launch has a five-change bisect space
  across two owners. Named on the coordination board so the PASS records what it
  covers.

## 2026-09-02 12:55 - Doctrine: installed implies Keep, enforced by a preflight gate

- **What:** the Keep definition changed from "installed **and enabled**" to
  **"installed"**, and adding the Keep became a required step of installing
  rather than a follow-up. Three artifacts: (1) `docs/CURATION_POLICY.md`
  rewritten - new "Installed implies Keep" section with the two corollaries,
  a Skip must not be installed (move it to `mo2-instances\_archived-rejects`,
  never delete) and our own id-less artifacts are exempt; (2) new gate
  `audit/keep_coverage.py`, wired into `audit/preflight.py`, blocking on
  installed-with-no-Keep, Keep-with-nothing-installed, and Skip-is-installed -
  a Keep already sitting in the relay spool downgrades to a WARN because the
  extension applies it on the next Nexus page load and we cannot force that;
  (3) `audit/install_mod.py` now queues the Keep into the relay spool itself at
  the end of every successful install, so the step cannot be forgotten.
  Keeps were also queued for the 14 installed-but-disabled mods the old
  definition had excluded (7 CS feature pages, 5 parked rebuild candidates,
  98175, 126683); the relay served both batches, live Keeps 148 -> 167.
  The gate now reports exactly 3 violations, all owned by the adoption batch in
  flight: 2357 and 78772 kept but not installed, 138991 Azurite III HDR skipped
  but installed.
- **Source:** user, 2026-09-02 - *"make sure everything in keeps is installed
  (not necissarily active) and everything installed is in keeps"* and *"Make
  sure that our processes and proceedures doctrine makes adding to keeps
  necessary for installed mods."* Audit that found the gap:
  `records/keep-install-audit-2026-09-02.md`. Memory:
  `feedback_skyrim_installed_implies_keep`.
- **Verification:** N/A for build state - no mod installed, disabled, removed
  or reordered, no profile or INI change. Tooling verified by running the gate
  (`3 keep-coverage violation(s)`, exit 1) and `audit/preflight.py`, which now
  reports the same three as blocking.

## 2026-09-02 12:25 - Keep list vs installed audit: 2 un-actioned adoptions, 5 Keep gaps queued

- **What:** read-only reconciliation of the live Nexus curator state against
  every directory in `mo2-instances/skyrim-se/mods/` (installed, not merely
  enabled). 238 installed directories / 166 Nexus ids / 148 live Keeps.
  Result: **2 Keeps with nothing installed** - Enhanced Blood Textures (2357,
  kept 09-01 01:14Z) and Daedric Shrines AIO (78772, kept 08-31 21:44Z), both
  the user's own mid-browse adoptions that never went through
  audit -> install, so neither was cleared. **20 installed ids with no Keep** -
  5 of them installed AND enabled (26138 Skyrim Landscape and Water Fixes,
  49616 USMP SE, 65070 Misc Effects ENB Light, 92948 Media Keys Fix SKSE,
  175362 Dyn FNIS AA functions), queued as a guarded keep batch; the other 15
  are deliberately disabled (7 CS feature pages superseded by the AIO source
  build, 5 parked for a 1.7.104 rebuild or a silent author, 98175 replaced by
  `Ensrick - Scoped Werewolf Totem Skull 98175`, 126683 parked on a waterfall
  overlap check) plus 138991 Azurite III HDR which is an explicit Skip. No
  installed directory is missing from `modlist.txt`; the 39 id-less directories
  are all Ensrick overlays, native rebuilds, or harness mods.
- **Source:** user, 2026-09-02 - *"make sure everything in keeps is installed
  (not necissarily active) and everything installed is in keeps"*. Record:
  `records/keep-install-audit-2026-09-02.md`. Controller:
  `nexus-local-curator/scripts/reconcile-installed-keeps.py` (plan only) plus an
  installed-based variant; batch written to the relay spool `decisions-pending.json`
  behind the compare-before-write guard, relay started on 127.0.0.1:38492.
- **Verification:** N/A - curation-only, no mod installed, disabled, removed or
  reordered, no profile or INI touched, no plugin change. The 5 queued Keeps
  apply on the extension's next Nexus page load.

## 2026-09-02 10:06 - #165/#166 restore: decided skins on top + vanilla `_sk` soft-light overlay (both reversible)

- **What:** Under claim `skin-face-diagnosis-2` (no game or MO2 process; the
  user's 09:34-10:05 session had ended), MO2Headless `mod-priority`: (1)
  `SkySight Skins` 10 -> directly above `The New Gentleman` (now 13 vs 12,
  transaction `20260902T150554430Z-ad9da584547b`); (2) `Reverie - Skin` 9 ->
  directly above `CBBE` (now 90 vs 89, `20260902T150554563Z-2186a81b488a`).
  Enabled flags of all 315 rows unchanged; `modlist.txt` backed up to
  `modlist.txt.bak.v20260902-100554-preskinreorder`. One deviation from
  "priority only": SkySight ships 22 meshes (malefeet_0/1 + 18 open-toed
  footwear from its forced RequiredHighPolyFeet option) that lost to
  HIMBO/TNG/HIMBO Refits/Lords of the Reach before the move and would have
  flipped 18 HIMBO-shaped footwear meshes to vanilla shape after it, so
  `mods\SkySight Skins\meshes` is renamed `meshes.mohidden` - a deliberate
  hide, approved by team-lead 2026-09-02; rollback = rename back. No mesh
  changes hands, texture-only effect. (3) New mod `Ensrick -
  Vanilla Skin Soft-Light Maps` (MO2Headless `mod-stage`, transaction
  `20260902T150554695Z-a8bcf3daafe6`, priority 237 = top row, enabled): the
  six vanilla `_sk` maps (`femalehead/femalebody_1/femalehands_1`,
  `malehead/malebody_1/malehands_1`) byte-copied from `Skyrim - Textures0.bsa`
  by `overlays/ensrick-vanilla-skin-soft-light-maps/build.py` (pinned entry
  hashes, refuses on mismatch; zip SHA-256 E7C01E72...C9E, 214,061 B),
  because Reverie and TNG replace all six with 4x4 black stubs and CBBE's
  are near-black, which zeroes the vanilla soft-light wrap (CS
  `Common/LightingEval.hlsli:119`). Installed files re-hashed 6/6. Ledger:
  overlay row `distribution: recipe` (vanilla bytes, never bundled) + notes
  on the CBBE / Reverie / TNG / SkySight rows. Resulting winners
  (`resolve_winners` after): every female head/body/hands map = Reverie,
  every male map = SkySight, every `_sk` = the overlay; `install_mod --verify`
  0 problems, `verify_order` CLEAN, preflight clean (3 warnings: Steam
  overlay unverifiable, saves mirrored, and the overlay's ledger row, which
  now exists). A/B for the user: disable `Ensrick - Vanilla Skin Soft-Light
  Maps` alone to see the stubs' look; rollback of the moves = the two
  transactions or the modlist backup.
- **Source:** team-lead ruling 2026-09-02 on #165/#166 (mechanical restore
  of BASELINE.md:184-186 skin decisions + vanilla `_sk` overlay); records
  `records/face-eye-makeup-audit-2026-09-02.md`,
  `records/skin-distance-detail-audit-2026-09-02.md`.
- **Verification:** VERIFIED 2026-09-02 10:07 by
  `records/launch-verify-20260902-100735.md` (main menu 31.4 s, save loaded
  41.7 s, 232 plugins, claim skin-face-diagnosis-2). Launch/load level only;
  the in-game look (soft-light wrap back, Reverie/SkySight skins) is the
  user's A/B, not yet seen.

## 2026-09-02 09:50 - #165/#166 diagnosis: face makeup source + distance-detail metric (tooling only, no build change)

- **What:** (1) `audit/mip_retention.py` (new, sibling of `inspect_mod.py`):
  decodes a DDS mip chain as shipped, reports RMS-Laplacian high-frequency
  energy and tonal std per mip, compares against the vanilla texture at the
  same pixel size, and `--resharpen` regenerates a Lanczos + unsharp chain
  through texconv (the recipe form). Bytes-input path fixed (texconv refused
  an input inside its own `-o`). (2) `inspect_mod.py` runs that check on up
  to 12 sampled diffuse/normal/specular maps >= 1024 px and flags
  `soft-at-distance` under `DISTANCE_HF_FLOOR = 0.70`; `--mip=N` / `--mip=0`
  control it. (3) `audit/README.md` documents both. (4) Records:
  `records/face-eye-makeup-audit-2026-09-02.md` (#165: ring = Bethesda's
  baked facetint, rendered harsh because CBBE/TNG `_sk` maps zero the
  soft-light wrap) and `records/skin-distance-detail-audit-2026-09-02.md`
  (#166: winner-vs-vanilla mid/far ratios, resharpen test, candidate
  shortlist with permissions). No mod, INI, priority or overlay changed.
- **Source:** user 2026-09-02 (#165 "dark makeup around the eyes", #166
  "matte and single-tone from a distance"); team-lead dispatch; CS 1.8
  shader source `_rebuild_CommunityShaders/package/Shaders/Lighting.hlsl`.
- **Verification:** n/a - build state untouched, so no launch. Tooling
  smoke: `mip_retention` bytes path decoded CBBE `femalehead.dds` vs vanilla
  (hf x0.48 at 512-128 px) through the exact `inspect_mod` call sequence.

## 2026-09-02 09:36 - #160 packaging: vendorBytesAllowed ruling applied, six recipe gaps closed, collection built clean

- **What:** (1) Lead ruling implemented in `tools/package_ensrick.py`: a
  ledger row may carry `vendorBytesAllowed: {basis, files}`; a vendor-hash
  match on a listed file passes (manifest `allowedVendorFiles`, README
  section "Vendor bytes shipped under licence") only when the basis names a
  permissive licence (MIT/BSD/Apache/CC-BY/CC-BY-SA) or quotes a Nexus
  permission granting upload of modified files; anything else stays a
  violation. Set on `Light Placer - Ensrick 1.7.104` for
  `po3_LightPlacer.ini`, `Scripts/LightPlacer.pex`,
  `Source/Scripts/LightPlacer.psc` (MIT, `LightPlacer-LICENSE.txt` ships;
  the parked vendor Light Placer is NOT a required download).
  `Ensrick - Media Keys Fix Configuration` got its `distributionBasis` (own
  INI overlay, no vendor bytes). (2) Six recipe gaps closed from existing
  records, no re-runs on the instance: Better Fur refit and Werewolf Totem
  98175 records now carry the full per-mesh `nif-port-cli clone-shape` /
  `remap-textures` invocations (pins c63f74e / e12079c) plus the 8 verbatim
  texture copies, and both were reproduced byte-identically into the
  scratchpad with the pinned binary (4/4 and 1/1); CRF Semantic Patch record
  gained the generator pin (this repo, commit 19875a9), the nine
  master-plugin input hashes and the reconstructed `run-patcher` command
  (exact 2026-08-30 argument line was never captured, same as Collectibles
  Helper); Varinia got a `recipe` field (new `tool` kind: Caprica 0.3.0
  commit + exe hash, per-fragment vendor PSC hash from the BSA, restored
  declarations, command, PEX hash); VHR SMP NPC Compatibility got a `script`
  recipe (build.py + modasset.py pins, both BSA hashes, all 32 input/output
  hashes recomputed from the BSAs and matching the installed overlay);
  Pandora Output got a `tool` recipe (headless exe 6adf04b + hash, input
  aggregates for Pandora_Engine templates, the sppffp/sppftp VFS view and
  the XPMSSE animations folder, vendor archive hashes, SHA-256 of all 205
  payload outputs = 171 hkx + 2 singlefile txt + 32 json; not re-run, hashes
  hold for that input set only). Packager also learned the generic `tool`
  recipe kind, aggregate inputs/outputs for `script` rows, per-mesh commands
  and `inputs` lists in source-builds records. (3) `dist/` rebuilt (dry then
  real): 17 mods / 109 files / 62,019,454 B, 3 vendor-identical files shipped
  under the MIT allow, 13 complete recipes, 0 gaps, 0 violations, exit 0.
  Ledger written by one atomic replace after an immediate re-read. A 09:38
  re-run, after the concurrent `Dyn FNIS AA functions` row (fnis-aa-fix,
  #148, `distribution: distributable` under GPL-3.0-only) entered the ledger,
  withheld all 8 of that vendor row's files as byte-identical to its GitHub
  release zip and exited 2; every `Ensrick - *` row stayed clean. The #160
  packaging box was ticked on the 09:30 result and re-opened on the 09:38
  one: an unmodified vendor release is a required download, not collection
  payload, and GPL is outside the MIT/BSD/Apache/CC-BY allow ruling.
  RESOLVED 09:52 by the lead's ruling (vendor releases are downloads, never
  collection payload; `distribution` belongs only to Ensrick-made rows; no
  GPL allow): the `Dyn FNIS AA functions` row lost its distribution fields
  and gained `sourceUrl`, `sourceTag` and a verified zip `sha256Note`; the
  packager now admits a classified row only if it has an Ensrick
  source-build record or its name starts with `Ensrick` / ends with
  `- Ensrick <ver>`, reporting anything else as a classification error
  (exit 2, not packaged); the rule is written into `docs/PATCH_INTENTS.md`
  and the generated `dist/README.md`. Final re-run (dry then real) exit 0:
  17 mods / 109 files / 62,019,454 B, 13 recipes, 0 gaps, 0 violations, 0
  classification errors; #160 packaging box ticked.
- **Source:** team-lead ruling on #160 (MIT explicitly permits verbatim
  redistribution with the notice; the byte check alone is over-strict for
  permissively licensed sources) and the 2026-09-02 packaging dry-run
  comment on #160 listing the six gaps. Agent `packaging`.
- **Verification:** none required (ledger metadata, records, packager and
  gitignored `dist/` only; the MO2 instance was read, never written; no
  launch). Nothing committed.

## 2026-09-02 09:30 - Dyn FNIS AA functions 3.0.1 staged: the FNIS_aa provider Pandora's FNIS stub assumed (#148)

- **What:** New mod `Dyn FNIS AA functions` (MO2Headless `mod-stage`,
  transaction `20260902T143023275Z-ea7f2934758d`, priority 13 directly above XPMSSE at 12; enabled)
  from the SARDONYX-sard/fnis_aa GitHub release v3.0.1 (tag `8e4ea36`,
  published 2026-09-02 14:15Z, GPL-3.0-only; Nexus 175362 still lists 3.0.0
  MAIN and 3.0.1-beta): `SKSE/Plugins/fnis_aa.dll` (sha256 `EE5F4C29...30EBB`,
  version 3.0.1.0) + `.pdb`; `scripts/FNIS_aa.pex`, `FNIS_aa2.pex`, `fnis.pex`,
  `FNISVersion.pex`, `FNISVersionGenerated.pex`; `Source/Scripts/*.psc` and
  `fnis_aa-LICENSE.txt` added from the tag. Package kept at
  `headless/packages/Dyn-FNIS-AA-functions-3.0.1-github-8e4ea36`, zip in
  `downloads/`. Why: Pandora 4.4.0-beta's FNIS support is a dummy `FNIS.esp`
  plus an OAR conversion of XPMSE's alternate-animation sets and a
  `SKSE/Plugins/fnis_aa/config.json` written for exactly this plugin
  (`AltAnimToOarBuilder.cs`); nothing provided the `FNIS_aa` / `FNIS` Papyrus
  natives, so XPMSSE 5.06 - the only caller (`XPMSELib`, `XPMSEWeaponQuest`,
  `XPMSEWeaponStyleScaleEffect`, `XPMSEMCM`) - aborted every call. Receipt:
  the 21:28-22:03 play session logged 2033 `not found on object fnis_aa` /
  `fnis` errors (GetInstallationCRC 1123, SetAnimGroupEX 727, peak 524/min at
  21:54) out of 2233 error lines -
  `records/log-snapshots/20260901-2354-play-session/Script/Papyrus.3.log`
  (copied from the overnight-soak 23:54 snapshot). Gate
  `audit/skse_version_data.py` PASS (versionIndependence=1, PE stamp
  2026-09-02, above the cutoff); CommonLibSSE-NG 7.1.0 (`2dde70e8`, contains
  the 1.7.99+ layout fix `68ae73e1` the ConsoleUtil/Proteus rebuilds needed);
  import table has no hard `SKSEMenuFramework.dll` dependency (menu is
  runtime-optional) and imports `MessageBoxW` only through CommonLib's fatal
  path. Scope: restores the API and the `FNISaa_*` graph-variable plumbing so
  XPMSE's weapon-style MCM path is live; the visible draw/sheathe animation
  swap still needs Open Animation Replacer, parked for the #140 load hang.
  Ledger row added; preflight exit 0 after staging.
- **Source:** issue #148 (team-lead dispatch 2026-09-02 09:12, "fnis_aa
  Papyrus flood"); Pandora source
  `Models/Patch.Skyrim64/Format.FNIS/AltAnimToOarBuilder.cs`; Nexus 175362
  description ("Users who use Pandora ... and want to run FNIS AA mods (such
  as XPMSE ...)"); agent fnis-aa-fix.
- **Verification:** `VERIFIED 2026-09-02 09:32` - `records/launch-verify-20260902-093221.md` PASS (main menu 29.8s, save loaded 63.9s; 33 SKSE plugins, 0 refused; `skse64.log`: "plugin fnis_aa.dll (00000001 fnis_aa 03000010) loaded correctly (handle 6)"; `fnis_aa.log`: v3-0-1-0, FNIS_aa2 / FNIS_aa / FNIS natives registered, 0 errors). Soak: `records/launch-verify-20260902-093606.md` PASS (main menu at 29.3s, save loaded at 112.7s), left running with `--leave-running`; after-count at the 09:43 mark from `Papyrus.0.log`: **0** `not found on object fnis*` errors over 4.7 min of flushed post-load log (VM thawed 09:36:02, last flush 09:40:44, 363 post-load lines) against the 09:19 soak baseline of **497** over 6.5 min (`records/log-snapshots/20260902-0920-soak/Script/Papyrus.0.log`) and 2033 in the play session; "XPMSE MainQuest Initialization successful" at 09:36:06 (the 16 `GetGroupBaseValue` init calls that errored on every previous load). Two residual one-off lines, both new signatures: `FNIS.GetFlags` not bound at load (DLL registers it, shipped `fnis.pex` does not declare it, nothing calls it) and one `cannot fetch variable FNISaa_maceqp` on `WindhelmGuardSonsExteriorPatrolBREF` during effect cleanup at unload (Pandora pushed all 33 `FNISaa*` vars; an unload race, not a missing variable). At 09:36:35 the user took the controls of the soak game (TweenMenu; HUMAN_AT_CONTROLS, `records/human-at-controls.jsonl`), so the game was left running for them; `records/launch-verify-20260902-093910.md` is the refused attach-kill of that same pid 26276 - its "FAIL - no main menu" text is an attach-mode artifact, not a launch failure. Still owed: the in-game weapon-style check (XPMSE MCM styles), which also needs OAR (#140).

## 2026-09-02 09:14 - MO2Headless controller 0.2.1 deployed (stale-row fix, #105 follow-up)

- **What:** `mo2-instances\skyrim-se\MO2Headless.exe` replaced with the 0.2.1
  build (`fa8cb528fbb2`, sequence 1788321827, SHA-256 `C9753382...851B04`,
  from `mo2-builds/headless-core-33589364228-fa8cb528/`, GitHub Actions run
  33589364228, disposable-instance regression 40/40 at 23:58). The 0.2.0
  binary is kept beside it as `MO2Headless.exe.bak.v6ed40ae7` (rollback =
  rename back). First stamp via `plugin-disable Ensrick-Deploy-Stamp-NoSuchPlugin.esp`
  (`changed: false`): `headless/controller.version` = 0.2.1 / `fa8cb528fbb2`.
  `toolchain.json` `tools.mo2` re-pinned (root/path/sha256/guiPath/guiSha256/
  commit/run/artifact digest, `controllerVersion` 0.2.1), `TOOLCHAIN.md` row
  updated, `records/source-builds/mo2-headless-0.2.1-fa8cb528.json` written,
  deployment table appended to `docs/MO2-HEADLESS-BUILD-2026-09-01.md`. Only
  the controller binary changed; the instance GUI stays the 3769ece build.
  Live checks: `status` build = stamp, `audit` 0/0, `plugin-list` 236/232,
  `mod-list` 314, `install_mod.py --verify` 0 problems, `preflight.py` exit 0.
- **Source:** morning checklist item "Deploy controller 0.2.1"
  (`docs/MORNING-CHECKLIST-2026-09-02.md`), team-lead dispatch 09:13 to
  morning-ops; deploy steps per `docs/MO2-HEADLESS-BUILD-2026-09-01.md`.
  Done under claim `morning-ops` with no game/MO2 process alive.
- **Verification:** VERIFIED 2026-09-02 09:16 - `records/launch-verify-20260902-091622.md`
  (main menu 30.4 s, save loaded 41.3 s, 32 SKSE plugins checked, 0 refused;
  first live `run` on 0.2.1, stamp `command: run`, 232 plugins active before
  and after). Second PASS on 0.2.1 at 09:20:09
  (`records/launch-verify-20260902-092009.md`, main menu 36.7 s, save loaded
  48.6 s; the soak launch, which the user then played in and quit at 09:27,
  `records/soak-2026-09-02.md`). Log triage of every run since 09-01 17:28:
  `records/log-triage-2026-09-02.md` (#174-#178 opened, receipts on #146,
  #148, #157).

## 2026-09-02 00:06 - Two texture-path overlays staged for the env-mask sweep typos; six sweep issues opened (#167-#172)

- **What:** Two new local overlays, each a byte copy of an existing vendor
  texture placed under the misspelled path its mesh asks for, staged with
  MO2Headless `mod-stage` under the `envmask-sweep` claim (no game or MO2
  process alive; audit `errors: []`, 0 warnings). (1) `Ensrick - CC Madness
  Longsword Env Mask Path Fix` (transaction
  `20260902T050602046Z-725b51195af0`, priority 234, modlist row 2):
  `ccbgssse025-advdsgs.bsa`'s `madness_longsword01_em.dds` copied to
  `textures\creationclub\bgssse025\weapons\madness\madness_longsword_01em.dds`,
  the name both the vanilla CC meshes and Believable Weapons' copies ask
  for (#167; the typo is Bethesda's). (2) `Ensrick - Skyland Solitude
  Manhole Texture Path Fix` (transaction `20260902T050602116Z-cbe4e3d83cbb`,
  priority 235, row 1): Skyland AIO 1K's `smanhole_m.dds` + `smanhole_e.dds`
  copied into `textures\arechitecture\solitude\` (#168). Recipes
  `overlays/ensrick-cc-madness-longsword-envmask-path-fix/build.py` and
  `overlays/ensrick-skyland-smanhole-texture-path-fix/build.py` (pinned
  input/output hashes, refuse on mismatch); ledger rows `distribution:
  recipe`; nothing vendor-derived committed. Issues opened from the sweep
  record: #169 SFCO3 Whiterun castle drapery (archive `113045-783076.7z`
  ships no `gm misc textures` folder and no `GM_DraperyBlue03b.dds` in any
  option), #170 Water for ENB Nordic wall waterfall textures (no
  `tmdwaterfalls` folder or `waterfall_e.dds` in any option of
  `x37061-784038`), #171 HIMBO orcish + SFCO Dwemer metal masks
  (`status:needs-decision`, for the user), #172 Sons of Skyrim
  `SplintedBoots*` meshes (closed on opening: the ESP only uses the
  `BootsSplinted*` meshes, whose `bg_iron_splinted` textures ship). No
  installer option or extra download supplies #169 or #170; nothing else
  installed.
- **Source:** team-lead follow-up on the #159 sweep (2026-09-02 00:03:
  issues per finding, overlay the typo cases, check FOMOD plans for the
  missing sets); evidence in `records/envmask-missing-scan-2026-09-02.md`.
- **Verification:** PASS in `records/launch-verify-20260902-091326.md` (main menu 32.2s, save 58.1s; 32 plugins, 0 refused) - first launch after the 00:06 staging; also covered by `records/launch-verify-20260902-091622.md` (controller 0.2.1; 30.4s / 41.3s). In-game look of the blade and the manhole cover still unverified.

## 2026-09-02 00:05 - Ensrick patch collection packager `tools/package_ensrick.py`: 17 mods packaged, 5 recipes, 6 gaps, 3 vendor-byte withholds (#160)

- **What:** new `tools/package_ensrick.py` (stdlib only, read-only on the
  MO2 instance, `--dry-run` plans without writing). From the ledger's
  `distribution` field it assembles every `distributable` row's MO2 folder
  into `dist/ensrick-patches/<mod>/` honouring `.packagingignore` and each
  row's `packagingExcludes`, skipping `sharedList: excluded` rows; writes
  `dist/ensrick-patches/manifest.json` (per mod: version, every file's
  SHA-256, `distributionBasis` text, source-build record / build script /
  tracked overlay); writes `dist/ensrick-recipes/recipes.json` for every
  `recipe` row whose recorded recipe carries tool + pin, input hashes,
  executable command and expected output hashes (rows missing any of those
  are listed under `gaps`, not included); writes `dist/README.md`. Before
  writing it hashes every shipped file against vendor bytes: all 217 other
  mod folders (size-prefiltered: 1,162 of 50,520 files hashed), 76 extracted
  download folders, 97 zips (25 of 15,332 entries), 308 recorded input
  hashes; 258 7z/rar archives are not readable with the stdlib and are
  reported as unscanned. Matches are withheld from `dist/` and exit 2.
  Run 2026-09-02 05:04Z: 20 distributable rows, 17 packaged (LaunchProbe,
  MenuPilot, Proteus 1.7.99 excluded by `sharedList`), 106 files /
  62,018,212 B, 18 files dropped by `.packagingignore`; 11 recipe rows,
  5 complete (FFF, NotWL, Quicksilver, Vikings mesh, Vikings textures),
  6 gaps (Better Fur and Werewolf Totem: command recorded as a bare verb;
  CRF Semantic Patch: no tool pin / inputs / command; VHR: no machine-
  readable recipe; Varinia: markdown-only recipe; Pandora Output: no
  input/output hashes); 3 violations: `Light Placer - Ensrick 1.7.104`
  ships `po3_LightPlacer.ini`, `Scripts/LightPlacer.pex` and
  `Source/Scripts/LightPlacer.psc` byte-identical to the parked vendor
  `Light Placer` 4.2.1 (MIT; parity documented in the record). Withheld,
  #160 packaging box left unticked pending a ruling. `dist/` gitignored;
  `tools/package_ensrick.py` whitelisted. Nothing committed.
- **Source:** team-lead assignment 2026-09-02 (issue #160 last box, dry run);
  `records/ensrick-overlay-distribution-2026-09-02.md`; `.packagingignore`.
- **Verification:** none required (tooling, no build-state change, no
  launch); packager self-verifies every copy by re-hashing the destination.

## 2026-09-02 00:01 - #102 follow-up: Proteus rows reconciled, five native-overlay build records, JContainers + Proteus source committed (records only)

- **What:** (1) Ledger row `Proteus` enabled false -> true to match
  modlist.txt (+Proteus since 2026-08-28; the park reason no longer applies
  because the DLL-only overlay `Proteus 1.7.104 Native Overlay - Ensrick`
  shadows the package's own Proteus.dll); new row `Proteus 1.7.99 Native
  Overlay - Ensrick` with enabled=false, superseded by the 1.7.104 overlay,
  folder kept on disk (priority 93, DLL SHA-256 316DF6BB..., version
  resource 1.1.0.0, built from `_rebuild_ProteusUtils` at ed5cf51). (2) Five
  new `records/source-builds` records: ensrick-consoleutilsse-1.7.104
  (Ensrick/ConsoleUtilSSE ad5e6e5, CI run 33208154245 success
  20:25-20:41Z, CommonLibSSE-NG 70c1acd), ensrick-jcontainers-1.7.104,
  ensrick-proteus-1.7.104, ensrick-racemenu-skee64-1.7.104,
  ensrick-papyrusutil-1.7.104; each carries base commit, the change list,
  DLL version resource, SHA-256 (all five installed DLLs match the build
  outputs still in `skyrim-tools-source/*-1.7.104`), transaction id, MSVC
  14.44.35207 / VS 17.14.37012.4, vcpkg boost 1.92. (3) The uncommitted
  working trees that produced the installed JContainers64.dll and
  Proteus.dll were committed on their local `ensrick/1.7.104` branches:
  JContainers 70b7362251dd (9 files: version 4.3.1.104, BSFixedString
  offsets for 1.7.104, Boost 1.92 fixes, vcxproj plumbing) and Proteus
  901a5cd79a63 (5 files: version 1.1.0.104, CommonLibSSE 3d81614 ->
  70c1acd, 1.7.104 runtime allowlist, verifier update). Commit only: not
  pushed, no remotes added. RaceMenu (3 files) and PapyrusUtil (3 files)
  stay uncommitted by scope (no redistribution licence); their records pin
  the working tree by per-file SHA-256 and patch hash. No MO2 profile,
  plugin or game-state change in this item.
- **Source:** team-lead follow-up 2026-09-02 on #102 (flags from the ledger
  fill: Proteus enabled mismatch, unledgered 1.7.99 folder; provenance gap
  F8 in `docs/PROCESS-AUDIT-2026-08-30.md`); #160 build-record boxes.
- **Verification:** none required (records and local source commits only;
  no launch). `install_mod.py --verify` 0 problem(s); preflight clean (1
  pre-existing Steam-overlay warning).

## 2026-09-02 00:01 - Misc Effects ENB Light main 1.6 + update 1.6.1 installed below Believable Weapons (#102 follow-up)

- **What:** Two new mods via `audit/install_mod.py` under the work claim
  (SkyrimSE.exe and ModOrganizer.exe confirmed absent first): `Misc Effects
  ENB Light` (65070 MAIN 1.6, file 418811, archive SHA-256 F2870D9D...,
  transaction 20260902T045458708Z-faa5633eab6a) and `Misc Effects ENB Light -
  Update 1.6.1` (file 423903, one new mesh
  `dlc1falmervalleybrazierlight.nif`, SHA-256 706DB892...,
  transaction 20260902T045459760Z-f1fd059060d4). Reason: the already-installed
  optional `Misc Effects ENB Light - Believable Weapons` is documented on its
  page as an overwrite of the main file, and the main was never installed.
  Placed with `mod-priority` at 90 (main) and 91 (update), BELOW Believable
  Weapons (now 92) and the optional (now 94): the main overlaps Believable
  Weapons on 2 bound-weapon ench-effect meshes and the optional on 4, so the
  base-layer rule in `docs/PATCH_INTENTS.md` holds and the optional wins its
  4 files. Meshes only, no plugins, no INI/config change. Ledger rows written
  by the installer, notes added (ledger 228 -> 232 with the Proteus rows
  below). `install_mod.py --verify` 0 problem(s); preflight clean.
- **Source:** team-lead follow-up 2026-09-02 on #102 (the missing main file was
  flagged in the optional's ledger row); Nexus file 270746 description
  "Install the main file and then overwrite with this"; update file 423903
  "Merge with main file" (latest version is law).
- **Verification:** VERIFIED 2026-09-01 23:58 by records/launch-verify-20260901-235806.md (envmask-sweep launch; SkyrimSE.exe started 23:57:16 local, after the 23:54:58 install and 23:55:00 priority moves; main menu 30.7 s, save loaded 43.5 s, 232 plugins). Launch/load level only; the ENB-light meshes were not render-checked. No launch by this agent; envmask-sweep was messaged
  before its run so the record covers these meshes.

## 2026-09-01 23:55 - Human-at-the-controls guard on every harness kill and on installs under a live game (#164)

- **What:** new `audit/human_presence.py`: after the harness's
  `AUTOLOAD_SETTLED` (or, in a menu-only run, `MAIN_MENU_OPEN`), any
  `MENU_OPEN` of a gameplay menu in `LaunchProbe.log` (TweenMenu,
  InventoryMenu, MagicMenu, MapMenu, Journal Menu, Sleep/Wait Menu, Dialogue
  Menu, Console, plus container/barter/favorites/stats/crafting/lockpicking/
  book/training/gift) that no MenuPilot `COMMAND` explains within 2 s means a
  person is playing. `launch_verify.kill` (the only kill in the file; there is
  no idle timeout under `--leave-running`) now judges first: on a human it
  REFUSES, prints and records `HUMAN_AT_CONTROLS`
  (`records/human-at-controls.jsonl` + the run record), leaves the game up
  and exits **88** whatever the verdict; `--force-kill "<reason>"` overrides
  and logs the reason. `install_mod.py` install and `--sort` run the same
  check when `SkyrimSE.exe` is alive and refuse with 88 on a human. Fixtures
  in `audit/fixtures/`: the 23:41 session's real `LaunchProbe.log` +
  `menupilot.log` (the one the 23:45 kill ended) and the 23:11 smoke's log
  reconstructed from its record. `py -3 audit/human_presence.py --selftest`:
  8/8 - 23:41 detected (first unmatched Journal Menu 23:42:01.909, the piloted
  Console open at 23:42:07 correctly excluded), 23:11 not detected, a missing
  pilot log makes every gameplay open count, a stale log never claims a
  human. In-process wiring test: `launch_verify.kill` refused on the human
  fixture (flag set, taskkill not run), killed with `--force-kill`, killed on
  the clean fixture. Not launched; no game process was touched.
- **Source:** team-lead directive 2026-09-01 23:50; issue #164 (23:45 kill of
  guard-patch's `--leave-running` session while the user played, unsaved).
- **Verification:** UNVERIFIED as a launch (tooling; selftest + wiring test
  only, no launch required per directive). First live exercise is whichever
  `launch_verify` run next ends a session.

## 2026-09-01 23:53 - Ensrick - Skyking Signs Env Mask Fix extended 4 -> 11 masks; load-order env-mask sweep, 10 mods flagged (#159)

- **What:** `Ensrick - Skyking Signs Env Mask Fix` re-staged (MO2Headless
  `mod-stage --replace`, transaction `20260902T045315225Z-7d160abddf8d`,
  priority kept at 228 = modlist row 4, enabled, audit `errors: []`). The
  same 212-byte 4x4 black alpha-1 env mask now also sits at the seven
  remaining paths Skyking Signs' `03 Parallax` meshes reference and nothing
  ships: `markarth\mrkdeco01_m`, `markarth\mrkinnwindows01_m`,
  `riften\riftenlogdetails01_m`, and `landscape\{fieldgrass01,
  mountains\mountainslab02, rocks01, tundra01}_m` (load-screen mesh). The two
  Markarth masks are also what `Skyking Unique Signs` asks for
  (signthehagscure, signarnleifandsons), and `mountainslab02_m` is what
  `ERM - Fix and Addon`'s `minecboulderl02.nif` asks for, so those are covered
  by the same files. Vanilla ships no `_m` for any of the eleven and shades the
  same surfaces with the Default shader, so a black mask reproduces the
  vanilla look. `build.py` carries the eleven paths; all 11 DDS read cleanly by
  texconv 2026.4.1.1. Ledger row updated (files, recipe, hashes). New tool
  `audit/envmask_scan.py` swept every enabled mod's loose NIFs (207 mods,
  11,351 NIFs, 4,999 env-mapped shapes, 10 s) against loose files + 59 mod
  BSAs + 92 vanilla BSAs: 103 shapes in 10 mods have an env mask or cubemap
  that resolves nowhere. Only the Skyking / Unique Signs / ERM cases were
  masked (matte wood, stone, ground, rock). NOT masked, listed for the user in
  `records/envmask-missing-scan-2026-09-02.md`: HIMBO Refits orcish armor
  (metal, obsidian cubemap), SFCO 3 Dwemer furniture (metal) and Whiterun
  castle drapery (mask exists under another SFCO path, diffuse missing too),
  Sons of Skyrim splinted set (whole texture set absent), Believable Weapons
  madness sword (`_01em` vs the CC BSA's `01_em`), Skyland AIO `smanhole.nif`
  (`arechitecture` typo, real mask + cubemap ship beside it), Water for ENB
  `norextwallbg1way01water.nif` (its own `tmdwaterfalls` textures not
  installed), Lux Orbis `sbridge01.nif` (shadowed by Assorted Mesh Fixes, never
  renders). Vanilla BSA-packed NIFs and mod BSA-packed NIFs were not opened.
- **Source:** user question 2026-09-01 ("now we should have no more of these
  strangely reflective textures?"), team-lead dispatch on #159 (extend the
  overlay to all eleven + sweep the load order); evidence in the record.
- **Verification:** PASS in `records/launch-verify-20260901-235806.md`
  (main menu 30.7s, save loaded 43.5s, claim `envmask-sweep`, direct chain).
  In-game A/B on #159 still owed (Numpad * discriminator; now also a Markarth
  sign and the Riften orphanage sign).

## 2026-09-01 23:52 - Light Placer rebuilt from source for 1.7.104 / Address Library v5, installed as `Light Placer - Ensrick 1.7.104`, vendor row stays parked (#79, #140)

- **What:** New mod `Light Placer - Ensrick 1.7.104` (MO2Headless `mod-stage`,
  transaction `20260902T045032956Z-13ae860d76e1`, priority 43 directly above the parked vendor
  `Light Placer` at 42; enabled). Complete package built from the public
  fork `Ensrick/LightPlacer` branch `ensrick/1.7.104` (commit `ae48c76`,
  pushed; upstream master `1f15e5c` = v4.2.1 + 2 fixes): `po3_LightPlacer.dll`
  (sha256 `2BD0ADFD...EA92`, file version 4.2.1.1.0) + `.pdb`,
  `po3_LightPlacer.ini` and `Scripts/LightPlacer.pex` byte-identical to the
  vendor 4.2.1 files, `Source/Scripts/LightPlacer.psc`, `LightPlacer-LICENSE.txt`.
  Why a rebuild: the vendor DLL's embedded CommonLib reads Address Library
  formats 1-2 only, so on 1.7.104 `po3_LightPlacer.log` ended with
  "Unsupported address library format: 5" and the game died at t+4.3s
  (`records/launch-verify-20260901-230735.md`). The fork follows upstream's
  own August migration: submodule -> `powerof3/CommonLibSSE` dev `cbb5c29a1`
  + `libxse/commonlib-shared` `b8f30fb8` (its `IDDB.cpp` has `load_v5`),
  plus `no-modal-fail.patch` so `REX::FAIL` logs and terminates without a
  MessageBox (the built DLL imports neither MessageBoxA nor MessageBoxW; the
  vendor DLL imported MessageBoxW). Not CommonLibSSE-NG: po3's code uses
  fork-specific APIs and upstream's own migration (BaseObjectSwapper /
  PapyrusExtender, 2026-08-25) was the smaller, more faithful diff to follow.
  Gate: `audit/skse_version_data.py` PASS - versionIndependence=5,
  versionIndependenceEx=2 (AddressLibraryV5 bit YES), compatibleVersions
  `1.7.104.0`, PE stamp 1788323919 (2026-09-02 04:38:39Z). Feature defaults
  identical to vendor (`feature_defaults_diff.py` exit 0, #144). Build 0
  warnings under upstream's `/W4 /WX`. Licence: MIT (notice ships in the
  package), so the row is `distribution: distributable`. Vendor `Light
  Placer` 4.2.1 row stays disabled with a SUPERSEDED note. Record:
  `records/source-builds/ensrick-light-placer.json`; ledger row added.
- **Source:** team-lead assignment (rebuild-forward, never park; no popups;
  latest is law), issues #79 and #140, `records/launch-verify-20260901-230735.md`.
- **Verification:** `VERIFIED 2026-09-01 23:52` - `records/launch-verify-20260901-235200.md` PASS, main menu 31.4s, save loaded 42.1s (232 plugins seeded). `skse64.log`: "plugin po3_LightPlacer.dll (00000001 LightPlacer 04020010) loaded correctly (handle 16)". `po3_LightPlacer.log`: "po3_LightPlacer v4.2.1.1 / Game version : 1.7.104.0", 9 Lux CS Patch JSON configs read, 30 hooks installed, RESULTS "Models : 267 (295 lights)", console commands installed - the vendor build never got past the address-library header. Preflight exit 0 before the launch. Not yet eyeballed: a lit Lux CS interior.

## 2026-09-01 23:48 - #102 ledger gaps closed: 7 enabled mods without a row recorded (records only)

- **What:** `records/installed-mods.json` 221 -> 228 rows. Five Ensrick native
  rebuild overlays for Skyrim 1.7.104 (DLL-only, priority 106-110 above their
  base mods; provenance, transaction ids and installed-DLL SHA-256 taken from
  `docs/NATIVE-RUNTIME-1.7.104-REBUILD-2026-08-28.md`,
  `docs/CONSOLEUTIL-1.7.104-REBUILD-2026-08-28.md` and
  `docs/RUNTIME-ISSUES-2026-08-28.md`): ConsoleUtilSSE 1.6.1.104
  (Ensrick/ConsoleUtilSSE ad5e6e5, CI run 33208154245, distributable),
  JContainers 4.3.1.104 (ryobg base 90db5e2, MIT, distributable),
  Proteus 1.1.0.104 (Nightfallstorm base 324e07c, GPL-3.0, distributable),
  RaceMenu skee64 0.4.19.17 (expired6978 base 748ca80, local-only) and
  PapyrusUtil 4.7 (eeveelo base 01ac25d, local-only); the two local-only
  classes mirror the active blockers in
  `records/private-runtime-dependencies.json`, the three distributable rows
  carry the "notices and reproducible build still owed" gap from the #160
  sweep. Two vendor rows resolved through the Nexus API from each folder's
  `meta.ini` installationFile and hashed from the downloads folder: Believable
  Weapons 37737 / file 260562 v1.5 (archive SHA-256 C9F93A3F..., FOMOD plan
  `records/fomod-plans/37737-believable-weapons.json`, 136 mappings; noted as
  the user-designated base layer for generic iron/steel per
  `docs/PATCH_INTENTS.md`) and Misc Effects ENB Light - Believable Weapons
  65070 / file 270746 v1.2.1BoundOptionals (archive SHA-256 6409B9D8..., 6
  bound-weapon NIFs). Both were installed 2026-08-26 straight through
  MO2Headless, which is why no row existed (PROCESS-AUDIT F4). Flagged in the
  rows, not acted on: the base `Proteus` row still says enabled=false while
  modlist.txt has +Proteus; the ENB Light main file is not installed although
  the optional file's page says to overwrite it. No MO2 profile, plugin or
  game-state change.
- **Source:** `audit/preflight.py` WARN "7 enabled mod(s) have no ledger row
  (#102)"; issue #102; team-lead task 2026-09-01.
- **Verification:** none required (records only; no launch).
  `py -3 audit/install_mod.py --verify` = 0 problem(s);
  `py -3 audit/preflight.py` clean, the ledger-gap WARN is gone (1
  pre-existing Steam-overlay warning remains).

## 2026-09-01 23:35 - #160 recipe gaps closed: every Ensrick recipe row now reproducible from recorded inputs (records only)

- **What:** Closed 10 of the 12 checklist boxes on #160. texconv pinned in
  `toolchain.json` (`tools.texconv`, DirectXTex 2026.4.1.1, SHA-256
  563D9ECA...) and the stale nifPortCli hash refreshed; nif-port-cli commits
  e12079c + c63f74e pushed to `agent/shape-overlay-and-texture-remap` (PR
  Ensrick/nif-port-cli#2; `main` is protected). New executable recipe
  `overlays/ensrick-bloodskal-blade-4-static-glow/build.py` (reproduces the
  installed mesh byte-for-byte from the vendor NIF). New
  `records/source-builds` records: collectibles-helper-ussep-forward,
  quickloot-ie-1799, general-compatibility-patch,
  assorted-mesh-fixes-se-mesh-port (57 input/output hash pairs, rerun 57/57
  identical with two binaries), vikings-weaponry-se-mesh-port (6/6 identical
  from BSA-extracted inputs). Ledger: `recipe` field on the 5 texture caps
  (per-file texconv command + vendor input hash + output hash), FFF cap
  (archive entry `textures 1k/.../Twigs_Freak.dds`, SHA-256 E4CC21AE...),
  AMF/Vikings ports, Bloodskal glow; LaunchProbe/MenuPilot
  `sharedList: excluded (diagnostic tooling)`; SDT row sha256 filled +
  `packagingExcludes`; QuickLoot/Lux Water rows' null hashes filled; 4 rows
  added (CRF Semantic Patch=recipe, General Compatibility Patch=distributable,
  Scoped Werewolf Totem Skull=recipe, Pandora Output=recipe; ledger 216 ->
  220). Lux Water CS Patch blocker cleared in
  `records/private-runtime-dependencies.json` after re-parsing the ESP (559
  overrides, 0 new forms, no assets). `.packagingignore` added (stray
  `SSEDisplayTweaks_Custom.ini.bak.v20260901-pre-120hz`, `*.bak*`,
  `meta.ini`, Pandora `Engine.log`, LaunchProbe/MenuPilot). Collectibles
  Helper generator source staged in-tree at
  `mods/collectibles-helper-ussep-forward` (no repo exists; commit + push
  still open). Still open: that box and the packaging step. Flagged: the
  installed General Compatibility Patch came from an uncommitted worktree
  state (pushed manifest hash differs). No MO2 profile, plugin or game-state
  change.
- **Source:** #160 sweep (`records/ensrick-overlay-distribution-2026-09-02.md`,
  "Closure pass" section); team-lead task 2026-09-01.
- **Verification:** none required (records, recipes and tool pins only; no
  launch). Recipe reproduction checks: Bloodskal 42-byte patch hash match,
  AMF 57/57, Vikings 6/6, FFF entry hash match. `audit/preflight.py` clean
  (3 pre-existing warnings).

## 2026-09-01 23:37 - Ensrick - Guard Scaling Patch installed: ordinary guards PC x1.0 from level 5 instead of 20 (#51)

- **What:** New generated plugin `Ensrick Guard Scaling Patch.esp` (ESL-flagged,
  override-only, 3 NPC_ records, masters Skyrim.esm + Dragonborn.esm) in local
  mod `Ensrick - Guard Scaling Patch` (MO2Headless `mod-stage`, tx
  `20260902T043727658Z-14d275ba88ef`, priority 230; `plugin-enable` tx
  `20260902T043728222Z-17887e2ec06b`; LOOT rule added to
  `config/loot/userlist.yaml` and the live userlist, group `Ensrick Generated
  Patches` after the CRF Semantic Patch; `install_mod.py --sort` run
  `records/tool-runs/20260902T043805857Z-mo2-loot-5278d2f0`, plugin lands
  last at plugins.txt line 237, 232 active; `--verify` 0 problems). Record
  audit `records/guard-scaling-audit-2026-09-02.md`: the level-20 guard is
  **vanilla** - every hold/city guard inherits stats from
  `EncGuardImperialTemplate` (0F6F37) / `EncGuardSonsTemplate` (0F6F38),
  Skyrim.esm PC x1.0 calc-min 20 max 50, USSEP forwards identical values; no
  installed mod inflates guard levels (Sons of Skyrim / Xtudo / USSEP touch
  placed guard records for outfits and class only). The patch sets those two
  plus `DLC2RRGuardTemplate` (Raven Rock, same 20-50) to PC x1.0 min 5 max 50.
  Untouched and listed with reasons in `mods/guard-scaling-patch/policy.json`:
  named captains/commanders, CW soldiers (PC x0.25 from 1), siege/Penitus/
  Thalmor tiers, `GuardWinterholdCollege` (CRF winner, kept out of masters),
  and mod-added guard families (Bruma, Wyrmstooth, Beyond Reach, 3DNPC,
  Vigilant, Grand Solitude). Generator + Spriggit tree + policy committed
  under `mods/guard-scaling-patch/` (`regenerate.ps1`, 2 byte-identical runs,
  73 links / 0 unresolved, raw ACBS byte parse as independent receipt); build
  record `records/source-builds/ensrick-guard-scaling-patch.json`; ledger row
  `distribution: distributable`. Rollback: disable the one mod.
- **Source:** user rule on #51 (2026-08-29) and the 2026-09-01 report "I tried
  attacking a single guard and it was like fighting a level 20 at level 1";
  team-lead brief 2026-09-01 (guard-patch agent).
- **Verification:** VERIFIED 2026-09-01 23:42 - `launch_verify` PASS, main
  menu **34.9 s**, save loaded **46.3 s** (`kPostLoadGame success=1`), direct
  chain, claim `guard-patch`, post-launch preflight clean (4 warnings, all
  pre-existing). Record: `records/launch-verify-20260901-234200.md`. The
  guard *level* itself is not yet witnessed in-game: MenuPilot can fill the
  console entry but cannot execute it (see `docs/MENUPILOT.md`, console
  section), so the manual check stands: open the console on any hold guard
  and run `GetLevel` - expect `max(5, player level)` instead of 20 (fresh
  spawns only; guards already loaded in the save keep their level until they
  respawn or the cell resets). Note: the user took the controls inside this
  verification session at 23:43 and the agent's `launch_verify.kill` of pid
  49836 at 23:45 ended it (team-lead heads-up arrived afterwards); nothing
  was saved by the agent.

## 2026-09-01 23:12 - Hardening package 3/3: controller 0.2.0 deployed, real LocalSettings flag flipped, Light Placer validated and re-parked, smoke PASS (#105, #91, #143, #98, #140)

- **What:** (1) MO2Headless **0.2.0** (`Ensrick/modorganizer@6ed40ae7`, GHA run
  33571039440, sha256 `E484A21C...2DB4`) deployed to
  `mo2-instances\skyrim-se\MO2Headless.exe` (3769ece kept as
  `MO2Headless.exe.bak.v3769ece`), instance stamped
  `headless/controller.version` = 6ed40ae74272 / 1788305193, `toolchain.json`
  re-pinned. `run` now restores plugin enable markers itself and reports
  `stateDelta`; an older controller refuses a newer-stamped instance (exit
  78); `--replace` keeps priority and enabled state. Disposable-instance
  regression 39/40 (the one gap is fixed in 0.2.1 `fa8cb528`, run
  33589364228: downloaded 23:58, same regression 40/40, NOT deployed so the
  smoked build stays the verified state - morning item). Record:
  `docs/MO2-HEADLESS-BUILD-2026-09-01.md`,
  `records/source-builds/mo2-headless-0.2.0-6ed40ae7.json`. (2) The REAL
  profile flag: `profiles/Default/settings.ini` `LocalSettings` false -> true
  (original kept as `settings.ini.bak.v20260901-localsettings-false`); the
  stray `settings.txt` that every gate had been reading renamed
  `settings.txt.bak.v20260901-stray`; empty `skyrimcustom.ini` copied into the
  profile so the MO2 GUI cannot raise its "missing profile-specific INI"
  dialog. `preflight.check_profile_owns_inis` now reads `settings.ini`
  (FAIL), `preflight_extra` warns on any stray; `docs/INI_AND_PROFILE_STATE.md`
  gained "The file that actually holds the flag". (3) **Light Placer** 4.2.1
  restored (`mod-enable`, tx 20260902T040611304Z) under the
  unpark-requires-PASS rule and validated by launch: the game died at t+4.3s
  on `loading plugin "LightPlacer"`, `po3_LightPlacer.log`: "Unsupported
  address library format: 5" - a genuine #140 failure, so it was re-parked
  (`mod-disable`, tx 20260902T040821246Z; ledger `enabled:false` with the
  reason; evidence on #140). `preflight.check_last_launch_completed` now
  checks whether the dying plugin's DLL is still in an enabled mod (via SKSE
  version data) and only FAILs while it is - otherwise the next launch is the
  park's confirmation. (4) One consolidated `launch_verify` smoke through the
  hardened chain covering packages 1-3 plus everything other agents staged
  since the 17:28 PASS (Skyking Signs env-mask overlay #159, shadow filter
  #151, fMoveLimitMass #150, DT 119 fps cap / LockCursor #149, CS Advanced
  Skin + Hair Specular off #144 - config-load only, visuals not judged).
  Steam cleanly restarted afterwards from a scrubbed environment; post-launch
  preflight clean, deliberate INI keys intact, 231 active plugins before and
  after, claim released.
- **Source:** team-lead hardening brief items 1, 2c, 3, 4 and the resume
  order of 2026-09-01 23:00; #140 "unpark requires a PASS"; #143 root cause
  (`modorganizer/src/profile.cpp:94`).
- **Verification:** VERIFIED 2026-09-01 23:11 - `launch_verify` PASS, main
  menu **31.3 s**, kDataLoaded 30.8 s, save load started 34.4 s, save loaded
  **43.5 s** (`kPostLoadGame success=1`), 31 plugins checked / 0 refused,
  direct chain `MO2Headless run -> headless-run -> skse64_loader` with the
  probe variables on that child only, `settings.ini LocalSettings=true`
  mapping in effect, Documents INIs identical to the profile. Record:
  `records/launch-verify-20260901-231117.md`. The preceding run
  `records/launch-verify-20260901-230735.md` is the Light Placer FAIL.

## 2026-09-01 19:15 - Hardening package 2/3: launch chain - env scrub, profile-INI sync, direct spawn, claim (#141, #143, #103)

- **What:** `audit/launch_skyrim.ps1` rewritten in place: [0] refuses to run
  under another owner's instance claim (exit 75; `-IgnoreClaim` logs a
  warning instead); [0] harvests every `SKYRIM_LAUNCH_PROBE_*`,
  `SKYRIM_MENU_PILOT_*` and `SKYRIM_CLAIM_OWNER` variable and REMOVES it from
  the process before the Steam cycle, so the restarted Steam can never carry a
  harness autoload into the user's own launches again (the 15:39 / 15:58
  crashes of 2026-09-01); `SKSE_AUTOMATION_SILENT_UI=1` deliberately stays
  (popup suppression is wanted everywhere); [2] copies profile
  `skyrim.ini` / `skyrimprefs.ini` / `skyrimcustom.ini` over the Documents
  pair whenever the hashes differ, keeping the Documents copy as
  `.bak.v<stamp>-presync`, and prints which file MO2 will actually map
  (`settings.ini` LocalSettings); [5] `-Direct` spawns the game through
  `MO2Headless --timeout 0 run skse64_loader.exe` (headless-run under usvfs)
  with the harvested variables set on that child ONLY; without `-Direct` the
  Steam chain is used and no harness variable can reach the game.
  `audit/launch_verify.py`: acquires the instance claim for the run (REFUSED
  when someone else holds it; `--claim-owner`, `--keep-claim`), refuses while
  SkyrimSE.exe / MO2Headless.exe / ModOrganizer.exe already exist, launches
  `-Direct` by default (`--steam-chain` is menu-only by construction), and
  records claim + chain in the evidence. `preflight.py`: MO2Headless alongside
  a running game is the launcher holding the lock, a WARN, not a competing
  writer.
- **Source:** #141 comment 2026-09-01 (environment leak through the Steam
  cycle), #143, #103; team-lead hardening brief item 2b/2c/2d.
- **Verification:** VERIFIED 2026-09-01 23:11 by the package 3/3 smoke (`records/launch-verify-20260901-231117.md`: direct chain, env scrubbed, INIs identical after sync, main menu 31.3 s, save loaded 43.5 s).

## 2026-09-01 22:46 - Ensrick - Skyking Signs Env Mask Fix overlay installed, enabled at priority 227 (#159)

- **What:** New local overlay mod `Ensrick - Skyking Signs Env Mask Fix`
  (MO2Headless `mod-stage`, transaction `20260902T034620898Z-5cd4ea984e2b`,
  modlist row 2, above `Skyking Signs` at row 107). Four 4x4 solid-black
  alpha-1 env masks at `textures\architecture\{whiterun\wrwoodbeam01_m,
  farmhouse\woodpost02_m, riften\riftencanalwood01_m,
  windhelm\whwoodbase01_m}.dds`, generated by
  `overlays/ensrick-skyking-signs-envmask-fix/build.py` (nothing
  vendor-derived). Skyking's chosen `03 Parallax` meshes point every sign's
  wooden post at those masks, which no loose mod, vanilla BSA or enabled-mod
  BSA ships; with the 1x1 black cubemap that makes CS Dynamic Cubemaps paint a
  full-strength glossy reflection on the wood (the user's "oily acrylic"). A
  black mask zeroes envMask so the post shades like the standard `01` meshes;
  the sign boards keep their parallax. No CS setting changed (all relevant
  ones are source defaults). Rollback: disable the one mod. Fallback if the
  shine survives: standard-only reinstall of Skyking Signs (drop the two
  `03 Parallax` mappings in `records/fomod-plans/112902-skyking-signs.json`).
  Ledger row added. Audit `errors: []`. Claim taken and released; no game or
  MO2 GUI process during the change.
- **Source:** user report ("weird material shine on the posts holding up
  signs ... slick oily acrylic"), team-lead choice of option (c) on #159;
  evidence in #159 (NIF shader parse, VFS + BSA scans, `Lighting.hlsl`
  ~1905-1950).
- **Verification:** UNVERIFIED. Morning A/B in #159: Riverwood Sleeping Giant
  post / Whiterun sign brackets; Numpad * (CS shaders off) is the instant
  discriminator.

## 2026-09-01 18:47 - Farming CC re-download via MenuPilot: BLOCKED by the native store; 2 launches, no build change (#142)

- **What:** No file changed in the build. Attempted `ccvsvsse004-beafarmer.bsa`
  re-acquisition headlessly: (1) main menu -> CREATIONS through `input.tap`
  (first real exercise; Down/Up/Accept/Cancel verified with text readback);
  the engine opened `Login Menu` then `Marketplace Menu`, whose movie is the
  `CreditsMenu.swf` placeholder - the store is native, nothing readable, so no
  blind input was sent into it. (2) `bUpsellOwned=0` first-run state for 10
  min plus two store visits: no download. (3) `gfx.invoke` of
  `ExternalInterface.call("OpenCreditsMenu")` to reach the main menu's
  `DownloadAll` FxDelegate callback: AV `SkyrimSE.exe+117AB19`
  (`crash-2026-09-01-18-43-46.log`). Cleanup: both INIs restored to pre-edit
  SHA256, preflight clean, Steam restarted from a clean env (#141), claim
  released. Tooling: `launch_verify.py --no-autoload` (verdict `MENU-ONLY`,
  never PASS), `docs/MENUPILOT.md` store section rewritten,
  `records/menupilot-farming-attempt-2026-09-01.md`, logs in `records/tool-runs/`.
  Remaining #142 item stays open with the ~30s manual path (CREATIONS -> O ->
  "Download all owned Creation Club Creations"); expected bsa 18,261,078 B.
- **Source:** team-lead task (finish #142), user launch mandate; Steam guide
  3107226125 for the options-key path; `ContentCatalog.txt` for the size.
- **Verification:** MENU-ONLY x2 (`records/launch-verify-20260901-181756.md`,
  t+48.8s; launch 2 t+31.6s) - deliberately no save load; build state
  identical to the 17:28 PASS baseline.

## 2026-09-01 18:45 - Hardening package 1/3: instance work claim, canonical-checkout guard, preflight gates (#103, #105, #102, #143, #140, #144)

- **What:** (1) `audit/claim.py` - the instance work claim
  (`mo2-instances/skyrim-se/.assistant-claim.json`: owner, pid, purpose,
  acquiredAt, ttlMinutes, expiresAt); acquire/renew/release/check/status,
  atomic create, stale-TTL takeover with a logged warning
  (`records/claim-log.jsonl`), `--selftest` 17/17. (2) `install_mod.py`:
  install and `--sort` run under the claim (a claim held by someone else stops
  the script before the download, exit 75) and refuse to mutate the live
  profile from any checkout but `C:\Users\danjo\source\repos\skyrim-mod-assistant`
  (`--i-know-what-im-doing` overrides, logged). (3) `audit/preflight_extra.py`,
  wired into `preflight.py`: DLL-depth sweep (an enabled mod with a `.dll`
  under `Plugins/` that is not `SKSE/Plugins/` = FAIL), modlist-vs-ledger gap
  = WARN with names (11 today), watched-config snapshot+diff
  (`audit/watched_configs.json` -> `records/config-history/`: CS
  SettingsUser/SettingsDefault, FSMP configs.json, SSEDisplayTweaks*.ini,
  Underwear.ini, MLO.ini, FirstPersonFOV.ini, profile settings.ini), saves
  mirror before launch (`records/save-backups/<stamp>/`, 72 files, newest 5
  kept, skipped when unchanged), the claim in the report. (4) FINDING: MO2
  reads the profile's `settings.ini` (`modorganizer/src/profile.cpp:94`),
  which says `LocalSettings=false`; the `settings.txt` every gate checked is a
  stray nobody reads. That is why #143 happened with "LocalSettings=true".
  Gate added as WARN now, promoted to FAIL when the flag is flipped under the
  claim (package 3). (5) `audit/feature_defaults_diff.py` for source builds
  (#144). (6) Policy: `docs/CURATION_POLICY.md` "Launch verification is the
  definition of done" and "Source builds record their feature defaults";
  `docs/AGENT_WORK_QUEUE.md` "Instance work claim" and "Done means
  launch-verified"; `audit/README.md` tool rows. Also includes in-flight
  `preflight.py` additions found uncommitted on disk (INI snapshots,
  game-folder manifest, fMoveLimitMass / fPoissonRadiusScale deliberate keys)
  so the file on disk and the file in git agree.
- **Source:** user directive 2026-09-01 ("make sure we don't have the issues
  we've already worked through today ever again"), team-lead hardening brief;
  `docs/PROCESS-AUDIT-2026-08-30.md` F0, F2, F4, F5; #103 comment (FSMP
  double-install, VHR near-collision).
- **Verification:** UNVERIFIED as a launch (tooling only; `preflight.py` runs
  clean apart from the live farming-store claim and its deliberate
  `bUpsellOwned=0`); the package-3 smoke launch covers the chain.

## 2026-09-01 18:30 - Shadow filter radius doubled: fPoissonRadiusScale 4 -> 8 (staged, #151)

- **What:** profile `skyrim.ini` [Display] gains `fPoissonRadiusScale=8.0` (key was absent = engine default 4.0; BethINI Pie "Shadow Filtering" slider 0-8, Skyrim.ini key, not Prefs). Original kept as `skyrim.ini.bak.v20260901-preshadowfilter`. This is the radius of the fixed kernel CS 1.8's Utility shadow-mask shader uses for every sun, spot and point shadow (`Utility.hlsl:281,312-335`; CS binds it from the vanilla constants). Doubling it softens all shadow edges uniformly; Screen Space Shadows keeps contact edges crisp. No PCSS exists in CS 1.8 or the ecosystem (doodlum Soft Shadows 74632 hidden 2026-08-24). Registered in `audit/preflight.py` DELIBERATE and the INI-state table. Not launched: another agent holds launch authority.
- **Source:** user report 2026-09-01 ("window shadows... too sharp around the edges"), team-lead task; diagnosis in #151.
- **Verification:** UNVERIFIED (config staged only; needs relaunch + the #151 Dragonsreach / Whiterun market check).

## 2026-09-01 23:02 - Media Keys Fix SKSE 1.0.2 installed (Windows key)

- **What:** `Media Keys Fix SKSE` (Nexus 92948, file 792882 v1.0.2 2026-08-21, archive
  sha256 49918f7a...17ec6, DLL gate PASS: PE stamp 1787337700 = 2026-08-21,
  versionIndependence=1, viEx=1, outside the SKSE reject window) installed
  through install_mod.py under the work claim, plus the config overlay mod
  `Ensrick - Media Keys Fix Configuration` (mod-stage from
  overlays/ensrick-media-keys-fix-config, `DisableWindowsKey=false`) staged
  ABOVE it in priority (modlist line 1 vs 2). Effect at next launch: the
  game's DirectInput flags become FOREGROUND|NONEXCLUSIVE, so the Windows key,
  media keys and Alt+F4 work while the game is focused; DT LockCursor still
  confines the pointer while focused and releases it when Start opens.
  Ledger rows added; INI doc rows updated.
- **Source:** user reports 2026-09-01 (Win key), #149 evidence (game sets
  DISCL_EXCLUSIVE|DISCL_FOREGROUND|DISCL_NOWINKEY, epinter/MediaKeysFix
  src/Main.h); team-lead authorisation 2026-09-01 evening ("install Media Keys
  Fix SKSE through the standard pipeline"), citing the user's standing "try to
  fix all these".
- **Verification:** PASS in `records/launch-verify-20260901-231117.md` (main menu 31.3s, save 43.5s) - config loaded: `MediaKeysFix.log` 23:10:31 `DisableWindowsKey='false'` then `SetCooperativeLevel ... setting to 0x06`. In-game Windows-key check still owed (#149).
## 2026-09-01 18:50 - Window/input and clutter-physics triage (staged, no install)

- **What:** (1) profile `skyrim.ini` `[HAVOK] fMoveLimitMass=0` added (engine
  default 95 = mass ceiling the player shoves; 0 stops the player knocking
  clutter around), original at `skyrim.ini.bak.v20260901-pre-movelimitmass`;
  stale DT comment on `fMaxTime` corrected; key added to `preflight.py`
  DELIBERATE and to docs/INI_AND_PROFILE_STATE.md. (2) `LockCursor` row in the
  INI doc corrected to the deployed `true` (17:41 flip); repo overlay copy
  synced to the deployed file. (3) NEW config overlay
  `overlays/ensrick-media-keys-fix-config/SKSE/Plugins/MediaKeysFix.ini`
  (`DisableWindowsKey=false`) staged for Media Keys Fix SKSE 1.0.2 (Nexus
  92948 file 792882, 2026-08-21, "Supports ... 1.7.104"), which is NOT
  installed - it is the only thing that frees the Windows key, because the
  game's own DirectInput flags (EXCLUSIVE|FOREGROUND|NOWINKEY) eat it, not DT.
  fMaxTime lead closed: SSEDisplayTweaks.log 18:04 shows `[HAVOK] (DYNAMIC)
  fMaxTime=0.00416667-0.0166667`, so Havok is already decoupled from fps.
  (4) 19:05 user scope expansion ("is 120 Hz too high"): DT overlay now sets
  `[Render] FramerateLimit=119` and `[HAVOK] MaximumFramerate=0` per STEP's
  SSE Display Tweaks rule for a 120 Hz panel (original at
  `SSEDisplayTweaks_Custom.ini.bak.v20260901-pre-120hz`; expected log receipt
  `(Max FPS = 119)`); repo overlay copy synced. Morning test checklists sit at
  the top of #149 and #150.
- **Source:** user reports 2026-09-01 (Win key / invisible cursor / clutter
  scatter), team-lead triage dispatch; GitHub issues #149 (window/input) and
  #150 (clutter physics); STEP Guide:Skyrim INI/HAVOK, UESP
  Skyrim:Respawning, epinter/MediaKeysFix src/Main.h, DT window.cpp.
- **Verification:** VERIFIED 2026-09-01 23:11 at config-load level by
  `records/launch-verify-20260901-231117.md` (main menu 31.3s, save 43.5s):
  preflight passed `fMoveLimitMass=0`; `SSEDisplayTweaks.log` 23:10:50
  `[Render] Framerate limit (game): 119` and `[HAVOK] (DYNAMIC)
  fMaxTime=0.00840336-0.0166667 ... (Max FPS = 119)`; `MediaKeysFix.log`
  23:10:31 `SetCooperativeLevel dwFlags found ... setting to 0x06`. In-game
  Windows-key / cursor / clutter checks are still owed (#149, #150, morning
  checklist).

## 2026-09-01 17:40 - LaunchProbe handler-wide bounds hardening (deploy queued)

- **What:** per team-lead audit request, PayloadName (kPreLoadGame/kSaveGame/
  kDeleteGame) now refuses to dereference implausible pointers (<0x10000) and
  caps its scan at min(dataLen, 512) - closes the whole message-data class,
  not just the kPostLoadGame case below. LaunchProbe commit on top of 12ce92e;
  gate PASS. DLL swap is QUEUED: the user is playing (game holds the file
  lock); a watcher swaps mod + staged copies and scrub-cycles Steam when the
  session ends. Until then mods/LaunchProbe runs the 17:27 build (fixed, but
  pre-hardening; its .pdb is momentarily newer than the .dll).
- **Source:** team-lead directive 2026-09-01; crash class from the entry below.
- **Verification:** UNVERIFIED (build+gate only; runtime code path identical
  to the verified 17:28 PASS except the added guards).

## 2026-09-01 17:26 - LaunchProbe kPostLoadGame AV fixed (the 17:12/17:25 crashes)

- **What:** LaunchProbe dereferenced kPostLoadGame's data as `bool*`; this
  SKSE build passes the success bool BY VALUE in the pointer slot, so the
  FIRST successful save load after the #142 fix AV'd at LaunchProbe.dll+2C51
  (17:12:51 and 17:25:41; failed loads pass null and never crashed, which is
  why every earlier run survived). Guard added (values <0x10000 are the flag),
  rebuilt, redeployed to mods/LaunchProbe + staged copy, committed
  (skyrim-tools-source/LaunchProbe 12ce92e, includes the previously
  uncommitted _wfsopen tail-sharing change). New DLL sha256 47cfbe47...b210.
- **Source:** menupilot agent; crash-2026-09-01-17-25-41.log call stack
  (Dispatch_Message -> LoadGame_Hook), records/launch-verify-20260901-172546.md.
- **Verification:** VERIFIED 2026-09-01 17:28 - launch PASS, main menu 31.2s,
  save loaded 35.7s, kPostLoadGame success=1 logged cleanly
  (records/launch-verify-20260901-172851.md).

## 2026-09-01 17:23 - MenuPilot installed: headless in-game menu control

- **What:** new MO2 mod `MenuPilot` (SKSE, source
  skyrim-tools-source/MenuPilot commit 93e5afa, gate PASS): file-driven
  bridge - assistant writes SKSE/MenuPilot/commands.jsonl, plugin consumes it
  exactly once and drives menus (kShow/kHide), Scaleform
  (Invoke/GetVariable/dump) and engine-layer input (ButtonEvent via
  BSInputDeviceManager) on the main thread, logging every step. Inert without
  a command file; panic op; no popups. Driver audit/menupilot.py; docs
  docs/MENUPILOT.md; record records/source-builds/ensrick-menu-pilot.json.
  Purpose: user order - drive game menus without the user clicking; first
  target the Creations store re-download of Farming (#142). Discovery so far:
  runtime registers no "Creation Club Menu"; "Marketplace Menu" = credits
  movie; store surfaces must be driven from the main-menu context
  (records/menupilot-cc-discovery-2026-09-01.log).
- **Source:** user order via team lead 2026-09-01; issue #142 remaining action.
- **Verification:** VERIFIED 2026-09-01 17:28-17:33 - installed for the PASS
  launch above; in-game round-trip proven (Journal open/query/close, 39-menu
  enumeration, Scaleform dumps). input.tap not yet exercised.

## 2026-09-01 ~07:40-07:52 - #142 ROOT CAUSE: truncated ccvsvsse004-beafarmer.bsa; hang fixed

- **What (diagnosis, zero launches):** captured the live 07:35 hang specimen
  from outside with the new `audit/spindump.py` (all-thread RIP sampling +
  handle resolution + minidump). The 3 spinning threads: an engine IO worker
  in an unbounded ReadFile retry loop on handle 0x85C =
  `Data\ccvsvsse004-beafarmer.bsa` (real Steam path, outside the VFS), file
  position pinned 544,816 bytes PAST the 4,194,256-byte EOF; the other two are
  poll loops (Sleep-loop worker + PeekMessage main-thread pump) waiting on it.
  The BSA is truncated at exactly 4MB-48: Steam content_log + mtimes show the
  game process re-downloaded CC content 22:04:31-53 on 08-31 (first-run
  `bUpsellOwned=0` state from the INI reset) and the run-2 kill at 22:04:30
  truncated the last file mid-write. Not in any Steam depot (only the 4
  free-AE creations are), so `steam://validate/489830` ran clean in 25s and
  could not repair it. Full evidence: `records/hang-rootcause-2026-09-01.md`.
- **What (fix):** renamed `ccvsvsse004-beafarmer.bsa/.esl` to
  `.bak.v20260831-truncated`; disabled the two dependent patch plugins via
  MO2Headless (`Lux - Farmer patch.esp`, transaction
  20260901T125112069Z; `Landscape and Water Fixes - Patch - Farming.esp`,
  20260901T125112329Z) and marked both `disabledPlugins` in the ledger with
  re-enable instructions. Preflight clean (224 active plugins).
- **What (confirmation launch 07:52):** kDataLoaded t+24.6s, MAIN MENU
  t+25.2s - the hang is gone after 11 consecutive failures. Save load
  reports success=-1 as expected: the 08-29 save references the parked
  `ccvsvsse004-beafarmer.esl`. Full PASS is blocked until the Farming
  creation is re-downloaded. Record `records/launch-verify-20260901-075219.md`.
- **Pending user action:** in-game Creations menu -> re-download "Farming"
  (restores canonical bsa+esl), then re-enable both patch plugins, clear the
  two ledger `disabledPlugins` entries, delete the `.bak.v20260831-truncated`
  files, and run a full launch_verify PASS. `ccbgssse068-bloodfall.*` /
  `ccbgssse069-contest.*` were rewritten in the same window and survived data
  load; a re-download of those two is cheap insurance at the same time.
- **Source:** #142 phase-2 investigation (machine/VFS agent, user out of
  loop).
- **Verification:** hang fix VERIFIED 2026-09-01 07:52 (main menu 25.2s);
  save-load half FAILED by design until Farming is restored.

---

## 2026-09-01 - #142 bisect rounds 3 + verdict: ALL content exonerated, build restored

- **What (round 3, launch 07:28):** parked the final content slice - 28
  weapons/armor/gameplay smalls plus the 3 generated non-ledger mods (Pandora
  Output - Ensrick regenerated 08-30 19:15, Ensrick - General Compatibility
  Patch, Ensrick - Scoped Werewolf Totem Skull). At that point EVERY mod
  installed or regenerated after the 2026-08-29 17:23 good launch was parked
  (91 active plugins) alongside the 8-DLL wave. The game STILL hung:
  identical signature, hang onset t+16s, exactly 3 SkyrimSE.exe-entry threads
  spinning at 100 percent each, working set flat at 1810MB, skse64.log
  stopping after the last translations line, kDataLoaded never dispatched,
  LaunchProbe seeing only Loading/Mist/Fader/LoadWaitSpinner menus. Records
  launch-verify-20260901-072617.md (round 2) and -072845.md (round 3).
- **Verdict:** the post-08-29 install wave - native DLLs (launch 5) and all
  ~99 content/generated mods (rounds 1-3) - is EXONERATED wholesale. The
  spin-hang plateau (1879/1815/1810MB at 149/106/91 plugins) is nearly
  content-independent. Suspect space is now usvfs/MO2 overlay, Steam overlay,
  profile-level state (plugin order, archives), or machine-side change
  (driver/OS) - a different investigation per the campaign rails; stopped at
  4 launches of the 8 budgeted.
- **What (restore):** applied the pre-campaign baseline snapshot (MO2Headless
  transaction 20260901T122948673Z-7f1c30834ecd): all bisect parks reversed,
  226 active plugins, the 13-mod DLL wave still parked as directed,
  LaunchProbe still installed. Ledger rounds reversed; ~41 ledger notes the
  round tooling had clobbered were restored from git HEAD (notes on the 6
  rows newer than the last ledger commit had none to restore).
  verify_order CLEAN, install_mod --verify 0 problems, preflight clean.
- **Source:** #142 autonomous bisect campaign (team-lead directive, user
  out of loop).
- **Verification:** FAILED x3 as designed evidence (rounds 1-3); final
  restored state UNVERIFIED (no launch can pass until the residual cause is
  found).

## 2026-09-01 - #142 bisect rounds 1-2: content halves

- **What (round 1, launch 07:23):** with the facegen/NPC + city-stack half
  parked (entry below), the game STILL hung - same signature, new location:
  skse64.log stops after the last translation line (now Skyrim Unbound, nwsFF
  parked), no kDataLoaded, LaunchProbe saw only loading-screen menus, ~3 cores
  spinning with working set flat at 1879MB t+38..60s. Record
  records/launch-verify-20260901-072310.md. That half (39 mods, incl. every
  facegen carrier) is EXONERATED as sole culprit; left parked for now.
  (The 07:19 attempt aborted at t+9s: LaunchProbe held its log deny-all
  sharing; probe rebuilt with _SH_DENYWR, launch_watch.probe_events hardened.
  No bisect signal - not counted as a round.)
- **What (round 2):** additionally parked 30 mods - the record/payload-heavy
  half: USMP, SLaWF (15 plugins), ACMOS x2, sound stack (ISC, AOS x2), fix
  floor (UMF, VSM, AMF + Ensrick port, Navigator), Skyland AIO, NotWL family,
  MLO2 x2, ERM x3, Ulvenwald x2, grass stack x6, Ensrick Lux Water CS Patch.
  MO2Headless apply transaction 20260901T122434359Z-19ea1febe33e. 106 active
  plugins; verify_order CLEAN, install_mod --verify 0 problems. Still active
  from the post-08-29 wave: weapons/armor + small-gameplay mods only.
- **Source:** #142 autonomous bisect campaign.
- **Verification:** PENDING - next launch: menu = culprit in round-2's 30;
  hang = culprit among the ~25 weapons/gameplay smalls or outside the ledger.

## 2026-09-01 - #142 bisect round 1: facegen/NPC + city-stack half parked

- **What:** parked 39 mod folders (3DNPC + 6 addons/patches, Cutting Room
  Floor + CRF Semantic Patch, INIGO + 2 patches, Varinia + dialogue fix,
  Nether's Follower Framework, Skyking x4, Whiterun Trellis, Rally's Market
  Stalls x2, Grand Solitude x2, Solitude Docks + NotWL docks patch, Snazzy x4,
  SFCO3 patches, Lux/Lux Orbis patch hubs x5, Collectibles Helper x2, CC Bow
  of Shadows fix) and unstarred 2 cross-half patch plugins (3DNPCNavFix.esp,
  NotWL-CuttingRoomFloor.esp) so Navigator and SLaWF stay active. Applied as
  MO2Headless `apply` transaction 20260901T121850734Z-ff9bf0e8b786 from
  snapshot-derived state; baseline snapshot retained by the bisect agent.
  149 active plugins; verify_order CLEAN, install_mod --verify 0 problems.
- **Source:** #142 autonomous bisect campaign (launch 5 exonerated the DLL
  wave; crash evidence is a facegendata path string - this half contains every
  candidate mod shipping facegen payloads: 3DNPC, CRF, Inigo, Varinia, Grand
  Solitude, Snazzy Solitude, Solitude Docks).
- **Verification:** PENDING - next launch decides. Menu reached = culprit in
  this half; hang = culprit in the landscape/fix-floor/sound/weapons half.

## 2026-09-01 - #142 instrumentation: LaunchProbe installed

- **What:** LaunchProbe 2026-09-01 installed as MO2 mod (priority 225,
  transaction 20260901T121454337Z-a0ba87af72df, ledger row added, sha256
  167051c7eb2cafe5...). One SKSE DLL logging MenuOpenClose + every SKSE
  message with timestamps to SKSE/LaunchProbe.log - the authoritative
  kDataLoaded/MainMenu pass-fail signal launch_verify.py requires.
- **Source:** #142 bisect campaign; built by the watchdog agent from
  C:/Users/danjo/source/repos/skyrim-tools-source/LaunchProbe, staged at
  records/source-builds/launch-probe/, SKSE-gate PASS.
- **Verification:** PENDING - validated implicitly by the round-1 launch (if
  it malfunctions it gets removed and the campaign falls back to the
  skse64.log translations-line criterion).

## 2026-09-01 - #142 corruption bisect: eight-DLL wave parked

- **What:** parked 13 mod folders (FSMP AVX-512, VHR SMP + NPCs + Ensrick facegen
  overlay, Community Shaders AIO source build, SSE Display Tweaks Official +
  Ensrick config overlay, SkyParkour v3 SPPF + Pandora cache, Simple Dual
  Sheath, MCM Helper, Sound Record Distributor, QuickLoot IE rebuild) and
  unstarred their 5 plugins. Content mods untouched. 226 active plugins.
- **Source:** docs/CRASH-2026-08-31-DEEP-DIVE.md + issue #142 - heap corruption
  during menu-phase load (facegendata path string over pointer data, engine
  code, job thread); this is the recommended single test that splits the
  hypothesis space. Wave = every new/replaced native DLL since the last
  VERIFIED launch (2026-08-29 17:23).
- **Verification:** PENDING - next launch is the test. Clean = corruption is in
  the wave, bisect in 2-3 launches. Hung/crashed = all new native code
  exonerated in one shot.

## 2026-08-31

### 2026-09-02 - Distribution doctrine for Ensrick overlays (docs + tracking, no build change)
- **What:** every `Ensrick - *` overlay now carries a distribution class (distributable / recipe / local-only) - section added to `docs/PATCH_INTENTS.md`; classification sweep of all 18 overlays running, results land on ledger rows + `records/ensrick-overlay-distribution-2026-09-02.md`.
- **Source:** user, "we're making a modlist to share, so I take it this has to be packaged as a patch" (re #159 signpost env-mask fix). Issue #160.
- **Verification:** none required - no profile, plugin, INI or asset changed.

### Verification launch wave, 22:00-22:47 - FAILED, three distinct signatures

- **What:** repeated attempts to launch and load the save. MO2 usvfs logs show
  six game sessions between 22:02 and 22:47
  (`mo2-instances/skyrim-se/logs/usvfs-2026-09-01_03-02-52` through
  `_03-47-19`). No attempt loaded the save.
  1. **FAILED - OAR load hang:** Open Animation Replacer 3.2.0 passes the SKSE
     timestamp gate, then hangs inside its own load with a popup; every SKSE
     plugin after it in load order never loads. Evidence: skse64.log
     2026-08-31 22:00, `threaddump-2026-08-31-22-13-15.log`, issue #140.
  2. **FAILED - INI first-run reset:** game came up 1920x1080 windowed on the
     4K panel with the AE upsell prompt; Skyrim had rewritten SkyrimPrefs.ini
     because MO2 was not managing INIs (`LocalSettings=false`). Evidence:
     `SkyrimPrefs.ini.bak.v20260901-firstrun-reset` (22:07), issue #98,
     `docs/INI_AND_PROFILE_STATE.md`.
  3. **FAILED - access violation at 85s uptime:** EXCEPTION_ACCESS_VIOLATION at
     SkyrimSE.exe+0E128B2 (JobListManager::ServingThread on stack). Evidence:
     `crash-2026-08-31-22-42-16.log`.
- **Source:** user-directed verification launches.
- **Verification:** FAILED (all three signatures above). The whole 08-29 to
  08-31 pile below is suspect until bisected.

### Mitigations during the launch wave

- **What:** Open Animation Replacer re-parked (ledger transaction
  `20260901T030136569Z`, verify_order clean at 231). Gate-pass alone is now
  known to be necessary-not-sufficient for unparks.
  **Source:** issue #140 (also invalidates the gate-only unpark basis of
  #83/#84/#85).
  **Verification:** UNVERIFIED (a later launch with OAR parked still crashed).
- **What:** SkyrimPrefs.ini restored from the `.base` snapshot;
  `LocalSettings=true` set in `profiles/Default/settings.txt`; deliberate-key
  table and before/after-launch checks written down.
  **Source:** issue #98; user directive "Since AI is managing MO2 I want you
  and Sol to never forget a single thing like ini files";
  `docs/INI_AND_PROFILE_STATE.md`.
  **Verification:** UNVERIFIED.

### Installs and repo work earlier on 08-31

- **What:** Skyrim Landscape and Water Fixes v10.6 installed, 15 plugins
  (19:29; ledger 2026-09-01T00:29Z).
  **Source:** fix-floor/survey lineage (`docs/ECOSYSTEM-SURVEY-2026-08-30.md`,
  issue #107 family); fomod plan `records/fomod-plans/26138-slawf.json`. **No
  issue or user line names this install specifically - source partially
  inferred (process hole).**
  **Verification:** UNVERIFIED.
- **What:** Bounded Encounters observe-only alpha: repo-side plugin project,
  commits 2dbea66..85de98f on main, tag `bounded-encounters/v0.1.0-alpha.1`,
  PRs #135/#136/#137 merged, #138/#139 open. Not installed into the profile;
  no game-state change.
  **Source:** design issue #133; user direction on bounded scaling.
  **Verification:** n/a (not in profile).
- **What:** `docs/NEW-LANDS-SURVEY-2026-08-31.md` added (research only).
  **Source:** research-newlands agent.
  **Verification:** n/a (no state change).

---

## 2026-08-30 late evening, 21:58-23:46 - grass and fix-floor wave

- **What:** smoke-test plan for the whole 08-30/31 wave
  (`docs/SMOKE-TEST-2026-08-31.md`, commit 3f434c7).
  **Source:** session docs work following the install wave.
  **Verification:** n/a (doc).
- **What:** grass stack installed: DrJacopo's 3D Grass Library meshes, Freak's
  Floral Fields 3.2.3 Realistic Regional Mix (7 plugins) + Ensrick texture
  cap, Freak's Floral Solstheim, Freak's Floral Veil, Landscape Fixes For
  Grass Mods. Commits 4347647, 60be49c.
  **Source:** issue #112 (empty grass slot);
  `records/freaks-floral-fields-3.2.3-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** DLL-free fix floor installed: Unofficial Material Fix 1.18.0,
  Vanilla Script MicroOptimizations, Assorted Mesh Fixes 0.139.3 + Ensrick SE
  mesh port, Navigator navmesh fixes (4 plugins), USMP 2.6.8b.
  **Source:** issue #107 (fix-floor batch from survey);
  `docs/ECOSYSTEM-SURVEY-2026-08-30.md`; USMP install opened #134 (Lux Water
  CS patch must be regenerated).
  **Verification:** UNVERIFIED.
- **What:** issues #130-#134 opened (Fuz Ro D-oh gate failure, deflate64
  install failure, verify false-positive on disabled plugins, bounded-scaling
  design, Lux Water CS regen).
  **Source:** session triage during the wave.
  **Verification:** n/a (tracking).

## 2026-08-30 evening, 16:22-18:32 - landscape, lighting, hair, movement

- **What:** base texture/landscape foundation: Skyland AIO 1K + full Nature of
  the Wild Lands 3.14 + active-profile patches + Solitude Docks patch +
  Ensrick texture cap. Commit 0aca55b.
  **Source:** user decision closing issue #88 (base texture and landscape
  stack); `records/skyland-notwl-foundation-install-2026-08-30.md`; follow-up
  tracking #119, #120.
  **Verification:** UNVERIFIED.
- **What:** Modern Lighting Overhaul 2 (MLO2) 5.4.1 + Ensrick foundation
  config adopted as the Lux lighting foundation. Commit 01387c8.
  **Source:** `records/mlo2-5.4.1-2026-08-30.md`; smoke test tracked as #121.
  **Verification:** UNVERIFIED.
- **What:** Vanilla Hair Remake SMP + NPCs file + Ensrick NPC compatibility
  overlay + FSMP 4.1.1 (hair physics dependency). Commit f526268.
  **Source:** research-hair agent;
  `records/vanilla-hair-remake-smp-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** ERM - Enhanced Rocks and Mountains 1.1.2 + Fix and Addon 6.4 +
  DynDOLOD add-on; layered-landscape decision recorded (commit 36306a2).
  **Source:** issue #122 (mountain/rock slot); conflict finding filed as #127
  (ERM outranks Lux on 28 ice-cave meshes).
  **Verification:** UNVERIFIED.
- **What:** SkyParkour v3 3.6.3 + Pandora animation cache; Pandora headless
  fork built and run so SkyParkour behaviors generate (`run-pandora.cmd`,
  commit 1a855dc).
  **Source:** issues #128 (closed by the Pandora run), #129 opened for
  Animation Queue Fix; fork-pandora / push-pandora agents.
  **Verification:** UNVERIFIED.
- **What:** controlled tree blend: Traverse the Ulvenwald 3.3.2 assets + Tree
  Diversity Project (NotWL base, Ulvenwald mix). Commit d5451ff.
  **Source:** `records/notwl-ulvenwald-tree-diversity-2026-08-30.md`; tree
  decision lineage in
  `records/tree-overhaul-and-morthal-cypress-audit-2026-08-29.md`.
  **Verification:** UNVERIFIED.
- **What:** issues #119-#129 opened (texture-cap overlay tracking, mip chains,
  MLO2 smoke test, mountain slot, fire/spell/creature adoption decisions,
  Eldergleam clusters, ERM/Lux ranking, Pandora, AQF rebuild).
  **Source:** survey-ecosystem + session triage.
  **Verification:** n/a (tracking).

## 2026-08-30 afternoon, 12:17-14:53 - reconciliation and clothing

- **What:** ledger re-registration of three pre-existing source builds:
  Community Shaders AIO 1.7.99 source build, Ensrick Lux Water CS Patch,
  QuickLoot IE Ensrick 1.7.99 (all stamped 17:17:26Z in the same second).
  Commit 668c4b9 "Record current installed foundation state".
  **Source:** ledger reconciliation (#102). **The stamps are registration
  time, not change time - no transaction trail for the underlying files
  (process hole).**
  **Verification:** UNVERIFIED (builds predate the checkpoint but their ledger
  rows are new).
- **What:** Better Fur - Fine Clothes + Merchant's Hat + Ensrick CBBE-HIMBO
  refit.
  **Source:** user explicitly kept Nexus 69240 and 70589
  (`docs/AGENT_WORK_QUEUE.md` keep-review coordination);
  `records/better-fur-jg1-adoption-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** Ensrick - Collectibles Helper USSEP Forward overlay plugin
  generated and installed.
  **Source:** issue #92 (forward USSEP over Collectibles Helper on twelve
  records).
  **Verification:** UNVERIFIED.
- **What:** issues #106-#118 opened (Solitude confirmation, fix floor,
  ISC-SRDified, survey outliers, DLL-gate batch, UI layer, grass slot, perk
  slot, CoMAP, Synthesis/PGPatcher chain, per-city plan, waterfalls,
  gitignore/records visibility).
  **Source:** survey-ecosystem + survey-standards digests
  (`docs/ECOSYSTEM-SURVEY-2026-08-30.md`,
  `docs/STANDARDS-DIGEST-2026-08-30.md`).
  **Verification:** n/a (tracking).

## 2026-08-30 midday, 14:52 commit wave - process audit and tooling

- **What:** eleven commits (fc4835e..cb40cf2): snapshot-driven LOOT sort +
  SKSE gate checker tooling, curation-state policy, equipment intake policy,
  profile-state ledger docs, LOOT rules, research records, werewolf-totem
  overlay recipe, CRF semantic patch source, vendor-integrity/display/water
  records, ecosystem survey + standards digest, process-audit findings F0-F16.
  **Source:** audit-process agent (`docs/PROCESS-AUDIT-2026-08-30.md`);
  findings filed as issues #97-#105.
  **Verification:** n/a (docs/tools; no profile change).

## 2026-08-30 morning, 09:44-11:19 - Solitude, sound, map, companions

- **What:** Cutting Room Floor 3.1.26 + CRF semantic patch (spriggit source,
  commit 19875a9) + Interesting NPCs CRF patch.
  **Source:**
  `records/cutting-room-floor-3.1.26-compatibility-audit-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** INIGO 2.4C + Bloodchill Manor patch + Official Patch SE.
  **Source:** `records/inigo-1461-2026-08-30.md`; mesh-format caveat filed as
  issue #77.
  **Verification:** UNVERIFIED.
- **What:** Baltimore Weapons; Vikings Weaponry SE + Ensrick mesh port +
  texture cap.
  **Source:** `records/baltimore-weapons-29612-2026-08-30.md`,
  `records/vikings-weaponry-14409-2026-08-30.md` (keep-review equipment
  intake).
  **Verification:** UNVERIFIED.
- **What:** Simple Hunting Overhaul 1.16 + Bruma patch + Dynamic Activation
  Key (dependency).
  **Source:** `records/simple-hunting-overhaul-95943-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** world map: A Clear Map of Skyrim and Other Worlds 4.0 (4 plugins)
  + Water for ENB patch.
  **Source:** research-worldmap agent; `records/acmos-56367-2026-08-30.md`;
  known limitations filed as #81 (LOD32 at DynDOLOD time) and #82 (water
  patch sort order, currently inert).
  **Verification:** UNVERIFIED.
- **What:** sound stack: Sound Record Distributor, Immersive Sounds
  Compendium 3.0, Audio Overhaul for Skyrim SE 4.1.3, AOS-ISC integration.
  **Source:** research-sound agent; `records/sound-stack-2026-08-30.md`;
  USSEP-reversion caveat filed as #89, ISC-SRDified follow-up as #108.
  **Verification:** UNVERIFIED.
- **What:** MCM Helper 1.6.3 installed (unparked on gate pass).
  **Source:** issue #83; `records/mcm-helper-1.6.3-2026-08-30.md`. Gate-only
  basis invalidated later by #140; needs launch re-validation.
  **Verification:** UNVERIFIED.
- **What:** unparks on gate pass alone: Open Animation Replacer (#84),
  Crafting Recipe Distributor (#85).
  **Source:** issues #84, #85 (both closed on the gate result). OAR was
  re-parked 2026-08-31 after #140; CRD still needs launch re-validation.
  **Verification:** OAR FAILED (#140); CRD UNVERIFIED.
- **What:** Simple Dual Sheath 1.5.9 installed.
  **Source:** issue #78 (closed - provenance decision); audit-dualsheath
  agent.
  **Verification:** UNVERIFIED.
- **What:** Scale Nord Armor + Ensrick texture cap + Bloodskal static-glow
  overlay.
  **Source:** compare-41118 agent; distribution follow-up filed as #96.
  **Verification:** UNVERIFIED.
- **What:** Solitude city stack: Whiterun 3D Trellis AIO, Rally's Market
  Stalls + hotfix, Grand Solitude + patch collection, CC Bow of Shadows fix,
  Solitude Docks Updated, Snazzy Location Resources, Snazzy Solitude
  Separated Houses + patch collection, SFCO3-BOS + patch collection, Lux
  Patch Hub + Solitude Docks patch, Lux Orbis patch hubs, Collectibles
  Helper.
  **Source:** issue #106 (Solitude stack as the city decision);
  `records/solitude-city-interior-cell-matrix-2026-08-30.md`,
  `records/solitude-trellis-stalls-installation-2026-08-30.md`,
  `records/city-interior-layering-direction-2026-08-30.md` (commit 30c4679).
  **Verification:** UNVERIFIED.
- **What:** issues #77-#96 opened (Inigo meshes, dual sheath, Light Placer
  re-check, water effects, ACMOS, unparks, artifacts design, SKSE rebuilds,
  texture/blood/landscape decisions, mod-install --replace defect, USSEP
  forwards, Steel Plate textures, IED block, cloak tracking, Scale Nord
  distribution).
  **Source:** morning audit + intake sessions (audit-* / research-* agents).
  **Verification:** n/a (tracking).

---

## 2026-08-29 evening, 17:40-23:36 - keep-review equipment wave

- **What:** commit 2809071 "docs: track new Skyrim playtest requirements".
  **Source:** user playtest feedback after the 17:23 session.
  **Verification:** n/a (doc).
- **What:** keep-review ascending pass installs (Claude cursor opened at the
  oldest keep, Nexus 62271): One-handed warhammers (install-62271), Steel
  Plate Armors + HD textures (install-154073; 4K body-texture question filed
  as #93), Lunar Guard Armor (install-75349), Sagittarius Real Bows
  (install-109490), Bloodskal Blade 4 + No Glow variant (disabled) + Ensrick
  texture cap (install-120399), Akatosh's Talon + Chitin Bow
  (install-121553-162825), Quicksilver's Sword Pack + Ensrick texture cap.
  **Source:** `docs/AGENT_WORK_QUEUE.md` keep-review coordination + the named
  install agents; per-mod records in `records/`.
  **Verification:** UNVERIFIED.
- **What:** Ring of Khajiit replacer installed.
  **Source:** `docs/KEEP_REVIEW.md` decision ledger. **Thinnest trail of the
  wave - no dedicated record file (process hole).**
  **Verification:** UNVERIFIED.
- **What:** Skyking Signs + Unique Signs + Bruma patch + Interesting NPCs
  patch.
  **Source:** `records/skyking-signs-2026-08-29.md`.
  **Verification:** UNVERIFIED.
- **What:** High Poly 3D Wolf Skull werewolf totem replacer installed
  DISABLED pending the overlay build.
  **Source:** overlay recipe committed as 8d51193.
  **Verification:** UNVERIFIED (disabled; inert by design).
- **What:** Varinia companion 1.1.0 + Ensrick six-PEX dialogue fragment fix
  overlay.
  **Source:** `records/varinia-148853-2026-08-29.md`,
  `records/varinia-private-fragment-fix-2026-08-30.md` (commit 5cec4ce);
  upstream report drafted.
  **Verification:** UNVERIFIED.
- **What:** SSE Display Tweaks migrated to official 0.5.25 + Ensrick
  configuration overlay (borderless/fullscreen mirror, LockCursor=true - the
  LockCursor choice is Sol's and contradicts an earlier user complaint; ask
  before flipping, per `docs/INI_AND_PROFILE_STATE.md`).
  **Source:**
  `records/sse-display-tweaks-official-migration-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** screen-effect QoL trio: Disable Screen Blood, No More Blur on
  Hit, 3rd Person Camera Stagger Remover.
  **Source:** `records/blood-visuals-audit-2026-08-30.md` lineage; the larger
  blood-system decision remains open as #90.
  **Verification:** UNVERIFIED.
- **What:** Interesting NPCs 4.5 + 4.54 update + ILS freeze fix + Abandoned
  Prison combat fix + Cat and Mouse script fix + Survival Mode patch +
  Nether's Follower Framework 2.8.6b.
  **Source:**
  `records/hit-effects-and-interesting-npcs-install-2026-08-30.md`; health
  audit `records/interesting-npcs-party-banter-health-2026-08-29.md`.
  **Verification:** UNVERIFIED.

---

## 2026-08-29 17:23 - checkpoint launch (last known good)

- **What:** launch of the pre-wave profile: main menu reached, save loaded.
  Earlier failure that afternoon (`crash-2026-08-29-16-46-11.log`) was
  resolved before this launch; a play session followed (saves written 18:40).
- **Source:** user session.
- **Verification:** VERIFIED 2026-08-29. **This is the baseline every entry
  above stacks onto. Nothing after this line has been verified.**

---

## Backfill notes - process holes found during reconstruction

1. `mo2-instances/skyrim-se/.mo2-headless-journal/` does not exist; actor
   attribution for ledger transactions comes only from timestamps and agent
   names, not a journal.
2. Three ledger rows (CS AIO build, Lux Water CS patch, QuickLootIE) carry a
   same-second registration stamp, not a true change time.
3. The SLaWF v10.6 install has a fomod plan but no issue or user line naming
   it; its source is inferred from the #107 survey batch.
4. Ring of Khajiit has a Keep decision but no per-mod record file.
5. Launch attempts were not first-class events anywhere; the three 08-31
   failure signatures had to be reconstructed from skse64.log, a threaddump,
   a crash log, usvfs logs, and issue text. This changelog's Verification
   field is the fix.
6. `records/installed-mods.json` and several docs sit modified/untracked in
   the working tree; ledger state and git state can drift (issue #118 is the
   standing example).
