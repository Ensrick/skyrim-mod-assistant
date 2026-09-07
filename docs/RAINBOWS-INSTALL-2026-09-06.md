# Rainbows Remade — installation and repair

Owner decision, September 6, 2026: install Rainbows Remade; Skip Wonders of
Weather and Shooting Stars SE. No facial-animation, expression-controller,
audio or lightning mod was approved by the accompanying research questions.

## Installed route

| Priority, low to high | Nexus SSE88161 input | Selected payload |
|---|---|---|
| Rainbows Remade - 1K | File374394, v1.2.0 | ESP-FE and BSA; complete 1K edition, not an add-on requiring 4K |
| Rainbows Remade - Official Hotfix | File382939, v1.2.1 | Eleven original loose meshes |
| Rainbows Remade - Partial Moonbow Path Fix | Same official hotfix | One intact vendor mesh mapped to the corrected virtual path |

The [main plan](../records/fomod-plans/88161-rainbows-remade-1k.json),
[official-hotfix plan](../records/fomod-plans/88161-rainbows-remade-hotfix.json)
and [repair plan](../records/fomod-plans/88161-rainbows-remade-partial-moonbow-fix.json)
are the reproducible installation recipe. Original archives remain immutable.
No new binary-editing tool, synthetic texture, custom plugin or dependency is
required. The one active ESP loads before the global weapon patch, preserving
every previously active plugin's relative order.

## Confirmed defect and minimal correction

The official v1.2.1 `moonbowpartiall.nif` still names
`textures/rainbows/moonbowpartiall.dds`, which the package does not contain.
The existing correct texture is `rainbowpartiall.dds`. Correcting only that
path changes three bytes and yields exactly the official hotfix's existing
`rainbowpartiall.nif`. The final installation therefore maps that intact asset
to `meshes/rainbows/moonbowpartiall.nif` in a separate higher-priority folder.

Both meshes are250,969bytes. Bad source SHA256:
`0CD57DA983810EC9E5F1D91F0163F022763B8FE47C8C2DE1FF7ABDBC544B4BCF`.
Correct winner SHA256:
`2CD39FF5FB5392F6DDCD10AA72402969C893FB0C5A9A99558A657380F066B405`.
This is consistent with the hotfix's other moonbow meshes sharing the ordinary
rainbow texture/model data. Geometry, material settings and scripts are unchanged.

The author/posts acknowledge moonbow texture problems generally; the exact
missed-left-path defect was not found acknowledged in the bounded review.
[Our issue250](https://github.com/Ensrick/skyrim-mod-assistant/issues/250)
tracks the repair and remaining visual acceptance. No upstream report was sent.

## Evidence and remaining test

Independent inspection and live-file verification found14 exact vendor payloads,
11 resolving effective mesh texture paths and eight1024x1024 BC7 textures with
complete11-level mip chains. ESP-FE adds18 records, zero overrides and no
equipment; Skyrim.esm is its only master. Six packaged scripts decompile;
there is no native DLL. Current Azurite/CS integration does not require a new
weather patch for this self-contained effect, but appearance remains untested.

The author intentionally limits the effect by distance/viewing angle and uses
fixed cardinal placement; this is not a physically calculated CS rainbow.
Disappearance while moving is therefore not automatically the missing-texture
defect. Chance, lifespan, moonbows and in-game notifications retain defaults.
No promise of better sun alignment or changed frequency is made.

The [bounded installation receipt](../records/rainbows-install-2026-09-06.json)
records exact transactions, curation state and dependent patch gates. Weapon
regeneration preserves3494 overrides and all27 translations byte-for-byte;
cloak re-audit preserves240 directives and569 present mesh winners. The existing
seven cloak asset absences remain separately tracked, not repaired here.

**Runtime UNVERIFIED.** No game, save, INI or desktop/UI launch was performed.
Observe a normal rainbow and both partial moonbow variants on the project's
supported fresh-character test setup before closing issue250. Known unrelated
ledger gaps and existing runtime issues are not resolved by this installation.

## Publication

Publish original plans, documentation and receipts only. Users obtain the two
[official downloads](https://www.nexusmods.com/skyrimspecialedition/mods/88161?tab=files)
and run the existing installer locally. No vendor NIF/DDS/BSA/ESP/PEX or private
prototype package is committed. The mod's and underlying contributors'
permissions remain attached to their assets; an installer mapping does not
change their ownership or licence.
