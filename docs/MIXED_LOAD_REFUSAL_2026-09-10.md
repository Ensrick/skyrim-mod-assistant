# Mixed live-character load refusal — September 10, 2026

Result: the tested missing-co-save Journal refusal preserved the already-live
character and allowed subsequent movement/save/reload. This is a bounded
experimental result, not production admission or full #262 closure.

## Inputs and source

Private profile `Astra Load262 Lifetime mixed-refusal`, cloned from Default;
muted QuietWorker desktop, game PID29240, controller17668. Run04:36:10.654–
04:42:56.556 America/Chicago. No desktop switch, external popup or vendor edit.

Experimental SKSE source `b01fb46b0638d9a8ff0128e93ce823aa70405e0e` adds the
already-read request stream pointer to diagnostic output, allowing correlation
with destruction even on refusal. No new release or refusal behavior.
DLL SHA256 `9164118D6FF7A86A35E28565DB912FFFCA6BC7AE73FA7732B2919DBED2B90981`.
Four actual-source test suites and full experimental build pass; GitHub runs
[34461568153](https://github.com/Ensrick/skse64/actions/runs/34461568153) and
[34461568150](https://github.com/Ensrick/skse64/actions/runs/34461568150) pass.
Temporary currency0.2.3 supplies the tested native admission fingerprint.

Actual Fable5.1 read-only review used session2a8fe176, exec83094, terminal0,
six turns with no writes/agents. Parent accepted correlation and post-refusal
assertions. Reviewer overlooked existing native627B20 disassembly; it was
rechecked along with a new pinned625Fxx caller slice. Neither alone proves all
downstream state behavior.

## Negative fixture and observations

Initially loaded healthy copied dry Save4, ESS SHA256
`6C18D93232493C965B68E36B875FA5632274002CCF05CD6FED3A962EEBAE2509`.
An externally copied Save99 did not appear in the live Journal: only Save4 was
listed. No load of Save99 was attempted. It remains an UNUSED negative fixture
in this disposable profile and must not be used for acceptance/Continue tests.

Instead created Save5 with the game's New Save action at04:38:19.671.
Moved ONLY that newly generated private co-save to the evidence folder before
attempting Journal load5, retaining it byte-for-byte for restoration. This is
an intentionally incomplete test fixture, not save cleaning or migration.
ESS SHA256 `89EF372F92C20CB9DBA9C6F68DD9C03D22B4CA7C93B8201E85AE8DEDE77B6979`;
co-save65384 bytes, SHA256
`C39B2EBFECCD8A690597234E40EE652DCCABBC3FAC5C9E388B35C1841D44786F`.

At04:39:02 the refusal reported `status=6`, read-sharing lease acquisition
failure `Win32=2` (file not found), NOT a stale pending lease. It logged
`engine_target_entered=0`. The same request stream `0000019F914AB040` then
appeared at scalar destruction, seq9, pending=0/matched=0. No PreLoad or
LoadRequestResult for this refused attempt, no currency reinitialization.
Recovery delegate was current but `main_cancel_queued=0`: native Journal
returned without an inappropriate Main Menu cancellation.

Player identity/cell/world/state and position were unchanged between04:38:32
and04:39:06: form14, cell1A276, world1A26F, state0,
position(24862.389,-4551.8213,-2999.7717). These are bounded read-only observations
using the independently audited position/identity layout, not an atomic whole
actor/VM health certificate. No native health calls or memory writes.

Restored the exact co-save hash before further loads. Two normal Cancel events
backed out of the Journal. Auto-Move on/off produced displacement to
(24842.832,-4354.7837,-2997.673), observed stopped with auto=0/state0 at04:40:05.
F5 created a correctly named quicksave, not a Save5/Save99 stale serialization
target. Subsequent successful PostLoad callbacks:

| Route | PostLoad time | Currency completion |
|---|---|---|
|F9 newly created quicksave|04:40:20.784|admission6, ledger11|
|Journal restored Save5|04:40:56.473|admission9, ledger11|
|Journal original copied Save4|04:41:33.706|admission12, ledger11|

Each consumed a matched admitted co-save handle and released its lease. Native
admission context generations and UI request generations are separate counters;
do not equate the similarly numbered log fields. Player observation at04:42:34
and unpaused responsive ping at04:42:50 followed the final load by61/76 seconds.
Normal menu Quit completed04:42:56. No fresh crash/member-guard rejection or
deferred pending stream was observed. Quit interrupted its final command
acknowledgement as expected; controller termination and archived logs confirm
normal exit rather than inferring it from a driver timeout.

## Restoration and remaining release gaps

Fresh current backups restored clean installed SKSE4E3, currency0.2.2 C8ED,
and CrashLogger0A38 exactly. Original Adventurer3 and healthy source fixture
pairs plus Default's three lists retained their hashes. Game/controller absent,
claim released. The restored private Save5 co-save still matches C39B. Logs and
backup retained under `records-work/lifetime262-20260910/mixed-refusal`.

The refusal displayed NO descriptive reason in the Journal. A release needs
clear in-game feedback without desktop windows or forcing a different save.
Other refusal classes, queued-recovery races, native deferred/cancelled stream
ownership, late-inner cleanup, packaging and broader travel/combat acceptance
remain unproven. Original campaign restoration/migration still requires user
direction; no such policy was selected by this test. #262 remains OPEN.
