# Modern Lighting Overhaul 2 (MLO2) 5.4.1 adoption

Date: 2026-08-30

Status: installed and enabled; static qualification passed; foreground visual
and runtime acceptance remains open

## Decision

[Modern Lighting Overhaul 2](https://www.nexusmods.com/skyrimspecialedition/mods/160748)
is adopted as a particle-light foundation beneath Lux, Lux Orbis, Lux CS,
Light Placer, and the city/interior stack. It is not an interior-lighting
plugin and has no ESP, ESL, or ESM to sort. Its SKSE DLL attaches Community
Shaders particle-light templates to matching loaded meshes at runtime.

The exact current Nexus file was installed with the author's `Shadow Casters
Off` FOMOD branch, but an Ensrick-owned configuration overlay makes the
important 5.4.1 source default explicit: `disableLights=false`. Existing Lux
and city/interior placed lights are therefore not deleted. This is a deliberate
foundation posture, not an attempt to make MLO2 win over later city work.

## Current upstream state

| Item | Audited value |
|---|---|
| Nexus mod | 160748 |
| Current version | 5.4.1 |
| Nexus file | 796941, main file |
| Upstream update | 2026-08-29 |
| Changelog | Recompiled for the latest Skyrim update |
| Source repository | [TrumanGIT/MLO2](https://github.com/TrumanGIT/MLO2) |
| Audited source head | `c5479a459ebe8d4dfc2d4fdad63e422d0cf0d8ce` (2026-08-15, `fixed some bugs + removed an infinite loading hazard`) |
| Source release state | No tags or GitHub releases |
| Source licence | **None published**; GitHub reports no licence and the repository contains no `LICENSE` file |

MLO2 is current rather than abandoned: its Nexus binary was rebuilt one day
before this audit and the repository received a material bug-fix commit in
August 2026. The related ReLight line is newer and more ambitious, but the
MLO2 page does not mark MLO2 obsolete and MLO2 itself received the same current
runtime update. ReLight is an adjacent alternative, not a proven supersession.

The GitHub repository is source-visible, but it must not be described or
treated as open source. Nexus allows credited modification/bug-fix releases
while prohibiting re-upload elsewhere, but the absent repository licence means
we do not fork, rebuild, or redistribute the DLL without clarified permission.
The public modpack should reference the Nexus dependency. The owned INI contains
only Ensrick configuration policy and can be shipped separately.

## Exact vendor input and resolved output

- Archive: `160748-796941.7z`
- Nexus filename: `Modern Lighting Overhaul 2 (MLO2) 160748 5.4.1
  2026-08-29T11-05Z hfH9s6P9N.7z`
- Archive size: 8,650,881 bytes
- Archive SHA-256:
  `A1B4F65BF875383ED070F389B9E02F0EA254FB2D411E2C914C55EF07DB1577E1`
- Deterministic install plan:
  `records/fomod-plans/160748-mlo2-5.4.1.json`
- Resolved branch: `00 Main Module` plus `02 MLO.ini Whitelist/02 Shadow
  Casters Off`
- Resolved vendor output: 45 payload files, 40,568,383 bytes uncompressed
- MO2 mod: `Modern Lighting Overhaul 2 (MLO2)`
- Install transaction: `20260830T213542127Z-b47fc699a2d1`
- Priority transaction: `20260830T213554743Z-c43d1df8d0c6`

Every one of the 45 installed vendor payload files hashes identically to its
selected archive source. `meta.ini` is MO2 bookkeeping and is not part of the
vendor payload. The retained archive is byte-identical and the vendor mod has
not been edited.

Important binary hashes:

| File | Bytes | SHA-256 |
|---|---:|---|
| `SKSE/Plugins/MLO.dll` | 2,867,712 | `F9961780CEEBD4FBC558DC9EAAA88D4892931D8BDDF3C96096B5C9BE1849E937` |
| `SKSE/Plugins/MLO.pdb` | 37,588,992 | `02BF7A012E3BE2A8AFB78DC26F4746D08FF9C9AAE6B417F3E256982303027B8C` |
| `SKSE/Plugins/Masterlist.ini` | 4,317 | `9B05EBFBEB2D2DA209510772DE597F4074B9E91582AC9C40916277E681A8D03C` |
| selected vendor `MLO.ini` | 1,954 | `A5CBBED4A162C46C1A8D83B673446084306B212F9B10366543FE39997A727D44` |

The PDB exposes source paths and function names matching the current repository,
including the current hook and template-attachment functions. That is useful
correspondence evidence, but not reproducible proof: upstream publishes no tag,
release manifest, toolchain lock, or signed source-to-binary attestation.

## Runtime gate and exact stack

The live game is Skyrim SE/AE 1.7.104.0 with SKSE 2.3.1. The required stack is
present and enabled:

- Address Library v12, including `versionlib-1-7-104-0.bin`;
- powerofthree's Tweaks 1.17.1;
- the source-built Community Shaders AIO runtime;
- Community Shaders Light Limit Fix with particle lights and particle-light
  culling both enabled;
- Light Placer 4.2.1;
- Lux 7.0, Lux Orbis 4.5, Lux CS 2.6.0, Lux Via 2.2, and their active-profile
  patches.

The DLL's PE timestamp is `1788000388` (`2026-08-29T10:46:28Z`). Its exported
SKSE version structure declares Address Library independence and no-struct use,
and the project gate reports `PASS (version independent)` on 1.7.104.

Upstream version metadata is stale and should not be used as the compatibility
signal: the DLL reports plugin version `1.0.0.0`, author `AUTHOR_NAME`, and its
compatible-version array is filled with placeholder `1.0.0.0` values. The FOMOD
`info.xml` also says 5.3 even though the Nexus file is 5.4.1. The PE timestamp,
SKSE independence flags, current rebuild date, Address Library usage, and
current source are the relevant evidence.

The MLO2 page's old Light Limit Fix advice mentions billboard-radius and
brightness controls. Those controls do not exist in the installed Community
Shaders 1.8-era Light Limit Fix settings or current source. No obsolete keys
were invented. The live supported settings already have
`EnableParticleLights=true` and `EnableParticleLightsCulling=true`.

## Configuration and ordering contract

MO2 priority zero is the lowest asset winner. The installed order is:

| MO2 priority | Mod |
|---:|---|
| 33 | Modern Lighting Overhaul 2 (MLO2) |
| 34 | Ensrick - MLO2 Foundation Config |
| 36 | Lux |
| 37 | Lux Orbis |
| 38 | Light Placer |
| 39 | Lux CS |
| 175+ | Grand Solitude, Solitude Docks, Snazzy interiors, and their patches |

This is the technically correct expression of “MLO2 before city/interior
overhauls.” There is no synthetic plugin load-order rule because MLO2 ships no
plugin.

The separately tracked overlay is:

- source: `overlays/ensrick-mlo2-foundation-config/SKSE/Plugins/MLO.ini`;
- MO2 mod: `Ensrick - MLO2 Foundation Config`;
- transaction: `20260830T213608570Z-70e715a645a3`;
- effective INI SHA-256:
  `56571056A43EDF58EA281949B07977AFB244D7060A6724C0D8A14CBD2D99E227`.

The source contains a newer master switch that the FOMOD omits:

```ini
disableLights=false
```

With this setting, MLO2 does not remove any existing placed light. The
`disableShadowCasters`, `disableTorchLights`, and plugin-whitelist settings
only refine behavior if `disableLights` is deliberately changed to `true` in
the future. The defensive whitelist already protects `Lux`, `Grand Solitude`,
`Solitude Docks`, and `Snazzy` by case-insensitive owner-plugin substring. Add
each future city/interior family's stable fragment before ever opting into
placed-light deletion.

`enableColorConsistency=true` remains the author's default. Unlike light
deletion, the current hook can recolor existing non-excluded lights even when
`disableLights=false`. This is the one material visual choice that static
analysis cannot settle. If Lux's authored colour variation looks flattened or
uniformly warm in the foreground tour, change only the owned overlay to
`enableColorConsistency=false`; do not edit the vendor INI.

## Conflicts and static validation

- No ESP/ESL/ESM, Papyrus script, behavior file, or interface file is shipped.
- MLO2's template meshes and DLL are unique in the enabled profile.
- The owned INI is the intentional and only order-sensitive MLO2 configuration
  winner.
- MLO2's `textures/!_Rudy_Misc/effects/fxglowENB.dds` loses to SFCO3 as intended;
  the two files are byte-identical with SHA-256
  `4BF16CEB3C5F0BCCD9814BD2E6B11EEFDE3A1095757E9C9A4E45D157C20FA831`.
- Lux CS and Light Placer use their own configuration paths, so there is no
  static file collision. Both can still illuminate the same visual fixture at
  runtime; that is a visual smoke-test item rather than a load-order error.
- Ledger verification: 187 rows, zero problems.
- Plugin/order verification: 198 active, 280 discoverable, `CLEAN`.
- Active file scan: 35,300 files, 1,891 expected collision paths, 24
  order-sensitive paths; the MLO2 INI winner is correct.
- Physical Skyrim `Data` contains no `MLO.dll`, `MLO.ini`, `Masterlist.ini`,
  `Meshes/MLO`, or MLO2 texture. Installation remains MO2-contained.
- No game, MO2 GUI, visible tool, or popup was launched.

The latest existing logs cannot prove MLO2 runtime loading because this is the
first installation. `MLO.log` should be created only on the next user-owned
foreground launch.

## Source-level limitations worth tracking

1. The source repository has no published licence, tags, or releases.
2. DLL/FOMOD version metadata is stale as described above.
3. The FOMOD's Shadow Casters wording predates the `disableLights` master switch;
   in 5.4.1 the switch defaults false and is absent from all shipped INIs.
4. Numeric INI parsing uses uncaught `std::stoi` for logging level and RGB
   values. A malformed local value could terminate plugin initialization. The
   owned overlay uses valid literals and should remain schema-validated.
5. The Nexus bug tracker still shows reports about lights shining through
   geometry, torch lights, and NPC-attached light. Some predate 5.4.1 and the
   current source explicitly revised torch attachment and removed an infinite
   loading hazard, so they are acceptance targets rather than established
   current failures.

No source modification is justified before the foreground tour. If a defect is
reproduced, pursue an upstream report first. Any necessary local DLL work must
remain a separate overlay and cannot be publicly redistributed until the
licence/permission boundary is resolved.

## Foreground acceptance matrix

The next user-owned test should cover:

- [ ] Main menu and save load complete without a popup, CTD, or infinite cell
      transition; `skse64.log` shows `MLO` accepted and `MLO.log` is present.
- [ ] Bannered Mare and Dragonsreach: no double-bright candles, missing bulbs,
      lights through floors, or flattened Lux colour design.
- [ ] Solitude city, docks, and at least one Bryling/Erikur/Vittoria interior:
      later city/interior lighting remains authoritative.
- [ ] Nordic dungeon and Dwemer room: candles, fires, and Dwemer fixtures have
      particle light with no obvious duplicate halos.
- [ ] Hand-held torch in first and third person, including unequip/re-equip:
      light attaches only while appropriate and does not stick to the actor.
- [ ] NPCs near fireplaces do not appear to emit light after moving away.
- [ ] Check the MLO2, Community Shaders, and crash logs after the tour.

If the only failure is excessive warmth or lost Lux colour contrast, set
`enableColorConsistency=false` in the owned overlay and repeat the same fixed
cells. If fixtures are genuinely double-lit, capture the exact mesh/form and
cell before deciding whether MLO2 or the corresponding Lux CS/Light Placer
mapping should own that fixture.

## Rollback

The reversible first response is to disable, in this order:

1. `Ensrick - MLO2 Foundation Config`;
2. `Modern Lighting Overhaul 2 (MLO2)`.

That immediately restores the prior Lux/Lux CS/Light Placer stack. Do not use
old transaction rollback IDs after unrelated profile changes, because a
historical list before-image can overwrite later ordering work. For complete
removal, verify the two exact mod names and use recoverable `mod-trash` through
MO2Headless, then remove the two ledger rows and return Nexus 160748 to
unreviewed. Never delete the physical game `Data` directory or edit another
author's mod folder.
