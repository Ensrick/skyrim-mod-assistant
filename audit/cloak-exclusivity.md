# Full-cloak equipment repair

This repairs equipment-slot exclusion, not leveled-list distribution. The user's
September 5 test is consistent with the records: Sons of Skyrim's full cloaks
occupy 40/46, while Pelts 'o' Plenty full cloaks occupy 57. The engine therefore
has no shared equipment bit with which to reject the pair.

## Scope and classification

The original SkyPatcher configuration adds one reserved **slot 58/index 28** bit
to an explicit allowlist while preserving every original ARMO/ARMA slot. No NIF
partition, texture, vendor plugin, item count, or NPC inventory is rewritten.
The existing `bipedSlotsToAdd` operation updates the selected ARMO and every
attached ARMA. Both the current source implementation and the installed
binary's parser-token presence were inspected; the latter is not proof of
execution in the game.

| Source | Patched full cloaks/capes | Important exclusions |
|---|---:|---|
| Sons of Skyrim |12|Two fur collars; all armor and pauldrons|
| Cloaks - RMB SPCH |122|No unrelated records are present in its armor group|
| Pelts 'o' Plenty |99|Ten mantle-family pieces, ten hoods, one body armor|
| Campfire |4|Backpacks, bedrolls, and other equipment|
| More Scarves |3|Nine scarves/shawls/gaiters|
| Scale Nord |0|Both fur collars remain unchanged|

The old audit's 109 “Pelts cloaks” was a slot count, not an anatomical
classification. Nine explicitly named mantles are shoulder-only geometry; the
tenth `FurPeltMantle` displays “Pelt Cloak (Crude)” but uses a short upper-body
fur mantle mesh. All ten are conservatively excluded from the full-cloak group.
The actual `PeltCloakPauldrons` variants retain long HDT cloak chains and are
cloaks shaped for pauldrons, not standalone pauldrons.

This is **additive exclusion only**. Existing slot conflicts remain: Sons/Scale
Nord collars conflict with slot 46 cloth cloaks; Pelts mantles conflict with
slot 57 Pelts cloaks. It introduces no additional restriction on those smaller
items. Letting every collar/mantle pair with every cloak would be a separate
ARMO/ARMA/NIF slot migration. MrDragonfly slot 57 accessories are not moved or
newly blocked by slot 58.

## Why not use slot 57?

A first-pass slot 57 union was stopped by the generator's count assertion
before a package existed. It would have blocked cloth cloaks together with the
ten small fur mantles the user specifically exempted. Slot 56 is also occupied
by a Creation Club ArmorAddon. Slots 58/59 are the candidate unused bits; 58 is
reserved only after record, runtime-config, and participating mesh checks.

`biped_slot_audit.py` parses all 348 current official/CCC/managed plugins,
8,747 ARMO declarations and 4,315 ARMA declarations. Slot 58 has zero record
users. Losing overrides are included conservatively. The strict reader rejects
bad TES4 lengths, malformed groups/subrecords, and malformed compressed streams.
The generator additionally checks all active armor declarations, including
cross-plugin overrides, for any excluded item sharing an ARMA that the patch
would mutate. Original source files are hash-pinned and a changed version
requires classification review.

The September 5 layer proof covers 240 selected armors, 224 attached armor
addons, 302 explicit model paths and 274 additional `_0.nif` weight-slider
companions. All 569 present models parsed successfully; none uses partition
58. Seven absent paths are recorded as absence sentinels, not successful
models. This includes two Cloaks developer-test meshes, two existing Pelts
horker-pauldron cloak mesh references, and three derived weight companions.
The missing Pelts models remain a separate pre-existing defect to investigate.
All 34 winning SkyPatcher INIs were inspected; none adds or otherwise operates
on index 28. The proof binds the active runtime DLL, configurations, winning
loose meshes and participating Campfire BSA. Any relevant input change requires
a fresh audit; slot 58 is not claimed universally free across arbitrary mods.

## Rebuild and installation boundary

### September 6 book-config admission and Apocalypse review

Book Covers Skyrim SkyPatched (SSE 109254, file 461289) and its Missing Books
addition (149814, file 755004) introduce five BOOK-only SkyPatcher INIs, with
316/401/52/10/130 active lines respectively. The layer-proof script admits
only their exact virtual paths and SHA-256 digests, and independently requires
every active line to select `filterByBooks` and use only `model`,
`alternateTexturesToAdd`, and `inventoryArt` operations. These are book art
changes, not biped or equipment operations. Missing optional files add no
allowance; changed bytes, renamed files and unknown extra files do not pass a
generic config-count exception. With all five and the reviewed currency
config present, the expected total becomes 40 instead of 35. The original
one biped config / five biped directive lines requirement remains unchanged.
The proof records which exact book files were admitted.

`audit/test_nif_slot_layer_config_admission.ps1` exercises the production
functions extracted through PowerShell's AST, using original synthetic
fixtures only. It rejects hash drift, count drift, non-BOOK selectors,
equipment operations, unknown operations and malformed/empty assignments.
Run it with PowerShell 7; it does not read or write MO2 or launch the game.

The inspected Apocalypse 10.3.0 ESP (SSE 1090, file 793875, SHA-256
`B0A9632372F2117F7D96583E1522B42758F414129D3572F848B8F7AC65681384`)
contains 87 ARMO / 65 ARMA records. Its
`0B1C12:Apocalypse - Magic of Skyrim.esp` (`WB_ConjureCraftlord_Cloak`) is
NonPlayable, weight zero and slot 35 (Amulet); its own ARMA `0B1C11` also uses
35 and names `apocnew/nikinoodles_model/cloak_1.nif`. The dedicated outfit
`123E5E` contains it and is assigned to Craftlord NPC `0B00DB`, whose editor
ID is `WB_Con_Human_Actor_ConjureCraftlord`. The active RMB base cloak injector
targets 58 explicit Skyrim/Dawnguard outfits, not this Apocalypse outfit.

The reviewed conclusion is to leave the six-source, 240-item equipment
allowlist unchanged during this installation. A named non-player summon
costume is not automatically a new ordinary equip/distribution target. This
does not establish that every new-land/summon costume can never overlap a
future outfit injector; a future distribution or playable-item change needs
its own review. Apocalypse's new ARMO/ARMA declarations still participate in
the global slot-58 and shared-ARMA scan. No blanket NonPlayable exclusion was
added to that scan or to the generator.

The profile fingerprint includes **every enabled plugin hash and its order**,
including `WeaponBalancePatch.esp`; do not omit the weapon patch to bypass
freshness. Finish root's final weapon generation/install and all mod/config
changes before producing the cloak staging receipt, all-layer proof and ZIP.
Source/config edits described here are not an installation or runtime pass.

```powershell
$cloakInstance = 'C:/Users/danjo/source/repos/mo2-instances/skyrim-se'
$cloakGameData = 'C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition/Data'
$cloakRecordCli = 'C:/Users/danjo/source/repos/skyrim-tools-builds/skyrim-record-cli-bb9aafb/skyrim-record-cli.exe'
$cloakDotnet = 'C:/Users/danjo/source/repos/.codex-tmp/dotnet10-sdk'
$cloakParserBin = 'C:/Users/danjo/source/repos/skyrim-tools-source/houseCARL/src/housecarl-generator/bin/Release/net9.0'
$cloakWork = 'records-work/cloak-slot-repair-2026-09-05/new-empty-rebuild'

# 1. Fresh record classification and conservative scope; no ZIP is emitted.
py -3 audit/cloak_exclusivity.py --instance $cloakInstance `
  --record-cli $cloakRecordCli --dotnet-root $cloakDotnet `
  --game-data $cloakGameData --output "$cloakWork/staged"
if ($LASTEXITCODE -ne 0) { throw 'Record staging failed' }

# 2. Use PowerShell 7 with a runtime able to load the .NET 9 parser.
pwsh -NoProfile -File audit/generate_nif_slot_layer_proof.ps1 `
  -Instance $cloakInstance -GameData $cloakGameData `
  -Receipt "$cloakWork/staged/receipt.json" -Output "$cloakWork/layer-proof.json" `
  -ToolBin $cloakParserBin
if ($LASTEXITCODE -ne 0) { throw 'Layer reservation proof failed' }

# 3. Rescan the profile and reject stale proof before creating the original patch.
py -3 audit/cloak_exclusivity.py --instance $cloakInstance `
  --record-cli $cloakRecordCli --dotnet-root $cloakDotnet `
  --game-data $cloakGameData --layer-audit "$cloakWork/layer-proof.json" `
  --output "$cloakWork/package"
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
```

Run from the repository root, adjusting the declared environment paths. Every
Python staging/package directory must be empty and outside MO2. These commands
do not launch the game or install the patch. The layer-proof script intentionally
pins the reviewed 302/576 model-scope counts; changes require a scope review.

The record CLI source is [Ensrick/skyrim-record-cli](https://github.com/Ensrick/skyrim-record-cli)
at `bb9aafb`; its existing build receipt is
`records/source-builds/skyrim-record-cli-graph-audit.json`. The mesh parser comes
from [Ensrick/houseCARL](https://github.com/Ensrick/houseCARL) at
`6386941e6ebaf84b5bf10decfa60c99af5847e44`, built with .NET SDK 9.0.311 using
`dotnet build src/housecarl-generator/housecarl-generator.csproj -c Release`
from that repository. The project pins NuGet `Nifly` 1.1.0. The proof records
the actual HousecarlCore and NiflySharp binary hashes; external tools and
vendor assets are not bundled in this patch.

Without `--layer-audit` the tool emits staging and a local inspection receipt,
**not an installable ZIP**. The independent layer proof must be fresh and bound
to the actual inspected inputs before packaging. The owned manifest binds the
reservation to the current runtime plugin hashes/order, enabled mods, winning
SkyPatcher configurations, native parser, and audited assets. Reinstalling or
updating equipment requires a reservation re-audit, not just reusing an old
PASS result. Preflight API: `check_installed(instance, game_data) -> list[str]`.
An empty list is a fresh static gate, never a gameplay pass.

The agent builds outside MO2. The root agent owns any live claim, install,
ledger/Keep reconciliation, issue update, and preflight integration.

## Runtime acceptance still owed

Start a fresh game process after installing the overlay. On a disposable test
save, equip a full Sons of Skyrim cloak, then a full Pelts cloak: the first
must unequip. Reverse the order. Repeat with CoS, a Campfire travel cloak and
each More Scarves hooded cape. Verify both genders and that no piece becomes
invisible. Verify a small Pelts mantle can still accompany the SoS cloth cloak
and that the tested fur collar/hood behavior is unchanged.

Repeat on a character/NPC that already had two cloaks equipped in the old save.
Saved worn flags may need a normal unequip/re-equip before the engine resolves
the new mask; this config does not proactively erase equipment or reset NPC
inventories. An NPC can carry several cloaks while only wearing one. Physics
requires its own asset repair and acceptance test and is not fixed by this INI.

## Provenance and redistribution

The generator, tests, diagnostic code and generated INI are original Ensrick
code/configuration under this repository's MIT license. The package references
existing forms and depends on the user's separately obtained vendor mods. It
contains no vendor ESP, NIF, DDS, or DLL. All vendor assets remain untouched.
The independently downloaded SkyPatcher checkout stays in ignored records-work;
none of its implementation is copied into the package.

Authoritative implementation inspected at
[SkyPatcher commit 876662e](https://github.com/Zzyxz/SkyPatcher/blob/876662e5c5b91326edf9797540c466399cb317db/armor.cpp):
the parser's `bipedSlotsToAdd` list and the application loop add a bit to ARMO
and attached ARMA; `utility.cpp` maps index 28 to the engine's corresponding
biped flag. The public [Armor Patcher documentation](https://www.nexusmods.com/skyrimspecialedition/articles/6088)
describes the same indexing and propagation. Source checkout and installed
vendor binary equivalence are not established merely by matching these tokens.
