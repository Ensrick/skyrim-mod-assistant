# Currency accounting handover: payout audit

Status: implementation/review input, not a runtime acceptance result. This audit
made no live mod, save, inventory, or game changes. Findings were sent to the
isolated denomination implementation owner and tracked under #209.

## Evidence boundary

Inspected the installed ECE 4.1.1, Exchange Currency SE bank archive, C.O.I.N.
scripts and owned regional integration. The installed ECE function bytecode was
freshly disassembled with headless Champollion 1.3.2; the bundled decompiled PSC
was not assumed to be authoritative. The exact `EC_septimsFunctions.pex` SHA-256
is `C969F0B21D7C9802FF122816A86B26ACA5DB881B688DA53D7633B909EA55AC30`.
Vendor scripts, extracted archive members and decompilations remain private;
only this original factual report is published.

## Accounting writers that must not coexist

| Existing path | Existing writes | Implication for the native owner |
| --- | --- | --- |
| ECE `getBeneficeBis` / `getBenefice` | Creates physical denominations to mirror backend Gold001 already received | Disable this mirror before admitting the new owner; otherwise a backend reward can be credited twice |
| ECE `getBeneficeSilver` / `getBeneficeGold` | Creates silver/gold, but puts its copper remainder into Gold001 itself | Retiring only the derived menu handler is insufficient unless every caller/instance is retired |
| ECE `goldCheck`, `locationSwitch`, `altConversion` | Reconciles physical and backend money in both directions | Conflicts with another authoritative reconciliation loop |
| ECE `septimsOnActor` / `moneyOnActor` | Removes the target actor's Gold001 and adds one physical copper/regional coin per unit | Direct explanation for corpse inventories dominated by copper |
| ECE physical OnItemAdded / OnItemRemoved | Credits/debits Gold001 during inventory/container operations | Must be retired before native pickup, drop and storage mirroring |
| C.O.I.N. automatic exchanger | Removes ancient coin forms and pays Gold001, retaining fractional change internally | Preserve the approved auto-exchange-off policy; native modern-family accounting must not count those ancient removals as a second expense |

The replacement must conserve a combined transaction, not choose whichever side
changed last. Tests must cover a backend reward and physical pickup in the same
batch, physical removal and backend spending together, conversion in either
direction, zero balance, self-generated notifications and save/load boundaries.

## Bank and recipe endpoints

The Exchange Currency SE BSA contains exactly two compiled scripts:

- `SL99EXC_TIF__ExchangeTopic.pex`, SHA-256
  `6F8E1C245ECDECAFFA32F65E899983C526958E1A305081C277AC5DA1E17C55CE`,
  activates the appropriate bank/company/shop crafting marker. It does not add
  or remove money.
- `SL99EXCAddFactionSpell.pex`, SHA-256
  `D7835ECB2F5B2FB483E862B1217670374C709116783528DBAE18E30D686A79D3`,
  changes merchant factions; it does not pay currency.

The actual exchange is therefore a COBJ recipe transaction, not another bank
script payout. Inspected records: 28 in the winning compact SL99 plugin, 82 in
ECE, 33 in its C.O.I.N. patch, and 27 in the installed integration. Existing
owned overrides disable 17 coin-to-ingot recipes; ten owned ancient cash-out
recipes produce backend Gold001 only.

Sixteen surviving modern-currency exchange recipes use non-parity regional
rates. Examples include 375 Medes to 500 Gold001, 500 Gold001 to 600 Ulfrics,
and 500 Gold001 to 750 Oshkas. These cannot remain unchanged if every modern
copper is now worth one common unit and regional relabeling preserves value.
The affected C.O.I.N.-patch local FormIDs are `82D`, `82E`, `82F`, `830`, `834`,
`835`, `84B`, `84C`, `84D`, `84F`, `853`, `854`, `873`, `874`, `875`, `876`.
The generation owner must reconcile or explicitly disable these redundant
exchange paths, with a matching post-build audit. Existing approved fees must
not be changed accidentally. No automatic economy-design approval is implied.

Also review `DE5015:Update.esm`: if the canonical Drakr becomes native tender,
the existing twenty-for-three ancient bank recipe must not simultaneously
value it at a different rate. Face variants and canonical spendable tender
must have an explicit, non-overlapping classification.

## Existing-save admission remains a separate gate

Stopping a quest is not, by itself, evidence that all old latent script work
is gone. The inspected handlers contain menu waits, delayed refresh functions
that register menus again, and `ExitMintExchanger`, which waits two seconds
before replacing all backend Gold001 with a regional count. A pending instance
must not be allowed to resume over a new ledger.

CurrencySwapper also persists a custom currency independently of these quests.
The implementation must await a successful `SEA_BarterFunctions.ResetCurrency`
callback at the appropriate load/new-game boundary before accepting money
events. That reset alone does not prove legacy Papyrus stacks are retired.
If safe old-save migration cannot be established, require a documented fresh
test character instead of mutating the user's existing save under an assumed
safety guarantee.

## Required acceptance

Fresh corpse and purse contents, Quick Loot's first displayed contents, normal
container transfer, loose regional coins, pickup/drop/storage, shopping,
training, bank exchanges, zero funds, and save/reload all need real runtime
acceptance. Native unit tests and static record audits are necessary but do not
replace it. Regional items need explicit Copper/Silver/Gold names as well as
distinct visuals so their identity does not depend on color perception.
