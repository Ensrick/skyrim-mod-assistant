# Immutable co-save snapshot — 2026-09-10

Scope: experimental save admission for Skyrim 1.7.104, master issue #262.
This is a narrow reader improvement, not closure of the crash investigation.

## Implementation

SKSE fork commit `dfd1a0a8d275eaef71eeef8277f12f86b02e533e` consumes the
immutable co-save bytes already validated by admission instead of reopening
the pathname later. Shared ownership pins the admission lease while the reader
uses those bytes, including if pending-context ownership ends first. Binding
does not copy the file or allocate another shared-owner control block.

Bounds failures return failure through checked serialization APIs without
throwing through third-party callbacks or falsely reporting a successful read.
Invalid write/phase calls are counted separately from fatal host-reader errors.
The save callback refuses a bound-load reentry before its co-save deletion or
creation code. This does not certify the whole native save path as reentrant.

Actual Claude Fable 5.1 performed two read-only reviews through the installed
CLI. Parent corrections include the pre-delete guard, separating API misuse
from fatal reader errors, and explicit host-fault diagnostics. A Windows build
also caught and corrected the real `UInt32` virtual-signature distinction.

Local checks: 49 adapter, 27 extracted production serialization API/save-guard,
39 actual-source lifecycle checks, and four existing request test suites pass.
Both GitHub runs `34463996181` and `34463996169` succeeded. Portable tests do
not establish native engine behavior on their own.

## Private runtime control

Muted private profile `Astra Load262 Lifetime snapshot-reader`, cloned from
Default; copied healthy dry-ground Save4, no original-save changes. Candidate
DLL SHA-256:
`8687E0329154DADAE80818EC5696DFEA89EC42A5C7F70821F46E2C9CB258E2E9`.
Currency admission candidate 0.2.3 was temporary for this test.

| Route | Successful post-load (CDT) | Snapshot bytes consumed | Faults / rejected API calls |
| --- | --- | ---: | --- |
| Continue, copied Save4 | 05:04:54 | 64,729 | 0 / 0 |
| Journal, newly generated Save5 | 05:11:17.876 | 65,384 | 0 / 0 |
| F5 save then F9 quickload | 05:11:23.411 | 65,275 | 0 / 0 |

Each logged `pathname_reopened=0`, cursor equal to snapshot length, context
release and subsequent native stream destruction. Currency admissions 3, 6,
and 9 completed with ledger 11. Player identity, cell/world, and position were
stable in the post-load read-only check. Waiting in a paused journal before
the second load is not counted as sustained gameplay.

At 05:12:33.451 the player remained at `(24862.389, -4551.821,
-2999.7717)`, cell `0001A276`, world `0001A26F`; identity and position were
stable, reported life-state 0, auto-move 0. An unpaused responsive ping at
05:12:33.696 was more than 70 seconds after the latest successful post-load.
This is idle stability, not a new movement/combat test.

Normal journal Quit-to-desktop confirmation was accepted at 05:12:38.692.
The private controller finished at 05:12:40.980 with exit 0. The expected
MenuPilot callback timeout during process shutdown is not counted as a pass;
actual process termination and restoration were checked separately. No fresh
crash artifact or member-guard rejection was observed in this control.

Harness verified unchanged original ESS/co-save, source fixture pair and all
three Default list hashes. Exact restoration independently confirmed:

- Normal SKSE DLL: `4E3F618B6A413B6EA3C38E238EBC607E056EEBFC34ED72073DD46BEEA7BD7184`.
- Currency DLL: `C8ED83D13E0EEFC0353A20D4C7C40438CD2DF31596B15979994BBB501074007E`.
- CrashLogger configuration: `0A38C67861A8BFAFD6640EB8D05398060ECF170621EB7FE2DF368AEB9A5C58DB`.

Private logs are retained under
`records-work/lifetime262-20260910/snapshot-reader`; no licensed payload or
private save is published with this report. No game/controller remains.

## Remaining release gates

Follow-up native inspection and actual Fable review found ownership transfers
after the inner routine returns false (`628414..62841C` and `628E24..628E2C`),
not just the previously identified early callback. A false inner result is
therefore not proof of synchronous cleanup. The meanings of the intervening
native calls are not established; no branch bypass or cancellation-release
change was implemented. Review also rejected treating a naked asynchronously
published abandoned pointer as generation-safe cleanup.

All four archived lifetime controls (`observe-only`, `enforce`,
`mixed-refusal`, `snapshot-reader`) contain zero
`SAVE_ADMISSION_PENDING ... transferred=1` records. The observe-only control
did not enforce admission; zero there is expected and not coverage. The three
enforced controls do not establish deferred success/cancellation behavior.

- Native deferred/cancelled stream ownership and late continuity-failure cleanup.
- Clear in-game refusal feedback; no desktop popup is acceptable.
- Reproducible production packaging and representative travel/combat coverage.
- Original campaign compatibility decisions remain user-owned; no save cleaning,
  missing-mod restoration, or campaign migration is authorized by this test.

The normal installed release does not enable experimental admission. Preserve
that distinction when comparing healthy-control and original-incident results.
