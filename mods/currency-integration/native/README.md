# Ensrick Currency Denominations native bridge

This original CommonLibSSE plug-in keeps `Gold001` as the transaction ledger
while mirroring its value with droppable physical 1/10/100 coins. It also
normalizes reviewed corpse/container sources before vanilla or QuickLoot reads
them. The generated ESP and runtime JSON are required; the DLL is not a
standalone replacement for those records.

The 0.2.0 native bridge requires configuration schema 2. Every face/design
family must supply exactly `copper=1`, `silver=10`, and `gold=100`, with distinct
physical forms. Singleton families, mislabeled tiers, duplicate salts, legacy
ancient exclusions, and references to unknown or disabled routing families
are rejected. No ancient-currency exemption remains.

`routing.rules` is an explicit ordered array of
`{id, anyKeywords, familyIds}` objects. The first rule matching the source's
location or any parent location wins. A rule can list multiple regional face
designs; rendezvous hashing of the source identity and each unique family salt
selects exactly one of them for the existing total value. This does not spawn
one budget per design. The player's wallet uses identity zero for a stable
design within that route. Unmatched locations use the single configured
fallback family. Source safety still excludes protected actors, quest/vendor
storage and other non-reviewed inventories; those are source exceptions, not
currency-family or denomination exceptions.

An optional family `inputAliases: [{tier, form}]` array recognizes an authored
duplicate source form, such as Mania's second Gibber copper form. The alias
inherits its named canonical tier's value; it cannot specify a different
exchange rate. Alias holdings participate in inventory valuation, removal,
verification and full rollback, but payout/wallet output always contains zero
aliases. They are not fourth denominations. Initialization verifies the
winning MISC value and VendorItemNoSale keyword for canonical and alias forms.

The first supported playthrough must be a new character. A save made after
successful admission carries a versioned 40-byte ledger checkpoint. Later
loads accept exactly that schema and exact ledger-form fingerprint. Missing,
old, malformed, duplicate, or mismatched checkpoints fail closed. This does
not make an old save safe after the companion ESP has removed legacy currency
owners.

This candidate is not compatible with the published partial-currency 0.3.0
configuration or its saves. The ledger fingerprint namespace is now
`EnsrickCurrencyLedgerV2`; its serialized contract includes named tier bindings,
family salts/enabled state/labels/perks, routing rule order and membership,
distribution and accounting flags. The existing 40-byte save checkpoint
structure is unchanged, but its old fingerprint fails closed. A fresh
character is required after the complete companion package is installed.

Build without touching the game or MO2 profile:

```powershell
./build-native.ps1 `
  -CommonLibRoot C:/path/to/CommonLibSSE-NG `
  -OutputRoot C:/b/currency `
  -RuntimeConfig ../package/SKSE/Plugins/EnsrickCurrencyDenominations.json
```

`CommonLibRoot` must be a clean tracked checkout at commit
`90a64a4d65ce659a139137c968f42151bb6ecec9`. Keep `OutputRoot` short because
the vcpkg/DirectX dependency object paths can exceed legacy Windows path limits
when nested under the repository. The script emits a DLL plus a receipt that
hashes every native source input and records the toolchain and CommonLib
licence provenance.

`RuntimeConfig` is mandatory. The build validates and hashes the exact JSON
before compiling, repeats the source/config snapshot after all tests, and
refuses to emit a receipt if either input set changed during the build.

The original code in this directory is available under the repository's MIT
licence. The linked DLL is a combined work with CommonLibSSE-NG and must be
distributed under its GPL-3.0-or-later terms and explicit exceptions, with
corresponding source. A distributable package must include the exact pinned
CommonLib `COPYING` and `EXCEPTIONS.md`, the repository MIT notice, the full
QuickLoot IE MIT notice in `third_party/QuickLootIE-LICENSE.txt`, and dependency
notices. No gameplay/runtime acceptance is claimed by a successful compile.
