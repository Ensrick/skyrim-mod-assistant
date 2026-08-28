# Wolf spawning and wildlife design — 2026-08-28

Tracker: [GitHub issue #42](https://github.com/Ensrick/skyrim-mod-assistant/issues/42)

## Vanilla record audit

The installed `Skyrim.esm` does not make ordinary wolves disappear at a high
player level.

`LCharWolf` (`0B83C2`) contains three level-1 entries: ordinary wolf, red wolf,
and another ordinary-wolf weighting entry. Its flags are
`CalculateFromAllLevelsLessThanOrEqualPlayer` and
`CalculateForEachItemInCount`, with zero chance of no spawn. Once the list is
eligible, a high-level player still qualifies for all three level-1 entries.

The special lists are similarly persistent:

| Leveled list | Entries | Consequence |
|---|---|---|
| `LCharWolf` (`0B83C2`) | Wolf level 1, red wolf level 1, wolf level 1 | Ordinary wilderness wolf lists remain eligible at every higher level. |
| `DunCragslaneLCharPitWolf` (`0E160C`) | Wolf level 1, ice wolf level 5; calculate from all lower levels | Ordinary wolves remain in the pool after ice wolves become eligible. |
| `DunDarkshadeCopseLCharWolf` (`023BC0`) | Wolf level 1 | This dungeon list always resolves to the ordinary wolf. |

This answers only vanilla list behavior. A placed reference can still fail to
return if its reference/base does not respawn or its encounter zone never
resets. By default, uncleared cells reset after 10 in-game days and cleared
cells after 30; creatures normally respawn when the cell resets. Encounter-zone
level itself remains locked after first visit.

The same audit must be repeated against Bruma, Wyrmstooth, Beyond Reach, and
every other adopted worldspace. Their authors can use different fixed actors,
leveled lists, scripts, factions, or no-respawn references.

## Behavior audit

Vanilla ordinary wolf (`EncWolf`) and red wolf (`EncWolfRed`) records are level
2, respawning, auto-calculated, and marked `Unaggressive`; ice wolf is level 6
and `VeryAggressive`. Ordinary bears are also marked `Unaggressive`. Both
families share Creature, Predator, and Spriggan Predator factions, but each has
its own species faction.

Therefore, making wolves "behave like bears" is not safely solved by changing
one aggression enum. Detection distance, warning/combat behavior, faction
relationships, encounter placement, and any race/behavior data must be tested.
At minimum, ice-wolf aggression is a concrete difference; ordinary wolves need
an in-game approach/retreat test before changing records that already claim to
be unaggressive.

## Preferred implementation

Create a load-order-aware generated compatibility patch instead of adopting a
broad animal overhaul:

1. Discover wolf actors, races, and leveled lists by explicit form links plus a
   reviewed include/exclude manifest—not editor-ID substring alone.
2. Preserve quest, summoned, spirit, dead, companion, scripted, and unique
   wolves unless deliberately approved.
3. Normalize only the selected wildlife actors' aggression/faction behavior and
   preserve each worldspace mod's visuals, stats, placement, and scripts.
4. Keep wolves in their existing leveled lists; do not replace the wildlife
   population with a single global list.
5. Test warning distance, pack assistance, flee/return behavior, follower and
   summon interactions, hunting, cell reset, and save/reload in every adopted
   worldspace.

The hostile-population deficit should be solved separately through issue #43's
selective humanoid/undead spawning. Wolves should not remain routine enemies
merely to keep the wilderness combat count high.
