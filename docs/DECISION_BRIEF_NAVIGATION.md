# Decision brief - map and worldspace navigation

This build spans many worldspaces (Bruma, Wyrmstooth, Beyond Reach, the Gray
Cowl Alik'r, Vicn's realms), so the map slot is really three decisions plus a
QoL pick. All candidates undecided, harvested with evidence.

## 1. Map style branch (pick one)

| branch | mods | notes |
|---|---|---|
| **Paper maps** | Flat World Map Framework 29932 + A Clear Map of Skyrim 56367 | FWMF is the framework; A Clear Map covers Bruma/Beyond Reach worldspaces - the strongest multi-world fit. Community Shaders caveat: needs **CS-FWMF Map Brightness Fix 171391** (overbright paper maps under CS). Per-world paper maps exist for Haafstad, Akavir, etc. |
| 3D vanilla+ | A Quality World Map (already in your pool) | classic; modded worldspaces get whatever the land mod ships |
| Immersive outlier | No Google Maps Skyrim 147105 | SKSE rework that de-Googles navigation entirely; a playstyle statement, not a default |

## 2. Marker framework (pick one)

- Kept already: **Atlas Map Markers** (installed base decision earlier).
- CoMAP 56123 is the rival framework (icon variety, addon ecosystem - the
  VIGILANT/DAc0da CoMAP addons in the harvest hang off it).
- Map Markers Complete 4138 is the older AIO alternative.
Atlas vs CoMAP is the real question; the Vicn addons slightly favor CoMAP.

## 3. Cross-worldspace travel QoL (pick one, both are new)

- **Map Menu Extension 188483** (2026-08) - ESO-style world menu to open other
  worldspaces' maps and travel; the polished pick.
- World Map Selector 187315 - same service, simpler presentation.
Either one directly serves the Bruma/Wyrmstooth/Gray Cowl design.

## 4. Cheap adds regardless of branch

- STB Markers Control 161110 - prune marker clutter dynamically.
- Baka World Map Pan Speed 153672 - per-worldspace pan speed (2026-08-23).
- Map Edge Fix 145788 + Gray Cowl World Map CS fix 155390 (already in the
  gray-cowl support list) - required-reading if the paper branch wins.

## Recommendation shape (not a decision)

The multi-world design pushes toward: FWMF + A Clear Map + CS brightness fix,
Atlas kept as-is unless the Vicn CoMAP addons matter to you, plus Map Menu
Extension. The 3D branch stays viable if paper maps feel wrong in-hand - it's
a pure taste call you can make from screenshots on the mod pages.
