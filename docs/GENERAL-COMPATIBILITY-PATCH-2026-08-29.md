# General compatibility patch — Decision A implementation

## Outcome

Decision A from issue 47 is implemented as one reproducible, ESL-flagged,
override-only plugin. The local binary contains exactly 12 WRLD and 2 CELL
overrides, creates no forms, and has no scripts, quests, aliases, persistent
references, or NAVM records.

The plugin is **not installed**. The live `Default` profile and every vendor mod
remain unchanged, Skyrim was not launched, and gameplay acceptance is pending.

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

## Reproducibility and output

| Artifact | SHA-256 | Size |
|---|---|---:|
| Generated ESP | `1C034213707F5EB9B10B51CC9DA0E70CBDA8E80D00463AD2635B7A216F657E8E` | 7,593 bytes |
| Spriggit text tree | `179AB60E1A9CD74B2CC3391A0A0BB17C0AC493D8755DCA695A8F458C87EB51F3` | 20 files |
| Deterministic local archive | `40272AC543781C070D30AB1A672CA3B9330BF64C2800D312064624FA175540CC` | 2,848 bytes |

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
- masters: six present and ordered inputs, zero missing/late
- tracked LOOT rule: patch ordered after Lux Orbis CS, PROTEUS, Skyrim Unbound,
  Water for ENB's Bruma/Lux inputs, and the existing generated Water patch
- deterministic one-entry archive: embedded plugin bytes and fixed timestamp
  verified

## Promotion gate

Promotion requires a separate user-approved change to the active MO2 profile,
followed by foreground testing of Water for ENB transitions, Lux Orbis CS
worldspace behavior, and Bruma climate/location behavior. Regeneration and all
headless audits must run again if any target source or later winner changes.
