# Ensrick Weapon Speed Balance

Status: 0.1.0 test build.

This is a generated, ESL-flagged Skyrim SE/AE patch that normalizes the speed
of conventional melee weapon classes without editing any source mod. It copies
the current load-order winner for each affected weapon and changes only
`WEAP.DATA.Speed`. Regenerate after adding weapon or broad balance mods.

## Balance profile

| Class | Speed | Dragonbone reference damage | Record-level damage x speed |
|---|---:|---:|---:|
| Dagger | 1.25 | 12 | 15 |
| Sword | 1.00 | 15 | 15 |
| War axe | 0.9375 | 16 | 15 |
| Mace | 0.88235295 | 17 | 15 |
| Greatsword | 0.80 | 25 | 20 |
| Battleaxe | 0.7692308 | 26 | 20 |
| Warhammer | 0.71428573 | 28 | 20 |

The figure in the final column is a record-level balancing index, not a claim
about exact animation DPS. Weapon reach, stagger, power-attack timing, perks,
enchantments, dual wielding, and animation event windows remain distinct.

## Scope and safety

- Classifies by Bethesda's seven standard weapon-type keywords.
- Includes NPC-only conventional weapons so the rule applies consistently in
  combat, but excludes creature-only and utility/test records by default. This
  prevents misleading ordinary keywords on giant clubs or civil-war display
  dummies from changing unrelated behavior.
- Uses animation-type fallback only when unambiguous.
- Skips unkeyworded `TwoHandAxe` records because battleaxes and warhammers
  share that animation type but intentionally receive different speeds.
- Skips records with multiple standard class keywords and reports them.
- Creates no scripts, quests, abilities, magic effects, or new records.
- Contains no armor-matchup damage bonuses, passive-health changes, projectile
  changes, or locational-damage implementation.
- Carries only winning WEAP overrides and is safe to replace between saves.

## Build and validation

```powershell
dotnet run --project tests/WeaponBalancePatcher.Tests/WeaponBalancePatcher.Tests.csproj -c Release
./generate.ps1
./audit.ps1
./package.ps1
```

`generate.ps1` launches the source-built patcher through MO2's headless VFS,
so it reads the actual active profile rather than only the physical game Data
folder. The generated plugin and archive are intentionally ignored by Git.

## Configuration

Defaults live in `src/WeaponBalancePatcher/settings.json`.
`IncludeNonPlayableWeapons` defaults to true so NPC-only conventional weapons
remain balanced; set it false to restrict the output to player-playable records.
The conservative `ExcludeEditorIdContains` defaults (`Dummy` and `GiantClub`)
can be adjusted for unusual mods. `Exclude` accepts FormKeys such as
`000ABC:SomeMod.esp`. `ForceClass` accepts objects shaped as:

```json
{ "FormId": "000ABC:SomeMod.esp", "Class": "Warhammer" }
```

Valid classes are Dagger, Sword, WarAxe, Mace, Greatsword, Battleaxe, and
Warhammer.

## License

The generator source and scripts are covered by the repository's MIT license.
The generated patch contains no third-party meshes, textures, scripts, audio,
or other assets; users must install every master it references.
