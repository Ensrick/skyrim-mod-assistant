# Finite native mouse-look experiment: not accepted

September10, 2026. Parent #262; automation acceptance #267. Normal installed
MenuPilot `1A1D5CEC`, SKSE `F7435705`, currency `4DAB6D30` restored/unchanged.

## Question and result

Could a finite MouseMoveEvent sent through the existing input event source,
without a new frame hook, rotate the camera enough to navigate the obstructed
test fixture? **The tested recipe did not.** Do not promote it or rerun the
same recipe as a supposed gameplay test.

Actual Fable5.1 CLI session `86a3337d-1c79-431b-a9fe-9bfa06d3cadc` completed a
second read-only review in18 turns/94.407 seconds. Root independently checked
the exact executable, PC control map, allocation helpers and dispatch code.
Fable's stronger suggestion that no reliable positive observation is possible
without a frame hook was not adopted: appropriately controlled observations
can establish change; the unverified issue here is event timing/delivery.
No external read-only observer called a game virtual function.

## Source evidence and candidate safeguards

- Exact engine MD5 `113faeb71fd8f62b26d0c8627299ab40` inspected offline.
- LookHandler vtable RVA1935150 slot5 points to7B3270. The36-byte native
  consumer reads signed deltas from event+28/+2C and writes look-vector+8/+C.
  It does not itself establish that the camera applies them later.
- MouseMoveEvent vtable1A23BC0 has targetsCFA600/7B4470/7B4830. Those targets
  and the delta-consumer bytes are checked before candidate dispatch.
- PlayerControls input sink7AD900 resets movement AND look vectors at entry,
  then traverses input. This makes dispatch/update ordering a concrete next
  investigation; it is not alone proof of why this packet had no visible effect.
- Base game's PC control map confirms mouse axis0xA for Look, and keyboard
  Strafe Right0x20. No guessed rebound key was used to justify acceptance.

Candidate source is preserved separately as
`patches/menupilot/experimental-look267.patch`, local source commit5e59613 based
on9be3f58 (the earlier CancelLoading diagnostic, not installed sourceb3b1b31).
Native candidate DLL SHA256:
`F7101EFBDCA02EB8438DAFBA3CB7D167FDB484F6509C3FDC7E87F1486F62489F`.
PDB `F3F0B4D7A1E0F1C586783AFEC93762BB9B996C2C77DF1AF548D8F4ADE3929382`.
Final source's test CHECK diagnostic change does not alter the native DLL.

Compile-time option defaults OFF, with a second explicit process opt-in. One
packet per command, integer components within+/-512, not both zero; native
runtime/layout checks; unpaused loaded-game/look-enabled guards; two-second
expiry checked before execution; panic check; lifetime cap64 allocations.
Events/string references are retained until process exit rather than destroyed
through an unaudited virtual. No input queue mutation, direct camera/position
write, new gameplay mod, collision bypass or campaign migration.

The15-case standalone contract test initially caught mixed signed/unsigned
JSON comparison at uint64 maximum. Explicit signedness handling fixes that;
tests pass after recompilation with non-aborting CHECKs. ON and OFF builds both
compile; only the ON binary contains the input.look command string. The local
cache is now OFF. These are bounded source/build checks, not gameplay proof.
Runtime expiry/cap exhaustion were not exercised; they remain unverified.

## Live evidence

Both runs used the muted private desktop, protected crash logger, copied
post-USSEP fresh-character Save5, normal SKSE/currency, and temporary pinned
MenuPilot DLL/PDB backups with finally restoration. No normal profile promotion.

1. `Astra Look267 Candidate 20260910`, controller23328/game32244,
   10:34:05.094–10:35:33.062 CDT, normal main-menu Quit, exit0. The launcher
   cleared the inherited experimental variable, so input.look refused before
   dispatch. No save was loaded. This exposed the missing explicit harness
   switch; it was not a camera test.
2. `Astra Look267 Enabled 20260910`, controller35192/game14752,
   10:35:54.136–10:40:49.966 CDT, normal Journal Quit, exit0. Explicit switch
   allowed the candidate while preserving normal launcher defaults. Main-menu
   look refused because gameplay was paused. Continue loaded the copied save;
   boolean and uint64-max deltas refused. One dx160/dy0 packet at10:37:15.041
   dispatched, retained count1. Normal Save6 and Journal reload succeeded.

Save6:
`Save6_FFCEF459_0_416476656E7475726572_WhiterunWorld_000007_20260910153718_1_1`
ESS SHA256 `E1AF492D24EAED83A67C27E86F1D57AB8F66A3E5E38B075DC661EB0C208DBA27`.
Offline plugin/currency admission passed before reload. A pinned read-only
parser inspected the27-byte INITIAL prefix of original fixture and Save6:
both yaw6.1846457, pitch/roll0. The new preview visibly still faces the tree.
The guarded live observer still reports cell1A276/world1A26F, approximately
(24826.994,-4226.012,-2996.45). This is no positive camera/travel result.
Prefix-only parsing does not validate the whole ACHR body or save health.

Reload succeeded10:39:24.444. Final unpaused ping10:40:43.083 is78.639 seconds
later. No protected crash file appeared. Original campaign, fixture, Default,
root DLL/PDB and all41 currency overlay files passed preservation checks.
MenuPilot DLL/PDB and normal logger restored; no owned game/controller/Fable
job remains; claim released. Raw reports, saved previews and candidate binary
remain private under `records-work/look267-{candidate,enabled}-20260910/`.

## Remaining work

The next input change must address the real input/update phase or another
observed native gate, not send more identical finite packets and call it a fix.
A verified native-frame hook would be a separate candidate requiring review.
No such hook has been implemented by this experiment. #267 travel/combat and
#262 overall crash goal remain open. Original Adventurer3 recovery still needs
the user's approval for a restoration/migration strategy; no decision made.
