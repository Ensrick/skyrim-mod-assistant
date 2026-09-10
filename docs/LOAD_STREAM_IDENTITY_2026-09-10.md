# Actual engine input identity — September 10

Issue [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) is OPEN.
This is evidence for a runtime-admission prerequisite, not campaign recovery.

## Finding and implemented diagnostic

The pinned1.7.104 engine uses a derived Win32FileType containing the buffered
ESS image. Reading NiFile::file or merely comparing basenames would not prove
which bytes the engine consumes. Private executable inspection established
vtableRVA1B521A0, buffered pointer+BD0, byte count+174, position+BE0 and
decompressed flag+BCA. Its read method159D800 copies from that buffer and
updates position. Constructor159C730 reserves64MiB. These are version-specific
observations, not a portable Bethesda ABI.

Original diagnostic source [db977df](https://github.com/Ensrick/skse64/commit/db977dfdd9d6064ecb9ee8f6f2fd1a1a9403555e)
adds opt-in SKSE_AUTOMATION_LOAD_STREAM_PROBE. It validates the exact vtable,
bounded field reads and undecompressed1..64MiB image, then opens the named disk
input read-only with read sharing and compares every byte in4KiB chunks.
It changes neither stream position nor file contents, does not dump the
save, and makes no admission decision. Unknown layouts are explicitly uncovered.

## Empirical results on the exact diagnostic build

Candidate DLL SHA256:
`40125953FE87C5E336C29CB148E21C71DAED4B44158F4BE0333F2759C7807EDB`.

| Controlled path | Actual compared bytes | Result |
|---|---:|---|
| Main Continue, exact copied Adventurer3 autosave |5,550,827|Exact match, position0, undecompressed; deliberately rejected before engine target; automatic Main recovery/native navigation/Quit worked|
| Main Continue, admitted disposable Save7 |4,606,518|Exact match; original target returned success; currency admission completed|
| Normal new save, then Journal Load of Save8 |4,601,612|Exact match; original target returned success; continued operation and normal Quit|

Run1: gamePID7180/controller33048; private muted desktop; controller0 at
05:10:33.039UTC. Run2: gamePID32360/controller35028; controller0 at
05:16:52.277UTC. Save8 PostLoadGame succeeded05:15:32.701UTC; the game remained
running80seconds afterward. Four bounded movement-input events were delivered,
but no position/displacement measurement was made. This is not long-session
gameplay or an assertion that the user cannot encounter other crashes.

Private evidence: records-work/load-request-20260909/automatic-recovery-stream
and automatic-recovery-healthy-stream. SKSE log hashes respectively:
`84175B00E2C166C7E8F5612741D31A5F20DB050DEFADA3F48C6ADC7B53BC5157`,
`15ED769163991A7AB19425F92AA3D179045CBB7CC63BE88D0CA21367BEEBC2CF`.
New Save8 remains in its disposable profile; input copies were retained in
the evidence directories. No original save was removed, rewritten or cleaned.
Original failing ESS stillSHA256
`ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.

Both test wrappers restored installed rootCC2F98A4. MenuPilot1A1D and currency
0.2.2 were unchanged. No game/controller remains; profile claim released.
The Quit batch timed out because the game exited during the callback, while
the owning controller independently returned0. This timeout is not counted
as a completed MenuPilot batch or mistaken for a game crash.

Full local plugin build and all4 request-probe test targets PASS, including
19 tests compiling the actual Windows observer. Existing1,572,864 wrapper,
35 UI and48 installation checks remain. Hosted source CI allPASS:
[request/snapshot regression34440507184](https://github.com/Ensrick/skse64/actions/runs/34440507184),
[load arguments34440507229](https://github.com/Ensrick/skse64/actions/runs/34440507229),
[full build34440507287](https://github.com/Ensrick/skse64/actions/runs/34440507287).
Earlier currency identity and lease prerequisites at664c3c3 also passed
[Check34439134788](https://github.com/Ensrick/skyrim-mod-assistant/actions/runs/34439134788) and
[Native34439134935](https://github.com/Ensrick/skyrim-mod-assistant/actions/runs/34439134935).

## Independent review and remaining work

Fable5.1 actual-source review completed with no denied reads in session
1118b72b-bb7e-4f51-a2cd-63da8b12f858. It confirms the stale CancelLoading
generation gap and recommends fork-owned admission. Its proposed pass-counter
solution is not adopted solely on review: the fork's named
ProcessEventQueue_HookTarget at116E030 actually cleans already-processed UI
message data; the containing native loop1169D20 performs dispatch beforehand.
Root is validating that loop and producer ordering before changing recovery.
The reviewer is drafting a bounded plugin-table reader and focused tests for
parent integration; no independent live mutation is authorized.

Claude invocation correction: passing a multiline prompt through claude.cmd
truncated the argument list before model/tool restrictions. That owned process
was stopped, and no review result from it was accepted. Direct claude.exe with
stdin prompt, explicit claude-fable-5-1, noninteractive mode, read-only tool list
and dontAsk was then verified in the actual process command line. The user's
interactive PowerShell was never controlled. Claude preserves its conversation.

Still required: actual engine plugin snapshots, bound currency0.2.3 export in
game, co-save path/object/lease lifetime proof, source-only admission integration,
consume-safe cancellation, informative in-game refusal, quickload coverage and
mixed rejected/accepted/live-character tests. Do not drop parser compression1
support simply because the current corpus only containsLZ4. Do not mistake
readiness identity for package correctness, checkpoint validity for complete
save health, or rejection for repaired campaign data.

The original Adventurer3 MCM fault and the user's campaign choice remain open.

## Follow-up: engine plugin table and quickload

Fable5.1 drafted the standalone read-only plugin snapshot reader and tests;
parent reviewed, hardened and integrated an opt-in observer in
[2eef94f](https://github.com/Ensrick/skse64/commit/2eef94f).
It uses the actual loaded arrays, checked capacity/count, bounded reads,
full/light flags, sequential full/light indices and FE light-plugin marker,
bounded names and ASCII-case duplicate checks. Typed refusals and allocation
exceptions are contained by the diagnostic wrapper. No disk plugins.txt
contents are used as the engine's active table. Non-ASCII case equivalence is
still unresolved, explicitly not certified.

Parent corrections before testing: empty Names fixture helper, FE marker,
wrapping read spans before callback invocation, dot-directory name rejection,
and Windows max macro compatibility.72 synthetic checks pass, including
254full/4096light maxima, and all prior request/observer tests pass. The full
native plugin compiles with actual GameData offset assertions.

Candidate DLL:
`7AF80B2F20F0FDCD0B3F7BE2B69890A88BEBB6FC30CF37F06ADD219E555B5975`.
Muted private run PID34544/controller18068:

- Continue-loaded copied admitted Save7; engine snapshot77full/307light,
  every name in index order matched independently parsed Save7.
- Quicksave input created the isolated Quicksave0; the currency gate admitted
  its actual co-save before quickload was attempted.
- F9 Quickload reached625FF5 on thread31020 with arg2=1, and exactly matched
  all4,604,467 buffered bytes. Engine target and PostLoadGame succeeded.
- Normal Journal Quit/controller0 at05:30:17.279UTC,82seconds after quickload
  PostLoadGame. No new crash report. Original source fixture unchanged; new
  quicksave remains in the disposable profile, input copy archived.
- Root restoredCC2F, no game/controller or live claim remains. Currency0.2.2
  and MenuPilot unchanged. No permanent deployment or production guard yet.

Evidence folder records-work/load-request-20260909/automatic-recovery-healthy-plugins;
SKSE logSHA256
`42365562D910F929A8D393BEF128BA9562FB768BD2E2B629AB1D47051FA88A73`.
Source CI all completed successfully:34441333722(request/plugin tests on
Windows/Linux),34441333932(arguments),34441333734(full build). Canonical
report c2f6457 Check34440821935 passed; acc2c92 Check34441442869 was still
running at this source-validation checkpoint and is not yet claimed passed.

This closes the observed F9 route unknown for this runtime. It does not prove
every possible console/external load route, mixed rejected/accepted sequences
under a real policy, or the unresolved original campaign.
