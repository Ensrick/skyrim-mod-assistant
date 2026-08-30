# Decision brief - interior lighting (slot #1)

The most patch-heavy slot in the build; cities and every interior-touching mod
patch against whichever wins. Renderer is Community Shaders, which changes the
calculus: CS ships Light Limit Fix, so light-count ceilings that shaped the
older mods matter less, and one candidate is built *for* CS.

## Candidates

| mod | id | version | updated | endorse | CS posture |
|---|---|---|---|---|---|
| **Lux** (+ Lux CS addon) | 43158 + 153919 | 7.1 + 2.6.0 | 2025-12 / **2026-08** | 31k + 6.2k | **Lux CS is a dedicated Community Shaders build** - HDR tonemapping via CS + SKSE, explicit LLF guidance in its FOMOD |
| ELFX (+ Shadows, Fixes, Exteriors-Fixes) | 2424 (+63790, 25498, 26327) | 3.06 | **2017** | 139k | base frozen 2017; kept alive by its addon/patch family; ENB-era design |
| Realistic Lighting Overhaul | 844 | 5.0.4 | 2024-09 | 61k | script-free, self-contained; no CS-specific work |
| Relighting Skyrim | 8586 | 3.1 | 2026-03 | 21.8k | page states compatible with **both CS and ENB**; conservative - only relocates light sources, no ambience changes |
| Luminosity | 16830 | 4.2 | 2021 | 12.7k | Cathedral-era, dimmer-vanilla feel; dormant |

## What the data says

- **Lux family is the only actively developed line** (Lux CS updated this
  month) and the only one engineered for your renderer. Its cost: the largest
  patch surface (Lux/Orbis/Via each carry patch hubs), though FOMODs
  auto-detect most of it.
- **ELFX has the biggest legacy ecosystem** (139k endorsements, every city mod
  has an ELFX patch) but the base is nine years old and needs three companion
  mods to be current. Its look leans dramatic/contrasty.
- **Relighting Skyrim is the low-risk floor**: explicitly CS-tested,
  near-zero patch burden, but it only *corrects* light placement - it will
  not transform interiors.
- RLO and Luminosity are functional but neither has CS-era momentum.

## Deep-read additions (found after this brief was first written)

- **ELFX - SkyPatcher (150615)**: auto-restores ELFX lighting wherever other
  mods override it - this shrinks the "ELFX = patch hell" argument above by a
  lot. ELFX + Fixes + SkyPatcher is now a more credible third finalist.
- **Modern Lighting Overhaul 2 (160748)**: CS-required SKSE light-source
  upgrade line (2026-08). It composes with a placement mod rather than
  competing. MLO2 5.4.1 is now installed as a foundation below Lux and the
  city/interior stack; MLO MISC was not implicitly adopted.
- **Umbrae Lucem (115616)**: one-mod interior+exterior lighting/shadows with
  torch/candle smoke - a lighter-weight all-in-one if the Lux stack feels
  heavy.
- Darkness layers that stack with any winner: Dynamic Seriously Dark
  Dungeons 7535, Ambiance 46383 (stealth-balanced ambient recalibration).
- Native Mesh Light Flicker Fix 186432 - engine light-slot fix worth taking
  regardless of winner.

## Recommendation shape (not a decision)

Two honest finalists: **Lux + Lux CS** (modern, CS-native, heavier patching)
vs **Relighting Skyrim** (conservative, nearly patch-free). ELFX only if you
already know you love its look and accept the four-mod stack to modernize it.

The placement decision is no longer open in the active profile: Lux + Lux CS
is the installed winner. MLO2 is a separate runtime particle-light layer, not
a replacement for Lux. Exact version, source/licence review, ordering contract,
configuration, rollback, and foreground acceptance are recorded in
`records/mlo2-5.4.1-2026-08-30.md`.

## How to decide with your eyes

Install one finalist, then in-game: `bat claude` batches can `coc` you through
a fixed tour - `WhiterunBanneredMare`, `WhiterunDragonsreach`, a Riften
cistern, a farmhouse, a dungeon (`BleakFallsBarrow01`) - at day and night
(`set gamehour to 22`). Swap finalist, repeat the same tour. The MO2 profile
system can hold both variants so the swap is a profile flip, not a reinstall.
