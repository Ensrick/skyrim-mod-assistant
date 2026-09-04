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

The driver tags every batch and, on timeout or interruption before the DLL
claims it, atomically quarantines its exact bytes. It never leaves its own
`commands.jsonl` armed for a later launch. A pre-existing file is somebody
else's command and is refused, not overwritten.

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

## The Creations store: what two piloted sessions established (2026-09-01)

Records: `records/menupilot-cc-discovery-2026-09-01.log` (first session),
`records/menupilot-farming-attempt-2026-09-01.md` (launches 1+2 below, with
the pilot/probe logs under `records/tool-runs/*20260901-launch[12]*`).

**Verified, main-menu context (`Interface/StartMenu.swf`):**

- `_root.MenuHolder.Menu_mc.MainList.EntriesA[i].text` holds the entries:
  `$CONTINUE $NEW $LOAD $CREATIONS $CREDITS $QUIT` (6 entries; CREATIONS is
  list position 3, engine index 5). Read the selection back with
  `MainList.iSelectedIndex` / `MainList.selectedEntry.text` (use `EntriesA.3.text`
  dotted-index syntax for `gfx.get`; `[3]` fails in GetVariable).
- `input.tap` works end to end: `Down`=208, `Up`=200, `Accept`=28 (Enter),
  `Cancel`=15 (Tab) move/act exactly like the keyboard. ALWAYS read
  `selectedEntry.text` back before `Accept`: the selection does NOT reliably
  reset to 0 after a sub-screen closes (it did once, not the second time; a
  blind Down x3 landed on QUIT).
- Accept on CREATIONS = engine flow: `Login Menu` opens (silent Bethesda.net
  login via the linked Steam account, ~0.3s, no modal), then `Marketplace
  Menu` opens and Login closes. `Cancel` (Tab) closes the store cleanly.
- Quit: select `$QUIT`, Accept -> `strCurrentState="MainConfirm"`,
  `ConfirmPanel_mc.textField.text="Quit to desktop? ..."`, Accept again ->
  clean process exit (no crash log). This is the exit to use after any
  download; never kill the process while the store may be writing.

**The store itself is a NATIVE UI, unreadable and undrivable by this pilot:**

- `Marketplace Menu` is the Creations store when the ENGINE opens it, but its
  movie is a placeholder: `menu.query` says `Interface/CreditsMenu.swf` and the
  dump is credits-only (`CodeObj.closeMenu/getScrollSpeed/requestCredits`).
  The visible store is drawn natively (`MarketplaceMenu::InputHandler`,
  `BSMarketplaceImage`, `MarketplaceTextures.bsa`,
  `MarketplaceCategoryConfiguration.json` in the exe; no CEF/webview module
  loaded). No Scaleform member reflects its tiles, tabs, options list or
  confirm prompts. The documented "press O -> Download all owned Creation Club
  Creations" path exists (Steam guide 3107226125) but pressing O produced no
  Scaleform menu and no `MessageBoxMenu`; the same options list holds Delete
  All / Disable All with native sure-prompts (`CreationsSurePromptDeleteAll`
  etc.), so blind Accepts there are forbidden.
- `bUpsellOwned=0` (SkyrimPrefs, the first-run state that re-acquired owned
  content on 08-31) does NOT trigger a download by itself: 10 minutes at the
  main menu plus two store visits, `DLCPanel.warningText="Loading Add-Ons"`
  and `LoadingContentMessage._visible=true` the whole time, no file written.
  The 08-31 re-download therefore needed something the reset INI carried
  beyond that key (probably `uiMarketplaceUpdatedHash=0`; untested) or a
  human click. Restore the key to 1 afterwards (preflight FAILs on 0).
- `DownloadAll`, `CreationClub`, `OpenMarketplace`, `LoadDLC`,
  `DoLoadDLCPlugins`, `Sky10DLCPressed` are the main menu's FxDelegate
  callbacks (exe string table, next to `OpenCreditsMenu`). They are NOT
  members of `_root.CodeObj` / `Menu_mc.codeObj` (those 13 members are the
  login handlers only) so they cannot be hit with `gfx.invoke` on a script
  object. **`gfx.invoke` of `_global.flash.external.ExternalInterface.call`
  ["OpenCreditsMenu"] CRASHES the game**: AV at `SkyrimSE.exe+117AB19`
  (null string compare) under `MenuPilot.dll` main.cpp:570 `view->Invoke`
  (`crash-2026-09-01-18-43-46.log`, archived in `records/tool-runs/`). The
  delegate dispatch expects the GameDelegate marshalling, not a bare Invoke.
  A future pilot op would have to call the registered `FxDelegateHandler`
  natively (`RE::FxDelegate` lookup by name) rather than go through the movie.
- Never cold-kShow `Marketplace Menu` from in-game context (first session:
  engine worker AV ~3s later, `crash-2026-09-01-17-29-31.log`).

**Bottom line for the Farming (`ccvsvsse004`) BSA:** not re-downloadable
headlessly with the current pilot. Manual path (~30s): main menu -> CREATIONS
-> press O -> "Download all owned Creation Club Creations" -> confirm; expect
`Data\ccvsvsse004-beafarmer.bsa` = 18,261,078 bytes (ContentCatalog.txt
FilesSize 18,746,124 minus the 485,046-byte esl). Then quit via the menu.

## The console: readable and writable, not executable (2026-09-01, #51 guard receipt attempt)

Record: `records/tool-runs/menupilot-20260901-guard-console-probe.log`, in-game
after a `launch_verify --leave-running` PASS.

- `Console` is always on the stack (`menus_on_stack=2` at rest); `menu.open`
  queues a no-op. The movie is `Interface/Console.swf`; the instance is
  `_global.Console.ConsoleInstance` (== `_root.instance1.instance2`, unnamed
  children) with text fields `CommandEntry`, `CommandHistory` (the scrollback,
  `.text`/`.length`, 16384-char buffer) and `CurrentSelection` (`'' RefID:
  (000888ae) | BaseID: (000226ba)` style). `gfx.get`/`gfx.set` on
  `CommandEntry.text` and reading `CommandHistory.text` work.
- Nothing executes it. `ExecuteCommand` in the swf is the **GameDelegate
  callback name** inside `onKeyDown`, not an ActionScript function:
  `gfx.invoke` of `_global.Console.ConsoleInstance.ExecuteCommand` returns
  ok=0/undefined (no crash). The class statics on `_global.Console` are
  `Show`, `Hide`, `AddHistory`, `SetCurrentSelection`, `ClearHistory`,
  `NextCommand`, `PreviousCommand`, `Minimize`, `SetTextSize`, ... - no
  execute. `input.tap Accept` (28) does not reach the console's Key listener
  (`Shown` stays false even after `gfx.invoke _global.Console.Show`, which
  returns ok=1 but does not flip it). A console receipt therefore needs a new
  pilot op that calls the engine's `ExecuteCommand` delegate natively
  (`RE::Console`/`ConsoleUtil`-style script-command dispatch), same conclusion
  as the Creations `FxDelegate` note above.
- Caveat: the user had taken the controls in that same session (TweenMenu /
  InventoryMenu at 23:43, possibly the console at 23:45), and the agent's
  `launch_verify.kill` at 23:45 ended it before the heads-up arrived. The
  `gfx.invoke` results are unaffected, but re-check the `Show` / `input.tap`
  observations in a session nobody else is driving.

**Operational notes**: `menupilot.log` truncates per launch - archive it
before relaunching. One in-flight `commands.jsonl` at a time; a file left
unclaimed when the game dies executes on the NEXT launch - `menupilot.py
status` warns, delete it if stale. Command ids continue across batches within
one launch. Agent shells reset their cwd between calls: invoke the driver by
absolute path (`py -3 C:\Users\danjo\source\repos\skyrim-mod-assistant\audit\menupilot.py`),
a relative path silently sends nothing. Reach the main menu with
`launch_verify.py --no-autoload --leave-running` (verdict `MENU-ONLY`, never a
PASS; the record says so).

## Disposable fresh-character gate (#227, V2)

`py -3 audit/fresh_verify.py` is the automated New Game stage. It wraps the
existing primitives; no new DLL command was needed:

1. Preflight and the instance claim must be clean. With no game or MO2 process
   alive, an old `commands.jsonl` is renamed to a stamped stale archive so it
   cannot execute on this launch.
2. `Default` is copied, never edited, to a unique `Codex Fresh FV-...` profile.
   Its source saves are excluded, `LocalSettings=true`, `LocalSaves=true`, and
   audio is muted. The profile is never reused.
3. `launch_verify` starts that profile on a separate hidden Windows desktop,
   with no INI sync, no Steam restart, no autoload, and a refuse-instead-of-kill
   guard for any process that appeared during the preflight/launch gap.
4. The pilot reads `MainList.selectedEntry.text`, sends one `Down` at a time,
   and reads again. It accepts only when the immediately preceding value is
   exactly `$NEW`; no fixed input count is used.
5. If `strCurrentState` becomes `MainConfirm`, its text is read twice and only
   the observed shipped prompt `Start a New Game?` is accepted. Any other
   state, confirmation, or MessageBox fails closed.
6. PASS requires LaunchProbe `kNewGame` followed by `MENU_OPEN name="RaceSex
   Menu"`, the current Skyrim Unbound-to-RaceMenu readiness boundary. Cleanup
   calls the existing human-presence-aware kill; detection leaves the process
   and its disposable profile intact and exits 88.

Safe checks, neither of which launches the game or changes a profile:

```powershell
py -3 audit/fresh_verify.py --selftest
py -3 audit/fresh_verify.py --dry-run
```

This is deliberately **V2 only**. MenuPilot still has no audited primitive for
finishing RaceMenu with a supplied character name or saving under a supplied
name. Therefore this stage does not claim V3 feature probes or V4 named-save /
reload. The unique identity names the isolated run/profile and its evidence;
it is not yet typed into RaceMenu. Add an engine-level name/save primitive (or
prove a fully readable menu route) before extending the harness; never use an
old "clean" save as a substitute.
