# Apocrypha Ohzer and Varken integration policy

**Audit date:** 2026-09-03

**Runtime:** Skyrim `1.7.104.0`

**Status:** Ohzer mapping and transaction handling are installed in Ensrick
Regional Currency Integration v0.2.4 and passed the configuration/save-load
smoke gate; Varken is deferred under #210 pending implementation and runtime
tests.

**Tracking:** master [#207](https://github.com/Ensrick/skyrim-mod-assistant/issues/207);
deferred Varken child [#210](https://github.com/Ensrick/skyrim-mod-assistant/issues/210).

## Decision

- **Ohzer is Apocrypha's currency.** Assign ECE's `isOhzerMoney` keyword to
  the complete ten-record `Dragonborn.esm` Apocrypha location tree.
- **Varken is Dremora currency, not a second Apocrypha currency.** Do not
  assign `isVarkenMoney` to any `Dragonborn.esm` location at this stage.
- Ohzer location classification is implemented with a pack-owned Keyword Item
  Distributor configuration. The v0.2.4 ESPFE also provides the owned runtime
  quest/handler required for ECE transactions; no Bethesda location record is
  overridden.
- Treat Varken as two later workstreams: constrained Dremora/conjurer loot and
  an actor-aware Black Market merchant adapter. The latter requires an owned
  plugin and original source; it should ship as an ESP-FE after FormID
  compaction and conflict review.

This policy deliberately rejects the tempting shortcut of marking all of
Apocrypha as both currencies. Apocrypha is Hermaeus Mora's realm, while the
Varken assets and their original distribution are explicitly Dremora-themed.
The Black Market merchant can also be summoned anywhere, so his currency
cannot be selected reliably from the player's current location.

## Audited stack and dead-hook diagnosis

The following installed content was inspected directly rather than inferred
from filenames or Nexus descriptions:

| Component | Audited version | Relevant evidence |
|---|---:|---|
| Exchange Currency Enhanced | 4.1.1 | Defines the currency keywords and consumes them from its BOS, CDF, and Papyrus paths |
| C.O.I.N. | 3.5.3 | Supplies the currency integration base used by ECE |
| M.I.N.T. | 1.0.6 | Supplies the active regional-currency layer; no Ohzer or Varken location producer was found |
| Keyword Item Distributor | 4.1.0 | Local log identifies KID `4.1.0.0` running against game `1.7.104.0` |
| `Dragonborn.esm` | Skyrim 1.7.104 installation | Supplies all location, chest, spell, actor, and cell records enumerated below |

`exchangeCurrency_enhanced.esp` defines these keywords:

| Purpose | Record |
|---|---|
| Ohzer location currency | `isOhzerMoney` `[KYWD:000BB5]` in `exchangeCurrency_enhanced.esp` |
| Varken location currency | `isVarkenMoney` `[KYWD:000BB6]` in `exchangeCurrency_enhanced.esp` |

`exchangeCurrency_patch_COIN.esp` defines the actual currency items:

| Currency | Record | Raw value | Weight | Mesh |
|---|---|---:|---:|---|
| Ohzer | `EC_Ohzer` `[MISC:00086F]` | 12 | 0.01 | `Meshes\\Mihail's Shards of Immersion\\Coin Apocrypha\\ohzer.nif` |
| Varken | `EC_Varken` `[MISC:000870]` | 16 | 0.01 | `Meshes\\Mihail's Shards of Immersion\\Coin Dremora\\varken.nif` |

ECE's packaged SkyPatcher comments call Ohzer “Apocrypha's currency” and
Varken “Dremora's currency.” Its CDF files (`EC_ohzers.json` and
`EC_varkens.json`) consume `isOhzerMoney` and `isVarkenMoney`, respectively.
Its Papyrus location-change script also tests those keywords directly.

In the unmodified vendor stack, no ECE, C.O.I.N., or M.I.N.T. KID file assigns
either keyword to a location. ECE packages location KID data for Ulfric, Dram,
Drakr, Mede, and Oshka only, and plugin inspection found no location override
carrying Ohzer or Varken. Ensrick Regional Currency Integration v0.2.4 now
supplies the missing form-qualified Ohzer KID mapping; its final launch log
reports `isOhzerMoney` added to exactly 10 of 1,639 locations. Varken alone
remains inert and receives no location assignment.

The friendly name in ECE's `EC_varkens.json` says “Septims to Varkens in
Apocrypha.” That conflicts with ECE's own SkyPatcher comment, the parallel
Ohzer definition, and the original Mihail distribution. It is treated as a
copy/paste label, not as evidence that Varken belongs throughout Apocrypha.

## Exact Ohzer location map

Direct `Dragonborn.esm` record inspection found exactly one Apocrypha root and
nine immediate children. There are no grandchildren in this tree.

| Form-qualified record | Editor ID | Parent | Direct cells |
|---|---|---|---:|
| `0x016E2B~Dragonborn.esm` | `DLC2ApocryphaLocation` | none | 0 |
| `0x0142AC~Dragonborn.esm` | `DLC2Book05DungeonLocation` | `0x016E2B` | 1 |
| `0x0142AE~Dragonborn.esm` | `DLC2Book07DungeonLocationNEW` | `0x016E2B` | 1 |
| `0x0142AF~Dragonborn.esm` | `DLC2Book03DungeonLocation` | `0x016E2B` | 1 |
| `0x0142B0~Dragonborn.esm` | `DLC2Book01DungeonLocation` | `0x016E2B` | 14 |
| `0x01EE06~Dragonborn.esm` | `DLC2Book04DungeonLocation` | `0x016E2B` | 1 |
| `0x01EE07~Dragonborn.esm` | `DLC2Book06DungeonLocation` | `0x016E2B` | 1 |
| `0x01EE08~Dragonborn.esm` | `DLC2Book02DungeonLocationNEW` | `0x016E2B` | 1 |
| `0x0382F5~Dragonborn.esm` | `DLC2ApoIslandALocation` | `0x016E2B` | 4 |
| `0x03A1E7~Dragonborn.esm` | `DLC2ApocrypaMiraaksTowerLocation` | `0x016E2B` | 16 |

`DLC2ApocrypaMiraaksTowerLocation` is Bethesda's exact misspelled Editor ID;
it must not be silently “corrected” in documentation or tooling.

All 40 cells currently assigned to the Apocrypha subtree use one of the nine
child locations. None points directly at the root. None of the ten locations
has a native keyword in the inspected master.

### Owned KID configuration

Installed pack-owned filename:
`zz_Ensrick_Currency_Apocrypha_KID.ini`

The installed file uses form-qualified lookups rather than a bare Editor ID.
This fails closed if ECE or Dragonborn is absent and avoids silently creating
an unrelated dynamic keyword with the same spelling. KID's final launch log
confirmed ten Ohzer assignments; Varken received none.

```ini
; ECE Ohzer currency in all Dragonborn Apocrypha locations.
; Keyword: isOhzerMoney [KYWD:000BB5 in exchangeCurrency_enhanced.esp]
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x016E2B~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x0142AC~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x0142AE~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x0142AF~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x0142B0~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x01EE06~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x01EE07~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x01EE08~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x0382F5~Dragonborn.esm
Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x03A1E7~Dragonborn.esm
```

### Why the ten-entry set is intentional

The complete set is needed for safe behavior across all three ECE consumers:

1. Container Distribution Framework's `LocationKeywordCondition` checks the
   current location and then explicitly walks every `parentLoc`. The root alone
   would therefore be sufficient for CDF's present Apocrypha containers.
2. Base Object Swapper's keyword condition calls `HasKeyword` or
   `HasKeywordString` on the current location. It does not walk location
   parents for a keyword condition. The pack's Ohzer BOS rule keys on
   `0x000BB5`, so each of the nine locations directly used by cells must carry
   the keyword.
3. ECE's packaged `ec_septimsscript.psc` also calls
   `akNewLoc.HasKeywordString(...)` directly. It likewise needs the keyword on
   the actual current child location.

The nine children are thus operationally required for the 40 current cells.
The root is deliberately included as the canonical semantic marker so CDF can
use the authored hierarchy, so any future/direct-root cell remains covered,
and so other hierarchy-aware consumers see the realm itself as Apocrypha. The
root is not falsely claimed to have a direct cell today; it is the defensive
tenth entry that keeps the location-tree invariant complete.

KID adds the keyword at runtime and creates no override for any of these `LCTN`
records, so the classification itself consumes no plugin record and cannot
create a conventional location-record conflict. The unified v0.2.4 ESPFE is
present for transaction handling and other currency repairs; it does not
override these locations.

## Varken evidence and boundaries

### Evidence-backed distribution

The original Mihail Ohzer plugin, `mihailhermamoracoin.esp`, contains 20
records and overrides these Apocrypha treasure containers:

| Record | Editor ID |
|---|---|
| `0x02C460~Dragonborn.esm` | `DLC2TreasApocryphaChest` |
| `0x02C461~Dragonborn.esm` | `DLC2TreasApocryphaChestBoss` |

It also places curated references in cells `0x019CD7~Dragonborn.esm`
(`DLC2TempleofMiraak02`) and `0x017787~Dragonborn.esm`
(`DLC2TelMithryn`). Those exceptions support authored placement; they do not
support marking all of the Temple of Miraak or Tel Mithryn as Ohzer territory.

The original Mihail Varken plugin, `mihaildremoracoin.esp`, contains 33 records
and overrides these warlock treasure containers:

| Record | Editor ID |
|---|---|
| `0x02065D~Skyrim.esm` | `TreasWarlockChestBoss` |
| `0x05418E~Skyrim.esm` | `TreasWarlockChest` |

It also places curated references in:

| Cell | Editor ID |
|---|---|
| `0x013810~Skyrim.esm` | `WinterholdCollegeArcanaeum` |
| `0x0138D0~Skyrim.esm` | `MorthalFalionsHouse` |
| `0x015283~Skyrim.esm` | `FellglowKeep01` |
| `0x0240B7~Skyrim.esm` | `DawnstarSilussHouse` |

This is evidence for rare conjurer/warlock loot and carefully chosen placed
coins. It is not evidence for a world-region mapping. The two generic warlock
chest bases may also occur in non-Dremora contexts, so even the original target
set must be reference-audited against the final load order before it is enabled.

### Why the Dremora shop location must remain untagged

The only Dremora-named `Dragonborn.esm` location is:

- `DLC2DremoraShopLocation` `[LCTN:01FF28]`
- parent: `DLC2SolstheimLocation` `[LCTN:016E2A]`
- direct cell: `DLC2DremoraShop` `[CELL:01EE98]`, displayed as “Dremora Holding
  Cell”

The holding cell contains these persistent references:

| Record | Editor ID / role |
|---|---|
| `0x01FF27~Dragonborn.esm` | `DLC2DremoraButlerRef` |
| `0x01EEC5~Dragonborn.esm` | `DLC2MerchantDremoraChestRef` |
| `0x01EEC2~Dragonborn.esm` | `DLC2DremoraMerchantMarker` |
| `0x01EEC1~Dragonborn.esm` | `DLC2DremoraMerchantRef` |

Related base records are:

| Record | Editor ID / role |
|---|---|
| `0x01EEC0~Dragonborn.esm` | `DLC2MerchantDremoraChest` |
| `0x01EEC6~Dragonborn.esm` | `DLC2ConjureDremoraMerchant` |

ECE already assigns `IsDramMoney` to `DLC2DremoraShopLocation` in
`exchangeCurrency_enhanced_drams_KID.ini`. KID only adds keywords; assigning
Varken there would create a double-tag rather than replace Dram. More
importantly, the merchant is summoned to the player's current world location,
while his hidden holding-cell location does not follow him. A location keyword
there cannot safely select his live barter currency.

Neither ECE's stock `EC_varkens.json` nor the current pack-owned
`00_Ensrick_Currency_30_Varken.json` enables `allowVendors`. CDF initializes
vendor distribution as false, so the merchant chest is presently excluded.
ECE's Papyrus code treats Ohzer and Varken as exceptions to default Septim
handling but does not itself switch barter currency for this actor.

### Current actor-aware precedent and its limits

The 2026 “Currency Exchange Vendors” optional file “Dremora Merchant Uses
Varken” targets only the Black Market Dremora Merchant. Inspection of its
`DremoraMerchantUsesVarken.esp` found four records:

- new magic effect `DES_DremoraVarkenSwapEffect` `[MGEF:000800]`;
- new perk `DES_DremoraVarkenPriceAdjustmentPerk` `[PERK:000801]`;
- override of `DLC2MerchantDremoraChest` `[CONT:01EEC0]`;
- override of `DLC2ConjureDremoraMerchant` `[SPEL:01EEC6]`.

Its script listens for Dialogue Menu and BarterMenu activity, verifies
`DLC2DremoraMerchantRef.IsInDialogueWithPlayer()`, saves the previous Currency
Swapper state, switches tender, and restores state afterward. This is strong
architectural evidence that the merchant needs an actor/dialogue gate.

It is not a patch to copy or redistribute. It depends on the standalone Mihail
Varken item rather than ECE's `EC_Varken`, its inspected plugin is not
ESL-flagged, its chest replaces `Gold001 x2000` with Varken `x2000`, and it
uses a price-adjustment perk whose economics are not automatically valid for
ECE. The original Mihail item has value 1; ECE's raw `EC_Varken` has value 16.
Neither its 2,000-coin stock nor its price multiplier may be adopted until the
pack's final exchange rate and price semantics are measured.

## Proposed owned Varken architecture

### Track A: constrained loot

1. Leave every `Dragonborn.esm` location free of `isVarkenMoney`.
2. Begin the audit from the two evidence-backed bases
   `TreasWarlockChestBoss [CONT:02065D]` and
   `TreasWarlockChest [CONT:05418E]`.
3. Enumerate every placed/reference use of those bases in the final load order,
   including new-land and overhaul plugins. A generic warlock chest is only a
   proxy for conjurer activity; it does not prove Dremora presence.
4. Prefer a pack-owned CDF/SkyPatcher rule with an explicit chance, count, and
   level curve, with vendor distribution disabled. Do not replace every gold
   stack. If the frameworks cannot express the required contextual boundary,
   use a compact ESP-FE with curated references or leveled lists instead.
5. Consider actor inventory distribution only after reviewing the final Dremora
   leveled actors. Exclude unique/scripted actors and quest rewards unless
   individually approved.
6. Preserve the four original placed-coin ideas only through independently
   authored placements after conflict and narrative review; the original
   plugin is evidence, not redistributable implementation material.

This loot track can remain configuration-only. A plugin becomes necessary only
if new records or exact record overrides are chosen.

### Track B: actor-aware Black Market barter

Build an original pack-owned adapter against ECE's
`EC_Varken [MISC:000870 in exchangeCurrency_patch_COIN.esp]`:

1. Add an owned scripted magic effect to
   `DLC2ConjureDremoraMerchant [SPEL:01EEC6]`.
2. Gate all currency switching on the exact actor reference
   `DLC2DremoraMerchantRef [REFR:01EEC1]`, not race, location, or a generic
   Dremora keyword.
3. On Dialogue Menu/BarterMenu entry with that actor, save the prior Currency
   Swapper tender and notification state, set Varken as tender, and apply a
   purpose-built price-adjustment perk only if testing proves one is needed.
4. Restore the prior tender, notification state, and perk on normal menu close,
   dialogue cancellation, effect finish, failed dialogue, dismiss/resummon,
   load, and any abort path. Cleanup must be idempotent.
5. Define one consistent inventory policy for
   `DLC2MerchantDremoraChest [CONT:01EEC0]`: stock enough Varken for barter and
   either remove or quarantine its barter-visible Septims. Prefer a runtime
   patch if it can deterministically replace the exact stack; otherwise carry
   a minimal reviewed container override in the adapter.
6. Calculate stock and any price perk from the final Varken exchange ratio.
   Do not assume the precedent's `x2000` stock or multiplier.

This adapter functionally requires a plugin because it needs owned MGEF/PERK
records and an override or injection path for the summon spell, and possibly
the merchant chest. Compact its new records before release and flag the plugin
ESL so it loads as ESP-FE. The ESL flag is a slot optimization, not what makes
the behavior work. Ship all original Papyrus source beside the compiled script.

Future true Dremora/Oblivion new lands may receive Varken location keywords
only after their own `LCTN` trees are reviewed. Do not tag generic Daedric
sites, all summoner sites, or Apocrypha merely because they are Daedric-adjacent.

## Validation matrix

| Gate | Test | Pass condition |
|---|---|---|
| Static — Ohzer forms | Resolve every form-qualified KID entry against the final load order | One existing `isOhzerMoney` keyword and exactly ten existing `Dragonborn.esm` `LCTN` targets; no dynamically created keyword or unresolved form |
| Static — location exclusivity | Inspect the ten Apocrypha locations plus `01FF28` | Apocrypha has Ohzer only; none gains Dram, Drakr, or Varken from the owned file; `01FF28` gains no Varken and retains the current ECE Dram behavior until separately resolved |
| Static — CDF/BOS | Validate all owned JSON/INI files and effective priority | Schema parses; Ohzer rules reference `000BB5`; Varken vendor behavior is disabled until the merchant adapter is ready; no competing regional rule can fire at higher priority |
| Runtime — KID | Launch with logging and inspect KID output | Existing `isOhzerMoney` receives ten `Location` records, with no unresolved forms or duplicate/dynamic keyword creation |
| Runtime — Ohzer containers | Test ordinary containers in at least two different Black Book child locations and Miraak's tower | Ohzer replacement occurs once; ordinary copper/silver/gold and Drakr/Dram regional replacements do not also fire |
| Runtime — Ohzer loose coins | Test placed `Gold001` in at least two Black Book children and Miraak's tower | BOS selects Ohzer under the current child location; pickup/value/weight match the intended ECE presentation |
| Runtime — persistence | Save/load, leave/re-enter, and allow a container/cell reset | No duplicate currency, repeated conversion, lost inventory, or stale regional state |
| Deferred Varken loot | Test normal and boss warlock chests across representative vanilla and modded references | Approved chance/count/level curve only; no blanket gold replacement; no merchant or unrelated non-warlock leakage |
| Deferred merchant — scope | Summon the Black Market merchant in Skyrim, Solstheim, and Apocrypha | He uses Varken in every world because the exact actor gate wins; unrelated merchants retain their normal tender |
| Deferred merchant — economics | Buy and sell at boundary prices with 0, 1, and many Varken | Stock, rounding, displayed prices, and price perk match the approved exchange rate without arbitrage or free transactions |
| Deferred merchant — cleanup | Normal close, cancel dialogue, rapid reopen, dismiss/resummon, save/load during safe states, and quit/relaunch | Previous Currency Swapper tender and notification behavior are always restored; no persistent perk or notification suppression |
| Regression | Exercise ECE exchange, M.I.N.T. regional barter, ordinary Solstheim, and existing Drakr/Dram sites | Existing currencies remain unchanged outside the explicit Ohzer/Varken boundaries |
| Plugin quality | xEdit/check-for-errors and conflict review of `01EEC0` and `01EEC6` | No missing masters/errors; new FormIDs compacted before ESL flag; minimal intentional overrides forwarded against the final load order |

## Sources

Local plugin/config/script inspection is the primary evidence for every FormID,
Editor ID, hierarchy, record count, and active behavior stated above. Source
pages establish release identity and author-stated purpose:

- [Exchange Currency Enhanced](https://www.nexusmods.com/skyrimspecialedition/mods/141884)
- [C.O.I.N.](https://www.nexusmods.com/skyrimspecialedition/mods/51439)
- [M.I.N.T.](https://www.nexusmods.com/skyrimspecialedition/mods/178940)
- [Keyword Item Distributor](https://www.nexusmods.com/skyrimspecialedition/mods/55728)
- [Container Distribution Framework](https://www.nexusmods.com/skyrimspecialedition/mods/120152)
- [Audited CDF `LocationKeywordCondition` source](https://github.com/Ensrick/DynamicContainerInventoryFramework/blob/5f2ddbb4abd27c00d2c4d8aff56bd95dcc61ffd0/src/conditions/locationKeywordCondition.cpp)
- [Base Object Swapper](https://www.nexusmods.com/skyrimspecialedition/mods/60805)
- [Audited BOS direct-location keyword source](https://github.com/powerof3/BaseObjectSwapper/blob/c0b9c093aa6260fd9b68beddea411db97f585ea2/src/ConditionalData.cpp)
- [Ohzer — Coin of Apocrypha](https://www.nexusmods.com/skyrimspecialedition/mods/90069)
- [Varken — Coin of Dremora](https://www.nexusmods.com/skyrimspecialedition/mods/89990)
- [Currency Swapper](https://www.nexusmods.com/skyrimspecialedition/mods/127686)
- [Currency Exchange Vendors — actor-specific merchant precedent](https://www.nexusmods.com/skyrimspecialedition/mods/184612)

## Remaining uncertainties

- The final Varken-to-Septim exchange rate, barter rounding, merchant stock, and
  any compensating price perk require an isolated runtime economic test.
- The two generic warlock chest bases may be too broad after the final mod list
  is installed; their full winning-override/reference graph must be regenerated
  immediately before implementation.
- The safe behavior of Currency Swapper across save/load while a barter menu is
  active must be measured on Skyrim 1.7.104; design cleanup defensively even if
  that edge case cannot be forced reliably.
- Permissions and licenses for all upstream assets must be rechecked at release.
  The pack should distribute only its independently authored configuration,
  ESP-FE, source, and scripts, while retaining vendor mods as external
  dependencies.
