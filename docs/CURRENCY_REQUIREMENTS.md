# Complete regional currency requirements

Owner clarification, 2026-09-06:

> The idea behind the mods chosen was that we would have a complete regional currency system with copper, silver, and gold versions of every goddamn coin!

This is the controlling requirement, not an optional future extension. The
installed 0.3.0 package is incomplete against it. Its singleton and ancient
currency exclusions were an implementation mistake, not owner-approved scope.

## Denominations and identity

- Every supported currency family/design needs Copper, Silver and Gold items,
  worth exactly 1, 10 and 100 in the common accounting unit.
- This includes ancient, regional, and presently single-denomination currency.
  A missing metal variant requires a private, reproducible asset variant; it
  does not justify excluding that family.
- Preserve each coin's recognizable cultural design. Variant faces/designs
  must be explicitly inventoried; do not silently drop them or replace them
  with a generic Septim model.
- Item names and inventory icons must identify the denomination without
  requiring the player to distinguish colors.
- Model, plugin record, runtime configuration, distribution rule and exchange
  value must agree for each exact FormKey. Seeing the values 1, 10 and 100
  somewhere in a file is not a sufficient test.

## Distribution and accounting

- Regional identity must apply to loose placed coins, purses, container money
  and NPC money. Match authored cultural/site information, not just which
  new-land plugin owns the location.
- Retain the approved loose-coin probabilities and normal efficient-change /
  occasional imperfect-change behavior. Never flatten silver or gold into a
  one-for-one count of copper during regional conversion.
- Inventory conversion, spending, exchanges, save/reload and source reopening
  must conserve value and must not create a second payment for physical coins.
- Anciency is not a reason to bypass denomination handling. Ancient sites
  need an appropriate three-tier regional family, not a Septim fallback.
- Protect quest mechanics and player storage from unsafe rewriting. Such
  safety limits are not permission to leave a currency family without tiers;
  any unresolved acquisition path remains an explicit coverage gap.
- Region assignments that cannot be established from installed content must
  be reported as open decisions. Do not invent cultural assignments or mark
  dormant/unrouted coins as a complete regional system.

## Release gates

1. An exact inventory accounts for all supported monetary forms, design
   variants and aliases from the installed providers.
2. Each inventory row has all three assets, exact tier-to-value bindings, and
   a documented acquisition/distribution route. No singleton exemptions.
3. Record, asset, source, denomination, routing and accounting tests pass;
   deliberately wrong tier values, missing variants and bypasses must fail.
4. Build and deployment are reversible, outside vendor folders, without
   silently altering user saves. Restricted assets remain user-local outputs.
5. Actual fresh-game acquisition, transactions and save/reload are tested.
   Static success does not count as completed gameplay acceptance.

Track implementation and unresolved coverage in the existing currency master
issue #207 and denomination issue #217. No additional mod is approved merely
because it might make this implementation easier.

## Existing price modifiers are a separate mechanic

The denomination correction does not authorize rebalancing regional shop
prices. ECE's existing price perks are retained: their two entry points are
`ModBuyPrices` (8) and `ModSellPrices` (60), not denomination exchange rates.
The inspected buy/sell multipliers are Mede 0.75/1.25, Ulfric 1.20/0.80,
Dram 1.12/0.88, Drakr 0.50/1.50, and Oshka 1.50/0.50. Thus a silver coin
still represents ten copper accounting units even where merchant prices
differ. Whether to retain these substantial regional price differences is a
separate owner decision; the current repair preserves existing behavior.

Evidence: installed `exchangeCurrency_patch_COIN.esp` PERKs 00082B, 000829,
00082A, 00082C and 000872 respectively; CommonLibSSE-NG
`include/RE/B/BGSEntryPoint.h` names the entry-point IDs.

## Remaining gameplay choices, not new permissions

- The existing bridge automatically reconciles the carried wallet into the
  current region's design on location changes. Preserving foreign coins until
  a deliberate exchange would change that existing architecture and remains an
  explicit owner decision; it is not implemented under tier-completion work.
- The fifteen added regional purse helpers inherit the approved small 2–28,
  medium 5–42 and large 10–70 budgets. They have silver/copper mixtures but no
  100-value gold payout. Raising those budgets requires a balance decision,
  separate from ensuring correct denominations whenever a budget exceeds 100.
