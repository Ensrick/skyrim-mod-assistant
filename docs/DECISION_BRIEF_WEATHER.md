# Decision brief - weather (slot #2 by patch weight, after lighting)

Renderer is Community Shaders, and unlike lighting this slot now has TWO
candidates built natively for it. Everything below is undecided; harvested
with evidence across the full deep-read.

## The CS-native finalists

| line | ids | posture |
|---|---|---|
| **NAT.CS III** | 139567 (+ NAT Effect 11 186575) | NAT 3 ported natively to CS - the headline CS-era weather. NAT Effect 11 (2026-08-22) is an Effects-11 polish preset tuned for NAT + Lux CS - i.e. the weather and lighting slots reinforce each other if NAT + Lux both win. |
| **Azurite III CS** | 138991 family | second CS-native line; big ecosystem of self-serve tweaks found in the read (ambient lighting edits 162246, darker nights 162673, vanilla-ish nights, no-custom-clouds, Reduced Cut 147751, MCM preset RAW 163516) - Azurite is the "dial it yourself" pick. |

## Legacy candidates still alive (work under CS, no CS-specific work)

- Rustic Weathers 8398 (medieval palette), Mythical Ages 11578, NAT classic
  12842, Climates of Tamriel 2237, Obsidian (via Obsidian CS tweaks seen in
  the read), Wander, Azurite II.
- RAID Weathers 63116 - the stealth-balance outlier (weather as gameplay).

## Layers that stack with any winner

- True Storms 2472 - additive storm layer (patch availability varies by
  winner).
- Mists of Tamriel 78703 - volumetric mists, ships patches for the majors.
- Darker Nights 694 - attaches to whichever wins if its nights are too kind.
- Wetness: CS Wetness Effects 112739 + Dynamic Wetness 158207 are
  renderer-side and weather-agnostic.
- Worldspace consistency: Azurite-Wyrmstooth tweaks 178572 exist if Azurite
  wins; Bruma/Reach coverage should be checked for NAT before committing.

## Recommendation shape (not a decision)

Two honest finalists: **NAT.CS III** (curated look, pairs with the Lux CS +
Effects 11 stack) vs **Azurite III CS** (bigger self-tuning ecosystem). Legacy
lines only if you already love one. Same eyes-on method as lighting: profile
A/B, `fw` through clear/rain/storm/snow at noon and 22:00 in tundra, Reach,
and a snow hold; the MO2 profile flip makes it a 10-minute comparison.
