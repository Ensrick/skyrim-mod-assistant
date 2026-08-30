# Varinia private dialogue-fragment correction

Completed: `2026-08-30`

## Result

Varinia 1.1.0's six missing compiled dialogue fragments are a packaging / CK
source-generation defect, not intentionally disabled content. A separate local
MO2 overlay now supplies only those six PEX files. The official Varinia plugin
and both BSAs remain byte-identical. The correction is private and must not be
published or bundled without the author's permission.

The separately requested 3DNPC comparison found no material value loss and no
need for a Varinia--Interesting NPCs compatibility plugin. No ESP or ESL was
created.

## Vendor provenance and immutability

- Current official input: Varinia 1.1.0, Nexus file `697835`, archive SHA-256
  `4FDB7EBEFBA131ED392F2B2C17A9E0CC26AF848E6392B96B2A4EE8D3981C1DFF`.
- Historical control: official Varinia 1.0.2, Nexus file `696575`, locally
  retained archive SHA-256
  `10A71A62C71A542E651D6FAEB3E117B98EF1E93F1661678877E437E3F2DAF197`.
- Installed `VLIOVarinia.esp` SHA-256:
  `91E6F027E7B708FCC8EFAB83417F2B951B7215045C12830D00A615C0C715CDE2`.
- Installed `VLIOVarinia.bsa` SHA-256:
  `BA4F2294D1AA144F2D97B901C5D0BAFC3144401AD29AD9A8A267DA0E21017BAA`.
- Installed `VLIOVarinia - Textures.bsa` SHA-256:
  `5A54385CE02EA2200573806A2B5DA3040A97A2C3DB329AD7A934614033281DE4`.

Those three installed vendor hashes are unchanged from the pre-correction
audit. The vendor directory was not edited.

## Why this is a packaging defect

The 1.1.0 BSA contains 317 PEX and 324 PSC files. These six scripts have PSC
source and are attached to live `INFO` records through complete plugin VMAD
data, but their PEX files are absent:

| Script | Attached dialogue action |
|---|---|
| `VLIO_TIF__050F8A8A` | Dismiss Moe, clear `VLIOCrowIsHere`; voiced response has Moe ruffle her feathers and leave. |
| `VLIO_TIF__050F8A8C` | Dismiss Hedy and clear `VLIOCrowIsHere`. |
| `VLIO_TIF__050F8A8E` | Dismiss Mata and clear `VLIOCrowIsHere`. |
| `VLIO_TIF__050FDB94` | Remove Varinia's Arcane Mist / concentration spell. |
| `VLIO_TIF__050FDB98` | Remove Varinia's Arcane Bolt / aimed spell. |
| `VLIO_TIF__050FDB9C` | Remove Fast Healing from Varinia. |

The spell targets are Varinia, not the player. The crow fragments dismiss the
named crow actor, move its alias reference to `VoidReturn`, and clear the
shared crow-present global.

Each missing fragment is the alternating response variant beside an intact,
compiled sibling: `8A89/8A8A`, `8A8B/8A8C`, `8A8D/8A8E`, `DB93/DB94`,
`DB97/DB98`, and `DB9B/DB9C`. The missing PSC bodies are complete but uniquely
lack the property-declaration block needed to compile them. The plugin VMAD
still contains the exact property names, types, and bound forms. The official
1.0.2 archive has the same six absent PEX files and the same property-less PSC
sources. The 1.1.0 changelog, description, posts, and formal bug-report list do
not identify an intentional removal; the public description instead advertises
the crows and their dialogue. Taken together, the alternating sibling pattern,
live VMAD attachment, voiced responses, and historical recurrence are strong
evidence of a packaging / generated-source omission.

`VLIO_TIF__051B4278` remains untouched: unlike these six, it is unreferenced
source debris and has no plugin VMAD attachment.

## Reproducible source correction

Starting from the six PSC files extracted from the verified 1.1.0 BSA, only
the following `Auto` property declarations were restored from the plugin VMAD:

| Script | Restored properties |
|---|---|
| `050F8A8A` | `ReferenceAlias VLIOMoeAlias`; `Actor VLIOMoe`; `ObjectReference VoidReturn`; `GlobalVariable VLIOCrowIsHere` |
| `050F8A8C` | `ObjectReference VoidReturn`; `Actor VLIOHedy`; `ReferenceAlias VLIOHedyAlias`; `GlobalVariable VLIOCrowIsHere` |
| `050F8A8E` | `Actor VLIOMata`; `GlobalVariable VLIOCrowIsHere`; `ReferenceAlias VLIOMataAlias`; `ObjectReference VoidReturn` |
| `050FDB94` | `Actor VLIOVarinia`; `Spell VLIOConcentrationMag` |
| `050FDB98` | `Spell VLIOAimedMag`; `Actor VLIOVarinia` |
| `050FDB9C` | `Spell FastHealing`; `Actor VLIOVarinia` |

No function body, fragment order, identifier, or plugin record was changed.
The corrected private PSC hashes are:

| Source | SHA-256 |
|---|---|
| `vlio_tif__050f8a8a.psc` | `35A95563A69D60F535A9ED0810075D342C438F7432BE46BDA1F298035FCB0BB2` |
| `vlio_tif__050f8a8c.psc` | `2BE17B20AF30F471B1192B6C1763DCB2BAB1591E4AD6D260D0B8B592A7A079CB` |
| `vlio_tif__050f8a8e.psc` | `B02448877CB194AFFE146D5AA3A22BB6E0DF54591282D3618348118A200861C7` |
| `vlio_tif__050fdb94.psc` | `D77F37FCFA12656BC2CFD38516926EBC0D930495E9E8B497756062851F27D802` |
| `vlio_tif__050fdb98.psc` | `0789A71BE2AFC74C55A36320E79BF4CAE7F48FA3948C30325868CCE12E9CD0DF` |
| `vlio_tif__050fdb9c.psc` | `13C87A362FA35CE805CCFEC0B816ADB2019625115526AF4B9597A201F19D29BF` |

These derivative PSC files are not committed to the public repository. The
verified vendor archive plus the declaration table above is the reproducible
input recipe.

## Pinned source-built toolchain and command

- Caprica v0.3.0 source commit
  `2042C902EC269E33C1061CCD8AAC0760C981253B`; executable SHA-256
  `D28CDDD7E476709C0DAA473AD558E783C00CA8E1B0DE407DDBA839C55E9A3630`.
- Champollion v1.3.2 source commit
  `108BB84FB960884639560C04CD67143BA0A9608F`; executable SHA-256
  `4DA9CB6E31EA16834D76791635A7F08ED025A39EC9835635772D9FF8992EA754`.
- Vanilla header source: local SKSE source commit
  `872C2D6FE4BC17B9E7F74D66B38C229750CE18E0`.
- Missing `TopicInfo.psc` and `TESV_Papyrus_Flags.flg`: Rukan
  `Grimy-Skyrim-Papyrus-Source` commit
  `4BA71332B4851985240F582A76017216A3BD452F`, with file SHA-256 values
  `970D87591BDF9EA055344AACA47E01E7302E6351B39B5C109F24093D587796A3`
  and `DB28D5AE6C57AA9C4797F3E571F3E22B2443348D20CE730D0AF358F2746B1666`.

The compiler was invoked once per relative PSC using this option set (the
semicolon-separated import value is accepted by Caprica):

```text
Caprica.exe --ignorecwd --quiet --game skyrim \
  --import "<corrected-src>;<local-headers>;<skse64>/scripts/vanilla" \
  --flags "<local-headers>/TESV_Papyrus_Flags.flg" \
  --strict=1 --all-warnings-as-errors \
  --enable-ck-optimizations=1 --enable-debug-info=1 \
  --output "<output>" "<corrected-src>/<fragment>.psc"
```

All six compiles exited zero with no warnings or source errors.

## Binary validation and installed payload

Champollion decompiled and emitted assembly for every generated PEX without an
error. For each generated fragment, a normalized comparison against its intact
official sibling compared the sorted property table, local variables, and
ordered `Fragment_0` bytecode while ignoring only script/source identity,
compile metadata, debug line numbers/comments, and identifier case. All six
pairs were exact functional matches.

| Installed PEX | Bytes | SHA-256 |
|---|---:|---|
| `vlio_tif__050f8a8a.pex` | 969 | `8097D6F4A30AC8389A561D2086306D01FD1F9ACAF71FCDB80106E3FE352525CC` |
| `vlio_tif__050f8a8c.pex` | 973 | `DACA59A34F5A49696ADB22796EF12E30D3AB226380180733F026E3E16B1E9218` |
| `vlio_tif__050f8a8e.pex` | 973 | `65601C971707EFA7404BCBF0E656BB1474DEF6BFD1899BCF13E0A44D3D7E1C59` |
| `vlio_tif__050fdb94.pex` | 803 | `99158E36A58C3C45135B1BBD791F0E5E45E82C55DCEA3C274A402FE5F8FCC0AA` |
| `vlio_tif__050fdb98.pex` | 787 | `279BB665C54E8730AD0F08A605EE764EA37240CFA007D69A9F25D727A8306730` |
| `vlio_tif__050fdb9c.pex` | 785 | `1B36CFEBCE10E84123798705785D109A2F5F9D43C2E05E9ACF1D594802F48AE2` |

- Local archive: `Ensrick - Varinia Dialogue Fragment Fix 2026-08-30.7z`.
- Archive SHA-256:
  `FC31AF46675BBC200D9012EB8CBC2D79205E76FDD899F0B516DAFBB645C7F1FA`.
- MO2 mod: `Ensrick - Varinia Dialogue Fragment Fix`, enabled at priority 143.
- MO2 transaction: `20260830T032405369Z-9DF63C188F32`.
- Payload: exactly `Scripts/<six names above>.pex`; MO2 adds only `meta.ini`.
- Post-install ledger verification: 128 entries, zero problems.
- Post-install active plugin/master-order verification: 112 plugins, clean.
- Post-install active loose-file collision scan: clean for this overlay. The
  Varinia BSA did not contain these six paths, so the overlay supplies missing
  assets rather than replacing packaged PEX files.

The game was not launched as part of this headless task. Runtime route tests
should exercise one crow-dismissal line and each of the three spell-removal
choices before this private correction is treated as playthrough-proven.

## Interesting NPCs overlap audit

`3DNPC.esp` and `VLIOVarinia.esp` share 17 vanilla override chains: 12 `CELL`,
four placed-NPC references, and the Tamriel `WRLD` record.

- Eight CELL records are substantively identical between the two plugins.
- Three inn CELL records differ only in `WaterHeight`: Candlehearth Hall
  (`016789`), the Winking Skeever (`016A0E`), and the Silver-Blood Inn
  (`016DFE`). 3DNPC uses the standard no-water sentinel while Varinia serializes
  zero. Current later Lux winners retain the 3DNPC value.
- Dead Man's Drink (`03A184`) differs in `SkyAndWeatherFromRegion`; the later
  Lux winner retains the 3DNPC region value.
- The other shared CELL chains are Tamriel cell `000D74`, Thalmor Embassy
  exterior `00923C`, Fellglow Keep `015283`, Viola Giordano's house `016779`,
  Windhelm Hall of the Dead `016786`, Brunwulf's house `01678B`, Radiant
  Raiment `016A0F`, and Haelga's Bunkhouse `016BD4`.
- The four placed NPCs--Haelga (`019DDA`), Brunwulf (`01B117`), Adonato
  (`01B119`), and Orthorn (`02A389`)--are substantively identical. Varinia
  preserves 3DNPC's `Version2` value for Brunwulf and Adonato where USSEP's
  older value differs.
- Tamriel worldspace `00003C` is substantively identical across USSEP, 3DNPC,
  and Varinia. The final WENB Shades USSEP winner changes only the intended
  Water for ENB `LodWater` value.

The remaining final CELL differences from 3DNPC/USSEP are intended Lux
lighting, image-space, flags, or Water for ENB environment-map values. No
Varinia--3DNPC compatibility ESL is technically justified in the current
profile.

## Distribution boundary

The Nexus permissions require consent to modify or reuse the author's files.
The six generated PEX files are derivative corrections even though they are
small and contain no voice assets. Keep the overlay and its archive local. A
public modlist may fetch the official Varinia file and document the defect, but
must not include these PSC/PEX outputs unless the author grants permission.
