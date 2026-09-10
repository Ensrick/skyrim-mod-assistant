# Early load cancellation investigation — September 9, 2026

Related: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).
This is a diagnostic experiment, **not** a deployed compatibility policy or
repair of the Adventurer3 campaign. The public issue stays open.

## Why a new boundary

The mid-load SKSE hook cannot safely be treated as a veto merely by returning
false: the original engine function's rejection path has additional cleanup
and state writes. Earlier exact-engine inspection identified the queued-load
call at RVA625FF5 to627DE0. That target itself permits an immediate false
return for a null stream. Its caller invokes627B20 on false and retains stream
destruction/housekeeping ownership. Unlike the later hook, an intercepted
request has not yet entered627DE0 or emitted SKSE pre/post-load messages.

This does not prove session preservation. Fable 5.1's independent read-only
review, session92cab6dd-ff89-4acb-8a42-ae21c423a9cc, confirmed the six-argument
ABI but identified627B20 as UI notification rather than world-state rollback.
Its warnings drove the healthy-save-first test sequence below.

The engine also has multiple request entry routes. Hooking only the
`Load(filename)` wrapper622F30 would miss paths; most-recent loading623080
uses the save service directly. The queued boundary is a candidate common
point, not yet proof of exhaustive route coverage.

## Diagnostic implementation

Candidate DLL SHA256:
`57DEFE36D604033621F51EAE00D26223EBE612731BFCAD2361866509C3FEE57B`.
Based on the repaired SKSE source73d2f7b, with a separate opt-in experiment.
Diagnostic source is published as
[7c8ee72](https://github.com/Ensrick/skse64/commit/7c8ee7284f1913f47267c14f25d6858bd1e39524).

- No hook installation unless `SKSE_AUTOMATION_LOAD_REQUEST_PROBE=1`.
- Exact call bytes checked before installation on the audited executable
  (MD5 `113faeb71fd8f62b26d0c8627299ab40`).
- An optional exact basename in `SKSE_AUTOMATION_REJECT_LOAD` rejects only
  that name, case-insensitively; unreadable names also reject when configured.
- Name reads use bounded ReadProcessMemory calls. The field's availability at
  this earlier boundary was a hypothesis until the observation run proved it
  for these actual paths.
- Six ABI arguments preserved: this, stream**, UInt32, UInt8, UInt8, UInt32.
  The compiled incoming/outgoing stack slots were independently inspected.
- Production wrapper/declarations tested in524,288 mock-engine cases;
  prior load-hook2,048-case regression still passes. These do not test engine
  cancellation, save integrity or the pointer layout.
- No ESS/co-save rewriting, missing-mod restoration or automatic migration.
  No compatibility allowlist, plugin-table parser or currency checkpoint
  validation exists in this diagnostic hook.

## Runtime evidence

All runs are isolated muted private-desktop sessions; no OS input or user
desktop focus. Default lists and original saves are not test outputs.

### Observation: PID30028

Cold-loaded admitted Save4; normal Journal > Load of the same Save4 also
passed. Both entered the new boundary with readable names and
`arg1=0 arg2=0 arg3=0 arg4=D0000010`. The stream name is therefore available
before627DE0 on these routes. Manual reload succeeded21:42:07.485; normal
quit, controller exit0 at21:42:26.847. This was an observation run, not a soak.
Private evidence: `records-work/load-request-20260909/observe/`.

### Healthy rejection: PID21412

Configured only Save3 (a healthy admitted Winterhold save) for rejection;
cold-loaded Save4 normally. Journal > Load selected fileNum3 and confirmed
the actual prompt. The diagnostic logged `reject=1` and
`engine_target_entered=0`; no SKSE pre/post-load event for Save3 followed.
Journal and Cursor remained open, while the fader/spinner closed. A Journal
key did not exit that menu state; normal Cancel did, returning unpaused.

Normal Save > New Save then created Save5, SHA256
`FF581ECE899C932F25B81BC6F8C3777770BBF12D7824E5C62F71A51D8151A9EC`.
Both offline plugin-table and currency gates admitted it. Normal in-session
reload of Save5 succeeded21:45:39.661. Responsive/unpaused at21:46:23.826
(44.165seconds later); normal exit0 at21:46:31.039. No fresh crash report.
Private evidence: `records-work/load-request-20260909/reject-healthy/`.

This establishes bounded menu/save/reload survival, not movement/combat
correctness or a universal safe-cancellation guarantee. Rejection needs clear
in-game feedback rather than an unexplained return to the load menu.

### Known-incompatible copy

PID32964: a byte-identical ESS/co-save pair was copied to the isolated test
profile from the exact failing Adventurer3 autosave. ESS SHA256 remains
`ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.
Co-save SHA256:
`E708EC7CE1B7CC384A4E676E2A52A41DCC668BA235D5FD0FD30571AF9E27A1CF`.
The experiment cold-loaded admitted Save5, never auto-loaded the bad copy.
The exact bad basename was confirmed in the installed diagnostic log.

The game initially filtered the Load menu to the current character. The
observed Character Selection button (MouseButton2, label
`$CharacterSelection`) exposed Adventurer3. That character had exactly one
entry, `AUTO` / `Tamriel`. The file's serialized header still says Bruma;
do not infer the selected input from the display location alone. Confirmed
its actual load prompt and observed the exact filename in the hook log:
`reject=1`, `engine_target_entered=0`. No SKSE preload/postload event for that
filename, no missing-content popup, and no MCM deserialization/crash followed.

After two normal Cancel events, the current Adventurer returned unpaused.
Normal Save > New Save produced Save6, still character ID96C075A9, in
WinterholdJail, not Adventurer3. SHA256:
`5F7C9F61C7B4A83B0E61B2AFBD5526220D4A3FEDDD06E2B8D7669966ABBAF969`.
Both admission gates passed; normal reload succeeded21:51:36.648 and remained
responsive/unpaused at21:52:40.765 (64.117seconds later). Normal controller
exit0 at21:52:46.918; no new crash report. Native ledger continuity and full
gameplay have not been comprehensively assessed by this bounded test.
Private evidence: `records-work/load-request-20260909/reject-adventurer3/`.

Both offline gates continue to refuse the bad copy: missing TrueHUD.esl and
QuickLootIE.esp, and no native currency v2 checkpoint. They were not bypassed
for an automated bad-save load. This is a deliberately intercepted manual
rejection test, not admission of the incompatible campaign.

### Main-menu Continue: rejection works, menu recovery FAILS

PID484, isolated `Astra Admission Continue` profile, contains only the exact
bad copied pair; no autoload. Verified the configured rejection basename and
selected `$CONTINUE`, then read and accepted the actual confirmation:
`Continue from your last saved game?` At21:59:02 the hook rejected that exact
filename before entering the engine target. No campaign deserialization was
attempted. However, at21:59:06 the menu entered `CharacterSelection` and did
not return to `Main` after repeated normal Cancel events. Down also did not
change the main selection. Invoking the observed `$Back` button's own
onPress/onRelease handlers did not recover it either.

At22:00:14 the SaveLoadListHolder reported `bSaving=true`, one pending element
and zero processed elements; its only entry was `$[NEW SAVE]`, not a real
character selection. These are symptoms, not proof of the underlying cause.
This **fails usable Continue cancellation** despite successful interception.
The per-name rejection probe must not be deployed as a production solution.
The isolated worker's existing bounded lifetime remains the cleanup backstop;
do not claim normal quit or complete cancellation acceptance for this run.

The controller timed out with code75 at22:03:31.910; the owned game process
ended. No new crash report appeared (latest remains20:12:50). The game was
responsive to diagnostic reads, but this was **not a normal quit**. Archive:
`records-work/load-request-20260909/reject-continue/`. A read-only attempt to
identify the engine's notification string used an incorrect static address
and failed; its output provides no string-identity evidence. Do not infer
current offsets from old InterfaceStrings member comments.

## Restoration and preservation

At22:04 the original root DLL/PDB were restored after confirming no game/MO2
process remained. DLL SHA256:
`CC2F98A4189E1980B216E0C10C15DBDB65827B44028FBAD11A129FF6D2094591`;
PDB SHA256:
`4527910038FF7E3D009B7B7B85EB0FED5D793E1015944E0143D88D783864CFA6`.
All10 pinned load-argument audit checks pass. ModOrganizer.ini and both
Default lists match the before-images byte-for-byte. No pending MenuPilot
command batch remains. Both bad test pairs were moved, with exact hash
verification, from their isolated profiles into `quarantined-copies/` in
the private evidence folder. Originals were not moved: both hashes match,
and all38 ordinary ESS files remain. The live mutation claim is released.

Hosted Windows/Linux request-probe regression34431758506 and prior
load-argument regression34431758463 pass. These source tests do not override
the failed Continue runtime result or certify campaign recovery.

## Remaining work

- Manual rejection has bounded save/reload survival evidence. Continue
  interception has a verified menu-recovery failure: diagnose and fix that
  before claiming coverage or deploying a compatibility policy.
- Test other routes and nonzero argument paths; no coverage claim by inference.
- Design real admission against active plugin state and currency checkpoint,
  with bounded parsing, stale-state and file-identity protection.
- Provide in-game failure explanation; no desktop popups.
- Keep the user's campaign recovery/migration decision explicit. Rejecting a
  bad load does not repair the save, identify the MCM corrupting writer, or
  complete the crash-repair goal.
- The previous root DLL/PDB are restored; do not install the per-name test
  gate as a production deployment.
