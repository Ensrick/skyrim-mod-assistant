# MenuPilot - headless in-game menu control

SKSE plugin (source: `C:\Users\danjo\source\repos\skyrim-tools-source\MenuPilot`,
installed as MO2 mod `MenuPilot`) that lets the assistant drive the game's own
menus with no window focus, no OS input, and no clicking. File-based, same
shape as the VT2 console bridge: the assistant writes a command file, the
plugin consumes it exactly once and appends timestamped results to a log.

## Paths (fixed, real, outside the VFS - LaunchProbe rationale)

- Commands: `Documents\My Games\Skyrim Special Edition\SKSE\MenuPilot\commands.jsonl`
- Log: `...\SKSE\MenuPilot\menupilot.log` (truncated per launch, flushed per line)
- Consumed batches are archived beside them as `commands-<n>-<stamp>-done.jsonl`.

Driver: `py -3 audit/menupilot.py send '<json>' ...` | `tail` | `status` | `panic`.

## Safety contract

- Plugin is **inert until a commands.jsonl appears** (poll starts at kInputLoaded,
  250ms interval, `SKYRIM_MENU_PILOT_POLL_MS` overrides).
- Consume-exactly-once: the file is **renamed before a byte is read**.
- Every command echoes to the log **before** execution (`COMMAND id=...`).
- `{"op":"panic"}` halts everything (only `ping`/`resume`/`panic` still run) and
  kHides every menu the pilot opened.
- Log-only, no popups: own-DLL MessageBox IAT stubs, LaunchProbe pattern.

## Commands (one JSON object per line)

| op | args | effect |
|---|---|---|
| `ping` | - | runtime version, UI alive, paused, stack size |
| `wait` | `ms` (0-60000) | pause between commands in a batch |
| `menu.list` | - | `STACK` lines (open stack, bottom-up) + one `MENU` line per registered menu with open/has_view |
| `menu.open` / `menu.close` | `menu` | UIMessageQueue kShow / kHide; confirm via a later `menu.query` or `menu.list` |
| `menu.query` | `menu` | open?, movie view?, and the menu's `swf=` file URL |
| `menu.msg` | `menu`, `event` | BSUIMessageData kUserEvent string to the menu |
| `gfx.get` / `gfx.set` | `menu`, `path`, (`value`) | GetVariable / SetVariable on the menu's movie |
| `gfx.invoke` | `menu`, `method`, `args`:[primitives] | GFxMovieView::Invoke; logs return type+value |
| `gfx.dump` | `menu`, `path`(=`_root`), `depth`(0-4), `max`(<=2000) | recursive VisitMembers -> `MEMBER` lines; the discovery tool |
| `input.tap` | `event` (user-event name), `code`, `device`(=keyboard), `hold_ms`(=80) | engine-layer ButtonEvent press+release via BSInputDeviceManager SendEvent - reaches MenuControls exactly like real input, focus-independent |
| `panic` / `resume` | - | halt / re-arm |

Every result line carries `id=` matching its `COMMAND` echo. `RESULT ok=0`
carries `reason=`. `menu.open`/`close` results mean *queued*, not done - the
UI thread applies them next frame.

## What the Creations store turned out to expose (2026-09-01 session)

Full trace: `records/menupilot-cc-discovery-2026-09-01.log`.

- clib-ng declares `RE::CreationClubMenu` ("Creation Club Menu",
  `creationclub.swf`, an IMenu + **GFxFunctionHandler** whose download flow is
  native `Call` dispatch, not Papyrus) - but **this 1.7.104 runtime does not
  register that name at all**. `menu.list` shows 39 menus; the store-adjacent
  names are `Mod Manager Menu` (untested; the likely Creations UI) and
  `Marketplace Menu`.
- **`Marketplace Menu` is a red herring**: kShow loads
  `Interface/CreditsMenu.swf`; `_root.CodeObj` = closeMenu / getScrollSpeed /
  requestCredits only.
- **Never cold-kShow store surfaces from in-game context.** Doing so ran the
  movie without its native backing and an engine worker AV'd ~3s later
  (SkyrimSE.exe+059F446, crash-2026-09-01-17-29-31.log; not in
  MenuPilot.dll). Store surfaces must be driven from the MAIN MENU, ideally by
  input-navigating the engine's own CREATIONS entry so the engine performs its
  prefetch, then `gfx.dump`-ing what appears.
- Verified this session: command bridge round-trip, `menu.list/open/close/
  query`, `gfx.dump` (all in-game); `input.tap` implemented but not yet
  exercised - a person took over the desktop mid-session and pilot driving
  stopped.
- The Farming (`ccvsvsse004`) re-download was therefore NOT executed yet.
  Next session, at the main menu: `menu.query`/`gfx.dump` on
  `Mod Manager Menu`, else `input.tap` down the Main Menu list to CREATIONS +
  Accept, then dump the screen that opens for its item list and download
  method. Least-bad manual fallback: main menu -> CREATIONS -> owned list ->
  Farming -> download.

**Operational notes**: menupilot.log truncates per launch - archive it before
relaunching. One in-flight commands.jsonl at a time; a file left unclaimed
when the game dies executes on the NEXT launch - `menupilot.py status` warns,
delete it if stale.
