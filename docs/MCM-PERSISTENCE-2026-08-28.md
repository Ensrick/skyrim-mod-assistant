# MCM persistence and distribution — 2026-08-28

Trackers: [configuration #39](https://github.com/Ensrick/skyrim-mod-assistant/issues/39) and [persistence #40](https://github.com/Ensrick/skyrim-mod-assistant/issues/40)

## Direct answer

SkyUI provides the Mod Configuration Menu interface and registration system; it
does not turn every mod's settings into a universal cross-save configuration.
Traditional MCM values usually live in plug-in global variables or Papyrus
state and are therefore stored in the save. A new game normally starts from the
mod's defaults, not from the MCM choices made in another character's save.

An MO2 profile can isolate its own saves and INIs, but that does not make
save-local MCM state portable. Copying or backing up only the MO2 profile is not
enough for every menu.

## Persistence classes

| Class | Persistence | Packaging treatment |
|---|---|---|
| Traditional SkyUI/Papyrus MCM | Usually save-local | Record and replay approved choices on a new game. Do not assume settings cross characters. |
| MCM Helper mod settings | File-backed under `Data/MCM/Settings` | Ship reviewed default/user INIs when permissions allow; keep generated user state in a dedicated MO2 output mod. |
| Native mod INI/JSON/XML | File-backed and normally cross-save | Version-control our overrides or a source template; never copy secrets or machine paths. |
| Mod-specific export/profile | Defined by that mod | Prefer the native export when it is complete and stable; document what it omits. |
| MCM Recorder recipe | Replays menu interactions | Store reviewed recordings as reproducible configuration artifacts and test them after every relevant menu update. |

MCM Helper's current source reads defaults from `Data/MCM/Config/<mod>/settings.ini`
and writes user choices to `Data/MCM/Settings/<mod>.ini`. Keybind registrations
are also file-backed under `Data/MCM/Settings/keybinds.json`. This applies only
to mods that actually use MCM Helper's setting API.

MCM Recorder writes readable recipes beneath `Data/McmRecorder`; under MO2,
new recordings appear in Overwrite unless that output is redirected into a
named mod. It can reproduce traditional menu choices on a new game, but it is
an interaction replay rather than a direct export of arbitrary script state.

## Current profile observations

The enabled profile contains traditional MCM scripts for QuickLoot IE,
Wyrmstooth, The New Gentleman, XPMSSE, Nether's Follower Framework, Proteus,
Skyrim Unbound Reborn, and VioLens. This is not yet a claim that every menu has
registered successfully.

- QuickLoot IE reads plug-in global variables. Changes to those globals are
  save-local unless captured by a separate replay/default patch.
- Proteus and Skyrim Unbound Reborn use traditional SkyUI MCM scripts and must
  be treated as save-local until an explicit export path is proved.
- VioLens ships human-readable `.VLCK` JSON profiles for killmove selection,
  but those files do not prove that every general MCM option is exported. No
  user-generated VioLens file is currently present in MO2 Overwrite.
- Community Shaders, SSE Display Tweaks, FSMP, and several native frameworks
  have important file-backed settings outside SkyUI MCM. These belong in the
  configuration manifest even though they are not MCM state.
- MCM Helper is installed but disabled, so no MCM Helper-dependent persistence
  workflow is currently active.

## Proposed reproducible workflow

1. Restore and validate a source-built MCM Helper for Skyrim 1.7.104.
2. Create a dedicated disabled-by-default MO2 mod named `Modpack - Generated
   Settings`; direct configuration output there instead of leaving files in
   Overwrite.
3. Build a machine-readable inventory classifying every adopted setting as
   save-local, MCM Helper file-backed, native file-backed, or mod-exported.
4. Configure one disposable new game, record traditional MCM actions, and
   separate user preferences from mandatory experience settings.
5. Replay onto a second clean save and compare every menu and generated file.
6. Redact machine paths and exclude saves before publication. Ship only our own
   configuration artifacts and files whose permissions allow redistribution.
7. Re-run the replay whenever a mod version changes its menu labels, pages,
   order, or setting semantics.

## Acceptance criteria

- A new disposable game reaches the approved configuration without manual
  menu work beyond starting the supported replay/import.
- A save/reload preserves the same values.
- A second MO2 profile can reproduce them without copying a character save.
- MCM Helper and native file-backed values are captured separately from MCM
  Recorder recipes.
- The process produces no modal background dialogs and leaves no unexplained
  files in Overwrite.
