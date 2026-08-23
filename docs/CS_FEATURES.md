# Community Shaders build checklist (deep-read harvest reference)

Everything CS-adjacent the full catalogue read surfaced, in one place. CS core
1.4.7 already bundles Light Limit Fix, Sky Sync, grass lighting/collision, and
SSS (per the earlier bundling analysis) - do NOT install standalone copies of
those.

## Feature modules worth adding (each is its own decision, all CS-native)

- **Wetness Effects 112739** - official CS wetness module.
- **Dynamic Wetness 158207** - SKSE character wetness; pairs with the above.
- **HDR - Community Shaders 179371** - native 10-bit HDR output.
- **Effects 11 (179824)** - runs most ENB *presets* under CS (2026-08). This
  may reopen preset-grade color grading without ENB; NAT Effect 11 (186575)
  is the first weather-tuned example.
- **CS Light 138443** + Light Placer - emissive-object config hub; third-party
  relights (e.g. Lux CS-style location relights) hang off it.
- **ISL Helper SKSE 179132** - inverse-square falloff conversion; Lux CS lists
  it, so it arrives with the lighting slot if Lux wins.
- **Particle Wind 174812** / SMP Wind 76776 - engine particle wind; SMP Wind
  drives FSMP cloth (we run FSMP cloth-only, so this one is on-theme).

## Known CS hazards found in the read

- **Skylighting can crash heavy city cells** - CS Crash Fix - Ultimate
  Markarth 165498 is the proof-case and the fix for that mod; if unexplained
  city CTDs appear later, suspect Skylighting first.
- **FWMF paper maps render overbright under CS** - CS-FWMF Map Brightness Fix
  171391 (only matters if the paper-map branch wins the navigation slot).
- **Gray Cowl worldspace** needs its CS world-map fix 155390 + Map Edge Fix
  145788 (both in the gray-cowl support list).
- Seasonal Landscapes grass textures need the CS grass-lighting edits 163761
  for consistent tint (only if Seasonal Landscapes is adopted).
- ENB-particle-light meshes still WORK (CS Particle Lights consumes them) -
  that entire mod class was deliberately left undecided, not skipped.

## Rule-of-thumb carried through the whole sweep

ENB *presets* not built for CS, ENB-only support files, and ENB-artifact
fixes were skipped with evidence; CS-compatible ReShade/Effects-11 presets,
ENB-light mesh packs, and anything stating CS support were left for you.
