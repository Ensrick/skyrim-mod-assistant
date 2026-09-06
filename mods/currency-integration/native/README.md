# Ensrick Currency Denominations native bridge

This original CommonLibSSE plug-in keeps `Gold001` as the transaction ledger
while mirroring its value with droppable physical 1/10/100 coins. It also
normalizes reviewed corpse/container sources before vanilla or QuickLoot reads
them. The generated ESP and runtime JSON are required; the DLL is not a
standalone replacement for those records.

The first supported playthrough must be a new character. A save made after
successful admission carries a versioned 40-byte ledger checkpoint. Later
loads accept exactly that schema and exact ledger-form fingerprint. Missing,
old, malformed, duplicate, or mismatched checkpoints fail closed. This does
not make an old save safe after the companion ESP has removed legacy currency
owners.

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
