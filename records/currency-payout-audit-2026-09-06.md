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

The independent M.I.N.T. audit also identified one conflicting owner added by
our older generator: Ma'dran alias 5 of `000002:WindhelmUsesUlfrics.esp` is
assigned `DES_CurrencyFramework_BarterExclusion`. That handler resets Currency
Swapper on activation and calls its currency-switching function after dialogue
closes. The new generator must remove that exact ownership path. Do not stop
the shared `000800:M.I.N.T.esp` functions quest or the whole Windhelm/Dram
module quests; they retain dialogue, exchange and service responsibilities.
Keep the narrow `DE5037:Update.esm` automatic-conversion-off policy. Module
price/global maintenance stripped by prior ECE overrides is a separate
compatibility obligation, not permission to restore all original switching
scripts.

The follow-up winning-record audit confirmed 29 old modern-exchange INFO
callbacks still win: Dram local IDs `17,19,1B,1D,1F,25,27,29,2B,32,34,36,38,3A`
and Ulfric `53,54,55,56,57,58,59,5A,5B,1F,5C,5D,93,95,92` in their respective
module ESPs. Nine additional Dram responses belong to those same obsolete
exchange branches (`64,65,66,7,67,68,69,6A,9`); `7` retains an older
`TIF__ExchangeAll` attachment. They cannot be assumed absent merely because
their quest-level currency-switching scripts were removed.

Separately, Ulfric INFOs `A` and `C` are horse-purchase responses. Their
`GetItemCount` conditions count `DE5024:Update.esm` physical copper against
the `0000C9:WindhelmUsesUlfrics.esp` horse-cost global. Forward only the counted
form to backend Gold001, preserving the cost global and unrelated dialogue.
The winning ECE overrides already remove `DialogueGenericScript` from both
module quests; do not restore its obsolete copper-only Gold binding while
restoring unrelated cost maintenance. All these INFO records have no EditorID;
audit identities by FormKey, type and exact relevant fields instead.

Stopping a quest is not, by itself, evidence that all old latent script work
is gone. The inspected handlers contain menu waits, delayed refresh functions
that register menus again, and `ExitMintExchanger`, which waits two seconds
before replacing all backend Gold001 with a regional count. A pending instance
must not be allowed to resume over a new ledger.

CurrencySwapper also persists a custom currency independently of these quests.
The implementation must await a successful CurrencySwapper backend-selection
callback at the appropriate load/new-game boundary before accepting money
events. The reviewed candidate calls `SEA_BarterFunctions.SetCurrency(Gold001)`;
the pinned source confirms that this also clears per-trainer currency overrides.
Successful selection alone does not prove legacy Papyrus stacks are retired.
If safe old-save migration cannot be established, require a documented fresh
test character instead of mutating the user's existing save under an assumed
safety guarantee.

Native review also caught and returned three implementation defects before
deployment: SKSE's PostLoadGame bool is encoded in the pointer value, not a
dereferenceable bool pointer; SKSE drains newly queued tasks in the same loop,
so immediate self-requeue is not a next-frame timer; and an origin marker alone
cannot preserve a pickup/drop awaiting reconciliation when an autosave occurs.
The revised candidate must use the actual message contract, bounded scheduling,
and a validated serialized ledger checkpoint. These remain candidate review
requirements, not evidence of an in-game pass.

## Required acceptance

The read-only `audit/currency_save_gate.py` now gates `launch_verify` autoload:
the selected `.ess` must have an intact SKSE v1 co-save wrapper containing
exactly one native ECDN/ECMK v2 checkpoint with the matching ledger-configuration
fingerprint. Missing, old, duplicate, malformed and changed-configuration
checkpoints are refused before launch. A menu-only observation remains allowed
and is never a loaded-save PASS. General preflight prints the fresh-character
restriction rather than implying that any existing save is safe. Thirteen synthetic
test groups pass, including every truncation boundary, pending pickup/spending/
drop checkpoints and winner-config drift. No real save is modified by this gate.

The gate also requires the companion ESP to be reachable and active, and pins
the winning DLL, JSON and ESP to the trusted repository release receipt. It
rejects missing, disabled, stale and overridden companions, a replaced DLL,
and missing or malformed receipts. A mod-local receipt cannot authorize itself.
This closes the case where a valid co-save would otherwise pass while runtime
initialization failed because its companion records were unavailable.

This tool cannot prevent a person from manually selecting an incompatible save
from Skyrim's own menu. Do not do so with the new package: retain the old package
and its save together, and use a fresh character for initial acceptance.

Fresh corpse and purse contents, Quick Loot's first displayed contents, normal
container transfer, loose regional coins, pickup/drop/storage, shopping,
training, bank exchanges, zero funds, and save/reload all need real runtime
acceptance. Native unit tests and static record audits are necessary but do not
replace it. Regional items need explicit Copper/Silver/Gold names as well as
distinct visuals so their identity does not depend on color perception.

## Final integration findings

The two Windhelm horse INFOs require **both** the GetItemCount condition and
their VMAD `Gold001` property retargeted to backend `00000F:Skyrim.esm`.
The actual vanilla `TIF__0009841D` and `TIF__00098422` handlers debit that
property. Retargeting only the condition would allow a purchase without the
correct debit. Preserve the five other property bindings, including horse
alias IDs 40 and 31, the cost global and original fragments. The Dram cost-only
shim must look up the exact `DES_UlfricWindhelmServicesQuest` EditorID, with
the `Quest` suffix. Existing blank rental INFOs are not restored, and bounty
responses retain vanilla `PlayerPayCrimeGold` behavior.

The native actor gate must inspect effective/template data, not only the raw
NPC base flags: vanilla leveled bandit and commoner wrappers have zero flags
while inheriting BaseData. The reviewed implementation bounds template walks,
rejects cycles and retains unique/essential/protected/vendor exclusions across
the chain. Fresh-game admission conserves physical coins received before the
asynchronous backend-selection callback instead of erasing them. Source
rollback failure suspends accounting; stale generation callbacks are ignored.
Ancient-source passthrough is distinct from the player's modern fallback so
the CDF Drakr route is not silently changed into Septims.

Root generated and independently repeated 18 SSE coin NIFs and 18 BC7 diffuse
textures. All 36 hashes and sizes match across two clean builds; all mesh
geometry and non-diffuse bindings are preserved. Mede/Dram/Ulfric diffuses are
512 x 1024; other modern families are 1024 x 1024, with complete mip chains.
Copper/Silver/Gold treatment preserves engraving and is supplemented by names
and inventory icon colors. These are private derived assets, not permission
to redistribute the vendor designs. Septim weights remain 0.06/0.07/0.13;
regional source weights are retained, not newly certified as realistic.
