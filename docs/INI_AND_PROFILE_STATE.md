# INI and profile state - the assistant owns this, not the game

**User directive, 2026-09-01:** *"Since AI is managing MO2 I want you and Sol to
never forget a single thing like ini files."* Read this before touching the
profile, and before and after every launch.

The build was launched on 2026-08-31 22:00 with the game running at **1920x1080
windowed on a 4K display**, showing the Anniversary Edition upsell prompt as if
it were a first run. Nothing had been installed wrongly. Skyrim had simply
rewritten `SkyrimPrefs.ini` with its own defaults, because MO2 was not managing
the file.

## The rule

**INIs are build state. They are as load-bearing as plugins.txt, and nothing
outside MO2 may own them.**

- `profiles/Default/settings.txt` must contain `LocalSettings=true`. With it
  false, the game reads and writes
  `Documents\My Games\Skyrim Special Edition\*.ini`, where the vanilla launcher,
  a Steam validation, a game update, or the game's own first-run path can reset
  them silently. Fixed 2026-09-01; **verify it is still true after anything that
  rewrites the profile.**
- The profile's `skyrim.ini` and `skyrimprefs.ini` are the source of truth.
  Global copies in Documents are a fallback that should never be authoritative.
- `LocalSaves` stays **false** deliberately - saves are shared across profiles.

## What was lost and how it was recovered

`SkyrimPrefs.ini.base` in the Documents folder held the pre-reset configuration
and was the recovery source. `.base` and `.baked` files are MO2/BethINI
snapshots - **check for them before reconstructing settings by hand.** The
damaged file was preserved as `SkyrimPrefs.ini.bak.v20260901-firstrun-reset`.

The reset changed: resolution to 1920x1080, `bBorderless` to 0, `bUpsellOwned`
to 0, `bUseTAA` 1->0, `bIBLFEnable` 1->0, `bEnableImprovedSnow` 1->0, block
distances 60000/90000 -> 35000/70000, shadow distance 10000 -> 8000, and the
LOD fade multipliers. `Skyrim.ini` was untouched.

## Settings that are deliberate - never "correct" them

| file | key | value | why |
|---|---|---|---|
| SkyrimPrefs | `iSize W` / `iSize H` | 3840 / 2160 | the primary display is the 4K panel; the 1440p/144Hz screen is secondary |
| SkyrimPrefs | `bFull Screen` / `bBorderless` | 0 / 1 | user requires borderless |
| SkyrimPrefs | `bUpsellOwned` | 1 | suppresses the AE upsell prompt. 0 makes the game act like a first run |
| Skyrim | `fDefaultWorldFOV` | 120 | user directive |
| Skyrim | `fDefault1stPersonFOV` | 120 | user directive; third-person 90 and hands 80 live in FirstPersonFOV.ini |
| Skyrim | `[HAVOK] fMaxTime` | 0.0083 | 120 Hz desktop; the 60 fps cap was a refresh-rate problem, not a mod |
| Skyrim | `bEnableLogging` / `bEnableTrace` | 1 | Papyrus logging, needed for triage |
| SSEDisplayTweaks_Custom (Ensrick overlay) | `Fullscreen` / `Borderless` | false / true | mirrors the above at the DLL level |
| SSEDisplayTweaks_Custom | `LockCursor` | **false** | user directive 2026-09-01: "don't lock cursor while in menus and while loading" - it swallowed the Windows key and trapped the pointer. DT has no menus-only mode, so confinement is off entirely. Supersedes Sol's second-monitor rationale; if the invisible-cursor scroll returns, solve it another way. |

## Checks that must happen

These are no longer prose to remember. `py -3 audit/launch_session.py` runs the
whole sequence in order and refuses to move on when a step says no:

| step | tool | gate |
|---|---|---|
| before launch | `audit/preflight.py` | non-zero exit = **do not tell the user to launch** |
| user launches | (manual) or `audit/launch_verify.py` | verification launches are ASSISTANT-driven by user mandate 2026-09-01 ("you will do that part too"); pass = main menu <60s + save loaded |
| during the run | `audit/launch_watch.py` | names the live state every few seconds |
| after the run | `audit/launch_triage.py` | every plugin the SKSE loader refused |
| after a hang | `audit/threaddump.py` | what the process was actually doing |

**Before every launch** (all of this is `preflight.py`): `LocalSettings=true`;
profile INIs exist and are non-empty; the deliberate keys above still hold
their values; `install_mod --verify` and `verify_order` exit clean; the last
launch did not die mid-plugin-load or crash after init; no headless MO2 writer
is running (#103); Steam is not wedged with a phantom Running flag; the
game-side `%LOCALAPPDATA%\Skyrim Special Edition\Plugins.txt` still matches the
profile's active list.

**During every launch:** `launch_watch.py`. It separates loading from shader
compilation from a hang, which is the distinction that cost the evening of
2026-08-31 - the user sat through a 2.5-minute stall with no way to tell them
apart and had to ask. A hang gets a verdict, a per-thread CPU snapshot, and a
report in `records/launch-watch-<timestamp>.md`. It never kills the game.

**After every launch:** re-check the deliberate keys. The game writes INIs on
exit. If a value moved, something is not being managed - find out what before
correcting it. Then `launch_triage.py`.

The value comparison is numeric on purpose: an earlier preflight stripped
trailing zeros from both sides, which made `iSize W=384` compare equal to
`3840`. A resolution reset would have passed the gate that exists to catch it.

**After any Steam update, file validation, or vanilla-launcher run:** assume the
INIs were touched and verify all of it. The vanilla launcher rewrites
SkyrimPrefs unconditionally.

## The wider principle

The same failure shape has now cost this build four times in two days: plugin
enable markers stripped by LOOT sorts, SKSE DLLs staged one directory too high,
CBBE silently disabled, and now INIs reset by the game. **Every one was
invisible until something was observed to be broken.** State that the assistant
manages must be verified programmatically, not assumed - and where a gate exists
(`--verify`, `verify_order.py`), it must read clean for the right reasons, never
because nobody looked.

Related: #98 (this issue), #73, #100, #102, #132, #140, and
`docs/STANDARDS-DIGEST-2026-08-30.md` section 2.
