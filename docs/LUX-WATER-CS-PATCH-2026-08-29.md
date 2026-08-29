# Lux and Water for ENB conflict resolution — 2026-08-29

## Decision

Use both the official Lux Patch Hub compatibility plugin and a generated,
ESL-flagged Ensrick conflict patch. The official patch contains only six
Dawnguard CELL/WRLD overrides and is valuable, but it does not cover the full
active conflict surface. The generated patch resolves the remaining record
chains without editing either vendor mod.

The active order is:

1. `Lux.esp` and its official compatibility patches
2. `Water for ENB (Shades of Skyrim).esp` and its official add-on patches
3. `Lux - Water for ENB (Shades of skyrim) patch.esp`
4. `Ensrick Lux Water CS Patch.esp`

The prior `Water for ENB - Generated Conflict Patch` mod remains installed but
disabled for rollback. It produced no useful active output and must not be
reenabled alongside the replacement.

## Conflict policy

For each Water-family CELL or WRLD record, the generator begins with the latest
active record outside the Water family. It then forwards only the fields owned
by the water overhaul:

- CELL: water FormID, environment map, water height, and the exact `HasWater`
  flag bit
- WRLD: water FormID, LOD water FormID, LOD water height, and environment map

All lighting, image-space, lighting-template, and unrelated compatibility data
therefore remain those of the latest non-Water winner. The implementation also
supports official Water add-on plugins which intentionally do not list the main
Water plugin as a master, then discovers downstream Water-family patches such
as the official Lux compatibility plugin.

The Dustman's Cairn record `02A03A:Skyrim.esm` was inspected as a representative
proof: the output retains Lux's lighting template and image space while carrying
Water for ENB's water height, environment map, and `HasWater` state.

## Installed artifacts

- Official patch: Nexus 113002 file 695703, installed transaction
  `20260829T062758120Z-4525c1761677`
- Official patch SHA-256:
  `2E16684D5F31E7ACCED94ACC7E3C10DF2824E68CF67F8E77D9D1575F5974E8D6`
- Source fork: <https://github.com/Ensrick/WaterForENBPatcherCS>
- Reviewed merge: <https://github.com/Ensrick/WaterForENBPatcherCS/pull/1>
- Source commit: `f7d459bdade1e6c04aeb8426f02e2191907c9d35`
- Generated plugin SHA-256:
  `5D65CFB115AACEDB516D3C0EB3503C94347A638FAF61C11DE81F9BAD0A5FDAA8`
- MO2 mod: `Ensrick - Lux Water CS Patch`, priority 117
- Plugin: `Ensrick Lux Water CS Patch.esp`, active plugin priority 101

No file inside Lux, Water for ENB, or Lux Patch Hub was modified. Their active
plugin hashes remained identical after the installation.

## Validation

- clean source build with warnings treated as errors: 0 warnings, 0 errors
- built-in water-field merge self-test: pass
- NuGet direct and transitive vulnerability audit: no known vulnerabilities
- two headless generations from the same load order: byte-identical
- strict Spriggit serialize/check/deserialize round trip: pass
- record parser: 559 overrides, 551 CELL and 8 WRLD, no new records
- master audit: pass
- MO2 audit: no errors
- active conflict inventory: all 559 output records win their chains; 175 of
  those chains include `Lux.esp`
- Skyrim was not launched during installation or validation

Gameplay acceptance remains required. The first foreground test should inspect
interior water boundaries, waterfall transitions, underwater entry/exit,
reflections, and Lux lighting in water-bearing cells. Any defect should be
reported against the exact plugin hash above.

## Nexus curation and distribution

Water for ENB, Lux, and Lux Patch Hub are all recorded as **Keep**. Their authors
(`mindflux` and `GGUNIT`) were removed from the curator's Excluded set as part
of that same operation.

The patcher source is public under GPL-3.0-only. The generated ESP remains a
local-only runtime artifact until its redistribution status is reviewed
separately. A public installer may regenerate it on the user's machine from
authorized downloads; it must not silently bundle vendor files or this generated
ESP before that review is complete.

The complete machine-readable record is
`records/source-builds/ensrick-lux-water-cs-patch.json`.
