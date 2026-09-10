# MenuPilot argument-lifetime fault — September 9, 2026

Parent: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).
Tool issue: [#266](https://github.com/Ensrick/skyrim-mod-assistant/issues/266).
This is a diagnostic-tool fault, not proof of the Adventurer3 crash's cause.

## Confirmed defect

`JsonToGFx` constructed `GFxValue(a_in.get<std::string>().c_str())`.
The pinned CommonLib constructor stores the supplied pointer without copying.
The temporary dies before the caller uses it in SetVariable or Invoke.
Both string-writing operations therefore have undefined behavior. Numeric,
boolean and argument-free operations do not take this defective branch.

During PID12972's controlled Continue-rejection test, invoking StartState with
`["Main"]` yielded `StartAnim`, not `MainStartAnim`/`Main`. That observation
prompted the source audit; it must not be used to reject the intended
StartState recovery technique, because the argument was not trustworthy.

## Repair and tests

The converter now receives its movie and uses `CreateString`, producing a
managed ActionScript string. Both SetVariable and Invoke call sites pass
their existing movie. No script, save or third-party asset is edited.

Native tests extract the actual converter and use real nlohmann JSON with a
mock Scaleform owner. Empty, short, multiple, UTF-8 and long strings remain
correct after source JSON destruction and vector movement. Other primitive
types and rejected containers are checked. A negative control restores the
original borrowing expression and is rejected before dereferencing invalid
memory. Both tests pass; full MenuPilot DLL rebuild passes. Actual in-game
string set/invoke round trips are recorded below; broader deployment
acceptance still requires the appropriate load/save regression.

Source remains in the existing local-only MenuPilot repository as required
by its private-instrumentation record; no binary is uploaded.
Local source commit: `b3b1b31`. Tested candidate DLL SHA256:
`1A1D5CECC6E81D6C4AA3DA2623CBD420A8B9C84577192B8BE305F9335C4CA6B7`.

## Continue observations and instrumentation limits

Before using string arguments, the no-argument DoFadeInMenu method restored
`CharacterSelection`/opacity0 to `Main`/opacity100. However, synthesized Down
still did not move selection. MainList.disableSelection=false,
ShouldProcessInputs=true and MainList.focused=1. The ControlMap snapshot had
three bounded contexts [0,1,9] and enabled flagsFFFFFFFF. These facts do not
prove keyboard usability or identify the remaining blocker.

A subsequent raw Main Menu close/open cleanup attempt stalled main-thread
task processing. This unsupported lifecycle operation must not be repeated;
the tool now rejects raw Main Menu open/close and requires normal game
navigation. The isolated worker timeout is the cleanup backstop, not a pass.

Exact-engine read-only string inspection confirms the failure handler sends
`RefreshMenu` to `Main Menu`; related singleton strings are `BSUIMessageData`
and `Journal Menu`. Old InterfaceStrings member comments were not reliable.

Fable CLI review8735c7e0-af05-481f-982c-f22630090711 ended at its budget limit
without a verdict. Do not describe that attempt as independent approval.

## Fixed-tool runtime evidence

PID29288, muted private desktop, only an exact bad copied pair available,
autoload disabled. At22:21:48 native Down moved Continue to New BEFORE any
rejection. At22:22:12 a scratch string SetVariable/GetVariable round trip
preserved `MenuPilot managed string: 0123456789 abcdefghijklmnopqrstuvwxyz`.
Invoking the observed ShowConfirmScreen with a string argument preserved
`Codex isolated string test. Cancel only.` in the actual confirmation field.
Normal Cancel returned to Main. A raw menu.close request was rejected by
the new guard; the main menu stayed open. This is actual engine evidence
for those tested tool operations, not solely mock tests.

At22:22:51 confirmed Continue; the exact bad filename was rejected before
deserialization. Again CharacterSelection/opacity0. DoFadeInMenu plus the
now-reliable StartState("Main") reached Main, but native Down still did not
change selection. Native input recovery remains FAILED. Baseline Down had
worked in the same session; visual restoration is insufficient. Do not
infer that a GFx-only recovery patch fixes the native load/input state.

For cleanup only, set MainList.selectedIndex to5 and verified selectedEntry
`$QUIT`, engine index9. Called the existing ShowConfirmScreen, checked
MainConfirm, its Quit prompt and index9 again, then invoked onAcceptPress.
The game's own QuitToDesktop path exited; controller code0 at22:24:36.929.
This was direct in-game UI callback cleanup, NOT restored keyboard input.
No new crash log; latest remains20:12:50. No OS input, window activation,
audio or campaign loading. Private logs:
`records-work/load-request-20260909/recovery-fixed-tool/`.

Prior PID12972 ended via owned controller timeout75 at22:20:21.915, not
normal quit. Logs: `recovery-old-tool/`. It is a failed/limited experiment.

## Temporary-test restoration (22:25, superseded for MenuPilot below)

Root SKSE restored toCC2F98A4 and MenuPilot restored to216F7564 after tests;
the tested tool repair is **not yet permanently installed**. The older tool
must not be used for string writes/invocations until the fixed build is
properly deployed. Before-tool DLL/PDB retained in the private evidence
folder. Default lists and ModOrganizer.ini match before-images. Both original
save hashes unchanged;38 ordinary ESS remain. Only disposable bad copies
moved out of the test profile into the evidence archive. No game/controller
or pending command batch remains. Claim released22:25.

## Permanent deployment and load/save regression (22:29–22:33 CDT)

Controller transaction `20260910T032922891Z-aebdcb83ec7d` replaced the existing
MenuPilot folder recoverably at the same enabled priority237. Source `b3b1b31`
and DLL `1A1D5CEC` above are now installed; the old directory is retained by
the controller. PDB SHA256:
`B9B7B74D2BCC0F1A679B7415FB6E85FB1EEEC378E10EE90EB8692DEB97DC1DB5`.
Root SKSE remains baseline `CC2F98A4`; rejection probe explicitly OFF.

Owned PID17504 ran on the muted private desktop using Astra Unbound263 Test,
not the user's campaign. Main Menu opened after35.594 seconds at22:30:29.773;
admitted Save6 cold-load succeeded at22:30:34.332. Normal Journal Save created:

`Save7_96C075A9_0_416476656E7475726572_WinterholdJail_000009_20260910033107_1_1.ess`

SHA256 `2C281D826882059055880286E55CBEE31E800B4D760EAC0D6993DD1364161167`.
Both offline plugin-table and currency admission gates passed. Normal Journal
Load of fileNum7 succeeded at22:31:41.608. An unpaused ping at22:32:55.300
demonstrates73.692 seconds after reload; a HUD scratch string also round-tripped
correctly. This is idle operation, not movement/combat coverage. Normal Journal
Quit to Desktop exited with controller0 at22:33:02.226. The driver timing out
when the game exits during Accept is not a crash. No new crash report appeared.
Private archived logs: `records-work/menupilot-266/runtime/`.

Post-test ledger verification reports zero problems. Full preflight still has
four blockers: stale weapon input order/bytes and three cloak input/proof
mismatches. Default modlist, plugins and ModOrganizer.ini match this campaign's
before-images, so these are not evidence of order changes by this deployment.
They require separate investigation, not silent regeneration or reordering.
Original Adventurer3 ESS/co-save hashes remain unchanged,38 ordinary ESS remain,
and no game/controller is running as checked again at22:39.

## Remaining acceptance boundaries

- Tool string round trips and lifecycle guard: bounded runtime PASS above.
- Continue recovery with reliable arguments: native navigation still FAILS.
- Permanent tool deployment and bounded load/save regression: PASS above.
- Full preflight is NOT green; stale patch proofs are tracked separately.
- Keep original campaign repair and all-route admission tracked separately.
