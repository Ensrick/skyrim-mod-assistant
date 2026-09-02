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

### The file that actually holds the flag: `settings.ini`, not `settings.txt`

**Trap found 2026-09-01 (#143 root cause).** MO2 2.5.2 reads the profile's
`settings.ini` for `LocalSettings` and `LocalSaves`
(`modorganizer/src/profile.cpp:94`, `Profile::localSettingsEnabled()` at
`:882`). The `LocalSettings=true` written on 2026-08-31 went into a
`settings.txt` beside it - a file nothing loads - and for a full day
`profiles/Default/settings.ini` kept saying `LocalSettings=false`. Every gate
that "verified" the flag read the stray. The profile was unmanaged the whole
time, which is why the 2026-09-01 session ran at 1920x1080 with launcher
defaults while the profile INIs were correct.

What the real flag does: with `LocalSettings=true` in `settings.ini`, MO2's
game plugin maps `Documents\My Games\Skyrim Special Edition\Skyrim.ini`,
`SkyrimPrefs.ini` and `SkyrimCustom.ini` onto the profile copies through
usvfs for every launch MO2 performs - the GUI and `headless-run` alike. The
game then reads and writes the profile files; the Documents copies are only
what a launch that bypasses MO2 (the vanilla launcher, a Steam validation)
sees. `launch_skyrim.ps1` still copies the profile INIs over the Documents
pair before every launch and prints which mechanism applies (`settings.ini
LocalSettings=...` line, then `identical` / `DIFFERED` per file), so drift is
attributable to one of the two.

Rules that follow:

- `preflight.py::check_profile_owns_inis` reads `settings.ini`. A
  `settings.txt` in the profile is reported as a stray until it is removed.
- The profile must carry all three INIs (`skyrim.ini`, `skyrimprefs.ini`,
  `skyrimcustom.ini`); a missing one makes the MO2 GUI show a modal "missing
  profile-specific INI" dialog on launch.
- Never "verify" a flag by grepping a file whose name you assumed. Find the
  reader in the source first.

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
| Skyrim | `[HAVOK] fMaxTime` | 0.0083 | 120 Hz desktop fallback only: SSE Display Tweaks Official overrides it per frame (SSEDisplayTweaks.log `[HAVOK] (DYNAMIC) fMaxTime=0.00416667-0.0166667`), so Havok is already decoupled from the render rate |
| Skyrim | `[HAVOK] fMoveLimitMass` | 0 | STAGED 2026-09-01 clutter triage, needs in-game test: engine default 95 is the mass ceiling the player's character controller shoves, so every plate and cup gets knocked around; 0 turns the player push off (NPCs unaffected). Original at `skyrim.ini.bak.v20260901-pre-movelimitmass` |
| Skyrim | `bEnableLogging` / `bEnableTrace` | 1 | Papyrus logging, needed for triage |
| Skyrim | `fPoissonRadiusScale` | 8.0 | #151: user reports shadow edges too sharp. CS 1.8 Utility shadow-mask kernel radius; engine default 4.0, BethINI range 0-8. Skyrim.ini key, NOT SkyrimPrefs. Backup `skyrim.ini.bak.v20260901-preshadowfilter` |
| SSEDisplayTweaks_Custom (Ensrick overlay) | `Fullscreen` / `Borderless` | false / true | mirrors the above at the DLL level |
| SSEDisplayTweaks_Custom | `[Render] FramerateLimit` / `[HAVOK] MaximumFramerate` | 119 / 0 | STAGED 2026-09-01 (#150), needs the morning launch: STEP's DT rule for a 120 Hz panel (limit 1 fps under the refresh; 117 if the LG runs VRR) and 0 so DT derives the Havok ceiling from the limit (borderless ignores the VSync refresh). Receipt: SSEDisplayTweaks.log `(DYNAMIC) fMaxTime=0.00840336-0.0166667 ... (Max FPS = 119)`. Original at `SSEDisplayTweaks_Custom.ini.bak.v20260901-pre-120hz` |
| SSEDisplayTweaks_Custom | `LockCursor` | **true** | flipped twice 2026-09-01, settled by #149: DT confines with `ClipCursor` whenever the window has focus and releases on focus loss; all-or-nothing, no gameplay-only mode, and no external utility does better (same Win32 call). The Windows key is NOT eaten by this setting: the game's own DirectInput flags (`DISCL_EXCLUSIVE\|DISCL_FOREGROUND\|DISCL_NOWINKEY`) do that, and only Media Keys Fix SKSE frees it - INSTALLED 2026-09-01 (Nexus 92948 file 792882 v1.0.2, gate PASS, PE 2026-08-21) with the overlay mod `Ensrick - Media Keys Fix Configuration` (`DisableWindowsKey=false`) above it; UNVERIFIED until the morning launch. Keep true; do not flip again. |
| MediaKeysFix.ini (Ensrick overlay) | `DisableWindowsKey` | false | #149: frees the Windows key; the vendor default true re-applies NOWINKEY. Overlay mod must stay above `Media Keys Fix` in the mod order. Side effects accepted: Alt+F4 closes the game, media keys work |

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
