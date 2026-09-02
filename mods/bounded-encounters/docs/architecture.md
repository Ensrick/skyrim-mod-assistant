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
resolve independently as a valid bandit, draugr, or creature. The reroll can
legitimately select the same entry as the authored actor; it is not an exact
clone operation, but visual uniqueness is not guaranteed. After creation, the
runtime requires the actor to retain the exact authored leveled-source identity
used for creation or rolls it back. The initial safety candidate rejects fixed
resolved actors because cloning one without its authored leveled selection is
not yet an approved source policy. Generated actors are tagged in runtime state
and can never become sources.

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

Configuration parsing, spawn mathematics, and the saturating population-cap
calculation are engine-independent. The same code is linked into the plugin,
command-line simulator, and unit-test binary. This prevents the simulator's
reported capacity from drifting away from the live runtime decision.
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

Active creation also requires an authored source with no ExtraData that imposes
stateful reference behavior. The classifier rejects enable-state parents,
encounter zones, linked/activation references, patrol data, locations and all
location-reference types, horse/multibound associations, alias provenance,
missing-reference recovery data, attachment references, scene/interaction
state, forced targets, and open/close activation references. Each rejection has
a deterministic `stateful-reference-*` reason, and the normal cell summary
reports their aggregate count even when per-source debug logging is disabled.

This gate is intentionally about conditions imposed on the source. Reverse
child indexes (`ExtraEnableStateChildren`, `ExtraLinkedRefChildren`,
`ExtraActivateRefChildren`, and `ExtraAttachRefChildren`) describe other
references that point to the source; they are not copied and are not themselves
a rejection reason. Package/process ExtraData is likewise neither copied nor
rejected: a created actor receives fresh engine-owned runtime package and
process state. These exclusions from the gate do not prove active lifecycle or
save safety; active behavior remains subject to the disposable-profile in-game
acceptance matrix.

The alpha treats `ActorTypeAnimal`, `ActorTypeCreature`, `ActorTypeDragon`,
`GiantRace`, `MammothRace`, and the `Skyrim.esm` boss location-reference type
`000130F7` (editor ID `Boss`) as mandatory vanilla forms. The boss form's local
ID, defining file, editor ID, and editor-ID lookup identity are all verified.
If any lookup fails or mismatches, the manager disables encounter scaling
instead of silently placing an actor into a broader category.

Respawn eligibility is taken from `TESActorBase::Respawns()`. ACHR header bit
30 is not treated as an affirmative respawn flag: xEdit labels it `No Respawn`
for generic references and does not expose it in the ACHR-specific flags.

### Encounter manager

The manager listens for fully loaded cells and performs all engine-facing work
on Skyrim's main thread. Its responsibilities are to:

1. reject cells or game states that are not safe to process;
2. take a stable snapshot of eligible authored sources;
3. count existing hostiles and select the correct interior/exterior caps;
4. invoke the pure planner once for the snapshot;
5. in observe-only mode, log the plan and stop before creation;
6. otherwise spawn from the captured source form, offset placement, and accept
   a nearest-navmesh snap only inside the configured distance and same
   cell/worldspace postconditions;
7. roll back every unaccepted created reference, and register a generated actor
   before treating it as a successful spawn; and
8. emit one bounded, structured summary rather than per-frame log noise.

Scanning a container while mutating it is prohibited. The source snapshot and
spawn pass are separate phases. The alpha processes a cell FormID at most once
per plugin session; reset-aware reprocessing is not yet claimed. Candidates are
snapshotted by stable source key, then the planner admits them by a stable
seed-derived rank with source key as a tie-breaker. Engine iteration order
therefore cannot decide which source wins a saturated cap.

### Runtime registry and save-safety evidence

The registry owns handles for committed generated actors and processed cell
IDs. It supports attached-area cap accounting, lifecycle auditing, and any
future narrowly owned cleanup. Unconditional dynamic-reference rejection
prevents generated actors from becoming sources; the registry's `IsSpawned`
query is currently unused. The plugin never modifies or deletes an authored
actor. See
[Spawn lifecycle and save safety](save-lifecycle.md).

### Simulator

`BoundedEncounters.Simulate.exe` consumes the shipping JSON and reports exact
uncapped expectations, deterministic fractional-capacity projections, and
sampled populations at representative player levels. The capped projection is
not a statistical expectation after Bernoulli outcomes. The simulator performs
no game or mod-manager discovery and writes no game files.

## Determinism and identity

The planner mixes the configured seed and stable source identity once to obtain
a unit-interval threshold. Player level changes the expected fraction compared
with that same threshold; it is not mixed into a fresh roll. This makes each
source's uncapped result monotonic as the player gains levels. Input order does
not change an individual threshold or the final admitted set. Category and
global caps use a separately domain-separated deterministic seed-derived rank,
so saturated admission remains reproducible without permanently favoring low
FormIDs or correlating cap priority with a fractional success roll.

For identical planner inputs, the planned count and admission set are
deterministic and make the planning portion of a log reproducible. A successful
game load starts a new runtime generation, and Skyrim's engine-controlled
leveled-list resolution can select a different base even when the plan is the
same. The alpha therefore does not claim to prevent save/reload reroll farming.
Changing player level can cross the existing threshold as intended; changing
the seed, configuration, load order, source FormID, or underlying leveled list
can also change the plan.

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
