# Architecture and design

This document describes the safety boundary and intended runtime architecture
of Bounded Encounters. It is normative for the first test candidate: a code
change that violates an invariant here needs an explicit design review and a
corresponding documentation change.

## Problem definition

Skyrim does not expose one universal "encounter size" field. A dungeon or
wilderness encounter normally contains several authored actor references, and
each leveled-actor reference resolves independently. Bounded Encounters treats
each eligible authored reference as one source and applies a bounded
probabilistic expansion to that source.

For a category curve, the uncapped expected extra count per source is:

```text
progress = max(0, playerLevel - baselineLevel)
expectedExtras = progress * ratePerLevel
```

The value is clamped by `maxMultiplier - 1` and `maxExtrasPerSource`. Its whole
part is guaranteed; its fractional part is compared against one deterministic
per-source threshold. Cell and population caps are applied afterward. This is
linear growth, not compounding growth.

The source actor remains untouched. If the source resolved from a leveled actor
list, that original list is submitted to the engine again so a companion can
resolve to a different valid bandit, draugr, or creature. The initial safety
candidate rejects fixed resolved actors because cloning one without its
authored leveled selection is not yet an approved source policy. Generated
actors are tagged in runtime state and can never become sources.

## Components

```text
SKSE load and runtime gate
          |
          v
configuration ---> classifier ---> per-cell source snapshot
                                         |
                                         v
                              deterministic spawn planner
                                         |
                                         v
                           engine spawn/placement adapter
                                         |
                    +--------------------+------------------+
                    v                                       v
              runtime registry                    structured log/audit
                    |
                    v
         lifecycle ownership and save-safety verification
```

### Plugin entry and runtime gate

The entry point initializes logging, validates the exact runtime, loads the
configuration, and installs its event sinks. It must return a load failure or
leave spawning disabled if any required safety mechanism cannot be established.
Any proposed save hook is a separate runtime-specific design change, not an
assumed part of initialization. User-visible modal dialogs are prohibited.

### Configuration and pure spawn model

Configuration parsing and spawn mathematics are engine-independent. The same
code is linked into the plugin, command-line simulator, and unit-test binary.
This keeps balance calculations auditable without launching Skyrim. The
shipping configuration sets `observeOnly: true`, which allows engine-side
classification and planning evidence without actor creation.

### Classifier

The classifier turns a live authored actor reference into either an exclusion
reason or one category plus a spawnable source form. Exclusion is evaluated
before category selection and always wins. Classification should use engine
flags, keywords, form types, extra data, and explicit configuration; display
names and partial editor-ID text are not authoritative.

The default fail-closed exclusions include dragons, unique/essential/protected
or non-respawning actor bases, persistent references, quest aliases,
location-reference bosses, summons, commanded actors, teammates, dead actors,
non-hostiles, script-bound actors, fixed resolved sources, denied plugins, and
all plugin-generated actors. Authored source references are admitted only when
their defining and effective providers, resolved actor base, and every form in
the reachable leveled-template graph appear in the non-empty
`allowedSourcePlugins` list; the default list contains only official masters.

The alpha treats `ActorTypeAnimal`, `ActorTypeCreature`, `ActorTypeDragon`,
`GiantRace`, `MammothRace`, and `LocRefTypeBoss` as mandatory vanilla forms. If
any lookup fails, the manager disables encounter scaling instead of silently
placing an actor into a broader category.

### Encounter manager

The manager listens for fully loaded cells and performs all engine-facing work
on Skyrim's main thread. Its responsibilities are to:

1. reject cells or game states that are not safe to process;
2. take a stable snapshot of eligible authored sources;
3. count existing hostiles and select the correct interior/exterior caps;
4. invoke the pure planner once for the snapshot;
5. in observe-only mode, log the plan and stop before creation;
6. otherwise spawn from the captured source form, offset placement, and snap to
   usable navigation when the engine permits it;
7. register every generated actor before it can be observed by later work; and
8. emit one bounded, structured summary rather than per-frame log noise.

Scanning a container while mutating it is prohibited. The source snapshot and
spawn pass are separate phases. The alpha processes a cell FormID at most once
per plugin session; reset-aware reprocessing is not yet claimed. Candidates are
snapshotted by stable source key, then the planner admits them by a stable
seed-derived rank with source key as a tie-breaker. Engine iteration order
therefore cannot decide which source wins a saturated cap.

### Runtime registry and save-safety evidence

The registry owns handles for generated actors and processed source/cell keys.
It is the authority used by recursion prevention, lifecycle auditing, and any
future narrowly owned cleanup. The plugin never modifies or deletes an authored
actor. See
[Spawn lifecycle and save safety](save-lifecycle.md).

### Simulator

`BoundedEncounters.Simulate.exe` consumes the shipping JSON and reports expected
and sampled populations at representative player levels. It performs no game
or mod-manager discovery and writes no game files.

## Determinism and identity

The planner mixes the configured seed and stable source identity once to obtain
a unit-interval threshold. Player level changes the expected fraction compared
with that same threshold; it is not mixed into a fresh roll. This makes each
source's uncapped result monotonic as the player gains levels. Input order does
not change an individual threshold or the final admitted set. Category and
global caps use the deterministic seed-derived rank so saturated admission
remains reproducible without permanently favoring low FormIDs.

Determinism prevents save/reload reroll farming and makes a log reproducible.
Changing player level can cross the existing threshold as intended; changing
the seed, configuration, load order, source FormID, or underlying leveled list
can also change the encounter.

## Release invariants and acceptance requirements

These are required for release; they are not claims that an untested alpha has
already satisfied every item. In particular, generated-reference
non-serialization remains pending foreground save inspection.

1. Generated actors are never multiplication sources.
2. Exclusion wins over category membership and all allow behavior.
3. No authored reference is edited, moved, deleted, or made persistent.
4. A generated actor must not be serialized into the save.
5. Missing/invalid configuration and unsupported runtimes disable spawning.
6. Every addition path has per-source, per-category, per-cell, total-hostile,
   attached-area active-owned, and per-evaluation bounds.
7. Engine-facing operations execute on Skyrim's main thread.
8. No code path displays a modal dialog or intentionally steals focus.
9. The build and packaging tools never deploy into a game or mod-manager path.

## Deliberate non-goals for the first test candidate

- changing actor stats, equipment, combat style, or leveled-list contents;
- expanding fixed resolved sources or mod-authored references by default;
- multiplying dragons, named bosses, quest actors, followers, or summons;
- persisting generated actors across saves;
- editing cells or navigation meshes;
- claiming compatibility with an untested runtime;
- providing an ESP/ESL, MCM, Papyrus scripts, or an in-game updater.

## Failure policy

Configuration errors, unresolved required forms, failed hooks, unsupported
runtimes, invalid source forms, placement failures, and exhausted caps all fail
closed for the affected operation. The plugin records the reason in its log and
continues only where doing so cannot compromise save safety.
