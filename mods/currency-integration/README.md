# Ensrick Regional Currency Integration 0.3.0

This module is the owned Skyrim Special Edition compatibility layer for the
approved physical-currency stack. It ships an ESL-flagged ESP, a native SKSE
ledger bridge, four narrow Papyrus compatibility scripts, winning distribution
configuration, and preconverted tier assets. It does not modify a vendor mod or
the live MO2 profile while being built.

## Release boundary

Version 0.3.0 requires a fresh character. Do not load a save first admitted by
an older currency architecture. The native bridge writes a versioned ledger
checkpoint and fails closed when that checkpoint is missing, duplicated,
malformed, old, or bound to a different configuration. A menu-only launch is
not gameplay acceptance.

The private, locally generated modlist archive contains the reviewed SSE-ready
NIF/DDS outputs already. The public source release contains only the reproducible
recipe and receipts; licensed derivatives must be rebuilt locally from the
required vendor downloads. Cathedral Assets Optimizer is not a runtime
dependency, and CAO alone does not reproduce the tier textures: the pinned
recipe uses the NIF port tool, ImageMagick, and DirectXTex. Users should not run
CAO over an already generated package because that invalidates the asset hashes
and can change shader or texture bindings.

## Accounting model

`Gold001` (`00000F:Skyrim.esm`) remains the hidden transaction ledger. The
native owner `EnsrickCurrencyDenominations` mirrors the same conserved value in
physical coins:

| Tier | Value |
| --- | ---: |
| Copper | 1 |
| Silver | 10 |
| Gold | 100 |

Every Septim and enabled modern family uses those values. The physical forms
are droppable and storable, but all carry Skyrim's `VendorNoSale` keyword
(`0FF9FB`) so ordinary barter cannot count the same value twice. The backend is
never included among physical forms.

Active modern families are Septim, Mede, Ulfric, Dram, Oshka, and Ohzer.
Varken's three records and assets exist, but its route remains disabled because
the installed sources contain no exact authored Varken location assignment.
Canonical Drakr Whale (`DE5015:Update.esm`) and Sancar
(`DE5023:Update.esm`) are reviewed singleton value-1 families. Drakr Dragon,
Moth, and Owl remain ancient face coins and are never treated as modern ledger
tender.

## Source conversion and purse policy

The bridge works at the NPC/container/purse source before normal inventory or
Quick Loot presentation. It is deterministic and idempotent for the stable
identity `(source form, reference FormID, family)`:

- 80% uses the efficient 100/10/1 decomposition.
- 20% breaks at most one largest available tier into the next tier.
- Exact value is conserved in both branches.
- Examples: 24 becomes `2 silver + 4 copper` or
  `1 silver + 14 copper`; 100 becomes `1 gold` or `10 silver`; 110
  becomes `1 gold + 1 silver` or `11 silver`.

Only dead, generic NPCs pass the actor gate. Player, teammate/follower, vendor,
unique, persistent, essential, protected, owned, and active-quest-alias actors
fail closed. Only respawning, nonpersistent, ownerless, nonvendor,
non-quest containers pass the container gate. If the runtime cannot prove a
container safe, it leaves it unchanged and increments an exact reason counter.
The six typed purse base forms and six budget lists are explicit allowlists.

Loose countertop/world coins keep the authored BOS 75% copper, 20% silver, 5%
gold choice. Regional BOS rules map copper to copper, silver to silver, and gold
to gold; they do not flatten a wallet into one regional base coin. Bruma Ayleid
sites retain Mala precedence, while Wyrmstooth and Beyond Reach remain on the
default Septim fallback. Ancient Nordic, Dwemer, Falmer, Ayleid, and root-cave
routes remain outside modern ledger conversion.

## Single-owner compatibility

The ESP removes the transaction attachments and start-enabled flag from exactly
two ECE player-alias quests:

- `000B63:exchangeCurrency_enhanced.esp` — `EC_septimsFunctions` and
  `EC_septimsScript`.
- `000827:exchangeCurrency_patch_COIN.esp` — `EC_altCurrencyFunctions`,
  Ulfric, Dram, Mede, Drakr, and Oshka transaction scripts.

That retires ECE's `getBenefice`, `getBeneficeBis`,
`getBeneficeSilver`, `getBeneficeGold`, `goldCheck`, `locationSwitch`,
`altConversion`, `septimsOnActor`, `moneyOnActor`, and physical
`OnItemAdded`/`OnItemRemoved` accounting paths. The native bridge replaces the
canonical Drakr 1:1 route, so the shared ECE quest can be retired without
losing that region.

The M.I.N.T. Dram and Ulfric module quests are preserved. Their winning VMADs
restore only property-compatible cost/stage maintenance and the shipped empty
player-alias proxies; no `SwapCurrency`, `ResetCurrency`, `SetGoldValue`, or
module-registration call remains. Windhelm alias 5's obsolete
`DES_MadranSwapper` transaction attachment is removed, and the same-name
packaged class is inert for stale loader instances. The existing ECE winners
already removed `DialogueGenericScript`; it is not restored.

The 29 modern-exchange callback INFOs and nine exchange-only failure responses
are hidden while `DES_ConvertCoins` is forced to zero. Exact local IDs are:

- Morrowind/Dram: `17,19,1B,1D,1F,25,27,29,2B,32,34,36,38,3A` plus
  failure rows `64,65,66,7,67,68,69,6A,9`.
- Windhelm/Ulfric: `53,54,55,56,57,58,59,5A,5B,1F,5C,5D,93,95,92`.

Windhelm horse-purchase INFOs `A` and `C` instead retain their original price
global and dialogue, but their `GetItemCount` operand is forwarded from
physical Ulfric copper to backend `Gold001`.

All 17 currency-to-ingot COBJ recipes are disabled. The 16 obsolete non-parity
modern bank COBJ local IDs `82D,82E,82F,830,834,835,84B,84C,84D,84F,853,854,
873,874,875,876` in `exchangeCurrency_patch_COIN.esp` are also disabled.
Canonical Drakr Whale no longer has a 20-to-3 recipe. The three noncanonical
Drakr faces and authored Mala, Mallari, Nchuark, and Gibber rates remain
available at the ancient bank.

## Visual and UI contract

Mede, Ulfric, Dram, Oshka, Ohzer, and dormant Varken each have genuine Copper,
Silver, and Gold NIF/DDS variants. The transformation changes the diffuse tier
appearance while preserving geometry, normal/mask/environment bindings, and
the family's approved carry weight. New diffuses never exceed 1024 pixels.
This is a clear denomination treatment, not a claim of historically realistic
coin geometry. Inventory Injector assigns explicit copper, silver, and gold
icon colors to all 23 physical forms; names always include the tier so the
distinction does not depend on color perception.

## Required runtime and order

The generated ESP has exactly these eleven direct masters, in order:

1. `Skyrim.esm`
2. `Update.esm`
3. `HearthFires.esm`
4. `Dragonborn.esm`
5. `SL99Exchanger.esp`
6. `exchangeCurrency_enhanced.esp`
7. `C.O.I.N.esp`
8. `M.I.N.T.esp`
9. `MorrowindUsesDrams.esp`
10. `WindhelmUsesUlfrics.esp`
11. `exchangeCurrency_patch_COIN.esp`

The package must win conflicts for its ESP, PEX files, native DLL/config,
assets, BOS/KID/CDF/SkyPatcher rules, translation, and I4 rules. It targets
Skyrim runtime 1.7.104 and SKSE 2.3.1. Existing framework requirements include
C.O.I.N., M.I.N.T., Exchange Currency Enhanced, Exchange Currency SE, Base
Object Swapper, Keyword Item Distributor, Container Distribution Framework,
SkyPatcher, Inventory Interface Information Injector, and Quick Loot IE when
Quick Loot is used.

## Deterministic build

The final rebuild is intentionally serialized because ESP generation reads the
MO2 virtual filesystem:

```powershell
pwsh ./mods/currency-integration/regenerate.ps1 `
  -ToolchainManifest ./toolchain.json `
  -InstanceRoot ../mo2-instances/skyrim-se `
  -GameRoot "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition" `
  -Version 0.3.0
```

The pipeline refuses to run while MO2 or Skyrim is open, hashes every pinned
tool/input, compiles the four PEX files twice, normalizes their metadata,
generates the ESP twice, audits exact records/links/SEQ, checks a Spriggit
semantic round trip, runs `validate.py`, and creates the archive twice. It does
not install into the game or mutate the selected profile.

The ESP gate expects 286 records: 3 ACTI, 152 LVLI, 22 MISC, 1 GLOB, 42 COBJ,
5 QUST, 1 KYWD, 20 parent DIAL, and 40 INFO. Each parent DIAL must retain its
source metadata and contain exactly the targeted INFO overrides with no sibling
responses. The gate also requires no deleted records, one SEQ entry
(`0B000800`), 33 disabled recipes, the exact two ECE owner removals, the two
cost-only M.I.N.T. quest bindings, 38 disabled exchange INFOs, and two service
condition retargets.

## Licensing and redistribution

Read `NOTICE.txt`, `DEPENDENCIES.txt`, `SOURCE.txt`, and every bundled licence
before redistribution. Original project source is offered under MIT where
identified. The statically linked native DLL is a combined work with
CommonLibSSE-NG and is distributed under GPL-3.0-or-later plus CommonLib's
explicit exceptions, with corresponding source. The generated ESP and
interoperability data are mixed-terms artifacts and must not be represented as
all-MIT. Vendor mods remain required separate downloads.

The two cost-only M.I.N.T. Papyrus derivatives credit Tate Taylor and retain
M.I.N.T.'s upstream terms rather than the Ensrick MIT grant. Those permissions
were checked on 2026-09-06 at
<https://www.nexusmods.com/skyrimspecialedition/mods/178940>; they allow
credited modifications and upload elsewhere, prohibit paid use, and do not
authorize voice-asset changes. These compatibility scripts contain no voice
assets.

## Acceptance still required

Passing builds and static tests does not prove gameplay. Release acceptance
must use a fresh test character and cover corpse/purse contents, Quick Loot's
first view, normal container transfer, loose regional coins, pickup/drop/
storage, shopping, training, the remaining ancient bank exchanges, zero funds,
backend rewards, simultaneous physical/backend changes, and save/reload. Keep
the previous package and its saves together until that matrix passes.
