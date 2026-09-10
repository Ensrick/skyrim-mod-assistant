# Native rejected-load menu recovery — September 9, 2026

Parent: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262), OPEN.
This establishes a bounded main-menu cancellation path. It is not an installed
admission policy, campaign repair, or load/save/gameplay certification.

## Exact native evidence

Examined the installed SkyrimSE1.7.104 executable, MD5
`113faeb71fd8f62b26d0c8627299ab40`, and its format5 Address Library. Dense
offsets start at byte96; IDs401263/215773/215779/215698 resolve MenuControls
singleton/vtable, DirectionHandler vtable, and MainMenu vtable respectively.
Read-only process snapshots verify all three vtables against the pinned engine.
No memory allocation, suspension, flag patching, or OS input was used.

- MenuControls ProcessEvent at95F020 checks byte+83, handler registration and
  remap state. DirectionHandler ProcessButton at960E50 checks byte+29.
- MainMenu ProcessMessage at959F90 dispatches message6 (Scaleform input) via
  table95A8AC to95A671. That path discards input if global byte3258201 is set,
  or MainMenu+68 equals1. Thus an apparently restored Flash movie can still
  have its input discarded by native code.
- For kUpdate, comparison95A4FE matches InterfaceStrings+258. Live reads in
  PID15848 confirm this string is `CancelLoading`, while+250 is `RefreshMenu`.
- The CancelLoading branch clears MainMenu+6D and calls95C780. That function
  invokes the existing `FadeInMenu` movie method and clears global3258201.
  This is the engine's own cancellation handling, not a hand-written memory
  reset or raw menu close/reopen.

The local-only MenuPilot source commit `9be3f587da50227b107c57d9bdfd542df5ad22ce`
adds diagnostic `menu.cancel-load`: only on runtime1.7.104, with Main Menu
open and Loading Menu closed, queue `CancelLoading` as kUpdate. It does not
infer that every load is safe to cancel. The operator must establish a completed
rejection first. Build passes;16 extracted-production guard/message cases and
the existing managed-string/negative-control tests pass. These unit tests do
not substitute for the engine evidence below.

Temporary tested MenuPilot DLL SHA256:
`02FF25E70876C72982EC2BB1FB108610F4650FEE47E7069DF07B71BAF6D6E9ED`.
Temporary SKSE rejection candidate remains57DEFE36/source7c8ee72.

## Failed configuration control: PID35320

The first new test was MISCONFIGURED: the runner supplied the extensionless
rejection name, although the probe README requires `.ess`. The actual name
included `.ess`, so the log truthfully reports reject=0, target result=0,
kPreLoadGame and failed kPostLoadGame. This is NOT a successful admission test.
It demonstrates the importance of asserting `engine_target_entered=0`, not
inferring interception from a failed load or lack of crash. The runner was
corrected; no production comparator change was required.

Native flags changed from0/0 to1/1 (MainMenu+6D/global3258201). The correctly
invoked visual-only restore left both set. Earlier two calls used `path` instead
of required `method` and were rejected by MenuPilot; their snapshots are not
evidence of successful invocation. Normal direct UI callback cleanup exited
with controller0 at22:51:56.110 CDT. No new crash. Original save untouched.
Private evidence: `records-work/load-request-20260909/native-input/`.

## Corrected rejection and native cancellation: PID15848

Muted private desktop; dedicated Astra Load262 Input Retry profile contains
only an exact disposable copy of Adventurer3 Autosave3. Autoload disabled.
Main Menu reached at22:55:40.349,36.854 seconds after probe attachment.
Baseline native Down selects New; Up returns to Continue.

Both Continue confirmations were inspected before Accept. Both attempts log
the full `.ess` name, reject=1 and `engine_target_entered=0`; neither emits
kPreLoadGame/kPostLoadGame. State progression is repeatable:

| Observation (CDT) | MainMenu+6D | Global3258201 | Result |
| --- | ---: | ---: | --- |
|22:56:01 baseline|0|0|Normal native menu navigation|
|22:56:55 rejected Continue|1|1|CharacterSelection, stranded|
|22:57:11 after CancelLoading|0|0|Main; native Down selects New|
|22:57:54 second rejection|1|1|CharacterSelection again|
|22:58:07 second cancellation|0|0|Main; native Down selects New again|

MenuControls+83/remap82 and DirectionHandler+29 stayed0; handler registration
stayed1, handler count9, and MainMenu+68 stayed0. Snapshot gate bytes were
stable across each bounded read; snapshots are asynchronous, not global atomic
state assertions. The exact engine branch plus the repeatable native-message
intervention explains the navigation failure more specifically than a GFx fix.

After the second recovery, only ordinary engine Down/Accept events selected
Quit, displayed the exact Quit to Desktop confirmation, and exited. No direct
GFx Quit callback was needed. Controller exit0 at22:58:41.753 CDT. No new crash
log; newest remains the actual20:12:50 report. MenuPilot's quit-batch timeout
is expected when the process exits, not evidence of a crash.
Private evidence: `records-work/load-request-20260909/native-input-retry/`.

## Restoration and scope

Both wrappers restored root SKSE `CC2F98A4`. Second wrapper also restored the
permanently installed, string-repaired MenuPilot `1A1D5CEC`; experimental
`menu.cancel-load` is NOT installed. Both copied save pairs were moved out of
test profiles into their evidence directories after exit, not deleted. No game,
controller or pending command batch remains; claim released. Default modlist,
plugins and ModOrganizer.ini match before-images. Original ESS/co-save hashes:

- ESS: `ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`
- Co-save: `E708EC7CE1B7CC384A4E676E2A52A41DCC668BA235D5FD0FD30571AF9E27A1CF`

All38 ordinary ESS remain. No removed mods restored, saves cleaned, or campaign
migration selected. No game assets/binaries uploaded; private instrumentation
source remains local per its existing distribution exclusion.

## Next required work

1. Integrate this native cancellation into a reviewed automatic admission
   mechanism with correct event ordering; it must not cancel an active load.
2. Parse actual requested-save plugin/currency identity, fail safely with useful
   in-game feedback, and cover Continue/Load/quickload/other relevant routes.
3. Prove rejected-save preservation from both main menu and running gameplay,
   then admitted load/new-save/reload and sustained gameplay. Two menu cycles
   do not prove those requirements.
4. Continue the original Adventurer3 MCM failure diagnosis; the campaign
   recovery-versus-new-character decision remains the user's. Rejection is not
   recovery, and the existing normal-load admission gap is not yet deployed shut.
5. Reconcile the independently stale weapon/cloak proofs (#253): identical
   active plugin bytes/set but FuzzBeed Resources/Thanedom swapped at115/116;
   four added CLLF folders, common mod order unchanged. Config/DLL/INI/BSA
   fingerprint components unchanged. No silent order reset/regeneration done.
