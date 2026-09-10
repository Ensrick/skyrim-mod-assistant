# SKSE load argument repair — September 9, 2026

Related: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).
**Confirmed ABI defect; repaired with bounded runtime verification. The Adventurer3
crash and manual-load admission gap are NOT closed.**

## Mechanism and scope

On the exact installed 1.7.104 executable, the caller at RVA62812F passes six
Win64 arguments including `this`. SKSE's hook and original-target declarations
only accepted five. The sixth byte, written at caller `[rsp+28h]`, is consumed
by the target at618A9D and influences load validation. The old hook's outgoing
stack slot was not initialized with the incoming value.

The correction adds a `UInt8` parameter to both declarations, the definition
and the forwarding call. It preserves the byte, not a guessed Boolean
interpretation. Existing lock/message order and target return semantics are
unchanged. Opt-in `SKSE_AUTOMATION_LOAD_ARGUMENT_PROBE=1` logs the forwarded
arguments and result; its default is OFF. There is no save cleaning, missing
content restoration, load veto, or speculative null-pointer suppression.

Source: [73d2f7b](https://github.com/Ensrick/skse64/commit/73d2f7ba9db08d18423c82edc1442adc433597aa).
Detailed stack arithmetic and binary RVAs are in the source test README.
Independent Fable5.1 read-only review, session
`6cc49471-80f7-4908-b1e2-61fbe9fb6071`, confirmed the omission and minimal fix;
it did not establish crash causality or approve a manual-load veto.

## Verification

- Exact engine MD5 `113faeb71fd8f62b26d0c8627299ab40`.
- Old DLL SHA256 `240C9B5CFC5CE6D632FF931B96A91219CA71B34AE7D263CF4F688C25DF8AE707`.
- Candidate SHA256 `CC2F98A4189E1980B216E0C10C15DBDB65827B44028FBAD11A129FF6D2094591`.
- Disassembly of both DLLs confirms the missing outgoing store in the old
  code and incoming-to-outgoing byte forwarding in the candidate. The pinned
  read-only `audit/skse_load_arguments.py` passes ten identity/instruction
  checks on the candidate and refuses the old DLL. It is not a general ABI
  proof for other builds.
- Production-body/declaration extraction test: 2,048 cases covering every
  byte, both target results, probe states and registration cleanup states.
  Checks pointers, other arguments, save names, lock balance and message order.
  Engine collaborators are mocks; this does not execute engine validation.
- [Windows/Linux regression CI](https://github.com/Ensrick/skse64/actions/runs/34429092151)
  and [full build CI](https://github.com/Ensrick/skse64/actions/runs/34429091997) passed.

### Diagnostic-on runtime: PID25732

Muted private-desktop run; no interactive desktop input. Controller start
21:20:22CDT, clean exit0 at21:25:10.445. Main menu reached before the cold load
at21:21:09 (under60seconds). Source `Astra Unbound263 Source`, target
`Astra Unbound263 Test`, not Default. This test also retains the isolated
Unbound jail-pool candidate; it does not establish that Default has that patch.

1. Exact admitted Save3 WinterholdJail cold load succeeded21:21:12.624.
2. Normal Journal > Save > New Save created Save4 at21:22:02, SHA256
   `E860644B9374BCF7DF1931CA36D9E06D94BA4687836CF1C1152F4981FE083169`.
3. Both plugin-table and currency checkpoint gates admitted Save4.
4. Journal > Load selected fileNum4, The Chill; confirmed the actual load
   prompt. Reload succeeded21:23:09.625.
5. Main-thread ping remained responsive/unpaused at21:24:16.763, 67.138seconds
   after success. This is an idle observation, not representative gameplay.
6. Both actual loads forwarded `sixth=00`, `arg1=00000000`, `arg2=D0000010`
   and returned1. This does not runtime-cover nonzero sixth arguments.
7. Native currency admitted both loads with ledger8. Normal engine quit;
   no fresh crash reports, no owned processes/pending commands, Default
   lists and ModOrganizer.ini byte-identical to before-images afterward.

Private evidence: `records-work/skse-load-20260909/runtime/` (five logs).
Rollback DLL/PDB and config before-images: `records-work/skse-load-20260909/before/`.

### Diagnostic-OFF runtime: PID32700

Controller start21:25:39.445, normal exit0 at21:28:01.979. Main menu and
Save4 cold-load attempt occurred under60seconds; success21:26:27.596.
Responsive/unpaused main-thread ping at21:27:55.734 was88.138seconds later.
Native currency admission3 completed with ledger8. Zero `LOAD_ARGUMENT`
diagnostic lines. No fresh crash reports; config before-images matched after
exit; no owned game/controller or pending commands. Logs are archived under
`records-work/skse-load-20260909/runtime-off/`.

All38 ordinary ESS files remain present, and the original Adventurer3 autosave
still hashes to `ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.
The corrected root DLL/PDB remain installed. Both diagnostics are default OFF.
The instance claim was released after verification and restoration.

### Remaining gates

- Nonzero sixth-byte engine paths and failure/cancellation remain runtime
  untested; unit tests cover byte preservation but not those engine paths.
- The actual old Adventurer3 input still has removed plugin/script types and
  lacks a currency v2 checkpoint. No original save has been changed.
- This repair is not empirical proof of the writer responsible for the MCM
  refcount corruption. A current-save success does not substitute for testing
  the reported input or an explicitly approved campaign recovery strategy.
- Normal Continue/Load admission still needs a verified pre-mutation boundary,
  safe cancellation and diagnostic feedback without desktop popups. A bare
  false return from this hook is not yet an approved implementation.

## Distribution and ownership

Original source changes are separately published in our SKSE fork. Upstream
SKSE terms remain in force (not MIT); no binary public release is approved.
No vendor mod payload, load order, Keep decision, or original save is altered.
Existing property-sheet edits and Claude's dirty canonical files are excluded.

## Admission-boundary investigation (not implemented)

Further exact-executable inspection gives a concrete reason not to implement
a bare `return false` in the SKSE hook. The engine's own early-rejection path
at `618AF3` calls `61FEF0`, writes `FF` through a saved pointer at `618B06`,
sets result state and jumps to its shared epilogue at `619381`. Those effects
would be skipped by returning from the wrapper. Separately, the outer caller
always invokes `624D70` after the hook and before branching on its result.
The identities/invariants of those state objects and cleanup calls are not
yet fully mapped. This is evidence of a nontrivial rejection contract, not
proof that any proposed interception is safe or unsafe in every context.

Next: trace the normal menu/queued-load request before deserialization or
character teardown, then verify cancellation leaves the existing session
usable. Do not bypass the current offline admission gates merely to obtain a
passing test, and do not turn a missing-content load into silent recovery.
