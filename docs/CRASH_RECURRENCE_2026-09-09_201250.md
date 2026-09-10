# Critical load-crash recurrence — September 9, 20:12:50 CDT

**Unresolved: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).**
Related: #256 (earlier incident), #157 (Papyrus failures), #227 (acceptance
automation), #102 (lifecycle), #261 (separate SKSE save-time repair).

## What the evidence establishes

| Observation | Evidence |
| --- | --- |
| Immediate crash | `SkyrimSE.exe+09C00FC`, `lock xadd [rbx], eax`, RBX=2: invalid write to address2. |
| Active script work | Live R13 `CodeTasklet` is in `SKI_ConfigBase.OnConfigManagerReady`, via `MCM_ConfigBase`. The warning stack includes `[None].TrueHUD_MCM.OnConfigManagerReady`. |
| Actual input | Adventurer3 Bruma autosave, SHA256 `ed8255cd464f8e17ba19aad5f2154549d9bff51ccc5fb8165473fd26fb1ef8f9`: byte-identical to the previously failing September8 input. |
| Timeline | Load failure callback at20:12:34.483; another load at20:12:42.124; success at20:12:49.475; crash roughly one second later. |
| Admission | Read-only plugin gate refuses `TrueHUD.esl` and `QuickLootIE.esp`, which remain in the save but are inactive/removed. Currency gate refuses the absent v2 checkpoint. |
| SKSE repair | Installed DLL still hashes to `240C9B5CFC5CE6D632FF931B96A91219CA71B34AE7D263CF4F688C25DF8AE707`. This is an on-disk identity check, not a dump-derived loaded-image hash. |

The immediate failure is **not** the `GetStackInfo` legacy-pointer dereference
repaired under #261. The old MCM failure family is recurring, but stack mentions
and missing plugins do not identify the original corrupting writer with certainty.
A different crash address alone does not rule out an indirect shared cause.
Do not label this an animation/Havok fault from scanned behavior names.

The prior work did not repair or migrate this campaign save. Restoring Default
made the ordinary saves visible again; it did not make them compatible. That
distinction needed to be prominent in the user-facing handoff, not buried in
the technical report. The user's continued crash experience remains unresolved.

## Concrete process failure and hardening

The normal in-game Continue/Load path still allows an inadmissible save.
Python prelaunch admission only protects automated runs, and the currency
plugin's refusal does not veto the game's load. This gap must not be presented
as solved. No original save was cleaned or rewritten, no mod was reinstalled,
and no game was launched for this investigation.

Separately, `audit/launch_verify.py` could return PASS on the first successful
load callback. This was not the full procedure used for #261 (which included
manual repeated saves/reloads), but it was a genuine false-positive hazard:

- Require at least60 seconds after the latest successful load before bounded
  smoke-test PASS. This is not a soak test or a universal crash-free guarantee.
- A new load resets the prior success and observation timer; malformed latest
  timing cannot retain a previous success.
- Process death, failed load, watchdog hang or a matching fresh crash report
  outranks the success callback. Check reports even while a crash handler keeps
  the process alive; match PID and report time, not filename/mtime alone.
- Regression cases include this success-then-crash timeline, stale/other-PID
  reports, invalid timestamps, reload reset, and the observation boundary.
- Run these offline tests in CI. No runtime repair is claimed from them.

Private evidence retained before any relaunch:
`records-work/crash-recurrence-20260909-201250/` contains the exact crash,
LaunchProbe, SKSE and native currency logs. Original save remains untouched.

## Required next work and closure boundary

- [x] Archive logs; identify actual input and recheck both admission gates.
- [x] Add and locally test post-load/crash-report regression checks.
- [ ] Identify the causal saved/native MCM state using copies, without
  speculative pointer suppression or deletion of script instances.
- [ ] Design and verify admission for manual Continue/Load inside the game,
  without desktop popups or silently changing which save the user loads.
- [ ] Obtain approval for any campaign restoration/migration strategy that
  would require restoring removed mods or modifying a save copy.
- [ ] Reproduce and verify the selected repair against the relevant input,
  then run representative sustained play before closing this recurrence.

The existing #261 mechanism-level evidence remains valid for its tested scope;
it is not a whole-modlist or old-campaign acceptance certificate. If that same
lookup failure recurs, reopen #261. Keep #262 open until its own criteria pass.
See [crash closure standard](CRASH_CLOSURE_STANDARD.md).

## Follow-up: current-build fresh control and independent review

The later isolated test did launch a genuinely new character, preserving all
original saves. It successfully initialized MCM and currency, saved, reloaded
in-session, remained unpaused more than68 seconds after load, and quit normally.
**It failed normal world entry**, exposing a separate Unbound location-selection
error tracked in [#263](https://github.com/Ensrick/skyrim-mod-assistant/issues/263).
See [full control evidence](UNBOUND_START_FAILURE_2026-09-09.md). This is not
an overall acceptance pass or a repair of Adventurer3; #262 remains open.

The20:12 crash's rotated Papyrus log was recovered before another rotation and
archived as `records-work/crash-recurrence-20260909-201250/Papyrus.log`. It
confirms missing TrueHUD_MCM type information, missing LoadConfig, and type
mismatches in the same live MCM call chain as the crash report.

A separate read-only Fable5.1 review (CLI session
`7bd2c84c-95fb-4c94-9b0a-734c67163223`, no permission denials, no mutations)
favored obsolete saved script state but did not rule out a native writer.
Its suggested Variable/refcount teardown interpretation remains an inference
until exact binary IDs and instructions are mapped. Returning false from
SKSE's load hook is **not yet a reviewed safe veto**: caller state, prompts,
revert timing, flags and message/lock symmetry must be established first.
The existing hook's false-return path alone is insufficient proof.

Additional hardening: the isolated launcher now invokes the currency gate for
both menu-only package checks and explicit cold-load checkpoint checks.
Previously that launcher only checked the save plugin table. Four CLI wiring
tests plus20 existing currency-gate tests pass. This does not intercept manual
Continue/Load or certify Papyrus state; those remain separate open requirements.

September9 21:28: a concrete SKSE ABI defect was found and repaired: the load
hook omitted the engine's sixth argument. Exact binary verification, independent
Fable review, source tests/CI and isolated diagnostic-on/off load/save/reload
checks support that narrow repair. They do **not** establish that this caused
the old MCM crash or repair the saved script state. See
[load-argument report](SKSE_LOAD_ARGUMENT_REPAIR_2026-09-09.md). The corrected
root DLL is CC2F98A4; original saves remain unchanged. This issue stays open.
