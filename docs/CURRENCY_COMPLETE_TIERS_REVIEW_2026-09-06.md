# Currency Complete Tiers — Independent Static Review

**Date:** 2026-09-06
**Scope:** Read-only review of the full-tier candidate in this worktree. This is a static design/source review, not runtime acceptance or release approval.

## Verdict

The current ownership model is internally coherent: Base Object Swapper (BOS) owns placed loose `Gold001` presentation, the native bridge owns eligible actor/container normalization before loot is presented, and the packaged Container Distribution Framework (CDF) files are inert compatibility masks. No static defect was found that would knowingly reroll an already minted physical coin, double-convert a C.O.I.N coin, or overlap the frozen denomination FormIDs.

Runtime behavior remains unverified. Final generated plugins and their winning records must be audited after generation, followed by disposable-save tests before this can be treated as gameplay-ready.

## BOS loose-coin routing

Reviewed inputs:

- `mods/currency-integration/generate_bos.py`
- `mods/currency-integration/bos-location-roots.json`
- `mods/currency-integration/package/*_SWAP.ini`

The package contains 24 BOS files: 16 active rule files and 8 inert compatibility masks. The active scope is the default route, 14 prioritized regional/ancient routes, and the Gyldenhul quest exception. The root catalog is explicitly marked `reviewed-source-roots/runtime-unverified`; it records 1,639 locations across 349 inspected plugins, but it does not prove the player's observed runtime location chain.

For raw vanilla `Gold001`, each active route implements the intended exact value-tier distribution: 75% copper, 20% silver, and 5% gold. Multi-face routes subdivide each tier with cumulative `chanceS` bins. Rows are emitted in reverse order because BOS evaluates applicable rows in reverse, while the shared reference seed keeps the tier and face decision correlated for the same placed reference.

The 55 already-physical currency forms are only mapped within their existing value tier. This is essential: dropping and picking up an existing copper, silver, or gold coin cannot reroll it into a different denomination and inflate or destroy value. Identity winners use `scale(1)` to reserve precedence without changing the authored reference scale.

The Gyldenhul exception restores the intended Septim route and reserves the relevant purse references. Default rules exclude Gyldenhul. Static generated structure is correct; filename precedence and observed location matching still require runtime confirmation.

The eight inert BOS compatibility masks are:

- `C.O.I.N_SWAP.ini`
- `C.O.I.N. - Beyond Skyrim Patch_SWAP.ini`
- `C.O.I.N. - The Cause Patch_SWAP.ini`
- `DominionUsesSancar_SWAP.ini`
- `MorrowindUsesDrams_SWAP.ini`
- `WindhelmUsesUlfrics_SWAP.ini`
- `zz_Ensrick_Currency_80_Regional_SWAP.ini`
- `zz_Ensrick_Currency_90_Ancient_SWAP.ini`

## CDF ownership and compatibility masks

All 14 packaged currency CDF JSON files were inspected and contain zero rules (`{"rules":[]}`). This is deliberate and necessary. Legacy CDF distributions could mutate inventories independently of the native bridge, including persistent, quest, or storage objects, and could run at a different point from QuickLoot/activation accounting. Making these files inert leaves one normalization owner for actors and containers and avoids duplicate or order-dependent conversion.

The masked families cover C.O.I.N, EC Drakr/Dram/Mede/Ohzer/Oshka/Septim/Ulfric/Varken, Morrowind/Windhelm/Dominion, Bruma Ayleid/Varken, and Kolbjorn distributions. Typed purse plugins, rather than CDF, own the FLOR purse budgets.

## C.O.I.N auto-exchange race

C.O.I.N's `DES_CoinExchanger.psc` only auto-exchanges a picked-up base item when it lacks the configured `DES_NoExchange` keyword. Inspection of the released C.O.I.N plugin found all nine C.O.I.N coin forms carrying `VendorItemNoSale` (`0x0FF9FB` in `Skyrim.esm`), which is the keyword used by that property.

The generator preserves/adds `VendorItemNoSale`, and the native bridge rejects a canonical denomination or alias unless its value is exact and the same no-sale keyword is present. Consequently, native-recognized physical coins remain protected even during the brief interval in which the Papyrus helper may retry setting `autoExchange=false`; the reviewed path does not double-account those coins.

This conclusion is static. Runtime acceptance must still toggle/reset C.O.I.N settings and confirm that no later MCM/script initialization re-enables exchange for the integrated forms.

## Actor/container safety boundary

The native policy rejects the player, persistent references, quest objects, quest aliases, vendors, teammates, unique actors, essential/protected actors, and all owned or faction-owned containers. Eligible actors must be dead, generic, and respawning; eligible containers must be respawning and unowned. The runtime denylist adds 12 explicit protected references.

The owned-container exclusion was checked against `Skyrim.esm` source records:

- 251 respawning container base records were identified.
- 451 placed references using those bases were owned.
- Only 19 had a bandit-named owner, and all 19 used `MS07BanditFaction` (`0x088EE4`).
- Representative records were `0x088E4D` (`TreasBanditChest`) and `0x08E700` (`TreasBanditChestEMPTY`) in Icerunner exterior/location space, plus `0x0979C8` (`TreasSatchel`) in Katariah space.

Those examples belong to quest-associated Icerunner/Katariah spaces and are not evidence that a broad generic hostile-faction exception is safe. Retaining the conservative owner rejection is correct for this candidate. If a missed ordinary hostile container is later proven, add only a reviewed explicit reference allowlist; do not relax the rule for an entire faction.

**Limitation:** this count examined `Skyrim.esm` source records, not fully resolved winning placed references across the complete 349-plugin load order. It therefore documents the safety rationale but cannot claim exhaustive container coverage.

## FormID range review

No additional static overlap was found in the owned ranges:

- Main purse DAG: `0x990–0x9FF` and `0xA16–0xF3F`, exactly 1,434 nodes.
- Frozen denomination IDs deliberately skipped by that DAG: `0xA00–0xA15`.
- Static main-plugin records occupy earlier disjoint allocations, including runtime/route records near `0x800`, modern denominations at `0x820–0x82B`, and helper purse families at `0x900–0x980`.
- The regional companion uses its own plugin namespace: FLOR records at `0x800–0x80E`, selectors at `0x810–0x81E`, and terminal graph records beginning at `0x820`.

The generator assertions for the `0xA00` jump and final `0xF40` cursor are appropriate. This is a source-range review, not proof of the final binary output; generated plugins must be enumerated before release.

## Superseded 199-file static release gate

This section records the original 199-file review. Its archive identity is
superseded by the 201-file compatibility correction below; the unchanged
ESP/DLL/PEX/assets evidence remains applicable.

The completed private candidate is a **static GO for commit and local serial
installation**. This is not gameplay acceptance.

- Archive: `Ensrick-Regional-Currency-Integration-0.4.0.zip`, SHA-256
  `1A403D0121A3672042A82F766DB54E70D58E2958F5D94367C3DB18C7E7628852`,
  33,319,850 bytes.
- Closure: exactly 199 archive file entries and 199 package files, with zero
  missing, extra, duplicate, case-colliding, unsafe-path, zero-byte, or
  content-hash-mismatched entries. All entries use the same fixed timestamp.
- Main ESP: both generator runs and the packaged file are byte-identical at
  SHA-256 `BEB89F2A7FF52B06F5CCE1E81CD6C6150F7751B55910FF0415DD705711957F05`.
- Regional-purse ESP: both generator runs and the packaged file are
  byte-identical at SHA-256
  `873A1DD331270B0E76EBB28209F8D6D0378D05105CFAD3EABD4A98FA968A8B61`.
- Native DLL: the package and deterministic native-build receipt agree on
  SHA-256 `879C230DF742570E2B218B25B6DD0E0AE2C073AA9F4E45621CE107E7720446C6`.
- `validate.py` passed. The four currency unit-test groups passed with
  19, 19, 9, and 14 tests. A fresh invocation of the independent purse binary
  gate passed for 405 owned records (15 FLOR and 390 reachable LVLI), all 15
  purse bases, and exact `4/5` canonical plus `1/5` single-break outcomes.
- The line-ending-sensitive BSA reader now has raw SHA-256
  `56B02A5EA17593F5262D602DD2D9037F3B29C334F91B51E3961043E6A6FA8E3B`,
  matching its pinned canonical-LF input. `git diff --check` reports no error.
- No generated ESP, DLL, PEX, NIF, DDS, SEQ, or ZIP is tracked by Git. The
  archive and licensed derivative tier assets remain ignored private outputs.
  No credential value was found in the reviewed change set.

Three nonblocking publication/telemetry debts remain:

1. `DEPENDENCIES.txt` names the four content foundations, while the README and
   manifest also identify the framework/runtime dependencies. Before a
   standalone public release, consolidate exact supported versions and links
   for BOS, KID, CDF, SkyPatcher, Inventory Interface Information Injector,
   SKSE, and the optional Quick Loot integration.
2. Asset/native receipts and the underlying recipe retain absolute local build
   and provenance paths. They contain no credential and `rebuild.py` replaces
   operational paths from explicit arguments, so this does not block the local
   package. Sanitize or label these paths as builder-local provenance before
   presenting the source release as portable professional documentation.
3. `native/src/Plugin.cpp` logs native version `0.1.0`, while the native CMake
   project is `0.2.0` and the integration package is `0.4.0`. This is cosmetic
   telemetry drift, but should be aligned before a public release.

The earlier Copper Septim concern is not a current artifact defect. The final
candidate-winner scan passed across the 349-plugin active profile with explicit
candidate-main substitution and companion insertion (350 simulated entries),
covering all 55 physical forms. The 54 emitted forms win from the main ESP. The
source-only `000B6D:exchangeCurrency_enhanced.esp` winner is ECE itself (provider
SHA-256 `3DAAF50FB3FBA43644B7AB7E47987350F5F486F9E5D8D0A92E606E6CFF893592`)
and has the approved Copper Septim name, value 1, `VendorItemNoSale`, and model;
the raw `Clutter\Coin01.nif` path is equivalent under the gate's sole optional
`Meshes\`-prefix normalization. No later MISC override exists. The independent
winner gate has SHA-256
`7837C3B3BD523321F2C94E1C99D039C598D59EDF5EC6F3F5F6511122E4B0FE3D`
and its nine tests pass. Its scope is simulated static plugin winners, not
installed SKSE, SkyPatcher, or asset winners. The installed winning-file gate
must therefore repeat the check after deployment; a future profile that adds a
later override must fail closed rather than rely only on the named ECE source
record.

## Superseding 201-file static release gate

The corrected candidate is a **static GO for commit and local serial
installation**. This supersedes the 199-file archive identity above; it does
not grant gameplay acceptance.

The installed ECE source files were compared directly with the two packaged
same-path overrides. The original `ECE_regionalCurrencies.ini` contained 11
active physical-coin rows, each assigning value zero. Its override is now
comment-only (zero active rows), SHA-256
`ABCDABB6DA16E12354B69B62C9E2CA29F0470BAB188B76D6181773798ED8DF25`.
The original `ECE_septims_100.ini` contained three physical Septim edits,
including Silver Septim value 25. Its override removes those three rows while
preserving byte-for-byte the `Gold001` value-1/weight-0/name-`Septim` backend
row and all four plural-display rows, SHA-256
`D5A26D41EF4EE9D1A00C11FC8C189DF7A32E01BFF8FD922D1931C5C755DA60A0`.
Because these are same-relative-path MO2 winners, no SkyPatcher directory
iteration order is required once the integration mod's file priority is
verified after installation.

- Archive: `Ensrick-Regional-Currency-Integration-0.4.0.zip`, SHA-256
  `AC738CCA9AD67ECFAC109B7A85D73C979985F8BBC3311A7015D165C3C4F8F86A`,
  33,320,658 bytes.
- Independent current closure: exactly 201 archive entries and 201 package
  files, with zero missing, extra, content/size-mismatched, duplicate,
  case-colliding, unsafe-path, or zero-byte entries. Every entry has the fixed
  timestamp `2000-01-01T00:00:00`.
- The archive-refresh receipt, SHA-256
  `4B580F40E6BFE2920F8930D70AC03F9066DDDD12A75A2585A3A43582830A2432`,
  records two byte-identical archive builds and an exact comparison with the
  prior 199-entry inventory: precisely the two masks were added; zero prior
  entries changed or were removed.
- The main ESP remains
  `BEB89F2A7FF52B06F5CCE1E81CD6C6150F7751B55910FF0415DD705711957F05`;
  the companion ESP remains
  `873A1DD331270B0E76EBB28209F8D6D0378D05105CFAD3EABD4A98FA968A8B61`;
  and the native DLL remains
  `879C230DF742570E2B218B25B6DD0E0AE2C073AA9F4E45621CE107E7720446C6`.
- The exact-byte mask validator, all eight new mask regression tests, the full
  currency release validator, and `git diff --check` pass locally. Package
  files are covered by the repository's `-text` attribute, preventing checkout
  line-ending conversion from invalidating the byte-pinned masks.

The exact correction commit
`a79d2d5033423347fc7bb1e453ae8847d09600c3` passed GitHub workflow `Check`,
run `34050098303`, including the new mask suite and actual currency
policy/distribution step. The subsequent post-install static audit also passed:
all 201 archive files match both the installed integration folder and effective
MO2 winners; both same-path masks win from the owned integration mod; and all
55 physical forms have exactly one classified value/name/weight writer. Its
active SkyPatcher MISC row counts are regional 0, backend/display 5, ancient 0,
modern 52, and Septim 3. The canonical evidence is
`records-work/currency-040-deployment/currency-effective-payload.json`, SHA-256
`C1B10C52C71B467312E91784806566303990AB5527E542C528D8B5EBE1E93EC5`.
The reviewed DLL, configuration, and four compiled scripts were unchanged.

This closes the static candidate-winner and installed-file-priority gates. The
three publication/telemetry debts already listed above remain open. No game was
launched for this review, so SKSE/SkyPatcher execution and the required
disposable-save matrix remain runtime acceptance gates.

## Required runtime acceptance

Use a fresh disposable save and preserve logs for each test:

1. Sample placed vanilla `Gold001` in each active route and confirm the observed 75/20/5 value-tier distribution, correct face family, default fallback, and Gyldenhul exception.
2. Drop and repick every physical copper/silver/gold form and confirm its value tier never changes.
3. Verify every required regional/ancient design exists in copper, silver, and gold, with correct model, name, value, weight, keyword, and plugin owner.
4. Exercise all 42 purse FLOR bases: 27 existing bases and 15 owned helper bases in the separate regional companion plugin. Evaluate every source budget independently, then confirm the main owned terminal DAG preserves each total purse value before its final physical-face selection; no per-leaf rounding or multiplication is acceptable.
5. Inspect eligible dead NPCs and unowned respawning containers through QuickLoot and ordinary activation. Normalization must complete before display/transfer, with no duplication or value loss.
6. Save/reload, change locations, respawn cells, and repeat looting to prove idempotence and stable regional routing.
7. Confirm player storage, vendors, persistent/unique/quest references, owned containers, and the 12 denied references remain untouched.
8. Reset/toggle C.O.I.N MCM options and restart the game to confirm auto-exchange cannot reclaim integrated physical coins.

Until these tests and a final plugin/FormID/master audit pass, the candidate should remain **runtime-unverified**.
