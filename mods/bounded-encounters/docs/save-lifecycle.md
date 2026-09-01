# Spawn lifecycle and save safety

Population scaling is useful only if it does not leave generated references in
the save. This document defines the required ownership model and the acceptance
evidence for the first test candidate.

The shipping alpha configuration has `observeOnly: true` and therefore creates
no actors. The lifecycle risks below apply when an in-game tester explicitly
sets `observeOnly` to `false` on a disposable profile. Observe-only evidence is
a prerequisite, not a substitute, for that active save-integrity matrix.

## Ownership boundary

Bounded Encounters owns only actors that it creates. A local rollback guard
takes immediate responsibility for a newly created reference. The runtime
registry records committed ownership only after all creation checks succeed.
Authored actors, actors made by other plugins, and references whose ownership
is ambiguous are never cleaned up or filtered by this plugin.

Each generated actor must satisfy all of these properties:

- it is marked temporary;
- its handle is present in the runtime registry;
- it is rejected by the source classifier;
- save inspection demonstrates that it is not serialized; and
- any cleanup can target it without touching its authored source.

The current alpha implements the first three properties. Non-serialization and
cleanup behavior remain acceptance tests, not established guarantees.

Before active planning, authored sources with stateful-reference ExtraData are
rejected. The gate covers enable parents, encounter/location associations,
linked/activation/attachment and patrol relationships, aliases and missing-ID
recovery records, horse/multibound associations, and
scene/interaction/forced-target state. The spawn path does not copy any of
those records from its source.
Reverse enable-state, linked, activation, and attachment child indexes are
intentionally not rejected because they record other references pointing at the
source rather than an authored condition imposed on it. Package/process
ExtraData is also not copied or used as a rejection reason; the engine supplies
fresh runtime package and process state to a created actor.

That source-selection gate narrows the active test surface; it does not establish
that generated actors are absent from saves or safe across every transition.
Active save behavior remains an in-game gate and must pass the disposable-save
matrix below before promotion.

Immediately after creation, the alpha applies the temporary flag and reads the
record flags back. A failed verification is disabled and marked for deletion
instead of entering the registry. This narrows risk but does not replace save
inspection.

## State model

```text
eligible authored source
        |
        v
planned companion --creation failure--> discarded plan/logged reason
        |
        v
created + registered + temporary
        |
        +---- cell unload/reset ----> engine cleanup under verification
        |
        +---- new game/load/revert --> alpha registry reset; cleanup unproven
        |
        +---- save requested -------> temporary behavior under inspection
```

Registration must happen before later scans can observe the actor. A generated
actor that cannot be registered safely is treated as a failed spawn and cleaned
up through the narrowest engine-safe path. The active test path holds each new
reference in a rollback guard until temporary-state verification, bounded
placement, post-resolution classification, and strongly exception-safe
registry insertion all succeed.

## Save boundary: current status

The engine may attempt to serialize a dynamic actor despite its temporary flag.
The current alpha deliberately does not intercept Character save virtuals. It
marks owned actors temporary and keeps an in-memory handle registry, but that is
not evidence that the actors stay out of every save path.

This makes generated-reference persistence an explicit release blocker. The
first in-game test must inspect saves made with live and dead generated actors.
If references are serialized, the build is rejected; marking it "experimental"
does not make a contaminated save acceptable.

Direct Character virtual-table interception is not a default remedy. An
incorrect slot, signature, or runtime relocation can crash or damage saves. A
future hook requires a separate design review, an exact runtime gate, an owned
live-handle predicate (never a dynamic FormID range), delegation for every
non-owned actor, and the full save matrix. If a safe non-persistence boundary
cannot be demonstrated, use curated static reinforcement placements or reject
the runtime backend.

## Cell and game transitions

### Fully loaded cell

The manager processes a stable actor snapshot at most once for each cell FormID
in the current plugin session. Existing generated actors do not qualify as
sources. Repeated fully loaded notifications must not compound the population.
The alpha does not attempt to recognize a same-session cell reset as a new
generation.

### Cell unload or reset

Generated actors are allowed to leave combat and be reclaimed by the engine.
The current alpha does not yet retire stale registry entries on cell unload.
That omission must be profiled during the endurance test. Any future explicit
deletion must be limited to a currently resolved, plugin-owned actor and use an
engine-safe main-thread operation.

### Save

The intended result is that no generated actor is serialized. This is unproven
for the alpha and must be checked directly. Saving does not intentionally mutate
or clear the registry, because gameplay continues after a save.

### Pre-load, load, new game, and revert

The current alpha preserves ownership and processed-cell state while a load is
pending and if that load fails. It clears both only after a successful load or
when a new game/session begins. It does not explicitly clean up live owned
actors first. Losing ownership before cleanup is a known gap: a candidate may
proceed only on disposable saves while tests determine whether the engine
reliably reclaims those temporary actors. A production design must either clean
up resolved owned handles safely before clearing state or prove that the
transition always makes them unreachable. Old handles and FormIDs must never
leak across saves.

### Shutdown

Skyrim does not provide a general-purpose unload contract for active SKSE DLLs.
The plugin must not depend on hot-unloading. Process exit reclaims in-memory
state.

## Deterministic regeneration

Generated actors are intended to be session objects, not saved world state.
That claim remains conditional on save inspection. A future reset-aware design
may generate companions again from reset authored sources; the alpha does not
reprocess a cell FormID during the same plugin session. Stable input preserves
the per-source fractional threshold, while the underlying leveled list remains
free to resolve according to Skyrim's own rules. Consequently, a stable plan
does not guarantee the same resolved actor base after a successful reload.

The plugin must not create a new threshold merely because the player quick-saved
and reloaded the same active encounter. This is tested separately from any
future legitimate cell-reset regeneration.

## Known risk areas

- actor death or dismemberment while a save starts;
- a generated actor entering combat across a cell boundary;
- another mod adding a generated actor to an alias or persistent collection;
- rapid save/load during a queued cell event;
- handle reuse after revert;
- any future save hook relying on Character virtual-table layout;
- spawning from a leveled form whose result has unusual scripted lifecycle;
- uninstalling from a save created by an experimental build that failed to
  suppress serialization.

The initial package is therefore a prerelease for disposable test saves. A
promotion to stable requires the save-integrity suite in the test plan.

## Save-integrity acceptance criteria

1. A save made with live generated enemies loads without warnings or crashes.
2. The generated references are absent from save inspection and do not reappear
   as persisted actors after reload.
3. Source actors retain their original FormIDs, position, base, inventory, and
   persistence state.
4. Repeated save/load cycles do not increase actor count.
5. Revert between two saves does not carry registry ownership across saves.
6. A failed/unsupported runtime gate produces no generated actors.
7. Removing the plugin after saving and quitting does not produce missing-form
   references attributable to Bounded Encounters on a disposable test save.

No stable release should be published if any criterion is unverified.
