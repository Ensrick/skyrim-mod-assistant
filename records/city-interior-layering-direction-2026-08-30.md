# City and interior layering direction

Status: **leading architecture, not installation authority.** The apparent
three-mod recommendation is three layers, not permission to stack three blanket
overhauls over the same records.

Tree compatibility now targets full Nature of the Wild Lands 3.14. Nordic Cut
is not installed; references to a NotWL/Nordic composition in the research
below are superseded.

## The three layers

1. [Grand Solitude - The Walls of High King Erling](https://www.nexusmods.com/skyrimspecialedition/mods/157506)
   is the inside-city anchor. It is a genuine capital expansion rather than a
   decoration pass: roughly 20 buildings, more than 50 scheduled NPCs, and
   major Castle Dour and Temple of the Divines rebuilding.
2. [Solitude Docks Updated](https://www.nexusmods.com/skyrimspecialedition/mods/33777)
   is the exterior harbor layer. It adds the missing working docks settlement
   below/outside the city rather than competing for the same inside-city design
   role.
3. The modern [Snazzy interior family](https://www.nexusmods.com/skyrimspecialedition/mods/147618)
   is a **per-cell catalog**, not a third global Solitude winner. It offers
   light-flagged AIO or individual-location plugins, mostly interactive clutter,
   occlusion work, and a very active
   [patch collection](https://www.nexusmods.com/skyrimspecialedition/mods/91604).

## Do they fit together?

Grand Solitude and Solitude Docks Updated have an explicit current patch in the
[Grand Solitude Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/157450),
so this is an evidenced combination rather than a guessed spatial merge.

An exact archive audit corrected an important naming ambiguity. `Snazzy
Solitude AIO 2.3` covers only six houses (Bryling, Erikur, Evette San, Jala,
Addvar, and Vittoria Vici); it does not contain Castle Dour or the Temple and it
shares no placed-reference or NAVM override with Grand's rebuilt interiors.
`Snazzy Furniture and Clutter Overhaul 3` is a different BOS-driven furniture
layer, and its current patch hub has exact Grand, Docks, and Snazzy Solitude
patches. Grand's own legacy SFCO patch is not the current SFCO3 route.

The professional rule is therefore:

- one city-layout winner;
- one exterior/docks winner with an exact combination patch; and
- at most one redesign winner for each interior cell.

Selected Snazzy house modules can fill cells that Grand does not redesign; the
AIO is technically the same six-house set, while separated modules provide
better testing and rollback granularity.
Selected JK or Ryn interiors can still be used where they win a deliberate
cell-by-cell comparison, but neither JK's inside-city Solitude layer nor a
blanket interior AIO should be added by default.

The completed exact matrix is
[`solitude-city-interior-cell-matrix-2026-08-30.md`](solitude-city-interior-cell-matrix-2026-08-30.md).
It covers Grand, Docks, Snazzy/SFCO3, Lux/Lux Orbis, Water for ENB, AI
Overhaul, 3DNPC, Nature of the Wild Lands/Nordic Cut, eFPS, and selective
JK/Ryn modules. DynDOLOD generation comes only after this geometry and patch
set is frozen.
