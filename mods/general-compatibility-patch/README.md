# Ensrick General Compatibility Patch

Status: Decision A generated and headlessly audited on 2026-08-29; not
installed or promoted into the active MO2 profile.

This owned, ESL-flagged ESP resolves the proven stale override families from
the 2026-08-29 compatibility sweep. It contains exactly fourteen overrides:
twelve worldspaces and two exterior cells. It creates no forms and contains no
scripts, quests, aliases, persistent references, or NAVM records.

## Field policy

Every target begins with its final winner in the disposable LOOT-sorted load
order. The generator then changes only the fields approved in Decision A:

- eight WRLD records receive the specified Lux Orbis CS `Flags`, `MaxHeight`,
  and/or `Parent` fields;
- two CELL records receive Lux Orbis CS `Location`;
- `BSHeartland` receives Bruma `Climate`, `Location`, and `ObjectBoundsMax`;
- three additional Bruma WRLD records receive Bruma `Climate`; and
- all Water for ENB `Water`, `LodWater`, `LodWaterHeight`, and
  `WaterEnvironmentMap` fields remain those of the final active winner.

The complete target allowlist lives in
`records/synthesis/compatibility-sweep-2026-08-29/decisions.json`. The patcher
fails if any target or EditorID is missing, if the output is not exactly twelve
WRLD plus two CELL overrides, if the current 99-plugin profile differs from the
pinned `expected-values.json`, if the exact seven-master set differs, or if a
new FormKey is allocated. `Lux Orbis CS.esp` is deliberately retained as a
hard master even though its contributed scalar and vanilla-linked fields do not
naturally create a FormLink dependency.

Three records are intentional ITMs in the reviewed sorted order:

- `Sovngarde` asserts Lux Orbis CS `MaxHeight`;
- `WhiterunPlainsDistrict04` asserts Lux Orbis CS `Location`; and
- `SolitudeOrigin` asserts Lux Orbis CS `Location`.

They are future-order guards required by Decision A. Cleaning tools must not
remove them merely because Lux Orbis CS currently wins those chains.

## Reproduction

`regenerate.ps1` performs the complete hidden workflow against an explicitly
selected disposable MO2 profile:

1. verifies the pinned MO2, Spriggit, and record-inspector hashes;
2. builds the locked .NET generator with warnings treated as errors;
3. generates the plugin twice and requires byte-identical output;
4. performs a full-load-order link audit;
5. serializes, checks, deserializes, and reserializes with Spriggit 0.41.0;
6. compares all 374 selected WRLD/CELL fields to their approved source or final
   winner, including 48 explicit water-field comparisons; and
7. verifies the exact 99-plugin profile hashes, input plugin hashes, target
   values, seven hard masters, and three intentional ITMs; and
8. creates and verifies a deterministic one-file MO2 archive.

Example:

```powershell
pwsh ./mods/general-compatibility-patch/regenerate.ps1 `
  -ToolchainManifest C:/private/path/toolchain.json `
  -InstanceRoot C:/private/path/mo2-instance `
  -DataFolder C:/private/path/Skyrim/Data
```

The ignored `package` and `work` folders contain local binaries and logs. The
committed `spriggit` tree is the reviewable text representation; the repository
does not contain the generated ESP or any vendor archive.

## Load order and acceptance

The eventual plugin must load after its seven binary masters and after the
non-master semantic inputs listed in `config/loot/userlist.yaml`. Promotion is
deliberately separate from generation:
the live `Default` profile was not changed, Skyrim was not launched, and visual
acceptance for water, Lux Orbis CS behavior, and Bruma remains pending.

Vendor mods are never edited. Updating Lux Orbis CS, Water for ENB, Bruma, or
any later target winner requires deterministic regeneration and the full audit.
This standalone 14-record plugin supplements rather than replaces the existing
559-record `Ensrick Lux Water CS Patch.esp`; that patch remains separate and the
tracked LOOT rule places this plugin after it.
