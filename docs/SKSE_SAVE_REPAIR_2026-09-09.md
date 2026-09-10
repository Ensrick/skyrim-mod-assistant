# September 9 SKSE save-time crash and save visibility

Tracker: [#261](https://github.com/Ensrick/skyrim-mod-assistant/issues/261).
Status: targeted fix installed; controlled crash comparison, repeated saves,
in-session reloads and cold reloads pass, including diagnostics OFF.
This is distinct from the earlier BTPS ControlMap input-context corruption.

**September 9, 20:12 recurrence:** the user still cannot load the old Adventurer3
campaign reliably. Its byte-identical earlier failing autosave now crashes in
engine Papyrus/MCM work, not this immediate save-time lookup. #261's scope is
only the mechanism tested below, not campaign recovery or modlist acceptance.
The unresolved recurrence and manual-load admission gap are tracked in
[#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) and
[the new incident report](CRASH_RECURRENCE_2026-09-09_201250.md).

## Cause and narrow repair

The 18:11:02 crash occurs in `SKSEPersistentObjectStorage::CleanDroppedStacks`,
inside the inlined `VMClassRegistry::GetStackInfo`. Old code follows a legacy
two-pointer chain. The current engine map instead contains StackID -> direct
smart-pointer-held Stack. Stack+0x18 is a small-array header, not a pointer.
The original crash read address 0x1E after treating header value 6 as a pointer.

Disassembly identifies the offending loads, and a read-only live map snapshot
matched a map key to the Stack's embedded ID at 0x80. CommonLib and SKSE agree
on the map at 0x9320 and recursive lock at 0x9318. Returning the direct pointer
under the existing lock repairs the lookup without disabling object cleanup,
changing save formats, removing scripts, or modifying any third-party mod.
Internal consumers only check this opaque return for null.

Source: [Ensrick/skse64 commit 3778070](https://github.com/Ensrick/skse64/commit/3778070a8486359b36e12d3924360d351c417d3b).
The corresponding mail patch is retained under `patches/skse/` in this repo.
The SKSE license remains applicable; this is not relabeled MIT. No full binary
release to Nexus is approved by this repair.

## Empirical evidence, not just a successful launch

All times below are September 9, America/Chicago. Private evidence is under
`records-work/skse-save-20260909/`; full logs, dumps, saves and DLL/PDB files
are not public repository payloads.

| Test | Result and limits |
| --- | --- |
| Natural replay, original DLL | Two saves succeeded. This did not exercise the conditional failing lookup and was not accepted as a fix. |
| Old code plus diagnostic,18:23:40 | Real active Stack lookup crashed at the same bad second dereference with header0x80000003. One persistent storage slot. |
| First fixed build, same original input fixture | Three covered saves at18:29:26,18:30:09,18:31:04; header words6 and12; direct pointers match; serialization continued. One additional save was NOT_COVERED. Test hit its600-second bounded lifetime while paused at the quit menu; this was not a clean-exit test. |
| Final guarded build,18:38-18:42 | Cold-loaded the first fixed save. Three consecutive saves at18:39:52,18:40:26,18:40:55 have pointer AND embedded-ID match. Saved slots1/filled0. Clean engine-menu desktop exit. |
| Final guarded build,18:42-18:45 | Cold-loaded that final save, `STACK_STORAGE_LOAD slots=1 filled=0 restored=0`; `kPostLoadGame success=1`. Clean desktop exit. |
| Current Default clone, 18:46-18:54 | Admitted fresh currency 0.2.2 fixture loaded. Unbound Begin Adventure produced two covered saves (IDs 4182 and 4335, pointer/ID matches). A third quicksave completed with no active stack, explicitly NOT_COVERED. That quicksave passed currency admission and loaded through the engine's Journal Load menu at 18:52:55; slots 1, filled 0, restored 0. Clean desktop exit. |
| Current Default clone, diagnostic OFF | Cold load at 18:55:47 succeeded; quicksave at 18:56:08 completed and passed currency admission; in-session reload at 18:57:12 succeeded. Zero diagnostic lines. Clean desktop exit at 18:59:33; no fresh crash report. |
| Native regression |65,536 production-function cases, null/absent entries, nested locking, pointer identity and no pointee writes pass. GitHub Windows and Linux jobs pass. |

The diagnostic forces coverage using an existing real engine stack. The
controlled crash is not a claim of reproducing the user's exact interaction
timing. The storage round-trip above has zero populated slots: it does not
claim to test every serializable object type or prove an absence of leaks.

`SKSE_AUTOMATION_STACK_LOOKUP_PROBE` is OFF unless explicitly set to1 on a
test launch. The probe revalidates pointer and embedded ID while holding the
recursive lock; disappeared/replaced stacks are NOT_COVERED. Log I/O is outside
the lock. The raw eight-byte `legacy_first_value` may include neighboring bytes
alongside the 32-bit capacity; it is deliberately what the old pointer load saw.

Separate Fable 5.1 review: first run could read evidence but was denied source
access. After granting only the necessary source directories, the second run
had no denied reads and approved the scoped code, pending runtime tests. This
was a headless review, not a message delivered to the user's interactive chat.

## Why saves appeared missing

MO2 was selected to `Astra Crash256 - New Game`, with profile-local saves.
That stale diagnostic profile also used the old currency configuration. The
38 ordinary ESS files were still present in the normal Documents save folder;
the original successful test fixture was also present. The failed save left
an empty ESS.tmp and a partial co-save, which have been preserved as evidence.
We did not delete, clean, migrate or rewrite player saves.

`selected_profile` was restored to Default using MO2Headless transaction
`20260909T231412317Z-959605eaf75f`. Default uses the ordinary Documents save
folder. Temporary tests use separate profile-local copies and restore the
selection afterward. Presence of 38 saves does not establish that every save
ever made remains available; only the checked files are accounted for.

Old campaign saves are not silently loaded to claim a regression pass:
plugin/currency admission must pass, and removed-script migration is a separate
decision. The current-profile fixture is an admitted fresh 0.2.2 currency save.

Build receipt: `records/source-builds/ensrick-skse-stack-lookup-1.7.104.json`.
Final DLL SHA256:
`240C9B5CFC5CE6D632FF931B96A91219CA71B34AE7D263CF4F688C25DF8AE707`.
Original failed-session input ESS SHA256 remains
`657D57C98B6495F57A7672B2F059AB6C0088F21EB23A352D4FB598389C2A36CE`.

The root-file manifest was updated only for the repaired SKSE DLL, not to
silently bless unrelated files. This is an existing root tool repair, not a
new Nexus mod or a reason to change Keep/Skip decisions. The SKSE scripts
package and all plugin/mod load order inputs were unchanged by the repair.

Final checks at 18:59:39: no Skyrim/MO2Headless test process, no pending
MenuPilot batch, selected profile Default, `LocalSaves=false`, and all 38
ordinary ESS files still present. Original, control and fixed DLL/PDB copies
remain archived for rollback and symbolization. The last crash log is the
intentional 18:23:40 old-code control; none appeared during corrected runs.

## Operating rules reinforced

- Never leave a diagnostic profile selected for the next player launch.
- Never use an arbitrary newest test save as the player's continuation save.
- Back up evidence before relaunching: SKSE/MenuPilot logs truncate per launch.
- Require completed ESS/co-save pairs plus successful load signals; a process
  exit code alone is insufficient (the controlled crash returned controller 0).
- Use only owned, muted private-desktop sessions; quit through the game's menu.
- Keep the repair, source provenance and tests separate from vendor mod assets.
- This evidence closes a specific native save-time fault, not a promise that
  an entire modlist or old campaign cannot crash for another reason.
