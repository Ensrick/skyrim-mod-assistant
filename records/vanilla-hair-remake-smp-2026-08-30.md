# Vanilla Hair Remake SMP adoption — 2026-08-30

Profile: MO2 `Default`

Runtime: Skyrim SE 1.7.104 / SKSE 2.3.1 / Address Library v12 / FSMP 4.1.1 AVX

Author: jg1 (Nexus user 6520144)

Decision: install the vanilla-replacer SMP path for player and vanilla NPCs

## Outcome

[Vanilla Hair Remake](https://www.nexusmods.com/skyrimspecialedition/mods/63979)
is installed and enabled as a vanilla-plus hair baseline. The current 1.0.3
SMP main replaces the original 146 playable-race hairstyles without adding an
ESP or Apachii/KS-style hairs. The official optional 1.0.1 SMP NPC package
adds prebuilt physics FaceGen for vanilla, DLC, Fishing, and Saints & Seducers
NPCs through an ESL-flagged archive-loader ESP.

The equippable-wigs optional file was not installed. The no-physics main and
NPC files were not installed. Nothing was copied into physical game `Data`, no
game or Creation Kit launch occurred, and no vendor plugin or asset was edited.

One private, deterministic loose-file compatibility layer sits above both
pristine vendor packages:

- 29 exact USSEP FaceGen NIFs win over VHR where both archives ship the same
  path. Some of these accompany deliberate USSEP sex, race, head-part, morph,
  hair-color, or weight corrections. Following jg1's documented rule that
  head-changing mods win rather than combine, those 29 NPCs keep their fixed
  faces and intentionally forgo SMP hair.
- three Dawnguard Snow Elf VHR meshes had retained an obsolete
  `darkelf01.xml` string. Loose copies change only that NIF string-table entry
  to the installed current `darkelf01m.xml`.
- Cutting Room Floor loads after VHR and its archive remains the winner for
  two additional FaceGen paths. Those two NPCs likewise keep CRF's faces and
  forgo SMP hair.

The effective result is 2,405 VHR SMP NPC FaceGen winners, 29 preserved USSEP
winners, and 2 preserved CRF winners, plus the SMP player replacer.

## Exact inputs and transactions

The current official Nexus v1 metadata was queried by exact mod/file ID on
2026-08-30. Mod-page version 1.0.3 is still current.

| MO2 mod | Nexus/file | Version | Archive bytes | SHA-256 | Transaction |
|---|---:|---:|---:|---|---|
| Vanilla Hair Remake SMP | 63979/510409 | 1.0.3 | 8,561,414 | `BAEC986DE9AAA7F35FF2DBC372844E8B9C4A609C929D1115F293FCACEE14372E` | `20260830T215810031Z-2115c73434fc` |
| Vanilla Hair Remake SMP - NPCs | 63979/500742 | 1.0.1 | 71,734,666 | `F708E4116C7183AD71545A19115C1EAF4C049D9EDEA3AB1F43F8DB34722743BB` | `20260830T215800258Z-6a006384c373` |
| Ensrick - VHR SMP NPC Compatibility | local build | 2026-08-30 | 7,846,248 installed payload | aggregate `0504FF16F3239BD116867D37E5511B8B453B8E1EF96F11D6FE506FA00FCDA2DE` | `20260830T220546414Z-660cdd66dc7b` |

The two vendor installed trees match their independent extractions exactly:
568/568 files for the main and 95/95 files for the NPC package, with no
missing, extra, or hash-mismatched payload beyond MO2's `meta.ini`.

## Archive and format audit

### SMP main 1.0.3

- 568 files / 59,475,244 extracted bytes;
- 271 NIF, 204 TRI, and 93 XML; no plugin, BSA, DLL, script, or texture;
- all 271 NIFs load as valid SSE stream 100 / user version 12 with no unknown
  blocks;
- all 204 TRI files have valid `FRTRI` headers;
- all 93 XML files are well-formed and validate against the installed FSMP
  4.1.1 `hdtSMP64.xsd`;
- the main's 93 XML files are byte-identical to the older NPC package copies,
  but the current main is deliberately the higher MO2 winner.

### SMP NPC package 1.0.1

- archive-loader plugin: 128 bytes, TES4 header only, 0 records, ESL flag
  `0x200`, masters `Skyrim.esm` and `Update.esm`;
- BSA: 2,436/2,436 entries are valid SSE stream-100 FaceGen NIFs, decoded
  payload 1,228,170,632 bytes, with a physics marker in every mesh;
- namespace coverage: Skyrim 1,917; Dragonborn 314; Dawnguard 161;
  Saints & Seducers 30; Fishing 8; HearthFires 6;
- 2,433 meshes reference an installed XML directly. The other three are the
  repaired Snow Elf paths described below.

The plugin is active at load position 40 of 199. LOOT places USSEP first, VHR
at 40, and CRF at 41, which produces the intended archive order. The plugin
contains no NPC records and therefore creates no record-forwarding burden.

## Requirements and runtime boundary

The installed `SkyrimSE.exe` is 1.7.104.0, `skse64_loader.exe` is 2.3.1, and
`hdtSMP64.dll` is the AVX build, version 4.1.1.0. The VHR page requires FSMP
1.50.1 or later and does not require XPMSSE (XPMSSE is installed anyway).

FSMP's active `configs.json` already has:

- `disableSMPHairWhenWigEquipped: true`, the VHR author's recommendation for
  avoiding severe helmet clipping;
- `autoAdjustMaxSkeletons: true`, `maximumActiveSkeletons: 5`, and
  `budgetMs: 3.0`, bounding crowded-scene hair cost;
- no body physics policy change: FSMP is used for cloth and hair, not jiggle.

The older [SMP-NPC Crash Fix](https://www.nexusmods.com/skyrimspecialedition/mods/91616)
was audited but not installed. Its sole file 389370 says it is for Skyrim
1.6.x and the DLL has no 1.7.104 build. More importantly, the maintained
[FSMP changelog](https://github.com/DaymareOn/hdtSMP64/wiki/10-%E2%80%90-Changelog)
documents the 3.0 head-corruption/FaceGen crash correction, and the FSMP
maintainer has confirmed the separate fix is obsolete on 3.0+. Installing both
is therefore unnecessary and potentially conflicting. The audited but unused
archive SHA-256 is
`887C1E48E5AF241C5B7479E1A6C3CFFF14B985588A00058696214F5ADF3E4654`.

No High Poly Head, Expressive Facegen Morphs, High Poly Vanilla Hair, Vanilla
Hair Replacer, or other player-hair replacer is enabled. CBBE, HIMBO, TNG,
SkySight, and Reverie change bodies/skin rather than these hair or FaceGen
paths. Interesting NPCs and custom followers use their own plugin namespaces.

## Compatibility overlay

Tracked recipe:
`overlays/ensrick-vanilla-hair-remake-smp-npc-compatibility/build.py`.
Generated NIFs remain local and are not committed or redistributed.

For the 29 VHR/USSEP archive overlaps, the builder copies the exact USSEP NIF
bytes into loose paths. The overlap is not theoretical: 19 of those NPCs have
USSEP NPC-record overrides with changed head-affecting fields; one example is
Dragonborn `01E858`, where USSEP corrects a female Dunmer while the old VHR
NPC package contains a male Dunmer FaceGen mesh. Preserving all 29 exact USSEP
files is the conservative, author-documented winner policy.

The remaining three output NIFs are VHR copies for Dawnguard FormIDs `002B44`,
`003788`, and `00A8B0`. Each output is exactly one byte longer because the
string table changes `darkelf01.xml` to `darkelf01m.xml`; block types, shapes,
textures, and geometry remain otherwise untouched. Their output SHA-256 values
are respectively:

- `1C4C34028BD79CB6177594D17858A4A69A84A2C7987A8761869233FC98F1A384`;
- `F9400D5757300FE69198D410A96A6171190E5AA40EF936FC63143A701F5DA110`;
- `BEB06FB4CF895541AA8393EC42B0C6B542E7687E8FED944B986A7F30A02A9C8F`.

All 32 outputs load as valid SSE stream-100 NIFs with no unknown blocks. Two
clean builds and the installed MO2 tree produce the same 32-file, 7,846,248
byte aggregate SHA-256 shown above. jg1 permits releasing fixes/modifications
with credit; USSEP bytes and derived VHR meshes remain private here.

## Verification

- the compatibility overlay, current main, and NPC package are the top three
  enabled managed rows in descending winner order; all are enabled;
- main is the effective loose winner for 93 shared XMLs;
- BSA-aware conflict inventory: only the 29 USSEP and 2 CRF FaceGen archive
  overlaps exist in the enabled stack; no BSA read failures;
- ledger verification: 190 rows, 281 plugins discovered, 0 problems;
- master/order verification: 199 active plugins, `CLEAN`;
- MO2Headless `audit --profile Default`: `errors: []`;
- physical `Data`: 236 files / 20,732,350,348 bytes before and after; exact
  sorted path/size/mtime-ns manifest SHA-256
  `B338DE836A6C7DB19FAE733B5E2E83AFE6FB7471D7014F4755C1B0DDCB371591`;
- no game, CK, visible UI, or popup was launched.

## Remaining foreground smoke and rollback

Issue #27 remains open only for the explicitly prohibited foreground checks:

1. inspect representative player styles for all playable races, including
   Argonian and Khajiit;
2. equip helmets/hoods over long styles and verify hair physics disables with
   no severe clipping;
3. visit crowded vanilla interiors/exteriors and inspect frame time plus
   `hdtSMP64.log` under the 3 ms / five-NPC budget;
4. inspect the 29 USSEP and 2 CRF preserved faces for color/geometry mismatch;
5. inspect the three repaired Dawnguard Snow Elves for live physics; and
6. switch Proteus characters with SMP hair, save/reload, and confirm no stale
   hair skeleton or crash.

Rollback is MO2-local and recoverable: disable the compatibility overlay, NPC
package, and main in that order, then disable the archive-loader plugin. This
returns immediately to USSEP/CRF/vanilla FaceGen and vanilla player hair.
Do not delete the vendor downloads or copy any payload to physical `Data`.
