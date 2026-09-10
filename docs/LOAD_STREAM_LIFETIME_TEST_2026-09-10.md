# Native stream lifetime diagnostic control — 2026-09-10

Status: narrow experimental controls passed; #262 and the full crash/gameplay
goal remain OPEN. No new release build or admission policy installed.

## Source and review

SKSE fork commit `3c44909bb84ae6570600251ed36f72b67aa98a80` adds opt-in
diagnostic-only scalar/nondeleting stream destructor observers. Exact 1.7.104
entry signatures, whole-six-byte forwarders, separate ABIs and trampoline
capacity checks precede installation. Native destruction is forwarded once;
observation never releases a lease or changes a load result. Output is bounded
to128 events plus exhaustion; contended/reentrant snapshots are unknown.
Sequence numbers are allocated under the same gate as pending-state snapshots
and releases. They order snapshots, NOT completion of destruction. Pointer
matching is explicitly not allocation identity/ABA protection.

Actual Claude Fable5.1 session `2a8fe176-04c4-4e46-9b1f-a4200719d941`
performed read-only source reviews. Parent fixed log ordering and same-thread
mutex reentry; declined an unbounded logging exemption and unsafe pathname
fallback after losing validated-reader continuity. No simulated Fable agent.

Local checks:147 bounded observer +34 actual-source lifecycle checks pass;
experimental DLL build passes. GitHub regression matrix
[34460714920](https://github.com/Ensrick/skse64/actions/runs/34460714920)
and build [34460714903](https://github.com/Ensrick/skse64/actions/runs/34460714903)
both pass. Tests do not prove native callback cancellation safety.

Experimental DLL SHA256:
`FA0E6BF0641F92109E3C6B1F5568BB742F19B18DD6A94B4AFF568F5B58611617`.
The local build includes experimental admission; CI/default clean build does
not acquire that capability merely because this source commit exists.

## Isolated empirical runs (America/Chicago)

Both used a copied healthy dry-ground Save4 from the prior Whiterun control:
ESS SHA256 `6C18D93232493C965B68E36B875FA5632274002CCF05CD6FED3A962EEBAE2509`.
Dedicated cloned profiles, muted private QuietWorker desktop, local saves,
no desktop switch, private crash output and cleanup disabled. Minidumps off.

| Control | Interval | Observed result |
|---|---|---|
| `Astra Load262 Lifetime observe-only` |04:23:41–04:25:59|Admission enforcement off, existing currency0.2.2; Continue, new Save5, Journal reload, normal quit; five scalar observations, no pending lease as expected.|
| `Astra Load262 Lifetime enforce` |04:26:33–04:29:09|Admission on with temporary currency0.2.3; Continue, new Save5, Journal reload, F5/F9, normal quit; three successful admissions, seven scalar observations.|

Enforced sequence evidence:

| Input | Successful PostLoad | Context / release / destroy sequence |
|---|---|---|
|Copied Save4 Continue|04:27:38.815|1 /2 /3|
|New Save5 Journal load|04:28:21.705|7 /8 /9|
|New quicksave F9|04:28:49.438|11 /12 /13|

All three logged matched consumption of the verified co-save handle and
currency admission completion. At corresponding destruction the gate snapshot
had pending=0. Other scalar destructions occurred during save enumeration and
on another thread; they cannot be labelled cancelled loads from pointers alone.
No `SAVE_ADMISSION_PENDING`, nondeleting observation, exhaustion, member-guard
rejection or fresh crash was observed. Both destructor hooks reported installed,
but absence of a nondeleting event is not execution coverage for that entry.

The first driver query arrived before initialization completed and timed out;
its read-only batch later completed, then commands resumed. Normal Quit ended
the process before its last batch acknowledgement, also a driver timeout—not
an inferred crash. Controller exit0 was checked alongside fresh logs rather
than used as standalone certification.

Private receipts/logs: `records-work/lifetime262-20260910/{observe-only,enforce}`.
Harness `records-work/lifetime262-run.ps1` snapshots the CURRENT installed
DLL/PDB first; it does not restore an obsolete earlier experiment's backup.

## Restoration and unresolved work

Both runs restored clean installed SKSE SHA256
`4E3F618B6A413B6EA3C38E238EBC607E056EEBFC34ED72073DD46BEEA7BD7184`,
currency0.2.2 `C8ED83D13E0EEFC0353A20D4C7C40438CD2DF31596B15979994BBB501074007E`,
and CrashLogger configuration
`0A38C67861A8BFAFD6640EB8D05398060ECF170621EB7FE2DF368AEB9A5C58DB`.
Original Adventurer3 ESS/co-save, source fixture pair and Default's three
load-order lists retain identical hashes. No game/controller remains; live
claim released. Vendor assets and other assistants' work were not changed.

Still required before production admission: native deferred/cancelled ownership
coverage and safe cleanup, late-inner failure policy that neither bypasses
validation nor skips required engine cleanup, mixed admitted/refused loads
without corrupting a live character, and reproducible packaging. These runs
are not long-duration travel/combat acceptance, an original-save migration,
or evidence that every crash is fixed. Original save currency-ledger/missing-mod
decisions still require the user; no campaign policy was chosen here.
