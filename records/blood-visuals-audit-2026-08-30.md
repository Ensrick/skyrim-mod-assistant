# Blood visuals audit — EBT versus the current stack

**Audit date:** 2026-08-30  
**Scope:** research and archive inspection only; no candidate was installed,
enabled, added to Keep/Skip, or launched.  
**Runtime target:** Skyrim SE/AE 1.7.99, SKSE 2.3.x, Community Shaders, VioLens.

## Outcome

Enhanced Blood Textures is no longer the strongest complete blood system for
this build. The current visual leader is:

1. [Sanguine Symphony 1.3.3](https://www.nexusmods.com/skyrimspecialedition/mods/148388)
2. [Core Impact Framework 2.0.5](https://www.nexusmods.com/skyrimspecialedition/mods/146873)
3. [Dynamic Bloodpool Framework 1.1.0](https://www.nexusmods.com/skyrimspecialedition/mods/172080), if animated pools are wanted

This is the closest thing to a modern successor to full EBT: directed 3D
sprays, weapon/armor/hit-location-aware impacts, actor wounds, surface decals,
separate insect blood and automaton oil, and mesh-based animated pools. Its
author explicitly recommends removing EBT because EBT Lite's textures become
redundant and full EBT forces blood on impacts outside Sanguine Symphony's
logic.

It is not an unconditional install recommendation. The new stack contains
three closed-source native DLLs and has had active update churn through August
2026. It is the better visual architecture, but EBT Lite remains the
conservative, runtime-independent fallback.

## Current profile facts

- No blood overhaul, EBT, Just Blood, Dirt and Blood, Sanguine Symphony,
  Maximum Carnage, Dismembering Framework, Deadly Spell Impacts, or Precision
  is enabled.
- `Disable Screen Blood`, `No More Blur on Hit`, and `3rd Person Camera Stagger
  Remover` are enabled.
- SKSE, Address Library, SkyUI, Community Shaders, SPID, and powerofthree's
  Papyrus Extender are enabled. MCM Helper is installed but disabled/parked.
- VioLens is enabled.
- The active profile has no loose-file collision with the candidate blood
  texture paths.

## Version and payload comparison

| Candidate | Current file | Implementation found in archive | What it covers | Risk / burden |
|---|---|---|---|---|
| **Sanguine Symphony** | 1.3.3, 2026-08-01 | ESP-FE, `SanguineSymphony.dll`, PDB, two BSAs, 25 CIF/DBF JSON mappings, INI; BSA also contains five Papyrus MCM/maintenance scripts and sources | Directional sprays, weapon-specific wounds and decals, impact sounds, insect blood, automaton oil, optional fatal-hit impulses, screen/death effects, pools through DBF | Modern and modular; closed native source; defaults violate this build's screen-effect policy until overridden |
| **Core Impact Framework** | 2.0.5, 2026-08-28 | DLL, PDB, INI, five biped-mapping JSONs; no game plugin or Papyrus scripts | Native impact/spray engine used by Sanguine | Required native dependency; very current, therefore higher update cadence |
| **Dynamic Bloodpool Framework** | 1.1.0, 2026-07-25 | DLL, PDB, INI and four NIFs; no ESP/Papyrus | Script-free, terrain-conforming, animated mesh pools driven by JSON | Optional; collision-poor surfaces can clip; closed native source |
| **Sanguine Symphony PBR** | 1.22, 2026-08-06 | ESP-FE, 103 DDS, 94 material/patcher JSONs; updated for SS 1.3.3 and DBF 1.1 | Community Shaders PBR conversion of SS decals and DBF pools | Attractive later layer, but its static-decal side ships `PBRNifPatcher` instructions and should wait for the PGPatcher path |
| **Enhanced Blood Textures full/SPID** | 4.0 main file, 2021-12-15; page updated 2022-06-28 | Non-light ESP, five SPID Papyrus scripts (seven standard), BSA, textures/sounds; 247–251 records and 64 overrides | More/frequent splatters, wounds, trails, drips, pools, spasms, green insect blood, oil, sounds, longer weapon blood, screen blood | No DLL and therefore runtime-stable, but larger plugin/override surface and persistent scripted quest |
| **Optimised Scripts for EBT** | 1.0.0 main, 2022-10-08; DF patches 2024-08-13 | Five replacement PEX files | Micro-optimises full EBT; SPID build uses PAPER `OnImpact` | PAPER is not installed; does not modernize EBT's decal/pool architecture |
| **EBT Lite** | 1.1, 2018-10-11 | Non-light ESP plus 15 DDS; no scripts | Textures, wounds, decals, weapon-blood duration; no scripted trails/pools | Stable but 15 vanilla BPTD and 21 IPCT overrides create a larger body/dismemberment conflict surface than Sanguine |
| **Just Blood** | 1.3, 2025-08-04 | ESP-FE, SPID INI, five DDS; no scripts | Health-driven blood overlays on player, NPCs and supported creatures | Excellent tiny fallback/add-on, but largely redundant beside Sanguine's health/weapon-aware wounds |
| **Dirt and Blood** | 2.38, 2025-10-31 | ESP-FE, SPID INI, 13 Papyrus scripts plus source, 17 DDS | Persistent player dirt/blood, NPC overlays, bathing/rain/swimming cleanup, reactions and optional gameplay effects | A survival/hygiene system, not a world-blood replacement; can visually stack with Sanguine and needs its own decision |

Archive inspection found that stock Sanguine Symphony uses 61 BC7 textures:
43 at 1K, 10 at 2K, six at 512, and two 512×1024. The PBR conversion also
tops out at 2K. Both satisfy the modpack's 4K hard cap without an optional
downscale. Do not use the 147 MB Ultra-HD texture option; the stock pack is
already the appropriate performance/quality tier.

## Why the modern architecture wins

Full EBT makes pools by stacking traditional decals and keeps Papyrus effects
active around the player. DBF instead grows one terrain-conforming mesh using
native code and JSON configuration. Sanguine's plugin originates its records
instead of overriding vanilla records: inspection found 138 records, zero
plugin-record overrides, and an ESL flag. EBT full had 64 vanilla override
records; EBT Lite had 50.

The claim that Sanguine is literally “script-free” is imprecise. Its archive
contains five Papyrus scripts for MCM/maintenance. The combat implementation is
native, however, and there is no broad Papyrus actor scan like older systems.

## Non-negotiable screen-effect configuration

Sanguine's shipped defaults are unsuitable for this profile:

```ini
[Misc]
fScreenSplatterDuration = 20.0

[DeathEffect]
iIMODEffect = 1
bSlowTimeStatus = true
```

Any adoption must include a separate modpack-owned configuration patch with at
least:

```ini
[Misc]
fScreenSplatterDuration = 0.0

[DeathEffect]
iIMODEffect = 0
bSlowTimeStatus = false
```

`Disable Screen Blood` should remain enabled as defense in depth. Sanguine
applies its runtime setting after plugins load, so the external GMST plugin is
not a substitute for setting `fScreenSplatterDuration=0`. Its fatal-hit impulse
acts on actor body nodes, not the camera; that feature can be tested separately
without reintroducing camera stagger.

EBT also changes the same screen-blood GMST family that `Disable Screen Blood`
overrides. If EBT is chosen, the existing screen-removal plugin must win the
record chain and EBT's own no-screen option should be selected.

## Compatibility findings

### Community Shaders

Stock Sanguine uses ordinary BC7 decals and meshes and does not require ENB.
DBF 1.0.1+ added PBR shader support with Community Shaders collaboration. The
optional [Sanguine Symphony PBR 1.22](https://www.nexusmods.com/skyrimspecialedition/mods/170736)
is the native CS visual upgrade. Its archive includes PGPatcher instructions;
PGPatcher is not active in the profile, so install and validate the stock stack
first or explicitly adopt the PGPatcher pipeline before adding the PBR layer.

### Bodies, skins, and Precision

Sanguine's ESP has no vanilla body, race, NPC, armor, or skin overrides. Wounds
are impact/effect assets, so CBBE, HIMBO, Reverie, and SkySight are not direct
record conflicts. Precision is recommended, not required; it improves impact
localization when it is later adopted. EBT Lite is less clean here because it
overrides 15 vanilla body-part-data records.

### VioLens and killmoves

Sanguine 1.3 specifically improved pool triggering after killmoves and permits
its effects during killmoves. There is no direct plugin override conflict with
VioLens. Disable Sanguine's independent death imagespace and slow-time effects
so it does not layer cinematic feedback over VioLens. Pool and decal behavior
still needs a real killmove smoke test.

### Dirt and Blood / Just Blood

These apply actor overlays rather than replacing the impact/pool architecture.
They can coexist at the record level, but two blood-on-body systems can look
overdone. `Just Blood` adds little beside Sanguine and should not be stacked.
Full Dirt and Blood remains a valid later survival/hygiene decision because its
dirt accumulation, rain/swimming cleanup, bathing and reactions are unique.

### Related mods that do not fill this slot

- [Deadly Spell Impacts 1.9](https://www.nexusmods.com/skyrimspecialedition/mods/12939)
  improves elemental marks on surfaces; it complements rather than replaces a
  blood system.
- [Maximum Carnage](https://www.nexusmods.com/skyrimspecialedition/mods/43494)
  and [Dismembering Framework](https://www.nexusmods.com/skyrimspecialedition/mods/126203)
  occupy the gore/dismemberment slot. They should be decided separately.
  Sanguine is explicitly designed to complement Dismembering Framework.
- `Blood and Ash` (85718) is a Dawnguard/Dragonborn female NPC appearance
  replacer and is unrelated despite its name.
- `Enhanced Blood Textures - Alternative Splatters` and `Rip n Tear` are
  retexture choices for EBT-era paths, not replacements for the system.

## Runtime and stability evidence

The three modern DLLs export both `SKSEPlugin_Load` and
`SKSEPlugin_Version`, identify as CommonLibSSE-NG-compatible, and were built in
July/August 2026. Their metadata declares Address Library post-AE independence
and no-structure-use compatibility; their post-2025 build timestamps satisfy
the local SKSE 1.7.99 Address Library v5 gate. The author states that SE, AE and
VR are supported.

That is eligibility evidence, not a launch result. Because this audit was
explicitly read-only, 1.7.99 loading and combat behavior remain unverified.
The archives include PDBs, which materially improves crash attribution.

Sanguine's 2026 changelog includes fixes for a start-up CTD with SSE Fixes,
combat-freeze hardening, delayed-task safety, True Directional Movement spray
crashes, oversized pools, and settings not applying until MCM opened. This is
good maintenance evidence, but also demonstrates that the stack has nontrivial
native complexity. Pin exact versions and smoke-test them as a unit.

## Permissions and modpack packaging

- Sanguine Symphony, CIF, and DBF may not be redistributed as part of the
  modpack. Their native source is not currently public.
- Sanguine explicitly allows patches, add-ons, retextures and translations
  that require the original mod. A separate settings patch is therefore the
  correct public-pack form; the installer must fetch the originals.
- DBF requires permission before modified framework files can be published.
- Sanguine PBR's author permits reuse outside paid mods and reuploads, subject
  to the original assets' terms. It should still be fetched as a dependency,
  not bundled blindly.
- EBT-derived texture/script add-ons inherit EBT asset permission constraints;
  do not copy their assets into an owned patch.

## Ranked decision

1. **Recommended visual target:** Sanguine Symphony 1.3.3 + CIF 2.0.5 + DBF
   1.1.0, stock texture BSA, with the no-screen/no-death-filter/no-slow-time
   settings patch. This is the current best feature and performance design.
2. **Recommended conservative fallback:** EBT Lite 1.1 plus the existing
   `Disable Screen Blood`. It avoids native DLLs and Papyrus but gives up the
   modern directed sprays and animated pools. Its body-part and impact records
   need xEdit review against any future dismemberment system.
3. **Do not choose for this slot:** full EBT SPID. It is functional and
   runtime-independent, but its old scripted pool/impact architecture and
   conflict surface are no longer the best fit. If selected anyway, use the
   SPID variant plus Optimised Scripts and PAPER, and never mix it with
   Sanguine.

Open user decisions before installation:

- Accept the closed-source native Sanguine/CIF/DBF stack in exchange for the
  modern system, or choose the conservative EBT Lite fallback?
- Include animated blood pools (DBF), or start with Sanguine+CIF only?
- Add the Community Shaders PBR conversion now by adopting PGPatcher, or first
  validate the stock 2K stack?
- Treat Dirt and Blood as a later hygiene/survival layer, independently of this
  blood-impact decision?

## Primary sources

- [Sanguine Symphony page and changelog](https://www.nexusmods.com/skyrimspecialedition/mods/148388)
- [Core Impact Framework](https://www.nexusmods.com/skyrimspecialedition/mods/146873)
- [Dynamic Bloodpool Framework](https://www.nexusmods.com/skyrimspecialedition/mods/172080)
- [Sanguine Symphony PBR](https://www.nexusmods.com/skyrimspecialedition/mods/170736)
- [Enhanced Blood Textures](https://www.nexusmods.com/skyrimspecialedition/mods/2357)
- [Optimised Scripts for Enhanced Blood Textures](https://www.nexusmods.com/skyrimspecialedition/mods/76767)
- [Just Blood](https://www.nexusmods.com/skyrimspecialedition/mods/46501)
- [Dirt and Blood](https://www.nexusmods.com/skyrimspecialedition/mods/38886)

Version/file metadata above was verified through the authenticated Nexus API;
payload claims were checked against downloaded archives in ignored work
storage. No private API material is present in this record.
