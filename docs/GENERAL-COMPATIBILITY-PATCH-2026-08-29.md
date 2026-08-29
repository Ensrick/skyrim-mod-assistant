# General compatibility patch — Decision A implementation

## Outcome

Decision A from issue 47 is implemented as one reproducible, ESL-flagged,
override-only plugin. The local binary contains exactly 12 WRLD and 2 CELL
overrides, creates no forms, and has no scripts, quests, aliases, persistent
references, or NAVM records.

The plugin is **not installed**. The live `Default` profile and every vendor mod
remain unchanged, Skyrim was not launched, and gameplay acceptance is pending.
It is a standalone supplement to the existing 559-record
`Ensrick Lux Water CS Patch.esp`, which remains separate and enabled in the
reviewed inputs; the new patch neither replaces nor disables it.

## Record policy

- Eight WRLD records begin with their final sorted-profile winners and receive
  only their approved Lux Orbis CS non-water fields.
- The same records retain final-winner Water for ENB water fields.
- Two CELL records assert the Lux Orbis CS `Location` value.
- Four Bruma WRLD records restore only the approved `Climate`, `Location`, and
  `ObjectBoundsMax` fields.

The generator treats the decision JSON as a closed allowlist, validates all
EditorIDs, clears record compression, requires exactly fourteen overrides, and
fails if any output FormKey belongs to the patch itself.

`Lux Orbis CS.esp` is an explicit hard master. Its approved contributions are
scalar or vanilla-linked data and therefore would otherwise be removed by
automatic FormLink-only master inference. The complete reviewed master order is
Skyrim, Dragonborn, BSAssets, BSHeartland, Lux Orbis CS, Water for ENB, and the
Water for ENB Bruma patch.

Three approved records are intentional ITMs under the current order:
`Sovngarde` (`MaxHeight`), `WhiterunPlainsDistrict04` (`Location`), and
`SolitudeOrigin` (`Location`). They are explicit future-order assertions and
must not be stripped by a cleaning pass.

## Reproducibility and output

| Artifact | SHA-256 | Size |
|---|---|---:|
| Generated ESP | `ADAED3D2704F98E491773284F3BEE0C480FA72088F5D519D4566EC784B906334` | 7,630 bytes |
| Spriggit text tree | `D71650F7DA239C89C797F068A50AF7B6BAFB502823C3DAC6BB44EDE0CF183DA0` | 20 files |
| Expected profile/target values | `73B8C750AA78E044F0242235E9E7901F6036298CE07A2E2327E29309AF794E08` | 14 targets |
| Deterministic local archive | `3A633723CFE528BB7A8647334920CEA965C2BA232E661342A6684B1817246163` | 2,854 bytes |

Two independent generation runs against the 174-entry effective sorted load
order produced the same ESP hash. Spriggit 0.41.0 passed strict checked
serialize/deserialize/serialize validation with identical text-tree digests.
The binary ESP and archive remain ignored local artifacts.

## Headless validation

- .NET 10.0.302 locked Release build: zero warnings, zero errors
- direct and transitive NuGet vulnerability audit: zero known vulnerabilities
- patcher target/field allowlist self-test: pass
- independent record structure: 12 WRLD, 2 CELL, no other types
- independent field comparison: 374 selected fields match either the approved
  source or final active winner
- explicit water retention: all 48 selected water fields match the final winner
- full active-load-order link audit: 62 links checked, zero unresolved
- masters: exact seven-master set present and ordered, including hard master
  `Lux Orbis CS.esp`; zero missing/late
- frozen inputs: 99 active plugins, three profile hashes, five participating
  plugin hashes, 14 source/winner value sets, and three intentional ITMs match
  `expected-values.json`
- tracked LOOT rule: patch ordered after Lux Orbis CS, PROTEUS, Skyrim Unbound,
  Water for ENB's Bruma/Lux inputs, and the existing generated Water patch
- deterministic one-entry archive: embedded plugin bytes and fixed timestamp
  verified

## Promotion gate

Promotion requires a separate user-approved change to the active MO2 profile,
followed by foreground testing of Water for ENB transitions, Lux Orbis CS
worldspace behavior, and Bruma climate/location behavior. Regeneration and all
headless audits must run again if any target source or later winner changes.
