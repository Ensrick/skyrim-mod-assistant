# Deferred native load ownership — September 10, 2026

Tracking: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).
**Experimental; not production admission or crash-goal closure.** This extends
the [refusal UI](LOAD_REFUSAL_UI_2026-09-10.md) and
[inner/outer recovery](LOAD_ADMISSION_RECOVERY_2026-09-10.md) work.

## Implemented contract

SKSE source `da4fa0125955ad7c2d53521a6c56e8abd3005d38` retains the admitted
immutable co-save lease when Skyrim transfers a save stream to a native callback.
Both derived destructor detours must be installed and read back correctly before
admission is available. Cleanup runs before native destruction; native destruction
still executes exactly once. Unknown ownership transitions or gate-owned
destruction permanently disable further admission rather than trusting a possibly
reused address.

An inner return no longer prematurely releases callback-owned state. Resumption
requires the retained stream, bounded name, admitted vtable and eligible lifecycle
state. Each resumed outer invocation receives a new generation, so stale outer or
inner tokens cannot retire the retry. The engine retains responsibility for its
stream cursor and decompression; our retry does not reparse a consumed ESS header.
Both live detour entries, stubs and relocated forwarders are verified before use.

Achievement-prompt suppression is now diagnostic, not a prerequisite: the real
native prompt's cancellation and resumption are supported by this lifecycle.
This is not permission to restore a Creations load order or missing mods.

Local tests passed: 127 actual-source lifecycle checks, 103 actual-source inner
hook checks, and 222 actual detour-verifier checks, plus the retained observer,
request/recovery and native-build tests. All three hosted runs passed:
`34480401446`, `34480401412`, `34480401393`.

## Exact controlled runtime

Private run: `Astra Load262 Lifetime deferred-native`, September 10,
08:04:57–08:14:36 CDT. Skyrim PID 32224, controller PID 27012. Muted QuietWorker
desktop, no interactive desktop input, no OS dialogs. Native game-menu API only.
Original saves and vendor files were not edited.

Candidate DLL SHA256:
`94CE3210465A459F08599E10A8CB7BD0FB4C629C80585F58E994DCF865906DE8`.
The isolated currency admission build was `4DAB6D30...293FD9AF`, fingerprint
`6270B86774F9F4F3`. A temporary overwrite-only Engine Fixes configuration disabled
achievement suppression to expose the callback; vendor configuration was unchanged.

Input was a copy of the current-Default dry-ground Save4 fixture, ESS SHA256
`6C18D93232493C965B68E36B875FA5632274002CCF05CD6FED3A962EEBAE2509`,
co-save `C590BC4895C7E0BCC41B2D32222DF9AC151F3ABB2EB6B5747F5588265B364666`.
This was not the incompatible Adventurer3 campaign.

| Native action | Evidence |
| --- | --- |
| Continue, then cancel achievement prompt | The actual message and Yes/No labels were read. Right selected No (index 1, focused), then Accept at 08:06:40.951. Pending generation 1 was retired before the scalar native destructor, sequences 3–4; no inner/PreLoad occurred. Message closed and Main menu Down/Up navigation recovered. |
| Continue again, accept Yes | Generation 2 transferred to the callback. Native Yes at 08:07:20.969 resumed as generation 3, retaining the snapshot and leaving the engine cursor untouched. PostLoad success at 08:07:27.891. |
| Move and create a new manual save | Native paired Auto-Move changed position from `(24862.389,-4551.8213,-2999.7717)` to `(24842.88,-4355.1826,-2996.429)`, alive and not swimming. Immediate position reads were not yet stable; this is movement evidence, not settled-position certification. New `[M]Whiterun` Save1 was created. |
| Journal load of that Save1 | Native selected filename/entry confirmed; PostLoad success at 08:09:03.821. |
| Two F5/F9 cycles | Successful PostLoad at 08:09:24.738 and 08:09:39.742. |
| Observation and exit | Unpaused native ping at 08:14:29.687, 289.945 seconds after the latest load. Native Quit-to-desktop accepted at 08:14:34.435; controller completed normally at 08:14:36.714. |

Four successful loads total. All four co-save reads completed without snapshot
faults or rejected API calls: initial 64,729 bytes, then three 66,329-byte reads.
Later streams retired on terminal caller ownership before native destruction.
No lifetime poison was reported. The protected private crash directory remained
empty. No claim is made that idle responsiveness is combat/travel coverage.

Quit's MenuPilot batch timed out because the process exited before acknowledging
the batch. The controller's terminal exit 0, final native menu events and absence
of game/controller processes were checked separately; a controller exit code alone
is not a stability verdict.

Private evidence: `records-work/lifetime262-20260910/deferred-native/`, including
SKSE, LaunchProbe, MenuPilot, currency and Papyrus logs. Generated manual Save1
and quicksave remain in that private test profile. The `[M]` prefix and save-number
change are consequences of the achievement test, not rewrites of the source save.

## Preservation and review

After exit the temporary Engine Fixes overwrite was moved into evidence,
restoring its original absence. The harness verified original ESS/co-save, source
fixture, vendor Engine Fixes configuration and Default's three lists unchanged.
Independent disk hashes confirmed ordinary DLL/PDB `0438215A` / `A33BF070`,
currency `C8ED83D1` and CrashLogger `0A38C678` restored. The ordinary DLL retains
the member bounds and texture release fixes, but does **not** link experimental
admission. Claim `astra/lifetime262` released; no owned game/controller remains.

The private CrashLogger template has no retention cleanup, auto-open, uploads,
minidumps or thread-dump hotkey. Its directory is pinned outside original reports.
CrashLogger rewrote/expanded the INI during startup; the effective critical values
were read back before testing. The ordinary INI was restored exactly afterward.

Actual Claude CLI `claude-fable-5-1` performed two read-only reviews, sessions
`762a90ff-d0de-4a28-bb6d-2ebd5bd5ce02` (8 turns) and
`8293f4da-9e1f-4fb1-9156-d892cc830edb` (10 turns), both terminal exit 0.
No Claude job remains. Parent checked reviewer claims against native code:
late callback Run `62C500` was already identified; retry needs a new generation;
gate-owned destruction must poison admission. The pinned scalar destructor calls
the base directly, not the nondeleting hook. Review is not runtime evidence.

## Remaining release gates

- Actual **late inner-failure** callback execution is not covered by this run.
  Native control flow and synthetic false-return cases were inspected/tested;
  this successful early achievement callback is not a substitute.
- Destructor coverage assumes the verified native derived ownership paths.
  Arbitrary foreign frees or direct base-destructor bypasses are unsupported.
- Production packaging, currency fingerprint export and clean diagnostic-off
  acceptance remain unshipped. Do not deploy this test DLL as the normal build.
- Original campaign compatibility/migration remains a user decision; do not
  restore removed mods or clean the save to obtain a green test.
- Representative sustained travel/combat remains #267. The overall goal and
  issues #262/#268 remain open.
