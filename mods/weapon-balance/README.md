# Ensrick Weapon Speed Balance

Status: 0.2.0 source candidate; final generation waits for the reviewed private
Lost Longswords curation layer.

This is a generated, ESL-flagged Skyrim SE/AE patch that normalizes the speed
of conventional melee weapon classes without editing any source mod in place.
It copies the current load-order winner for each affected weapon and changes
only `WEAP.DNAM.Speed` (Mutagen's `Weapon.Data.Speed`). Regenerate after adding,
updating, removing, or reordering a weapon or broad balance mod.

## Balance profile

| Class | Speed | Dragonbone reference damage | Record-level damage x speed |
|---|---:|---:|---:|
| Dagger | 1.25 | 12 | 15 |
| Sword | 1.00 | 15 | 15 |
| Lost Longsword (explicit custom class) | 1.00 | 20 (hypothetical anchor) | 20 |
| War axe | 0.9375 | 16 | 15 |
| Mace | 0.88235295 | 17 | 15 |
| Greatsword | 0.80 | 25 | 20 |
| Battleaxe | 0.7692308 | 26 | 20 |
| Warhammer | 0.71428573 | 28 | 20 |

The figure in the final column is a record-level balancing index, not a claim
about exact animation DPS. Weapon reach, stagger, power-attack timing, perks,
enchantments, dual wielding, and animation event windows remain distinct.

## Scope and safety

- Generic selection requires exactly one of Bethesda's seven standard
  weapon-type keywords and a coherent animation type.
- Includes NPC-only conventional weapons so the rule applies consistently in
  combat, but excludes records flagged `NotUsedInNormalCombat` and declared
  utility EditorID fragments. Unkeyworded records are default-denied.
- Does not infer a class from animation alone. This prevents the former eight
  fallback leaks (spears, invisible attacks, a test sword, and utility tools).
- Treats `01E719:Skyrim.esm` correctly as `WeapMaterialSteel`; it is neither a
  creature keyword nor a weapon-type keyword.
- Skips records with multiple standard class keywords and reports them.
- Preserves the winning speeds of both Ebony Blade records and The Longhammer.
- Gives nine exact Lost Longswords FormKeys the explicit `Longsword` speed-1
  class, and fails closed unless their reviewed private curation plugin is the
  winning provider with the approved damage. Each must also retain the
  Greatsword type keyword, two-handed skill, two-hand sword animation, and
  `BothHands` equip type. The three rejected forms are exact exclusions from
  generic normalization.
- Creates no scripts, quests, abilities, magic effects, or new records.
- Contains no armor-matchup damage bonuses, passive-health changes, projectile
  changes, or locational-damage implementation.
- Carries only speed-changed winning WEAP overrides. Runtime/save acceptance is
  still required; the source does not make a blanket mid-save safety promise.

## Build and validation

```powershell
dotnet run --project tests/WeaponBalancePatcher.Tests/WeaponBalancePatcher.Tests.csproj -c Release
./generate.ps1 -ExecutionMode Offline -DataFolder <staged-data> -LoadOrderFile <enabled-only-list>
./audit.ps1 -FreshnessOnly -Instance <instance> -Profile Default -ArtifactRoot ./artifacts
./package.ps1
```

Offline generation is the safe default. Its starred enabled-only list may omit
the five base masters; the wrapper prepends and deduplicates them. Final profile
generation requires `-ExecutionMode MO2Vfs`, `-AllowLiveProfileAccess`, and a
matching `-ClaimOwner` whose live claim covers the ten-minute child timeout plus
margin. The generated plugin, selection
report, manifest, audit receipts, and archive are intentionally ignored by Git.
Generation excludes its own output from the input order, verifies the physical
winning provider and SHA-256 of every input plugin, performs a second
deterministic build, and runs a semantic only-Speed audit. `audit.ps1
-FreshnessOnly` performs no VFS launch and writes no files; it detects input
name/order, input bytes/provider, source-policy, output hash, output file winner,
plugin-priority, and final-winner-receipt drift.
Release packaging reruns that read-only freshness gate and places the report,
manifest, and final-winner receipt under `EnsrickMetadata/` beside the root
plugin. `package.ps1 -AllowPendingFinalAudit` is only for an explicitly marked
non-release candidate and omits the not-yet-existing final receipt.
The local .NET SDK is pinned by `global.json`; NuGet dependencies and hashes
are pinned by `packages.lock.json`.

## Prior art and code-weight ruling

The CK-native operation is an override of `WEAP.DNAM.Speed`. A hand-authored
plugin is not practical here because the rule selects the current winner of
thousands of records across a changing load order; this is the rule-over-many
case in `docs/CK_FIRST_DOCTRINE.md` rule 4. The current standalone project is
still consolidation debt under rule 6 and should eventually become a policy in
the shared record-patch generator.

The 2026-09-04 prior-art pass found one exact architectural alternative that
the earlier 27-result search missed: [Weapon Stat Synthesis Patcher](https://www.nexusmods.com/skyrimspecialedition/mods/149027)
is also a configurable Synthesis patcher that normalizes melee weapon stats
across an entire load order, and version 1.2 can disable all non-speed edits.
It also preserves named-weapon offsets and has broader weapon-family support.
Replacing this patcher with that released implementation is therefore a user
choice, not an engineering fact. The installed 0.1.0 artifact remains a
historically receipted build; the current 0.2.0 source intentionally supersedes
that generator and does not claim to reproduce the retired binary.

Adjacent alternatives are not exact replacements. [Customize Weapon Speed](https://www.nexusmods.com/skyrimspecialedition/mods/22100)
mutates base forms at runtime using Papyrus/SKSE and name matching, while
[Weapon Speed - IPM](https://www.nexusmods.com/skyrimspecialedition/mods/96828)
adds IPM/MCM runtime dependencies. The three “weapon speed fix” releases found
in the original search address the `WeaponSpeedMult` actor-value stacking bug,
not `WEAP.DNAM.Speed` normalization.

## Configuration

Defaults live in `src/WeaponBalancePatcher/settings.json`.
`IncludeNonPlayableWeapons` defaults to true so NPC-only conventional weapons
remain balanced; set it false to restrict the output to player-playable records.
The conservative `ExcludeEditorIdContains` defaults (`Dummy` and `GiantClub`)
can be adjusted for unusual mods. Reviewed exceptions use exact `RecordRules`.
Supported actions are `Preserve`, `Exclude`, `Class`, and direct `Speed`; every
rule requires a reason. A custom-class rule can also pin its required input
winner and damage:

```json
{
  "FormId": "000ABC:SomeMod.esp",
  "Action": "Class",
  "Class": "Longsword",
  "ExpectedWinningProvider": "Reviewed Curation Patch.esp",
  "ExpectedDamage": 20,
  "Reason": "Approved custom category."
}
```

Valid classes are Dagger, Sword, Longsword, WarAxe, Mace, Greatsword,
Battleaxe, and Warhammer. Generically normalized records with a non-canonical
source speed or `MagicDisallowEnchanting` are listed as review candidates; they
are not silently promoted to exceptions.

## License

The generator source, configuration, and scripts are covered by the
repository's MIT license. A generated patch copies winning record data from its
inputs; being override-only does not itself grant redistribution rights to that
third-party data. Generated binaries are therefore **local-only by default**
until their concrete records and every source permission are reviewed. Users
must install every required master. This is separate from the private Lost
Longswords asset/conversion layer, which is not distributable.
