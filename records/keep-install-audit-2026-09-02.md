# Keep list vs installed mods - audit 2026-09-02

**Question (user):** is everything in Keeps installed (not necessarily active),
and is everything installed in Keeps?

Read-only pass over the live curator state (`nexus-local-curator/scripts/curator_state.py`,
journal keys overlaid on the compacted snapshot) against every directory under
`mo2-instances/skyrim-se/mods/`, resolving Nexus ids from
`records/installed-mods.json` plus each `meta.ini`
(`modid=` and the `<modid>-<fileid>` installation archive).

Note this uses **installed**, not the stricter *installed and enabled* that
`reconcile-installed-keeps.py` enforces; both numbers are given where they differ.

## Counts

| metric | value |
|---|---|
| installed mod directories | 238 |
| of those, enabled in `Default` | 214 |
| distinct Nexus ids among installed mods | 166 |
| distinct Nexus ids among **enabled** mods | 148 |
| live Keeps | 148 |
| live Skips | 4,551 |
| Keeps with nothing installed | **2** |
| installed Nexus ids with no Keep | **20** |
| installed directories with no Nexus id (ours) | 39 |
| installed directories missing from `modlist.txt` | 0 |

## 1. Keeps with nothing installed (2)

Both were added by the user mid-browse and never went through
approval -> audit -> install, so they are adoption intents, not stale Keeps.
Not cleared: clearing would erase the intent.

| id | mod | Keep added |
|---|---|---|
| 2357 | Enhanced Blood Textures (dDefinder) | 2026-09-01 01:14Z |
| 78772 | Daedric Shrines - All in One (Mandragorasprouts) | 2026-08-31 21:44Z |

Confirmed absent: no `mods/` directory, no ledger row, no `meta.ini` archive
match for either id.

Note both are also **stale** under the enabled-only definition, which is why
`reconcile-installed-keeps.py` proposes clearing them. Do not run that clear
until the adopt/drop call is made.

## 2. Installed with no Keep (20)

### 2a. Installed AND enabled - genuine Keep gaps (5, queued)

| id | mod | note |
|---|---|---|
| 26138 | Skyrim Landscape and Water Fixes | installed 2026-08-3x, 15 plugins |
| 49616 | Unofficial Skyrim Modder's Patch (USMP SE) | |
| 65070 | Misc Effects ENB Light | 3 directories share the id (base, Believable Weapons, 1.6.1 update) |
| 92948 | Media Keys Fix SKSE | installed 2026-09-01 for #149 |
| 175362 | Dyn FNIS AA functions | installed 2026-09-02 for #148 |

Queued as a guarded batch (compare-before-write against live state, no pending
batch clobbered) to `%TEMP%\nlc-relay\decisions-pending.json`; the relay was
started so the extension applies them on the next Nexus page load.

### 2b. Installed but deliberately disabled - Keep withheld on purpose (14)

Under the strict definition these are correctly Keep-less. Under
"installed, not necessarily active" they are the open question; each is
disabled for a recorded reason, so none was flipped automatically.

**Superseded by `Community Shaders AIO - 1.7.99 Source Build` (enabled).** The
AIO carries these features in-tree and is newer than the separate Nexus pages:

| id | mod |
|---|---|
| 86492 | Community Shaders (vendor row) |
| 112739 | CS Wetness Effects |
| 130375 | CS Screen Space GI |
| 139352 | CS Skylighting |
| 148123 | CS Terrain Variation |
| 156952 | CS Upscaling |
| 157076 | CS Terrain Blending |

**Parked pending a 1.7.104 rebuild or an author update** (`docs/HANDOFF-2026-08-27.md` park table):

| id | mod | park reason |
|---|---|---|
| 33261 | Bug Fixes SSE | closed source, author silent |
| 43532 | Scrambled Bugs | rebuild candidate |
| 63725 | EVLaS | closed source, author silent |
| 82558 | Skill Uncapper | rebuild candidate |
| 62001 | Immersive Equipment Displays | 1.7.104 rebuild queue |

**Superseded by an Ensrick overlay:**

| id | mod | replaced by |
|---|---|---|
| 98175 | High Poly 3D Wolf Skull - Werewolf Totem Replacer | `Ensrick - Scoped Werewolf Totem Skull 98175` (enabled) |

**Parked on an overlap check:**

| id | mod | reason |
|---|---|---|
| 126683 | Slightly Brighter Water Effects Fix | overlaps the selected waterfall/effects add-on (`docs/ECOSYSTEM-SURVEY-2026-08-30.md`) |

### 2c. Installed and explicitly rejected (1)

| id | mod | status |
|---|---|---|
| 138991 | Azurite III HDR | **skip** - disabled trial left on disk; correct as-is |

## 3. Installed directories with no Nexus id (39)

All ours or harness-only, so no Keep can exist for them: 27 `Ensrick - *`
overlays and patches, 6 `* Native Overlay - Ensrick` rebuilds (ConsoleUtilSSE,
JContainers, PapyrusUtil, Proteus x2, RaceMenu), `Community Shaders AIO -
1.7.99 Source Build`, `Light Placer - Ensrick 1.7.104`, `QuickLoot IE - Ensrick
1.7.99`, `Pandora Output - Ensrick`, `LaunchProbe`, `MenuPilot`, `Period
Underlayers - SPID`, `Water for ENB - Generated Conflict Patch`.

The rebuilt native overlays sit above their vendor rows, which are installed
with their own ids and already Keep, so the upstream pages are represented.

## Verdict

- Keeps -> installed: **2 gaps**, both the user's own un-actioned adoptions.
- Installed -> Keeps: **5 real gaps** (queued), 14 deliberate omissions, 1 correct Skip.
- No installed directory is missing from `modlist.txt`; no Keep points at a mod
  that was removed.

Reproducer: `nexus-local-curator/scripts/reconcile-installed-keeps.py`
(enabled-based plan, read-only without `--queue`); the installed-based variant
used here is recorded in this file's counts.
