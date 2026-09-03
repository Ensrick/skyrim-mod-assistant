# Selective encounter-population review — 2026-08-28

Tracker: [GitHub issue #43](https://github.com/Ensrick/skyrim-mod-assistant/issues/43)

## Desired rule

Increase ordinary humanoid and undead combatants—bandits, soldiers, guards in
hostile military camps, draugr, skeletons, goblins, and deliberately approved
equivalents—without doubling wildlife, giants, dragons, bosses, unique actors,
summons, quest actors, or every creature in the game.

This is a category-selection problem, not just a numeric multiplier.

## Dynamic Enemy Spawns SKSE 3.1 audit

The current candidate was checked through the Nexus API and its separately
published source archive was downloaded for inspection only. It was not
installed.

| Fact | Evidence |
|---|---|
| Nexus mod/file | Mod 178556, source file 786583, version 3.1, uploaded 2026-08-07 |
| Source archive | `178556-786583.zip`, 5,819,606 bytes |
| SHA-256 | `840B8C11E1A1158A0FC4E32E0DD8F4DFA9B913983AD29BA1C1CF94514747766B` |
| Published compatibility | 1.5.97, 1.6.640, and 1.6.1170; no 1.7.104 claim |
| Permission statement | Nexus author instruction says "Do whatever you want with the mod" |
| Source completeness | 13 C++ headers/sources and one PDB; no CMake/vcpkg/project file, README, or license file |

### Strengths

- Native rather than Papyrus-driven spawning.
- Copies actors already resolved in the active world, which should preserve
  their current equipment/distribution and reduce static compatibility patches.
- Attempts to keep spawned actors out of saves through character save hooks and
  cleanup on cell transition.
- Avoids unique/non-respawning enemies by default, batches creation, caps
  interiors, and has configurable follower scaling.
- Version 3.1 improves editor-ID resolution by building a reverse form cache.

### Blocking limitations

- Version 3.1 exposes a case-insensitive partial-match blacklist, not a positive
  allowlist. Excluding every animal, monster, boss, summon, and quest actor from
  every current and future worldspace is brittle and fails the requested rule.
- Default settings blacklist only mammoths and dragon priests; an unmodified
  installation would still duplicate wolves, bears, giants, and other hostile
  creatures.
- The source itself still declares internal version `1.0.0` despite the Nexus
  package being 3.1, so binary/source provenance cannot be validated by that
  version field.
- The source package is not independently buildable as published. Its build
  graph, dependency revisions, compiler flags, and exact SKSE Menu Framework
  headers are absent.
- It installs two `RE::Character` virtual-function hooks for save suppression.
  Those hooks are high-risk on an unclaimed runtime and require a 1.7.104-aware
  CommonLib/address-library build plus explicit save-integrity tests.
- Spawned corpses are deliberately non-lootable by default because depositing
  items into them can make them persist in a save. Enabling looting adds a user
  behavior constraint that is easy to violate.
- Exterior grouping and caps are approximate; the author documents that nearby
  camps can be conflated and that large actors can spawn on top of one another.

## Decision

Hold the upstream binary. The underlying approach is promising, but version 3.1
does not meet the category-selection or runtime acceptance gates.

If we proceed, use the author's broad modification permission to create a
clearly attributed, source-complete derivative or an original equivalent with:

1. An allowlist-first policy based on reviewed races, keywords, factions, base
   records, and explicit worldspace/mod rules.
2. Deny precedence for unique, essential/protected, boss, summoned, scripted,
   quest-alias, non-respawning, large-creature, wildlife, and user-excluded
   actors.
3. A dry-run audit that reports every eligible source actor before gameplay.
4. Runtime 1.7.104 support built from pinned dependencies, with hook-layout and
   save serialization tests.
5. Separate interior/exterior caps, deterministic randomness, structured logs,
   and no modal error path.
6. Long-run tests covering cell unload/reload, save/load, fast travel, follower
   scaling, furniture placement, corpse cleanup, and removal of the mod.

Until that exists, a smaller record-based patch for selected camps/dungeons is
safer but less adaptive. It must still avoid indiscriminate doubling and must be
regenerated as worldspace mods enter the load order.
