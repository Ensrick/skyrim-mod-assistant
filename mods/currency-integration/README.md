# Ensrick Regional Currency Integration

This is the owned compatibility layer for the approved currency stack. It does
not contain meshes, textures, audio, or plugins from the required mods. Six
narrowly modified ECE script binaries are included under ECE's redistribution
terms; all complete upstream mods remain separate Nexus downloads.

## Policy

- Loose modern Septims resolve deterministically to 75% copper (value 1,
  weight 0.06), 20% silver (value 25, weight 0.07), and 5% gold (value 100,
  weight 0.13). Expected value is 10.75 per placed vanilla coin: a deliberate
  975% increase accepted by the user because currency has weight and the final
  inventory/loot economy will be much stricter.
- Skyrim exposes an abstract carry-weight number rather than a documented mass
  unit. This modlist treats 1.00 as approximately one pound for economy
  balancing. Copper's 0.06 is near the mass of a large historical one-ounce
  circulation coin; silver and gold preserve approximate same-volume metal
  density ratios. The three ECE meshes have identical dimensions, so their
  weights differ by material rather than denomination value.
- Quest-specific exceptions win first, then ancient-site currency, then modern
  regional tender, then the ordinary Septim mix. The hidden vanilla Gold001
  remains the accounting backend.
- Modern Cyrodiil uses Medes, while Ayleid sites in Bruma use Mala. Nordic,
  Dwemer, Falmer and root-cave sites retain C.O.I.N.'s culturally specific
  currency families.
- No invented tender is assigned to Beyond Reach, Wyrmstooth, Moonpath, Gray
  Cowl, or VIGILANT merely because the content comes from another plugin.
  Tagged ancient sites work now; unresolved site classifications remain a
  tracked coverage task.

## Compatibility and runtime fixes

The package masks or corrects released configuration and plugin conflicts without
modifying the vendor mod folders:

1. M.I.N.T. 1.0.6's four bare `|60` BOS fields become `chanceS(60)`.
2. Its Fort Frostmoth cleanup rule is positively scoped to Fort Frostmoth,
   rather than running everywhere except the fort.
3. ECE's Mede CDF rule points to the actual `Update.esm` form.
4. Dedicated CDF precedence rules stop generic Septim conversion from consuming
   Bruma Ayleid and Solstheim regional containers first.
5. ECE's generic container conversion excludes twelve quest, prisoner,
   stolen-goods and player-storage references instead of converting their
   hidden `Gold001` accounting inventory.
6. Regional Drakr swaps resolve directly to ECE's canonical Drakr Whale MISC;
   they do not target a leveled list that BOS drops on encounter-zoned refs.
7. `Ensrick Currency Integration Patch.esp` forwards ECE's silver/gold
   `DLC2GoldPile01` and `DLC2GoldPile02` behavior over C.O.I.N.'s later
   overrides, and restores `GiftUniversallyValuable` to `Gold001`.
8. The ESPFE sets M.I.N.T.'s injected `DES_ConvertCoins` global to zero and
   disables all 17 active currency-to-ingot recipes by nulling their workbench
   keyword. Money-changer bank recipes remain available; physical money cannot
   be converted into crafting metal.
9. A start-enabled quest with a forced player alias sets C.O.I.N.'s
   `autoExchange` and `verbose` properties false and M.I.N.T.'s conversion
   global to zero on initialization, save load, four bounded delayed boot
   passes, and Journal Menu close. This deliberately overrides C.O.I.N.'s
   shipped `autoExchange=true` MCM default without replacing its PEX files or
   relying on a per-save MCM preset. It works on new and existing saves; the
   packaged SEQ ensures the newly added start-enabled quest is discovered.
10. ECE's numeric `IsOhzerMoney` keyword is assigned to Apocrypha's parent and
    nine shipped direct child locations. Both are required: CDF walks parent
    locations, while BOS/ECE evaluate the current location directly.
11. The three vanilla coin-purse leveled lists are rebuilt as sixteen equal,
    single-choice hidden-`Gold001` entries. `UseAll`, chance-none and chance
    globals are cleared. Small/medium/large retain vanilla means of
    10.75/20.25/34.75 while widening to 2–28, 5–42 and 10–70; ECE then
    physicalizes the awarded accounting currency. This removes ECE's duplicate
    Small Gold10 entry and its accidental 221-coin outlier.
12. ECE's selected I4 inventory data requests `$Currency`, but its English
    translation only defines `$Gold`. A same-path UTF-16LE-BOM override keeps
    `$Gold` as “Septims” and adds `$Currency` as “Currency”; speculative `$Ore`
    and `$Ingot` keys are intentionally absent.
13. ECE's language-neutral I4 JSON hard-codes the French label “Métal dwemer”
    for Dwarven scrap. A pinned same-path copy changes only that label to I4's
    existing `$DwarvenScrap` localization token. The ambiguous duplicate
    `DE5018` Gibber assignment remains unchanged pending runtime evidence.
14. C.O.I.N. 3.5.3's `Randomize Leveled Drakr` CDF rule omits the required
    `0x` prefix from its `Update.esm` removal form. CDF rejects that rule at
    runtime. A source-hash-pinned same-path copy corrects only
    `01DE5012|Update.esm` to `0xDE5012|Update.esm`, restoring the intended
    Drakr-face-to-leveled-Drakr randomization without replacing C.O.I.N.'s
    plugin or scripts.
15. ECE's C.O.I.N. quest binds the `EC_drakrsScript.Drakr` `MiscObject`
    property to `DE5016`, which is a leveled list and therefore fails Papyrus
    type binding. The ESPFE forwards that quest and changes only the property
    target to `DE5015`, the canonical Drakr Whale MISC used throughout ECE's
    own regional-conversion and item-patching configs. The four physical Drakr
    face records and their random leveled list remain intact. ECE's transaction
    architecture can count only that one canonical MISC, so `IsDrakrMoney` and
    Kolbjorn regional rules emit `DE5015`; ordinary ancient Nordic ruins still
    retain the four-face visual mix. Ancient rules explicitly defer to
    `IsDrakrMoney`, preventing five Solstheim Nordic sites from receiving
    attractive but non-spendable face variants.
16. C.O.I.N.'s three Drakr purse lists and its scripted Drakr pile also emit
    noncanonical face records. The ESPFE redirects only those regional pickup
    paths to `DE5015`; two owned leveled-list adapters preserve C.O.I.N.'s
    original counts and probabilities without altering its shared ancient-loot
    lists.
17. ECE distributes an Ohzer item and Apocrypha rules but no Ohzer transaction
    script, which otherwise leaves the currency unspendable. A second owned,
    start-enabled quest attaches `Ensrick_OhzerCurrencyScript` to the player.
    It uses ECE's public alternate-currency contract, initializes safely on
    existing saves already inside Apocrypha, and uses a neutral exchange rate;
    no unsupported regional price perk is invented.
18. ECE's main Septim quest carries three stale VMAD properties, while the
    selected Ulfric/Ma'dran patch references the obsolete `DES_MadranSwapper`
    class and eight stale quest-fragment properties. The ESPFE removes the
    orphaned bindings and migrates the alias to M.I.N.T. 1.0.6's shipped
    `DES_CurrencyFramework_BarterExclusion` class and current property names.
    Skyrim still tries to resolve the stale class while reading the earlier
    vendor plugin, so an independently authored `DES_MadranSwapper.pex` shim
    satisfies the class loader and maps legacy fields if an old instance is
    encountered. No vendor PEX or PSC is redistributed.
19. ECE weights only its canonical Drakr record and omits the three alternate
    Drakr faces, both Gibber faces retained from C.O.I.N., and M.I.N.T.'s
    unified Gibber used by the root-cave rule. A narrow owned SkyPatcher rule
    gives alternate Drakr weight 0.01 and all three Gibber records weight 0.02,
    so no physical currency silently escapes the weighted-money policy.
20. All five shipped ECE regional handlers use their inherited `altCoins`
    property before assigning it on the first location transition, while none
    of their VMAD attachments binds that property. The ESPFE adds the missing
    binding separately to Ulfric, Dram, Mede, canonical Drakr, and Oshka; it
    does not add the property only to ECE's separate base-script instance,
    whose state is not shared with the child script instances.
21. Ancient coins remain physical because C.O.I.N. auto-exchange is forced off.
    Ten owned, one-way recipes therefore provide a deliberate cash-out at
    Exchange Currency SE's bank counter without restoring automatic pickup
    conversion or enabling coin-to-ingot arbitrage. All four Drakr faces cash
    out at 20:3 Septims; Mala at 5:2; Mallari at 5:3; Nchuark at 4:1; Gibber
    (Mania) at 5:8; Gibber (Dementia) at 1:1; and M.I.N.T.'s unified root-cave
    Gibber at 1:1. The first nine batches preserve C.O.I.N. 3.5.3's effective
    installed defaults, while the unified Gibber follows the active M.I.N.T.
    core record's value of one. No reverse recipes are supplied.
22. Solstheim's mixed-Dram container rule is intentionally allowed to run once,
    late, after the specific ECE/C.O.I.N. regional and ancient rules. The owned
    generic-Septim CDF override and the owned default-Septim BOS rule both
    exclude the Solstheim root, and an earlier double-processing Dram rule was
    removed. This preserves M.I.N.T.'s native
    50/50 one-Septim-or-three-Dram roll for ordinary Solstheim containers while
    letting explicit routes consume their original `Gold001` first. Kolbjorn
    carries both Dram and Drakr keywords, so one final owned CDF correction
    converts the earlier direct Dram result to ECE's canonical Drakr. Loose
    coins, purses, containers, and the transaction handler therefore agree in
    Kolbjorn, Snowclad Ruins, Frostmoon Crag, Benkongerike, and other explicitly
    tagged locations instead of diverging because of file order.
23. Gyldenhul Barrow deliberately retains its authored Septim treasure rather
    than becoming a Drakr region. This matches both C.O.I.N.'s location
    exclusion and M.I.N.T.'s Deathbrand-treasure exclusions. A pinned same-name
    ECE KID override removes only its contradictory Gyldenhul `IsDrakrMoney`
    assignment, while the regional BOS rule also excludes the location
    defensively. Its eighty placed silver/gold pile references, ordinary loose
    coins, purses, and containers consequently follow one consistent Septim
    route.
24. ECE reapplies 0.01/0.02/0.03 to its physical copper, silver, and gold
    Septim records through SkyPatcher at runtime. A separate, later-sorting
    owned rule changes only those three weight fields to 0.06/0.07/0.13. The
    hidden `Gold001` accounting object and display-only plural proxies remain
    weightless, and no vendor file is edited or copied.
25. ECE's main Septim handler and all five regional handlers dereference both
    `OnLocationChange` parameters without checking for `None`. Valid exterior,
    worldspace, fast-travel, and root-location transitions produced 316
    `HasKeywordString()`-on-None errors in the September 3 playtest. Six
    same-class PEX overrides add only explicit old/new Location guards. Their
    non-null branches remain byte-for-source equivalent to ECE 4.1.1, verified
    against pinned vendor hashes; no currency value, route, or notification is
    changed.

The ECE omnibus `ECE_CraftAndRecipes.ini`, malformed
`ECE_AncientCoinsToIngot.ini`, and `exchangeCurrency_patch_BS.esp` are
intentionally absent or masked. They respectively overwrite unrelated
skooma/Dwarven recipes, reference nonexistent/wrong currencies in smelting
recipes, and alter Bruma jewelry, materials, hides and quest rewards. A later
owned ESPFE may forward only approved recipes or Bruma currency rewards after
the final load order exists.

ECE ships Ohzer and Varken currency records and distribution rules but assigns
neither location keyword. This package activates Ohzer only for the evidenced
Apocrypha location tree. Varken remains deliberately dormant: no location
receives `IsVarkenMoney` until a reviewed Dremora-region policy exists.

## Required runtime and load order

Install after C.O.I.N. 3.5.3, M.I.N.T. 1.0.6, Exchange Currency Enhanced
4.1.1 and `exchangeCurrency_patch_COIN.esp`, so these same-path masks and
record overrides win. It also requires current Base Object
Swapper, Keyword Item Distributor, SkyPatcher, Inventory Interface Information
Injector (`I4IconAddon.esp`), Currency Swapper, Container Distribution Framework
and Dynamic Dialogue Replacer, plus Exchange Currency SE, Notification Filter,
powerofthree's Tweaks, SkyUI and Beyond Skyrim - Bruma. The current native gate
is Skyrim 1.7.104, SKSE 2.3.1 and Address Library v13/format 5. Description
Framework remains intentionally omitted because it is cosmetic and its released
DLL cannot parse that Address Library format.

ECE's compact `SL99Exchanger.esp` must win the MO2 left-pane file conflict over
the separate Exchange Currency SE 3.00 copy. The required winner is ESL-flagged,
159,056 bytes, SHA-256
`C9342F1B669A3AE1F4A51E0CA8FBD9CDA3AEC915D36DC4CC9A0798B09E5B2446`,
has 470 major records, and owns `SL99CraftingExchangeBank` at
`000801:SL99Exchanger.esp`. Generation and post-build audit both fail closed if
any part of that identity differs; the similarly named full ESP places its bank
keyword elsewhere and is not interchangeable.

The generator does not write to the live profile. A complete rebuild is:

```powershell
pwsh ./mods/currency-integration/regenerate.ps1 `
  -ToolchainManifest ./toolchain.json `
  -InstanceRoot ../mo2-instances/skyrim-se `
  -GameRoot "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition"
```

That command verifies pinned source/tool hashes, proves the six ECE-derived
sources differ only by their null guards, compiles all nine packaged Papyrus
scripts twice, generates the plugin twice through the MO2 VFS, checks its exact
record set and all links, validates the file-relative SEQ identity, performs a
checked Spriggit semantic roundtrip, and builds the archive twice byte-for-byte.
Caprica debug information and CK optimizations are disabled. Its PEX header
compile timestamp, checkout-dependent source path, build user and machine name
are normalized to fixed release metadata, so identical source remains
byte-identical across worktrees, clone paths and builders.

The 45-record ESPFE declares exactly nine direct masters: Skyrim, Update,
Dragonborn, Exchange Currency SE, ECE, C.O.I.N., M.I.N.T., the selected
Ulfric/Ma'dran patch, and ECE's C.O.I.N. patch. Exchange Currency SE is now a
direct master because the ten cash-out recipes use its bank-crafting keyword;
Dawnguard and HearthFires remain transitive vendor dependencies. The audit
derives the direct-master set from every record owner and serialized FormLink
and requires exact equality; the resulting SEQ identifies the two owned
start-enabled quests as file-relative `09000800` and `09000803`.

Runtime acceptance still requires a disposable save: inspect an ordinary
countertop, each ancient-site family, Bruma city/Ayleid locations, Apocrypha,
Solstheim regional sites and exchangers; verify physical coins survive pickup,
then repeat after Journal/MCM close, save/load and container reset. Because the
five inherited `altCoins` VMAD bindings are newly added to a released quest,
test both a fresh game and a save created before this integration revision.

## Credits and distribution

Original systems and records remain the work of their respective authors:
[C.O.I.N.](https://www.nexusmods.com/skyrimspecialedition/mods/51439),
[M.I.N.T.](https://www.nexusmods.com/skyrimspecialedition/mods/178940), and
[Exchange Currency Enhanced](https://www.nexusmods.com/skyrimspecialedition/mods/141884).
The two same-path M.I.N.T. masks, ECE's same-path I4 JSON, and C.O.I.N.'s
same-path CDF JSON are narrowly modified bug-fix configurations, redistributed
with credit under their authors' Nexus modification/upload terms. The ECE
translation override also preserves its shipped `$Gold` line. These
vendor-derived text/config files are not relicensed as MIT. The owned Ohzer
handler and six null-Location repairs are interoperability derivatives of ECE
scripts and are likewise excluded from MIT; they remain under ECE's applicable
Nexus terms, with credit and without sale or Donation Points. The ESP contains 14 newly
authored records and 31 compatibility overrides. MIT covers our source and
original record content, but not the vendor-origin data serialized into those
overrides; the mixed-terms ESP must not be described as an all-MIT binary.
The archive includes `LICENSE.txt` and a dependency/terms `NOTICE.txt`. This
package contains no WiZkiD asset; users must obtain
[Ancient Imperial Septims](https://www.nexusmods.com/skyrimspecialedition/mods/37545)
separately, and its no-redistribution terms continue to apply.
