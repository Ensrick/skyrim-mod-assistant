# Currency and economy overhaul research

**Status:** research complete; implementation deliberately deferred. No mod was
installed, enabled, edited, or copied into the live profile during this audit.

**Current through:** 2026-09-02.

## Decision

The strongest current foundation is not one monolithic economy mod. It is a
layered system with one owner for each responsibility:

1. [C.O.I.N. 3.5.3](https://www.nexusmods.com/skyrimspecialedition/mods/51439)
   owns ancient ruin currency.
2. [M.I.N.T. 1.0.6](https://www.nexusmods.com/skyrimspecialedition/mods/178940)
   and [Currency Swapper 2.2.0](https://www.nexusmods.com/skyrimspecialedition/mods/127686)
   own genuine regional tender and transaction switching.
3. [Exchange Currency Enhanced 4.1.1](https://www.nexusmods.com/skyrimspecialedition/mods/141884)
   is the best current candidate for weighted copper, silver, and gold
   denominations, notes, purse decomposition, and Bruma currency.
4. A pack-owned **Ensrick Currency Integration** ESPFE/config package should own
   exact distribution policy, location tagging, new-land integration, and
   conflict resolution. It must depend on vendor mods rather than repackaging or
   modifying them.
5. [Trade & Barter 2.2](https://www.nexusmods.com/skyrimspecialedition/mods/23081)
   is the lower-risk price/economy layer to test only after currency behavior is
   stable.

Do not adopt [M.I.N.T. - Borders of Coin 2.3.0](https://www.nexusmods.com/skyrimspecialedition/mods/187837)
as the initial foundation. It is promising, but version 2.3.0 was released on
the date of this audit after rapid fixes for new-game initialization, currency
selection, rate modifiers, dialogue, property purchases, and stable behavior.
It deserves a separate source/plugin audit and soak test later.

The first disposable-profile test should proceed in two gates:

- **Gate A:** ECE's `new Septims only` option, leaving M.I.N.T. authoritative for
  regional currency while denomination and transaction mechanics are isolated.
- **Gate B:** ECE's `new Septims + regional currencies` option if Gate A is
  stable. This lets ECE supply its broader Mede/Oshka integration while retaining
  M.I.N.T. exchangers and Sancar support. Gate B is the stronger eventual pack
  candidate, not a foregone conclusion.

C.O.I.N.'s automatic conversion on pickup should be disabled during both gates;
otherwise the physical ancient coins immediately collapse back into vanilla
`Gold001` value.

## Choose the accounting model before choosing probabilities

Skyrim's engine recognizes only `Gold001 [MISC:0000000F]` as native money. A
different MISC record with a sale value is merchandise, not another native
denomination; the engine-facing `IsGold()` test in CommonLib checks that exact
FormID. Currency Swapper/ECE are therefore doing real transaction adaptation,
not merely replacing a texture.

There are two coherent but incompatible accounting models:

- **Compatibility-first:** retain one vanilla price unit as the accounting
  unit. Copper can be worth 1 unit, silver 25, and gold 100. Vanilla prices and
  scripted `Gold001` rewards remain numerically valid, but a one-for-one swap of
  an ordinary one-unit coin to silver or gold creates wealth. This is the ECE
  pilot described in this report.
- **True subunits:** reinterpret a physical gold coin as, for example, 100
  copper; a vanilla price `P` becomes `100P` subunits. That gives denominations
  more intuitive names, but requires every price, reward, service, script, UI,
  and transaction path to understand the new base unit. It is a custom native
  economy-engine project, not a configuration choice.

Neither model allows one original coin reference to become one randomly chosen
1/10/100 coin while also preserving value. Under the compatibility-first model
the random result increases wealth; under a true-subunit model it usually
reduces the value of what was originally a gold coin. Count or total payout must
also change.

## The 75/20/5 problem

The requested visual distribution—75% copper, 20% silver, and 5% gold—is
technically possible with stable Base Object Swapper randomness. It is not
economically neutral when every original one-Septim reference is replaced
one-for-one by a denomination worth more than one.

Under the recommended compatibility-first pilot and candidate values of
1/25/100:

`expected value = 0.75(1) + 0.20(25) + 0.05(100) = 10.75`

That is **10.75 times the vanilla loose-coin value**. Even 1/10/100 produces an
expected value of 7.75. This is why a direct 75/20/5 swap on every countertop
coin should not ship.

| Loose-reference policy | Copper | Silver | Gold | Expected value at 1/25/100 | Effect |
|---|---:|---:|---:|---:|---:|
| Requested one-for-one swap | 75% | 20% | 5% | 10.7500 | +975% |
| Conservative windfalls | 99.45% | 0.50% | 0.05% | 1.1695 | +16.95% |
| Strict value preservation | 100% | 0% | 0% | 1.0000 | none |

The recommended rule is therefore:

- Treat **75/20/5 as a composition target for purses and value-budgeted piles**,
  not as the one-for-one value distribution of isolated loose references.
- Make isolated one-value coins copper by default. A rare silver or gold coin is
  an explicit windfall whose permitted inflation must be chosen and tested.
- For a purse, first roll a baseline payout calibrated to the vanilla formula or
  an explicitly approved wider distribution; there is no fixed purse value
  before activation. Then decompose that rolled budget into eligible
  denominations. For a fixed pile, start from its authored total. Repeatedly
  choose among denominations no greater than the remaining budget, subtract the
  selected value, and finish with copper. This keeps the chosen payout exact
  while allowing varied contents.
- Where a placed reference has a sufficiently large original stack count, a
  generation-time xEdit patch may replace the stack with an equivalent
  denomination mix. Base Object Swapper alone cannot safely change both base
  object and count; swapping a stack of 100 one-value coins to 100 gold coins
  would multiply wealth catastrophically.

If a small amount of loose-world inflation is desired, the general formula at
1/25/100 is:

`inflation = 24(silver probability) + 99(gold probability)`

Exact percentages should be chosen only after the user selects an acceptable
inflation ceiling. Visual diversity can also come from multiple copper meshes,
coin orientations, and value-neutral clutter without falsifying denominations.

## Vanilla purses and broader payouts

The three vanilla purse objects are `FLOR` harvestables, and their harvest
targets are leveled lists. Their current payout behavior is compact and does not
need an activation script:

| Purse | Vanilla formula | Range | Mean |
|---|---|---:|---:|
| Small | `5 + LootGoldChange + LootGoldChange25` | 5–23 | 10.75 |
| Medium | `10 + 2×LootGoldChange + LootGoldChange25` | 10–37 | 20.25 |
| Large | `20 + 3×LootGoldChange + LootGoldChange25` | 20–56 | 34.75 |

`LootGoldChange` is 10% empty and otherwise uniform from 1–9;
`LootGoldChange25` is 75% empty and otherwise uniform from 1–9. Wider purse
ranges can therefore use three owned replacement/nested leveled lists. Do not
modify the shared vanilla lists because unrelated records also use them.

A good first-pass “wider but not richer” policy is to roll the vanilla baseline
`B`, then select approximately half of `B` 25% of the time, unchanged `B` 62.5%
of the time, and double `B` 12.5% of the time. The expected multiplier is:

`0.25(0.5) + 0.625(1) + 0.125(2) = 1.0`

With unbiased integer rounding for odd half-values, this widens the approximate
ranges to 2–46 (small), 5–74 (medium), and 10–112 (large) while retaining the
vanilla means of 10.75, 20.25, and 34.75. The owned-list generator should
enumerate the exact integer distribution rather than use runtime floating-point
rounding. The selected budget is then decomposed into denominations without
changing its value. This is the recommended prototype, subject to the user's
approval of the larger tails.

CDF should own contextual contents of ordinary resettable containers, not purse
activation. If purse currency must change by region, BOS can swap the purse
`FLOR` to a regional duplicate whose harvest target is the corresponding owned
regional leveled list. Every new list must be tested for minimum, maximum, mean,
and conservation after denomination decomposition.

CDF 3.1.0 works at inventory initialization, stores no serialized distribution
state, and reapplies when an eligible inventory resets. A 20-entry owned list
with 15 repeated copper entries, four silver entries, and one gold entry can
express a 75/20/5 roll only when the list resolves exactly one equally weighted
eligible entry and duplicate entries remain distinct. It still does not solve
value conservation by itself, so it belongs inside a controlled payout budget
rather than as an unrestricted replacement for every one-value coin.

## What the current mods actually do

### C.O.I.N.

C.O.I.N. is the current ancient-currency foundation. It distributes Drakr,
Nchuark, Mallari, Mala, and Gibber through Base Object Swapper, Container
Distribution Framework, and location keywords rather than broad cell edits. It
has bundled Bruma/Ayleid support and exposes/injects useful location sets for
third-party content. Some leveled-list integration still needs an xEdit audit.

Its physical coins can be left intact, exchanged, or automatically converted on
pickup. For this design, leave automatic conversion off and provide intentional
exchange or crafting sinks. The released plugin must be inspected before use:
the Nexus documentation gives Drakr an exchange value of 0.25 while the current
source default appears to be 0.15.

### M.I.N.T. and Currency Swapper

M.I.N.T. is the current successor to the author's older standalone currency
mods. Its modules cover Solstheim Dram, Ulfric currency, exchangeable Sancar,
and optional Gibber behavior. Currency Swapper supplies verified transaction
behavior for the Dram/Ulfric/Gibber paths across merchants, training, bounties,
and related menus. Do not describe Sancar as regional legal tender until its
packaged plugin and runtime behavior prove that; it is documented as
distributed and exchangeable.

Use M.I.N.T.'s **no Raven Rock exterior office** and **no Windhelm exterior
stall** variants. They avoid unnecessary city/worldspace edits, reduce conflicts
with the selected city stack, and reduce possible downstream worldspace/LOD
review. No claim is made that the omitted kiosks themselves generate distant
LOD.

Proteus/multiple-character behavior requires explicit testing: after switching
characters in the same save, the active tender must be derived from the current
character's location before a transaction opens.

The released Currency Swapper 2.2.0 source/tag counts one bound custom-currency
form; it does not natively aggregate several denominations in one family. ECE
supplies the additional behavior for the off-the-shelf pilot. If ECE cannot pass
the runtime gates, the correct fallback is a source-built Currency Swapper
derivative—not another layer of `OnItemAdded` Papyrus conversion.

### Exchange Currency Enhanced

ECE is the closest available match to the requested denomination design. It
provides configurable copper/silver/gold values, weights of 0.01/0.02/0.03,
1,000/2,000/5,000-value exchange notes, randomized purse contents, regional
currencies, exchangers, and Bruma integration. It retains invisible vanilla
`Gold001` as a compatibility/accounting backend for game systems that assume the
base form.

It does **not** passively compress money like Terraria. Copper, silver, gold,
regional tender, and notes remain separate physical inventory forms. Scripts
total or switch them for transactions; exchangers and notes are the deliberate
consolidation mechanisms. This is desirable for currency weight, provided the
UI and transaction paths are reliable.

The framework chain is substantial: Address Library, BOS, CDF, Currency
Swapper, the original Exchange Currency, KID, Notification Filter,
powerofthree's Tweaks, SkyPatcher 6.5+, SkyUI, and—under regional mode—Dynamic
Dialogue Replacer, C.O.I.N., and M.I.N.T. ECE also documents a TrueHUD recent
loot conflict. The current profile already has BOS 3.5.0 and SkyPatcher 7.0.3,
but does not presently contain CDF, Currency Swapper, C.O.I.N., M.I.N.T., or
ECE, so none of this research is evidence that the stack is already installed.

## World and culture mapping

Currencies should follow a polity, culture, or historical site—not exist merely
because a plugin has its own worldspace. That keeps the inventory readable and
avoids inventing one-off money for every quest mod.

| Area | Current evidence | Recommended policy | Required work |
|---|---|---|---|
| Skyrim settlements | Vanilla `Gold001`; M.I.N.T./ECE can add modern variants | Weighted copper/silver/gold Septims; Ulfric tender only where the selected regional rules make it meaningful | ECE pilot, transaction tests, and conflict patch |
| Nordic ruins | Standard Nordic location keywords | C.O.I.N. Drakr | Audit missing/mistagged mod locations |
| Dwemer ruins | Standard Dwemer location keywords | C.O.I.N. Nchuark | Audit missing/mistagged mod locations |
| Falmer sites | Standard/injected Falmer location keywords | C.O.I.N. Mallari | Audit missing/mistagged mod locations |
| Ayleid ruins | C.O.I.N. supports Ayleid Mala; Bruma already has its own Ayleid coin and purses | Pick one deliberate visual winner while retaining one economic identity | Asset/record comparison before patching |
| Solstheim | 174 loose vanilla coins plus direct lists; C.O.I.N. covers ancient sites and M.I.N.T. supplies Dram | Dram in Raven Rock; Drakr in culturally appropriate Skaal/Nordic contexts; Nchuark in Dwemer sites | M.I.N.T. no-office variant; exception audit |
| Beyond Skyrim: Bruma | 95 native Ayleid coins, 990 loose vanilla coins; C.O.I.N. has Ayleid mapping and ECE has Mede integration | Mede in modern Cyrodiil; Mala or Bruma's native equivalent in Ayleid sites; Drakr in the tagged Northfringe Nordic site | Decide Ayleid asset winner; test Bruma services and rewards |
| Beyond Reach | 235 loose vanilla coins; no spendable custom currency; only five useful ancient-site tags found | Retain recognized modern tender in ordinary settlements unless lore/content audit justifies a Breton issue; ancient currencies in correctly tagged ruins | KID/location patch, loose-reference audit, compiled-script and dialogue audit |
| Wyrmstooth | 116 loose vanilla coins; 24 occur in already tagged Nordic or Dwemer/Falmer locations | Septims in current settlements; C.O.I.N. currencies in ancient sites | Classify the remaining 92 untagged references; do not rely on the old Merchant Exchange patch |
| Moonpath to Elsweyr | No loose `Gold001`, no direct gold lists, no native tender, and no useful ruin tags found | Leave transactions neutral until dialogue/script rewards are understood; add Khajiiti tender only as a coherent designed system | PEX/dialogue audit; fully custom if adopted |
| Gray Cowl | A value-200 `AnotherWorldCoin` collectible exists; 79 loose vanilla coins; some Dwemer-tagged sites | Do not repurpose the collectible without proving quest semantics; ancient currency in tagged ruins; decide a Hammerfell policy later | Reference/quest audit and custom regional module if approved |
| VIGILANT | No loose coins or currency MISC; gold arrives through 17 leveled lists and two container/NPC entries; most visible heaps are non-lootable statics | Preserve visual statics; decide separately whether Coldharbour should award no conventional money or a lore-specific collectible | Reward-list/script audit, not broad BOS swapping |

The direct plugin scan establishes record counts and keyword coverage. It does
not prove behavior hidden in compiled PEX or dialogue fragments. Beyond Reach,
Moonpath, Gray Cowl, and VIGILANT therefore require disassembly/record-flow
inspection before a distributable patch is generated.

## Pack-owned implementation boundary

The future custom package should be one source-controlled mod with small,
separable modules:

- `Ensrick Currency Integration.esp`, ESL-flagged, for owned keywords,
  location corrections, leveled-list forwarding, and explicit conflict
  resolution;
- one namespaced BOS `_SWAP.ini` for value-safe visual/reference swaps;
- CDF rules for contextual contents of ordinary containers;
- private leveled lists for small, medium, and large purse rewards, plus
  regional purse `FLOR` duplicates only where needed;
- KID rules for regional and ancient-site classification;
- SkyPatcher rules only where runtime patching is safer than plugin overrides;
- owned Papyrus source only if value-budgeted placed piles cannot be generated
  offline; and
- a silent Notification Filter preset and generic `Money` UI label if required.

Precedence must be explicit:

1. quest-specific exclusions and authored unique currency;
2. ancient-site currency by verified location classification;
3. modern regional currency by current polity/location;
4. ordinary copper/silver/gold Septims;
5. invisible `Gold001` only as the compatibility backend.

BOS 3.5.0 stable per-reference probability can express exact non-overlapping
75/20/5 selection if ever approved. The following is pseudocode for the rule
ordering; production form references use BOS syntax `0xFormID~Plugin.esp`, while
pipes delimit BOS fields:

```ini
[Forms]
Gold001|CopperCoin
Gold001|SilverCoin|NONE|chanceS(25)
Gold001|GoldCoin|NONE|chanceS(5)
```

Current BOS processes same-base rules in reverse and both `chanceS` rules use
the same reference-seeded random value: 0–5 selects gold, greater than 5 through
25 selects silver, and the remainder falls back to copper. Pin the BOS version
and regression-test this source-dependent behavior. Use `chanceS`, not
`chanceR` (rerolls across restarts) or `chanceL` (correlates results by
location).

The rules must live in one authoritative namespaced file and be statistically
verified; config ordering and another mod's competing `Gold001` swap can change
the result. BOS positive conditions are alternatives rather than a general AND
expression, so complex cases such as “Bruma worldspace and Dwemer ruin” should
use generated exact reference maps or mutually exclusive owned keywords instead
of ambiguous condition lists.

All external DLLs, meshes, textures, voices, scripts, and plugins remain
dependencies downloaded from their authors. The pack may distribute only its
own ESPFE/config/source and permission-cleared assets. This also prevents local
source builds or private fixes from silently becoming altered copies of someone
else's mod.

### Native fallback if ECE fails

A native denomination-aware fork should have these hard boundaries:

- physical inventory forms are authoritative; there is no global virtual
  wallet;
- currency family and legal tender derive from the current location, not from a
  permanent character global;
- denomination totals use checked signed 64-bit subunits and wider temporaries
  for multiplication;
- exchange rates use exact rational arithmetic with carried remainders and an
  explicit bid/ask spread or fee—never upward rounding in both directions;
- purchases, sales, training, bounties, fines, housing, services, and UI updates
  execute atomically behind a recursion/transaction guard;
- Proteus character switching is rejected while a transaction, exchange, or
  follower-inventory menu is open; and
- co-save state is limited to versioned configuration and fractional exchange
  remainders, with FormIDs resolved on load and a recovery command available.

This is a fallback because it is a real SKSE engineering project. If built from
Currency Swapper, the exact base must be pinned: released tag 2.2.0 is
Apache-2.0, while current `main` is AGPL-3.0.

## Source-audit flags to resolve in the pilot

- M.I.N.T.'s published exchange helper currently uses `Math.Ceiling` on both
  multiplication and division paths. Small bidirectional exchanges may round
  upward and must be tested for profitable loops. A pack-owned exchanger should
  use floor plus a carried remainder or an explicit fee.
- The published M.I.N.T. Dram BOS config contains bare `|60` fields, while BOS
  3.5.0 only parses probability fields containing `chance`. Against that source,
  the published rules are unconditional rather than 60%. Verify whether the
  downloaded Nexus archive differs, then ship a corrected owned override and
  runtime-test the intended distribution before adoption.
- C.O.I.N.'s website/source Drakr-rate discrepancy must be resolved from the
  released ESP property.
- C.O.I.N.'s published source has an apparent loop-bound defect in a
  module-array compaction path. Compare source with the released PEX and exercise
  module removal/re-registration before relying on automatic conversion or
  uninstall/recovery behavior.
- Custom denomination MISC forms must not also be saleable as ordinary
  merchandise, which could count the same value once as tender and again as a
  vendor good.

## Economy layer

Currency plumbing and price formation should be separate test gates.

- **Trade & Barter 2.2** is the recommended first price layer. It is mature,
  comparatively small, and exposes merchant gold, barter curve, faction/race,
  and location adjustments without becoming the currency framework.
- [Evolving Economy 3.0.1](https://www.nexusmods.com/skyrimspecialedition/mods/149830)
  is the richer later candidate for seasonal, regional, Civil War, and
  reputation-sensitive prices. It should replace—not blindly stack with—other
  systems that write the same price variables.
- [Trade Routes](https://www.nexusmods.com/skyrimspecialedition/mods/12358) is an
  older beta with periodic regional update scripts. Its age and persistent
  regional state make it a weaker fit for a stability-first, multi-character
  same-save design.
- Very recent banking/inflation overhauls and the 2026 alpha New Economy
  Overhaul are not first-playthrough foundations.

Coin weight should be tested as an economy mechanic, not just a realism toggle.
At ECE's documented weights, 100 value carried as copper weighs 1.00, four
25-value silver coins weigh 0.08, and one 100-value gold coin weighs 0.03.
Higher denominations and notes therefore become meaningful encumbrance relief;
automatic passive compression would remove much of that gameplay.

## Verification gates

The stack is not approved for the main profile until all of the following pass
in a disposable profile and then a new long-form test save.

### Static audit

- Pin exact archive versions and hashes; inspect every plugin in xEdit.
- Resolve `Gold001`, coin MISC, leveled-list, merchant, service-dialogue, global
  price, and location-keyword conflicts against every active master.
- Inspect C.O.I.N.'s released exchange-rate properties and the apparent source
  discrepancy before using them.
- Disassemble relevant new-land PEX and dialogue fragments; never infer scripted
  reward behavior from raw byte-string matches.
- Confirm every produced plugin is ESL-safe and every distributed file is owned
  or permission-cleared.

### Statistical and value tests

- Simulate at least 10,000 stable reference seeds for every BOS probability
  table; require observed rates within a predeclared statistical tolerance.
- Enumerate every purse/container tier, compare old and new minimum, maximum,
  mean, and percentile payouts, and require exact per-purse value preservation
  where that policy applies.
- Scan generated loose-reference patches and prove that total original and new
  value are equal, except for an explicitly approved windfall budget.
- Repeat tests after save/load and cell reset to prove stable swaps do not reroll.

### Runtime matrix

- New game and disposable existing save.
- Pickup, drop, repick, stack, container transfer, follower inventory, corpse
  loot, QuickLoot, respawning containers, and merchant restock.
- Buying, selling, training, bounties, fines, bribery, room rental, carriages,
  houses, scripted rewards, and every exchanger/note path.
- Travel and transactions in Skyrim, Solstheim, Bruma, Beyond Reach, Wyrmstooth,
  Moonpath, Gray Cowl, and VIGILANT.
- Proteus character switching in the same save, including switching while
  characters occupy different currency regions.
- Rapidly enter/leave transaction dialogue, save/load in every region, and
  confirm currency always returns to a neutral state after a menu closes.
- Verify no duplication, currency loss, negative balances, stuck regional
  tender, notification spam, popup windows, or Papyrus/native log errors.
- If TrueHUD is later installed, disable its recent-loot widget or verify an
  equivalent ECE-safe configuration.

### Acceptance criteria

- No crash, hang, visible error dialog, or background popup.
- No unresolved xEdit conflicts in currency-owned records.
- No transaction can spend the wrong region's tender or strand the player with
  unusable money without an available exchange path.
- Total payout and inflation remain within the user-approved budget.
- Proteus character switching cannot duplicate, erase, or leak currency state.
- Config and MCM choices are reproducible for a packaged profile.

## Decisions to make before implementation

1. Compatibility-first accounting or a true 1/10/100 subunit economy. The
   compatibility-first ECE pilot is the safe recommendation.
2. Final denomination values and weights: 1/25/100, 1/10/100, or another curve.
3. Maximum acceptable inflation from rare loose silver/gold windfalls; zero is
   the safe default, with 75/20/5 reserved for value-budgeted contents.
4. Whether to approve the mean-neutral wider purse prototype: approximate
   ranges 2–46, 5–74, and 10–112 at unchanged vanilla means.
5. Whether ECE regional mode survives Gate B, or M.I.N.T. remains the sole
   regional authority.
6. Whether Beyond Reach, Moonpath, Gray Cowl, and VIGILANT truly need new
   spendable tender, rather than culturally appropriate ancient loot or neutral
   Septims.
7. Ancient/regional exchange rates, fees, vendor change policy, and whether
   Grand Solitude's Bank of Haafingar is the single dedicated exchange venue.
8. Whether Proteus characters keep independent physical wallets (recommended)
   or share funds through an explicit bank.
9. Whether the later price layer begins with Trade & Barter or waits for an
   Evolving Economy comparison profile.

## Alternatives rejected or deferred

- [Ruin Coins 1.5](https://www.nexusmods.com/skyrimspecialedition/mods/88859)
  is a credible, simpler alternative, but it is narrower than C.O.I.N. and
  should not be combined with it.
- C.O.I.N. Merchant Exchange targets an older generation and is superseded by
  current exchange options.
- [C.O.I.N. Treasury Exchange](https://www.nexusmods.com/skyrimspecialedition/mods/131682)
  and [Grand Solitude - C.O.I.N. Bank Exchange](https://www.nexusmods.com/skyrimspecialedition/mods/157596)
  are alternatives, not cumulative requirements. Given the selected Grand
  Solitude, its Bank of Haafingar addon is the thematic candidate after audit.
- Coins of Tamriel SSE, Skyrim Currency System SE, and older weighted-coin
  patches are superseded for this design.
- Nordic Souls 3 Currency demonstrates that the C.O.I.N./M.I.N.T./ECE stack is
  used in a current list, but its list-specific patch and its reported high
  wealth generation are evidence to study, not a patch to copy.

Detailed source provenance and confidence notes are recorded in
`records/currency-economy-overhaul-sources-2026-09-02.md`.
