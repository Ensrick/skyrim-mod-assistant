# Decision brief - the dragon package (late-game pillar)

Dragons are your designated late-game, so this slot is a PACKAGE: one combat
core plus stacking layers. Everything below is undecided and harvested with
evidence; nothing has been queued.

## The core (pick exactly one)

| mod | id | shape |
|---|---|---|
| **Dragon War** | 51310 | SKSE-driven AI/fight overhaul - the heavyweight, most patched-against modern core |
| KS Dragon Overhaul 2 | 19051 | the classic scripted rival; MCM-tunable pacing, older design |

## Stacking layers (compatible with either core, add to taste)

- **Dragons Use Thu'um 87085** - voiced shout AI; the single biggest "dragons
  feel like dov" upgrade per endorsement-weight.
- **Infinite Dragon Variants 74983** (SPID visual variety) and/or **Bellyaches
  New Dragon Species 5133** (13 non-replacing species) - variety without
  touching balance.
- **Sons of Akatosh 79742** - overhauls the dragon magical arsenal; overlaps
  the core's ambitions, so treat as an alternative flavor layer, not a stack
  with Dragon War until tested.
- **Dragon and Vampire Attacks Restored 176594** - restores the city
  dragon/vampire attack events SE removed; directly feeds "dragons as
  late-game threat" pacing.
- **Ominous Boss Weather 115893** - dragons drag dark weather in with them;
  cheap atmosphere.
- **Dragons Actually Fall Down 156824** + modernized models 122491 - death
  physics + visuals polish.
- Small fixes already in the small-bug-fixes list: Not Another Dragon
  Stalking Fix 88238, small dragon collision fix 42042.

## Interaction warnings gathered during the read

- Play as a Dragon x Dragon War needs its dedicated patch (118867) - only
  relevant if that novelty ever enters.
- The journey-stat Cataclysm ceiling and soul-mechanics mods (Dragon Souls to
  Perk Points family) are orthogonal spice; decide after the core.
- Delay Dragonborn Start 121301 (level-20 gate) is the bluntest tool for
  late-gaming the questline; your Vicn-style delayed-start philosophy already
  covers the elegant path.

## Recommendation shape (not a decision)

Dragon War + Dragons Use Thu'um + one variety mod is the modern default
package; KS DO2 only if you want MCM-dial-everything pacing over SKSE
behavior. Atmosphere pieces (176594, 115893) are cheap adds either way.
